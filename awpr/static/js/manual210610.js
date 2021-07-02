// PR2021-06-10 added
document.addEventListener('DOMContentLoaded', function() {
    "use strict";


// --- get data stored in page
    let el_data = document.getElementById("id_data");
    const data_list = get_attr_from_el(el_data, "data-list");

    console.log ('data_list', data_list)

    //* Loop through all dropdown buttons to toggle between hiding and showing its dropdown content - This allows the user to have multiple dropdowns without any conflict */
    var dropdown = document.getElementsByClassName("dropdown-btn");
    var i;

    for (i = 0; i < dropdown.length; i++) {
      dropdown[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var dropdownContent = this.nextElementSibling;
        if (dropdownContent.style.display === "block") {
          dropdownContent.style.display = "none";
        } else {
          dropdownContent.style.display = "block";
        }
      });
    }
    let html_str = "", html_list = [];
    switch (data_list){
    case "main":
        html_list = [
        "<div class='my-4'>",
        "<div class='mfc mb-4'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<h3 class='px-2'>Gegevens uploaden</h3>",
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
                "<p>Het heeft de voorkeur om gegevens te uploaden in plaats van ze handmatig in te voeren. Dat gaat sneller en geeft minder kans op fouten. ",
                "Je hebt een Excel spreadsheet nodig met gegevens van de kandidaten, vakken en cijfers. Het leerlingvolgsysteem kan zo'n Excel spreadsheet aanmaken.</p>",
                "<p class='pb-0'>De volgende gegevens moeten afzonderlijk, in deze volgorde, worden geüpload:</p>",
                "<ul class='manual_bullet'><li>de kandidaatgegevens;</li>",
                "<li>de vakken van de kandidaten;</li>",
                "<li>cijfers of scores van de kandidaten.</li></ul>",
                "<p>Je kunt ook alleen de kandidaatgegevens uploaden of alleen de kandidaatgegevens met vakken.</p>",
                "<p>Bij het uploaden voert AWP de nodige controles uit. Voordat de gegevens worden opgeslagen kun je eerst een test-upload doen, om te zien of alle gegevens correct worden ingevoerd.</p>",
                "<p>In de pagina's <i>Kandidaten</i>, <i>Vakken</i> en <i>Cijfers</i> vind je in de menubalk een knop met respectievelijk: <i>Kandidaten uploaden</i>,  <i>Vakken uploaden</i> en <i>Cijfers uploaden</i>. ",
                "Als je hierop klikt verschijnt het upload-venster. Doorloop de volgende vier stappen.</p>",
            "</div>",
        "</div>",

        "<div class='mfc mb-0'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<h4 class='px-2'>Stap 1: Open een Excel bestand</h4>",
            "</div>",
        "</div>",
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>Selecteer eerst het Excel bestand met de gegevens die je wilt importeren. Klik hiervoor op de knop <i>Choose file...</i>, selecteer het gewenste bestand en klik op <i>OK</i>.</p>",
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

        "<div class='mfc mt-4 mb-0'>",
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
                "Selecteer een regel in de lijst met AWP-kolommen, bijvoorbeeld ‘Achternaam’.",
                "Klik vervolgens in de lijst met Excel-kolommen op de naam van de kolom waarin de achternamen staan. Beide namen worden nu verplaatst naar de lijst <i>Gekoppelde kolommen</i>.</p>",
                "<p>Klik op een regel in de lijst met gekoppelde kolommen om kolommen te <b>ontkoppelen</b>.</p>",
                "<p>AWP koppelt automatisch kolommen met dezelfde naam. Je kunt ze zo nodig ontkoppelen.<br>AWP onthoudt de gekoppelde velden, zodat je ze een volgende keer niet opnieuw hoeft te koppelen.</p>",
                "<p>Er zijn een paar <b>verplichte velden</b> die altijd gekoppeld moeten worden.",
                "Het veld <i>ID-nummer</i> is altijd verplicht, bij het uploaden van kandidaten zijn ook <i>Achternaam</i> en <i>Voornamen</i> verplicht.</p>",
                "<p>Klik op <i>Volgende stap</i> als je de gewenste kolommen hebt gekoppeld. Dit gaat alleen als je alle verplichte velden hebt gekoppeld.</p>",

            "</div>",
        "</div>",
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<div class='img_upload_stud_step2'></div>",
            "</div>",
        "</div>",

        "<div class='mfc mt-4 mb-0'>",
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
                "<p>Klik op <i>Volgende stap</i> als je de gewenste kolommen hebt gekoppeld.",
                "Dit gaat alleen als je alle verplichte velden hebt gekoppeld.</p>",

            "</div>",
        "</div>",
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<div class='img_upload_stud_step2'></div>",
            "</div>",
        "</div>",

        "</div>"]
        break;
    case "sct":
        html_str = "<h1> CONTENT TEST </h1>"
        break;
    };
    html_str = html_list.join('');

    document.getElementById("id_content").innerHTML = html_str;

})  // document.addEventListener('DOMContentLoaded', function()