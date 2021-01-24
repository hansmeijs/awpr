# PR2021-01-17
from decimal import Decimal
from django.utils.translation import ugettext_lazy as _
from awpr import constants as c
from awpr import calculations as calc
from awpr import locale as l

import logging
logger = logging.getLogger(__name__)

def calc_final_grade(grade):
    studentsubject = grade.studentsubject
    schemeitem = studentsubject.schemeitem
    gradetype = schemeitem.gradetype
    finalgrade = None
    if gradetype == c.GRADETYPE_02_CHARACTER:
        if grade.examperiod == c.EXAMPERIOD_SECOND:
            finalgrade = calc_finalgrade_char_reex_corona(grade.segrade, grade.cegrade, schemeitem.weight_se)
        else:
            finalgrade = grade.segrade
    elif gradetype == c.GRADETYPE_01_NUMBER:
        se_number = get_number_from_inputgrade(grade.segrade)
        pe_number = get_number_from_inputgrade(grade.pegrade)
        ce_number = get_number_from_inputgrade(grade.cegrade)
        finalgrade = calc_finalgrade_number(se_number, pe_number, ce_number)

    setattr(grade, 'finalgrade', finalgrade)

# --- end of calc_final_grade


"""
#1. geef waarde aan booNoInputSE, onthoudt of input niet is ingevuld 'PR2019-03-25
        If strInputSE(Tv) = vbNullString And crcSEweging > 0 Then
            booNoInputSE(Tv) = True
        End If
    
    '2. zet SE-cijfer in Kv_SE_Ref. Eindcijfer is gelijk aan SE (TODO niet bij Corona!). Zet SE-cijfer in Kv_Eindcijfer_Ref.
        If Not booNoInputSE(Tv) Then
            kv_SE_Ref(Tv) = strInputSE(Tv)
    
        'PR2020-05-15 Corona: Herkansing mogelijk bij ovg vakken.
            If pblAfd.IsCorona Then
            '2. bereken PeCecijfer uit PE en CE of crcCEvrijst PR2019-01-24
                'geen crc bij ovg vakken
            '2. geef waarde aan booNoInputPeCe, onthoudt of input niet is ingevuld 'PR2019-03-06
               ' alleen bij herkansing
                booNoInputPeCe(Tv) = (Tv = conTv02 And strInputCE(Tv) = vbNullString)
    
            '3. zet herkansing cijfer in kv_CE_Ref en Kv_PeCe_Ref (formatted string)
                'laat blanco als een van de vereiste input cijfers niet is ingevuld PR2019-03-06
                'PR2020-05-12 Corona. kv_PeCe_Ref = 0 bij Corona, behalve bij TvVrst. Die berekent eincijfer op de normale manier
                If Tv = conTv02 And Not booNoInputPeCe(Tv) Then
                    kv_CE_Ref(Tv) = strInputCE(Tv)
                    kv_PeCe_Ref(Tv) = strInputCE(Tv)
                End If
    '-----------------------------------------------------------------------------
    'Bereken crcEindcijfer van Tv01 tm Tv 03 en TvVrst
    '-----------------------------------------------------------------------------
        '1. bereken crcEindcijfer per tijdvak, is 0 als een van de cijfers niet is ingevuld
                'niet bij ovg
        '2. zet eindcijfer per tijdvak in Kv_Eindcijfer_Ref.
                Call CalcEindcijfer_Ovg_Her_Corona(Tv, booNoInputSE(), booNoInputPeCe(), kv_SE_Ref(), kv_CE_Ref(), kv_Eindcijfer_Ref())
            Else 'If pblAfd.IsCorona Then
                kv_Eindcijfer_Ref(Tv) = strInputSE(Tv)
            
            End If ' If pblAfd.IsCorona
        End If ' If Not booNoInputSE(Tv)
"""


# --- end of calc_finalgrade_char


def calc_finalgrade_number(grade, studentsubject, schemeitem):
    final_grade = None
    return final_grade
# --- end of calc_finalgrade_number


def calc_finalgrade_char_reex_corona(se_grade, ce_grade, weight_se):
    #logger.debug(' ----- calc_finalgrade_char -----')
    # --- create rows of all students of this examyear / school PR2021-01-17
    # PR2020-05-15 Corona: Herkansing mogelijk bij ovg vakken. her-cijfer wordt in cegrade gezet
    # berekening:
    # - gebruik SE cijfer als herkansing lager is dan SE of gelijk aan SE
    # - bereken'gemiddelde' van se en ce als herkansing hoger is dan SE: v + g > g;  o + g > v (geen g !); o + v > v
    final_grade = None
    if weight_se:
        if se_grade and ce_grade and se_grade != ce_grade:
            if se_grade == 'g':
                # gebruik SE cijfer als herkansing lager is dan SE
                final_grade = 'g'
            elif se_grade == 'v':
                if ce_grade == 'g':
                    #gemiddeld eindcijfer v + g > g
                    final_grade = 'g'
                elif ce_grade == 'o':
                    #' gebruik SE cijfer als herkansing lager is dan SE
                    final_grade = 'v'
            elif se_grade == 'o':
                # gemiddeld eindcijfer o + g > v (geen g !!!)
                # gemiddeld eindcijfer o + v > v
                final_grade = 'v'
        else:
            final_grade = se_grade
    return final_grade


def calc_pece_number(examperiod_int, has_practex, ce_grade, pe_grade):  # PR2021-01-18
    # logger.debug(' ----- calc_finalgrade_char -----')


    # - bereken PeCecijfer uit PE en CE of crcCEvrijst PR2019-01-24
    # - PeCe=0 als CE=0 of als bij Vsi_HasPraktijkex PE=0
    # -  bij vrijstelling wordt geen PE ingevuld, daarom is pece_number gelijk aan ce_number
    #  - Corona: geen PE bij Corona: If pblAfd.IsCorona Then vsi_HasPraktijkex = False
    pece_number = None
    ce_number = get_number_from_inputgrade(ce_grade)
    if examperiod_int in (c.EXAMPERIOD_FIRST, c.EXAMPERIOD_SECOND, c.EXAMPERIOD_THIRD):
        # 'a. bij praktijkexamen: bereken PeCecijfer uit CE en PE cijfer
        if has_practex:
#         'i. zet PE string om in getal
            pe_number = get_number_from_inputgrade(pe_grade)
    #         'ii. bereken PeCecijfer

# '1. PEcijfer en CEcijfer moeten beide zijn ingevuld
            if ce_number and pe_number:
# '2. bereken gemiddeld PeCe-cijfer
                pece_number_not_rounded = (ce_number + pe_number) / 2
# '3. rond af op 1 cijfer achter de komma
                pece_number = calc.round_decimal(pece_number_not_rounded, 1)
        else:
    #     'b. bij geen Vsi_HasPraktijkex is PeCe(Tv)=0 gelijk aan crcCE(Tv)
            pece_number = ce_number
    #         End If
    elif examperiod_int == c.EXAMPERIOD_EXEMPTION:
    #     'c. bij vrijstelling wordt geen PE ingevuld, daarom is PeCe(Tv)=0 gelijk aan crcCEvrijst
             pece_number = ce_number


    return pece_number
# --- end of calc_pece_number


def get_score_from_inputscore(input_value, max_score):
    logger.debug(' ----- get_score_from_inputscore -----')
    logger.debug('input_value: ' + str(input_value) + ' ' + str(type(input_value)))
    # function converts input_value to whole number PR2021-01-18

# 1. reset output variables
    input_number, output_text, msg_err = 0, None, None
# 2. remove spaces before and after input_value
    imput_trim = input_value.strip() if input_value else ''
# - exit if imput_trim has no value, without msg_err
    if imput_trim:
        has_error = False
# - replace all comma's with dots
        input_with_dots = imput_trim.replace(',', '.')
# cast input_with_dots to decimal, exit if not numeric
        # '', ' ' and non-numeric give InvalidOperation error
        input_number = None
        try:
            input_number = Decimal(input_with_dots)
        except:
            has_error = True
        if not has_error:
# - get remainder of input_number
            # the remainder / modulus operator (%) returns the remainder after (integer) division.
            remainder = input_number % 1
            if remainder != 0:
                has_error = True
            elif max_score and input_number > max_score:
                has_error = True
        if has_error:
            input_number = None
            msg_err = str(_("Score '%(val)s' is not allowed.") % {'val': str(input_value)}  ) + "\n" + \
                    str(_("The score must be a whole number between 0 and %(max)s.") % {'max': max_score})

    return input_number, msg_err
# --- end of get_score_from_inputscore


def get_number_from_inputgrade(input_value):
    logger.debug(' ----- get_number_from_inputgrade -----')
    logger.debug('input_value: ' + str(input_value) + ' ' + str(type(input_value)))
    """
        Functie maakt getal van string 15 jan 07, 29 jan 12, 3 mei 13
        - string heeft formaat "5,6", "5.6", "56"  1 cijfer achter de komma, exit als Cijfer <= 0 of  > 100
        - zowel punt als komma zijn toegestaan als delimiter (delimiter wordt niet meer gebruikt in deze functie PR2016-03-04

        PR2019-03-28 strCaptionText toegevoegd voor Form_C_N_Normen
    """
# 1. reset output variables
    input_number, output_text, msg_err = 0, None, None
# 2. remove spaces before and after input_value
    imput_trim = input_value.strip() if input_value else ''
    logger.debug('imput_trim: ' + str(imput_trim) + ' ' + str(type(imput_trim)))
# - exit if imput_trim has no value, without msg_err
    if imput_trim:
        msg_index = None
# - vervang alle komma's door punten
        input_with_dots = imput_trim.replace(',', '.')
        logger.debug('input_with_dots: ' + str(input_with_dots) + ' ' + str(type(input_with_dots)))
# - exit als input_with_dots niet Numeric is
        input_number = None
        try:
            input_number = Decimal(input_with_dots)
        except:
            msg_index = 1
            logger.debug('msg_index: ' + str(msg_index) + ' ' + str(type(msg_index)))
        logger.debug('input_number: ' + str(input_number) + ' ' + str(type(input_number)))
        if input_number is not None:
# - zet strCijfer om in Decimal (crcCijfer is InputCijfer * 10 bv: 5,6 wordt 56 en .2 wordt 2
            # casting to string then converting to decimal
            # '', ' ' and non-numeric give InvalidOperation error
# - replace '67' by '6.7', only when it has no decimal places and is between 11 thru 99
            # the remainder / modulus operator (%) returns the remainder after (integer) division.
            remainder = input_number % 1
            logger.debug('remainder: ' + str(remainder) + ' ' + str(type(remainder)))
            if remainder == 0:
                if input_number < 1 or input_number > 99:
                    msg_index = 1
                elif input_number > 10 and input_number < 100:
    # input_number is an integer between 11 and 99. Convert to 1.1 through 9.9
                    input_number = input_number / 10
                    logger.debug('input_number / 10: ' + str(input_number) + ' ' + str(type(input_number)))
                    output_text = str(input_number)
    # replace dot by comma
                    output_text = output_text.replace('.', ',')
                else:
    # input_number is an integer between 1 and 10. Convert to string and add ",0"
                    output_text = str(input_number) + ",0"
            else:
    # input_number has digits after the dot
    # - exit als more than 1 digit after the dot.
                # multiply by 10, get remainder after division by 1, check if remainder has value
                # the remainder / modulus operator (%) returns the remainder after (integer) division.
                remainder_2nd_digit = (input_number * 10) % 1
                if remainder_2nd_digit:
                    msg_index = 2
                else:
                    output_text = str(input_number)
# replace dot by comma
                    output_text = output_text.replace('.', ',')

        if msg_index:
            msg_err = str(_('Grade')) + " '" + imput_trim + "' " + str(_('is not allowed.')) + "\n"
            if msg_index == 1:
                msg_err += str(_('The grade must be a number between 1 and 10.'))
            elif msg_index == 2:
                msg_err += str(_('The grade may only have one digit after the dot.'))
        # eturn array with output number and msg_err

    logger.debug('return input_number: ' + str(input_number) + ' ' + str(type(input_number)))
    return input_number, output_text, msg_err

"""
Public Function CalcEindcijfer_CijferOvg(ByVal Exk_Locked As Boolean, ByRef kv_AfkVak As String, _
                        ByVal IsCombiOfKeuzeCombi As Boolean, ByVal vsi_HasPraktijkex As Boolean, ByVal Kv_IsExtraVak_TeltNietMee As Boolean, _
                        ByVal vsi_CijferTypeID As Byte, ByVal vsi_SEweging As Single, ByVal vsi_CEweging As Single, _
                        ByRef kv_IsHerVak() As Boolean, ByVal kv_HasVrst As Boolean, ByRef kv_Input() As String, _
                        ByRef kv_SE_Ref() As String, kv_CE_Ref() As String, ByRef kv_PeCe_Ref() As String, kv_Eindcijfer_Ref() As String, _
                        ByRef MaxTv() As Byte, ByRef kv_UseVrst() As Boolean, ByRef kv_CheckVrst() As Boolean, ByRef Kv_Eindcijfers As String, _
                        ByRef kv_CLcijferSE As String, ByRef kv_CLcijferCE As String, ByRef kv_CLcijferEIND As String) As Boolean
On Error GoTo Err_CalcEindcijfer_CijferOvg

        'PR 6 jan 07, 15 jan 07, 3 okt 09 gew, 15 feb 12, 8 mrt 12, 2 mei 12 PR2015-12-09 PR2016-01-23
            'Functie berekent Eindcijfer van dit vak op basis van cijfers Kv_GemidSE, Kv_GemidCSE, Kv_Input(PEcijfer) (+na her), weging, combinatievakken
            'bij cijfertype 2 "Voldoende/Onvoldoende" wordt alleen waarde van Kv_GemidSE genomen als resultaat, Kv_GemidCSE wordt dan niet meegeteld
        'NB: skip functie in 1. als kandidaat is vergrendeld PR2016-04-16
        'PR2017-01-21 verwijderd: 'NB: in deze functie wordt Resultaat en CijferID van de andere combivakken geupdate
        
        'Functie wordt aangeroepen door:
            'ClassKandidaat.CalculateResultaten, ClassKandidaat.Kv_CalcEindcijfer, Form_C_CL_Resultaten.Calc_Eindcijfer, Form_K_BL_Resultaten.Calc_Eindcijfer

        ' VakSchema.CE en VakSchema.SE geven verhouding weer (Single, default 1) 'PR 3 jun 09 In update07 wordt default gewijzigd in 1
        'waarde Vakken.CijferTypeID:  1="Nummer";2="Voldoende/Onvoldoende";3="Geen cijfer"
            
        'PR 28 jan 12: Kv_IsKeuzeCombi toegevoegd
        'PR  7 mrt 12: als booIsNormalExamen=True wordt gewoon resultaat berekend, als kv_IsHerVak=True wordt HerExamen resultaat berekend
        'PR  2 mei 12: VakResultaat blijft Null als er een cijfer niet is ingevuld, in overleg HvD
        'PR 28 apr 13: Kv_EindcijferTv02_Ref geeft hoogste resultaat van 1e en 2e tijdvak, ipv resultaat GemSE en GemHer
        'PR2013-11-23 functie naar ClassKandidaat verplaatst, stond in module Calculations
        'PR2015-04-11 staat weer terug in Calculations, wanneer dat gebeurd is weet ik niet
        'PR2015-11-02 naam functie was: GetVakResultaat
        'PR2015-12-08 toegevoegd: Kv_GemidPE, KvGemidPS, Kv_GemidPEHer, KvGemidPSHer
        'PR2016-01-16 uitgeschakeld Was: 'PR2015-12-08 Kv_GemidCSE en Kv_GemidHerex ByRef van gemaakt, om berekende waarde terug te kunnen zetten
        'PR2016-01-16 Kv_GemidPECe_Ref en Kv_GemidPECeHer_Ref toegevoegd, CE-cijfer van praktijkexamen wordt hierin opgeslagen (GemidCSE bevat schriftelijk deel)
        'PR2016-01-23 zet CE cijfer bij niet praktijkvakken ook in Kv_GemidPECe, calcPassedFailed rekent voortaan met Kv_GemidPECe en niet meer met Kv_GemidCSE
        'PR2016-02-07 verwijderd: ByVal Kv_GemidPEHer As String
        'PR2016-02-07 PeHer verwijderd: Was: debug: LET OP bij berekening PeCeHer: PeCeHer is gemiddelde van Max(Ce en CeHer) en Max(Pe en PeHer), dus NIET: gemiddelde van CeHer en PeHer

        'PR2017-01-21 verwijderd (NIG): ByRef_KvCijferIDTv01, ByRef_KvCijferIDHerex_IsMaxTv01Tv02
        'PR2017-02-27 ook voor combi/keuze-combi vakken wordt miv 2017 Eindcijfer berekend. Gebeurt in CalcEindcijfer_Cijfer
        'PR2019-01-16 Vrijstelling en HerTv03 toegevoegd KvHerTv03 As String, ByRef Kv_PeCeTv03_Ref
        'PR2019-04-11 kv_IsExtraVak_TeltNietMee toegevoegd, wordt alleen gebruikt in ConvertOutputToString om in Ex5 aan te kunnen geven

        'PR2019-02-06 toegevoegd:
        ' Public Const inputSE As Byte = 0, inputPE As Byte = 1, inputCE As Byte = 2, inputHER As Byte = 3, inputTV03 As Byte = 4, inputSEvrst As Byte = 5, inputCEvrst As Byte = 6

        'PR2020-05-12 Corona:
        ' - waarde Vsi_HasPraktijkex wordt op 0 gezet voor alle vakken

        Dim crcSEweging As Currency, crcCEweging As Currency, isOk As Boolean
        Dim crcSE(3) As Currency, crcPE As Currency, crcCE(3) As Currency, crcPeCe(3) As Currency, crcEINDcijfer(3) As Currency 'PR2019-03-12
        Dim booNoInputSE(3) As Boolean, booNoInputPeCe(3) As Boolean 'PR2019-03-06 toegevoegd, om PeCeCijfer op 0 te zetten als niet alle cijfers zijn ingevuld
        Dim strInputSE(6) As String, strInputCE(6) As String, strOvgMax As String 'PR2019-03-25
        Dim Tv As Byte, DEFtv As Byte
        Dim kv_Ex5cijfers As String
        
        Dim crcPeCeMAX As Currency, crcEindcijferMAX As Currency 'PR2019-04-23

        'PR2020-05-29 Corona debug: Lorraine Wieske JPD: SE_na_herkansing verschijnt niet op cijferlijst,
        ' aparte parameter crcSEcijfer_na_herkansing() gemaakt
        Dim crcSEcijfer_na_herkansing(3) As Currency
        
        'Ex5 cijfers :
            'Tv01: als UseVrst: SEvrst-CEvrst-ECvrst, anders SE-PeCe-Ec
            'Tv02: als UseVrst blanco, anders: PeCeHER-EcHER
            'Tv03: als UseVrst blanco, anders: PeCeTv03-EcTv03
        'op CIjferlijst: als vrst: SEvrst-CEvrst-ECvrst,anders: MAX SE-PeCe-Ec
        'voor uitslagberekening:
            'Tv01: als UseVrst: SEvrst-CEvrst-ECvrst, anders SE-PeCe-Ec
            'Tv02: als UseVrst: SEvrst-CEvrst-ECvrst, anders MAX (tv01-Tv02)
            'Tv03: als UseVrst: SEvrst-CEvrst-ECvrst, anders MAX (tv01-Tv02-Tv03)
            
'==========================
'A. Validatie
'==========================
        '1. Exit als kandidaat vergrendeld PR2016-04-03
            'PR2019-01-24 vervallen: 2. Exit bij IsCombinatieVak
                                    '3. Exit bij IsKeuzeCombiVak
        '4. alleen bij CijferType = Nummer
        '5. Ga na of vak CombinatieVak of KeuzeCombivak is 'PR2017-02-27
        '6. Herex kan alleen bij Herex kandidaat (moet altijd het geval zijn, voor de zekerheid toegevoegd PR2016-02-07
        '7. Praktijkexamen alleen bij Exk_Examenjaar >= 2016, set Vsi_HasPraktijkex = False bij eerdere examenjaren 'PR2016-01-02
            'PR2015-12-12 vervallen: '8. haal Vsi-variabelen op 'PR2015-12-12 Vsi-variabelen in Query opgenomen, is sneller.
        
    '1. Exit als kandidaat vergrendeld PR2016-04-03
        If Exk_Locked Then
            GoTo Exit_CalcEindcijfer_CijferOvg
        End If
        
    '2. Exit bij IsCombinatieVak
        'PR2016-12-26 uitgeschakeld, ook voor combivakken wordt voortaan eindcijfer berekend

    '3. Exit bij IsKeuzeCombiVak
        'PR2016-12-26 uitgeschakeld, ook voor combivakken wordt voortaan eindcijfer berekend

    '4. reset output parameters PR2019-03-22
        Erase kv_SE_Ref
        Erase kv_CE_Ref
        Erase kv_PeCe_Ref()
        Erase kv_Eindcijfer_Ref()
        
        Kv_Eindcijfers = vbNullString
        kv_CLcijferSE = "---" 'PR2019-05-03 toegevoegd
        kv_CLcijferCE = "---"
        kv_CLcijferEIND = "---"

        'NB: kv_hasVrst is input parameter, niet resetten PR2019-04-21
        Erase MaxTv()
        Erase kv_UseVrst()
        Erase kv_CheckVrst()

    '5. Ga na of vak CombinatieVak of KeuzeCombivak is 'PR2017-02-27
        'PR2019-02-26 debug.(pblAfd.KeuzeCombiAllowed ontbrak). Was: booIsCombi = True als (Vsi_IsCombiVak=True) OR (Vsi_KeuzeCombiAllowed=True AND VsiKeuzeCombiAllowed=True AND KvIsKeuzeCombi=True)
        'PR2015-04-26 DEBUG CAL Lionel Mongen: Bij vsbo waren alle kandidaatvakken IsKeuzeCombi, daarom werd eindcijfer niet berekend.  'zie opmerking PR2015-02-16 debug: IsExtraVak en KeuzeCombi werden als True ingevuld, weet niet waarom
        'Om dit te voorkomen wordt IsKeuzeCombi allleen True als pblafd.KeuzeCombiAllowed (alleen bij Vwo) en als VsiKeuzeCombiAllowed (alleen vakken waarbij KeuzeCombi is toegestaan)
        'PR2019-04-19 buiten deze functie geplaatst: IsCombiOfKeuzeCombi = (Vsi_IsCombiVak) Or (pblAfd.KeuzeCombiAllowed And Vsi_KeuzeCombiAllowed And Kv_IsKeuzeCombi)

    '6. Herex kan alleen bij Herex kandidaat (moet altijd het geval zijn, voor de zekerheid toegevoegd PR2016-02-07
        'PR2019-04-23 uitgeschakeld, laat eindcijfer alleen afhangen van gegevens van kv record, niet van exk record
        ' in plaats van steeds (Exk_IsHerexKand And kv_IsHerVak) te gebruiken:
        'was: IsHerVak(conTv02) = k_IsHerexKandTv02 And kv_IsHerVak(conTv02)
             'IsHerVak(conTv03) = k_IsHerexKandTv03 And kv_IsHerVak(conTv03) 'PR2019-01-23 toegevoegd

    '7. Praktijkexamen alleen bij Exk_Examenjaar >= 2016, set Vsi_HasPraktijkex = False bij eerdere examenjaren 'PR2016-01-02
        'PR2019-04-21 verwijderd:
        'Vsi_HasPraktijkex = (Exk_Examenjaar >= 2016) And Vsi_HasPraktijkex 'PR2019-01-23 Was:   If Exk_Examenjaar < 2016 Then 'Vsi_HasPraktijkex = False 'End If

    '8. haal Vsi-variabelen op
        'PR2015-12-12 Vsi-variabelen in Query opgenomen, is sneller. Was: 2. haal gegevens op uit ClassVakSchemaItem
            
    '9. bereken weging
        'exit bij negatieve weging of geen weging, zet Vsi_SEweging (Single) om in crcSEweging(Currency)
        'PR2020-05-10 Corona. Geen CE. CalcWeging maakt CE-weging = 0 voor alle vakken
            'PR2020-05-20 debug. Niet doen, dan wordt weging vrijstelling 0.
        isOk = CalcWeging(vsi_SEweging, vsi_CEweging, crcSEweging, crcCEweging)
        If Not isOk Then
            GoTo Exit_CalcEindcijfer_CijferOvg
        End If

'=====================================================================================================
'B. bereken SE, PeCe en Eindcijfer voor elk tijdvak, alleen bij CijferType Nummer
'=====================================================================================================

    ' PR2019-01-23 alleen Vsbo vakken 'stage' en 'sectorwerkstuk' en Havo/Vwo vakken 'cav' en 'lo' hebben CijferType VoldoendeOnvoldoende
    ' ze worden bij uitslagberekening apart behandeld:
    ' Havo/Vwo:CAV en LO moeten voldoende zijn, behalve bij avondschool PR2014-05-18 'PR2019-10-21 toegevoegd: idem bij landsexamen
    ' Vsbo TKL: sectorwerkstuk de kwalificatie "voldoende" of "goed" is behaald.
    ' Vsbo Pkl PBL stage telt niet mee bij uitslag, moet wel gedaan zijn.
    'NB: T/M EXAMENJAAR 2015 tellen alleen CE cijfers mee en kun je geen praktijkcijfers invoeren PR2016-01-23
    ' bepaal Eindcijfer bij CijferType Nummer miv 2017 ook voor combivakken en KeuzeCombi vakken
               
'Bereken PeCe-cijfer
            '1. bereken PeCe-cijfer als HasPraktijkexamen (nvt als Examenjaar<2016, wordt bovenin uitgefilterd) 'PR2015-12-08 'PR2016-01-16 ' PR2016-01-23
                'a. CE en PE moeten beide zijn ingevuld
                'b. bereken gemiddeld PeCe-cijfer
                'c. rond af op 1 cijfer achter de komma
            '2. als geen HasPraktijkexamen:
                'a. PeCe-cijfer is gelijk aan CE-cijfer
            '3. Bij Herexamen of HerTv03: idem als bij eerste tijdvak
            
            '4. bereken PeCe-cijfer bij vrijstelling: PE cijfer is niet ingevuld. CE cijfer wordt tevens PeCe cijfer PR2019-02-06
            '5. bij geen Praktijkexamen: zet waarde CE in crcPeCeCijfer en waarde HER in crcPeCeHerCijfer
            '6. bereken Kv_GemidPECe_Ref en Kv_GemidPECeHer_Ref
    
            '+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            '+  PeCEcijferNietAfgerond = (PEcijfer + CEcijfer) / 2                       +
            '+  PeCEcijfer             = Int(0.5 + PeCEcijferNietAfgerond x 10) / 10     +
            '+                                                                           +
            '+                           (SEcijfer x SEweging) + (PeCEcijfer x CEweging) +
            '+  EindcijferNietAfgerond = ---------------------------------------------   +
            '+                                       (SEWeging + CEweging)               +
            '+                                                                           +
            '+  Eindcijfer             = Int(0.5 + EindcijferNietAfgerond)               +
            '+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

'Bereken eindcijfer
            '5. bereken weging
                'a. haal weging op uit Vsi
                'b. exit bij negatieve weging of geen weging
                'c. voer controles uit. Exit als getal kleiner dan 0 of groter dan 10
            '6. ga na of cijfers zijn ingevuld. Zo niet, geen vakresultaat PR 2 mei 12 validatie toegevoegd na overleg HvD voor Ex2A
            '5. bereken Eindcijfer ( = VakResultaat) van het eerste tijdvak
            '6. bereken eindcijfer herexamen
    
            ' VakSchema.CE en VakSchema.SE geven verhouding weer (Single, default 1) 'PR 3 jun 09 In update07 wordt default gewijzigd in 1
            'waarde Vakken.CijferTypeID:  1="Nummer";2="Voldoende/Onvoldoende";3="Geen cijfer"
    
            'PR2017-01-22
            ' eindcijfer wordt berekend op basis van 3 cijfers: SE, PE en CE en de berekende PeCe.
            ' er zijn 7 invoercijfers: SE, SEvrst, PE, CE, CEvrst, Her, Tv03
            ' en 4 modifiers: HasVrst, HasPraktijk, IsHer, IsHerTv03
            ' er zijn 4 tijdvakken Tv01, Tv02, Tv03 en Vrst en de hoogste van deze: DEF
            
            '  PR2019-01-24 de volgende inputcijfers worden gebruikt bij het berekenen van het eindcijfer van de verschillende tijdvakken:
            '  Invoercijfer | Vrst  |Tv01   | Tv02  | Tv03
            '  -------------------------------------------
            '  SEvrst       |   X   |       |       |       als IsVrst=True
            '  SE           |       |   X   |   X   |   X
            '  -------------------------------------------
            '  PE           |       |   X   |   X   |   X   als Hasprakt = True, skip als IsVrst=True
            '  -------------------------------------------
            '  CEvrst       |   X   |       |       |       als IsVrst=True
            '  CE           |       |   X   |       |
            '  Her          |       |       |   X   |       als IsHer = True
            '  HerTv03      |       |       |       |   X   als IsTv03 = True
            
            'PR2020-10-08 In examenjaar 2021 na Corona wordt Vrst eindcijfer ook berekend als CE niet is ingevuld
 
        Dim IsTv123 As Boolean, IsTvVrst As Boolean


Dim strTv(3) As String
strTv(0) = "Tv01"
strTv(1) = "Tv02"
strTv(2) = "Tv03"
strTv(3) = "TvVrst"

If WriteToDebug Then DebugLog "---------------- CalcEindcijfer_CijferOvg ------------ vak: " & kv_AfkVak & vbCrLf & _
                              "kv_IsHerVak : <" & kv_IsHerVak(conTv01) & "> <" & kv_IsHerVak(conTv02) & "> <" & kv_IsHerVak(conTv03) & ">" & vbCrLf & _
                              "kv_Input(SE): <" & kv_Input(inputSE) & "> PE: <" & kv_Input(inputPE) & "> CE: <" & kv_Input(inputCE) & "> HER: <" & kv_Input(inputHER) & "> TV03: <" & kv_Input(inputTV03) & "> SEvrst: <" & kv_Input(inputSEvrst) & "> CEvrst: <" & kv_Input(inputCEvrst) & ">"
                              
'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        For Tv = conTv01 To conTvVrst
'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

        ' Kv_Input heeft index inputSE tm inputCEvrst
        ' strInputSE en heeft index Tv01 tm TvVrst tm inputCEvrst
        ' Deze functie zet inputcijfers van Kv_Input om in naar strInputSE(Tv01 tm TvVrst) etc., is makkelijker met doorlopen Tv's
 
            IsTv123 = (Tv = conTv01) Or _
                      (Tv = conTv02 And kv_IsHerVak(conTv02)) Or _
                      (Tv = conTv03 And kv_IsHerVak(conTv03))
            IsTvVrst = Tv = conTvVrst And kv_HasVrst
            
            If IsTv123 Or IsTvVrst Then
        '1. geef waarde aan strInputSE. Is kv_Input(inputSE) of kv_Input(inputSEvrst)
            'zet de Kv_Input(met index inputSE en inputSEvrst), om in strInputSE( met index Tv123 of TvVrst)
               If IsTv123 Then
                    strInputSE(Tv) = kv_Input(inputSE)
                ElseIf IsTvVrst Then
                    strInputSE(Tv) = kv_Input(inputSEvrst)
                End If
        '2. geef waarde aan strInputCE. Is kv_Input(inputCE), kv_Input(inputHER), kv_Input(inputTV03) of kv_Input(inputCEvrst)
            'zet de Kv_Input(met index inputCE, inputHER, inputTV03, inputCEvrst), om in strInputCE( met index Tv123 of TvVrst)
                If Tv = conTv01 Then
                    strInputCE(Tv) = kv_Input(inputCE)
                ElseIf Tv = conTv02 And kv_IsHerVak(conTv02) Then
                    strInputCE(Tv) = kv_Input(inputHER)
                ElseIf Tv = conTv03 And kv_IsHerVak(conTv03) Then
                    strInputCE(Tv) = kv_Input(inputTV03)
                ElseIf IsTvVrst Then
                    strInputCE(Tv) = kv_Input(inputCEvrst)
                End If

'=============================================================================
'1. bepaal Eindcijfer bij CijferType VoldoendeOnvoldoende
'=============================================================================
                If Not vsi_CijferTypeID = conCijferType01_Nummer Then
            
                    'NB: Herex komt niet voor bij vakken die VoldoendeOnvoldoende hebben 'PR 9 mrt 1
                    'NB: CE cijfer komt niet voor bij vakken die VoldoendeOnvoldoende hebben
                    'PR2019-02-13 Eindcijfer Ovg kan waarde inputSE of inputSEvrst hebben
                        
                '1. geef waarde aan booNoInputSE, onthoudt of input niet is ingevuld 'PR2019-03-25
                    If strInputSE(Tv) = vbNullString And crcSEweging > 0 Then
                        booNoInputSE(Tv) = True
                    End If

                '2. zet SE-cijfer in Kv_SE_Ref. Eindcijfer is gelijk aan SE (TODO niet bij Corona!). Zet SE-cijfer in Kv_Eindcijfer_Ref.
                    If Not booNoInputSE(Tv) Then
                        kv_SE_Ref(Tv) = strInputSE(Tv)
    
                    'PR2020-05-15 Corona: Herkansing mogelijk bij ovg vakken.
                        If pblAfd.IsCorona Then
                        '2. bereken PeCecijfer uit PE en CE of crcCEvrijst PR2019-01-24
                            'geen crc bij ovg vakken
                        '2. geef waarde aan booNoInputPeCe, onthoudt of input niet is ingevuld 'PR2019-03-06
                           ' alleen bij herkansing
                            booNoInputPeCe(Tv) = (Tv = conTv02 And strInputCE(Tv) = vbNullString)
            
                        '3. zet herkansing cijfer in kv_CE_Ref en Kv_PeCe_Ref (formatted string)
                            'laat blanco als een van de vereiste input cijfers niet is ingevuld PR2019-03-06
                            'PR2020-05-12 Corona. kv_PeCe_Ref = 0 bij Corona, behalve bij TvVrst. Die berekent eincijfer op de normale manier
                            If Tv = conTv02 And Not booNoInputPeCe(Tv) Then
                                kv_CE_Ref(Tv) = strInputCE(Tv)
                                kv_PeCe_Ref(Tv) = strInputCE(Tv)
                            End If
        '-----------------------------------------------------------------------------
        'Bereken crcEindcijfer van Tv01 tm Tv 03 en TvVrst
        '-----------------------------------------------------------------------------
                    '1. bereken crcEindcijfer per tijdvak, is 0 als een van de cijfers niet is ingevuld
                            'niet bij ovg
                    '2. zet eindcijfer per tijdvak in Kv_Eindcijfer_Ref.
                            Call CalcEindcijfer_Ovg_Her_Corona(Tv, booNoInputSE(), booNoInputPeCe(), kv_SE_Ref(), kv_CE_Ref(), kv_Eindcijfer_Ref())
                        Else 'If pblAfd.IsCorona Then
                            kv_Eindcijfer_Ref(Tv) = strInputSE(Tv)
                        
                        End If ' If pblAfd.IsCorona
                    End If ' If Not booNoInputSE(Tv)

                Else

'=============================================================================
'2. bepaal Eindcijfer bij CijferType Nummer
'=============================================================================
    '-----------------------------------------------------------------------------
    ' Zet cijfer om in getal
    '-----------------------------------------------------------------------------
    
             '1. zet SE string om in getal
                 'PR2019-03-06 SE cijfer bij alle tijdvakken invullen
                     crcSE(Tv) = GetNumericFromInputCijfer(strInputSE(Tv))

             '2. zet CE string om in getal
                     crcCE(Tv) = GetNumericFromInputCijfer(strInputCE(Tv))
             
             '3. geef waarde aan booNoInputSE, onthoudt of input niet is ingevuld 'PR2019-03-22
                     If crcSE(Tv) = 0 And crcSEweging > 0 Then
                         booNoInputSE(Tv) = True
                     End If
             '4. zet SE cijfer per tijdvak in Kv_SE_Ref
                     If (Not booNoInputSE(Tv)) Then
                         kv_SE_Ref(Tv) = strInputSE(Tv)
                     End If
             '5. geef waarde aan booNoInputCE,
                  'samen met PE, booNoInputPeCe wordt ingevuld bij PeCe 'PR2019-03-06

    '-----------------------------------------------------------------------------
    ' Bereken PeCe cijfer
    '-----------------------------------------------------------------------------
        
                '1. als Corona: zet waarde Vsi_HasPraktijkex op 0 voor alle vakken. PeCe is dan gelijk aan CE-cijfer. PR2020-05-12
                    If pblAfd.IsCorona Then vsi_HasPraktijkex = False
        
                    Call CalcEindcijfer_PeCe(Tv, kv_HasVrst, vsi_HasPraktijkex, crcCEweging, kv_IsHerVak(), _
                                                booNoInputPeCe(), strInputCE(), kv_Input(), _
                                                crcCE(), crcPeCe(), kv_CE_Ref(), kv_PeCe_Ref())

    '-----------------------------------------------------------------------------
    'Bereken crcEindcijfer van Tv01 tm Tv 03 en TvVrst
    '-----------------------------------------------------------------------------

            '1. bereken crcEindcijfer per tijdvak, is 0 als een van de cijfers niet is ingevuld
                    'crcEINDcijfer wordt berekend uit crcSEcijfer en PeCeCijfer (plus crcSEweging en crcCEweging)
                    If pblAfd.IsCorona And Not IsTvVrst Then
                        'PR2020-05-12 Corona. Aparte berekening voor Corona, behalve bij TvVrst. Die berekent het op de normale manier
                        
                        'PR2020-05-29 Corona debug: Lorraine Wieske JPD: SE_na_herkansing verschijnt niet op cijferlijst,
                        ' aparte parameter crcSEcijfer_na_herkansing() gemaakt. Wordt alleen gebruikt in Tv02 bij IsCorona
                        crcEINDcijfer(Tv) = CalcEindcijfer_Crc_Corona(kv_AfkVak, Tv, crcSEweging, crcSE(Tv), crcPeCe(Tv), crcSEcijfer_na_herkansing())
                    
                    ElseIf pblAfd.IsPostCorona And IsTvVrst Then
                        'PR2020-10-082 PostCorona. Aparte berekening voor 2021 Wordt alleen gebruikt in TvVrst bij PostCorona. Geeft ook eindcijfer als CE niet is ingevuld.
                        crcEINDcijfer(Tv) = CalcEindcijfer_Crc_Vrst_PostCorona(kv_AfkVak, Tv, crcSEweging, crcCEweging, crcSE(Tv), crcPeCe(Tv))
                    
                    Else
                        'PR2019-05-03 debug: geldt NIET voor KeuzeCombi (denk ik), omdat CE cijfer meetelt in Eindcijfer
                        crcEINDcijfer(Tv) = CalcEindcijfer_Crc(IsCombiOfKeuzeCombi, crcSEweging, crcCEweging, crcSE(Tv), crcPeCe(Tv))
                    End If
                    
            '2. zet eindcijfer per tijdvak in Kv_Eindcijfer_Ref.
                    'EIndcijfer is geheel getal, geen andere formatting nodig dan Cstr()
                    'PR2020-10-082 PostCorona. Bij PostCorona als conTvVrst: skip booNoInputPeCe
                    If (Not booNoInputSE(Tv) And Not booNoInputPeCe(Tv)) Or (pblAfd.IsPostCorona And Tv = conTvVrst And Not booNoInputSE(Tv)) Then
                        kv_Eindcijfer_Ref(Tv) = CStr(crcEINDcijfer(Tv))
                    End If

                End If 'If Vsi_CijferTypeID = conCijferType01_Nummer
                
            End If 'If IsTv123 Or IsTvVrst Then
        Next Tv
'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
'       einde  For Tv = conTv01 To conTvVrst
'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

If WriteToDebug Then DebugLog "booNoInputSE  : <" & booNoInputSE(conTv01) & "> <" & booNoInputSE(conTv02) & "> <" & booNoInputSE(conTv03) & "> Vrst: <" & booNoInputSE(conTvVrst) & ">" & vbCrLf & _
                              "booNoInputPeCe: <" & booNoInputPeCe(conTv01) & "> <" & booNoInputPeCe(conTv02) & "> <" & booNoInputPeCe(conTv03) & "> Vrst: <" & booNoInputPeCe(conTvVrst) & ">" & vbCrLf & _
                              "kv_SE_Ref     : <" & kv_SE_Ref(conTv01) & "> <" & kv_SE_Ref(conTv02) & "> <" & kv_SE_Ref(conTv03) & "> Vrst: <" & kv_SE_Ref(conTvVrst) & ">" & vbCrLf & _
                              "kv_CE_Ref     : <" & kv_CE_Ref(conTv01) & "> <" & kv_CE_Ref(conTv02) & "> <" & kv_CE_Ref(conTv03) & "> Vrst: <" & kv_CE_Ref(conTvVrst) & ">" & vbCrLf & _
                              "kv_PeCe_Ref   : <" & kv_PeCe_Ref(conTv01) & "> <" & kv_PeCe_Ref(conTv02) & "> <" & kv_PeCe_Ref(conTv03) & "> Vrst: <" & kv_PeCe_Ref(conTvVrst) & ">" & vbCrLf & _
                              "kv_Eind_Ref   : <" & kv_Eindcijfer_Ref(conTv01) & ">   <" & kv_Eindcijfer_Ref(conTv02) & ">   <" & kv_Eindcijfer_Ref(conTv03) & ">   Vrst: <" & kv_Eindcijfer_Ref(conTvVrst) & ">" & vbCrLf

'==================================================================
'E.Bereken MaxTv en UseVrst voor Tv01, Tv02 en Tv03
'==================================================================

    '1. bereken voor elk tijdvak, het tijdvak met het hoogste eindcijfer
        'NB: geen NoInput gebruiken, hoogste wordt altijd weergegeven ook al is een van de 2 niet ingevuld of als geen Her

        Call CalcEindcijfer_Max(kv_AfkVak, kv_HasVrst, kv_IsHerVak(), booNoInputSE(), booNoInputPeCe(), _
                                vsi_CijferTypeID, crcSE(), crcPeCe(), crcEINDcijfer(), kv_SE_Ref(), kv_PeCe_Ref(), kv_Eindcijfer_Ref(), _
                                MaxTv(), kv_UseVrst(), kv_CheckVrst())
                                
If WriteToDebug Then DebugLog "MaxTv         : <" & strTv(MaxTv(conTv01)) & ">   <" & strTv(MaxTv(conTv02)) & ">   <" & strTv(MaxTv(conTv03)) & ">" & vbCrLf & _
                              "Kv_UseVrst    : <" & kv_UseVrst(conTv01) & ">   <" & kv_UseVrst(conTv02) & ">   <" & kv_UseVrst(conTv03) & ">" & vbCrLf & _
                              "kv_CheckVrst  : <" & kv_CheckVrst(conTv01) & ">   <" & kv_CheckVrst(conTv02) & ">   <" & kv_CheckVrst(conTv03) & ">" & vbCrLf


'==================================================================
'G. vul cijfers in die op de cijferlijst worden getoond, "---" als niet ingevuld
'==================================================================
      
        'PR2019-06-28 debug: Randy de Wolff St Jozef: Cijferlijst geeft her weer ook als CE hoger is
        'PR2020-05-29 Corona debug: Lorraine Wieske JPD: SE_na_herkansing verschijnt niet op cijferlijst,
        ' aparte parameter crcSEcijfer_na_herkansing() gemaakt. Wordt alleen gebruikt in Tv02 bij IsCorona
        Call CalcEindcijfer_Display(kv_AfkVak, kv_IsHerVak(), MaxTv(), kv_UseVrst(), kv_SE_Ref(), kv_PeCe_Ref(), kv_Eindcijfer_Ref(), _
                                        crcSEcijfer_na_herkansing(), _
                                    kv_CLcijferSE, kv_CLcijferCE, kv_CLcijferEIND)
        
    '6. Geef waarde aan kv_Eindcijfers
        'PR2019-04-20 gebruik UseHerTv02/UseHerTv03 in plaats van IsHerTv02, IsHerTv03
        Kv_Eindcijfers = ConvertOutputToString(kv_AfkVak, kv_SE_Ref(), kv_PeCe_Ref(), kv_Eindcijfer_Ref(), _
                                               IsCombiOfKeuzeCombi, Kv_IsExtraVak_TeltNietMee, vsi_HasPraktijkex, kv_IsHerVak(), kv_HasVrst, _
                                               MaxTv(), kv_UseVrst(), kv_CheckVrst())
                                           
    '7. ga na of vrijstelling is gebruikt voor eindcijfer
        'PR2020-05-13 Corona geeft vrijstelling weer op cijferlijst
        Dim booVrijstellinggebruiktVoorEindcijfer As Boolean
        If kv_HasVrst Then
            If kv_IsHerVak(conTv03) Then
                booVrijstellinggebruiktVoorEindcijfer = kv_UseVrst(conTv03)
            ElseIf kv_IsHerVak(conTv02) Then
                booVrijstellinggebruiktVoorEindcijfer = kv_UseVrst(conTv02)
            Else
                booVrijstellinggebruiktVoorEindcijfer = kv_UseVrst(conTv01)
            End If
        End If


'de volgende velden wordn in tabel KandVak bijgewerkt:
       
    'GemidPeCe      = kv_PeCe_Ref(conTv01)
    'GemidPeCeHer   = kv_PeCe_Ref(conTv02)
    'GemidPeCeTv03  = kv_PeCe_Ref(conTv03)

    'Resultaat      = kv_Eindcijfer_Ref(conTv01)
    'ResultaatHerex = kv_Eindcijfer_Ref(conTv02)
    'ResultaatTv03  = kv_Eindcijfer_Ref(conTv03)
    'ResultaatVrst  = kv_Eindcijfer_Ref(conTvVrst)
    
    'Eindcijfers    = kv_Eindcijfers
    'CLcijferSE     = kv_CLcijferSE
    'CLcijferCE     = kv_CLcijferCE
    'CLcijferEIND   = kv_CLcijferEIND
       
       
    'SE examen
        'GemidSE blijft ongewijzigd
        'GemidSEvrst blijft ongewijzigd
    'CE examen
        'GemidCSE blijft ongewijzigd
        'GemidCSEvrst blijft ongewijzigd
        'GemidPeCe = Kv_PeCe_Ref(conTv01)
        'Resultaat = Kv_Eindcijfer_Ref(conTv01)
    
    'HerExamen
        'GemidHER blijft ongewijzigd
        'GemidPeCeHer = Kv_PeCe_Ref(conTv02)
        'ResultaatHerex = Kv_Eindcijfer_Ref(conTv02)
    
    'Herexamen 3e tv
        'GemidHERTv03 blijft ongewijzigd
        'GemidPeCeTv03 = Kv_PeCe_Ref(conTv03)
        'ResultaatTv03 = Kv_Eindcijfer_Ref(conTv03)
    
    'Vrst
        'ResultaatVrst = Kv_Eindcijfer_Ref(conTvVrst)

'OP cijferlijst
    'SEcijferDEF
    'PeCeDEF
    'EindcijferDEF

'in Ex5:
' eerste tijdvak:
    'GemidSE
    'GemidPeCe
    'Resultaat
    'Aantal vakken          QueryColumn18_EindcijferCount
    'Gemid CE cijfer        QueryColumn14_CEcijferGem_Tv01
    'Som der Eindcijfers:   QueryColumn16_EindcijferSom_Tv01
    ''Uitslag van het examen'  QueryColumn20_IsTeruggetrokken, QueryColumn19_IsManualResultaat, QueryColumn11_ResultaatID_Tv01
'pos ExcelColumn_FirstColumnNaHerexamenVakken
    'ShowGemiddeldCECijfer  QueryColumn15_CEcijferGem_Herex
    'Totaal van de eindcijfers na het herexamen QueryColumn17_EindcijferSom_Herex
    'Uitslag van het examen na tweede tijdvak'  QueryColumn20_IsTeruggetrokken, QueryColumn19_IsManualResultaat, QueryColumn12_ResultaatID_Herex, QueryColumn13_ResultaatID
                         

        CalcEindcijfer_CijferOvg = True 'PR 8 mrt 12  parameter van gemaakt van Kv_EindcijferTv01_Ref. Was: IIf(Kv_EindcijferTv01_Ref = "", Null, Kv_EindcijferTv01_Ref) 'PR 12 feb 07 debug: veld Resultaat accepteert geen ZeroLength string, Null van maken (CalcEindcijfer is variant)
     
        
If WriteToDebug Then DebugLog "booVrijstellinggebruiktVoorEindcijfer   : <" & booVrijstellinggebruiktVoorEindcijfer & vbCrLf & _
        "kv_CLcijferSE = <" & kv_CLcijferSE & "> kv_CLcijferCE = <" & kv_CLcijferCE & "> kv_CLcijferEIND = <" & kv_CLcijferEIND & ">" & vbCrLf & _
        "---------------- end of CalcEindcijfer_CijferOvg ------------ vak: " & kv_AfkVak & vbCrLf

Exit_CalcEindcijfer_CijferOvg:
        Exit Function
    
Err_CalcEindcijfer_CijferOvg:
    '1. reset output parameters 'PR2019-01-23 'PR2014-10-10 toegevoegd
        Erase kv_PeCe_Ref()
        Erase kv_Eindcijfer_Ref()

        MsgBox Err.Description
        ErrorLog conModuleName & " Err_CalcEindcijfer_CijferOvg", Err.Description
        Resume Exit_CalcEindcijfer_CijferOvg
    End Function



"""
