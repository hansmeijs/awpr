// PR2020-07-30 added

// PR2021-09-22  these variables are declared in base.js to make them global variables
// declared as global: let selected_btn = null;
//let setting_dict = {};
//let permit_dict = {};
//let loc = {};
//let urls = {};

const field_settings = {};

let user_list = [];
let user_rows = [];


const userapproval_dicts = {}; //PR2023-02-24
const usercompensation_dicts = {}; //PR2023-02-24

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
    let mod_MUA_dict = {};
    let mod_MUPM_dict = {};
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
    urls.url_user_upload = get_attr_from_el(el_data, "data-user_upload_url");

    urls.url_user_allowedsections_upload = get_attr_from_el(el_data, "data-url_user_allowedsections_upload");

    urls.url_userpermit_upload = get_attr_from_el(el_data, "data-userpermit_upload_url");
    urls.url_download_permits = get_attr_from_el(el_data, "data-user_download_permits_url");
    urls.url_download_userdata_xlsx = get_attr_from_el(el_data, "data-url_download_userdata_xlsx");

    urls.url_usercompensation_upload = get_attr_from_el(el_data, "data-url_usercompensation_upload");

    // url_importdata_upload is stored in id_MIMP_data of modimport.html

    mod_MCOL_dict.columns.all = {
        user_sb_code: "Organization", last_name: "Name",
        depbase_code: "Department", lvlbase_code: "Learning_path",
        subj_name_nl:  "Subject", exam_version: "Version",
        uc_amount: "Number_approvals", uc_meetings: "Number_meetings"
    };
    mod_MCOL_dict.columns.btn_approval = {sb_code: "School_code", school_abbrev: "School"};
    mod_MCOL_dict.columns.btn_compensation = { compensation: "Compensation"};


// --- get field_settings
    field_settings.btn_approval = {
                    field_caption: ["", "Organization", "User", "Name",
                                    "Department", "Learning_path", "Subjectcode_2lines", "Subject", "Version", "Exam_period",
                                    "School_code", "School", "Number_approvals_2lines",  "Number_meetings_2lines", "Inactive"],
                    field_names: ["select", "user_sb_code", "username", "last_name",
                                    "depbase_code", "lvlbase_code", "subjbase_code", "subj_name_nl", "exam_version", "examperiod",
                                     "sb_code", "school_abbrev","uc_amount", "uc_meetings", "is_active"],
                    field_tags: ["div", "div", "div", "div",
                                    "div", "div", "div", "div", "div", "div",
                                     "div", "div","div", "input", "div"],
                    filter_tags: ["select", "text", "text",  "text",
                                    "text", "text",  "text",  "text", "text", "text",
                                     "text",  "text", "text",  "toggle",  "inactive"],
                    field_width:  ["020", "090", "150",  "180",
                                    "090", "090", "090", "220", "090",  "090",
                                    "090", "150", "150",  "150",  "090"],
                    field_align: ["c", "l", "l", "l",
                                    "c", "c", "c", "l",  "l", "c",
                                    "l", "l", "c",  "c",  "c"]};

    field_settings.btn_compensation = {
                    field_caption: ["", "Organization", "User", "Name",
                                    "Department", "Learning_path", "Subjectcode_2lines", "Subject", "Version", "Exam_period",
                                    "Number_approvals_2lines",  "Number_meetings_2lines", "Compensation", "Inactive"],
                    field_names: ["select", "user_sb_code", "username", "last_name",
                                    "depbase_code", "lvlbase_code", "subjbase_code", "subj_name_nl", "exam_version", "examperiod",
                                    "uc_amount", "uc_meetings", "compensation", "is_active"],
                    field_tags: ["div", "div", "div", "div",
                                    "div", "div", "div", "div", "div", "div",
                                    "div", "input","div", "div"],
                    filter_tags: ["select", "text", "text", "text",
                                    "text", "text",  "text",  "text", "text", "text",
                                    "text",  "toggle", "text", "inactive"],
                    field_width:  ["020", "090", "150",  "180",
                                    "090", "090", "090", "220", "090",  "090",
                                    "150",  "150", "150", "090"],
                    field_align: ["c", "l", "l", "l",
                                    "c", "c", "c", "l",  "l", "c",
                                        "c",  "c", "c", "c"]};


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
        const el_hdrbar_school = document.getElementById("id_hdrbar_school");
        const el_hdrbar_department = document.getElementById("id_hdrbar_department");

        if (el_hdrbar_examyear){
            el_hdrbar_examyear.addEventListener("click",
                function() {t_MSED_Open(loc, "examyear", examyear_map, setting_dict, permit_dict, MSED_Response)}, false );
        };
        if (el_hdrbar_department){
            el_hdrbar_department.addEventListener("click",
                function() {t_MSED_Open(loc, "department", department_map, setting_dict, permit_dict, MSED_Response)}, false );
        };
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

// ---  MODAL USER SET ALLOWED SECTIONS
        const el_MUPS_username = document.getElementById("id_MUPS_username");
        const el_MUPS_loader = document.getElementById("id_MUPS_loader");

        const el_MUPS_tbody_container = document.getElementById("id_MUPS_tbody_container");
        const el_MUPS_tbody_select = document.getElementById("id_MUPS_tbody_select");

        const el_MUPS_btn_expand_all = document.getElementById("id_MUPS_btn_expand_all");
        if (el_MUPS_btn_expand_all){
            el_MUPS_btn_expand_all.addEventListener("click", function() {MUPS_ExpandCollapse_all()}, false);
        };
        const el_MUPS_btn_save = document.getElementById("id_MUPS_btn_save");
        if (el_MUPS_btn_save){
            el_MUPS_btn_save.addEventListener("click", function() {MUPS_Save("save")}, false);
        };
        const el_MUPS_btn_cancel = document.getElementById("id_MUPS_btn_cancel");

// ---  MSSS MOD SELECT SCHOOL SUBJECT STUDENT ------------------------------
        const el_MSSSS_input = document.getElementById("id_MSSSS_input");
        const el_MSSSS_tblBody = document.getElementById("id_MSSSS_tbody_select");
        const el_MSSSS_btn_save = document.getElementById("id_MSSSS_btn_save");
        if (el_MSSSS_input){
            el_MSSSS_input.addEventListener("keyup", function(event){
                setTimeout(function() {t_MSSSS_InputKeyup(el_MSSSS_input)}, 50)});
        };
        if (el_MSSSS_input){
            el_MSSSS_input.addEventListener("click", function() {t_MSSSS_Save(el_MSSSS_input, MSSSS_Response)}, false );
        };

// ---  MODAL USER
        const el_MUA_schoolname = document.getElementById("id_MUA_schoolname");
        const el_MUA_username = document.getElementById("id_MUA_username");
        const el_MUA_last_name = document.getElementById("id_MUA_last_name");
        const el_MUA_email = document.getElementById("id_MUA_email");
        const el_MUA_btn_delete = document.getElementById("id_MUA_btn_delete");
        const el_MUA_btn_submit = document.getElementById("id_MUA_btn_submit");
        const el_MUA_btn_cancel = document.getElementById("id_MUA_btn_cancel");
        const el_MUA_footer_container = document.getElementById("id_MUA_footer_container");
        const el_MUA_footer01 = document.getElementById("id_MUA_footer01");
        const el_MUA_footer02 = document.getElementById("id_MUA_footer02");
        const el_MUA_loader = document.getElementById("id_MUA_loader");
        const el_MUA_msg_modified = document.getElementById("id_MUA_msg_modified");

        if (el_MUA_schoolname){
            el_MUA_schoolname.addEventListener("keyup", function() {MUA_InputSchoolname(el_MUA_schoolname, event.key)}, false);
        };
        if (el_MUA_username){
            el_MUA_username.addEventListener("keyup", function() {MUA_InputKeyup(el_MUA_username, event.key)}, false);
        };
        if (el_MUA_last_name){
            el_MUA_last_name.addEventListener("keyup", function() {MUA_InputKeyup(el_MUA_last_name, event.key)}, false);
        };
        if (el_MUA_email){
            el_MUA_email.addEventListener("keyup", function() {MUA_InputKeyup(el_MUA_email, event.key)}, false);
        };
        if (el_MUA_btn_delete){
            el_MUA_btn_delete.addEventListener("click", function() {ModConfirmOpen("user", "delete")}, false);
        };
        if (el_MUA_btn_submit){
            el_MUA_btn_submit.addEventListener("click", function() {MUA_Save("validate")}, false);
        };

// ---  MODAL GROUP PERMISSION
        const el_MUPM_btn_delete = document.getElementById("id_MUPM_btn_delete");
        const el_MUPM_btn_submit = document.getElementById("id_MUPM_btn_submit");
        if (el_MUPM_btn_delete){
            el_MUPM_btn_delete.addEventListener("click", function() {MUPM_Save("delete")}, false);
        };
        if (el_MUPM_btn_submit){
            el_MUPM_btn_submit.addEventListener("click", function() {MUPM_Save("save")}, false);
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
                user_rows: {get: true},
                userapproval_rows: {get: true},
                // PR2023-01-06 was: department_rows: {skip_allowed_filter: true},
                department_rows: {get: true},
                school_rows: {skip_allowed_filter: true},
                level_rows: {skip_allowed_filter: true},
                subject_rows_page_users: {get: true},
                cluster_rows: {get: true},
            };

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
                if ("user_rows" in response) {
                    user_rows = response.user_rows;
                };
                if ("userapproval_rows" in response) {
                    // mapid : "usercomp_2897"
                    b_fill_datadicts("usercomp", "id", null, response.userapproval_rows, userapproval_dicts);
                };
                if ("usercompensation_rows" in response) {
                    // mapid : "user_exam__792_159"
                    b_fill_datadicts("user_exam", "u_id", "exam_id", response.usercompensation_rows, usercompensation_dicts);
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
                if ("cluster_rows" in response)  {
                    FillDatadicts("cluster", response.cluster_rows);
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


//=========  FillDatadicts  ===  PR2023-01-26
    function FillDatadicts(tblName, data_rows) {
        //console.log("===  FillDatadicts == ");
        //console.log("    tblName", tblName);
        //console.log("    data_rows", data_rows);

        const data_dicts = (tblName === "cluster") ? cluster_dictsNEW :  null;

        b_clear_dict(data_dicts);

        if (data_rows && data_rows.length){
            for (let i = 0, row; row = data_rows[i]; i++) {
                const pk_int = row.id;
                const key_str = get_datadicts_keystr(tblName, pk_int, row.studsubj_id);
                data_dicts[key_str] = row;
            };
        };
        //console.log("    data_dicts", data_dicts);
    };  // FillDatadicts

    function get_datadicts_keystr(tblName, pk_int, studsubj_pk) {  // PR2023-01-05
        let key_str = tblName + "_" + ((pk_int) ? pk_int : 0);
        //if (tblName === "studsubj") {key_str += "_" + ((studsubj_pk) ? studsubj_pk : 0)};
        return key_str
    };


//=========  CreateSubmenu  ===  PR2020-07-31
    function CreateSubmenu() {
        //console.log("===  CreateSubmenu == ");
        let el_submenu = document.getElementById("id_submenu");
        // hardcode access of system admin, to get access before action 'crud' is added to permits
        const permit_system_admin = (permit_dict.requsr_role_system && permit_dict.usergroup_list.includes("admin"));
        const permit_role_admin = (permit_dict.requsr_role_admin && permit_dict.usergroup_list.includes("admin"));

        if (permit_dict.permit_crud_sameschool || permit_dict.permit_crud_otherschool) {
            AddSubmenuButton(el_submenu, loc.Delete_user, function() {ModConfirmOpen("user","delete")}, []);
        };
        AddSubmenuButton(el_submenu, loc.Download_user_data, function() {ModConfirmOpen_DownloadUserdata("download_userdata_xlsx")});

        AddSubmenuButton(el_submenu, loc.Hide_columns, function() {t_MCOL_Open("page_corrector")}, [])

        el_submenu.classList.remove(cls_hide);
    };//function CreateSubmenu

//###########################################################################
// +++++++++++++++++ EVENT HANDLERS +++++++++++++++++++++++++++++++++++++++++
//=========  HandleBtnSelect  ================ PR2020-09-19 PR2021-08-01
    function HandleBtnSelect(data_btn, skip_upload) {
        console.log( "===== HandleBtnSelect ========= ");
        console.log( "skip_upload", skip_upload);

// ---  get  selected_btn
        // set to default "btn_approval" when there is no selected_btn
        // this happens when user visits page for the first time
        // includes is to catch saved btn names that are no longer in use
        if (data_btn && ["btn_approval", "btn_compensation"].includes(data_btn)){
            selected_btn = data_btn;
        } else if (!selected_btn) {
            selected_btn = "btn_approval";
        };

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

        const datadict = (tr_clicked && tr_clicked.id && tr_clicked.id in userapproval_dicts)  ? userapproval_dicts[tr_clicked.id]: null;

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        DeselectHighlightedRows(tr_clicked, cls_selected);
        tr_clicked.classList.add(cls_selected)

// --- get existing data_dict from data_rows
        //console.log( "tr_clicked.id: ", tr_clicked.id);
        //const data_dict = get_datadict_from_mapid(tr_clicked.id)
        //console.log( "data_dict: ", data_dict);

    };  // HandleTblRowClicked

//========= FillTblRows  =================== PR2021-08-01 PR2022-02-28
    function FillTblRows(skip_upload) {
        console.log( "===== FillTblRows  === ");
        //console.log( "    selected_btn: ", selected_btn);

        const tblName = get_tblName_from_selectedBtn() // tblName = userapproval or usercompensation
        const field_setting = field_settings[selected_btn];
        const data_dicts = get_datadicts_from_selectedBtn();  // data_dicts = userapproval_dicts or usercompensation_dicts

// ---  get list of hidden columns
        const col_hidden = get_column_is_hidden();

        console.log( "    tblName", tblName);
        console.log( "    data_dicts", data_dicts);
        console.log( "    field_setting", field_setting);

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

//=========  CreateTblHeader  === PR2020-07-31 PR2021-03-23  PR2021-08-01
    function CreateTblHeader(field_setting, col_hidden) {
        console.log("===  CreateTblHeader ===== ");
        //console.log("field_setting", field_setting);

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

                    } else if (filter_tag === "inactive") {
                        // add EventListener for icon to th_filter, not el_filter
                        th_filter.addEventListener("click", function(event){HandleFilterInactive(el_filter)});
                        th_filter.classList.add("pointer_show");
                        // set inactive icon
                        const filter_showinactive = (filter_dict && filter_dict.showinactive != null) ? filter_dict.showinactive : 1;
                        const icon_class = (filter_showinactive === 2) ? "inactive_1_3" : (filter_showinactive === 1) ? "inactive_0_2" : "inactive_0_0";

                        el_filter.classList.add(icon_class);
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

        console.log("    data_dict", data_dict);

// ---  lookup index where this row must be inserted
        const ob1 = (data_dict.username) ? data_dict.username : "";
        const ob2 = (data_dict.subjbase_code) ? data_dict.subjbase_code : "";
        const ob3 = (data_dict.sb_code) ? data_dict.sb_code : "";

        console.log("    ob1", ob1);
        console.log("    ob2", ob2);
        console.log("    ob3", ob3);
        const row_index = b_recursive_tblRow_lookup(tblBody_datatable, setting_dict.user_lang, ob1, ob2, ob3);

// --- insert tblRow into tblBody at row_index
        const tblRow = tblBody_datatable.insertRow(row_index);
        tblRow.id = map_id

        //console.log("    tblRow", tblRow);

// --- add data attributes to tblRow
        tblRow.setAttribute("data-pk", data_dict.id);
        if (!data_dict.is_active){
            tblRow.setAttribute("data-inactive", "1");
        };

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
                    if (field_name === "select") {
                        // TODO add select multiple users option PR2020-08-18

                    } else if (field_name === "uc_meetings") {
                        el.addEventListener("change", function(){HandleInputChange(el)});
                    } else if (field_name === "uc_meetingsxx") {
                        // attach eventlistener and hover to td, not to el. No need to add icon_class here
                        td.addEventListener("click", function() {UploadToggle(el)}, false)
                        add_hover(td);

                    } else if (field_name === "is_active") {
                        el.addEventListener("click", function() {ModConfirmOpen("user", "is_active", el)}, false )
                        el.classList.add("inactive_0_2")
                        add_hover(el);

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

            } else if (["user_sb_code", "username", "last_name", "sb_code", "school_abbrev",
                "depbase_code", "lvlbase_code", "subjbase_code", "subj_name_nl", "exam_version"].includes(field_name)){
                inner_text = data_dict[field_name];
                filter_value = (inner_text) ? inner_text.toLowerCase() : null;

            } else if (["uc_meetings"].includes(field_name)){
                inner_text = (data_dict[field_name]) ? data_dict[field_name] : null;  // don't show zero's
                filter_value = (inner_text) ? inner_text : null;

            } else if (["uc_amount", "examperiod"].includes(field_name)){
                inner_text = (data_dict[field_name]) ? data_dict[field_name] : null;  // don't show zero's
                filter_value = (inner_text) ? inner_text : null;

            } else if (field_name === "compensation") {
                inner_text = ( Number(data_dict[field_name])) ? Number( data_dict[field_name]) / 100 : null;
                filter_value = (inner_text) ? inner_text : null;

            } else if (field_name === "school_abbrev") {
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

            } else if (field_name === "is_active") {
                const is_inactive = !( (data_dict[field_name]) ? data_dict[field_name] : false );
                // give value '0' when inactive, '1' when active
                filter_value = (is_inactive) ? "0" : "1";

                el_div.className = (is_inactive) ? "inactive_1_3" : "inactive_0_2";

// ---  add title
                title_text = (is_inactive) ? loc.This_user_is_inactive : null;

            } else if ( field_name === "last_login") {
                const datetimeUTCiso = data_dict[field_name]
                const datetimeLocalJS = (datetimeUTCiso) ? new Date(datetimeUTCiso) : null;
                inner_text = format_datetime_from_datetimeJS(loc, datetimeLocalJS);
                filter_value = inner_text;
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
        return (selected_btn === "btn_approval") ? "userapproval" :
                        (selected_btn === "btn_compensation") ? "usercompensation" : null;
    }  // get_tblName_from_selectedBtn

//========= get_datadicts_from_selectedBtn  ======== // PR2023-02-26
    function get_datadicts_from_selectedBtn() {
        return (selected_btn === "btn_approval") ? userapproval_dicts :
               (selected_btn === "btn_compensation") ? usercompensation_dicts : null;
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


// +++++++++++++++++ UPLOAD CHANGES +++++++++++++++++ PR2020-08-03

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
                        const url_str = (tblName === "userpermit") ? urls.url_userpermit_upload : urls.url_user_upload;
                        const upload_dict = {mode: "update", mapid: data_dict.mapid};
                        if (tblName === "userpermit"){
                            upload_dict.userpermit_pk = data_dict.id;
                        } else {
                            // use this both for table 'user' and 'usergroup'
                            upload_dict.user_pk = data_dict.id,
                            upload_dict.schoolbase_pk = data_dict.schoolbase_id;
                        }
                        const usergroupname = fldName.substr(6);
                        upload_dict.usergroups = {}
                        upload_dict.usergroups[usergroupname] = permit_bool;
    console.log( "upload_dict", upload_dict);

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
                   // only used in MUPS allowes schools
                    if("msg_html" in response){
                        b_show_mod_message_html(response.msg_html, null, MUPS_MessageClose);
                    };

                    const mode = get_dict_value(response, ["mode"]);
                    if(["delete", "send_activation_email"].includes(mode)) {
                        ModConfirmResponse(response);
                    };

                    if ("updated_user_rows" in response) {
                        // must get  tblName from selectedBtn, to get 'usergroup' instead of 'user'
                        const tblName = get_tblName_from_selectedBtn();
                        RefreshDataRows(tblName, response.updated_user_rows, user_rows, true)  // true = update
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

        if (selected_btn === "btn_compensation"){
            // reset el_input.value to saved value
            const data_dict = usercompensation_dicts[map_id];
            el_input.value = (data_dict && data_dict.uc_meetings) ? data_dict.uc_meetings : null
            b_show_mod_message_html(loc.cannot_enter_meetings_in_tab_compensation + "<br>" + loc.select_tab_approvals_to_enter_meetings);
        } else {

            if (map_id){
                const data_dict = userapproval_dicts[map_id];

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
            selected_pk = (tblName === "userpermit") ? selected_userpermit_pk : selected_user_pk;
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
            if (tblName === "userpermit"){
                mod_dict.userpermit_pk = selected_userpermit_pk
            } else {
                mod_dict.user_pk = data_dict.id;
                mod_dict.user_ppk = data_dict.schoolbase_id;
            }
        };
        if (mode === "is_active") {
            mod_dict.current_isactive = data_dict.is_active;
        } else if (mode === "user_without_userallowed") {
            if (!isEmpty(user_without_userallowed)) {
                mod_dict.user_pk = user_without_userallowed.user_pk;
                mod_dict.schoolbase_pk = user_without_userallowed.schoolbase_pk;
                mod_dict.username = user_without_userallowed.username;
                mod_dict.last_name = user_without_userallowed.last_name;
            };
        };
       console.log("    mod_dict", mod_dict);

// ---  put text in modal form
        let dont_show_modal = false;
        const is_mode_permission_admin = (mode === "permission_admin");
        const is_mode_send_activation_email = (mode === "send_activation_email");

        const inactive_txt = (mod_dict.current_isactive) ? loc.Make_user_inactive : loc.Make_user_active;
        const header_text = (mode === "delete") ? (tblName === "userpermit") ? loc.Delete_permission : loc.Delete_user :
                            (mode === "is_active") ? inactive_txt :
                            (mode === "user_without_userallowed") ? loc.Add_user :
                            (is_mode_send_activation_email) ? loc.Send_activation_email :
                            (is_mode_permission_admin) ? loc.Set_permissions : "";

        let msg_list = [];
        let hide_save_btn = false;
        if(mode === "user_without_userallowed"){
            // PR2023-01-01 from https://stackoverflow.com/questions/4842993/javascript-push-an-entire-list
            // use push.apply instead of joining the list before pushing
            msg_list.push(["<p>", loc.Username, " '", mod_dict.username,  "' ", loc._of_, loc.User.toLowerCase()," '" , mod_dict.last_name, "'</p>"].join(""));
            msg_list.push(["<p>", loc.already_exists_in_previous_examyear, "</p>"].join(""));

            msg_list.push(["<p class='mt-3'>", loc.Doyou_wantto_add_to_this_examyear, "</p>"].join(""));
        } else if (!has_selected_item){
            msg_list.push("<p>" + loc.No_user_selected + "</p>");
            hide_save_btn = true;
        } else {
            if(tblName === "userpermit"){
                const action = (data_dict.action) ? data_dict.action  : "-";
                const page = (data_dict.page) ? data_dict.page  : "-";
                msg_list.push(["<p>", loc.Action, " '", action, "'", loc.on_page, "'",page, "'", loc.will_be_deleted, "</p>"].join(""));
                msg_list.push("<p>" + loc.Do_you_want_to_continue + "</p>");
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
                } else if(mode === "is_active"){
                    if(is_request_user && mod_dict.current_isactive){
                        msg_list.push("<p>" + loc.Sysadm_cannot_set_inactive + "</p>");
                        hide_save_btn = true;
                    } else {
                        const inactive_txt = (mod_dict.current_isactive) ? loc.will_be_made_inactive : loc.will_be_made_active
                        msg_list.push(["<p>", loc.User + " '" + username + "'", inactive_txt, "</p>"].join(""));
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
        }
        if(!dont_show_modal){
            el_confirm_header.innerText = header_text;
            el_confirm_loader.classList.add(cls_visible_hide)
            el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");

            const msg_html = (msg_list.length) ? msg_list.join("") : null;
            el_confirm_msg_container.innerHTML = msg_html;

            //el_confirm_msg_container.classList.add("border_bg_transparent");

            const caption_save = (mode === "delete") ? loc.Yes_delete :
                            (mode === "is_active") ? ( (mod_dict.current_isactive) ? loc.Yes_make_inactive : loc.Yes_make_active ) :
                            (is_mode_send_activation_email) ? loc.Yes_send_email : loc.OK;
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

        } else if(mod_dict.mode === "download_userdata_xlsx"){
            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            if (el_modconfirm_link) {
                const href_str = urls.url_download_userdata_xlsx;
                el_modconfirm_link.setAttribute("href", href_str);
                el_modconfirm_link.click();

                close_modal = true;
            };
            skip_uploadchanges = true;

        } else if(mod_dict.table === "userpermit"){
            if (mod_dict.mode === "delete"){
                url_str = urls.url_userpermit_upload;
                upload_dict.userpermit_pk = mod_dict.userpermit_pk;

                close_modal = true;
            }
        } else {
            if(["delete", "send_activation_email"].includes(mod_dict.mode)) {
    // show loader
                el_confirm_loader.classList.remove(cls_visible_hide)
            } else if (mod_dict.mode === "is_active") {
                mod_dict.new_isactive = !mod_dict.current_isactive
                close_modal = true;
                // change inactive icon, before uploading, not when new_inactive = true
                const el_input = document.getElementById(mod_dict.mapid)
                for (let i = 0, cell, el; cell = tblRow.cells[i]; i++) {
                    const cell_fldName = get_attr_from_el(cell, "data-field")
                    if (cell_fldName === "is_active"){
    // ---  change icon, before uploading
                        let el_icon = cell.children[0];
                        if(el_icon){add_or_remove_class (el_icon, "inactive_1_3", !mod_dict.new_isactive,"inactive_0_2" )};
                        break;
                    };
                };
            };

            url_str = urls.url_user_upload;
            upload_dict.user_pk = mod_dict.user_pk;
            upload_dict.schoolbase_pk = mod_dict.user_ppk;
            if (mod_dict.mode === "is_active") {
                upload_dict.is_active = mod_dict.new_isactive;
            };
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

//=========  RefreshDataRowsAfterUpload  ================ PR2021-08-05
function RefreshDataRowsAfterUpload(response) {
    //console.log(" --- RefreshDataRowsAfterUpload  ---");
    //console.log("response:", response);
    const is_test = (!!response && !!response.is_test) ;
    if(!is_test && response && "updated_user_rows" in response) {
        RefreshDataRows("user", response.updated_user_rows, user_rows, true)  // true = update
    }

}  // RefreshDataRowsAfterUpload

//=========  RefreshDataRowsPermitsAfterUpload  ================ PR2021-07-20
    function RefreshDataRowsPermitsAfterUpload(response) {
        //console.log(" --- RefreshDataRowsPermitsAfterUpload  ---");
        //console.log( "response", response);

        const is_test = (response && response.is_test);
        //console.log( "is_test", is_test);
        if (response && "updated_user_rows" in response) {
            const updated_user_rows = response.updated_user_rows;
        }

    }  //  RefreshDataRowsPermitsAfterUpload

// +++++++++++++++++ REFRESH PERMIT MAP ++++++++++++++++++++++++++++++++++++++++++++++++++
//=========  refresh_permit_map  ================ PR2021-03-18
    function refresh_permit_map(updated_permitlist) {
        //console.log(" --- refresh_permit_map  ---");
        //console.log( "updated_permitlist", updated_permitlist);
        if (updated_permitlist) {
            for (let i = 0, update_dict; update_dict = updated_permitlist[i]; i++) {
               // refresh_usermap_item(permit_map, update_dict);
               //RefreshDatarowItem(tblName, field_setting, update_dict, data_rows)
            }
        }
    }  //  refresh_permit_map


// +++++++++++++++++ REFRESH DATA ROWS ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataRows  ================ PR2021-08-01
    function RefreshDataRows(page_tblName, update_rows, data_rows, is_update) {
        //console.log(" --- RefreshDataRows  ---");
        //console.log("page_tblName", page_tblName);
        //console.log("update_rows", update_rows);
        //console.log("data_rows", data_rows);
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


//=========  RefreshDatarowItem  ================ PR2021-08-01
    function RefreshDatarowItem(page_tblName, field_setting, update_dict, data_rows) {
        //console.log(" --- RefreshDatarowItem  ---");
        //console.log("page_tblName", page_tblName);
        //console.log("update_dict", update_dict);
        //console.log("field_setting", field_setting);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

            const pk_int = update_dict.id;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);
            //console.log("is_created", is_created);

            // field_error_list is not in use (yet)
            let field_error_list = [];
            const error_list = get_dict_value(update_dict, ["error"], []);
            //console.log("error_list", error_list);

            if(error_list && error_list.length){
    // - show modal messages
                b_show_mod_message_dictlist(error_list);

    // - add fields with error in field_error_list, to put old value back in field
                for (let i = 0, msg_dict ; msg_dict = error_list[i]; i++) {
                    if ("field" in msg_dict){field_error_list.push(msg_dict.field)};
                };
            //} else {
            // close modal MSJ when no error --- already done in modal
                //$("#id_mod_subject").modal("hide");
            }

// NIU:
// ---  get list of hidden columns
            //const col_hidden = b_copy_array_to_new_noduplicates(mod_MCOL_dict.cols_hidden);

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
                const new_tblRow = CreateTblRow(page_tblName, field_setting, update_dict)

    // ---  scrollIntoView,
                if(new_tblRow){
                    new_tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' })

    // ---  make new row green for 2 seconds,
                    ShowOkElement(new_tblRow);
                }
            } else {

// --- get existing data_dict
                const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);
                const data_dict = found_dict;
                const datarow_index = index;
;
// ++++ deleted ++++
                if(is_deleted){
                    // delete row from data_rows. Splice returns array of deleted rows
                    const deleted_row_arr = data_rows.splice(datarow_index, 1)
                    const deleted_row_dict = deleted_row_arr[0];

        //--- delete tblRow
                    if(deleted_row_dict && deleted_row_dict.mapid){
                        const tblRow_tobe_deleted = document.getElementById(deleted_row_dict.mapid);
        //console.log("tblRow_tobe_deleted", tblRow_tobe_deleted);
                        if (tblRow_tobe_deleted ){tblRow_tobe_deleted.parentNode.removeChild(tblRow_tobe_deleted)};
                    }
                } else {

// +++++++++++ updated row +++++++++++
    // ---  check which fields are updated, add to list 'updated_columns'
                    if(!isEmpty(data_dict) && field_names){
                        let updated_columns = [];

                        // skip first column (is margin)
                        // col_field is the name of the column on page, not the db_field
                        for (let i = 1, col_field, old_value, new_value; col_field = field_names[i]; i++) {
                            let has_changed = false;
                            if (col_field.slice(0, 5) === "group") {
                            // data_dict.usergroups example: "anlz;auth1;auth2;auth3;auth4;edit;read"
                                const usergroup = col_field.slice(6);
                                // usergroup_in_data_dict and usergroup_in_update_dict are necessary to catch empty usergroup field
                                const usergroup_in_data_dict = (!!data_dict.usergroups && data_dict.usergroups.includes(usergroup));
                                const usergroup_in_update_dict = (!!update_dict.usergroups && update_dict.usergroups.includes(usergroup));
                                has_changed = usergroup_in_data_dict != usergroup_in_update_dict;

                            } else if (col_field in data_dict && col_field in update_dict){
                                has_changed = (data_dict[col_field] !== update_dict[col_field] );
                            };
                            if (has_changed){
        // ---  add field to updated_columns list
                                updated_columns.push(col_field)
                            };
                        };
// ---  update fields in data_row
                        for (const [key, new_value] of Object.entries(update_dict)) {
                            if (key in data_dict){
                                if (new_value !== data_dict[key]) {
                                    data_dict[key] = new_value;
                        }}};

        // ---  update field in tblRow
                        // note: when updated_columns is empty, then updated_columns is still true.
                        // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
                        if(updated_columns.length || field_error_list.length){

// --- get existing tblRow
                            let tblRow = document.getElementById(data_dict.mapid);
                            if(tblRow){
                                // to make it perfect: move row when username have changed
                                if (updated_columns.includes("username")){
                                //--- delete current tblRow
                                    tblRow.parentNode.removeChild(tblRow);
                                //--- insert row new at new position
                                    tblRow = CreateTblRow(page_tblName, field_setting, update_dict)
                                }

                // loop through cells of row
                                for (let i = 1, el_fldName, el, td; td = tblRow.cells[i]; i++) {
                                    el = td.children[0];
                                    if (el){
                                        el_fldName = get_attr_from_el(el, "data-field")
                                        UpdateField(el, update_dict);

                // make field green when field name is in updated_columns
                                        if(updated_columns.includes(el_fldName)){
                                            ShowOkElement(el);
                                        };
                                    };
                                };  //  for (let i = 1, el_fldName, el; el = tblRow.cells[i]; i++) {
                            };  // if(tblRow){
                        }; //  if(updated_columns.length){
                    };  //  if(!isEmpty(data_dict) && field_names){
                };  // if(is_deleted){
            };  // if(is_created)
        };  // if(!isEmpty(update_dict)){
    };  // RefreshDatarowItem

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

//========= HandleFilterInactive  =============== PR2022-03-03
    function HandleFilterInactive(el_filter) {
        //console.log( "===== HandleFilterInactive  ========= ");
        //console.log( "el_filter", el_filter);

        // show active only when opening page
        const filter_showinactive = (filter_dict && filter_dict.showinactive != null) ? filter_dict.showinactive : 1;
    //console.log( "filter_dict", filter_dict);
    //console.log( "filter_showinactive", filter_showinactive, typeof filter_showinactive);

// - toggle filter value
        // filter inactive '0'; is show all, '1' is show active only, '2' is show inactive only
        // filter inactive '0'; is show active only, '1' is show all, '2' is show inactive only
        // set to default 1 when opening page (el_filter is then undefined
        const new_value = (!el_filter) ? 1 : (filter_showinactive === 2) ? 0 : (filter_showinactive === 1) ? 2 : (filter_showinactive === 0) ? 1 : 1;
// - get new icon_class
        const icon_class =  (new_value === 2) ? "inactive_1_3" : (new_value === 1) ? "inactive_0_2" : "inactive_0_0";

    // - put new filter value in filter_dict
        filter_dict.showinactive = new_value
    //console.log( "filter_dict", filter_dict);

        if( el_filter ) {el_filter.className = icon_class};
        Filter_TableRows();

    };  // HandleFilterInactive

//========= Filter_TableRows  ====================================
    function Filter_TableRows(set_filter_isactive) {  // PR2019-06-09 PR2020-08-31 PR2022-03-03
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

        if (set_filter_isactive){
            HandleFilterInactive();
        };

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
                user_rows: {get: true},
                department_rows: {get: true},
                school_rows: {skip_allowed_filter: true},
                level_rows: {skip_allowed_filter: true},
                subject_rows_page_users: {get: true},
                cluster_rows: {get: true}
            };

        DatalistDownload(datalist_request);

    }  // MSED_Response

//###########################################################################
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
})  // document.addEventListener('DOMContentLoaded', function()