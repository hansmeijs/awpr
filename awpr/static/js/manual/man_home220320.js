// PR2021-07-18 added

"use strict";

console.log("+++++++ script 'man_home'")
const man_home = {
    nl: [
        write_paragraph_header("id_intro", "Welkom bij AWP-online"),
        write_paragraph_body("",
            ["<p>Welkom bij de geheel vernieuwde online versie van AWP. Het invoeren en verwerken van examengegevens wordt nu nog eenvoudiger.</p>",
                "<p>Maar zoals met alle nieuwe programma's zal de nieuwe opzet even wennen zijn. ",
                "Begin daarom op tijd met het aanmaken van accounts en het invoeren van gegevens. ",
                "We adviseren je dringend om de handleiding goed door te nemen voor je aan de slag gaat.</p>",
                "<p>Op deze pagina vind je veel handige tips voor het gebruik van AWP-online. ",
                "Ze maken het opzoeken van informatie een stuk makkelijker. Neem even de tijd ze door te lezen. Dat bespaart straks veel tijd en ergernis.</p>",

                "<p>Er zullen ongetwijfeld de nodige 'bugs' in het programma zitten. Laat het ons weten, dan kunnen we ze corrigeren. Ook tips om pagina's te verbeteren zijn welkom.</p>",

                "<p>Namens het Expertisecentrum voor Toetsen & Examens wensen we je veel succes in het gebruik van AWP-online.</p>"
            ]),

        write_paragraph_header("id_page_layout", "De pagina lay-out"),
        write_paragraph_body("",
            [            "<p class='pb-0'>Bovenaan de pagina is de <b>titelbalk</b> met de volgende knoppen:</p>",
                "<ul class='manual_bullet mb-0'><li>het <i>AWP logo</i>. Klik hierop om naar de startpagina te gaan;</li>",
                "<li>het <i>Examenjaar</i>. Als er meerdere examenjaren zijn kun je hierop klikken om naar een ander examenjaar te gaan;</li>",
                "<li>de <i>Afdeling van de school</i>. Als de school meerdere afdelingen heeft kun je hiermee een andere afdeling selecteren;</li>",
                "<li>de <i>Schoolcode</i> en <i>Naam van de school</i>;</li></ul>",
            "<p class='pb-0'>Als je op je <i>Gebruikersnaam</i> klikt verschijnt een drop-down menu met de volgende opties:</p>",
                "<ul class='manual_bullet mb-0'><li>de knop <i>Gebruikers</i> waarmee je naar de pagina <i>Gebruikers</i> kunt gaan. Deze optie is alleen beschikbaar als je systeembeheerder bent;</li>",
                "<li>de knop <i>Wijzig wachtwoord</i>;</li>",
                "<li>de knop <i>Nederlands</i> en <i>Engels</i> om de taal in te stellen;</li></ul>",
            "<p class='pb-0'>Tenslotte de knop <i>Uitloggen</i> en de <i>knop met het vraagteken</i> om naar de handleiding te gaan.</p>",
               "<p class='pb-0'>Met de knoppen op de <b>paginabalk</b> kun je naar een andere pagina gaan.</p>",
                "<p class='pb-0'>Onder de pagina balk is de <b>menubalk</b>. Afhankelijk van de pagina en je permissies heeft de menubalk verschillende knoppen, waarmee je bewerkingen kunt uitvoeren.</p>",
               "<p class='pb-0'>Dan is er een balk met een of meer <b>tabs</b>. Elke tab geeft een tabel met andere gegevens weer.",
            "<p class='pb-0'>De tweede regel van de tabel is de <b>filterregel</b> waarmee je de regels van de tabel kunt filteren.",
            "<p class='pb-0'>Ook op de <b>filterbalk</b>, dit is de grijze verticale balk links, staan er soms knoppen waarmee je een filter kunt instellen.</p>"
            ]),

        write_image("img_page_layout_ne"),

        write_paragraph_header("id_select_windowe", "Het selectie venster"),
        write_paragraph_body("",
            ["<p>Om eenvoudig een vak of een kandidaat te kunnen selecteren beschikt AWP over een handig <b>selectie venster</b>. ",
            "Hieronder zie je het venster waarmee je een vak kunt selecteren. Links is een lijst met de beschikbare vakken, rechts kun je enkele letters intypen.</p>",
            "<p>Er zijn twee manieren om een vak te selecteren: de eerste manier is het gewenste vak in de lijst op te zoeken en dan op het vak te klikken. ",
            "Het vak wordt geselecteerd en het venster sluit.</p>",
            "<p>Je kunt ook een paar letters van het vak intypen. Dan worden alleen de vakken met die letters in de naam of de afkorting in de lijst weergegeven. ",
            "In onderstaand voorbeeld is alleen de letter 'w' ingetypt. Er zijn 4 vakken met een 'w' in de naam of de afkorting. ",
            "Als je 'wis' intypt is er maar 1 vak over in de lijst: Wiskunde. De naam van het vak komt nu rechts in plaats van 'wis'. Klik op OK om het vak te selecteren.</p>",
            "<p>Als er weinig vakken zijn is het het snelste om het vak in de lijst op te zoeken. ",
            "Maar een kandidaat opzoeken gaat over het algemeen sneller met het intypen van een paar letters.</p>"
            ]),
        write_image("img_intro_select_window_ne"),

        write_paragraph_header("id_filterrow", "De filterregel"),
        write_paragraph_body("",
            ["<p>Als een tabel veel regels heeft is het niet handig om met de muis naar beneden te scrollen tot je de gewenste regel hebt gevonden. ",
                "Beter is het de regels te filteren met behulp van de <b>filterregel</b>, dit is de lege lichtgrijze regel onder de kolomnaam.</p>"
            ]),
        write_image("img_intro_filterrow_ne"),

        write_paragraph_body("",
            ["<p class='pb-0'>Bij <b>kolommen met tekst</b> kun je in de filterregel een of meer letters intypen, ",
                "dan worden alleen de regels weergegeven met die letters in de kolom. ",
                "Je kunt meerdere kolommen tegelijk filteren. ",
                "Er zijn een paar bijzondere tekens die je kunt intypen om te filteren:</p>"
            ]),

        write_paragraph_body("",
            ["<div class='mfc mx-2'>",
                    "<div class='mfl ml-2 pl-3'>#</div>",
                    "<div class='mfr'>Alleen de regels waarvan dit veld leeg is worden weergegeven.</div>",
                "</div>",
                "<div class='mfc mx-2'>",
                    "<div class='mfl ml-2 pl-3'>@</div>",
                    "<div class='mfr'>Alleen de regels waarvan dit veld is ingevuld worden weergegeven.</div>",
                "</div>"
            ]),

        write_paragraph_body("",
            ["<p>Je kunt het <b>filter wissen</b> door op de Escape toets te klikken.</p>"
            ]),
        write_paragraph_body("",
            ["<p class='pb-0'><b>Kolommen met een vinkje</b> kun je filteren door op de filterregel te klikken. ",
            "Achtereenvolgens verschijnen de volgende icoontjes:</p>",
                "<div class='mfc mx-2'>",
                    "<div class='mfl'><p class='tickmark_2_2'></p></div>",
                    "<div class='mfr'>Alleen de regels met een vinkje worden weergegeven.</div>",
                "</div>",
                "<div class='mfc mx-2'>",
                    "<div class='mfl'><p class='tickmark_2_1'></p></div>",
                    "<div class='mfr'>Alleen de regels zonder vinkje worden weergegeven.</div>",
                "</div>",
                "<div class='mfc mx-2'>",
                    "<div class='mfl'><p class='tickmark_2_0'></p></div>",
                    "<div class='mfr'>Alle regels worden weergegeven.</div>",
                "</div>"
            ]),

        write_paragraph_body("",
            ["<p class='pb-0'>Tenslotte kun je <b>kolommen met een cijfer</b> als volgt filteren:</p>"
            ]),
        write_paragraph_body("",
            ["<div class='mfc mx-2'>",
                "<div class='mfl_10pc ml-2'>=5,5</div>",
                "<div class='mfr_10pc ml-2'>Alleen regels met het cijfer 5,5 in deze kolom worden weergegeven.</div>",
            "</div>",
            "<div class='mfc mx-2'>",
                "<div class='mfl_10pc ml-2'>>=5,5</div>",
                "<div class='mfr_10pc ml-2'>Alleen cijfers gelijk aan of hoger dan 5,5 worden weergegeven.</div>",
            "</div>",
            "<div class='mfc mx-2'>",
                "<div class='mfl_10pc ml-2'><5,5</div>",
                "<div class='mfr_10pc ml-2'>Alleen cijfers lager dan 5,5 worden weergegeven.</div>",
            "</div>"
            ]),

        write_paragraph_header("id_hide_columns", "Kolommen verbergen"),
        write_paragraph_body("",
            ["<p>Zoals je het aantal regels kan beperken door te filteren, kun je <b>kolommen verbergen</b> met de knop <i>Kolommen verbergen</i>. ",
            "Hieronder zie je het venster waarmee je kolommen kunt weergeven of verbergen. ",
            "Links is een lijst met kolommen die worden verborgen, rechts is de lijst met kolommen die worden weergegeven. ",
            "Er zijn 'verplichte' kolommen die je niet kunt verbergen. Ze staan niet in de lijsten.</p>",
            "<p>Klik op een kolomnaam in een van de lijsten om hem naar de andere lijst te verplaatsen. ",
            "Klik op <i>OK</i> om de wijzigingen op te slaan. ",
            "AWP slaat de wijzigingen op in de <b>gebruikersinstellingen</b>, zodat je niet elke keer opnieuw de kolommen hoeft te verbergen.</p>"
            ]),
        write_image("img_intro_hide_columns_ne"),

    ],
    en: [

        write_paragraph_header("id_intro", "Welcome at AWP-online"),
        write_paragraph_body("",
            ["<p>Welcome at the completely renewed online version of AWP. Entering and processing exam data just got easier.</p>",
            "<p>But as with all new programs, the new setup will take some time getting used to. ",
            "Therefore, start on time with creating accounts and entering data. ",
            "We strongly advise you to read the manual carefully before you get started.</p>",
            "<p>On this page you will find many useful tips for using AWP-online. ",
            "They make looking up information a lot easier. Take a moment to read them. That will save a lot of time and aggravation.</p>",

            "<p>There will undoubtedly be some 'bugs' in the program. Let us know so we can correct them. Tips to improve pages are also welcome.</p>",

            "<p>On behalf of the Division of Examinations, we wish you good luck in using AWP-online.</p>",
            ]),

        write_paragraph_header("id_page_layout", "The page layout"),
        write_paragraph_body("",
            ["<p class='pb-0'>At the top of the page is the <b>title bar</b> with the following buttons:</p>",
                "<ul class='manual_bullet mb-0'><li>the <i>AWP logo</i>. Click this to go to the homepage;</li>",
                "<li>the <i>Exam year</i>. If there are several exam years, you can click on this to go to another exam year;</li>",
                "<li>the <i>Department of the school</i>. If the school has more than one department, you can use this to select another department;</li>",
                "<li>the <i>School code</i> and <i>Name of the school</i>;</li></ul>",
            "<p class='pb-0'>When you click on your <i>Username</i> a drop-down menu will appear with the following options:</p>",
                "<ul class='manual_bullet mb-0'><li>the <i>Users</i> button that takes you to the <i>Users</i> page. This option is only available if you are a System Administrator ;</li>",
                "<li>button <i>Change password</i>;</li>",
                "<li>button <i>Dutch</i> and <i>English</i> to set the language;</li></ul>",
            "<p class='pb-0'>Finally the <i>Logout</i> button and the <i>button with the question mark</i> to go to the manual.</p>",
               "<p class='pb-0'>The buttons on the <b>page bar</b> allow you to go to another page.</p>",
                "<p class='pb-0'>Below the page bar is the <b>menu bar</b>. Depending on the page and your permissions, the menu bar has different buttons with which you can perform operations.</p>" ,
               "<p class='pb-0'>Then there is a bar with one or more <b>tabs</b>. Each tab displays a table with different data.",
            "<p class='pb-0'>The second line of the table is the <b>filter row</b> which allows you to filter the rules of the table.",
            "<p class='pb-0'>Also on the <b>filter bar</b>, this is the gray vertical bar on the left, there are sometimes buttons with which you can set a filter.</p>"]),
        write_image("img_page_layout_ne"),

        write_paragraph_header("id_select_windowe", "The selection window"),
        write_paragraph_body("",
            ["<p>To be able to easily select a course or a candidate, AWP has a handy <b>selection window</b>. ",
            "Below you see the window with which you can select a course. On the left is a list with the available courses, on the right you can enter a few letters.</p>",
            "<p>There are two ways to select a course: the first way is to find the desired course in the list and then click on the course. ",
            "The box is selected and the window closes.</p>",
            "<p>You can also type in a few letters of the box. Then only the boxes with those letters in the name or abbreviation will be displayed in the list. ",
            "In the example below, only the letter 'w' was typed in. There are 4 boxes with a 'w' in the name or abbreviation.",
            "If you type 'delete' there is only 1 box left in the list: Mathematics. The name of the subject now appears on the right instead of 'delete'. Click OK to select the box.</p>",
            "<p>If there are few subjects, the fastest is to find the subject in the list.",
            "But looking up a candidate is generally faster with typing a few letters.</p>"
            ]),
        write_image("img_intro_select_window_en"),

        write_paragraph_header("id_filterrow", "The filter row"),
        write_paragraph_body("",
            ["<p>If a table has many rows it is not useful to scroll down with the mouse until you find the desired row. ",
                 "It is better to filter the rows using the <b>filter row</b>, this is the empty light grey row under the column name.</p>"
            ]),
         write_image("img_intro_filterrow_ne"),

        write_paragraph_body("",
            ["<p class='pb-0'>For <b>columns with text</b> you can type one or more letters in the filter row. ",
                "Then, only the rows with those letters in the column will be displayed. ",
                "You can filter multiple columns at once. ",
                "There are some special characters you can type to filter:</p>"]),


        write_paragraph_body("",
            [   "<div class='mfc mx-2'>",
                    "<div class='mfl ml-2 pl-3'>#</div>",
                    "<div class='mfr'>Only the rows where this field is empty are displayed.</div>",
                "</div>",
                "<div class='mfc mx-2'>",
                    "<div class='mfl ml-2 pl-3'>@</div>",
                    "<div class='mfr'>Only the rows for which this field is filled will be displayed.</div>",
                "</div>"]),


        write_paragraph_body("",
            ["<p>You can clear the <b>filter</b> by clicking the Escape key.</p>"]),


        write_paragraph_body("",
            [
            "<p class='pb-0'><b>Columns with a check mark</b> can be filtered by clicking on the filter line. ",
            "The following icons appear one after the other:</p>",
                "<div class='mfc mx-2'>",
                    "<div class='mfl'><p class='tickmark_2_2'></p></div>",
                    "<div class='mfr'>Only the rows with a check mark are displayed.</div>",
                "</div>",
                "<div class='mfc mx-2'>",
                    "<div class='mfl'><p class='tickmark_2_1'></p></div>",
                    "<div class='mfr'>Only the rows without a check mark are displayed.</div>",
                "</div>",
                "<div class='mfc mx-2'>",
                    "<div class='mfl'><p class='tickmark_2_0'></p></div>",
                    "<div class='mfr'>All rows are displayed.</div>",
                "</div>"]),

        write_paragraph_body("",
            ["<p class='pb-0'>Finally, you can filter <b>columns with a number</b> like this:</p>"]),


        write_paragraph_body("",
            ["<div class='mfc mx-2'>",
                "<div class='mfl ml-2'>=5,5</div>",
                "<div class='mfr ml-2'>Only rows with the number 5.5 in this column are displayed.</div>",
            "</div>",
            "<div class='mfc mx-2'>",
                "<div class='mfl ml-2'>>=5,5</div>",
                "<div class='mfr ml-2'>Only numbers equal to or greater than 5.5 are displayed.</div>",
            "</div>",
            "<div class='mfc mx-2'>",
                "<div class='mfl ml-2'><5,5</div>",
                "<div class='mfr ml-2'>Only numbers lower than 5.5 will be displayed.</div>",
            "</div>"]),

        write_paragraph_header("id_hide_columns", "Hide columns"),
        write_paragraph_body("",
            ["<p>As you can limit the number of rows by filtering, you can <b>hide columns</b> with the button <i>Hide columns</i>. ",
            "Below is the window that allows you to show or hide columns.",
            "Left is a list of columns that will be hidden, right is the list of columns that will be displayed.",
            "There are 'mandatory' columns that you cannot hide. They are not in the lists.</p>",
            "<p>Click a column name in one of the lists to move it to the other list.",
            "Click <i>OK</i> to save the changes.",
            "AWP saves the changes in the <b>user settings</b> so you don't have to hide the columns every time.</p>"
            ]),
        write_image("img_intro_hide_columns_en")
    ]
};
manual_dict.man_home = man_home;
