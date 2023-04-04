
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

# - reset language
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get permit
        has_permit = acc_prm.get_permit_of_this_page('page_result', 'calc_results', request)

        # note: this is part of get_permit_crud_of_this_page:
        #       'if has_permit and request.user and request.user.country and request.user.schoolbase:'
        if not has_permit:
            messages.append({'header': str(_('Calculate re-examinations')), 'class': 'border_bg_invalid',
                            'msg_html': str(_("You don't have permission to calculate re-examinations."))})
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

# - exit when examyear or school is locked etc
                if not may_edit:
                    msg_list.append(str(_('The re-examinations cannot be calculated.')))
                    msg_html = '<br>'.join(msg_list)
                    msg_dict = {'header': str(_('Calculate re-examinations')), 'class': 'border_bg_invalid',
                                'msg_html': msg_html}
                    messages.append(msg_dict)
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

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of CalcResultsView



def calc_batch_reex(sel_examyear, sel_school, sel_department, student_pk_list, sel_lvlbase_pk, user_lang):
    # PR2023-04-04
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ---------------  posreex_student_result  ---------------')

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

def posreex_calc_student_result(examyear, department, student_dict, scheme_dict, schemeitems_dict,
                        log_list, sql_studsubj_list, sql_student_list):
    # PR2023-04-04
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ---------------  posreex_student_result  ---------------')

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
# - end of calc_student_result

