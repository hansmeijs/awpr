# PR2018-04-14
from django.contrib.auth.decorators import login_required # PR2018-04-01
from django.shortcuts import render, redirect #, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView, DeleteView, View, ListView, CreateView

import json # PR2018-12-03

from schools.models import Department, Schoolbase, School, Schoolsetting
from subjects.models import Subject, Level, Sector, Subjecttype, Scheme, Schemeitem
from students.models import Birthcountry, Birthcity, Student
from awpr import functions as f
from awpr import constants as c

# PR2018-04-27
import logging
logger = logging.getLogger(__name__)

# PR2018-05-06
from django.utils.translation import activate, get_language_info, ugettext_lazy as _



# PR2018-04-27 import Excel file from "How to upload and process the Excel file in Django" http://thepythondjango.com/upload-process-excel-file-django/
import openpyxl
from tablib import Dataset, import_set


@method_decorator([login_required], name='dispatch')
class ImportSchoolView(View):

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system_perm_admin
        param = {'display_school': True, 'display_user': True, 'override_school': request.user.role_str}
        headerbar_param = f.get_headerbar_param(request, param)
        return render(request, 'import_school.html', headerbar_param)

    def post(self, request):
        # self.request = request
        logger.debug('ImportSchoolView post: request.user: ' + str(request.user) + ' type: ' + str(type(request.user)))
        logger.debug('ImportSchoolView post: self.request.user: ' + str(self.request.user) + ' type: ' + str(type(self.request.user)))

        # Note that request.FILES will only contain data if the request method was POST and
        # the <form> that posted the request has the attribute enctype="multipart/form-data".
        # Otherwise, request.FILES will be empty.

        # from https://docs.djangoproject.com/en/2.0/ref/files/uploads/#django.core.files.uploadedfile.UploadedFile.name
        uploadedfile = request.FILES["excel_file"]
        # logger.debug('import_school_excel_view uploadedfile.name: ' + str(uploadedfile.name))

        # you may put validations here to check extension or file size
        wb = openpyxl.load_workbook( uploadedfile)

        # PR2018-04-27 debug: DeprecationWarning: Call to deprecated function get_sheet_names (Use wb.sheetnames). Was:  ws_names = wb.get_sheet_names()
        ws_names = wb.sheetnames
        # logger.debug('import_school_excel_view ws_names: ' + str(ws_names))
        worksheet = wb.worksheets[0]
        # logger.debug('import_school_excel_view worksheet: ' + str(worksheet))
        excel_data = list()

        # check if request.user.country is parent of request.user.examyear PR2018-10-18
        if request.user is not None:
            if request.user.country is not None and request.user.examyear is not None:
                if request.user.examyear.country.pk == request.user.country.pk:

                    # Map dep.abbrev to dep.base.id  {'vsbo': 1, 'havo': 2, 'vwo': 3}
                    mapped_depbase_list = get_mapped_depbase_list(request.user.examyear)

#examyear = request.user.examyear
#country = examyear.country

                    # iterating over the rows and
                    # getting value from each cell in row
                    for row in worksheet.iter_rows():
                        row_data = list()
                        for cell in row:
                            row_data.append(str(cell.value))
                        logger.debug('import_school_excel_view row_data: ' + str(row_data))

                        school_code = str(row_data[0])
                        school_name = str(row_data[1])
                        school_abbrev = str(row_data[2])
                        school_article = str(row_data[3])

                        school_depname_list = str(row_data[4])
                        school_depbase_list = convert_nameslist_to_baseidlist(school_depname_list, mapped_depbase_list)

                        school_is_template = True if str(row_data[5]) == "1" else False

                        school = School()
                        school.examyear = request.user.examyear
                        school.name = school_name
                        school.code = school_code
                        school.abbrev = school_abbrev
                        school.article = school_article
                        school.depbase_list = school_depbase_list

                        # is_template stores the examyear.id. In that way there can only be one template per examyear / country
                        if school_is_template:
                            school.is_template = request.user.examyear.id

                        school.save(request=self.request)
                        logger.debug('import_school_excel_view _school: ' + str(school.name))

                        excel_data.append(row_data)

        return render(request, 'import_school.html', {"excel_data": excel_data})


@method_decorator([login_required], name='dispatch')
class ImportSubjectView(View):

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system
        param = {'display_school': True, 'display_user': True, 'override_school': request.user.role_str}
        headerbar_param = f.get_headerbar_param(request, param)
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'import_subject.html', headerbar_param)

    def post(self,request):
        # Note that request.FILES will only contain data if the request method was POST and
        # the <form> that posted the request has the attribute enctype="multipart/form-data".
        # Otherwise, request.FILES will be empty.

        # from https://docs.djangoproject.com/en/2.0/ref/files/uploads/#django.core.files.uploadedfile.UploadedFile.name
        uploadedfile = request.FILES["excel_file"]
        # you may put validations here to check extension or file size
        wb = openpyxl.load_workbook(uploadedfile)

        # PR2018-04-27 debug: DeprecationWarning: Call to deprecated function get_sheet_names (Use wb.sheetnames). Was:  ws_names = wb.get_sheet_names()
        ws_names = wb.sheetnames
        worksheet = wb.worksheets[0]
        excel_data = list()

        # check if request.user.country is parent of request.user.examyear PR2018-10-18
        if request.user is not None:
            if request.user.examyear is not None and request.user.country is not None:
                if request.user.examyear.country.pk == request.user.country.pk:

                    # Map dep.abbrev to dep.base.id  {'vsbo': 1, 'havo': 2, 'vwo': 3}
                    mapped_depbase_list = get_mapped_depbase_list(request.user.examyear)

                    # iterating over the rows and getting value from each cell in row
                    for row in worksheet.iter_rows():
                        row_data = list()
                        for cell in row:
                            row_data.append(str(cell.value))
                        # row_data: ['Nederlandse taal', 'ne', '10', 'vsbo']

                        subject_name = str(row_data[0])
                        subject_abbrev = str(row_data[1])
                        subject_sequence = int(row_data[2])
                        subject_depname_list = str(row_data[3])

                        subject_depbase_list = convert_nameslist_to_baseidlist(subject_depname_list, mapped_depbase_list)

                        # PR2018-04-28 debug: don't forget de brackets when creating an instance of the class
                        subject = Subject()

                        # new subject.base is created in subject.save
                        subject.examyear = request.user.examyear
                        subject.name = subject_name
                        subject.abbrev = subject_abbrev
                        subject.sequence = subject_sequence
                        subject.depbase_list = subject_depbase_list

                        subject.save(request=self.request)

                        excel_data.append(row_data)

        return render(request, 'import_subject.html', {"excel_data": excel_data})

@method_decorator([login_required], name='dispatch')
class ImportDepartmentView(View):

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system_perm_admin
        param = {'display_school': True, 'display_user': True, 'override_school': request.user.role_str}
        headerbar_param = f.get_headerbar_param(request, param)

        logger.debug('ImportDepartmentView headerbar_param: ' + str(headerbar_param))
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'import_department.html', headerbar_param)

    def post(self,request):
        uploadedfile = request.FILES["excel_file"]
        # logger.debug('ImportDepartmentView uploadedfile.name: ' + str(uploadedfile.name))

        # you may put validations here to check extension or file size
        wb = openpyxl.load_workbook(uploadedfile)
        # PR2018-04-27 debug: DeprecationWarning: Call to deprecated function get_sheet_names (Use wb.sheetnames). Was:  ws_names = wb.get_sheet_names()
        ws_names = wb.sheetnames
        worksheet = wb.worksheets[0]
        excel_data = list()

        # check if request.user.country is parent of request.user.examyear PR2018-10-18
        if request.user.examyear is not None and request.user.country is not None:
            if request.user.examyear.country.id == request.user.country.id:

        # iterating over the rows and
        # getting value from each cell in row
                for row in worksheet.iter_rows():
                    row_data = list()
                    for cell in row:
                        row_data.append(str(cell.value))
                    logger.debug('row_data: ' + str(row_data))

                    dep_name = str(row_data[0])
                    dep_abbrev = str(row_data[1])
                    dep_sequence = int(row_data[2])

                    #PR2018-04-28 debug: don't forget de brackets when creating an instance of the class
                    dep = Department()

                    # dep.base: new dep.base is created in dep.save
                    dep.examyear = request.user.examyear

                    dep.name = dep_name
                    dep.abbrev = dep_abbrev
                    dep.sequence = dep_sequence

                    dep.save(request=self.request)
                    logger.debug('dep.id: ' + str(dep.id) + ' .name: ' + str(dep.name) + ' .abbrev: ' + str(dep.abbrev) + ' .sequence: ' + str(dep.sequence))

                    excel_data.append(row_data)

        return render(request, 'import_department.html', {"excel_data": excel_data})


@method_decorator([login_required], name='dispatch')
class ImportLevelView(View):

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system_perm_admin
        param = {'display_school': True, 'display_user': True, 'override_school': request.user.role_str}
        headerbar_param = f.get_headerbar_param(request, param)
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'import_level.html', headerbar_param)

    def post(self, request):
        uploadedfile = request.FILES["excel_file"]
        # logger.debug('ImportDepartmentView uploadedfile.name: ' + str(uploadedfile.name))
        # you may put validations here to check extension or file size
        wb = openpyxl.load_workbook(uploadedfile)
        # PR2018-04-27 debug: DeprecationWarning: Call to deprecated function get_sheet_names (Use wb.sheetnames). Was:  ws_names = wb.get_sheet_names()
        ws_names = wb.sheetnames
        worksheet = wb.worksheets[0]
        excel_data = list()

        # check if request.user.country is parent of request.user.examyear PR2018-10-18
        if request.user.examyear is not None and request.user.country is not None:
            if request.user.examyear.country.id == request.user.country.id:

                # Map dep.abbrev to dep.base.id  {'vsbo': 1, 'havo': 2, 'vwo': 3}
                mapped_depbase_list = get_mapped_depbase_list(request.user.examyear)

                # iterating over the rows and getting value from each cell in row
                self.sequence = 1
                for row in worksheet.iter_rows():
                    row_data = list()
                    for cell in row:
                        row_data.append(str(cell.value))
                    # row_data: ['Theoretisch Kadergerichte Leerweg', 'TKL', 'vsbo']

                    level_name = str(row_data[0])
                    level_abbrev = str(row_data[1])

                    level_depname_list = str(row_data[2])
                    level_depbase_list = convert_nameslist_to_baseidlist(level_depname_list, mapped_depbase_list)

                    level_sequence = self.sequence
                    self.sequence += 1

                    #PR2018-04-28 debug: don't forget de brackets when creating an instance of the class
                    level = Level()

                    # new level.base is created in level.save
                    level.examyear = request.user.examyear

                    level.name = level_name
                    level.abbrev = level_abbrev
                    level.sequence = level_sequence

                    level.depbase_list = level_depbase_list
                    level.save(request=self.request)

                    excel_data.append(row_data)

        return render(request, 'import_level.html', {"excel_data": excel_data})


@method_decorator([login_required], name='dispatch')
class ImportSectorView(View):

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system_perm_admin
        param = {'display_school': True}
        headerbar_param = f.get_headerbar_param(request, param)
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'import_sector.html', headerbar_param)

    def post(self, request):
        uploadedfile = request.FILES["excel_file"]
        # logger.debug('ImportDepartmentView uploadedfile.name: ' + str(uploadedfile.name))

        # you may put validations here to check extension or file size
        wb = openpyxl.load_workbook(uploadedfile)
        # PR2018-04-27 debug: DeprecationWarning: Call to deprecated function get_sheet_names (Use wb.sheetnames). Was:  ws_names = wb.get_sheet_names()
        ws_names = wb.sheetnames
        worksheet = wb.worksheets[0]
        excel_data = list()

        # check if request.user.country is parent of request.user.examyear PR2018-10-18
        if request.user.examyear is not None and request.user.country is not None:
            if request.user.examyear.country.id == request.user.country.id:

                # Map dep.abbrev to dep.base.id  {'vsbo': 1, 'havo': 2, 'vwo': 3}
                mapped_depbase_list = get_mapped_depbase_list(request.user.examyear)

                # iterating over the rows and  getting value from each cell in row
                self.sequence = 1
                for row in worksheet.iter_rows():
                    row_data = list()
                    for cell in row:
                        row_data.append(str(cell.value))
                    # row_data: ['Economie', 'ec', 'vsbo']

                    sector_name = str(row_data[0])
                    sector_abbrev = str(row_data[1])

                    sector_depname_list = str(row_data[2])
                    sector_depbase_list = convert_nameslist_to_baseidlist(sector_depname_list, mapped_depbase_list)

                    sector_sequence = self.sequence
                    self.sequence += 1

                    # PR2018-04-28 debug: don't forget de brackets when creating an instance of the class
                    sector = Sector()

                    #sector.base = sector_base: New sector.base is created in sector.save
                    sector.examyear = request.user.examyear

                    sector.name = sector_name
                    sector.abbrev = sector_abbrev
                    sector.sequence = sector_sequence

                    sector.depbase_list = sector_depbase_list

                    sector.modified_by = request.user
                    sector.modified_at = timezone.now()

                    sector.save(request=self.request)

                    excel_data.append(row_data)

        return render(request, 'import_sector.html', {"excel_data": excel_data})


# ===== Import Subjecttype ===================

@method_decorator([login_required], name='dispatch')
class ImportSubjecttypeView(View):

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system_perm_admin
        param = {'display_school': True, 'display_user': True, 'override_school': request.user.role_str}
        headerbar_param = f.get_headerbar_param(request, param)
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'import_subjecttype.html', headerbar_param)


    def post(self,request):
        # from https://docs.djangoproject.com/en/2.0/ref/files/uploads/#django.core.files.uploadedfile.UploadedFile.name
        uploadedfile = request.FILES["excel_file"]
        wb = openpyxl.load_workbook(uploadedfile)

        # PR2018-04-27 debug: DeprecationWarning: Call to deprecated function get_sheet_names (Use wb.sheetnames). Was:  ws_names = wb.get_sheet_names()
        ws_names = wb.sheetnames
        worksheet = wb.worksheets[0]
        excel_data = list()

        # check if request.user.country is parent of request.user.examyear PR2018-10-18
        if request.user is not None:
            if request.user.examyear is not None and request.user.country is not None:
                if request.user.examyear.country.pk == request.user.country.pk:

                    # Map dep.abbrev to dep.base.id  {'vsbo': 1, 'havo': 2, 'vwo': 3}
                    mapped_depbase_list = get_mapped_depbase_list(request.user.examyear)

                    # iterating over the rows and getting value from each cell in row
                    for row in worksheet.iter_rows():
                        row_data = list()
                        for cell in row:
                            row_data.append(str(cell.value))
                        logger.debug('row_data: ' + str(row_data))
                        # [‘Gemeenschappelijk deel’, ‘Gemeensch. ’, ‘gmd’, ‘1’, ‘vsbo;havo;vwo’]
                        # [‘Sector deel’, ‘Sector deel’, ‘spd’, ‘2’, ‘vsbo’]
                        # [‘Profiel deel’, ‘Profiel deel’, ‘spd’, ‘3’, ‘havo;vwo’]
                        # [‘Extra vak’, ‘Extra vak’, ‘vrd’, ‘4’, ‘vsbo’]
                        # [‘Vrije deel’, ‘Vrije deel’, ‘vrd’, ‘5’, ‘havo;vwo’]
                        # [‘Sector programma’, ‘Sectorpr. ’, ‘spr’, ‘6’, ‘vsbo’]
                        # [‘Sector werkstuk’, ‘Werkstuk’, ‘wst’, ‘7’, ‘vsbo’]
                        # [‘Profiel werkstuk’, ‘Werkstuk’, ‘wst’, ‘8’, ‘havo;vwo’]
                        # [‘Stage’, ‘Stage’, ‘stg’, ‘9’, ‘vsbo’]

                        subjecttype_name = str(row_data[0])
                        subjecttype_abbrev = str(row_data[1])
                        subjecttype_code = str(row_data[2])
                        subjecttype_sequence = int(row_data[3])
                        subjecttype_depname_list = str(row_data[4])

                        subjecttype_depbase_list = convert_nameslist_to_baseidlist(subjecttype_depname_list, mapped_depbase_list)

                        # PR2018-04-28 debug: don't forget de brackets when creating an instance of the class
                        subjecttype = Subjecttype()

                        # new subjecttype.base is created in subjecttype.save
                        subjecttype.examyear = request.user.examyear
                        subjecttype.name = subjecttype_name
                        subjecttype.abbrev = subjecttype_abbrev
                        subjecttype.code = subjecttype_code
                        subjecttype.sequence = subjecttype_sequence
                        subjecttype.depbase_list = subjecttype_depbase_list

                        subjecttype.save(request=self.request)

                        excel_data.append(row_data)

        return render(request, 'import_subjecttype.html', {"excel_data": excel_data})


# ===== Import Scheme ===================
@method_decorator([login_required], name='dispatch')
class ImportSchemeView(View): # PR2018-11-10

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system
        param = {'display_school': True, 'display_user': True, 'override_school': request.user.role_str}
        headerbar_param = f.get_headerbar_param(request, param)
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'import_scheme.html', headerbar_param)

    def post(self,request):
        uploadedfile = request.FILES["excel_file"]
        wb = openpyxl.load_workbook(uploadedfile)
        # ws_names = wb.sheetnames
        worksheet = wb.worksheets[0]
        excel_data = list()

        # check if request.user.country is parent of request.user.examyear PR2018-10-18
        if request.user is not None:
            if request.user.examyear is not None and request.user.country is not None:
                if request.user.examyear.country.pk == request.user.country.pk:

                    # Map dep.abbrev to base.id  {'vsbo': 1, 'havo': 2, 'vwo': 3}
                    mapped_depbase_list = get_mapped_depbase_list(request.user.examyear)
                    logger.debug('mapped_depbase_list: ' + str(mapped_depbase_list))
                    mapped_levelbase_list = get_mapped_levelbase_list(request.user.examyear)
                    logger.debug('mapped_levelbase_list: ' + str(mapped_levelbase_list))
                    mapped_sectorbase_list = get_mapped_sectorbase_list(request.user.examyear)
                    logger.debug('mapped_sectorbase_list: ' + str(mapped_sectorbase_list))


                    # iterating over the rows and
                    # getting value from each cell in row
                    for row in worksheet.iter_rows():
                        row_data = list()
                        for cell in row:
                            row_data.append(str(cell.value))
                        # row_data: ['vsbo', 'TKL', 'tech']
                        logger.debug('--- row_data[0]: ' + str(row_data[0]))

                        dep_abbrev = ''
                        department = None
                        if row_data[0]:
                            depbase_id = mapped_depbase_list.get(str(row_data[0]).lower(), None)
                            logger.debug('depbase_id: ' + str(depbase_id))
                            if depbase_id:
                                # skip if more than 1 record found
                                logger.debug('count: ' + str(Department.objects.filter(base__id=depbase_id, examyear=request.user.examyear).count()))

                                if Department.objects.filter(base__id=depbase_id, examyear=request.user.examyear).count() == 1:
                                    department = Department.objects.filter(base__id=depbase_id, examyear=request.user.examyear).first()
                                    logger.debug('department: ' + str(department))

                                    if department:
                                        dep_abbrev = department.abbrev

                        level_abbrev = ''
                        level = None
                        logger.debug('--- row_data[1]: ' + str(row_data[1]))
                        if row_data[1] is not None:
                            levelbase_id = mapped_levelbase_list.get(str(row_data[1]).lower(), None)
                            logger.debug('levelbase_id: ' + str(levelbase_id))
                            if levelbase_id:
                                # skip if more than 1 record found
                                logger.debug('count: ' + str(Level.objects.filter(base__id=levelbase_id, examyear=request.user.examyear).count()))

                                if Level.objects.filter(base__id=levelbase_id, examyear=request.user.examyear).count() == 1:
                                    level = Level.objects.filter(base__id=levelbase_id, examyear=request.user.examyear).first()
                                    logger.debug('level: ' + str(level))
                                    if level:
                                        level_abbrev = level.abbrev.lower()
                                        logger.debug('level_abbrev: ' + str(level_abbrev))

                        sector_abbrev = ''
                        sector = None
                        logger.debug('--- row_data[2]: ' + str(row_data[2]))
                        if row_data[2] is not None:
                            sectorbase_id = mapped_sectorbase_list.get(str(row_data[2]).lower(), None)
                            logger.debug('sectorbase_id: ' + str(sectorbase_id))
                            if sectorbase_id:
                                # skip if more than 1 record found
                                logger.debug('count: ' + str(Sector.objects.filter(base__id=sectorbase_id, examyear=request.user.examyear).count()))

                                if Sector.objects.filter(base__id=sectorbase_id, examyear=request.user.examyear).count() == 1:
                                    sector = Sector.objects.filter(base__id=sectorbase_id, examyear=request.user.examyear).first()
                                    logger.debug('sector: ' + str(sector))
                                    if sector:
                                        sector_abbrev = sector.abbrev.lower()
                                        logger.debug('sector_abbrev: ' + str(sector_abbrev))

                        scheme = Scheme()

                        if department is not None:
                            scheme.department = department
                        if level is not None:
                            scheme.level = level
                        if sector is not None:
                            scheme.sector = sector

                        logger.debug('dep_abbrev: ' + str(dep_abbrev))
                        logger.debug('level_abbrev: ' + str(level_abbrev))
                        logger.debug('sector_abbrev: ' + str(sector_abbrev))

                        scheme.name = Scheme.create_scheme_name(
                            dep_abbrev=dep_abbrev,
                            level_abbrev=level_abbrev,
                            sector_abbrev=sector_abbrev )
                        logger.debug('scheme.name: ' + str(scheme.name))

                        scheme.save(request=self.request)
                        # logger.debug('subject.id: ' + str(subject.id) + ' .name: ' + str(subject.name) + ' .abbrev: ' + str(subject.abbrev) + ' .sequence: ' + str(subject.sequence))

                        excel_data.append(row_data)

        return render(request, 'import_scheme.html', {"excel_data": excel_data})



# ===== Import Scheme items ===================
@method_decorator([login_required], name='dispatch')
class ImportSchemeitemView(View):  # PR2018-11-10

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system
        param = {'display_school': True, 'display_user': True, 'override_school': request.user.role_str}
        headerbar_param = f.get_headerbar_param(request, param)
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'import_schemeitem.html', headerbar_param)

    def post(self,request):
        logger.debug('# ===== Import Scheme items =========')
        uploadedfile = request.FILES["excel_file"]
        logger.debug('uploadedfile: ' + str(uploadedfile))
        wb = openpyxl.load_workbook(uploadedfile)
        # ws_names = wb.sheetnames
        worksheet = wb.worksheets[0]
        excel_data = list()

        # check if request.user.country is parent of request.user.examyear PR2018-10-18
        if request.user is not None:
            if request.user.examyear is not None and request.user.country is not None and request.user.schoolbase is not None:
                if request.user.examyear.country.pk == request.user.country.pk:
                    # get request.user.school of request.user.examyear
                    school = School.objects.filter(examyear=request.user.examyear, base=request.user.schoolbase).first()
                    if school is not None:
                        logger.debug(school.name)

                        # Excel file colums:
                        # 0: schemename, 1: subject, 2: subjecttype, 3: gradetype, 4: sequence,
                        # 5: weighSE, 6: weighCE, 7: mandatory, 8: combi, 9: keuzecombi,  10: praktijk


                        # Map scheme.name to scheme.id {'vsbo - tkl - tech': 4, ... 'vwo - n&g': 15, 'vwo - n&t': 14}
                        scheme_dict = {}
                        schemes =  Scheme.objects.filter(department__examyear=request.user.examyear)
                        for scheme in schemes:
                            scheme_key =  scheme.name.lower()
                            scheme_dict[scheme_key] = scheme.id
                        logger.debug(scheme_dict)
                        # scheme_dict = {'vsbo - tkl - tech': 4, ... 'vwo - n&g': 15, 'vwo - n&t': 14}

                        # Map subject.abbrev to subject.id {'ne': 3}
                        subject_dict = {}
                        subjects =  Subject.objects.filter(examyear=request.user.examyear)
                        for subject in subjects:
                            subject_key =  subject.abbrev.lower()
                            subject_dict[subject_key] = subject.id
                        logger.debug(subject_dict)
                        # subject_dict = {'ne': 37, 'pa': 6, 'en': 33, 'sp': 8, ... , 'stg': 24, 'go': 47}

                        # Map subjecttype.code
                        # Cannot map subjecttype, because code can refer to different departments. Lookup after scheme is found

                        # iterating over the rows and
                        # getting value from each cell in row
                        for row in worksheet.iter_rows():
                            row_data = list()
                            for cell in row:
                                row_data.append(str(cell.value))
                            logger.debug(str(row_data))
                            # ['Name', 'subject', 'subjecttype', 'gradetype', 'sequence', 'weighSE', 'weighCE', 'mandatory', 'combi', 'keuzecombi', 'praktijk']
                            # ['vsbo - tkl - tech', 'ne', 'gmd', '1', '30', '1', '1', '1', '0', '0', '0']

                            # get scheme id
                            scheme_id = int(scheme_dict.get(str(row_data[0]), '-1'))
                            logger.debug('scheme_id: ' + str(scheme_id))

                            scheme = Scheme.objects.filter(id=scheme_id).first()
                            if scheme:
                                logger.debug('scheme found: ' + scheme.name)

                                # get subject id
                                subject_id = int(subject_dict.get(str(row_data[1]), '-1'))
                                subject = Subject.objects.filter(id=subject_id).first()
                                if subject:
                                    logger.debug('subject found: ' + subject.abbrev)

                                    # get subjecttype id
                                    code = str(row_data[2])
                                    logger.debug('code: ' + code)  # code: 'gmd'
                                    dep_id_str = ';' + str(scheme.department.base.id) + ';'
                                    logger.debug('dep_id_str: ' + dep_id_str)  # dep_id_str: ';1;'
                                    subjecttype = Subjecttype.objects.filter(
                                        examyear=request.user.examyear,
                                        code=code,
                                        depbase_list__contains=dep_id_str
                                    ).first()
                                    logger.debug('subjecttype: ' + str(subjecttype) + ' type: ' + str(type(subjecttype)))

                                    if subjecttype:
                                        logger.debug('subjecttype found: ' + subjecttype.code)
                                        #  0 Scheme 1 subject 2 Subjecttype 3 Gradetype 4 Sequence 5 weightSE 6 weightCE
                                        # 7 is_mandatory 8 is_combi 9 choicecombi_allowed 10 has_practexam

                                        gradetype = int(str(row_data[3]))
                                        sequence = int(str(row_data[4]))
                                        weightSE = int(str(row_data[5]))
                                        weightCE = int(str(row_data[6]))
                                        is_mandatory = True if  str(row_data[7]) == '1' else False
                                        is_combi = True if  str(row_data[8]) == '1' else False
                                        choicecombi_allowed = True if  str(row_data[9]) == '1' else False
                                        has_practexam = True if  str(row_data[10]) == '1' else False

                                        # create new schemeitem
                                        schemeitem = Schemeitem()

                                        schemeitem.school = school
                                        schemeitem.scheme = scheme
                                        schemeitem.subject = subject
                                        schemeitem.subjecttype = subjecttype

                                        logger.debug('schemeitem.school: ' + schemeitem.school.name)
                                        logger.debug('schemeitem.scheme: ' + schemeitem.scheme.name)
                                        logger.debug('schemeitem.subject: ' + schemeitem.subject.name)
                                        logger.debug('schemeitem.subjecttype: ' + schemeitem.subjecttype.name)

                                        schemeitem.gradetype = gradetype
                                        schemeitem.sequence = sequence
                                        schemeitem.weightSE = weightSE
                                        schemeitem.weightCE = weightCE
                                        schemeitem.is_mandatory = is_mandatory
                                        schemeitem.is_combi = is_combi
                                        schemeitem.choicecombi_allowed = choicecombi_allowed
                                        schemeitem.has_practexam = has_practexam

                                        schemeitem.save(request=self.request)
                                        # logger.debug('subject.id: ' + str(subject.id) + ' .name: ' + str(subject.name) + ' .abbrev: ' + str(subject.abbrev) + ' .sequence: ' + str(subject.sequence))


                                        logger.debug('CORRECT???? schemeitem.school: ' + schemeitem.school.name)
                                        excel_data.append(row_data)

        return render(request, 'import_schemeitem.html', {"excel_data": excel_data})


@method_decorator([login_required], name='dispatch')
class ImportBirthcountryView(View):  # PR2018-08-31

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system_perm_admin
        param = {'display_school': True, 'display_user': True, 'override_school': request.user.role_str}
        headerbar_param = f.get_headerbar_param(request, param)
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'import_birthcountry.html', headerbar_param)

    def post(self, request):
        uploadedfile = request.FILES["excel_file"]
        # logger.debug('ImportDepartmentView uploadedfile.name: ' + str(uploadedfile.name))

        # you may put validations here to check extension or file size
        wb = openpyxl.load_workbook(uploadedfile)
        # PR2018-04-27 debug: DeprecationWarning: Call to deprecated function get_sheet_names (Use wb.sheetnames). Was:  ws_names = wb.get_sheet_names()
        ws_names = wb.sheetnames
        worksheet = wb.worksheets[0]
        excel_data = list()

        # iterating over the rows and
        # getting value from each cell in row
        self.sequence = 1
        for row in worksheet.iter_rows():
            row_data = list()
            for cell in row:
                row_data.append(str(cell.value))
                logger.debug('cell.value: ' + str(cell.value))
            logger.debug('row_data: ' + str(row_data))
            row_data.append(self.sequence)
            logger.debug('row_data: ' + str(row_data))
            self.sequence += 1

            #PR2018-04-28 debug: don't forget de brackets when creating an instance of the class
            birthcountry = Birthcountry()

            birthcountry.name = str(row_data[0])
            birthcountry.modified_by = request.user
            birthcountry.modified_at = timezone.now()

            birthcountry.save(request=self.request)

            excel_data.append(row_data)

        return render(request, 'import_birthcountry.html', {"excel_data": excel_data})



@method_decorator([login_required], name='dispatch')
class ImportBirthcityView(View):  # PR2018-09-01

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system_perm_admin
        param = {'display_school': True, 'display_user': True, 'override_school': request.user.role_str}
        headerbar_param = f.get_headerbar_param(request, param)
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'import_birthcity.html', headerbar_param)

    def post(self, request):
        uploadedfile = request.FILES["excel_file"]
        # logger.debug('ImportDepartmentView uploadedfile.name: ' + str(uploadedfile.name))

        # you may put validations here to check extension or file size
        wb = openpyxl.load_workbook(uploadedfile)
        # PR2018-04-27 debug: DeprecationWarning: Call to deprecated function get_sheet_names (Use wb.sheetnames). Was:  ws_names = wb.get_sheet_names()
        ws_names = wb.sheetnames
        worksheet = wb.worksheets[0]
        excel_data = list()

        # iterating over the rows and
        # getting value from each cell in row
        for row in worksheet.iter_rows():
            row_data = list()
            for cell in row:
                row_data.append(str(cell.value))
            # logger.debug('row_data: ' + str(row_data))

            #PR2018-04-28 debug: don't forget de brackets when creating an instance of the class
            birthcity = Birthcity()

            # get birthcountry
            countryname = str(row_data[0])
            if countryname is not None:
                logger.debug('countryname: ' + str(countryname) + ' Type: ' + str(type(countryname)))
                birthcountry = Birthcountry.objects.filter(name=countryname).first()
                logger.debug('birthcountry: ' + str(birthcountry) + ' Type: ' + str(type(birthcountry)))
                if birthcountry:

                    logger.debug('birthcountry: Type: ' + str(type(birthcountry)))

                    if birthcountry is not None:
                        logger.debug('birthcountry: ' + str(birthcountry) + ' Type: ' + str(type(birthcountry)))
                        birthcity.birthcountry = birthcountry
                        birthcity.name = str(row_data[1])
                        birthcity.modified_by = request.user
                        birthcity.modified_at = timezone.now()

                        birthcity.save(request=self.request)
                    else:
                        row_data[0] +=  " (not found)"
            else:
                row_data[0] = "no country"
            excel_data.append(row_data)

        return render(request, 'import_birthcity.html', {"excel_data": excel_data})


# ===================== Functions
def get_mapped_depbase_list(request_user_examyear):  # PR2018-12-12
    # this function returns a dict of the mapped department names.
    # it looks for the abbrev in the departments of this examyear
    # and returns the lowercase abbrev as key and its depbase_id as value
    # Map dep.abbrev to department.id {'vsbo': 4, 'havo': 5,'vwo': 6}
    dep_dict = {}
    deps = Department.objects.filter(examyear=request_user_examyear)
    for dep in deps:
        if dep.abbrev:
            dep_dict[dep.abbrev.lower()] = dep.base.id
    return dep_dict

def get_mapped_levelbase_list(request_user_examyear):  # PR2018-12-12
    # this function returns a dict of the mapped level names.
    # it looks for the abbrev in the levels of this examyear
    # and returns the lowercase abbrev as key and its levelbase_id as value
    # Map level.abbrev to level.id {'tkl': 1, 'pkl': 2,'pbl': 3}
    level_dict = {}
    levels = Level.objects.filter(examyear=request_user_examyear)
    for level in levels:
        if level.abbrev:
            level_dict[level.abbrev.lower()] = level.base.id
    return level_dict


def get_mapped_sectorbase_list(request_user_examyear):  # PR2018-12-12
    # this function returns a dict of the mapped sector names.
    # it looks for the abbrev in the sectors of this examyear
    # and returns the lowercase abbrev as key and its sectorbase_id as value
    # Map sector.abbrev to sector.id {'ec': 4, 'z&w': 5,'techn': 6}
    sector_dict = {}
    sectors = Sector.objects.filter(examyear=request_user_examyear)
    for sector in sectors:
        if sector.abbrev:
            sector_dict[sector.abbrev.lower()] = sector.base.id
    return sector_dict


def convert_nameslist_to_baseidlist(names_list, mapped_baselist):  # PR2018-12-12
    # PR2018-12-12 functioen replaces 'tkl,pkl,pbl' with ';1;2;3;'
    # mapped_sectorlist_dict is a separate function that gets the sectorbaseID's from this examyear

    base_id_list_str = ''
    if names_list:
        array = names_list.split(';')
        if array:
            for abbrev in array:
                # look up abbrev in mapped_sectorbaselist_dict
                if abbrev:
                    base_id = mapped_baselist.get(abbrev.lower())
                    if base_id:
                        base_id_list_str = base_id_list_str + str(base_id) + ';'
            # add ';' in font of string
            if base_id_list_str:
                base_id_list_str = ';' + base_id_list_str
    return base_id_list_str


def get_dep_from_abbrev(abbrev, request_user_examyear):  # PR2018-12-13
    dep = None
    if abbrev:
        if Department.objects.filter(abbrev__iexact=abbrev, examyear=request_user_examyear).count() == 1:
            dep = Department.objects.filter(abbrev__iexact=abbrev, examyear=request_user_examyear).first()
    return dep

def get_level_from_abbrev(abbrev, request_user_examyear):  # PR2018-12-13
    level = None
    if abbrev:
        if Level.objects.filter(abbrev__iexact=abbrev, examyear=request_user_examyear).count() == 1:
            level = Level.objects.filter(abbrev__iexact=abbrev, examyear=request_user_examyear).first()
    return level


def get_sector_from_abbrev(abbrev, request_user_examyear):  # PR2018-12-13
    sector = None
    if abbrev:
        if Sector.objects.filter(abbrev__iexact=abbrev, examyear=request_user_examyear).count() == 1:
            sector = Sector.objects.filter(abbrev__iexact=abbrev, examyear=request_user_examyear).first()
    return sector