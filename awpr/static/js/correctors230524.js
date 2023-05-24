// PR2020-07-30 added

// PR2021-09-22  these variables are declared in base.js to make them global variables
// declared as global: let selected_btn = null;
//let setting_dict = {};
//let permit_dict = {};
//let loc = {};
//let urls = {};
//const field_settings = {};  // PR2023-04-20 made global

const corrector_dicts = {}; //PR2023-03-26
const usercompensation_dicts = {}; //PR2023-02-24
const usercomp_agg_dicts = {}; //PR2023-02-24

document.addEventListener('DOMContentLoaded', function() {
    "use strict";

    let el_loader = document.getElementById("id_loader");

// ---  get permits
    // permit dict gets value after downloading permit_list PR2021-03-27
    //  if user has no permit to view this page ( {% if no_access %} ): el_loader does not exist PR2020-10-02

    // Note: may_view_page is the only permit that gets its value on DOMContentLoaded,
    // all other permits get their value in function get_permits, after downloading permit_list
    const may_view_page = (!!el_loader)


    let mod_dict = {};
    const mod_MCH_dict = {};
    const mod_MSM_dict = {};

    let time_stamp = null; // used in mod add user

// ---  id of selected customer and selected order
    let selected_user_pk = null;

    let selected_userpermit_pk = null;
    let selected_period = {};

    let examyear_map = new Map();
    let department_map = new Map();
    let permit_map = new Map();

    //let filter_dict = {};
    let filter_mod_employee = false;

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    urls.url_usersetting_upload = get_attr_from_el(el_data, "data-url_usersetting_upload");
    urls.url_userallowedcluster_upload = get_attr_from_el(el_data, "data-url_userallowedcluster_upload");

    urls.url_usercompensation_upload = get_attr_from_el(el_data, "data-url_usercompensation_upload");
    urls.url_usercomp_approve_single = get_attr_from_el(el_data, "data-url_usercomp_approve_single");
    urls.url_usercomp_approve_submit = get_attr_from_el(el_data, "data-url_usercomp_approve_submit");

    mod_MCOL_dict.columns.all = {
        user_sb_code: "Organization", last_name: "Name",
        uc_depbase_code: "Department", uc_lvlbase_code: "Learning_path",
        subj_name_nl:  "Subject", exam_version: "Version",
        uc_amount: "Number_approvals", uc_meetings: "Number_meetings"
    };
    mod_MCOL_dict.columns.btn_usercompensation = {sb_code: "School_code", uc_school_abbrev: "School"};
    mod_MCOL_dict.columns.btn_usercomp_agg = { compensation: "Compensation"};


// --- get field_settings
    field_settings.btn_correctors = {
                    field_caption: ["", "Name", "Allowed_departments",
                                    "Allowed_levels", "Allowed_subjects", "Allowed_clusters"],
                    field_names: ["select", "last_name","allowed_depbases",
                                    "allowed_lvlbases", "allowed_subjbases", "allowed_clusters"],
                    field_tags: ["div", "div", "div", "div", "div", "div", "div"],
                    filter_tags: ["select", "text", "text", "text", "text", "text"],
                    field_width:  ["032", "180", "180", "180", "180", "180"],
                    field_align: ["c", "l", "l", "l", "l",  "l", "l", "l"]};

    field_settings.btn_usercompensation = {
                    field_caption: ["", "Organization_twolines", "Name",
                                    "Department", "Learning_path", "Subjectcode_2lines", "Subject", "Version", "Exam_period",
                                    "School_code", "School", "Number_approvals_2lines",  "Number_meetings_2lines",  "",
                                    "Correction_approvals_2lines",  "Correction_meetings_2lines","Compensation_2lines"],
                    field_names: ["select",  "user_sb_code", "last_name",
                                    "uc_depbase_code", "uc_lvlbase_code", "subjbase_code", "subj_name_nl", "exam_version", "examperiod",
                                     "sb_code", "uc_school_abbrev", "uc_amount", "uc_meetings", "status", "uc_corr_amount", "uc_corr_meetings", "uc_compensation"],
                    field_tags: ["div", "div", "div",
                                    "div", "div", "div", "div", "div", "div",
                                     "div", "div","div", "div", "div", "input", "input", "div"],
                    filter_tags: ["select", "text",  "text",
                                    "text", "text",  "text",  "text", "text", "text",
                                     "text",  "text", "number",  "number", "status", "number",  "number", "number"],
                    field_width:  ["020", "090",  "180",
                                    "075", "075", "075", "220", "090",  "090",
                                    "090", "150", "090",  "090", "032", "090",  "090", "090"],
                    field_align: ["c",  "l", "l",
                                    "c", "c", "c", "l",  "l", "c",
                                    "l", "l", "c",  "c", "c", "c", "c", "c"]};

    field_settings.btn_usercomp_agg = {
                    field_caption: ["", "Organization_twolines", "Name",
                                    "Department", "Learning_path", "Subjectcode_2lines", "Subject", "Version", "Exam_period",
                                    "Number_approvals_2lines",  "Number_meetings_2lines", "Compensation_2lines"],
                    field_names: ["select", "user_sb_code", "last_name",
                                    "depbase_code", "lvlbase_code", "subjbase_code", "subj_name_nl", "exam_version", "examperiod",
                                    "uc_amount", "uc_meetings", "uc_compensation"],
                    field_tags: ["div", "div",  "div",
                                    "div", "div", "div", "div", "div", "div",
                                    "div", "div","div"],
                    filter_tags: ["select", "text",  "text",
                                    "text", "text",  "text",  "text", "text", "text",
                                    "text",  "toggle", "text"],
                    field_width:  ["020", "090",  "180",
                                    "090", "090", "090", "220", "090",  "090",
                                    "150",  "150", "150"],
                    field_align: ["c", "l",  "l",
                                    "c", "c", "c", "l",  "l", "c",
                                        "c",  "c", "c"]};

    const tblHead_datatable = document.getElementById("id_tblHead_datatable");
    const tblBody_datatable = document.getElementById("id_tblBody_datatable");

// === EVENT HANDLERS ===
// === reset filter when ckicked on Escape button ===
        document.addEventListener("keydown", function (event) {
             if (event.key === "Escape") { ResetFilterRows()}
        });

 // freeze table header PR2022-01-19
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

// --- BUTTON CONTAINER ------------------------------------
        const el_btn_container = document.getElementById("id_btn_container");
        if (el_btn_container){
            const btns = el_btn_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                const data_btn = get_attr_from_el(btn,"data-btn")
                btn.addEventListener("click", function() {HandleBtnSelect(data_btn)}, false )
            };
        };

// ---  HEADER BAR ------------------------------------
        const el_hdrbar_examyear = document.getElementById("id_hdrbar_examyear");
        if (el_hdrbar_examyear){
            el_hdrbar_examyear.addEventListener("click",
                function() {t_MSED_Open(loc, "examyear", examyear_map, setting_dict, permit_dict, MSED_Response)}, false );
        };
        const el_hdrbar_department = document.getElementById("id_hdrbar_department");
        if (el_hdrbar_department){
            el_hdrbar_department.addEventListener("click",
                function() {t_MSED_Open(loc, "department", department_map, setting_dict, permit_dict, MSED_Response)}, false );
        };
        const el_hdrbar_school = document.getElementById("id_hdrbar_school");
        if (el_hdrbar_school){
            el_hdrbar_school.addEventListener("click",
                function() {t_MSSSS_Open(loc, "school", school_rows, false, false, setting_dict, permit_dict, MSSSS_Response)}, false );
        };

        const el_hdrbar_allowed_sections = document.getElementById("id_hdrbar_allowed_sections");
        if (el_hdrbar_allowed_sections){
            el_hdrbar_allowed_sections.addEventListener("click", function() {t_MUPS_Open()}, false );
        };

// ---  MODAL SELECT COLUMNS ------------------------------------
        const el_MCOL_btn_save = document.getElementById("id_MCOL_btn_save")
        if(el_MCOL_btn_save){
            el_MCOL_btn_save.addEventListener("click", function() {
                t_MCOL_Save(urls.url_usersetting_upload, HandleBtnSelect)}, false )
        };

 // ---  MODAL COMPENSATION HOURS ------------------------------------
        const el_MCH_header_text = document.getElementById("id_MCH_header_text")
        const el_MCH_meetingdate1 = document.getElementById("id_MCH_meetingdate1")
        if(el_MCH_meetingdate1){
            el_MCH_meetingdate1.addEventListener("change", function() {
                MCH_InputChange(el_MCH_meetingdate1)}, false )
        };
        const el_MCH_err_date01 = document.getElementById("id_MCH_err_date01")
        const el_MCH_meetingdate2 = document.getElementById("id_MCH_meetingdate2")
        if(el_MCH_meetingdate2){
            el_MCH_meetingdate2.addEventListener("change", function() {
                MCH_InputChange(el_MCH_meetingdate2)}, false )
        };
        const el_MCH_err_date02 = document.getElementById("id_MCH_err_date02")
        const el_MCH_msg = document.getElementById("id_MCH_msg")
        const el_MCH_btn_add = document.getElementById("id_MCH_btn_add")
        if(el_MCH_btn_add){
            el_MCH_btn_add.addEventListener("click", function() {MCH_AddDelete("add")}, false )
        };
        const el_MCH_btn_delete = document.getElementById("id_MCH_btn_delete")
        if(el_MCH_btn_delete){
            el_MCH_btn_delete.addEventListener("click", function() {MCH_AddDelete("delete")}, false )
        };
        const el_MCH_btn_save = document.getElementById("id_MCH_btn_save")
        if(el_MCH_btn_save){
            el_MCH_btn_save.addEventListener("click", function() {MCH_Save()}, false )
        };

// ---  MSSS MOD SELECT SCHOOL SUBJECT STUDENT ------------------------------
        const el_MSSSS_input = document.getElementById("id_MSSSS_input");
        const el_MSSSS_tblBody = document.getElementById("id_MSSSS_tbody_select");
        if (el_MSSSS_input){
            el_MSSSS_input.addEventListener("keyup", function(event){
                setTimeout(function() {t_MSSSS_InputKeyup(el_MSSSS_input)}, 50)});
        };
        if (el_MSSSS_input){
            el_MSSSS_input.addEventListener("click", function() {t_MSSSS_Save(el_MSSSS_input, MSSSS_Response)}, false );
        };

// ---  MOD SELECT MULTIPLE  ------------------------------
        const el_MSM_tblbody_select = document.getElementById("id_MSM_tbody_select");
        const el_MSM_input = document.getElementById("id_MSM_input");
        if (el_MSM_input){
            el_MSM_input.addEventListener("keyup", function(){
                setTimeout(function() {MSM_InputKeyup(el_MSM_input)}, 50)});
        };
        const el_MSM_btn_save = document.getElementById("id_MSM_btn_save")
        if (el_MSM_btn_save){
            el_MSM_btn_save.addEventListener("click", function() {MSM_Save()}, false )
        };

// ---  MOD CONFIRM ------------------------------------
        let el_confirm_header = document.getElementById("id_modconfirm_header");
        let el_confirm_loader = document.getElementById("id_modconfirm_loader");
        let el_confirm_msg_container = document.getElementById("id_modconfirm_msg_container")
        let el_confirm_btn_cancel = document.getElementById("id_modconfirm_btn_cancel");
        let el_confirm_btn_save = document.getElementById("id_modconfirm_btn_save");
        if (el_confirm_btn_save){el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()}, false)};

    if(may_view_page){
// ---  set selected menu button active
        SetMenubuttonActive(document.getElementById("id_hdr_users"));

        const datalist_request = {
                setting: {page: "page_corrector"},
                schoolsetting: {setting_key: "import_username"},
                locale: {page: ["page_user", "page_corrector", "upload"]},
                examyear_rows: {get: true},
                corrector_rows: {get: true},
                usercompensation_rows: {get: true},
                // PR2023-01-06 was: department_rows: {skip_allowed_filter: true},
                // PR2023-05-08 was: school_rows: {skip_allowed_filter: true}, level_rows: {skip_allowed_filter: true},
                department_rows: {get: true},
                school_rows: {get: true},
                level_rows: {get: true},
                subject_rows_page_users: {get: true},
                cluster_rows: {page: "page_corrector"}
            };

        console.log("    datalist_request: ", datalist_request)
        DatalistDownload(datalist_request, "DOMContentLoaded");
    };
//  #############################################################################################################

//========= DatalistDownload  ===================== PR2020-07-31
    function DatalistDownload(datalist_request, called_by) {
        //console.log( "=== DatalistDownload ", called_by)
        //console.log("request: ", datalist_request)

// ---  Get today's date and time - for elapsed time
        let startime = new Date().getTime();

// ---  show loader
        el_loader.classList.remove(cls_visible_hide)

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

                // hide loader
                el_loader.classList.add(cls_visible_hide)
                let check_status = false;
                let isloaded_loc = false, isloaded_settings = false, isloaded_permits = false;
                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                    isloaded_loc = true;
        //console.log("loc: ", loc)
                };

                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict;
                    selected_btn = setting_dict.sel_btn;
                    isloaded_settings = true;

        // ---  fill cols_hidden
                    if("cols_hidden" in setting_dict){
                        b_copy_array_noduplicates(setting_dict.cols_hidden, mod_MCOL_dict.cols_hidden);
                    };

        // add level to cols_skipped when dep has no level, thumbrule_allowed PR2023-01-24
                    mod_MCOL_dict.cols_skipped = {};
                    const cols_skipped_all = [];
                    //if (!setting_dict.sel_dep_level_req) {cols_skipped_all.push("lvl_abbrev") };
                    //if (!setting_dict.sel_examyear_thumbrule_allowed) {cols_skipped_all.push("is_thumbrule")};
                    if (cols_skipped_all.length){mod_MCOL_dict.cols_skipped.all = cols_skipped_all};
                };

                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    isloaded_permits = true;
                    // get_permits must come before CreateSubmenu and FiLLTbl
                    b_get_permits_from_permitlist(permit_dict);
                };

                if(isloaded_loc && isloaded_permits){CreateSubmenu()};
                if(isloaded_settings || isloaded_permits){b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);};

                if ("examyear_rows" in response) {
                    examyear_rows = response.examyear_rows;
                    b_fill_datamap(examyear_map, response.examyear_rows);
                };

                if ("corrector_rows" in response) {
                    b_fill_datadicts("user", "id", null, response.corrector_rows, corrector_dicts);
                };

                if ("usercompensation_rows" in response) {
                    // mapid : "usercomp_124_222"
                    b_fill_datadicts_by_mapid(response.usercompensation_rows, usercompensation_dicts)
                    console.log("usercompensation_dicts", usercompensation_dicts);
                };
                if ("usercomp_agg_rows" in response) {
                    b_fill_datadicts("usercomp_agg", "u_id", "exam_id", response.usercomp_agg_rows, usercomp_agg_dicts);
                };
                if ("examyear_rows" in response) {
                    examyear_rows = response.examyear_rows;
                    b_fill_datamap(examyear_map, response.examyear_rows) ;
                };
                if ("department_rows" in response){
                    department_rows = response.department_rows
                };
                if ("school_rows" in response)  {school_rows = response.school_rows};

                if ("level_rows" in response)  {
                    level_rows = response.level_rows
                };
                if ("subject_rows_page_users" in response)  {subject_rows = response.subject_rows_page_users};
                if ("cluster_rows" in response) {
                    b_fill_datadicts("cluster", "id", null, response.cluster_rows, cluster_dictsNEW);
                };
                if ("msg_html" in response) {
                    b_show_mod_message_html(response.msg_html)
                };
                HandleBtnSelect(selected_btn, true);  // true = skip_upload

            },
            error: function (xhr, msg) {
// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                //console.log(msg + '\n' + xhr.responseText);
            }
        });
    }  // function DatalistDownload


    function get_datadicts_keystr(tblName, pk_int, studsubj_pk) {  // PR2023-01-05
        let key_str = tblName + "_" + ((pk_int) ? pk_int : 0);
        //if (tblName === "studsubj") {key_str += "_" + ((studsubj_pk) ? studsubj_pk : 0)};
        return key_str
    };


//=========  CreateSubmenu  ===  PR2020-07-31
    function CreateSubmenu() {

        // PR2023-03-26 show tab 'Correctors' only when requsr_same_school
        add_or_remove_class(document.getElementById("id_btn_correctors"), cls_hide, !permit_dict.requsr_same_school)

        //console.log("===  CreateSubmenu == ");
        let el_submenu = document.getElementById("id_submenu");
        // hardcode access of system admin, to get access before action 'crud' is added to permits
        const permit_system_admin = (permit_dict.requsr_role_system && permit_dict.usergroup_list.includes("admin"));
        const permit_role_admin = (permit_dict.requsr_role_admin && permit_dict.usergroup_list.includes("admin"));

        if (permit_dict.permit_crud_sameschool || permit_dict.permit_crud_otherschool) {
            AddSubmenuButton(el_submenu, loc.Delete_user, function() {ModConfirmOpen("user","delete")}, []);
        };

        AddSubmenuButton(el_submenu, loc.Hide_columns, function() {t_MCOL_Open("page_corrector")}, [])

        el_submenu.classList.remove(cls_hide);
    };//function CreateSubmenu

//###########################################################################
// +++++++++++++++++ EVENT HANDLERS +++++++++++++++++++++++++++++++++++++++++
//=========  HandleBtnSelect  ================ PR2020-09-19 PR2021-08-01
    function HandleBtnSelect(data_btn, skip_upload) {
        console.log( "===== HandleBtnSelect ========= ");
        console.log( "    data_btn", data_btn);
        console.log( "    skip_upload", skip_upload);

// ---  get  selected_btn
        // set to default "btn_usercompensation" when there is no selected_btn
        // this happens when user visits page for the first time
        // includes is to catch saved btn names that are no longer in use
        if (data_btn && ["btn_correctors", "btn_usercompensation", "btn_usercomp_agg"].includes(data_btn)){
            selected_btn = data_btn;
        } else if (!["btn_correctors", "btn_usercompensation", "btn_usercomp_agg"].includes(data_btn)) {
            selected_btn = (permit_dict.requsr_same_school) ? "btn_correctors" : "btn_usercompensation";
        };

        console.log( "    selected_btn", selected_btn);
// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_corrector: {sel_btn: selected_btn}};
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);
        };

// ---  highlight selected button
        b_highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn);

// ---  show only the elements that are used in this tab
        b_show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

// ---  fill datatable
        FillTblRows(skip_upload);

    };  // HandleBtnSelect

//=========  HandleTblRowClicked  ================ PR2020-08-03 PR2021-08-01
    function HandleTblRowClicked(tr_clicked) {
        //console.log("=== HandleTblRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);
        //console.log( "tr_clicked.id: ", tr_clicked, typeof tr_clicked.id);

// ---  deselect all highlighted rows, select clicked row
        t_td_selected_toggle(tr_clicked, true);  // select_single = True

        //const data_dicts = get_datadicts_from_selectedBtn();
        //const data_dict = (tr_clicked && tr_clicked.id && tr_clicked.id in data_dicts) ? data_dicts[tr_clicked.id]: null;
        //console.log( "  data_dict: ", data_dict);

    };  // HandleTblRowClicked

//========= FillTblRows  =================== PR2021-08-01 PR2022-02-28
    function FillTblRows(skip_upload) {
        console.log( "===== FillTblRows  === ");
        console.log( "    selected_btn: ", selected_btn);

        const tblName = get_tblName_from_selectedBtn() // tblName = userapproval or usercompensation
        const field_setting = field_settings[selected_btn];
        const data_dicts = get_datadicts_from_selectedBtn();

// ---  get list of hidden columns
        const col_hidden = get_column_is_hidden();

        //console.log( "    tblName", tblName);
        console.log( "    data_dicts", data_dicts);
        //console.log( "    field_setting", field_setting);

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null

// --- create table header and filter row
        CreateTblHeader(field_setting, col_hidden);

// --- loop through data_rows
        for (const data_dict of Object.values(data_dicts)) {
            const tblRow = CreateTblRow(tblName, field_setting, data_dict, col_hidden);
        };

// --- filter tblRow
        // set filterdict isactive after loading page (then skip_upload = true)
        // const set_filter_isactive = skip_upload;
        Filter_TableRows(skip_upload)
    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-07-31 PR2021-03-23  PR2021-08-01 PR2023-04-15
    function CreateTblHeader(field_setting, col_hidden) {
        //console.log("===  CreateTblHeader ===== ");
        //console.log("field_setting", field_setting);
        //console.log("    col_hidden", col_hidden);

        const column_count = field_setting.field_names.length;

// +++  insert header and filter row ++++++++++++++++++++++++++++++++
        let tblRow_header = tblHead_datatable.insertRow (-1);
        let tblRow_filter = tblHead_datatable.insertRow (-1);

    // --- loop through columns
        for (let j = 0; j < column_count; j++) {
            const field_name = field_setting.field_names[j];

    // skip columns if in col_hidden
            if (!col_hidden.includes(field_name)){
        // --- get field_caption from field_setting
                const field_caption = loc[field_setting.field_caption[j]];
                const field_tag = field_setting.field_tags[j];
                const filter_tag = field_setting.filter_tags[j];
                const class_width = "tw_" + field_setting.field_width[j] ;
                const class_align = "ta_" + field_setting.field_align[j];

// ++++++++++ insert columns in header row +++++++++++++++
        // --- add th to tblRow.
                let th_header = document.createElement("th");
        // --- add div to th, margin not working with th
                    const el_header = document.createElement("div");
        // --- add innerText to el_header
                    el_header.innerText = (field_caption) ? field_caption : null;
        // --- add width, text_align
                        // not necessary: th_header.classList.add(class_width, class_align);
                    th_header.classList.add(class_width, class_align);
                    el_header.classList.add(class_width, class_align);
                    if (field_name === "status"){
                        // --- add  statud icon.
                        el_header.classList.add("diamond_0_0");
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
                    // PR2021-05-30 debug: use cellIndex instead of attribute data-colindex,
                    //el_filter.setAttribute("data-colindex", j);

        // --- add EventListener to el_filter / th_filter
                    if (["text", "number"].includes(filter_tag)) {
                        el_filter.addEventListener("keyup", function(event){HandleFilterKeyup(el_filter, event)});
                        add_hover(th_filter);

                    } else if (filter_tag === "toggle") {
                        // add EventListener for icon to th_filter, not el_filter
                        th_filter.addEventListener("click", function(event){HandleFilterToggle(el_filter)});
                        th_filter.classList.add("pointer_show");

                        // default empty icon necessary to set pointer_show
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

                    el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");
                th_filter.appendChild(el_filter)
                tblRow_filter.appendChild(th_filter);
            };
        };
    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09 PR2021-08-01 PR2023-02-26
    function CreateTblRow(tblName, field_setting, data_dict, col_hidden) {
        //console.log("=========  CreateTblRow =========", tblName);
        //console.log("    data_dict", data_dict);

        const field_names = field_setting.field_names;
        const field_tags = field_setting.field_tags;
        const filter_tags = field_setting.filter_tags;
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;

        const map_id = (data_dict.mapid) ? data_dict.mapid : null;

// ---  lookup index where this row must be inserted
        const ob1 = (data_dict.username) ? data_dict.username : "";
        const ob2 = (data_dict.subjbase_code) ? data_dict.subjbase_code : "";
        const ob3 = (data_dict.sb_code) ? data_dict.sb_code : "";

        const row_index = b_recursive_tblRow_lookup(tblBody_datatable, setting_dict.user_lang, ob1, ob2, ob3);

// --- insert tblRow into tblBody at row_index
        const tblRow = tblBody_datatable.insertRow(row_index);
        tblRow.id = map_id

        //console.log("    tblRow", tblRow);

// --- add data attributes to tblRow
        tblRow.setAttribute("data-pk", data_dict.id);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);
        tblRow.setAttribute("data-ob2", ob2);
        tblRow.setAttribute("data-ob3", ob3);

// --- add EventListener to tblRow
        tblRow.addEventListener("click", function() {HandleTblRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
        for (let j = 0; j < column_count; j++) {
            const field_name = field_names[j];

    // - skip column if field_name in col_hidden;
            if (!col_hidden.includes(field_name)){
                const field_tag = field_tags[j];
                const class_width = "tw_" + field_width[j];
                const class_align = "ta_" + field_align[j];

        // --- insert td element,
                let td = tblRow.insertCell(-1);

        // --- create element with tag from field_tags
                let el = document.createElement(field_tag);

        // --- add data-field attribute
                    el.setAttribute("data-field", field_name);

        // --- add  text_align
                el.classList.add(class_width, class_align);

        // --- append element
                td.appendChild(el);

        // --- add data-field Attribute when input element
                    if (field_tag === "input") {
                        el.setAttribute("type", "text")
                        el.setAttribute("autocomplete", "off");
                        el.setAttribute("ondragstart", "return false;");
                        el.setAttribute("ondrop", "return false;");
                // --- add class 'input_text' and text_align
                    // class 'input_text' contains 'width: 100%', necessary to keep input field within td width
                        el.classList.add("input_text");
                    }

    // --- add EventListener to td
                    // only input fields are: "uc_corr_amount", "uc_corr_meetings"
                    // only auth1 of auth2 vfrom role corrector may edit them
                    if (field_tag === "input") {
                        if (permit_dict.permit_make_corrections){
                            el.addEventListener("change", function() {UploadInputChange(el)}, false)
                            add_hover(td);
                        };
                        el.readOnly = !permit_dict.permit_make_corrections;

                    } else if (field_name === "select") {
                        // TODO add select multiple users option PR2020-08-18

                    } else if (field_name === "uc_meetings") {
                        el.addEventListener("click", function(){MCH_Open(td)});
                        add_hover(td);
                    } else if (field_name === "uc_meetingsxx") {
                        // attach eventlistener and hover to td, not to el. No need to add icon_class here
                        td.addEventListener("click", function() {UploadToggle(el)}, false)
                        add_hover(td);

                   } else if (field_name === "allowed_clusters") {
                        if (permit_dict.permit_crud && permit_dict.requsr_same_school) {
                            td.addEventListener("click", function() {MSM_Open(el)}, false);
                            add_hover(td);
                        };

                    } else if (field_name === "status"){

                        const published_id = (data_dict.published_id) ? data_dict.published_id : null;
                        const has_comp = (!!data_dict.uc_amount || !!data_dict.uc_meetings);
                        if(!published_id && has_comp && permit_dict.permit_approve_comp){
                            td.addEventListener("click", function() {UploadToggleStatus(el)}, false)
                            add_hover(td);
                        };
                    };
// --- put value in field
                UpdateField(el, data_dict)
            };
        };
        return tblRow;
    };  // CreateTblRow

//=========  UpdateTblRow  ================ PR2020-08-01
    function UpdateTblRow(tblRow, tblName, data_dict) {
        console.log("=========  UpdateTblRow =========");
        if (tblRow && tblRow.cells){
            for (let i = 0, td; td = tblRow.cells[i]; i++) {
                UpdateField(td.children[0], data_dict);
            };
        };
    };  // UpdateTblRow

//=========  UpdateField  ================ PR2020-08-16 PR2023-02-25
    function UpdateField(el_div, data_dict) {
        //console.log("=========  UpdateField =========");
        //console.log("    data_dict", data_dict);

        const field_name = get_attr_from_el(el_div, "data-field");

    //console.log("    field_name", field_name);

        if(el_div && field_name){
            let inner_text = null, title_text = null, filter_value = null;
            if (field_name === "select") {
                // TODO add select multiple users option PR2020-08-18

            } else if (["user_sb_code", "username", "last_name", "sb_code", "uc_school_abbrev",
                "depbase_code", "lvlbase_code", "uc_depbase_code", "uc_lvlbase_code", "subjbase_code", "subj_name_nl", "exam_version"].includes(field_name)){
                inner_text = data_dict[field_name];
                filter_value = (inner_text) ? inner_text.toLowerCase() : null;

            } else if (["uc_meetings"].includes(field_name)){
                inner_text = (data_dict[field_name]) ? data_dict[field_name] : "&nbsp";  // don't show zero's
                filter_value = (inner_text) ? inner_text : null;
                if(data_dict.uc_meetingdate1 || data_dict.uc_meetingdate2) {
                    const date1_txt = (data_dict.uc_meetingdate1) ? format_dateISO_vanilla (loc, data_dict.uc_meetingdate1) : null;
                    const date2_txt = (data_dict.uc_meetingdate2) ? format_dateISO_vanilla (loc, data_dict.uc_meetingdate2) : null;
                    title_text = [date1_txt, date2_txt].join("\n");
                };

            } else if (["uc_amount", "uc_corr_amount", "uc_corr_meetings", "examperiod"].includes(field_name)){
                inner_text = (data_dict[field_name]) ? data_dict[field_name] : null;  // don't show zero's
                filter_value = (inner_text) ? inner_text : null;

            } else if (field_name === "uc_compensation") {
                inner_text = ( Number(data_dict[field_name])) ? Number( data_dict[field_name]) / 100 : null;
                filter_value = (inner_text) ? inner_text : null;

            } else if (field_name === "uc_school_abbrev") {
                // schoolname cannot be put in user table, because it has no examyear PR2021-07-05
                // lookup schoolname in school_rows instead
                if (data_dict.schoolbase_id){
                    for (let i = 0, dict; dict = school_rows[i]; i++){
                        if(dict.base_id && dict.base_id === data_dict.schoolbase_id) {
                            inner_text = (dict.abbrev)  ? dict.abbrev : "---";
                            filter_value = (inner_text) ? inner_text.toLowerCase() : null;
                            break;
                }}};

            } else if (field_name.includes("allowed")){
                const field_value = (data_dict[field_name]) ? data_dict[field_name] : null;
                inner_text = (field_value) ? field_value : "&nbsp";
                if (field_name === "allowed_schoolbases") {
                    inner_text = (field_value) ? field_value : "&nbsp";
                    title_text = (data_dict.allowed_schoolbases_title) ? data_dict.allowed_schoolbases_title : null;
                    filter_value = (field_value) ? field_value.toLowerCase() : null;
                } else if (field_name === "allowed_subjbases") {
                    inner_text = (field_value) ? field_value : "&nbsp";
                    title_text = (data_dict.allowed_subjbases_title) ? data_dict.allowed_subjbases_title : null;
                    filter_value = (field_value) ? field_value.toLowerCase() : null;
                } else  if (field_name === "allowed_clusters") {
                    inner_text = (field_value && field_value.length) ? field_value.join(", ") : "&nbsp";
                    title_text = (field_value && field_value.length) ? field_value.join("\n") : null;
                    filter_value = (field_value && field_value.length) ? field_value.join(" ") : "&nbsp";
                } else {
                    inner_text = (field_value) ? field_value : "&nbsp";
                    filter_value = (field_value) ? field_value.toLowerCase() : null;
                };

            } else if (field_name === "role") {
                const role = data_dict[field_name];
                inner_text = (loc.role_caption && loc.role_caption[role])  ? loc.role_caption[role] : role;
                filter_value = inner_text;

            } else if (field_name === "action"){
                el_div.value = data_dict[field_name];
                filter_value = data_dict[field_name];

            } else if (field_name.slice(0, 5) === "group") {
                //  field_name is "group_read", "group_edit",  "group_auth1", "group_auth2", etc

                // data_dict[field_name] example: perm_system: true
                const db_field = field_name.slice(6);
                //  db_field is "read", "edit",  "auth1", "auth2", etc

                // const permit_bool = (data_dict[field_name]) ? data_dict[field_name] : false;
                const permit_bool = (data_dict.usergroups) ? data_dict.usergroups.includes(db_field) : false;

    //console.log("    field_name", field_name);
    //console.log("    db_field", db_field);
    //console.log("    data_dict.usergroups", data_dict.usergroups);
    //console.log("    permit_bool", permit_bool);

                filter_value = (permit_bool) ? "1" : "0";
                el_div.className = (permit_bool) ? "tickmark_2_2" : "tickmark_0_0" ;

            } else if (field_name === "status"){
                if (!!data_dict.uc_amount || !!data_dict.uc_meetings) {
                    const [status_className, status_title_text, filter_val] = f_format_status_subject("uc", data_dict)
                    filter_value = filter_val;
                    el_div.className = status_className;
                    title_text = status_title_text;
                };
            };

// ---  put value in innerText and title
            if (el_div.tagName === "INPUT"){
                el_div.value = inner_text;
            } else {
                el_div.innerHTML = inner_text;
            };
            add_or_remove_attr (el_div, "title", !!title_text, title_text);

// ---  add attribute filter_value
        //console.log("filter_value", filter_value);
            add_or_remove_attr (el_div, "data-filter", !!filter_value, filter_value);
        };  // if(el_div && field_name){
    };  // UpdateField


//========= get_tblName_from_selectedBtn  ======== // PR2023-02-26
    function get_tblName_from_selectedBtn() {
        return (selected_btn === "btn_usercompensation") ? "userapproval" :
                        (selected_btn === "btn_usercomp_agg") ? "usercompensation" : null;
    }  // get_tblName_from_selectedBtn

//========= get_datadicts_from_selectedBtn  ======== // PR2023-02-26
    function get_datadicts_from_selectedBtn() {
        return (selected_btn === "btn_correctors") ? corrector_dicts :
                (selected_btn === "btn_usercompensation") ? usercompensation_dicts :
                (selected_btn === "btn_usercomp_agg") ? usercomp_agg_dicts : null;
    } // get_datadicts_from_selectedBtn

//========= get_column_is_hidden  ====== PR2023-02-26
    function get_column_is_hidden() {
        //console.log(" --- get_column_is_hidden ---")

// ---  get list of hidden columns
        // copy col_hidden from mod_MCOL_dict.cols_hidden
        const col_hidden = [];
        // can also add multiple values with push:
        // was:
        // col_hidden.push( "srgrade", "sr_status", "pescore", "pe_status", "pegrade");

        b_copy_array_noduplicates(mod_MCOL_dict.cols_hidden, col_hidden);

// - hide level when not level_req
       //if(!setting_dict.sel_dep_level_req){col_hidden.push("lvl_abbrev")};
        return col_hidden;
    };  // get_column_is_hidden


// +++++++++++++++++ UPLOAD CHANGES +++++++++++++++++ PR2023-04-15
    function UploadInputChange(el_input) {
        console.log( " ==== UploadInputChange ====");
        console.log("el_input: ", el_input);
        // only input fields are: "uc_corr_amount", "uc_corr_meetings"

// ---  upload changes
        if (permit_dict.permit_crud){
            const tblRow = t_get_tablerow_selected(el_input);
            const data_field = get_attr_from_el(el_input, "data-field");
        console.log("data_field: ", data_field);
            if(tblRow){
                const data_dict = usercompensation_dicts[tblRow.id];
                if (data_dict){
                    const new_value = (el_input.value && Number(el_input.value)) ? Number(el_input.value) : 0;
                    const old_value = (data_dict[data_field]) ? data_dict[data_field] : null;
                     // ??? (data_field === "uc_corr_meetings") ? data_dict.uc_meetings : 0;

        console.log("old_value: ", old_value);
        console.log("data_dict: ", data_dict);
                    const max_meetings = 2;
                    const amount_or_meetings = (data_field === "uc_corr_amount") ? data_dict.uc_amount :
                                                (data_field === "uc_corr_meetings") ? data_dict.uc_meetings : 0

                    const not_valid_txt = [loc.Correction, " '", el_input.value, "'", loc.is_not_valid, "<br>"].join("");
                    let msg_txt = null;
                    if (el_input.value && !Number(el_input.value)){
                        msg_txt = [not_valid_txt, loc.must_enter_whole_number].join("");

                    // the remainder / modulus operator (%) returns the remainder after (integer) division.
                    } else if(new_value % 1) {
                        msg_txt = [not_valid_txt, loc.must_enter_whole_number].join("");

                    } else if (amount_or_meetings + new_value  < 0 ){
                        msg_txt = [not_valid_txt, loc.cannot_deduct_more_than_original_number].join("");

                    } else if (data_field === "uc_corr_meetings" && amount_or_meetings + new_value > max_meetings ) {
                        msg_txt = [not_valid_txt, loc.Total_number_meetings_cannot_be_greater_than, max_meetings, "."].join("");
                    };

                    if (msg_txt){
                        const msg_html = ["<p class='border_bg_invalid p-2'>", msg_txt, "</p>"].join("");
                        b_show_mod_message_html(msg_html);
                        el_input.value = old_value;

                    } else {
                        let upload_dict = {
                            table: "usercompensation",
                            mode: "update",
                            usercompensation_pk: data_dict.uc_id
                        };
                        const db_field = (data_field === "uc_corr_amount") ? "correction_amount" :
                                                (data_field === "uc_corr_meetings") ? "correction_meetings" : "-";
                        upload_dict[db_field] = new_value;
                        UploadChanges(upload_dict, urls.url_usercompensation_upload);
                    };
                };
            };
        };
    }  // UploadInputChange

//========= UploadToggleStatus  ============= PR2023-03-23
    function UploadToggleStatus(el_input) {
        console.log( " ==== UploadToggleStatus ====");

        if (permit_dict.permit_approve_comp){

            const tblRow = t_get_tablerow_selected(el_input);
        console.log( "    tblRow", tblRow);

// - get statusindex of requsr ( statusindex = 1 when auth1 etc
            // auth_index : 0 = None, 1 = auth1, 2 = auth2, 3 = auth3, 4 = auth4
            // b_get_auth_index_of_requsr returns index of auth user, returns 0 when user has none or multiple auth usergroups
            // this function gives err message when multiple found. (uses b_show_mod_message_html)
            // const requsr_auth_index = b_get_auth_index_of_requsr(loc, permit_dict);

            // PR2022-05-30 debug: don't use b_get_auth_index_of_requsr, goes wrong when selected_auth = examinator

// get auth index of requsr, null when multiple found
            const usergroup_list = (permit_dict.usergroup_list) ? permit_dict.usergroup_list : [];
            const is_auth1 = usergroup_list.includes("auth1");
            const is_auth2 = usergroup_list.includes("auth2");
            const requsr_auth_index = (is_auth1 && !is_auth2) ? 1 :
                                      (!is_auth1 && is_auth2) ? 2 : null;
        console.log( "    usergroup_list", usergroup_list);
        console.log( "    requsr_auth_index", requsr_auth_index);

            if (requsr_auth_index){
                const data_dict = get_usercompensation_dict(tblRow);
        console.log( "    data_dict", data_dict);

                if(!isEmpty(data_dict)){
// - get auth info
                    const is_published = (!!data_dict.published_id);

// give message and exit when published
                    if (is_published){
                        const msg_html = [loc.This_approval, " ", loc.is_already_published, "<br>",
                                          loc.You_cannot_change_approval].join("");
                        b_show_mod_message_html(msg_html);

                    } else {
                        const model_field = "auth" +  requsr_auth_index + "by";
                        const field_auth_id = model_field + "_id";
                        // field_auth_id = 'auth1by_id'
                        const auth_id = (data_dict[field_auth_id]) ? data_dict[field_auth_id] : null;
                        // field_auth_id = 47
                        const auth_dict = {};
                        let requsr_auth_bool = false;

                        for (let auth_index = 1, key_str; auth_index < 3; auth_index++) {
                            key_str = "uc_auth" + auth_index + "by_id";

                            if (data_dict[key_str]){
                                if (requsr_auth_index === auth_index) {
                                    requsr_auth_bool = true;
                                };
                                // only 2 auths are used, show icon with left or right part black
                                auth_dict[auth_index] = (!!data_dict[key_str]);
                            };
                        };
``

// ---  toggle value of requsr_auth_bool
                        // - get new_requsr_auth_bool - set false if already filled in
                        // use 'true' instead of requsr_pk
                        const new_requsr_auth_bool = !requsr_auth_bool;

// also update value in auth_dict;
                        auth_dict[requsr_auth_index] = new_requsr_auth_bool

    // ---  change icon, before uploading (set auth4 also when auth 1, auth3 also when auth 2)
                        el_input.className = f_get_status_auth12_iconclass(is_published, false, auth_dict[1], auth_dict[2]);

        // ---  upload changes
                        const usercompensation_dict = {
                            usercompensation_pk: data_dict.uc_id
                        };
                        usercompensation_dict[model_field] = new_requsr_auth_bool

                        const upload_dict = {
                            table: "usercompensation",
                            usercompensation_list: [usercompensation_dict]
                        };
                        const url_str = urls.url_usercomp_approve_single
                        UploadChanges(upload_dict, url_str);

                    };  //if (is_published)
                };  //  if(!isEmpty(data_dict))
            };  //  if(requsr_auth_index)
        }; //   if(permit_dict.permit_approve_subject)
    };  // UploadToggleStatus

//========= UploadToggle  ============= PR2020-07-31
    function UploadToggle(el_input) {
        console.log( " ==== UploadToggle ====");
        console.log( "el_input", el_input);
        console.log( "permit_dict", permit_dict);

        mod_dict = {};
        const has_permit = (permit_dict.permit_crud_otherschool) ||
                            (permit_dict.permit_crud_sameschool && selected_btn !== "btn_userpermit");

        console.log( "has_permit", has_permit);

        if(has_permit){
            const tblRow = t_get_tablerow_selected(el_input);
            if(tblRow){
                const tblName = get_tblName_from_mapid(tblRow.id);
                const data_dict = get_datadict_from_mapid(tblRow.id)
    console.log( "tblName", tblName);
    console.log( "data_dict", data_dict);

                if(!isEmpty(data_dict)){
                    const fldName = get_attr_from_el(el_input, "data-field");
                    let permit_bool = (get_attr_from_el(el_input, "data-filter") === "1");

    // show message when sysadmin tries to delete sysadmin permit
                    // TODO remove requsr_pk from client
                    const is_request_user = (permit_dict.requsr_pk && permit_dict.requsr_pk === data_dict.id);
                    if(fldName === "group_admin" && is_request_user && permit_bool ){
                        ModConfirmOpen("usergroup", "permission_admin", el_input)
                    } else {

            // ---  toggle permission el_input
                        permit_bool = (!permit_bool);
    console.log( "new permit_bool", permit_bool);
            // ---  put new permission in el_input
                        el_input.setAttribute("data-filter", (permit_bool) ? "1" : "0")
           // ---  change icon, before uploading
                        el_input.className = (permit_bool) ? "tickmark_1_2" : "tickmark_0_0";

    console.log( "tblName", tblName);
    console.log( "fldName", fldName);
                        const url_str = urls.url_user_upload;
                        const upload_dict = {mode: "update", mapid: data_dict.mapid};

                        upload_dict.user_pk = data_dict.id,
                        upload_dict.schoolbase_pk = data_dict.schoolbase_id;

                        const usergroupname = fldName.substr(6);
                        upload_dict.usergroups = {}
                        upload_dict.usergroups[usergroupname] = permit_bool;
    console.log( "upload_dict", upload_dict);
    console.log( "  >>>>>>>> url_str", url_str);

                        UploadChanges(upload_dict, url_str);
                    }  // if(fldName === "group_admin" && is_request_user && permit_bool ){
                }  //  if(!isEmpty(data_dict)){
            }  //   if(!!tblRow)
        }  // if(permit_dict.usergroup_system)
    }  // UploadToggle

//========= UploadChanges  ============= PR2020-08-03 PR2023-01-01
    function UploadChanges(upload_dict, url_str) {
        console.log("=== UploadChanges");
        console.log("    url_str: ", url_str);
        console.log("    upload_dict: ", upload_dict);

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

                    console.log("response");
                    console.log( response);

                    if("msg_dictlist" in response){
                        b_show_mod_message_dictlist(response.msg_dictlist);
                    }
                    if("msg_html" in response){
                        b_show_mod_message_html(response.msg_html);
                    };

                    const mode = get_dict_value(response, ["mode"]);
                    if(["delete", "send_activation_email"].includes(mode)) {
                        ModConfirmResponse(response);
                    };

                    if ("updated_corrector_rows" in response) {
                        RefreshDataRows("user", response.updated_corrector_rows, corrector_dicts, true)  // true = update
                    };
                    if ("updated_usercompensation_rows" in response) {
                        RefreshDataRows("usercompensation", response.updated_usercompensation_rows, usercompensation_dicts, true)  // true = update
                    };
                    if ("msg_html" in response) {
                        b_show_mod_message_html(response.msg_html)
                    };
                    if ("messages" in response) {
                        b_show_mod_message_dictlist(response.messages)
                    };

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

//========= HandleInputChange  =============== PR2021-03-20 PR2022-02-21
    function HandleInputChange(el_input){
        console.log(" --- HandleInputChange ---")

        const tblRow = t_get_tablerow_selected(el_input);
        const pk_int = get_attr_from_el_int(tblRow, "data-pk");
        const map_id = tblRow.id;

        console.log("    tblRow", tblRow)
        console.log("    pk_int", pk_int)
        console.log("    map_id", map_id)

        if (selected_btn === "btn_usercomp_agg"){
            // reset el_input.value to saved value
            const data_dict = usercomp_agg_dicts[map_id];
            el_input.value = (data_dict && data_dict.uc_meetings) ? data_dict.uc_meetings : null
            b_show_mod_message_html(loc.cannot_enter_meetings_in_tab_compensation + "<br>" + loc.select_tab_approvals_to_enter_meetings);
        } else {

            if (map_id){
                const data_dict = usercompensation_dicts[map_id];

                const fldName = get_attr_from_el(el_input, "data-field");
                const usercompensation_pk = data_dict.id;
                const map_value = data_dict[fldName];

                let new_value = null;
                if (el_input.value){
                    if (!Number(el_input.value) ) {
                        const msg_html = ["'", el_input.value, "'", loc.is_an_invalid_number,
                        "<br>", loc.must_enter_whole_number_between_0_and_, "2."].join("");
                        b_show_mod_message_html(msg_html);

                    } else if (![0,1,2].includes(Number(el_input.value))) {
                        const msg_html = ["'", el_input.value, "'", loc.is_not_valid,
                        "<br>", loc.must_enter_whole_number_between_0_and_, "2."].join("");
                        b_show_mod_message_html(msg_html);
                    } else {
                        new_value = Number(el_input.value);
                    };
                };

                if(new_value !== map_value){
            // ---  create mod_dict
                    const url_str = urls.url_usercompensation_upload;
                    const upload_dict = {mode: "update",
                                        usercompensation_pk: usercompensation_pk};
                    upload_dict[fldName] = new_value;
            //console.log("upload_dict: ", upload_dict);

            // ---  upload changes
                    UploadChanges(upload_dict, url_str);
                };
            };
        };
    };  // HandleInputChange


//=========  MCH_Open  ================ PR2023-03-22
    function MCH_Open(td_clicked) {
        console.log(" -----  MCH_Open   ----")
        console.log("    td_clicked", td_clicked)
        console.log("    usercompensation_dicts", usercompensation_dicts)

        const tr_clicked = td_clicked.parentNode;
        console.log("    tr_clicked", tr_clicked)

        const map_id = tr_clicked.id;
        const data_dict = usercompensation_dicts[map_id];
        console.log("    map_id", map_id)
        console.log("    data_dict", data_dict)
        if (data_dict){
            el_MCH_header_text.innerHTML = [loc.Meetings, data_dict.subj_name_nl + " - " + loc.examperiod_caption[data_dict.examperiod]].join("<br>");
    // --- get data_dict from tblName and selected_pk
            //const data_dict = get_datadict_from_pk(tblName, selected_pk)
            //console.log("    data_dict", data_dict);

            el_MCH_meetingdate1.value = data_dict.uc_meetingdate1;
            el_MCH_meetingdate2.value = data_dict.uc_meetingdate2;

    // ---  create mod_MCH_dict
            b_clear_dict(mod_MCH_dict);
            mod_MCH_dict.data_dict = data_dict;
            mod_MCH_dict.meeting_count = data_dict.uc_meetings;
            mod_MCH_dict.usercomp_pk = data_dict.id;
            mod_MCH_dict.show_err_msg = false;
            mod_MCH_dict.has_changes = false;

            MCH_Hide_Inputboxes();

    // show modal
            $("#id_mod_comphours").modal({backdrop: true});
        };
    };  // MCH_Open

//=========  MCH_InputChange  ================ PR2023-03-22
    function MCH_InputChange(el_input) {
        console.log(" -----  MCH_InputChange   ----")
        console.log("    el_input", el_input)
        mod_MCH_dict.has_changes = true;
        MCH_Hide_Inputboxes();
    };  // MCH_InputChange

//=========  MCH_AddDelete  ================ PR2023-03-22
    function MCH_AddDelete(mode) {
        console.log(" -----  MCH_AddDelete   ----")
        console.log("    mode", mode);
        console.log("    meeting_count", mod_MCH_dict.meeting_count);

        if (mode === "add"){
            if (mod_MCH_dict.meeting_count < 2) {
                mod_MCH_dict.meeting_count += 1;
            };
        } else {
            if (mod_MCH_dict.meeting_count) {
                if (mod_MCH_dict.meeting_count === 2){
                    el_MCH_meetingdate2.value = null;
                } else if (mod_MCH_dict.meeting_count === 1){
                    el_MCH_meetingdate1.value = null;
                };
                mod_MCH_dict.meeting_count -= 1;

                mod_MCH_dict.has_changes = true;
            };
        };
        MCH_Hide_Inputboxes()
    };  // MCH_AddDelete


//=========  MCH_Save  ================ PR2023-03-22
    function MCH_Save() {
        console.log(" -----  MCH_Save   ----")

        mod_MCH_dict.show_err_msg = true;
        const enable_save_btn = MCH_Hide_Inputboxes();

        if (enable_save_btn){
            const data_dict = mod_MCH_dict.data_dict;
        console.log("    data_dict", data_dict)
            const usercompensation_pk = data_dict.uc_id;

            const new_uc_meetings = mod_MCH_dict.meeting_count;
            const new_uc_meetingdate1 = (el_MCH_meetingdate1.value) ? el_MCH_meetingdate1.value : null;
            const new_uc_meetingdate2 = (el_MCH_meetingdate2.value) ? el_MCH_meetingdate2.value : null;
            let data_has_changed = false;

            const upload_dict = {mode: "update",
                                usercompensation_pk: usercompensation_pk};
            if (new_uc_meetings !== data_dict.uc_meetings){
                upload_dict.meetings = new_uc_meetings;
                data_has_changed = true;
            };
            if (new_uc_meetingdate1 !== data_dict.uc_meetingdate1){
                upload_dict.meetingdate1 = new_uc_meetingdate1;
                data_has_changed = true;
            };
            if (new_uc_meetingdate2 !== data_dict.uc_meetingdate2){
                upload_dict.meetingdate2 = new_uc_meetingdate2;
                data_has_changed = true;
            };
            if (data_has_changed){

        // ---  create mod_dict
                const url_str = urls.url_usercompensation_upload;

        // ---  upload changes
                UploadChanges(upload_dict, url_str);

        // --- hide modal
            $("#id_mod_comphours").modal("hide");

            };
        };
    };  // MCH_Save

//=========  MCH_Hide_Inputboxes  ================ PR2023-03-22
    function MCH_Hide_Inputboxes() {
        console.log(" -----  MCH_Hide_Inputboxes   ----")
        console.log("    mod_MCH_dict.meeting_count", mod_MCH_dict.meeting_count);
        console.log("    mod_MCH_dict.show_err_msg", mod_MCH_dict.show_err_msg);
        console.log("    mod_MCH_dict.has_changes", mod_MCH_dict.has_changes);

        add_or_remove_class(el_MCH_meetingdate1.parentNode, cls_hide, (!mod_MCH_dict.meeting_count));
        add_or_remove_class(el_MCH_meetingdate2.parentNode, cls_hide, (mod_MCH_dict.meeting_count < 2), false);
        add_or_remove_class(el_MCH_msg.parentNode, cls_hide, (mod_MCH_dict.meeting_count < 2), false);

        const min_date = setting_dict.sel_examyear_code + "-04-01";
        const max_date = setting_dict.sel_examyear_code + "-08-31";
        el_MCH_meetingdate1.setAttribute("min", min_date);
        el_MCH_meetingdate1.setAttribute("max", max_date);
        el_MCH_meetingdate2.setAttribute("min", min_date);
        el_MCH_meetingdate2.setAttribute("max", max_date);



        el_MCH_btn_add.disabled  = (mod_MCH_dict.meeting_count > 1);
        el_MCH_btn_delete.disabled = (!mod_MCH_dict.meeting_count);

        const has_err_date01 = (mod_MCH_dict.show_err_msg && mod_MCH_dict.meeting_count && !el_MCH_meetingdate1.value);
        const has_err_date02 = (mod_MCH_dict.show_err_msg && mod_MCH_dict.meeting_count > 1 && !el_MCH_meetingdate2.value);

        const show_err_msg_date01 = (mod_MCH_dict.show_err_msg && has_err_date01);
        const show_err_msg_date02 = (mod_MCH_dict.show_err_msg && has_err_date02);

        add_or_remove_class(el_MCH_meetingdate1, "border_bg_invalid", show_err_msg_date01);
        add_or_remove_class(el_MCH_meetingdate2, "border_bg_invalid", show_err_msg_date02);

        add_or_remove_class(el_MCH_err_date01.parentNode, cls_hide, !show_err_msg_date01);
        add_or_remove_class(el_MCH_err_date02.parentNode, cls_hide, !show_err_msg_date02);

        const enable_save_btn =  mod_MCH_dict.has_changes && !has_err_date01 && !has_err_date02
        el_MCH_btn_save.disabled  = !enable_save_btn;

        return enable_save_btn;
    };  // MCH_Hide_Inputboxes


// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++

//=========  ModConfirmOpen_DownloadUserdata  ================ PR2023-01-31
    function ModConfirmOpen_DownloadUserdata(mode ) {
        console.log(" -----  ModConfirmOpen_DownloadUserdata   ----")

// variables for future use in other functions
        console.log("    mode", mode);
        const may_edit = true;
        const show_modal = true;
        const show_large_modal = true;

// ---  create mod_dict
        mod_dict = {mode: mode};

 // ---  put text in modal for
        let header_txt = "";
        const msg_list = [];
        let caption_save = loc.OK;
        let hide_save_btn = false;

        header_txt = loc.Download_user_data;
        caption_save = loc.Yes_download;
        msg_list.push("<p>" + loc.The_user_data + loc.will_be_downloaded_plur + "</p><p>");
        msg_list.push("<p>" +  loc.Do_you_want_to_continue + "</p>");

        el_confirm_header.innerText = header_txt;
        el_confirm_loader.classList.add(cls_visible_hide);
        el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");

        el_confirm_msg_container.innerHTML = msg_list.join("");

        el_confirm_btn_save.innerText = caption_save;
        add_or_remove_class (el_confirm_btn_save, cls_hide, hide_save_btn);

        //add_or_remove_class (el_confirm_btn_save, "btn-primary", (mode !== "delete"));
        add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", (mode === "delete_candidate"), "btn-primary");

        el_confirm_btn_cancel.innerText = (hide_save_btn) ? loc.Close : loc.No_cancel;

// set focus to cancel button
        set_focus_on_el_with_timeout(el_confirm_btn_cancel, 150);

// show modal
        if (show_modal) {
            $("#id_mod_confirm").modal({backdrop: true});

            // this code must come after $("#id_mod_confirm"), otherwise it will not work
            add_or_remove_class(document.getElementById("id_mod_confirm_size"), "modal-md", show_large_modal, "modal-md");
        };
    };  // ModConfirmOpen_DownloadUserdata

//=========  ModConfirmOpen  ================ PR2020-08-03 PR2021-06-30 PR2022-12-31
    function ModConfirmOpen(tblName, mode, el_input, user_without_userallowed) {
        console.log(" -----  ModConfirmOpen   ----")
        // values of mode are : "delete", "is_active" or "send_activation_email", "permission_admin", "user_without_userallowed"

        // ModConfirmOpen(null, "user_without_userallowed", null, response.user_without_userallowed);
        console.log("    mode", mode )
        console.log("    tblName", tblName )

// ---  get selected_pk
        let selected_pk = null;
        // tblRow is undefined when clicked on delete btn in submenu btn or form (no inactive btn)
        const tblRow = t_get_tablerow_selected(el_input);
        if(tblRow){
            selected_pk = get_attr_from_el_int(tblRow, "data-pk")
        } else {
            selected_pk = selected_user_pk;
        }
        console.log("    tblRow", tblRow )
        console.log("    selected_pk", selected_pk )

// --- get data_dict from tblName and selected_pk
        const data_dict = get_datadict_from_pk(tblName, selected_pk)
        console.log("data_dict", data_dict);

// ---  get info from data_dict
        // TODO remove requsr_pk from client
        const is_request_user = (data_dict && permit_dict.requsr_pk && permit_dict.requsr_pk === data_dict.id)
        console.log("    is_request_user", is_request_user)

// ---  create mod_dict
        mod_dict = {mode: mode, table: tblName};
        const has_selected_item = (!isEmpty(data_dict));
        if(has_selected_item){
            mod_dict.mapid = data_dict.mapid;

            mod_dict.user_pk = data_dict.id;
            mod_dict.user_ppk = data_dict.schoolbase_id;

        };
       console.log("    mod_dict", mod_dict);

// ---  put text in modal form
        let dont_show_modal = false;
        const is_mode_permission_admin = (mode === "permission_admin");
        const is_mode_send_activation_email = (mode === "send_activation_email");

        const header_text = (mode === "delete") ? loc.Delete_user :
                            (mode === "user_without_userallowed") ? loc.Add_user :
                            (is_mode_send_activation_email) ? loc.Send_activation_email :
                            (is_mode_permission_admin) ? loc.Set_permissions : "";

        let msg_list = [];
        let hide_save_btn = false;
        if (!has_selected_item){
            msg_list.push("<p>" + loc.No_user_selected + "</p>");
            hide_save_btn = true;
        } else {

            const username = (data_dict.username) ? data_dict.username  : "-";
            if(mode === "delete"){
                if(is_request_user){
                    msg_list.push("<p>" + loc.Sysadm_cannot_delete_own_account + "</p>");
                    hide_save_btn = true;
                } else {
                    msg_list.push(["<p>", loc.User + " '" + username + "'", loc.will_be_deleted, "</p>"].join(""));
                    msg_list.push("<p>" + loc.Do_you_want_to_continue + "</p>");
                }
            } else if(is_mode_permission_admin){
                hide_save_btn = true;
                const fldName = get_attr_from_el(el_input, "data-field")
                if (fldName === "group_admin") {
                    msg_list.push("<p>" + loc.Sysadm_cannot_remove_sysadm_perm + "</p>");
                }
            }

        }
        if(!dont_show_modal){
            el_confirm_header.innerText = header_text;
            el_confirm_loader.classList.add(cls_visible_hide)
            el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");

            const msg_html = (msg_list.length) ? msg_list.join("") : null;
            el_confirm_msg_container.innerHTML = msg_html;

            //el_confirm_msg_container.classList.add("border_bg_transparent");

            const caption_save = (mode === "delete") ? loc.Yes_delete : loc.OK;
            el_confirm_btn_save.innerText = caption_save;
            add_or_remove_class (el_confirm_btn_save, cls_hide, hide_save_btn);

            add_or_remove_class (el_confirm_btn_save, "btn-primary", (mode !== "delete"));
            add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", (mode === "delete"));

            const caption_cancel = (mode === "delete") ? loc.No_cancel :
                            (mode === "is_active") ? loc.No_cancel :
                            (is_mode_send_activation_email) ? loc.No_cancel : loc.Cancel;

            el_confirm_btn_cancel.innerText = (has_selected_item && !is_mode_permission_admin) ? caption_cancel : loc.Close;

    // set focus to cancel button
            set_focus_on_el_with_timeout(el_confirm_btn_cancel, 150);

// show modal
            $("#id_mod_confirm").modal({backdrop: true});
        };
    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2019-06-23
    function ModConfirmSave() {
        console.log(" --- ModConfirmSave --- ");
        console.log("    mod_dict: ", mod_dict);
        let tblRow = document.getElementById(mod_dict.mapid);

// ---  when delete: make tblRow red, before uploading
        if (tblRow && mod_dict.mode === "delete"){
            ShowClassWithTimeout(tblRow, "tsa_tr_error");
        }

        let close_modal = false, skip_uploadchanges = false, url_str = null;
        const upload_dict = {mode: mod_dict.mode, mapid: mod_dict.mapid};

        if (mod_dict.mode === "user_without_userallowed"){
            url_str = urls.url_user_upload;

            upload_dict.user_pk = mod_dict.user_pk;
            upload_dict.schoolbase_pk = mod_dict.schoolbase_pk;
            upload_dict.username = mod_dict.username;
            upload_dict.schoolbase_pk

            close_modal = true;

        };
// ---  Upload changes
        if (!skip_uploadchanges){
            UploadChanges(upload_dict, url_str);
        };

// ---  hide modal
        if(close_modal) {

            $("#id_mod_confirm").modal("hide");
        };
    };  // ModConfirmSave

//=========  ModConfirmResponse  ================ PR2019-06-23
    function ModConfirmResponse(response) {
        //console.log(" --- ModConfirmResponse --- ");
        //console.log("mod_dict: ", mod_dict);
        // hide loader
        el_confirm_loader.classList.add(cls_visible_hide);
        const mode = get_dict_value(response, ["mode"]);
        if(mode === "delete"){
//--- delete tblRow. Multiple deleted rows not in use yet, may be added in the future PR2020-08-18
            if ("updated_list" in response) {
                for (let i = 0, updated_dict; updated_dict = response.updated_list[i]; i++) {
                    if(updated_dict.deleted) {
                        const tblRow = document.getElementById(updated_dict.mapid);
                        if (tblRow){ tblRow.parentNode.removeChild(tblRow) };
                    };
                };
            };
        };
        if ("msg_err" in response || "msg_ok" in response) {
            let msg_list = [];
            if ("msg_err" in response) {
                const msg_err = get_dict_value(response, ["msg_err", "msg01"]);
                if (msg_err) {msg_list.push("<p>" + msg_err + "</p>")};
                if (mod_dict.mode === "send_activation_email") {
                    msg_list.push("<p>" + loc.Activation_email_not_sent + "</p>")
                };
                el_confirm_msg_container.classList.add("border_bg_invalid");
            } else if ("msg_ok" in response){
                const msg01 = get_dict_value(response, ["msg_ok", "msg01"]);
                const msg02 = get_dict_value(response, ["msg_ok", "msg02"]);
                const msg03 = get_dict_value(response, ["msg_ok", "msg03"]);
                if (msg01) {msg_list.push("<p>" + msg01 + "</p>")};
                if (msg02) {msg_list.push("<p>" + msg02 + "</p>")};
                if (msg03) {msg_list.push("<p>" + msg03 + "</p>")};
                el_confirm_msg_container.classList.add("border_bg_valid");
            };

            const msg_html = (msg_list.length) ? msg_list.join("") : null;
            el_confirm_msg_container.innerHTML = msg_html;

            el_confirm_btn_cancel.innerText = loc.Close;
            el_confirm_btn_save.classList.add(cls_hide);
        } else {
        // hide mod_confirm when no message
            $("#id_mod_confirm").modal("hide");
        };
    };  // ModConfirmResponse

//###########################################################################

// +++++++++++++++++ REFRESH DATA ROWS ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataRows  ================ PR2021-08-01
    function RefreshDataRows(page_tblName, update_rows, data_rows, is_update) {
        console.log(" --- RefreshDataRows  ---");
        //console.log("page_tblName", page_tblName);
        console.log("    update_rows", update_rows);
        console.log("    data_rows", data_rows);
        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length

        if (update_rows && update_rows.length ) {
            //const field_setting = field_settings[page_tblName];

            const field_setting = field_settings[selected_btn];
            //console.log("field_setting", field_setting);
            for (let i = 0, update_dict; update_dict = update_rows[i]; i++) {
                RefreshDatarowItem(page_tblName, field_setting, update_dict, data_rows);
            }
        } else if (!is_update) {
            // empty the data_rows when update_rows is empty PR2021-01-13 debug forgot to empty data_rows
            // PR2021-03-13 debug. Don't empty de data_rows when is update. Returns [] when no changes made
           data_rows = [];
        }
    }  //  RefreshDataRows

//=========  RefreshDatarowItem  ================ PR2020-08-16 PR2020-09-30 PR2021-06-21 PR2022-03-04 PR2023-01-04
    function RefreshDatarowItem(tblName, field_setting, update_dict, data_rows) {
        console.log(" --- RefreshDatarowItem  ---");
        //console.log("tblName", tblName);
        console.log("field_setting", field_setting);
        console.log("update_dict", update_dict);
        console.log("update_dict.err_fields", update_dict.err_fields);

        const data_dicts = get_datadicts_from_selectedBtn();

        if(data_dicts && !isEmpty(update_dict)){
            const field_names = field_setting.field_names;
            const map_id = update_dict.mapid;

        console.log("field_names", field_names);
        console.log("map_id", map_id);
        console.log("update_dict", update_dict);
        console.log("update_dict.mapid", update_dict.mapid);

    // ---  get list of hidden columns
        const col_hidden = b_copy_array_to_new_noduplicates(mod_MCOL_dict.cols_hidden);

    // ---  get list of columns that are not updated because of errors
            const error_columns = [];
            if (update_dict.err_fields){
                // replace field 'subj_auth2by' by 'subj_status'
                for (let i = 0, err_field; err_field = update_dict.err_fields[i]; i++) {
                    if (err_field && err_field.includes("_auth")){
                        const arr = err_field.split("_");
                        err_field = arr[0] + "_status";
                    };
                    error_columns.push(err_field);
                };
            };

// ++++ created ++++
    // - rows cannot be created in this page

// +++ get existing data_dict
            const data_dict = data_dicts[map_id];

// ++++ deleted ++++
    // - rows cannot be deleted in this page

// +++++++++++ updated row +++++++++++
// ---  check which fields are updated, add to list 'updated_columns'
            if(!isEmpty(data_dict) && field_names){

// ---  first add updated fields to updated_columns list, before updating data_row
                let updated_columns = [];
                // first column subj_error
                for (let i = 0, col_field, old_value, new_value; col_field = field_names[i]; i++) {

// ---  'status' fields are not in data_row
                    if (col_field === "status"){
                        const old_status_className = f_get_status_auth12_iconclass(data_dict.uc_published_id, false, data_dict.uc_auth1by_id, data_dict.uc_auth2by_id);
                        const new_status_className = f_get_status_auth12_iconclass(update_dict.uc_published_id, false, update_dict.uc_auth1by_id, update_dict.uc_auth2by_id);
                        if (old_status_className !== new_status_className) {
                            updated_columns.push(col_field)
                        };
                    } else if (col_field in data_dict && col_field in update_dict){
                        if (data_dict[col_field] !== update_dict[col_field] ) {
                            updated_columns.push(col_field)
                        };
                    };
                };

// ---  update fields in data_row
                for (const [key, new_value] of Object.entries(update_dict)) {
                    if (key in data_dict){
                        const old_value = data_dict[key];
                        if (new_value !== data_dict[key]) {
                            data_dict[key] = new_value;
                        };
                    };
                };

// ---  update field in tblRow
                // note: when updated_columns is empty, then updated_columns is still true.
                // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
                // PR2021-09-29 always update all columns, to remove strikethrough after undelete
                // was: if(updated_columns.length || field_error_list.length){

// --- get existing tblRow
                let tblRow = document.getElementById(map_id);
                if(tblRow){
// - loop through cells of row
                    for (let i = 1, el_fldName, el, td; td = tblRow.cells[i]; i++) {
                        el = td.children[0];
                        if (el){
                            el_fldName = get_attr_from_el(el, "data-field");
                            const is_updated_field = updated_columns.includes(el_fldName);
                            const is_err_field = error_columns.includes(el_fldName);

// - update field and make field green when field name is in updated_columns
                            if(is_updated_field){
                                UpdateField(el, update_dict);
                            };
                            if(is_updated_field){ShowOkElement(el)};
                            if(is_err_field){
// - make field red when error and reset old value after 2 seconds
                                reset_element_with_errorclass(el, update_dict)
        }}}}}};
    };  // RefreshDatarowItem

//=========  reset_element_with_errorclass  ================ PR2021-09-20
    function reset_element_with_errorclass(el_input, update_dict) {
        // make field red when error and reset old value after 2 seconds
        const err_class = "border_bg_invalid";
        el_input.classList.add(err_class);
        setTimeout(function (){
            el_input.classList.remove(err_class);
            UpdateField(el_input, update_dict);
        }, 2000);
    }  //  reset_element_with_errorclass
//###########################################################################
// +++++++++++++++++ FILTER ++++++++++++++++++++++++++++++++++++++++++++++++++

//========= HandleFilterKeyup  ================= PR2021-03-23
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
        };
    }; // function HandleFilterKeyup


//========= HandleFilterToggle  =============== PR2020-07-21 PR2020-09-14 PR2021-03-23 PR2022-02-28
    function HandleFilterToggle(el_input) {
        //console.log( "===== HandleFilterToggle  ========= ");

        // PR2021-05-30 debug: use cellIndex instead of attribute data-colindex,
        // because data-colindex goes wrong with hidden columns
        // was:  const col_index = get_attr_from_el(el_input, "data-colindex")
        const col_index = el_input.parentNode.cellIndex;
    //console.log( "col_index", col_index);

    // - get col_index and filter_tag from  el_input
        const filter_tag = get_attr_from_el(el_input, "data-filtertag")
        const field_name = get_attr_from_el(el_input, "data-field")
    //console.log( "filter_tag", filter_tag);
    //console.log( "field_name", field_name);

    // - get current value of filter from filter_dict, set to '0' if filter doesn't exist yet
        const filter_array = (col_index in filter_dict) ? filter_dict[col_index] : [];
        const filter_value = (filter_array[1]) ? filter_array[1] : "0";
        let new_value = "0", icon_class = "tickmark_0_0"
        if(field_name === "is_active") {
// - toggle filter value
            // default filter inactive '0'; is show all, '1' is show active only, '2' is show inactive only
            // default filter inactive '0'; is show active only, '1' is show all, '2' is show inactive only
            new_value = (filter_value === "2") ? "0" : (filter_value === "1") ? "2" : "1";
// - get new icon_class
            icon_class =  (new_value === "2") ? "inactive_1_3" : (new_value === "1") ? "inactive_0_2" : "inactive_0_0";

        } else if(filter_tag === "toggle") {
            // default filter triple '0'; is show all, '1' is show tickmark, '2' is show without tickmark
// - toggle filter value
            new_value = (filter_value === "2") ? "0" : (filter_value === "1") ? "2" : "1";
// - get new icon_class
            icon_class =  (new_value === "2") ? "tickmark_2_1" : (new_value === "1") ? "tickmark_2_2" : "tickmark_0_0";
        }

    // - put new filter value in filter_dict
        filter_dict[col_index] = [filter_tag, new_value]

    //console.log( "filter_dict", filter_dict);
        el_input.className = icon_class;
        Filter_TableRows();
    };  // HandleFilterToggle


//========= Filter_TableRows  ====================================
    function Filter_TableRows() {  // PR2019-06-09 PR2020-08-31 PR2022-03-03
        //console.log( "===== Filter_TableRows=== ");
        //console.log( "filter_dict", filter_dict);

        // function filters by inactive and substring of fields
        //  - iterates through cells of tblRow
        //  - skips filter of new row (new row is always visible)
        //  - if filter_name is not null:
        //       - checks tblRow.cells[i].children[0], gets value, in case of select element: data-value
        //       - returns show_row = true when filter_name found in value
        //  - if col_inactive has value >= 0 and hide_inactive = true:
        //       - checks data-value of column 'inactive'.
        //       - hides row if inactive = true

        const data_inactive_field = null; //  "data-inactive";
        for (let i = 0, tblRow, show_row; tblRow = tblBody_datatable.rows[i]; i++) {
            tblRow = tblBody_datatable.rows[i]
            show_row = t_Filter_TableRow_Extended(filter_dict, tblRow, data_inactive_field);
            add_or_remove_class(tblRow, cls_hide, !show_row);
        };
    }; // Filter_TableRows

//========= ShowTableRow  ==================================== PR2020-08-17
    function ShowTableRow(tblRow, tblName_settings) {
        // only called by Filter_TableRows
        //console.log( "===== ShowTableRow  ========= ");
        let hide_row = false;
        if (tblRow){
// show all rows if filter_name = ""
            if (!isEmpty(filter_dict)){
                for (let i = 1, el_fldName, el; el = tblRow.cells[i]; i++) {
                    const filter_text = filter_dict[i];
                    const filter_tag = field_settings[tblName_settings].filter_tags[i];
                // skip if no filter on this colums
                    if(filter_text){
                        if(filter_tag === "text"){
                            const blank_only = (filter_text === "#")
                            const non_blank_only = (filter_text === "@" || filter_text === "!")
                // get value from el.value, innerText or data-value
                            // PR2020-06-13 debug: don't use: "hide_row = (!el_value)", once hide_row = true it must stay like that
                            let el_value = el.innerText;
                            if (blank_only){
                                // empty value gets '\n', therefore filter asc code 10
                                if(el_value && el_value !== "\n" ){
                                    hide_row = true
                                };
                            } else if (non_blank_only){
                                // empty value gets '\n', therefore filter asc code 10
                                if(!el_value || el_value === "\n" ){
                                    hide_row = true
                                }
                            } else {
                                el_value = el_value.toLowerCase();
                                // hide row if filter_text not found or el_value is empty
                                // empty value gets '\n', therefore filter asc code 10
                                if(!el_value || el_value === "\n" ){
                                    hide_row = true;
                                } else if(!el_value.includes(filter_text)){
                                    hide_row = true;
                                }
                            }
                        } else if(filter_tag === "toggle"){
                            const el_value = get_attr_from_el_int(el, "data-value")
                            if (filter_text === 1){
                                if (!el_value ) {hide_row = true};
                            } else  if (filter_text === -1){
                                if (el_value) {hide_row = true};
                            }
                        }
                    }  //  if(!!filter_text)
                }  // for (let i = 1, el_fldName, el; el = tblRow.cells[i]; i++) {
            }  // if if (!isEmpty(filter_dict))
        }  // if (!!tblRow)
        return !hide_row
    }; // ShowTableRow

//========= ResetFilterRows  ====================================
    function ResetFilterRows() {  // PR2019-10-26 PR2020-06-20
       //console.log( "===== ResetFilterRows  ========= ");

        selected_user_pk = null;

        filter_dict = {};
        filter_mod_employee = false;

        Filter_TableRows(true);  // true = set filter isactive

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
    }  // function ResetFilterRows

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL SELECT EXAMYEAR OR DEPARTMENT  ++++++++++++++++++++
// functions are in table.js, except for MSED_Response

//=========  MSED_Response  ================ PR2020-12-18 PR2021-05-10 PR2022-12-02
    function MSED_Response(new_setting) {
        console.log( "===== MSED_Response ========= ");
        console.log( "new_setting", new_setting);

// ---  upload new selected_pk
        new_setting.page = setting_dict.sel_page;
// also retrieve the tables that have been changed because of the change in examyear / dep
        const datalist_request = {
                setting: new_setting,

                department_rows: {get: true},

                // PR2023-05-08 was: school_rows: {skip_allowed_filter: true}, level_rows: {skip_allowed_filter: true}
                school_rows: {get: true},
                level_rows: {get: true},

                subject_rows_page_users: {get: true},
                cluster_rows: {page: "page_corrector"}
            };

        DatalistDownload(datalist_request);

    }  // MSED_Response

//###########################################################################

// +++++++++++++++++ MODAL SELECT MULTIPLE CLUSTERS ++++++++++++++++++++++++++++++++++++++++++
//========= MSM_Open ====================================  PR2022-01-26 PR2023-01-26
    function MSM_Open (el_input) {
        console.log(" ===  MSM_Open  =====") ;

        b_clear_dict(mod_MSM_dict)

        const tblRow = t_get_tablerow_selected(el_input);
        const has_permit = (permit_dict.permit_crud && permit_dict.requsr_same_school);
        if(tblRow && has_permit){

// --- get existing data_dict from data_rows
            const pk_int = get_attr_from_el_int(tblRow, "data-pk")
              const data_dict = corrector_dicts["user_" + pk_int];

    console.log("    data_dict", data_dict)

            // fldName = allowed_clusters

            mod_MSM_dict.user_pk = data_dict.id;
            mod_MSM_dict.ual_pk = data_dict.ual_id;
            mod_MSM_dict.schoolbase_pk = data_dict.schoolbase_id;
            mod_MSM_dict.mapid = data_dict.mapid;

            // allowed_clusters = ""ac - 4A1, ac - 4VA1, ac - 4VA2,"
            mod_MSM_dict.allowed_clusters = data_dict.allowed_clusters;
            mod_MSM_dict.allowed_clusters_pk_arr = data_dict.allowed_clusters_pk;

    // ---  set header text
            const header_text = loc.Select + loc.Clusters.toLowerCase() + ":";
            document.getElementById("id_MSM_hdr_multiple").innerText = header_text;

            const hide_msg = (get_attr_from_el(el_input, "data-field") === "allowed_clusters");
            add_or_remove_class_by_id ("id_MSM_message_container", cls_hide, hide_msg);

            el_MSM_input.value = null;

    // ---  fill select table 'customer'
            MSM_FillSelectTable();

    // ---  Set focus to el_MSM_input
            //Timeout function necessary, otherwise focus wont work because of fade(300)
            setTimeout(function (){ el_MSM_input.focus() }, 50);
    // ---  show modal
             $("#id_mod_select_multiple").modal({backdrop: true});
        }
    }; // MSM_Open

//=========  MSM_Save  ================ PR2022-01-26 PR2023-01-27
    function MSM_Save() {
        console.log("===  MSM_Save =========");

        const has_permit = (permit_dict.permit_crud && permit_dict.requsr_same_school);

        console.log("    has_permit", has_permit);
        console.log("    permit_dict", permit_dict);

        if(has_permit){

            let new_array = [];
            let allowed_str = ""
            const tblBody_select = el_MSM_tblbody_select;
            for (let i = 0, row; row = tblBody_select.rows[i]; i++) {
                const base_pk_int = get_attr_from_el_int(row, "data-pk")
                if(base_pk_int > 0) {
                    const is_selected = (!!get_attr_from_el_int(row, "data-selected"))
                    if(is_selected){
                        new_array.push(base_pk_int);

                    };
                }
            }
            if(new_array){
                // PR2020-11-02 from https://www.w3schools.com/js/js_array_sort.asp
                new_array.sort(function(a, b){return a - b});
            };

    // ---  upload changes
            // mod_MSM_dict = user_data_dict with additional keys
            const upload_dict = {  mode: "update",
                                    user_pk: mod_MSM_dict.user_pk,
                                    ual_pk: mod_MSM_dict.ual_pk,
                                    allowed_clusters: (new_array.length) ? new_array : null
                                };

            UploadChanges(upload_dict, urls.url_userallowedcluster_upload);
        };
// hide modal
        $("#id_mod_select_multiple").modal("hide");
    }  // MSM_Save

//=========  MSM_InputKeyup  ================ PR2020-11-02
    function MSM_InputKeyup(el_input) {
        //console.log( "=== MSM_InputKeyup === ")
        //console.log( "el_input.value:  ", el_input.value)

        let tblBody_select = el_MSM_tblbody_select;

        const new_filter = el_input.value
        if (tblBody_select.rows.length){
// ---  filter select rows
            const col_index_list = [1];
            t_Filter_SelectRows(tblBody_select, new_filter, false, false, null, col_index_list);
        }
    }  // MSM_InputKeyup

//=========  MSM_FillSelectTable  ================ PR2022-01-26 PR23-01-26
    function MSM_FillSelectTable() {
        //console.log( "===== MSM_FillSelectTable ========= ");

        // check if school has multiple departments, needed for allowed_clusters
        let school_has_multiple_deps = false;
        if (setting_dict.sel_school_depbases ){
            const depbase_arr = setting_dict.sel_school_depbases.split(";");
            school_has_multiple_deps = depbase_arr && depbase_arr.length > 1;
        };
    //console.log( "    setting_dict.sel_school_depbases: ", setting_dict.sel_school_depbases);
    //console.log( "    school_has_multiple_deps: ", school_has_multiple_deps);

        // cluster has no base table
        const base_pk_field = "id"
        const caption_none = loc.No_ + loc.Clusters.toLowerCase();

        let tblBody_select = el_MSM_tblbody_select;
        tblBody_select.innerText = null;

        let has_selected_rows = false;

// --- loop through data_rows
        // data_array contains a list of strings with cluster_id's
        console.log( "    mod_MSM_dict.allowed_clusters: ", mod_MSM_dict.allowed_clusters);
        const allowed_clusters_pk_arr = (mod_MSM_dict.allowed_clusters_pk_arr) ? mod_MSM_dict.allowed_clusters_pk_arr : [];

        //console.log( "    allowed_clusters_pk_arr: ", allowed_clusters_pk_arr);

        for (const data_dict of Object.values(cluster_dictsNEW)) {
    //console.log( "    data_dict: ", data_dict)
            const pk_int = data_dict.id;
            const row_is_selected = (pk_int && allowed_clusters_pk_arr && allowed_clusters_pk_arr.includes(pk_int));

    //console.log( "    pk_int: ", pk_int);
    //console.log( "   ==== row_is_selected: ", row_is_selected);
            if(row_is_selected){
                has_selected_rows = true;
            };

            const row_index = -1;
            MSM_FillSelectRow(tblBody_select, data_dict, row_is_selected);
        };

    //console.log( "  >>>>>>>>>>   has_selected_rows: ", has_selected_rows);

// ---  add 'all' at the beginning of the list, with id = 0, make selected if no other rows are selected
        //const data_dict = {};
        //data_dict.id = -9;
        //data_dict.name = "<" + loc.All_ + loc.Clusters.toLowerCase() + ">"

        //const row_index = 0;
        // select <All> when has_selected_rows = false;
        //MSM_FillSelectRow(tblBody_select, data_dict, !has_selected_rows, true)  // true = insert_at_index_zero

    }  // MSM_FillSelectTable

//=========  MSM_FillSelectRow  ================ PR2022-01-26
    function MSM_FillSelectRow(tblBody_select, data_dict, row_is_selected, insert_at_index_zero) {
        //console.log( "===== MSM_FillSelectRow ========= ");
        //console.log("data_dict: ", data_dict);

        // cluster has no base table
        const pk_int = data_dict.id;
        const display_name = (data_dict.name) ? data_dict.name : "-";

    //console.log( "display_name: ", display_name);

        const map_id = (data_dict.mapid) ? data_dict.mapid : null;

// ---  lookup index where this row must be inserted
        //const ob1 = (data_dict.dep_sequence) ? "00000" + data_dict.dep_sequence.toString() : "";
        const ob1 = (data_dict.name) ? data_dict.name.toLowerCase() : "";

        const row_index = (insert_at_index_zero) ? 0 :
            b_recursive_tblRow_lookup(tblBody_select, setting_dict.user_lang, ob1);

// --- insert tblRow into tblBody at row_index
        const tblRow = tblBody_select.insertRow(row_index);
        tblRow.id = map_id

        tblRow.setAttribute("data-pk", pk_int);
        tblRow.setAttribute("data-selected", (row_is_selected) ? "1" : "0")

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);
        //tblRow.setAttribute("data-ob2", ob2);

// ---  add EventListener to tblRow, not when 'no items' (pk_int is then -1, ''all clusters = -9
        if (pk_int !== -1) {
            tblRow.addEventListener("click", function() {MSM_SelecttableClicked(tblRow)}, false )
// ---  add hover to tblRow
            add_hover(tblRow);
        }
        let td, el;

// ---  add select td to tblRow.
        td = tblRow.insertCell(-1);
            td.classList.add("mx-1", "tw_032")

// --- add a element to td., necessary to get same structure as item_table, used for filtering
            el = document.createElement("div");
                el.className = (row_is_selected) ? "tickmark_2_2" : "tickmark_0_0";
            td.appendChild(el);

// ---  add td with display_name to tblRow
        td = tblRow.insertCell(-1);
            td.classList.add("mx-1", "tw_270")
// --- add a element to td., necessary to get same structure as item_table, used for filtering
        el = document.createElement("div");
            el.innerText = display_name;
        td.appendChild(el);
        if (display_name) { tblRow.title = display_name};

    };  // MSM_FillSelectRow

//=========  MSM_SelecttableClicked  ================ PR2022-01-26
    function MSM_SelecttableClicked(tblRow) {
        //console.log( "===== MSM_SelecttableClicked ========= ");
        //console.log("tblRow: ", tblRow);
        if(tblRow) {
            // toggle is_selected
            const is_selected = (!get_attr_from_el_int(tblRow, "data-selected"))

            tblRow.setAttribute("data-selected", (is_selected) ? "1" : "0")
            tblRow.cells[0].children[0].className = (is_selected) ? "tickmark_2_2" : "tickmark_0_0";

            // row 'all' has pk = -9
            if(is_selected){
                const selected_pk_int = get_attr_from_el_int(tblRow, "data-pk");
                const selected_is_all = (selected_pk_int === -9);
                const tblBody_select = tblRow.parentNode;
                for (let i = 0, lookup_row; lookup_row = tblBody_select.rows[i]; i++) {
                    const lookup_pk_int = get_attr_from_el_int(lookup_row, "data-pk");
                    if (lookup_pk_int !== selected_pk_int){
                        const lookup_is_all = (lookup_pk_int === -9);

                        // remove tickmark on all other items when 'all' is selected
                        // remove  tickmark on 'all' when other item is selected
                        //let remove_selected = (base_is_all) ? (lookup_base_pk_int !== -9) : (lookup_base_pk_int === -9);;
                        let remove_selected = (selected_is_all && !lookup_is_all) || (!selected_is_all && lookup_is_all);
                        if(remove_selected){
                            lookup_row.setAttribute("data-selected", "0");
                            lookup_row.cells[0].children[0].className = "tickmark_0_0";
                        };
                    };
                };
            };
        };
    };  // MSM_SelecttableClicked

// +++++++++++++++++ END OF MODAL SELECT MULTIPLE DEPS / LEVELS/ SUBJECTS / CLUSTERS  +++++++++++++++++++++++++++++++

//////////////////////////////////////


//=========  MSSSS_Response  ================ PR2021-04-23  PR2021-07-26
    function MSSSS_Response(tblName, selected_dict, selected_pk) {
        //console.log( "===== MSSSS_Response ========= ");

        // Note: when tblName = school: pk_int = schoolbase_pk
        if(selected_pk === -1) { selected_pk = null};

// ---  put new selected_pk in setting_dict
        setting_dict.sel_schoolbase_pk = selected_pk;

// ---  upload new setting and refresh page
        let datalist_request = {setting: {page: "page_corrector", sel_schoolbase_pk: selected_pk}};
        DatalistDownload(datalist_request);

    };  // MSSSS_Response


    function get_usercompensation_dict(tblRow){  // PR2023-03-23
        return  (tblRow && tblRow.id && tblRow.id in usercompensation_dicts)  ? usercompensation_dicts[tblRow.id]: null;
    };


})  // document.addEventListener('DOMContentLoaded', function()