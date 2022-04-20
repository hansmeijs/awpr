# PR2022-04-19
from decimal import Decimal
#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import gettext_lazy as _

from awpr import constants as c
from awpr import settings as s

from grades import calculations as grade_calc
import logging
logger = logging.getLogger(__name__)


"""
'Regeling van het College voor Toetsen en Examens van 9 februari 2015, nummer CvTE-15.00618,
'houdende vaststelling van regels voor de omzetting van scores in cijfers bij centrale examens en de rekentoets in het voortgezet onderwijs
'(Regeling omzetting scores in cijfers centrale examens en rekentoets VO 2015)

'Uitgangspunten: Het systeem voor de omzetting van score naar cijfer is gebaseerd op de volgende vier uitgangspunten:
'    1. Elk gescoord punt draagt altijd bij tot een hoger examencijfer (afronding daargelaten);
'    2. Een score van 0% correspondeert altijd met examencijfer 1,0;
'    3. Een score van 100% correspondeert altijd met examencijfer 10,0;
'    4. Over een zo breed mogelijk centraal interval van de scoreschaal is er (afronding daargelaten) sprake van een evenredige stijging van score- en cijferpunten die onafhankelijk is van de normering.

'het normeringsvoorschrift
'Het normeringsvoorschrift bestaat uit twee onderdelen:
'    – de hoofdrelatie: de formule die, voor de overgrote meerderheid van de kandidaten, het berekeningsvoorschrift geeft voor het omzetten van score naar cijfer;
'    – vier grensrelaties: vier formules die (bij andere N-termen dan 1,0) voorkomen dat kandidaten met zeer lage of zeer hoge scores een cijfer zouden krijgen dat in strijd is met bovengenoemde vier uitgangspunten.

'de hoofdrelatie
'De hoofdrelatie geeft aldus het examencijfer als functie van de score:
'C = 9,0 * (S/L) + N .......................................... (1)
'waarin:
'C = het cijfer voor het centraal examen.
'S = de score, dat wil zeggen de zuivere aan de kandidaat toegekende score.
'L = de lengte van de scoreschaal, zoals vastgelegd in het correctievoorschrift;
'N = de normeringsterm, liggend tussen de waarden: N = 0,0 en N = 2,0, vast te stellen door het College voor Toetsen en Examens middels een normeringsbeslissing.
'Zijn zowel L als N bekend, dan leidt invullen van de score S direct tot het examencijfer C.

'De grensrelaties
'Deze zijn nodig om de boven gegeven vier uitgangspunten óók te kunnen eerbiedigen als de normeringsterm N groter of kleiner is dan 1,0.
'Voorbeeld:
'Bij een waarde voor de normeringsterm van N = 1,3, zouden de drie kandidaten met scores 0%, 50% en 100% op grond van de hoofdrelatie resp. de cijfers 1,3, 5,8 en 10,3 krijgen;
'daarvan is echter het eerste cijfer guller dan de bedoeling en is het derde cijfer hoger dan het toegestane maximum.
'Iets dergelijks treedt op bij een normeringsterm lager dan 1,0, bijvoorbeeld: N = 0,7. Genoemde drie kandidaten zouden in dat geval de examencijfers 0,7, 5,2 en 9,7 krijgen, waarvan het eerste cijfer uitkomt onder het toegestane minimum en het derde cijfer lager is dan de verdiende 10,0!
'Deze problematiek is in beeld gebracht in Fig.2:

'De grensrelaties worden gevormd door de volgende vier formules:
'bij N > 1,0 geldt voor de laagste scores de formule:
    'C =< 1,0 + S* (9/L)*2 ......................................... (2a)
'En voor de hoogste scores
    'C =<10,0 – (L-S)* 9/L) * 0,5................................................ (2b)
'bij N < 1,0 geldt voor de laagste scores de formule:
    'C >= 1,0 + S* (9/L)* 0,5 ......................................... (3a)
'en voor de hoogste scores
    'C >= 10,0 – (L-S)*(9/L)*2.................................................. (3b)
'Bij een waarde voor de normeringsterm van N = 1,0 treedt het systeem van grensrelaties niet in werking en resulteert een score-cijfertransformatie die grafisch wordt gerepresenteerd door de rechte lijn van Fig.1, de lijn die in Fig.4 is gelabeld met: "N=1,0".
'Bij alle andere waarden van N zijn de grensrelaties wel van belang. In Fig. 4 zijn als voorbeelden de twee uiterste gevallen in beeld gebracht, die resp. corresponderen met de normeringsbeslissingen N = 2,0 en N = 0,0 . Deze leveren als score-cijfertransformaties de twee dubbel-geknikte lijnen op (gelabeld met "N=2,0" en "N=0,0").


'Cito uitleg grensrelaties:
'De lijnen 1 en 2 starten vanuit het punt (0,1):
'(1) C = 1 + S * (9 / L) * 2     bij N > 1,0
'(2) C = 1 + S * (9 / L) * 0,5  'bij N < 1,0
'De lijnen 3 en 4 worden berekend vanaf het punt (L,10): voor elk scorepunt onder de maximumscore
'(dus L-S) worden cijferpunten in mindering gebracht (vandaar 10-…) volgens deze formules:
'(3) C = 10 – (L – S) * (9 / L) * 2    'bij N < 1,0
'(4) C = 10 – (L – S) * (9 / L) * 0,5   bij N > 1,0

"""
def calc_grade_from_score(score_int , scalelength_int , nterm_str , cesuur_int, is_ete_exam ):
    # from AWP Scores.CalcCijferTextFromScore PR2022-04-19
    logging_on = s.LOGGING_ON
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
        caption = str(caption).lower()
        err_txt = _('Score must be fewer than %(cpt)s.') % {'cpt': caption}

    else:
        if is_ete_exam:
            if cesuur_int <= 0:
                err_txt = _('%(cpt)s must be a whole number greater than zero.') % {'cpt': _('Cesuur')}
            elif cesuur_int >= scalelength_int:
                err_txt = _('Cesuur must be fewer than maximum score.')
            else:
                grade = calc_grade_from_score_ETE(score_int, scalelength_int, cesuur_int)
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
                    grade = calc_grade_from_score_CITO(score_int, scalelength_int, nterm_decimal)
    return grade, err_txt

def calc_grade_from_score_ETE(score_int, scalelength_int, cesuur_int):
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
    score_dec = Decimal(score_int)
    scalelength_dec = Decimal(scalelength_int)
    cesuur_dec = Decimal(cesuur_int)

    dec_0_5 = Decimal('0.5')
    dec_1 = Decimal('1')
    dec_4_45 = Decimal('4.45')
    dec_4_55 = Decimal('4.55')
    dec_9 = Decimal('9')
    dec_10 = Decimal('10')


# - bereken Laagtse functie, van score 0 tot L/2
    if score_int < cesuur_int:
        grade_dec = dec_1 + score_dec * dec_4_45 / (cesuur_dec - dec_0_5)
    else:

#' - Bereken Hoogste functie, van score L/2 tot score L
        grade_dec = dec_10 - (scalelength_dec - score_dec) * dec_4_55 / (scalelength_dec - (cesuur_dec - dec_0_5) )

#' - afronden op 1 cijfer achter de komma
    grade_str = str(grade_calc.round_decimal(grade_dec, dec_1))

    return grade_str


def calc_grade_from_score_CITO(score_int, scalelength_int, nterm_dec):
    """
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
    """

    score_dec = Decimal(score_int)
    scalelength_dec = Decimal(scalelength_int)

    dec_half = Decimal('0.5')
    dec_1 = Decimal('1')
    dec_2 = Decimal('2')
    dec_9 = Decimal('9')
    dec_10 = Decimal('10')

# De hoofdrelatie geeft aldus het examencijfer als functie van de score:
#     'C = 9,0 * (S/L) + N .......................................... (1)
    grade_dec = dec_9 * (score_dec / scalelength_dec) + nterm_dec

# De grensrelaties worden gevormd door de volgende vier formules:

    """
    a.compare(b) =  0  if a = b
    a.compare(b) =  1  if a > b
    a.compare(b) = -1  if a < b
    """
    nterm_compare = nterm_dec.compare(dec_1)
    if nterm_compare > 0:
# bij N > 1,0 geldt voor de laagste scores de formule:
#     'C = 1,0 + S * (9/L) * 2 ......................................... (2a)
        grade_max_low = dec_1 + score_dec * (dec_9 / scalelength_dec) * dec_2

        grade_gt_maxlow = (grade_dec.compare(grade_max_low) == 1)
        if grade_gt_maxlow:
            grade_dec = grade_max_low

# En voor de hoogste scores
#     'C = 10,0 – (L-S) * 9/L) * 0,5................................................ (2b)
        grade_max_high = dec_10 - (scalelength_dec - score_dec) * (dec_9 / scalelength_dec) * dec_half
        if grade_dec > grade_max_high:
            grade_dec = grade_max_high

    elif nterm_compare < 0:
# bij N < 1,0 geldt voor de laagste scores de formule:
#     'C = 1,0 + S* (9/L)* 0,5 ......................................... (3a)
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

    return grade_str

################################
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