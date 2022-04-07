// PR2021-07-18 added

    "use strict";

const man_approve = {

/////////  NEDERLANDS //////////////////////////////
    nl: [
        write_paragraph_header("id_intro", "Goedkeuren en indienen van Ex-formulieren"),
        "<div class='mfc'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>Bij de indiening van de Ex-formulieren is de handtekening op papier vervangen door een digitale handtekening.</p>",
                "<p class='pb-0'>Het indienen van Ex-formulieren gaat in twee stappen:</p>",
                "<ul class='manual_bullet mb-0'><li>De eerste stap is het <b>goedkeuren</b> van de vakken, scores of cijfers door de voorzitter, secretaris, examinator en eventueel gecommitteerde.</li>",
                "<li>De tweede stap is het <b>indienen</b> van het Ex-formulier door de voorzitter of secretaris.</li></ul>",
            "</div>",
        "</div>",

        write_paragraph_header("id_digital_signature", "De digitale handtekening"),
        "<div class='mfc'>",
            "<div class='mfl'>",
            "</div>",
            "<div class='mfr'>",
                "<p>In plaats van Ex-formulieren te ondertekenen, dienen voortaan voorzien te worden van een digitale handtekening.</p>",

                "<p class='mb-0 pt-2 pb-0'>Hiervoor gelden de volgende regels:</p>",
                "<ul class='manual_bullet mb-0 pb-2'><li>Alleen een gebruiker, die behoort tot de gebruikersgroep <i>Voorzitter</i>, <i>Secretaris</i>, <i>Examinator</i> of <i>Gecommitteerde</i> kan een digitale handtekening zetten.</li>",
                "<li>Meerdere gebruikers kunnen tot deze gebruikersgroep behoren. Een school kan dus meerdere voorzitters en secretarissen hebben.</li>",
                "<li>Een gebruiker kan niet tegelijk voorzitter en secretaris zijn.</li>",
                "<li>Een voorzitter kan niet tevens als secretaris ondertekenen.</li>",
                "<li>Een voorzitter of secretaris kan tevens als examinator ondertekenen.</li>",
                "<li>Een gecommitteerde kan niet tevens als voorzitter, secretaris of examinator ondertekenen.</li>",
                "<li>Alleen een voorzitter of secretaris kan Ex-formulieren indienen en diploma's en definitieve cijferlijsten printen.</li></ul>",

                "<p>De naam en het e-mail adres van de gebruiker dienen als identificatie. ",
                "Het is daarom belangrijk dat je zorgvuldig omgaat met je gebruikersnaam en wachtwoord. ",
                "Je moet een persoonlijk e-mail adres gebruiken. Het is niet toegestaan het algemene e-mail adres van de school te gebruiken, maar 'kevin.martina@rkcs.org' is wel toegestaan.</p>",
                "<p>Elke wijziging van de naam of het e-mail adres van de gebruiker wordt vastgelegd in een logbestand. ",
                "Hiermee is naderhand altijd terug te vinden wie welke wijzigingen heeft aangebracht.</p>",

                "<p class='mb-0 pb-0'>Als extra beveiliging dient de gebruiker bij het indienen van Ex-formulieren of het uitprinten van diploma's of cijferlijsten een verificatiecode in te voeren. ",
                "Deze verificatiecode wordt per e-mail naar de gebruiker verstuurd.</p>",
             "</div>",
        "</div>",

        write_paragraph_header("id_approve", "Goedkeuren van vakken, scores of cijfers"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>In de pagina's <i>Vakken</i> en <i>Cijfers</i> vind je in de menubalk een knop met respectievelijk: <i>Vakken goedkeuren</i> en  <i>Cijfers goedkeuren</i>. ",
                "Klik hierop en het goedkeuringsvenster verschijnt.</p>",
            "</div>",
        "</div>",
        write_image("img_studsubj_approve_menu_ne"),

        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>In het kader met 'Selectie van de vakken die worden goedgekeurd' staat welke vakken worden goedgekeurd. ",
                "Je kunt een leerweg, sector, profiel en vak selecteren. ALs je 'PBL' en 'Papiamentu' selecteert worden alleen de vakken 'Papiamentu' van de kandidaten in de leerweg 'PBL' goedgekeurd. ",
                "Je kunt ook alle vakken in een keer goedkeuren. Klik dan eerst in de grijze verticale balk links op <i>Alle vakken weergeven</i>.</p> ",
                "<p>Zodra het venster is geopend controleert AWP of er al vakken zijn goedgekeurd of ingediend. ",
                "Klik op <i>Vakken goedkeuren</i>  om de geselecteerde vakken goed te keuren. ",
                "Je kunt goedkeuringen weer verwijderen door op de knop <i>Goedkeuringen verwijderen</i> te klikken.</p>",
            "</div>",
        "</div>",
        write_image("img_studsubj_mod_approve_ne"),

        write_paragraph_header("id_approve_icon", "Het goedkeurings-icoontje"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p class='mt-2XX diamond_0_4XX'></p></div>",
            "<div class='mfr'>",
                "<p class='pb-0'>In de lijst met vakken of cijfers van kandidaten staat een icoontje in de vorm van een ruit. ",
                "De betekenis ervan is als volgt:</p>",
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
                            "<div class='mfl'><p class='diamond_0_4'></p></div>",
                            "<div class='mfr'>Dit vak is op het Ex1-formulier ingediend.</div>",
                        "</div>",
                    "</div>",
                "</div>",

                "<p class='pb-0'>Bij het goedkeuren van cijfers of scores is de ruit in vieren verdeeld.</p>",
                "<div class='mfc mb-2'>",
                    "<div class='mfl'><p></p></div>",
                    "<div class='mfr mb-0'>",
                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_0_1'></p></div>",
                            "<div class='mfr'>Dit cijfer is goedgekeurd door de voorzitter.</div>",
                        "</div>",
                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_0_2'></p></div>",
                            "<div class='mfr'>Dit cijfer is goedgekeurd door de secretaris.</div>",
                        "</div>",
                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_1_0'></p></div>",
                            "<div class='mfr'>Dit cijfer is goedgekeurd door de examinator.</div>",
                        "</div>",
                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_2_0'></p></div>",
                            "<div class='mfr'>Dit cijfer is goedgekeurd door de gecommiteerde.</div>",
                        "</div>",
                    "</div>",
                "</div>",

                "<p class='pb-0'>Klik op het icoontje om het vak goed te keuren. ",
                "Klik op het icoontje van een goedgekeurd vak om de goedkeuring te verwijderen.</p>",

                "<p>Alleen een voorzitter of secretaris kunnen vakken goedkeuren.<br>",
                "De voorzitter, secretaris en examinator kunnen cijfers van het schoolexamen goedkeuren.<br>",
                "De voorzitter, secretaris, examinator en gecommitteerde kunnen scores van het centraal examen goedkeuren.</p>",

                "<p class='pb-0'>Een voor een de vakken goedkeuren is natuurlijk onbegonnen werk, ",
                "maar het is handig dat je de goedkeuring van een vak kunt verwijderen, als er vragen over zijn.</p>",
            "</div>",
        "</div>",

        write_paragraph_header("id_prelim_exform", "Het voorlopige Ex-formulier"),

        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>Voordat het Ex-formulier wordt ingediend kun je een voorlopig Ex-formulier downloaden, om te controleren of alle gegevens correct zijn.</p>",
                "<p class='pb-0'>Het verschil met het definitieve Ex-formulier is:</p>",
                "<ul class='manual_bullet mb-0'><li>er is een regel VOORLOPIG Ex1-FORMULIER toegevoegd;</li>",
                "<li>vakken hoeven niet eerst te worden goedgekeurd;</li>",
                "<li>alle kandidaten verschijnen op het formulier, ook als een kandidaat geen vakken heeft;</li>",
                "<li>alle vakken verschijnen op het formulier, ook als ze niet zijn goedgekeurd;</li>",
                "<li>de regel 'Digitaal ondertekend door' en de namen van de voorzitter en secretaris worden niet weergegevens;</li>",
                "<li>het voorlopige Ex-formulier wordt niet opgeslagen op de server.</li></ul>",
            "</div>",
        "</div>",

        write_paragraph_header("id_submit_exform", "Het Ex-formulier indienen"),

        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>Als alle vakken zijn goedgekeurd door de voorzitter en secretaris kan het Ex1-formulier worden ingediend. ",
                "Klik in de menubalk op <i>Ex-formulier indienen</i>. Het onderstaande venster verschijnt.</p>",
            "</div>",
        "</div>",
        write_image("img_studsubj_submit_step1_ne"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>Als niet alle vakken zijn goedgekeurd verschijnt er een waarschuwing. Sluit het venster en keur de resterende vakken goed. ",
                "Ook als er niet-goedgekeurde vakken zijn kun je het Ex1-formulier indienen. De niet-goedgekeurde vakken worden dan niet opgenomen in het Ex-formulier. ",
                "We raden aan om alle vakken goed te keuren. Wanneer een vak niet is goedgekeurd en ingediend kunnen er later geen cijfers worden ingevoerd.</p>",

                "<p>Om het Ex1-formulier in te kunnen dienen heb je een 6-cijferige verificatiecode nodig. ",
                "Klik op <i>Verificatiecode aanvragen</i>. AWP stuurt nu een e-mail met de verificatiecode naar het e-mail adres van de gebruiker. ",
                "De verificatiecode blijft 30 minuten geldig. Als de verificatiecode is verlopen kun je een nieuwe aanvragen.</p>",
                "<p>Vul de verificatiecode in en klik op <i>Ex1-formulier indienen</i>. ",
                "Het Ex1-formulier wordt nu aangemaakt en opgeslagen op de server. Hiermee is het Ex1-formulier ingediend. De gegevens zijn nu zichtbaar voor het ETE en de Inspectie.</p>",

            "</div>",
        "</div>",
        write_image("img_studsubj_submit_step2_ne"),

        write_paragraph_header("id_submitted_exforms", "Lijst met ingediende Ex-formulieren"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>De ingediende Ex-formulieren worden opgeslagen op de server. ",
                "Je kunt ze altijd opnieeuw downloaden. Klik op de tab <i>Ingediende Ex-formulieren</i>. De lijst met Ingediende Ex-formulieren verschijnt. Klik op <i>Download</i> om het gewenste Ex-formulieren te downloaden..</p>",
            "</div>",
        "</div>",
        write_image("img_studsubj_submitted_exforms_ne"),

        "<div class='p-3 visibility_hide'>-</div>",
    ],
/////////  ENGLISH //////////////////////////////
    en:  [
        write_paragraph_header("id_intro", "Approve and submit Ex forms"),
        "<div class='mfc'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>When submitting the Ex forms, the signature on paper has been replaced by a digital signature.</p>",
                 "<p class='pb-0'>Submitting Ex forms is done in two steps:</p>",
                 "<ul class='manual_bullet mb-0'><li>The first step is the <b>approval</b> of the subjects, scores or grades by the chairperson, secretary, examiner and possibly the corrector.</li>",
                 "<li>The second step is the <b>submission</b> of the Ex-form by the chairperson or secretary.</li></ul>",
            "</div>",
        "</div>",

        write_paragraph_header("id_digital_signature", "The digital signature"),
        "<div class='mfc'>",
            "<div class='mfl'>",
            "</div>",
            "<div class='mfr'>",
                "<p>Instead of signing Ex forms, from now on, a digital signature must be provided.</p>",

                "<p class='mb-0 pt-2 pb-0'>The following rules apply:</p>",
                "<ul class='manual_bullet mb-0 pb-2'><li>Only a user belonging to the user group <i>Chairperson</i>, <i>Secretary</i>, <i>Examinator</i> or <i>Gecommitteerde</i> can put a digital signature.</li>",
                "<li>Multiple users can belong to a user group. A school can therefore have several chairpersons and secretaries.</li>",
                "<li>A user cannot be chairperson and secretary at the same time.</li>",
                "<li>A chairperson cannot also sign as secretary.</li>",
                "<li>A chairperson or secretary can also sign as examiner.</li>",
                "<li>A corrector may not also sign as chairperson, secretary or examiner.</li>",
                "<li>Only a chairperson or secretary can submit Ex forms and print diplomas and final grade lists.</li></ul>",

                "<p>The user's name and email address serve as identification. ",
                "It is therefore important that you handle your username and password with care. ",
                "You must use a personal email address. You are not allowed to use the general email address of your school, but 'kevin.martina@svobe.org' is allowed.</p>",
                "<p>Any change to the user's name or email address is logged in a log file. ",
                "This always allows you to find out who made which changes afterwards. </p>",

                "<p class='mb-0 pb-0'>As extra security, the user must enter a verification code when submitting Ex forms or printing diplomas or lists of marks. ",
                "This verification code will be emailed to the user.</p>",
             "</div>",
        "</div>",

        write_paragraph_header("id_approve", "Approve subjects, scores or grades "),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                  "<p>In the pages <i>Subjects</i> and <i>Grades</i> you will find in the menu bar a button with respectively: <i>Approve subjects</i> and <i>Approve grades</i>.",
                 "Click this and the approval window will appear.</p>",
            "</div>",
        "</div>",
        write_image("img_studsubj_approve_menu_en"),

        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                 "<p>The frame with 'Selection of the subjects to be approved' shows which subjects will be approved. ",
                 "You can select a 'leerweg', 'sector', 'profiel' and subject. If you select 'PBL' and 'Papiamentu', only the subjects 'Papiamentu' of the candidates in the leerweg 'PBL' will be approved.",
                 "You can also approve all subjects at once. First click in the grey vertical bar on the left on <i>Show all subjects</i>.</p> ",
                 "<p>Once the window is opened, AWP will check if any subjects have already been approved or submitted. ",
                 "Click <i>Approve subjects</i> to approve the selected subjects. ",
                 "You can remove approvals again by clicking the <i>Remove approvals</i> button.</p>",
            "</div>",
        "</div>",
        write_image("img_studsubj_mod_approve_en"),

        write_paragraph_header("id_approve_icon", "The approval icon"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p class='mt-2XX diamond_0_4XX'></p></div>",
            "<div class='mfr'>",
                "<p class='pb-0'>In the list of subjects or grades of candidates there is an icon in the shape of a diamond. ",
                "Its meaning is as follows:</p>",
                "<div class='mfc mb-2'>",
                    "<div class='mfl'><p></p></div>",
                    "<div class='mfr mb-0'>",
                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_0_0'></p></div>",
                            "<div class='mfr'>This subject has not yet been approved.</div>",
                        "</div>",
                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_2_1'></p></div>",
                            "<div class='mfr'>This subject has been approved by the chairperson.</div>",
                        "</div>",
                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_1_2'></p></div>",
                            "<div class='mfr'>This subject has been approved by the secretary.</div>",
                        "</div>",
                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_3_3'></p></div>",
                            "<div class='mfr'>This subject has been approved by the chairperson and the secretary.</div>",
                        "</div>",

                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_0_4'></p></div>",
                            "<div class='mfr'>This subject was submitted on the Ex1 form.</div>",
                        "</div>",
                    "</div>",
                "</div>",

                "<p class='pb-0'>When approving grades or scores, the diamond is divided into four.</p>",
                "<div class='mfc mb-2'>",
                    "<div class='mfl'><p></p></div>",
                    "<div class='mfr mb-0'>",
                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_0_1'></p></div>",
                            "<div class='mfr'>This grade has been approved by the chair.</div>",
                        "</div>",
                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_0_2'></p></div>",
                            "<div class='mfr'>This grade has been approved by the secretary.</div>",
                        "</div>",
                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_1_0'></p></div>",
                            "<div class='mfr'>This grade has been approved by the examiner.</div>",
                        "</div>",
                        "<div class='mfc'>",
                            "<div class='mfl'><p class='diamond_2_0'></p></div>",
                            "<div class='mfr'>This grade has been approved by the reviewer.</div>",
                        "</div>",
                    "</div>",
                "</div>",

                "<p class='pb-0'>Click the icon to approve the subject. ",
                "Click on the icon of an approved subject to remove the approval.</p>",

                "<p>Only a chairperson or secretary can approve subjects.<br>",
                "The chairperson, secretary and examiner can approve grades of the school examination.<br>",
                "The chairperson, secretary, examiner and examiner can approve scores of the central exam.</p>",

                "<p class='pb-0'>Approving the subjects one by one is of subjects impossible, ",
                "but it's handy that you can remove the approval of a subject, if there are questions about it.</p>",
            "</div>",
        "</div>",

        write_paragraph_header("id_prelim_exform", "The preliminary Ex form "),

        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>Before submitting the Ex-form, you can download a preliminary Ex-form to verify that all details are correct.</p>",
                "<p class='pb-0'>The difference with the final Ex form is:</p>",
                "<ul class='manual_bullet mb-0'><li>A PRELIMINARY Ex1 FORM line has been added;</li>",
                "<li>subjects do not need to be approved first;</li>",
                "<li>all candidates appear on the form, even if a candidate has no subjects;</li>",
                "<li>all subjects appear on the form, even if they are not approved;</li>",
                "<li>the line 'Digitally signed by' and the names of the chairperson and secretary are not displayed;</li>",
                "<li>the preliminary Ex form is not saved on the server.</li></ul>",
            "</div>",
        "</div>",

        write_paragraph_header("id_submit_exform", "Submitting the Ex form "),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>If all subjects have been approved by the chairperson and secretary, the Ex1 form can be submitted.",
                "Click <i>Submit Ex Form</i> in the menu bar. The window below will appear.</p>",
            "</div>",
        "</div>",
        write_image("img_studsubj_submit_step1_en"),
        "<div class='mfc mb-2'>",
            "<div class='mfl'><p></p></div>",
            "<div class='mfr'>",
                "<p>If not all subjects have been approved, a warning will appear. Close the window and approve the remaining subjects. ",
                "Even if there are unapproved subjects, you can submit the Ex1 form. The non-approved subjects will then not be included in the Ex form.",
                "We recommend approving all subjects. If a subject is not approved and submitted, no grades can be entered later.</p>",

                "<p>To submit the Ex1 form you need a 6-digit verification code.",
                "Click <i>Request Verification Code</i>. AWP will now send an email with the verification code to the user's email address.",
                "The verification code will remain valid for 30 minutes. If the verification code has expired, you can request a new one.</p>",
                "<p>Enter the verification code and click <i>Submit Ex1 Form</i>.",
                "The Ex1 form is now being created and saved on the server. With this, the Ex1 form has been submitted. The data is now visible to the Division Of Examinations and the Inspectorate Division.</p>",
            "</div>",
        "</div>",
        write_image("img_studsubj_submit_step2_en"),

        write_paragraph_header("id_submitted_exforms", "List of Ex forms submitted "),
        "<div class='mfc mb-2'>",
             "<div class='mfl'><p></p></div>",
             "<div class='mfr'>",
                 "<p>The submitted Ex forms are stored on the server. ",
                 "You can always download them again. Click on the <i>Submitted Ex Forms</i> tab. ",
                 "The list of Submitted Ex Forms appears. Click on <i>Download</i> to download the desired Ex Form.</p>",
             "</div>",
         "</div>",
        write_image("img_studsubj_submitted_exforms_en"),

        "<div class='p-3 visibility_hide'>-</div>",

    ]
}
