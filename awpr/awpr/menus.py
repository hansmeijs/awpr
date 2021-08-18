from django.shortcuts import render
from django.urls import reverse_lazy

from django.utils.translation import activate, ugettext_lazy as _
from django.utils import timezone

from django.views.generic import View
#from django.contrib import messages

import json #PR2018-12-21

from accounts import views as acc_view
from awpr import constants as c
from awpr import functions as af
from awpr import settings as s

from schools import models as sch_mod
from schools import dicts as sch_dicts

import logging
logger = logging.getLogger(__name__)


height = 32
indent_none = 0
indent_10 = 10
pos_y = 18
#class_sel = 'fill:#2d4e77;stroke:#2d4e77;stroke-width:1'
#class_unsel = 'fill:#bacee6;stroke:#bacee6;stroke-width:1'

# viewpermits: 'none', 'read', 'write', 'auth', 'admin', 'all'


MENUS_ITEMS = {
    c.ROLE_128_SYSTEM: ['page_examyear', 'page_subject', 'page_school', 'page_student', 'page_studsubj', 'page_exams', 'page_grade',
                      'page_result'], #  'page_report', 'page_analysis'],
    c.ROLE_064_ADMIN: ['page_examyear', 'page_subject', 'page_school', 'page_orderlist', 'page_student', 'page_studsubj', 'page_exams', 'page_grade',
                     'page_result'],  #, 'page_report', 'page_analysis'],
    c.ROLE_032_INSP: ['page_examyear', 'page_school', 'page_student', 'page_studsubj', 'page_exams', 'page_grade', 'page_result'],  #,'page_report', 'page_analysis'],
    c.ROLE_016_COMM: ['page_examyear', 'page_school', 'page_student', 'page_grade', 'page_result'],
    c.ROLE_008_SCHOOL: ['page_examyear', 'page_student', 'page_studsubj', 'page_exams', 'page_grade', 'page_result', 'page_report']
}

MENUS_DICT = {
    'page_examyear': {'caption': _('Exam year'), 'href': 'examyears_url', 'width': 100},
    'page_school': {'caption': _('School'), 'href': 'schools_url', 'width': 90},
    'page_subject': {'caption': _('Subjects'), 'href': 'subjects_url', 'width': 100},
    'page_student': {'caption': _('Candidates'), 'href': 'students_url', 'width': 120},
    'page_studsubj': {'caption': _('Subjects'), 'href': 'studentsubjects_url', 'width': 100},
    'page_orderlist': {'caption': _('Orderlist'), 'href': 'orderlists_url', 'width': 130},
    'page_exams': {'caption': _('Exam questions'), 'href': 'exams_url', 'width': 130},
    'page_grade': {'caption': _('Grades'), 'href': 'grades_url', 'width': 120},
    'page_result': {'caption': _('Results'), 'href': 'subjects_url', 'width': 120},
    'page_report': {'caption': _('Reports'), 'href': 'subjects_url', 'width': 120},
    'page_analysis': {'caption':  _('Analysis'), 'href': 'subjects_url', 'width': 90}
}




# === MANUAL =====================================
# @method_decorator([login_required], name='dispatch')
class ManualListView(View):
    # PR2021-06-10

    def get(self, request, page, paragraph):
        logger.debug(" =====  ManualListView  =====")
        logger.debug("page: " + str(page))
        logger.debug("paragraph: " + str(paragraph))
        logger.debug("request: " + str(request))
        logger.debug("request.user: " + str(request.user))
        logger.debug("request.user.is_anonymous: " + str(request.user.is_anonymous))
        logger.debug("request.user.is_authenticated: " + str(request.user.is_authenticated))

        # 'AnonymousUser' object has no attribute 'lang'
        # -  get user_lang
        user_lang = c.LANG_DEFAULT
        if request.user.is_authenticated:
            if request.user.lang:
                user_lang = request.user.lang
        activate(user_lang)

        # - get headerbar parameters
       # page = 'page_manual'
        #param = {'list': list}
        #headerbar_param = awpr_menu.get_headerbar_param(request, page, param)
        param = {'page': page, 'paragraph': paragraph, 'lang': user_lang}

        logger.debug("param: " + str(param))

        return render(request, 'manual.html', param)


def get_headerbar_param(request, sel_page, param=None):  # PR2021-03-25
    # PR2018-05-28 set values for headerbar
    # params.get() returns an element from a dictionary, second argument is default when not found
    # this is used for arguments that are passed to headerbar
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('===== get_headerbar_param ===== ' + str(sel_page))

# - save this page in Usersetting, so at next login this page will open. Used in LoggedIn
    # PR2021-06-24 debug. Firefox gives sudenly error: 'AnonymousUser' object has no attribute 'set_usersetting_dict'
    # solved by adding 'try' statement
    if request and request.user:
        try:
            acc_view.set_usersetting_dict('sel_page', {'page': sel_page}, request)
        except Exception as e:
            logger.error('e: ' + str(e))

    param = param if param else {}
    headerbar_param = {}
    _class_bg_color = 'awp_bg_blue'

    req_user = request.user
    if req_user.is_authenticated and req_user.country and req_user.schoolbase:
        awp_messages = []

# -  get user_lang
        requsr_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
        activate(requsr_lang)

# - set background color in headerbar to purple when role is not a school
        if req_user.role in (c.ROLE_016_COMM, c.ROLE_032_INSP):
            _class_bg_color = 'awp_bg_green'
        elif req_user.role == c.ROLE_064_ADMIN:
            _class_bg_color = 'awp_bg_purple'
        elif req_user.role == c.ROLE_128_SYSTEM:
            _class_bg_color = 'awp_bg_yellow'
        else:
            _class_bg_color = 'awp_bg_blue'

        permit_list, usergroup_list = acc_view.get_userpermit_list(sel_page, req_user)

# - PR2021-06-28 debug. Add permit 'permit_userpage' if role = system,
        # to prevent you from locking out when no permits yet
        if req_user.role == c.ROLE_128_SYSTEM:
            if 'permit_userpage' not in permit_list:
                permit_list.append('permit_userpage')
            if sel_page == 'page_user':
                if 'permit_crud' not in permit_list:
                    permit_list.append('permit_crud')
                if 'permit_view' not in permit_list:
                    permit_list.append('permit_view')

        if logging_on:
            logger.debug('sel_page:           ' + str(sel_page))
            logger.debug('req_user.role:  ' + str(req_user.role))
            logger.debug('permit_list:    ' + str(permit_list))
            logger.debug('usergroup_list: ' + str(usergroup_list))

# +++ display examyear -------- PR2020-11-17 PR2020-12-24 PR2021-06-14
    # - get selected examyear from Usersetting
        no_examyears, examyear_not_published = False, False

        sel_country_abbrev, sel_country_name, country_locked, examyear_locked = None, None, False, False
        sel_examyear_code = None
        sel_examyear, sel_examyear_save, may_select_examyear = af.get_sel_examyear_instance(request)
        if sel_examyear is None:
            # PR2021-06-14 debug: not true. New user has no selected examyear yet
            # was: there is always an examyear selected, unless country has no examyears

    # - if there is no saved examyear: get latest examyear_pk of table, save it in usersettings
            sel_examyear = sch_mod.Examyear.objects.filter(
                country=req_user.country
            ).order_by('-code').first()
            if sel_examyear:
                selected_pk_dict = {c.KEY_SEL_EXAMYEAR_PK: sel_examyear.pk}
                acc_view.set_usersetting_dict(c.KEY_SELECTED_PK, selected_pk_dict, request)

        if sel_examyear is None:
            sel_examyear_str = ' <' + str(_('No exam years')) + '>'
            no_examyears = True
        else:
            # examyear.code is PositiveSmallIntegerField
            sel_examyear_code = sel_examyear.code
            sel_examyear_str = str(_('Exam year')) + ' ' + str(sel_examyear_code)
            sel_country_name = sel_examyear.country.name
# +++ do not display pages when country is locked,
            country_locked = sel_examyear.country.locked
# +++ do not display pages when examyear is not published yet,
            examyear_not_published = not sel_examyear.published
            examyear_locked = sel_examyear.locked
# +++ give warning when examyear is different from current examyear,
            # is moved to downloadsettings

# +++ display_school -------- PR2020-10-27
        # <PERMIT> PR2020-10-27
        # - requsr_school is set when user is created and never changes
        # - may_select_school is True when:
        #   - req_user is_role_comm, is_role_insp, is_role_admin or is_role_system:
        #   - selected school is stored in usersettings
        #   - otherwise sel_schoolbase_pk is equal to _requsr_schoolbase_pk
        # note: may_select_school only sets hover of school. Permissions are set in JS HandleHdrbarSelect

        # hide school in page_examyear
        display_school = param.get('display_school', True)
        sel_school = None
        sel_school_activated = False
        school_name = ''

        # used in page exams template to show school or admin mod exam form PR2021-05-22
        is_requsr_same_school = False
        is_requsr_admin_or_system = (req_user.role in (c.ROLE_064_ADMIN, c.ROLE_128_SYSTEM))

        # if sel_examyear and display_school:
        if sel_examyear:
            sel_schoolbase, save_sel_schoolbase_NIU = af.get_sel_schoolbase_instance(request)
            school_name = sel_schoolbase.code if sel_schoolbase.code else ''
    # - get school from sel_schoolbase and sel_examyear
            sel_school = sch_mod.School.objects.get_or_none(
                base=sel_schoolbase,
                examyear=sel_examyear)

            if sel_school:
                school_name += ' ' + sel_school.name
                sel_school_activated = sel_school.activated
                is_requsr_same_school = (req_user.role == c.ROLE_008_SCHOOL and
                                         req_user.schoolbase.pk == sel_schoolbase.pk)
            else:
                school_name += ' <' + str(_('School not found in this exam year')) + '>'

        if logging_on:
            logger.debug('sel_school: ' + str(sel_school))
            logger.debug('sel_school_activated: ' + str(sel_school_activated))

# +++ display department -------- PR2029-10-27 PR2020-11-17

# PR2018-08-24 select department PR2020-10-13 PR2021-04-25
        department_name = ''
        display_department = param.get('display_department', True)
        if display_department:
            sel_depbase, sel_depbase_save, allowed_depbases = af.get_sel_depbase_instance(sel_school, request)

            sel_department = sch_mod.Department.objects.get_or_none(base=sel_depbase, examyear=sel_examyear)
            if sel_department is None:
                department_name = '<' + str(_('No department')) + '>'
            else:
                department_name = sel_depbase.code

        if logging_on:
            logger.debug('department_name: ' + str(department_name))
            logger.debug('display_department: ' + str(display_department))

# ------- set menu_items -------- PR2018-12-21
        # get selected menu_key and selected_button_key from request.GET, settings or default, check viewpermit
        menu_items = set_menu_items(sel_page, _class_bg_color, request)

# ------- set no_access -------- PR2021-04-27 PR2021-07-03
        no_access = ('permit_view' not in permit_list and 'permit_crud' not in permit_list)

# ------- set message -------- PR2021-03-25
        if no_examyears:
            no_access_message = _("There are no exam years yet.")
            awp_messages.append(no_access_message)
        elif country_locked:
            no_access_message = _("%(country)s has no license to use AWP-online.") % \
                                                 {'country': sel_country_name}
            awp_messages.append(no_access_message)
        elif examyear_locked:
            no_access_message = _("Exam year %(ey)s is locked. You cannot make changes.") % \
                                                 {'ey': str(sel_examyear.code)}
            awp_messages.append(no_access_message)
        elif examyear_not_published:
            # get latest name of ETE / Div of Exam from schools, if not found: default = MinOnd
            school_admin = sch_mod.School.objects.filter(
                base__country=req_user.country,
                base__defaultrole=c.ROLE_064_ADMIN
            ).order_by('-examyear', '-pk').first()

            admin_name = None
            if school_admin:
                admin_name = school_admin.name
                if admin_name and school_admin.article:
                    admin_name = ' '.join((school_admin.article.capitalize(), admin_name))
            if not admin_name:
                admin_name = _('The Ministry of Education')
            no_access_message = _("%(admin)s has not yet published examyear %(exyr)s. You cannot enter data yet.") % \
                                                 {'admin': admin_name, 'exyr': str(sel_examyear_code)}
            awp_messages.append(no_access_message)

        elif not sel_school_activated:
            # block certain pages when not sel_school_activated
            if sel_page in ('page_student', 'page_studsubj', 'page_grade'):
                no_access_message = _("You must first activate the examyear before you can enter data. Go to the page 'School' and activate the examyear.")
                awp_messages.append(no_access_message)

        headerbar_param = {
            'no_access': no_access,
            'examyear_locked': examyear_locked,
            'is_requsr_same_school': is_requsr_same_school,
            'is_requsr_admin_or_system': is_requsr_admin_or_system,
            'examyear_code': sel_examyear_str,
            'display_school': display_school, 'school': school_name,
            'display_department': display_department, 'department': department_name,
            'menu_items': menu_items,
            'awp_messages': awp_messages,
            'permit_list': permit_list,
            'page': sel_page[5:],
            'paragraph': 'intro'
        }
        if param:
            headerbar_param.update(param)
    headerbar_param['class_bg_color'] = _class_bg_color
    #if logging_on:
        #logger.debug('headerbar_param: ' + str(headerbar_param))

    return headerbar_param


def get_saved_page_url(sel_page, request):  # PR2018-12-25 PR2020-10-22  PR2020-12-23
    #logger.debug('------------ get_saved_page_url ----------------')
    #logger.debug('sel_page: ' + str(sel_page))
    # only called by schools.views.Loggedin,
    # retrieves submenu_href for: return HttpResponseRedirect(reverse_lazy(saved_href))
    lookup_page = sel_page if sel_page else 'page_examyear'
    #logger.debug('lookup_page: ' + str(lookup_page))

    page_href = None
    menu = MENUS_DICT.get(lookup_page)
    if menu:
        page_href = menu.get('href')
    if page_href is None:
        page_href = 'home_url'

    #logger.debug('page_href: ' + str(page_href))
    return page_href

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++

def set_menu_items(sel_page, _class_bg_color, request):
    # function is called by get_headerbar_param, creates template tags menu_items and submenus
    # setting: {'menu': 'mn_schl', 'mn_schl': 'schllst'}
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('===== set_menu_items ===== ')
        logger.debug('sel_page: ' + str(sel_page))

# - reset language
    user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
    activate(user_lang)

    if logging_on:
        logger.debug('user_lang: ' + str(user_lang))
        logger.debug('Subject: ' + str(_('Subject')))

    menu_item_tags = []

    # list of menuitems to be shown in page
    menu_items = MENUS_ITEMS.get(request.user.role)

    # loop through all menus in menus, to retrieve href from all menu-buttons
    # from https://treyhunner.com/2016/04/how-to-loop-with-indexes-in-python/
    for menu_index, key_str in enumerate(menu_items):
        menu_item = MENUS_DICT[key_str]

        # lookup the href that belongs to this index in submenus_tuple
        # function gets first href in href_string, when insp or admin it gets the second item
        menu_href = menu_item.get('href')

    # ------------ get menu ------------
        caption = menu_item.get('caption', '-')
        if logging_on:
            logger.debug('caption: ' + str(caption))


        h_ref_reverse = ''
        if menu_href:
           h_ref_reverse = reverse_lazy(menu_href)

        # highlight selected menu
        if key_str == sel_page:
            if _class_bg_color == 'awp_bg_purple':
                polygon_class = 'menu_polygon_selected_purple'
            elif _class_bg_color == 'awp_bg_green':
                polygon_class = 'menu_polygon_selected_green'
            elif _class_bg_color == 'awp_bg_yellow':
                polygon_class = 'menu_polygon_selected_yellow'
            else:
                polygon_class = 'menu_polygon_selected_blue'
            text_fill = '#EDF2F8'
        else:
            polygon_class = 'menu_polygon_unselected'
            text_fill = '#212529'
        #logger.debug('polygon_class: ' + str(polygon_class))
        #logger.debug('caption: ' + str(caption))

        # add menu settings to parameter 'menu_item'
        width = menu_item.get('width', 0)
        indent_left = indent_none if menu_index == 0 else indent_10
        indent_right = indent_none if menu_index == len(menu_items) - 1 else indent_10
        points = get_svg_arrow(width, height, indent_left, indent_right)
        pos_x = width / 2
        menu_item_tag= {'caption': caption, 'href': h_ref_reverse,
                   'width': str(width), 'height':  str(height), 'points': points,
                    'class': polygon_class,
                    'x': str(pos_x), 'y': pos_y, 'fill': text_fill}
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
        allowed = False  # c.GROUP_STR_15_ALL in viewpermits
        if not allowed:
            # role_abbr: 'system'
            role_abbr = c.ROLE_DICT.get(request.user.role, '')
            if role_abbr in viewpermits:
                #logger.debug('role_abbr "' + str(role_abbr) + '" found in : "' + str(permits_view) + '"')
                permits = viewpermits.get(role_abbr, '')
                if permits:
                    # is_allowed = True when 'all' in permits
                    allowed =  False  # c.GROUP_STR_15_ALL in permits
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
                sel_depbase_instance = sch_mod.Departmentbase.objects.get_or_none(pk=sel_depbase_pk)
            elif allowed_dep_count > 1:
# - get saved sel_depbase: if multiple exist in depbase_pk_list
                saved_sel_depbase_instance = af.get_saved_sel_depbase_instance(request)
    # check if saved_sel_depbase is in depbase_pk_list
                if saved_sel_depbase_instance and saved_sel_depbase_instance.pk in depbase_pk_list:
                    sel_depbase_instance = saved_sel_depbase_instance
            may_select_dep = (allowed_dep_count > 1)

    return depbase_pk_list, may_select_dep, sel_depbase_instance
# --- end of get_depbase_list ---
