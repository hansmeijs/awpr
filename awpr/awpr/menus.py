import gettext

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse_lazy

#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, gettext_lazy as _
from django.utils.decorators import method_decorator

from django.views.generic import View

from accounts import views as acc_view
from accounts import  permits as acc_prm
from awpr import constants as c
from awpr import functions as af
from awpr import settings as s

from schools import models as sch_mod

import logging
logger = logging.getLogger(__name__)

height = 32
indent_none = 0
indent_10 = 10
pos_y = 18
#class_sel = 'fill:#2d4e77;stroke:#2d4e77;stroke-width:1'
#class_unsel = 'fill:#bacee6;stroke:#bacee6;stroke-width:1'

# viewpermits: 'none', 'read', 'write', 'auth', 'admin', 'all'


MENUS_BUTTONS = {
    c.ROLE_128_SYSTEM: ['page_examyear', 'page_subject', 'page_school', 'page_orderlist', 'page_student',
                         'page_exams', 'page_studsubj', 'page_wolf', 'page_grade',
                      'page_result', 'page_corrector', 'page_archive', 'page_exampaper'], #  'page_report', 'page_analysis'],
    c.ROLE_064_ADMIN: ['page_examyear', 'page_subject', 'page_school', 'page_orderlist', # 'page_student',
                       'page_exams', 'pageF_studsubj', 'page_grade', 'page_secretexam',
                     'page_result', 'page_archive', 'page_exampaper'],  #, 'page_corrector', 'page_report', 'page_analysis'],
    c.ROLE_032_INSP: ['page_examyear', 'page_subject', 'page_school', 'page_orderlist', 'page_student', 'page_studsubj',
                      'page_exams', 'page_grade', 'page_result', 'page_archive', 'page_exampaper'],  #,'page_report', 'page_analysis'],
    # PR2024-06-10 page_school is confusing for second correctors. They try to click tn School instead of the titlebar
    c.ROLE_016_CORR: ['page_student', 'page_wolf', 'page_grade', 'page_result', 'page_corrector', 'page_archive', 'page_exampaper'],
    c.ROLE_008_SCHOOL: ['page_student', 'page_studsubj', 'page_wolf', 'page_grade', 'page_result', 'page_corrector', 'page_archive', 'page_exampaper'] # 'page_report',
}

MENUS_DICT = {
    'page_examyear': {'caption': _('Exam year'), 'href': 'examyears_url', 'width': 100},
    'page_school': {'caption': _('School'), 'href': 'schools_url', 'width': 90},
    'page_subject': {'caption': _('Subject schemes'), 'href': 'subjects_url', 'width': 120},
    'page_student': {'caption': _('Candidates'), 'href': 'students_url', 'width': 120},
    'page_studsubj': {'caption': _('Subjects'), 'href': 'studentsubjects_url', 'width': 100},
    'page_orderlist': {'caption': _('Orderlist'), 'href': 'orderlists_url', 'width': 120},
    'page_exams': {'caption': _('Exams'), 'href': 'exams_url', 'width': 100},
    'page_wolf': {'caption': _('Wolf'), 'href': 'wolf_url', 'width': 100},
    'page_grade': {'caption': _('Grades'), 'href': 'grades_url', 'width': 100},
    'page_secretexam': {'caption': _('Designated exams'), 'href': 'secretexam_url', 'width': 180},
    'page_result': {'caption': _('Results'), 'href': 'results_url', 'width': 100},
    'page_report': {'caption': _('Reports'), 'href': 'url_archive', 'width': 120},
    'page_corrector': {'caption': _('Second correctors'), 'href': 'url_corrector', 'width': 150},
    'page_archive': {'caption': _('Archive'), 'href': 'url_archive', 'width': 90},
    'page_exampaper': {'caption': _('Publications'), 'href': 'url_exampapers', 'width': 150},
    'page_analysis': {'caption':  _('Analysis'), 'href': 'url_archive', 'width': 90}
}


# === MANUAL =====================================
# @method_decorator([login_required], name='dispatch')
class ManualListView(View):
    # PR2021-06-10

    def get(self, request, page, paragraph):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
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
        # headerbar_param = awpr_menu.get_headerbar_param(request, page, param)
        param = {'page': page, 'paragraph': paragraph, 'lang': user_lang}

        if logging_on:
            logger.debug("param: " + str(param))

        return render(request, 'manual.html', param)


def get_headerbar_param(request, sel_page, param=None):
    # PR2018-05-28 PR2021-03-25 PR2023-01-08 PR2023-04-12
    # set values for headerbar
    # params.get() returns an element from a dictionary, second argument is default when not found
    # this is used for arguments that are passed to headerbar

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('')
        logger.debug('===== get_headerbar_param ===== ')
        logger.debug('    sel_page: ' + str(sel_page))

# - save this page in Usersetting, so at next login this page will open. Used in LoggedIn
    # PR2021-06-24 debug. Firefox gives sudenly error: 'AnonymousUser' object has no attribute 'set_usersetting_dict'
    # solved by adding 'try' statement
    if request and request.user:
        try:
            acc_view.set_usersetting_dict(
                key_str='sel_page',
                setting_dict={'page': sel_page},
                request=request
            )
        except Exception as e:
            logger.error('e: ' + str(e))

    # PR2024-06-14 move parameter param to this function
    hide_auth_in_hdr = False
    if not param:
        if sel_page == 'page_corrector':
            display_school = request.user.role == c.ROLE_008_SCHOOL
            param = {'display_school': display_school, 'display_department': False}
        elif sel_page == 'page_secretexam':
            param = {'display_school': False, 'display_department': True}
        elif sel_page == 'page_user':
            # PR2024-06-27 show requser orgainzation instead of selected school, hide functions
            # must add sel_page == 'page_user' also in h_UpdateHeaderBar
            # hide_auth_in_hdr = True
            # PR2018-05-31 debug: self.role = False when value = 0!!! Use is not None instead
            show_btn_userpermit = request.user.role is not None and request.user.is_role_system
            param = {'show_btn_userpermit': show_btn_userpermit, 'display_school': True, 'display_department': False}


    param = param if param else {}

    headerbar_param = {}
    _class_bg_color = 'awp_bg_blue'
    _class_has_mail = 'envelope_0_0'

    req_usr = request.user
    if req_usr.is_authenticated and req_usr.country and req_usr.schoolbase:

# -  get user_lang
        requsr_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
        activate(requsr_lang)

        country_locked, examyear_locked, no_examyears, examyear_not_published = False, False, False, False
        sel_country_abbrev, sel_country_name, sel_examyear_code = None, None, None
        no_practexam, sr_allowed, no_centralexam, no_thirdperiod = False, False, False, False

# +++ get selected examyear
    # PR2023-01-06 get examyear first, it is needed in permit_list

    # - get selected examyear from Usersetting
        # - get new examyear_pk from request_setting,
        # - if None: get saved_examyear_pk from Usersetting
        # - if None: get today's examyear
        # - if None: get latest examyear_int of table
        sel_examyear_instance, sel_examyear_save, multiple_examyears_exist = af.get_sel_examyear_with_default(request)
        if logging_on:
            logger.debug('    sel_examyear_instance: ' + str(sel_examyear_instance))
            logger.debug('    multiple_examyears_exist: ' + str(multiple_examyears_exist))

    # - if sel_examyear_instance is not saved yet: save it in usersettings
        if sel_examyear_instance and sel_examyear_save:
            sel_examyear_pk_dict = {c.KEY_SEL_EXAMYEAR_PK: sel_examyear_instance.pk}
            acc_view.set_usersetting_dict(c.KEY_SELECTED_PK, sel_examyear_pk_dict, request)

# - set background color in headerbar
        if req_usr.role == c.ROLE_032_INSP:
            _class_bg_color = 'awp_bg_green'
        elif req_usr.role == c.ROLE_016_CORR:
            _class_bg_color = 'awp_bg_corr_green'
        elif req_usr.role == c.ROLE_064_ADMIN:
            _class_bg_color = 'awp_bg_purple'
        elif req_usr.role == c.ROLE_128_SYSTEM:
            _class_bg_color = 'awp_bg_yellow'
        else:
            _class_bg_color = 'awp_bg_blue'

# -  get permit_list from userallowed
        #PR2023-02-13 not in use, usergroups are displayed in moduserallowedsections
        permit_list, usergroup_list, requsr_allowed_sections_dict, requsr_allowed_clusters_arr = \
            acc_prm.get_requsr_permitlist_usergroups_allowedsections_allowedclusters(request, sel_page)

# - PR2021-06-28 debug. Add permit 'permit_userpage' if role = system,
        # to prevent you from locking out when no permits yet
        if req_usr.role == c.ROLE_128_SYSTEM:
            if 'permit_userpage' not in permit_list:
                permit_list.append('permit_userpage')
            if sel_page == 'page_user':
                if 'permit_crud' not in permit_list:
                    permit_list.append('permit_crud')
                if 'permit_view' not in permit_list:
                    permit_list.append('permit_view')

        if logging_on:
            logger.debug('    sel_page:       ' + str(sel_page))
            logger.debug('    req_usr.role:   ' + str(req_usr.role))
            logger.debug('    permit_list:    ' + str(permit_list))
            logger.debug('    usergroup_list: ' + str(usergroup_list))

# +++ display examyear -------- PR2020-11-17 PR2020-12-24 PR2021-06-14
        if sel_examyear_instance is None:
            sel_examyear_str = ' <' + str(_('No exam years')) + '>'
            no_examyears = True
        else:
            # examyear.code is PositiveSmallIntegerField
            sel_examyear_code = sel_examyear_instance.code
            sel_examyear_str = str(_('Exam year')) + ' ' + str(sel_examyear_instance)
            sel_country_name = sel_examyear_instance.country.name

# +++ do not display pages when examyear is not published yet,
            examyear_not_published = not sel_examyear_instance.published

    # - show padlock in headerbar when examyear_locked
            examyear_locked = sel_examyear_instance.locked
    # - used in page grades: set tab buttons practexam, sr_allowed, centralexam, thirdperiod
            no_practexam = sel_examyear_instance.no_practexam
            sr_allowed = sel_examyear_instance.sr_allowed
            no_centralexam = sel_examyear_instance.no_centralexam
            no_thirdperiod = sel_examyear_instance.no_thirdperiod

        if logging_on:
            logger.debug(' -- sel_examyear_instance: ' + str(sel_examyear_instance))

            logger.debug('    country_locked:   ' + str(country_locked))
            logger.debug('    examyear_not_published:   ' + str(examyear_not_published))
            logger.debug('    examyear_locked:   ' + str(examyear_locked))

            logger.debug('    no_practexam:   ' + str(no_practexam))
            logger.debug('    sr_allowed:     ' + str(sr_allowed))
            logger.debug('    no_centralexam: ' + str(no_centralexam))
            logger.debug('    no_thirdperiod: ' + str(no_thirdperiod))

# +++ give warning when examyear is different from current examyear,
            # is moved to downloadsettings

# +++ display_school -------- PR2020-10-27
        # <PERMIT> PR2020-10-27
        # - requsr_school is set when user is created and never changes
        # - may_select_school is True when:
        #   - req_usr is_role_corr, is_role_insp, is_role_admin or is_role_system:
        #   - selected school is stored in usersettings
        #   - otherwise sel_schoolbase_pk is equal to _requsr_schoolbase_pk
        # note: may_select_school only sets hover of school. Permissions are set in JS HandleHdrbarSelect

        school_name = ''

        # used in page exams template to show school or admin mod exam form PR2021-05-22
        is_requsr_same_school = False
        is_requsr_admin = req_usr.role == c.ROLE_064_ADMIN

        # when display_requsrschool = True the organization of the user is shown, not the selected school
        # Note: this must also be set in h_UpdateHeaderBar
        display_requsrschool = sel_page in ('page_user', 'page_subject', 'page_examyear',
                                            'page_school', 'page_corrector',
                                            'page_exampaper', 'page_archive', 'page_orderlist')


        if logging_on:
            logger.debug('    requsr_allowed_sections_dict: ' + str(requsr_allowed_sections_dict))
            logger.debug('    display_requsrschool: ' + str(display_requsrschool))
            logger.debug('    req_usr.schoolbase: ' + str(req_usr.schoolbase))

# - get sel_schoolbase_instance
        if display_requsrschool:
            sel_schoolbase_instance = req_usr.schoolbase
        else:
            sel_schoolbase_instance, sel_schoolbase_tobesaved_NIU = \
                acc_view.get_sel_schoolbase_instance(
                    request=request,
                    request_item_schoolbase_pk=None,
                    allowed_sections_dict=requsr_allowed_sections_dict
                )
        sel_school_instance = None

# if sel_examyear and display_school:
        if sel_examyear_instance:
            school_name = sel_schoolbase_instance.code if sel_schoolbase_instance.code else ''

            if logging_on:
                logger.debug('    school_code: ' + str(school_name))
    # - get school from sel_schoolbase and sel_examyear_instance
            sel_school_instance = sch_mod.School.objects.get_or_none(
                base=sel_schoolbase_instance,
                examyear=sel_examyear_instance)

            if sel_school_instance:
                school_name += ' ' + sel_school_instance.name
                is_requsr_same_school = (req_usr.role == c.ROLE_008_SCHOOL and
                                         req_usr.schoolbase.pk == sel_schoolbase_instance.pk)
            else:
                school_name += ' <' + str(_('School not found in this exam year')) + '>'

    # - check if there are any unread mailbox items
            if af.has_unread_mailbox_items(sel_examyear_instance, req_usr):
                _class_has_mail = 'envelope_0_2'

        if logging_on:
            logger.debug('  ..sel_school_instance: ' + str(sel_school_instance))

# +++ display functions -------- PR2024-06-13
        activate(requsr_lang)
    # - get selected_pk_dict from usersettings
        selected_pk_dict = acc_prm.get_usersetting_dict(c.KEY_SELECTED_PK, request)

    # - get requsr_authindex_list from usergroup_list
        requsr_authindex_list = []

        if usergroup_list:
            for auth_index in (1, 2, 3, 4):
                usergroup = 'auth' + str(auth_index)
                if usergroup in usergroup_list:
                    requsr_authindex_list.append(auth_index)

    # - get saved_auth_index from usersetting
        saved_auth_index = selected_pk_dict.get(c.KEY_SEL_AUTH_INDEX)

    # - get sel_auth_index
        sel_auth_index = None
        if saved_auth_index in requsr_authindex_list:
            sel_auth_index = saved_auth_index
        elif requsr_authindex_list:
            sel_auth_index = requsr_authindex_list[0]

    # - save sel_auth_index in settings if it has changed
        if sel_auth_index != saved_auth_index:
            selected_pk_dict[c.KEY_SEL_AUTH_INDEX] = sel_auth_index
            acc_view.set_usersetting_dict(c.KEY_SELECTED_PK, selected_pk_dict, request)

        sel_auth = 'auth' + str(sel_auth_index) if sel_auth_index else None
        if logging_on:
            logger.debug('    selected_pk_dict:       ' + str(selected_pk_dict))
            logger.debug('    sel_auth_index:       ' + str(sel_auth_index))
            logger.debug('    sel_auth:       ' + str(sel_auth))


        sel_function = '---'

        # Note: display functions also set by h_UpdateHeaderBar


        display_auth = {'functions': 'display_hide' if hide_auth_in_hdr or not requsr_authindex_list else ''}
        sel_function = '---'
        for auth_index in (1, 2, 3, 4):
            found = auth_index in requsr_authindex_list
            is_selected = found and auth_index == sel_auth_index
            if is_selected:
                sel_function = c.get_auth_caption(auth_index)

            class_bg_color = 'display_hide' if not found else 'tsa_tr_selected' if is_selected else ''
            display_auth['auth' + str(auth_index)] = class_bg_color
        display_auth['sel_function'] = sel_function

        if logging_on:
            logger.debug('    display_auth: ' + str(display_auth))
            logger.debug('    sel_function: ' + str(sel_function))

# +++ display department -------- PR2029-10-27 PR2020-11-17

# PR2018-08-24 select department PR2020-10-13 PR2021-04-25
        department_name = ''
        display_department = param.get('display_department', True)
        display_department = not display_requsrschool
        if display_department:
            # - get allowed_schoolbase_dict
            allowed_schoolbase_dict, allowed_depbases_pk_arr = \
                acc_prm.get_userallowed_schoolbase_dict_depbases_pk_arr(
                    userallowed_sections_dict=requsr_allowed_sections_dict,
                sel_schoolbase_pk=sel_schoolbase_instance.pk if sel_schoolbase_instance else None
                )

            if logging_on:
                logger.debug('  ..allowed_schoolbase_dict: ' + str(allowed_schoolbase_dict))
                logger.debug('  ..allowed_depbases_pk_arr: ' + str(allowed_depbases_pk_arr))

            # - get sel_depbase_instance
            sel_depbase_instance, sel_depbase_tobesavedNIU, allowed_depbases_arr = \
                acc_view.get_sel_depbase_instance(
                    sel_school_instance=sel_school_instance,
                    page=sel_page,
                    request=request,
                    allowed_schoolbase_dict=allowed_schoolbase_dict,
                    selected_pk_dict=selected_pk_dict
                )

            sel_department = sch_mod.Department.objects.get_or_none(base=sel_depbase_instance, examyear=sel_examyear_instance)
            if sel_department is None:
                department_name = '<' + str(_('No department')) + '>'
            else:
                department_name = sel_depbase_instance.code

        if logging_on:
            logger.debug('    department_name: ' + str(department_name))
            logger.debug('    display_department: ' + str(display_department))

# ----- set menu_buttons -------- PR2018-12-21
        # get selected menu_key and selected_button_key from request.GET, settings or default, check viewpermit
        menu_buttons = set_menu_buttons(sel_page, _class_bg_color, usergroup_list, request)

# ------- set no_access -------- PR2021-04-27 PR2021-07-03 PR2022-05-30
        #  PR2022-05-30 only give no_access when user has no usergroups (commissioner could not log in
        # was no_access = ('permit_view' not in permit_list and 'permit_crud' not in permit_list)

#  PR2022-06-06 back to previous one, to be able to block acces to result page when user is not chairperson of secretary
        # was: no_access = (not permit_list)

        may_receive_messages = 'msgreceive' in usergroup_list  # PR2023-04-05

        # PR2023-04-11 debug. Friedeman Sg Otrobanda: user cannot access page 'No permit to viw page.
        # cause: had no permit 'view'
        # better turn off permit 'View'. User can be made inactive to block him
        # was:
        #if not ('permit_view' in permit_list or 'permit_crud' in permit_list):
        #    no_access = True

        country_locked = sel_examyear_instance.country.locked if sel_examyear_instance else True

# PE2023-04-17 to prevent - for instance - access to page exam when role = school:
# but all users have acces to page page_exampaper
        no_access = False
        if sel_page != 'page_exampaper':

            if 'permit_view' in permit_list or \
                'permit_crud' in permit_list or \
                'permit_auth1' in permit_list or \
                'permit_auth2' in permit_list or \
                'permit_auth3' in permit_list or \
                'permit_auth4' in permit_list or \
                'permit_admin' in permit_list or \
                'permit_admin' in permit_list:
                pass
            else:
                no_access = True

    # +++ display pages when country is locked,
            if country_locked:
                pass

            elif sel_page == 'page_archive' and 'archive' not in usergroup_list:
                no_access = True
            elif sel_page == 'page_mailbox' and not may_receive_messages:
                no_access = True

        if logging_on:
            logger.debug('  ..sel_page: ' + str(sel_page))
            logger.debug('  ..permit_list: ' + str(permit_list))
            logger.debug('  ..no_access: ' + str(no_access))

# ------- set message -------- PR2021-03-25
        # messages block access to the page.
        # warnings must be given via DatalistDownloadView

        # PR2023-04-11 debug. when examyear is locked user must be able to view pages. Give message in downlaod instead
        # elif examyear_locked:
        #    # this is a warning, dont block access when examyear_locked
        #    no_access_message = _("Exam year %(ey)s is locked. You cannot make changes.") % {'ey': str(sel_examyear_instance.code)}
        #    messages.append(no_access_message)


        messages = []
        if no_examyears:
            no_access_message = _("There are no exam years yet.")
            messages.append(no_access_message)

        elif country_locked:
            no_access_message = _("%(country)s has no license yet to use AWP-online this exam year.") % \
                                                 {'country': sel_country_name}
            messages.append(no_access_message)

        elif examyear_not_published:
            # get latest name of ETE / Div of Exam from schools, if not found: default = MinOnd
            school_admin = sch_mod.School.objects.filter(
                base__country=req_usr.country,
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
            messages.append(no_access_message)

            if logging_on:
                logger.debug('  ..messages: ' + str(messages))

# - sentr_src contains link for Sentry awp_js PR2021-09-19
        sentry_src = s.SENTRY_SRC

# - make background red when testsite PR2022-01-11
        class_bg_testsite = "tsa_tr_error" if s.IS_TESTSITE else ""
        class_bg_testsite = "test_color" if s.IS_TESTSITE else ""

        headerbar_param = {
            'no_access': no_access,
            'examyear_locked': examyear_locked,
            'is_requsr_same_school': is_requsr_same_school,
            'is_requsr_admin': is_requsr_admin,
            'examyear_code': sel_examyear_str,
            'display_requsrschool': display_requsrschool,
            'school': school_name,
            'display_department': display_department,
            'department': department_name,
            'menu_buttons': menu_buttons,
            'messages': messages,
            'msgreceive': may_receive_messages,
            'permit_list': permit_list,

            'display_auth': display_auth,
            'sel_function': sel_function,
            'page': sel_page[5:],
            'paragraph': 'intro',
            'no_practexam': no_practexam,
            'sr_allowed': sr_allowed,
            'no_centralexam': no_centralexam,
            'no_thirdperiod': no_thirdperiod,
            'sentry_src': sentry_src,
            'class_bg_testsite': class_bg_testsite
        }
        if param:
            headerbar_param.update(param)
    headerbar_param['class_bg_color'] = _class_bg_color

    headerbar_param['class_has_mail'] = _class_has_mail
    if logging_on:
        logger.debug('headerbar_param: ' + str(headerbar_param))

    return headerbar_param
# - end of get_headerbar_param


def get_saved_page_url(sel_page, request):  # PR2018-12-25 PR2020-10-22  PR2020-12-23 PR22021-12-03
    #logger.debug('------------ get_saved_page_url ----------------')
    #logger.debug('sel_page: ' + str(sel_page))
    # only called by schools.views.Loggedin,
    # retrieves submenu_href for: return HttpResponseRedirect(reverse_lazy(saved_href))
    lookup_page = sel_page if sel_page else 'page_student'
    #logger.debug('lookup_page: ' + str(lookup_page))

    page_href = None
    menu = MENUS_DICT.get(lookup_page)
    if menu:
        page_href = menu.get('href')
    if page_href is None:
        page_href = 'home_url'

    #logger.debug('page_href: ' + str(page_href))
    return page_href


def set_menu_buttons(sel_page, _class_bg_color, usergroup_list, request):
    # function is called by get_headerbar_param, creates template tags menu_buttons and submenus
    # setting: {'menu': 'mn_schl', 'mn_schl': 'schllst'}
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('===== set_menu_buttons ===== ')
        logger.debug('    sel_page: ' + str(sel_page))

    def show_page_btn(key_str):
        # PR2023-02-24 show page button 'Second correctors' only when:
        # - role is corrector or admin
        #  - or if role c.ROLE_008_SCHOOL and user has usergroup chairperson, secretary or corrector (auth1, auth2, auth4)
        if key_str == 'page_exampaper':
            show_btn = False
        elif key_str == 'page_corrector':
            show_btn = False
            if request.user.role == c.ROLE_016_CORR or request.user.role == c.ROLE_064_ADMIN:
                show_btn = True

            elif request.user.role == c.ROLE_008_SCHOOL:
                if 'auth1' in usergroup_list or 'auth2' in usergroup_list or 'auth4' in usergroup_list:
                    show_btn = True

        #PR2023-04-05 show page button 'Archive' only when user has usergroup 'archive'
        elif key_str == 'page_archive':
            show_btn = 'archive' in usergroup_list
        else:
            show_btn = True
        return show_btn

# - reset language
    user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
    activate(user_lang)

    if logging_on:
        logger.debug('    user_lang: ' + str(user_lang))

    menu_item_tags = []

    # list of menuitems to be shown in page

    # - hide page button 'Second correctors' when user has not proper role / usergroup:
    # - hide page 'archive' when not in usergroups
    # create list necessary to get the right indent_right PR2023-04-05
    menu_buttons = []
    for key_str in MENUS_BUTTONS.get(request.user.role):
        if show_page_btn(key_str):
            menu_buttons.append(key_str)
    menu_buttons_count =  len(menu_buttons)
    last_index = menu_buttons_count - 1 if menu_buttons_count else 0

    # loop through all menus in menus, to retrieve href from all menu-buttons
    # from https://treyhunner.com/2016/04/how-to-loop-with-indexes-in-python/
    for menu_index, key_str in enumerate(menu_buttons):
        if key_str in MENUS_DICT:
            menu_item = MENUS_DICT[key_str]

            # lookup the href that belongs to this index in submenus_tuple
            # function gets first href in href_string, when insp or admin it gets the second item
            menu_href = menu_item.get('href')

        # ------------ get menu ------------
            caption = menu_item.get('caption', '-')
            if logging_on:
                logger.debug('caption: ' + str(caption))

            # PR2023-06-15 diplay 'Compensation'  when corrector role opens page
            if key_str == 'page_corrector':
                caption = _('Second correctors')  if request.user.role == c.ROLE_008_SCHOOL else _('Compensation')

            if logging_on:
                logger.debug('    key_str: ' + str(key_str))
                logger.debug('    menu_item: ' + str(menu_item))
                logger.debug('    caption: ' + str(caption))
                logger.debug('    caption: ' + str(caption))

            h_ref_reverse = ''
            if menu_href:
               h_ref_reverse = reverse_lazy(menu_href)

            # highlight selected menu
            if key_str == sel_page:
                if _class_bg_color == 'awp_bg_purple':
                    polygon_class = 'menu_polygon_selected_purple'
                elif _class_bg_color == 'awp_bg_green':
                    polygon_class = 'menu_polygon_selected_green'
                elif _class_bg_color == 'awp_bg_corr_green':
                    polygon_class = 'menu_polygon_selected_corr_green'

                elif _class_bg_color == 'awp_bg_yellow':
                    polygon_class = 'menu_polygon_selected_yellow'
                else:
                    polygon_class = 'menu_polygon_selected_blue'
                text_fill = '#EDF2F8'
            else:
                polygon_class = 'menu_polygon_unselected'
                text_fill = '#212529'


# add menu settings to parameter 'menu_item'
            width = menu_item.get('width', 0)
            indent_left = indent_none if menu_index == 0 else indent_10
            indent_right = indent_none if menu_index == last_index else indent_10

            points = get_svg_arrow(width, height, indent_left, indent_right)
            pos_x = width / 2
            menu_item_tag= {'caption': caption, 'href': h_ref_reverse,
                       'width': str(width), 'height':  str(height), 'points': points,
                        'class': polygon_class,
                        'x': str(pos_x), 'y': pos_y, 'fill': text_fill}
            menu_item_tags.append(menu_item_tag)

    if logging_on:
        logger.debug('    menu_item_tags: ' + str(menu_item_tags))

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


def get_menu_keys_from_GET_NIU(request):
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

    req_usr = request.user
    if req_usr and requsr_school:
        allowed_dep_count = 0
# - if school does not have any departments: sel_depbase_instance = None
        if requsr_school.depbases:
# - if requsr_allowed_depbase_list is empty: add all school_depbases to list
            if req_usr.allowed_depbases is None:
                depbase_pk_list = requsr_school.depbases
                allowed_dep_count = len(depbase_pk_list)
            else:
# - if requsr_allowed_depbase_list has values:
                # iterate through departments of this school,
                # add only the ones in requsr_allowed_depbase_list
                for school_depbase_pk in requsr_school.depbases:
    # - add_to_list if school_depbase is in requsr_allowed_depbase_list
                    if school_depbase_pk in req_usr.allowed_depbases:
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


