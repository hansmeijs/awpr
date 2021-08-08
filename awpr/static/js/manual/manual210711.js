// PR2021-06-10 added
document.addEventListener('DOMContentLoaded', function() {
    "use strict";

    console.log ('===== manual =====')

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    const href_page = get_attr_from_el(el_data, "data-page");
    const data_paragraph = get_attr_from_el(el_data, "data-paragraph");
    const data_lang = get_attr_from_el(el_data, "data-lang");

    console.log ('href_page', href_page)
    console.log ('data_paragraph', data_paragraph)
    console.log ('data_lang', data_lang)

    let html_upload_list = [];
    let user_lang = (data_lang) ? data_lang : null;

// - Loop through all dropdown buttons to toggle between hiding and showing its dropdown content - This allows the user to have multiple dropdowns without any conflict */
    const el_sidenav = document.getElementById("id_sidenav");
    const dropdown_els = el_sidenav.getElementsByClassName("dropdown-btn");

    for (let i = 0, el; el = dropdown_els[i]; i++) {
        const btn_page = (el.id) ? el.id.slice(7) : null; // "id_btn_intro"
        console.log (".... btn_page", btn_page)

        if (btn_page === href_page) {
            SelectBtn(el);
        };

        el.addEventListener("click", function() {HandleDropdownClicked(el)});

    }

    LoadPage(href_page);

//========= HandleDropdownClicked  ============= PR2021-07-30
    function HandleDropdownClicked(el){
        console.log( "===== HandleDropdownClicked  ========= ");
        DeselectAll();
        SelectBtn(el);

        const el_id = el.id  // "id_btn_intro"
        const btn_page = (el_id) ? el_id.slice(7) : null;
        console.log (".... btn_page", btn_page)
        LoadPage(btn_page);
      };  // HandleDropdownClicked


//========= LoadPage  ============= PR2021-07-30
    function LoadPage(page,){
        console.log( "===== LoadPage  ========= ");
        console.log( "page", page);
        console.log( "user_lang", user_lang);

        const html_dict = (page === "home") ? man_home :
                        (page === "upload") ? man_upload :
                        (page === "approve") ? man_approve : null;
        console.log( "html_dict", html_dict);
        const html_list= (user_lang === 'en' && html_dict.en) ?  html_dict.en :  html_dict.nl;
        console.log( "html_list", html_list);
        const html_str = (html_list && html_list.length) ? html_list.join('') : "<h4 class='p-5'> Deze pagina is nog niet beschikbaar.</h4>";

        document.getElementById("id_content").innerHTML = html_str;
    };  // LoadPage

//========= SelectBtn  ============= PR2021-07-30
    function SelectBtn(el){
        console.log( "===== SelectBtn  ========= ");
        el.classList.add("active");
        const el_dropdown = document.getElementById(el.id + "_dropdown")
        if(el_dropdown) {el_dropdown.style.display = "block"};
    } // DeselectAll

//========= DeselectAll  ============= PR2021-07-30
    function DeselectAll(){
        console.log( "===== DeselectAll  ========= ");
        for (let i = 0, el; el = dropdown_els[i]; i++) {
            el.classList.remove("active");
            const el_dropdown = document.getElementById(el.id + "_dropdown")
            if(el_dropdown) {el_dropdown.style.display = "none"};
        }
    } // DeselectAll
})  // document.addEventListener('DOMContentLoaded', function()