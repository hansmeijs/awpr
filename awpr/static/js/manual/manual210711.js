// PR2021-06-10 added
document.addEventListener('DOMContentLoaded', function() {
    "use strict";

    console.log ('===== manual =====')

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    const data_page = get_attr_from_el(el_data, "data-page");
    const data_paragraph = get_attr_from_el(el_data, "data-paragraph");

    console.log ('data_page', data_page)
    console.log ('data_paragraph', data_paragraph)

    let html_upload_list = [];

// - Loop through all dropdown buttons to toggle between hiding and showing its dropdown content - This allows the user to have multiple dropdowns without any conflict */
    const dropdown = document.getElementsByClassName("dropdown-btn");

    for (let i = 0, el; el = dropdown[i]; i++) {
        const page = get_attr_from_el(el, "data-page");
        if (page === data_page) {el.classList.add("active")};
        el.addEventListener("click", function() {HandleDropdownClicked(el);});
    }

/*
    for (let i = 0; i < dropdown.length; i++) {
      dropdown[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var dropdownContent = this.nextElementSibling;
        if (dropdownContent.style.display === "block") {
          dropdownContent.style.display = "none";
        } else {
          dropdownContent.style.display = "block";
        }
      });
    }
*/

    let html_str = "", html_list = [];
    switch (data_page){
    case "home":
        html_list = man_home_list;
        break;
    case "upload":
        html_list = man_upload_list;
        break;
    case "sct":
        html_str = "<h1> CONTENT TEST </h1>"
        break;
    };
    html_str = html_list.join('');

    console.log ('html_list', html_list)


    document.getElementById("id_content").innerHTML = html_str;

    function HandleDropdownClicked(el){
        el.classList.toggle("active");
        const dropdownContent = el.nextElementSibling;
        if (dropdownContent.style.display === "block") {
          dropdownContent.style.display = "none";
        } else {
          dropdownContent.style.display = "block";
        }
      };

})  // document.addEventListener('DOMContentLoaded', function()