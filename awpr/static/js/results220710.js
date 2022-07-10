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
    let mod_MAG_dict = {};

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
    urls.url_grade_submit_ex5 = get_attr_from_el(el_data, "data-url_grade_submit_ex5");

    urls.url_send_email_verifcode = get_attr_from_el(el_data, "data-url_send_email_verifcode");

    urls.url_download_gradelist = get_attr_from_el(el_data, "data-url_download_gradelist");
    urls.url_download_pok = get_attr_from_el(el_data, "data-url_download_pok");

    urls.url_calc_results = get_attr_from_el(el_data, "data-url_calc_results");
    urls.url_get_auth = get_attr_from_el(el_data, "data-url_get_auth");
    urls.url_get_auth = get_attr_from_el(el_data, "data-url_get_auth");
    urls.url_result_download_ex5 = get_attr_from_el(el_data, "data-url_result_download_ex5");
    urls.url_result_download_overview = get_attr_from_el(el_data, "data-url_result_download_overview");
    urls.url_result_download_short_gradelist = get_attr_from_el(el_data, "data-url_result_download_short_gradelist");
    urls.url_change_birthcountry = get_attr_from_el(el_data, "data-url_change_birthcountry");

    // columns_hidden and columns_tobe_hidden are declared in tables.js, they are also used in t_MCOL_Open and t_MCOL_Save
    // columns_tobe_hidden contains the fields and captions that can be hidden
    // key 'all' contains fields that will be hidden in all buttons
    // key with btn name contains fields that will be hidden in this selected_btn
    // either 'all' or selected_btn are used in a page

    columns_tobe_hidden.btn_result = {
        idnumber: "ID_number", lvl_abbrev: "Leerweg", sct_abbrev: "Sector", classname: "Class",
        examnumber: "Examnumber", regnumber: "Regnumber", result_status: "Result", withdrawn: "Withdrawn", diplomanumber: "Diploma_number", gradelistnumber: "Gradelist_number"
    };

    columns_tobe_hidden.btn_overview = {
        idnumber: "ID_number", lvl_abbrev: "Leerweg", sct_abbrev: "Sector", classname: "Class",
        examnumber: "Examnumber", regnumber: "Regnumber", result_status: "Result", withdrawn: "Withdrawn"
    };
// --- get field_settings
    // declared as global: let field_settings = {};
    field_settings.student = {
        field_caption: ["", "Examnumber_twolines", "Name", "Leerweg", "Sector", "Class",  "Result", "Withdrawn_2lines", "Diplomanumber_2lines", "Gradelistnumber_2lines"],
        field_names: ["select", "examnumber", "fullname", "lvl_abbrev", "sct_abbrev", "classname", "result_status", "withdrawn", "diplomanumber", "gradelistnumber"],
        field_tags:["div", "div", "div", "div","div", "div", "div", "div", "input", "input"],

        filter_tags: ["select", "text", "text", "text" ,"text", "text", "text", "toggle", "text", "text"],
        field_width:  ["020", "120", "390", "090", "090", "090", "120", "090", "120", "120"],
        field_align: ["c", "l", "l", "l", "l", "l", "l", "c", "c", "c"]
        };

    field_settings.overview = {
        field_caption: ["", "", "", "", "",
                        "M", "V", "T", "M", "V", "T", "M", "V", "T", "M", "V", "T", "M", "V", "T", "M", "V", "T"],

        field_names: ["select", "db_code", "lvl_code", "sb_code", "sch_name",
                        "c_m", "c_v", "c_t",
                        "r_p_m", "r_p_v", "r_p_t",
                        "r_r_m", "r_r_v", "r_r_t",
                        "r_f_m", "r_f_v", "r_f_t",
                        "r_w_m", "r_w_v", "r_w_t",
                        "r_n_m", "r_n_v", "r_n_t"],
        field_tags: ["div", "div", "div", "div", "div", "div", "div", "div", "div", "div", "div", "div", "div", "div",
                    "div", "div", "div", "div", "div", "div", "div", "div", "div"],

        filter_tags: ["select", "text", "text", "text", "text", "text", "text", "text", "text", "text", "text", "text",
                    "text", "text", "text", "text", "text", "text", "text", "text", "text", "text", "text"],
        field_width:  ["020", "075", "075", "075", "180", "032", "032", "032", "032", "032", "032", "032", "032", "032", "032", "032", "032", "032", "032", "032", "032", "032", "032"],
        field_align: ["c", "c", "c", "c", "l", "c", "c", "c", "c", "c", "c", "c", "c", "c", "c", "c", "c", "c", "c","c", "c", "c", "c"]
    };
    field_settings.group_header = {
        field_caption: ["", "Department", "Level", "Code", "School",
                        "Total_candidates", "", "",
                        "Passed", "", "",
                        "Re_examination", "", "",
                        "Failed", "", "",
                        "Withdrawn_2lines", "", "",
                        "No_result", "", ""],
        field_names: ["select", "db_code", "lvl_code", "sb_code", "sch_name",
                        "count", "count", "count",
                        "pass", "pass", "pass",
                        "reex", "reex", "reex",
                        "fail", "fail", "fail",
                        "wdr", "wdr", "wdr",
                        "nores", "nores", "nores"],

        field_tags: ["div", "div", "div", "div", "div",
                        "div", "div", "div",
                        "div", "div", "div",
                        "div", "div", "div",
                        "div", "div", "div",
                        "div", "div", "div",
                        "div", "div", "div"],
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
                        "c", "c", "c",
                        "c", "c", "c",
                        "c", "c", "c",
                        "c", "c", "c",
                        "c", "c", "c",
                        "c", "c", "c"]
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
        const el_SBR_select_class = document.getElementById("id_SBR_select_class");
        if(el_SBR_select_class){
            el_SBR_select_class.addEventListener("click", function() {t_MSSSS_Open(loc, "class", classname_rows, true, setting_dict, permit_dict, MSSSS_Response)}, false)};

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
        };

// ---  MOD APPROVE GRADE ------------------------------------
        const el_mod_approve_grade = document.getElementById("id_mod_approve_grade");
        const el_MAG_header = document.getElementById("id_MAG_header");
        const el_MAG_select_container = document.getElementById("id_MAG_select_container");
            const el_MAG_subheader = document.getElementById("id_MAG_subheader");
            const el_MAG_examperiod = document.getElementById("id_MAG_examperiod");
            const el_MAG_examtype = document.getElementById("id_MAG_examtype");

        if (el_MAG_examtype){
            el_MAG_examtype.addEventListener("change", function() {MAG_ExamtypeChange(el_MAG_examtype)}, false );
        };

        const el_MAG_subj_lvl_cls_container = document.getElementById("id_MAG_subj_lvl_cls_container");
            const el_MAG_subject = document.getElementById("id_MAG_subject");
            const el_MAG_lvlbase = document.getElementById("id_MAG_lvlbase");
            const el_MAG_cluster = document.getElementById("id_MAG_cluster");

        const el_MAG_approved_by_label = document.getElementById("id_MAG_approved_by_label");
        const el_MAG_approved_by = document.getElementById("id_MAG_approved_by");
        const el_MAG_auth_index = document.getElementById("id_MAG_auth_index");
        if (el_MAG_auth_index){
            el_MAG_auth_index.addEventListener("change", function() {MAG_UploadAuthIndex(el_MAG_auth_index)}, false );
        };

        const el_MAG_loader = document.getElementById("id_MAG_loader");
        const el_MAG_msg_container = document.getElementById("id_MAG_msg_container");
        const el_MAG_info_container = document.getElementById("id_MAG_info_container");

        const el_MAG_input_verifcode = document.getElementById("id_MAG_input_verifcode");
        if (el_MAG_input_verifcode){
            el_MAG_input_verifcode.addEventListener("keyup", function() {MAG_InputVerifcode(el_MAG_input_verifcode, event.key)}, false);
            el_MAG_input_verifcode.addEventListener("change", function() {MAG_InputVerifcode(el_MAG_input_verifcode)}, false);
        };
        const el_MAG_btn_delete = document.getElementById("id_MAG_btn_delete");
        if (el_MAG_btn_delete){
            el_MAG_btn_delete.addEventListener("click", function() {MAG_Save("delete")}, false );  // true = reset
        };
        const el_MAG_btn_save = document.getElementById("id_MAG_btn_save");
        if (el_MAG_btn_save){
            el_MAG_btn_save.addEventListener("click", function() {MAG_Save("save")}, false );
        };
        const el_MAG_btn_cancel = document.getElementById("id_MAG_btn_cancel");

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

        const el_MGL_info_container = document.getElementById("id_MGL_info_container");
        const el_MGL_msg_info = document.getElementById("id_MGL_msg_info");

        const el_MGL_select_container = document.getElementById("id_MGL_select_container");
        const el_MGL_print_reex_container = document.getElementById("id_MGL_print_reex_container");

        const el_MGL_select_auth1 = document.getElementById("id_MGL_select_auth1");
        if(el_MGL_select_auth1){el_MGL_select_auth1.addEventListener("change", function() {MGL_Input(el_MGL_select_auth1)}) };
        const el_MGL_select_auth2 = document.getElementById("id_MGL_select_auth2");
        if(el_MGL_select_auth2){el_MGL_select_auth2.addEventListener("change", function() {MGL_Input(el_MGL_select_auth2)}) };

        const el_MGL_printdate = document.getElementById("id_MGL_printdate");
        if(el_MGL_printdate){el_MGL_printdate.addEventListener("change", function() {MGL_Input(el_MGL_printdate)}) };
        const el_MGL_printdate_label = document.getElementById("id_MGL_printdate_label");

        const el_MGL_print_reex = document.getElementById("id_MGL_print_reex");
        const el_MGL_msg_error = document.getElementById("id_MGL_msg_error");

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
                check_birthcountry_rows: {get: true}
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
                if ("check_birthcountry_msg_html" in response) {
                    ModConfirmOpen("check_birthcountry", response);
                    OpenLogfile("check_birthcountry", response.check_birthcountry_rows);
                };

                HandleBtnSelect(selected_btn, true)  // true = skip_upload
            },
            error: function (xhr, msg) {
// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                console.log(msg + '\n' + xhr.responseText);

                const msg_html = msg + "<br>" + xhr.responseText;
                b_show_mod_message_html(msg_html);

            }
        });
    }  // function DatalistDownload

//=========  CreateSubmenu  ===  PR2020-07-31
    function CreateSubmenu() {
        console.log("===  CreateSubmenu == ");
        //console.log("loc.Add_subject ", loc.Add_subject);
        console.log("permit_dict ", permit_dict);
        console.log("permit_dict.permit_calc_results ", permit_dict.permit_calc_results);

        const el_submenu = document.getElementById("id_submenu")

        if(permit_dict.permit_calc_results){
            AddSubmenuButton(el_submenu, loc.Calculate_results, function() {MGL_Open("calc_results")}, ["tab_show", "tab_btn_result"]);
        };
        if(permit_dict.requsr_same_school){
            AddSubmenuButton(el_submenu, loc.Preliminary_gradelist, function() {MGL_Open("prelim")}, ["tab_show", "tab_btn_result"]);
        };

        //AddSubmenuButton(el_submenu, loc.Download_short_gradelist, function() {ModConfirmOpen("short_gradelist")}, ["tab_show", "tab_btn_result"]);

        AddSubmenuButton(el_submenu, loc.Preliminary_ex5_form, function() {ModConfirmOpen("prelim_ex5")}, ["tab_show", "tab_btn_result"]);

        if (permit_dict.requsr_same_school && permit_dict.permit_submit_ex5){
            AddSubmenuButton(el_submenu, loc.Submit_Ex5, function() {MAG_Open("submit_ex5")}, ["tab_show", "tab_btn_result"]);
        };

        if(permit_dict.requsr_same_school && permit_dict.permit_submit_gl_dipl){
            AddSubmenuButton(el_submenu, loc.Final_gradelist, function() {MGL_Open("final")}, ["tab_show", "tab_btn_result"]);
            AddSubmenuButton(el_submenu, loc.Download_diploma, function() {MGL_Open("diploma")}, ["tab_show", "tab_btn_result"]);
            AddSubmenuButton(el_submenu, loc.Ex6_pok, function() {MGL_Open("pok")}, ["tab_show", "tab_btn_result"]);
        };

        AddSubmenuButton(el_submenu, loc.Download_result_overview, function() {ModConfirmOpen("overview")}, ["tab_show", "tab_btn_overview"]);
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
                    if([0, 1, 2, 3, 4, 5, 8, 11, 14, 17, 20, 23].includes(j)){


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
                        if(selected_btn === "btn_overview" && [5, 8, 11, 14, 17, 20, 23].includes(j)){
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
                    if(selected_btn === "btn_overview" && [5, 8, 11, 14, 17, 20, 23].includes(j)){
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
                if(selected_btn === "btn_overview" && [5, 8, 11, 14, 17, 20, 23].includes(j)){
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
        const field_tags = field_setting.field_tags;
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
                const field_tag = field_tags[j];
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
                if(selected_btn === "btn_overview" && [5, 8, 11, 14, 17, 20, 23].includes(j)){
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
                } else if (["diplomanumber", "gradelistnumber"].includes(field_name)){
                    td.addEventListener("change", function() {HandleInputChange(el)}, false)
                    el.classList.add("input_text");
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

                } else if (["diplomanumber", "gradelistnumber"].includes(field_name)){
                    filter_value = (fld_value) ? fld_value.toString().toLowerCase() : null;
                    // "NBSP (non-breaking space)" is necessary to show green box when field is empty
                    el_div.value = fld_value;

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


//========= HandleInputChange  =============== PR2022-06-19
    function HandleInputChange(el_input){
        //console.log(" --- HandleInputChange ---")
        // only used for "diplomanumber", "gradelistnumber"
        // may also change after submitting studsubject

// ---  get selected.data_dict
        const tblRow = t_get_tablerow_selected(el_input)
        const data_dict = get_datadict_from_tblRow(tblRow);
        //console.log("data_dict", data_dict)

        if (data_dict){
            const fldName = get_attr_from_el(el_input, "data-field")
            const old_value = data_dict[fldName];
            const has_permit = (permit_dict.permit_crud && permit_dict.requsr_same_school);

            if (!has_permit){
        // show message no permission
                b_show_mod_message_html(loc.No_permission);
        // put back old value  in el_input
                el_input.value = old_value;

            } else {
                const new_value = (el_input.value) ? el_input.value : null;

                if (new_value !== old_value){
                // must loose focus, otherwise green / red border won't show
                //el_input.blur();

            // ---  upload changes
                    const upload_dict = { table: data_dict.table,
                                           mode: "update",
                                           student_pk: data_dict.id,
                                           };
                    upload_dict[fldName] = new_value;
                    UploadChanges(upload_dict, urls.url_student_upload);
                };

            };  // if (!permit_dict.permit_crud)
        };
    };  // HandleInputChange

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
            const field_name = get_attr_from_el(el_input, "data-field");
            console.log( "pk_int", pk_int);
            console.log( "field_name", field_name);

            if (field_name === "withdrawn"){
    // --- get existing data_dict from data_rows
                const [index, found_dict, compare] = b_recursive_integer_lookup(student_rows, "id", pk_int);
                const data_dict = (!isEmpty(found_dict)) ? found_dict : null;

                const old_value = get_attr_from_el_int(el_input, "data-value");
                const full_name = (data_dict.fullname) ? data_dict.fullname : "---";
            console.log( "old_value", old_value, typeof old_value);
                const new_value = (!old_value);
            console.log( "new_value", new_value, typeof new_value);
                mod_dict = {
                    table: "student",
                    mode: "withdrawn",
                    student_pk: pk_int,
                    full_name: full_name,
                    withdrawn: new_value,
                    el_input: el_input,
                    data_dict: data_dict
                };
        // open mod confirm
                ModConfirmOpen("withdrawn");
            };
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

                    console.log("updated_student_rows in response", "updated_student_rows" in response);
                    if ("updated_student_rows" in response) {
                        const el_MSTUD_loader = document.getElementById("id_MSTUD_loader");
                        if(el_MSTUD_loader){ el_MSTUD_loader.classList.add(cls_visible_hide)};

                        const tblName = "student";
                    console.log("tblName" , tblName);
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
                        OpenLogfile("log_list", response.log_list, response.log_student_name);
                    }
                    if ("approve_msg_dict" in response) {
                        MAG_UpdateFromResponse (response);
                    };
                    if ( "approve_msg_html" in response){
                        MAG_UpdateFromResponse(response)
                    };

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
//=========   OpenLogfile   ====================== PR2021-11-20 PR2022-06-20
    function OpenLogfile(mode, log_list, log_student_name) {
        //console.log(" ========== OpenLogfile ===========");

        if (!!log_list && log_list.length) {
            const today = new Date();
            const this_month_index = 1 + today.getMonth();
            const date_str = today.getFullYear() + "-" + this_month_index + "-" + today.getDate();
            let file_name = "";
            if (mode === "check_birthcountry") {
                file_name = loc.Log_change_birth_country;
            } else if (mode === "log_list") {
                file_name = loc.Log_result_calculation;
                if (log_student_name) {
                    file_name += " " + log_student_name;
                };
            };
            const full_filename = ((file_name) ? file_name : "Log") + " dd " + get_now_formatted() + ".pdf";

            printPDFlogfile(log_list, full_filename )
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
        console.log(" --- RefreshDataRows  ---");
        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length

        console.log("tblName" , tblName);
        console.log("update_rows" , update_rows);
        console.log("data_rows" , data_rows);

        if (update_rows && update_rows.length ) {
            const field_setting = field_settings[tblName];
        console.log("field_setting" , field_setting);
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
        console.log(" --- RefreshDatarowItem  ---");
        console.log("tblName", tblName);
        console.log("update_dict", update_dict);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);

            let field_error_list = []
            const error_list = get_dict_value(update_dict, ["error"], []);
    console.log("error_list", error_list);

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
        console.log("pk_int", pk_int);
        console.log("data_dict", data_dict);

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
        console.log("updated_columns", updated_columns);

// ---  update fields in data_row
                        for (const [key, new_value] of Object.entries(update_dict)) {
                            if (key in data_dict){
                                if (new_value !== data_dict[key]) {
                                    data_dict[key] = new_value
                        }}};
        console.log("data_dict", data_dict);

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
//=========  MGL_Open  ================ PR2021-11-18 PR2021-12-28  PR2022-06-08
    function MGL_Open(mode) {
        console.log(" -----  MGL_Open   ----")
        // only called by menubtn Preliminary_gradelist and PrintGradelist and CalcResults
        mod_dict = {mode: mode}; // modes are "calc_results", "prelim", "final", "diploma"
        el_MGL_header.innerText = (mode === "calc_results") ? loc.Calculate_results :
                                    (mode === "prelim") ? loc.Preliminary_gradelist :
                                    (mode === "final") ? loc.Download_gradelist :
                                    (mode === "diploma") ? loc.Download_diploma :
                                    (mode === "pok") ? loc.Download_Ex6_pok :
                                    null;

        el_MGL_printdate_label.innerText = (
            (mode === "diploma") ? loc.Date_ofthe_diploma :
            (mode === "pok") ? loc.Print_date : loc.Date_ofthe_gradelist
        ) + ":" ;

// hide options
        add_or_remove_class(el_MGL_select_container, cls_hide, ["calc_results"].includes(mode))
        add_or_remove_class(el_MGL_print_reex_container, cls_hide, mode !== "prelim")

        let msg_html = null;
        let count_added_to_list = 0, count_selected = 0;
        let student_pk_list = [], print_all = false;

// --- count number of selected rows that are not hidden
        const rows = tblBody_datatable.querySelectorAll("tr:not(.display_hide).tsa_tr_selected");
        for (let i = 0, tr, el; tr = rows[i]; i++) {
            count_selected += 1;

            const pk_int = get_attr_from_el_int(tr, "data-pk");
            if(pk_int){

// --- get existing data_dict from data_rows
                // check if student has passed - only when printing diploma
                // check if student has not passed - only when downloading pok
                // when mode is not "diploma" has_passed = true
                const [index, data_dict, compare] = b_recursive_integer_lookup(student_rows, "id", pk_int);
                if (!isEmpty(data_dict)) {
                    const add_to_list = (mode === "diploma") ? data_dict.result === 1 :
                                        (mode === "pok") ? data_dict.result !== 1 : true;
                    if (add_to_list){
                        student_pk_list.push(pk_int);
                        count_added_to_list += 1;
                    };
                };
            };
        };

// download all visible rows if there are no selected rows that are not hidden:
        if (!count_selected){
            count_selected = 0;
            count_added_to_list = 0;

// --- count number of rows that are not hidden
            const elements = tblBody_datatable.querySelectorAll("tr:not(.display_hide)");
            for (let i = 0, tr, el; tr = elements[i]; i++) {
                count_selected += 1;
                const pk_int = get_attr_from_el_int(tr, "data-pk");
                if (pk_int) {

// --- get existing data_dict from data_rows
                    // check if student has passed - only when printing diploma
                    // check if student has not passed - only when downloading pok
                    // when mode is not "diploma" has_passed = true
                    const [index, data_dict, compare] = b_recursive_integer_lookup(student_rows, "id", pk_int);
                    if (!isEmpty(data_dict)) {
                        const add_to_list = (mode === "diploma") ? data_dict.result === 1 :
                                            (mode === "pok") ? data_dict.result !== 1 : true;
                        if (add_to_list){
                            student_pk_list.push(pk_int);
                            count_added_to_list += 1;
                        };
                    };
                };
            };
        };

// --- if all students of student_rows are in student_pk_list: set print_all = true, so you dont have to filter database on student_pk_list

        const student_rows_length = (student_rows) ? student_rows.length : 0;
        const student_pk_list_length = student_pk_list.length;
        if (student_pk_list_length === student_rows_length){
            print_all = true;
            student_pk_list = [];
            count_added_to_list = student_rows_length;
        }
        mod_dict.count_added_to_list = count_added_to_list;
        if(student_pk_list_length) {
            mod_dict.student_pk_list = student_pk_list;
        }
        mod_dict.print_all = print_all;

        console.log("mod_dict", mod_dict);

        const msg01_txt = (mode === "calc_results") ?
            loc.The_result_of
        : (mode === "prelim") ?
            loc.The_preliminary_gradelist_of
        : (mode === "final") ?
            loc.The_final_gradelist_of
        : (mode === "diploma") ?
            (student_pk_list_length > 1) ? loc.The_diplomas_of : loc.The_diploma_of
        : (mode === "pok") ?
            loc.The_pok_of
        : null;

        console.log("msg01_txt", msg01_txt);
        let msg02_txt = '';

        if (student_pk_list_length === 1) {
            const pk_int = student_pk_list[0];
            const [index, found_dict, compare] = b_recursive_integer_lookup(student_rows, "id", pk_int);
            const data_dict = (!isEmpty(found_dict)) ? found_dict : null;
            if (!isEmpty(data_dict)) {msg02_txt = (data_dict.fullname) ? data_dict.fullname : "---"};
        } else {
            msg02_txt = student_pk_list_length + loc.candidates;
        };

        if (mode === "calc_results"){
            msg_html = ["<div class='m-2'><p>", msg01_txt, "</p><ul class='mb-0'><li>", msg02_txt, "</li></ul><p>", loc.will_be_calculated,
                        "</p><p class='mt-2'>", loc.Logfile_with_details_willbe_downloaded, "</p></div>"
                        ].join("");

        } else  if (mode === "pok"){
            msg_html = ["<p>",
                            msg01_txt, " ",  msg02_txt, " ", loc.will_be_downloaded_sing , "</p>"
                          ].join("");
        } else {
            msg_html = ["<p>",
                            msg01_txt, " ",  msg02_txt, " ",
                            (student_pk_list_length === 1) ? loc.will_be_downloaded_sing : loc.will_be_downloaded_plur,
                             "</p>"
                          ].join("");
        }

        el_MGL_info_container.innerHTML = msg_html;

// hide autrh2 when pok
        add_or_remove_class(document.getElementById("id_MGL_auth2_container"), cls_hide, ["pok"].includes(mode))

        if (!["calc_results"].includes(mode)){
// ---  get auth and printdate info from server
            UploadChanges({ get: true}, urls.url_get_auth);
        };
// ---  disable save button
        el_MGL_btn_save.disabled = !["calc_results"].includes(mode);

// show loader
        add_or_remove_class(el_MGL_loader, cls_hide, ["calc_results"].includes(mode) )

// ---  show msg_info when printing final gardelist or diploma
        add_or_remove_class(el_MGL_msg_info, cls_hide, !["final", "diploma"].includes(mod_dict.mode));

        if (!["calc_results"].includes(mode)) {
            const selected_value = null;
            t_FillOptionsFromList(el_MGL_select_auth1, pres_secr_dict.auth1, "pk", "name",
                                        loc.Select_a_chairperson, loc.No_chairperson, selected_value);
            t_FillOptionsFromList(el_MGL_select_auth2, pres_secr_dict.auth2, "pk", "name",
                                        loc.Select_a_secretary, loc.No_secretary, selected_value);
        };

        $("#id_mod_gradelist").modal({backdrop: true});
    };  // MGL_Open

//=========  MGL_ResponseAuth  ================ PR2021-11-19 PR2021-12-28
    function MGL_ResponseAuth(pres_secr_dict) {
        console.log(" -----  MGL_ResponseAuth   ----")
        console.log("pres_secr_dict", pres_secr_dict)

// ---  enable save button
        const enabled = (!!mod_dict.count_added_to_list || !!mod_dict.print_all);
        el_MGL_btn_save.disabled = (!enabled);

// ---  hide loader
        add_or_remove_class(el_MGL_loader, cls_hide, true)

        const selected_value = null;
        t_FillOptionsFromList(el_MGL_select_auth1, pres_secr_dict.auth1, "pk", "name",
                                    loc.Select_a_chairperson, loc.No_chairperson, pres_secr_dict.sel_auth1_pk);
        t_FillOptionsFromList(el_MGL_select_auth2, pres_secr_dict.auth2, "pk", "name",
                                    loc.Select_a_secretary, loc.No_secretary, pres_secr_dict.sel_auth2_pk);
        el_MGL_printdate.value = (pres_secr_dict.printdate) ? pres_secr_dict.printdate : null;

    };  // MGL_ResponseAuth

//=========  MGL_Save  ================ PR2021-11-18 PR2022-06-08
    function MGL_Save() {
        console.log(" -----  MGL_Save   ----")
        const el_MGL_link = document.getElementById("id_MGL_link");

        if (mod_dict.mode === "calc_results"){
            Calc_result()
            $("#id_mod_gradelist").modal("hide");

        } else {
            const url_str = (mod_dict.mode === "pok") ? urls.url_download_pok : urls.url_download_gradelist
            const upload_dict = {
                mode: mod_dict.mode,
                now_arr: get_now_arr(),  // only for timestamp on filename
                print_all: mod_dict.print_all,
                print_reex: el_MGL_print_reex.checked
            };
            if (mod_dict.student_pk_list) { upload_dict.student_pk_list = mod_dict.student_pk_list};
            if (mod_dict.print_all) { upload_dict.print_all = mod_dict.print_all};

            if (Number(el_MGL_select_auth1.value)) { upload_dict.auth1_pk = Number(el_MGL_select_auth1.value)};
            if (Number(el_MGL_select_auth2.value)) { upload_dict.auth2_pk = Number(el_MGL_select_auth2.value)};
            if (el_MGL_printdate.value) { upload_dict.printdate = el_MGL_printdate.value};

            const may_save = (mod_dict.mode === "pok") ? (upload_dict.auth1_pk && upload_dict.printdate) :
                                (upload_dict.auth1_pk && upload_dict.auth2_pk && upload_dict.printdate);
            if (may_save){
                const href_str = JSON.stringify(upload_dict);
                const href = url_str.replace("-", href_str);

                el_MGL_link.href = href;
                el_MGL_link.click();
                $("#id_mod_gradelist").modal("hide");
            } else {
                el_MGL_msg_error.innerText = (mod_dict.mode === "pok") ? loc.mgl_error_noauth_pok : mgl_error_noauth;
                add_or_remove_class(el_MGL_msg_error, cls_hide, false);
                el_MGL_btn_save.disabled = true;
            };
        };

    };  // MGL_Save

//=========  MGL_Input  ================ PR2022-06-17
    function MGL_Input(el_input) {
        console.log(" -----  MGL_Input   ----")
        console.log("el_input", el_input)

// ---  enable save button
        el_MGL_btn_save.disabled = !el_input.value;
        add_or_remove_class(el_MGL_msg_error, cls_hide, el_input.value)
    };  // MGL_Input

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
    function ModConfirmOpen(mode, response) {
        console.log(" -----  ModConfirmOpen   ----")
        // values of mode are : "check_birthcountry", "prelim_ex5", "pok", "overview", "withdrawn"

        const tblName = "student";
        let show_modal = false;

// ---  get selected.student_dict
        // already done in HandleTblRowClicked

// ---  get info from data_map
        const map_dict = selected.student_dict;
    //console.log("map_dict", map_dict)

// ---  create mod_dict
        mod_dict.mode = mode;

// ---  put text in modal for
        let header_text = "";
        let msg_html = "";

        let msg01_txt = null, msg02_txt = null, msg03_txt = null;
        let hide_save_btn = false;

        if (mode === "check_birthcountry"){
            const may_edit = (permit_dict.permit_crud && permit_dict.requsr_same_school);
            console.log("may_edit", may_edit)
            if (may_edit){
                show_modal = true;

                add_or_remove_class(document.getElementById("id_mod_confirm_size"), "modal-md", true, "modal-lg");
                header_text = loc.Birthcountry_not_correct;
                msg_html = response.check_birthcountry_msg_html;

                const el_modconfirm_link = document.getElementById("id_modconfirm_link");
                if (el_modconfirm_link) {
                    const url_str = urls.url_result_download_overview;
                    el_modconfirm_link.setAttribute("href", url_str);
                };

                //"Click <a href='#' class='awp_href' onclick='LoadPage(&#39upload&#39)'>here</a> to go to its manual;</li>",
                //el_confirm_btn_cancel.innerText = (has_selected_item) ? loc.No_cancel : loc.Close;
                el_confirm_btn_save.innerText = loc.Yes_change;
                el_confirm_btn_cancel.innerText = loc.Cancel;
                add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", false, "btn-primary");
            };
        } else if(mode === "overview"){
            show_modal = true;

            header_text = loc.Download_result_overview;
            msg_html = ["<p>", loc.The_overview_of_results, " ", loc.will_be_downloaded_sing, "</p><p>"].join("");

            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            if (el_modconfirm_link) {
                const url_str = urls.url_result_download_overview;
                el_modconfirm_link.setAttribute("href", url_str);
            };

            el_confirm_btn_save.innerText = loc.OK;
            el_confirm_btn_cancel.innerText = loc.Cancel;
            add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", false, "btn-primary");

        } else if(mode === "short_gradelist"){
            show_modal = true;
            header_text = loc.Download_short_gradelist;
            msg_html = ["<p>", loc.The_short_gradelist, " ", loc.will_be_downloaded_sing, "</p><p>"].join("");

            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            if (el_modconfirm_link) {
                const url_str = urls.url_result_download_short_gradelist;
                el_modconfirm_link.setAttribute("href", url_str);
            };
        } else if(mode === "prelim_ex5"){
            show_modal = true;

            const has_selected_item = (!isEmpty(map_dict));

            //el_confirm_btn_cancel.innerText = (has_selected_item) ? loc.No_cancel : loc.Close;
            el_confirm_btn_save.innerText = loc.OK;
            el_confirm_btn_cancel.innerText = loc.Cancel;

            add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", false, "btn-primary");

            header_text = loc.Download_Ex_form;
            msg_html = ["<p>", loc.The_preliminary_ex5_form, " ", loc.will_be_downloaded_sing, "</p><p>", loc.Do_you_want_to_continue, "</p>"].join("");

            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            if (el_modconfirm_link) {
                const url_str = urls.url_result_download_ex5;
                el_modconfirm_link.setAttribute("href", url_str);
            };



        } else if(mode === "withdrawn"){
            const may_edit = (permit_dict.permit_crud && permit_dict.requsr_same_school);
            if (may_edit){
                show_modal = true;
                header_text = loc.Withdraw_candidate;
                if(mod_dict.withdrawn){
                    msg01_txt = loc.Candidate +  ":<br>&emsp;" + mod_dict.full_name + "<br>" + loc.will_be_withdrawn;
                } else {
                    msg01_txt = loc.Status_withdrawn_of + "<br>&emsp;" + mod_dict.full_name + "<br>" + loc.will_be_removed;
                };
                msg02_txt = loc.Do_you_want_to_continue;
            };

        } else if (mode === "pok"){
            show_modal = true;

            add_or_remove_class(document.getElementById("id_mod_confirm_size"), "modal-md", true, "modal-lg");

            header_text = loc.Birthcountry_not_correct;
            msg_html = response.check_birthcountry_msg_html;

            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            if (el_modconfirm_link) {
                const url_str = urls.url_result_download_overview;
                el_modconfirm_link.setAttribute("href", url_str);
            };

            //"Click <a href='#' class='awp_href' onclick='LoadPage(&#39upload&#39)'>here</a> to go to its manual;</li>",
            //el_confirm_btn_cancel.innerText = (has_selected_item) ? loc.No_cancel : loc.Close;
            el_confirm_btn_save.innerText = loc.Yes_change;
            el_confirm_btn_cancel.innerText = loc.Cancel;
            add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", false, "btn-primary");




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
// change size to 'large' when check_birthcountry
            // this code must come after $("#id_mod_confirm"), otherwise it will not work
            add_or_remove_class(document.getElementById("id_mod_confirm_size"), "modal-lg", (mode === "check_birthcountry"), "modal-md");
        };
    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2019-06-23
    function ModConfirmSave() {
        console.log(" --- ModConfirmSave --- ");
        console.log("mod_dict: ", mod_dict);

// ---  Upload Changes

        if (mod_dict.mode === "check_birthcountry"){
            const may_edit = (permit_dict.permit_crud && permit_dict.requsr_same_school);
            if(may_edit){
                const upload_dict = {
                        mode: mod_dict.mode,
                        table: "student"
                        };
                UploadChanges(upload_dict, urls.url_change_birthcountry);
            };
        } else if(["prelim_ex5", "short_gradelist", "overview"].includes(mod_dict.mode)){
            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            if (el_modconfirm_link) {
                el_modconfirm_link.click();
                   console.log("el_modconfirm_link", el_modconfirm_link)

            // show loader
                el_confirm_loader.classList.remove(cls_visible_hide)
            };
        } else if(mod_dict.mode === "withdrawn"){
            const may_edit = (permit_dict.permit_crud && permit_dict.requsr_same_school);
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


//========= MOD APPROVE GRADE ================ PR2022-06-12
    function MAG_Open (mode ) {
        console.log("===  MAG_Open  =====") ;
        console.log("mode", mode) ;

        b_clear_dict(mod_MAG_dict);

// --- check sel_examperiod
        let msg_html = null;
        if (![1,2,3].includes(setting_dict.sel_examperiod) ){
            msg_html = loc.Please_select_examperiod;
        // sel_examtype = "se", "pe", "ce", "reex", "reex03", "exem"
        } else if (mode === "approve"){
            // Ex5 has no approve mode
        } else if (mode === "submit_ex5") {

        //TODO make select btn exam period
            if (selected_btn === "btn_ep_01" || true){
                if (setting_dict.sel_examtype !== "ce") {
                    setting_dict.sel_examtype = "ce";
                    upload_examtype("ce");
                };
            } else if (selected_btn === "btn_reex"){
                if (setting_dict.sel_examtype !== "reex") {
                    setting_dict.sel_examtype = "reex";
                    upload_examtype("reex");
                };
            } else if (selected_btn === "btn_reex03"){
                if (setting_dict.sel_examtype !== "reex03") {
                    setting_dict.sel_examtype = "reex03";
                    upload_examtype("reex03");
                };
            } else{
                msg_html = loc.Please_select_examperiod;
            };

        };
        if (msg_html) {
            b_show_mod_message_html(msg_html);
        } else {


// PR2022-03-13 debug: also check on allowed subjects, levels and clusters

// put info in mod_MAG_dict
            // modes are 'approve' 'submit_test' 'submit_save'
            mod_MAG_dict.mode = mode;
            mod_MAG_dict.step = 0;

            mod_MAG_dict.auth_index = setting_dict.sel_auth_index;

            mod_MAG_dict.may_test = true;
            mod_MAG_dict.test_is_ok = false;
            mod_MAG_dict.submit_is_ok = false;
            mod_MAG_dict.is_reset = false;

// --- get list of auth_index of requsr
            const requsr_auth_list = [];
            if (permit_dict.usergroup_list.includes("auth1")){requsr_auth_list.push(1)};
            if (permit_dict.usergroup_list.includes("auth2")){requsr_auth_list.push(2)};
           // add examiner and commissiner only when mode = approve
            if (mod_MAG_dict.is_approve_mode){
                if (permit_dict.usergroup_list.includes("auth3")){requsr_auth_list.push(3)};
                if (permit_dict.usergroup_list.includes("auth4")){requsr_auth_list.push(4)};
            };
            console.log("requsr_auth_list", requsr_auth_list) ;

// get selected auth_index (user can be pres / secr and examiner at the same time)
            if (requsr_auth_list.length) {
                if(!setting_dict.sel_auth_index || !requsr_auth_list.includes(setting_dict.sel_auth_index)){
                    // when sel_auth_index is null or not in requsr_auth_list: make first item of requsr_auth_list the sel_auth_index
                    setting_dict.sel_auth_index = requsr_auth_list[0];
                };
            } else {
                // reset sel_auth_index when user has no auth
                setting_dict.sel_auth_index = null;
            };
            //console.log("setting_dict.sel_auth_index", setting_dict.sel_auth_index) ;

// get has_permit
            mod_MAG_dict.has_permit = (permit_dict.requsr_same_school && permit_dict.permit_submit_ex5);

            if (mod_MAG_dict.has_permit && mod_MAG_dict.auth_index){

// --- get header_txt and subheader_txt
                const header_txt = loc.Submit_Ex5_form
                el_MAG_header.innerText = header_txt;
                const subheader_txt = loc.MAG_ex5_info.subheader_submit_ex5;
                el_MAG_subheader.innerText = subheader_txt;

// --- get examperiod and examtype text
                // sel_examperiod 4 shows "Vrijstelling" as examperiod, replace by "Eerste tijdvak"
                // sel_examperiod 12 shows "Eerste tijdvak / Tweede tijdvak" replace by "---"
                // replace by First period
                el_MAG_examperiod.innerText = (setting_dict.sel_examperiod === 3) ? loc.examperiod_caption[3] :
                                (setting_dict.sel_examperiod === 2) ? loc.examperiod_caption[2] :
                                ([1, 4].includes(setting_dict.sel_examperiod)) ? loc.examperiod_caption[1] : "---"

// --- hide select examperiod when downloadfing Ex5
                add_or_remove_class(el_MAG_examperiod.parentNode, cls_hide, mode === "submit_ex5");

// --- fill selectbox examtype
                if (el_MAG_examtype){
                    const examtype_list = []
                    if (setting_dict.sel_examperiod === 1){
                        examtype_list.push({value: 'ce', caption: loc.examtype_caption.ce})
                    } else if (setting_dict.sel_examperiod === 2){
                        examtype_list.push({value: 'reex', caption: loc.examtype_caption.reex})
                    } else if (setting_dict.sel_examperiod === 3){
                        examtype_list.push({value: 'reex03', caption: loc.examtype_caption.reex03})
                    };
                    t_FillOptionsFromList(el_MAG_examtype, examtype_list, "value", "caption",
                        loc.Select_examtype, loc.No_examtypes_found, setting_dict.sel_examtype);
                };


// --- hide select examtype, subject and cluster
                add_or_remove_class(el_MAG_examtype.parentNode, cls_hide, true);
                add_or_remove_class(el_MAG_subject.parentNode, cls_hide, true);
                add_or_remove_class(el_MAG_cluster.parentNode, cls_hide, true);

// --- show level visible if sel_dep_level_req, MPC must be able to submit per level
                const show_subj_lvl_cls_container = setting_dict.sel_dep_level_req;
                add_or_remove_class(el_MAG_subj_lvl_cls_container, cls_hide, !show_subj_lvl_cls_container);

                const level_abbrev = (setting_dict.sel_lvlbase_pk) ? setting_dict.sel_level_abbrev : "<" + loc.All_levels + ">";
                el_MAG_lvlbase.innerText = level_abbrev;

// --- get approved_by
                if (el_MAG_approved_by_label){
                    el_MAG_approved_by_label.innerText = loc.Submitted_by + ":"
                }
                if (el_MAG_approved_by){
                    el_MAG_approved_by.innerText = permit_dict.requsr_name;
                }

// --- fill selectbox auth_index
                if (el_MAG_auth_index){
                    // auth_list = [{value: 1, caption: 'Chairperson'}, {value: 3, caption: 'Examiner'} )
                    const auth_list = [];
                    const cpt_list = [null, loc.Chairperson, loc.Secretary, loc.Examiner, loc.Corrector];
                    for (let i = 0, auth_index; auth_index = requsr_auth_list[i]; i++) {

            console.log("auth_index", auth_index, typeof auth_index) ;
            console.log("requsr_auth_list[i]", requsr_auth_list[i], typeof requsr_auth_list[i]) ;
            console.log("loc.Secretary", loc.Secretary) ;
                        auth_list.push({value: auth_index, caption: cpt_list[auth_index]});
                    };
                    t_FillOptionsFromList(el_MAG_auth_index, auth_list, "value", "caption",
                        loc.Select_function, loc.No_functions_found, setting_dict.sel_auth_index);
                };

// --- reset ok button
                MAG_SetMsgContainer()
                MAG_SetInfoContainer();
                MAG_SetBtnSaveDeleteCancel();

// --- open modal
                $("#id_mod_approve_grade").modal({backdrop: true});
            };  // if (permit_dict.permit_approve_grade || permit_dict.permit_submit_grade)
         };
    };  // MAG_Open

//=========  MAG_Save  ================
    function MAG_Save (save_mode) {
        console.log("===  MAG_Save  =====") ;
        // save_mode = 'save''

        if (permit_dict.permit_submit_ex5) {
    console.log("mod_MAG_dict.step", mod_MAG_dict.step)

            //  upload_modes are: 'approve_test', 'approve_save', 'approve_reset', 'submit_test', 'submit_save'
            const upload_dict = {
                table: "result",
                form: "ex5",
                auth_index: mod_MAG_dict.auth_index,
                now_arr: get_now_arr()  // only for timestamp on filename saved Ex-form
                };

            let url_str = null;
            if (mod_MAG_dict.step === 1 && mod_MAG_dict.test_is_ok){
                url_str = urls.url_send_email_verifcode;
            } else {
                url_str = urls.url_grade_submit_ex5;

                if (mod_MAG_dict.test_is_ok){
                    upload_dict.mode = "submit_save";

                    upload_dict.verificationcode = el_MAG_input_verifcode.value
                    upload_dict.verificationkey = mod_MAG_dict.verificationkey;
                } else {
                    upload_dict.mode = "submit_test";
                };
            };


    // ---  show loader
            add_or_remove_class(el_MAG_loader, cls_hide, false)

    // ---  disable select auth_index after clicking save button
            if (el_MAG_auth_index){
                el_MAG_auth_index.disabled = true;
            };

    // ---  hide info box and msg box and input verifcode
            add_or_remove_class(el_MAG_msg_container, cls_hide, true);
            add_or_remove_class(el_MAG_info_container, cls_hide, true);
            add_or_remove_class(el_MAG_input_verifcode.parentNode, cls_hide, true);

    // ---  hide delete btn
            add_or_remove_class(el_MAG_btn_delete, cls_hide, true);

    console.log("upload_dict", upload_dict);

            UploadChanges(upload_dict, url_str);
// hide modal when clicked on save btn when test_is_ok
            if (mod_MAG_dict.test_is_ok){
                //$("#id_mod_approve_grade").modal("hide");
            };
            MAG_SetBtnSaveDeleteCancel();

        }  // if (permit_dict.permit_approve_grade || permit_dict.permit_submit_grade)
    };  // MAG_Save

//=========  MAG_ExamtypeChange  ================ PR2022-05-29
    function MAG_ExamtypeChange (el_select) {
        console.log("===  MAG_ExamtypeChange  =====") ;
        console.log("el_select.value", el_select.value) ;

// ---  put new  auth_index in mod_MAG_dict and setting_dict
        mod_MAG_dict.sel_examtype = el_select.value;
        setting_dict.sel_examtype = el_select.value;

// ---  upload new setting
        const upload_dict = {selected_pk: {sel_examtype: setting_dict.sel_examtype}};
        console.log("upload_dict", upload_dict) ;
        b_UploadSettings (upload_dict, urls.url_usersetting_upload);

    }; // MAG_ExamtypeChange

//=========  MAG_UploadAuthIndex  ================ PR2022-03-13
    function MAG_UploadAuthIndex (el_select) {
        //console.log("===  MAG_UploadAuthIndex  =====") ;

// ---  put new  auth_index in mod_MAG_dict and setting_dict
        mod_MAG_dict.auth_index = (Number(el_select.value)) ? Number(el_select.value) : null;
        setting_dict.sel_auth_index = mod_MAG_dict.auth_index;
        setting_dict.sel_auth_function = b_get_function_of_auth_index(loc, mod_MAG_dict.auth_index);
        //console.log( "setting_dict.sel_auth_function: ", setting_dict.sel_auth_function);

// ---  upload new setting
        const upload_dict = {selected_pk: {sel_auth_index: setting_dict.sel_auth_index}};
        b_UploadSettings (upload_dict, urls.url_usersetting_upload);

    }; // MAG_UploadAuthIndex

//=========  MAG_UpdateFromResponse  ================ PR2021-02-08 PR2022-04-18
    function MAG_UpdateFromResponse (response) {
        console.log("===  MAG_UpdateFromResponse  =====") ;
        if (!isEmpty(response)){
            mod_MAG_dict.step += 1;
            console.log("mod_MAG_dict.step", mod_MAG_dict.step) ;

            mod_MAG_dict.verification_is_ok = !!response.verification_is_ok;
            mod_MAG_dict.verificationkey = (mod_MAG_dict.verification_is_ok) ? response.verificationkey : null;

    // create message in el_MAG_msg_container
            MAG_SetMsgContainer(response);
            MAG_SetInfoContainer();
    // hide ok button when not mod_MAG_dict.test_is_ok
            MAG_SetBtnSaveDeleteCancel();
    // hide modal after submitting, only when is_approve_mode
            if(mod_MAG_dict.step === 2 && mod_MAG_dict.is_approve_mode){
                $("#id_mod_approve_grade").modal("hide");
            };
        };
    };  // MAG_UpdateFromResponse

//=========  MAG_SetMsgContainer  ================ PR2021-02-08 PR2022-04-17
     function MAG_SetMsgContainer(response) {
        console.log("===  MAG_SetMsgContainer  =====") ;
        console.log("response", response);

// --- show info and hide loader
        add_or_remove_class(el_MAG_loader, cls_hide, true);

        el_MAG_msg_container.innerHTML = null;
        let show_msg_container = false;

        // response is undefined when opening modal

        const show_input_verifcode = (response && !!response.approve_msg_html);
        add_or_remove_class(el_MAG_input_verifcode.parentNode, cls_hide, !show_input_verifcode);

    console.log("mod_MAG_dict.step", mod_MAG_dict.step);
    console.log("show_input_verifcode.step", show_input_verifcode);

        if (show_input_verifcode){
            show_msg_container = true;

            mod_MAG_dict.verificationkey = response.verificationkey

            el_MAG_msg_container.className = "mt-2";
            el_MAG_msg_container.innerHTML = response.approve_msg_html

            if (show_input_verifcode){set_focus_on_el_with_timeout(el_MAG_input_verifcode, 150)};

        } else if (!response){
            if (mod_MAG_dict.mode === "submit_ex2a" && !mod_MAG_dict.step){
                el_MAG_msg_container.className = "mt-2 p-2 border_bg_warning";
                el_MAG_msg_container.innerHTML = loc.MAG_ex5_info.subheader_submit_ex2a_2 + " " + loc.MAG_ex5_info.subheader_submit_ex2a_3;
                show_msg_container = true;
            };

        } else if (response && !isEmpty(response.approve_msg_dict)){

            const msg_dict = response.approve_msg_dict;
            console.log("msg_dict", msg_dict);
            console.log("response.test_is_ok", response.test_is_ok);

            console.log("response.approve_msg_html", response.approve_msg_html);
            console.log("response.approve_msg_dict", response.approve_msg_dict);

            //console.log("mod_MAG_dict", mod_MAG_dict);

            const test_is_ok = (!!response.test_is_ok)

    // ---  hide loader
            add_or_remove_class(el_MAG_loader, cls_hide, true);
            let msg01_txt = null,  msg02_txt = null, msg03_txt = null, msg_04_txt = null;

    // make message container green when grades can be published, red otherwise
            // msg_dict.saved > 0 when grades are approved or published

            mod_MAG_dict.may_test = false;
            mod_MAG_dict.test_is_ok = !!response.test_is_ok;
            mod_MAG_dict.has_already_approved = (msg_dict && !!msg_dict.already_approved)
            mod_MAG_dict.has_already_published = (msg_dict && !!msg_dict.already_published)
            mod_MAG_dict.has_saved = msg_dict && !!msg_dict.saved;
            mod_MAG_dict.submit_is_ok = msg_dict && !!msg_dict.now_saved;  // submit_is_ok when records are saved

            show_msg_container = true
           // const border_class = (mod_MAG_dict.test_is_ok) ? "border_bg_valid" : "border_bg_invalid";
            //console.log("mod_MAG_dict.test_is_ok", mod_MAG_dict.test_is_ok) ;
            //const bg_class = (mod_MAG_dict.test_is_ok) ? "border_bg_valid" : "border_bg_invalid" // "border_bg_message"
            //el_MAG_msg_container.className = bg_class
            let bg_class_ok = (mod_MAG_dict.test_is_ok || mod_MAG_dict.has_saved );
            const bg_class = (!bg_class_ok) ? "border_bg_invalid" : (msg_dict.warning) ? "border_bg_warning" : "border_bg_valid";

        console.log("bg_class", bg_class) ;
            el_MAG_msg_container.className = "mt-2 p-2 " + bg_class;

    // create message in container
            const array = ['count_text', 'no_value_text', 'skip_text', 'already_published_text', 'auth_missing_text',
                'double_approved_text', 'already_approved_text', 'saved_text', 'saved_text2']
            for (let i = 0, el, key; key = array[i]; i++) {
                if(key in msg_dict) {
        //console.log("key", key) ;
        //console.log("msg_dict[key]", msg_dict[key]) ;
                    el = document.createElement("p");
                    el.innerHTML = msg_dict[key];
                    if (key === "count_text") {
                    } else if (key === "saved_text") {
                        el.classList.add("pt-2");
                    } else if (key === "saved_text2") {
                        el.classList.add("pt-0");
                    } else if (key === "skip_text") {
                        el.classList.add("pt-2");
                    } else {
                        el.classList.add("pl-4");
                    };
                    el_MAG_msg_container.appendChild(el);
                };
            };
            if(msg_dict.file_name) {
                const el = document.createElement("p");
                el.innerHTML = msg_dict.file_name;
                el_MAG_msg_container.appendChild(el);
            };

            if(msg_dict.warning) {
                const el = document.createElement("div");
                el.innerHTML = msg_dict.warning;
                el_MAG_msg_container.appendChild(el);
            };

           // msg01_txt = "The selection contains " + msg_dict.count + " grades."
           // if (msg_dict.no_value){msg02_txt = " -  " + msg_dict.no_value + " grades have no value. They will be skipped."}
           // if (msg_dict.auth_missing){msg03_txt = " -  " + msg_dict.auth_missing + " grades are not completely authorized. They will be skipped"}
            //if (msg_dict.already_published){msg03_txt = " -  " + msg_dict.already_published + " grades are already submitted.They will be skipped."}
        };

        add_or_remove_class(el_MAG_msg_container, cls_hide, !show_msg_container)
    };  // MAG_SetMsgContainer

//=========  MAG_SetInfoContainer  ================ PR2022-04-17
     function MAG_SetInfoContainer() {
        console.log("===  MAG_SetInfoContainer  =====") ;
        console.log("mod_MAG_dict.step", mod_MAG_dict.step) ;
        console.log("mod_MAG_dict.test_is_ok", mod_MAG_dict.test_is_ok) ;

        el_MAG_info_container.innerHTML = null;

// put info text in el_MAG_info_container, only on open modal
        // el_MAG_info_container contains: 'Klik op 'Cijfers controleren' om de cijfers te controleren voordat ze worden ingediend.
        // only visible on open modal
        // Klik op 'Verificatiecode aanvragen', dan sturen we je een e-mail met de verificatiecode. De verificatiecode blijft 30 minuten geldig.

        let inner_html = "";
        if (mod_MAG_dict.step === 0) {
            // step 0: when form opens
            const ex2_key = ( ["se", "sr"].includes(setting_dict.sel_examtype) ) ? "ex2" :
                            ( ["pe", "ce"].includes(setting_dict.sel_examtype) ) ? "ex2a" : "ex2";
        console.log("ex2_key", ex2_key) ;
            const keys = ["submit_0", "submit_1"];
            for (let i = 0, el, key; key = keys[i]; i++) {
                inner_html += "<div><small>" + loc.MAG_ex5_info[key] + "</div></small>";
            }
        } else if (mod_MAG_dict.step === 1) {
            if(mod_MAG_dict.is_submit_ex2_mode || mod_MAG_dict.is_submit_ex2a_mode){
                if(mod_MAG_dict.test_is_ok){
                    inner_html = ["<div class='py-0'><small>", loc.MAG_ex5_info.verif_01,
                                "<br>", loc.MAG_ex5_info.verif_02,
                                "<br>", loc.MAG_ex5_info.verif_03,
                                "</small></div>"].join("");
                };
            };
        };
        add_or_remove_class(el_MAG_info_container, cls_hide, !inner_html)
        el_MAG_info_container.innerHTML = inner_html
    };  // MAG_SetInfoContainer

//=========  MAG_SetBtnSaveDeleteCancel  ================ PR2021-02-08
     function MAG_SetBtnSaveDeleteCancel() {
        console.log("===  MAG_SetBtnSaveDeleteCancel  =====") ;


        const step = mod_MAG_dict.step;
        const may_test = mod_MAG_dict.may_test;
        const test_is_ok = mod_MAG_dict.test_is_ok;
        const submit_is_ok = mod_MAG_dict.submit_is_ok;

        const has_already_approved = !!mod_MAG_dict.has_already_approved;
        const has_already_published = !!mod_MAG_dict.has_already_published;
        const has_saved = !!mod_MAG_dict.has_saved;

    console.log("mod_MAG_dict.step", mod_MAG_dict.step) ;
    console.log("may_test", may_test) ;
    console.log("test_is_ok", test_is_ok) ;
    console.log("submit_is_ok", submit_is_ok) ;

// ---  hide save button when not can_publish
        // may_test = true when opening modal, gets false when not isEmpty(response.approve_msg_dict))
        const show_save_btn = (may_test || test_is_ok);


        let save_btn_txt = loc.Check_grades;
        if (step === 0) {
            // step 0: opening modal
            save_btn_txt = loc.Check_grades;
        } else if (step === 1) {
        // step 1 + response : return after check
            if (test_is_ok){
                save_btn_txt = loc.Request_verifcode;
            };
        } else if (step === 2) {
            if (test_is_ok){
                save_btn_txt = loc.Submit_Ex5_form;
            }
        }

    console.log("vvvvvvvvvvvvvvv step", step) ;
    console.log("test_is_ok", test_is_ok) ;
    console.log("save_btn_txt", save_btn_txt) ;

        el_MAG_btn_save.innerText = save_btn_txt;
        add_or_remove_class(el_MAG_btn_save, cls_hide, !show_save_btn);

        let btn_cancel_text = (submit_is_ok || (!may_test && !test_is_ok) || (!submit_is_ok)) ? loc.Close : loc.Cancel;
        el_MAG_btn_cancel.innerText = btn_cancel_text;

// ---  show only the elements that are used in this tab
        let show_class = "tab_step_" + step;

        b_show_hide_selected_elements_byClass("tab_show", show_class, el_mod_approve_grade);

// ---  hide delete btn
        add_or_remove_class(el_MAG_btn_delete, cls_hide, true);

     } //  MAG_SetBtnSaveDeleteCancel

//=========  MAG_InputVerifcode  ================ PR2022-04-18
     function MAG_InputVerifcode(el_input, event_key) {
        console.log("===  MAG_InputVerifcode  =====") ;

        if(event_key && event_key === "Enter"){

        }
        // enable save btn when el_input has value
        const disable_save_btn = !el_input.value;
        //console.log("disable_save_btn", disable_save_btn) ;
        el_MAG_btn_save.disabled = disable_save_btn;

        if(!disable_save_btn && event_key && event_key === "Enter"){
            MAG_Save("save")
        }
     };  // MAG_InputVerifcode

//=========  upload_examtype  ================ PR2022-06-12
    function upload_examtype(new_examtype) {
        console.log("----- upload_examtype -----");

        // sel_examtype = "se", "pe", "ce", "reex", "reex03", "exem"
        setting_dict.sel_examtype = new_examtype;

// - not necessary, but to be on the safe side:
        setting_dict.sel_examperiod = (setting_dict.sel_examtype === "reex03") ? 3 :
                           (setting_dict.sel_examtype === "reex") ? 2 :
                           (setting_dict.sel_examtype === "reex") ? 2 :
                           (setting_dict.sel_examtype && ["se", "sr", "pe", "ce"].includes(setting_dict.sel_examtype) ) ? 1 :
                           setting_dict.sel_examperiod;

// ---  upload new setting
        const upload_dict = {selected_pk: {sel_examtype: setting_dict.sel_examtype,
                                         sel_examperiod: setting_dict.sel_examperiod}};
        console.log( "upload_dict: ", upload_dict);

        b_UploadSettings (upload_dict, urls.url_usersetting_upload);

        //PR2022-05-23 dont show SBR_examtype
        //FillOptionsExamtype();
        FillTblRows();
    }  // upload_examtype


/////////////////////////////////////////////


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

// --- reset table
        tblBody_datatable.innerText = null;

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

// --- reset table
        tblBody_datatable.innerText = null;

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


//========= get_datadict_from_tblRow ============= PR2022-06-19
    function get_datadict_from_tblRow(tblRow) {
        //console.log( " ==== get_datadict_from_tblRow ====");
        //console.log( "tblRow", tblRow);

// get student_pk and studsubj_pk from tr_clicked.id
        const pk_int = get_attr_from_el_int(tblRow, "data-pk");
        const [middle_index, found_dict, compare] = b_recursive_integer_lookup(student_rows, "id", pk_int);
        const data_dict = (!isEmpty(found_dict)) ? found_dict : null;

        return data_dict;
    }  //  get_datadict_from_tblRow

})  // document.addEventListener('DOMContentLoaded', function()