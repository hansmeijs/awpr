# PR2021-01-18
from django.utils.translation import ugettext_lazy as _

from awpr import constants as c
from grades import calc_finalgrade as calc_final

import logging
logger = logging.getLogger(__name__)


#######################################################
def validate_input_grade(grade, field, input_value, logging_on):  # PR2021-01-18
    logging_on = False
    #  PR2021-05-02 field "srgrade" added, TODO no validations yet
    is_score = field in ("pescore", "cescore")
    is_grade = field in ("segrade", "srgrade", "pegrade", "cegrade")
    is_se_grade = (field == "segrade")
    is_se =  (field in ("segrade", "srgrade"))
    is_pe = (field in ("pescore", "pegrade"))
    is_pe_or_ce = (field in ("pescore", "pegrade", "cescore", "cegrade"))

    examperiod_int = grade.examperiod

    studsubj = grade.studentsubject
    has_exemption = studsubj.has_exemption
    has_reex = studsubj.has_reex
    has_reex03 = studsubj.has_reex03

    schemeitem = studsubj.schemeitem
    gradetype = schemeitem.gradetype
    weight_se = schemeitem.weight_se
    weight_ce = schemeitem.weight_ce
    is_combi = schemeitem.is_combi
    extra_count_allowed = schemeitem.extra_count_allowed
    extra_nocount_allowed = schemeitem.extra_nocount_allowed
    has_practexam = schemeitem.has_practexam

    subject = schemeitem.subject

    scheme = schemeitem.scheme
    department = scheme.department

    examyear = department.examyear

    # TODO move to schemitems PR2021-04-24
    no_practexam = False  # was: examyear.no_practexam
    no_centralexam = False  # was: examyear.no_centralexam
    combi_reex_allowed = False  # was: examyear.combi_reex_allowed
    no_exemption_ce = False  # was: examyear.no_exemption_ce
    no_thirdperiod = False  # was: examyear.no_thirdperiod

    student = studsubj.student
    is_eveningstudent  = student.iseveningstudent

    school = student.school
    is_dayschool = school.isdayschool
    is_eveningschool = school.iseveningschool
    is_lexschool = school.islexschool

    norm = schemeitem.norm
    scalelength_ce = norm.scalelength_ce if norm else None
    scalelength_pe =  norm.scalelength_pe if norm else None
    scalelength_reex =  norm.scalelength_reex if norm else None

    if logging_on:
        logger.debug(' ------- validate_input_grade -------')
        logger.debug("subject: ", subject.base.code, "student: ", student)
        logger.debug("field: ", field, "input_value: ", input_value)
        logger.debug("is_score: ", is_score, "is_grade: ", is_grade, "is_pe: ", is_pe)

# - reset output parameters
    output_str, msg_err = None, None

# - exit als kandidaat is vergrendeld >>> handle outside this function
    #  if (dict.ey_locked) { msg_err = err_list.examyear_locked} else
    #  if (dict.school_locked) { msg_err = err_list.school_locked} else
    #  if (dict.stud_locked) {msg_err = err_list.candidate_locked};
    #  if( (dict.se_locked && fldName === "segrade") ||
    #      (dict.sr_locked && fldName === "srgrade") ||
    #      (dict.pe_locked && fldName in ["pescore", "pegrade"]) ||
    #      (dict.ce_locked && fldName in ["cescore", "cegrade"]) ) {
    #          msg_err = err_list.grade_locked;
    #  }

# - exit als dit vak bewijs van kennis heeft. Dan is invoer gegevens geblokkeerd.
    #  PR2010-06-10 mail Lorraine Wieske: kan geen PE cjfers corrigeren. Weghalen
    #  If KvHasBewijsKennis Then
    #  strMsgText = "Vak heeft Bewijs van Kennis en is daarom vergrendeld." & vbCrLf & "Ga naar Rapportages Ex6 om Bewijs van Kennis zo nodig te wissen."

# - check if entry is allowed this examperiod
    # - EXAMPERIOD_FIRST:       all entries allowed
    # - EXAMPERIOD_SECOND:      only cescore or cegrade allowed (or cegrade is blocked??)
    # - EXAMPERIOD_THIRD:       only cegrade allowed (no scores in third period
    # - EXAMPERIOD_EXEMPTION:   only segrade and cegrade allowed. No score, no pe allowed

    field_allowed = False
    if examperiod_int == c.EXAMPERIOD_FIRST:
        field_allowed = field in ("pescore", "cescore", "segrade", "pegrade", "cegrade")
    if examperiod_int == c.EXAMPERIOD_SECOND:
        field_allowed = field in ("cescore", "cegrade")
    elif examperiod_int == c.EXAMPERIOD_THIRD:
        field_allowed = field == "cegrade"
    elif examperiod_int == c.EXAMPERIOD_EXEMPTION:
        field_allowed = field in ("segrade", "cegrade")

# - exit als input_value niet ingevuld (msg_err = None, geen foutmelding)
    if field_allowed and input_value:

# - Corona: check if no_centralexam (not when examperiod is exemption)
        if is_pe_or_ce:
            if examperiod_int != c.EXAMPERIOD_EXEMPTION and no_centralexam:
                msg_err = _('There are no central exams this exam year.')
            elif examperiod_int == c.EXAMPERIOD_THIRD and no_thirdperiod:
# - Corona: check if no_thirdperiod (only when examperiod is exemption)
                msg_err = _('There is this exam year no third exam period.')
            elif is_combi and not combi_reex_allowed and examperiod_int in (c.EXAMPERIOD_SECOND, c.EXAMPERIOD_THIRD):
# - Corona: reexamination not allowed for combination subjects, except when combi_reex_allowed
                msg_err = _('Combination subject has no re-examination.')
# - afterCorona: check if exemption has no_centralexam,  PR2020-12-16
            # skip when iseveningstudent school or islexschool
        if msg_err is None:
            if examperiod_int == c.EXAMPERIOD_EXEMPTION:
                if is_pe_or_ce and no_exemption_ce:
                    if not is_eveningstudent and not is_lexschool:
                        msg_err = _('Exemption has no central exam this exam year.')
# - controleer Praktijkexamen 'PR2019-02-22 'PR2015-12-08
        if msg_err is None:
            if is_pe:
                if no_practexam:
                    msg_err = _('There are no practical exams this exam year.')
                elif not has_practexam:
                    msg_err = _('This subject has no practical exam.')

# - controleer Herexamen 'PR2015-12-13
        # not necessary PR2020-12-16

# - controleer ce cijfer van combivak
        if msg_err is None:
            # 'PR2019-05-03 keuze-combi weer uitgeschakeld. Was:   Or KvIsKeuzeCombiVak Then 'PR2016-05-30 KeuzeCombi toegevoegd. Was: If VsiIsCombinatieVak Then
            if is_pe_or_ce:
                if is_combi:
# - reexamination not allowed for combination subjects, except when Corona
                    if examperiod_int == c.EXAMPERIOD_FIRST:
                        caption = None
                        if field == "pescore":
                            caption = str(_("Score practical exam"))
                        elif field == "cescore":
                            caption = str(_("CE grade"))
                        elif field == "pegrade":
                            caption = str(_("Grade practical exam"))
                        elif field == "cegrade":
                            caption = str(_("CE grade"))

                        msg_err = caption + str(_(' not allowed in combination subject.'))
                    elif examperiod_int in (c.EXAMPERIOD_SECOND, c.EXAMPERIOD_THIRD):
#  'PR2020-05-15 Corona: herkansing wel mogelijk bij combivakken
                        if not combi_reex_allowed:
                             msg_err = _('Re-examination grade not allowed in combination subject.')

# - controleer weging
        if msg_err is None:
            if is_se_grade:
                if not weight_se:
                    msg_err = _('The SE weighing of this subject is zero.\nYou cannot enter a grade.')
            else:
                if not weight_ce:
                    if is_score:
                        msg_err = _('The CE weighing of this subject is zero.\nYou cannot enter a score.')
                    else:
                        msg_err = _('The CE weighing of this subject is zero.\nYou cannot enter a grade.')

# A. SCORE
    # 1. controleer score PR2015-12-27 PR2016-01-03
        if msg_err is None:
            if is_score:
                # this is already covered by 'no_practexam' and 'no_centralexam'
                # 'PR2020-05-15 Corona: geen scores
                # strMsgText = "Er kunnen geen scores ingevuld worden in examenjaar " & ExkExamenjaar & "."

                #PR2015-12-27 debug: vervang komma door punt, anders wordt komma genegeerd
                max_score = None
                if field == "pescore":
                    max_score = scalelength_pe
                elif field == "cescore":
                    if examperiod_int == c.EXAMPERIOD_FIRST:
                        max_score =  scalelength_ce
                    elif examperiod_int == c.EXAMPERIOD_SECOND:
                        max_score =  scalelength_reex
                input_number, msg_err = calc_final.get_score_from_inputscore(input_value, max_score)
# B. CIJFER
            elif is_grade:
#  /1. exit als CijferType VoldoendeOnvoldoende is en inputcijfer niet booIsOvg is
#
#         //GRADETYPE_00_NONE = 0
#         //GRADETYPE_01_NUMBER = 1
#         //GRADETYPE_02_CHARACTER = 2  # goed / voldoende / onvoldoende

                if gradetype == c.GRADETYPE_00_NONE:
                    msg_err =_("Grade type has no value.\nGrades cannot be entered."),

                elif gradetype == c.GRADETYPE_02_CHARACTER:  # goed / voldoende / onvoldoende
                    value_lc = input_value.lower()
                    if value_lc in ('o', 'v', 'g'):
                        output_str = value_lc
                    else:
                        msg_err = _("Grade can only be 'g', 'v' or 'o'.")

                elif gradetype == c.GRADETYPE_01_NUMBER:
                    output_str, msg_err = calc_final.get_grade_from_input_str(input_value, logging_on)

    if logging_on:
        logger.debug("output_str: " + str(output_str))
        if msg_err:
            logger.debug("msg_err: " + str(msg_err))
    return output_str, msg_err
