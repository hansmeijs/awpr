from django.core.validators import validate_email
from django.db.models import Q

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from accounts import models as am
from students import models as stud_mod
from schools import models as sch_mod
from subjects import models as subj_mod
from awpr import constants as c
from awpr import settings as s

import logging
logger = logging.getLogger(__name__)


# === validate_unique_username ===================================== PR2020-03-31 PR2020-09-24 PR2021-01-01 PR2021-08-05
def validate_unique_username(username, schoolbaseprefix, cur_user_id=None, skip_msg_activated=False):
    #logger.debug ('=== validate_unique_username ====')
    #logger.debug ('username: <' + str(username) + '>')
    #logger.debug ('cur_user_id: <' + str(cur_user_id) + '>')
    #logger.debug ('schoolbaseprefix: <' + str(schoolbaseprefix) + '>')
    # __iexact looks for the exact string, but case-insensitive. If username is None, it is interpreted as an SQL NULL

    msg_err = None
    if schoolbaseprefix is None:
        msg_err = _('School cannot be blank.')
    elif not username:
        msg_err = _('Username cannot be blank.')
    elif len(username) > c.USERNAME_SLICED_MAX_LENGTH:
        msg_err = _('Username must have %(fld)s characters or fewer.') % {'fld': c.USERNAME_SLICED_MAX_LENGTH}
    else:
        prefixed_username = schoolbaseprefix + username
        #logger.debug ('prefixed_username: ' + str(prefixed_username))
        #logger.debug ('cur_user_id: ' + str(cur_user_id))
        if cur_user_id:
            user = am.User.objects.filter(username__iexact=prefixed_username).exclude(pk=cur_user_id).first()
        else:
            user = am.User.objects.filter(username__iexact=prefixed_username).first()
        #logger.debug ('user: ' + str(user))
        if user:
            msg_err = str(_("Username '%(val)s' already exists at this school.") % {'val': user.username_sliced})
            if not skip_msg_activated:
                if not user.activated:
                    msg_err += str(_("The account is not activated yet."))
                elif not user.is_active:
                    msg_err += str(_("The account is inactive."))

    return msg_err
# - end of validate_unique_username



# === validate_unique_user_lastname ===================================== PR2021-08-05
def validate_unique_user_lastname(schoolbase, user_lastname, cur_user_id=None, skip_msg_activated=False):
    #logger.debug ('=== validate_unique_username ====')
    # __iexact looks for the exact string, but case-insensitive. If username is None, it is interpreted as an SQL NULL

    msg_err = None
    if schoolbase is None:
        msg_err = _('School cannot be blank.')
    elif not user_lastname:
        msg_err = _('Name of the user cannot be blank.')
    elif len(user_lastname) > c.USER_LASTNAME_MAX_LENGTH:
        msg_err = _('Name of the user must have %(fld)s characters or fewer.') % {'fld': c.USER_LASTNAME_MAX_LENGTH}
    else:
        # don't use get_or_none, it will return None when multiple users with the same name exist
        if cur_user_id:
            user = am.User.objects.filter(
                schoolbase=schoolbase,
                last_name__iexact=user_lastname
            ).exclude(pk=cur_user_id).first()
        else:
            user = am.User.objects.filter(
                schoolbase=schoolbase,
                last_name__iexact=user_lastname
            ).first()
        if user:
            msg_err = str(_("Username '%(val)s' already exists at this school.") % {'val': user.username_sliced})
            if not skip_msg_activated:
                if not user.activated:
                    msg_err += str(_("The account is not activated yet."))
                elif not user.is_active:
                    msg_err += str(_("The account is inactive."))

    return msg_err
# - end of validate_unique_user_lastname

# === validate_email_address ========= PR2020-08-02
def validate_email_address(email_address):
    msg_err = None
    if email_address:
        try:
            validate_email(email_address)
        except:
            msg_err = _("Email address '%(val)s' is not valid'.") % {'val': email_address}
    else:
        msg_err = _('The email address cannot be blank.')
    return msg_err


# === validate_unique_useremail ===================================== PR2020-03-31 PR2020-09-24 PR2021-08-05
def validate_unique_useremail(value, country, schoolbase, cur_user_id=None, skip_msg_activated=False):
    #logger.debug ('validate_unique_useremail', value)
    #logger.debug ('cur_user_id', cur_user_id)
    # __iexact looks for the exact string, but case-insensitive. If value is None, it is interpreted as an SQL NULL
    msg_err = None
    if not value:
        msg_err = _('The email address cannot be blank.')
    else:
        if schoolbase is None:
            msg_err = _('There is no school selected. You must first select a school before you can add a new user')
        else:
            if cur_user_id:
                user = am.User.objects.filter(
                    country=country,
                    schoolbase=schoolbase,
                    email__iexact=value
                ).exclude(pk=cur_user_id).first()
            else:
                user = am.User.objects.filter(
                    country=country,
                    schoolbase=schoolbase,
                    email__iexact=value
                ).first()

            #logger.debug('user', user)
            if user:
                username = user.username_sliced
                msg_err = str(_("Email address '%(val)s' is already in use by '%(usr)s'. ") % {'val': value, 'usr': username})
                if not skip_msg_activated:
                    if not user.activated:
                        msg_err += str(_("The account is not activated yet."))
                    elif not user.is_active:
                        msg_err += str(_("The account is inactive."))

            #logger.debug('msg_err', msg_err)
    return msg_err


# === validate_unique_username ========= PR2020-08-02 PR2021-06-29
def validate_notblank_maxlength(value, max_length, caption, blank_allowed=False):
    #logger.debug ('=== validate_notblank_maxlength ====')
    msg_html = None
    if not value and not blank_allowed:
        msg_html = _('%(cpt)s cannot be blank.') % {'cpt': caption}
    elif max_length and len(value) > max_length:
        msg_html = _("%(cpt)s '%(val)s' is too long.<br>Maximum %(max)s characters.") \
                    % {'cpt': caption, 'val': value, 'max': max_length}
        
    return msg_html


# === validate_unique_examyear ======== PR2020-10-05
def validate_unique_examyear(country, examyear_int, request):
    # logger.debug ('=== validate_unique_examyear ====')

    msg_err = None
    if not examyear_int:
        caption = _('Exam year')
        msg_err = _('%(caption)s cannot be blank.') % {'caption': caption}
    elif request.user.country:
        examyear_exists = sch_mod.Examyear.objects.filter(
            country=country,
            code=examyear_int).exists()
        if examyear_exists:
            caption = _('This exam year')
            msg_err = _('%(caption)s already exists.') % {'caption': caption}
    return msg_err


# === validate_delete_examyear ======== PR2020-10-05
def validate_delete_examyear(examyear):
    logger.debug ('  -----  validate_delete_examyear  -----')

    msg_err = None
    if examyear:
# - check if examyear is closed
        if examyear.locked:
            msg_err = _('Exam year %(exyr)s is closed and cannot be deleted.') % {'exyr': examyear.code}
        else:
# - check if schools have activated or locked their school of this exam year  - can only happen when examyear.published =True
            crit = Q(examyear=examyear) & \
                   (Q(activated=True) | Q(locked=True))
            exists = sch_mod.School.objects.filter(crit).exists()
            if exists:
                msg_err = _('There are schools that have activated this exam year. Exam year %(exyr)s cannot be deleted.') % {'exyr': examyear.code}

    return msg_err


# === validate_locked_activated_examyear ======== PR2020-10-29
def validate_locked_activated_examyear(examyear):
    #logger.debug ('  -----  validate_locked_activated_examyear  -----')

    examyear_is_locked = False
    examyear_has_activated_schools = False
    if examyear:
# - check if examyear is closed
        if examyear.locked:
            examyear_is_locked = True
        else:
# - check if schools have activated or locked their school of this exam year  - can only happen when examyear.published =True
            crit = Q(examyear=examyear) & \
                   (Q(activated=True) | Q(locked=True))
            exists = sch_mod.School.objects.filter(crit).exists()
            if exists:
                examyear_has_activated_schools = True

    return examyear_is_locked, examyear_has_activated_schools


def message_diff_exyr(examyear):  #PR2020-10-30
    # check if selected examyear is the same as this examyear,
    # return warning when examyear is different from this_examyear
    awp_message = {}
    if examyear.code:
        examyear_int = examyear.code

        now = timezone.now()
        this_examyear = now.year
        if now.month > 7:
            this_examyear = now.year + 1
        if examyear_int != this_examyear:
            # TODO === FIXIT set msg, not for admin in July
            # PR2018-08-24 debug: in base.html  href="#" is needed,
            # because bootstrap line 233: a:not([href]):not([tabindex]) overrides navbar-item-warning

            msg = str(_(
                '<b>Please note</b>:<br>The selected exam year %(exyr)s is different from the current exam year.') % {
                          'exyr': str(examyear.code)})
            awp_message = {'msg_html': [msg], 'class': 'border_bg_warning'}

    return awp_message


# ============ SUBJECTS
def validate_subject_code_exists(code, cur_subject=None):  # PR2020-12-11 PR2021-06-22
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug ('----- validate_subject_code_exists -----')
        logger.debug('code: ' + str(code))

    msg_html = None

# - check if this code already exists
    value_exists = False

    # __iexact looks for the exact string, but case-insensitive. If value is None, it is interpreted as an SQL NULL
    crit = Q(code__iexact=code)
# - exclude this subject base in case it is an existing subject
    if cur_subject:
        crit.add(~Q(pk=cur_subject.base.pk), crit.connector)
    subjectbases = subj_mod.Subjectbase.objects.filter(crit)

# check if the matching subjectbases have children (=subjects). If no subjects: delete subjectbase
    # PR2021-05-14 debug: could not add subject because there was a subjectbase with this code without children
    # there might be multiple subjectbases with this code and no children. Check them all
    for subjectbase in subjectbases:
        has_children = subj_mod.Subject.objects.filter(base=subjectbase).exists()
        if logging_on:
            logger.debug('matching subjectbase: ' + str(subjectbase))
            logger.debug('has_children: ' + str(has_children))

        if has_children:
            value_exists = True
            if logging_on:
                logger.debug('value_exists')
        else:
            subjectbase.delete()
            if logging_on:
                logger.debug('subjectbase deleted')

    if value_exists:
        msg_html = str(_("Abbreviation '%(val)s' already exists.") % {'val': code})

    if logging_on:
        logger.debug('msg_err: ' + str(msg_html))
    return msg_html


def validate_subject_name_exists(name, examyear, cur_subject=None):  # PR2021-06-22
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug ('----- validate_subject_name_exists -----')
        logger.debug('name: ' + str(name))

    msg_html = None

    # __iexact looks for the exact string, but case-insensitive. If value is None, it is interpreted as an SQL NULL
    crit = Q(examyear=examyear)
    crit.add(Q(name__iexact=name), crit.connector)

# exclude this subject
    if cur_subject:
        crit.add(~Q(pk=cur_subject.pk), crit.connector)

    value_exists = subj_mod.Subject.objects.filter(crit).exists()

    if value_exists:
        field_caption = ' '.join((str(_('Subject')), str(_('name'))))
        msg_html = str(_("%(cpt)s '%(val)s' already exists.") % {'cpt': field_caption, 'val': name})

    return msg_html


def validate_code_name_identifier(table, field, new_value, is_absence, parent, update_dict, msg_dict, request, this_pk=None):
    # validate if code already_exists in this table PR2019-07-30 PR2020-06-14 PR2021-03-28
    # from https://stackoverflow.com/questions/1285911/how-do-i-check-that-multiple-keys-are-in-a-dict-in-a-single-pass
                    # if all(k in student for k in ('idnumber','lastname', 'firstname')):
    #logger.debug('validate_code_name_identifier: ' + str(table) + ' ' + str(field) + ' ' + str(new_value) + ' ' + str(parent) + ' ' + str(this_pk))
    # filter is_absence is only used in table 'order' PR2020-06-14
    # TODO function is from tsa, must change part of it
    # TODO update_dict to be deprecated, to be replaced by msg_dict
    msg_html = None
    if not parent:
        msg_html = _("No parent record.")
    else:
        max_len = 0
        if field == 'code':
            if table == 'subjecttype':
                max_len = c.MAX_LENGTH_04
            else:
                max_len = c.MAX_LENGTH_SCHOOLCODE
        elif field == 'name':
            max_len = c.MAX_LENGTH_NAME

        length = 0
        if new_value:
            length = len(new_value)

        blank_not_allowed = False
        fld = ''
        if field == 'code':
            fld = _('Code')
            blank_not_allowed = True
        elif field == 'name':
            fld = _('Name')
            blank_not_allowed = True

        if blank_not_allowed and length == 0:
            msg_html = _('%(fld)s cannot be blank.') % {'fld': fld}
        elif length > max_len:
            msg_html = _("%(fld)s '%(val)s' is too long, %(max)s characters or fewer.") % {'fld': fld, 'val': new_value, 'max': max_len}
        if not msg_html:
            crit = None
            if table in ('departmentbase', 'schoolbase', 'subjectbase', 'subjecttype'):
                crit = Q(company=request.user.company)
            else:
                msg_html = _("Model '%(mdl)s' not found.") % {'mdl': table}

    # filter code, name, identifier, not case sensitive
            if field == 'code':
                crit.add(Q(code__iexact=new_value), crit.connector)
            elif field == 'name':
                crit.add(Q(name__iexact=new_value), crit.connector)
    # exclude this record
            if this_pk:
                crit.add(~Q(pk=this_pk), crit.connector)

            exists = False
            is_inactive = False
            instance = None
            if table == 'employee':
                pass
                #instance = m.Employee.objects.filter(crit).first()

            else:
                msg_html = _("Model '%(mdl)s' not found.") % {'mdl': table}

            if instance:
                exists = True
                is_inactive = getattr(instance, 'inactive', False)
            if exists:
                if is_inactive:
                    msg_html = _("%(fld)s '%(val)s' exists, but is inactive.") % {'fld': fld, 'val': new_value}
                else:
                    msg_html = _("%(cpt)s '%(val)s' already exists.") % {'cpt': fld, 'val': new_value}

    if msg_html:
        # empty update_dict {} is Falsey
        if update_dict:
            if field not in update_dict:
                update_dict[field] = {}
            update_dict[field]['error'] = msg_html
        elif msg_dict:
            update_dict['err_' + field] = msg_html

    return msg_html

# ============ SCHEME  ===========
def validate_scheme_name_exists(lookup_value, examyear, error_list, cur_scheme=None):  # PR2021-06-27
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug ('----- validate_scheme_name_exists -----')
        logger.debug('lookup_value: ' + str(lookup_value))

# - function checks if this name already exists in this scheme

    blank_not_allowed = True
    max_len = c.MAX_LENGTH_NAME
    caption = _('Subject scheme name')
    length = 0
    if lookup_value:
        length = len(lookup_value)

    msg_html = None
    has_error = False
    if blank_not_allowed and length == 0:
        has_error = True
        msg_html = _('%(cpt)s cannot be blank.') % {'cpt': caption}
    elif length > max_len:
        has_error = True
        msg_html = _("%(cpt)s '%(val)s' is too long.<br>Maximum %(max)s characters.") \
                    % {'cpt': caption, 'val': lookup_value, 'max': max_len}

    if not has_error:
        # __iexact looks for the exact string, but case-insensitive. If value is None, it is interpreted as an SQL NULL
        crit = Q(department__examyear=examyear) & Q(name__iexact=lookup_value)

    # - exclude this subjecttype in case it is an existing subjecttype
        if cur_scheme:
            crit.add(~Q(pk=cur_scheme.pk), crit.connector)

    # - check if value exists
        has_error = subj_mod.Scheme.objects.filter(crit).exists()
        if has_error:
            msg_html = str(_("%(cpt)s '%(val)s' already exists.") % {'cpt': caption, 'val': lookup_value})

    if has_error:
        header_txt = _('Update subject scheme')
        msg_dict = {'field': 'scheme_name', 'header': header_txt, 'class': 'border_bg_warning', 'msg_html': msg_html}
        error_list.append(msg_dict)

    return has_error
# - end of validate_scheme_name_exists

# ============ SUBJECT TYPE BASE

def validate_subjecttypebase_code_name_abbrev_exists(field, lookup_value, cur_subjecttypebase=None):
# - function checks if this name or abbrev already exists in this scheme  # PR2021-06-29

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug ('----- validate_subjecttypebase_code_name_abbrev_exists -----')
        logger.debug('field: ' + str(field))
        logger.debug('lookup_value: ' + str(lookup_value))

    msg_html = None
    caption = _('Base character')

    # __iexact looks for the exact string, but case-insensitive. If value is None, it is interpreted as an SQL NULL
    crit = None
    if field == 'code':
        crit = Q(code__iexact=lookup_value)
    elif field == 'name':
        crit = Q(name__iexact=lookup_value)
    elif field == 'abbrev':
        crit = Q(abbrev__iexact=lookup_value)

# - exclude this subjecttype in case it is an existing subjecttype
    if cur_subjecttypebase:
        crit.add(~Q(pk=cur_subjecttypebase.pk), crit.connector)

# - check if value exists
    has_error = subj_mod.Subjecttypebase.objects.filter(crit).exists()
    if has_error:
        msg_html = str(_("%(cpt)s '%(val)s' already exists.") % {'cpt': caption, 'val': lookup_value})

    return msg_html
# - end of validate_subjecttypebase_code_name_abbrev_exists


# ============ SUBJECT TYPES
def validate_subjecttype_name_abbrev_exists(field, lookup_value, scheme, cur_subjecttype=None):  # PR2021-06-27
# - function checks if this name or abbrev already exists in this scheme

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug ('----- validate_subjecttype_name_abbrev_exists -----')
        logger.debug('field: ' + str(field))
        logger.debug('lookup_value: ' + str(lookup_value))

    msg_html = None
    caption = _('Character')

    # __iexact looks for the exact string, but case-insensitive. If value is None, it is interpreted as an SQL NULL
    crit = Q(scheme=scheme)
    if field == 'name':
        crit.add(Q(name__iexact=lookup_value), crit.connector)
    elif field == 'abbrev':
        crit.add(Q(abbrev__iexact=lookup_value), crit.connector)

# - exclude this subjecttype in case it is an existing subjecttype
    if cur_subjecttype:
        crit.add(~Q(pk=cur_subjecttype.pk), crit.connector)

# - check if value exists
    has_error = subj_mod.Subjecttype.objects.filter(crit).exists()
    if has_error:
        msg_html = str(_("%(cpt)s '%(val)s' already exists in this subject scheme.") % {'cpt': caption, 'val': lookup_value})

    return msg_html
# - end of validate_subjecttype_name_abbrev_exists


def validate_subjecttype_duplicate_base(scheme, sjtpbase, error_list, cur_subjecttype=None):  # PR2021-06-27
# - function checks if this subjecttype_base already exists in this scheme

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug ('----- validate_subjecttype_duplicate_base -----')
        logger.debug('sjtpbase: ' + str(sjtpbase))

    crit = Q(scheme=scheme) & Q(base=sjtpbase)

# - exclude this subjecttype in case it is an existing subjecttype (should not be possible, base cannot be changed
    if cur_subjecttype:
        crit.add(~Q(pk=cur_subjecttype.pk), crit.connector)

# - check if value exists
    has_error = subj_mod.Subjecttype.objects.filter(crit).exists()
    if has_error:
        header_txt = _('Update character')
        caption = _('Character')
        msg_html = str(_("%(cpt)s '%(val)s' already exists in this subject scheme.") % {'cpt': caption, 'val': sjtpbase.name})
        msg_dict = {'field': 'sjtpbase_pk', 'header': header_txt, 'class': 'border_bg_invalid', 'msg_html': msg_html}
        error_list.append(msg_dict)

    return has_error
# - end of validate_subjecttype_duplicate_base

