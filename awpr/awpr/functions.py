# PR2018-05-28
import json
from datetime import date, datetime, timedelta
from random import randint

from django.core.mail import send_mail
from django.db import connection
from django.db.models import Q
from django.template.loader import render_to_string
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from awpr import constants as c
from awpr import settings as s
from awpr import library as awpr_lib


from accounts import models as acc_mod
from accounts import views as acc_view
from  accounts import  permits as acc_prm

from grades import views as grade_view
from grades import calc_results as grade_calc

from schools import models as sch_mod
from subjects import models as subj_mod
from subjects import views as subj_view
from students import models as stud_mod
from students import views as stud_view

import pytz
import logging
logger = logging.getLogger(__name__)


# PR2019-01-04 from https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy
from django.utils.functional import Promise

# PR2022-02-13 From Django 4 we dont have force_text You Just have to Use force_str Instead of force_text.
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder

class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)


def send_email_verifcode(formname, email_template, request, sel_examyear, sel_school=None, sel_department=None ):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ----- send_email_verifcode  -----')
        logger.debug('sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))

    verifcode_key, exception_str = None, None

    req_usr = request.user

    try:
        # create _verificationcode and key, store in usersetting, send key to client, set expiration to 30 minutes
        # get random number between 1,000,000 en 1,999,999, convert to string and get last 6 characters
        # this way you get string from '000000' thru '999999'
        # key is sent to client, code must be entered by user
        # key_code is stored in usersettings, with
        _verificationcode = str(randint(1000000, 1999999))[-6:]
        verifcode_key = str(randint(1000000, 1999999))[-6:]

        key_code = '_'.join((verifcode_key, _verificationcode))

        now = datetime.now()  # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07
        expirationtime = now + timedelta(seconds=1800)
        expirationtime_iso = expirationtime.isoformat()

        verification_dict = {'form': formname, 'key_code': key_code, 'expirationtime': expirationtime_iso}
        acc_view.set_usersetting_dict(c.KEY_VERIFICATIONCODE, verification_dict, request)

        if logging_on:
            logger.debug('verification_dict: ' + str(verification_dict))

        subject = str(_('AWP-online verificationcode'))
        from_email = 'AWP-online <noreply@awponline.net>'
        msg_dict = {
            'user': req_usr,
            'examyear': sel_examyear,
            'verificationcode': _verificationcode
        }
        if sel_school:
            msg_dict['school'] = sel_school
        if sel_department:
            msg_dict['department'] = sel_department

        if logging_on:
            logger.debug('msg_dict: ' + str(msg_dict))
            logger.debug('email_template: ' + str(email_template))

        message_str = render_to_string(email_template, msg_dict)

        if logging_on:
            logger.debug('message_str: ' + str(message_str) + ' ' + str(type(message_str)))
            logger.debug('from_email: ' + str(from_email) + ' ' + str(type(from_email)))
            logger.debug('[req_usr.email: ' + str([req_usr.email]) + ' ' + str(type([req_usr.email])))

        # PR2018-04-25 arguments: send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None, connection=None, html_message=None)
        mail_count = send_mail(subject, message_str, from_email, [req_usr.email], fail_silently=False)
        if logging_on:
            logger.debug('mail_count: ' + str(mail_count))

        if not mail_count:
            verifcode_key = None

    except Exception as e:
        verifcode_key = None
        exception_str = str(e)
        logger.error(getattr(e, 'message', str(e)))

    return verifcode_key, exception_str
# - end of send_email_verifcode


def create_verificationcode(formname, request):  # PR2022-02-04
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  ----- create_verificationcode -----')

    # create verification key and code, store key_code in usersetting, send key to client, set expiration to 30 minutes
    # get random number between 1,000,000 en 1,999,999, convert to string and get last 6 characters
    # this way you get string from '000000' thru '999999'
    # key is sent to client, code must be entered by user
    # key_code is stored in usersettings
    verif_key = str(randint(1000000, 1999999))[-6:]
    verif_code = str(randint(1000000, 1999999))[-6:]

    key_code = '_'.join((verif_key, verif_code))

    now = datetime.now()  # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07
    expirationtime = now + timedelta(seconds=1800)
    expirationtime_iso = expirationtime.isoformat()

    verification_dict = {'form': formname, 'key_code': key_code, 'expirationtime': expirationtime_iso}
    acc_view.set_usersetting_dict(c.KEY_VERIFICATIONCODE, verification_dict, request)

    if logging_on:
        logger.debug('verif_key: ' + str(verif_key))

    return verif_key, verif_code
# - end of create_verificationcode


def check_verificationcode(upload_dict, formname, request ):  # PR2021-09-8
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  ----- check_verificationcode -----')

    _verificationkey = upload_dict.get('verificationkey')
    _verificationcode = upload_dict.get('verificationcode')

    if logging_on:
        logger.debug('_verificationkey: ' + str(_verificationkey))
        logger.debug('_verificationcode: ' + str(_verificationcode))

    is_ok, is_expired = False, False
    msg_err = None

    if _verificationkey and _verificationcode:
        key_code = '_'.join((_verificationkey, _verificationcode))
    # - get saved key_code
        saved_dict = acc_prm.get_usersetting_dict(c.KEY_VERIFICATIONCODE, request)
        if logging_on:
            logger.debug('saved_dict: ' + str(saved_dict))

        if saved_dict:
# - check if code is expired:
            saved_expirationtime = saved_dict.get('expirationtime')
            # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07
            now_iso = datetime.now().isoformat()
            if logging_on:
                logger.debug('saved_expirationtime: ' + str(saved_expirationtime))
                logger.debug('now_iso: ' + str(now_iso))

            if now_iso > saved_expirationtime:
                is_expired = True
                msg_err = _("The verificationcode has expired.")
            else:
# - check if code is correct:
                saved_form = saved_dict.get('form')
                saved_key_code = saved_dict.get('key_code')
                if logging_on:
                    logger.debug('saved_form: ' + str(saved_form))
                    logger.debug('saved_key_code: ' + str(saved_key_code))

                if saved_form == formname and key_code == saved_key_code:
                    is_ok = True
                else:
                    msg_err = _("The verificationcode you have entered is not correct.")

# - delete setting when expired or ok
            if is_ok or is_expired:
                acc_view.set_usersetting_dict(c.KEY_VERIFICATIONCODE, None, request)
        else:
            msg_err = _("The verificationcode is not found.")
    else:
        msg_err = _("The verificationcode is not entered.")

    if logging_on:
        logger.debug('is_ok: ' + str(is_ok))
        logger.debug('is_expired: ' + str(is_expired))

    return msg_err
# - end of check_verificationcode


############################################################
# also for permits


def add_one_to_count_dict(msg_dict, key):  # PR2022-02-27
    if key in msg_dict:
        msg_dict[key] += 1
    else:
        msg_dict[key] = 1
# - end of def add_one_to_count_dict(msg_dict, key):


def get_status_list_from_status_sum(status_sum):  # PR2021-01-15
    # status_sum:                            117
    # bin:                             0b1110101
    # binary_str:                        1110101
    # binary_str_extended: 000000000000001110101
    # binary_str_cut:            000000001110101
    # binary_str_reversed:       101011100000000
    # status_list: ['1', '0', '1', '0', '1', '1', '1', '0', '0', '0', '0', '0', '0', '0', '0']

    if status_sum is None:
        status_sum = 0
    binary_str = bin(status_sum)[2:]
    binary_str_extended = '00000000000000' + binary_str
    binary_str_cut = binary_str_extended[-15:]
    binary_str_reversed = binary_str_cut[-1::-1]
    status_list = list(binary_str_reversed)
    return status_list
# --- end of get_status_bool_by_index


def get_status_bool_by_index(status_sum, index):  # PR2021-01-15
    status_list = list(bin(status_sum)[-1:1:-1])
    status_bool = False
    if len(status_list) > index and status_list[index] == '1':
        status_bool = True
    return status_bool
# --- end of get_status_bool_by_index


def set_status_sum_by_index(status_sum, index, new_value_bool):  # PR2021-01-15
    #logger.debug(' =============== set_status_sum_by_index ============= ')
    # bin(status_sum): '0b0010111' <class 'str'>   binary string from int
    # bin(status_sum)[-1:1:-1]: '1110100' <class 'str'>     reversed string from binary string, leave out '0b'
    # status_list: ['1', '1', '1', '0', '1', '0', '0']  convert to list

    #logger.debug('status_sum: ' + str(status_sum))
    #logger.debug('index: ' + str(index))
    #logger.debug('new_value_bool: ' + str(new_value_bool))
# - convert status_sum to status_list
    status_list = list(bin(status_sum)[-1:1:-1])
    #logger.debug('status_list: ' + str(status_list))
# - if index > length of list: extend list with zero's
    length = len(status_list)
    if length <= index:
        for i in range(length, index + 1):
            status_list.append('0')
    #logger.debug('extended status_list: ' + str(status_list))

# - replace binary value at index with '1' if new_value_bool = True, else with '0'
    status_list[index] = '1' if new_value_bool else '0'

    #logger.debug('new status_list: ' + str(status_list))
    new_status_str = ''.join(status_list)
    #logger.debug('new new_status_str: ' + str(new_status_str))
    new_status_str_reversed = new_status_str[::-1]
    #logger.debug('new new_status_str_reversed: ' + str(new_status_str_reversed))
# - convert status_list to new_status_sum
    # PR2021-02-06 from https://stackoverflow.com/questions/8928240/convert-base-2-binary-number-string-to-int
    new_status_sum = int(new_status_str_reversed, 2)
    #logger.debug('new_status_sum: ' + str(new_status_sum))

    return new_status_sum
# --- end of set_status_sum_by_index


def get_status_sum(auth1, auth2, auth3, auth4, publ, blocked):
    # PR2022-03-20
    status_sum = 0
    if auth1:
        status_sum += c.STATUS_01_AUTH1
    if auth2:
        status_sum += c.STATUS_02_AUTH2
    if auth3:
        status_sum += c.STATUS_03_AUTH3
    if auth4:
        status_sum += c.STATUS_04_AUTH4
    if publ:
        status_sum += c.STATUS_05_PUBLISHED
    if blocked:
        status_sum += c.STATUS_06_BLOCKED
    return status_sum
# - end of get_status_sum

#################################################################
# ---------- Date functions ---------------

def get_today_dateobj():  # PR2020-10-20
    # function gets today in '2019-12-05' format
    now = datetime.now()
    now_arr = [now.year, now.month, now.day, now.hour, now.minute]
    # today_iso: 2019-11-17 <class 'str'>
    today_dte = get_date_from_arr(now_arr)

    # today_dte: 2019-11-17 <class 'datetime.date'>
    # NIU now_usercomp_dtm = get_datetime_from_arr(now_arr)
    # now: 2019-11-17 07:41:00 <class 'datetime.datetime'>

    return today_dte


def get_datetime_from_arr(arr_int):  # PR2022-11-01
    datetime_obj = None
    if arr_int:
        try:
            datetime_obj = datetime(arr_int[0], arr_int[1], arr_int[2], arr_int[3], arr_int[4])
        except Exception as e:
            logger.error(' '.join((getattr(e, 'message', str(e)), '- arr_int:', str(arr_int), str(type(arr_int)))))

    return datetime_obj

def get_date_from_arr(arr_int):  # PR2019-11-17  # PR2020-10-20 PR2021-08-12
    date_obj = None
    if arr_int:
        try:
            date_obj = date(arr_int[0], arr_int[1], arr_int[2])
        except Exception as e:
            logger.error(' '.join((getattr(e, 'message', str(e)), '- arr_int:', str(arr_int), str(type(arr_int)))))

    return date_obj


def get_date_from_arr_str_ddmmyy(date_str):  # PR2022-06-02
    # format of date_str is "05-20-2022"
    date_obj = None
    if date_str:
        try:
            arr_str = date_str.split('-')
            year_int = arr_str[2]
            month_int = arr_str[1]
            day_int = arr_str[0]
            date_obj = date(year_int, month_int, day_int)
        except Exception as e:
            logger.error(' '.join((getattr(e, 'message', str(e)), '- date_str:', str(date_str))))

    return date_obj


# ################### DATE STRING  FUNCTIONS ###################


def get_dateISO_from_dateOBJ(date_obj):  # PR2019-12-22 from tsa PR2021-08-12
    # use row.rosterdate.isoformat() instead PR2020-06-25
    date_iso = None
    if date_obj:
        try:
            year_str = str(date_obj.year)
            month_str = ('0' + str(date_obj.month))[-2:]
            date_str = ('0' + str(date_obj.day))[-2:]
            date_iso = '-'.join([year_str, month_str, date_str])
            # today_iso: 2019-11-17 <class 'str'>
        except Exception as e:
            logger.error(' '.join((getattr(e, 'message', str(e)), '- date_obj:', str(date_obj), str(type(date_obj)))))

    return date_iso


def get_dateISO_from_string(date_string, format=None):  # PR2019-08-06
    #logger.debug('... get_dateISO_from_string ...')
    #logger.debug('date_string: ' + str(date_string), ' format: ' + str(format))

    # function converts string into given format. Used in employee_import
    if format is None:
        format = 'yyyy-mm-dd'

    new_dat_str = ''
    if date_string:
        # replace / by -
        try:
            date_string = date_string.replace('/', '-')
            if '-' in date_string:
                arr = date_string.split('-')
                if len(arr) >= 2:
                    day_int = 0
                    month_int = 0
                    year_int = 0
                    if format == 'dd-mm-yyyy':
                        day_int = int(arr[0])
                        month_int = int(arr[1])
                        year_int = int(arr[2])
                    elif format == 'mm-dd-yyyy':
                        month_int = int(arr[0])
                        day_int = int(arr[1])
                        year_int = int(arr[2])
                    elif format == 'yyyy-mm-dd':
                        year_int = int(arr[0])
                        month_int = int(arr[1])
                        day_int = int(arr[2])
                    #logger.debug('year_int: ' + str(year_int) + ' month_int: ' + str(month_int) + ' day_int:' + str(day_int))

                    if year_int < 100:
                        currentYear = datetime.now().year
                        remainder = currentYear % 100  # 2019 -> 19
                        year100_int = currentYear // 100  # 2019 -> 20
                        # currentYear = 2019, remainder = 19. When year_int <=29 convert to 2009, else convert to 1997
                        if year_int <= remainder + 10:
                            year_int = year_int + year100_int * 100
                        else:
                            year_int = year_int + (year100_int - 1) * 100

                    year_str = '0000' + str(year_int)
                    year_str = year_str[-4:]
                    month_str = '00' + str(month_int)
                    month_str = month_str[-2:]

                    day_str = '00' + str(day_int)
                    day_str = day_str[-2:]
                    #logger.debug('year_str: ' + str(year_str) + ' month_str: ' + str(month_str) + ' day_str:' + str(day_str))

                    new_dat_str = '-'.join([year_str, month_str, day_str])

        except Exception as e:
            logger.error(' '.join((getattr(e, 'message', str(e)), '- date_string:', str(date_string), str(type(date_string)))))

    return new_dat_str


# ========  get_birthdateiso_from_idnumber  ======= PR2021-08-23
def get_birthdateiso_from_idnumber(idnumber_nodots_stripped):
    birthdate_iso = None

    if idnumber_nodots_stripped:
        if len(idnumber_nodots_stripped) >= 8:
            year = int(idnumber_nodots_stripped[0:4])
            month = int(idnumber_nodots_stripped[4:6])
            day = int(idnumber_nodots_stripped[6:8])
            date_obj = get_date_from_arr((year, month, day))
            if date_obj:
                birthdate_iso = get_dateISO_from_dateOBJ(date_obj)

    return birthdate_iso
# - end of get_birthdateiso_from_idnumber


# ========  get_dateiso_from_excel_ordinal  ======= PR2021-08-23

def get_dateiso_from_excel_ordinal(date_ordinal, error_list):
    # - check if date is a valid date
    # date_ordinal has format of excel ordinal or number '20020823'

    date_iso = None
    if date_ordinal:
        # PR2021-08-23 debug: JPD entered '20020823' as a numeber. accept that too
        if isinstance(date_ordinal, int):
            if date_ordinal > 19000000:
                bd = str(date_ordinal)
                date_iso = '-'.join((bd[0:4], bd[4:6], bd[6:8]))
        else:
            date_obj = get_date_from_excel_ordinal(date_ordinal, error_list)
            if date_obj:
                date_iso = get_dateISO_from_dateOBJ(date_obj)

    return date_iso
# - end of get_dateiso_from_excel_ordinal


# ========  get_date_from_excel_ordinal  ======= PR2021-07-20

def get_date_from_excel_ordinal(excel_ordinal, error_list):
    date_obj = None
    if excel_ordinal:
        try:
            epoch0 = date(1899, 12, 31)
            if excel_ordinal >= 60:
                excel_ordinal -= 1  # Excel leap year bug, 1900 is not a leap year!
            date_obj = (epoch0 + timedelta(days=excel_ordinal))
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            logger.error(' '.join((getattr(e, 'message', str(e)), '- excel_ordinal:', str(excel_ordinal), str(type(excel_ordinal)))))
            error_list.append(' '.join((str(_('An error occurred:')), str(e), str(_("This is not a valid date.")))))

    return date_obj
# - end of get_date_from_excel_ordinal

# >>>>>> This is the right way, I think >>>>>>>>>>>>>

def get_date_from_ISO(date_iso):  # PR2019-09-18 PR2020-03-20
    # this is the simple way, it works though
    #logger.debug('... get_date_from_ISO ...')
    #logger.debug('date_iso: ' + str(date_iso))
    # PR2020-05-04 try is necessary, When creating public holiday schemeitem date_iso = "onph', must return: dte = None
    dte = None
    if date_iso:
        try:
            arr = date_iso.split('-')
            dte = date(int(arr[0]), int(arr[1]), int(arr[2]))
        except:
            pass
    return dte


def get_datetime_naive_from_dateobject(datetime_obj):
    # function removes the timezone from a datetime object PR2021-05-09
    # https://stackoverflow.com/questions/10944047/how-can-i-remove-a-pytz-timezone-from-a-datetime-object

    datetime_naive = None
    if datetime_obj:
        try:
            logger.debug('datetime_obj: ' + str(datetime_obj) + ' type: ' + str(type(datetime_obj)))
            logger.debug('datetime_obj.tzinfo: ' + str(datetime_obj.tzinfo) + ' type: ' + str(type(datetime_obj.tzinfo)))
            # dt.tzinfo: None <class 'NoneType'>
            datetime_naive = datetime_obj.replace(tzinfo=None)
            # datetime_obj: 2021-05-09 01:27:57.041618+00:00 type: <class 'datetime.datetime'>
            logger.debug('datetime_naive: ' + str(datetime_naive) + ' type: ' + str(type(datetime_naive)))
            logger.debug('datetime_naive.tzinfo: ' + str(datetime_naive.tzinfo) + ' type: ' + str(type(datetime_naive.tzinfo)))
            # datetime_naive: 2021-05-09 01:27:57.041618 type: <class 'datetime.datetime'>
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            logger.error('datetime_obj: ' + str(datetime_obj) + ' ' + str(type(datetime_obj)))
    return datetime_obj


def get_datetimelocal_from_datetime_utc(datetime_utc):
    # based on tsa function get_datetimelocal_from_offset PR2021-05-09
    # from https://stackoverflow.com/questions/4563272/convert-a-python-utc-datetime-to-a-local-datetime-using-only-python-standard-lib
    #logger.debug(' +++ get_datetimelocal_from_datetime_naive +++')

    datetime_local = None
    if datetime_utc is not None:
        local_timezone = pytz.timezone('America/Curacao')
        datetime_local = datetime_utc.astimezone(local_timezone)

        #logger.debug('datetime_utc: ' + str(datetime_utc) + ' ' + str(type(datetime_utc)))
        # datetime_utc: 2021-05-08 21:32:57.189035+00:00 <class 'datetime.datetime'>
        #logger.debug('datetime_utc.tzinfo: ' + str(datetime_utc.tzinfo) + ' ' + str(type(datetime_utc.tzinfo)))
        # datetime_utc.tzinfo: UTC <class 'pytz.UTC'>
        #logger.debug('datetime_local: ' + str(datetime_local) + ' ' + str(type(datetime_local)))
        # datetime_local: 2021-05-08 17:32:57.189035-04:00 <class 'datetime.datetime'>
        #logger.debug('datetime_local.tzinfo: ' + str(datetime_local.tzinfo) + ' ' + str(type(datetime_local.tzinfo)))
        # datetime_local.tzinfo: America/Curacao <class 'pytz.tzfile.America/Curacao'>

    return datetime_local


def get_now_formatted_from_now_arr(now_arr):
    #PR2022-07-08
    now_formatted = ''
    if now_arr:
        year_str = str(now_arr[0])
        month_str = ("00" + str(now_arr[1]))[-2:]
        date_str = ("00" + str(now_arr[2]))[-2:]
        hour_str = ("00" + str(now_arr[3]))[-2:]
        minute_str = ("00" + str(now_arr[4]))[-2:]
        now_formatted = ''.join((
            str(now_arr[0]), "-",
            ("00" + str(now_arr[1]))[-2:], "-",
            ("00" + str(now_arr[2]))[-2:], " ",
            ("00" + str(now_arr[3]))[-2:], "u",
            ("00" + str(now_arr[4]))[-2:]))
    return now_formatted


def format_WDMY_from_dte(dte, user_lang, month_abbrev=True):  # PR2020-10-20
    # returns 'zo 16 juni 2019'
    date_WDMY = ''
    if dte:
        try:
            date_DMY = format_DMY_from_dte(dte, user_lang, month_abbrev)
            # get weekdays translated
            if not user_lang in c.WEEKDAYS_ABBREV:
                user_lang = c.LANG_DEFAULT
            weekday_int = int(dte.strftime("%w"))
            if not weekday_int:
                weekday_int = 7
            weekday_str = c.WEEKDAYS_ABBREV[user_lang][weekday_int]
            date_WDMY = ' '.join([weekday_str, date_DMY])
        except:
            pass
    #logger.debug('... format_WDMY_from_dte: ' + str(date_WDMY) + ' type:: ' + str(type(date_WDMY)) + ' user_lang: ' + str(user_lang))
    return date_WDMY


def format_DMY_from_dte(dte, lang, month_abbrev=True):  # PR2019-06-09  # PR2020-10-20 PR2021-08-10 PR2022-05-22
    #logger.debug('... format_DMY_from_dte: ' + str(dte) + ' type:: ' + str(type(dte)) + ' lang: ' + str(lang))
    # returns '16 juni 2019'
    date_DMY = ''
    if dte:
        try:
            year_str = str(dte.year)
            day_str = str(dte.day)
            month_locale = ''
            if month_abbrev:
                if lang in c.MONTHS_ABBREV:
                    month_locale = c.MONTHS_ABBREV[lang]
            else:
                if lang in c.MONTHS_LONG:
                    month_locale = c.MONTHS_LONG[lang]
            month_str = month_locale[dte.month]

            date_DMY = ' '.join([day_str, month_str, year_str])
        except:
            pass
    #logger.debug('... date_DMY: ' + str(date_DMY) + ' type:: ' + str(type(dte)) + ' lang: ' + str(lang))
    return date_DMY


def format_HM_from_dt_local(datetime_local, use24insteadof00, use_suffix, timeformat, user_lang):
    # PR2020-01-26
    # Function returns time : "18.15 u." or "6:15 p.m."
    # 12.00 a.m is midnight, 12.00 p.m. is noon

    display_txt = ''
    is24insteadof00 = False
    if datetime_local:
        # from https://howchoo.com/g/ywi5m2vkodk/working-with-datetime-objects-and-timezones-in-python
        # entered date is dattime-naive, make it datetime aware with  pytz.timezone

        # .strftime("%H") returns zero-padded 24 hour based string '03' or '22'
        hours_int = datetime_local.hour
        minutes_int = datetime_local.minute

        suffix = None
        if use_suffix and user_lang == 'nl':
            suffix = 'u'

        if timeformat.lower() == 'ampm':
            suffix = 'p.m.' if hours_int >= 12 else 'a.m.'
            if hours_int > 12:
                hours_int -= 12
        elif use24insteadof00 and hours_int == 0 and minutes_int == 0:
            hours_int = 24
            is24insteadof00 = True

        hour_str = ''.join(['00', str(hours_int)])[-2:]
        minutes_str = ''.join(['00', str(minutes_int)])[-2:]

        separator = '.' if user_lang == 'nl' else ':'
        display_txt = separator.join([hour_str, minutes_str])

        if suffix:
            display_txt = ' '.join([display_txt, suffix])

    return display_txt


def format_modified_at(modifiedat, user_lang, month_abbrev=True):
    # PR2021-07-13

    datetime_formatted = ''
    if modifiedat:
        # local timezone is set to 'America/Curacao' by default
        datetime_local = get_datetimelocal_from_datetime_utc(modifiedat)
        last_modified_date = datetime_local.date()
        date_formatted = format_DMY_from_dte(last_modified_date, user_lang, month_abbrev)  # True = month_abbrev
        time_formatted = format_HM_from_dt_local(datetime_local, True, True, '24h', user_lang)
        datetime_formatted = date_formatted + ', ' + time_formatted

    return datetime_formatted


def format_number(value, user_lang):
    # PR2022-08-21

    number_formatted = ''
    value_str = str(value) if value else '0'
    if isinstance(value, int):
        if value < 1000:
            number_formatted = value_str
        else:
            delimiter = ',' if user_lang == 'en' else '.'
            number_formatted = delimiter.join((value_str[-4], value_str[-3:] ))
    else:
        number_formatted = value_str

    return number_formatted


def get_modifiedby_formatted(instance, user_lang, skip_modifiedby=False):
    # Function returns 'Laatst gewijzigd door Hans Meijs op 6 mei 2021, 15.55 u'  PR2021-05-09 R2022-05-08
    last_modified_text, date_formatted, time_formatted = '', '', ''
    if instance:
        user_name = '-'
        user = instance.modifiedby
        if user:
            user_name = user.last_name
        datetime_formatted = ''
        if instance.modifiedat:
            # local timezone is set to 'America/Curacao' by default
            datetime_local = get_datetimelocal_from_datetime_utc(instance.modifiedat)
            last_modified_date = datetime_local.date()
            date_formatted = format_DMY_from_dte(last_modified_date, user_lang, True)  # True = month_abbrev

            time_formatted = format_HM_from_dt_local(datetime_local, True, True, '24h', user_lang)
            datetime_formatted = date_formatted + ', ' + time_formatted

        if skip_modifiedby:
            last_modified_text = ' '.join((str(_('Last modified at')), datetime_formatted))
        else:
            last_modified_text = ' '.join(( str(_('Last modified by')), user_name, str(_('at')), datetime_formatted))

    return last_modified_text


def get_published_at_formatted(exam_instance, user_lang):
    # Function returns 'Gepubliceerd op 6 mei 2021, 15.55 u'  P R2022-05-08
    published_at_text, date_formatted, time_formatted = '', '', ''
    if exam_instance:
        published = exam_instance.published
        if published:

            datetime_formatted = ''
            if published.modifiedat:
                # local timezone is set to 'America/Curacao' by default
                datetime_local = get_datetimelocal_from_datetime_utc(published.modifiedat)
                last_modified_date = datetime_local.date()
                date_formatted = format_DMY_from_dte(last_modified_date, user_lang, True)  # True = month_abbrev

                time_formatted = format_HM_from_dt_local(datetime_local, True, True, '24h', user_lang)
                datetime_formatted = date_formatted + ', ' + time_formatted

            published_at_text = str(_('Published at ')) + datetime_formatted
        else:
            published_at_text = str(_('This exam is not published'))
    return published_at_text


def get_submitted_at_formatted(grade_instance, user_lang):
    # Function returns 'Ingediend op 6 mei 2021, 15.55 u'  P R2022-05-08
    published_at_text, date_formatted, time_formatted = '', '', ''
    if grade_instance:
        published = grade_instance.ce_exam_published
        if published:

            datetime_formatted = ''
            if published.modifiedat:
                # local timezone is set to 'America/Curacao' by default
                datetime_local = get_datetimelocal_from_datetime_utc(published.modifiedat)
                last_modified_date = datetime_local.date()
                date_formatted = format_DMY_from_dte(last_modified_date, user_lang, True)  # True = month_abbrev

                time_formatted = format_HM_from_dt_local(datetime_local, True, True, '24h', user_lang)
                datetime_formatted = date_formatted + ', ' + time_formatted

            published_at_text = str(_('Submitted at ')) + datetime_formatted
        else:
            published_at_text = str(_('This exam is not submitted.'))
    return published_at_text
# ----------  end of Date functions ---------------


def get_dict_value(dictionry, key_tuple, default_value=None):
    # PR2020-02-04 like in base.js Iterate through key_tuple till value found
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  get_dict_value  -----')
        logger.debug('     dictionry: ' + str(dictionry))
        logger.debug('     key_tuple: ' + str(key_tuple))
    if key_tuple and dictionry:  # don't use 'dictionary' - is PyCharm reserved word
        for key in key_tuple:
            if logging_on:
                logger.debug('     key: ' + str(key) + ' key_tuple: ' + str(key_tuple))
            if isinstance(dictionry, dict) and key in dictionry:
                dictionry = dictionry[key]
                if logging_on:
                    logger.debug('     new dictionry: ' + str(dictionry))
            else:
                dictionry = None
                break
    if dictionry is None and default_value is not None:
        dictionry = default_value

    if logging_on:
        logger.debug('     return dictionry: ' + str(dictionry))
    return dictionry

# NOT IN USE I think, to be removed
def get_mode_strNIU(self):  # PR2018-11-28
    mode_str = '-'
    if self.mode is not None:
        mode_str = c.MODE_DICT.get(str(self.mode))
    return mode_str


def get_selected_examyear_from_usersetting_without_check(request):  # PR2021-05-31 PR2021-11-03 PR2022-12-09
    #logger.debug(' ----- get_selected_examyear_from_usersetting_without_check ----- ' )
    # this function gets sel_examyear_instance from saved settings.
    # used in students.create_studentsubjectnote_rows, MailmessageUploadView, MailboxUploadView, MailinglistUploadView
    selected_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
    s_ey_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK)
    sel_examyear_instance = sch_mod.Examyear.objects.get_or_none(
        pk=s_ey_pk,
        country=request.user.country
    )
    return sel_examyear_instance
# - end of get_selected_examyear_from_usersetting_without_check


def get_selected_examyear_school_instance_from_usersettingNIU(request):  # PR2021-10-12
    #logger.debug(' ----- get_selected_examyear_from_usersetting_without_check ----- ' )
    # this function gets sel_examyear_instance from saved settings.
    # NOT IN USE - was used in MailmessageUploadView

# - get selected examyear from Usersetting
    selected_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
    s_ey_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK)
    sel_school_instance = None
    sel_examyear_instance = sch_mod.Examyear.objects.get_or_none(
        pk=s_ey_pk,
        country=request.user.country
    )

# - get selected schoolbase from Usersetting, from role if role = school
    if request.user.role == c.ROLE_008_SCHOOL:
        sel_sb_pk = request.user.schoolbase.pk
    else:
        sel_sb_pk = selected_dict.get(c.KEY_SEL_SCHOOLBASE_PK)

    sel_schoolbase = sch_mod.Schoolbase.objects.get_or_none(
        pk=sel_sb_pk,
        country=request.user.country
    )
    sel_school_instance = sch_mod.School.objects.get_or_none(
        base=sel_schoolbase,
        examyear=sel_examyear_instance
    )

    return sel_examyear_instance, sel_school_instance
# - end of get_selected_examyear_from_usersetting_without_check


def get_sel_examyear_with_default(request, request_item_examyear_pk=None):
    # PR2020-12-25 PR2021-08-12 PR2023-01-08
    # called by: get_headerbar_param, download_setting create_or_validate_user_instance, UploadOldAwpView
    # only examyears that are in userallowed records are permitted
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  get_sel_examyear_with_default  -----')
        logger.debug('    username: ' + str(request.user.username))

    def get_saved_examyear_instance():
        saved_examyear_instance = None
        selected_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
        if selected_dict:
            s_ey_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK)
            if s_ey_pk:
                saved_examyear_instance = sch_mod.Examyear.objects.get_or_none(pk=s_ey_pk, country=requsr_country)
        return saved_examyear_instance

    sel_examyear_instance = None
    sel_examyear_tobesaved = False
    multiple_examyears_exist = False

    if request.user and request.user.country:
        requsr_country = request.user.country

# - get list of userallowed_examyears
        allowed_examyear_list = []
        user_allowed_rows = acc_mod.UserAllowed.objects.filter(user=request.user)
        if user_allowed_rows:
            for row in user_allowed_rows:
                allowed_examyear_list.append(row.examyear.pk)
        if logging_on:
            logger.debug('    allowed_examyear_list: ' + str(allowed_examyear_list))

# - skip if there are no allowed_examyears
        if allowed_examyear_list:

# - if there is only 1 allowedexamyear: select that one
            if len(allowed_examyear_list) == 1:
                sel_examyear_instance = sch_mod.Examyear.objects.get_or_none(
                    pk=allowed_examyear_list[0],
                    country=requsr_country
                )
                if logging_on:
                    logger.debug('    there is only 1 allowedexamyear: ' + str(sel_examyear_instance))
                # - save if different from saved_examyear_instance
                if sel_examyear_instance:
                    saved_examyear_instance = get_saved_examyear_instance()
                    if sel_examyear_instance != saved_examyear_instance:
                        sel_examyear_tobesaved = True
            else:
                # - multiple_examyears_exist is used to enable select examyear
                multiple_examyears_exist = True

    # - check if there is a new examyear_pk in request_setting, check if request_examyear exists and is in allowed_examyear_list
            if sel_examyear_instance is None:
                if request_item_examyear_pk and request_item_examyear_pk in allowed_examyear_list:
                    sel_examyear_instance = sch_mod.Examyear.objects.get_or_none(
                        pk=request_item_examyear_pk,
                        country=requsr_country
                    )
                    if sel_examyear_instance is not None:
                        sel_examyear_tobesaved = True

                if logging_on:
                    logger.debug('    sel_examyear_instance: ' + str(sel_examyear_instance))

            # - if None: get saved_examyear_pk from Usersetting, check if saved_examyear exists
            if sel_examyear_instance is None:
                saved_examyear_instance = get_saved_examyear_instance()
                if saved_examyear_instance and saved_examyear_instance.pk in allowed_examyear_list:
                    sel_examyear_instance = saved_examyear_instance

                if logging_on:
                    logger.debug('    saved_examyear_instance: ' + str(sel_examyear_instance))

    # - if None: get today's examyear
            # get this year in Jan through July, get next year in Aug through Dec PR2020-09-29 PR2020-12-24
            if sel_examyear_instance is None:
                todays_examyear_instance = get_todays_examyear_instance(requsr_country)
                if todays_examyear_instance and todays_examyear_instance.pk in allowed_examyear_list:
                    sel_examyear_instance = todays_examyear_instance
                    sel_examyear_tobesaved = True

                if logging_on:
                    logger.debug('    todays_examyear_instance: ' + str(sel_examyear_instance))

    # - if None: get latest examyear_int of table
            if sel_examyear_instance is None:
                latest_examyear_instance = sch_mod.Examyear.objects.filter(country=requsr_country).order_by('-code').first()
                if latest_examyear_instance and latest_examyear_instance.pk in allowed_examyear_list:
                    sel_examyear_instance = latest_examyear_instance
                    sel_examyear_tobesaved = True
                if logging_on:
                    logger.debug('    latest_examyear_instance: ' + str(sel_examyear_instance))

        if logging_on:
            logger.debug('    multiple_examyears_exist: ' + str(multiple_examyears_exist))
            logger.debug('    sel_examyear_instance: ' + str(sel_examyear_instance))
            logger.debug('    sel_examyear_tobesaved: ' + str(sel_examyear_tobesaved))
# - also add sel_examperiod and sel_examtype, used in page grades

    return sel_examyear_instance, sel_examyear_tobesaved, multiple_examyears_exist
# --- end of get_sel_examyear_with_default

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


def get_this_examyear_int():
    # get this year in Jan thru July, get next year in Aug thru Dec PR2020-09-29 PR2020-12-24
    now = timezone.now()
    this_examyear_int = now.year
    if now.month + 1 > c.MONTH_START_EXAMYEAR:
        this_examyear_int = now.year + 1
    return this_examyear_int


def get_todays_examyear_instance(country):  # PR2020-12-24 PR2021-08-06
    # get this year in Jan thru July, get next year in Aug thru Dec PR2020-09-29 PR2020-12-24
    examyear_instance = None
    if country:
        try:
            todays_examyear_int = get_this_examyear_int()
            examyear_instance = sch_mod.Examyear.objects.filter(
                country=country,
                code=todays_examyear_int
            ).first()
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
    return examyear_instance
# - end of get_todays_examyear_instance


def get_todays_examyear_or_latest_instance(country):
    # get this year in Jan thru July, get next year in Aug thru Dec PR2020-09-29 PR2020-12-24
    examyear_instance = get_todays_examyear_instance(country)
# - get latest examyear if todays_examyear does not exist
    if examyear_instance is None:
        examyear_instance = sch_mod.Examyear.objects.filter(country=country).order_by('-code').first()
    return examyear_instance


def get_saved_sel_depbase_instance(request):  # PR2020-12-24 PR2021-09-04
    #logger.debug('  -----  get_saved_sel_depbase_instance  -----')
    sel_depbase_instance = None
# - get saved selected_pk's from Usersetting, key: selected_pk
    req_user = request.user
    if req_user:
        selected_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
# - get saved_depbase_pk, check if saved_depbase exists
        if selected_dict:
            s_db_pk = selected_dict.get(c.KEY_SEL_DEPBASE_PK)
    # - get selected examyear
            if s_db_pk:
                sel_depbase_instance = sch_mod.Department.objects.get_or_none(pk=s_db_pk)
    return sel_depbase_instance


def get_depbase_list_field_sorted_zerostripped(depbase_list):  # PR2018-08-23
    # sort depbase_list. List ['16', '15', '0', '18'] becomes ['0', '15', '16', '18'].
    # Sorted list is necessary, otherwise data_has_changed will not work properly (same values in different order gives modified=True)
    # PR2018-08-27 debug. Also remove value '0'
    # function will store depbase_list as: [;15;16;18;] with delimiters at the beginning and end,
    # so it can filter depbase_list__contains =";15;"
    if depbase_list:
        depbase_list_sorted = sorted(depbase_list)
        #logger.debug('get_depbase_list_field_sorted_zerostripped depbase_list_sorted: <' + str(depbase_list_sorted) + '> Type: ' + str(type(depbase_list_sorted)))

        sorted_depbase_list = ''
        if depbase_list_sorted:
            for dep in depbase_list_sorted:
                #logger.debug('get_depbase_list_field_sorted_zerostripped dep: <' + str(dep) + '> Type: ' + str(type(dep)))
                # skip zero
                if dep != '0':
                    sorted_depbase_list = sorted_depbase_list + ';' + str(dep)
        if sorted_depbase_list:
            # PR2018-08-30 Was: slice off the first character ';'
            # sorted_depbase_list = sorted_depbase_list[1:]
            # PR2018-08-30 add delimiter ';' at the end
            sorted_depbase_list += ';'

            #logger.debug('get_depbase_list_field_sorted_zerostripped sorted_depbase_list: <' + str(sorted_depbase_list) + '> Type: ' + str(type(sorted_depbase_list)))
            return sorted_depbase_list
        else:
            return None
    else:
        return None


def has_unread_mailbox_items(examyear, req_user):
    # --- function checks if this user this examyear has unread mail_inbox rows PR2021-10-29
    # -   skip deleted unread mail
    # - PR2021-11-04 debug: filter on examyear.code, not on examyear.pk, to retrieve also messages from other countries
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== has_unread_mailbox_items ============= ')
        logger.debug('examyear.pk: ' + str(examyear.pk))
        logger.debug('req_user.pk: ' + str(req_user.pk))

    has_items = False
    try:
        sql_keys = {'ey_code': examyear.code, 'req_usr_id': req_user.pk}
        sql = ' '.join((
            "SELECT 1 FROM schools_mailbox AS mb",
            "INNER JOIN schools_mailmessage AS msg ON (msg.id = mb.mailmessage_id)",
            "INNER JOIN schools_examyear AS ey ON (ey.id = msg.examyear_id)",

            "WHERE ey.code = %(ey_code)s::INT",
            "AND mb.user_id = %(req_usr_id)s::INT",
            "AND NOT mb.read AND NOT mb.deleted",
            "AND msg.sentdate IS NOT NULL",
            "LIMIT 1"))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            row = cursor.fetchone()
            if row:
                has_items = True
        if logging_on:
           logger.debug(' has_items: ' + str(has_items))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return has_items


def system_updates(examyear, request):
    # these are once-only updates in tables. Data will be changed / moved after changing fields in tables
    # after uploading the new version the function can be removed

# PR2021-03-26 run this to update text in ex-forms, when necessary
    #if request.user.role == c.ROLE_128_SYSTEM:
    awpr_lib.update_library(examyear, request)

    transfer_grade_tobedeleted_to_deletedONCEONLY(request)

# functions calcultes POK of all failed students and stors it in StudentSubjects PR2023-01-21
    calcPok2022AndSaveInStudsubjONCEONLY(request)


# once only function converts allowed deps, levels and subjects to a dict and stores it in allword_schools PR2022-11-23
    #convertAllowedSectionsONCEONLY(request)

# PR 2022-10-09 one time function to fill table EnvelopSubject
    # fillEnvelopSubjectONCEONLY(request)

# PR 2022-07-03 one time function to add secret exams to
    # add_ntermONCEONLY(request)

    #get_long_pws_title_pws_subjectsONCEONLY(request)

    #recalc_reex_count(request)

    # show_unmatched_reex_rows()

# PR 2022-06-05 one time function to recalc number of exemptions, reex, reex03, thumbrule and put it in student
    #calc_count_reex_etc(request)

# PR 2022-05-28 one time function to set rule_avg_pece_sufficient = TRUE, rule_core_notatevlex = FALSE
    # for all departments SXM and CUR departments Havo/Vwo
    #set_ce_avg_rule(request)

# PR 2022-05-28 one time function to set rule_core_sufficient = TRUE, rule_core_notatevlex = FALSE
    # for departments Havo/Vwo
    #set_core_sufficient_rule(request)

# PR 2022-05-28 one time function to set rule_grade_sufficient = TRUE, rule_gradesuff_notatevlex = TRUE
    # subjects 'cav' and 'lo' in 'Havo' and 'Vwo'
    #set_cav_lo_sufficient_rule(request)

# PR 2022-05-26 one time function to set thumb_rule = True for Havo/Vwo excluding core subjects
    #set_thumb_rule(request)

#PR2022-05-03 debug: Oscar Panneflek grade not showing. Tobeleted was still true, after undelete subject
    #show_deleted_grades(request)

# PR2022-05-16 add usergroup 'download' to all users with usergroups other than 'read'
    # add_usergroup_download_archive(request)

# PR2022-05-15 field pescore was temporary used to store ce_exam_score
    # move value of pescore to field ce_exam_score, set pescore = null
    #move_pescore_to_ce_exam_score(request)

# PR2022-05-15 # debug: Yolande van Erven Ancilla Domini : pescore not calculated. recalc missing pescore
    # must come after move_pescore_to_ce_exam_score
    #recalc_ce_score(request)

# PR2022-05-11 debug: Yolande van Erven Ancilla Domini: pescore not calculated. recalc missing pescore
    #recalc_score_of_ce_result()

# PR2022-05-03 debug: Oscar Panneflek grade not showing. Tobeleted was still true, after undelete subject
    #show_deleted_grades(request)

# PR2022-05-02 recalc amount and scalelength in exams
    #recalc_amount_and_scalelength_of_assignment(request)

# PR2022-04-18 add usergroup 'download' to not 'read' en non null users
    #add_usergroup_download(request)

# PR2022-04-18 add no_ce_years = '2020' to_schemeitems
    #add_no_ce_years_to_schemeitems(request)

# PR2022-04-17 add exemption_year 2021 when field exemption_year is empty
    #add_exemption_year(request)

    # PR2021-10-11 move otherlang from subject to schemitem, after this: must delete field otherlang from subject
    # transfer_otherlang_from_subj_to_schemeitem(request)

    #PR2021-08-05 add SXMSYS school if not exists
    # add_sxmsys_school_if_not_exist(request)

    #transfer_depbases_from_array_to_string()

# - end of system_updates


def reset_show_msg(request):
    # PR 2022-06-01 function resets open_args
    # called by Loggedin, to reset before setting is retrieved
    # this function deletes key 'open_args' from the usersetting of all users

    # to reset hiding messages: remove 'reset_show_msg' from schools_systemupdate manually

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- reset_show_msg -------')
    try:
        name = 'reset_show_msg'
        exists = sch_mod.Systemupdate.objects.filter(
            name=name
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))
        if not exists:
            # reset values
            sql = "DELETE FROM accounts_usersetting WHERE key='open_args'"
            with connection.cursor() as cursor:
                cursor.execute(sql)

        # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name=name
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
# -end of reset_show_msg


def transfer_grade_tobedeleted_to_deletedONCEONLY(request):
    # - from 2023 gade field 'tobedeleted' not in use any more, use field 'deleted' instead.
    #   Transfer values from  'tobedeleted' to 'deleted'

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- transfer_grade_tobedeleted_to_deletedONCEONLY -------')

    try:
        name = 'transfer_grade_tobedeleted'
        exists = sch_mod.Systemupdate.objects.filter(
            name=name
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))

        if not exists:

            sql = "UPDATE students_grade SET deleted = TRUE WHERE students_grade.tobedeleted;"

            with connection.cursor() as cursor:
                cursor.execute(sql)

    # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name=name
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('    systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
# end of transfer_grade_tobedeleted_to_deletedONCEONLY


def calcPok2022AndSaveInStudsubjONCEONLY(request):
    # functions calcultes POK of all failed students and stors it in StudentSubjects PR2023-01-21
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- calcPok2022AndSaveInStudsubjONCEONLY -------')

    try:
        name = 'calc_pok2022'
        exists = sch_mod.Systemupdate.objects.filter(
            name=name
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))

        if not exists:

            exam_years = sch_mod.Examyear.objects.filter(
                code=2022
            )
            for exam_year in exam_years:
                if logging_on:
                    logger.debug('exam_year: ' + str(exam_year))

    # -  set thumbrule_allowed = True in exam_year 2022
                    # PR2023-01-21 field thumbrule_allowed added, to skip thumbrule from 2023
                    # set thumbrule_allowed = True in 2022

                    setattr(exam_year, 'thumbrule_allowed', True)
                    exam_year.save()

                no_centralexam = exam_year.no_centralexam

                students = stud_mod.Student.objects.filter(
                    school__examyear=exam_year,
                    deleted=False,
                    tobedeleted=False,
                    result=c.RESULT_FAILED,
                    partial_exam=False
                ).order_by('lastname', 'firstname')

                for student in students:
                    if logging_on:
                        logger.debug('student: ' + str(student))

                    is_evelex = student.iseveningstudent or student.islexstudent
                    valid_years = 10 if is_evelex else 1
                    pok_validthru = exam_year.code + valid_years

                    studsubjects = stud_mod.Studentsubject.objects.filter(
                        student=student,
                        tobedeleted=False,
                        deleted=False
                    )
                    for studsubj in studsubjects:
                        si = studsubj.schemeitem
                        subj_code = si.subject.base.code

                        sesr_grade = studsubj.gradelist_sesrgrade
                        pece_grade = studsubj.gradelist_pecegrade
                        final_grade = studsubj.gradelist_finalgrade
                        use_exem = studsubj.gradelist_use_exem

                        if logging_on:
                            logger.debug(' subj_code : ' + str(subj_code))
                            logger.debug('   sesr_grade : ' + str(sesr_grade))
                            logger.debug('   pece_grade : ' + str(pece_grade))
                            logger.debug('   final_grade : ' + str(final_grade))

            # calc if this subject has pok
                        has_pok = grade_calc.calc_pok(
                            no_centralexam=no_centralexam,
                            gradetype=si.gradetype,
                            is_combi=si.is_combi,
                            weight_se=si.weight_se,
                            weight_ce=si.weight_ce,
                            subj_code=subj_code,
                            use_exemp=use_exem,
                            no_input=False if final_grade else True,
                            sesr_grade=sesr_grade,
                            pece_grade=pece_grade,
                            final_grade=final_grade
                        )
                        if logging_on:
                            logger.debug('   has_pok : ' + str(has_pok))

                        if has_pok:
                            # has proof of knowledge = True when pok_validthru has value PR2021-09-07
                            studsubj.pok_validthru = pok_validthru

                            # PR2022-07-30 pok_sesr etc added, to store proof of knowledge / proof of exemption
                            studsubj.pok_sesr = sesr_grade
                            studsubj.pok_pece = pece_grade
                            studsubj.pok_final = final_grade
                            studsubj.save()
                            if logging_on:
                                logger.debug('   >> studsubj.pok_final : ' + str(studsubj.pok_final))
                                logger.debug('   >> studsubj.pok_validthru : ' + str(studsubj.pok_validthru))
                                logger.debug('   >> studsubj.pk : ' + str(studsubj.pk))

    # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name=name
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('    systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

# -end of calcPok2022AndSaveInStudsubjONCEONLY


def convertAllowedSectionsONCEONLY(request):
    # functions converts allowed deps, levels and subjects to a dict and stores it in allowerd_schools PR2022-11-23 PR2022-12-03
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- convertAllowedSectionsONCEONLY -------')

    def get_subject_dict(examyear_pk):
        subject_dict = {}

        sql_keys = {'ey_id': examyear_pk}
        sql = ' '.join(["SELECT subj.base_id,",
                    "ARRAY_AGG(DISTINCT dep.base_id) AS depbase_id_arr,",
                    "ARRAY_AGG(DISTINCT lvl.base_id) AS lvlbase_id_arr",

                    "FROM subjects_schemeitem AS si",
                    "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                    "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
                    "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id)",
                    "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
                    "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",

                    "WHERE subj.examyear_id = %(ey_id)s::INT",
                    "GROUP BY subj.base_id"
                    ])

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = cursor.fetchall()
            for row in rows:
                subject_dict[row[0]] = [row[1], row[2]]

        return subject_dict

    def get_user_list(examyear_pk):
        sql_keys = {'ey_pk': examyear_pk}
        sql = ' '.join(
            ["SELECT u.id, u.last_name, u.role, u.schoolbase_id, school.depbases,",
            "u.usergroups, u.allowed_schoolbases, u.allowed_depbases, u.allowed_levelbases,",
            "u.allowed_subjectbases, u.allowed_clusterbases",
            "FROM accounts_user AS u",
            "INNER JOIN schools_school AS school ON (school.base_id = u.schoolbase_id)",
            "WHERE school.examyear_id = %(ey_pk)s::INT"
            ])
        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            user_list = dictfetchall(cursor)
        return user_list

    def get_dep_lvlreq_dict(examyear_pk):
        sql_keys = {'ey_pk': examyear_pk}
        sql_list = [
            "SELECT depbase.id AS depbase_id, dep.level_req",
            "FROM schools_department AS dep",
            "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
            "WHERE dep.examyear_id = %(ey_pk)s::INT"]
        sql = ' '.join(sql_list)

        dep_lvlreq_dict = {}
        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = cursor.fetchall()
            for row in rows:
                dep_lvlreq_dict[row[0]] = row[1]

        # dep_lvlreq_dict: {1: True, 2: False, 3: False}
        return dep_lvlreq_dict

    def get_allowed_arr(allowed_str, fldName):
        allowed_arr = []
        if not allowed_str:
            if fldName == 'allowed_depbases':
                # add all departments of this examyear when allowed_str is empty (key of dep_lvlreq_dict contains depabse_id)
                for depbase_pk_int in dep_lvlreq_dict:
                    if depbase_pk_int in user_school_depbases_arr:
                        allowed_arr.append(depbase_pk_int)
            elif fldName == 'allowed_levelbases':
                # return 'all (-9) when when allowed_str is empty
                allowed_arr.append(-9)
        else:
            arr = allowed_str.split(';')
            if fldName == 'allowed_levelbases' and len(arr) == 3:
                # return 'all (-9) when all levels are selected
                allowed_arr.append(-9)
            else:
                for pk_str in arr:
                    pk_int = int(pk_str)
                    # skip when allowed_depbase_pk not in user_school_depbases_arr
                    if fldName != 'allowed_depbases' or pk_int in user_school_depbases_arr:
                        allowed_arr.append(pk_int)
        return allowed_arr

    def create_allowed_subjbase_arr(depbase_pk, lvlbase_pk, allowed_subjectbases_arr):
        allowed_subjbase_arr = []
        # loop through allowed_subjbase_arr
        for subjbase_pk in allowed_subjectbases_arr:
            # check if this subject exists in this dep / lvl:
            # subjects_dict = {157: [[1, 2, 3], [4, 5, 6, None]]}
            subject_arr = subjects_dict.get(subjbase_pk)
            if subject_arr:
                depbase_id_arr = subject_arr[0]
                lvlbase_id_arr = subject_arr[1]
                if depbase_pk in depbase_id_arr:
                    if lvlbase_pk == -9 or lvlbase_pk in lvlbase_id_arr:
                        allowed_subjbase_arr.append(subjbase_pk)
        return allowed_subjbase_arr

    def skip_auth4_only(examyear_code, usergroups_arr):
        # dont create if user is only corrector (auth4) or has no usergroups
        if usergroups_arr:
            skip = (examyear_code != 2022 and
                    'auth4' in usergroups_arr and
                    'auth1' not in usergroups_arr and
                    'auth2' not in usergroups_arr and
                    'auth3' not in usergroups_arr and
                    'admin' not in usergroups_arr
                )
        else:
            # skip when there is no usergroup - should not be possible
            skip = True
        return skip

    try:
        name = 'fill_userallowed'
        exists = sch_mod.Systemupdate.objects.filter(
            name=name
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))

        if not exists:
            examyears = sch_mod.Examyear.objects.filter().all().order_by('country_id', 'code')

            for examyear in examyears:
                examyear_pk = examyear.pk
                examyear_code = examyear.code
                if logging_on:
                    logger.debug('  +++++   examyear: ' + str(examyear))
                    logger.debug('          examyear_pk: ' + str(examyear_pk))

            # - create a dict with key = depbase_id and value = lvlreq
                # dep_lvlreq_dict: {1: True, 2: False, 3: False} key = depbase_id
                dep_lvlreq_dict = get_dep_lvlreq_dict(examyear_pk)

            # - create list of users per examyear
                users = get_user_list(examyear_pk)

                # subjects_dict = {157: [[1, 2, 3], [4, 5, 6, None]]}
                subjects_dict = get_subject_dict(examyear_pk)

            # - loop through user list
                for user in users:
                    user_pk = user.get('id')
                    user_schoolbase_id = user.get('schoolbase_id')

                    user_school_depbases_arr = []
                    user_school_depbases = user.get('depbases')
                    if user_school_depbases:
                        arr = user_school_depbases.split(';')
                        for pk_str in arr:
                            user_school_depbases_arr.append(int(pk_str))
                    if logging_on:
                        logger.debug(str(user.get('last_name')))
                        logger.debug('    .. user_schoolbase_id: ' + str(user_schoolbase_id))
                        logger.debug('    .. user_pk: ' + str(user_pk))
                        logger.debug('    .. user: ' + str(user))

                    allowed_depbases = user.get('allowed_depbases')
                    allowed_subjectbases = user.get('allowed_subjectbases')

                # - create arr with allowed_lvlbases
                    # set to [-9] when allowed_lvlbases is None, otherwise e.g. [1, 2 ]
                    allowed_levelbases = user.get('allowed_levelbases')
                    allowed_levelbases_arr = get_allowed_arr(allowed_levelbases, 'allowed_levelbases')
                    # allowed_levelbases_arr: [-9] <class 'list'>

                # - create arr with allowed_subjbases
                    # set to [] when allowed_subjbases is None
                    allowed_subjectbases_arr = get_allowed_arr(allowed_subjectbases, 'allowed_subjectbases')
                    # allowed_subjectbases_arr: [133, 155] <class 'list'>

                # - get schoolbase_pk:
                    # set to user.schoolbase_id when user_role = school
                    # set to 'all schools' (id=-9) when user is not role school,
                    # set to 0 when None (is not possible)
                    user_role = user.get('role')
                    allowed_sections_dict = {}
                    allowed_school_dict = {}
                    schoolbase_pk = user.get('schoolbase_id') or 0 if user_role == c.ROLE_008_SCHOOL else -9
                    if logging_on:
                        logger.debug('       schoolbase_pk: ' + str(schoolbase_pk) + ' ' + str(type(schoolbase_pk)))

                # - loop through allowed_depbase_arr
                    # there s no 'all' [-9] in allowed_depbase_arr
                    allowed_depbase_arr = get_allowed_arr(allowed_depbases, 'allowed_depbases')
                    if logging_on:
                        logger.debug('       allowed_depbase_arr: ' + str(allowed_depbase_arr) + ' ' + str(type(allowed_depbase_arr)))

                    for depbase_pk in allowed_depbase_arr:
                        allowed_depbase_dict = {}

                    # - loop through allowed_levelbases_arr,
                        lvl_req = dep_lvlreq_dict.get(depbase_pk) or False
                        if not lvl_req:
                            allowed_levelbases_arr = [-9]
                        if logging_on:
                            logger.debug('       allowed_levelbases_arr: ' + str(allowed_levelbases_arr) + ' ' + str(type(allowed_levelbases_arr)))

                        # allowed_levelbases_arr: [-9] <class 'list'>
                        for lvlbase_pk in allowed_levelbases_arr:

                            allowed_subjbase_arr = create_allowed_subjbase_arr( depbase_pk, lvlbase_pk, allowed_subjectbases_arr)
                            # allowed_subjbase_arr: [117, 136] <class 'list'>
                            if logging_on:
                                logger.debug('       allowed_subjbase_arr: ' + str(allowed_subjbase_arr) + ' ' + str(type(allowed_subjbase_arr)))

                            allowed_depbase_dict[lvlbase_pk] = allowed_subjbase_arr

                        allowed_school_dict[depbase_pk] = allowed_depbase_dict

                    allowed_sections_dict[schoolbase_pk] = allowed_school_dict
                    # allowed_sections_dict: {2: {1: {-9: [117, 136]}}} <class 'dict'>

                # - convert  user_usergroups to array
                    user_usergroups = user.get('usergroups')
                    usergroups_arr = user_usergroups.split(';') if user_usergroups else None
                    if logging_on:
                        logger.debug('       usergroups_arr: ' + str(usergroups_arr) + ' ' + str( type(usergroups_arr)))

                # don't create in 2023 if user is corrector (auth4) and has no other usergroups
                    skip = skip_auth4_only(examyear_code, usergroups_arr)
                    if not skip:

                # - convert allowed_clusters to array of integers
                        user_allowed_clusterbases = user.get('allowed_clusterbases')
                        allowed_clusters_arr = None
                        # only create cluster_list when examyear = 2022, leave allowed_clusters empty in 2023 PR2023-01-27
                        if examyear_code == 2022 and user_allowed_clusterbases:
                            arr_str = user_allowed_clusterbases.split(';')

                            pk_int_list = []
                            for pk_str in arr_str:
                                pk_int = int(pk_str)
                                if pk_int not in pk_int_list:
                                    pk_int_list.append(pk_int)
                            if pk_int_list:
                                pk_int_list.sort()
                                allowed_clusters_arr = pk_int_list

                    # - create userallowed row for each user and examyear
                        """
                        set_userallowed_dict(user_pk, examyear_pk, usergroups_arr, allowed_clusters_arr, allowed_sections_dict)
                        """
                        acc_view.set_userallowed_dict(
                            user_pk=user_pk,
                            examyear_pk=examyear_pk,
                            usergroups_arr=usergroups_arr,
                            allowed_clusters_arr=allowed_clusters_arr,
                            allowed_sections_dict=allowed_sections_dict
                        )
                        if logging_on:
                            logger.debug('allowed_sections_dict: ' + str(allowed_sections_dict))

    # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name=name
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
# -end of convertAllowedSectionsONCEONLY


# fill table EnvelopSubjec with data from Exams PR2022-10-09
def fillEnvelopSubjectONCEONLY(request):
    # PR2022-10-09 one time function fills table EnvelopSubjec with data from Exams PR2022-10-09

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- fillEnvelopSubjectONCEONLY -------')
    try:
        name = 'fill_envelopsubject'
        exists = sch_mod.Systemupdate.objects.filter(
            name=name
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))

        if not exists:

# - loop through schemitems, grouped by subj / dep / lvl
            sql = ' '.join(["SELECT si.subject_id, scheme.department_id, scheme.level_id",
                                    "FROM subjects_schemeitem AS si",
                                    "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id)",
                                    "GROUP BY si.subject_id, scheme.department_id, scheme.level_id"
                                    ])
            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = dictfetchall(cursor)

            for row in rows:
                if logging_on:
                    logger.debug('si row: ' + str(row))
                subject_id = row.get('subject_id')
                department_id = row.get('department_id')
                level_id = row.get('level_id')

        # create envelopsubject for each dep / lvl / subj if it does not exist

# get EnvelopSubject if it already exists
                envelopsubject = subj_mod.Envelopsubject.objects.filter(
                    subject_id=subject_id,
                    department_id=department_id,
                    level_id=level_id
                ).first()

                if logging_on:
                    logger.debug('   envelopsubject exists: ' + str(envelopsubject))

                if envelopsubject is None:
                    envelopsubject = subj_mod.Envelopsubject(
                        subject_id=subject_id,
                        department_id=department_id,
                        level_id=level_id
                    )
                    envelopsubject.save(request=request)

                    if logging_on:
                        logger.debug('   envelopsubject created: ' + str(envelopsubject))

                if envelopsubject is not None:
                    # get exam with data of this envelopsubject
                    crit = Q(ete_exam=True) & \
                           Q(subject=envelopsubject.subject) & \
                           Q(department=envelopsubject.department) & \
                           Q(level=envelopsubject.level) & \
                           Q(examperiod=envelopsubject.examperiod) & \
                           (Q(envelopbundle__isnull=False) |
                            Q(datum__isnull=False) |
                            Q(begintijd__isnull=False) |
                            Q(eindtijd__isnull=False) |
                            Q(has_errata=True) )

                    exam = subj_mod.Exam.objects.filter(crit).first()

                    if logging_on:
                        logger.debug('   exam exists: ' + str(exam))

                    # if exam with data exists: copy to envelopsubject
                    if exam is not None:

                        setattr(envelopsubject, 'envelopbundle', exam.envelopbundle)
                        setattr(envelopsubject, 'firstdate', exam.datum)
                        setattr(envelopsubject, 'starttime', exam.begintijd)
                        setattr(envelopsubject, 'endtime', exam.eindtijd)
                        setattr(envelopsubject, 'has_errata', exam.has_errata)
                        setattr(envelopsubject, 'modifiedby', exam.evl_modifiedby)
                        setattr(envelopsubject, 'modifiedat', exam.evl_modifiedat)
                        envelopsubject.save()

                        if logging_on:
                            logger.debug('   >> exam copied to envelopsubject: ' + str(exam))

    # - end of  for row in rows

   # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name=name
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
# -end of fillEnvelopSubjectONCEONLY


# get long psw_title and pws_subjcts
def add_ntermONCEONLY(request):
    values = [
        {'nex_id': 22991, 'sty_id': 3, 'opl_code': 'VMBO', 'leerweg': 'BB', 'omschrijving': '*BB Frans GEHEIM EXAMEN tijdvak 2'},
        {'nex_id': 22992, 'sty_id': 3, 'opl_code': 'VMBO', 'leerweg': 'KB', 'omschrijving': '*KB Frans GEHEIM EXAMEN tijdvak 2'},
        {'nex_id': 22993, 'sty_id': 3, 'opl_code': 'VMBO', 'leerweg': 'BB', 'omschrijving': '*BB Spaans GEHEIM EXAMEN tijdvak 2'},
        {'nex_id': 22994, 'sty_id': 3, 'opl_code': 'VMBO', 'leerweg': 'KB', 'omschrijving': '*KB Spaans GEHEIM EXAMEN tijdvak 2'}
    ]

    for value in values:
        nex_id = value.get('nex_id')
        exists = subj_mod.Ntermentable.objects.filter(
            nex_id=nex_id
        ).exists()
        if not exists:
            ntermentable_instance = subj_mod.Ntermentable(
                nex_id=nex_id,
                examyear_id=1,
                sty_id=value.get('sty_id'),
                opl_code=value.get('opl_code'),
                leerweg=value.get('leerweg'),
                omschrijving=value.get('omschrijving'),
                tijdvak=2
            )
            ntermentable_instance.save(request=request)


# get long psw_title and pws_subjcts
def get_long_pws_title_pws_subjectsONCEONLY(request):
    # PR 2022-06-11 one time function to get long psw_title and pws_subjcts, so i can send email to schools

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- get_long_pws_title_pws_subjectsONCEONLY -------')
    try:
        from reportlab.pdfbase.pdfmetrics import stringWidth, registerFont
        from reportlab.pdfbase.ttfonts import TTFont
        import math
# - get Garamond font
        try:
            filepath = s.STATICFILES_FONTS_DIR + 'Garamond.ttf'
            ttfFile = TTFont('Garamond', filepath)
            registerFont(ttfFile)
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))


        selected_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)
        s_ey_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK)
        sel_examyear_instance = sch_mod.Examyear.objects.get_or_none(pk=s_ey_pk)
        if sel_examyear_instance:
            sql_dict = {'ey_code': sel_examyear_instance.code}
    # - update exemption_count in student
            sql_list = [
                "SELECT sbase.code AS sbase_code, school.name AS school_name, depbase.code AS depbase_code,",
                "CASE WHEN stud.prefix IS NULL THEN CONCAT(TRIM(stud.lastname), ', ', TRIM(stud.firstname)) ELSE",
                    "CONCAT(TRIM(stud.prefix), ' ', TRIM(stud.lastname), ', ', TRIM(stud.firstname))",
                "END AS fullname,",

                "studsubj.pws_title, studsubj.pws_subjects",

                "FROM students_studentsubject AS studsubj",
                "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",

                "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                "INNER JOIN schools_schoolbase AS sbase ON (sbase.id = school.base_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",

                "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",
                "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",

                "WHERE ey.code = %(ey_code)s::INT",
                "AND (LENGTH(TRIM(studsubj.pws_title))>60 OR LENGTH(TRIM(studsubj.pws_subjects))>50)",
                "AND NOT stud.tobedeleted AND NOT studsubj.tobedeleted",
                "ORDER BY sbase.code, depbase.code, stud.lastname, stud.firstname"
            ]
            sql = ' '.join(sql_list)
            with connection.cursor() as cursor:
                cursor.execute(sql, sql_dict)
                if logging_on:
                    for row in dictfetchall(cursor):
                        pws_title = (row.get('pws_title') or '').strip()
                        pws_subjects = (row.get('pws_subjects') or '').strip()
                        pws_title_width = stringWidth(pws_title, 'Times-Roman', 10) if pws_title else 0
                        pws_title_width_roundup_mm = math.ceil(pws_title_width / 72 * 25.4)
                        max_title_width_mm = c.GRADELIST_PWS_TITLE_MAX_LENGTH_MM

                        pws_subjects_width = stringWidth(pws_subjects, 'Times-Roman', 10) if pws_subjects else 0
                        pws_subjects_width_roundup_mm = math.ceil(pws_subjects_width / 72 * 25.4)
                        max_subjects_width_mm = c.GRADELIST_PWS_SUBJECTS_MAX_LENGTH_MM

                        if pws_title_width_roundup_mm > max_title_width_mm or \
                                pws_subjects_width_roundup_mm > max_subjects_width_mm:

                            log_list = [str(row.get('sbase_code')),
                                        str(row.get('school_name')),
                                        str(row.get('depbase_code')),
                                        str(row.get('fullname'))
                                        ]
                            if pws_title_width > 267:
                                log_list.extend(["- Titel:", "'" + str(pws_title) + "'", '(breedte:', str(pws_title_width_roundup_mm), 'mm, max:',  str(max_title_width_mm), 'mm)'])

                            if pws_subjects_width > 208:
                                log_list.extend(['- Vakken:', "'" + str(pws_subjects) + "'", '(breedte:', str(pws_subjects_width_roundup_mm), 'mm, max:',  str(max_subjects_width_mm), 'mm)'])

                            logger.debug(str(' '.join(log_list)))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
# -end of get_long_pws_title_pws_subjectsONCEONLY


######################################
def recalc_exemption_countNIU(request):
    # PR 2022-06-11 one time function to recalculate exemption
    # Dont run this one, it might give problems
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- recalc_exemption_count -------')
    try:
        name = 'recalc_exemption_count'
        exists = sch_mod.Systemupdate.objects.filter(
            name=name
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))
        if not exists:

# - get list of studsubj_id that have reex
            sub_sql_list = ["SELECT studsubj.id AS studsubj_id",
                    "FROM students_grade AS grd",
                    "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                    "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                    "WHERE grd.examperiod =", str(c.EXAMPERIOD_EXEMPTION),
                    "AND NOT grd.tobedeleted AND NOT grd.deleted AND NOT studsubj.tobedeleted AND NOT stud.tobedeleted",
                    "GROUP BY studsubj.id"
            ]
            sub_sql = ' '.join(sub_sql_list)

# - set has_exemption = TRUE in studsubj if it is False
            sql_list = [
                "WITH sub_sql AS (", sub_sql, ")",
                "UPDATE students_studentsubject AS studsubj",
                "SET has_exemption = TRUE",
                "FROM sub_sql",
                "WHERE studsubj.id = sub_sql.studsubj_id",
                "AND NOT studsubj.has_exemption",
                "RETURNING studsubj.id, studsubj.has_exemption"
            ]
            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql)
                if logging_on:
                    for row in cursor.fetchall():
                        logger.debug('updated has_exemption row: ' + str(row))

# - count number of exemption of each student
            sub_sql_list = ["SELECT stud.id AS stud_id, COUNT(*) AS exemption_count",
                            "FROM students_studentsubject AS studsubj",
                            "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                            "WHERE studsubj.has_exemption",
                            "AND NOT studsubj.tobedeleted AND NOT stud.tobedeleted",
                            "GROUP BY stud.id"
                            ]
            sub_sql = ' '.join(sub_sql_list)

# - update exemption_count in student
            sql_list = [
                "WITH sub_sql AS (", sub_sql, ")",
                "UPDATE students_student AS stud",
                "SET exemption_count = sub_sql.exemption_count",
                "FROM sub_sql",
                "WHERE stud.id = sub_sql.stud_id",
                "AND stud.exemption_count <> sub_sql.exemption_count",
                "RETURNING stud.id, stud.exemption_count"
            ]
            sql = ' '.join(sql_list)
            with connection.cursor() as cursor:
                cursor.execute(sql)
                if logging_on:
                    for row in cursor.fetchall():
                        logger.debug('updated exemption_count row: ' + str(row))

   # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name=name
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
# -end of recalc_exemption_count


def recalc_reex_count(request):
    # PR 2022-06-11 one time function to recalculate reex
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- recalc_reex_count -------')
    try:
        name = 'recalc_reex_count'
        exists = sch_mod.Systemupdate.objects.filter(
            name=name
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))
        if not exists:

# - get list of studsubj_id that have reex
            sub_sql_list = ["SELECT studsubj.id AS studsubj_id",
                    "FROM students_grade AS grd",
                    "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                    "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                    "WHERE grd.examperiod =", str(c.EXAMPERIOD_SECOND),
                    "AND NOT grd.tobedeleted AND NOT grd.deleted AND NOT studsubj.tobedeleted AND NOT stud.tobedeleted",
                    "GROUP BY studsubj.id"
            ]
            sub_sql = ' '.join(sub_sql_list)

# - set has_reex = TRUE in studsubj if it is False (happened in 20 cases)
            sql_list = [
                "WITH sub_sql AS (",  sub_sql, ")",
                "UPDATE students_studentsubject AS studsubj",
                "SET has_reex = TRUE",
                "FROM sub_sql",
                "WHERE studsubj.id = sub_sql.studsubj_id",
                "AND NOT studsubj.has_reex",
                "RETURNING studsubj.id, studsubj.has_reex"
            ]
            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql)
                if logging_on:
                    for row in cursor.fetchall():
                        logger.debug('has_reex row: ' + str(row))

# - count number of reex of each student
            sub_sql_list = ["SELECT stud.id AS stud_id, COUNT(*) AS reex_count",
                            "FROM students_studentsubject AS studsubj",
                            "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                            "WHERE studsubj.has_reex",
                            "AND NOT studsubj.tobedeleted AND NOT stud.tobedeleted",
                            "GROUP BY stud.id"
                            ]
            sub_sql = ' '.join(sub_sql_list)

# - update reex_count in student
            sql_list = [
                "WITH sub_sql AS (", sub_sql, ")",
                "UPDATE students_student AS stud",
                "SET reex_count = sub_sql.reex_count",
                "FROM sub_sql",
                "WHERE stud.id = sub_sql.stud_id",
                "AND stud.reex_count <> sub_sql.reex_count",
                "RETURNING stud.id, stud.reex_count"
            ]
            sql = ' '.join(sql_list)
            with connection.cursor() as cursor:
                cursor.execute(sql)
                for row in cursor.fetchall():
                    logger.debug('updated reex_count row: ' + str(row))

        # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name=name
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
# -end of recalc_reex_count


def set_ce_avg_rule(request):
    # PR 2022-05-28 one time function to set rule_avg_pece_sufficient = TRUE, rule_core_notatevlex = FALSE
    # for all departments SXM and CUR departments Havo/Vwo
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- set_ce_avg_rule -------')
    try:
        name = 'ce_avg_rule'
        exists = sch_mod.Systemupdate.objects.filter(
            name=name
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))
        if not exists:
            # reset values
            sql = "UPDATE subjects_scheme SET rule_avg_pece_sufficient=FALSE, rule_avg_pece_notatevlex=FALSE"
            with connection.cursor() as cursor:
                cursor.execute(sql)

            sql_list = [
                "WITH sub_sql AS (",
                    "SELECT scheme.id",
                    "FROM subjects_scheme AS scheme",
                    "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
                    "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
                    "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",
                    "INNER JOIN schools_country AS country ON (country.id = ey.country_id)",
                    "WHERE (depbase.code = 'Havo') OR (depbase.code = 'Vwo') OR (depbase.code = 'Vsbo' AND country.abbrev = 'Sxm')",
                ")",
                "UPDATE subjects_scheme",
                "SET rule_avg_pece_sufficient = TRUE, rule_avg_pece_notatevlex = FALSE",
                "FROM sub_sql",
                "WHERE subjects_scheme.id = sub_sql.id"
            ]
            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql)

        # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name=name
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
# -e nd of set_ce_avg_rule


#####################################


def calc_count_reex_etc(request):
    # PR 2022-06-05 one time function to recalc number of exemptions, reex, reex03, thumbrule and put it in student
    # for all departments SXM and CUR departments Havo/Vwo
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- calc_count_reex_etc -------')

    try:
        name = 'calc_count_reex_etc'
        exists = sch_mod.Systemupdate.objects.filter(
            name=name
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))
        if not exists:
            for field in ('has_exemption', 'has_sr', 'has_reex', 'has_reex03', 'is_thumbrule'):
                stud_view.update_reexcount_etc_in_student(field)

        # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name=name
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
# -e nd of set_ce_avg_rule


def set_core_sufficient_rule(request):
    # PR 2022-05-28 one time function to set rule_core_sufficient = TRUE, rule_core_notatevlex = FALSE
    # for departments Havo/Vwo
    logging_on = False  #s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- set_core_sufficient_rule -------')
    try:
        key = 'core_sufficient'
        exists = sch_mod.Systemupdate.objects.filter(
            name=key
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))
        if not exists:
            # reset values
            sql = "UPDATE subjects_scheme SET rule_core_sufficient = FALSE, rule_core_notatevlex = FALSE"
            with connection.cursor() as cursor:
                cursor.execute(sql)

            sql_list = [
                "WITH sub_sql AS (",
                    "SELECT scheme.id",
                    "FROM subjects_scheme AS scheme",
                    "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
                    "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
                    "WHERE (depbase.code = 'Havo' OR depbase.code = 'Vwo')",
                ")",
                "UPDATE subjects_scheme",
                "SET rule_core_sufficient = TRUE, rule_core_notatevlex = FALSE",
                "FROM sub_sql",
                "WHERE subjects_scheme.id = sub_sql.id"
            ]
            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql)

        # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name=key
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
# -e nd of set_core_sufficient_rule


def set_cav_lo_sufficient_rule(request):
    # PR 2022-05-28 one time function to set rule_grade_sufficient = TRUE, rule_gradesuff_notatevlex = TRUE
    # subjects 'cav' and 'lo' in 'Havo' and 'Vwo'
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- set_cav_lo_sufficient_rule -------')
    try:
        key = 'cav_lo_sufficient'
        exists = sch_mod.Systemupdate.objects.filter(
            name=key
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))
        if not exists:
            # reset values
            sql = "UPDATE subjects_schemeitem SET rule_grade_sufficient = FALSE, rule_gradesuff_notatevlex = FALSE"
            with connection.cursor() as cursor:
                cursor.execute(sql)

            sql_list = [
                "WITH sub_sql AS (",
                    "SELECT subj_si.id",

                    "FROM subjects_schemeitem AS subj_si",
                    "INNER JOIN subjects_subject AS subj ON (subj.id = subj_si.subject_id)",
                    "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                    "INNER JOIN subjects_scheme AS scheme ON (scheme.id = subj_si.scheme_id)",
                    "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
                    "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
                    "WHERE subjbase.code='lo' OR subjbase.code='cav'"
                    "AND (depbase.code = 'Havo' OR depbase.code = 'Vwo')",
                ")",
                "UPDATE subjects_schemeitem",
                "SET rule_grade_sufficient = TRUE, rule_gradesuff_notatevlex = TRUE",
                "FROM sub_sql",
                "WHERE subjects_schemeitem.id = sub_sql.id"
            ]
            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql)

        # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name=key
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
# -e nd of set_cav_lo_sufficient_rule


def set_thumb_rule(request):
    # PR 2022-05-26 one time function to set thumb_rule = True for Havo/Vwo excluding core subjects
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- set_thumb_rule -------')
    try:
        key = 'set_thumb_rule'
        exists = sch_mod.Systemupdate.objects.filter(
            name=key
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))
        if not exists:
            # reset values
            sql = "UPDATE subjects_schemeitem SET thumb_rule = FALSE"
            with connection.cursor() as cursor:
                cursor.execute(sql)

            sql_list = [
                "WITH sub_sql AS (",
                    "SELECT subj_si.id",
                    "FROM subjects_schemeitem AS subj_si",
                    "INNER JOIN subjects_scheme AS scheme ON (scheme.id = subj_si.scheme_id)",
                    "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
                    "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
                    "WHERE NOT subj_si.is_core_subject",
                    "AND (depbase.code = 'Havo' OR depbase.code = 'Vwo')",
                ")",
                "UPDATE subjects_schemeitem",
                "SET thumb_rule = TRUE",
                "FROM sub_sql",
                "WHERE subjects_schemeitem.id = sub_sql.id"
            ]
            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql)

        # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name=key
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
# -e nd of set_thumb_rule


def move_pescore_to_ce_exam_score(request):
    # PR2022-05-15 field pescore was temporary used to store ce_exam_score
    # move value of pescore to field ce_exam_score, set pescore = null
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- move_pescore_to_ce_exam_score -------')

    try:
        key = 'move_pescore_to_ceexamscore'
        exists = sch_mod.Systemupdate.objects.filter(
            name=key
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))

        if not exists:
            sql_list = [
                "UPDATE students_grade",
                "SET ce_exam_score = pescore, pescore = null",
                "WHERE ce_exam_id IS NOT NULL AND pescore IS NOT NULL",
                "RETURNING ce_exam_score, pescore;"
            ]
            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()

            if logging_on:
                logger.debug('rows: ' + str(rows))

        # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name=key
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
# - end of move_pescore_to_ce_exam_score


def recalc_grade_ce_examscoreXXX(request):
    # PR2022-05-15 # debug: Yolande van Erven Ancilla Domini : pescore not calculated. recalc missing pescore
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- recalc_score_of_ce_result -------')

    try:
        key = 'recalc_score_of_result'
        exists = sch_mod.Systemupdate.objects.filter(
            name=key
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))

        if not exists:
            crit = Q(ce_exam_id__isnull=False) & \
                   Q(ce_exam_result__isnull=False) & \
                   Q(ce_exam_score__isnull=True) & \
                   ( Q(ce_exam_blanks__isnull=True) | Q(ce_exam_blanks=0) )

            grades = stud_mod.Grade.objects.filter(crit)

            for grade_instance in grades:
                exam_instance = grade_instance.ce_exam
                if exam_instance:
                    stud_name = ' '.join((
                        grade_instance.studentsubject.student.school.base.code or '',
                        grade_instance.studentsubject.student.department.base.code or '',
                        grade_instance.studentsubject.student.lastname or '',
                        grade_instance.studentsubject.student.firstname or ''
                    ))
                    exam_name = ' '.join((
                        exam_instance.subject.base.code or '',
                        exam_instance.department.base.code or '',
                        exam_instance.level.base.code or '',
                        exam_instance.version or ''
                    ))
                    logger.debug(str(stud_name) + ': ' + exam_name)

                    result_str = getattr(grade_instance, 'ce_exam_result')
                    total_score, total_blanks, total_has_errors = \
                        grade_view.get_all_result_with_assignment_dict_CALC_SCORE_BLANKS(
                            partex_str=getattr(exam_instance, 'partex'),
                            assignment_str=getattr(exam_instance, 'assignment'),
                            keys_str=getattr(exam_instance, 'keys'),
                            result_str=result_str
                        )
                    if logging_on:
                        logger.debug('     total_score: ' + str(total_score))
                        logger.debug('     total_blanks: ' + str(total_blanks))
                        logger.debug('     total_has_errors: ' + str(total_has_errors))

                    if not total_has_errors:
                        setattr(grade_instance, 'ce_exam_score', total_score)
                        setattr(grade_instance, 'ce_exam_blanks', total_blanks)
                        grade_instance.save()
                        logger.debug('     saved ce_exam_score: ' + str(getattr(grade_instance, 'ce_exam_score')))
                    else:
                        logger.debug('     ERRORS: ' + str(total_has_errors))

            # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name=key
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))


def show_deleted_grades(request):
    #PR2022-05-03 debug: Oscar Panneflek grade not showing. Tobeleted was still true, after undelete subject
    # check other 36 grades that have tobedeleted=True
    logging_on = s.LOGGING_ON
    if logging_on:  # and request.user.role == c.ROLE_128_SYSTEM:
        logger.debug(' ------- show_deleted_grades, examperiod=1 -------')
        rows = stud_mod.Grade.objects.filter(
            tobedeleted=True,
            studentsubject__tobedeleted=False,
            examperiod=1
        ).order_by('studentsubject__student__school__base__code', 'studentsubject__student__lastname')
        if rows:
            if logging_on:
                logger.debug(' ------- grade_tobedeleted = True, studsubj_tobedeleted = False')
                for row in rows:
                    msg_txt = ' '.join((
                            str(row.studentsubject.student.school.base.code),
                            str(row.studentsubject.student.lastname), str(row.studentsubject.student.firstname) ,
                            str(row.studentsubject.schemeitem.subject.base.code),
                            'studsubj.del', str(row.studentsubject.tobedeleted),
                            ' stud.del', str(row.studentsubject.student.tobedeleted)))
                    logger.debug(msg_txt)

        logger.debug(' ------- show_deleted_grades studentsubject__tobedeleted=True, examperiod=1 -------')
        rows = stud_mod.Grade.objects.filter(
            studentsubject__tobedeleted=True,
            examperiod=1
        ).order_by('studentsubject__student__school__base__code', 'studentsubject__student__lastname')

        if rows:
            for row in rows:
                msg_txt = ' '.join((
                    str(row.studentsubject.student.school.base.code),
                    str(row.studentsubject.student.school.name), '-',
                    str(row.studentsubject.student.pk), '-',
                    str(row.studentsubject.student.lastname), str(row.studentsubject.student.firstname),
                    str(row.studentsubject.schemeitem.subject.name_nl),
                    'studsubj.del', str(row.studentsubject.tobedeleted),
                    ' stud.del', str(row.studentsubject.student.tobedeleted)))
                logger.debug(msg_txt)


def show_unmatched_reex_rows():
    #PR2022-05-08 debug: Friedeman: enetered reex has no 'has_reex' in studsubj  not showing.
    # Tobeleted was still true, after undelete subject
    # check other 36 grades that have tobedeleted=True
    logging_on = s.LOGGING_ON
    if logging_on:  # and request.user.role == c.ROLE_128_SYSTEM:
        logger.debug(' ------- show_unmatched_reex_rows, examperiod=1 -------')
        rows = stud_mod.Grade.objects.filter(
            tobedeleted=False,
            studentsubject__tobedeleted=False,
            studentsubject__has_reex=False,
            examperiod=2
        ).order_by('studentsubject__student__school__base__code', 'studentsubject__student__lastname')
        if rows:
            if logging_on:
                logger.debug(' ------- show_unmatched_reex_rows')
                for row in rows:
                    msg_txt = ' '.join((
                            str(row.studentsubject.student.school.base.code),
                            str(row.studentsubject.student.lastname), str(row.studentsubject.student.firstname) ,
                            str(row.studentsubject.schemeitem.subject.base.code),
                            'garde_pk', str(row.pk),
                            'studsubj_pk', str(row.studentsubject.pk),
                            ' has_reex', str(row.studentsubject.has_reex)))
                    logger.debug(msg_txt)

        logger.debug(' ------- show_unmatched_reex_rows -------')


def recalc_amount_and_scalelength_of_assignment(request):
    # PR2022-05-02  PR2022-05-20
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- recalc_amount_and_scalelength_of_assignment -------')

    try:
        key = 'recalc_assignment'
        exists = sch_mod.Systemupdate.objects.filter(
            name=key
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))

        if not exists:
            exams = subj_mod.Exam.objects.filter( ete_exam=True)
            for exam in exams:
                total_amount, total_maxscore, total_blanks, total_keys_missing, has_changed = grade_view.calc_amount_and_scalelength_of_assignment(exam)
                if has_changed:
                    setattr(exam, 'scalelength', total_maxscore)
                    setattr(exam, 'amount', total_amount)
                    exam.save()

        # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name=key
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))


def add_usergroup_download_archive(request):
    # PR2022-05-16 add usergroup 'download' and archive to all users with usergroups other than 'read'

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- add_usergroup_download -------')
    try:
        key = 'add_ug_archive'
        exists = sch_mod.Systemupdate.objects.filter(
            name=key
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))
        if not exists:
            # skip users whose usergroups is empty or only 'read'
            users = acc_mod.User.objects.filter(
            ).exclude(usergroups__isnull=True).exclude(usergroups__exact='').exclude(usergroups__exact='read')
            if users:
                for user in users:

                    arr = user.usergroups.split(';')
                    if 'download' not in arr:
                        arr.append('download')
                    arr.sort()

                    usergroups_str = ';'.join(arr)

                    setattr(user,'usergroups', usergroups_str)
                    user.save()

        # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name=key
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
# - end of add_usergroup_download


def add_exemption_year(request):
    # PR2022-04-17 add exemption_year 2021 when field exemption_year is empty
    # from now on exemption_year will be added when creating exemption grdae
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- add_exemption_year -------')
    try:
        exists = sch_mod.Systemupdate.objects.filter(
            name='add_exemption_year'
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))
        if not exists:
            sql_list = [
                "UPDATE students_studentsubject",
                "SET exemption_year = 2021",
                "WHERE has_exemption AND exemption_year IS NULL",
            ]
            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql)

        # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name='add_exemption_year'
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))


def add_no_ce_years_to_schemeitems(request):
    # PR2022-04-18 add no_ce_years '2020' when field no_ce_years is empty and weight_ce = 0
    # from now on exemption_year will be added when creating exemption grdae
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- add_no_ce_years_to_schemeitems -------')

    try:
        exists = sch_mod.Systemupdate.objects.filter(
            name='add_no_ce_years'
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))
        if not exists:
            sql_list = [
                "UPDATE subjects_schemeitem",
                "SET no_ce_years = '2020'",
                "WHERE weight_ce > 0 AND no_ce_years IS NULL",
            ]
            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql)

        # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name='add_no_ce_years'
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
# - end of add_no_ce_years_to_schemeitems


def transfer_otherlang_from_subj_to_schemeitem(request):
    # PR 2021-10-12 one time function to move otherlang from table subjects to schemeitem
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- transfer_otherlang_from_subj_to_schemeitem -------')
    try:
        exists = sch_mod.Systemupdate.objects.filter(
            name='transfer_otherlang_from_subj_to_schemeitem'
        ).exists()
        if logging_on:
            logger.debug('exists: ' + str(exists))
        if not exists:
            sql_list = [
                "UPDATE subjects_schemeitem AS si",
                "SET otherlang = subj.otherlang",
                "FROM subjects_subject AS subj",
                "WHERE si.subject_id = subj.id",
                "RETURNING si.id"
            ]
            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql)

        # - add function to systemupdate, so it won't run again
            systemupdate = sch_mod.Systemupdate(
                name='transfer_otherlang_from_subj_to_schemeitem'
            )
            systemupdate.save(request=request)
            if logging_on:
                logger.debug('systemupdate: ' + str(systemupdate))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))


def add_sxmsys_school_if_not_exist(request):  # PR2021-08-05
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- add_sxmsys_school_if_not_exist -------')

# get SXM country
    sxm_country = get_country_instance_by_abbrev('sxm')

    if sxm_country:
# get SXM examyear of today
        sxm_examyear = None
        try:
            sxm_examyear = get_todays_examyear_instance(sxm_country)

# - create SXM examyear of today if it doesnt exist yet
            if sxm_examyear is None:
                todays_examyear_int = get_this_examyear_int()
                sxm_examyear = sch_mod.Examyear(
                    country=sxm_country,
                    code=todays_examyear_int
                )
                sxm_examyear.save(request=request)
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

        if logging_on:
            logger.debug('sxm_examyear: ' + str(sxm_examyear))

# get SXMSYS schoolbase
        sxmsys_schoolbase = None
        try:
            sxmsys_schoolbase = sch_mod.Schoolbase.objects.filter(
                country=sxm_country,
                code__iexact='sxmsys'
            ).first()
            if sxmsys_schoolbase is None:
                sxmsys_schoolbase = sch_mod.Schoolbase(
                    country=sxm_country,
                    code='SXMSYS',
                    defaultrole=128
                )
                sxmsys_schoolbase.save()
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

        if logging_on:
            logger.debug('sxmsys_schoolbase: ' + str(sxmsys_schoolbase))

        if sxmsys_schoolbase and sxm_examyear:

# - get SXMSYS school of this year
            sxmsys_school = None
            try:
                sxmsys_school = sch_mod.School.objects.filter(
                    base=sxmsys_schoolbase,
                    examyear=sxm_examyear
                ).first()
                if sxmsys_school is None:
                    sxmsys_school = sch_mod.School(
                        base=sxmsys_schoolbase,
                        examyear=sxm_examyear,
                        name='Panta Rhei',
                        abbrev='Panta Rhei',
                        activated=True,
                        activatedat=timezone.now()
                    )
                    sxmsys_school.save(request=request)
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

            if logging_on:
                logger.debug('sxmsys_school: ' + str(sxmsys_school))

            if sxmsys_school:
# - get SXMSYS user
                sxmsys_user = None
                try:
                    user_name = 'Hans'
                    last_name = 'Hans Meijs'
                    email_address = 'hmeijs@gmail.com'
                    usergroups = 'admin;edit;read'

        # - check if user exists
                    id_str = '000000' + str(sxmsys_schoolbase.pk)
                    schoolbase_prefix = id_str[-6:]
                    prefixed_username = schoolbase_prefix + user_name

                    sxmsys_user = acc_mod.User.objects.filter(
                        country=sxm_country,
                        schoolbase=sxmsys_schoolbase,
                        username__iexact=prefixed_username
                    ).first()

        # - add user if user does not exists
                    if sxmsys_user is None:
                        sxmsys_user = acc_mod.User(
                            country=sxm_country,
                            schoolbase=sxmsys_schoolbase,
                            username=prefixed_username,
                            last_name=last_name,
                            email=email_address,
                            role=c.ROLE_128_SYSTEM,
                            usergroups=usergroups,
                            is_active=True,
                            activated=False,
                            lang=c.LANG_DEFAULT,
                            modified_by=request.user,
                            modified_at=timezone.now())
                        sxmsys_user.save(request=request)

                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

                if logging_on:
                    logger.debug('sxmsys_user: ' + str(sxmsys_user))
# - end of add_sxmsys_school_if_not_exist


def get_country_instance_by_abbrev(abbrev):
    # get country by abbrev 'sxm' or 'cur' PR2021-08-06

    country = None
    if abbrev:
        try:
            country = sch_mod.Country.objects.filter(
                abbrev__iexact=abbrev
            ).first()
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
    return country
# - end of get_country_instance_by_abbrev


def transfer_depbases_from_array_to_string():
    subjecttypes = subj_mod.Subjecttype.objects.all()
    for subjecttype in subjecttypes:
        if subjecttype.depbases:
            depbases_list = list(map(str, subjecttype.depbases))
            subjecttype.depbases = ';'.join(depbases_list)
            subjecttype.depbases = None
            subjecttype.save()

    transfer_depbases(sch_mod.School.objects.all())
    transfer_depbases(sch_mod.School_log.objects.all())

    transfer_depbases(subj_mod.Level.objects.all())
    transfer_depbases(subj_mod.Level_log.objects.all())

    transfer_depbases(subj_mod.Sector.objects.all())
    transfer_depbases(subj_mod.Sector_log.objects.all())

    transfer_depbases(subj_mod.Subject.objects.all())
    transfer_depbases(subj_mod.Subject_log.objects.all())

    transfer_depbases(subj_mod.Subjecttype.objects.all())
    transfer_depbases(subj_mod.Subjecttype_log.objects.all())

    transfer_depbases(subj_mod.Cluster.objects.all())
    transfer_depbases(subj_mod.Cluster_log.objects.all())


def transfer_depbases(instances):
    for instance in instances:
        if instance.depbases:
            depbases_list = list(map(str, instance.depbases))
            instance.depbases = ';'.join(depbases_list)
            instance.depbases = None
            instance.save()


def dictfetchall(cursor):
    # PR2019-10-25 from https://docs.djangoproject.com/en/2.1/topics/db/sql/#executing-custom-sql-directly
    # creates dict from output cursor.execute instead of list
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def dictfetchone(cursor):
    # Return one row from a cursor as a dict  PR2020-06-28
    return_dict = {}
    try:
        columns = [col[0] for col in cursor.description]
        return_dict = dict(zip(columns, cursor.fetchone()))
    except:
        pass
    return return_dict


def dictfetchrows(cursor):
    # PR2019-10-25 from https://docs.djangoproject.com/en/2.1/topics/db/sql/#executing-custom-sql-directly
    # creates dict from output cusror.execute instead of list
    # key is first column of row
    #starttime = timer()

    #  cursor.description:
    #  (Column(name='action', type_code=1043, display_size=None, internal_size=24, precision=None, scale=None, null_ok=None),
    #  Column(name='perm_system', type_code=16, display_size=None, internal_size=1, precision=None, scale=None, null_ok=None),
    #  Column(name='perm_admin', type_code=16, display_size=None, internal_size=1, precision=None, scale=None, null_ok=None),

    #  columns:
    #  ['action', 'perm_system', 'perm_admin', 'perm_anlz', 'perm_auth3', 'perm_auth2', 'perm_auth1', 'perm_edit', 'perm_read']

    columns = [col[0] for col in cursor.description]
    return_dict = {}
    for row in cursor.fetchall():
        logger.debug(">>>>> row: " + str(row))
        return_dict[row[0]] = dict(zip(columns, row))
    #elapsed_seconds = int(1000 * (timer() - starttime) ) /1000
    #elapsed_seconds = (timer() - starttime)
    #return_dict['elapsed_milliseconds'] = elapsed_seconds * 1000
    return return_dict


def register_font_arial():  # PR2022-09-02
    # from https://www.download-free-fonts.com/details/89466/arial-black
    # PR2022-10-19 downloaded arial-corsivo-2.ttf (renamed to arialitalic221019) from  https://www.download-free-fonts.com/download/89015/bf6ffae4262cb2209cae8e98078c1dcc
    # PR2022-10-19 downloaded arialbi.ttf (renamed to arialbolditalic221019) from  https://www.download-free-fonts.com/download/89015/bf6ffae4262cb2209cae8e98078c1dcc

    try:
        filepath = s.STATICFILES_FONTS_DIR + 'arial220815.ttf'
        ttfFile = TTFont('Arial', filepath)
        pdfmetrics.registerFont(ttfFile)

        filepath = s.STATICFILES_FONTS_DIR + 'arialblack220815.ttf'
        ttfFile = TTFont('Arial_Black', filepath)
        pdfmetrics.registerFont(ttfFile)

        filepath = s.STATICFILES_FONTS_DIR + 'arialbd.ttf'
        ttfFile = TTFont('Arial_Bold', filepath)
        pdfmetrics.registerFont(ttfFile)

        filepath = s.STATICFILES_FONTS_DIR + 'ariali.ttf'
        ttfFile = TTFont('Arial_Italic', filepath)
        pdfmetrics.registerFont(ttfFile)

        filepath = s.STATICFILES_FONTS_DIR + 'arialbi.ttf'
        ttfFile = TTFont('Arial_Bold_Italic', filepath)
        pdfmetrics.registerFont(ttfFile)

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))


def register_font_calibri():  # PR2022-09-02
    try:
        filepath = s.STATICFILES_FONTS_DIR + 'Calibri.ttf'
        ttfFile = TTFont('Calibri', filepath)
        pdfmetrics.registerFont(ttfFile)

        filepath = s.STATICFILES_FONTS_DIR + 'Calibri_Bold.ttf'
        ttfFile = TTFont('Calibri_Bold', filepath)
        pdfmetrics.registerFont(ttfFile)

        filepath = s.STATICFILES_FONTS_DIR + 'Calibri_Italic.ttf'
        ttfFile = TTFont('Calibri_Italic', filepath)
        pdfmetrics.registerFont(ttfFile)

        filepath = s.STATICFILES_FONTS_DIR + 'Calibri_Bold_Italic.ttf'
        ttfFile = TTFont('Calibri_Bold_Italic', filepath)
        pdfmetrics.registerFont(ttfFile)

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))


def get_exam_extended_key(envelopsubject_instance):  # PR2022-09-02  PR2022-10-10
    extended_key = None
    """
    PR2022-10-10 was: extended_key = depbase_pk _ lvlbase_pk _ subjbase_pk _ examperiod _ ete_exam (1 if ete_exam else 0)
    extended_key = depbase_pk _ lvlbase_pk _ subjbase_pk
    printlabel_dict = { 1_5_126: [
    """
    if envelopsubject_instance:
        depbase_pk = envelopsubject_instance.department.base_id or 0
        lvlbase_pk = envelopsubject_instance.level.base_id if envelopsubject_instance.level else 0
        subjbase_pk = envelopsubject_instance.subject.base_id or 0
        #examperiod = envelopsubject_instance.examperiod or 0
        #ete_exam = 1 if envelopsubject_instance.ete_exam else 0

        extended_key = '_'.join((
            str(depbase_pk),
            str(lvlbase_pk),
            str(subjbase_pk)
            #str(examperiod),
            #str(ete_exam)
        ))
    return extended_key

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

def message(req_usr, page_name ='None'):
    # PR2018-08-18 Give message when page is not enabled, page is enabled if _page_message = None
    # school admin may add his own school, subjects etc. Is function, not form
    # system and insp may add schoolyear
    #         _has_permit = False
    # req_usr.is_role_insp_or_system_and_group_admin is: req_usr.is_authenticated AND (req_usr.is_role_system OR req_usr.is_role_insp) AND (req_usr.is_usergroup_admin:

    _no_permission =_("You don't have permission to view this page.")

# ===== every user must be authenticated
    if not req_usr.is_authenticated:
        # logger.debug('message : user not authenticated')
        return _("You must be logged in to view this page.")
    # logger.debug('message : user is authenticated')

# ===== every insp and school user must have a country PR2018-09-15
    if not req_usr.is_role_system:
        if not req_usr.country:
# >>>>>
            return _("You are not connected to a country. You cannot view this page.")

# ===== every school user must have a school PR2018-09-15
    if not req_usr.is_role_insp_or_admin_or_system:
        if not req_usr.schoolbase:
            return _("You are not connected to a school. You cannot view this page.")

# ==============================================================
# ----- these pages can be viewed without country selected:
# ==============================================================
# - userlist: only admin can view and modify userlist
    if page_name == 'user_view_modify':
        # only admins can view user list
        if not req_usr.is_usergroup_admin:
            return _no_permission
        else:
            return None
# - countrylist: only system can view countrylist
    if page_name == 'country_view':
        # logger.debug('page: country_view username: ' + str(req_usr.username) + ' role: ' + str(req_usr.role))
        if not req_usr.is_role_system:
            # logger.debug('page: not req_usr.is_role_system')
# >>>
            return _("You don't have permission to view countries.")
        else:
            return None # Not disabled: role_system can view country list
# =====================================================================
# ===== country selected
# =====================================================================
    if not req_usr.country:
        # logger.debug('page: user not connected to a country')
# >>>>>
        return _("You are not connected to a country. You cannot view this page.")
# =====================================================================
# ===== the rest of the pages cannot be viewed without country selected
# =====================================================================
# - userlist, but only by role_insp
    if page_name == 'user_view':
        # logger.debug('page: user_view')
        if req_usr.is_role_insp:
            # logger.debug('page: user is_role_insp')
            return None  # Not disabled:  role_insp can view userlist without school selected
        elif not req_usr.schoolbase:  # role_school need school selected to view userlist
            # logger.debug('page: user not connected to a school')
            return _("You are not connected to a school. You cannot view this page.")
        else:
            # logger.debug('page: user connected to a school')
            return None  # Not disabled:  role_system can view userlist without country selected

# - examyear_list, can only be viewed by role_system and role_insp
    if page_name == 'examyear_view':
        # logger.debug('page: examyear_view')
        if not req_usr.is_role_insp_or_admin_or_system:
            # logger.debug('page: is_role_insp_or_system_and_group_admin')
            return _("You don't have permission to view exam years.")
        else:
            # logger.debug('page: return False')
            return None  # Not disabled:  role_system and role_insp can view examyear_list

# - examyear_modify, only by role_system and role_insp, only admin
    # TODO exclude read, authorize and None permissions
    if page_name == 'examyear_modify':
        # logger.debug('page: examyear_modify')
        if not acc_prm.is_role_insp_or_system_and_group_admi(req_usr):
            # logger.debug('page: is_role_insp_or_system_and_group_admin')
            return _("You don't have permission to modify exam years.")
        elif req_usr.country_locked:
            # logger.debug('page: country_locked')
            return _("This country is locked. You cannot modify exam years.")
        else:
            # logger.debug('page: return None')
            return None  # Not disabled: admin of role_system and role_insp can modify examyears, if country not locked
# =====================================================================
# ===== no permissions if no examyear selected
# =====================================================================
    if not req_usr.examyear:
        return _("You must first select an examyear, before you can view this page.")

# =====================================================================
# ===== the rest of the pages cannot be viewed without examyear selected
# =====================================================================

    # - departments / levels / sectors:  can only be viewed by role_system and role_insp
    if page_name == 'default_items_view':
        if not req_usr.is_role_insp_or_admin_or_system:
            # logger.debug('page: is_role_insp_or_system_and_group_admin')
            return _("You don't have permission to view these items.")
        else:
            # logger.debug('page: return False')
            return None  # Not disabled:  role_system and role_insp can view examyear_list

    # - departments / levels / sectors: can only be modified by role_system and role_insp, only admin
    # TODO exclude read, authorize and None permissions
    if page_name == 'default_items_modify':
        if not acc_prm.is_role_insp_or_system_and_group_admi(req_usr):
            return _("You don't have permission to modify these items.")
        elif req_usr.country_locked:
            return _("This country is locked. You cannot modify these items.")
        else:
            return None  # TODO: change: Not disabled: admin of role_system and role_insp can modify default schools, if country not locked

    # - scheme, PR2018-08-23   >>>>>>>>>/ subject / package:
    if page_name == 'scheme_etc_view':
        return None  # Not disabled:  anyone can view schemes

    # - scheme, PR2018-08-23   >>>>>>>>>schooldefault / subjectdefault / departments / levels / sectors: can only be modified by role_system and role_insp, only admin
    if page_name == 'scheme_etc_edit':
        # TODO exclude read, authorize and None permissions
        if not acc_prm.is_role_insp_or_system_and_group_admi(req_usr):
            return _("You don't have permission to modify these items.")
        elif req_usr.country_locked:
            return _("This country is locked. You cannot modify these items.")
        elif req_usr.examyear_locked:
            return _("This examyear is locked. You cannot modify these items.")
        else:
            return None  # Not disabled: admin of role_system and role_insp can modify schemes, if country not locked


    # - school PR2018-09-15
    if page_name == 'school_view':
        # filter that role-school users can only view their own school is part of view
        return None  # Not disabled:  anyone can view school


# =====================================================================
# ===== no permissions if no schoolbase selected
# =====================================================================
    if not req_usr.schoolbase:
        return _("You are not connected to a school. You cannot view this page.")

# =====================================================================
# ==== the rest of the pages cannot be viewed without schooldefault selected
# =====================================================================

    if page_name == 'school_edit' or page_name == 'school_add_delete':
        if req_usr.country_locked:
            return _("This country is locked. You cannot modify schools.")
        elif req_usr.examyear_locked:
            return _("This examyear is locked. You cannot modify schools.")
        elif not req_usr.is_usergroup_admin:
            # only admin users can modify school
            # filter that role-school users can only modify their own school is part of form-get
            return _("You don't have permission to modify schools.")
        elif page_name == 'school_add_delete':
            if not req_usr.is_role_insp_or_admin_or_system:
                return _("You don't have permission to add or delete schools.")
            else:
                return None
        else:
            return None  # Not disabled: admin of role_system and role_insp can modify schemes, if country not locked

    # - students
    if page_name == 'students_view':
        return None  # Not disabled:  anyone can view students

    # - scheme, also for school PR2018-08-23   >>>>>>>>>schooldefault / subjectdefault / departments / levels / sectors: can only be modified by role_system and role_insp, only admin
    if page_name == 'students_modify':
        # TODO activate rule that only schools can enter students
        #  if not req_usr.is_role_school:
        #    return _("You don't have permission to modify these items.")
        if req_usr.country_locked:
            return _("This country is locked. You cannot modify these items.")
        elif req_usr.examyear_locked:
            return _("This examyear is locked. You cannot modify these items.")
        elif req_usr.school_locked:
            return _("This school is locked. You cannot modify these items.")
        # TODO  student_locked:, exclude read, authorise, None permissions
        #     return _("This student is locked. You cannot modify thise item.")
        else:
            return None  # Not disabled: admin of role_system and role_insp can modify schemes, if country not locked

# =====================================================================
# ===== the rest of the pages cannot be viewed without schooldefault selected
# =====================================================================

    return _("Error. You cannot view this page.")