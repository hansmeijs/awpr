# PR2018-05-28
from django.contrib import messages
from django.utils.translation import activate, ugettext_lazy as _

from datetime import date, datetime

from awpr import constants as c
from schools import models as sch_mod
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


def get_schooldefault_choices_all(request_user):
    # PR2018-08-01  this function is used in UserAddForm, in UserEditForm

    # RequestUser role = School:
        # RequestUser cannot change their own country and school
        # RequestUser Admin: at Add: can only add users with country=RequestUser.country and defaultschool=RequestUser.defaultschool
        #                    at Edit: country and school cannot be modified

    # RequestUser role = Inspection:
        # Inspection users can change their own school, not their own country
        # RequestUser Admin: at Add: can only add Inspection users, country is RequestUser's country, leave school blank
        # RequestUser Admin: at Edit Inspection users: country is locked, RequestUser cannot change school

    # RequestUser role = System:
        # System Users can edit their own country and school
        # RequestUser Admin: at Add: can add school users, set country and school of that country
        #                    at Add: can add Inspection users, set country, leave school blank
        #                    at Add: can add System users, leave country and school blank

        # RequestUser Admin: at Edit School users: country and school cannot be modified
        #                    at Edit Inspection users: country cannot be modified, RequestUser cannot change school
        #                    at Edit System users: RequestUser cannot change country or school

    # PR2018-07-28  Show only schools from selecteduser.country
    # self = request_user, not selected_user when called by UserEditForm
    """
    if is_AddMode:
        if request_user.is_role_school:
            # SelectedUser's country = RequestUser's country
            # SelectedUser's school = RequestUser's school
        elif request_user.is_role_insp:
            if selected_user.is_role_school:
                # SelectedUser's country = RequestUser's country
                # SelectedUser's school can be set by RequestUser, only schools of SelectedUser's country
            if selected_user.is_role_insp:
                # SelectedUser's country = RequestUser's country
                # SelectedUser's school = blank
        elif request_user.is_role_system:
            if selected_user.is_role_school:
                # SelectedUser's country can be set by RequestUser
                # SelectedUser's school can be set by RequestUser, only schools of SelectedUser's country
            if selected_user.is_role_insp:
                # SelectedUser's country can be set by RequestUser
                # SelectedUser's school = blank
            if selected_user.is_role_system:
                # SelectedUser's country = blank
                # SelectedUser's school = blank
    else: # is_EditMode
        if request_user == selected_user:
            # user changes his own country / school
            if selected_user.is_role_school:
                # SelectedUser's country cannot be changed
                # SelectedUser's school cannot be changed
            if selected_user.is_role_insp:
                # SelectedUser's country cannot be changed
                # SelectedUser's school can be set by SelectedUser, only schools of SelectedUser's country
            if selected_user.is_role_system:
                # SelectedUser's country can be set by SelectedUser
                # SelectedUser's school can be set by SelectedUser, only schools of SelectedUser's country
        else:
            # RequestUser changes SelectedUser's country / school
            if request_user.is_role_school:
                # SelectedUser's country cannot be changed
                # SelectedUser's school cannot be changed
            elif request_user.is_role_insp:
                if selected_user.is_role_school:
                    # SelectedUser's country cannot be changed
                    # SelectedUser's school cannot be changed
                if selected_user.is_role_insp:
                    # SelectedUser's country cannot be changed
                    # SelectedUser's school cannot be changed by RequestUser
            elif request_user.is_role_system:
                if selected_user.is_role_school:
                    # SelectedUser's country cannot be changed
                    # SelectedUser's school cannot be changed
                if selected_user.is_role_insp:
                    # SelectedUser's country cannot be changed
                    # SelectedUser's school cannot be changed by RequestUser
                if selected_user.is_role_system:
                    # SelectedUser's country cannot be changed by RequestUser
                    # SelectedUser's school cannot be changed by RequestUser
        """
    choices = [c.CHOICE_NONE] # CHOICE_NONE = (0, _('None'))

    request_user_countryid = 0
    if request_user:
        if request_user.country:
            request_user_countryid = request_user.country.id

    #if request_user.country:
    #logger.debug('class User(AbstractUser) self.selecteduser_countryid: ' + str(selecteduser_countryid))
    #schooldefaults = Schooldefault.objects.filter(country=request_user.country)
    #for item in schooldefaults:
    #    item_str = ''
    #    if item.code is not None:
    #        item_str = str(item.code) + ' - '
    #    if item.name is not None:
    #        item_str = item_str + str(item.name)
    #    choices.append((item.id, item_str))

    #logger.debug('class User(AbstractUser) schooldefault_choices: ' + str(choices))
    return choices


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


def get_tuple_from_list_str(list_str):  # PR2018-08-28
    # get_tuple_from_list_str converts list_str string into tuple,
    # e.g.: list_str='1;2' will be converted to list_tuple=(1,2)
    # empty list = (0,), e.g: 'None'
    depbase_list_str = str(list_str)
    list_tuple = tuple()
    if depbase_list_str:
        try:
            depbase_list_split = depbase_list_str.split(';')
            list_tuple = tuple(depbase_list_split)
        except:
            pass
    #logger.debug('get_tuple_from_list_str tuple list_tuple <' + str(list_tuple) + '> Type: " + str(list_tuple))
    return list_tuple


def id_found_in_list(id_str='', list_str='', value_at_empty_list=False):  # PR2018-11-22
    # Function searches for id in string,
    # e.g.: id '2' will serach ';2;' in ';1;2;3;'
    found = value_at_empty_list
    if list_str:
        found = False
        if id_str:
    # PR2018-11-23 debug: error 'must be str, not int', argument changes form str to int, don't now why. Usse str()
            id_delim = ';' + str(id_str) + ';'
            if id_delim in list_str:
                found = True
    return found


def slice_firstlast_delim(list_str):  # PR2018-11-22
    # slice off first and last delimiter from list_str
    # e.g.: ';1;2;3;' becomes '1;2;3'
    if list_str:
        if list_str[0] == ';':
            list_str = list_str[1:]
        if list_str:
            if list_str[-1] == ';':
                list_str = list_str[:-1]
    return list_str


def get_dict_value(dictionry, key_tuple, default_value=None):
    # PR2020-02-04 like in base.js Iterate through key_tuple till value found
    if key_tuple and dictionry:  # don't use 'dictionary' - is PyCharm reserved word
        for key in key_tuple:
            if isinstance(dictionry, dict) and key in dictionry:
                dictionry = dictionry[key]
            else:
                dictionry = None
                break
    if dictionry is None and default_value is not None:
        dictionry = default_value
    return dictionry


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
