# PR2022-08-03
from django.contrib.auth.decorators import login_required
from django.db import connection

from django.http import HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views import View

#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, pgettext_lazy, gettext_lazy as _
from reportlab.pdfbase.pdfmetrics import stringWidth

from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import mm, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Frame

from accounts import views as acc_view
from accounts import permits as acc_prm

from awpr import constants as c
from awpr import settings as s
from awpr import functions as af
from awpr import validators as av
from awpr import downloads as dl

from schools import models as sch_mod
from students import validators as stud_val
from subjects import models as subj_mod
from subjects import views as subj_view
from subjects import calc_orderlist as subj_calc

# PR2019-01-04  https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy
from django.utils.functional import Promise
from django.utils.encoding import force_text
from django.core.serializers.json import DjangoJSONEncoder

import json
import io

import logging
logger = logging.getLogger(__name__)


class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)


@method_decorator([login_required], name='dispatch')
class EnvelopItemUploadView(View):  # PR2020-10-01 PR2021-07-18  PR2022-09-16

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= EnvelopItemUploadView ============= ')

        error_dict = {}
        update_wrap = {}
        messages = []

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)
            mode = upload_dict.get('mode')

# - get permit
            page_name = 'page_orderlist'
            has_permit = acc_prm.get_permit_crud_of_this_page(page_name, request)

            if logging_on:
                logger.debug('has_permit: ' + str(has_permit))
                logger.debug('upload_dict: ' + str(upload_dict))
            """
            upload_dict: {'table': 'envelopitem', 'mode': 'create', 'content_nl': 'aa', 'content_color': 'blue'}
            upload_dict: {'table': 'envelopitem', 'mode': 'delete', 'envelopitem_pk': 2, 'map_id': 'envelopitem_2'}
            upload_dict: {'table': 'envelopitem', 'mode': 'update', 'envelopitem_pk': 6, 'mapid': 'envelopitem_6', 
            'content_nl': 'Errata', 'content_en': 'Errata', 'content_pa': 'Errata', 
            'instruction_nl': 'Errata', 'instruction_en': 'Errata', 
            'instruction_pa': 'Errata'}

            """

            if has_permit:

# - reset language
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

# - get variables
                envelopitem_pk = upload_dict.get('pk_int')
                is_create = mode == 'create'
                is_delete = mode == 'delete'

                updated_rows = []
                append_dict = {}

                header_txt = _('Create label text') if is_create else _('Delete label text') if is_delete else _('Edit label text')

# ----- get selected examyear from usersettings
                sel_examyear, may_edit, error_list = acc_view.get_selected_examyear_from_usersetting(request, True)  # allow_not_published = True
                if logging_on:
                    logger.debug('sel_examyear:   ' + str(sel_examyear))
                    logger.debug('may_edit:       ' + str(may_edit))

                if error_list:
                    error_list.append(str(_('You cannot make changes.')))
                    err_html = '<br>'.join(error_list)
                    messages.append({'header': str(header_txt), 'class': "border_bg_invalid", 'msg_html': err_html})
                else:

# +++  Create new envelopitem
                    if is_create:
                        envelopitem_instance, err_html = create_envelopitem(sel_examyear, request)
                        # this is used when msg is shown in modal envelopitem
                        #if err_html:
                        #    error_dict['nonfield'] = err_html

                        # this is used when msg is shown in modal message modal
                        if err_html:
                            messages.append({'header': str(header_txt), 'class': "border_bg_invalid", 'msg_html': err_html})
                        if envelopitem_instance:
                            append_dict['created'] = True
                    else:

# +++  or get existing envelopitem
                        envelopitem_instance = subj_mod.Envelopitem.objects.get_or_none(
                            pk=envelopitem_pk,
                            examyear=sel_examyear
                        )
                    if logging_on:
                        logger.debug('envelopitem_instance: ' + str(envelopitem_instance))

                    if envelopitem_instance:
# +++ Delete envelopitem
                        if is_delete:
                            deleted_row, err_html = sch_mod.delete_instance(
                                table='envelopitem',
                                instance=envelopitem_instance,
                                request=request,
                                this_txt=_('This label text')
                            )
                            if err_html:
                                messages.append(
                                    {'header': str(header_txt), 'class': "border_bg_invalid", 'msg_html': err_html})
                            else:
        # - set envelopitem = None to skip create_envelopitem_rows when deleting successfull
                                envelopitem_instance = None
        # - add deleted_row to updated_rows
                                updated_rows.append(deleted_row)

                                if logging_on:
                                    logger.debug('    delete order ok')
                                    logger.debug('    deleted_row: ' + str(deleted_row))

# +++  Update envelopitem, also when it is created
                        else:
                            update_envelopitem_instance(
                                instance=envelopitem_instance,
                                upload_dict=upload_dict,
                                error_dict=error_dict,
                                request=request
                            )

# - create updated_row, also when deleting failed, not when deleted ok, in that case deleted_row is already added to updated_rows
# - error_dict is added to updated_row, messages are added to update_wrap['messages']
                    if envelopitem_instance:
                        if error_dict:
                            append_dict['error'] = error_dict

                        updated_rows = create_envelopitem_rows(
                            sel_examyear=sel_examyear,
                            append_dict=append_dict,
                            envelopitem_pk=envelopitem_instance.pk)

                update_wrap['updated_envelopitem_rows'] = updated_rows

# - addd messages to update_wrap
        if messages:
            update_wrap['messages'] = messages

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of EnvelopItemUploadView


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_envelopitem(sel_examyear, request):
    # --- create envelopitem PR2022-08-04
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' +++++++++++++++++ create_envelopitem +++++++++++++++++ ')

    err_html = None
    envelopitem = None
    if sel_examyear:

        try:
    # - create and save envelopitembase
            envelopitembase = subj_mod.Envelopitembase()
            envelopitembase.save()

    # - create and save envelopitem
            envelopitem = subj_mod.Envelopitem(
                base=envelopitembase,
                examyear=sel_examyear
            )
            envelopitem.save(request=request)

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

            this_text = str(_('This label text'))
            # &emsp; add 4 'hard' spaces
            err_html = ''.join((
                str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
                str(_('%(cpt)s could not be created.') % {'cpt': this_text})
            ))

    """
    new approach PR2022-08-04:
    if this_text is None:
        this_text = str(_('This item'))
    # &emsp; add 4 'hard' spaces
    err_html = ''.join((
        str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
        str(_('%(cpt)s could not be deleted.') % {'cpt': this_text})
    ))
    return err_html
    ...
    deleted_row, msg_html = delete_customer_instance (customer_instance, request)
    if msg_html:
        error_dict['nonfield'] = msg_html
    
    if error_dict:
        updated_row['error'] = error_dict
    .....    
    if updated_rows and updated_rows[0]:
        updated_row = updated_rows[0]
        if is_created:
        # - add 'created' to updated_row, to show OK when new row is added to table
            updated_row['created'] = True
        if error_dict:
            updated_row['error'] = error_dict
    """

    return envelopitem, err_html
# - end of create_envelopitem


def update_envelopitem_instance(instance, upload_dict, error_dict, request):
    # --- update existing and new instance PR2022-08-04 PR2022-09-04 PR2022-09-28 PR2022-10-20

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_envelopitem_instance -------')
        logger.debug('    upload_dict: ' + str(upload_dict))
        logger.debug('    instance:    ' + str(instance))

    has_error = False
    if instance:
        save_changes = False

        for field, new_value in upload_dict.items():

            if field in ('content_color', 'instruction_color'):
                # set default to black
                if not new_value:
                    new_value = 'black'
                saved_value = getattr(instance, field)

                # PR2022-06-29 debug: when value is None it converts it to string 'None'
                #if new_value is not None:
                #    if not isinstance(new_value, str):
                #        new_value = str(new_value)

                if new_value != saved_value:
                    if logging_on:
                        logger.debug('saved_value: ' + str(saved_value) + ' ' + str(type(saved_value)))
                        logger.debug('new_value:   ' + str(new_value)+ ' ' + str(type(new_value)))

                    setattr(instance, field, new_value)
                    save_changes = True

            elif field in ('content_font', 'instruction_font'):  #PR2022-10-20
                # default is None
                saved_value = getattr(instance, field)

                # PR2022-06-29 debug: when value is None it converts it to string 'None'
                # if new_value is not None:
                #    if not isinstance(new_value, str):
                #        new_value = str(new_value)

                if new_value != saved_value:
                    if logging_on:
                        logger.debug('saved_value: ' + str(saved_value) + ' ' + str(type(saved_value)))
                        logger.debug('new_value:   ' + str(new_value) + ' ' + str(type(new_value)))

                    setattr(instance, field, new_value)
                    save_changes = True

            elif field in ('content_nl', 'content_en', 'content_pa',
                           'instruction_nl', 'instruction_en', 'instruction_pa'):

                if logging_on:
                    logger.debug('    field: ' + str(field))
                    logger.debug('    new_value: ' + str(new_value))

                if new_value:
                    max_len = c.MAX_LENGTH_EMAIL_ADDRESS if 'instr' in field else c.MAX_LENGTH_NAME
                    # - validate length of new_value, don't show new_value in msg_err
                    msg_err = stud_val.validate_length(
                        caption=_('The text'),
                        input_value=new_value,
                        max_length=max_len,
                        blank_allowed=True,
                        hide_value_in_msg=True
                    )
                    if msg_err:
                        has_error = True
                        error_dict[field] = msg_err

                if not has_error:
                    saved_value = getattr(instance, field)

                    # PR2022-06-29 debug: when value is None it converts it to string 'None'
                    #if new_value is not None:
                    #    if not isinstance(new_value, str):
                    #        new_value = str(new_value)

                    if new_value != saved_value:
                        if logging_on:
                            logger.debug('saved_value: ' + str(saved_value) + ' ' + str(type(saved_value)))
                            logger.debug('new_value:   ' + str(new_value)+ ' ' + str(type(new_value)))

                        setattr(instance, field, new_value)
                        save_changes = True

# --- end of for loop ---

# 5. save changes
        if save_changes:
            try:
                instance.save(request=request)
            except Exception as e:
                has_error = True
                logger.error(getattr(e, 'message', str(e)))

                # &emsp; add 4 'hard' spaces
                err_html = ''.join((
                    str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
                    str(_('The changes have not been saved.'))
                ))
                error_dict['nonfield'] = err_html

    return has_error
# - end of update_envelopitem_instance


@method_decorator([login_required], name='dispatch')
class EnvelopLabelUploadView(View):  # PR2022-08-08 PR2022-09-16

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= EnvelopLabelUploadView ============= ')

        error_dict = {}
        update_wrap = {}
        messages = []

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)
            mode = upload_dict.get('mode')

# - get permit
            page_name = 'page_orderlist'
            has_permit = acc_prm.get_permit_crud_of_this_page(page_name, request)

            if logging_on:
                logger.debug('has_permit: ' + str(has_permit))
                logger.debug('upload_dict: ' + str(upload_dict))
            """
            upload_dict: {'table': 'enveloplabel', 'mode': 'create', 'name': 'dd', 'is_errata': True, 
                'is_variablenumber': False, 'numberinenvelop': 2, 'numberofenvelops': 2, '
                uniontable': [{'picklist_pk': 6, 'uniontable_pk': None, 'sequence': 20, 'selected': True}, 
                              {'picklist_pk': 14, 'uniontable_pk': None, 'sequence': 21, 'selected': True}]}
                              
            upload_dict: {'table': 'enveloplabel', 'mode': 'update', 'name': 'dd', 
                        'enveloplabel_pk': 5, 'is_errata': True, 
                        'is_variablenumber': False, 'numberinenvelop': 2, 'numberofenvelops': 2, 
                        'uniontable': [{'picklist_pk': 6, 'uniontable_pk': 7, 'sequence': 20, 'selected': True}, 
                                        {'picklist_pk': 1, 'uniontable_pk': None, 'sequence': 33, 'selected': True}, 
                                        {'picklist_pk': 14, 'uniontable_pk': 8, 'sequence': None, 'selected': False}]}

            upload_dict: {'table': 'enveloplabel', 'mode': 'delete', 'enveloplabel_pk': 7}
            
            upload_dict: {'table': 'enveloplabel', 'mode': 'update', 'name': 'errata', 
                'enveloplabel_pk': 4, 'is_errata': True, 
                'is_variablenumber': False, 'numberinenvelop': 1, 'numberofenvelops': 1, 
                'uniontable': [
                    {'picklist_pk': 1, 'uniontable_pk': 6, 'sequence': 20, 'selected': True}, 
                    {'picklist_pk': 12, 'uniontable_pk': None, 'sequence': 39, 'selected': True},
                    {'picklist_pk': 19, 'uniontable_pk': None, 'sequence': 40, 'selected': True}]}
            
            """

            if has_permit:

# - reset language
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

# - get variables
                enveloplabel_pk = upload_dict.get('pk_int')
                name = upload_dict.get('name')

                is_create = mode == 'create'
                is_delete = mode == 'delete'

                updated_rows = []
                append_dict = {}

                header_txt = _('Create label') if is_create else _('Delete label') if is_delete else _('Edit label')

# ----- get selected examyear from usersettings
                sel_examyear, may_edit, error_list = acc_view.get_selected_examyear_from_usersetting(request, True)  # allow_not_published = True
                if logging_on:
                    logger.debug('sel_examyear:   ' + str(sel_examyear))
                    logger.debug('may_edit:       ' + str(may_edit))

                if error_list:
                    error_list.append(str(_('You cannot make changes.')))
                    err_html = '<br>'.join(error_list)
                    messages.append({'header': str(header_txt), 'class': "border_bg_invalid", 'msg_html': err_html})
                else:

# +++  Create new enveloplabel
                    if is_create:
                        enveloplabel_instance, err_html = create_enveloplabel(sel_examyear, name, request)
                        # this is used when msg is shown in modal envelopitem
                        #if err_html:
                        #    error_dict['nonfield'] = err_html

                        # this is used when msg is shown in modal message modal
                        if err_html:
                            messages.append({'header': str(header_txt), 'class': "border_bg_invalid", 'msg_html': err_html})
                        if enveloplabel_instance:
                            append_dict['created'] = True
                    else:

# +++  or get existing enveloplabel
                        enveloplabel_instance = subj_mod.Enveloplabel.objects.get_or_none(
                            id=enveloplabel_pk,
                            examyear=sel_examyear
                        )
                    if logging_on:
                        logger.debug('    enveloplabel_pk: ' + str(enveloplabel_pk))
                        logger.debug('    sel_examyear: ' + str(sel_examyear))
                        logger.debug('    enveloplabel_instance: ' + str(enveloplabel_instance))

                    if enveloplabel_instance:

# +++ Delete enveloplabel
                        if is_delete:
                            deleted_row, err_html = sch_mod.delete_instance(
                                table='enveloplabel',
                                instance=enveloplabel_instance,
                                request=request,
                                this_txt=_('This label')
                            )
                            if logging_on:
                                logger.debug('    deleted_row: ' + str(deleted_row))
                                logger.debug('    err_html: ' + str(err_html))
                            if err_html:
                                messages.append(
                                    {'header': str(header_txt), 'class': "border_bg_invalid", 'msg_html': err_html})
                            else:
        # - set enveloplabel_instance = None to skip create_enveloplabel_rows when deleting was successfull
                                enveloplabel_instance = None
        # - add deleted_row to updated_rows
                                updated_rows.append(deleted_row)

                                if logging_on:
                                    logger.debug('    deleted_row: ' + str(deleted_row))

# +++  Update enveloplabel, also when it is created
                        else:
                            err_html = update_enveloplabel_instance(
                                examyear=sel_examyear,
                                enveloplabel_instance=enveloplabel_instance,
                                upload_dict=upload_dict,
                                request=request
                            )
                            if err_html:
                                messages.append({'header': str(header_txt), 'class': "border_bg_invalid", 'msg_html': err_html})

# - create updated_row, also when deleting failed, not when deleted ok, in that case deleted_row is already added to updated_rows
# - error_dict is added to updated_row, messages are added to update_wrap['messages']
                    if enveloplabel_instance:
                        if error_dict:
                            append_dict['error'] = error_dict

                        updated_rows = create_enveloplabel_rows(
                            sel_examyear=sel_examyear,
                            append_dict=append_dict,
                            enveloplabel_pk=enveloplabel_instance.pk)

                update_wrap['updated_enveloplabel_rows'] = updated_rows

                update_wrap['updated_enveloplabelitem_rows'] = create_enveloplabelitem_rows(sel_examyear)

# - addd messages to update_wrap
        if messages:
            update_wrap['messages'] = messages

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of EnvelopLabelUploadView


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_enveloplabel(sel_examyear, name, request):
    # --- create enveloplabel PR2022-08-08
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' +++++++++++++++++ create_enveloplabel +++++++++++++++++ ')

    err_html = None
    enveloplabel = None
    if sel_examyear:

        try:
            # - create and save enveloplabelbase
            enveloplabelbase = subj_mod.Enveloplabelbase()
            enveloplabelbase.save()

            # - create and save enveloplabel
            enveloplabel = subj_mod.Enveloplabel(
                base=enveloplabelbase,
                examyear=sel_examyear,
                name=name
            )
            enveloplabel.save(request=request)

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

            this_text = str(_('This label'))
            err_html = ''.join((
                str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
                str(_('%(cpt)s could not be created.') % {'cpt': this_text})
            ))

    return enveloplabel, err_html
# - end of create_enveloplabel


def update_enveloplabel_instance(examyear, enveloplabel_instance, upload_dict, request):
    # --- update existing and new instance PR2022-08-08 PR2022-10-09

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_enveloplabel_instance -------')
        logger.debug('    enveloplabel_instance: ' + str(enveloplabel_instance))
        logger.debug('    upload_dict:    ' + str(upload_dict))
    """
    upload_dict: {
        'table': 'enveloplabel', 'mode': 'update',
        'enveloplabel_pk': 13, 'name': 'yyy', 
        'numberinenvelop': 77, 'numberofenvelops': None, 
        'uniontable': 
            [{'picklist_pk': 5, 'uniontable_pk': 12, 'selected': False, 'sequence': 0},
            {'picklist_pk': 6, 'uniontable_pk': 13, 'selected': True, 'sequence': 0}, 
            {'picklist_pk': 7, 'uniontable_pk': None, 'selected': True, 'sequence': None}]}
    """
    save_changes = False

    msg_html = None
    if enveloplabel_instance:
        for field, new_value in upload_dict.items():

            if field == 'name':
                err_html = av.validate_bundle_label_name_blank_length_exists('enveloplabel', examyear, new_value, enveloplabel_instance)
                if err_html:
                    msg_html = err_html
                else:
                    saved_value = getattr(enveloplabel_instance, field)
                    if new_value != saved_value:
                        setattr(enveloplabel_instance, field, new_value)
                        save_changes = True

            elif field == 'numberinenvelop':
                # numberinenvelop can be 0
                if new_value is None:
                    setattr(enveloplabel_instance, field, None)
                    save_changes = True
                elif isinstance(new_value, int):
                    saved_value = getattr(enveloplabel_instance, field)
                    if new_value != saved_value:
                        setattr(enveloplabel_instance, field, new_value)
                        save_changes = True

            elif field == 'numberofenvelops':
                if not new_value:
                    setattr(enveloplabel_instance, field, None)
                    save_changes = True
                elif isinstance(new_value, int):
                    saved_value = getattr(enveloplabel_instance, field)
                    if new_value != saved_value:
                        setattr(enveloplabel_instance, field, new_value)
                        save_changes = True

            elif field in ('is_variablenumber', 'is_errata'):
                if not new_value:
                    new_value = False

                saved_value = getattr(enveloplabel_instance, field)
                if new_value != saved_value:
                    setattr(enveloplabel_instance, field, new_value)
                    save_changes = True
                    # reset numberofenvelops when is_variablenumber = True
                    # Note: field numberofenvelops must be changed first. Therefore loop through tuple to get right order
                    if new_value and field == 'is_variablenumber':
                        setattr(enveloplabel_instance, 'numberofenvelops', None)

            elif field == 'uniontable':
                if new_value: # new_value = uniontable
                    if logging_on:
                        logger.debug('    new_value: ' + str(new_value))

                    for row in new_value:
                        envelopitem_pk = row.get('picklist_pk')
                        labelitem_pk = row.get('uniontable_pk')
                        sequence = row.get('sequence') or 0
                        is_selected = row.get('selected')

                        if logging_on:
                            logger.debug('    envelopitem_pk: ' + str(envelopitem_pk))
                            logger.debug('    labelitem_pk: ' + str(labelitem_pk))
                            logger.debug('    is_selected: ' + str(is_selected))

        # - get existing labelitem_instance
                        labelitem_instance = subj_mod.Enveloplabelitem.objects.get_or_none(pk=labelitem_pk)
                        if logging_on:
                            logger.debug('    get labelitem_instance: ' + str(labelitem_instance))

                        if labelitem_instance:
                            if is_selected:
    # - check if sequence has changed, if so: update
                                labelitem_instance_sequence = getattr(labelitem_instance, 'sequence') or 0
                                if sequence != labelitem_instance_sequence:
                                    setattr(labelitem_instance,'sequence', sequence)
                                    labelitem_instance.save(request=request)
                                    if logging_on:
                                        logger.debug('    update labelitem_instance: ' + str(labelitem_instance))
                            else:
    # - delete labelitem if not selected
                                if logging_on:
                                    logger.debug('    delete labelitem_instance: ' + str(labelitem_instance))
                                labelitem_instance.delete()

        #- add labelitem if is_selected and labelitem_pk does not exist yet
                        elif is_selected and envelopitem_pk:
                            envelopitem_instance = subj_mod.Envelopitem.objects.get_or_none(pk=envelopitem_pk)
                            if logging_on:
                                logger.debug('    new envelopitem_instance: ' + str(envelopitem_instance))

                            if envelopitem_instance:
        # - check if item already exists in labelitems, to prevent doubles
                                exists = subj_mod.Enveloplabelitem.objects.filter(
                                    enveloplabel=enveloplabel_instance,
                                    envelopitem=envelopitem_instance
                                ).exists()
                                if logging_on:
                                    logger.debug('    exists: ' + str(exists))

                                if not exists:
                                    labelitem_instance = subj_mod.Enveloplabelitem(
                                        enveloplabel=enveloplabel_instance,
                                        envelopitem=envelopitem_instance,
                                        sequence=sequence
                                    )
                                    labelitem_instance.save(request=request)
                                    if logging_on:
                                        logger.debug('    new saved labelitem_instance: ' + str(labelitem_instance))
    # --- end of for loop ---

# 5. save changes
        if save_changes:
            try:
                enveloplabel_instance.save(request=request)
            except Exception as e:
                has_error = True
                logger.error(getattr(e, 'message', str(e)))

                # &emsp; add 4 'hard' spaces
                msg_html = ''.join((
                    str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
                    str(_('The changes have not been saved.'))
                ))

    return msg_html
# - end of update_enveloplabel_instance


@method_decorator([login_required], name='dispatch')
class EnvelopBundleUploadView(View):  # PR2022-08-11 PR2022-09-16

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= EnvelopBundleUploadView ============= ')

        error_dict = {}
        update_wrap = {}
        messages = []

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)
            mode = upload_dict.get('mode')

# - get permit
            page_name = 'page_orderlist'
            has_permit = acc_prm.get_permit_crud_of_this_page(page_name, request)

            if logging_on:
                logger.debug('has_permit: ' + str(has_permit))
                logger.debug('upload_dict: ' + str(upload_dict))
            """
            upload_dict: {'table': 'envelopbundle', 'mode': 'update', 'envelopbundle_pk': 1, 'parent_name': 'ww', 
                'uniontable': [
                    {'picklist_pk': 6, 'uniontable_pk': None, 'selected': True},
                    {'picklist_pk': 3, 'uniontable_pk': None, 'selected': True}]}
            upload_dict: {'table': 'envelopbundle', 'mode': 'create', 'name': 'bundle 2', 
                'uniontable': [{'picklist_pk': 6, 'uniontable_pk': None, 'selected': True}]}

            upload_dict: {'table': 'envelopbundle', 'mode': 'create', 'name': 'bb', 
                'uniontable': [{'picklist_pk': 6, 'uniontable_pk': None, 'selected': True}, 
                                {'picklist_pk': 4, 'uniontable_pk': None, 'selected': True}, 
                                {'picklist_pk': 5, 'uniontable_pk': None, 'selected': True}]}
            """

            if has_permit:

# - reset language
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

# - get variables
                envelopbundle_pk = upload_dict.get('pk_int')
                name = upload_dict.get('name')

                is_create = mode == 'create'
                is_delete = mode == 'delete'

                updated_rows = []
                append_dict = {}

                header_txt = _('New label bundle') if is_create else _('Delete label bundle') if is_delete else _('Edit label bundle')

# ----- get selected examyear from usersettings
                sel_examyear, may_edit, error_list = acc_view.get_selected_examyear_from_usersetting(request, True)  # allow_not_published = True
                if logging_on:
                    logger.debug('sel_examyear:   ' + str(sel_examyear))
                    logger.debug('may_edit:       ' + str(may_edit))
                    logger.debug('is_create:       ' + str(is_create))
                    logger.debug('is_delete:       ' + str(is_delete))

                if error_list:
                    error_list.append(str(_('You cannot make changes.')))
                    err_html = '<br>'.join(error_list)
                    messages.append({'header': str(header_txt), 'class': "border_bg_invalid", 'msg_html': err_html})
                else:

# +++  Create new envelopitem
                    if is_create:
                        envelopbundle_instance, err_html = create_envelopbundle(sel_examyear, name, request)
                        # this is used when msg is shown in modal envelopitem
                        #if err_html:
                        #    error_dict['nonfield'] = err_html

                        # this is used when msg is shown in modal message modal
                        if err_html:
                            messages.append({'header': str(header_txt), 'class': "border_bg_invalid", 'msg_html': err_html})
                        if envelopbundle_instance:
                            append_dict['created'] = True
                    else:

# +++  or get existing envelopitem
                        envelopbundle_instance = subj_mod.Envelopbundle.objects.get_or_none(
                            id=envelopbundle_pk,
                            examyear=sel_examyear
                        )
                    if logging_on:
                        logger.debug('    envelopbundle_instance: ' + str(envelopbundle_instance))

                    if envelopbundle_instance:

# +++ Delete enveloplabel
                        if is_delete:
                            deleted_row, err_html = sch_mod.delete_instance(
                                table='envelopbundle',
                                instance=envelopbundle_instance,
                                request=request,
                                this_txt=_('This lable bundle')
                            )
                            if err_html:
                                messages.append(
                                    {'header': str(header_txt), 'class': "border_bg_invalid", 'msg_html': err_html})
                            else:
        # - set envelopitem = None to skip create_envelopitem_rows when deleting successfull
                                envelopbundle_instance = None
        # - add deleted_row to updated_rows
                                updated_rows.append(deleted_row)

                                if logging_on:
                                    logger.debug('    delete order ok')
                                    logger.debug('    deleted_row: ' + str(deleted_row))

# +++  Update envelopitem, also when it is created, to add items to uniontable
                        else:
                            err_html = update_envelopbundle_instance(
                                examyear=sel_examyear,
                                envelopbundle_instance=envelopbundle_instance,
                                upload_dict=upload_dict,
                                request=request
                            )
                            if err_html:
                                messages.append(
                                    {'header': str(header_txt), 'class': "border_bg_invalid", 'msg_html': err_html})
# - create updated_row, also when deleting failed, not when deleted ok, in that case deleted_row is already added to updated_rows
# - error_dict is added to updated_row, messages are added to update_wrap['messages']
                    if envelopbundle_instance:
                        if error_dict:
                            append_dict['error'] = error_dict

                        updated_rows = create_envelopbundle_rows(
                            sel_examyear=sel_examyear,
                            append_dict=append_dict,
                            envelopbundle_pk=envelopbundle_instance.pk)

                update_wrap['updated_envelopbundle_rows'] = updated_rows

                update_wrap['updated_envelopbundlelabel_rows'] = create_envelopbundlelabel_rows(sel_examyear)

# - addd messages to update_wrap
        if messages:
            update_wrap['messages'] = messages

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of EnvelopBundleUploadView


def create_envelopbundle(sel_examyear, name, request):
    # --- create enveloplabel PR2022-08-11
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' +++++++++++++++++ create_envelopbundle +++++++++++++++++ ')
        logger.debug('name: ' + str(name))

    err_html = None
    envelopbundle = None
    if sel_examyear:
        err_html = av.validate_bundle_label_name_blank_length_exists('envelopbundle', sel_examyear, name)

        if err_html is None:
            try:
    # - create and save envelopbundlebase
                envelopbundlebase = subj_mod.Envelopbundlebase()
                envelopbundlebase.save()

    # - create and save envelopbundle
                envelopbundle = subj_mod.Envelopbundle(
                    base=envelopbundlebase,
                    examyear=sel_examyear,
                    name=name
                )
                envelopbundle.save(request=request)

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

                this_text = str(_('This lable bundle'))
                err_html = ''.join((
                    str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
                    str(_('%(cpt)s could not be created.') % {'cpt': this_text})
                ))

    return envelopbundle, err_html
# - end of create_envelopbundle


def update_envelopbundle_instance(examyear, envelopbundle_instance, upload_dict, request):
    # --- update existing instance PR2022-08-11

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_envelopbundle_instance -------')
        logger.debug('    envelopbundle_instance: ' + str(envelopbundle_instance))
        logger.debug('    upload_dict:    ' + str(upload_dict))
    """
     upload_dict:    {'table': 'envelopbundle', 'mode': 'update', 'name': 'Bundel met errata', 
     'envelopbundle_pk': 2,
      'uniontable':
       [{'picklist_pk': 14, 'uniontable_pk': None, 'selected': True}]}

    """
    save_changes = False
    msg_html = None

    if envelopbundle_instance:

        for field, new_value in upload_dict.items():
            if field == 'name':
                err_html = av.validate_bundle_label_name_blank_length_exists('envelopbundle', examyear, new_value, envelopbundle_instance)
                if err_html:
                    msg_html = err_html
                else:
                    saved_value = getattr(envelopbundle_instance, field)
                    if new_value != saved_value:
                        setattr(envelopbundle_instance, field, new_value)
                        save_changes = True

            elif field == 'uniontable':
                if new_value: # new_value = uniontable
                    if logging_on:
                        logger.debug('    new_value: ' + str(new_value))
                    """
                    new_value: [
                        {'picklist_pk': 6, 'uniontable_pk': None, 'selected': True}, 
                        {'picklist_pk': 10, 'uniontable_pk': None, 'selected': True}]
                    """

                    for row in new_value:
                        enveloplabel_pk = row.get('picklist_pk')
                        bundlelabel_pk = row.get('uniontable_pk')
                        sequence = row.get('sequence') or 0
                        is_selected = row.get('selected')

                        if logging_on:
                            logger.debug(' ...enveloplabel_pk: ' + str(enveloplabel_pk))
                            logger.debug('    bundlelabel_pk: ' + str(bundlelabel_pk))
                            logger.debug('    sequence: ' + str(sequence))
                            logger.debug('    is_selected: ' + str(is_selected))

            # - get existing bundlelabel_instance
                        bundlelabel_instance = subj_mod.Envelopbundlelabel.objects.get_or_none(pk=bundlelabel_pk)
                        if logging_on:
                            logger.debug('    get bundlelabel_instance: ' + str(bundlelabel_instance))

                        if bundlelabel_instance:
                            if is_selected:
                                bundlelabel_instance_sequence = getattr(bundlelabel_instance, 'sequence') or 0
        # - check if sequence has changed, if so: update
                                if sequence != bundlelabel_instance_sequence:
                                    setattr(bundlelabel_instance, 'sequence', sequence)
                                    bundlelabel_instance.save(request=request)
                                    if logging_on:
                                        logger.debug('    update bundlelabel_instance: ' + str(bundlelabel_instance))
                            else:
        # - delete labelitem if not selected
                                if logging_on:
                                    logger.debug('    delete bundlelabel_instance: ' + str(bundlelabel_instance))
                                bundlelabel_instance.delete()

        # - add bundlelabel if is_selected and enveloplabel_pk does not exist yet
                        elif is_selected and enveloplabel_pk:
                            enveloplabel_instance = subj_mod.Enveloplabel.objects.get_or_none(
                                pk=enveloplabel_pk
                            )
                            if logging_on:
                                logger.debug('    new enveloplabel_instance: ' + str(enveloplabel_instance))

                            if enveloplabel_instance:
        # - check if label already exists in bundlelabels, to prevent doubles
                                exists = subj_mod.Envelopbundlelabel.objects.filter(
                                    envelopbundle=envelopbundle_instance,
                                    enveloplabel=enveloplabel_instance
                                ).exists()
                                if logging_on:
                                    logger.debug('    exists: ' + str(exists))

                                if not exists:
                                    bundlelabel_instance = subj_mod.Envelopbundlelabel(
                                        envelopbundle=envelopbundle_instance,
                                        enveloplabel=enveloplabel_instance,
                                        sequence=sequence
                                    )
                                    bundlelabel_instance.save(request=request)
                                    if logging_on:
                                        logger.debug(
                                            '    new saved bundlelabel_instance: ' + str(bundlelabel_instance))
# --- end of for loop ---


# 5. save changes
        if save_changes:
            try:
                envelopbundle_instance.save(request=request)
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

                # &emsp; add 4 'hard' spaces
                msg_html = ''.join((
                    str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
                    str(_('The changes have not been saved.'))
                ))

    return msg_html
# - end of update_envelopbundle_instance




@method_decorator([login_required], name='dispatch')
class EnvelopSubjectUploadView(View):  # PR2022-10-10

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= EnvelopSubjectUploadView ============= ')

        error_dict = {}
        update_wrap = {}
        messages = []

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)
            mode = upload_dict.get('mode')

# - get permit
            page_name = 'page_orderlist'
            has_permit = acc_prm.get_permit_crud_of_this_page(page_name, request)

            if logging_on:
                logger.debug('has_permit: ' + str(has_permit))
                logger.debug('upload_dict: ' + str(upload_dict))
            """
            upload_dict: {'table': 'envelopsubject', 'mode': 'update', 'examyear_pk': 4, 'envelopsubject_pk': 76, 'lastdate': '2022-10-13'}
            """

            if has_permit:

# - reset language
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

# - get variables
                envelopsubject_pk = upload_dict.get('envelopsubject_pk')
                # envelopsubject cannot be created or deleted in this class
                # TODO create or delete envelopsubject when adding subjects etc

                updated_rows = []
                append_dict = {}

                header_txt = _('Edit subject bundle')

# ----- get selected examyear from usersettings
                sel_examyear, may_edit, error_list = acc_view.get_selected_examyear_from_usersetting(request, True)  # allow_not_published = True
                if logging_on:
                    logger.debug('sel_examyear:   ' + str(sel_examyear))
                    logger.debug('may_edit:       ' + str(may_edit))
                    logger.debug('envelopsubject_pk:       ' + str(envelopsubject_pk))

                if error_list:
                    error_list.append(str(_('You cannot make changes.')))
                    err_html = '<br>'.join(error_list)
                    messages.append({'header': str(header_txt), 'class': "border_bg_invalid", 'msg_html': err_html})
                else:

# +++  Create new envelopsubject
                    # envelopsubject cannot be created or deleted in this class

# +++  get existing envelopitem
                    envelopsubject_instance = subj_mod.Envelopsubject.objects.get_or_none(
                        id=envelopsubject_pk,
                        department__examyear=sel_examyear
                        )
                    if logging_on:
                        logger.debug('    envelopsubject_instance: ' + str(envelopsubject_instance))

                    if envelopsubject_instance:

# +++ Delete enveloplabel
                    # envelopsubject cannot be created or deleted in this class

# +++  Update envelopsubject
                        err_html = update_envelopsubject_instance(
                            examyear=sel_examyear,
                            envelopsubject_instance=envelopsubject_instance,
                            upload_dict=upload_dict,
                            request=request
                        )
                        if err_html:
                            messages.append(
                                {'header': str(header_txt), 'class': "border_bg_invalid", 'msg_html': err_html})
# - create updated_row, also when deleting failed, not when deleted ok, in that case deleted_row is already added to updated_rows
# - error_dict is added to updated_row, messages are added to update_wrap['messages']
                    if envelopsubject_instance:
                        if error_dict:
                            append_dict['error'] = error_dict

                        updated_rows = get_envelopsubject_rows(
                            sel_examyear=sel_examyear,
                            append_dict=append_dict,
                            envelopsubject_pk=envelopsubject_instance.pk)

                update_wrap['updated_envelopsubject_rows'] = updated_rows

# - addd messages to update_wrap
        if messages:
            update_wrap['messages'] = messages

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of EnvelopSubjectUploadView


def update_envelopsubject_instance(examyear, envelopsubject_instance, upload_dict, request):
    # --- update existing instance PR2022-10-10

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_envelopsubject_instance -------')
        logger.debug('    envelopsubject_instance: ' + str(envelopsubject_instance))
        logger.debug('    upload_dict:    ' + str(upload_dict))
    """
    upload_dict: {'table': 'envelopsubject', 'mode': 'update', 'examyear_pk': 4, 'envelopsubject_pk': 76, 'lastdate': '2022-10-13'}
    """
    save_changes = False
    msg_html = None

    if envelopsubject_instance:

        for field, new_value in upload_dict.items():

            if field == 'envelopbundle_pk':
                db_field = 'envelopbundle'

                new_instance = subj_mod.Envelopbundle.objects.get_or_none(pk=new_value)
                old_instance = getattr(envelopsubject_instance, db_field)

                if logging_on:
                    logger.debug('     field:        ' + str(field))
                    logger.debug('     new_instance:    ' + str(new_instance) + ' ' + str(type(new_instance)))
                    logger.debug('     old_instance:    ' + str(old_instance) + ' ' + str(type(old_instance)))

                if new_instance != old_instance:
                    setattr(envelopsubject_instance, db_field, new_instance)
                    save_changes = True

                if logging_on:
                    logger.debug('     save_changes:        ' + str(save_changes))
                    logger.debug('     envelopsubject_instance: ' + str(envelopsubject_instance))

            elif field in ('firstdate', 'lastdate'):
                # new_value has format of date-iso, Excel ordinal format is already converted
                saved_dateobj = getattr(envelopsubject_instance, field)

                new_dateobj = af.get_date_from_ISO(new_value)

                if new_dateobj != saved_dateobj:
                    if logging_on:
                        logger.debug('saved_dateobj saved: ' + str(saved_dateobj) + ' ' + str(type(saved_dateobj)))
                        logger.debug('new_dateobj new  : ' + str(new_dateobj) + ' ' + str(type(new_dateobj)))

                    setattr(envelopsubject_instance, field, new_value)
                    save_changes = True

            elif field in ('starttime', 'endtime'):
                if logging_on:
                    logger.debug('field: ' + str(field))
                    logger.debug('new_value: ' + str(new_value))

                old_value = getattr(envelopsubject_instance, field)
                if new_value != old_value:
                    setattr(envelopsubject_instance, field, new_value)
                    save_changes = True
                    logger.debug('save_changes: ' + str(save_changes))

            elif field == 'has_errata':
                if not new_value:
                    new_value = False

                if logging_on:
                    logger.debug('field: ' + str(field))
                    logger.debug('new_value: ' + str(new_value))

                old_value = getattr(envelopsubject_instance, field, False)
                if new_value != old_value:
                    setattr(envelopsubject_instance, field, new_value)
                    save_changes = True

# 5. save changes
        if save_changes:
            try:
                envelopsubject_instance.save(request=request)
            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

                # &emsp; add 4 'hard' spaces
                msg_html = ''.join((
                    str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
                    str(_('The changes have not been saved.'))
                ))

    return msg_html
# - end of update_envelopsubject_instance
##################################



def create_orderlist_rows(request, sel_examyear):
    # --- create rows of all schools with published subjects PR2021-08-18
    # only used in downloads.py
    # PR2022-02-15 filter also on student.tobedeleted=False
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== students.view create_orderlist_rows ============= ')
        logger.debug('sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))

    # create list of schools of this examyear (CUR and SXM), only where defaultrole = school
    # for sxm: only sxm schools
    # with left join of studentsubjects with deleted=False, group by school_id with count(*)

    # CASE WHEN  POSITION(';" + sch.otherlang + ";' IN CONCAT(';', subj.otherlang, ';')) > 0 THEN ELSE END

    """

    "si.ete_exam AS si_ete_exam,",
    CASE WHEN subj.otherlang IS NULL OR sch.otherlang IS NULL  THEN 'nl'   ELSE
    CASE WHEN POSITION(sch.otherlang IN subj.otherlang) > 0 THEN sch.otherlang ELSE 'nl' END END AS lang

    or even better with delimiters:
    CASE WHEN subj.otherlang IS NULL OR sch.otherlang IS NULL 
        THEN 
            'nl' 
        ELSE
            CASE WHEN POSITION(';" + sch.otherlang + ";' IN CONCAT(';', subj.otherlang, ';')) > 0 
                THEN 
                ELSE 
            END
    END    

    """
    rows = []
    if sel_examyear:

        requsr_country_pk = request.user.country.pk
        is_curacao = request.user.country.abbrev.lower() == 'cur'
        show_sxm_only = "AND ey.country_id = %(requsr_country_pk)s::INT" if not is_curacao else ''

        sel_exam_period = 1
        sql_keys = {'ey_code_int': sel_examyear.code,
                    'ex_period_int': sel_exam_period,
                    'default_role': c.ROLE_008_SCHOOL,
                    'requsr_country_pk': requsr_country_pk}

        sql_sublist = ["SELECT st.school_id AS school_id, publ.id AS subj_published_id, count(*) AS publ_count,",
                       "publ.datepublished, publ.examperiod",

                       "FROM students_studentsubject AS studsubj",
                       "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",

                       "INNER JOIN schools_published AS publ ON (publ.id = studsubj.subj_published_id)",
                       "WHERE publ.examperiod = %(ex_period_int)s::INT",
                       "AND NOT st.tobedeleted AND NOT studsubj.tobedeleted",

                       "GROUP BY st.school_id, publ.id, publ.datepublished, publ.examperiod"
                       ]
        sub_sql = ' '.join(sql_sublist)

        total_sublist = ["SELECT st.school_id AS school_id, count(*) AS total",
                         "FROM students_studentsubject AS studsubj",
                         "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
                         "WHERE NOT st.tobedeleted AND NOT studsubj.tobedeleted",
                         "GROUP BY st.school_id"
                         ]
        total_sql = ' '.join(total_sublist)
        # see https://www.postgresqltutorial.com/postgresql-group-by/
        total_students_sublist = ["SELECT st.school_id, count(*) AS total_students",
                                  "FROM students_student AS st",
                                  "WHERE NOT st.tobedeleted",
                                  "GROUP BY st.school_id"
                                  ]
        total_students_sql = ' '.join(total_students_sublist)

        sql_list = ["WITH sub AS (", sub_sql, "), total AS (", total_sql, "), total_students AS (", total_students_sql, ")",
                    "SELECT sch.id AS school_id, schbase.code AS schbase_code, sch.abbrev AS school_abbrev, sub.subj_published_id,",
                    "total.total, total_students.total_students, sub.publ_count, sub.datepublished, sub.examperiod",

                    "FROM schools_school AS sch",
                    "INNER JOIN schools_schoolbase AS schbase ON (schbase.id = sch.base_id)",
                    "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",

                    "LEFT JOIN sub ON (sub.school_id = sch.id)",
                    "LEFT JOIN total ON (total.school_id = sch.id)",
                    "LEFT JOIN total_students ON (total_students.school_id = sch.id)",

                    "WHERE schbase.defaultrole = %(default_role)s::INT",
                    "AND ey.code = %(ey_code_int)s::INT",
                    show_sxm_only,
                    "ORDER BY sch.id"
                    ]
        sql = ' '.join(sql_list)

        if logging_on:
            logger.debug('sql: ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = af.dictfetchall(cursor)

            for row in rows:
                published_pk = row.get('subj_published_id')
                if published_pk:
                    # can't use sql because of file field
                    published = sch_mod.Published.objects.get_or_none(pk=published_pk)
                    if published and published.file:
                        row['file_name'] = str(published.file)
                        row['url'] = published.file.url

    return rows
# --- end of create_orderlist_rows


def check_envelopsubject_rows(sel_examyear, request):
    # PR2023-03-23
    # function cheks if every subject / dep /level combination has an envelopsubject in all 3 examperiods
    # and creates new envelopsubject if it does not exist
    logging_on = s.LOGGING_ON

    if logging_on:
        logger.debug(' =============== check_envelopsubject_rows ============= ')
        logger.debug('    sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))

    def get_si_sql_subj():
        # - loop through schemitems, grouped by subj / dep / lvl, filter by this exanmyear (ete only??)
        # COALESCE  level_id=NULL to level_id=0 is necessary, otherwise link will not work and subjects without level_id will be omitted
        return ' '.join(
            ["SELECT si.subject_id  AS subj_id, scheme.department_id AS dep_id, scheme.level_id AS lvl_id, ",
             "COALESCE(scheme.level_id, 0) AS lvl_id_nz",
             "FROM subjects_schemeitem AS si",
             "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id)",
             "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
             "WHERE si.ete_exam AND dep.examyear_id=", str(sel_examyear.pk),
             "GROUP BY si.subject_id, scheme.department_id, scheme.level_id"
             ])

    def get_envsubj_sql_sub(exam_period):
        return  ' '.join(("SELECT env_subj.subject_id AS subj_id, ",
                                     "env_subj.department_id AS dep_id, ",
                                    "COALESCE(env_subj.level_id, 0) AS lvl_id_nz, env_subj.examperiod",
                            "FROM subjects_envelopsubject AS env_subj",
                            "INNER JOIN subjects_subject AS subj ON (subj.id = env_subj.subject_id)",
                            "WHERE subj.examyear_id=", str(sel_examyear.pk),
                            "AND env_subj.examperiod=", str(exam_period)
                            ))

    try:
        for examperiod in (1,2,3):
            if logging_on:
                logger.debug('    examperiod: ' + str(examperiod) + ' ' + str(type(examperiod)))

            #sql_sub = ' '.join(("WITH si_subj AS (", get_si_sql_subj(), "), ",
                        #"env_subj AS (", get_envsubj_sql_sub(examperiod), ") ",

            sql_sub = ' '.join(("SELECT si_subj.subj_id, si_subj.dep_id, si_subj.lvl_id",
                        "FROM (", get_si_sql_subj(), ") AS si_subj",
                        "LEFT JOIN (", get_envsubj_sql_sub(examperiod), ") AS env_subj ON (env_subj.subj_id=si_subj.subj_id AND env_subj.dep_id=si_subj.dep_id AND env_subj.lvl_id_nz=si_subj.lvl_id_nz)",
                        "WHERE env_subj.subj_id IS NULL"
                        ))

            sql = ''.join(("INSERT INTO subjects_envelopsubject(",
                "subject_id, department_id, level_id, examperiod, envelopbundle_id, ",
                "firstdate, lastdate, starttime, endtime, has_errata, modifiedat, modifiedby_id) ",
                "SELECT sql_sub.subj_id, sql_sub.dep_id, sql_sub.lvl_id,", str(examperiod), "::INT, NULL, ",
                "NULL, NULL, NULL, NULL, FALSE, '", str(timezone.now()), "', ", str(request.user.pk),
                " FROM (" ,sql_sub , ") AS sql_sub ",
                "RETURNING id;"))

            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = af.dictfetchall(cursor)

                if logging_on:
                    logger.debug('    row count: ' + str(len(rows)))
                    if rows:
                        for row in rows:
                            logger.debug('    row: ' + str(row) + ' ' + str(type(row)))
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
# --- end of check_envelopsubject_rows


def get_envelopsubject_rows(sel_examyear, append_dict, envelopsubject_pk=None, practex_only=None, errata_only=False):
    # PR2022-10-09 PR2022-10-10 PR2023-03-24
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== get_envelopsubject_rows ============= ')
        logger.debug('    sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))
        logger.debug('    errata_only: ' + str(errata_only))

    envelopsubject_rows = []
    if sel_examyear:
        try:
            si_has_practex_sql = ''.join(["SELECT si.subject_id, scheme.department_id, scheme.level_id ",
                           "FROM subjects_schemeitem AS si ",
                           "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id) ",
                           "WHERE si.has_practexam ",
                           "GROUP BY si.subject_id, scheme.department_id, scheme.level_id"
                           ])

            si_ete_exam_sql = ''.join(["SELECT si.subject_id, scheme.department_id, scheme.level_id ",
                           "FROM subjects_schemeitem AS si ",
                           "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id) ",
                           "WHERE si.ete_exam ",
                           "GROUP BY si.subject_id, scheme.department_id, scheme.level_id"
                           ])

            sql_list = ["WITH si_has_practex AS (", si_has_practex_sql, "),  si_ete_exam AS (", si_ete_exam_sql, ") ",

                "SELECT env_subj.id, subj.examyear_id AS subj_examyear_id, ",
                "CONCAT('envelopsubject_', env_subj.id::TEXT) AS mapid, ",

                "env_subj.subject_id, env_subj.department_id, env_subj.level_id, ",
                "dep.base_id AS depbase_id, depbase.code AS depbase_code, ",
                "lvl.abbrev AS lvl_abbrev, lvl.base_id AS lvlbase_id, ",
                "env_subj.examperiod, ",
                "env_subj.envelopbundle_id, bndl.name AS bundle_name, ",
                "subjbase.code AS subjbase_code, subj.name_nl AS subj_name_nl, "
                "env_subj.firstdate, env_subj.lastdate, env_subj.starttime, env_subj.endtime, env_subj.has_errata, ",

                # because of WHERE si.has_practexam in sub_sql, sub_sql.si.subject_id has only value when has_practexam
                "si_has_practex.subject_id IS NOT NULL AS has_practexam, "
                "si_ete_exam.subject_id IS NOT NULL AS ete_exam, "
                
                "env_subj.modifiedat, au.last_name AS modby_username ",

                "FROM subjects_envelopsubject AS env_subj ",
                "INNER JOIN subjects_subject AS subj ON (subj.id = env_subj.subject_id) ",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id) ",
                "INNER JOIN schools_department AS dep ON (dep.id = env_subj.department_id) ",
                "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id) ",

                "LEFT JOIN subjects_level AS lvl ON (lvl.id = env_subj.level_id) ",
                "LEFT JOIN subjects_envelopbundle AS bndl ON (bndl.id = env_subj.envelopbundle_id) ",

                "LEFT JOIN si_has_practex ON (si_has_practex.subject_id = env_subj.subject_id AND si_has_practex.department_id = env_subj.department_id AND si_has_practex.level_id = env_subj.level_id) ",

                "LEFT JOIN si_ete_exam ON (si_ete_exam.subject_id = env_subj.subject_id AND si_ete_exam.department_id = env_subj.department_id AND si_ete_exam.level_id = env_subj.level_id) ",

                "LEFT JOIN accounts_user AS au ON (au.id = env_subj.modifiedby_id) ",

                "WHERE dep.examyear_id=" + str(sel_examyear.pk) + "::INT ",
                # this filter on ETE exam doesnt work, dont know why PR2023-03-24:
                    #"AND si_ete_exam.subject_id IS NOT NULL "
            ]

            if errata_only:
                sql_list.append("AND env_subj.has_errata ")

            if envelopsubject_pk:
                sql_list.append("AND env_subj.id=" + str(envelopsubject_pk) + "::INT")
            else:
                if practex_only is not None:
                    if practex_only:
                        sql_list.append("AND si_has_practex.subject_id IS NOT NULL")
                    else:
                        sql_list.append("AND si_has_practex.subject_id IS NULL")

                sql_list.append("ORDER BY env_subj.id")

            sql = ''.join(sql_list)

            if logging_on:
                for sql_txt in sql_list:
                    logger.debug(' > ' + str(sql_txt))

            with connection.cursor() as cursor:
                cursor.execute(sql)
                envelopsubject_rows = af.dictfetchall(cursor)

            if envelopsubject_pk and envelopsubject_rows and append_dict:
                # when envelopsubject_pk has value there is only 1 row
                row = envelopsubject_rows[0]
                if row:
                    for key, value in append_dict.items():
                        row[key] = value

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        if envelopsubject_rows:
            for row in envelopsubject_rows:
                logger.debug('    row: ' + str(row))
    """
        id = env_subj.id
         row: {'id': 68, 'subj_examyear_id': 4, 'mapid': 'envelopsubject_68', 'subject_id': 262, 
            'department_id': 10, 'level_id': 11, 'depbase_id': 1, 'depbase_code': 'Vsbo', 'lvl_abbrev': 'PKL', 'lvlbase_id': 5, 
            'examperiod': 1, 'envelopbundle_id': 53, 'bundle_name': 'CSPE-ZWI-A t/m D-PKL ', 
             'subjbase_code': 'zwi', 'subj_name_nl': 'Zorg & Welzijn intrasectoraal', 
            'firstdate': datetime.date(2023, 4, 17), 'lastdate': datetime.date(2023, 5, 5), 
            'starttime': '340', 'endtime': None, 
            'has_errata': False, 'has_practexam': True, 'ete_exam': True, 
            'modifiedat': datetime.datetime(2022, 10, 14, 20, 1, 39, 221621, tzinfo=<UTC>), 'modby_username': 'drukteam'}
    """
    return envelopsubject_rows
# --- end of get_envelopsubject_rows


def create_envelopbundle_rows(sel_examyear, append_dict, envelopbundle_pk=None):
    # PR2022-08-06
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_envelopbundle_rows ============= ')
        logger.debug('sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))

    envelopbundle_rows = []
    if sel_examyear:
        try:
            sql_keys = {'ey_id': sel_examyear.pk}
            sql_list = [
                "SELECT bndl.id, bndl.base_id AS bndlbase_id, bndl.examyear_id AS bndl_examyear_id,",
                "CONCAT('envelopbundle_', bndl.id::TEXT) AS mapid,",
                "bndl.name, bndl.modifiedat, au.last_name AS modby_username",

                "FROM subjects_envelopbundle AS bndl",
                "LEFT JOIN accounts_user AS au ON (au.id = bndl.modifiedby_id)",

                "WHERE bndl.examyear_id = %(ey_id)s::INT",
            ]

            if envelopbundle_pk:
                sql_keys['bndl_pk'] = envelopbundle_pk
                sql_list.append('AND bndl.id = %(bndl_pk)s::INT')
            else:
                sql_list.append('ORDER BY bndl.id')

            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('sql_keys: ' + str(sql_keys))
                logger.debug('sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                envelopbundle_rows = af.dictfetchall(cursor)

            if envelopbundle_pk and envelopbundle_rows and append_dict:
                # when enveloplabel_pk has value there is only 1 row
                row = envelopbundle_rows[0]
                if row:
                    for key, value in append_dict.items():
                        row[key] = value

            if logging_on:
                logger.debug('envelopbundle_rows: ' + str(envelopbundle_rows))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    return envelopbundle_rows
# --- end of create_envelopbundle_rows


def create_enveloplabel_rows(sel_examyear, append_dict, enveloplabel_pk=None):
    # PR2022-08-06

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_enveloplabel_rows ============= ')
        logger.debug('sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))

    enveloplabel_rows = []
    if sel_examyear :
        try:
            sql_keys = {'ey_id': sel_examyear.pk}
            sql_list = [
                "SELECT lbl.id, lbl.base_id AS lblbase_id, lbl.examyear_id AS lbl_examyear_id,",
                "CONCAT('enveloplabel_', lbl.id::TEXT) AS mapid,",
                "lbl.name, lbl.is_variablenumber, lbl.numberofenvelops, lbl.numberinenvelop, lbl.is_errata,",
                "lbl.modifiedat, au.last_name AS modby_username",

                "FROM subjects_enveloplabel AS lbl",
                "LEFT JOIN accounts_user AS au ON (au.id = lbl.modifiedby_id)",

                "WHERE lbl.examyear_id = %(ey_id)s::INT",
            ]

            if enveloplabel_pk:
                sql_keys['lbl_pk'] = enveloplabel_pk
                sql_list.append('AND lbl.id = %(lbl_pk)s::INT')
            else:
                sql_list.append('ORDER BY lbl.id')

            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('sql_keys: ' + str(sql_keys) )
                logger.debug('sql: ' + str(sql) )

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                enveloplabel_rows = af.dictfetchall(cursor)

            if enveloplabel_pk and enveloplabel_rows and append_dict:
                # when enveloplabel_pk has value there is only 1 row
                row = enveloplabel_rows[0]
                if row:
                    for key, value in append_dict.items():
                        row[key] = value

            if logging_on:
                logger.debug('enveloplabel_rows: ' + str(enveloplabel_rows) )

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    return enveloplabel_rows
# --- end of create_enveloplabel_rows


def create_envelopitem_rows(sel_examyear, append_dict, envelopitem_pk=None):
    # PR2022-08-03 PR2022-10-20
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_envelopitem_rows ============= ')
        logger.debug('    sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))
        logger.debug('    envelopitem_pk: ' + str(envelopitem_pk) + ' ' + str(type(envelopitem_pk)))
        logger.debug('    append_dict: ' + str(append_dict) + ' ' + str(type(append_dict)))

    envelopitem_rows = []
    try:
        if sel_examyear :
            sql_keys = {'ey_id': sel_examyear.pk}
            sql_list = ["SELECT envit.id, CONCAT('envelopitem_', envit.id::TEXT) AS mapid,",

                        "envit.base_id, envit.examyear_id,",
                        "envit.content_nl, envit.content_en, envit.content_pa,",
                        "envit.instruction_nl, envit.instruction_en, envit.instruction_pa,",
                        "envit.content_color, envit.instruction_color,",
                        "envit.content_font, envit.instruction_font,",
                        "envit.modifiedby_id, envit.modifiedat,",
                        "au.last_name AS modby_username",

                        "FROM subjects_envelopitem AS envit",
                        "LEFT JOIN accounts_user AS au ON (au.id = envit.modifiedby_id)",

                        "WHERE envit.examyear_id = %(ey_id)s::INT"]

            if envelopitem_pk:
                # when schemeitem_pk has value: skip other filters
                sql_keys['envit_pk'] = envelopitem_pk
                sql_list.append('AND envit.id = %(envit_pk)s::INT')
            else:
                sql_list.append('ORDER BY envit.id')

            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('sql_keys: ' + str(sql_keys) )
                logger.debug('sql: ' + str(sql) )

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                envelopitem_rows = af.dictfetchall(cursor)

# - add hex_color  to envelopitem_row
            if envelopitem_rows:
                for row in envelopitem_rows:
                    content_color = row.get('content_color') or 'black'
                    instruction_color = row.get('instruction_color') or 'black'

                    row['content_hexcolor'] = c.LABEL_COLOR.get(content_color)
                    row['instruction_hexcolor'] = c.LABEL_COLOR.get(instruction_color)

# - add messages to envelopitem_row
            if envelopitem_pk and envelopitem_rows:
                # when envelopitem_pk has value there is only 1 row
                row = envelopitem_rows[0]
                if row:
                    for key, value in append_dict.items():
                        row[key] = value

            if logging_on:
                logger.debug('envelopitem_rows: ' + str(envelopitem_rows) )

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return envelopitem_rows
# --- end of create_envelopitem_rows


def create_envelopbundlelabel_rows(sel_examyear):
    # PR2022-08-11

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_envelopbundlelabel_rows ============= ')
        logger.debug('sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))

    envelopbundleitem_rows = []
    try:
        if sel_examyear :
            sql_keys = {'ey_id': sel_examyear.pk}
            sql_list = [
                "SELECT bndllbl.id, bndllbl.envelopbundle_id, bndllbl.enveloplabel_id, bndllbl.sequence,",
                "lbl.name AS lbl_name, bundle.name AS bundle_name",

                "FROM subjects_envelopbundlelabel AS bndllbl",
                "INNER JOIN subjects_envelopbundle AS bundle ON (bundle.id = bndllbl.envelopbundle_id)",
                "INNER JOIN subjects_enveloplabel AS lbl ON (lbl.id = bndllbl.enveloplabel_id)",

                "WHERE bundle.examyear_id = %(ey_id)s::INT",
                "ORDER BY bndllbl.id"
            ]
            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('sql_keys: ' + str(sql_keys) )
                logger.debug('sql: ' + str(sql) )

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                envelopbundleitem_rows = af.dictfetchall(cursor)

            if logging_on:
                logger.debug('envelopbundleitem_rows: ' + str(envelopbundleitem_rows) )

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return envelopbundleitem_rows
# -end of create_envelopbundlelabel_rows


def create_enveloplabelitem_rows(sel_examyear):
    # PR2022-08-06

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_enveloplabelitem_rows ============= ')
        logger.debug('sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))

    enveloplabelitem_rows = []
    try:
        if sel_examyear :
            sql_keys = {'ey_id': sel_examyear.pk}
            sql_list = [
                "SELECT lblitem.id, lblitem.enveloplabel_id, lblitem.envelopitem_id, lblitem.sequence,",
                "lbl.examyear_id AS examyear_id, lbl.name AS lbl_name, lbl.numberofenvelops, lbl.numberinenvelop,",

                "envit.content_nl, envit.instruction_nl, envit.content_color, envit.instruction_color",

                "FROM subjects_enveloplabelitem AS lblitem",
                "INNER JOIN subjects_enveloplabel AS lbl ON (lbl.id = lblitem.enveloplabel_id)",
                "INNER JOIN subjects_envelopitem AS envit ON (envit.id = lblitem.envelopitem_id)",

                "WHERE lbl.examyear_id = %(ey_id)s::INT",
                "ORDER BY lblitem.id"
            ]
            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('sql_keys: ' + str(sql_keys) )
                logger.debug('sql: ' + str(sql) )

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                enveloplabelitem_rows = af.dictfetchall(cursor)

            if logging_on:
                logger.debug('enveloplabelitem_rows: ' + str(enveloplabelitem_rows) )

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return enveloplabelitem_rows
# -end of create_enveloplabelitem_rows


#####################

def create_enveloporderlist_rows(sel_examyear):
    # PR2023-03-02
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_enveloporderlist_rows ============= ')
        logger.debug('sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))

    orderdict = None
    if sel_examyear:
        try:
            sql_keys = {'ey_id': sel_examyear.pk}
            sql_list = [
                "SELECT eol.modifiedat, au.last_name AS modby_username, eol.orderdict ",
                "FROM subjects_enveloporderlist AS eol ",
                "LEFT JOIN accounts_user AS au ON (au.id = eol.modifiedby_id) ",

                "WHERE eol.examyear_id=", str(sel_examyear.pk), "::INT ",
                "ORDER BY eol.id DESC LIMIT 1;"
            ]


            sql = ''.join(sql_list)

            if logging_on:
                logger.debug('sql_keys: ' + str(sql_keys))
                logger.debug('sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                row = cursor.fetchone()
                if row:
                    orderdict = {
                        'modifiedat': row[0],
                        'modby_username': row[1],
                        'orderdict': json.loads(row[2])
                    }
            if logging_on:
                logger.debug('    ----------: ')
                logger.debug('    >>> ' + str(row[2]) + ' <<<')
                logger.debug('    ----------: ')

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    return orderdict
# --- end of create_enveloporderlist_rows


#####################


def get_schemeitem_info_per_dep_lvl(sel_examyear):
    # PR2022-08-12
    # filtered by department.examyear_id
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== get_schemeitem_info_per_dep_lvl ============= ')
        logger.debug('sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))

    info_dict = {}
    if sel_examyear :
        try:
            sql_keys = {'ey_id': sel_examyear.pk}
            sql_list = [
                "SELECT scheme.department_id AS dep_id, dep.abbrev AS dep_abbrev, ",
                "scheme.level_id AS lvl_id, lvl.abbrev AS lvl_abbrev, ",
                "subj.name_nl AS subj_name_nl, subj.name_en AS subj_name_en, subj.name_pa AS subj_name_pa,",
                "si.subject_id AS subj_id, si.has_practexam, si.otherlang",
                "FROM subjects_schemeitem AS si",
                "INNER JOIN subjects_scheme AS scheme ON (scheme.id = si.scheme_id)",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = scheme.department_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = scheme.level_id)",
                "WHERE dep.examyear_id = %(ey_id)s::INT"
            ]

            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                rows = af.dictfetchall(cursor)
            if rows:
                for row in rows:
                    dep_id = row.get('dep_id')
                    if dep_id not in info_dict:
                        dep_abbrev = row.get('dep_abbrev', '---').replace('.', '')
                        info_dict[dep_id] = {'dep_abbrev': dep_abbrev}
                    dep_dict = info_dict[dep_id]

                    lvl_id = row.get('lvl_id') or 0
                    if lvl_id not in dep_dict:
                        dep_dict[lvl_id] = {'lvl_abbrev': row.get('lvl_abbrev', '---')}
                    lvl_dict = dep_dict[lvl_id]

                    subj_id = row.get('subj_id')
                    if subj_id not in lvl_dict:
                        lvl_dict[subj_id] = {
                            'subj_name_nl': row.get('subj_name_nl', '---'),
                            'subj_name_en': row.get('subj_name_en'),
                            'subj_name_pa': row.get('subj_name_pa'),
                            'otherlang': [],
                            'has_practexam': False}
                    subj_dict = lvl_dict[subj_id]

                    has_practexam = row.get('has_practexam')
                    if has_practexam:
                        subj_dict['has_practexam'] = True

                    otherlang = row.get('otherlang')
                    if otherlang:
                        otherlang_arr = otherlang.split(';')
                        for lang in otherlang_arr:
                            if lang not in subj_dict['otherlang']:
                                subj_dict['otherlang'].append(lang)
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('info_dict: ' + str(info_dict))
    """
    schemeitem_info_dict: {
        4: {'code': 'VSBO', 
            6: {'lvl_code': 'PBL', 
                113: {'subj_name_nl': 'Nederlandse taal', 'otherlang': [], 'has_practexam': False}, 
                130: {'subj_name_nl': 'Uiterlijke verzorging', 'otherlang': [], 'has_practexam': False}, 
                133: {'subj_name_nl': 'Administratie en commercie', 'otherlang': ['en', 'pa'], 'has_practexam': True},
    """
    return info_dict


def create_printlabel_dict(sel_examyear, sel_examperiod, sel_layout, envelopsubject_pk_list=None):
    # PR2022-10-10
    # values of sel_layout are: "no_errata", "errata_only", "all" , None

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- create_printlabel_dict ----- ')
        logger.debug('    sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))
        logger.debug('    sel_examperiod: ' + str(sel_examperiod) + ' ' + str(type(sel_examperiod)))
        logger.debug('    sel_layout: ' + str(sel_layout) + ' ' + str(type(sel_layout)))
        logger.debug('    envelopsubject_pk_list: ' + str(envelopsubject_pk_list) + ' ' + str(type(envelopsubject_pk_list)))

    printlabel_dict = {}

    printlabel_rows = subj_calc.create_printlabel_rows(
        sel_examyear=sel_examyear,
        sel_examperiod=sel_examperiod,
        sel_layout=sel_layout,
        envelopsubject_pk_list=envelopsubject_pk_list)

    for row in printlabel_rows:
        if logging_on:
            logger.debug(' >>>   printlabel_row: ' + str(row))
        """
        school_subject_count_row:  {'subjbase_id': 149, 'ete_exam': False, 'id_key': '2_0_149_0', 'lang': 'nl', 
            'country_id': 1, 'sb_code': 'CUR13', 'lvl_abbrev': None, 'dep_abbrev': 'H.A.V.O.', 'subj_name': 'Wiskunde A', 
            'schoolbase_id': 13, 'school_name': 'Abel Tasman College', 'depbase_id': 2, 'lvlbase_id': None, 
            'subj_count': 13, 'extra_count': 7, 'tv2_count': 5}
        printlabel_row: {
            'env_subj_id': 76, 'dep_id': 10, 'lvl_id': 10, 'subj_id': 259, 
            'firstdate': datetime.date(2022, 4, 18), 'lastdate': None, 
            'starttime': '07.30', 'endtime': '09.30', 'has_errata': False, 
            'depbase_id': 1, 'lvlbase_id': 6, 'subjbase_id': 133, 
            'bnd_name': 'Voorbeeld etikettenbundel', 'bndlbl_sequence': 1, 
            'lbl_name': 'Voorbeeld etiket', 'is_errata': False, 'is_variablenumber': False, 
            'numberofenvelops': 1, 'numberinenvelop': 0, 
            'content_nl_arr': ['Correctievoorschrift (2 ex)', 'Opgavenboek', 'Minitoets ond. A - B - C - D (rood & blauw)', 'Minitoets ond. A - B (rood & blauw)', 'Minitoets ond. A - C (rood & blauw)', 'Minitoets ond. A (rood & blauw)', 'Uitwerkbijlage'], 
            'content_en_arr': ['Scoring Instruction (2 ex)', 'Assignment book', 'Mini-test part A - B - C - D (red & blue)', 'Mini-test part A - B (red & blue)', 'Mini-test part A - C (red & blue)', 'Mini-test part A (red & blue)', 'Work appendix'], 
            'content_pa_arr': ['Reglamento di korekshon (2 ex)', 'Buki di tarea', 'Mini-prueba èks. A - B - C - D (kòrá & blou)', 'Mini-prueba èks. A - B (kòrá & blou)', 'Mini-prueba èks. A - C (kòrá & blou)', 'Mini-prueba èks. A (kòrá & blou)', 'Anekso di elaborashon'], 
            'instruction_nl_arr': ['NIET EERDER OPENEN, DAN NA AFLOOP VAN DE EXAMENZITTING.', 'EERST DE NAAM VAN HET EXAMEN, DATUM EN TIJDSDUUR VOORLEZEN, DAARNA OPENEN!', None, None, None, None, None], 
            'instruction_en_arr': ['DO NOT OPEN BEFORE THE EXAMINATION SESSION HAS ENDED.', 'FIRST READ THE EXAM NAME, DATE AND TIME, THEN OPEN!', None, None, None, None, None], 
            'instruction_pa_arr': ['NO HABRI PROMÉ KU E SESHON DI ÈKSAMEN FINALISÁ.', 'LESA PROMÉ NA BOS HALTU ÈKSAMEN, FECHA I DURASHON PROMÉ KU HABRI!', None, None, None, None, None], 
            'content_color_arr': ['red', 'black', 'black', 'black', 'black', 'black', 'black'], 
            'instruction_color_arr': ['red', 'red', 'red', 'red', 'red', 'red', None], 
            'content_font_arr': [None, None, None, None, None, 'None, None], 
            'instruction_font_arr': [None, None, None, None, None, 'None, None], 
            'sequence_arr': [1, 2, 61, 62, 63, 64, 65]}
        """
        id_key = row.get('id_key')

        if id_key not in printlabel_dict:
            printlabel_dict[id_key] = []
        printlabel_dict[id_key].append(row)

    if logging_on:
        logger.debug('    printlabel_dict: ' + str(printlabel_dict))

    return printlabel_dict
# - end of create_printlabel_dict


def create_exam_count_dictNIU(sel_examyear, exam_pk_list=None):
    exam_count_dict = {}
    # function count exams per subject / level / department and puts it in a dictionary.
    # dict key is '1_4_112_1' ( dep_id _ lvl_id _ subj_id _ examperiod )
    if sel_examyear :
        try:
            sql_keys = {'ey_id': sel_examyear.pk}

            sql_list = [
                "SELECT dep.id AS dep_id, lvl.id AS lvl_id, subj.id AS subj_id, exam.examperiod, count(*) AS exam_count",

                "FROM subjects_exam AS exam",
                "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = exam.department_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = exam.level_id)",

                "WHERE dep.examyear_id = %(ey_id)s::INT",
            ]

            if exam_pk_list:
                sql_keys['exam_pk_lst'] = exam_pk_list
                sql_list.append('AND exam.id IN (SELECT UNNEST( %(exam_pk_lst)s::INT[]))')

            sql_list.append("GROUP BY dep.id, lvl.id, subj.id, exam.examperiod")

            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                for row in cursor.fetchall():

                    exam_count_key = '_'.join((
                        str(row[0]),
                        str(row[1] or 0),
                        str(row[2]),
                        str(row[3] or 0)
                    ))
                    exam_count_dict[exam_count_key] = (row[4] or 0)

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    logger.debug(' >>> exam_count_dict: ' + str(exam_count_dict))

    return exam_count_dict
# - end of create_exam_count_dict


@method_decorator([login_required], name='dispatch')
class EnvelopPrintCheckView(View):  # PR2022-08-19 PR2022-10-10

    def post(self, request):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug('')
            logger.debug(' ============= EnvelopPrintCheckView ============= ')

        update_wrap = {}
        messages = []

# - get upload_dict from request.POST
        upload_json = request.POST.get('upload', None)
        if upload_json:
            upload_dict = json.loads(upload_json)
            mode = upload_dict.get('mode')
            errata_only = mode == 'errata_only'

            # - reset language
            user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get permit
            page_name = 'page_orderlist'
            has_permit = acc_prm.get_permit_crud_of_this_page(page_name, request)

            if logging_on:
                logger.debug('    has_permit: ' + str(has_permit))
                logger.debug('    upload_dict: ' + str(upload_dict))
            """
            upload_dict: {'table': 'envelopitem', 'mode': 'create', 'content_nl': 'aa', 'content_color': 'blue'}
            upload_dict: {'table': 'envelopitem', 'mode': 'delete', 'envelopitem_pk': 2, 'map_id': 'envelopitem_2'}
            upload_dict: {'check': True}
            """

            if has_permit:

# ----- get selected examyear from usersettings
                sel_examyear, may_edit, error_list = acc_view.get_selected_examyear_from_usersetting(request, True)  # allow_not_published = True
                if logging_on:
                    logger.debug('sel_examyear:   ' + str(sel_examyear))
                    logger.debug('may_edit:       ' + str(may_edit))

                if error_list:
                    error_list.append(str(_('You cannot make changes.')))
                    err_html = '<br>'.join(error_list)
                    messages.append({'header': str(_('Download labels')), 'class': "border_bg_invalid", 'msg_html': err_html})
                else:

# - get selected examperiod from usersettings
                    sel_examperiod, sel_examtype_NIU, sel_subject_pk_NIU = acc_view.get_selected_experiod_extype_subject_from_usersetting(request)
                    if logging_on:
                        logger.debug('sel_examperiod:   ' + str(sel_examperiod))

# +++ get schoolbase dictlist
                    # functions creates ordered dictlist of all schoolbase_pk, schoolbase_code and school_name
                    # of this exam year of all countries when req_usr country = cur, or only sxm when req_usr country = sxm,
                    schoolbase_dictlist = subj_view.create_schoolbase_dictlist(sel_examyear, request)

# +++ get nested dicts of subjects per school, dep, level, lang, ete_exam
                    #count_rows = subj_calc.create_studsubj_count_rows(
                    #    sel_examyear_instance=sel_examyear,
                    #    sel_examperiod=sel_examperiod,
                    #    request=request
                    #)
                    """
                    row: {'subjbase_id': 121, 'ete_exam': True, 'lang': 'en', 
                        'country_id': 2, 'sb_code': 'SXM01', 
                        'lvl_abbrev': 'PBL', 'dep_abbrev': 'V.S.B.O.', 'subj_name': 'Wiskunde', 
                        'schoolbase_id': 30, 'school_name': 'Milton Peters College', 
                        'depbase_id': 1, 'lvlbase_id': 6, 
                        'subj_count': 11, 
                        'extra_count': 4, 
                        'tv2_count': 5}
                    """

                    envelopsubject_rows = get_envelopsubject_rows(
                        sel_examyear=sel_examyear,
                        append_dict={},
                        errata_only=errata_only
                    )

                    if logging_on:
                        for row in envelopsubject_rows:
                            logger.debug('  #########  envelopsubject_row: ' + str(row))

                    update_wrap['checked_envelopsubject_rows'] = envelopsubject_rows
                    update_wrap['checked_envelop_school_rows'] = schoolbase_dictlist


            # - check if Enveloporderlist of this examyear exists, return modifiedat if exists
                    enveloporderlist = subj_mod.Enveloporderlist.objects.filter(
                        examyear=sel_examyear
                    ).order_by('-pk').first()
                    enveloporderlist_modifiedat = enveloporderlist.modifiedat if enveloporderlist else None
                    if enveloporderlist_modifiedat:
                        update_wrap['updated_enveloporderlist_modifiedat'] = enveloporderlist_modifiedat

                    if logging_on:
                        logger.debug('    enveloporderlist: ' + str(enveloporderlist))


    # - addd messages to update_wrap
        if messages:
            update_wrap['messages'] = messages

# - return update_wrap
        return HttpResponse(json.dumps(update_wrap, cls=af.LazyEncoder))
# - end of EnvelopPrintCheckView


@method_decorator([login_required], name='dispatch')
class EnvelopPrintView(View):  # PR2022-08-19 PR2022-10-10

    def get(self, request, lst):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= EnvelopPrintView ============= ')
            logger.debug('    lst: ' + str(lst))
            """
            lst: {"subject_list":[12],"schoolbase_list":[2,5],"sel_layout":"none","lvlbase_pk_list":[]}
            lst: {"exam_pk_list":[34],"schoolbase_pk_list":[2],"subjbase_pk_list":[133],"sel_layout":"errata_only"}
            lst: {"envelopsubject_pk_list":[76],"sel_layout":"all"}  
            """

    # paper size of labels is: 'Statement', Width: 21.59 cm Height: 13.97 cm or 8.5 inch x 5.5 inch or 612 x 396 points
    # pagesize A4  = (595.27, 841.89) points, 1 point = 1/72 inch

        response = None

        if request.user and request.user.country and request.user.schoolbase and lst:
            upload_dict = json.loads(lst)

            req_user = request.user

# - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get selected examyear, school and department from usersettings
            sel_examyear, sel_schoolNIU, sel_departmentNIU, sel_level, may_edit, msg_list = \
                acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

# - get selected examperiod from usersettings
            sel_examperiod, sel_examtype_NIU, sel_subject_pk_NIU = acc_view.get_selected_experiod_extype_subject_from_usersetting(request)
            # PR2022-08-27 debug: saved sel_examperiod was 12 (deprecated, 12 was all exam periods), change it to 1
            if sel_examperiod not in (1,2,3):
                sel_examperiod = 1

            if sel_examperiod:
                # sel_layout values are: 'no_errata', 'errata_only', 'all' , None, 'show_errata_always'
                sel_layout = upload_dict.get('sel_layout')

                subjbase_pk_list = upload_dict.get('subjbase_pk_list')

                envelopsubject_pk_list = upload_dict.get('envelopsubject_pk_list')

                # when schoolbase_pk_list has value [-1], it means that all schools must be printed
                # when schoolbase_pk_list has value None, it means that no schools must be printed

                schoolbase_pk_list = upload_dict.get('schoolbase_pk_list')

                print_without_schools = False
                if schoolbase_pk_list is None:
                    print_without_schools = True
                    sel_layout = 'show_errata_always'
                elif not len(schoolbase_pk_list):
                    print_without_schools = True
                    sel_layout = 'show_errata_always'
                elif schoolbase_pk_list[0] == -1:
                    schoolbase_pk_list = None

                if logging_on:
                    logger.debug('    sel_examperiod: ' + str(sel_examperiod))
                    logger.debug('    sel_layout:     ' + str(sel_layout))
                    logger.debug('    schoolbase_pk_list: ' + str(schoolbase_pk_list))
                    logger.debug('    envelopsubject_pk_list:   ' + str(envelopsubject_pk_list))
                    logger.debug('    print_without_schools:   ' + str(print_without_schools))

# --- get department dictlist, ordered by sequence
                # fields are: depbase_id, depbase_code, dep_name, dep_level_req
                department_dictlist = subj_view.create_department_dictlist(sel_examyear)
                """
                department_dictlist: [
                    {'depbase_id': 1, 'depbase_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'dep_level_req': True}, 
                    {'depbase_id': 2, 'depbase_code': 'Havo', 'dep_name': 'Hoger Algemeen Voortgezet Onderwijs', 'dep_level_req': False}, 
                    {'depbase_id': 3, 'depbase_code': 'Vwo', 'dep_name': 'Voorbereidend Wetenschappelijk Onderwijs', 'dep_level_req': False}]
                """

# --- get lvlbase dictlist, ordered by sequence
                lvlbase_dictlist = subj_view.create_level_dictlist(sel_examyear)
                """
                lvlbase_dictlist: [
                    {'lvlbase_id': 6, 'lvlbase_code': 'PBL', 'lvl_name': 'Praktisch Basisgerichte Leerweg'}, 
                    {'lvlbase_id': 5, 'lvlbase_code': 'PKL', 'lvl_name': 'Praktisch Kadergerichte Leerweg'}, 
                    {'lvlbase_id': 4, 'lvlbase_code': 'TKL', 'lvl_name': 'Theoretisch Kadergerichte Leerweg'}, 
                    {'lvlbase_id': 0, 'lvlbase_code': '', 'lvl_name': ''}]
                """

# - get dict with schemeitem info per dep and lvl
                # schemeitem_dict is  filtered by department.examyear_id
                schemeitem_dict = get_schemeitem_info_per_dep_lvl(sel_examyear)

# - get envelop label info
                printlabel_dict = create_printlabel_dict(
                    sel_examyear=sel_examyear,
                    sel_examperiod=sel_examperiod,
                    sel_layout=sel_layout,
                    envelopsubject_pk_list=envelopsubject_pk_list
                )

# +++ create enveloplabel_pdf without school
                if print_without_schools:
                    pdf = create_enveloplabel_pdf_without_school(
                        sel_examyear=sel_examyear,
                        schemeitem_dict=schemeitem_dict,
                        printlabel_dict=printlabel_dict,
                        envelopsubject_pk_list=envelopsubject_pk_list
                    )
                else:

# +++ create enveloplabel_pdf per school

    # - get schoolbase dictlist
                    # functions creates ordered dictlist of all schoolbase_pk, schoolbase_code and school_name
                    #  of this exam year of all countries (only SXM when requsr=sxm), ordered by code
                    # filtered by schoolbase_pk_list
                    schoolbase_dictlist = subj_view.create_schoolbase_dictlist(sel_examyear, request, schoolbase_pk_list)
                    if logging_on:
                        logger.debug('    schoolbase_dictlist: ' + str(schoolbase_dictlist))
                    """
                    schoolbase_dictlist: [
                        {'sbase_id': 2, 'sbase_code': 'CUR01', 'depbases': '1', 'sch_otherlang': None, 'sch_article': 'de', 'sch_name': 'Ancilla Domini Vsbo', 'sch_abbrev': 'Ancilla Domini', 'defaultrole': 8}, 
                        {'sbase_id': 3, 'sbase_code': 'CUR02', 'depbases': '1', 'sch_otherlang': None, 'sch_article': 'de', 'sch_name': 'Skol Avansá Amador Nita', 'sch_abbrev': 'SAAN', 'defaultrole': 8}, 

                        {'sbase_id': 33, 'sbase_code': 'SXM04', 'depbases': '1;2;3', 'sch_otherlang': 'en', 'sch_article': 'de', 'sch_name': 'Landsexamens Sint Maarten', 'sch_abbrev': 'LEX St. Maarten', 'defaultrole': 8}, 
                        {'sbase_id': 34, 'sbase_code': 'SXMDOE', 'depbases': '1;2;3', 'sch_otherlang': 'en', 'sch_article': 'de', 'sch_name': 'Division of Examinations', 'sch_abbrev': 'Division of Examinations', 'defaultrole': 64}]  
                    """

# +++ get dict with number of studsubj. PR2022-10-14
                    # if orderlist is published: Enveloporderlist exists and orderdict has value
                    #   get envelop_count_per_school_dict from enveloporderlist
                    # if orderlist is not published: create envelop_count_per_school_dict

    # - get existing Enveloporderlist of this examyear
                    # it contains 1 row per examyear with orderdict with amount
                    enveloporderlist = subj_mod.Enveloporderlist.objects.filter(
                        examyear=sel_examyear
                    ).order_by('-pk').first()
                    if logging_on:
                        logger.debug('    enveloporderlist: ' + str(enveloporderlist))

    # - get envelop_count_per_school_dict from enveloporderlist.orderdict
                    envelop_count_per_school_dict = None
                    if enveloporderlist and enveloporderlist.orderdict:
                        envelop_count_per_school_dict = json.loads(enveloporderlist.orderdict)
                        if logging_on and False:
                            logger.debug('    enveloporderlist.orderdict: ' + str(enveloporderlist.orderdict))

    # - remove schools that are not in schoolbase_pk_list
                        if schoolbase_pk_list:
                            # because of error 'dictionary changed size during iteration':
                            # first store keys in list, then remove them
                            keys_tobe_removed = []
                            for envelop_sbase_pk_str in envelop_count_per_school_dict:
                # - check if schoolbase_pk exists in schoolbase_pk_list
                                key_exists_in_list = False
                                for schoolbase_pk in schoolbase_pk_list:
                                    if envelop_sbase_pk_str == str(schoolbase_pk):
                                        key_exists_in_list = True
                                        break
                # - add key to keys_tobe_removed list if it does not exist in schoolbase_pk_list
                                if not key_exists_in_list:
                                    keys_tobe_removed.append(envelop_sbase_pk_str)

                # - remove keys that don't exist in schoolbase_pk_list
                            if keys_tobe_removed:
                                for sbase_pk_str in keys_tobe_removed:
                                    envelop_count_per_school_dict.pop(sbase_pk_str, None)

    # ---use existing envelop_count_per_school_dict if it exists
                    if envelop_count_per_school_dict:
                        if logging_on:
                            logger.debug(' >>>>>>>> published envelop_count_per_school_dict is used')
                            #logger.debug('envelop_count_per_school_dict: ' + str(envelop_count_per_school_dict))
                        """
                        envelop_count_per_school_dict: {
                            '34': {'c': '-', 
                                '0': {'c': '-', 
                                    '0': [{'subjbase_id': None, 'ete_exam': None, 'id_key': None, 'subjbase_code': None, 'lang': 'nl', 'country_id': 2, 'schoolbase_id': 34, 'depbase_id': None, 'lvlbase_id': None, 'subj_count': None, 'extra_count': 0, 'tv2_count': 0}]}}}
                        """
                    else:
    # --- or create new existing envelop_count_per_school_dict if it does not yet existexists
                        count_dictNIU, envelop_count_per_school_dict = subj_calc.create_studsubj_count_dict(
                            sel_examyear_instance=sel_examyear,
                            sel_examperiod=sel_examperiod,
                            request=request,
                            schoolbase_pk_list=schoolbase_pk_list,
                            subjbase_pk_list=subjbase_pk_list
                        )
                        if logging_on:
                            logger.debug(' ---- calculated envelop_count_per_school_dict is used')
    # --- print labels
                    pdf = create_enveloplabel_pdf_with_school(
                        sel_examyear=sel_examyear,
                        sel_examperiod=sel_examperiod,
                        schoolbase_dictlist=schoolbase_dictlist,
                        department_dictlist=department_dictlist,
                        lvlbase_dictlist=lvlbase_dictlist,
                        schemeitem_dict=schemeitem_dict,
                        printlabel_dict=printlabel_dict,
                        count_per_school_dict=envelop_count_per_school_dict
                    )

                # pdf_file = File(temp_file)

                # was: buffer.close()

                """
                # TODO as test try to save file in
                studsubjnote = stud_mod.Studentsubjectnote.objects.get_or_none(pk=47)
                content_type='application/pdf'
                file_name = 'test_try.pdf'
                if studsubjnote and pdf_file:
                    instance = stud_mod.Noteattachment(
                        studentsubjectnote=studsubjnote,
                        contenttype=content_type,
                        filename=file_name,
                        file=pdf_file)
                    instance.save()
                    logger.debug('instance.saved: ' + str(instance))
                # gives error: 'bytes' object has no attribute '_committed'
                """

                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="Labels.pdf"'

                response.write(pdf)

        #except Exception as e:
       #     logger.error(getattr(e, 'message', str(e)))
       #     raise Http404("Error creating Ex2A file")

        if response:

            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of EnvelopPrintView
#####################################


def create_enveloplabel_pdf_with_school(sel_examyear, sel_examperiod, schoolbase_dictlist, department_dictlist,
                                        lvlbase_dictlist,
                                        schemeitem_dict, printlabel_dict, count_per_school_dict):
    # PR2022-08-19 PR2022-09-03 PR2022-10-12
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' --- create_enveloplabel_pdf_with_school  -----')
        # logger.debug('    count_per_school_dict: ' + str(count_per_school_dict))

    # https://stackoverflow.com/questions/43373006/django-reportlab-save-generated-pdf-directly-to-filefield-in-aws-s3

    af.register_font_arial()
    af.register_font_calibri()

    # PR2021-04-28 from https://docs.python.org/3/library/tempfile.html
    # temp_file = tempfile.TemporaryFile()
    # canvas = Canvas(temp_file)
    buffer = io.BytesIO()
    canvas = Canvas(buffer)

    # PR2022-05-05 debug Oscar Panneflek Vpco lines not printing on Ex3
    # turn off setLineWidth (0)
    # canvas.setLineWidth(0)

    # paper size of labels is: 'Statement', Width: 21.59 cm Height: 13.97 cm or 8.5 inch x 5.5 inch or 612 x 396 points
    canvas.setPageSize(
        (612, 396))  # some page size, given as a tuple in points pdf.setPageSize((width,height)

    max_rows = 30  # was:  24
    line_height = 6.73 * mm  # was:  8 * mm

    # TODO if school_list = None: create fake school, to print labels before schools have submitted Ex1
    """
    school_subject_count_row:  {'subjbase_id': 149, 'ete_exam': False, 'id_key': '2_0_149_0', 'lang': 'nl', 
        'country_id': 1, 'sb_code': 'CUR13', 'lvl_abbrev': None, 'dep_abbrev': 'H.A.V.O.', 'subj_name': 'Wiskunde A', 
        'schoolbase_id': 13, 'school_name': 'Abel Tasman College', 'depbase_id': 2, 'lvlbase_id': None, 
        'subj_count': 13, 'extra_count': 7, 'tv2_count': 5}

    count_per_school_dict: {
        "2": {"sb_code": "CUR01", "school_name": "Ancilla Domini Vsbo", 
            "1": {"depbase_code": "Vsbo", "school_name": "Ancilla Domini Vsbo",
                "6": [{"subjbase_id": 133, "ete_exam": true, "id_key": "1_6_133_1_1", "lang": "nl", 
                    "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PBL", "depbase_code": "Vsbo", 
                    "subj_name": "Administratie en commercie", 
                    "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", 
                    "depbase_id": 1, "lvlbase_id": 6, 
                    "subj_count": 13, "exam_count": 2, "dep_sequence": 1, "lvl_sequence": 1, 
                    "subjbase_code": "ac", "extra_count": 7, "tv2_count": 5}],            

    count_per_school_dict: {
    "2": {"sb_pk": 2, 
            "1_6_131": [22, 8, 5],
             "1_4_120": [59, 6, 15], 
    "34": {"sb_pk": 34, 
            "0": [0, 0, 0]}}

    """

    receipt_total_list = []

    # +++ loop through list of all schools
    for schoolbase_dict in schoolbase_dictlist:
        """
        schoolbase_dict: {'sbase_id': 2, 'sbase_code': 'CUR01', 'depbases': '1', 'sch_otherlang': None, 
            'sch_article': 'de', 'sch_name': 'Ancilla Domini Vsbo', 'sch_abbrev': 'Ancilla Domini', 'defaultrole': 8}
        """
        sbase_id = str(schoolbase_dict.get('sbase_id') or 0)
        school_name = schoolbase_dict.get('sch_name') or ''
        school_lang = schoolbase_dict.get('sch_otherlang') or 'nl'
        if logging_on:
            logger.debug('>>> schoolbase_dict: ' + str(schoolbase_dict))
            logger.debug('    sbase_id: ' + str(sbase_id))
            logger.debug('    school_name: ' + str(school_name))
            logger.debug('    school_lang: ' + str(school_lang))

        schoolbase_count_dict = count_per_school_dict.get(sbase_id)
        if logging_on and False:
            logger.debug('    schoolbase_count_dict: ' + str(schoolbase_count_dict))
        """
        schoolbase_count_dict: {'sb_code': '-', 'school_name': '-', 
            1: {'depbase_code': '-', 'school_name': '-', 
                6: [{'subjbase_id': 131, 'ete_exam': True, 'id_key': '1_6_131', 'lang': 'nl', 'country_id': 1, 
                    'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 6, 
                    'subj_count': 22, 'extra_count': 8, 'tv2_count': 5}, 
                    {'subjbase_id': 124, 'ete_exam': True,    
        """

        # - check if school exists in print_dict
        if schoolbase_count_dict:

            # +++ loop through list of all departments
            """
            department_dictlist: [
                {'depbase_id': 1, 'depbase_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'dep_level_req': True}, 
                {'depbase_id': 2, 'depbase_code': 'Havo', 'dep_name': 'Hoger Algemeen Voortgezet Onderwijs', 'dep_level_req': False}, 
                {'depbase_id': 3, 'depbase_code': 'Vwo', 'dep_name': 'Voorbereidend Wetenschappelijk Onderwijs', 'dep_level_req': False}]
            """
            for department_dict in department_dictlist:

                depbase_id = str(department_dict.get('depbase_id') or 0)
                dep_name = department_dict.get('dep_name') or ''

                # - check if department exists in schoolbase_count_dict
                # print_rows contains a list of subj/dep/level/examperiod/ete_exam combination (without link to exams)
                # with the number of exams-items , including extra exams. Blue/red version are taken in account
                # and count of different examns for the subject (blue/ red)
                depbase_count_dict = schoolbase_count_dict.get(depbase_id)
                if logging_on:
                    logger.debug('    depbase_count_dict: ' + str(depbase_count_dict))
                """
                depbase_count_dict: {'depbase_code': '-', 'school_name': '-', 
                    6: [{'subjbase_id': 131, 'ete_exam': True, 'id_key': '1_6_131', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 22, 'extra_count': 8, 'tv2_count': 5}, 
                        {'subjbase_id': 124, 'ete_exam': True, 'id_key': '1_6_124', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 22, 'extra_count': 8, 'tv2_count': 5},
                """
                if depbase_count_dict:

                    # +++ loop through list of all levels
                    """
                    lvlbase_dictlist: [
                        {'lvlbase_id': 6, 'lvlbase_code': 'PBL', 'lvl_name': 'Praktisch Basisgerichte Leerweg'}, 
                        {'lvlbase_id': 5, 'lvlbase_code': 'PKL', 'lvl_name': 'Praktisch Kadergerichte Leerweg'}, 
                        {'lvlbase_id': 4, 'lvlbase_code': 'TKL', 'lvl_name': 'Theoretisch Kadergerichte Leerweg'}, 
                        {'lvlbase_id': 0, 'lvlbase_code': '', 'lvl_name': ''}]
                    """
                    for lvlbase_dict in lvlbase_dictlist:
                        lvlbase_id = str(lvlbase_dict.get('lvlbase_id') or 0)
                        lvl_name = lvlbase_dict.get('lvl_name') or ''

                        # - check if level exists in schoolbase_count_dict
                        # print_rows contains a list of subj/dep/level/examperiod/ete_exam combination (without link to exams)
                        # with the number of exams-items , including extra exams. Blue/red version are taken in account
                        # and count of different examns for the subject (blue/ red)
                        lvlbase_count_list = depbase_count_dict.get(lvlbase_id)
                        """
                        lvlbase_count_list: [
                            {'subjbase_id': 131, 'ete_exam': True, 'id_key': '1_6_131', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 22, 'extra_count': 8, 'tv2_count': 5}, 
                            {'subjbase_id': 124, 'ete_exam': True, 'id_key': '1_6_124', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 22, 'extra_count': 8, 'tv2_count': 5}, 
                            {'subjbase_id': 155, 'ete_exam': True, 'id_key': '1_6_155', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 17, 'extra_count': 3, 'tv2_count': 5}, 
                            {'subjbase_id': 123, 'ete_exam': True, 'id_key': '1_6_123', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 22, 'extra_count': 8, 'tv2_count': 5}, 
                            {'subjbase_id': 114, 'ete_exam': True, 'id_key': '1_6_114', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 39, 'extra_count': 6, 'tv2_count': 10}, 
                            {'subjbase_id': 121, 'ete_exam': True, 'id_key': '1_6_121', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 17, 'extra_count': 3, 'tv2_count': 5}, 
                            {'subjbase_id': 113, 'ete_exam': True, 'id_key': '1_6_113', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 39, 'extra_count': 6, 'tv2_count': 10}, 
                            {'subjbase_id': 133, 'ete_exam': True, 'id_key': '1_6_133', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 17, 'extra_count': 3, 'tv2_count': 5}, 
                            {'subjbase_id': 118, 'ete_exam': True, 'id_key': '1_6_118', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 39, 'extra_count': 6, 'tv2_count': 10}]
                        """

                        # +++ loop through list of subject of this dep / level of this school
                        if lvlbase_count_list:
                            if logging_on:
                                logger.debug('  --lvlbase_count_list: ' + str(lvlbase_count_list))

                            # - create dict with info for receipt per school/dep/lvl
                            receipt_school_dep_lvl_dict = {
                                'school_name': school_name,
                                'dep_name': dep_name,
                                'lvl_name': lvl_name,
                                'total_envelops': 0,
                                'total_items': 0,
                                'exam_list': []
                            }
                            receipt_exam_list = receipt_school_dep_lvl_dict.get('exam_list')

                            receipt_school_dep_lvl_total_envelops = 0
                            receipt_school_dep_lvl_total_items = 0

                            if logging_on:
                                logger.debug('  ')
                                logger.debug(' --- loop through lvlbase_count_list  -----')

                            for lvlbase_count_row in lvlbase_count_list:
                                if logging_on and False:
                                    logger.debug('.. lvlbase_count_row: ' + str(lvlbase_count_row))
                                """                         
                                lvlbase_count_row: {'subjbase_id': 131, 'ete_exam': True, 'id_key': '1_6_131', 'lang': 'nl', 
                                            'country_id': 1, 'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 6, 
                                            'subj_count': 22, 'extra_count': 8, 'tv2_count': 5}   
                                """

                                receipt_count_dict = {'subj_name': '', 'total_items': 0, 'total_envelops': 0,
                                                      'has_errata': False}

                                # +++ lookup labels with id_key and loop through labels of printlabel_list
                                id_key = lvlbase_count_row.get('id_key')
                                lbl_list = printlabel_dict.get(id_key)
                                if lbl_list:

                                    # - get tv_count if lbl_list of this id_key exists
                                    subj_count = lvlbase_count_row.get('subj_count') or 0
                                    extra_count = lvlbase_count_row.get('extra_count') or 0
                                    if sel_examperiod == c.EXAMPERIOD_FIRST:
                                        tv_count = subj_count + extra_count
                                    elif sel_examperiod == c.EXAMPERIOD_SECOND:
                                        tv_count = lvlbase_count_row.get('tv2_count') or 0
                                    else:
                                        tv_count = 0

                                    if logging_on:
                                        logger.debug('    subj_count: ' + str(subj_count))
                                        logger.debug('    extra_count: ' + str(extra_count))
                                        logger.debug('    tv_count: ' + str(tv_count))
                                        logger.debug('....for lbl_dict in lbl_list: ')

                                    for lbl_dict in lbl_list:
                                        if logging_on:
                                            logger.debug('lbl_dict: ' + str(lbl_dict))
                                        """
                                        lbl_dict: {'env_subj_id': 40, 'dep_id': 10, 'lvl_id': 10, 'subj_id': 238, 
                                                    'firstdate': datetime.date(2023, 5, 10), 'lastdate': None, 
                                                    'starttime': '07.30', 'endtime': '09.30', 
                                                    'has_errata': False, 
                                                    'depbase_id': 1, 'lvlbase_id': 6, 'subjbase_id': 123, 
                                                    'id_key': '1_6_123', 
                                                    'bnd_name': 'EXACT VK- BIO-PBL-CSE ', 'bndlbl_sequence': 137, 
                                                    'lbl_name': 'BIO-PBL ', 'is_errata': False, 
                                                    'is_variablenumber': True, 'numberofenvelops': None, 'numberinenvelop': 15, 
                                                    'content_nl_arr': ['Opgavenboek'], 
                                                    'content_en_arr': ['Assignment book'], 
                                                    'content_pa_arr': ['Buki di tarea'], 
                                                    'instruction_nl_arr': ['EERST DE NAAM VAN HET EXAMEN, DATUM EN TIJDSDUUR VOORLEZEN, DAARNA OPENEN!'], 
                                                    'instruction_en_arr': ['FIRST READ THE EXAM NAME, DATE AND TIME, THEN OPEN!'], 
                                                    'instruction_pa_arr': ['LESA PROMÉ NA BOS HALTU ÈKSAMEN, FECHA I DURASHON PROMÉ KU HABRI!'], 
                                                    'content_color_arr': ['black'], 
                                                    'instruction_color_arr': ['red'], 
                                                    'sequence_arr': [56]}
                                        """
                                        # get dep abbrev and lvl_abbrev, sub_name
                                        dep_pk = lbl_dict.get('dep_id')
                                        lvl_pk = lbl_dict.get('lvl_id') or 0
                                        subj_pk = lbl_dict.get('subj_id')
                                        examperiod = lbl_dict.get('examperiod')
                                        firstdate = lbl_dict.get('firstdate')
                                        lastdate = lbl_dict.get('lastdate')
                                        starttime = lbl_dict.get('starttime')
                                        endtime = lbl_dict.get('endtime')
                                        has_errata = lbl_dict.get('has_errata') or False

                                        # is_errata labels are filtered out in create_printlabel_rows
                                        # no need to get is_errata here
                                        #  was: is_errata = lbl_dict.get('is_errata') or False
                                        is_variablenumber = lbl_dict.get('is_variablenumber') or False
                                        numberofenvelops = lbl_dict.get('numberofenvelops') or 0
                                        numberinenvelop = lbl_dict.get('numberinenvelop') or 0
                                        # was: exam_count = lbl_dict.get('exam_count')

                                        bnd_lbl_name = ' - '.join(
                                            (lbl_dict.get('bnd_name') or '-', lbl_dict.get('lbl_name') or '-'))

                                        if logging_on:
                                            logger.debug(' ----- school_name:  ' + str(school_name))
                                            logger.debug('       bnd_lbl_name: ' + str(bnd_lbl_name))
                                            logger.debug('       is_variablenumber: ' + str(is_variablenumber))
                                            logger.debug('       numberofenvelops: ' + str(numberofenvelops))
                                            logger.debug('       numberinenvelop: ' + str(numberinenvelop))

                                        dep_abbrev, lvl_abbrev, subj_name_nl, subj_name_en, subj_name_pa, version = None, None, None, None, None, None
                                        has_practexam, otherlang_arr = False, []

                                        if dep_pk in schemeitem_dict:
                                            dep_dict = schemeitem_dict.get(dep_pk)
                                            dep_abbrev = dep_dict.get('dep_abbrev')
                                            if lvl_pk in dep_dict:
                                                lvl_dict = dep_dict.get(lvl_pk)
                                                lvl_abbrev = lvl_dict.get('lvl_abbrev')

                                                if subj_pk in lvl_dict:
                                                    subj_dict = lvl_dict.get(subj_pk)
                                                    subj_name_nl = subj_dict.get('subj_name_nl')
                                                    subj_name_en = subj_dict.get('subj_name_en')
                                                    subj_name_pa = subj_dict.get('subj_name_pa')
                                                    has_practexam = subj_dict.get('has_practexam') or False
                                                    otherlang_arr = subj_dict.get('otherlang')
                                                    version = lbl_dict.get('version')

                                                    if logging_on and False:
                                                        logger.debug('       subj_dict: ' + str(subj_dict))
                                                        logger.debug('       printlabel_dict: ' + str(printlabel_dict))
                                                        logger.debug('       version: ' + str(version))

                                        dep_lvl_abbrev = dep_abbrev if dep_abbrev else '---'
                                        if lvl_abbrev:
                                            dep_lvl_abbrev += ' ' + lvl_abbrev
                                        dep_lvl_color = get_dep_lvl_color(dep_abbrev, lvl_abbrev)

                                        # - get language of this school
                                        # in this function tehre is always a school selected
                                        # when there is a school selected: school has only 1 lang per subject. Use that one
                                        # PR2022-10-27 debug: added: use school_lang only when in otherlang_arr, else use 'nl'
                                        # when no school selected: print all languages

                                        if logging_on:
                                            logger.debug(' $$$$ school_lang:  ' + str(school_lang))
                                            logger.debug('       otherlang_arr: ' + str(otherlang_arr))

                                        # school_lang has value of schoolbase_dict.sch_otherlang or 'nl'
                                        lang = 'nl'
                                        if school_lang:
                                            if school_lang in otherlang_arr:
                                                lang = school_lang

                                        if logging_on:
                                            logger.debug(
                                                '+++  school_lang: ' + str(school_lang) + ' ' + str(type(school_lang)))
                                            logger.debug('     otherlang_arr: ' + str(otherlang_arr) + ' ' + str(
                                                type(otherlang_arr)))
                                            logger.debug(' >>> lang: ' + str(lang) + ' ' + str(type(lang)))

                                        # +++ loop through languages of lang_list -
                                        # there is a school selected: therefore tehr is only 1 lang - the lang of the school
                                        # no need for: for lang in lang_list:

                                        # - translate version, get color
                                        # translated_version, version_hex_color = translate_version(version, lang)

                                        subj_name = get_subj_name(lang, subj_name_pa, subj_name_en, subj_name_nl)

                                        if logging_on:
                                            logger.debug(
                                                '       subj_name: ' + str(subj_name) + ' ' + str(type(subj_name)))
                                            logger.debug('       lang: ' + str(lang))

                                        content_key = '_'.join(
                                            (
                                            'content', 'pa' if lang == 'pa' else 'en' if lang == 'en' else 'nl', 'arr'))
                                        instruction_key = '_'.join(
                                            ('instruction', 'pa' if lang == 'pa' else 'en' if lang == 'en' else 'nl',
                                             'arr'))
                                        content_arr = lbl_dict.get(content_key) or []
                                        instruction_arr = lbl_dict.get(instruction_key) or []
                                        content_color_arr = lbl_dict.get('content_color_arr') or []
                                        instruction_color_arr = lbl_dict.get('instruction_color_arr') or []
                                        content_font_arr = lbl_dict.get('content_font_arr') or []
                                        instruction_font_arr = lbl_dict.get('instruction_font_arr') or []

                                        # - calculate number of labels that must be printed
                                        total_envelops = calc_number_of_envelops(sel_examyear, is_variablenumber,
                                                                                 numberinenvelop,
                                                                                 numberofenvelops, tv_count)

                                        # +++ loop through number of labels for this exam and this school
                                        # tv_count / exam_count is always an integer, but because we dont use decimal function the division is 10.0 instead of 10
                                        if is_variablenumber:
                                            # was: total_items = int(tv_count / exam_count) if exam_count > 1 else tv_count
                                            total_items = tv_count
                                            # add to total_items, only when is_variablenumber
                                            receipt_count_dict['total_items'] += total_items
                                            receipt_school_dep_lvl_total_items += total_items

                                        else:
                                            total_items = numberinenvelop * numberofenvelops

                                        receipt_count_dict['subj_name'] = subj_name
                                        if has_errata:
                                            receipt_count_dict['has_errata'] = True

                                        if logging_on and False:
                                            logger.debug(' --- calc_number_of_envelops  -----')
                                            logger.debug('    numberinenvelop: ' + str(numberinenvelop))
                                            logger.debug('    numberofenvelops: ' + str(numberofenvelops))
                                            logger.debug('    total_envelops: ' + str(total_envelops))
                                            logger.debug('  >>total_items: ' + str(total_items))

                                        remaining_items = total_items

                                        for page_index in range(0,
                                                                total_envelops):  # range(start_value, end_value, step), end_value is not included!

                                            if logging_on:
                                                logger.debug('    ...page_index: ' + str(page_index))

                                            numberofenvelops_str = ' '.join((
                                                str(page_index + 1),
                                                'di' if lang == 'pa' else 'of' if lang == 'en' else 'van',
                                                str(total_envelops)
                                            ))

                                            items_in_envelop = 0
                                            itemsinenvelop_str = ''
                                            if remaining_items:
                                                if logging_on and False:
                                                    logger.debug('items_in_envelop: ' + str(items_in_envelop))
                                                    logger.debug('numberinenvelop: ' + str(numberinenvelop))
                                                    logger.debug('remaining_items >= numberinenvelop: ' + str(
                                                        remaining_items >= numberinenvelop))
                                                if remaining_items >= numberinenvelop:
                                                    items_in_envelop = numberinenvelop
                                                    remaining_items -= numberinenvelop
                                                else:
                                                    items_in_envelop = remaining_items
                                                    remaining_items = 0

                                            if logging_on:
                                                logger.debug('       items_in_envelop: ' + str(items_in_envelop))
                                                logger.debug('       numberinenvelop: ' + str(numberinenvelop))
                                                logger.debug('       remaining_items: ' + str(remaining_items))

                                            if total_envelops > 1:
                                                itemsinenvelop_str = ' '.join((
                                                    str(items_in_envelop),
                                                    'di' if lang == 'pa' else 'of' if lang == 'en' else 'van',
                                                    str(total_items)
                                                ))
                                            elif total_items:
                                                itemsinenvelop_str = str(total_items)

                                            if logging_on:
                                                logger.debug('       total_envelops: ' + str(total_envelops))
                                                logger.debug('       itemsinenvelop_str: ' + str(itemsinenvelop_str))

                                            draw_label(canvas, sel_examyear, examperiod, dep_lvl_abbrev, dep_lvl_color,
                                                       subj_name, school_name,
                                                       has_practexam, firstdate, lastdate, starttime, endtime,
                                                       numberofenvelops_str,
                                                       itemsinenvelop_str, lang, bnd_lbl_name,
                                                       content_arr, instruction_arr,
                                                       content_color_arr, instruction_color_arr,
                                                       content_font_arr, instruction_font_arr
                                                       )

                                            canvas.showPage()

                                            receipt_count_dict['total_envelops'] += 1
                                            receipt_school_dep_lvl_total_envelops += 1

                                    receipt_exam_list.append(receipt_count_dict)

                                # receipt_count_dict = {'subj_name': '', 'total_items': 0, 'total_envelops': 0, 'has_errata': False}

                            # add receipt_info_dict to list
                            if receipt_school_dep_lvl_total_envelops:
                                receipt_school_dep_lvl_dict['total_envelops'] = receipt_school_dep_lvl_total_envelops
                                receipt_school_dep_lvl_dict['total_items'] = receipt_school_dep_lvl_total_items
                                receipt_total_list.append(receipt_school_dep_lvl_dict)
                            if logging_on:
                                logger.debug('----receipt_total_list: ' + str(receipt_total_list))

                """
                receipt_total_list: [
                    {'school_name': 'Ancilla Domini Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'lvl_name': 'Praktisch Basisgerichte Leerweg', 
                        'total_envelops': 7, 'total_items': 55, 
                        exam_list': [  
                            {'subj_name': 'Administratie en commercie - Versie rood', 'total_items': 20, 'total_envelops': 4, 'has_errata': True}, 
                            {'subj_name': 'Engelse taal', 'total_items': 35, 'total_envelops': 3, 'has_errata': False}]}, 
                    {'school_name': 'Ancilla Domini Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'lvl_name': 'Praktisch Kadergerichte Leerweg', 
                        'total_envelops': 7, 'total_items': 65, 
                        'exam_list': [
                            {'subj_name': 'Administratie en commercie - Versie rood', 'total_items': 20, 'total_envelops': 4, 'has_errata': True}, 
                            {'subj_name': 'Engelse taal', 'total_items': 45, 'total_envelops': 3, 'has_errata': False}]}, 
                    {'school_name': 'Ancilla Domini Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'lvl_name': 'Theoretisch Kadergerichte Leerweg', 
                        'total_envelops': 9, 'total_items': 70, 
                        'exam_list': [
                            {'subj_name': 'Administratie en commercie', 'total_items': 15, 'total_envelops': 3, 'has_errata': True}, 
                            {'subj_name': 'Engelse taal', 'total_items': 55, 'total_envelops': 6, 'has_errata': True}]}, 
                    {'school_name': 'Skol Avansá Integrá Humanista', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'lvl_name': 'Praktisch Basisgerichte Leerweg', 
                        'total_envelops': 5, 'total_items': 20, 
                        'exam_list': [
                            {'subj_name': 'Administratie en commercie - Vershon kórà', 'total_items': 10, 'total_envelops': 4, 'has_errata': True},
                            {'subj_name': 'Engelse taal', 'total_items': 10, 'total_envelops': 1, 'has_errata': False}]},
                    {'school_name': 'Skol Avansá Integrá Humanista', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'lvl_name': 'Praktisch Kadergerichte Leerweg', 
                        'total_envelops': 5, 'total_items': 20, 
                        'exam_list': [
                            {'subj_name': 'Administratie en commercie - Vershon kórà', 'total_items': 10, 'total_envelops': 4, 'has_errata': True}, 
                            {'subj_name': 'Engelse taal', 'total_items': 10, 'total_envelops': 1, 'has_errata': False}]}, 
                    {'school_name': 'Skol Avansá Integrá Humanista', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'lvl_name': 'Theoretisch Kadergerichte Leerweg', 
                        'total_envelops': 7, 'total_items': 35, 
                        'exam_list': [
                            {'subj_name': 'Administratie en commercie', 'total_items': 10, 'total_envelops': 3, 'has_errata': True}, 
                            {'subj_name': 'Engelse taal', 'total_items': 25, 'total_envelops': 4, 'has_errata': True}]}]
                """

    canvas.save()
    pdf = buffer.getvalue()
    # pdf_file = File(temp_file)

    # was: buffer.close()

    """
    # TODO as test try to save file in
    studsubjnote = stud_mod.Studentsubjectnote.objects.get_or_none(pk=47)
    content_type='application/pdf'
    file_name = 'test_try.pdf'
    if studsubjnote and pdf_file:
        instance = stud_mod.Noteattachment(
            studentsubjectnote=studsubjnote,
            contenttype=content_type,
            filename=file_name,
            file=pdf_file)
        instance.save()
        logger.debug('instance.saved: ' + str(instance))
    # gives error: 'bytes' object has no attribute '_committed'
    """

    return pdf


# - end of create_enveloplabel_pdf_with_school
###########################################

def create_enveloplabel_pdf_without_school(sel_examyear, schemeitem_dict, printlabel_dict, envelopsubject_pk_list):
    # PR2022-09-02 PR2022-10-10
    # this function creates all labels in all langauages of the selected exam
    # examperiod is taken from exam, not from settings
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('-----  create_enveloplabel_pdf_without_school ----- ')
        logger.debug('    envelopsubject_pk_list: ' + str(envelopsubject_pk_list))

    af.register_font_arial()
    af.register_font_calibri()

    buffer = io.BytesIO()
    canvas = Canvas(buffer)

    # paper size of labels is: 'Statement', Width: 21.59 cm Height: 13.97 cm or 8.5 inch x 5.5 inch or 612 x 396 points
    canvas.setPageSize((612, 396))  # some page size, given as a tuple in points pdf.setPageSize((width,height)

# +++ loop through envelopsubject_pk_list ( this is a list of subject / dep / level combinations)
    if envelopsubject_pk_list:
        for envelopsubject_pk in envelopsubject_pk_list:
            envelopsubject_instance = subj_mod.Envelopsubject.objects.get_or_none(pk=envelopsubject_pk)

            if logging_on:
                logger.debug('    envelopsubject_instance: ' + str(envelopsubject_instance))

            if envelopsubject_instance:
                id_key = '_'.join((
                    str(envelopsubject_instance.department.base_id),
                    str(envelopsubject_instance.level.base_id if envelopsubject_instance.level else 0),
                    str(envelopsubject_instance.subject.base_id)
                ))

                if logging_on:
                    logger.debug('    envelopsubject_instance: ' + str(envelopsubject_instance))
                    logger.debug('    id_key: ' + str(id_key))

        # +++ lookup labels with envelopsubject_key  and loop through labels of printlabel_list
                lbl_list = printlabel_dict.get(id_key)
                if lbl_list:
                    for lbl_dict in lbl_list:

        # get dep abbrev and lvl_abbrev, sub_name
                        dep_pk = lbl_dict.get('dep_id')
                        lvl_pk = lbl_dict.get('lvl_id') or 0
                        subj_pk = lbl_dict.get('subj_id')
                        examperiod = lbl_dict.get('examperiod')
                        firstdate = lbl_dict.get('firstdate')
                        lastdate = lbl_dict.get('lastdate')
                        starttime = lbl_dict.get('starttime')
                        endtime = lbl_dict.get('endtime')

                        is_variablenumber = lbl_dict.get('is_variablenumber') or False

                        numberinenvelop = lbl_dict.get('numberinenvelop') or 0

                        numberofenvelops = 1

                        #exam_count = lbl_dict.get('exam_count')

                        if logging_on:
                            logger.debug('    lbl_dict: ' + str(lbl_dict))
                        """
                        envelopsubject_key: 76
                        lbl_dict: {'env_subj_id': 76, 'dep_id': 10, 'lvl_id': 10, 'subj_id': 259, 
                        'firstdate': datetime.date(2022, 4, 18), 'lastdate': None, 'starttime': '07.30', 'endtime': '09.30', 
                        'has_errata': False, 'depbase_id': 1, 'lvlbase_id': 6, 'subjbase_id': 133, 
                        'bnd_name': 'Voorbeeld etikettenbundel', 'bndlbl_sequence': 1, 'lbl_name': 'Voorbeeld etiket', 
                        'is_errata': False, 'is_variablenumber': False, 'numberofenvelops': 1, 'numberinenvelop': 0, 
                        'content_nl_arr': ['Correctievoorschrift (2 ex)', 'Opgavenboek', 'Minitoets ond. A - B - C - D (rood & blauw)', 'Minitoets ond. A - B (rood & blauw)', 'Minitoets ond. A - C (rood & blauw)', 'Minitoets ond. A (rood & blauw)', 'Uitwerkbijlage'], 
                        'content_en_arr': ['Scoring Instruction (2 ex)', 'Assignment book', 'Mini-test part A - B - C - D (red & blue)', 'Mini-test part A - B (red & blue)', 'Mini-test part A - C (red & blue)', 'Mini-test part A (red & blue)', 'Work appendix'], 
                        'content_pa_arr': ['Reglamento di korekshon (2 ex)', 'Buki di tarea', 'Mini-prueba èks. A - B - C - D (kòrá & blou)', 'Mini-prueba èks. A - B (kòrá & blou)', 'Mini-prueba èks. A - C (kòrá & blou)', 'Mini-prueba èks. A (kòrá & blou)', 'Anekso di elaborashon'], 
                        'instruction_nl_arr': ['NIET EERDER OPENEN, DAN NA AFLOOP VAN DE EXAMENZITTING.', 'EERST DE NAAM VAN HET EXAMEN, DATUM EN TIJDSDUUR VOORLEZEN, DAARNA OPENEN!', None, None, None, None, None], 
                        'instruction_en_arr': ['DO NOT OPEN BEFORE THE EXAMINATION SESSION HAS ENDED.', 'FIRST READ THE EXAM NAME, DATE AND TIME, THEN OPEN!', None, None, None, None, None], 
                        'instruction_pa_arr': ['NO HABRI PROMÉ KU E SESHON DI ÈKSAMEN FINALISÁ.', 'LESA PROMÉ NA BOS HALTU ÈKSAMEN, FECHA I DURASHON PROMÉ KU HABRI!', None, None, None, None, None], 
                        'content_color_arr': ['red', 'black', 'black', 'black', 'black', 'black', 'black'], 
                        'instruction_color_arr': ['red', 'red', 'red', 'red', 'red', 'red', None], 
                        'sequence_arr': [1, 2, 61, 62, 63, 64, 65]}                      
                        """

                        bnd_lbl_name = ' - '.join((lbl_dict.get('bnd_name') or '-', lbl_dict.get('lbl_name') or '-'))

                        dep_abbrev, lvl_abbrev, subj_name_nl, subj_name_en, subj_name_pa = None, None, None, None, None
                        has_practexam, otherlang_arr = False, []

                        if dep_pk in schemeitem_dict:
                            dep_dict = schemeitem_dict.get(dep_pk)
                            dep_abbrev = dep_dict.get('dep_abbrev')
                            if lvl_pk in dep_dict:
                                lvl_dict = dep_dict.get(lvl_pk)
                                lvl_abbrev = lvl_dict.get('lvl_abbrev')

                                if subj_pk in lvl_dict:
                                    subj_dict = lvl_dict.get(subj_pk)
                                    subj_name_nl = subj_dict.get('subj_name_nl')
                                    subj_name_en = subj_dict.get('subj_name_en')
                                    subj_name_pa = subj_dict.get('subj_name_pa')
                                    has_practexam = subj_dict.get('has_practexam') or False

                        dep_lvl_abbrev = dep_abbrev if dep_abbrev else '---'
                        if lvl_abbrev:
                            dep_lvl_abbrev += ' ' + lvl_abbrev

                        dep_lvl_color = get_dep_lvl_color(dep_abbrev, lvl_abbrev)

        # - get all languages of this subject
                        lang_list = ['nl']

                        # get all other languages of this subject
                        schemeitems = subj_mod.Schemeitem.objects.filter(
                            scheme__department=envelopsubject_instance.department,
                            scheme__level=envelopsubject_instance.level,
                            subject=envelopsubject_instance.subject
                            #ete_exam=exam_instance.ete_exam
                        )
                        for schemeitem in schemeitems:
                            otherlang = schemeitem.otherlang
                            if otherlang:
                                otherlang_arr = otherlang.split(';')
                                for lang in otherlang_arr:
                                    if lang and lang not in lang_list:
                                        lang_list.append(lang)

    # +++ loop through languages of lang_list - when there is a school selected: there is only 1 lang - the lang of the school
                        for lang in lang_list:

                            if logging_on:
                                logger.debug('++lang: ' + str(lang))
                            # - translate version, get color
                            #translated_version, version_hex_color = translate_version(version, lang)

                            subj_name = get_subj_name(lang, subj_name_pa, subj_name_en, subj_name_nl)

                            content_key = '_'.join( ('content', 'pa' if lang == 'pa' else 'en' if lang == 'en' else 'nl', 'arr'))
                            instruction_key = '_'.join( ('instruction', 'pa' if lang == 'pa' else 'en' if lang == 'en' else 'nl', 'arr'))

                            content_arr = lbl_dict.get(content_key) or []
                            instruction_arr = lbl_dict.get(instruction_key) or []
                            content_color_arr = lbl_dict.get('content_color_arr') or []
                            instruction_color_arr = lbl_dict.get('instruction_color_arr') or []
                            content_font_arr = lbl_dict.get('content_font_arr') or []
                            instruction_font_arr = lbl_dict.get('instruction_font_arr') or []

                # - calculate number of labels that must be printed
                            school_name = None
                            tv_count = 10
                            total_envelops = calc_number_of_envelops(sel_examyear, is_variablenumber,
                                                                     numberinenvelop,
                                                                     numberofenvelops, tv_count)

        # +++ loop through number of labels for this exam and this school
                            # tv_count / exam_count is always an integer, but because we dont use decimal function the division is 10.0 instead of 10
                            if is_variablenumber:
                                total_items = tv_count
                            else:
                                total_items = numberinenvelop * numberofenvelops
                            if logging_on:
                                logger.debug('----total_items: ' + str(total_items))
                                logger.debug('    numberofenvelops: ' + str(numberofenvelops))
                                logger.debug('    numberinenvelop: ' + str(numberinenvelop))
                                logger.debug('    total_envelops: ' + str(total_envelops))

                            remaining_items = total_items

                            for page_index in range(0, total_envelops):  # range(start_value, end_value, step), end_value is not included!
                                numberofenvelops_str = ' '.join((
                                    str(page_index + 1),
                                    'di' if lang == 'pa' else 'of' if lang == 'en' else 'van',
                                    str(total_envelops)
                                ))

                                if logging_on:
                                    logger.debug('    ....remaining_items: ' + str(remaining_items))

                                items_in_envelop = 0
                                itemsinenvelop_str = ''

                                if remaining_items:
                                    if remaining_items >= numberinenvelop:
                                        items_in_envelop = numberinenvelop
                                        remaining_items -= numberinenvelop
                                    else:
                                        items_in_envelop = remaining_items
                                        remaining_items = 0

                                if total_envelops > 1:
                                    itemsinenvelop_str = ' '.join((
                                        str(items_in_envelop),
                                        'di' if lang == 'pa' else 'of' if lang == 'en' else 'van',
                                        str(total_items)
                                    ))
                                elif total_envelops == 1:
                                    if total_items:
                                        itemsinenvelop_str = str(total_items)

                                if logging_on:
                                    logger.debug('        total_items: ' + str(total_items) + ' ' + str(type(total_items)))
                                    logger.debug('        items_in_envelop: ' + str(items_in_envelop) + ' ' + str(type(items_in_envelop)))
                                    logger.debug('        itemsinenvelop_str: ' + str(itemsinenvelop_str) + ' ' + str(type(itemsinenvelop_str)))

                                draw_label(canvas, sel_examyear, examperiod, dep_lvl_abbrev, dep_lvl_color,
                                           subj_name, school_name,
                                           has_practexam, firstdate, lastdate, starttime, endtime, numberofenvelops_str,
                                           itemsinenvelop_str, lang, bnd_lbl_name,
                                           content_arr, instruction_arr,
                                           content_color_arr, instruction_color_arr,
                                           content_font_arr, instruction_font_arr
                                           )

                                canvas.showPage()

    canvas.save()
    pdf = buffer.getvalue()

    return pdf
# - end of create_enveloplabel_pdf_without_school
###########################################


def calc_acknowledgment_of_receipt_dictlist(sel_examyear, request):
    # PR2022-09-04 TODO finish ths code
    # this function creates an acknowledgment of receipt for each school / department / level
    # it always includes the errata labels

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' --- calc_acknowledgment_of_receipt_dictlist  -----')
        #logger.debug('schoolbase_dictlist: ' + str(schoolbase_dictlist))
        #logger.debug('count_per_school_dict: ' + str(count_per_school_dict))
        #logger.debug('print_without_schools: ' + str(print_without_schools))

# --- get department dictlist, ordered by sequence
    # fields are: depbase_id, depbase_code, dep_name, dep_level_req
    department_dictlist = subj_view.create_department_dictlist(sel_examyear)

# --- get lvlbase dictlist, ordered by sequence
    lvlbase_dictlist = subj_view.create_level_dictlist(sel_examyear)

# - get dict with schemeitem info per dep and lvl
    schemeitem_dict = get_schemeitem_info_per_dep_lvl(sel_examyear)

# - get envelop label info
    sel_layout = ''
    sel_examperiod = 1
    printlabel_dict = create_printlabel_dict(
        sel_examyear=sel_examyear,
        sel_examperiod=sel_examperiod,
        sel_layout=sel_layout
    )

    # functions creates ordered dictlist of all schoolbase_pk, schoolbase_code and school_name
    #  of this exam year of all countries (only SXM when requsr=sxm), ordered by code
    schoolbase_dictlist = subj_view.create_schoolbase_dictlist(sel_examyear, request)

    # was: envelop_count_per_school_dict = subj_calc.create_envelop_count_per_school_dict(
    #    sel_examyear_instance=sel_examyear,
    #    sel_examperiod=sel_examperiod,
    #    request=request,
    #    schoolbase_pk_list=None,
    #    subjbase_pk_list=None
    #)

    count_dictNIU, envelop_count_per_school_dict = subj_calc.create_studsubj_count_dict(
        sel_examyear_instance=sel_examyear,
        sel_examperiod=sel_examperiod,
        request=request,
        schoolbase_pk_list=None,
        subjbase_pk_list=None
    )

    acknowledgment_of_receipt_dictlist = []

# +++ loop through list of all schools

    for schoolbase_dict in schoolbase_dictlist:
        sbase_id = schoolbase_dict.get('sbase_id')
        school_name = schoolbase_dict.get('sch_name') or ''

        envelop_schoolbase_dict = envelop_count_per_school_dict.get(sbase_id)

# - check if school exists in print_dict
        if envelop_schoolbase_dict:

# +++ loop through list of all departments
            for department_dict in department_dictlist:
                depbase_id = department_dict.get('depbase_id')
                dep_name = department_dict.get('dep_name') or ''

# - check if department exists in envelop_schoolbase_dict
                # print_rows contains a list of subj/dep/level/examperiod/ete_exam combination (without link to exams)
                # with the number of exams-items , including extra exams. Blue/red version are taken in account
                # and count of different exams for the subject (blue/ red)
                depbase_count_dict = envelop_schoolbase_dict.get(depbase_id)

                if depbase_count_dict:

# +++ loop through list of all levels
                    for lvlbase_dict in lvlbase_dictlist:
                        lvlbase_id = lvlbase_dict.get('lvlbase_id')
                        lvl_name = lvlbase_dict.get('lvl_name') or ''

# - check if level exists in envelop_schoolbase_dict
                        # print_rows contains a list of subj/dep/level/examperiod/ete_exam combination (without link to exams)
                        # with the number of exams-items , including extra exams. Blue/red version are taken in account
                        # and count of different examns for the subject (blue/ red)
                        lvlbase_count_list = depbase_count_dict.get(lvlbase_id)

# +++ loop through list of subject of this dep / level of this school
                        if lvlbase_count_list:

# - create dict with info for receipt per school/dep/lvl
                            receipt_school_dep_lvl_dict = {
                                'school_name': school_name,
                                'dep_name': dep_name,
                                'lvl_name': lvl_name,
                                'total_envelops': 0,
                                'total_items': 0,
                                'exam_list': []
                            }
                            receipt_exam_list = receipt_school_dep_lvl_dict.get('exam_list')

                            receipt_school_dep_lvl_total_envelops = 0
                            receipt_school_dep_lvl_total_items = 0

                            for lvlbase_count_row in lvlbase_count_list:
                                if logging_on:
                                    logger.debug('    lvlbase_count_row: ' + str(lvlbase_count_row))

                                receipt_count_dict = {'subj_name': '', 'total_items': 0, 'total_envelops': 0, 'has_errata': False}

                                id_key = lvlbase_count_row.get('id_key')
                                school_name = lvlbase_count_row.get('school_name') or ''
                                school_lang = lvlbase_count_row.get('lang') or 'nl'
                                subj_count = lvlbase_count_row.get('subj_count') or 0
                                extra_count = lvlbase_count_row.get('extra_count') or 0
                                if sel_examperiod == c.EXAMPERIOD_FIRST:
                                    tv_count = subj_count + extra_count
                                elif sel_examperiod == c.EXAMPERIOD_SECOND:
                                    tv_count = lvlbase_count_row.get('tv2_count') or 0
                                else:
                                    tv_count = 0

        # +++ lookup labels with id_key and loop through labels of printlabel_list
                                lbl_list = printlabel_dict.get(id_key)
                                if lbl_list:
                                    for lbl_dict in lbl_list:
                                        # get dep abbrev and lvl_abbrev, sub_name
                                        dep_pk = lbl_dict.get('dep_id')
                                        lvl_pk = lbl_dict.get('lvl_id') or 0
                                        subj_pk = lbl_dict.get('subj_id')
                                        has_errata = lbl_dict.get('has_errata') or False

                                    # is_errata labels are filtered out in create_printlabel_rows
                                        is_variablenumber = lbl_dict.get('is_variablenumber') or False
                                        numberofenvelops = lbl_dict.get('numberofenvelops') or 0
                                        numberinenvelop = lbl_dict.get('numberinenvelop') or 0
                                        # was: exam_count = lbl_dict.get('exam_count')

                                        has_practexam, otherlang_arr = False, []

                                        if dep_pk in schemeitem_dict:
                                            dep_dict = schemeitem_dict.get(dep_pk)
                                            dep_abbrev = dep_dict.get('dep_abbrev')
                                            if lvl_pk in dep_dict:
                                                lvl_dict = dep_dict.get(lvl_pk)
                                                if subj_pk in lvl_dict:
                                                    subj_dict = lvl_dict.get(subj_pk)
                                                    if subj_dict:
                                                        otherlang_arr = subj_dict.get('otherlang')

            # - get language of this school
                                        # when there is a school selected: school has only 1 lang per subject. Use that one
                                        # when no school selected: print all languages
                                        lang_list = []
                                        if school_lang:
                                            lang_list.append(school_lang)
                                        else:
                                            # otherwise: loop throudh all languages of this subject
                                            lang_list.append('nl')
                                            if otherlang_arr:
                                                for lang in otherlang_arr:
                                                    if lang not in lang_list:
                                                        lang_list.append(lang)

        # +++ loop through languages of lang_list - when there is a school selected: there is only 1 lang - the lang of the school
                                        for lang in lang_list:

                # - calculate number of labels that must be printed
                                            total_envelops = calc_number_of_envelops(sel_examyear, is_variablenumber, numberinenvelop,
                                                                    numberofenvelops, tv_count)

        # +++ loop through number of labels for this exam and this school
                                            # was: tv_count / exam_count is always an integer, but because we dont use decimal function the division is 10.0 instead of 10
                                            if is_variablenumber:
                                                # was: total_items = int(tv_count / exam_count) if exam_count > 1 else tv_count
                                                total_items = tv_count
                                                # add to total_items, only when is_variablenumber
                                                receipt_count_dict['total_items'] += total_items
                                                receipt_school_dep_lvl_total_items += total_items

                                            else:
                                                total_items = numberinenvelop * numberofenvelops

                                            if has_errata:
                                                receipt_count_dict['has_errata'] = True

                                            remaining_items = total_items

                                            for page_index in range(0, total_envelops):  # range(start_value, end_value, step), end_value is not included!
                                                if remaining_items:
                                                    if remaining_items >= numberinenvelop:
                                                        remaining_items -= numberinenvelop
                                                    else:
                                                        remaining_items = 0

                                                # - skip draw_label

                                                receipt_count_dict['total_envelops'] += 1
                                                receipt_school_dep_lvl_total_envelops += 1

                                    receipt_exam_list.append(receipt_count_dict)

        # add receipt_info_dict to list
                            if receipt_school_dep_lvl_total_envelops:
                                receipt_school_dep_lvl_dict['total_envelops'] = receipt_school_dep_lvl_total_envelops
                                receipt_school_dep_lvl_dict['total_items'] = receipt_school_dep_lvl_total_items
                                acknowledgment_of_receipt_dictlist.append(receipt_school_dep_lvl_dict)
    if logging_on:
        logger.debug('acknowledgment_of_receipt_dictlist: ' + str(acknowledgment_of_receipt_dictlist))

    return acknowledgment_of_receipt_dictlist
# - end of create_acknowledgment_of_receipt_dictlist
###########################################


def calc_number_of_envelops(sel_examyear, is_variablenumber, numberinenvelop, numberofenvelops, tv_count):
    # - calculate number of labels that must be printed PR2022-08-26
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' --- calc_number_of_envelops  -----')
        logger.debug('    sel_examyear: ' + str(sel_examyear))
        logger.debug('    is_variablenumber: ' + str(is_variablenumber))
        logger.debug('    numberinenvelop: ' + str(numberinenvelop))
        logger.debug('    numberofenvelops: ' + str(numberofenvelops))
        logger.debug('    tv_count: ' + str(tv_count))

    total_envelops_integer = 0
    if is_variablenumber:
        if logging_on:
            logger.debug('    --- is_variablenumber')
        # NOT IN USE
        # when there are multiple exams (blue, red), the items must be divided over the exam
        # when calculating extra exams it is alereay taken in account of multiple exams
        # exam_count is number of exams of this subject / dep / level / exammperiod
        # if not exam_count:
        #    exam_count = 1

        # divide items over the exams, round items up to 'chunk'. Is already done in calc exams, but let it stay
        # if exam_count > 1:
            #     order_round_to = sel_examyear.order_round_to or 5

            #     # divide total exams over blue and red and roundup to order_round_to

            #     # 45 items / 2 exams = 22,5  items per exam
            #     items_not_rounded = tv_count / exam_count
            #     # 22,5 items / 5 per 'chunk' = 4,5 'chunks' of 5 items
            #     items_divided_by_roundto = items_not_rounded / order_round_to
            #     # integer of 4,5 'chunks' = 4 chunks , roundup to 5 chunks
            #     items_divided_integer = int(items_divided_by_roundto)
            #     items_divided_frac = items_divided_by_roundto - items_divided_integer
            #     if items_divided_frac:
            #         items_divided_integer += 1
            #     # total items = 5 chunks *  5 items per 'chunk' = 25 items
        #     total_items = items_divided_integer * order_round_to
        # else:
        #     total_items = tv_count

        total_items = tv_count
        # 15 items per envelop > 25 items / 15 numberinenvelop = 1,667 envelops
        total_envelops_not_rounded = total_items / numberinenvelop if numberinenvelop else 0
        # roundup to 2 envelops
        total_envelops_integer = int(total_envelops_not_rounded)
        if logging_on:
            logger.debug('    total_items: ' + str(total_items))
            logger.debug('    total_envelops_not_rounded: ' + str(total_envelops_not_rounded))
            logger.debug('    total_envelops_integer: ' + str(total_envelops_integer))

        total_envelops_frac = (total_envelops_not_rounded - total_envelops_integer)
        if total_envelops_frac:
            total_envelops_integer += 1

        if logging_on:
            logger.debug('    total_envelops_frac: ' + str(total_envelops_frac))
            logger.debug('    total_envelops_integer: ' + str(total_envelops_integer))
    else:
        if not numberofenvelops:
            numberofenvelops = 1
        total_envelops_integer = numberofenvelops
        if logging_on:
            logger.debug('    ---not is_variablenumber')
            logger.debug('    numberofenvelops: ' + str(numberofenvelops))

    if logging_on:
        logger.debug('    total_envelops_integer: ' + str(total_envelops_integer))
        logger.debug(' --- end of calc_number_of_envelops  -----')
    return total_envelops_integer

def translate_versionNIU(version, lang): # PR2022-08-26
    translated_version = version
    hex_color = c.LABEL_COLOR.get('black')
    if version and lang:
        version_lc = version.lower()
        if lang == 'en':
            if 'blauw' in version_lc:
                translated_version = 'Version blue'
            elif 'rood' in version_lc:
                translated_version = 'Version red'
            elif 'groen' in version_lc:
                translated_version = 'Version green'
        elif lang == 'pa':
            if 'blauw' in version_lc:
                translated_version = 'Vershon blou'
            elif 'rood' in version_lc:
                translated_version = 'Vershon kórà'
            elif 'groen' in version_lc:
                translated_version = 'Vershon bèrdè'
        else:
            if 'blauw' in version_lc:
                translated_version = 'Versie blauw'
            elif 'rood' in version_lc:
                translated_version = 'Versie rood'
            elif 'groen' in version_lc:
                translated_version = 'Versie green'

        if 'blauw' in version_lc:
            hex_color = c.LABEL_COLOR.get('blue')
        elif 'rood' in version_lc:
            hex_color = c.LABEL_COLOR.get('red')
        elif 'groen' in version_lc:
            hex_color = c.LABEL_COLOR.get('green')
        elif 'geel' in version_lc:
            hex_color = c.LABEL_COLOR.get('yellow')
        elif 'oranje' in version_lc:
            hex_color = c.LABEL_COLOR.get('orange')
        elif 'paars' in version_lc:
            hex_color = c.LABEL_COLOR.get('purple')

    return translated_version, hex_color
# - end of translate_version

def get_ex3_grade_rows (self, examyear, school, department, upload_dict, examperiod):

    # note: don't forget to filter deleted = false!! PR2021-03-15
    # grades that are not published are only visible when 'same_school'
    # note_icon is downloaded in separate call

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_ex3_grade_rows -----')
        logger.debug('upload_dict: ' + str(upload_dict))

    # upload_dict: {'subject_list': [2206, 2165, 2166], 'sel_layout': 'level', 'level_list': [86, 85]}

    # values of sel_layout are:"none", "level", "class", "cluster"
    # "none" or None: all students of subject on one form
    # "level:" seperate form for each leeerweg
    #  Note: when lvlbase_pk_list has values: filter on lvlbase_pk_list in all lay-outs
    #  filter on lvlbase_pk, not level_pk, to make filter also work in other examyears

    lvlbase_pk_list = upload_dict.get('lvlbase_pk_list', [])
    subject_list = upload_dict.get('subject_list', [])
    sel_layout = upload_dict.get('sel_layout')

    sql_keys = {'ey_id': examyear.pk, 'sch_id': school.pk, 'dep_id': department.pk,
                'lvlbase_pk_arr': lvlbase_pk_list, 'subj_arr': subject_list, 'experiod': examperiod}
    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))

    ex3_dict = {}

    level_filter = "AND lvl.base_id IN ( SELECT UNNEST( %(lvlbase_pk_arr)s::INT[]))" if lvlbase_pk_list else ""
    subject_filter = "AND subj.id IN ( SELECT UNNEST( %(subj_arr)s::INT[]))" if subject_list else ""

    logger.debug('subject_filter: ' + str(subject_filter))
    sql_list = ["SELECT subj.id AS subj_id, subjbase.code AS subj_code, subj.name_nl AS subj_name,",
                "stud.lastname, stud.firstname, stud.prefix, stud.examnumber, ",
                "stud.classname, cl.name AS cluster_name,",
                "stud.level_id, lvl.name AS lvl_name",

                "FROM students_grade AS grd",
                "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
                "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = stud.level_id)",

                "INNER JOIN schools_school AS school ON (school.id = stud.school_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = school.examyear_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",

                "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
                "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

                "LEFT JOIN subjects_cluster AS cl ON (cl.id = studsubj.cluster_id)",

                "WHERE ey.id = %(ey_id)s::INT AND school.id = %(sch_id)s::INT AND dep.id = %(dep_id)s::INT",
                level_filter,
                subject_filter,
                "AND NOT grd.tobedeleted AND NOT grd.deleted AND NOT studsubj.tobedeleted",
                "AND grd.examperiod = %(experiod)s::INT",
                "ORDER BY LOWER(subj.name_nl), LOWER(stud.lastname), LOWER(stud.firstname)"
                ]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        grade_rows = af.dictfetchall(cursor)

    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))
        logger.debug('sql: ' + str(sql))

# - add full name to rows, and array of id's of auth
    if grade_rows:
        for row in grade_rows:
            subj_pk = row.get('subj_id')
            subj_name = row.get('subj_name', '---')
            classname = row.get('classname', '---')
            cluster_name = row.get('cluster_name', '---')
            level_id = row.get('level_id')
            lvl_name = row.get('lvl_name', '---')

            if sel_layout == "level":
                key = (subj_pk, level_id)
            elif sel_layout == "class":
                key = (subj_pk, classname)
            elif sel_layout == "cluster":
                key = (subj_pk, cluster_name)
            else:
                sel_layout = None
                key = subj_pk
            if key not in ex3_dict:
                ex3_dict[key] = {'subject': subj_name}
                if sel_layout == "level":
                    ex3_dict[key][sel_layout] = lvl_name
                elif sel_layout == "class":
                    ex3_dict[key][sel_layout] = classname
                elif sel_layout == "cluster":
                    ex3_dict[key][sel_layout] = cluster_name
                ex3_dict[key]['students'] = []

            student_list = ex3_dict[key].get('students', [])
            #student_list.append((examnumber, full_name))

    if logging_on:
        logger.debug('ex3_dict: ' + str(ex3_dict))

    return ex3_dict

# - end of DownloadEx3View


def draw_label(canvas, examyear, examperiod, dep_lvl_abbrev, dep_lvl_color, subj_name, school_name, has_practexam,
               firstdate, lastdate, starttime, endtime, numberofenvelops_str, itemsinenvelop_str, lang, bnd_lbl_name,
               content_arr, instruction_arr, content_color_arr, instruction_color_arr,
               content_font_arr, instruction_font_arr):
    # PR2022-09-29 PR2022-10-08 PR2022-10-20
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_label -----')

    # paper size of labels is: 'Statement', Width: 21.59 cm Height: 13.97 cm or 8.5 inch x 5.5 inch or 612 x 396 points
    margin_bottom = 0.2 * inch

    pos_x = 0.625 * inch
    pos_x2 = 2.625 * inch  #   pos_x2 = 2.375 * inch
    pos_x3 = 2.875 * inch  #  pos_x3 = 2.625 * inch
    pos_x4 = 7.875 * inch

    pos_y = 4.95 * inch  # PR2022-10-09 was: pos_y = 4.75 * inch
    line_height = 0.25 * inch

    label_txt = c.LABEL_TEXT.get(lang)

# - draw ETE logo
    # canvas.drawImage(image, x, y, width, height, mask=None)
    file_name = s.STATICFILES_IMG_DIR + "ETElogo2022-08-15.png"  # size 1750 - 1000
    # PR2022-10-06 was: canvas.drawInlineImage(file_name, pos_x, 4.35 * inch, 1.75 * inch, 1 * inch)
    canvas.drawInlineImage(file_name, pos_x, pos_y - .45 * inch, 1.4 * inch,  0.8 * inch)

# - draw CSPE EXAMEN 2023

    # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
    canvas.setFont('Arial_Black', 20, leading=None)
    caption = ' '.join((label_txt.get('exam'), str(examyear)))
    caption_width = stringWidth(caption, 'Arial_Black', 20)

    canvas.setFillColor(colors.HexColor("#000000"))
    canvas.drawRightString(pos_x4, pos_y, caption)

    canvas.setFillColor(colors.HexColor("#ff0000"))
    cse_cspe = 'CSPE' if has_practexam else 'CSE'
    canvas.drawRightString(pos_x4 - caption_width - 0.125 * inch, pos_y, cse_cspe)

    pos_y -= line_height * 1.5

# - draw Vsbo PBL
    hex_color = c.LABEL_COLOR.get(dep_lvl_color)
    canvas.setFillColor(colors.HexColor(hex_color))
    canvas.drawRightString(pos_x4, pos_y, dep_lvl_abbrev)

    # PR2022-10-09 was: pos_y = 3.75 * inch
    pos_y -= .575 * inch

# - draw grey bar with examperiod and subject
    bottom = pos_y - 0.125 * inch
    height = 0.5 * inch
    canvas.setFillColor(colors.HexColor("#bfbfbf"))  # grey background in label  RGB 181, 181, 191
    canvas.rect(0.5 * inch, bottom, 7.5 * inch, height, stroke=0, fill=1)  # canvas.rect(left, bottom, page_width, height)

    caption = ' '.join((label_txt.get('ep'), str(examperiod)))
    canvas.setFont('Calibri_Bold', 20, leading=None)
    canvas.setFillColor(colors.HexColor("#000000"))
    canvas.drawString(pos_x, pos_y, caption)

    canvas.drawRightString(pos_x4, pos_y, subj_name)

# - draw examdate or examperiod
    caption, examdate_str = format_examdate_from_dte(firstdate, lastdate, label_txt, lang, has_practexam)

    pos_y -= 0.5 * inch
    canvas.setFont('Arial', 14, leading=None)
    canvas.drawString(pos_x, pos_y, caption)
    canvas.drawString(pos_x2, pos_y, ':')
    canvas.drawString(pos_x3, pos_y, examdate_str)

# - draw starttime, endtime
    if starttime or endtime:
        caption, examtime_formatted = format_examtime(starttime, endtime, label_txt, has_practexam)
        if logging_on:
            logger.debug('    label_txt: ' + str(label_txt))
            logger.debug('    examtime_formatted: ' + str(examtime_formatted))

        pos_y -= line_height
        canvas.drawString(pos_x, pos_y, caption)
        canvas.drawString(pos_x2, pos_y, ':')
        canvas.drawString(pos_x3, pos_y, examtime_formatted)

# - draw school name
    pos_y -= line_height

    caption = label_txt.get('school') or '---'
    canvas.drawString(pos_x, pos_y, caption)
    canvas.drawString(pos_x2, pos_y, ':')
    if school_name:
        canvas.setFont('Arial_Black', 14)
        canvas.drawString(pos_x3, pos_y, school_name)
    canvas.setFont('Arial', 14, leading=None)

# - skip when itemsinenvelop_str is blank
    if itemsinenvelop_str:
        pos_y -= line_height
        caption = label_txt.get('numex') or '---'
        value = itemsinenvelop_str
        canvas.drawString(pos_x, pos_y, caption)
        canvas.drawString(pos_x2, pos_y, ':')
        canvas.drawString(pos_x3, pos_y, value)

    pos_y -= line_height
    caption = label_txt.get('numenv') or '---'
    value = str(numberofenvelops_str) if numberofenvelops_str else ''
    canvas.drawString(pos_x, pos_y, caption)
    canvas.drawString(pos_x2, pos_y, ':')
    canvas.drawString(pos_x3, pos_y, value)

# - draw content
    # PR2022-10-17 email Rushaina:
    #   - Dat er tussen envelop en inhoud een extra ruimte kan komen.
    #   - Op het etiket bij inhoud het woord inhoud kan Bold worden? Dit telt voor CSPE en CSE.
    #   - Bij (inhoud) Examen onderdeel A (60 min) moet ook bold worden (alleen deze row),

    # was: pos_y -= line_height * 1.5
    pos_y -= line_height * 2
    caption = label_txt.get('content') or '---'

    # Arial_Black is heavier than Arial_Bold
    canvas.setFont('Arial_Bold', 14)
    canvas.drawString(pos_x, pos_y, caption)

    canvas.setFont('Arial', 14, leading=None)
    canvas.drawString(pos_x2, pos_y, ':')

    if content_arr:
        row_count = 0
        for i, content in enumerate(content_arr):
            if content:
                content_color = content_color_arr[i]
                hex_color = c.LABEL_COLOR.get(content_color)
                if not hex_color:
                    hex_color = '#000000'  # 'black': rgb 0 0 0  #000000
                canvas.setFillColor(colors.HexColor(hex_color))

                # PR2022-10-20 content_font_arr added
                font_style = content_font_arr[i]
                set_font_style(canvas, 'Arial', font_style, 14)

                canvas.drawString(pos_x3, pos_y - line_height * row_count, content or '')
                row_count += 1

    row_count = 0

# - PR2022-09-29 request Rushaina Manuel drukteam: allow long lines.
    # - split line when it has a '~' (tilde '~' means hard return)

    instruction_arr_with_split_lines = []
    instruction_color_arr_with_split_lines = []
    instruction_font_arr_with_split_lines = []
    if instruction_arr:
        for i, instruction in enumerate(instruction_arr):
            if instruction:
                if logging_on:
                    logger.debug('i: ' + str(i) + ' instruction: ' + str(instruction))
                if '~' in instruction:
                    arr = instruction.split('~')
                    for item in arr:
                        instruction_arr_with_split_lines.append(item)
                        instruction_color_arr_with_split_lines.append(instruction_color_arr[i])
                        instruction_font_arr_with_split_lines.append(instruction_font_arr[i])
                        row_count += 1

                        if logging_on:
                            logger.debug('item: ' + str(item))

                else:
                    instruction_arr_with_split_lines.append(instruction)
                    instruction_color_arr_with_split_lines.append(instruction_color_arr[i])
                    instruction_font_arr_with_split_lines.append(instruction_font_arr[i])
                    row_count += 1

# calculate heigth of bar
    canvas.setFillColor(colors.HexColor("#bfbfbf"))  # grey background in label  RGB 181, 181, 191
    # PR2022-10-08 was: bar_bottom = 0.375 * inch
    bar_bottom = margin_bottom
    bar_height = 0.375 * inch + (row_count - 1 ) * line_height * .75 if row_count > 1 else 0.375 * inch
    bar_top = bar_bottom + bar_height
    canvas.rect(0.5 * inch, bar_bottom, 7.5 * inch, bar_height, stroke=0, fill=1)  # canvas.rect(left, bottom, page_width, height)
    canvas.setFillColor(colors.HexColor("#000000"))

    if instruction_arr_with_split_lines:
        row_count = 0
        pos_y = bar_top - line_height
        canvas.setFont('Calibri', 12, leading=None)
        for i, instruction in enumerate(instruction_arr_with_split_lines):
            if instruction:
                instruction_color = instruction_color_arr_with_split_lines[i]
                hex_color = c.LABEL_COLOR.get(instruction_color)
                if not hex_color:
                    hex_color = '#000000'  # 'black': rgb 0 0 0  #000000
                canvas.setFillColor(colors.HexColor(hex_color))

                # PR2022-10-20 content_font_arr added
                font_style = instruction_font_arr_with_split_lines[i]
                set_font_style(canvas, 'Calibri', font_style, 12)

                canvas.drawCentredString(4.25 * inch, pos_y - line_height * .75 * row_count, instruction or '')
                row_count += 1

    #pos_y = 0.6125 * inch
    #canvas.setFillColor(colors.HexColor("#ff0000"))
    #canvas.setFont('Calibri', 12, leading=None)
    #anvas.drawCentredString(4.25 * inch, pos_y, 'E MODELO DI KOREKSHON DI E ÈKSAMEN AKÍ TA KONFIDENSIAL')

    #pos_y -= line_height * .75
    #canvas.drawCentredString(4.25 * inch, pos_y, 'I E ÈKSAMEN TA KEDA KORIGÍ DOR DI E KOMISHON DI ÈKSAMEN DI ESTADO')

# dont draw bnd_lbl_name when there is a school_name
    if not school_name:
        canvas.setFillColor(colors.HexColor("#000000"))
        canvas.setFont('Calibri', 8)
        canvas.drawRightString(pos_x4, bar_bottom - 0.125 * inch, bnd_lbl_name)
        canvas.setFillColor(colors.HexColor("#000000"))

    canvas.setFont('Calibri', 12, leading=None)

# - end of draw_label


def set_font_style(canvas, font, style, font_size):
    # PR2022-10-21
    font_name = font
    if style:
        if 'Bold' in style:
            if 'Italic' in style:
                font_name = font + '_Bold_Italic'
            else:
                font_name = font + '_Bold'
        else:
            if 'Italic' in style:
                font_name = font + '_Italic'

    canvas.setFont(font_name, font_size)


def draw_red_cross(canvas, x, y):
    # draw red cross, for outlining while designing
    canvas.setStrokeColorRGB(1, 0, 0)
    canvas.line(x, y + 5 * mm, x, y - 5 * mm)
    canvas.line(x - 5 * mm, y , x + 5 * mm, y )

def draw_green_cross(canvas, x, y):
    # draw red cross, for outlining while designing
    canvas.setStrokeColorRGB(0, 1, 0)
    canvas.line(x, y + 5 * mm, x, y - 5 * mm)
    canvas.line(x - 5 * mm, y , x + 5 * mm, y )

def create_ete_exam_rows(req_usr, sel_examyear, sel_depbase, append_dict, setting_dict=None, exam_pk_list=None):
    # --- create rows of all exams of this examyear  PR2021-04-05  PR2022-01-23 PR2022-02-23 PR2022-05-13  PR2022-06-02
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_ete_exam_rows ============= ')
        logger.debug('sel_examyear: ' + str(sel_examyear))
        logger.debug('sel_depbase: ' + str(sel_depbase))

    # PR2022-05-13 debug: Raymond Romney MPC: cannot open exam.
    # cause: exams were filtered by examyear.pk, SXM has different examyear.pk from CUR
    # solved by: filter by examyear.code instead of examyear.pk

    # PR2022-06-02 tel Lavern SMAC: has sp DUO
    # try solving by filtering on examyear.pk when ETE/DOE logs in

    # - when user is school: only show published exams

    # PR2022-06-23
    # --- creates rows with exams that:
    # - are exam.ete_exam
    # - this department
    # - this examyear_code i.e Sxm also sees Cur ETE exams
    # - if not role = admin:
    #       - only shows published ETE exams

    sel_depbase_pk = sel_depbase.pk if sel_depbase else 0
    sel_ey_code = sel_examyear.code if sel_examyear else 0

    sql_keys = {'ey_code': sel_ey_code, 'depbase_id': sel_depbase_pk}

    logger.debug('sql_keys: ' + str(sql_keys))
    sql_list = [
        "SELECT ex.id, ex.subject_id AS subj_id, subj.base_id AS subjbase_id, subj.examyear_id AS subj_examyear_id,",
        "CONCAT('exam_', ex.id::TEXT) AS mapid,",
        "CONCAT(subj.name_nl,",
            "CASE WHEN lvl.abbrev IS NULL THEN NULL ELSE CONCAT(' - ', lvl.abbrev) END,",
            "CASE WHEN ex.version IS NULL OR ex.version = '' THEN NULL ELSE CONCAT(' - ', ex.version) END ) AS exam_name,",

        "ex.ete_exam, ex.examperiod, ex.department_id, depbase.id AS depbase_id, depbase.code AS depbase_code,",
        "ex.level_id, lvl.base_id AS lvlbase_id, lvl.abbrev AS lvl_abbrev,",
        "ex.version, ex.has_partex, ex.partex, ex.assignment, ex.keys, ex.amount, ex.blanks,",
        "ex.nex_id, ex.scalelength, ex.cesuur, ex.nterm, ex.secret_exam,",

        "ex.status, ex.auth1by_id, ex.auth2by_id, ex.published_id, ex.locked, ex.modifiedat,",
        "sb.code AS subjbase_code, subj.name_nl AS subj_name,",
        "bundle.id AS bundle_id, bundle.name AS bundle_name,"
        "ey.id AS ey_id, ey.code AS ey_code, ey.locked AS ey_locked,",
        "au.last_name AS modby_username,",

        "auth1.last_name AS auth1_usr, auth2.last_name AS auth2_usr, publ.modifiedat AS publ_modat",

        "FROM subjects_exam AS ex",
        "INNER JOIN subjects_subject AS subj ON (subj.id = ex.subject_id)",
        "INNER JOIN subjects_subjectbase AS sb ON (sb.id = subj.base_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = subj.examyear_id)",

        "INNER JOIN schools_department AS dep ON (dep.id = ex.department_id)",
        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = ex.level_id)",
        "LEFT JOIN subjects_envelopbundle AS bundle ON (bundle.id = ex.envelopbundle_id)",

        "LEFT JOIN accounts_user AS auth1 ON (auth1.id = ex.auth1by_id)",
        "LEFT JOIN accounts_user AS auth2 ON (auth2.id = ex.auth2by_id)",
        "LEFT JOIN schools_published AS publ ON (publ.id = ex.published_id)",

        "LEFT JOIN accounts_user AS au ON (au.id = ex.modifiedby_id)",
        "WHERE ex.ete_exam",
        "AND ey.code = %(ey_code)s::INT",
    ]
    if sel_depbase_pk:
        # PR2022-08-11 show ete_exams of all deps in page orderlist / envelop
        "AND depbase.id = %(depbase_id)s::INT"

# - only show exams that are published when user is not role_admin
    if not req_usr.is_role_admin:
        sql_list.append("AND ex.published_id IS NOT NULL")

# skip other filters when exam_pk_list has value
    if exam_pk_list:
        sql_keys['pk_arr'] = exam_pk_list
        sql_list.append("AND ex.id IN (SELECT UNNEST( %(pk_arr)s::INT[]))")
    else:
        if setting_dict:
            sel_examperiod = setting_dict.get(c.KEY_SEL_EXAMPERIOD)
            if sel_examperiod in (1, 2, 3):
                sql_keys['ep'] = sel_examperiod
                sql_list.append("AND (ex.examperiod = %(ep)s::INT)")

            sel_lvlbase_pk = setting_dict.get(c.KEY_SEL_LVLBASE_PK)
            if sel_lvlbase_pk:
                sql_keys['lvlbase_pk'] = sel_lvlbase_pk
                sql_list.append("AND lvl.base_id = %(lvlbase_pk)s::INT")

    sql_list.append("ORDER BY ex.id")

    sql = ' '.join(sql_list)
    if logging_on:
        logger.debug('sql_keys: ' + str(sql_keys))

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        ete_exam_rows = af.dictfetchall(cursor)

# - add messages to first exam_row, only when exam_pk exists
        if exam_pk_list and len(exam_pk_list) == 1 and ete_exam_rows:
            # when exam_pk has value there is only 1 row
            row = ete_exam_rows[0]
            if row:
                for key, value in append_dict.items():
                    row[key] = value

    if logging_on:
        logger.debug('ete_exam_rows: ' + str(ete_exam_rows))

    return ete_exam_rows
# --- end of create_ete_exam_rows

def format_examdate_from_dte(firstdate, lastdate, label_txt, lang, has_practexam):  # PR2022-08-13 PR2022-10-13

    def format_perioddate(examdate, show_year):
        date_formatted = ''
        if examdate:
            year_str = str(examdate.year)
            day_str = str(examdate.day)
            month_str = c.LABEL_MONTHS[lang][examdate.month]

            weekday_int = int(examdate.strftime("%w"))
            if not weekday_int:
                weekday_int = 7
            weekday_str = c.LABEL_WEEKDAYS[lang][weekday_int]

            # Djaluna, 17 di sèptèmber,
            if show_year:
                if lang == 'pa':
                    date_formatted = ' '.join([weekday_str, day_str, label_txt['of'], month_str, year_str])
                elif lang == 'en':
                    date_formatted = ''.join([weekday_str, ', ', month_str, ' ', day_str, ', ', year_str])
                else:
                    date_formatted = ' '.join([weekday_str, day_str, month_str, year_str])
            else:
                if lang == 'pa':
                    date_formatted = ' '.join([weekday_str, day_str, label_txt['of'], month_str])
                elif lang == 'en':
                    date_formatted = ''.join([weekday_str, ', ', month_str, ' ', day_str])
                else:
                    date_formatted = ' '.join([weekday_str, day_str, month_str])
        return date_formatted

    def format_examdate(examdate):
        date_formatted = ''
        if examdate:
            year_str = str(examdate.year)
            day_str = str(examdate.day)
            month_str = c.LABEL_MONTHS[lang][examdate.month]

            weekday_int = int(examdate.strftime("%w"))
            if not weekday_int:
                weekday_int = 7
            weekday_str = c.LABEL_WEEKDAYS[lang][weekday_int]

            # Djaluna, 17 di sèptèmber,
            if lang == 'pa':
                date_formatted = ' '.join([weekday_str, day_str, label_txt['of'], month_str, year_str])
            elif lang == 'en':
                date_formatted = ''.join([weekday_str, ', ', month_str, ' ', day_str, ', ', year_str])
            else:
                date_formatted = ' '.join([weekday_str, day_str, month_str, year_str])
        return date_formatted

    examdate_formatted = ''
    if has_practexam:
        caption = label_txt.get('period') or '---'
        examdate_formatted = ' - '.join([format_perioddate(firstdate, False), format_perioddate(lastdate, True)])

    else:
        caption = label_txt.get('date') or '---'
        examdate_formatted = format_examdate(firstdate)

    return caption, examdate_formatted


def format_examtime(starttime, endtime, label_txt, has_practexam):  # PR2022-08-13 PR2022-10-13

    examtime_formatted = ''

    if has_practexam:
        caption = label_txt.get('duration') or '---'
        if starttime:
            examtime_formatted = ' '.join((starttime, label_txt['minutes']))
    else:
        caption = label_txt.get('time') or '---'
        time_str = ''
        if starttime:
            if endtime:
                time_str = ' - '.join((starttime, endtime))
            else:
                time_str = starttime
        else:
            if endtime:
                time_str = endtime
        if time_str:
            examtime_formatted = ' '.join((time_str,  label_txt['oclock']))

    return caption, examtime_formatted


def create_exam_with_label_rows(sel_examyear):
    # PR2022-08-19
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_exam_with_label_rows ----- ')

    rows = []
    if sel_examyear:
        # note: ORDER BY lblitm.id is added to make sure the agg listst have the samme order,
        # even when they have the same sequence
        sql_keys = {'ey_id': sel_examyear.pk}

        sub_sql_list = [
            "SELECT bndllbl.id, bndllbl.envelopbundle_id, bndllbl.enveloplabel_id,",
            "lbl.name AS lbl_name, bundle.name AS bundle_name",

            "ARRAY_AGG(itm.content_nl ORDER BY lblitm.sequence, lblitm.id) AS content_nl,",
            "ARRAY_AGG(itm.content_en ORDER BY lblitm.sequence, lblitm.id) AS content_en,",
            "ARRAY_AGG(itm.content_pa ORDER BY lblitm.sequence, lblitm.id) AS content_pa,",
            "ARRAY_AGG(itm.instruction_nl ORDER BY lblitm.sequence, lblitm.id) AS instruction_nl,",
            "ARRAY_AGG(itm.instruction_en ORDER BY lblitm.sequence, lblitm.id) AS instruction_en,",
            "ARRAY_AGG(itm.instruction_pa ORDER BY lblitm.sequence, lblitm.id) AS instruction_pa,",
            "ARRAY_AGG(itm.content_color ORDER BY lblitm.sequence, lblitm.id) AS content_color,",
            "ARRAY_AGG(itm.instruction_color ORDER BY lblitm.sequence, lblitm.id) AS instruction_color,",
            "ARRAY_AGG(lblitm.sequence ORDER BY lblitm.sequence, lblitm.id) AS sequence,",

            "FROM subjects_enveloplabel AS lbl",
            "INNER JOIN subjects_enveloplabelitem AS lblitm ON (lblitm.enveloplabel_id = lbl.id)",
            "INNER JOIN subjects_envelopitem AS itm ON (itm.id = lblitm.envelopitem_id)",

            "WHERE lbl.examyear_id = %(ey_id)s::INT",
            "GROUP BY lbl.id"
        ]
        sub_sql = ' '.join(sub_sql_list)

        sql_keys = {'ey_id': sel_examyear.pk}
        sub_sql_list = [
            "SELECT bndllbl.id, bndllbl.envelopbundle_id, bndllbl.enveloplabel_id,",
            "lbl.name AS lbl_name, bundle.name AS bundle_name",

            "FROM subjects_envelopbundle AS bundle",
            "FROM subjects_envelopbundlelabel AS bndllbl",
            "INNER JOIN subjects_envelopbundlelabel AS bndllbl ON (bndllbl.envelopbundle_id = bundle.id)",
            "INNER JOIN subjects_enveloplabel AS lbl ON (lbl.id = bndllbl.enveloplabel_id)",
            "INNER JOIN subjects_enveloplabel AS lbl ON (lbl.id = bndllbl.enveloplabel_id)",

            "WHERE bundle.examyear_id = %(ey_id)s::INT",
            "ORDER BY bndllbl.id"
        ]
        sub_sql = ' '.join(sub_sql_list)

        sql_list = ["WITH enveloplabel AS (", sub_sql, ")",

                "SELECT exam.id AS exam_id, exam.version, exam.examperiod, exam.ete_exam,",
                "exam.datum, exam.begintijd, exam.eindtijd, exam.secret_exam,",
                "exam.has_errata, exam.subject_color,",
                "subjbase.id AS subjbase_id, subj.name AS subj_name,",
                "depbase.id AS depbase_id, depbase.code AS depbase_code,",
                "lvl.base_id AS lvlbase_id, level.abbrev AS lvl_abbrev,",

                "FROM subjects_exam AS exam",
                "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id)",
                "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = subj.examyear_id)",

                "INNER JOIN schools_department AS dep ON (dep.id = exam.department_id)",
                "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = exam.level_id)",

                "LEFT JOIN enveloplabel ON (enveloplabel.envelopbundle_id = exam.envelopbundle_id)",

# - show only exams of this exam year
                "WHERE ey.code = %(ey_code_int)s::INT"
                ]

        sql = ' '.join(sql_list)

        #if logging_on:
            #logger.debug('sql_keys: ' + str(sql_keys))
            #logger.debug('sql: ' + str(sql))
            #logger.debug('connection.queries: ' + str(connection.queries))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = af.dictfetchall(cursor)

    return rows
# - end of create_exam_with_label_rows

def get_dep_lvl_color(dep_abbrev, lvl_abbrev):  #PR2022-09-03
    if lvl_abbrev == 'PBL':
        dep_lvl_color = 'green'
    elif lvl_abbrev == 'PKL':
        dep_lvl_color = 'yellow'
    elif lvl_abbrev == 'TKL':
        dep_lvl_color = 'purple'
    elif dep_abbrev == 'HAVO':
        dep_lvl_color = 'blue'
    elif dep_abbrev == 'VWO':
        dep_lvl_color = 'orange'
    else:
        dep_lvl_color = 'black'
    return dep_lvl_color


def get_subj_name(lang, subj_name_pa, subj_name_en, subj_name_nl):  #PR2022-09-03

    if lang == 'pa' and subj_name_pa:
        subj_name = subj_name_pa
    elif lang == 'en' and subj_name_en:
        subj_name = subj_name_en
    elif subj_name_nl:
        subj_name = subj_name_nl
    else:
        subj_name = ''

    #if version:
    #    translated_version, version_hex_color = translate_version(version, lang)
    #    subj_name += ' - ' + translated_version

    return subj_name


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

@method_decorator([login_required], name='dispatch')
class EnvelopPrintReceiptView(View):  # PR2023-03-04

    def get(self, request, lst):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ')
            logger.debug(' ============= EnvelopPrintReceiptView ============= ')
            logger.debug('    lst: ' + str(lst))
            """
            lst: {"subject_list":[12],"schoolbase_list":[2,5],"sel_layout":"none","lvlbase_pk_list":[]}
            lst: {"exam_pk_list":[34],"schoolbase_pk_list":[2],"subjbase_pk_list":[133],"sel_layout":"errata_only"}
            lst: {"envelopsubject_pk_list":[76],"sel_layout":"all"}  
            lst: {"mode":"receipt","schoolbase_pk_list":[3],"sel_exam":"cspe"}
            """

    # paper size of labels is: 'Statement', Width: 21.59 cm Height: 13.97 cm or 8.5 inch x 5.5 inch or 612 x 396 points
    # pagesize A4 = (595.27, 841.89) points, 1 point = 1/72 inch

        response = None

        if request.user and request.user.country and request.user.schoolbase and lst:
            upload_dict = json.loads(lst)

            req_user = request.user

# - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get selected examyear, school and department from usersettings
            sel_examyear, sel_schoolNIU, sel_departmentNIU, sel_level, may_edit, msg_list = \
                acc_view.get_selected_ey_school_dep_lvl_from_usersetting(request)

# - get selected examperiod from usersettings
            # sel_exam values are: 'cspe', 'cse', 'tv02'
            sel_exam = upload_dict.get('sel_exam')
            practex_only = sel_exam == 'cspe'
            sel_examperiod = 2 if sel_exam == 'tv02' else 1
            if logging_on:
                logger.debug(' practex_only ' + str(practex_only) + ' ' + str(type(practex_only)))
                logger.debug(' sel_examperiod ' + str(sel_examperiod) + ' ' + str(type(sel_examperiod)))

            # when schoolbase_pk_list has value [-1], it means that all schools must be printed
            # when schoolbase_pk_list has value None, it means that no schools must be printed

            schoolbase_pk_list = upload_dict.get('schoolbase_pk_list')
            envelopsubject_rows = get_envelopsubject_rows(
                sel_examyear=sel_examyear,
                append_dict={},
                practex_only=practex_only
            )
            if logging_on and False:
                if envelopsubject_rows:
                    logger.debug(' > envelopsubject_rows:')
                    for row in envelopsubject_rows:
                        logger.debug(' > ' + str(row))

            envelopsubject_pk_list = []
            if envelopsubject_rows:
                for row in envelopsubject_rows:
                    envelopsubject_pk = row.get('id')
                    if envelopsubject_pk:
                        envelopsubject_pk_list.append(envelopsubject_pk)

            if logging_on:
                logger.debug('    envelopsubject_pk_list: ' + str(envelopsubject_pk_list))

            sel_layout = None
            if schoolbase_pk_list is None:
                sel_layout = 'show_errata_always'

            elif not len(schoolbase_pk_list):
                sel_layout = 'show_errata_always'
            elif schoolbase_pk_list[0] == -1:
                schoolbase_pk_list = None

            if logging_on:
                logger.debug('    sel_examperiod: ' + str(sel_examperiod))
                logger.debug('    sel_exam:     ' + str(sel_exam))
                logger.debug('    schoolbase_pk_list: ' + str(schoolbase_pk_list))

# --- get department dictlist, ordered by sequence
            # fields are: depbase_id, depbase_code, dep_name, dep_level_req
            department_dictlist = subj_view.create_department_dictlist(sel_examyear)
            """
            department_dictlist: [
                {'depbase_id': 1, 'depbase_code': 'Vsbo', 'dep_name': 'Voorbereidend Secundair Beroepsonderwijs', 'dep_level_req': True}, 
                {'depbase_id': 2, 'depbase_code': 'Havo', 'dep_name': 'Hoger Algemeen Voortgezet Onderwijs', 'dep_level_req': False}, 
                {'depbase_id': 3, 'depbase_code': 'Vwo', 'dep_name': 'Voorbereidend Wetenschappelijk Onderwijs', 'dep_level_req': False}]
            """

# --- get lvlbase dictlist, ordered by sequence
            lvlbase_dictlist = subj_view.create_level_dictlist(sel_examyear)
            """
            lvlbase_dictlist: [
                {'lvlbase_id': 6, 'lvlbase_code': 'PBL', 'lvl_name': 'Praktisch Basisgerichte Leerweg'}, 
                {'lvlbase_id': 5, 'lvlbase_code': 'PKL', 'lvl_name': 'Praktisch Kadergerichte Leerweg'}, 
                {'lvlbase_id': 4, 'lvlbase_code': 'TKL', 'lvl_name': 'Theoretisch Kadergerichte Leerweg'}, 
                {'lvlbase_id': 0, 'lvlbase_code': '', 'lvl_name': ''}]
            """

# - get dict with schemeitem info per dep and lvl
            # schemeitem_dict is  filtered by department.examyear_id
            schemeitem_dict = get_schemeitem_info_per_dep_lvl(sel_examyear)

# - get envelop label info
            printlabel_dict = create_printlabel_dict(
                sel_examyear=sel_examyear,
                sel_examperiod=sel_examperiod,
                sel_layout=sel_layout,
                envelopsubject_pk_list=envelopsubject_pk_list
            )
            if logging_on:
                logger.debug('    printlabel_dict: ' + str(printlabel_dict) + ': ' + str(printlabel_dict))
                if printlabel_dict:
                    for key, value in printlabel_dict.items():
                        logger.debug('    printlabel_dict: ' + str(key) + ': ' + str(value))

            """
            key '1_5_133' = 'depbase_id': 1, 'lvlbase_id': 5, 'subjbase_id': 133,
            values: list of labels in bundle 
            printlabel_dict: {'1_5_133': [
                    {'env_subj_id': 278, 'dep_id': 10, 'lvl_id': 11, 'subj_id': 259, 'examperiod': 1, 'firstdate': datetime.date(2023, 4, 17), 'lastdate': datetime.date(2023, 5, 5), 'starttime': '240', 'endtime': None, 'has_errata': False, 'depbase_id': 1, 'lvlbase_id': 5, 'subjbase_id': 133, 'id_key': '1_5_133', 'bnd_name': 'CSPE-AC-A t/m D-PKL ', 'bndlbl_sequence': 133, 'lbl_name': 'CSPE-AC-PKL-A', 'is_errata': False, 'is_variablenumber': True, 'numberofenvelops': None, 'numberinenvelop': 15, 'content_nl_arr': ['Examen onderdeel A (60 min)', 'Minitoets (rood & blauw)', 'Bijlagen (3) (digitaal)', 'Bijlage '], 'content_en_arr': ['Exam part A (60 min)', 'Mini-test (red & blue)', 'Appendix (3) (digital)', 'Appendix '], 'content_pa_arr': ['Èksamen sekshon A (60 min)', 'Mini-prueba (kòrá & blou)', 'Anekso (3) (digital)', 'Anekso '], 'instruction_nl_arr': ['15 MINUTEN VOOR BEGIN VAN HET EXAMEN OPENEN EN BEOORDELINGSCHEMA VOORBEREIDEN.', None, None, None], 'instruction_en_arr': ['OPEN 15 MINUTES PRIOR TO THE START OF THE EXAM AND PREPAIR THE EVALUATION TABLE.', None, None, None], 'instruction_pa_arr': ['HABRI 15 MINÜT PROMÉ KU ÈKSAMEN KUMINSÁ I PREPARÁ E SKEMA DI EVALUASHON.', None, None, None], 'content_color_arr': ['black', 'black', 'black', 'black'], 'instruction_color_arr': ['red', 'red', None, None], 'content_font_arr': ['Bold', None, None, None], 'instruction_font_arr': [None, None, None, None], 'sequence_arr': [51, 52, 53, 138]}, 
                    {'env_subj_id': 278, 'dep_id': 10, 'lvl_id': 11, 'subj_id': 259, 'examperiod': 1, 'firstdate': datetime.date(2023, 4, 17), 'lastdate': datetime.date(2023, 5, 5), 'starttime': '240', 'endtime': None, 'has_errata': False, 'depbase_id': 1, 'lvlbase_id': 5, 'subjbase_id': 133, 'id_key': '1_5_133', 'bnd_name': 'CSPE-AC-A t/m D-PKL ', 'bndlbl_sequence': 134, 'lbl_name': 'CSPE-AC-PKL-B', 'is_errata': False, 'is_variablenumber': True, 'numberofenvelops': None, 'numberinenvelop': 15, 'content_nl_arr': ['Examen onderdeel B (30 min)', 'Bijlage (digitaal)', 'Bijlage '], 'content_en_arr': ['Exam part B (30 min)', 'Appendix (digital)', 'Appendix '], 'content_pa_arr': ['Èksamen sekshon B (30 min)', 'Anekso (digital)', 'Anekso '], 'instruction_nl_arr': ['15 MINUTEN VOOR BEGIN VAN HET EXAMEN OPENEN EN BEOORDELINGSCHEMA VOORBEREIDEN.', None, None], 'instruction_en_arr': ['OPEN 15 MINUTES PRIOR TO THE START OF THE EXAM AND PREPAIR THE EVALUATION TABLE.', None, None], 'instruction_pa_arr': ['HABRI 15 MINÜT PROMÉ KU ÈKSAMEN KUMINSÁ I PREPARÁ E SKEMA DI EVALUASHON.', None, None], 'content_color_arr': ['black', 'black', 'black'], 'instruction_color_arr': ['red', None, None], 'content_font_arr': ['Bold', None, None], 'instruction_font_arr': [None, None, None], 'sequence_arr': [51, 137, 138]}, 
                    {'env_subj_id': 278, 'dep_id': 10, 'lvl_id': 11, 'subj_id': 259, 'examperiod': 1, 'firstdate': datetime.date(2023, 4, 17), 'lastdate': datetime.date(2023, 5, 5), 'starttime': '240', 'endtime': None, 'has_errata': False, 'depbase_id': 1, 'lvlbase_id': 5, 'subjbase_id': 133, 'id_key': '1_5_133', 'bnd_name': 'CSPE-AC-A t/m D-PKL ', 'bndlbl_sequence': 135, 'lbl_name': 'CSPE-AC-PKL-C', 'is_errata': False, 'is_variablenumber': True, 'numberofenvelops': None, 'numberinenvelop': 15, 'content_nl_arr': ['Examen onderdeel C (60 min)', 'Bijlage '], 'content_en_arr': ['Exam part C (60 min)', 'Appendix '], 'content_pa_arr': ['Èksamen sekshon C (60 min)', 'Anekso '], 'instruction_nl_arr': ['15 MINUTEN VOOR BEGIN VAN HET EXAMEN OPENEN EN BEOORDELINGSCHEMA VOORBEREIDEN.', None], 'instruction_en_arr': ['OPEN 15 MINUTES PRIOR TO THE START OF THE EXAM AND PREPAIR THE EVALUATION TABLE.', None], 'instruction_pa_arr': ['HABRI 15 MINÜT PROMÉ KU ÈKSAMEN KUMINSÁ I PREPARÁ E SKEMA DI EVALUASHON.', None], 'content_color_arr': ['black', 'black'], 'instruction_color_arr': ['red', None], 'content_font_arr': ['Bold', None], 'instruction_font_arr': [None, None], 'sequence_arr': [51, 137]}, 
                    {'env_subj_id': 278, 'dep_id': 10, 'lvl_id': 11, 'subj_id': 259, 'examperiod': 1, 'firstdate': datetime.date(2023, 4, 17), 'lastdate': datetime.date(2023, 5, 5), 'starttime': '240', 'endtime': None, 'has_errata': False, 'depbase_id': 1, 'lvlbase_id': 5, 'subjbase_id': 133, 'id_key': '1_5_133', 'bnd_name': 'CSPE-AC-A t/m D-PKL ', 'bndlbl_sequence': 136, 'lbl_name': 'CSPE-AC-PKL-D', 'is_errata': False, 'is_variablenumber': True, 'numberofenvelops': None, 'numberinenvelop': 15, 'content_nl_arr': ['Examen onderdeel D (90 min)', 'Minitoets (rood & blauw)', 'Bijlagen (2)', 'Uitwerkbijlagen (4) '], 'content_en_arr': ['Exam part D (90 min)', 'Mini-test (red & blue)', 'Appendix (2)', 'Work appendix (4)'], 'content_pa_arr': ['Èksamen sekshon D (90 min)', 'Mini-prueba (kòrá & blou)', 'Anekso (2)', 'Anekso di elaborashon (4)'], 'instruction_nl_arr': ['15 MINUTEN VOOR BEGIN VAN HET EXAMEN OPENEN EN BEOORDELINGSCHEMA VOORBEREIDEN.', None, None, None], 'instruction_en_arr': ['OPEN 15 MINUTES PRIOR TO THE START OF THE EXAM AND PREPAIR THE EVALUATION TABLE.', None, None, None], 'instruction_pa_arr': ['HABRI 15 MINÜT PROMÉ KU ÈKSAMEN KUMINSÁ I PREPARÁ E SKEMA DI EVALUASHON.', None, None, None], 'content_color_arr': ['black', 'black', 'black', 'black'], 'instruction_color_arr': ['red', 'red', None, None], 'content_font_arr': ['Bold', None, None, None], 'instruction_font_arr': [None, None, None, None], 'sequence_arr': [51, 52, 183, 185]}, 
                    {'env_subj_id': 278, 'dep_id': 10, 'lvl_id': 11, 'subj_id': 259, 'examperiod': 1, 'firstdate': datetime.date(2023, 4, 17), 'lastdate': datetime.date(2023, 5, 5), 'starttime': '240', 'endtime': None, 'has_errata': False, 'depbase_id': 1, 'lvlbase_id': 5, 'subjbase_id': 133, 'id_key': '1_5_133', 'bnd_name': 'CSPE-AC-A t/m D-PKL ', 'bndlbl_sequence': 137, 'lbl_name': 'CSPE-CV-AC R&B', 'is_errata': False, 'is_variablenumber': False, 'numberofenvelops': 1, 'numberinenvelop': 1, 'content_nl_arr': ['Correctievoorschrift (minitoets)'], 'content_en_arr': ['Scoring instruction (mini-test) '], 'content_pa_arr': ['Reglamento di korekshon (mini-prueba) '], 'instruction_nl_arr': ['NIET EERDER OPENEN, DAN NA AFLOOP VAN DE EXAMENZITTING.'], 'instruction_en_arr': ['DO NOT OPEN BEFORE THE EXAMINATION SESSION HAS ENDED.'], 'instruction_pa_arr': ['NO HABRI PROMÉ KU E SESHON DI ÈKSAMEN FINALISÁ.'], 'content_color_arr': ['red'], 'instruction_color_arr': ['red'], 'content_font_arr': [None], 'instruction_font_arr': [None], 'sequence_arr': [56]}, 
                    {'env_subj_id': 278, 'dep_id': 10, 'lvl_id': 11, 'subj_id': 259, 'examperiod': 1, 'firstdate': datetime.date(2023, 4, 17), 'lastdate': datetime.date(2023, 5, 5), 'starttime': '240', 'endtime': None, 'has_errata': False, 'depbase_id': 1, 'lvlbase_id': 5, 'subjbase_id': 133, 'id_key': '1_5_133', 'bnd_name': 'CSPE-AC-A t/m D-PKL ', 'bndlbl_sequence': 138, 'lbl_name': 'CSPE-CV-AC-PBL/PKL', 'is_errata': False, 'is_variablenumber': False, 'numberofenvelops': 1, 'numberinenvelop': 1, 'content_nl_arr': ['Correctievoorschrift (praktijkexamen) ', 'Instructie examinator '], 'content_en_arr': ['Scoring instruction (practical exam) ', 'Instruction Examiner '], 'content_pa_arr': ['Reglamento di korekshon (èksamen práktiko) ', 'Instrukshon eksaminadó'], 'instruction_nl_arr': ['15 MINUTEN VOOR BEGIN VAN HET EXAMEN OPENEN EN BEOORDELINGSCHEMA VOORBEREIDEN.', None], 'instruction_en_arr': ['OPEN 15 MINUTES PRIOR TO THE START OF THE EXAM AND PREPAIR THE EVALUATION TABLE.', None], 'instruction_pa_arr': ['HABRI 15 MINÜT PROMÉ KU ÈKSAMEN KUMINSÁ I PREPARÁ E SKEMA DI EVALUASHON.', None], 'content_color_arr': ['red', 'black'], 'instruction_color_arr': ['red', None], 'content_font_arr': [None, None], 'instruction_font_arr': [None, None], 'sequence_arr': [60, 136]}, 
                    {'env_subj_id': 278, 'dep_id': 10, 'lvl_id': 11, 'subj_id': 259, 'examperiod': 1, 'firstdate': datetime.date(2023, 4, 17), 'lastdate': datetime.date(2023, 5, 5), 'starttime': '240', 'endtime': None, 'has_errata': False, 'depbase_id': 1, 'lvlbase_id': 5, 'subjbase_id': 133, 'id_key': '1_5_133', 'bnd_name': 'CSPE-AC-A t/m D-PKL ', 'bndlbl_sequence': 139, 'lbl_name': 'moeder env. AC-PKL ', 'is_errata': False, 'is_variablenumber': False, 'numberofenvelops': 1, 'numberinenvelop': 0, 'content_nl_arr': ['Examen onderdeel A, B, C, D', 'Minitoets ond. A - D (rood & blauw)', 'Bijlagen (digitaal)', 'Bijlagen', 'Uitwerkbijlagen', 'Correctievoorschrift (praktijk & minitoets) ', 'Instructie examinator '], 'content_en_arr': ['Exam part A, B, C, D', 'Mini-test part A - D (red & blue)', 'Appendix (digital)', 'Appendix', 'Work appendix', 'Scoring instruction (practical & mini-test) ', 'Instruction Examiner '], 'content_pa_arr': ['Èksamen sekshon A, B, C, D', 'Mini-prueba èks. A - D (kòrá & blou)', 'Anekso (digital)', 'Anekso', 'Anekso di elaborashon', 'Reglamento di korekshon (práktiko & mini-prueba) ', 'Instrukshon eksaminadó'], 'instruction_nl_arr': ['20 MINUTEN VOOR BEGIN VAN HET EXAMEN OPENEN EN BEOORDELINGSCHEMA VOORBEREIDEN!', None, None, None, None, None, None], 'instruction_en_arr': ['OPEN 20 MINUTES PRIOR TO THE START OF THE EXAM AND PREPAIR THE EVALUATION TABLE!', None, None, None, None, None, None], 'instruction_pa_arr': ['HABRI 20 MINÜT PROMÉ KU ÈKSAMEN KUMINSÁ I PREPARÁ E SKEMA DI EVALUASHON!', None, None, None, None, None, None], 'content_color_arr': ['black', None, 'black', 'black', 'black', 'black', 'black'], 'instruction_color_arr': ['red', None, None, None, None, None, None], 'content_font_arr': ['Bold', None, None, None, None, None, None], 'instruction_font_arr': [None, None, None, None, None, None, None], 'sequence_arr': [55, 88, 105, 107, 109, 185, 252]}], 
            """

# - get schoolbase dictlist
            # function creates ordered dictlist of all schoolbase_pk, schoolbase_code and school_name
            #  of this exam year of all countries (only SXM when requsr=sxm), ordered by code
            # filtered by schoolbase_pk_list
            schoolbase_dictlist = subj_view.create_schoolbase_dictlist(sel_examyear, request, schoolbase_pk_list)
            if logging_on:
                logger.debug(' schoolbase_dictlist: ' + str(schoolbase_dictlist))
            """
            schoolbase_dictlist contains a list of selected schools
            schoolbase_dictlist: [
                {'sbase_id': 2, 'sbase_code': 'CUR01', 'depbases': '1', 'sch_otherlang': None, 'sch_article': 'de', 'sch_name': 'Ancilla Domini Vsbo', 'sch_abbrev': 'Ancilla Domini', 'defaultrole': 8}, 
                {'sbase_id': 3, 'sbase_code': 'CUR02', 'depbases': '1', 'sch_otherlang': None, 'sch_article': 'de', 'sch_name': 'Skol Avansá Amador Nita', 'sch_abbrev': 'SAAN', 'defaultrole': 8}, 

                {'sbase_id': 33, 'sbase_code': 'SXM04', 'depbases': '1;2;3', 'sch_otherlang': 'en', 'sch_article': 'de', 'sch_name': 'Landsexamens Sint Maarten', 'sch_abbrev': 'LEX St. Maarten', 'defaultrole': 8}, 
                {'sbase_id': 34, 'sbase_code': 'SXMDOE', 'depbases': '1;2;3', 'sch_otherlang': 'en', 'sch_article': 'de', 'sch_name': 'Division of Examinations', 'sch_abbrev': 'Division of Examinations', 'defaultrole': 64}]  
           
            schoolbase_dictlist: [
                {'sbase_id': 13, 'sbase_code': 'CUR13', 'depbases': '1;2;3', 'sch_otherlang': None, 'sch_article': 'het', 'sch_name': 'Abel Tasman College', 'sch_abbrev': 'ATC', 'defaultrole': 8}]

            """

# +++ get dict with number of studsubj. PR2022-10-14
            # if orderlist is published: Enveloporderlist exists and orderdict has value
            #   get envelop_count_per_school_dict from enveloporderlist
            # if orderlist is not published: create envelop_count_per_school_dict

# - get existing Enveloporderlist of this examyear
            # it contains 1 row per examyear with orderdict with amount
            enveloporderlist = subj_mod.Enveloporderlist.objects.filter(
                examyear=sel_examyear
            ).order_by('-pk').first()

            if logging_on and False:
                order_dict = getattr(enveloporderlist, 'orderdict')
                logger.debug(' > order_dict: ' + str(order_dict))

# - get envelop_count_per_school_dict from enveloporderlist.orderdict
            envelop_count_per_school_dict = None
            if enveloporderlist and enveloporderlist.orderdict:
                envelop_count_per_school_dict = json.loads(enveloporderlist.orderdict)

                if logging_on:
                    logger.debug(' > schoolbase_pk_list: ' + str(schoolbase_pk_list))

                # - remove schools that are not in schoolbase_pk_list
                if schoolbase_pk_list:
                    # because of error 'dictionary changed size during iteration':
                    # first store keys in list, then remove them
                    keys_tobe_removed = []
                    for envelop_sbase_pk_str in envelop_count_per_school_dict:
        # - check if schoolbase_pk exists in schoolbase_pk_list
                        key_exists_in_list = False
                        for schoolbase_pk in schoolbase_pk_list:
                            if envelop_sbase_pk_str == str(schoolbase_pk):
                                key_exists_in_list = True
                                break
        # - add key to keys_tobe_removed list if it does not exist in schoolbase_pk_list
                        if not key_exists_in_list:
                            keys_tobe_removed.append(envelop_sbase_pk_str)

                    if logging_on and False:
                        logger.debug(' > keys_tobe_removed: ' + str(keys_tobe_removed))

        # - remove keys that don't exist in schoolbase_pk_list
                    if keys_tobe_removed:
                        for sbase_pk_str in keys_tobe_removed:
                            envelop_count_per_school_dict.pop(sbase_pk_str, None)

                    if logging_on :
                        for key, value in envelop_count_per_school_dict.items():
                            logger.debug('    envelop_count_per_school_item: ' + str(key) + ': ' + str(value))
#?????????????????????????????????????????????????
            if logging_on:
                logger.debug(' ????????   printlabel_dict: ' + str(printlabel_dict))
                for key, value in printlabel_dict.items():
                    logger.debug(' ????????   printlabel_item: ' + str(key) + ': ' + str(value))

# ---use existing envelop_count_per_school_dict if it exists
            if envelop_count_per_school_dict:
                """
                envelop_count_per_school_dict: 
                {'2': {'c': '-', 
                        '1': {'c': '-', 
                            '4': [  {'subjbase_id': 133, 'ete_exam': True, 'id_key': '1_4_133', 'subjbase_code': 'ac', 'lang': 'nl', 'country_id': 1, 
                                        'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 4, 'subj_count': 8, 'extra_count': 7, 'tv2_count': 5}, 
                                    {'subjbase_id': 123, 'ete_exam': False, 'id_key': '1_4_123', 'subjbase_code': 'bi', 'lang': 'nl', 'country_id': 1, 
                                        'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 4, 'subj_count': 52, 'extra_count': 8, 'tv2_count': 15}, 
                                    {'subjbase_id': 155, 'ete_exam': False, 'id_key': '1_4_155', 'subjbase_code': 'ec', 'lang': 'nl', 'country_id': 1, 
                                    'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 4, 'subj_count': 8, 'extra_count': 7, 'tv2_count': 5}, 
                                    {'subjbase_id': 114, 'ete_exam': True, 'id_key': '1_4_114', 'subjbase_code': 'en', 'lang': 'nl', 'country_id': 1, 
                                    'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 4, 'subj_count': 60, 'extra_count': 5, 'tv2_count': 15}, 
                                    {'subjbase_id': 124, 'ete_exam': True, 'id_key': '1_4_124', 'subjbase_code': 'mm2', 'lang': 'nl', 'country_id': 1, 
                                    'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 4, 'subj_count': 60, 'extra_count': 5, 'tv2_count': 15}, 
                                    {'subjbase_id': 113, 'ete_exam': True, 'id_key': '1_4_113', 'subjbase_code': 'ne', 'lang': 'nl', 'country_id': 1, 
                                    'schoolbase_id': 2, 'depbase_id': 1, 'lvlbase_id': 4, 'subj_count': 60, 'extra_count': 5, 'tv2_count': 15}, 
                                    {'subjbase_id': 118, 'ete_exam': True, 'id_key': '1_4_118', 'subjbase_code': 'pa', 'lang': 'nl', 'country_id': 1,            
                """

            else:
# --- or create new existing envelop_count_per_school_dict if it does not yet existexists
                # TODO chekc this code
                subjbase_pk_list = []
                count_dictNIU, envelop_count_per_school_dict = subj_calc.create_studsubj_count_dict(
                    sel_examyear_instance=sel_examyear,
                    sel_examperiod=sel_examperiod,
                    request=request,
                    schoolbase_pk_list=schoolbase_pk_list,
                    subjbase_pk_list=subjbase_pk_list
                )

# --- print receipt
            pdf = create_envelop_receipt_pdf(
                sel_examyear=sel_examyear,
                sel_examperiod=sel_examperiod,
                schoolbase_dictlist=schoolbase_dictlist,
                department_dictlist=department_dictlist,
                lvlbase_dictlist=lvlbase_dictlist,
                schemeitem_dict=schemeitem_dict,
                printlabel_dict=printlabel_dict,
                count_per_school_dict=envelop_count_per_school_dict,
                practex_only=practex_only
            )

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="Labels.pdf"'

            response.write(pdf)

        #except Exception as e:
       #     logger.error(getattr(e, 'message', str(e)))
       #     raise Http404("Error creating Ex2A file")

        if response:
            return response
        else:
            logger.debug('HTTP_REFERER: ' + str(request.META.get('HTTP_REFERER')))
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
# - end of EnvelopPrintReceiptView


def create_envelop_receipt_pdf(sel_examyear, sel_examperiod, schoolbase_dictlist, department_dictlist,
                                        lvlbase_dictlist,
                                        schemeitem_dict, printlabel_dict, count_per_school_dict, practex_only):
    # PR2023-03-03
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' ----- create_envelop_receipt_pdf  -----')
        # logger.debug('    count_per_school_dict: ' + str(count_per_school_dict))


    ###########################
    def create_page_ranges():

        max_rows_one_page = 16 # PR2023-03-16 was: 14
        max_rows_first_last_page = 20  # PR2023-03-16 was: 18
        max_rows_middle_page = 26  # PR2023-03-16 was: 24

        row_count = len(receipt_examlabel_dictlist)
        page_ranges = []

        if logging_on and False:
            logger.debug(' ----- create_page_ranges  -----')
            logger.debug('    row_count: ' + str(row_count))

# - all rows fit on one page
        if row_count <= max_rows_one_page:
            page_ranges.append((0, row_count))

# - all rows fit on two pages
        elif row_count <= max_rows_first_last_page * 2:
            # put half of rows on first page (rounded up), rest on second page
            last_page_rows = int(row_count / 2)
            first_page_rows = row_count - last_page_rows
            page_ranges.append((0, first_page_rows))
            page_ranges.append((first_page_rows, row_count))

        else:

# - all rows fit on 3 or more pages
            # - calc number of pages
            # add difference of max_rows of first and last page
            row_count_adjusted = row_count + 2 * (max_rows_middle_page - max_rows_first_last_page)
            # divide by max_rows_middle_page and make integer
            page_count_rounddown = int(row_count_adjusted / max_rows_middle_page)
            page_count_frac = row_count_adjusted - (page_count_rounddown * max_rows_middle_page)
            page_count = page_count_rounddown + 1 if page_count_frac > 0 else page_count_rounddown

            avg_rows_per_page_rounddown = int(row_count_adjusted / page_count)
            avg_rows_frac = row_count_adjusted - (avg_rows_per_page_rounddown * page_count)
            avg_rows_per_page = avg_rows_per_page_rounddown + 1 if avg_rows_frac > 0 else avg_rows_per_page_rounddown

            # - calc average number of rows on 1 page (rounded up)
            if logging_on and False:
                logger.debug(' >  row_count_adjusted:  ' + str(row_count_adjusted))
                logger.debug(' >  page_count:  ' + str(page_count))
                logger.debug(' >  avg_rows_per_page:  ' + str(avg_rows_per_page))

            page_index = 0
            first_index_of_remaining_rows = 0
            remaining_rows = row_count

            while remaining_rows > 0:
                if page_index == 0 or page_index >= page_count - 1:
                    max_rows = avg_rows_per_page - (max_rows_middle_page - max_rows_first_last_page)
                else:
                    max_rows = avg_rows_per_page

                rows_tobe_added = max_rows if remaining_rows >= max_rows else remaining_rows
                if logging_on and False:
                    logger.debug('    ... page_index ' + str(page_index))
                    logger.debug('        remaining_rows ' + str(remaining_rows))
                    logger.debug('        max_rows ' + str(max_rows))
                    logger.debug('        rows_tobe_added ' + str(rows_tobe_added))

        # append page_range to page_ranges
                last_index = first_index_of_remaining_rows + rows_tobe_added
                page_ranges.append((first_index_of_remaining_rows, last_index))

                remaining_rows -= rows_tobe_added
                first_index_of_remaining_rows = last_index
                if logging_on and False:
                    logger.debug('     +  remaining_rows ' + str(remaining_rows))
                    logger.debug('     +  first_index_of_remaining_rows ' + str(first_index_of_remaining_rows))
                    logger.debug('     +  last_index ' + str(last_index))

                page_index += 1
        # end of while remaining_rows > 0

        if logging_on and False:
            logger.debug('     -> page_ranges ' + str(page_ranges))
        return page_ranges
    # - end of create_page_ranges
#################################

    # https://stackoverflow.com/questions/43373006/django-reportlab-save-generated-pdf-directly-to-filefield-in-aws-s3

    af.register_font_arial()
    af.register_font_calibri()
    af.register_font_palatino()

    # PR2021-04-28 from https://docs.python.org/3/library/tempfile.html
    # temp_file = tempfile.TemporaryFile()
    # canvas = Canvas(temp_file)
    buffer = io.BytesIO()
    canvas = Canvas(buffer)

    # PR2022-05-05 debug Oscar Panneflek Vpco lines not printing on Ex3
    # turn off setLineWidth (0)
    # canvas.setLineWidth(0)

    # A4 size (21cm, 29.7cm) is (595, 842)
    canvas.setPageSize( (595, 842))

    examperiod_txt = ''
    if sel_examperiod == 1:
        examperiod_txt = '1ste tijdvak'
    elif sel_examperiod == 2:
        examperiod_txt = '2e tijdvak'

# +++ loop through list of all schools
    for schoolbase_dict in schoolbase_dictlist:

        sbase_id = str(schoolbase_dict.get('sbase_id') or 0)
        school_name = schoolbase_dict.get('sch_name') or ''
        school_article = schoolbase_dict.get('sch_article') or ''

        school_lang = schoolbase_dict.get('sch_otherlang') or 'nl'
        if logging_on:
            logger.debug('    sbase_id: ' + str(sbase_id))
            logger.debug('    school_name: ' + str(school_name))
            logger.debug('    school_lang: ' + str(school_lang))

        schoolbase_count_dict = count_per_school_dict.get(sbase_id)

    # - check if school exists in print_dict
        if schoolbase_count_dict:

# +++ loop through list of all departments
            for department_dict in department_dictlist:

                depbase_id = str(department_dict.get('depbase_id') or 0)
                dep_name = department_dict.get('dep_name') or ''
                if logging_on:
                    logger.debug('========================')
                    logger.debug('    dep_name: ' + str(dep_name))

                # - check if department exists in schoolbase_count_dict
                # print_rows contains a list of subj/dep/level/examperiod/ete_exam combination (without link to exams)
                # with the number of exams-items , including extra exams. Blue/red version are taken in account
                # and count of different examns for the subject (blue/ red)
                depbase_count_dict = schoolbase_count_dict.get(depbase_id)
                if logging_on and False:
                    logger.debug('    depbase_count_dict: ' + str(depbase_count_dict))
                """
                depbase_count_dict = 
                {'c': '-', 
                '4': [{'subjbase_id': 133, 'ete_exam': True, 'id_key': '1_4_133', 'subjbase_code': 'ac', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 9, 'depbase_id': 1, 'lvlbase_id': 4, 'subj_count': 40, 'extra_count': 5, 'tv2_count': 10}, 
                      {'subjbase_id': 123, 'ete_exam': False, 'id_key': '1_4_123', 'subjbase_code': 'bi', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 9, 'depbase_id': 1, 'lvlbase_id': 4, 'subj_count': 27, 'extra_count': 8, 'tv2_count': 10}, 
                """

                if depbase_count_dict:

# +++ loop through list of all levels

                    for lvlbase_dict in lvlbase_dictlist:
                        lvlbase_id = str(lvlbase_dict.get('lvlbase_id') or 0)
                        lvl_name = lvlbase_dict.get('lvl_name') or ''
                        if logging_on:
                            logger.debug('    --------------------')
                            logger.debug('    lvl_name: ' + str(lvl_name))
                            #logger.debug('    lvlbase_dict: ' + str(lvlbase_dict))

                        """
                        lvlbase_dict: {'lvlbase_id': 6, 'lvlbase_code': 'PBL', 'lvl_name': 'Praktisch Basisgerichte Leerweg'}
                        """

                        """
                            -- printlabel_dict: 
                                {'1_6_123': [
                                    {'env_subj_id': 492, 'dep_id': 10, 'lvl_id': 10, 'subj_id': 238, 'examperiod': 1, 'firstdate': datetime.date(2023, 5, 10), 'lastdate': None, 'starttime': '07.30', 'endtime': '09.30', 'has_errata': False, 'depbase_id': 1, 'lvlbase_id': 6, 'subjbase_id': 123, 'id_key': '1_6_123', 'bnd_name': 'EXACT VK- BIO-PBL-CSE ', 'bndlbl_sequence': 137, 'lbl_name': 'BIO-PBL ', 'is_errata': False, 
                                        'is_variablenumber': True, 'numberofenvelops': None, 'numberinenvelop': 15, 'content_nl_arr': ['Opgavenboek'], 'content_en_arr': ['Assignment book'], 'content_pa_arr': ['Buki di tarea'], 'instruction_nl_arr': ['EERST DE NAAM VAN HET EXAMEN, DATUM EN TIJDSDUUR VOORLEZEN, DAARNA OPENEN!'], 'instruction_en_arr': ['FIRST READ THE EXAM NAME, DATE AND TIME, THEN OPEN!'], 'instruction_pa_arr': ['LESA PROMÉ NA BOS HALTU ÈKSAMEN, FECHA I DURASHON PROMÉ KU HABRI!'], 'content_color_arr': ['black'], 'instruction_color_arr': ['red'], 'content_font_arr': [None], 'instruction_font_arr': [None], 'sequence_arr': [56]}, 
                                    {'env_subj_id': 492, 'dep_id': 10, 'lvl_id': 10, 'subj_id': 238, 'examperiod': 1, 'firstdate': datetime.date(2023, 5, 10), 'lastdate': None, 'starttime': '07.30', 'endtime': '09.30', 'has_errata': False, 'depbase_id': 1, 'lvlbase_id': 6, 'subjbase_id': 123, 'id_key': '1_6_123', 'bnd_name': 'EXACT VK- BIO-PBL-CSE ', 'bndlbl_sequence': 187, 'lbl_name': 'BIO-CV ', 'is_errata': False,
                                        'is_variablenumber': False, 'numberofenvelops': 1, 'numberinenvelop': 2, 'content_nl_arr': ['Correctievoorschrift '], 'content_en_arr': ['Scoring Instruction '], 'content_pa_arr': ['Reglamento di korekshon '], 'instruction_nl_arr': ['NIET EERDER OPENEN, DAN NA AFLOOP VAN DE EXAMENZITTING.'], 'instruction_en_arr': ['DO NOT OPEN BEFORE THE EXAMINATION SESSION HAS ENDED.'], 'instruction_pa_arr': ['NO HABRI PROMÉ KU E SESHON DI ÈKSAMEN FINALISÁ.'], 'content_color_arr': ['red'], 'instruction_color_arr': ['red'], 'content_font_arr': [None], 'instruction_font_arr': [None], 'sequence_arr': [56]}]}
                        """


                        # - check if level exists in schoolbase_count_dict
                        # print_rows contains a list of subj/dep/level/examperiod/ete_exam combination (without link to exams)
                        # with the number of exams-items , including extra exams. Blue/red version are taken in account
                        # and count of different examns for the subject (blue/ red)
                        lvlbase_count_list = depbase_count_dict.get(lvlbase_id)

                        if logging_on:
                            if lvlbase_count_list:
                                logger.debug('    lvlbase_count_list: ' + str(len(lvlbase_count_list)))
                            else:
                                logger.debug('    lvlbase_count_list: ' + str(lvlbase_count_list))

                        """
                        lvlbase_count_list: [
                            {'subjbase_id': 133, 'ete_exam': True, 'id_key': '1_6_133', 'subjbase_code': 'ac', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 9, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 4, 'extra_count': 6, 'tv2_count': 5}, 
                            {'subjbase_id': 123, 'ete_exam': True, 'id_key': '1_6_123', 'subjbase_code': 'bi', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 9, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 2, 'extra_count': 3, 'tv2_count': 5}, 
                            {'subjbase_id': 155, 'ete_exam': True, 'id_key': '1_6_155', 'subjbase_code': 'ec', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 9, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 4, 'extra_count': 6, 'tv2_count': 5}, 
                            {'subjbase_id': 114, 'ete_exam': True, 'id_key': '1_6_114', 'subjbase_code': 'en', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 9, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 7, 'extra_count': 3, 'tv2_count': 5}, 
                            {'subjbase_id': 129, 'ete_exam': True, 'id_key': '1_6_129', 'subjbase_code': 'ie', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 9, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 1, 'extra_count': 4, 'tv2_count': 5}, 
                            {'subjbase_id': 124, 'ete_exam': True, 'id_key': '1_6_124', 'subjbase_code': 'mm2', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 9, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 1, 'extra_count': 4, 'tv2_count': 5}, 
                            {'subjbase_id': 122, 'ete_exam': True, 'id_key': '1_6_122', 'subjbase_code': 'nask1', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 9, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 1, 'extra_count': 4, 'tv2_count': 5}, 
                            {'subjbase_id': 113, 'ete_exam': True, 'id_key': '1_6_113', 'subjbase_code': 'ne', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 9, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 7, 'extra_count': 3, 'tv2_count': 5}, 
                            {'subjbase_id': 118, 'ete_exam': True, 'id_key': '1_6_118', 'subjbase_code': 'pa', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 9, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 7, 'extra_count': 3, 'tv2_count': 5}, 
                            {'subjbase_id': 120, 'ete_exam': True, 'id_key': '1_6_120', 'subjbase_code': 'sp', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 9, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 4, 'extra_count': 6, 'tv2_count': 5}, 
                            {'subjbase_id': 121, 'ete_exam': True, 'id_key': '1_6_121', 'subjbase_code': 'wk', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 9, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 2, 'extra_count': 3, 'tv2_count': 5}, 
                            {'subjbase_id': 131, 'ete_exam': True, 'id_key': '1_6_131', 'subjbase_code': 'zwi', 'lang': 'nl', 'country_id': 1, 'schoolbase_id': 9, 'depbase_id': 1, 'lvlbase_id': 6, 'subj_count': 2, 'extra_count': 3, 'tv2_count': 5}]
                        """

                        receipt_examlabel_dictlist = create_receipt_examlabel_dictlist(
                            sel_examyear=sel_examyear,
                            sel_examperiod=sel_examperiod,
                            schemeitem_dict=schemeitem_dict,
                            lvlbase_count_list=lvlbase_count_list,
                            printlabel_dict=printlabel_dict,
                            school_lang=school_lang
                        )
                        if receipt_examlabel_dictlist:
                            if logging_on and False:
                                logger.debug(' --->> receipt_examlabel_dictlist')
                                for txt in receipt_examlabel_dictlist:
                                    logger.debug(' --->> ' + str(txt))
                            """
                            receipt_examlabel_dictlist = [
                                {'subj_name': 'Administratie & Commercie', 'content_txt': 'Examen onderdeel A (60 min) etc.', 'total_items_txt': '20', 'total_envelops_txt': '1'}
                                {'subj_name': 'Administratie & Commercie', 'content_txt': 'Examen onderdeel D (90 min) etc.', 'total_items_txt': '20', 'total_envelops_txt': '1'}
                                {'subj_name': 'Administratie & Commercie', 'content_txt': 'Correctievoorschrift (minitoets)', 'total_items_txt': '1', 'total_envelops_txt': '1'}
                                {'subj_name': 'Administratie & Commercie', 'content_txt': 'Correctievoorschrift (praktijkexamen)  etc.', 'total_items_txt': '1', 'total_envelops_txt': '1'}
                                {'subj_name': 'Administratie & Commercie', 'content_txt': 'Examen onderdeel A, B, C, D etc.', 'total_items_txt': '0', 'total_envelops_txt': '1'}
                                {'subj_name': 'Biologie', 'content_txt': 'Opgavenboek', 'total_items_txt': '30', 'total_envelops_txt': '1'}
                            """
                            # create list with tuples of first rowindex and last rowindex plus one and last
                            page_ranges = create_page_ranges()
                            if logging_on:
                                logger.debug(' -> page_ranges ' + str(page_ranges))

                            total_pages = len(page_ranges)
                            total_number_of_envelops = 0
                            for page_index, page_range in enumerate(page_ranges):
                                if logging_on:
                                    logger.debug('  ... page_index: ' + str(page_index))
                                    logger.debug('  ... page_range: ' + str(page_range))

                                total_envelops_on_page = draw_receipt(canvas=canvas,
                                             examyear_txt=str(sel_examyear.code),
                                             examperiod_txt=examperiod_txt,
                                             school_name=school_name,
                                             school_article=school_article,
                                             dep_name=dep_name,
                                             lvl_name=lvl_name,
                                             practex_only=practex_only,
                                             school_lang=school_lang,
                                             receipt_examlabel_dictlist=receipt_examlabel_dictlist,
                                             page_index=page_index,
                                             total_pages=total_pages,
                                             page_range=page_range,
                                             total_number_of_envelops=total_number_of_envelops
                                             )
                                total_number_of_envelops += total_envelops_on_page
                                canvas.showPage()
    canvas.save()
    pdf = buffer.getvalue()

    return pdf
# - end of create_envelop_receipt_pdf


#######################################################################
def draw_receipt(canvas, examyear_txt, examperiod_txt, school_name, school_article, dep_name, lvl_name, practex_only,
                 school_lang, receipt_examlabel_dictlist,
                    page_index, total_pages, page_range, total_number_of_envelops):
    # PR2023-03-04
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('----- draw_receipt -----')

    def draw_page_header(coord):
        pos_x = coord[0]
        pos_y = coord[1]

        # - draw OWC and ETE logo
        # canvas.drawImage(image, x, y, width, height, mask=None)
        file_name = s.STATICFILES_IMG_DIR + "logo_minows.png"  # size 293 - 333
        # PR2022-10-06 was: canvas.drawInlineImage(file_name, pos_x, 4.35 * inch, 1.75 * inch, 1 * inch)
        canvas.drawInlineImage(file_name, pos_x, pos_y - .55 * inch, .8 * inch, 0.8 * inch)

        file_name = s.STATICFILES_IMG_DIR + "ETElogoWithText.png"  # size 1750 - 1000
        # PR2022-10-06 was: canvas.drawInlineImage(file_name, pos_x, 4.35 * inch, 1.75 * inch, 1 * inch)
        canvas.drawInlineImage(file_name, pos_x_margin_right - 1.4 * inch, pos_y - .55 * inch, 1.4 * inch, 0.8 * inch)

        # - draw MIN_OWC ETE text
        # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
        canvas.setFont('Palatino', 8, leading=None)
        # color header min owc rgb (255, 102, 0), #ff6600
        canvas.setFillColor(colors.HexColor("#ff6600"))
        canvas.drawString(pos_x + inch, pos_y, 'MINISTERIE VAN')
        canvas.setFont('Palatino_Bold_Italic', 11, leading=None)
        pos_y -= .8 * line_height
        canvas.drawString(pos_x + inch, pos_y, 'ONDERWIJS, WETENSCHAP, CULTUUR & SPORT')
        pos_y -= .8 * line_height
        canvas.setFont('Palatino_Italic', 9)
        canvas.drawString(pos_x + inch, pos_y, 'Expertisecentrum voor Toetsen & Examens')

        pos_y -= line_height * 1.5

        pos_y -= .575 * inch

        coord[1] = pos_y
# - end of draw_page_header

    def draw_line_statement(coord):
        pos_x = coord[0]
        pos_y = coord[1]

        # - draw VERKLARING VAN ONTVANGST
        caption = 'VERKLARING VAN ONTVANGST'
        canvas.setFont('Calibri_Bold', 20, leading=None)
        canvas.setFillColor(colors.HexColor("#000000"))
        canvas.drawCentredString(pos_x_center, pos_y, caption)

        pos_y -= .575 * inch

        caption = 'Hierbij verklaart ondergetekende de navolgende enveloppen te hebben ontvangen'
        canvas.setFont('Calibri', 14)
        canvas.setFillColor(colors.HexColor("#000000"))
        canvas.drawString(pos_x, pos_y, caption)

        pos_y -= line_height
        caption = 'van het Expertisecentrum voor Toetsen & Examens ten behoeve van ' + school_article + ':'
        canvas.drawString(pos_x, pos_y, caption)

        pos_y -= line_height * 2

        coord[1] = pos_y
# - end of draw_line_statement

    def draw_line_school_dep_lvl(coord):
        pos_y = coord[1]

        # - draw school name
        canvas.setFillColor(colors.HexColor("#000000"))
        canvas.setFont('Arial_Black', 14)
        canvas.drawCentredString(pos_x_center, pos_y, school_name)

        # - draw dep name
        pos_y -= line_height
        canvas.setFont('Arial', 14)
        canvas.drawCentredString(pos_x_center, pos_y, dep_name)
        canvas.setFont('Arial', 14)

        # - draw level name if it exists
        if lvl_name:
            pos_y -= line_height
            canvas.setFont('Arial', 12)
            canvas.drawCentredString(pos_x_center, pos_y, lvl_name)

        pos_y -= line_height

        coord[1] = pos_y
# - end of draw_line_school_dep_lvl

    def draw_receipt_table_header(canvas, coord, col_tab_list):

        col_last_index = len(col_tab_list) - 1
        line_height = 6 * mm

        x = coord[0]
        y_top = coord[1]
        y_bottom = y_top - line_height * 2

# - draw horizontal lines above and below column header
        x_left = coord[0] + col_tab_list[0] * mm
        x_right = coord[0] + col_tab_list[col_last_index] * mm
        canvas.line(x_left, y_top, x_right, y_top)

        canvas.line(x_left, y_bottom, x_right, y_bottom)

# - draw horizontal lines below 'Examens ETE'
        x_index_2 = x + col_tab_list[2] * mm
        y_top_index_2 = y_top - line_height
        canvas.line(x_left, y_top_index_2, x_index_2, y_top_index_2)

# - draw vertical lines of columns
        for index in range(0, col_last_index + 1):  # range(start_value, end_value, step), end_value is not included!
            line_x = coord[0] + col_tab_list[index] * mm
            line_y_top = y_top_index_2 if index == 1 else y_top
            canvas.line(line_x, line_y_top, line_x, y_bottom)

        cse_cspe_txt = 'Centraal Schriftelijke Praktijk Examens ETE' if practex_only else 'Centraal Schriftelijke Examens ETE'
        caption = ' '.join((cse_cspe_txt, examyear_txt, '-', examperiod_txt))
        txt_list = [
            {'txt': caption, 'font': 'Calibri_Bold', 'size': 12, 'padding': 2, 'x': x + col_tab_list[0] * mm},
            {},
            {'txt': 'Aantal', 'font': 'Calibri', 'size': 11, 'align': 'c', 'x': x + (col_tab_list[2] + col_tab_list[3]) / 2 * mm, 'offset': 0},
            {'txt': 'Aantal', 'font': 'Calibri', 'size': 11, 'align': 'c', 'x': x + (col_tab_list[3] + col_tab_list[4]) / 2 * mm, 'offset': 0},
        ]
        draw_receipt_one_line(canvas, coord, col_tab_list, line_height, 1.5, False, False, txt_list)

        txt_list = [
            {'txt': 'Vak', 'font': 'Calibri_Bold', 'size': 12, 'padding': 2, 'x': x + col_tab_list[0] * mm},
            {'txt': 'Inhoud', 'font': 'Calibri_Bold', 'size': 12, 'padding': 2, 'x': x + col_tab_list[1] * mm},
            {'txt': 'exemplaren', 'font': 'Calibri', 'size': 11, 'align': 'c', 'x': x + (col_tab_list[2] + col_tab_list[3]) / 2 * mm},
            {'txt': 'enveloppen', 'font': 'Calibri', 'size': 11, 'align': 'c', 'x': x + (col_tab_list[3] + col_tab_list[4]) / 2 * mm},
        ]
        draw_receipt_one_line(canvas, coord, col_tab_list, line_height, 1.5, False, False, txt_list)
# - end of draw_receipt_table_header

    def draw_receipt_table_rows():
        total_envelops_on_page = 0
        #  page_range = [first_row_of_page, last_row_of_page_plus_one]
        if page_range[1] > len(receipt_examlabel_dictlist):
            last_index_plus_one = len(receipt_examlabel_dictlist)
        else:
            last_index_plus_one = page_range[1]
        row_font = 'Calibri'
        row_size = 12
        for row_index in range(page_range[0],last_index_plus_one):  # range(start_value, end_value, step), end_value is not included!
            row = receipt_examlabel_dictlist[row_index]
            if row:

                subj_name = row.get('subj_name') or '-'
                content_txt = row.get('content_txt') or '-'
                total_items = row.get('total_items') or ''
                total_envelops = row.get('total_envelops') or 0
                total_envelops_on_page += total_envelops
                # print master_envelop bold. Is master envelop when total_items = 0
                row_font = 'Calibri' if total_items else 'Calibri_Bold'
    # - draw exam label line
                txt_list = [
                    {'txt': subj_name, 'font': row_font, 'size': row_size, 'padding': 2, 'x': coord[0] + col_tab_list[0] * mm},
                    {'txt': content_txt, 'font': row_font, 'size': row_size, 'padding': 2, 'x': coord[0] + col_tab_list[1] * mm},
                    {'txt': str(total_items), 'font': row_font, 'size': row_size, 'align': 'c',
                     'x': coord[0] + (col_tab_list[2] + col_tab_list[3]) / 2 * mm},
                    {'txt': str(total_envelops), 'font': row_font, 'size': row_size, 'align': 'c',
                     'x': coord[0] + (col_tab_list[3] + col_tab_list[4]) / 2 * mm},
                ]

                draw_receipt_one_line(canvas, coord, col_tab_list, line_height, 1.25, True, True, txt_list)

        return total_envelops_on_page
    # - end of draw_receipt_table_rows

    def draw_receipt_table_footer(total_number_of_envelops):
        line_height = 6 * mm
        # y_top = margin_bottom + inch * 3
        y_top = coord[1]
        y_bottom = y_top - line_height
        x_middle = pos_x_margin_left + col_tab_list[3] * mm

    # - draw horizontal lines above and below table_footer
        col_last_index = len(col_tab_list) - 1
        x_left = coord[0] + col_tab_list[0] * mm
        x_right = coord[0] + col_tab_list[col_last_index] * mm
        canvas.line(x_left, y_top, x_right, y_top)

        canvas.line(x_left, y_bottom, x_right, y_bottom)

# - draw horizontal lines above and below column header
        #canvas.setStrokeColorRGB(0, 0, 0)
        canvas.line(x_left, y_top, x_right, y_top)
        canvas.line(x_left, y_bottom, x_right, y_bottom)

# - draw vertical lines
        canvas.line(x_left, y_top, x_left, y_bottom)
        canvas.line(x_middle, y_top, x_middle, y_bottom)
        canvas.line(x_right, y_top, x_right, y_bottom)

# - draw text 'Totaal aantal enveloppen'
        txt_list = [
            {'txt': 'Totaal aantal enveloppen', 'font': 'Calibri_Bold', 'size': 11, 'padding': 2, 'x': coord[0] + col_tab_list[0] * mm},
            {}, {},
            {'txt': str(total_number_of_envelops), 'font': 'Calibri_Bold', 'size': 11, 'align': 'c', 'x': coord[0] + (col_tab_list[3] + col_tab_list[4]) / 2 * mm},
        ]
        draw_receipt_one_line(canvas, [x_left, y_top], col_tab_list, line_height, 1.5, False, False, txt_list)

        coord[1] = y_bottom
# - end of draw_receipt_table_footer

    def draw_receipt_CVTE_header():
        # skip when printing receipt of practex
        if not practex_only:
            line_height = 6 * mm
            # y_top = margin_bottom + inch * 3
            y_top = coord[1] - line_height
            y_middle = y_top - line_height
            y_bottom = y_middle - line_height
            x_middle = pos_x_margin_left + col_tab_list[1] * mm

            # - draw horizontal lines above and below column header
            col_last_index = len(col_tab_list) - 1
            x_left = coord[0] + col_tab_list[0] * mm
            x_right = coord[0] + col_tab_list[col_last_index] * mm
            canvas.line(x_left, y_top, x_right, y_top)

            canvas.line(x_left, y_bottom, x_right, y_bottom)

            # - draw horizontal lines above and below column header
            # canvas.setStrokeColorRGB(0, 0, 0)
            canvas.line(x_left, y_top, x_right, y_top)
            canvas.line(x_left, y_middle, x_right, y_middle)
            canvas.line(x_left, y_bottom, x_right, y_bottom)

            # - draw vertical lines
            canvas.line(x_left, y_top, x_left, y_bottom)
            canvas.line(x_middle, y_middle, x_middle, y_bottom)
            canvas.line(x_right, y_top, x_right, y_bottom)

            # - draw text 'Examens CVTE'
            caption = ' '.join(('Centraal Schriftelijke Examens CVTE', examyear_txt, '-', examperiod_txt))
            txt_list = [{'txt': caption, 'font': 'Calibri_Bold', 'size': 12, 'padding': 2, 'x': x_left}]
            draw_receipt_one_line(canvas, [x_left, y_top], col_tab_list, line_height, 1.5, False, False, txt_list)

            # - draw text 'Aantal dozen'
            txt_list = [{'txt': 'Aantal dozen', 'font': 'Calibri', 'size': 11, 'padding': 2, 'x': x_left}]
            draw_receipt_one_line(canvas, [x_left, y_top - line_height], col_tab_list, line_height, 1.5, False, False,
                                  txt_list)

            coord[1] = y_bottom
    # - end of draw_receipt_CVTE_header

    def draw_line_signature(coord):
        pos_x = coord[0]
        pos_x2 = pos_x + 1.5 * inch
        pos_x3 = pos_x + 4.5 * inch

        # pos_y = margin_bottom + inch * 1.25

        pos_y = coord[1] - line_height * 4

        canvas.line(pos_x, pos_y, pos_x2 - .5 * inch, pos_y)
        canvas.line(pos_x2, pos_y, pos_x3 - .5 * inch, pos_y)
        canvas.line(pos_x3, pos_y, pos_x_margin_right, pos_y)

        pos_y -= line_height

        canvas.setFont('Calibri', 12)
        canvas.setFillColor(colors.HexColor("#000000"))
        canvas.drawString(pos_x, pos_y, 'Datum')
        canvas.drawString(pos_x2, pos_y, 'Naam')
        canvas.drawString(pos_x3, pos_y, 'Handtekening voor ontvangst')
# - end of draw_line_signature

    def draw_page_footer(coord):
        pos_x = coord[0]
        #pos_y = margin_bottom + inch
        pos_y = margin_bottom + 15 * mm # PR2023-03-16 request drukteam 'De header moet hoger zijn'

        canvas.setFont('Calibri', 12)
        canvas.setFillColor(colors.HexColor("#000000"))
        if total_pages > 1:
            caption = ' '.join(('Bladzijde', str(page_index + 1), 'van',  str(total_pages)))
            canvas.drawRightString(pos_x_margin_right, pos_y, caption)

        pos_y -= line_height * .5

        canvas.setStrokeColorRGB(1, 102/255, 0)
        canvas.line(pos_x, pos_y, pos_x_margin_right, pos_y)

        canvas.setStrokeColorRGB(0, 0, 0)

        pos_y -= .6 * line_height

        # - draw MIN_OWC ETE text
        # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.

        canvas.setFillColor(colors.HexColor("#ff6600"))
        canvas.setFont('Palatino', 8, leading=None)
        # color header min owc rgb (255, 102, 0), #ff6600
        caption = 'Schouwburgweg 26 – (Office Complex APC-Plaza), Curaçao'
        canvas.drawCentredString(pos_x_center, pos_y, caption)
        pos_y -= .6 * line_height
        caption ='Tel.: (+599 9) 434-3700 / E-mail: helpdesk@ete.cw'
        canvas.drawCentredString(pos_x_center, pos_y, caption)
# - end of draw_page_header

    # paper size of labels is: 'Statement', Width: 21.59 cm Height: 13.97 cm or 8.5 inch x 5.5 inch or 612 x 396 points
    margin_bottom = 0.2 * inch
    line_height = 0.25 * inch

    pos_x_margin_left = .8 * inch
    pos_x_margin_right = 7.45 * inch
    pos_x_center = (pos_x_margin_left + pos_x_margin_right) / 2

    # pos_y = 10.75 * inch  # A4 is 11.69 x 8.27 inch
    pos_y = 282 * mm  #  A4 is 11.69 x 8.27 inch # PR2023-03-16 request drukteam 'De header moet hoger zijn'

    coord = [pos_x_margin_left, pos_y]

    col_tab_list = (0, 54, 128, 149, 170)

    total_envelops_on_page = 0
    draw_page_header(coord)

    if page_index == 0:
        draw_line_statement(coord)

    draw_line_school_dep_lvl(coord)

    draw_receipt_table_header(canvas, coord, col_tab_list)

    total_envelops_on_table = draw_receipt_table_rows()
    total_envelops_on_page += total_envelops_on_table

    if page_index == total_pages -1:
        # total_number_of_envelops does not include number of envelops on this page
        total_number_of_envelops += total_envelops_on_table
        draw_receipt_table_footer(total_number_of_envelops)
        draw_receipt_CVTE_header()

        draw_line_signature(coord)

    draw_page_footer(coord)


    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    if logging_on and False:
        for txt in receipt_examlabel_dictlist:
            logger.debug('  --: ' + str(txt))

    return total_envelops_on_page

# - end of draw_receipt
#######################################################################


def draw_receipt_one_line(canvas, coord, col_tab_list, line_height, offset_bottom,
                       draw_line_below, has_vertical_lines, text_list):
    # function creates one line with text for each item in list PR2021-11-16
    # x-coord[0] is not in use
    # coord[1] decreases with line_height

    y_pos_line = coord[1] - line_height

    for text_dict in text_list:
        #  text_dict = {'txt': '-', 'font', 'Times-Roman', 'size', 10 'color', '#000000' 'align', 'l' 'padding': 4, 'x': x 4 * mm,},
# - get info from text_dict
        text = text_dict.get('txt')
        if text:
            font_type = text_dict.get('font', 'Times-Roman')
            font_size = text_dict.get('size', 10)
            font_hexcolor = text_dict.get('color', '#000000')
            text_align = text_dict.get('align', 'l')
            padding = text_dict.get('padding', 0) * mm

            x_pos = text_dict.get('x', 0)

            # offset_bottom is default, can be overrruled by text_dict.offset
            offset = text_dict.get('offset')
            offset_text =  offset if offset is not None else offset_bottom
            y_pos_txt = y_pos_line + offset_text * mm

            # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
            canvas.setFont(font_type, font_size, leading=None)
            canvas.setFillColor(colors.HexColor(font_hexcolor))
            if text_align == 'c':
                x_pos_txt = x_pos
                canvas.drawCentredString(x_pos_txt, y_pos_txt, text)
            elif text_align == 'r':
                x_pos_txt = x_pos - padding
                canvas.drawRightString(x_pos_txt, y_pos_txt, text)
            else:
                x_pos_txt = x_pos + padding
                canvas.drawString(x_pos_txt, y_pos_txt, text)

    # - draw line at bottom of row
    if draw_line_below:
        canvas.setStrokeColorRGB(.5, .5, .5)
        left = coord[0] + col_tab_list[0] * mm
        right = coord[0] + col_tab_list[len(col_tab_list) -1] * mm
        canvas.line(left, y_pos_line, right, y_pos_line)

# - draw vertical lines of columns
    if has_vertical_lines:
        canvas.setStrokeColorRGB(.5, .5, .5)

        for index in range(0, len(col_tab_list)):  # range(start_value, end_value, step), end_value is not included!
            line_x = coord[0] + col_tab_list[index] * mm
            y_top = coord[1]
            y_bottom = y_pos_line
            canvas.line(line_x, y_top, line_x, y_bottom)

    coord[1] = y_pos_line
# - end of draw_receipt_one_line


def create_receipt_examlabel_dictlist(sel_examyear, sel_examperiod, schemeitem_dict, lvlbase_count_list, printlabel_dict, school_lang):

    # PR2023-03-05
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- create_receipt_examlabel_dictlist -------')

    receipt_examlabel_dictlist = []

    if sel_examyear and sel_examperiod and schemeitem_dict and lvlbase_count_list and printlabel_dict:

        for lvlbase_count_row in lvlbase_count_list:

# +++ lookup labels with id_key and loop through labels of printlabel_list
            #  id_key '1_4_133' = depbase_id, lvlbase_id or 0, subjbase_id
            id_key = lvlbase_count_row.get('id_key')
            lbl_list = printlabel_dict.get(id_key)

            if logging_on:
                logger.debug('    sel_examperiod: ' + str(sel_examperiod))
                logger.debug('    lbl_list: ' + str(lbl_list))

            if lbl_list:

    # - get tv_count if lbl_list of this id_key exists
                subj_count = lvlbase_count_row.get('subj_count') or 0
                extra_count = lvlbase_count_row.get('extra_count') or 0
                if sel_examperiod == c.EXAMPERIOD_FIRST:
                    tv_count = subj_count + extra_count
                elif sel_examperiod == c.EXAMPERIOD_SECOND:
                    tv_count = lvlbase_count_row.get('tv2_count') or 0
                else:
                    tv_count = 0

                if logging_on:
                    logger.debug('    tv_count: ' + str(tv_count))

    # loop through labels of this subject
                for lbl_dict in lbl_list:
                    dep_pk = lbl_dict.get('dep_id')
                    lvl_pk = lbl_dict.get('lvl_id') or 0
                    subj_pk = lbl_dict.get('subj_id')
                    examperiod = lbl_dict.get('examperiod')
                    has_errata = lbl_dict.get('has_errata') or False

                    if logging_on:
                        logger.debug('    lbl_dict: ' + str(lbl_dict))

                    dep_dict = schemeitem_dict.get(dep_pk)
                    if dep_dict:
                        lvl_dict = dep_dict.get(lvl_pk)
                        if lvl_dict:
                            subj_dict = lvl_dict.get(subj_pk)
                            if subj_dict:
                                otherlang_arr = subj_dict.get('otherlang')
                                lang = school_lang if otherlang_arr and school_lang in otherlang_arr else 'nl'
                                subj_name_key = 'subj_name_pa' if lang == 'pa' else 'subj_name_en' if lang == 'en' else 'subj_name_nl'
                                subj_name = subj_dict.get(subj_name_key) or '-'
                                #has_practexam = subj_dict.get('has_practexam') or False
                                #version = lbl_dict.get('version')

                                content_key = 'content_pa_arr' if lang == 'pa' else 'content_en_arr' if lang == 'en' else 'content_nl_arr'
                                content_arr = lbl_dict.get(content_key) or []
                                content_txt = content_arr[0] if content_arr else '-'
                                if len(content_arr) > 1:
                                    content_txt += '...'

                                is_variablenumber = lbl_dict.get('is_variablenumber') or False
                                numberofenvelops = lbl_dict.get('numberofenvelops') or 0
                                numberinenvelop = lbl_dict.get('numberinenvelop') or 0

                                total_items = tv_count if is_variablenumber else numberinenvelop * numberofenvelops

                                total_envelops = calc_number_of_envelops(
                                    sel_examyear=sel_examyear,
                                    is_variablenumber=is_variablenumber,
                                    numberinenvelop=numberinenvelop,
                                    numberofenvelops=numberofenvelops,
                                    tv_count=tv_count
                                )

                                receipt_examlabel_dictlist.append({
                                    'subj_name':  subj_name,
                                    'content_txt': content_txt,
                                    'total_items': total_items,
                                    'total_envelops': total_envelops
                                })

    return receipt_examlabel_dictlist
# - end of create_receipt_examlabel_dictlist

###########################################

