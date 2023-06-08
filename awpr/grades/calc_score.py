# PR2022-04-19
from decimal import Decimal
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import gettext_lazy as _
from django.db import connection

from awpr import constants as c
from awpr import settings as s
from awpr import functions as af

from grades import calculations as grade_calc
from grades import calc_finalgrade as calc_final
from grades import calc_results as calc_result
import logging
logger = logging.getLogger(__name__)


"""
from: https://wetten.overheid.nl/BWBR0037590/2021-04-10
Regeling van het College voor Toetsen en Examens van 30 november 2015, nummer CvTE-15.02159, 
houdende vaststelling van regels voor de omzetting van scores in cijfers bij centrale examens en de rekentoets in het voortgezet onderwijs 
(Regeling omzetting scores in cijfers centrale examens en rekentoets VO 2016)

'Regeling van het College voor Toetsen en Examens van 9 februari 2015, nummer CvTE-15.00618,
'houdende vaststelling van regels voor de omzetting van scores in cijfers bij centrale examens en de rekentoets in het voortgezet onderwijs
'(Regeling omzetting scores in cijfers centrale examens en rekentoets VO 2015)

Het systeem voor de omzetting van score naar cijfer is gebaseerd op de volgende vier uitgangspunten:
    1. Elk gescoord punt draagt altijd bij tot een hoger examencijfer (afronding daargelaten);
    2. Een score van 0% correspondeert altijd met examencijfer 1,0;
    3. Een score van 100% correspondeert altijd met examencijfer 10,0;
    4. Over een zo breed mogelijk centraal interval van de scoreschaal is er (afronding daargelaten) sprake van een evenredige stijging van score- en cijferpunten die onafhankelijk is van de normering.
Hierbij wordt onder de score verstaan: de zuivere score, dus uitsluitend de punten die aan de kandidaat zijn toegekend voor goede antwoordelementen.
Er zal derhalve geen sprake meer zijn van scorepunten-vooraf en/of scorepunten-bijtelling (in geval van cesuuraanpassing).

Het normeringsvoorschrift
Het normeringsvoorschrift bestaat uit twee onderdelen:
    – de hoofdrelatie: de formule die, voor de overgrote meerderheid der kandidaten, het berekeningsvoorschrift geeft voor het omzetten van score naar cijfer;
    – vier grensrelaties: vier formules die (bij andere N-termen dan 1,0) voorkomen dat kandidaten met zeer lage of zeer hoge scores een cijfer zouden krijgen dat in strijd is met bovengenoemde vier uitgangspunten.

De hoofdrelatie
De hoofdrelatie geeft aldus het examencijfer als functie van de score:
C = 9,0 * (S/L) + N .................... (1)
waarin:
C = het cijfer voor het centraal examen.
S = de score, dat wil zeggen de zuivere aan de kandidaat toegekende score.
L = de lengte van de scoreschaal, zoals vastgelegd in het correctievoorschrift;
N = de normeringsterm, liggend tussen de waarden: N = 0,0 en N = 2,0, vast te stellen door het College voor Toetsen en Examens middels een normeringsbeslissing.
Zijn zowel L als N bekend, dan leidt invullen van de score S direct tot het examencijfer C.

Voorbeeld:
Stel de lengte van de scoreschaal is L = 90 punten;
dan gaat formule (1) over in:
C = 9,0 * (S/90) + N.
Voordat hiermee uit score S examencijfer C kan worden berekend, moet het College voor Toetsen en Examens eerst een waarde voor normeringsterm N hebben vastgesteld.
Stel dat wordt: N = 1,0; dan krijgt formule (1) zijn definitieve vorm:
C = 9,0 * (S/90) + 1,0.

Deze is gevisualiseerd in figuur 1:

De grensrelaties
Deze zijn nodig om de boven gegeven vier uitgangspunten óók te kunnen eerbiedigen als de normeringsterm N groter of kleiner is dan 1,0.

Voorbeeld:
Bij een waarde voor de normeringsterm van N = 1,3, zouden de drie kandidaten met scores 0%, 50% en 100% op grond van de hoofdrelatie resp. de cijfers 1,3, 5,8 en 10,3 krijgen;
daarvan is echter het eerste cijfer guller dan de bedoeling en is het derde cijfer hoger dan het toegestane maximum.
Iets dergelijks treedt op bij een normeringsterm lager dan 1,0, bijvoorbeeld: N = 0,7. Genoemde drie kandidaten zouden in dat geval de examencijfers 0,7, 5,2 en 9,7 krijgen, waarvan het eerste cijfer uitkomt onder het toegestane minimum en het derde cijfer lager is dan de verdiende 10,0!
Deze problematiek is in beeld gebracht in figuur 2:

Deze ‘bijzonderheden’ worden verholpen door middel van een systeem van zogeheten grensrelaties.
Het principe van grensrelaties is gevisualiseerd in figuur 3. Bij voorbaat zullen alle score-cijfercombinaties liggen binnen het gebied dat begrensd wordt door de vier lijnstukken in deze figuur.

Samen vormen de vier lijnstukken 2a, 2b, 3a en 3b een ‘venster’ waarbinnen alle toegestane score-cijfercombinaties moeten liggen. Dreigt bij toepassing van de hoofdrelatie – formule (1) – een score-cijfercombinatie buiten deze grenzen te vallen, dan moet voor de desbetreffende score dat cijfer vervangen worden door het cijfer berekend met de corresponderende grensrelatie. Wat informeler gezegd: score-cijfercombinaties die buiten het ‘venster’ dreigen te vallen, komen op het ‘kozijn’ terecht.
De grensrelaties worden gevormd door de volgende vier formules:
C = 1,0 + S* (9/L)*2 .................... (2a)
C = 10,0 – (L-S)* (9/L) * 0,5 .................... (2b)
C = 1,0 + S* (9/L)* 0,5 .................... (3a)
C = 10,0 – (L-S)*(9/L)*2 .................... (3b)

Bij N > 1,0 geldt voor de laagste scores de formule (2a) en voor de hoogste scores de formule (2b).

In figuur 4 is dit gevisualiseerd.

Bij N < 1,0 geldt voor de laagste scores de formule (3a) en voor de hoogste scores de formule (3b).
In figuur 5 is dit gevisualiseerd.

Bij een waarde voor de normeringsterm van N = 1,0 treedt het systeem van grensrelaties niet in werking 
en resulteert een score-cijfertransformatie die grafisch wordt gerepresenteerd door de rechte lijn van Fig.1, 
de lijn die in Fig. 4 is gelabeld met: ‘N=1,0’.
Bij alle andere waarden van N zijn de grensrelaties wel van belang. 
In figuur 6 zijn als voorbeelden de twee uiterste gevallen in beeld gebracht, 
die resp. corresponderen met de normeringsbeslissingen N = 2,0 en N = 0,0. 
Deze leveren als score-cijfertransformaties de twee dubbel-geknikte lijnen op (gelabeld met ‘N=2,0’ en ‘N=0,0’).


"""
def calc_grade_from_score(score_int, scalelength_int , nterm_str , cesuur_int, is_ete_exam ):
    # from AWP Scores.CalcCijferTextFromScore PR2022-04-19
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- calc_grade_from_score -----')

    grade = None
    err_txt = None

    if not scalelength_int:
        err_txt = _('Scale length is not entered.')

    elif scalelength_int <= 0:
        caption = _('Maximum score') if is_ete_exam else _('Scale length')
        err_txt = _('%(cpt)s must be a whole number greater dan zero.') % {'cpt': caption}

    elif score_int < 0:
        # score can be zero
        err_txt = _('%(cpt)s must be a whole number greater than or equal to zero.') % {'cpt': _('The score')}

    elif score_int > scalelength_int:
        caption = _('Maximum score') if is_ete_exam else _('Scale length')
        err_txt = _('%(cpt)s must be fewer than or equal to %(val)s.') % {'cpt': caption, 'val': str(scalelength_int)}

    else:
        if is_ete_exam:
            caption = _('The cesuur')
            if cesuur_int <= 0:
                err_txt = _('%(cpt)s must be a whole number greater than zero.') % {'cpt': caption}
            elif cesuur_int >= scalelength_int:
                caption = _('The cesuur')
                err_txt = _('%(cpt)s must be fewer than or equal to %(val)s.') % {'cpt': caption, 'val': str(scalelength_int)}
            else:
                grade = calc_grade_from_score_ete(score_int, scalelength_int, cesuur_int)
        else:
            if not nterm_str:
                err_txt = _('Nterm is not entered.')
            else:
    # - replace comma in nterm by dot, convert to decimal
                nterm_dot_nz = nterm_str.replace(',', '.')
                nterm_decimal = Decimal(nterm_dot_nz)
                if logging_on:
                    logger.debug('... nterm_decimal: ' + str(nterm_decimal) + ' ' + str(type(nterm_decimal)))

            #PR2019-06-29 Radulpus is n_term > 2 : Uitgeschaked: If crcNorm < 0 Or crcNorm > 2 Then

                """
                a.compare(b) =  0  if a = b
                a.compare(b) =  1  if a > b
                a.compare(b) = -1  if a < b
                """
                compare_pece = nterm_decimal.compare(Decimal("0"))
                if compare_pece <= 0:
                    err_txt = _('N-term must be a number greater than zero.')
                else:
                    grade = calc_grade_from_score_duo(score_int, scalelength_int, nterm_str)
    return grade, err_txt


def calc_grade_from_score_wrap(department, si_dict, row):
    # - calc ce_grade from score
    # only when weight_ce > 0, not no_centralexam, ep not exemption, (was: not secret_exam)
    # when exemption (was: or secret_exam) the ce_grade is entered, not calculated

    # note: scores of secret_exam are also entered, not grades

#++++++++ this is the one that works +++++++++++++++++++++ PR2022-05-29

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug('----- calc_grade_from_score_wrap -----')
        logger.debug('     sjb_code: ' + si_dict.get('subj_code', '-'))
        logger.debug('     si_dict:  ' + str(si_dict))
        logger.debug('     row:      ' + str(row))

    ce_grade = None

# - ce_grade = None when no_centralexam or weight_ce = 0

    has_centralexam = department and not department.examyear.no_centralexam and si_dict.get('weight_ce')
    if has_centralexam:
        examperiod = row.get('examperiod')
        if logging_on:
            logger.debug('     examperiod:     ' + str(examperiod) + ' ' + str(type(examperiod)))

# - ce_grade is an entered value when is_secret_exam or exemption
        #PR2022-06-19 scores of secret_exam are also entered, not grades
        # was:  is_secret_exam = row.get('secret_exam', False)
        #       if is_secret_exam or examperiod == c.EXAMPERIOD_EXEMPTION:
        if examperiod == c.EXAMPERIOD_EXEMPTION:
            ce_grade = row.get('cegrade')
            if logging_on:
                logger.debug('     examperiod ce_grade: ' + str(ce_grade) + ' ' + str(type(ce_grade)))
        else:

# - ce_grade is None when cescore is not published
    # WARNING: this one blocks cegrade when score is not published, may be too strict
            cescore_is_published = True if row.get('ce_published_id') else False
            if logging_on:
                logger.debug('     cescore_is_published: ' + str(cescore_is_published) + ' ' + str(type(cescore_is_published)))

    # TODO enabled cescore_is_published
            # if cescore_is_published:
            if True:
# - calculate ce_grade from ce_score
                scalelength = row.get('scalelength')
                if logging_on:
                    logger.debug('     scalelength: ' + str(scalelength) + ' ' + str(type(scalelength)))

                if scalelength:
                    is_ete_exam = row.get('ete_exam', False)
                    if logging_on:
                        logger.debug('     is_ete_exam: ' + str(is_ete_exam) + ' ' + str(type(is_ete_exam)))

                    if is_ete_exam:
                        cesuur = row.get('cesuur')
                        exam_is_published = True if row.get('published_id') else False
                        if logging_on:
                            logger.debug('     exam_is_published: ' + str(exam_is_published) + ' ' + str(type(exam_is_published)))

    # - ce_grade is None when exam is not published
                        if exam_is_published and cesuur:
                            ce_score = row.get('cescore')
                            score_int = int(ce_score) if ce_score is not None else None
                            scalelength_int = int(scalelength)
                            cesuur_int = int(cesuur)
                            ce_grade = calc_grade_from_score_ete(score_int, scalelength_int, cesuur_int)

                            if logging_on:
                                logger.debug('     score_int: ' + str(score_int) + ' ' + str(type(score_int)))
                                logger.debug('     scalelength_int: ' + str(scalelength_int) + ' ' + str(type(scalelength_int)))
                                logger.debug('     cesuur_int: ' + str(cesuur_int) + ' ' + str(type(cesuur_int)))
                                logger.debug('     ce_grade: ' + str(ce_grade) + ' ' + str(type(ce_grade)))

                    else:
                        nterm_str = row.get('nterm')
                        if logging_on:
                            logger.debug('     nterm_str: ' + str(nterm_str) + ' ' + str(type(nterm_str)))

    # - DUO exams don't have to be published
                        if nterm_str:
                            ce_score = row.get('cescore')
                            score_int = int(ce_score) if ce_score is not None else None
                            scalelength_int = int(scalelength)

                            ce_grade = calc_grade_from_score_duo(score_int, scalelength_int, nterm_str)

                            if logging_on:
                                logger.debug('     score_int: ' + str(score_int) + ' ' + str(type(score_int)))
                                logger.debug('     scalelength_int: ' + str(scalelength_int) + ' ' + str(type(scalelength_int)))

    if logging_on:
        logger.debug(' >>> ce_grade: ' + str(ce_grade) + ' ' + str(type(ce_grade)))
    return ce_grade
# - end of calc_grade_from_score_wrap


def calc_grade_from_score_ete(score_int, scalelength_int, cesuur_int):

    #++++++++ this is the one that works +++++++++++++++++++++ PR2022-05-29

    logging_on = False  # s.LOGGING_ON
    """
    'PR2019-05-27 mail from Angela.Verschoor@cito.nl>
    ' Geachte heer Meijs,
    ' Mijn excuses dat ik u niet op de hoogte heb gebracht van de iets veranderde methodiek in het bepalen van de omzettingstabellen.
    ' Werd er tot voorheen uitgegaan bij de lineaire omzetting met knik van het feit dat - bijvoorbeeld in het geval van Bouw PBL -
    ' een score 55 een 5,5 zou geven en een score van 54 een 5,4 wordt nu als uitgangspunt genomen dat 54,5 punten een 5,45 oplevert.
    ' Tussen 0 en 54 punten wordt het cijfer dan 1 + score * 4,45 / 54,5.
    ' Tussen 55 punten en de maximum score van 92 wordt het cijfer 10 - (92 - score) * 4,55 / (92 - 54,5).
    ' Vervolgens worden de cijfers dan desgewenst op het juiste aantal decimalen afgerond, in het geval van de examens op 1 decimaal.
    ' Ik hoop u hiermee voldoende duidelijkheid te hebben gegeven. Vanaf woensdagochtend ben ik op kantore bij ETE.
    ' Met vriendelijke groet,
    ' Angela Verschoor

    If intLschaal > 0 Then
        If crcCesuur > 0 And crcCesuur < intLschaal Then
            If intScore >= 0 And intScore <= intLschaal Then
            '1. bereken Laagtse functie, van score 0 tot L/2
                If intScore < crcCesuur Then
                    crcCijfer = 1 + intScore * 4.45 / (crcCesuur - 0.5)
                Else
            '2. Bereken Hoogste functie, van score L/2 tot score L
                    crcCijfer = 10 - (intLschaal - intScore) * 4.55 / (intLschaal - (crcCesuur - 0.5))
                End If
            '4. afronden op 1 cijfer achter de komma
                crcCijfer = Int(0.5 + 10 * crcCijfer) / 10
            End If 'If intScore >= 0 And intScore <= intLschaal
        End If 'If crcCesuur > 0 And crcCesuur < intLschaal
    End If 'If intLschaal > 0
    """

    if logging_on:
        logger.debug(' ----- calc_grade_from_score_ete -----')
        logger.debug('     score_int:       ' + str(score_int) + ' ' + str(type(cesuur_int)))
        logger.debug('     scalelength_int: ' + str(scalelength_int) + ' ' + str(type(cesuur_int)))
        logger.debug('     cesuur_int:      ' + str(cesuur_int) + ' ' + str(type(cesuur_int)))

    grade_str = None

    # PR2022-05-19 debug: cannot cal Decimal from None. Add if not None
    if score_int is not None and scalelength_int is not None and cesuur_int is not None:
        score_dec = Decimal(score_int)
        scalelength_dec = Decimal(scalelength_int)
        cesuur_dec = Decimal(cesuur_int)

        dec_0_5 = Decimal('0.5')
        dec_1 = Decimal('1')
        dec_4_45 = Decimal('4.45')
        dec_4_55 = Decimal('4.55')
        dec_10 = Decimal('10')

    # - bereken Laagtse functie, van score 0 tot cesuur_int
        if score_int < cesuur_int:
            #  crcCijfer =  1 + intScore  *     4.45 / (crcCesuur - 0.5)
            grade_dec = dec_1 + score_dec * dec_4_45 / (cesuur_dec - dec_0_5)
        else:
            if logging_on:
                logger.debug(' ----- calc_grade_from_score_ete -----')
                logger.debug('     cesuur_dec:       ' + str(cesuur_dec) + ' ' + str(type(cesuur_dec)))
                logger.debug('     scalelength_dec:  ' + str(scalelength_dec) + ' ' + str(type(scalelength_dec)))
                logger.debug('     dec_10:           ' + str(dec_10) + ' ' + str(type(dec_10)))
                logger.debug('     dec_4_55:         ' + str(dec_4_55) + ' ' + str(type(dec_4_55)))
                logger.debug('     dec_0_5:         ' + str(dec_0_5) + ' ' + str(type(dec_0_5)))
    #' - Bereken Hoogste functie, van score cesuur_int tot score L
            # crcCijfer =   10 - (intLschaal - intScore) * 4.55           / (intLschaal - (crcCesuur - 0.5))
            grade_dec = dec_10 - (scalelength_dec - score_dec) * dec_4_55 / (scalelength_dec - (cesuur_dec - dec_0_5) )

            if logging_on:
                logger.debug('     grade_dec:       ' + str(grade_dec) + ' ' + str(type(grade_dec)))

    #' - afronden op 1 cijfer achter de komma
        grade_str = str(grade_calc.round_decimal(grade_dec, dec_1))

    if logging_on:
        logger.debug('   > grade_str:       ' + str(grade_str))

    return grade_str
# - end of calc_grade_from_score_ete


def calc_grade_from_score_duo(score_int, scalelength_int, nterm_str):
    #++++++++ this is the one that works +++++++++++++++++++++ PR2022-05-29

    logging_on = False  # s.LOGGING_ON

    if logging_on:
        logger.debug(' ----- calc_grade_from_score_duo -----')
        logger.debug('     score_int:       ' + str(score_int))
        logger.debug('     scalelength_int: ' + str(scalelength_int))
        logger.debug('     nterm_str:      ' + str(nterm_str))

    grade_str = None

    # PR2022-05-24 error conversion from NoneType to Decimal is not supported.
    # Add not None clause. score_int can be zero, scalelength_int cannot be zero
    if score_int is not None and scalelength_int and nterm_str:
    # - replace comma in nterm by dot, convert to decimal
        nterm_dot_nz = nterm_str.strip().replace(',', '.')
        if logging_on:
            logger.debug('     nterm_dot_nz: ' + str(nterm_dot_nz) + ' ' + str(type(nterm_dot_nz)))

        # test nterm_dot_nz is number, to prevent error 'decimal.ConversionSyntax'
        try:
            # remove first dot to see if rest is numeric (multiple dots must give error)
            nterm_nodots = nterm_dot_nz.replace('.', '', 1)  # 1 means: replace only 1 occurency
            nterm_test = int(nterm_nodots)
            if logging_on:
                logger.debug('     nterm_nodots: ' + str(nterm_nodots) + ' ' + str(type(nterm_nodots)))
                logger.debug('     nterm_test: ' + str(nterm_test) + ' ' + str(type(nterm_test)))
        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))
        else:
            if logging_on:
                logger.debug('     nterm_dot_nz: ' + str(nterm_dot_nz) + ' ' + str(type(nterm_dot_nz)))
            nterm_decimal = Decimal(nterm_dot_nz)
            if logging_on:
                logger.debug('     nterm_decimal: ' + str(nterm_decimal) + ' ' + str(type(nterm_decimal)))
            # note: the Decimal function accept number as argument
            score_dec = Decimal(score_int)
            scalelength_dec = Decimal(scalelength_int)

            if logging_on:
                logger.debug('     score_dec:       ' + str(score_dec) + ' ' + str(type(score_dec)))
                logger.debug('     scalelength_dec:       ' + str(scalelength_dec) + ' ' + str(type(scalelength_dec)))

            dec_half = Decimal('0.5')
            dec_1 = Decimal('1')
            dec_2 = Decimal('2')
            dec_9 = Decimal('9')
            dec_10 = Decimal('10')

        # De hoofdrelatie geeft aldus het examencijfer als functie van de score:
        #     'C = 9,0 * (S/L) + N .......................................... (1)
            grade_dec = dec_9 * (score_dec / scalelength_dec) + nterm_decimal

        # De grensrelaties worden gevormd door de volgende vier formules:

            """
            a.compare(b) =  0  if a = b
            a.compare(b) =  1  if a > b
            a.compare(b) = -1  if a < b
            """
            nterm_compare = nterm_decimal.compare(dec_1)
            if nterm_compare > 0:
        # bij N > 1,0 geldt voor de laagste scores de formule:
        #     'C = 1,0 + S * (9/L) * 2 ......................................... (2a)
                grade_max_low = dec_1 + score_dec * (dec_9 / scalelength_dec) * dec_2

                grade_gt_maxlow = (grade_dec.compare(grade_max_low) > 0)
                if grade_gt_maxlow:
                    grade_dec = grade_max_low

        # En voor de hoogste scores
        #     'C = 10,0 – (L-S) * 9/L) * 0,5................................................ (2b)
                grade_max_high = dec_10 - (scalelength_dec - score_dec) * (dec_9 / scalelength_dec) * dec_half

                grade_gt_maxhigh = (grade_dec.compare(grade_max_high) > 0)
                if grade_gt_maxhigh:
                    grade_dec = grade_max_high

            elif nterm_compare < 0:
        # bij N < 1,0 geldt voor de laagste scores de formule:
        #     'C = 1,0 + S * (9/L)* 0,5 ......................................... (3a)
                grade_min_low = dec_1 + score_dec * (dec_9 / scalelength_dec) * dec_half

                grade_lt_minlow = (grade_dec.compare(grade_min_low) < 0)
                if grade_lt_minlow:
                    grade_dec = grade_min_low

        # en voor de hoogste scores
        #    'C = 10,0 – (L-S)*(9/L)*2.................................................. (3b)
                grade_min_high = dec_10 - (scalelength_dec - score_dec) * (dec_9 / scalelength_dec) * dec_2

                grade_lt_minhigh = (grade_dec.compare(grade_min_high) < 0)
                if grade_lt_minhigh:
                    grade_dec = grade_min_high

        # afronden op 1 cijfer achter de komma 'NB: CITO norm rondt af op 1 decimaal
            grade_str = str(grade_calc.round_decimal(grade_dec, 1))

    if logging_on:
        logger.debug('     grade_str:       ' + str(grade_str) + ' ' + str(type(grade_str)))
    return grade_str
# - end of calc_grade_from_score_duo


def create_gradelist_for_score_calc(exam_pk):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' --- create_gradelist_for_score_calc --- ')
        logger.debug('    exam_pk: ' + str(exam_pk))

    # create list of grades with this exam, so cegrade can be calculated

    # IMPORTANT: pescore contains ce_exam_score, dont use this one to calc grade, becasue it is not submitted yet
    # instead use cescore, this one contains submitted score.

    gradelist_for_score_calc = []
    if exam_pk:
        try:
            sql_keys = {'exam_pk': exam_pk}
            sql_list = [
                "SELECT grd.id, grd.segrade, grd.srgrade, grd.pescore, grd.cescore, studsubj.schemeitem_id, grd.examperiod,",
                "exam.scalelength, exam.cesuur, exam.nterm, exam.ete_exam, exam.published_id",
                "FROM students_grade AS grd",
                "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",

                "INNER JOIN subjects_exam AS exam ON (exam.id = grd.ce_exam_id)",
                "WHERE grd.ce_exam_id = %(exam_pk)s::INT",
                "AND grd.examperiod = exam.examperiod",
                # skip secret exam
                "AND NOT exam.secret_exam",
                # both exam and grd.ce_exam must be published to calc grade
                # TODO URGENT ADD BACK "AND grd.ce_exam_published_id IS NOT NULL",
                # DUO exams are not published
                "AND (exam.published_id IS NOT NULL OR NOT exam.ete_exam)"
            ]
            sql = ' '.join(sql_list)
            if logging_on:
                logger.debug('sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql, sql_keys)
                rows = af.dictfetchall(cursor)
            if rows:
                for row in rows:
                    gradelist_for_score_calc.append(row)

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    return gradelist_for_score_calc
# - end of create_gradelist_for_score_calc


def batch_update_cegrade(grade_rows_tobe_updated, request):
    #PR2022-05-07
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- batch_update_cegrade -----')
        logger.debug('     grade_rows_tobe_updated:    ' + str(grade_rows_tobe_updated))
        """
            grade_rows_tobe_updated:    [
            {'id': 22539, 'pescore': 56, 'cegrade': '5.9'}, 
            {'id': 22569, 'pescore': 57, 'cegrade': '6.0'}, 
            {'id': 22459, 'pescore': 43, 'cegrade': '4.7'}]
        """
    updated_cegrade_count = 0
    updated_cegrade_list = []
    if grade_rows_tobe_updated and request.user:

        try:
            # do not change modby, it will give user of admin
            # to do: write as modifiedat = %(modat)s::TIMESTAMP, dont know how to do it yet
            # modifiedat_str = str(timezone.now())
            # sql_keys = {'modby_id': request.user.pk}

            sql_list = ["CREATE TEMP TABLE gr_update (grade_id, cegrade) AS",
                        "VALUES (0::INT, 0::INT)"]

            for row in grade_rows_tobe_updated:
                grade_id = str(row.get('id'))

                cegrade = row.get('cegrade')
                if not cegrade:
                    cegrade = 'NULL'

                sql_list.append(''.join((", (", grade_id, ", ", cegrade, ")")))

            sql_list.extend((
                "; UPDATE students_grade AS gr",
                "SET cegrade = gr_update.cegrade",
                #"modifiedby_id = %(modby_id)s::INT, modifiedat = '", modifiedat_str, "'",

                "FROM gr_update",
                "WHERE gr_update.grade_id = gr.id",
                "RETURNING gr.id;"
                ))

            sql = ' '.join(sql_list)

            if logging_on:
                logger.debug('     sql:    ' + str(sql))

            if logging_on:
                logger.debug('sql: ' + str(sql))

            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
                if rows:
                    for row in rows:
                        updated_cegrade_list.append(row[0])

            updated_cegrade_count = len(rows)

            if logging_on:
                logger.debug('     rows:    ' + str(rows))

        except Exception as e:
            logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug('     updated_cegrade_count:    ' + str(updated_cegrade_count))

    return updated_cegrade_count, updated_cegrade_list
# - end of batch_approve_grade_rows


def get_nterm_number_from_input_str(input_str):
    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- get_nterm_number_from_input_str -----')
        logger.debug('     input_str: >' + str(input_str) + '< ' + str(type(input_str)))

    output_str = None
    err_list = []

# - remove spaces before and after input_value
    imput_trim = input_str.strip() if input_str else ''

# - exit if imput_trim has no value, without msg_err
    if imput_trim:
        has_error = False

# check if imput_trim is integer
        if not ',' in imput_trim and not '.' in imput_trim:
            if len(imput_trim) > 2:
                has_error = True
            else:
                input_int = 0
                try:
                    input_int = int(imput_trim)
                    if logging_on:
                        logger.debug('     input_int: >' + str(input_int) + '< ' + str(type(input_int)))
                except:
                    has_error = True
                else:
                    if input_int <= 0 or input_int > 99:
                        has_error = True
                    else:
                        if input_int < 10:
                            output_str = str(input_int) + ',0'
                        else:
                            output_str = ''.join((str(input_int)[:1], '.', str(input_int)[1:]))
                            if logging_on:
                                logger.debug('     input_int: >' + str(input_int) + '< ' + str(type(input_int)))
        else:
# - remove first comma or dot
            input_nodots = imput_trim.replace(',', '', 1).replace('.', '', 1)
            #input_nodots = input_nodots.replace('.', '', 1)
            if logging_on:
                logger.debug('     input_nodots: >' + str(input_nodots) + '< ' + str(type(input_nodots)))

# only accept input with 3 characters (with dots removed)
            # values can be from '01' thru '99'
            if len(input_nodots) == 2:
        # check if input without dots is integer
                input_int = 0
                try:
                    input_int = int(input_nodots)
                except:
                    has_error = True

        # check if input > 0 and < 100
                else:
                    if input_int <= 0 or input_int > 99:
                        has_error = True
                    else:
                        if input_int <= 9:
                            output_str ='0.' + str(input_int)
                        else:
                            # if input_int is between '10' en '99': put dot in the middle
                            output_str = ''.join((str(input_int)[0:1], '.', str(input_int)[1:]))

                        if logging_on:
                            logger.debug('     output_str: >' + str(output_str) + '< ' + str(type(output_str)))
            else:
                has_error = True

        if has_error:
            err_list.append(str(_("N-term '%(val)s' is not allowed.") % {'val': imput_trim}))
            err_list.append(''.join((str(_('The N-term must be a number between 1 and 10')), ',')))
            err_list.append(str(_('with one digit after the decimal point.')))

    if logging_on:
        logger.debug(' >>> output_str: ' + str(output_str))
        if err_list:
            logger.debug(' >>> err_list: ' + str(err_list))

    return output_str, err_list
# - end of get_nterm_number_from_input_str


def batch_update_finalgrade(department_instance, exam_instance=None, grade_pk_list=None, student_pk_list=None):
    #PR2022-05-25 PR2022-06-03
    # called by calc_cegrade_from_exam_score and CalcResultsView

#++++++++ this is the one that works +++++++++++++++++++++ PR2022-05-29
    # function calculates cegrade from score, or gets cegrade from row when exemption (was: or secret_exam)
    # - calculates sesrgrade, pecegrade and final grade
    # - and puts it in returnvalue updated_cegrade_list

    # note: scores of secret_exam are also entered, not grades

    logging_on = False  # s.LOGGING_ON
    if logging_on:
        logger.debug(' ----- batch_update_finalgrade -----')
        logger.debug('     exam_instance:    ' + str(exam_instance))
        logger.debug('     grade_pk_list:    ' + str(grade_pk_list))
        logger.debug('     student_pk_list:    ' + str(student_pk_list))

    updated_cegrade_count = 0
    updated_cegrade_list = []
    updated_student_pk_list = []

    if department_instance:

# - get rows of all grades that must be calculated
        # retrieve id and fields necessary to calculate final grade
        sql_keys = {'depbase_pk': department_instance.base.pk}
        sql_list = [
            "SELECT grd.id, grd.examperiod, grd.segrade, grd.srgrade, grd.pescore, grd.cescore, grd.pegrade, grd.cegrade,",
            "grd.ce_published_id,",
            "studsubj.student_id, studsubj.schemeitem_id, studsubj.has_sr, studsubj.has_exemption, studsubj.exemption_year,",
            "exam.ete_exam, exam.secret_exam, exam.scalelength, exam.cesuur, exam.nterm, exam.published_id",

            "FROM students_grade AS grd",
            "LEFT JOIN subjects_exam AS exam ON (exam.id = grd.ce_exam_id)",

            "INNER JOIN students_studentsubject AS studsubj ON (studsubj.id = grd.studentsubject_id)",
            "INNER JOIN students_student AS stud ON (stud.id = studsubj.student_id)",
            "INNER JOIN schools_department AS dep ON (dep.id = stud.department_id)",

            "WHERE dep.base_id = %(depbase_pk)s::INT",
            "AND NOT stud.deleted AND NOT stud.tobedeleted ",
            "AND NOT studsubj.deleted AND NOT studsubj.tobedeleted ",
            "AND NOT grd.deleted AND NOT grd.tobedeleted"
        ]

        if student_pk_list:
            sql_keys['stud_pk_arr'] = student_pk_list
            sql_list.append("AND stud.id IN (SELECT UNNEST( %(stud_pk_arr)s::INT[]))")

        elif grade_pk_list:
            sql_keys['grd_pk_arr'] = grade_pk_list
            sql_list.append("AND grd.id IN (SELECT UNNEST( %(grd_pk_arr)s::INT[]))")

        elif exam_instance:
            sql_keys['exam_pk'] = exam_instance.pk
            sql_list.append("AND grd.ce_exam_id = %(exam_pk)s::INT")

        sql = ' '.join(sql_list)

        if logging_on:
            logger.debug('     sql:    ' + str(sql))

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            rows = af.dictfetchall(cursor)

        if logging_on and False:
            for cq in connection.queries:
                if 'SELECT "grd' in cq:
                    logger.debug('query: ' + str(cq))
            for row in rows:
                logger.debug('     row:    ' + str(row))

        if rows:

# - get_schemeitems_dict - of CUR and SXM - therefore filter by examyear.code intsead of examyear.pk
            schemeitems_dict = calc_result.get_schemeitems_dict(department_instance.examyear, department_instance)

            try:
                # do not change modby, it will give user of admin
                # to do: write as modifiedat = %(modat)s::TIMESTAMP, dont know how to do it yet
                # modifiedat_str = str(timezone.now())
                # sql_keys = {'modby_id': request.user.pk}

                sql_list = ["CREATE TEMP TABLE gr_update (grade_id, sesrgrade, cegrade, pecegrade, finalgrade) AS",
                            "VALUES (0::INT, '-'::TEXT, '-'::TEXT, '-'::TEXT, '-'::TEXT)"]
                for row in rows:
                    if logging_on:
                        logger.debug('     row:    ' + str(row))

                    grade_id = str(row.get('id'))

        # updated_student_pk_list is used to calculate passedfailed of students with updates grades
                    student_id = row.get('student_id')
                    if student_id not in updated_student_pk_list:
                        updated_student_pk_list.append(student_id)

                    schemeitem_id = row.get('schemeitem_id') or 0
                    si_dict = schemeitems_dict.get(schemeitem_id)
                    if si_dict:

        # - calc ce_grade from score, or get from row when exemption (was: or secret_exam)
                        ce_grade = calc_grade_from_score_wrap(department_instance, si_dict, row)

        # - calc sesrgrade pecegrade and final grade
                        sesr_grade, pece_grade, finalgrade, delete_cegrade = \
                            calc_final.calc_sesr_pece_final_grade(
                                si_dict=si_dict,
                                examperiod=row.get('examperiod'),
                                has_sr=row.get('has_sr', False),
                                exemption_year=row.get('exemption_year'),
                                se_grade=row.get('segrade'),
                                sr_grade=row.get('srgrade'),
                                pe_grade=row.get('pegrade'),
                                ce_grade=ce_grade
                            )
                        if logging_on:
                            logger.debug('     ce_grade:    ' + str(ce_grade))
                            logger.debug('     sesr_grade:    ' + str(sesr_grade))
                            logger.debug('     pece_grade:    ' + str(pece_grade))
                            logger.debug('     finalgrade:    ' + str(finalgrade))

                        ce_grade_str = "'" + str(ce_grade) + "'" if ce_grade is not None else 'NULL'
                        sesr_grade_str = "'" + str(sesr_grade) + "'" if sesr_grade is not None else 'NULL'
                        pece_grade_str = "'" + str(pece_grade) + "'" if pece_grade is not None else 'NULL'
                        finalgrade_str = "'" + str(finalgrade) + "'" if finalgrade is not None else 'NULL'

    # - put grades in TEMP TABLE gr_update
                        sql_list.append(''.join((", (", grade_id, ", ",
                                                        sesr_grade_str, ", ",
                                                        ce_grade_str, ", ",
                                                        pece_grade_str, ", ",
                                                        finalgrade_str, ")")))

                sql_list.extend((
                    "; UPDATE students_grade AS gr",
                    "SET sesrgrade = gr_update.sesrgrade, cegrade = gr_update.cegrade,",
                    "pecegrade = gr_update.pecegrade, finalgrade = gr_update.finalgrade",
                    #"modifiedby_id = %(modby_id)s::INT, modifiedat = '", modifiedat_str, "'",
                    "FROM gr_update",
                    "WHERE gr_update.grade_id = gr.id",
                    "RETURNING gr.id, gr.sesrgrade, gr.pecegrade, gr.finalgrade;"
                    ))

                sql = ' '.join(sql_list)
                if logging_on:
                    logger.debug('     sql:    ' + str(sql))

                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    rows = cursor.fetchall()

                if rows:
                    for row in rows:
                        updated_cegrade_list.append(row[0])
                        if logging_on:
                            logger.debug('  updated_cegrade_list row:    ' + str(row))
                updated_cegrade_count = len(rows)

            except Exception as e:
                logger.error(getattr(e, 'message', str(e)))

    if logging_on:
        logger.debug(' >>> updated_cegrade_count:    ' + str(updated_cegrade_count))
        logger.debug(' >>> updated_cegrade_list:    ' + str(updated_cegrade_list))

    return updated_cegrade_count, updated_cegrade_list, updated_student_pk_list
# end of batch_update_finalgrade

"""
Public Function CalcCijferFromScoreCITO(ByVal intScore As Integer, ByVal intLschaal As Integer, ByVal crcNterm As Currency) As Currency
On Error GoTo Err_CalcCijferFromScoreCITO 'PR2015-12-27 'PR2016-03-05 Validatie vindt plaats buiten deze functie
    Dim crcCijfer As Currency, crcMaxLaag As Currency, crcMinLaag As Currency, crcMaxHoog As Currency, crcMinHoog As Currency
    If intLschaal > 0 Then
        If crcNterm >= 0 Then ' PR2019-06-29And crcNterm <= 2 Then
            If intScore >= 0 And intScore <= intLschaal Then
                'De hoofdrelatie geeft aldus het examencijfer als functie van de score:
                    'C = 9,0 * (S/L) + N .......................................... (1)
                crcCijfer = 9 * (intScore / intLschaal) + crcNterm
                'De grensrelaties worden gevormd door de volgende vier formules:
                If crcNterm > 1 Then
                    'bij N > 1,0 geldt voor de laagste scores de formule:
                        'C = 1,0 + S* (9/L)*2 ......................................... (2a)
                    crcMaxLaag = 1 + intScore * (9 / intLschaal) * 2
                    If crcCijfer > crcMaxLaag Then
                        crcCijfer = crcMaxLaag
                    End If
                    'En voor de hoogste scores
                        'C =<10,0 – (L-S)* 9/L) * 0,5................................................ (2b)
                    crcMaxHoog = 10 - (intLschaal - intScore) * (9 / intLschaal) * 0.5
                    If crcCijfer > crcMaxHoog Then
                        crcCijfer = crcMaxHoog
                    End If
                ElseIf crcNterm < 1 Then
                    'bij N < 1,0 geldt voor de laagste scores de formule:
                        'C = 1,0 + S* (9/L)* 0,5 ......................................... (3a)
                    crcMinLaag = 1 + intScore * (9 / intLschaal) * 0.5
                    If crcCijfer < crcMinLaag Then crcCijfer = crcMinLaag
                    'en voor de hoogste scores
                        'C = 10,0 – (L-S)*(9/L)*2.................................................. (3b)
                    crcMinHoog = 10 - (intLschaal - intScore) * (9 / intLschaal) * 2
                    If crcCijfer < crcMinHoog Then crcCijfer = crcMinHoog
                End If
                'afronden op 1 cijfer achter de komma 'NB: CITO norm rondt af op 1 decimaal
                crcCijfer = Int(0.5 + 10 * crcCijfer) / 10
            End If 'If intScore >= 0 And intScore <= intLschaal
        End If 'If crcNterm >= 0 And crcNterm <= 2 Then
    End If 'If intLschaal > 0
    CalcCijferFromScoreCITO = crcCijfer
Exit_CalcCijferFromScoreCITO:
    Exit Function
Err_CalcCijferFromScoreCITO:
    ErrorLog conModuleName, "Err_CalcCijferFromScoreCITO", Err.Description
    Resume Exit_CalcCijferFromScoreCITO
End Function
"""