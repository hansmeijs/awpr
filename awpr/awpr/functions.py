# PR2018-05-28
from django.contrib import messages
from django.utils.translation import activate, ugettext_lazy as _

from schools.models import Examyear, Department, School, Country
from awpr import constants as c
from awpr.menus import lookup_button_key_with_viewpermit, save_setting, set_menu_items

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

def get_headerbar_param(request, params):
    # PR2018-05-28 set values for headerbar
    # params.get() returns an element from a dictionary, second argument is default when not found
    # this is used for arguments that are passed to headerbar
    logger.debug('===== get_headerbar_param ===== ')

    # select_country overrides display_country
    display_country = False
    select_country = False

    display_school = params.get('display_school', False)
    # PR2018-12-15: select_school is True when user has role insp or system
    select_school = False
    if request.user.is_authenticated:
        select_school = request.user.is_role_insp_or_system

    # params.pop() removes and returns an element from a dictionary, second argument is default when not found
    # this is used for arguments that are not passed to headerbar
    override_school = params.pop('override_school', None)

    display_dep = params.get('display_dep', False)

    _select_dep = False
    # These are arguments that are added to headerbar in this function
    _country = ''
    _country_list = ''
    _examyear = ''
    _examyear_list = ''
    _schoolname = ''
    _school_list = ''
    _depname = '-'
    _depbase_list = ''
    _class_examyear_warning = ''

    menu_items = {}
    sub_items = {}

    if request.user.is_authenticated:
        # PR2018-05-11 set language
        if request.user.lang is not None:
            activate(request.user.lang)
            logger.debug('activated lang: ' + str(request.user.lang))
        else:
            activate('nl')

# ------- display_country --------
        # PR2018-08-11 display_country = True when user.is_role_system,
        # _select_country is always True when display_country = True
        select_country = request.user.is_role_system
        display_country = select_country
        # TODO display_country always True for testing only
        select_country = True
        display_country = True

        if display_country:
            _country_list = get_country_list(request.user)
            # logger.debug('_country_list: <' + str(_country_list) + '> Type: ' + str(type(_country_list)))
            if request.user.country is None:
                if select_country:
                    _country = _('<Select country>')
                    # messages.warning(request, _('Please select ancountry.'))
                else:
                    _country = _('<No country selected>')
            else:
                _country = request.user.country

# ------- display_examyear --------
        # PR2018-12-17 every logged-in user can select examyear
        #   system and insp can choose from all examyear
        #   school can only choose from examyear from that school

        _examyear_list, rowcount = get_examyear_list(request.user)

        if rowcount == 0:
            _examyear = _('<No exam years found>')
        else:
            if request.user.examyear is None:
                _examyear = _('<Select exam year>')
            else:
                _examyear = request.user.examyear# .examyear
                # if select_examyear:
                # PR2018-05-18 check if request.user.examyear equals this examyear
                if not request.user.examyear.equals_this_examyear:
                    # PR2018-08-24 debug: in base.html  href="#" is needed,
                    # because bootstrap line 233: a:not([href]):not([tabindex]) overrides navbar-item-warning
                    _class_examyear_warning = 'navbar-item-warning'
                    messages.warning(request,  _("Please note: selected exam year is different from the current exam year."))

        # ------- display_school --------
# PR2018-05-11 select school
        # TODO  True is for testing only
        select_school = True
        display_school = True

        if display_school:
            if override_school:
                _schoolname = override_school
            else:
                _school_list = get_school_list(request.user)
                if request.user.schoolbase is None:
                    if select_school:
                        _schoolname = _('<Select school>')
                        # messages.warning(request, _('Please select a school.'))
                    else:
                        _schoolname = _('<No school selected>')
                else:
                    if request.user.examyear is None:
                        _schoolname = _('<No exam year selected>')
                    else:
                        # PR2018-10-15
                        # TODO test both ways to get schoolname
                        _school = School.objects.filter(base=request.user.schoolbase, examyear=request.user.examyear).first()
                        # _schoolbase = request.user.schoolbase
                        # _school = _schoolbase.school_set.filter(examyear=request.user.examyear).first()
                        if _school is not None:
                            if select_school:
                                _schoolname = _school.code + ' - ' + _school.name
                            else:
                                _schoolname = _school.name

# PR2018-08-24 select department
        if display_dep:
            _depbase_list, allowed_dep_count = get_depbase_list(request)
            # logger.debug('------------ get_headerbar_param ------------------------')
            # logger.debug('depbase_list: <' + str(_depbase_list) + '> Type: ' + str(type(_depbase_list)))
            # logger.debug('depbase_count: <' + str(allowed_dep_count) + '> Type: ' + str(type(allowed_dep_count)))
            if allowed_dep_count == 0:
                _depname = _('<No departments found>')
            else:
                if allowed_dep_count > 1:
                    _select_dep = True

                _depname = _('<Select department>')
                if request.user.depbase:
                    department = Department.objects.filter(base=request.user.depbase, examyear=request.user.examyear).first()
                    if department:
                        _depname = department.abbrev

# ------- set menu_items -------- PR2018-12-21

        # get selected menu_key and selected_button_key from request.GET, settings or default, check viewpermit
        return_dict = lookup_button_key_with_viewpermit(request)
        setting = return_dict['setting']
        menu_key = return_dict['menu_key']
        button_key = return_dict['button_key']

        # update or create usersetting
        save_setting(request, setting, menu_key, button_key)

        menu_items, sub_items = set_menu_items(request, setting, menu_key, button_key)


    else:
        activate('nl')

    headerbar = {
        'request': request,
        'display_country': display_country, 'select_country': select_country, 'country': _country, 'country_list': _country_list,
        'examyear': _examyear, 'examyear_list': _examyear_list, 'class_examyear_warning': _class_examyear_warning,
        'display_school': display_school, 'select_school': select_school, 'school': _schoolname, 'school_list': _school_list,
        'display_dep': display_dep, 'select_dep': _select_dep, 'departmentname': _depname, 'depbase_list': _depbase_list,
        'menu_items': menu_items, 'sub_items': sub_items,
    }

    # append the rest of the dict 'params' to the dict 'headerbar'.
    # the rest can be for instance: {'form': form},  {'countries': countries}
    headerbar.update(params)
    # logger.debug('get_headerbar_param headerbar: ' + str(headerbar))

    return  headerbar

def get_country_list(request_user):
    # PR2018-12-17   country_list: [{'pk': '1', 'country': 'Curaçao', 'selected': False},
    #                               {'pk': '2', 'country': 'Sint Maarten', 'selected': True}]
    country_list = []
    if request_user is not None:
        for country in Country.objects.all():
            # selected country will be disabled in dropdown list
            selected = False
            if request_user.country is not None:
                if country == request_user.country:
                    selected = True
            row_dict = {'pk': str(country.id), 'country':country.name, 'selected': selected}
            country_list.append(row_dict)
    return country_list

def get_examyear_list(request_user):
    # PR2018-05-14 objects.order_by('-examyear').all() not necessary, because model class Meta: ordering=['-examyear',]

    # PR2018-05-14 if user not authenticated examyear_list is not used in base.html

    #examyear_list: [{'pk': '2', 'examyear': '2019', 'selected': True},
    #                  {'pk': '1', 'examyear': '2018', 'selected': False}]

    # PR2018-12-18  when school user: show only published examyears

    examyear_list = []
    rowcount = 0
    if request_user is not None:
        if request_user.country is not None:
            # when request_user.is_role_insp_or_system: show all examyears
            if request_user.is_role_insp_or_system:
                rowcount = Examyear.objects.filter(country=request_user.country).count()
                if rowcount:
                    # show only examyears in request_user.country
                    for item in Examyear.objects.filter(country=request_user.country):
                        # PR 2018-05-19 current examyear = request.user.examyear,
                        # this_examyear = year(now) or 1 + year(now)
                        # current examyear cannot be selected in dropdown list
                        selected = False
                        if request_user.examyear is not None:
                            if item == request_user.examyear:
                                selected = True
                        row_dict = {'pk': str(item.id), 'examyear': item.examyear,
                                    'selected': selected, 'published': item.published}
                        # logger.debug('get_examyear_list row_dict: ' + str(row_dict))
                        examyear_list.append(row_dict)
            else:
                # when request_user.is_role_school: show only examyears of user's school
                if request_user.examyear is not None:

                    # check if user.examyear.country equals user.country
                    request_user_examyear = None
                    if request_user.examyear.country.pk == request_user.country.pk:
                        request_user_examyear = request_user.examyear

                    rowcount = School.objects.filter(base=request_user.schoolbase, examyear__published=True).count()
                    # rowcount = School.objects.filter(base=request_user.schoolbase).count()
                    if rowcount:
                        # logger.debug('get_examyear_list request_user.country: ' + str(request_user.country))
                        # show only examyears in request_user.country
                        for item in School.objects.filter(base=request_user.schoolbase):
                            # PR 2018-05-19 current examyear = request.user.examyear, this_examyear = year(now) or 1 + year(now)
                            # current examyear cannot be selected in dropdown list
                            selected = False
                            if request_user_examyear is not None:
                                if item.examyear == request_user_examyear:
                                    selected = True
                            row_dict = {'pk':str(item.examyear.id), 'examyear':item.examyear.examyear, 'selected':selected }
                            examyear_list.append(row_dict)

    return examyear_list, rowcount

def get_school_list(request_user):
    # PR2018-05-28 school_list: [{'pk': '1', 'school': 'SXM01 -  Milton Peters College', 'selected': False}
    # PR2018-08-04 omit schoolcode when user is School
    # PR2018-10-15 get name from school
    school_list = []
    rowcount = 0
    if request_user is not None:
        if request_user.country is not None and request_user.examyear is not None:
            if request_user.examyear.country.pk == request_user.country.pk:
                if request_user.is_role_insp_or_system:
                    rowcount = School.objects.filter(examyear=request_user.examyear).count()
                    if rowcount:
                        # show only schools in request_user.examyear, (country is parent of examyear)
                        schools = School.objects.filter(examyear=request_user.examyear)

                        for school in schools:
                            _schoolbase_id = school.base.id
                            _school_name = ''
                            # current school cannot be selected in dropdown list
                            selected = False
                            if request_user.schoolbase is not None:
                                if school.base == request_user.schoolbase:
                                    selected = True

                            # PR2018-08-04 omit schoolcode when request_user role=School
                            if request_user.is_role_insp_or_system:
                                _school_name = school.code + ' - ' + school.name
                            else:
                                _school_name = school.name

                            row_dict = {'pk':str(_schoolbase_id), 'school':_school_name, 'selected':selected }
                            # logger.debug('get_school_list row_dict: ' + str(row_dict))
                            school_list.append(row_dict)
                else:
                    if request_user.schoolbase:
                        rowcount = School.objects.filter(base=request_user.schoolbase, examyear=request_user.examyear).count()
                        if rowcount == 1:
                            # show only schools in request_user.examyear, (country is parent of examyear)
                            school = School.objects.filter(base=request_user.schoolbase, examyear=request_user.examyear).first()
                            if school:
                                row_dict = {'pk': str(school.base.id), 'school': school.name, 'selected': True}
                                # logger.debug('get_school_list row_dict: ' + str(row_dict))
                                school_list.append(row_dict)

    return school_list

def get_depbase_list(request):  # PR2018-08-24  PR2018-11-23
    # PR2018-10-15 function is only called by get_headerbar_param
    # function creates list of available deps in selected school and schoolyear,
    # function filters deps of user_allowed_depbase_list
    # functions sets current department, which cannot be selected in dropdown list
    # depbase_list: [{'pk': '1', 'department': 'Vsbo', 'is_cur_dep': False}

    depbase_list = []
    has_cur_dep = False
    allowed_dep_count = 0
    request_user_depbase_is_modified = False
    if request:
        if request.user is not None:
            if request.user.country is not None and request.user.examyear is not None:
                if request.user.country == request.user.examyear.country:
            # get selected school from schoolbase and examyear
                    if request.user.schoolbase is not None:
                        school = School.objects.filter(base=request.user.schoolbase, examyear=request.user.examyear).first()
                        # logger.debug('---------get_depbase_list-------------')
                        # logger.debug('school: <' + str(school) + '> type: ' + str(type(school)) + '')
                        # logger.debug('request_user.depbase: ' + str(request.user.depbase))
                        if school is not None:
            # get depbase_list of school
                            if school.depbase_list:
            # slice off first and last delimiter from school.depbase_list
                                school_depbase_list = slice_firstlast_delim(school.depbase_list)
                                # logger.debug('school.depbase_list: <' + str(school.depbase_list) + '> type: ' + str(type(school.depbase_list)) + '')
            # make array of school_depbase_list
                                school_depbase_array = school_depbase_list.split(';')
                                if bool(school_depbase_array):
            # get allowed departments of request user
                                    user_allowed_depbase_list = request.user.allowed_depbase_list
                                    # logger.debug('user_allowed_depbase_list: ' + str(user_allowed_depbase_list))
            # count departments of depbase_array and check if user_dep is in school_depbase_list
            # iterate through departments of this school
                                    for base_id_str in school_depbase_array:
                                        # logger.debug('user_allowed_depbase_list: ' + str(base_id_str))
                                        if base_id_str:
            # if user_allowed_depbase_list has value: check if dep is in user_allowed_depbase_list, otherwise allowed = True
                                            is_allowed = id_found_in_list(
                                                id_str=base_id_str,
                                                list_str=user_allowed_depbase_list,
                                                value_at_empty_list=True
                                            )
                                            # logger.debug('base_id_str: ' + str(base_id_str) + ' is_allowed: ' + str(is_allowed))
                                            if is_allowed:
            # if dep is_allowed: get department
                                                base_id_int = int(base_id_str)
                                                dep = Department.objects.filter(base__id=base_id_int, examyear=request.user.examyear).first()
                                                if dep is not None:
            # give value to is_cur_dep: current department cannot be selected in dropdown list
                                                    is_cur_dep = False
                                                    if request.user.depbase is not None:
                                                        if dep.base.pk == request.user.depbase.pk:
                                                            is_cur_dep = True
                                                            has_cur_dep = True
                                                            # logger.debug('is_cur_dep = True dep.base.pk: ' + str(dep.base.pk))
            # get dep.shortname
                                                    dep_name = ''
                                                    if dep.abbrev:
                                                        dep_name = dep.abbrev
                                                    # logger.debug('dep_name: ' + str(dep_name))
            # add row to depbase_list
                                                    row_dict = {'pk': base_id_str, 'dep_name': dep_name, 'is_cur_dep': is_cur_dep}
                                                    # logger.debug('row_dict: ' + str(row_dict))
                                                    depbase_list.append(row_dict)

                                                    allowed_dep_count += 1
                                                    # logger.debug('allowed_dep_count: ' + str(allowed_dep_count))

            # if request_user.depbase is not found and school has only 1 dep: set user_dep = this dep

            # if there are allowed deps and current_dep is an allowed dep: do nothing
                    if not has_cur_dep:
                        # there are no allowed deps or current_dep is not an allowed dep:
                        if allowed_dep_count == 1:
                            # if there is only 1 allowed dep: make this dep the current dep
                            row_dict_pk_int = int(depbase_list[0]['pk'])

                            department = Department.objects.filter(id=row_dict_pk_int).first()
                            # logger.debug('department: ' + str(department) + ' Type: ' + str(type(department)))

                            request.user.depbase = department.base
                            # logger.debug('request.user.depbase: ' + str(request.user.depbase) + ' Type: ' + str(type(request.user.depbase)))

                            request_user_depbase_is_modified = True
                            # set is_cur_dep true
                            depbase_list[0]['is_cur_dep'] = True
                        else:
                            # if there are multiple allowed deps: remove current dep, because it is not in the allowed deps
                            if request.user.depbase is not None:
                                request.user.depbase = None
                                request_user_depbase_is_modified = True
                if request_user_depbase_is_modified:
                    request.user.save(request=request)

        # logger.debug('depbase_list: ' + str(depbase_list) + ' allowed_dep_count: '  + str(allowed_dep_count))
        # logger.debug('request.user.depbase: ' + str(request.user.depbase))
        # logger.debug('---------get_depbase_list END -------------')
        # logger.debug('   ')

    return depbase_list, allowed_dep_count
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


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
    countries = Country.objects.all()
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
    # logger.debug('class User(AbstractUser) self.selecteduser_countryid: ' + str(selecteduser_countryid))
    #schooldefaults = Schooldefault.objects.filter(country=request_user.country)
    #for item in schooldefaults:
    #    item_str = ''
    #    if item.code is not None:
    #        item_str = str(item.code) + ' - '
    #    if item.name is not None:
    #        item_str = item_str + str(item.name)
    #    choices.append((item.id, item_str))

    # logger.debug('class User(AbstractUser) schooldefault_choices: ' + str(choices))
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
                # logger.debug('get_depbase_list_field_sorted_zerostripped dep: <' + str(dep) + '> Type: ' + str(type(dep)))
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
    # logger.debug('get_tuple_from_list_str tuple list_tuple <' + str(list_tuple) + '> Type: " + str(list_tuple))
    return list_tuple


def id_found_in_list(id_str='', list_str='', value_at_empty_list = False):  # PR2018-11-22
    # Function searches for id in string,
    # e.g.: id '2' will serach ';1' in ';1;2;3;'
    found = value_at_empty_list
    # PR2018-11-23 debug: error 'must be str, not int', argument changes form str to int, don't now why. Usse str()
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

