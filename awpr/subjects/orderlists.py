# PR2022-08-03
from django.contrib.auth.decorators import login_required
from django.db import connection

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View

#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import activate, pgettext_lazy, gettext_lazy as _

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
                envelopitem_pk = upload_dict.get('envelopitem_pk')
                is_create = mode == 'create'
                is_delete = mode == 'delete'

                updated_rows = []
                append_dict = {}

                header_txt = _('New label item') if is_create else _('Delete label item') if is_delete else _('Change label item')

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
                        envelopitem, err_html = create_envelopitem(sel_examyear, request)
                        # this is used when msg is shown in modal envelopitem
                        #if err_html:
                        #    error_dict['nonfield'] = err_html

                        # this is used when msg is shown in modal message modal
                        if err_html:
                            messages.append({'header': str(header_txt), 'class': "border_bg_invalid", 'msg_html': err_html})
                        if envelopitem:
                            append_dict['created'] = True
                    else:

# +++  or get existing envelopitem
                        envelopitem = subj_mod.Envelopitem.objects.get_or_none(
                            id=envelopitem_pk,
                            examyear=sel_examyear
                        )
                    if logging_on:
                        logger.debug('envelopitem: ' + str(envelopitem))

                    deleted_ok = False

                    if envelopitem:
# +++ Delete envelopitem
                        if is_delete:
                            deleted_row, err_html = sch_mod.delete_instance(
                                table='envelopitem',
                                instance=envelopitem,
                                request=request,
                                this_txt=_('This label item')
                            )
                            if err_html:
                                messages.append(
                                    {'header': str(header_txt), 'class': "border_bg_invalid", 'msg_html': err_html})
                            else:
        # - set envelopitem = None to skip create_envelopitem_rows when deleting successfull
                                envelopitem = None
        # - add deleted_row to updated_rows
                                updated_rows.append(deleted_row)

                                if logging_on:
                                    logger.debug('    delete order ok')
                                    logger.debug('    deleted_row: ' + str(deleted_row))

# +++  Update envelopitem, also when it is created
                        else:
                            update_envelopitem_instance(
                                instance=envelopitem,
                                upload_dict=upload_dict,
                                error_dict=error_dict,
                                request=request
                            )

# - create updated_row, also when deleting failed, not when deleted ok, in that case deleted_row is already added to updated_rows
# - error_dict is added to updated_row, messages are added to update_wrap['messages']
                    if envelopitem:
                        if error_dict:
                            append_dict['error'] = error_dict

                        updated_rows = create_envelopitem_rows(
                            sel_examyear=sel_examyear,
                            append_dict=append_dict,
                            envelopitem_pk=envelopitem.pk)

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
    logging_on = s.LOGGING_ON
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

            this_text = str(_('This label item'))
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
            upload_dict: {
                'table': 'enveloplabel', 'mode': 'create', 
                'name': 'naam5', 'numberfixed': '4', 'numberperexam': '5', 
                'labelitem_list': [
                {'envelopitem_pk': 3, 'labelitem_pk': None, 'labelitem_sequence': None, 'selected': True}, 
                {'envelopitem_pk': 5, 'labelitem_pk': None, 'labelitem_sequence': None, 'selected': True},
                {'envelopitem_pk': 6, 'labelitem_pk': None, 'labelitem_sequence': None, 'selected': True},
                {'envelopitem_pk': 1, 'labelitem_pk': None, 'labelitem_sequence': None, 'selected': False}, 
                {'envelopitem_pk': 7, 'labelitem_pk': None, 'labelitem_sequence': None, 'selected': False}, 
                {'envelopitem_pk': 9, 'labelitem_pk': None, 'labelitem_sequence': None, 'selected': False}]}

            """

            if has_permit:

# - reset language
                user_lang = request.user.lang if request.user.lang else c.LANG_DEFAULT
                activate(user_lang)

# - get variables
                enveloplabel_pk = upload_dict.get('enveloplabel_pk')
                name = upload_dict.get('name')

                is_create = mode == 'create'
                is_delete = mode == 'delete'

                updated_rows = []
                append_dict = {}

                header_txt = _('New label item') if is_create else _('Delete label item') if is_delete else _('Change label item')

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

# +++  or get existing envelopitem
                        enveloplabel_instance = subj_mod.Enveloplabel.objects.get_or_none(
                            id=enveloplabel_pk,
                            examyear=sel_examyear
                        )
                    if logging_on:
                        logger.debug('enveloplabel_instance: ' + str(enveloplabel_instance))

                    if enveloplabel_instance:
# +++ Delete enveloplabel
                        if is_delete:
                            deleted_row, err_html = sch_mod.delete_instance(
                                table='enveloplabel',
                                instance=enveloplabel_instance,
                                request=request,
                                this_txt=_('This label')
                            )
                            if err_html:
                                messages.append(
                                    {'header': str(header_txt), 'class': "border_bg_invalid", 'msg_html': err_html})
                            else:
        # - set envelopitem = None to skip create_envelopitem_rows when deleting successfull
                                envelopitem = None
        # - add deleted_row to updated_rows
                                updated_rows.append(deleted_row)

                                if logging_on:
                                    logger.debug('    delete order ok')
                                    logger.debug('    deleted_row: ' + str(deleted_row))

# +++  Update envelopitem, also when it is created
                        else:
                            update_enveloplabel_instance(
                                examyear=sel_examyear,
                                enveloplabel_instance=enveloplabel_instance,
                                upload_dict=upload_dict,
                                request=request
                            )

# - create updated_row, also when deleting failed, not when deleted ok, in that case deleted_row is already added to updated_rows
# - error_dict is added to updated_row, messages are added to update_wrap['messages']
                    if enveloplabel_instance:
                        if error_dict:
                            append_dict['error'] = error_dict

                        updated_rows = create_enveloplabel_rows(
                            sel_examyear=sel_examyear,
                            append_dict=append_dict,
                            enveloplabel_pk=enveloplabel_instance.pk)

                update_wrap['updated_envelopitem_rows'] = updated_rows

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
    logging_on = s.LOGGING_ON
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

    save_changes = False

    has_error = False
    if enveloplabel_instance:

        for field, new_value in upload_dict.items():
            if field == 'name':
                err_html = av.validate_enveloplabel_name_blank_length_exists(examyear, new_value, enveloplabel_instance)
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

            elif field == 'labelitem_list':
                if new_value: #      new_value = labelitem_list
                    for labelitem in new_value:
                        envelopitem_pk = labelitem.get('envelopitem_pk')
                        labelitem_pk = labelitem.get('labelitem_pk')
                        sequence = labelitem.get('labelitem_sequence') or 0
                        is_selected = labelitem.get('selected')

                # - get labelitem
                        if labelitem_pk:
                            labelitem_instance = subj_mod.Enveloplabelitem.objects.get_or_none(pk=labelitem_pk)
                            if labelitem_instance:
                                if is_selected:
                        # check if sequence has changed, if so: update
                                    labelitem_instance_sequence = getattr(labelitem_instance, 'sequence') or 0
                                    if sequence != labelitem_instance_sequence:
                                        setattr(labelitem_instance,'sequence', sequence)
                                        labelitem_instance.save(request=request)
                                else:
                        # delete labelitem if not selected
                                    labelitem_instance.delete()

                #- add labelitem if is_selected and labelitem_pk does not exist yet
                        elif is_selected and envelopitem_pk:
                            item_instance = subj_mod.Envelopitem.objects.get_or_none(pk=envelopitem_pk)
                            if item_instance:
                                labelitem_instance = subj_mod.Enveloplabelitem(
                                    enveloplabel=enveloplabel_instance,
                                    envelopitem=item_instance,
                                    sequence=sequence
                                )
                                labelitem_instance.save(request=request)
    # --- end of for loop ---

# 5. save changes
        if save_changes:
            try:
                enveloplabel_instance.save(request=request)
            except Exception as e:
                has_error = True
                logger.error(getattr(e, 'message', str(e)))

                # &emsp; add 4 'hard' spaces
                err_html = ''.join((
                    str(_('An error occurred')), ':<br>', '&emsp;<i>', str(e), '</i><br>',
                    str(_('The changes have not been saved.'))
                ))

    return has_error
# - end of update_enveloplabel_instance


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
    CASE WHEN subj.otherlang IS NULL OR sch.otherlang IS NULL  THEN 'ne'   ELSE
    CASE WHEN POSITION(sch.otherlang IN subj.otherlang) > 0 THEN sch.otherlang ELSE 'ne' END END AS lang

    or even better with delimiters:
    CASE WHEN subj.otherlang IS NULL OR sch.otherlang IS NULL 
        THEN 
            'ne' 
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
def create_envelopbundle_rows(sel_examyear, envelopbundle_pk=None):
    # PR2022-08-06
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_envelopbundle_rows ============= ')
        logger.debug('sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))

    envelopbundle_rows = []
    try:
        if sel_examyear:
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
    try:
        if sel_examyear :
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
    logging_on = s.LOGGING_ON
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
    # PR2022-08-06

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_envelopbundlelabel_rows ============= ')
        logger.debug('sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))

    envelopbundlelabel_rows = []
    try:
        if sel_examyear:
            sql_keys = {'ey_id': sel_examyear.pk}
            sql_list = [
                "SELECT bndlbl.id, bndlbl.envelopbundle_id, bndlbl.enveloplabel_id, bndl.examyear_id AS examyear_id,",

                "bndl.name AS bndl_name,",

                "lbl.name, lbl.numberperexam, lbl.numberfixed",

                "FROM subjects_envelopbundlelabel AS bndlbl",
                "INNER JOIN subjects_envelopbundle AS bndl ON (bndl.id = bndlbl.envelopbundle_id)",
                "INNER JOIN subjects_enveloplabel AS lbl ON (lbl.id = bndlbl.enveloplabel_id)",

                "WHERE bndl.examyear_id = %(ey_id)s::INT",
                "ORDER BY bndlbl.id"
            ]
            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('sql_keys: ' + str(sql_keys))
                logger.debug('sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                envelopbundlelabel_rows = af.dictfetchall(cursor)

            if logging_on:
                logger.debug('envelopbundlelabel_rows: ' + str(envelopbundlelabel_rows))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return envelopbundlelabel_rows
# - end of create_envelopbundlelabel_rows


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
                "ORDER BY lbl.id"
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
# /////////////////////////////////////////////////////////////////

