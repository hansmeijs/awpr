
from django.utils.translation import pgettext_lazy, ugettext_lazy as _

from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Frame, Spacer, Image

from awpr import constants as c
from awpr import functions as af
from awpr import settings as s
from awpr import library as awpr_lib

import logging
logger = logging.getLogger(__name__)


def draw_exam(canvas, sel_exam_instance, sel_examyear, user_lang):  # PR2021-05-07 PR2022-01-28
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
    examperiod = sel_exam_instance.examperiod
    amount = sel_exam_instance.amount if sel_exam_instance.amount else 0
    amount_str = str(amount) if amount else '---'
    blanks_str = str(sel_exam_instance.blanks) if sel_exam_instance.blanks else '-'
    scalelength_str = str(sel_exam_instance.scalelength) if sel_exam_instance.scalelength else '-'

    partex_str = sel_exam_instance.partex
    assignment_str = sel_exam_instance.assignment
    keys_str = sel_exam_instance.keys

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

# - get form_text from examyearsetting
    form_text = awpr_lib.get_library(sel_examyear, ['exform', 'exam'])
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
    blanks = form_text.get('blanks', '-') + ':'

    header_list = [
        (minond, None, None, None),
        (title, None, version_cpt, version),
        (educationtype, dep_abbrev, max_score, scalelength_str),
        (examtype, examperiod_cpt, number_questions, amount_str),
        (subject_cpt, subject.name, blanks, blanks_str)
    ]

    filepath = s.STATICFILES_FONTS_DIR + 'arial.ttf'
    try:
        ttfFile = TTFont('Arial', filepath)
        #logger.debug('ttfFile: ' + str(ttfFile))
        pdfmetrics.registerFont(ttfFile)
    except Exception as e:
        logger.error('filepath: ' + str(filepath))
        logger.error(getattr(e, 'message', str(e)))

# create list of questions
    all_partex_assignment_keys_dict = get_all_partex_assignment_keys_dict(partex_str, assignment_str, keys_str)
    if logging_on:
        logger.debug('all_partex_assignment_keys_dict: ' + str(all_partex_assignment_keys_dict) + ' ' + str(
            type(all_partex_assignment_keys_dict)))

    draw_exam_page(canvas, form_text, header_list, last_modified_text, all_partex_assignment_keys_dict)

# - end of draw_exam


def draw_exam_page(canvas, form_text, header_list, last_modified_text, all_partex_assignment_keys_dict):
    # PR2021-05-10 PR2022-01-29
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_exam_page -----')

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
    available_lines = lines_per_page
    number_of_columns = 5
    row_height = 8 * mm

# create pagenumber_text
    page_count = get_page_count(number_of_columns, lines_per_page, all_partex_assignment_keys_dict)

    page_number = 1
    pagenumber_text = ' '.join((
            str(_('Page')), str(page_number),
            'van', str(page_count) + ',',
            today_formatted
    ))
    draw_exam_page_header(canvas, border, coord, header_list, last_modified_text, pagenumber_text)

    for partex_pk, partex_dict in all_partex_assignment_keys_dict.items():

        # calculate necessary lines: 2 for partex_header, 1 for each line
        amount = int(partex_dict.get('amount', 0))
        # calculate number of rows - 5 columns per row
        number_of_columns = 5
        number_of_rows = 1 + int((amount - 1) / number_of_columns) if amount > 0 else 0
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


def get_page_count(number_of_columns, lines_per_page, all_partex_assignment_keys_dict):
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
        number_of_rows = 1 + int((amount - 1) / number_of_columns) if amount > 0 else 0
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
    # loop trhrough rows of page_header
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
            canvas.drawString(x + 40 * mm, y, text)

# draw label 2
        if label2:
        # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
            set_font_timesbold_11_black(canvas)
            canvas.drawString(x + 120 * mm, y, label2)

# draw text 2
        if text2:
            set_font_arial_11_blue(canvas)
            canvas.drawString(x + 160 * mm, y, text2)

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
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_partex_header -----')

    """
    {'amount': 15, 'max_score': 19, 'name': 'Praktijktoets blauw', 
            'q': {1: '4', 2: 'D-b', 3: '6', 4: 'E-d', 5: '2', 6: '1', 7: '1', 8: '1', 9: '1'}},
    """

    top, right, bottom, left = border[0], border[1], border[2], border[3]

    amount = partex_assignment_keys_dict.get('amount', 0)
    questions_dict = partex_assignment_keys_dict.get('q')

# calculate number of rows - 5 columns per row
    number_of_columns = 5
    number_of_rows = 1 + int( (amount - 1) / number_of_columns ) if amount > 0 else 0

    section_top = coord[1]
# +++ loop through rows of this partex
    for row_index in range(0, number_of_rows):  # range(start_value, end_value, step), end_value is not included!

        draw_question_row(canvas, border, coord, form_text, number_of_columns, number_of_rows, row_index, row_height, amount, questions_dict)

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

def draw_question_row(canvas, border, coord, form_text, number_of_columns, number_of_rows, row_index, row_height, amount, questions_dict):
#  questions_dict = {1: '4', 2: 'D-b', 3: '6', 4: 'E-d', 5: '2', 6: '1', 7: '1', 8: '1', 9: '1'}},
    # border = [top, right, bottom, left]
    # coord = [left, top]
    top, right, bottom, left = border[0], border[1], border[2], border[3]

    line_height = 8 * mm
    padding_left = 4 * mm

    col_width = 38*mm
    padding_x = 2*mm

    left = border[3] + padding_left
    y = coord[1]

    y -= line_height

# +++ loop through columns of this page
    for col_index in range(0, number_of_columns):  # range(start_value, end_value, step), end_value is not included!
        q_number = (1 + row_index) + col_index * number_of_rows
        if q_number <= amount:
            answer = None
            if q_number in questions_dict:
                answer = questions_dict[q_number]

            # lookup in questions_dict
            x_label = left + col_index * col_width
            x_data = x_label + 10 * mm
            # draw_red_cross(canvas, x_label, y)

        # draw label
            # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
            set_font_timesroman_11_black(canvas)
            canvas.drawString(x_label, y, str(q_number) + ':')

        # draw text amount
            hex_color = "#000080" if answer else "#000000"
            if answer is None:
                answer = '________'
            canvas.setFillColor(colors.HexColor(hex_color))
            canvas.setFont('Arial', 11, leading=None)
            canvas.drawString(x_data, y, answer)

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

    scalelength = sel_exam_instance.scalelength if sel_exam_instance.scalelength else 0

    partex = sel_exam_instance.partex
    assignment = sel_exam_instance.assignment
    keys = sel_exam_instance.keys
    examyear_code = str(examyear.code)

    subject_name = subject.name
    examperiod_caption = c.get_examperiod_caption(examperiod)
    examtype_caption = c.get_examtype_caption(examtype)

# create list of questions
    assignment_keys_dict = get_all_partex_assignment_keys_dict(amount, scalelength, partex, assignment, keys, {})
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
    partex: 1;1;15;19;Praktijktoets blauw # 2;1;12;12;Minitoets rood # 3;2;12;13;Minitoets groen
    assignment: 1;15;19|1;;4;|2;D;2;|3;;6;|4;E;;|5;;2;|6;;1;|7;;1;|8;;1;|9;;1; # 2;12;12|1;;2;|2;D;2;|3;B;;|4;E;;|5;;6; # 3;12;13|1;;2;|2;C;;|3;;2;|4;;3;|5;E;;|6;;2;|7;;2;
    keys: 1|2;b|4;d # 2|2;a|3;b|4;c # 3|2;ab|3;d|5;a
    """

# - create dict with assignments PR2021-05-08
    all_assignment_dict = get_allassignment_dict_from_string(assignment_str, keys_str)


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
        logger.debug( 'XXXXXXXXXXXXXXXXX all_partex_assignment_keys_dict: ' + str(all_partex_assignment_keys_dict) + ' ' + str(type(all_partex_assignment_keys_dict)))

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
    return all_partex_assignment_keys_dict
# - end of get_all_partex_assignment_keys_dict


#$$$$$$$$$$$$$$$$$$$$$$$$$$$

def get_all_partex_assignment_keys_detail_dict(partex_str, assignment_str, keys_str):  # PR2022-01-30
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- get_all_partex_assignment_keys_detail_dict -----')
        logger.debug('partex_str: ' + str(partex_str))
        logger.debug('assignment_str: ' + str(assignment_str))
        logger.debug('keys_str: ' + str(keys_str))

    """
    partex: 1;1;15;19;Praktijktoets blauw # 2;1;12;12;Minitoets rood # 3;2;12;13;Minitoets groen
    assignment: 1;15;19|1;;4;|2;D;2;|3;;6;|4;E;;|5;;2;|6;;1;|7;;1;|8;;1;|9;;1; # 2;12;12|1;;2;|2;D;2;|3;B;;|4;E;;|5;;6; # 3;12;13|1;;2;|2;C;;|3;;2;|4;;3;|5;E;;|6;;2;|7;;2;
    keys: 1|2;b|4;d # 2|2;a|3;b|4;c # 3|2;ab|3;d|5;a
    """

# - create dict with assignments PR2021-05-08
    all_assignment_detail_dict = get_allassignment_detail_dict_from_string(assignment_str, keys_str)

#  create dict from partex
    all_partex_assignment_keys_detail_dict = {}
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
                if partex_pk in all_assignment_detail_dict:
                    partex_dict['q'] = all_assignment_detail_dict[partex_pk]

                all_partex_assignment_keys_detail_dict[partex_pk] = partex_dict

    if logging_on:
        logger.debug( 'XXXXXXXXXXXXXXXXX all_partex_assignment_keys_dict: ' + str(all_partex_assignment_keys_detail_dict) + ' ' + str(type(all_partex_assignment_keys_detail_dict)))

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
    return all_partex_assignment_keys_detail_dict
# - end of get_all_partex_assignment_keys_detail_dict

#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

def get_allassignment_dict_from_string(assignment_str, keys_str):
    # - create dict with assignments and keys PR2022-01-27

    all_keys_dict = get_allkeys_dict_from_string(keys_str)

    logging_on = False  #s.LOGGING_ON
    if logging_on:
        logger.debug( 'all_keys_dict: ' + str(all_keys_dict) + ' ' + str(type(all_keys_dict)))

    all_assignment_dict = {}
    if assignment_str:
        # pa is the assignment of a partial exam
        for pa in assignment_str.split('#'):
            if pa:
                assignment_dict = {}
                partex_pk = None

                # pa: 1;15;19 | 1;;4; | 2;D;2; | 3;;6; | 4;E;; | 5;;2; | 6;;1; | 7;;1; | 8;;1; | 9;;1;
                pa_arr = pa.split('|')
                if pa_arr:
                    # first item contains partex_pk, amount and max_score
                    info_str = pa_arr[0]
                    if info_str:
                        info_arr = info_str.split(';')
                        partex_pk = int(info_arr[0])

                # all_keys_dict: {1: {2: 'b', 4: 'd'}, 2: {2: 'a', 3: 'b', 4: 'c'}, 3: {2: 'ab', 3: 'd', 5: 'a'}}
                    if all_keys_dict and partex_pk in all_keys_dict:
                        keys_dict = all_keys_dict[partex_pk]
                    else:
                        keys_dict = None


                    skip_first = True
                    for qa in pa_arr:
                        # qa: 1;C;22;
                        # first item contains partex_pk, amount and max_score
                        if skip_first:
                            skip_first = False
                        else:
                            qa_arr = qa.split(';')

                            # qa_arr: ['2', 'D', '2', '']  q_number, max_char, max_score, min_score
                            if len(qa_arr) == 4:
                                q_number = int(qa_arr[0])
                                max_char = qa_arr[1] if qa_arr[1] else ""
                                max_score_str = qa_arr[2] if qa_arr[2] else ""
                                min_score_str = qa_arr[3] if qa_arr[3] else ""

                                if max_char:
                                    value = max_char
                                    if keys_dict and q_number in keys_dict:
                                        keys = keys_dict[q_number]
                                        if keys:
                                            value += ' - ' + keys
                                elif max_score_str:
                                    value = max_score_str
                                else:
                                    value = ""

                                if min_score_str:
                                    value += ' min: ' + min_score_str
                                assignment_dict[q_number] = value

                all_assignment_dict[partex_pk] = assignment_dict
    if logging_on:
        logger.debug('all_assignment_dict: ' + str(all_assignment_dict))
    """
    all_assignment_dict: {
        1: { 1: '4', 2: 'D - b', 3: '6', 4: 'E - d', 5: '2', 6: '1', 7: '1', 8: '1', 9: '1', 10: '5'}, 2: {1: '2', 2: 'D - a', 3: 'B - b', 4: 'E - c', 5: '6'}, 3: {1: '2', 2: 'C - ab', 3: 'D - d', 4: '3', 5: 'E - a', 6: '2', 7: '2'}, 4: {}}
    """
    return all_assignment_dict
# - end of get_allassignment_dict_from_string


def get_allassignment_detail_dict_from_string(assignment_str, keys_str):
    # - create dict with assignments and keys PR2022-01-30

    all_keys_dict = get_allkeys_dict_from_string(keys_str)

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('@@@@@@@@@@@@@@@@@ ----- get_allassignment_detail_dict_from_string -----')
        logger.debug( 'assignment_str: ' + str(assignment_str) + ' ' + str(type(assignment_str)))
        logger.debug( 'keys_str: ' + str(keys_str) + ' ' + str(type(keys_str)))

    all_assignment_dict = {}
    if assignment_str:
        # pa is the assignment of a partial exam
        for pa in assignment_str.split('#'):

            if pa:
                assignment_dict = {}
                partex_pk = None

                # pa: 1;15;19 | 1;;4; | 2;D;2; | 3;;6; | 4;E;; | 5;;2; | 6;;1; | 7;;1; | 8;;1; | 9;;1;
                pa_arr = pa.split('|')
                if pa_arr:
                    # first item contains partex_pk, amount and max_score
                    info_str = pa_arr[0]
                    if info_str:
                        info_arr = info_str.split(';')
                        partex_pk = int(info_arr[0])
                        #amount = int(info_arr[1]) if info_arr[1] else None
                        #assignment_dict['amount'] = amount

                # all_keys_dict: {1: {2: 'b', 4: 'd'}, 2: {2: 'a', 3: 'b', 4: 'c'}, 3: {2: 'ab', 3: 'd', 5: 'a'}}
                    if all_keys_dict and partex_pk in all_keys_dict:
                        keys_dict = all_keys_dict[partex_pk]
                    else:
                        keys_dict = None

                    skip_first = True
                    for qa in pa_arr:
                        # qa: 1;C;22;
                        # first item contains partex_pk, amount and max_score
                        if skip_first:
                            skip_first = False
                        else:
                            qa_arr = qa.split(';')

                            # qa_arr: ['2', 'D', '2', '']  q_number, max_char, max_score, min_score
                            if len(qa_arr) == 4:
                                q_number = int(qa_arr[0])
                                max_char = qa_arr[1] if qa_arr[1] else ""
                                max_score_str = qa_arr[2] if qa_arr[2] else ""
                                min_score_str = qa_arr[3] if qa_arr[3] else ""
                                q_dict = {
                                    'max_char': max_char,
                                    'max_score': max_score_str,
                                    'min_score': min_score_str
                                }
                                if max_char:
                                    if keys_dict and q_number in keys_dict:
                                        keys = keys_dict[q_number]
                                        if keys:
                                            q_dict['keys'] = keys

                                assignment_dict[q_number] = q_dict

                all_assignment_dict[partex_pk] = assignment_dict
    if logging_on:
        logger.debug('allassignment_detail_dict_from_string: ' + str(all_assignment_dict))
    """
    all_assignment_dict: {
    allassignment_detail_dict_from_string: {
        1: {1: {'max_char': '', 'max_score': '4', 'min_score': ''}, 
            2: {'max_char': 'D', 'max_score': '2', 'min_score': '', 'keys': 'b'}, 
            3: {'max_char': '', 'max_score': '6', 'min_score': ''}, 
            4: {'max_char': 'E', 'max_score': '', 'min_score': '', 'keys': 'd'}, 
            5: {'max_char': '', 'max_score': '2', 'min_score': ''}, 
            6: {'max_char': '', 'max_score': '1', 'min_score': ''}, 7: {'max_char': '', 'max_score': '1', 'min_score': ''}, 
            8: {'max_char': '', 'max_score': '1', 'min_score': ''}, 9: {'max_char': '', 'max_score': '1', 'min_score': ''}, 
            10: {'max_char': '', 'max_score': '5', 'min_score': ''}}, 
            
        2: {1: {'max_char': '', 'max_score': '2', 'min_score': ''}, 
            2: {'max_char': 'D', 'max_score': '2', 'min_score': '', 'keys': 'a'}, 
            3: {'max_char': 'B', 'max_score': '', 'min_score': '', 'keys': 'b'}, 
            4: {'max_char': 'E', 'max_score': '', 'min_score': '', 'keys': 'c'}, 5: {'max_char': '', 'max_score': '6', 'min_score': ''}}, 
        3: {1: {'max_char': '', 'max_score': '2', 'min_score': ''}, 2: {'max_char': 'C', 'max_score': '', 'min_score': '', 'keys': 'ab'}, 
            3: {'max_char': 'D', 'max_score': '2', 'min_score': '', 'keys': 'd'}, 4: {'max_char': '', 'max_score': '3', 'min_score': ''}, 
            5: {'max_char': 'E', 'max_score': '', 'min_score': '', 'keys': 'a'}, 6: {'max_char': '', 'max_score': '2', 'min_score': ''}, 
            7: {'max_char': '', 'max_score': '2', 'min_score': ''}}, 
        4: {}}    """
    return all_assignment_dict
# - end of get_allassignment_detail_dict_from_string


def get_allkeys_dict_from_string(keys_str):
    #  keys: 1|2;b|4;d # 2|2;a|3;b|4;c # 3|2;ab|3;d|5;a
    all_keys_dict = {}
    if keys_str:
        for ka in keys_str.split('#'):
            # ka is the keys of a partial exam
            #  ka: 2|2;a|3;b|4;c
            if ka:
                ka_arr = ka.split('|')
                if ka_arr:
                    # first item contains partex_pk
                    partex_pk = int(ka_arr[0])
                    keys_dict = {}
                    skip_first = True
                    for kq in ka.split('|'):
                        # skip first item, it contains partex_pk
                        if skip_first:
                            skip_first = False
                        else:
                            # kq[0] = partex_number
                            #  kq{1] etc : 2;a  q_number ; keys (a,b,c etc)
                            kq_arr = kq.split(';')
                            if len(kq_arr) > 0:
                                q_number = int(kq_arr[0])
                                keys_dict[q_number] = kq_arr[1]
                    all_keys_dict[partex_pk] = keys_dict

                # keys_dict: {2: 'ab', 3: 'd', 5: 'a'} <class 'dict'>
    # all_keys_dict: {1: {2: 'b', 4: 'd'}, 2: {2: 'a', 3: 'b', 4: 'c'}, 3: {2: 'ab', 3: 'd', 5: 'a'}}

    return all_keys_dict
# - end of get_allkeys_dict_from_string


def get_all_result_dict_from_string(result_str):  # PR2022-01-30
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('   ')
        logger.debug('----- get_all_result_dict_from_string -----')
        logger.debug('result_str: ' + str(result_str))
        """
        result_str: 189;202#1|1;1|2;a|3;2|4;b|5;2|6;0|7;x|8;x#2|1;x|2;c|3;b|4;d|5;x#3#4
        """

# - loop through result_str
    all_result_dict = {'partex': {}}
    if result_str:
        partex_result_arr = result_str.split('#')
        if logging_on:
            logger.debug('-----------------------------')
            logger.debug('partex_result_arr: ' + str(partex_result_arr))

        is_first_row = True
        for r_str in partex_result_arr:
            if r_str:
                # first item contains blanks ; total_amount
                # r_str: 189;202
                #  r_str: 1|1;1|2;a|3;2|4;b|5;2|6;0|7;x|8;x

                if is_first_row:
                    is_first_row = False
                # first item contains [blanks ; total_amount]
                    r_arr = r_str.split(';')
                    # r_arr = [ 189, 202 ]
                    if r_arr:
                        all_result_dict['blanks'] = int(r_arr[0]) if r_arr[0] else None
                        all_result_dict['amount'] = int(r_arr[1]) if r_arr[1] else None
                else:
                    this_partex_dict = {}
                    r_arr = r_str.split('|')
                    if logging_on:
                        logger.debug('r_arr: ' + str(r_arr))
                        """
                            r_arr: ['1', '1;1', '2;a', '3;2', '4;b', '5;2', '6;0', '7;x', '8;x']
                        """
                    if r_arr:
                        is_first_r_row = True
                        partex_pk = None
                        this_result_dict = {}
                        for q_str in r_arr:
                            if is_first_r_row:
                                is_first_r_row = False
                                partex_pk = int(r_arr[0])
                            else:
                                q_arr = q_str.split(';')
                                if q_arr:
                                    q_number = int(q_arr[0]) if q_arr[0] else None
                                    q_result = q_arr[1] if q_arr[1] else None
                                    if q_number:
                                        this_result_dict[q_number] = q_result
                        all_result_dict['partex'][partex_pk] = this_result_dict

    if logging_on:
        logger.debug('all_result_dict: ' + str(all_result_dict))
        """
        all_result_dict: {
            'partex': {
                1: {'1': '1', '2': 'a', '3': '2', '4': 'b', '5': '2', '6': '0', '7': 'x', '8': 'x'}, 
                2: {'1': 'x', '2': 'c', '3': 'b', '4': 'd', '5': 'x'}, 
                3: {}}, 
            'blanks': 90, 
            'amount': 103}
        """
    return all_result_dict
# - end of get_all_result_dict_from_string


def get_all_result_with_assignment_dict_from_string(partex_str, assignment_str, keys_str, result_str):  # PR2022-01-29
    #  ce_exam_result: "189;202#1|1;1|2;a|3;2|4;b|5;2|6;0|7;x|8;x#2|1;x|2;c|3;b|4;d|5;x#3#4"
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('   ')
        logger.debug('----- get_all_result_with_assignment_dict_from_string -----')
        logger.debug('result_str: ' + str(result_str))
        """
         result_str: 90;103#1|1;1|2;a|3;2|4;b|5;2|6;0|7;x|8;x#2|1;x|2;c|3;b|4;d|5;x#3
        """

    all_result_dict = get_all_result_dict_from_string(result_str)

    if logging_on:
        logger.debug('all_result_dict: ' + str(all_result_dict))
        """
        all_result_dict: {
            'partex': {
                1: {'1': '1', '2': 'a', '3': '2', '4': 'b', '5': '2', '6': '0', '7': 'x', '8': 'x'}, 
                2: {'1': 'x', '2': 'c', '3': 'b', '4': 'd', '5': 'x'}, 
                3: {}}, 
            'blanks': 90, 
            'amount': 103}
        """

    all_result_with_assignment_dict = {
        'blanks': all_result_dict.get('blanks'),
        'amount': all_result_dict.get('amount'),
        'partex': {}
    }
# - get dict with assignments PR2021-05-08
     # this one gives 'D-3':  get_allassignment_detail_dict_from_string(assignment_str, keys_str)
    all_partex_assignment_keys_detail_dict = get_all_partex_assignment_keys_detail_dict(partex_str, assignment_str, keys_str)
    if logging_on:
        logger.debug('all_partex_assignment_keys_detail_dict: ' + str(all_partex_assignment_keys_detail_dict))
        """
        all_partex_assignment_keys_detail_dict: {
            1: {'amount': 31, 'max_score': 24, 'name': 'Praktijktoets blauw', 
                'q': {
                    1: {'max_char': '', 'max_score': '4', 'min_score': ''}, 
                    2: {'max_char': 'D', 'max_score': '2', 'min_score': '', 'keys': 'b'}, 
                    10: {'max_char': '', 'max_score': '5', 'min_score': ''}}}, 
            2: {'amount': 31, 'max_score': 12, 'name': 'Minitoets rood', 
                'q': {
                1: {'max_char': '', 'max_score': '2', 'min_score': ''}, 
                    2: {'max_char': 'D', 'max_score': '2', 'min_score': '', 'keys': 'a'}, 
                    3: {'max_char': 'B', 'max_score': '', 'min_score': '', 'keys': 'b'}, 
                    4: {'max_char': 'E', 'max_score': '', 'min_score': '', 'keys': 'c'}, 
                    5: {'max_char': '', 'max_score': '6', 'min_score': ''}}}, 
            3: {'amount': 41, 'max_score': 13, 'name': 'Minitoets groen', 
                'q': {
                    1: {'max_char': '', 'max_score': '2', 'min_score': ''}, 
                    2: {'max_char': 'C', 'max_score': '', 'min_score': '', 'keys': 'ab'}, 
                    3: {'max_char': 'D', 'max_score': '2', 'min_score': '', 'keys': 'd'}, 
                    7: {'max_char': '', 'max_score': '2', 'min_score': ''}}}, 
            4: {'amount': 99, 'max_score': 0, 'name': 'Deelexamen 4', 
                'q': {}}}
        """

# - loop through all_result_dict, to get only the partex that are present in result_str
    if all_result_dict:
        all_result_partex_dict = all_result_dict.get('partex')
        if logging_on:
            logger.debug('all_result_partex_dict: ' + str(all_result_partex_dict))
            """
            all_result_partex_dict: {
                1: {'1': '1', '2': 'a', '3': '2', '4': 'b', '5': '2', '6': '0', '7': 'x', '8': 'x'}, 
                2: {'1': 'x', '2': 'c', '3': 'b', '4': 'd', '5': 'x'}, 
                3: {}}
            """
        if all_result_partex_dict:
            total_score = 0
            has_errors = False
            for partex_pk, result_partex_dict in all_result_partex_dict.items():
                if logging_on:
                    logger.debug('-----------------------------')
                    logger.debug('partex_pk: ' + str(partex_pk) + ' result_partex_dict: ' + str(result_partex_dict))
                    """
                    partex_pk: 1 result_partex_dict: {'1': '1', '2': 'a', '3': '2', '4': 'b', '5': '2', '6': '0', '7': 'x', '8': 'x'}
                    """
                this_partex_result_dict = {'blanks': None, 'q': {},  's': {}} # q = display value, s = score

# get assignment info from this partex
                assignment_detaildict = all_partex_assignment_keys_detail_dict.get(partex_pk)
                if logging_on:
                    logger.debug('assignment_detaildict: ' + str(assignment_detaildict))
                """
                assignment_detaildict: {
                    'amount': 31, 'max_score': 24, 'name': 'Praktijktoets blauw', 
                    'q': {  1: {'max_char': '', 'max_score': '4', 'min_score': ''}, 
                            2: {'max_char': 'D', 'max_score': '2', 'min_score': '', 'keys': 'b'}, 
                            3: {'max_char': '', 'max_score': '6', 'min_score': ''}, 
                            4: {'max_char': 'E', 'max_score': '', 'min_score': '', 'keys': 'd'}, 
                            10: {'max_char': '', 'max_score': '5', 'min_score': ''}}}
                """
                entered_count = 0
                if assignment_detaildict is None:
                    pass
                    # return error when assignment not found
                else:
                    name = assignment_detaildict.get('name')
                    amount = assignment_detaildict.get('amount', 0)
                    amount_int = int(amount) if amount else 0
                    if not amount_int:
                        pass
                        # give error when there are no questions
                    else:
                        this_partex_result_dict['name'] = name
                        this_partex_result_dict['amount'] = amount_int

    # loop through all questions of assignment
                        all_q_dict = assignment_detaildict.get('q')
                        if logging_on:
                            logger.debug('all_q_dict: ' + str(all_q_dict))
                            """
                            all_q_dict: {
                                1: {'max_char': '', 'max_score': '4', 'min_score': ''}, 
                                2: {'max_char': 'D', 'max_score': '2', 'min_score': '', 'keys': 'b'}, 
                                3: {'max_char': '', 'max_score': '6', 'min_score': ''},  
                                10: {'max_char': '', 'max_score': '5', 'min_score': ''}}
                            """
                        for q_number in range(1, amount + 1):  # range(start_value, end_value, step), end_value is not included!
                            result = result_partex_dict.get(q_number)
                            score = None
                            is_not_entered = False  # is_not_entered, ie score not entered by examinator
                            is_blank = False # is_blank, ie question not answered by candidate
                            has_error = False

                            q_dict = all_q_dict.get(q_number)
                            """
                            q_dict: {'max_char': 'D', 'max_score': '2', 'min_score': '', 'keys': 'b'}
                            """

                            if logging_on:
                                logger.debug('q_dict: ' + str(q_dict))

                            if q_dict is None:
                                has_error = True
                                # give error when there are no assignment for this q_number
                                #r_dict['error'] = 'No assignment for this question'
                            elif not result:
                                is_not_entered = True  # is_not_entered, ie score not entered by examinator
                            elif result == 'x':
                                is_blank = True # is_blank, ie question not answered by candidate
                                entered_count += 1 # count entered by examinator
                            else:
                                max_char = q_dict.get('max_char')
                                max_score = q_dict.get('max_score')
                                max_score_int = int(max_score) if max_score else None
                                # min_score = int(q_dict.get('min_score', 0))
                                keys = q_dict.get('keys')

            # if max_char has value, it is a multiplechoice question
                                if max_char:
                                    if not keys:
                                        has_error = True
                                    else:
                                        max_char_lc = max_char.lower()
                                        result_lc = result.lower()
                                        result_ord = ord(result_lc)
                                        if not (ord('a') <= result_ord <= ord('w')) :
                                            has_error = True
                                        elif result_ord > ord(max_char_lc):
                                            has_error = True
                                        else:
                                            if not max_score_int:
                                                max_score_int = 1
                                            if result in keys: # keys may comntain multiple characters: 'ac'
                                                score = max_score_int
                                                total_score += max_score_int
                                                result += ' - ok' # Character “✓” (U + 2713)
                                            else:
                                                score = 0

                                            entered_count += 1  # count entered by examinator

                                        if logging_on:
                                            logger.debug('max_char_lc: ' + str(max_char_lc))
                                            logger.debug('result_lc: ' + str(result_lc))
                                            logger.debug('entered_count: ' + str(entered_count))
                                            logger.debug('result: ' + str(result))

                                else:
                                    if not max_score_int:
                                        has_error = True
                                        #r_dict['error'] = 'No max_score for this question'
                                    else:
                                        result_int = int(result)
                                        if result_int > max_score_int:
                                            has_error = True
                                            #r_dict['error'] = 'Score exceeds max_score'
                                        elif result_int < 0:
                                            has_error = True
                                            #r_dict['error'] = 'Score is less than zero'
                                        else:
                                            score = result_int
                                            total_score += result_int
                                            entered_count += 1  # count entered by examinator

                                    if logging_on:
                                        logger.debug('score: ' + str(score))
                                        logger.debug('total_score: ' + str(total_score))
                                        logger.debug('entered_count: ' + str(entered_count))

                            if has_error:
                                has_errors = True
                                r_str = 'e'
                            elif is_not_entered:
                                r_str = 'n'
                            elif is_blank:
                                r_str = 'x'
                            else:
                                r_str = score
                            if r_str:
                                this_partex_result_dict['s'][q_number] = r_str
                            if result:
                                this_partex_result_dict['q'][q_number] = result
                    if amount_int:
                        this_partex_result_dict['blanks'] = amount_int - entered_count
                all_result_with_assignment_dict['partex'][partex_pk] = this_partex_result_dict
                if not has_errors :
                    all_result_with_assignment_dict['total_score'] = total_score

    if logging_on:
        logger.debug('all_result_with_assignment_dict: ' + str(all_result_with_assignment_dict))

    """
all_result_with_assignment_dict: {
    'blanks': 90, 
    'amount': 103, 
    'partex': {
        1: {'d': {1: '1', 2: 'a', 3: '2', 4: 'b', 5: '2', 6: '0', 7: 'x', 8: 'x'}, 
            's': {1: 1, 3: 2, 5: 2, 7: 'x', 8: 'x', 9: 'n', 10: 'n', 11: 'e', 12: 'e', 13: 'e', 14: 'e', 15: 'e', 16: 'e', 17: 'e', 18: 'e', 19: 'e', 20: 'e', 21: 'e', 22: 'e', 23: 'e', 24: 'e', 25: 'e', 26: 'e', 27: 'e', 28: 'e', 29: 'e', 30: 'e'}, 
            'name': 'Praktijktoets blauw',
            'amount': 31}, 
        2: {'d': {1: 'x', 2: 'c', 3: 'b', 4: 'd', 5: 'x'}, 
            's': {1: 'x', 3: 1, 5: 'x', 6: 'e', 7: 'e', 8: 'e', 9: 'e', 10: 'e', 11: 'e', 12: 'e', 13: 'e', 14: 'e', 15: 'e', 16: 'e', 17: 'e', 18: 'e', 19: 'e', 20: 'e', 21: 'e', 22: 'e', 23: 'e', 24: 'e', 25: 'e', 26: 'e', 27: 'e', 28: 'e', 29: 'e', 30: 'e'}, 
            'name': 'Minitoets rood', 
            'amount': 31}, 
        3: {'d': {}, 
            's': {1: 'n', 2: 'n', 3: 'n', 4: 'n', 5: 'n', 6: 'n', 7: 'n', 8: 'e', 9: 'e', 10: 'e', 11: 'e', 12: 'e', 13: 'e', 14: 'e', 15: 'e', 16: 'e', 17: 'e', 18: 'e', 19: 'e', 20: 'e', 21: 'e', 22: 'e', 23: 'e', 24: 'e', 25: 'e', 26: 'e', 27: 'e', 28: 'e', 29: 'e', 30: 'e', 31: 'e', 32: 'e', 33: 'e', 34: 'e', 35: 'e', 36: 'e', 37: 'e', 38: 'e', 39: 'e', 40: 'e'}, 
            'name': 'Minitoets groen', 
            'amount': 41}}
    }
    """
    return all_result_with_assignment_dict
# - end of get_all_result_with_assignment_dict_from_string


def draw_grade_exam(canvas, sel_grade_instance, sel_exam_instance, sel_examyear, user_lang):  # PR2022-01-29
    logging_on = False  # s.LOGGING_ON
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
    amount = sel_exam_instance.amount if sel_exam_instance.amount else 0
    amount_str = str(amount) if amount else '---'
    blanks_str = str(sel_exam_instance.blanks) if sel_exam_instance.blanks else '-'
    scalelength_str = str(sel_exam_instance.scalelength) if sel_exam_instance.scalelength else '-'

    partex_str = sel_exam_instance.partex
    assignment_str = sel_exam_instance.assignment
    keys_str = sel_exam_instance.keys
    result_str = sel_grade_instance.ce_exam_result

# create list of results
    all_result_dict = get_all_result_with_assignment_dict_from_string(partex_str, assignment_str, keys_str, result_str)
    if logging_on:
        logger.debug('----- draw_grade_exam -----')
        logger.debug('sel_exam_instance: ' + str(sel_exam_instance) + ' ' + str(type(sel_exam_instance)))


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

    total_score_str = "---"
    if 'total_score' in all_result_dict:
        total_score_str = str(all_result_dict.get('total_score'))
    total_score_cpt = form_text.get('total_score', '-') + ':'

    header_list = [
        (minond, None, None, None),
        (title, None, version_cpt, version),
        (school_cpt, school, educationtype_cpt, dep_abbrev),
        (candidate_cpt, full_name, exam_number_cpt, exam_number),
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
    # PR2022-01-29
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_grade_exam_page -----')

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
    available_lines = lines_per_page
    number_of_columns = 5
    row_height = 8 * mm

# create pagenumber_text
    page_count = 1 # get_page_count(number_of_columns, lines_per_page, all_result_dict)

    page_number = 1
    pagenumber_text = ' '.join((
            str(_('Page')), str(page_number),
            'van', str(page_count) + ',',
            today_formatted
    ))
    draw_grade_exam_page_header(canvas, border, coord, header_list, last_modified_text, pagenumber_text)

    all_result_partex_dict = all_result_dict.get('partex')
    for partex_pk, partex_dict in all_result_partex_dict.items():
        if logging_on:
            logger.debug('partex_dict: ' + str(partex_dict))

        # calculate necessary lines: 2 for partex_header, 1 for each line
        amount = int(partex_dict.get('amount', 0))
        if logging_on:
            logger.debug('amount: ' + str(amount))
        # calculate number of rows - 5 columns per row
        number_of_columns = 5
        number_of_rows = 1 + int((amount - 1) / number_of_columns) if amount > 0 else 0
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

        draw_grade_partex_header(canvas, border, coord, form_text, partex_dict)

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


def draw_grade_partex_header(canvas, border, coord, form_text, partex_dict):
    # loop through rows of page_header
    logging_on = False  #s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_grade_partex_header -----')

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
    blanks = partex_dict.get('blanks', 0)
    if blanks:
        set_font_timesroman_11_black(canvas)
        canvas.drawRightString(x + 115 * mm, y, form_text.get('blanks', '-') + ':')

# draw text 1
        set_font_arial_11_blue(canvas)
        canvas.drawString(x + 120 * mm, y, str(blanks))

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
# - end of draw_grade_partex_header


def draw_red_cross(canvas, x, y):
    # draw red cross, for outlining while designing
    canvas.setStrokeColorRGB(1, 0, 0)
    canvas.line(x, y + 5 * mm, x, y - 5 * mm)
    canvas.line(x - 5 * mm, y , x + 5 * mm, y )
