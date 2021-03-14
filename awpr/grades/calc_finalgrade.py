# PR2021-01-17
from decimal import Decimal
from django.utils.translation import ugettext_lazy as _
from awpr import constants as c
from grades import calculations as calc
from awpr import locale as loc

from students import models as stud_mod

import logging
logger = logging.getLogger(__name__)

def update_finalgrade(grade, logging_on):
    if logging_on:
        logger.debug(' ------- update_finalgrade -------')

    studentsubject = grade.studentsubject
    schemeitem = studentsubject.schemeitem
    gradetype = schemeitem.gradetype
    weight_se = schemeitem.weight_se
    weight_ce = schemeitem.weight_ce

    se_grade = None
    pe_grade = None
    finalgrade = None

# - when second or third examperiod: get se_grade and pe_grade from first examperiod,
    if grade.examperiod == c.EXAMPERIOD_SECOND or grade.examperiod == c.EXAMPERIOD_THIRD:
        # get grade of first examperiod
        grade_first_period = stud_mod.Grade.objects.get_or_none(
            studentsubject=studentsubject,
            examperiod=c.EXAMPERIOD_FIRST
        )
        if grade_first_period is None:
            count_grade_first_period = stud_mod.Grade.objects.filter(
                studentsubject=studentsubject,
                examperiod=c.EXAMPERIOD_FIRST
            ).count()
            logger.error('ERROR: ' + count_grade_first_period + ' grades found in first examperiod.')
            logger.error('       subject: ' + str(schemeitem.subject.base.code))
            logger.error('       student: ' + str(studentsubject.student))
        else:

# - when second / third examperiod: get se_grade and pe_grade from grade_first_period
            se_grade = grade_first_period.segrade
            pe_grade = grade_first_period.pegrade
    else:

# - when first examperiod or exemption: get se_grade and pe_grade from grade
        se_grade = grade.segrade
        pe_grade = grade.pegrade

# - get ce_grade always from grade
    ce_grade = grade.cegrade

# - calculate finalgrade when gradetype is character
    if gradetype == c.GRADETYPE_02_CHARACTER:
        if grade.examperiod == c.EXAMPERIOD_SECOND:
            finalgrade = calc_finalgrade_char_reex_corona(se_grade, ce_grade, weight_se, logging_on)
        else:
            finalgrade = se_grade

# - calculate finalgrade when gradetype is number
    elif gradetype == c.GRADETYPE_01_NUMBER:

    # - calculate pe_ce
        has_practex = schemeitem.has_practexam
        pece_grade = calc_pece_grade(grade.examperiod, has_practex, ce_grade, pe_grade, logging_on)
        setattr(grade, 'pecegrade', pece_grade)

        finalgrade = calc_final_grade(se_grade, pece_grade, weight_se, weight_ce, logging_on)

    setattr(grade, 'finalgrade', finalgrade)

# --- end of calc_final_grade


def calc_final_grade(se_grade, pece_grade, weight_se, weight_ce, logging_on):
    if logging_on:
        logger.debug(' ----- calc_final_grade -----')
        logger.debug('se_grade: ' + str(se_grade) + ' ' + str(type(se_grade)))
        logger.debug('pece_grade: ' + str(pece_grade) + ' ' + str(type(pece_grade)))
        logger.debug('weight_se: ' + str(weight_se) + ' ' + str(type(weight_se)))
        logger.debug('weight_ce: ' + str(weight_ce) + ' ' + str(type(weight_ce)))

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
    """

    final_grade = None

# - no_se_grade = True if als weight_se > 0 and  se_decimal is None or 0
    no_se_grade = (weight_se > 0 and not se_grade)

# - no_pece_grade = True if als weight_ce > 0 and  pece_decimal is None or 0
    # note: if pe_number = 0 or None, pece_decimal = 0. Therefore you don't have to check if pe_number has value
    no_pece_grade = (weight_ce > 0 and not pece_grade)

    if no_se_grade or no_pece_grade:
        if not no_se_grade:
            final_grade = se_grade
        elif not no_pece_grade:
            final_grade = pece_grade
    else:
        se_grade_dot = se_grade.replace(',', '.')
        pece_grade_dot = pece_grade.replace(',', '.')
        decimal_notrounded = (Decimal(se_grade_dot) * Decimal(str(weight_se)) +
                                 Decimal(pece_grade_dot) * Decimal(str(weight_ce))) \
                                / (Decimal(str(weight_se)) + Decimal(str(weight_ce)))
        logger.debug('decimal_notrounded: ' + str(decimal_notrounded) + ' ' + str(type(decimal_notrounded)))
        output_decimal = decimal_notrounded.quantize(Decimal("1"), rounding='ROUND_HALF_UP')

        final_dot = str(output_decimal) if output_decimal else None
        if final_dot:
            final_grade = final_dot.replace('.', ',')

        if logging_on:
            logger.debug('output_decimal: ' + str(output_decimal) + ' ' + str(type(output_decimal)))


    if logging_on:
        logger.debug('final_grade: ' + str(final_grade) + ' ' + str(type(final_grade)))

    return final_grade
# --- end of calc_final_grade


def calc_finalgrade_char_reex_corona(se_grade, ce_grade, weight_se, logging_on):
    if logging_on:
        logger.debug(' ----- calc_finalgrade_char_reex_corona -----')
        logger.debug('se_grade: ' + str(se_grade) + ' ce_grade: ' + str(se_grade) + ' weight_se: ' + str(weight_se))
    # PR2020-05-15 Corona: Herkansing mogelijk bij ovg vakken. her-cijfer wordt in cegrade gezet
    # berekening:
    # - gebruik SE cijfer als herkansing lager is dan SE of gelijk aan SE
    # - bereken'gemiddelde' van se en ce als herkansing hoger is dan SE: v + g > g;  o + g > v (geen g !); o + v > v
    final_grade = None
    if weight_se:
        if se_grade and ce_grade and se_grade != ce_grade:
            if se_grade == 'g':
                # gebruik SE cijfer als herkansing lager is dan SE
                final_grade = 'g'
            elif se_grade == 'v':
                if ce_grade == 'g':
                    #gemiddeld eindcijfer v + g > g
                    final_grade = 'g'
                elif ce_grade == 'o':
                    #' gebruik SE cijfer als herkansing lager is dan SE
                    final_grade = 'v'
            elif se_grade == 'o':
                # gemiddeld eindcijfer o + g > v (geen g !!!)
                # gemiddeld eindcijfer o + v > v
                final_grade = 'v'
        else:
            final_grade = se_grade

    if logging_on:
        logger.debug( 'final_grade: ' + str(final_grade))
    return final_grade


def calc_pece_grade(examperiod_int, has_practex, ce_grade, pe_grade, logging_on):  # PR2021-01-18
    if logging_on:
        logger.debug(' ----- calc_pece_grade -----')
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

    pece_grade = None
    if examperiod_int in (c.EXAMPERIOD_FIRST, c.EXAMPERIOD_SECOND, c.EXAMPERIOD_THIRD):
        # 'a. bij praktijkexamen: bereken PeCecijfer uit CE en PE cijfer
        if has_practex:
# '1. PEcijfer en CEcijfer moeten beide zijn ingevuld
            if ce_grade and pe_grade:
                ce_dot = ce_grade.replace(',', '.')
                pe_dot = pe_grade.replace(',', '.')
# '2. bereken gemiddeld PeCe-cijfer
                pece_decimal = ( Decimal(ce_dot) + Decimal(pe_dot) ) / Decimal("2")
                if logging_on:
                    logger.debug('pece_decimal: ' + str(pece_decimal) + ' ' + str(type(pece_decimal)))
# '3. rond af op 1 cijfer achter de komma
                output_decimal = pece_decimal.quantize(Decimal("1.0"), rounding='ROUND_HALF_UP')
                if logging_on:
                    logger.debug('output_decimal: ' + str(output_decimal) + ' ' + str(type(output_decimal)))
                pece_dot = str(output_decimal) if output_decimal else None
                if pece_dot:
                    pece_grade = pece_dot.replace('.', ',')
        else:
    #     'b. bij geen Vsi_HasPraktijkex is PeCe(Tv)=0 gelijk aan crcCE(Tv)
            pece_grade = ce_grade
    #         End If
    elif examperiod_int == c.EXAMPERIOD_EXEMPTION:
    #     'c. bij vrijstelling wordt geen PE ingevuld, daarom is PeCe(Tv)=0 gelijk aan crcCEvrijst
             pece_grade = ce_grade
    if logging_on:
        logger.debug('pece_grade: ' + str(pece_grade))
    return pece_grade
# --- end of calc_pece_grade


def get_score_from_inputscore(input_value, max_score):
    logger.debug(' ----- get_score_from_inputscore -----')
    logger.debug('input_value: ' + str(input_value) + ' ' + str(type(input_value)))
    # function converts input_value to whole number PR2021-01-18

# 1. reset output variables
    input_number, output_text, msg_err = 0, None, None
# 2. remove spaces before and after input_value
    imput_trim = input_value.strip() if input_value else ''
# - exit if imput_trim has no value, without msg_err
    if imput_trim:
        has_error = False
# - replace all comma's with dots
        input_with_dots = imput_trim.replace(',', '.')
# cast input_with_dots to decimal, exit if not numeric
        # '', ' ' and non-numeric give InvalidOperation error
        input_number = None
        try:
            input_number = Decimal(input_with_dots)
        except:
            has_error = True
        if not has_error:
# - get remainder of input_number
            # the remainder / modulus operator (%) returns the remainder after (integer) division.
            remainder = input_number % 1
            if remainder != 0:
                has_error = True
            elif max_score and input_number > max_score:
                has_error = True
        if has_error:
            input_number = None
            msg_err = str(_("Score '%(val)s' is not allowed.") % {'val': str(input_value)}  ) + "\n" + \
                    str(_("The score must be a whole number between 0 and %(max)s.") % {'max': max_score})

    return input_number, msg_err
# --- end of get_score_from_inputscore


def get_grade_from_input_str(input_str, logging_on):
    logging_on = False
    if logging_on:
        logger.debug(' ----- get_grade_from_input_str -----')
        logger.debug('input_value: ' + str(input_str) + ' ' + str(type(input_str)))

# - set output variables
    output_str, msg_err = None, None

# - remove spaces before and after input_value
    imput_trim = input_str.strip() if input_str else ''

# - exit if imput_trim has no value, without msg_err
    if imput_trim:
        has_err = False

# - replace all comma's by dots
        input_replaced = imput_trim.replace(',', '.')
        length = len(input_replaced)

# - add dot when input_replaced has no dots
        if '.' not in input_replaced:
    # if input_replaced is between '1' en '9': add '.0'
            if length == 1:
                input_replaced += '.0'
            elif length == 2:
    # if input_replaced = '10': add '.0'
                if input_replaced == '10':
                    input_replaced += '.0'
                else:
    # if input_replaced is between '11' en '99': pu dot in the middle
                    input_replaced = ''.join( ( input_replaced[0:1], '.', input_replaced[1:] ) )
            else:
                has_err = True
        else:
            if length == 2:
                #  '.7' is not allowed, '7.0' is allowed
                has_err = (input_replaced[0:1] == '.')
            elif length == 3:
                #  '.56' and '.56' are not allowed, '5.6' is allowed
                has_err = (input_replaced[1:2] != '.')
            else:
                #  'only '10.0' is allowed
                has_err = (input_replaced != '10.0')

        if not has_err:
# - convert input_replaced to Decimal type
            try:
                output_decimal = Decimal(input_replaced)
                output_str = str(output_decimal)
                # replace dot by comma
                output_str = output_str.replace('.', ',')
            except Exception as e:
                # '', ' ' and non-numeric give InvalidOperation error
                has_err = True
                if logging_on:
                    logger.debug(getattr(e, 'message', str(e)))

        if has_err:
            msg_err = str(_('Grade')) + " '" + imput_trim + "' " + str(_('is not allowed.')) + "\n"
            msg_err += str(_('The grade must be a number between 1 and 10.'))

    if logging_on:
        logger.debug('output_str: ' + str(output_str))
        if msg_err:
            logger.debug('msg_err: ' + str(msg_err))

    return output_str, msg_err
# - end of get_grade_from_input_str
