# PR2018-04-14
from django.contrib.auth.decorators import login_required # PR2018-04-01
from django.core.files import File
from django.core.mail import EmailMessage
from mimetypes import guess_type
from os.path import basename

from django.core.serializers.json import DjangoJSONEncoder
from django.template.loader import render_to_string
from django.utils.functional import Promise
from django.utils.encoding import force_text

from django.db import connection
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseRedirect

from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import View

from accounts import views as acc_view
from accounts import models as acc_mod

from awpr import settings as s
from awpr import excel as awpr_excel
from awpr import functions as af
from awpr import constants as c
from awpr import validators as av
from awpr import menus as awpr_menu
from awpr import downloads as dl

from schools import functions as sf
from schools import dicts as sch_dicts
from schools import models as sch_mod
from students import models as stud_mod
from subjects import models as subj_mod
from subjects import views as subj_view

import xlsxwriter
import tempfile
import json
import logging
logger = logging.getLogger(__name__)

class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)

# PR2018-05-06
from django.utils.translation import activate, pgettext_lazy, ugettext_lazy as _


def home(request):
    # PR2018-04-29
    # function get_headerbar_param sets:
    # - activates request.user.language
    # - display/select schoolyear, schoolyear list, color red when not this schoolyear
    # - display/select school, school list
    # - display user dropdown menu
    # note: schoolyear, school and user are only displayed when user.is_authenticated

    #logger.debug('  ==========  home ==========')

    # set headerbar parameters PR2018-08-06
    display_school = False
    display_department = False
    if request.user:
        display_school = True
        display_department = True
    _param = awpr_menu.get_headerbar_param(request, 'home', {
        'display_school': display_school,
        'display_department': display_department
    })
    # PR2019-02-15 go to login form if user is not authenticated
    # PR2019-02-15 temporary disabled
    #if request.user.is_authenticated:    # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.

    #logger.debug('_param: ' + str(_param))
    return render(request, 'home.html', _param)
    #else:
     #   return redirect('login')


def Loggedin(request):
    #logger.debug('  ==========  Loggedin ==========')
    # redirect to saved_href of last selected menubutton # PR2018-12-25 # PR2020-10-22 PR2021-01-25

# retrieve last opened page from, so at next login this page will open. Uses in LoggedIn
    sel_page = None
    if request and request.user:
        req_usr = request.user
        #logger.debug('req_usr: ' + str(req_usr))
        sel_page_dict = acc_view.get_usersetting_dict('sel_page', request)
        #logger.debug('sel_page_dict: ' + str(sel_page_dict))

        if sel_page_dict is not None:
            sel_page = sel_page_dict.get('page')
# get page_url of sel_page, rturns 'home' when not found
    page_url = awpr_menu.get_saved_page_url(sel_page, request)
    #logger.debug('page_url: ' + str(page_url))

    return HttpResponseRedirect(reverse_lazy(page_url))


# === MAIL =====================================
@method_decorator([login_required], name='dispatch')
class MailListView(View):
    # PR2021-09-11

    def get(self, request):

        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(" =====  MailListView  =====")

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get headerbar parameters
        page = 'page_mailbox'
        # don't show dep and school on page examyear
        # Note: set display_school / display_dep also in download_setting
        display_school = True  # (request and request.user and request.user.role <= c.ROLE_008_SCHOOL)
        display_department = True
        param = {'display_school': display_school, 'display_department': display_department}
        headerbar_param = awpr_menu.get_headerbar_param(request, page, param)

        # - save this page in Usersetting, so at next login this page will open. Uses in LoggedIn
        # PR2021-06-22 moved to get_headerbar_param
        return render(request, 'mailbox.html', headerbar_param)


@method_decorator([login_required], name='dispatch')
class MailUploadView(View):  # PR2021-01-16  PR2021-10-11

    def post(self, request):
        logging_on = s.LOGGING_ON

        files = request.FILES
        file = files.get('file')
        if logging_on:
            logger.debug('')
            logger.debug(' ============= MailUploadView ============= ')
            logger.debug('files: ' + str(files) + ' ' + str(type(files)))
            logger.debug('file: ' + str(file) + ' ' + str(type(file)))

        messages = []
        update_wrap = {}

# - get permit
        # has_permit = get_permit_crud_page_mailbox(request)
        # TODO set permit
        has_permit = True  # (request.user.role > c.ROLE_002_STUDENT and request.user.is_group_edit)
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)

# - get  variables
                mailbox_pk = upload_dict.get('mailbox_pk')
                # mode = 'save', 'send' or 'delete'
                # is_create = True when mailbox_pk is None
                mode = upload_dict.get('mode')
                is_create = (not mailbox_pk)
                is_delete = (mode == 'delete')
                is_send = (mode == 'send')

                header = upload_dict.get('header')
                body = upload_dict.get('body')

                mailto_list = upload_dict.get('mailto')
                mailto_user = ''
                if mailto_list:
                    for user_pk in mailto_list:
                        if mailto_user:
                            mailto_user += ';'
                        mailto_user += str(user_pk)
                # change '' into None
                if not mailto_user:
                    mailto_user = None

                mailcc_list = upload_dict.get('mailcc')
                mailcc_user = ''
                if mailcc_list:
                    for user_pk in mailcc_list:
                        if mailcc_user:
                            mailcc_user += ';'
                        mailcc_user += str(user_pk)
                # change '' into None
                if not mailcc_user:
                    mailcc_user = None

                if logging_on:
                    logger.debug('upload_dict: ' + str(upload_dict))
                    logger.debug('mode: ' + str(mode))
                    logger.debug('mailto_user: ' + str(mailto_user))
                    logger.debug('mailcc_user: ' + str(mailcc_user))

                updated_rows = []
                error_list = []
                is_created = False
                message_header = _('Message')

# - get selected examyear, school from usersettings
                sel_examyear, sel_school = af.get_selected_examyear_school_instance_from_usersetting(request)

                if logging_on:
                    logger.debug('mailbox_pk: ' + str(mailbox_pk))
                    logger.debug('sel_examyear: ' + str(sel_examyear))
                    logger.debug('sel_school: ' + str(sel_school))
                    logger.debug('is_create: ' + str(is_create))

# ++++ Create new mailbox_instance:
                if is_create:
                    mailbox_instance = create_mailbox_and_mailmessage_instance(sel_examyear, sel_school,
                                           header, body, mailto_user, mailcc_user, messages, request)
                    if mailbox_instance:
                        is_created = True

                else:
# +++  get existing mailbox instance
                    mailbox_instance = sch_mod.Mailbox.objects.get_or_none(
                        id=mailbox_pk,
                        user=request.user
                    )
                if logging_on:
                    logger.debug('..... mailbox_instance: ' + str(mailbox_instance))

                deleted_ok = False

                if mailbox_instance:
                    mailmessage_instance = mailbox_instance.mailmessage
                    if logging_on:
                        logger.debug('..... mailmessage_instance: ' + str(mailmessage_instance))

# ++++ Delete mailbox_instance
                    if is_delete:
                        deleted_ok = delete_mailbox_instance(mailbox_instance, request)

# +++ Update mailmessage, not when it is created, nor when deleted
                    elif not is_create:
                        update_mailmessage_instance(mailmessage_instance, header, body, mailto_user, mailcc_user,
                                                    error_list, request)

# +++ send mailmessage, onlt when is_send
                    if is_send:
                        send_mail(mailmessage_instance, mailto_user, mailcc_user, request)

# - create mailbox_row, also when is_delete (then deleted=True)
                # PR2021-089-04 debug. gave error on subject.pk: 'NoneType' object has no attribute 'pk'
                if mailbox_instance:
                    updated_rows = sch_dicts.create_mailbox_rows(
                        examyear_pk=sel_examyear.pk,
                        request=request,
                        mailbox_pk=mailbox_instance.pk
                    )


# - add messages to updated_row (there is only 1 updated_row
                if updated_rows:
                    row = updated_rows[0]
                    if row:
                        # TODO fix it or remove
                        # - add error_list to updated_rows[0]
                        if error_list:
                            updated_rows[0]['error'] = error_list
                        if is_created:
                            updated_rows[0]['created'] = True

                    update_wrap['updated_mailbox_rows'] = updated_rows

# - Create new studsubjnote if is_create:

                # attachments are stored in spaces awpmedia/awpmedia/media/private

# +++ save attachment

# ---  create file_path

# 9. return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=LazyEncoder))
# - ens of MailUploadView


def create_mailbox_and_mailmessage_instance(examyear, sender_school, header, body, mailto_user, mailcc_user, messages, request):
    # --- create mailbox item and mailmessage itemPR2021-10-11

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_mailbox_and_mailmessage_instance ----- ')

    mailbox = None
    caption = _('Create message')

    if examyear:

        msg_list = []
# - validate code and name. Function checks null, max_len, exists
        msg_err = av.validate_notblank_maxlength(header, c.MAX_LENGTH_FIRSTLASTNAME, _('The title of this message'))
        if msg_err:
            msg_list.append(msg_err)
        msg_err = av.validate_notblank_maxlength(body, 2048, _('The text of this message'), True)  # True = blanks allowed
        if msg_err:
            msg_list.append(msg_err)
        msg_err = av.validate_notblank_maxlength(mailto_user, 2048, _('The list of recipients'))
        if msg_err:
            msg_list.append(msg_err)
        msg_err = av.validate_notblank_maxlength(mailto_user, 2048, _('The list of c.c. recipients'), True)  # True = blanks allowed
        if msg_err:
            msg_list.append(msg_err)

# - first create and save mailbox item
        if len(msg_list) > 0:
            msg_html = '<br>'.join(msg_list)
            messages.append({'header': str(caption), 'class': "border_bg_invalid", 'msg_html': msg_html})
        else:
            try:
# - first create and save mailmessage item
                mailmessage = sch_mod.Mailmessage(
                    examyear=examyear,
                    sender_user=request.user,
                    sender_school=sender_school,
                    header=header,
                    body=body,
                    mailto_user=mailto_user,
                    mailcc_user=mailcc_user
                )
                mailmessage.save(request=request)

                if logging_on:
                    logger.debug('mailmessage: ' + str(mailmessage))
                    logger.debug('mailmessage.pk: ' + str(mailmessage.pk))

# - add link to this message in draft box of request.user
                # when issentmail and isreceivedmail are False: it is a saved draft mail
                # don't add mailbox item of recipients and cc until the message is sent.
                if mailmessage.pk:
                    mailbox = sch_mod.Mailbox(
                        user=request.user,
                        mailmessage=mailmessage,
                        # read=False,
                        # deleted=False,
                        #issentmail=False,
                        #isreceivedmail=False
                    )
                    mailbox.save(request=request)

                    if logging_on:
                        logger.debug('mailbox: ' + str(mailbox))

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                msg_html = ''.join((str(_('An error occurred')), ': ', '<br><i>', str(e), '</i><br>',
                                    str(_("%(cpt)s '%(val)s'could not be added.") % {'cpt': _('Message'), 'val': str(header)})))
                messages.append(
                    {'class': "border_bg_invalid", 'header': str(_('Create message')), 'msg_html': msg_html})

    if logging_on:
        logger.debug('mailbox: ' + str(mailbox))
        logger.debug('messages: ' + str(messages))

    return mailbox
# - end of create_mailbox_and_mailmessage_instance


def delete_mailbox_instance(mailbox_instance, request):
    # --- delete mailbox instance # PR2021-10-12
    # set deleted=True insted of deleting instance
    deleted_ok = False
    if mailbox_instance:
        try:
            setattr(mailbox_instance, 'deleted', True)
            mailbox_instance.save(request=request)
            deleted_ok = True
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
    return deleted_ok
# - end of delete_mailbox_instance


def update_mailmessage_instance(mailmessage_instance, header, body, mailto_user, mailcc_user, msg_list, request):
    # --- update existing mailbox instance and mailmessage instance PR2021-10-11
    # the following fiels can not be changed: examyear, sender_user, sender_school
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- update_mailmessage_instance ----- ')
        logger.debug('header: ' + str(header))
        logger.debug('body: ' + str(body))
        logger.debug('mailto_user: ' + str(mailto_user))
        logger.debug('mailcc_user: ' + str(mailcc_user))

    messages = []
    mailbox = None
    if mailmessage_instance:
        save_changes = False

        caption = _('Message')

# - save changes in field 'header'
        for field in ('header', 'body', 'mailto_user', 'mailcc_user'):
            new_value = None
            caption = ''
            if field == 'header':
                new_value = header
                caption = _('The title of this message')
            elif field == 'body':
                new_value = body
                caption = _('The text of this message')
            elif field == 'mailto_user':
                new_value = mailto_user
                caption = _('The list of recipients')
            elif field == 'mailcc_user':
                new_value = mailcc_user
                caption = _('The list of c.c. recipients')

            blanks_allowed = False if field in ('header', 'mailto_user') else True

            msg_err = av.validate_notblank_maxlength(new_value, c.MAX_LENGTH_FIRSTLASTNAME, caption, blanks_allowed)
            if msg_err:
                msg_list.append(msg_err)
            else:
                saved_value = getattr(mailmessage_instance, field)
                if logging_on:
                    logger.debug('field:        ' + str(field))
                    logger.debug('new_value:   <' + str(new_value) + '> ' + str(type(new_value)))
                    logger.debug('saved_value: <' + str(saved_value) + '> ' + str(type(saved_value)))

                if new_value != saved_value:
                    setattr(mailmessage_instance, field, new_value)
                    save_changes = True
                    if logging_on:
                        logger.debug('save field ' + str(field) + ':  ' + str(new_value))

        if save_changes:
            try:
                mailmessage_instance.save(request=request)
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                msg_html = ''.join((str(_('An error occurred')), ': ', '<br><i>', str(e), '</i><br>',
                                    str(_("%(cpt)s '%(val)s' could not be updated.") % {'cpt': _('Message'), 'val': header})))
                messages.append({'class': "border_bg_invalid", 'header': str(_('Create message')), 'msg_html': msg_html})

    if logging_on:
        logger.debug('messages: ' + str(messages))
# - end of update_mailmessage_instance


def send_mail(mailmessage_instance, mailto_user, mailcc_user, request):
    # function adds isreceivedmail mailbox_items for mailto_users and mailcc_user, issentmail for sender_user
        # - when sending: add link to this message in inbox of request.user, if not exists
        # when issentmail and isreceivedmail are False: it is a saved draft mail
        # don't add mailbox item of recipients and cc until the message is sent.

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- send_mail ----- ')
        logger.debug('mailmessage_instance: ' + str(mailmessage_instance))

    for to_cc in ('to', 'cc', 'sender'):
        is_receivedmail = False if to_cc == 'sender' else True
        is_sentmail = True if to_cc == 'sender' else False

        mailto_str = None
        if to_cc == 'to':
            mailto_str = mailto_user
        elif to_cc == 'cc':
            mailto_str = mailcc_user
        elif to_cc == 'sender':
            # sender mailbox already exists, set issentmail = True
            mailto_str = str(request.user.pk)

        if mailto_str:
            mailto_list = mailto_str.split(';')
            if mailto_list:
                for user_pk_str in mailto_list:
                    try:
                        user_pk_int = int(user_pk_str)
                        mailbox_instance = sch_mod.Mailbox.objects.filter(
                            mailmessage=mailmessage_instance,
                            user_id=user_pk_int
                        ).first()
                        if mailbox_instance is None:
                            mailbox_instance = sch_mod.Mailbox(
                                mailmessage=mailmessage_instance,
                                user_id=user_pk_int,
                                isreceivedmail=is_receivedmail,
                                issentmail=is_sentmail,
                            )
                        if mailbox_instance:
                            setattr(mailbox_instance, 'isreceivedmail', is_receivedmail)
                            setattr(mailbox_instance, 'issentmail', is_sentmail)
                            mailbox_instance.save(request=request)
                        if logging_on:
                            logger.debug('mailbox ' + str(to_cc) + ': ' + str(mailbox_instance))
                    except Exception as e:
                        logger.error(getattr(e, 'message', str(e)))


# === EXAMYEAR =====================================
@method_decorator([login_required], name='dispatch')
class ExamyearListView(View):
    # PR2018-08-06 PR2018-05-10 PR2018-03-02 PR2020-10-04 PR2021-03-25

    def get(self, request):
        #logger.debug(" =====  ExamyearListView  =====")

# -  get user_lang
        user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
        activate(user_lang)

# - get headerbar parameters
        page = 'page_examyear'
        # don't show dep and school on page examyear
        # Note: set display_school / display_dep also in download_setting
        display_school = True  # (request and request.user and request.user.role <= c.ROLE_008_SCHOOL)
        display_department = False
        param = {'display_school': display_school, 'display_department': display_department}
        headerbar_param = awpr_menu.get_headerbar_param(request, page, param)

# - save this page in Usersetting, so at next login this page will open. Uses in LoggedIn
        # PR2021-06-22 moved to get_headerbar_param

        #logger.debug("headerbar_param: " + str(headerbar_param))

        return render(request, 'examyears.html', headerbar_param)


@method_decorator([login_required], name='dispatch')
class ExamyearUploadView(View):  # PR2020-10-04 PR2021-08-30

    def post(self, request):
        logging_on = s.LOGGING_ON

        update_wrap = {}
        examyear_rows = []

        if request.user is not None and request.user.country is not None:
            req_usr = request.user
            permit_list, requsr_usergroups_list = acc_view.get_userpermit_list('page_examyear', req_usr)
            has_permit = 'permit_crud' in permit_list

            if logging_on:
                logger.debug(' ')
                logger.debug(' ============= ExamyearUploadView ============= ')
                logger.debug('permit_list: ' + str(permit_list))
                logger.debug('has_permit:  ' + str(has_permit))

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if has_permit and upload_json:
                upload_dict = json.loads(upload_json)

                append_dict = {}
                error_list = []

# - get mode
                mode = upload_dict.get('mode')

# - get country of requsr, only if country is not locked
                country = None
                if request.user.country and not request.user.country.locked:
                    country = request.user.country
                if logging_on:
                    # upload_dict: {'id': {'table': 'examyear', 'mode': 'delete', 'mapid': 'examyear_59'}}
                    logger.debug('upload_dict: ' + str(upload_dict))
                    logger.debug('country: ' + str(country))
                    logger.debug('mode:    ' + str(mode))

                if country:
                    new_examyear_instance = None

# - get current examyear from upload_dict - when mode is 'create': examyear is None. It will be created at "elif mode == 'create'"
                    examyear_pk = upload_dict.get('examyear_pk')
                    current_examyear_instance = sch_mod.Examyear.objects.get_or_none(pk=examyear_pk)

                    if logging_on:
                        logger.debug('current_examyear_instance: ' + str(current_examyear_instance))

# +++ delete current_examyear_instance
                    if mode == 'delete':
                        if current_examyear_instance:
                            this_text = _("Exam year '%(tbl)s' ") % {'tbl': str(current_examyear_instance.code)}
        # - check if current_examyear_instance is closed or schools have activated or locked it
                            msg_err = av.validate_delete_examyear(current_examyear_instance)
                            if msg_err:
                                error_list.append(msg_err)
                                if logging_on:
                                    logger.debug('msg_err: ' + str(msg_err))

                            else:
                                if logging_on:
                                    logger.debug('delete current_examyear_instance: ' + str(current_examyear_instance))
                                msg_list = []  # TODO
                                current_examyear_instance_pk = current_examyear_instance.pk
                                deleted_ok = sch_mod.delete_instance(current_examyear_instance, msg_list, error_list, request, this_text)
                                if logging_on:
                                    logger.debug('deleted_ok' + str(deleted_ok))

                                if deleted_ok:
                                    # - add deleted_row to current_examyear_instance_rows
                                    examyear_rows.append({'pk': current_examyear_instance_pk,
                                                         'mapid': 'examyear_' + str(current_examyear_instance_pk),
                                                         'deleted': True})
                                    instance = None
                                    if logging_on:
                                        logger.debug('examyear_rows' + str(examyear_rows))
# +++ create new examyear
                    elif mode == 'create':
     # - validate unique examyear_code_int
                        country = request.user.country
                        examyear_code_int = upload_dict.get('examyear_code')
                        msg_err = av.validate_unique_examyear(country, examyear_code_int, request)
                        if msg_err:
                            error_list.append(msg_err)
                            if logging_on:
                                logger.debug('msg_err: ' + str(msg_err))
                        else:
     # - create new examyear
                            new_examyear_instance, msg_err = create_examyear(country, examyear_code_int, request)
                            if new_examyear_instance:
                                append_dict['created'] = True
    # - copy all tables from last examyear existing examyear
                                also_copy_schools = True
                                # prev_examyear_instance, msg_err = sf.get_previous_examyear_instance(new_examyear_instance)
                                log_list = []
                                copy_tables_from_last_year(current_examyear_instance, new_examyear_instance, also_copy_schools, log_list, request)
                            if msg_err:
                                error_list.append(msg_err)
                                if logging_on:
                                    logger.debug('msg_err: ' + str(msg_err))

# +++ update examyear, skip when it is created. All fields are saved in create_examyear
                    if logging_on:
                        logger.debug('new_examyear_instance: ' + str(new_examyear_instance))
                        logger.debug('mode: ' + str(mode))

                    if current_examyear_instance and mode == 'update':
                        updated = update_examyear(current_examyear_instance, upload_dict, error_list, request)
                        if updated:
                            examyear_rows = sch_dicts.create_examyear_rows(
                                req_usr=req_usr,
                                append_dict={},
                                examyear_pk=current_examyear_instance.pk
                            )
                    if logging_on:
                        logger.debug('error_list: ' + str(error_list))

                    if error_list:
                        update_wrap['messages'] = error_list
# - add update_dict to update_wrap
                    if new_examyear_instance:
                        examyear_rows = sch_dicts.create_examyear_rows(
                            req_usr=req_usr,
                            append_dict=append_dict,
                            examyear_pk=new_examyear_instance.pk
                        )
                    else:
                        # examyear is None when error on creating examyear. Return msg_err still
                        if append_dict:
                            examyear_rows = [append_dict]
        update_wrap['updated_examyear_rows'] = examyear_rows

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of ExamyearUploadView


############ ORDER LIST ##########################
@method_decorator([login_required], name='dispatch')
class OrderlistsParametersView(View):  # PR2021-08-31

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug('OrderlistsParametersView')

        # function updates orderlist parameters in examyear table
        update_wrap = {}
        examyear_rows = []
        messages = []
        error_list = []

# - get permit
        has_permit = False
        req_usr = request.user
        if req_usr and req_usr.country and req_usr.schoolbase:
            permit_list = req_usr.permit_list('page_orderlist')
            if permit_list:
                has_permit = 'permit_crud' in permit_list
            if logging_on:
                logger.debug('permit_list: ' + str(permit_list))
                logger.debug('has_permit: ' + str(has_permit))

            # - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

            # - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if has_permit and upload_json:
                upload_dict = json.loads(upload_json)

                # - get selected examyear,from usersettings
                # exames are only ordered in first exam period
                sel_examyear_instance, sel_examperiodNIU = \
                    dl.get_selected_examyear_examperiod_from_usersetting(request)
                if logging_on:
                    logger.debug('sel_examyear_instance: ' + str(sel_examyear_instance))

                if sel_examyear_instance:
                    update_examyear(sel_examyear_instance, upload_dict, error_list, request)

# - create examyear_row
                    updated_rows = sch_dicts.create_examyear_rows(
                        req_usr=req_usr,
                        append_dict={},
                        examyear_pk=sel_examyear_instance.pk
                    )
                    update_wrap['updated_examyear_rows'] = updated_rows

        if len(messages):
            update_wrap['messages'] = messages
        if logging_on:
            logger.debug('update_wrap: ' + str(update_wrap))

        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))


# --- end of OrderlistsParametersView


############ PUBLISH ORDER LIST ##########################

@method_decorator([login_required], name='dispatch')
class OrderlistRequestVerifcodeView(View):  # PR2021-09-08
    def post(self, request):
        logging_on = False  # s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= OrderlistRequestVerifcodeView ============= ')

        update_wrap = {}
        has_error = False

# - get permit
        has_permit = False
        req_usr = request.user
        if req_usr and req_usr.country:
            permit_list = req_usr.permit_list('page_orderlist')
            if permit_list:
                has_permit = 'permit_submit_orderlist' in permit_list
            if logging_on:
                logger.debug('req_usr.usergroup_list:: ' + str(req_usr.usergroup_list))
                logger.debug('permit_list: ' + str(permit_list))
                logger.debug('has_permit: ' + str(has_permit))

# - reset language
        user_lang = req_usr.lang if req_usr and req_usr.lang else c.LANG_DEFAULT
        activate(user_lang)

        msg_list = []
        class_str = 'border_bg_transparent'
        if not has_permit:
            class_str = 'border_bg_invalid'
            msg_list.append(str(_("You don't have permission to perform this action.")))
            has_error = True
        else:

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                sel_examyear, may_edit, msg_list = \
                    dl.get_selected_examyear_from_usersetting(request)

                if not may_edit:
                    class_str = 'border_bg_warning'
                    has_error = True
                else:
                    verifcode_key, exception_str = af.send_email_verifcode(
                        formname='orderlist',
                        email_template='email_send_verifcode_orderlist.html',
                        request=request,
                        sel_examyear=sel_examyear
                    )
                    if verifcode_key:
                        update_wrap['verificationkey'] = verifcode_key
                        msg_list += (str(_("We have sent an email with a 6 digit verification code to the email address:")),
                                     '<br>', req_usr.email, '<br>',
                                     str(_("Enter the verification code and click 'Publish orderlist' to publish the orderlist.")))
                    else:
                        class_str = 'border_bg_invalid'
                        has_error = True
                        if exception_str:
                            msg_list += (str(_('An error occurred')), ':<br><i>', exception_str, '</i><br>')
                        else:
                            msg_list += (str(_('An error occurred')), '. ')
                        msg_list += (str(_('The email with the verification code has not been sent.')), '</p>')

        if has_error:
            update_wrap['error'] = True

        if msg_list:
            msg_wrap_start = ["<div class='p-2 ", class_str, "'>"]
            msg_wrap_end = ['</p>']

            msg_html = ''.join(msg_wrap_start + msg_list + msg_wrap_end)

            update_wrap['publish_orderlist_msg_html'] = msg_html

    # - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of OrderlistRequestVerifcodeView


@method_decorator([login_required], name='dispatch')
class OrderlistsPublishView(View):  # PR2021-09-08 PR2021-10-12

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug('  ===== OrderlistsPublishView =====')

        # function publishes orderlist and sends email to schools

        update_wrap = {}
        has_error = False

# - get permit
        has_permit = False
        req_usr = request.user
        if req_usr and req_usr.country and req_usr.schoolbase:
            permit_list = req_usr.permit_list('page_orderlist')
            if permit_list:
                has_permit = 'permit_submit_orderlist' in permit_list
            if logging_on:
                logger.debug('permit_list: ' + str(permit_list))
                logger.debug('has_permit: ' + str(has_permit))

# - reset language
        user_lang = req_usr.lang if req_usr and req_usr else c.LANG_DEFAULT
        activate(user_lang)

        log_list = []
        msg_list = []
        class_str = 'border_bg_transparent'
        if not has_permit:
            class_str = 'border_bg_invalid'
            msg_list.append(str(_("You don't have permission to perform this action.")))
            has_error = True
        else:

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload')
            if upload_json:
                upload_dict = json.loads(upload_json)

                if logging_on:
                    logger.debug('upload_dict' + str(upload_dict))

                sel_examyear_instance, may_edit, msg_list = \
                    dl.get_selected_examyear_from_usersetting(request)

                if not may_edit:
                    class_str = 'border_bg_warning'
                    has_error = True
                else:

# - check verificationcode.
                    formname = 'orderlist'
                    msg_err = af.check_verificationcode(upload_dict, formname, request)
                    if logging_on:
                        logger.debug('msg_err' + str(msg_err))
                    if msg_err:
                        has_error = True
                        class_str = 'border_bg_invalid'
                        msg_list.append(str(msg_err))
                    else:
                        update_wrap['verification_is_ok'] = True

# - get selected examyear,from usersettings
                        # exames are only ordered in first exam period
                        sel_examyear_instance, sel_examperiodNIU = \
                            dl.get_selected_examyear_examperiod_from_usersetting(request)
                        if logging_on:
                            logger.debug('sel_examyear_instance: ' + str(sel_examyear_instance))

# - create log_list
                        today_dte = af.get_today_dateobj()
                        today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)
                        log_list = [c.STRING_DOUBLELINE_80,
                                    str(_('Publish orderlist exams')) + ' ' + str(_('date')) + ': ' + str(
                                        today_formatted),
                                    c.STRING_DOUBLELINE_80]
                        log_list.append(
                            c.STRING_SPACE_10 + str(_("Exam year : %(ey)s") % {'ey': str(sel_examyear_instance.code)}))
                        log_list.append(c.STRING_SPACE_05)

# get count_dict only once and create orderlists from this dict,
# to make sure that the published orderlist and the excel files per schoolcontain the same amout of subjects

# get text from examyearsetting
                        settings = af.get_exform_text(sel_examyear_instance, ['exform', 'ex1'])

# - get department_dictlist, lvlbase_dictlist, subjectbase_dictlist, schoolbase_dictlist
                        department_dictlist = subj_view.create_departmentbase_dictlist(sel_examyear_instance)
                        lvlbase_dictlist = subj_view.create_levelbase_dictlist(sel_examyear_instance)
                        subjectbase_dictlist = subj_view.create_subjectbase_dictlist(sel_examyear_instance)
                        schoolbase_dictlist = subj_view.create_schoolbase_dictlist(sel_examyear_instance)

# +++ get nested dicts of subjects per school, dep, level, lang, ete_exam
                        count_dict = subj_view.create_studsubj_count_dict(sel_examyear_instance, request)
                        total_dict = count_dict.get('total')
                        if logging_on:
                            logger.debug('total_dict: ' + str(total_dict))

                        if not total_dict:
                            has_error = True
                            class_str = 'border_bg_warning'
                            msg_str = str(_("There are no submitted subjects."))
                            msg_list.append(msg_str)

                            log_list.append(''.join((c.STRING_SPACE_10, msg_str)))
                        else:

# - get school of request_user, for storing in Published table and as sender in emails
                            requsr_school = sch_mod.School.objects.get_or_none(
                                examyear=sel_examyear_instance,
                                base=req_usr.schoolbase
                            )
                            requsr_school_name = requsr_school.name
                            min_ond = settings['minond']
                            now_arr = upload_dict.get('now_arr', [])

# -create published_instance
                            published_instance, temp_file, file_path, filename_ext = \
                                create_published_instance_orderlist(
                                    now_arr=now_arr,
                                    examyear=sel_examyear_instance,
                                    school=requsr_school,
                                    request=request,
                                    user_lang=user_lang)

# -create final_orderlist
                            msg_err = create_final_orderlist_xlsx(temp_file, sel_examyear_instance,
                                                        department_dictlist, lvlbase_dictlist, subjectbase_dictlist,
                                                        schoolbase_dictlist, count_dict,
                                                        requsr_school_name, min_ond, user_lang)
                            if msg_err:
                                has_error = True
                                class_str = 'border_bg_invalid'
                                err_str01 = str(_('An error occurred'))
                                err_str02 = str(_('The orderlist is not created.'))
                                msg_str = ''.join((err_str01, ': ', msg_err, '<br>', err_str02))
                                msg_list.append(msg_str)

                                log_list.append(''.join((c.STRING_SPACE_10, err_str01, ':')))
                                log_list.append(''.join((c.STRING_SPACE_10, msg_err)))
                                log_list.append(''.join((c.STRING_SPACE_10, err_str02)))
                                log_list.append(c.STRING_SPACE_05)
                            else:
# - save published instance
                                msg_err = save_published_instance(published_instance, file_path, temp_file, request)
                                if msg_err:
                                    class_str = 'border_bg_invalid'
                                    err_str01 = str(_('An error occurred'))
                                    err_str02 = str(_('The orderlist is not saved.'))
                                    msg_str = ''.join((err_str01, ': ', msg_err, '<br>', err_str02))
                                    msg_list.append(msg_str)

                                    log_list.append(''.join((c.STRING_SPACE_10, err_str01, ':')))
                                    log_list.append(''.join((c.STRING_SPACE_10, msg_err)))
                                    log_list.append(''.join((c.STRING_SPACE_10, err_str02)))
                                    log_list.append(c.STRING_SPACE_05)

                                else:
                                    class_str = 'border_bg_valid'
                                    msg_str = str(_("An orderlist is created with the filename:"))
                                    msg_list.append('<br>'.join((msg_str, filename_ext)))

                                    log_list.append(''.join((c.STRING_SPACE_10, msg_str)))
                                    log_list.append(''.join((c.STRING_SPACE_15, filename_ext)))
                                    log_list.append(c.STRING_SPACE_05)

        # get list of 'auth1' and 'auth2' users of requsr_school, for sending email with total_orderlist and cc to schools
                                    allowed_usergroups = ('auth1', 'auth2')
                                    cc_pk_str_list, cc_name_list, cc_email_list = get_school_emailto_list(requsr_school, allowed_usergroups)
                                    if logging_on:
                                        logger.debug('cc_pk_str_list: ' + str(cc_pk_str_list))
                                        logger.debug('cc_name_list: ' + str(cc_name_list))
                                        logger.debug('cc_email_list: ' + str(cc_email_list))
# - send email
                                    sendto_pk_str_list = cc_pk_str_list
                                    sendto_name_list = cc_name_list
                                    sendto_email_list = cc_email_list
                                    mail_sent = send_email_orderlist(
                                        examyear=sel_examyear_instance,
                                        school=requsr_school,
                                        is_total_orderlist=True,
                                        sendto_pk_str_list=sendto_pk_str_list,
                                        sendto_name_list=sendto_name_list,
                                        sendto_email_list=sendto_email_list,
                                        cc_pk_str_list=None,
                                        cc_email_list=None,
                                        published_instance=published_instance,
                                        request=request
                                    )
                                    if not mail_sent:
                                        log_list.append(''.join((c.STRING_SPACE_10, str(_('An error occurred while sending the email.')), ' ', str(_('The email is not sent.')))))
                                    else:
                                        log_list.append(''.join((c.STRING_SPACE_10, str(_('An email with the orderlist is sent to')), ':')))
                                        log_list.append(''.join((c.STRING_SPACE_15, ', '.join((sendto_name_list)) )))
                                    log_list.append(c.STRING_SPACE_05)

                                    if logging_on:
                                        logger.debug('mail_sent: ' + str(mail_sent))

#######################################
# create separate orderlist for each school, also when no exams found
                                    # schoolbase_dictlist: [{'sbase_id': 2, 'sbase_code': 'CUR01', 'sch_name': 'Ancilla Domini Vsbo'},
                                    count_school_orderlists = 0
                                    for schoolbase_dict in schoolbase_dictlist:

                            # +++ get nested dicts of subjects of this  school, dep, level, lang, ete_exam
                                        schoolbase_pk = schoolbase_dict.get('sbase_id')
                                        count_dict = subj_view.create_studsubj_count_dict(sel_examyear_instance,
                                                                                          request, schoolbase_pk)

                                        is_created = create_orderlist_per_school(
                                            sel_examyear_instance, schoolbase_dict,
                                            department_dictlist, lvlbase_dictlist, subjectbase_dictlist,
                                            count_dict, now_arr, min_ond, requsr_school_name, log_list,
                                            cc_pk_str_list, cc_email_list, cc_name_list,
                                            user_lang, request)
                                        if is_created:
                                            count_school_orderlists += 1

                                    if count_school_orderlists == 1:
                                        msg_list.append(str(_("The orderlist of one school is created.")))
                                    else:
                                        counst_str = str(count_school_orderlists) if count_school_orderlists else pgettext_lazy('geen', 'no')
                                        msg_list.append(str(_("The orderlists of %(count)s schools are created.") % {'count': counst_str}))

        update_wrap['log_list'] = log_list

        if logging_on:
            logger.debug('msg_list: ' + str(msg_list))

        if has_error:
            update_wrap['error'] = True

        msg_wrap_start = ["<div class='p-2 ", class_str, "'>"]
        msg_list_html = []
        for item in msg_list:
            msg_list_html.append(''.join(("<p>", item, "</p>")))

        msg_openlogfile = ['<p>', str(_("Click")),
                             " <a id='id_MPUBORD_OpenLogfile' href='#' class='awp_href'>",
                                str(_("here")), "</a> ",
                             str(_("to download the logfile with the details.")),
                             "</p>"]
        msg_wrap_end = ['</p>']

        msg_html = ''.join(msg_wrap_start + msg_list_html + msg_openlogfile + msg_wrap_end)

        if logging_on:
            logger.debug('msg_html: ' + str(msg_html))

        update_wrap['publish_orderlist_msg_html'] = msg_html

        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# --- end of OrderlistsPublishView

def create_orderlist_per_school(sel_examyear_instance, schoolbase_dict,
                                department_dictlist, lvlbase_dictlist, subjectbase_dictlist,
                                count_dict, now_arr, min_ond, requsr_school_name, log_list,
                                cc_pk_str_list, cc_email_list, cc_name_list,
                                user_lang, request):
    # function creates orderlist of one school # PR2021-10-12
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('  ===== create_orderlist_per_school =====')

    sbase_id = schoolbase_dict.get('sbase_id')
    sbase_code = schoolbase_dict.get('sbase_code', '')
    sch_name = schoolbase_dict.get('sch_name', '')
    sch_abbrev = schoolbase_dict.get('sch_abbrev', '')
    orderlist_is_created = False
    # filter on examyear.code (is integer), not on examyear to include SXM schools
    school = sch_mod.School.objects.get_or_none(
        examyear__code=sel_examyear_instance.code,
        base_id=sbase_id
    )

    if school:
        log_list.append(''.join(
            ((sbase_code + c.STRING_SPACE_10)[:10], sch_name)))

        # - get list of 'auth1' and 'auth2'users of this school, for sending email
        allowed_usergroups = ('auth1', 'auth2')
        sendto_pk_str_list, sendto_name_list, sendto_email_list = \
            get_school_emailto_list(school, allowed_usergroups)

        count_total, subjbasepk_inuse_list = count_total_exams(count_dict, sbase_id)

        if not count_total:
            log_list.append(''.join((c.STRING_SPACE_10,
                                     str(_("This school has no submitted subjects.")))))

            log_list.append(c.STRING_SPACE_05)
        else:
            if logging_on:
                logger.debug('..... school: ' + str(school))
                logger.debug('sendto_pk_str_list: ' + str(sendto_pk_str_list))
                logger.debug('sendto_name_list: ' + str(sendto_name_list))
                logger.debug('sendto_email_list: ' + str(sendto_email_list))
                logger.debug('count_total: ' + str(count_total))
                logger.debug('subjbasepk_inuse_list: ' + str(subjbasepk_inuse_list))

            # create published instance for this school
            published_instance, temp_file, file_path, filename_ext = \
                create_published_instance_orderlist(
                    now_arr=now_arr,
                    examyear=sel_examyear_instance,
                    school=school,
                    request=request,
                    user_lang=user_lang,
                    school_code=sbase_code,
                    school_abbrev=sch_abbrev)

            msg_err = create_final_orderlist_perschool_xlsx(
                output=temp_file,
                sel_examyear_instance=sel_examyear_instance,
                department_dictlist=department_dictlist,
                lvlbase_dictlist=lvlbase_dictlist,
                subjectbase_dictlist=subjectbase_dictlist,
                count_dict=count_dict,
                subjbasepk_inuse_dict=subjbasepk_inuse_list,
                school_code=sbase_code,
                school_name=sch_name,
                requsr_school_name=requsr_school_name,
                min_ond=min_ond,
                user_lang=user_lang)

            if msg_err:
                err_str01 = str(_('An error occurred'))
                err_str02 = str(_('The orderlist of this school is not created.'))
                log_list.append(''.join((c.STRING_SPACE_10, err_str01, ':')))
                log_list.append(''.join((c.STRING_SPACE_10, msg_err)))
                log_list.append(''.join((c.STRING_SPACE_10, err_str02)))
                log_list.append(c.STRING_SPACE_05)
            else:
                msg_err = save_published_instance(published_instance, file_path, temp_file, request)
                if msg_err:
                    err_str01 = str(_('An error occurred'))
                    err_str02 = str(
                        _('The orderlist of this school is not saved.'))
                    log_list.append(''.join((c.STRING_SPACE_10, err_str01, ':')))
                    log_list.append(''.join((c.STRING_SPACE_10, msg_err)))
                    log_list.append(''.join((c.STRING_SPACE_10, err_str02)))
                    log_list.append(c.STRING_SPACE_05)
                else:
                    orderlist_is_created = True
                    log_list.append(''.join((c.STRING_SPACE_10,
                                             str(_('An orderlist of this school is created with the filename:')))))
                    log_list.append(''.join((c.STRING_SPACE_10, filename_ext)))
                    log_list.append(c.STRING_SPACE_05)

                    # get list of users of this school, for sending email
                    mail_sent = send_email_orderlist(
                        examyear=sel_examyear_instance,
                        school=school,
                        is_total_orderlist=False,
                        sendto_pk_str_list=sendto_pk_str_list,
                        sendto_name_list=sendto_name_list,
                        sendto_email_list=sendto_email_list,
                        cc_pk_str_list=cc_pk_str_list,
                        cc_email_list=cc_email_list,
                        published_instance=published_instance,
                        request=request
                    )
                    if not mail_sent:
                        log_list.append(''.join((c.STRING_SPACE_10, str(_(
                            'An error occurred while sending the email.')), ' ',
                                                 str(_('The email is not sent.')))))
                    else:
                        log_list.append(''.join((c.STRING_SPACE_10, str(_(
                            'An email with the orderlist is sent to')), ':')))
                        log_list.append(''.join((c.STRING_SPACE_15, ', '.join((sendto_name_list)))))
                        log_list.append(''.join((c.STRING_SPACE_10, str(_(
                            'c.c.')), ':')))
                        log_list.append(''.join((c.STRING_SPACE_15, ', '.join((cc_name_list)))))
                    log_list.append(c.STRING_SPACE_05)
                    if logging_on:
                        logger.debug('mail_sent: ' + str(mail_sent))

    return orderlist_is_created
# - end of create_orderlist_per_school


def count_total_exams(count_dict, sbase_id):  # PR2021-09-10
    count_total = 0
    # subjbasepk_inuse_dict must have same stryucture as 'total' in count_dict
    subjbasepk_inuse_dict = {}
    # count total subjects of school with schoolbase_pk = sbase_id
    for ete_duo_key in count_dict:
        if ete_duo_key != 'total':
            ete_duo_dict = count_dict[ete_duo_key]
            for lang_key in ete_duo_dict:
                if lang_key != 'total':
                    lang_dict = ete_duo_dict[lang_key]
                    for depbase_pk in lang_dict:
                        if isinstance(depbase_pk, int):
                            depbase_dict = lang_dict[depbase_pk]
                            for lvlbase_pk in depbase_dict:
                                if isinstance(lvlbase_pk, int):
                                    lvlbase_dict = depbase_dict[lvlbase_pk]
                                    for schoolbase_pk in lvlbase_dict:
                                        if schoolbase_pk == sbase_id:
                                            schoolbase_dict = lvlbase_dict[schoolbase_pk]
                                            for subjbase_pk in schoolbase_dict:
                                                if isinstance(subjbase_pk, int):
                                                    subjbase_list = schoolbase_dict[subjbase_pk]
                                                    exams_plus_extra = subjbase_list[0] + subjbase_list[1]
                                                    if exams_plus_extra:
                                                        count_total += exams_plus_extra
                                                        if subjbase_pk not in subjbasepk_inuse_dict:
                                                            subjbasepk_inuse_dict[subjbase_pk] = []
    return count_total, subjbasepk_inuse_dict
# - end of count_total_exams


def get_school_emailto_list(school, allowed_usergroups):  # PR2021-09-09

    sendto_pk_str_list, sendto_email_list, sendto_name_list = [], [], []
    # get list of users of this school, for sending email
    # only users with allowed_usergroups will be added
    school_users = acc_mod.User.objects.filter(
        schoolbase=school.base,
        activated=True,
        is_active=True,
        usergroups__isnull=False
    )
    for school_user in school_users:
        is_allowed = False
        if school_user.usergroups:
            user_usergroup_arr = school_user.usergroups.split(';')
            is_allowed = False
            for user_usergroup in user_usergroup_arr:
                for allowed_usergroup in allowed_usergroups:
                    if allowed_usergroup == user_usergroup:
                        is_allowed = True
                        break
                if is_allowed:
                    break
        if is_allowed:
            sendto_pk_str_list.append(str(school_user.pk))
            sendto_email_list.append(school_user.email)
            sendto_name_list.append(school_user.last_name)

    return sendto_pk_str_list, sendto_name_list, sendto_email_list
# - end of get_school_emailto_list


def send_email_orderlist(examyear, school, is_total_orderlist,
                         sendto_pk_str_list, sendto_name_list, sendto_email_list,
                         cc_pk_str_list, cc_email_list, published_instance, request):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ----- send_email_orderlist  -----')
        logger.debug('sel_examyear: ' + str(examyear) + ' ' + str(type(examyear)))
        logger.debug('sel_school: ' + str(school) + ' ' + str(type(school)))

    mail_sent = False
    req_usr = request.user
    if sendto_email_list:
        try:
            subject_str = ' '.join((str(_('Orderlist')), str(_('Exams')).lower(), str(examyear.code), school.base.code, school.name))
            school_article = school.article if school.article else ''
            school_attn = ' '.join(( str(_('To')), school_article, school.name ))
            from_email = 'AWP-online <noreply@awponline.net>'

            requsr_school = sch_mod.School.objects.get_or_none(
                base=req_usr.schoolbase,
                examyear=examyear
            )
            requsr_school_article = requsr_school.article.capitalize() if requsr_school.article else ''
            sender_organisation = ''.join((requsr_school_article, ' ', requsr_school.name, ','))
            sender_name = req_usr.last_name
            msg_dict = {
                'examyear_str': str(examyear.code),
                'school_attn': school_attn,
                'school_code': school.base.code,
                'school_name': school.name,
                'sender_organisation': sender_organisation,
                'sender_name': sender_name,
                'sendto_name_list': sendto_name_list,
                'is_total_orderlist': is_total_orderlist
            }

            if logging_on:
                logger.debug('msg_dict: ' + str(msg_dict))

            email_template_name = 'publish_orderlist_email.html',
            body_str = render_to_string(email_template_name, msg_dict)

            if logging_on:
                #logger.debug('body_str: ' + str(body_str) + ' ' + str(type(body_str)))
                logger.debug('sendto_email_list: ' + str(sendto_email_list))
                logger.debug('cc_email_list: ' + str([cc_email_list]))

            # PR2018-04-25 arguments: send_mail(subject, message, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None, connection=None, html_message=None)
            reply_to = (request.user.email,)
            email_message = EmailMessage(
                subject=subject_str,
                body=body_str,
                from_email=from_email,
                to=sendto_email_list,
                cc=cc_email_list,
                reply_to=reply_to)

            if published_instance and published_instance.file:
                f = published_instance.file
                f.open()
                # msg.attach(filename, content, mimetype)
                #content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                email_message.attach(basename(f.name), f.read(), guess_type(f.name)[0])
                f.close()

                if logging_on:
                    logger.debug('published_instance.name: ' + str(published_instance.name))

            mail_count = email_message.send()
            if logging_on:
                logger.debug('mail_count: ' + str(mail_count) + ' ' + str(type(mail_count)))

            if mail_count:
                mail_sent = True

                mailto_user_str = ';'.join(sendto_pk_str_list) if sendto_pk_str_list else None
                mailcc_user_str = ';'.join(cc_pk_str_list) if cc_pk_str_list else None

                if logging_on:
                    logger.debug('mailto_user_str: ' + str(mailto_user_str))
                    logger.debug('mailcc_user_str: ' + str(mailcc_user_str))

# - add message to Mailmessage
                mailmessage = sch_mod.Mailmessage(
                    examyear=examyear,
                    sender_user=req_usr,
                    sender_school=requsr_school,
                    header=subject_str,
                    body=body_str,
                    mailto_user=mailto_user_str,
                    mailcc_user=mailcc_user_str
                )
                mailmessage.save(request=request)

                if logging_on:
                    logger.debug('mailmessage: ' + str(mailmessage))
                    logger.debug('mailmessage.pk: ' + str(mailmessage.pk))

# - add published_instance as Mailattachment
                mailattachment = sch_mod.Mailattachment.objects.create(
                    mailmessage=mailmessage,
                    filename = published_instance.filename,
                    file=published_instance.file
                )
                # save to add modifiedat and modifiedby to mailattachment
                mailattachment.save(request=request)

                if logging_on:
                    logger.debug('mailattachment: ' + str(mailattachment))
                    logger.debug('mailattachment.pk: ' + str(mailattachment.pk))

# - add message in Mailbox of mailto_user and mailcc_user
                # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07
                now_iso = timezone.now().isoformat()
                sender_pk_str = str(req_usr.pk)

                # fields of other_values: mailmessage_id, read, deleted, modifiedby_id, modifiedat
                other_values = ', '.join((str(mailmessage.pk), 'FALSE', 'FALSE', sender_pk_str, "'" + now_iso + "'"))
                sql_list = [
                    "INSERT INTO schools_mailbox (user_id, issentmail, isreceivedmail, mailmessage_id, read, deleted, modifiedby_id, modifiedat) VALUES"
                     ]

        # - add mail in inbox of recipients
                value_str = ''
                is_sent_mail_str = 'FALSE,'
                is_received_mail_str = 'TRUE,'
                if sendto_pk_str_list:
                    for pk_str in sendto_pk_str_list:
                        if value_str:
                            value_str += ','
                        value_str += ''.join(('(', pk_str, ',',  is_sent_mail_str, is_received_mail_str,  other_values, ')'))

                if cc_pk_str_list:
                    for pk_str in cc_pk_str_list:
                        if value_str:
                            value_str += ','
                        value_str += ''.join(('(', pk_str, ',', is_sent_mail_str, is_received_mail_str, other_values, ')'))

        # - add mail in mailbox of sender (request.user is sender)
                is_sent_mail_str = 'TRUE,'
                is_received_mail_str = 'FALSE,'
                if value_str:
                    value_str += ','
                value_str += ''.join(('(', sender_pk_str, ',',  is_sent_mail_str,  is_received_mail_str, other_values, ')'))

                sql_list.append(value_str)
                sql_list.append('RETURNING *;')
                sql = ' '.join(sql_list)

                if logging_on:
                    logger.debug('sql: ' + str(sql))

                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    rows = af.dictfetchall(cursor)
                    if logging_on:
                        for row in rows:
                            logger.debug('row: ' + str(row))

        except Exception as e:
            mail_sent = False
            logging_on.error(getattr(e, 'message', str(e)))

        if logging_on:
            logger.debug('mail_sent: ' + str(mail_sent))
    return mail_sent
# - end of send_email_orderlist

###################################################

def create_published_instance_orderlist(now_arr, examyear, school, request, user_lang, school_code=None, school_abbrev=None):
    # PR2021-09-09
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ============= create_published_instance_orderlist ============= ')

# +++ create new published_instance.
    # file  will be added after creating Ex-form
    year_str = str(now_arr[0])
    month_str = ("00" + str(now_arr[1]))[-2:]
    date_str = ("00" + str(now_arr[2]))[-2:]
    hour_str = ("00" + str(now_arr[3]))[-2:]
    minute_str = ("00" + str(now_arr[4]))[-2:]
    now_formatted = ''.join([year_str, "-", month_str, "-", date_str, " ", hour_str, "u", minute_str])
    today_date = af.get_date_from_arr(now_arr)
    exams_str = str(_('Exams')).lower()
    examyear_str = str(examyear.code)
    if school_code:
        examyear_str += ' ' + school_code
    if school_abbrev:
        examyear_str += ' ' + school_abbrev
    file_name = ' '.join( (str(_('Orderlist')), exams_str, examyear_str, 'dd', now_formatted))
    filename_ext = file_name + '.xlsx'
    published_instance = sch_mod.Published(
        school=school,
        department=None,
        examtype=None,
        examperiod=c.EXAMPERIOD_FIRST,
        name=file_name,
        filename=filename_ext,
        datepublished=today_date,
        modifiedat=timezone.now,
        modifiedby=request.user
    )
    # Note: filefield 'file' gets value after creating orderlist

    #published_instance.filename = file_name + '.xlsx'
    # PR2021-09-06 debug: request.user is not saved in instance.save, don't know why
    published_instance.save(request=request)

    if logging_on:
        logger.debug(' request.user: ' + str(request.user))
        logger.debug('published_instance.saved: ' + str(published_instance))
        logger.debug('published_instance.pk: ' + str(published_instance.pk))
        logger.debug('published_instance.modifiedby: ' + str(published_instance.modifiedby))

# ---  create file_path
    # PR2021-08-07 changed to file_dir = 'country/examyear/published/'
    # this one gives path:awpmedia/awpmedia/media/cur/2022/published
    country_abbrev = examyear.country.abbrev.lower()
    examyear_str = str(examyear.code)
    file_dir = '/'.join((country_abbrev, examyear_str, 'exfiles'))
    file_path = '/'.join((file_dir, published_instance.filename))
    file_name = published_instance.name

    if logging_on:
        logger.debug('file_dir: ' + str(file_dir))
        logger.debug('file_name: ' + str(file_name))
        logger.debug('filepath: ' + str(file_path))

# ---  create file Name and worksheet Name
    today_dte = af.get_today_dateobj()
    today_formatted = af.format_DMY_from_dte(today_dte, user_lang, False)  # False = not month_abbrev
    title = ' '.join((str(_('Orderlist')), exams_str, examyear_str, 'dd', today_dte.isoformat()))
    file_name = title + ".xlsx"
    worksheet_name = str(_('Ex1'))

# - Create an in-memory output file for the new workbook.
    # from https://docs.python.org/3/library/tempfile.html
    output = tempfile.TemporaryFile()

    return published_instance, output, file_path, filename_ext
# - end of create_published_instance_orderlist


def save_published_instance(published_instance, file_path, output, request):
    # PR2021-09-09
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ============= save_published_instance ============= ')


# +++ save file to disk
    msg_err = None
    try:
        excel_file = File(output)
        published_instance.file.save(file_path, excel_file)

        # published_instance.file.save saves without modifiedby_id. Save again to add modifiedby_id
        published_instance.save(request=request)
    except Exception as e:
        msg_err = getattr(e, 'message', str(e))
        logger.error(msg_err)

    return msg_err
# - end of save_published_instance


def create_final_orderlist_xlsx(output, sel_examyear_instance,
                                department_dictlist, lvlbase_dictlist, subjectbase_dictlist, schoolbase_dictlist,
                                count_dict, requsr_school_name, min_ond, user_lang):  # PR2021-09-09
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_final_orderlist_xlsx -----')
        logger.debug('count_dict: ' + str(count_dict))

    # check for empty count_dict is done outside this function

    msg_err = None
    try:
# ---  create file Name and worksheet Name
        now_formatted = af.format_modified_at(timezone.now(), user_lang, False)  # False = not month_abbrev

# Create an in-memory output file for the new workbook.
        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        #  book = xlsxwriter.Workbook(response, {'in_memory': True})
        book = xlsxwriter.Workbook(output)

# create dict with cell formats
        formats = awpr_excel.create_formats(book)

# ++++++++++++ loop through sheets  ++++++++++++++++++++++++++++
        for ete_duo in ('ETE', 'DUO'):
            for summary_detail in ('overzicht', 'details', 'herexamens'):
                is_herexamens = (summary_detail == 'herexamens')

                if ete_duo in count_dict:
                    ete_duo_dict = count_dict.get(ete_duo)
                    ete_duo_dict_total = ete_duo_dict.get('total')

            # get number of subject columns from DEO/ETE total dict
                    # 'DUO': {'total': {137: 513, 134: 63, 156: 63, 175: 63},
                    # columns are (0: 'schoolbase_code', 1: school_name"
                    # columns 2 etc  are subject columns. Extend number when more than 15 subjects

                    col_count, first_subject_column, col_width, field_names, field_captions, \
                        col_header_formats, detail_row_formats, summary_row_formats, totalrow_formats = \
                            awpr_excel.create_row_formats(subjectbase_dictlist, ete_duo_dict_total, formats)

    # +++++ create worksheet +++++
                    sheet_name = ' '.join((ete_duo, summary_detail))
                    sheet = book.add_worksheet(sheet_name)
                    sheet.hide_gridlines(2) # 2 = Hide screen and printed gridlines

            # --- set column width
                    for i, width in enumerate(col_width):
                        sheet.set_column(i, i, width)

            # --- title row
                    exam_str = summary_detail if (summary_detail == 'herexamens') else 'examens'
                    title = ' '.join(('Bestellijst', ete_duo, exam_str, str(sel_examyear_instance.code)))
                    sheet.write(0, 0, min_ond, formats['bold_format'])
                    sheet.write(1, 0, requsr_school_name)
                    sheet.write(2, 0, now_formatted)

                    row_index = 7
#########################################################################
                    list = 'totals_only'
                    if summary_detail == 'details':
                        awpr_excel.write_orderlist_with_details(
                            sheet, ete_duo_dict, is_herexamens, department_dictlist, lvlbase_dictlist, schoolbase_dictlist,
                            row_index, col_count, first_subject_column, list, title, field_names, field_captions,
                            formats, col_header_formats, detail_row_formats,
                            totalrow_formats)
                    else:
                        awpr_excel.write_orderlist_summary(
                            sheet, ete_duo_dict, is_herexamens, department_dictlist, lvlbase_dictlist, schoolbase_dictlist,
                            row_index, col_count, first_subject_column, list, title, field_names, field_captions,
                            formats, col_header_formats, detail_row_formats,
                            totalrow_formats)
#########################################################################
        book.close()

    # Rewind the buffer.
        # seek(0) sets the pointer position at 0.
        output.seek(0)

    except Exception as e:
        msg_err = getattr(e, 'message', str(e))
        logger.error(msg_err)

    return msg_err
# - end of create_final_orderlist_xlsx


#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
def create_final_orderlist_perschool_xlsx(output, sel_examyear_instance,
                                department_dictlist, lvlbase_dictlist, subjectbase_dictlist, count_dict,
                                subjbasepk_inuse_dict, school_code, school_name, requsr_school_name, min_ond, user_lang):  # PR2021-09-10
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_final_orderlist_perschool_xlsx -----')
        logger.debug('count_dict: ' + str(count_dict))

    msg_err = None
    try:
# ---  create file Name and worksheet Name
        now_formatted = af.format_modified_at(timezone.now(), user_lang, False)  # False = not month_abbrev

# Create an in-memory output file for the new workbook.
        # Even though the final file will be in memory the module uses temp
        # files during assembly for efficiency. To avoid this on servers that
        # don't allow temp files, for example the Google APP Engine, set the
        # 'in_memory' Workbook() constructor option as shown in the docs.
        #  book = xlsxwriter.Workbook(response, {'in_memory': True})
        book = xlsxwriter.Workbook(output)

# create dict with cell formats
        formats = awpr_excel.create_formats(book)
        # subjbasepk_inuse_dict contains subjectsa in use by thisschool, in format of ete_duo_dict_total
        ete_duo_dict_total = subjbasepk_inuse_dict
        col_count, first_subject_column, col_width, field_names, field_captions, \
            col_header_formats, detail_row_formats, summary_row_formats, totalrow_formats = \
                awpr_excel.create_row_formats(subjectbase_dictlist, ete_duo_dict_total, formats)

# +++++ create worksheet +++++
        sheet_name = ' '.join((str(_('Orderlist')), str(_('Exams')).lower()))
        sheet = book.add_worksheet(sheet_name)
        sheet.hide_gridlines(2) # 2 = Hide screen and printed gridlines

# --- set column width
        for i, width in enumerate(col_width):
            sheet.set_column(i, i, width)

# --- title row
        title = ' '.join(('Bestelling examens', str(sel_examyear_instance.code), ' - ', school_code, school_name))
        sheet.write(0, 0, min_ond, formats['bold_format'])
        sheet.write(1, 0, requsr_school_name)

        sheet.write(3, 0, title, formats['bold_format'])
        sheet.write(4, 0, now_formatted)

        row_index = 7

#########################################################################
        awpr_excel.write_orderlist_per_school(
            sheet, count_dict, department_dictlist, lvlbase_dictlist,
            row_index, col_count, first_subject_column, title, field_names, field_captions,
            formats, detail_row_formats, totalrow_formats)
#########################################################################
        book.close()

# Rewind the buffer.
        # seek(0) sets the pointer position at 0.
        output.seek(0)

    except Exception as e:
        msg_err = getattr(e, 'message', str(e))
        logger.error(msg_err)

    return msg_err
# - end of create_final_orderlist_perschool_xlsx
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@method_decorator([login_required], name='dispatch')
class ExamyearCopyToSxmView(View):  # PR2021-08-06

    def post(self, request):
        logging_on = s.LOGGING_ON

        update_wrap = {}
        error_list = []
        SXM_added_list = []
        if request.user is not None and request.user.country is not None:
            req_usr = request.user
            permit_list, requsr_usergroups_list = acc_view.get_userpermit_list('page_examyear', req_usr)
            has_permit = 'permit_crud' in permit_list

            if logging_on:
                logger.debug(' ')
                logger.debug(' ============= ExamyearCopyToSxmView ============= ')
                logger.debug('permit_list: ' + str(permit_list))
                logger.debug('has_permit:  ' + str(has_permit))

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST - upload_dict not in use
            upload_json = request.POST.get('upload', None)
            if has_permit and upload_json:
                # upload_dict = json.loads(upload_json)

# - get examyear_code_int of current examyear
                sel_examyear_code_int = None
                sel_examyear, sel_schoolNIU, sel_departmentNIU, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)
                if sel_examyear:
                    sel_examyear_code_int = sel_examyear.code

# - get examyear curacao with current examyear_code (logged in with SXM gives different examyear_instance)
                curacao_country_instance = af.get_country_instance_by_abbrev('cur')
                curacao_examyear_instance = sch_mod.Examyear.objects.get_or_none(
                    code=sel_examyear_code_int,
                    country=curacao_country_instance
                )
                if logging_on:
                    logger.debug('sel_examyear_code_int: ' + str(sel_examyear_code_int))
                    logger.debug('curacao_country_instance: ' + str(curacao_country_instance))
                    logger.debug('curacao_examyear_instance: ' + str(curacao_examyear_instance))

# - get countr sxm
                sxm_country_instance = af.get_country_instance_by_abbrev('sxm')
                if logging_on:
                    logger.debug('sxm_country_instance: ' + str(sxm_country_instance))

# - get examyear of SXM with  sel_examyear_code_int
                sxm_examyear_instance = sch_mod.Examyear.objects.get_or_none(
                    code=sel_examyear_code_int,
                    country=sxm_country_instance
                )
                if logging_on:
                    logger.debug('sxm_examyear_instance: ' + str(sxm_examyear_instance))

# - create new examyear if it does not exist yet
                if sxm_examyear_instance is None:
                    sxm_examyear_instance, msg_err = create_examyear(sxm_country_instance, sel_examyear.code, request)
                    if msg_err:
                        error_list.append(msg_err)
                    if logging_on:
                        logger.debug('msg_err: ' + str(msg_err))
                        logger.debug('created sxm_examyear_instance: ' + str(sxm_examyear_instance))

                SXM_added_list.append('sxm_examyear_instance: ' + str(sxm_examyear_instance))
                if sxm_examyear_instance:
                    SXM_added_list.append('sxm_examyear_country: ' + str(sxm_examyear_instance.country))

# - copy all tables from current_examyear_instance_instance to new_sxm_examyear_instance
                if curacao_examyear_instance and sxm_examyear_instance:
                    if logging_on:
                        logger.debug('curacao_examyear_instance and sxm_examyear_instance')

                    also_copy_schools = False
                    log_list = []
                    copy_tables_from_last_year(curacao_examyear_instance, sxm_examyear_instance, also_copy_schools, log_list, request)

        update_wrap['error_list'] = error_list
        update_wrap['SXM_added_list'] = SXM_added_list


# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of ExamyearCopyToSxmView

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@method_decorator([login_required], name='dispatch')
class CopySchemesFromExamyearView(View):  # PR2021-09-24

    def post(self, request):
        logging_on = s.LOGGING_ON

        update_wrap = {}
        log_list = []
        if request.user is not None and request.user.country is not None:
            req_usr = request.user
            permit_list, requsr_usergroups_list = acc_view.get_userpermit_list('page_examyear', req_usr)
            has_permit = 'permit_crud' in permit_list and request.user.is_role_system

            if logging_on:
                logger.debug(' ')
                logger.debug(' ============= CopySchemesFromExamyearView ============= ')
                logger.debug('permit_list: ' + str(permit_list))
                logger.debug('has_permit:  ' + str(has_permit))

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if has_permit and upload_json:
                upload_dict = json.loads(upload_json)
                if logging_on:
                    logger.debug('upload_dict: ' + str(upload_dict))
                """
                upload_dict: {'mode': 'copy_scheme', 'copyto_mapid': 'examyear_64', 'copyto_examyear_pk': 64, 'copyto_country_id': 2, 'copyto_country': 'Sint Maarten'}
                """

                copyto_examyear_pk = upload_dict.get('copyto_examyear_pk')

# - get copyfrom_examyear  - which is the current examyear
                copyfrom_examyear_instance, sel_schoolNIU, sel_departmentNIU, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

                if logging_on:
                    logger.debug('copyfrom_examyear_instance: ' + str(copyfrom_examyear_instance) + ' ' + str(copyfrom_examyear_instance.country.abbrev))

# - get copyto_examyear from upload_dict
                copyto_examyear_instance = sch_mod.Examyear.objects.get_or_none(
                    pk=copyto_examyear_pk
                )
                if logging_on:
                    logger.debug('copyto_examyear_instance: ' + str(copyto_examyear_instance) + ' ' + str(copyto_examyear_instance.country.abbrev))

# - copy all tables from current_examyear_instance_instance to new_copyto_examyear_instance, except for schools
                if copyfrom_examyear_instance and copyto_examyear_instance:

# - create log_list
                    today_dte = af.get_today_dateobj()
                    today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)

                    log_list = [c.STRING_DOUBLELINE_80,
                                str(_('Copy subject schemes ')) + ' ' + str(_('date')) + ': ' + str(
                                    today_formatted),
                                c.STRING_DOUBLELINE_80]
                    from_examyear = ' '.join((str(_("From exam year:")), copyfrom_examyear_instance.country.name, str(copyfrom_examyear_instance.code)))
                    to_examyear = ' '.join((str(_("To exam year:  ")), copyto_examyear_instance.country.name, str(copyto_examyear_instance.code)))
                    log_list.append(c.STRING_SPACE_05 + from_examyear)
                    log_list.append(c.STRING_SPACE_05 + to_examyear)

                    also_copy_schools = False
                    copy_tables_from_last_year(copyfrom_examyear_instance, copyto_examyear_instance, also_copy_schools, log_list, request)

        if logging_on:
            logger.debug('log_list: ' + str(log_list) )
        update_wrap['log_list'] = log_list


# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of CopySchemesFromExamyearView

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@method_decorator([login_required], name='dispatch')
class ExamyearDeleteSubjectsFromSxmView(View):  # PR2021-08-06

    def post(self, request):
        logging_on = s.LOGGING_ON

        update_wrap = {}
        error_list = []
        SXM_deletedlist = []
        if request.user is not None and request.user.country is not None:
            req_usr = request.user
            permit_list, requsr_usergroups_list = acc_view.get_userpermit_list('page_examyear', req_usr)
            # only admin of system may do this
            has_permit = (req_usr.role == c.ROLE_128_SYSTEM and requsr_usergroups_list and 'admin' in requsr_usergroups_list)

            # DISABLE THIS FUNCTION,it will remove all students and subjects of SXM
            # has_permit = False
            if logging_on:
                logger.debug(' ')
                logger.debug(' ============= ExamyearDeleteSubjectsFromSxmView ============= ')
                logger.debug('has_permit: ' + str(has_permit))

# - reset language
            user_lang = req_usr.lang if req_usr.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST - upload_dict not in use
            upload_json = request.POST.get('upload', None)
            if has_permit and upload_json:
                upload_dict = json.loads(upload_json)
                if logging_on:
                    logger.debug('upload_dict: ' + str(upload_dict))
                    # upload_dict: {'mode': 'delete_subjects_from_sxm', 'examyear_code': 2022}

# - get current examyear and check if it is SXM and user country is also SXM
                sxm_examyear_instance = None
                sel_examyear, sel_schoolNIU, sel_departmentNIU, may_edit, msg_list = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

                if sel_examyear:
                    sel_country = sel_examyear.country

                    if sel_country and req_usr.country == sel_country:
                        if sel_country.abbrev and sel_country.abbrev.lower() == 'sxm':
                            sxm_examyear_instance = sel_examyear

                SXM_deletedlist.append('sxm_examyear_instance: ' + str(sxm_examyear_instance))
                if sxm_examyear_instance:
                    SXM_deletedlist.append('sxm_examyear_country: ' + str(sxm_examyear_instance.country))

                if sxm_examyear_instance:

# +++ Delete all students of this SXM examyear
                    # - first make sure that no sudsubjects exist
                    # relationship studsubj - subj is PROTECT, but better safe than sorry
                    students = stud_mod.Student.objects.filter(
                        school__examyear=sxm_examyear_instance
                    )
                    for student in students:
                        sch_mod.delete_instance(student, msg_list, error_list, request, '', '')
                        SXM_deletedlist.append('deleted student: ' + str(student))

# +++ Delete all subjects of this SXM examyear
                    subjects = subj_mod.Subject.objects.filter(
                        examyear=sxm_examyear_instance
                    )
                    for subject in subjects:
                        sch_mod.delete_instance(subject, msg_list, error_list, request, '', '')
                        SXM_deletedlist.append('deleted subject: ' + str(subject))

# +++ Delete all departments of this SXM examyear
                    # relationship with Published - CASCADE, PrivateDocument=CASCADE, Scheme=CASCADE,
                    # relationship with student=PROTECT Exam=PROTECT Cluster=PROTECT
                    # relationship scheme - lvl is CASCADE, so also schemes, schemitems and subjecttypes will be deleted
                    departments = sch_mod.Department.objects.filter(
                        examyear=sxm_examyear_instance
                    )
                    for department in departments:
                        sch_mod.delete_instance(department, msg_list, error_list, request, '', '')
                        SXM_deletedlist.append('deleted subject: ' + str(department))

# +++ Delete all level of this SXM examyear
                    # relationship with student=SET_NULL Exam=SET_NULL
                    # relationship scheme=CASCADE, so also schemes, schemitems and subjecttypes will be deleted
                    levels = subj_mod.Level.objects.filter(
                        examyear=sxm_examyear_instance
                    )
                    for level in levels:
                        sch_mod.delete_instance(level, msg_list, error_list, request, '', '')
                        SXM_deletedlist.append('deleted level: ' + str(level))

# +++ Delete all sectors of this SXM examyear
                    # relationship scheme - sct is CASCADE, so also schemes, schemitems and subjecttypes will be deleted
                    sectors = subj_mod.Sector.objects.filter(
                        examyear=sxm_examyear_instance
                    )
                    for sector in sectors:
                        sch_mod.delete_instance(sector, msg_list, error_list, request, '', '')
                        SXM_deletedlist.append('deleted sector: ' + str(sector))
        update_wrap['SXM_deletedlist'] = SXM_deletedlist
        update_wrap['error_list'] = error_list

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of ExamyearDeleteSubjectsFromSxmView



# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_examyear(country, examyear_code_int, request):
    # --- create examyear # PR2019-07-30 PR2020-10-05 PR2021-07-14 PR2021-08-21
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_examyear ----- ')
        logger.debug('examyear_code_int: ' + str(examyear_code_int) + ' ' + str(type(examyear_code_int)))

    instance = None
    msg_err = None
    if country and examyear_code_int:

# - create and save examyear
        try:
            instance = sch_mod.Examyear(
                country=country,
                code=examyear_code_int,
                createdat=timezone.now()
            )
            instance.save(request=request)
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            caption = _('Exam year')
            name = str(examyear_code_int) if examyear_code_int else '---'
            msg_err = str(_('An error occurred.')) + ' ' + \
                      str(_("%(caption)s '%(val)s' could not be created.") % {'caption': caption, 'val': name})

    return instance, msg_err
# - end of create_examyear


def update_examyear(instance, upload_dict, msg_list, request):
    # --- update existing examyear instance PR2019-06-06 PR2021-09-03
    # add new values to update_dict (don't reset update_dict, it has values)
    logger.debug(' ------- update_examyear -------')
    logger.debug('upload_dict: ' + str(upload_dict))
    logger.debug('instance: ' + str(instance))

    # FIELDS_EXAMYEAR = ('country', 'examyear', 'published', 'locked',
    #                   'createdat', 'publishedat', 'lockedat', 'modifiedby', 'modifiedat')
    # order_extra_fixed, order_extra_perc, order_round_to, order_tv2_divisor, order_tv2_max, order_tv2_multiplier

    # upload_dict: {'table': 'examyear', 'country_pk': 1, 'examyear_pk': 58, 'mapid': 'examyear_58', 'mode': 'update', 'published': True}

    updated = False
    if instance:
        try:
            save_changes = False
            for field in upload_dict:
                logger.debug('field: ' + str(field))

                if field in ('table', 'mode', 'mapid',):
                    pass
# --- update field 'examyear' is not allowed
                elif field == 'examyear':
                    pass

# --- update field 'published', 'locked'
                elif field in ('published', 'locked', 'no_practexam', 'sr_allowed', 'no_centralexam', 'no_thirdperiod'):
                    new_value = upload_dict.get(field)
                    saved_value = getattr(instance, field)

                    logger.debug('new_value: ' + str(new_value))

                    if new_value is None:
                        new_value = False
                    logger.debug('field]: ' + str(field) + ' ' + str(type(field)))
                    logger.debug('new_value: ' + str(new_value) + ' ' + str(type(new_value)))
                    logger.debug('saved_value: ' + str(saved_value) + ' ' + str(type(saved_value)))
                    if new_value != saved_value:
                        setattr(instance, field, new_value)
                        save_changes = True
                        logger.debug('save_changes]: ' + str(save_changes) + ' ' + str(type(save_changes)))

                        if field in ('published', 'locked'):
                            # timezone.now() is timezone aware, based on the USE_TZ setting; datetime.now() is timezone naive. PR2018-06-07
                            new_date = timezone.now()
                            date_field = field + 'at'
                            setattr(instance, date_field, new_date)

                    # --- update fieldpython manage.py runserver
                    # 'published', 'locked'
                elif field in ('order_extra_fixed', 'order_extra_perc', 'order_round_to',
                               'order_tv2_divisor', 'order_tv2_multiplier', 'order_tv2_max',
                               'order_admin_divisor', 'order_admin_multiplier', 'order_admin_max'):
                    new_value = upload_dict.get(field)
                    saved_value = getattr(instance, field)

                    logger.debug('new_value: ' + str(new_value))
                    logger.debug('saved_value: ' + str(saved_value))
                    if new_value is None:
                        if field in ('order_round_to', 'order_tv2_divisor'):
                            new_value = 1
                        else:
                            new_value = 0

                    if new_value != saved_value:
                        setattr(instance, field, new_value)
                        save_changes = True
# --- end of for loop ---

# --- save changes
            if save_changes:
                instance.save(request=request)
                updated = True

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            msg_html = ''.join((
                str(_('An error occurred')), ': ', '<br><i>', str(e), '</i><br>',
                str(_("The changes have not been saved."))))
            msg_dict = {'header': str(_('Update exam year')), 'class': 'border_bg_invalid','msg_html': msg_html}
            msg_list.append(msg_dict)
    return updated
# - end of update_examyear

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def copy_tables_from_last_year(prev_examyear_instance, new_examyear_instance, also_copy_schools, log_list, request):
    # --- copy_tables_from_last_year # PR2019-07-30 PR2020-10-05 PR2021-04-25 PR2021-08-06
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_tables_from_last_year -------')
        logger.debug('prev_examyear_instance: ' + str(prev_examyear_instance) + '' + str(prev_examyear_instance.country.abbrev))
        logger.debug('new_examyear_instance: ' + str(new_examyear_instance) + '' + str(new_examyear_instance.country.abbrev))

    if new_examyear_instance and prev_examyear_instance:

        sf.copy_examyear_from_prev_examyear(request, prev_examyear_instance, new_examyear_instance, log_list)

        sf.copy_exfilestext_from_prev_examyear(request, prev_examyear_instance, new_examyear_instance, log_list)

        mapped_deps = sf.copy_deps_from_prev_examyear(request, prev_examyear_instance, new_examyear_instance, log_list)

        if also_copy_schools:
            sf.copy_schools_from_prev_examyear(request, prev_examyear_instance, new_examyear_instance, log_list)

        mapped_levels = sf.copy_levels_from_prev_examyear(request, prev_examyear_instance, new_examyear_instance, log_list)
        mapped_sectors = sf.copy_sectors_from_prev_examyear(request, prev_examyear_instance, new_examyear_instance, log_list)

        mapped_schemes = sf.copy_schemes_from_prev_examyear(request, prev_examyear_instance, mapped_deps, mapped_levels, mapped_sectors, log_list)

        mapped_subjecttypes = sf.copy_subjecttypes_from_prev_examyear(request, prev_examyear_instance, mapped_schemes, log_list)
        mapped_subjects = sf.copy_subjects_from_prev_examyear(request, prev_examyear_instance, new_examyear_instance, log_list)
        mapped_schemeitems = sf.copy_schemeitems_from_prev_examyear(request, prev_examyear_instance, mapped_schemes, mapped_subjects, mapped_subjecttypes, log_list)
        mapped_packages = sf.copy_packages_from_prev_examyear(request, prev_examyear_instance, mapped_schemes, log_list)
        sf.copy_packageitems_from_prev_examyear(request, prev_examyear_instance, mapped_packages, mapped_schemeitems, log_list)

        # these tables are not copied:
        # Exam
        # Norm
        # School_message
        # Published
        # PrivateDocument
        # Entrylist
        # Schoolsetting
        # Cluster
        # Birthcountry
        # Birthplace
        # Student
        # Result
        # Resultnote
        # Studentsubject
        # Studentsubjectnote
        # Noteattachment
        # Grade

# end of copy_tables_from_last_year

# === School =====================================
@method_decorator([login_required], name='dispatch')
class SchoolListView(View):  # PR2018-08-25 PR2020-10-21 PR2021-03-25

    def get(self, request):
        #logger.debug('  =====  SchoolListView ===== ')

# - get headerbar parameters
        page = 'page_school'
        display_school = True  #(request and request.user and request.user.role <= c.ROLE_008_SCHOOL)
        display_department = False
        param = {'display_school': display_school, 'display_department': display_department}
        headerbar_param = awpr_menu.get_headerbar_param(request, page, param)

        return render(request, 'schools.html', headerbar_param)


@method_decorator([login_required], name='dispatch')
class SchoolUploadView(View):  # PR2020-10-22 PR2021-03-27

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= SchoolUploadView ============= ')

        messages = []
        update_wrap = {}
        if request.user and request.user.country and request.user.schoolbase:

# - get permit
            has_permit = False
            req_usr = request.user
            if req_usr and req_usr.country and req_usr.schoolbase:
                permit_list = req_usr.permit_list('page_school')
                if permit_list:
                    has_permit = 'permit_crud' in permit_list
                if logging_on:
                    logger.debug('permit_list: ' + str(permit_list))
                    logger.debug('has_permit: ' + str(has_permit))

            if has_permit:

# - reset language
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

# --- get upload_dict from request.POST
                upload_json = request.POST.get('upload', None)
                if upload_json:
                    upload_dict = json.loads(upload_json)

# --- get variables from upload_dict PR2020-12-25
                    school_pk = upload_dict.get('school_pk')
                    mode = upload_dict.get('mode')
                    is_create = (mode == 'create')
                    is_delete = (mode == 'delete')

                    message_header = _('Delete school') if is_delete \
                                else _('Create school') if is_create \
                                else _('Update school')

                    school_dict = {}
                    error_dict = {}

                    if logging_on:
                        logger.debug('upload_dict' + str(upload_dict))
                        logger.debug('school_pk: ' + str(school_pk))
                        logger.debug('is_create: ' + str(is_create))
                        logger.debug('is_delete: ' + str(is_delete))

# - get selected examyear from Usersetting
                    selected_dict = acc_view.get_usersetting_dict(c.KEY_SELECTED_PK, request)
                    selected_examyear_pk = selected_dict.get(c.KEY_SEL_EXAMYEAR_PK)
                    examyear = None
                    if selected_examyear_pk:
                        examyear = sch_mod.Examyear.objects.get_or_none(
                            id=selected_examyear_pk,
                            country=request.user.country
                        )

# - exit when no examyear or examyear is locked
                    # note: subjects may be changed before publishing, therefore don't exit on examyear.published
                    if examyear is None:
                        messages.append({'class': "border_bg_warning",
                                         'header': str(message_header),
                                         'msg_html': str(_('No exam year selected'))})
                    elif examyear.locked:
                        messages.append({'class': "border_bg_warning",
                                         'header': str(message_header),
                                         'msg_html': str(
                                             _("Exam year %(exyr)s is locked.") % {'exyr': str(examyear.code)})
                                         })
                    else:
# +++ Delete school
                        if is_delete:
                            school = sch_mod.School.objects.get_or_none(id=school_pk)
                            if logging_on:
                                logger.debug('school: ' + str(school))

                            if school:
                                this_text = _("School '%(tbl)s' ") % {'tbl': school.name}
                                # a. TODO check if school has child rows, put msg_err in update_dict when error
                                msg_err = None  # validate_employee_has_emplhours(employee)
                                if msg_err:
                                    # error_dict['error'] = msg_err
                                    pass
                                else:
                                    # b. check if there are teammembers with this employee: absence teammembers, remove employee from shift teammembers
                                    # delete_employee_from_teammember(employee, request)
                                    # c. delete school
                                    # format of error_list: [err_str1, err_str2]
                                    # TODO msg and err not correct
                                    err_list = []
                                    deleted_ok = sch_mod.delete_instance(school, messages, err_list, request, this_text)
                                    if deleted_ok:
                                        # - add deleted_row to school_rows
                                        school_dict.update({'pk': school_pk,
                                                            'table': 'school',
                                                            'mapid': 'school_' + str(school_pk),
                                                            'deleted': True})
                                        school = None

# +++ Create new school
                        if is_create:

                            school = create_school_instance(examyear, upload_dict, error_dict, request)
                            if school:
                                school_dict['created'] = True

                            if logging_on:
                                logger.debug('school: ' + str(school))

    # --- get existing school
                        else:
                            school = sch_mod.School.objects.get_or_none(id=school_pk)

                        if school:
# --- Update school, also when it is created. When deleted: school is None
                        #  Not necessary when created. Most fields are required. All fields are saved in create_school_instance

                            saved_ok = update_school_instance(school, upload_dict, error_dict, request)
                            if saved_ok:
                                school_dict['updated'] = True

                            permit_dict = {
                                'requsr_role': req_usr.role,
                                'requsr_schoolbase_pk': req_usr.schoolbase_id
                            }
                            school_rows = sch_dicts.create_school_rows(
                                examyear=examyear,
                                permit_dict=permit_dict,
                                school_pk=school.pk
                            )
                            if school_rows:
                                # update appends dict to dict. school_row may have value like 'created = True
                                school_dict.update(school_rows[0])
                    if error_dict:
                        school_dict['error'] = error_dict
                    update_wrap['updated_school_rows'] = [school_dict]

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=LazyEncoder))


@method_decorator([login_required], name='dispatch')
class SchoolImportView(View):  # PR2020-10-01

    def get(self, request):
        param = {}
        has_permit = False
        if request.user is not None and request.user.country is not None and request.user.schoolbase is not None:
            has_permit = True # (request.user.is_perm_planner or request.user.is_perm_hrman)
        if has_permit:
            # coldef_list = [{'tsaKey': 'employee', 'caption': _('Company name')},
            #                      {'tsaKey': 'ordername', 'caption': _('Order name')},
            #                      {'tsaKey': 'orderdatefirst', 'caption': _('First date order')},
            #                      {'tsaKey': 'orderdatelast', 'caption': _('Last date order')} ]

    # get coldef_list  and caption
            coldef_list = c.COLDEF_SUBJECT
            captions_dict = c.CAPTION_IMPORT

            settings_json = request.user.schoolbase.get_schoolsetting_dict(c.KEY_IMPORT_SUBJECT)
            stored_setting = json.loads(settings_json) if settings_json else {}

            # don't replace keyvalue when new_setting[key] = ''
            self.has_header = True
            self.worksheetname = ''
            self.codecalc = 'linked'
            if 'has_header' in stored_setting:
                self.has_header = False if Lower(stored_setting['has_header']) == 'false' else True
            if 'worksheetname' in stored_setting:
                self.worksheetname = stored_setting['worksheetname']
            if 'codecalc' in stored_setting:
                self.codecalc = stored_setting['codecalc']

            if 'coldefs' in stored_setting:
                stored_coldefs = stored_setting['coldefs']
                # skip if stored_coldefs does not exist
                if stored_coldefs:
                    # loop through coldef_list
                    for coldef in coldef_list:
                        # coldef = {'tsaKey': 'employee', 'caption': 'Cliënt'}
                        # get fieldname from coldef
                        fieldname = coldef.get('tsaKey')
                        #logger.debug('fieldname: ' + str(fieldname))

                        if fieldname:  # fieldname should always be present
                            # check if fieldname exists in stored_coldefs
                            if fieldname in stored_coldefs:
                                # if so, add Excel name with key 'excKey' to coldef
                                coldef['excKey'] = stored_coldefs[fieldname]
                                #logger.debug('stored_coldefs[fieldname]: ' + str(stored_coldefs[fieldname]))

            coldefs_dict = {
                'worksheetname': self.worksheetname,
                'has_header': self.has_header,
                'codecalc': self.codecalc,
                'coldefs': coldef_list
            }
            coldefs_json = json.dumps(coldefs_dict, cls=LazyEncoder)

            captions = json.dumps(captions_dict, cls=LazyEncoder)

            param = awpr_menu.get_headerbar_param(request, 'school_import', {'captions': captions, 'setting': coldefs_json})

        # render(request object, template name, [dictionary optional]) returns an HttpResponse of the template rendered with the given context.
        return render(request, 'subjectimport210724.html', param)


@method_decorator([login_required], name='dispatch')
class SchoolImportUploadSetting(View):   # PR2019-03-10
    # function updates mapped fields, no_header and worksheetname in table Companysetting
    def post(self, request, *args, **kwargs):
        #logger.debug(' ============= SubjectImportUploadSetting ============= ')
        #logger.debug('request.POST' + str(request.POST) )
        schoolsetting_dict = {}
        has_permit = False
        if request.user is not None and request.user.schoolbase is not None:
            has_permit = (request.user.is_role_adm_or_sys_and_group_system)
        if has_permit:
            if request.POST['upload']:
                new_setting_json = request.POST['upload']
                # new_setting is in json format, no need for json.loads and json.dumps
                #logger.debug('new_setting_json' + str(new_setting_json))

                new_setting_dict = json.loads(request.POST['upload'])
                settings_key = c.KEY_IMPORT_SUBJECT

                new_worksheetname = ''
                new_has_header = True
                new_code_calc = ''
                new_coldefs = {}

                stored_json = request.user.schoolbase.get_schoolsetting_dict(settings_key)
                if stored_json:
                    stored_setting = json.loads(stored_json)
                    #logger.debug('stored_setting: ' + str(stored_setting))
                    if stored_setting:
                        new_has_header = stored_setting.get('has_header', True)
                        new_worksheetname = stored_setting.get('worksheetname', '')
                        new_code_calc = stored_setting.get('codecalc', '')
                        new_coldefs = stored_setting.get('coldefs', {})

                if new_setting_json:
                    new_setting = json.loads(new_setting_json)
                    #logger.debug('new_setting' + str(new_setting))
                    if new_setting:
                        if 'worksheetname' in new_setting:
                            new_worksheetname = new_setting.get('worksheetname', '')
                        if 'has_header' in new_setting:
                            new_has_header = new_setting.get('has_header', True)
                        if 'coldefs' in new_setting:
                            new_coldefs = new_setting.get('coldefs', {})
                    #logger.debug('new_code_calc' + str(new_code_calc))
                new_setting = {'worksheetname': new_worksheetname,
                               'has_header': new_has_header,
                               'codecalc': new_code_calc,
                               'coldefs': new_coldefs}
                new_setting_json = json.dumps(new_setting)
                request.user.schoolbase.set_schoolsetting_dict(settings_key, new_setting_json)

        return HttpResponse(json.dumps(schoolsetting_dict, cls=LazyEncoder))
# --- end of SubjectImportUploadSetting

@method_decorator([login_required], name='dispatch')
class SchoolImportUploadData(View):  # PR2018-12-04 PR2019-08-05 PR2020-06-04

    def post(self, request):
        #logger.debug(' ========================== SchoolImportUploadData ========================== ')
        params = {}
        has_permit = False
        is_not_locked = False
        if request.user is not None and request.user.schoolbase is not None:
            has_permit = (request.user.is_role_adm_or_sys_and_group_system)
            # TODO change request.user.examyear to sel_examyear
            is_not_locked = not request.user.examyear.locked

        if is_not_locked and has_permit:
            # - Reset language
            # PR2019-03-15 Debug: language gets lost, get request.user.lang again
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                params = import_schools(upload_dict, user_lang, request)

        return HttpResponse(json.dumps(params, cls=LazyEncoder))

# --- end of SubjectImportUploadData


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


@method_decorator([login_required], name='dispatch')
class SchoolAwpUploadView(View):  # PR2021-05-03

    def post(self, request):
        logging_on = s.LOGGING_ON

        files = request.FILES
        file = files.get('file')
        if logging_on:
            logger.debug(' ============= SchoolAwpUploadView ============= ')
            logger.debug('files: ' + str(files) + ' ' + str(type(files)))
            logger.debug('file: ' + str(file) + ' ' + str(type(file)))

        # function creates, deletes and updates studentsubject records of current student PR2020-11-21
        update_wrap = {}

        #<PERMIT>
        # only users with role > student and perm_edit can change student data
        # only school that is requsr_school can be changed
        #   current schoolbase can be different from request.user.schoolbase (when role is insp, admin, system)
        # only if country/examyear/school/student not locked, examyear is published and school is activated
        has_permit = False
        if request.user and request.user.country and request.user.schoolbase:
            has_permit = True # (request.user.role > c.ROLE_002_STUDENT and request.user.is_group_edit)
        if has_permit:

# - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get upload_dict from request.POST
            upload_json = request.POST.get('upload', None)
            if upload_json:
                upload_dict = json.loads(upload_json)
                logger.debug('upload_dict: ' + str(upload_dict))

                # - get selected examyear, school and department from usersettings
                sel_examyear, sel_school, sel_department, is_locked, \
                examyear_published, school_activated, requsr_same_schoolNIU = \
                    dl.get_selected_ey_school_dep_from_usersetting(request)

                file_type = upload_dict.get('file_type')
                file_name = upload_dict.get('file_name')
                file_size = upload_dict.get('file_size')


# 9. return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=LazyEncoder))
# - end of SchoolAwpUploadView

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def create_school_instance(examyear, upload_dict, error_dict, request):
    # --- create school # PR2019-07-30 PR2020-10-22 PR2021-06-20
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_school_instance ----- ')
        logger.debug('examyear: ' + str(examyear))
        logger.debug('upload_dict: ' + str(upload_dict))

    school = None
    if examyear:
# - get value of 'abbrev'
        code = upload_dict.get('code')
        abbrev = upload_dict.get('abbrev')
        name = upload_dict.get('name')
        article = upload_dict.get('article')
        depbases = upload_dict.get('depbases')
        defaultrole = upload_dict.get('defaultrole')
        if logging_on:
            logger.debug('code: ' + str(code))
            logger.debug('abbrev: ' + str(abbrev))
            logger.debug('name: ' + str(name))
            logger.debug('article: ' + str(article))
            logger.debug('depbases: ' + str(depbases) + str(type(depbases)))
            logger.debug('defaultrole: ' + str(defaultrole) + str(type(defaultrole)))

        if abbrev and name and code and defaultrole:
            lookup_value = code
# - validate if code already exists
            schoolbase, school, msg_err_multiple_found = lookup_schoolbase(examyear, lookup_value, request)
            if msg_err_multiple_found is None:
                if schoolbase is not None:
                    if school is not None:
                        error_dict['general'] = [_("School code '%(fld)s' already exists.") % {'fld': lookup_value}]
                    else:
                        error_dict['general'] = [_("School code '%(fld)s' already exists in other exam years.") % {'fld': lookup_value}]
# - if schoolbase exitsts but child school does not exist this examyear: add school

            if logging_on:
                logger.debug('schoolbase: ' + str(schoolbase))
                logger.debug('error_dict: ' + str(error_dict))

# - create and save school
            if error_dict:
                pass
                #error_dict['error_create'] = msg_err
            else:
                try:
                    # First create base record. base.id is used in School. Create also saves new record
                    schoolbase = sch_mod.Schoolbase.objects.create(
                        country=request.user.country,
                        code=code,
                        defaultrole=defaultrole
                    )
                    school = sch_mod.School(
                        base=schoolbase,
                        examyear=examyear,
                        name=name,
                        abbrev=abbrev,
                        article=article,
                        depbases=depbases
                    )
                    school.save(request=request)
                    if logging_on:
                        logger.debug('schoolbase: ' + str(schoolbase))
                        logger.debug('school: ' + str(school))
                except Exception as e:
                    school = None
                    logger.error(getattr(e, 'message', str(e)))
                    msg_err = str(_("An error occurred. School '%(val)s' could not be added.") % {'val': name})
                    error_dict['error_create'] = msg_err

    return school
# - end of create_school_instance

#######################################################
def update_school_instance(instance, upload_dict, err_dict, request):
    # --- update existing and new instance PR2019-06-06 PR2021-05-13
    # add new values to update_dict (don't reset update_dict, it has values)
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_school_instance -------')
        logger.debug('upload_dict' + str(upload_dict))

    # upload_dict = {id: {table: "school", ppk: 1, pk: 1, mapid: "school_1"},
    #                depbases: {value: Array(1), update: true} }

    # format of error_list: [err_str1, err_str2]
    saved_ok = False
    if instance:
        save_changes = False
        save_parent = False
        schoolbase = instance.base
        for field, new_value in upload_dict.items():

            if field == 'code':
                saved_value = getattr(schoolbase, field)
                if new_value and new_value != saved_value:
                    # TODO validate_code_name_id checks for null, too long and exists. Puts err_msg in update_dict
                    #err_msg = av.validate_code_name_identifier()
                    #err_dict[field] = [err_msg]
                    setattr(schoolbase, field, new_value)
                    save_parent = True

            elif field == 'defaultrole':
                saved_value = getattr(schoolbase, field)
                if new_value and new_value != saved_value:
                    setattr(schoolbase, field, new_value)
                    save_parent = True

            elif field in ['name', 'abbrev']:
                saved_value = getattr(instance, field)
                if new_value and new_value != saved_value:
                    # TODO validate_code_name_id checks for null, too long and exists. Puts err_msg in update_dict
                    # err_msg = validate_code_name_identifier(
                    err_msg = None
                    if not err_msg:
                        setattr(instance, field, new_value)
                        save_changes = True
                    else:
                        err_dict[field] = [err_msg]

            elif field in('article', 'otherlang'):
                saved_value = getattr(instance, field)
                # article / otherlang can be None
                if new_value != saved_value:
                    setattr(instance, field, new_value)
                    save_changes = True

# 3. save changes in depbases
            elif field == 'depbases':
                saved_value = getattr(instance, field)
                # depbases is string:  "1;2;3", sorted, otherwise "1;2;3" and "3;1;2" will not be equal
                new_value = '' if new_value is None else new_value
                saved_value = '' if saved_value is None else saved_value
                if new_value != saved_value:
                    setattr(instance, field, new_value)
                    save_changes = True

# 4. save changes in boolean fields
            elif field in ['activated', 'locked', 'isdayschool', 'iseveningschool', 'islexschool', 'no_order']:
                saved_value = getattr(instance, field)
                new_value = False if new_value is None else new_value

                if new_value != saved_value:
                    setattr(instance, field, new_value)
                    save_changes = True

                    # set time modified if new_value = True, remove time modified when new_value = False
                    mod_at_field = None
                    if field == 'activated':
                        mod_at_field = 'activatedat'
                    elif field == 'locked':
                        mod_at_field = 'lockedat'
                    if mod_at_field:
                        mod_at = timezone.now() if new_value else None
                        setattr(instance, mod_at_field, mod_at)

                if logging_on:
                    logger.debug('----- field:  ' + str(field))
                    logger.debug('new_value:    ' + str(new_value) + ' ' + str(type(new_value)))
                    logger.debug('saved_value:  ' + str(saved_value) + ' ' + str(type(saved_value)))
                    logger.debug('save_changes: ' + str(save_changes))
                    logger.debug('save_parent:  ' + str(save_parent))

# --- end of for loop ---

# 5. save changes
        if save_parent:
            try:
                schoolbase = instance.base
                schoolbase.save()
                if logging_on:
                    logger.debug('parent changes saved')
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                err_dict['general'] = [_('An error occurred: ') + str(e),  _('The changes have not been saved.')]
                saved_ok = False
            else:
                saved_ok = True
        if save_changes:
            try:
                instance.save(request=request)
                if logging_on:
                    logger.debug('instance changes saved')
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))
                err_dict['general'] = [_('An error occurred: ') + str(e),  _('The changes have not been saved.')]
                saved_ok = False
            else:
                saved_ok = True
    return saved_ok
# - -end of update_school_instance
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>



def import_schools(upload_dict, user_lang, request):

    #logger.debug(' -----  import_schools ----- ')
    #logger.debug('upload_dict: ' + str(upload_dict))
# - get is_test, codecalc, dateformat, awpKey_list
    is_test = upload_dict.get('test', False)
    awpKey_list = upload_dict.get('awpKey_list')
    dateformat = upload_dict.get('dateformat', '')

    params = {}
    if awpKey_list:
# - get lookup_field
        # lookup_field is field that determines if employee alreay exist.
        # check if one of the fields 'payrollcode', 'identifier' or 'code' exists
        # first in the list is lookup_field
        lookup_field = 'code'

# - get upload_dict from request.POST
        school_list = upload_dict.get('schools')
        if school_list:

            today_dte = af.get_today_dateobj()
            today_formatted = af.format_WDMY_from_dte(today_dte, user_lang)
            double_line_str = '=' * 80
            indent_str = ' ' * 5
            space_str = ' ' * 30
            logfile = []
            logfile.append(double_line_str)
            logfile.append( '  ' + str(request.user.schoolbase.code) + '  -  ' +
                            str(_('Import schools')) + ' ' + str(_('date')) + ': ' + str(today_formatted))
            logfile.append(double_line_str)

            if lookup_field is None:
                info_txt = str(_('There is no field given to lookup schools. Schools cannot be uploaded.'))
                logfile.append(indent_str + info_txt)
            else:
                if is_test:
                    info_txt = str(_("This is a test. The school data are not saved."))
                else:
                    info_txt = str(_("The school data are saved."))
                logfile.append(indent_str + info_txt)
                lookup_caption = str(get_field_caption('school', lookup_field))
                info_txt = str(_("Schools are looked up by the field: '%(fld)s'.") % {'fld': lookup_caption})
                logfile.append(indent_str + info_txt)
                #if dateformat:
                #    info_txt = str(_("The date format is: '%(fld)s'.") % {'fld': dateformat})
                #    logfile.append(indent_str + info_txt)
                update_list = []
                for school_dict in school_list:
                    # from https://docs.quantifiedcode.com/python-anti-patterns/readability/not_using_items_to_iterate_over_a_dictionary.html

                    update_dict = upload_school_NIU(school_list, school_dict, lookup_field,
                                                 awpKey_list, is_test, dateformat, indent_str, space_str, logfile, request)
                    # json_dumps_err_list = json.dumps(msg_list, cls=f.LazyEncoder)
                    if update_dict:  # 'Any' returns True if any element of the iterable is true.
                        update_list.append(update_dict)

                if update_list:  # 'Any' returns True if any element of the iterable is true.
                    params['school_list'] = update_list
            if logfile:  # 'Any' returns True if any element of the iterable is true.
                params['logfile'] = logfile
                        # params.append(new_employee)
    return params


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def upload_school_NIU(school_list, school_dict, lookup_field, awpKey_list,
                   is_test, dateformat, indent_str, space_str, logfile, request):  # PR2019-12-17 PR2020-10-21
    #logger.debug('----------------- import school  --------------------')
    #logger.debug(str(school_dict))
    # awpKeys are: 'code', 'name', 'sequence', 'depbases'

# - get index and lookup info from school_dict
    row_index = school_dict.get('rowindex', -1)
    new_code = school_dict.get('code')
    new_name = school_dict.get('name')
    new_sequence = school_dict.get('sequence')
    new_depbases = school_dict.get('depbases')

# - create update_dict
    update_dict = {'id': {'table': 'school', 'rowindex': row_index}}

# - give row_error when lookup went wrong
    # multiple_found and value_too_long return the lookup_value of the error field

    lookup_field_caption = str(get_field_caption('school', lookup_field))
    lookup_field_capitalized = '-'
    if lookup_field_caption:
        lookup_field_capitalized = lookup_field_caption.capitalize()
    is_skipped_str = str(_("is skipped."))
    skipped_str = str(_("Skipped."))
    logfile.append(indent_str)
    msg_err = None
    log_str = ''

    schoolbase = None
    school = None

# check if lookup_value has value ( lookup_field = 'code')
    lookup_value = school_dict.get(lookup_field)
    if not lookup_value:
        log_str = str(_("No value for lookup field: '%(fld)s'.") % {'fld': lookup_field_caption})
        msg_err = ' '.join((skipped_str, log_str))

# check if lookup_value is not too long
    elif len(lookup_value) > c.MAX_LENGTH_SCHOOLCODE:
        value_too_long_str = str(_("Value '%(val)s' is too long.") % {'val': lookup_value})
        max_str = str(_("Max %(fld)s characters.") % {'fld': c.MAX_LENGTH_SCHOOLCODE})
        log_str = value_too_long_str + ' ' + max_str
        msg_err = ' '.join((skipped_str, value_too_long_str, max_str))

# check if new_name has value
    elif new_name is None:
        field_caption = str(get_field_caption('school', 'name'))
        log_str = str(_("No value for required field: '%(fld)s'.") % {'fld': field_caption})
        msg_err = ' '.join((skipped_str, log_str))

# check if school name  is not too long
    elif len(new_name) > c.MAX_LENGTH_NAME:
        value_too_long_str = str(_("Value '%(val)s' is too long.") % {'val': lookup_value})
        max_str = str(_("Max %(fld)s characters.") % {'fld': c.MAX_LENGTH_NAME})
        log_str = value_too_long_str + ' ' + max_str
        msg_err = ' '.join((skipped_str, value_too_long_str, max_str))
    else:

# - check if lookup_value occurs mutiple times in Excel file
        excel_list_multiple_found = False
        excel_list_count = 0
        for dict in school_list:
            value = dict.get(lookup_field)
            if value and value == lookup_value:
                excel_list_count += 1
            if excel_list_count > 1:
                excel_list_multiple_found = True
                break
        if excel_list_multiple_found:
            log_str = str(_("%(fld)s '%(val)s' is not unique in Excel file.") % {'fld': lookup_field_capitalized, 'val': lookup_value})
            msg_err = ' '.join((skipped_str, log_str))

    if msg_err is None:

# - check if schoolbase with this code exists in request.user.country. schoolbase has value when only one found
        # lookup_value = school_dict.get(lookup_field)

        schoolbase, school, msg_err_multiple_found = lookup_schoolbase(lookup_value, request)
        if msg_err_multiple_found:
            log_str = msg_err_multiple_found
            msg_err = msg_err_multiple_found

    code_text = (new_code + space_str)[:30]

# - if error: put msg_err in update_dict and logfile
    if msg_err:
        update_dict['row_error'] = msg_err
        update_dict[lookup_field] = {'error': msg_err}
        logfile.append(code_text + is_skipped_str)
        logfile.append(' ' * 30 + log_str)
    else:

# - create new schoolbase when schoolbase not found in database
        if schoolbase is None:
            try:
                schoolbase = sch_mod.Schoolbase(
                    country=request.user.country,
                    code=new_code
                )
                if schoolbase:
                    schoolbase.save()
            except:
# - give error msg when creating schoolbase failed
                error_str = str(_("An error occurred. The school is not added."))
                logfile.append(" ".join((code_text, error_str )))
                update_dict['row_error'] = error_str

        if schoolbase :
# - create new school when school not found in database
            is_existing_school = False
            save_instance = False

            if school is None:
                try: # TODO change request.user.examyear to sel_examyear
                    school = sch_mod.School(
                        base=schoolbase,
                        examyear=request.user.examyear,
                        name=new_name
                    )
                    if school:
                        school.save(request=request)
                        update_dict['id']['created'] = True
                        logfile.append(code_text + str(_('is added.')))
                except:
    # - give error msg when creating school failed
                    error_str = str(_("An error occurred. The school is not added."))
                    logfile.append(" ".join((code_text, error_str )))
                    update_dict['row_error'] = error_str
            else:
                is_existing_school = True
                logfile.append(code_text + str(_('already exists.')))

            if school:
                # add 'id' at the end, after saving the school. Pk doent have value until instance is saved
                #update_dict['id']['pk'] = school.pk
                #update_dict['id']['ppk'] = school.company.pk
                #if school:
                #    update_dict['id']['created'] = True

                # PR2020-06-03 debug: ... + (list_item) gives error: must be str, not __proxy__
                # solved bij wrapping with str()

                blank_str = '<' + str(_('blank')) + '>'
                was_str = str(_('was') + ': ')
                # FIELDS_schoolS = ('base', 'examyear', 'name', 'abbrev', 'sequence', 'depbases', 'modifiedby', 'modifiedat')
                for field in ('name', 'abbrev', 'sequence', 'depbases'):
                    # --- get field_dict from  upload_dict  if it exists
                    if field in awpKey_list:
                        #('field: ' + str(field))
                        field_dict = {}
                        field_caption = str(get_field_caption('school', field))
                        caption_txt = (indent_str + field_caption + space_str)[:30]

                        if field in ('code', 'name', 'namefirst', 'email', 'address', 'city', 'country'):
                            if field == 'code':
                                # new_code is created in this function and already checked for max_len
                                new_value = new_code
                            else:
                                new_value = school_dict.get(field)
                # check length of new_value
                            max_len = c.MAX_LENGTH_NAME \
                                if field in ('namelast', 'namefirst', 'email', 'address', 'city', 'country') \
                                else c.MAX_LENGTH_CODE

                            if max_len and new_value and len(new_value) > max_len:
                                msg_err = str(_("'%(val)s' is too long. Maximum is %(max)s characters'.") % {
                                    'val': new_value, 'max': max_len})
                                field_dict['error'] = msg_err
                            else:
                    # - replace '' by None
                                if not new_value:
                                    new_value = None
                                field_dict['value'] = new_value
                                if not is_existing_school:
                                    logfile.append(caption_txt + (new_value or blank_str))
                    # - get saved_value
                                saved_value = getattr(school, field)
                                if new_value != saved_value:
                    # put new value in school instance
                                    setattr(school, field, new_value)
                                    field_dict['updated'] = True
                                    save_instance = True
                    # create field_dict and log
                                    if is_existing_school:
                                        old_value_str = was_str + (saved_value or blank_str)
                                        field_dict['info'] = field_caption + ' ' + old_value_str
                                        update_str = ((new_value or blank_str) + space_str)[:25] + old_value_str
                                        logfile.append(caption_txt + update_str)

                # add field_dict to update_dict
                        update_dict[field] = field_dict

               # dont save data when it is a test run
                #if not is_test and save_instance:
                    #employee.save(request=request)
                    #update_dict['id']['pk'] = employee.pk
                    #update_dict['id']['ppk'] = employee.company.pk
                    # wagerate wagecode
                    # priceratejson additionjson
                    #try:
                        #employee.save(request=request)
                        #update_dict['id']['pk'] = employee.pk
                        #update_dict['id']['ppk'] = employee.company.pk
                    #except:
        # - give error msg when creating employee failed
                        #error_str = str(_("An error occurred. The school data is not saved."))
                        #logfile.append(" ".join((code_text, error_str)))
                        #update_dict['row_error'] = error_str

    return update_dict
# --- end of upload_school_NIU

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def lookup_schoolbase(examyear, lookup_value, request, this_pk=None):  # PR2020-10-22 PR2021-06-20
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----------- lookup_schoolbase ----------- ')
        logger.debug('lookup_value: ' + str(lookup_value) + ' ' + str(type(lookup_value)))

    # function searches for existing schoolbase
    schoolbase = None
    school = None
    msg_err_multiple_found = None
    if lookup_value and request:
# --- check if 'code' exists multiple times in Schoolbase with filter country
        crit = Q(country=request.user.country) & \
               Q(code__iexact=lookup_value)
# --- exclude this record
        if this_pk:
            crit.add(~Q(pk=this_pk), crit.connector)
        row_count = sch_mod.Schoolbase.objects.filter(crit).count()
        if row_count > 1:
            msg_err_multiple_found = _("School code '%(fld)s' is found multiple times.") % {'fld': lookup_value}
        elif row_count == 1:
    # get schoolbase when only one found (get_or_none does not work with Q, is not necessary, use first() instead)
            schoolbase = sch_mod.Schoolbase.objects.filter(crit).first()
            if schoolbase:
    # --- if 1 found: check if it has school this examyear
                crit = Q(base=schoolbase) & Q(examyear=examyear)
                school_count = sch_mod.School.objects.filter(crit).count()
                if school_count > 1:
                    msg_err_multiple_found = _("School code '%(fld)s' is found multiple times in this exam year.") % {'fld': lookup_value}
                elif row_count == 1:
    # get school when only one found (get_or_none does not work with Q, is not necessary, use first() instead)
                    school = sch_mod.School.objects.filter(crit).first()

    return schoolbase, school, msg_err_multiple_found


def lookup_school(schoolbase, request):  # PR2019-12-17 PR2020-10-20
    #logger.debug('----------- lookup_school ----------- ')

    school = None
    multiple_schools_found = False

# - search school by schoolbase and request.user.examyear
    # TODO change request.user.examyear to sel_examyear
    if schoolbase:
        # check if school exists multiple times
        row_count = sch_mod.School.objects.filter(base=schoolbase, examyear=request.user.examyear).count()
        if row_count > 1:
            multiple_schools_found = True
        elif row_count == 1:
            # get school when only one found
            school = sch_mod.School.objects.get_or_none(base=schoolbase, examyear=request.user.examyear)

    return school, multiple_schools_found


def get_field_caption(table, field):
    caption = ''
    if table == 'school':
        if field == 'code':
            caption = _('Short name')
        elif field == 'name':
            caption = _('School name')
        elif field == 'sequence':
            caption = _('Sequence')
        elif field == 'depbases':
            caption = _('Departments')
    return caption

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


# ++++++++++++++++++   VALIDATORS     ++++++++++++++++++++++++++++++++++++++

class Validate_examyear(object):

    @staticmethod  # PR2018-08-14
    def examyear_does_not_exist_in_country(user_country, new_examyear_int):
        # This validation is used when user wants to add a new examyear (only systenm and insp users can add new examyear)
        # It checks if new examyear exists in user.country. Name of examyear is Int type.
        # returns True if examyear.code does not exist in user.country, otherwise False
        _does_not_exist = True
        if user_country is not None:
            if new_examyear_int is not None:
                if not sch_mod.Examyear.objects.filter(country=user_country, code=new_examyear_int).exists():
                    _does_not_exist = True
        return _does_not_exist

    @staticmethod  # PR2018-08-14
    def get_examyear_in_selected_country(country_selected, user_examyear_int):
        # This validation is used when user wants to change user.country (only systenm users can change user.country)
        # It checks if user.examyear exists in selected_country. Returns examyear in selected_country if it exists, otherwise None
        # If it exists: selected_country is OK, if not: delete user.examyear
        if country_selected is None:
            # if country is None: selected_country NOT OK, exit code is outside this function
            _examyear_country_selected = None
        else:
            if user_examyear_int is None:
                # if examyear is None: selected_country OK (examyear is None, no need to delete)
                _examyear_country_selected = None
            else:
                if sch_mod.Examyear.objects.filter(code=user_examyear_int, country=country_selected).exists():
                    # examyear exists in selected_country: selected_country OK
                    _examyear_country_selected = sch_mod.Examyear.objects.filter(code=user_examyear_int, country=country_selected).get()
                    #logger.debug('get_examyear_in_selected_country _examyear_country_selected: ' + str(_examyear_country_selected) + ' type: ' + str(type(_examyear_country_selected)))
                else:
                    # examyear does not exist in country: select country NOT OK: delete user.examyear
                    _examyear_country_selected = None
        return _examyear_country_selected


    def examyear_exists_in_this_country(cls, country, examyear):
        # PR2018-08-13
        # This validation is used when user wants to add a new examyear (only systenm and insp users can add new examyear)
        # It checks if new examyear exists in user.country.
        # If it exists: new examyear cannot be added, if not: OK

        # except_for_this_examyear not necessray because examyear cannot be changed

        if country is None:
            # if country is None: new examyear cannot be added
            _isOK = False
        else:
            if examyear is None:
                # if examyear is None: new examyear cannot be added
                _isOK = False
            else:
                if sch_mod.Examyear.objects.filter(examyear=examyear, country=country).exists():
                    # examyear exists in country: new examyear cannot be added
                    _isOK = False
                else:
                    # examyear does not exist in country: add examyear OK, new examyear can be added
                    _isOK = True
        return _isOK
