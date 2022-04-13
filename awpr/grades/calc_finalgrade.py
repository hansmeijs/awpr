# PR2021-01-17
from decimal import Decimal
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import gettext_lazy as _

from awpr import constants as c
from awpr import settings as s

from grades import calculations as grade_calc
import logging
logger = logging.getLogger(__name__)


def calc_sesr_pece_final_grade(si_dict, is_ep_exemption, has_sr, exem_year, se_grade, sr_grade, pe_grade, ce_grade):
    # PR2021-12-28 PR2022-04-11
    # called by GradeUploadView.recalc_finalgrade_in_grade_and_save and by import_studsubj_grade_from_datalist
    # this function does not save the calculated dields
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- calc_sesr_pece_final_grade -------')

    # - when second or third examperiod: get se_grade and pe_grade from first examperiod,
    # and store them in second or third examperiod
    # NOT ANY MORE: se, sr and pe grades are already stored in grade reex and reex03 when updating

    # PR2022-04-12 no_ce_years = '2020;2021' has list of examyears that had no CE. This is used to skip no_input_ce when calculating exemption endgrade
    # PR2022-04-12 thumb_rule = True: may skip this subject when calculating result
    # TODO thumb_rule = si_dict.get('thumb_rule')

    sesr_grade, pece_grade, finalgrade = None, None, None
    try:

        has_practexam = si_dict.get('has_practexam', False)
        gradetype = si_dict.get('gradetype', 0)
        weight_se = si_dict.get('weight_se', 0)
        weight_ce = si_dict.get('weight_ce', 0)
        no_ce_years = si_dict.get('no_ce_years')

        if logging_on:
            logger.debug('gradetype: ' + str(gradetype))
            logger.debug('weight_se: ' + str(weight_se))
            logger.debug('weight_ce: ' + str(weight_ce))
            logger.debug('se_grade: ' + str(se_grade) + ' ' + str(type(se_grade)))
            logger.debug('sr_grade: ' + str(sr_grade) + ' ' + str(type(sr_grade)))
            logger.debug('pe_grade: ' + str(pe_grade) + ' ' + str(type(pe_grade)))
            logger.debug('ce_grade: ' + str(ce_grade) + ' ' + str(type(ce_grade)))

# ++++  calculate finalgrade when gradetype is character
        if gradetype == c.GRADETYPE_02_CHARACTER:
    # - calculate sesr_grade
            sesr_grade, se_noinput, sr_noinput = calc_sesr_char(se_grade, sr_grade, has_sr, weight_se)
    # - calculate finalgrade
            finalgrade = calc_finalgrade_char(sesr_grade, se_noinput, sr_noinput, weight_se)

# ++++  calculate finalgrade when gradetype is number
        elif gradetype == c.GRADETYPE_01_NUMBER:

    # - calculate se_sr
            sesr_decimal, se_noinput, sr_noinput = calc_sesr_decimal(is_ep_exemption, se_grade, sr_grade, has_sr, weight_se)
            sesr_grade = str(sesr_decimal) if sesr_decimal else None

    # - calculate pe_ce
            pece_decimal, pe_noinput, ce_noinput = calc_pece_decimal(is_ep_exemption, ce_grade, pe_grade, weight_ce,
                                                                     has_practexam, exem_year, no_ce_years)
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
        logger.debug('sesr_grade: ' + str(sesr_grade))
        logger.debug('pece_grade: ' + str(pece_grade))
        logger.debug('finalgrade: ' + str(finalgrade))

    return sesr_grade, pece_grade, finalgrade
# --- end of calc_sesr_pece_final_grade

#@@@@@@@@@@@@@@@@@@@@@@@@@@

def calc_final_grade_number(sesr_decimal, pece_decimal, sesr_noinput, pece_noinput, weight_se, weight_ce):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- calc_final_grade_number -----')
        logger.debug('sesr_decimal: ' + str(sesr_decimal) + ' ' + str(type(sesr_decimal)))
        logger.debug('pece_decimal: ' + str(pece_decimal) + ' ' + str(type(pece_decimal)))
        logger.debug('sesr_noinput: ' + str(sesr_noinput))
        logger.debug('pece_noinput: ' + str(pece_noinput))

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
            logger.debug('final_decimal_notrounded: ' + str(final_decimal_notrounded) + ' ' + str(type(final_decimal_notrounded)))

        if final_decimal_notrounded:
            final_decimal_rounded = final_decimal_notrounded.quantize(Decimal("1"), rounding='ROUND_HALF_UP')
            if logging_on:
                logger.debug('final_decimal_rounded: ' + str(final_decimal_rounded) + ' ' + str(type(final_decimal_rounded)))
            # final_decimal_rounded is integer , so no need for: final_grade = final_dot.replace('.', ',')
            final_grade = str(final_decimal_rounded)
        else:
            final_grade = None

    if logging_on:
        logger.debug('final_grade: ' + str(final_grade) + ' ' + str(type(final_grade)))

    return final_grade
# --- end of calc_final_grade_number


def calc_finalgrade_char(sesr_grade, se_noinput, sr_noinput, weight_se):  # PR2021-12-15
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- calc_finalgrade_char -----')
        logger.debug('sesr_grade: ' + str(sesr_grade) + ' se_noinput: ' + str(se_noinput) + ' sr_noinput: ' + str(sr_noinput) + ' weight_se: ' + str(weight_se))

    final_grade = None
    if weight_se:
        # if there is no sr: sr_noinput = False
        if not se_noinput and not sr_noinput:
            final_grade = sesr_grade

    if logging_on:
        logger.debug( 'final_grade: ' + str(final_grade))
    return final_grade
# --- end of calc_finalgrade_char


def calc_sesr_char(se_grade, sr_grade, has_sr, weight_se):  # PR2021-12-15
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- calc_sesr_char -----')
        logger.debug('se_grade: ' + str(se_grade) + ' sr_grade: ' + str(sr_grade) + ' has_sr: ' + str(has_sr))

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
        logger.debug( 'sesr_grade: ' + str(sesr_grade))
    return sesr_grade, se_noinput, sr_noinput
# --- end of calc_sesr_char


def calc_sesr_decimal(is_ep_exemption, se_grade, sr_grade, has_sr, weight_se):  # PR2021-12-13
    # from AWP Calculations.CalcEindcijfer_SeFinal PR2021-04-12
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- calc_sesr_decimal -----')
        logger.debug('... is_ep_exemption:  ' + str(is_ep_exemption))
        logger.debug('... se_grade: ' + str(se_grade) + ' ' + str(type(se_grade)))
        logger.debug('... sr_grade: ' + str(sr_grade) + ' ' + str(type(sr_grade)))
        logger.debug('... has_sr: ' + str(has_sr))
        logger.debug('... weight_se: ' + str(weight_se))

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
            if logging_on:
                logger.debug('... se_decimal_A: ' + str(se_decimal_A) + ' ' + str(type(se_decimal_A)))

# if examperiod exemption: sesr_grade = se_grade
            if is_ep_exemption:
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
                    if logging_on:
                        logger.debug('... sr_decimal_B: ' + str(sr_decimal_B) + ' ' + str(type(sr_decimal_B)))
                        logger.debug('... compare_se_sr: ' + str(compare_se_sr))

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
        logger.debug('... sesr_decimal: ' + str(sesr_decimal) + ' ' + str(type(sesr_decimal)))
        logger.debug('... se_noinput: ' + str(se_noinput) + ' sr_noinput: ' + str(sr_noinput))
    return sesr_decimal, se_noinput, sr_noinput
# - end of calc_sesr_decimal


def calc_pece_decimal(is_ep_exemption, ce_grade, pe_grade, weight_ce, has_practexam, exem_year, no_ce_years):
    # PR2021-01-18 PR2021-09-18 PR2021-12-14 PR2022-04-12
    # PR2022-04-12 no_ce_years = '2020;2021' has list of examyears that had no CE. This is used to skip no_input_ce when calculating exemption endgrade

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- calc_pece_decimal -----')
        logger.debug('... is_ep_exemption:  ' + str(is_ep_exemption))
        logger.debug('... ce_grade: ' + str(ce_grade) + ' ' + str(type(ce_grade)))
        logger.debug('... pe_grade: ' + str(pe_grade) + ' ' + str(type(pe_grade)))
        logger.debug('... weight_ce: ' + str(weight_ce))
        logger.debug('... has_practexam: ' + str(has_practexam))
        logger.debug('... exem_year: ' + str(exem_year))
        logger.debug('... no_ce_years: ' + str(no_ce_years))

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

# - skip if weight_ce = 0, no error
    if weight_ce:

# - check if ce_grade has value, if not: set ce_noinput = True, except when is_exemption_without_ce
        if not ce_grade:
    # - check if this subject had central exam, only when is_ep_exemption
            is_exemption_without_ce = False
            if is_ep_exemption and exem_year and no_ce_years:
                # no_ce_years = '2020;2021', value in schemeitem
                # exem_year = 2020, value in studentsubject
                no_ce_years_arr = no_ce_years.split(';')
                if str(exem_year) in no_ce_years_arr:
                    is_exemption_without_ce = True

            if not is_exemption_without_ce:
                ce_noinput = True

            if logging_on:
                logger.debug('... ce_noinput = True')
        else:

# - in ce_grade: replace comma by dot, convert to decimal
            ce_dot_nz = ce_grade.replace(',', '.') if ce_grade else "0"
            ce_decimal_A = Decimal(ce_dot_nz)
            if logging_on:
                logger.debug('... ce_dot_nz: ' + str(ce_dot_nz) + ' ' + str(type(ce_dot_nz)))
                logger.debug('... ce_decimal_A: ' + str(ce_decimal_A) + ' ' + str(type(ce_decimal_A)))

# if subject has no practical exam: pece_grade = ce_grade
# also if exemption: pece_grade = ce_grade
            if not has_practexam or is_ep_exemption:
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
                    logger.debug('... pe_dot_nz: ' + str(pe_dot_nz) + ' ' + str(type(pe_dot_nz)))
                    logger.debug('... pe_decimal_B: ' + str(pe_decimal_B) + ' ' + str(type(pe_decimal_B)))
                    logger.debug('... pece_decimal_not_rounded: ' + str(pece_decimal_not_rounded) + ' ' + str(type(pece_decimal_not_rounded)))

    if logging_on:
        logger.debug('... pece_decimal: ' + str(pece_decimal) + ' ' + str(type(pece_decimal)))
        logger.debug('... pe_noinput: ' + str(pe_noinput) + ' ' + str(type(pe_noinput)))
        logger.debug('... ce_noinput: ' + str(ce_noinput) + ' ' + str(type(ce_noinput)))

    return pece_decimal, pe_noinput, ce_noinput
# --- end of calc_pece_decimal


def get_score_from_inputscore(input_value, max_score):
    # PR2022-02-09
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_score_from_inputscore -----')
        logger.debug('input_value: ' + str(input_value) + ' ' + str(type(input_value)))
    # function converts input_value to whole number PR2021-01-18

# 1. reset output variables
    input_number, output_text = 0, None
    err_list = []

# 2. remove spaces before and after input_value
    imput_trim = input_value.strip() if input_value else ''
    if logging_on:
        logger.debug('imput_trim: ' + str(imput_trim) + ' ' + str(type(imput_trim)))

# - exit if imput_trim has no value, without msg_err
    if imput_trim:
        has_error = False

# - remove all comma's and dots
        input_no_comma = imput_trim.replace(',', '')
        input_no_dots = input_no_comma.replace(',', '')
        if logging_on:
            logger.debug('input_no_dots: ' + str(input_no_dots) + ' ' + str(type(input_no_dots)))
# cast input_with_dots to decimal, exit if not numeric
        # '', ' ' and non-numeric give InvalidOperation error
        input_number = None
        try:
            input_number = int(input_no_dots)
        except Exception as e:
            has_error = True
            if logging_on:
                logger.debug('Exception: ' + str(e))
        if logging_on:
            logger.debug('imput_trim: ' + str(imput_trim) + ' ' + str(type(imput_trim)))

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

        if logging_on:
            logger.debug('input_number: ' + str(input_number) + ' ' + str(type(input_number)))

        input_str = str(input_number) if input_number is not None else None
    return input_str, err_list
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
        logger.debug('imput_trim: >' + str(imput_trim) + '< ' + str(type(imput_trim)))

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
    logging_on = False
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
