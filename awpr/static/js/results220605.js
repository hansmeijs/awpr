// PR2020-09-29 added

// PR2021-07-23  declare variables outside function to make them global variables

// selected_btn is also used in t_MCOL_Open
let selected_btn = "btn_result";

let setting_dict = {};
let permit_dict = {};
let loc = {};
let urls = {};

let selected = {student_pk: null, student_dict: {}};

let student_rows = [];
let results_per_school_rows = [];
let pres_secr_dict = {};
let school_rows = [];

const field_settings = {};

document.addEventListener('DOMContentLoaded', function() {
    "use strict";

// ---  check if user has permit to view this page. If not: el_loader does not exist PR2020-10-02
    const el_loader = document.getElementById("id_loader");
    const el_hdr_left = document.getElementById("id_header_left");
    const may_view_page = (!!el_loader);

    const cls_hide = "display_hide";
    const cls_hover = "tr_hover";
    const cls_visible_hide = "visibility_hide";
    const cls_selected = "tsa_tr_selected";

// ---  id of selected customer and selected order
    // declared as global: let selected_btn = "btn_result";
    //let setting_dict = {};
    //let permit_dict = {};

    let mod_dict = {};
    let mod_MSTUD_dict = {};

    let mod_MSTUDSUBJ_dict = {}; // stores general info of selected candidate in MSTUDSUBJ PR2020-11-21
    //let mod_studsubj_dict = {};  // stores studsubj of selected candidate in MSTUDSUBJ
    //let mod_schemeitem_dict = {};   // stores available studsubj for selected candidate in MSTUDSUBJ
    let mod_studsubj_map = new Map();  // stores studsubj of selected candidate in MSTUDSUBJ
    let mod_schemeitem_map = new Map();

    let examyear_map = new Map();
    let school_map = new Map();
    // PR2020-12-26 These variable defintions are moved to import.js, so they can also be used in that file
    let department_map = new Map();
    let level_map = new Map();
    let sector_map = new Map();
    //let selected = {student_pk: null,
    //                student_dict: {}};

    // PR2021-07-23 moved outside this function, to make it available in import.js
    // let student_rows = [];
    // let loc = {};

    let subject_map = new Map();
    let studentsubject_map = new Map()
    let scheme_map = new Map()
    let schemeitem_map = new Map()

    let filter_dict = {};

// --- get data stored in page
    const el_data = document.getElementById("id_data");
    urls.url_user_modmsg_hide = get_attr_from_el(el_data, "data-url_user_modmsg_hide");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    urls.url_usersetting_upload = get_attr_from_el(el_data, "data-url_usersetting_upload");
    urls.url_student_upload = get_attr_from_el(el_data, "data-url_student_upload");
    urls.url_studsubj_validate_scheme = get_attr_from_el(el_data, "data-url_studsubj_validate_scheme");
    urls.url_download_gradelist = get_attr_from_el(el_data, "data-url_download_gradelist");
    urls.url_calc_results = get_attr_from_el(el_data, "data-url_calc_results");
    urls.url_get_auth = get_attr_from_el(el_data, "data-url_get_auth");
    urls.url_get_auth = get_attr_from_el(el_data, "data-url_get_auth");
    urls.url_result_download_ex5 = get_attr_from_el(el_data, "data-url_result_download_ex5");
    urls.url_result_download_overview = get_attr_from_el(el_data, "data-url_result_download_overview");

    // columns_hidden and columns_tobe_hidden are declared in tables.js, they are also used in t_MCOL_Open and t_MCOL_Save
    // columns_tobe_hidden contains the fields and captions that can be hidden
    // key 'all' contains fields that will be hidden in all buttons
    // key with btn name contains fields that will be hidden in this selected_btn
    // either 'all' or selected_btn are used in a page

    columns_tobe_hidden.btn_result = {
        idnumber: "ID_number", lvl_abbrev: "Leerweg", sct_abbrev: "Sector", classname: "Class",
        examnumber: "Examnumber", regnumber: "Regnumber", result_status: "Result", withdrawn: "Withdrawn"
    };

    columns_tobe_hidden.btn_overview = {
        idnumber: "ID_number", lvl_abbrev: "Leerweg", sct_abbrev: "Sector", classname: "Class",
        examnumber: "Examnumber", regnumber: "Regnumber", result_status: "Result", withdrawn: "Withdrawn"
    };
// --- get field_settings
    // declared as global: let field_settings = {};
    field_settings.student = {
        field_caption: ["", "Examnumber_twolines", "Name", "Leerweg", "Sector", "Class",  "Result", "Withdrawn_2lines"],
        field_names: ["select", "examnumber", "fullname", "lvl_abbrev", "sct_abbrev", "classname", "result_status", "withdrawn"],
        filter_tags: ["select", "text", "text", "text","text", "text", "text", "toggle"],
        field_width:  ["020", "120", "390", "090", "090", "090",  "120","090"],
        field_align: ["c", "l", "l", "l", "l", "l",  "l","c"]
        };

    field_settings.overview = {
        field_caption: ["", "", "", "", "",
                        "M", "V", "T",
                        "M", "V", "T",
                        "M", "V", "T",
                        "M", "V", "T",
                        "M", "V", "T",
                        "M", "V", "T"],
        field_names: ["select", "db_code", "lvl_code", "sb_code", "sch_name",
                        "m", "v", "t",
                        "m_pass", "v_pass", "t_pass",
                        "m_fail", "v_fail", "t_fail",
                        "m_reex", "v_reex", "t_reex",
                        "m_wdr", "v_wdr", "t_wdr",
                        "m_nores", "v_nores", "t_nores"],
        filter_tags: ["select", "text", "text", "text", "text",
                        "text", "text", "text",
                        "text", "text", "text",
                        "text", "text", "text",
                        "text", "text", "text",
                        "text", "text", "text",
                        "text", "text", "text"],
        field_width:  ["020", "075", "075", "075", "180",
                        "032", "032", "032",
                        "032", "032", "032",
                        "032", "032", "032",
                        "032", "032", "032",
                        "032", "032", "032",
                        "032", "032", "032"],
        field_align: ["c", "c", "c", "c", "l",
                        "r", "r", "r",
                        "c", "c", "c",
                         "c", "c", "c",
                         "c", "c", "c",
                         "c", "c","c",
                         "c", "c", "c"]
    };
    field_settings.group_header = {
        field_caption: ["", "Department", "Level", "Code", "School",
                        "Total_candidates", "", "", "Passed", "", "", "Failed", "", "", "Re_examination", "", "", "Withdrawn_2lines", "", "", "No_result", "", ""],
        field_names: ["select", "db_code", "lvl_code", "sb_code", "sch_name",
                        "count", "count", "count", "pass", "pass", "pass", "fail", "fail", "fail",
                        "reex", "reex", "reex", "wdr", "wdr", "wdr", "nores", "nores", "nores"],
        filter_tags: ["select", "text", "text", "text", "text","text", "text", "text","text", "text", "text", "text", "text"],
        field_width:  ["020", "075", "075", "075", "180","032", "032", "032", "032", "032", "032", "032","032"],
        field_align: ["c", "c", "c", "c", "l", "c", "c", "c", "c", "c", "c", "c","c"]
    };

    const tblHead_datatable = document.getElementById("id_tblHead_datatable");
    const tblBody_datatable = document.getElementById("id_tblBody_datatable");

// === EVENT HANDLERS ===
// === reset filter when ckicked on Escape button ===
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") { ResetFilterRows()}
        });

 // freeze table header PR2021-08-03
        // from https://stackoverflow.com/questions/673153/html-table-with-fixed-headers
        // borders dont translate. fixed with https://stackoverflow.com/questions/45692744/td-border-disappears-when-applying-transform-translate
        // no luck, border still not showing
        const el_tbl_container = document.getElementById("id_tbl_container");
        if(el_tbl_container){
            el_tbl_container.addEventListener("scroll",function(){
               const scroll = this.scrollTop - 8
               const translate = "translate(0," + scroll + "px)";
               this.querySelector("thead").style.transform = translate;
            });
        };

// --- buttons in btn_container
        const el_btn_container = document.getElementById("id_btn_container")
        if (el_btn_container){
            const btns = el_btn_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                const data_btn = get_attr_from_el(btn,"data-btn")
                btn.addEventListener("click", function() {HandleBtnSelect(data_btn)}, false )
            };
        };

// ---  HEADER BAR ------------------------------------
        const el_hdrbar_examyear = document.getElementById("id_hdrbar_examyear");
        const el_hdrbar_school = document.getElementById("id_hdrbar_school");
        const el_hdrbar_department = document.getElementById("id_hdrbar_department");
        if (el_hdrbar_examyear){
            el_hdrbar_examyear.addEventListener("click", function() {
                t_MSED_Open(loc, "examyear", examyear_map, setting_dict, permit_dict, MSED_Response)}, false );
        };
        if (el_hdrbar_department){
            el_hdrbar_department.addEventListener("click", function() {
                t_MSED_Open(loc, "department", department_map, setting_dict, permit_dict, MSED_Response)}, false );
        };
        if (el_hdrbar_school){
            el_hdrbar_school.addEventListener("click",
                function() {t_MSSSS_Open(loc, "school", school_rows, false, setting_dict, permit_dict, MSSSS_Response)}, false );
        };

// ---  SIDEBAR ------------------------------------
        const el_SBR_select_level = document.getElementById("id_SBR_select_level");
        if(el_SBR_select_level){
            el_SBR_select_level.addEventListener("change",
                function() {t_SBR_select_and_update_level_sector("lvlbase", el_SBR_select_level, Response_from_SBR_select_level_sector)}, false);
        };
        const el_SBR_select_sector = document.getElementById("id_SBR_select_sector");
        if(el_SBR_select_sector){
            el_SBR_select_sector.addEventListener("change",
                function() {t_SBR_select_and_update_level_sector("sctbase", el_SBR_select_sector, Response_from_SBR_select_level_sector)}, false);
        };
        //const el_SBR_select_class = document.getElementById("id_SBR_select_class");
        //if(el_SBR_select_class){
        //    el_SBR_select_class.addEventListener("click", function() {t_MSSSS_Open(loc, "class", classname_rows, true, setting_dict, permit_dict, MSSSS_Response)}, false)};
        const el_SBR_select_student = document.getElementById("id_SBR_select_student");
        if(el_SBR_select_student){
            el_SBR_select_student.addEventListener("click", function() {t_MSSSS_Open(loc, "student", student_rows, true, setting_dict, permit_dict, MSSSS_Response)}, false)};
        const el_SBR_select_showall = document.getElementById("id_SBR_select_showall");
        if(el_SBR_select_showall){
            el_SBR_select_showall.addEventListener("click", function() {SBR_show_all(FillTblRows)}, false);
            add_hover(el_SBR_select_showall);
        };
        const el_SBR_item_count = document.getElementById("id_SBR_item_count")

// ---  MODAL SIDEBAR FILTER ------------------------------------
        const el_SBR_filter = document.getElementById("id_SBR_filter")
        if(el_SBR_filter){
            el_SBR_filter.addEventListener("keyup", function() {MSTUD_InputKeyup(el_SBR_filter)}, false );
        };

// ---  MODAL SELECT COLUMNS ------------------------------------
        const el_MCOL_btn_save = document.getElementById("id_MCOL_btn_save")
        if(el_MCOL_btn_save){
            el_MCOL_btn_save.addEventListener("click", function() {
                t_MCOL_Save(urls.url_usersetting_upload, HandleBtnSelect)}, false )
        };;

// ---  MOD CONFIRM ------------------------------------
        const el_confirm_header = document.getElementById("id_modconfirm_header");
        const el_confirm_loader = document.getElementById("id_modconfirm_loader");
        const el_confirm_msg_container = document.getElementById("id_modconfirm_msg_container")

        const el_confirm_btn_cancel = document.getElementById("id_modconfirm_btn_cancel");
        const el_confirm_btn_save = document.getElementById("id_modconfirm_btn_save");
        if(el_confirm_btn_save){ el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()}) };

// ---  MOD MESSAGE ------------------------------------
        const el_mod_message_btn_hide = document.getElementById("id_mod_message_btn_hide");
        if(el_mod_message_btn_hide){
            el_mod_message_btn_hide.addEventListener("click", function() {ModMessageHide()});
        };

// ---  MOD GRADELIST ------------------------------------
        const el_MGL_header = document.getElementById("id_MGL_header");
        const el_MGL_loader = document.getElementById("id_MGL_loader");

        const el_MGL_info_container = document.getElementById("id_MGL_info_container")

        const el_MGL_select_pres = document.getElementById("id_MGL_select_pres")
        const el_MGL_select_secr = document.getElementById("id_MGL_select_secr")
        const el_MGL_printdate = document.getElementById("id_MGL_printdate")
        const el_MGL_print_reex_container = document.getElementById("id_MGL_print_reex_container")
        const el_MGL_print_reex = document.getElementById("id_MGL_print_reex")

        const el_MGL_link = document.getElementById("id_MGL_link");

        const el_MGL_btn_cancel = document.getElementById("id_MGL_btn_cancel");
        const el_MGL_btn_save = document.getElementById("id_MGL_btn_save");
        if(el_MGL_btn_save){ el_MGL_btn_save.addEventListener("click", function() {MGL_Save()}) };

// ---  set selected menu button active
        const btn_clicked = document.getElementById("id_plg_page_student")

        //console.log("btn_clicked: ", btn_clicked)
        SetMenubuttonActive(document.getElementById("id_plg_page_student"));

    if(may_view_page){
        // period also returns emplhour_list
        const datalist_request = {
                setting: {page: "page_result"},
                schoolsetting: {setting_key: "page_result"},
                locale: {page: ["page_result", "page_student"]},
                examyear_rows: {get: true},
                school_rows: {get: true},
                department_rows: {get: true},
                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},
                student_rows: {cur_dep_only: true},
                results_per_school_rows: {get: true},
                pres_secr_rows: {get: true}
            };

        DatalistDownload(datalist_request);
    };
//  #############################################################################################################

//========= DatalistDownload  ===================== PR2020-07-31 PR2021-11-18
    function DatalistDownload(datalist_request, skip_messages) {
        console.log( "=== DatalistDownload ")
        console.log("request: ", datalist_request)

// ---  Get today's date and time - for elapsed time
        let startime = new Date().getTime();

// ---  show loader
        el_loader.classList.remove(cls_visible_hide)
        el_hdr_left.classList.add(cls_hide)

        let param = {"download": JSON.stringify (datalist_request)};
        let response = "";
        $.ajax({
            type: "POST",
            url: urls.url_datalist_download,
            data: param,
            dataType: 'json',
            success: function (response) {
                console.log("response - elapsed time:", (new Date().getTime() - startime) / 1000 )
                console.log(response)

// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                el_hdr_left.classList.remove(cls_hide)

                let must_update_headerbar = false;
                let check_status = false;
                let isloaded_loc = false, isloaded_settings = false, isloaded_permits = false;

                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                    isloaded_loc = true;
                };

                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict
                    selected_btn = (setting_dict.sel_btn)
                    isloaded_settings = true;

            // ---  fill cols_hidden
                    if("cols_hidden" in setting_dict){
                        //  setting_dict.cols_hidden was dict with key 'all' or se_btn, changed to array PR2021-12-14
                        //  skip when setting_dict.cols_hidden is not an array,
                        // will be changed into an array when saving with t_MCOL_Save
                        if (Array.isArray(setting_dict.cols_hidden)) {
                             b_copy_array_noduplicates(setting_dict.cols_hidden, mod_MCOL_dict.cols_hidden);
                        };
                    };
                    must_update_headerbar = true;
                };

                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    // get_permits must come before CreateSubmenu and FiLLTbl
                    b_get_permits_from_permitlist(permit_dict);
                    isloaded_permits = true;
                    must_update_headerbar = true;
                }
                if ("schoolsetting_dict" in response) {

                };
                // both 'loc' and 'setting_dict' are needed for CreateSubmenu
                if (isloaded_loc && isloaded_settings) {CreateSubmenu()};
                if(isloaded_settings || isloaded_permits){
                    b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);
                };
                if (!skip_messages && "messages" in response) {
                    b_show_mod_message_dictlist(response.messages);
                }

                if ("examyear_rows" in response) { b_fill_datamap(examyear_map, response.examyear_rows)};
                if ("school_rows" in response)  {
                    school_rows =  response.school_rows;
                    b_fill_datamap(school_map, response.school_rows)};
                if ("department_rows" in response) {
                    b_fill_datamap(department_map, response.department_rows)
                    };

                if ("level_rows" in response)  {
                    b_fill_datamap(level_map, response.level_rows);
                    t_SBR_filloptions_level_sector("level", response.level_rows)

                };
                if ("sector_rows" in response) {
                    b_fill_datamap(sector_map, response.sector_rows);
                    t_SBR_filloptions_level_sector("sector", response.sector_rows);
                };
                if ("student_rows" in response) {
                    student_rows = response.student_rows;
                };
                if ("results_per_school_rows" in response) {
                    results_per_school_rows = response.results_per_school_rows;
                };
                if ("pres_secr_rows" in response) {
                    pres_secr_dict = response.pres_secr_rows;
                };
                HandleBtnSelect(selected_btn, true)  // true = skip_upload

            },
            error: function (xhr, msg) {
// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                console.log(msg + '\n' + xhr.responseText);
            }
        });
    }  // function DatalistDownload

//=========  CreateSubmenu  ===  PR2020-07-31
    function CreateSubmenu() {
        console.log("===  CreateSubmenu == ");
        //console.log("loc.Add_subject ", loc.Add_subject);
        //console.log("loc ", loc);

        const el_submenu = document.getElementById("id_submenu")
        //if(permit_dict.permit_crud){
        //    AddSubmenuButton(el_submenu, loc.Add_candidate, function() {MSTUD_Open()});
        //    AddSubmenuButton(el_submenu, loc.Delete_candidate, function() {ModConfirmOpen("delete")});
        //};
        if(permit_dict.requsr_role_system){
            AddSubmenuButton(el_submenu, loc.Validate_candidate_schemes, function() {ModConfirmOpen("validate_scheme")});
            AddSubmenuButton(el_submenu, loc.Correct_candidate_schemes, function() {ModConfirmOpen("correct_scheme")});
        };
        AddSubmenuButton(el_submenu, loc.Preliminary_gradelist, function() {MGL_Open("prelim")}, ["tab_show", "tab_btn_result"]);

        if(permit_dict.permit_crud){
            AddSubmenuButton(el_submenu, loc.Calc_result, function() {Calc_result("prelim")}, ["tab_show", "tab_btn_result"]);
        };

        AddSubmenuButton(el_submenu, loc.Preliminary_ex5_form, function() {ModConfirmOpen("prelim_ex5")}, ["tab_show", "tab_btn_result"]);
        AddSubmenuButton(el_submenu, loc.Download_overview, function() {ModConfirmOpen("overview")}, ["tab_show", "tab_btn_overview"]);
        AddSubmenuButton(el_submenu, loc.Hide_columns, function() {t_MCOL_Open("page_result")}, [], "id_submenu_columns");
        el_submenu.classList.remove(cls_hide);

    };//function CreateSubmenu

//###########################################################################
//=========  HandleBtnSelect  ================ PR2020-09-19 PR2020-11-14 PR2022-06-04
    function HandleBtnSelect(data_btn, skip_upload) {
        //console.log( "===== HandleBtnSelect ========= ", data_btn);

        // check if data_btn exists, gave error because old btn name was still in saved setting PR2021-09-07 debug
        if (!data_btn) {data_btn = selected_btn};
        if (data_btn && ["btn_result", "btn_overview"].includes(data_btn)) {
            selected_btn = data_btn;
        } else {
            selected_btn = "btn_result";
        };

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_result: {sel_btn: selected_btn}};
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);
        };

// ---  highlight selected button
        b_highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  show only the elements that are used in this tab
        b_show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

// ---  fill sidebar selecttable students
        //SBR_FillSelectTable();

// ---  fill datatable
        FillTblRows();

    }  // HandleBtnSelect

//=========  HandleTblRowClicked  ================ PR2020-08-03
    function HandleTblRowClicked(tr_clicked) {
        //console.log("=== HandleTblRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

// ---  get selected.student_dict
        selected.student_pk = get_attr_from_el_int(tr_clicked, "data-pk");
        selected.student_dict = b_get_datadict_by_integer_from_datarows(student_rows, "id", selected.student_pk);
        //console.log( "selected.student_pk: ", selected.student_pk);
        //console.log( "selected.student_dict: ", selected.student_dict);

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        //DeselectHighlightedRows(tr_clicked, cls_selected);
       //tr_clicked.classList.add(cls_selected)


// ---  deselect all highlighted rows, select clicked row
       // t_td_selected_clear(tr_clicked.parentNode);
       // t_td_selected_set(tr_clicked);
        t_td_selected_toggle(tr_clicked);

    }  // HandleTblRowClicked

//========= FillTblRows  ============== PR2021-06-16  PR2021-12-14
    function FillTblRows() {
        console.log( "===== FillTblRows  === ");
        //console.log( "setting_dict", setting_dict);

        const tblName = (selected_btn === "btn_overview") ? "overview" : "student";
        const field_setting = field_settings[tblName];

        const data_rows =  (selected_btn === "btn_overview") ? results_per_school_rows : student_rows;

// ---  get list of hidden columns
        // copy col_hidden from mod_MCOL_dict.cols_hidden
        const col_hidden = [];
        b_copy_array_noduplicates(mod_MCOL_dict.cols_hidden, col_hidden)
        // hide level when not level_req
        if(!setting_dict.sel_dep_level_req){col_hidden.push("lvl_abbrev")};

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

// --- create table header
        CreateTblHeader(field_setting, col_hidden);

// --- loop through data_rows
        if(data_rows && data_rows.length){
            for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {

        // --- set SBR_filter
        // Note: filter of filterrow is done by Filter_TableRows
                let show_row = true;
                if (show_row && setting_dict.sel_lvlbase_pk){
                    show_row = (setting_dict.sel_lvlbase_pk === data_dict.lvlbase_id)
                }
                if (show_row && setting_dict.sel_sctbase_pk){
                    show_row = (setting_dict.sel_sctbase_pk === data_dict.sctbase_id)
                }
                if(show_row){
                    CreateTblRow(tblName, field_setting, data_dict, col_hidden);
                };
            };
        };
// --- filter tblRows
        Filter_TableRows();
    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-07-31 PR2021-06-15 PR2021-08-02 PR2021-12-14
    function CreateTblHeader(field_setting, col_hidden) {
        //console.log("===  CreateTblHeader ===== ");
        //console.log("field_setting", field_setting);
        //console.log("col_hidden", col_hidden);

//--- get info from selected department_map
        let sct_caption = null, has_profiel = false,  lvl_req = false, sct_req = false;
        const dep_dict = get_mapdict_from_datamap_by_tblName_pk(department_map, "department", setting_dict.sel_department_pk);
        if(dep_dict){
            has_profiel = (!!dep_dict.has_profiel);
            lvl_req = (!!dep_dict.lvl_req);
            sct_req = (!!dep_dict.sct_req);
        }

// +++  insert header and filter row ++++++++++++++++++++++++++++++++
        let tblRow_group_header = null;
        if (selected_btn === "btn_overview"){
            tblRow_group_header = tblHead_datatable.insertRow (-1);
        };
        const column_count = field_setting.field_names.length;
        const tblRow_header = tblHead_datatable.insertRow (-1);
        const tblRow_filter = tblHead_datatable.insertRow (-1);

    // --- loop through columns
        for (let j = 0; j < column_count; j++) {
            const field_name = field_setting.field_names[j];
            let th_header = null, el_header = null;

    // skip columns if in columns_hidden
            if (!col_hidden.includes(field_name)){
        // --- get field_caption from field_setting, display 'Profiel' in column sct_abbrev if has_profiel
                const key = field_setting.field_caption[j];
                const field_caption = (field_name === "sct_abbrev" && has_profiel) ? loc.Profiel : (loc[key]) ? loc[key] : key;
                const filter_tag = field_setting.filter_tags[j];
                const class_width = "tw_" + field_setting.field_width[j] ;
                const class_align = "ta_" + field_setting.field_align[j];

        //console.log(j, "field_name", field_name);
// ++++++++++ insert columns in group header row +++++++++++++++
                if (selected_btn === "btn_overview"){
            // --- add th to tblRow_header
                    if([0, 1, 2, 3, 4, 5, 8, 11, 14, 17, 20].includes(j)){


    // --- add left border, not when status field
                        const key = field_settings.group_header.field_caption[j];
                        const field_caption = (loc[key]) ? loc[key] : key;
                        th_header = document.createElement("th");
        //console.log(j, "key", key);
        //console.log(j, "field_caption", field_caption);
        // --- add div to th, margin not working with th
                        const el_header = document.createElement("div");
            // --- add innerText to el_header
                        th_header.innerText = field_caption;
            // --- add width, text_align, right padding in examnumber
                        th_header.classList.add(class_width, class_align);
                        el_header.classList.add(class_width, class_align);
            // --- add  left border before each group
                        if(selected_btn === "btn_overview" && [5, 8, 11, 14, 17, 20].includes(j)){
                            th_header.classList.add("border_left");
                        };

                        // if(field_name === "examnumber"){el_header.classList.add("pr-2")};
                        if(j > 4){
        //console.log(j, "colspan", field_caption);
                            th_header.setAttribute("colspan", 3);
                        };
                        //th_header.appendChild(el_header)
                        tblRow_group_header.appendChild(th_header);
                    };
                };
// ++++++++++ insert columns in header row +++++++++++++++
        // --- add th to tblRow_header
                th_header = document.createElement("th");
        // --- add div to th, margin not working with th
                    const el_header = document.createElement("div");
        // --- add innerText to el_header
                    el_header.innerText = field_caption;
        // --- add width, text_align, right padding in examnumber
                    th_header.classList.add(class_width, class_align);
                    el_header.classList.add(class_width, class_align);
                    // if(field_name === "examnumber"){el_header.classList.add("pr-2")};
        // --- add  left border before each group
                    if(selected_btn === "btn_overview" && [5, 8, 11, 14, 17, 20].includes(j)){
                        th_header.classList.add("border_left");
                    };

                    th_header.appendChild(el_header)
                tblRow_header.appendChild(th_header);

// ++++++++++ create filter row +++++++++++++++
        // --- add th to tblRow_filter.
                const th_filter = document.createElement("th");

        // --- create element with tag based on filter_tag
                const filter_field_tag = (["text", "number"].includes(filter_tag)) ? "input" : "div";
                const el_filter = document.createElement(filter_field_tag);

        // --- add data-field Attribute.
                el_filter.setAttribute("data-field", field_name);
                el_filter.setAttribute("data-filtertag", filter_tag);

        // --- add EventListener to el_filter / th_filter
                if (filter_tag === "select") {
                    th_filter.addEventListener("click", function(event){HandleFilterSelect(el_filter)});
                    add_hover(th_filter);
                } else if (filter_tag === "text") {
                    el_filter.addEventListener("keyup", function(event){HandleFilterKeyup(el_filter, event)});
                    add_hover(th_filter);
                } else if (filter_tag === "toggle") {
                    // add EventListener for icon to th_filter, not el_filter
                    th_filter.addEventListener("click", function(event){HandleFilterToggle(el_filter)});
                    th_filter.classList.add("pointer_show");

                    el_filter.classList.add("tickmark_0_0");
                    add_hover(th_filter);
                }

        // --- add other attributes
                if (filter_tag === "text") {
                    el_filter.setAttribute("type", "text")
                    el_filter.classList.add("input_text");

                    el_filter.setAttribute("autocomplete", "off");
                    el_filter.setAttribute("ondragstart", "return false;");
                    el_filter.setAttribute("ondrop", "return false;");
                }

        // --- add width, text_align
                // PR2021-05-30 debug. Google chrome not setting width without th_filter class_width
                th_filter.classList.add(class_width, class_align);
        // --- add  left border before each group
                if(selected_btn === "btn_overview" && [5, 8, 11, 14, 17, 20].includes(j)){
                    th_filter.classList.add("border_left");
                };

                // el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");
                th_filter.appendChild(el_filter)
                tblRow_filter.appendChild(th_filter);
            }  //  if (!columns_hidden[field_name])
        }  // for (let j = 0; j < column_count; j++)
    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09 PR2021-06-21 PR2021-12-14
    function CreateTblRow(tblName, field_setting, data_dict, col_hidden) {
        //console.log("=========  CreateTblRow =========", tblName);
        //console.log("data_dict", data_dict);

        const field_names = field_setting.field_names;
        //const field_tags = field_setting.field_tags;
        const field_tag = "div";
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;

// ---  lookup index where this row must be inserted
        const ob1 = (data_dict.fullname) ? data_dict.fullname : "";
        // ordering of table overview is doe on server, put row at end
        const row_index = (selected_btn === "btn_result") ? b_recursive_tblRow_lookup(tblBody_datatable, setting_dict.user_lang, ob1) : -1;

// --- insert tblRow into tblBody at row_index
        const tblRow = tblBody_datatable.insertRow(row_index);
        if (data_dict.mapid) {tblRow.id = data_dict.mapid};

// --- add data attributes to tblRow
        tblRow.setAttribute("data-pk", data_dict.id);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);

// --- add EventListener to tblRow
        tblRow.addEventListener("click", function() {HandleTblRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
        for (let j = 0; j < column_count; j++) {
            const field_name = field_names[j];

    // skip columns if in columns_hidden
            if (!col_hidden.includes(field_name)){
                const class_width = "tw_" + field_width[j];
                const class_align = "ta_" + field_align[j];

    // --- insert td element,
                const td = tblRow.insertCell(-1);

    // --- create element with tag from field_tags
                const el = document.createElement(field_tag);

        // --- add data-field attribute
                el.setAttribute("data-field", field_name);

        // --- add  text_align
                el.classList.add(class_width, class_align);

        // --- add  left border before each group
                if(selected_btn === "btn_overview" && [5, 8, 11, 14, 17, 20].includes(j)){
                    td.classList.add("border_left");
                };

        // --- append element
                td.appendChild(el);

// --- add EventListener to td
                if (field_name === "withdrawn") {
                    if(permit_dict.permit_crud && permit_dict.requsr_same_school){
                        td.addEventListener("click", function() {UploadToggle(el)}, false)
                        add_hover(td);
                       // this is done in add_hover:  td.classList.add("pointer_show");
                    };
                };
    // --- put value in field
               UpdateField(el, data_dict)
           }  // if (!columns_hidden[field_name])
        }  // for (let j = 0; j < 8; j++)
        return tblRow
    };  // CreateTblRow

//=========  UpdateTblRow  ================ PR2020-08-01
    function UpdateTblRow(tblRow, tblName, data_dict) {
        //console.log("=========  UpdateTblRow =========");
        if (tblRow && tblRow.cells){
            for (let i = 0, td; td = tblRow.cells[i]; i++) {
                UpdateField(td.children[0], data_dict);
            }
        }
    };  // UpdateTblRow

//=========  UpdateField  ================ PR2020-08-16 PR2021-06-16
    function UpdateField(el_div, data_dict) {
        //console.log("=========  UpdateField =========");
        //console.log("data_dict", data_dict);

        if(el_div){
            const field_name = get_attr_from_el(el_div, "data-field");
            const fld_value = data_dict[field_name];
        //console.log("field_name", field_name);
        //console.log("fld_value", fld_value);

            if(field_name){
                let filter_value = null;
                if (field_name === "select") {
                    // TODO add select multiple users option PR2020-08-18
                } else if (field_name === "withdrawn") {
                    el_div.className = (data_dict.withdrawn) ? "tickmark_2_2" : "tickmark_0_0";
                    filter_value = (data_dict.withdrawn) ? "1" : "0";
                    el_div.setAttribute("data-value", filter_value);

                } else if (["lvl_code", "sct_code"].includes(field_name)){
                    // put hard return in el_div, otherwise green border doesnt show in update PR2021-06-16
                    let abbrev = null;
                    if (field_name === "lvl_code"){
                        abbrev = (data_dict.lvl_code) ? data_dict.lvl_code : null;
                    } else if (field_name === "sct_abbrev"){
                        abbrev = (data_dict.sct_abbrev) ? data_dict.sct_abbrev : null;
                    }
                    el_div.innerText = (abbrev) ? abbrev : "\n";
                    filter_value = (abbrev) ? abbrev.toLowerCase() : null;

                } else if (field_name === "result_status") {
                    // put hard return in el_div, otherwise green border doesnt show in update PR2021-06-16
                    el_div.innerText = (fld_value) ? fld_value : "\n";
                    filter_value = (fld_value) ? fld_value.toLowerCase() : null;

                    if (data_dict.result_info) {
                        el_div.title = data_dict.result_info.replaceAll("|", "\n"); // replace | with \n // g modifier replaces all occurances
                    };

                } else {
                    // put hard return in el_div, otherwise green border doesnt show in update PR2021-06-16
                    if (fld_value == null || fld_value === "" ){
                        el_div.innerText = "\n";
                        filter_value = null;
                    } else if (typeof fld_value === 'string' || fld_value instanceof String){
                    // replace dot with comma
                        el_div.innerText = fld_value
                        filter_value = fld_value.toLowerCase();
                    } else {
                        el_div.innerText = (fld_value) ? fld_value : null;
                        filter_value = fld_value;
                    };
                };
    // ---  add attribute filter_value
                add_or_remove_attr (el_div, "data-filter", !!filter_value, filter_value);
            }  // if(field_name)
        }  // if(el_div)
    };  // UpdateField

// +++++++++++++++++ UPLOAD CHANGES +++++++++++++++++ PR2020-08-03

//========= Response_from_SBR_select_level_sector  ============= PR2021-11-17
    function Response_from_SBR_select_level_sector(tblName, selected_base_pk) {
        console.log(" =====  Response_from_SBR_select_level_sector  =====");
        console.log("tblName: ", tblName);
        console.log("selected_base_pk: ", selected_base_pk);

        const key_str = (tblName === "lvlbase") ? "sel_lvlbase_pk" : (tblName === "sctbase") ? "sel_sctbase_pk" : null;
        const new_setting = {page: "page_result"};
        if (key_str){
            new_setting[key_str] = selected_base_pk;
        }
        console.log("key_str: ", key_str);
        console.log("new_setting: ", new_setting);
        const datalist_request = {
                setting: new_setting,
                student_rows: {cur_dep_only: true}
            };

        DatalistDownload(datalist_request, true); // true = skip_messages
    };  // Response_from_SBR_select_level_sector


//========= UploadToggle  ============= PR2022-06-05
    function UploadToggle(el_input) {
        console.log( " ==== UploadToggle ====");
        console.log( "el_input", el_input);
        // (still) only called in brn Exemptions
        if (permit_dict.permit_crud && permit_dict.requsr_same_school){

            const tblRow = t_get_tablerow_selected(el_input);
            const pk_int = get_attr_from_el_int(tblRow, "data-pk");

// --- get existing data_dict from data_rows
            const [index, found_dict, compare] = b_recursive_integer_lookup(student_rows, "id", pk_int);
            const data_dict = (!isEmpty(found_dict)) ? found_dict : null;

            const fldName = get_attr_from_el(el_input, "data-field");
            const old_value = get_attr_from_el_int(el_input, "data-value");

        console.log( "old_value", old_value, typeof old_value);
            const new_value = (!old_value);
            mod_dict = {
                table: "student",
                mode: "withdrawn",
                student_pk: pk_int,
                withdrawn: new_value,
                el_input: el_input,
                data_dict: data_dict
            };
    // open mod confirm
            ModConfirmOpen("withdrawn");
        }; //   if(permit_dict.permit_approve_subject)
    };  // UploadToggle


//========= UploadChanges  ============= PR2020-08-03
    function UploadChanges(upload_dict, url_str) {
        console.log("=== UploadChanges");
        console.log("url_str: ", url_str);
        console.log("upload_dict: ", upload_dict);

        if(!isEmpty(upload_dict)) {
            const parameters = {"upload": JSON.stringify (upload_dict)}
            let response = "";
            $.ajax({
                type: "POST",
                url: url_str,
                data: parameters,
                dataType:'json',
                success: function (response) {
    // ---  hide loader
                    el_loader.classList.add(cls_visible_hide)
                    console.log( "response");
                    console.log( response);

                    if ("updated_student_rows" in response) {
                        const el_MSTUD_loader = document.getElementById("id_MSTUD_loader");
                        if(el_MSTUD_loader){ el_MSTUD_loader.classList.add(cls_visible_hide)};

                        const tblName = "student";
                        RefreshDataRows(tblName, response.updated_student_rows, student_rows, true)  // true = update
                    };

                    if("messages" in response){
                        b_show_mod_message_dictlist(response.messages);
                    }
                    if ("validate_scheme_response" in response) {
                        ValidateScheme_Response(response.validate_scheme_response)
                    }
                    if ("pres_secr_dict" in response) {
                        MGL_ResponseAuth(response.pres_secr_dict)
                    }
                    if ("log_list" in response) {
                        OpenLogfile(response.log_list);
                    }


                    $("#id_mod_student").modal("hide");

                },  // success: function (response) {
                error: function (xhr, msg) {
                    // ---  hide loader
                    el_loader.classList.add(cls_visible_hide)
                    console.log(msg + '\n' + xhr.responseText);
                }  // error: function (xhr, msg) {
            });  // $.ajax({
        }  //  if(!!row_upload)
    };  // UploadChanges

// +++++++++++++++++ UPDATE +++++++++++++++++++++++++++++++++++++++++++
//=========   OpenLogfile   ====================== PR2021-11-20
    function OpenLogfile(log_list) {
        //console.log(" ========== OpenLogfile ===========");

        if (!!log_list && log_list.length) {
            const today = new Date();
            const this_month_index = 1 + today.getMonth();
            const date_str = today.getFullYear() + "-" + this_month_index + "-" + today.getDate();
            let filename = "Log calculate results dd " + get_now_formatted() + ".pdf";

            printPDFlogfile(log_list, filename )
        };
    }; //OpenLogfile

//###########################################################################
// +++++++++++++++++ REFRESH DATA ROWS ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataRowsAfterUpload  ================ PR2021-07-20
function RefreshDataRowsAfterUpload(response) {
    //console.log(" --- RefreshDataRowsAfterUpload  ---");
    //console.log("response:", response);
    const is_test = (!!response && !!response.is_test) ;
    if(!is_test && response && "updated_student_rows" in response) {
        RefreshDataRows("student", response.updated_student_rows, student_rows, true)  // true = update
    }

}  // RefreshDataRowsAfterUpload

//=========  RefreshDataRows  ================ PR2020-08-16 PR2021-06-16
    function RefreshDataRows(tblName, update_rows, data_rows, is_update) {
        //console.log(" --- RefreshDataRows  ---");
        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length

        if (update_rows && update_rows.length ) {
            const field_setting = field_settings[tblName];
            for (let i = 0, update_dict; update_dict = update_rows[i]; i++) {
                RefreshDatarowItem(tblName, field_setting, update_dict, data_rows);
            }
        } else if (!is_update) {
            // empty the data_rows when update_rows is empty PR2021-01-13 debug forgot to empty data_rows
            // PR2021-03-13 debug. Don't empty de data_rows when is update. Returns [] when no changes made
           data_rows = [];
        }
    }  //  RefreshDataRows

//=========  RefreshDatarowItem  ================ PR2020-08-16 PR2020-09-30 PR2021-06-16
    function RefreshDatarowItem(tblName, field_setting, update_dict, data_rows) {
        //console.log(" --- RefreshDatarowItem  ---");
        //console.log("tblName", tblName);
        //console.log("update_dict", update_dict);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);

            let field_error_list = []
            const error_list = get_dict_value(update_dict, ["error"], []);
        //console.log("error_list", error_list);

            if(error_list && error_list.length){

    // - show modal messages
                b_show_mod_message_dictlist(error_list);

    // - add fields with error in field_error_list, to put old value back in field
                for (let i = 0, msg_dict ; msg_dict = error_list[i]; i++) {
                    if ("field" in msg_dict){field_error_list.push(msg_dict.field)};
                };
            // close modal when no error --- already done in modal
            }

// ++++ created ++++
            // PR2021-06-16 from https://stackoverflow.com/questions/586182/how-to-insert-an-item-into-an-array-at-a-specific-index-javascript
            //arr.splice(index, 0, item); will insert item into arr at the specified index
            // (deleting 0 items first, that is, it's just an insert).

            if(is_created){
    // ---  first remove key 'created' from update_dict
                delete update_dict.created;

    // --- lookup index where new row must be inserted in data_rows
                // not necessary:
                // rows are sorted by id int. new row always has a bigger int, therefore new dict can go at the end
                // was: insert new row in data_rows. Splice inserts row at index, 0 means deleting zero rows
                //      data_rows.splice(map_index, 0, update_dict);

    // ---  insert new item at end
                data_rows.push(update_dict)

    // ---  create row in table., insert in alphabetical order
                const new_tblRow = CreateTblRow(tblName, field_setting, update_dict)

    // ---  scrollIntoView,
                if(new_tblRow){
                    new_tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' })

    // ---  make new row green for 2 seconds,
                    ShowOkElement(new_tblRow);
                }
            } else {

// --- get existing data_dict from data_rows
                const pk_int = (update_dict && update_dict.id) ? update_dict.id : null;
                const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);
                const data_dict = (!isEmpty(found_dict)) ? found_dict : null;
                const datarow_index = index;
        //console.log("pk_int", pk_int);
        //console.log("data_dict", data_dict);

// ++++ deleted ++++
                if(is_deleted){
                    // delete row from data_rows. Splice returns array of deleted rows
                    const deleted_row_arr = data_rows.splice(datarow_index, 1)
                    const deleted_row_dict = deleted_row_arr[0];
        //console.log("deleted_row_dict", deleted_row_dict);
        //console.log("deleted_row_dict.mapid", deleted_row_dict.mapid);

        //--- delete tblRow
                    if(deleted_row_dict && deleted_row_dict.mapid){
                        const tblRow_tobe_deleted = document.getElementById(deleted_row_dict.mapid);
        //console.log("tblRow_tobe_deleted", tblRow_tobe_deleted);
                        if (tblRow_tobe_deleted ){
                            tblRow_tobe_deleted.parentNode.removeChild(tblRow_tobe_deleted);
                        };
                    }
                } else {

// +++++++++++ updated row +++++++++++
    // ---  check which fields are updated, add to list 'updated_columns'
                    if(!isEmpty(data_dict) && field_names){

        //console.log("data_dict", data_dict);
                        let updated_columns = [];
                        // skip first column (is margin)
                        for (let i = 1, col_field, old_value, new_value; col_field = field_names[i]; i++) {
                            if (col_field in data_dict && col_field in update_dict){
                                if (data_dict[col_field] !== update_dict[col_field] ) {
        // ---  add field to updated_columns list
                                    updated_columns.push(col_field)
                                }};
                        };
        //console.log("updated_columns", updated_columns);

// ---  update fields in data_row
                        for (const [key, new_value] of Object.entries(update_dict)) {
                            if (key in data_dict){
                                if (new_value !== data_dict[key]) {
                                    data_dict[key] = new_value
                        }}};
        //console.log("data_dict", data_dict);

        // ---  update field in tblRow
                        // note: when updated_columns is empty, then updated_columns is still true.
                        // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
                        if(updated_columns.length){

// --- get existing tblRow
                            let tblRow = document.getElementById(map_id);
                            if(tblRow){
                                // to make it perfect: move row when first or last name have changed
                                if (updated_columns.includes("fullname")){
                                //--- delete current tblRow
                                    tblRow.parentNode.removeChild(tblRow);
                                //--- insert row new at new position
                                    tblRow = CreateTblRow(tblName, field_setting, update_dict)
                                };

        //console.log("tblRow", tblRow);
                // loop through cells of row
                                for (let i = 1, el_fldName, el, td; td = tblRow.cells[i]; i++) {
                                    el = td.children[0];
                                    if (el){
        //console.log("el", el);
                                        el_fldName = get_attr_from_el(el, "data-field")
        //console.log("el_fldName", el_fldName);
                                        UpdateField(el, update_dict);

                // make field green when field name is in updated_columns
                                        if(updated_columns.includes(el_fldName)){
                                            ShowOkElement(el);
                                        };
                                    };
                                };  //  for (let i = 1, el_fldName
                            };  // if(tblRow)
                        }; // if(updated_columns.length)
                    };  //  if(!isEmpty(data_dict) && field_names){
                };  // if(is_deleted)
            };  // if(is_created)
        //console.log("student_rows", student_rows);
        };  // if(!isEmpty(update_dict))
    };  // RefreshDatarowItem


// +++++++++++++++++ MODAL GRADEIST +++++++++++++++++++++++++++++++++++++++++++
//=========  MGL_Open  ================ PR2021-11-18 PR2021-12-28
    function MGL_Open(mode) {
        console.log(" -----  MGL_Open   ----")
        // only called by menubtn Preliminary_gradelist and PrintGradelist
        mod_dict = {mode: mode};
        el_MGL_header.innerText = (mode === "prelim") ? loc.Preliminary_gradelist : loc.Download_gradelist;
        // hide "Print uitslag 'Herexamen' instead of 'Afgewezen'" when printing final grade list
        add_or_remove_attr(el_MGL_print_reex_container, cls_hide, mode !== "prelim")

        const student_count = student_rows.length;
        console.log("student_count", student_count);

        let count = 0, student_pk_list = [], print_all = false;
// get all visible students selected
        if (!student_count){
            msg_html = "no students"
        } else {
// --- count number of selected elements that are not hidden
            const elements = tblBody_datatable.querySelectorAll("tr:not(.display_hide).tsa_tr_selected");

            for (let i = 0, tr, el; tr = elements[i]; i++) {
                const pk_int = get_attr_from_el_int(tr, "data-pk");
                if(pk_int){
                    student_pk_list.push(pk_int);
                    count += 1;
                };
            };

// if there are no selected elements that are not hidden:
            if (!student_pk_list.length){
// --- count number of elements that are not hidden
                const elements = tblBody_datatable.querySelectorAll("tr:not(.display_hide)");
                for (let i = 0, tr, el; tr = elements[i]; i++) {
                    const pk_int = get_attr_from_el_int(tr, "data-pk");
                    if(pk_int){
                        student_pk_list.push(pk_int);
                        count += 1;
                    };
                };
            }
// --- if all students are in list: set print_all = true, so you dont have to filter database on student_pk_list
            if (student_pk_list.length === student_count){
                print_all = true;
                student_pk_list = [];
                count = student_count;
            }
        }
        if(student_pk_list.length) {
            mod_dict.student_pk_list = student_pk_list;
        }
        mod_dict.print_all = print_all;

        console.log("student_pk_list", student_pk_list);
        console.log("count", count);

        const msg01_txt =  (mode === "prelim") ? loc.The_preliminary_gradelist_of : loc.The_final_gradelist_of;
        let msg02_txt = '';
        if (count === 1) {
            if (student_count === 1) {
                msg02_txt = "&emsp;" + student_rows[0].fullname;
            } else {
                const pk_int = student_pk_list[0];
                const [index, found_dict, compare] = b_recursive_integer_lookup(student_rows, "id", pk_int);
                const data_dict = (!isEmpty(found_dict)) ? found_dict : null;
                if (!isEmpty(data_dict)) {msg02_txt = "&emsp;" + data_dict.fullname};
            };
        } else {
            msg02_txt = "&emsp;" + count + loc.candidates;  // &emsp—the em space, wide space equal 4 normal spaces
        }
        const msg_html = ["<div class='p-2'>",
                            msg01_txt, "<br>",  msg02_txt, "<br>",
                            loc.will_be_downloaded,
                             "</div>"
                          ].join("");
        console.log("msg_html", msg_html);
        el_MGL_info_container.innerHTML = msg_html;
        console.log("el_MGL_info_container", el_MGL_info_container);
        console.log("pres_secr_dict", pres_secr_dict);

// ---  get auth and printdate info from server
        UploadChanges({ get: true}, urls.url_get_auth);

// ---  disable save button
        el_MGL_btn_save.disabled = true;

// show loader
        el_MGL_loader.classList.remove(cls_visible_hide)

        const selected_value = null;
        t_FillOptionsFromList(el_MGL_select_pres, pres_secr_dict.auth1, "pk", "name",
                                    loc.Select_a_chairperson, loc.No_chairperson, selected_value);
        t_FillOptionsFromList(el_MGL_select_secr, pres_secr_dict.auth2, "pk", "name",
                                    loc.Select_a_secretary, loc.No_secretary, selected_value);

        $("#id_mod_gradelist").modal({backdrop: true});
    };  // MGL_Open

//=========  MGL_ResponseAuth  ================ PR2021-11-19 PR2021-12-28
    function MGL_ResponseAuth(pres_secr_dict) {
        console.log(" -----  MGL_ResponseAuth   ----")
        console.log("pres_secr_dict", pres_secr_dict)

// ---  enable save button
        el_MGL_btn_save.disabled = false;

// ---  hide loader
        el_MGL_loader.classList.add(cls_visible_hide)

        const selected_value = null;
        t_FillOptionsFromList(el_MGL_select_pres, pres_secr_dict.auth1, "pk", "name",
                                    loc.Select_a_chairperson, loc.No_chairperson, selected_value);
        t_FillOptionsFromList(el_MGL_select_secr, pres_secr_dict.auth2, "pk", "name",
                                    loc.Select_a_secretary, loc.No_secretary, selected_value);
        el_MGL_printdate.value = (pres_secr_dict.printdate) ? pres_secr_dict.printdate : null;

    };  // MGL_ResponseAuth

//=========  MGL_Save  ================ PR2021-11-18
    function MGL_Save(mode) {
        console.log(" -----  MGL_Save   ----")
        const el_MGL_link = document.getElementById("id_MGL_link");

        let href = null;
        const upload_dict = {
            mode: mod_dict.mode,
            print_all: mod_dict.print_all,
            print_reex: el_MGL_print_reex.checked
        };
        if (mod_dict.student_pk_list) { upload_dict.student_pk_list = mod_dict.student_pk_list};
        if (mod_dict.print_all) { upload_dict.print_all = mod_dict.print_all};

        if (Number(el_MGL_select_pres.value)) { upload_dict.auth1_pk = Number(el_MGL_select_pres.value)};
        if (Number(el_MGL_select_secr.value)) { upload_dict.auth2_pk = Number(el_MGL_select_secr.value)};
        if (el_MGL_printdate.value) { upload_dict.printdate = el_MGL_printdate.value};

        const href_str = JSON.stringify(upload_dict);
        href = urls.url_download_gradelist.replace("-", href_str);

        el_MGL_link.href = href;
        el_MGL_link.click();

        $("#id_mod_gradelist").modal("hide");

    };  // MGL_Save


//=========  Calc_result  ================ PR2019-11-19
    function Calc_result(){
        console.log(" --- Calc_result --- ");

        const student_count = student_rows.length;
        let count = 0, student_pk_list = [], print_all = false;

        console.log("student_count", student_count);
// get all visible students selected
        if (student_count){
// --- count number of selected elements that are not hidden
            const elements = tblBody_datatable.querySelectorAll("tr:not(.display_hide).tsa_tr_selected");
            for (let i = 0, tr, el; tr = elements[i]; i++) {
                const pk_int = get_attr_from_el_int(tr, "data-pk");
                if(pk_int){
                    student_pk_list.push(pk_int);
                    count += 1;
                };
            };
// if there are no selected elements that are not hidden:
            if (!student_pk_list.length){
// --- count number of elements that are not hidden
                const elements = tblBody_datatable.querySelectorAll("tr:not(.display_hide)");
                for (let i = 0, tr, el; tr = elements[i]; i++) {
                    const pk_int = get_attr_from_el_int(tr, "data-pk");
                    if(pk_int){
                        student_pk_list.push(pk_int);
                        count += 1;
                    };
                };
            }
// --- if all students are in list: set print_all = true, so you dont have to filter database on student_pk_list
            if (student_pk_list.length === student_count){
                print_all = true;
                student_pk_list = [];
                count = student_count;
            }
        }
        if(student_pk_list.length) {
         student_pk_list = student_pk_list;
         }
        console.log("student_pk_list", student_pk_list);

        let href = null;
        const upload_dict = {};
        if (student_pk_list) {upload_dict.student_pk_list = student_pk_list};

        console.log("upload_dict", upload_dict);

    // ---  Upload Changes
        let url_str = urls.url_calc_results;
        UploadChanges(upload_dict, url_str);


    };  // Calc_result

// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2020-08-03 PR2021-06-15 PR2021-07-23 PR2022-05-10
    function ModConfirmOpen(mode) {
        console.log(" -----  ModConfirmOpen   ----")
        // only called by menubtn Delete_candidate and mod MSTUD btn delete
        // values of mode are : "prelim_ex5",  "delete" , "validate_scheme", "correct_scheme"

        const tblName = "student";
        let show_modal = false;

// ---  get selected.student_dict
        // already done in HandleTblRowClicked

// ---  get info from data_map
        const map_dict = selected.student_dict;
    //console.log("map_dict", map_dict)

        console.log("mode", mode)

        if(["prelim_ex5", "overview"].includes(mode)){

// ---  create mod_dict
            mod_dict = {mode: mode};
            const has_selected_item = (!isEmpty(map_dict));

            //el_confirm_btn_cancel.innerText = (has_selected_item) ? loc.No_cancel : loc.Close;
            el_confirm_btn_save.innerText = loc.OK;
            el_confirm_btn_cancel.innerText = loc.Cancel;


            add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", false, "btn-primary");
        };

// ---  put text in modal for
        let header_text = "";
        let msg_html = "";

        let msg01_txt = null, msg02_txt = null, msg03_txt = null;
        let hide_save_btn = false;

        const full_name = (map_dict.fullname) ? map_dict.fullname  : "---";
        if(mode === "overview"){
            show_modal = true;
            header_text = loc.Download_overview;
            msg_html = ["<p>", loc.The_overview_of_results, " ", loc.will_be_downloaded, "</p><p>"].join("");

            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            if (el_modconfirm_link) {
                const url_str = urls.url_result_download_overview;
                el_modconfirm_link.setAttribute("href", url_str);
            };

        } else if(mode === "prelim_ex5"){
            show_modal = true;
            header_text = loc.Download_Ex_form;
            msg_html = ["<p>", loc.The_preliminary_ex5_form, " ", loc.will_be_downloaded, "</p><p>", loc.Do_you_want_to_continue, "</p>"].join("");

            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            if (el_modconfirm_link) {
                const url_str = urls.url_result_download_ex5;
                el_modconfirm_link.setAttribute("href", url_str);
            };

        } else if(mode === "withdrawn"){

            const may_edit = (permit_dict.permit_crud && permit_dict.requsr_same_school);
            if (may_edit){
                show_modal = true;

        console.log("mod_dict", mod_dict)
        /*
            mod_dict = {
                table: "student",
                mode: "withdrawn",
                student_pk: pk_int,
                withdrawn: new_value,
                el_input: el_input,
                data_dict: data_dict
        */

                header_text = loc.Withdraw_candidate;
                const full_name = (mod_dict.data_dict && mod_dict.data_dict.fullname) ? mod_dict.data_dict.fullname  : "---";
                if(mod_dict.withdrawn){
                    msg01_txt = loc.Candidate +  ":<br>&emsp;" + full_name + "<br>" + loc.will_be_withdrawn;
                } else {
                    msg01_txt = loc.Status_withdrawn_of + "<br>&emsp;" + full_name + "<br>" + loc.will_be_removed;
                };
                msg02_txt = loc.Do_you_want_to_continue;
            };
         };

        el_confirm_header.innerText = header_text;
        el_confirm_loader.classList.add(cls_visible_hide)
        add_or_remove_class(el_confirm_loader)
        el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");

        if (msg01_txt) {msg_html += "<p>" + msg01_txt + "</p>"};
        if (msg02_txt) {msg_html += "<p>" + msg02_txt + "</p>"};
        if (msg03_txt) {msg_html += "<p>" + msg03_txt + "</p>"};
        el_confirm_msg_container.innerHTML = msg_html

        const caption_save = (mode === "delete") ? loc.Yes_delete : loc.OK;
        el_confirm_btn_save.innerText = caption_save;
        add_or_remove_class (el_confirm_btn_save, cls_hide, hide_save_btn);


// set focus to cancel button
        set_focus_on_el_with_timeout(el_confirm_btn_cancel, 150);

// show modal
        if (show_modal) {
            $("#id_mod_confirm").modal({backdrop: true});
        };
    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2019-06-23
    function ModConfirmSave() {
        //console.log(" --- ModConfirmSave --- ");
        //console.log("mod_dict: ", mod_dict);

        const may_edit = (permit_dict.permit_crud && permit_dict.requsr_same_school);
// ---  Upload Changes
        let url_str = null;
        if(mod_dict.mode === "prelim_ex5"){
            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            if (el_modconfirm_link) {
                el_modconfirm_link.click();
            // show loader
                el_confirm_loader.classList.remove(cls_visible_hide)
            };

        } else if(mod_dict.mode === "withdrawn"){
            if(may_edit){
                const upload_dict = {
                        mode: mod_dict.mode,
                        table: "student",
                        student_pk: mod_dict.student_pk,
                        withdrawn: mod_dict.withdrawn
                        };
                UploadChanges(upload_dict, urls.url_student_upload);
     // ---  change icon, before uploading
                // when validation on server side fails, the old value is reset by RefreshDataRowItem PR2022-05-27
                // updated_studsubj_rows must contain ie err_fields: ['has_reex']
                add_or_remove_class(mod_dict.el_input, "tickmark_1_2", mod_dict.withdrawn, "tickmark_0_0");
            };
        };
// ---  hide modal
        $("#id_mod_confirm").modal("hide");
    };  // ModConfirmSave

//=========  ModConfirmResponse  ================ PR2019-06-23
    function ModConfirmResponse(response) {
        console.log(" --- ModConfirmResponse --- ");
        console.log("mod_dict: ", mod_dict);
        // hide loader
        el_confirm_loader.classList.add(cls_visible_hide)
        const mode = get_dict_value(response, ["mode"])
        if(mode === "delete"){
//--- delete tblRow. Multiple deleted rows not in use yet, may be added in the future PR2020-08-18
            if ("updated_list" in response) {
                for (let i = 0, updated_dict; updated_dict = response.updated_list[i]; i++) {
                    if(updated_dict.deleted) {
                        const tblRow = document.getElementById(updated_dict.mapid)
                        if (tblRow){ tblRow.parentNode.removeChild(tblRow) };
                    }
                }
            };
        }
        if ("msg_err" in response || "msg_ok" in response) {
            let msg01_txt = null, msg02_txt = null, msg03_txt = null;
            if ("msg_err" in response) {
                msg01_txt = get_dict_value(response, ["msg_err", "msg01"], "");
                if (mod_dict.mode === "send_activation_email") {
                    msg02_txt = loc.Activation_email_not_sent;
                }
                el_confirm_msg_container.classList.add("border_bg_invalid");
            } else if ("msg_ok" in response){
                msg01_txt  = get_dict_value(response, ["msg_ok", "msg01"]);
                msg02_txt = get_dict_value(response, ["msg_ok", "msg02"]);
                msg03_txt = get_dict_value(response, ["msg_ok", "msg03"]);
                el_confirm_msg_container.classList.add("border_bg_valid");
            }

            let msg_html = "";
            if (msg01_txt) {msg_html += "<p>" + msg01_txt + "</p>"};
            if (msg02_txt) {msg_html += "<p>" + msg02_txt + "</p>"};
            if (msg03_txt) {msg_html += "<p>" + msg03_txt + "</p>"};
            el_confirm_msg_container.innerHTML = msg_html

            el_confirm_btn_cancel.innerText = loc.Close
            el_confirm_btn_save.classList.add(cls_hide);
        } else {
        // hide mod_confirm when no message
            $("#id_mod_confirm").modal("hide");
        };
    };  // ModConfirmResponse

//=========  ModMessageHide  ================ PR2022-05-28
    function ModMessageHide() {
        console.log(" --- ModMessageHide --- ");
        // hide message that opens when opening page
        const upload_dict = {hide_msg: true};
        UploadChanges(upload_dict, urls.url_user_modmsg_hide)
    }  // ModMessageHide


//###########################################################################
// +++++++++++++++++ FILTER TABLE ROWS ++++++++++++++++++++++++++++++++++++++

//========= HandleFilterKeyup  ================= PR2021-06-16
    function HandleFilterKeyup(el, event) {
        //console.log( "===== HandleFilterKeyup  ========= ");
        // skip filter if filter value has not changed, update variable filter_text

        // PR2021-05-30 debug: use cellIndex instead of attribute data-colindex,
        // because data-colindex goes wrong with hidden columns
        // was:  const col_index = get_attr_from_el(el_input, "data-colindex")
        const col_index = el.parentNode.cellIndex;
        //console.log( "col_index", col_index, "event.key", event.key);

        const skip_filter = t_SetExtendedFilterDict(el, col_index, filter_dict, event.key);
        //console.log( "filter_dict", filter_dict);

        if (!skip_filter) {
            Filter_TableRows();
        }
    }; // function HandleFilterKeyup

//========= HandleFilterToggle  =============== PR2021-06-16
    function HandleFilterToggle(el_input) {
        //console.log( "===== HandleFilterToggle  ========= ");

    // - get col_index and filter_tag from  el_input
        // PR2021-05-30 debug: use cellIndex instead of attribute data-colindex,
        // because data-colindex goes wrong with hidden columns
        // was:  const col_index = get_attr_from_el(el_input, "data-colindex")
        const col_index = el_input.parentNode.cellIndex;

    // - get filter_tag from  el_input
        const filter_tag = get_attr_from_el(el_input, "data-filtertag")
        const field_name = get_attr_from_el(el_input, "data-field")
        //console.log( "col_index", col_index);
        //console.log( "filter_tag", filter_tag);
        //console.log( "field_name", field_name);

    // - get current value of filter from filter_dict, set to '0' if filter doesn't exist yet
        const filter_array = (col_index in filter_dict) ? filter_dict[col_index] : [];
        const filter_value = (filter_array[1]) ? filter_array[1] : "0";
        //console.log( "filter_array", filter_array);
        //console.log( "filter_value", field_name);

        let new_value = "0", icon_class = "tickmark_0_0"

        // default filter triple '0'; is show all, '1' is show tickmark, '2' is show without tickmark
// - toggle filter value
        new_value = (filter_value === "2") ? "0" : (filter_value === "1") ? "2" : "1";
// - get new icon_class
        icon_class =  (new_value === "2") ? "tickmark_2_1" : (new_value === "1") ? "tickmark_2_2" : "tickmark_0_0";

    // - put new filter value in filter_dict
        filter_dict[col_index] = [filter_tag, new_value]
        //console.log( "filter_dict", filter_dict);
        el_input.className = icon_class;

        Filter_TableRows();

    };  // HandleFilterToggle

//========= HandleFilterSelect  =============== PR2021-06-16
    function HandleFilterSelect(el_input) {
        //console.log( "===== HandleFilterSelect  ========= ");
        //console.log( "el_input", el_input);

    // - get col_index and filter_tag from  el_input
        // PR2021-05-30 debug: use cellIndex instead of attribute data-colindex,
        // because data-colindex goes wrong with hidden columns
        // was:  const col_index = get_attr_from_el(el_input, "data-colindex")
        const col_index = el_input.parentNode.cellIndex;
        //console.log( "col_index", col_index);

    // - get filter_tag from  el_input
        const filter_tag = get_attr_from_el(el_input, "data-filtertag")
        const field_name = get_attr_from_el(el_input, "data-field")
        //console.log( "filter_tag", filter_tag);
        //console.log( "field_name", field_name);

    // - get current value of filter from filter_dict, set to '0' if filter doesn't exist yet
        const filter_array = (col_index in filter_dict) ? filter_dict[col_index] : [];
        const filter_value = (filter_array[1]) ? filter_array[1] : "0";
        //console.log( "filter_array", filter_array);
        //console.log( "filter_value", field_name);

        let new_value = "0", html_str = null;

        // default filter triple '0'; is show all, '1' is show tickmark, '2' is show without tickmark
// - toggle filter value
        new_value = (filter_value === "1") ? "0" : "1";
// - set el_input.innerHTML
        el_input.innerHTML = (new_value === "1") ? "&#9658;" : null
        if (new_value === "1") {
            // set all visible students selected
             let filter_toggle_elements = tblBody_datatable.querySelectorAll("tr:not(.display_hide:not(.tsa_tr_selected)");
        //console.log("filter_toggle_elements", filter_toggle_elements);
            let count = 0;
             for (let i = 0, tr, el; tr = filter_toggle_elements[i]; i++) {
                tr.classList.add(cls_selected)
                el = tr.cells[0].children[0];
                if (el){ el.innerHTML = "&#9658;"};
                count += 1;
             }
        //console.log("made se;lected: count", count);

        } else {
            // unselect all visible student
             // set all visible students selected
             //let filter_toggle_elements = tblBody_datatable.querySelectorAll("tr.tsa_tr_selected");
             let filter_toggle_elements = tblBody_datatable.querySelectorAll("tr:not(.display_hide).tsa_tr_selected");
        //console.log("filter_toggle_elements", filter_toggle_elements);
            let count = 0;
            for (let i = 0, tr, el; tr = filter_toggle_elements[i]; i++) {
                tr.classList.remove(cls_selected)
                el = tr.cells[0].children[0];
                if (el){ el.innerHTML = null};
                count += 1;
            }
        //console.log("removed selected: count", count);
        }
    // - put new filter value in filter_dict
        // filter_dict = { 0: ['select', '2'], 2: ['text', 'f', ''] }

        filter_dict[col_index] = [filter_tag, new_value]
        //console.log( "filter_dict", filter_dict);

        Filter_TableRows();

    };  // HandleFilterSelect

//========= Filter_TableRows  ==================================== PR2020-08-17
    function Filter_TableRows() {
        //console.log( "===== Filter_TableRows  ========= ");

        const tblName_settings = "student";
        const field_setting = field_settings[tblName_settings];
        const filter_tags = field_setting.filter_tags;
        let item_count = 0

// ---  loop through tblBody.rows
        for (let i = 0, tblRow, show_row; tblRow = tblBody_datatable.rows[i]; i++) {
            show_row = t_ShowTableRowExtended(filter_dict, tblRow);
            add_or_remove_class(tblRow, cls_hide, !show_row);
            if (show_row) {item_count += 1};
        }

// ---  show total in sidebar
        if (el_SBR_item_count){
            let inner_text = null;
            if (item_count){
                const format_count = f_format_count(setting_dict.user_lang, item_count);
                const unit_txt = ((item_count === 1) ? loc.Candidate : loc.Candidates).toLowerCase();
                inner_text = [loc.Total, format_count, unit_txt].join(" ");
            }
            el_SBR_item_count.innerText = inner_text;
        }
    }; // Filter_TableRows

//========= ResetFilterRows  ====================================
    function ResetFilterRows() {  // PR2019-10-26 PR2020-06-20
       //console.log( "===== ResetFilterRows  ========= ");

        selected.student_pk = null;
        selected.student_dict = {};
        filter_dict = {};

        Filter_TableRows();

        let filterRow = tblHead_datatable.rows[1];
        if(!!filterRow){
            for (let j = 0, cell, el; cell = filterRow.cells[j]; j++) {
                if(cell){
                    el = cell.children[0];
                    if(el){
                        const filter_tag = get_attr_from_el(el, "data-filtertag")
                        if(el.tagName === "INPUT"){
                            el.value = null
                        } else {
                            const el_icon = el.children[0];
                            if(el_icon){
                                let classList = el_icon.classList;
                                while (classList.length > 0) {
                                    classList.remove(classList.item(0));
                                }
                                el_icon.classList.add("tickmark_0_0")
                            }
                        }
                    }
                }
            }
       };
        FillTblRows();
    };  // function ResetFilterRows

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL SELECT EXAMYEAR OR DEPARTMENT  ++++++++++++++++++++
// functions are in table.js, except for MSED_Response

//=========  MSED_Response  ================ PR2020-12-18 PR2021-05-10
    function MSED_Response(new_setting) {
        console.log( "===== MSED_Response ========= ");
        console.log( "new_setting", new_setting);

// ---  upload new selected_pk
        new_setting.page = setting_dict.sel_page;
// also retrieve the tables that have been changed because of the change in examyear / dep
        const datalist_request = {
                setting: new_setting,
                student_rows: {get: true},
                studentsubject_rows: {get: true},
                grade_rows: {get: true},
                schemeitem_rows: {get: true},
                schoolsetting: {setting_key: "import_student"}
            };
        DatalistDownload(datalist_request);

    };  // MSED_Response


//###########################################################################
//=========  MSSSS_Response  ================ PR2021-01-23 PR2021-02-05 PR2021-07-26
    function MSSSS_Response(tblName, selected_dict, selected_pk) {
        //console.log( "===== MSSSS_Response ========= ");
        //console.log( "selected_pk", selected_pk);
        //console.log( "selected_code", selected_code);
        //console.log( "selected_name", selected_name);

// ---  upload new setting and refresh page
        const datalist_request = {
                setting: {page: "page_result",
                          sel_schoolbase_pk: selected_pk  },
                school_rows: {get: true},
                department_rows: {get: true},
                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},
                student_rows: {get: true},
                subject_rows: {get: true},
                studentsubject_rows: {get: true},
                scheme_rows: {cur_dep_only: true},
            };

        DatalistDownload(datalist_request);

    };  // MSSSS_Response

//=========  SBR_show_all  ================ PR2021-11-18
    function SBR_show_all(FillTblRows) {
        console.log("===== SBR_show_all =====");

        setting_dict.sel_lvlbase_pk = null;
        setting_dict.sel_level_abbrev = null;

        setting_dict.sel_sctbase_pk = null;
        setting_dict.sel_sector_abbrev = null;

        setting_dict.sel_classname = null;

        setting_dict.sel_student_pk = null;

        const el_SBR_select_department = document.getElementById("id_SBR_select_department");
        const el_SBR_select_level = document.getElementById("id_SBR_select_level");
        const el_SBR_select_sector = document.getElementById("id_SBR_select_sector");
        const el_SBR_select_class = document.getElementById("id_SBR_select_class");

        if (el_SBR_select_department){ el_SBR_select_department.value = null};
        if (el_SBR_select_level){ el_SBR_select_level.value = null};
        if (el_SBR_select_sector){ el_SBR_select_sector.value = null};
        if (el_SBR_select_class){ el_SBR_select_class.value = "0"};

// ---  upload new setting
        const selected_pk_dict = {};
        if (el_SBR_select_department){selected_pk_dict.sel_depbase_pk = null};
        if (el_SBR_select_level){selected_pk_dict.sel_lvlbase_pk = null};
        if (el_SBR_select_sector){selected_pk_dict.sel_sctbase_pk = null};
        if (el_SBR_select_class){selected_pk_dict.sel_classname = null};

        const new_setting = {page: "page_result", sel_lvlbase_pk: null, sel_sctbase_pk: null };
        const datalist_request = {
                setting: new_setting,
                student_rows: {cur_dep_only: true}
            };
        DatalistDownload(datalist_request, true); // true = skip_message

    };  // SBR_show_all


//========= get_recursive_integer_lookup  ========  PR2021-09-08
    function get_recursive_integer_lookup(tblRow) {
        // PR2021-09-08 debug: don't use b_get_mapdict_from_datarows with field 'mapid'.
        // It doesn't lookup mapid correctly: school_rows is sorted by id, therefore school_100 comes after school_99
        // instead b_recursive_integer_lookup with field 'id'.

// ---  lookup data_dict in data_rows, search by id
        const pk_int = get_attr_from_el_int(tblRow, "data-pk");
        const data_rows = (selected_btn === "btn_result") ? student_rows : null;
        const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);

        return found_dict;
    };  // get_recursive_integer_lookup



})  // document.addEventListener('DOMContentLoaded', function()