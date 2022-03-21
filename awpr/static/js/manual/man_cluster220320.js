// PR2021-07-18 added

    "use strict";

const man_cluster = {

/////////  NEDERLANDS //////////////////////////////
    nl: [
        write_paragraph_header("id_intro", "Clusters"),
        write_paragraph_body("",
            [
                "<p>Een <b>cluster</b> is een groep examenkandidaten die hetzelfde vak volgen. ",
                "Het verschil met de klas is dat elke kandidaat maar in één klas kan zitten, ",
                "terwijl een kandidaat voor elk vak tot een apart cluster behoort. ",
                "Clusters worden gebruikt bij het uitprinten van rapportages - met name voor het Ex3-formulier - en bij het filteren van kandidaten.</p>",

                "<p>Klik in de pagina <i>Vakken</i> op de knop <i>Clusters</i>. Het onderstaande venster <i>Clusters</i> wordt nu geopend. </p>",
            ]),
        write_image("img_studsubj_mod_cluster_ne"),

        write_paragraph_header("id_cluster_add_delete", "Clusters toevoegen of wissen"),
        write_paragraph_body("",
            [
                "<p class='mb-0 pb-0'>Een <b>cluster toevoegen</b> gaat als volgt:</p>",
                "<ul class='manual_bullet mb-0'><li>Selecteer eerst een vak in het veld <i>Selecteer vak</i>, links boven in het venster.</li>",
                "<li>Klik op de knop <i>Cluster toevoegen</i> links onder de lijst met clusters. Er verschijnt een veld <i>Naam cluster</i>.</li>",
                "<li>AWP vult automatisch de naam van de cluster in. Je kunt deze naam wijzigen. Elke clusternaam kan maar eenmaal voorkomen.</li>",
                "<li>Klik op <i>OK</i> onder de clusternaam.</li>",
                "<li>Wanneer je alle wijzigingen hebt aangebracht klik je op <i>Opslaan</i> rechts onder in het venster. De wijzigingen worden nu opgeslagen.</li></ul>",

                "<p class='mb-0 pt-2 pb-0'>Een <b>cluster wissen</b> gaat als volgt:</p>",
                "<ul class='manual_bullet mb-0'><li>Selecteer een cluster in de lijst <i>Clusters</i>.</li>",
                "<li>Klik op <i>Cluster wissen</i> rechts onder de lijst met clusters.</li>",
                "<li>Wanneer de cluster kandidaten heeft verschijnt er een melding, dat de cluster bij deze kandidaten wordt verwijderd. Klik op <i>OK</i> om door te gaan.</li>",
                "<li>Klik op <i>OK</i>.</li>",
                "<li>Klik op <i>Opslaan</i> rechts onder in het venster om de wijzigingen op te slaan.</li></ul>",

                "<p class='mb-0 pt-2 pb-0'>De <b>naam van een cluster wijzigen</b> gaat als volgt:</p>",
                "<ul class='manual_bullet mb-0'><li>Selecteer een cluster in de lijst <i>Clusters</i>.</li>",
                "<li>Klik op <i>Clusternaam wijzigen</i> onder aan de lijst met clusters.</li>",
                "<li>Wijzig de naam van de cluster en klik op <i>OK</i>.</li>",
                "<li>Klik op <i>Opslaan</i> rechts onder in het venster om de wijzigingen op te slaan.</li></ul>",
            ]),
        write_paragraph_header("id_cluster_student", "Kandidaten toevoegen of verwijderen"),
        write_paragraph_body("",
            [
                "<p class='mb-0 pt-2 pb-0'>Kandidaten toevoegen of verwijderen gaat als volgt:</p>",
                "<ul class='manual_bullet mb-0'><li>Selecteer een cluster in de lijst <i>Clusters</i>.</li>",
                "<li>Klik op een kandidaat in de lijst <i>Beschikbare kandidaten</i>. ",
                "De kandidaat wordt nu toegevoegd aan de lijst <i>Kandidaten van dit cluster</i>.</li>",
                "<li>Klik op een kandidaat in de lijst <i>Kandidaten van dit cluster</i> om de kandidaat te verwijderen.</li>",
                "<li>Klik op <i>Alle kandidaten toevoegen</i> of <i>Alle kandidaten verwijderen</i> om alle kandidaten van de lijst toe te voegen of te verwijderen.</li>",
                "<li>Klik op <i>Opslaan</i> rechts onder in het venster om de wijzigingen op te slaan.</li></ul>",

                "<p class='mb-0 pt-2 pb-0'><b>Alle kandidaten van een klas toevoegen</b></p>",
                "<p class='mt-0 mb-0 pb-0'>Je kunt alle kandidaten van een klas in een keer aan een cluster toevoegen. Dit gaat als volgt:</p>",
                "<ul class='manual_bullet mb-0'><li>Selecteer een klas in het veld <i>Filter klas</i> in het kader <i>Filter kandidaten</i>.</li>",
                "<li>Klik vervolgens op <i>Alle kandidaten toevoegen</i> onder de lijst met beschikbare kandidaten.</li>",
                "<li>Klik tenslotte op <i>Opslaan</i> rechts onder in het venster om de wijzigingen op te slaan.</li></ul>",

                "<p class='mb-0 pt-2 pb-0'>Standaard worden in de lijst met beschikbare kandidaten alleen de kandidaten weergegeven, die nog niet tot een cluster voor dit vak behoren. ",
                "Wanneer de lijst met beschikbare kandidaten leeg is, betekent dit dat alle kandidaten tot een cluster voor dit vak behoren.<br>",
                "Zet een vinkje bij <i>Ook kandidaten met cluster weergeven</i> om ook de kandidaten, die al tot een cluster behoren, weer te geven in de lijst met beschikbare kandidaten.</p>",
            ]),
        write_paragraph_body("img_lightbulb",
            [
                "<p>Wanneer je per ongeluk een cluster hebt gewist of andere fouten hebt gemaakt, kun je op <i>Annuleren</i> klikken. ",
                "Het venster wordt nu gesloten zonder dat de wijzigingen worden opgeslagen. ",
                "Open het venster opnieuw om de laatst opgeslagen gegevens weer te geven.</p>",
            ]),

        "<div class='p-3 visibility_hide'>-</div>",
    ],

en:  [
        write_paragraph_header("id_intro", "Clusters"),
        write_paragraph_body("",
            [
                "<p>A <b>cluster</b> is a group of exam candidates who attend the same course. ",
                "The difference with the class is that each candidate can only be in one class, ",
                "while a candidate belongs to a separate cluster for each subject. ",
                "Clusters are used when printing reports - especially for the Ex3 form - and when filtering candidates.</p>",

                "<p>On the <i>Subjects</i> page, click the <i>Clusters</i> button. The <i>Clusters</i> window below will now open. </p>",
            ]),

        write_image("img_studsubj_mod_cluster_en"),
        write_paragraph_body("",
            [
                "<p><b>Add or delete clusters</b></p>",
                "<p class='mb-0 pb-0'>Adding a <b>cluster</b> goes like this:</p>",
                "<ul class='manual_bullet mb-0'><li>First select a subject in the <i>Select subject</i> field, at the top left of the window.</li>",
                "<li>Click the <i>Add cluster</i> button to the left below the cluster list. A <i>Cluster Name</i> field will appear.</li>",
                "<li>AWP automatically fills in the name of the cluster. You can change this name. Each cluster name can only appear once.</li>",
                "<li>Click <i>OK</i> under the cluster name.</li>",
                "<li>When you have made all the changes, click <i>Save</i> in the lower right corner of the window. The changes will now be saved.</li></ul>",

                "<p class='mb-0 pt-2 pb-0'>How to delete a <b>cluster</b>:</p>",
                "<ul class='manual_bullet mb-0'><li>Select a cluster from the list <i>Clusters</i>.</li>",
                "<li>Click <i>Delete cluster</i> right below the list of clusters.</li>",
                "<li>When the cluster has candidates, a message will appear stating that the cluster will be removed from these candidates. Click <i>OK</i> to continue.</li>",
                "<li>Click <i>OK</i>.</li>",
                "<li>Click <i>Save</i> at the bottom right of the window to save the changes.</li></ul>",

                "<p class='mb-0 pt-2 pb-0'>How to <b>change the name of a cluster</b>:</p>",
                "<ul class='manual_bullet mb-0'><li>Select a cluster from the list <i>Clusters</i>.</li>",
                "<li>Click <i>Change cluster name</i> at the bottom of the list of clusters.</li>",
                "<li>Rename the cluster and click <i>OK</i>.</li>",
                "<li>Click <i>Save</i> at the bottom right of the window to save the changes.</li></ul>",

                "<p class='mb-0 pt-2 pb-0'><b>Add or remove candidates</b> goes as follows:</p>",
                "<ul class='manual_bullet mb-0'><li>Select a cluster from the list <i>Clusters</i>.</li>",
                "<li>Click on a candidate in the list <i>Available candidates</i>.",
                "The candidate will now be added to the list of <i>Candidates of this cluster</i>.</li>",
                "<li>Click on a candidate in the list <i>Candidates of this cluster</i> to remove the candidate.</li>",
                "<li>Click on <i>Add all candidates</i> or <i>Remove all candidates</i> to add or remove all candidates from the list.</li>",
                "<li>Click <i>Save</i> at the bottom right of the window to save the changes.</li></ul>",

                "<p class='mb-0 pt-2 pb-0'><b>Add all candidates of a class</b></p>",
                "<p class='mt-0 mb-0 pb-0'>You can add all candidates of a class to a cluster at once. This is how:</p>",
                "<ul class='manual_bullet mb-0'><li>Select a class in the <i>Filter class</i> field in the frame <i>Filter candidates</i>.</li>",
                "<li>Then click on <i>Add all candidates</i> under the list of available candidates.</li></ul>",

                "<p class='mb-0 pt-2 pb-0'>By default, the list of available candidates shows only those candidates who do not yet belong to a cluster for this subject. ",
                "When the list of available candidates is empty, it means that all candidates belong to a cluster for this subject.<br>",
                "Tick the field <i>Show also candidates with cluster</i> to also display candidates who already belong to a cluster in the list of available candidates.</p>",
            ]),
        write_paragraph_body("img_lightbulb",
            [
                 "<p>If you accidentally delete a cluster or make other mistakes, you can click <i>Cancel</i>. ",
                 "The window will now close without saving the changes. ",
                 "Open the window again to display the last saved data.</p>",
            ]),
        "<div class='p-3 visibility_hide'>-</div>",
     ]
}
