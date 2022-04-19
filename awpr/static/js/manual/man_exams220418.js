// PR2021-07-18 added

    "use strict";

const man_exams = {

/////////  NEDERLANDS //////////////////////////////
    nl: [
        write_paragraph_header("id_intro_exams", "Examens (voormalige WOLF programma)"),
        write_paragraph_body("",
            [
                "<p>De pagina 'Examens' vervangt het voormalige WOLF programma voor het invoeren van de antwoorden op de examenvragen van de ETE examens. </p>",
                "<p class='pb-0'>Dit heeft een aantal voordelen:</p>",
                "<ul class='manual_bullet mb-0'><li>Gegevens van de kandidaten en hun vakken hoeven niet opnieuw ingevoerd te worden;</li>",
                "<li>Na het indienen van de antwoorden wordt de totaal score automatisch ingevuld bij het betreffende vak van de kandidaat;</li>",
                "<li>Het ETE hoeft de ingevulde examens van de scholen niet te verzamelen en samen te voegen.</li></ul>",

                 "<p class='pb-0 pt-2'>De <b>procedure voor het invoeren van de antwoorden en het indienen</b> bij het ETE is als volgt:</p>",
                "<ul class='manual_bullet mb-0'><li>Het ETE voert de algemene gegevens van de examens in: de naam, het aantal vragen, welke vragen meerkeuzevraag zijn en welke antwoorden zijn toegestaan;</li>",
                "<li>Zodra het ETE dit heeft afgerond worden de examens 'gepubliceerd', dat wil zeggen: ze worden zichtbaar voor de scholen. AWP koppelt waar mogelijk het examen aan de vakken van de kandidaten. Alleen wanneer bij een vak meerdere examens beschikbaar zijn, dient de school het juiste examen te kiezen;</li>",
                "<li>De school vult alle antwoorden van de vragen in. AWP controleert of het ingevulde antwoord is toegestaan;</li>",
                "<li>Nadat de antwoorden van alle examens zijn ingevoerd, dienen ze te worden goedgekeurd en ingediend. De procedure hiervoor is hetzelfde als bij het indienen van het Ex1- en Ex2-formulier;</li>",
                "<li>Na het indienen van de antwoorden vult AWP de totaal score in bij het betreffende vak van de kandidaat.</li></ul>",

                "<p>De pagina <i>Examens</i> bevat een tabel met alle kandidaten, hun vakken en het bijbehorende examen. ",
                "In deze pagina kun je examens aan vakken koppelen, de antwoorden invullen, de antwoorden downloaden en de examens goedkeuren en indienen.</p>",

                "<p>Klik in de paginabalk op de knop <i>Examens</i>. De onderstaande pagina <i>Examens</i> wordt nu geopend.</p>",
                "<p>In de kolom <i>Examen</i> staat de naam van het examen.<br>",
                "In de kolom <i>Niet ingevuld</i> staat het aantal vragen dat de school nog moet invullen en het totaal aantal vragen.<br>",
                "Klik op <i>PDF downloaden</i> om een overzicht te downloaden van de ingevulde antwoorden.</p>",

                "<p><b>Filteren</b><br>Op elke regel in de tabel staat een vak van een kandidaat. ",
                "Je kunt alle examens van alle kandidaten weergeven, maar dat is niet handig. ",
                "Het maakt de pagina onoverzichtelijk en bij veel kandidaten ook traag. Beter is het om examens te filteren.</p>",

                "<p class='pb-0'>Het filteren kan op verschillende manieren:</p>",
                "<ul class='manual_bullet mb-0'><li>In de verticale grijze filterbalk links kun je ",
                "een <b>soort examen</b>, <b>leerweg</b>, <b>vak</b>, <b>cluster</b> of <b>kandidaat</b> selecteren; ",
                "alleen de gegevens die voldoen aan de filter criteria worden gedownload van de server. ",
                "Klik op <i>Alles weergeven</i> onderaan de grijze verticale balk om het filter te wissen en alle gegevens tedownloaden.",
                "</li>",
                "<li>Tenslotte kun je alle kolommen filteren met behulp van de <b>filterregel</b>. ",
                "Klik <a href='#' class='awp_href' onclick='LoadPage(&#39home&#39, &#39id_filterrow&#39)'>hier</a> om naar de handleiding hiervan te gaan;</li>",

                "Klik op de ESCAPE toets om dit filter te wissen.</li></ul>",
            ]),
        write_image("img_exams_tableA_ne"),

        write_paragraph_header("id_link_exams", "Examen koppelen aan een vak"),
        write_paragraph_body("",
            [
                "<p>Zodra het ETE de examens heeft gepubliceerd koppelt AWP waar mogelijk het bijbehorende examen aan de vakken van de kandidaten. ",
                "Alleen wanneer bij een vak meerdere examens beschikbaar zijn, dient de school het juiste examen te kiezen.</p>",

                "<p>Klik in de kolom 'Examen' van het betreffende vak van de kandidaat. Er verschijnt een venster met een of meerdere examens. Selecteer een examen en klik op <i>OK</i>. ",
                "Wanneer bij een vak (nog) geen examens beschikbaar zijn, verschijnt de melding'Er zijn nog geen examens voor dit vak.'.</p>",

                "<p><b>Examen verwijderen</b><br>Als een kandidaat niet aan het examen heeft deelgenomen kun je het examen verwijderen. ",
                "Klik op het examen van het betreffende vak van de kandidaat. Klik in het venster dat verschijnt op <i>Examen verwijderen</i>.</p>",
            ]),

        write_paragraph_header("id_enter_exams", "Antwoorden invoeren"),
        write_paragraph_body("",
            [
                "<p><b>Het venster met antwoorden openen</b><br>Klik op de naam van de kandidaat of op de naam van het vak om het venster te openen waarmee je de antwoorden van de kandidaat kunt invoeren. ",
                "Het onderstaande  venster verschijnt.</p>",

                "<p>Boven in het venster staan de naam van het examen, het vak en de kandidaat. ",
                "Daaronder staan de nummers van de vragen met een kader voor het antwoord. Bij een meerkeuzevraag staat er een asterisk (*) achter de vraaag.<br>",
                "Wanneer een examen meer dan 50 vragen heeft worden de vragen over twee pagina's verdeeld. Links onderin het venster staan dan knoppen waarmee je naar een andere pagina kunt gaan.</p>",

                "<p class='pb-0'><b>Antwoorden invullen</b><br>Vul het antwoord van de vraag in. Bij een open vraag vul je de behaalde score in, bij een meerkeuzevraag een letter. ",
                "Vul een 'x' in als de kandidaat een vraag niet heeft beantwoord of bij een meerkeuzevraag meerdere antwoorden heeft ingevuld. Alle vragen moeten worden ingevuld.</p>",
                "<p class='pb-0'>Wanneer je een antwoord invult dat niet mogelijk is, verschijnt er een venster. Hierin staat welke antwoorden zijn toegestaan.</p>",

                "<p>Het invoeren gaat het snelste, wanneer je na het intypen van het antwoord op de ENTER toets klikt. Je gaat dan meteen naar de volgende vraag. ",
                "Klik op een toetsen met een pijltje om naar een volgende of vorige vraag, of naar een vraag in de volgende of vorige kolom te gaan.</p>",

                "<p><b>Opslaan</b><br>De ingevulde antwoorden worden pas opgeslagen als je op de knop <i>Opslaan</i> klikt .",
                "Vergeet daarom niet op de knop <i>Opslaan</i> te klikken als je de antwoorden hebt ingevoerd.</p>",
                "<p class='pb-0'>In de kolom <i>Niet ingevuld</i> kunt je zien hoeveel vragen er nog ingevuld moeten worden. 49/58 betekent dat 49 van de 58 vragen nog niet zijn ingevuld. Als alle vragen zijn ingevuld blijft deze kolom leeg.</p>",
            ]),
        write_image("img_exams_modA_ne"),

        write_paragraph_header("id_download_exams", "Antwoorden downloaden"),
        write_paragraph_body("",
            [
                "<p>Klik op <i>PDF downloaden</i> om een overzicht van de ingevulde antwoorden te downloaden. Zie het voorbeeld hieronder.<br>",
                "In het kader bovenaan de pagina staan de gegevens van het examen, het vak en de kandidaat. Als alle vragen zijn ingevuld geeft AWP de behaalde totaal score weer.<br>",
                "In het kader daaronder staat hoeveel vragen niet zijnn ingevuld. Dit is het aantal vragen dat de school nog moet invullen, dus niet het aantal vragen dat de kandidaat niet heeft ingevuld.<br>",
                "Daaronder staan de vragen en de ingevulde antwoorden. Onderaan de pagina staat de naam van de gebruiker, die het laatst gegevens heeft ingevoerd en de datum van de laatste invoer.</p>",
            ]),
        write_paragraph_body("img_exclamationsign",
            [
                "<p>Print dit overzicht alleen als het echt nodig is. Als je alles uitprint gaat het al gauw om een paar honderd pagina's. Dat is slecht voor het milieu en slecht voor het budget van de school. De  informatie is ook te lezen vanaf het scherm.</p>",
            ]),
        write_image("img_exams_print_result_ne_en"),

        write_paragraph_header("id_submit_exams", "Examens goedkeuren en indienen"),
        write_paragraph_body("",
            [
                "<p>Nadat de antwoorden van alle examens zijn ingevoerd, dienen ze te worden goedgekeurd en ingediend. De procedure hiervoor is hetzelfde als bij het indienen van het Ex1- en Ex2-formulier. ",
               "Klik <a href='#' class='awp_href' onclick='LoadPage(&#39approve&#39)'>hier</a> voor een gedetailleerde beschijving van deze procedure.</p>",

                "<p class='mb-0 pb-0'>Het indienen van de examens gaat in twee stappen:</p>",
                "<ul class='manual_bullet'><li>De eerste stap is het <b>goedkeuren</b> van de examens door de voorzitter en secretaris.</li>",
                "<li>De tweede stap is het <b>indienen</b> van het Ex-formulier door de voorzitter of secretaris.</li></ul>",


                "<p><b>Goedkeuren</b><br>Klik in de menubalk op <i>Examens goedkeuren</i>. Het venster <i>Examens goedkeuren</i> verschijnt. ",
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
                "<p><b>Antwoorden invoeren</b><br>Selecteer eerst een deelexamen. Het invoeren van de antwoorden van de deelexamens gaat op dezelfde manier als bij de gewone examens.</p>",
            ]),

        "<div class='p-3 visibility_hide'>-</div>",

    ],

    en:  [

        write_paragraph_header("id_intro_exams", "Exams (former WOLF program)"),
        write_paragraph_body("",
            [
                "<p>The 'Exams' page replaces the former WOLF program for entering the answers to the exam questions of the ETE exams. </p>",
                "<p class='pb-0'>This has several advantages:</p>",
                "<ul class='manual_bullet mb-0'><li>Data of the candidates and their courses do not need to be re-entered;</li>",
                "<li>After submitting the answers, the total score is automatically entered in the relevant course of the candidate;</li>",
                "<li>The ETE does not have to collect and merge the completed exams from the schools.</li></ul>",

                 "<p class='pb-0 pt-2'>The <b>procedure for entering the answers and submitting them</b> to the ETE is as follows:</p>",
                "<ul class='manual_bullet mb-0'><li>The ETE enters the general data of the exams: the name, the number of questions, which questions are multiple choice and which answers are allowed;</li>",
                "<li>As soon as the ETE has completed this, the exams are 'published', i.e. they become visible to the schools. Where possible, AWP links the exam to the subjects of the candidates. Only if several exams are available for a subject , the school should choose the correct exam;</li>",
                "<li>The school fills in all the answers of the questions. AWP checks whether the entered answer is allowed;</li>",
                "<li>After the answers of all exams have been entered, they must be approved and submitted. The procedure for this is the same as for submitting the Ex1 and Ex2 form;</li>",
                "<li>After submitting the answers, AWP fills in the total score for the relevant subject of the candidate.</li></ul>",

                "<p>The <i>Exams</i> page contains a table with all candidates, their subjects and the corresponding exam. ",
                "In this page you can link exams to courses, fill in the answers, download the answers and approve and submit the exams.</p>",

                "<p>Click the <i>Exams</i> button in the page bar. The <i>Exams</i> page below will now open.</p>",
                "<p>The <i>Exam</i> column contains the name of the exam.<br>",
                "The column <i>Not filled in</i> shows the number of questions that the school still needs to fill in and the total number of questions.<br>",
                "Click on <i>Download PDF</i> to download an overview of the completed answers.</p>",

                "<p><b>Filter</b><br>Each line in the table shows a candidate's course. ",
                "You can display all exams of all candidates, but that is not convenient. ",
                "It makes the page cluttered and for many candidates also slow. It is better to filter exams.</p>",

                "<p class='pb-0'>The filtering can be done in several ways:</p>",
                "<ul class='manual_bullet mb-0'><li>In the vertical gray filter bar on the left you can ",
                "select a <b>type of exam</b>, <b>learning path</b>, <b>subject</b>, <b>cluster</b> or <b>candidate</b>; " ,
                "only the data that meets the filter criteria will be downloaded from the server.",
                "Click <i>Show All</i> at the bottom of the gray vertical bar to clear the filter and download all data.",
                "</li>",
                "<li>Finally, you can filter all columns using the <b>filter rule</b>. ",
                "Click <a href='#' class='awp_href' onclick='LoadPage(&#39home&#39, &#39id_filterrow&#39)'>here</a> to go to the manual for this;</li> ",

                "Click the ESCAPE button to clear this filter.</li></ul>",
            ]),
        write_image("img_exams_tableA_en"),

        write_paragraph_header("id_link_exams", "Link exam to a course"),
        write_paragraph_body("",
            [
                "<p>As soon as the ETE has published the exams, AWP will link the corresponding exam to the subjects of the candidates where possible.",
                "The school should only choose the correct exam if several exams are available for a subject. </p>",

                "<p>Click in the column 'Exam' of the relevant subject of the candidate. A window with one or more exams will appear. Select an exam and click on <i>OK</i>. ",
                "If no exams are (yet) available for a subject, the message 'There are no exams for this subject yet.'.</p>",

                "<p><b>Delete exam</b><br>If a candidate has not taken the exam, you can delete the exam. ",
                "Click on the exam of the candidate's subject. In the window that appears, click on <i>Delete exam</i>.</p>",
           ]),

        write_paragraph_header("id_enter_exams", "Enter answers"),
        write_paragraph_body("",
            [
                "<p><b>Opening the Answers Window</b><br>Click on the candidate's name or the subject's name to open the window where you can enter the candidate's answers.",
                "The window below will appear.</p>",

                "<p>At the top of the window is the name of the exam, subject and candidate.",
                "Below are the numbers of the questions with a box for the answer. With a multiple choice question there is an asterisk (*) after the question.<br>",
                "When an exam has more than 50 questions, the questions are divided over two pages. At the bottom left of the window there are buttons with which you can go to another page.</p>",

                "<p class='pb-0'><b>Fill in answers</b><br>Enter the answer of the question. For an open question, enter the score obtained, for a multiple choice question a letter. ",
                "Enter an 'x' if the candidate has not answered a question or has entered multiple answers for a multiple choice question. All questions must be completed.</p>",
                "<p class='pb-0'>If you enter an answer that is not possible, a window will appear. This shows which answers are allowed.</p>",

                "<p>Entering is fastest if you click on the ENTER key after typing in the answer. You then go directly to the next question. ",
                "Click on a button with an arrow to go to the next or previous question, or to a question in the next or previous column.</p>",

                "<p><b>Save</b><br>The answers you entered will not be saved until you click the <i>Save</i> button.",
                "So don't forget to click the <i>Save</i> button when you have entered the answers.</p>",
                "<p class='pb-0'>In the column <i>Not filled in</i> you can see how many questions still need to be filled in. 49/58 means that 49 of the 58 questions have not yet been filled in. If all questions have been completed, this column remains empty.</p>",
            ]),
        write_image("img_exams_modA_en"),

        write_paragraph_header("id_download_exams", "Download answers"),
        write_paragraph_body("",
            [
                "<p>Click on <i>Download PDF</i> to download an overview of the completed answers. See the example below.<br>",
                "The box at the top of the page lists the details of the exam, the subject and the candidate. When all questions have been completed, AWP displays the total score obtained.<br>",
                "The box below shows how many questions have not been filled in. This is the number of questions that the school still has to fill in, so not the number of questions that the candidate has not filled in.<br>",
                "Below are the questions and the completed answers. At the bottom of the page is the name of the user who last entered data and the date of the last entry.</p>",
            ]),
        write_paragraph_body("img_exclamationsign",
            [
                "<p>Print this overview only if it is really necessary. If you print everything it will easily be a few hundred pages. That is bad for the environment and bad for the school's budget. The information can also be read from the screen.</p>",
            ]),
        write_image("img_exams_print_result_ne_en"),

        write_paragraph_header("id_submit_exams", "Approve and submit exams"),
        write_paragraph_body("",
            [
               "<p>After the answers of all exams have been entered, they must be approved and submitted. The procedure for this is the same as when submitting the Ex1 and Ex2 form.",
               "Click <a href='#' class='awp_href' onclick='LoadPage(&#39approve&#39)'>here</a> for a detailed description of this procedure.</p>",

                "<p class='mb-0 pb-0'>Submission of the exams is done in two steps:</p>",
                "<ul class='manual_bullet'><li>The first step is to <b>approve</b> the exams by the chairperson and secretary.</li>",
                "<li>The second step is the <b>submission</b> of the Ex-form by the chairperson or secretary.</li></ul>",


                "<p><b>Approve</b><br>Click <i>Approve Exams</i> in the menu bar. The <i>Approve Exams</i> window appears. ",
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
            ["<p><b>Partial exams</b><br>In 2022, the new examination of the practical exams will be introduced.",
                "The separate practical exam and central exam have now been merged into a practical exam that consists of different parts: the practical tests and the theoretical 'mini tests'.",
                "These tests are included as partial exams.</p> ",
                "<p><b>Enter answers</b><br>First select a partial exam. Enter the answers of the partial exam in the same way as for the regular exams.</p>",
            ]),

        "<div class='p-3 visibility_hide'>-</div>",

    ]
}
