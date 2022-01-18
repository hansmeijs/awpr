
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
from subjects import views as subj_views

import logging
logger = logging.getLogger(__name__)


def draw_exam(canvas, sel_exam_instance, user_lang):  # PR2021-05-07
    logging_on = s.LOGGING_ON
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
    assignment_keys_dict = subj_views.get_assignment_keys_dict(amount, scalelength, partex, assignment, keys)
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
            write_page(canvas, header_list, data_list, question_list, assignment_keys_dict,
                       amount, page_number, page_count, max_rows_per_page, last_modified_text)

# - end of draw_exam


def write_page(canvas, header_list, data_list, question_list, assignment_keys_dict, amount, page_number, page_count, max_rows_per_page, last_modified_text):
    # PR2021-05-10
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- write_page -----')

# +++ write header block
    canvas.setLineWidth(.5)
    # corners of the rectangle
    top, right, bottom, left = 287 * mm, 200 * mm, 17 * mm, 10 * mm
    page_width = right - left  # 190 mm
    height = top - bottom  # 275 mm
    border = (top, right, bottom, left)
    canvas.rect(left, bottom, page_width, height)

    row_height = 7*mm
    padding_x = 2*mm

# - draw horizontal line at bottom of header section
    x1, x2, y = left, right, top - 45 * mm
    canvas.line(x1, y, x2, y)

# - draw horizontal line at top of footer section
    y = bottom + 21*mm
    canvas.line(x1, y, x2, y)

# - vertical lines - w_list contains width of columns
    w_list = (38, 38, 38, 38)  # last col is 38 mm
    x, y1, y2 = left, top - 45 * mm, bottom  + 3 * row_height

    for w in w_list:
        x += w * mm
        canvas.line(x, y1, x, y2)

    style_label = ParagraphStyle(name="ex_header", alignment=TA_LEFT, fontName="Times-Bold", fontSize=11,
                                   leading=row_height, leftIndent=padding_x, rightIndent=padding_x)
    style_data = ParagraphStyle(name="ex_data", alignment=TA_LEFT, fontName="Arial", fontSize=11,
                                   textColor=colors.HexColor("#000080"),
                                   leading=row_height, leftIndent = padding_x, rightIndent = padding_x)

    style_footer_left = ParagraphStyle(name="footer", alignment=TA_LEFT, fontName="Arial", fontSize=8,
                                   textColor=colors.HexColor("#000000"),
                                   leading=row_height, leftIndent = padding_x, rightIndent = padding_x)
    style_footer_right = ParagraphStyle(name="footer", alignment=TA_RIGHT, fontName="Arial", fontSize=8,
                                   textColor=colors.HexColor("#000000"),
                                   leading=row_height, leftIndent = padding_x, rightIndent = padding_x)

    write_page_header(canvas, border, header_list, data_list, style_label, style_data, row_height)
    write_page_footer(canvas, border, question_list, style_label, style_data, style_footer_left, style_footer_right, row_height, last_modified_text, page_number, page_count)

    #canvas.setFont('Arial', 8, leading=None)
    x, y = left + 2 * mm, top - 50 * mm

    top = top - 60 * mm

    #canvas.setFont('Arial', 10, leading=None)
    write_question(canvas, amount, assignment_keys_dict, max_rows_per_page, page_number, top, left)


def write_page_header(canvas, border, header_list, data_list, style_label, style_data, row_height):
    #logger.debug('----- write_page_header -----') PR2021-05-08

    # border = [top, right, bottom, left]
    # width = right - left  # 190 mm
    # height = top - bottom  # 275 mm

    left = border[3]
    page_width = border[1] - border[3]
    height = 48 * mm
    bottom = border[0] - height


    # Frame(x1, y1, width,height, leftPadding=6, bottomPadding=6, rightPadding=6, topPadding=6, id=None, showBoundary=0)
    # (x1,y1) = lower left hand corner at coordinate (x1,y1)
    # If showBoundary is non-zero then the boundary of the frame will get drawn at run time.
    header_frame = Frame(left, bottom, page_width, height, showBoundary=0)
    bottom = bottom - 2 * row_height
    label_width = 38*mm
    label_frame = Frame(left, bottom, label_width , height, showBoundary=0)

    data_frame = Frame(left + label_width, bottom, page_width - label_width, height, showBoundary=0)

    header_arr = []
    for line in header_list:
        header_arr.append(Paragraph(line, style_label))
    header_frame.addFromList(header_arr, canvas)

    label_arr, data_arr = [], []
    for data in data_list:
        label_arr.append(Paragraph(data[0], style_label))
        data_arr.append(Paragraph(data[1], style_data))
    label_frame.addFromList(label_arr, canvas)
    data_frame.addFromList(data_arr, canvas)


def write_page_footer(canvas, border, question_list, style_label, style_data, style_footer_left, style_footer_right, row_height,
                      last_modified_text, page_number, page_count):
    # PR2021-05-09
    #logger.debug('----- write_page_footer -----')
    #logger.debug('last_modified_text: ' + str(last_modified_text))
    # border = [top, right, bottom, left]
    # width = right - left  # 190 mm
    # height = top - bottom  # 275 mm

    right = border[1]
    left = border[3]
    page_width = right - left
    bottom = border[2]

    padding_x = 2*mm
    label_width = 38*mm
    label_height = 3 * row_height
    y1= bottom - 2*mm

# Frame(x1, y1, width,height, leftPadding=6, bottomPadding=6,  rightPadding=6, topPadding=6, id=None, showBoundary=0)
    frame_question_label = Frame(x1=left, y1=y1, width=label_width, height=label_height, showBoundary=0)
    frame_question_data = Frame(x1=left + label_width, y1=y1, width=label_width, height=label_height, showBoundary=0)

    label_arr, data_arr = [], []
    for data in question_list:
        label_arr.append(Paragraph(data[0], style_label))
        data_arr.append(Paragraph(data[1], style_data))
    frame_question_label.addFromList(label_arr, canvas)
    frame_question_data.addFromList(data_arr, canvas)

    pagenumber_text = ' '.join(( str(_('Page')), str(page_number), str(pgettext_lazy('van', 'of')), str(page_count) ))

    #canvas.saveState()
    #canvas.setFont('Arial', 8)
    #canvas.setStrokeColorRGB(0.5, 0.5, 0.5)
    #canvas.drawString(left + 2*mm, bottom - 4*mm, last_modified_text)
    #canvas.drawRightString(left + 100*mm, bottom - 4*mm, pagenumber_text)
    #canvas.restoreState()

    modifiedby_frame = Frame(x1=left, y1=bottom - 12*mm, width= 4/5 *page_width,  height= 12*mm, showBoundary=0)
    modifiedby_frame.addFromList([Paragraph(last_modified_text, style_footer_left)], canvas)

    pagenumber_frame = Frame(x1=right - page_width / 5, y1=bottom - 12*mm, width=page_width / 5, height= 12*mm, showBoundary=0)
    pagenumber_frame.addFromList([Paragraph(pagenumber_text, style_footer_right)], canvas)


def write_question(canvas, amount, assignment_keys_dict, max_rows_per_page, page_number, top, left):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- write_question -----')
    # The vertical offset between the point at which one line starts and where the next starts is called the leading offset.

    col_width = 38*mm
    row_height = 8*mm
    padding_x = 2*mm
    styleLabel = ParagraphStyle(name="style_label", alignment=TA_LEFT, fontName="Arial", fontSize=10,
                                   textColor=colors.HexColor("#000000"),
                                   leading=row_height, leftIndent = padding_x, rightIndent = padding_x)
    styleData = ParagraphStyle(name="style_data", alignment=TA_LEFT, fontName="Arial", fontSize=10,
                                   textColor=colors.HexColor("#000080"),
                                   leading=row_height, leftIndent = padding_x, rightIndent = padding_x)

    question_number = (page_number -1) * max_rows_per_page * 5

# +++ loop through columns of this page
    for col_index in range(0, 5):  # range(start_value, end_value, step), end_value is not included!
        # create 2 frames per column: 1 for label and 1 for values
        label_list = []
        data_list = []

        if question_number < amount:
            for row_index in range(0, max_rows_per_page):  # range(start_value, end_value, step), end_value is not included!
                y = top - row_index * row_height
                question_number += 1
                if question_number <= amount:
                    data_text = assignment_keys_dict.get(question_number)
                    if logging_on:
                        logger.debug('data_text: ' + str(data_text) + ' ' + str(type(data_text)))

                    label_text = str(question_number) + ':'
                    label_list.append(Paragraph(label_text, styleLabel))

                    style = styleData if data_text else styleLabel
                    if data_text is None:
                        data_text = '________'
                    data_list.append(Paragraph(data_text, style))

# - get coordinates of frames
            x_label = left + col_index * col_width
            x_data = x_label + 10 * mm
            bottom = 20*mm
            width = 38*mm
            height = 220*mm

    # - add label_frame to canvas
            label_frame = Frame(x_label, bottom, width, height, showBoundary=0)
            label_frame.addFromList(label_list, canvas)

    # - add data_frame to canvas
            data_frame = Frame(x_data, bottom, width, height, showBoundary=1)
            data_frame.addFromList(data_list, canvas)


#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

def draw_pdf_upload_log(canvas, sel_exam_instance, user_lang):  # PR2021-07-16
    logging_on = s.LOGGING_ON
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
    assignment_keys_dict = subj_views.get_assignment_keys_dict(amount, scalelength, partex, assignment, keys)
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
            write_page(canvas, header_list, data_list, question_list, assignment_keys_dict,
                       amount, page_number, page_count, max_rows_per_page, last_modified_text)

# - end of draw_exam
