# PR2021-11-5

from django.db import connection

from schools import models as sch_mod

import logging
logger = logging.getLogger(__name__)


def update_library(examyear):
    # function to update library PR2020-07-30 PR2023-08-31
    # logger.debug('........update_library..........')

    key_value_list = [
        ('exform', 'minond', 'MINISTERIE VAN ONDERWIJS, WETENSCHAP, CULTUUR EN SPORT'),

        ('exform', 'eex', 'EINDEXAMEN'),
        ('exform', 'lex', 'LANDSEXAMEN'),
        ('exform', 'ey', 'examenjaar'),
        ('exform', 'se', 'schoolexamen'),
        ('exform', 'ses', 'schoolexamens'),
        ('exform', 'cie', 'commissie-examen (CIE)'),
        ('exform', 'cies', 'commissie-examens (CIE)'),
        ('exform', 'ce', 'centraal examen'),
        ('exform', 'cece', 'centraal examen (CE)'),
        ('exform', 'de_ces', 'de centrale examens'),
        ('exform', 'de_cesce', 'de centrale examens (CE)'),
        ('exform', 'eex_lb_rgl01', 'Landsbesluit eindexamens V.W.O., H.A.V.O., V.S.B.O. van de 23ste juni 2008,'),
        ('exform', 'eex_lb_rgl02', 'ter uitvoering van artikel 32, vijfde lid, van de Landsverordening voortgezet onderwijs, no. 54.'),
        ('exform', 'lex_lb_rgl01', 'Landsbesluit landsexamens v.w.o., h.a.v.o., v.s.b.o. van 3 mei 2016,'),
        ('exform', 'lex_lb_rgl02', 'ter uitvoering van artikel 57 van de Landsverordening voorgezet onderwijs, no. 21.'),

        ('exform', 'in_examyear', 'in het examenjaar'),
        ('exform', 'school', 'School:'),
        ('exform', 'col_name01', 'Naam en voorletters van de kandidaat'),
        ('exform', 'col_name02', '(in alfabetische volgorde)'),
        ('exform', 'col_class', 'Klas'),
        ('exform', 'col_exnr', 'Ex.nr.'),
        ('exform', 'col_idnr', 'ID-nummer'),
        ('exform', 'bullet', '*'),

        ('exform', 'extrafacilities', 'Kandidaat maakt gebruik van extra faciliteiten.'),
        ('exform', 'bullet_submitted', 'Dit vak is al op een eerder Ex-formulier ingediend.'),
        ('exform', 'bullet_new', 'Dit is een nieuw vak.'),
        ('exform', 'bullet_deleted', 'Dit vak is gewist.'),
        ('exform', 'bullet_changed', 'Het karakter van dit vak is gewijzigd.'),

        ('exform', 'signature_chairperson', '(Handtekening voorzitter)'),
        ('exform', 'signature_secretary', '(Handtekening secretaris)'),

        ('exam', 'title', 'Examenvragen voor het examenjaar '),
        ('exam', 'title_ep1', 'Antwoorden van het centraal examen '),
        ('exam', 'title_ep2', 'Antwoorden van het herexamen '),
        ('exam', 'title_scoretable_ete', 'Omzettingstabel ETE-examen voor het examenjaar '),
        ('exam', 'title_scoretable_duo', 'Omzettingstabel CVTE-examen voor het examenjaar '),
        ('exam', 'educationtype', 'Onderwijssoort'),
        ('exam', 'examtype', 'Soort examen'),
        ('exam', 'Central_exam', 'Centraal examen'),
        ('exam', 'Re_exam', 'Herexamen'),
        ('exam', 'Re_exam_3rd_period', 'Herexamen 3e tijdvak'),
        ('exam', 'Ce_Re_exam', 'Centraal examen en Herexamen'),
        ('exam', 'subject', 'Vak'),
        ('exam', 'school', 'School'),
        ('exam', 'candidate', 'Kandidaat'),
        ('exam', 'exam_number', 'Examennummer'),
        ('exam', 'version', 'Versie'),
        ('exam', 'number_questions', 'Aantal vragen'),
        ('exam', 'blanks', 'Niet ingevuld'),
        #('exam', 'keys', 'sleutels'),
        #('exam', 'scores', 'scores'),
        ('exam', 'max_score', 'Maximale score'),
        ('exam', 'scalelength', 'Schaallengte'),
        ('exam', 'total_score', 'Behaalde score'),
        ('exam', 'cesuur', 'Cesuur'),
        ('exam', 'n_term', 'N-term'),
        ('exam', 'nex_id', 'nex_ID'),
        ('exam', 'duo_exam', 'CVTE examen'),

        ('ex1', 'title', 'Genummerde alfabetische naamlijst van de kandidaten'),
        # PR2023-08-31 email Esther ETE: chnage to 31 august. was:  ('ex1', 'submit_before', 'Inzenden vóór 1 november *'),
        ('ex1', 'submit_before', 'Inzenden vóór 1 september *'),
        ('ex1', 'footnote01', 'Dit formulier dient tevens voor bestelling schriftelijk werk.'),
        ('ex1', 'footnote02', 'Examennummer: onder dit nummer doet de kandidaat examen.'),
        ('ex1', 'footnote03', 'Vakken waarin geëxamineerd moet worden zijn aangegeven met een cirkel.'),
        ('ex1', 'footnote04', None),
        ('ex1', 'footnote05', None),
        ('ex1', 'footnote06', '*  Het getekend exemplaar en een digitale versie'),
        # PR2023-08-31 email Esther ETE: chnage to 31 august. was:     ('ex1', 'footnote07', '   vóór 1 november inzenden naar de Onderwijs Inspectie'),
        ('ex1', 'footnote07', '   vóór 1 september inzenden naar de Onderwijs Inspectie'),
        ('ex1', 'footnote08', '   en een digitale versie naar het ETE.'),
        # PR2023-08-31 email Esther ETE: chnage to 31 august. was:     ('ex1', 'footnote07', '   vóór 1 november inzenden naar de Onderwijs Inspectie'),
        ('ex1', 'lex_footnote07', '   vóór 1 september inzenden naar de Onderwijs Inspectie.'),
        ('ex1', 'lex_footnote08', None),

        ('ex2', 'ex2_title', 'Verzamellijst van cijfers van schoolexamens'),
        ('ex2', 'ex2_title_exem', 'Verzamellijst van cijfers van vrijstellingen'),
        ('ex2', 'submit_before', 'Inzenden ten minste 3 dagen vóór aanvang van de centrale examens*'),
        ('ex2', 'footnote01', 'Examennummer en naam dienen in overeenstemming te zijn met formulier EX.1'),
        ('ex2', 'footnote02', None),
        # PR2024-06-05 was: ('ex2', 'footnote03', '1) doorhalen hetgeen niet van toepassing is.'),
        ('ex2', 'footnote03', 'Het getekend exemplaar en een digitale versie ten minste 3 dagen'),
        ('ex2', 'footnote04', 'vóór aanvang van de centrale examens inzenden naar de Onderwijs Inspectie'),
        ('ex2', 'footnote05', 'en een digitale versie naar het ETE.'),
        ('ex2', 'footnote06', None),
        ('ex2', 'lex_footnote05', None),

        ('ex2', 'backpage01_eex', 'Digitale handtekening van de examinatoren voor akkoord cijfers schoolonderzoek als aan ommezijde vermeld.'),
        ('ex2', 'backpage01_lex', 'Digitale handtekening van de examinatoren voor akkoord cijfers commissie-examen (CIE) als aan ommezijde vermeld.'),
        ('ex2', 'backpage01_ex2a', 'Digitale handtekening van de examinatoren en gecommitteerden voor akkoord scores als aan ommezijde vermeld.'),
        ('ex2', 'backpage02', 'Ieder voorzover het zijn kandidaten betreft'),

        ('ex2', 'backheader01', 'Naam examinator'),
        ('ex2', 'backheader02', 'Vak'),
        ('ex2', 'backheader03', 'Klas'),
        ('ex2', 'backheader04', 'Cluster'),
        ('ex2', 'backheader05', 'Handtekening'),
        ('ex2', 'backheader01_ex2a', 'Naam gecommitteerde'),

        ('ex2a', 'ex2a_title', 'Verzamellijst van scores van '),
        ('ex2a', 'ex2a_title_tv01', 'centrale examens'),
        ('ex2a', 'ex2a_title_tv02', 'herexamens'),
        ('ex2a', 'ex2a_title_tv03', 'herexamens 3e tijdvak'),
        ('ex2a', 'ex2a_eex_article', '(Artikel 20 Landsbesluit eindexamens v.w.o., h.a.v.o., v.s.b.o., 23 juni 2008, no 54)'),
        ('ex2a', 'ex2a_lex_article', '(Artikel 34 Landsbesluit landsexamens v.w.o., h.a.v.o., v.s.b.o. van 3 mei 2016, no 21)'),

        ('ex3', 'proces_verbaal', 'Proces-verbaal'),
        ('ex3', 'title', 'Proces-verbaal van Toezicht'),
        ('ex3', 'eex_article', '(Artikel 28, Landsbesluit eindexamens v.w.o., h.a.v.o., v.s.b.o., 23 juni 2008, no 54)'),
        ('ex3', 'lex_article', '(Artikel 18, Landsbesluit landsexamens v.w.o., h.a.v.o., v.s.b.o. van 3 mei 2016, no 21)'),
        ('ex3', 'ex_code', 'EX.3'),
        ('ex3', 'eindexamen', 'EINDEXAMEN'),
        ('ex3', 'landsexamen', 'LANDSEXAMEN'),
        ('ex3', 'in_het_examenjaar', 'in het examenjaar'),
        ('ex3', 'voor_het_vak', 'voor het vak:'),
        ('ex3', 'naam_school', 'Naam van de school:'),

        ('ex3', 'col_00_00', 'Examennr.'),
        ('ex3', 'col_00_01', '1)'),
        ('ex3', 'col_01_00', 'Naam en voorletters kandidaat'),
        ('ex3', 'col_01_01', '(in alfabetische volgorde)'),
        ('ex3', 'col_02_00', 'Handtekening kandidaat'),
        ('ex3', 'col_02_01', '(bij aanvang)'),
        ('ex3', 'col_03_00', 'Aantal ingeleverde bladen'),
        ('ex3', 'col_03_01', 'uitwerk-'),
        ('ex3', 'col_03_02', 'bladen'),
        ('ex3', 'col_04_01', 'folio-'),
        ('ex3', 'col_04_02', 'bladen'),
        ('ex3', 'col_05_00', 'Tijdstip van'),
        ('ex3', 'col_05_01', 'inlevering'),
        ('ex3', 'col_06_00', 'Paraaf voor inlevering'),
        ('ex3', 'col_06_01', 'surveillant'),
        ('ex3', 'col_06_02', None),
        ('ex3', 'col_07_01', 'kandidaat'),
        #('ex3', 'col_06_02', '(voor inlevering)'),
        #('ex3', 'col_06_02', '(voor inlevering)'),
        #('ex3', 'col_06_02', '(voor inlevering)'),
        ('ex3', 'footer_01', '1) Examennummer en naam dienen in overeenstemming te zijn met formulier EX.1'),

        ('ex3', 'back_01', 'Verloop en eventuele bijzonderheden van het schriftelijk examen van het vak'),
        ('ex3', 'back_02', 'voor de groep kandidaten als aan ommezijde vermeld.'),
        ('ex3', 'back_03', 'Indien meer dan 2 verschillende personen toezicht hebben gehouden opmerkingen paraferen.'),
        ('ex3', 'back_place', '(plaatsnaam)'),
        ('ex3', 'back_date', '(datum)'),
        ('ex3', 'back_signature', 'Handtekening toezichthouders:'),
        ('ex3', 'back_from', '(Toezicht van'),
        ('ex3', 'back_till', 'uur tot'),
        ('ex3', 'back_hour', 'uur)'),
        ('ex3', 'backfooter_01', 'In elk lokaal dienen twee toezichthouders aanwezig te zijn. Elk moment dient derhalve door 2 handtekeningen gedekt te zijn.'),

        ('ex4', 'ex4_title', 'Lijst van kandidaten voor het herexamen.'),
        ('ex4', 'ex4_title_reex03', 'Lijst van kandidaten voor het herexamen derde tijdvak.'),
       # ('ex4', 'ex4_title_corona', 'Lijst van kandidaten voor herkansing.'),
        ('ex4', 'ex4_eex_article', '(Landsbesluit eindexamens v.w.o., h.a.v.o., v.s.b.o., 23 juni 2008, no 54)'),
        ('ex4', 'ex4_lex_article', '(Landsbesluit landsexamens v.w.o., h.a.v.o., v.s.b.o. van 3 mei 2016, no 21)'),
        ('ex4', 'ex4_tevens_lijst', 'Tevens lijst van kandidaten, die om een geldige reden verhinderd waren het examen te voltooien.'),
        ('ex4', 'ex4_eex_submit', 'Direct na elke uitslag inzenden naar de Onderwijs Inspectie en digitaal naar het ETE.'),
        ('ex4', 'ex4_lex_submit', 'Direct na elke uitslag het ondertekend exemplaar en digitaal inzenden naar de Onderwijs Inspectie.'),
        ('ex4', 'ex4_footer01', 'Dit formulier dient tevens voor bestelling schriftelijk werk.'),
        ('ex4', 'ex4_footer02', 'Examennummer en naam dienen in overeenstemming te zijn met formulier EX.1.'),
        ('ex4', 'ex4_verhinderd_header01', 'Kandidaten die om een geldige reden verhinderd waren het examen te voltooien.'),
        ('ex4', 'ex4_verhinderd_header02', '(Voortzetting schoolexamen aangeven met s en centraal examen met c).'),
        ('ex4', 'ex4_verhinderd_header03', 'Naam en voorletters van de kandidaat'),

        ('ex4', 'bullet_reex_submitted', 'Dit herexamen is al op een eerder Ex4-formulier ingediend.'),
        ('ex4', 'bullet_reex_new', 'Dit is een nieuw herexamen.'),
        ('ex4', 'bullet_reex_deleted', 'Dit herexamen is gewist.'),

        ('ex5', 'ex5_title', 'Verzamellijst van cijfers.'),
        ('ex5', 'eex_inzenden', 'Inzenden binnen één week na de uitslag en na afloop van de herkansing, het ondertekend exemplaar inzenden naar de Onderwijs Inspectie en digitaal naar de Onderwijs Inspectie en het ETE.'),
        ('ex5', 'lex_inzenden', 'Inzenden binnen één week na de uitslag en na afloop van de herkansing, het ondertekend exemplaar en digitaal inzenden naar de Onderwijs Inspectie.'),

        ('ex5', 'geg_kand', 'GEGEVENS OMTRENT DE KANDIDATEN'),
        ('ex5', 'cijf_kand', 'CIJFERS, AAN DE KANDIDATEN TOEGEKEND VOOR:'),
        ('ex5', 'uitslag_ex', 'Uitslag van het examen'),
        ('ex5', 'uitslag_reex', 'Uitslag na tweede tijdvak'),

        ('ex6', 'ex_code', 'EX.6'),
        ('ex6', 'ex6_article_cur_eex', '(Artikel 47 Landsbesluit eindexamens v.w.o., h.a.v.o., v.s.b.o., 23 juni 2008, no 54)'),
        ('ex6', 'ex6_article_cur_lex', '(Artikel 10 Landsbesluit landsexamens v.w.o., h.a.v.o., v.s.b.o. van 3 mei 2016, no 21)'),
        ('ex6', 'ex6_article_sxm_eex', '(Artikel 47 Landsbesluit eindexamens v.w.o., h.a.v.o., v.s.b.o., 23 juni 2008, no 54)'),
        ('ex6', 'ex6_article_sxm_lex', '(Artikel 10 Landsbesluit landsexamens v.w.o., h.a.v.o., v.s.b.o. van 3 mei 2016, no 21)'),

        ('ex6', 'ex6_pex', 'Bewijs van vrijstelling'),
        ('ex6', 'ex6_pok', 'Bewijs van kennis'),
        ('ex6', 'ex6_voorzitter', 'De voorzitter van de examencommissie van'),
        ('ex6', 'ex6_te', 'te'),
        ('ex6', 'ex6_examyear', 'in het examenjaar'),

        ('ex6', 'ex6_belast', 'belast met het afnemen van het'),
        ('ex6', 'ex6_eindexamen', 'eindexamen'),
        ('ex6', 'ex6_landsexamen', 'landsexamen'),
        ('ex6', 'ex6_aan_deze', 'aan deze '),
        ('ex6', 'ex6_bovengenoemde', 'aan de bovengenoemde '),
        ('ex6', 'ex6_instelling', 'instelling'),
        ('ex6', 'ex6_school', 'school'),
        ('ex6', 'ex6_het_eindexamen', ' het eindexamen'),
        ('ex6', 'ex6_het_landsexamen', ' het landsexamen'),
        ('ex6', 'ex6_verklaart_dat', ', verklaart dat'),
        ('ex6', 'ex6_geboren_op', 'geboren op'),

        ('ex6', 'ex6_afgelegd', 'heeft afgelegd, dat'),
        ('ex6', 'ex6_hij', 'hij'),
        ('ex6', 'ex6_zij', 'zij'),
        ('ex6', 'ex6_volgend_jaar', 'in het volgend examenjaar aan deze'),
        ('ex6', 'ex6_geen_examen', 'geen examen behoeft af te leggen'),
        ('ex6', 'ex6_hieronder_vermelde', 'in de hieronder vermelde vakken, dat voor deze vakken de hieronder vermelde cijfers zijn vastgesteld:'),

        ('ex6', 'ex6_commissie', 'Commissie'),

        ('ex6', 'ex6_examen_afgelegd', 'Vakken waarin examen is afgelegd'),
        ('ex6', 'ex6_Cijfers_voor', 'Cijfers voor'),
        ('ex6', 'ex6_Eindcijfers', 'Eindcijfers'),
        ('ex6', 'ex6_Commissie', 'Commissie'),
        ('ex6', 'ex6_School', 'School-'),
        ('ex6', 'ex6_Centraal', 'Centraal'),
        ('ex6', 'ex6_examen', 'examen'),

        ('gradelist', 'preliminary', 'VOORLOPIGE CIJFERLIJST'),

        ('gradelist', 'undersigned', 'De ondergetekenden verklaren dat'),
        ('gradelist', 'born_on', 'geboren op'),
        ('gradelist', 'born_at', 'te'),
        ('gradelist', 'in_the_examyear', 'in het examenjaar'),
        ('gradelist', 'attended_the_exam', 'heeft deelgenomen aan'),
        ('gradelist', 'het_eindexamen', ' het eindexamen'),
        ('gradelist', 'het_landsexamen', ' het landsexamen'),

        ('gradelist', 'conform', 'conform'),
        ('gradelist', 'het_profiel', 'het profiel'),
        #('gradelist', 'de_leerweg', 'de leerweg'),
        ('gradelist', 'leerweg', 'leerweg'),
        ('gradelist', 'de_sector', 'de sector'),
        ('gradelist', 'at_school', 'aan'),
        ('gradelist', 'at_country', 'te'),

# heeft deelgenomen aan het eindexamen text for Curacao
        ('gradelist', 'eex_article01_cur', 'De kandidaat heeft examen afgelegd in de onderstaande vakken volgens de voorschriften gegeven bij en'),
        # standard text
        #('gradelist', 'eex_article02', 'krachtens artikel 32 van de Landsverordening Voortgezet Onderwijs en heeft de hierna vermelde cijfers behaald.'),
        #('gradelist', 'eex_article03', ''),
        # text 2022
            #('gradelist', 'eex_article02_cur', 'krachtens artikel 32 van de Landsverordening Voortgezet Onderwijs en de Tijdelijke regeling afwijking'),
            #('gradelist', 'eex_article03_cur', 'centrale examens v.w.o., h.a.v.o., v.s.b.o. voor het schooljaar 2021-2022 P.B. 2022, no. 53 d.d. 10 juni 2022'),
            #('gradelist', 'eex_article04_cur', 'en heeft de hierna vermelde cijfers behaald.'),

        # text 2023
        ('gradelist', 'eex_article02_cur', 'krachtens artikel 32 van de Landsverordening Voortgezet Onderwijs en heeft de hierna vermelde cijfers behaald.'),
        ('gradelist', 'eex_article03_cur', None),
        ('gradelist', 'eex_article04_cur', None),

# heeft deelgenomen aan het eindexamen text for St Maarten
        ('gradelist', 'eex_article01_sxm','De kandidaat heeft examen afgelegd in de onderstaande vakken volgens de voorschriften gegeven bij en'),
        ('gradelist', 'eex_article02_sxm', 'krachtens artikel 32 van de Landsverordening Voortgezet Onderwijs en heeft de hierna vermelde cijfers behaald.'),
        ('gradelist', 'eex_article03_sxm', None),
        ('gradelist', 'eex_article04_sxm', None),

        ('gradelist', 'col_00_00', 'Vakken waarin examen is afgelegd'),

        ('gradelist', 'col_01_00', 'Cijfers voor'),
        ('gradelist', 'col_01_01_eex', 'School-'),
        ('gradelist', 'col_01_01_lex', 'Commissie-'),
        ('gradelist', 'col_01_02', 'examen'),
        ('gradelist', 'col_02_01', 'Centraal'),
        ('gradelist', 'col_02_02', 'examen'),
        ('gradelist', 'col_03_00', 'Eindcijfers'),
        ('gradelist', 'col_03_01', 'in cijfers'),
        ('gradelist', 'col_04_01', 'in letters'),

        ('gradelist', 'combi_grade', 'Combinatiecijfer, het gemiddelde van de met * gemerkte vakken'),

        ('gradelist', 'pws', 'Profielwerkstuk'),
        ('gradelist', 'sws', 'Sectorwerkstuk'),
        ('gradelist', 'lbl_title_pws', 'Titel/onderwerp van het profielwerkstuk:'),
        ('gradelist', 'lbl_title_sws', 'Titel/onderwerp van het sectorwerkstuk:'),
        ('gradelist', 'lbl_subjects_pws', 'Vakken waarop het profielwerkstuk betrekking heeft:'),
        ('gradelist', 'lbl_subjects_sws', 'Vakken waarop het sectorwerkstuk betrekking heeft:'),

        ('gradelist', 'avg_grade', 'Gemiddelde der cijfers'),
        ('gradelist', 'result', 'Uitslag op grond van de resultaten:'),

        ('gradelist', 'footnote_exem', '(vr):  Vrijstelling   '),
        #  PR2021-04-15 PostCorona: 'Extra vak' verwijderd bij telt niet mee (altijd, niet alleen in 2021)
        ('gradelist', 'footnote_extra_nocount', '+ : Vak telt niet mee voor uitslag   '),
        ('gradelist', 'footnote_extra_counts', '++ :  Extra vak, telt mee voor uitslag'),

        ('gradelist', 'place', 'Plaats:'),
        ('gradelist', 'date', 'Datum:'),

        # PR2023-06-20 was:
        #   ('gradelist', 'chairperson', 'voorzitter'),
        #   ('gradelist', 'secretary', 'secretaris'),
        ('gradelist', 'chairperson', 'Voorzitter Examencommissie'),
        ('gradelist', 'secretary', 'Secretaris Examencommissie'),

        # PR2023-06-20 added:
        ('gradelist', 'reg_nr', 'Registratienr.:'),
        ('gradelist', 'id_nr', 'Id.nr.:'),

        ('diploma', 'born', 'geboren op'),
        ('diploma', 'born_at', 'te'),
        ('diploma', 'attended', 'met gunstig gevolg heeft deelgenomen aan het eindexamen'),
        ('diploma', 'attended_lex', 'met gunstig gevolg heeft deelgenomen aan het landsexamen'),
        ('diploma', 'conform', 'conform'),
        ('diploma', 'conform_sector', 'de sector'),
        ('diploma', 'conform_profiel', 'het profiel'),
        ('diploma', 'at_school', 'aan'),
        ('diploma', 'at_country', 'te'),

        # standard
        ('diploma', 'dpl_article_01', 'welk examen werd afgenomen volgens de voorschriften gegeven bij en krachtens artikel 32 van de'),
        ('diploma', 'dpl_article_02', 'Landsverordening voortgezet onderwijs van de 21ste mei 2008, P.B. no. 33, (P.B. 1979, no 29), zoals gewijzigd.'),

# heeft deelgenomen aan het eindexamen text for Curacao
        # text 2022 curacao
        # ('diploma', 'dpl_article01_cur', 'welk examen werd afgenomen volgens de voorschriften gegeven bij en krachtens artikel 32 van de '),
        # ('diploma', 'dpl_article02_cur', 'Landsverordening voortgezet onderwijs van de 21ste mei 2008, P.B. no. 33, (P.B. 1979, no 29),'),

        # ('diploma', 'dpl_article03_cur', 'zoals gewijzigd en de Tijdelijke regeling afwijking centrale examens v.w.o., h.a.v.o., v.s.b.o.'),
        # ('diploma', 'dpl_article04_cur', 'voor het schooljaar 2021-2022 P.B. 2022, no. 53 d.d. 10 juni 2022.'),

        # text 2023 curacao
        ('diploma', 'dpl_article01_cur', 'welk examen werd afgenomen volgens de voorschriften gegeven bij en krachtens artikel 32 van de'),
        ('diploma', 'dpl_article02_cur', 'Landsverordening voortgezet onderwijs van de 21ste mei 2008, P.B. no. 33, (P.B. 1979, no 29),'),

        ('diploma', 'dpl_article03_cur', 'zoals gewijzigd.'),
        ('diploma', 'dpl_article04_cur', None),

        ('diploma', 'place', 'Plaats:'),
        ('diploma', 'date', 'Datum:'),
        ('diploma', 'chairperson', 'De voorzitter van de examencommissie:'),
        ('diploma', 'secretary', 'De secretaris van de examencommissie:'),

        # PR2023-06-21 changes requested by Esther
        ('diploma', 'chairperson_cur', 'Voorzitter Examencommissie'),
        ('diploma', 'secretary_cur', 'Secretaris Examencommissie'),

        ('diploma', 'ete', 'Het Expertisecentrum voor Toetsen & Examens:'),

        ('diploma', 'signature', 'Handtekening van de geslaagde:'),
        ('diploma', 'reg_nr', 'Registratienr.:'),
        ('diploma', 'id_nr', 'Id.nr.:'),
    ]
    # PR2023-05-03 update both sxm and cur
    examyears = sch_mod.Examyear.objects.filter(
        code=examyear.code
    )
    for ey in examyears:

        for key_value in key_value_list:
            instance = sch_mod.ExfilesText.objects.filter(
                examyear=ey,
                key=key_value[0],
                subkey=key_value[1]).first()
            if instance is None:
                instance = sch_mod.ExfilesText(
                    examyear=examyear,
                    key=key_value[0],
                    subkey=key_value[1],
                    setting=key_value[2]
                )
            else:
                instance.setting = key_value[2]
            instance.save()


def get_library(examyear, key_list):  # PR2021-03-10
    # get text for exform etc from ExfilesText
    return_dict = {}
    # key_list must be list, not tuple
    if examyear and key_list:
        sql_keys = {'ey_id': examyear.pk, 'key_arr': key_list}
        sql = "SELECT eft.subkey, eft.setting FROM schools_exfilestext AS eft " + \
                "WHERE eft.examyear_id = %(ey_id)s::INT AND eft.key IN ( SELECT UNNEST( %(key_arr)s::TEXT[])) ORDER BY eft.subkey"

        with connection.cursor() as cursor:
            cursor.execute(sql, sql_keys)
            for row in cursor.fetchall():
                return_dict[row[0]] = row[1]

    return return_dict
# --- end of get_library

