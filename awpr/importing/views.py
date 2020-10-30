# PR2018-04-14
from django.contrib.auth.decorators import login_required # PR2018-04-01
from django.http import HttpResponse
from django.shortcuts import render, redirect #, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView, DeleteView, View, ListView, CreateView

from datetime import datetime

import json # PR2018-12-03

from schools.models import Department, Schoolbase, School, Schoolsetting
from subjects.models import Subject, Level, Sector, Subjecttype, Scheme, Schemeitem, Package
from students.models import Birthcountry, Birthcity, Student
from awpr import functions as f
from awpr import constants as c
from awpr import menus as am

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
        headerbar_param = am.get_headerbar_param(request, param)
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
       #  ws_names = wb.sheetnames
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

                    # iterating over the rows and
                    # getting value from each cell in row
                    skip_first_row = True # skip first row, it contains headers PR2019-02-16
                    for row in worksheet.iter_rows():
                        if skip_first_row:
                            skip_first_row = False
                        else:
                            row_data = list()
                            for cell in row:
                                row_data.append(str(cell.value))
                            # logger.debug('import_school_excel_view row_data: ' + str(row_data))

                            school = School()
                            school.examyear = request.user.examyear
                            school.code = row_data[0]
                            school.name = row_data[1]
                            school.abbrev = row_data[2]
                            school.article = row_data[3]
                            school.depbase_list = convert_nameslist_to_baseidlist(row_data[4], mapped_depbase_list)

                            # is_template stores the examyear.id. In that way there can only be one template per examyear / country
                            school_is_template = True if str(row_data[5]) == "1" else False
                            if school_is_template:
                                school.is_template = request.user.examyear.id

                            school.save(request=self.request)
                            # logger.debug('import_school_excel_view _school: ' + str(school.name))

                            excel_data.append(row_data)

        return render(request, 'import_school.html', {"excel_data": excel_data})


@method_decorator([login_required], name='dispatch')
class ImportDepartmentView(View):

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system_perm_admin
        param = {'display_school': True, 'display_user': True, 'override_school': request.user.role_str}
        headerbar_param = am.get_headerbar_param(request, param)

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
                skip_first_row = True # skip first row, it contains headers PR2019-02-16
                for row in worksheet.iter_rows():
                    if skip_first_row:
                        skip_first_row = False
                    else:
                        row_data = list()
                        for cell in row:
                            row_data.append(str(cell.value))
                        # logger.debug('row_data: ' + str(row_data))

                        #PR2018-04-28 debug: don't forget de brackets when creating an instance of the class
                        dep = Department()

                        # dep.base: new dep.base is created in dep.save
                        dep.examyear = request.user.examyear


                        dep.name = row_data[0]
                        dep.abbrev = row_data[1]
                        dep.sequence = int(str(row_data[2]))
                        dep.level_req = True if str(row_data[3]) == '1' else False
                        dep.sector_req = True if str(row_data[4]) == '1' else False
                        dep.level_caption = row_data[5]
                        dep.sector_caption = row_data[6]

                        dep.save(request=self.request)
                        # logger.debug('dep.id: ' + str(dep.id) + ' .name: ' + str(dep.name) + ' .abbrev: ' + str(dep.abbrev) + ' .sequence: ' + str(dep.sequence))

                        excel_data.append(row_data)

        return render(request, 'import_department.html', {"excel_data": excel_data})


@method_decorator([login_required], name='dispatch')
class ImportLevelView(View):

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system_perm_admin
        param = {'display_school': True, 'display_user': True, 'override_school': request.user.role_str}
        headerbar_param = am.get_headerbar_param(request, param)
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'import_level.html', headerbar_param)

    def post(self, request):
        uploadedfile = request.FILES["excel_file"]
        logger.debug('ImportDepartmentView uploadedfile.name: ' + str(uploadedfile.name))
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
                skip_first_row = True # skip first row, it contains headers PR2019-02-16
                for row in worksheet.iter_rows():
                    if skip_first_row:
                        skip_first_row = False
                    else:
                        row_data = list()
                        for cell in row:
                            row_data.append(str(cell.value))
                        # row_data: ['Praktisch Basisgerichte Leerweg', 'PBL', '1', 'vsbo']

                        logger.debug('row_data: ' + str(row_data))

                        #PR2018-04-28 debug: don't forget de brackets when creating an instance of the class
                        level = Level()

                        # new level.base is created in level.save
                        level.examyear = request.user.examyear

                        level.name = row_data[0]
                        level.abbrev = row_data[1]
                        level.sequence = int(str(row_data[2]))
                        level.depbase_list = convert_nameslist_to_baseidlist(row_data[3], mapped_depbase_list)

                        level.save(request=self.request)

                        excel_data.append(row_data)

        return render(request, 'import_level.html', {"excel_data": excel_data})


@method_decorator([login_required], name='dispatch')
class ImportSectorView(View):

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system_perm_admin
        param = {'display_school': True}
        headerbar_param = am.get_headerbar_param(request, param)
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
                skip_first_row = True # skip first row, it contains headers PR2019-02-16
                for row in worksheet.iter_rows():
                    if skip_first_row:
                        skip_first_row = False
                    else:
                        row_data = list()
                        for cell in row:
                            row_data.append(str(cell.value))
                        # row_data: ['Economie', 'ec', '1', 'vsbo']

                        # PR2018-04-28 debug: don't forget de brackets when creating an instance of the class
                        sector = Sector()

                        #sector.base = sector_base: New sector.base is created in sector.save
                        sector.examyear = request.user.examyear

                        sector.name = row_data[0]
                        sector.abbrev = row_data[1]
                        sector.sequence = int(str(row_data[2]))
                        sector.depbase_list = convert_nameslist_to_baseidlist(row_data[3], mapped_depbase_list)

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
        headerbar_param = am.get_headerbar_param(request, param)
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
                    skip_first_row = True # skip first row, it contains headers PR2019-02-16
                    for row in worksheet.iter_rows():
                        if skip_first_row:
                            skip_first_row = False
                        else:
                            row_data = list()
                            for cell in row:
                                row_data.append(str(cell.value))
                            # logger.debug('row_data: ' + str(row_data))
                            # [‘Gemeenschappelijk deel’, ‘Gemeensch. ’, ‘gmd’, ‘1’, ‘vsbo;havo;vwo’]

                            # PR2018-04-28 debug: don't forget de brackets when creating an instance of the class
                            subjecttype = Subjecttype()

                            # new subjecttype.base is created in subjecttype.save
                            subjecttype.examyear = request.user.examyear
                            subjecttype.name = row_data[0]
                            subjecttype.abbrev = row_data[1]
                            subjecttype.code = row_data[2]
                            subjecttype.sequence = int(str(row_data[3]))
                            subjecttype.has_prac = True if str(row_data[4]) == '1' else False  # has practical exam
                            subjecttype.has_pws =True if str(row_data[5]) == '1' else False  # has profielwerkstuk or sectorwerkstuk
                            subjecttype.one_allowed =True if str(row_data[6]) == '1' else False  # if true: only one subject with this Subjecttype allowed per student
                            subjecttype.depbase_list = convert_nameslist_to_baseidlist(row_data[7], mapped_depbase_list)

                            subjecttype.save(request=self.request)

                            excel_data.append(row_data)

        return render(request, 'import_subjecttype.html', {"excel_data": excel_data})


# ===== Import Subjectse ===================
@method_decorator([login_required], name='dispatch')
class ImportSubjectView(View):

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system
        param = {'display_school': True, 'display_user': True, 'override_school': request.user.role_str}
        headerbar_param = am.get_headerbar_param(request, param)
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
                    skip_first_row = True # skip first row, it contains headers PR2019-02-16
                    for row in worksheet.iter_rows():
                        if skip_first_row:
                            skip_first_row = False
                        else:
                            row_data = list()
                            for cell in row:
                                row_data.append(str(cell.value))
                            # row_data: ['Nederlandse taal', 'ne', '10', 'vsbo']

                            # PR2018-04-28 debug: don't forget de brackets when creating an instance of the class
                            subject = Subject()

                            # new subject.base is created in subject.save
                            subject.examyear = request.user.examyear
                            subject.name = row_data[0]
                            subject.abbrev = row_data[1]
                            subject.sequence = int(str(row_data[2]))
                            subject.depbase_list =  convert_nameslist_to_baseidlist(row_data[3], mapped_depbase_list)

                            subject.save(request=self.request)

                            excel_data.append(row_data)

        return render(request, 'import_subject.html', {"excel_data": excel_data})

# ===== Import Scheme ===================
@method_decorator([login_required], name='dispatch')
class ImportSchemeView(View): # PR2018-11-10

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system
        param = {'display_school': True, 'display_user': True, 'override_school': request.user.role_str}
        headerbar_param = am.get_headerbar_param(request, param)
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
                    # logger.debug('mapped_depbase_list: ' + str(mapped_depbase_list))
                    mapped_levelbase_list = get_mapped_levelbase_list(request.user.examyear)
                    # logger.debug('mapped_levelbase_list: ' + str(mapped_levelbase_list))
                    mapped_sectorbase_list = get_mapped_sectorbase_list(request.user.examyear)
                    # logger.debug('mapped_sectorbase_list: ' + str(mapped_sectorbase_list))

                    # iterating over the rows and
                    skip_first_row = True # skip first row, it contains headers PR2019-02-16
                    for row in worksheet.iter_rows():
                        if skip_first_row:
                            skip_first_row = False
                        else:
                            # get value from each cell in row
                            row_data = list()
                            for cell in row:
                                row_data.append(str(cell.value))
                            # row_data: ['vsbo', 'TKL', 'tech']
                            logger.debug('--- row_data[0]: ' + str(row_data[0]))

                            dep_abbrev = ''
                            department = None
                            if row_data[0]:
                                depbase_id = mapped_depbase_list.get(str(row_data[0]).lower(), None)
                                # logger.debug('depbase_id: ' + str(depbase_id))
                                if depbase_id:
                                    # skip if more than 1 record found
                                    # logger.debug('count: ' + str(Department.objects.filter(base__id=depbase_id, examyear=request.user.examyear).count()))

                                    if Department.objects.filter(base__id=depbase_id, examyear=request.user.examyear).count() == 1:
                                        department = Department.objects.filter(base__id=depbase_id, examyear=request.user.examyear).first()
                                        #logger.debug('department: ' + str(department))
                                        if department:
                                            dep_abbrev = department.abbrev

                            level_abbrev = ''
                            level = None
                            # logger.debug('--- row_data[1]: ' + str(row_data[1]))
                            if row_data[1] is not None:
                                levelbase_id = mapped_levelbase_list.get(str(row_data[1]).lower(), None)
                                # logger.debug('levelbase_id: ' + str(levelbase_id))
                                if levelbase_id:
                                    # skip if more than 1 record found
                                    # logger.debug('count: ' + str(Level.objects.filter(base__id=levelbase_id, examyear=request.user.examyear).count()))

                                    if Level.objects.filter(base__id=levelbase_id, examyear=request.user.examyear).count() == 1:
                                        level = Level.objects.filter(base__id=levelbase_id, examyear=request.user.examyear).first()
                                        # logger.debug('level: ' + str(level))
                                        if level:
                                            level_abbrev = level.abbrev.lower()
                                            logger.debug('level_abbrev: ' + str(level_abbrev))

                            sector_abbrev = ''
                            sector = None
                            # logger.debug('--- row_data[2]: ' + str(row_data[2]))
                            if row_data[2] is not None:
                                sectorbase_id = mapped_sectorbase_list.get(str(row_data[2]).lower(), None)
                                # logger.debug('sectorbase_id: ' + str(sectorbase_id))
                                if sectorbase_id:
                                    # skip if more than 1 record found
                                    # logger.debug('count: ' + str(Sector.objects.filter(base__id=sectorbase_id, examyear=request.user.examyear).count()))

                                    if Sector.objects.filter(base__id=sectorbase_id, examyear=request.user.examyear).count() == 1:
                                        sector = Sector.objects.filter(base__id=sectorbase_id, examyear=request.user.examyear).first()
                                        # logger.debug('sector: ' + str(sector))
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

                            # logger.debug('dep_abbrev: ' + str(dep_abbrev))
                            #  logger.debug('level_abbrev: ' + str(level_abbrev))
                            # logger.debug('sector_abbrev: ' + str(sector_abbrev))

                            scheme.name = Scheme.create_scheme_name(
                                dep_abbrev=dep_abbrev,
                                level_abbrev=level_abbrev,
                                sector_abbrev=sector_abbrev )

                            scheme.fields = row_data[3]

                            # logger.debug('scheme.name: ' + str(scheme.name))

                            scheme.save(request=self.request)
                            # logger.debug('subject.id: ' + str(subject.id) + ' .name: ' + str(subject.name) + ' .abbrev: ' + str(subject.abbrev) + ' .sequence: ' + str(subject.sequence))

                            excel_data.append(row_data)

        return render(request, 'import_scheme.html', {"excel_data": excel_data})


# ===== Import Scheme items ===================
@method_decorator([login_required], name='dispatch')
class ImportSchemeitemView(View):  # PR2018-11-10

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system
        param = {
            'display_school': True,
            'display_dep': True,
            'display_user': True
        }
        headerbar_param = am.get_headerbar_param(request, param)
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'import_schemeitem.html', headerbar_param)


# ===== AjaxImportSSIupload ===================
@method_decorator([login_required], name='dispatch')
class AjaxImportSSIupload(View):  # PR2019-02-15

    def post(self,request):
        logger.debug(' ===== Import Scheme items =========')
        rowcount = 0
        # PR2019-02-17 speed test
        time_start = datetime.datetime.now()
        params = {}
        # check if request.user.country is parent of request.user.examyear PR2018-10-18
        if request.user is not None:
            if request.user.examyear is not None and request.user.country is not None:
                if request.user.examyear.country.pk == request.user.country.pk:

                    # logger.debug(request.POST['schemeitems'])
                    schemeitems = json.loads(request.POST['schemeitems'])
                    # Excel file colums:
                    # 0. dep_abbrev,
                    # 1. lvl_abbrev,
                    # 2. sct_aabrev,
                    # 3. subject_abbrev,
                    # 4. subjecttype_name,
                    # 5. gradetype_id,
                    # 6. weightSE,
                    # 7. weightCE,
                    # 8. is_mandatory,
                    # 9. is_combi,
                    # 10. extra_count_allowed,
                    # 11. extra_nocount_allowed,
                    # 12. choicecombi_allowed,
                    # 13. has_practexam,
                    # 14. sequence

                    # ['Vwo', '', 'n&t', 'pws', 'Profiel werkstuk', '1', '1', '0', '1', '1', '1', '1', '0', '0', '4200', 0, 0],

                    # logger.debug('schemeitems')
                    # logger.debug(schemeitems)

                    # Map subject.abbrev to subject.id {'ne': 3}
                    # because 'ne' is different in Vsbo and Havo/Vwo, also depbase_list must be checked
                    subject_list = []
                    for subject in Subject.objects.filter(examyear=request.user.examyear):
                        subject_list.append({'id': subject.id, 'abbrev': subject.abbrev.lower(),'depbase_list': subject.depbase_list})
                    # subject_list: [{'id': 95, 'abbrev': 'ne', 'depbase_list': ';11;'}, ...

                    # Map schemes_list by dep, lvl, sct
                    schemes_list = Scheme.get_lookup_scheme_list(request.user.examyear)  # PR2019-02-17
                    # logger.debug(str(schemes_list))

                    # Map subjecttype.name
                    subjtype_list = Subjecttype.get_lookup_subjtype_list(request.user.examyear)  # PR2019-02-17
                    # logger.debug(str(subjtype_list))

                    # iterating over the rows and getting value from each cell in row
                    for row in schemeitems:
                        # get scheme_id from schemes_list
                        dep_abbrev = row[0]
                        lvl_abbrev = row[1]
                        sct_abbrev = row[2]
                        subj_abbrev = row[3]

                        scheme_id = get_scheme_id_from_abbrevs(dep_abbrev, lvl_abbrev, sct_abbrev, schemes_list) # PR2018-02-14
                        # logger.debug('scheme_id: ' + str(schemes_list) + ' type: ' + str(type(schemes_list)))
                        # get scheme
                        scheme = Scheme.objects.filter(id=scheme_id).first()

                        if scheme:
                            logger.debug('scheme: ' + str(scheme) + ' type: ' + str(type(scheme)))

                            # get subject fom abbrev and depbase_id
                            # subject_id = int(subject_dict.get(str(subj_abbrev), '-1'))
                            subject = None
                            for dict in subject_list:
                                if dict['abbrev'] == subj_abbrev:
                                    if dict['depbase_list']:
                                        depbase_delim = ';' + str(scheme.department.base_id) + ';'
                                        if dict['depbase_list'].find(depbase_delim) != -1:
                                            subject_id = int(dict['id'])
                                            subject = Subject.objects.filter(id=subject_id).first()
                                            break
                            if subject:
                                logger.debug('subject: ' + str(subject) + ' type: ' + str(type(subject)))
                                # get subjecttype
                                subjtype_name = str(row[4])
                                subjtype_id = get_subjtype_id_from_name(subjtype_name, subjtype_list)
                                logger.debug('subjtype_name: ' + str(subjtype_name) + ' subjtype_id: ' + str(subjtype_id) + ' type: ' + str(type(subjtype_id)))

                                subjecttype = Subjecttype.objects.filter(id=subjtype_id).first()
                                #has_pws = BooleanField(default=False)  # has profielwerkstuk or sectorwerkstuk
                                #one_allowed = BooleanField(

                                if subjecttype:
                                    logger.debug('subjecttype: ' + str(subjecttype) + ' type: ' + str(type(subjecttype)))

                                    #  0 Scheme 1 subject 2 Subjecttype 3 Gradetype 4 Sequence 5 weightSE 6 weightCE
                                    # 7 is_mandatory 8 is_combi 9 choicecombi_allowed 10 has_practexam
                                    rowcount = rowcount + 1
                                    logger.debug(str(rowcount) + ': ' + str(scheme.name) + ' ' + str(subject.abbrev) + ' ' + str(subjecttype.abbrev))

                                    gradetype = int(row[5])
                                    weightSE = int(row[6])
                                    weightCE = int(row[7])
                                    is_mandatory = True if str(row[8]) == '1' else False
                                    is_combi = True if str(row[9]) == '1' else False
                                    logger.debug('is_combi: ' + str(is_combi) + ' type: ' + str(type(is_combi)))

                                    extra_count_allowed = True if str(row[10]) == '1' else False
                                    extra_nocount_allowed = True if str(row[11]) == '1' else False

                                    choicecombi_allowed = True if str(row[12]) == '1' else False
                                    has_practexam = True if str(row[13]) == '1' else False
                                    sequence = int(str(row[14]))
                                    logger.debug('sequence: ' + str(sequence) + ' type: ' + str(type(sequence)))

                                    # create new schemeitem
                                    schemeitem = Schemeitem()

                                    schemeitem.scheme = scheme
                                    schemeitem.subject = subject
                                    schemeitem.subjecttype = subjecttype

                                    schemeitem.gradetype = gradetype
                                    schemeitem.weightSE = weightSE
                                    schemeitem.weightCE = weightCE
                                    schemeitem.is_mandatory = is_mandatory
                                    schemeitem.is_combi = is_combi

                                    schemeitem.extra_count_allowed = extra_count_allowed
                                    schemeitem.extra_nocount_allowed = extra_nocount_allowed

                                    schemeitem.choicecombi_allowed = choicecombi_allowed
                                    schemeitem.has_practexam = has_practexam
                                    schemeitem.sequence = sequence

                                    logger.debug('schemeitem.sequence: ' + str(schemeitem.sequence))
                                    # save new schemeitem
                                    schemeitem.save(request=self.request)

                                    logger.debug('saved schemeitem.sequence: ' + str(schemeitem.sequence))
                                    if schemeitem is None:
                                        params['error'] = _('An error occurred. This action cannot be completed.')

        # PR2019-02-17 speed test
        params['created'] = str(rowcount)
        params['elapsed'] = str(datetime.datetime.now() - time_start)
        return HttpResponse(json.dumps(params, cls=f.LazyEncoder))


# ===== Import Package ===================
@method_decorator([login_required], name='dispatch')
class ImportPackageView(View): # PR2019-02-24

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system
        param = {'display_school': True, 'display_user': True}
        headerbar_param = am.get_headerbar_param(request, param)
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'import_package.html', headerbar_param)

    def post(self,request):
        uploadedfile = request.FILES["excel_file"]
        wb = openpyxl.load_workbook(uploadedfile)
        # ws_names = wb.sheetnames
        worksheet = wb.worksheets[0]
        excel_data = list()

        logger.debug('=== Import Package ========')

        # check if request.user.country is parent of request.user.examyear PR2018-10-18
        if request.user is not None:
            if request.user.examyear is not None and request.user.country is not None:
                if request.user.examyear.country.pk == request.user.country.pk:
                    if request.user.schoolbase is not None:
                        schoolbase_id = request.user.schoolbase.id
                        if School.objects.filter(base__id=schoolbase_id, examyear=request.user.examyear).count() == 1:
                            school = School.objects.filter(base__id=schoolbase_id, examyear=request.user.examyear).first()

                            # Map schemes_list by dep, lvl, sct
                            schemes_list = Scheme.get_lookup_scheme_list(request.user.examyear)  # PR2019-02-17
                            # logger.debug(str(schemes_list))

                            # iterating over the rows and
                            # dep_abbrev, level_abbrev, sector_abbrev, name
                            skip_first_row = True # skip first row, it contains headers PR2019-02-16
                            for row in worksheet.iter_rows():
                                if skip_first_row:
                                    skip_first_row = False
                                else:
                                    # get value from each cell in row
                                    row_data = list()
                                    for cell in row:
                                        row_data.append(str(cell.value))
                                    # row_data: ['vsbo', 'TKL', 'tech', 'TKL tech alg tech']
                                    logger.debug('--- row_data[0]: ' + str(row_data[0]))

                                    # get scheme_id from schemes_list
                                    scheme_id = get_scheme_id_from_abbrevs(row_data[0], row_data[1], row_data[2], schemes_list)
                                    scheme = Scheme.objects.filter(id=scheme_id).first()

                                    if scheme:
                                        package = Package()

                                        package.school = school
                                        package.scheme = scheme
                                        package.name = row_data[3]

                                        package.modified_by = request.user
                                        package.modified_at = timezone.now()

                                        package.save(request=self.request)

                                        logger.debug('package.id: ' + str(package.id) + ' .name: ' + str(package.name))

                                        excel_data.append(row_data)

        return render(request, 'import_package.html', {"excel_data": excel_data})


# ===== Import Packagiteme ===================
@method_decorator([login_required], name='dispatch')
class ImportPackageitemView(View): # PR2019-02-24

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system
        param = {'display_school': True, 'display_user': True}
        headerbar_param = am.get_headerbar_param(request, param)
        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'import_packageitem.html', headerbar_param)

    def post(self,request):
        uploadedfile = request.FILES["excel_file"]
        wb = openpyxl.load_workbook(uploadedfile)
        # ws_names = wb.sheetnames
        worksheet = wb.worksheets[0]
        excel_data = list()

        logger.debug('=== Import Package items ========')

        # check if request.user.country is parent of request.user.examyear PR2018-10-18
        if request.user is not None:
            if request.user.examyear is not None and request.user.country is not None:
                if request.user.examyear.country.pk == request.user.country.pk:
                    if request.user.schoolbase is not None:
                        school = School.objects.filter(base__id=request.user.schoolbase.id,
                                                       examyear=request.user.examyear).first()
                        if school is not None:
                            # Map schemes_list by dep, lvl, sct
                            schemes_list = Scheme.get_lookup_scheme_list(request.user.examyear)  # PR2019-02-17
                            logger.debug(str(schemes_list))

                            # iterating over the rows
                            # package_name, dep_abbrev, level_abbrev, sector_abbrev, subject_abbrev, subjecttype
                            row_count = 0
                            skip_first_row = True # skip first row, it contains headers PR2019-02-16
                            for row in worksheet.iter_rows():
                                if skip_first_row:
                                    skip_first_row = False
                                else:
                                    # get value from each cell in row
                                    row_data = []
                                    for cell in row:
                                        row_data.append(str(cell.value))
                                    # row_data: ['vsbo', 'TKL', 'tech', 'TKL tech alg tech']
                                    package_name = row_data[0]
                                    dep_abbrev = row_data[1]
                                    lvl_abbrev = str(row_data[2])
                                    sct_abbrev = row_data[3]
                                    subject_abbrev = row_data[4]
                                    subjecttype = row_data[5]
                                    logger.debug('--- package_name: ' +package_name)
                                    logger.debug('--- dep_abbrev: ' +dep_abbrev)
                                    logger.debug('--- lvl_abbrev: <' + lvl_abbrev + '> ' + str(type(lvl_abbrev)))
                                    logger.debug('--- lvl_abbrev: LEN ' + str(len(lvl_abbrev)))
                                    logger.debug('--- row_data[2]: <' + str(len(row_data[2])) + '>')
                                    logger.debug('--- row_data[2]: LEN ' + str(len(row_data[2])))
                                    logger.debug('--- row_data[2]: type ' + str(type(row_data[2])))
                                    logger.debug('--- sct_abbrev: ' +sct_abbrev)
                                    logger.debug('--- subject_abbrev: ' +subject_abbrev)
                                    logger.debug('--- subjecttype: ' +subjecttype)

                                    logger.debug('-++ lvl_abbrev bool: <' + str(bool(lvl_abbrev)) +'>' )

                                    # get dep
                                    dep = Department.get_dep_by_abbrev(dep_abbrev, request.user.examyear)  # PR2019-02-26

                                    scheme = Scheme.get_scheme_by_abbrevs(dep_abbrev, lvl_abbrev, sct_abbrev, request.user.examyear)

                                    if scheme is None:
                                        logger.debug('--- scheme: None')
                                    else:
                                        logger.debug('--- scheme: ' + scheme.name)

                                        depbase_id_delim = ';' + str(scheme.department.base.pk) + ';'
                                        subject = Subject.objects.filter(
                                            examyear=request.user.examyear,
                                            abbrev__iexact=subject_abbrev,
                                            depbase_list__contains=depbase_id_delim).first()
                                        if subject is None:
                                            logger.debug('--- subject: None')
                                        else:
                                            logger.debug('--- subject: ' + subject.name)

                                        subjecttype = Subjecttype.objects.filter(
                                            examyear=request.user.examyear,
                                            name__iexact=subjecttype,
                                            depbase_list__contains=depbase_id_delim).first()
                                        if subjecttype:
                                            logger.debug('--- subjecttype: ' + subjecttype.name)
                                        else:
                                            logger.debug('--- subjecttype: None')



                                        #package = Package()

                                       # package.school = school
                                        #package.scheme = scheme
                                        #package.name = row_data[3]

                                        #package.modified_by = request.user
                                        #package.modified_at = timezone.now()

                                        #package.save(request=self.request)

                                        #logger.debug('package.id: ' + str(package.id) + ' .name: ' + str(package.name))

                                        excel_data.append(row_data)
                                        row_count = row_count + 1
                                        logger.debug('--- row_count: ' + str(row_count))

                                    logger.debug('')
        return render(request, 'import_packageitem.html', {"excel_data": excel_data})


@method_decorator([login_required], name='dispatch')
class ImportBirthcountryView(View):  # PR2018-08-31

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_system_perm_admin
        param = {'display_school': True, 'display_user': True, 'override_school': request.user.role_str}
        headerbar_param = am.get_headerbar_param(request, param)
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
        headerbar_param = am.get_headerbar_param(request, param)
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


def get_scheme_id_from_abbrevs(dep_abbrev, lvl_abbrev, sct_abbrev, schemes_list):  # PR2018-02-17
    # logger.debug('get_scheme_id_from_abbrevs: ' + dep_abbrev + ' - ' + lvl_abbrev + ' - ' + sct_abbrev )
    scheme_id = None
    for dict in schemes_list:
        found = False
        if 'dep' in dict:
            if dep_abbrev:
                if dict['dep'] == dep_abbrev.lower():
                    lvl_is_ok = False
                    if 'lvl' in dict:
                        if lvl_abbrev:
                            lvl_is_ok =( dict['lvl'] == lvl_abbrev.lower())
                    else:
                        lvl_is_ok = True
                    if lvl_is_ok:
                        if 'sct' in dict:
                            if sct_abbrev:
                                 found = (dict['sct'] == sct_abbrev.lower())
                        else:
                            found = True
        if found:
            if 'id' in dict:
                scheme_id = dict['id']
            break
    return scheme_id


def get_dep_from_abbrev(abbrev, examyear):  # PR2018-12-13
    dep = None
    if abbrev:
        if Department.objects.filter(abbrev__iexact=abbrev, examyear=examyear).count() == 1:
            dep = Department.objects.filter(abbrev__iexact=abbrev, examyear=examyear).first()
    return dep


def get_level_from_abbrev(abbrev, examyear):  # PR2018-12-13
    level = None
    if abbrev:
        if Level.objects.filter(abbrev__iexact=abbrev, examyear=examyear).count() == 1:
            level = Level.objects.filter(abbrev__iexact=abbrev, examyear=examyear).first()
    return level


def get_sector_from_abbrev(abbrev, examyear):  # PR2018-12-13
    sector = None
    if abbrev:
        if Sector.objects.filter(abbrev__iexact=abbrev, examyear=examyear).count() == 1:
            sector = Sector.objects.filter(abbrev__iexact=abbrev, examyear=examyear).first()
    return sector

def get_subjecttype_from_name(name, scheme):  # PR2018-02-14
    subjecttype = None
    if scheme:
        depbase_id_delim = ';' + str(scheme.department.base_id) + ';'
        examyear = scheme.department.examyear
        subjecttype = Subjecttype.objects.filter(
            examyear=examyear,
            name__iexact=name,
            depbase_list__contains=depbase_id_delim
        ).first()
    return subjecttype



def get_subjtype_id_from_name(subjtype_name, subjtype_list):  # PR2018-02-17
    # logger.debug('get_subjtype_id_from_name: ' + subjtype_name )
    # {'id': 1, 'name': 'gemeenschappelijk deel'}
    subjtype_id = None
    for dict in subjtype_list:
        found = False
        if 'id' in dict and 'name' in dict:
            if dict['name'] == subjtype_name.lower():
                subjtype_id = dict['id']
                break
    return subjtype_id



