// PR2021-07-18 added

    "use strict";

    const man_upload = {
/////////  NEDERLANDS //////////////////////////////
        nl: [
        write_paragraph_header("id_intro", "Gegevens uploaden"),
        write_paragraph_body("",
        ["<p>Je kunt beter gegevens uploaden in plaats van ze handmatig in te voeren. Dat gaat sneller en geeft minder kans op fouten. ",
            "Je hebt een Excel spreadsheet nodig met gegevens van de kandidaten, vakken en cijfers. Het leerlingvolgsysteem kan zo'n Excel spreadsheet aanmaken.</p>",
            "<p class='pb-0'>De volgende gegevens kunnen afzonderlijk, in deze volgorde, worden geüpload:</p>",
            "<ul class='manual_bullet'><li>de kandidaatgegevens;</li>",
            "<li>de vakken van de kandidaten;</li>",
            "<li>cijfers of scores van de kandidaten.</li></ul>",
            "<p>Je kunt ook alleen de kandidaatgegevens uploaden of alleen de kandidaatgegevens en de vakken.</p>",

            "<p>Bij het uploaden voert AWP de nodige controles uit. Voordat de gegevens worden opgeslagen moet je eerst een test-upload doen, om te zien of alle gegevens correct worden ingevoerd.</p>",
            "<p>In de pagina's <i>Kandidaten</i>, <i>Vakken</i> en <i>Cijfers</i> vind je in de menubalk een knop met respectievelijk: <i>Kandidaten uploaden</i>,  <i>Vakken uploaden</i> en <i>Cijfers uploaden</i>. ",
            "Als je hierop klikt verschijnt het upload-venster. Doorloop de volgende stappen.</p>",
        ]),
        write_image("img_upload_stud_menu_ne"),

        write_paragraph_header("id_upload_step01", "Stap 1: Selecteer een Excel bestand"),
        write_paragraph_body("",
        ["<p>Selecteer eerst het Excel bestand met de gegevens die je wilt uploaden. Klik hiervoor op de knop <i>Open een Excel-bestand</i>, selecteer het gewenste bestand en klik op <i>Open</i>.</p>",
         ]),
        write_paragraph_body("",
        ["<p class='mb-0 pb-0'>De structuur van het Excel bestand moet er als volgt uitzien:</p>",
            "<ul class='manual_bullet'><li>Het bestand moet een kolom <b>Identiteitsnummer</b> bevatten.</li>",
            "<li><b>Elk vak staat in een aparte kolom</b>. De namen van de vakken hoeven niet hetzelfde te zijn als in AWP. ",
            "Als namen hetzelfde zijn als in AWP worden ze gekoppeld, anders moet je ze eenmalig koppelen in de stap <i>Gegevens koppelen</i>.</li>",
            "<li><b>Elke kandidaat staat in een regel</b> en mag maar eenmaal voorkomen in het bestand.</li>",
            "<li>De volgorde van de kolommen is niet van belang, kolommen die niet gekoppeld zijn worden overgeslagen.</li></ul>",
        ]),
        write_image("img_exemption_excel_ne_en"),

        write_paragraph_body("",
        ["<p>Als het Excel bestand meerdere werkbladen bevat, kies je het juiste werkblad onder <i>Selecteer een werkblad</i>.</p>",
            "<p>Zet een vinkje bij <i>De eerste regel van het werkblad bevat kolom-namen</i> als de eerste regel van het Excel bestand de namen van de kolommen bevat. Als dit hokje niet is aangevinkt worden de kolommen van het Excel bestand aangeduid met F1, F2 etc.</p>",
            "<p>Klik op <i>Volgende stap</i>. Dit gaat alleen als je een Excel bestand hebt ingevuld. Klik op <i>Annuleren</i> of klik ergens buiten het venster om dit venster te sluiten.</p>",
        ]),
        write_image("img_upload_stud_step1_ne"),

        write_paragraph_header("id_upload_step02a", "Stap 2: Selecteer het soort examencijfer"),
        write_paragraph_body("",
        ["<p>Deze stap verschijnt alleen bij het uploaden van cijfers. De hierna volgende stappen hebben dan een volgnummer dat 1 hoger is dan in deze handleiding.</p>",
            "<p>Afhankelijk van het geselecteerde tijdvak verschijnen er een of meer soorten examencijfers waaruit je kunt kiezen. ",
            "Selecteer het gewenste soort examencijfer en klik op <i>Volgende</i>.</p>",
            "<p>Als je een ander tijdvak wilt selecteren sluit je het upload venster. Klik op het gewenste tijdvak in de horizontale zwarte balk.</p>",
        ]),
        write_image("img_upload_step2a_ne"),

        write_paragraph_header("id_upload_step02", "Stap 2: Kolommen koppelen"),
        write_paragraph_body("",
        ["<p class='pb-0'>Er verschijnen drie lijsten op het scherm: </p>",
            "<ul class='manual_bullet'><li>de lijst <i>AWP-kolommen</i> met de namen van de velden die je kunt uploaden;</li>",
            "<li>de lijst <i>Excel-kolommen</i> met de namen van de kolommen in het Excel bestand;</li>",
            "<li>de lijst <i>Gekoppelde kolommen</i>.</li></ul>",

            "<p class='mt-2'>Het <b>koppelen van kolommen</b> gaat als volgt:</br>",
            "Selecteer een regel in de lijst met AWP-kolommen, bijvoorbeeld ‘ID-nummer’. ",
            "Klik vervolgens in de lijst met Excel-kolommen op de naam van de kolom waarin de ID-nummers staan. Beide namen worden nu verplaatst naar de lijst <i>Gekoppelde kolommen</i>.</p>",
            "<p>Klik op een regel in de lijst met gekoppelde kolommen om kolommen te <b>ontkoppelen</b>.</p>",

            "<p>AWP koppelt automatisch kolommen met dezelfde naam. Je kunt ze zo nodig ontkoppelen.<br>AWP onthoudt de gekoppelde velden, zodat je ze een volgende keer niet opnieuw hoeft te koppelen.</p>",

            "<p>Er zijn een paar <b>verplichte velden</b> die altijd gekoppeld moeten worden. ",
            "Het veld <i>ID-nummer</i> is altijd verplicht. Bij het uploaden van kandidaten zijn ook <i>Achternaam</i>, <i>Voornamen</i> en <i>Profiel</i> of <i>Leerweg</i> en <i>Sector</i> verplicht.</p>",

            "<p>Het <b>ID-nummer</b> mag met en zonder punten geschreven worden. AWP verwijdert eventuele punten in het ID-nummer. ",
            "Gebruik bij kandidaten zonder ID-nummmer de geboortedatum plus twee letters. ",
            "Op het diploma en de cijferlijst wordt het ID-nummer met punten weergegeven, eventuele letters worden niet weergegeven.</p>",

            "<p>Als het veld <b>Geboortedatum</b> niet is gekoppeld of als de geboortedatum niet is ingevuld, haalt AWP de geboortedatum uit het ID-nummer.</p>",

            "<p>Als het veld <b>Examennummer</b> niet is gekoppeld of als het examennummer niet is ingevuld, vult AWP automatisch het eerstvolgende examennummer in.</p>",

            "<p>Het <b>Registratienummer</b> van de kandidaat wordt automatisch aangemaakt.</p>",

            "<p>Het veld <b>Afdelingen</b> verschijnt alleen als je school meerdere afdelingen heeft (afdelingen zijn: Vsbo, Havo en Vwo). ",
            "Je hoeft dit veld alleen de koppelen als in het Excel bestand de kandidaten van meerdere afdelingen staan. AWP uploadt dan alleen de kandidaten van de afdeling, waar je nu aan werkt. ",
            "ALs je het veld <i>Afdelingen</i> niet koppelt, worden alle kandidaten van het Excel bestand in de huidige afdeling geüpload.</p>",

            "<p>Klik op <i>Volgende stap</i> als je de gewenste kolommen hebt gekoppeld. Dit gaat alleen als je alle verplichte velden hebt gekoppeld.</p>",
        ]),

        write_paragraph_header("id_upload_step03", "Stap 3: Gegevens koppelen"),
        write_paragraph_body("",
        ["<p class='pb-0'>Afhankelijk van de afdelingen van de school verschijnen er nu een of meer sets met 3 lijsten op het scherm.</p>",
            "<p class='pb-0'>Het zijn de set <i>Leerwegen koppelen</i> en <i>Sectoren koppelen</i> of de set <i>Profielen koppelen</i>. ",
            "Als je school meerdere afdelingen heeft verschijnt ook de set <i>Afdelingen koppelen</i>.<br>",
            "De kolom <i>AWP-waarden</i> bevat alle nog beschikbare opties in AWP, ",
            "de kolom <i>Excel-waarden</i> bevat de niet gekoppelde waarden van het Excel-bestand, ",
            "de kolom <i>Gekoppelde waarden</i> bevat de opties die al gekoppeld zijn.</p>",

            "<p class='mt-2'>Het <b>koppelen en ontkoppelen van gegevens</b> gaat op dezelde manier als bij het koppelen van kolommen in stap 2.</p>",

            "<p class='pb-0'><span class='man_underline'>Voorbeeld</span><br>",
            "In onderstaand voorbeeld staan bij <i>Sectoren koppelen</i> de AWP-opties: <i>z&w</i>, <i>tech</i> en <i>ec</i>. ",
            "Deze school heeft geen sector <i>z&w</i>, die hoeft daarom niet gekoppeld te worden.<br>",
            "Als waarden van het Excel-bestand niet gekoppeld zijn, wordt de kandidaat wel geüpload, maar het betreffende gegeven blijft dan blanco.<br>",
            "AWP koppelt automatisch opties met dezelfde naam. Je kunt ze zo nodig ontkoppelen. ",
            "AWP onthoudt de gekoppelde gegevens, zodat je ze een volgende keer niet opnieuw hoeft te koppelen.</p>",
            "<p>Klik op <i>Volgende stap</i> als je de gewenste opties hebt gekoppeld.</p>",
        ]),
        write_image("img_upload_stud_step3_ne"),

        write_paragraph_header("id_upload_step04", "Stap 4: Test upload"),
        write_paragraph_body("",
        ["<p>Klik op <i>Test upload</i> om de nieuwe gegevens te controleren en te vergelijken met de opgeslagen gegevens. De nieuwe gegevens worden nog niet opgeslagen.</p>",

            "<p>Na de test upload verschijnt er een kader met de testresulaten. Het geeft aan hoeveel nieuwe kandidaten worden geüpload, hoeveel kandidaten worden overgeslagen en hoeveel kandidaten al in het AWP bestand voorkomen. ",
            "Je kunt een logbestand downloaden met de details, onder andere de reden waarom een kandidaat wordt overgeslagen.</p>",

            "<p class='pb-0'>Kandidaten worden overgeslagen als:</p>",
            "<ul class='manual_bullet'><li>het ID-nummer meerdere keren voorkomt in het upload-bestand;</li>",
                "<li>het ID-nummer op deze school al voorkomt;</li>",
                "<li>het ID-nummer niet is ingevuld of te lang is.</li></ul>",

            "<p>Klik op <i>hier</i> om het logbestand te downloaden.</p>",

            "<p>Klik op <i>Volgende stap</i> als je de gegevens wilt uploaden of op <i>Annuleren</i> als je nog wijzigingen in het upload bestand wilt aanbrengen.</p>",
        ]),
        write_image("img_upload_stud_step4_ne"),

        write_paragraph_header("id_upload_step05", "Stap 5: Uploaden"),
        write_paragraph_body("",
        ["<p>Klik op <i>Uploaden</i> om de nieuwe gegevens te uploaden en op te slaan.</p>",
            "<p>Na het uploaden verschijnt er een melding hoeveel nieuwe kandidaten zijn geüpload en hoeveel kandidaten zijn overgeslagen.<br>",
            "Je kunt een logbestand downloaden met de details. ",
            "Klik op <i>hier</i> om het logbestand te downloaden.</p>",
            "<p>Klik op <i>Sluiten</i> of klik buiten het venster om het venster te sluiten.</p>",
        ]),
        write_image("img_upload_stud_step5_ne"),

        "<div class='p-3 visibility_hide'>-</div>"
    ],

/////////  ENGELS //////////////////////////////
    en:  [

        write_paragraph_header("id_intro", "Upload data"),
        write_paragraph_body("",
        ["<p>It's better to upload data instead of entering it manually. It's faster and less likely to make mistakes. ",
            "You need an Excel spreadsheet with data from the candidates, subjects and grades. The student tracking system can create such an Excel spreadsheet.</p>",
            "<p class='pb-0'>The following data can be uploaded separately, in this order:</p>",
            "<ul class='manual_bullet'><li>the candidate data;</li>",
            "<li>the subjects of the candidates;</li>",
            "<li>grades or scores of the candidates.</li></ul>",
            "<p>You can also upload only the candidate data or only the candidate data and the subjects.</p>",

            "<p>When uploading, AWP performs the necessary checks. Before the data is saved, you must first do a test upload to see if all data is entered correctly.</p>",
            "<p>In the pages <i>Candidates</i>, <i>Subjects</i> and <i>Grades</i> you will find a button in the menu bar with respectively: <i>Upload candidates</i>, <i>Upload subjects</i> and <i>Upload grades</i>. ",
            "If you click on this, the upload window will appear. Go through the following steps.</p>",
        ]),
        write_image("img_upload_stud_menu_en"),

        write_paragraph_header("id_upload_step01", "Step 1: Select an Excel file"),
        write_paragraph_body("",
        ["<p>First select the Excel file with the data you want to upload. Click on the button <i>Open an Excel file</i>, select the desired file and click on <i>Open</i>.</p>",
        ]),
        write_paragraph_body("",
        ["<p class='mb-0 pb-0'>The structure of the Excel file should look like this:</p>",
            "<ul class='manual_bullet'><li>The file must contain a column <b>ID-number</b>.</li>",
            "<li><b>Each subject is in a separate column</b>. The names of the subjects do not have to be the same as in AWP. ",
            "If names are the same as in AWP they will be linked, otherwise you have to link them once in the step <i>Link data</i>.</li>",
            "<li><b>Each candidate is in a line</b> and may only appear once in the file.</li>",
            "<li>The order of the columns is not important, columns that are not linked are skipped.</li></ul>",
        ]),
        write_image("img_exemption_excel_ne_en"),

        write_paragraph_body("",
        ["<p>If the Excel file contains multiple worksheets, choose the correct worksheet under <i>Select a worksheet</i>.</p>",
            "<p>Tick <i>The first line of the worksheet contains column names</i> if the first line of the Excel file contains the names of the columns. If this box is not checked, the columns of the Excel file marked with F1, F2 etc.</p>",
            "<p>Click on <i>Next step</i>. This will only work if you have entered an Excel file. Click on <i>Cancel</i> or click anywhere outside the window to close this window.< /p>",
        ]),
        write_image("img_upload_stud_step1_en"),

        write_paragraph_header("id_upload_step02a", "Step 2: Select the type of exam grade"),
        write_paragraph_body("",
        ["<p>This step only appears when uploading grades. The following steps will then have a sequence number that is 1 higher than in this manual.</p>",
                 "<p>Depending on the selected exam period, one or more types of exam grades will appear for you to choose from. ",
                 "Select the desired exam grade type and click <i>Next</i>.</p>",
                 "<p>If you want to select a different exam period, close the upload window. Click on the desired exam period in the horizontal black bar.</p>",
        ]),
        write_image("img_upload_step2a_en"),

        write_paragraph_header("id_upload_step02", "Step 2: Link Columns"),
        write_paragraph_body("",
        ["<p class='pb-0'>Three lists appear on the screen: </p>",
            "<ul class='manual_bullet'><li>the list of <i>AWP columns</i> containing the names of the fields you can upload;</li>",
            "<li>the list of <i>Excel columns</i> with the names of the columns in the Excel file;</li>",
            "<li>the list of <i>Linked Columns</i>.</li></ul>",

            "<p class='mt-2'>The <b>column linking</b> goes like this:</br>",
            "Select a line from the list of AWP columns, for example 'ID number'. ",
            "Then, in the list of Excel columns, click on the name of the column that contains the ID numbers. Both names will now be moved to the <i>Linked Columns</i> list.</p>",
            "<p>Click a line in the list of linked columns to <b>unlink columns</b>.</p>",

            "<p>AWP automatically links columns with the same name. You can unlink them if needed.<br>AWP remembers the linked fields, so you don't have to link them again next time.</p>",

            "<p>There are a few <b>mandatory fields</b> that must always be linked. ",
            "The <i>ID Number</i> field is always required. When uploading candidates, also <i>Last Name</i>, <i>First Names</i> and <i>Profile</i> or <i>Learning</i> and <i>Sector</i> required.</p>",

            "<p>The <b>ID number</b> may be written with or without dots. AWP removes any dots in the ID number. ",
            "For candidates without an ID number, use the date of birth plus two letters. ",
            "The ID number with points is shown on the diploma and the list of marks, any letters are not shown.</p>",

            "<p>If the <b>Birthdate</b> field is not matched or if the date of birth is not filled in, AWP will extract the date of birth from the ID number.</p>",

            "<p>If the <b>Exam number</b> field is not linked or if the exam number is not entered, AWP will automatically fill in the next exam number.</p>",

            "<p>The candidate's <b>Registration Number</b> will be created automatically.</p>",

            "<p>The <b>Departments</b> field only appears if your school has multiple departments (departments are: Vsbo, Havo and Vwo). ",
            "You only need to link this field if the Excel file contains candidates from multiple departments. AWP will then only upload the candidates from the department you are currently working on. ",
            "If you don't link the <i>Departments</i> field, all candidates from the Excel file in the current department will be uploaded.</p>",

            "<p>Click on <i>Next step</i> when you have linked the desired columns. This will only work if you have linked all required fields.</p>",
        ]),

        write_paragraph_header("id_upload_step03", "Step 3: Link data"),
        write_paragraph_body("",
        ["<p class='pb-0'>Depending on the departments of the school, one or more sets with 3 lists now appear on the screen.</p>",
            "<p class='pb-0'>They are the <i>Linking Learning Paths</i> and <i>Linking Sectors</i> set or the <i>Linking Profiles</i> set. ",
            "If your school has multiple departments, the set <i>Link departments</i>.<br>",
            "The <i>AWP Values</i> column contains all options still available in AWP, ",
            "the <i>Excel Values</i> column contains the unlinked values ​​from the Excel file, ",
            "the column <i>Linked values</i> contains the options that are already linked.</p>",

            "<p class='mt-2'>The <b>linking and unlinking of data</b> is done in the same way as when linking columns in step 2.</p>",

            "<p class='pb-0'><span class='man_underline'>Example</span><br>",
            "In the example below, <i>Link Sectors</i> contains the AWP options: <i>z&w</i>, <i>tech</i> and <i>ec</i>. ",
            "This school does not have a sector <i>z&w</i>, so it does not need to be linked.<br>",
            "If values ​​from the Excel file are not linked, the candidate will be uploaded, but the relevant data will remain blank.<br>",
            "AWP automatically links options with the same name. You can unlink them if necessary. ",
            "AWP remembers the linked data, so you don't have to link it again next time.</p>",
            "<p>Click <i>Next Step</i> when you have linked the options you want.</p>",
        ]),
        write_image("img_upload_stud_step3_en"),

        write_paragraph_header("id_upload_step04", "Step 4: Test upload"),
        write_paragraph_body("",
            ["<p>Click on <i>Test upload</i> to check the new data and compare it with the saved data. The new data will not be saved yet.</p>",

            "<p>After the test upload, a box appears with the test results. It indicates how many new candidates are uploaded, how many candidates are skipped and how many candidates already exist in the AWP file. ",
            "You can download a log file with details, including why a candidate is being skipped.</p>",

            "<p class='pb-0'>Candidates are skipped if:</p>",
            "<ul class='manual_bullet'><li>the ID number appears multiple times in the upload file;</li>",
                "<li>the ID number already exists at this school;</li>",
                "<li>the ID number is not filled in or is too long.</li></ul>",

            "<p>Click <i>here</i> to download the log file.</p>",

            "<p>Click on <i>Next step</i> if you want to upload the data or on <i>Cancel</i> if you want to make any changes to the upload file.</p>",
        ]),
        write_image("img_upload_stud_step4_en"),

        write_paragraph_header("id_upload_step05", "Step 5: Upload"),
        write_paragraph_body("",
        ["<p>Click <i>Upload</i> to upload and save the new data.</p>",
         "<p>After uploading, you will be notified how many new candidates have been uploaded and how many candidates have been skipped.<br>",
         "You can download a log file with the details. ",
         "Click <i>here</i> to download the log file.</p>",
         "<p>Click <i>Close</i> or click outside the window to close the window.</p>",
         ]),
         write_image("img_upload_stud_step5_en"),

        "<div class='p-3 visibility_hide'>-</div>"

    ]
    };
