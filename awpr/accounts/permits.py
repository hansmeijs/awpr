# PR2023-01-13
import json
from datetime import date, datetime, timedelta
from random import randint

from django.core.mail import send_mail
from django.db import connection
from django.db.models import Q
from django.template.loader import render_to_string
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import gettext, gettext_lazy as _
from django.utils import timezone

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from accounts import models as acc_mod

from awpr import constants as c
from awpr import settings as s
from awpr import library as awpr_lib

from schools import models as sch_mod
from subjects import models as subj_mod
from students import models as stud_mod
from subjects import views as subj_view
from students import views as stud_view
from grades import views as grade_view

import logging
logger = logging.getLogger(__name__)


def get_selected_pk_dict_of_user_instance(user_instance):
    #   PR2023-01-16 get selected_pk_dict from user_instance

    selected_pk_dict = {}
    try:
        usersetting = acc_mod.Usersetting.objects.filter(
            user=user_instance,
            key=c.KEY_SELECTED_PK
        ).order_by('pk').first()

        if usersetting and usersetting.setting:
            selected_pk_dict = json.loads(usersetting.setting)

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return selected_pk_dict


def get_sel_examyear_from_selected_pk_dict(selected_pk_dict):
    #   PR2023-01-16

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ' )
        logger.debug('  ----- get_sel_examyear_from_selected_pk_dict ----- ')

    sel_examyear_instance = None
    if selected_pk_dict:
        sel_examyear_instance = sch_mod.Examyear.objects.get_or_none(
            pk=selected_pk_dict.get(c.KEY_SEL_EXAMYEAR_PK)
        )
    return sel_examyear_instance


def get_sel_examyear_from_user_instance(user_instance):
    #   PR2023-01-13 get userallowed_instance from user_instance and selected examyear
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ---  get_sel_examyear_from_user_instance  ------- ')
        logger.debug('    user_instance: ' + str(user_instance))

    sel_examyear_instance = None

    try:
# - get selected_pk_dict
        selected_pk_dict = get_selected_pk_dict_of_user_instance(user_instance)
        if logging_on:
            logger.debug('    selected_pk_dict: ' + str(selected_pk_dict))

    # - get sel_examyear_instance
        if selected_pk_dict:
            sel_examyear_instance = sch_mod.Examyear.objects.get_or_none(
                pk=selected_pk_dict.get(c.KEY_SEL_EXAMYEAR_PK),
                country=user_instance.country
            )

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('    sel_examyear_instance: ' + str(sel_examyear_instance))
    return sel_examyear_instance


def get_sel_examyear_from_requsr(request):  # PR2023-02-07
    return get_sel_examyear_from_user_instance(request.user)


def get_sel_schoolbase_from_selected_pk_dict(selected_pk_dict):
    #   PR2023-01-16
    sel_schoolbase_instance = None
    try:
        if selected_pk_dict:
            sel_schoolbase_instance = sch_mod.Schoolbase.objects.get_or_none(
                pk=selected_pk_dict.get(c.KEY_SEL_SCHOOLBASE_PK)
            )
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return sel_schoolbase_instance


def get_sel_depbase_from_selected_pk_dict(selected_pk_dict):
    #   PR2023-01-16
    sel_depbase_instance = None
    try:
        if selected_pk_dict:
            sel_depbase_instance = sch_mod.Schoolbase.objects.get_or_none(
                pk=selected_pk_dict.get(c.KEY_SEL_DEPBASE_PK)
            )
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    return sel_depbase_instance


def get_userallowed_instance(user_instance, sel_examyear_instance):
    #   PR2023-01-13 get userallowed_instance from user_instance and selected examyear

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ---  get_userallowed_instance  ------- ')
        logger.debug('    sel_examyear_instance: ' + str(sel_examyear_instance))

    userallowed_instance = None

    try:
# - get userallowed_instance of this user_instance and this sel_examyear_instance
        if sel_examyear_instance:
            userallowed_instance = acc_mod.UserAllowed.objects.filter(
                user=user_instance,
                examyear=sel_examyear_instance,
            ).order_by('pk').first()

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('    userallowed_instance: ' + str(userallowed_instance))

    return userallowed_instance
# - end of get_userallowed_instance


def get_userallowed_instance_from_user_instance(user_instance):  #PR2023-01-25
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ---  get_userallowed_instance_from_user_instance  ------- ')
        logger.debug('    user_instance: ' + str(user_instance))

    sel_examyear_instance = get_sel_examyear_from_user_instance(user_instance)
    if logging_on:
        logger.debug('    sel_examyear_instance: ' + str(sel_examyear_instance))

    userallowed_instance = get_userallowed_instance(
        user_instance=user_instance,
        sel_examyear_instance=sel_examyear_instance
    )
    if logging_on:
        logger.debug('    userallowed_instance: ' + str(userallowed_instance))

    return userallowed_instance
# - end of get_userallowed_instance_from_user_instance


def get_userallowed_instance_from_request(request):  #PR2023-02-07
    return get_userallowed_instance_from_user_instance(request.user)
# - end of get_userallowed_instance_from_user_instance


def get_userallowed_sections_dict_from_request(request):  # PR2023-01-25
    return get_userallowed_sections_dict(
        userallowed_instance=get_userallowed_instance_from_request(request)
    )


def get_userallowed_sections_dict(userallowed_instance):  # PR2023-01-25
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('----- get_userallowed_sections_dict -----')

    userallowed_sections_dict = {}
    if userallowed_instance:
        allowed_sections_str = getattr(userallowed_instance, 'allowed_sections')
        if allowed_sections_str:
            userallowed_sections_dict = json.loads(allowed_sections_str)
    if logging_on:
        logger.debug('    userallowed_sections_dict: ' + str(userallowed_sections_dict))

    return userallowed_sections_dict


def get_userallowed_schoolbase_dict_depbases_pk_arr(userallowed_sections_dict, sel_schoolbase_pk):
    # PR2023-01-09 PR2023-01-25

    userallowed_schoolbase_dict = {}
    userallowed_depbases_pk_arr = []

    if userallowed_sections_dict:

# - check if sel_schoolbase_pk exists in allowed_sections_dict
        if sel_schoolbase_pk:
            userallowed_schoolbase_dict = userallowed_sections_dict.get(str(sel_schoolbase_pk)) or {}

# - if not, check if '-9' (all) exists in allowed_sections_dict
        if not userallowed_schoolbase_dict:
            userallowed_schoolbase_dict = userallowed_sections_dict.get('-9') or {}

# - add allowed depbase_pk_int to allowed_depbases_pk_arr
        if userallowed_schoolbase_dict:
            # PR2023-02-02 this one works:
            # was: for depbase_pk_str in userallowed_schoolbase_dict:
            #           userallowed_depbases_pk_arr.append(int(depbase_pk_str))
            userallowed_depbases_pk_arr = list(map(int, userallowed_schoolbase_dict))

    # userallowed_sections_dict:  {"28": {"1": {"-9": [116]}, "2": {"-9": [116]}, "3": {"-9": [116]}}}
    # userallowed_schoolbase_dict:       {"1": {"-9": [116]}, "2": {"-9": [116]}, "3": {"-9": [116]}}}
    # allowed_depbases_pk_arr:           [1, 2, 3] <class 'list'>

    return userallowed_schoolbase_dict, userallowed_depbases_pk_arr
# - end of get_userallowed_schoolbase_dict_depbases_pk_arr


def get_userallowed_depbase_dict_lvlbases_pk_arr(allowed_schoolbase_dict, sel_depbase_pk):
    # PR2023-01-09 PR2023-02-08
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ---  get_userallowed_depbase_dict_lvlbases_pk_arr  ------- ')
        logger.debug('    allowed_schoolbase_dict:      ' + str(allowed_schoolbase_dict))
        logger.debug('    sel_depbase_pk: ' + str(sel_depbase_pk))
        """
        userallowed_sections_dict:   {'13': {'1': {'4': [113], '-9': [122]}, '2': {'-9': [167]}}}
        userallowed_schoolbase_dict:        {'1': {'4': [113], '-9': [122]}, '2': {'-9': [167]}}
        userallowed_depbases_pk_arr:        [1, 2]
        userallowed_depbase_dict:                 {'4': [113], '-9': [122]}
        userallowed_lvlbase_pk_arr:         [4, -9]
        userallowed_cluster_pk_list: []
        """

    allowed_depbase_dict = {}
    allowed_lvlbase_pk_arr = []

# - check if sel_depbase_pk exists in allowed_schoolbase_dict
    if sel_depbase_pk and allowed_schoolbase_dict:
        # - allowed_depbase_dict, contains allowed lvlbases / subjbases of selected school
        sel_depbase_pk_str = str(sel_depbase_pk)
        allowed_depbase_dict = allowed_schoolbase_dict.get(sel_depbase_pk_str) or {}

# - if not, check if '-9' (all) exists in allowed_schoolbase_dict
    if not allowed_depbase_dict:
        sel_depbase_pk_str = '-9'
        allowed_depbase_dict = allowed_schoolbase_dict.get(sel_depbase_pk_str) or {}

# add allowed lvlbase_pk_int to allowed_lvlbase_pk_arr
    if allowed_depbase_dict:
        for lvlbase_pk_str in allowed_depbase_dict:
            allowed_lvlbase_pk_arr.append(int(lvlbase_pk_str))

    if logging_on:
        logger.debug('    allowed_depbase_dict: ' + str(allowed_depbase_dict))
        logger.debug('    allowed_lvlbase_pk_arr: ' + str(allowed_lvlbase_pk_arr))

    return allowed_depbase_dict, allowed_lvlbase_pk_arr
# - end of get_userallowed_depbase_dict_lvlbases_pk_arr


def get_userallowed_subjbase_arr(allowed_depbase_dict, sel_lvlbase_pk):
    # PR2023-02-12
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('  ---  get_userallowed_subjbase_arr  ------- ')
        logger.debug('    allowed_depbase_dict:      ' + str(allowed_depbase_dict))
        logger.debug('    sel_lvlbase_pk: ' + str(sel_lvlbase_pk))

    allowed_subjbase_pk_arr = []
    lvlbase_pk_arr = ['-9']
    if sel_lvlbase_pk:
        lvlbase_pk_arr.append(str(sel_lvlbase_pk))
    # loop through 'all' and selected lvlbase_pk
    for lvlbase_pk_str in lvlbase_pk_arr:
        if lvlbase_pk_str in allowed_depbase_dict:
            allowed_lvlbase_arr = allowed_depbase_dict.get(lvlbase_pk_str)
            if allowed_lvlbase_arr:
                for subject_pk in allowed_lvlbase_arr:
                    if subject_pk not in allowed_subjbase_pk_arr:
                        allowed_subjbase_pk_arr.append(subject_pk)

    if logging_on:
        logger.debug('    allowed_subjbase_pk_arr:      ' + str(allowed_subjbase_pk_arr))
    return allowed_subjbase_pk_arr
# - end of get_userallowed_subjbase_arr


def get_usergroup_list(userallowed_instance):  # PR2023-01-14
    usergroup_list = []
    if userallowed_instance:
        usergroups_str = getattr(userallowed_instance, 'usergroups')
        if usergroups_str:
            usergroup_list = json.loads(usergroups_str)
    return usergroup_list


def get_usergroup_list_from_user_instance(user_instance):  # PR2023-01-25
    return get_usergroup_list(
        userallowed_instance=get_userallowed_instance_from_user_instance(user_instance)
    )


def get_userallowed_cluster_pk_list(userallowed_instance):  # PR2023-01-14
    allowed_cluster_pk_list = []
    if userallowed_instance:
        allowed_clusters_str = getattr(userallowed_instance, 'allowed_clusters')
        if allowed_clusters_str:
            allowed_cluster_pk_list = json.loads(allowed_clusters_str)
    return allowed_cluster_pk_list


def get_userallowed_cluster_pk_list_from_request(request):  # PR2023-02-10
    userallowed_instance = get_userallowed_instance_from_request(request)
    allowedcluster_pk_list = get_userallowed_cluster_pk_list(userallowed_instance)
    return allowedcluster_pk_list


def get_allowedusergrouplist_allowedsectionsdict_allowedclusterlist(user_instance):
    # --- create list of  usergroups and allowed_clusters of this user  PR2021-07-26 PR2023-01-13

    #   PR2023-01-12 'usergroups' and 'allowed_clusters' are moved from table User to table UserAllowed

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- get_allowedusergrouplist_allowedsectionsdict_allowedclusterlist ----- ')
        logger.debug('    user_instance: ' + str(user_instance))

    sel_examyear_instance = get_sel_examyear_from_user_instance(user_instance)
    userallowed_instance = get_userallowed_instance(user_instance, sel_examyear_instance)

    usergroup_list = get_usergroup_list(userallowed_instance)

    userallowed_sections_dict = get_userallowed_sections_dict(userallowed_instance)

    allowed_clusters_list = get_userallowed_cluster_pk_list(userallowed_instance)

    if logging_on:
        logger.debug('    usergroup_list: ' + str(usergroup_list))
        logger.debug('    allowed_clusters_list: ' + str(allowed_clusters_list))
        logger.debug('    userallowed_sections_dict: ' + str(userallowed_sections_dict))
        logger.debug('    sel_examyear_instance: ' + str(sel_examyear_instance))

    return usergroup_list, userallowed_sections_dict, allowed_clusters_list, sel_examyear_instance
# - end of get_allowedusergrouplist_allowedsectionsdict_allowedclusterlist


# +++++++++++++++++++  get user setting +++++++++++++++++++++++


def get_usersetting_dict(key_str, request):  # PR2019-03-09 PR2021-01-25
    # function retrieves the string value of the setting row that match the filter and converts it to a dict
    # logger.debug(' ---  get_usersetting_dict  ------- ')
    #  json.dumps converts a dict in a json object
    #  json.loads retrieves a dict (or other type) from a json object

    # logger.debug('cls: ' + str(cls) + ' ' + str(type(cls)))
    setting_dict = {}
    row_setting = None
    try:
        if request.user and key_str:
            row = acc_mod.Usersetting.objects.filter(
                user=request.user,
                key=key_str
            ).order_by('pk').first()
            if row:
                row_setting = row.setting
                if row_setting:
                    setting_dict = json.loads(row_setting)
    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
        logger.error('key_str: ', str(key_str))
        logger.error('row_setting: ', str(row_setting))

    return setting_dict
# end of get_usersetting_dict


#+++++++++++ SQL CLAUSE ALLOWED++++++++++++

def get_sqlclause_allowed_schoolbase_from_request(request, schoolbase_pk=None, skip_allowed_filter=False, table=None):
    # PR2023-02-02

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('----- get_sqlclause_allowed_schoolbase_from_request ----- ')

# - get allowed_sections_dict
    userallowed_sections_dict = get_userallowed_sections_dict_from_request(request)
    if logging_on:
        logger.debug('    userallowed_sections_dict: ' + str(userallowed_sections_dict))

    return get_sqlclause_allowed_schoolbase_from_allowed_sections(
        userallowed_sections_dict=userallowed_sections_dict,
        schoolbase_pk=schoolbase_pk,
        skip_allowed_filter=skip_allowed_filter,
        table=table)
# - end of get_sqlclause_allowed_schoolbase_from_request


def get_sqlclause_allowed_schoolbase_from_allowed_sections(userallowed_sections_dict, schoolbase_pk=None, skip_allowed_filter=False, table=None):
    # PR2022-03-13 PR2022-12-04 PR2023-01-25 PR2023-01-20
    #  if schoolbase_pk has value:
    #       if userallowed_schoolbase_pk_arr exists and not skip_allowed_filter:
    #           --> filter on schoolbase_pk_pk, only when schoolbase_pk_pk in arr, otherwise: return FALSE
    #       else:
    #           --> filter on schoolbase_pk_pk
    #  if schoolbase_pk_pk is None:
    #       if arr exists and not skip_allowed_filter:
    #           --> filter on schoolbase_pk_pk's in array
    #       else:
    #           --> no filter

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- get_sqlclause_allowed_schoolbase_from_allowed_sections ----- ')
        logger.debug('    schoolbase_pk: ' + str(schoolbase_pk) + ' ' + str(type(schoolbase_pk)))
        logger.debug('    skip_allowed_filter: ' + str(skip_allowed_filter))
        logger.debug('    -----')

    filter_single_pk, filter_pk_arr, filter_none = None, None, False

    sql_clause = ''

    userallowed_schoolbase_pk_int_arr = []
    if userallowed_sections_dict:
        # PR2023-02-02 this one works:
        # was: for schoolbase_pk_str in userallowed_sections_dict:
        #           userallowed_schoolbase_pk_int_arr.append(int(schoolbase_pk_str))
        userallowed_schoolbase_pk_int_arr = list(map(int, userallowed_sections_dict))

    if logging_on:
        logger.debug('    userallowed_schoolbase_pk_int_arr: ' + str(userallowed_schoolbase_pk_int_arr))

    if schoolbase_pk and schoolbase_pk != -9:
        if not userallowed_schoolbase_pk_int_arr or \
                schoolbase_pk in userallowed_schoolbase_pk_int_arr or \
                skip_allowed_filter:
            filter_single_pk = schoolbase_pk
        else:
            filter_none = True

    elif userallowed_schoolbase_pk_int_arr and not skip_allowed_filter:
        # no filter when -9 ('all schools') in userallowed_schoolbase_pk_int_arr
        if -9 not in userallowed_schoolbase_pk_int_arr:
            if len(userallowed_schoolbase_pk_int_arr) == 1:
                filter_single_pk = userallowed_schoolbase_pk_int_arr[0]
            else:
                filter_pk_arr = userallowed_schoolbase_pk_int_arr

    if logging_on:
        logger.debug('    filter_single_pk: ' + str(filter_single_pk) + ' ' + str(type(filter_single_pk)))
        logger.debug('    filter_pk_arr: ' + str(filter_pk_arr) + ' ' + str(type(filter_pk_arr)))
        logger.debug('    filter_none: ' + str(filter_none) + ' ' + str(type(filter_none)))

    if table == 'studsubj':
        field_name = 'studsubj.schoolbase_id'
    else:
        field_name = 'school.base_id'

    if filter_single_pk:
        sql_clause = ''.join(("AND ", field_name, "=", str(filter_single_pk), "::INT"))

    elif filter_pk_arr:
        sql_clause = ''.join(("AND ", field_name, " IN (SELECT UNNEST(ARRAY", str(filter_pk_arr), "::INT[]))"))

    elif filter_none:
        sql_clause = "AND FALSE"

    if logging_on:
        logger.debug('    sql_clause: ' + str(sql_clause))
        logger.debug('--- end of get_sqlclause_allowed_schoolbase_from_allowed_sections ----- ')

    return sql_clause
# - end of get_sqlclause_allowed_schoolbase_from_allowed_sections


def get_sqlclause_allowed_depbase_from_request(request, depbase_pk=None, sel_schoolbase_pk=None, skip_allowed_filter=False):
    # PR2023-02-02
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('----- get_sqlclause_allowed_depbase_from_request ----- ')

# - get allowed_sections_dict
    userallowed_sections_dict = get_userallowed_sections_dict_from_request(request)
    if logging_on:
        logger.debug('    userallowed_sections_dict: ' + str(userallowed_sections_dict) + ' ' + str( type(userallowed_sections_dict)))

    return get_sqlclause_allowed_depbase_from_allowed_sections(
        userallowed_sections_dict=userallowed_sections_dict,
        depbase_pk=depbase_pk,
        sel_schoolbase_pk=sel_schoolbase_pk,
        skip_allowed_filter=skip_allowed_filter
    )
# - end of get_sqlclause_allowed_depbase_from_request


def get_sqlclause_allowed_depbase_from_allowed_sections(userallowed_sections_dict, depbase_pk=None, sel_schoolbase_pk=None, skip_allowed_filter=False):
    # PR2022-03-14  PR2022-12-08 PR2023-01-25

    #  if depbase_pk has value:
    #       if allowed_depbase_pk_arr exists and not skip_allowed_filter:
    #           --> filter on depbase_pk_pk, only when depbase_pk_pk in arr, otherwise: return FALSE
    #       else:
    #           --> filter on depbase_pk_pk
    #  if depbase_pk_pk is None:
    #       if arr exists and not skip_allowed_filter:
    #           --> filter on depbase_pk_pk's in array
    #       else:
    #           --> no filter

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug('----- get_sqlclause_allowed_depbase_from_allowed_sections ----- ')
        logger.debug('    depbase_pk: ' + str(depbase_pk) + ' ' + str(type(depbase_pk)))
        logger.debug('    sel_schoolbase_pk: ' + str(sel_schoolbase_pk) + ' ' + str(type(sel_schoolbase_pk)))
        logger.debug('    skip_allowed_filter: ' + str(skip_allowed_filter))

    filter_single_pk, filter_pk_arr, filter_none = None, None, False

    sql_key_dict = {}
    sql_clause = ''

# - get allowed_schoolbase_dict
    userallowed_schoolbase_dict, userallowed_depbases_pk_int_arr = get_userallowed_schoolbase_dict_depbases_pk_arr(
        userallowed_sections_dict=userallowed_sections_dict,
        sel_schoolbase_pk=sel_schoolbase_pk
    )
    if logging_on:
        logger.debug('    userallowed_schoolbase_dict: ' + str(userallowed_schoolbase_dict) + ' ' + str( type(userallowed_schoolbase_dict)))
        logger.debug('    userallowed_depbases_pk_int_arr: ' + str(userallowed_depbases_pk_int_arr) + ' ' + str( type(userallowed_depbases_pk_int_arr)))

    if depbase_pk:
        if not userallowed_depbases_pk_int_arr or \
                depbase_pk in userallowed_depbases_pk_int_arr or \
                skip_allowed_filter:
            filter_single_pk = depbase_pk
        else:
            filter_none = True

    elif userallowed_depbases_pk_int_arr and not skip_allowed_filter:
        if -9 in userallowed_depbases_pk_int_arr:
            # all deps are allowed when '-9' in userallowed_depbases_pk_int_arr
            pass
        elif len(userallowed_depbases_pk_int_arr) == 1:
            filter_single_pk = userallowed_depbases_pk_int_arr[0]
        else:
            filter_pk_arr = userallowed_depbases_pk_int_arr

    if logging_on:
        logger.debug('    filter_single_pk: ' + str(filter_single_pk) + ' ' + str(type(filter_single_pk)))
        logger.debug('    filter_pk_arr: ' + str(filter_pk_arr) + ' ' + str(type(filter_pk_arr)))
        logger.debug('    filter_none: ' + str(filter_none) + ' ' + str(type(filter_none)))

    if filter_single_pk:
        sql_key_dict = {'dep_pk': filter_single_pk}
        sql_clause = "AND dep.base_id = %(dep_pk)s::INT"

    elif filter_pk_arr:
        sql_key_dict = {'dep_arr': filter_pk_arr}
        sql_clause = "AND dep.base_id IN (SELECT UNNEST(%(dep_arr)s::INT[]) )"

    elif filter_none:
        sql_clause = "AND FALSE"

    if logging_on:
        logger.debug('    sql_clause: ' + str(sql_clause))
        logger.debug('    sql_key_dict: ' + str(sql_key_dict))
        logger.debug('--- end of get_sqlclause_allowed_depbase_from_allowed_sections ----- ')

    return sql_clause, sql_key_dict
# - end of get_sqlclause_allowed_depbase_from_allowed_sections


def get_sqlclause_allowed_clusters(table, userallowed_cluster_pk_list):
    # PR2023-02-09
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_sqlclause_allowed_clusters -----')
        logger.debug('    userallowed_cluster_pk_list: ' + str(userallowed_cluster_pk_list))

    if table == 'studsubj':
        field_name = 'studsubj.cluster_id'
    else:
        field_name = 'cluster.id'

    # - create sql_clause
    sql_clause = ''
    if userallowed_cluster_pk_list:
        if len(userallowed_cluster_pk_list) == 1:
            sql_clause = ''.join(("AND ", field_name, " = ", str(userallowed_cluster_pk_list[0]), "::INT"))
        else:
            sql_clause = ''.join(("AND ", field_name, " IN (SELECT UNNEST(ARRAY", str(userallowed_cluster_pk_list), "::INT[]))"))

    if logging_on:
        logger.debug('    sql_clause: ' + str(sql_clause))

    return sql_clause


def allowedsections_has_subjbases(userallowed_sections_dict):
    # check if there any allowed subjects PR2023-02-16
    has_subjbases = False
    if userallowed_sections_dict:
    # check if there any allowed subjects
        has_subjbases = False
        for userallowed_schoolbase_dict in userallowed_sections_dict.values():
            for userallowed_depbase_dict in userallowed_schoolbase_dict.values():
                for userallowed_lvlbase_list in userallowed_depbase_dict.values():
                     if userallowed_lvlbase_list:
                        has_subjbases = True
    return has_subjbases


def get_sqlclause_allowed_NEW(table, sel_schoolbase_pk, sel_depbase_pk, sel_lvlbase_pk, userallowed_sections_dict, return_false_when_no_allowedsubjects):
    # PR2023-02-15 PR2023-04-10
    # This function  gives sql clause of all allowed schools, deps, levels and subjects.
    # It does not filter on sel_schoolpk etc.

    # called by create_studentsubject_rows, create_grade_rows,  create_grade_with_ete_exam_rows

    def get_add_to_list(sel_base_pk, base_pk_str):
        # add_to_list = True if:
        # - when base_pk_str = '-9' or
        # - when base_pk_str = sel_base_pk or
        # - when sel_base_pk is None

        add_to_list = False
        if base_pk_str:
            if sel_base_pk:
                if base_pk_str in ('-9', str(sel_base_pk)):
                    add_to_list = True
            else:
                add_to_list = True

        return add_to_list

    def get_AND_joined(parent_clause, child_clause, has_subjbases):
        and_joined = None
        if parent_clause:
            if child_clause:
                and_joined = ' AND '.join((parent_clause, child_clause))
            else:
                if not has_subjbases:
                    and_joined = parent_clause
        else:
            if child_clause:
                and_joined = child_clause
        return and_joined

    def get_OR_joined(clause_arr):
        or_joined = None
        if clause_arr:
            if len(clause_arr) == 1:
                or_joined = clause_arr[0]
            else:
                or_joined = ''.join(('(', ' OR '.join(clause_arr), ')'))
        return or_joined

    def get_base_clause(field_name, base_pk_str):
        if base_pk_str == '-9':
            base_clause = None
        else:
            base_clause = ''.join((field_name, "=", base_pk_str, "::INT"))
        return base_clause

    def get_lvl_subjbase_clause(lvlbase_pk_str, allowed_subjbase_list, return_false_when_no_allowedsubjects):

    # - create lvlbase_clause
        lvlbase_clause = get_base_clause('lvl.base_id', lvlbase_pk_str)
        logger.debug('    lvlbase_clause: ' + str(lvlbase_clause))

    # - create subjbase_clause
        subjbase_clause = None
        if allowed_subjbase_list:
            logger.debug('    allowed_subjbase_list: ' + str(allowed_subjbase_list))
            if len(allowed_subjbase_list) == 1:
                subjbase_clause = ''.join((subjbase_id_fld, "=", str(allowed_subjbase_list[0]), "::INT"))
            else:
                subjbase_clause = ''.join(
                    (subjbase_id_fld, " IN (SELECT UNNEST(ARRAY", str(allowed_subjbase_list), "::INT[]))"))
            logger.debug('    subjbase_clause: ' + str(subjbase_clause))
        else:
            logger.debug('    return_false_when_no_allowedsubjects: ' + str(return_false_when_no_allowedsubjects))
            # when user is inspectorate: 'all subjects' is not possible
            if return_false_when_no_allowedsubjects:
                subjbase_clause = 'FALSE'
    # - join lvlbase_clause AND subjbase_clause
        lvl_subjbase_clause = get_AND_joined(lvlbase_clause, subjbase_clause, has_subjbases)

        logger.debug('    lvl_subjbase_clause: ' + str(lvl_subjbase_clause))
        return lvl_subjbase_clause

#############################################

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ')
        logger.debug(' +++++ get_sqlclause_allowed_NEW +++++')
        logger.debug('    allowed_sections_dict: ' + str(userallowed_sections_dict))
        logger.debug('    sel_schoolbase_pk: ' + str(sel_schoolbase_pk))
        logger.debug('    sel_depbase_pk: ' + str(sel_depbase_pk))
        logger.debug('    sel_lvlbase_pk: ' + str(sel_lvlbase_pk))
        logger.debug('    return_false_when_no_allowedsubjects: ' + str(return_false_when_no_allowedsubjects))
        logger.debug(' ----------')

    if table == 'studsubj':
        subjbase_id_fld = 'studsubj.subjbase_id'
    else:
        subjbase_id_fld = 'subj.base_id'

    sch_dep_lvl_subjbase_clause_joined = None

    if userallowed_sections_dict:
# - check if there any allowed subjects
        has_subjbases = False
        for userallowed_schoolbase_dict in userallowed_sections_dict.values():
            for userallowed_depbase_dict in userallowed_schoolbase_dict.values():
                for userallowed_lvlbase_list in userallowed_depbase_dict.values():
                     if userallowed_lvlbase_list:
                        has_subjbases = True

        if logging_on:
            logger.debug('    has_subjbases: ' + str(has_subjbases))

# - don't return grades when corrector has no allowed subjects PR2023-04-10
        if return_false_when_no_allowedsubjects and not has_subjbases:
            sch_dep_lvl_subjbase_clause_joined = 'FALSE'
            if logging_on:
                logger.debug('   return_false_when_no_allowedsubjects > has_subjbases = False')
        else:

# +++++ loop through schools
            sch_dep_lvl_subjbase_clause_arr = []
            for schoolbase_pk_str, userallowed_schoolbase_dict in userallowed_sections_dict.items():
                # add_to_list when schoolbase_pk_str = sel_schoolbase_pk or = -9
                # - sel_schoolbase_pk has always a value
                add_to_list = get_add_to_list(sel_schoolbase_pk, schoolbase_pk_str)
                if logging_on:
                    logger.debug('    ----- ')
                    logger.debug('      schoolbase_pk_str: ' + str(schoolbase_pk_str))
                    logger.debug('      add_to_list: ' + str(add_to_list))

                if add_to_list:
            # - create schoolbase_clause
                    schoolbase_clause = get_base_clause('school.base_id', schoolbase_pk_str)
                    if logging_on:
                        logger.debug('      userallowed_schoolbase_dict: ' + str(userallowed_schoolbase_dict))
                        logger.debug('      > schoolbase_clause: ' + str(schoolbase_clause))

# ===== loop through departments
                    # PR2023-02-27: debug: must handle sqlclause,
                    # also when userallowed_schoolbase_dict is empty
                    # for instance: allowed_sections_dict: {'13': {} }
                    if sel_depbase_pk and not userallowed_schoolbase_dict:
                        # if allowed_depbase_dict is empty and  sel_depbase_pk has value: add sel_depbase_pk to allowed_depbase_dict
                        userallowed_schoolbase_dict[str(sel_depbase_pk)] = {}

                    dep_lvl_subjbase_clause_arr = []
                    for depbase_pk_str, allowed_depbase_dict in userallowed_schoolbase_dict.items():
                        # add_to_list when depbase_pk_str = sel_depbase_pk or = -9
                        # - sel_depbase_pk has always a value
                        add_to_list = get_add_to_list(sel_depbase_pk, depbase_pk_str)

                        if logging_on:
                            logger.debug('      ----- ')
                            logger.debug('        depbase_pk_str ' + str(depbase_pk_str))
                            logger.debug('        add_to_list: ' + str(add_to_list))

                        if add_to_list:

                # - create depbase_clause
                            # PR2023-02-09 all deps '-9' not in use (maybe tobe used for inspectorate)
                            depbase_clause = get_base_clause('dep.base_id', depbase_pk_str)
                            if logging_on:
                                logger.debug('        allowed_depbase_dict ' + str(allowed_depbase_dict))
                                logger.debug('        > depbase_clause: ' + str(depbase_clause))

                            # PR2023-02-27: debug: must handle sqlclause,
                            # also when allowed_depbase_dict is empty
                            # for instance: allowed_depbase_dict: {'1': {} }
                            if sel_lvlbase_pk and not allowed_depbase_dict:
                                # if allowed_depbase_dict is empty and  sel_depbase_pk has value: add sel_depbase_pk to allowed_depbase_dict
                                allowed_depbase_dict[str(sel_lvlbase_pk)] = {}

            # ----- loop through levels
                            lvl_subjbase_clause_arr = []
                            for lvlbase_pk_str, allowed_subjbase_list in allowed_depbase_dict.items():

                                if logging_on:
                                    logger.debug('        ----- ')
                                    logger.debug('          lvlbase_pk_str ' + str(lvlbase_pk_str))

                                add_to_list = get_add_to_list(sel_lvlbase_pk, lvlbase_pk_str)
                                if logging_on:
                                    logger.debug('          add_to_list: ' + str(add_to_list))

                                if add_to_list:

                                    lvl_subjbase_clause = get_lvl_subjbase_clause(lvlbase_pk_str, allowed_subjbase_list, return_false_when_no_allowedsubjects)
                                    if logging_on:
                                        logger.debug('          allowed_subjbase_list ' + str(allowed_subjbase_list))
                                        logger.debug('          > lvl_subjbase_clause: ' + str(lvl_subjbase_clause))

                                    if lvl_subjbase_clause:
                                        lvl_subjbase_clause_arr.append(''.join(('(', lvl_subjbase_clause, ')')))

            # ----- end of loop through levels

                    # - join lvl_subjbase_clause_arr with OR
                            lvl_subjbase_clause_joined = get_OR_joined(lvl_subjbase_clause_arr)

                    # - join depbase_clause and lvl_subjbase_clause_arr with AND
                            dep_lvl_subjbase_clause = get_AND_joined(depbase_clause, lvl_subjbase_clause_joined, has_subjbases)
                            if logging_on:
                                logger.debug('            > dep_lvl_subjbase_clause: ' + str(dep_lvl_subjbase_clause))

                    # - add clause to dep_lvl_subjbase_clause_arr
                            if dep_lvl_subjbase_clause:
                                dep_lvl_subjbase_clause_arr.append(''.join(('(', dep_lvl_subjbase_clause, ')')))
                                if logging_on:
                                    logger.debug('   ---> ' + str(dep_lvl_subjbase_clause))
# ===== end of loop through departments

                # - join dep_lvl_subjbase_clause_arr with OR
                    dep_lvl_subjbase_clause_joined = get_OR_joined(dep_lvl_subjbase_clause_arr)
                    if logging_on:
                        logger.debug('  > dep_lvl_subjbase_clause_joined: ' + str(dep_lvl_subjbase_clause_joined))

                # - join schoolbase_clause and dep_lvl_subjbase_clause_joined with AND
                        sch_dep_lvl_subjbase_clause = get_AND_joined(schoolbase_clause, dep_lvl_subjbase_clause_joined, has_subjbases)
                        if logging_on:
                            logger.debug('    > sch_dep_lvl_subjbase_clause: ' + str(sch_dep_lvl_subjbase_clause))

                # - add clause to sch_dep_lvl_subjbase_clause_arr
                        if sch_dep_lvl_subjbase_clause:
                            sch_dep_lvl_subjbase_clause_arr.append(''.join(('(', sch_dep_lvl_subjbase_clause, ')')))

# +++++ end of loop through schools
            # - join sch_dep_lvl_subjbase_clause_arr with OR
                sch_dep_lvl_subjbase_clause_joined = get_OR_joined(sch_dep_lvl_subjbase_clause_arr)
                if logging_on:
                    logger.debug(' ===> sch_dep_lvl_subjbase_clause_joined: ' + str(sch_dep_lvl_subjbase_clause_joined))

# - if userallowed_sections_dict is None:
    else:
        # don't return grades when corrector has no allowed subjects PR2023-04-10
        if return_false_when_no_allowedsubjects:
            sch_dep_lvl_subjbase_clause_joined = 'FALSE'
            if logging_on:
                logger.debug('   return_false_when_no_allowedsubjects > userallowed_sections_dict is None')
        else:
            # add sqlclause when sel_schoolbase_pk etc has value and allowed_sections = None
            sql_clause_arr = []
            if sel_schoolbase_pk:
                sql_clause_arr.append(get_base_clause('school.base_id', str(sel_schoolbase_pk)))
            if sel_depbase_pk:
                sql_clause_arr.append(get_base_clause('dep.base_id', str(sel_depbase_pk)))
            if sel_lvlbase_pk:
                sql_clause_arr.append(get_base_clause('lvl.base_id', str(sel_lvlbase_pk)))
            if sql_clause_arr:
                sch_dep_lvl_subjbase_clause_joined = ' AND '.join(sql_clause_arr)

    sql_clause = ''
    if sch_dep_lvl_subjbase_clause_joined:
        sql_clause = ''.join(('AND (', sch_dep_lvl_subjbase_clause_joined, ')'))

    if logging_on:
        logger.debug('   sql_clause: ' + str(sql_clause))

    return sql_clause
# - end of get_sqlclause_allowed_NEW

###########################

def validate_userallowed_school(userallowed_sections_dict, schoolbase_pk):
    # This function checks if een given school is allowed, based on allowedsections # PR2023-02-16

    is_allowed = True if schoolbase_pk else False

    if userallowed_sections_dict:
        is_allowed = False

        sb_pk_arr = ['-9']
        if schoolbase_pk:
            sb_pk_arr.append(str(schoolbase_pk))

        for sb_pk_str in sb_pk_arr:
            if sb_pk_str in userallowed_sections_dict:
                is_allowed = True
                break

    return is_allowed


def validate_userallowed_depbase(userallowed_sections_dict, sel_schoolbase_pk, sel_depbase_pk):
    # This function checks if een given depbase is allowed, based on allowedsections # PR2023-02-16
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- validate_userallowed_depbase -----')
        logger.debug('    userallowed_sections_dict: ' + str(userallowed_sections_dict))
        logger.debug('    sel_schoolbase_pk: ' + str(sel_schoolbase_pk) + ' ' + str(type(sel_schoolbase_pk)))
        logger.debug('    sel_depbase_pk: ' + str(sel_depbase_pk) + ' ' + str(type(sel_depbase_pk)))

    is_allowed = True if sel_schoolbase_pk and sel_depbase_pk else False

    if userallowed_sections_dict:
        is_allowed = False
        has_depbase_pk = False
        if sel_schoolbase_pk and sel_depbase_pk:
            for sb_pk_str in ('-9', str(sel_schoolbase_pk)):
                if sb_pk_str in userallowed_sections_dict:
                    schoolbase_dict = userallowed_sections_dict[sb_pk_str]

                    if logging_on:
                        logger.debug(' -- sb_pk_str: ' + str(sb_pk_str) + ' ' + str(type(sb_pk_str)))
                        logger.debug(' -- schoolbase_dict: ' + str(schoolbase_dict))

                    if schoolbase_dict:
                        has_depbase_pk = True
                        if logging_on:
                            logger.debug('  > has_depbase_pk: ' + str(has_depbase_pk))

                        for db_pk_str in ('-9', str(sel_depbase_pk)):
                            if db_pk_str in schoolbase_dict:
                                is_allowed = True
                                break

                if is_allowed:
                    break
        # set is_allowed = True when there are no depbases in schooldicts
        if not has_depbase_pk:
            is_allowed = True

    if logging_on:
        logger.debug(' >> is_allowed: ' + str(is_allowed))
    return is_allowed


def validate_userallowed_lvlbase(userallowed_sections_dict, sel_schoolbase_pk, sel_depbase_pk, sel_lvlbase_pk):
    # This function checks if een given lvlbase is allowed, based on allowedsections # PR2023-02-22
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- validate_userallowed_lvlbase -----')
        logger.debug('    userallowed_sections_dict: ' + str(userallowed_sections_dict))
        logger.debug('    sel_schoolbase_pk: ' + str(sel_schoolbase_pk) + ' ' + str(type(sel_schoolbase_pk)))
        logger.debug('    sel_depbase_pk: ' + str(sel_depbase_pk) + ' ' + str(type(sel_depbase_pk)))
        logger.debug('    sel_lvlbase_pk: ' + str(sel_lvlbase_pk) + ' ' + str(type(sel_lvlbase_pk)))

    is_allowed = True if sel_schoolbase_pk and sel_depbase_pk else False

    if userallowed_sections_dict:
        is_allowed = False
        has_lvlbase_pk = False
        if sel_schoolbase_pk and sel_depbase_pk:
            for sb_pk_str in ('-9', str(sel_schoolbase_pk)):
                if logging_on:
                    logger.debug(' -- sb_pk_str: ' + str(sb_pk_str) + ' ' + str(type(sb_pk_str)))
                if sb_pk_str in userallowed_sections_dict:
                    schoolbase_dict = userallowed_sections_dict[sb_pk_str]
                    if logging_on:
                        logger.debug(' -- schoolbase_dict: ' + str(schoolbase_dict))

                    if schoolbase_dict:
                        for db_pk_str in ('-9', str(sel_depbase_pk)):
                            if logging_on:
                                logger.debug('     .. db_pk_str: ' + str(db_pk_str) + ' ' + str(type(db_pk_str)))
                            if db_pk_str in schoolbase_dict:
                                depbase_dict = schoolbase_dict[db_pk_str]
                                if logging_on:
                                    logger.debug('     .. depbase_dict: ' + str(depbase_dict))

                                if depbase_dict:
                                    has_lvlbase_pk = True
                                    for lb_pk_str in ('-9', str(sel_lvlbase_pk)):
                                        is_allowed = True
                                        break

                            if is_allowed:
                                break

                if is_allowed:
                    break

        # set is_allowed = True when there are no depbases in schooldicts
        if not has_lvlbase_pk:
            is_allowed = True

    if logging_on:
        logger.debug(' >> is_allowed: ' + str(is_allowed))
    return is_allowed
# - end of validate_userallowed_lvlbase


def validate_userallowed_subjbase(userallowed_sections_dict, sel_schoolbase_pk, sel_depbase_pk, sel_lvlbase_pk, sel_subjbase_pk):
    # This function checks if een given subjbase is allowed, based on allowedsections # PR2023-02-22
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- validate_userallowed_subjbase -----')
        logger.debug('    userallowed_sections_dict: ' + str(userallowed_sections_dict))
        logger.debug('    sel_schoolbase_pk: ' + str(sel_schoolbase_pk) + ' ' + str(type(sel_schoolbase_pk)))
        logger.debug('    sel_depbase_pk: ' + str(sel_depbase_pk) + ' ' + str(type(sel_depbase_pk)))
        logger.debug('    sel_lvlbase_pk: ' + str(sel_lvlbase_pk) + ' ' + str(type(sel_lvlbase_pk)))
        logger.debug('    sel_subjbase_pk: ' + str(sel_subjbase_pk) + ' ' + str(type(sel_subjbase_pk)))

    is_allowed = True if sel_schoolbase_pk and sel_depbase_pk else False

    if userallowed_sections_dict:
        is_allowed = False
        has_subjbase_pk = False
        if sel_schoolbase_pk and sel_depbase_pk:
            for sb_pk_str in ('-9', str(sel_schoolbase_pk)):
                if logging_on:
                    logger.debug(' -- sb_pk_str: ' + str(sb_pk_str) + ' ' + str(type(sb_pk_str)))
                if sb_pk_str in userallowed_sections_dict:
                    schoolbase_dict = userallowed_sections_dict[sb_pk_str]
                    if logging_on:
                        logger.debug(' -- schoolbase_dict: ' + str(schoolbase_dict))

                    if schoolbase_dict:
                        for db_pk_str in ('-9', str(sel_depbase_pk)):
                            if logging_on:
                                logger.debug('     .. db_pk_str: ' + str(db_pk_str) + ' ' + str(type(db_pk_str)))
                            if db_pk_str in schoolbase_dict:
                                depbase_dict = schoolbase_dict[db_pk_str]
                                if logging_on:
                                    logger.debug('     .. depbase_dict: ' + str(depbase_dict))

                                if depbase_dict:
                                    for lb_pk_str in ('-9', str(sel_lvlbase_pk)):
                                        if logging_on:
                                            logger.debug('         .. lb_pk_str: ' + str(lb_pk_str))
                                        if lb_pk_str in depbase_dict:
                                            lvlbase_arr = depbase_dict[lb_pk_str]
                                            if logging_on:
                                                logger.debug('         .. lvlbase_arr: ' + str(lvlbase_arr))
                                            if lvlbase_arr:
                                                has_subjbase_pk = True
                                                if sel_subjbase_pk and sel_subjbase_pk in lvlbase_arr:
                                                    is_allowed = True
                                                    break

                                        if is_allowed:
                                            break

                            if is_allowed:
                                break

                if is_allowed:
                    break
        # set is_allowed = True when there are no depbases in schooldicts
        if not has_subjbase_pk:
            is_allowed = True

    if logging_on:
        logger.debug(' >> is_allowed: ' + str(is_allowed))
    return is_allowed
# - end of validate_userallowed_subjbase


def validate_userallowed_subjbaseOLD(userallowed_sections_dict, schoolbase_pk, depbase_pk, lvlbase_pk, subjbase_pk):
    # PR2023-02-16
    # This function checks if een given subject or grade is allowed, based on allowedsections

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- validate_userallowed_subjbase -----')
        logger.debug('    allowed_sections_dict: ' + str(userallowed_sections_dict))

    is_allowed = True
    has_subjbases = allowedsections_has_subjbases(userallowed_sections_dict)

    if has_subjbases:
        is_allowed = False
        if schoolbase_pk and depbase_pk:
            sb_pk_arr = ('-9', str(schoolbase_pk))
            for sb_pk_str in sb_pk_arr:
                depbase_dict = userallowed_sections_dict.get(sb_pk_str)
                if depbase_dict:
                    db_pk_arr = ('-9', str(depbase_pk))
                    for db_pk_str in db_pk_arr:
                        lvlbase_dict = depbase_dict.get(db_pk_str)
                        if lvlbase_dict:
                            lb_pk_arr = ['-9']
                            if lvlbase_pk:
                                lb_pk_arr.append(str(lvlbase_pk))
                            if lb_pk_arr:
                                for lb_pk_str in lb_pk_arr:
                                    subjbase_arr = lvlbase_dict.get(lb_pk_str)
                                    if subjbase_arr:
                                        if subjbase_pk in subjbase_arr:
                                            is_allowed = True
                                            break
                            if is_allowed:
                                break
                    if is_allowed:
                        break

    return is_allowed
# - end of validate_userallowed_subjbase


def validate_userallowed_cluster(userallowed_cluster_pk_list, cluster_pk):
    # PR2023-02-18
    # This function checks if een given subject or grade is allowed, based on userallowed_cluster_pk_list

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- validate_userallowed_cluster -----')
        logger.debug('    userallowed_cluster_pk_list: ' + str(userallowed_cluster_pk_list))

    is_allowed = True
    if userallowed_cluster_pk_list:
        is_allowed = False
        if cluster_pk and cluster_pk in userallowed_cluster_pk_list:
            is_allowed = True
    return is_allowed
# - end of validate_userallowed_subjbase


###########################
def get_sqlclause_allowed_lvlbase_from_lvlbase_pk_arr(allowed_lvlbase_pk_arr):
    # PR2023-02-21 used in get_sqlclause_allowed_lvlbase and approve / submit Ex1 Ex4
    # filter school and depbase not included, happens outsude this functions
    # only add sqlclasue lvlbase

    sql_clause = None
    if allowed_lvlbase_pk_arr:
        if -9 in allowed_lvlbase_pk_arr:
            pass
        elif len(allowed_lvlbase_pk_arr) == 1:
            sql_clause = ''.join(("AND lvl.base_id= ", str(allowed_lvlbase_pk_arr[0]), "::INT"))
        else:
            sql_clause = ''.join(("AND lvl.base_id IN (SELECT UNNEST(ARRAY", str(allowed_lvlbase_pk_arr), "::INT[]))"))

    return sql_clause
# - end of get_sqlclause_allowed_lvlbase_from_lvlbase_pk_arr


def get_sqlclause_allowed_lvlbaseNIU(userallowed_sections_dict, sel_schoolbase_pk, sel_depbase_pk):
    # PR2023-02-21 used in approve / submit Ex1 Ex4
    # filter school and depbase not included, happens outsude this functions
    # only add sqlclasue lvlbase

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('')
        logger.debug('----- get_sqlclause_allowed_lvlbase -----')

    # - filter on allowed depbases, levelbase, subjectbases, not when is_submit PR2023-02-18
    # dont filter on allowed subjects and allowed clusters, but do filter on allowed lvlbases'
    userallowed_schoolbase_dict, userallowed_depbases_pk_arr = get_userallowed_schoolbase_dict_depbases_pk_arr(
        userallowed_sections_dict, sel_schoolbase_pk)
    allowed_depbase_dict, allowed_lvlbase_pk_arr = get_userallowed_depbase_dict_lvlbases_pk_arr(
        userallowed_schoolbase_dict, sel_depbase_pk)

    if logging_on:
        logger.debug('    userallowed_schoolbase_dict: ' + str(userallowed_schoolbase_dict))
        logger.debug('    allowed_depbase_dict: ' + str(allowed_depbase_dict))
        logger.debug('    allowed_lvlbase_pk_arr: ' + str(allowed_lvlbase_pk_arr))

    sql_clause = get_sqlclause_allowed_lvlbase_from_lvlbase_pk_arr(allowed_lvlbase_pk_arr)

    return sql_clause


def get_sqlclause_allowed_dep_lvl_subj(table, userallowed_sections_dict, sel_schoolbase_pk, sel_depbase_pk):
    # PR2022-03-14  PR2022-12-08 PR2023-01-25 PR2023-02-09
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_sqlclause_allowed_dep_lvl_subj -----')
        logger.debug('    allowed_sections_dict: ' + str(userallowed_sections_dict))
    # allowed_sections_dict: {'2': {'1': {'4': [117, 114], '5': [], '-9': [118, 121]}}} <class 'dict'>

    if table == 'studsubj':
        subjbase_id_fld = 'studsubj.subjbase_id'
    else:
        subjbase_id_fld = 'subj.base_id'

    userallowed_schoolbase_dict, userallowed_depbases_pk_arr = \
        get_userallowed_schoolbase_dict_depbases_pk_arr(
            userallowed_sections_dict=userallowed_sections_dict,
            sel_schoolbase_pk=sel_schoolbase_pk
        )
    if logging_on:
        logger.debug('    userallowed_schoolbase_dict: ' + str(userallowed_schoolbase_dict))
        logger.debug('    userallowed_depbases_pk_arr: ' + str(userallowed_depbases_pk_arr))
    # userallowed_schoolbase_dict: {'1': {'4': [117, 114], '5': [], '-9': [118, 121]}} <class 'dict'>
    # userallowed_depbases_pk_arr: [1] <class 'list'>

    allowed_depbase_dict, allowed_lvlbase_pk_arr = \
        get_userallowed_depbase_dict_lvlbases_pk_arr(
            allowed_schoolbase_dict=userallowed_schoolbase_dict,
            sel_depbase_pk=sel_depbase_pk
        )
    if logging_on:
        logger.debug('    allowed_depbase_dict: ' + str(allowed_depbase_dict) + ' ' + str(type(allowed_depbase_dict)))
        logger.debug(
            '    allowed_lvlbase_pk_arr: ' + str(allowed_lvlbase_pk_arr) + ' ' + str(type(allowed_lvlbase_pk_arr)))
    # allowed_depbase_dict: {'4': [117, 114], '5': [], '-9': [118, 121]} <class 'dict'>
    # allowed_lvlbase_pk_arr: [4, 5, -9] <class 'list'>

    dep_lvl_subj_clause_arr = []

# +++++ loop through allowed depbases +++++
    # userallowed_schoolbase_dict: {'1': {'4': [117, 114], '-9': [118, 121]}} <class 'dict'>
    for sel_depbase_pk_str, allowed_depbase_dict in userallowed_schoolbase_dict.items():
        if logging_on:
            logger.debug('  ----- ')
            logger.debug('    sel_depbase_pk_str: ' + str(sel_depbase_pk_str))
            logger.debug('    allowed_depbase_dict: ' + str(allowed_depbase_dict))
        # sel_depbase_pk_str: 1 <class 'str'>
        # allowed_depbase_dict: {'4': [117, 114], '5': [], '-9': [118, 121]}

    # - create depbase_clause
        # PR2023-02-09 all deps '-9' not in use (maybe tobe used for inspectorate)
        if sel_depbase_pk_str == '-9':
            depbase_clause = None
        else:
            depbase_clause = ''.join(("dep.base_id = ", sel_depbase_pk_str, "::INT"))
        if logging_on:
            logger.debug('    depbase_clause: ' + str(depbase_clause))
        # depbase_clause: dep.base_id = 1::INT

        lvl_subjbase_clause_joined = None
        if allowed_depbase_dict:
            lvl_subjbase_clause_arr = []

    # ===== loop through allowed lvlbases =====
            for sel_lvlbase_pk_str, allowed_subjbases_list in allowed_depbase_dict.items():
                if logging_on:
                    logger.debug('  ..... ')
                    logger.debug(
                        '    sel_lvlbase_pk_str: ' + str(sel_lvlbase_pk_str) + ' ' + str(type(sel_lvlbase_pk_str)))
                    logger.debug('    allowed_subjbases_list: ' + str(allowed_subjbases_list))
                # sel_lvlbase_pk_str: 4 <class 'str'>
                # allowed_subjbases_list: [117, 114]
                # sel_lvlbase_pk_str: 5 <class 'str'>
                # allowed_subjbases_list: []
                # sel_lvlbase_pk_str: -9 <class 'str'>
                # allowed_subjbases_list: [118, 121]

        # - create lvlbase_clause
                if sel_lvlbase_pk_str == '-9':
                    lvlbase_clause = None
                else:
                    lvlbase_clause = ''.join(("lvl.base_id = ", sel_lvlbase_pk_str, "::INT"))
                if logging_on:
                    logger.debug('    lvlbase_clause: ' + str(lvlbase_clause))
                # lvlbase_clause: lvl.base_id = 4::INT
                # lvlbase_clause: lvl.base_id = 5::INT
                # lvlbase_clause: None

        # - create subjbase_clause
                subjbase_clause = None
                skip_allowedsubjbase_filter = False
                if allowed_subjbases_list and not skip_allowedsubjbase_filter:
                    if len(allowed_subjbases_list) == 1:
                        subjbase_clause = ''.join((subjbase_id_fld, " = ", str(allowed_subjbases_list[0]), "::INT"))
                    else:
                        subjbase_clause = ''.join((subjbase_id_fld, " IN (SELECT UNNEST(ARRAY", str(allowed_subjbases_list), "::INT[]))"))

                if logging_on:
                    logger.debug('    subjbase_clause: ' + str(subjbase_clause))
                # subjbase_clause: subj.base_id IN (SELECT UNNEST(ARRAY[117, 114]::INT[]))
                # subjbase_clause: None
                # subjbase_clause: subj.base_id IN (SELECT UNNEST(ARRAY[118, 121]::INT[]))


        # - join depbase_clause and lvlbase_clause  and add to array, to prvent error when base_clause = None
                lvl_subjbase_clause = None
                if lvlbase_clause:
                    if subjbase_clause:
                        lvl_subjbase_clause = ' AND '.join((lvlbase_clause, subjbase_clause))
                    else:
                        lvl_subjbase_clause = lvlbase_clause
                else:
                    if subjbase_clause:
                        lvl_subjbase_clause = subjbase_clause

                if lvl_subjbase_clause:
                    lvl_subjbase_clause_arr.append(''.join(('(', lvl_subjbase_clause, ')')))
                # lvl_subjbase: subj.base_id IN (SELECT UNNEST(ARRAY[167, 118]::INT[]))

                if logging_on:
                    logger.debug('    lvl_subjbase_clause_arr: ' + str(lvl_subjbase_clause_arr))
                #  lvl_subjbase_clause_arr: ['(lvl.base_id = 4::INT AND subj.base_id IN (SELECT UNNEST(ARRAY[117, 114]::INT[])))']
                #  lvl_subjbase_clause_arr: ['(lvl.base_id = 4::INT AND subj.base_id IN (SELECT UNNEST(ARRAY[117, 114]::INT[])))', '(lvl.base_id = 5::INT)']
                # lvl_subjbase_clause_arr: [
                #       '(lvl.base_id = 4::INT AND subj.base_id IN (SELECT UNNEST(ARRAY[117, 114]::INT[])))',
                #       '(lvl.base_id = 5::INT)',
                #       '(subj.base_id IN (SELECT UNNEST(ARRAY[118, 121]::INT[])))']
                #

    # ===== end of loop through allowed lvlbases =====

        # - join lvl_subjbase_clause_arr
            if lvl_subjbase_clause_arr:
                lvl_subjbase_clause_joined = ''.join(('(', ' OR '.join(lvl_subjbase_clause_arr), ')'))
            if logging_on:
                logger.debug('    lvl_subjbase_clause_joined: ' + str(lvl_subjbase_clause_joined))
                # lvl_subjbase_clause_joined: ((lvl.base_id = 4::INT AND subj.base_id IN (SELECT UNNEST(ARRAY[117, 114]::INT[]))) OR
                #                           (lvl.base_id = 5::INT) OR
                #                           (subj.base_id IN (SELECT UNNEST(ARRAY[118, 121]::INT[]))))


        # - join depbase_clause and lvlbase_clause  and add to array, to prvent error when base_clause = None
        dep_lvl_subj_clause_joined = None
        if depbase_clause:
            if lvl_subjbase_clause_joined:
                dep_lvl_subj_clause_joined = ' AND '.join((depbase_clause, lvl_subjbase_clause_joined))
            else:
                dep_lvl_subj_clause_joined = depbase_clause
        else:
            if lvl_subjbase_clause_joined:
                dep_lvl_subj_clause_joined = lvl_subjbase_clause_joined

        if dep_lvl_subj_clause_joined:
            dep_lvl_subj_clause_arr.append(''.join(('(', dep_lvl_subj_clause_joined, ')')))

# +++++ end of loop through allowed depbases +++++

    sql_clause = ''
    if dep_lvl_subj_clause_arr:
        sql_clause = ''.join(('AND (', ' OR '.join(dep_lvl_subj_clause_arr), ')'))
    if logging_on:
        logger.debug('   sql_clause: ' + str(sql_clause))
    """
    sql_clause: 
        (
            (dep.base_id = 1::INT AND 
                (   
                    (
                        lvl.base_id = 4::INT AND subj.base_id IN (SELECT UNNEST(ARRAY[117, 114]::INT[]))
                    ) OR  (
                        lvl.base_id = 5::INT
                    ) OR (
                        subj.base_id IN (SELECT UNNEST(ARRAY[118, 121]::INT[]))
                    )
                )
            )
        )
    """

    return sql_clause
# - end of get_sqlclause_allowed_dep_lvl_subj
# +++++++++++++++++++++++++++++++++++++++++++++


def has_permit(request, page, permit_arr):  # PR2023-04-13
    has_permit = False
    if request.user and page and permit_arr:
        req_usr = request.user
        if req_usr.country and req_usr.schoolbase:
            permit_list = get_permit_list(page, req_usr)
            if permit_list:
                for permit in permit_arr:
                    if permit in permit_list:
                        has_permit = True
                        break
    return has_permit


def get_permit_list(page, req_usr):
    # --- create list of all permits  of this user PR2021-04-22  PR2021-07-03 PR2023-01-13 PR2023-04-18
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('')
        logger.debug('----- get_permit_list -----')
        logger.debug('    page: ' + str(page))

    requsr_role = getattr(req_usr, 'role')

    userallowed_instance = get_userallowed_instance_from_user_instance(req_usr)
    requsr_usergroups_list = get_usergroup_list(userallowed_instance)

    if logging_on:
        logger.debug('    requsr_usergroups_list: ' + str(requsr_usergroups_list) + ' ' + str(type(requsr_usergroups_list)))
        logger.debug('    requsr_role: ' + str(requsr_role) + ' ' + str(type(requsr_role)))
    # requsr_usergroups_list: ['admin', 'auth2', 'edit'] <class 'list'>

    permit_list = []
    if page and requsr_role and requsr_usergroups_list:

        sql_filter = ""
        filter_list = []

        for usergroup in requsr_usergroups_list:
            filter_list.append("(POSITION('" + usergroup + "' IN p.usergroups) > 0)")

        if filter_list:
            sql_filter = ' OR '.join(filter_list)

        if logging_on:
            logger.debug('    sql_filter: ' + str(sql_filter))

        if sql_filter:
            sql_filter = ''.join(("AND (", sql_filter, ")"))

            sql_list = ["SELECT p.action FROM accounts_userpermit AS p ",
                        "WHERE (p.page = '", page, "' OR p.page = 'page_all') ",
                        "AND p.role = ", str(requsr_role), "::INT ",
                        sql_filter]
            sql = ''.join(sql_list)

            if logging_on:
                logger.debug('    sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql)
                """
                accounts_userpermit = {role: 8, page: 'page_school', action: 'view', usergroups: 'admin;anlz;auth1;auth2;auth3;edit;read'} 
                """
                for row in cursor.fetchall():
                    if logging_on:
                        logger.debug('row: ' + str(row) + ' ' + str(type(row)))

                    if row[0]:
                        permit = 'permit_' + row[0]
                        if permit not in permit_list:
                            permit_list.append(permit)

    if logging_on:
        logger.debug('    permit_list: ' + str(permit_list) + ' ' + str(type(permit_list)))

    return permit_list
# - end of get_permit_list


def get_requsr_permitlist_usergroups_allowedsections_allowedclusters(request, page):
    # --- create list of all permits and usergroups of req_usr PR2021-03-19
    # - usergroups are now stored per examyear in usergroup_allowed PR2022-12-09
    # PR2023-01-13
    logging_on = False  # s.LOGGING_ON

# - get requsr_usergroups_list, requsr_allowed_clusters_list and  sel_examyear
    requsr_usergroups_list, requsr_allowed_sections_dict, requsr_allowed_clusters_list, sel_examyear = \
        get_allowedusergrouplist_allowedsectionsdict_allowedclusterlist(
            user_instance=request.user
        )

    if logging_on:
        logger.debug('')
        logger.debug('----- get_requsr_permitlist_usergroups_allowedsections_allowedclusters ----- ')
        logger.debug('    page:                   ' + str(page) + ' ' + str(type(page)))
        logger.debug('    requsr_usergroups_list: ' + str(requsr_usergroups_list) + ' ' + str(type(requsr_usergroups_list)))

    permit_list = []
    if request.user.role and page:
        sql_filter = ""
        for usergroup in requsr_usergroups_list:
            sql_filter += " OR (POSITION('" + usergroup + "' IN p.usergroups) > 0)"

        if sql_filter:
            sql_filter = "AND (" + sql_filter[4:] + ")"

            sql_keys = {'page': page, 'role': request.user.role}
            sql_list = ["SELECT p.action FROM accounts_userpermit AS p",
                        "WHERE (p.page = %(page)s OR p.page = 'page_all') AND p.role = %(role)s::INT",
                        sql_filter
                        ]
            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                for row in cursor.fetchall():

                    # PR2023-04-05 permit 'write_message' is not in use any more, use usergroup msgsend instead

                    if row[0]:
                        permit = 'permit_' + row[0]
                        if permit not in permit_list:
                            permit_list.append(permit)

    if logging_on:
        logger.debug('    permit_list: ' + str(permit_list) + ' ' + str(type(permit_list)))

    return permit_list, requsr_usergroups_list, requsr_allowed_sections_dict, requsr_allowed_clusters_list
# - end of get_requsr_permitlist_usergroups_allowedsections_allowedclusters


def get_permit_of_this_page(page, permit, request):
    # --- get permit for this page # PR2021-07-18 PR2021-09-05 PR2022-07-05 PR2023-01-13

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- get_permit_of_this_page  -------')

    has_permit = False
    if page and permit and request.user and request.user.country and request.user.schoolbase:
        permit_list = get_permit_list(page, request.user)
        if logging_on:
            logger.debug('    permit_list: ' + str(permit_list))

        if permit_list:
            prefix_permit = 'permit_' + permit
            if logging_on:
                logger.debug('    prefix_permit: ' + str(prefix_permit))

            has_permit = prefix_permit in permit_list

    if logging_on:
        logger.debug('    has_permit: ' + str(has_permit))

    return has_permit
# - end of get_permit_of_this_page


def get_permit_crud_of_this_page(page, request):
    # --- get crud permit for this page # PR2021-07-18 PR2021-09-05 PR2023-01-13

    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug('----- get_permit_crud_of_this_page  -------')

    has_permit = get_permit_of_this_page(page, 'crud', request)

    if logging_on:
        logger.debug('    has_permit: ' + str(has_permit))

    return has_permit
# - end of get_permit_crud_of_this_page

# ==========================

def is_usergroup_admin(req_usr):
    # PR2023-01-13
    has_permit = False
    if req_usr.is_authenticated:
        requsr_usergroups_list, allowed_sections_dictNIU, requsr_allowed_clusters_listNIU, sel_examyearNIU = \
            get_allowedusergrouplist_allowedsectionsdict_allowedclusterlist(req_usr)

        has_permit = requsr_usergroups_list and 'admin' in requsr_usergroups_list

    return has_permit


def is_role_insp_or_system_and_group_admin(req_usr):
    # PR2018-05-31 PR2023-01-13
    has_permit = False
    if req_usr.is_authenticated:
        if req_usr.role is not None: # PR2018-05-31 debug: req_usr.role = False when value = 0!!! Use is not None instead
            if req_usr.role == c.ROLE_128_SYSTEM or req_usr.role == c.ROLE_032_INSP:

                has_permit = is_usergroup_admin(req_usr)

    return has_permit


def err_html_no_permit(action_txt=None):  # PR2023-03-20
    return ''.join(("<div class='p-2 border_bg_invalid'>", err_txt_no_permit(action_txt), "</div>"))


def err_txt_no_permit(action_txt=None):  # PR2023-04-16
    if not action_txt:
        action_txt = _('to perform this action')
    return gettext("You don't have permission %(cpt)s.") % {'cpt': str(action_txt)}


def err_txt_cannot_make_changes():  # PR2023-04-16
    return gettext("You cannot make changes.")


def msghtml_error_occurred_no_border(err_txt, msg_txt=None):  # PR2023-04-17
    msg_list = [gettext('An error occurred')]
    if err_txt:
        msg_list.extend(['<br>&emsp;<i>', str(err_txt), '</i>'])
    if msg_txt:
        msg_list.extend(['<br>', str(msg_txt)])
    return ''.join((msg_list))



def msghtml_error_occurred_with_border(err_txt, msg_txt=None):  # PR2023-03-20
    msg_list = ["<p class='border_bg_invalid p-2'>",
                str(_('An error occurred'))]
    if err_txt:
        msg_list.extend(['<br>&emsp;<i>', str(err_txt), '</i>'])
    if msg_txt:
        msg_list.extend(['<br>', str(msg_txt)])
    msg_list.append("</p>")

    return ''.join((msg_list))


def msghtml_from_msglist_with_border(err_list, border_class=None):  # PR2023-04-02
    msg_list = []
    if err_list:
        if border_class is None:
            border_class = ""

        msg_list.extend(["<p class='", border_class, " p-2'>"])

        # loop is necessary to convert err_txt to string
        for index, err_txt in enumerate(err_list):
            if index:
                msg_list.append("<br>")
            msg_list.append(str(err_txt))

        msg_list.append("</p>")

    return ''.join(msg_list)


def msghtml_from_msgtxt_with_border(msg_text, border_class=None):  # PR2023-04-01
    msg_html = None
    if msg_text:
        if border_class is None:
            border_class = "border_bg_transparent"
        msg_html = ''.join((
            "<p class='", border_class, " p-2'>",
            str(msg_text),
            "</p>"
        ))
    return msg_html





