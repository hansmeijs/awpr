// PR2023-05-13 added

    "use strict";

const man_corrector = {

/////////  NEDERLANDS //////////////////////////////
    nl: [
        write_paragraph_header("id_intro", "Gecommitteerden"),
        write_paragraph_body("",[
            "<p>Met de ingebruikname van AWP-online is de handtekening op papier vervangen door een digitale handtekening. ",
            "Dit geldt ook voor de goedkeuring van de behaalde scores door de gecommitteerden.</p>",
            "<p>In deze paragraaf wordt beschreven hoe dit in zijn werk gaat.</p>",
        ]),

        write_paragraph_header("id_corr_account", "Gebruikersaccount"),
        write_paragraph_body("",[

        "<p>Elke gecommitteerde krijgt één gebruikersaccount voor AWP-online. ",
        "De gebruikersaccounts worden uitgegeven door het Ministerie van Onderwijs, Wetenschap, Cultuur & Sport, Uitvoeringsorganisatie Onderwijs en Wetenschap (UOW). ",
        "UOW geeft voor elke gebruiker aan, tot welke scholen, afdelingen (Vsbo, Havo, Vwo), leerwegen en vakken de gebruiker toegang heeft. ",
        "Neem contact op met UOW als je vragen hebt met betrekking tot je account.</p>",
        "<p>Een uitzondering vormen de gecommitteerden van praktijkexamens. ",
        "Zij worden aangesteld door de school zelf en dienen hiervoor hun account van de school te gebruiken.</p>",

        "<p><b>Gebruikersaccount activeren</b><br>",
        "Wanneer UOW een gebruikersaccount heeft aangemaakt, stuurt AWP-online een e-mail naar het opgegeven e-mailadres van de gebruiker. ",
        "Deze e-mail bevat een link waarmee je je account kunt activeren.</p>",
        "<p>De activeringslink blijft zeven dagen geldig. Wanneer de link verlopen is moet je UOW vragen een e-mail met een nieuwe activeringslink te sturen.</p>",
        "<p>De e-mail ziet er als volgt uit:</p>",

        ]),
        write_image("img_corr_email_activate_ne"),

        write_paragraph_body("",[
            "<p>Als je op de link geklikt hebt, verschijnt het onderstaande venster.<br>",
            "Vul een wachtwoord in, herhaal het wachtwoord en klik op <i>Activeer je account</i>.<br>",
            "Onthoud je schoolcode (CURCOM), gebruikersnaam en wachtwoord om de volgende keer in te kunnen loggen.</p>",
        ]),

        write_image("img_corr_activate_account_ne"),

        write_paragraph_body("",[
            "<p>Wanneer de activering is gelukt verschijnt onderstaand venster.</p>"
        ]),

        write_image("img_corr_activate_succes_ne"),


        "<div class='p-3 visibility_hide'>-</div>"
    ],

/////////  ENGLISH //////////////////////////////
    en:  [
        write_paragraph_header("id_intro", "Second correctors"),
        write_paragraph_body("",[
            "<p>With the implementation of AWP-online, the signature on paper has been replaced by a digital signature.",
             "This also applies to the approval of the scores achieved by the second correctors.</p>",
             "<p>This section describes how to do this.</p>",
        ]),

        write_paragraph_header("id_corr_account", "User account"),
        write_paragraph_body("",[
            "<p>Each second correctors will receive a user account for AWP-online. ",
            "The user accounts are issued by the Division of Examinations of the Ministry of Education, Culture, Youth and Sport (DES). ",
            "DES indicates for each user which schools, departments (Vsbo, Havo, Vwo), learning paths and subjects the user has access to.",
            "Please contact DES if you have any questions regarding your account.</p>",

            "<p><b>Activate user account</b><br>",
            "When DES has created a user account, AWP-online will send an email to the specified email address of the user.",
            "This email contains a link to activate your account.</p>",
            "<p>The activation link remains valid for seven days. When the link has expired you must ask DES to send an email with a new activation link.</p>",
            "<p>The email looks like this:</p>",
        ]),

        write_image("img_corr_email_activate_en"),


        write_paragraph_body("",[
            "<p>After clicking on the link, the window below will appear.<br>",
            "Enter a password, repeat the password and click on <i>Activate your account</i>.<br>",
            "Remember your school code (SXMCOR), username and password to log in next time.</p>",        ]),

        write_image("img_corr_activate_account_en"),

        write_paragraph_body("",[
            "<p>If the activation has been successful, the window below will appear.</p>"
        ]),
        write_image("img_corr_activate_succes_en"),


        "<div class='p-3 visibility_hide'>-</div>"
    ]
}
