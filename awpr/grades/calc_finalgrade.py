# PR2021-01-17
from decimal import Decimal
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import connection

from awpr import constants as c
from awpr import settings as s
from awpr import functions as af
from awpr import logs as awpr_logs
from grades import calculations as grade_calc
from grades import calc_score as calc_score

import logging
logger = logging.getLogger(__name__)


def calc_sesr_pece_final_grade(si_dict, examperiod, has_sr, exemption_year, se_grade, sr_grade, pe_grade, ce_grade):
    # PR2021-12-28 PR2022-04-11  PR2022-05-26
    # called by GradeUploadView.recalc_finalgrade_in_grade_and_save and by import_studsubj_grade_from_datalist
    # this function does not save the calculated fields
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- calc_sesr_pece_final_grade -------')
        logger.debug('si_dict: ' + str(si_dict))

    # - when second or third examperiod: get se_grade and pe_grade from first examperiod,
    # and store them in second or third examperiod
    # NOT ANYMORE: se, sr and pe grades are already stored in grade reex and reex03 when updating

    # PR2022-04-12 no_ce_years = '2020;2021' has list of examyears that had no CE. This is used to skip no_input_ce when calculating exemption endgrade
    # PR2022-04-12 thumb_rule = True: may skip this subject when calculating result

    sesr_grade, pece_grade, finalgrade, delete_cegrade = None, None, None, False
    try:
        sjb_code = si_dict.get('subj_code', '-')
        gradetype = si_dict.get('gradetype', 0)
        weight_se = si_dict.get('weight_se', 0)
        weight_ce = si_dict.get('weight_ce', 0)
        no_ce_years = si_dict.get('no_ce_years')
        #has_practexam = si_dict.get('has_practexam', False)

        # Practical exam does not exist any more. Set has_practexam = False PR2022-05-26
        # was: has_practexam = si_dict.get('has_practexam', False)
        has_practexam = False

        if logging_on:
            logger.debug('     examperiod: ' + str(examperiod))
            logger.debug('     sjb_code:   ' + str(sjb_code))
            logger.debug('     gradetype:  ' + str(gradetype))
            logger.debug('     weight_se:  ' + str(weight_se))
            logger.debug('     weight_ce:  ' + str(weight_ce))
            logger.debug('     se_grade:   ' + str(se_grade) + ' ' + str(type(se_grade)))
            logger.debug('     sr_grade:   ' + str(sr_grade) + ' ' + str(type(sr_grade)))
            logger.debug('     pe_grade:   ' + str(pe_grade) + ' ' + str(type(pe_grade)))
            logger.debug('     ce_grade:   ' + str(ce_grade) + ' ' + str(type(ce_grade)))

# ++++  calculate finalgrade when gradetype is character
        if gradetype == c.GRADETYPE_02_CHARACTER:
    # - calculate sesr_grade
            sesr_grade, se_noinput, sr_noinput = calc_sesr_char(se_grade, sr_grade, has_sr, weight_se)
    # - calculate finalgrade
            finalgrade = calc_finalgrade_char(sesr_grade, se_noinput, sr_noinput, weight_se)

# ++++  calculate finalgrade when gradetype is number
        elif gradetype == c.GRADETYPE_01_NUMBER:

    # - calculate se_sr
            sesr_decimal, se_noinput, sr_noinput = calc_sesr_decimal(examperiod, se_grade, sr_grade, has_sr, weight_se)
            sesr_grade = str(sesr_decimal) if sesr_decimal else None

    # - calculate pe_ce
            # also check if no_exemption_ce
            pece_decimal, pe_noinput, ce_noinput, delete_cegrade = calc_pece_decimal(examperiod, ce_grade, pe_grade, weight_ce,
                                                                     has_practexam, exemption_year, no_ce_years, sjb_code)
            pece_grade = str(pece_decimal) if pece_decimal else None

    # - sesr_noinput = True if als weight_se > 0 and  se_noinput = True or sr_noinput = True
            sesr_noinput = weight_se > 0 and (se_noinput or sr_noinput)

    # - pece_noinput = True if als weight_ce > 0 and  pe_noinput = True or ce_noinput = True
            pece_noinput = weight_ce > 0 and (pe_noinput or ce_noinput)

    # - calculate finalgrade
            finalgrade = calc_final_grade_number(sesr_decimal, pece_decimal,
                                                sesr_noinput, pece_noinput,
                                                weight_se, weight_ce)

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug(' >>> sesr_grade: ' + str(sesr_grade))
        logger.debug(' >>> pece_grade: ' + str(pece_grade))
        logger.debug(' >>> finalgrade: ' + str(finalgrade))

    return sesr_grade, pece_grade, finalgrade, delete_cegrade
# --- end of calc_sesr_pece_final_grade

#@@@@@@@@@@@@@@@@@@@@@@@@@@

def calc_final_grade_number(sesr_decimal, pece_decimal, sesr_noinput, pece_noinput, weight_se, weight_ce):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- calc_final_grade_number -----')
        logger.debug('     sesr_decimal: ' + str(sesr_decimal) + ' ' + str(type(sesr_decimal)))
        logger.debug('     pece_decimal: ' + str(pece_decimal) + ' ' + str(type(pece_decimal)))
        logger.debug('     sesr_noinput: ' + str(sesr_noinput))
        logger.debug('     pece_noinput: ' + str(pece_noinput))

    """
    #'+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #'+  PeCEcijferNietAfgerond = (PEcijfer + CEcijfer) / 2                       +
    #'+  PeCEcijfer             = Int(0.5 + PeCEcijferNietAfgerond x 10) / 10     +
    #'+                                                                           +
    #'+                           (SEcijfer x SEweging) + (PeCEcijfer x CEweging) +
    #'+  EindcijferNietAfgerond = ---------------------------------------------   +
    #'+                                       (SEWeging + CEweging)               +
    #'+                                                                           +
    #'+  Eindcijfer             = Int(0.5 + EindcijferNietAfgerond)               +
    #'+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
   
    HERKANSING - Function Calculations.CalcEindcijfer_Crc_Corona
            'PR2020-05-12 eindcijfer berekening ten tijde van Corona:
        ' - in eerste tijdvak is eindcijfer gelijk aan SE cijfer
        ' - in tweede tijdvak (herkansing) is berekening als in mail Esther:
        ' - vrijstelling berekent eindcijfer op de normale manier, doorloopt de functie CalcEindcijfer_Crc
        ' - derde tijdvak is niet van toepassing
        
        'mail Esther ETE 1 mei 2020:
           ' Het cijfer voor de extra her-toets wordt bepaald op één decimaal en telt voor 50% mee,
           ' het eerder behaalde SE-resultaat voor dat vak ook voor 50%.
           ' Beide cijfers worden gemiddeld en dat is het nieuwe eindcijfer.
           ' Dit geldt niet als het gemiddelde resultaat lager is dan het SE-resultaat.
           ' In dat geval is het Eindcijfer gelijk aan het eerder behaalde SE-resultaat.

        'ook de op 1 decimaal afgerond eindcijfer is een return value, voor weergave op de cijferlijst.
        'daarom crcSEcijfer_na_herkansing() als byref parameter opgenomen.
        
        'PR2020-05-29 debug: Lorraine Wieske JPD: SE_na_herkansing verschijnt niet op cijferlijst,
        ' aparte parameter crcSEcijfer_na_herkansing() gemaakt
    """

    final_grade = None
    if not sesr_noinput and not pece_noinput:
        weight_se_decimal = Decimal(str(weight_se))
        weight_ce_decimal = Decimal(str(weight_ce))
        if sesr_decimal and pece_decimal:
            final_decimal_notrounded = (sesr_decimal * weight_se_decimal + pece_decimal * weight_ce_decimal) \
                                        /( weight_se_decimal + weight_ce_decimal)
        elif sesr_decimal:
            final_decimal_notrounded = sesr_decimal
        elif pece_decimal:
            final_decimal_notrounded = pece_decimal
        else:
            final_decimal_notrounded = None
        if logging_on:
            logger.debug('     final_decimal_notrounded: ' + str(final_decimal_notrounded) + ' ' + str(type(final_decimal_notrounded)))

        if final_decimal_notrounded:
            final_decimal_rounded = final_decimal_notrounded.quantize(Decimal("1"), rounding='ROUND_HALF_UP')
            if logging_on:
                logger.debug('     final_decimal_rounded: ' + str(final_decimal_rounded) + ' ' + str(type(final_decimal_rounded)))
            # final_decimal_rounded is integer , so no need for: final_grade = final_dot.replace('.', ',')
            final_grade = str(final_decimal_rounded)
        else:
            final_grade = None

    if logging_on:
        logger.debug(' >>> final_grade: ' + str(final_grade) + ' ' + str(type(final_grade)))

    return final_grade
# --- end of calc_final_grade_number


def calc_finalgrade_char(sesr_grade, se_noinput, sr_noinput, weight_se):  # PR2021-12-15
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- calc_finalgrade_char -----')
        logger.debug('     sesr_grade: ' + str(sesr_grade) + ' ' + str(type(sesr_grade)))
        logger.debug('     se_noinput: ' + str(se_noinput))
        logger.debug('     sr_noinput: ' + str(sr_noinput))
        logger.debug('     weight_se: ' + str(weight_se) + ' ' + str(type(weight_se)))

    final_grade = None
    if weight_se:
        # if there is no sr: sr_noinput = False
        if not se_noinput and not sr_noinput:
            final_grade = sesr_grade

    if logging_on:
        logger.debug( ' >>> final_grade: ' + str(final_grade) + ' ' + str(type(final_grade)))
    return final_grade
# --- end of calc_finalgrade_char


def calc_sesr_char(se_grade, sr_grade, has_sr, weight_se):  # PR2021-12-15
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- calc_sesr_char -----')
        logger.debug('se_grade: ' + str(se_grade) + ' sr_grade: ' + str(sr_grade) + ' has_sr: ' + str(has_sr))

    if logging_on:
        logger.debug(' ----- calc_sesr_char -----')
        logger.debug('     se_grade: ' + str(se_grade) + ' ' + str(type(se_grade)))
        logger.debug('     sr_grade: ' + str(sr_grade) + ' ' + str(type(sr_grade)))
        logger.debug('     has_sr: ' + str(has_sr))
        logger.debug('     weight_se: ' + str(weight_se) + ' ' + str(type(weight_se)))

    # PR2020-05-15 Corona: Herkansing mogelijk bij ovg vakken. her-cijfer wordt in cegrade gezet
    # berekening:
    # - gebruik SE cijfer als herkansing lager is dan SE of gelijk aan SE
    # - bereken'gemiddelde' van se en ce als herkansing hoger is dan SE:
    #   v + g > g;
    #   o + g > v  LET OP: geen g !
    #   o + v > v

# - reset output variabelen
    se_noinput = False
    sr_noinput = False
    sesr_grade = None

# - skip if weight_se = 0, no error
    if weight_se:

# - check if se_grade has value, if so: set se_noinput = True
        if not se_grade:
            se_noinput = True
        else:

# if subject has no herkansing: sesr_grade = se_grade
            if not has_sr:
                sesr_grade = se_grade

# - check if sr_grade has no value, if so: set sr_noinput = True
            elif not sr_grade:
                sr_noinput = True
            else:
                if se_grade == sr_grade:
                    sesr_grade = se_grade
                else:
                    if se_grade.lower() == 'g':
                        # gebruik SE cijfer als herkansing lager is dan SE
                        sesr_grade = 'g'
                    elif se_grade.lower() == 'v':
                        if sr_grade == 'g':
                            #gemiddeld eindcijfer v + g > g
                            sesr_grade = 'g'
                        elif sr_grade.lower() == 'o':
                            #' gebruik SE cijfer als herkansing lager is dan SE
                            sesr_grade = 'v'
                    elif se_grade.lower() == 'o':
                        # gemiddeld eindcijfer o + g > v (geen g !!!)
                        # gemiddeld eindcijfer o + v > v
                        sesr_grade = 'v'
    if logging_on:
        logger.debug(' >>> sesr_grade: ' + str(sesr_grade))

    return sesr_grade, se_noinput, sr_noinput
# --- end of calc_sesr_char


def calc_sesr_decimal(examperiod, se_grade, sr_grade, has_sr, weight_se):  # PR2021-12-13
    # from AWP Calculations.CalcEindcijfer_SeFinal PR2021-04-12
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- calc_sesr_decimal -----')
        logger.debug('     examperiod:  ' + str(examperiod))
        logger.debug('     se_grade: ' + str(se_grade) + ' ' + str(type(se_grade)))
        logger.debug('     sr_grade: ' + str(sr_grade) + ' ' + str(type(sr_grade)))
        logger.debug('     has_sr: ' + str(has_sr))
        logger.debug('     weight_se: ' + str(weight_se))

# - reset output variabelen
    se_noinput = False
    sr_noinput = False
    sesr_decimal = None

# - skip when second or third examperiod, no error
    # in examperiod reex and reex03 the fields se_grade, sr_grade and sesr_grade are not used
    # PR2021-12-21 not correct: must also calc sesrgrade; se_grade znd sr_grade got value from examperiod 1
    # was: if examperiod_int in (c.EXAMPERIOD_EXEMPTION, c.EXAMPERIOD_FIRST):

# - skip if weight_se = 0, no error
    if weight_se:

# - check if se_grade has value, if so: set se_noinput = True
        if not se_grade:
            se_noinput = True
        else:

# - in se_grade: replace comma by dot, convert to decimal
            se_dot_nz = se_grade.replace(',', '.') if se_grade else "0"
            se_decimal_A = Decimal(se_dot_nz)

# if examperiod exemption: sesr_grade = se_grade
            if examperiod == c.EXAMPERIOD_EXEMPTION:
                sesr_decimal = se_decimal_A
            else:

# if subject has no herkansing: sesr_grade = se_grade
                if not has_sr:
                    sesr_decimal = se_decimal_A

# - check if sr_grade has no value, if so: set sr_noinput = True
                elif not sr_grade:
                    sr_noinput = True
                else:

# - in sr_grade: replace comma by dot, convert to decimal
                    sr_dot_nz = sr_grade.replace(',', '.') if sr_grade else "0"
                    sr_decimal_B = Decimal(sr_dot_nz)

# - check if sr_grade > se_grade:
                    compare_se_sr = sr_decimal_B.compare(se_decimal_A)

# - if sr_grade > se_grade:
                    if compare_se_sr == 1:  # b.compare(a) == 1 means b > a

# calculate average se_grade, only when sr_grade > se_grade
                        sesr_decimal_not_rounded = ( se_decimal_A + sr_decimal_B ) / Decimal("2")

# round to one digit after dot
                        sesr_decimal = grade_calc.round_decimal(sesr_decimal_not_rounded, 1)
                    else:

# if sr_grade <= se_grade: sesr_grade = se_grade
                        sesr_decimal = se_decimal_A

    if logging_on:
        logger.debug(' >>> sesr_decimal: ' + str(sesr_decimal) + ' ' + str(type(sesr_decimal)))
        logger.debug(' >>> se_noinput: ' + str(se_noinput) + ' sr_noinput: ' + str(sr_noinput))
    return sesr_decimal, se_noinput, sr_noinput
# - end of calc_sesr_decimal


def calc_pece_decimal(examperiod, ce_grade, pe_grade, weight_ce, has_practexam, exemption_year, no_ce_years, sjb_code):
    # PR2021-01-18 PR2021-09-18 PR2021-12-14 PR2022-04-12
    # PR2022-04-12 no_ce_years = '2020;2021' has list of examyears that had no CE. This is used to skip no_input_ce when calculating exemption endgrade

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- calc_pece_decimal -----')
        logger.debug('     sjb_code:       ' + str(sjb_code))
        logger.debug('     examperiod:     ' + str(examperiod))
        logger.debug('     ce_grade:       ' + str(ce_grade) + ' ' + str(type(ce_grade)))
        logger.debug('     pe_grade:       ' + str(pe_grade) + ' ' + str(type(pe_grade)))
        logger.debug('     weight_ce:      ' + str(weight_ce))
        logger.debug('     has_practexam:  ' + str(has_practexam))
        logger.debug('     exemption_year: ' + str(exemption_year))
        logger.debug('     no_ce_years:    ' + str(no_ce_years))

    """
    #'+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #'+  PeCEcijferNietAfgerond = (PEcijfer + CEcijfer) / 2                       +
    #'+  PeCEcijfer             = Int(0.5 + PeCEcijferNietAfgerond x 10) / 10     +
    #'+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    """

    # - bereken PeCecijfer uit PE en CE of crcCEvrijst PR2019-01-24
    # - PeCe=0 als CE=0 of als bij Vsi_HasPraktijkex PE=0
    # -  bij vrijstelling wordt geen PE ingevuld, daarom is pece_number gelijk aan ce_number
    #  - Corona: geen PE bij Corona: If pblAfd.IsCorona Then vsi_HasPraktijkex = False

    # PR2022-04-12
# - reset output variabelen
    ce_noinput = False
    pe_noinput = False
    pece_decimal = None
    delete_cegrade = False

# - skip if weight_ce = 0, no error
    if weight_ce:

# - check if this subject had central exam, only when is_ep_exemption
        is_exemption_without_ce = False
        if examperiod == c.EXAMPERIOD_EXEMPTION and exemption_year and no_ce_years:
            # no_ce_years = '2020;2021', value in schemeitem
            # exemption_year = 2020, value in studentsubject
            no_ce_years_arr = no_ce_years.split(';')
            if logging_on:
                logger.debug('     no_ce_years_arr: ' + str(no_ce_years_arr))
                logger.debug('     is_exemption_without_ce: ' + str(str(exemption_year) in no_ce_years_arr))

            if str(exemption_year) in no_ce_years_arr:
                is_exemption_without_ce = True
        # - in case ce_grade has value: remove value from ce_grade
                # this can happen when ETE changes no_ce_years_arr after school has entered exemption CEgrade
                if ce_grade:
                    # delete_cegrade is return_value, to set original ce_grade to None
                    delete_cegrade = True
                    ce_grade = None

# - check if ce_grade has value, if not: set ce_noinput = True, except when is_exemption_without_ce
        if not ce_grade:
            if not is_exemption_without_ce:
                ce_noinput = True

        else:
# - in ce_grade: replace comma by dot, convert to decimal
            ce_dot_nz = ce_grade.replace(',', '.') if ce_grade else "0"
            ce_decimal_A = Decimal(ce_dot_nz)
            if logging_on:
                logger.debug('     ce_dot_nz: ' + str(ce_dot_nz) + ' ' + str(type(ce_dot_nz)))
                logger.debug('     ce_decimal_A: ' + str(ce_decimal_A) + ' ' + str(type(ce_decimal_A)))

# if subject has no practical exam: pece_grade = ce_grade
# also if exemption: pece_grade = ce_grade
            if not has_practexam or examperiod == c.EXAMPERIOD_EXEMPTION:
                pece_decimal = ce_decimal_A

# - check if pe_grade has value, if not: set pe_noinput = True
            elif not pe_grade:
                # exemption has no pe, therefore no need to check on is_exemption_without_ce:
                pe_noinput = True
            else:

# - in pe_grade: replace comma by dot, convert to decimal
                pe_dot_nz = pe_grade.replace(',', '.') if pe_grade else "0"
                pe_decimal_B = Decimal(pe_dot_nz)

# calculate average pece_grade
                pece_decimal_not_rounded = (ce_decimal_A + pe_decimal_B) / Decimal("2")

# round to one digit after dot
                pece_decimal = grade_calc.round_decimal(pece_decimal_not_rounded, 1)
                if logging_on:
                    logger.debug('     pe_dot_nz: ' + str(pe_dot_nz) + ' ' + str(type(pe_dot_nz)))
                    logger.debug('     pe_decimal_B: ' + str(pe_decimal_B) + ' ' + str(type(pe_decimal_B)))
                    logger.debug('     pece_decimal_not_rounded: ' + str(pece_decimal_not_rounded) + ' ' + str(type(pece_decimal_not_rounded)))

    if logging_on:
        logger.debug(' >>> pece_decimal: ' + str(pece_decimal) + ' ' + str(type(pece_decimal)))
        logger.debug(' >>> pe_noinput: ' + str(pe_noinput) + ' ' + str(type(pe_noinput)))
        logger.debug(' >>> ce_noinput: ' + str(ce_noinput) + ' ' + str(type(ce_noinput)))

    return pece_decimal, pe_noinput, ce_noinput, delete_cegrade
# --- end of calc_pece_decimal


def get_score_from_inputscore(input_value, max_score=None):
    # PR2022-02-09 PR2022-05-25
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_score_from_inputscore -----')
        logger.debug('     input_value: ' + str(input_value) + ' ' + str(type(input_value)))
        logger.debug('     max_score:   ' + str(max_score) + ' ' + str(type(max_score)))
    # function converts input_value to whole number PR2021-01-18

# 1. reset output variables
    input_number = None
    input_str = None
    err_list = []

# 2. remove spaces before and after input_value
    imput_trim = input_value.strip() if input_value else ''
    if logging_on:
        logger.debug('     imput_trim: ' + str(imput_trim) + ' ' + str(type(imput_trim)))

# - exit if imput_trim has no value, without msg_err
    if imput_trim:
        has_error = False

# - remove all comma's and dots
        input_no_comma = imput_trim.replace(',', '')
        input_no_dots = input_no_comma.replace('.', '')
        if logging_on:
            logger.debug('     input_no_dots: ' + str(input_no_dots) + ' ' + str(type(input_no_dots)))
# cast input_with_dots to integer
        # '', ' ' and non-numeric give InvalidOperation error
        # '1.7'   gives error: invalid literal for int() with base 10: '1.7'

        try:
            input_number = int(input_no_dots)
        except Exception as e:
            has_error = True
            if logging_on:
                logger.debug('Exception: ' + str(e))
        if logging_on:
            logger.debug('     imput_trim: ' + str(imput_trim) + ' ' + str(type(imput_trim)))
            logger.debug('     input_number: ' + str(input_number) + ' ' + str(type(input_number)))
            logger.debug('     max_score: ' + str(max_score) + ' ' + str(type(max_score)))

# - check if score is within range
        if not has_error:
            if max_score and input_number > max_score:
                has_error = True
            elif input_number < 0:
                has_error = True

        if has_error:
            input_number = None
            err_list.append(str(_("Score '%(val)s' is not allowed.") % {'val': str(input_value)}))
            if max_score:
                err_list.append(str(_("The score must be a whole number between 0 and %(max)s.") % {'max': max_score}))
            else:
                err_list.append(str(_("The score must be a whole number.")))

        input_str = str(input_number) if input_number is not None else None

    if logging_on:
        logger.debug(' >>> input_number: ' + str(input_number) + ' ' + str(type(input_number)))
        logger.debug(' >>> input_str: ' + str(input_str) + ' ' + str(type(input_str)))
        logger.debug(' >>> err_list: ' + str(err_list))

    return input_number, input_str, err_list
# --- end of get_score_from_inputscore


def get_grade_number_from_input_str(input_str):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_grade_number_from_input_str -----')
        logger.debug('input_value: ' + str(input_str) + ' ' + str(type(input_str)))

    output_str = None
    err_list = []

# - remove spaces before and after input_value
    imput_trim = input_str.strip() if input_str else ''
    if logging_on:
        logger.debug('input_trim: >' + str(imput_trim) + '< ' + str(type(imput_trim)))

# - exit if imput_trim has no value, without msg_err
    if imput_trim:
        has_error = False

# - remove all comma's and dots
        input_replaced = imput_trim.replace(',', '')
        input_replaced = input_replaced.replace('.', '')

        if logging_on:
            logger.debug('input_replaced: >' + str(input_replaced) + '< ' + str(type(input_replaced)))

# check if input without dots is integer
        input_int = 0
        try:
            input_int = int(input_replaced)
        except:
            has_error = True
        if logging_on:
            logger.debug('input_int: >' + str(input_int) + '< ' + str(type(input_int)))

# check if input >= 1 and <= 100
        if not has_error:
            if input_int < 1:
                has_error = True
            elif input_int > 100:
                has_error = True

        if not has_error:
            if input_int < 11:
                # '0.9' must give error, not '9'
                if input_replaced[0:1] == '0':
                    has_error = True
                else:
                    output_str = str(input_int) + '.0'
            elif input_int == 100:
                output_str = '10.0'
            else:
                input_str = str(input_int)
                # if input_int is between '11' en '99': put dot in the middle
                output_str = ''.join((input_str[0:1], '.', input_str[1:]))

        if has_error:
            err_list.append(str(_("Grade '%(val)s' is not allowed.") % {'val': imput_trim}))
            err_list.append(''.join((str(_('The grade must be a number between 1 and 10')), ',')))
            err_list.append(str(_('with one digit after the decimal point.')))

    if logging_on:
        logger.debug('output_str: ' + str(output_str))
        if err_list:
            logger.debug('msg_list: ' + str(err_list))

    return output_str, err_list
# - end of get_grade_number_from_input_str


def get_grade_char_from_input_str(input_str):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_grade_char_from_input_str -----')
        logger.debug('input_value: ' + str(input_str) + ' ' + str(type(input_str)))

# - set output variables
    output_str = None
    err_list = []
# - remove spaces before and after input_value
    imput_trim = input_str.strip() if input_str else ''

# - exit if imput_trim has no value, without msg_err
    if imput_trim:
        value_lc = imput_trim.lower()
        if value_lc in ('o', 'v', 'g'):
            output_str = value_lc
        else:
            err_list.append(str(_("Grade '%(val)s' is not allowed.") % {'val': value_lc}))
            err_list.append(str(_("Grade can only be 'g', 'v' or 'o'.")))

    if logging_on:
        logger.debug('output_str: ' + str(output_str))
        if err_list:
            logger.debug('msg_list: ' + str(err_list))

    return output_str, err_list
# - end of get_grade_char_from_input_str


############################## VERSION 2 of batch update  ############################### PR2024-05-14

def calc_final_grade_v2(examperiod, subj_code, gradetype, weight_se, weight_ce, no_ce_years,
                                    segrade, srgrade, pegrade, cegrade, exemption_year,
                                    sr_allowed, has_sr, has_practex):
    # was: def calc_sesr_pece_final_grade(si_dict, examperiod, has_sr, exemption_year, se_grade, sr_grade, pe_grade, ce_grade):
    # PR2021-12-28 PR2022-04-11 PR2022-05-26 PR2024-05-19
    # called by:
    # - batch_update_grade
    # - recalc_finalgrade_in_grade_and_save
    # - import_studsubj_grade_from_datalist

    """

    # - parameters of calc_final_grade_v2 are:
    #     ey.no_centralexam, si.gradetype, si.weight_se, si.weight_ce, si.ete_exam,
    #     grd.examperiod, grd.cegrade, grd.ce_score,
    #     grd.exam.scalelength, grd.exam.cesuur, grd.exam.nterm, grd.exam.published_id


    ey.no_centralexam
    ey.no_thirdperiod
    ey.no_practexam
    ey.sr_allowed
    ey.thumbrule_allowed

    si.gradetype,
    si.weight_se,
    si.weight_ce,
    si.ete_exam,
    si.has_practexam
    si.no_ce_years

    has_practex = si.has_practexam and not ey.no_practexam

    studsubj.exemption_year
    studsubj.has_exemption
    studsubj.has_sr
    studsubj.has_reex
    studsubj.has_reex03

    grd.segrade, grd.srgrade, grd.pegrade, grd.cegrade

    #  - return value is new_ce_grade
    """

    # this function does not save the calculated fields, but returns sesr_grade, pece_grade, finalgrade, delete_exemption_cegrade_without_ce

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ------- calc_final_grade_v2 -------')

    # - when second or third examperiod: get se_grade and pe_grade from first examperiod,
    # and store them in second or third examperiod
    # NOT ANYMORE: se, sr and pe grades are already stored in grade reex and reex03 when updating

    # PR2022-04-12 si.no_ce_years = '2020;2021': is a list of examyears that had no CE. This is used to skip no_input_ce when calculating exemption endgrade
    #               si.thumb_rule = True: it is allowed to set ss.is_thumbrule = True for this subject
    #             ss.is_thumbrule = True: skip this subject when calculating result, only if ss.is_thumbrule=True

    # Practical exam does not exist any more.
    # PR2024-05-18 has_practex = (NOT ey.no_practexam AND si.has_practexam)

    sesr_grade, pece_grade, finalgrade, delete_exemption_cegrade_without_ce = None, None, None, False
    try:
        if logging_on:
            logger.debug('     examperiod:       ' + str(examperiod))
            logger.debug('     subj_code:        ' + str(subj_code))
            logger.debug('     gradetype:        ' + str(gradetype))
            logger.debug('     weight_se:        ' + str(weight_se))
            logger.debug('     weight_ce:        ' + str(weight_ce))
            logger.debug('     no_ce_years:      ' + str(no_ce_years))
            logger.debug('     segrade:         ' + str(segrade) + ' ' + str(type(segrade)))
            logger.debug('     srgrade:         ' + str(srgrade) + ' ' + str(type(srgrade)))
            logger.debug('     pegrade:         ' + str(pegrade) + ' ' + str(type(pegrade)))
            logger.debug('     cegrade:         ' + str(cegrade) + ' ' + str(type(cegrade)))
            logger.debug('     exemption_year:   ' + str(exemption_year))
            logger.debug('     sr_allowed:    ' + str(sr_allowed))
            logger.debug('     has_sr:        ' + str(has_sr))
            logger.debug('     has_practex: ' + str(has_practex))

        # PR2024-05-18
        this_has_sr = sr_allowed and has_sr

# ++++  calculate finalgrade when gradetype is character
        if gradetype == c.GRADETYPE_02_CHARACTER:

    # - calculate sesr_grade
            sesr_grade, se_noinput, sr_noinput = calc_sesr_char(segrade, srgrade, this_has_sr, weight_se)

    # - calculate finalgrade
            finalgrade = calc_finalgrade_char(sesr_grade, se_noinput, sr_noinput, weight_se)

# ++++  calculate finalgrade when gradetype is number
        elif gradetype == c.GRADETYPE_01_NUMBER:

    # - calculate se_sr
            sesr_decimal, se_noinput, sr_noinput = calc_sesr_decimal(examperiod, segrade, srgrade, has_sr, weight_se)
            sesr_grade = str(sesr_decimal) if sesr_decimal else None

    # - calculate pe_ce
            # also check if no_exemption_ce
            pece_decimal, pe_noinput, ce_noinput, delete_exemption_cegrade_without_ce = \
                calc_pece_decimal(examperiod, cegrade, pegrade, weight_ce, has_practex, exemption_year, no_ce_years, subj_code)
            pece_grade = str(pece_decimal) if pece_decimal else None

    # - sesr_noinput = True if als weight_se > 0 and  se_noinput = True or sr_noinput = True
            sesr_noinput = weight_se > 0 and (se_noinput or sr_noinput)

    # - pece_noinput = True if als weight_ce > 0 and  pe_noinput = True or ce_noinput = True
            pece_noinput = weight_ce > 0 and (pe_noinput or ce_noinput)

    # - calculate finalgrade
            finalgrade = calc_final_grade_number(sesr_decimal, pece_decimal,
                                                sesr_noinput, pece_noinput,
                                                weight_se, weight_ce)

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug(' >>> sesr_grade: ' + str(sesr_grade))
        logger.debug(' >>> pece_grade: ' + str(pece_grade))
        logger.debug(' >>> finalgrade: ' + str(finalgrade))
        logger.debug(' ------- end of calc_final_grade_v2 -------')

    return sesr_grade, pece_grade, finalgrade, delete_exemption_cegrade_without_ce
# --- end of calc_final_grade_v2


def calc_max_grade_v2(max_grade_dict, calc_ep = None):
    # PR2024-05-16
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('')
        logger.debug('--------------- calc_max_grade_v2 ---------------')

    #  max_grade_dict  :
    #  {1: {'ep': 1, 'sesrgrade': '9.0', 'pecegrade': '9.7', 'finalgrade': '9', 'noinput': False,
    #  'pok_sesrgrade': '9.0', 'pok_pecegrade': '9.7', 'pok_finalgrade': '9'}}

    max_sesrgrade, max_pecegrade, max_finalgrade = None, None, None
    max_use_exem, max_noinput = False, False

    ep_list = (4, 1) if calc_ep == 1 else (4, 2, 1) if calc_ep == 2 else (4, 3, 2, 1)
    if logging_on:
        logger.debug('  ep_list  : ' + str(ep_list))

    for this_examperiod in ep_list:
        if this_examperiod in max_grade_dict:
            ep_dict = max_grade_dict[this_examperiod]

            if logging_on:
                logger.debug(' -- ep_dict: ' + str(this_examperiod) + ': ' + str(ep_dict))

            this_sesrgrade = ep_dict['sesrgrade']
            this_pecegrade = ep_dict['pecegrade']
            this_finalgrade = ep_dict['finalgrade']
            this_noinput = ep_dict['noinput']

            if this_noinput:
                get_this_grade_as_new_max = True

                if logging_on:
                    logger.debug(' > max noinput this_examperiod: ' + str(this_examperiod))
            else:

                get_this_grade_as_new_max = \
                    compare_two_grades_v2(this_sesrgrade, this_pecegrade, this_finalgrade,
                                      max_sesrgrade, max_pecegrade, max_finalgrade)

            if get_this_grade_as_new_max:
                max_sesrgrade = this_sesrgrade
                max_pecegrade = this_pecegrade
                max_finalgrade = this_finalgrade
                max_use_exem = this_examperiod == c.EXAMPERIOD_EXEMPTION

                if logging_on:
                    logger.debug('     > max has changed: max_finalgrade: ' + str(max_finalgrade))

            # first of the list of examperiods must always have value: (order of examperiods is: 4, 3, 2, 1)
            # - if student has exemption, exemption must have value
            # - if student has reex03, reex03 must have value
            # - if student has reex, reex must have value
            # - otherwise: first examperiod must have value

            # if first has no input: skip rest of the list
            if this_noinput:
                max_noinput = True
                break
# - end of for this_examperiod in ep_list
    if logging_on:
        logger.debug('   - max_sesrgrade  : ' + str(max_sesrgrade))
        logger.debug('   - max_pecegrade  : ' + str(max_pecegrade))
        logger.debug('   - max_finalgrade  : ' + str(max_finalgrade))
        logger.debug('   - max_noinput  : ' + str(max_noinput))
        logger.debug('   - max_use_exem  : ' + str(max_use_exem))
        logger.debug('--------------- end of calc_max_grade_v2 ---------------')

    return max_sesrgrade, max_pecegrade, max_finalgrade, max_noinput, max_use_exem
# - end of calc_max_grade_v2


def compare_two_grades_v2(this_sesrgrade, this_pecegrade, this_finalgrade,
                          max_sesrgrade, max_pecegrade, max_finalgrade):
    # PR2024-05-28
    # function compares two finalgrades / pecegrades / sesrgrade
    # and returns highest
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('')
        logger.debug('--------------- compare_two_grades_v2 ---------------')
        logger.debug('this_sesrgrade: ' + str(this_sesrgrade) +
                     ' this_pecegrade: ' + str(this_pecegrade) +
                     ' this_finalgrade: ' + str(this_finalgrade))
        logger.debug('max_sesrgrade: ' + str(max_sesrgrade) +
                     ' max_pecegrade: ' + str(max_pecegrade) +
                     ' max_finalgrade: ' + str(max_finalgrade))

    get_this_grade_as_new_max = False

    if max_finalgrade is None:
        if this_finalgrade is not None:
            get_this_grade_as_new_max = True
            if logging_on:
                logger.debug('     > max_finalgrade is None: get_this_grade_as_new_max = True')
        else:
            if logging_on:
                logger.debug('     > both this and max_finalgrade are None: get_this_grade_as_new_max = False')

    elif this_finalgrade is not None:
        # - both this_finalgrade and max_grade_final have value

        if this_finalgrade.isnumeric() and max_finalgrade.isnumeric():
            # calc_max_examperiod returns True when this_grade is greater than or equal to max_grade
            get_this_grade_as_new_max = calc_max_examperiod_gradetype_decimal(
                True, this_finalgrade, this_pecegrade, this_sesrgrade,
                False, max_finalgrade, max_pecegrade, max_sesrgrade)
            if logging_on:
                logger.debug('     > isnumeric new_max: get_this_grade_as_new_max = ' + str(get_this_grade_as_new_max))
        else:
            # - if final grade is ovg (sesr is same as final, pece is None)
            # calc_max_examperiod returns True when this_grade is greater than or equal to max_grade
            get_this_grade_as_new_max = calc_max_examperiod_gradetype_character(
                True, this_finalgrade,
                False, max_finalgrade)
            if logging_on:
                logger.debug('     > is character new_max: get_this_grade_as_new_max = ' + str(get_this_grade_as_new_max))

    return get_this_grade_as_new_max
# - end of calc_max_grade_v2


def calc_has_pok_v2(noinput, no_centralexam, gradetype, is_combi, weight_se, weight_ce, sesrgrade, pecegrade, finalgrade, examperiod=None):
    # PR2022-07-01 PR2024-05-03 PR2024-05-27
    # function calculates proof of knowledge
    # examperiod is only used to skip exemption. examperiod can be None

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ---------- calc_has_pok_v2 ----------')
        logger.debug('    examperiod: ' + str(examperiod) + ' no_centralexam: ' + str(no_centralexam) + ' gradetype: ' + str(gradetype))
        logger.debug('    is_combi: ' + str(is_combi) + ' weight_se: ' + str(weight_se) + ' weight_ce: ' + str(weight_ce))
        logger.debug('    sesrgrade: ' + str(sesrgrade) + ' pecegrade: ' + str(pecegrade) + ' finalgrade: ' + str(finalgrade))

    """
    PR2019-05-29 van Nancy Josefina: Inspectie
        'Landsbesluit eindexamens vwo, havo, vsbo, Artikel 1 lid o:
        'bewijs van kennis: een bewijs van een, bij een eindexamen, met goed gevolg afgelegd examen in een vak,
        'waarin ten minste een zeven als eindcijfer is behaald,
        'met dien verstande dat het cijfer van het schoolexamen en, indien van toepassing,
        'van het centraal examen van dat vak ten minste 6,0 bedraagt;

    'PR2019-11-26 ovl Nancy Josephina: voorstel om een zes bij combivakken ook vrijstelling te geven. Nog niet geaccordeerd
    'PR2020-05-20 ovl met Esther, Rubia, Nancy op 8 mei 2020: is van toepassing, vooruitlopend op vaststelling
    'Alleen voor Curacao?
    'dit filter is niet ingesteld: SXM filter: If booIsCombiOfKeuzeCombi And Not pblAfd.IsSXMschool Then

    PR2020-05-27: brief IG 17 okt 2019 aan schoolbesturen: combivakken met EC 6 en SE 5,5 krijgen vrijstelling

    PR2020-05-26 debug: bij vrijstelling werd ook bewijs van kennis afgegeven. gewijzigd in: overslaan als vrjstelling wordt gebruikt voor dit vak
    PR2020-05-27 LET OP: geslaagde kandidaten krijgen geen bewijs van kennis. BvK wordt gewist bij Kand_Verwerken: J. wis Bewijs van Kennis / Bewijs van Vrijstelling van geslaagde kandidaten
    PR2019-08-29 vraag mw Bruno New Song,  antwoord Esther:
        ' Nancy geeft aan in acht nemende artikel 14 van de onderwijswetgeving, lid 2, 6 en 7,
        ' dat bij een voldoende (dus 6) een bewijs van vrijstelling gegeven kan worden.
        ' ik: Weet Nancy zeker dat het artikel waar ze naar verwijst ook van toepassing is op de dagscholen?
        ' Esther: Ja Hans. We hadden het over dagschool. Die ene artikel geeft dat niet expliciet aan.
    dus ook een 'v' geeft bewijs van kennis:    
    """

    has_pok = False

    if noinput:
        if logging_on:
            logger.debug('  >  no input ')

# 1. geen BvK als het eindcijfer niet is ingevuld
    elif not finalgrade:
        if logging_on:
            logger.debug('  >  final_grade is empty ')

    # PR2024-05-07 function is only called when examperiod is ep1, ep2 ep3, not when exemption
    elif examperiod == c.EXAMPERIOD_EXEMPTION:
        if logging_on:
            logger.debug('  >  examperiod not in ep 1 2 3 ')
    else:
# 2b. bereken BvK als het cijfer niet is gebaseerd is op vrijstelling
        final_grade_ok, sesr_grade_ok, pece_grade_ok = False, False, False

# 3. als cijferType is VoldoendeOnvoldoende
        if gradetype == c.GRADETYPE_02_CHARACTER:

# a. Eindcijfer moet een "v" of "g" zijn.
            final_grade_ok = finalgrade and finalgrade.lower() in ('v', 'g')

            if logging_on:
                logger.debug('  >  ovg final_grade_ok: ' + str(final_grade_ok) + ' ' + str(finalgrade))

            if final_grade_ok:
# b. SE cijfer moet een "v" of "g" zijn.
                if not weight_se:
                    sesr_grade_ok = True
                elif sesrgrade and sesrgrade.lower() in ('v', 'g'):
                    sesr_grade_ok = True

# c. CE cijfer moet een "v" of "g" zijn. (crcCEweging > 0 komt niet voor)
                # 'PR2020-05-27 ovg vakken hebben geen CE, sla deze eis dus over
                pece_grade_ok = True

# 4. als cijferType is Numeric
        elif gradetype == c.GRADETYPE_01_NUMBER:

# 4a. als het een combinatievak is
            if is_combi:
    # a. Eindcijfer moet minstens een 6 zijn.
                final_grade_ok = finalgrade and Decimal(finalgrade) >= 6
                if logging_on:
                    logger.debug(
                        '  >  combinatievak final_grade_ok: ' + str(final_grade_ok) + ' ' + str(finalgrade))

                if final_grade_ok:
    # b. SE cijfer moet minstens een 5,5 zijn.
                    sesr_grade_ok = weight_se > 0 and sesrgrade and Decimal(sesrgrade) >= 5.5

    # c. CE cijfer niet van toepassing bij combinatievak.
                    pece_grade_ok = True

# 4b. als het een gewoon vak is (geen combinatievak)
            else:
    # a. Eindcijfer moet minstens een 7 zijn.
                final_grade_ok = finalgrade and Decimal(finalgrade) >= 7
                if logging_on:
                    logger.debug(
                        '  >  final_grade_ok = ' + str(final_grade_ok) + ' (' + str(finalgrade) + ')')

                if final_grade_ok:
    # b. SE cijfer moet minstens een 6,0 zijn.
                    sesr_grade_ok = weight_se > 0 and sesrgrade and Decimal(sesrgrade) >= 6
                    if logging_on:
                        logger.debug('  >  sesr_grade_ok = ' + str(sesr_grade_ok) + ' (' + str(sesrgrade)+ ')')
                    if sesr_grade_ok:
    # c. CE cijfer moet minstens een 6,0 zijn.
                        # PR2020-05-20 Corona: geen CE cijfer, sla deze eis daarom over
                        if no_centralexam:
                            pece_grade_ok = True
                        elif not weight_ce:
                            pece_grade_ok = True
                        else:
                            pece_grade_ok = pecegrade and Decimal(pecegrade) >= 6
                            if logging_on:
                                logger.debug(
                                    '  >  pece_grade_ok =  ' + str(pece_grade_ok)  + ' (' + str(pecegrade)+ ')')

# 5. bereken BewijsVanKennis
        if final_grade_ok and sesr_grade_ok and pece_grade_ok:
            has_pok = True

    if logging_on:
        logger.debug('  >  has_pok: ' + str(has_pok))

    return has_pok
# end of calc_has_pok_v2


def calc_max_pokV2(max_grade_dict):
    # PR2024-05-28
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('')
        logger.debug('--------------- calc_max_pokV2 ---------------')
        logger.debug('    max_grade_dict : ' + str(max_grade_dict))

    # Note: pok is possible if use_exemp
    # The following situation is possible:
    # - a student has an exemption with final grade 9
    # - she does exam this exam period and gets an 8
    # - AWP calculates the result based on the exemption
    #  - the student fails again
    # - because he did the exam this year, he must get a new exemption, based on final grade 8
    # - therefore calculating max_pok is not enough, because it looks at the exemption and gives pok = False
    # - solution: add pok_sesr, pok_pece and pok_final to studsubject

    get_this_grade_as_new_max = False

    max_pok_sesr, max_pok_pece, max_pok_final = None, None, None
    max_use_exem, max_noinput = False, False

    for this_examperiod in ( 3, 2, 1):
        if this_examperiod in max_grade_dict:
            ep_dict = max_grade_dict[this_examperiod]

            if logging_on:
                logger.debug(' -- ep_dict: ' + str(this_examperiod) + ': ' + str(ep_dict))

    # skip when ep has no input or no pok
            if not ep_dict['noinput'] and ep_dict['has_pok']:

                this_sesrgrade = ep_dict['sesrgrade']
                this_pecegrade = ep_dict['pecegrade']
                this_finalgrade = ep_dict['finalgrade']

                get_this_grade_as_new_max = \
                    compare_two_grades_v2(this_sesrgrade, this_pecegrade, this_finalgrade,
                                          max_pok_sesr, max_pok_pece, max_pok_final)

                if get_this_grade_as_new_max:
                    max_pok_sesr = this_sesrgrade
                    max_pok_pece = this_pecegrade
                    max_pok_final = this_finalgrade

                    if logging_on:
                        logger.debug('     > max has changed: new max_pok_final ' + str(max_pok_final))
# - end of for this_examperiod in ep_list

    if logging_on:
        logger.debug('   - max_pok_sesr  : ' + str(max_pok_sesr))
        logger.debug('   - max_pok_pece  : ' + str(max_pok_pece))
        logger.debug('   - max_pok_final  : ' + str(max_pok_final))
        logger.debug('--------------- end of calc_max_pokV2 ---------------')
    return max_pok_sesr, max_pok_pece, max_pok_final
# - end of calc_max_pokV2


def calc_noinputV2(examperiod,sr_allowed, has_sr, has_practex, subj_code,
                   weight_se, weight_ce, exemption_year, no_ce_years,
                   segrade, srgrade, pegrade, cegrade, ni_list = None, noin_dict= None):

    # PR2021-11-21 PR2021-12-27 PR2022-01-05 PR2024-05-16
    # only called by calc_studsubj_result

    # from AWP Calculation.CalcEindcijfer_CijferOvg
    # function checks if this grade should have input, if so: add '-noinput' to grade_dict
    # Note: this function is only called when grade has no value
    # takes in account that in 2020 there was no central exam

    # only if noin_dict is not None:
    #   when noinput: mapped_key is appended to noin_dict with value: subj_code
    #                 key_str is appended to ni_list

    # note: combi subject can have weight_ce = 1. In that case it gives 'no input' when CE not entered.
    # let it stay, so combi with ce can be possible

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('---------  calc_noinputV2  --------- ')
        logger.debug('   examperiod: ' + str(examperiod))
        logger.debug('   segrade: ' + str(segrade))
        logger.debug('   cegrade: ' + str(cegrade))

    # don't skip calc noinput when is_extra_nocount
    # put se, sr, pe from first period also in reex and reex03

# - get grade info from this_examperiod_dict
    examtype_tuple = ('segrade', 'cegrade') if examperiod == c.EXAMPERIOD_EXEMPTION else \
                     ('segrade', 'srgrade', 'pegrade', 'cegrade')

    this_ep_has_noinput = False

# - get sr only if has_sr, practexam if has_practex
    # PR2024-05-18 has_practex = (NOT ey.no_practexam AND si.has_practexam)

    for key_str in examtype_tuple:

        if (key_str == 'srgrade' and sr_allowed and has_sr) or \
                (key_str == 'pegrade' and has_practex) or \
                (key_str in ('segrade', 'cegrade')):

            # PR2022-01-05 se, sr, pe grades are also stored in reexand reex03
            grade = segrade if key_str == 'segrade' else \
                cegrade if key_str == 'cegrade' else \
                srgrade if key_str == 'srgrade' else \
                pegrade if key_str == 'pegrade' else \
                '---'

            if logging_on:
                logger.debug('   grade ' + key_str + ': >' + str(grade) + '<')

            has_no_input = False

            if grade is None:

                if logging_on:
                    logger.debug('   weight_se: ' + str(weight_se))
                    logger.debug('   weight_ce: ' + str(weight_ce))

                if key_str in ('segrade', 'srgrade'):
                    if weight_se > 0:
                        has_no_input = True
                elif key_str == 'pegrade':
                    if weight_ce > 0:
                        has_no_input = True
                elif key_str == 'cegrade':
                    if weight_ce > 0:
                        if examperiod == c.EXAMPERIOD_EXEMPTION:
                            # CORONA: in 2020 there was no central exam, therefore:
                            #         in 2021: for certain subjects no central exam
                            # table 'schemeitem' contains field 'no_ce_years' with string with years without ce: "2020;2021"
                            # table 'studsubj' contains field 'exemption_year' with year of the exemption

                            # skip 'no_input' if exemption has no ce PR2022-05-26

                            exemp_no_ce = calc_exemp_noceV2(exemption_year, no_ce_years)
                            if not exemp_no_ce:
                                has_no_input = True
                        else:
                            has_no_input = True

            if logging_on:
                logger.debug(' >>> has_no_input: ' + str(has_no_input))

            if has_no_input:
                this_ep_has_noinput = True

                if noin_dict is not None:
                    mapped_key_str = '-'
                    if key_str == 'segrade':
                        mapped_key_str = 'SE'
                    elif key_str == 'srgrade':
                        mapped_key_str = 'SR'
                    elif key_str == 'pegrade':
                        mapped_key_str = 'PE'
                    elif key_str == 'cegrade':
                        if examperiod == c.EXAMPERIOD_THIRD:
                            mapped_key_str = 'h3'
                        elif examperiod == c.EXAMPERIOD_SECOND:
                            mapped_key_str = 'h2'
                        else:
                            mapped_key_str = 'CE'

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

                        if mapped_key_str not in noin_dict:
                            noin_dict[mapped_key_str] = []

                        if subj_code not in noin_dict[mapped_key_str]:
                            noin_dict[mapped_key_str].append(subj_code)
                    if logging_on:
                        logger.debug('   noin_dict: ' + str(noin_dict))

                if ni_list is not None:
                    ni_list.append(key_str)
                # or: mapped_key_str??
                # ni_list.append(mapped_key_str)

                    if logging_on:
                        logger.debug('   ni_list: ' + str(ni_list))
    if logging_on:
        logger.debug(' this_ep_has_noinput: ' + str(this_ep_has_noinput))
        logger.debug('---------  end of calc_noinputV2  --------- ')
    return this_ep_has_noinput
# - end of calc_noinputV2


def calc_exemp_noceV2(exemption_year, no_ce_years):
    #PR2024-05-16
# PR2022-05-26 calculate if exemption has ce
    # PR2022-05-26:
    # in studsubj field 'exemption_year' contains the examyear of the exemption
    # the schemeitem field 'no_ce_years' contains string with examyears without CE, i.e. '2020;2021'
    # if exemption_year is in no_ce_years: no_ce_exam = True

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------  calc_exemp_noce  ----------')


    if logging_on:
        logger.debug('    exemption_year: ' + str(exemption_year))
        logger.debug('    no_ce_years: ' + str(no_ce_years))

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


def calc_max_examperiod_gradetype_decimal(examperiod_A, finalgrade_A, pece_A, sesr_A, examperiod_B, finalgrade_B, pece_B, sesr_B):
    # PR2021-11-21 from AWP Function Calculations.EindcijferTvMax
    # Function returns examperiod with the highest grade, returns A when grades are the same or not entered
    # when the final grades are the same, it returns te examperiod with the highest pece grade
    # PR2022-07-06 sesr added, to compare when weighing_ce = 0
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug( '  -----  calc_max_examperiod_gradetype_decimal  -----')
        logger.debug('..... examperiod_A: ' + str(examperiod_A))
        logger.debug('..... finalgrade_A: ' + str(finalgrade_A) + ' ' + str(type(finalgrade_A)))
        logger.debug('..... pece_A: ' + str(pece_A) + ' ' + str(type(pece_A)))
        logger.debug('..... sesr_A: ' + str(sesr_A) + ' ' + str(type(sesr_A)))
        logger.debug('..... examperiod_B: ' + str(examperiod_B) )
        logger.debug('..... finalgrade_B: ' + str(finalgrade_B) + ' ' + str(type(finalgrade_B)))
        logger.debug('..... pece_B: ' + str(pece_B) + ' ' + str(type(pece_B)))
        logger.debug('..... sesr_B: ' + str(sesr_B) + ' ' + str(type(sesr_B)))

    final_A_dot_nz = finalgrade_A.replace(',', '.') if finalgrade_A else "0"
    final_decimal_A =  Decimal(final_A_dot_nz)

    final_B_dot_nz =  finalgrade_B.replace(',', '.') if finalgrade_B else "0"
    final_decimal_B =  Decimal(final_B_dot_nz)

    if logging_on:
        logger.debug('..... final_decimal_A: ' + str(final_decimal_A) + ' ' + str(type(final_decimal_A)))
        logger.debug('..... final_decimal_B: ' + str(final_decimal_B) + ' ' + str(type(final_decimal_B)))

    max_examperiod = examperiod_A
    # from https://www.geeksforgeeks.org/python-decimal-compare-method/

# - compare final grades
    compare_final = final_decimal_B.compare(final_decimal_A)

    if compare_final == 1:  # b.compare(a) == 1 means b > a
        max_examperiod = examperiod_B
    elif compare_final == -1:  # b.compare(a) == -1 means b < a
        pass  # max_examperiod = examperiod_A

# - if final grades as the same: compare pece grades
    elif compare_final == 0:  # # b.compare(a) == 0 means b = a
        pece_A_dot_nz = pece_A.replace(',', '.') if pece_A else "0"
        pece_decimal_A = Decimal(pece_A_dot_nz)

        pece_B_dot_nz = pece_B.replace(',', '.') if pece_B else "0"
        pece_decimal_B = Decimal(pece_B_dot_nz)

        compare_pece = pece_decimal_B.compare(pece_decimal_A)
        if compare_pece == 1:  # b.compare(a) == 1 means b > a
            max_examperiod = examperiod_B

        elif compare_pece == -1:  # b.compare(a) == -1 means b < a
            pass  # max_examperiod = examperiod_A

# - if pece grades as the same: compare sesr grades
        elif compare_pece == 0:  # # b.compare(a) == 0 means b = a
            sesr_A_dot_nz = sesr_A.replace(',', '.') if sesr_A else "0"
            sesr_decimal_A = Decimal(sesr_A_dot_nz)

            sesr_B_dot_nz = sesr_B.replace(',', '.') if sesr_B else "0"
            sesr_decimal_B = Decimal(sesr_B_dot_nz)

            compare_sesr = sesr_decimal_B.compare(sesr_decimal_A)
            if compare_sesr == 1:  # b.compare(a) == 1 means b > a
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





############################## END OF VERSION 2 of batch update  ############################### PR2024-05-14


##################

def batch_update_finalgrade_v2(req_user, grade_pk_list=None, student_pk_list=None, schemeitem_pk_list=None, ce_exam_pk=None):
    #PR2022-05-25 PR2022-06-03 PR2024-06-01
    # called by calc_cegrade_from_exam_score and CalcResultsView

#++++++++ this is the one that works +++++++++++++++++++++ PR2022-05-29
    # function calculates cegrade from score, or gets cegrade from row when exemption (was: or secret_exam)
    # - calculates sesrgrade, pecegrade and final grade
    # - and puts it in returnvalue updated_cegrade_list

    # note: scores of secret_exam are also entered, not grades

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- batch_update_finalgrade_v2 -----')
        logger.debug('     ce_exam_pk:    ' + str(ce_exam_pk))
        logger.debug('     grade_pk_list:    ' + str(grade_pk_list))
        logger.debug('     student_pk_list:    ' + str(student_pk_list))

    def where_clause(field_name, pk_list):
        sql_clause = ''
        if pk_list:
            if len(pk_list) == 1:
                sql_clause = ''.join(("AND ", field_name, "=", str(pk_list[0]), "::INT"))
            else:
                sql_clause = ''.join(("AND ", field_name, " IN (SELECT UNNEST(ARRAY", str(pk_list), "::INT[]))"))
        return sql_clause

    def get_sql_value_str(value):
        return ''.join(("'", str(value), "'")) if value else 'NULL'

    updated_cegrade_list = []
    updated_student_pk_list = []

    # PR2024-05-19
    # exam_instance only has value when called by update_exam_instance
    # when exam_instance has value: only return grades with this exam,
    # therefore use INNER JOIN instead of LEFT JOIN in sub_sql and sql
    inner_or_left_join = 'INNER JOIN' if ce_exam_pk is not None else 'LEFT JOIN'

# - get rows of all grades that must be calculated
    # retrieve id and fields necessary to calculate final grade
    sql_list = [
        "SELECT grd.id, grd.examperiod, grd.segrade, grd.srgrade, grd.pescore, grd.cescore, grd.pegrade, grd.cegrade, ",
        "grd.ce_published_id, ",

        "studsubj.student_id, studsubj.schemeitem_id, studsubj.has_sr, studsubj.has_exemption, studsubj.exemption_year, ",
        "subjbase.code AS subj_code, ",
        "ce_exam.ete_exam, ce_exam.secret_exam, ce_exam.scalelength, ce_exam.cesuur, ce_exam.nterm, ",
        "ce_exam.published_id AS ce_exam_published_id, ",

        "ey.no_centralexam, ey.no_thirdperiod,",
        "(ey.sr_allowed AND si.sr_allowed) AS sr_allowed,",
        "(NOT ey.no_practexam AND si.has_practexam) AS has_practex,",

        "si.gradetype, si.weight_se, si.weight_ce, si.is_combi, si.no_ce_years, si.ete_exam",

        "FROM students_grade AS grd",
        "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

        "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
        "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",

        # "INNER JOIN schools_school AS school ON (school.id = st.school_id)",
        # "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
        # "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",

        inner_or_left_join, "subjects_exam AS ce_exam ON (ce_exam.id = grd.ce_exam_id)",

        "WHERE NOT grd.deleted AND NOT grd.tobedeleted",
        "AND NOT studsubj.deleted AND NOT studsubj.tobedeleted ",
        "AND NOT stud.deleted AND NOT stud.tobedeleted ",
    ]
    if ce_exam_pk is not None:
        sql_list.append(where_clause('ce_exam.id', [ce_exam_pk]))
    elif schemeitem_pk_list:
        # PR2024-05-27 schemeitem_pk_list has value when schemeitems are changed
        sql_list.append(where_clause('si.id', schemeitem_pk_list))
    elif student_pk_list:
        sql_list.append(where_clause('stud.id', student_pk_list))
    elif grade_pk_list:
        sql_list.append(where_clause('grd.id', grade_pk_list))

    sql = ' '.join(sql_list)

    if logging_on and False:
        for sql_txt in sql_list:
            logger.debug('     > ' + str(sql_txt))

    with connection.cursor() as cursor:
        cursor.execute(sql)
        rows = af.dictfetchall(cursor)

    if logging_on and False:
        for cq in connection.queries:
            logger.debug('query: ' + str(cq))

    if rows:
        try:
            # do not change modby in grade and sstudsubj table, it will give user of admin, but do store it in log table
            # to do: write as modifiedat = %(modat)s::TIMESTAMP, dont know how to do it yet
            # modifiedat_str = str(timezone.now())
            # sql_keys = {'modby_id': request.user.pk}

            sql_value_list = []

            for row in rows:
                if logging_on and False:
                    logger.debug('     row:    ' + str(row))

                grade_id_str = str(row['id'])

    # updated_student_pk_list is used to calculate passedfailed of students with updates grades
                student_id = row['student_id']
                if student_id not in updated_student_pk_list:
                    updated_student_pk_list.append(student_id)

    # - calc ce_grade from score, or get from row when exemption (was: or secret_exam)
                new_ce_grade = calc_score.calc_grade_from_score_v2(
                    examperiod=row['examperiod'],
                    no_centralexam=row['no_centralexam'],

                    weight_ce=row['weight_ce'],
                    cegrade=row['cegrade'],
                    cescore=row['cescore'],
                    ete_exam=row['ete_exam'],

                    scalelength=row['scalelength'],
                    cesuur=row['cesuur'],
                    nterm=row['nterm'],
                    exam_published_id=row['ce_exam_published_id']
                )

    # - calc sesrgrade pecegrade and final grade
                sesr_grade, pece_grade, finalgrade, delete_exemption_cegrade_without_ce = \
                    calc_final_grade_v2(
                        examperiod=row['examperiod'],
                        subj_code=row['subj_code'],
                        gradetype=row['gradetype'],
                        weight_se=row['weight_se'],
                        weight_ce=row['weight_ce'],
                        no_ce_years=row['no_ce_years'],

                        segrade=row['segrade'],
                        srgrade=row['srgrade'],
                        pegrade=row['pegrade'],
                        cegrade=new_ce_grade,

                        exemption_year=row['exemption_year'],
                        sr_allowed=row['sr_allowed'],
                        has_sr=row['has_sr'],
                        has_practex=row['has_practex']
                    )

                if logging_on:
                    logger.debug('     new_ce_grade:    ' + str(new_ce_grade))
                    logger.debug('     sesr_grade:    ' + str(sesr_grade))
                    logger.debug('     pece_grade:    ' + str(pece_grade))
                    logger.debug('     finalgrade:    ' + str(finalgrade))

# - put grades in TEMP TABLE gr_update
                sql_value_list.append(''.join((
                    "(", grade_id_str, ", ",
                    get_sql_value_str(sesr_grade), ", ",
                    get_sql_value_str(new_ce_grade), ", ",
                    get_sql_value_str(pece_grade), ", ",
                    get_sql_value_str(finalgrade), ")"
                )))
# - end of loop
            sql_value_str = ', '.join(sql_value_list)
            sql_update = ''.join((
                "DROP TABLE IF EXISTS gr_update; CREATE TEMP TABLE gr_update (",
               "grade_id, sesrgrade, cegrade, pecegrade, finalgrade) AS VALUES ",
                "(0::INT, '-'::TEXT, '-'::TEXT, '-'::TEXT, '-'::TEXT), ",
                sql_value_str,
                "; UPDATE students_grade AS gr ",
                "SET sesrgrade = gr_update.sesrgrade, cegrade = gr_update.cegrade, ",
                "pecegrade = gr_update.pecegrade, finalgrade = gr_update.finalgrade ",
                #"modifiedby_id = %(modby_id)s::INT, modifiedat = '", modifiedat_str, "'",
                "FROM gr_update ",
                "WHERE gr_update.grade_id = gr.id ",
                "RETURNING gr.id;"
                ))

            if logging_on:
                logger.debug('     sql_update:    ' + str(sql_update))

            with connection.cursor() as cursor:
                cursor.execute(sql_update)
                updated_rows = cursor.fetchall()

            if updated_rows:
                for updated_row in updated_rows:
                    updated_cegrade_list.append(updated_row[0])
                    if logging_on:
                        logger.debug('  updated_cegrade_list updated_row:    ' + str(updated_row))

            if updated_cegrade_list:
                awpr_logs.copytolog_grade_v2(
                    grade_pk_list=grade_pk_list,
                    req_mode='b',
                    modifiedby_id=req_user.pk
                )

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug(' >>> updated_cegrade_list:    ' + str(updated_cegrade_list))

    return updated_cegrade_list, updated_student_pk_list
# end of batch_update_finalgrade_v2


####################


def batch_recalc_update_studsubj_grade_v2(request, studsubj_pk_list= None, schemeitem_pk_list = None, ce_exam_pk = None):
    # PR2024-05-10 PR2024-05-19 PR2024-05-27
    # in grades: recalc grades from score, final_grade
    # in studsubj: recalc pok
    # TODO: recalc gl_final etc.
    # - count number of reex of each student
    # - get list of studsubj_id that have reex

    # PR2024-05-19
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('')
        logger.debug('--------------- batch_recalc_update_studsubj_grade_v2 ---------------')
        logger.debug('    studsubj_pk_list: ' + str(studsubj_pk_list))
        logger.debug('    schemeitem_pk_list: ' + str(schemeitem_pk_list))
        logger.debug('    ce_exam_pk: ' + str(ce_exam_pk))

    def get_gradedict_from_row(rw, idx):
        # PR2024-05-12
        return {
            'studsubj_pk': rw['id'],
            'subj_code': rw['subj_code'],  # for log info only

            'grade_pk': rw['grd_id_arr'][idx],
            'examperiod': rw['examperiod_arr'][idx],
            'cescore': rw['cescore_arr'][idx],

            'segrade': rw['segrade_arr'][idx],
            'srgrade': rw['srgrade_arr'][idx],
            'sesrgrade': rw['sesrgrade_arr'][idx],

            'pegrade': rw['pegrade_arr'][idx],
            'cegrade': rw['cegrade_arr'][idx],
            'pecegrade': rw['pecegrade_arr'][idx],

            'finalgrade': rw['finalgrade_arr'][idx],

            'ce_published_id': rw['grd_ce_published_id_arr'][idx],

            'scalelength': rw['exam_scalelength_arr'][idx],
            'cesuur': rw['exam_cesuur_arr'][idx],
            'nterm': rw['exam_nterm_arr'][idx],
            'published_id': rw['exam_published_id_arr'][idx]
        }
    # - end of get_gradedict_from_row

    def sql_update_dict(tobe_updated_sql_dict, examperiod, table, pk_int, field, value):
        # PR2024-05-15
        if value is None:
            value_nz = 'NULL'
        elif isinstance(value, str):
            value_nz =  ''.join(("'", value, "'"))
        elif isinstance(value, int):
            value_nz = str(value)
        elif isinstance(value, bool):
            value_nz = 'TRUE' if value else 'FALSE'
        else:
            value_nz = None

        if value_nz:
            if table not in tobe_updated_sql_dict:
                tobe_updated_sql_dict[table] = {}
            tobe_updated_table = tobe_updated_sql_dict[table]

            if pk_int not in tobe_updated_table:
                tobe_updated_table[pk_int] = {'examperiod': examperiod, 'fields': {}}

            tobe_updated_fields = tobe_updated_table[pk_int]['fields']

            tobe_updated_fields[field] = value_nz
    # end of sql_update_dict

    def update_sql():

        if tobe_updated_sql_dict:
            if logging_on:
                logger.debug(' ----- update_sql ----- ')
                logger.debug('    tobe_updated_sql_dict: ' + str(tobe_updated_sql_dict))

            try:
                # tobe_updated_sql_dict: {'grade': {95439: {'cegrade': "'7.3'"}}}
                #  tobe_updated_sql_dict: {
                #       'grade': {
                #           95439: {
                #               'fields': {'cegrade': "'4.0'", 'sesrgrade': "'5.3'", 'pecegrade': "'4.0'", 'finalgrade': "'5'"},
                #               'ppk': 88012
                #   }}}

                tobe_updated_sql_list = []

                for table, table_dict in tobe_updated_sql_dict.items():
                    if logging_on:
                        logger.debug('    table: ' + str(table))

                    table_name = 'students_grade' if table == 'grade' else 'students_studentsubject' if table == 'studsubj' else None
                    if table_name:
                        # create update sql for each pk
                        for pk_int, grade_dict in table_dict.items():
                            if logging_on:
                                logger.debug('    grade_dict: ' + str(grade_dict))

                            update_sqllist = []

                        # create sql for each pk in table
                            field_dict = grade_dict['fields']
                            if logging_on:
                                logger.debug('        field_dict: ' + str(field_dict))

                            for fieldname, value in field_dict.items():
                                if logging_on:
                                    logger.debug('            fieldname: ' + str(fieldname) + ' value: ' + str(value))

                                update_sqllist.append('='.join((fieldname, value)))

                            if update_sqllist:
                                tobe_updated_sql_list.append(
                                    ''.join((
                                        "UPDATE ", table_name, " SET ",
                                        ', '.join(update_sqllist),
                                        " WHERE id=", str(pk_int), "::INT;"
                                    ))
                                )

                if tobe_updated_sql_list:
                    #tobe_updated_sql_list.insert(0, "BEGIN; ")
                    #tobe_updated_sql_list.append("COMMIT;")

                    if logging_on:
                        logger.debug('    tobe_updated_sql_list ')
                        for row in tobe_updated_sql_list:
                            logger.debug('         ' + str(row))

                    sql = ' '.join(tobe_updated_sql_list)
                    with connection.cursor() as cursor:
                        for sql_line in tobe_updated_sql_list:
                            logger.debug('    sql_line: ' + str(sql_line))
                            try:
                                cursor.execute(sql)
                            except Exception as e:
                                logger.error(getattr(e, 'message', str(e)))

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

            if logging_on:
                logger.debug('  ---- updated_grade_pk_list: ' + str(updated_grade_pk_list))
                logger.debug('  ---- updated_studsubj_pk_list: ' + str(updated_studsubj_pk_list))
    # - end of update_sql

    def insert_to_log_sql():

        if tobe_updated_sql_dict:
            if logging_on:
                logger.debug(' ----- insert_to_log_sql ----- ')
                logger.debug('    tobe_updated_sql_dict: ' + str(tobe_updated_sql_dict))

            try:
                # tobe_updated_sql_dict: {'grade': {95439: {'cegrade': "'7.3'"}}}
                #  tobe_updated_sql_dict: {
                #       'grade': {
                #           95439: {
                #               'fields': {'cegrade': "'4.0'", 'sesrgrade': "'5.3'", 'pecegrade': "'4.0'", 'finalgrade': "'5'"},
                #               'ppk': 88012
                #               }}}

                tobe_inserted_sql_list = []
                for table, table_dict in tobe_updated_sql_dict.items():

                    log_table_name = 'students_gradelog' if table == 'grade' else 'students_studentsubjectlog' if table == 'studsubj' else 'x'
                    log_id_field = 'grade_id' if table == 'grade' else 'studentsubject_id' if table == 'studsubj' else None
                    if log_table_name:

            # create insert sql for each pk
                        for pk_int, grade_dict in table_dict.items():
                            if logging_on:
                                logger.debug('    grade_dict: ' + str(grade_dict))

                            field_dict = grade_dict['fields']
                            examperiod = grade_dict['examperiod']

                            insert_fieldlist = []
                            insert_valuelist = []
                            for fieldname, value in field_dict.items():
                                insert_fieldlist.append(fieldname)
                                insert_valuelist.append(value)

                            if insert_fieldlist:

                                insert_fieldlist.extend((log_id_field, 'mode', 'modifiedat', 'modifiedby_id'))
                                insert_valuelist.extend((
                                    str(pk_int),
                                    "'b'",
                                    ''.join(("'", str(timezone.now()), "'")),
                                    str(request.user.pk)
                                ))

                                if table == 'grade':
                                    insert_fieldlist.append('examperiod')
                                    insert_valuelist.append(str(examperiod))

                                #PR2024-06-28 Sentry error: null value in column "gradelist_use_exem" violates not-null const
                                # TODO: make field nullable, remove this temporary code:
                                if table == 'studsubj':
                                    if 'gradelist_use_exem' not in insert_fieldlist:
                                        insert_fieldlist.append('gradelist_use_exem')

                                tobe_inserted_sql_list.append(''.join((
                                    "INSERT INTO ", log_table_name, " (",
                                    ', '.join(insert_fieldlist),
                                    ") VALUES (",
                                    ', '.join(insert_valuelist),
                                    ");"
                                )))

                if tobe_inserted_sql_list:
                    #tobe_inserted_sql_list.insert(0, "BEGIN; ")
                    #tobe_inserted_sql_list.append("COMMIT;")

                    if logging_on:
                        logger.debug('    tobe_inserted_sql_list ')
                        for row in tobe_inserted_sql_list:
                            logger.debug('         ' + str(row))

                    sql = ' '.join(tobe_inserted_sql_list)
                    with connection.cursor() as cursor:
                        cursor.execute(sql)

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
    # - end of insert_to_log_sql

    # PR2024-05-19
    # exam_instance only has value when called by update_exam_instance
    # when exam_instance has value: only return grades with this exam,
    # therefore use INNER JOIN instead of LEFT JOIN in sub_sql and sql

    inner_or_left_join = 'INNER JOIN' if ce_exam_pk is not None else 'LEFT JOIN'
    ce_exam_clause = ''.join(("AND grd.ce_exam_id=", str(ce_exam_pk), "::INT")) if ce_exam_pk is not None else ''

    sub_sql = ' '.join((
        "SELECT grd.studentsubject_id,",

        "ARRAY_AGG(grd.id ORDER BY grd.id) AS grd_id_arr,",
        "ARRAY_AGG(grd.examperiod ORDER BY grd.id) AS examperiod_arr,",

        "ARRAY_AGG(grd.cescore ORDER BY grd.id) AS cescore_arr,",

        "ARRAY_AGG(grd.segrade ORDER BY grd.id) AS segrade_arr,",
        "ARRAY_AGG(grd.srgrade ORDER BY grd.id) AS srgrade_arr,",
        "ARRAY_AGG(grd.sesrgrade ORDER BY grd.id) AS sesrgrade_arr,",

        "ARRAY_AGG(grd.pegrade ORDER BY grd.id) AS pegrade_arr,",
        "ARRAY_AGG(grd.cegrade ORDER BY grd.id) AS cegrade_arr,",
        "ARRAY_AGG(grd.pecegrade ORDER BY grd.id) AS pecegrade_arr,",

        "ARRAY_AGG(grd.finalgrade ORDER BY grd.id) AS finalgrade_arr,",
        "ARRAY_AGG(grd.ce_published_id ORDER BY grd.id) AS grd_ce_published_id_arr,",

        "ARRAY_AGG(exam.scalelength ORDER BY grd.id) AS exam_scalelength_arr,",
        "ARRAY_AGG(exam.cesuur ORDER BY grd.id) AS exam_cesuur_arr,",
        "ARRAY_AGG(exam.nterm ORDER BY grd.id) AS exam_nterm_arr,",
        "ARRAY_AGG(exam.published_id ORDER BY grd.id) AS exam_published_id_arr",

        "FROM students_grade AS grd",
        #"INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
        #"INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        #"INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",

        inner_or_left_join, "subjects_exam AS exam ON (exam.id = grd.ce_exam_id)",

        #"INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
        #"LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",
        #"LEFT JOIN subjects_sector AS sct ON (sct.id = stud.sector_id)",

        #"INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
        #"INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
        #"INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",

        "WHERE NOT grd.deleted AND NOT grd.tobedeleted",
        ce_exam_clause,
        "GROUP BY grd.studentsubject_id"
    ))
    sql_list = [
        "WITH grd_arr AS (", sub_sql, ")",
        "SELECT studsubj.id,",

        "subjbase.code AS subj_code,",

        "studsubj.exemption_year,",
        "studsubj.has_sr,",

        "studsubj.gradelist_sesrgrade, studsubj.gradelist_pecegrade,",
        "studsubj.gradelist_finalgrade, studsubj.gradelist_use_exem,",

        # PR2024-05-31 TODO gl_noinput is not declared in model yet
        #   "studsubj.gl_noinput, studsubj.gl_examperiod,",
        "studsubj.gl_examperiod,",

        "studsubj.pok_sesr, studsubj.pok_pece, studsubj.pok_final,",

        "ey.no_centralexam,",
        "ey.no_thirdperiod,",

        "si.gradetype,",
        "si.weight_se, si.weight_ce,",
        "si.is_combi,",
        "(ey.sr_allowed AND si.sr_allowed) AS sr_allowed,",
        "(NOT ey.no_practexam AND si.has_practexam) AS has_practex,",

        "si.no_ce_years,",
        "si.ete_exam,",

        "grd_arr.grd_id_arr,",
        "grd_arr.examperiod_arr,",

        "grd_arr.cescore_arr,",
        "grd_arr.segrade_arr,",
        "grd_arr.srgrade_arr,",
        "grd_arr.sesrgrade_arr,",
        "grd_arr.pegrade_arr,",
        "grd_arr.cegrade_arr,",
        "grd_arr.pecegrade_arr,",
        "grd_arr.finalgrade_arr,",

        "grd_arr.grd_ce_published_id_arr,",

        "grd_arr.exam_scalelength_arr,",
        "grd_arr.exam_cesuur_arr,",
        "grd_arr.exam_nterm_arr,",
        "grd_arr.exam_published_id_arr",

        "FROM students_studentsubject AS studsubj ",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

        "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
        # "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",
        # "LEFT JOIN subjects_sector AS sct ON (sct.id = st.sector_id)",
        "INNER JOIN schools_school AS school ON (school.id = st.school_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
        # "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",

        inner_or_left_join, "grd_arr ON (grd_arr.studentsubject_id = studsubj.id)",

        "WHERE NOT studsubj.deleted AND NOT studsubj.tobedeleted",
        "AND NOT st.deleted AND NOT st.tobedeleted"
    ]
    if ce_exam_pk is not None:
        # skip other filters when exam has changed
        # filter is already set with ce_exam_clause
        pass
    # PR2024-05-27 schemeitem_pk_list has value when schemeitems are changed
    elif schemeitem_pk_list:
        if len(schemeitem_pk_list) == 1:
            sql_list.append(''.join(("AND si.id=", str(schemeitem_pk_list[0]), "::INT;")))
        else:
            sql_list.append(''.join(("AND si.id IN (SELECT UNNEST(ARRAY", str(schemeitem_pk_list), "::INT[]))")))

    elif studsubj_pk_list:
        if len(studsubj_pk_list) == 1:
            sql_list.append(''.join(("AND studsubj.id=", str(studsubj_pk_list[0]), "::INT;")))
        else:
            sql_list.append(''.join(("AND studsubj.id IN (SELECT UNNEST(ARRAY", str(studsubj_pk_list), "::INT[]))")))

    sql = ' '.join(sql_list)

    if logging_on and False:
        for sql_txt in sql_list:
            logger.debug('    > ' + str(sql_txt))

    tobe_updated_sql_dict = {}
    updated_grade_pk_list = []
    updated_studsubj_pk_list = []

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            studsubj_rows = af.dictfetchall(cursor)
            if logging_on:
                logger.debug('++++++++ loop through studsubjects len: ' + str(len(studsubj_rows)))

# +++++ loop through studsubjects +++++++++++++++++++++++++++++++++++++++++++++++++++++++
        for row in studsubj_rows:

            if logging_on:
                logger.debug('  row: ' + str(row))

            examperiod = None

            old_pok_sesr = row['pok_sesr']
            old_pok_pece = row['pok_pece']
            old_pok_final = row['pok_final']

            max_grade_dict = {}
            max_pok_dict = {'sesr': None, 'pece': None, 'final': None}

            ni_list = []
            noin_dict = {}

            if logging_on:
                logger.debug('......... loop through grades of this studsubj: ' + str(row['subj_code']))

# ===== loop through examperiods / grades of this studsubj ======================================
            for index, grade_pk in enumerate(row['grd_id_arr']):
                grade_dict = get_gradedict_from_row(row, index)
                examperiod = grade_dict['examperiod']

                if examperiod not in max_grade_dict:
                    max_grade_dict[examperiod] = {}

                max_grade_ep_dict = max_grade_dict[examperiod]

                if logging_on:
                    logger.debug(' ')
                    logger.debug('  -------------  examperiod: ' + str(examperiod))
                    logger.debug('  grade_dict: ' + str(grade_dict))

# --- calc grade from score
                new_ce_grade = calc_score.calc_grade_from_score_v2(
                    examperiod=examperiod,
                    no_centralexam=row['no_centralexam'],
                    weight_ce=row['weight_ce'],
                    ete_exam=row['ete_exam'],

                    scalelength=grade_dict['scalelength'],
                    cesuur=grade_dict['cesuur'],
                    nterm=grade_dict['nterm'],
                    exam_published_id=grade_dict['published_id'],  # = exam_published_id

                    cescore=grade_dict['cescore'],
                    cegrade=grade_dict['cegrade']
                )
                if logging_on:
                    logger.debug('  ----- new_ce_grade: ' + str(grade_dict['cegrade']) + '  >   ' + str(new_ce_grade))

                if new_ce_grade != grade_dict['cegrade']:

    # - IMPORTANT must put back new_ce_grade in grade_dict, to calc finalgrade with new cegrade
                    grade_dict['cegrade'] = new_ce_grade

    # - add new cegrade to sql_update_dict
                    sql_update_dict(tobe_updated_sql_dict, examperiod,'grade', grade_pk,'cegrade', new_ce_grade)

                    if grade_pk not in updated_grade_pk_list:
                        updated_grade_pk_list.append(grade_pk)

# --- calc final grade
                new_sesrgrade, new_pecegrade, new_finalgrade, delete_exemption_cegrade_without_ce = \
                    calc_final_grade_v2(
                        examperiod=examperiod,
                        subj_code=grade_dict['subj_code'],
                        gradetype=row['gradetype'],
                        weight_se=row['weight_se'],
                        weight_ce=row['weight_ce'],
                        exemption_year=row['exemption_year'],
                        no_ce_years=row['no_ce_years'],
                        has_practex=row['has_practex'],
                        sr_allowed=row['sr_allowed'],
                        has_sr=row['has_sr'],

                        segrade=grade_dict['segrade'],
                        srgrade=grade_dict['srgrade'],
                        pegrade=grade_dict['pegrade'],
                        cegrade=grade_dict['cegrade']
                    )
                if logging_on:
                    logger.debug('  ----- new_finalgrade: ' + str(grade_dict['finalgrade']) + '  >   ' + str(new_finalgrade))
                    logger.debug('        delete_exemption_cegrade_without_ce: ' + str(delete_exemption_cegrade_without_ce))

                if delete_exemption_cegrade_without_ce:

    # - IMPORTANT must put back new_ce_grade in grade_dict, to calc finalgrade with new cegrade
                    grade_dict['cegrade'] = None

    # - add new cegrade to sql_update_dict
                    # don't worry, if there is already an update of cegrade, it will be overwritten by this one
                    sql_update_dict(tobe_updated_sql_dict, examperiod,'grade', grade_pk, 'cegrade', None)

                    if logging_on:
                        logger.debug('  ----- tobe_updated_sql_dict: ' + str(tobe_updated_sql_dict))

                    if grade_pk not in updated_grade_pk_list:
                        updated_grade_pk_list.append(grade_pk)

                if logging_on:
                    logger.debug('  ----- sesrgrade: ' + str(grade_dict['sesrgrade']) + '  >  ' +  str(new_sesrgrade))
                    logger.debug('  ----- pecegrade: ' + str(grade_dict['pecegrade']) + '  >  ' + str(new_pecegrade))
                    logger.debug('  ----- finalgrade:  ' + str(grade_dict['finalgrade']) + '  >  ' + str(new_finalgrade))

                if new_sesrgrade != grade_dict['sesrgrade'] or \
                        new_pecegrade != grade_dict['pecegrade'] or \
                        new_finalgrade != grade_dict['finalgrade']:

    # - IMPORTANT must put back new grades in grade_dict, to calc max grade
                    grade_dict['sesrgrade'] = new_sesrgrade
                    grade_dict['pecegrade'] = new_pecegrade
                    grade_dict['finalgrade'] = new_finalgrade

                    if logging_on:
                        logger.debug('  ----- BINGO')
                        logger.debug('  .... new sesrgrade:  ' + str(grade_dict['sesrgrade']) + '  >  ' + str(new_sesrgrade))
                        logger.debug('  .... new pecegrade:  ' + str(grade_dict['pecegrade']) + '  >  ' + str(new_pecegrade))
                        logger.debug('  .... new finalgrade:   ' + str(grade_dict['finalgrade']) + '  >    ' + str(new_finalgrade))

    # - add new finalgrade etc in sql_update_dict
                    sql_update_dict(tobe_updated_sql_dict, examperiod, 'grade', grade_pk, 'sesrgrade', new_sesrgrade)
                    sql_update_dict(tobe_updated_sql_dict, examperiod, 'grade', grade_pk, 'pecegrade', new_pecegrade)
                    sql_update_dict(tobe_updated_sql_dict, examperiod, 'grade', grade_pk, 'finalgrade', new_finalgrade)

                    if grade_pk not in updated_grade_pk_list:
                        updated_grade_pk_list.append(grade_pk)

# --- calc no input
                this_ep_has_noinput = calc_noinputV2(
                    examperiod=examperiod,
                    sr_allowed=row['sr_allowed'],
                    has_sr=row['has_sr'],
                    has_practex=row['has_practex'],
                    subj_code=grade_dict['subj_code'],
                    weight_se=row['weight_se'],
                    weight_ce=row['weight_ce'],
                    exemption_year=row['exemption_year'],
                    no_ce_years=row['no_ce_years'],

                    segrade=grade_dict['segrade'],
                    srgrade=grade_dict['srgrade'],
                    pegrade=grade_dict['pegrade'],
                    cegrade=grade_dict['cegrade']
                )

# --- calc_has_pok
                this_ep_has_pok = calc_has_pok_v2(
                    noinput=this_ep_has_noinput,
                    no_centralexam=row['no_centralexam'],
                    gradetype=row['gradetype'],
                    is_combi=row['is_combi'],
                    weight_se=row['weight_se'],
                    weight_ce=row['weight_ce'],
                    sesrgrade=grade_dict['sesrgrade'],
                    pecegrade=grade_dict['pecegrade'],
                    finalgrade=grade_dict['finalgrade'],
                    examperiod=examperiod
                )
                if logging_on:
                    logger.debug('    this_ep_has_noinput:  ' + str(this_ep_has_noinput))
                    logger.debug('    this_ep_has_pok:  ' + str(this_ep_has_pok))

 # --- add grades to max_grade_ep_dict used to calculate max grade and max pok
                max_grade_ep_dict['sesrgrade'] = grade_dict['sesrgrade']
                max_grade_ep_dict['pecegrade'] = grade_dict['pecegrade']
                max_grade_ep_dict['finalgrade'] = grade_dict['finalgrade']
                max_grade_ep_dict['noinput'] = this_ep_has_noinput
                max_grade_ep_dict['has_pok'] = this_ep_has_pok

                if logging_on:
                    logger.debug('......... end of loop through grades of this studsubj .....')
# ===== end of loop through examperiods / grades of this studsubj ======================================

# --- calc max grade
            max_sesrgrade, max_pecegrade, max_finalgrade, max_noinput, max_use_exem = \
                calc_max_grade_v2(max_grade_dict)

            if max_sesrgrade != row['gradelist_sesrgrade'] or \
                    max_pecegrade != row['gradelist_pecegrade'] or \
                    max_finalgrade !=  row['gradelist_finalgrade'] or \
                    max_use_exem != row['gradelist_use_exem']:
                    # PR2024-05-31 TODO gl_noinput is not declared in model yet
                    #   max_noinput != row['gl_noinput']:
                # or old_gl_examperiod = row['gl_examperiod']

                studsubj_pk = row['id']

                sql_update_dict(tobe_updated_sql_dict, examperiod,'studsubj', studsubj_pk, 'gradelist_sesrgrade',max_sesrgrade)
                sql_update_dict(tobe_updated_sql_dict, examperiod,'studsubj', studsubj_pk, 'gradelist_pecegrade', max_pecegrade)
                sql_update_dict(tobe_updated_sql_dict, examperiod,'studsubj', studsubj_pk, 'gradelist_finalgrade', max_finalgrade)
                sql_update_dict(tobe_updated_sql_dict, examperiod,'studsubj', studsubj_pk, 'gradelist_use_exem', max_use_exem)

                # PR2024-05-31 TODO gl_noinput is not declared in model yet
                # sql_update_dict(tobe_updated_sql_dict, examperiod,'studsubj', studsubj_pk, 'gl_noinput', max_noinput)

                if studsubj_pk not in updated_studsubj_pk_list:
                    updated_studsubj_pk_list.append(studsubj_pk)

# --- calc max pok
            max_pok_sesr, max_pok_pece, max_pok_final = calc_max_pokV2(max_grade_dict)

            if max_pok_sesr != row['pok_sesr'] or \
                    max_pok_pece != row['pok_pece'] or \
                    max_pok_final != row['pok_final']:

                if logging_on:
                    logger.debug('  ---- new max_pok_sesr: ' + str(old_pok_sesr) + '  >  ' + str(max_pok_sesr))
                    logger.debug('  ---- new max_pok_pece: ' + str(old_pok_pece) + '  >  ' + str(max_pok_pece))
                    logger.debug('  ---- new max_pok_final: ' + str(old_pok_final) + '  >  ' + str(max_pok_final))

                studsubj_pk = row['id']

                sql_update_dict(tobe_updated_sql_dict, examperiod,'studsubj', studsubj_pk, 'pok_sesr',max_pok_sesr)
                sql_update_dict(tobe_updated_sql_dict, examperiod,'studsubj', studsubj_pk, 'pok_pece', max_pok_pece)
                sql_update_dict(tobe_updated_sql_dict, examperiod,'studsubj', studsubj_pk, 'pok_final', max_pok_final)

                if studsubj_pk not in updated_studsubj_pk_list:
                    updated_studsubj_pk_list.append(studsubj_pk)
            if logging_on:
                logger.debug('++++++++ end of loop through studsubjects ++++++++')
# +++++ end of loop through studsubjects +++++++++++++++++++++++++++++++++++++++++++++++++++++++

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('   before update_sql')
    update_sql()

    if logging_on:
        logger.debug('   before insert_to_log_sql')
    insert_to_log_sql()

    if logging_on:
        logger.debug('++++++++ end of batch_recalc_update_studsubj_grade_v2 ++++++++')

    return updated_grade_pk_list, updated_studsubj_pk_list
# - end of batch_recalc_update_studsubj_grade_v2

