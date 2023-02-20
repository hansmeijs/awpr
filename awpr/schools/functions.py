from django.db import connection

#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import gettext_lazy as _
# PR2019-01-04 from https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy

from awpr import constants as c
from awpr import settings as s

from accounts import models as acc_mod
from schools import models as sch_mod
from subjects import models as subj_mod

import logging
logger = logging.getLogger(__name__)


def copy_examyear_from_prev_examyearNIU(prev_examyear, new_examyear, log_list):
    # copy examyear fields from previous examyear PR2021-07-14 PR2022-07-31

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- copy_examyear_from_prev_examyear ----- ')
        logger.debug('prev_examyear: ' + str(prev_examyear) + ' ' + str(type(prev_examyear)))
        logger.debug('new_examyear: ' + str(new_examyear) + ' ' + str(type(new_examyear)))

    # the following fields got value in create_examyear:
    #    country=request.user.country,
    #    code=examyear_code_int,
    #    createdat=timezone.now()
    # the following fields got default value:
    #    published = False
    #    locked = False
    #    publishedat = None
    #    lockedat = None
    # the following fields get value from previous examyear::
    fields = ('no_practexam', 'sr_allowed', 'no_centralexam', 'no_thirdperiod',
              'order_extra_fixed', 'order_extra_perc', 'order_round_to',
              'order_tv2_divisor', 'order_tv2_multiplier', 'order_tv2_max',
              'order_admin_divisor', 'order_admin_multiplier', 'order_admin_max',
              'modifiedat', 'modifiedby_id')
    try:
        sql_keys = {'ey_id': prev_examyear.pk}

# - create select table of previous exam year
        sub_sql_list = [
            "SELECT",
            ', '.join(fields),
            "FROM schools_examyear",
            "WHERE id = %(ey_id)s::INT"]
        sub_sql = ' '.join(sub_sql_list)
        if logging_on:
            logger.debug('sub_sql: ' + str(sub_sql))

        sql_fields = []
        for field in fields:
            sql_fields.append(''.join((field, "=prev_ey.", field)))
        sql_fields_list = ', '.join(sql_fields)
        if logging_on:
            logger.debug('sql_fields_list: ' + str(sql_fields_list))

        sql_list = [
            "WITH prev_ey AS (", sub_sql, ")",
            "UPDATE schools_examyear AS this_ey",
            "SET",
            sql_fields_list,
            "FROM prev_ey",
            "WHERE this_ey.id = %(ey_id)s::INT",
            "RETURNING this_ey.code"
        ]
        sql = ' '.join(sql_list)
        if logging_on:
            logger.debug('sql: ' + str(sql))
        ey_code = '---'
        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = cursor.fetchall()
            if rows:
                first_row = rows[0]
                if first_row:
                    ey_code = first_row[0]

        log_list.append(c.STRING_SPACE_05 + str(_("Exam year data are copied to exam year %(ey_code)s.") % {'ey_code': ey_code}))

    except Exception as e:
        logger.error(getattr(e, 'message', str(e)))
        log_list.append(get_error_logtext(_('exam year data'), e))
# - end of copy_examyear_from_prev_examyear



def copy_userallowed_from_prev_examyear(prev_examyear_pk, new_examyear_pk, log_list):
    # copy userallowed records from previous examyear PR2022-12-16
    # TODO test if code is correct
    logging_on = s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_userallowed_from_prev_examyear -------')

    caption = _('User permissions')

# - loop through deps of prev examyear
    prev_userallowed_rows = acc_mod.UserAllowed.objects.filter(
        examyear_id=prev_examyear_pk
    )

    for prev_row in prev_userallowed_rows:
        if logging_on:
            logger.debug('prev_row: ' + str(prev_row))
        try:
            new_prev_userallowed_row = acc_mod.UserAllowed(
                user_id=prev_row.user_id,
                examyear_id=new_examyear_pk,

                usergroups=prev_row.usergroups,
                allowed_sections = prev_row.allowed_sections,
                allowed_clusters = prev_row.allowed_clusters,

                modifiedby_id=prev_row.modifiedby_id,
                modifiedat=prev_row.modifiedat
            )

            new_prev_userallowed_row.save()

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            log_list.append(get_error_logtext(caption, e))

    row_count = len(prev_userallowed_rows) if prev_userallowed_rows else 0
    log_txt = str(_("The permissions of %(row_count)s users are copied.") % {'row_count': row_count})
    log_list.append(c.STRING_SPACE_05 + log_txt)


# - end of copy_userallowed_from_prev_examyear


def copy_exfilestext_from_prev_examyear(prev_examyear_pk, new_examyear_pk, log_list):
    # copy exfilestext from previous examyear PR2021-04-25 PR2021-08-06 PR2022-08-01
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_exfilestext_from_prev_examyear -------')

    try:
        sql_keys = {'prev_ey_id': prev_examyear_pk, 'new_ey_id': new_examyear_pk}
        sql_list = [
        "INSERT INTO schools_exfilesText(",
            "examyear_id, key, subkey, setting,",
            "modifiedat, modifiedby_id)",
        "(SELECT",
            "%(new_ey_id)s::INT, key, subkey, setting,",
            "modifiedat, modifiedby_id",
        "FROM schools_exfilesText",
        "WHERE examyear_id = %(prev_ey_id)s::INT)",
        "RETURNING id;"
        ]

        sql = ' '.join(sql_list)

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = cursor.fetchall()

        row_count = len(rows) if rows else 0
        log_txt = str(_("%(row_count)s text items of the Ex forms are copied.") % {'row_count': row_count})
        log_list.append(c.STRING_SPACE_05 + log_txt)

        if logging_on:
            logger.debug('log_txt: ' + str(log_txt))

    except Exception as e:
        caption = _('Exfiles text')
        logger.error(getattr(e, 'message', str(e)))
        log_list.append(get_error_logtext(caption, e))
# - end of copy_exfilestext_from_prev_examyear


def copy_deps_from_prev_examyear(prev_examyear_pk, new_examyear_pk, log_list):
    # copy departments from previous examyear if it exists # PR2021-04-25  PR2021-08-06 PR2022-08-01
    # cannot create mapped_deps when using INSERT INTO. Copy it the Django way
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_deps_from_prev_examyear -------')

    mapped_deps = {}

    caption = _('Department')

# - loop through deps of prev examyear
    prev_deps = sch_mod.Department.objects.filter(
        examyear_id=prev_examyear_pk
    )

    for prev_dep in prev_deps:
        if logging_on:
            logger.debug('prev_dep: ' + str(prev_dep))
        try:
            new_dep = sch_mod.Department(
                base=prev_dep.base,
                examyear_id=new_examyear_pk,

                name=prev_dep.name,
                abbrev=prev_dep.abbrev,
                sequence=prev_dep.sequence,

                level_req=prev_dep.level_req,
                sector_req=prev_dep.sector_req,
                has_profiel=prev_dep.has_profiel,

                color=prev_dep.color,

                modifiedby_id=prev_dep.modifiedby_id,
                modifiedat=prev_dep.modifiedat
            )
    # - copy new department to department_log happens in save(request=request)
            new_dep.save()

            log_list.append(get_iscopied_logtext(caption, new_dep.abbrev))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            log_list.append(get_error_logtext(caption, e))
        else:
            if new_dep:
                mapped_deps[prev_dep.pk] = new_dep.pk

    if logging_on:
        logger.debug('mapped_deps: ' + str(mapped_deps))
    return mapped_deps
# - end of copy_deps_from_prev_examyear


def copy_levels_from_prev_examyear(prev_examyear_pk, new_examyear_pk, log_list):
    # copy levels from previous examyear PR2021-04-25 PR2021-08-06 PR2022-08-01
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_levels_from_prev_examyear -------')

    mapped_levels = {}

    caption = _('Learning path')

# - loop through levels of prev examyear
    prev_levels = subj_mod.Level.objects.filter(
        examyear_id=prev_examyear_pk
    )
    for prev_lvl in prev_levels:
        if logging_on:
            logger.debug('prev_lvl: ' + str(prev_lvl))
        try:
            new_lvl = subj_mod.Level(
                base=prev_lvl.base,
                examyear_id=new_examyear_pk,

                name=prev_lvl.name,
                abbrev=prev_lvl.abbrev,
                sequence=prev_lvl.sequence,
                depbases=prev_lvl.depbases,

                color=prev_lvl.color,

                modifiedby_id=prev_lvl.modifiedby_id,
                modifiedat=prev_lvl.modifiedat
            )
            new_lvl.save()

            log_list.append(get_iscopied_logtext(caption, new_lvl.abbrev))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            log_list.append(get_error_logtext(caption, e))
        else:
            if new_lvl:
                mapped_levels[prev_lvl.pk] = new_lvl.pk

    if logging_on:
        logger.debug('mapped_levels: ' + str(mapped_levels))
    return mapped_levels
# - end of copy_levels_from_prev_examyear


def copy_sectors_from_prev_examyear(prev_examyear_pk, new_examyear_pk, log_list):
    # copy sectors from previous examyear PR2021-04-25 PR2021-08-06 PR2022-08-01
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_sectors_from_prev_examyear -------')

    mapped_sectors = {}

    caption = _('Sector')

# - loop through sectors of prev examyear
    prev_sectors = subj_mod.Sector.objects.filter(
        examyear_id=prev_examyear_pk
    )
    for prev_sct in prev_sectors:
        if logging_on:
            logger.debug('prev_sct: ' + str(prev_sct))

        try:
            new_sct = subj_mod.Sector(
                base=prev_sct.base,
                examyear_id=new_examyear_pk,

                name=prev_sct.name,
                abbrev=prev_sct.abbrev,
                sequence=prev_sct.sequence,
                depbases=prev_sct.depbases,

                modifiedby_id=prev_sct.modifiedby_id,
                modifiedat=prev_sct.modifiedat
            )
# - copy new sector to log happens in save(request=request)
            new_sct.save()

            log_list.append(get_iscopied_logtext(caption, new_sct.abbrev))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            log_list.append(get_error_logtext(caption, e))
        else:
            if new_sct:
                mapped_sectors[prev_sct.pk] = new_sct.pk

    if logging_on:
        logger.debug('mapped_sectors: ' + str(mapped_sectors))
    return mapped_sectors
# - end of copy_sectors_from_prev_examyear


def copy_schools_from_prev_examyear(prev_examyear_pk, new_examyear_pk, log_list):
    # copy schools from previous examyear PR2021-04-25 PR2021-08-06 PR2022-08-01
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_schools_from_prev_examyear -------')

    mapped_schools = {}

    caption = _('School')

# - loop through schools of prev examyear
    prev_schools = sch_mod.School.objects.filter(
        examyear_id=prev_examyear_pk
    )
    for prev_school in prev_schools:
        if logging_on:
            logger.debug('prev_school: ' + str(prev_school))

        try:
            new_school = sch_mod.School(
                base=prev_school.base,
                examyear_id=new_examyear_pk,

                name=prev_school.name,
                abbrev=prev_school.abbrev,
                article=prev_school.article,
                telephone=prev_school.telephone,

                depbases=prev_school.depbases,
                otherlang=prev_school.otherlang,
                # not in use: no_order
                isdayschool=prev_school.isdayschool,
                iseveningschool=prev_school.iseveningschool,
                islexschool=prev_school.islexschool,

                #These fields get default value:
                #    activated=False,  is deprecated
                #    activatedat=None,  is deprecated
                #    locked=False,
                #    lockedat=None,

                modifiedby_id=prev_school.modifiedby_id,
                modifiedat=prev_school.modifiedat
            )
            new_school.save()

            log_list.append(get_iscopied_logtext(caption, new_school.name))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            log_list.append(get_error_logtext(caption, e))
        else:
            if new_school:
                mapped_schools[prev_school.pk] = new_school.pk

    if logging_on:
        logger.debug('mapped_schools: ' + str(mapped_schools))
    return mapped_schools
# - end of copy_schools_from_prev_examyear


def copy_subjecttypes_from_prev_examyear(prev_examyear_pk, mapped_schemes, log_list):
    # copy subjecttypes from previous examyear PR2021-04-25  PR2021-08-06 PR2022-08-01
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_subjecttypes_from_prev_examyear -------')

    mapped_subjecttypes = {}

    caption = _('Character')

# - loop through subjecttypes of prev examyear
    prev_subjecttypes = subj_mod.Subjecttype.objects.filter(
        scheme__department__examyear_id=prev_examyear_pk
    )
    for prev_sjtp in prev_subjecttypes:
        if logging_on:
            logger.debug('prev_sjtp: ' + str(prev_sjtp))

        try:
# get mapped values of scheme
            new_scheme_pk = mapped_schemes.get(prev_sjtp.scheme_id)

            new_sjtp = subj_mod.Subjecttype(
                base=prev_sjtp.base,
                scheme_id=new_scheme_pk,

                name=prev_sjtp.name,
                abbrev=prev_sjtp.abbrev,

                has_prac=prev_sjtp.has_prac,
                has_pws=prev_sjtp.has_pws,

                min_subjects=prev_sjtp.min_subjects,
                max_subjects=prev_sjtp.max_subjects,

                min_extra_nocount=prev_sjtp.min_extra_nocount,
                max_extra_nocount=prev_sjtp.max_extra_nocount,

                min_extra_counts=prev_sjtp.min_extra_counts,
                max_extra_counts=prev_sjtp.max_extra_counts,

                modifiedby_id=prev_sjtp.modifiedby_id,
                modifiedat=prev_sjtp.modifiedat
            )

# - copy new subjecttype to log happens in save(request=request)
            new_sjtp.save()

            log_list.append(get_iscopied_logtext(caption, new_sjtp.abbrev))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            log_list.append(get_error_logtext(caption, e))
        else:
            if new_sjtp:
                mapped_subjecttypes[prev_sjtp.pk] = new_sjtp.pk

    if logging_on:
        logger.debug('mapped_subjecttypes: ' + str(mapped_subjecttypes))
    return mapped_subjecttypes
# - end of copy_subjecttypes_from_prev_examyear


def copy_subjects_from_prev_examyear(prev_examyear_pk, new_examyear_pk, log_list):
    # copy subjects from previous examyear PR2021-04-25 PR2021-08-06 PR2022-08-01
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_subjects_from_prev_examyear -------')

    mapped_subjects = {}

    caption = _('Subject')

# - loop through subjects of prev examyear
    prev_subjects = subj_mod.Subject.objects.filter(
        examyear_id=prev_examyear_pk
    )
    for prev_subject in prev_subjects:
        if logging_on:
            logger.debug('prev_subject: ' + str(prev_subject))
        try:
            new_subject = subj_mod.Subject(
                base=prev_subject.base,
                examyear_id=new_examyear_pk,

                name_nl=prev_subject.name_nl,
                name_en=prev_subject.name_en,
                name_pa=prev_subject.name_pa,

                sequence=prev_subject.sequence,
                depbases=prev_subject.depbases,

                # PR201-10-11 moved from Subject to Schemitem
                #otherlang=prev_subject.otherlang,

                notatdayschool=prev_subject.notatdayschool,

                modifiedby_id=prev_subject.modifiedby_id,
                modifiedat=prev_subject.modifiedat
            )
            new_subject.save()

            log_list.append(get_iscopied_logtext(caption, new_subject.name_nl))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            log_list.append(get_error_logtext(caption, e))
        else:
            if new_subject:
                mapped_subjects[prev_subject.pk] = new_subject.pk

    if logging_on:
        logger.debug('mapped_subjects: ' + str(mapped_subjects))
    return mapped_subjects
# - end of copy_subjects_from_prev_examyear


def copy_schemes_from_prev_examyear(prev_examyear_pk, mapped_deps, mapped_levels, mapped_sectors, log_list):
    # copy schemes from previous examyear PR2021-04-25  PR2021-08-06 PR2022-08-01
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_schemes_from_prev_examyear -------')

    mapped_schemes = {}

    caption = _('Subject scheme')

# - loop through schemes of prev examyear
    prev_schemes = subj_mod.Scheme.objects.filter(
        department__examyear_id=prev_examyear_pk
    )
    for prev_scheme in prev_schemes:
        if logging_on:
            logger.debug('prev_scheme: ' + str(prev_scheme))
            logger.debug('prev_scheme.modifiedby_id: ' + str(prev_scheme.modifiedby_id))
            logger.debug('prev_scheme.modifiedat: ' + str(prev_scheme.modifiedat))

        try:
# get mapped values of dep. lvl and sct
            new_dep_pk = mapped_deps.get(prev_scheme.department_id)
            new_lvl_pk = mapped_levels.get(prev_scheme.level_id)
            new_sct_pk = mapped_sectors.get(prev_scheme.sector_id)

            new_scheme = subj_mod.Scheme(
                department_id=new_dep_pk,
                level_id=new_lvl_pk,
                sector_id=new_sct_pk,

                name=prev_scheme.name,
                fields=prev_scheme.fields,

                min_studyloadhours=prev_scheme.min_studyloadhours,

                min_subjects=prev_scheme.min_subjects,
                max_subjects=prev_scheme.max_subjects,

                min_mvt=prev_scheme.min_mvt,
                max_mvt=prev_scheme.max_mvt,

                min_wisk=prev_scheme.min_wisk,
                max_wisk=prev_scheme.max_wisk,

                min_combi=prev_scheme.min_combi,
                max_combi=prev_scheme.max_combi,
                max_reex=prev_scheme.max_reex,

                rule_avg_pece_sufficient=prev_scheme.rule_avg_pece_sufficient,
                rule_avg_pece_notatevlex=prev_scheme.rule_avg_pece_notatevlex,
                rule_core_sufficient=prev_scheme.rule_core_sufficient,
                rule_core_notatevlex=prev_scheme.rule_core_notatevlex,

                modifiedby=prev_scheme.modifiedby,
                modifiedat=prev_scheme.modifiedat
            )
            new_scheme.save()

            log_list.append(get_iscopied_logtext(caption, new_scheme.name))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            log_list.append(get_error_logtext(caption, e))
        else:
            if new_scheme:
                mapped_schemes[prev_scheme.pk] = new_scheme.pk

    if logging_on:
        logger.debug('mapped_schemes: ' + str(mapped_schemes))
    return mapped_schemes
# - end of copy_schemes_from_prev_examyear


def copy_schemeitems_from_prev_examyear(prev_examyear_pk, mapped_schemes, mapped_subjects, mapped_subjecttypes, log_list):
    # copy schemeitems from previous examyear PR2021-04-25 PR2021-08-06 PR2022-03-11 PR2022-08-01
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_schemeitems_from_prev_examyear -------')

    mapped_schemeitems = {}

# - loop through schemeitems of prev examyear
    prev_schemeitems = subj_mod.Schemeitem.objects.filter(
        scheme__department__examyear_id=prev_examyear_pk
    )
    count_copied, count_exists, count_error = 0, 0, 0
    for prev_si in prev_schemeitems:

        try:
# get mapped values of scheme, subject and subjecttype
            prev_si_pk = prev_si.pk
            new_scheme_pk = mapped_schemes.get(prev_si.scheme_id)

            new_subject_pk = mapped_subjects.get(prev_si.subject_id)

            # PR2023-01-04 new_is_mand_subj_pk is not tested yet:
            # is_mand_subj: only mandatory if student has this subject
            new_is_mand_subj_pk = mapped_subjects.get(prev_si.is_mand_subj_id)

            new_subjecttype_pk = mapped_subjecttypes.get(prev_si.subjecttype_id)

            new_si = subj_mod.Schemeitem(
                scheme_id=new_scheme_pk,
                subject_id=new_subject_pk,
                subjecttype_id=new_subjecttype_pk,

                ete_exam=prev_si.ete_exam,

                otherlang=prev_si.otherlang,
                no_order=prev_si.no_order,

                gradetype=prev_si.gradetype,
                weight_se=prev_si.weight_se,
                weight_ce=prev_si.weight_ce,
                multiplier=prev_si.multiplier,

                is_mandatory=prev_si.is_mandatory,
                is_mand_subj_id=new_is_mand_subj_pk,
                is_combi=prev_si.is_combi,

                extra_count_allowed=prev_si.extra_count_allowed,
                extra_nocount_allowed=prev_si.extra_nocount_allowed,

                has_practexam=prev_si.has_practexam,

                is_core_subject=prev_si.is_core_subject,
                is_mvt=prev_si.is_mvt,
                is_wisk=prev_si.is_wisk,

                rule_grade_sufficient=prev_si.rule_grade_sufficient,
                rule_gradesuff_notatevlex=prev_si.rule_gradesuff_notatevlex,

                sr_allowed=prev_si.sr_allowed,

                no_ce_years=prev_si.no_ce_years,
                thumb_rule=prev_si.thumb_rule,

                studyloadhours=prev_si.studyloadhours,
                notatdayschool=prev_si.notatdayschool,

                modifiedby_id=prev_si.modifiedby_id,
                modifiedat=prev_si.modifiedat
            )
            new_si.save()

            if logging_on and False:
                logger.debug('prev_si: ' + str(prev_si) + ' new_si: ' + str(new_si))
            count_copied += 1

            if new_si:
                mapped_schemeitems[prev_si_pk] = new_si.pk

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            log_list.append(get_error_logtext(_('subjectscheme item'), e))
            count_error += 1

    if logging_on:
        logger.debug('    mapped_schemeitems: ' + str(mapped_schemeitems))

    caption = _('subjectscheme items')
    log_list.append(c.STRING_SPACE_05 + str(_("%(count)s %(cpt)s are copied.") % {'count': str(count_copied), 'cpt': str(caption)}))

    if count_exists:
        log_list.append(c.STRING_SPACE_05 + str(_("%(count)s %(cpt)s already exist.") % {'count': str(count_exists)}))

    if count_error:
        log_list.append(c.STRING_SPACE_05 + str(_("%(count)s %(cpt)s have errors.") % {'count': str(count_error)}))

    if logging_on:
        logger.debug('    log_list: ' + str(log_list))
    return mapped_schemeitems
# - end of copy_schemeitems_from_prev_examyear

##############################

def copy_envelopbundles_from_prev_examyear(prev_examyear_pk, new_examyear_pk, log_list):
    # copy envelopbundles from previous examyear PR2022-08-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_envelopbundles_from_prev_examyear -------')

    mapped_envelopbundles = {}

    caption = _('Label bundle')

    prev_envelopbundles = subj_mod.Envelopbundle.objects.filter(
        examyear_id=prev_examyear_pk
    )
    for prev_bndl in prev_envelopbundles:
        if logging_on:
            logger.debug('prev_bndl: ' + str(prev_bndl))

        try:
            new_bndl = subj_mod.Envelopbundle(
                base=prev_bndl.base,
                examyear_id=new_examyear_pk,

                name=prev_bndl.name,

                modifiedby_id=prev_bndl.modifiedby_id,
                modifiedat=prev_bndl.modifiedat
            )
            new_bndl.save()

            log_list.append(get_iscopied_logtext(caption, new_bndl.name))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            log_list.append(get_error_logtext(caption, e))
        else:
            if new_bndl:
                mapped_envelopbundles[prev_bndl.pk] = new_bndl.pk

    if logging_on:
        logger.debug('mapped_envelopbundles: ' + str(mapped_envelopbundles))
    return mapped_envelopbundles
# - end of copy_envelopbundles_from_prev_examyear


def copy_enveloplabels_from_prev_examyear(prev_examyear_pk, new_examyear_pk, log_list):
    # copy enveloplabels from previous examyear PR2022-08-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_enveloplabels_from_prev_examyear -------')

    mapped_enveloplabels = {}

    caption = _('Label')

# - loop through enveloplabels of prev examyear
    prev_enveloplabels = subj_mod.Enveloplabel.objects.filter(
        examyear_id=prev_examyear_pk
    )
    for prev_lbl in prev_enveloplabels:
        if logging_on:
            logger.debug('prev_lbl: ' + str(prev_lbl))

        try:
            new_lbl = subj_mod.Enveloplabel(
                base=prev_lbl.base,
                examyear_id=new_examyear_pk,

                name=prev_lbl.name,

                is_errata=prev_lbl.is_errata,
                is_variablenumber=prev_lbl.is_variablenumber,
                numberinenvelop=prev_lbl.numberinenvelop,
                numberofenvelops=prev_lbl.numberofenvelops,

                modifiedby_id=prev_lbl.modifiedby_id,
                modifiedat=prev_lbl.modifiedat
            )
            new_lbl.save()

            log_list.append(get_iscopied_logtext(caption, new_lbl.name))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            log_list.append(get_error_logtext(caption, e))
        else:
            if new_lbl:
                mapped_enveloplabels[prev_lbl.pk] = new_lbl.pk

    if logging_on:
        logger.debug('mapped_enveloplabels: ' + str(mapped_enveloplabels))

    return mapped_enveloplabels
# - end of copy_enveloplabels_from_prev_examyear


def copy_envelopitems_from_prev_examyear(prev_examyear_pk, new_examyear_pk, log_list):
    # copy envelopitems from previous examyear PR2022-08-23
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_envelopitems_from_prev_examyear -------')

    mapped_envelopitems = {}

    caption = _('Label text')

    prev_envelopitems = subj_mod.Envelopitem.objects.filter(
        examyear_id=prev_examyear_pk
    )
    for prev_itm in prev_envelopitems:
        if logging_on:
            logger.debug('prev_itm: ' + str(prev_itm))

        try:
            new_itm = subj_mod.Envelopitem(
                base=prev_itm.base,
                examyear_id=new_examyear_pk,

                content_nl=prev_itm.content_nl,
                content_en=prev_itm.content_en,
                content_pa=prev_itm.content_pa,

                instruction_nl=prev_itm.instruction_nl,
                instruction_en=prev_itm.instruction_en,
                instruction_pa=prev_itm.instruction_pa,

                content_color=prev_itm.content_color,
                instruction_color=prev_itm.instruction_color,

                modifiedby_id=prev_itm.modifiedby_id,
                modifiedat=prev_itm.modifiedat
            )
            new_itm.save()

            log_list.append(get_iscopied_logtext(caption, new_itm.content_nl))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            log_list.append(get_error_logtext(caption, e))
        else:
            if new_itm:
                mapped_envelopitems[prev_itm.pk] = new_itm.pk

    if logging_on:
        logger.debug('mapped_envelopitems: ' + str(mapped_envelopitems))

    return mapped_envelopitems
# - end of copy_envelopitems_from_prev_examyear



def copy_envelopbundlelabels_from_prev_examyear(prev_examyear_pk, mapped_envelopbundles, mapped_enveloplabels, log_list):
    # copy schemeitems from previous examyear PR2021-04-25 PR2021-08-06 PR2022-03-11 PR2022-08-01
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_schemeitems_from_prev_examyear -------')

    mapped_schemeitems = {}

# - loop through schemeitems of prev examyear
    prev_envelopbundlelabels = subj_mod.Envelopbundlelabel.objects.filter(
        envelopbundle_id__examyear_id=prev_examyear_pk
    )
    count_copied, count_exists, count_error = 0, 0, 0
    for prev_bndlbl in prev_envelopbundlelabels:

        try:
# get mapped values of scheme, subject and subjecttype
            prev_bndlbl_pk = prev_bndlbl.pk
            new_envelopbundle_pk = mapped_envelopbundles.get(prev_bndlbl.envelopbundle_id)
            new_enveloplabel_pk = mapped_enveloplabels.get(prev_bndlbl.enveloplabel_id)

            new_bndlbl = subj_mod.Envelopbundlelabel(
                envelopbundle_id=new_envelopbundle_pk,
                enveloplabel_id=new_enveloplabel_pk,

                modifiedby_id=prev_bndlbl.modifiedby_id,
                modifiedat=prev_bndlbl.modifiedat
            )
            new_bndlbl.save()

            if logging_on and False:
                logger.debug('prev_bndlbl: ' + str(prev_bndlbl) + ' new_bndlbl: ' + str(new_bndlbl))
            count_copied += 1

            if new_bndlbl:
                mapped_schemeitems[prev_bndlbl_pk] = new_bndlbl.pk

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            log_list.append(get_error_logtext(_('envelopbundle label'), e))
            count_error += 1

    caption = _('envelopbundle labels')
    log_list.append(c.STRING_SPACE_05 + str(_("%(count)s %(cpt)s are copied.") % {'count': str(count_copied), 'cpt': str(caption)}))

    if count_error:
        log_list.append(c.STRING_SPACE_05 + str(_("%(count)s %(cpt)s have errors.") % {'count': str(count_error)}))

    if logging_on:
        logger.debug('    log_list: ' + str(log_list))
# - end of copy_envelopbundlelabels_from_prev_examyear


def copy_enveloplabelitems_from_prev_examyear(prev_examyear_pk, mapped_enveloplabels, mapped_envelopitems, log_list):
    # copy schemeitems from previous examyear PR2021-04-25 PR2021-08-06 PR2022-03-11 PR2022-08-01
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_enveloplabelitems_from_prev_examyear -------')

    mapped_schemeitems = {}

# - loop through schemeitems of prev examyear
    prev_enveloplabelitems = subj_mod.Enveloplabelitem.objects.filter(
        enveloplabel__examyear_id=prev_examyear_pk
    )
    count_copied, count_error = 0, 0

    for prev_lblitm in prev_enveloplabelitems:
        try:
# get mapped values of scheme, subject and subjecttype
            prev_lblitm_pk = prev_lblitm.pk
            new_enveloplabel_pk = mapped_enveloplabels.get(prev_lblitm.enveloplabel_id)
            new_envelopitem_pk = mapped_envelopitems.get(prev_lblitm.envelopitem_id)

            new_lblitm = subj_mod.Enveloplabelitem(
                enveloplabel_id=new_enveloplabel_pk,
                envelopitem_id=new_envelopitem_pk,

                sequence=prev_lblitm.sequence,

                modifiedby_id=prev_lblitm.modifiedby_id,
                modifiedat=prev_lblitm.modifiedat
            )
            new_lblitm.save()

            if logging_on and False:
                logger.debug('prev_lblitm: ' + str(prev_lblitm) + ' new_lblitm: ' + str(new_lblitm))
            count_copied += 1

            if new_lblitm:
                mapped_schemeitems[prev_lblitm_pk] = new_lblitm.pk

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            log_list.append(get_error_logtext(_('label text'), e))
            count_error += 1

    caption = _('label text')
    log_list.append(c.STRING_SPACE_05 + str(_("%(count)s %(cpt)s are copied.") % {'count': str(count_copied), 'cpt': str(caption)}))

    if count_error:
        log_list.append(c.STRING_SPACE_05 + str(_("%(count)s %(cpt)s have errors.") % {'count': str(count_error)}))

    if logging_on:
        logger.debug('    log_list: ' + str(log_list))
# - end of copy_enveloplabelitems_from_prev_examyear


def copy_exams_from_prev_examyear(prev_examyear_pk, mapped_deps, mapped_levels, mapped_subjects, mapped_envelopbundles, log_list):
    # copy exams from previous examyear PR2022-08-07  PR2022-12-16
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_exams_from_prev_examyear -------')

# - loop through exams of prev examyear
    prev_exams = subj_mod.Exam.objects.filter(
        department__examyear_id=prev_examyear_pk
    )
    count_copied, count_exists, count_error = 0, 0, 0
    for prev_exam in prev_exams:

        try:
# get mapped values of departmen, level and subject
            new_dep_pk = mapped_deps.get(prev_exam.department_id)
            new_lvl_pk = mapped_levels.get(prev_exam.level_id)
            new_subject_pk = mapped_subjects.get(prev_exam.subject_id)
            new_envelopbundle_pk = mapped_envelopbundles.get(prev_exam.envelopbundle_id)

            new_exam = subj_mod.Exam(
                subject_id=new_subject_pk,
                department_id=new_dep_pk,
                level_id=new_lvl_pk,

                # ntermentable is not copied

                ete_exam=prev_exam.ete_exam,
                examperiod=prev_exam.examperiod,
                version=prev_exam.version,

                envelopbundle_id=new_envelopbundle_pk,
                has_errata=False,
                subject_color=prev_exam.subject_color,
                evl_modifiedby=prev_exam.evl_modifiedby,
                evl_modifiedat=prev_exam.evl_modifiedat,

                modifiedby_id=prev_exam.modifiedby_id,
                modifiedat=prev_exam.modifiedat
            )
            new_exam.save()

            if logging_on and False:
                logger.debug('prev_si: ' + str(prev_exam) + ' new_exam: ' + str(new_exam))
            count_copied += 1

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            log_list.append(get_error_logtext(_('subjectscheme item'), e))
            count_error += 1

    caption = _('exams')
    log_list.append(c.STRING_SPACE_05 + str(_("%(count)s %(cpt)s are copied.") % {'count': str(count_copied), 'cpt': str(caption)}))

    if count_exists:
        log_list.append(c.STRING_SPACE_05 + str(_("%(count)s %(cpt)s already exist.") % {'count': str(count_exists)}))

    if count_error:
        log_list.append(c.STRING_SPACE_05 + str(_("%(count)s %(cpt)s have errors.") % {'count': str(count_error)}))

    if logging_on:
        logger.debug('    log_list: ' + str(log_list))

# - end of copy_exams_from_prev_examyear


def copy_packages_from_prev_examyear(prev_examyear_pk, mapped_schemes, log_list):
    # copy packages from previous examyear PR2021-04-25 PR2021-08-06 PR2022-08-01
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_packages_from_prev_examyear -------')

    mapped_packages = {}

    caption = _('Package')

# - loop through packages of prev examyear
    prev_packages = subj_mod.Package.objects.filter(
        scheme__department__examyear_id=prev_examyear_pk
    )
    for prev_package in prev_packages:
        if logging_on:
            logger.debug('prev_package: ' + str(prev_package))

        try:

# get mapped values of scheme
            new_scheme_pk = mapped_schemes.get(prev_package.scheme_id)

# - first check if package already exists - don't overwrite existing packages
            new_package = subj_mod.Package.objects.filter(
                scheme_id=new_scheme_pk
            ).order_by('pk').first()

            if new_package:
                log_list.append(get_alreadyexists_logtext(caption, new_package.name))
            else:
# - create new package if it does not exist yet
                new_package = subj_mod.Package(
                    scheme_id=new_scheme_pk,

                    name=prev_package.name,

                    modifiedby_id=prev_package.modifiedby_id,
                    modifiedat=prev_package.modifiedat
                )
    # - copy new package to log happens in save(request=request)
                new_package.save()

                log_list.append(get_iscopied_logtext(caption, new_package.name))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            log_list.append(get_error_logtext(caption, e))
        else:
            if new_package:
                mapped_packages[prev_package.pk] = new_package.pk

    if logging_on:
        logger.debug('mapped_packages: ' + str(mapped_packages))
    return mapped_packages
# - end of copy_packages_from_prev_examyear


def copy_packageitems_from_prev_examyear(prev_examyear_pk, mapped_packages, mapped_schemeitems, log_list):
    # copy packageitems from previous examyear PR2021-04-25 PR2021-08-06 PR2022-08-01
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- copy_sectors_from_prev_examyear -------')

    count_copied, count_exists, count_error = 0, 0, 0

# - loop through packageitems of prev examyear
    prev_packageitems = subj_mod.Packageitem.objects.filter(
        package__scheme__department__examyear_id=prev_examyear_pk
    )
    for prev_pi in prev_packageitems:
        if logging_on:
            logger.debug('prev_pi: ' + str(prev_pi))
        try:

# get mapped values of packages and schemeitems
            new_package_pk = mapped_packages.get(prev_pi.package_id)
            new_schemeitem_pk = mapped_schemeitems.get(prev_pi.schemeitem_id)

# - first check if packageitem already exists - don't overwrite existing packageitems
            new_pi = subj_mod.Packageitem.objects.filter(
                package_id=new_package_pk,
                schemeitem_id=new_schemeitem_pk
            ).order_by('pk').first()

            if new_pi:
                count_exists += 1
            else:
# - create new packageitem if it does not exist yet
                new_pi = subj_mod.Packageitem(
                    package_id=new_package_pk,
                    schemeitem_id=new_schemeitem_pk,

                    modifiedby_id=prev_pi.modifiedby_id,
                    modifiedat=prev_pi.modifiedat
                )

# - copy new packageitems to log happens in save(request=request)
                new_pi.save()

                count_copied += 1

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
            log_list.append(get_error_logtext(_('package item'), e))
            count_error += 1

    caption = _('package items')
    log_list.append(c.STRING_SPACE_05 + str(_("%(count)s %(cpt)s are copied.") % {'count': str(count_copied), 'cpt': str(caption)}))
    log_list.append(c.STRING_SPACE_05 + str(_("%(count)s %(cpt)s already exist.") % {'count': str(count_exists)}))
    log_list.append(c.STRING_SPACE_05 + str(_("%(count)s %(cpt)s have errors.") % {'count': str(count_error)}))
# - end of copy_packageitems_from_prev_examyear


def get_previous_examyear_instance(new_examyear_instance):
    # get previous examyear of this country from new_examyear, check if it exists # PR2019-02-23 PR2020-10-06

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ------- get_previous_examyear_instance -------')
        logger.debug('new_examyear_instance: ' + str(new_examyear_instance) + ' ' + str(type(new_examyear_instance)))

    prev_examyear_instance = None
    msg_err = None
    if new_examyear_instance is not None:
        new_examyear_code_int = new_examyear_instance.code
        prev_examyear_int = int(new_examyear_code_int) - 1
        prev_examyear_instance = sch_mod.Examyear.objects.get_or_none(
            country=new_examyear_instance.country,
            code=prev_examyear_int)
        if logging_on:
            logger.debug('prev_examyear_int: ' + str(prev_examyear_int) + ' ' + str(type(prev_examyear_int)))
            logger.debug('prev_examyear_instance: ' + str(prev_examyear_instance) + ' ' + str(type(prev_examyear_instance)))

        if prev_examyear_instance is None:
            prev_examyear_count = sch_mod.Examyear.objects.filter(
                country=new_examyear_instance.country,
                code=prev_examyear_int).count()
            if prev_examyear_count:
                msg_err = _("Multiple instances of previous exam year %(ey_yr) were found. Please delete duplicates first.")
            else:
                msg_err = _("Previous exam year %(ey_yr) is not found. Please create the previous exam year first.")
    return prev_examyear_instance, msg_err


def get_department(old_examyear, new_examyear):
    # get previous examyear of this country from new_examyear, check if it exists # PR2019-02-23
    prev_examyear = None
    if new_examyear is not None:
        prev_examyear_int = int(new_examyear.code) - 1
        prev_examyear = sch_mod.Department.objects.filter(
            country=new_examyear.country,
            examyear=prev_examyear_int
        ).first()
    return prev_examyear


# ===============================
def get_schoolsettings(request, request_item_setting, sel_examyear, sel_schoolbase, sel_depbase):
    # PR2020-04-17 PR2020-12-28  PR2021-01-12 PR2022-03-19
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ---------------- get_schoolsetting ---------------- ')
        logger.debug('    request_item_setting: ' + str(request_item_setting))
        logger.debug('    sel_examyear: ' + str(sel_examyear))
        logger.debug('    sel_schoolbase: ' + str(sel_schoolbase))
        logger.debug('    sel_depbase: ' + str(sel_depbase))

    # only called by DatalistDownloadView
    # setting_keys are: 'import_subject', 'import_studsubj', 'import_subject'. 'import_grade', 'import_permit'
    # TODO: add 'import_user'

    setting_key = request_item_setting.get('setting_key')
    schoolsetting_dict = {}
    if setting_key:
        if setting_key in (c.KEY_IMPORT_SUBJECT, c.KEY_IMPORT_STUDENT, c.KEY_IMPORT_STUDENTSUBJECT,
                           c.KEY_IMPORT_GRADE, c.KEY_IMPORT_PERMITS, c.KEY_IMPORT_USERNAME):
            sel_examyear_pk = sel_examyear.pk if sel_examyear else None
            sel_examyear_code = sel_examyear.code if sel_examyear else None
            sel_schoolbase_pk = sel_schoolbase.pk if sel_schoolbase else None
            sel_schoolbase_code = sel_schoolbase.code if sel_schoolbase else None
            sel_depbase_pk = sel_depbase.pk if sel_depbase else None
            sel_depbase_code = sel_depbase.code if sel_depbase else None
            sel_school_pk = None
            sel_school_name = None
            if sel_examyear and sel_schoolbase:
                sel_school = sch_mod.School.objects.get_or_none(
                    base=sel_schoolbase,
                    examyear=sel_examyear
                )
                if sel_school:
                    sel_school_pk = sel_school.pk
                    sel_school_name = sel_school.name

            schoolsetting_dict = {'sel_examyear_pk': sel_examyear_pk,
                                  'sel_examyear_code': sel_examyear_code,
                                  'sel_schoolbase_pk': sel_schoolbase_pk,
                                  'sel_schoolbase_code': sel_schoolbase_code,
                                  'sel_depbase_pk': sel_depbase_pk,
                                  'sel_depbase_code': sel_depbase_code,
                                  'sel_school_pk': sel_school_pk,
                                  'sel_school_name': sel_school_name}
            schoolsetting_dict[setting_key] = get_stored_coldefs_dict(request, setting_key, sel_examyear, sel_schoolbase, sel_depbase)
        else:
            schoolsetting_dict[setting_key] = sel_schoolbase.get_schoolsetting_dict(setting_key)

    if logging_on:
        logger.debug('setting_key: ' + str(setting_key) + ' ' + str(type(setting_key)))
        logger.debug('schoolsetting_dict: ' + str(schoolsetting_dict))
    return schoolsetting_dict


# ===============================
def get_stored_coldefs_dict(request, setting_key, sel_examyear, sel_schoolbase, sel_depbase):  # PR2021-08-01
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ---------------- get_stored_coldefs_dict ---------------- ')
        logger.debug('    setting_key: ' + str(setting_key))
        logger.debug('    sel_depbase: ' + str(sel_depbase))

    # stored_settings_dict: {'worksheetname': 'Compleetlijst', 'has_header': True,
    # 'coldef': {'idnumber': 'ID', 'classname': 'KLAS', 'department': 'Vakantiedagen', 'level': 'Payrollcode', 'sector': 'Profiel'},
    # 'department': {'21': 2},
    # 'level': {'W6': 1, 'W3': 2, 'W2': 3},
    # 'sector': {'EM': 3, 'CM': 4, 'NT': 7}}

# - first get info from sel_school
    # sel_schoolbase can be different from request.user.schoolbase
    # This can be the case when role insp, admin or system has selected different school
    # only import students from the selected department
    # only add 'department' to coldefs and tablelist when school has multiple departments
    sel_school = sch_mod.School.objects.get_or_none(base=sel_schoolbase, examyear=sel_examyear)

# - is_level_req / is_sector_req is True when _req is True in the selected department of sel_school
    is_level_req = False
    is_sector_req = False
    has_profiel = False
    sel_department = None
    school_has_multiple_deps = False
    if sel_school:
        sel_school_depbases_list = get_list_int_from_delim_string(sel_school.depbases)
        if sel_school_depbases_list and len(sel_school_depbases_list) > 1:
            school_has_multiple_deps = True

        if logging_on:
            logger.debug('    sel_school.depbases: ' + str(sel_school.depbases))
            logger.debug('    sel_school_depbases_list: ' + str(sel_school_depbases_list))
            logger.debug('    school_has_multiple_deps: ' + str(school_has_multiple_deps))

        if sel_depbase and sel_school_depbases_list and sel_depbase.pk in sel_school_depbases_list:
            sel_department = sch_mod.Department.objects.get_or_none(base=sel_depbase, examyear=sel_examyear)
            if sel_department:
                is_level_req = sel_department.level_req
                is_sector_req = sel_department.sector_req
                has_profiel = sel_department.has_profiel

# - get Schoolsetting from sel_schoolbase, not from request.user.schoolbase
    # (sel_schoolbase may be different from user.schoolbase when role is comm, insp, adm, system)
    stored_settings_dict = sel_schoolbase.get_schoolsetting_dict(setting_key)
    if logging_on:
        logger.debug('stored_settings_dict: ' + str(stored_settings_dict))
        logger.debug('    setting_key: ' + str(setting_key))
        logger.debug('    sel_school: ' + str(sel_school))
        logger.debug('    sel_department: ' + str(sel_department))

    noheader = False
    worksheetname = ''
    examgradetype = None
    coldef_list = []
    stored_coldef = {}

# - get list of tables needed for uploading
    if setting_key == c.KEY_IMPORT_STUDENT:
        if school_has_multiple_deps:
            table_list = ("coldef", "department", "level", "sector", "profiel")
        else:
            table_list = ("coldef", "level", "sector", "profiel")
    elif setting_key == c.KEY_IMPORT_GRADE:
        # PR2021-08-11 subjecttype NIU was: table_list = ("coldef", "subject", "subjecttype")
        # 'subject' comes first, subject values are used in coldef to exclude linked subjects from coldef list PR2021-08-11
        table_list = ("subject", "coldef")
    elif setting_key == c.KEY_IMPORT_STUDENTSUBJECT:
        # PR2021-08-11 subjecttype NIU was: table_list = ("coldef", "subject", "subjecttype")
        # 'subject' comes first, subject values are used in coldef to exclude linked subjects from coldef list PR2021-08-11
        table_list = ("subject", "coldef")
    else:
        table_list = ("coldef",)

    if setting_key and sel_school:
        if stored_settings_dict:
            noheader = stored_settings_dict.get('noheader', False)
            worksheetname = stored_settings_dict.get('worksheetname')
            examgradetype = stored_settings_dict.get('examgradetype')
            stored_coldef = stored_settings_dict.get('coldef')

        default_coldef_list = c.KEY_COLDEF.get(setting_key)

# - remove 'department' from coldefs if school has ony 1 department
        if setting_key == c.KEY_IMPORT_STUDENT:
            if not school_has_multiple_deps:
                index_tobe_removed = None

                for i, coldef_dict in enumerate(default_coldef_list):
                    if coldef_dict.get('awpColdef') == 'department':
                        index_tobe_removed = i
                        break
                if index_tobe_removed:
                    del default_coldef_list[index_tobe_removed]
        if logging_on:
            logger.debug('stored_coldef: ' + str(stored_coldef))
            logger.debug('    default_coldef_list: ' + str(default_coldef_list))
        """
        KEY_IMPORT_USERNAME default_coldef_list: [
            {'awpColdef': 'schoolcode', 'caption': 'Schoolcode', 'linkrequired': True}, 
            {'awpColdef': 'username', 'caption': 'Gebruikersnaam', 'linkrequired': True}, 
            {'awpColdef': 'last_name', 'caption': 'Naam', 'linkrequired': True},
             {'awpColdef': 'email', 'caption': 'Email', 'linkrequired': True}, 
             {'awpColdef': 'function', 'caption': 'Functie'}]

        """

# +++ loop through default_coldef_list
        if default_coldef_list:
            for dict in default_coldef_list:
                awpColdef = dict.get('awpColdef')

# - only add level or sector when sel_department has is_level_req=True / is_sector_req=True
                # sector and profiel are 2 different items. Choose the one that is applicable
                if awpColdef == 'level':
                    add_to_list = is_level_req
                elif awpColdef == 'sector':
                    add_to_list = is_sector_req and not has_profiel
                elif awpColdef == 'profiel':
                    add_to_list = is_sector_req and has_profiel
                elif awpColdef == 'schoolcode':
                    # only occurs in KEY_IMPORT_USERNAME: skip schoolcode when school wants to import users
                    add_to_list = not request.user.is_role_school
                else:
                    add_to_list = True

# --- loop through stored_coldef, add excColdef to corresponding item in coldef_list
                if add_to_list:
                    # stored_coldef: {'examnumber': 'exnr', 'classname': 'KLAS', 'level': 'Payrollcode', 'sector': 'Profiel'}
                    if stored_coldef:
                        stored_excColdef = None
                        for stored_awpColdef in stored_coldef:
                            if stored_awpColdef == awpColdef:
                                stored_excColdef = stored_coldef.get(stored_awpColdef)
                                break
                        if stored_excColdef:
                            dict['excColdef'] = stored_excColdef
                    coldef_list.append(dict)

    setting_dict = {
        'worksheetname': worksheetname,
        'noheader': noheader,
        'examgradetype': examgradetype,
        'coldefs': coldef_list,
        'tablelist': table_list
        }

# create list of required levels and sectors with excColdef when linked
    # 'profiel' also stored in table 'sector', but is separate item in import

    if table_list:
        for tblName in table_list:
            # PR2021-08-11 subjecttype NIU was: if tblName in ('department', 'level', 'sector', 'profiel', 'subject', 'subjecttype'):
            if tblName in ('department', 'level', 'sector', 'profiel', 'subject'):
    # - only add list of level / sector when _req is True in sel_department
                if tblName == 'level':
                    is_req = is_level_req
                elif tblName in ('sector', 'profiel'):
                    is_req = is_sector_req
                else:
                    #TODO set isreq for dep, subj, subjtype
                    is_req = True

                if is_req:
                    tbl_instances = []
                    instances = None

        # - reverse the stored_dict : convert {'ned': 4} to {4: 'ned'} to speed up search
                    reversed_dict = {}
                    stored_dict = stored_settings_dict.get(tblName) if stored_settings_dict else None
                    if logging_on:
                        logger.debug('tblName: ' + str(tblName))
                        logger.debug('    stored_dict: ' + str(stored_dict))

                    if stored_dict:
                        for excValue, awpBasePk in stored_dict.items():
                            reversed_dict[awpBasePk] = excValue

        # - get all instances of tblNmae of sel_examyear
                    if tblName == 'department':
                        instances = sch_mod.Department.objects.filter(examyear=sel_examyear)
                    elif tblName == 'level':
                        instances = subj_mod.Level.objects.filter(examyear=sel_examyear)
                    elif tblName in ('sector', 'profiel'):
                        instances = subj_mod.Sector.objects.filter(examyear=sel_examyear)
                    elif tblName == 'subject':
                       instances = subj_mod.Subject.objects.filter(examyear=sel_examyear)

                        # TODO add filter on notatdayschool with create_subject_rows
                        #    skip_notatdayschool = get_skip_notatdayschool(sel_school, request)
                        #rows = subj_vw.create_subject_rows(
                        #    request=request,
                        #    sel_examyear=sel_examyear,
                        #    sel_depbase=sel_depbase,
                        #    sel_lvlbase=None,
                       #     skip_allowed_filter=skip_allowed_filter,
                        #    skip_notatdayschool=skip_notatdayschool,
                        #    cur_dep_only=cur_dep_only)

                    # PR2021-08-11 NIU:
                    #elif tblName == 'subjecttype':
                    #    # PR2021-07-20 switched to subjecttypebase, because subjecttype is now per scheme
                    #    instances = subj_mod.Subjecttypebase.objects.all()

        # - loop through instances of this examyear
                    for instance in instances:

            # - check if one of the depbases of the instance is in the list of depbases of the school
                        add_to_list = False
                        if sel_department:
                            if tblName == 'department':
                    # if department: check if depbasePk is in school_depbasePk_list
                                # PR2022-06-26 tried to also import students from other departments.
                                # Better not do it, beacuse you need to link sectors + profiles at the same time.
                                # Keep:  'if instance == sel_department:'
                                if instance == sel_department:
                                    add_to_list = True

                    # if subjecttype: check if subjecttype.scheme.department is in school_depbasePk_list
                            # PR2021-07-20 switched to subjecttypebase, get all rows
                            #elif tblName == 'subjecttype':
                            #    add_to_list = True

                            elif instance.depbases:
                    # in other tables: only add if sel_depbase.pk is in depbases
                                # PR20210-05-04 debug . imported depbases may contain ';2;3;',
                                # which give error:  invalid literal for int() with base 10: ''
                                # was: depbases_str_list = instance.depbases.split(';') if instance.depbases else None
                                #       depbases_list = list(map(int, depbases_str_list)) if depbases_str_list else None
                                depbases_list = []
                                if instance.depbases:
                                    depbases_str_list = instance.depbases.split(';')
                                    for depbase_pk_str in depbases_str_list:
                                        if depbase_pk_str:
                                            depbases_list.append(int(depbase_pk_str))

                                if sel_depbase.pk in depbases_list:
                                    if tblName == 'sector':
                                        add_to_list = not has_profiel
                                    elif tblName == 'profiel':
                                        add_to_list = has_profiel
                                    else:
                                        add_to_list = True

                        if add_to_list:
                            #if tblName == 'subjecttype':
                            #    instance_basePk = instance.pk
                            #else:
                            instance_basePk = instance.base.pk

                            instance_value = None
                            if tblName in ('department', 'subject'):
                                instance_value = instance.base.code if instance.base.code else None
                            # NIU was: elif tblName in ('level', 'sector', 'profiel', 'subjecttype'):
                            elif tblName in ('level', 'sector', 'profiel'):
                                instance_value = instance.abbrev if instance.abbrev else None
                            dict = {'awpBasePk': instance_basePk, 'awpValue': instance_value}
                            if reversed_dict:
                                #  reversed_dict =  {3: 'EM', 4: 'CM', 7: 'NT'}
                                # - add excValue when this subject is linked
                                if reversed_dict and instance_basePk in reversed_dict:
                                    dict['excValue'] = reversed_dict[instance_basePk]
                            tbl_instances.append(dict)
                    if tbl_instances:
                        setting_dict[tblName] = tbl_instances

    if logging_on:
        logger.debug('setting_dict: ' + str(setting_dict))
        logger.debug(' ---------------- end of get_stored_coldef_dict ---------------- ')

    """
    setting_dict: {'worksheetname': 'Kandidaten', 'noheader': False, 'examgradetype': None, 
        'coldefs': [
                {'awpColdef': 'idnumber', 'caption': 'ID-nummer', 'linkrequired': True, 'unique': True, 'excColdef': 'ID-nummer'}, 
                {'awpColdef': 'lastname', 'caption': 'Achternaam', 'linkrequired': True, 'excColdef': 'Achternaam'}, 
                {'awpColdef': 'firstname', 'caption': 'Voornamen', 'linkrequired': True, 'excColdef': 'Voornamen'}, 
                {'awpColdef': 'prefix', 'caption': 'Voorvoegsel', 'excColdef': 'Voorvoegsel'}, 
                {'awpColdef': 'gender', 'caption': 'Geslacht', 'excColdef': 'Geslacht'}, 
                {'awpColdef': 'examnumber', 'caption': 'Examennummer', 'excColdef': 'Examennummer'}, 
                {'awpColdef': 'birthdate', 'caption': 'Geboortedatum', 'datefield': True, 'excColdef': 'Geboortedatum'}, 
                {'awpColdef': 'birthcountry', 'caption': 'Geboorteland', 'excColdef': 'Geboorteland'}, 
                {'awpColdef': 'birthcity', 'caption': 'Geboorteplaats', 'excColdef': 'Geboorteplaats'}, 
                {'awpColdef': 'classname', 'caption': 'Klas', 'excColdef': 'Klas'}, 
                {'awpColdef': 'bis_exam', 'caption': 'Bis-examen'}, 
                {'awpColdef': 'department', 'caption': 'Afdeling', 'excColdef': 'Afdeling'}, 
                {'awpColdef': 'level', 'caption': 'Leerweg', 'linkrequired': True, 'excColdef': 'Leerweg'},
                 {'awpColdef': 'sector', 'caption': 'Sector', 'linkrequired': True, 'excColdef': 'Sector___Profiel'}, 
                 {'awpColdef': 'diplomanumber', 'caption': 'Diploma-nummer'}, 
                 {'awpColdef': 'gradelistnumber', 'caption': 'Cijferlijst-nummer'}], 
             'tablelist': ('coldef', 'department', 'level', 'sector', 'profiel'), 
             'department': [{'awpBasePk': 1, 'awpValue': 'Vsbo'}], 
             'level': [{'awpBasePk': 6, 'awpValue': 'PBL'}, {'awpBasePk': 5, 'awpValue': 'PKL'}, {'awpBasePk': 4, 'awpValue': 'TKL'}], 
             'sector': [{'awpBasePk': 12, 'awpValue': 'tech'}, {'awpBasePk': 13, 'awpValue': 'ec'}, {'awpBasePk': 14, 'awpValue': 'z&w'}]}

    """


    return setting_dict


def get_list_int_from_delim_string(delim_string):
    # PR2022-08-21 NIU yet
    int_list = []
    if delim_string:
        str_list = delim_string.split(';')
        if str_list:
            int_list = list(map(int, str_list))
    return int_list


def get_alreadyexists_logtext(caption, value): # PR2021-09-26
    return c.STRING_SPACE_05 + str(_("%(cpt)s '%(val)s' already exists.") % {'cpt': caption, 'val': value})


def get_iscopied_logtext(caption, value): # PR2021-09-26
    return c.STRING_SPACE_05 + str(_("%(cpt)s '%(val)s' is copied.") % {'cpt': caption, 'val': value})


def get_error_logtext(caption, error): # PR2021-09-26
    cpt = caption.lower() if caption else ''
    return c.STRING_SPACE_05 + str(_("Error copying %(cpt)s: %(error)s") % {'cpt': cpt, 'val': str(error)})


def get_skip_notatdayschool(sel_school, request):
    # PR2022-08-21 notatdayschool added: show this subject only when school is evening school or lex school
    # attention: day/evening school shows notatdayschool subjects. Must be filtered out when adding subjects to day student
    # also don't filter on notatdayschool when user is admin

    skip_notatdayschool = (sel_school and sel_school.islexschool) or \
                          (sel_school and sel_school.iseveningschool) or \
                          (request.user.role > c.ROLE_016_CORR)
    return skip_notatdayschool