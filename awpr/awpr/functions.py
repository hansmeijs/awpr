# PR2018-05-28
from django.contrib import messages
from django.utils.translation import activate, ugettext_lazy as _
from django.utils import timezone
from datetime import date, datetime

from awpr import constants as c
from schools import models as sch_mod
from accounts import models as acc_mod


import re
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
            logger.debug('ERROR: get_dateISO_from_string: ' + str(date_string) + ' new_dat_str: ' + str(new_dat_str))
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


# PR2018-07-23
def get_country_choices_all():
    # PR2018-07-20 function creates list of countries, used in SubjectdefaultAddForm and SubjectdefaultEditForm
    # countries_choices: [(1, 'cur'), (2, 'sxm')]
    # choises must be tuple or list, dictionary gives error: 'int' object is not iterable
    choices = []
    countries = sch_mod.Country.objects.all()
    for country in countries:
        if country:
            item = (country.id, country.name)
            choices.append(item)
    return choices


def get_sel_examyear_instance(request, request_item_setting=None):  # PR2020-12-25
    #logger.debug('  -----  get_sel_examyear_instance  -----')
    sel_examyear_instance = None
    sel_examyear_save = False
    multiple_examyears = False
    if request.user and request.user.country:
        requsr_country = request.user.country

# - check if there is a new examyear_pk in request_item_setting, check if request_examyear exists
        if request_item_setting is not None:
            r_eyr_pk = get_dict_value(request_item_setting, (c.KEY_SELECTED_PK, c.KEY_SEL_EXAMYEAR_PK))
            sel_examyear_instance = sch_mod.Examyear.objects.get_or_none(pk=r_eyr_pk, country=requsr_country)
            if sel_examyear_instance is not None:
                sel_examyear_save = True

        if sel_examyear_instance is None:
# - get saved_examyear_pk from Usersetting, check if saved_examyear exists
            selected_dict = acc_mod.Usersetting.get_jsonsetting(c.KEY_SELECTED_PK, request.user)
            s_ey_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK)
            sel_examyear_instance = sch_mod.Examyear.objects.get_or_none(pk=s_ey_pk, country=requsr_country)

# - if there is no saved nor request examyear: get latest examyear_pk of table
        if sel_examyear_instance is None:
            sel_examyear_instance = sch_mod.Examyear.objects.filter(country=requsr_country).order_by('-code').first()
            if sel_examyear_instance is not None:
                sel_examyear_save = True

# - check if there are multiple examyears, used to enable select examyear
        multiple_examyears = (sch_mod.Examyear.objects.filter(country=requsr_country).count() > 1)

    return sel_examyear_instance, sel_examyear_save, multiple_examyears
# --- end of get_sel_examyear_instance


def get_sel_schoolbase_instance(request, request_item_setting=None):  # PR2020-12-25
    #logger.debug('  -----  get_sel_schoolbase_instance  -----')
    #logger.debug('request_item_setting: ' + str(request_item_setting))

# ===== SCHOOLBASE ======================= PR2020-12-18
    # - get schoolbase from settings / request when role is insp, admin or system, from req_user otherwise
    # req_user.schoolbase cannot be changed
    # Selected schoolbase is stored in {selected_pk: {sel_schoolbase_pk: val}}

    sel_schoolbase_instance = None
    sel_schoolbase_save = False
    if request.user and request.user.country:
        req_user = request.user
        requsr_country = req_user.country
        may_select_schoolbase = req_user.is_role_insp or req_user.is_role_admin or req_user.is_role_system

        if may_select_schoolbase:

    # - check if there is a new schoolbase_pk in request_item_setting, check if request_schoolbase exists
            if request_item_setting is not None:
                r_sb_pk = get_dict_value(request_item_setting, (c.KEY_SELECTED_PK, c.KEY_SEL_SCHOOLBASE_PK))
                sel_schoolbase_instance = sch_mod.Schoolbase.objects.get_or_none(pk=r_sb_pk, country=requsr_country)
                if sel_schoolbase_instance is not None:
                    sel_schoolbase_save = True

            if sel_schoolbase_instance is None:
    # - get saved_schoolbase_pk from Usersetting, check if saved_schoolbase exists
                selected_dict = acc_mod.Usersetting.get_jsonsetting(c.KEY_SELECTED_PK, req_user)
                s_sb_pk = selected_dict.get(c.KEY_SEL_SCHOOLBASE_PK)
                sel_schoolbase_instance = sch_mod.Schoolbase.objects.get_or_none(pk=s_sb_pk, country=requsr_country)
    # - if there is no saved nor request examyear: get schoolbase of this user
            if sel_schoolbase_instance is None:
                sel_schoolbase_instance = req_user.schoolbase
                if sel_schoolbase_instance is not None:
                    sel_schoolbase_save = True
        else:
            sel_schoolbase_instance = req_user.schoolbase

    return sel_schoolbase_instance, sel_schoolbase_save
# --- end of get_sel_schoolbase_instance


def get_sel_depbase_instance(sel_school, request, request_item_setting=None):  # PR2020-12-26
    logger.debug('  -----  get_sel_depbase_instance  -----')
    logger.debug('sel_school: ' + str(sel_school))
    sel_depbase_instance = None
    sel_depbase_save = False
    allowed_depbases = []

    if request.user and request.user.country:
        req_user = request.user
        requsr_country = req_user.country

    # - get allowed depbases from school and user
        may_select_department = False
        if sel_school and sel_school.depbases:
            for depbase_pk in sel_school.depbases:
                # skip if depbase not in list of req_user.allowed_depbases
                # if req_user.allowed_depbases is empty, all depbases of the
                # school are allowed
                skip = req_user.allowed_depbases and depbase_pk not in req_user.allowed_depbases
                if not skip:
                    allowed_depbases.append(depbase_pk)
        logger.debug('allowed_depbases: ' + str(allowed_depbases))

    # - check if there is a new depbase_pk in request_item_setting,
        if request_item_setting is not None:
            r_depbase_pk = get_dict_value(request_item_setting, (c.KEY_SELECTED_PK, c.KEY_SEL_DEPBASE_PK))
            logger.debug('request_item_setting instance: ' + str(request_item_setting))
            logger.debug('r_depbase_pk instance: ' + str(r_depbase_pk))
            # check if it is in allowed_depbases,
            if r_depbase_pk in allowed_depbases:
                # check if request_depbase exists
                sel_depbase_instance = sch_mod.Departmentbase.objects.get_or_none(pk=r_depbase_pk, country=requsr_country)
                if sel_depbase_instance is not None:
                    sel_depbase_save = True

        logger.debug('request_depbase instance: ' + str(sel_depbase_instance))
        logger.debug('sel_depbase_save: ' + str(sel_depbase_save))

        if sel_depbase_instance is None:
    # - get depbase_pk from Usersetting, check if request_depbase exists
            selected_dict = acc_mod.Usersetting.get_jsonsetting(c.KEY_SELECTED_PK, req_user)
            s_depbase_pk = selected_dict.get(c.KEY_SEL_DEPBASE_PK)
        # check if it is in allowed_depbases,
            if s_depbase_pk in allowed_depbases:
        # check if saved_depbase exists
                sel_depbase_instance = sch_mod.Departmentbase.objects.get_or_none(pk=s_depbase_pk, country=requsr_country)
        logger.debug('saved_depbase instance: ' + str(sel_depbase_instance))

    # - if there is no saved nor request examyear: get first allowed depbase_pk
        if sel_depbase_instance is None:
            if allowed_depbases and len(allowed_depbases):
                a_depbase_pk = allowed_depbases[0]
                sel_depbase_instance = sch_mod.Departmentbase.objects.get_or_none(pk=a_depbase_pk, country=requsr_country)
                if sel_depbase_instance is not None:
                    sel_depbase_save = True

        logger.debug('sel_depbase_instance instance: ' + str(sel_depbase_instance))
    return sel_depbase_instance, sel_depbase_save, allowed_depbases
# --- end of get_sel_depbase_instance


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
    selected_dict = acc_mod.Usersetting.get_jsonsetting(c.KEY_SELECTED_PK, request.user)

# - get saved_depbase_pk, check if saved_depbase exists
    if selected_dict:
        s_db_pk = selected_dict.get(c.KEY_SEL_DEPBASE_PK)
# - get selected examyear
        if s_db_pk:
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



def system_updates():
    # these are once-only updates in tables. Data will be changed / moved after changing fields in tables
    # after uploading the new version the function can be removed

    # update_isabsence_istemplate()
    # update_workminutesperday()  # PR20202-06-21
    # update_company_workminutesperday() # PR20202-06-29
    # update_paydateitems PR2020-06-26
    # update_shiftcode_in_orderhours() PR2020-07-25
    # update_customercode_ordercode_in_orderhours() PR2020-07-25
    # update_employeecode_in_orderhours() PR2020-07-25
    # update_sysadmin_in_user()  # PR2020-07-30
    pass
