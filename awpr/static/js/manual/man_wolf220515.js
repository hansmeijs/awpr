// PR2021-07-18 added

    "use strict";

const man_wolf = {

/////////  NEDERLANDS //////////////////////////////
    nl: [
        write_paragraph_header("id_intro", "Wolf"),

        write_paragraph_body("",
            ["<p>De pagina <i>Wolf</i> vervangt het voormalige WOLF programma voor het invoeren van de antwoorden op de examenvragen van de ETE examens. </p>",
                "<p class='pb-0'>Dit heeft een aantal voordelen:</p>",

                "<ul class='manual_bullet mb-0'><li>Gegevens van de kandidaten en hun vakken hoeven niet opnieuw ingevoerd te worden;</li>",
                "<li>Na het indienen van de antwoorden wordt de totaal score automatisch ingevuld bij het betreffende vak van de kandidaat;</li>",
                "<li>Het ETE hoeft de ingevulde examens van de scholen niet te verzamelen en samen te voegen.</li></ul>",

                 "<p class='pb-0 pt-2'>De <b>procedure voor het invoeren van de antwoorden en het indienen</b> bij het ETE is als volgt:</p>",
                "<ul class='manual_bullet mb-0'><li>Het ETE voert de algemene gegevens van de examens in: de naam, het aantal vragen, welke vragen meerkeuzevraag zijn en welke antwoorden zijn toegestaan;</li>",
                "<li>Zodra het ETE dit heeft afgerond worden de examens 'gepubliceerd', dat wil zeggen: ze worden zichtbaar voor de scholen. AWP koppelt waar mogelijk het examen aan de vakken van de kandidaten. ",
                "Alleen wanneer bij een vak meerdere examens beschikbaar zijn, dient de school het juiste examen te kiezen. ",
                "Dit is het geval bij de praktijkexamens, die meerdere versies hebben;</li>",
                "<li>De school vult alle antwoorden van de vragen in. AWP controleert of het ingevulde antwoord is toegestaan;</li>",

                "<li>Nadat de antwoorden van alle examens zijn ingevoerd, dienen ze te worden goedgekeurd door de voorzitter, secretaris en examinator ",
                "en ingediend door de voorzitter of secretaris;</li>",
                "<li>Na het indienen van de antwoorden vult AWP de totaal score in bij het betreffende vak van de kandidaat.</li></ul>",

                "<p>De pagina <i>Wolf</i> bevat een tabel met alle kandidaten, hun vakken en het bijbehorende examen. ",
                "In deze pagina kun je examens aan vakken koppelen, de antwoorden invullen, de antwoorden downloaden en de examens goedkeuren en indienen.</p>",

                "<p>Klik in de paginabalk op de knop <i>Wolf</i>. De onderstaande pagina <i>Wolf</i> wordt nu geopend.</p>",
                "<p>In de kolom <i>Examen</i> staat de naam van het examen.<br>",
                "In de kolom <i>Niet ingevuld</i> staat het aantal vragen dat de school nog moet invullen en het totaal aantal vragen.<br>",
                "Klik op <i>PDF downloaden</i> om een overzicht te downloaden van de ingevulde antwoorden.</p>",

                "<p class='pb-0'>De tabel bevat ondere andere de volgende kolommen:</p>",
                "<ul class='manual_bullet'><li>De kolom <b>Kandidaat</b>. Klik hierop om het invoervenster van de antwoorden te openen.</li>",
                "<li>In de kolom <b>Examen</b> staat de naam van het examen. Klik hierop om een examen te selecteren of te verwijderen.</li> ",
                "<li>In de kolom <b>Niet ingevuld</b> staat het aantal vragen dat de school nog moet invullen en het totaal aantal vragen. ",
                "Als het veld leeg is betekent dit dat alle vragen zijn ingevuld of dat er geen examen is geselecteerd.</li> ",
                "<li>De kolom <b>Score</b> bevat de behaalde score. Dit veld is leeg als niet alle vragen zijn ingevuld.</li> ",
                "<li>De kolom <b>PDF downloaden</b>. Klik hierop om een overzicht te downloaden van de ingevulde antwoorden.</li></ul> ",

            ]),
        write_image("img_exams_table_ne"),

        write_paragraph_header("id_link_exams", "Examen koppelen aan een vak"),
        write_paragraph_body("",
            ["<p>Zodra het ETE de examens heeft gepubliceerd koppelt AWP waar mogelijk het bijbehorende examen aan de vakken van de kandidaten. ",
                "Alleen wanneer bij een vak meerdere examens beschikbaar zijn, dient de school het juiste examen te kiezen. ",
                "Dit is het geval bij de praktijkexamens, die meerdere versies hebben.</p>",
                "<p><b>Examen selecteren</b><br>Klik in de kolom <i>Examen</i> van het betreffende vak van de kandidaat. Er verschijnt een venster met een of meerdere examens. Selecteer een examen en klik op <i>OK</i>. ",
                "Wanneer bij een vak (nog) geen examens beschikbaar zijn, verschijnt de melding 'Er zijn nog geen examens voor dit vak.'.</p>",

                "<p><b>Examen verwijderen</b><br>Als een kandidaat niet aan het examen heeft deelgenomen kun je het examen verwijderen. ",
                "Klik op het examen van het betreffende vak van de kandidaat. Klik in het venster dat verschijnt op <i>Examen verwijderen</i>.</p>",
            ]),
        write_image("img_exams_select_exam_ne"),

        write_paragraph_header("id_enter_exams", "Antwoorden invoeren"),
        write_paragraph_body("",
            ["<p>Klik op de naam van de kandidaat of op de naam van het vak om het venster te openen waarmee je de antwoorden van de kandidaat kunt invoeren. ",
                "Het onderstaande venster verschijnt.</p>"
            ]),
        write_image("img_exams_answers_ne"),
        write_paragraph_body("",
            [ "<p>Boven in het venster staan de naam van het examen, het vak en de kandidaat.<br> ",
                "Wanneer een examen uit meerdere deelexamens bestaat is er links een kader met de deelexamens. ",
                "Selecteer een deelexamen om de antwoorden van dat deelexamen in te vullen. ",
                "Bij examens zonder deelexamen is dit kader niet zichtbaar.</p>",
                "<p>Rechts staan de nummers van de vragen met een kader voor het antwoord. ",
                "Bij een meerkeuzevraag staat er een asterisk (*) achter de vraaag.<br>",
                "Wanneer een examen meer dan 50 vragen heeft worden de vragen over twee pagina's verdeeld. ",
                "Links onderin het venster staan dan knoppen waarmee je naar een andere pagina kunt gaan.</p>",

                "<p class='pb-0'><b>Antwoorden invullen</b><br>Vul het antwoord van de vraag in. Bij een open vraag vul je de behaalde score in, bij een meerkeuzevraag een letter. ",
                "Vul een 'x' in als de kandidaat een vraag niet heeft beantwoord of bij een meerkeuzevraag meerdere antwoorden heeft ingevuld. Alle vragen moeten worden ingevuld.</p>",
                "<p class='pb-0'>Wanneer je een antwoord invult dat niet mogelijk is, verschijnt er een venster. Hierin staat welke antwoorden zijn toegestaan.</p>",

                "<p>Het invoeren gaat het snelste, wanneer je na het intypen van het antwoord op de ENTER toets klikt. Je gaat dan meteen naar de volgende vraag. ",
                "Klik op een toetsen met een pijltje om naar een volgende of vorige vraag, of naar een vraag in de volgende of vorige kolom te gaan.</p>",

                "<p><b>Opslaan</b><br>De ingevulde antwoorden worden pas opgeslagen als je op de knop <i>Opslaan</i> klikt. ",
                "Vergeet daarom niet op de knop <i>Opslaan</i> te klikken als je de antwoorden hebt ingevoerd.</p>",
                "<p class='pb-0'>In de kolom <i>Niet ingevuld</i> kunt je zien hoeveel vragen er nog ingevuld moeten worden. ",
                "2/39 betekent dat 2 van de 39 vragen nog niet zijn ingevuld. Als alle vragen zijn ingevuld blijft deze kolom leeg.</p>",
            ]),

        write_paragraph_header("id_download_exams", "Overzicht met antwoorden downloaden"),
        write_paragraph_body("",
            ["<p>Klik op <i>PDF downloaden</i> om een overzicht van de ingevulde antwoorden te downloaden. Zie het voorbeeld hieronder.<br>",
                "In het kader bovenaan de pagina staan de gegevens van het examen, het vak en de kandidaat. Als alle vragen zijn ingevuld geeft AWP de behaalde totaal score weer.<br>",
                "Als niet alle vargen zijn ingevuld staat er hoeveel vragen niet zijn ingevuld. ",
                "Dit is het aantal vragen <span class='man_underline'>dat de school nog moet invullen</span>, dus niet het aantal vragen dat de kandidaat niet heeft ingevuld.<br>",
                "Daaronder staan de nummers van de vragen, de ingevulde antwoorden en de behaalde score.<br>",
                "Onderaan de pagina staat de naam van de gebruiker, die het laatst gegevens heeft ingevoerd en de datum van de laatste invoer.</p>",
            ]),
        write_paragraph_body("img_exclamationsign",
            ["<p>Print dit overzicht alleen als het echt nodig is. Als je alles uitprint gaat het al gauw om een paar honderd pagina's. Dat is slecht voor het milieu en slecht voor het budget van de school. De  informatie is ook te lezen vanaf het scherm.</p>",
            ]),
        write_image("img_exams_result_ne"),

        write_paragraph_header("id_submit_exams", "Examens goedkeuren en indienen"),
        write_paragraph_body("",
            [
            "<p>Nadat de antwoorden van alle examens zijn ingevoerd, dienen ze te worden goedgekeurd door de voorzitter, secretaris en examinator en ingediend door de voorzitter of secretaris. ",
               "Klik <a href='#' class='awp_href' onclick='LoadPage(&#39approve&#39)'>hier</a> voor een gedetailleerde beschijving van deze procedure.</p>",

                "<p class='mb-0 pb-0'>Het indienen van de examens gaat in twee stappen:</p>",
                "<ul class='manual_bullet'><li>De eerste stap is het <b>goedkeuren</b> van de examens door de voorzitter, secretaris en examinator.</li>",
                "<li>De tweede stap is het <b>indienen</b> van het Ex-formulier door de voorzitter of secretaris.</li></ul>",

                "<p><b>Goedkeuren</b><br>",
                "De voorzitter, secretaris en examinator moeten de examens goedkeuren.</p>",
                "<p>Klik in de menubalk op <i>Examens goedkeuren</i>. Het venster <i>Examens goedkeuren</i> verschijnt. ",
                "AWP controleert eerst de ingevulde gegevens en geeft een melding wanneer niet alle antwoorden zijn ingevuld. ",
                "Klik op <i>Examens goedkeuren</i> om de examens goed te keuren. Het icoontje achter de goedgekeurde examens wordt nu half zwart. ",
                "Ververs het scherm wanneer de goedkeuringen niet meteen zichtbaar zijn.</p>",
                "<p>Het goedkeuren van examens kan in gedeeltes plaatsvinden. Selecteer een vak of cluster in de verticale grijze balk links in het scherm. Nu worden alleen de geselecteerde examens goedgekeurd.</p>",
                "<p>Je kunt ook individuele examens goedkeuren of de goedkeuring van individuele examens verwijderen. Klik op het icoontje naast het examen om het goed te keuren of de goedkeuring te verzijderen.</p>",

                "<p><b>Indienen</b><br>Klik in de menubalk op <i>Examens indienen</i>. Het venster <i>Examens indienen</i> verschijnt. ",
                "AWP controleert eerst de ingevulde gegevens en geeft een melding wanneer niet alle examens kunnen worden ingediend.</p> ",
                "<p>Klik op <i>Verificatiecode aanvragen</i>. AWP stuurt nu een e-mail met een verificatiecode naar het e-mail adres van de gebruiker.",
                "Vul de verificatiecode in en klik op ENTER. De examens worden nu ingediend. Het icoontje naast de examens wordt nu blauw.</p>",
            ]),

        write_paragraph_header("id_practical_exams", "Praktijkexamens"),
        write_paragraph_body("",
            ["<p><b>Deelexamens</b><br>In 2022 is de nieuwe examinering van de praktijkexamens ingevoerd. ",
                "Het afzonderlijke praktijkexamen en centraal examen zijn nu samengevoegd tot een praktijkexamen dat uit verschillende onderdelen bestaat: de praktijktoetsen en de theoretische 'minitoetsen'. ",
                "Deze toetsen zijn als deelexamens opgenomen.</p>",
            ]),
        write_paragraph_body("img_exclamationsign",
            ["<p><b>LET OP</b>: Elke kandidaat dient steeds de deelexamens van dezelfde versie af te leggen, dus alleen deelexamens 'Versie BLAUW' of alleen 'Versie ROOD'. ",
            "Wanneer een kandidaat voor een deel 'Versie BLAUW' en voor een deel 'Versie ROOD' heeft afgelegd kan de score niet correct berekend worden.</p>",
            ]),

        "<div class='p-3 visibility_hide'>-</div>",
    ],

    en:  [
        write_paragraph_header("id_intro", "Wolf"),

        write_paragraph_body("",
            ["<p>The 'Exams' page replaces the former WOLF program for entering the answers to the exam questions of the ETE exams. </p>",
                "<p class='pb-0'>This has several advantages:</p>",
                "<ul class='manual_bullet mb-0'><li>Data of the candidates and their subjects do not need to be re-entered;</li>",
                "<li>After submitting the answers, the total score is automatically entered in the relevant subject of the candidate;</li>",
                "<li>The ETE does not have to collect and merge the completed exams from the schools.</li></ul>",

                 "<p class='pb-0 pt-2'>The <b>procedure for entering the answers and submitting them</b> to the ETE is as follows:</p>",
                "<ul class='manual_bullet mb-0'><li>The ETE enters the general data of the exams: the name, the number of questions, which questions are multiple choice and which answers are allowed;</li>",
                "<li>As soon as the ETE has completed this, the exams are 'published', i.e. they become visible to the schools. Where possible, AWP links the exam to the subjects of the candidates. ",
                "The school should only choose the correct exam if several exams are available for a subject. ",
                "This is the case with the practical exams, which have multiple versions;</li>",
                "<li>The school fills in all the answers of the questions. AWP checks whether the entered answer is allowed;</li>",
                "<li>After the answers of all exams have been entered, they must be approved by the chairperson, secretary and examiner ",
                 "and submitted by the chairperson or secretary;</li>",
                "<li>After submitting the answers, AWP fills in the total score for the relevant subject of the candidate.</li></ul>",

                "<p>The <i>Exams</i> page contains a table with all candidates, their subjects and the corresponding exam. ",
                "In this page you can link exams to subjects, fill in the answers, download the answers and approve and submit the exams.</p>",

                "<p>Click the <i>Exams</i> button in the page bar. The <i>Exams</i> page below will now open.</p>",
                "<p>The <i>Exam</i> column contains the name of the exam.<br>",
                "The column <i>Blanks</i> shows the number of questions that the school still needs to fill in and the total number of questions.<br>",
                "Click on <i>Download PDF</i> to download an overview of the completed answers.</p>",

                "<p class='pb-0'>The table contains, among others, the following columns:</p>",
                "<ul class='manual_bullet'><li>The column <b>Candidate</b>. Click this to open the answer input window.</li>",
                "<li>The <b>Exam</b> column contains the name of the exam. Click to select or delete an exam.</li> ",
                "<li>In the column <b>Blanks</b> is the number of questions that the school still needs to fill in and the total number of questions. ",
                "If the field is empty, it means that all questions have been completed or no exam has been selected.</li> ",
                "<li>The <b>Score</b> column contains the obtained score. This field is empty if not all questions are filled in.</li> ",
                "<li>The column <b>Download PDF</b>. Click here to download an overview of the completed answers.</li></ul> ",
            ]),
        write_image("img_exams_table_en"),

        write_paragraph_header("id_link_exams", "Link exam to a subject"),
        write_paragraph_body("",
            ["<p>Once the ETE has published the exams, AWP will link the corresponding exam to the candidates' subjects where possible. ",
                "The school should only choose the correct exam if several exams are available for a subject. ",
                "This is the case with the practical exams, which have multiple versions.</p>",
                "<p><b>Select exam</b><br>Click in the column <i>Exam</i> of the relevant subject of the candidate. A window with one or more exams appears. Select an exam and click <i>OK</i>. ",
                "If no exams are (yet) available for a subject, the message 'There are no exams for this subject yet.'.</p>",

                "<p><b>Delete exam</b><br>If a candidate has not taken the exam, you can delete the exam. ",
                "Click on the exam of the candidate's subject. In the window that appears, click on <i>Delete exam</i>.</p>",
            ]),
        write_image("img_exams_select_exam_en"),

        write_paragraph_header("id_enter_exams", "Enter answers"),
        write_paragraph_body("",
            ["<p>Click on the candidate's name or the name of the subject to open the window where you can enter the candidate's answers.",
                "The window below will appear.</p>"
            ]),
        write_image("img_exams_answers_en"),

        write_paragraph_body("",
            [ "<p>At the top of the window is the name of the exam, subject and candidate.<br>",
                "When an exam consists of several partial exams, there is a box on the left with the partial exams. ",
                "Select a partial exam to fill in the answers of that partial exam. ",
                "This frame is not visible for exams without partial exams.</p>",
                "<p>On the right are the numbers of the questions with a box in front of the answer. ",
                "For a multiple choice question, there is an asterisk (*) after the question.<br>",
                "When an exam has more than 50 questions, the questions are split over two pages. ",
                "At the bottom left of the window there are buttons with which you can go to another page.</p>",

                "<p class='pb-0'><b>Fill in answers</b><br>Enter the answer of the question. For an open question, enter the score obtained, for a multiple choice question a letter. ",
                "Enter an 'x' if the candidate has not answered a question or has entered multiple answers for a multiple choice question. All questions must be completed.</p>",
                "<p class='pb-0'>If you enter an answer that is not possible, a window will appear. This shows which answers are allowed.</p>",

                "<p>Entering is fastest if you click on the ENTER key after typing in the answer. You then go directly to the next question. ",
                "Click on a button with an arrow to go to the next or previous question, or to a question in the next or previous column.</p>",

                "<p><b>Save</b><br>The entered answers will not be saved until you click the <i>Save</i> button. ",
                "So don't forget to click the <i>Save</i> button when you have entered the answers.</p>",
                "<p class='pb-0'>In the column <i>Blanks</i> you can see how many questions still need to be filled in. ",
                "2/39 means that 2 of the 39 questions have not yet been completed. When all questions have been filled in, this column remains empty.</p>",
            ]),

        write_paragraph_header("id_download_exams", "Download overview of answers"),
        write_paragraph_body("",
            ["<p>Click on <i>Download PDF</i> to download an overview of the completed answers. See the example below.<br>",
                "The frame at the top of the page lists the details of the exam, the subject and the candidate. ",
                "When all questions have been completed, AWP displays the total score obtained.<br>",
                "If not all questions have been filled in, it will show how many questions have not been filled in. ",
                "This is the number of questions <span class='man_underline'>the school has yet to complete</span>, not the number of questions the candidate has not completed.<br>",
                "Below are the numbers of the questions, the completed answers and the score obtained.<br>",
                "At the bottom of the page is the name of the user who last entered data and the date of the last entry.</p>",
            ]),

        write_paragraph_body("img_exclamationsign",
            ["<p>Print this overview only if it is really necessary. If you print everything it will easily be a few hundred pages. ",
                "That is bad for the environment and bad for the school's budget. The information can also be read from the screen.</p>",
            ]),
        write_image("img_exams_result_en"),

        write_paragraph_header("id_submit_exams", "Approve and submit exams"),
        write_paragraph_body("",
            [

            "<p>After the answers of all exams have been entered, they must be approved by the chairperson, secretary and examiner and submitted by the chairperson or secretary. ",
               "Click <a href='#' class='awp_href' onclick='LoadPage(&#39approve&#39)'>here</a> for a detailed description of this procedure.</p>",

                "<p class='mb-0 pb-0'>Submission of the exams is done in two steps:</p>",
                "<ul class='manual_bullet'><li>The first step is to <b>approve</b> the exams by the chairperson, secretary and examiner.</li>",
                "<li>The second step is the <b>submission</b> of the Ex-form by the chairperson or secretary.</li></ul>",

                "<p><b>Approve</b><br>",
                "The chairperson, secretary and examiner must approve the exams.</p>",
                "<p>Click <i>Approve Exams</i> in the menu bar. The <i>Approve Exams</i> window appears. ",
                "AWP first checks the entered data and notifies you when not all answers have been entered.",
                "Click on <i>Approve exams</i> to approve the exams. The icon behind the approved exams will now turn half black. ",
                "Refresh the screen if the approvals are not immediately visible.</p>",
                "<p>The approval of exams can be done in parts. Select a subject or cluster in the vertical gray bar on the left of the screen. Now only the selected exams will be approved.</p>",
                "<p>You can also approve individual exams or remove the approval of individual exams. Click on the icon next to the exam to approve or cancel the approval.</p>",

                "<p><b>Submit</b><br>Click <i>Submit Exams</i> in the menu bar. The <i>Submit Exams</i> window appears. ",
                "AWP first checks the entered data and notifies you when not all exams can be submitted.</p> ",
                "<p>Click <i>Request Verification Code</i>. AWP will now send an email with a verification code to the user's email address.",
                "Enter the verification code and click ENTER. The exams will now be submitted. The icon next to the exams will now turn blue.</p>",
            ]),

        write_paragraph_header("id_practical_exams", "Practical exams"),
        write_paragraph_body("",
             ["<p><b>Partial exams</b><br>In 2022, the new examination of the practical exams has been introduced. ",
                 "The separate practical exam and central exam have now been merged into a practical exam that consists of different parts: the practical tests and the theoretical 'mini tests'.",
                 "These tests are included as partial exams.</p>",
            ]),
        write_paragraph_body("img_exclamationsign",
             ["<p><b>ATTENTION</b>: Each candidate must always take the partial exams of the same version, so only partial exams 'BLUE version' or only 'RED version'. ",
             "If a candidate has completed part 'BLUE version' and part 'Red version', the score cannot be calculated correctly.</p>",
            ]),

        "<div class='p-3 visibility_hide'>-</div>",

    ]
}
