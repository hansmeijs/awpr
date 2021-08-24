// PR2021-07-18 added

    "use strict";

const man_approve = {

    nl: [
        "<div class='mfc mt-4 mb-0'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<h4 class='px-2'>Goedkeuren en indienen van Ex-formulieren</h4>",
            "</div>",
        "</div>",

        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>Bij de indiening van de Ex-formulieren is de handtekening op papier vervangen door een digitale handtekening.</p>",
                "<p class='pb-0'>Het indienen van Ex-formulieren gaat in twee stappen:</p>",
                "<ul class='manual_bullet'><li>De eerste stap is het <b>goedkeuren</b> van de vakken, scores of cijfers door de voorzitter, secretaris en eventueel gecommitteerde.</li>",
                "<li>De tweede stap is het <b>indienen</b> van het Ex-formulier door de voorzitter of secretaris.</li></ul>",
            "</div>",
        "</div>",

        "<div id='id_digital_signature' class='mfc mt-4'>",
            "<div class='mfl'></div>",
            "<div class='mfr'>",
                "<h4 class='px-2'>De digitale handtekening</h4>",
            "</div>",
        "</div>",
        "<div class='mfc mb-2'>",
            "<div class='mfl'>",
            "</div>",
            "<div class='mfr'>",
                "<p>In plaats van Ex-formulieren te ondertekenen, dienen de voorzitter en secretaris ze voortaan te voorzien van een digitale handtekening.<br>",
                "<p>Alleen een gebruiker, die behoort tot de gebruikersgroep <i>Voorzitter</i> of <i>Secretaris</i>, kan een digitale handtekening zetten. ",
                "Een gebruiker kan niet tegelijk voorzitter en secretaris zijn. ",
                "Voor gecommitteerden is er een aparte gebruikersgroep <i>Gecommitteerden</i>.</p>",

                "<p>De naam en het e-mail adres van de gebruiker dienen als identificatie. ",
                "Het is daarom belangrijk dat je zorgvuldig omgaat met je gebruikersnaam en wachtwoord. </p>",
                "<p>Elke wijziging van de naam of het e-mail adres van de gebruiker wordt vastgelegd in een logbestand. ",
                "Hiermee is naderhand altijd terug te vinden wie welke wijzigingen heeft aangebracht.</p>",

                "<p>Als extra beveiliging dient de gebruiker bij het indienen van Ex-formulieren of het uitprinten van diploma's of cijferlijsten een verificatiecode in te voeren. ",
                "Deze verificatiecode wordt per e-mail naar de gebruiker verstuurd.</p>",
             "</div>",
        "</div>",

        "<div id='id_approve' class='mfc mt-4'>",
            "<div class='mfl'></div>",
            "<div class='mfr'>",
                "<h4  class='px-2'>Goedkeuren van vakken, scores of cijfers</h4>",
            "</div>",
        "</div>",

        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>In de pagina's <i>Vakken</i> en <i>Cijfers</i> vind je in de menubalk een knop met respectievelijk: <i>Vakken goedkeuren</i> en  <i>Cijfers goedkeuren</i>. ",
                "Klik hierop en het goedkeuringsvenster verschijnt.</p>",
            "</div>",
        "</div>",

        set_image_div("img_studsubj_approve_menu_ne"),

        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>In het kader met 'Selectie van de vakken die worden goedgekeurd' staat welke vakken worden goedgekeurd. ",
                "Je kunt een leerweg, sector, profiel en vak selecteren. ALs je 'PBL' en 'Papiamentu' selecteert worden alleen de vakken 'Papiamentu' van de kandidaten in de leerweg 'PBL' goedgekeurd. ",
                "De filters telle  Je kunt in een keer Zodra het venster is geopend controleert AWP eerst of er al vakken zijn de vakken. In de pagina's <i>Vakken</i> en <i>Cijfers</i> vind je in de menubalk een knop met respectievelijk: <i>Vakken goedkeuren</i> en  <i>Cijfers goedkeuren</i>. ",
                "Klik hierop en het goedkeuringsvenster verschijnt.</p>",
                "<p>Zodra het venster is geopend controleert AWP eerst of er al vakken zijn de vakken. In de pagina's <i>Vakken</i> en <i>Cijfers</i> vind je in de menubalk een knop met respectievelijk: <i>Vakken goedkeuren</i> en  <i>Cijfers goedkeuren</i>. ",
                "Klik hierop en het goedkeuringsvenster verschijnt.</p>",
            "</div>",
        "</div>",

        set_image_div("img_studsubj_mod_approve_ne"),

        "<div class='mfc mb-2'>",
            "<div class='mfl'><p class='mt-2 diamond_3_4'></p></div>",
            "<div class='mfr'>",
                "<p class='pb-0'><b>Het goedkeuring icoontje</b></p>",

                "<p class='pb-0'>In de lijst met vakken of cijfers van kandidaten staat achter het vak, cijfer of score een icoontje in de vorm van een ruit. De betekenis ervan is als volgt:</p>",

                "<div class='mfc mb-2'>",
                    "<div class='mfl'><p></p></div>",
                    "<div class='mfr mb-0'>",
                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_0_0'></p></div>",
                            "<div class='mfr'>Dit vak is nog niet goedgekeurd.</div>",
                        "</div>",
                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_2_1'></p></div>",
                            "<div class='mfr'>Dit vak is goedgekeurd door de voorzitter.</div>",
                        "</div>",
                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_1_2'></p></div>",
                            "<div class='mfr'>Dit vak is goedgekeurd door de secretaris.</div>",
                        "</div>",
                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_3_3'></p></div>",
                            "<div class='mfr'>Dit vak is goedgekeurd door de voorzitter en de secretaris.</div>",
                        "</div>",

                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_3_4'></p></div>",
                            "<div class='mfr'>Dit vak is op het Ex1-formulier ingediend.</div>",
                        "</div>",
                    "</div>",
                "</div>",

                "<p class='pb-0'>Bij het goedkeuren van cijfers of scores is de ruit in vieren verdeeld.</p>",

                "<div class='mfc mb-2'>",
                    "<div class='mfl'><p></p></div>",
                    "<div class='mfr mb-0'>",
                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_2_2'></p></div>",
                    "<div class='mfr'>Een donker segment betekent dat het cijfer of de score is goedgekeurd ",
                    "door respectievelijk de voorzitter, secretaris, eerste gecommitteerde en tweede gecommitteerde.</div>",
                        "</div>",
                    "</div>",
                "</div>",
            "</div>",
        "</div>",
    ],

    en:  [ "<div id='id_step01' class='mfc mt-4'>",
            "<div class='mfl'></div>",
            "<div class='mfr'>",
                "<h4  class='px-2'>Approve and submit Ex forms</h4>",
            "</div>",
        "</div>"]
}

//========= image_div  ============= PR2021-08-24
function write_paragraph(par_id, dispay_txt){
    return ["<div id='", par_id, "' class='mfc mt-4'>",
            "<div class='mfl'></div>",
            "<div class='mfr'>",
                "<h4  class='px-2'>", dispay_txt, "</h4>",
            "</div>",
        "</div>"
        ].join("");

//========= image_div  ============= PR2021-08-14
function set_image_div(img_class){
    return ["<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<div class='", img_class, "'></div>",
            "</div>",
        "</div>"
        ].join("");
}
