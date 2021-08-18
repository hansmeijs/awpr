// PR2021-07-18 added

    "use strict";

const man_studsubj = {

    nl: [
        "<div class='mfc mt-4 mb-0'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<h4 class='px-2'>Vakken van kandidaten</h4>",
            "</div>",
        "</div>",

        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>Klik in de paginabalk op de knop <i>Vakken</i>. De onderstaande pagina <i>Vakken van kandidaten</i> wordt nu geopend. </p>",
                "<p class='pb-0'>In deze pagina kun je:</p>",
                "<ul class='manual_bullet mb-0'><li>Vakken van kandidaten uploaden. ",
            // from https://pagedart.com/blog/single-quote-in-html/
                "Klik <a href='#' class='awp_href' onclick='LoadPage(&#39upload&#39)'>hier</a> om naar de handleiding hiervan te gaan;</li>",
                "<li>De controle op de samenstelling van de vakken bekijken;</li>",
                "<li>Vakken aan een kandidaat toewijzen;</li>",
                "<li>Vakken van kandidaten goedkeuren en het Ex1 formulier indienen. ",
                "Klik <a href='#' class='awp_href' onclick='LoadPage(&#39approve&#39)'>hier</a> voor de handleiding ervan.;</li>",
                "<li>Het voorlopige en ingediende Ex1-formulier downloaden.</li></ul>",
                "<p class='pb-0'>De optie om vakken van vakkenpakketten toe te toewijzen is nog niet beschikbaar.</p>",
            "</div>",
        "</div>",

        "<div class='mfc mb-4'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p class='pb-0'><b>Vakken filteren</b></p>",
                "<p>Op elke regel in de tabel staat een vak van een kandidaat. ",
                "Je kunt alle vakken van alle kandidaten weergeven, maar dat is niet handig. ",
                "Het maakt de pagina onoverzichtelijk en bij veel kandidaten ook traag. Beter is het om vakken te filteren.</p>",

                "<p class='pb-0'>Het filteren kan op verschillende manieren:</p>",
                "<ul class='manual_bullet mb-0'><li>In de vertikale grijze filterbalk links kun je ",
                "een <b>leerweg</b>, <b>sector</b> of <b>profiel</b> selecteren;</li>",
                "<li>Je kunt ook een <b>vak</b> of <b>kandidaat</b> selecteren, maar niet beide. ",
                "<li>Tenslotte kun je vakken filteren met behulp van de <b>filterregel</b>;</li></ul>",
            "</div>",
        "</div>",
        set_image_div("img_studsubj_tab_subj_ne"),

        "<div class='mfc mt-4 mb-0'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<h4 class='px-2'>Controle op de samenstelling van de vakken</h4>",
            "</div>",
        "</div>",
        "<div class='mfc mb-2'>",
            "<div class='mfl mt-2'><div class='img_studsubj_exclamationsign'></div></div>",
            "<div class='mfr'>",
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
            "</div>",
        "</div>",

        set_image_div("img_studsubj_mod_studsubj_ne"),


        "<div id='id_step01' class='mfc mt-4'>",
            "<div class='mfl'></div>",
            "<div class='mfr'>",
                "<h4  class='px-2'>Vakken van kandidaten invoeren</h4>",
            "</div>",
        "</div>",

        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>Klik op de naam van de kandidaat om het venster te openen waarmee je de vakken van de kandidaat kunt wijzigen. ",
                "In de linker lijst staan de beschikbare vakken, de rechter lijst bevat de vakken van de kandidaat. ",
                "Alleen de afkorting en het karakter van het vak worden in de lijst weergegeven. ",
                "Als je met de muis boven de afkorting gaat staan, verschijnt er een venster met de volledige naam.",
                "Een ^ teken achter het vak betekent dat het een verplicht vak is, een * betekent dat het een combinatievak is.</p>",

                "<p><b>Vakken toevoegen of verwijderen</b><br> ",
                "Klik op een vak in de lijst om een vak te selecteren. ",
                "De regel wordt blauw en er verschijnt een vinkje. Nog een keer klikken en het vinkje verdwijnt. ",
                "Je kunt meerdere vakken selecteren.<br>",
                "Een of meerdere <b>vakken toevoegen</b> gaat als volgt: selecteer de gewenste vakken in de linker lijst en klik op de knop <i>Vakken toevoegen</i>, ",
                "Je kunt ook op een vak dubbelklikken om het toe te voegen.<br>",
                "Het <b>verwijderen van vakken</b> gaat op dezelfde manier. Klik op de knop <i>Vakken verwijdreen</i> of dubbelklik op een vak in de rechter lijst. ",
                "Elke keer wanneer vakken zijn toegevoegd of verwijderd berekent AWP opnieuw of de samenstelling van de vakken klopt.<br>",
                "Klik op de knop <b><i>Opslaan</i></b> om de wijzigingen op te slaan. </p>",

                "<p><b>Kenmerken van het vak wijzigen</b><br> ",
                "Klik op een kandidaat in de rechter lijst. In het kader <i>Kenmerken van het vak</i> staan alle kenmerken van dat vak. ",
                "De algemene kenmerken kun je niet veranderen. Dat zijn bijvboorbeeld: 'Combinatievak', 'Verplicht vak'. ",
                "Individuele kenmerken kun je wel per kandidaat instellen. het zijn: <b>Extra vak</b> en <b>Keuze-combinatievak</b>. ",
                "Ook de <b>Titel van het werkstuk en <b>Vakken waarop het werkstuk betrekking heeft</b> zijn voortaan opgenomen als individueel kenmerk van het vak 'Werkstuk'. ",
                "Je kunt meerdere vakken selecteren.<br>",
            "</div>",
        "</div>",

        set_image_div("img_studsubj_mod_studsubj_ne"),


        "<div class='mfc mb-4'>",
            "<div class='mfl'><p class='mt-2 diamond_3_4'></p></div>",
            "<div class='mfr'>",
            "</div>",
        "</div>",
    ],

    en:  [ "<div id='id_step01' class='mfc mt-4'>",
            "<div class='mfl'></div>",
            "<div class='mfr'>",
                "<h4  class='px-2'>Subjects of candidates</h4>",
            "</div>",
        "</div>"]
}
