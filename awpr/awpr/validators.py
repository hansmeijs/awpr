from django.core.validators import validate_email
from django.db.models import Q

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from accounts import models as am
from students import models as stud_mod
from schools import models as sch_mod
from subjects import models as subj_mod
from awpr import constants as c

import logging
logger = logging.getLogger(__name__)  # __name__ tsap.validators


# === validate_unique_username ===================================== PR2020-03-31 PR2020-09-24 PR2021-01-01
def validate_unique_username(username, schoolbaseprefix, cur_user_id=None):
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
            msg_err = str(_("This username already exists at this school."))
            if not user.activated:
                msg_err += str(_("The account is not activated yet."))
            elif not user.is_active:
                msg_err += str(_("The account is inactive."))

    return msg_err


# === validate_unique_useremail ========= PR2020-08-02
def validate_email_address(email_address):
    msg_err = None
    if email_address:
        try:
            validate_email(email_address)
        except :
            msg_err = _("This email address is not valid.")
    else:
        msg_err = _('The email address cannot be blank.')
    return msg_err


# === validate_unique_useremail ===================================== PR2020-03-31 PR2020-09-24
def validate_unique_useremail(value, country, schoolbase, cur_user_id=None):
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
                user = am.User.objects.filter(country=country, schoolbase=schoolbase, email__iexact=value).exclude(pk=cur_user_id).first()
            else:
                user = am.User.objects.filter(country=country, schoolbase=schoolbase, email__iexact=value).first()

            #logger.debug('user', user)
            if user:
                username = user.username_sliced
                msg_err = str(_("This email address is already in use by '%(usr)s'. ") % {'usr': username})
                if not user.activated:
                    msg_err += str(_("The account is not activated yet."))
                elif not user.is_active:
                    msg_err += str(_("The account is inactive."))

    return msg_err


# === validate_unique_username ========= PR2020-08-02
def validate_notblank_maxlength(value, max_length, caption):
    #logger.debug ('=== validate_notblank_maxlength ====')
    msg_err = None
    if not value:
        msg_err = _('%(caption)s cannot be blank.') % {'caption': caption}
    elif len(value) > max_length:
        msg_err = _("%(caption)s '%(val)s' is too long, maximum %(max)s characters.") % {'caption': caption, 'val': value, 'max': max_length}
    return msg_err


# === validate_unique_examyear ======== PR2020-10-05
def validate_unique_examyear(examyear_int, request):
    logger.debug ('=== validate_unique_examyear ====')

    msg_err = None
    if not examyear_int:
        caption = _('Exam year')
        msg_err = _('%(caption)s cannot be blank.') % {'caption': caption}
    elif request.user.country:
        examyear_exists = sch_mod.Examyear.objects.filter(
            country=request.user.country,
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
            # PR2018-08-24 debug: in base.html  href="#" is needed,
            # because bootstrap line 233: a:not([href]):not([tabindex]) overrides navbar-item-warning
            awp_message = {'info': _("Please note: the selected exam year is different from the current exam year."),
                           'class': 'alert-warning',
                           'id': 'id_diff_exyr'}
    return awp_message


# ============ SUBJECTS
def validate_subject_code(code, cur_subject=None):  # PR2020-12-11
    #logger.debug ('validate_unique_company_name', value)
    # __iexact looks for the exact string, but case-insensitive. If value is None, it is interpreted as an SQL NULL
    msg_err = None
    value_exists = False
    is_locked = False
    if not code:
        msg_err = _('Abbreviation cannot be blank.')
    elif len(code) > c.MAX_LENGTH_SCHOOLCODE:
        value_too_long_str = str(_("Value '%(val)s' is too long.") % {'val': code})
        max_str = str(_("Max %(fld)s characters.") % {'fld': c.MAX_LENGTH_SCHOOLCODE})
        msg_err = ' '.join((value_too_long_str, max_str))
    elif cur_subject is None:
        value_exists = subj_mod.Subjectbase.objects.filter(code__iexact=code).exists()
    else:
        # check if current subject is in locked examyears
        is_locked = subj_mod.Subject.objects.filter(base__pk=cur_subject.base.pk, examyear__locked=True).exists()
        if is_locked:
            msg_err = _('This subject appears in locked exam years. The abbreviation cannot be changed.')
        else:
            value_exists = subj_mod.Subjectbase.objects.filter(code__iexact=code).exclude(pk=cur_subject.base.pk).exists()
    if value_exists:
        msg_err = str(_("Abbreviation '%(val)s' already exists.") % {'val': code})
    return msg_err


def validate_code_name_identifier(table, field, new_value, is_absence, parent, update_dict, msg_dict, request, this_pk=None):
    # validate if code already_exists in this table PR2019-07-30 PR2020-06-14 PR2021-03-28
    # from https://stackoverflow.com/questions/1285911/how-do-i-check-that-multiple-keys-are-in-a-dict-in-a-single-pass
                    # if all(k in student for k in ('idnumber','lastname', 'firstname')):
    #logger.debug('validate_code_name_identifier: ' + str(table) + ' ' + str(field) + ' ' + str(new_value) + ' ' + str(parent) + ' ' + str(this_pk))
    # filter is_absence is only used in table 'order' PR2020-06-14
    # TODO function is from tsa, must change part of it
    # TODO update_dict to be deprecated, to be replaced by msg_dict
    msg_err = None
    if not parent:
        msg_err = _("No parent record.")
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
            msg_err = _('%(fld)s cannot be blank.') % {'fld': fld}
        elif length > max_len:
            # msg_err = _('%(fld)s is too long. %(max)s characters or fewer.') % {'fld': fld, 'max': max_len}
            msg_err = _("%(fld)s '%(val)s' is too long, %(max)s characters or fewer.") % {'fld': fld, 'val': new_value, 'max': max_len}
            # msg_err = _('%(fld)s cannot be blank.') % {'fld': fld}
        if not msg_err:
            crit = None
            if table in ('departmentbase', 'schoolbase', 'subjectbase', 'subjecttype'):
                crit = Q(company=request.user.company)
            else:
                msg_err = _("Model '%(mdl)s' not found.") % {'mdl': table}

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
                instance = m.Employee.objects.filter(crit).first()

            else:
                msg_err = _("Model '%(mdl)s' not found.") % {'mdl': table}
            # TODO msg not working yet
            #logger.debug('instance: ' + str(instance))
            if instance:
                exists = True
                is_inactive = getattr(instance, 'inactive', False)
            if exists:
                if is_inactive:
                    msg_err = _("%(fld)s '%(val)s' exists, but is inactive.") % {'fld': fld, 'val': new_value}
                else:
                    msg_err = _("%(fld)s '%(val)s' already exists.") % {'fld': fld, 'val': new_value}

    #logger.debug('msg_err: ' + str(msg_err))
    if msg_err:
        # empty update_dict {} is Falsey
        if update_dict:
            if field not in update_dict:
                update_dict[field] = {}
            update_dict[field]['error'] = msg_err
        elif msg_dict:
            update_dict['err_' + field] = msg_err

    return msg_err

