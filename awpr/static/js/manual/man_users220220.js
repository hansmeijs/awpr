// PR2022-02-11 added

    "use strict";

const man_users = {

/////////  NEDERLANDS //////////////////////////////
    nl: [
        write_paragraph_header("id_intro", "Gebruikers"),

        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>AWP-online maakt gebruik van een geavanceerd systeem van gebruikers en gebruikersrechten (permissies). ",
                "Dit is nodig omdat de beveiliging van de gegevens van groot belang is en omdat er veel verschillende soorten gebruikers zijn, ",
                "die allemaal op verschillende manieren gebruik maken van AWP-online en toegang hebben tot verschillende onderdelen van het programma.</p>",
                "<p>Het aanmaken van gebruikers accounts en toekennen van permissies gebeurt door de organisatie zelf. ",
                "Alleen een gebruiker die tot de gebruikersgroep 'Systeembeheerder' behoort kan gebruikers accounts aanmaken en wijzigen.</p>",
                "<p>In deze paragraaf wordt uitgelegd hoe het beheren van de gebruikers accounts en hun permissies in zijn werk gaat.</p>",
            "</div>",
        "</div>",

        write_paragraph_header("id_user_login", "Inloggen"),
        "<div class='mfc mb-4'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",

                "<p>Klik op <i>Login</i> rechts boven in het scherm. ",
                "Vul je schoolcode, gebruikersnaam en wachtwoord in en klik op <i>Inloggen</i>.</p>",
                "<p>Wanneer de inloggegevens niet correct zijn ingevuld, verschijnt er een foutmelding. Probeer het opnieuw. ",
                "Let erop dat het wachtwoord hoofdlettergevoelig is. De schoolcode en gebruikersnaam zijn niet hoofdlettergevoelig.</p>",
                "<p class='mb-0 pb-0'>Als het niet lukt om in te loggen kan dat verschillende oorzaken hebben:</p>",
                "<ul class='manual_bullet'><li>Je bent al ingelogd. Klik dan op het AWP logo links boven in het venster.</li>",
                "<li>Een andere gebruiker is al ingelogd in deze browser. Sluit de browser, open de browser opnieuw en log in.</li>",
                "<li>Je browser accepteert geen cookies. Wijzig de instelling van de browser.</li></ul></p>",

                "<p><b>Wachtwoord vergeten</b><br>Klik op <i>Wachtwoord vergeten?</i> onderaan het inlog venster als je je wachtwoord bent vergeten. ",
                 "AWP stuurt dan een e-mail naar het e-mail adres van de gebruiker. De e-mail bevat een link. Klik hierop om naar de pagina te gaan, waar je je wachtwoord kunt wijzigen.</p>",
            "</div>",
        "</div>",

        write_paragraph_header("id_user_manage", "Gebruikersaccount beheren"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p><b>Gebruikerspagina openen</b><br>Klik op je gebruikersnaam rechts boven in het scherm. ",
                 "Als je systeembeheerder bent staat er een knop <i>Gebruikers</i> onder je naam. ",
                 "Klik hierop en de onderstaande pagina 'Gebruikers' wordt geopend.<p>",
            "</div>",
        "</div>",
        write_image("img_users_tbl_users_ne"),

        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p><b>Gebruikersaccount toevoegen</b><br>Klik in de menubalk op <i>Gebruiker toevoegen</i>. Het venster <i>Gebruiker toevoegen</i> verschijnt. ",
                "Vul de gebruikersnaam, volledige naam van de gebruiker en het e-mail adres in.</p>",
                "<p>De gebruikersnaam wordt gebruikt om in te loggen. De volledige naam wordt gebruikt in officiële documenten zoals het diploma, cijferlijst en Ex-formulieren. ",
                " De gebruikersnaam, volledige naam en e-mail-adres moeten uniek zijn binnen de organisatie. ",
                 "Dezelfde gebruikersnaam en e-mail adres mogen wel gebruikt worden bij een andere organisatie, bijvoorbeeld wanneer een gebruiker tevens gecommiteerde is bij een ander school.</p>",

                 "<p><b>Activeringslink</b><br>Nadat je geklikt heb op <i>Gebruikersaccount aanmaken</i> verstuurt AWP een e-mail naar de gebruiker om het e-mail adres te verifiëren. ",
                "De e-mail bevat een link waarmee de nieuwe gebruiker een wachtwoord kan aanmaken en kan inloggen. ",
                "Zodra de gebruiker een wachtwoord heeft aangemaakt is de account geactiveerd.</p>",
                "<p>De activeringslink blijft zeven dagen geldig. Je kunt zo nodig een nieuwe activeringslink versturen. ",
                "Klik in de kolom <i>Geactiveerd</i> en klik in het venster dat verschijnt op <i>Activeringslink versturen</i>.</p>",

                 "<p><b>Gebruiker gegevens wijzigen</b><br>Klik op de naam van de gebruiker. Er verschijnt een scherm waarin je de gegevens van de gebruiker kunt wijzigen. Klik op <i>Opslaan</i> om de wijzigingen op te slaan. ",

                 "<p><b>Gebruikersaccount wissen</b><br>Selecteer een gebruiker en klik in de menubalk op <i>Gebruiker wissen</i>. Er verschijnt een scherm om te bevestigen dat de gebruiker wordt gewist. Klik op <i>Ja, wis</i>. ",
                 "Wanneer een gebruiker gegevens heeft ingevoerd kun je de account niet meer wissen. In plaats daarvan kun je de account 'Niet-actief' maken.",

                 "<p><b>Gebruikersaccount niet-actief maken</b><br>Klik in de kolom <i>Niet actief</i> van een gebruiker. Er verschijnt een scherm om te bevestigen dat de gebruiker 'Niet-actief' wordt gemaakt. Klik op <i>Ja, maak niet-actief</i>. ",
                  "Het icoontje wordt nu zwart. De gebruiker kan nu niet meer inloggen.",
                  "Klik op het zwarte icoontje om een gebruiker weer actief te maken.</p>",

            "</div>",
        "</div>",

        write_paragraph_header("id_user_permissions", "Permissies"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>Klik in de pagina <i>Gebruikers</i> in de horizontale zwarte balk op de tab <i>Gebruikersgroepen</i>. ",
                "Er verschijnt een lijst met de gebruikers en de gebruikersgroepen waartoe de gebruiker behoort. ",
                "Er staat een vinkje in de kolommen van de gebruikersgroepen waartoe de gebruiker behoort.</p>",

                "<p><b>Gebruikersgroepen toewijzen en verwijderen</b><br>Klik in de kolom van een gebruikersgroep om de gebruikersgroep toe te wijzen aan de gebruikersaccount. ",
                "Klik op een vinkje om de gebruikersgroep te verwijderen.</p>",

                 "<p class='mb-0 pb-0'>AWP kent de volgende gebruikersgroepen:</p>",
                "<ul class='manual_bullet'><li><b>Alleen lezen</b>. Deze gebruikersgroep kan de pagina's inzien, maar geen gegevens wijzigen.</li>",
                "<li><b>Wijzigen</b>. Deze gebruikersgroep kan de pagina's inzien en gegevens wijzigen.</li>",
                "<li><b>Voorzitter</b>. De voorzitter kan gegevens goedkeuren en diploma's, cijferlijsten en Ex-formulieren indienen.</li>",
                "<li><b>Secretaris</b>. De secretaris kan gegevens goedkeuren en diploma's, cijferlijsten en Ex-formulieren indienen.</li>",
                "<li><b>Examinator</b>. De examinator kan scores en cijfers goedkeuren.</li>",
                "<li><b>Gecommitteerde</b>. De gecommitteerde kan scores en cijfers goedkeuren.</li>",
                "<li><b>Systeembeheerder</b>. Alleen de systeembeheerder heeft toegang tot de gebruikers pagina en kan gebruikersaccounts aanmaken, wissen en permissies instellen.</li></ul></p>",

                 "<p class='mb-0 pb-0'>Een gebruiker kan tot <b>meerdere gebruikersgroepen</b> behoren. ",
                 "Wijs de gebruikersgroepen toe afhankelijk van de situatie op school, bijvoorbeeld: ",
                 "<ul class='manual_bullet'><li>Een examinator die ook de cijfers invoert of corrigeert, krijgt de gebruikersgroepen 'Wijzigen' en 'Examinator'.</li>",
                 "<li>Als de administratie de cijfers invoert, krijgt zij de gebruikersgroep 'Wijzigen'.</li></ul></p>",

                 "<p class='mb-0 pb-0'>De volgende <b>restricties</b> gelden: ",
                 "<ul class='manual_bullet'><li>Een gebruiker kan niet tegelijk voorzitter en secretaris zijn.</li>",
                 "<li>Er kunnen wel meerdere gebruikers tot de gebruikersgroep 'Voorzitter' en 'Secretaris' behoren.</li>",
                 "<li>Dezelfde gebruiker kan vakken en cijfers niet zowel als voorzitter als als secretaris goedkeuren.</li>",
                 "<li>Een systeembeheerder kan de gebruikersgroep 'Systeembeheerder' bij zichzelf niet wissen.</li>",
                 "<li>Het ETE kan gebruikers bij andere organisaties aanmaken en indien nodig wissen of niet-actief maken.</li></ul></p>",

            "</div>",
        "</div>",

        write_paragraph_header("id_user_allowed", "Toegestane secties"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",


                "<p>Een gebruiker heeft standaard toegang tot alle gegevens van alle kandidaten. Dat is niet altijd gewenst. ",
                "In AWP is het mogelijk voor elke gebruiker beperkingen in te stellen welke informatie hij/zij kan inzien en wijzigen. ",
                "Dit gaat door middel van de 'Toegestane secties'. ",
                "<p class='mb-0 pb-0'>De perkingen kunnen op de volgende niveaus worden ingesteld:</p>",
                "<ul class='manual_bullet'><li><b>Toegestane afdelingen</b>. De gebruiker kan alleen de opgegeven afdelingen (Vsbo, Havo, Vwo) inzien.</li>",
                "<li><b>Toegestane leerwegen</b>. De gebruiker kan alleen de opgegeven leerwegen inzien.</li>",
                "<li><b>Toegestane vakken</b>. De gebruiker kan alleen de opgegeven vakken inzien.</li>",
                "<li><b>Toegestane clusters</b>. De gebruiker kan alleen de opgegeven clusters wijzigen.</li></ul></p>",

                 "<p>Wanneer <b>toegestane afdelingen, leerwegen en /of vakken</b> worden ingesteld, kan de gebruiker alleen de gegevens zien van de opgegeven afdelingen, leerwegen en /of vakken.<br>",
                 "Wanneer <b>toegestane clusters</b> worden ingesteld, kan de gebruiker alleen de gegevens van de opgegeven clusters wijzigen, de overige gegevens blijven echter wel zichtbaar.</p>",
                 "<p>Voorbeeld: ",


                 "<ul class='manual_bullet'><li>Een gebruiker behoort tot de gebruikersgroepen 'Wijzigen' en 'Examinator' en heeft als toegestane clusters de cluster 'wk -2' van het vak Wiskunde. ",
                 "Deze gebruiker kan alle gegevens van alle kandidaten inzien, maar kan alleen de cijfers wijzigen en goedkeuren van het vak Wiskunde van de kandidaten in de cluster 'wk -2'.</li>",
                 "<li>Een gebruiker behoort alleen tot de gebruikersgroepen 'Gecommitteerde' en heeft als toegestane afdeling 'Vsbo', als toegestaan vak 'Wiskunde' en als toegestane clusters de cluster 'wk -2'. ",
                 "Deze gebruiker kan de gegegevens zien van het vak Wiskunde van alle Vbso-kandidaten, maar kan alleen de wiskunde-cijfers goedkeuren van de kandidaten in de cluster 'wk -2'.</li></ul></p>",

                 "<p class='mb-0 pb-0'>Het <b>instellen van toegestane secties</b> gaat als volgt: ",
                 "<ul class='manual_bullet'><li>Klik in de horizontale zwarte balk op de tab <i>Toegestane secties</i>.</li>",
                 "<li>Klik in de regel van de gebruiker op gewenste kolom <i>Toegestane ...</i>. Het keuzevenster verschijnt.</li>",
                 "<li>Selecteer de items waar de gebruiker toegang toe heeft, of klik op <i>&#60Alle...&#62</i>.</li>",
                 "<li>De lijst met toegestane items verschijnt in de betreffende kolom. Als niet alle items zichtbaar zijn ga je met de muis naar het betreffende veld zonder te klikken. De items worden nu onder elkaar zichtbaar.</li>",
                 "<li>Wanneer er geen restricties zijn blijft de kolom leeg.</li></ul></p>",

            "</div>",
        "</div>",


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
