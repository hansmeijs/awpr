# PR2019-02-17
from django.utils.translation import pgettext_lazy, ugettext_lazy as _

from django.db.models import Q

from datetime import datetime
import logging
logger = logging.getLogger(__name__)

from awpr import constants as c
from awpr import settings as s

from students import models as stud_mod
from subjects import models as subj_mod


# ========  validate_studentsubjects  ======= PR2021-07-09
def validate_studentsubjects(student):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' -----  validate_studentsubjects  -----')
        logger.debug('student: ' + str(student))

# - store info of schemeitem in si_dict

    msg_list = []
    if student:
        stud_scheme = student.scheme
        if logging_on:
            logger.debug('stud_scheme: ' + str(stud_scheme))

        if stud_scheme is None:
            msg_list.append(_("No subject scheme found. Please enter the 'profiel' or 'leerweg' and 'sector'."))
            if logging_on:
                logger.debug('msg_list: ' + str(msg_list))
        else:

# ++++++++++++++++++++++++++++++++
# - get min max subjects and mvt from scheme
            scheme_dict = get_scheme_si_sjtp_dict(stud_scheme)
# ++++++++++++++++++++++++++++++++
# - get info from studsubjects
            doubles_pk_list = []
            doubles_code_list = []
            studsubj_dict = get_studsubj_dict(stud_scheme, student, doubles_pk_list, msg_list)
            doubles_pk_len = len(doubles_pk_list)
            if doubles_pk_len:
                subject_code_dict = scheme_dict.get('subj_code')
                for pk_int in doubles_pk_list:
                    doubles_code_list.append(subject_code_dict.get(pk_int, '-'))
                display_str = convert_code_list_to_display_str(doubles_code_list)
                if doubles_pk_len == 1:
                    msg_list.append(''.join(
                        ("<li>",
                         str(_("The subject %(list)s occurs twice and must be deleted.") % {'list': display_str}),
                         "<br>",
                         str(_("It will be disregarded in the rest of the validation.")),
                         "</li>")))
                else:
                    msg_list.append(''.join((
                        "<li>",
                        str(_("The subjects %(list)s occur multiple times and must be deleted.") % {'list': display_str}),
                        "<br>",
                        str(_("They will be disregarded in the rest of the validation.")),
                        "</li>") ))

            if logging_on:
                logger.debug('scheme_dict: ' + str(scheme_dict))
                logger.debug('studsubj_dict: ' + str(studsubj_dict))

# -------------------------------
# - check required subjects
            validate_required_subjects(scheme_dict, studsubj_dict, msg_list)

# - check total amount of subjects
            validate_amount_subjects('subject', scheme_dict, studsubj_dict, msg_list)

# - check amount of mvt and combi subjects
            validate_amount_subjects('mvt', scheme_dict, studsubj_dict, msg_list)
            validate_amount_subjects('combi', scheme_dict, studsubj_dict, msg_list)

# - check amount of subjects per subjecttype
            validate_amount_subjecttype_subjects(scheme_dict, studsubj_dict, msg_list)

    msg_html = None
    if len(msg_list):

        msg_str = ''.join(( '<h6>', str(_('The composition of the subjects is not correct:')), '</h5>', "<ul class='manual_bullet'>" ))
        msg_list.insert(0, msg_str)
        msg_list.append("</ul>")
        msg_html = ''.join(msg_list)

    return msg_html
# --- end of validate_studentsubjects


def validate_required_subjects(scheme_dict, studsubj_dict, msg_list):
    # - validate ampount of subjects PR2021-07-10

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  validate_required_subjects  -----')

    scheme_req_list = scheme_dict.get('req_list', [])
    studsubj_req_list = studsubj_dict.get('req_list', [])

    subject_code_dict = scheme_dict.get('subj_code')

    missing_req_list = []
    if len(scheme_req_list):
        for i, req_pk in enumerate(scheme_req_list):
            if req_pk not in studsubj_req_list:
                req_code = subject_code_dict[req_pk]
                missing_req_list.append(req_code)

    msg_txt = None
    missing_req_len = len(missing_req_list)
    if missing_req_len:
        if missing_req_len == 1:
            req_code = missing_req_list[0]
            msg_txt = _("The required subject '%(code)s' is missing.") % {'code': req_code}
        else:
            req_code_list = convert_code_list_to_display_str(missing_req_list)
            msg_txt = _("The required subjects %(code)s are missing.") % {'code': req_code_list}

    if msg_txt:
        msg_html = ''.join(('<li>', msg_txt, '</li>'))
        msg_list.append(msg_html)

    if logging_on:
        logger.debug('msg_txt: ' + str(msg_txt))


def convert_code_list_to_display_str(code_list):
    # function converts ['wk', 'en' 'pa'] in  "'en', 'pa' and 'wk'" PR2021-07-20
    display_str = ''
    if code_list:
        list_len = len(code_list)
        code_list.sort()
        for x in range(0, list_len):  # range(start_value, end_value, step), end_value is not included!
            if x == 0:
                join_str = ''
            elif x == (list_len - 1):
                join_str = str(_(' and '))
            else:
                join_str = ', '
            display_str += ''.join((join_str, "'", code_list[x], "'"))

    return display_str


def validate_amount_subjecttype_subjects(scheme_dict, studsubj_dict, msg_list):
    # - validate amount of subjects PR2021-07-11

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  validate_amount_subjecttype_subjects  -----')

    scheme_sjtp_dict = scheme_dict.get('sjtp_dict')
    studsubj_sjtp_dict = studsubj_dict.get('sjtp_dict')
    if scheme_sjtp_dict:
        for scheme_sjtp_dict_pk, scheme_item_dict in scheme_sjtp_dict.items():
            if logging_on:
                logger.debug('scheme_item_dict: ' + str(scheme_item_dict))
            # scheme_item_dict: {'name': 'Gemeensch.', 'min_subjects': 2, 'max_subjects': 4,
            # 'min_extra_nocount': 2, 'max_extra_nocount': 4, 'min_extra_counts': 2, 'max_extra_counts': 4,
            # 'min_elective_combi': 2, 'max_elective_combi': 4}

            sjtp_name = scheme_item_dict.get('name', '')
            min_subjects = scheme_item_dict.get('min_subjects')
            max_subjects = scheme_item_dict.get('max_subjects')

            min_extra_nocount = scheme_item_dict.get('min_extra_nocount')
            max_extra_nocount = scheme_item_dict.get('max_extra_nocount')

            min_extra_counts = scheme_item_dict.get('min_extra_counts')
            max_extra_counts = scheme_item_dict.get('max_extra_counts')

            min_elective_combi = scheme_item_dict.get('min_elective_combi')
            max_elective_combi = scheme_item_dict.get('max_elective_combi')

            if logging_on:
                logger.debug('----------------: ' + str(sjtp_name))
                logger.debug('min_subjects: ' + str(min_subjects))
                logger.debug('max_subjects: ' + str(max_subjects))

            subject_count = 0
            if scheme_sjtp_dict_pk in studsubj_sjtp_dict:
                studsubj_item_dict = studsubj_sjtp_dict.get(scheme_sjtp_dict_pk)
                # studsubj_item_dict: {'min': 2, 'max': 4, 'name': 'Gemeensch.',
                #                       'subj_list': [1026, 999, 998, 1002, 1027],
                #                       'nocount_list': [], 'counts_list': [], 'elective_list': []}
                subj_list = studsubj_item_dict.get('subj_list')
                nocount_list = studsubj_item_dict.get('nocount_list', [])
                counts_list = studsubj_item_dict.get('counts_list', [])
                elective_list = studsubj_item_dict.get('elective_list', [])
                subject_count = len(subj_list)

                if logging_on:
                    logger.debug('----------------: ' + str(sjtp_name))
                    logger.debug('studsubj_item_dict: ' + str(studsubj_item_dict))

                    logger.debug('subj_list: ' + str(subj_list))
                    logger.debug('nocount_list: ' + str(nocount_list))
                    logger.debug('counts_list: ' + str(counts_list))
                    logger.debug('elective_list: ' + str(elective_list))
                    logger.debug('subject_count: ' + str(subject_count))

            caption = _('subject')
            captions = _('subjects')

            validate_minmax_count('sjtp', scheme_dict, subject_count, caption, captions, sjtp_name, min_subjects, max_subjects, msg_list)

# - end of validate_amount_subjecttype_subjects


def validate_amount_subjects(field, scheme_dict, studsubj_dict, msg_list):
    # - validate amount of subjects PR2021-07-10

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  validate_amount_subjects  -----')
        logger.debug('field: ' + str(field))

    caption, captions = '', ''

    msg_html = None
    min_subj_key, max_subj_key, subject_list_key = '', '', ''
    if field == 'subject':
        min_subj_key = 'min_subj'
        max_subj_key = 'max_subj'
        subject_list_key = 'subject_list'
        caption = _('subject')
        captions = _('subjects')
    elif field == 'mvt':
        min_subj_key = 'min_mvt'
        max_subj_key = 'max_mvt'
        subject_list_key = 'mvt_list'
        caption = _('MVT subject')
        captions = _('MVT subjects')
    elif field == 'core':
        min_subj_key = 'min_core'
        max_subj_key = 'max_core'
        subject_list_key = 'core_list'
        caption = _('core subject')
        captions = _('core subjects')
    elif field == 'combi':
        min_subj_key = 'min_combi'
        max_subj_key = 'max_combi'
        subject_list_key = 'combi_list'
        caption = _('combination subject')
        captions = _('combination subjects')

    min_subj = scheme_dict.get(min_subj_key)
    max_subj = scheme_dict.get(max_subj_key)
    studsubj_list = studsubj_dict.get(subject_list_key)

    subject_count = len(studsubj_list) if studsubj_list else 0

    if subject_count == 0:
        msg_count = _('There are no %(cpt)s.') % {'cpt': captions}
    elif subject_count == 1:
        msg_count = _('There is 1 %(cpt)s.') % {'cpt': caption}
    else:
        msg_count = _('There are %(val)s %(cpt)s.') % {'cpt': captions, 'val': subject_count}

    if logging_on:
        logger.debug('msg_count: ' + str(msg_count))
        logger.debug('studsubj_list: ' + str(studsubj_list))

    msg_txt, msg_available = '', ''
    if min_subj and max_subj and min_subj == max_subj:
        if subject_count != min_subj:
            msg_txt = _("The amount of %(cpt)s must be %(max)s.") % {'cpt': captions, 'max': max_subj}
    elif min_subj or max_subj:
        minmax_txt = None
        minmax_val = None
        if min_subj and subject_count < min_subj:
            minmax_txt = pgettext_lazy('NL_minimale', 'minimum')
            minmax_val = min_subj
            # - add available list , not when field = 'subject'
            if field != 'subject':
                scheme_pk_list = scheme_dict.get(subject_list_key)
                subject_code_dict = scheme_dict.get('subj_code')

                available_list = []
                if logging_on:
                    logger.debug('scheme_pk_list: ' + str(scheme_pk_list))

                for subj_pk in scheme_pk_list:
                    if logging_on:
                        logger.debug('subj_pk: ' + str(subj_pk))

                    code = subject_code_dict[subj_pk]
                    if code not in available_list:
                        available_list.append(code)

                if logging_on:
                    logger.debug('available_list: ' + str(available_list))

                available_len = len(available_list)
                if available_len:
                    if available_len == 1:
                        msg_available = _("The %(cpt)s is: '%(list)s'.") % {'cpt': caption, 'list': available_list}
                    else:
                        available_list.sort()
                        if logging_on:
                            logger.debug('available_list.sort: ' + str(available_list))
                        list_str = ''
                        for x in range(0, available_len):  # range(start_value, end_value, step), end_value is not included!
                            if x == 0:
                                join_str = ''
                            elif x == (available_len - 1):
                                join_str = str(_(' and '))
                            else:
                                join_str = ', '
                            list_str += ''.join((join_str, "'", available_list[x], "'"))
                        msg_available = _("The %(cpt)s are: %(list)s.") % {'cpt': captions, 'list': list_str}
                        if logging_on:
                            logger.debug('list_str: ' + str(list_str))
                            logger.debug('msg_available: ' + str(msg_available))

        if max_subj and subject_count > max_subj:
            minmax_txt = pgettext_lazy('NL_maximale', 'maximum')
            minmax_val = max_subj

        if minmax_txt:
            msg_txt = _("The %(minmax_txt)s amount of %(cpt)s is %(minmax_val)s.") \
                      % {'cpt': captions, 'minmax_txt': minmax_txt, 'minmax_val': minmax_val}

            #msg_available += _("<br>Available MVT subjects are: %(list)s.") % {'list': 'min_mvt'}
    if msg_txt:
        msg_html = ''.join(('<li>', msg_count, ' ', msg_txt, ' ', msg_available, '</li>'))
        msg_list.append(msg_html)

    if logging_on:
        logger.debug('msg_txt: ' + str(msg_txt))
        logger.debug('msg_list: ' + str(msg_html))
# - validate_amount_subjects


def validate_minmax_count(field, scheme_dict, subject_count, caption, captions, sjtp_name, min_subj, max_subj, msg_list):

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  validate_minmax_count  -----')
        logger.debug('subject_count: ' + str(subject_count))

    if subject_count == 0:
        msg_count = _('There are no %(cpt)s') % {'cpt': captions}
    elif subject_count == 1:
        msg_count = _('There is 1 %(cpt)s') % {'cpt': caption}
    else:
        msg_count = _('There are %(val)s %(cpt)s') % {'cpt': captions, 'val': subject_count}

    if sjtp_name:
        msg_count = ''.join((str(msg_count), str(_(' with character ')), "'", sjtp_name, "'"))
    else:
        msg_count += '.'

    if logging_on:
        logger.debug('msg_count: ' + str(msg_count))

    msg_txt, msg_available = '', ''
    if min_subj and max_subj and min_subj == max_subj:
        if subject_count != min_subj:
            msg_txt = _("The amount of %(cpt)s must be %(max)s.") % {'cpt': captions, 'max': max_subj}
    elif min_subj or max_subj:
        minmax_txt = None
        minmax_val = None
        if min_subj and subject_count < min_subj:
            minmax_txt = pgettext_lazy('NL_minimale', 'minimum')
            minmax_val = min_subj
            # - add available list , not when field = 'subject'
            if field != 'subject':
                subject_code_dict = scheme_dict.get('subj_code')
                available_list = []
                for subj_pk, subject_code in subject_code_dict.items():
                    if logging_on:
                        logger.debug('subj_pk: ' + str(subj_pk))
                        logger.debug('subject_code: ' + str(subject_code))

                    if subject_code not in available_list:
                        available_list.append(subject_code)

                if logging_on:
                    logger.debug('available_list: ' + str(available_list))

                available_len = len(available_list)
                if available_len:
                    if available_len == 1:
                        msg_available = _("The %(cpt)s is: '%(list)s'.") % {'cpt': caption, 'list': available_list}
                    else:
                        available_list.sort()
                        if logging_on:
                            logger.debug('available_list.sort: ' + str(available_list))
                        list_str = ''
                        for x in range(0, available_len):  # range(start_value, end_value, step), end_value is not included!
                            if x == 0:
                                join_str = ''
                            elif x == (available_len - 1):
                                join_str = str(_(' and '))
                            else:
                                join_str = ', '
                            list_str += ''.join((join_str, "'", available_list[x], "'"))
                        msg_available = _("The %(cpt)s are: %(list)s.") % {'cpt': captions, 'list': list_str}
                        if logging_on:
                            logger.debug('list_str: ' + str(list_str))
                            logger.debug('msg_available: ' + str(msg_available))

        if max_subj and subject_count > max_subj:
            minmax_txt = pgettext_lazy('NL_maximale', 'maximum')
            minmax_val = max_subj

        if minmax_txt:
            msg_txt = _("The %(minmax_txt)s amount of %(cpt)s is %(minmax_val)s.") \
                      % {'cpt': captions, 'minmax_txt': minmax_txt, 'minmax_val': minmax_val}

            #msg_available += _("<br>Available MVT subjects are: %(list)s.") % {'list': 'min_mvt'}
    if msg_txt:
        msg_html = ''.join(('<li>', msg_count, ' ', msg_txt, ' ', msg_available, '</li>'))
        msg_list.append(msg_html)
# - end of validate_minmax_count


def get_scheme_si_sjtp_dict(scheme):
# - get info from scheme, subjecttypes and schemeitems PR2021-07-10
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  get_scheme_si_sjtp_dict  -----')
        logger.debug('scheme: ' + str(scheme))

# - get min max subjects and mvt from scheme
    schemename = getattr(scheme, 'name')
    min_subj = getattr(scheme, 'min_subjects')
    max_subj = getattr(scheme, 'max_subjects')
    min_mvt = getattr(scheme, 'min_mvt')
    max_mvt = getattr(scheme, 'max_mvt')
    min_combi = getattr(scheme, 'min_combi')
    max_combi = getattr(scheme, 'max_combi')

# - get info from subjecttypes
    sjtp_dict = {}
    sjtps = subj_mod.Subjecttype.objects.filter(scheme=scheme)
    for sjtp in sjtps:
        sjtp_pk = sjtp.pk
        if sjtp_pk not in sjtp_dict:
            sjtp_dict[sjtp_pk] = {'name': sjtp.name,
                'min_subjects': sjtp.min_subjects,
                'max_subjects': sjtp.max_subjects,

                'min_extra_nocount': sjtp.min_extra_nocount,
                'max_extra_nocount': sjtp.max_extra_nocount,

                'min_extra_counts': sjtp.min_extra_counts,
                'max_extra_counts': sjtp.max_extra_counts,

                'min_elective_combi': sjtp.min_elective_combi,
                'max_elective_combi': sjtp.max_elective_combi,
            }

# - get info from schemeitems
    req_list = []
    combi_list = []
    mvt_list = []
    core_list = []

    subject_code = {}

    sis = subj_mod.Schemeitem.objects.filter(scheme=scheme)
    for si in sis:
        subj_pk = si.subject.pk
        subj_code = si.subject.base.code
        subject_code[subj_pk] = subj_code

        if si.is_mandatory:
            req_list.append(subj_pk)
        if si.is_combi:
            combi_list.append(subj_pk)
        if si.is_mvt:
            mvt_list.append(subj_pk)
        if si.is_core_subject:
            core_list.append(subj_pk)

    scheme_dict = {
        'schemename': schemename,
        'min_subj': min_subj,
        'max_subj': max_subj,
        'min_mvt': min_mvt,
        'max_mvt': max_mvt,
        'min_combi': min_combi,
        'max_combi': max_combi,

        'sjtp_dict': sjtp_dict,

        'req_list': req_list,
        'combi_list': combi_list,
        'mvt_list': mvt_list,
        'core_list': core_list,

        'subj_code': subject_code
    }
    return scheme_dict
# - end of get_scheme_si_sjtp_dict


def get_studsubj_dict(stud_scheme, student, doubles_list, msg_list):
    # - get info from student subjects PR2021-07-10
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  get_studsubj_dict  -----')
        logger.debug('scheme: ' + str(student))

    subject_list = []

    sjtp_dict = {}

    req_list = []
    combi_list = []
    mvt_list = []
    core_list = []

# - create dict with studentsubject values that are used in validator
    rows = stud_mod.Studentsubject.objects.filter(
        student=student,
        deleted=False
    )
    if rows is None:
        msg_list.append(_("Candidate has no subjects."))
    else:

        for studsubj in rows:
            if logging_on:
                logger.debug('studsubj: ' + str(studsubj))
                logger.debug('studsubj.schemeitem.subject.name: ' + str(studsubj.schemeitem.subject.name))
            si = studsubj.schemeitem
            if si.scheme_id != stud_scheme.pk:
                value = si.subject.name
                msg_list.append(_("Subject '%(val)s' does not belong to this subject scheme.") % {'val': value})
            else:

# - put subject.pk in subject_list, or in doubles_list when already exists
                subj_pk = si.subject.pk

    # if subject already exists: skip double from other checks (double should not be possible)
                if subj_pk in subject_list:
                    doubles_list.append(subj_pk)
                else:
                    subject_list.append(subj_pk)

            # add subject to subjecttype list
                    subjecttype = si.subjecttype
                    sjtp_pk = subjecttype.pk
                    if sjtp_pk not in sjtp_dict:
                        sjtp_dict[sjtp_pk] = {
                            'min': subjecttype.min_subjects,
                            'max': subjecttype.max_subjects,
                            'name': subjecttype.name,
                            'subj_list': [],
                            'nocount_list': [],
                            'counts_list': [],
                            'elective_list': [],

                        }
                    dict = sjtp_dict.get(sjtp_pk)

                    subj_list = dict.get('subj_list')
                    subj_list.append(subj_pk)

                    if studsubj.is_extra_nocount:
                        nocount_list = dict.get('nocount_list')
                        nocount_list.append(subj_pk)
                    if studsubj.is_extra_counts:
                        counts_list = dict.get('counts_list')
                        counts_list.append(subj_pk)
                    if studsubj.is_elective_combi:
                        elective_list = dict.get('elective_list')
                        elective_list.append(subj_pk)

                    if si.is_mandatory:
                        req_list.append(subj_pk)
                    if si.is_combi:
                        combi_list.append(subj_pk)
                    if si.is_mvt:
                        mvt_list.append(subj_pk)
                    if si.is_core_subject:
                        core_list.append(subj_pk)

    if logging_on:
        logger.debug('subject_list: ' + str(subject_list))
        logger.debug('doubles_list: ' + str(doubles_list))

    studsubj_dict = {
        'subject_list': subject_list,
        'doubles_list': doubles_list,

        'sjtp_dict': sjtp_dict,

        'req_list': req_list,
        'combi_list': combi_list,
        'mvt_list': mvt_list,
        'core_list': core_list
    }

    if logging_on:
        logger.debug('studsubj_dict: ' + str(studsubj_dict))
    return studsubj_dict

# - end of get_studsubj_dict


#######################################################################################

# TODO from tsa, to be adapted
def validate_namelast_namefirst(namelast, namefirst, company, update_field, msg_dict, this_pk=None):
    # validate if employee already_exists in this company PR2019-03-16
    # from https://stackoverflow.com/questions/1285911/how-do-i-check-that-multiple-keys-are-in-a-dict-in-a-single-pass
    # if all(k in student for k in ('idnumber','lastname', 'firstname')):
    #logger.debug(' --- validate_namelast_namefirst --- ' + str(namelast) + ' ' + str(namefirst) + ' ' + str(this_pk))

    msg_err_namelast = None
    msg_err_namefirst = None
    has_error = False
    if not company:
        msg_err_namelast = _("No company.")
    else:
        # first name can be blank, last name not
        if not namelast:
            msg_err_namelast = _("Last name cannot be blank.")
    if msg_err_namelast is None:
        if len(namelast) > c.NAME_MAX_LENGTH:
            msg_err_namelast = _("Last name is too long.") + str(c.NAME_MAX_LENGTH) + _(' characters or fewer.')
        elif namefirst:
            if len(namefirst) > c.NAME_MAX_LENGTH:
                msg_err_namefirst = _("First name is too long.") + str(c.NAME_MAX_LENGTH) + _(' characters or fewer.')

        # check if first + lastname already exists
        if msg_err_namelast is None and msg_err_namefirst is None:
            if this_pk:
                name_exists = m.Employee.objects.filter(namelast__iexact=namelast,
                                                      namefirst__iexact=namefirst,
                                                      company=company
                                                      ).exclude(pk=this_pk).exists()
            else:
                name_exists = m.Employee.objects.filter(namelast__iexact=namelast,
                                                      namefirst__iexact=namefirst,
                                                      company=company
                                                      ).exists()
            if name_exists:
                new_name = ' '.join([namefirst, namelast])
                msg_err = str(_("%(cpt)s '%(val)s' already exists.") % {'cpt': _('Name'), 'val': new_name})
                if update_field == 'namelast':
                    msg_err_namelast = msg_err
                elif update_field == 'namefirst':
                    msg_err_namefirst = msg_err

    if msg_err_namelast or msg_err_namefirst:
        has_error = True
        if msg_err_namelast:
            msg_dict['err_namelast'] = msg_err_namefirst
        if msg_err_namefirst:
            msg_dict['err_namefirst'] = msg_err_namefirst

    return has_error


def employee_email_exists(email, company, this_pk = None):
    # validate if email address already_exists in this company PR2019-03-16

    msg_dont_add = None
    if not company:
        msg_dont_add = _("No company.")
    elif not email:
        msg_dont_add = _("The email address cannot be blank.")
    elif len(email) > c.NAME_MAX_LENGTH:
        msg_dont_add = _('The email address is too long.') + str(c.CODE_MAX_LENGTH) + _(' characters or fewer.')
    else:
        if this_pk:
            email_exists = m.Employee.objects.filter(email__iexact=email,
                                                  company=company
                                                  ).exclude(pk=this_pk).exists()
        else:
            email_exists = m.Employee.objects.filter(email__iexact=email,
                                                  company=company).exists()
        if email_exists:
            msg_dont_add = _("This email address already exists.")

    return msg_dont_add



# ++++++++++++ Validations  +++++++++++++++++++++++++


# ========  get_double_entrieslist_from_uploadfile  ======= PR2021-06-14
def get_double_entrieslist_from_uploadfile(data_list):
    # function returns list of trimmed idnumbers without dots that occur multiple times in data_list
    double_entrieslist = []
    id_number_list = []
    for data_dict in data_list:
        id_number = data_dict.get('idnumber')
        if id_number:
            id_number_nodots = id_number.strip().replace('.', '')
            if id_number_nodots not in id_number_list:
                id_number_list.append(id_number_nodots)
            else:
                double_entrieslist.append(id_number_nodots)
    return double_entrieslist


# ========  validate_double_entries_in_uploadfile  ======= PR2021-06-19
def validate_double_entries_in_uploadfile(id_number_nodots, double_entrieslist, error_list):

    has_error = False
    if id_number_nodots and double_entrieslist:
        if id_number_nodots in double_entrieslist:
            has_error = True
            error_list.append(_("%(fld)s '%(val)s' is found multiple times in this upload file.") \
                      % {'fld': _("The ID-number"), 'val': id_number_nodots})
    return has_error


# ========  validate_name_idnumber_length  ======= PR2021-06-19
def validate_name_idnumber_length(id_number_nodots, lastname_stripped, firstname_stripped, prefix_stripped, error_list):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------- validate_name_idnumber_length ----------- ')

    has_error = False
    if not id_number_nodots:
        has_error = True
        error_list.append(_('%(fld)s cannot be blank.') % {'fld': _("The ID-number")})
    elif len(id_number_nodots) > c.MAX_LENGTH_IDNUMBER:
        has_error = True
        error_list.append(_("%(fld)s '%(val)s' is too long, maximum %(max)s characters.") \
                    % {'fld': _("The ID-number"), 'val': id_number_nodots, 'max': c.MAX_LENGTH_IDNUMBER})

    if not lastname_stripped:
        has_error = True
        error_list.append(_('%(fld)s cannot be blank.') % {'fld': _("The last name")})
    elif len(lastname_stripped) > c.MAX_LENGTH_FIRSTLASTNAME:
        has_error = True
        error_list.append(_("%(fld)s '%(val)s' is too long, maximum %(max)s characters.") \
                    % {'fld': _("The last name"), 'val': lastname_stripped, 'max': c.MAX_LENGTH_FIRSTLASTNAME})

    if not firstname_stripped:
        has_error = True
        error_list.append(_('%(fld)s cannot be blank.') % {'fld': _("The first name")})
    elif len(firstname_stripped) > c.MAX_LENGTH_FIRSTLASTNAME:
        has_error = True
        error_list.append(_("%(fld)s '%(val)s' is too long, maximum %(max)s characters.") \
                    % {'fld': _("The first name"), 'val': firstname_stripped, 'max': c.MAX_LENGTH_FIRSTLASTNAME})

    if len(prefix_stripped) > c.MAX_LENGTH_10:
        has_error = True
        error_list.append(_("%(fld)s '%(val)s' is too long, maximum %(max)s characters.") \
                          % {'fld': _("The prefix"), 'val': prefix_stripped, 'max': c.MAX_LENGTH_10})

    if logging_on:
        logger.debug('has_error: ' + str(has_error))
        logger.debug('error_list: ' + str(error_list))

    return has_error
# - end of validate_name_idnumber_length


# +++++++++++++++++++++++++++++++++++++

def validate_idnumber(id_str):
    # logger.debug('validate_idnumber: ' + id_str)
    # validate idnumber, convert to string without dots PR2019-02-17
    msg_dont_add = None
    idnumber_clean = None
    birthdate = None
    if id_str:
        if len(id_str) == 13:
            if id_str[4:5] == '.' and id_str[7:8] == '.' and id_str[10:11] == '.':
                id_str = id_str.replace('.', '')
                    # PR2019-02-17 was:
                    # strip all non-numeric characters from string:
                    # from https://docs.python.org/2/library/re.html
                    #  re.sub(pattern, repl, string, count=0, flags=0)
                    # Reeplaces the leftmost non-overlapping occurrences
                    # of pattern in string by the replacement repl.
                    # If the pattern isn’t found, string is returned unchanged
                    # idnumber_stripped = re.sub("[^0-9]", "", id_str
        if id_str:
            if len(id_str) == 10: # PR2019-02-18 debug: object of type 'NoneType' has no len(), added: if id_str
                # logger.debug('id_str: ' + id_str + ' len: ' + str(len(id_str)))
                date_str = id_str[:8]
                # logger.debug('date_str: ' + date_str + ' len: ' + str(len(date_str)))
                if date_str.isnumeric():
                    birthdate = calc_bithday_from_id(date_str)
                    # logger.debug('birthdate: ' + str( birthdate) + ' type: ' + str(type(birthdate)))

            if birthdate is not None:
                idnumber_clean = id_str
            else:
                msg_dont_add = _("ID number not valid.")

    else:
        msg_dont_add = _("ID number not entered.")

    return idnumber_clean, birthdate, msg_dont_add


def idnumber_already_exists(idnumber_stripped, school):
    # validate if idnumber already exist in this school and examyear PR2019-02-17
    msg_dont_add = None
    if not idnumber_stripped:
        msg_dont_add =_("ID number not entered.")
    elif Student.objects.filter(
                idnumber__iexact=idnumber_stripped,  # _iexact filters a Case-insensitive exact match.
                school=school).exists():
            msg_dont_add =_("ID number already exists.")
    return msg_dont_add


def studentname_already_exists(lastname, firstname, school):
    # validate if student name already exists in this school and examyear PR2019-02-17
    # from https://stackoverflow.com/questions/1285911/how-do-i-check-that-multiple-keys-are-in-a-dict-in-a-single-pass
                    # if all(k in student for k in ('idnumber','lastname', 'firstname')):
    msg_dont_add = None
    if not lastname:
        if not firstname:
            msg_dont_add = _("First name and last name not entered.")
        else:
            msg_dont_add = _("Last name not entered.")
    else:
        if not firstname:
            msg_dont_add = _("First name not entered.")
        else:
            if Student.objects.filter(
                    lastname__iexact=lastname,
                    firstname__iexact=firstname,
                    school=school).exists():
                msg_dont_add =_("Student name already exists.")
    return msg_dont_add


def examnumber_already_exists(examnumber, school):
    # validate if examnumber already exists in this school and examyear PR2019-02-19
    msg_dont_add = None
    if not examnumber:
        msg_dont_add = _("Exam number not entered.")
    else:
        if Student.objects.filter(
                examnumber__iexact=examnumber,
                school=school).exists():
            msg_dont_add =_("Exam number already exists.")
    return msg_dont_add


def validate_gender(value):
    # validate gender, convert to string 'M' or 'V' PR2019-02-18
    clean_gender = c.GENDER_NONE
    msg_text = None
    if value:
        valid = False
        if len(value) == 1:
            value_upper = value.upper()
            if value_upper == 'M': # was if value_upper in ('M', 'F',):
                clean_gender = c.GENDER_MALE
                valid = True
            elif value_upper in ('V', 'F',):
                clean_gender = c.GENDER_FEMALE
                valid = True
        if not valid:
            msg_text = _('Gender \'"%s"\' is not allowed.' % value)
    return clean_gender, msg_text


def calc_bithday_from_id(id_str):
    # PR2019-02-18
    # id_str_stripped is sedulanummer: format:: YYYYMMDD

    date_dte = None

    if len(id_str) == 8:
# ---   create date_str (format: yyyy-mm-dd)
        date_str = id_str[:4] + "-" + id_str[4:6] + "-" + id_str[6:8]
# ---   convert to date
        try:
            date_dte = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            # logger.debug('date_dte=' + str(date_dte) + ' type: ' + str(type(date_dte)))
        except:
            pass
    return date_dte
