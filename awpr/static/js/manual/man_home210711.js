// PR2021-07-18 added

    "use strict";

    const man_home = [
        "<div class='my-4'>",
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<h3 class='px-2'>Introductie</h3>",
            "</div>",
        "</div>",

        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<ul class='manual_bullet'><li>Inleiding</li>",
                "<li><a href='#id_step01'>Stap 1</a></li>",
                "<li>Stap 2</li></ul>",

            "</div>",
        "</div>",



        "<div class='mfc mb-0'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<h4 class='px-2'>Inleiding</h4>",
            "</div>",
        "</div>",
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>Je kunt beter gegevens uploaden in plaats van ze handmatig in te voeren. Dat gaat sneller en geeft minder kans op fouten. ",
                "Je hebt een Excel spreadsheet nodig met gegevens van de kandidaten, vakken en cijfers. Het leerlingvolgsysteem kan zo'n Excel spreadsheet aanmaken.</p>",
                "<p class='pb-0'>De volgende gegevens kunnen afzonderlijk, in deze volgorde, worden geüpload:</p>",
                "<ul class='manual_bullet'><li>de kandidaatgegevens;</li>",
                "<li>de vakken van de kandidaten;</li>",
                "<li>cijfers of scores van de kandidaten.</li></ul>",
                "<p>Je kunt ook alleen de kandidaatgegevens uploaden of alleen de kandidaatgegevens en de vakken.</p>",

                "<p>Bij het uploaden voert AWP de nodige controles uit. Voordat de gegevens worden opgeslagen moet je eerst een test-upload doen, om te zien of alle gegevens correct worden ingevoerd.</p>",
                "<p>In de pagina's <i>Kandidaten</i>, <i>Vakken</i> en <i>Cijfers</i> vind je in de menubalk een knop met respectievelijk: <i>Kandidaten uploaden</i>,  <i>Vakken uploaden</i> en <i>Cijfers uploaden</i>. ",
                "Als je hierop klikt verschijnt het upload-venster. Doorloop de volgende vier stappen.</p>",
            "</div>",
        "</div>",

        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<div class='img_home_titlebar'></div>",
            "</div>",
        "</div>",

        "<div id='id_step01' class='mfc mt-4'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<h4  class='px-2'>Stap 1: Selecteer een Excel bestand</h4>",
            "</div>",
        "</div>",
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>Selecteer eerst het Excel bestand met de gegevens die je wilt uploaden. Klik hiervoor op de knop <i>Choose file...</i>, selecteer het gewenste bestand en klik op <i>OK</i>.</p>",
                "<p>Als het Excel bestand meerdere werkbladen bevat, kies je het juiste werkblad onder <i>Selecteer een werkblad</i>.</p>",
                "<p>Zet een vinkje bij <i>De eerste regel van het werkblad bevat kolom-namen</i> als de eerste regel van het Excel bestand de namen van de kolommen bevat. Als dit hokje niet is aangevinkt worden de kolommen van het Excel bestand aangeduid met F1, F2 etc.</p>",
                "<p>Klik op <i>Volgende stap</i>. Dit gaat alleen als je een Excel bestand hebt ingevuld. Klik op <i>Annuleren</i> of klik ergens buiten het venster om dit venster te sluiten.</p>",
            "</div>",
        "</div>",
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<div class='img_upload_stud_step1'></div>",
            "</div>",
        "</div>",

        "<div class='mfc mt-4'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<h4 class='px-2'>Stap 2: Kolommen koppelen</h4>",
            "</div>",
        "</div>",
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p class='pb-0'>Er verschijnen nu drie lijsten op het scherm: </p>",
                "<ul class='manual_bullet'><li>de lijst <i>AWP-kolommen</i> met de namen van de velden die je kunt uploaden;</li>",
                "<li>de lijst <i>Excel-kolommen</i> met de namen van de kolommen in het Excel bestand;</li>",
                "<li>de lijst <i>Gekoppelde kolommen</i>.</li></ul>",

                "<p class='mt-2'>Het <b>koppelen van kolommen</b> gaat als volgt:</br>",
                "Selecteer een regel in de lijst met AWP-kolommen, bijvoorbeeld ‘Achternaam’. ",
                "Klik vervolgens in de lijst met Excel-kolommen op de naam van de kolom waarin de achternamen staan. Beide namen worden nu verplaatst naar de lijst <i>Gekoppelde kolommen</i>.</p>",
                "<p>Klik op een regel in de lijst met gekoppelde kolommen om kolommen te <b>ontkoppelen</b>.</p>",
                "<p>AWP koppelt automatisch kolommen met dezelfde naam. Je kunt ze zo nodig ontkoppelen.<br>AWP onthoudt de gekoppelde velden, zodat je ze een volgende keer niet opnieuw hoeft te koppelen.</p>",
                "<p>Er zijn een paar <b>verplichte velden</b> die altijd gekoppeld moeten worden. ",
                "Het veld <i>ID-nummer</i> is altijd verplicht. Bij het uploaden van kandidaten zijn ook <i>Achternaam</i> en <i>Voornamen</i> verplicht.</p>",
                "<p>Klik op <i>Volgende stap</i> als je de gewenste kolommen hebt gekoppeld. Dit gaat alleen als je alle verplichte velden hebt gekoppeld.</p>",

            "</div>",
        "</div>",
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<div class='img_upload_stud_step2'></div>",
            "</div>",
        "</div>",

        "<div class='mfc mt-4'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<h4 class='px-2'>Stap 3: Gegevens koppelen</h4>",
            "</div>",
        "</div>",
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p class='pb-0'>Er verschijnen nu drie lijsten op het scherm: </p>",
                "<ul class='manual_bullet'><li>de lijst <i>AWP-kolommen</i> met de namen van de velden die je kunt uploaden;</li>",
                "<li>de lijst <i>Excel-kolommen</i> met de namen van de kolommen in het Excel bestand;</li>",
                "<li>de lijst <i>Gekoppelde kolommen</i>.</li></ul>",

                "<p class='mt-2'>Het <b>koppelen van kolommen</b> gaat als volgt:</br>",
                "Selecteer een regel in de lijst met AWP-kolommen, bijvoorbeeld ‘Achternaam’.",
                "Klik vervolgens in de lijst met Excel-kolommen op de naam van de kolom waarin de achternamen staan.",
                "Beide namen worden nu verplaatst naar de lijst <i>Gekoppelde kolommen</i>.</p>",
                "<p>Klik op een regel in de lijst met gekoppelde kolommen om kolommen te <b>ontkoppelen</b>.</p>",
                "<p>AWP koppelt automatisch kolommen met dezelfde naam. Je kunt ze zo nodig ontkoppelen.<br>",
                "AWP onthoudt de gekoppelde velden, zodat je ze een volgende keer niet opnieuw hoeft te koppelen.</p>",
                "<p>Er zijn een paar <b>verplichte velden</b> die altijd gekoppeld moeten worden.",
                "Het zijn: <i>ID-nummer</i>, <i>Achternaam</i> en <i>Voornamen</i>.</p>",
                "<p>Klik op <i>Volgende stap</i> als je de gewenste kolommen hebt gekoppeld. ",
                "Dit gaat alleen als je alle verplichte velden hebt gekoppeld.</p>",

            "</div>",
        "</div>",
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<div class='img_upload_stud_step3'></div>",
            "</div>",
        "</div>",
        "<div class='mfc mt-4'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<h4 class='px-2'>Stap 4: Test upload</h4>",
            "</div>",
        "</div>",

        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",

            "<p>Klik op <i>Test upload</i> om de nieuwe gegevens te controleren en te vergelijken met de opgeslagen gegevens. De nieuwe gegevens worden nog niet opgeslagen.</p>",

            "<p>Na de test upload verschijnt er een kader met de testresulaten. Het geeft aan hoeveel nieuwe kandidaten worden geüpload, hoeveel kandidaten worden overgeslagen en hoeveel kandidaten al in het AWP bestand voorkomen. ",
            "Je kunt een logbestand downloaden met de details, onder andere de reden waarom een kandidaat wordt overgeslagen.</p>",

            "<p class='pb-0'>Kandidaten worden overgeslagen als:</p>",
            "<ul class='manual_bullet'><li>het ID-nummer meerdere keren voorkomt in het upload-bestand;</li>",
                "<li>het ID-nummer op deze school al voorkomt in een andere afdeling;</li>",
                "<li>het ID-nummer niet is ingevuld of te lang is.</li></ul>",

            "<p>Als een kandidaat al voorkomt op deze afdeling worden de nieuwe gegevens vegeleken met de opgeslagen gegevens. ",
            "Gewijzigde gegevens worden opgeslagen. Dat wordt in het logbestand vermeld.</p>",

            "<p>Klik op <i>hier</i> om het logbestand te downloaden.</p>",

            "<p>Klik op <i>Volgende stap</i> als je de gegevens wilt uploaden of op <i>Annuleren</i> als je nog wijzigingen in het upload bestand wilt aanbrengen.</p>",
            "</div>",
        "</div>",

         "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<div class='img_upload_stud_step4'></div>",
            "</div>",
        "</div>",

        "</div>"
    ]