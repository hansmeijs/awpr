// PR2021-07-18 added

    "use strict";

const man_studsubj = {

/////////  NEDERLANDS //////////////////////////////
    nl: [
        write_paragraph_header("id_intro", "Vakken van kandidaten"),
        write_paragraph_body("",
            [
                "<p>Klik in de paginabalk op de knop <i>Vakken</i>. De onderstaande pagina <i>Vakken van kandidaten</i> wordt nu geopend. </p>",
                "<p class='pb-0'>In deze pagina kun je:</p>",
                "<ul class='manual_bullet mb-0'><li>Vakken van kandidaten uploaden. ",
            // from https://pagedart.com/blog/single-quote-in-html/
                "Klik <a href='#' class='awp_href' onclick='LoadPage(&#39upload&#39)'>hier</a> om naar de handleiding hiervan te gaan;</li>",
                "<li>De controle op de samenstelling van de vakken bekijken;</li>",
                "<li>Vakken aan een kandidaat toewijzen;</li>",
                "<li>Vakken van kandidaten goedkeuren. ",
                    "Klik <a href='#' class='awp_href' onclick='LoadPage(&#39approve&#39)'>hier</a> voor de handleiding ervan;</li>",

                "<li>Aangeven of de kandidaat een vrijstelling voor dit vak heeft;</li>",
                "<li>Aangeven of de kandidaat een herexamen in het tweede of derde tijdvak dit heeft;</li>",

                "<li>Het voorlopige Ex1-formulier en Ex4-formulier downloaden.</li>",
                "<li>Het Ex1-formulier en Ex4-formulier indienen.</li></ul>",
                //"<p class='pb-0'>De optie om vakken van vakkenpakketten toe te toewijzen is nog niet beschikbaar.</p>",
            ]),

        write_paragraph_header("id_filter_subjects", "Vakken filteren"),
        write_paragraph_body("",
            [
                "<p>Op elke regel in de tabel staat een vak van een kandidaat. ",
                "Je kunt alle vakken van alle kandidaten weergeven, maar dat is niet handig. ",
                "Het maakt de pagina onoverzichtelijk en bij veel kandidaten ook traag. Beter is het om vakken te filteren.</p>",

                "<p class='pb-0'>Het filteren kan op verschillende manieren:</p>",
                "<ul class='manual_bullet mb-0'><li>In de verticale grijze filterbalk links kun je ",
                "een <b>leerweg</b>, <b>sector</b> of <b>profiel</b> selecteren;</li>",
                "<li>Je kunt ook een <b>vak</b>, <b>cluster</b> of <b>kandidaat</b> selecteren;</li>",
                "<li>Tenslotte kun je vakken filteren met behulp van de <b>filterregel</b>.</li></ul>",
            ]),
        write_image("img_studsubj_tab_subj_ne"),

        write_paragraph_header("id_validate_subjects", "Controle op de samenstelling van de vakken"),
        write_paragraph_body("img_exclamationsign",
            [
                //"<p>Nieuw in AWP is de controle op de samenstelling van de vakken. ",
                "<p>AWP gaat na of de samenstelling van de vakken van de kandidaten voldoet aan de wettelijke voorschriften. ",
                "Wanneer de samenstelling van de vakken niet correct is verschijnt er een gele driehoek met een uitroepteken voor de naam van de kandidaat. ",
                "Klik op de naam van de kandidaat om het venster te openen waarmee je de vakken van de kandidaat kunt wijzigen. ",
                "Bovenaan verschijnt een kader waarin staat welke fouten er zijn gevonden.</p>",

                "<p class='pb-0'>De vakken worden onder meer op de volgende punten gecontroleerd:</p>",
                "<ul class='manual_bullet mb-0'><li>of de verplichte vakken aanwezig zijn;</li>",
                "<li>of het totaal aantal vakken en het aantal vakken per karakter (Gemeenschappelijk deel etc.) klopt;</li>",
                "<li>of het totaal aantal moderne vreemde talen en wiskundevakken klopt.</li></ul>",
                "<p>Bij de avondscholen en Landsexamens wordt de controle op de verplichte vakken en het minimaal vereiste aantal vakken overgeslagen:</p>",
                "<p>Bij het uploaden van vakken wordt geen rekening gehouden met het karakter van het vak. ",
                "Er kunnen daarom foutmeldingen ontstaan, omdat AWP een vak het verkeerde karakter heeft meegegeven. ",
                "In dat geval moet het karakter van het vak handmatig gecorrigeerd worden.</p>",
            ]),
        write_image("img_studsubj_mod_studsubj_ne"),

        write_paragraph_header("id_enter_studsubj", "Vakken invoeren"),
        write_paragraph_body("img_exclamationsign",
            [
                "<p>Klik op de naam van de kandidaat om het venster te openen waarmee je de vakken van de kandidaat kunt wijzigen. ",
                "In de linker lijst staan de beschikbare vakken, de rechter lijst bevat de vakken van de kandidaat. ",
                "Alleen de afkorting en het karakter van het vak worden in de lijst weergegeven. ",
                "Als je met de muis boven de afkorting gaat staan, verschijnt er een venster met de volledige naam. ",
                "Een ^ teken achter het vak betekent dat het een verplicht vak is, een * betekent dat het een combinatievak is, een + betekent dat het een extra vak is.</p>",

                "<p><b>Vakken toevoegen</b><br> ",
                "Klik op een vak in de lijst met beschikbare vakken. ",
                "De regel wordt blauw en er verschijnt een vinkje. Nog een keer klikken en het vinkje verdwijnt. ",
                "Je kunt meerdere vakken selecteren.<br>",
                "Klik vervolgens op de knop <i>Vakken toevoegen</i>. ",
                "Je kunt ook op een vak dubbelklikken om het toe te voegen.<br",
                "Elke keer wanneer vakken zijn toegevoegd berekent AWP opnieuw of de samenstelling van de vakken klopt.<br>",
                "Klik op de knop <b><i>Opslaan</i></b> om de wijzigingen op te slaan. </p>",

                "<p><b>Vakken verwijderen</b><br> ",
                "Het verwijderen van vakken gaat op dezelfde manier. Klik op de knop <i>Vakken verwijderen</i> of dubbelklik op een vak in de rechter lijst. ",
                "Elke keer wanneer vakken zijn toegevoegd of verwijderd berekent AWP opnieuw of de samenstelling van de vakken klopt.<br>",
                "Klik op de knop <b><i>Opslaan</i></b> om de wijzigingen op te slaan. </p>",

                "<p><b>Vakken aanmerken om gewist te worden</b><br>",
                "Wanneer het vak, dat je wilt wissen, al op een Ex1-formulier is ingediend, ",
                "wordt het vak niet meteen gewist, maar wordt het 'aangemerkt om gewist te worden'. ",
                "Dit wordt aangegeven met een dubbele rode streep door de naam van het vak.<br>" ,
                "De voorzitter en secretaris moeten de gewiste vakken eerst goedkeuren ",
                "en door middel van een aanvullend Ex1-formulier bij de Inspectie en het ETE indienen.<br>",
                "De vakken worden gewist als het aanvullende Ex1-formulier is ingediend.</p>",
            ]),
        write_image("img_studsubj_mod_studsubj_ne"),

        write_paragraph_header("id_pws_title_subjects", "Titel en vakken van het werkstuk"),
        write_paragraph_body("",
            [
                "<p>De 'Titel van het werkstuk' en 'Vakken waarop het werkstuk betrekking heeft' zijn opgenomen als individueel kenmerk van het vak 'Werkstuk'.</p>",

                "<p class='pb-0'><b>Invoeren titel en vakken van het werkstuk</b><br> ",
                "Het invoeren van de titel en vakken van het werkstuk gaat als volgt:</p>",
                "<ul class='manual_bullet mb-2'><li>Ga naar de regel met het vak 'Werkstuk' van de betreffende kandidaat.</li>",
                "<li>Klik op de kolom 'Titel van het werkstuk' of 'Vakken waarop het werkstuk betrekking heeft'. ",
                "Het venster 'Titel werkstuk' of 'Vakken werkstuk' verschijnt.</li>",
                "<li>Vul de titel of vakken van het werkstuk in en klik op Opslaan.</li>",
                "<li>Klik op de knop <i>Bijzondere tekens invoeren</i> als je letters met accenten of dergelijke wilt invoeren.</li></ul>",

                "<p class='pb-0'><b>Uploaden titels en vakken van het werkstuk</b><br> ",
                "<p>Je kunt de titels en vakken van het werkstuk ook uploaden. ",
                "Klik in de menubalk van de pagina <i>Vakken</i> op <i>Vakken uploade n</i> en koppel bij stap 2 de velden 'Titel van het werkstuk' en 'Vakken van het werkstuk' ",
                "aan de betreffende Excel kolommen.<br>",
                "Ook als de vakken reeds zijn ingevoerd in AWP kun je de titels en vakken van het werkstuk uploaden.</p>",

                "<p class='pb-0'><b>Fout bij printen bijzondere tekens</b><br> ",
                "<p>Het kan voorkomen dat op de cijferlijst een zwart hokje wordt geprint in plaats van een bijzonder teken. ",
                "Dit betekent dat AWP het bijzondere teken niet herkent bij het aanmaken van de cijferlijst. ",
                "Dat kan gebeuren wanneer de gegevens zijn geïmporteerd of zijn ingevoerd op een Apple computer.<br>",
                "Voer het teken dan opnieuw in door middel van de knop <i>Bijzondere tekens invoeren</i>.</p>"
            ]),

        "<div class='p-3 visibility_hide'>-</div>",
    ],

en:  [
        write_paragraph_header("id_intro", "Subjects of candidates"),

        write_paragraph_body("img_exclamationsign",
            [
                "<p>Click the <i>Subjects</i> button in the page bar. The <i>Subjects of candidates</i> page below will now open.</p>",
                "<p class='pb-0'>In this page you can:</p>",
                "<ul class='manual_bullet mb-0'><li>Upload candidate subjects. ",
            // from https://pagedart.com/blog/single-quote-in-html/
                "Click <a href='#' class='awp_href' onclick='LoadPage(&#39upload&#39)'>here</a> to go to its manual;</li>",
                "<li>View the subject composition check;</li>",
                "<li>Assign subjects to a candidate;</li>",
                "<li>Approve candidates' subjects. ",
                    "Click <a href='#' class='awp_href' onclick='LoadPage(&#39approve&#39)'>here</a> for its tutorial;</li>",

                "<li>Indicate whether the candidate has an exemption for this subject;</li>",
                "<li>Indicate whether the candidate has a retake in the second or third period;</li>",

                "<li>Download the preliminary Ex1 form and Ex4 form.</li></ul>",
                "<li>Submit the Ex1 form and Ex4 form .</li></ul>",
                //"<p class='pb-0'>The option to assign subjects from subject packages is not yet available.</p>",
            ]),

        write_paragraph_header("id_filter_subjects", "Filter subjects"),
        write_paragraph_body("",
            [
                "<p>On each line in the table is a subject of a candidate. ",
                "You can display all subjects of all candidates, but that is not convenient. ",
                "It makes the page cluttered and for many candidates also slow. It is better to filter subjects. </p>",

                "<p class='pb-0'>The filtering can be done in several ways:</p>",
                "<ul class='manual_bullet mb-0'><li>In the vertical gray filter bar on the left you can ",
                "select a <b>learning path</b>, <b>sector</b> or <b>profile</b>;</li>",
                "<li>You can also select a <b>subject</b>, <b>cluster</b> or <b>candidate</b>;</li>",
                "<li>Finally, you can filter subjects using the <b>filter row</b>.</li></ul>",
            ]),
        write_image("img_studsubj_tab_subj_en"),

        write_paragraph_header("id_validate_subjects", "Composition check"),
        write_paragraph_body("img_exclamationsign",
            [
                //"<p>New in AWP is the check on the composition of the subjects. ",
                "<p>AWP checks whether the composition of the candidates' subjects meets the legal requirements. ",
                "If the composition of the subjects is not correct, a yellow triangle with an exclamation sign will appear in front of the candidate's name. ",
                "Click on the candidate's name to open the window where you can change the candidate's subjects. ",
                "A frame appears at the top stating which errors were found.</p>",

                "<p class='pb-0'>The subjects are checked on the following points, among other things:</p>",
                "<ul class='manual_bullet mb-0'><li>whether the required subjects are present;</li>",
                "<li>whether the total number of subjects and the number of subjects per character ('Gemeenschappelijk deel' etc.) is correct;</li>",
                "<li>whether the total number of modern foreign languages and mathematics subjects is correct.</li></ul>",
                "<p>In the evening schools and Landsexamens, the check on the compulsory subjects and the minimum required number of subjects is skipped.</p>",

                "<p>When uploading subjects, the character of the subject is not taken into account. ",
                "Error messages can therefore arise because AWP has given a subject the wrong character. ",
                "In that case, the character of the subject must be corrected manually.</p>",
            ]),
        write_image("img_studsubj_mod_studsubj_en"),

        write_paragraph_header("id_enter_studsubj", "Entering subjects"),
        write_paragraph_body("",
            [
                "<p>Click on the candidate's name to open the window where you can edit the candidate's subjects. ",
                "The list on the left shows the available subjects, the list on the right contains the subjects of the candidate. ",
                "Only the abbreviation and character of the subject are displayed in the list. ",
                "If you hover the mouse over the abbreviation, a window with the full name will appear. ",
                "A ^ character after the subject means it is a required field, a * means it is a combination subject, a + means it is an extra subject.</p>",

                "<p><b>Add subjects</b><br> ",
                 "Click on a subject in the list of available subjects. ",
                 "The line turns blue and a check mark appears. Click again and the check mark disappears. ",
                 "You can select multiple subjects.<br>",
                 "Then click on the <i>Add subjects</i> button.",
                 "You can also double click on a subject to add it.<br",
                 "Every time when subjects are added, AWP recalculates whether the composition of the subjects is correct.<br>",
                 "Click the <b><i>Save</i></b> button to save the changes. </p>",

                 "<p><b>Remove subjects</b><br> ",
                 "Deleting subjects is done in the same way. Click on the <i>Delete subjects</i> button or double click on a subject in the list on the right.",
                 "Every time subjects are added or removed, AWP recalculates whether the composition of the subjects is correct.<br>",
                 "Click the <b><i>Save</i></b> button to save the changes. </p>",

                 "<p><b>Mark subjects to be deleted</b><br>",
                 "If the subject you want to delete has already been submitted on an Ex1 form,",
                 "the subject will not be deleted immediately, but will be 'marked to be deleted'.",
                 "This is indicated by a double red line through the subject name.<br>" ,
                 "The chairman and secretary must first approve the deleted subjects",
                 "and submit to the Inspectorate and the ETE by means of an additional Ex1 form.<br>",
                 "The subjects will be deleted when the supplementary Ex1 form is submitted.</p>",
            ]),
        write_image("img_studsubj_mod_studsubj_en"),
        write_paragraph_header("id_pws_title_subjects", "Assignment title and subjects"),
         write_paragraph_body("",
             [
                 "<p>The 'Title of the assignment' and 'Subjects to which the assignment relates' are included as individual attributes of the subject 'Werkstuk'. ",
                 "<p class='pb-0'><b>Entering the title and subjects of the assignment</b><br> ",
                "Entering the title and subjects of the assignment can be done as follows:</p>",
                "<ul class='manual_bullet mb-2'><li>Go to the line with the subject 'Werkstuk' of the candidate.</li>",
                "<li>Click on the column 'Assignment title' or Assignment subjects'. ",
                "The window 'Title of the assignment' or 'Subjects of the assignment' appears.</li>",
                "<li>Enter the title or subjects of the assignment and click 'Save'.</li>",
                "<li>Click on the button <i>Enter special characters</i> if you want to enter letters with accents or the like.</li></ul>",

                "<p class='pb-0'><b>Uploading titles and subjects of the assignment</b><br> ",
                "<p>You can also upload the titles and subjects of the assignment. ",
                "Click on <i>Upload subjects</i> in the menu bar of the <i>Subjects</i> page and link the fields 'Titel van het werkstuk' and 'Vakken van het werkstuk' ",
                "to the relevant Excel columns in step 2.<br>",
                "Even if the subjects have already been entered in AWP, you can upload the titles and subjects of the assignment.</p>",

                "<p class='pb-0'><b>Error when printing special characters</b><br> ",
                "<p>It is possible that a black box is printed on the grade list instead of a special character. ",
                "This means that AWP does not recognize the special character when creating the grade list. ",
                "That can happen when the data has been imported or entered on an Apple computer.<br>",
                "Then re-enter the character using the <i>Enter special characters</i> button.</p>"
             ]),
        "<div class='p-3 visibility_hide'>-</div>",
     ]
}
