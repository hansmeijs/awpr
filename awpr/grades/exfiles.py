# PR2021-11-24
from django.contrib.auth.decorators import login_required

from django.db.models import Q
from django.db import connection
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import activate, ugettext_lazy as _
from django.views.generic import View

from django.core.files.storage import default_storage
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from django.core.files import File

from awpr import constants as c
from awpr import downloads as dl

from accounts import models as acc_mod
from schools import models as sch_mod
from students import models as stud_mod
from students import views as stud_view
from subjects import models as subj_mod
from grades import views as gr_vw

import io
import json
import logging
logger = logging.getLogger(__name__)

@method_decorator([login_required], name='dispatch')
class GradeDownloadEx2aView(View):  # PR2021-01-24

    def get(self, request):
        logger.debug(' ============= GradeDownloadEx2aView ============= ')
        # function creates, Ex2A pdf file based on settings in usersetting
        response = None
        try:
            if request.user and request.user.country and request.user.schoolbase:
                req_usr = request.user
                logger.debug('req_usr: ' + str(req_usr))

    # - reset language
                user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
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
                logger.debug('sel_subject_pk: ' + str(sel_subject_pk))
                if sel_examperiod and sel_school and sel_department and sel_subject_pk:
                    sel_subject = subj_mod.Subject.objects.get_or_none(pk=sel_subject_pk, examyear=sel_examyear)
    # +++ get selected grade_rows
                    grade_rows = gr_vw.create_grade_rows(
                        sel_examyear_pk=sel_examyear.pk,
                        sel_schoolbase_pk=sel_school.base_id,
                        sel_depbase_pk=sel_department.base_id,
                        sel_subject_pk=sel_subject.id,
                        )

                    response = HttpResponse(content_type='application/pdf')
                    response['Content-Disposition'] = 'inline; filename="testpdf.pdf"'

                    buffer = io.BytesIO()
                    canvas = Canvas(buffer)

                    # Start writing the PDF here
                    draw_Ex2A(canvas, grade_rows)
                    # End writing

                    canvas.showPage()
                    canvas.save()

                    pdf = buffer.getvalue()
                    buffer.close()
                    response.write(pdf)

        except:
            raise Http404("Error creating Ex2A file")
        if response:
            return response
        else:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def draw_Ex2A(c, grade_rows):

    # pagesize A4  = (595.27, 841.89) points 1 point = 1/72 inch
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

    c.setLineWidth(.5)
    # corners of the rectangle
    top, left, right, bottom = 287*mm, 10*mm, 200*mm, 12*mm
    width, height = 190*mm, 275*mm
    c.rect(left, bottom, width, height)

    # c.setStrokeColorRGB(0.2,0.5,0.3)
    # horizontal lines
    x1, x2, y = left, right, top - 45*mm
    c.line(x1, y, x2, y)
    # rectangle around Ex2A
    c.rect(right - 16*mm, top - 12*mm, 16*mm, 12*mm)

    x1, x2, y = left, right, top - 62*mm
    c.line(x1, y,x2, y)
    # verrtical lines
    x_list = (25, 65, 17, 22, 22, 22, 17) # last col is 17 mm
    x, y1, y2 = left, top - 45*mm, bottom + 40*mm
    for w in x_list:
        x += w*mm
        c.line(x, y1, x, y2)

    # canvas.setFont(psfontname, size, leading = None)
    c.setFont('Times-Bold', 11, leading=None)
    text_list = ("MINISTERIE VAN ONDERWIJS, WETENSCHAP, CULTUUR EN SPORT",
                 "Lijst van cijfers",
                 "(Artikel 20 Landsbesluit eindexamens v.w.o., h.a.v.o., v.s.b.o., 23 juni 2008, no 54)",
                 "voor het vak:",
                 "EINDEXAMEN in het examenjaar",
                 "Naam van de school:")
    x, y = left + 5 * mm, top
    c.drawString(right - 13*mm, y - 8*mm, "EX.2a")

    for index, text in enumerate(text_list):
        y -= 8*mm if index < 2 else 6*mm
        c.drawString(x, y, text)

    pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
    c.setFont('Arial', 8, leading=None)
    x, y = left + 2*mm, top - 50*mm
    c.drawString(x, y, 'Examennummer')
    c.drawString(x, y -4*mm, 'van de kandidaat')
    c.drawString(x + 10*mm, y -10*mm, '1)')

    x += 30*mm
    c.drawString(x, y, 'Naam en voorletters van de kandidaat')
    y -= 4*mm
    c.drawString(x + 7*mm, y, '(in alfabetische volgorde)')
    y -= 6*mm
    c.drawString(x + 15*mm, y, '2)')
    y -= 6*mm
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    if grade_rows:
        for row in grade_rows:
            logger.debug('row: ' + str(row) + ' ' + str(type(row)))
            c.drawString(left + 12*mm, y, row.get('examnumber', '---'))
            c.drawString(left + 28*mm, y, row.get('fullname', '---'))
            c.drawString(left + 97*mm, y, row.get('se_grade', '---'))
            c.line(left, y -1.25*mm, right, y -1.25*mm)
            y -= 5*mm
