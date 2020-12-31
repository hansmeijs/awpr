"""
Public Function Validate_InputCijfer(ByVal bytSoortExamen As Byte, ByVal booIsScore As Boolean, ByVal ExkExamenjaar As Integer, ByVal ExkLocked As Boolean, _
                                        ByVal KvIsHerTv02 As Boolean, ByVal KvIsHerTv03 As Boolean, _
                                        ByVal KvIsKeuzeCombiVak As Boolean, ByVal KvHasBewijsKennis As Boolean, ByVal KvHasVrst As Boolean, _
                                        ByVal VsiVakSchemaItemAID As Long, ByVal VsiCijferTypeID As Long, _
                                        ByVal VsiSEweging As Single, ByVal VsiCEweging As Single, _
                                        ByVal VsiIsCombinatieVak As Boolean, ByVal VsiHasPraktijkexamen As Boolean, _
                                        ByVal strInputValue As String, ByRef strMsgText As String, _
                                        Optional ByVal booIsImportCijfers As Boolean = False, _
                                        Optional ByVal strScoreOrCijferValue As String = vbNullString, _
                                        Optional ByRef booContinueAllowedRef As Boolean = False, _
                                        Optional ByVal VsiIsETEnorm As Boolean = False, _
                                        Optional ByVal VsiLschaal As String = vbNullString) As Boolean
On Error GoTo Err_Validate_InputCijfer
        Dim intLen As Integer, strCharacter As String, booIsOvg As Boolean, booHasDelimiter As Boolean
        Dim strScoreText As String, strCijferText As String
        'PR2015-04-05 functie hier gezet omdat bij Vakschema wellicht verkeerde vsi gebruikt kan worden.
        'PR 19 feb 12 functie controleert invoer cijfer,
            'NB functie maakt gebruikt van Current Vsi, zorg dat GetVakSchemaItem eerst wordt doorlopen om Current Vsi op te halen
            'output parameters zijn booError en strMsgText
            'booIsImportCijfers =True: verbergt in MsgText melding: "Verander de weging als u hier een cijfer wilt invoeren."
        'PR2015-12-10 functie hier gezet ipv in ClassVsi, Vsi variabelen worden opgehaald in Kv-Vsi query. Werkt (hopeijk) sneller dan ClassVsi

        'SoortExamen =  0.<alle examens kunnen worden ingevuld>, 1.Schoolexamen, 2.CentraalExamen, 3.PraktijkExamen, 4.Herexamen, 5.Her 3e tijdvak PR2019-01-16

        'PR2019-01-16 KvHasVrst toegevoegd.
        ' Als vrijstelling cijfers worden gebruikt (HasVrst = True) worden de volgende instellingen genegeerd:
        ' - scores worden niet gebruikt, maar cijfers
        ' - praktijkcijfer wordt niet ingevuld > has_praktijcijfer = False
        ' - herexamen en herTv03 worden niet gebruikt.

    '1. reset output parameters
        strMsgText = vbNullString
        booContinueAllowedRef = False

    '2. exit als strInputValue  niet ingevuld (strMsgText = vbNullString, geen foutmelding)
        strInputValue = Trim(strInputValue)
        If strInputValue = vbNullString Then GoTo Exit_Validate_InputCijfer

    '3. exit als kandidaat is vergrendeld 'PR2016-03-27
        If ExkLocked Then
            strMsgText = "Kandidaat gegevens zijn vergrendeld."
            GoTo Exit_Validate_InputCijfer
        End If

        'PR2010-06-10 mail Lorraine Wieske: kan geen PE cjfers corrigeren. Weghalen
    '4. exit als dit vak bewijs van kennis heeft. Dan is invoer gegevens geblokkeerd. Ga naar Rpt_Ex6_BewijsKennis om Bewijs van Kennis te wissen. 'PR2017-01-04
        'If KvHasBewijsKennis Then
        '    strMsgText = "Vak heeft Bewijs van Kennis en is daarom vergrendeld." & vbCrLf & "Ga naar Rapportages Ex6 om Bewijs van Kennis zo nodig te wissen."
        '    GoTo Exit_Validate_InputCijfer
        'End If

    '5. exit als VakSchemaItemID niet ingevuld
        If VsiVakSchemaItemAID = 0 Then
            strMsgText = "Vakschema van dit vak is niet ingevuld."
            GoTo Exit_Validate_InputCijfer
        End If

    '6. controleer Praktijkexamen 'PR2019-02-22 'PR2015-12-08
            'wordt ook ingesteld buiten deze functie, in Form_K_BL_Resultaten.Form_Current en Form_C_CL_Resultaten.Form_Current  'PR2016-03-04
        If bytSoortExamen = conExamen03_PE Then 'PR2016-02-07 verwijderd: Or bytSoortExamen = conExamen05_PeHer Then
            'HasPraktijkexamen = False als examenjaar < 2016. Eerdere jaren kunnen geen Pe hebben in AWP
            Dim HasPraktijkexamen As Boolean

            'PR2020-05-15 Corona: heeft geen PE
            HasPraktijkexamen = (ExkExamenjaar >= 2016 And VsiHasPraktijkexamen And Not pblAfd.IsCorona)
            If Not HasPraktijkexamen Then
                If ExkExamenjaar < 2016 Then
                    strMsgText = "AWP heeft nog geen cijfer voor praktijkexamen in examenjaar " & ExkExamenjaar & "." 'PR2016-04-30
                ElseIf pblAfd.IsCorona Then
                    strMsgText = "Er zijn geen praktijkexamens in examenjaar " & ExkExamenjaar & "." 'PR2016-04-30
                Else
                    strMsgText = "Dit vak heeft geen praktijkexamen." 'PR2016-01-16
                End If
                GoTo Exit_Validate_InputCijfer
            End If
        End If

    '7. controleer Herexamen 'PR2015-12-13
        'PR2019-01-16 KvHasVrst kan alleen als conExamen01_SE of conExamen02_CE
        If bytSoortExamen = conExamen04_HER Then 'PR2016-02-07 verwijderd: Or bytSoortExamen = conExamen05_PeHer Then
            If Not booIsImportCijfers Then  'PR2016-04-30 toegevoegd. Debug: import her werd overgeslagen vanwege deze check
                If Not KvIsHerTv02 Then
                    'PR2020-05-15 Corona: "herkansing" ipv "herexamenvak"
                    strMsgText = IIf(pblAfd.IsCorona, "Dit is geen herkansing.", "Dit is geen herexamenvak.")
                    GoTo Exit_Validate_InputCijfer
                End If
            End If
        End If
        If bytSoortExamen = conExamen05_HerTv03 Then 'PR2019-02-08
            If Not booIsImportCijfers Then  'PR2016-04-30 toegevoegd. Debug: import her werd overgeslagen vanwege deze check
                If Not KvIsHerTv03 Then
                    strMsgText = "Dit is geen herexamenvak van het 3e tijdvak."
                    GoTo Exit_Validate_InputCijfer
                ElseIf pblAfd.IsCorona Then
                    strMsgText = "Er is dit examenjaar geen 3e tijdvak."
                    GoTo Exit_Validate_InputCijfer
                End If
            End If
        End If

    '8. controleer weging
        'SoortExamen =  0.<alle examens kunnen worden ingevuld>, 1.Schoolexamen, 2.CentraalExamen, 3.PraktijkExamen, 4.SchriftelijkPraktijkexamen, 5.Herexamen, 6.PeHer, 7.PsHer
        Select Case bytSoortExamen
        Case conExamen01_SE
            If VsiSEweging = 0 Then
                strMsgText = "De SE weging is 0 voor dit vak."
                If Not booIsImportCijfers Then strMsgText = strMsgText & vbCrLf & "Verander de weging als u hier een cijfer wilt invoeren."  'PR2015-01-08 toegevoegd, overslaan bij logfile import cijfers
            End If
        Case conExamen02_CE, conExamen03_PE, conExamen04_HER, conExamen05_HerTv03 'PR2019-01-16. PR2016-02-07 verwijderd: , conExamen05_PeHer ', conExamen06_ScoreCE, conExamen07_ScoreHer, conExamen08_ScorePE, conExamen09_ScorePeHer
            'PR2020-05-19 Corona: dit jaar geen PE, CE (wel bij vrijstelling) en HerTv03
            If pblAfd.IsCorona Then
                Select Case bytSoortExamen
                Case conExamen02_CE
                    'PR2020-05-20 debug: wel bij vrijstelling
                    If Not KvHasVrst Then
                        strMsgText = "Er is dit examenjaar geen Centraal Examen."
                    End If
                Case conExamen03_PE
                    strMsgText = "Er is dit examenjaar geen praktijkexamen."
                Case conExamen05_HerTv03
                    strMsgText = "Er is dit examenjaar geen 3e tijdvak."
                End Select
                If Not strMsgText = vbNullString Then GoTo Exit_Validate_InputCijfer
            End If
            If VsiIsCombinatieVak Then 'PR2019-05-03 keuze-combi weer uitgeschakeld. Was:   Or KvIsKeuzeCombiVak Then 'PR2016-05-30 KeuzeCombi toegevoegd. Was: If VsiIsCombinatieVak Then
                Dim strCombiText As String 'PR2016-05-30
                strCombiText = " niet toegestaan in " & IIf(VsiIsCombinatieVak, "combinatievak.", "keuze-combi vak.")
                If booIsScore Then
                    strMsgText = "Score" & strCombiText 'PR2016-05-30
                Else
                   Select Case bytSoortExamen
                   Case conExamen02_CE, conExamen06_Vrst
                        strMsgText = "CE-cijfer" & strCombiText 'PR2016-05-30
                    Case conExamen03_PE
                        strMsgText = "Praktijkcijfer" & strCombiText 'PR2016-05-30
                    Case conExamen04_HER 'PR2016-02-07 verwijderd: , conExamen05_PeHer ', conExamen07_ScoreHer, conExamen09_ScorePeHer
                        'PR2020-05-15 Corona: herkansing wel mogelijk bij combivakken
                        If Not pblAfd.IsCorona Then
                            strMsgText = "Herexamen-cijfer" & strCombiText 'PR2016-05-30
                        End If
                    Case conExamen05_HerTv03 'PR2019-02-08
                        strMsgText = "Herexamen-cijfer 3e tijdvak" & strCombiText
                    End Select
                End If

            ElseIf VsiCEweging = 0 Then
                'PR2020-05-15 Corona: herkansing wel mogelijk bij vakken die alleen SE hebben
                If pblAfd.IsCorona And bytSoortExamen = conExamen04_HER Then
                    'herkansing wel mogelijk bij vakken die alleen SE hebben
                Else
                    strMsgText = "De CE-weging is 0 voor dit vak."
                End If
                'PR2016-01-10 uitgeschakeld: If Not booIsImportCijfers Then strMsgText = strMsgText & vbCrLf & "Verander de weging als u hier een cijfer wilt invoeren."  'PR2015-01-08 toegevoegd, overslaan bij logfile import cijfers
            End If
        End Select
        If Not strMsgText = vbNullString Then GoTo Exit_Validate_InputCijfer

'A. SCORE
        'PR2019-01-16 bij KvHasVrst is booIsScore = False
    '1. controleer score PR2015-12-27 PR2016-01-03
        If booIsScore Then 'PR2016-01-14 Was: Select Case bytSoortExamen     Case conExamen06_ScoreCE, conExamen07_ScoreHer, conExamen08_ScorePE, conExamen09_ScorePeHer

            'PR2020-05-15 Corona: geen scores
            If pblAfd.IsCorona Then
                strMsgText = "Er kunnen geen scores ingevuld worden in examenjaar " & ExkExamenjaar & "."
            Else
                'PR2015-12-27 debug: vervang komma door punt, anders wordt komma genegeerd
                'PR2016-03-05 debug: werkt niet vanwege Regional Settings. Was: strInputCijfer = Replace(strInputCijfer, ",", ".")
                If Not IsNumeric(strInputValue) Then
                    strMsgText = "Score moet een getal zijn."
                ElseIf CCur(strInputValue) < 0 Then
                    strMsgText = "Score moet een getal groter dan nul zijn."
                ElseIf CCur(strInputValue) - Int(strInputValue) > 0 Then
                    strMsgText = "Score moet een geheel getal zijn."
                End If
                If Not strMsgText = vbNullString Then GoTo Exit_Validate_InputCijfer

                Select Case bytSoortExamen
                Case conExamen01_SE 'PR2016-02-14
                    strMsgText = "SE heeft geen score."
                Case conExamen02_CE, conExamen03_PE, conExamen04_HER, conExamen05_HerTv03 'PR2019-02-08 'PR2016-01-14
                    If Not VsiLschaal = vbNullString Then
                        If IsNumeric(VsiLschaal) Then
                            If CCur(strInputValue) > CCur(VsiLschaal) Then
                                strMsgText = "Score moet kleiner of gelijk zijn aan " & IIf(VsiIsETEnorm, "max. score", "schaallengte") & " (" & VsiLschaal & ")."
                            End If
                        End If
                    End If
                'PR2016-02-07 verwijderd:'Case conExamen05_PeHer 'PR2016-01-14 Was: conExamen09_ScorePeHer
                End Select
            End If
            If Not strMsgText = vbNullString Then GoTo Exit_Validate_InputCijfer

    'PR2019-05-18 deze controle vervalt omdat alleen nog scores kunnen worden ingevuld
    '2. bij invullen score: controleer of cijfer/cijferHer is ingevuld PR2016-01-23
            'als strInputValue een cijfer is bevat strScoreOrCijferValue de score en vice versa PR2019-01-08
            'Select Case bytSoortExamen
            'Case conExamen02_CE, conExamen03_PE, conExamen04_HER, conExamen05_HerTv03
            '    If Not strScoreOrCijferValue = vbNullString Then ' strScoreOrCijferValue is textbox.Value van CE, Her, Pe of HerTv03
            '        Select Case bytSoortExamen
            '        Case conExamen02_CE
            '            strScoreText = "score"
            '            strCijferText = "CE-cijfer"
            '        Case conExamen03_PE
            '            strScoreText = "praktijk score"
            '            strCijferText = "praktijk cijfer"
            '        Case conExamen04_HER
            '            strScoreText = "herexamen score"
            '            strCijferText = "herexamencijfer"
            '        Case conExamen05_HerTv03
            '            strScoreText = "herexamen score 3e tijdvak"
            '            strCijferText = "herexamencijfer 3e tijdvak"
            '        End Select
            '        strMsgText = "Er is een " & strCijferText & " ingevuld (" & strScoreOrCijferValue & ")." & vbCrLf & "Dit cijfer wordt gewist als u de " & strScoreText & " invult. " & vbCrLf & vbCrLf & "Wilt U doorgaan?"
            '        booContinueAllowedRef = True
            '    End If
            'End Select
            'If Not strMsgText = vbNullString Then GoTo Exit_Validate_InputCijfer
        Else 'If booIsScore

'B. CIJFER
    '1. exit als CijferType VoldoendeOnvoldoende is en inputcijfer niet booIsOvg is
            'PR2014-12-10 debug: gaf fout bij importeren cijfers omdat daar gebruik wordt gemaakt van pssVakSchema, niet van pblVakSchema
                'Was: If pblVakSchema.Vsi_CijferTypeID = conCijferType02_VoldoendeOnvoldoende Then 'PR 3 okt 09 was: Me.cijferTypeID = 2 Then

            Select Case VsiCijferTypeID
            Case conCijferType00_GeenCijfer
                strMsgText = "Cijfertype 'Geen cijfer'. Er kan geen cijfer ingevuld worden." 'PR2016-02-14
            Case conCijferType02_VoldoendeOnvoldoende 'PR 3 okt 09 was: Me.cijferTypeID = 2 Then
                'PR2016-02-14 StrComp() = 0 als strings hetzelfde zijn
                If Not StrComp(strInputValue, "o", vbTextCompare) = 0 And _
                    Not StrComp(strInputValue, "v", vbTextCompare) = 0 And _
                    Not StrComp(strInputValue, "g", vbTextCompare) = 0 Then 'PR 19 feb 12 was: If IsNull(DLookup("CijferAID", "Cijfers", "Cijfer = '" & Me.invCijferCE.Value & "'")) Or IsNumeric(Me.invCijferCE.Value) Then
                        strMsgText = "Het cijfer kan alleen g, v of o zijn."
                End If
            Case conCijferType01_Nummer  'PR2016-02-14
                Dim crcCijfer As Currency
                'GetNumericFromInputCijfer wordt alleen gebruikt om te controleren of cijfer een correct getal is, strMsgText<>"" als fout   'PR2016-03-04
                crcCijfer = GetNumericFromInputCijfer(strInputValue, strMsgText)
            End Select
            If Not strMsgText = vbNullString Then GoTo Exit_Validate_InputCijfer

    'PR2019-06-03 toch maar laten vervallen, na paniek mail van Lorraine Wieske dat alle scores zijn verdwenen
    'PR2019-05-18 cijfers invullen kan niet meer, deze controle is dus overbodg. laat voorlopig maar staan.
    '2. bij invullen cijfer: controleer of score/scoreHer is ingevuld PR2016-01-04 PR2016-01-16
            ''als strInputValue een cijfer is bevat strScoreOrCijferValue de score en vice versa PR2019-01-08
            'Select Case bytSoortExamen
            'Case conExamen02_CE, conExamen03_PE, conExamen04_HER, conExamen05_HerTv03
            '    If Not strScoreOrCijferValue = vbNullString Then ' strScoreOrCijferValue is textbox.Value van Score, ScoreHer, ScorePE of ScoreHerTv03
            '        Select Case bytSoortExamen
            '        Case conExamen02_CE
            '            strScoreText = "score"
            '            strCijferText = "CE-cijfer"
            '        Case conExamen03_PE
            '            strScoreText = "praktijk score"
            '            strCijferText = "praktijk cijfer"
            '        Case conExamen04_HER
            '            strScoreText = "herexamen score"
            '            strCijferText = "herexamencijfer"
            '        Case conExamen05_HerTv03
            '            strScoreText = "herexamen score 3e tijdvak"
            '            strCijferText = "herexamencijfer 3e tijdvak"
            '        'PR2016-02-07 verwijderd: Case conExamen05_PeHer
            '            'strScoreText = "praktijk score (herexamen)"
            '        End Select
            '        strMsgText = "Er is een " & strScoreText & " ingevuld (" & strScoreOrCijferValue & ")." & vbCrLf & "Deze score wordt gewist als u het " & IIf(bytSoortExamen = conExamen02_CE, "CE-cijfer", "herexamencijfer") & " invult. " & vbCrLf & vbCrLf & "Wilt U doorgaan?"
            '        booContinueAllowedRef = True
            '    End If
            'If Not strMsgText = vbNullString Then GoTo Exit_Validate_InputCijfer
            'End Select
        End If 'If booIsScore

Exit_Validate_InputCijfer:
        If Not strMsgText = vbNullString Then
            Validate_InputCijfer = True 'PR2015-12-08 Was: Validate_InputCijfer = booError
        End If
        Exit Function
Err_Validate_InputCijfer:
        MsgBox Err.Description
        ErrorLog conModuleName & " Exit_Validate_InputCijfer", Err.Description
        Resume Exit_Validate_InputCijfer
    End Function




"""