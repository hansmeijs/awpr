from django.core.validators import validate_email
from django.db.models import Q

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from accounts import models as am
from students import models as student_models
from schools import models as school_models
from awpr import constants as c

import logging
logger = logging.getLogger(__name__)  # __name__ tsap.validators


# === validate_unique_username ===================================== PR2020-03-31 PR2020-09-24
def validate_unique_username(username, schoolbaseprefix, cur_user_id=None):
    logger.debug ('=== validate_unique_username ====')
    logger.debug ('username: <' + str(username) + '>')
    logger.debug ('cur_user_id: <' + str(cur_user_id) + '>')
    logger.debug ('schoolbaseprefix: <' + str(schoolbaseprefix) + '>')
    # __iexact looks for the exact string, but case-insensitive. If username is None, it is interpreted as an SQL NULL

    msg_err = None
    if not username:
        msg_err = _('Username cannot be blank.')
    elif len(username) > c.USERNAME_SLICED_MAX_LENGTH:
        msg_err = _('Username must have %(fld)s characters or fewer.') % {'fld': c.USERNAME_SLICED_MAX_LENGTH}
    else:
        prefixed_username = schoolbaseprefix + username
        logger.debug ('prefixed_username: ' + str(prefixed_username))
        logger.debug ('cur_user_id: ' + str(cur_user_id))
        if cur_user_id:
            user = am.User.objects.filter(username__iexact=prefixed_username).exclude(pk=cur_user_id).first()
        else:
            user = am.User.objects.filter(username__iexact=prefixed_username).first()
        logger.debug ('user: ' + str(user))
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
        examyear_exists = school_models.Examyear.objects.filter(
            country=request.user.country,
            examyear=examyear_int).exists()
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
            msg_err = _('Exam year %(exyr)s is closed and cannot be deleted.') % {'exyr': examyear.examyear}
        else:
# - check if schools have activated or locked their school of this exam year  - can only happen when examyear.published =True
            crit = Q(examyear=examyear) & \
                   Q(istemplate__isnull=True) & \
                   (Q(activated=True) | Q(locked=True))
            exists = school_models.School.objects.filter(crit).exists()
            if exists:
                msg_err = _('There are schools that have activated this exam year. Exam year %(exyr)s cannot be deleted.') % {'exyr': examyear.examyear}

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
                   Q(istemplate__isnull=True) & \
                   (Q(activated=True) | Q(locked=True))
            exists = school_models.School.objects.filter(crit).exists()
            if exists:
                examyear_has_activated_schools = True

    return examyear_is_locked, examyear_has_activated_schools

def message_diff_exyr(examyear):  #PR2020-10-30
    # check if selected examyear is the same as this examyear,
    # return warning when examyear is different from this_examyear
    awp_message = {}
    if examyear.examyear:
        examyear_int = examyear.examyear

        now = timezone.now()
        this_examyear = now.year
        if now.month > 7:
            this_examyear = now.year + 1
        if examyear_int != this_examyear:
            # PR2018-08-24 debug: in base.html  href="#" is needed,
            # because bootstrap line 233: a:not([href]):not([tabindex]) overrides navbar-item-warning
            awp_message = {'info': _("Please note: selected exam year is different from the current exam year."),
                           'class': 'alert-warning',
                           'id': 'id_diff_exyr'}
    return awp_message