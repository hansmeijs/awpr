
# PR2021-11-19

from django.contrib.auth.decorators import login_required
from django.db import connection

from django.http import HttpResponse
from django.utils.decorators import method_decorator
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, pgettext_lazy, gettext_lazy as _
from django.views.generic import View

from decimal import Decimal
from accounts import views as acc_view
from accounts import  permits as acc_prm

from awpr import constants as c
from awpr import settings as s
from awpr import functions as af
from awpr import downloads as dl

from grades import calculations as grade_calc
from grades import calc_score as calc_score
from grades import calc_results as calc_res
from students import functions as stud_fnc
from students import views as stud_view


import json

import logging
logger = logging.getLogger(__name__)


@method_decorator([login_required], name='dispatch')
class CalcReexView(View):  # PR2023-04-04

    def post(self, request, list):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= CalcReexView ============= ')

        update_wrap = {}
        messages = []
        msg_html = None

# - reset language
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get permit
        has_permit = acc_prm.get_permit_of_this_page('page_result', 'calc_results', request)

        # note: this is part of get_permit_crud_of_this_page:
        #       'if has_permit and request.user and request.user.country and request.user.schoolbase:'
        if not has_permit:
            msg_html = acc_prm.err_html_no_permit(_('to calculate re-examinations'))
        else:

# - get upload_dict from request.POST
            # upload_dict = json.loads(list) if list != '-' else {}
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                if logging_on:
                    logger.debug('upload_dict: ' + str(upload_dict))

# ----- get selected examyear, school and department from usersettings
                # - get selected examyear, school and department from usersettings
                # may_edit = False when:
                #  - country is locked,
                #  - examyear is not found, not published or locked
                #  - school is not found, not same_school, not activated, or locked
                #  - department is not found, not in user allowed depbase or not in school_depbase
                sel_examyear, sel_school, sel_department, sel_level, may_edit, msg_list = \
                    acc_view.get_selected_ey_school_dep_lvl_from_usersetting(
                        request=request,
                        skip_same_school_clause= request.user.role in (c.ROLE_032_INSP, c.ROLE_064_ADMIN)
                    )

# - exit when examyear or school is locked, not published etc
                if not may_edit:
                    msg_html = acc_prm.msghtml_from_msglist_with_border(msg_list, c.HTMLCLASS_border_bg_invalid)
                else:
                    sel_lvlbase_pk, sel_sctbase_pkNIU = acc_view.get_selected_lvlbase_sctbase_from_usersetting(request)
                    student_pk_list = upload_dict.get('student_pk_list')

# +++++ calc_batch_student_result ++++++++++++++++++++
                    log_list, single_student_name = calc_batch_reex(
                        sel_examyear=sel_examyear,
                        sel_school=sel_school,
                        sel_department=sel_department,
                        student_pk_list=student_pk_list,
                        sel_lvlbase_pk=sel_lvlbase_pk,
                        user_lang=user_lang
                    )
                    update_wrap['log_list'] = log_list
                    update_wrap['log_student_name'] = single_student_name

                    update_wrap['updated_student_rows'], error_dict = stud_view.create_student_rows(
                        request=request,
                        sel_examyear=sel_examyear,
                        sel_schoolbase=sel_school.base,
                        sel_depbase=sel_department.base,
                        append_dict={})


# - return html with log_list
        if messages:
            update_wrap['messages'] = messages
# - return html with log_list
        if msg_html:
            update_wrap['msg_html'] = msg_html

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of CalcResultsView


def calc_batch_reex(sel_examyear, sel_school, sel_department, student_pk_list, sel_lvlbase_pk, user_lang):
    # PR2023-04-04
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ---------------  calc_batch_reex  ---------------')
        logger.debug('    sel_examyear: ' + str(sel_examyear))
        logger.debug('    sel_school: ' + str(sel_school))
        logger.debug('    sel_department: ' + str(sel_department))
        logger.debug('    student_pk_list: ' + str(student_pk_list))
        logger.debug('    sel_lvlbase_pk: ' + str(sel_lvlbase_pk))

    log_list = []
    single_student_name = None

# - get_scheme_dict
    scheme_dict = calc_res.get_scheme_dict(sel_examyear, sel_department)

# - get_schemeitems_dict
    schemeitems_dict = calc_res.get_schemeitems_dict(sel_examyear, sel_department)

# +++  get_students_with_grades_dictlist
    student_dictlist = calcreex_get_students_with_final_grades(
        examyear=sel_examyear,
        school=sel_school,
        department=sel_department,
        student_pk_list=student_pk_list,
        lvlbase_pk=sel_lvlbase_pk
    )

    if logging_on:
        if student_dictlist:
            for student_dict in student_dictlist:
                logger.debug('  $$$$$$$$$$$$  student_dict: ' + str(student_dict))
    """
    student_dict: {'fullname': 'Fonseca, Timothy Justin', 'stud_id': 7983, 'lastname': 'Fonseca', 'firstname': 'Timothy Justin', 'prefix': '', 
    'examnumber': '105', 'classname': '5', 'iseveningstudent': False, 'islexstudent': False, 'bis_exam': True, 'partial_exam': False, 'withdrawn': False, 
    'school_name': 'Abel Tasman College', 'islexschool': False, 'school_code': 'CUR13', 'depbase_code': 'Havo', 'lvlbase_code': None, 'examyear_code': 2023, 
    'dep_abbrev': 'H.A.V.O.', 'level_req': False, 'lvl_name': None, 'sct_name': 'Cultuur en Maatschappij', 
    'c_subj': 9, 'c_extra_nocount': 18, 'c_extra_counts': 18, 'c_thumbrule': 7, 'c_sr': 9, 
    64333: {'subject_id': None, 'schemeitem_id': 2765, 'is_extra_nocount': True, 'is_extra_counts': True, 'exemption_year': 2022, 
    'gl_sesrgrade': '5.0', 'gl_pecegrade': '5.5', 'gl_finalgrade': '5', 'is_thumbrule': True, 'has_sr': True, 
    'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'is_combi': False, 'is_core_subject': False, 
    'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'thumb_rule': False, 'rule_avg_pece_sufficient': True,  'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'subj_name_nl': 'Geschiedenis', 'subj_code': 'gs', 'subjtype_abbrev': 'Profieldeel'}, 
    'thumbrule_combi': True, 
        64328: {'subject_id': None, 'schemeitem_id': 2770, 'is_extra_nocount': True, 'is_extra_counts': True, 'exemption_year': 2022, 'gl_sesrgrade': '5.0', 'gl_pecegrade': None, 'gl_finalgrade': '5', 'is_thumbrule': True, 'has_sr': True, 'gradetype': 1, 'weight_se': 1, 'weight_ce': 0, 'multiplier': 1, 'is_combi': True, 'is_core_subject': False, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'thumb_rule': False, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'subj_name_nl': 'Algemene sociale wetenschappen', 'subj_code': 'asw', 'subjtype_abbrev': 'Gemeensch.'}, 
        64330: {'subject_id': None, 'schemeitem_id': 2787, 'is_extra_nocount': True, 'is_extra_counts': True, 'exemption_year': 2022, 'gl_sesrgrade': '5.8', 'gl_pecegrade': '8.3', 'gl_finalgrade': '7', 'is_thumbrule': True, 'has_sr': True, 'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'is_combi': False, 'is_core_subject': True, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'thumb_rule': False, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'subj_name_nl': 'Engelse taal en literatuur', 'subj_code': 'entl', 'subjtype_abbrev': 'Gemeensch.'}, 
        64332: {'subject_id': None, 'schemeitem_id': 2763, 'is_extra_nocount': True, 'is_extra_counts': True, 'exemption_year': 2022, 'gl_sesrgrade': '4.5', 'gl_pecegrade': '3.9', 'gl_finalgrade': '4', 'is_thumbrule': True, 'has_sr': True, 'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'is_combi': False, 'is_core_subject': False, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'thumb_rule': False, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'subj_name_nl': 'Informatica', 'subj_code': 'if', 'subjtype_abbrev': 'Profieldeel'}, 
        64335: {'subject_id': None, 'schemeitem_id': 2779, 'is_extra_nocount': True, 'is_extra_counts': True, 'exemption_year': 2022, 'gl_sesrgrade': '4.3', 'gl_pecegrade': '3.4', 'gl_finalgrade': '4', 'is_thumbrule': True, 'has_sr': True, 'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'is_combi': False, 'is_core_subject': True, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'thumb_rule': False, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'subj_name_nl': 'Wiskunde A', 'subj_code': 'wa', 'subjtype_abbrev': 'Vrije deel'}, 
        64336: {'subject_id': None, 'schemeitem_id': 2773, 'is_extra_nocount': True, 'is_extra_counts': True, 'exemption_year': 2022, 'gl_sesrgrade': '6.2', 'gl_pecegrade': None, 'gl_finalgrade': '6', 'is_thumbrule': True, 'has_sr': True, 'gradetype': 1, 'weight_se': 1, 'weight_ce': 0, 'multiplier': 1, 'is_combi': True, 'is_core_subject': False, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'thumb_rule': False, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'subj_name_nl': 'Profielwerkstuk', 'subj_code': 'pws', 'subjtype_abbrev': 'Werkstuk'}, 
        64331: {'subject_id': None, 'schemeitem_id': 2764, 'is_extra_nocount': True, 'is_extra_counts': True, 'exemption_year': 2022, 'gl_sesrgrade': '5.6', 'gl_pecegrade': '5.2', 'gl_finalgrade': '5', 'is_thumbrule': True, 'has_sr': True, 'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'is_combi': False, 'is_core_subject': False, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'thumb_rule': False, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'subj_name_nl': 'Papiamentu', 'subj_code': 'pa', 'subjtype_abbrev': 'Gemeensch.'}, 
        64329: {'subject_id': None, 'schemeitem_id': 2788, 'is_extra_nocount': True, 'is_extra_counts': True, 'exemption_year': 2022, 'gl_sesrgrade': '5.1', 'gl_pecegrade': '5.4', 'gl_finalgrade': '5', 'is_thumbrule': True, 'has_sr': True, 'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'is_combi': False, 'is_core_subject': True, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'thumb_rule': False, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'subj_name_nl': 'Nederlandse taal en literatuur', 'subj_code': 'netl', 'subjtype_abbrev': 'Gemeensch.'}, 
        64334: {'subject_id': None, 'schemeitem_id': 2759, 'is_extra_nocount': True, 'is_extra_counts': True, 'exemption_year': 2022, 'gl_sesrgrade': '4.7', 'gl_pecegrade': '4.7', 'gl_finalgrade': '5', 'is_thumbrule': True, 'has_sr': True, 'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 'is_combi': False, 'is_core_subject': False, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 'thumb_rule': False, 'rule_avg_pece_sufficient': True, 'rule_avg_pece_notatevlex': False, 'rule_core_sufficient': True, 'rule_core_notatevlex': False, 'subj_name_nl': 'Franse taal en literatuur', 'subj_code': 'frtl', 'subjtype_abbrev': 'Profieldeel'}}

    """


    """
    '1. print header AWPlog Herexamenberekening
    strLogFileName = "AWPlog Herexamenberekening " & pblAfd.CurSchoolnaam & " " & IIf(pblAfd.CurHasMultipleAfdelingen,
                                                                                      Replace(pblAfd.CurAfkAfdeling,
                                                                                              ".",
                                                                              "",,, vbTextCompare) & " ", "") & Format(
        Date, "dd mmm yyyy") & " " & Format(Time(), "hh.mm") & " uur.txt"
    strLogPath = pblDirectoryRoot & conDirectoryLogfilesDefault & "\" & strLogFileName

    strLogMsg = " "
    Call
    AppendLogFile(strLogPath, strLogMsg, True)
    strLogMsg = "========================================================================================================================"
    Call
    AppendLogFile(strLogPath, strLogMsg, True)
    strLogMsg = "LOG Herexamenberekening " & pblAfd.CurAfkAfdeling & " - " & Now()
    Call
    AppendLogFile(strLogPath, strLogMsg, True)
    strLogMsg = "========================================================================================================================"
    Call
    AppendLogFile(strLogPath, strLogMsg, True)
    strLogMsg = " "
    Call
    AppendLogFile(strLogPath, strLogMsg, True)

    strLogMsg = "AWP heeft de herexamenvakken berekend en het cijfer dat minimaal behaald moet worden om te slagen. " & vbCrLf & _
    "Het vak met een > ervoor heeft het laagst benodigde herexamencijfer. "

    Call
    AppendLogFile(strLogPath, strLogMsg, True)
    """
    return log_list, single_student_name

def calcreex_calc_student_result(examyear, department, student_dict, scheme_dict, schemeitems_dict,
                        log_list, sql_studsubj_list, sql_student_list):
    # PR2023-04-04
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ---------------  calcreex_calc_student_result  ---------------')

    dep_level_req = department.level_req
    depbase_code = str(department.base.code).lower()
    depbase_is_vsbo = (depbase_code == 'vsbo')
    sr_allowed = examyear.sr_allowed
    no_practexam = examyear.no_practexam
    no_centralexam = examyear.no_centralexam

# - get isevlex and full name with (evening / lex student)
    isevlexstudent, partial_exam, withdrawn, full_name = calc_res.get_isevlex_isreex_fullname(student_dict)

# - get result rules from scheme and schemeitem
    rule_avg_pece_sufficient, rule_core_sufficient, scheme_error = \
        calc_res.get_rules_from_schemeitem(student_dict, isevlexstudent, scheme_dict)

    """
    'A. Validate
        'a. exit if no student_id >> done in getting students
        'b. exit if locked >> done by may_edit in CalcResultsView.
        'c. exit if no scheme  >> done in this function
        TODO exit if student is tobedeleted
    """
    skip_student = False

# - student name header
    if log_list is not None:
        calc_res.log_list_student_header(student_dict, full_name, log_list)

# - A.3c. skip when scheme not found, put err_msg in loglist
    # PR2022-06-18 debug: msut give result 'no result, therefore don't skip student
    if not skip_student and scheme_error:
        skip_student = True
        if log_list is not None:
            calc_res.log_list_add_scheme_notfound(dep_level_req, log_list)

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# - studsubj_aggr_dict calculates totals, used in calculate result

    # Note: k_CountCijfers(OnvoldoendesInSectordeelProfieldeel,Tv01) telt aantal onvoldoendes in vakType Profieldeel,
    # werd alleen gebruikt bij PassFailedHavoVwo Oude Stijl PR2015-04-08

    # Count Eindcijfers: tel hoe vaak eindcijfers voorkomen (niet voor combinatievakken (> apart voor combi))
    #  - wordt ook doorlopen bij CijferType_OVG, voor controle of stage. LO en cav voldoende zijn
    #  - Niet bij VakType06_Stage, telt niet mee voor uitslag
    #  - Niet bij combinatievakken, cijfer van combivak wordt aan het einde opgeteld bij Count Eindcijfers PR2016-12-29
    #  PR 22 jun 09 debug: overslaan als Werkstuk onderdeel vormt van combivak (nog anders organiseren: werkstuk met cijfer behandelen als ;gewoon' vak
    #    'dan: hier combivak invullen, omdat werkstuk Kv_VakTypeID=conVakTypeSectorVak niet doorloopt
    #. tel hoe vaak eindcijfers voorkomen (wordt niet gebruikt in Havo Nieuwe Stijl, toch doorlopen ivm drieen)

    # PR2016-12-30 countWerkstuk toegevoegd, omdat CountVakken de combivakken overslaat en bij HavoVwo profielwerkstuk onderdeel is van combivak

    # COMBIVAKis3ofLager: ga na of Combivak een 3 of lager heeft PR2017-01-14 toegevoegd

    # store variables in list per examperiod, use listindex to lookup. Index = 0 is not in use

    # add dict with examperiod_key to sudent_dict, before iterating through student_dict.items,
    # otherwise error 'dictionary changed size during iteration' will come up

    if not skip_student:
        # student_dict is created in get_students_with_grades_dictlist
        # it also counts the number of grade_rows of exempttion, reex and reex_03 and puts it in 'c_ep4', 'c_ep2' and 'c_ep3'
        # later these will be saved stored in table student, fields exemption_count, reex_count and reex03_count
        exemption_count = student_dict.get('c_ep4', 0)
        sr_count = student_dict.get('c_sr', 0)
        reex_count = student_dict.get('c_ep2', 0)
        reex03_count = student_dict.get('c_ep3', 0)
        thumbrule_count = student_dict.get('c_thumbrule') or 0
        thumbrule_combi = student_dict.get('thumbrule_combi') or False

# - create ep_list, list of examperiods te be calculated
        # always add EXAMPERIOD_FIRST,
        # add exemption, reex and reex03 only when there are grades with this examperiod
        ep_list = []
        if exemption_count:
            ep_list.append(c.EXAMPERIOD_EXEMPTION)
        ep_list.append(c.EXAMPERIOD_FIRST)
        if reex_count:
            ep_list.append(c.EXAMPERIOD_SECOND)
        if reex03_count:
            if c.EXAMPERIOD_SECOND not in ep_list:
                ep_list.append(c.EXAMPERIOD_SECOND)
            ep_list.append(c.EXAMPERIOD_THIRD)

# - add number of sr, reex, reex03 to log_list
        # TODO add extra_nocount
        if log_list is not None:
            calc_res.log_list_reex_count(exemption_count, sr_count, reex_count, reex03_count, thumbrule_count, thumbrule_combi, log_list)

# - create dict per examperiod, not for exemption,
        for examperiod in ep_list:
            if examperiod != c.EXAMPERIOD_EXEMPTION:
                student_dict['ep' + str(examperiod)] = {'ep': examperiod, 'final': {}, 'combi': {}, 'pece': {}, 'count': {}}

        log_list.append(' ')

        # student_dict has dicts with key 'ep1' ep2' ep3', these are dicts per examperiod to store totals
        # studsubj_dict contains dicts with key '1' etc to store info per subject

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++
# - loop through studsubjects from student, get schemeitem
        has_subjects = False
        for studsubj_pk, studsubj_dict in student_dict.items():
        # - get info from schemeitems_dict
            # skip keys 'fullname' etc, only get studsubj_dict when key is integer, then it is a studsubj_pk
            if isinstance(studsubj_pk, int):
                has_subjects = True

# - get schemeitem_dict of this studsubj_dict
                si_dict = {}
                si_pk = studsubj_dict.get('si_id')
                if si_pk:
                    si_dict = schemeitems_dict.get(si_pk)

# - calc studsubj result
                calc_res.calc_studsubj_result(student_dict, isevlexstudent, sr_allowed, no_practexam, no_centralexam,
                                     studsubj_pk, studsubj_dict, si_dict, ep_list, log_list, sql_studsubj_list)

                # - put the max values that will appear on the gradelist back in studsubj, also max_use_exem
                #   done in calc_studsubj_result
                #   get_sql_studsubj_values(studsubj_pk, gl_sesr, gl_pece, gl_final, gl_use_exem, gl_ni_se, gl_ni_sr, gl_ni_pe, gl_ni_ce, gl_examperiod)

        if logging_on:
            logger.debug('    end of loop through studsubjects')
            logger.debug('    sql_studsubj_list: ' + str(sql_studsubj_list))

# - end of loop through studsubjects
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

# +++ calc_student_passedfailed:
        # - calculates combi grade for each examperiod and add it to final and count dict in student_ep_dict
        # - calculates passed / failed for each exam period (ep1, ep2, ep3)
        # - puts calculated result of the last examperiod in log_list

        calc_res.calc_student_passedfailed(ep_list, student_dict, rule_avg_pece_sufficient, rule_core_sufficient,
                                  withdrawn, partial_exam, has_subjects, depbase_is_vsbo, log_list, sql_student_list)

        if logging_on:
            logger.debug('     sql_student_list: ' + str(sql_student_list))

        if not has_subjects and log_list is not None:
            log_list.append(''.join((c.STRING_SPACE_05, str(_('This candidate has no subjects.')))))
# - end of calcreex_calc_student_result


def calcreex_get_students_with_final_grades(examyear, school, department, student_pk_list, lvlbase_pk=None):
    # PR2023-04-06

    # NOTE: don't forget to filter studsubj.deleted = False and grade.deleted = False!! PR2021-03-15
    # TODO grades that are not published are only visible when 'same_school' (or not??)
    # also add grades of each period

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ----- calcreex_get_students_with_final_grades -----')
        logger.debug('student_pk_list: ' + str(student_pk_list))

    # values of sel_layout are:"none", "level", "class", "cluster"
    # "none" or None: all students of subject on one form
    # "level:" seperate form for each leeerweg
    #  Note: when lvlbase_pk_list has values: filter on lvlbase_pk_list in all lay-outs
    #  filter on lvlbase_pk, not level_pk, to make filter also work in other examyears

    student_field_list = ('stud_id', 'lastname', 'firstname', 'prefix', 'examnumber', 'classname',
                'iseveningstudent', 'islexstudent', 'bis_exam', 'partial_exam', 'withdrawn',
                'school_name', 'islexschool', 'school_code', 'depbase_code', 'lvlbase_code', 'examyear_code',
                'dep_abbrev', 'level_req', 'lvl_name', 'sct_name')

    studsubj_field_list = ('subject_id', 'schemeitem_id',
                           'is_extra_nocount', 'is_extra_counts', 'exemption_year',
                           'gl_sesrgrade', 'gl_pecegrade', 'gl_finalgrade',
                           'is_extra_nocount', 'is_extra_counts', 'is_thumbrule', 'has_sr',
                           'gradetype', 'weight_se', 'weight_ce',  'multiplier', 'is_combi',
                           'is_core_subject', 'rule_grade_sufficient', 'rule_gradesuff_notatevlex', 'thumb_rule',
                           'rule_avg_pece_sufficient', 'rule_avg_pece_notatevlex',
                           'rule_core_sufficient', 'rule_core_notatevlex',
                           'subj_name_nl', 'subj_code', 'subjtype_abbrev'
                           )

    sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk,
                'student_pk_list': student_pk_list}


    sql_list = ["SELECT stud.id AS stud_id, studsubj.id AS studsubj_id,",

                "stud.lastname, stud.firstname, stud.prefix, stud.examnumber, stud.classname,",
                "stud.iseveningstudent, stud.islexstudent, stud.bis_exam, stud.partial_exam, stud.withdrawn,",
                "stud.exemption_count, stud.sr_count, stud.reex_count, stud.reex03_count, stud.thumbrule_count,",

                "school.name AS school_name, school.islexschool,",
                "sb.code AS school_code, depbase.code AS depbase_code, lvlbase.code AS lvlbase_code,",
                "ey.code AS examyear_code,",

                "dep.id AS dep_id, lvl.id AS lvl_id, sct.id AS sct_id, stud.scheme_id AS scheme_id,",
                "dep.name AS dep_name, dep.abbrev AS dep_abbrev, dep.level_req, dep.has_profiel,",
                "lvl.name AS lvl_name, sct.name AS sct_name,",

                "studsubj.subject_id, studsubj.schemeitem_id,",
                "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.exemption_year,",
                "studsubj.gradelist_sesrgrade AS gl_sesrgrade, studsubj.gradelist_pecegrade AS gl_pecegrade,",
                "studsubj.gradelist_finalgrade AS gl_finalgrade,",
                "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.is_thumbrule, studsubj.has_sr,",

                "si.gradetype, si.weight_se, si.weight_ce,  si.multiplier, si.is_combi,",
                "si.is_core_subject, si.rule_grade_sufficient, si.rule_gradesuff_notatevlex, si.thumb_rule,",

                "scheme.rule_avg_pece_sufficient, scheme.rule_avg_pece_notatevlex,",
                "scheme.rule_core_sufficient, scheme.rule_core_notatevlex,",

                "subj.base_id AS subjbase_id, subj.name_nl AS subj_name_nl, subjbase.code AS subj_code,",
                "subjtype.abbrev AS subjtype_abbrev",

                "FROM students_studentsubject AS studsubj",

                "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id)",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                "INNER JOIN subjects_subjecttype AS subjtype ON (subjtype.id = si.subjecttype_id)",

                "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                "INNER JOIN schools_schoolbase AS sb ON (sb.id = school.base_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",

                "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
                "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
                "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",

                "LEFT JOIN subjects_sector AS sct ON (sct.id = stud.sector_id)",

                "WHERE NOT stud.tobedeleted AND NOT stud.deleted AND NOT studsubj.tobedeleted AND NOT studsubj.deleted",
                "AND ey.id = %(ey_id)s::INT AND school.id = %(sch_id)s::INT AND dep.id = %(dep_id)s::INT",
                "AND stud.result = " + str(c.RESULT_FAILED) + "::INT"
                ]

    if student_pk_list:
        sql_keys['student_pk_arr'] = student_pk_list
        sql_list.append("AND stud.id IN ( SELECT UNNEST( %(student_pk_arr)s::INT[]))")
    else:
        if lvlbase_pk:
            sql_keys['lvlbase_pk'] = lvlbase_pk
            sql_list.append("AND lvl.base_id = %(lvlbase_pk)s::INT")

    sql_list.append("ORDER BY stud.lastname, stud.firstname")

    sql = ' '.join(sql_list)
    if logging_on and False:
        for sql_txt in sql_list:
            logger.debug(' > ' + sql_txt)

    grade_dictlist_sorted = []
    cascade_dict = {}
    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

    if rows:
        for row in rows:
            stud_id = row.get('stud_id')
            if stud_id not in cascade_dict:
                full_name = stud_fnc.get_full_name(row.get('lastname'), row.get('firstname'), row.get('prefix'))
                # stud_dict = {'fullname': full_name, 'result': [], }
                stud_dict = {'fullname': full_name}
                for field in student_field_list:
                    value = row.get(field)
                    if value is not None or True:
                        stud_dict[field] = value
                # PR 2022-06-09 debug: count exemp, reex, reex3
                # id safer than getting it from student row
                cascade_dict[stud_id] = stud_dict

            # - add studsubj_dict dict
            student_dict = cascade_dict.get(stud_id)
            if student_dict:
                # put studsubjects in dict with key: 'studsubj_id'
                studsubj_pk = row.get('studsubj_id')

                if studsubj_pk not in student_dict:
                    # add 1 to count subjects
                    student_dict['c_subj'] = 1 + (student_dict.get('c_subj') or 0)

                    # count put value of studsubj_field_list fields in studsubj_dict
                    studsubj_dict = {}
                    for field in studsubj_field_list:
                        studsubj_dict[field] = row.get(field)

                        # count is_extra_nocount, is_extra_counts, is_thumbrule
                        if field == 'has_sr':
                            student_dict['c_sr'] = 1 + (student_dict.get('c_sr') or 0)
                            studsubj_dict['has_sr'] = True  # has_school_reex
                        if field == 'is_thumbrule':
                            if row.get('is_combi'):
                                student_dict['thumbrule_combi'] = True
                            else:
                                student_dict['c_thumbrule'] = 1 + (student_dict.get('c_thumbrule') or 0)
                            studsubj_dict['is_thumbrule'] = True
                        elif field == 'is_extra_nocount':
                            student_dict['c_extra_nocount'] = 1 + (student_dict.get('c_extra_nocount') or 0)
                            studsubj_dict['is_extra_nocount'] = True
                        elif field == 'is_extra_counts':
                            student_dict['c_extra_counts'] = 1 + (student_dict.get('c_extra_counts') or 0)
                            studsubj_dict['is_extra_counts'] = True

                    student_dict[studsubj_pk] = studsubj_dict

        # convert dict to sorted dictlist
        grade_list = list(cascade_dict.values())

        # sort list to sorted dictlist
        # PR2021-11-15 from https://stackoverflow.com/questions/72899/how-do-i-sort-a-list-of-dictionaries-by-a-value-of-the-dictionary
        if grade_list:
            grade_dictlist_sorted = sorted(grade_list, key=lambda d: d['fullname'])

    return grade_dictlist_sorted
# - end of calcreex_get_students_with_final_grades


