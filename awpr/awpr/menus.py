from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

import json #PR2018-12-21
import logging

from accounts.models import Usersetting
from awpr import constants as c

logger = logging.getLogger(__name__)


height = 32
indent_none = 0
indent_10 = 10
pos_y = 20
style_sel = 'fill:#2d4e77;stroke:#2d4e77;stroke-width:1'
style_unsel = 'fill:#bacee6;stroke:#bacee6;stroke-width:1'
fill_sel = '#EDF2F8'
fill_unsel = '#212529'

menu_school = {'caption': 'School', 'width': 90, 'height': height, 'pos_x': 45, 'pos_y': pos_y,
               'indent_left': indent_none, 'indent_right': indent_10,
               'style_sel': style_sel, 'style_unsel': style_unsel, 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
               'submenu': ('cntrlst', 'exyrlst', 'schllst', 'deplst','levllst', 'sectlst')
               }
menu_subjects = {'caption': 'Subjects', 'width': 100, 'height': height, 'pos_x': 50, 'pos_y': pos_y,
                 'indent_left': indent_10, 'indent_right': indent_10,
                 'style_sel': style_sel, 'style_unsel': style_unsel, 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
                 'submenu': ('subjlst', 'subjtyplst', 'schemlst')
                 }
menu_students = {'caption': 'Students', 'width': 120, 'height': height, 'pos_x': 60, 'pos_y': pos_y,
                 'indent_left': indent_10, 'indent_right': indent_10,
                 'style_sel': style_sel, 'style_unsel': style_unsel, 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
                 'submenu': ('studlst', 'impstud', 'subjtyplst','schemlst')
                 }
menu_package = {'caption': 'Study program', 'width': 140, 'height': height, 'pos_x': 70, 'pos_y': pos_y,
                      'indent_left': indent_10, 'indent_right': indent_10,
                     'style_sel': style_sel, 'style_unsel': style_unsel, 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
                     'submenu': ('subjlst', 'subjtyplst', 'schemlst')
                     }
menu_schoolexam = {'caption': 'School exam', 'width': 140, 'height': height, 'pos_x': 70, 'pos_y': pos_y,
                   'indent_left': indent_10, 'indent_right': indent_10,
                   'style_sel': style_sel, 'style_unsel': style_unsel, 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
                   'submenu': ('subjlst', 'subjtyplst', 'schemlst')
                   }
menu_centalexam = {'caption': 'Central exam', 'width': 140, 'height': height, 'pos_x': 70, 'pos_y': pos_y,
                   'indent_left': indent_10, 'indent_right': indent_10,
                   'style_sel': style_sel, 'style_unsel': style_unsel, 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
                   'submenu': ('subjlst', 'subjtyplst', 'schemlst')
                   }
menu_reexam = {'caption': 'Re-exam', 'width': 120, 'height': height, 'pos_x': 60, 'pos_y': pos_y,
               'indent_left': indent_10, 'indent_right': indent_10,
               'style_sel': style_sel, 'style_unsel': style_unsel, 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
               'submenu': ('subjlst', 'subjtyplst', 'schemlst')
               }
menu_results = {'caption': 'Results', 'width': 120, 'height': height, 'pos_x': 60, 'pos_y': pos_y,
                'indent_left': indent_10, 'indent_right': indent_10,
                'style_sel': style_sel, 'style_unsel': style_unsel, 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
                'submenu': ('subjlst', 'subjtyplst', 'schemlst')
                }
menu_reports = {'caption': 'Reports',  'width': 120, 'height': height,  'pos_x': 60,  'pos_y': pos_y,
               'indent_left': indent_10, 'indent_right': indent_none,

                'style_sel': style_sel, 'style_unsel': style_unsel, 'fill_sel': fill_sel, 'fill_unsel': fill_unsel,
                'submenu': ('subjlst', 'subjtyplst', 'schemlst')
                }
menus = {'mn_schl': menu_school, 'mn_subj': menu_subjects, 'mn_stud': menu_students, 'mn_pack': menu_package,
               'mn_se': menu_schoolexam, 'mn_ce': menu_centalexam, 'mn_reex': menu_reexam, 'mns_res': menu_results, 'mn_rep': menu_reports}


menu_default = {'menu': 'mn_schl', 'mn_schl': 'schllst', 'mn_subj': 'subjlst', 'mn_stud': 'studlst', 'mn_pack': 'subjlst',
              'mn_se': 'subjlst', 'mn_ce': 'subjlst', 'mn_reex': 'subjlst', 'mns_res': 'subjlst', 'mn_rep': 'subjlst'
              }
menubuttons = {
'home': {'caption': 'Home', 'href': 'home',  'viewpermits': {'all': 'all'}},
'cntrlst': {'caption': 'Countries', 'href': 'country_list_url', 'viewpermits': {'insp': 'all', 'system': 'auth admin'}},
'exyrlst': {'caption': 'Exam years', 'href': 'examyear_list_url',  'viewpermits': {'all': 'all'}},
'schllst': {'caption': 'Schools', 'href': 'school_list_url', 'viewpermits': {'all': 'all'}},
'deplst': {'caption': 'Departments', 'href': 'department_list_url', 'viewpermits': {'all': 'all'}},
'levllst': {'caption': 'Levels', 'href': 'level_list_url', 'viewpermits': {'all': 'all'}},
'sectlst': {'caption': 'Sectors', 'href': 'sector_list_url', 'viewpermits': {'all': 'all'}},
'subjlst': {'caption': 'Subjects', 'href': 'subject_list_url', 'viewpermits': {'all': 'all'}},
'subjtyplst': {'caption': 'Subject types', 'href': 'subjecttype_list_url', 'viewpermits': {'all': 'all'}},
'schemlst': {'caption': 'Subject schemes', 'href': 'scheme_list_url', 'viewpermits': {'all': 'all'}},
'studlst': {'caption': 'Students', 'href': 'student_list_url', 'viewpermits': {'all': 'all'}},
'impstud': {'caption': 'Import students', 'href': 'import_student_url', 'viewpermits': {'school': 'admin', 'insp': 'none','system': 'admin'}}
}


# ---- get  get_saved_submenu_url
def get_saved_menubutton_url(request):  # PR2018-12-25
    # only called by schools.views.Loggedin,
    # retrieves submenu_href for: return HttpResponseRedirect(reverse_lazy(saved_href))

    # get selected menu_key and selected_button_key from request.GET, settings or default, check viewpermit
    return_dict = lookup_button_key_with_viewpermit(request)
    button_key = return_dict['button_key']

    submenu_href = None
    # get menubutton with key button_key from menubuttons
    menubutton = get_value_from_dict(button_key, menubuttons)
    if menubutton:
        # PR2018-12-23 submenus are only visible when user_role and user_permit have view_permit
        # !!! this does not block user from viewing page via url !!!

        # 'viewpermit': {'insp': 'all', 'system': 'auth admin'}},
        viewpermits = get_value_from_dict('viewpermits', menubutton)
        # set href, only when request has view_permit
        if has_view_permit(request, viewpermits):
            submenu_href = get_value_from_dict('href', menubutton)

    if not submenu_href:
        submenu_href = 'home'

    return submenu_href


def save_setting(request, setting, menu_key, button_key):  # PR2018-12-25
    # function is called by get_headerbar_param, creates and saves usersetting
    # logger.debug('===== save_setting ===== ')
    # logger.debug('       menu_key: ' + str(menu_key) + '  button_key: ' + str(button_key)  )

    if request.user:
    # update setting with new value of menu_key
        setting['menu'] = menu_key

    # update setting with new value of button_key
        if menu_key and button_key:
            setting[menu_key] = button_key

    # get usersetting
        if Usersetting.objects.filter(user=request.user, key_str=c.KEY_USER_MENU_SELECTED).exists():
            usersetting = Usersetting.objects.filter(user=request.user, key_str=c.KEY_USER_MENU_SELECTED).first()
        else:
    # create new usersetting if it doesn't exist
            usersetting = Usersetting(user=request.user, key_str=c.KEY_USER_MENU_SELECTED)

    # save setting in usersetting
        if setting:
            usersetting.char01 = json.dumps(setting)
            usersetting.save()

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

def lookup_button_key_with_viewpermit(request):
    # function searches for menu_key and button_key in request, setting and default
    # and checks if button havs view_permits
    # returns menu_key and button_key and menubutton  # PR2018-12-25
    # logger.debug('===== lookup_button_key_with_viewpermit ===== ')

    setting = {}
    menu_key = None
    button_key = None

    if request.user.is_authenticated:

    # get menu_key and button_key from request.GET, if not found: return None
        # request.GET: '/student/?menu=mn_stud&sub=studlst'>
        request_menu_key, request_button_key = get_menu_keys_from_GET(request)
        # logger.debug('   request_menu_key: ' + str(request_menu_key) + '  request_button_key: ' + str(request_button_key))

    # get setting_dict from get_setting_from_usersetting, if not found: return None
        #setting_dict: {'menu': 'mn_schl', 'mn_schl': 'schllst'}
        setting = get_setting_from_usersetting(request)
        saved_menu_key = get_value_from_dict('menu', setting)
        saved_button_key = get_value_from_dict(saved_menu_key, setting)

        default_menu_key = get_value_from_dict('menu', menu_default)

        is_request_key = False
        is_saved_key = False

        if request_menu_key in menus: # 'in' gives false when key = '' of key = None, no error
            # check if request-keys exist, if so: make selected
            menu_key = request_menu_key
            is_request_key = True
        elif saved_menu_key in menus:
            # if menu_key not found in request.GET: lookup in usersetting. This is the case when a user logs in
            menu_key = saved_menu_key
            is_saved_key = True
        elif default_menu_key in menus:
            # get default meny_key at first login
            menu_key = default_menu_key

        if menu_key:
            menu = get_value_from_dict(menu_key, menus)
            # show only pages with viewpermit
            buttons_keys_with_viewpermit = get_buttons_keys_with_viewpermit(request, menu)

            if is_request_key:
                if request_button_key in buttons_keys_with_viewpermit:
                    button_key = request_button_key
            if not button_key:
                if is_request_key or is_saved_key:
                    if saved_button_key in buttons_keys_with_viewpermit:
                        button_key = saved_button_key
            if not button_key:
                default_button_key = get_value_from_dict(menu_key, menu_default)
                if default_button_key in buttons_keys_with_viewpermit:
                    button_key = default_button_key
    # show home page if no other found, should not happen
    if not button_key:
        button_key = 'home' # default if no other found, should not happen

    # logger.debug('       return setting: ' + str(setting))
    # logger.debug('       return menu_key: ' + str(menu_key) + '  button_key: ' + str(button_key))

    return {'setting': setting,
            'menu_key': menu_key,
            'button_key': button_key}

def set_menu_items(request, setting, selected_menu_key, selected_button_key):
    # function is called by get_headerbar_param, creates template tags menu_items and submenus
    # setting: {'menu': 'mn_schl', 'mn_schl': 'schllst'}

    # logger.debug('===== set_menu_items ===== ')
    # logger.debug('setting: ' + str(setting))

    menu_item_tags = []
    submenu_tags = []

    # loop through all menus in menus, to retrieve href from all menu-buttons
    # from https://treyhunner.com/2016/04/how-to-loop-with-indexes-in-python/
    for menu_index, menu_key in enumerate(menus):
        # logger.debug('-----------------------------')
        # logger.debug('menu_key: "' + str(menu_key) + '"')

        # get menu_dict with key menu_key from menus, if not found: menu_dict = None
        # menu = {'caption': 'Subjects', ....,
        #         'submenu': ('cntrlst', 'exyrlst', 'schllst', 'deplst','levllst', 'sectlst')
        menu = get_value_from_dict(menu_key, menus)

        # show only buttons with view_permit
        # button_keys: ('cntrlst', 'exyrlst', 'schllst', 'deplst','levllst', 'sectlst')
        buttons_keys_with_viewpermit =  get_buttons_keys_with_viewpermit(request, menu)
        # logger.debug('buttons_keys_with_viewpermit: "' + str(buttons_keys_with_viewpermit) + '" + type: ' + str(type(buttons_keys_with_viewpermit)))

        button_key = None
        # get saved_button_key from setting, if not found: return None
        # setting_dict: {'menu': 'mn_schl', 'mn_schl': 'schllst'}
        saved_button_key = get_value_from_dict(menu_key, setting)
        if saved_button_key in buttons_keys_with_viewpermit:
            button_key = saved_button_key
        if not button_key:
            default_button_key = get_value_from_dict(menu_key, menu_default)
            if default_button_key in buttons_keys_with_viewpermit:
                button_key = default_button_key
        if not button_key:
            button_key = 'home'  # default if no other found, should not happen

        # logger.debug('--> button_key: ' + str(saved_button_key))
        # get menubutton with key button_key from menubuttons
        menubutton = get_value_from_dict(button_key, menubuttons)

        # button_key = 'schllst'
        # menubutton: {'caption': 'Schools', 'href': 'school_list_url', 'visib': {'all': 'all'}}
        # logger.debug('menubutton: ' + str(menubutton))

        # lookup the href that belongs to this index in submenus_tuple
        submenu_href = menubutton.get('href', '')
        # logger.debug('submenu_href: "' + str(submenu_href) + '"')

    # ------------ get menu ------------
        svg_index = 'id_svg0' + str(menu_index)
        caption = menu.get('caption', '-')

    # add menu_key to GET parameters of menu link
        # e.g.: h_ref_reverse: /subject/?menu=mn_rep&sub=subjlst

        # Menu-items don't have their own link but use the link of selected submenu instead.
        # GET parameters are needed to mark the buttons in the menu and submenu as 'selected'

        h_ref_reverse = ''
        if submenu_href:
            h_ref_reverse = reverse_lazy(submenu_href) + '?menu=' + str(menu_key) + '&sub=' + str(button_key)

        # highlight selected menu
        if menu_key == selected_menu_key:
            style = menu.get('style_sel', '')
            fill = menu.get('fill_sel', '')
        else:
            style = menu.get('style_unsel', '')
            fill = menu.get('fill_unsel', '')

        # add menu settings to parameter 'menu_item'
        indent_left =  menu.get('indent_left', 0)
        indent_right =  menu.get('indent_right', 0)
        height =  menu.get('height', 0)
        width =  menu.get('width', 0)
        points = get_svg_arrow(width, height, indent_left, indent_right)
        pos_y =  menu.get('pos_y', 0)
        pos_x =  menu.get('pos_x', 0)
        menu_item_tag= {'svg_index': svg_index, 'caption': _(caption), 'href': h_ref_reverse,
                   'width': str(width), 'height':  str(height), 'points': points,
                    'style': style, 'x': str(pos_x), 'y': pos_y, 'fill': fill}
        menu_item_tags.append(menu_item_tag)
        # logger.debug('menu_item_tag: "' + str(menu_item_tag))

        # logger.debug('menu_key: ' + str(menu_key) + ' h_ref_reverse: ' + str(h_ref_reverse))
    # ------------ get submenus ------------
        if menu_key == selected_menu_key:
            class_navlink = 'nav-link'
            # for submenu_index, button_key in enumerate(menubuttons):
            # logger.debug('.buttons_keys_with_viewpermit: ' + str(buttons_keys_with_viewpermit) )
            # logger.debug('........... for button_key in buttons_keys:  menu_key: "' + str(menu_key) + '"')
            for button_key in buttons_keys_with_viewpermit:

                # menubutton = {'caption': 'Countries', 'href': 'country_list_url', 'viewpermit': {'insp': 'all', 'system': 'auth admin'}},
                menubutton = get_value_from_dict(button_key, menubuttons)

                sub_caption = menubutton.get('caption', '-')
                sub_href = menubutton.get('href', '')

                # add sub_index to GET parameter of submenu
                sub_h_ref_reverse = reverse_lazy(sub_href) + '?menu=' + str(menu_key) + '&sub=' + str(button_key)

                # highlight selected submenu
                class_item = class_navlink
                if button_key == selected_button_key:
                    class_item += ' active'
                submenu_tag = {'caption': _(sub_caption), 'href': sub_h_ref_reverse, 'class': class_item}

                # logger.debug('       button_key: "' + str(button_key) + '"  sub_h_ref_reverse: "' + str(sub_h_ref_reverse) + '"  class_item: "' + str(class_item) + '"')

                submenu_tags.append(submenu_tag)

    return menu_item_tags, submenu_tags


def get_buttons_keys_with_viewpermit(request, menu):
    # filter only submenus that have view_permit PR2018-12-25

    # button_keys: ('cntrlst', 'exyrlst', 'schllst', 'deplst','levllst', 'sectlst')
    button_keys = get_value_from_dict('submenu', menu)

    button_keys_with_permit = []
    for index, button_key in enumerate(button_keys):
        # check if user_role/permit may view page, skip submenu if user has no view_permit
        # get button from menubuttons
        menubutton = get_value_from_dict(button_key, menubuttons)

        if menubutton:
            # PR2018-12-23 submenus are only visible when user_role and user_permit have view_permit
            # !!! this does not block user from viewing page via url !!!

            # 'viewpermit': {'insp': 'all', 'system': 'auth admin'}},
            viewpermits = get_value_from_dict('viewpermits', menubutton)

            if has_view_permit(request, viewpermits):
                button_keys_with_permit.append (button_key)

    return tuple(button_keys_with_permit)


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
        allowed = c.PERMIT_STR_15_ALL in viewpermits
        if not allowed:
            # role_abbr: 'system'
            role_abbr = c.ROLE_DICT.get(request.user.role, '')
            if role_abbr in viewpermits:
                # logger.debug('role_abbr "' + str(role_abbr) + '" found in : "' + str(permits_view) + '"')
                permits = viewpermits.get(role_abbr, '')
                if permits:
                    # is_allowed = True when 'all' in permits
                    allowed = c.PERMIT_STR_15_ALL in permits
                    if not allowed:
                        # is_allowed = True when user_permit found in permits
                        if request.user.permits_str_tuple is not None:
                            # logger.debug('permits_str_tuple: "' + str(request.user.permits_str_tuple) + '" type: ' + str(type(request.user.permits_str_tuple)))
                            for permit in request.user.permits_str_tuple:
                                if permit in permits:
                                    # logger.debug('permit "' + str(permit) + '" found in : "' + str(permits) + '"')
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
    # get selected menu_key and selected_button_key from request.GET  # PR2018-12-25
    menu_key = None
    button_key = None
    if request.user:
        menu_key = request.GET.get('menu')  # returns None if not found
        # get button_key, but only when menu_key exists
        if menu_key:
            button_key = request.GET.get('sub')  # returns None if not found
    return menu_key, button_key


def get_setting_from_usersetting(request):  # PR2018-12-24
    # function loads usersetting 'KEY_USER_MENU_SELECTED" into setting_dict
    # in settings: first item is selected menu_item, followed by selected submenus
    # setting: {'menu': 'mn_schl', 'mn_schl': 'exyrlst', 'mn_subj': 'subjtyplst', ....}
    setting = {}
    if request.user:
        if Usersetting.objects.filter(user=request.user, key_str=c.KEY_USER_MENU_SELECTED).exists():
            usersetting = Usersetting.objects.filter(user=request.user, key_str=c.KEY_USER_MENU_SELECTED).first()
            if usersetting.char01:
                setting = json.loads(usersetting.char01)
    return setting


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
