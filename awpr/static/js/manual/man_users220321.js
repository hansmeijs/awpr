// PR2022-02-11 added

    "use strict";

const man_user = {

/////////  NEDERLANDS //////////////////////////////
    nl: [
        write_paragraph_header("id_intro", "Gebruikers"),
        write_paragraph_body("",[
            "<p>AWP-online maakt gebruik van een geavanceerd systeem van gebruikers en gebruikersrechten (permissies). ",
            "Dit is nodig omdat de beveiliging van de gegevens van groot belang is en omdat er veel verschillende soorten gebruikers zijn, ",
            "die allemaal op verschillende manieren gebruik maken van AWP-online en toegang hebben tot verschillende onderdelen van het programma.</p>",
            "<p>Het aanmaken van gebruikers accounts en toekennen van permissies gebeurt door de organisatie zelf. ",
            "Ook de accounts voor de examinatoren en gecommitteerden worden door de school zelf aangemaakt.</p>",
            "<p>Alleen een gebruiker die tot de gebruikersgroep 'Systeembeheerder' behoort kan gebruikers accounts aanmaken en wijzigen.</p>",
            "<p>In deze paragraaf wordt uitgelegd hoe het beheren van de gebruikers accounts en hun permissies in zijn werk gaat.</p>",
        ]),

        write_paragraph_header("id_user_login", "Inloggen"),
        write_paragraph_body("",[
            "<p>Klik op <i>Login</i> rechts boven in het scherm. ",
            "Vul je schoolcode, gebruikersnaam en wachtwoord in en klik op <i>Inloggen</i>.</p>",
            "<p>Wanneer de inloggegevens niet correct zijn ingevuld, verschijnt er een foutmelding. Probeer het opnieuw. ",
            "Let erop dat het wachtwoord hoofdlettergevoelig is. De schoolcode en gebruikersnaam zijn niet hoofdlettergevoelig.</p>",
            "<p class='mb-0 pb-0'>Als het niet lukt om in te loggen kan dat verschillende oorzaken hebben:</p>",
            "<ul class='manual_bullet'><li>Je bent al ingelogd. Klik dan op het AWP logo links boven in het venster.</li>",
            "<li>Een andere gebruiker is al ingelogd in deze browser. Sluit de browser, open de browser opnieuw en log in.</li>",
            "<li>Je browser accepteert geen cookies. Wijzig de instelling van de browser.</li></ul></p>"
        ]),
        write_paragraph_body("",[
            "<p><b>Wachtwoord vergeten</b><br>Klik op <i>Wachtwoord vergeten?</i> onderaan het inlog venster als je je wachtwoord bent vergeten. ",
            "Er verschijnt een venster <i>Nieuw wachtwoord aanmaken</i>.<br>",
            "Vul je schoolcode en e-mail adres in en klik op <i>E-mail aanvragen</i>. ",
            "Let erop dat het e-mail adres dat je invult hetzelfde moet zijn als het e-mail adres van je gebruikersaccount.<br>",
            "AWP stuurt nu een e-mail naar het e-mail adres van de gebruiker. De e-mail bevat een link. Klik hierop om naar de pagina te gaan, waar je je wachtwoord kunt wijzigen.</p>",
        ]),

        write_paragraph_body("",[
            "<p class='mb-0 pb-0'>Wanneer je geen e-mail hebt ontvangen kan dat verschillende oorzaken hebben:</p>",
            "<ul class='manual_bullet'><li>De e-mail is in de map met spam terecht gekomen.</li>",
            "<li>Het e-mail adres dat je hebt ingevuld komt niet overeen met het e-mail adres van je gebruikersaccount.</li>",
            "<li>De e-mail is tegengehouden door de firewall van je organisatie.</li>",
            "<li>AWP heeft de e-mail om andere redenen niet kunnen versturen.</li></ul>"
        ]),

        write_paragraph_header("id_user_manage", "Gebruikersaccounts"),
        write_paragraph_body("",[
            "<p><b>Gebruikerspagina openen</b><br>Klik op je gebruikersnaam rechts boven in het scherm. ",
             "Als je systeembeheerder bent staat er een knop <i>Gebruikers</i> onder je naam. ",
             "Klik hierop en de onderstaande pagina 'Gebruikers' wordt geopend.<p>",
        ]),
        write_image("img_users_tbl_users_ne"),

        write_paragraph_body("",[
            "<p><b>Gebruikersaccount toevoegen</b><br>Klik in de menubalk op <i>Gebruiker toevoegen</i>. Het venster <i>Gebruiker toevoegen</i> verschijnt. ",
            "Vul de gebruikersnaam, volledige naam van de gebruiker en het e-mail adres in.</p>",
            "<p>De gebruikersnaam wordt gebruikt om in te loggen. De volledige naam wordt gebruikt in officiële documenten zoals het diploma, cijferlijst en Ex-formulieren. ",
            " De gebruikersnaam, volledige naam en e-mail-adres moeten uniek zijn binnen de organisatie. ",
             "Dezelfde gebruikersnaam en e-mail adres mogen wel gebruikt worden bij een andere organisatie, bijvoorbeeld wanneer een gebruiker tevens gecommiteerde is bij een ander school.</p>",

             "<p><b>Activeringslink</b><br>Nadat je geklikt heb op <i>Gebruikersaccount aanmaken</i> verstuurt AWP een e-mail naar de gebruiker om het e-mail adres te verifiëren. ",
            "De e-mail bevat een link waarmee de nieuwe gebruiker een wachtwoord kan aanmaken en kan inloggen. ",
            "Zodra de gebruiker een wachtwoord heeft aangemaakt is de account geactiveerd. Er staat dan een vinkje in de kolom <i>Geactiveerd</i>.</p>",
            "<p>De activeringslink blijft zeven dagen geldig.  Wanneer de link verlopen is staat dan een uitroepteken in de kolom <i>Geactiveerd</i>.</p>",
            "<p>Je kunt zo nodig een nieuwe activeringslink versturen, ook als hij nog niet verlopen is. ",
            "Klik in de kolom <i>Geactiveerd</i> en klik in het venster dat verschijnt op <i>Activeringslink versturen</i>.</p>",

             "<p><b>Gebruiker gegevens wijzigen</b><br>Klik op de naam van de gebruiker. Er verschijnt een scherm waarin je de gegevens van de gebruiker kunt wijzigen. Klik op <i>Opslaan</i> om de wijzigingen op te slaan. ",

             "<p><b>Gebruikersaccount wissen</b><br>Selecteer een gebruiker en klik in de menubalk op <i>Gebruiker wissen</i>. Er verschijnt een scherm om te bevestigen dat de gebruiker wordt gewist. Klik op <i>Ja, wis</i>. ",
             "Wanneer een gebruiker gegevens heeft ingevoerd kun je de account niet meer wissen. In plaats daarvan kun je de account 'Niet-actief' maken.",

             "<p><b>Gebruikersaccount niet-actief maken</b><br>Klik in de kolom <i>Niet actief</i> van een gebruiker. Er verschijnt een scherm om te bevestigen dat de gebruiker 'Niet-actief' wordt gemaakt. Klik op <i>Ja, maak niet-actief</i>. ",
              "Het icoontje wordt nu zwart. De gebruiker kan nu niet meer inloggen. ",
              "Klik op het zwarte icoontje om een gebruiker weer actief te maken.</p>",

             "<p><b>Niet-actieve gebruikersaccounts tonen</b><br>Klik in de kolom <i>Niet actief</i> op het icoontje met het oog onder 'Niet actief'. Nu worden alleen de niet-actieve accounts weergegeven. ",
             "Nog een keer klikken en alle accounts worden weergegeven. Nog een keer klikken en alleen de actieve accounts worden weergegeven.</p>",
        ]),

        write_paragraph_header("id_user_usergroups", "Gebruikersgroepen"),
        write_paragraph_body("",[
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
             "<li>Dezelfde gebruiker kan vakken en cijfers niet zowel als examinator als als gecommitteerde goedkeuren.</li>",
             "<li>Een systeembeheerder kan de gebruikersgroep 'Systeembeheerder' bij zichzelf niet wissen.</li>",
             "<li>Het ETE kan gebruikers bij andere organisaties aanmaken en indien nodig wissen of niet-actief maken.</li></ul></p>",
        ]),
        write_image("img_users_tbl_usergroups_ne"),

        write_paragraph_header("id_user_allowed", "Toegestane secties"),
        write_paragraph_body("",[
            "<p>Een gebruiker heeft standaard toegang tot alle gegevens van alle kandidaten. Dat is niet altijd gewenst. ",
            "In AWP is het mogelijk voor elke gebruiker beperkingen in te stellen welke informatie hij/zij kan inzien en wijzigen. ",
            "Dit gaat door middel van de 'Toegestane secties'. ",
            "<p class='mb-0 pb-0'>De beperkingen kunnen op de volgende niveaus worden ingesteld:</p>",
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
        ]),
        write_image("img_users_tbl_allowed_ne"),

        write_paragraph_header("id_user_examiners", "Examinatoren en gecommitteerden"),
        write_paragraph_body("",
            ["<p>Ook de examinatoren en gecommitteerden zullen voortaan hun digitale handtekening moeten zetten.<br>",
            "In het eerste deel van deze paragraaf wordt aangegeven hoe de accounts van de examinatoren en gecommitteerden worden aangemaakt.<br>",
            "In het tweede deel wordt de procedure omschreven voor het goedkeuren door de examinator en gecommitteerde.</p>",

            "<h5 class='mx-2 mt-4 mb-0 pb-0'><span class='man_underline'>Accounts aanmaken voor de examinatoren en gecommitteerden</span></h5>",
            "<p>Alle examinatoren en gecommitteerden krijgen een gebruikersaccount. ",
            "Ze kunnen worden aangemaakt door een gebruiker met systeembeheerder permissie. Doorloop de volgende drie stappen:</p>",

            "<p class='mb-0 pb-0'><b>Stap 1: Gebruikersaccounts voor examinatoren en gecommitteerden aanmaken</b><br>",
            "<ul class='manual_bullet'><li>Ga naar de pagina <i>Gebruikers</i> en klik in de menubalk op <i>Gebruiker toevoegen</i>.</li>",
            "<li>In het venster <i>Gebruiker toevoegen</i> vul je de gebruikersnaam en de volledige naam in. ",
            "De gebruikersnaam wordt gebruikt voor het inloggen, de volledige naam wordt weergegeven op de Ex-formulieren.</li>",
            "<li>Vul tenslotte het e-mail adres in en klik op <i>Gebruikersaccount aanmaken</i>. ",
            "AWP stuurt nu een e-mail met een link naar het opgegeven e-mail adres.</li>",
            "<li>De gebruiker moet op de link in die e-mail klikken om een wachtwoord in te vullen en de account te activeren.</li></ul>",

            "<p class='mb-0 pb-0'><b>Stap 2: Gebruikersgroepen toewijzen</b><br>",
            "<ul class='manual_bullet'><li>Klik in de horizontale zwarte balk op de tab <i>Gebruikersgroepen</i> ",
            "en zet in de kolom <i>Examinator</i> of <i>Gecommitteerde</i> een vinkje achter de naam van de gebruiker.</li>",
            "<li>Als de examinator ook cijfers invoert zet je ook een vinkje in de kolom <i>Wijzigen</i>.</li></ul>",

            "<p class='mb-0 pb-0'><b>Stap 3: Toegestane secties instellen</b><br>",
            "De examinator en gecommiteerden kunnen nu alle vakken van alle kandidaten goedkeuren. ",
            "Dat is niet altijd gewenst. ",
            "In de tab <i>Toegestane secties</i> kun je als volgt beperkingen instellen welke vakken hij/zij kan goedkeuren:",
            "<ul class='manual_bullet'><li>Klik in de horizontale zwarte balk op de tab <i>Toegestane secties</i></li>",
            "<li>Klik in de regel van  een gebruiker op een van de kolommen <i>Toegestane afdelingen, - leerwegen, - vakken of - clusters</i>.</li>",
            "<li>Selecteer in het venster dat verschijnt een of meerdere items of klik op <i>Alle ... </i>.</li>",
            "<li>Klik op <i>Opslaan</i></ul>",
            ]),
        write_paragraph_body("img_lightbulb",
            ["<p><b>Gebruikersnamen uploaden</b><br>",
                "In plaats van de accounts een voor een aan te maken, kun je ze ook importeren vanuit een Excel bestand. ",
                "Klik in de menubalk op <i>Gebruikersnamen uploaden</i> en doorloop de stappen. ",
                "Na het uploaden stuurt AWP <span class='man_underline'>niet</span> automatsich een e-mail met een activeringslink. ",
                "Klik bij elke gebruiker in de kolom <i>Geactiveerd</i> om de activerings e-mail te versturen.</p>",
            ]),
        write_paragraph_body("",
            ["<h5 class='mx-2 mt-4 mb-0 pb-0'><span class='man_underline'>Goedkeuren van scores en cijfers door de examinator en gecommitteerde</span></h5>",
            "<p>Alle schoolexamen cijfers dienen digitaal goedgekeurd te worden door de voorzitter, secretaris en examinator. ",
            "Wanneer een vak geen examinator heeft, omdat het een cijfer van vorig jaar betreft, dient de voorzitter of secretaris tevens als examinator goed te keuren.</p>",
            "<p>De scores van het centraal examen dienen tevens door de gecommitteerde te worden goedgekeurd.</p>",
            "<p>Doorloop de volgende stappen om de scores of cijfers goed te keuren:</p>",

            "<p class='mb-0 pb-0'><b>Stap 1: Selecteer de goed te keuren kandidaten en vakken</b></p>",
            "<ul class='manual_bullet'><li>Open de pagina <i>Cijfers</i> door in de lichtblauwe paginabalk op de knop <i>Cijfers</i> te klikken.</li>",
            "<li>Desgewenst kun je in de verticale grijze balk links een filter instellen van de cijfers die je wilt goedkeuren.</li>",
            "<li>Klik op <i>Alles van dit tijdvak weergeven</i> onder in de verticale grijze balk links ",
            "als je in een keer alle cijfers, waar je toestemming voor hebt, wilt goedkeuren.</li></ul>",

            "<p class='mb-0 pb-0'><b>Stap 2: Controleer de goed te keuren cijfers</b></p>",
            "<ul class='manual_bullet mb-0 pb-0'><li>Klik in de horizontale grijze menubalk op de knop <i>Cijfers goedkeuren</i>. Het venster <i>Cijfers goedkeuren</i> wordt geopend.</li>",
            "<li>In het kader is aangegeven welk filter is ingesteld. In het veld <i>Functie</i> staat in welke hoedanigheid je de cijfers goedkeurt. ",
            "Als je zowel examinator als voorzitter / secretaris bent, kun je in dit veld selecteren in welke hoedanigheid je de cijfers goedkeurt.</li>",
            "<li>Klik op <i>Cijfers controleren</i>. AWP controleert de cijfers en geeft de resultaten weer in een apart kader.</li></ul>",
        ]),
        write_paragraph_body("img_exclamationsign",
            ["<p>Het filter op de toegestane vakken en clusters wordt (nog) niet weergegeven in het grijze kader. ",
                "In het resultaat van de controle is wel rekening gehouden met de toegestane vakken en clusters.</p>",
            ]),
        write_paragraph_body("",
            ["<p class='mb-0 pb-0'><b>Stap 3: Cijfers goedkeuren of goedkeuringen wissen</b></p>",
            "<ul class='manual_bullet'><li>Klik op <i>Cijfers goedkeuren</i>. De cijfers worden nu goedgekeurd. De ruit achter het cijfer geeft de status van de goedkeuring weer. ",
            "Ga met de muis boven de ruit staan om te zien wie het cijfer heeft goedgekeurd.</li>",
            "<li>Klik op <i>Goedkeuringen verwijderen</i>. De goedkeuring van de geselcteerde cijfers wordt verwijderd.</li></ul>",

            "<p class='mb-0 pb-0'><b>Stap 4: Individuele cijfers goedkeuren of goedkeuringen wissen</b></p>",
            "<ul class='manual_bullet'><li>Klik op de ruit achter een cijfer om het cijfer goed te keuren of de goedkeuring te verwijderen.</li></ul>",

        ]),


        "<div class='p-3 visibility_hide'>-</div>",
    ],

/////////  ENGLISH //////////////////////////////
    en:  [
        write_paragraph_header("id_intro", "Users"),
        write_paragraph_body("",[
            "<p>AWP-online uses an advanced system of users and user rights (permissions). ",
            "This is necessary because the security of the data is of great importance and because there are many different types of users, ",
            "all of which use AWP-online in different ways and access different parts of the program.</p>",
            "<p>The creation of user accounts and the granting of permissions is done by the organization itself. ",
            "The accounts for the examiners and correctors are also created by the school itself.</p>",
            "<p>Only a user belonging to the user group 'System Administrator' can create and edit user accounts.</p>",
            "<p>This section explains how to manage user accounts and their permissions.</p>",
        ]),

        write_paragraph_header("id_user_login", "Login"),
        write_paragraph_body("",[
            "<p>Click <i>Login</i> at the top right of the screen. ",
            "Enter your school code, username and password and click <i>Login</i>.</p>",
            "<p>If the login details are not entered correctly, an error message will appear. Please try again. ",
            "Note that the password is case sensitive. The school code and username are not case sensitive.</p>",
            "<p class='mb-0 pb-0'>Failure to login can have several causes:</p>",
            "<ul class='manual_bullet'><li>You are already logged in. Then click on the AWP logo at the top left of the window.</li>",
            "<li>Another user is already logged in to this browser. Close the browser, reopen the browser and log in.</li>",
            "<li>Your browser does not accept cookies. Change the browser setting.</li></ul></p>"
        ]),
        write_paragraph_body("",[
            "<p><b>Forgotten password</b><br>Click on <i>Wachtwoord vergeten?</i> at the bottom of the login window if you have forgotten your password.",
            "A window <i>Nieuw wachtwoord aanmaken</i> will appear.<br>",
            "Enter your school code and email address and click <i>Request email</i>.",
            "Note that the e-mail address you enter must be the same as the email address of your user account.<br>",
            "AWP will now send an email to the user's email address. The email contains a link. Click this link to go to the page where you can change your password.</p>",
        ]),

        write_paragraph_body("",[
            "<p class='mb-0 pb-0'>If you have not received an e-mail, it can be for several reasons:</p>",
            "<ul class='manual_bullet'><li>The email ended up in the spam folder.</li>",
            "<li>The e-mail address you entered does not match the e-mail address of your user account.</li>",
            "<li>The email was blocked by your organization's firewall.</li>",
            "<li>AWP was unable to send the email for other reasons.</li></ul>"
        ]),
        write_paragraph_header("id_user_manage", "User Accounts"),
        write_paragraph_body("",[
            "<p><b>Open user page</b><br>Click on your username at the top right of the screen. ",
             "If you're a system administrator, there's a <i>Users</i> button below your name. ",
             "Click this and the 'Users' page below will open.<p>",
        ]),
        write_image("img_users_tbl_users_ne"),
        write_paragraph_body("",[
            "<p><b>Add User Account</b><br>Click <i>Add User</i> in the menu bar. The <i>Add User</i> window appears. ",
            "Enter the username, full name of the user and the e-mail address.</p>",
            "<p>The username is used to log in. The full name is used in official documents such as the diploma, grade list and Ex forms. ",
            "The username, full name and email address must be unique within the organization. ",
             "The same username and e-mail address may be used at another organization, for example when a user is also a corrector at another school.</p>",

             "<p><b>Activation Link</b><br>After you click on <i>Create User Account</i> AWP will send an email to the user to verify the email address. ",
            "The email contains a link that allows the new user to create a password and log in. ",
            "As soon as the user has created a password, the account is activated. There will be a check mark in the column <i>Activated</i>.</p>",
            "<p>The activation link remains valid for seven days. When the link has expired, an exclamation mark will appear in the column <i>Activated</i>.</p>",
            "<p>You can send a new activation link if needed, even if it hasn't expired yet. ",
            "Click in the <i>Activated</i> column and in the window that appears, click on <i>Send activation link</i>.</p>",

             "<p><b>Change user data</b><br>Click on the user's name. A screen will appear where you can change the user's data. Click on <i>Save</i> to save the changes. ",

             "<p><b>Delete user account</b><br>Select a user and click <i>Delete user</i> in the menu bar. A screen will appear to confirm that the user will be deleted. Click on <i>Yes, delete</i>. ",
             "Once a user has entered data, you cannot delete the account. Instead, you can make the account 'Inactive'. ",

             "<p><b>Disable user account</b><br>Click in a user's <i>Inactive</i> column. A screen will appear to confirm that the user is 'Inactive ' is created. Click <i>Yes, make inactive</i>. ",
              "The icon now turns black. The user can no longer log in. ",
              "Click on the black icon to make a user active again.</p>",

             "<p><b>Show inactive user accounts</b><br>In the <i>Inactive</i> column, click on the icon with the eye under 'Inactive'. Now only the inactive active accounts are shown. ",
             "Click again and all accounts will be displayed. Click again and only the active accounts will be displayed.</p>",
        ]),
        write_paragraph_header("id_user_usergroups", "Usergroups"),
        write_paragraph_body("",[
            "<p>On the <i>Users</i> page, click in the horizontal black bar on the <i>User groups</i> tab. ",
            "A list of the users and user groups to which the user belongs will appear. ",
            "There is a check mark in the columns of the user groups to which the user belongs.</p>",

            "<p><b>Assign and remove user groups</b><br>Click in the column of a user group to assign the user group to the user account. ",
            "Click on a checkmark to delete the user group.</p>",

             "<p class='mb-0 pb-0'>AWP has the following user groups:</p>",
            "<ul class='manual_bullet'><li><b>Read only</b>. This user group can view the pages, but not edit any data.</li>",
            "<li><b>Change</b>. This user group can view the pages and change data.</li>",
            "<li><b>Chairperson</b>. The chairperson can approve data and submit diplomas, lists of marks and Ex forms.</li>",
            "<li><b>Secretary</b>. The secretary can approve data and submit diplomas, lists of marks and Ex forms.</li>",
            "<li><b>Examiner</b>. The examiner can approve scores and grades.</li>",
            "<li><b>Corrector</b>. The corrector can approve scores and grades.</li>",
            "<li><b>System Administrator</b>. Only the System Administrator has access to the Users page and can create, delete and set permissions for user accounts.</li></ul></p>",

             "<p class='mb-0 pb-0'>A user can belong to <b>multiple user groups</b>. ",
             "Assign the user groups according to the situation at school, for example: ",
             "<ul class='manual_bullet'><li>An examiner who also enters or corrects the grades will be given the user groups 'Change' and 'Examiner'.</li>",
             "<li>If the administration enters the numbers, it gets the user group 'Change'.</li></ul></p>",

             "<p class='mb-0 pb-0'>The following <b>restrictions</b> apply: ",
             "<ul class='manual_bullet'><li>A user cannot be chairperson and secretary at the same time.</li>",
             "<li>Several users can belong to the user group 'Chairperson' and 'Secretary'.</li>",
             "<li>The same user cannot approve subjects and grades as both chairperson and secretary.</li>",
             "<li>The same user cannot approve subjects and grades both as an examiner and as a examiner.</li>",
             "<li>A system administrator cannot delete the user group 'System Administrator' for himself.</li>",
             "<li>The ETE can create users at other organizations and if necessary delete or disable them.</li></ul></p>",
        ]),
        write_image("img_users_tbl_usergroups_ne"),

        write_paragraph_header("id_user_allowed", "Allowed Sections"),
        write_paragraph_body("",[
            "<p>A user has access to all data of all candidates by default. This is not always desirable. ",
            "In AWP it is possible for each user to set restrictions on what information he/she can view and change. ",
            "This goes through the 'Allowed Sections'.",
            "<p class='mb-0 pb-0'>The restrictions can be set to the following levels:</p>",
            "<ul class='manual_bullet'><li><b>Allowed departments</b>. The user can only view the specified departments (Vsbo, Havo, Vwo).</li>",
            "<li><b>Allowed learning paths</b>. The user can only view the specified learning paths.</li>",
            "<li><b>Allowed subjects</b>. The user can only view the specified subjects.</li>",
            "<li><b>Allowed clusters</b>. The user can only change the specified clusters.</li></ul></p>",

             "<p>When <b>allowed departments, learning paths and/or subjects</b> are set, the user can only see the data of the specified departments, learning paths and/or subjects.<br>",
             "When <b>allowed clusters</b> are set, the user can only change the data of the specified clusters, but the rest of the data remains visible.</p>",
             "<p>Example: ",
             "<ul class='manual_bullet'><li>A user belongs to the user groups 'Modify' and 'Examiner' and has the cluster 'wk -2' of the Mathematics subject as allowed clusters. ",
             "This user can view all data of all candidates, but can only change and approve the grades of the Mathematics subject of the candidates in the cluster 'wk -2'.</li>",
             "<li>A user only belongs to the user group 'Corrector' and has the allowed department 'Vsbo', the allowed subject 'Mathematics' and the cluster 'wk -2' as allowed clusters. ",
             "This user can see the Mathematics data of all Vbso candidates, but can only approve the Mathematics grades of the candidates in the cluster 'wk -2'.</li></ul></p>" ,

             "<p class='mb-0 pb-0'>How to <b>set allowed sections</b> is as follows: ",
             "<ul class='manual_bullet'><li>In the horizontal black bar, click the <i>Allowed Sections</i> tab.</li>",
             "<li>In the user's row, click on the desired column <i>Allowed ...</i>. The selection window appears.</li>",
             "<li>Select the items the user has access to, or click <i>&#60All...&#62</i>.</li>",
             "<li>The list of allowed items appears in the relevant column. If not all items are visible, move the mouse to the relevant field without clicking. The items are now visible below each other.</li>",
             "<li>If there are no restrictions, the column remains empty.</li></ul></p>",
        ]),
        write_image("img_users_tbl_allowed_ne"),

        write_paragraph_header("id_user_examiners", "Examiners and correctors"),
        write_paragraph_body("",
            ["<p>The examiners and correctors will also have to put their digital signature from now on.<br>",
            "The first part of this section describes how the accounts of the examiners and correctors are created.<br>",
            "The second part describes the procedure for approval by the examiner and the examiner.</p>",

            "<h5 class='mx-2 mt-4 mb-0 pb-0'><span class='man_underline'>Create accounts for the examiners and correctors</span></h5>",
            "<p>All examiners and correctors will receive a user account.",
            "They can be created by a user with system administrator permission. Go through the following three steps:</p>",

            "<p class='mb-0 pb-0'><b>Step 1: Create user accounts for examiners and examiners</b><br>",
            "<ul class='manual_bullet'><li>Go to the <i>Users</i> page and click <i>Add User</i> in the menu bar.</li>",
            "<li>In the <i>Add User</i> window, enter the username and full name.",
            "The username is used for login, the full name is displayed on the Ex forms.</li>",
            "<li>Finally enter the email address and click on <i>Create user account</i>.",
            "AWP will now send an e-mail with a link to the specified e-mail address.</li>",
            "<li>The user must click on the link in that email to enter a password and activate the account.</li></ul>",

            "<p class='mb-0 pb-0'><b>Step 2: Assign User Groups</b><br>",
            "<ul class='manual_bullet'><li>In the horizontal black bar, click the <i>Usergroups</i> tab ",
            "and put a check next to the user's name in the <i>Examiner</i> or <i>Assignee</i> column.</li>",
            "<li>If the examiner also enters grades, put a check in the <i>Edit</i> column.</li></ul>",

            "<p class='mb-0 pb-0'><b>Step 3: Set allowed sections</b><br>",
            "The examiner and correctors can now approve all subjects of all candidates.",
            "That is not always desirable.",
            "In the <i>Allowed Sections</i> tab, you can restrict which courses he/she can approve as follows:",
            "<ul class='manual_bullet'><li>In the horizontal black bar, click the <i>Allowed Sections</i></li> tab",
            "<li>In a user's line, click on one of the columns <i>Allowed departments, learning paths, courses or clusters</i>.</li>",
            "<li>In the window that appears, select one or more items or click on <i>All ... </i>.</li>",
            "<li>Click <i>Save</i></ul>",
            ]),

        write_paragraph_body("img_lightbulb",
            ["<p><b>Upload usernames</b><br>",
                "Instead of creating the accounts one by one, you can also import them from an Excel file.",
                "Click <i>Upload Usernames</i> in the menu bar and go through the steps.",
                "After uploading, AWP will automatically send <span class='man_underline'>not</span> an email with an activation link.",
                "Click in the <i>Activated</i> column for each user to send the activation email.</p>",
            ]),

        write_paragraph_body("",
            ["<h5 class='mx-2 mt-4 mb-0 pb-0'><span class='man_underline'>Approval of scores and grades by the examiner and examiner</span></h5>",
            "<p>All school exam figures must be digitally approved by the chairperson, secretary and examiner.",
            "If a subject does not have an examiner, because it has grades from last year, the chair or secretary must also approve as an examiner. </p>",
            "<p>The scores of the central exam must also be approved by the examiner.</p>",
            "<p>Go through the following steps to approve the scores or grades:</p>",

            "<p class='mb-0 pb-0'><b>Step 1: Select the candidates and subjects to be approved</b></p>",
            "<ul class='manual_bullet'><li>Open the <i>Grades</i> page by clicking the <i>Grades</i> button in the light blue page bar.</li>",
            "<li>If desired, you can filter the grades you want to approve in the vertical gray bar on the left.</li>",
            "<li>Click <i>View all of this time slot</i> at the bottom of the vertical gray bar on the left ",
            "if you want to approve all grades for which you have permission at once.</li></ul>",

            "<p class='mb-0 pb-0'><b>Step 2: Check the grades to be approved</b></p>",
            "<ul class='manual_bullet mb-0 pb-0'><li>Click the <i>Approve Grades</i> button in the horizontal gray menu bar. The <i>Approve Grades</i> window opens .</li>",
            "<li>The frame indicates which filter has been set. The <i>Function</i> field shows the capacity in which you approve the grades. ",
            "If you are both examiner and chairperson/secretary, you can select in this field in which capacity you approve the grades.</li>",
            "<li>Click <i>Check Grades</i>. AWP checks the grades and displays the results in a separate frame.</li></ul>",
        ]),

        write_paragraph_body("img_exclamationsign",
            ["<p>The filter on the allowed subjects and clusters is not (yet) displayed in the gray frame. ",
                "The result of the check does take into account the permitted subjects and clusters. </p>",
            ]),

        write_paragraph_body("",
            ["<p class='mb-0 pb-0'><b>Step 3: Approve grades or clear approvals</b></p>",
            "<ul class='manual_bullet'><li>Click <i>Approve Grades</i>. The grades are now approved. The diamond behind the grade shows the status of the approval. ",
            "Hover over the diamond to see who approved the grade.</li>",
            "<li>Click on <i>Remove approvals</i>. The approval of the selected grades will be removed.</li></ul>",

            "<p class='mb-0 pb-0'><b>Step 4: Approve individual grades or clear approvals</b></p>",
            "<ul class='manual_bullet'><li>Click the diamond behind a grade to approve the grade or remove the approval.</li></ul>",
        ]),


        "<div class='p-3 visibility_hide'>-</div>",

    ]
}
