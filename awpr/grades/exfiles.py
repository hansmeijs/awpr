# PR2021-11-24
from django.contrib.auth.decorators import login_required

from django.core.files.storage import default_storage, FileSystemStorage

from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseNotFound, FileResponse
from django.utils.decorators import method_decorator
from django.utils.translation import activate, ugettext_lazy as _
from django.views.generic import View

from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Frame, Spacer, Image

from awpr import constants as c
from awpr import downloads as dl
from awpr import settings as awpr_settings

from accounts import models as acc_mod
from schools import models as sch_mod
from students import models as stud_mod
from students import views as stud_view
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
class DownloadPublishedFile_with_filename(View):  # PR2021-02-07

    def post(self, request, filename):
        logger.debug(' ============= DownloadPublishedFile ============= ')
        logger.debug('filename: ' + str(filename))
        # download published pdf file from server

        response = None


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
class GradeDownloadEx2aView(View):  # PR2021-01-24

    def get(self, request):
        logger.debug(' ============= GradeDownloadEx2aView ============= ')
        # function creates, Ex2A pdf file based on settings in usersetting

        response = None
        try:
            if request.user and request.user.country and request.user.schoolbase:
                req_user = request.user

    # - reset language
                user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
                activate(user_lang)

    # - get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, is_locked, \
                    examyear_published, school_activated, is_requsr_school = \
                        dl.get_selected_examyear_school_dep_from_usersetting(request)

        # - get selected examperiod, examtype, subject_pk from usersettings
                sel_examperiod, sel_examtype, sel_subject_pk = dl.get_selected_examperiod_examtype_from_usersetting(request)

                logger.debug('sel_examperiod: ' + str(sel_examperiod))
                logger.debug('sel_school: ' + str(sel_school))
                logger.debug('sel_department: ' + str(sel_department))

                if sel_examperiod and sel_school and sel_department and sel_subject_pk:
                    sel_subject = subj_mod.Subject.objects.get_or_none(pk=sel_subject_pk, examyear=sel_examyear)
                    logger.debug('sel_subject: ' + str(sel_subject))

    # +++ get selected grade_rows
                    grade_rows = gr_vw.create_grade_rows(
                        sel_examyear_pk=sel_examyear.pk,
                        sel_schoolbase_pk=sel_school.base_id,
                        sel_depbase_pk=sel_department.base_id,
                        sel_examperiod=sel_examperiod,
                        sel_subject_pk=sel_subject_pk,
                        )

                    buffer = io.BytesIO()
                    canvas = Canvas(buffer)

                    # Start writing the PDF here
                    draw_Ex2A(canvas, sel_examyear, sel_school, sel_department, sel_subject, sel_examperiod, sel_examtype, grade_rows)
                    #test_pdf(canvas)
                    # testParagraph_pdf(canvas)

                    logger.debug('end of draw_Ex2A')

                    canvas.showPage()
                    canvas.save()

                    pdf = buffer.getvalue()
                    buffer.close()

                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = 'inline; filename="testpdf.pdf"'
                    #response['Content-Disposition'] = 'attachment; filename="testpdf.pdf"'

                    response.write(pdf)

        except:
            raise Http404("Error creating Ex2A file")

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
    from reportlab import rl_config
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


def draw_Ex2A(canvas, sel_examyear, sel_school, sel_department, sel_subject, sel_examperiod, sel_examtype, grade_rows):
    logger.debug('----- draw_Ex2A -----')
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

    filepath = awpr_settings.STATICFILES_FONTS_DIR + 'arial.ttf'
    logger.debug('filepath: ' + str(filepath))

    try:
        ttfFile = TTFont('Arial', filepath)
        logger.debug('ttfFile: ' + str(ttfFile))
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

    add_frame_header(canvas, border, text_list, school_name, subject_name)

    canvas.setFont('Arial', 8, leading=None)
    x, y = left + 2*mm, top - 50*mm
    canvas.drawString(x, y, 'Examennummer')
    canvas.drawString(x, y - 4*mm, 'van de kandidaat')
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


def add_frame_header(canvas, border, text_list, school_name, subject_name):
    #logger.debug('----- add_frame_header -----')

    # border = [top, right, bottom, left]
    # width = right - left  # 190 mm
    # height = top - bottom  # 275 mm

    left = border[3]
    width = border[1] - border[3]
    height = 48 * mm
    bottom = border[0] - height
    # canvas.setFillColorRGB(0, 0, 0.5) #  =.HexColor("#000080"),
    # add some flowables

    styleHeader = ParagraphStyle(name="ex_header", alignment=TA_LEFT, fontName="Times-Bold", fontSize=11,
                                   leading=7*mm, leftIndent=2*mm, rightIndent=2*mm)

    #logger.debug('styleHeader: ' + str(styleHeader) + ' ' + str(type(styleHeader)))
    story = []
    for index, text in enumerate(text_list):
        story.append(Paragraph(text, styleHeader))
    # Frame(x1, y1, width,height, leftPadding=6, bottomPadding=6, rightPadding=6, topPadding=6, id=None, showBoundary=0)
    # (x1,y1) = lower left hand corner at coordinate (x1,y1)
    # If showBoundary is non-zero then the boundary of the frame will getdrawn at run time.
    f = Frame(left, bottom, width, height, showBoundary=0)
    f.addFromList(story, canvas)
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
"""