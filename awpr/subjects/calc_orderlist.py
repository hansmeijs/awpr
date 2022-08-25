# PR2022-08-13
import json

from django.db import connection

from awpr import settings as s
from awpr import constants as c
from awpr import functions as af

import logging
logger = logging.getLogger(__name__)

# /////////////////////////////////////////////////////////////////


def create_studsubj_count_dict(sel_examyear_instance, sel_examperiod, request, prm_schoolbase_pk=None):
    # PR2021-08-19 PR2021-09-24 PR2022-08-13
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_studsubj_count_dict ----- ')

    #  create nested dict with subjects count per exam, lang, dep, lvl, school and subjbase_id
    #  all schools of CUR and SXM only submitted subjects, not deleted # PR2021-08-19
    #  add extra for ETE and DOE PR2021-09-25
    # called by: create_orderlist_xlsx, create_orderlist_per_school_xlsx, OrderlistsPublishView

# - get schoolbase_id of ETE and DOE - necessary to calculate extra exams for ETE and DOE

# - create mapped_admin_dict with key = country_id and value = row_dict
    # mapped_admin_dict: key = country_id, value = {'country_id': 2, 'sb_id': 34, 'c': 'SXMDOE', ...
    mapped_admin_dict = create_mapped_admin_dict(sel_examyear_instance)
    """
     mapped_admin_dict: {
        1: {'country_id': 1, 'sb_id': 23, 'c': 'CURETE', 'order_extra_fixed': 8, 'order_extra_perc': 8, 'order_round_to': 8, 'order_tv2_divisor': 88, 'order_tv2_multiplier': 8, 'order_tv2_max': 88, 'order_admin_divisor': 88, 'order_admin_multiplier': 8, 'order_admin_max': 88}, 
        2: {'country_id': 2, 'sb_id': 34, 'c': 'SXMDOE', 'order_extra_fixed': 2, 'order_extra_perc': 5, 'order_round_to': 5, 'order_tv2_divisor': 25, 'order_tv2_multiplier': 5, 'order_tv2_max': 25, 'order_admin_divisor': 100, 'order_admin_multiplier': 5, 'order_admin_max': 25}} 
    """
    rows = create_studsubj_count_rows(sel_examyear_instance, sel_examperiod, request, prm_schoolbase_pk)

    # TODO to be solved: group by si.ete_exam and si.otherlang goes wrong when sectors of one level have different otherlang PR2022-08-13

    count_dict = {'total': {}}

    for row in rows:

        # admin_id is schoolbase_id of school of ETE / DOE
        admin_id, admin_code = None, None

        country_id = row.get('country_id')
        if country_id in mapped_admin_dict:
            mapped_country_dict = mapped_admin_dict[country_id]
            admin_id = mapped_country_dict.get('sb_id')
            admin_code = mapped_country_dict.get('c')

# +++ count extra exams and examns tv2 per school / subject
        subj_count = row.get('subj_count') or 0
        extra_count = row.get('extra_count') or 0
        tv2_count = row.get('tv2_count') or 0

        """
        row: {'subjbase_id': 121, 'ete_exam': True, 'lang': 'nl', 'country_id': 1, 'sb_code': 'CUR05', 
        'lvl_abbrev': 'PKL', 'subj_name': 'Wiskunde', 'schoolbase_id': 6, 'depbase_id': 1, 'lvlbase_id': 5, 
        'subj_count': 32, 'extra_count': 8, 'tv2_count': 10}
        """

    # - get eteduo_dict
        ete_duo = 'ETE' if row.get('ete_exam', False) else 'DUO'
        if ete_duo not in count_dict:
            count_dict[ete_duo] = {'total': {}}
        eteduo_dict = count_dict[ete_duo]

    # - get lang_dict
        lang = row.get('lang', 'nl')
        if lang not in eteduo_dict:
            # lang_dict has no key 'total'
            # eteduo_dict[lang] = {}
            eteduo_dict[lang] = {'total': {}}
        lang_dict = eteduo_dict[lang]

    # - get depbase_dict
        depbase_pk = row.get('depbase_id')

        if depbase_pk not in lang_dict:
            dep_abbrev = row.get('dep_abbrev')
            # depbase_dict has no key 'total'
            #lang_dict[depbase_pk] = {}
            lang_dict[depbase_pk] = {'c': dep_abbrev, 'total': {}}
        depbase_dict = lang_dict[depbase_pk]

    # - get lvlbase_dict
        # value is '0' when lvlbase_id = None (Havo/Vwo)
        lvlbase_pk = row.get('lvlbase_id', 0)
        if lvlbase_pk is None:
            lvlbase_pk = 0
        if lvlbase_pk not in depbase_dict:
            lvl_abbrev = row.get('lvl_abbrev', '-')
            depbase_dict[lvlbase_pk] = {'c': lvl_abbrev, 'total': {}, 'country': {}}
        lvlbase_dict = depbase_dict[lvlbase_pk]

    # - get schoolbase_dict
        row_sb_pk = row.get('schoolbase_id')
        if row_sb_pk not in lvlbase_dict:
            row_sb_code = row.get('sb_code', '-')  # for testing only
            lvlbase_dict[row_sb_pk] = {'c': row_sb_code}
        schoolbase_dict = lvlbase_dict[row_sb_pk]

# +++ calculate  schoolbase_dict total
        subjbase_pk = row.get('subjbase_id')
        if subjbase_pk not in schoolbase_dict:
            schoolbase_dict[subjbase_pk] = [subj_count, extra_count, tv2_count]
        else:
            schoolbase_dict[subjbase_pk][0] += subj_count
            schoolbase_dict[subjbase_pk][1] += extra_count
            schoolbase_dict[subjbase_pk][2] += tv2_count

        if logging_on and False:
            logger.debug('schoolbase_dict: ' + str(schoolbase_dict))
        """
        schoolbase_dict: {'c': 'CUR05', 121: [32, 8, 10]}  [subj_count, extra_count, tv2_count]
        """

# +++ calculate lvlbase_total
        lvlbase_total = lvlbase_dict.get('total')
        if subjbase_pk not in lvlbase_total:
            lvlbase_total[subjbase_pk] = [subj_count, extra_count, tv2_count]
        else:
            lvlbase_total[subjbase_pk][0] += subj_count
            lvlbase_total[subjbase_pk][1] += extra_count
            lvlbase_total[subjbase_pk][2] += tv2_count

# +++ calculate admin_total
     # skip admin_total when calculate per school > when schoolbase_pk has value
        if prm_schoolbase_pk is None:
            lvlbase_country = lvlbase_dict.get('country')
            if admin_id not in lvlbase_country:
                lvlbase_country[admin_id] = {'c': admin_code}
            admin_total = lvlbase_country[admin_id]

            if subjbase_pk not in admin_total:
                admin_total[subjbase_pk] = [subj_count, extra_count, tv2_count]
            else:
                admin_total[subjbase_pk][0] += subj_count
                admin_total[subjbase_pk][1] += extra_count
                admin_total[subjbase_pk][2] += tv2_count

            if logging_on and False:
                logger.debug(' - - - - ')
                logger.debug('........admin_total: ' + str(admin_total))
                """
                admin_total: {'c': 'CURETE', 121: [32, 8, 10], 120: [1, 4, 5], 114: [76, 9, 20]}
                """

# +++ calculate eteduo_total
        eteduo_total = eteduo_dict.get('total')
        if subjbase_pk not in eteduo_total:
            eteduo_total[subjbase_pk] = [subj_count, extra_count, tv2_count]
        else:
            eteduo_total[subjbase_pk][0] += subj_count
            eteduo_total[subjbase_pk][1] += extra_count
            eteduo_total[subjbase_pk][2] += tv2_count

# +++ calculate examyear_total
        examyear_total = count_dict.get('total')
        if subjbase_pk not in examyear_total:
            examyear_total[subjbase_pk] = [subj_count, extra_count, tv2_count]
        else:
            examyear_total[subjbase_pk][0] += subj_count
            examyear_total[subjbase_pk][1] += extra_count
            examyear_total[subjbase_pk][2] += tv2_count

# +++ after adding schools: calculate extra for ETE and DOE:
    # skip when calculate per school > when schoolbase_pk has value
    if prm_schoolbase_pk is None:
        for ete_duo, eteduo_dict in count_dict.items():
            if ete_duo != 'total':
                if logging_on:
                    logger.debug('ete_duo: ' + str(ete_duo) + ' ' + str(type(ete_duo)))

                for lang, lang_dict in eteduo_dict.items():
                    if lang != 'total':
                        if logging_on:
                            logger.debug('lang: ' + str(lang) + ' ' + str(type(lang)))

                        for depbase_pk, depbase_dict in lang_dict.items():
                            if isinstance(depbase_pk, int):
                                for lvlbase_pk, lvlbase_dict in depbase_dict.items():
                                    if isinstance(lvlbase_pk, int):
                                        if logging_on and False:
                                            logger.debug('lvlbase_pk: ' + str(lvlbase_pk) + ' ' + str(type(lvlbase_pk)))
                                            logger.debug('lvlbase_dict: ' + str(lvlbase_dict) + ' ' + str(type(lvlbase_dict)))
                                        """
                                        lvlbase_dict: {
                                            'c': 'PKL', 
                                            'total': {121: [192, 48, 60], 120: [81, 39, 55], 
                                            'country': {23: {'c': 'CURETE', 121: [192, 48, 60], 
                                                        34: {'c': 'SXMDOE', 129: [8, 7, 5], 114: [70, 20, 20], 
                                            6: {'c': 'CUR05', 121: [32, 8, 10], 133: [24, 6, 5],
                                        """

                                        lvlbase_country_dict = lvlbase_dict.get('country')
                                        lvlbase_total_dict = lvlbase_dict.get('total')
                                        eteduo_total_dict = eteduo_dict.get('total')
                                        examyear_total_dict = count_dict.get('total')

                                        if lvlbase_country_dict:
                                            if logging_on and False:
                                                logger.debug('lvlbase_country_dict: ' + str(lvlbase_country_dict) + ' ' + str(type(lvlbase_country_dict)))
                                                """
                                                lvlbase_country_dict: {
                                                23: {'c': 'CURETE', 121: [192, 48, 60], 120: [81, 39, 55], 114: [370, 70, 110], ]}, 
                                                34: {'c': 'SXMDOE', 129: [8, 7, 5], 114: [70, 20, 20], 113: [70, 20, 20], 126: [4, 6, 5], 125: [2, 3, 5]}} 
                                                """

                                            #  country_id: 1
                                            # mapped_country_dict: { 'country_id': 1, 'sb_id': 23, 'c': 'CURETE',
                                            # 'order_extra_fixed': 2, 'order_extra_perc': 5, 'order_round_to': 5,
                                            # 'order_tv2_divisor': 25, 'order_tv2_multiplier': 6, 'order_tv2_max': 25,
                                            # 'order_admin_divisor': 30, 'order_admin_multiplier': 7, 'order_admin_max': 25}

                            # - get admin_pk from mapped_country_dict with key: country_id
                                            # admin_pk is schoolbase_id of school of ETE / DEX
                                            for country_id, mapped_country_dict in mapped_admin_dict.items():
                                                admin_pk = mapped_country_dict.get('sb_id')
                                                admin_code = mapped_country_dict.get('c')
                                                order_admin_divisor = mapped_country_dict.get('order_admin_divisor')
                                                order_admin_multiplier = mapped_country_dict.get('order_admin_multiplier')
                                                order_admin_max = mapped_country_dict.get('order_admin_max')

                            # - lookup 'country_admin_dict' in lvlbase_country_dict, with key: admin_pk
                                                # country_admin_dict contains subject_count of all subjects of this admin, this level
                                                if admin_pk in lvlbase_country_dict:
                                                    country_admin_dict = lvlbase_country_dict.get(admin_pk)
                                                    if logging_on and False:
                                                        logger.debug(
                                                            'mapped_country_dict: ' + str(mapped_country_dict) + ' ' + str( type(mapped_country_dict)))
                                                        """
                                                        mapped_country_dict: {'country_id': 2, 'sb_id': 34, 'c': 'SXMDOE', 'order_extra_fixed': 2, 'order_extra_perc': 5, 'order_round_to': 5, 
                                                        'order_tv2_divisor': 25, 'order_tv2_multiplier': 5, 'order_tv2_max': 25, 'order_admin_divisor': 100, 
                                                        'order_admin_multiplier': 5, 'order_admin_max': 25} 
                                                        """

                            # - add extra row 'lvlbase_admin_dict' for ETE / DOE in lvlbase_dict, if not exists yet
                                                    if admin_pk not in lvlbase_dict:
                                                        lvlbase_dict[admin_pk] = {'c': admin_code}
                                                    lvlbase_admin_dict = lvlbase_dict[admin_pk]

                                                    if logging_on:
                                                        logger.debug('lvlbase_admin_dict: ' + str(lvlbase_admin_dict) + ' ' + str(type(lvlbase_admin_dict)))
                                                        """
                                                        lvlbase_admin_dict = {'c': 'CURETE', 430: [0, 25, 0], 440: [0, 21, 0], 435: [0, 7, 0]}}
                                                        """
                            # - loop through subjects in country_admin_dict
                                                    for subjbase_pk, count_list in country_admin_dict.items():
                                                        if logging_on:
                                                            logger.debug(' >>> subjbase_pk: ' + str(subjbase_pk) + ' count_list: ' + str(count_list))
                                                        """
                                                        subjbase_pk: 133 count_list: [127, 43, 50]
                                                        """
                                                        if isinstance(subjbase_pk, int):
                            # - caculate extra exams for ETE / DEX
                                                            sj_count = count_list[0]
                                                            tv2_count = count_list[2]

                                                            admin_extra_count = calc_exams_tv02(sj_count, order_admin_divisor, order_admin_multiplier, order_admin_max)
                                                            # TODO tv2 calc for extra ETE / DEZ
                                                            # TODO separate variables for extra tv2 ETE/DOE
                                                            admin_tv2_count = calc_exams_tv02(tv2_count, order_admin_divisor, order_admin_multiplier, order_admin_max)
                                                            if logging_on:
                                                                logger.debug('admin_extra_count: ' + str(admin_extra_count) + ' ' + str(type(admin_extra_count)))
                                                                logger.debug('admin_tv2_count: ' + str(admin_tv2_count) + ' ' + str(type(admin_tv2_count)))

                            # - add extra exams to lvlbase_admin_dict
                                                            # index 0 contains sj_count, but admins don't have exams, omly extra and tv2 extra
                                                            lvlbase_admin_dict[subjbase_pk] = [0, admin_extra_count, admin_tv2_count ]

                            # - also add admin_extra_count to total row of lvlbase_total_dict, eteduo_total_dict and examyear_total_dict
                                                            if subjbase_pk in lvlbase_total_dict:
                                                                # Note: admin has no exams: total_dict[subjbase_pk][0] += 0
                                                                lvlbase_total_dict[subjbase_pk][1] += admin_extra_count
                                                                lvlbase_total_dict[subjbase_pk][2] += admin_tv2_count

                                                            if subjbase_pk in eteduo_total_dict:
                                                                # Note: admin has no exams: total_dict[subjbase_pk][0] += 0
                                                                eteduo_total_dict[subjbase_pk][1] += admin_extra_count
                                                                eteduo_total_dict[subjbase_pk][2] += admin_tv2_count

                                                            if subjbase_pk in examyear_total_dict:
                                                                # Note: admin has no exams: total_dict[subjbase_pk][0] += 0
                                                                examyear_total_dict[subjbase_pk][1] += admin_extra_count
                                                                examyear_total_dict[subjbase_pk][2] += admin_tv2_count

                                                    if logging_on and False:
                                                        logger.debug('lvlbase_admin_dict: ' + str( lvlbase_admin_dict) + ' ' + str(type(lvlbase_admin_dict)))

    if logging_on:
        logger.debug('schoolbase_pk is NOT None')

        """
        lvlbase_pk: 13 <class 'int'>
        lvlbase_dict: {'c': 'PKL', 
                       'total': {'total': {427: [102, 8, 30]}, 
                            1: {'c': 'Cur', 427: [51, 4, 15]}, 
                            2: {'c': 'Sxm', 427: [51, 4, 15]}
                            }, 
                        2: {'c': 'CUR01', 427: [51, 4, 15]}, 
                        35: {'c': 'SXM01', 427: [51, 4, 15]}} 
        """

        """
        examyear_dict_sample = {'total': {137: 513, 134: 63, 156: 63, 175: 63},
            'DUO': {'total': {137: 513, 134: 63, 156: 63, 175: 63},  # eteduo_dict: { 'total': {}, lang_dict: {}
                'nl': {'total': {137: 513, 134: 63, 156: 63, 175: 63},  # lang_dict: { 'total': {}, depbase_dict: {}
                    1: {'total': {137: 513, 134: 63, 156: 63, 175: 63},  # depbase_dict: { 'total': {}, lvlbase_dict: {}
                        12: {'total': {137: 90},  # lvlbase_dict: { 'total': {}, schoolbase_pk: {}
                             2: {137: [90, 5]}  #  schoolbase_pk: { subjbase_pk: [ subj_count, extra_count, tv2_count]
                             },
                        13: {'total': {134: 63, 137: 156, 156: 63, 175: 63},
                             2: {134: 63, 137: 156, 156: 63, 175: 63}
                             },
                        14: {'total': {137: 267},
                             2: {137: [267, 10]}
                             }
                    }
                }
            }
        }

    lvlbase_dict = {'c': 'PBL',
            'total': {430: [190, 66, 50], 440: [114, 56, 35], 435: [4, 13, 5]},
            'country': {
                39: {'c': 'SXMDOE', 430: [82, 8, 20], 440: [52, 8, 15]},
                23: {'c': 'CURETE', 430: [108, 12, 30], 440: [62, 13, 20], 435: [4, 6, 5]}},
            35: {'c': 'SXM01', 430: [82, 8, 20], 440: [52, 8, 15]},
             2: {'c': 'CUR01', 430: [82, 8, 20], 440: [52, 8, 15]},
             4: {'c': 'CUR03', 430: [26, 4, 10], 440: [10, 5, 5], 435: [4, 6, 5]},
            39: {'c': 'SXMDOE', 430: [0, 21, 0], 440: [0, 14, 0]},
            23: {'c': 'CURETE', 430: [0, 25, 0], 440: [0, 21, 0], 435: [0, 7, 0]}}

"""
    if logging_on:
        logger.debug('studsubj_count_dict: ' + str(json.dumps(count_dict, cls=af.LazyEncoder)))

    return count_dict, rows
# --- end of create_studsubj_count_dict


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
def create_envelop_studsubj_dict(sel_examyear_instance, sel_examperiod, request, schoolbase_pk_list, subjbase_pk_list):
    # PPR2022-08-23
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_studsubj_count_dict ----- ')
        logger.debug('    sel_examyear: ' + str(sel_examyear_instance))
        logger.debug('    schoolbase_pk_list: ' + str(schoolbase_pk_list))

    # this one is for printing labels: dict order: dep - lvl - subj - exam - lang - school
    # no count needed, happens when creating labels
    # ete/DUO not necessary, but let it stay if they want to include them in letter to cinfirm received exams

    #  create nested dict with subjects count per exam, lang, dep, lvl, school and subjbase_id
    #  all schools of CUR and SXM only submitted subjects, not deleted # PR2021-08-19
    #  add extra for ETE and DOE PR2021-09-25
    # called by: create_orderlist_xlsx, create_orderlist_per_school_xlsx, OrderlistsPublishView

    rows = create_studsubj_count_rows(sel_examyear_instance, sel_examperiod, request, schoolbase_pk_list, subjbase_pk_list)

    # TODO to be solved: group by si.ete_exam and si.otherlang goes wrong when sectors of one level have different otherlang PR2022-08-13

    school_envelop_studsubj_dict = {}

    for row in rows:
        if logging_on and False:
            logger.debug('row: ' + str(row))
        """
        row: {'subjbase_id': 133, 'ete_exam': True, 'id_key': '1_6_133_1', 'lang': 'nl', 'country_id': 1, 
        'sb_code': 'CUR01', 'lvl_abbrev': 'PBL', 'dep_abbrev': 'V.S.B.O.', 'subj_name': 'Administratie en commercie', 
        'subjbase_code': 'ac', 'schoolbase_id': 2, 'school_name': 'Ancilla Domini Vsbo',  'depbase_id': 1, 'lvlbase_id': 6, 
        'subj_count': 13, 'extra_count': 7, 'tv2_count': 5}
        """

# - get or create eteduo_dict
        ete_duo = 'ETE' if row.get('ete_exam', False) else 'DUO'
        if ete_duo not in school_envelop_studsubj_dict:
            school_envelop_studsubj_dict[ete_duo] = {}
        eteduo_dict = school_envelop_studsubj_dict[ete_duo]

# - get or create depbase_dict
        depbase_pk = row.get('depbase_id')

        if depbase_pk not in eteduo_dict:
            dep_abbrev = row.get('dep_abbrev')
            eteduo_dict[depbase_pk] = {'c': dep_abbrev}
        depbase_dict = eteduo_dict[depbase_pk]

# - get or create lvlbase_dict
        # value is '0' when lvlbase_id = None (Havo/Vwo)
        lvlbase_pk = row.get('lvlbase_id', 0)
        if lvlbase_pk is None:
            lvlbase_pk = 0
        if lvlbase_pk not in depbase_dict:
            lvl_abbrev = row.get('lvl_abbrev') or '-'
            depbase_dict[lvlbase_pk] = {'c': lvl_abbrev}
        lvlbase_dict = depbase_dict[lvlbase_pk]

# - get or create subjbase_dict
        subjbase_pk = row.get('subjbase_id')
        if subjbase_pk not in depbase_dict:
            subjbase_code = row.get('subjbase_code', '-')
            lvlbase_dict[subjbase_pk] = {'c': subjbase_code}
        subjbase_dict = lvlbase_dict[subjbase_pk]

# - get or create schoolbase_dict
        row_sb_pk = row.get('schoolbase_id')
        if row_sb_pk not in subjbase_dict:
            row_sb_code = row.get('sb_code', '-')  # for testing only
            subjbase_dict[row_sb_pk] = {'c': row_sb_code, 'count': 0, 'extra': 0, 'tv2': 0}
        schoolbase_dict = subjbase_dict[row_sb_pk]

        subj_count = row.get('subj_count')
        if subj_count:
            schoolbase_dict['count'] += subj_count
        extra_count = row.get('extra_count')
        if extra_count:
            schoolbase_dict['extra'] += extra_count
        tv2_count = row.get('tv2_count')
        if tv2_count:
            schoolbase_dict['tv2'] += tv2_count

    if logging_on:
        datalists_json = json.dumps(school_envelop_studsubj_dict, cls=af.LazyEncoder)
        logger.debug('_envelop_studsubj_dict: ' + str(datalists_json))


    """
    school_envelop_studsubj_dict: {'ETE': {1: {'c': 'V.S.B.O.', 6: {'c': 'PBL', 'total': {}, 'country': {}, 133: {'c': 'PBL'}, 2: {'c': 'CUR01'}, 155: {'c': 'PBL'}, 124: {'c': 'PBL'}, 113: {'c': 'PBL'}, 121: {'c': 'PBL'}, 131: {'c': 'PBL'}, 118: {'c': 'PBL'}, 123: {'c': 'PBL'}, 114: {'c': 'PBL'}}, 5: {'c': 'PKL', 'total': {}, 'country': {}, 113: {'c': 'PKL'}, 2: {'c': 'CUR01'}, 114: {'c': 'PKL'}, 133: {'c': 'PKL'}, 123: {'c': 'PKL'}, 118: {'c': 'PKL'}, 121: {'c': 'PKL'}, 155: {'c': 'PKL'}, 131: {'c': 'PKL'}, 124: {'c': 'PKL'}}, 4: {'c': 'TKL', 'total': {}, 'country': {}, 114: {'c': 'TKL'}, 2: {'c': 'CUR01'}, 118: {'c': 'TKL'}, 113: {'c': 'TKL'}, 124: {'c': 'TKL'}, 131: {'c': 'TKL'}, 120: {'c': 'TKL'}, 133: {'c': 'TKL'}}}, 'nl': {'total': {}}}, 'DUO': {1: {'c': 'V.S.B.O.', 4: {'c': 'TKL', 'total': {}, 'country': {}, 155: {'c': 'TKL'}, 2: {'c': 'CUR01'}, 121: {'c': 'TKL'}, 123: {'c': 'TKL'}}}, 'nl': {'total': {}}}}
[2022-08-23 19:43:24] DEBUG [subjects.orderlists.create_env
    """


    return school_envelop_studsubj_dict
# --- end of create_studsubj_count_dict



#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
def create_mapped_admin_dict(sel_examyear_instance):
    # PR2022-08-13
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_mapped_admin_dict ----- ')

# create mapped_admin_dict with key = country_id and value = row_dict
    mapped_admin_dict = {}
    sql_keys = {'ey_code_int': sel_examyear_instance.code, 'default_role': c.ROLE_064_ADMIN }
    sql_list = ["SELECT sb.country_id, sch.base_id AS sb_id, sb.code AS c,",
                "ey.order_extra_fixed, ey.order_extra_perc, ey.order_round_to,",
                "ey.order_tv2_divisor, ey.order_tv2_multiplier, ey.order_tv2_max,",
                "ey.order_admin_divisor, ey.order_admin_multiplier, ey.order_admin_max",

                "FROM schools_school AS sch",
                "INNER JOIN schools_schoolbase AS sb ON (sb.id = sch.base_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
                "WHERE ey.code = %(ey_code_int)s::INT",
                "AND sb.defaultrole = %(default_role)s::INT"
                ]
    sql = ' '.join(sql_list)

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)
        for row in rows:
            country_id = row.get('country_id')
            if country_id not in mapped_admin_dict:
                mapped_admin_dict[country_id] = row

    if logging_on:
        logger.debug('mapped_admin_dict: ' + str(mapped_admin_dict) + ' ' + str(type(mapped_admin_dict)))
        # mapped_admin_dict: {39: {'c': 'SXMDOE'}, 23: {'c': 'CURETE'}} <class 'dict'>

    return mapped_admin_dict
# - end of create_mapped_admin_dict


# /////////////////////////////////////////////////////////////////


def calc_extra_exams(subj_count, extra_fixed, extra_perc, round_to):  # PR2021-09-25
    # - function counts extra exams and examns tv2 per school / subject
    # - Note: values of extra_fixed, extra_perc, round_to are from table examyear,
    #         thus can be different for CUR and SXM schools

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- calc_extra_exams -------')
        logger.debug('subj_count:  ' + str(subj_count))
        logger.debug('extra_fixed: ' + str(extra_fixed))
        logger.debug('extra_perc:  ' + str(extra_perc))
        logger.debug('round_to:  ' + str(round_to))

    extra_count = 0
    if subj_count:
        total_not_rounded = subj_count + extra_fixed + (subj_count * extra_perc / 100)
        total_divided = total_not_rounded / round_to
        total_integer = int(total_divided)
        # total_frac = (total_divided - total_integer)
        total_roundup = total_integer + 1 if (total_divided - total_integer) else total_integer
        # total_roundup = total_frac_roundup * order_round_to
        extra_count = total_roundup * round_to - subj_count

        if logging_on:
            logger.debug('subj_count:  ' + str(subj_count))
            logger.debug('total_not_rounded: ' + str(total_not_rounded))
            logger.debug('total_divided:  ' + str(total_divided))
            logger.debug('total_integer:  ' + str(total_integer))
            logger.debug('total_frac: ' + str(total_divided - total_integer))
            logger.debug('total_roundup: ' + str(total_roundup))
            logger.debug('total_roundup:   ' + str(total_roundup))
            logger.debug('extra_count:   ' + str(extra_count))
            logger.debug('..........: ')

    return extra_count
# - end of calc_extra_exams


def calc_exams_tv02(subj_count, divisor, multiplier, max_exams):  # PR2021-09-25
    # - count examns tv2 per school / subject:
    # - 'multiplier' tv02-examns per 'divisor' tv01-examns, roundup to 'multiplier', with max of 'max_exams'
    # - Note: values of divisor, multiplier, max_exams are from table examyear,
    #         thus can be different for CUR and SXM schools

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- calc_exams_tv02 -------')
        logger.debug('subj_count:  ' + str(subj_count))
        logger.debug('divisor: ' + str(divisor))
        logger.debug('multiplier:  ' + str(multiplier))
        logger.debug('max_exams:  ' + str(max_exams))

    tv2_count = 0
    if subj_count:
        try:
            # PR2021-10-12 debug: gave ZeroDivisionError. "if divisor else 0" added.
            total_divided = subj_count / divisor if divisor else 0
            total_integer = int(total_divided)
            # total_frac = (total_divided - total_integer)
            total_roundup = total_integer + 1 if (total_divided - total_integer) else total_integer
            # total_roundup = total_frac_roundup * order_round_to
            tv2_count = total_roundup * multiplier

            if tv2_count > max_exams:
                tv2_count = max_exams

            if logging_on:
                logger.debug('subj_count:  ' + str(subj_count))
                logger.debug('total_divided:  ' + str(total_divided))
                logger.debug('total_integer:  ' + str(total_integer))
                logger.debug('total_frac: ' + str(total_divided - total_integer))
                logger.debug('total_roundup: ' + str(total_roundup))
                logger.debug('tv2_count:   ' + str(tv2_count))
                logger.debug('..........: ')

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    return tv2_count
# - end of calc_exams_tv02


def create_studsubj_count_rows(sel_examyear_instance, sel_examperiod, request, schoolbase_pk_list=None, subjbase_pk_list=None):
    # PR2021-08-19 PR2021-09-24 PR2022-08-13
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_studsubj_count_dict ----- ')

    #  create nested dict with subjects count per exam, lang, dep, lvl, school and subjbase_id
    #  all schools of CUR and SXM only submitted subjects, not deleted # PR2021-08-19
    #  add extra for ETE and DOE PR2021-09-25
    # called by: create_orderlist_xlsx, create_orderlist_per_school_xlsx, OrderlistsPublishView

# - get schoolbase_id of ETE and DOE - necessary to calculate extra exams for ETE and DOE

# - create mapped_admin_dict with key = country_id and value = row_dict
    # mapped_admin_dict: key = country_id, value = {'country_id': 2, 'sb_id': 34, 'c': 'SXMDOE', ...
    mapped_admin_dict = create_mapped_admin_dict(sel_examyear_instance)
    """
     mapped_admin_dict: {
        1: {'country_id': 1, 'sb_id': 23, 'c': 'CURETE', 'order_extra_fixed': 8, 'order_extra_perc': 8, 'order_round_to': 8, 'order_tv2_divisor': 88, 'order_tv2_multiplier': 8, 'order_tv2_max': 88, 'order_admin_divisor': 88, 'order_admin_multiplier': 8, 'order_admin_max': 88}, 
        2: {'country_id': 2, 'sb_id': 34, 'c': 'SXMDOE', 'order_extra_fixed': 2, 'order_extra_perc': 5, 'order_round_to': 5, 'order_tv2_divisor': 25, 'order_tv2_multiplier': 5, 'order_tv2_max': 25, 'order_admin_divisor': 100, 'order_admin_multiplier': 5, 'order_admin_max': 25}} 
    """

    requsr_country_pk = request.user.country.pk
    sql_keys = {'ey_code_int': sel_examyear_instance.code, 'ep': sel_examperiod, 'requsr_country_id': requsr_country_pk}

# - set filter on ETE / DUO exams when country is CUR and when country = SXM
    # - when request.user = ETE: add all ETE-exams of CUR and SXM, and DUO-exams of CUR schools, but skip DUO-exams of SXM schools
    # - when request.user = SXM: show only SXM schools, show ETE exams and DUO exams
    #  when print per school: show all
    skip_ete_or_duo = ''
    if request.user.country.abbrev.lower() == 'cur':
    # when print orderlist ETE
        # - when request,user = ETE: add all ETE-exams of CUR and SXM, and DUO-exams of CUR schools, but skip DUO-exams of SXM schools
        # - WHERE is_ete_exam OR (NOT is_ete_exam AND country = requsr_country)
        skip_ete_or_duo = "AND ( (si.ete_exam) OR (NOT si.ete_exam AND ey.country_id = %(requsr_country_id)s::INT ))"

    elif request.user.country.abbrev.lower() == 'sxm':
    # when print orderlist DOE
        # - when request.user = SXM: show only SXM schools, show ETE exams and DUO exams
        # -  WHERE country = requsr_country
        skip_ete_or_duo = "AND (ey.country_id = %(requsr_country_id)s::INT )"

    filter_subjbase = ''
    if subjbase_pk_list:
        sql_keys['subjbase_arr'] = subjbase_pk_list
        filter_subjbase = "AND subjbase.id IN (SELECT UNNEST(%(subjbase_arr)s::INT[]))"

# - create subquery with count of subjects
    sql_studsubj_agg_list = [
        "SELECT st.school_id, ey.country_id as ey_country_id, dep.base_id AS depbase_id, lvl.base_id AS lvlbase_id,",
        "sch.otherlang AS sch_otherlang,",

        "CONCAT_WS ('_', dep.base_id, COALESCE(lvl.base_id, 0), subj.base_id, ",
        "%(ep)s::INT",
        ", CASE WHEN si.ete_exam THEN 1 ELSE 0 END) AS id_key,",
        "dep.sequence AS dep_sequence, lvl.sequence AS lvl_sequence, subjbase.code AS subjbase_code, ",  # for order by
        "depbase.code AS depbase_code,",  # for testing only, must also delete from group_by
        "lvl.abbrev AS lvl_abbrev,",  # for testing only, must also delete from group_by
        "subj.name_nl AS subj_name,",  # for testing only, must also delete from group_by

        #PR2021-10-12 subj.otherlang replaced by si.otherlang
        # was: "subj.base_id AS subjbase_id, si.ete_exam, subj.otherlang AS subj_otherlang, count(*) AS subj_count",
        "subj.base_id AS subjbase_id, si.ete_exam, si.otherlang AS si_otherlang, count(*) AS subj_count",

        "FROM students_studentsubject AS studsubj",
        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

        "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
        "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
        "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
        "INNER JOIN schools_departmentbase AS depbase ON (depbase.id = dep.base_id)", # for testing only, depbase can be deleted
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",

# - show only exams that are not deleted
        "WHERE NOT studsubj.tobedeleted",
# - show only published exams
        "AND studsubj.subj_published_id IS NOT NULL",
# - show only exams that have a central exam
        "AND NOT si.weight_ce = 0",
# - skip DUO exams for SXM schools when CUR
        skip_ete_or_duo,
# - filter subjects if subjbase_pk_list has value
        filter_subjbase,

        # PR2021-10-12 subj.otherlang replaced by si.otherlang
        #  was: "GROUP BY st.school_id, ey.country_id, dep.base_id, lvl.base_id, lvl.abbrev, sch.otherlang, subj.base_id, si.ete_exam, subj.otherlang"
        "GROUP BY st.school_id, ey.country_id, dep.base_id, lvl.base_id,",
        "dep.sequence, lvl.sequence, subjbase.code,"
        "depbase.code, lvl.abbrev, subj.name_nl, subjbase.code,", # for testing only, must also delete from group_by
        "sch.otherlang, subj.base_id, si.ete_exam, si.otherlang"
    ]

    # TODO to be solved: group by si.ete_exam and si.otherlang goes wrong when sectors of one level have different otherlang PR2022-08-13
    sql_studsubj_agg = ' '.join(sql_studsubj_agg_list)

# - create query with row per school and inner join with subquery count_studsubj
    sql_list = ["WITH studsubj AS (", sql_studsubj_agg, ")",
                "SELECT studsubj.subjbase_id, studsubj.ete_exam, studsubj.id_key, studsubj.subjbase_id,",

                # PR2021-10-12 subj.otherlang replaced by si.otherlang
                "CASE WHEN studsubj.si_otherlang IS NULL OR studsubj.sch_otherlang IS NULL THEN 'nl' ELSE",
                "CASE WHEN POSITION(studsubj.sch_otherlang IN studsubj.si_otherlang) > 0 ",
                "THEN studsubj.sch_otherlang ELSE 'nl' END END AS lang,",

                "cntr.id AS country_id,",  # PR2021-09-24 added, for extra exams ETE and DoE
                "sb.code AS sb_code, studsubj.lvl_abbrev, studsubj.depbase_code,",  # for testing only
                "studsubj.subj_name,",  # for testing only
                "sch.base_id AS schoolbase_id, sch.name AS school_name,",
                "studsubj.depbase_id, studsubj.lvlbase_id, studsubj.subj_count,",
                "studsubj.dep_sequence, studsubj.lvl_sequence, studsubj.subjbase_code",

                "FROM schools_school AS sch",
                "INNER JOIN schools_schoolbase AS sb ON (sb.id = sch.base_id)",
                "INNER JOIN schools_country AS cntr ON (cntr.id = sb.country_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
                "LEFT JOIN studsubj ON (studsubj.school_id = sch.id)",
# - show only exams of this exam year
                "WHERE ey.code = %(ey_code_int)s::INT"
                ]

# - filter on parameter schoolbase_pk_list when it has value

    if schoolbase_pk_list:
        sql_keys['sb_arr'] = schoolbase_pk_list
        sql_list.append("AND sb.id IN ( SELECT UNNEST(%(sb_arr)s::INT[]) )")

    sql_list.append("ORDER BY studsubj.dep_sequence, LOWER(studsubj.subjbase_code), studsubj.lvl_sequence, LOWER(sb.code)")

    sql = ' '.join(sql_list)

    #if logging_on:
        #logger.debug('sql_keys: ' + str(sql_keys))
        #logger.debug('sql: ' + str(sql))
        #logger.debug('connection.queries: ' + str(connection.queries))

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_keys)
        rows = af.dictfetchall(cursor)

    for row in rows:

        # admin_id is schoolbase_id of school of ETE / DOE
        #admin_id, admin_code = None, None
        order_extra_fixed, order_extra_perc, order_round_to = None, None, None
        order_tv2_divisor, order_tv2_multiplier, order_tv2_max = None, None, None

        country_id = row.get('country_id')
        if country_id in mapped_admin_dict:
            mapped_country_dict = mapped_admin_dict[country_id]
            #admin_id = mapped_country_dict.get('sb_id')
            #admin_code = mapped_country_dict.get('c')

            order_extra_fixed = mapped_country_dict.get('order_extra_fixed')
            order_extra_perc = mapped_country_dict.get('order_extra_perc')
            order_round_to = mapped_country_dict.get('order_round_to')

            order_tv2_divisor = mapped_country_dict.get('order_tv2_divisor')
            order_tv2_multiplier = mapped_country_dict.get('order_tv2_multiplier')
            order_tv2_max = mapped_country_dict.get('order_tv2_max')

            if logging_on and False:
                logger.debug('mapped_country_dict: ' + str(mapped_country_dict))
                #logger.debug('admin_code: ' + str(admin_code))
                logger.debug('order_extra_fixed: ' + str(order_extra_fixed))
                logger.debug('order_extra_perc: ' + str(order_extra_perc))
                logger.debug('order_round_to: ' + str(order_round_to))

# +++ count extra exams and examns tv2 per school / subject
        subj_count = row.get('subj_count', 0)

        extra_count = 0
        tv2_count = 0
        if subj_count:
            extra_count = calc_extra_exams(subj_count, order_extra_fixed, order_extra_perc, order_round_to)
            tv2_count = calc_exams_tv02(subj_count, order_tv2_divisor, order_tv2_multiplier, order_tv2_max)

    # - add extra_count and tv2_count to row, for enveloplabel print
        row['extra_count'] = extra_count
        row['tv2_count'] = tv2_count

        if logging_on :
            logger.debug('row: ' + str(row))
        """
        row: {'subjbase_id': 121, 'ete_exam': True, 'lang': 'nl', 'country_id': 1, 'sb_code': 'CUR05', 
        'lvl_abbrev': 'PKL', 'subj_name': 'Wiskunde', 'schoolbase_id': 6, 'depbase_id': 1, 'lvlbase_id': 5, 
        'subj_count': 32, 'extra_count': 8, 'tv2_count': 10}
        """

        if logging_on and False:
            logger.debug('........subj_count: ' + str(subj_count))
            logger.debug('.......extra_count: ' + str(extra_count))
            logger.debug('.........tv2_count: ' + str(tv2_count))

    return rows
# - end of create_studsubj_count_rows
