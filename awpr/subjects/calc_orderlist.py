# PR2022-08-13
import json

from django.db import connection

from awpr import settings as s
from awpr import constants as c
from awpr import functions as af

import logging
logger = logging.getLogger(__name__)


def create_studsubj_count_dict(sel_examyear_instance, sel_examperiod, request, prm_schoolbase_pk=None):
    # PR2021-08-19 PR2021-09-24 PR2022-08-13 PR2022-09-25
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_studsubj_count_dict ----- ')

    #  create nested dict with subjects count per exam, lang, dep, lvl, school and subjbase_id
    #  all schools of CUR and SXM, only submitted subjects, not deleted # PR2021-08-19
    #  add extra for ETE and DOE PR2021-09-25

    # called by:
    #   create_orderlist_per_school_xlsx
    #   create_orderlist_xlsx
    #   OrderlistsPublishView

# - get schoolbase_id of ETE and DOE - necessary to calculate extra exams for ETE and DOE

# - create mapped_admin_dict with key = country_id and value = row_dict
    # mapped_admin_dict: key = country_id, value = {'country_id': 2, 'sb_id': 34, 'c': 'SXMDOE', ...
    mapped_admin_dict = create_mapped_admin_dict(sel_examyear_instance)
    """
     mapped_admin_dict: {
        1: {'country_id': 1, 'sb_id': 23, 'c': 'CURETE', 'order_extra_fixed': 8, 'order_extra_perc': 8, 'order_round_to': 8, 'order_tv2_divisor': 88, 'order_tv2_multiplier': 8, 'order_tv2_max': 88, 'order_admin_divisor': 88, 'order_admin_multiplier': 8, 'order_admin_max': 88}, 
        2: {'country_id': 2, 'sb_id': 34, 'c': 'SXMDOE', 'order_extra_fixed': 2, 'order_extra_perc': 5, 'order_round_to': 5, 'order_tv2_divisor': 25, 'order_tv2_multiplier': 5, 'order_tv2_max': 25, 'order_admin_divisor': 100, 'order_admin_multiplier': 5, 'order_admin_max': 25}} 
    """

# - count number of sudsubj. i.e. number of students with that subject
    schoolbase_pk_list = [prm_schoolbase_pk] if prm_schoolbase_pk else None
    rows = create_studsubj_count_rows(
        sel_examyear_instance=sel_examyear_instance,
        sel_examperiod=sel_examperiod,
        request=request,
        schoolbase_pk_list=schoolbase_pk_list
    )

    # TODO to be solved: group by si.ete_exam and si.otherlang goes wrong when sectors of one level have different otherlang PR2022-08-13

    # TODO create dict with studsubj_count + extra for receipt. Group by school/dep/levl and agg by exam, count = studsubj_count + extra PR2022-09-04
    count_dict = {'total': {}}
    receipt_dict = {}
    """
    row contains subj_count (= number of studsubj) and exam_count(= number of exams of this 
    row is grouped by school_id, country_id, depbase_id, lvlbase_id,",
        subjbase_id, ete_exam, sch.otherlang, si.otherlang"
    """
    for row in rows:
        """
        row: {'subjbase_id': 131, 'ete_exam': True, 'id_key': '1_5_131_1_1', 'lang': 'nl',
         'country_id': 1, 'sb_code': 'CUR02', 'lvl_abbrev': 'PKL', 'depbase_code': 'Vsbo', 
         'subjbase_code': 'zwi', 'subj_name': 'Zorg & Welzijn intrasectoraal', 
         'schoolbase_id': 3, 'school_name': 'Skol Avansá Amador Nita', 'depbase_id': 1, 'lvlbase_id': 5, 
         'dep_sequence': 1, 'lvl_sequence': 2,
         
         'subj_count': 4, 'exam_count': 2,  'extra_count': 6, 'tv2_count': 5}
        """

        # admin_id is schoolbase_id of school of ETE / DOE
        admin_id, admin_code = None, None

        country_id = row.get('country_id')
        if country_id in mapped_admin_dict:
            mapped_country_dict = mapped_admin_dict[country_id]
            admin_id = mapped_country_dict.get('sb_id')
            admin_code = mapped_country_dict.get('c')

# +++ get number of exams, extra exams and exams tv2 per school / subject
        subj_count = row.get('subj_count') or 0
        extra_count = row.get('extra_count') or 0
        tv2_count = row.get('tv2_count') or 0

        """
        row: {'subjbase_id': 121, 'ete_exam': True, 'lang': 'nl', 'country_id': 1, 'sb_code': 'CUR05', 
                'lvl_abbrev': 'PKL', 'subj_name': 'Wiskunde', 'schoolbase_id': 6, 'depbase_id': 1, 'lvlbase_id': 5, 
                'subj_count': 32, 'extra_count': 8, 'tv2_count': 10}
        """

# +++ store info also in count_dict
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
            # depbase_dict has no key 'total'
            lang_dict[depbase_pk] = {'c': row.get('depbase_code')}
        depbase_dict = lang_dict[depbase_pk]

    # - get lvlbase_dict
        # value is '0' when lvlbase_id = None (Havo/Vwo)
        lvlbase_pk = row.get('lvlbase_id') or 0
        if lvlbase_pk not in depbase_dict:
            lvl_abbrev = row.get('lvl_abbrev', '-')
            depbase_dict[lvlbase_pk] = {'c': lvl_abbrev, 'total': {}, 'admin_total': {}}
        lvlbase_dict = depbase_dict[lvlbase_pk]

    # - get schoolbase_dict
        row_sb_pk = row.get('schoolbase_id') or 0
        if row_sb_pk not in lvlbase_dict:
            row_sb_code = row.get('sb_code', '-')  # for testing only
            lvlbase_dict[row_sb_pk] = {'c': row_sb_code}
        schoolbase_dict = lvlbase_dict[row_sb_pk]

    # - calculate schoolbase_dict total
        subjbase_pk = row.get('subjbase_id') or 0
        if subjbase_pk not in schoolbase_dict:
            schoolbase_dict[subjbase_pk] = [subj_count, extra_count, tv2_count]
        else:
            schoolbase_dict[subjbase_pk][0] += subj_count
            schoolbase_dict[subjbase_pk][1] += extra_count
            schoolbase_dict[subjbase_pk][2] += tv2_count

# +++ store info also in receipt_dict  PR2022-09-30
    # - add eteduo_dict to receipt_dict ( DUO not in use, but let it stay )
        if ete_duo not in receipt_dict:
            receipt_dict[ete_duo] = {}
        receipt_eteduo_dict = receipt_dict[ete_duo]

    # - add schoolbase_dict to receipt_eteduo_dict
        if row_sb_pk not in receipt_eteduo_dict:
            receipt_eteduo_dict[row_sb_pk] = {'c': row.get('sb_code') or '-'}  # for testing only
        receipt_schoolbase_dict = receipt_eteduo_dict[row_sb_pk]

    # there is no separate lang_dict in receipt_dict

    # - add depbase_dict to receipt_schoolbase_dict
        if depbase_pk not in receipt_schoolbase_dict:
            receipt_schoolbase_dict[depbase_pk] = {'c': row.get('depbase_code') or '-'}
        receipt_depbase_dict = receipt_schoolbase_dict[depbase_pk]

    # - add lvlbase_dict to receipt_dict
        if lvlbase_pk not in receipt_depbase_dict:
            receipt_depbase_dict[lvlbase_pk] = {'c': row.get('lvl_abbrev') or '-'}
        receipt_lvlbase_dict = receipt_depbase_dict[lvlbase_pk]

    # - calculate receipt_lvlbase_dict total
        if subjbase_pk not in receipt_lvlbase_dict:
            receipt_lvlbase_dict[subjbase_pk] = [subj_count, extra_count, tv2_count]
        else:
            receipt_lvlbase_dict[subjbase_pk][0] += subj_count
            receipt_lvlbase_dict[subjbase_pk][1] += extra_count
            receipt_lvlbase_dict[subjbase_pk][2] += tv2_count

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
            lvlbase_admin_total = lvlbase_dict.get('admin_total')
            if admin_id not in lvlbase_admin_total:
                lvlbase_admin_total[admin_id] = {'c': admin_code}
            admin_total = lvlbase_admin_total[admin_id]

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
# - end of for row in rows

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
                                            'admin_total': {23: {'c': 'CURETE', 121: [192, 48, 60], 
                                                        34: {'c': 'SXMDOE', 129: [8, 7, 5], 114: [70, 20, 20], 
                                            6: {'c': 'CUR05', 121: [32, 8, 10], 133: [24, 6, 5],
                                        """

                                        lvlbase_admin_total_dict = lvlbase_dict.get('admin_total')
                                        lvlbase_total_dict = lvlbase_dict.get('total')
                                        eteduo_total_dict = eteduo_dict.get('total')
                                        examyear_total_dict = count_dict.get('total')

                                        if lvlbase_admin_total_dict:
                                            if logging_on and False:
                                                logger.debug('lvlbase_admin_total_dict: ' + str(lvlbase_admin_total_dict) + ' ' + str(type(lvlbase_admin_total_dict)))
                                                """
                                                lvlbase_admin_total_dict: {
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

                            # - lookup 'admin_total_dict' in lvlbase_admin_total_dict, with key: admin_pk
                                                # admin_total_dict contains subject_count of all subjects of this admin, this level
                                                if admin_pk in lvlbase_admin_total_dict:
                                                    admin_total_dict = lvlbase_admin_total_dict.get(admin_pk)
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

                                                    #if logging_on:
                                                    #    logger.debug('lvlbase_admin_dict: ' + str(lvlbase_admin_dict) + ' ' + str(type(lvlbase_admin_dict)))
                                                    """
                                                    lvlbase_admin_dict = {'c': 'CURETE', 430: [0, 25, 0], 440: [0, 21, 0], 435: [0, 7, 0]}}
                                                    """
                            # - loop through subjects in admin_total_dict
                                                    for subjbase_pk, count_list in admin_total_dict.items():
                                                        #if logging_on:
                                                        #    logger.debug(' >>> subjbase_pk: ' + str(subjbase_pk) + ' count_list: ' + str(count_list))
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

                                                    #if logging_on:
                                                    #    logger.debug('lvlbase_admin_dict: ' + str( lvlbase_admin_dict) + ' ' + str(type(lvlbase_admin_dict)))

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
        logger.debug('receipt_dict: ' + str(json.dumps(receipt_dict, cls=af.LazyEncoder)))

    """
    studsubj_count_dict: {
        "total": {"133": [462, 263, 215], "123": [553, 217, 240], "126": [64, 56, 35], "155": [763, 242, 305], "114": [1308, 247, 360], "132": [58, 77, 60], "129": [92, 88, 50], "124": [426, 164, 185], "125": [9, 11, 10], "127": [8, 12, 10], "122": [414, 121, 145], "134": [136, 54, 55], "113": [1309, 246, 360], "118": [1768, 282, 450], "120": [409, 151, 185], "137": [163, 47, 60], "121": [944, 216, 300], "131": [369, 231, 170], "140": [137, 38, 45], "158": [163, 37, 55], "144": [2, 3, 5], "167": [543, 67, 125], "160": [55, 20, 25], "145": [246, 54, 65], "146": [131, 34, 50], "138": [139, 41, 55], "165": [543, 67, 125], "139": [195, 45, 60], "159": [172, 43, 55], "149": [338, 52, 90], "150": [133, 37, 50], "156": [1, 4, 5], "0": [0, 0, 0]}, 
        "ETE": {
            "total": {"133": [462, 263, 215], "123": [215, 110, 110], "126": [64, 56, 35], "155": [260, 130, 140], "114": [1308, 247, 360], "132": [58, 77, 60], "129": [92, 88, 50], "124": [426, 164, 185], "125": [9, 11, 10], "127": [8, 12, 10], "122": [222, 63, 75], "113": [1309, 246, 360], "118": [1768, 282, 450], "120": [409, 151, 185], "137": [163, 47, 60], "121": [459, 136, 165], "131": [369, 231, 170], "145": [246, 54, 65], "146": [131, 34, 50], "165": [543, 67, 125], "159": [172, 43, 55]}, 
            "nl": {
                "total": {}, 
                "1": {"c": "Vsbo", 
                    "6": {"c": "PBL", 
                        "total": {"133": [57, 63, 40], "123": [70, 40, 35], "126": [39, 31, 20], "155": [84, 36, 40], "114": [297, 78, 90], "132": [22, 28, 15], "129": [35, 45, 25], "124": [48, 32, 30], "125": [4, 6, 5], "127": [5, 5, 5], "122": [93, 27, 35], "113": [294, 76, 90], "118": [260, 60, 75], "120": [41, 44, 40], "121": [162, 43, 50], "131": [65, 65, 35]}, 
                        "admin_total": {
                            "23": {"c": "CURETE", "133": [57, 63, 40], "123": [70, 40, 35], "126": [39, 31, 20], "155": [84, 36, 40], "114": [259, 61, 75], "132": [22, 28, 15], "129": [35, 45, 25], "124": [48, 32, 30], "125": [4, 6, 5], "127": [5, 5, 5], "122": [93, 27, 35], "113": [260, 60, 75], "118": [260, 60, 75], "120": [41, 44, 40], "121": [162, 43, 50], "131": [65, 65, 35]}, 
                            "34": {"c": "SXMDOE", "114": [38, 12, 10], "113": [34, 11, 10]}}, 
                        "2": {"c": "CUR01", "133": [17, 13, 5], "123": [22, 8, 5], "155": [17, 3, 5], "114": [39, 6, 10], "124": [22, 8, 5], "113": [39, 6, 10], "118": [39, 6, 10], "121": [17, 3, 5], "131": [22, 8, 5]}, 
                        "3": {"c": "CUR02", "133": [5, 5, 5], "123": [11, 4, 5], "155": [5, 5, 5], "114": [16, 4, 5], "124": [8, 7, 5], "113": [16, 4, 5], "118": [16, 4, 5], "120": [4, 6, 5], "121": [4, 6, 5], "131": [11, 9, 5]}, 
                     "5": {"c": "PKL", "total": {"133": [104, 86, 45], "123": [91, 39, 40], "126": [25, 25, 15], "155": [112, 53, 50], "114": [395, 80, 120], "132": [8, 22, 15], "129": [57, 43, 25], "124": [78, 37, 40], "125": [5, 5, 5], "127": [3, 7, 5], "122": [125, 30, 35], "113": [399, 81, 120], "118": [349, 66, 100], "120": [70, 40, 45], "121": [192, 48, 65], "131": [89, 71, 40]}, "admin_total": {"23": {"c": "CURETE", "133": [104, 86, 45], "123": [91, 39, 40], "126": [25, 25, 15], "155": [112, 53, 50], "114": [345, 65, 100], "132": [8, 22, 15], "129": [57, 43, 25], "124": [78, 37, 40], "125": [5, 5, 5], "127": [3, 7, 5], "122": [125, 30, 35], "113": [349, 66, 100], "118": [349, 66, 100], "120": [70, 40, 45], "121": [192, 48, 65], "131": [89, 71, 40]}, "34": {"c": "SXMDOE", "114": [50, 10, 15], "113": [50, 10, 15]}}, "2": {"c": "CUR01", "133": [18, 12, 5], "123": [26, 4, 10], "155": [18, 7, 5], "114": [44, 6, 10], "124": [26, 4, 10], "113": [44, 6, 10], "118": [44, 6, 10], "121": [18, 7, 5], "131": [26, 14, 10]}, "3": {"c": "CUR02", "133": [2, 8, 5], "123": [4, 6, 5], "155": [2, 3, 5], "114": [6, 4, 5], "124": [2, 3, 5], "113": [6, 4, 5], "118": [6, 4, 5], "120": [1, 4, 5], "121": [3, 7, 5], "131": [4, 6, 5]}, "4": {"c": "CUR03", "133": [3, 7, 5], "123": [8, 7, 5], "126": [1, 9, 5], "155": [3, 7, 5], "114": [27, 8, 10], "129": [4, 6, 5], "124": [4, 6, 5], "122": [16, 4, 5], "113": [27, 8, 10], "118": [27, 8, 10], "120": [2, 3, 5], "121": [21, 4, 5], "131": [8, 12, 5]}, "5": {"c": "CUR04", "133": [1, 9, 5], "123": [9, 6, 5], "155": [3, 7, 5], "114": [12, 3, 5], "132": [2, 8, 5], "124": [9, 6, 5], "113": [12, 3, 5], "118": [12, 3, 5], "120": [3, 7, 5], "131": [7, 13, 5]}, "6": {"c": "CUR05", "133": [25, 15, 5], "123": [20, 5, 5], "155": [30, 5, 10], "114": [67, 8, 15], "132": [5, 5, 5], "129": [14, 6, 5], "124": [20, 5, 5], "127": [3, 7, 5], "122": [17, 3, 5], "113": [67, 8, 15], "118": [67, 8, 15], "120": [21, 4, 5], "121": [26, 4, 10], "131": [20, 10, 5]}, "8": {"c": "CUR08", "133": [4, 6, 5], "123": [9, 6, 5], "155": [5, 5, 5], "114": [14, 6, 5], "132": [1, 9, 5], "124": [8, 7, 5], "113": [14, 6, 5], "118": [14, 6, 5], "120": [2, 3, 5], "121": [4, 6, 5], "131": [9, 11, 5]}, "9": {"c": "CUR09", "133": [18, 12, 5], "123": [15, 5, 5], "155": [18, 7, 5], "114": [47, 8, 10], "129": [14, 6, 5], "124": [9, 6, 5], "122": [14, 6, 5], "113": [47, 8, 10], "118": [47, 8, 10], "120": [9, 6, 5], "121": [29, 6, 10], "131": [15, 5, 5]}, "11": {"c": "CUR11", "133": [20, 10, 5], "126": [14, 6, 5], "155": [20, 5, 5], "114": [76, 9, 20], "129": [18, 12, 5], "122": [56, 9, 15], "113": [76, 9, 20], "118": [76, 9, 20], "120": [20, 5, 5], "121": [56, 9, 15]}, "12": {"c": "CUR12", "133": [13, 7, 5], "126": [10, 10, 5], "155": [13, 7, 5], "114": [35, 5, 10], "129": [7, 13, 5], "125": [5, 5, 5], "122": [22, 8, 5], "113": [35, 5, 10], "118": [35, 5, 10], "121": [35, 5, 10]}, "10": {"c": "CUR10", "114": [11, 4, 5], "113": [15, 5, 5], "118": [15, 5, 5], "120": [10, 5, 5]}, "20": {"c": "CUR20", "114": [6, 4, 5], "113": [6, 4, 5], "118": [6, 4, 5], "120": [2, 3, 5]}, "31": {"c": "SXM02", "114": [17, 3, 5], "113": [17, 3, 5]}, "32": {"c": "SXM03", "114": [33, 7, 10], "113": [33, 7, 10]}, "23": {"c": "CURETE", "133": [0, 0, 0], "123": [0, 0, 0], "126": [0, 0, 0], "155": [0, 0, 0], "114": [0, 0, 0], "132": [0, 0, 0], "129": [0, 0, 0], "124": [0, 0, 0], "125": [0, 0, 0], "127": [0, 0, 0], "122": [0, 0, 0], "113": [0, 0, 0], "118": [0, 0, 0], "120": [0, 0, 0], "121": [0, 0, 0], "131": [0, 0, 0]}, "34": {"c": "SXMDOE", "114": [0, 5, 5], "113": [0, 5, 5]}}, 
                "2": {"c": "Havo", 
                    "0": {"c": null, "total": {"145": [213, 37, 45], "146": [82, 23, 30], "165": [461, 44, 95], "118": [461, 44, 95], "159": [159, 31, 40]}, "admin_total": {"23": {"c": "CURETE", "145": [213, 37, 45], "146": [82, 23, 30], "165": [461, 44, 95], "118": [461, 44, 95], "159": [159, 31, 40]}}, "15": {"c": "CUR15", "145": [43, 7, 10], "146": [28, 7, 10], "165": [109, 11, 25], "118": [109, 11, 25], "159": [44, 6, 10]}, "16": {"c": "CUR16", "145": [47, 8, 10], "146": [27, 8, 10], "165": [133, 12, 25], "118": [133, 12, 25], "159": [53, 7, 15]}, "17": {"c": "CUR17", "145": [75, 10, 15], "146": [20, 5, 5], "165": [140, 10, 25], "118": [140, 10, 25], "159": [18, 7, 5]}, "18": {"c": "CUR18", "145": [24, 6, 5], "165": [31, 4, 10], "118": [31, 4, 10], "159": [24, 6, 5]}, "19": {"c": "CUR19", "145": [24, 6, 5], "146": [7, 3, 5], "165": [48, 7, 10], "118": [48, 7, 10], "159": [20, 5, 5]}, "23": {"c": "CURETE", "145": [0, 0, 0], "146": [0, 0, 0], "165": [0, 0, 0], "118": [0, 0, 0], "159": [0, 0, 0]}}}, 
                "3": {"c": "Vwo", 
                    "0": {"c": null, "total": {"145": [33, 17, 20], "146": [49, 11, 20], "165": [82, 23, 30], "118": [82, 23, 30], "159": [13, 12, 15]}, "admin_total": {"23": {"c": "CURETE", "145": [33, 17, 20], "146": [49, 11, 20], "165": [82, 23, 30], "118": [82, 23, 30], "159": [13, 12, 15]}}, "15": {"c": "CUR15", "145": [15, 5, 5], "146": [26, 4, 10], "165": [34, 6, 10], "118": [34, 6, 10], "159": [7, 3, 5]}, "16": {"c": "CUR16", "145": [12, 3, 5], "146": [16, 4, 5], "165": [33, 7, 10], "118": [33, 7, 10], "159": [4, 6, 5]}, "18": {"c": "CUR18", "145": [2, 3, 5], "165": [3, 7, 5], "118": [3, 7, 5], "159": [2, 3, 5]}, "19": {"c": "CUR19", "145": [4, 6, 5], "146": [7, 3, 5], "165": [12, 3, 5], "118": [12, 3, 5]}, "23": {"c": "CURETE", "145": [0, 0, 0], "146": [0, 0, 0], "165": [0, 0, 0], "118": [0, 0, 0], "159": [0, 0, 0]}}}}, 
            "pa": {"total": {}, "1": {"c": "Vsbo", "6": {"c": "PBL", "total": {"133": [6, 14, 10], "123": [7, 3, 5], "155": [6, 9, 10], "124": [6, 4, 5], "121": [7, 3, 5], "131": [7, 13, 5]}, "admin_total": {"23": {"c": "CURETE", "133": [6, 14, 10], "123": [7, 3, 5], "155": [6, 9, 10], "124": [6, 4, 5], "121": [7, 3, 5], "131": [7, 13, 5]}}, "10": {"c": "CUR10", "133": [5, 5, 5], "123": [7, 3, 5], "155": [5, 5, 5], "124": [6, 4, 5], "121": [7, 3, 5], "131": [7, 13, 5]}, "20": {"c": "CUR20", "133": [1, 9, 5], "155": [1, 4, 5]}, "23": {"c": "CURETE", "133": [0, 0, 0], "123": [0, 0, 0], "155": [0, 0, 0], "124": [0, 0, 0], "121": [0, 0, 0], "131": [0, 0, 0]}}, 
            "5": {"c": "PKL", "total": {"133": [8, 22, 10], "123": [9, 6, 5], "155": [8, 7, 10], "124": [9, 6, 5], "122": [4, 6, 5], "121": [10, 10, 10], "131": [9, 11, 5]}, "admin_total": {"23": {"c": "CURETE", "133": [8, 22, 10], "123": [9, 6, 5], "155": [8, 7, 10], "124": [9, 6, 5], "122": [4, 6, 5], "121": [10, 10, 10], "131": [9, 11, 5]}}, "10": {"c": "CUR10", "133": [6, 14, 5], "123": [9, 6, 5], "155": [6, 4, 5], "124": [9, 6, 5], "121": [6, 4, 5], "131": [9, 11, 5]}, "20": {"c": "CUR20", "133": [2, 8, 5], "155": [2, 3, 5], "122": [4, 6, 5], "121": [4, 6, 5]}, "23": {"c": "CURETE", "133": [0, 0, 0], "123": [0, 0, 0], "155": [0, 0, 0], "124": [0, 0, 0], "122": [0, 0, 0], "121": [0, 0, 0], "131": [0, 0, 0]}}, 
            "4": {"c": "TKL", "total": {"133": [11, 9, 10], "124": [8, 7, 5], "137": [22, 8, 10], "131": [6, 4, 5]}, "admin_total": {"23": {"c": "CURETE", "133": [11, 9, 10], "124": [8, 7, 5], "137": [22, 8, 10], "131": [6, 4, 5]}}, "10": {"c": "CUR10", "133": [6, 4, 5], "124": [8, 7, 5], "137": [16, 4, 5], "131": [6, 4, 5]}, "20": {"c": "CUR20", "133": [5, 5, 5], "137": [6, 4, 5]}, "23": {"c": "CURETE", "133": [0, 0, 0], "124": [0, 0, 0], "137": [0, 0, 0], "131": [0, 0, 0]}}}}, 
            "en": {"total": {}, "1": {"c": "Vsbo", "6": {"c": "PBL", "total": {"133": [20, 10, 10], "123": [11, 9, 10], "155": [27, 13, 15], "132": [7, 8, 10], "124": [11, 9, 10], "121": [38, 17, 15], "131": [11, 9, 10]}, "admin_total": {"34": {"c": "SXMDOE", "133": [20, 5, 5], "123": [11, 4, 5], "155": [27, 8, 10], "132": [7, 3, 5], "124": [11, 4, 5], "121": [38, 12, 10], "131": [11, 4, 5]}}, "31": {"c": "SXM02", "133": [20, 5, 5], "155": [20, 5, 5], "121": [20, 5, 5]}, "32": {"c": "SXM03", "123": [11, 4, 5], "155": [7, 3, 5], "132": [7, 3, 5], "124": [11, 4, 5], "121": [18, 7, 5], "131": [11, 4, 5]}, "34": {"c": "SXMDOE", "133": [0, 5, 5], "123": [0, 5, 5], "155": [0, 5, 5], "132": [0, 5, 5], "124": [0, 5, 5], "121": [0, 5, 5], "131": [0, 5, 5]}}, 
            "5": {"c": "PKL", "total": {"133": [17, 8, 10], "123": [27, 13, 15], "155": [23, 12, 15], "132": [6, 9, 10], "124": [27, 13, 15], "121": [50, 15, 20], "131": [27, 13, 15]}, "admin_total": {"34": {"c": "SXMDOE", "133": [17, 3, 5], "123": [27, 8, 10], "155": [23, 7, 10], "132": [6, 4, 5], "124": [27, 8, 10], "121": [50, 10, 15], "131": [27, 8, 10]}}, "31": {"c": "SXM02", "133": [17, 3, 5], "155": [17, 3, 5], "121": [17, 3, 5]}, "32": {"c": "SXM03", "123": [27, 8, 10], "155": [6, 4, 5], "132": [6, 4, 5], "124": [27, 8, 10], "121": [33, 7, 10], "131": [27, 8, 10]}, "34": {"c": "SXMDOE", "133": [0, 5, 5], "123": [0, 5, 5], "155": [0, 5, 5], "132": [0, 5, 5], "124": [0, 5, 5], "121": [0, 5, 5], "131": [0, 5, 5]}}}}}, 
        "DUO": {
            "total": {"123": [338, 107, 130], "155": [503, 112, 165], "122": [192, 58, 70], "134": [136, 54, 55], "121": [485, 80, 135], "140": [137, 38, 45], "158": [163, 37, 55], "144": [2, 3, 5], "167": [543, 67, 125], "160": [55, 20, 25], "138": [139, 41, 55], "139": [195, 45, 60], "149": [338, 52, 90], "150": [133, 37, 50], "156": [1, 4, 5], "0": [0, 0, 0]}, 
            "nl": {"total": {}, "1": {"c": "Vsbo", "4": {"c": "TKL", "total": {"123": [195, 55, 75], "155": [280, 60, 100], "122": [192, 58, 70], "134": [136, 54, 55], "121": [485, 80, 135]}, "admin_total": {"23": {"c": "CURETE", "123": [195, 55, 75], "155": [280, 60, 100], "122": [192, 58, 70], "134": [136, 54, 55], "121": [485, 80, 135]}}, "2": {"c": "CUR01", "123": [52, 8, 15], "155": [7, 3, 5], "121": [59, 6, 15]}, "3": {"c": "CUR02", "123": [15, 5, 5], "155": [7, 3, 5], "122": [9, 6, 5], "134": [7, 3, 5], "121": [18, 7, 5]}, "4": {"c": "CUR03", "123": [5, 5, 5], "155": [6, 4, 5], "122": [11, 4, 5], "134": [10, 5, 5], "121": [19, 6, 5]}, "6": {"c": "CUR05", "123": [31, 4, 10], "155": [80, 10, 20], "122": [40, 5, 10], "134": [25, 5, 5], "121": [85, 10, 20]}, "8": {"c": "CUR08", "123": [5, 5, 5], "155": [17, 3, 5], "122": [2, 3, 5], "121": [13, 7, 5]}, "9": {"c": "CUR09", "123": [27, 8, 10], "155": [53, 7, 15], "122": [27, 8, 10], "134": [8, 7, 5], "121": [79, 6, 20]}, "10": {"c": "CUR10", "123": [6, 4, 5], "155": [6, 4, 5], "122": [16, 4, 5], "134": [8, 7, 5], "121": [27, 8, 10]}, "11": {"c": "CUR11", "123": [17, 3, 5], "155": [56, 9, 15], "122": [46, 9, 10], "134": [46, 9, 10], "121": [102, 8, 25]}, "12": {"c": "CUR12", "123": [12, 3, 5], "155": [12, 3, 5], "122": [15, 5, 5], "134": [11, 4, 5], "121": [27, 8, 10]}, "18": {"c": "CUR18", "123": [5, 5, 5], "155": [5, 5, 5], "122": [2, 3, 5], "134": [1, 4, 5], "121": [6, 4, 5]}, "28": {"c": "CUR23", "123": [20, 5, 5], "155": [26, 4, 10], "122": [14, 6, 5], "134": [14, 6, 5], "121": [35, 5, 10]}, "20": {"c": "CUR20", "155": [5, 5, 5], "122": [10, 5, 5], "134": [6, 4, 5], "121": [15, 5, 5]}, "23": {"c": "CURETE", "123": [0, 0, 0], "155": [0, 0, 0], "122": [0, 0, 0], "134": [0, 0, 0], "121": [0, 0, 0]}}}, 
            "2": {"c": "Havo", "0": {"c": null, "total": {"140": [112, 28, 30], "158": [129, 21, 40], "123": [112, 33, 35], "144": [2, 3, 5], "155": [193, 32, 45], "167": [461, 44, 95], "160": [52, 13, 15], "138": [105, 25, 35], "139": [154, 26, 40], "149": [291, 39, 70], "150": [99, 26, 35]}, "admin_total": {"23": {"c": "CURETE", "140": [112, 28, 30], "158": [129, 21, 40], "123": [112, 33, 35], "144": [2, 3, 5], "155": [193, 32, 45], "167": [461, 44, 95], "160": [52, 13, 15], "138": [105, 25, 35], "139": [154, 26, 40], "149": [291, 39, 70], "150": [99, 26, 35]}}, "15": {"c": "CUR15", "140": [24, 6, 5], "158": [26, 4, 10], "123": [23, 7, 5], "155": [36, 4, 10], "167": [109, 11, 25], "160": [25, 5, 5], "138": [26, 4, 10], "139": [36, 4, 10], "149": [58, 7, 15], "150": [29, 6, 10]}, "16": {"c": "CUR16", "140": [17, 3, 5], "158": [56, 9, 15], "123": [32, 8, 10], "144": [2, 3, 5], "155": [46, 9, 10], "167": [133, 12, 25], "160": [11, 4, 5], "138": [25, 5, 5], "139": [47, 8, 10], "149": [86, 9, 20], "150": [20, 5, 5]}, "17": {"c": "CUR17", "140": [43, 7, 10], "158": [30, 5, 10], "123": [30, 5, 10], "155": [75, 10, 15], "167": [140, 10, 25], "160": [16, 4, 5], "138": [40, 5, 10], "139": [43, 7, 10], "149": [99, 11, 20], "150": [35, 5, 10]}, "18": {"c": "CUR18", "140": [13, 7, 5], "123": [14, 6, 5], "155": [17, 3, 5], "167": [31, 4, 10], "138": [4, 6, 5], "139": [11, 4, 5], "149": [19, 6, 5], "150": [4, 6, 5]}, "19": {"c": "CUR19", "140": [15, 5, 5], "158": [17, 3, 5], "123": [13, 7, 5], "155": [19, 6, 5], "167": [48, 7, 10], "138": [10, 5, 5], "139": [17, 3, 5], "149": [29, 6, 10], "150": [11, 4, 5]}, "23": {"c": "CURETE", "140": [0, 0, 0], "158": [0, 0, 0], "123": [0, 0, 0], "144": [0, 0, 0], "155": [0, 0, 0], "167": [0, 0, 0], "160": [0, 0, 0], "138": [0, 0, 0], "139": [0, 0, 0], "149": [0, 0, 0], "150": [0, 0, 0]}}}, 
            "3": {"c": "Vwo", "0": {"c": null, "total": {"140": [25, 10, 15], "158": [34, 16, 15], "123": [31, 19, 20], "155": [30, 20, 20], "167": [82, 23, 30], "160": [3, 7, 10], "138": [34, 16, 20], "139": [41, 19, 20], "149": [47, 13, 20], "150": [34, 11, 15], "156": [1, 4, 5]}, "admin_total": {"23": {"c": "CURETE", "140": [25, 10, 15], "158": [34, 16, 15], "123": [31, 19, 20], "155": [30, 20, 20], "167": [82, 23, 30], "160": [3, 7, 10], "138": [34, 16, 20], "139": [41, 19, 20], "149": [47, 13, 20], "150": [34, 11, 15], "156": [1, 4, 5]}}, "15": {"c": "CUR15", "140": [12, 3, 5], "158": [13, 7, 5], "123": [11, 4, 5], "155": [8, 7, 5], "167": [34, 6, 10], "160": [2, 3, 5], "138": [16, 4, 5], "139": [16, 4, 5], "149": [17, 3, 5], "150": [17, 3, 5]}, "16": {"c": "CUR16", "140": [6, 4, 5], "158": [14, 6, 5], "123": [14, 6, 5], "155": [14, 6, 5], "167": [33, 7, 10], "160": [1, 4, 5], "138": [12, 3, 5], "139": [18, 7, 5], "149": [21, 4, 5], "150": [12, 3, 5]}, "19": {"c": "CUR19", "140": [7, 3, 5], "158": [7, 3, 5], "123": [4, 6, 5], "155": [7, 3, 5], "167": [12, 3, 5], "138": [5, 5, 5], "139": [5, 5, 5], "149": [7, 3, 5], "150": [5, 5, 5]}, "18": {"c": "CUR18", "123": [2, 3, 5], "155": [1, 4, 5], "167": [3, 7, 5], "138": [1, 4, 5], "139": [2, 3, 5], "149": [2, 3, 5], "156": [1, 4, 5]}, "23": {"c": "CURETE", "140": [0, 0, 0], "158": [0, 0, 0], "123": [0, 0, 0], "155": [0, 0, 0], "167": [0, 0, 0], "160": [0, 0, 0], "138": [0, 0, 0], "139": [0, 0, 0], "149": [0, 0, 0], "150": [0, 0, 0], "156": [0, 0, 0]}}}, 
            "null": {"c": null, "0": {"c": null, "total": {"0": [0, 0, 0]}, "admin_total": {"23": {"c": "CURETE", "0": [0, 0, 0]}, "34": {"c": "SXMDOE", "0": [0, 0, 0]}}, "13": {"c": "CUR13", "0": [0, 0, 0]}, "14": {"c": "CUR14", "0": [0, 0, 0]}, "21": {"c": "CUR21", "0": [0, 0, 0]}, "22": {"c": "CUR22", "0": [0, 0, 0]}, "25": {"c": "CURCOM", "0": [0, 0, 0]}, "23": {"c": "CURETE", "0": [0, 0, 0]}, "24": {"c": "CURINSP", "0": [0, 0, 0]}, "1": {"c": "CURSYS", "0": [0, 0, 0]}, "30": {"c": "SXM01", "0": [0, 0, 0]}, "33": {"c": "SXM04", "0": [0, 0, 0]}, "34": {"c": "SXMDOE", "0": [0, 0, 0]}, "35": {"c": "SXMINSP", "0": [0, 0, 0]}, "29": {"c": "SXMSYS", "0": [0, 0, 0]}}}}}}

    receipt_dict:
        {"ETE": 
            {"2": {"c": "CUR01", 
                "1": {"c": "Vsbo", 
                    "6": {"c": "PBL", "133": [17, 13, 5], "123": [22, 8, 5], "155": [17, 3, 5], "114": [39, 6, 10], "124": [22, 8, 5], "113": [39, 6, 10], "118": [39, 6, 10], "121": [17, 3, 5], "131": [22, 8, 5]}, 
                    "5": {"c": "PKL", "133": [18, 12, 5], "123": [26, 4, 10], "155": [18, 7, 5], "114": [44, 6, 10], "124": [26, 4, 10], "113": [44, 6, 10], "118": [44, 6, 10], "121": [18, 7, 5], "131": [26, 14, 10]}, 
                    "4": {"c": "TKL", "133": [7, 3, 5], "114": [59, 6, 15], "124": [59, 6, 15], "113": [59, 6, 15], "118": [59, 6, 15], "120": [59, 6, 15], "131": [52, 8, 15]}}}, 
            "3": {"c": "CUR02", 
                "1": {"c": "Vsbo", "6": {"c": "PBL", "133": [5, 5, 5], "123": [11, 4, 5], "155": [5, 5, 5], "114": [16, 4, 5], "124": [8, 7, 5], "113": [16, 4, 5], "118": [16, 4, 5], "120": [4, 6, 5], "121": [4, 6, 5], "131": [11, 9, 5]}, 
                "5": {"c": "PKL", "133": [2, 8, 5], "123": [4, 6, 5], "155": [2, 3, 5], "114": [6, 4, 5], "124": [2, 3, 5], "113": [6, 4, 5], "118": [6, 4, 5], "120": [1, 4, 5], "121": [3, 7, 5], "131": [4, 6, 5]}, 
    """
    return count_dict, receipt_dict
# --- end of create_studsubj_count_dict


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
def create_envelop_count_per_school_dict(sel_examyear_instance, sel_examperiod, request, schoolbase_pk_list, subjbase_pk_list):
    # PPR2022-08-26 PR2022-09-03 PR2022-10-13
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_envelop_count_per_school_dict ----- ')
        logger.debug('    sel_examyear: ' + str(sel_examyear_instance))
        logger.debug('    schoolbase_pk_list: ' + str(schoolbase_pk_list))
        logger.debug('    subjbase_pk_list: ' + str(subjbase_pk_list))

    # this one is for printing labels per school: dict order: school - dep - lvl - subj - exam - lang -
    # no count needed, happens when creating labels
    # ete/DUO not necessary, but let it stay if they want to include them in letter to cinfirm received exams

    #  create nested dict with subjects count per exam, lang, dep, lvl, school and subjbase_id
    #  all schools of CUR and SXM only submitted subjects, not deleted # PR2021-08-19
    #  add extra for ETE and DOE PR2021-09-25
    # called by: create_orderlist_xlsx, create_orderlist_per_school_xlsx, OrderlistsPublishView

    print_without_schools = False
    if schoolbase_pk_list is None:
        print_without_schools = True
    elif not len(schoolbase_pk_list):
        print_without_schools = True
    elif schoolbase_pk_list[0] == -1:
        schoolbase_pk_list = None

    rows = create_studsubj_count_rows(
        sel_examyear_instance=sel_examyear_instance,
        sel_examperiod=sel_examperiod,
        request=request,
        schoolbase_pk_list=schoolbase_pk_list,
        subjbase_pk_list=subjbase_pk_list
    )

    # to be solved: group by si.ete_exam and si.otherlang goes wrong when sectors of one level have different otherlang PR2022-08-13

    count_per_school_dict = {}

    for row in rows:
        if logging_on:
            logger.debug('row: ' + str(row))
        """
        row: {'subjbase_id': 133, 'ete_exam': True, 'id_key': '1_6_133_1_1', 'lang': 'nl', 'country_id': 1, 'sb_code': 'CUR01', 
           'lvlbase_id': 6, 'lvl_sequence': 1, 'lvl_abbrev': 'PBL', 
           'depbase_id': 1, 'dep_sequence': 1, 'depbase_code': 'Vsbo', 
           'subjbase_code': 'ac', 'subj_name': 'Administratie en commercie', 
           'schoolbase_id': 2, 'school_name': 'Ancilla Domini Vsbo', 
           'subj_count': 13, 'exam_count': 2, 'extra_count': 7, 'tv2_count': 5}
        """

# - get or create schoolbase_dict
        row_sb_pk = row.get('schoolbase_id')
        if row_sb_pk not in count_per_school_dict:
            count_per_school_dict[row_sb_pk] = {
                'sb_code': row.get('sb_code') or '-'
               #'school_name': row.get('school_name') or '-'
            }
        schoolbase_dict = count_per_school_dict[row_sb_pk]

# - get or create depbase_list
        depbase_pk = row.get('depbase_id')

        if depbase_pk not in schoolbase_dict:
            schoolbase_dict[depbase_pk] = {
                'depbase_code': row.get('depbase_code') or '-',
                'school_name': row.get('school_name') or '-'
            }
        depbase_dict = schoolbase_dict[depbase_pk]

# - get or create lvlbase_list
        lvlbase_pk = row.get('lvlbase_id') or 0

        if lvlbase_pk not in depbase_dict:
            depbase_dict[lvlbase_pk] = []
        lvlbase_list = depbase_dict[lvlbase_pk]

        lvlbase_list.append(row)

    if logging_on:
        #datalists_json = json.dumps(count_per_school_dict, cls=af.LazyEncoder)
        logger.debug('count_per_school_dict: ' + str(count_per_school_dict))

    """              
    count_per_school_dict: {
        "2": {"sb_code": "CUR01", "school_name": "Ancilla Domini Vsbo", 
            "1": {"depbase_code": "Vsbo", "school_name": "Ancilla Domini Vsbo",
                "6": [{"subjbase_id": 133, "ete_exam": true, "id_key": "1_6_133", "lang": "nl", 
                        "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PBL", "depbase_code": "Vsbo", 
                        "subj_name": "Administratie & Commercie", 
                        "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", 
                        "depbase_id": 1, "lvlbase_id": 6, 
                        "subj_count": 17, "dep_sequence": 1, "lvl_sequence": 1, 
                        "subjbase_code": "ac", "extra_count": 3, "tv2_count": 5}, 
                    {"subjbase_id": 123, "ete_exam": true, "id_key": "1_6_123", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PBL", "depbase_code": "Vsbo", "subj_name": "Biologie", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 6, "subj_count": 22, "dep_sequence": 1, "lvl_sequence": 1, "subjbase_code": "bi", "extra_count": 8, "tv2_count": 5}, 
                    {"subjbase_id": 155, "ete_exam": true, "id_key": "1_6_155", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PBL", "depbase_code": "Vsbo", "subj_name": "Economie", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 6, "subj_count": 17, "dep_sequence": 1, "lvl_sequence": 1, "subjbase_code": "ec", "extra_count": 3, "tv2_count": 5}, 
                    {"subjbase_id": 114, "ete_exam": true, "id_key": "1_6_114", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PBL", "depbase_code": "Vsbo", "subj_name": "Engelse taal", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 6, "subj_count": 39, "dep_sequence": 1, "lvl_sequence": 1, "subjbase_code": "en", "extra_count": 6, "tv2_count": 10}, 
                    {"subjbase_id": 124, "ete_exam": true, "id_key": "1_6_124", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PBL", "depbase_code": "Vsbo", "subj_name": "Mens & Maatschappij-2", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 6, "subj_count": 22, "dep_sequence": 1, "lvl_sequence": 1, "subjbase_code": "mm2", "extra_count": 8, "tv2_count": 5}, 
                    {"subjbase_id": 113, "ete_exam": true, "id_key": "1_6_113", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PBL", "depbase_code": "Vsbo", "subj_name": "Nederlandse taal", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 6, "subj_count": 39, "dep_sequence": 1, "lvl_sequence": 1, "subjbase_code": "ne", "extra_count": 6, "tv2_count": 10}, 
                    {"subjbase_id": 118, "ete_exam": true, "id_key": "1_6_118", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PBL", "depbase_code": "Vsbo", "subj_name": "Papiamentu", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 6, "subj_count": 39, "dep_sequence": 1, "lvl_sequence": 1, "subjbase_code": "pa", "extra_count": 6, "tv2_count": 10}, 
                    {"subjbase_id": 121, "ete_exam": true, "id_key": "1_6_121", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PBL", "depbase_code": "Vsbo", "subj_name": "Wiskunde", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 6, "subj_count": 17, "dep_sequence": 1, "lvl_sequence": 1, "subjbase_code": "wk", "extra_count": 3, "tv2_count": 5}, 
                    {"subjbase_id": 131, "ete_exam": true, "id_key": "1_6_131", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PBL", "depbase_code": "Vsbo", "subj_name": "Zorg & Welzijn intrasectoraal", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 6, "subj_count": 22, "dep_sequence": 1, "lvl_sequence": 1, "subjbase_code": "zwi", "extra_count": 8, "tv2_count": 5}], 
                "5": [{"subjbase_id": 133, "ete_exam": true, "id_key": "1_5_133", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PKL", "depbase_code": "Vsbo", "subj_name": "Administratie & Commercie", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 5, "subj_count": 18, "dep_sequence": 1, "lvl_sequence": 2, "subjbase_code": "ac", "extra_count": 7, "tv2_count": 5}, 
                    {"subjbase_id": 123, "ete_exam": true, "id_key": "1_5_123", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PKL", "depbase_code": "Vsbo", "subj_name": "Biologie", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 5, "subj_count": 26, "dep_sequence": 1, "lvl_sequence": 2, "subjbase_code": "bi", "extra_count": 4, "tv2_count": 10}, 
                    {"subjbase_id": 155, "ete_exam": true, "id_key": "1_5_155", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PKL", "depbase_code": "Vsbo", "subj_name": "Economie", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 5, "subj_count": 18, "dep_sequence": 1, "lvl_sequence": 2, "subjbase_code": "ec", "extra_count": 7, "tv2_count": 5}, 
                    {"subjbase_id": 114, "ete_exam": true, "id_key": "1_5_114", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PKL", "depbase_code": "Vsbo", "subj_name": "Engelse taal", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 5, "subj_count": 44, "dep_sequence": 1, "lvl_sequence": 2, "subjbase_code": "en", "extra_count": 6, "tv2_count": 10}, 
                    {"subjbase_id": 124, "ete_exam": true, "id_key": "1_5_124", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PKL", "depbase_code": "Vsbo", "subj_name": "Mens & Maatschappij-2", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 5, "subj_count": 26, "dep_sequence": 1, "lvl_sequence": 2, "subjbase_code": "mm2", "extra_count": 4, "tv2_count": 10},
                    {"subjbase_id": 113, "ete_exam": true, "id_key": "1_5_113", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PKL", "depbase_code": "Vsbo", "subj_name": "Nederlandse taal", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 5, "subj_count": 44, "dep_sequence": 1, "lvl_sequence": 2, "subjbase_code": "ne", "extra_count": 6, "tv2_count": 10}, 
                    {"subjbase_id": 118, "ete_exam": true, "id_key": "1_5_118", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PKL", "depbase_code": "Vsbo", "subj_name": "Papiamentu", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 5, "subj_count": 44, "dep_sequence": 1, "lvl_sequence": 2, "subjbase_code": "pa", "extra_count": 6, "tv2_count": 10}, 
                    {"subjbase_id": 121, "ete_exam": true, "id_key": "1_5_121", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PKL", "depbase_code": "Vsbo", "subj_name": "Wiskunde", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 5, "subj_count": 18, "dep_sequence": 1, "lvl_sequence": 2, "subjbase_code": "wk", "extra_count": 7, "tv2_count": 5}, 
                    {"subjbase_id": 131, "ete_exam": true, "id_key": "1_5_131", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "PKL", "depbase_code": "Vsbo", "subj_name": "Zorg & Welzijn intrasectoraal", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 5, "subj_count": 26, "dep_sequence": 1, "lvl_sequence": 2, "subjbase_code": "zwi", "extra_count": 4, "tv2_count": 10}],
                "4": [{"subjbase_id": 133, "ete_exam": true, "id_key": "1_4_133", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "TKL", "depbase_code": "Vsbo", "subj_name": "Administratie & Commercie", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 4, "subj_count": 7, "dep_sequence": 1, "lvl_sequence": 3, "subjbase_code": "ac", "extra_count": 3, "tv2_count": 5}, 
                    {"subjbase_id": 123, "ete_exam": false, "id_key": "1_4_123", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "TKL", "depbase_code": "Vsbo", "subj_name": "Biologie", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 4, "subj_count": 52, "dep_sequence": 1, "lvl_sequence": 3, "subjbase_code": "bi", "extra_count": 8, "tv2_count": 15},
                    {"subjbase_id": 155, "ete_exam": false, "id_key": "1_4_155", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "TKL", "depbase_code": "Vsbo", "subj_name": "Economie", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 4, "subj_count": 7, "dep_sequence": 1, "lvl_sequence": 3, "subjbase_code": "ec", "extra_count": 3, "tv2_count": 5}, 
                    {"subjbase_id": 114, "ete_exam": true, "id_key": "1_4_114", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "TKL", "depbase_code": "Vsbo", "subj_name": "Engelse taal", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 4, "subj_count": 59, "dep_sequence": 1, "lvl_sequence": 3, "subjbase_code": "en", "extra_count": 6, "tv2_count": 15}, 
                    {"subjbase_id": 124, "ete_exam": true, "id_key": "1_4_124", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "TKL", "depbase_code": "Vsbo", "subj_name": "Mens & Maatschappij-2", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 4, "subj_count": 59, "dep_sequence": 1, "lvl_sequence": 3, "subjbase_code": "mm2", "extra_count": 6, "tv2_count": 15}, 
                    {"subjbase_id": 113, "ete_exam": true, "id_key": "1_4_113", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "TKL", "depbase_code": "Vsbo", "subj_name": "Nederlandse taal", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 4, "subj_count": 59, "dep_sequence": 1, "lvl_sequence": 3, "subjbase_code": "ne", "extra_count": 6, "tv2_count": 15}, 
                    {"subjbase_id": 118, "ete_exam": true, "id_key": "1_4_118", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "TKL", "depbase_code": "Vsbo", "subj_name": "Papiamentu", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 4, "subj_count": 59, "dep_sequence": 1, "lvl_sequence": 3, "subjbase_code": "pa", "extra_count": 6, "tv2_count": 15}, 
                    {"subjbase_id": 120, "ete_exam": true, "id_key": "1_4_120", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "TKL", "depbase_code": "Vsbo", "subj_name": "Spaanse taal", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 4, "subj_count": 59, "dep_sequence": 1, "lvl_sequence": 3, "subjbase_code": "sp", "extra_count": 6, "tv2_count": 15}, 
                    {"subjbase_id": 121, "ete_exam": false, "id_key": "1_4_121", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "TKL", "depbase_code": "Vsbo", "subj_name": "Wiskunde", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 4, "subj_count": 59, "dep_sequence": 1, "lvl_sequence": 3, "subjbase_code": "wk", "extra_count": 6, "tv2_count": 15}, 
                    {"subjbase_id": 131, "ete_exam": true, "id_key": "1_4_131", "lang": "nl", "country_id": 1, "sb_code": "CUR01", "lvl_abbrev": "TKL", "depbase_code": "Vsbo", "subj_name": "Zorg & Welzijn intrasectoraal", "schoolbase_id": 2, "school_name": "Ancilla Domini Vsbo", "depbase_id": 1, "lvlbase_id": 4, "subj_count": 52, "dep_sequence": 1, "lvl_sequence": 3, "subjbase_code": "zwi", "extra_count": 8, "tv2_count": 15}]}}}                                
    """
    return count_per_school_dict
# --- end of create_envelop_count_per_school_dict


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
def create_envelop_print_per_subject_dict(sel_examyear_instance, sel_examperiod, request, schoolbase_pk_list, subjbase_pk_list):
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

    rows = create_studsubj_count_rows(
        sel_examyear_instance=sel_examyear_instance,
        sel_examperiod=sel_examperiod,
        request=request,
        schoolbase_pk_list=schoolbase_pk_list,
        subjbase_pk_list=subjbase_pk_list
    )

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

def calc_extra_examsNEW(item_count, extra_fixed, extra_perc, round_to):

    logging_on = False  # s.LOGGING_ON
    # NOT IN USE:
    # - PR2022-08-26 this function takes in account that there can be multiple exams for a subject (blue and red)
    # for example:
    #   - with 1 exam: 43 students > 45 exams (rounded up to 5)
    #   - with 2 exams: 43 student / 2 = 21,5 > 25 per exam * 2 = 50 exams

    extra_count = 0
    if item_count:

# PR2022-10-10 exam_count is not in use any more,
# instead of claculating exams the items are calculated per envelopsubject(i.e the subj/dep/lvl combination)
# exam_count is number of exams of this subject / dep / level / exammperiod, default = 1
        # was: if not exam_count:
        #           exam_count = 1

# divide items over the exams, calculate extra per exam
        # was: item_count_per_exam = item_count / exam_count

        extra_not_rounded = (item_count * extra_perc / 100)
        total_not_rounded = item_count + extra_fixed + extra_not_rounded
        total_divided = total_not_rounded / round_to
        total_integer = int(total_divided)
        # total_frac = (total_divided - total_integer)
        total_roundup = total_integer + 1 if (total_divided - total_integer) else total_integer
        # total_roundup = total_frac_roundup * order_round_to
        total_count = total_roundup * round_to
        # was: extra_count_per_exam = total_count_per_exam - item_count
        # was: extra_count = int(extra_count_per_exam * exam_count)
        extra_count = int(total_count - item_count)

        if logging_on:
            logger.debug(' ------- calc_extra_exams -------')
            logger.debug('    item_count:   ' + str(item_count))
            logger.debug('    extra_not_rounded: ' + str(extra_not_rounded))
            logger.debug('    total_not_rounded: ' + str(total_not_rounded))
            logger.debug('    total_divided: ' + str(total_divided))
            logger.debug('    total_roundup:  ' + str(total_roundup))
            logger.debug('    total_count:  ' + str(total_count))
            logger.debug('    extra_count:  ' + str(extra_count))
            logger.debug(' --------------')

    return extra_count
# - end of calc_extra_examsNEW


def calc_exams_tv02(item_count, divisor, multiplier, max_exams):  # PR2021-09-25
    # - count examns tv2 per school / subject:
    # - 'multiplier' tv02-examns per 'divisor' tv01-examns, roundup to 'multiplier', with max of 'max_exams'
    # - Note: values of divisor, multiplier, max_exams are from table examyear,
    #         thus can be different for CUR and SXM schools

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- calc_exams_tv02 -------')
        logger.debug('item_count:  ' + str(item_count))
        logger.debug('divisor: ' + str(divisor))
        logger.debug('multiplier:  ' + str(multiplier))
        logger.debug('max_exams:  ' + str(max_exams))

    tv2_count = 0
    if item_count:
        try:
            # PR2021-10-12 debug: gave ZeroDivisionError. "if divisor else 0" added.
            total_divided = item_count / divisor if divisor else 0
            total_integer = int(total_divided)
            # total_frac = (total_divided - total_integer)
            total_roundup = total_integer + 1 if (total_divided - total_integer) else total_integer
            # total_roundup = total_frac_roundup * order_round_to
            tv2_count = total_roundup * multiplier

            if tv2_count > max_exams:
                tv2_count = max_exams

            if logging_on:
                logger.debug('item_count:  ' + str(item_count))
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
    # PR2021-08-19 PR2021-09-24 PR2022-08-13 PR2022-10-10
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- create_studsubj_count_rows ----- ')
        logger.debug('    sel_examyear_instance: ' + str(sel_examyear_instance))
        logger.debug('    sel_examperiod: ' + str(sel_examperiod))
        logger.debug('    schoolbase_pk_list: ' + str(schoolbase_pk_list))
        logger.debug('    subjbase_pk_list: ' + str(subjbase_pk_list))

    #  create nested dict with studsubj count + extra
    #   grouped by country, ete_exam, otherlang, depbase, lvlbase, subjbase, school

    #  all schools of CUR and SXM, only submitted subjects, not deleted # PR2021-08-19
    #  add extra for ETE and DOE PR2021-09-25

    # called by:
    #   create_studsubj_count_dict
    #   create_envelop_count_per_school_dict
    #   create_envelop_print_per_subject_dict
    #   EnvelopPrintView

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

# - NIU: this subquery counts number of exams of this school / dep / level / subject / examperiod
    # used for envelops, when practical exam: the number of exams must be divided by the number of exams of that subject
    # was: count_sql = create_sql_count_exams_per_subject()

# - create subquery with count of subjects per school / dep / lvl / subject
    # was: add number of exams ["WITH counts AS (" + count_sql + ")",
    sql_studsubj_agg_list = [
        "SELECT st.school_id, ey.country_id as ey_country_id, dep.base_id AS depbase_id, lvl.base_id AS lvlbase_id,",
        "sch.otherlang AS sch_otherlang,",

        # PR2022-10-10 was:
        #   "CONCAT_WS ('_', dep.base_id, COALESCE(lvl.base_id, 0), subj.base_id, ",
        #   "%(ep)s::INT",
        #   ", CASE WHEN si.ete_exam THEN 1 ELSE 0 END) AS id_key,",

        "CONCAT_WS ('_', dep.base_id, COALESCE(lvl.base_id, 0), subj.base_id) AS id_key,",

        # "dep.sequence AS dep_sequence, lvl.sequence AS lvl_sequence, ",  # for order by
        #"depbase.code AS depbase_code,",  # for testing only, must also delete from group_by
        #"lvl.abbrev AS lvl_abbrev,",  # for testing only, must also delete from group_by
        #"subj.name_nl AS subj_name,",  # for testing only, must also delete from group_by

        #PR2021-10-12 subj.otherlang replaced by si.otherlang
        # was: "subj.base_id AS subjbase_id, si.ete_exam, subj.otherlang AS subj_otherlang, count(*) AS subj_count",
        "subj.base_id AS subjbase_id, subjbase.code AS subjbase_code, si.ete_exam, si.otherlang AS si_otherlang, ",

        "count(*) AS subj_count",
        # was: ", counts.exam_count",
        
        "FROM students_studentsubject AS studsubj",

        "INNER JOIN subjects_schemeitem AS si ON (si.id = studsubj.schemeitem_id)",
        "INNER JOIN subjects_subject AS subj ON (subj.id = si.subject_id)",
        "INNER JOIN subjects_subjectbase AS subjbase ON (subjbase.id = subj.base_id)",

        "INNER JOIN students_student AS st ON (st.id = studsubj.student_id)",
        "INNER JOIN schools_school AS sch ON (sch.id = st.school_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
        "INNER JOIN schools_department AS dep ON (dep.id = st.department_id)",
        "INNER JOIN  schools_departmentbase AS depbase ON (depbase.id = dep.base_id)", # for testing only, depbase can be deleted

        "LEFT JOIN subjects_level AS lvl ON (lvl.id = st.level_id)",

        # was: "LEFT JOIN counts ON (counts.dep_id = dep.id AND counts.lvl_id = COALESCE(lvl.id, 0) AND",
        #       "counts.subj_id = subj.id AND counts.examperiod = %(ep)s::INT)",

# - show only exams that are not deleted
        "WHERE NOT studsubj.tobedeleted",
# - show only submitted studsubjects
        "AND studsubj.subj_published_id IS NOT NULL",
# - show only subjects that have a central exam
        "AND NOT si.weight_ce = 0",
# - skip DUO exams for SXM schools when CUR
        skip_ete_or_duo,
# - filter subjects if subjbase_pk_list has value
        filter_subjbase,

        "GROUP BY st.school_id, ey.country_id, dep.base_id, lvl.base_id,",
        "dep.sequence, lvl.sequence,"
        # was: "counts.exam_count,"
        "depbase.code, lvl.abbrev, subj.name_nl, subjbase.code,", # for testing only, must also delete from group_by
        "sch.otherlang, subj.base_id, si.ete_exam, si.otherlang"
    ]

    # to be solved: group by si.ete_exam and si.otherlang goes wrong when sectors of one level have different otherlang PR2022-08-13
    sql_studsubj_agg = ' '.join(sql_studsubj_agg_list)

# - create query with row per school and inner join with subquery count_studsubj
    sql_list = ["WITH studsubj AS (", sql_studsubj_agg, ")",
                "SELECT studsubj.subjbase_id, studsubj.ete_exam, studsubj.id_key, ",
                "studsubj.subjbase_id, studsubj.subjbase_code,",

                "CASE WHEN studsubj.si_otherlang IS NULL OR studsubj.sch_otherlang IS NULL THEN 'nl' ELSE",
                "CASE WHEN POSITION(studsubj.sch_otherlang IN studsubj.si_otherlang) > 0 ",
                "THEN studsubj.sch_otherlang ELSE 'nl' END END AS lang,",

                "cntr.id AS country_id,",  # PR2021-09-24 added, for extra exams ETE and DoE
                # "sb.code AS sb_code, studsubj.lvl_abbrev, studsubj.depbase_code,",  # for testing only
                # "studsubj.subj_name,",  # for testing only
                # "sch.name AS school_name,",
                "sch.base_id AS schoolbase_id, studsubj.depbase_id, studsubj.lvlbase_id,",
                # "studsubj.dep_sequence, studsubj.lvl_sequence, ",

                "studsubj.subj_count",

                "FROM schools_school AS sch",
                "INNER JOIN schools_schoolbase AS sb ON (sb.id = sch.base_id)",
                "INNER JOIN schools_country AS cntr ON (cntr.id = sb.country_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = sch.examyear_id)",
                "LEFT JOIN studsubj ON (studsubj.school_id = sch.id)",

# - show only exams of this exam year
                # filter by ey.code, because sxm school must also be included
                "WHERE ey.code = %(ey_code_int)s::INT"
                ]

# - filter on parameter schoolbase_pk_list when it has value
    if schoolbase_pk_list:
        sql_keys['sb_arr'] = schoolbase_pk_list
        sql_list.append("AND sb.id IN ( SELECT UNNEST(%(sb_arr)s::INT[]) )")

    #sql_list.append("ORDER BY studsubj.dep_sequence, LOWER(studsubj.subjbase_code), studsubj.lvl_sequence, LOWER(sb.code)")
    #sql_list.append("ORDER BY LOWER(sb.code), studsubj.dep_sequence, studsubj.lvl_sequence, LOWER(studsubj.subjbase_code)")

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
        # TODO delete exam_count
        # practical exams have multiple exams for the same subject (Blue, Red). Count number of exams,
        # default is 1 if no value given or value = 0
        # exam_count = row.get('exam_count') or 1

        extra_count = 0
        tv2_count = 0
        if subj_count:
            extra_count = calc_extra_examsNEW(subj_count, order_extra_fixed, order_extra_perc, order_round_to)
            tv2_count = calc_exams_tv02(subj_count, order_tv2_divisor, order_tv2_multiplier, order_tv2_max)

    # - add extra_count and tv2_count to row, for enveloplabel print
        row['extra_count'] = extra_count
        row['tv2_count'] = tv2_count

        if logging_on :
            logger.debug('row: ' + str(row))
        """          
        row: { 'id_key': '1_6_133', 'ete_exam': True,'lang': 'nl', 'country_id': 1, 
            'depbase_id': 1, 'dep_sequence': 1, 'depbase_code': 'Vsbo', 
            'lvlbase_id': 6, lvl_abbrev': 'PBL', 'lvl_sequence': 1, 
            'subjbase_id': 133, 'subjbase_code': 'ac', 'subj_name': 'Administratie & Commercie', 
            'schoolbase_id': 2, 'sb_code': 'CUR01', 'school_name': 'Ancilla Domini Vsbo',            
            'subj_count': 17,  'extra_count': 3, 'tv2_count': 5}
        """

        if logging_on:
            logger.debug('........subj_count: ' + str(subj_count))
            logger.debug('.......extra_count: ' + str(extra_count))
            logger.debug('.........tv2_count: ' + str(tv2_count))

    return rows
# - end of create_studsubj_count_rows

##############################

def create_printlabel_rows(sel_examyear, sel_examperiod, sel_layout, envelopsubject_pk_list=None):
    # PR2022-08-12 PR2022-10-10
    # function creates list of labels with labelitem info in ARRAY_AGG
    # NIU function includes subquery that counts number of exams of this subject / dep / level / examperiod

    # values of sel_layout are: "no_errata", "errata_only", "all , None

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' =============== create_printlabel_rows ============= ')
        logger.debug('    sel_examyear: ' + str(sel_examyear) + ' ' + str(type(sel_examyear)))
        logger.debug('    envelopsubject_pk_list: ' + str(envelopsubject_pk_list) + ' ' + str(type(envelopsubject_pk_list)))
        logger.debug('    sel_layout: ' + str(sel_layout) + ' ' + str(type(sel_layout)))
        logger.debug('    ey_code_int: ' + str(sel_examyear.code) + ' ' + str(type(sel_examyear.code)))
        logger.debug('    sel_examperiod: ' + str(sel_examperiod) + ' ' + str(type(sel_examperiod)))

    printlabel_rows = []
    if sel_examyear :
        try:
            sql_keys = {'ey_code_int': sel_examyear.code, 'ep': sel_examperiod}

            sub_list = [
                "SELECT lblitm.enveloplabel_id,",
                "ARRAY_AGG(itm.content_nl ORDER BY lblitm.sequence, lblitm.id) AS content_nl_arr,",
                "ARRAY_AGG(itm.content_en ORDER BY lblitm.sequence, lblitm.id) AS content_en_arr,",
                "ARRAY_AGG(itm.content_pa ORDER BY lblitm.sequence, lblitm.id) AS content_pa_arr,",
                "ARRAY_AGG(itm.instruction_nl ORDER BY lblitm.sequence, lblitm.id) AS instruction_nl_arr,",
                "ARRAY_AGG(itm.instruction_en ORDER BY lblitm.sequence, lblitm.id) AS instruction_en_arr,",
                "ARRAY_AGG(itm.instruction_pa ORDER BY lblitm.sequence, lblitm.id) AS instruction_pa_arr,",
                "ARRAY_AGG(itm.content_color ORDER BY lblitm.sequence, lblitm.id) AS content_color_arr,",
                "ARRAY_AGG(itm.instruction_color ORDER BY lblitm.sequence, lblitm.id) AS instruction_color_arr,",
                "ARRAY_AGG(lblitm.sequence ORDER BY lblitm.sequence, lblitm.id) AS sequence_arr",

                "FROM subjects_enveloplabelitem AS lblitm",
                "INNER JOIN subjects_envelopitem AS itm ON (itm.id = lblitm.envelopitem_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = itm.examyear_id)",

                "WHERE ey.code = %(ey_code_int)s::INT",
                "GROUP BY lblitm.enveloplabel_id"
            ]
            sub_sql = ' '.join(sub_list)

    # - this subquery counts number of exams of this subject / dep / level / examperiod
            # used for envelops, when practical exam: the number of exams must be divided by the number of exams of that subject
            #count_sql = create_sql_count_exams_per_subject()

            #sql_list = ["WITH items AS (" + sub_sql + "),  counts AS (" + count_sql + ")",
            sql_list = ["WITH items AS (" + sub_sql + ")",
                "SELECT env_subj.id as env_subj_id,",
                "env_subj.department_id AS dep_id,"
                "env_subj.level_id AS lvl_id,"
                "env_subj.subject_id AS subj_id,"

                        
                #"env_subj.ete_exam, env_subj.version,"
                "env_subj.examperiod, env_subj.firstdate, env_subj.lastdate, env_subj.starttime, env_subj.endtime,"
                "env_subj.has_errata,"
                #"env_subj.subject_color,"
                "dep.base_id AS depbase_id, lvl.base_id AS lvlbase_id, subj.base_id AS subjbase_id,"
                
                "CONCAT_WS ('_', dep.base_id, COALESCE(lvl.base_id, 0), subj.base_id) AS id_key,",

                "bnd.name AS bnd_name, bndlbl.sequence AS bndlbl_sequence,",
                "lbl.name AS lbl_name, lbl.is_errata, lbl.is_variablenumber, lbl.numberofenvelops, lbl.numberinenvelop,",

                "items.content_nl_arr, items.content_en_arr, items.content_pa_arr,",
                "items.instruction_nl_arr, items.instruction_en_arr, items.instruction_pa_arr,",
                "items.content_color_arr, items.instruction_color_arr, items.sequence_arr",
                #"counts.exam_count",

                "FROM subjects_envelopsubject AS env_subj",
                "INNER JOIN subjects_subject AS subj ON (subj.id = env_subj.subject_id)",
                "INNER JOIN schools_department AS dep ON (dep.id = env_subj.department_id)",
                "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",
                "LEFT JOIN subjects_level AS lvl ON (lvl.id = env_subj.level_id)",

                "INNER JOIN subjects_envelopbundle AS bnd ON (bnd.id = env_subj.envelopbundle_id)",
                "INNER JOIN subjects_envelopbundlelabel AS bndlbl ON (bndlbl.envelopbundle_id = bnd.id)",
                "INNER JOIN subjects_enveloplabel AS lbl ON (lbl.id = bndlbl.enveloplabel_id)",
                "INNER JOIN items ON (items.enveloplabel_id = lbl.id)",

                #"LEFT JOIN counts ON (counts.dep_id = dep.id AND counts.lvl_id = COALESCE(lvl.id, 0) AND",
                #        "counts.subj_id = subj.id AND counts.examperiod = exam.examperiod)",

                "WHERE ey.code = %(ey_code_int)s::INT",
            ]

            if envelopsubject_pk_list:
                sql_keys['envelopsubject_pk_list'] = envelopsubject_pk_list
                sql_list.append('AND env_subj.id IN (SELECT UNNEST( %(envelopsubject_pk_list)s::INT[]))')
            #else:
            #    # PR2022-09-02 debug: must skip filter examperiod when envelopsubject_pk_list has value
            #    sql_list.append('AND exam.examperiod = %(ep)s::INT')

    # values of sel_layout are: "no_errata", "errata_only", "all" , None
            if sel_layout == 'no_errata':
                sql_list.append('AND NOT lbl.is_errata')
            elif sel_layout == 'errata_only':
                sql_list.append('AND env_subj.has_errata AND lbl.is_errata')
            elif sel_layout == 'show_errata_always':
                # when printing test bundle: always print errata label, also when env_subj.has_errata = False
                pass
            else:
                # skip iserrata when not env_subj.has_errata
                sql_list.append('AND ((lbl.is_errata AND env_subj.has_errata) OR (NOT lbl.is_errata))')

            #sql_list.append('ORDER BY subj.name_nl, exam.version, bndlbl.sequence')
            sql_list.append('ORDER BY subj.name_nl, bndlbl.sequence')

            sql = ' '.join(sql_list)

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                printlabel_rows = af.dictfetchall(cursor)

            if logging_on:
                if printlabel_rows:
                    for printlabel_row in printlabel_rows:
                        logger.debug('    printlabel_row: ' + str(printlabel_row) )

            """
            printlabel_rows: [
                {'env_subj_id': 76, 'dep_id': 10, 'lvl_id': 10, 'subj_id': 259, 
                'firstdate': datetime.date(2022, 4, 18), 'lastdate': None, 'starttime': '07.30', 'endtime': '09.30', 
                'has_errata': False, 'depbase_id': 1, 'lvlbase_id': 6, 'subjbase_id': 133, 
                'id_key': '1_6_133', 
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
                'sequence_arr': [1, 2, 61, 62, 63, 64, 65]}] 
            """
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
    return printlabel_rows
# --- end of create_enveloplabel_rows


def create_sql_count_exams_per_subjectNIU():
    # PR2022-08-26
    # this subquery counts number of exams of this subject / dep / level / examperiod
    # used for envelops: when practical exam the number of exams must be divided by the number of exams of that subject
    #  "WITH items AS (" + sub_sql + "),  counts AS (" + count_sql + ")",
    # join with:
    #   "LEFT JOIN counts ON (counts.dep_id = dep.id AND counts.lvl_id = COALESCE(lvl.id, 0) AND",
    #        "counts.subj_id = subj.id AND counts.examperiod = exam.examperiod)",

    count_list = [
        "SELECT dep.id AS dep_id, COALESCE(lvl.id, 0) AS lvl_id, subj.id AS subj_id, exam.examperiod, count(*) AS exam_count",

        "FROM subjects_exam AS exam",
        "INNER JOIN subjects_subject AS subj ON (subj.id = exam.subject_id)",
        "INNER JOIN schools_department AS dep ON (dep.id = exam.department_id)",
        "INNER JOIN schools_examyear AS ey ON (ey.id = dep.examyear_id)",
        "LEFT JOIN subjects_level AS lvl ON (lvl.id = exam.level_id)",

        "WHERE ey.code = %(ey_code_int)s::INT",
        "GROUP BY dep.id, lvl.id, subj.id, exam.examperiod"
    ]
    count_sql = ' '.join(count_list)

    return count_sql
# --- end of create_enveloplabel_rows

