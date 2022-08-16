# PR2022-08-03
from django.contrib.auth.decorators import login_required
from django.db import connection

from django.http import HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
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

from awpr import constants as c
from awpr import settings as s
from awpr import functions as af
from awpr import validators as av
from awpr import downloads as dl
from schools import models as sch_mod
from students import validators as stud_val
from subjects import models as subj_mod

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
class EnvelopItemUploadView(View):  # PR2020-10-01 PR2021-07-18

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
            has_permit = af.get_permit_crud_of_this_page(page_name, request)

            if logging_on:
                logger.debug('has_permit: ' + str(has_permit))
                logger.debug('upload_dict: ' + str(upload_dict))
            """
            upload_dict: {'table': 'envelopitem', 'mode': 'create', 'content_nl': 'aa', 'content_color': 'blue'}
            upload_dict: {'table': 'envelopitem', 'mode': 'delete', 'envelopitem_pk': 2, 'map_id': 'envelopitem_2'}
            """

            if has_permit:

# - reset language
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

# - get variables
                envelopitem_pk = upload_dict.get('parent_pk')
                is_create = mode == 'create'
                is_delete = mode == 'delete'

                updated_rows = []
                append_dict = {}

                header_txt = _('Create label text') if is_create else _('Delete label text') if is_delete else _('Edit label text')

# ----- get selected examyear from usersettings
                sel_examyear, may_edit, error_list = dl.get_selected_examyear_from_usersetting(request, True)  # allow_not_published = True
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
                            id=envelopitem_pk,
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
    # --- update existing and new instance PR2022-08-04

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_envelopitem_instance -------')
        logger.debug('    upload_dict: ' + str(upload_dict))
        logger.debug('    instance:    ' + str(instance))


    fields = ('content_nl', 'content_en', 'content_pa', 'content_color', 'instruction_nl',
              'instruction_en', 'instruction_pa', 'instruction_color')

    has_error = False
    if instance:
        save_changes = False

        for field, new_value in upload_dict.items():
            if field in fields:

                if new_value:
                    if 'color' not in field:
                        max_len = c.MAX_LENGTH_FIRSTLASTNAME if 'instr' in field else c.MAX_LENGTH_NAME
                        # - validate length of new_value
                        msg_err = stud_val.validate_length(_('The text'), new_value, max_len, True)  # blank_allowed = True
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
class EnvelopLabelUploadView(View):  # PR2022-08-08

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
            has_permit = af.get_permit_crud_of_this_page(page_name, request)

            if logging_on:
                logger.debug('has_permit: ' + str(has_permit))
                logger.debug('upload_dict: ' + str(upload_dict))
            """
            upload_dict: {'table': 'enveloplabel', 'mode': 'delete', 'enveloplabel_pk': 7}
            """

            if has_permit:

# - reset language
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

# - get variables
                enveloplabel_pk = upload_dict.get('parent_pk')
                name = upload_dict.get('name')

                is_create = mode == 'create'
                is_delete = mode == 'delete'

                updated_rows = []
                append_dict = {}

                header_txt = _('Create label') if is_create else _('Delete label') if is_delete else _('Edit label')

# ----- get selected examyear from usersettings
                sel_examyear, may_edit, error_list = dl.get_selected_examyear_from_usersetting(request, True)  # allow_not_published = True
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
    # --- update existing and new instance PR2022-08-08

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- update_enveloplabel_instance -------')
        logger.debug('    enveloplabel_instance: ' + str(enveloplabel_instance))
        logger.debug('    upload_dict:    ' + str(upload_dict))
    """
    upload_dict: {
        'table': 'enveloplabel', 'mode': 'update',
        'parent_pk': 13, 'name': 'yyy', 
        'numberfixed': 77, 'numberperexam': None, 
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

            elif field in ('numberfixed', 'numberperexam'):
                if not new_value:
                    setattr(enveloplabel_instance, field, None)
                    save_changes = True
                elif isinstance(new_value, int):
                    saved_value = getattr(enveloplabel_instance, field)
                    if new_value != saved_value:
                        setattr(enveloplabel_instance, field, new_value)
                        # set other field None when new_value has value
                        other_field = 'numberperexam' if field == 'numberfixed' else 'numberfixed'
                        setattr(enveloplabel_instance, other_field, None)
                        save_changes = True

            elif field == 'uniontable':
                if new_value: # new_value = labelitem_list
                    if logging_on:
                        logger.debug('    new_value: ' + str(new_value))

                    for labelitem in new_value:
                        envelopitem_pk = labelitem.get('picklist_pk')
                        labelitem_pk = labelitem.get('uniontable_pk')
                        sequence = labelitem.get('sequence') or 0
                        is_selected = labelitem.get('selected')
                        if logging_on:
                            logger.debug('    envelopitem_pk: ' + str(envelopitem_pk))
                            logger.debug('    labelitem_pk: ' + str(labelitem_pk))
                            logger.debug('    is_selected: ' + str(is_selected))

                # - get labelitem
                        if labelitem_pk:
                            labelitem_instance = subj_mod.Enveloplabelitem.objects.get_or_none(pk=labelitem_pk)
                            if logging_on:
                                logger.debug('    get labelitem: ' + str(labelitem_instance))
                            if labelitem_instance:
                                if is_selected:
                        # check if sequence has changed, if so: update
                                    labelitem_instance_sequence = getattr(labelitem_instance, 'sequence') or 0
                                    if sequence != labelitem_instance_sequence:
                                        setattr(labelitem_instance,'sequence', sequence)
                                        labelitem_instance.save(request=request)
                                        if logging_on:
                                            logger.debug('    update labelitem_instance: ' + str(labelitem_instance))
                                else:
                        # delete labelitem if not selected
                                    if logging_on:
                                        logger.debug('    delete labelitem_instance: ' + str(labelitem_instance))
                                    labelitem_instance.delete()

                #- add labelitem if is_selected and labelitem_pk does not exist yet
                        elif is_selected and envelopitem_pk:
                            item_instance = subj_mod.Envelopitem.objects.get_or_none(pk=envelopitem_pk)
                            if logging_on:
                                logger.debug('    new item_instance: ' + str(item_instance))
                            if item_instance:
                                # check if item already exists, to prevent doubles
                                exists = subj_mod.Enveloplabelitem.objects.filter(
                                    enveloplabel=enveloplabel_instance,
                                    envelopitem=item_instance
                                ).exists()
                                if logging_on:
                                    logger.debug('    exists: ' + str(exists))
                                if not exists:
                                    labelitem_instance = subj_mod.Enveloplabelitem(
                                        enveloplabel=enveloplabel_instance,
                                        envelopitem=item_instance,
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
class EnvelopBundleUploadView(View):  # PR2022-08-11

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
            has_permit = af.get_permit_crud_of_this_page(page_name, request)

            if logging_on:
                logger.debug('has_permit: ' + str(has_permit))
                logger.debug('upload_dict: ' + str(upload_dict))
            """
            upload_dict: {'table': 'envelopbundle', 'mode': 'update', 'parent_pk': 1, 'parent_name': 'ww', 
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
                envelopbundle_pk = upload_dict.get('parent_pk')
                name = upload_dict.get('name')

                is_create = mode == 'create'
                is_delete = mode == 'delete'

                updated_rows = []
                append_dict = {}

                header_txt = _('New label bundle') if is_create else _('Delete label bundle') if is_delete else _('Edit label bundle')

# ----- get selected examyear from usersettings
                sel_examyear, may_edit, error_list = dl.get_selected_examyear_from_usersetting(request, True)  # allow_not_published = True
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
                """
                'uniontable': [ {'picklist_pk': 3, 'uniontable_pk': None, 'selected': True} ]
                """
                if new_value: #      new_value = uniontable
                    for item in new_value:
                        enveloplabel_pk = item.get('picklist_pk')
                        bundlelabel_pk = item.get('uniontable_pk')
                        is_selected = item.get('selected')

                # - delete bundlelabel, if it exists and is_selected = False
                        if bundlelabel_pk:
                            if not is_selected:
                                bundlelabel_instance = subj_mod.Envelopbundlelabel.objects.get_or_none(pk=bundlelabel_pk)
                                if bundlelabel_instance:
                                    bundlelabel_instance.delete()

                # - create bundlelabel if is_selected and bundlelabel_pk does not exist yet
                        elif is_selected and enveloplabel_pk:
                            # lookup label_instance
                            label_instance = subj_mod.Enveloplabel.objects.get_or_none(
                                pk=enveloplabel_pk
                            )
                            if label_instance:
                                bundlelabel_instance = subj_mod.Envelopbundlelabel(
                                    envelopbundle=envelopbundle_instance,
                                    enveloplabel=label_instance
                                )
                                bundlelabel_instance.save(request=request)
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



# /////////////////////////////////////////////////////////////////
def create_orderlist_rows(request, sel_examyear):
    # --- create rows of all schools with published subjects PR2021-08-18
    # PR2022-02-15 filter also on student.tobedeleted=False
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== students.view create_orderlist_rows ============= ')
        logger.debug('sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))

    # create list of schools of this examyear (CUR and SXM), only where defaultrole = school
    # for sxm: only sxm schools
    # with left join of studentsubjects with deleted=False, group by school_id with count(*)

    # logger.debug('sel_examyear_pk: ' + str(sel_examyear_pk))
    # logger.debug('sel_schoolbase_pk: ' + str(sel_schoolbase_pk))
    # logger.debug('sel_depbase_pk: ' + str(sel_depbase_pk))

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

#/////////////////////////////////////////////////////////////
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
                "lbl.name, lbl.numberperexam, lbl.numberfixed,",
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
    # PR2022-08-03
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_envelopitem_rows ============= ')
        logger.debug('sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))


    envelopitem_rows = []
    try:
        if sel_examyear :
            sql_keys = {'ey_id': sel_examyear.pk}
            sql_list = ["SELECT envit.id, CONCAT('envelopitem_', envit.id::TEXT) AS mapid,",

                        "envit.base_id, envit.examyear_id,",
                        "envit.content_nl, envit.content_en, envit.content_pa,",
                        "envit.instruction_nl, envit.instruction_en, envit.instruction_pa,",
                        "envit.content_color, envit.instruction_color,",
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
                "SELECT bndllbl.id, bndllbl.envelopbundle_id, bndllbl.enveloplabel_id,",
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
                "lbl.examyear_id AS examyear_id, lbl.name AS lbl_name, lbl.numberperexam, lbl.numberfixed,",

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


def get_schemeitem_info_per_dep_lvl(sel_examyear):
    # PR2022-08-12
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


def create_printlabel_rows(sel_examyear, exam_pk=None):
    # PR2022-08-12

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_printlabel_rows ============= ')
        logger.debug('sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))
        logger.debug('exam_pk: ' + str(exam_pk) + ' ' + str(type(exam_pk)))

    printlabel_rows = []
    if sel_examyear :
        try:
            sql_keys = {'ey_id': sel_examyear.pk}

            sub_list = [
                "SELECT lblitm.enveloplabel_id,",
                "ARRAY_AGG(itm.content_nl) AS content_nl_arr,",
                "ARRAY_AGG(itm.content_en) AS content_en_arr,",
                "ARRAY_AGG(itm.content_pa) AS content_pa_arr,",
                "ARRAY_AGG(itm.instruction_nl) AS instruction_nl_arr,",
                "ARRAY_AGG(itm.instruction_en) AS instruction_en_arr,",
                "ARRAY_AGG(itm.instruction_pa) AS instruction_pa_arr,",
                "ARRAY_AGG(itm.content_color) AS content_color_arr,",
                "ARRAY_AGG(itm.instruction_color) AS instruction_color_arr,",
                "ARRAY_AGG(lblitm.sequence) AS sequence_arr",

                "FROM subjects_enveloplabelitem AS lblitm",
                "INNER JOIN subjects_envelopitem AS itm ON (itm.id = lblitm.envelopitem_id)",
                "WHERE itm.examyear_id = %(ey_id)s::INT",
                "GROUP BY lblitm.enveloplabel_id"
            ]
            sub_sql = ' '.join(sub_list)

            sql_list = ["WITH items AS (" + sub_sql + ")",
                "SELECT exam.id as exam_id,",
                "exam.department_id AS dep_id,"
                "exam.level_id AS lvl_id,"
                "exam.subject_id AS subj_id,"
                "exam.examperiod,"
                "exam.datum, exam.begintijd, exam.eindtijd,"

                "bnd.name AS bnd_name,",
                "lbl.name AS lbl_name, lbl.numberperexam, lbl.numberfixed,",
                "items.content_nl_arr, items.content_en_arr, items.content_pa_arr,",
                "items.instruction_nl_arr, items.instruction_en_arr, items.instruction_pa_arr,",
                "items.content_color_arr, items.instruction_color_arr, items.sequence_arr",
                
                "FROM subjects_exam AS exam",
                "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = exam.department_id)",

                "INNER JOIN subjects_envelopbundle AS bnd ON (bnd.id = exam.envelopbundle_id)",
                "INNER JOIN subjects_envelopbundlelabel AS bndlbl ON (bndlbl.envelopbundle_id = bnd.id)",
                "INNER JOIN subjects_enveloplabel AS lbl ON (lbl.id = bndlbl.enveloplabel_id)",
                "INNER JOIN items ON (items.enveloplabel_id = lbl.id)",

                "WHERE dep.examyear_id = %(ey_id)s::INT",
            ]
            enveloplabel_pk = None
            if exam_pk:
                sql_keys['exam_pk'] = exam_pk
                sql_list.append('AND exam.id = %(exam_pk)s::INT')

            else:
                sql_list.append('ORDER BY lbl.id')

            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('sql_keys: ' + str(sql_keys) )
                logger.debug('sql: ' + str(sql) )

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                printlabel_rows = af.dictfetchall(cursor)

            if logging_on:
                if printlabel_rows:
                    for row in printlabel_rows:
                        logger.debug(' >>> row: ' + str(row) )

            """
            printlabel_rows = [
                {'exam_id': 26, 'dep_id': 4, 'lvl_id': 6, 'subj_id': 129, 'examperiod': 1, 
                'bnd_name': 'ww7', 'lbl_name': 'Naam nw', 'name': 'Naam nw', 
                'numberperexam': None, 'numberfixed': 4, 
                'content_nl_arr': ['GROEN', 'ORANJE', 'ORANJE', 'PAARS'], 
                'content_en_arr': [None, None, None, None], 
                'content_pa_arr': ['aa', None, None, None], 
                'instruction_nl_arr': ['GEEL', None, None, 'PAARS'], 
                'instruction_en_arr': ['ff', None, None, None], 
                'instruction_pa_arr': ['vv', None, None, None], 
                'content_color_arr': ['green', 'purple', 'purple', 'purple'], 
                'instruction_color_arr': ['green', None, None, 'purple']}
            """
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
    return printlabel_rows
# --- end of create_enveloplabel_rows



# /////////////////////////////////////////////////////////////////


@method_decorator([login_required], name='dispatch')
class EnvelopPrintView(View):  # PR2022=-8=10

    def get(self, request, lst):
        logging_on = s.LOGGING_ON
        if logging_on:
            logger.debug(' ============= EnvelopPrintView ============= ')
            if logging_on:
                logger.debug('     lst: ' + str(lst))

    # paper size of labels is: 'Statement', Width: 21.59 cm Height: 13.97 cm or 8.5 inch x 5.5 inch or 612 x 396 points
    # pagesize A4  = (595.27, 841.89) points, 1 point = 1/72 inch

        # function creates, Ex3 pdf file based on settings in lst and usersetting

        response = None

        if request.user and request.user.country and request.user.schoolbase and lst:
            upload_dict = json.loads(lst)

            req_user = request.user

# - reset language
            user_lang = req_user.lang if req_user.lang else c.LANG_DEFAULT
            activate(user_lang)

# - get selected examyear, school and department from usersettings
            sel_examyear, sel_school, sel_department, may_edit, msg_list = \
                dl.get_selected_ey_school_dep_from_usersetting(request)

# - get selected examperiod from usersettings
            sel_examperiod, sel_examtype_NIU, sel_subject_pk_NIU = dl.get_selected_experiod_extype_subject_from_usersetting(request)

            if logging_on:
                logger.debug('sel_examperiod: ' + str(sel_examperiod))
                logger.debug('sel_school: ' + str(sel_school))
                logger.debug('sel_department: ' + str(sel_department))

            if sel_examperiod and sel_school and sel_department:
                exam_pk =  upload_dict.get('exam_pk')
                lvlbase_pk_list = upload_dict.get('lvlbase_pk_list', [])
                subject_list = upload_dict.get('subject_list', [])

# - save sel_layout and lvlbase_pk_list and in usersetting
                setting_dict = {'subject_list': subject_list, 'lvlbase_pk_list': lvlbase_pk_list}
                #acc_view.set_usersetting_dict(c.KEY_EX3, setting_dict, request)

                try:
                    filepath = s.STATICFILES_FONTS_DIR + 'Arial.ttf'
                    ttfFile = TTFont('Arial', filepath)
                    pdfmetrics.registerFont(ttfFile)
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

                try:
                    filepath = s.STATICFILES_FONTS_DIR + 'Arial_Black.ttf'
                    logger.debug('filepath: ' + str(filepath))
                    ttfFile = TTFont('Arial_Black', filepath)
                    pdfmetrics.registerFont(ttfFile)
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

                try:
                    filepath = s.STATICFILES_FONTS_DIR + 'Calibri.ttf'
                    ttfFile = TTFont('Calibri', filepath)
                    pdfmetrics.registerFont(ttfFile)
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

                try:
                    filepath = s.STATICFILES_FONTS_DIR + 'Calibri_Bold.ttf'
                    ttfFile = TTFont('Calibri_Bold', filepath)
                    pdfmetrics.registerFont(ttfFile)
                except Exception as e:
                    logger.error(getattr(e, 'message', str(e)))

                # https://stackoverflow.com/questions/43373006/django-reportlab-save-generated-pdf-directly-to-filefield-in-aws-s3

                # PR2021-04-28 from https://docs.python.org/3/library/tempfile.html
                #temp_file = tempfile.TemporaryFile()
                # canvas = Canvas(temp_file)

                buffer = io.BytesIO()
                canvas = Canvas(buffer)

                # PR2022-05-05 debug Oscap Panneflek Vpco lines not printing on Ex3
                # turn off setLineWidth (0)
                # canvas.setLineWidth(0)

                # paper size of labels is: 'Statement', Width: 21.59 cm Height: 13.97 cm or 8.5 inch x 5.5 inch or 612 x 396 points
                canvas.setPageSize((612, 396))  # some page size, given as a tuple in points pdf.setPageSize((width,height)

                max_rows = 30  # was:  24
                line_height = 6.73 * mm  # was:  8 * mm

                schemeitem_dict = get_schemeitem_info_per_dep_lvl(sel_examyear)
                #if logging_on:
                #    logger.debug('schemeitem_dict: ' + str(schemeitem_dict))

                printlabel_list = create_printlabel_rows(
                    sel_examyear=sel_examyear,
                    exam_pk=exam_pk
                )
                for label_dict in printlabel_list:
                    if logging_on:
                        logger.debug(' --- label_dict: ' + str(label_dict))
                    """
                    label_dict = 
                        {'exam_id': 26, 'dep_id': 4, 'lvl_id': 6, 'subj_id': 129, 'examperiod': 1, 
                        'bnd_name': 'ww7', 'lbl_name': 'Naam nw', 'name': 'Naam nw', 
                        'numberperexam': None, 'numberfixed': 4, 
                        'content_nl_arr': ['GROEN', 'ORANJE', 'ORANJE', 'PAARS'], 
                        'content_en_arr': [None, None, None, None], 
                        'content_pa_arr': ['aa', None, None, None], 
                        'instruction_nl_arr': ['GEEL', None, None, 'PAARS'], 
                        'instruction_en_arr': ['ff', None, None, None], 
                        'instruction_pa_arr': ['vv', None, None, None], 
                        'content_color_arr': ['green', 'purple', 'purple', 'purple'], 
                        'instruction_color_arr': ['green', None, None, 'purple']}
                        
                        label_dict: {
                            'exam_id': 26, 'dep_id': 4, 'lvl_id': 6, 'subj_id': 129, 'examperiod': 1, 
                            'datum': None, 'begintijd': None, 'eindtijd': None, 
                            'bnd_name': 'ww7', 'lbl_name': 'naam5', 
                            'numberperexam': 15, 'numberfixed': None, 
                            'content_nl_arr': ['Correctievoorschrift', 'GROEN', 'PAARS'], 
                            'content_en_arr': [None, None, None], 
                            'content_pa_arr': [None, 'aa', None], 
                            'instruction_nl_arr': ['EERST DE NAAM, DATUM EN TIJDSDUUR VOORLEZEN, DAARNA OPENEN!', 'GEEL', 'PAARS'], 
                            'instruction_en_arr': [None, 'ff', None], 
                            'instruction_pa_arr': [None, 'vv', None], 
                            'content_color_arr': ['blue', 'green', 'purple'], 
                            'instruction_color_arr': ['red', 'green', 'purple'], 
                            'sequence_arr': [0, 0, 0]}    
            
                    """

                    if label_dict:
                     # get dep abbrev and lvl_abbrev, sub_name
                        dep_pk = label_dict.get('dep_id')
                        lvl_pk = label_dict.get('lvl_id') or 0
                        subj_pk = label_dict.get('subj_id')
                        examperiod = label_dict.get('examperiod')
                        examdate = label_dict.get('datum')
                        starttime = label_dict.get('begintijd')
                        endtime = label_dict.get('eindtijd')

                        numberperexam = label_dict.get('numberperexam')
                        numberfixed = label_dict.get('eindtijd')

                        bnd_lbl_name = ' '.join((label_dict.get('bnd_name') or '-', label_dict.get('lbl_name') or '-'))

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
                                    otherlang_arr = subj_dict.get('otherlang')

                        dep_lvl_abbrev = dep_abbrev if dep_abbrev else '---'
                        if lvl_abbrev:
                            dep_lvl_abbrev += ' ' + lvl_abbrev

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

    # - loop through languages of this subject
                        lang_list = ['nl']
                        if otherlang_arr:
                            for lang in otherlang_arr:
                                logger.debug('     lang: ' + str(lang))
                                if lang not in lang_list:
                                    lang_list.append(lang)
                                    logger.debug('     lang_list: ' + str(lang_list))

                        school_name = '---'

                        for lang in lang_list:

                            if lang == 'pa' and subj_name_pa:
                                subj_name = subj_name_pa
                            elif lang == 'en' and subj_name_en:
                                subj_name = subj_name_en
                            elif subj_name_nl:
                                subj_name = subj_name_nl
                            else:
                                subj_name = '---'

                            content_key = '_'.join(('content', 'pa' if lang == 'pa' else 'en' if lang == 'en' else 'nl', 'arr'))
                            instruction_key = '_'.join(('instruction', 'pa' if lang == 'pa' else 'en' if lang == 'en' else 'nl', 'arr'))
                            content_arr = label_dict.get(content_key) or []
                            instruction_arr = label_dict.get(instruction_key) or []
                            content_color_arr = label_dict.get('content_color_arr') or []
                            instruction_color_arr = label_dict.get('instruction_color_arr') or []



                            if logging_on:
                                logger.debug(' ... lang: ' + str(lang))
                            row_count = 1 #len(student_list)
                            pages_not_rounded = row_count / max_rows
                            pages_integer = int(pages_not_rounded)
                            pages_roundup = pages_integer + 1 if (pages_not_rounded - pages_integer) else pages_integer
                            pages_roundup = 1
                            for page_index in range(0, pages_roundup):  # range(start_value, end_value, step), end_value is not included!

                                draw_label(canvas, sel_examyear, examperiod, dep_lvl_abbrev, dep_lvl_color,
                                           subj_name, school_name,
                                           has_practexam, examdate, starttime, endtime, numberperexam, numberfixed, lang, bnd_lbl_name,
                                           content_arr, instruction_arr, content_color_arr, instruction_color_arr
                                           )
                                canvas.showPage()

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

                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="Ex3_voorblad.pdf"'
                #response['Content-Disposition'] = 'attachment; filename="testpdf.pdf"'

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
                    "AND NOT grd.tobedeleted AND NOT studsubj.tobedeleted",
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
               examdate, starttime, endtime, numberperexam, numberfixed, lang, bnd_lbl_name,
                content_arr, instruction_arr, content_color_arr, instruction_color_arr
               ):
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- draw_label -----')


# - set the corners of the rectangle
    top, right, bottom, left = 287 * mm, 200 * mm, 12 * mm, 10 * mm
    top, right, bottom, left = 396, 612, 12 * mm, 10 * mm
    #width = right - left  # 190 mm
    #height = top - bottom  # 275 mm
    border = [top, right, bottom, left]
    coord = [left, top]

    pos_x = 0.625 * inch
    pos_x2 = 2.625 * inch  #   pos_x2 = 2.375 * inch
    pos_x3 = 2.875 * inch  #  pos_x3 = 2.625 * inch
    pos_x4 = 7.875 * inch

    label_txt = c.LABEL_TEXT.get(lang)

    # canvas.drawImage(image, x, y, width, height, mask=None)
    file_name = s.STATICFILES_IMG_DIR + "ETElogo2022-08-15.png" # size 1750 - 1000
    canvas.drawInlineImage(file_name, pos_x, 4.35 * inch, 1.75 * inch, 1 * inch)

# draw EXAMEN
    pos_y = 4.75 * inch
    line_height = 0.25 * inch

    # leading: This is the spacing between adjacent lines of text; a good rule of thumb is to make this 20% larger than the point size.
    canvas.setFont('Arial_Black', 20, leading=None)
    caption = ' '.join(( label_txt.get('exam'), str(examyear)))
    caption_width = stringWidth(caption, 'Arial_Black', 20)

    canvas.setFillColor(colors.HexColor("#000000"))
    canvas.drawRightString(pos_x4 , pos_y, caption)

    canvas.setFillColor(colors.HexColor("#ff0000"))
    cse_cspe = 'CSPE' if has_practexam else 'CSE'
    canvas.drawRightString(pos_x4 - caption_width - 0.125 * inch, pos_y, cse_cspe)

    pos_y -= line_height * 1.5

    hex_color = c.LABEL_COLOR.get(dep_lvl_color)
    canvas.setFillColor(colors.HexColor(hex_color))
    canvas.drawRightString(pos_x4, pos_y, dep_lvl_abbrev)

    pos_y = 3.75 * inch

    bottom = pos_y - 0.125 * inch
    height = 0.5 * inch
    canvas.setFillColor(colors.HexColor("#bfbfbf"))  # grey background in label  RGB 181, 181, 191
    canvas.rect(0.5 * inch, bottom, 7.5 * inch, height, stroke=0, fill=1)  # canvas.rect(left, bottom, page_width, height)

    caption = ' '.join((label_txt.get('ep'), str(examperiod)))
    canvas.setFont('Calibri_Bold', 20, leading=None)
    canvas.setFillColor(colors.HexColor("#000000"))
    canvas.drawString(pos_x, pos_y, caption)
    canvas.drawRightString(pos_x4, pos_y, subj_name)

    examdate_str = format_examdate_from_dte(examdate, label_txt, lang)

    pos_y -= 0.5 * inch
    caption = label_txt.get('date') or '---'
    canvas.setFont('Arial', 14, leading=None)
    canvas.drawString(pos_x, pos_y, caption)
    canvas.drawString(pos_x2, pos_y, ':')
    canvas.drawString(pos_x3, pos_y, examdate_str)

    examtime_formatted = format_examtime_from_dte(starttime, endtime, label_txt)
    pos_y -= line_height
    caption = label_txt.get('time') or '---'
    canvas.drawString(pos_x, pos_y, caption)
    canvas.drawString(pos_x2, pos_y, ':')
    canvas.drawString(pos_x3, pos_y, examtime_formatted)

    pos_y -= line_height

    name_txt = label_txt.get('school_name') or '---'
    caption = label_txt.get('school') or '---'
    canvas.drawString(pos_x, pos_y, caption)
    canvas.drawString(pos_x2, pos_y, ':')
    canvas.setFont('Arial_Black', 14, leading=None)
    canvas.drawString(pos_x3, pos_y, name_txt)
    canvas.setFont('Arial', 14, leading=None)

    pos_y -= line_height
    caption = label_txt.get('numex') or '---'
    value = str(numberperexam) if numberperexam else ''
    canvas.drawString(pos_x, pos_y, caption)
    canvas.drawString(pos_x2, pos_y, ':')
    canvas.drawString(pos_x3, pos_y, value)

    pos_y -= line_height
    caption = label_txt.get('numenv') or '---'
    value = str(numberfixed) if numberfixed else ''
    canvas.drawString(pos_x, pos_y, caption)
    canvas.drawString(pos_x2, pos_y, ':')
    canvas.drawString(pos_x3, pos_y, value)

    pos_y -= line_height * 1.5
    canvas.drawString(pos_x, pos_y, 'INHOUD')
    canvas.drawString(pos_x2, pos_y, ':')

    if content_arr:
        row_count = 0
        for i, content in enumerate(content_arr):
            if content:
                conten_color = content_color_arr[i]
                hex_color = c.LABEL_COLOR.get(conten_color)
                canvas.setFillColor(colors.HexColor(hex_color))
                canvas.drawString(pos_x3, pos_y - line_height * row_count, content or '')
                row_count += 1

    row_count = 0
    if instruction_arr:
        #count rows to be pronted
        for instruction in instruction_arr:
            if instruction:
                row_count += 1
# calculate heigth of bar

    canvas.setFillColor(colors.HexColor("#bfbfbf"))  # grey background in label  RGB 181, 181, 191
    bar_bottom = 0.375 * inch
    bar_height = 0.375 * inch + (row_count - 1 ) * line_height * .75 if row_count > 1 else 0.375 * inch
    bar_top = bar_bottom + bar_height
    canvas.rect(0.5 * inch, bar_bottom, 7.5 * inch, bar_height, stroke=0, fill=1)  # canvas.rect(left, bottom, page_width, height)
    canvas.setFillColor(colors.HexColor("#000000"))


    if instruction_arr:
        row_count = 0
        pos_y = bar_top - line_height
        canvas.setFont('Calibri', 12, leading=None)
        for i, instruction in enumerate(instruction_arr):
            if instruction:
                instruction_color = instruction_color_arr[i]
                hex_color = c.LABEL_COLOR.get(instruction_color)
                canvas.setFillColor(colors.HexColor(hex_color))
                canvas.drawCentredString(4.25 * inch, pos_y - line_height * .75 * row_count, instruction or '')
                row_count += 1

    #pos_y = 0.6125 * inch
    #canvas.setFillColor(colors.HexColor("#ff0000"))
    #canvas.setFont('Calibri', 12, leading=None)
    #anvas.drawCentredString(4.25 * inch, pos_y, 'E MODELO DI KOREKSHON DI E ÈKSAMEN AKÍ TA KONFIDENSIAL')

    #pos_y -= line_height * .75
    #canvas.drawCentredString(4.25 * inch, pos_y, 'I E ÈKSAMEN TA KEDA KORIGÍ DOR DI E KOMISHON DI ÈKSAMEN DI ESTADO')

    canvas.setFillColor(colors.HexColor("#000000"))
    canvas.setFont('Calibri', 8, leading=None)
    canvas.drawRightString(pos_x4, bar_bottom - 0.125 * inch, bnd_lbl_name)
    canvas.setFillColor(colors.HexColor("#000000"))

    canvas.setFont('Calibri', 12, leading=None)


# - end of draw_label


def draw_red_cross(canvas, x, y):
    # draw red cross, for outlining while designing
    canvas.setStrokeColorRGB(1, 0, 0)
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

def format_examdate_from_dte(dte, label_txt, lang):  # PR2022-08-13

    examdate_formatted = ''
    if dte:
        try:
            year_str = str(dte.year)
            day_str = str(dte.day)

            month_str = c.LABEL_MONTHS[lang][dte.month]

            weekday_int = int(dte.strftime("%w"))
            if not weekday_int:
                weekday_int = 7
            weekday_str = c.LABEL_WEEKDAYS[lang][weekday_int]

            # Djaluna, 17 di sèptèmber,
            if lang == 'pa':
                examdate_formatted = ' '.join([weekday_str, day_str, label_txt['of'], month_str, year_str])
            elif lang == 'en':
                examdate_formatted = ''.join([weekday_str, ', ',  month_str, ' ', day_str, ', ', year_str])
            else:
                examdate_formatted = ' '.join([weekday_str, day_str, month_str, year_str])
        except:
            pass

    return examdate_formatted


def format_examtime_from_dte(starttime, endtime, label_txt):  # PR2022-08-13

    examtime_formatted = ''
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

    return examtime_formatted



