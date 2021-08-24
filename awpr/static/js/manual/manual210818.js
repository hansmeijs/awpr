// PR2021-06-10 added

let user_lang =  null;

document.addEventListener('DOMContentLoaded', function() {
    "use strict";

    console.log ('===== manual =====')

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    const href_page = get_attr_from_el(el_data, "data-page");
    const data_paragraph = get_attr_from_el(el_data, "data-paragraph");
    const data_lang = get_attr_from_el(el_data, "data-lang");

    //console.log ('href_page', href_page)
    //console.log ('data_paragraph', data_paragraph)
    //console.log ('data_lang', data_lang)

    let html_upload_list = [];
    user_lang = (data_lang) ? data_lang : null;

// - Loop through all dropdown buttons to toggle between hiding and showing its dropdown content - This allows the user to have multiple dropdowns without any conflict */
// --- highlight SBR btn of selected page,
    const el_sidenav = document.getElementById("id_sidenav");
    const dropdown_els = el_sidenav.getElementsByClassName("dropdown-btn");

    for (let i = 0, el; el = dropdown_els[i]; i++) {
        const btn_page = (el.id) ? el.id.slice(7) : null; // "id_btn_intro"
        //console.log (".... btn_page", btn_page ," href_page", href_page)

        if (btn_page === href_page) {
            SelectBtn(el);
        };

        el.addEventListener("click", function() {HandleDropdownClicked(el)});

    }

    LoadPage(href_page);

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


//========= LoadPage  ============= PR2021-07-30
    function LoadPage(page){
        //console.log( "===== LoadPage  ========= ");
        //console.log( "page", page);
        //console.log( "user_lang", user_lang);
        //console.log( "man_studsubj", man_studsubj);

        const is_en = (user_lang === "en");
        const html_dict = (page === "intro") ? man_home :
                        (page === "user") ? man_user :
                        (page === "upload") ? man_upload :
                        (page === "studsubj") ? man_studsubj :
                        (page === "approve") ? man_approve : null;
        //console.log( "html_dict", html_dict);

        const html_list = (html_dict) ? (user_lang === 'en' && html_dict.en) ?  html_dict.en :  html_dict.nl : null;
        //console.log( "html_list", html_list);

        const html_str = (html_list && html_list.length) ? html_list.join('') : (is_en) ? "<h4 class='p-5'> This page is not available yet.</h4>" : "<h4 class='p-5'> Deze pagina is nog niet beschikbaar.</h4>";

        document.getElementById("id_content").innerHTML = html_str;

        FillSideNav(is_en);

        SelectBtnAndDeselctOthers("id_btn_" + page )

    };  // LoadPage

//========= SelectBtn  ============= PR2021-07-30
    function SelectBtn(el){
        //console.log( "===== SelectBtn  ========= ");
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
        //console.log( "===== SelectBtnAndDeselctOthers  ========= ");

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

//========= SelectBtnAndDeselctOthers  ============= PR2021-08-23
    function FillSideNav(is_en){
        const sbr_list = (!is_en) ? [
            get_dropdown_button("intro", "id_btn_intro", "Welkom bij AWP-online"),
/*
            get_dropdown_button("user", "id_btn_users", "Gebruikers"),
            get_dropdown_button("upload", "id_btn_upload", "Gegevens uploaden"),
            "<div id='id_btn_upload_dropdownXX' class='dropdown-container display_hide'>",
            "<a href='#'>{% trans 'Introduction' %}</a>",
            "</div>",
*/
            get_dropdown_button("studsubj", "id_btn_studsubj", "Vakken van kandidaten"),
            "<div id='id_btn_studsubj_dropdownXX' class='dropdown-container display_hide'>",
            "<a href='#'>{% trans 'Introduction' %}</a>",
            "</div>",

            get_dropdown_button("approve", "id_btn_approve", "Goedkeuren en indienen van Ex-formulieren", [
                ["id_digital_signature", "Digitale handtekening"],
                ["id_digital_signature", "Vakken goedkeuren"],
                ["id_digital_signature", "Ex-formulier indienen"],
                ["id_digital_signature", "Lijst met ingediende Ex-formulieren"],

                ]),
            "</div>"
            ] : [
            "--"
            ]

        console.log("sbr_list", sbr_list)
    const el_sidenav = document.getElementById("id_sidenav");
           el_sidenav.innerHTML = sbr_list.join('');

    }

    function GotoParagraph(h_ref){
        console.log(" ----- GotoParagraph ----- ")
        console.log("h_ref", h_ref)
    }

/*
        if(!hover_class){hover_class = "tr_hover"};
        if(el){
            el.addEventListener("mouseenter", function(){
                if(default_class) {el.classList.remove(default_class)}
                el.classList.add(hover_class)
            });
            el.addEventListener("mouseleave", function(){
                if(default_class) {el.classList.add(default_class)}
                el.classList.remove(hover_class)
            });
        }
        el.classList.add("pointer_show")
*/
    function get_dropdown_button(page, btn_id, btn_txt, item_list){
        console.log(" ----- get_dropdown_button ----- ");
        console.log("btn_txt", btn_txt);
        console.log("item_list", item_list);
        let html_str = "<button id='" + btn_id + "' class='dropdown-btn' onclick='LoadPage(&#39" + page + "&#39)'>" + btn_txt + "<i class='fa fa-caret-down'></i></button>";
       /*
        if (item_list && item_list.length){
            html_str += "<div id='" + btn_id + "_dropdown' class='dropdown-container'>";
            for (let i = 0, arr; arr = item_list[i]; i++) {
                html_str += "<p class='dropdown_item' onclick='GotoParagraph(&#39" + arr[0] + "&#39)'>" + arr[1] + "</p>";
            };
            html_str += "</div>"
        }
       */
        return html_str;
    }