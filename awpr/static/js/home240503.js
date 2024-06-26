// PR2023-04-12 added


document.addEventListener('DOMContentLoaded', function() {
    "use strict";

// --- get data stored in page
        let el_data = document.getElementById("id_data");
        // PR2023-04-17 debug: Snery error: 'urls' is undefined. Must check why , add 'if (urls){' for now
        if (urls){
            urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
        };

// ---  HEADER BAR ------------------------------------
        const el_hdrbar_examyear = document.getElementById("id_hdrbar_examyear");
        //const examyear_map = null
        //if (el_hdrbar_examyear){
        //    el_hdrbar_examyear.addEventListener("click", function() {
       //         t_MSED_Open(loc, "examyear", examyear_map, setting_dict, permit_dict, MSED_Response)}, false);
       // }
        const el_hdrbar_department = document.getElementById("id_hdrbar_department");
        //if (el_hdrbar_department){
        //    el_hdrbar_department.addEventListener("click", function() {
        //        //t_MSED_Open(loc, "department", department_map, setting_dict, permit_dict, MSED_Response)}, false);
       //         t_MSED_OpenDepLvlFromDicts("department", department_dicts, setting_dict.sel_schoolbase_pk, setting_dict.sel_depbase_pk, MSED_Response)}, false);
        //}
        const el_hdrbar_school = document.getElementById("id_hdrbar_school");
       // if (el_hdrbar_school){
        //    el_hdrbar_school.addEventListener("click",
       //         function() {t_MSSSS_Open(loc, "school", school_rows, false, false, setting_dict, permit_dict, MSSSS_Response)}, false);
       // }

       // const el_hdrbar_allowed_sections = document.getElementById("id_hdrbar_allowed_sections");
       // if (el_hdrbar_allowed_sections){
       //     el_hdrbar_allowed_sections.addEventListener("click", function() {t_MUPS_Open()}, false );
       // };

        //DatalistDownload({page: "page_home"});

//========= DatalistDownload  ===================== PR2023-06-27
    function DatalistDownload(request_item_setting) {
        console.log( "=== DatalistDownload ")
        console.log("request_item_setting: ", request_item_setting)
        const datalist_request = {
                setting: request_item_setting,
                locale: {page: ["page_home"]},
                examyear_rows: {get: true},
                school_rows: {get: true},
                department_rows: {get: true},
            };


        let param = {"download": JSON.stringify (datalist_request)};
        let response = "";
        $.ajax({
            type: "POST",
            url: urls.url_datalist_download,
            data: param,
            dataType: 'json',
            success: function (response) {
                console.log("response")
                console.log(response)

                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                };

                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict
                    b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);
                };

                if ("messages" in response) {
                    b_show_mod_message_dictlist(response.messages);
                }

                if ("examyear_rows" in response) {
                    b_fill_datadicts("examyear", "id", null, response.examyear_rows, examyear_dicts);
                };
                if ("department_rows" in response) {
                    b_fill_datadicts("department", "id", null, response.department_rows, department_dicts);

                };
                if ("school_rows" in response)  {
                     console.log("response.school_rows: ", response.school_rows)
                    b_fill_datadicts("school", "id", null, response.school_rows, school_dicts);
                };

            },
            error: function (xhr, msg) {
                console.log(msg + '\n' + xhr.responseText);
            }
        });
    }  // function DatalistDownload



// +++++++++++++++++ MODAL SELECT EXAMYEAR OR DEPARTMENT ++++++++++++++++++++
// functions are in table.js, except for MSED_Response

//=========  MSED_Response  ================ PR2020-12-18  PR2023-06-27
    function MSED_Response(new_setting) {
        console.log( "===== MSED_Response ========= ");

// ---  upload new selected_pk
        new_setting.page = setting_dict.sel_page;
        //DatalistDownload(new_setting);
    }  // MSED_Response


//=========  MSSSS_Response  ================ PR2021-01-23 PR2021-02-05 PR2021-07-26
    function MSSSS_Response(modalName, tblName, selected_dict, selected_pk) {
        console.log( "===== MSSSS_Response ========= ");
        //console.log( "selected_pk", selected_pk);
        //console.log( "selected_code", selected_code);
        //console.log( "selected_name", selected_name);

// --- reset table
        tblBody_datatable.innerText = null;

// ---  upload new setting and refresh page
        const request_item_setting =  {page: "page_student", sel_schoolbase_pk: selected_pk};
        //DatalistDownload(request_item_setting);
    };  // MSSSS_Response

// +++++++++++++++++ MODAL SIDEBAR SELECT ++++++++++++++++++++++++++++++++++

})  // document.addEventListener('DOMContentLoaded', function()