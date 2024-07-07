// PR2023-04-12 added

document.addEventListener('DOMContentLoaded', function() {
    "use strict";

// ---  check if user has permit to view this page. If not: el_loader does not exist PR2020-10-02
    const el_loader = document.getElementById("id_loader");
    const may_view_page = (!!el_loader)
    console.log("may_view_page", may_view_page)

    //PR2024-06=25 TODO: change to examyear_rows, department_rows
    let examyear_map = new Map();
    let department_map = new Map();

// --- get data stored in page
        let el_data = document.getElementById("id_data");
        // PR2023-04-17 debug: Snery error: 'urls' is undefined. Must check why , add 'if (urls){' for now
        if (urls){
            urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
            urls.url_usersetting_upload = get_attr_from_el(el_data, "data-url_usersetting_upload");

        };

// ---  HEADER BAR ------------------------------------
        const el_hdrbar_examyear = document.getElementById("id_hdrbar_examyear");
        if (el_hdrbar_examyear){
            el_hdrbar_examyear.addEventListener("click", function() {
                t_MSED_Open(loc, "examyear", examyear_map, setting_dict, permit_dict, MSED_Response)}, false );
        };
        const el_hdrbar_department = document.getElementById("id_hdrbar_department");
        if (el_hdrbar_department){
            el_hdrbar_department.addEventListener("click", function() {
                t_MSED_Open(loc, "department", department_map, setting_dict, permit_dict, MSED_Response)}, false );
        };
        const el_hdrbar_school = document.getElementById("id_hdrbar_school");
        if (el_hdrbar_school){
            el_hdrbar_school.addEventListener("click",
                function() { t_MSSSS_Open_NEW("hdr", "school", school_rows, MSSSS_school_response)}, false );
        };

       // const el_hdrbar_allowed_sections = document.getElementById("id_hdrbar_allowed_sections");
       // if (el_hdrbar_allowed_sections){
       //     el_hdrbar_allowed_sections.addEventListener("click", function() {t_MUPS_Open()}, false );
       // };
        if(may_view_page){
            DatalistDownload({page: "page_home"}, true);
        };
//========= DatalistDownload  ===================== PR2023-06-27 PR2024-06-25
    function DatalistDownload(request_item_setting, keep_loader_hidden) {
        console.log( "=== DatalistDownload ")
        console.log("    request_item_setting: ", request_item_setting)

// ---  Get today's date and time - for elapsed time
        let startime = new Date().getTime();

// ---  show loader
        if(!keep_loader_hidden){el_loader.classList.remove(cls_visible_hide)}

        const datalist_request = {
            setting: request_item_setting,
            locale: {page: ["page_home"]},

            examyear_rows: {get: true},
            school_rows: {get: true},
            department_rows: {get: true},
        };

        console.log("    datalist_request: ", datalist_request)

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

        // hide loader
                el_loader.classList.add(cls_visible_hide);

                let isloaded_loc = false, isloaded_settings = false, isloaded_permits = false;
                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                    isloaded_loc = true;
                };

                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict;
        console.log("setting_dict", setting_dict);
                    //selected_btn = setting_dict.sel_btn;
                    isloaded_settings = true;
                    h_UpdateHeaderBar(el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);
                };
                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    isloaded_permits = true;
                    // get_permits must come before CreateSubmenu and FiLLTbl
                    b_get_permits_from_permitlist(permit_dict);
                };
                if ("messages" in response) {
                    b_show_mod_message_dictlist(response.messages);
                }
                if ("examyear_rows" in response) {
                    examyear_rows = response.examyear_rows;
                    b_fill_datamap(examyear_map, response.examyear_rows);
                    //b_fill_datadicts("examyear", "id", null, response.examyear_rows, examyear_dicts);
                };
                if ("department_rows" in response) {
                    department_rows = response.department_rows;
                    b_fill_datamap(department_map, response.department_rows);
                   // b_fill_datadicts("department", "id", null, response.department_rows, department_dicts);
                };
                if ("school_rows" in response)  {
                    school_rows = response.school_rows;
                    b_fill_datadicts("school", "id", null, response.school_rows, school_dicts);
                };

                if(isloaded_settings || isloaded_permits){
                    h_UpdateHeaderBar(el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);
                };
            },
            error: function (xhr, msg) {
                console.log(msg + '\n' + xhr.responseText);
            }
        });
    }  // function DatalistDownload

// +++++++++++++++++ MODAL SELECT EXAMYEAR OR DEPARTMENT ++++++++++++++++++++
// functions are in table.js, except for MSED_Response

//=========  MSED_Response  ================ PR2020-12-18  PR2023-06-27  PR2024-06-25
    function MSED_Response(new_setting) {
        console.log( "===== MSED_Response ========= ");

// ---  upload new selected_pk
        new_setting.page = setting_dict.sel_page;
        DatalistDownload(new_setting);
    }  // MSED_Response

//=========  MSSSS_school_response  ================ PR2023-03-29 PR2024-06-25
    function MSSSS_school_response(modalName, tblName, selected_dict, sel_schoolbase_pk) {
        console.log( "===== MSSSS_school_response ========= ");
        console.log( "   modalName", modalName);
        console.log( "tblName", tblName);
        console.log( "sel_schoolbase_pk", sel_schoolbase_pk, typeof sel_schoolbase_pk);
        console.log( "selected_dict", selected_dict);
        // arguments of MSSSS_response are set in t_MSSSS_Save_NEW

// reset text dep and school in headerbar
        el_hdrbar_department.innerText = null;
        el_hdrbar_school.innerText = null;

// reset cluster and student

// ---  upload new setting and refresh page
        const request_item_setting = {
            sel_schoolbase_pk: sel_schoolbase_pk,
            sel_cluster_pk: null,
            sel_student_pk: null
        };
        console.log( "   request_item_setting", request_item_setting);
        DatalistDownload(request_item_setting);

    };  // MSSSS_school_response
})  // document.addEventListener('DOMContentLoaded', function()