from django.shortcuts import render
from django.urls import reverse_lazy

from django.utils.translation import activate, ugettext_lazy as _
from django.utils import timezone

#from django.contrib import messages

import json #PR2018-12-21

from accounts import models as acc_mod
from awpr import constants as c
from awpr import functions as af
from schools import models as sch_mod
from schools import dicts as sch_dicts

import logging
logger = logging.getLogger(__name__)


height = 32
indent_none = 0
indent_10 = 10
pos_y = 18
class_sel = 'fill:#2d4e77;stroke:#2d4e77;stroke-width:1'
class_unsel = 'fill:#bacee6;stroke:#bacee6;stroke-width:1'
fill_sel = '#EDF2F8'
fill_unsel = '#212529'

menus = {
'examyear': {'href': 'examyears_url',
               'caption': str(_('Exam year')), 'width': 100, 'height': height, 'pos_x': 50, 'pos_y': pos_y,
               'indent_left': indent_none, 'indent_right': indent_10,
               'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
               'submenu': ('cntrlst', 'exyrlst', 'schllst', 'deplst','levllst', 'sectlst')
                },
'schools': {'href': 'school_list_url',
               'caption': str(_('School')), 'width': 90, 'height': height, 'pos_x': 45, 'pos_y': pos_y,
               'indent_left': indent_10, 'indent_right': indent_10,
               'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
               'submenu': ('cntrlst', 'exyrlst', 'schllst', 'deplst','levllst', 'sectlst')
               },
'subjects': {'href': 'subjects_url',
               'caption': str(_('Subjects')), 'width': 100, 'height': height, 'pos_x': 50, 'pos_y': pos_y,
                 'indent_left': indent_10, 'indent_right': indent_10,
                 'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
                 'submenu': ('subjlst', 'subjtyplst', 'schemlst', 'schemitemlst')
                 },
'students': {'href': 'students_url',
               'caption': str(_('Students')), 'width': 120, 'height': height, 'pos_x': 60, 'pos_y': pos_y,
                 'indent_left': indent_10, 'indent_right': indent_10,
                 'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel
                 },
'grades': {'href': 'students_url',
               'caption': str(_('Grades')), 'width': 120, 'height': height, 'pos_x': 60, 'pos_y': pos_y,
                 'indent_left': indent_10, 'indent_right': indent_10,
                 'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel
                 },
'results': {'href': 'subjects_url',
               'caption': str(_('Results')), 'width': 120, 'height': height, 'pos_x': 60, 'pos_y': pos_y,
                'indent_left': indent_10, 'indent_right': indent_10,
                'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel
                },
'reports': {'href': 'subjects_url',
               'caption': str(_('Reports')), 'width': 120, 'height': height,  'pos_x': 60,  'pos_y': pos_y,
               'indent_left': indent_10, 'indent_right': indent_10,
                'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel
                },
'analysis': {'href': 'subjects_url',
               'caption':  str(_('Analysis')), 'width': 120, 'height': height,  'pos_x': 60,  'pos_y': pos_y,
               'indent_left': indent_10, 'indent_right': indent_none,
                'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel
                }
}

"""
    
'package': {'href': 'subjects_url',
               'caption': 'Study program', 'width': 140, 'height': height, 'pos_x': 70, 'pos_y': pos_y,
                      'indent_left': indent_10, 'indent_right': indent_10,
                     'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
                     'submenu': ('subjlst', 'subjtyplst', 'schemlst')
                     },

'schoolexam': {'href': 'subjects_url',
               'caption': 'School exam', 'width': 140, 'height': height, 'pos_x': 70, 'pos_y': pos_y,
                   'indent_left': indent_10, 'indent_right': indent_10,
                   'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
                   'submenu': ('subjlst', 'subjtyplst', 'schemlst')
                   },
'reexam': {'href': 'subjects_url',
               'caption': 'Re-exam', 'width': 120, 'height': height, 'pos_x': 60, 'pos_y': pos_y,
               'indent_left': indent_10, 'indent_right': indent_10,
               'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
               'submenu': ('subjlst', 'subjtyplst', 'schemlst')
               },
"""


# viewpermits: 'none', 'read', 'write', 'auth', 'admin', 'all'



def get_headerbar_param(request, params):
    # PR2018-05-28 set values for headerbar
    # params.get() returns an element from a dictionary, second argument is default when not found
    # this is used for arguments that are passed to headerbar
    #logger.debug('===== get_headerbar_param ===== ')
    #logger.debug('params: ' + str(params))


    # - _select_department is allway True for now - TODO set _select_department when allowed_depbase_list has multiple departments PR2020-10-13

    headerbar = {}
    req_user = request.user
    if req_user.is_authenticated:
        awp_messages = []

# +++ set language # PR2018-05-11
        req_user_lang = req_user.lang if req_user.lang else 'nl'
        activate(req_user_lang)

    # - set flag in headerbar to proper language
        _class_flag, _class_flag0_hidden, _class_flag1_hidden, _class_flag2_hidden = '', '', '', ''
        if req_user_lang == 'nl':
            _class_flag = 'flag_1_0'
            _class_flag0_hidden = 'display_hide'
        elif req_user_lang == 'en':
            _class_flag = 'flag_1_1'
            _class_flag1_hidden = 'display_hide'
        elif req_user_lang == 'pm':
            _class_flag = 'flag_1_2'
            _class_flag2_hidden = 'display_hide'

# +++ display selected examyear of req_usr, show warning when examyear is not this_examyear
        _examyear = req_user.examyear
        _examyear_int = _examyear.examyear if _examyear.examyear else 0
        _examyear_str = str(_('Exam year')) + ' ' + str(_examyear_int) \
            if _examyear_int else ' <' + str(_('Select exam year')) + '>'

        now = timezone.now()
        this_examyear = now.year
        if now.month > 7:
            this_examyear = now.year + 1

        _class_examyear_warning = 'navbar-item-warning' if _examyear_int != this_examyear else ''
        if _examyear_int != this_examyear:
            # PR2018-08-24 debug: in base.html  href="#" is needed,
            # because bootstrap line 233: a:not([href]):not([tabindex]) overrides navbar-item-warning
            awp_message = {'info': _("Please note: selected exam year is different from the current exam year."),
                           'class': 'alert-warning',
                           'id': 'id_diff_exyr'}
            awp_messages.append(awp_message)

# +++ display_school -------- PR2029-10-27
        # <PERMIT> PR2020-10-27
        # - select_school is True when user can change the selected school PR2018-12-15:
        #   - user can only change school when req_user is_role_insp, is_role_admin or is_role_system:
        #   - otherwise sel_schoolbase_pk is equal to _req_user_schoolbase_pk
        # note: select_school only sets hover of school. Permissions are set in JS HandleHdrbarSelect
        display_school = params.get('display_school', True)
        select_school = False
        class_select_school = 'awp_navbar_item'
        _schoolname = ''
        req_user_school_depbases = []
        if display_school:
            if req_user.is_role_insp or req_user.is_role_admin or req_user.is_role_system:
                select_school = True
                class_select_school = 'awp_navbar_item_with_hover'

        if display_school:
            # when user can select school the value is retrieved from usersettings and set in JS, display here:' Select school'
            # when user cannot select school de req_user school is displayed
            if select_school:
                _schoolname = ' <' + str(_('Select school')) + '>'
            else:
                req_user_schoolbase = req_user.schoolbase
                if req_user_schoolbase is None:
                    _schoolname = ' <' + str(_('No school selected')) + '>'
                else:
                    _schoolname = req_user_schoolbase.code
                    req_user_examyear = req_user.examyear
                    if req_user_examyear is None:
                        _schoolname += ' <' + str(_('No exam year selected')) + '>'
                    else:
                        req_user_school = sch_mod.School.objects.get_or_none(
                            base=req_user_schoolbase,
                            examyear=req_user_examyear
                        )
                        if req_user_school is not None:
                            _schoolname += ' - ' + req_user_school.name
                        else:
                            _schoolname += ' <' + str(_('School not found in this exam year')) + '>'
                        if req_user_school.depbases:
                            req_user_school_depbases = req_user_school.depbases
# +++ display department -------- PR2029-10-27
        display_dep = params.get('display_dep', False)
        _select_dep = True
        depbase_list = get_depbase_list(req_user_school_depbases, req_user.allowed_depbase_list)
        #logger.debug('depbase_list: ' + str(depbase_list))

        # params.pop() removes and returns an element from a dictionary, second argument is default when not found
        # this is used for arguments that are not passed to headerbar
        #override_school = params.pop('override_school', None)

        # These are arguments that are added to headerbar in this function

        _depname = '-'
        depbases = []

        menu_items = {}



# PR2018-08-24 select department PR2020-10-13

        if display_dep:
            if req_user.depbase is None:
                if _select_dep:
                    _depname = '<' + str(_('Select department')) + '>'
                    # messages.warning(request, _('Please select a school.'))
                else:
                    _depname = '<' + str(_('No department selected')) + '>'
            else:
                if req_user.examyear is None:
                    _depname = '<' + str(_('No exam year selected')) + '>'
                else:
                    _department = sch_mod.Department.objects.filter(
                        base=req_user.depbase,
                        examyear=req_user.examyear).first()
                    if _department is not None:
                        _depname = _department.abbrev
                    else:
                        _depname = '<' + str(_('Department not found in this exam year')) + '>'

# ------- set menu_items -------- PR2018-12-21
        # get selected menu_key and selected_button_key from request.GET, settings or default, check viewpermit
        #XXX return_dict = lookup_button_key_with_viewpermit(request)
        #XXX setting = return_dict['setting']
        #XXX selected_menu_key = return_dict['menu_key']
        selected_menu_key = params.get('menu_key', 'examyear')  # default is 'examyear'

        menu_items = set_menu_items(selected_menu_key)

        # return_dict: {'setting': None, 'menu_key': 'mn_exyr', 'button_key': None}
        # selected_menu_key: mn_exyr
        #logger.debug('selected_menu_key: ' + str(selected_menu_key))
        #logger.debug('menu_items: ' + str(menu_items))


        headerbar = {
            'request': request,
            'examyear': _examyear_str, 'class_examyear_warning': _class_examyear_warning,
            'display_school': display_school, 'class_select_school': class_select_school, 'school': _schoolname,
            'display_dep': display_dep, 'select_dep': _select_dep, 'department': _depname, 'depbase_list': depbases,
            'class_flag': _class_flag,
            'class_flag0_hidden': _class_flag0_hidden,
            'class_flag1_hidden': _class_flag1_hidden,
            'class_flag2_hidden': _class_flag2_hidden,
            'menu_items': menu_items,
            'awp_messages': awp_messages
        }

        # append the rest of the dict 'params' to the dict 'headerbar'.
        # the rest can be for instance: {'form': form},  {'countries': countries}
        headerbar.update(params)

    return headerbar



def get_saved_page_url(sel_page):  # PR2018-12-25 PR2020-10-22
    # only called by schools.views.Loggedin,
    # retrieves submenu_href for: return HttpResponseRedirect(reverse_lazy(saved_href))
    lookup_page = sel_page if sel_page else 'examyear'
    page_url = None
    menu_btn = menus.get(lookup_page)
    if menu_btn:
        page_url = menu_btn.get('href')

    if page_url is None:
        page_url = 'home_url'

    return page_url

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

def set_menu_items(selected_menu_key):
    # function is called by get_headerbar_param, creates template tags menu_items and submenus
    # setting: {'menu': 'mn_schl', 'mn_schl': 'schllst'}

    #logger.debug('===== set_menu_items ===== ')
    #logger.debug('selected_menu_key: ' + str(selected_menu_key))

    menu_item_tags = []

    # loop through all menus in menus, to retrieve href from all menu-buttons
    # from https://treyhunner.com/2016/04/how-to-loop-with-indexes-in-python/
    for menu_index, menu_key in enumerate(menus):
        #logger.debug('-----------------------------')
        #logger.debug('menu_key: "' + str(menu_key) + '"')

        # get menu_dict with key menu_key from menus, if not found: menu_dict = None
        # menu = {'caption': 'Subjects', ....,
        #         'submenu': ('cntrlst', 'exyrlst', 'schllst', 'deplst','levllst', 'sectlst')
        menu = get_value_from_dict(menu_key, menus)
        #logger.debug('menu: ' + str(menu))

        # lookup the href that belongs to this index in submenus_tuple
        menu_href = menu.get('href', '')
        #logger.debug('menu_href: "' + str(menu_href) + '"')

    # ------------ get menu ------------
        index_str = '0' + str(menu_index)
        svg_id = 'id_svg' + index_str[-2]
        polygon_id = 'id_plg' + index_str[-2]

        caption = menu.get('caption', '-')

    # add menu_key to GET parameters of menu link
        # e.g.: h_ref_reverse: /subject/?menu=mn_rep&sub=subjlst

        # Menu-items don't have their own link but use the link of selected submenu instead.
        # GET parameters are needed to mark the buttons in the menu and submenu as 'selected'

        h_ref_reverse = ''
        if menu_href:
           h_ref_reverse = reverse_lazy(menu_href)

        # highlight selected menu
        if menu_key == selected_menu_key:
            polygon_class = menu.get('class_sel', '')
            text_fill = menu.get('fill_sel', '')
        else:
            polygon_class = menu.get('class_unsel', '')
            text_fill = menu.get('fill_unsel', '')
        #logger.debug('polygon_class: ' + str(polygon_class))
        #logger.debug('caption: ' + str(caption))

        # add menu settings to parameter 'menu_item'
        indent_left = menu.get('indent_left', 0)
        indent_right = menu.get('indent_right', 0)
        height = menu.get('height', 0)
        width = menu.get('width', 0)
        points = get_svg_arrow(width, height, indent_left, indent_right)
        pos_y = menu.get('pos_y', 0)
        pos_x = menu.get('pos_x', 0)
        menu_item_tag= {'svg_id': svg_id, 'caption': caption, 'href': h_ref_reverse, 'polygon_id': polygon_id,
                   'width': str(width), 'height':  str(height), 'points': points,
                    'class': polygon_class, 'x': str(pos_x), 'y': pos_y, 'fill': text_fill}
        menu_item_tags.append(menu_item_tag)

    return menu_item_tags

def menubutton_has_view_permit(request, menubutton):
    # PR2018-12-23 submenus are only visible when user_role and user_permit have view_permit
    # !!! this does not block user from viewing page via url !!!
    # 'viewpermit': {'insp': 'all', 'system': 'auth admin'}},
    viewpermit = get_value_from_dict('viewpermit', menubutton)

    has_permit = has_view_permit(request, viewpermit)
    return has_permit


def has_view_permit(request, viewpermits):
    # Function checks if user role and permits are in the list of VIEW_PERMITS  # PR2018-12-23
    # viewpermits: {'insp': 'all', 'system': 'auth admin'}

    allowed = False
    if viewpermits:
        # allowed if key 'all' in viewpermits: {'all': 'all'}
        allowed = False  # c.PERMIT_STR_15_ALL in viewpermits
        if not allowed:
            # role_abbr: 'system'
            role_abbr = c.ROLE_DICT.get(request.user.role, '')
            if role_abbr in viewpermits:
                #logger.debug('role_abbr "' + str(role_abbr) + '" found in : "' + str(permits_view) + '"')
                permits = viewpermits.get(role_abbr, '')
                if permits:
                    # is_allowed = True when 'all' in permits
                    allowed =  False  # c.PERMIT_STR_15_ALL in permits
                    if not allowed:
                        # is_allowed = True when user_permit found in permits
                        if request.user.permits_str_tuple is not None:
                            #logger.debug('permits_str_tuple: "' + str(request.user.permits_str_tuple) + '" type: ' + str(type(request.user.permits_str_tuple)))
                            for permit in request.user.permits_str_tuple:
                                if permit in permits:
                                    #logger.debug('permit "' + str(permit) + '" found in : "' + str(permits) + '"')
                                    allowed = True
                                    break
    return allowed


def get_svg_arrow(width, height, indent_left, indent_right):
    # PR2018-12-21 creates arrow shape
    points = "0,0 " # lower left corner
    if indent_right:
        points += str(width - indent_right) + ",0 " # lower right corner
        points += str(width) + "," + str(height/2) + " "  # middle right point
        points += str(width - indent_right) + "," + str(height) + " " # top right corner
    else:
        points += str(width) + ",0 " # lower right corner
        points += str(width) + "," + str(height) + " " # top right corner
    points += "0," + str(height) + " " # top left corner
    if indent_left:
        points += str(indent_left) + "," + str(height/2)  # middle left point
    return points


def get_menu_keys_from_GET(request):
    # get selected menu_key and selected_button_key from request.GET  # PR2018-12-25 PR2020-10-05
    # look for 'page_' in key 'setting'
    # setting: {page_examyear: {mode: "get"}, },
    menu_key = None
    if request.user:
        request_get = request.GET
        # loop through request_get
        for key, value in request_get.items():
            if len(key) > 5:
                if key[0,5] == 'page_':
                    menu_key = 'mn_' +  key[5]
    return menu_key


def get_value_from_dict(key_str, dict):
    # function looks up key 'key_str' in dict, returns None if not found # PR2018-12-25
    value = None
    if dict and key_str:
        value = dict.get(key_str)  # returns None if not found
    return value


def get_menu_from_menus(menu_index):
    menu = {}
    if menu_index in menus:
        menu = menus.get(menu_index, {})
    return menu


def get_depbase_list(req_user_school_depbases, req_user_allowed_depbase_list):  # PR2018-08-24  PR2018-11-23 PR2020-10-28
    # PR2018-10-15 function is only called by get_headerbar_param
    # function creates list of available deps in selected school and schoolyear,
    # function filters deps of user_allowed_depbase_list
    # functions sets current department, which cannot be selected in dropdown list
    # depbase_list: [{'pk': '1', 'department': 'Vsbo', 'is_cur_dep': False}

    depbase_list = []
    has_cur_dep = False
    allowed_dep_count = 0
    request_user_depbase_is_modified = False

# get depbase_list of school
    if req_user_school_depbases:
        logger.debug('school.depbases: <' + str(req_user_school_depbases) + '> type: ' + str(type(req_user_school_depbases)) + '')
# make array of school_depbase_list
        school_depbase_array = req_user_school_depbases
        logger.debug('school_depbase_array: <' + str(school_depbase_array) + '> type: ' + str(type(school_depbase_array)) + '')
# get allowed departments of request user
        logger.debug('req_user_allowed_depbase_list: ' + str(req_user_allowed_depbase_list))
# count departments of depbase_array and check if user_dep is in school_depbase_list
        # TODO check school_depbase_array
        school_depbase_array = []
# iterate through departments of this school
        for base_id_str in school_depbase_array:
            logger.debug('req_user_allowed_depbase_list: ' + str(base_id_str))
            if base_id_str:
# if req_user_allowed_depbase_list has value: check if dep is in req_user_allowed_depbase_list, otherwise allowed = True
                is_allowed = af.id_found_in_list(
                    id_str=base_id_str,
                    list_str=req_user_allowed_depbase_list,
                    value_at_empty_list=True
                )
                logger.debug('base_id_str: ' + str(base_id_str) + ' is_allowed: ' + str(is_allowed))
                if is_allowed:
# if dep is_allowed: get department
                    base_id_int = int(base_id_str)
                    dep = sch_mod.Department.objects.filter(base__id=base_id_int, examyear=request.user.examyear).first()
                    if dep is not None:
# give value to is_cur_dep: current department cannot be selected in dropdown list
                        is_cur_dep = False
                        if request.user.depbase is not None:
                            if dep.base.pk == request.user.depbase.pk:
                                is_cur_dep = True
                                has_cur_dep = True
                                #logger.debug('is_cur_dep = True dep.base.pk: ' + str(dep.base.pk))
# get dep.shortname
                        dep_name = ''
                        if dep.abbrev:
                            dep_name = dep.abbrev
                        #logger.debug('dep_name: ' + str(dep_name))
# add row to depbase_list
                        row_dict = {'pk': base_id_str, 'dep_name': dep_name, 'is_cur_dep': is_cur_dep}
                        #logger.debug('row_dict: ' + str(row_dict))
                        depbase_list.append(row_dict)

                        allowed_dep_count += 1
                        #logger.debug('allowed_dep_count: ' + str(allowed_dep_count))

# if request_user.depbase is not found and school has only 1 dep: set user_dep = this dep

# if there are allowed deps and current_dep is an allowed dep: do nothing
        if not has_cur_dep:
            # there are no allowed deps or current_dep is not an allowed dep:
            if allowed_dep_count == 1:
                # if there is only 1 allowed dep: make this dep the current dep
                row_dict_pk_int = int(depbase_list[0]['pk'])

                department = sch_mod.Department.objects.filter(id=row_dict_pk_int).first()
                #logger.debug('department: ' + str(department) + ' Type: ' + str(type(department)))
                if department:
                    request.user.depbase = department.base
                    #logger.debug('request.user.depbase: ' + str(request.user.depbase) + ' Type: ' + str(type(request.user.depbase)))

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

    #logger.debug('depbase_list: ' + str(depbase_list) + ' allowed_dep_count: '  + str(allowed_dep_count))
    #logger.debug('request.user.depbase: ' + str(request.user.depbase))
    #logger.debug('---------get_depbase_list END -------------')
    #logger.debug('   ')

    return depbase_list, allowed_dep_count
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

