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
        req_user= request.user
        requsr_country = request.user.country

# - check if there is a new examyear_pk in request_item_setting, check if request_examyear exists
        if request_item_setting is not None:
            selected_pk_dict = request_item_setting.get(c.KEY_SELECTED_PK)
            #logger.debug('selected_pk_dict: ' + str(selected_pk_dict))
            if selected_pk_dict:
                r_eyr_pk = selected_pk_dict.get(c.KEY_SEL_EXAMYEAR_PK)
                sel_examyear_instance = sch_mod.Examyear.objects.get_or_none(pk=r_eyr_pk, country=requsr_country)
                if sel_examyear_instance is not None:
                    sel_examyear_save = True

        if sel_examyear_instance is None:
# - get saved_examyear_pk from Usersetting, check if saved_examyear exists
            selected_dict = req_user.get_usersetting_dict(c.KEY_SELECTED_PK)
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
                selected_dict = req_user.get_usersetting_dict(c.KEY_SELECTED_PK)
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
    #logger.debug('  -----  get_sel_depbase_instance  -----')
    #logger.debug('sel_school: ' + str(sel_school))
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
        #logger.debug('allowed_depbases: ' + str(allowed_depbases))

# - check if there is a new depbase_pk in request_item_setting,
        if request_item_setting is not None:
            r_depbase_pk = get_dict_value(request_item_setting, (c.KEY_SELECTED_PK, c.KEY_SEL_DEPBASE_PK))
            #logger.debug('request_item_setting instance: ' + str(request_item_setting))
            #logger.debug('r_depbase_pk instance: ' + str(r_depbase_pk))
            # check if it is in allowed_depbases,
            if r_depbase_pk in allowed_depbases:
                # check if request_depbase exists
                sel_depbase_instance = sch_mod.Departmentbase.objects.get_or_none(pk=r_depbase_pk, country=requsr_country)
                if sel_depbase_instance is not None:
                    sel_depbase_save = True

        #logger.debug('request_depbase instance: ' + str(sel_depbase_instance))
        #logger.debug('sel_depbase_save: ' + str(sel_depbase_save))

        if sel_depbase_instance is None:
# - get depbase_pk from Usersetting, check if request_depbase exists
            selected_dict = req_user.get_usersetting_dict(c.KEY_SELECTED_PK)
            s_depbase_pk = selected_dict.get(c.KEY_SEL_DEPBASE_PK)
        # check if it is in allowed_depbases,
            if s_depbase_pk in allowed_depbases:
        # check if saved_depbase exists
                sel_depbase_instance = sch_mod.Departmentbase.objects.get_or_none(pk=s_depbase_pk, country=requsr_country)
        #logger.debug('saved_depbase instance: ' + str(sel_depbase_instance))

# - if there is no saved nor request examyear: get first allowed depbase_pk
        if sel_depbase_instance is None:
            if allowed_depbases and len(allowed_depbases):
                a_depbase_pk = allowed_depbases[0]
                sel_depbase_instance = sch_mod.Departmentbase.objects.get_or_none(pk=a_depbase_pk, country=requsr_country)
                if sel_depbase_instance is not None:
                    sel_depbase_save = True

        #logger.debug('sel_depbase_instance instance: ' + str(sel_depbase_instance))
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
    req_user = request.user
    if req_user:
        selected_dict = req_user.get_usersetting_dict(c.KEY_SELECTED_PK)
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



def system_updates(examyear, request):
    # these are once-only updates in tables. Data will be changed / moved after changing fields in tables
    # after uploading the new version the function can be removed

    update_examyearsetting(examyear, request)


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
        ('ex1', 'title', 'Dit formulier dient tevens voor bestelling schriftelijk werk.'),
        ('ex1', 'title', 'Ex.nr.: onder dit nummer doet de kandidaat examen.'),
        ('ex1', 'title', 'Vakken waarin geëxamineerd moet worden aangeven met x.'),
        ('ex1', 'footnote01', 'het getekend exemplaar en een digitale versie'),
        ('ex1', 'footnote02', 'vóór 1 november inzenden naar de Onderwijs Inspectie'),
        ('ex1', 'footnote03', 'en een digitale versie naar het ETE.'),
        ('ex1', 'footnote03', 'en een digitale versie naar het ETE.'),

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
        instance = sch_mod.Examyearsetting.objects.filter(
            examyear=examyear,
            key=key_value[0],
            subkey=key_value[1]).first()
        if instance is None:
            instance = sch_mod.Examyearsetting(
                examyear=examyear,
                key=key_value[0],
                subkey=key_value[1],
                setting=key_value[2]
            )
        else:
            instance.setting = key_value[2]
        instance.save()
