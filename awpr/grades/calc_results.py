# PR2021-11-19

from django.contrib.auth.decorators import login_required
from django.db import connection

from django.http import HttpResponse
from django.utils.decorators import method_decorator
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, pgettext_lazy, gettext_lazy as _
from django.views.generic import View

from awpr import constants as c
from awpr import settings as s
from awpr import functions as af
from awpr import downloads as dl


from grades import calculations as grade_calc
from grades import calc_score as calc_score
from students import functions as stud_fnc
from students import views as stud_view

from decimal import Decimal

import json

import logging
logger = logging.getLogger(__name__)

"""
@@@@@@@@@@@@@ EXAMENREGELING VSBO @@@@@@@@@@@@@@@@@@@@

'MEMO Uitslagregeling VO t.b.v. van het ETE 29 juli 2009 van Hans Bikker

'De uitslagregeling is voor het VSBO vanaf 2005 niet meer gewijzigd. In PB 2008, nr.54, is de regeling correct weergegeven.
    
'De uitslagregeling luidt als volgt:
    '1.  De kandidaat die eindexamen v.s.b.o. heeft afgelegd, is geslaagd indien hij:
    '       a. voor al zijn vakken waarvoor een eindcijfer is vastgesteld, het eindcijfer 6 of hoger heeft behaald,
    '       b. voor ten hoogste één van zijn examenvakken het eindcijfer 5 heeft behaald en voor zijn overige examenvakken een 6 of hoger, of
    '       c. voor ten hoogste één van zijn examenvakken het eindcijfer 4 heeft behaald en voor zijn overige examenvakken een 6 of hoger waarvan ten minste één 7 of hoger, of
    '       d. voor twee van zijn examenvakken het eindcijfer 5 heeft behaald en voor zijn overige examenvakken een 6 of hoger waarvan ten minste één 7 of hoger.
    '       e. het eindcijfer van het sectorprogramma in de praktisch basisgerichte leerweg dan wel de praktisch kadergerichte leerweg telt twee maal. (NB: dit betreft MULTIPLIER PR 30 apr 13)
    
    '2.  In aanvulling op het eerste lid geldt tevens dat voor het sectorwerkstuk de kwalificatie "voldoende" of "goed" is behaald.
    
    '3.     a.Tevens is regel dat het cijfer voor het schoolexamen in de praktisch beroepsgerichte leerweg tweemaal meetelt. (NB: dit betreft SE/CE WEGING PR 30 apr 13)
    '       b.Bij pkl en tkl tellen SE en CE even zwaar.
    
    '4.     Cijfer sectorwerkstuk wordt met een o/v/g aangegeven.

    '5.     In het inrichtingsbesluit (art. 20, 9de en 10de lid) is geregeld dat de leerlingen in de PBL en PKL in het derde en vierde leerjaar stage lopen.
            'In het eindexamenbesluit wordt in artikel, 1ste lid, gesteld dat van alle vakken, deelvakken en programmaonderdelen een schoolexamen wordt afgenomen.
            'Dit zou dus ook moeten gelden voor het onderdeel 'stage'. Het is echter aan de school om uit te maken in hoeverre dit onderdeel meetelt bij het schoolexamen.
            'Het is daarom geen apart onderdeel van de uitslagregeling.

    '6. vanaf 2016 wel in AWP opgenomen. PR2016-06-19 Was: (niet van belang voor AWP:)
    '       Cijfer sectorprogramma voor het CE en CP (praktijk) examen voor pbl het cpe en pkl het cie tellen even zwaar, dus 1 op 1.
    '       Deze twee, dus CE en CP vormen samen het centraal eindexamen cijfer voor het sectorprogramma.
'ofwel

'PR: slagingsregeling Vsbo
    '1a een kandidaat is geslaagd als voor al zijn vakken een eindcijfer 6 of hoger is behaald
    '1b een kandidaat is geslaagd als voor ten hoogste 1 vak een 5 heeft behaald en voor de overige vakken een 6 of hoger is behaald
    '1c een kandidaat is geslaagd als voor ten hoogste 1 vak een 4 is behaald en voor de overige vakken een 6 of hoger waarvan tenminste 1 een 7 of hoger
    '1d een kandidaat is geslaagd als voor 2 vakken een 5 is behaald en voor de overige vakken een 6 of hoger waarvan tenminste 1 een 7 of hoger
    '2a. in TKL voor het sectorwerkstuk een 'voldoende' of 'goed' is behaald    (2 in memo)

'PR 15 sep 09: stage telt niet meer mee in uitslagberekening
    '3a in PKL en PBL voor stage en 'voldoende' of 'goed' is behaald
        'gewijzigd op verzoek St Paulus, na akkoord ETE: stage niet verplicht   (5. in memo)
        
'overige regelingen Vsbo
    ' - voor PBL geldt dat het SE cijfer 2x meetelt en het CE cijfer 1x        (3a in memo)
    ' - bij PKL en TKL tellen SE en CE even zwaar                              (3b in memo)
    ' - bij PBL en PKL telt het cijfer in het sectorprogramma 2x mee            (1e in memo)
    ' - sectorwerkstuk en stage heeft cijfertype o/v/g, rest nummer             (4 in memo)
    
'NB: in deze examenregeling wordt GemidEindcijfer en gemidCEcijfer NIET gebruikt   PR 1 jun 13

'PR2015-10-28 prmAantalVakkenInSectorProgrammaNIG wordt niet gebruikt, Was: ByVal prmAantalVakkenInSectorProgrammaNIG As Integer, _

@@@@@@@@@@@@@ EXAMENREGELING HAVO VWO @@@@@@@@@@@@@@@@@@@@
'PR2015-06-12 debug HvD: HELP!!! Fout bij deling gemCEcijfer 385/7 = 5,49, moet zijn 5,5. Fout in Access bij Double variabele > omgezet in Currency
    'Was: ByVal dblGemidEindcijfer As Double, ByVal dblGemidCEcijfer As Double,
'UITSLAGREGELING NEDERLAND 2012 - zie onderaan deze blz 'PR 18 apr 12

'UITSLAGREGELING SINT MAARTEN miv 1 aug 2012 - zie Ministeriel Beschikking Nr: OCJS 2012/920 van 5 juni 2012
'De kandidaat die het eindexamen vwo of havo heeft afgelegd is geslaagd indien, met inachtneming van artikel 35, vijfde lid, tweede volzin:
    'a. het rekenkundig gemiddelde van zijn bij het centraal examen behaalde cijfers ten minste 5,5 is;
    'b. voor al zijn vakken waarvoor een eindcijfer is vastgesteld, het eindcijfer 6 of meer is behaald;
    'c. voor één van zijn vakken waarvoor een eindcijfer is vastgesteld, het eindcijfer 5 en
    '   voor de overige vakken waarvoor een eindcijfer is vastgesteld, het eindcijfer 6 of meer is behaald of;
    'd. voor één van zijn vakken waarvoor een eindcijfer is vastgesteld, het eindcijfer 4 en
    '   voor de overige vakken waarvoor een eindcijfer is vastgesteld, het eindcijfer 6 of meer is behaald,
    '   en het gemiddelde van de eindcijfers tenminste 6,0 bedraagt;
    'of
    'e. voor twee van zijn vakken waarvoor een eindcijfer is vastgesteld, het eindcijfer 5 is behaald
    '   dan wel voor één van de vakken waarvoor een eindcijfer is vastgesteld, het eindcijfer 4 en voor één van deze vakken het eindcijfer 5 is behaald,
    '   en voor de overige vakken waarvoor een eindcijfer is vastgesteld, het eindcijfer 6 of meer is behaald,
    '   en het gemiddelde van de eindcijfers tenminste 6,0 bedraagt;
    
'NB: + CAV en LO moeten voldoende zijn, behalve bij avondschool PR2014-05-18
        'PR 22 jun 07: bij CAL overslaan op verzoek Juni Pieters met toestemming ETE
        'PR2019-10-21 toegevoegd: idem bij landsexamen

'Ofwel: een kandidaat is geslaagd als
    'a. GemidCSE 5,5 of meer
    
    'b. voor al zijn vakken een eindcijfer 6 of hoger is behaald
    'c. voor ten hoogste 1 vak een 5 is behaald en voor de overige vakken een 6 of hoger
    'd. voor ten hoogste 1 vak een 4 is behaald en voor de overige vakken een 6 of hoger en het gemiddelde van de eindcijfers tenminste 6,0 bedraagt
    'e. voor 2 vakken een 5 is behaald danwel
    '   voor 1 vakken een 5 en 1 vak een 4 is behaald, en voor de overige vakken een 6 of hoger en het gemiddelde van de eindcijfers tenminste 6,0 bedraagt
    
'NB: in deze examenregeling worden zowel GemCE als GemidEindcijfer gebruikt PR 1 jun 13 
"""


@method_decorator([login_required], name='dispatch')
class CalcResultsView(View):  # PR2021-11-19

    def post(self, request, list):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= CalcResultsView ============= ')

        update_wrap = {}
        messages = []

# - reset language
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get permit
        has_permit = af.get_permit_crud_of_this_page('page_result', request)
        # note: this is part of get_permit_crud_of_this_page:
        #       'if has_permit and request.user and request.user.country and request.user.schoolbase:'
        if not has_permit:
            messages.append({'header': str(_('Calculate results')), 'class': 'border_bg_invalid',
                            'msg_html': str(_("You don't have permission to calculate results."))})
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
                sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

# - exit when examyear or school is locked etc
                if not may_edit:
                    msg_list.append(str(_('The results cannot be calculated.')))
                    msg_html = '<br>'.join(msg_list)
                    msg_dict = {'header': str(_('Calculate results')), 'class': 'border_bg_invalid',
                                'msg_html': msg_html}
                    messages.append(msg_dict)
                else:

                    sel_lvlbase_pk, sel_sctbase_pkNIU = dl.get_selected_lvlbase_sctbase_from_usersetting(request)
                    student_pk_list = upload_dict.get('student_pk_list')

# +++++ calc_batch_student_result ++++++++++++++++++++
                    log_list = calc_batch_student_result(
                        sel_examyear=sel_examyear,
                        sel_school=sel_school,
                        sel_department=sel_department,
                        student_pk_list=student_pk_list,
                        sel_lvlbase_pk=sel_lvlbase_pk,
                        user_lang=user_lang
                    )

                    update_wrap['updated_student_rows'], error_dict = stud_view.create_student_rows(
                        sel_examyear=sel_examyear,
                        sel_schoolbase=sel_school.base,
                        sel_depbase=sel_department.base,
                        append_dict={})

                    update_wrap['log_list'] = log_list

# - return html with log_list
        if messages:
            update_wrap['messages'] = messages

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of CalcResultsView


def calc_batch_student_result(sel_examyear, sel_school, sel_department, student_pk_list, sel_lvlbase_pk, user_lang):
    # PR2022-05-26
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ---------------  calc_batch_student_result  ---------------')
        logger.debug('student_pk_list: ' + str(student_pk_list))

# - get_scheme_dict
    scheme_dict = get_scheme_dict(sel_examyear, sel_department)

# - get_schemeitems_dict
    schemeitems_dict = get_schemeitems_dict(sel_examyear, sel_department)

# +++  recalculate and save the final grades of the subjects of each student in student_pk_list PR2022-05-25
    calc_score.batch_update_finalgrade(
        department_instance=sel_department,
        student_pk_list=student_pk_list)

# +++  get_students_with_grades_dictlist
    student_dictlist = get_students_with_grades_dictlist(
        examyear=sel_examyear,
        school=sel_school,
        department=sel_department,
        student_pk_list=student_pk_list,
        lvlbase_pk=sel_lvlbase_pk
    )

    if logging_on and False:
        logger.debug('############################### ')
        logger.debug('student_dictlist: ' + str(student_dictlist))

# - create log_list with header
    log_list = log_list_header(sel_school, sel_department, sel_examyear, user_lang)
    sql_studsubj_list = []
    sql_student_list = []

# loop through student_dictlist - ordered list of students with grades
    for student_dict in student_dictlist:
        calc_student_result(sel_examyear, sel_department, student_dict, scheme_dict, schemeitems_dict, log_list,
                            sql_studsubj_list, sql_student_list)

# - save calculated fields in studsubj
    if sql_studsubj_list:
        save_studsubj_batch(sql_studsubj_list)

# - save calculated fields in student
    if sql_student_list:
        save_student_batch(sql_student_list)

    if not student_dictlist:
        log_list.append(''.join((c.STRING_SPACE_05, str(_('There are no candidates.')))))

    log_list.append(c.STRING_SINGLELINE_80)

    return log_list
# - end of calc_batch_student_result


def calc_student_result(examyear, department, student_dict, scheme_dict, schemeitems_dict, log_list, sql_studsubj_list, sql_student_list):
    # PR2021-11-19 PR2021-12-18 PR2021-12-30 PR2022-01-04
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ---------------  calc_student_result  ---------------')

    dep_level_req = department.level_req
    depbase_code = str(department.base.code).lower()
    depbase_is_vsbo = (depbase_code == 'vsbo')
    sr_allowed = examyear.sr_allowed
    no_practexam = examyear.no_practexam

# - get isevlex and full name with (evening / lex student)
    isevlexstudent, partial_exam, withdrawn, full_name = get_isevlex_isreex_fullname(student_dict)

# - get result rules from scheme and schemeitem
    rule_avg_pece_sufficient, rule_core_sufficient, scheme_error = \
        get_rules_from_schemeitem(student_dict, isevlexstudent, scheme_dict)

    """
    'A. Validate
        'a. exit if no student_id >> done in getting students
        'b. exit if locked >> done by may_edit in CalcResultsView.
        'c. exit if no scheme  >> done in this function
    """
    skip_student = False

# - student name header
    if log_list is not None:
        log_list_student_header(student_dict, full_name, log_list)

# - A.3c. skip when scheme not found, put err_msg in loglist
    if not skip_student and scheme_error:
        skip_student = True
        if log_list is not None:
            log_list_add_scheme_notfound(dep_level_req, log_list)

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# - studsubj_aggr_dict calculates totals, used in calculate result

    # Note" tel k_CountCijfers(OnvoldoendesInSectordeelProfieldeel,Tv01) telt aantal onvoldoendes in vakType Profieldeel,
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
        exemption_count = student_dict.get('c_ep4', 0)
        sr_count = student_dict.get('c_sr', 0)
        reex_count = student_dict.get('c_ep2', 0)
        reex03_count = student_dict.get('c_ep3', 0)
        thumbrule_count = student_dict.get('c_thumbrule', 0)

        ep_list = [c.EXAMPERIOD_EXEMPTION, c.EXAMPERIOD_FIRST]
        if reex_count:
            ep_list.append(c.EXAMPERIOD_SECOND)
        if reex03_count:
            if c.EXAMPERIOD_SECOND not in ep_list:
                ep_list.append(c.EXAMPERIOD_SECOND)
            ep_list.append(c.EXAMPERIOD_THIRD)

# - add amount of sr, reex, reex03 to log_list
        if log_list is not None:
            log_list_reex_count(exemption_count, sr_count, reex_count, reex03_count, thumbrule_count, log_list)

        for examperiod in ep_list:
            # - create dict per examperiod, not for exemption,
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

                calc_studsubj_result(student_dict, isevlexstudent, sr_allowed, no_practexam, studsubj_pk, studsubj_dict, si_dict, ep_list, log_list, sql_studsubj_list)

                # - put the max values that will appear on the gradelist back in studsubj, also max_use_exem
                #   done in calc_studsubj_result
                #   save_max_grade_in_studsubj(studsubj_pk, gl_sesr, gl_pece, gl_final, gl_use_exem, gl_ni_se, gl_ni_sr, gl_ni_pe, gl_ni_ce, gl_examperiod)

        if logging_on:
            logger.debug('    end of loop through studsubjects')
            logger.debug('    sql_studsubj_list: ' + str(sql_studsubj_list))

# - end of loop through studsubjects
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++

# +++ calc_student_passedfailed:
        # - calculates combi grade for each examperiod and add it to final and count dict in student_ep_dict
        # - calculates passed / failed for each exam period (ep1, ep2, ep3)
        # - puts calculated result of the last examperiod in log_list

        calc_student_passedfailed(ep_list, student_dict, rule_avg_pece_sufficient, rule_core_sufficient,
                                  withdrawn, partial_exam, has_subjects, depbase_is_vsbo, log_list, sql_student_list)

        if logging_on:
            logger.debug('     sql_student_list: ' + str(sql_student_list))

        if not has_subjects and log_list is not None:
            log_list.append(''.join((c.STRING_SPACE_05, str(_('This candidate has no subjects.')))))
# - end of calc_student_result


def calc_studsubj_result(student_dict, isevlexstudent, sr_allowed, no_practexam, studsubj_pk, studsubj_dict, si_dict, ep_list, log_list, sql_studsubj_list):
    # PR2021-12-30 PR2022-01-02
    # called by calc_student_result and update_and_save_gradelist_fields_in_studsubj_student
    logging_on = False  #s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  calc_studsubj_result  -----')
        logger.debug('     studsubj_dict: ' + str(studsubj_dict))
        logger.debug('     si_dict: ' + str(si_dict))
    """
    si_dict: {'si_id': 1714, 'ete_exam': False, 'gradetype': 1, 'weight_se': 1, 'weight_ce': 1, 'multiplier': 1, 
    'is_mandatory': True, 'is_combi': False, 'extra_count_allowed': False, 'extra_nocount_allowed': False, 
    'has_practexam': False, 'is_core_subject': False, 'is_mvt': False, 'is_wisk': False, 'sr_allowed': False,
     'no_ce_years': '2020', 
     'si': '(1714,"2021-10-13 18:25:58.509888+00",1,1,1,t,f,f,f,f,1,71,123,274,f,f,f,f,,f,f,pa,1,f,f,2020,f)', 
     'thumb_rule': False, 'rule_grade_sufficient': False, 'rule_gradesuff_notatevlex': False, 
     'subj_name': 'Biologie', 'subj_code': 'bi', 'sjtp_name': 'Sectordeel', 'sjtp_code': 'spd', 'sjtp_has_pws': False}

    """
    subj_code = si_dict.get('subj_code', '-')
    subj_name = si_dict.get('subj_name', '-')
    gradetype = si_dict.get('gradetype')
    multiplier = si_dict.get('multiplier', 1)
    weight_se = si_dict.get('weight_se', 0)
    weight_ce = si_dict.get('weight_ce', 0)
    is_combi = si_dict.get('is_combi', False)
    is_core = si_dict.get('is_core_subject', False)

    rule_grade_sufficient = si_dict.get('rule_grade_sufficient', False)
    rule_gradesuff_notatevlex = si_dict.get('rule_gradesuff_notatevlex', False)

    no_ce_years = si_dict.get('no_ce_years')
    thumb_rule_applies = si_dict.get('thumb_rule', False)

    # Practical exam does not exist any more. Set has_practexam = False PR2022-05-26
    # was: has_practexam = si_dict.get('has_practexam', False)
    has_practexam = False

    if logging_on:
        logger.debug('     subj_code: ' + str(subj_code))

# - put subject name + combi, core if appl. in log_list
    subj_name_str = subj_name
    if is_combi or is_core:
        subj_name_str += ' ('
        if is_combi:
            subj_name_str += str(_('Combination subject'))
        if is_combi and is_core:
            subj_name_str += ', '
        if is_core:
            subj_name_str += str(_('Core subject'))
        subj_name_str += ')'

    if log_list is not None:
        log_list.append(subj_name_str)

    has_sr = studsubj_dict.get('has_sr', False)
    has_reex = studsubj_dict.get('has_reex', False)
    has_reex03 = studsubj_dict.get('has_reex03', False)

    # PR2022-06-09 debug value of has_reex etc is not always correct
    # it is safer to loop through ep_list to calculate values of has_reex etc
    # then has_reex can be stored in student

    is_extra_nocount = studsubj_dict.get('is_extra_nocount', False)
    if is_extra_nocount:
        if log_list is not None:
            log_list.append(''.join((c.STRING_SPACE_05, str(_('Extra subject, does not count for the result.')))))

    is_thumbrule = False
    if thumb_rule_applies:
        is_thumbrule = studsubj_dict.get('is_thumbrule', False)
        if is_thumbrule:
            if log_list is not None:
                log_list.append(''.join((c.STRING_SPACE_05, str(_('Thumb rule applies, subject does not count for the result.')))))

    exemp_no_ce = False
    has_exemption = studsubj_dict.get('has_exemption', False)
    if has_exemption:
        exemption_year = studsubj_dict.get('exemption_year')
        no_ce_years = si_dict.get('no_ce_years')
        exemp_no_ce = calc_exemp_noce(exemption_year, no_ce_years)

    if logging_on:
        logger.debug(' ')
        logger.debug(' =====================  ' + str(subj_name) + '   =====================')
        logger.debug('     has_exemption: ' + str(has_exemption))
        logger.debug('     has_reex:      ' + str(has_reex))
        logger.debug('     is_thumbrule:  ' + str(is_thumbrule))

    # gl_max_examperiod contains the examperiod that must be stored in studsubj, to be shown on gradelist
    gl_max_examperiod = c.EXAMPERIOD_FIRST
    gl_max_ni = []

# ----------------------------------------
    log_subj_grade_dict = {}

# - loop through examperiods, in order: exemption, ep_01, ep_02, ep_03;
    # grade exemption, reex, reex03 only exist when has_exemption, is_reex_candidate or is_reex03_candidate
    for examperiod in ep_list:

# - these calculations are only made when examperiod exists in studsubj_dict
        if examperiod in studsubj_dict:
            this_examperiod_dict = studsubj_dict.get(examperiod)
            if logging_on :
                logger.debug('--------------- this examperiod: ' + str(examperiod) + ' ---------------')

# --- check for '-noinput': if grade should have value, add '-noinput if required value not entered
            # also when exemption
            # when noinput: 'ni' = ['se', 'sr', 'pe', 'ce'] is stored in this_examperiod_dict
            # also noin_dict is added, is used in log_list
            # 'noin': {'vr': {'cav': ['se']}, 'pe': {'bw': ['se', 'ce']}, 'se': ['mm1'], 'ce': ['ec'], 'h3': ['ac']}
            calc_noinput(examperiod, studsubj_dict, subj_code, weight_se, weight_ce, has_practexam,
                         has_exemption, has_sr, has_reex, has_reex03, exemp_no_ce)
            if logging_on:
                logger.debug('    this_examperiod_dict: ' + str(this_examperiod_dict))
                logger.debug('    this_examperiod_dict ni: ' + str(this_examperiod_dict.get('ni')))
                logger.debug('    this_examperiod_dict noin: ' + str(this_examperiod_dict.get('noin')))
                """
                this_examperiod_dict: {'subj': 'pa', 'se': '6.8', 'sesr': '6.8', 'final': '7', 'noin': {'vr': {'pa': ['CE']}}, 'ni': ['ce']}
                this_examperiod_dict ni: ['ce']
                this_examperiod_dict noin: {'vr': {'pa': ['CE']}}
                """
# --- calculate max values, maximum grade when comparing exemption, ep_1, ep_2, ep_3
            #  calc_max_grades stores these keys to this_examperiod_dict:
            #  'max_ep' 'max_sesr''max_pece' 'max_final', 'max_ni' 'max_use_exem'
            #  will be saved in studsubj by: save_max_grade_in_studsubj
            max_examperiod, max_ni = calc_max_grades(examperiod, this_examperiod_dict, studsubj_dict, gradetype)

# - gl_max_examperiod is the max_examperiod of the highest examperiod (is 1, 2 or 3)
            if max_examperiod and examperiod != c.EXAMPERIOD_EXEMPTION:
                gl_max_examperiod = max_examperiod
                if max_ni:
                    gl_max_ni = max_ni

            if logging_on:
                logger.debug('    this_examperiod_dict: ' + str(this_examperiod_dict))
                logger.debug('    max_examperiod: ' + str(max_examperiod))
                logger.debug('    gl_max_examperiod: ' + str(gl_max_examperiod))
                logger.debug('    max_ni: ' + str(max_ni))
                logger.debug('    gl_max_ni: ' + str(gl_max_ni))

# add subj_grade_str to log_subj_grade_dict
            # subj_grade_str: '     Vrijstelling: SE:9,7 CE:6,0 Eindcijfer:8'
            subj_grade_str = log_list_subject_grade(this_examperiod_dict, examperiod, multiplier,
                                                    weight_se, weight_ce, has_practexam, sr_allowed, no_practexam)
            if subj_grade_str:
                log_subj_grade_dict[examperiod] = subj_grade_str

# --- end of "if examperiod in studsubj_dict"

# --- create student_ep_dicts with key ep1, ep2 and ep3 in student_dict[ep_key]
        if examperiod != c.EXAMPERIOD_EXEMPTION:
            # when student has reex or reex03 and this subject is not a reex,
            # then this_examperiod_dict does not exist
            # take in that case the values from the previous period_dict
            # use_examperiod is the examperiod that will be used - obviously
            use_examperiod = examperiod
            while use_examperiod:
                if use_examperiod in studsubj_dict:
                    break
                elif use_examperiod > 1:
                    use_examperiod -= 1
                else:
                    break
            use_studsubj_ep_dict = studsubj_dict.get(use_examperiod)

            ep_key = 'ep' + str(examperiod)

            if logging_on:
                logger.debug('----- examperiod: ' + str(examperiod) + ' ----- use_examperiod: ' + str(use_examperiod))

# --- calculate totals for ep1, ep2 and ep3 and put them in student_ep_dicts, not when exemption
            if ep_key in student_dict:

# - get the dict with key 'ep1' ep2' ep3' from student_dict to store totals
                calc_student_ep_dict = student_dict[ep_key]

                max_ep = use_studsubj_ep_dict.get('max_ep')
                max_pece = use_studsubj_ep_dict.get('max_pece')
                max_final = use_studsubj_ep_dict.get('max_final')
                max_ni = use_studsubj_ep_dict.get('max_ni')
                max_noin = use_studsubj_ep_dict.get('max_noin')

                if logging_on:
                    logger.debug('     max_ep: ' + str(max_ep))
                    logger.debug('     max_pece: ' + str(max_pece) + ' ' + str(type(max_pece)))
                    logger.debug('     max_final: ' + str(max_final)+ ' ' + str(type(max_final)))
                    logger.debug('     max_ni: ' + str(max_ni))
                    logger.debug('     max_noin: ' + str(max_noin))

# - calc no imput: pu noinput in student_ep for total and combi, to skip calculating result
                put_noinput_in_student_ep_dict(is_combi, use_studsubj_ep_dict, calc_student_ep_dict)

# - calculate count of each final grade
                calc_count_final_3457_core(calc_student_ep_dict, max_final,
                                gradetype, is_combi, is_core, multiplier, is_extra_nocount, is_thumbrule, subj_code)

# - calculate sum of final grades, separate for combi subjects
                calc_sum_finalgrade_and_combi(max_final, max_ep, max_ni, calc_student_ep_dict,
                                gradetype, multiplier, is_combi, is_extra_nocount, is_thumbrule, subj_code)

# - calculate CE-sum with subject_count
                calc_sum_pece(max_pece, max_ep, max_ni, calc_student_ep_dict,
                                gradetype, multiplier, weight_ce, exemp_no_ce, is_extra_nocount, is_thumbrule, subj_code)

# - after adding max_grades: check result requirements
                # when failed: 'failed' info is added to student_ep_dict
                # 'failed': {'insuff': ['Lichamelijke Opvoeding is onvoldoende.', 'Sectorwerkstuk is onvoldoende.'],
                calc_rule_issufficient(use_studsubj_ep_dict, calc_student_ep_dict,
                                        isevlexstudent, is_extra_nocount, thumb_rule_applies,
                                        rule_grade_sufficient, rule_gradesuff_notatevlex, subj_name)

            if logging_on and False:
                logger.debug('use_studsubj_ep_dict: ' + str(use_studsubj_ep_dict))
    if logging_on and False:
        logger.debug('>>>> end of loop through examperiods ')
# - end of loop through examperiods,
# ----------------------------------------

# put subj_grade_str in log_list, add '>' when it is maxperiod
    # subj_grade_str: '     Vrijstelling: SE:9,7 CE:6,0 Eindcijfer:8'
    if log_list is not None and log_subj_grade_dict:
        for ep in (4,1,2,3):
            subj_grade_str = log_subj_grade_dict.get(ep)
            if subj_grade_str:
                prefix = '   > ' if ep == gl_max_examperiod else '     '
                log_list.append(''.join((prefix, subj_grade_str)))

# - put the max values that will appear on the gradelist back in studsubj, also max_use_exem, gl_ni_se etc
    max_examperiod_dict = studsubj_dict.get(gl_max_examperiod)
    if logging_on:
        logger.debug('max_examperiod_dict: ' + str(max_examperiod_dict))
    """
     max_examperiod_dict: {
        'subj': 'cav', 
        'noin': {'vr': {'cav': ['SE']}}, 
        'ni': ['se'], 
        'max_ep': 4, 'max_sesr': None, 'max_pece': None, 'max_final': None, 
        'max_ni': ['se'], 
        'max_noin': {'vr': {'cav': ['SE']}}, 
        'max_use_exem': True}
    """
    gl_sesr = max_examperiod_dict.get('sesr')
    gl_pece = max_examperiod_dict.get('pece')
    gl_final = max_examperiod_dict.get('final')
    gl_use_exem = max_examperiod_dict.get('max_use_exem') or False

    sql_studsubj_values = save_max_grade_in_studsubj(studsubj_pk, gl_sesr, gl_pece, gl_final, gl_use_exem, gl_max_ni, gl_max_examperiod)
    if sql_studsubj_values:
        sql_studsubj_list.append(sql_studsubj_values)
# - end of calc_studsubj_result


def calc_noinput(examperiod, studsubj_dict, subj_code, weight_se, weight_ce, has_practexam,
                 has_exemption, has_sr, has_reex, has_reex03, exemp_no_ce):
    # PR2021-11-21 PR2021-12-27 PR2022-01-05
    # only called by calc_studsubj_result

    # from AWP Calculation.CalcEindcijfer_CijferOvg
    # function checks if this grade should have input, if so: add '-noinput' to grade_dict
    # Note: this function is only called when grade has no value
    # takes in account that in 2020 there was no central exam
    #  when noinput: key is appendedd to key with 'noinput' in this_examperiod_dict
    """"""
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('---------  calc_noinput  --------- ')
        logger.debug('   examperiod: ' + str(examperiod))
        logger.debug('   subj_code: ' + str(subj_code))
        logger.debug('   exemp_no_ce: ' + str(exemp_no_ce))
    """
    67838: {'si_id': 9734, 'subj': 'ec', 'is_extra_nocount': True, 'has_exemption': True, 
        1: {'subj': 'ec', 'se': '7,4', 'sesr': '7.4', 'ni': ['ce'], 'max_ep': 4, 'max_sesr': None, 'max_pece': None, 'max_final': None, 
            'max_ni': ['se', 'ce'], 'max_use_exem': True}, 
        4: {'subj': 'ec', 'ni': ['se', 'ce'], 'max_ep': 4, 'max_sesr': None, 'max_pece': None, 'max_final': None, 
            'max_ni': ['se', 'ce'], 'max_use_exem': True}}, 

    this_examperiod_dict: {'subj': 'ec', 'se': '7,4', 'sesr': '7.4', 'ni': ['ce']} 
    """
    # dont skip calc noinput when is_extra_nocount
    # put se, sr, pe from first period also in reex and reex03

# - get exemption only if has_exem, reex only if has_reex,  reex03 only if has_reex03,
    if (examperiod == c.EXAMPERIOD_EXEMPTION and has_exemption) or \
            (examperiod == c.EXAMPERIOD_SECOND and has_reex) or \
            (examperiod == c.EXAMPERIOD_THIRD and has_reex03) or \
            (examperiod == c.EXAMPERIOD_FIRST):

        this_examperiod_dict = studsubj_dict.get(examperiod)

# - get grade info from this_examperiod_dict
        examtype_tuple = ('se', 'ce') if examperiod == c.EXAMPERIOD_EXEMPTION else \
                         ('se', 'sr', 'pe', 'ce')

    # - get sr only if has_sr, practexam if has_practexam
        for key_str in examtype_tuple:
            if logging_on:
                logger.debug(' - key: ' + str(key_str))
            if (key_str == 'sr' and has_sr) or \
                    (key_str == 'pe' and has_practexam) or \
                    (key_str in ('se', 'ce')):
                # PR2022-01-05 se, sr, pe grades are also stored in reexand reex03
                grade = this_examperiod_dict.get(key_str)

                if grade is None:
                    if logging_on:
                        logger.debug('   weight_se: ' + str(weight_se))
                        logger.debug('   weight_ce: ' + str(weight_ce))

                    has_no_input = False
                    if key_str in ('se', 'sr'):
                        if weight_se > 0:
                            has_no_input = True
                    elif key_str == 'pe':
                        if weight_ce > 0:
                            has_no_input = True
                    elif key_str == 'ce':
                        if weight_ce > 0:
                            if examperiod == c.EXAMPERIOD_EXEMPTION:
                                # CORONA: in 2020 there was no central exam, therefore:
                                #         in 2021: for certain subjects no central exam
                                # table 'schemeitem' contains field 'no_ce_years' with string with years without ce: "2020;2021"
                                # table 'studsubj' contains field 'exemption_year' with year of the exemption

                                # skip 'no_input' if exemption has no ce PR2022-05-26
                                if not exemp_no_ce:
                                    has_no_input = True
                            else:
                                has_no_input = True

                    if logging_on:
                        logger.debug('   has_no_input: ' + str(has_no_input))

                    if has_no_input:
                        if 'noin' not in this_examperiod_dict:
                            this_examperiod_dict['noin'] = {}
                        noin_dict = this_examperiod_dict['noin']

                        if examperiod == c.EXAMPERIOD_EXEMPTION:
                            # keys 'vr', 'h3', 'h2', 'pe', 'ce', 'se', 'sr' are used to create separate lines in noinput info
                            # 'noin': {'vr': {'cav': ['se']}, 'pe': {'bw': ['se', 'ce']}, 'se': ['mm1'], 'ce': ['ec'], 'h3': ['ac']}
                            if 'vr' not in noin_dict:
                                noin_dict['vr'] = {}
                            vr_dict = noin_dict['vr']

                            if subj_code not in vr_dict:
                                vr_dict[subj_code] = []

                            if key_str not in vr_dict[subj_code]:
                                vr_dict[subj_code].append(key_str.upper())

                            # keys 'vr', 'h3', 'h2', 'pe', 'ce', 'se', 'sr' are used to create separate lines in noinput info
                            # 'noin': {'vr': {'cav': ['se']}, 'pe': {'bw': ['se', 'ce']}, 'se': ['mm1'], 'ce': ['ec'], 'h3': ['ac']}

                        else:

                            mapped_key_str = 'h3' if key_str == 'ce' and examperiod == c.EXAMPERIOD_THIRD else \
                                'h2' if key_str == 'ce' and examperiod == c.EXAMPERIOD_SECOND else \
                                    key_str

                            if mapped_key_str not in noin_dict:
                                noin_dict[mapped_key_str] = []

                            if subj_code not in noin_dict[mapped_key_str]:
                                noin_dict[mapped_key_str].append(subj_code)

                        if logging_on:
                            logger.debug('   noin_dict: ' + str(noin_dict))

                        if 'ni' not in this_examperiod_dict:
                            this_examperiod_dict['ni'] = []
                        this_examperiod_dict['ni'].append(key_str)

                        if logging_on:
                            logger.debug('   ni: ' + str(this_examperiod_dict['ni']))
                            logger.debug('   noin: ' + str(this_examperiod_dict['noin']))
# - end of calc_noinput

def calc_exemp_noce(exemption_year, no_ce_years):
# PR2022-05-26 calculate if exemption has ce
    # PR2022-05-26:
    # in studsubj field 'exemption_year' contains the examyear of the exemption
    # the schemeitem field 'no_ce_years' contains string with examyears without CE, i.e. '2020;2021'
    # if exemption_year is in no_ce_years: no_ce_exam = True

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------  calc_exemp_noce  ----------')
        logger.debug('   exemption_year: ' + str(exemption_year))
        logger.debug('no_ce_years: ' + str(no_ce_years))

    no_ce_exam = False
    if exemption_year and no_ce_years:
        no_ce_years_arr = no_ce_years.split(';')
        if logging_on:
            logger.debug('   no_ce_years_arr: ' + str(no_ce_years_arr))
        if str(exemption_year) in no_ce_years_arr:
            no_ce_exam = True

            if str(exemption_year) in no_ce_years_arr:
                no_ce_exam = True
    if logging_on:
        logger.debug(' >>> no_ce_exam: ' + str(no_ce_exam))

    return no_ce_exam
# end of calc_exemp_noce


def calc_max_grades(this_examperiod, this_examperiod_dict, studsubj_dict, gradetype):  # PR2021-12-21
    # PR2021-11-21 from AWP Calculations.CalcEindcijfer_Max
    # values of examperiod are: 1, 2, 3

    # PR2020-05-18 Andere aanpak berekening Max cijfers per tijdvak: bereken meteen of Vrst gebruikt moet worden ipv eerst Max en dan Vrst.
    # - bereken eerst de 'kale' eindcijfers per tijdvak in CalcEindcijfer_CijferOvg
    # - doorloop Tv01, Tv02 en Tv03 om Max te bepalen, incl Vrst
    # - return values: MaxSE(), MaxPeCe(),  MaxEind(),  MaxUseVrst(),  MaxCheckVrst()
    # bereken MaxSE, MaxPeCe, MaxEind. DIt is het hoogste cijfer van het betreffende tijdvak, rekening houdend met Her en Vrst
    # 'NB: geen NoInput gebruiken, hoogste wordt altijd weergegeven ook al is een van de 2 niet ingevuld of als geen Her

    # - function is only called when this_examperiod exists in studsubj_dict
    # loop through examperiods, in order: ep_01, ep_02, ep_03;

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------  calc_max_grades  ----------')
        logger.debug('     this_examperiod: ' + str(this_examperiod))

# - loop through examperiod: firstperiod, reex and reex03

# - get previous exam period:
    #   - if reex03:      get reex period if exists, get firstperiod otherwise
    #   - if reex:        get firstperiod otherwise
    #   - if firstperiod: get exemption if exists, else None
    #   firstperiod should always exist
    previous_examperiod = None
    if this_examperiod == c.EXAMPERIOD_THIRD:
        if c.EXAMPERIOD_SECOND in studsubj_dict:
            previous_examperiod = c.EXAMPERIOD_SECOND
        else:
            previous_examperiod = c.EXAMPERIOD_FIRST
    elif this_examperiod == c.EXAMPERIOD_SECOND:
        previous_examperiod = c.EXAMPERIOD_FIRST
    elif this_examperiod == c.EXAMPERIOD_FIRST:
        if c.EXAMPERIOD_EXEMPTION in studsubj_dict:
            previous_examperiod = c.EXAMPERIOD_EXEMPTION

    if logging_on:
        logger.debug('     previous_examperiod: ' + str(previous_examperiod))

    max_sesr, max_pece, max_final, max_ni, max_noin, max_use_exemption = None, None, None, [], [], False
    max_examperiod = None

# previous_examperiod is None when:
    #  - this is exemption or
    #  - this is first examperiod and no exemption
# when previous_examperiod is None
    #  - put values of first period in max_ fields

    if previous_examperiod is None:
        max_examperiod = this_examperiod
        max_sesr = this_examperiod_dict.get('sesr')
        max_pece = this_examperiod_dict.get('pece')
        max_final = this_examperiod_dict.get('final')
        max_ni = this_examperiod_dict.get('ni') or []
        max_noin = this_examperiod_dict.get('noin') or []
        max_use_exemption = (this_examperiod == c.EXAMPERIOD_EXEMPTION)
        if logging_on:
            logger.debug('     previous_examperiod is None ')
            logger.debug('     max_examperiod = this_examperiod: ' + str(max_examperiod))
            logger.debug('     max_ni: ' + str(max_ni))
    else:

# - get previous examperiod_dict
        prev_examperiod_dict = studsubj_dict.get(previous_examperiod)

        if logging_on:
            logger.debug('     this_examperiod_dict: ' + str(this_examperiod_dict))
            logger.debug('     prev_examperiod_dict: ' + str(prev_examperiod_dict))

        this_ni = this_examperiod_dict.get('ni')
        prev_ni = prev_examperiod_dict.get('ni')

        if logging_on:
            logger.debug('     this_ni: ' + str(this_ni))
            logger.debug('     prev_ni: ' + str(prev_ni))

        if this_examperiod == c.EXAMPERIOD_FIRST:
            # (exemption and firstperiod without exemption are already filtered out)
            # when exemption or first period have no input:
            #  - make exemption the max period
            # otherwise:
            #  - compare firstperiod and exemption

            if prev_ni or this_ni:
                # make max_use_exemption = True when exemption has no input

                max_examperiod = c.EXAMPERIOD_EXEMPTION
                max_sesr = prev_examperiod_dict.get('sesr')
                max_pece = prev_examperiod_dict.get('pece')
                max_final = prev_examperiod_dict.get('final')
                max_ni = prev_examperiod_dict.get('ni') or []
                max_noin = prev_examperiod_dict.get('noin') or []
                max_use_exemption = True

                if logging_on:
                    logger.debug('if prev_ni or this_ni')
                    logger.debug('     max_ni: ' + str(max_ni))
                    logger.debug('     max_noin: ' + str(max_noin))
                    logger.debug('     max_use_exemption: ' + str(max_use_exemption))


# ---  examperiod is reex or reex03
        elif this_examperiod in (c.EXAMPERIOD_SECOND, c.EXAMPERIOD_THIRD):

            # when this is reex or reex03 examperiod and this period has no input:
            # - make reex / reex03 the max period, to show 'noinput' on the log_list and gradelist
            if this_ni:
                max_examperiod = this_examperiod
                max_sesr = this_examperiod_dict.get('sesr')
                max_pece = this_examperiod_dict.get('pece')
                max_final = this_examperiod_dict.get('final')
                max_ni = this_examperiod_dict.get('ni') or []
                max_noin = this_examperiod_dict.get('noin') or []
                max_use_exemption = False

                if logging_on:
                    logger.debug('if this_ni')
                    logger.debug('     max_ni: ' + str(max_ni))
                    logger.debug('     max_noin: ' + str(max_noin))
                    logger.debug('     max_use_exemption: ' + str(max_use_exemption))

            elif prev_ni:
                # if reex03: previous = reex if exists, else firstperiod
                # if reex:   previous = firstperiod

                # when this period has input and previous period has no input:
                # - set max_examperiod = this_examperiod

                max_examperiod = this_examperiod
                max_sesr = this_examperiod_dict.get('max_sesr')
                max_pece = this_examperiod_dict.get('max_pece')
                max_final = this_examperiod_dict.get('max_final')
                max_ni = this_examperiod_dict.get('max_ni') or []
                max_noin = this_examperiod_dict.get('max_noin') or []
                max_use_exemption = this_examperiod_dict.get('max_use_exem', False)
            # else: # if reex / reex03 has input compare
                # compare previous_examperiod and this examperiod
                # happens further in this function

                if logging_on:
                    logger.debug('elif prev_ni')
                    logger.debug('     max_ni: ' + str(max_ni))
                    logger.debug('     max_noin: ' + str(max_noin))
                    logger.debug('     max_use_exemption: ' + str(max_use_exemption))

            if logging_on:
                logger.debug('>>>> prev_examperiod_dict: ' + str(prev_examperiod_dict))
                logger.debug('>>>> prev_examperiod_dict.get(sesr): ' + str(prev_examperiod_dict.get('sesr')))
                logger.debug('>>>> prev_ni: ' + str(prev_ni))

# - reex and reex03 have no sesr. Use sesr of first period instead, also put se and sr in ni if exists in prev period
            # PR2021-12-27 not any more, when calculating final grade of reex and reex03,
            # the values of se, sr, sesr, pe will pe put in the reex and reex03 grade
            # was:
            #this_examperiod_dict['sesr'] = prev_examperiod_dict.get('sesr')
            #if (prev_ni) and ('se' in prev_ni or 'sr' in prev_ni):
            #    if 'se' in prev_ni:
            #        this_ni.append('se')
            #    if 'sr' in prev_ni:
            #        this_ni.append('sr')
            #    this_examperiod_dict['ni'] = this_ni

# - if both this_examperiod and previous_examperiod have values: compare
        # - calculate which examperiod gives the highest final grade, use max_value in prev period
        if max_examperiod is None:
            this_finalgrade = this_examperiod_dict.get('final')
            prev_finalgrade = prev_examperiod_dict.get('max_final')

            if logging_on:
                logger.debug('------------- compare this and prev examperiod ------------------')
                logger.debug('..... this_finalgrade: ' + str(this_finalgrade) + ' ' + str(type(this_finalgrade)))
                logger.debug('..... prev_finalgrade: ' + str(prev_finalgrade) + ' ' + str(type(prev_finalgrade)))
            # prev_examperiod_dict: {
            #       'se': '6.0', 'sesr': '6.0', 'ce': '3.0', 'pece': '3.0', 'final': '5',
            #       'max_ep': 1, 'max_sesr': '6.0', 'max_pece': '3.0', 'max_final': '5'}

            if gradetype == c.GRADETYPE_02_CHARACTER:
                #'OvgTvMax kiest bij gelijke cijfers de eerste parameter als TvMax
                #'Tv01 heeft de voorkeur boven vrijstelling: daaarom Tv01 invullen als eerste parameter
                max_examperiod = calc_max_examperiod_gradetype_character(
                    this_examperiod, this_finalgrade,
                    previous_examperiod, prev_finalgrade)
                if logging_on:
                    logger.debug('     max_examperiod == calc_max_examperiod_gradetype_character')

            elif gradetype == c.GRADETYPE_01_NUMBER:
                this_pece = this_examperiod_dict.get('pece')
                prev_pece = prev_examperiod_dict.get('max_pece')

                max_examperiod = calc_max_examperiod_gradetype_decimal(
                    this_examperiod, this_finalgrade, this_pece,
                    previous_examperiod, prev_finalgrade, prev_pece)
                if logging_on:
                    logger.debug('     max_examperiod == calc_max_examperiod_gradetype_decimal')

# get max_use_exemption.
            # - is False when max_examperiod = this_examperiod
            # - is True  when max_examperiod = prev_period and prev_period = exemption
            # - is True  when max_examperiod = prev_period and use_exemption of prev_period = True

            if max_examperiod == this_examperiod:
                if logging_on:
                    logger.debug('     max_examperiod == this_examperiod')
                # max_examperiod = this_examperiod
                max_sesr = this_examperiod_dict.get('sesr')
                max_pece = this_examperiod_dict.get('pece')
                max_final = this_examperiod_dict.get('final')
                max_ni = this_examperiod_dict.get('ni') or []
                max_noin = this_examperiod_dict.get('noin') or []
                max_use_exemption = False
            else:
                if logging_on:
                    logger.debug('     else: max_examperiod = previous_examperiod')
                #max_examperiod = previous_examperiod
                max_sesr = prev_examperiod_dict.get('max_sesr')
                max_pece = prev_examperiod_dict.get('max_pece')
                max_final = prev_examperiod_dict.get('max_final')
                max_ni = prev_examperiod_dict.get('max_ni') or []
                max_noin = prev_examperiod_dict.get('max_noin') or []
                max_use_exemption = prev_examperiod_dict.get('max_use_exem', False)
# -----------------------------------------------------------

# put max values in this_examperiod_dict
    # max_examperiod is used to put (h) (h3) or (vr) behind grade
    this_examperiod_dict['max_ep'] = max_examperiod
    this_examperiod_dict['max_sesr'] = max_sesr
    this_examperiod_dict['max_pece'] = max_pece
    this_examperiod_dict['max_final'] = max_final
    this_examperiod_dict['max_ni'] = max_ni
    this_examperiod_dict['max_noin'] = max_noin
    this_examperiod_dict['max_use_exem'] = max_use_exemption

    if logging_on:
        logger.debug('max_examperiod: ' + str(max_examperiod))
        logger.debug('..... max_sesr: ' + str(max_sesr))
        logger.debug('..... max_pece: ' + str(max_pece))
        logger.debug('..... max_final ' + str(max_final))
        logger.debug('..... max_ni:   ' + str(max_ni))
        logger.debug('..... max_noin:   ' + str(max_noin))
        logger.debug('..... max_use_exemption: ' + str(max_use_exemption))

    return max_examperiod, max_ni
# - end of calc_max_grades


def save_max_grade_in_studsubj(studsubj_pk, gl_sesr, gl_pece, gl_final, gl_use_exem,
        gl_max_ni, gl_examperiod):  # PR2021-12-30 PR2022-01-03
    # only called by calc_studsubj_result
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' -----  save_max_grade_in_studsubj -----')
    sql_studsubj_values = []
    try:
        # gl_max_ni =  ['sr', 'ce']
        gl_sesrgrade_str = ''.join(("'", gl_sesr, "'")) if gl_sesr else 'NULL'
        gl_pecegrade_str = ''.join(("'", gl_pece, "'")) if gl_pece else 'NULL'
        gl_finalgrade_str = ''.join(("'", gl_final, "'")) if gl_final else 'NULL'
        gl_use_exem_str = 'TRUE' if gl_use_exem else 'FALSE'

        gl_ni_se_str = 'TRUE' if 'se' in gl_max_ni else 'FALSE'
        gl_ni_sr_str = 'TRUE' if 'sr' in gl_max_ni else 'FALSE'
        gl_ni_pe_str = 'TRUE' if 'pe' in gl_max_ni else 'FALSE'
        gl_ni_ce_str = 'TRUE' if 'ce' in gl_max_ni else 'FALSE'
        gl_examperiod_str = str(gl_examperiod) if gl_examperiod else 'NULL'

        sql_studsubj_values = [
            str(studsubj_pk),
            gl_sesrgrade_str,
            gl_pecegrade_str,
            gl_finalgrade_str,
            gl_use_exem_str,

            gl_ni_se_str,
            gl_ni_sr_str,
            gl_ni_pe_str,
            gl_ni_ce_str,
            gl_examperiod_str
        ]
        """
        sql_keys = {'studsubj_id': studsubj_pk}
        sql_list = ["UPDATE students_studentsubject AS ss",
                    " SET gradelist_sesrgrade = ", gl_sesrgrade_str,
                    ", gradelist_pecegrade = ", gl_pecegrade_str,
                    ", gradelist_finalgrade = ", gl_finalgrade_str,
                    ", gradelist_use_exem = ", gl_use_exem_str,

                    ", gl_ni_se = ", gl_ni_se_str,
                    ", gl_ni_sr = ", gl_ni_sr_str,
                    ", gl_ni_pe = ", gl_ni_pe_str,
                    ", gl_ni_ce = ", gl_ni_ce_str,
                    ", gl_examperiod = ", gl_examperiod_str,

                    " WHERE ss.id = %(studsubj_id)s::INT"
                  ]

        if logging_on:
            sql_list.append(" RETURNING ss.id, ss.gradelist_sesrgrade, ss.gradelist_pecegrade, ss.gradelist_finalgrade, ")
            sql_list.append("ss.gradelist_use_exem, ss.gl_examperiod, ss.gl_ni_se, ss.gl_ni_sr, ss.gl_ni_pe, ss.gl_ni_ce")

        sql = ''.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)

            if logging_on:
                rows = cursor.fetchall()
                if rows:
                    logger.debug('............................................')
                    for row in rows:
                        logger.debug('row: ' + str(row))
        """
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return sql_studsubj_values
# - end of save_max_grade_in_studsubj


def calc_sum_finalgrade_and_combi(max_final, max_ep, max_ni, calc_student_ep_dict, gradetype, multiplier,
                                  is_combi, is_extra_nocount, is_thumbrule, subj_code):
    # function adds final-grade * multiplier to final.sum, adds multiplier to subj_count

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' -----  calc_sum_finalgrade_and_combi  -----')
        logger.debug('     calc_student_ep_dict: ' + str(calc_student_ep_dict))
    """
    calc_student_ep_dict: {'ep': 1, 
                           'final': {'sum': -5994, 'cnt': 6, 'info': ' ne:- pa:- en:- sp:- ec:- ac:-'}, 
                           'combi': {'sum': 18, 'cnt': 3, 'info': ' mm1:5 cav:6 lo:7'}, 
                           'pece': {'sumX10': -59994, 'cnt': 6, 'info': ' ne:- pa:- en:- sp:- ec:- ac:-'}, 
                           'count': {'c3': 0, 'c4': 0, 'c5': 0, 'c6': 0, 'c7': 0, 'core4': 0, 'core5': 0}, 
                           'noin': {
                                'ce': ['ne', 'pa', 'en', 'sp', 'ec', 'ac'], 
                                'pe': ['ac']}}
    """
    try:
# - calc only when gradetype is number
# - skip when subject is 'is_extra_nocount' or 'is_thumbrule'
        if gradetype == c.GRADETYPE_01_NUMBER and not is_extra_nocount and not is_thumbrule:
            key_str = 'combi' if is_combi else 'final'
            ep_dict = calc_student_ep_dict[key_str]
            """
            'final': {'sum': -5994, 'cnt': 6, 'info': ' ne:- pa:- en:- sp:- ec:- ac:-'}, 
            'combi': {'sum': 18, 'cnt': 3, 'info': ' mm1:5 cav:6 lo:7'}, 
            """
    # - add key with default value if key doesn't exist
            for key_str in ('sum', 'cnt', 'info'):
                if key_str not in ep_dict:
                    default_value = '' if key_str == 'info' else 0
                    ep_dict[key_str] = default_value

    # - add multiplier to cnt_final, to cnt_combi when combi
            # multiplier = 1, except when sectorprogramma PBL CUR
            ep_dict['cnt'] += multiplier

            max_final_int = 0

    # - make sum negative when no_input, to show '-' as combi grade or final sum  when one of the subejcts has noinput
            if max_ni:
                max_final_int = -999
            else:
    # - convert string to integer - final grade is integer of 'ovg'
                if isinstance(max_final, int):
                    max_final_int = max_final
                elif isinstance(max_final, str):
                    max_final_int = int(max_final)

    # - add final grade to sum_final, to sum_combi when combi
            if max_final_int:
                ep_dict['sum'] += max_final_int * multiplier

    # - add subj_code and final grade to info_pece:
            max_final_str = str(max_final_int) if max_final_int > 0 else '-'
            ep_dict['info'] += ''.join((' ', subj_code, ':', str(max_final_str)))

    # - add '2x','vr','h','h3' to grade
            gradeinfo_extension = get_gradeinfo_extension(multiplier, max_ep)
            if gradeinfo_extension:
                ep_dict['info'] += gradeinfo_extension

            if logging_on:
                logger.debug('     ep_dict: ' + str(ep_dict))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
# - end of calc_sum_finalgrade_and_combi


def calc_sum_pece(max_pece, max_ep, max_ni, calc_student_ep_dict,
                  gradetype, multiplier, weight_ce, exemp_no_ce, is_extra_nocount, is_thumbrule, subj_code):  # PR2021-12-22
    # function adds CE-grade * multiplier to CE-sum, adds final-grade * multiplier to final-sum, adds multiplier to subj_count

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' -----  calc_sum_pece  -----')
        logger.debug('     max_ep: ' + str(max_ep))
        logger.debug('     max_pece: ' + str(max_pece) + ' ' + str(type(max_pece)))
        logger.debug('     max_ni: ' + str(max_ni))
        logger.debug('     multiplier: ' + str(multiplier))
        logger.debug('     weight_ce: ' + str(weight_ce))

        logger.debug('     calc_student_ep_dict: ' + str(calc_student_ep_dict))

    """
    calc_student_ep_dict: {'ep': 1, 
        'final': {'sum': 42, 'cnt': 7, 'info': ' ne:5 pa:7(vr) en:6 wk:6 nask1:5 nask2:6 ta:7'}, 
        'combi': {'sum': 19, 'cnt': 3, 'info': ' mm1:5 cav:8(vr) lo:6(vr)'}, 
        'pece': {'sumX10': 372, 'cnt': 7, 'info': ' ne:4,1 pa:-(vr) en:6,2 wk:5,6 nask1:5,8 nask2:6,9 ta:8,6'}, 
        'count': {'c3': 0, 'c4': 0, 'c5': 2, 'c6': 3, 'c7': 2, 'core4': 0, 'core5': 0}}
    """

    # calc only when :
    #  - gradetype is number
    #  - weight_ce > 0
    #  - exemption has central exam
    #  - subject is not 'is_extra_nocount'
    #  - subject is not 'is_thumbrule'

    if gradetype == c.GRADETYPE_01_NUMBER and weight_ce > 0 and not exemp_no_ce and not is_extra_nocount and not is_thumbrule:
        try:
            pece_dict = calc_student_ep_dict['pece']

            for key_str in ('sumX10', 'cnt', 'info'):
                if key_str not in pece_dict:
                    default_value = '' if key_str == 'info' else 0
                    pece_dict[key_str] = default_value

            if logging_on:
                logger.debug('     pece_dict: ' + str(pece_dict) + ' ' + str(type(pece_dict)))
                logger.debug('     max_ep: ' + str(max_ep) + ' ' + str(type(max_ep)))
                logger.debug('     max_pece: ' + str(max_pece) + ' ' + str(type(max_pece)))
                logger.debug('     multiplier: ' + str(multiplier) + ' ' + str(type(multiplier)))

    # - add multiplier to count dict (multiplier =1, except when sectorprogramma PBL
            pece_dict['cnt'] += multiplier

            if logging_on:
                logger.debug('     pece_dict[cnt]: ' + str(pece_dict['cnt']) + ' ' + str(type(pece_dict['cnt'])))

            max_pece_x10_int = 0
            max_pece_str = '-'
            if 'pe' in max_ni or 'ce' in max_ni:
                # make sum negatve when no_input, to show '-' as combi grade or final sum  when one of the subejcts has noinput
                max_pece_x10_int = -9999
            elif max_pece:
                max_pece_str = str(max_pece).replace('.', ',')
                max_pece_dot = max_pece.replace(',', '.')
                if '.' in max_pece_dot:
                    max_pece_dot = max_pece_dot.replace('.', '')
                else:
                    max_pece_dot += '0'
                max_pece_x10_int = int(max_pece_dot)

            if logging_on:
                logger.debug('     max_pece_x10_int: ' + str(max_pece_x10_int) + ' ' + str(type(max_pece_x10_int)))

    # - add pece_x10_int * multiplier to this_sum_int (multiplier =1, except when sectorprogramma PBL
            if max_pece_x10_int:
                pece_dict['sumX10'] += max_pece_x10_int * multiplier

    # - add subj_code and grade to info_pece:
            pece_dict['info'] += ''.join((' ', subj_code, ':', max_pece_str))

            # - add '2x','vr','h','h3' to grade
            gradeinfo_extension = get_gradeinfo_extension(multiplier, max_ep)
            if gradeinfo_extension:
                pece_dict['info'] += gradeinfo_extension

            if logging_on:
                logger.debug('     pece_dict: ' + str(pece_dict))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
# - end of calc_sum_pece


def get_gradeinfo_extension(multiplier, max_ep):

    # PR021-11-26
    # add '2x','vr','h','h3' to grade
    gradeinfo_extension = None
    addition_list = []
    if multiplier != 1:
        addition_list.append(str(multiplier) + 'x')
    if max_ep == c.EXAMPERIOD_EXEMPTION:
        addition_list.append('vr')
    if max_ep == c.EXAMPERIOD_SECOND:
        addition_list.append('h')
    if max_ep == c.EXAMPERIOD_THIRD:
        addition_list.append('h3')
    if addition_list:
        addition = ','.join(addition_list)
        gradeinfo_extension = ''.join(('(', str(addition), ')'))

    return gradeinfo_extension
# - end of get_gradeinfo_extension


def calc_count_final_3457_core(calc_student_ep_dict, max_final, gradetype, is_combi, is_core, multiplier,
                               is_extra_nocount, is_thumbrule, subj_code):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  calc_count_final_3457_core  ----- examperiod: ' +  str(calc_student_ep_dict.get('ep', '-')))
        logger.debug('     subj_code: ' + str(subj_code))
        logger.debug('     is_core: ' + str(is_core))
        logger.debug('     is_combi: ' + str(is_combi))
        logger.debug('     max_final: ' + str(max_final))
        logger.debug('     is_thumbrule: ' + str(is_thumbrule))

# - calc only when gradetype is number
# - skip count 3457 when subject is 'is_combi (combi grade is checked at the end by calc_combi_and_add_to_totals)
    #  - note: grade '3 or less' is not skipped when is_combi
    #  - note: core is not skipped when is_combi

# - skip when subject is 'is_extra_nocount' or 'is_thumbrule'
    if gradetype == c.GRADETYPE_01_NUMBER and not is_extra_nocount and not is_thumbrule:
        try:
            count_dict = calc_student_ep_dict['count']

            for grade_int in range(3, 8):  # range(start_value, end_value, step), end_value is not included!
                key_str = 'c' + str(grade_int)
                if key_str not in count_dict:
                    count_dict[key_str] = 0

            #key_str = 'info'
            #if key_str not in count_dict:
            #    count_dict[key_str] = ''

            #for key_str in ('cnt', 'core4', 'core5', 'info'):
            for key_str in ('core4', 'core5'):
                #default_value = '' if key_str == 'info' else 0
                default_value = 0
                if key_str not in count_dict:
                    count_dict[key_str] = default_value

            # skip count when is combi
            #if not is_combi:
            #    count_dict['cnt'] += multiplier

            if max_final:
                max_final_int = None
                if isinstance(max_final, int):
                    max_final_int = max_final
                elif isinstance(max_final, str):
                    max_final_int = int(max_final)

                if max_final_int:
                    if max_final_int < 3:
                        max_final_int = 3
                    if 6 < max_final_int < 11:
                        max_final_int = 7
        # skip count when is combi, except when max_final_int <= 3
                    if not is_combi or max_final_int == 3:
                        key_str = 'c' + str(max_final_int)
                        count_dict[key_str] += multiplier

                    # note: don't skip core when is combi
                    if is_core:
                        if 3 < max_final_int < 6:
                            key_str = 'core' + str(max_final_int)
                            count_dict[key_str] += multiplier

            if logging_on:
                logger.debug('count_dict: ' + str(count_dict))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
# - end of calc_count_final_3457_core


def calc_combi_and_add_to_totals(examperiod, student_ep_dict, log_list):  # PR2021-12-22
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' @@@@@@@@@@@@@@@@ -----  calc_combi_and_add_to_totals  -----')
        logger.debug('examperiod: ' + str(examperiod))
        logger.debug('student_ep_dict: ' + str(student_ep_dict))
    """
    student_ep_dict: {
        'combi': {
            'sum': 20, 
            'cnt': 3, 
            'info': ' mm1:6 cav:7 lo:7', 
            'final': '7', 
            'result': 'Combinatiecijfer: 7 (20/3) '}, 
    """
    combi_dict = student_ep_dict['combi']

    # skip calculating combi grade when no combi subjects - correct? PR2021-11-30
    if combi_dict:
        combi_cnt_int = combi_dict.get('cnt', 0)

# - calculate final combi grade
        combi_cnt_str, combi_sum_str, combi_final_str, combi_final_int = None, None, None, None
        if combi_cnt_int > 0:
            combi_cnt_str = str(combi_cnt_int)

            combi_sum_int = combi_dict.get('sum', 0)
            if combi_sum_int > 0:
                combi_sum_str = str(combi_sum_int)

                combi_avg_decimal_not_rounded = Decimal(combi_sum_str) / Decimal(combi_cnt_str)

                # round to integer
                combi_avg_decimal_rounded = grade_calc.round_decimal(combi_avg_decimal_not_rounded, 0)
                combi_final_str = str(combi_avg_decimal_rounded)
                combi_final_int = int(combi_final_str)

# - put final combi grade in student_ep_dict.combi.final
            combi_dict['final'] = combi_final_int

# - put combi in result
            combi_dict['result'] = ''.join((
                str(_('Combination grade')), ': ',
                combi_final_str if combi_final_str else '-',
                ' (',
                combi_sum_str if combi_sum_str else '-',
                '/',
                combi_cnt_str if combi_cnt_str else '-',
                ') '))

# - add 1 to count of final grades
            final_dict = student_ep_dict['final']
            final_dict['cnt'] += 1

# - add combi_final_int to sum of final grades
            if combi_final_int:
                final_dict['sum'] += combi_final_int

# add 'combi'' and combi grade to final_dict info:
            final_dict['info'] += ''.join((' ', 'combi', ':',
                combi_final_str if combi_final_str else '-'
                ))


# - add combi grade to calc_count_final_3457_core(use_studsubj_ep_dict, calc_student_ep_dict, gradetype, is_core, multiplier, log_list):
        is_thumbrule = False

        # note: here is_combi is False. When True it skips counting, this is used when for combi subjects
        calc_count_final_3457_core(
            calc_student_ep_dict=student_ep_dict,
            max_final=combi_final_int,
            gradetype=c.GRADETYPE_01_NUMBER,
            is_combi=False,
            is_core=False,
            multiplier=1,
            is_extra_nocount=False,   # is_extra_nocount is not True when combi subject
            is_thumbrule=is_thumbrule,
            subj_code='combi' # only for debugging
        )
# - end of calc_combi_and_add_to_totals


def calc_pece_avg(examperiod, student_ep_dict):  # PR2021-12-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('-----  calc_pece_avg  -----')
        logger.debug('     examperiod: ' + str(examperiod))
        logger.debug('     student_ep_dict: ' + str(student_ep_dict))
    # see https://www.examenblad.nl/veel-gevraagd/hoe-moeten-cijfers-worden-afgerond/2013
    # Een gemiddelde van 5,48333 is lager dan 5,5.

    """
    student_ep_dict: {
        'pece': {
            'sumX10': -19731, 
            'cnt': 6, 
            'info': ' ne:-(h) pa:-(h) en:10,0 ec:4,5 ac:6,1(2x)', 
            'avg': None, 
            'result': 'Gemiddeld CE-cijfer: - (-/6) '
        },
    """
    pece_dict = student_ep_dict['pece']

    # skip calculating combi grade when no combi subjects - correct? PR2021-11-30
    if pece_dict:
        pece_cnt_int = pece_dict.get('cnt', 0)
        pece_sumX10_int = pece_dict.get('sumX10', 0)
        pece_cnt_str, pece_sum_str = None, None
        pece_avg_dot, pece_avg_comma = None, '-'
        if pece_cnt_int > 0:
            pece_cnt_str = str(pece_cnt_int)
            if pece_sumX10_int > 0:
                pece_sumX10_decimal = Decimal(str(pece_sumX10_int))
                pece_sum_decimal = pece_sumX10_decimal / Decimal(10)
                pece_sum_str = str(pece_sum_decimal).replace('.', ',')

                # PR20220-05-27 DO NOT ROUND !!!
                #   Een gemiddelde van 5,48333 is lager dan 5,5.

                # was:
                # - round to one digit after dot
                #   pece_avg_decimal_rounded = grade_calc.round_decimal(pece_avg_decimal_not_rounded, 1)
                #   pece_avg_rounded_dot = str(pece_avg_decimal_rounded)
                #   pece_avg_rounded_comma = pece_avg_rounded_dot.replace('.', ',')

                # no need to use decimal
                pece_avg_dot = str(int(pece_sumX10_int / pece_cnt_int ) / 10)
                pece_avg_comma = pece_avg_dot.replace('.', ',')

                if logging_on:
                    logger.debug('     pece_avg_dot: ' + str(pece_avg_dot))

        if logging_on:
            logger.debug('     pece_avg_dot: ' + str(pece_avg_dot))
        # put avg in student_ep_dict.pece.avg
        pece_dict['avg'] = pece_avg_dot

        pece_dict['result'] = ''.join((
            # used in result_info
            str(_('Average CE grade')), ': ',
            pece_avg_comma if pece_avg_comma else '-',
            ' (', pece_sum_str if pece_sum_str else '-',
            '/', pece_cnt_str if pece_cnt_str else '-',
            ') '
        ))

        if logging_on:
            logger.debug(' >>> pece_dict: ' + str(pece_dict))
# - end of calc_pece_avg


def calc_final_avg(student_ep_dict):  # PR2021-12-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  calc_final_avg  -----')

    # calulate avergae final grade and put it back in student_ep_dict

    """
    student_ep_dict: {
        'final': {
            'sum': -3974, 
            'cnt': 7, 
            'info': ' ne:-(h) pa:-(h) en:7 ec:8 ac:-(2x) combi:7', 
            'avg': None, 
            'result': 'Gemiddeld eindcijfer: - (-/7) '
            },
    """
    # final_dict: {sum: 49, cnt: 7, info: ' ne:6 pa:9 en:6 sp:8 wk:6 ec:6 ac:8'}
    final_dict = student_ep_dict.get('final')
    final_sum = final_dict.get('sum')
    final_cnt = final_dict.get('cnt')

    final_count_str, final_sum_str, final_rounded_str, final_rounded_int = None, None, None, 0
    if final_cnt:
        final_count_str = str(final_cnt)
        if final_sum > 0:
            final_sum_str = str(final_sum)

            # final_avg will be rounded with 1 digit (unlike calc_pece_avg that is not rounded)
            final_avg = Decimal(final_sum) / Decimal(final_cnt)
            if final_avg > 0:
                final_rounded_str = str(grade_calc.round_decimal_from_str(final_avg, digits=1))
    # put avg in student_ep_dict.final.avg
    final_dict['avg'] = final_rounded_str

    final_dict['result'] = ''.join((
        str(_('Average final grade')), ': ',
        final_rounded_str if final_rounded_str else '-',
        ' (',
        final_sum_str if final_sum_str else '-',
        '/',
        final_count_str if final_count_str else '-',
        ') '))
# - end of calc_final_avg


def calc_max_examperiod_gradetype_decimal(examperiod_A, finalgrade_A, pece_A, examperiod_B, finalgrade_B, pece_B):
    # PR2021-11-21 from AWP Function Calculations.EindcijferTvMax
    # Function returns examperiod with the highest grade, returns A when grades are the same or not entered
    # when the final grades are the same, it returns te examperiod with the highest pece grade

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug( '  -----  calc_max_examperiod_gradetype_decimal  -----')
        logger.debug('..... examperiod_A: ' + str(examperiod_A))
        logger.debug('..... finalgrade_A: ' + str(finalgrade_A) + ' ' + str(type(finalgrade_A)))
        logger.debug('..... pece_A: ' + str(pece_A) + ' ' + str(type(pece_A)))
        logger.debug('..... examperiod_B: ' + str(examperiod_B) )
        logger.debug('..... finalgrade_B: ' + str(finalgrade_B) + ' ' + str(type(finalgrade_B)))
        logger.debug('..... pece_B: ' + str(pece_B) + ' ' + str(type(pece_B)))

    final_A_dot_nz = finalgrade_A.replace(',', '.') if finalgrade_A else "0"
    final_decimal_A =  Decimal(final_A_dot_nz)

    final_B_dot_nz =  finalgrade_B.replace(',', '.') if finalgrade_B else "0"
    final_decimal_B =  Decimal(final_B_dot_nz)

    if logging_on:
        logger.debug('..... final_decimal_A: ' + str(final_decimal_A) + ' ' + str(type(final_decimal_A)))
        logger.debug('..... final_decimal_B: ' + str(final_decimal_B) + ' ' + str(type(final_decimal_B)))

    max_examperiod = examperiod_A
    # from https://www.geeksforgeeks.org/python-decimal-compare-method/
    compare_final = final_decimal_B.compare(final_decimal_A)

    if compare_final == 1:  # b.compare(a) == 1 means b > a
        max_examperiod = examperiod_B
    elif compare_final == -1:  # b.compare(a) == -1 means b < a
        pass  # max_examperiod = examperiod_A
    elif compare_final == 0:  # # b.compare(a) == 0 means b = a
        pece_A_dot_nz = pece_A.replace(',', '.') if pece_A else "0"
        pece_decimal_A = Decimal(pece_A_dot_nz)

        pece_B_dot_nz = pece_B.replace(',', '.') if pece_B else "0"
        pece_decimal_B = Decimal(pece_B_dot_nz)

        compare_pece = pece_decimal_B.compare(pece_decimal_A)
        if compare_pece == 1:  # b.compare(a) == 1 means b > a
            max_examperiod = examperiod_B

    if logging_on:
        logger.debug('..... max_examperiod: ' + str(max_examperiod))
    return max_examperiod
# end of calc_max_examperiod_gradetype_decimal


def calc_max_examperiod_gradetype_character(ep_A, grade_A, ep_B, grade_B):
    # PR2021-11-21 from AWP Function Calculations.OvgTvMax
    # Function returns examperiod with the highest grade, returns A when grades are the same or not entered

    grade_A_lc = grade_A.lower() if grade_A else ''
    grade_B_lc = grade_B.lower() if grade_B else ''

    max_examperiod = ep_A
    if grade_A_lc == 'g':
        max_examperiod = ep_A
    elif grade_A_lc == 'v':
        if grade_B_lc == 'g':
            max_examperiod = ep_B
    elif grade_A_lc == 'o':
        if grade_B_lc in ('g', 'v'):
            max_examperiod = ep_B
    else:
        if grade_B_lc in ('g', 'v', 'o'):
            max_examperiod = ep_B
    return max_examperiod
# - end of calc_max_examperiod_gradetype_character


def put_noinput_in_student_ep_dict(is_combi, use_studsubj_ep_dict, calc_student_ep_dict):  # PR2021-12-22
    # function puts no_inpt in total , separate for combi subject
    # do not skip this function when subject is is_extra_nocount (grades must be entered, also when subject does not count)
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug( '-----  put_noinput_in_student_ep_dict  -----')
        logger.debug('   use_studsubj_ep_dict: ' + str(use_studsubj_ep_dict))
        logger.debug('   is_combi: ' + str(is_combi))
    """
    use_studsubj_ep_dict: {
        'subj': 'mm1', 'ni': ['se'], 'max_ep': 1, 'max_sesr': None, 'max_pece': None, 'max_final': None, 'max_ni': ['se'], 'max_use_exem': False}
    calc_student_ep_dict: {
        'combi': {'ni': {'mm1': ['se']}}, 
        'ni': {'ne': ['sr', 'ce'], 'ec': ['ce'], 'mm1': ['se']}}
        
    max_noin: {'vr': {'cav': ['se']}, 'pe': {'bw': ['se', 'ce']}, 'se': ['mm1'], 'ce': ['ec'], 'h3': ['ac']}
    """
    #try:
    if True:
        noin_dict = use_studsubj_ep_dict.get('max_noin')
        if noin_dict:
            if 'noin' not in calc_student_ep_dict:
                calc_student_ep_dict['noin'] = {}
            total_noin_dict = calc_student_ep_dict['noin']

            # keys are: 'vr', 'pe', 'se', 'sr', 'ce', 'h2', 'h3'
            #  when key is vr, pe: value is dict:  {'bw': ['se', 'ce']}, othherwise it is a list: ['ac']
            for key, value in noin_dict.items():
                if logging_on:
                    logger.debug( '-----')
                    logger.debug('   key: ' + str(key))
                    logger.debug('   value: ' + str(value))

                if key == 'vr':
                    if key not in total_noin_dict:
                        total_noin_dict[key] = {}
                    total_sub_dict = total_noin_dict[key]
                    if logging_on:
                        logger.debug('   total_sub_dict: ' + str(total_sub_dict))

                    # examtype_dict = {'cav': ['se']}
                    # value = ['ac']
                    for subj_code, examtype_list in value.items():
                        if subj_code not in total_sub_dict:
                            total_sub_dict[subj_code] = []
                        total_et_list = total_sub_dict[subj_code]
                        if logging_on:
                            logger.debug('   total_et_list: ' + str(total_et_list))
                        for et in examtype_list:
                            if logging_on:
                                logger.debug('   et: ' + str(et))
                            if et not in total_et_list:
                                total_et_list.append(et)
                else:
                    if key not in total_noin_dict:
                        total_noin_dict[key] = []
                    total_sub_list = total_noin_dict[key]
                    for subj_code in value:
                        if subj_code not in total_sub_list:
                            total_sub_list.append(subj_code)
        """
        'noin': {'vr': {'en': ['se', 'ce'], 'ec': ['se', 'ce'], 'mm12': ['se'], 'cav': ['se']}, 
                'sr': ['ne'], 'ce': ['ne'], 
                'se': ['mm1'], 'h3': ['ac']}
        """

    #except Exception as e:
    #    logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('calc_student_ep_dict: ' + str(calc_student_ep_dict))
# - end of put_noinput_in_student_ep_dict


def calc_rule_issufficient(use_studsubj_ep_dict, student_ep_dict, isevlexstudent,
                           is_extra_nocount, thumb_rule_applies, rule_grade_sufficient, rule_gradesuff_notatevlex, subj_name):  # PR2021-11-23
    # function checks if max final grade is sufficient (
    # - only when 'rule_grade_sufficient' for this subject is set True in schemeitem
    # - skip when evlex student and notatevlex = True
    # - skip when subject is 'is_extra_nocount'

    # rule 2022 Havo/VWO CUR + SXM
    # - voor de vakken cav en lo een voldoende of goed is behaald

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug( ' -----  calc_rule_issufficient  -----')
        logger.debug('use_studsubj_ep_dict: ' + str(use_studsubj_ep_dict))

# - skip when subject is 'is_extra_nocount' or when thumb_rule_applies
    if not is_extra_nocount or thumb_rule_applies:
        try:
            has_failed = False

# - skip when 'rule_grade_sufficient' for this subject is not set True in schemeitem
            if rule_grade_sufficient:

# - skip when evlex student and notatevlex = True
                if not isevlexstudent or not rule_gradesuff_notatevlex:

# - check if subject is sufficient
                    max_final = use_studsubj_ep_dict.get('max_final')
                    if max_final:
                        if max_final.isnumeric():
                            max_final_int = int(max_final)
                            if max_final_int < 6:
                                has_failed = True
                        else:
                            if max_final and max_final.lower() not in ('v', 'g'):
                                has_failed = True

# - if not: create dict with key 'insuff' if it does not exist
                    if has_failed:

                        max_final_str = str(_('not sufficient')) if max_final else ''.join(('<', str(_('Not entered')).lower(), '>'))
                        result_info = ''.join((subj_name, str(_(' is ')), max_final_str))

        # - if has_failed: create dict with key 'failed' if it does not exist
                        if 'failed' not in student_ep_dict:
                            student_ep_dict['failed'] = {}
                        failed_dict = student_ep_dict.get('failed')

                        if 'insuff' not in failed_dict:
                            failed_dict['insuff'] = []
                        failed_dict['insuff'].append(result_info)
            """
            'failed': {'insuff': ['Lichamelijke Opvoeding is onvoldoende.', 'Sectorwerkstuk is onvoldoende.'],
            """
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
# - end of calc_rule_issufficient


def calc_student_passedfailed(ep_list, student_dict, rule_avg_pece_sufficient, rule_core_sufficient, withdrawn, partial_exam,
                              has_subjects, depbase_is_vsbo, log_list, sql_student_list):
    # PR2021-12-31 PR2022-06-04
    # - calculate combi grade for each examperiod and add it to final and count dict in student_ep_dict
    # last_examperiod contains the grades that must pe put un the grade_list.
    # is reex03 when reex03 student, reex when reex student, firstperiod otherwise
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('--------- calc_student_passedfailed ---------------')
        logger.debug('student_dict: ' + str(student_dict))
    """
    student_dict: {
        'fullname': 'Gondim Matos, Mikeias', 'stud_id': 9226, 'country': 'Curacao', 'examyear_txt': '2021', 
        'school_name': 'Abel Tasman College', 'school_code': 'CUR13', 
        'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'depbase_code': 'Vsbo', 'dep_abbrev': 'V.S.B.O.', 
        'lvl_name': 'Theoretisch Kadergerichte Leerweg', 'lvlbase_code': 'TKL', 'level_req': True, 
        'sct_name': 'Economie', 'dep_id': 1, 'lvl_id': 117, 'sct_id': 265, 'scheme_id': 554, 'examnumber': '003', 
        'exemption_count': 4, 'sr_count': 1, 'reex_count': 1, 'reex03_count': 1, 

        67838: {'si_id': 9734, 'subj': 'ec', 'is_extra_nocount': True, 'has_exemption': True, 
	            1: {'subj': 'ec', 'se': '7.0', 'sesr': '7.0', 'ce': '4.0', 'pece': '4.0', 'final': '6', 
	                'max_ep': 4, 'max_sesr': '9.6', 'max_pece': None, 'max_final': None, 
	                'max_ni': ['ce'], 'max_noin': {'vr': {'ec': ['CE']}}, 'max_use_exem': True}, 
	            4: {'subj': 'ec', 'se': '9.6', 'sesr': '9.6', 
	                'noin': {'vr': {'ec': ['CE']}}, 
	                'ni': ['ce'], 
	                'max_ep': 4, 'max_sesr': '9.6', 'max_pece': None, 'max_final': None, 
	                'max_ni': ['ce'], 
	                'max_noin': {'vr': {'ec': ['CE']}}, 'max_use_exem': True}}, 

        67836: {'si_id': 9730, 'subj': 'ac', 'has_sr': True, 'has_reex': True, 'has_reex03': True, 
                3: {'subj': 'ac', 'se': '4.5'}, 
                1: {'subj': 'ac', 'se': '2.4', 'sr': '2.0', 'sesr': '2.4', 'pe': '2.0', 'ce': '2.0', 'pece': '2.0', 'final': '2'}, 
                2: {'subj': 'ac', 'se': '4.5', 'ce': '6.2'}},
        
        'ep1':  {'ep': 1, 
                'final': {'sum': -976, 'cnt': 7, 'info': ' ne:- pa:6 en:6(vr) wk:4 mm12:5 ac:2 combi:-', 'avg': None, 'result': 'Gemiddeld eindcijfer: - (-/7) '}, 
                'combi': {'sum': -988, 'cnt': 3, 'info': ' mm1:6 cav:-(vr) lo:5', 'final': None, 'result': 'Combinatiecijfer: - (-/3) '}, 
                'pece': {'sumX10': -9879, 'cnt': 4, 'info': ' ne:- en:7,0(vr) wk:3,0 ac:2,0', 'avg': None, 'result': 'Gemiddeld CE-cijfer: - (-/4) '}, 
                'count': {'c3': 1, 'c4': 1, 'c5': 1, 'c6': 2, 'c7': 0, 'core4': 1, 'core5': 0}, 
                'noin': {'sr': ['ne'], 'ce': ['ne'], 'vr': {'ec': ['CE'], 'cav': ['SE']}}, 
                'failed': {'insuff': ['Lichamelijke Opvoeding is onvoldoende.', 'Sectorwerkstuk is onvoldoende.']}
                }
        'ep2':  {'ep': 2, 'final': {'sum': -976, 'cnt': 7, 'info': ' ne:- pa:6 en:6(vr) wk:4 mm12:5 ac:2 combi:-', 'avg': None, 'result': 'Gemiddeld eindcijfer: - (-/7) '}, 'combi': {'sum': -988, 'cnt': 3, 'info': ' mm1:6 cav:-(vr) lo:5', 'final': None, 'result': 'Combinatiecijfer: - (-/3) '}, 'pece': {'sumX10': -9879, 'cnt': 4, 'info': ' ne:- en:7,0(vr) wk:3,0 ac:2,0', 'avg': None, 'result': 'Gemiddeld CE-cijfer: - (-/4) '}, 'count': {'c3': 1, 'c4': 1, 'c5': 1, 'c6': 2, 'c7': 0, 'core4': 1, 'core5': 0}, 'noin': {'sr': ['ne'], 'ce': ['ne'], 'vr': {'ec': ['CE'], 'cav': ['SE']}}, 'failed': {'insuff': ['Lichamelijke Opvoeding is onvoldoende.', 'Sectorwerkstuk is onvoldoende.']}}
        'ep3': {'ep': 3, 'final': {'sum': -1977, 'cnt': 7, 'info': ' ne:- pa:6 en:6(vr) wk:4 mm12:5 ac:-(h3) combi:-', 'avg': None, 'result': 'Gemiddeld eindcijfer: - (-/7) '}, 'combi': {'sum': -988, 'cnt': 3, 'info': ' mm1:6 cav:-(vr) lo:5', 'final': None, 'result': 'Combinatiecijfer: - (-/3) '}, 'pece': {'sumX10': -19898, 'cnt': 4, 'info': ' ne:- en:7,0(vr) wk:3,0 ac:-(h3)', 'avg': None, 'result': 'Gemiddeld CE-cijfer: - (-/4) '}, 'count': {'c3': 0, 'c4': 1, 'c5': 1, 'c6': 2, 'c7': 0, 'core4': 1, 'core5': 0}, 'noin': {'sr': ['ne'], 'ce': ['ne'], 'vr': {'ec': ['CE'], 'cav': ['SE']}, 'h3': ['ac']}, 'failed': {'insuff': ['Lichamelijke Opvoeding is onvoldoende.', 'Sectorwerkstuk is onvoldoende.']}} 


    student_dict: {
      'fullname': 'Bansingh, Akim', 'stud_id': 4377, 'country': 'Sint Maarten', 'examyear_txt': '2022', 'school_name': 'Milton Peters College', 'school_code': 'SXM01', 'islexschool': False, 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'depbase_code': 'Vsbo', 'dep_abbrev': 'V.S.B.O.', 
                    'lvl_name': 'Praktisch Kadergerichte Leerweg', 'lvlbase_code': 'PKL', 'level_req': True, 'sct_name': 'Economie', 'dep_id': 7, 'lvl_id': 8, 'sct_id': 20, 'scheme_id': 93, 'has_profiel': False, 'examnumber': '301', 'iseveningstudent': False, 'islexstudent': False, 
                    'bis_exam': False, 'partial_exam': False, 'exemption_count': 0, 
                    'sr_count': 0, 'reex_count': 0, 'reex03_count': 0, 'thumbrule_count': 0, 'withdrawn': False, 
    28266: {
            'si_id': 2555, 'subj': 'ac', 
            2: {'subj': 'ac', 'se': '5.4', 'sr': None, 'sesr': '5.4', 'pe': None, 'ce': None, 'pece': None, 'final': None}, 
            1: {'subj': 'ac', 'se': '5.4', 'sr': None, 'sesr': '5.4', 'pe': None, 'ce': '5.1', 'pece': '5.1', 'final': '5', 'max_ep': 1, 'max_sesr': '5.4', 'max_pece': '5.1', 'max_final': '5', 'max_ni': [], 'max_noin': [], 'max_use_exem': False}}, 
    28262: {'si_id': 2551, 'subj': 'cav', 
        1: {'subj': 'cav', 'se': '7.3', 'sr': None, 'sesr': '7.3', 'pe': None, 'ce': None, 'pece': None, 'final': '7', 'max_ep': 1, 'max_sesr': '7.3', 'max_pece': None, 'max_final': '7', 'max_ni': [], 'max_noin': [], 'max_use_exem': False}}, 
    28268: {'si_id': 2554, 'subj': 'ec', 
        1: {'subj': 'ec', 'se': '6.0', 'sr': None, 'sesr': '6.0', 'pe': None, 'ce': '6.5', 'pece': '6.5', 'final': '6', 'max_ep': 1, 'max_sesr': '6.0', 'max_pece': '6.5', 'max_final': '6', 'max_ni': [], 'max_noin': [], 'max_use_exem': False}}, 
    28259: {'si_id': 2559, 'subj': 'en', 
        1: {'subj': 'en', 'se': '5.9', 'sr': None, 'sesr': '5.9', 'pe': None, 'ce': '6.4', 'pece': '6.4', 'final': '6', 'max_ep': 1, 'max_sesr': '5.9', 'max_pece': '6.4', 'max_final': '6', 'max_ni': [], 'max_noin': [], 'max_use_exem': False}}, 28263: {'si_id': 2563, 'subj': 'fr', 1: {'subj': 'fr', 'se': '6.2', 'sr': None, 'sesr': '6.2', 'pe': None, 'ce': '3.5', 'pece': '3.5', 'final': '5', 'max_ep': 1, 'max_sesr': '6.2', 'max_pece': '3.5', 'max_final': '5', 'max_ni': [], 'max_noin': [], 'max_use_exem': False}}, 
    28261: {'si_id': 2550, 'subj': 'lo', 
        1: {'subj': 'lo', 'se': '7.6', 'sr': None, 'sesr': '7.6', 'pe': None, 'ce': None, 'pece': None, 'final': '8', 'max_ep': 1, 'max_sesr': '7.6', 'max_pece': None, 'max_final': '8', 'max_ni': [], 'max_noin': [], 'max_use_exem': False}}, 
      28260: {'si_id': 2549, 'subj': 'mm1', 
        1: {'subj': 'mm1', 'se': '6.1', 'sr': None, 'sesr': '6.1', 'pe': None, 'ce': None, 'pece': None, 'final': '6', 'max_ep': 1, 'max_sesr': '6.1', 'max_pece': None, 'max_final': '6', 'max_ni': [], 'max_noin': [], 'max_use_exem': False}}, 
      28258: {'si_id': 2548, 'subj': 'ne', 
        1: {'subj': 'ne', 'se': '7.3', 'sr': None, 'sesr': '7.3', 'pe': None, 'ce': '7.5', 'pece': '7.5', 'final': '7', 'max_ep': 1, 'max_sesr': '7.3', 'max_pece': '7.5', 'max_final': '7', 'max_ni': [], 'max_noin': [], 'max_use_exem': False}}, 
      28264: {'si_id': 2561, 'subj': 'sp', 
        1: {'subj': 'sp', 'se': '6.1', 'sr': None, 'sesr': '6.1', 'pe': None, 'ce': '5.4', 'pece': '5.4', 'final': '6', 'max_ep': 1, 'max_sesr': '6.1', 'max_pece': '5.4', 'max_final': '6', 'max_ni': [], 'max_noin': [], 'max_use_exem': False}}, 28267: {'si_id': 2557, 'subj': 'stg', 1: {'subj': 'stg', 'se': 'v', 'sr': None, 'sesr': 'v', 'pe': None, 'ce': None, 'pece': None, 'final': 'v', 'max_ep': 1, 'max_sesr': 'v', 'max_pece': None, 'max_final': 'v', 'max_ni': [], 'max_noin': [], 'max_use_exem': False}}, 
      28265: {'si_id': 2558, 'subj': 'wk', 
        1: {'subj': 'wk', 'se': '6.8', 'sr': None, 'sesr': '6.8', 'pe': None, 'ce': '5.9', 'pece': '5.9', 'final': '6', 'max_ep': 1, 'max_sesr': '6.8', 'max_pece': '5.9', 'max_final': '6', 'max_ni': [], 'max_noin': [], 'max_use_exem': False}}, 
    'ep1': {'ep': 1, 'final': {'sum': 41, 'cnt': 7, 'info': ' ac:5 ec:6 en:6 fr:5 ne:7 sp:6 wk:6'}, 
                    'combi': {'sum': 21, 'cnt': 3, 'info': ' cav:7 lo:8 mm1:6'}, 
                    'pece': {'sumX10': 403, 'cnt': 7, 'info': ' ac:5,1 ec:6,5 en:6,4 fr:3,5 ne:7,5 sp:5,4 wk:5,9'}, 
                    'count': {'c3': 0, 'c4': 0, 'c5': 2, 'c6': 4, 'c7': 1, 'core4': 0, 'core5': 0}}}
     ###########################
        
    """
    last_examperiod = None

# - loop through ep_list, skip exemption
    for examperiod in ep_list:
        if examperiod != c.EXAMPERIOD_EXEMPTION:

            last_examperiod = examperiod
            ep_key = 'ep' + str(examperiod)
            student_ep_dict = student_dict[ep_key]

            if logging_on:
                logger.debug(' ')
                logger.debug('--------- calc examperiod: ' + str(examperiod) + ' ---------------')

# +++ calculate passed / failed for each exam period (ep1, ep2, ep3)
            # and put result back in student_ep_dict
            # - if no result because of no input: skip calculating result
            if withdrawn:
                student_ep_dict['result_index'] = c.RESULT_WITHDRAWN
                if logging_on:
                    logger.debug('     withdrawn: ' + str(withdrawn))
            elif partial_exam:
                # PR2022-06-10 Richard Westerink ATC: partial exam student has always 'No result' on gradelist
                student_ep_dict['result_index'] = c.RESULT_NORESULT
            elif not has_subjects:
                student_ep_dict['result_index'] = c.RESULT_NORESULT
            else:
                calc_combi_and_add_to_totals(examperiod, student_ep_dict, log_list)

                calc_pece_avg(examperiod, student_ep_dict)

                calc_final_avg(student_ep_dict)

                result_no_input = calc_passfailed_noinput(student_ep_dict)
                # student_ep_dict['result_index'] = c.RESULT_NORESULT gets value in calc_passfailed_noinput
                if logging_on:
                    logger.debug('     result_no_input: ' + str(result_no_input))

    # - if no_input: create dict with key 'noresult' if it does not exist
                if not result_no_input:
                    has_failed = False
                    # calc_rule_issufficient is already called in subj loop
                    # student_ep_dict['result_index'] = c.RESULT_FAILED gets value in calc_passfailed
                    if depbase_is_vsbo:
                        has_failed_count6 = calc_passfailed_count6_vsbo(student_ep_dict)
                    else:
                        has_failed_count6 = calc_passfailed_count6_havovwo(student_ep_dict)
                    if has_failed_count6:
                        has_failed = True
                    if logging_on:
                        logger.debug('     has_failed_count6: ' + str(has_failed_count6))

                    if rule_core_sufficient:
                        # check for notatevlex is included in rule_core_sufficient
                        failed_core = calc_passfailed_core_rule(student_ep_dict)
                        if failed_core:
                            has_failed = True
                        if logging_on:
                            logger.debug('     failed_core: ' + str(failed_core))

                    if logging_on:
                        logger.debug('   ??????????????  rule_avg_pece_sufficient: ' + str(rule_avg_pece_sufficient))
                    if rule_avg_pece_sufficient:
                        # check for notatevlex is included in rule_avg_pece_sufficient
                        failed_pece_avg = calc_passfailed_pece_avg_rule(student_ep_dict)
                        if failed_pece_avg:
                            has_failed = True
                        if logging_on:
                            logger.debug('     failed_pece_avg: ' + str(failed_pece_avg))

                    if not has_failed:
                        student_ep_dict['result_index'] = c.RESULT_PASSED


            if logging_on:
                logger.debug('student_ep_dict: ' + str(student_ep_dict))

    if logging_on:
        logger.debug('--------- end of loop through calc examperiods ')

    # put calculated result of the last examperiod in log_list
    # if is_reex_student: last_examperiod = 2, is_reex03_student: last_examperiod = 3, last_examperiod = 1 otherwise

    last_ep_str = 'ep' + str(last_examperiod) if last_examperiod else None
    student_dict['last_ep'] = last_ep_str
    if last_examperiod:
        last_student_ep_dict = student_dict[last_ep_str]

        result_info_list, result_info_log_list = calc_add_result_to_log(last_examperiod, last_student_ep_dict,
                                                                        rule_avg_pece_sufficient, rule_core_sufficient)
        log_list.extend(result_info_log_list)

# - put result and grade info in sql_student_values
        sql_student_values = get_sql_student_values(student_dict, last_student_ep_dict, result_info_list)

        if sql_student_values:
            sql_student_list.append(sql_student_values)
# - calc_student_passedfailed


def calc_passfailed_noinput(student_ep_dict):  # PR2021-12-27 PR2022-01-04 PR2022-05-26
    # examperiod = ep1, ep2, ep3
    # noinput_dict: {1: {'sr': ['ne'], 'ce': ['ne', 'ec']}, 2: {'ce': ['ac']}, 3: {'ce': ['ac']}}
    #  - function returns 'no_input',
    #  - puts result_index = 0 in student_ep_dict['result_index']
    #  -  puts info in student_ep_dict['noin_info']
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('@@@@@@@@@@@@@@ -----  calc_passfailed_noinput  -----')
        logger.debug('     student_ep_dict: ' + str(student_ep_dict))
    """
    student_ep_dict: {
        'ep': 1, 
        'final': {'sum': 48, 'cnt': 8, 'info': ' ne:5 pa:7(vr) en:6 wk:6 nask1:5 nask2:6 ta:7 combi:6', 'avg': '6.0', 
                    'result': 'Gemiddeld eindcijfer: 6.0 (48/8) '}, 
        'combi': {'sum': 19, 'cnt': 3, 'info': ' mm1:5 cav:8(vr) lo:6(vr)', 'final': 6, 
                    'result': 'Combinatiecijfer: 6 (19/3) '}, 
        'pece': {'sumX10': 372, 'cnt': 6, 'info': ' ne:4,1 en:6,2 wk:5,6 nask1:5,8 nask2:6,9 ta:8,6',  'avg': None, 
                    'result': 'Gemiddeld CE-cijfer: 6,2 (37,2/6) '}, 
        'count': {'c3': 0, 'c4': 0, 'c5': 2, 'c6': 4, 'c7': 2, 'core4': 0, 'core5': 0}}

    """
    no_input = False
    noinput_list = []

    noin_dict = student_ep_dict.get('noin')
    if logging_on:
        logger.debug('noin_dict: ' + str(noin_dict))
        logger.debug('ni: ' + str(student_ep_dict.get('ni')))
    """
    noin_dict: {
        'sr': ['ne', 'ac'], 
        'ce': ['ne'], 
        'vr': {'en': ['se', 'ce'], 'ec': ['se', 'ce'], 'mm12': ['se'], 'cav': ['se']}, 
        'se': ['mm1']}
    """

    if noin_dict:
        no_input = True

        # loop through tuple to get lines in right ord
        for key in ('vr', 'se', 'sr', 'ce', 'pe', 'h2', 'h3'):
            value = noin_dict.get(key)
            if value:
                if logging_on:
                    logger.debug( 'key: ' + str(key))
                    logger.debug( 'value: ' + str(value))

                # keys 'vr', 'pe', 'se', 'sr' 'ce', h2', 'h3' 'are used to create separate lines in noinput info
                caption = _('Exemption') if key == 'vr' else \
                                _('Practical exam') if key == 'pe' else \
                                _('School exam') if key == 'se' else \
                                _('Re-examination school exam') if key == 'sr' else \
                                _('Central exam') if key == 'ce' else \
                                _('Re-examination') if key == 'h2' else \
                                _('Re-examination 3rd period') if key == 'h3' else '-'
                noin_info_str = str(caption) + ': '

                if key == 'vr':
                    for subj_code, subvalue in value.items():
                        if logging_on:
                            logger.debug('     value:     ' + str(value))
                            # value:     {'en': ['se', 'ce'], 'ec': ['se', 'ce'], 'mm12': ['se'], 'cav': ['se']}
                            logger.debug('     subj_code: ' + str(subj_code))
                            logger.debug('     subvalue:  ' + str(subvalue))
                        et_list = ','.join(subvalue)

                        noin_info_str += ''.join((subj_code, '(', et_list, ') '))
                    noin_info_str += str(_('Not entered')).lower()

                else:
                    noin_info_str += ','.join(value)
                    noin_info_str += ' ' + str(_('Not entered')).lower()

                if logging_on:
                    logger.debug('     noin_info_str: ' + str(noin_info_str))

                noinput_list.append(noin_info_str)

    if no_input:
        student_ep_dict['result_index'] = c.RESULT_NORESULT

        if 'noin_info' not in student_ep_dict:
            student_ep_dict['noin_info'] = []
        if noinput_list:
            student_ep_dict['noin_info'].extend(noinput_list)

        if logging_on:
            logger.debug('     student_ep_dict: ' + str(student_ep_dict))
        """
        student_ep_dict: {'ep': 1, 
            'final': {'sum': -1964, 'cnt': 8, 'info': ' ne:6 pa:6 en:5 wk:6 ec:4 ac:-(2x) combi:7', 'avg': None, 
                'result': 'Gemiddeld eindcijfer: - (-/8) '}, 
            'combi': {'sum': 21, 'cnt': 3, 'info': ' mm1:6 cav:8 lo:7', 'final': 7, 
                'result': 'Combinatiecijfer: 7 (21/3) '}, 
            'pece': {'sumX10': -19676, 'cnt': 7, 'info': ' ne:7,7 pa:5,9 en:6,7 wk:7,6 ec:4,3 ac:-(2x)', 'avg': None, 
                'result': 'Gemiddeld CE-cijfer: - (-/7) '}, 
            'count': {'c3': 0, 'c4': 1, 'c5': 1, 'c6': 3, 'c7': 1, 'core4': 0, 'core5': 0}, 
            'noin': {'praktijk': ['ac']}, 
            'result_index': 0, 
            'noin_info': []}
        """

    return no_input
# - end of calc_passfailed_noinput


def calc_passfailed_count6_vsbo(student_ep_dict):  #  PR2021-12-24 PR2022-05-26
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  calc_passfailed_count6_vsbo  -----')

    """
    'PR: slagingsregeling Vsbo
    '1a een kandidaat is geslaagd als voor al zijn vakken een eindcijfer 6 of hoger is behaald
    '1b een kandidaat is geslaagd als voor ten hoogste 1 vak een 5 heeft behaald en voor de overige vakken een 6 of hoger is behaald
    '1c een kandidaat is geslaagd als voor ten hoogste 1 vak een 4 is behaald en voor de overige vakken een 6 of hoger waarvan tenminste 1 een 7 of hoger
    '1d een kandidaat is geslaagd als voor 2 vakken een 5 is behaald en voor de overige vakken een 6 of hoger waarvan tenminste 1 een 7 of hoger
    """
    count_dict = student_ep_dict['count']
    c3 = count_dict.get('c3', 0)
    c4 = count_dict.get('c4', 0)
    c5 = count_dict.get('c5', 0)
    # NIU c6 = count_dict.get('c6', 0)
    c7 = count_dict.get('c7', 0)

    has_failed = False

    if c3:  # 1 of meer drieën of lager
        has_failed = True
        three_str = ' '.join((str(c3), str( _('three or lower') if c3 == 1 else _('threes or lower'))))
        result_info = ''.join((three_str, '.'))

    else:
        # kandidaat geen drieën of lager, alleen vieren of hoger
        four_str = ' '.join((str(c4), str( _('four') if c4 == 1 else _('fours'))))
        five_str = ' '.join((str(c5), str( _('five') if c5 == 1 else _('fives'))))
        seven_str = ' '.join((str(c7) if c7 else str(pgettext_lazy('geen', 'no')), str( _('seven or higher') if c7 == 1 else _('sevens or higher'))))

        if c4 > 1:  # meer dan 1 vier
            has_failed = True
            result_info = ''.join((four_str, '.'))

        elif c4 == 1:
            # 'kandidaat heeft 1 vier, de rest vijven of hoger

            if c5:  # kandidaat heeft 1 vier en 1 of meer vijven
                has_failed = True
                result_info = ''.join((four_str, str(_(' and ')), five_str, '.'))
            else:  # 'kandidaat heeft 1 vier en geen vijf
                if not c7:
                    has_failed = True
                result_info = ''.join((four_str, str(_(' and ')), seven_str, '.')) # '1 four and no sevens or higher.'

        else:
            # 'kandidaat heeft geen vier, alleen vijven of hoger
            if c5 > 2:
                # '3 of meer vijven
                has_failed = True
                result_info = ''.join((five_str, '.'))

            elif c5 == 2:
                # kandidaat heeft 2 vijven, rest zessen of hoger
                if not c7:  # geen zevens en hoger
                    has_failed = True
                result_info = ''.join((five_str, str(_(' and ')), seven_str, '.')) # '2 fives and no sevens or higher.'

            elif c5 == 1:
                # kandidaat heeft 1 vijf, rest zessen of hoger
                result_info = ''.join((five_str, str(_(' and ')), str(_('for the other subjects a 6 or higher.'))))

            else:
                # kandidaat heeft geen vijf, rest zessen of hoger
                result_info = str(_('For all subjects a 6 or higher.'))


# - if has_failed: create dict with key 'failed' if it does not exist
    if has_failed:
        student_ep_dict['result_index'] = c.RESULT_FAILED
        if 'failed' not in student_ep_dict:
            student_ep_dict['failed'] = {}
        failed_dict = student_ep_dict.get('failed')
# - add key 'cnt3457' with value 'result_info'
        failed_dict['cnt3457'] = result_info
    else:
# - if not has_failed: create dict with key 'passed' if it does not exist
        # note: student might have failed beacsuse of other rules
        if 'passed' not in student_ep_dict:
            student_ep_dict['passed'] = {}
        passed_dict = student_ep_dict.get('passed')
# - add key 'cnt3457' with value 'failed_info'
        passed_dict['cnt3457'] = result_info

    if logging_on:
        logger.debug('     student_ep_dict: ' + str(student_ep_dict))

    return has_failed
# end of calc_passfailed_count6_vsbo


def calc_passfailed_count6_havovwo(student_ep_dict):  #  PR2021-11-30  PR2022-05-26
    # add result to combi_dict result:
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('-----  calc_passfailed_count6_havovwo  -----')
        logger.debug('student_ep_dict: ' + str(student_ep_dict))

    count_dict = student_ep_dict['count']
    c3 = count_dict.get('c3', 0)
    c4 = count_dict.get('c4', 0)
    c5 = count_dict.get('c5', 0)
    # NIU: c6 = count_dict.get('c6', 0)
    c7 = count_dict.get('c7', 0)

    final_dict = student_ep_dict['final']
    avgfinal_str = final_dict.get('avg','')
    avgfinal_lt_6 = True
    if avgfinal_str:
        avgfinal_lt_6 = (Decimal(avgfinal_str).compare(Decimal(6)) < 0)
        # PR2022-05-29 debug: replace dot after Decimal(avgfinal_str), otherwise you get error ConversionSyntax
        avgfinal_str = avgfinal_str.replace('.', ',')

    has_failed = False
    result_info = ''
    if c3:  # 1 of meer drieën of lager
        has_failed = True
        three_str = ' '.join((str(c3), str( _('three or lower') if c3 == 1 else _('threes or lower'))))
        result_info = ''.join((three_str, '.'))

    else:
        # kandidaat geen drieën of lager, alleen vieren of hoger
        four_str = ' '.join((str(c4), str( _('four') if c4 == 1 else _('fours'))))
        five_str = ' '.join((str(c5), str( _('five') if c5 == 1 else _('fives'))))
        seven_str = ' '.join((str(c7) if c7 else 'no', str( _('seven or higher') if c7 == 1 else _('sevens or higher'))))

        if c4 > 1:  # meer dan 1 vier
            has_failed = True
            result_info = ''.join((four_str, '.'))

        elif c4 == 1:
            # 'kandidaat heeft 1 vier, de rest vijven of hoger
            result_info = ''.join((four_str, str(_(' and ')), five_str))
            if c5 > 1:
                # '1 vier en 2 of meer vijven
                has_failed = True
            elif c5 == 1:
                # een vier en een vijf: geslaagd als gemiddeld een 6 of hoger is behaald
                if avgfinal_lt_6:
                    has_failed = True
                result_info += ''.join((', ', str(_('average final grade is ')), avgfinal_str))
            else: # 1 vier geen vijven
                # geslaagd als gemiddeld een 6 of hoger is behaald
                if avgfinal_lt_6:
                    has_failed = True
                result_info += ''.join((', ', str(_('average final grade is ')), avgfinal_str))

        else:
            # 'kandidaat heeft geen vieren, alleen vijven of hoger
            if c5 > 2:
                # '3 of meer vijven
                has_failed = True
                result_info = five_str
            elif c5 == 2: # 2 vijven, rest zessen of hoger
                # geslaagd als gemiddeld een 6 of hoger is behaald
                if avgfinal_lt_6:
                    has_failed = True
                result_info += ''.join((', ', str(_('average final grade is ')), avgfinal_str))

            elif c5 == 1:
                # 'kandidaat heeft 1 vijf, rest zessen of hoger
                # 'PR 17 jun 10 NB: gemiddeld een 6 of hoger is hier NIET van toepassing
                result_info = ' '.join((five_str, str(_('and for the other subjects a 6 or higher.'))))
            else:
                # kandidaat heeft geen vijf, rest zessen of hoger
                result_info = str(_('For all subjects a 6 or higher.'))

    # TODO add herexamen
    #result_dict['caption'] = str(c.RESULT_CAPTION[result_id])

# - if has_failed: create dict with key 'failed' if it does not exist
    if has_failed:
        student_ep_dict['result_index'] = c.RESULT_FAILED
        if 'failed' not in student_ep_dict:
            student_ep_dict['failed'] = {}
        failed_dict = student_ep_dict.get('failed')
        # - add key 'cnt3457' with value 'result_info'
        failed_dict['cnt3457'] = result_info
    else:
        # - if not has_failed: create dict with key 'passed' if it does not exist
        # note: student might have failed because of other rules
        if 'passed' not in student_ep_dict:
            student_ep_dict['passed'] = {}
        passed_dict = student_ep_dict.get('passed')
        # - add key 'cnt3457' with value 'failed_info'
        passed_dict['cnt3457'] = result_info

    if logging_on:
        logger.debug(' >>> has_failed: ' + str(has_failed))
        logger.debug(' >>> result_info: ' + str(result_info))
        logger.debug(' >>> student_ep_dict: ' + str(student_ep_dict))

    return has_failed
# end of calc_passfailed_count6_havovwo


def calc_passfailed_core_rule(student_ep_dict):  # PR2021-12-24  PR2022-05-28
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('-----  calc_passfailed_core_rule  -----')
# 'count': {'c3': 0, 'c4': 1, 'c5': 1, 'c6': 2, 'c7': 2, 'core4': 0, 'core5': 0}

    """
    in kernvak geen vieren en niet meer dan 1 vijf 'PR2015-10-31
    """
    count_dict = student_ep_dict['count']
    core4 = count_dict.get('core4', 0)
    core5 = count_dict.get('core5', 0)

    if logging_on:
        logger.debug( '     count_dict: ' + str(count_dict) + ' ' + str(type(count_dict)))
        logger.debug( '     core4: ' + str(core4) + ' ' + str(type(core4)))
        logger.debug( '     core5: ' + str(core5) + ' ' + str(type(core5)))

    has_failed = False
    result_info = ''
    if core4:
        result_info = ' '.join((str(core4), str(_('four') if core4 == 1 else _('fours'))))
    if core5:
        if result_info:
            result_info += str(_(' and '))
        result_info += ' '.join((str(core5), str(_('five') if core5 == 1 else _('fives'))))

    if core4 or core5 > 1:
        has_failed = True
        result_info += ''.join(( str(_(' in ')), str(_('core subjects')), '.'))

# - if has_failed: create dict with key 'failed' if it does not exist
    if has_failed:
        student_ep_dict['result_index'] = c.RESULT_FAILED
        if 'failed' not in student_ep_dict:
            student_ep_dict['failed'] = {}
        failed_dict = student_ep_dict.get('failed')

# - add key 'core45' with value 'result_info'
        failed_dict['core45'] = result_info

# - add info to passed_dict
    else:
        # - if not has_failed: create dict with key 'passed' if it does not exist
        # note: student might have failed because of other rules
        if 'passed' not in student_ep_dict:
            student_ep_dict['passed'] = {}
        passed_dict = student_ep_dict.get('passed')

        if core5:
            result_info = ''.join(('1 ', str(_('five'))))
        else:
            result_info = str(_('No fail marks'))
        result_info += ''.join((str(_(' in ')), str(_('core subjects')), '.'))
        passed_dict['core45'] = result_info

    if logging_on:
        logger.debug(' >>> result_info: ' + str(result_info))
        logger.debug(' >>> student_ep_dict: ' + str(student_ep_dict))
        logger.debug(' >>> has_failed: ' + str(has_failed))

    return has_failed
# end of calc_passfailed_core_rule


def calc_passfailed_pece_avg_rule(student_ep_dict):  # PR2021-12-24 PR2022-05-26
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('-----  calc_passfailed_pece_avg_rule  -----')
        logger.debug( '     student_ep_dict: ' + str(student_ep_dict))
    """
    student_ep_dict: {
        'ep': 1, 
        'final': {'sum': 48, 'cnt': 8, 
                    'info': ' wb:5 na:6 sk:6 bec:6 frtl:7 netl:4 entl:6 combi:8', 'avg': '6.0', 
                    'result': 'Gemiddeld eindcijfer: 6.0 (48/8) '}, 
        'combi': {'sum': 15, 'cnt': 2, 
                    'info': ' asw:7 pws:8', 'final': 8, 
                    'result': 'Combinatiecijfer: 8 (15/2) '}, 
        'pece': {'sumX10': 351, 'cnt': 7, 
                    'info': ' wb:4,1 na:6,0 sk:6,0 bec:7,0 frtl:6,5 netl:1,2 entl:4,3', 'avg': None, 
                    'result': 'Gemiddeld CE-cijfer: 5,0 (35,1/7) '}, 
        'count': {'c3': 0, 'c4': 1, 'c5': 1, 'c6': 4, 'c7': 2, 'core4': 1, 'core5': 1}, 
        'failed': {
            'insuff': ['Culturele en artistieke vorming is onvoldoende.', 'Lichamelijke opvoeding is onvoldoende.'], 
            'core45': '1 vier en 1 vijf in kernvakken.'}, 
            'passed': {'cnt3457': '1 vier en 1 vijf, gemiddeld eindcijfer is 6,0'}, 
            'result_index': 2}
    """
    has_failed = False

    pece_dict = student_ep_dict['pece']
    if logging_on:
        logger.debug('     pece_dict' + str(pece_dict))

    avg = pece_dict.get('avg')
    if avg:
        avg_str = str(avg)
        avg_display = avg_str.replace('.', ',')
        result_info = ''.join((str(_('Average CE grade')), str(_(' is ')), avg_display))
        if logging_on:
            logger.debug( 'avg_str' + str(avg_str))

        avg_decimal_A = Decimal(avg_str)
        if logging_on:
            logger.debug( 'avg_decimal_A' + str(avg_decimal_A))
        avg_55_B = Decimal('5.5')
        # a.compare(b) == -1 means a < b
        if avg_decimal_A.compare(avg_55_B) == -1:  # a.compare(b) == -1 means a < b
            has_failed = True
            result_info += str(_(', must be unrounded 5,5 or higher.'))
        else:
            result_info += '.'

# - if has_failed: create dict with key 'failed' if it does not exist
        if has_failed:
            student_ep_dict['result_index'] = c.RESULT_FAILED
            if 'failed' not in student_ep_dict:
                student_ep_dict['failed'] = {}
            failed_dict = student_ep_dict.get('failed')
# - add key 'avgce55' with value 'result_info'
            failed_dict['avgce55'] = result_info
            if logging_on:
                logger.debug('     result_info: ' + str(result_info))
                logger.debug('     failed_dict: ' + str(failed_dict))
        else:

# - also add info to passed_dict
            # - if not has_failed: create dict with key 'passed' if it does not exist
            # note: student might have failed beacsuse of other rules
            if 'passed' not in student_ep_dict:
                student_ep_dict['passed'] = {}
            passed_dict = student_ep_dict.get('passed')
            # - add key 'avgce55' with value 'result_info'
            passed_dict['avgce55'] = result_info
            if logging_on:
                logger.debug('     result_info: ' + str(result_info))
                logger.debug('     passed_dict: ' + str(passed_dict))

    if logging_on:
        logger.debug(' >>> has_failed: ' + str(has_failed))
        logger.debug(' >>> student_ep_dict: ' + str(student_ep_dict))

    return has_failed
# end of calc_passfailed_pece_avg_rule


def calc_add_result_to_log(examperiod, last_student_ep_dict, rule_avg_pece_sufficient, rule_core_sufficient):
    # PR2021-11-29 PR2022-06-05
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  calc_add_result_to_log  -----')
        logger.debug('last_student_ep_dict: ' + str(last_student_ep_dict))
    """
    last_student_ep_dict: {
        'ep': 2, 
        'final': {'sum': -962, 'cnt': 7, 'info': ' ec:-(h) en:6 fr:5 ne:7 sp:6 wk:6 combi:7', 'avg': None, 
                    'result': 'Gemiddeld eindcijfer: - (-/7) '}, 
        'combi': {'sum': 21, 'cnt': 3, 'info': ' cav:7 lo:8 mm1:6', 'final': 7, 
                    'result': 'Combinatiecijfer: 7 (21/3) '}, 
        'pece': {'sumX10': -9712, 'cnt': 6, 'info': ' ec:-(h) en:6,4 fr:3,5 ne:7,5 sp:5,4 wk:5,9', 'avg': None, 
                    'result': 'Gemiddeld CE-cijfer: - (-/6) '}, 
        'count': {'c3': 0, 'c4': 0, 'c5': 1, 'c6': 3, 'c7': 2, 'core4': 0, 'core5': 0}, 
        'noin': {'h2': ['ec']}, 
        'noin_info': ['Herexamen: ec niet ingevuld'],
        'result_index': 0}
    """
    #last_student_ep_dict = student_dict[last_ep_str]

    # add result to combi_dict result: PR2021-11-29
    result_info_list = []
    result_info_log_list = []

    if examperiod == 3:
        result_str = ''.join((str(_('Result')), ' ', str(_('after')), ' ', str(_('Re-examination 3rd period')).lower(), ': '))
    elif examperiod == 2:
        result_str = ''.join((str(_('Result')), ' ', str(_('after')), ' ', str(_('Re-examination')).lower(), ': '))
    else:
        result_str = ''.join((str(_('Result')), ': '))

    show_details = False
    result_info_log_list.append(' ')
    result_index = last_student_ep_dict.get('result_index')
    if result_index == c.RESULT_WITHDRAWN:
        result_str += str(_('Withdrawn')).upper()
        result_info_list.append(result_str)
        result_info_log_list.append(result_str)
    elif result_index == c.RESULT_NORESULT:
        result_str += str(_('No result')).upper()
        result_info_list.append(result_str)
        result_info_log_list.append(result_str)
        noin_info_list = last_student_ep_dict.get('noin_info')
        if noin_info_list:
            for noin_info in noin_info_list:
                result_info_list.append(noin_info)
                result_info_log_list.append(''.join((c.STRING_SPACE_05, noin_info)))
    elif result_index == c.RESULT_FAILED:
        show_details = True
        result_str += str(_('Failed')).upper()
        result_info_list.append(result_str)
        result_info_log_list.append(result_str)

        fail_dict = last_student_ep_dict.get('failed')
        if fail_dict:
            cnt3457_dict = fail_dict.get('cnt3457')
            if cnt3457_dict:
                result_info_list.append(str(cnt3457_dict))
                result_info_log_list.append(''.join((c.STRING_SPACE_05, str(cnt3457_dict))))

            if rule_core_sufficient:
                core45_dict = fail_dict.get('core45')
                if core45_dict:
                    result_info_list.append(str(core45_dict))
                    result_info_log_list.append(''.join((c.STRING_SPACE_05, str(core45_dict))))

            if rule_avg_pece_sufficient:
                avgce55_dict = fail_dict.get('avgce55')
                if avgce55_dict:
                    result_info_list.append(str(avgce55_dict))
                    result_info_log_list.append(''.join((c.STRING_SPACE_05, str(avgce55_dict))))

            insuff_list = fail_dict.get('insuff')
            if insuff_list:
                # 'insuff': ['Lichamelijke Opvoeding is onvoldoende.', 'Sectorwerkstuk is onvoldoende.']}
                for info in insuff_list:
                    result_info_list.append(str(info))
                    result_info_log_list.append(''.join((c.STRING_SPACE_05, info)))

    elif result_index == c.RESULT_PASSED:
        show_details = True
        result_str += str(_('Passed')).upper()
        result_info_list.append(result_str)
        result_info_log_list.append(result_str)

        passed_dict = last_student_ep_dict.get('passed')
        if passed_dict:
            cnt3457_dict = passed_dict.get('cnt3457')
            if cnt3457_dict:
                result_info_log_list.append(''.join((c.STRING_SPACE_05, str(cnt3457_dict))))
            core45_dict = passed_dict.get('core45')
            if core45_dict:
                result_info_log_list.append(''.join((c.STRING_SPACE_05, str(core45_dict))))
            avgce55_dict = passed_dict.get('avgce55')
            if avgce55_dict:
                result_info_log_list.append(''.join((c.STRING_SPACE_05, str(avgce55_dict))))
            insuff_list = passed_dict.get('insuff')
            if insuff_list:
                # 'insuff': ['Lichamelijke Opvoeding is onvoldoende.', 'Sectorwerkstuk is onvoldoende.']}
                for info in insuff_list:
                    result_info_log_list.append(''.join((c.STRING_SPACE_05, info)))

    if show_details:
# - add line with combi grade
        combi_dict = last_student_ep_dict['combi']
        if 'result' in combi_dict:
            result_info_log_list.append(('').join((c.STRING_SPACE_05, combi_dict['result'], '{' + combi_dict['info'][1:] + '}')))

# - add line with final grade
        # final_sum_int is negative when grades have no input, therefore use: if final_sum_int > 0
        final_dict = last_student_ep_dict.get('final')
        final_sum_int = final_dict.get('sum', 0)
        final_cnt_int = final_dict.get('cnt', 0)

        final_count_str = str(final_cnt_int) if final_cnt_int else '-'
        final_sum_str = str(final_sum_int) if final_sum_int > 0 else '-'
        final_rounded_str = '-'
        if final_cnt_int and final_sum_int > 0:
            final_avg = Decimal(final_sum_str) / Decimal(final_count_str)
            final_rounded_str = str(grade_calc.round_decimal_from_str(final_avg, digits=1))

        final_info = final_dict.get('info', '-')
        final_info_str = final_info[1:] if final_info else '-'
        log_txt = ''.join((str(_('Average final grade')), ': ',
            final_rounded_str, ' (', final_sum_str, '/', final_count_str, ') ', '{' + final_info_str + '}'
        ))
        result_info_log_list.append(('').join((c.STRING_SPACE_05, str(log_txt))))

# - add line with average pece grade
        pece_dict = last_student_ep_dict.get('pece')
        if pece_dict:
            result_str = pece_dict['result'] if 'result' in pece_dict else ''
            info_str = pece_dict['info'][1:] if 'info' in pece_dict else ''
            result_info_log_list.append(''.join((c.STRING_SPACE_05, result_str, '{' + info_str + '}')))

        if logging_on:
            logger.debug( 'log_txt: ' + str(log_txt))
    return result_info_list, result_info_log_list
# - end of calc_add_result_to_log


def save_studsubj_batch(sql_studsubj_list):  # PR2022-01-03
    # this function saves calculated fields in studentsubject
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- save_studsubj_batch  --------------------')
        logger.debug('sql_studsubj_list: ' + str(sql_studsubj_list))

    if sql_studsubj_list:
       # sql_keys = {'ey_id': school.examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk}

        """
        # you can define the types by casting the values of the first row:
        CREATE TEMP TABLE lookup (key, val) AS
        VALUES 
            (0::bigint, -99999::int), 
            (1, 100) ;
        """
        # fields are: [grade_id, value, modifiedby_id, modifiedat]
        sql_list = ["DROP TABLE IF EXISTS tmp; CREATE TEMP TABLE tmp (ss_id, sesr, pece, final, use_exem, nise, nisr, nipe, nice, ep) AS",
            "VALUES (0::INT, '-'::TEXT, '-'::TEXT, '-'::TEXT, FALSE::BOOLEAN, FALSE::BOOLEAN, FALSE::BOOLEAN, FALSE::BOOLEAN, FALSE::BOOLEAN, 0::INT)"]

        for row in sql_studsubj_list:
            sql_item = ', '.join((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]))
            sql_list.append(''.join((", (", sql_item, ")")))
        sql_list.extend((
            "; UPDATE students_studentsubject AS ss",
            "SET gradelist_sesrgrade = tmp.sesr, gradelist_pecegrade = tmp.pece, gradelist_finalgrade = tmp.final, gradelist_use_exem = tmp.use_exem,",
            "gl_ni_se = tmp.nise, gl_ni_sr = tmp.nisr, gl_ni_pe = tmp.nipe, gl_ni_ce = tmp.nice, gl_examperiod = tmp.ep",
            "FROM tmp",
            "WHERE ss.id = tmp.ss_id",
            "RETURNING ss.id, ss.gradelist_pecegrade;"
            ))

        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

        if logging_on:
            if rows:
                logger.debug('............................................')
                for row in rows:
                    logger.debug('row: ' + str(row))
# - end of save_studsubj_batch


def save_student_batch(sql_student_list):  # PR2022-01-03 PR2022-06-03
    # this function saves calculated fields in student
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- save_student_batch  --------------------')
        logger.debug('sql_student_list: ' + str(sql_student_list))

    if sql_student_list:
       # sql_keys = {'ey_id': school.examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk}

        """
        sql_student_values = [ str(student_id),
            gl_ce_avg_str, gl_combi_avg_str, gl_final_avg_str, result_index_str, 
                result_status_str,  result_info_str,
            e1_ce_avg_str, e1_combi_avg_str, e1_final_avg_str, e1_result_index_str,
            e2_ce_avg_str, e2_combi_avg_str, e2_final_avg_str, e2_result_index_str
        ]
        """
        # fields are: [grade_id, value, modifiedby_id, modifiedat]
        sql_list = ["DROP TABLE IF EXISTS tmp;",
                    "CREATE TEMP TABLE tmp (st_id,",
                        "avg_ce, avg_combi, avg_final, index, status, info,",
                        "e1_ce_avg, e1_combi_avg, e1_final_avg, e1_result,",
                        "e2_ce_avg, e2_combi_avg, e2_final_avg, e2_result,",
                        "exemption_count, sr_count,",
                        "reex_count, reex03_count,thumbrule_count",

                    ") AS VALUES (0::INT,",
                        "'-'::TEXT, '-'::TEXT, '-'::TEXT,",
                        "0::INT, '-'::TEXT, '-'::TEXT,",
                        "'-'::TEXT, '-'::TEXT, '-'::TEXT, 0::INT,",
                        "'-'::TEXT, '-'::TEXT, '-'::TEXT, 0::INT,",
                        "0::INT, 0::INT,"
                        "0::INT, 0::INT, 0::INT"
                    ")"]

        for row in sql_student_list:

            if logging_on:
                logger.debug(' >>>>>>>>>>>>> row: ' + str(row))
            """
            row: ['3957', 
                'NULL', "'7'", 'NULL', '0', "'Geen uitslag'", "'Uitslag na herexamen: GEEN UITSLAG|Herexamen: en,ne,pa,wk niet ingevuld'", 
                'NULL', "'7'", 'NULL', '0', 
                'NULL', "'7'", 'NULL', '0']

            row: ['4377', 
                "'5.8'", "'7'", "'6.1'", '1', "'Geslaagd'", "'Uitslag na herexamen: GESLAAGD'", 
                "'5.8'", "'7'", "'6.1'", '1', "'5.8'", "'7'", "'6.1'", '1']

            

            """
            sql_item = ', '.join((row[0],
                row[1], row[2], row[3], row[4], row[5], row[6],
                row[7], row[8], row[9], row[10],
                row[11], row[12], row[13], row[14],
                row[15], row[16], row[17], row[18], row[19]
            ))
            sql_list.append(''.join((", (", sql_item, ")")))

        if logging_on:
            logger.debug(' >>>>>>>>>>>>> sql_list: ' + str(sql_list))


        sql_list.extend((
            "; UPDATE students_student AS st",
            "SET gl_ce_avg = tmp.avg_ce, gl_combi_avg = tmp.avg_combi, gl_final_avg = tmp.avg_final,",
            "result = tmp.index, result_status = tmp.status, result_info = tmp.info,",
            "ep01_ce_avg=tmp.e1_ce_avg, ep01_combi_avg=tmp.e1_combi_avg, ep01_final_avg=tmp.e1_final_avg, ep01_result=tmp.e1_result,",
            "ep02_ce_avg=tmp.e2_ce_avg, ep02_combi_avg=tmp.e2_combi_avg, ep02_final_avg=tmp.e2_final_avg, ep02_result=tmp.e2_result,",
            "exemption_count=tmp.exemption_count, sr_count=tmp.sr_count,",
            "reex_count=tmp.reex_count, reex03_count=tmp.reex03_count, thumbrule_count=tmp.thumbrule_count",

            "FROM tmp",
            "WHERE st.id = tmp.st_id",
            "RETURNING st.id, st.result_info;"
            ))

        sql = ' '.join(sql_list)

        if logging_on:
            logger.debug(',,,,,,,,,,,,,,,,,: ' + str(sql))
            """
            CREATE TEMP TABLE tmp (
            st_id, avg_ce, avg_combi, avg_final, index, status, info, c_exem, c_sr, c_reex, c_reex03, c_thrule, e1_ce_avg, e1_combi_avg, e1_final_avg, e1_result, e2_ce_avg, e2_combi_avg, e2_final_avg, e2_result ) AS VALUES (0::INT, '-'::TEXT, '-'::TEXT, '-'::TEXT, 0::INT, '-'::TEXT, '-'::TEXT, '-'::TEXT, '-'::TEXT, '-'::TEXT, 0::INT, '-'::TEXT, '-'::TEXT, '-'::TEXT, 0::INT ) , (3957, NULL, '7', NULL, 0, 'Geen uitslag', 'Uitslag na herexamen: GEEN UITSLAG|Herexamen: en,pa,wk niet ingevuld', NULL, '7', NULL, 0, NULL, '7', NULL, 0) ; UPDATE students_student AS st SET gl_ce_avg = tmp.avg_ce, gl_combi_avg = tmp.avg_combi, gl_final_avg = tmp.avg_final, result = tmp.index, result_status = tmp.status, result_info = tmp.info, exemption_count=tmp.c_exem, sr_count=tmp.c_sr, reex_count=tmp.c_reex, reex03_count=tmp.c_reex03, thumbrule_count=tmp.c_thrule, ep01_ce_avg=tmp.e1_ce_avg, ep01_combi_avg=tmp.e1_combi_avg, ep01_final_avg=tmp.e1_final_avg, ep01_result=tmp.e1_result,  ep02_ce_avg=tmp.e2_ce_avg, ep02_combi_avg=tmp.e2_combi_avg, ep02_final_avg=tmp.e2_final_avg, ep02_result=tmp.e2_result FROM tmp WHERE st.id = tmp.st_id RETURNING st.id, st.result_info;
            
            """

        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

        if logging_on and rows:
            logger.debug('............................................')
            for row in rows:
                logger.debug('row: ' + str(row))
        """
         {'fullname': 'Ahoua, Ahoua Bryan Blanchard', 'stud_id': 3747, 'country': 'Curaçao', 'examyear_txt': '2022', 
         'school_name': 'Juan Pablo Duarte Vsbo', 'school_code': 'CUR03', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 
         'depbase_code': 'Vsbo', 'dep_abbrev': 'V.S.B.O.', 'lvl_name': 'Praktisch Basisgerichte Leerweg', 
         'lvlbase_code': 'PBL', 'level_req': True, 'sct_name': 'Economie', 'dep_id': 4, 'lvl_id': 6, 'sct_id': 13, 
         'scheme_id': 76, 'examnumber': '2101', 'bis_exam': True, 
         'exemption_count': 3, 
         21179: {'si_id': 1782, 'subj': 'ne', 'has_exemption': True, 'exemption_year':  2021, 
                    4: {'subj': 'ne', 'se': '7.7', 'sesr': '7.7', 'final': '8'}, 
                    1: {'subj': 'ne', 'se': '5.9', 'sesr': '5.9'}}, 
         21184: {'si_id': 1787, 'subj': 'pa', 
                    1: {'subj': 'pa', 'se': '7.6', 'sesr': '7.6'}}, 
         21180: {'si_id': 1783, 'subj': 'en', 1: {'subj': 'en', 'se': '8.0', 'sesr': '8.0'}}, 21509: {'si_id': 1788, 'subj': 'sp', 1: {'subj': 'sp', 'se': '8.0', 'sesr': '8.0'}}, 21188: {'si_id': 1793, 'subj': 'ec', 1: {'subj': 'ec', 'se': '6.1', 'sesr': '6.1'}}, 21181: {'si_id': 1784, 'subj': 'mm1', 1: {'subj': 'mm1', 'se': '5.4', 'sesr': '5.4', 'final': '5'}}, 23033: {'si_id': 1786, 'subj': 'cav', 'has_exemption': True, 'exemption_year': 2021, 4: {'subj': 'cav', 'se': '7.6', 'sesr': '7.6', 'final': '8'}, 1: {'subj': 'cav', 'se': '6.1', 'sesr': '6.1', 'final': '6'}}, 21182: {'si_id': 1785, 'subj': 'lo', 1: {'subj': 'lo', 'se': '7.0', 'sesr': '7.0', 'final': '7'}}, 21186: {'si_id': 1791, 'subj': 'ac', 'has_exemption': True, 'exemption_year': 2021, 1: {'subj': 'ac', 'se': '6.4', 'sesr': '6.4'}, 4: {'subj': 'ac', 'se': '6.0', 'sesr': '6.0', 'final': '6'}}, 21187: {'si_id': 1792, 'subj': 'stg', 1: {'subj': 'stg', 'se': 'g', 'sesr': 'g', 'final': 'g'}}}

        """


# - end of save_student_batch


def get_students_with_grades_dictlist(examyear, school, department, student_pk_list, lvlbase_pk=None):
    # PR2021-11-19 PR2022-05-26

    # NOTE: don't forget to filter studsubj.deleted = False and grade.deleted = False!! PR2021-03-15
    # TODO grades that are not published are only visible when 'same_school' (or not??)
    # also add grades of each period

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ----- get_students_with_grades_dictlist -----')
        logger.debug('student_pk_list: ' + str(student_pk_list))

    # values of sel_layout are:"none", "level", "class", "cluster"
    # "none" or None: all students of subject on one form
    # "level:" seperate form for each leeerweg
    #  Note: when lvlbase_pk_list has values: filter on lvlbase_pk_list in all lay-outs
    #  filter on lvlbase_pk, not level_pk, to make filter also work in other examyears

    student_field_list = ('stud_id', 'country', 'examyear_txt', 'school_name', 'school_code', 'islexschool',
                          'dep_name', 'depbase_code', 'dep_abbrev', 'lvl_name', 'lvlbase_code',  'level_req', 'sct_name',
                          'dep_id', 'lvl_id', 'sct_id', 'scheme_id', 'classname',
                          'has_profiel', 'examnumber', 'iseveningstudent', 'islexstudent', 'bis_exam', 'partial_exam',
                          'exemption_count', 'sr_count', 'reex_count', 'reex03_count', 'thumbrule_count', 'withdrawn',
                          )  # 'fullname is also added to dict

    studsubj_field_list = ('si_id', 'subj', 'is_extra_nocount', 'is_extra_counts', 'is_thumbrule',
                           'has_exemption', 'has_sr', 'has_reex', 'has_reex03', 'exemption_year')

    grade_field_list = ('subj', 'se', 'sr', 'sesr', 'pe', 'ce', 'pece', 'final')

    sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk,
                'student_pk_list': student_pk_list}
    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))

    cascade_dict = {}

    sub_list = ["SELECT studsubj.id,studsubj.student_id, si.id as si_id,",
                "subj.id AS subj_id, subj.name AS subj_name, subjbase.code AS subj, cl.name AS cluster_name,",
                "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.is_thumbrule,",
                "studsubj.has_exemption, studsubj.has_sr, studsubj.has_reex, studsubj.has_reex03, studsubj.exemption_year,",

                # "studsubj.gradelist_use_exem,",
                # "studsubj.gradelist_sesrgrade, studsubj.gradelist_pecegrade, studsubj.gradelist_finalgrade,",
                # "studsubj.pws_title, studsubj.pws_subjects,",

                "grade.examperiod, grade.segrade AS se, grade.srgrade AS sr, grade.sesrgrade AS sesr,",
                "grade.pegrade AS pe, grade.cegrade AS ce, grade.pecegrade AS pece, grade.finalgrade AS final",

                "FROM students_studentsubject AS studsubj",
                "INNER JOIN students_grade AS grade ON (grade.studentsubject_id = studsubj.id)",

                "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                "LEFT JOIN subjects_cluster AS cl ON (cl.id = studsubj.cluster_id)",

                "WHERE NOT studsubj.tobedeleted AND NOT grade.tobedeleted",
                "ORDER BY subjbase.code"
                ]

    sql_studsubjects = ' '.join(sub_list)

    sql_list = ["WITH studsubj AS (" + sql_studsubjects + ")",

                "SELECT stud.id AS stud_id, studsubj.id AS studsubj_id, studsubj.si_id,",
                "stud.lastname, stud.firstname, stud.prefix, stud.examnumber, stud.classname,",
                "stud.iseveningstudent, stud.islexstudent, stud.bis_exam, stud.partial_exam, stud.withdrawn,",
                "stud.exemption_count, stud.sr_count, stud.reex_count, stud.reex03_count, stud.thumbrule_count,",

                "school.name AS school_name, school.islexschool,",
                "sb.code AS school_code, depbase.code AS depbase_code, lvlbase.code AS lvlbase_code,"
                "ey.code::TEXT AS examyear_txt, c.name AS country,"

                "dep.id AS dep_id, lvl.id AS lvl_id, sct.id AS sct_id, stud.scheme_id AS scheme_id,",
                "dep.name AS dep_name, dep.abbrev AS dep_abbrev, dep.level_req, dep.has_profiel,"
                "lvl.name AS lvl_name, sct.name AS sct_name,"
                
                "studsubj.subj_id, studsubj.subj_name, studsubj.subj, studsubj.cluster_name,",
                "studsubj.is_extra_nocount, studsubj.is_extra_counts, studsubj.is_thumbrule,",
                "studsubj.has_exemption, studsubj.has_sr, studsubj.has_reex, studsubj.has_reex03, studsubj.exemption_year,",

                #"studsubj.gradelist_use_exem,",
                #"studsubj.gradelist_sesrgrade, studsubj.gradelist_pecegrade, studsubj.gradelist_finalgrade,",
                #"studsubj.pws_title, studsubj.pws_subjects,",

                "studsubj.examperiod,",
                "studsubj.se, studsubj.sr, studsubj.sesr AS sesr,",
                "studsubj.pe, studsubj.ce, studsubj.pece AS pece, studsubj.final",

                "FROM students_student AS stud",

                "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                "INNER JOIN schools_schoolbase AS sb ON (sb.id = school.base_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                "INNER JOIN schools_country AS c ON (c.id = ey.country_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
                "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
                "LEFT JOIN subjects_levelbase AS lvlbase ON (lvlbase.id = lvl.base_id)",
                "LEFT JOIN subjects_sector AS sct ON (sct.id = stud.sector_id)",
                "LEFT JOIN subjects_sectorbase AS sctbase ON (sctbase.id = sct.base_id)",

                "LEFT JOIN studsubj ON (studsubj.student_id = stud.id)",

                "WHERE ey.id = %(ey_id)s::INT AND school.id = %(sch_id)s::INT AND dep.id = %(dep_id)s::INT",
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

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)
        if logging_on:
            for cq in connection.queries:
                if "SELECT stud.id" in cq:
                    logger.debug('############# query: ' + cq)
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

# count exemption(c_ep4), reex(c_ep2), reex03(c_ep3)
                examperiod = row.get('examperiod')

                for ep_int in range(2, 5):
                    if examperiod == ep_int:
                        key_str = 'c_ep' + str(ep_int)
                        stud_dict[key_str] = 1 + (stud_dict.get(key_str) or 0)

                cascade_dict[stud_id] = stud_dict

    # - add studsubj_dict dict
                student_dict = cascade_dict.get(stud_id)
                if student_dict:
                    # put studsubjects in dict with key: 'studsubj_id'
                    studsubj_pk = row.get('studsubj_id')

                    if studsubj_pk not in student_dict:
    # add 1 to count subjects
                        stud_dict['c_subj'] = 1 + (stud_dict.get('c_subj') or 0)

    # count put value of studsubj_field_list fields in ss_dict
                        ss_dict = {}
                        for field in studsubj_field_list:
                            value = row.get(field)
                            if value:
                                ss_dict[field] = value

    # count is_extra_nocount, is_extra_counts, is_thumbrule
                                if field == 'has_sr':
                                    stud_dict['c_sr'] = 1 + (stud_dict.get('c_sr') or 0)
                                if field == 'is_thumbrule':
                                    stud_dict['c_thumbrule'] = 1 + (stud_dict.get('c_thumbrule') or 0)
                                elif field == 'is_extra_nocount':
                                    stud_dict['c_extra_nocount'] = 1 + (stud_dict.get('c_extra_nocount') or 0)
                                elif field == 'is_extra_counts':
                                    stud_dict['c_extra_counts'] = 1 + (stud_dict.get('c_extra_counts') or 0)

                        student_dict[studsubj_pk] = ss_dict

                    studsubj_dict = student_dict.get(studsubj_pk)
                    examperiod = row.get('examperiod')
                    if examperiod is None:
                        # this should not be possible - every studsubj must have at least 1 grade
                        pass
                    else:
                        if examperiod not in studsubj_dict:
                            grade_dict = {}
                            for field in grade_field_list:
                                value = row.get(field)
                                if value or True:
                                    grade_dict[field] = value
                            studsubj_dict[examperiod] = grade_dict

# convert dict to sorted dictlist
        grade_list = list(cascade_dict.values())

# sort list to sorted dictlist
        # PR2021-11-15 from https://stackoverflow.com/questions/72899/how-do-i-sort-a-list-of-dictionaries-by-a-value-of-the-dictionary
        grade_dictlist_sorted = sorted(grade_list, key=lambda d: d['fullname'])

    if logging_on and grade_dictlist_sorted:
        for row in grade_dictlist_sorted:
            logger.debug('XXXXXXXXXXXXXXXXXXXX row: ' + str(row))
            """
            {'fullname': 'Acosta Hurtado, Nathasha', 'stud_id': 4053, 'country': 'Curaçao', 'examyear_txt': '2022', 
            'school_name': 'Ancilla Domini Vsbo', 'school_code': 'CUR01', 'islexschool': False, 
            'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'depbase_code': 'Vsbo', 'dep_abbrev': 'V.S.B.O.', 
            'lvl_name': 'Praktisch Kadergerichte Leerweg', 'lvlbase_code': 'PKL', 'level_req': True, 
            'sct_name': 'Zorg & Welzijn', 'dep_id': 4, 'lvl_id': 5, 'sct_id': 14, 'scheme_id': 74, 'has_profiel': False, 
            'examnumber': 'V019', 'iseveningstudent': False, 'islexstudent': False, 'bis_exam': False, 'partial_exam': False, 
            'exemption_count': 0, 'sr_count': 0, 'reex_count': 0, 'reex03_count': 0, 'thumbrule_count': 0, 'withdrawn': False, 
             
            67812: {'si_id': 9738, 'subj_code': 'ne', 'has_reex': True, 1: {'sesr': '7,8'}, 2: {}}, 
            67815: {'si_id': 9743, 'subj_code': 'pa', 1: {'sesr': '6,3', 'final': '6'}}, 
            67813: {'si_id': 9739, 'subj_code': 'en', 1: {'sesr': '7,3'}}, 
            69176: {'si_id': 9746, 'subj_code': 'nask1', 1: {}}, 
            69177: {'si_id': 9753, 'subj_code': 'ec', 1: {}}, 
            67814: {'si_id': 9740, 'subj_code': 'mm1', 1: {}},  
            67818: {'si_id': 9748, 'subj_code': 'mm12', 'has_exemption': True, 'has_sr': True, 'has_reex': True, 
                4: {'sesr': '7.5', 'final': '8'}, 
                2: {}, 
                1: {'sesr': '6,9', 'final': '7'}},
            69179: {'si_id': 9742, 'subj_code': 'cav', 1: {}}, 69178: {'si_id': 9741, 'subj_code': 'lo', 1: {}}, 
            67819: {'si_id': 9750, 'subj_code': 'zwi', 'has_exemption': True, 'has_reex': True, 4: {'sesr': '4.5', 'final': '5'}, 2: {}, 1: {'sesr': '7.1'}}, 
            67820: {'si_id': 9752, 'subj_code': 'sws', 'has_exemption': True, 4: {'final': 'g'}, 2: {}, 1: {'sesr': 'v', 'final': 'v'}}}
 
 

 44768: {'si_id': 1861, 'subj': 'asw', 'is_thumbrule': True, 

            """
    return grade_dictlist_sorted
# - end of get_students_with_grades_dictlist


def get_scheme_dict(examyear, department):  # PR2021-11-28
    # function collect all variables from schemes and depending tables
    # stores in dict per schemitem

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_schemeitems_dict -----')

    # upload_dict: {'subject_list': [2206, 2165, 2166], 'sel_layout': 'level', 'level_list': [86, 85]}

    # values of sel_layout are:"none", "level", "class", "cluster"
    # "none" or None: all students of subject on one form
    # "level:" seperate form for each leeerweg
    #  Note: when lvlbase_pk_list has values: filter on lvlbase_pk_list in all lay-outs
    #  filter on lvlbase_pk, not level_pk, to make filter also work in other examyears

    #PR2022-05-27 debug: must use examyear.code instead of examyear.pk, because it must include SXM schemeitems
    # also use department.base_id instead of department.id
    sql_keys = {'ey_code': examyear.code, 'db_id': department.base_id}
    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))

    scheme_dict = {}
    sql_list = [
        "SELECT scheme.id,",

        "scheme.department_id, scheme.level_id, scheme.sector_id,",
        "scheme.rule_avg_pece_sufficient, scheme.rule_avg_pece_notatevlex,",
        "scheme.rule_core_sufficient, scheme.rule_core_notatevlex",

        "FROM subjects_scheme AS scheme",
        "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",

        "WHERE ey.code = %(ey_code)s::INT",
        "AND dep.base_id = %(db_id)s::INT"
        ]

    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

    if rows:
        for row in rows:
            scheme_id = row.get('id')

            if scheme_id not in scheme_dict:
                scheme_dict[scheme_id] = row

    if logging_on:
        logger.debug('scheme_dict: ' + str(scheme_dict))

    return scheme_dict
# - end of get_schemes_dict


def get_schemeitems_dict(examyear, department):  # PR2021-11-19
    # function collects all variables from schemeitem and depending tables
    # stores in dict per schemitem
    #++++++++ this is the one that works +++++++++++++++++++++ PR2022-05-29

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_schemeitems_dict -----')

    # upload_dict: {'subject_list': [2206, 2165, 2166], 'sel_layout': 'level', 'level_list': [86, 85]}

    # values of sel_layout are:"none", "level", "class", "cluster"
    # "none" or None: all students of subject on one form
    # "level:" seperate form for each leeerweg
    #  Note: when lvlbase_pk_list has values: filter on lvlbase_pk_list in all lay-outs
    #  filter on lvlbase_pk, not level_pk, to make filter also work in other examyears

    #PR2022-05-27 debug: must use examyear.code instead of examyear.pk, because it must include SXM schemeitems
    # also use department.base_id instead of department.id
    sql_keys = {'ey_code': examyear.code, 'db_id': department.base_id}
    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))

    si_dict = {}
    sql_list = [
        "SELECT si.id AS si_id,",
        "si.ete_exam, si.gradetype, si.weight_se, si.weight_ce, si.multiplier, si.is_mandatory, si.is_combi,",
        "si.extra_count_allowed, si.extra_nocount_allowed, si.has_practexam,",
        "si.is_core_subject, si.is_mvt, si.is_wisk,",
        "si.sr_allowed, si.no_ce_years, si,thumb_rule,",

        "si.rule_grade_sufficient, si.rule_gradesuff_notatevlex,",

        "subj.name AS subj_name, subjbase.code AS subj_code,",
        "sjtp.name AS sjtp_name, sjtpbase.code AS sjtp_code, sjtp.has_pws AS sjtp_has_pws",

        "FROM subjects_schemeitem AS si",
        "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id)",
        "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",
        "LEFT JOIN subjects_sector AS sct ON (lvl.id = scheme.sector_id)",

        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
        "INNER JOIN subjects_subjecttype AS sjtp ON (sjtp.id = si.subjecttype_id)",
        "INNER JOIN subjects_subjecttypebase AS sjtpbase ON (sjtpbase.id = sjtp.base_id)",

        "WHERE ey.code = %(ey_code)s::INT",
        "AND dep.base_id = %(db_id)s::INT"
        ]

    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

    if rows:
        for row in rows:
            si_id = row.get('si_id')

            if si_id not in si_dict:
                si_dict[si_id] = row

    if logging_on:
        logger.debug('si_dict: ' + str(si_dict))

    return si_dict
# - end of get_schemeitems_dict


def get_isevlex_isreex_fullname(student_dict):  # PR2021-12-19  PR2021-12-29 PR2022-06-05
    # - get from student_dict: isevlexstudent, reex_count, reex03_count and full name with (evening / lex student)

    full_name = student_dict.get('fullname', '---')
    iseveningstudent = student_dict.get('iseveningstudent') or False
    islexstudent = student_dict.get('islexstudent') or False
    partial_exam = student_dict.get('partial_exam') or False

    isevlexstudent = False
    ev_lex_part_list = []
    if iseveningstudent:
        isevlexstudent = True
        ev_lex_part_list.append(str(_('evening school candidate')))
    if islexstudent:
        isevlexstudent = True
        ev_lex_part_list.append(str(_('landsexamen candidate')))
    if partial_exam:
        ev_lex_part_list.append(str(_('partial exam')))
    if ev_lex_part_list:
        ev_lex_part_str = ', '.join(ev_lex_part_list)
        full_name += ''.join((' (', ev_lex_part_str, ')'))

    withdrawn = student_dict.get('withdrawn', False)

    return isevlexstudent, partial_exam, withdrawn, full_name
# - end of get_isevlex_isreex_fullname


def get_rules_from_schemeitem(student_dict, isevlexstudent, scheme_dict):
    # PR2021-12-19 PR2022-06-04
    # - get result rules from scheme and schemeitem
    scheme_error = True
    rule_avg_pece_sufficient, rule_avg_pece_notatevlex, rule_core_sufficient, rule_core_notatevlex = False, False, False, False

    stud_scheme_id = student_dict.get('scheme_id')
    if stud_scheme_id:
        stud_scheme = scheme_dict.get(stud_scheme_id)
        if stud_scheme:

    # - check if scheme of student is correct( dep, lvl and sct are the same)
            if student_dict.get('dep_id') == stud_scheme.get('department_id') and \
                student_dict.get('lvl_id') == stud_scheme.get('level_id') and \
                student_dict.get('sct_id') == stud_scheme.get('sector_id'):
                scheme_error = False
    # - get scheme rules
                rule_avg_pece_sufficient = stud_scheme.get('rule_avg_pece_sufficient')
                rule_avg_pece_notatevlex = stud_scheme.get('rule_avg_pece_notatevlex')
                rule_core_sufficient = stud_scheme.get('rule_core_sufficient')
                rule_core_notatevlex = stud_scheme.get('rule_core_notatevlex')
    if rule_avg_pece_sufficient:
        if rule_avg_pece_notatevlex and isevlexstudent:
            rule_avg_pece_sufficient = False

    if rule_core_sufficient:
        if rule_core_notatevlex and isevlexstudent:
            rule_core_sufficient = False
    return rule_avg_pece_sufficient, rule_core_sufficient, scheme_error
# - end of get_rules_from_schemeitem


def get_sql_student_values(student_dict, last_student_ep_dict, result_info_list):  # PR2021-12-30

    # function puts result and grade info in return list sql_student_values

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('>>>>> ----------- get_sql_student_values ----------- ')
        logger.debug('!!!!!!!!!!!@@ last_student_ep_dict: ' + str(last_student_ep_dict))
        logger.debug('@@@@@@@@@@@@@@@@@ student_dict: ' + str(student_dict))
    """

    last_student_ep_dict: {
        'ep': 2, 
        'final': {'sum': 43, 'cnt': 7, 'info': ' ec:6(h) en:6 fr:5 ne:7 sp:6 wk:6 combi:7', 'avg': '6.1', 'result': 'Gemiddeld eindcijfer: 6.1 (43/7) '}, 
        'combi': {'sum': 21, 'cnt': 3, 'info': ' cav:7 lo:8 mm1:6', 'final': 7, 'result': 'Combinatiecijfer: 7 (21/3) '}, 
        'pece': {'sumX10': 352, 'cnt': 6, 'info': ' ec:6,5(h) en:6,4 fr:3,5 ne:7,5 sp:5,4 wk:5,9', 'avg': '5.8', 'result': 'Gemiddeld CE-cijfer: 5,8 (35,2/6) '}, 
        'count': {'c3': 0, 'c4': 0, 'c5': 1, 'c6': 4, 'c7': 2, 'core4': 0, 'core5': 0}, 
        'passed': {'cnt3457': '1 vijf en voor de andere vakken een 6 of hoger.', 'avgce55': 'Gemiddeld CE-cijfer is 5,8.'}, 
        'result_index': 1}
        
    student_dict: {'fullname': 'Bansingh, Akim', 'stud_id': 4377, 'country': 'Sint Maarten', 'examyear_txt': '2022', 
        'school_name': 'Milton Peters College', 'school_code': 'SXM01', 'islexschool': False, 
        'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'depbase_code': 'Vsbo', 'dep_abbrev': 'V.S.B.O.', 
        'lvl_name': 'Praktisch Kadergerichte Leerweg', 'lvlbase_code': 'PKL', 'level_req': True, 
        'sct_name': 'Economie', 'dep_id': 7, 'lvl_id': 8, 'sct_id': 20, 'scheme_id': 93, 
        'classname': 'EACp4a', 'has_profiel': False, 'examnumber': '301', 
        'iseveningstudent': False, 'islexstudent': False, 'bis_exam': True, 'partial_exam': False, 
        'exemption_count': 1, 'sr_count': 0, 'reex_count': 2, 'reex03_count': 0, 'thumbrule_count': 0, 'withdrawn': False, 
        'c_subj': 11, 'c_thumbrule': 1, 
         'c_ep2': 2, 'c_ep4': 1, 
    28266: {'si_id': 2555, 'subj': 'ac', 'is_thumbrule': True, 
            1: {'subj': 'ac', 'se': '5.4', 'sr': None, 'sesr': '5.4', 'pe': None, 'ce': '5.1', 'pece': '5.1', 'final': '5', 
                'max_ep': 1, 'max_sesr': '5.4', 'max_pece': '5.1', 'max_final': '5', 'max_ni': [], 'max_noin': [], 'max_use_exem': False}, 
            2: {'subj': 'ac', 'se': '5.4', 'sr': None, 'sesr': '5.4', 'pe': None, 'ce': None, 'pece': None, 'final': None, 
                'max_ep': 1, 'max_sesr': '5.4', 'max_pece': '5.1', 'max_final': '5', 'max_ni': [], 'max_noin': [], 'max_use_exem': False}}, 
    28262: {'si_id': 2551, 'subj': 'cav', 1: {'subj': 'cav', 'se': '7.3', 'sr': None, 'sesr': '7.3', 'pe': None, 'ce': None, 'pece': None, 'final': '7',
            'max_ep': 1, 'max_sesr': '7.3', 'max_pece': None, 'max_final': '7', 'max_ni': [], 'max_noin': [], 'max_use_exem': False}}, 
    28268: {'si_id': 2554, 'subj': 'ec', 'has_reex': True,
            1: {'subj': 'ec', 'se': '6.0', 'sr': None, 'sesr': '6.0', 'pe': None, 'ce': '1.3', 'pece': '1.3', 'final': '4', 
                'max_ep': 1, 'max_sesr': '6.0', 'max_pece': '1.3', 'max_final': '4', 'max_ni': [], 'max_noin': [], 'max_use_exem': False}, 
            2: {'subj': 'ec', 'se': '6.0', 'sr': None, 'sesr': '6.0', 'pe': None, 'ce': '6.5', 'pece': '6.5', 'final': '6', 
                'max_ep': 2, 'max_sesr': '6.0', 'max_pece': '6.5', 'max_final': '6', 'max_ni': [], 'max_noin': [], 'max_use_exem': False}}, 
    28259: {'si_id': 2559, 'subj': 'en', 'has_exemption': True, 'exemption_year': 2021, 
            1: {'subj': 'en', 'se': '5.9', 'sr': None, 'sesr': '5.9', 'pe': None, 'ce': '6.4', 'pece': '6.4', 'final': '6', 
                'max_ep': 1, 'max_sesr': '5.9', 'max_pece': '6.4', 'max_final': '6', 'max_ni': [], 'max_noin': [], 'max_use_exem': False}, 
            4: {'subj': 'en', 'se': '6.7', 'sr': None, 'sesr': '6.7', 'pe': None, 'ce': '4.5', 'pece': '4.5', 'final': '6', 
                'max_ep': 4, 'max_sesr': '6.7', 'max_pece': '4.5', 'max_final': '6', 'max_ni': [], 'max_noin': [], 'max_use_exem': True}}, 

    'ep1': {'ep': 1, 
            'final': {'sum': 41, 'cnt': 7, 'info': ' ec:4 en:6 fr:5 ne:7 sp:6 wk:6 combi:7', 'avg': '5.9', 'result': 'Gemiddeld eindcijfer: 5.9 (41/7) '}, 
            'combi': {'sum': 21, 'cnt': 3, 'info': ' cav:7 lo:8 mm1:6', 'final': 7, 'result': 'Combinatiecijfer: 7 (21/3) '}, 
            'pece': {'sumX10': 300, 'cnt': 6, 'info': ' ec:1,3 en:6,4 fr:3,5 ne:7,5 sp:5,4 wk:5,9', 'avg': '5.0', 'result': 'Gemiddeld CE-cijfer: 5,0 (30/6) '}, 
            'count': {'c3': 0, 'c4': 1, 'c5': 1, 'c6': 3, 'c7': 2, 'core4': 0, 'core5': 0}, 
            'result_index': 2, 
            'failed': {'cnt3457': '1 vier en 1 vijf.', 'avgce55': 'Gemiddeld CE-cijfer is 5,0, moet onafgerond 5,5 of hoger zijn.'}}, 
    'ep2': {'ep': 2, 
            'final': {'sum': 43, 'cnt': 7, 'info': ' ec:6(h) en:6 fr:5 ne:7 sp:6 wk:6 combi:7', 'avg': '6.1', 'result': 'Gemiddeld eindcijfer: 6.1 (43/7) '}, 
            'combi': {'sum': 21, 'cnt': 3, 'info': ' cav:7 lo:8 mm1:6', 'final': 7, 'result': 'Combinatiecijfer: 7 (21/3) '}, 
            'pece': {'sumX10': 352, 'cnt': 6, 'info': ' ec:6,5(h) en:6,4 fr:3,5 ne:7,5 sp:5,4 wk:5,9', 'avg': '5.8', 'result': 'Gemiddeld CE-cijfer: 5,8 (35,2/6) '}, 
            'count': {'c3': 0, 'c4': 0, 'c5': 1, 'c6': 4, 'c7': 2, 'core4': 0, 'core5': 0}, 
            'passed': {'cnt3457': '1 vijf en voor de andere vakken een 6 of hoger.', 'avgce55': 'Gemiddeld CE-cijfer is 5,8.'}, 
            'result_index': 1}, 
    'last_ep': 'ep2'}
    """
    def get_sql_value_str(value):
        return ''.join(("'", str(value), "'")) if value else 'NULL'

    def get_sql_value_int(value):
        return str(value) if value else '0'

    sql_student_values = []
    try:
        student_id = student_dict.get('stud_id')
        exemption_count_str = get_sql_value_int(student_dict.get('c_ep4'))
        sr_count_str =  get_sql_value_int(student_dict.get('sr_count_str'))
        reex_count_str =  get_sql_value_int(student_dict.get('c_ep2'))
        reex03_count_str =  get_sql_value_int(student_dict.get('c_ep3'))
        thumbrule_count_str =  get_sql_value_int(student_dict.get('c_thumbrule'))
        # TODO add field subj_count to model
        # subject_count =  get_sql_value_int(student_dict.get('c_subj'))

        if logging_on:
            logger.debug('     exemption_count_str: ' + str(exemption_count_str))
            logger.debug('     reex_count_str: ' + str(reex_count_str))

        last_ep_key = student_dict.get('last_ep')
        last_ep_dict = student_dict.get(last_ep_key)

        if logging_on:
            logger.debug('?????????????!@@ last_ep_dict: ' + str(last_ep_dict))

        gl_ce_avg = af.get_dict_value(last_ep_dict, ('pece', 'avg'))
        gl_combi_avg = af.get_dict_value(last_ep_dict, ('combi', 'final'))
        gl_final_avg = af.get_dict_value(last_ep_dict, ('final', 'avg'))
        result_index = last_ep_dict.get('result_index') or 0

        """
        last_ep_dict: {'ep': 1, 
        'final': {'sum': 41, 'cnt': 7, 'info': ' ec:4 en:6 fr:5 ne:7 sp:6 wk:6 combi:7', 'avg': '5.9', 
        'result': 'Gemiddeld eindcijfer: 5.9 (41/7) '}, 
        'combi': {'sum': 21, 'cnt': 3, 'info': ' cav:7 lo:8 mm1:6', 'final': 7, 
        'result': 'Combinatiecijfer: 7 (21/3) '}, 
        'pece': {'sumX10': 300, 'cnt': 6, 'info': ' ec:1,3 en:6,4 fr:3,5 ne:7,5 sp:5,4 wk:5,9', 'avg': '5.0', 
        'result': 'Gemiddeld CE-cijfer: 5,0 (30/6) '}, 
        'count': {'c3': 0, 'c4': 1, 'c5': 1, 'c6': 3, 'c7': 2, 'core4': 0, 'core5': 0}, 
        'result_index': 2, 
        'failed': {'cnt3457': '1 vier en 1 vijf.', 'avgce55': 'Gemiddeld CE-cijfer is 5,0, moet onafgerond 5,5 of hoger zijn.'}}

        """
        gl_ce_avg_str = ''.join(("'", str(gl_ce_avg), "'")) if gl_ce_avg else 'NULL'
        gl_combi_avg_str = ''.join(("'", str(gl_combi_avg), "'")) if gl_combi_avg else 'NULL'
        gl_final_avg_str = ''.join(("'", str(gl_final_avg), "'")) if gl_final_avg else 'NULL'

        result_index_str = str(result_index) if result_index else '0'
        result_status_str = ''.join(("'", c.RESULT_CAPTION[result_index], "'")) if c.RESULT_CAPTION[
            result_index] else 'NULL'

        result_info = '|'.join(result_info_list) if result_info_list else None
        result_info_str = ''.join(("'", result_info, "'")) if result_info else 'NULL'

        e1_ce_avg_str, e1_combi_avg_str, e1_final_avg_str, e1_result_index_str = 'NULL', 'NULL', 'NULL', '0'
        ep1_dict = student_dict.get('ep1')
        if ep1_dict:
            e1_ce_avg = af.get_dict_value(ep1_dict, ('pece', 'avg'))
            e1_combi_avg = af.get_dict_value(ep1_dict, ('combi', 'final'))
            e1_final_avg = af.get_dict_value(ep1_dict, ('final', 'avg'))
            e1_result_index = ep1_dict.get('result_index')

            e1_ce_avg_str = ''.join(("'", str(e1_ce_avg), "'")) if e1_ce_avg else 'NULL'
            e1_combi_avg_str = ''.join(("'", str(e1_combi_avg), "'")) if e1_combi_avg else 'NULL'
            e1_final_avg_str = ''.join(("'", str(e1_final_avg), "'")) if e1_final_avg else 'NULL'
            e1_result_index_str = str(e1_result_index) if e1_result_index else '0'

        e2_ce_avg_str, e2_combi_avg_str, e2_final_avg_str, e2_result_index_str = 'NULL', 'NULL', 'NULL', '0'
        ep2_dict = student_dict.get('ep2')
        if ep2_dict:
            e2_ce_avg = af.get_dict_value(ep2_dict, ('pece', 'avg'))
            e2_combi_avg = af.get_dict_value(ep2_dict, ('combi', 'final'))
            e2_final_avg = af.get_dict_value(ep2_dict, ('final', 'avg'))
            e2_result_index = ep2_dict.get('result_index')

            e2_ce_avg_str = ''.join(("'", str(e2_ce_avg), "'")) if e2_ce_avg else 'NULL'
            e2_combi_avg_str = ''.join(("'", str(e2_combi_avg), "'")) if e2_combi_avg else 'NULL'
            e2_final_avg_str = ''.join(("'", str(e2_final_avg), "'")) if e2_final_avg else 'NULL'
            e2_result_index_str = str(e2_result_index) if e2_result_index else '0'

        """
        sql_student_values = [ str(student_id),
            gl_ce_avg_str, gl_combi_avg_str, gl_final_avg_str, result_index_str,  result_status_str,  result_info_str,
            e1_ce_avg_str, e1_combi_avg_str, e1_final_avg_str, e1_result_index_str,
            e2_ce_avg_str, e2_combi_avg_str, e2_final_avg_str, e2_result_index_str,
            exemption_count, sr_count, reex_count, reex03_count,thumbrule_count
        ]
        sql_student_values: [ '4377', 
            "'5.8'", "'7'", "'6.1'", '1', "'Geslaagd'", "'Uitslag na herexamen: GESLAAGD'", 
            "'5.0'", "'7'", "'5.9'", '2', 
            "'5.8'", "'7'", "'6.1'", '1']
        sql_student_values: ['4377', 
            "'5.0'", "'7'", "'5.9'", '2', "'Afgewezen'", "'Uitslag: AFGEWEZEN|1 vier en 1 vijf.|Gemiddeld CE-cijfer is 5,0, moet onafgerond 5,5 of hoger zijn.'", 
            "'5.0'", "'7'", "'5.9'", '2', 'NULL', 'NULL', 'NULL', '0', '0', '0', '0', '0', '0']
    
        """

        sql_student_values = [str(student_id),
                                gl_ce_avg_str, gl_combi_avg_str, gl_final_avg_str, result_index_str,
                                result_status_str, result_info_str,
                                e1_ce_avg_str, e1_combi_avg_str, e1_final_avg_str, e1_result_index_str,
                                e2_ce_avg_str, e2_combi_avg_str, e2_final_avg_str, e2_result_index_str,
                                exemption_count_str, sr_count_str,
                                reex_count_str, reex03_count_str, thumbrule_count_str
                              ]

        if logging_on:
            logger.debug('     sql_student_values: ' + str(sql_student_values))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return sql_student_values
# --- end of get_sql_student_values


###############################
def log_list_header(sel_school, sel_department, sel_examyear, user_lang):  # PR2021-12-20
# - create log_list
    today_dte = af.get_today_dateobj()
    today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)

    school_name = sel_school.base.code + ' ' + sel_school.name
    log_list = [c.STRING_DOUBLELINE_80,
                str(_('Calculate results')) + ' ' + str(_('date')) + ': ' + str(today_formatted),
                c.STRING_DOUBLELINE_80]
    log_list.append(c.STRING_SPACE_05 + str(_("School    : %(name)s") % {'name': school_name}))
    log_list.append(c.STRING_SPACE_05 + str(_("Department: %(dep)s") % {'dep': sel_department.name}))
    log_list.append(c.STRING_SPACE_05 + str(_("Exam year : %(ey)s") % {'ey': str(sel_examyear.code)}))

    log_list.append(c.STRING_SPACE_05)

    return log_list
# - end of log_list_header


def log_list_student_header(student_dict, full_name, log_list):  # PR2021-12-19

    log_list.append(c.STRING_SINGLELINE_80)
    log_list.append(full_name)
    depbase_code = student_dict.get('depbase_code') or ''
    lvlbase_code = student_dict.get('lvlbase_code') or ''
    sct_name = student_dict.get('sct_name') or ''
    log_list.append( ('').join((c.STRING_SPACE_05, depbase_code, ' ', lvlbase_code, ' ', sct_name )))


def log_list_add_scheme_notfound(dep_level_req, log_list):  # PR2021-12-19
    # - add msg when scheme not found
    log_list.append(''.join((c.STRING_SPACE_05, str(_('The subjectscheme of this candidate could not be found.')))))
    log_list.append(''.join((c.STRING_SPACE_05, str(_('The result cannot be calculated.')))))
    msg_txt = _('Please enter the leerweg and sector.') if dep_level_req else _('Please enter the profiel.')
    log_list.append(('').join((c.STRING_SPACE_05, str(msg_txt))))
# - end of log_list_add_scheme_notfound


def log_list_reex_count(exemption_count, sr_count, reex_count, reex03_count, thumbrule_count, log_list):
    # PR2021-12-20 PR2021-12-28 PR2022-06-03
    if exemption_count or sr_count or reex_count or reex03_count:
        if exemption_count:
            cpt = str(_('Exemption') if exemption_count == 1 else _('Exemptions')).lower()
            log_list.append(''.join((c.STRING_SPACE_05, str(_('has')), ' ', str(exemption_count), ' ', cpt)))
        elif sr_count:
            cpt = str(_('Re-examination school exam') if sr_count == 1 else _('Re-examinations school exam')).lower()
            log_list.append(''.join((c.STRING_SPACE_05, str(_('has')), ' ', str(sr_count), ' ', cpt)))
        if reex_count:
            cpt = str(_('Re-examination') if reex_count == 1 else _('Re-examinations')).lower()
            log_list.append(''.join((c.STRING_SPACE_05, str(_('has')), ' ', str(reex_count), ' ', cpt)))
        if reex03_count:
            cpt = str(_('Re-examination 3rd period') if reex03_count == 1 else _('Re-examinations 3rd period')).lower()
            log_list.append(''.join((c.STRING_SPACE_05, str(_('has')), ' ', str(reex03_count), ' ', cpt)))
        if thumbrule_count:
            cpt = str(_('thumb rule is applied') if thumbrule_count == 1 else _('thumb rules are applied'))
            log_list.append(''.join((c.STRING_SPACE_05, str(thumbrule_count), ' ', cpt)))


def log_list_subject_grade (this_examperiod_dict, examperiod, multiplier, weight_se, weight_ce, has_practexam, sr_allowed, no_practexam):
    # PR2021-12-20 PR2022-06-05

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ---------- log_list_subject_grade ----------')
        logger.debug('this_examperiod_dict: ' + str(this_examperiod_dict))
    multiplier_str = ''.join(('(', str(multiplier), 'x)')) if multiplier != 1 else ''
    weight_se_str = ''.join(('(x', str(weight_se), ')')) if weight_se != 1 else ''

    # this_examperiod_dict = {'se': '8.0', 'sesr': '8.0', 'ni': ['ce']}
    noinput_se, noinput_sr, noinput_pe, noinput_ce = False, False, False, False
    noinput_list = this_examperiod_dict.get('ni')
    if noinput_list:
        noinput_se = 'se' in noinput_list
        noinput_sr = 'sr' in noinput_list
        noinput_pe = 'pe' in noinput_list
        noinput_ce = 'ce' in noinput_list
    # {'se': '8.0', 'sesr': '8.0', 'ni': ['sr', 'ce']}
    se_str = '-' if noinput_se else (this_examperiod_dict.get('se') or '-')
    sr_str = '-' if noinput_sr else (this_examperiod_dict.get('sr') or '-')
    sesr_str = this_examperiod_dict.get('sesr') or '-'

    pe_str = '-' if noinput_pe else (this_examperiod_dict.get('pe') or '-')
    ce_str = '-' if noinput_ce else (this_examperiod_dict.get('ce') or '-')
    pece_str = this_examperiod_dict.get('pece') or '-'

    # when sr has value : display SE:6 [se: 4, her: 8]
    # when sr is '':  display SE:6

# when has_sr: sr_str has either value or 'noinput
    if weight_se <= 0:
        sesr_display = ''
    elif sr_str or noinput_sr:
        se_str = se_str.replace('.', ',')
        sr_str = sr_str.replace('.', ',')
        sesr_str = '-' if noinput_se or noinput_sr else sesr_str.replace('.', ',')
        detail_str = ''.join((' [se:', se_str, ' herk:', sr_str, ']')) if sr_allowed else ''
        sesr_display = ''.join(('SE:', sesr_str, detail_str, multiplier_str, weight_se_str))
    else:

# when not has_sr: sr_str has either value or 'noinput
        sesr_str = '-' if noinput_se else sesr_str.replace('.', ',')
        sesr_display = ''.join(('SE:', sesr_str, multiplier_str, weight_se_str))

    if weight_ce <= 0:
        pece_display = ''
    elif has_practexam and not examperiod == c.EXAMPERIOD_EXEMPTION:
        pe_str = pe_str.replace('.', ',')
        ce_str = ce_str.replace('.', ',')
        pece_str = '-' if noinput_pe or noinput_ce else pece_str.replace('.', ',')

        detail_str = ''.join((' [theorie:', ce_str, ' praktijk:', pe_str, ']')) if not no_practexam else ''
        pece_display = ''.join((' CE:', pece_str, detail_str))
    else:
        pece_str = '-' if noinput_ce else pece_str.replace('.', ',')
        pece_display = ''.join((' CE:', pece_str))

    ep_str = ''
    if examperiod == c.EXAMPERIOD_EXEMPTION:
        ep_str = str(_('Exemption')) + ': '
    elif examperiod == c.EXAMPERIOD_SECOND:
        ep_str = str(_('Re-examination')) + ': '
    elif examperiod == c.EXAMPERIOD_THIRD:
        ep_str = str(_('Re-examination 3rd period')) + ': '

    final_str = this_examperiod_dict.get('final') or '-'
    grade_str = ''.join((' ', str(_('Final grade')), ':', final_str))

    if logging_on:
        logger.debug('     ep_str: ' + str(ep_str))
        logger.debug('     sesr_display: ' + str(sesr_display))
        logger.debug('     pece_display: ' + str(pece_display))
        logger.debug('     grade_str: ' + str(grade_str))
    subj_grade_str = ''.join((str(ep_str), sesr_display, pece_display, grade_str))
    return subj_grade_str
# - end of log_list_subject_grade

"""
from AWP function CalcPassedFailed PR2021-11-19

'A. reset return variables / Validate
    '1. reset return variables
    '2. geef waarde aan k_AfkStudierichting en k_Studierichting
    '3. Validatie
        'a. exit als  k_KandidaatAID niet ingevuld
        'b. exit als  k_Locked PR2016-04-03
        'c. exit als leerweg/sector of profiel niet is ingevuld 'PR2015-01-17 toegevoegd
        'd. exit bij onbekende leerweg Vsbo PR 30 apr 13 hier gezet ipv aan einde functie. Was: 'PR 2 jul 09 Debug natuurwetenschappen is profiel oude stijl: 'na door lopen vakken gezet, om is havovwo te kunnen gebruiken

'B. open recordset Kandidaat_Vak / Vakken / VakSchemaItems van deze kandidaaat
    '1. maak read-only recordset Kandidaat_Vak (en gelinkte tabellen Vakken, VakSchemaItems) met filter k_KandidaatAID. Filter afdeling zit in functie Verwerken
    '2. exit als geen vakken ingevuld

'C. FILL ARRAY HEREXAMENVAKKEN - Doorloop mogelijke herexamens per vak   
    'FillArrHervakken zet gegevens van mogelijke herexamenvakken in arrHerVakken (dwz vakken met CE-weging>0, geen Combinatievak, geen KeuzeCombi vak, geen ExtraVakTeltNietMee)
    Call FillArrHervakken(rsKandVak, arrHerVakken(), intUbound, IsCalcHerexVakken, k_KandidaatAID)

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
' D. Doorloop intIndex - mogelijke herexamenvakken - eerste keer om uitslag Tv01 te berekenen
    For intIndex = -1 To intUbound
        ' Doorloop intIndex - mogelijke herexamenvakken - eerste keer om uitslag Tv01 te berekenen
        'bij intIndex = -1 wordt uitslag TV01 berekend, intUbound is arrHerVakken.Ubound

    '1. geef waarde aan lngTestVakAID - niet bij intIndex = -1
                'crcLowerCijfer begint met PeCE cijfer, crcUpperCijfer begint met 10
                 'Lower en Upper cijfer convergeren. Exit loop als ze in 2 cycles hetzelfde zijn gebleven.

'++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
' E. itineratie crcTestCijfer For X = 1 To xMax
            'bij intIndex = -1 wordt loop maar eenmaal doorlopen, anders maximaal 15x
    '1. reset variables
    '2. geef waarde aan crcPreviousTestCijfer

'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
'doorloop zo nodig 2e en 3e tijdvak als het herexkand is, niet bij calc_herex
    For loopTv = conTv01 To conTv03
               '1. Reset CountEindcijfers. debug PR2019-06-20 bedug: aantal vakken werd doorgeteld in Tv02 en Tv 03
                '1. skip Tv2 of Tv03 als geen herexkand, skip als bij calc_herex intIndex > -1
               '2. Reset CountEindcijfers. debug PR2019-06-20 bedug: aantal vakken werd doorgeteld in Tv02 en Tv 03

        $$$$$$$$$$$$$$$$$$$$$$$$$$$$
        'F. doorloop vakken van deze kandidaat - Do While Not rsKandVak.EOF
                    Do While Not rsKandVak.EOF
                '2. geef waarde aan KandVak variabelen
                    'a. Geef waarde aan Vakken_ en Vsi_ variabelen, gelden voor alle tijdvakken
                    'b. Geef waarde aan Input_ variabelen (inputSE, inputPE, inputCE, inputHER, inputTV03, inputSEvrst, inputCEvrst)
                    'c. Geef waarde aan IsCombinatievakOfKeuzeCombi 'PR2015-12-15 gewijzigd. 'PR 20 feb 12  OfKeuzeCombi toegevoegd  'As Boolean
                        'PR2015-04-26 debug CAL Lionel Mongen: Bij vsbo waren alle kandidaatvakken IsKeuzeCombi, daarom werd eindcijfer niet berekend.  'zie opmerking PR2015-02-16 debug: IsExtraVak en KeuzeCombi werden als True ingevuld, weet niet waarom
                        'Om dit te voorkomen wordt IsKeuzeCombi allleen True als pblafd.KeuzeCombiAllowed (alleen bij Vwo) en als clsVsi.KeuzeCombiAllowed (alleen vakken waarboij KeuzeCombi is toegestaan)
                    'd. Geef waarde aan IsExtraVak
                    'e. Geef waarde aan Has Vrijstelling
                    'f. Geef waarde aan HasPraktijkexamen 'PR2015-12-15
                    'g. Geef waarde aan kv_IsHerVak
                    'h. Geef waarde aan Kv_Multiplier (geldt voor alle tijdvaken)
                    'i. Geef waarde aan kv_Eindcijfers 'PR2019-04-16
                    'j. Geef waarde aan PeCe variabelen (conTv01, conTv02, conTv03)
                        'NB: kv_PeCe_Ref is berekend in CalcEindcijferOvg, dat wordt doorlopen in Kand_Verwerken, voor CalcPassedFailed
                        'PR2019-04-18 waarden PeCe variabelen worden voortaan opgehaald met ConvertOutputFromString uit kv_Eindcijfers in plaats van alle aparte velden
                    'k. Geef waarde aan kv_Eindcijfer_Ref variabelen (conTv01, conTv02, conTv03)
                        'NB: kv_Eindcijfer_Ref is berekend in CalcEindcijferOvg, dat wordt doorlopen in Kand_Verwerken, voor CalcPassedFailed
                        'PR2019-04-18 waarde kv_Eindcijfer_Ref variabelen worden voortaan opgehaald met ConvertOutputFromStringuit kv_Eindcijfers in plaats van alle aparte velden
                '3. Geef waarde aan k_IsHerexKand - ga na of er herexvakken zijn in Tv02 of Tv03, om Tv02 en Tv03 te doorlopen PR2019-04-23

            'H. VERVANG CEcijfer door Testcijfer als VakAID = lngTestVakAID
            If IsCalcHerexVakken And intIndex > -1 Then 'PR2015-11-07 voor de zekerheid toegevoegd (lngTestVakAID=0 dus hoeft eigenlijk niet)
                        'a. bij intIndex = -1 is lngTestVakAID = 0 en wordt CEcijfer niet vervangen
                        'b. vervang GemidCSE door TestCijfer
            'H. EINDE - VERVANG CEcijfer door Testcijfer als VakAID = lngTestVakAID

                '4. Bereken PeCe cijfer en Eindcijfer
                    CalcEindcijfer_CijferOvg

            'G. Validatie cijfers - voor overslaan extra vak geplaatst PR2015-11-18
                '1. Validate Cijfers
                      'a. Ga na of SE cijfer / CE cijfer / PEcijfer / HER / PeHer cijfer is ingevuld

                    'b. Validatie Werkstuk / Stage
                    'c. ga na of Vsi_HasPraktijkexamen correct is (niet toegestaan in Havo/Vwo en TKL en alleen bij sectorprogramma)
                '2. Vakken overslaan
                    'a. Extra vak wordt overgeslagen
                    'b. sla vak over als CijferType geen Nummer en geen VoldoendeOnvoldoende is

            'I. Bereken combicijfer
                        'NB: Combivakken kunnen een Her hebben, maar het Her wordt niet meegeteld in de berekening van het combivak (alleen SE cijfers tellen mee in het combivak) : PR 16 apr 13
                          'Herexamens worden ingesteld in form R_Her_KandVakken, alleen vakken met CE weging > 0 worden weergegeven.
                          'Vakken met CE weging > 0 kunnen niet als combivak worden aangemerkt, wel als keuze-combi. Dan wordt CE cijfer op Null gezet en ook overgeslagen bij berekening eindcijfer. PR2017-02-28
                    'HvD 17 apr 13: volgens hem kunnen keuzecombivakken geen her hebben, maar weet het niet zeker. Zal het nazoeken. (Wordt keuzecombi bepaald voor CE examen of kan het daarna nog?)

                    'PR2-016-12-26 achter 'E. Bereken kv_Eindcijfer_crc en k_CijferInfo gezet, omdat daar kv_Eindcijfer_crc berekend wordt uit kv_Eindcijfer_str

            ' K. CountCijfers: 'PR2019-04-19
                        k_v_Calc02a_CountCijfers

            'J. Bereken Som van de Eindcijfers en Som van de CE-cijfers
                        k_v_Calc02b_SumEindcijfers_SumCE
            'K. Bereken cijfer info 'PR2019-05-02 niet bij CalcHerexVakken
                    If IsCalcHerexVakken And intIndex > -1 Then
                        'skip
                    Else
                        Call k_v_Calc02c_CijferInfo
        'Einde F. doorloop vakken van deze kandidaat - Loop - Do While Not rsKandVak.EOF
        $$$$$$$$$$$$$$$$$$$$$$$$$$$$

        'L. Bereken gemiddelde Combicijfer, Eindcijfer en CE cijefr
                '1. Validate aantal keren dat Werkstuk, Stage voorkomt 'PR2015-11-14  NB: controle op ingevuld, cijfertype vindt plaats binnen loop Kv-loop in k_v_Calc01_Validate_Cijfers
                    kCalc01_Validate_Werkst_Stage_Sectorpr_Count
                '2. Bereken combi cijfer, tel op bij CountEindcijfers en SomEincijfers
                    kCalc02a_CountCombiEindcijfer
                '3. bereken text GemidCOMBI_info, ExtraVak_info, VakOvergeslagen_info PR 28 apr 13
                    kCalc02b_CombiEindcijfer_ExtraVak_info
                '3. Bereken EindCijfer_Gemid en k_CEcijfer_Gemid
                    kCalc03a_EINDgemid_CEgemid_calc_en_info

        'M. BEREKEN UITSLAG

               '1. geef waarde aan
                   'k_Examenregeling = bv.: "Examenregeling Havo Curaçao " & CStr(k_Examenjaar) & " met kernvak-eis (avondschool)"
                   'k_ShowGemidCijfer(CEcijfer/EINDcijfer) = TRUE / FALSE
                   'k_ResultaatID(Tv01/Tv02/TvEIND)
                   'k_UitslagReden
                        kCalc04a_Examenregeling
                        kCalc04b_AdjustResultaatId
               '2. geef waarde aan k_EINDcijfer_Gemid_Text (ook bij ManualResultaat) PR 1 mei 13
               '3. geef waarde aan k_k_CEcijferGemid_Text (ook bij ManualResultaat) PR 1 mei 13
                   'NB: k_k_CEcijferGemid_Text geldt zowel voor gewoon als herexamen, hoogste van gewoon en her wordt meegeteld PR 1 mei 13
                   'NB: k_k_CEcijferGemid_Text wordt berekend in F5. Zet hier op 0, als not k_ShowGemidcijfer(CEcijfer), dan wordt het niet op de cijferlijst geprint PR 10 jun 12

                        kCalc05_EINDcijfer__CEcijfer_GemidTEXT
                  'PR2019-12-02 gaf 0 bij lege combivakken., if = 0 toegevoegd

    Next loopTv
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
                loopTv = conTv01

                   'bij intIndex = -1 wordt uitslag berekend
                   'PR2019-0502 houd geen rekening met herexamens
               '1. pas waarde crcLowerCijfer en crcUpperCijfer aan
                   'verfijn cijfer op basis resultaten vorige loop (convergerende reeks) PR2015-10-05
                               'als testresult geslaagd: verlaag crcTestCijfer (dwz crcUpperCijfer wordt gelijk aan crcTestCijfer)
                                ' onthoudt dat dit cijfer uitslag geslaagd geeft, ofwel: crcMinimumPassedCijfer = crcTestCijfer
                               'als testresult afgewezen: verhoog crcTestCijfer (dwz crcLowerCijfer wordt gelijk aan crcTestCijfer)
                                ' onthoudt dat dit cijfer uitslag afgewezen geeft, ofwel: crcLowerCijfer = crcTestCijfer
                               'Call AppendLogFile(strLogPath, "Uitslag " & lngTestResult & " niet toegestaan", True)
                '2. genereer testcijfer
                   'a.het CEcijfer van het vak met VakAID uit arrHer wordt vervangen door een testCEcijfer. Het testcijfer ligt halverwege crcLowerCijfer en crcUpperCijfer
                   'b. afronden naar beneden
                   'c. max 10
                   'd. niet lager dan crcLowerCijfer

               '3. exit als crcPreviousTestCijfer = crcTestCijfer

' Einde E. itineratie crcTestCijfer For X = 1 To xMax
'++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        'N. AppendLogFile
' Einde D. Doorloop intIndex - mogelijke herexamenvakken - eerste keer om uitslag Tv01 te berekenen
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
'O. Bereken preferred herex
    '1. Bereken preferred herex
        'geen herexamenvakken mogelijk als
                    'bereken eerst de 'preferred herex' - met laagste Benodigd Cijfer
            'DifCount telt aantal herren met MinDif
            'als er meer dan 1 her is met laagste Benodigd Cijfer: zoek met laagste MinDif

        'a. beginwaarde Min variabelen  is 99
        'b. ga na of CE en Benodigd zijn ingevuld

           'maak vak met minCE preferred Herexamenvak
                       'geef waarde aan output parameter

'P. 'geef waarde aan appendlog (bij alle kandidaten ) en strValuelistHerexVakken ( bij 1 kand

'Q. ExitFunction en Logtext

"""
