# PR2018-05-28
from django.contrib import messages
from django.db import connection
from django.utils.translation import activate, ugettext_lazy as _
from django.utils import timezone
from datetime import date, datetime, time

from awpr import constants as c
from awpr import settings as s

from accounts import views as acc_view
from schools import models as sch_mod
from subjects import models as subj_mod
import pytz
import logging
logger = logging.getLogger(__name__)


# PR2019-01-04 from https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy
from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder

class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)


############################################################
# also for permits
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


def get_date_from_arr(arr_int):  # PR2019-11-17  # PR2020-10-20
    date_obj = None
    if arr_int:
        date_obj = date(arr_int[0], arr_int[1], arr_int[2])
    return date_obj


# ################### DATE STRING  FUNCTIONS ###################

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
        except:
            logger.error('ERROR: get_dateISO_from_string: ' + str(date_string) + ' new_dat_str: ' + str(new_dat_str))
    return new_dat_str


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


def format_WDMY_from_dte(dte, user_lang):  # PR2020-10-20
    # returns 'zo 16 juni 2019'
    date_WDMY = ''
    if dte:
        try:
            date_DMY = format_DMY_from_dte(dte, user_lang)
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


def format_DMY_from_dte(dte, lang):  # PR2019-06-09  # PR2020-10-20
    #logger.debug('... format_DMY_from_dte: ' + str(dte) + ' type:: ' + str(type(dte)) + ' lang: ' + str(lang))
    # returns '16 juni 2019'
    date_DMY = ''
    if dte:
        try:
            year_str = str(dte.year)
            day_str = str(dte.day)
            month_lang = ''

            if lang in c.MONTHS_ABBREV:
                month_lang = c.MONTHS_ABBREV[lang]
            month_str = month_lang[dte.month]

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


def get_modifiedby_formatted(instance, user_lang):
    # Function returns 'Laatst gewijzigd door Hans Meijs op 6 mei 2021, 15.55 u'  PR2021-05-09
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
            last_modified_date =  datetime_local.date()
            date_formatted = format_DMY_from_dte(last_modified_date, user_lang)

            time_formatted = format_HM_from_dt_local(datetime_local, True, True, '24h', user_lang)
            datetime_formatted = date_formatted + ', ' + time_formatted

        last_modified_text = ' '.join(( str(_('Last modified by')), user_name, str(_('at')), datetime_formatted))

    return last_modified_text

# ----------  end of Date functions ---------------


def get_dict_value(dictionry, key_tuple, default_value=None):
    # PR2020-02-04 like in base.js Iterate through key_tuple till value found
    #logger.debug('  -----  get_dict_value  -----')
    #logger.debug('     dictionry: ' + str(dictionry))
    if key_tuple and dictionry:  # don't use 'dictionary' - is PyCharm reserved word
        for key in key_tuple:
            #logger.debug('     key: ' + str(key) + ' key_tuple: ' + str(key_tuple))
            if isinstance(dictionry, dict) and key in dictionry:
                dictionry = dictionry[key]
                #logger.debug('     new dictionry: ' + str(dictionry))
            else:
                dictionry = None
                break
    if dictionry is None and default_value is not None:
        dictionry = default_value
    #logger.debug('     return dictionry: ' + str(dictionry))
    return dictionry


def get_mode_str(self):  # PR2018-11-28
    mode_str = '-'
    if self.mode is not None:
        mode_str = c.MODE_DICT.get(str(self.mode))
    return mode_str

def get_selected_examyear_from_usersetting(request):  # PR2021-05-31
    #logger.debug(' ----- get_selected_examyear_from_usersetting ----- ' )
    # this function gets sel_examyear_instance from saved settings.
    # used in students.create_studentsubjectnote_rows
    selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
    s_ey_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK)
    sel_examyear_instance = sch_mod.Examyear.objects.get_or_none(
        pk=s_ey_pk,
        country=request.user.country
    )
    return sel_examyear_instance
# - end of get_selected_examyear_from_usersetting


def get_sel_examyear_instance(request, request_setting=None):  # PR2020-12-25
    #logger.debug('  -----  get_sel_examyear_instance  -----')
    sel_examyear_instance = None
    sel_examyear_save = False
    multiple_examyears = False

    if request.user and request.user.country:
        req_user= request.user
        requsr_country = request.user.country

# - check if there is a new examyear_pk in request_setting, check if request_examyear exists
        if request_setting is not None:
            selected_pk_dict = request_setting.get(c.KEY_SELECTED_PK)
            #logger.debug('selected_pk_dict: ' + str(selected_pk_dict))
            if selected_pk_dict:
                r_eyr_pk = selected_pk_dict.get(c.KEY_SEL_EXAMYEAR_PK)
                sel_examyear_instance = sch_mod.Examyear.objects.get_or_none(pk=r_eyr_pk, country=requsr_country)
                if sel_examyear_instance is not None:
                    sel_examyear_save = True

        if sel_examyear_instance is None:
# - get saved_examyear_pk from Usersetting, check if saved_examyear exists
            selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
            s_ey_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK)
            sel_examyear_instance = sch_mod.Examyear.objects.get_or_none(pk=s_ey_pk, country=requsr_country)

# - if there is no saved nor request examyear: get latest examyear_pk of table
        if sel_examyear_instance is None:
            sel_examyear_instance = sch_mod.Examyear.objects.filter(country=requsr_country).order_by('-code').first()
            if sel_examyear_instance is not None:
                sel_examyear_save = True

# - check if there are multiple examyears, used to enable select examyear
        multiple_examyears = (sch_mod.Examyear.objects.filter(country=requsr_country).count() > 1)

# - also add sel_examperiod and sel_examtype, used in page grades

    return sel_examyear_instance, sel_examyear_save, multiple_examyears
# --- end of get_sel_examyear_instance


def get_sel_schoolbase_instance(request, request_setting=None):  # PR2020-12-25 PR2021-04-23
    #logger.debug('  -----  get_sel_schoolbase_instance  -----')

    # request_setting: {'page': 'page_user', 'sel_schoolbase_pk': 13}

    # - get schoolbase from settings / request when role is comm, insp, admin or system, from req_user otherwise
    # req_user.schoolbase cannot be changed
    # Selected schoolbase is stored in {selected_pk: {sel_schoolbase_pk: val}}

    sel_schoolbase_instance = None
    save_sel_schoolbase = False
    if request.user and request.user.country:
        req_user = request.user
        requsr_country = req_user.country

        #<PERMIT>
        # get req_user.schoolbase if not allowed to select other schools
        may_select_schoolbase = req_user.is_role_comm or req_user.is_role_insp or req_user.is_role_admin or req_user.is_role_system

        if not may_select_schoolbase:
            sel_schoolbase_instance = req_user.schoolbase
        else:

    # - check if there is a new schoolbase_pk in request_setting, check if request_schoolbase exists
            if request_setting is not None:
                r_sb_pk = request_setting.get(c.KEY_SEL_SCHOOLBASE_PK)
                if r_sb_pk:
                    sel_schoolbase_instance = sch_mod.Schoolbase.objects.get_or_none(pk=r_sb_pk, country=requsr_country)
                    if sel_schoolbase_instance is not None:
                        save_sel_schoolbase = True

    # - if not: get saved_schoolbase_pk from Usersetting, check if saved_schoolbase exists
            if sel_schoolbase_instance is None:
                selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                s_sb_pk = selected_dict.get(c.KEY_SEL_SCHOOLBASE_PK)
                sel_schoolbase_instance = sch_mod.Schoolbase.objects.get_or_none(pk=s_sb_pk, country=requsr_country)

    # - if there is no saved nor request schoolbase: get schoolbase of this user
            if sel_schoolbase_instance is None:
                sel_schoolbase_instance = req_user.schoolbase
                if sel_schoolbase_instance is not None:
                    save_sel_schoolbase = True

    return sel_schoolbase_instance, save_sel_schoolbase
# --- end of get_sel_schoolbase_instance


def get_sel_depbase_instance(sel_school, request, request_setting=None):  # PR2020-12-26 PR2021-05-07
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  -----  get_sel_depbase_instance  -----')
        logger.debug('sel_school: ' + str(sel_school))
        logger.debug('request_setting: ' + str(request_setting))

    sel_depbase_instance = None
    save_sel_depbase = False
    allowed_depbases = []
    # PR2021-07-11 depbase has not a field 'country' any more
    if request.user and request.user.country:
        req_user = request.user
        requsr_country = req_user.country

# - get allowed depbases from user
        # if req_user.allowed_depbases is empty, all depbases of the school are allowed
        if sel_school and sel_school.depbases:
            allowed_depbases_arr = req_user.allowed_depbases.split(';') if req_user.allowed_depbases else []
            # PR2021-05-04 warning. if depbases contains ';2;3;',
            # it will give error:  invalid literal for int() with base 10: ''
            allowed_depbases_list = list(map(int, allowed_depbases_arr))

# - get allowed depbases from school
            school_depbase_list = list(map(int, sel_school.depbases.split(';')))
            for depbase_pk in school_depbase_list:
                # skip if depbase not in list of req_user.allowed_depbases
                # if req_user.allowed_depbases is empty, all depbases of the school are allowed
                skip = allowed_depbases_list and depbase_pk not in allowed_depbases_list
                if not skip:
                    allowed_depbases.append(depbase_pk)

# - check if there is a new depbase_pk in request_setting,
        if request_setting is not None:
            r_depbase_pk = get_dict_value(request_setting, (c.KEY_SELECTED_PK, c.KEY_SEL_DEPBASE_PK))
    # check if it is in allowed_depbases,
            if r_depbase_pk in allowed_depbases:
    # check if request_depbase exists
                sel_depbase_instance = sch_mod.Departmentbase.objects.get_or_none(pk=r_depbase_pk)
                if sel_depbase_instance is not None:
                    save_sel_depbase = True
        if logging_on:
            logger.debug('request_depbase instance: ' + str(sel_depbase_instance))
            logger.debug('save_sel_depbase: ' + str(save_sel_depbase))

# - get depbase_pk from Usersetting when there is no request_depbase_pk; check if request_depbase exists
        if sel_depbase_instance is None:
            selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
            s_depbase_pk = selected_dict.get(c.KEY_SEL_DEPBASE_PK)
    # check if saved_depbase is in allowed_depbases,
            if s_depbase_pk in allowed_depbases:
    # check if saved_depbase exists
                sel_depbase_instance = sch_mod.Departmentbase.objects.get_or_none(pk=s_depbase_pk)
        if logging_on:
            logger.debug('saved_depbase instance: ' + str(sel_depbase_instance))

# - if there is no saved nor request depbase: get first allowed depbase_pk
        if sel_depbase_instance is None:
            if allowed_depbases and len(allowed_depbases):
                a_depbase_pk = allowed_depbases[0]
                sel_depbase_instance = sch_mod.Departmentbase.objects.get_or_none(pk=a_depbase_pk)
                if sel_depbase_instance is not None:
                    save_sel_depbase = True
    if logging_on:
        logger.debug('sel_depbase_instance: ' + str(sel_depbase_instance))
        logger.debug('save_sel_depbase: ' + str(save_sel_depbase))
        logger.debug('allowed_depbases: ' + str(allowed_depbases))

    return sel_depbase_instance, save_sel_depbase, allowed_depbases
# --- end of get_sel_depbase_instance


def is_allowed_depbase_requsr(depbase_pk, request):  # PR2021-06-14
    # function checks if depbase_pk is in req_user.allowed_depbases
    is_allowed_depbase = False
    if request.user:
        allowed_depbases = request.user.allowed_depbases

    # - get allowed depbases from user
        # if req_user.allowed_depbases is empty, all depbases of the school are allowed
        if allowed_depbases is None:
            is_allowed_depbase = True
        else:
            # add ';' in front and after allowed_depbases and depbase_pk
            depbases_str = ''.join([';', allowed_depbases, ';'])
            depbase_pk_str = ''.join([';', str(depbase_pk), ';'])
            if depbase_pk_str in depbases_str:
                is_allowed_depbase = True

    return is_allowed_depbase


def is_allowed_depbase_school(depbase_pk, school):  # PR2021-06-14
    # function checks if depbase_pk is in req_user.allowed_depbases
    is_allowed_depbase = False
    if school:
        school_depbases = school.depbases

        # - get allowed depbases from user
        # if req_user.allowed_depbases is empty, all depbases of the school are allowed
        if school_depbases is None:
            is_allowed_depbase = True
        else:
            # add ';' in front and after allowed_depbases and depbase_pk
            depbases_str = ''.join([';', school_depbases, ';'])
            depbase_pk_str = ''.join([';', str(depbase_pk), ';'])
            if depbase_pk_str in depbases_str:
                is_allowed_depbase = True

    return is_allowed_depbase


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
def get_this_examyear_int():
    # get this year in Jan thru July, get next year in Aug thru Dec PR2020-09-29 PR2020-12-24
    now = timezone.now()
    this_examyear_int = now.year
    if now.month + 1 > c.MONTH_START_EXAMYEAR:
        this_examyear_int = now.year + 1
    return this_examyear_int


def get_todays_examyear_instance(country):  # PR2020-12-24
    # get this year in Jan thru July, get next year in Aug thru Dec PR2020-09-29 PR2020-12-24
    todays_examyear_int = get_this_examyear_int()
    todays_examyear_instance = sch_mod.Examyear.objects.get_or_none(country=country, code=todays_examyear_int)
    return todays_examyear_instance


def get_todays_examyear_or_latest_instance(country):
    # get this year in Jan thru July, get next year in Aug thru Dec PR2020-09-29 PR2020-12-24
    examyear_instance = get_todays_examyear_instance(country)
# - get latest examyear if todays_examyear does not exist
    if examyear_instance is None:
        examyear_instance = sch_mod.Examyear.objects.filter(country=country).order_by('-code').first()
    return examyear_instance


def get_saved_sel_depbase_instance(request):  # PR2020-12-24
    #logger.debug('  -----  get_saved_sel_depbase_instance  -----')
    sel_depbase_instance = None
# - get saved selected_pk's from Usersetting, key: selected_pk
    req_user = request.user
    if req_user:
        selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
# - get saved_depbase_pk, check if saved_depbase exists
        if selected_dict:
            s_db_pk = selected_dict.get(c.KEY_SEL_DEPBASE_PK)
    # - get selected examyear
            if s_db_pk:
                #TODO XXXXXXXXXXXXXXXXXXXXXXXXXXX wrong : country=request.user.country
                sel_depbase_instance = sch_mod.Department.objects.get_or_none(pk=s_db_pk, country=request.user.country)
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


def system_updates(examyear, request):
    # these are once-only updates in tables. Data will be changed / moved after changing fields in tables
    # after uploading the new version the function can be removed
    pass

    #update_examyearsetting(examyear, request)
    # PR2021-03-26

    #transfer_depbases_from_array_to_string()
# - end of system_updates

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


def update_examyearsetting(examyear, request):
    # Once-only function to add sysadmin permit to admin users PR2020-07-30
    # logger.debug('........update_sysadmin_in_user..........')

    key_value_list = [
        ('exform', 'minond', 'MINISTERIE VAN ONDERWIJS, WETENSCHAP, CULTUUR EN SPORT'),

        ('exform', 'eex', 'EINDEXAMEN'),
        ('exform', 'lex', 'LANDSEXAMEN'),
        ('exform', 'ey', 'examenjaar'),
        ('exform', 'se', 'schoolexamen'),
        ('exform', 'ses', 'schoolexamens'),
        ('exform', 'cie', 'commissie-examen (CIE)'),
        ('exform', 'cies', 'commissie-examens (CIE)'),
        ('exform', 'ce', 'centraal examen'),
        ('exform', 'cece', 'centraal examen (CE)'),
        ('exform', 'de_ces', 'de centrale examens'),
        ('exform', 'de_cesce', 'de centrale examens (CE)'),
        ('exform', 'eex_lb_rgl01', 'Landsbesluit eindexamens V.W.O., H.A.V.O., V.S.B.O. van de 23ste juni 2008,'),
        ('exform', 'eex_lb_rgl02', 'ter uitvoering van artikel 32, vijfde lid, van de Landsverordening voortgezet onderwijs, no. 54.'),
        ('exform', 'lex_lb_rgl01', 'Landsbesluit landsexamens v.w.o., h.a.v.o., v.s.b.o. van 3 mei 2016,'),
        ('exform', 'lex_lb_rgl02', 'ter uitvoering van artikel 57 van de Landsverordening voorgezet onderwijs, no. 21.'),

        ('exform', 'in_examyear', 'in het examenjaar'),
        ('exform', 'school', 'School:'),
        ('exform', 'col_name01', 'Naam en voorletters van de kandidaat'),
        ('exform', 'col_name02', '(in alfabetische volgorde)'),
        ('exform', 'col_class', 'Klas'),
        ('exform', 'col_exnr', 'Ex.nr.'),
        ('exform', 'col_idnr', 'ID-nummer'),
        ('exform', 'bullet', '*'),
        ('exform', 'signature_president', '(Handtekening voorzitter)'),
        ('exform', 'signature_secretary', '(Handtekening secretaris)'),

        ('ex1', 'title', 'Genummerde alfabetische naamlijst van de kandidaten'),
        ('ex1', 'submit_before', 'Inzenden vóór 1 november *'),
        ('ex1', 'footnote01', 'Dit formulier dient tevens voor bestelling schriftelijk werk.'),
        ('ex1', 'footnote02', 'Ex.nr.: onder dit nummer doet de kandidaat examen.'),
        ('ex1', 'footnote03', 'Vakken waarin geëxamineerd moet worden aangeven met x.'),
        ('ex1', 'footnote04', None),
        ('ex1', 'footnote05', None),
        ('ex1', 'footnote06', '*  Het getekend exemplaar en een digitale versie'),
        ('ex1', 'footnote07', '   vóór 1 november inzenden naar de Onderwijs Inspectie'),
        ('ex1', 'footnote08', '   en een digitale versie naar het ETE.'),
        ('ex1', 'lex_footnote07', '   vóór 1 november inzenden naar de Onderwijs Inspectie.'),
        ('ex1', 'lex_footnote08', None),

        ('ex2', 'title', 'Verzamellijst van cijfers van schoolexamens'),
        ('ex2', 'submit', 'Inzenden ten minste 3 dagen vóór aanvang van de centrale examens*'),
        ('ex2', 'eex_backpage', 'Handtekening van de examinatoren voor akkoord cijfers schoolonderzoek als aan ommezijde vermeld.'),
        ('ex2', 'lex_backpage', 'Handtekening van de examinatoren voor akkoord cijfers commissie-examen (CIE) als aan ommezijde vermeld.'),
        ('ex2', 'footnote01', 'Ex. nr. en naam dienen in overeenstemming '),
        ('ex2', 'footnote02', 'te zijn met formulier EX.1'),
        ('ex2', 'footnote03', '1) doorhalen hetgeen niet van toepassing is.'),
        ('ex2', 'footnote04', 'het getekend exemplaar en een digitale versie ten minste 3 dagen vóór aanvang van de centrale examens'),
        ('ex2', 'footnote05', 'inzenden naar de Onderwijs Inspectie en een digitale versie naar het ETE.'),
        ('ex2', 'backpage01', 'Handtekening van de examinatoren voor akkoord cijfers schoolonderzoek als aan ommezijde vermeld.'),
        ('ex2', 'backpage02', 'Klas'),
        ('ex2', 'backpage03', 'Vak'),
        ('ex2', 'backpage04', 'Naam Examinator'),
        ('ex2', 'backpage05', 'Handtekening'),

        ('ex2a', 'title', 'Lijst van cijfers'),
        ('ex2a', 'eex_article', '(Artikel 20 Landsbesluit eindexamens v.w.o., h.a.v.o., v.s.b.o., 23 juni 2008, no 54)'),
        ('ex2a', 'lex_article', '(Artikel 34 Landsbesluit landsexamens v.w.o., h.a.v.o., v.s.b.o. van 3 mei 2016, no 21)'),
        ('ex3', 'title', 'Proces-Verbaal van Toezicht'),
        ('ex3', 'eex_article', '(Artikel 28, Landsbesluit eindexamens v.w.o., h.a.v.o., v.s.b.o., 23 juni 2008, no 54)'),
        ('ex3', 'lex_article', '((Artikel 18, Landsbesluit landsexamens v.w.o., h.a.v.o., v.s.b.o. van 3 mei 2016, no 21)'),
        ('ex4', 'title', 'Lijst van kandidaten voor het herexamen.'),
        ('ex4', 'title_corona', 'Lijst van kandidaten voor herkansing.'),
        ('ex4', 'eex_article', '(Landsbesluit eindexamens v.w.o., h.a.v.o., v.s.b.o., 23 juni 2008, no 54)'),
        ('ex4', 'lex_article', '(Landsbesluit landsexamens v.w.o., h.a.v.o., v.s.b.o. van 3 mei 2016, no 21)'),
        ('ex4', 'header03', 'Tevens lijst van kandidaten, die om een geldige reden verhinderd waren het examen te voltooien.'),
        ('ex4', 'eex_header04', 'Direct na elke uitslag inzenden naar de Onderwijs Inspectie en digitaal naar het ETE.'),
        ('ex4', 'lex_header04', 'Direct na elke uitslag het ondertekend exemplaar en digitaal inzenden naar de Onderwijs Inspectie.'),
        ('ex4', 'footer01', 'Dit formulier dient tevens voor bestelling schriftelijk werk.'),
        ('ex4', 'footer02', 'Ex. nr. en naam dienen in overeenstemming te zijn met formulier EX.1.'),
        ('ex4', 'verhinderd_header01', 'Kandidaten die om een geldige reden verhinderd waren het examen te voltooien.'),
        ('ex4', 'verhinderd_header02', '(Voortzetting schoolexamen aangeven met s en centraal examen met c).'),
        ('ex5', 'eex_inzenden', 'Inzenden binnen één week na de uitslag en na afloop van de herkansing, het ondertekend exemplaar inzenden naar de Onderwijs Inspectie en digitaal naar de Onderwijs Inspectie en het ETE.'),
        ('ex5', 'lex_inzenden', 'Inzenden binnen één week na de uitslag en na afloop van de herkansing, het ondertekend exemplaar en digitaal inzenden naar de Onderwijs Inspectie.'),
        ('ex6', 'eex_article', '(Artikel 47 Landsbesluit eindexamens v.w.o., h.a.v.o., v.s.b.o., 23 juni 2008, no 54)'),
        ('ex6', 'lex_article', '(Artikel 10 Landsbesluit landsexamens v.w.o., h.a.v.o., v.s.b.o. van 3 mei 2016, no 21)'),

        ('gradelist', 'preliminary', 'VOORLOPIGE CIJFERLIJST'),

        ('gradelist', 'undersigned', 'De ondergetekenden verklaren dat'),
        ('gradelist', 'born_on', 'geboren op'),
        ('gradelist', 'born_at', 'te'),
        ('gradelist', 'examyear', 'in het examenjaar'),
        ('gradelist', 'attended', 'heeft deelgenomen aan het eindexamen'),
        ('gradelist', 'conform', 'conform'),
        ('gradelist', 'profiel', 'het profiel'),
        ('gradelist', 'leerweg', 'de leerweg'),
        ('gradelist', 'at_school', 'aan'),
        ('gradelist', 'at_country', 'te'),
# & " heeft deelgenomen aan het eindexamen " & [Afd]![Afk_Afdeling] & " conform"
        ('gradelist', 'eex_article01', 'welk examen werd afgenomen volgens de voorschriften gegeven bij en krachtens artikel 32 van de Landsverordening Voortgezet Onderwijs'),
        ('gradelist', 'eex_article02', 'De kandidaat heeft examen afgelegd in de onderstaande vakken en heeft de daarachter vermelde cijfers behaald.'),

        ('gradelist', 'subjects', 'Vakken waarin examen is afgelegd'),
        ('gradelist', 'grades_for', 'Cijfers voor'),
        ('gradelist', 'final_grades', 'Eindcijfers'),
        ('gradelist', 'col_header_se', 'School-\nexamen'),
        ('gradelist', 'col_header_ce', 'Centraal\nexamen'),
        ('gradelist', 'col_in_numbers', 'in cijfers'),
        ('gradelist', 'col_in_letters', 'in letters'),

        ('gradelist', 'combi_grade', 'Combinatiecijfer, het gemiddelde van de met * gemerkte vakken:'),

        ('gradelist', 'lbl_title_pws', 'Titel/onderwerp van het profielwerkstuk:'),
        ('gradelist', 'lbl_title_sws', 'Titel/onderwerp van het profielwerkstuk:'),
        ('gradelist', 'lbl_subjects__ws', 'Vakken waarop het profielwerkstuk betrekking heeft:'),

        ('gradelist', 'avg_grade', 'Gemiddelde der cijfers'),
        ('gradelist', 'result', 'Uitslag op grond van de resultaten:'),
        ('gradelist', 'place', 'Plaats:'),
        ('gradelist', 'date', 'Datum:'),
        ('gradelist', 'president', 'De voorzitter:'),
        ('gradelist', 'secretary', 'De secretaris:'),

        ('diploma', 'born', 'geboren'),
        ('diploma', 'born_at', 'at'),
        ('diploma', 'attended', 'met gunstig gevolg heeft deelgenomen aan het eindexamen'),
        ('diploma', 'conform_sector', 'conform de sector'),
        ('diploma', 'at_school', 'aan'),
        ('diploma', 'at_country', 'te'),
        ('diploma', 'article', 'welk examen werd afgenomen volgens de voorschriften gegeven bij en krachtens artikel 32 van de Landsverordening voortgezet onderwijs van de 21ste mei 2008, P.B. no. 33, (P.B. 1979, no 29), zoals gewijzigd.'),

        ('diploma', 'place', 'Plaats:'),
        ('diploma', 'date', 'Datum:'),
        ('diploma', 'president', 'De voorzitter van de examencommissie:'),
        ('diploma', 'secretary', 'De secretaris van de examencommissie:'),

        ('diploma', 'ete', 'Het Expertisecentrum voor Toetsen & Examens:'),

        ('diploma', 'signature', 'Handtekening van de geslaagde:'),
        ('diploma', 'reg_nr', 'Registratienr.:'),
        ('diploma', 'id_nr', 'Id.nr.:'),
    ]
    for key_value in key_value_list:
        instance = sch_mod.ExfilesText.objects.filter(
            examyear=examyear,
            key=key_value[0],
            subkey=key_value[1]).first()
        if instance is None:
            instance = sch_mod.ExfilesText(
                examyear=examyear,
                key=key_value[0],
                subkey=key_value[1],
                setting=key_value[2]
            )
        else:
            instance.setting = key_value[2]
        instance.save()

def get_exform_text(examyear, key_list):  # PR2021-03-10
    # get text for exform etc from ExfilesText
    return_dict = {}
    # key_list must be list, not tuple
    if examyear and key_list:
        sql_keys = {'ey_id': examyear.pk, 'key_arr': key_list}
        sql = "SELECT eft.subkey, eft.setting FROM schools_exfilestext AS eft " + \
                "WHERE eft.examyear_id = %(ey_id)s::INT AND eft.key IN ( SELECT UNNEST( %(key_arr)s::TEXT[])) ORDER BY eft.subkey"

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            for row in cursor.fetchall():
                return_dict[row[0]] = row[1]

    return return_dict
# --- end of get_exform_text


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

