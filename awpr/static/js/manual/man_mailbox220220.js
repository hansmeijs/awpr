// PR2021-10-23 added

    "use strict";

const man_mailbox = {

/////////  NEDERLANDS //////////////////////////////
    nl: [
        write_paragraph_header("id_intro_mailbox", "Berichten service"),
        write_paragraph_body("",
            [ "<p>De berichtenservice is een nieuw onderdeel van AWP, waarmee je berichten kunt versturen naar andere gebruikers van AWP-online. ",
                "Dit kunnen berichten zijn aan het ETE, aan de Inspectie of aan andere gebruikers van je school of van andere scholen. ",
                "Het ETE zal deze berichtenservice voortaan gebruiken voor het versturen van informatie over de examens.</p>",
                "<p>De berichten kun je vinden in de tab <i>Ontvangen berichten</i> op de berichtenpagina. Klik op de envelop rechts boven in de titelbalk om naar deze pagina te gaan. ",
                "Wanneer je een bericht hebt verzonden stuurt AWP een e-mail naar alle geadresseerden met de mededeling dat er een bericht voor ze is.</p>"
            ]),
        write_paragraph_body("img_exclamationsign",
            ["<p>De berichtenservice is alleen voor mededelingen van algemene aard. ",
                "Voor de communicatie met de Inspectie en het ETE over individuele kandidaten wordt er een rubriek <i>Opmerkingen</i> toegevoegd in de pagina's 'Cijfers', 'Vakken' en 'Kandidaten'. ",
                "Deze optie is op dit moment nog niet beschikbaar.</p>"]),

        write_paragraph_header("id_mailbox_read_message", "Berichten lezen"),
        write_paragraph_body("img_envelope_0_2",
            ["<p>Wanneer er een nieuw bericht voor je is, verschijnt er een icoontje met een witte envelop en een rode vlag rechts boven in de titelbalk. ",
            "Klik hierop om het bericht te openen.<br>",
            "Als je een nieuw bericht opent wordt het gemarkeerd als 'gelezen'. Het icoontje met de witte envelop en de rode vlag verdwijnt. ",
            "Je kunt een bericht ook handmatig als 'gelezen' markeren. Klik dan op het icoontje met de witte envelop. ",
            "Wanneer je nog een keer klikt wordt het bericht weer als 'niet gelezen' gemarkeerd.</p>",

            "<p><b>Een bericht openen</b><br>",
            "Klik op de titel van het bericht om het te openen. Het onderstaande venster verschijnt. ",
            "Wanneer de tekst van het bericht groter is dan het kader waarin het staat, kun je de rechter onder hoek van het kader naar beneden slepen om het kader te vergroten.</p>",

            "<p><b>Bijlagen downloaden</b><br>",
            "Onder de tekst van het bericht staan de bijlagen. Klik op een bijlage om hem te downloaden. De bijlage wordt in een apart venster weergegeven. ",
            "Als je de bijlage wilt opslaan kun je in het venster met de bijlage op de rechter muisknop klikken. In het venster dat verschijnt klik je op <i>Opslaan als...</i>.</p>",

            "<p><b>Geadresseerden weergeven</b><br>",
            "Klik in het kader met <i>Geadresseerden</i>. De lijst met geadresseerden van dit bericht wordt nu weergegeven. Nog een keer klikken en de lijst wordt gesloten.</p>"

            ]),
        write_paragraph_body("img_delete_0_2",
            ["<p><b>Een bericht verwijderen</b><br>",
            "Klik het icoontje met het kruis rechts in de regel van een bericht om het te verwijderen.</p>",

            "<p><b>Verwijdering ongedaan maken</b><br>",
            "Je kunt een verwijderd bericht als volgt terughalen:<br>",
            "Klik rechts in de filterregel (dat is de tweede grijze regel van de tabel) op het icoontje met het kruis. ",
            "Alle verwijderde berichten worden nu weergegeven. Ze hebben een icoontje met een rood kruis.<br>",
            "Klik op het icoontje met het kruis om de verwijdering ongedaan te maken.</p>"
            ]),

        set_image_div("img_mailbox_read_message_ne"),

        write_paragraph_header("id_mailbox_create_message", "Een bericht aanmaken"),
        write_paragraph_body("",
            ["<p>Klik in de menubalk op <i>Nieuw bericht aanmaken</i>. Het onderstaande venster verschijnt.</p>",

                "<p><b>Geadresseerden</b><br>",
                "Links in het venster staan de kaders met geadresseerden. In de volgende paragraaf wordt uitgelegd hoe je geadresseerden kunt toevoegen.</p>",

                "<p><b>Titel van het bericht</b><br>",
                "In de bovenste regel van het rechter kader vul je de titel van het bericht in. De titel moet ingevuld worden en kan maximaal 80 tekens bevatten. ",
                "De titel wordt weergegevens in de lijst met berichten en in de e-mail die wordt verstuurd naar de geadresseerden.</p>",

                "<p><b>De tekst van het bericht</b><br>",
                "In de tweede regel van het rechter kader vul je de tekst van het bericht in. De tekst kan maximaal 2.000 tekens bevatten. ",
                "Het is niet mogelijk om in de tekst het lettertype te wijzigen, vetgedrukte of cursieve tekst weer te geven of afbeeldingen toe te voegen. ",
                "In dat geval kun je een PDF bestand of Word document met het bericht als bijlage toevoegen.</p>",

                "<p><b>Bijlagen</b><br>",
                "Klik onderaan in het kader rechts op de knop <i>Bijlage toevoegen</i>. Het venster <i>Open bestand</i> verschijnt. ",
                "Selecteer het bestand dat je als bijlage wilt toevoegen en klik op <i>Open</i>. ",
                "Het bestand wordt nu naar de server geüpload. De naam van de bijlage verschijnt in een apart kader onder de tekst van het bericht. ",
                "Klik op de naam van de bijlage om de bijlage te downloaden. ",
                "Klik op de knop met het kruis achter de naam van de bijlage om de bijlage te verwijderen.</p>",

                "<p><b>Een concept bericht opslaan</b><br>",
                "Klik op <i>Opslaan</i> om het concept bericht op te slaan, zonder dat het wordt verstuurd. ",
                "Je kunt het bericht opnieuw openen door op de tab <i>Concept berichten</i> te klikken en vervolgens op de titel van het concept bericht te klikken.</p>",

                "<p><b>Een bericht verzenden</b><br>",
                "Klik op <i>Verzenden</i>. AWP stuurt nu het bericht naar alle geadresseerde gebruikers. ",
                "Alleen de gebruikers van wie de account geactiveerd en niet niet-actief is, ontvangen het bericht. ",
                "AWP stuurt ook een e-mail naar alle geadresseerde gebruikers, met de mededeling dat er een bericht voor ze is.<br>",
                "Na het verzenden van de e-mails wordt er een logbestand gedownload met de namen van de geadresseerden.</p>"

            ]),
        set_image_div("img_mailbox_create_message_ne"),

        write_paragraph_header("id_mailbox_recipients", "Geadresseerden"),
        write_paragraph_body("",
            ["<p class='pb-0'>Je kun op drie verschillende manieren de geadresseerden voor een bericht selecteren:</p>",
                "<ul class='manual_bullet mb-0'><li>door een of meer verzendlijsten te selecteren</li>",
                "<li>door een of meer organisaties te selecteren </li>",
                "<li>door individuele gebruikers te selecteren.</li></ul>",
                "<p>Elke gebruiker krijgt het bericht maar eenmaal, ook al komt de gebruiker voor in meerdere selecties.<br>",
                "AWP stuurt één e-mail per organisatie met de mededeling dat er een bericht klaar staat. ",
                "Alle geselecteerde gebruikers van deze organisatie ontvangen die e-mail.</p>",

                "<p><b>Versturen naar verzendlijst</b><br>",
                "In de volgende paragraaf wordt uitgelegd hoe je een verzendlijst kunt aanmaken. ",
                "Het selecteren van verzendlijsten gaat zoals hieronder bij het versturen naar organisaties is beschreven.</p>",

                "<p><b>Versturen naar organisaties</b><br>",
                "Met organisaties worden de scholen bedoeld, maar ook het ETE, de Inspectie en de Afdeling gecommiteerden zijn een organisatie.<br>",
                "Klik op <i>Verstuur naar organisaties...</i>. Het onderstaande venster <i>Selecteer organisatie</i> verschijnt. ",
                "In de blauwe lijst links staan de geselecteerde organisaties, in de rechter lijst staan de beschikbare organisaties.<br>",
                "Klik op een organisatie in een van de lijsten om hem naar de andere lijst te verplaatsen. ",
                "Klik op <i>Sluiten</i> of klik ergens buiten het venster om dit venster te sluiten. ",
                "De geselecteerde organisaties staan nu in de lijst <i>Verstuur naar organisaties...</i>.</p>",
                "<p>Als je het bericht ook naar organisaties op Sint Maarten wilt sturen, zet je een vinkje bij <i>Inclusief organisaties van Sint Maarten</i>, ",
                "In de lijst met beschikbare organisaties worden nu ook de organisaties van Sint Maarten weergegeven.</p>"
            ]),
        set_image_div("img_mailbox_select_items_ne"),

        write_paragraph_body("",
            ["<p><b>Alleen naar gebruikersgroep...</b><br>",
                "Als je het bericht niet naar alle gebruikers van een organisatie wilt sturen, ",
                "maar bijvoorbeeld alleen naar de voorzitter en secretaris, ",
                "kun je klikken op <i>Alleen naar gebruikersgroep...</i> ",
                "om de gewenste gebruikersgroepen te selecteren.<br>",
                "Als er geen gebruikersgroepen zijn geselecteerd wordt het bericht naar alle gebruikers van de organisatie gestuurd.<br>",
                "Als er meerdere organisaties zijn geselecteerd, is de selectie van gebruikersgroepen van toepassing op alle geselecteerde organisaties.</p>"
            ]),
        write_paragraph_body("",
            ["<p><b>Verstuur naar gebruikers</b><br>",
                "Klik op <i>Verstuur naar gebruikers...</i> om individuele gebruikers toe te voegen aan de lijst met geadresseerden. ",
                "Het gaat op dezelfde manier als bij het versturen naar organisaties.</p>"
            ]),

        write_paragraph_header("id_mailbox_mailinglist", "Verzendlijsten"),
        write_paragraph_body("",
            [ "<p>Wanneer je regelmatig berichten verstuurt naar dezelfde organisaties of gebruikers, ",
            "is het handig om een verzendlijst aan te maken. ",
            "Bij het aanmaken van een nieuw bericht selecteer je dan een verzendlijst in plaats van organisaties of gebruikers.<br>",
            "In aanvulling op de verzendlijst kun je nog steeds organisaties of gebruikers selecteren. ",
            "Elke gebruiker ontvangt het bericht slechts eenmaal, dus het is geen probleem wanneer een gebruiker meerdere keren voorkomt in de lijst.</p>"
            ]),
        write_paragraph_body("",
            ["<p><b>Verzendlijst aanmaken</b><br>",
             "Klik in de menubalk op <i>Verzendlijst aanmaken</i>. Het onderstaande venster verschijnt.</p>",
            "<p>In de bovenste regel vul je de naam van de verzendlijst in. De naam moet ingevuld worden en kan maximaal 80 tekens bevatten.</p>",
            "<p>Het toevoegen van organisaties en gebruikers aan de verzendlijst gaat op dezelfde manier als bij het aanmaken van een bericht.</p>",
            "<p><b>Verzendlijst wijzigen of wissen</b><br>",
            "Als je een verzendlijst wilt wijzigen of wissen klik je op de naam van de betreffende verzendlijst. ",
            "Wijzig de gegevens en klik op <i>Opslaan</i> of klik op <i>Verzendlijst wissen</i>.</p>",
            "<p><b>Verzendlijst voor algemeen gebruik</b><br>",
            "Als je wilt dat een verzendlijst ook door de andere gebruikers van je organisatie gebruikt kan worden, ",
            "zet je een vinkje bij <i>Beschikbaar voor alle gebruikers van deze organisatie</i>. ",
            "Een verzendlijst voor algemeen gebruik kan alleen gewijzigd of gewist worden ",
            "door de gebruiker die hem heeft aangemaakt of door je systeembeheerder.</p>",

            "<p><b>Organisaties of gebruikers van Sint Maarten toevoegen</b><br>",
            "Zet je een vinkje bij <i>Inclusief gebruikers van Sint Maarten</i> ",
            "als je ook organisaties of gebruikers van Sint Maarten wilt toevoegen aan de verzendlijst. ",
            "Wanneer je het vinkje weghaalt worden alle organisaties of gebruikers van Sint Maarten van de lijst met geselecteerden verwijderd.</p>"
            ]),
        set_image_div("img_mailbox_mailinglist_ne"),

        "<div class='p-3 visibility_hide'>-</div>",
    ],
/////////  ENGLISH //////////////////////////////
    en:  [
        write_paragraph_header("id_intro", "Messaging service"),
        write_paragraph_body("",
            ["<p>The messaging service is a new feature of AWP, which allows you to send messages to other users of AWP-online. ",
                 "These can be messages to the Division of Examinations, to the Inspectorate or to other users of your school or other schools. ",
                 "From now on, the Division of Examinations will this messaging service to send information about the exams.</p>",
                 "<p>The messages can be found in the <i>Received messages</i> tab on the message page. ",
                 "Click on the envelope in the upper right corner of the title bar to go to this page. ",
                 "When you have sent a message, AWP sends an email to all recipients informing them that there is a message for them.</p>"]),
        write_paragraph_body("img_exclamationsign",
            ["<p>The messaging service is for communications of a general nature only. ",
             "For communication with the Inspectorate and the Division of Examinations about individual candidates, ",
             "a section <i>Remarks</i> will be added in the pages 'Grades', 'Subjects' and 'Candidates'. ",
             "This option is not yet available.</p>"]),

        write_paragraph_header("id_mailbox_read_message", "Read messages"),
        write_paragraph_body("img_envelope_0_2",
        ["<p>When there is a new message for you, an icon with a white envelope and a red flag will appear in the top right corner of the title bar. ",
                    "Click to open the message.<br>",
                    "When you open a new message it will be marked as 'read'. The icon with the white envelope and the red flag disappears. ",
                    "You can also manually mark a message as 'read'. Click on the icon with the white envelope. ",
                    "When you click again, the message will be marked as 'not read' again.</p>",

                    "<p><b>Open a message</b><br>",
                    "Click on the title of the message to open it. The window below will appear. ",
                    "When the text of the message is larger than the frame it appears in, you can drag the bottom right corner of the frame down to enlarge the frame.</p>",

                    "<p><b>Download attachments</b><br>",
                    "Below the text of the message are the attachments. Click on an attachment to download it. The attachment will be displayed in a separate window. ",
                    "If you want to save the attachment, you can click the right mouse button in the attachment window. In the window that appears, click <i>Save As...</i>.</p>",

                    "<p><b>Show recipients</b><br>",
                    "Click in the box with <i>Recipients</i>. The list of recipients of this message will be displayed. Click again and the list will close.</p>"

            ]),
        set_image_div("img_mailbox_read_message_en"),

        write_paragraph_header("id_mailbox_create_message", "Create a message"),
        write_paragraph_body("",
            ["<p>Click <i>Create new message</i> in the menu bar. The window below will appear.</p>",

                "<p><b>Recipients</b><br>",
                "On the left side of the window are the boxes with recipients. The next section explains how to add recipients.</p>",

                "<p><b>The title of the message</b><br>",
                "Enter the title of the message in the top line of the right frame. The title cannot be blank and may contain up to 80 characters. ",
                "The title will be displayed in the message list and in the email sent to the recipients.</p>",

                "<p><b>The text of the message</b><br>",
                "In the second line of the right frame, enter the text of the message. The text can contain a maximum of 2,000 characters. ",
                "It is not possible to change the font, display bold or italic text or add images in the text. ",
                "In that case you can add a PDF file or Word document with the message as an attachment.</p>",

                "<p><b>Attachments</b><br>",
                "Click the <i>Add attachment</i> button at the bottom right of the box. The <i>Open File</i> window will appear. ",
                "Select the file you want to add as an attachment and click <i>Open</i>. ",
                "The file will now be uploaded to the server. The name of the attachment will appear in a separate box below the text of the message. ",
                "Click on the attachment name to download the attachment. ",
                "Click the cross button next to the attachment name to delete the attachment.</p>",

                "<p><b>Save a draft message</b><br>",
                "Click <i>Save</i> to save the draft message without sending it. ",
                "You can reopen the message by clicking the <i>Draft Messages</i> tab and then clicking the title of the draft message. </p>",

                "<p><b>Send a message</b><br>",
                "Click <i>Send</i>. AWP will now send the message to all recipients. ",
                "Only the users whose account is activated and not inactive will receive the message. ",
                "AWP also sends an email to all recipients, informing them that they have received a message.<br>",
                "After sending the emails, a logfile will be downloaded with the names of the recipients.</p>"
                ]),
        set_image_div("img_mailbox_create_message_en"),

        write_paragraph_header("id_mailbox_recipients", "Recipients"),
        write_paragraph_body("",
            ["<p class='pb-0'>You can select the recipients for a message in three different ways:</p>",
                "<ul class='manual_bullet mb-0'><li>by selecting one or more mailing lists</li>",
                "<li>by selecting one or more organizations </li>",
                "<li>by selecting individual users.</li></ul>",
                "<p>Each user gets the message only once, even if the user appears in multiple selections.<br>",
                "AWP also sends an email to all recipients, informing them that they have received a message.</p>",

                "<p><b>Send to mailing list</b><br>",
                "The next section explains how to create a mailing list. ",
                "Selecting mailing lists is done as described below when sending to organizations.</p>",

                "<p><b>Send to organizations</b><br>",
                "Organizations mean the schools, but Division of Examinations, the Inspectorate and the Department of Committees are also an organization.<br>",
                "Click on <i>Send to organizations...</i>. The <i>Select organization</i> window below will appear. ",
                "The blue list on the left shows the selected organizations, the right list shows the available organizations.<br>",
                "Click on an organization in one of the lists to move it to the other list. ",
                "Click <i>Close</i> or click anywhere outside the window to close this window. ",
                "The selected organizations are now in the list <i>Send to organizations...</i>.</p>",
                "<p>If you also want to send the message to organizations on Curaçao, check <i>Include organizations of Curaçao</i>, ",
                "The organizations of Curaçao are now also displayed in the list of available organizations.</p>"
            ]),
        set_image_div("img_mailbox_select_items_en"),
        write_paragraph_body("",
            ["<p><b>Only to user group...</b><br>",
                "If you don't want to send the message to all users of an organization, ",
                "but, for example, only to the chairman and secretary, ",
                "you can click <i>Only to user group...</i> ",
                "to select the desired user groups.<br>",
                "If no user groups are selected, the message will be sent to all users of the organization.<br>",
                "If multiple organizations are selected, the user group selection will apply to all selected organizations.</p>"
            ]),
        write_paragraph_body("",
            ["<p><b>Send to users</b><br>",
                "Click <i>Send to Users...</i> to add individual users to the recipient list. ",
                "It works the same as when sending to organizations.</p>"
            ]),

        write_paragraph_header("id_mailbox_mailinglist", "Mailing lists"),
        write_paragraph_body("",
            [ "<p>When you regularly send messages to the same organizations or users, ",
            "it is useful to create a mailing list. ",
            "When creating a new message, select a mailing list instead of organizations or users.<br>",
            "In addition to the mailing list, you can still select organizations or users. ",
            "Each user will receive the message only once, so it is not a problem if a user appears several times in the list.</p>"
            ]),
        write_paragraph_body("",
            ["<p><b>Create mailing list</b><br>",
             "Click <i>Create Mailing List</i> in the menu bar. The window below will appear.</p>",
            "<p>In the top line you enter the name of the mailing list. The name must be entered and can contain a maximum of 80 characters.</p>",
            "<p>Adding organizations and users to the mailing list is done in the same way as when creating a message.</p>",
            "<p><b>Change or delete mailing list</b><br>",
            "If you want to change or delete a mailing list, click on the name of the relevant mailing list. ",
            "Change the details and click <i>Save</i> or click <i>Delete Mailing List</i>.</p>",

            "<p><b>Mailing lists for general use </b><br>",
            "If you want a mailing list to be available to the other users of your organization, ",
            "check <i>Available to all users of this organization</i>. ",
            "A general purpose mailing list can only be changed or deleted ",
            "by the user who created it or by your system administrator.</p>",

            "<p><b>Add organizations or users of Curaçao</b><br>",
            "Tick the box <i>Include users from Curaçao</i> ",
            "if you also want to add organizations or users of Curaçao to the mailing list. ",
            "When you uncheck the box, all organizations or users of Curaçao will be removed from the list of selected people.</p>"
            ]),
        set_image_div("img_mailbox_mailinglist_en"),
        "<div class='p-3 visibility_hide'>-</div>",
        ]
}
