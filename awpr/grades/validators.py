# PR2021-01-18
from django.utils.translation import ugettext_lazy as _

from django.db import connection

from awpr import constants as c
from awpr import settings as s
from grades import calc_finalgrade as calc_final

from students import functions as stud_fnc
from students import models as stud_mod

import logging
logger = logging.getLogger(__name__)


def validate_grade_auth_publ(grade_instance, se_sr_pe_ce):  # PR2021-12-25
    err_list = []
    if grade_instance:
        # note: don't check on blocked:
        #   se_blocked etc is True when Inspection has blocked the subject from gradelist, until it is changed
        #   when blocked is set True, published_id  and all auth_id will be erased, so the school can submit the grade again

        is_publ, is_auth = False, False
        key_str = ''.join((se_sr_pe_ce, '_published_id'))
        is_publ = getattr(grade_instance, key_str)
        if not is_publ:
            for auth_index in range(1, 5):  # range(start_value, end_value, step), end_value is not included!
                key_str = ''.join((se_sr_pe_ce, '_auth', str(auth_index), 'by_id'))
                is_auth = getattr(grade_instance, key_str)
                if is_auth:
                    break

        if is_publ or is_auth:
            caption = '-'
            examperiod = getattr(grade_instance, 'examperiod')
            if examperiod == c.EXAMPERIOD_EXEMPTION:
                caption = str(_('This exemption'))
            elif examperiod == c.EXAMPERIOD_THIRD:
                caption = str(_('This re-examination 3rd exam period'))
            elif examperiod == c.EXAMPERIOD_SECOND:
                caption = str(_('This re-examination'))
            elif examperiod == c.EXAMPERIOD_FIRST:
                if se_sr_pe_ce == 'se':
                    caption = str(_('This school exam'))
                elif se_sr_pe_ce == 'sr':
                    caption = str(_('This re-examination school exam'))
                elif se_sr_pe_ce == 'pe':
                    caption = str(_('This practical exam'))
                elif se_sr_pe_ce == 'ce':
                    caption = str(_('This cental exam'))

            if is_publ:
                err_list.append(str(_('%(cpt)s is already submitted.') % {'cpt': caption}))
                err_list.append(str(_('You must ask the Inspection permission to make changes.')))
            elif is_auth:
                err_list.append(str(_('%(cpt)s is already authorized.') % {'cpt': caption}))
                err_list.append(str(_('You must first undo the authorization before you can make changes.')))

    return err_list


#######################################################
def validate_update_grade(grade_instance, examgradetype, input_value, sel_examyear, si_dict):
    # PR2021-01-18 PR2021-09-19 PR2021-12-15 PR2021-12-25
    logging_on = False  # s.LOGGING_ON
    # examgradetypes are: 'segrade', 'srgrade', 'pescore', 'pegrade', 'cescore', 'cegrade
    # calculaed fields are: 'sesrgrade', 'pecegrade', 'finalgrade'


    is_se = examgradetype in ("segrade", "srgrade")
    is_sr = examgradetype == "srgrade"
    is_pe = examgradetype in ("pescore", "pegrade")
    is_score = "score" in examgradetype
    is_grade = "grade" in examgradetype

    is_se_grade = (examgradetype == "segrade")
    is_pe_or_ce = (examgradetype in ("pescore", "pegrade", "cescore", "cegrade"))

    examperiod_int = grade_instance.examperiod

    gradetype = si_dict.get('gradetype')
    weight_se = si_dict.get('weight_se')
    weight_ce = si_dict.get('weight_ce')
    is_combi = si_dict.get('is_combi')
    extra_count_allowed = si_dict.get('extra_count_allowed')
    extra_nocount_allowed = si_dict.get('extra_nocount_allowed')
    si_has_practex = si_dict.get('has_practexam')
    si_sr_allowed = si_dict.get('sr_allowed')

    subj_code = si_dict.get('subj_code')


    studsubj = grade_instance.studentsubject


    student = studsubj.student
    # has_dyslexie = student.has_dyslexie
    st_iseveningstudent = student.iseveningstudent
    st_islexstudent =student.islexstudent

    # bis_exam = student.bis_exam
    st_partial_exam = student.partial_exam  # get certificate, only when evening- or lexstudent
    # deprecated, use partial_exam instead. Was: st_additional_exam = student.additional_exam  # when student does extra subject at a different school, possible in day/evening/lex school, only valid in the same examyear

    max_score, nex_id, cesuur, nterm = None, None, None, None
    if is_pe:
        exam = grade_instance.pe_exam
    else:
        exam = grade_instance.ce_exam

    if exam:
        max_score = exam.scalelength
        nex_id = exam.nex_id
        cesuur = exam.cesuur
        nterm = exam.nterm

    if logging_on:
        logger.debug(' ')
        logger.debug(' ------- validate_update_grade -------')
        logger.debug('subj_code: ' + str(subj_code) + ' student: ' + str(student))
        logger.debug('examgradetype: ' + str(examgradetype) + ' input_value: ' + str(input_value))
        logger.debug('is_score: ' + str(is_score) + ' is_grade: ' + str(is_grade) + ' is_pe: ' + str(is_pe))


# =======================================================================================
# - reset output parameters
    output_str = None
    msg_list = []

# - check if:
    #  - country is locked,
    #  - examyear is not found, not published or locked
    #  - school is not found, not same_school, not activated, or locked
    #  - department is not found, not in user allowed depbase or not in school_depbase
    #  these are taken care of in GradeUploadView > get_selected_ey_school_dep_from_usersetting

# - check if it is allowed to enter this examgradetype this examyear
    # - check if examyear has no_practexam, sr_allowed, no_centralexam, no_thirdperiod
    err_list = validate_grade_examgradetype_in_examyear(sel_examyear, examgradetype)
    if err_list:
        msg_list.extend(err_list)
    if logging_on:
        logger.debug("err_list: ", err_list)

# - check if grade is published or authorized
    if not err_list:
        se_sr_pe_ce = examgradetype[0:2]
        err_list = validate_grade_auth_publ(grade_instance, se_sr_pe_ce)

# - check if it is allowed to enter this examgradetype in this schemeitem
    # schemitem variables are has_practexam sr_allowed max_reex no_thirdperiod no_exemption_ce
    # checks if:
    #  - when srgrade: checks if sr is allowed
    #  - when exemcegrade: checks if no_exemption_ce  TODO: no_exemption_ce only applied to exam 2020, so doenst ake sense here. Fix it
    #  - when pescore or pegrade: checks if has_practexam
    #  - when reexscore or reexgrade: checks if max_reex > 0
    #  - when reex03score or reex03grade: checks if max_reex > 0 and not no_thirdperiod
    #  - when combi subject: check if not practex, ce, reex, reex-03
    #  - check if weighing > 0
    if not err_list:
        err_list = validate_grade_examgradetype_in_schemeitem(examgradetype, si_dict, input_value)
    if logging_on:
        logger.debug("err_list: ", err_list)

    # - exit if examgradetype not allowed for this studsubject
    # checks if:
    #  - when srgrade: checks if student has sr
    #  - when exemption: checks if student has exemption
    #  - when reex: checks if student has reex
    #  - when reex03: checks if student has reex03
    if not err_list:
        err_list = validate_grade_examgradetype_in_studsubj(
            examgradetype=examgradetype,
            ss_has_sr=studsubj.has_sr,
            ss_has_exemption=studsubj.has_exemption,
            ss_has_reex=studsubj.has_reex,
            ss_has_reex03=studsubj.has_reex03
        )
    if logging_on:
        logger.debug("err_list: ", err_list)

# - check if:
    #  - grade is already authorized, published or blocked
    #   se_blocked etc is True when Inspection has blocked the subject from gradelist, until it is changed
    #   when blocked is set True, published_id  and all auth_id will be erased, so the school can submit the grade again
    if not err_list:
        # examtype = 'se', 'sr', 'pe', 'ce'
        examtype = examgradetype[:2]
        is_score = ('score' in examgradetype)

        this_item_cpt = str(_('This score')) if is_score else str(_('This grade'))
        err_list = validate_grade_published_from_gradeinstance(grade_instance, examtype, this_item_cpt)
        if err_list:
            item_str = str(_('score')) if is_score else str(_('grade'))
            err_list.append('???' + str(_('You cannot enter a %(item_str)s.') % {'item_str': item_str}))
    if logging_on:
        logger.debug("err_list: ", err_list)

# - check if entry is allowed this examperiod
    # Note: value of examperiod is calculated from from examgradetype by get_examperiod_from_examgradetype
    # so there is no need to check if examgradetype is valid in this examperiod

# - exit als dit vak bewijs van kennis heeft. Dan is invoer gegevens geblokkeerd.
        #  PR2010-06-10 mail Lorraine Wieske: kan geen PE cjfers corrigeren. Weghalen
        #  If KvHasBewijsKennis Then
        #  strMsgText = "Vak heeft Bewijs van Kennis en is daarom vergrendeld." & vbCrLf & "Ga naar Rapportages Ex6 om Bewijs van Kennis zo nodig te wissen."

# - afterCorona: check if exemption has ey_no_centralexam,  PR2020-12-16
            # skip when iseveningstudent school or islexschool
        #if msg_err is None:
        #    if examperiod_int == c.EXAMPERIOD_EXEMPTION:
        #        if is_pe_or_ce and no_exemption_ce:
        #            if not is_eveningstudent and not is_lexschool:
        #                msg_err = _('Exemption has no central exam this exam year.')

# A. SCORE
    # 1. controleer score PR2015-12-27 PR2016-01-03
    if not err_list:
        if is_score:
            # this is already covered by 'no_practexam' and 'ey_no_centralexam'
            # 'PR2020-05-15 Corona: geen scores
            # strMsgText = "Er kunnen geen scores ingevuld worden in examenjaar " & ExkExamenjaar & "."
            #PR2015-12-27 debug: vervang komma door punt, anders wordt komma genegeerd

            input_number, err_list = calc_final.get_score_from_inputscore(input_value, max_score)
            if err_list:
                msg_list.extend(err_list)
            else:
                output_str = str(input_number)

# B. CIJFER
        elif 'grade' in examgradetype:
#  1. exit als CijferType VoldoendeOnvoldoende is en inputcijfer niet booIsOvg is

            if gradetype == c.GRADETYPE_00_NONE:
                msg_list.append(str(_("The grade type is not valid.")))
                msg_list.append(str(_("Grades cannot be entered.")))
            elif gradetype == c.GRADETYPE_02_CHARACTER:  # goed / voldoende / onvoldoende
                value_lc = input_value.lower()
                if value_lc in ('o', 'v', 'g'):
                    output_str = value_lc
                else:
                    msg_list.append(str(_("Grade '%(val)s' is not allowed.") % {'val': value_lc}))
                    msg_list.append(str(_("Grade can only be 'g', 'v' or 'o'.")))

            elif gradetype == c.GRADETYPE_01_NUMBER:
                output_str, err_list = calc_final.get_grade_number_from_input_str(input_value)
                if err_list:
                    msg_list.extend(err_list)
    if logging_on:
        logger.debug("output_str: " + str(output_str))
        if msg_list:
            logger.debug("msg_list: " + str(msg_list))

    return output_str, err_list
# - end of validate_update_grade


def validate_import_grade(student_dict, subj_dict, si_dict, examgradetype, grade_str):  # PR2021-12-11
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- validate_import_grade ----- ')

    is_se = (examgradetype in ("segrade", "srgrade"))
    is_score = 'score' in examgradetype
    is_grade = 'grade' in examgradetype

    gradetype = si_dict.get('gradetype')
    is_combi = si_dict.get('is_combi', False)
    extra_count_allowed = si_dict.get('extra_count_allowed', False)
    extra_nocount_allowed = si_dict.get('extra_nocount_allowed', False)
    has_practexam = si_dict.get('has_practexam', False)
    si_sr_allowed = si_dict.get('sr_allowed', False)
    si_max_reex = si_dict.get('max_reex', 1)
    si_no_thirdperiod = si_dict.get('no_thirdperiod', False)
    si_no_exemption_ce = si_dict.get('no_exemption_ce', False)

    # Note: value of examperiod is calculated from from examgradetype by get_examperiod_from_examgradetype
    # so there is no need to check if examgradetype is valid in this examperiod
# =======================================================================================

# - check if:
    #  - country is locked,
    #  - examyear is not found, not published or locked
    #  - school is not found, not same_school, not activated, or locked
    #  - department is not found, not in user allowed depbase or not in school_depbase
    #  these are taken care of in GradeUploadView > get_selected_ey_school_dep_from_usersetting

# - check if it is allowed to enter this examgradetype this examyear
    #  - examgradetype not allowed this examyear: already cheked in UploadImportGradeView with validate_grade_examgradetype_in_examyear
    #       examyear variables are no_practexam, sr_allowed, no_centralexam, no_thirdperiod

# - check if it is allowed to enter this examgradetype in this schemeitem
    err_list = validate_grade_examgradetype_in_schemeitem(examgradetype, si_dict, grade_str)

# - exit if examgradetype not allowed for this studsubject
    # checks if:
    #  - when srgrade: checks if student has sr
    #  - when exemption: checks if student has exemption
    #  - when reex: checks if student has reex
    #  - when reex03: checks if student has reex03
    if not err_list:
        err_list = validate_grade_examgradetype_in_studsubj(
            examgradetype=examgradetype,
            ss_has_sr=subj_dict.get('has_sr', False),
            ss_has_exemption=subj_dict.get('has_exemption', False),
            ss_has_reex=subj_dict.get('has_reex', False),
            ss_has_reex03=subj_dict.get('has_reex03', False),
        )

# - check if:
    #  - grade is already authorized, published or blocked
    if not err_list:
        this_item_cpt = str(_('This score')) if is_score else str(_('This grade'))
        err_list = validate_grade_published(subj_dict, this_item_cpt)
        if err_list:
            item_str = str(_('score')) if is_score else str(_('grade'))
            err_list.append('!!!' + str(_('You cannot enter a %(item_str)s.') % {'item_str': item_str}))


# - exit als dit vak bewijs van kennis heeft. Dan is invoer gegevens geblokkeerd.
    #  PR2010-06-10 mail Lorraine Wieske: kan geen PE cjfers corrigeren. Weghalen
    #  If KvHasBewijsKennis Then
    #   strMsgText = "Vak heeft Bewijs van Kennis en is daarom vergrendeld." & vbCrLf & "Ga naar Rapportages Ex6 om Bewijs van Kennis zo nodig te wissen."

    ######################################

    is_se_grade = (examgradetype == "segrade")
    is_sr = (examgradetype == "srgrade")
    is_pe = 'pe' in examgradetype
    is_pe_or_ce = (examgradetype in ("pescore", "pegrade", "cescore", "cegrade"))

    has_exemption = subj_dict.get('has_exemption', False)
    has_sr = subj_dict.get('has_sr', False)
    has_reex = subj_dict.get('has_reex', False)
    has_reex03 = subj_dict.get('has_reex03', False)

    # has_dyslexie = student.has_dyslexie
    iseveningstudent = student_dict.get('iseveningstudent', False)
    islexstudent = student_dict.get('islexstudent', False)

    # bis_exam = student.bis_exam
    partial_exam = student_dict.get('partial_exam', False)  # get certificate, only when evening- or lexstudent
    # deprecated, use partial_exam instead. Was:
    #   additional_exam = student_dict.get('additional_exam', False)  # when student does extra subject at a different school, possible in day/evening/lex school, only valid in the same examyear

    is_dayschool = student_dict.get('isdayschool', False)
    is_eveningschool = student_dict.get('iseveningschool', False)
    is_lexschool = student_dict.get('islexschool', False)

    # TODO make correct
    #exam = grade.exam
    ##scalelength_ce = exam.scalelength_ce if exam else None
    #scalelength_pe = exam.scalelength_pe if exam else None
    #scalelength_reex = exam.scalelength_reex if exam else None


# - reset output parameters
    output_str = None


#############

# - afterCorona: check if exemption has no_centralexam,  PR2020-12-16
        # skip when iseveningstudent school or islexschool
    #if msg_err is None:
    #    if examperiod_int == c.EXAMPERIOD_EXEMPTION:
    #        if is_pe_or_ce and no_exemption_ce:
    #            if not is_eveningstudent and not is_lexschool:
    #                msg_err = _('Exemption has no central exam this exam year.')


# A. SCORE
# 1. controleer score PR2015-12-27 PR2016-01-03
    if not err_list:
        if 'score' in examgradetype:
            # this is already covered by 'no_practexam' and 'no_centralexam'
            # 'PR2020-05-15 Corona: geen scores
            # strMsgText = "Er kunnen geen scores ingevuld worden in examenjaar " & ExkExamenjaar & "."

            # PR2015-12-27 debug: vervang komma door punt, anders wordt komma genegeerd
            # get max_score from exam

            max_score, nex_id, cesuur, nterm = None, None, None, None
            exam_id = subj_dict.get('exam_id')
            if exam_id:
                max_score = subj_dict.get('scalelength')
                nex_id = subj_dict.get('nex_id')
                cesuur = subj_dict.get('cesuur')
                nterm = subj_dict.get('nterm')

            input_number, err_lst = calc_final.get_score_from_inputscore(grade_str, max_score)
            if err_lst:
                err_list.extend(err_lst)
# B. CIJFER
        elif 'grade' in examgradetype:
#  /1. exit als CijferType VoldoendeOnvoldoende is en inputcijfer niet booIsOvg is

            if gradetype == c.GRADETYPE_00_NONE:
                err_list.append(str(_("The grade type is not valid.")))
                err_list.append(str(_("Grades cannot be entered.")))
            elif gradetype == c.GRADETYPE_02_CHARACTER:  # goed / voldoende / onvoldoende
                output_str, err_lst = calc_final.get_grade_char_from_input_str(grade_str)
                if err_lst:
                    err_list.extend(err_lst)
            elif gradetype == c.GRADETYPE_01_NUMBER:
                output_str, err_lst = calc_final.get_grade_number_from_input_str(grade_str)
                if err_lst:
                    err_list.extend(err_lst)
    if logging_on:
        if err_list:
            logger.debug("err_list: " + str(err_list))

    return output_str, err_list
# - end of validate_import_grade


def validate_grade_examgradetype_in_examyear(sel_examyear, examgradetype):  # PR2021-12-11 PR2021-12-25
    # functions checks if examyear has no_practexam, sr_allowed, no_centralexam, no_thirdperiod
    # values of examgradetype are:
    #   'exemsegrade', 'exemcegrade', 'segrade', 'srgrade', 'pescore', 'pegrade',
    #   'cescore', 'cegrade', 'reexscore', 'reexgrade', 'reex03score','reex03grade'

    # NIU: reex_combi_allowed
    # - Corona: reexamination not allowed for combination subjects, except when combi_reex_allowed
    #  'PR2020-05-15 Corona: herkansing wel mogelijk bij combivakken

    err_list = []
    if examgradetype == 'srgrade':
        if not sel_examyear.sr_allowed:
            err_list.append(str(_('Re-examination school exam is not allowed this exam year.')))
    else:
        if sel_examyear.no_centralexam:
            if examgradetype in ('pescore', 'pegrade', 'cescore', 'cegrade',
                                 'reexscore', 'reexgrade', 'reex03score', 'reex03grade'):
                err_list.append(str(_('This exam year has no central exams.')))
        else:
            if examgradetype in ('pescore', 'pegrade'):
                if sel_examyear.no_practexam:
                    err_list.append(str(_('This exam year has no practical exams.')))
            elif examgradetype in ('reex03score', 'reex03grade'):
                if sel_examyear.no_thirdperiod:
                    err_list.append(str(_('This exam year has no third exam period.')))

    return err_list
# - end of validate_grade_examgradetype_in_examyear


def validate_grade_examgradetype_in_schemeitem(examgradetype, si_dict, input_value):  # PR2021-12-11 PR2021-12-25
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- validate_grade_examgradetype_in_schemeitem ----- ')

    # NIU: reex_combi_allowed
    # - Corona: reexamination not allowed for combination subjects, except when combi_reex_allowed
    #  'PR2020-05-15 Corona: herkansing wel mogelijk bij combivakken

    err_list = []
    if examgradetype == 'srgrade':
        si_sr_allowed = si_dict.get('sr_allowed', False)
        if not si_sr_allowed:
            err_list.append(str(_('Re-examination school exam is not allowed for this subject.')))
    elif examgradetype == 'exemcegrade':
        # TODO: no_exemption_ce only applied to exam 2020, so doenst ake sense here. Fix it
        si_no_exemption_ce = si_dict.get('no_exemption_ce', False)
        if si_no_exemption_ce:
            err_list.append(str(_('This exemption has no cental exam.')))
    elif 'pe' in examgradetype:
        has_practexam = si_dict.get('has_practexam', False)
        if not has_practexam:
            err_list.append(str(_('This subject has no practical exam.')))
    elif 'reex' in examgradetype:
        si_max_reex = si_dict.get('max_reex', 1)
        if not si_max_reex:
            err_list.append(str(_('Re-examination is not allowed for this subject.')))
        elif 'reex03' in examgradetype:
            si_no_thirdperiod = si_dict.get('no_thirdperiod', False)
            if si_no_thirdperiod:
                err_list.append(str(_('This subject has no third exam period.')))

# - check if grade is allowed when combi subject
    if not err_list:
        if si_dict.get('is_combi', False):

            caption = None
            if 'reex' in examgradetype:
                # - reexamination not allowed for combination subjects, except when Corona
                caption = str(_('Re-examination')).lower()
            elif 'pe' in examgradetype:
                caption = str(_('Practical exam')).lower()
            elif 'ce' in examgradetype:
                caption = str(_('Central exam')).lower()
            if caption:
                err_list.append(str(_("A combination subject doesn't have a %(cpt)s.") % {'cpt': caption }))

# - check if weighing > 0
    if not err_list:

        is_se = (examgradetype in ("segrade", "srgrade"))
        se_ce_cpt = 'SE' if is_se else 'CE'
        grade_score_cpt = _('score') if 'score' in examgradetype else _('grade')

        weight_se = si_dict.get('weight_se', 0)
        weight_ce = si_dict.get('weight_ce', 0)

        if (is_se and not weight_se) or (not is_se and not weight_ce):
            # PR2022-01-02 debug: make it possible to delete grade, even when weight = 0, just in case it is necessary
                if input_value:
                    err_list.append(str(_('The %(se_ce_cpt)s weighing of this subject is zero.') % {'se_ce_cpt': se_ce_cpt}))
                    err_list.append(str(_('You cannot enter a %(item)s.') % {'item': grade_score_cpt}))

    return err_list
# - end of validate_grade_examgradetype_in_schemeitem


#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

def validate_grade_examgradetype_in_studsubj(examgradetype, ss_has_sr, ss_has_exemption, ss_has_reex, ss_has_reex03):  # PR2021-12-17
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- validate_grade_examgradetype_in_studsubj ----- ')

    # NIU: reex_combi_allowed
    # - Corona: reexamination not allowed for combination subjects, except when combi_reex_allowed
    #  'PR2020-05-15 Corona: herkansing wel mogelijk bij combivakken

    err_list = []

    if examgradetype == 'srgrade':
        #  sr_allowed in exam year is already checked in validate_grade_examgradetype_in_examyear
        #  sr_allowed in schemeitem is already checked in validate_grade_examgradetype_in_schemeitem
        if not ss_has_sr:
            caption = str(_("Re-examination school exam"))
            err_list.append(str(_('Candidate has no %(cpt)s for this subject.') % {'cpt': caption.lower()}))
            err_list.append(str(_("Go to the page 'Subjects' and tick off")))
            err_list.append(str(_("'%(cpt)s' of this subject.") % {'cpt': caption}))
    elif examgradetype in ('exemsegrade', 'exemcegrade'):
        if not ss_has_exemption:
            caption = str(_("Exemption"))
            err_list.append(str(_('Candidate has no %(cpt)s for this subject.') % {'cpt': caption.lower()}))
            err_list.append(str(_("Go to the page 'Subjects' and tick off")))
            err_list.append(str(_("'%(cpt)s' of this subject.") % {'cpt': caption}))

    elif examgradetype in ('reexscore', 'reexgrade'):
        if not ss_has_reex:
            caption = str(_("Re-examination"))
            err_list.append(str(_('Candidate has no %(cpt)s for this subject.') % {'cpt': caption.lower()}))
            err_list.append(str(_("Go to the page 'Subjects' and tick off")))
            err_list.append(str(_("'%(cpt)s' of this subject.") % {'cpt': caption}))

    elif examgradetype in ('reex03score', 'reex03grade'):
        if not ss_has_reex03:
            caption = str(_("Re-examination 3rd period"))
            err_list.append(str(_('Candidate has no %(cpt)s for this subject.') % {'cpt': caption.lower()}))
            err_list.append(str(_("Go to the page 'Subjects' and tick off")))
            err_list.append(str(_("'%(cpt)s' of this subject.") % {'cpt': caption}))

    return err_list
# - end of validate_grade_examgradetype_in_studsubj


def validate_exem_sr_reex_reex03_delete_allowed(studsubj_instance, field):  # PR2021-12-18
    # only called by update_studsubj
# - function checks
# if:
    #  - grade is already authorized, published or blocked
    #   se_blocked etc is True when Inspection has blocked the subject from gradelist, until it is changed
    #   when blocked is set True, published_id  and all auth_id will be erased, so the school can submit the grade again

    #  Note: 'se' and 'pe' don't have to be checked, because they have no 'is_se_cand" or 'is_pe_cand"

    exam_period = None
    examtype = None
    is_score = False
    if field == 'has_exemption':
        exam_period = c.EXAMPERIOD_EXEMPTION
        examtype = 'se'
        caption = str(_('This exemption')).lower()
    elif field == 'has_sr':
        exam_period = c.EXAMPERIOD_FIRST
        examtype = 'sr'
        caption = str(_('This re-examination school exam')).lower()
    elif field == 'has_reex':
        exam_period = c.EXAMPERIOD_SECOND
        examtype = 'ce'
        is_score = True
        caption = str(_('This re-examination')).lower()
    elif field == 'has_reex03':
        exam_period = c.EXAMPERIOD_THIRD
        examtype = 'ce'
        caption = str(_('This re-examination 3rd period')).lower()
    # NIU
    #elif field == 'has_practexam':
    #    exam_period = c.EXAMPERIOD_FIRST
    #    examtype = 'pe'
    #    caption = str(_('Practical exam')).lower()

# - check if grade of this exam_period exists
    grade_instance = stud_mod.Grade.objects.filter(
        studentsubject=studsubj_instance,
        examperiod=exam_period
    ).first()

    err_list = validate_grade_published_from_gradeinstance(grade_instance, examtype, is_score)
    if err_list:
        this_item_cpt = str(_('This score')).lower() if is_score else str(_('This grade')).lower()
        err_list.append(str(_('You cannot delete %(cpt)s.') % {'cpt': this_item_cpt}))

    return err_list
# --- end of validate_exem_sr_reex_reex03_delete_allowed



def validate_grade_published_from_gradeinstance(grade_instance, examtype, this_item_cpt):  # PR2021-12-18
    # examtype = 'se', 'sr', 'pe', 'ce'

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- validate_grade_published_from_gradeinstance -------')

    err_list = []
    if grade_instance:

        is_blocked = getattr(grade_instance, examtype + '_blocked', False)
        is_published = True if getattr(grade_instance, examtype + '_published_id') else False
        is_auth = True if getattr(grade_instance, examtype + '_auth1by_id') or \
                          getattr(grade_instance, examtype + '_auth2by_id') or \
                          getattr(grade_instance, examtype + '_auth3by_id') or \
                          getattr(grade_instance, examtype + '_auth4by_id') else False
        subj_dict = {'publ': is_published, 'bl': is_blocked, 'auth': is_auth}

        if logging_on:
            logger.debug('subj_dict: ' + str(subj_dict))

        err_list = validate_grade_published(subj_dict, this_item_cpt)

        if logging_on:
            logger.debug('............ err_list: ' + str(err_list))
    return err_list
# - end of validate_grade_published_from_gradeinstance


def validate_grade_published(subj_dict, this_item_cpt):  # PR2021-12-11 PR2021-12-26
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- validate_grade_published ----- ')

    #   se_blocked etc is True when Inspection has blocked the subject from gradelist, until it is changed
    #   when blocked is set True, published_id  and all auth_id will be erased, so the school can submit the grade again
    err_list = []

    # keys in subj_dict are: 'publ', 'bl', 'auth'. They are set in get_student_subj_grade_dict
    is_published = subj_dict.get('publ', False)
    is_blocked = subj_dict.get('bl', False)
    is_auth = subj_dict.get('auth', False)

    if logging_on:
        logger.debug('is_published: ' + str(is_published))
        logger.debug('is_blocked: ' + str(is_blocked))
        logger.debug('is_auth: ' + str(is_auth))

    if is_published or is_blocked or is_auth:
        publ_appr_cpt = str(_('Published')) if is_published or is_blocked else str(_('Approved'))
        publ_appr_cpt_lc = publ_appr_cpt.lower()

        err_list.append(str(_('%(cpt)s is already %(publ_appr_cpt)s.') % {'cpt': this_item_cpt, 'publ_appr_cpt': publ_appr_cpt_lc}))

    if logging_on:
        logger.debug('err_list: ' + str(err_list))

    return err_list
# - end of validate_grade_published

#######################################################


def get_student_subj_grade_dict(school, department, sel_examperiod, examgradetype, double_entrieslist,
                                student_id=None, studsubj_id=None):  # PR2021-12-10  PR2021-12-15 PR2022-01-04
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------------- get_student_subj_grade_dict  --------------------')
        logger.debug('double_entrieslist: ' + str(double_entrieslist))
        logger.debug('school.pk: ' + str(school.pk))
        logger.debug('department.pk: ' + str(department.pk))
        logger.debug('student_id: ' + str(student_id) + ' ' + str(type(student_id)))
        logger.debug('studsubj_id: ' + str(studsubj_id) + ' ' + str(type(studsubj_id)))

    # function uses idnumber as key, this way you can skip lookup student
    # don't add idnumber to list when it is found multiple times in upload list

    # function creates a dict with as key idnumber and as value a dict with key: subjbase_pk and value: subject_code
    # output:       dict: { idnumber: {student_id: id, subjectbase_pk: subject_code, ...}, ... }
    # '2004042204': {'stud_id': 3110, 133: 'ne', 134: 'en', 135: 'mm1', 136: 'lo', 138: 'pa', 141: 'wk', 142: 'ns1', 154: 'ns2', 155: 'sws'},

    ep_str = 'se' if 'se' in examgradetype else \
        'sr' if 'sr' in examgradetype else \
        'pe' if 'pe' in examgradetype else \
        'ce' if 'ce' in examgradetype else 'x'

    grade_str = 'grade' if 'grade' in examgradetype else \
                'score' if 'score' in examgradetype else 'x'

    value_str = "gr.%(ep_str)s%(grade_str)s AS value, CASE WHEN gr.%(ep_str)s_published_id IS NULL THEN FALSE ELSE TRUE END AS publ, gr.%(ep_str)s_blocked AS blocked," % {'ep_str': ep_str, 'grade_str': grade_str}
    auth_str = "CASE WHEN COALESCE (%(ep_str)s_auth1by_id, %(ep_str)s_auth2by_id, %(ep_str)s_auth3by_id, %(ep_str)s_auth4by_id) IS NULL THEN FALSE ELSE TRUE END AS auth," % {'ep_str': ep_str}

    student_subj_grade_dict = {}
    if value_str and ep_str:
        sql_keys = {'ey_id': school.examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk,
                    'ep': sel_examperiod, 'exgrtype': examgradetype}

        sql_grade_list = [
            "SELECT gr.id AS grade_id, gr.studentsubject_id AS studsubj_id, gr.examperiod,",
            value_str, auth_str,
            ]
        # add LEFT JOIN with  pe_exam_id when pe, with pce_exam_id when ce, else no join with exam
        if 'pe' in examgradetype or 'ce' in examgradetype:
            sql_grade_list.extend(("exam.id AS exam_id, exam.nex_id, exam.scalelength, exam.cesuur, exam.nterm",
                                   "FROM students_grade AS gr",
                                   "LEFT JOIN subjects_exam AS exam"))
            if 'pe' in examgradetype:
                sql_grade_list.append("ON (exam.id = gr.pe_exam_id)")
            else:
                sql_grade_list.append("ON (exam.id = gr.ce_exam_id)")

        else:
            sql_grade_list.extend(("NULL AS exam_id, NULL AS nex_id, NULL AS scalelength, NULL AS cesuur, NULL AS nterm",
                                    "FROM students_grade AS gr"))

        sql_grade_list.append("WHERE gr.examperiod = %(ep)s::INT AND NOT gr.tobedeleted")
            # Note: filter NOT studsubj.tobedeleted" in code, to prevent duplicate examperiod grade rows
            # PR2021-12-15 not true: adding grades only happens in page studsubj when adding subject (examperiod 1) or exemption, reex, reex03

        if studsubj_id:
            sql_keys['studsubj_id'] = studsubj_id
            sql_grade_list.append("AND gr.studentsubject_id = %(studsubj_id)s::INT")
        sub_grade_sql = ' '.join(sql_grade_list)

        if logging_on:
            with connection.cursor() as cursor:
                cursor.execute(sub_grade_sql, sql_keys)
                rows = cursor.fetchall()
            logger.debug('............================...................')
            logger.debug('sub_grade_sql: ' + str(sub_grade_sql))
            logger.debug('............================...................')
            for row in rows:
                logger.debug('row: ' + str(row))
            logger.debug('............================...................')

        sql_studsubj_list = ["WITH sub_grade_sql AS (" + sub_grade_sql + ")",
                             "SELECT studsubj.student_id, subj.base_id AS sjb_id, subjbase.code AS sjb_code,",
                             "studsubj.schemeitem_id AS ss_si_id,",  # studsubj.schemeitem_id

                             "studsubj.is_extra_nocount, studsubj.is_extra_counts,",
                             "studsubj.has_exemption, studsubj.has_sr,",
                             "studsubj.has_reex, studsubj.has_reex03,",

                             "sub_grade_sql.grade_id, sub_grade_sql.studsubj_id, sub_grade_sql.value,",
                             "sub_grade_sql.publ, sub_grade_sql.blocked, sub_grade_sql.auth,",
                             "sub_grade_sql.examperiod, sub_grade_sql.exam_id,",
                             "sub_grade_sql.nex_id, sub_grade_sql.scalelength, sub_grade_sql.cesuur, sub_grade_sql.nterm",
            "FROM students_studentsubject AS studsubj",
            "INNER JOIN sub_grade_sql ON (sub_grade_sql.studsubj_id = studsubj.id)",
            # was: "LEFT JOIN sub_grade_sql ON (sub_grade_sql.studsubj_id = studsubj.id)",
            #"LEFT JOIN students_grade AS gr ON (gr.studentsubject_id = studsubj.id)",
            "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
            "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
            "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
            "WHERE subj.examyear_id = %(ey_id)s::INT AND NOT studsubj.tobedeleted"
            # Note: filter NOT studsubj.tobedeleted" in code, to prevent duplicate examperiod grade rows
            # PR2021-12-15 not true: adding grades only happens in page studsubj when adding subject (examperiod 1) or exemption, reex, reex03
            ]

        if studsubj_id:
            # already added above: sql_keys['studsubj_id'] = studsubj_id
            sql_studsubj_list.append("AND studsubj.id = %(studsubj_id)s::INT")
        sub_sql = ' '.join(sql_studsubj_list)

        if logging_on:
            with connection.cursor() as cursor:
                cursor.execute(sub_sql, sql_keys)
                rows = cursor.fetchall()
            logger.debug('............++++++++++++....................')
            logger.debug('sub_sql: ' + str(sub_sql))
            logger.debug('............++++++++++++....................')
            for row in rows:
                logger.debug('row: ' + str(row))
            logger.debug('............++++++++++++....................')

        sql_list = ["WITH sub_sql AS (" + sub_sql + ")",
            "SELECT stud.idnumber, stud.id, stud.lastname, stud.firstname, stud.prefix,", # 5
            "stud.scheme_id, schm.name, stud.level_id, stud.sector_id,", # 4

            "stud.iseveningstudent, stud.islexstudent, stud.partial_exam,",  # 4
            "school.isdayschool, school.iseveningschool, school.islexschool,",  # 3

            "sub_sql.sjb_id, sub_sql.sjb_code,",  # 2
            "sub_sql.is_extra_nocount, sub_sql.is_extra_counts,",  # 2
            "sub_sql.has_exemption, sub_sql.has_sr, sub_sql.has_reex, sub_sql.has_reex03,",  # 4

            "sub_sql.ss_si_id, sub_sql.grade_id, sub_sql.studsubj_id, sub_sql.value,",  # 4
            "sub_sql.publ, sub_sql.blocked, sub_sql.auth,",  # 3
            "sub_sql.exam_id, sub_sql.nex_id, sub_sql.scalelength, sub_sql.cesuur, sub_sql.nterm",  # 5

            "FROM students_student AS stud",
            "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
            "LEFT JOIN subjects_scheme AS schm ON (schm.id = stud.scheme_id)",
            "LEFT JOIN sub_sql ON (sub_sql.student_id = stud.id)",
            "WHERE stud.school_id = %(sch_id)s::INT AND stud.department_id = %(dep_id)s::INT"]

        if student_id:
            sql_keys['st_id'] = student_id
            sql_list.append("AND stud.id = %(st_id)s::INT")

        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            grade_rows = cursor.fetchall()

        if logging_on:
            logger.debug('............###########....................')
            logger.debug('sql: ' + str(sql))
            logger.debug('............###########....................')
            for row in grade_rows:
                logger.debug('row: ' + str(row))
            logger.debug('............###########....................')

        if grade_rows:
            for row in grade_rows:
                # row: ('2003031202', 9240, 'Albertus', 'Lyanne Stephany', None, 372, 'ne')
                if logging_on:
                    logger.debug('row: ' + str(row))

# - get student_id, add as key to student_dict if it does not exists yet
                id_number = row[0]
                if not id_number:
                    if logging_on:
                        logger.debug('id_number is blank')
                elif double_entrieslist and id_number in double_entrieslist:
                    if logging_on:
                        logger.debug('id_number found in double_entrieslist: ' + str(id_number))
                else:
                    student_pk = row[1]
                    if id_number not in student_subj_grade_dict:
                        student_subj_grade_dict[id_number] = {
                            'stud_id': student_pk,
                            #'idnr': id_number,
                            'name': stud_fnc.get_lastname_firstname_initials(row[2], row[3], row[4]),
                            'schm_id': row[5],
                            'schm_name': row[6],
                            'lvl_id': row[7],
                            'sct_id': row[8],

                            'iseveningstudent': row[9],
                            'islexstudent': row[10],
                            'partial_exam': row[11],

                            'isdayschool': row[12],
                            'iseveningschool': row[13],
                            'islexschool': row[14],

                            'egt': examgradetype,
                            'ep': sel_examperiod
                        }

                    student_dict = student_subj_grade_dict[id_number]

    # - get subjectbase_pk, add as key to scheme_dict if it does not exists yet
                    # rows is ordered by sjtpbase.sequence
                    # therefore the schemeitem_subject with the lowest sequence will be added
                    # a schemeitem_subject can only occur once in the subject_dict

                    subjectbase_pk = row[15]
                    if subjectbase_pk not in student_dict:
                        student_dict[subjectbase_pk] = {
                            'sjb_id': subjectbase_pk,
                            'sjb_code': row[16],

                            'is_extra_nocount': row[17],
                            'is_extra_counts': row[18],
                            'has_exemption': row[19],
                            'has_sr': row[20],
                            'has_reex': row[21],
                            'has_reex03': row[22],

                            'ss_si_id': row[23],   # studsubj.schemeitem_id
                            'gr_id': row[24],
                            'ss_id': row[25],
                            'val': row[26],
                            'publ': row[27],
                            'bl': row[28],
                            'auth': row[29],

                            'exam_id': row[30],
                            'nex_id': row[31],
                            'scalelength': row[32],
                            'cesuur': row[33],
                            'nterm': row[34]
                        }
                    else:
                        # TODO error message when subject alreay exists (should not be possible
                        pass

    if logging_on:
        for id_nr, st_dict in student_subj_grade_dict.items():
            logger.debug( str(id_nr) + ': ' +  str(st_dict))

    """
     2003012406: {'st_id': 9340, 'idnr': '2003012406', 'name': 'Weyman, Natisha F.', 'schm_id': 555, 'lvl_id': 117, 'sct_id': 266, 'egt': 'segrade', 'ep': 1, 
                376: {'sjb_id': 376, 'sjb_code': 'cav', 'ss_si_id': 9816, gr_id': 68628, 'ss_id': 69168, 'val': '5.0', 'publ': None, 'bl': False, 'st': 0, 'auth': False, 'exam_id': None}, 
                373: {'sjb_id': 373, 'sjb_code': 'en', 'ss_si_id': 9816, 'gr_id': 68625, 'ss_id': 69165, 'val': '6.0', 'publ': None, 'bl': False, 'st': 0, 'auth': False, 'exam_id': None}, 
    """
    return student_subj_grade_dict
# - end of get_student_subj_grade_dict


def get_examperiod_from_examgradetype(examgradetype):
    # PR2021-12-17
    return c.EXAMPERIOD_EXEMPTION if 'exem' in examgradetype else \
        c.EXAMPERIOD_THIRD if 'reex03' in examgradetype else \
            c.EXAMPERIOD_SECOND if 'reex' in examgradetype else \
                c.EXAMPERIOD_FIRST
# - end of get_examperiod_from_examgradetype


def get_grade_db_field_from_examgradetype(examgradetype):
    return 'cescore' if examgradetype in ('reexscore', 'reex03score') else \
        'cegrade' if examgradetype in ('reexgrade', 'reex03grade') else \
            examgradetype
# - end of get_grade_db_field_from_examgradetype
