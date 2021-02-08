from django.shortcuts import render
from django.urls import reverse_lazy

from django.utils.translation import activate, ugettext_lazy as _
from django.utils import timezone

#from django.contrib import messages

import json #PR2018-12-21

from accounts import models as acc_mod
from awpr import constants as c
from awpr import functions as af
from awpr import settings as awpr_settings
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

menus_dict = {
'examyear': {'index': 0, 'href_tuple': ('examyears_url',),
               'caption': str(_('Exam year')), 'width': 100, 'height': height, 'pos_x': 50, 'pos_y': pos_y,
               'indent_left': indent_none, 'indent_right': indent_10,
               'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
               'submenu': ('cntrlst', 'exyrlst', 'schllst', 'deplst','levllst', 'sectlst')
                },
'schools': {'index': 1, 'href_tuple': ('school_list_url',),
               'caption': str(_('School')), 'width': 90, 'height': height, 'pos_x': 45, 'pos_y': pos_y,
               'indent_left': indent_10, 'indent_right': indent_10,
               'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
               'submenu': ('cntrlst', 'exyrlst', 'schllst', 'deplst','levllst', 'sectlst')
               },
'students': {'index': 2, 'href_tuple': ('students_url',),
               'caption': str(_('Students')), 'width': 120, 'height': height, 'pos_x': 60, 'pos_y': pos_y,
                 'indent_left': indent_10, 'indent_right': indent_10,
                 'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel
                 },
'subjects': {'index': 3, 'href_tuple': ('studentsubjects_url','subjects_url'),
               'caption': str(_('Subjects')), 'width': 100, 'height': height, 'pos_x': 50, 'pos_y': pos_y,
                 'indent_left': indent_10, 'indent_right': indent_10,
                 'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
                 'submenu': ('subjlst', 'subjtyplst', 'schemlst', 'schemitemlst')
                 },
'grades': {'index': 4, 'href_tuple': ('grades_url',),
               'caption': str(_('Grades')), 'width': 120, 'height': height, 'pos_x': 60, 'pos_y': pos_y,
                 'indent_left': indent_10, 'indent_right': indent_10,
                 'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel
                 },
'results': {'index': 5, 'href_tuple': ('subjects_url',),
               'caption': str(_('Results')), 'width': 120, 'height': height, 'pos_x': 60, 'pos_y': pos_y,
                'indent_left': indent_10, 'indent_right': indent_10,
                'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel
                },
'reports': {'index': 6, 'href_tuple': ('subjects_url',),
               'caption': str(_('Reports')), 'width': 120, 'height': height,  'pos_x': 60,  'pos_y': pos_y,
               'indent_left': indent_10, 'indent_right': indent_10,
                'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel
                },
'analysis': {'index': 7, 'href_tuple': ('subjects_url',),
               'caption':  str(_('Analysis')), 'width': 90, 'height': height,  'pos_x': 45,  'pos_y': pos_y,
               'indent_left': indent_10, 'indent_right': indent_none,
                'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel
                }
}

# viewpermits: 'none', 'read', 'write', 'auth', 'admin', 'all'



def get_headerbar_param(request, page):
    # PR2018-05-28 set values for headerbar
    # params.get() returns an element from a dictionary, second argument is default when not found
    # this is used for arguments that are passed to headerbar
    #logger.debug('===== get_headerbar_param ===== ' + str(page))

    headerbar = {}
    req_user = request.user
    if req_user.is_authenticated and req_user.country:
        awp_messages = []

# -  get user_lang
        requsr_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
        activate(requsr_lang)

# - set flag in headerbar to proper language
        _class_flag, _class_flag0_hidden, _class_flag1_hidden, _class_flag2_hidden = '', '', '', ''
        if requsr_lang == 'nl':
            _class_flag = 'flag_1_0'
            _class_flag0_hidden = 'display_hide'
        elif requsr_lang == 'en':
            _class_flag = 'flag_1_1'
            _class_flag1_hidden = 'display_hide'
        elif requsr_lang == 'pm':
            _class_flag = 'flag_1_2'
            _class_flag2_hidden = 'display_hide'

# +++ display examyear -------- PR2020-11-17 PR2020-12-24
    # - get selected examyear from Usersetting
        sel_examyear, sel_examyear_save, may_select_examyear = af.get_sel_examyear_instance(request)
        if sel_examyear:
            # examyear.code is PositiveSmallIntegerField
            sel_examyear_code = sel_examyear.code
            sel_examyear_str = str(_('Exam year')) + ' ' + str(sel_examyear_code)
        else:
            # there is always an examyear selected, unless country has no examyears
            sel_examyear_str = ' <' + str(_('No exam years')) + '>'

# +++ give warning when examyear is different from current examyear,
        todays_examyear_instance = af.get_todays_examyear_instance(req_user.country)
        # niu, I think class_examyear_warning = ''
        if sel_examyear and todays_examyear_instance:
            if sel_examyear.pk != todays_examyear_instance.pk:
                # class_examyear_warning = 'navbar-item-warning'
                # PR2018-08-24 debug: in base.html  href="#" is needed,
                # because bootstrap line 233: a:not([href]):not([tabindex]) overrides navbar-item-warning
                awp_message = {'info': _("Please note: the selected exam year is different from the current exam year."),
                               'class': 'alert-warning',
                               'id': 'id_diff_exyr'}
                awp_messages.append(awp_message)

# +++ display_school -------- PR2020-10-27
        # <PERMIT> PR2020-10-27
        # - requsr_school is set when user is created and never changes
        # - may_select_school is True when:
        #   - req_user is_role_insp, is_role_admin or is_role_system:
        #   - selected school is stored in usersettings
        #   - otherwise sel_schoolbase_pk is equal to _requsr_schoolbase_pk
        # note: may_select_school only sets hover of school. Permissions are set in JS HandleHdrbarSelect
        display_school = True  # params.get('display_school', True)
        sel_school = None
        schoolname = ''
        if sel_examyear and display_school:
            sel_schoolbase, sel_schoolbase_save = af.get_sel_schoolbase_instance(request)
            schoolname = sel_schoolbase.code if sel_schoolbase.code else ''

            # get school from sel_schoolbase and sel_examyear
            sel_school = sch_mod.School.objects.get_or_none(
                base=sel_schoolbase,
                examyear=sel_examyear)

            #logger.debug('requsr_schoolbase: ' + str(requsr_schoolbase))
            if sel_school:
                schoolname += ' ' + sel_school.name
            else:
                schoolname += ' <' + str(_('School not found in this exam year')) + '>'

# +++ display department -------- PR2029-10-27 PR2020-11-17
        depname = ''
        menu_items = {}

# PR2018-08-24 select department PR2020-10-13
        display_dep = True
        if display_dep:
            sel_depbase, sel_depbase_save, allowed_depbases = af.get_sel_depbase_instance(sel_school, request)

            sel_department = sch_mod.Department.objects.get_or_none(base=sel_depbase, examyear=sel_examyear)
            if sel_department is None:
                depname = '<' + str(_('No department')) + '>'
            else:
                depname = sel_depbase.code

# ------- set menu_items -------- PR2018-12-21
        # get selected menu_key and selected_button_key from request.GET, settings or default, check viewpermit
        #XXX return_dict = lookup_button_key_with_viewpermit(request)
        #XXX setting = return_dict['setting']
        #XXX selected_menu_key = return_dict['menu_key']
        selected_menu_key = page if page else 'examyear'  # default is 'examyear'
        menu_items = set_menu_items(selected_menu_key, request)

        # return_dict: {'setting': None, 'menu_key': 'mn_exyr', 'button_key': None}
        # selected_menu_key: mn_exyr
        #logger.debug('selected_menu_key: ' + str(selected_menu_key))
        #logger.debug('menu_items: ' + str(menu_items))


        headerbar = {
            'request': request,
            'examyear_code': sel_examyear_str,
            'display_school': display_school, 'school': schoolname,
            'display_dep': display_dep, 'department': depname,
            'class_flag': _class_flag,
            'class_flag0_hidden': _class_flag0_hidden,
            'class_flag1_hidden': _class_flag1_hidden,
            'class_flag2_hidden': _class_flag2_hidden,
            'menu_items': menu_items,
            'awp_messages': awp_messages,
            'media_dir': awpr_settings.MEDIA_DIR
        }

    return headerbar

def get_saved_page_url(sel_page, request):  # PR2018-12-25 PR2020-10-22  PR2020-12-23
    logger.debug('------------ get_saved_page_url ----------------')
    logger.debug('sel_page: ' + str(sel_page))
    # only called by schools.views.Loggedin,
    # retrieves submenu_href for: return HttpResponseRedirect(reverse_lazy(saved_href))
    lookup_page = sel_page if sel_page else 'examyear'
    logger.debug('lookup_page: ' + str(lookup_page))
    page_href = ''
    menu = menus_dict.get(lookup_page)
    logger.debug('menu: ' + str(menu))
    if menu:
        # function gets first href in href_tuple, when insp or admin it gets the second item
        page_href = get_href_from_href_tuple(menu, request)
    if not page_href:
        page_href = 'home_url'

    logger.debug('page_href: ' + str(page_href))
    return page_href

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

def set_menu_items(selected_menu_key, request):
    # function is called by get_headerbar_param, creates template tags menu_items and submenus
    # setting: {'menu': 'mn_schl', 'mn_schl': 'schllst'}

    #logger.debug('===== set_menu_items ===== ')
    #logger.debug('selected_menu_key: ' + str(selected_menu_key))

    menu_item_tags = []

    # loop through all menus in menus, to retrieve href from all menu-buttons
    # from https://treyhunner.com/2016/04/how-to-loop-with-indexes-in-python/
    for key, menu in menus_dict.items():
        #logger.debug('-----------------------------')
        #logger.debug('key: ' + str(key) + ' menu: ' + str(menu))
        # menu = {'subjects': {'index': 3, 'href_tuple': ('studentsubjects_url','subjects_url'),
        #                'caption': str(_('Subjects')), 'width': 100, 'height': height, 'pos_x': 50, 'pos_y': pos_y,
        #                  'indent_left': indent_10, 'indent_right': indent_10,
        #                  'class_sel': 'menu_polygon_selected', 'class_unsel': 'menu_polygon_unselected', 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
        #                  'submenu': ('subjlst', 'subjtyplst', 'schemlst', 'schemitemlst')
        #                  },

        # lookup the href that belongs to this index in submenus_tuple
        # function gets first href in href_tuple, when insp or admin it gets the second item
        menu_href = get_href_from_href_tuple(menu, request)

    # ------------ get menu ------------
        menu_index = menu.get('index', 0)
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
        if key == selected_menu_key:
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

def get_href_from_href_tuple(menu, request): # PR2020-12-23
    #logger.debug('------------ get_href_from_href_tuple ----------------')
    # function gets first href in menu_href_tuple, when role is insp or admin: it gets the second item
    menu_href = None
    menu_href_tuple = menu.get('href_tuple', ('',))
    if menu_href_tuple:
        if len(menu_href_tuple) > 1 and (request.user.is_role_admin or request.user.is_role_insp):
            menu_href = menu_href_tuple[1]
        else:
            menu_href = menu_href_tuple[0]
    if menu_href is None:
        menu_href = 'home_url'
    return menu_href


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
    if menu_index in menus_dict:
        menu = menus_dict.get(menu_index, {})
    return menu


def get_depbase_list(request, requsr_school):  # PR2018-08-24  PR2018-11-23 PR2020-11-17
    #logger.debug('-----  get_depbase_list ----- ')
    # PR2018-10-15 function is only called by get_headerbar_param
    # function creates list of available deps in selected school and schoolyear,
    # function filters deps of user_allowed_depbase_list
    # functions sets current department, which cannot be selected in dropdown list

    depbase_pk_list = []
    may_select_dep = False
    sel_depbase_instance = None

    req_user = request.user
    if req_user and requsr_school:
        allowed_dep_count = 0
# - if school does not have any departments: sel_depbase_instance = None
        if requsr_school.depbases:
# - if requsr_allowed_depbase_list is empty: add all school_depbases to list
            if req_user.allowed_depbases is None:
                depbase_pk_list = requsr_school.depbases
                allowed_dep_count = len(depbase_pk_list)
            else:
# - if requsr_allowed_depbase_list has values:
                # iterate through departments of this school,
                # add only the ones in requsr_allowed_depbase_list
                for school_depbase_pk in requsr_school.depbases:
    # - add_to_list if school_depbase is in requsr_allowed_depbase_list
                    if school_depbase_pk in req_user.allowed_depbases:
                        depbase_pk_list.append(school_depbase_pk)
                        allowed_dep_count += 1
    # if there is only 1 allowed dep: set user_dep = this dep
            if allowed_dep_count == 1:
                sel_depbase_pk = depbase_pk_list[0]
                sel_depbase_instance = sch_mod.Departmentbase.objects.get_or_none(pk=sel_depbase_pk, country=req_user.country)
            elif allowed_dep_count > 1:
# - get saved sel_depbase: if multiple exist in depbase_pk_list
                saved_sel_depbase_instance = af.get_saved_sel_depbase_instance(request)
    # check if saved_sel_depbase is in depbase_pk_list
                if saved_sel_depbase_instance and saved_sel_depbase_instance.pk in depbase_pk_list:
                    sel_depbase_instance = saved_sel_depbase_instance
            may_select_dep = (allowed_dep_count > 1)

    return depbase_pk_list, may_select_dep, sel_depbase_instance
# --- end of get_depbase_list ---
