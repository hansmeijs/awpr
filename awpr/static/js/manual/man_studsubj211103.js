// PR2021-07-18 added

    "use strict";

const man_studsubj = {

/////////  NEDERLANDS //////////////////////////////
    nl: [
        write_paragraph_header("id_intro", "Vakken van kandidaten"),
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
                "Klik <a href='#' class='awp_href' onclick='LoadPage(&#39approve&#39)'>hier</a> voor de handleiding ervan;</li>",
                "<li>Het voorlopige en ingediende Ex1-formulier downloaden.</li></ul>",
                "<p class='pb-0'>De optie om vakken van vakkenpakketten toe te toewijzen is nog niet beschikbaar.</p>",
            "</div>",
        "</div>",

        write_paragraph_header("id_filter_subjects", "Vakken filteren"),
        "<div class='mfc mb-4'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>Op elke regel in de tabel staat een vak van een kandidaat. ",
                "Je kunt alle vakken van alle kandidaten weergeven, maar dat is niet handig. ",
                "Het maakt de pagina onoverzichtelijk en bij veel kandidaten ook traag. Beter is het om vakken te filteren.</p>",

                "<p class='pb-0'>Het filteren kan op verschillende manieren:</p>",
                "<ul class='manual_bullet mb-0'><li>In de verticale grijze filterbalk links kun je ",
                "een <b>leerweg</b>, <b>sector</b> of <b>profiel</b> selecteren;</li>",
                "<li>Je kunt ook een <b>vak</b> of <b>kandidaat</b> selecteren, maar niet beide. ",
                "<li>Tenslotte kun je vakken filteren met behulp van de <b>filterregel</b>;</li></ul>",
            "</div>",
        "</div>",
        set_image_div("img_studsubj_tab_subj_ne"),

        write_paragraph_header("id_validate_subjects", "Controle op de samenstelling van de vakken"),
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

        write_paragraph_header("id_enter_studsubj", "Vakken van kandidaten invoeren"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
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
                "Individuele kenmerken kun je wel per kandidaat instellen. ", "Het zijn: 'Extra vak, telt niet mee voor de uitslag' en 'Extra vak, telt mee voor de uitslag'.<br>",
                "Ook de 'Titel van het werkstuk' en 'Vakken waarop het werkstuk betrekking heeft' zijn voortaan opgenomen als individueel kenmerk van het vak 'Werkstuk'. ",
            "</div>",
        "</div>",
        set_image_div("img_studsubj_mod_studsubj_ne"),

        write_paragraph_header("id_clusters", "Clusters"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",

                "<p>Een <b>cluster</b> is een groep examenkandidaten die hetzelfde vak volgen. ",
                "Het verschil met de klas is dat elke kandidaat maar in één klas kan zitten, ",
                "terwijl een kandidaat voor elk vak tot een apart cluster behoort. ",
                "Clusters worden gebruikt bij het uitprinten van rapportages - met name voor het Ex3-formulier - en bij het filteren van kandidaten.</p>",

                "<p>Klik in de pagina <i>Vakken</i> op de knop <i>Clusters</i>. Het onderstaande venster <i>Clusters</i> wordt nu geopend. </p>",


                "<p><b>Clusters toevoegen of verwijderen</b><br> ",
                /*
                Een cluster toevoegen gaat als volgt:
        Selecteer eerst een vak in het veld Selecteer vak, links boven in het venster.
        Klik op de knop Cluster toevoegen. Er verschijnt een veld Naam cluster.
        AWP vult automatisch de naam van de cluster in. U kunt deze naam wijzigen. Elke clusternaam
kan maar eenmaal voorkomen.
        Klik op OK.
Kandidaten toevoegen aan een cluster gaat als volgt:

        Selecteer eerst een cluster in de lijst Selecteer cluster.

        Selecteer één of meerdere kandidaten in de lijst Overige kandidaten met dit vak.

Houdt de Control  toets ingedrukt om meerdere kandidaten te selecteren of sleep met de muis.

Klik vervolgens op de knop < Toevoegen.

U kunt een kandidaat ook toevoegen of wissen door te dubbelklikken.
In de rechter lijst Overige kandidaten met dit vak staan alleen de kandidaten, die dit vak hebben en die nog niet in een andere cluster van dit vak zitten. Als u ook de kandidaten die al in een andere cluster van dit vakken zitten wilt weergeven, haalt u het vinkje weg bij Alleen kandidaten die nog niet in cluster zitten voor dit vak.
​
Elke kandidaat kan per vak maar in 1 cluster voorkomen. Als u een kandidaat in een nieuwe cluster zet wordt de oude cluster van de kandidaat gewist. AWP geeft vooraf een waarschuwing.
​
U kunt een kandidaat ook aan een cluster toevoegen of wissen in het scherm Examenkandidaat - Basisgegevens. Hier vindt u een veld Clusters. Klik op knop rechts van deze lijst. Het scherm Selecteer clusters van een kandidaat verschijnt.

Cluster wissen
Selecteer de cluster in de lijst en klik op de knop Wis cluster van de lijst. De cluster wordt nu gewist.
​
LET OP: Als u een cluster wist wordt de cluster ook bij alle kandidaten gewist, die in deze cluster zitten. Als dit geval is verschijnt eerst een waarschuwing.

Clusters printen
U kunt de volgende rapporten per cluster uitprinten:

-       Ex2A formulier
-       Ex3 formulier
-       Lijst ‘Kandidaten met persoonsgegevens’
-       Lijst ‘Kandidaten met uitslagen’
​

Selecteer in het keuzescherm de optie Print formulier per cluster en selecteer de clusters die u wilt printen.
                */

             "</div>",
        "</div>",

        set_image_div("img_studsubj_mod_cluster_ne"),

        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",


                "<p><b>Clusters toevoegen of verwijderen</b><br> ",

                "<p>Een cluster toevoegen gaat als volgt: ",
                "Selecteer eerst een vak in het veld Selecteer vak, links boven in het venster. ",
                "Klik op de knop <i>Cluster toevoegen</i>. Er verschijnt een veld Naam cluster. ",
                "AWP vult automatisch de naam van de cluster in. U kunt deze naam wijzigen. Elke clusternaam kan maar eenmaal voorkomen. ",
                "Klik op OK.</p>",

                "<p><b>Kandidaten toevoegen</b> aan een cluster gaat als volgt: ",
                "Selecteer eerst een cluster in de lijst Selecteer cluster. ",
                "Selecteer één of meerdere kandidaten in de lijst Overige kandidaten met dit vak. ",
                "AWP vult automatisch de naam van de cluster in. U kunt deze naam wijzigen. Elke clusternaam kan maar eenmaal voorkomen. ",
                "Klik op OK.</p>",

                /*

In de rechter lijst Overige kandidaten met dit vak staan alleen de kandidaten, die dit vak hebben en die nog niet in een andere cluster van dit vak zitten. Als u ook de kandidaten die al in een andere cluster van dit vakken zitten wilt weergeven, haalt u het vinkje weg bij Alleen kandidaten die nog niet in cluster zitten voor dit vak.
​
Elke kandidaat kan per vak maar in 1 cluster voorkomen. Als u een kandidaat in een nieuwe cluster zet wordt de oude cluster van de kandidaat gewist. AWP geeft vooraf een waarschuwing.
​
U kunt een kandidaat ook aan een cluster toevoegen of wissen in het scherm Examenkandidaat - Basisgegevens. Hier vindt u een veld Clusters. Klik op knop rechts van deze lijst. Het scherm Selecteer clusters van een kandidaat verschijnt.

Cluster wissen
Selecteer de cluster in de lijst en klik op de knop Wis cluster van de lijst. De cluster wordt nu gewist.
​
LET OP: Als u een cluster wist wordt de cluster ook bij alle kandidaten gewist, die in deze cluster zitten. Als dit geval is verschijnt eerst een waarschuwing.

Clusters printen
U kunt de volgende rapporten per cluster uitprinten:

-       Ex2A formulier
-       Ex3 formulier
-       Lijst ‘Kandidaten met persoonsgegevens’
-       Lijst ‘Kandidaten met uitslagen’
​

Selecteer in het keuzescherm de optie Print formulier per cluster en selecteer de clusters die u wilt printen.
                */

             "</div>",
        "</div>",


        "<div class='p-3 visibility_hide'>-</div>",
    ],

    en:  [

     "<div id='id_step01' class='mfc mt-4'>",
            "<div class='mfl'></div>",
            "<div class='mfr'>",
                "<h4  class='px-2'>Subjects of candidates</h4>",
            "</div>",
        "</div>"

        ]
}
