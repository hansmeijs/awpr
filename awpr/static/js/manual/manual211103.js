// PR2021-06-10 added

let user_lang =  null;

document.addEventListener('DOMContentLoaded', function() {
    "use strict";

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    const href_page = get_attr_from_el(el_data, "data-page");
    const data_paragraph = get_attr_from_el(el_data, "data-paragraph");
    const data_lang = get_attr_from_el(el_data, "data-lang");

    console.log ('href_page', href_page)
    console.log ('data_paragraph', data_paragraph)
    console.log ('data_lang', data_lang)

    let html_upload_list = [];
    user_lang = (data_lang) ? data_lang : null;

// - Loop through all dropdown buttons to toggle between hiding and showing its dropdown content - This allows the user to have multiple dropdowns without any conflict */
// --- highlight SBR btn of selected page,
    const el_sidenav = document.getElementById("id_sidenav");
    const dropdown_els = el_sidenav.getElementsByClassName("dropdown-btn");

    for (let i = 0, el; el = dropdown_els[i]; i++) {
        const btn_page = (el.id) ? el.id.slice(7) : null; // "id_btn_intro"
        console.log (".... btn_page", btn_page ," href_page", href_page)

        if (btn_page === href_page) {
            SelectBtn(el);
        };

        el.addEventListener("click", function() {HandleDropdownClicked(el)});

    }

    LoadPage(href_page, data_paragraph);

})  // document.addEventListener('DOMContentLoaded', function()

//========= HandleDropdownClicked  ============= PR2021-07-30
    function btn_click(page){
        console.log( "===== HandleDropdownClicked  ========= ");
        DeselectAll();
        SelectBtn(el);

        const el_id = el.id  // "id_btn_intro"
        const btn_page = (el_id) ? el_id.slice(7) : null;
        console.log (".... btn_page", btn_page)
        LoadPage(btn_page);
      };  // HandleDropdownClicked


//========= LoadPage  ============= PR2021-07-30 PR2021-10-30
    function LoadPage(page, data_paragraph){
        console.log( "===== LoadPage  ========= ");
        console.log( "page", page);
        console.log( "data_paragraph", data_paragraph);
        console.log( "user_lang", user_lang);

        const is_en = (user_lang === "en");
        console.log( "is_en", is_en);
        const html_dict = (page === "home") ? man_home :
                        (page === "user") ? man_user :
                        (page === "upload") ? man_upload :
                        (page === "studsubj") ? man_studsubj :
                        (page === "approve") ? man_approve :
                        (page === "mailbox") ? man_mailbox : null;
        //console.log( "html_dict", html_dict);

        const html_list = (html_dict) ? (user_lang === 'en' && html_dict.en) ?  html_dict.en :  html_dict.nl : null;
        //console.log( "html_list", html_list);

        const html_str = (html_list && html_list.length) ? html_list.join('') : (is_en) ? "<h4 class='p-5'> This page is not available yet.</h4>" : "<h4 class='p-5'> Deze pagina is nog niet beschikbaar.</h4>";

        document.getElementById("id_content").innerHTML = html_str;

        FillSideNav(is_en);

        SelectBtnAndDeselctOthers("id_btn_" + page )

        if (data_paragraph){
            GotoParagraph(data_paragraph)
        };

    };  // LoadPage

//========= SelectBtn  ============= PR2021-07-30
    function SelectBtn(el){
        console.log( "===== SelectBtn  ========= ");
        console.log( "el.id", el.id);
        el.classList.add("active");
        const el_dropdown = document.getElementById(el.id + "_dropdown")
        add_or_remove_class (el_dropdown, "display_block", true, "display_hide");
    } // SelectBtn

//========= DeselectAll  ============= PR2021-07-30
    function DeselectAll(){
        //console.log( "===== DeselectAll  ========= ");

        const el_sidenav = document.getElementById("id_sidenav");
        const dropdown_els = el_sidenav.getElementsByClassName("dropdown-btn");
        for (let i = 0, el; el = dropdown_els[i]; i++) {
            el.classList.remove("active");
            const el_dropdown = document.getElementById(el.id + "_dropdown");
            add_or_remove_class (el_dropdown, "display_hide", true, "display_block");
        }
    } // DeselectAll

//========= SelectBtnAndDeselctOthers  ============= PR2021-08-17
    function SelectBtnAndDeselctOthers(sel_btn_id){
        console.log( "===== SelectBtnAndDeselctOthers  ========= ");

        const el_sidenav = document.getElementById("id_sidenav");
        const dropdown_els = el_sidenav.getElementsByClassName("dropdown-btn");
        for (let i = 0, el; el = dropdown_els[i]; i++) {
            const is_sel_btn = (sel_btn_id && sel_btn_id === el.id);

            if (is_sel_btn){
                el.classList.add("active");
            } else {
                el.classList.remove("active");
            }
            const el_dropdown = document.getElementById(el.id + "_dropdown");
            const display_str = (is_sel_btn) ? "block" : "none";
            if(el_dropdown) {el_dropdown.style.display = display_str};

        }
    } // SelectBtnAndDeselctOthers

//========= FillSideNav  ============= PR2021-08-23
    function FillSideNav(is_en){
        console.log( " ===  FillSideNav  ===");
        //console.log("is_en", is_en)

        const sbr_list = (!is_en) ? [

/////////  NEDERLANDS //////////////////////////////
        get_dropdown_button("home", "id_intro", "id_btn_intro", "Welkom bij AWP-online", [
            ["id_page_layout", "De lay-out van de pagina's"],
            ["id_select_windowe", "Het selectie venster"],
            ["id_filterrow", "De filterregel"],
            ["id_hide_columns", "Kolommen verbergen"],
            ]),

        get_dropdown_button("upload", "id_intro", "id_btn_upload_data", "Gegevens uploaden", [
            ["id_upload_step01", "Stap 1: Selecteer een Excel bestand"],
            ["id_validate_subjects", "Controle op de samenstelling van de vakken"],
            ["id_enter_subjects", "Vakken van kandidaten invoeren"],
            ]),

        get_dropdown_button("studsubj", "id_intro", "id_btn_studsubj", "Vakken van kandidaten", [
            ["id_filter_subjects", "Vakken filteren"],
            ["id_validate_subjects", "Controle op de samenstelling van de vakken"],
            ["id_enter_subjects", "Vakken van kandidaten invoeren"],
            ]),

        get_dropdown_button("approve", "id_intro", "id_btn_approve", "Goedkeuren en indienen van Ex-formulieren", [
            ["id_digital_signature", "De digitale handtekening"],
            ["id_approve", "Goedkeuren van vakken, scores of cijfers"],
            ["id_approve_icon", "Het goedkeurings-icoontje"],
            ["id_prelim_exform", "Het voorlopige Ex-formulier"],
            ["id_submit_exform", "Het Ex-formulier indienen"],
            ["id_submitted_exforms", "Lijst met ingediende Ex-formulieren"],
            ]),

        get_dropdown_button("mailbox", "id_intro_mailbox", "id_btn_mailbox", "Berichtenservice", [
            ["id_mailbox_read_message", "Berichten lezen"],
            ["id_mailbox_create_message", "Bericht aanmaken"],
            ["id_mailbox_recipients", "Geadresseerden"],
            ["id_mailbox_mailinglist", "Verzendlijsten"],
            ]),

        "</div>",
        "<div class='my-4'>.</div>"
        ] :

/////////  ENGLISH //////////////////////////////
        [
        get_dropdown_button("home", "id_intro", "id_btn_intro", "Welcome at AWP-online", [
            ["id_page_layout", "The layout of the pages"],
            ["id_select_windowe", "The selection window"],
            ["id_filterrow", "The filter row"],
            ["id_hide_columns", "Hide columns"],
            ]),
        get_dropdown_button("studsubj", "id_intro", "id_btn_studsubj", "Subjects of candidates", [
            ["id_filter_subjects", "Vakken filteren"],
            ["id_approve", "Approve courses, scores or grades"],
            ["id_approve_icon", "The approval icon"],
            ["id_prelim_exform", "The preliminary Ex-form"],
            ["id_submit_exform", "Submit the Ex form"],
            ["id_submitted_exforms", "List of submitted Ex forms"],

            ]),

        get_dropdown_button("approve", "id_intro", "id_btn_approve", "Approve and submit Ex forms", [
            ["id_digital_signature", "The digital signature"],
            ["id_approve", "Approve courses, scores or grades"],
            ["id_approve_icon", "The approval icon"],
            ["id_prelim_exform", "The preliminary Ex-form"],
            ["id_submit_exform", "Submit the Ex form"],
            ["id_submitted_exforms", "List of submitted Ex forms"],
            ]),

        get_dropdown_button("mailbox", "id_intro", "id_btn_mailbox", "Messaging service", [
            ["id_mailbox_read_message", "Read messages"],
            ["id_mailbox_create_message", "Create message"],
            ["id_mailbox_recipients", "Recipients"],
            ["id_mailbox_mailinglist", "Mailing lists"],
            ]),
        "</div>"
        ]

        const el_sidenav =  document.getElementById("id_sidenav");
        console.log("el_sidenav", el_sidenav)
        el_sidenav.innerHTML = sbr_list.join('');
    }

    function GotoParagraph(par_id){
        console.log(" ----- GotoParagraph ----- ")
        console.log("par_id", par_id)
        const el = document.getElementById(par_id);
        console.log("el", el)
        if(el){
           el.scrollIntoView({ block: 'start',  behavior: 'smooth' })
        }
    }

    function get_dropdown_button(page, first_paragraph, btn_id, btn_txt, item_list){
        console.log(" ----- get_dropdown_button ----- ");
        //console.log("btn_txt", btn_txt);
        //console.log("item_list", item_list);
        let html_str = "<button id='" + btn_id + "' class='dropdown-btn' onclick='LoadPage(&#39" + page + "&#39, &#39" + first_paragraph + "&#39 )'>" + btn_txt + "<i class='fa fa-caret-down'></i></button>";
        //let html_str = "<button id='" + btn_id + "' class='dropdown-btn' onclick='LoadPage(&#39" + page + "&#39)'>" + btn_txt + "<i class='fa fa-caret-down'></i></button>";

        if (item_list && item_list.length){
            html_str += "<div id='" + btn_id + "_dropdown' class='dropdown-container'>";
            for (let i = 0, arr; arr = item_list[i]; i++) {
                html_str += "<p class='dropdown_item' onclick='GotoParagraph(&#39" + arr[0] + "&#39)'>" + arr[1] + "</p>";

        console.log("arr[1]", arr[1]);
            };
            html_str += "</div>"
        }

        console.log("html_str", html_str);
        return html_str;
    }

//========= write_paragraph_header  ============= PR2021-08-14
function write_paragraph_header(par_id, dispay_txt){
    return [
         "<div id='" + par_id + "' class='pb-3 visibility_hide'>-</div>",
        "<div class='mfc mt-4'>",
            "<div class='mfl'></div>",
            "<div class='mfr'>",
                "<h4  class='px-2'>", dispay_txt, "</h4>",
            "</div>",
        "</div>"
        ].join("");
};

//========= write_paragraph_body  ============= PR2021-11-02
function write_paragraph_body(icon_class, body_list){
    const icon_class_str = (icon_class) ? " class='" + icon_class + "'" : "";
    return "<div class='mfc'><div class='mfl mt-2'><div" + icon_class_str +
            "></div></div><div class='mfr'>" +
            (body_list).join("") + "</div></div>"
};


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