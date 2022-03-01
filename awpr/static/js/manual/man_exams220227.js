// PR2021-07-18 added

    "use strict";

const man_exams = {

/////////  NEDERLANDS //////////////////////////////
    nl: [
        write_paragraph_header("id_intro_exams", "Examens (voormalige WOLF programma)"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
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

            "</div>",
        "</div>",

        write_image("img_exams_tableA_ne"),

        write_paragraph_header("id_link_exams", "Examen koppelen aan een vak"),
        "<div class='mfc mb-4'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",

                "<p>Zodra het ETE de examens heeft gepubliceerd koppelt AWP waar mogelijk het bijbehorende examen aan de vakken van de kandidaten. ",
                "Alleen wanneer bij een vak meerdere examens beschikbaar zijn, dient de school het juiste examen te kiezen.</p>",

                "<p>Klik in de kolom 'Examen' van het betreffende vak van de kandidaat. Er verschijnt een venster met een of meerdere examens. Selecteer een examen en klik op <i>OK</i>. ",
                "Wanneer bij een vak (nog) geen examens beschikbaar zijn, verschijnt de melding'Er zijn nog geen examens voor dit vak.'.</p>",

                "<p><b>Examen verwijderen</b><br>Als een kandidaat niet aan het examen heeft deelgenomen kun je het examen verwijderen. ",
                "Klik op het examen van het betreffende vak van de kandidaat. Klik in het venster dat verschijnt op <i>Examen verwijderen</i>.</p>",

            "</div>",
        "</div>",

        write_paragraph_header("id_enter_exams", "Antwoorden invoeren"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
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

                "<p><b>Opslaan</b><br>De ingevulde antwoorden worden pas opgeslagen als je op de knop <i>Opslaan</i> klikt.",
                "Vergeet daarom niet op de knop <i>Opslaan</i> te klikken als je de antwoorden hebt ingevoerd.</p>",
                "<p class='pb-0'>In de kolom <i>Niet ingevuld</i> kunt je zien hoeveel vragen er nog ingevuld moeten worden. 49/58 betekent dat 49 van de 58 vragen nog niet zijn ingevuld. Als alle vragen zijn ingevuld blijft deze kolom leeg.</p>",

            "</div>",
        "</div>",
        write_image("img_exams_modA_ne"),

        write_paragraph_header("id_download_exams", "Antwoorden downloaden"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>Klik op <i>PDF downloaden</i> om een overzicht van de ingevulde antwoorden te downloaden. Zie het voorbeeld hieronder.<br>",
                "In het kader bovenaan de pagina staan de gegevens van het examen, het vak en de kandidaat. Als alle vragen zijn ingevuld geeft AWP de behaalde totaal score weer.<br>",
                "In het kader daaronder staat hoeveel vragen niet zijnn ingevuld. Dit is het aantal vragen dat de school nog moet invullen, dus niet het aantal vragen dat de kandidaat niet heeft ingevuld.<br>",
                "Daaronder staan de vragen en de ingevulde antwoorden. Onderaan de pagina staat de naam van de gebruiker, die het laatst gegevens heeft ingevoerd en de datum van de laatste invoer.</p>",
            "</div>",
        "</div>",
        "<div class='mfc mb-2'>",
            "<div class='mfl mt-2'><div class='img_exclamationsign'></div></div>",
            "<div class='mfr'>",
                "<p>Print dit overzicht alleen als het echt nodig is. Als je alles uitprint gaat het al gauw om een paar honderd pagina's. Dat is slecht voor het milieu en slecht voor het budget van de school. De  informatie is ook te lezen vanaf het scherm.</p>",

            "</div>",

        "</div>",
        write_image("img_exams_print_result_ne_en"),


        write_paragraph_header("id_submit_exams", "Examens goedkeuren en indienen"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
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
            "</div>",
        "</div>",


        write_paragraph_header("id_practical_exams", "Praktijkexamens"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",

                "<p><b>Deelexamens</b><br>In 2022 is de nieuwe examinering van de praktijkexamens ingevoerd. ",
                "Het afzonderlijke praktijkexamen en centraal examen zijn nu samengevoegd tot een praktijkexamen dat uit verschillende onderdelen bestaat: de praktijktoetsen en de theoretische 'minitoetsen'. ",
                "Deze toetsen zijn als deelexamens opgenomen. ",
                "Voordat de antwoorden van een praktijkexamen kunnen worden ingevoerd dienen eerst de deelexamens te worden geselecteerd, die de kandidaat heeft afgelegd.</p> ",
                "<p><b>Maximum score</b><br>Elk deelexamen heeft een maximum score. AWP controleert of de totale maximum score van de geselecteerde deelexamens overeenkomt met de maximale score van het hele praktijkexamen. ",
                "Hiermee wordt voorkomen dat er teveel, te weinig of verkeerde deelexamens worden geselecteerd.</p>",
                "<p><b>Antwoorden invoeren</b><br>Het invoeren van de antwoorden van de deelexamens gaat op dezelfde manier als bij de gewone examens.</p>",
                "<p><b>Herexamen</b><br>Wanneer de kandidaat een herexamen doet van het praktijkexamen wordt een deel van het examen opnieuw afgelegd. ",
                "AWP kopieert de antwoorden van het reeds afgelegde examen naar het herexamen. Verwijder eerst het overeenkomende deelexamen van het reeds afgelegde examen en selecteer het deelexamen waarin de kandidaat herexamen doet. ",
                "Vul de antwoorden van het herexamen in</p>.",

             "</div>",
        "</div>",

        write_image("img_studsubj_mod_cluster_ne"),

    ],

    en:  [

        write_paragraph_header("id_intro", "Subjects of candidates"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>Click the <i>Subjects</i> button in the page bar. The <i>Subjects of candidates</i> page below will now open. </p>",
                "<p class='pb-0'>In this page you can:</p>",
                "<ul class='manual_bullet mb-0'><li>Upload subjects of candidates. ",
            // from https://pagedart.com/blog/single-quote-in-html/
                "Click <a href='#' class='awp_href' onclick='LoadPage(&#39upload&#39)'>here</a> to go to its manual;</li>",
                "<li>View the subject composition check;</li>",
                "<li>Assign subjects to a candidate;</li>",
                "<li>Approve candidates' subjects and submit the Ex1 form.",
                "Click <a href='#' class='awp_href' onclick='LoadPage(&#39approve&#39)'>here</a> for its tutorial;</li>",
                "<li>Download the preliminary and submitted Ex1 form.</li></ul>",
                "<p class='pb-0'>The option to assign subjects of subject packages is not yet available.</p>",
            "</div>",
        "</div>",

        write_paragraph_header("id_filter_subjects", "Filter subjects"),
        "<div class='mfc mb-4'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>On each line in the table is a candidate's subject.",
                "You can display all subjects of all candidates, but that is not convenient.",
                "It makes the page cluttered and for many candidates also slow. It is better to filter subjects. </p>",

                "<p class='pb-0'>The filtering can be done in several ways:</p>",
                "<ul class='manual_bullet mb-0'><li>In the vertical gray filter bar on the left you can ",
                "select a <b>learning path</b>, <b>sector</b> or <b>profile</b>;</li>",
                "<li>You can also select a <b>subject</b> or <b>candidate</b>, but not both.",
                "<li>Finally, you can filter subjects using the <b>filter row</b>;</li></ul>",
            "</div>",
        "</div>",
        write_image("img_studsubj_tab_subj_en"),

        write_paragraph_header("id_validate_subjects", "Composition check"),
        "<div class='mfc mb-2'>",
            "<div class='mfl mt-2'><div class='img_exclamationsign'></div></div>",
            "<div class='mfr'>",
                "<p>New in AWP is the control of the composition of the subjects. ",
                "AWP checks whether the composition of the candidates' subjects meets the legal requirements.",
                "If the composition of the subjects is not correct, a yellow triangle with an exclamation mark will appear in front of the candidate's name.",
                "Click on the candidate's name to open the window where you can change the candidate's subjects.",
                "A subject appears at the top stating which errors were found.</p>",

                "<p class='pb-0'>The subjects are checked on the following points, among other things:</p>",
                "<ul class='manual_bullet mb-0'><li>whether the required subjects are present;</li>",
                "<li>whether the total number of subjects and the number of subjects per character (Common part etc.) is correct;</li>",
                "<li>whether the total number of modern foreign languages ​​and mathematics subjects is correct.</li></ul>",
                "<p>In the evening schools and National Exams, the check on the compulsory subjects and the minimum required number of subjects is skipped:</p>",
                "<p>When uploading subjects, the character of the subject is not taken into account. ",
                "Error messages can therefore arise because AWP has given a subject the wrong character.",
                "In that case, the character of the subject must be corrected manually.</p>",
            "</div>",
        "</div>",
        write_image("img_studsubj_mod_studsubj_en"),

        write_paragraph_header("id_enter_studsubj", "Enter candidate subjects"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>Click on the candidate's name to open the window where you can edit the candidate's subjects.",
                "The list on the left shows the available subjects, the list on the right contains the subjects of the candidate.",
                "Only the abbreviation and character of the subject are displayed in the list.",
                "If you hover the mouse over the abbreviation, a window with the full name will appear.",
                "A ^ character after the subject means it is a required field, a * means it is a combo subject.</p>",

                "<p><b>Add or remove subjects</b><br> ",
                "Click on a subject in the list to select a subject. ",
                "The line will turn blue and a checkmark will appear. Click one more time and the checkmark will disappear.",
                "You can select multiple subjects.<br>",
                "How to add one or more <b>subjects</b>: select the desired subjects in the list on the left and click on the button <i>Add subjects</i>, ",
                "You can also double click on a subject to add it.<br>",
                "The <b>delete of subjects</b> is done in the same way. Click on the button <i>Delete subjects</i> or double click on a subject in the right list. ",
                "Every time subjects are added or removed, AWP recalculates whether the composition of the subjects is correct.<br>",
                "Click the <b><i>Save</i></b> button to save the changes. </p>",

                "<p><b>Change subject attributes</b><br> ",
                "Click on a candidate in the list on the right. In the subject <i>Attributes of the subject</i> you will find all the characteristics of that subject. ",
                "You cannot change the general characteristics. These are for example: 'Combination subject', 'Required subject'.<br>",
                "You can set individual characteristics per candidate.", "They are: 'Extra subject, does not count towards the result' and 'Extra subject, counts towards the result'.<br>",
                "The 'Title of the assignment' and 'Subjects to which the assignment relates' are now also included as individual attributes of the subject 'Project'.",
            "</div>",
        "</div>",
        write_image("img_studsubj_mod_studsubj_en"),

        write_paragraph_header("id_clusters", "Clusters"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",

                "<p>A <b>cluster</b> is a group of exam candidates who follow the same subject. ",
                "The difference with the class is that each candidate can only be in one class, ",

                "while a candidate belongs to a separate cluster for each subject. ",
                "Clusters are used for candidates who take an exam together in the same classroom. ",
                "The 'Proces-verbaal van Toezicht' (Ex3 form) can be printed per cluster and when entering grades, the candidates can be filtered by cluster.</p>",

                "<p>On the <i>Subjects</i> page, click the <i>Clusters</i> button. The <i>Clusters</i> window below will now open.</p>",
            "</div>",
        "</div>",

        write_image("img_studsubj_mod_cluster_en"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p class='mb-0'><b>Add clusters and candidates</b><br> ",
                "How to add a cluster of candidates:</p>",
                "<ul class='manual_bullet mb-2'><li><b>Select a subject</b> in the top frame;</li>",
                "<li>Click <b>Add Cluster</b> under the left table <i>Clusters</i>. AWP will now add a cluster to the list.</li>",
                "<li><b>Select a cluster</b> and optionally click on <i>Change cluster name</i> to change the name of the cluster. Each cluster name can only appear once.</li>",
                "<li><b>Click on a candidate</b> in the list of <i>Available candidates</i> to add the candidate, ",
                "or click on a candidate in the list <i>Candidates of this cluster</i> to remove the candidate.</li>",
                "<li>Finally click <b>Save</b> to save the changes.</li></ul>",

                "<p><b>Delete cluster</b><br> ",
                "<b>Select a cluster</b> from the list, click the <b>Delete cluster</b> button and click <b>Save</b>. The cluster will now be deleted.<br>",
                "If a cluster is deleted, this cluster will also be deleted for all candidates belonging to this cluster. If this is the case, a warning appears first.</p>",

                "<p><b>Filter available candidates</b><br> ",
                "Click on <b>Filter class</b> in the right-most frame to display only the available candidates of the selected class.<br>",
                "Click <b>Show also candidates with cluster</b> to view candidates who already belong to a cluster.<br>",
                "If you add a candidate who already belongs to another cluster, the other cluster will be deleted. A candidate can only belong to 1 cluster.</p>",

                "<p><b>Change an individual candidate's cluster</b><br> ",
                "In the list of candidates, click on a candidate's <i>Cluster</i> column. The window <i>Select cluster</i> will appear.<br> ",
                "<b>Select a cluster</b> or click <b>Remove cluster</b>.</p>",
             "</div>",
        "</div>",

        "<div class='p-3 visibility_hide'>-</div>",

    ]
}
