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
                "<li>Vakken van kandidaten goedkeuren en het Ex1 formulier indienen. ",
                "Klik <a href='#' class='awp_href' onclick='LoadPage(&#39approve&#39)'>hier</a> voor de handleiding ervan;</li>",
                "<li>Het voorlopige Ex1-formulier downloaden.</li></ul>",
                "<p class='pb-0'>De optie om vakken van vakkenpakketten toe te toewijzen is nog niet beschikbaar.</p>",
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
                "<p>Nieuw in AWP is de controle op de samenstelling van de vakken. ",
                "AWP gaat na of de samenstelling van de vakken van de kandidaten voldoet aan de wettelijke voorschriften. ",
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
                "Een ^ teken achter het vak betekent dat het een verplicht vak is, een * betekent dat het een combinatievak is.</p>",

                "<p><b>Vakken toevoegen of verwijderen</b><br> ",
                "Klik op een vak in de lijst om een vak te selecteren. ",
                "De regel wordt blauw en er verschijnt een vinkje. Nog een keer klikken en het vinkje verdwijnt. ",
                "Je kunt meerdere vakken selecteren.<br>",
                "Een of meerdere <b>vakken toevoegen</b> gaat als volgt: selecteer de gewenste vakken in de linker lijst en klik op de knop <i>Vakken toevoegen</i>, ",
                "Je kunt ook op een vak dubbelklikken om het toe te voegen.<br>",
                "Het <b>verwijderen van vakken</b> gaat op dezelfde manier. Klik op de knop <i>Vakken verwijderen</i> of dubbelklik op een vak in de rechter lijst. ",
                "Elke keer wanneer vakken zijn toegevoegd of verwijderd berekent AWP opnieuw of de samenstelling van de vakken klopt.<br>",
                "Klik op de knop <b><i>Opslaan</i></b> om de wijzigingen op te slaan. </p>",

                "<p><b>Kenmerken van het vak wijzigen</b><br> ",
                "Klik op een kandidaat in de rechter lijst. In het kader <i>Kenmerken van het vak</i> staan alle kenmerken van dat vak. ",
                "De algemene kenmerken kun je niet veranderen. Dat zijn bijvboorbeeld: 'Combinatievak', 'Verplicht vak'.<br>",
                "Individuele kenmerken kun je wel per kandidaat instellen. ", "Het zijn: 'Extra vak, telt niet mee voor de uitslag' en 'Extra vak, telt mee voor de uitslag'.</p>",
            ]),
        write_image("img_studsubj_mod_studsubj_ne"),

        write_paragraph_header("id_pws_title_subjects", "Titel en vakken van het werkstuk"),
        write_paragraph_body("",
            [
                "<p>De 'Titel van het werkstuk' en 'Vakken waarop het werkstuk betrekking heeft' zijn voortaan opgenomen als individueel kenmerk van het vak 'Werkstuk'. ",
                "Klik op het vak 'Werkstuk' en vul de titel en vakken van het werkstuk in bij <i>Kenmerken van het vak</i> </p>",
                "<p>Je kunt de titels en vakken van het werkstuk ook uploaden. ",
                "Klik in de menubalk van de pagina <i>Vakken</i> op <i>Vakken uploaden</i> en koppel bij stap 2 de velden 'Titel van het werkstuk' en 'Vakken van het werkstuk' ",
                "aan de betreffende Excel kolommen.<br>",
                "Ook als de vakken reeds zijn ingevoerd in AWP kun je de titels en vakken van het werkstuk uploaden.</p"
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
                "<li>Approve candidates' subjects and submit the Ex1 form. ",
                "Click <a href='#' class='awp_href' onclick='LoadPage(&#39approve&#39)'>here</a> for its tutorial;</li>",
                "<li>Download the preliminary Ex1 form.</li></ul>",
                "<p class='pb-0'>The option to assign subjects from subject packages is not yet available.</p>",
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
                "<p>New in AWP is the check on the composition of the subjects. ",
                "AWP checks whether the composition of the candidates' subjects meets the legal requirements. ",
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
                "A ^ character after the subject means it is a required field, a * means it is a combination subject.</p>",

                "<p><b>Add or remove subjects</b><br> ",
                "Click on a subject in the list to select a subject. ",
                "The line will turn blue and a checkmark will appear. Click one more time and the checkmark will disappear. ",
                "You can select multiple subjects.<br>",
                "To <b>add</b> one or more subjects: select the desired subjects in the list on the left and click on the button <i>Add subjects</i>, ",
                "You can also double click on a subject to add it.<br>",
                "<b>Deleting</b> subjects is done in the same way. Click on the button <i>Delete subjects</i> or double click on a subject in the right list. ",
                "Every time subjects are added or removed, AWP recalculates whether the composition of the subjects is correct.<br>",
                "Click the <i>Save</i> button to save the changes.</p>",

                "<p><b>Change subject attributes</b><br> ",
                "Click on a candidate in the list on the right. In the frame <i>Attributes of the subject</i> you will find all the characteristics of that subject. ",
                "You cannot change the general characteristics. These are for example: 'Combination subject', 'Required subject'.<br>",
                "You can set individual characteristics per candidate. ",
                "They are: 'Extra subject, does not count towards the result' and 'Extra subject, counts towards the result'.</p>",
            ]),
        write_image("img_studsubj_mod_studsubj_en"),
        write_paragraph_header("id_pws_title_subjects", "Project title and subjects"),
         write_paragraph_body("",
             [
                 "<p>The 'Title of the assignment' and 'Subjects to which the assignment relates' are now included as individual attributes of the subject 'Project'. ",
                 "Click on the field 'Project' and fill in the title and fields of the assignment at <i>Attributes of the subject</i> </p>",
                 "<p>You can also upload the titles and subjects of the assignment. ",
                 "Click in the menu bar of the page <i>Subjects</i> on <i>Upload subjects</i> and link the fields 'Title of the assignment' and 'Subjects of the assignment' in step 2 ",
                 "to the appropriate Excel columns.<br>",
                 "Even if the subjects have already been entered in AWP, you can upload the titles and subjects of the assignment.</p"
             ]),
        "<div class='p-3 visibility_hide'>-</div>",
     ]
}
