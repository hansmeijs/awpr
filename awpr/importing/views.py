# PR2018-04-14
from django.contrib.auth.decorators import login_required # PR2018-04-01
from django.db.models import Q
from django.shortcuts import render, redirect #, get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from awpr import functions as af
from schools import models as sch_mod
from students import models as stud_mod
from subjects import models as subj_mod

# PR2018-04-27
import logging
logger = logging.getLogger(__name__)

# PR2018-05-06


# PR2018-04-27 import Excel file from "How to upload and process the Excel file in Django" http://thepythondjango.com/upload-process-excel-file-django/
import openpyxl


@method_decorator([login_required], name='dispatch')
class ImportAllView(View):  #PR2020-12-13

    def get(self, request):
        # permission: user.is_authenticated AND user.is_role_adm_or_sys_and_perm_adm_or_sys
        header_text = _('Upload') + ' ' + str(_('All').lower())
        return render(request, 'import.html', {'header': header_text})

    def post(self,request):
        uploadedfile = request.FILES["excel_file"]
        logger.debug('ImportDepartmentView uploadedfile.name: ' + str(uploadedfile.name))
        logger.debug('request.user.country: ' + str(request.user.country))

# get examyear from settings
        sel_examyear_instance, selected_dict_has_changed, may_select_examyear = af.get_sel_examyear_instance(request)

        excel_data = list()
        # check if request.user.country is parent of sel_examyear_instance PR2018-10-18
        if sel_examyear_instance is not None and request.user.country is not None:
            if sel_examyear_instance.country.id == request.user.country.id:
                # you may put validations here to check extension or file size
                wb = openpyxl.load_workbook(uploadedfile)
                # PR2018-04-27 debug: DeprecationWarning: Call to deprecated function get_sheet_names (Use wb.sheetnames). Was:  ws_names = wb.get_sheet_names()
                # ws_names = wb.sheetnames
                mapped = {'depbase': {}, 'level': {}, 'sector': {}, 'subjecttype': {}, 'subject': {}, 'scheme': {},
                                'package': {}}

                logger.debug('wb.worksheets: ' + str(wb.worksheets))
                # iterate through trhis tuple to make sure the data are imported in the right order
                for ws_name in ('department', 'level', 'sector', 'subjecttype', 'subject', 'scheme', 'schemeitem',
                                'package', 'packageitem', 'birthcountry', 'birthplace', 'schoolCUR', 'schoolSXM'):

                    excel_data.append('----- ' + ws_name)
                    index = -1
                    for wb_index, wb_sheetname in enumerate(wb.sheetnames):
                        if wb_sheetname == ws_name:
                            index = wb_index
                            break
                    worksheet = None
                    if index > -1:
                        worksheet = wb.worksheets[index]

                    if worksheet:
                        # iterating over the rows and getting value from each cell in row
                        # skip first row, it contains headers PR2019-02-16
                        skip_first_row = True
                        for row in worksheet.iter_rows():
                            if skip_first_row:
                                skip_first_row = False
                            else:
                                row_data = list()
                                for cell in row:
                                    row_data.append(str(cell.value))

                                ImportData(ws_name, row_data, excel_data, mapped, sel_examyear_instance, request)

        header_text = _('Upload') + ' ' + str(_('All').lower())
        return render(request, 'import.html', {"excel_data": excel_data, 'header': header_text})


def ImportData(ws_name, row_data, excel_data, mapped, sel_examyear, request):  #PR2020-12-13

    #try:
    if True:
        requsr_country = request.user.country
        if ws_name == 'department':
            logger.debug ('-------------------  department ----------------- sel_examyear: ' + str(sel_examyear))
            # 0: name 1: code 2: abbrev 3: sequence 4: level_req 5: sector_req 6: level_caption 7:sector_caption
            code = str(row_data[1]) if row_data[1] else None
            logger.debug ('code: ' + str(code))
            if code:
    # - check if depbase with this code already exists in this country. If not: create
                depbase = sch_mod.Departmentbase.objects.filter(country=requsr_country, code=code).order_by('-pk').first()
                logger.debug ('depbase found: ' + str(depbase))
                if depbase is None:
                    depbase = sch_mod.Departmentbase.objects.create(country=requsr_country, code=code)
                    logger.debug ('depbase created: ' + str(depbase))
    # - check if department with this depbase already exists in this examyear. If not: create
                department = sch_mod.Department.objects.filter(base=depbase, examyear=sel_examyear).order_by('-pk').first()
                logger.debug ('department found: ' + str(department))
                if department is None:
                    name = str(row_data[0]) if row_data[0] else None
                    #code = str(row_data[1]) if row_data[1] else None
                    abbrev = str(row_data[2]) if row_data[1] else None
                    sequence = int(str(row_data[3])) if row_data[2] else 9999
                    level_req = True if str(row_data[4]) == '1' else False
                    sector_req = True if str(row_data[5]) == '1' else False
                    level_caption = str(row_data[6]) if row_data[5] else None
                    sector_caption = str(row_data[7]) if row_data[6] else None
                    logger.debug ('depbase values: abbrev = ' + str(abbrev))
                    #PR2018-04-28 debug: don't forget de brackets when creating an instance of the class
                    department = sch_mod.Department(
                        base=depbase,
                        examyear=sel_examyear,
                        name=name,
                        abbrev=abbrev,
                        sequence=sequence,
                        level_req=level_req,
                        sector_req=sector_req,
                        level_caption=level_caption,
                        sector_caption=sector_caption
                    )
                    department.save(request=request)
                    logger.debug ('depbase created = ' + str(department))
                    excel_data.append(row_data)
                if department and department.base and department.base.code:
                    mapped['depbase'][department.base.code.lower()] = department.base.id

        elif ws_name == 'level':
            # check if level already exists
            abbrev = str(row_data[1]) if row_data[1] else None
            if abbrev:
                # check if level already exists
                levels = subj_mod.Level.objects.filter(
                    examyear=sel_examyear,
                    abbrev__iexact=abbrev
                )
                if levels:
                    level = levels[0]
                else:
                    # When new record: First create base record. base.id is used in Department. Create also saves new record
                    base = subj_mod.Levelbase.objects.create(country=requsr_country)

                    name = str(row_data[0]) if row_data[0] else None
                    #abbrev = str(row_data[1]) if row_data[1] else None
                    sequence = int(str(row_data[2])) if row_data[2] else 9999
                    depbases = get_depbase_id_list_from_nameslist(row_data[3], mapped)

                    #PR2018-04-28 debug: don't forget de brackets when creating an instance of the class
                    level = subj_mod.Level(
                        base=base,
                        examyear=sel_examyear,
                        name=name,
                        abbrev=abbrev,
                        sequence=sequence,
                        depbases=depbases
                    )
                    level.save(request=request)
                    excel_data.append(row_data)
                if level and level.abbrev:
                    mapped[ws_name][level.abbrev.lower()] = level.pk

        elif ws_name == 'sector':
            # check if sector already exists
            abbrev = str(row_data[1]) if row_data[1] else None
            if abbrev:
                # check if sector already exists
                sectors = subj_mod.Sector.objects.filter(
                    examyear=sel_examyear,
                    abbrev__iexact=abbrev
                )
                if sectors:
                    sector = sectors[0]
                else:
                    # create base record. Create also saves new record
                    base = subj_mod.Sectorbase.objects.create(country=requsr_country)

                    name = str(row_data[0]) if row_data[0] else None
                    #abbrev = str(row_data[1]) if row_data[1] else None
                    sequence = int(str(row_data[2])) if row_data[2] else 9999
                    depbases = get_depbase_id_list_from_nameslist(row_data[3], mapped)

                    sector = subj_mod.Sector(
                        base=base,
                        examyear=sel_examyear,
                        name=name,
                        abbrev=abbrev,
                        sequence=sequence,
                        depbases=depbases
                    )
                    sector.save(request=request)
                    excel_data.append(row_data)
                if sector and sector.abbrev:
                    mapped[ws_name][sector.abbrev.lower()] = sector.pk
                #logger.debug('sector.id: ' + str(sector.pk) + ' name: ' + str(sector.name) + ' .abbrev: ' + str(sector.abbrev))

        elif ws_name == 'subjecttype':
            # check if subjecttype already exists
            name = str(row_data[0]) if row_data[0] else None
            if name:
                # check if subjecttype already exists
                subjecttypes = subj_mod.Subjecttype.objects.filter(
                    examyear=sel_examyear,
                    name__iexact=name
                )
                if subjecttypes:
                    subjecttype = subjecttypes[0]
                else:
                    # create base record.
                    base = subj_mod.Subjecttypebase.objects.create(country=requsr_country)

                    #name = str(row_data[0]) if row_data[0] else None
                    abbrev = str(row_data[1]) if row_data[1] else None
                    code = str(row_data[2]) if row_data[2] else None
                    sequence = int(str(row_data[3])) if row_data[3] else 9999
                    has_prac = True if str(row_data[4]) == '1' else False  # has practical exam
                    has_pws = True if str(row_data[5]) == '1' else False  # has profielwerkstuk or sectorwerkstuk
                    one_allowed = True if str(row_data[6]) == '1' else False  # if true: only one subject with this Subjecttype allowed per student
                    depbases = get_depbase_id_list_from_nameslist(row_data[7], mapped)

                    subjecttype = subj_mod.Subjecttype(
                        base=base,
                        examyear=sel_examyear,
                        name=name,
                        abbrev=abbrev,
                        code=code,
                        sequence=sequence,
                        has_prac=has_prac,
                        has_pws=has_pws,
                        one_allowed=one_allowed,
                        depbases=depbases
                    )
                    subjecttype.save(request=request)
                    excel_data.append(row_data)
                if subjecttype and subjecttype.name:
                    mapped[ws_name][subjecttype.name.lower()] = subjecttype.pk
                #logger.debug('subjecttype.id: ' + str(subjecttype.pk) + ' name: ' + str(subjecttype.name) + ' .abbrev: ' + str(subjecttype.abbrev))

        elif ws_name == 'subject':
            code = str(row_data[1]) if row_data[1] else None
            if code:
                # check if subject already exists
                subject = get_subject(code, sel_examyear)
                if subject is None:
                    name = str(row_data[0]) if row_data[0] else None
                    #code = str(row_data[1]) if row_data[1] else None
                    sequence = int(str(row_data[2])) if row_data[2] else 9999
                    depbases = get_depbase_id_list_from_nameslist(row_data[3], mapped)

                    # create base record with code. Create also saves new record
                    base = subj_mod.Subjectbase.objects.create(
                        country=requsr_country,
                        code=code
                    )

                    # PR2018-04-28 debug: don't forget de brackets when creating an instance of the class
                    subject = subj_mod.Subject(
                        base=base,
                        examyear=sel_examyear,
                        name=name,
                        sequence=sequence,
                        depbases=depbases
                    )
                    subject.save(request=request)
                    excel_data.append(row_data)
                if subject and subject.base.code:
                    mapped[ws_name][subject.base.code.lower()] = subject.pk
                #logger.debug('subject.id: ' + str(subject.pk) + ' name: ' + str(subject.name) + ' .code: ' + str(subject.base.code))

        elif ws_name == 'scheme':
            # 0: depbase_code 1: level_abbrev 2: sector_abbrev 3: fields
            logger.debug('------------')
            depbase_code = str(row_data[0]) if row_data[0] else 'None'
            logger.debug('depbase_code: ' + str(depbase_code))
            if depbase_code:
                level_abbrev = str(row_data[1]) if row_data[1] else 'None'
                sector_abbrev = str(row_data[2]) if row_data[2] else 'None'
                logger.debug('row_data[1]: ' + str(row_data[1]) + ' ' + str(type(row_data[1])))
                logger.debug('level_abbrev: ' + str(level_abbrev) + ' ' + str(type(level_abbrev)))
                logger.debug('sector_abbrev: ' + str(sector_abbrev))
                logger.debug('mapped scheme: ' + str(mapped[ws_name]))

                # check if scheme already exists
                scheme = get_scheme(depbase_code, level_abbrev, sector_abbrev, sel_examyear)
                logger.debug('>>>>>>>>>> scheme: ' + str(scheme))

                if scheme is None:
                    logger.debug('>>>>>>>>>> scheme is None:')
                    logger.debug('mapped: ' + str(mapped))
                    department = get_department_from_mapped(depbase_code, sel_examyear, mapped)
                    logger.debug('department: ' + str(department))
                    level = get_level_from_mapped(level_abbrev, mapped)
                    sector = get_sector_from_mapped(sector_abbrev, mapped)
                    scheme_name = create_scheme_name(depbase_code, level_abbrev, sector_abbrev)
                    fields = str(row_data[3]) if row_data[3] else None
                    logger.debug('level: ' + str(level))
                    logger.debug('sector: ' + str(sector))
                    logger.debug('scheme_name: ' + str(scheme_name))

                    scheme = subj_mod.Scheme(
                        department=department,
                        level=level,
                        sector=sector,
                        name=scheme_name,
                        fields=fields
                    )
                    scheme.save(request=request)
                    excel_data.append(row_data)
                if scheme:
                    depbase_code_lc = scheme.department.base.code.lower() if scheme.department.base.code else 'none'
                    level_abbrev_lc = scheme.level.abbrev.lower() if scheme.level else 'none'
                    sector_abbrev_lc = scheme.sector.abbrev.lower() if scheme.sector else 'none'
                    key_tuple = (depbase_code_lc, level_abbrev_lc, sector_abbrev_lc)
                    mapped[ws_name][key_tuple] = scheme.pk
                logger.debug('scheme.id: ' + str(scheme.pk) + ' name: ' + str(scheme.name))

        elif ws_name == 'schemeitem':
            code = str(row_data[1]) if row_data[1] else None
            if code:
                depbase_code = str(row_data[0]) if row_data[0] else None
                level_abbrev = str(row_data[1]) if row_data[1] else None
                sector_abbrev = str(row_data[2]) if row_data[2] else None
                subject_code = str(row_data[3]) if row_data[3] else None
                subjtype_name = str(row_data[4]) if row_data[4] else None

                scheme = get_scheme(depbase_code, level_abbrev, sector_abbrev, sel_examyear)
                subject = get_subject(subject_code, sel_examyear)
                subjecttype = get_subjecttype(subjtype_name, sel_examyear)

                if scheme and subject and subjecttype:
                    # check if schemeitem already exists
                    schemeitem = get_schemeitem(scheme, subject, subjecttype)
                    if schemeitem is None:
                        gradetype = int(str(row_data[5])) if row_data[5] else None
                        weight_se = int(str(row_data[6])) if row_data[6] else None
                        weight_ce = int(str(row_data[7])) if row_data[7] else None

                        is_mandatory = True if str(row_data[8]) == '1' else False
                        is_combi = True if str(row_data[9]) == '1' else False
                        extra_count_allowed = True if str(row_data[10]) == '1' else False
                        extra_nocount_allowed = True if str(row_data[11]) == '1' else False
                        elective_combi_allowed = True if str(row_data[12]) == '1' else False
                        has_practexam = True if str(row_data[13]) == '1' else False

                        # PR2018-04-28 debug: don't forget de brackets when creating an instance of the class
                        schemeitem = subj_mod.Schemeitem(
                            scheme=scheme,
                            subject=subject,
                            subjecttype=subjecttype,
                            gradetype=gradetype,
                            weight_se=weight_se,
                            weight_ce=weight_ce,

                            is_mandatory=is_mandatory,
                            is_combi=is_combi,
                            extra_count_allowed=extra_count_allowed,
                            extra_nocount_allowed=extra_nocount_allowed,
                            elective_combi_allowed=elective_combi_allowed,
                            has_practexam=has_practexam,
                        )
                        schemeitem.save(request=request)
                        excel_data.append(row_data)

        elif ws_name == 'package':
            depbase_code = str(row_data[0]) if row_data[0] else None
            level_abbrev = str(row_data[1]) if row_data[1] else None
            sector_abbrev = str(row_data[2]) if row_data[2] else None
            package_name = str(row_data[3]) if row_data[3] else None

            school = sch_mod.School.objects.get_or_none(
                base=request.user.schoolbase,
                examyear=sel_examyear)
            scheme = get_scheme(depbase_code, level_abbrev, sector_abbrev, sel_examyear)

            if school and scheme and package_name:
                # check if package already exists
                package = get_package(school, scheme, package_name)
                if package is None:
                    package = subj_mod.Package(
                        school=school,
                        scheme=scheme,
                        name=package_name
                    )
                    package.save(request=request)
                    excel_data.append(row_data)

        elif ws_name == 'packageitem':
            depbase_code = str(row_data[0]) if row_data[0] else None
            level_abbrev = str(row_data[1]) if row_data[1] else None
            sector_abbrev = str(row_data[2]) if row_data[2] else None
            package_name = str(row_data[3]) if row_data[3] else None
            subject_code = str(row_data[4]) if row_data[4] else None
            subjtype_name = str(row_data[5]) if row_data[5] else None

            school = get_school(request.user.schoolbase, sel_examyear)
            scheme = get_scheme(depbase_code, level_abbrev, sector_abbrev, sel_examyear)
            package = get_package(school, scheme, package_name)

            subject = get_subject(subject_code, sel_examyear)
            subjecttype = get_subjecttype(subjtype_name, sel_examyear)
            schemeitem = get_schemeitem(scheme, subject, subjecttype)
            if package and schemeitem:
                # check if packageitem already exists
                packageitem = get_packageitem(package, schemeitem)
                if packageitem is None:
                    packageitem = subj_mod.Packageitem(
                        package=package,
                        schemeitem=schemeitem
                    )
                    packageitem.save(request=request)
                    excel_data.append(row_data)

        elif ws_name == 'birthcountry':
            name = str(row_data[0]) if row_data[0] else None
            # PR2018-04-28 debug: don't forget de brackets when creating an instance of the class
            if name:

                # check if birthcountry already exists
                birthcountry = get_birthcountry(name)
                if birthcountry is None:
                    birthcountry = stud_mod.Birthcountry(
                        name=name
                    )
                    birthcountry.save(request=request)
                    excel_data.append(row_data)

        elif ws_name == 'birthplace':
            birthcountry_name = str(row_data[0]) if row_data[0] else None
            birthplace_name = str(row_data[1]) if row_data[1] else None

            birthcountry = get_birthcountry(birthcountry_name)
            if birthcountry and birthplace_name:
                birthplace = get_birthplace(birthcountry, birthplace_name)
                if birthplace is None:
                    birthplace = stud_mod.Birthplace(
                        birthcountry=birthcountry,
                        name=birthplace_name
                    )
                    birthplace.save(request=request)
                    excel_data.append(row_data)

        elif ws_name in ('schoolCUR', 'schoolSXM'):
            logger.debug ('-------------------  school ----------------- examyear: ' + str(sel_examyear))
            # 0: country  1: code  2: name  3: abbrev  4: article  5: depbases  6: is_template
            country_code = str(row_data[0]) if row_data[0] else None
            school_code = str(row_data[1]) if row_data[1] else None
            logger.debug ('country_code: ' + str(country_code))
            logger.debug ('school_code: ' + str(school_code))

    # - get country based on code 'Cur' in excel file, not requsr_country with this code already exists in this country. If not: create
            exc_country = get_country(country_code)

    # skip if exc_country is different from requsr_country
            if exc_country and requsr_country and exc_country.pk == requsr_country.pk:

    # - check if schoolbase with this code already exists in this country. If not: create
                schoolbase = get_schoolbase(exc_country, school_code)
                if schoolbase is None:
                    schoolbase = sch_mod.Schoolbase.objects.create(country=exc_country, code=school_code)
                    logger.debug('schoolbase created: ' + str(schoolbase))

    # - check if school with this schoolbase already exists in this examyear. If not: create
                school = get_school(schoolbase, sel_examyear)
                logger.debug('school found: ' + str(school))
                if schoolbase is not None and school is None:
                    # 0: country  1: code  2: name  3: abbrev  4: article  5: depbases  6: is_template
                    name = str(row_data[2]) if row_data[2] else None
                    abbrev = str(row_data[3]) if row_data[3] else None
                    article = str(row_data[4]) if row_data[4] else None
                    depbases = get_depbase_id_list_from_nameslist(row_data[5], mapped)
                    # is_template = True if str(row_data[6]) == "1" else False

                    # PR2018-04-28 debug: don't forget de brackets when creating an instance of the class
                    school = sch_mod.School(
                        base=schoolbase,
                        examyear=sel_examyear,
                        name=name,
                        abbrev=abbrev,
                        article=article,
                        depbases=depbases
                    )
                    logger.debug('school: ' + str(school))
                    school.save(request=request)
                excel_data.append(row_data)
    #except:
    #    row_data[0] = _("An error occurred. '%(fld)s' is not saved.") % {'fld': ws_name}
    #    excel_data.append(row_data)


# ===================== Functions

def get_depbase_id_list_from_nameslist(names_list, mapped):  # PR2018-12-12  PR2020-12-13
    # PR2018-12-12 function replaces 'tkl,pkl,pbl' with ';1;2;3;'
    # PR2020-12-09 changed to arrayfield 'depbases' = [1,2,3]
    # mapped_sectorlist_dict is a separate function that gets the baseID's from this examyear
    # mapped_baselist = {'vsbo': 4, 'havo': 5,'vwo': 6}
    mapped_baselist = mapped.get('depbase')
    base_id_list = []
    if names_list:
        array = names_list.split(';')
        if array:
            for abbrev in array:
                # look up abbrev in mapped_baselist
                if abbrev:
                    base_id = mapped_baselist.get(abbrev.lower())
                    if base_id:
                        base_id_list.append(base_id)
    return base_id_list


def get_depbase_from_mapped(depbase_code_lc, examyear, mapped):  # PR2020-12-13
    depbase = None
    if depbase_code_lc:
        depbase_id = af.get_dict_value(mapped, ('depbase', depbase_code_lc))
        if depbase_id:
            depbase = sch_mod.Departmentbase.objects.get_or_none(id=depbase_id)
            if depbase:
                department = sch_mod.Department.objects.get_or_none(
                    base=depbase,
                    examyear=examyear
                )
                if department:
                    depbase = department.base
    return depbase


def get_department_from_mapped(depbase_code, examyear, mapped):  # PR2020-12-13
    logger.debug(' ----- get_department_from_mapped -----')
    logger.debug('depbase_code: ' + str(depbase_code))
    logger.debug('examyear: ' + str(examyear))
    logger.debug('mapped: ' + str(mapped.get('depbase', '')))
    department = None
    if depbase_code:
        depbase_code_lc = depbase_code.lower()
        depbase_id = af.get_dict_value(mapped, ('depbase', depbase_code_lc))
        logger.debug('depbase_id: ' + str(depbase_id))
        if depbase_id:
            depbase = sch_mod.Departmentbase.objects.get_or_none(pk=depbase_id)
            logger.debug('depbase: ' + str(depbase))
            if depbase:
                department = sch_mod.Department.objects.get_or_none(
                    base=depbase,
                    examyear=examyear
                )
    logger.debug('--------department: ' + str(department))
    return department


def get_level_from_mapped(lvl_abbrev, mapped):  # PR2020-12-13
    #logger.debug(' ----- get_level_from_mapped -----')
    #logger.debug('lvl_abbrev: ' + str(lvl_abbrev))
    level = None
    if lvl_abbrev:
        lvl_abbrev_lc = lvl_abbrev.lower()
        level_id = af.get_dict_value(mapped, ('level', lvl_abbrev_lc))
        #logger.debug('level_id: ' + str(level_id))
        if level_id:
            level = subj_mod.Level.objects.get_or_none(pk=level_id)
        #logger.debug('level: ' + str(level))
    return level


def get_sector_from_mapped(sct_abbrev, mapped):  # PR2020-12-13
    sector = None
    if sct_abbrev:
        sct_abbrev_lc = sct_abbrev.lower()
        sector_id = af.get_dict_value(mapped, ('sector', sct_abbrev_lc))
        if sector_id:
            sector = subj_mod.Sector.objects.get_or_none(pk=sector_id)
    return sector


def get_subject_from_mapped(subj_code_lc, mapped, examyear=None):  # PR2020-12-13
    #logger.debug(' ----- get_subject_from_mapped -----')
    #logger.debug('subj_code_lc: ' + str(subj_code_lc))
    #logger.debug('mapped_subject: ' + str(mapped.get('subject')))
    #logger.debug('examyear: ' + str(examyear))
    subject = None
    if subj_code_lc:
        # PR2020-12-09 debug: str() needed, otherwise gets eror:'Cell' object has no attribute 'lower'
        subject_id = af.get_dict_value(mapped, ('subject', subj_code_lc))
        #logger.debug('subject_id: ' + str(subject_id) )
        if subject_id:
            subject = subj_mod.Subject.objects.get_or_none(pk=subject_id)
        if subject is None and examyear:
            subject = subj_mod.Subject.objects.filter(
                examyear=examyear,
                base__code__iexact=subj_code_lc
                ).first()
    #logger.debug('subject: ' + str(subject) )
    return subject


def get_subjecttype_from_mapped(subjtype_name_lc, mapped, examyear=None):  # PR2020-12-13
    #logger.debug(' ----- get_subjecttype_from_mapped -----')
    #logger.debug('subjtype_name_lc: ' + str(subjtype_name_lc))
    #logger.debug('mapped_subjecttype: ' + str(mapped.get('subjecttype')))
    #logger.debug('examyear: ' + str(examyear))

    subjecttype = None
    if subjtype_name_lc:
    # PR2020-12-09 debug: str() needed, otherwise gets eror:'Cell' object has no attribute 'lower'
        subjtype_id = af.get_dict_value(mapped, ('subjecttype', subjtype_name_lc))
        #logger.debug('subjtype_id: ' + str(subjtype_id) )
        if subjtype_id:
            subjecttype = subj_mod.Subjecttype.objects.get_or_none(pk=subjtype_id)
        if subjecttype is None and examyear:
            subjecttype = subj_mod.Subjecttype.objects.filter(
                examyear=examyear,
                name__iexact=subjtype_name_lc
                ).first()
    #logger.debug('subjecttype: ' + str(subjecttype) )
    return subjecttype


def get_scheme_from_mapped(row_data, mapped, examyear=None):  # PR2020-12-13
    #logger.debug(' ----- get_scheme_from_mapped -----')
    scheme = None

    # PR2020-12-09 debug: str() needed, otherwise gets eror:'Cell' object has no attribute 'lower'
    # PR2020-12-09 debug: null value in tuple key not working, use string 'none' instead. That works

    # dep = row_data[0], lvl = = row_data[1], sct = = row_data[2]
    dep_lc = str(row_data[0]).lower() if row_data[1] else 'none'
    lvl_lc = str(row_data[1]).lower() if row_data[2] else 'none'
    sct_lc = str(row_data[2]).lower() if row_data[3] else 'none'
    key_tuple = (dep_lc, lvl_lc, sct_lc)
    #logger.debug('key_tuple: ' + str(key_tuple) )

    #mapped_scheme = mapped.get('scheme')
    #logger.debug('mapped_scheme: ' + str(mapped_scheme))
    scheme_id = af.get_dict_value(mapped, ('scheme', key_tuple))
    #logger.debug('scheme_id: ' + str(scheme_id) )

    if scheme_id:
        scheme = subj_mod.Scheme.objects.get_or_none(
            pk=scheme_id
        )
    if scheme is None and examyear:
        scheme = subj_mod.Scheme.objects.filter(
            department__examyear=examyear,
            department__base__code__iexact=dep_lc,
            level__abbrev__iexact=lvl_lc,
            sector__abbrev__iexact=sct_lc
        ).first()
    return scheme


def get_package_from_mapped(row_data, mapped):  # PR2020-12-13
    # logger.debug('get_package_from_mapped: ' + depbase_code + ' - ' + lvl_abbrev + ' - ' + sct_abbrev )
    # PR2020-12-09 debug: str() needed, otherwise gets eror:'Cell' object has no attribute 'lower'
    # PR2020-12-09 debug: null value in tuple key not working, use string 'none' instead. That works
    package = None
    package_name_lc = str(row_data[0]).lower() if row_data[0] else None
    if package_name_lc:
        package_id = af.get_dict_value(mapped, ('package', package_name_lc))
        if package_id:
            package = subj_mod.Package.objects.get_or_none(pk=package_id)
    return package


def create_scheme_name(depbase_code, level_abbrev, sector_abbrev ):
    # PR2018-11-09 create scheme-name i.e.: 'vsbo - tkl - tech' PR2020-12-13
    scheme_name = ''
    if depbase_code:
        scheme_name = depbase_code
    if level_abbrev and level_abbrev.lower() != 'none':
        scheme_name = scheme_name + " - " + level_abbrev
    if sector_abbrev:
        scheme_name = scheme_name + " - " + sector_abbrev
    return scheme_name


def get_country(country_abbrev):
    # get existing country PR2020-12-14
    country = None
    if country_abbrev:
        country = sch_mod.Country.objects.filter(
            abbrev__iexact=country_abbrev
        ).order_by('-pk').first()
    return country


def get_examyear(country, examyear_int):
    # lookup examyear of country PR2020-12-14
    # examyear is integer field of table Examyear
    examyear = None
    if country and examyear_int:
        examyear = sch_mod.Examyear.objects.filter(
            country=country,
            code=examyear_int
        ).order_by('-pk').first()
    return examyear


def get_subjecttype(subjtype_name, examyear):
    # check if subjecttype already exists
    subjecttype = None
    if subjtype_name and examyear:
        subjecttype = subj_mod.Subjecttype.objects.filter(
            examyear=examyear,
            name__iexact=subjtype_name
        ).order_by('-pk').first()
    return subjecttype


def get_subject(subject_code, examyear):
    # check if subject already exists
    subject = None
    if subject_code and examyear:
        subject =subj_mod.Subject.objects.filter(
            examyear=examyear,
            base__code__iexact=subject_code
        ).order_by('-pk').first()
    return subject


def get_scheme(depbase_code, level_abbrev, sector_abbrev, examyear):
    # check if scheme already exists
    #logger.debug('------- get_scheme -------------')

    scheme = None
    if depbase_code and examyear:
        crit = Q(department__examyear=examyear) & \
               Q(department__base__code__iexact=depbase_code)
        if level_abbrev and not level_abbrev.lower() == 'none':
            crit.add(Q(level__abbrev__iexact=level_abbrev), crit.connector)
        if sector_abbrev and not sector_abbrev.lower() == 'none':
            crit.add(Q(sector__abbrev__iexact=sector_abbrev), crit.connector)
        scheme = subj_mod.Scheme.objects.filter(crit).order_by('-pk').first()
    return scheme


def get_schemeitem(scheme, subject, subjecttype):
    # get existing schemeitem PR2020-12-13
    schemeitem = None
    if scheme and subject and subjecttype:
        schemeitem = subj_mod.Schemeitem.objects.filter(
            scheme=scheme,
            subject=subject,
            subjecttype=subjecttype
        ).order_by('-pk').first()
    return schemeitem


def get_package(school, scheme, package_name):
    # get existing schemeitem PR2020-12-13
    package = None
    if school and scheme and package_name:
        package = subj_mod.Package.objects.filter(
            school=school,
            scheme=scheme,
            name__iexact=package_name
        ).order_by('-pk').first()
    return package

def get_packageitem(package, schemeitem):
    # get existing packageitem PR2020-12-13
    packageitem = None
    if package and schemeitem:
        packageitem = subj_mod.Packageitem.objects.filter(
            package=package,
            schemeitem=schemeitem
        ).order_by('-pk').first()
    return packageitem



def get_birthcountry(name):
    # check if subject already exists
    birthcountry = None
    if name:
        birthcountry = stud_mod.Birthcountry.objects.filter(
            name__iexact=name
        ).order_by('-pk').first()
    return birthcountry


def get_birthplace(birthcountry, birthplace_name):
    # check if subject already exists
    birthplace = None
    if birthcountry and birthplace_name:
        birthplace = stud_mod.Birthplace.objects.filter(
            birthcountry=birthcountry,
            name__iexact=birthplace_name
        ).order_by('-pk').first()
    return birthplace


def get_schoolbase(country, code):
    # get existing schoolbase PR2020-12-14
    schoolbase = None
    if country and code:
        schoolbase = sch_mod.Schoolbase.objects.filter(
            country=country,
            code__iexact=code
        ).order_by('-pk').first()
    return schoolbase


def get_school(schoolbase, examyear):
    # get existing school from request_user PR2020-12-13
    school = None
    if schoolbase and examyear:
        school = sch_mod.School.objects.filter(
            base=schoolbase,
            examyear=examyear
        ).order_by('-pk').first()
    return school
