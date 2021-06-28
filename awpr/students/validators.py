# PR2019-02-17
from django.utils.translation import ugettext_lazy as _

from django.db.models import Q

from datetime import datetime
import logging
logger = logging.getLogger(__name__)

from students.models import Student
from awpr import constants as c
from awpr import settings as s


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
                msg_err = _("'%(val)s' already exists.") % {'val': new_name}
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
