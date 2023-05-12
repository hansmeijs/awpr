// PR2023-01-16 added

    "use strict";

const man_student = {

/////////  NEDERLANDS //////////////////////////////
    nl: [
        write_paragraph_header("id_intro", "Kandidaten"),
        write_paragraph_body("",
            [
                "<p>Klik in de paginabalk op de knop <i>Kandidaten</i>. De onderstaande pagina <i>Kandidaten</i> wordt nu geopend. </p>",
                "<p class='pb-0'>In deze pagina kun je:</p>",
                "<ul class='manual_bullet mb-0'><li>Kandidaten uploaden. ",
            // from https://pagedart.com/blog/single-quote-in-html/
                "Klik <a href='#' class='awp_href' onclick='LoadPage(&#39upload&#39)'>hier</a> om naar de handleiding hiervan te gaan;</li>",
                "<li>Kandidaten toevoegen en wissen;</li>",
                "<li>Gegevens van kandidaten wijzigen;</li>",
                "<li>Een Excel bestand met kandidaatgegevens downloaden.</li></ul>"
            ]),

        write_paragraph_header("id_filter_students", "Kandidaten filteren"),
        write_paragraph_body("",
            [
                "<p>Op elke regel in de tabel staat een kandidaat. ",
                "Je kunt alle kandidaten weergeven, maar als er veel kandidaten zijn is het handiger om kandidaten te filteren.</p>",

                "<p class='pb-0'>Het filteren kan op verschillende manieren:</p>",
                "<ul class='manual_bullet mb-2'><li>In de verticale grijze balk links op de pagina kun je ",
                "een <b>leerweg</b>, <b>sector</b> of <b>profiel</b> of <b>kandidaat</b> selecteren;</li>",
                "<li>Je kunt ook kandidaten filteren met behulp van de <b>filterregel</b>. Klik <a href='#' class='awp_href' onclick='LoadPage(&#39home&#39, &#39id_filterrow&#39 )'>hier</a> om naar de handleiding van de filterregel te gaan.</li></ul>",
            ]),

        write_image("img_student_page_ne"),

        write_paragraph_header("id_add_student", "Kandidaat toevoegen"),
        write_paragraph_body("",
            ["<p>Klik in de menubalk op de knop <i>Kandidaat toevoegen</i>. Het onderstaande venster <i>Kandidaat toevoegen</i> verschijnt nu. ",
                "In dit venster kunt u de persoonsgegevens en de algemene studiegegevens van de kandidaat invoeren.</p>",

                "<p><b>Achternaam, voornamen, voorvoegsel</b><br> ",
                "Vul hier de naam van de kandidaat in. De velden 'Achternaam' en 'Voornamen' moeten verplicht worden ingevuld.<br>",
                "Let erop dat de naam precies hetzelfde is geschreven als in het bevolkingsregister.<br>",
                "Het veld 'Voorvoegesel' is er om kandidaten in de juiste alfabetische volgorde weer te geven. ",
                "Wanneer je 'van Aanholt' invult in het veld 'Achternaam', wordt hij onder de 'V' weergegeven, ",
                "maar als je 'Aanholt' zet bij 'Achternaam' en 'van' bij 'Voorvoegsel, wordt de naam onder de 'A' weergegeven.</p>",

                "<p><b>Bijzondere tekens</b><br> ",
                "Klik op de knop <i>Bijzondere tekens invoeren</i> links onder in het venster om de lijst met bijzondere tekens weer te geven. ",
                "Klik op het betreffende teken om het in te voeren.</p>",

                "<p><b>ID-nummer</b><br> ",
                "Vul hier het sedulanummer van de kandidaat in. Het moet verplicht worden ingevuld. ",
                "Het formaat is: ‘yyyy.mm.dd.xx’ of ‘yyyymmddxx’, waarbij ‘xx’ twee cijfers, ‘00’ of twee letters kan zijn. ",
                "Het mag met en zonder punten worden ingevuld. AWP slaat het ID-nummer op zonder punten. Ze worden toegevoegd bij het printen van het diploma en de cijferlijst.<br>",
                "Wanneer een kandidaat (nog) niet is ingeschreven in het bevolkingsregister, vul je in plaats van de laatste twee cijfers, twee letters in of '00'. ",
                "De letters of '00' aan het einde worden niet geprint op het diploma of de cijferlijst. <br>",
                "Elk ID-nummer kan maar eenmaal voorkomen op een school. Als er meerdere kandidaten zijn met dezelfde geboortedatum en die niet zijn ingeschreven in het bevolkingsregister, geef je ze verschillende letters aan het einde.</p>",

                "<p><b>Geboorteland</b> en <b>geboorteplaats</b><br> ",
                "Tenminste één van de velden 'Geboorteland' en 'Geboorteplaats' moet worden ingevuld. ",
                "Als ze allebei worden ingevuld wordt het op het diploma en cijferlijst weergegeven als '&lt;Geboorteland&gt;, &lt;Geboorteplaats&gt;'.</p>",
            ]),
        write_paragraph_body("img_exclamationsign",
            [
                "<p>LET OP:<br>Bij een kandidaat die vóór 10-10-2010 op Curaçao is geboren, moet als geboorteland 'Nederlandse Antillen' worden ingevuld en als geboorteplaats 'Curaçao'.</p>",

                "<p><b>Examennummer</b><br> ",
                "Het examennummer moet verplicht worden ingevuld. ",
                "Elk examennummer kan maar eenmaal voorkomen op een afdeling (Vsbo, Havo, Vwo) van de school.</p>",

                "<p><b>Leerweg</b> en <b>sector</b> of <b>profiel</b><br> ",
                "De leerweg en sector of het profiel moeten verplicht worden ingevuld.</p>",

                "<p><b>Extra faciliteiten</b><br> ",
                "Klik op dit veld wanneer de kandidaat gebruik maakt van extra faciliteiten, bijvoorbeeld in geval van dyslexie.<br>",
                "Op het Ex1-formulier en het Ex3-formulier wordt dan een asterisk (*-teken) achter de naam van de kandidaat gezet, ",
                "ten teken dat de kandidaat gebruik maakt van exctra faciliteiten.</p>",

                "<p><b>Bis-kandidaat</b><br> ",
                "Zet een vinkje bij dit veld wanneer een kandidaat vorig jaar al examen gedaan heeft op deze afdeling en - bij Vsbo- leerweg. <br>",
                "Een kandidaat wordt automatisch aangemerkt als bis-kandidaat wanneer AWP de vrijstellingen van vorig jaar ophaalt. ",
                "Zie de handleiding van de pagina <i>Cijfers</i>.</p>"
            ]),
        write_paragraph_body("img_exclamationsign",
            ["<p>LET OP:<br>Wanneer je het bis-examen wist worden ook de vrijstellingen van de kandidaat gewist.</p>"
            ]),
        write_paragraph_body("",
            ["<p><b>Aanvullend examen</b> of <b>Deelexamen</b><br> ",
                "Klik op dit veld wanneer de kandidaat geen volledig examen aflegt, maar slechts examen doet in 1 of meerdere vakken.</p>"
            ]),
        write_image("img_student_mod_addnew_ne"),

        write_paragraph_header("id_change_student", "Kandidaatgegevens wijzigen"),
        write_paragraph_body("",
            ["<p>Klik in de lijst met kandidaten op de naam van de kandidaat die je wilt wijzigen. Het venster met de kandidaatgegevens verschijnt nu.<br>",
            "Breng de wijzigingen aan en klik op <i>Opslaan</i>.</p>",

            "<p>Je kunt de velden <b>Extra faciliteiten</b> en <b>Bis-examen</b> ook wijzigen door in de lijst op het betreffende veld te klikken.</p>",

            "<p><b>Leerweg</b> of <b>sector</b> of <b>profiel</b> wijzigen<br> ",
                "Wanneer je de leerweg of sector of profiel wijzigt nadat de vakken van de kandidaat zijn ingevuld, ",
                "kan het zijn dat sommige vakken niet voorkomen in de nieuwe leerweg / sector / profiel. ",
                "Wanneer dit het geval is wist AWP deze vakken van de kandidaat. AWP geeft eerst een waarschuwing. ",
                "U dient de correcte vakken daarna toevoegen in de pagina <i>Vakken van kandidaten</i>.</p>"
            ]),

        write_paragraph_header("id_delete_student", "Kandidaat wissen"),
        write_paragraph_body("",
            ["<p>Selecteer de kandidaat door te klikken op het veld links van de achternaam. ",
            "Er verschijnt een zwart pijltje en de regel wordt grijs.<br>",
            "Klik vervolgens in de menubalk op de knop <i>Kandidaat wissen </i>. ",
            "AWP vraagt om te bevestigen dat de kandidaat gewist moet worden. Klik op <i>Ja, wis</i>.</p>",

            "<p>Wanneer een kandidaat nog geen vakken heeft, of wanneer de vakken van de kandidaat nog niet op een Ex1-formulier zijn ingediend, ",
            "worden de kandidaat en de vakken van de kandidaat gewist.</p>"
            ]),

        write_image("img_student_deleted"),

        write_paragraph_body("",
            ["<p><b>Kandidaat aanmerken om gewist te worden</b><br>",
            "Wanneer een kandidaat vakken heeft, die al op een Ex1-formulier zijn ingediend, ",
            "wordt de kandidaat en de vakken van de kandidaat niet meteen gewist, maar worden ze 'aangemerkt om gewist te worden'. ",
            "Dit wordt aangegeven met een dubbele rode streep door de naam van de kandidaat en de vakken van de kandidaat.</p>" ,

            "<p>De voorzitter en secretaris moeten de gewiste vakken van de kandidaat eerst goedkeuren in de pagina <i>Vakken van kandidaten</i> ",
            "en door middel van een aanvullend Ex1-formulier bij de Inspectie en het ETE indienen.<br>",
            "De kandidaat en de vakken worden gewist als het aanvullende Ex1-formulier is ingediend.</p>",

            "<p>Je kunt wachten met het indienen van het aanvullende Ex1-formulier totdat je op het punt staat de SE-cijfers in te voeren. ",
            "Op deze manier worden alle wijzigingen in één aanvullend Ex1-formulier ingediend.</p>",

            "<p><b>Kandidaat herstellen</b><br>",
            "Wanneer een kandidaat is aangemerkt om gewist te worden, kun je dit ongedaan maken. ",
            "Selecteer een kandidaat die is aangemerkt om gewist te worden en klik in de menubalk op de knop <i>Kandidaat herstellen</i>. De kandidaat en de vakken van de kandidaat worden nu hersteld. ",
            "Herstelde vakken hoeven niet opnieuw ingediend te worden.",

            "<p class='mb-0 pb-0'><b>Gewiste kandidaat herstellen</b><br>",
            "Als een kandidaat is gewist kun je dit als volgt herstellen:</p>",
            "<ul class='manual_bullet mb-0'><li>Klik in de verticale grijze balk links op <i>Alle kandidaten weergeven</i>. De gewiste kandidaten worden nu ook weergegeven. Ze hebben een rode achtegrond.</li>",
            "<li>Selecteer de gewiste kandidaat die je wilt herstellen.</li>",
            "<li>Klik in de menubalk op de knop <i>Kandidaat herstellen</i>.</li></ul>",
            "<p>De gewiste kandidaat en de vakken van de kandidaat worden nu hersteld.</p>"
            ]),

        write_paragraph_header("id_download_students", "Kandidaatgegevens downloaden"),
        write_paragraph_body("",
            ["<p>Klik in de menubalk op de knop <i>Kandidaatgegevens downloaden</i>. ",
            "Er wordt nu een Excel bestand gedownload met alle kandidaten van deze afdeling.</p>"
            ]),

        "<div class='p-3 visibility_hide'>-</div>",
    ],

en:  [
        write_paragraph_header("id_intro", "Candidates"),
         write_paragraph_body("",
             ["<p>Click the <i>Candidates</i> button in the page bar. The <i>Candidates</i> page below will open.</p>",
                 "<p class='pb-0'>In this page you can:</p>",
                 "<ul class='manual_bullet mb-0'><li>Upload candidates. ",
             // from https://pagedart.com/blog/single-quote-in-html/
                 "Click <a href='#' class='awp_href' onclick='LoadPage(&#39upload&#39)'>here</a> to go to its manual;</li>",
                 "<li>Add and delete candidates;</li>",
                 "<li>Change candidate data;</li>",
                 "<li>Download an Excel file with candidate data.</li></ul>"
             ]),

        write_paragraph_header("id_filter_students", "Filter Candidates"),
         write_paragraph_body("",
             ["<p>On each line in the table is a candidate. ",
                 "You can display all candidates, but if there are many candidates it is more convenient to filter candidates.</p>",

                 "<p class='pb-0'>Filtering can be done in different ways:</p>",
                 "<ul class='manual_bullet mb-2'><li>In the vertical gray bar on the left side of the page you can ",
                 "select a <b>learning path</b>, <b>sector</b> or <b>profile</b> or <b>candidate</b>;</li>",
                 "<li>You can also filter candidates using the <b>filter row</b>. Click <a href='#' class='awp_href' onclick='LoadPage(&#39home&#39, &#39id_filterrow&#39)'>here</a> to go to the filter row manual.</li></ul>",
             ]),

        write_image("img_student_page_en"),

        write_paragraph_header("id_add_student", "Add a candidate"),
         write_paragraph_body("",
             ["<p>Click the <i>Add candidate</i> button in the menu bar. The <i>Add candidate</i> window below will now appear. ",
                 "In this window you can enter the candidate's personal data and general enrollment data.</p>",

                 "<p><b>Last name, first names, prefix</b><br> ",
                 "Enter the name of the candidate here. The fields 'Last name' and 'First names' are mandatory.<br>",
                 "Make sure that the name is written exactly the same as registered in the basic administration.<br>",
                 "The 'Prefix' field is there to display candidates in the correct alphabetical order. ",
                 "When you enter 'van Aanholt' in the 'Last name' field, it will be displayed under the 'V', ",
                 "but if you put 'Aanholt' in the 'Last name' and 'van' in the 'Prefix', the name will appear under the 'A'.</p>",

                 "<p><b>Special characters</b><br> ",
                 "Click the <i>Enter special characters</i> button at the bottom left of the window to display the list of special characters. ",
                 "Click on the relevant character to enter it.</p>",

                 "<p><b>ID number</b><br> ",
                 "Enter the candidate's ID number here. It is mandatory. ",
                 "The format is: 'yyyy.mm.dd.xx' or 'yyyymmddxx', where 'xx' can be two digits, '00' or two letters. ",
                 "It may be entered with or without dots. AWP stores the ID number without dots. They are added when printing the diploma and grade list.<br>",
                 "If a candidate is not (yet) registered in the basic administration, enter two letters or '00' instead of the last two digits. ",
                 "The letters or '00' at the end will not be printed on the diploma or grade list. <br>",
                 "Each ID number can only appear once in a school. If there are several candidates with the same date of birth, who are not registered in the basic administration, give them different letters at the end.</p>",

                 "<p><b>Country of birth</b> and <b>place of birth</b><br> ",
                 "At least one of the fields 'Country of birth' and 'Place of birth' must be completed. ",
                 "If both are filled in, it will appear on the diploma and grade list as '&lt;Country of birth&gt;, &lt;Place of birth&gt;'.</p>",
             ]),

             write_paragraph_body("img_exclamationsign",
                ["<p>PLEASE NOTE:<br>For a candidate who was born on Sint Maarten before 10-10-2010, the country of birth must be entered as 'Netherlandse Antillen' and as the place of birth 'Sint Maarten'.</p>",

                 "<p><b>Exam number</b><br> ",
                 "The exam number must be filled in. ",
                 "Each exam number can only occur once in a department (Vsbo, Havo, Vwo) of the school.</p>",

                 "<p><b>Learning path</b> and <b>sector</b> or <b>profile</b><br> ",
                 "The learning path and sector or profile must be completed.</p>",

                 "<p><b>Extra facilities</b><br> ",
                 "Click on this field if the candidate uses extra facilities, for example in case of dyslexia.<br>",
                 "On the Ex1 form and the Ex3 form, an asterisk (* sign) will be placed after the candidate's name, ",
                 "to indicate that the candidate uses extra facilities.</p>",

                 "<p><b>Bis candidate</b><br> ",
                 "Tick this box if a candidate has already taken an exam last year in this department and - at Vsbo - leerweg. <br>",
                 "A candidate is automatically classified as bis-candidate when AWP collects last year's exemptions. ",
                 "See the <i>Grades</i> page manual.</p>"
             ]),

        write_paragraph_body("img_exclamationsign",
             ["<p>NOTE:<br>When you delete the bis exam, the candidate's exemptions are also deleted.</p>"
             ]),
         write_paragraph_body("",
             ["<p><b>Additional exam</b> or <b>Partial exam</b><br> ",
                 "Click on this field if the candidate does not take a full exam, but only takes exams in 1 or more subjects.</p>"
             ]),
         write_image("img_student_mod_addnew_en"),

         write_paragraph_header("id_change_student", "Change candidate data"),
         write_paragraph_body("",
             ["<p>In the list of candidates, click on the name of the candidate you want to change. The window with the candidate data will now appear.<br>",
             "Make the changes and click <i>Save</i>.</p>",

             "<p>You can also change the <b>Extra facilities</b> and <b>Bis exam</b> fields by clicking on the relevant field in the list of candidates.</p>",

             "<p>Changing the <b>Learning path</b> or <b>sector</b> or <b>profile</b><br> ",
                 "When you change the learning path or sector or profile after the candidate's subjects have been completed, ",
                 "it may be that some subjects are not included in the new learning path / sector / profile.",
                 "When this is the case, AWP clears these subjects from the candidate. AWP issues a warning first.",
                 "You must then add the correct subjects in the page <i>Subjects of candidates</i>.</p>"
             ]),

            write_paragraph_header("id_delete_student", "Delete a candidate"),
            write_paragraph_body("",
             ["<p>Select the candidate by clicking on the field to the left of the last name. ",
             "A black arrow appears and the line turns gray.<br>",
             "Then click on the <i>Delete candidate</i> button in the menu bar. ",
             "AWP asks to confirm that the candidate should be deleted. Click <i>Yes, delete</i>.</p>",

             "<p>When a candidate has no subjects yet, or when the candidate's subjects have not yet been submitted on an Ex1 form, ",
             "the candidate and the candidate's subjects are deleted.</p>"
             ]),

         write_image("img_student_deleted"),

         write_paragraph_body("",
             ["<p><b>Mark a candidate to be deleted</b><br>",
             "When a candidate has subjects that are already submitted on an Ex1 form, ",
             "the candidate and the candidate's subjects are not deleted immediately, but are 'marked to be deleted'. ",
             "This is indicated by a double red line through the candidate's name and the candidate's subjects.</p>" ,

             "<p>The chairperson and secretary must first approve the deleted candidate's subjects in the <i>Subjects of candidates</i> page ",
             "and submit them to the Inspectorate and the Division of Examinations by means of an supplementary Ex1 form.<br>",
             "The candidate and the subjects will be deleted when the supplementary Ex1 form is submitted.</p>",

             "<p>You can wait to submit the supplementary Ex1 form until you are about to enter the SE grades. ",
             "In this way, all changes will be submitted in one supplementary Ex1 form.</p>",

             "<p><b>Restore a candidate</b><br>",
             "When a candidate is marked to be deleted, you can undo it. ",
             "Select a candidate marked to be deleted and click the <i>Restore candidate</i> button in the menu bar. The candidate and the candidate's subjects will now be restored.",
             "Restored subjects do not need to be resubmitted.",

             "<p class='mb-0 pb-0'><b>Restoring a deleted candidate</b><br>",
             "If a candidate has been deleted, you can restore it as follows:</p>",
             "<ul class='manual_bullet mb-0'><li>In the vertical gray bar on the left, click <i>Show all candidates</i>. The deleted candidates are now also displayed. They have a red background.</ li>",
             "<li>Select the deleted candidate you want to restore.</li>",
             "<li>Click the <i>Restore candidate</i> button in the menu bar.</li></ul>",
             "<p>The deleted candidate and the candidate's subjects are now restored.</p>"
             ]),

         write_paragraph_header("id_download_students", "Download candidate data"),
         write_paragraph_body("",
             ["<p>In the menu bar, click the <i>Download candidate data</i> button. ",
             "An Excel file is now being downloaded with all candidates from this department.</p>"
             ]),

        "<div class='p-3 visibility_hide'>-</div>",
     ]
}
