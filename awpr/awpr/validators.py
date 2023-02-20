from django.core.validators import validate_email
from django.db.models import Q

#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import gettext_lazy as _


from accounts import models as acc_mod
from students import models as stud_mod
from schools import models as sch_mod
from subjects import models as subj_mod
from awpr import constants as c
from awpr import settings as s

import logging
logger = logging.getLogger(__name__)


# === validate_unique_username =====================================
def validate_unique_username(sel_examyear, username, schoolbaseprefix, cur_user_id=None, skip_msg_activated=False):
    # PR2020-03-31 PR2020-09-24 PR2021-01-01 PR2021-08-05 PR2022-12-31
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('-----  validate_unique_username  -----')
        logger.debug ('    username: <' + str(username) + '>')
        logger.debug ('    cur_user_id: <' + str(cur_user_id) + '>')
        logger.debug ('    schoolbaseprefix: <' + str(schoolbaseprefix) + '>')

    # __iexact looks for the exact string, but case-insensitive. If username is None, it is interpreted as an SQL NULL

    msg_err = None
    user_without_userallowed = None

    if schoolbaseprefix is None:
        msg_err = get_err_html_cannot_be_blank(_('School'))

    elif not username:
        msg_err = get_err_html_cannot_be_blank(_('Username'))

    elif len(username) > c.USERNAME_SLICED_MAX_LENGTH:
        msg_err = _('Username must have %(fld)s characters or fewer.') % {'fld': c.USERNAME_SLICED_MAX_LENGTH}
    else:
        prefixed_username = schoolbaseprefix + username
        if logging_on:
            logger.debug ('    prefixed_username: ' + str(prefixed_username))
            logger.debug ('    cur_user_id: ' + str(cur_user_id))

        if cur_user_id:
            user = acc_mod.User.objects.filter(username__iexact=prefixed_username).exclude(pk=cur_user_id).first()
        else:
            user = acc_mod.User.objects.filter(username__iexact=prefixed_username).first()
        if logging_on:
            logger.debug ('user: ' + str(user))

        if user:
            # check if there is a UserAllowed record of this user in this examyear PR2022-12-31

            user_exists_this_examyear = acc_mod.UserAllowed.objects.filter(
                user=user,
                examyear=sel_examyear
            ).exists()

            msg_err = str(_("Username '%(val)s' already exists at this school.") % {'val': user.username_sliced})
            if not user_exists_this_examyear:
                user_without_userallowed = {
                    'user_pk': user.pk,
                    'schoolbase_pk': user.schoolbase.pk,
                    'username': user.username_sliced,
                    'last_name': user.last_name
                }
                msg_err = None
            elif not skip_msg_activated:
                if not user.activated:
                    msg_err += ' ' + str(_("The account is not activated yet."))
                elif not user.is_active:
                    msg_err += ' ' + str(_("The account is inactive."))

    return msg_err, user_without_userallowed
# - end of validate_unique_username


# === validate_unique_user_lastname ===================================== PR2021-08-05

def validate_unique_user_lastname(schoolbase, user_lastname, cur_user_id=None, skip_msg_activated=False):
    #logger.debug ('=== validate_unique_username ====')
    # __iexact looks for the exact string, but case-insensitive. If username is None, it is interpreted as an SQL NULL

    msg_err = None
    if schoolbase is None:
        msg_err = get_err_html_cannot_be_blank(_('School'))

    elif not user_lastname:
        msg_err = get_err_html_cannot_be_blank(_('Name of the user'))

    elif len(user_lastname) > c.USER_LASTNAME_MAX_LENGTH:
        msg_err = _('Name of the user must have %(fld)s characters or fewer.') % {'fld': c.USER_LASTNAME_MAX_LENGTH}
    else:
        # don't use get_or_none, it will return None when multiple users with the same name exist
        if cur_user_id:
            user = acc_mod.User.objects.filter(
                schoolbase=schoolbase,
                last_name__iexact=user_lastname
            ).exclude(pk=cur_user_id).first()
        else:
            user = acc_mod.User.objects.filter(
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
        msg_err = get_err_html_cannot_be_blank(_('The email address'))

    return msg_err


# === validate_unique_useremail ===================================== PR2020-03-31 PR2020-09-24 PR2021-08-05
def validate_unique_useremail(value, country, schoolbase, cur_user_id=None, skip_msg_activated=False):
    #logger.debug ('validate_unique_useremail', value)
    #logger.debug ('cur_user_id', cur_user_id)
    # __iexact looks for the exact string, but case-insensitive. If value is None, it is interpreted as an SQL NULL
    msg_err = None
    if not value:
        msg_err = get_err_html_cannot_be_blank(_('The email address'))

    else:
        if schoolbase is None:
            msg_err = _('There is no school selected. You must first select a school before you can add a new user')
        else:
            if cur_user_id:
                user = acc_mod.User.objects.filter(
                    country=country,
                    schoolbase=schoolbase,
                    email__iexact=value
                ).exclude(pk=cur_user_id).first()
            else:
                user = acc_mod.User.objects.filter(
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


# === validate_notblank_maxlength ========= PR2020-08-02 PR2021-06-29 PR2021-10-13
def validate_notblank_maxlength(value, max_length, caption, blank_allowed=False):
    #logger.debug ('=== validate_notblank_maxlength ====')
    msg_err = None
    if value:
        if max_length and len(value) > max_length:
            msg_err = get_err_html_max_char(caption, value, max_length)

    elif not blank_allowed:
        msg_err = get_err_html_cannot_be_blank(caption)

    return msg_err
# - end of validate_notblank_maxlength


# === validate_level_sector_in_student ========= PR2022-08-20

def validate_level_sector_in_student(examyear, school, department, lvlbase_pk, sctbase_pk):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ----- validate_level_sector_in_student ----- ')
        logger.debug('    lvlbase_pk: ' + str(lvlbase_pk))
        logger.debug('    sctbase_pk: ' + str(sctbase_pk))

    msg_list = []
    if school is None:
        msg_list.append(str(_('%(cpt)s is not found.') % {'cpt': _('School')}))
    elif department is None:
        msg_list.append(str(_('%(cpt)s is not found.') % {'cpt': _('Department')}))
    else:
        if department.level_req:
            caption = _('The learning path')
            if lvlbase_pk is None:
                msg_list.append(str(get_err_html_cannot_be_blank(caption)))

            else:
                level = subj_mod.Level.objects.get_or_none(
                    base_id=lvlbase_pk,
                    examyear=examyear
                )
                if level is None:
                    msg_list.append(str(_('%(cpt)s is not found.') % {'cpt': caption}))

        if department.sector_req:
            caption = _('The profile') if department.has_profiel else _('The sector')
            if sctbase_pk is None:
                msg_list.append(str(get_err_html_cannot_be_blank(caption)))
            else:
                sector = subj_mod.Sector.objects.get_or_none(
                    base_id=sctbase_pk,
                    examyear=examyear
                )
                if sector is None:
                    msg_list.append(str(_('%(cpt)s is not found.') % {'cpt': caption}))
    # use msglist, so it can show multiple messages (happens when both level and sector are missing)
    return msg_list
# - end of validate_level_sector_in_student


# === validate_unique_examyear ======== PR2020-10-05

def validate_unique_examyear(country, examyear_int, request):
    # logger.debug ('=== validate_unique_examyear ====')

    msg_err = None
    caption = _('Exam year')

    if not examyear_int:
        msg_err = get_err_html_cannot_be_blank(caption)

    elif request.user.country:
        examyear_exists = sch_mod.Examyear.objects.filter(
            country=country,
            code=examyear_int
        ).exists()
        if examyear_exists:
            msg_err = _("%(cpt)s '%(val)s' already exists.") % {'cpt': caption, 'val': str(examyear_int)}
    return msg_err


# === validate_delete_examyear ======== PR2020-10-05 PR2022-07-31
def validate_delete_examyear(examyear):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug ('  -----  validate_delete_examyear  -----')
        logger.debug ('examyear: ' + str(examyear))

    err_html = None

    if examyear is None:
        err_html = str(_('There is no exam year.'))
    else:
        msg_txt = None
# - check if examyear is locked
        if examyear.locked:
            msg_txt = str(_('Exam year %(exyr)s is closed.') % {'exyr': examyear.code})

        else:

# - check if examyear has students
            examyear_has_students = stud_mod.Student.objects.filter(
                school__examyear=examyear
            ).exists()

# - check if examyear is published
            if examyear.published:
                if examyear_has_students:
                    msg_txt = str(_('Exam year %(ey_code)s has candidates.') % {'ey_code': examyear.code})
                else:
                    msg_txt = str(_('Exam year %(ey_code)s is published.') % {'ey_code': examyear.code})

            elif examyear_has_students:
                msg_txt = str(_('Exam year %(ey_code)s is published and has candidates.') % {'ey_code': examyear.code})

        if msg_txt:
            err_html = '<br>'.join((
                str(msg_txt),
                str(_("You cannot delete exam year %(ey_code)s.") % {'ey_code': examyear.code})
            ))

    if logging_on:
        logger.debug ('err_html: ' + str(err_html))

    return err_html
# - end of validate_delete_examyear


# === validate_locked_activated_examyear ======== PR2020-10-29

def validate_locked_activated_examyear(examyear):
    #logger.debug ('  -----  validate_locked_activated_examyear  -----')

    examyear_is_locked = False
    examyear_has_activated_schools = False
    if examyear:
# - check if examyear is closed
        if examyear.locked:
            examyear_is_locked = True

            msg = '<br>'.join((str(_('Exam year %(exyr)s is locked.') % { 'exyr': str(examyear.code)}), str("")))
            awp_message = {'msg_html': [msg], 'class': 'border_bg_warning'}

        else:
# - check if schools have activated or locked their school of this exam year  - can only happen when examyear.published =True
            crit = Q(examyear=examyear) & \
                   (Q(activated=True) | Q(locked=True))
            exists = sch_mod.School.objects.filter(crit).exists()
            if exists:
                examyear_has_activated_schools = True

    return examyear_is_locked, examyear_has_activated_schools


def validate_examyear_locked(examyear):  #  PR2021-12-04
    # logger.debug ('  -----  validate_examyear_locked  -----')

    awp_message = {}
    if examyear and examyear.locked:
        msg = '<br>'.join((str(_('Exam year %(ey_code)s is locked.') % {'ey_code': str(examyear.code)}),
                           str(_('You cannot make changes.'))))
        awp_message = {'msg_html': [msg], 'class': 'border_bg_warning'}

    return awp_message


# === validate_undo_published_examyear ======== PR2022-07-31
def validate_undo_published_examyear(examyear):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug ('  -----  validate_undo_published_examyear  -----')
        logger.debug ('examyear: ' + str(examyear))
    # cannot undo published examyear when the examyear has students

    msg_err = None
    if examyear is None:
        msg_err = _('There is no exam year.')
# - check if examyear is published
    elif not examyear.published:
        msg_err = str(_('Exam year %(ey_code)s is not published.') % {'ey_code': str(examyear.code)})
    elif examyear.locked:
        msg_err = '<br>'.join((str(_('Exam year %(ey_code)s is locked.') % {'ey_code': str(examyear.code)}),
                               str(_("You cannot undo the publication."))))
    else:
# - check if examyear has students
        examyear_has_students = stud_mod.Student.objects.filter(
             school__examyear=examyear
         ).exists()
        if examyear_has_students:
            msg_err = '<br>'.join((str(_('Exam year %(ey_code)s has candidates.') % {'ey_code': str(examyear.code)}),
                       str(_("You cannot undo the publication."))))
    if logging_on:
        logger.debug ('msg_err: ' + str(msg_err))

    return msg_err
# - end of validate_undo_published_examyear


# === validate_undo_published_examyear ======== PR2022-08-03

def validate_undo_locked_examyear(examyear):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug ('  -----  validate_undo_published_examyear  -----')
        logger.debug ('examyear: ' + str(examyear))

    msg_err = None
    if examyear is None:
        msg_err = _('There is no exam year.')
# - check if examyear is locked
    elif not examyear.locked:
        msg_err = str(_('Exam year %(ey_code)s is not locked.') % {'ey_code': str(examyear.code)})

    if logging_on:
        logger.debug ('msg_err: ' + str(msg_err))

    return msg_err
# - end of validate_undo_published_examyear


# ============ SCHOOLS

def validate_schoolcode_blank_length_exists(examyear, school_code, request, cur_school=None):  # PR2020-10-22 PR2021-06-20 PR2022-08-07
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----------- validate_schoolcode_blank_length_exists ----------- ')
        logger.debug('school_code: ' + str(school_code) + ' ' + str(type(school_code)))

    msg_html = None

    caption = _('School code')

    if not school_code:
        msg_html = get_err_html_cannot_be_blank(caption)

    elif len(school_code) > c.MAX_LENGTH_SCHOOLCODE:
        msg_html = get_err_html_max_char(caption, school_code, c.MAX_LENGTH_SCHOOLCODE)

    if msg_html is None:
        exists_all_years, existst_this_year = False, False

# --- check if 'code' exists in Schoolbase with filter country
        crit = Q(country=request.user.country) & \
               Q(code__iexact=school_code)
# --- exclude schoolbase of this school this record
        if cur_school:
            crit.add(~Q(pk=cur_school.base.pk), crit.connector)
        exists_all_years = sch_mod.Schoolbase.objects.filter(crit).exists()

        if exists_all_years:
# --- if exists: check if school with this schoolcode exists this examyear
            crit = Q(examyear=examyear) & \
                   Q(base__code__iexact=school_code)
# --- exclude schoolbase of this school this record
            if cur_school:
                crit.add(~Q(pk=cur_school.base.pk), crit.connector)

            existst_this_year = sch_mod.School.objects.filter(crit).exists()

        if existst_this_year:
            msg_html = _("School code '%(val)s' already exists.") % {'val': school_code}
        elif exists_all_years:
           msg_html = _("School code '%(val)s' already exists in other exam years.") % {'val': school_code}

    return msg_html


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


def validate_subject_name_exists(field, new_value, examyear, cur_subject=None):  # PR2021-06-22 PR2022-08-14
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug ('----- validate_subject_name_exists -----')
        logger.debug('field: ' + str(field))
        logger.debug('new_value: ' + str(new_value))

    msg_html = None

    # __iexact looks for the exact string, but case-insensitive. If value is None, it is interpreted as an SQL NULL
    crit = Q(examyear=examyear)
    if field == 'name_nl':
        crit.add(Q(name_nl__iexact=new_value), crit.connector)

    elif field == 'name_en':
        crit.add(Q(name_en__iexact=new_value), crit.connector)

    elif field == 'name_pa':
        crit.add(Q(name_pa__iexact=new_value), crit.connector)

# exclude this subject
    if cur_subject:
        crit.add(~Q(pk=cur_subject.pk), crit.connector)

    value_exists = subj_mod.Subject.objects.filter(crit).exists()

    if value_exists:
        caption = _('Subject name in Papiamentu') if field == 'name_pa' \
            else _('Subject name in English') if field == 'name_en' \
            else _('Subject name in Dutch')
        msg_html = str(_("%(cpt)s '%(val)s' already exists.") % {'cpt': caption, 'val': new_value})

    return msg_html


def validate_code_name_blank_length_exists(table, field, new_value, this_pk=None):
    # validate if code or name  already_exists in this table PR2019-07-30 PR2020-06-14 PR2021-03-28

    msg_html = None

    max_len = 0
    if field == 'code':
        if table == 'subjecttype':
            max_len = c.MAX_LENGTH_04
        else:
            max_len = c.MAX_LENGTH_SCHOOLCODE
    elif field == 'name':
        max_len = c.MAX_LENGTH_NAME

    length = len(new_value) if new_value else 0

    blank_not_allowed = False
    fld = ''
    if field == 'code':
        fld = _('Code')
        blank_not_allowed = True
    elif field == 'name':
        fld = _('Name')
        blank_not_allowed = True

    if blank_not_allowed and length == 0:
        msg_html = get_err_html_cannot_be_blank(fld)

    elif length > max_len:
        msg_html = get_err_html_max_char(fld, new_value, max_len)

    if not msg_html:

# filter code, name, not case sensitive
        crit = None
        if field == 'code':
            crit = Q(code__iexact=new_value)
        elif field == 'name':
            crit = Q(name__iexact=new_value)
# exclude this record
        if this_pk and crit:
            crit.add(~Q(pk=this_pk), crit.connector)
        if crit:
            exists = False
            if table == 'department':
                exists = sch_mod.Department.objects.filter(crit).exists()
            elif table == 'departmentbase':
                exists = sch_mod.Departmentbase.objects.filter(crit).exists()
            elif table == 'school':
                exists = sch_mod.School.objects.filter(crit).exists()
            elif table == 'schoolbase':
                exists = sch_mod.Schoolbase.objects.filter(crit).exists()
            elif table == 'subject':
                exists = subj_mod.Subject.objects.filter(crit).exists()
            elif table == 'subjectbase':
                exists = subj_mod.Subjectbase.objects.filter(crit).exists()
            elif table == 'subjecttype':
                exists =  subj_mod.Subjecttype.objects.filter(crit).exists()
            elif table == 'subjecttypebase':
                exists = subj_mod.Subjecttypebase.objects.filter(crit).exists()
            else:
                msg_html = _("Model '%(mdl)s' not found.") % {'mdl': table}

            if msg_html is None and exists:
                msg_html = _("%(cpt)s '%(val)s' already exists.") % {'cpt': fld, 'val': new_value}

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
        msg_html = get_err_html_cannot_be_blank(caption)

    elif length > max_len:
        has_error = True
        msg_html = get_err_html_max_char(caption, lookup_value, max_len)

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
        header_txt = _('Edit subject scheme')
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


# ============ ENVELOP BUNDLE / LABEL  ===========

def validate_bundle_label_name_blank_length_exists(table, examyear, name, cur_instance=None):
    # PR2022-08-11
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----------- validate_bundle_label_name_blank_length_exists ----------- ')
        logger.debug('name: ' + str(name))

    msg_html = None

    caption = _('Label bundle name') if table == 'envelopbundle' else _('Label name')
    if not name:
        msg_html = get_err_html_cannot_be_blank(caption)

    elif len(name) > c.MAX_LENGTH_NAME:
        msg_html = get_err_html_max_char(caption, name, c.MAX_LENGTH_NAME)

    if msg_html is None:
# --- if exists: check if label with this name exists this examyear
        crit = Q(examyear=examyear) & \
               Q(name__iexact=name)
# --- exclude this record
        if cur_instance:
            crit.add(~Q(pk=cur_instance.pk), crit.connector)

        if table == 'envelopbundle':
            exists = subj_mod.Envelopbundle.objects.filter(crit).exists()
        else:
            exists = subj_mod.Enveloplabel.objects.filter(crit).exists()

        if exists:
            msg_html = _("%(cpt)s '%(val)s' already exists.") % {'cpt': caption, 'val': name}

    return msg_html
# - end of validate_bundle_label_name_blank_length_exists



def get_err_html_cannot_be_blank(caption):    # PR2022-08-08
    return _('%(cpt)s cannot be blank.') % {'cpt': caption}


def get_err_html_max_char(caption, value, max_len):    # PR2022-08-08
    return _("%(cpt)s '%(val)s' is too long.<br>Maximum %(max)s characters.") \
               % {'cpt': caption, 'val': value, 'max': max_len}


###########################



def message_testsite():  # PR2022-01-12
    # check if selected examyear is the same as this examyear,
    # return warning when examyear is different from this_examyear
    awp_message = {}

    if s.IS_TESTSITE:
        msg = ''.join(('<b>', str(_('Warning')).upper(), '</b>:<br>',
                       str(_('You are logged in to <b>awptest.net</b>, the testsite of AWP-online.')), '<br>',
                       str(_('This testsite is for testing and practicing only.')), '<br>',
                       str(_('It contains a copy of the actual data of AWP-online.')), '<br>',
                       str(_('The data you enter in the testsite will not affect the actual data in AWP-online.')),
                       '<br>',
                       str(_('Log in to <b>www.awponline.net</b> if you want to enter the actual data.'))
                       ))
        awp_message = {'msg_html': [msg], 'class': 'border_bg_warning'}

    return awp_message


def message_openargs():  # PR2022-05-28 PR2022-06-01
    # check if selected examyear is the same as this examyear,
    # return warning when examyear is different from this_examyear

    # reset_show_msg(request):

    # PR 2022-06-01 function 'reset_show_msg' resets open_args
    # called only once by Loggedin, to reset before setting is retrieved
    # to reset hiding messages: remove 'reset_show_msg' from schools_systemupdate manually

    msg = ''.join((
        '<p><b>', str(_("The following changes have been made in AWP-online 2023")), ':</b></p>',
        "<ul><li>", str(_("Previously submitted subjects and deleted subjects are included in the Ex1 form.")), "</li>",
        "<li>", str(_("When a candidate or subject is deleted, you must submit it in an additional Ex1 form")), "</li></ul>",
        "<ul><li>", str(_("AWP can enter exemptions from the previous examyear.")), "</li>",

        # PR2023-02-20 not for now: "<li>", str(_("Exemption grades must also be approved.")), "</li>",

        "<li>", str(_("Exemption grades are included in the Ex2 form.")), "</li></ul>",
        "<ul class='mb-0'><li>", str(_("The accounts of the second correctors will be created by the Ministry of Education.")), "</li>",
        "<li>", str(_("The 'Allowed sections' window is improved.")), "</li>",
        "<li>", str(_("In the candidates window you can enter special characters.")), "</li></ul>",
    ))

    message = {'msg_html': [msg], 'class': 'border_bg_transparent', 'size': 'lg', 'btn_hide': True}

    return message

    """
    
    msg = ''.join((
        '<p><b>', str(_("Examyear 2023 has been created in AWP-online.")), '</b><br>',
        str(_("You can start entering data now.")), '<br>',
        str(_("Selecting the new examyear goes as follows:")), '<br>',
        str(_("Click on <i>Examyear 2022</i> beside the AWP-logo in the left upper corner of the page.")), '<br>',
        str(_("The window <i>Select an examyear</i> opens. Select <i>2023</i>.")), '<br>',
        '<b>', str(_('Make sure that you enter the new information in the correct examyear.')), '</b><br>',
        str(_('AWP-online gives the warning below, when you open the previous exam year, but you can still enter data.')), '</p>',
        '</p>'
    ))
    
    msg = ''.join((
        '<p><b>', str(_("The 'Submit Ex5' button is now available")), '</b><br>',
        str(_('Go to the page <i>Results</i> and click the grey button <i>Submit Ex5</i>.')), ' ',
        str(_('There are now additional approvals needed, but all SE grades and CE scores must be approved.')), ' ',
        str(_('Only the chairperson or secretary can submit the Ex5 form.')), '</p>',
        '</p>'
    ))
    msg = ''.join((
        '<p><b>', str(_('How AWP-online will calculate the results')), '</b><br>',
        str(_('As soon as the conversion tables ares available, we will upload them in AWP-online.')), ' ',
        str(_('AWP will then calculate all grades, but not the results.')), ' ',
        str(_('Go to the page <i>Results</i> and click the grey button <i>Calculate results</i>, the results will then be calculated.')), ' ',
        str(_('A logfile will be downloaded with a detailed calculation of the results.')), ' ',
        str(_('The results will also be calculated when you download the preliminary grade lists.')), '</p>',

        '<p><b>', str(_('Overview of the results')), '</b><br>',
        str(_('Unfortunately the short grade list is not available yet. Instead you can use for the exam result meeting:')), '</p>',
        '<ul><li>', str(_('The preliminary Ex5 form.')),'</li>',
        '<li>', str(_('The preliminary grade lists.')),'</li>',
        '<li>', str(_('The logfile of the calculated results.')),'</li></ul>',

        '<p><b>', str(_('Applying the thumb rule')), '</b> (', str(_('only at Havo and Vwo')),')<br>',
        str(_('Go to the page <i>Subjects</i> and click in the horizontal black bar on <i>First exam period</i>.')),' ',
        str(_('Click in the column <i>Thumb rule</i> of the desired subject.</i>.')),' ',
        str(_('AWP will give a message when a thumb rule cannot be applied to a subject.')),'</p>',

        '<p><b>', str(_('Safety measure')), '</b><br>',
        str(_("To prevent leaking of the results, before the official announcement of the results,")),' ',
        str(_("only the chairperson and secretary have access to the page <i>Results</i> and <i>Archive</i>.")), '</p>'
    ))

    msg = ''.join((
        '<p><b>', str(_('How to submit the Ex2A form')), '</b></p>',
        '<ul><li>', str(_('Go to the page <i>Grades</i> and click in the horizontal black bar on the tab <i>First exam period</i>.')),'</li>',
        '<li>', str(_("Click the grey button <i>Approve grades</i>.")),'</li>',
        '<li>', str(_("Make sure that you have selected <b>Central exam</b> in the field <i>Exam type</i>, not 'School exam'.")),'</li>',
        '<li>', str(_('After the chairperson, secretary, examiner and second corrector have approved the scores,')),' ',
        str(_("the chairperson or secretary can submit the Ex2A form by clicking the grey button <i>Submit Ex2A</i>.")),
        '</li></ul>'
    ))


        msg = ''.join(('<p><b>', str(_('Anouncement')).upper(), '</b><br>',
        str(_('There were some issues with downloading the Ex forms.')), ' ',
        str(_('Hopefully they are solved now.')),'  ', str(_('We apologize for the inconvenience.')),'</p><p>',
        str(_('<b>How to submit the Ex4 form</b>')), '<br>',
        str(_('Go to the page <i>Subjects</i> and click on the tab <i>Second exam period</i>.')),'<br>',
        str(_('Click in the column <i>Re-examination</i> to select the re-examination subjects.')),'<br>',
        str(_('Make sure the number of re-examination does not exceed the maximum. AWP does not check this.')),'<br>',
        str(_('Only the chairperson and secretary must approve the Ex4 form.')),'<br>',
        str(_('Click <i>Submit Ex4 form</i> to submit the Ex4 form.')),'<br>',
        str(_('Go to the page <i>Archive</i> to download the submitted form.'))
    ))
    msg = ''.join(('<b>', str(_('Anouncement')).upper(), '</b><br>',
        str(_('The ETE has published the cesuur and conversion tables of the practical exams.')),'<br>',
        str(_('AWP has automatically calculated the grades. They are shown in the column <i>CE grade</i> on the page <i>Grades</i>.')),'<br>',
        str(_('To download the conversion table, click the down array in the column <i>Download conversion table</i>.')),'<br><br>',
# class='pb-0'><span class='man_underline'>Voorbeeld</span>
        str(_("For candidates whose exam was removed because of a mixture of blue and red 'minitoetsen':")),"<br>",
        str(_("AWP can only calculate the CE-grade of an ETE exam when an exam is selected in the page 'Exams'")), ' ',
        str(_("Therefore you must still select an exam in the page 'Exams'.")), "<br>",
        str(_('Since the cesuur for the blue and read version of an exam are the same, you can select either version.')), ' ',
        str(_("You must enter the score in the column 'CE-score' on the page 'Grades', not in the page 'Exams'.")),
    ))
    """


