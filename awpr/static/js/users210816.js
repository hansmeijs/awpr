// PR2020-07-30 added


let selected_btn = "btn_user";
let setting_dict = {};
let permit_dict = {};
let loc = {};
let urls = {};


document.addEventListener('DOMContentLoaded', function() {
    "use strict";

    let el_loader = document.getElementById("id_loader");

// ---  get permits
    // permit dict gets value after downloading permit_list PR2021-03-27
    //  if user has no permit to view this page ( {% if no_access %} ): el_loader does not exist PR2020-10-02

    // Note: may_view_page is the only permit that gets its value on DOMContentLoaded,
    // all other permits get their value in function get_permits, after downloading permit_list
    const may_view_page = (!!el_loader)

    const cls_hide = "display_hide";
    const cls_hover = "tr_hover";
    const cls_visible_hide = "visibility_hide";
    const cls_selected = "tsa_tr_selected";

// ---  id of selected customer and selected order
    let selected_btn = "btn_user";
    let selected_user_pk = null;
    let selected_user_dict = null;

    let selected_userpermit_pk = null;
    let selected_period = {};

    let loc = {};  // locale_dict
    let mod_dict = {};
    let mod_MUA_dict = {};
    let mod_MUPM_dict = {};
    let time_stamp = null; // used in mod add user

    let user_list = [];
    let user_rows = [];
    let permit_rows = [];
    let school_rows = [];

    let examyear_map = new Map();

    let department_map = new Map();

    let permit_map = new Map();

    let filter_dict = {};
    let filter_mod_employee = false;

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    urls.url_settings_upload = get_attr_from_el(el_data, "data-url_settings_upload");
    urls.url_user_upload = get_attr_from_el(el_data, "data-user_upload_url");
    urls.url_userpermit_upload = get_attr_from_el(el_data, "data-userpermit_upload_url");
    urls.url_download_permits = get_attr_from_el(el_data, "data-user_download_permits_url");

    // url_importdata_upload is stored in id_MIMP_data of modimport.html
    let columns_hidden = [];

// --- get field_settings
    const field_settings = {
        user: { field_caption: ["", "School_code", "School", "User", "Name", "Email_address",  "Activated", "Last_loggedin", "Inactive"],
                    field_names: ["select", "sb_code", "school_abbrev", "username", "last_name", "email",  "activated", "last_login", "is_active"],
                    field_tags: ["div", "div", "div", "div", "div",  "div", "div","div", "div"],
                    filter_tags: ["select", "text", "text",  "text",  "text", "text",  "toggle", "text", "toggle"],
                    field_width:  ["020", "090", "150", "150",  "180", "240",  "100", "180", "090"],
                    field_align: ["c", "l", "l", "l","l",  "l",  "c", "l", "c"]},
        usergroup: {
                    field_caption: ["", "School", "User", "Read_only_2lines", "Edit",
                                    "President", "Secretary", "Commissioner_2lines",
                                    "Analyze",  "System_manager_2lines"],
                    field_names: ["select", "sb_code", "username", "group_read", "group_edit",
                                    "group_auth1", "group_auth2", "group_auth3", "group_anlz", "group_admin"],
                    field_tags: ["div", "div", "div", "div", "div",
                                    "div", "div", "div",
                                    "div", "div"],
                    filter_tags: ["select", "text", "text",  "toggle", "toggle",
                                    "toggle", "toggle", "toggle",
                                     "toggle", "toggle"],
                    field_width:  ["020", "075", "150", "090", "090",
                                    "090", "090", "090",
                                    "090", "090"],
                    field_align: ["c", "l", "l", "c", "c",
                     "c", "c", "c",
                     "c", "c"]},
        userpermit: {
                    field_caption: ["", "Organization", "Page", "Action", "Read_only_2lines", "Edit",
                                    "President", "Secretary", "Commissioner_2lines",
                                    "Analyze", "System_manager_2lines"],
                    field_names: ["select", "role", "page", "action",
                                    "group_read", "group_edit", "group_auth1", "group_auth2", "group_auth3", "group_anlz", "group_admin"],
                    field_tags: ["div", "div", "div", "input", "div", "div",
                                    "div", "div", "div", "div", "div"],
                    filter_tags: ["select", "text", "text", "text", "toggle", "toggle",
                                    "toggle", "toggle", "toggle", "toggle", "toggle"],
                    field_width:  ["020", "090", "120","150", "075", "075",
                                    "090", "090", "090", "090", "090"],
                    field_align: ["c", "l", "l", "l", "c", "c", "c", "c", "c", "c", "c"]}
        };
    const tblHead_datatable = document.getElementById("id_tblHead_datatable");
    const tblBody_datatable = document.getElementById("id_tblBody_datatable");

// === EVENT HANDLERS ===
// === reset filter when ckicked on Escape button ===
        document.addEventListener("keydown", function (event) {
             if (event.key === "Escape") { ResetFilterRows()}
        });

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
        //const elMSESD_input = document.getElementById("id_MSED_input");

        if (el_hdrbar_examyear){
            el_hdrbar_examyear.addEventListener("click",
                function() {t_MSED_Open(loc, "examyear", examyear_map, setting_dict, permit_dict, MSED_Response)}, false );
        }
        if (el_hdrbar_department){
            el_hdrbar_department.addEventListener("click",
                function() {t_MSED_Open(loc, "department", department_map, setting_dict, permit_dict, MSED_Response)}, false );
        }
        if (el_hdrbar_school){
            el_hdrbar_school.addEventListener("click",
                function() {t_MSSSS_Open(loc, "school", school_rows, false, setting_dict, permit_dict, MSSSS_Response)}, false );
        }

// ---  MSED - MOD SELECT EXAMYEAR OR DEPARTMENT ------------------------------
        const el_MSED_input = document.getElementById("id_MSED_input");
        const el_MSED_btn_save = document.getElementById("id_MSED_btn_save");
        if (el_MSED_input){
            el_MSED_input.addEventListener("keyup", function(event){
                setTimeout(function() {t_MSED_InputName(el_MSED_input)}, 50)});
        }
        if (el_MSED_btn_save){
            el_MSED_btn_save.addEventListener("click", function() {t_MSED_Save(el_MSED_btn_save, MSED_Response)}, false);
        }

// ---  MSSS MOD SELECT SCHOOL SUBJECT STUDENT ------------------------------
        const el_MSSSS_input = document.getElementById("id_MSSSS_input");
        const el_MSSSS_tblBody = document.getElementById("id_MSSSS_tbody_select");
        const el_MSSSS_btn_save = document.getElementById("id_MSSSS_btn_save");
        if (el_MSSSS_input){
            el_MSSSS_input.addEventListener("keyup", function(event){
                setTimeout(function() {t_MSSSS_InputKeyup(el_MSSSS_input)}, 50)});
        }
        if (el_MSSSS_input){
            el_MSSSS_input.addEventListener("click", function() {t_MSSSS_Save(el_MSSSS_input, MSSSS_Response)}, false );
        }

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

        if (el_MUA_schoolname){
            el_MUA_schoolname.addEventListener("keyup", function() {MUA_InputSchoolname(el_MUA_schoolname, event.key)}, false);
        }
        if (el_MUA_username){
            el_MUA_username.addEventListener("keyup", function() {MUA_InputKeyup(el_MUA_username, event.key)}, false);
        }
        if (el_MUA_last_name){
            el_MUA_last_name.addEventListener("keyup", function() {MUA_InputKeyup(el_MUA_last_name, event.key)}, false);
        }
        if (el_MUA_email){
            el_MUA_email.addEventListener("keyup", function() {MUA_InputKeyup(el_MUA_email, event.key)}, false);
        }
        if (el_MUA_btn_delete){
            el_MUA_btn_delete.addEventListener("click", function() {ModConfirmOpen("user", "delete")}, false);
        }
        if (el_MUA_btn_submit){
            el_MUA_btn_submit.addEventListener("click", function() {MUA_Save("validate")}, false);
        };

// ---  MODAL GROUP PERMISSION
        const el_MUPM_btn_delete = document.getElementById("id_MUPM_btn_delete");
        const el_MUPM_btn_submit = document.getElementById("id_MUPM_btn_submit");
        if (el_MUPM_btn_delete){
            el_MUPM_btn_delete.addEventListener("click", function() {MUPM_Save("delete")}, false);
        }
        if (el_MUPM_btn_submit){
            el_MUPM_btn_submit.addEventListener("click", function() {MUPM_Save("save")}, false);
        };

// ---  MODAL IMPORT ------------------------------------
    // --- create EventListener for buttons in btn_container
        const el_MIMP_btn_container = document.getElementById("id_MIMP_btn_container");
        if(el_MIMP_btn_container){
            const btns = el_MIMP_btn_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                const data_btn = get_attr_from_el(btn,"data-btn")
                btn.addEventListener("click", function() {MIMP_btnSelectClicked(data_btn)}, false )
            }
        }
        const el_MIMP_filedialog = document.getElementById("id_MIMP_filedialog");
        if (el_MIMP_filedialog){el_MIMP_filedialog.addEventListener("change", function() {MIMP_HandleFiledialog(el_MIMP_filedialog)}, false)};
        const el_MIMP_btn_filedialog = document.getElementById("id_MIMP_btn_filedialog");

        if (el_MIMP_filedialog && el_MIMP_btn_filedialog){
            el_MIMP_btn_filedialog.addEventListener("click", function() {MIMP_OpenFiledialog(el_MIMP_filedialog)}, false)};
        const el_MIMP_filename = document.getElementById("id_MIMP_filename");

        const el_worksheet_list = document.getElementById("id_MIMP_worksheetlist");
        if (el_worksheet_list){el_worksheet_list.addEventListener("change", function() {MIMP_SelectWorksheet()}, false)};
        const el_MIMP_checkboxhasheader = document.getElementById("id_MIMP_hasheader");
        if (el_MIMP_checkboxhasheader){el_MIMP_checkboxhasheader.addEventListener("change", function() {MIMP_CheckboxHasheaderChanged()}, false)};
        const el_MIMP_btn_prev = document.getElementById("id_MIMP_btn_prev");
        if (el_MIMP_btn_prev){el_MIMP_btn_prev.addEventListener("click", function() {MIMP_btnPrevNextClicked("prev")}, false)};
        const el_MIMP_btn_next = document.getElementById("id_MIMP_btn_next");
        if (el_MIMP_btn_next){el_MIMP_btn_next.addEventListener("click", function() {MIMP_btnPrevNextClicked("next")}, false)};
        const el_MIMP_btn_test = document.getElementById("id_MIMP_btn_test");
        if (el_MIMP_btn_test){el_MIMP_btn_test.addEventListener("click", function() {MIMP_Save("test", RefreshDataRowsAfterUpload)}, false)};
        const el_MUP_btn_upload = document.getElementById("id_MIMP_btn_upload");
        if (el_MUP_btn_upload){el_MUP_btn_upload.addEventListener("click", function() {MIMP_Save("save", RefreshDataRowsAfterUpload)}, false)};

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
                setting: {page: "page_user"},
                schoolsetting: {setting_key: "import_username"},
                locale: {page: ["page_user", "upload"]},
                user_rows: {get: true},
                school_rows: {get: true}
            };

        DatalistDownload(datalist_request, "DOMContentLoaded");
    };
//  #############################################################################################################

//========= DatalistDownload  ===================== PR2020-07-31
    function DatalistDownload(datalist_request, called_by) {
        console.log( "=== DatalistDownload ", called_by)
        console.log("request: ", datalist_request)

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
        console.log("loc: ", loc)
                };
                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict;
                    selected_btn = setting_dict.sel_btn;
                    isloaded_settings = true;
                };
                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    isloaded_permits = true;
                    // get_permits must come before CreateSubmenu and FiLLTbl
                    b_get_permits_from_permitlist(permit_dict);
                    set_columns_hidden();
                }

                if(isloaded_loc && isloaded_permits){CreateSubmenu()};
                if(isloaded_settings || isloaded_permits){b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);};
                if ("schoolsetting_dict" in response) { i_UpdateSchoolsettingsImport(response.schoolsetting_dict) };

                if ("user_rows" in response) {
                    user_rows = response.user_rows;
                };
                if ("permit_rows" in response) {
                    permit_rows = response.permit_rows
                    refresh_permit_map(response.permit_rows) };

                if ("examyear_rows" in response) { b_fill_datamap(examyear_map, response.examyear_rows) };
                if ("school_rows" in response)  {
                   school_rows = response.school_rows
                };
                if ("department_rows" in response) { b_fill_datamap(department_map, response.department_rows) };

                HandleBtnSelect(selected_btn, true);  // true = skip_upload

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
        //console.log("===  CreateSubmenu == ");
        let el_submenu = document.getElementById("id_submenu")
        // hardcode access of system admin, to get access before action 'crud' is added to permits
        const permit_system_admin = (permit_dict.requsr_role_system && permit_dict.usergroup_list.includes("admin"));
        const permit_role_admin = (permit_dict.requsr_role_admin && permit_dict.usergroup_list.includes("admin"));

        if (permit_dict.permit_crud_sameschool || permit_dict.permit_crud_otherschool) {
            if(permit_system_admin || permit_role_admin){
                AddSubmenuButton(el_submenu, loc.Upload_usernames, function() {MIMP_Open(loc, "import_username")}, null, "id_submenu_import");
            }
            AddSubmenuButton(el_submenu, loc.Add_user, function() {MUA_Open("addnew")}, ["tab_show", "tab_btn_user", "tab_btn_usergroup"]);
            AddSubmenuButton(el_submenu, loc.Delete_user, function() {ModConfirmOpen("user","delete")}, ["tab_show", "tab_btn_user", "tab_btn_usergroup"]);
        }
        // hardcode access of system admin
        if (permit_system_admin){
            AddSubmenuButton(el_submenu, loc.Add_permission, function() {MUPM_Open("addnew")}, ["tab_show", "tab_btn_userpermit"]);;
            AddSubmenuButton(el_submenu, loc.Delete_permission, function() {ModConfirmOpen("userpermit","delete")}, ["tab_show", "tab_btn_userpermit"]);
            AddSubmenuButton(el_submenu, loc.Download_permissions, null, ["tab_show", "tab_btn_userpermit"], "id_submenu_download_perm", urls.url_download_permits, false);  // true = download
            AddSubmenuButton(el_submenu, loc.Upload_permissions, function() {MIMP_Open(loc, "import_permit")}, ["tab_show", "tab_btn_userpermit"], "id_submenu_import");
        };
         el_submenu.classList.remove(cls_hide);
    };//function CreateSubmenu

//###########################################################################
// +++++++++++++++++ EVENT HANDLERS +++++++++++++++++++++++++++++++++++++++++
//=========  HandleBtnSelect  ================ PR2020-09-19 PR2021-08-01
    function HandleBtnSelect(data_btn, skip_upload) {
        console.log( "===== HandleBtnSelect ========= ");

// ---  get  selected_btn
        // set to default "btn_user" when there is no selected_btn
        // this happens when user visits page for the first time
        // includes is to catch btn names that are no longer in use
        selected_btn = (data_btn && ["btn_user", "btn_usergroup", "btn_userpermit"].includes(data_btn)) ? data_btn : "btn_user"
        console.log( "selected_btn: ", selected_btn);

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_user: {sel_btn: selected_btn}};
            UploadSettings (upload_dict, urls.url_settings_upload);
        };

// ---  highlight selected button
        highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  show only the elements that are used in this tab
        b_show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

// ---  fill datatable
        FillTblRows();

    }  // HandleBtnSelect

//=========  HandleTableRowClicked  ================ PR2020-08-03 PR2021-08-01
    function HandleTableRowClicked(tr_clicked) {
        //console.log("=== HandleTableRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);
        //console.log( "tr_clicked.id: ", tr_clicked, typeof tr_clicked.id);

        selected_user_dict = get_datadict_from_mapid(tr_clicked.id);
        //console.log( "selected_user_dict: ", selected_user_dict);

        selected_userpermit_pk = null;

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        DeselectHighlightedRows(tr_clicked, cls_selected);
        tr_clicked.classList.add(cls_selected)

// --- get existing data_dict from data_rows
        console.log( "tr_clicked.id: ", tr_clicked.id);
        const data_dict = get_datadict_from_mapid(tr_clicked.id)
        //console.log( "data_dict: ", data_dict);

// ---  update selected_user_pk
        const tblName = get_tblName_from_mapid(data_dict.mapid);
        if(tblName === "userpermit"){
            selected_userpermit_pk = data_dict.id;
        } else {
            selected_user_pk = data_dict.id;
        }
        //console.log( "selected_userpermit_pk: ", selected_userpermit_pk, typeof selected_userpermit_pk);
        //console.log( "selected_user_pk: ", selected_user_pk, typeof selected_user_pk);
    }  // HandleTableRowClicked

//========= FillTblRows  =================== PR2021-08-01
    function FillTblRows() {
        //console.log( "===== FillTblRows  === ");
        const tblName = get_tblName_from_selectedBtn();

        const field_setting = field_settings[tblName];
        const data_rows = get_data_rows(tblName);

        //console.log( "selected_btn", selected_btn);
        //console.log( "tblName", tblName);
        //console.log( "data_rows", data_rows);
        //console.log( "field_setting", field_setting);

// --- show columns
        set_columns_hidden();
        //console.log( "columns_hidden", columns_hidden);

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null

// --- create table header and filter row
        CreateTblHeader(field_setting);

// --- loop through data_rows
        if(data_rows && data_rows.length){
            for (let i = 0, map_dict; map_dict = data_rows[i]; i++) {
                let tblRow = CreateTblRow(tblName, field_setting, map_dict);
            };
        };

// --- filter tblRow
        // happens in Filter_TableRows
    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-07-31 PR2021-03-23  PR2021-08-01
    function CreateTblHeader(field_setting) {
        //console.log("===  CreateTblHeader ===== ");
        //console.log("field_setting", field_setting);

        const column_count = field_setting.field_names.length;

// +++  insert header and filter row ++++++++++++++++++++++++++++++++
        let tblRow_header = tblHead_datatable.insertRow (-1);
        let tblRow_filter = tblHead_datatable.insertRow (-1);

    // --- loop through columns
        for (let j = 0; j < column_count; j++) {
            const field_name = field_setting.field_names[j];
    // - skip column if field_name in columns_hidden;
            const hide_column = columns_hidden.includes(field_name);
            if (!hide_column){

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
                    //el_filter.setAttribute("data-colindex", j);

        // --- add EventListener to el_filter / th_filter
                    if (["text", "number"].includes(filter_tag)) {
                        el_filter.addEventListener("keyup", function(event){HandleFilterKeyup(el_filter, event)});
                        add_hover(th_filter);
                    } else if (["toggle", "activated"].includes(filter_tag)) {
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
            }  // if (!columns_hidden.includes(field_name))
        }  // for (let j = 0; j < column_count; j++)
    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09 PR2021-08-01
    function CreateTblRow(tblName, field_setting, map_dict) {
        //console.log("=========  CreateTblRow =========", tblName);
        //console.log("map_dict", map_dict);

        const field_names = field_setting.field_names;
        const field_tags = field_setting.field_tags;
        const filter_tags = field_setting.filter_tags;
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;

        const map_id = (map_dict.mapid) ? map_dict.mapid : null;

// ---  lookup index where this row must be inserted
        const ob1 = (map_dict.sb_code) ? map_dict.sb_code : "";
        const ob2 = (map_dict.username) ? map_dict.username : "";

        const row_index = b_recursive_tblRow_lookup(tblBody_datatable,
                                     ob1, ob2, "", setting_dict.user_lang);

// --- insert tblRow into tblBody at row_index
        const tblRow = tblBody_datatable.insertRow(row_index);
        tblRow.id = map_id

// --- add data attributes to tblRow
        tblRow.setAttribute("data-pk", map_dict.id);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);
        tblRow.setAttribute("data-ob2", ob2);
        // NIU: tblRow.setAttribute("data-ob3", ---);

// --- add EventListener to tblRow
        tblRow.addEventListener("click", function() {HandleTableRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
        for (let j = 0; j < column_count; j++) {
            const field_name = field_names[j];

    // - skip column if field_name in columns_hidden;
            const hide_column = columns_hidden.includes(field_name);
            if (!hide_column){
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

                    } else if (["sb_code", "school_abbrev", "username", "last_name", "email"].includes(field_name)){
                        el.addEventListener("click", function() {MUA_Open("update", el)}, false)
                        el.classList.add("pointer_show");
                        add_hover(el);
                    } else if (["role", "page"].includes(field_name)){
                        el.addEventListener("click", function() {MUPM_Open("update", el)}, false)
                        el.classList.add("pointer_show");
                        add_hover(el);
                    } else if (["role", "page", "action", "sequence"].includes(field_name)){
                        el.addEventListener("change", function(){HandleInputChange(el)});
                    } else if (field_name.slice(0, 5) === "group") {
                        // attach eventlistener and hover to td, not to el. No need to add icon_class here
                        td.addEventListener("click", function() {UploadToggle(el)}, false)
                        add_hover(td);
                    } else if ( field_name === "activated") {
                        el.addEventListener("click", function() {ModConfirmOpen("user", "send_activation_email", el)}, false )
                    } else if (field_name === "is_active") {
                        el.addEventListener("click", function() {ModConfirmOpen("user", "is_active", el)}, false )
                        el.classList.add("inactive_0_2")
                        add_hover(el);
                    } else if ( field_name === "last_login") {
                        // pass
                    }

// --- put value in field
                UpdateField(el, map_dict)

            }  // if (!columns_hidden.includes(field_name))
        }  // for (let j = 0; j < 8; j++)

        return tblRow
    };  // CreateTblRow

//=========  UpdateTblRow  ================ PR2020-08-01
    function UpdateTblRow(tblRow, tblName, map_dict) {
        //console.log("=========  UpdateTblRow =========");
        if (tblRow && tblRow.cells){
            for (let i = 0, td; td = tblRow.cells[i]; i++) {
                UpdateField(td.children[0], map_dict);
            }
        }
    };  // UpdateTblRow

//=========  UpdateField  ================ PR2020-08-16 PR2021-03-23 PR2021-08-01
    function UpdateField(el_div, map_dict) {
        //console.log("=========  UpdateField =========");

        const field_name = get_attr_from_el(el_div, "data-field");
        if(el_div && field_name){
            let inner_text = null, title_text = null, filter_value = null;
            if (field_name === "select") {
                // TODO add select multiple users option PR2020-08-18

            } else if (["sb_code", "username", "last_name", "email", "page"].includes(field_name)){
                inner_text = map_dict[field_name];
                filter_value = (inner_text) ? inner_text.toLowerCase() : null;
            } else if (field_name === "school_abbrev") {
                // schoolname cannot be put in user table, because it has no examyear PR2021-07-05
                // lookup schoolname in school_rows instead
                if (map_dict.schoolbase_id){
                    for (let i = 0, dict; dict = school_rows[i]; i++){
                        if(dict.base_id && dict.base_id === map_dict.schoolbase_id) {
                            inner_text = (dict.abbrev)  ? dict.abbrev : "---";
                            filter_value = (inner_text) ? inner_text.toLowerCase() : null;
                            break;
                }}};
            } else if (field_name === "role") {
                const role = map_dict[field_name];
                inner_text = (loc.role_caption && loc.role_caption[role])  ? loc.role_caption[role] : role;
                filter_value = inner_text;
            } else if (field_name === "action"){
                el_div.value = map_dict[field_name];
                filter_value = map_dict[field_name];
            } else if (field_name.slice(0, 5) === "group") {
                // map_dict[field_name] example: perm_system: true
                const db_field = field_name.slice(6);
                // const permit_bool = (map_dict[field_name]) ? map_dict[field_name] : false;
                const permit_bool = (map_dict.usergroups) ? map_dict.usergroups.includes(db_field) : false;

                //console.log("field_name", field_name);
                //console.log("db_field", db_field);
                //console.log("map_dict.usergroups", map_dict.usergroups);
                //console.log("permit_bool", permit_bool);

                filter_value = (permit_bool) ? "1" : "0";
                el_div.className = (permit_bool) ? "tickmark_2_2" : "tickmark_0_0" ;

            } else if ( field_name === "activated") {
                const is_activated = (map_dict[field_name]) ? map_dict[field_name] : false;
                let is_expired = false;
                if(!is_activated) {
                    is_expired = activationlink_is_expired(map_dict.date_joined);
                }
                filter_value = (is_expired) ? "2" : (is_activated) ? "1" : "0"
                el_div.className = (is_activated) ? "tickmark_2_2" : (is_expired) ? "exclamation_0_2" : "tickmark_0_0" ;
// ---  add pointer when not is_activatd
                add_or_remove_class(el_div, "pointer_show", !is_activated)

// ---  add title
                title_text = (is_expired) ? loc.Activationlink_expired + "\n" + loc.Send_activationlink : null
            } else if (field_name === "is_active") {
                const is_inactive = !( (map_dict[field_name]) ? map_dict[field_name] : false );
                // give value '0' when inactive, '1' when active
                filter_value = (is_inactive) ? "0" : "1";

                el_div.className = (is_inactive) ? "inactive_1_3" : "inactive_0_2";

// ---  add title
                title_text = (is_inactive) ? loc.This_user_is_inactive : null;
            } else if ( field_name === "last_login") {
                const datetimeUTCiso = map_dict[field_name]
                const datetimeLocalJS = (datetimeUTCiso) ? new Date(datetimeUTCiso) : null;
                inner_text = format_datetime_from_datetimeJS(loc, datetimeLocalJS);
                filter_value = inner_text;
            }
// ---  put value in innerText and title
            el_div.innerText = inner_text;
            add_or_remove_attr (el_div, "title", !!title_text, title_text);

// ---  add attribute filter_value
        //console.log("filter_value", filter_value);
            add_or_remove_attr (el_div, "data-filter", !!filter_value, filter_value);

        }  // if(el_div && field_name){
    };  // UpdateField

//=========  activationlink_is_expired  ================ PR2020-08-18
    function activationlink_is_expired(datetime_linksent_ISO){
        let is_expired = false;
        const days_valid = 7;
        if(datetime_linksent_ISO){
            const datetime_linksent_LocalJS = new Date(datetime_linksent_ISO);
            const datetime_linkexpires_LocalJS = add_daysJS(datetime_linksent_LocalJS, days_valid)
            const now = new Date();
            const time_diff_in_ms = now.getTime() - datetime_linkexpires_LocalJS.getTime();
            is_expired = (time_diff_in_ms > 0)
        }
        return is_expired;
    }

// +++++++++++++++++ UPLOAD CHANGES +++++++++++++++++ PR2020-08-03

//========= UploadToggle  ============= PR2020-07-31
    function UploadToggle(el_input) {
        //console.log( " ==== UploadToggle ====");
        //console.log( "el_input", el_input);

        mod_dict = {};
        const has_permit = (permit_dict.permit_crud_otherschool) ||
                            (permit_dict.permit_crud_sameschool && selected_btn !== "btn_userpermit");
        if(has_permit){
            const tblRow = get_tablerow_selected(el_input);
            if(tblRow){
                const tblName = get_tblName_from_mapid(tblRow.id);
                const data_dict = get_datadict_from_mapid(tblRow.id)
        //console.log( "tblName", tblName);
        //console.log( "data_dict", data_dict);

                if(!isEmpty(data_dict)){
                    const fldName = get_attr_from_el(el_input, "data-field");
                    let permit_bool = (get_attr_from_el(el_input, "data-filter") === "1");

    // show message when sysadmin tries to delete sysadmin permit
                    const is_request_user = (permit_dict.requsr_pk && permit_dict.requsr_pk === data_dict.id);
                    if(fldName === "group_admin" && is_request_user && permit_bool ){
                        ModConfirmOpen("uergroup", "permission_admin", el_input)
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
                        UploadChanges(upload_dict, url_str);
                    }  // if(fldName === "group_admin" && is_request_user && permit_bool ){
                }  //  if(!isEmpty(data_dict)){
            }  //   if(!!tblRow)
        }  // if(permit_dict.usergroup_system)
    }  // UploadToggle

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

                    if("msg_dictlist" in response){
                        b_ShowModMessages(response.msg_dictlist);
                    }

                    const mode = get_dict_value(response, ["mode"]);
                    if(["delete", 'resend_activation_email'].includes(mode)) {
                        ModConfirmResponse(response);
                    };

                    if ("updated_user_rows" in response) {
                        // must get  tblName from selectedBtn, to get 'usergroup' instead of 'user'
                        const tblName = get_tblName_from_selectedBtn();
                        RefreshDataRows(tblName, response.updated_user_rows, user_rows, true)  // true = update
                    };
                    if ("updated_permit_rows" in response){
                        RefreshDataRows("userpermit", response.updated_permit_rows, permit_rows, true)  // true = is_update
                    }

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

// +++++++++ MOD ADD USER ++++++++++++++++ PR2020-09-18
    function MUA_Open(mode, el_input){
        console.log(" -----  MUA_Open   ---- mode: ", mode)  // modes are: addnew, update
        console.log("permit_dict: ", permit_dict)
        console.log("permit_dict.permit_crud_sameschool: ", permit_dict.permit_crud_sameschool)
        console.log("permit_dict.permit_crud_otherschool: ", permit_dict.permit_crud_otherschool)
        // mode = 'addnew' when called by SubmenuButton
        // mode = 'update' when called by tblRow event

        if (permit_dict.permit_crud_sameschool || permit_dict.permit_crud_otherschool){
            let data_dict = {}, user_pk = null;
            let user_schoolbase_pk = null, user_schoolbase_code = null, user_mapid = null;
            const fldName = get_attr_from_el(el_input, "data-field");
            const is_addnew = (mode === "addnew");

        console.log("fldName: ", fldName)
            if(el_input){
                const tblRow = get_tablerow_selected(el_input);
                user_mapid = tblRow.id;

// --- get existing data_dict from data_rows
                data_dict = get_datadict_from_mapid(tblRow.id);
    //console.log("data_dict", data_dict)
                if(!isEmpty(data_dict)){
                    user_pk = data_dict.id;
                    user_schoolbase_pk = data_dict.schoolbase_id;
                    user_schoolbase_code = data_dict.sb_code;
                }
        // when el_input is not defined: function is mode 'addnew'
            } else if (!permit_dict.permit_crud_otherschool){
                // when new user and not role_admin or role_system: : get user_schoolbase_pk from request_user
                user_schoolbase_pk = permit_dict.requsr_schoolbase_pk;
                user_schoolbase_code = permit_dict.requsr_schoolbase_code;
            }

            selected_user_pk = user_pk

            let user_schoolname = null;
            if(user_schoolbase_pk){
                user_schoolname = user_schoolbase_code
                for(let i = 0, tblRow, dict; dict = school_rows[i]; i++){
                    if (!isEmpty(dict)) {
                        if(user_schoolbase_pk === dict.base_id ) {
                            if (dict.abbrev) {user_schoolname += " - " + dict.abbrev};
                            break;
            }}}};

            mod_MUA_dict = {
                mode: mode, // modes are: addnew, update
                //skip_validate_username: is_addnew,
                //skip_validate_last_name: is_addnew,
                //skip_validate_email: is_addnew,
                user_pk: user_pk,
                user_schoolbase_pk: user_schoolbase_pk,
                user_schoolbase_code: user_schoolbase_code,
                user_schoolname: user_schoolname,
                user_mapid: user_mapid,
                username: (data_dict.username) ? data_dict.username : null,
                last_name: (data_dict.last_name) ? data_dict.last_name : null,
                email: (data_dict.email) ? data_dict.email : null
                };
            console.log("mod_MUA_dict: ", mod_MUA_dict)

    // ---  show only the elements that are used in this tab
            const container_element = document.getElementById("id_mod_user");
            let tab_str = (is_addnew) ? (permit_dict.permit_crud_otherschool) ? "tab_addnew_may_select_school" : "tab_addnew_noschool" : "tab_update";
            b_show_hide_selected_elements_byClass("tab_show", tab_str, container_element)

    // ---  set header text
            const header_text = (is_addnew) ? loc.Add_user : loc.User + ":  " + mod_MUA_dict.username;
            const el_MUA_header = document.getElementById("id_MUA_header");
            el_MUA_header.innerText = header_text;

    // ---  fill selecttable
            if(permit_dict.permit_crud_otherschool){
                MUA_FillSelectTableSchool();
            }

    // ---  remove values from elements
            MUA_ResetElements(true);  // true = also_remove_values

    // ---  put values in input boxes
            el_MUA_schoolname.value = user_schoolname;
            if (mode === "update"){
                el_MUA_username.value = mod_MUA_dict.username;
                el_MUA_last_name.value = mod_MUA_dict.last_name;
                el_MUA_email.value = mod_MUA_dict.email;
            }
    // ---  set focus to next el
            const el_focus = (is_addnew && permit_dict.permit_crud_otherschool) ? el_MUA_schoolname :
                             ( (is_addnew && !permit_dict.permit_crud_otherschool) || (fldName === "username") ) ? el_MUA_username :
                             (fldName === "last_name") ? el_MUA_last_name :
                             (fldName === "email") ? el_MUA_email : null;
            if(el_focus){setTimeout(function (){el_focus.focus()}, 50)};

    // ---  set text and hide info footer
            //el_MUA_footer01.innerText = loc.Click_to_register_new_user;
            //el_MUA_footer02.innerText = loc.We_will_send_an_email_to_the_new_user;
            //el_MUA_footer_container.classList.add(cls_hide);

    // ---  hide loader
            el_MUA_loader.classList.add(cls_hide);

    // ---  hide btn delete when addnew mode
            add_or_remove_class(el_MUA_btn_delete, cls_hide, is_addnew)


    // ---  disable btn submit
            MUA_DisableBtnSave()

    // ---  show modal
            $("#id_mod_user").modal({backdrop: true});

        }  //  if(permit_dict.permit_crud)
    };  // MUA_Open

//========= MUA_DisableBtnSave  ============= PR2021-06-30
   function MUA_DisableBtnSave(is_ok){
// ---  disable btn submit

        const disable_btn_save = (!mod_MUA_dict.user_schoolbase_pk || !el_MUA_username.value ||
                                  !el_MUA_last_name.value || !el_MUA_email.value )
        el_MUA_btn_submit.disabled = disable_btn_save;
        el_MUA_btn_submit.innerText = (mod_MUA_dict.mode === "update") ? loc.Save : loc.Create_user_account;

// ---  hide submit btn when is_ok
        add_or_remove_class(el_MUA_btn_submit, cls_hide, is_ok)

   }  // MUA_DisableBtnSave

//========= MUA_Save  ============= PR2020-08-02 PR2020-08-15 PR2021-06-30
   function MUA_Save(mode) {
        console.log("=== MUA_Save === ");
        console.log("mode: ", mode);
        //  mode = 'validate' when called by el_MUA_btn_submit
        //  mode = "save" after response OK

        // NOT IN USE:
        // send schoolbase, username and email to server after 1500 ms
        // abort if within that period a new value is entered.
        // checked by comparing the timestamp
        // 'args' is either 'save' or a time_stamp number
        // variable 'time_stamp' gets new value 'now' whenever a 'keyup' event occurs
        // MUA_Save has a time-out of 1500 ms
        // parameter 'args' (init_time_stamp) contains the value of time_stamp at the time this 'keyup' event occurred
        // when time_stamp = init_time_stamp, it means that there are no new keyup events within the time-out period

// ---  skip if one of the fields is blank
        let skip = !(el_MUA_username.value && el_MUA_last_name.value && el_MUA_email.value)
        if(!skip){
            // mod_MUA_dict. modes are: 'addnew', 'update'

            // in ModConfirmSave upload_dict.mode can get value "delete" or "resend_activation_email"
            // in this function value of 'mode' is only 'save'

            const upload_mode = (mode === "validate") ? "validate" :
                                //(mode === "resend_activation_email" ) ? "resend_activation_email" :
                                (mode === "save") ? "create" :
                                (mod_MUA_dict.mode === "update") ? "update" : null;

            console.log("mode: ", mode);
            console.log("mod_MUA_dict.mode", mod_MUA_dict.mode);
            console.log("................upload_mode", upload_mode);

   // ---  create mod_dict
            let upload_dict = {}
            if (upload_mode === "resend_activation_email" ){
                upload_dict = { user_pk: map_dict.id,
                               schoolbase_pk: map_dict.schoolbase_pk,
                               mode: upload_mode,
                               mapid: "user_" + map_dict.id,
                                username: {value: map_dict.username}
                              };
            } else if (upload_mode === "update" ){
                upload_dict = { schoolbase_pk: mod_MUA_dict.user_schoolbase_pk,
                                mode: upload_mode,
                                username: el_MUA_username.value,
                                last_name: el_MUA_last_name.value,
                                email: el_MUA_email.value
                              };
            } else if (["validate", "create"].includes(upload_mode)){
                upload_dict = { user_pk: mod_MUA_dict.user_pk,
                                schoolbase_pk: mod_MUA_dict.user_schoolbase_pk,
                                mode: upload_mode,
                                username: el_MUA_username.value,
                                last_name: el_MUA_last_name.value,
                                email: el_MUA_email.value
                              };
            }
            console.log("upload_dict: ", upload_dict);

            // must lose focus, otherwise green / red border won't show
            //el_input.blur();
            // show loader, hide msg_info
            el_MUA_loader.classList.remove(cls_hide);
            el_MUA_footer_container.classList.add(cls_hide);

            const parameters = {"upload": JSON.stringify (upload_dict)}
            let response = "";
            $.ajax({
                type: "POST",
                url: urls.url_user_upload,
                data: parameters,
                dataType:'json',
                success: function (response) {
                    console.log( "response");
                    console.log( response);

                    // hide loader
                    el_MUA_loader.classList.add(cls_hide);

                    MUA_SetMsgElements(response);

                    if ("updated_user_rows" in response) {
                        // must get  tblName from selectedBtn, to get 'usergroup' instead of 'user'
                        const tblName = get_tblName_from_selectedBtn();
                        RefreshDataRows(tblName, response.updated_user_rows, user_rows, true)  // true = update
                    };

                    if ("validation_ok" in response){
                        if(response.validation_ok){
                            MUA_CreateOrUpdate();
                        };
                    };

                },  // success: function (response) {
                error: function (xhr, msg) {
                    console.log(msg + '\n' + xhr.responseText);
                }  // error: function (xhr, msg) {
            });  // $.ajax({
        }
    };  // MUA_Save


//========= MUA_CreateOrUpdate  ============= PR2021-07-05
   function MUA_CreateOrUpdate() {
        console.log("=== MUA_Save === ");
        //  mode = 'validate' when called by el_MUA_btn_submit
        //  mode = "save" after response OK
        // create new user or update existing user

// ---  skip if one of the fields is blank
        let skip = !(el_MUA_username.value && el_MUA_last_name.value && el_MUA_email.value)
        if(!skip){
            console.log("mod_MUA_dict.mode", mod_MUA_dict.mode);
   // ---  create upload_dict
            const upload_mode = (mod_MUA_dict.user_pk) ? "update" : "create";
            const upload_dict = { mode:  upload_mode,
                                schoolbase_pk: mod_MUA_dict.user_schoolbase_pk,
                                username: el_MUA_username.value,
                                last_name: el_MUA_last_name.value,
                                email: el_MUA_email.value
                              };
            if (mod_MUA_dict.user_pk){upload_dict.user_pk = mod_MUA_dict.user_pk}
            console.log("upload_dict: ", upload_dict);

            // must lose focus, otherwise green / red border won't show
            //el_input.blur();
            // show loader, hide msg_info
            el_MUA_loader.classList.remove(cls_hide);
            el_MUA_footer_container.classList.add(cls_hide);

            const parameters = {"upload": JSON.stringify (upload_dict)}
            let response = "";
            $.ajax({
                type: "POST",
                url: urls.url_user_upload,
                data: parameters,
                dataType:'json',
                success: function (response) {
                    console.log( "response");
                    console.log( response);

                    // hide loader
                    el_MUA_loader.classList.add(cls_hide);

                    MUA_SetMsgElements(response);

                    if ("updated_user_rows" in response) {
                        // must get  tblName from selectedBtn, to get 'usergroup' instead of 'user'
                        const tblName = get_tblName_from_selectedBtn();
                        RefreshDataRows(tblName, response.updated_user_rows, user_rows, true)  // true = update
                    };

                },  // success: function (response) {
                error: function (xhr, msg) {
                    console.log(msg + '\n' + xhr.responseText);
                }  // error: function (xhr, msg) {
            });  // $.ajax({
        }
    };  // MUA_CreateOrUpdate

//========= MUA_FillSelectTableSchool  ============= PR2020--09-17
    function MUA_FillSelectTableSchool() {
        console.log("===== MUA_FillSelectTableSchool ===== ");

        const data_rows = school_rows;
        const tblBody_select = document.getElementById("id_MUA_tbody_select");
        tblBody_select.innerText = null;

// ---  loop through dictlist
        let row_count = 0

        if(data_rows && data_rows.length){
            const tblName = "school";
            for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
                if (!isEmpty(data_dict)) {
                    const defaultrole = (data_dict.defaultrole) ? data_dict.defaultrole : 0;
    // only add schools to list whith sme or lower role
                    if (defaultrole <= permit_dict.requsr_role){
        // ---  get info from data_dict
                        const base_id = data_dict.base_id;
                        const country_id = data_dict.country_id;
                        const code = (data_dict.sb_code) ? data_dict.sb_code : "";
                        const abbrev = (data_dict.abbrev) ? data_dict.abbrev : "";

// ---  lookup index where this row must be inserted
                        let ob1 = "", row_index = -1;
                        if (code) { ob1 = code.toLowerCase()};
                        row_index = b_recursive_tblRow_lookup(tblBody_select, ob1, "", "", loc.user_lang);
//--------- insert tblBody_select row at row_index
                        const map_id = "sel_" + tblName + "_" + base_id
                        const tblRow = tblBody_select.insertRow(row_index);

                        row_count += 1;

                        tblRow.id = map_id;
                        tblRow.setAttribute("data-pk", base_id);
                        tblRow.setAttribute("data-ppk", country_id);
                        tblRow.setAttribute("data-value", code + " - " + abbrev);

// ---  add data-sortby attribute to tblRow, for ordering new rows
                        tblRow.setAttribute("data-ob1", ob1);

        // ---  add hover to select row
                        add_hover(tblRow)

        // ---  add first td to tblRow.
                        let td = tblRow.insertCell(-1);
                        let el_div = document.createElement("div");
                            el_div.classList.add("tw_075")
                            el_div.innerText = code;
                            td.appendChild(el_div);

        // ---  add second td to tblRow.
                        td = tblRow.insertCell(-1);
                        el_div = document.createElement("div");
                            el_div.classList.add("tw_150")
                            el_div.innerText = abbrev;
                            td.appendChild(el_div);

                        //td.classList.add("tw_200", "px-2", "pointer_show", "tsa_bc_transparent")

        // ---  add addEventListener
                        tblRow.addEventListener("click", function() {MUA_SelectSchool(tblRow, event.target)}, false);
                    } //  if (defaultrole < permit_dict.requsr_role)
                }  //  if (!isEmpty(item_dict))
            }  // for (const [map_id, data_dict] of data_map.entries())
        }  // if(data_map)

    } // MUA_FillSelectTableSchool

//========= MUA_ResetElements  ============= PR2020-08-03
    function MUA_ResetElements(also_remove_values){
        //console.log( "===== MUA_ResetElements  ========= ");
// ---  loop through input elements
        const fields = ["username", "last_name", "email", "schoolname"]
        for (let i = 0, field, el_input, el_msg; field = fields[i]; i++) {
            el_input = document.getElementById("id_MUA_" + field);
            if(el_input){
                el_input.classList.remove("border_bg_invalid", "border_bg_valid");
                if(also_remove_values){ el_input.value = null};
                let is_enabled = false;
                if  (field === "schoolname") {
                // disable field 'schoolname' when is_update or when not requsr_role_admin and not requsr_role_system
                    if (permit_dict.requsr_role_admin || permit_dict.requsr_role_system) {
                        is_enabled = (mod_MUA_dict.mode === "addnew");
                    }
                } else {
                // disable other fields when no school selected
                    is_enabled = mod_MUA_dict.user_schoolbase_pk;
                }
                add_or_remove_attr (el_input, "readonly", !is_enabled, true);
            }
            el_msg = document.getElementById("id_MUA_msg_" + field);
            if(el_msg){
                el_msg.innerText = (loc.msg_user_info[i]) ? loc.msg_user_info[i] : null;
                el_msg.classList.remove("text-danger")
            }
        }
        el_MUA_footer_container.classList.add(cls_hide);

// ---  reset text on btn cancel
        if(el_MUA_btn_cancel) {el_MUA_btn_cancel.innerText = loc.Cancel};

    }  // MUA_ResetElements

//========= MUA_SetMsgElements  ============= PR2020-08-02
    function MUA_SetMsgElements(response){
        console.log( "===== MUA_SetMsgElements  ========= ");
        // TOD) switch to render msg box
        const err_dict = (response && "msg_err" in response) ? response.msg_err : {}
        const validation_ok = get_dict_value(response, ["validation_ok"], false);


        const el_msg_container = document.getElementById("id_MUA_msg_container")
        let err_save = false;
        let is_ok = (response && "msg_ok" in response);
        if (is_ok) {
            const ok_dict = response.msg_ok;
            document.getElementById("id_msg_01").innerText = get_dict_value(ok_dict, ["msg01"]);
            document.getElementById("id_msg_02").innerText = get_dict_value(ok_dict, ["msg02"]);
            document.getElementById("id_msg_03").innerText = get_dict_value(ok_dict, ["msg03"]);
            document.getElementById("id_msg_04").innerText = get_dict_value(ok_dict, ["msg04"]);

            el_msg_container.classList.remove("border_bg_invalid");
            el_msg_container.classList.add("border_bg_valid");
// ---  show only the elements that are used in this tab
            b_show_hide_selected_elements_byClass("tab_show", "tab_ok");

        } else {
            // --- loop through input elements
            if("save" in err_dict){

        console.log( "err_dict", err_dict);
                const save_dict = err_dict.save
        console.log( "save_dict", save_dict);
                err_save = true;

                document.getElementById("id_msg_01").innerText = get_dict_value(save_dict, ["msg01"]);
                document.getElementById("id_msg_02").innerText = get_dict_value(save_dict, ["msg02"]);
                document.getElementById("id_msg_03").innerText = get_dict_value(save_dict, ["msg03"]);
                document.getElementById("id_msg_04").innerText = get_dict_value(save_dict, ["msg04"]);

                el_msg_container.classList.remove("border_bg_valid");
                el_msg_container.classList.add("border_bg_invalid");
// ---  show only the elements that are used in this tab
                b_show_hide_selected_elements_byClass("tab_show", "tab_ok");

            } else {
                const fields = ["username", "last_name", "email"]
                for (let i = 0, field; field = fields[i]; i++) {
                    const msg_err = get_dict_value(err_dict, [field]);
                    const msg_info = loc.msg_user_info[i];
        //console.log( "-----------field", field);
        //console.log( "msg_err", msg_err);
        //console.log( "msg_info", msg_info);
                    let el_input = document.getElementById("id_MUA_" + field);

                    const must_blur = ( (!!msg_err && !el_input.classList.contains("border_bg_invalid")) ||
                                        (!msg_err && !el_input.classList.contains("border_bg_valid")) );
                    if( must_blur) { el_input.blur() };
                    add_or_remove_class (el_input, "border_bg_invalid", (!!msg_err));
                    add_or_remove_class (el_input, "border_bg_valid", (!msg_err));

                    let el_msg = document.getElementById("id_MUA_msg_" + field);
                    add_or_remove_class (el_msg, "text-danger", (!!msg_err));
                    el_msg.innerText = (!!msg_err) ? msg_err : msg_info
                }
            }

            el_MUA_btn_submit.disabled = !validation_ok;
            if(validation_ok){el_MUA_btn_submit.focus()}
        }

// ---  show message in footer when no error and no ok msg
        add_or_remove_class(el_MUA_footer_container, cls_hide, !validation_ok )

// ---  hide submit btn and delete btnwhen is_ok or when error
        add_or_remove_class(el_MUA_btn_submit, cls_hide, is_ok || err_save)
        add_or_remove_class(el_MUA_btn_delete, cls_hide, is_ok || err_save)

// ---  set text on btn cancel
        if (el_MUA_btn_cancel){
            el_MUA_btn_cancel.innerText = ((is_ok || err_save) ? loc.Close : loc.Cancel);
            if(is_ok || err_save){el_MUA_btn_cancel.focus()}
        }
    }  // MUA_SetMsgElements

//=========  MUA_SelectSchool  ================ PR2020-09-25
    function MUA_SelectSchool(tblRow) {
        //console.log( "===== MUA_SelectSchool ========= ");
        //console.log( tblRow);
// ---  get clicked tablerow
        if(tblRow) {
// ---  deselect all highlighted rows
            DeselectHighlightedRows(tblRow, cls_selected)
// ---  highlight clicked row
            tblRow.classList.add(cls_selected)
// ---  get pk from id of select_tblRow
            mod_MUA_dict.user_schoolbase_pk = get_attr_from_el_int(tblRow, "data-pk");
            mod_MUA_dict.country_pk = get_attr_from_el_int(tblRow, "data-ppk");
            mod_MUA_dict.user_schoolname = get_attr_from_el(tblRow, "data-value");
// ---  put value in input box
            el_MUA_schoolname.value = mod_MUA_dict.user_schoolname
            MUA_headertext();
            MUA_ResetElements();

            el_MUA_username.focus()
        }
    }  // MUA_SelectSchool

//=========  MUA_InputSchoolname  ================ PR2020-09-24 PR2021-01-01
    function MUA_InputSchoolname(el_input, event_key) {
        //console.log( "===== MUA_InputSchoolname  ========= ");
        //console.log( "event_key", event_key);

        if(el_input){
// ---  filter rows in table select_school
            const filter_dict = MUA_Filter_SelectRows(el_input.value);
            //console.log( "filter_dict", filter_dict);
// ---  if filter results have only one school: put selected school in el_MUA_schoolname
            const selected_pk = Number(filter_dict.selected_pk);
            if (selected_pk) {
                el_input.value = filter_dict.selected_value
    // ---  put pk of selected school in mod_MUA_dict
                mod_MUA_dict.user_schoolbase_pk = selected_pk;
                mod_MUA_dict.user_schoolname = filter_dict.selected_value;

                MUA_headertext();
                MUA_ResetElements();
    // ---  Set focus to flied 'username'
                el_MUA_username.focus()
            }  // if (!!selected_pk)
        }
    }; // MUA_InputSchoolname

//=========  MUA_InputKeyup  ================ PR2020-09-24
    function MUA_InputKeyup(el_input, event_key) {
        //console.log( "===== MUA_InputKeyup  ========= ");
        //console.log( "event_key", event_key);

        const fldName = get_attr_from_el(el_input, "data-field");
        if(el_input){
            if(event_key === "Shift"){
                // pass
            } else if(event_key === "Enter" && fldName === "username"){
                el_MUA_last_name.focus();
            } else if(event_key === "Enter" && fldName === "last_name"){
                el_MUA_email.focus();
            } else {
                let field_value = el_input.value;
            //console.log( "fldName", fldName);
            //console.log( "field_value", field_value);
                // fldName is 'username', 'last_name' or 'email' . fldName "schoolname" is handled in MUA_InputSchoolname
                if (fldName === "username" && field_value){
                    field_value = field_value.replace(/, /g, "_"); // replace comma or space with "_"
                    field_value = replaceChar(field_value)
                    if (field_value !== el_input.value) { el_input.value = field_value}
                }
                mod_MUA_dict[fldName] = (field_value) ? field_value : null
                mod_MUA_dict["has_changed_" + fldName] = true;

                MUA_ResetElements();
                // send schoolbase, username and email to server after 1000 ms
                // abort if within that period a new value is entered.
                // checked by comparing the timestamp
                //time_stamp = Number(Date.now())
                //setTimeout(MUA_Save, 1500, time_stamp);  // time_stamp is an argument passed to the function  MUA_Save.

                MUA_DisableBtnSave()

            }
        }
    }; // MUA_InputKeyup

//========= MUA_Filter_SelectRows  ======== PR2020-09-19
    function MUA_Filter_SelectRows(filter_text) {
        //console.log( "===== MUA_Filter_SelectRows  ========= ");
        //console.log( "filter_text: <" + filter_text + ">");
        const filter_text_lower = (filter_text) ? filter_text.toLowerCase() : "";
        let has_selection = false, has_multiple = false;
        let sel_value = null, sel_pk = null, sel_mapid = null;
        let row_count = 0;

        let tblBody_select = document.getElementById("id_MUA_tbody_select");
        for (let i = 0, tblRow; tblRow = tblBody_select.rows[i]; i++) {
            if (tblRow){
                let hide_row = false
// ---  show all rows if filter_text = ""
                if (filter_text_lower){
                    const data_value = get_attr_from_el(tblRow, "data-value")
// ---  show row if filter_text_lower is found in data_value, hide when data_value is blank
                    hide_row = (data_value) ? hide_row = (!data_value.toLowerCase().includes(filter_text_lower)) : true;
                };
                if (hide_row) {
                    tblRow.classList.add(cls_hide)
                } else {
                    tblRow.classList.remove(cls_hide);
                    row_count += 1;
// ---  put values from first row that is shown in select_value etc
                    if(!has_selection ) {
                        sel_pk = get_attr_from_el(tblRow, "data-pk");
                        sel_value = get_attr_from_el(tblRow, "data-value");
                        sel_mapid = tblRow.id;
                    } else {
                        has_multiple = true;
                    }
                    has_selection = true;
        }}};
// ---  set select_value etc null when multiple items found
        if (has_multiple){
            sel_pk = null;
            sel_value = null,
            sel_mapid = null;
        }
        return {selected_pk: sel_pk, selected_value: sel_value, selected_mapid: sel_mapid};
    }; // MUA_Filter_SelectRows

//=========  MUA_headertext  ================ PR2020-09-25
    function MUA_headertext(mode) {
        let header_text = (mode === "update") ? loc.User + ":  " + mod_MUA_dict.username : loc.Add_user;
        if(mod_MUA_dict.user_schoolbase_pk){ header_text = loc.Add_user_to + mod_MUA_dict.user_schoolname;}
        document.getElementById("id_MUA_header").innerText = header_text;
    }  // MUA_headertext

// +++++++++ END MOD USER ++++++++++++++++++++++++++++++++++++++++++++++++++++

// +++++++++ MOD UPLOAD PERMITS ++++++++++++++++ PR2021-04-20
    function MUP_Open(){
        console.log(" -----  MUP_Open   ----")

    // ---  show modal
        $("#id_mod_upload_permits").modal({backdrop: true});
   } //  MUP_Open
// +++++++++ END MOD UPLOAD PERMITS ++++++++++++++++++++++++++++++++++++++++++++++++++++

// +++++++++ MOD GROUP PERMIT ++++++++++++++++ PR2021-03-19
    function MUPM_Open(mode, el_input){
        console.log(" -----  MUPM_Open   ---- mode: ", mode)  // modes are: addnew, update
        // mode = 'addnew' when called by SubmenuButton
        // mode = 'update' when called by tblRow event

        const is_addnew = (mode === "addnew");
        mod_MUPM_dict = {is_addnew: (is_addnew) ? "create" : "update" };
        mod_MUPM_dict = {mode: mode};

        let userpermit_pk = null, role = null, permit_page = null, permit_action = null, permit_sequence = null;
        if(el_input){
            const tblRow = get_tablerow_selected(el_input);
            const map_dict = get_mapdict_from_datamap_by_id(permit_map, tblRow.id);
        console.log("map_dict", map_dict)
            if(!isEmpty(map_dict)){
                userpermit_pk = map_dict.id;
                role = map_dict.role;
                permit_page = map_dict.page;
                permit_action = map_dict.action;
                permit_sequence = map_dict.sequence;
            }
        }
        mod_MUPM_dict.userpermit_pk = userpermit_pk;

        document.getElementById("id_MUPM_action").value = permit_action;

    // ---  show modal
        $("#id_mod_userpermit").modal({backdrop: true});
    };  // MUPM_Open

    function MUPM_Save(mode){ //PR2021-03-20
        console.log("=== MUPM_Save === ");
        //  mode = 'save', 'delete'
        const upload_mode = (mode === "delete") ? "delete" :
                            (mod_MUPM_dict.mode === "addnew") ? "create" : "update";

        const el_MUPM_role = document.getElementById("id_MUPM_role")
        const role = (el_MUPM_role && el_MUPM_role.value) ? el_MUPM_role.value : null;
        const permit_page = document.getElementById("id_MUPM_page").value;
        const permit_action = document.getElementById("id_MUPM_action").value;
        const sequence_value = true; //document.getElementById("id_MUPM_sequence").value;
        const permit_sequence_int = 0; //(Number(sequence_value)) ? Number(sequence_value) : 1;
// ---  create mod_dict
        const url_str = urls.url_userpermit_upload;
        const upload_dict = {mode: upload_mode,
                            userpermit_pk: mod_MUPM_dict.userpermit_pk,
                            role: role,
                            page: permit_page,
                            action: permit_action,
                            sequence: permit_sequence_int};
        console.log("upload_dict: ", upload_dict);

        const parameters = {"upload": JSON.stringify (upload_dict)}
        let response = "";
        $.ajax({
            type: "POST",
            url: url_str,
            data: parameters,
            dataType:'json',
            success: function (response) {
                console.log( "response");
                console.log( response);

                // hide loader
                el_MUA_loader.classList.add(cls_hide);

                if ("updated_list" in response){
                    for (let i = 0, updated_dict; updated_dict = response.updated_list[i]; i++) {
                        refresh_permitmap_item(updated_dict);
                    }
                }
            },  // success: function (response) {
            error: function (xhr, msg) {
                console.log(msg + '\n' + xhr.responseText);
            }  // error: function (xhr, msg) {
        });  // $.ajax({

        $("#id_mod_userpermit").modal("hide");
    }  // MUPM_Save

//^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

//========= MUPM_FillSelectTableDepartment  ============= PR2020--09-30
    function MUPM_FillSelectTableDepartment() {
        console.log("===== MUPM_FillSelectTableDepartment ===== ");
        //console.log("department_map", department_map);

        const data_map = department_map;
        const tblBody_select = document.getElementById("id_MUPM_tbody_select");
        tblBody_select.innerText = null;

// ---  loop through data_map
        let row_count = 0
        if(data_map.size > 1) {
            MUPM_FillSelectRow(tblBody_select, {}, "<" + loc.All_departments + ">");
        }
        for (const [map_id, dict] of data_map.entries()) {
            MUPM_FillSelectRow(tblBody_select, dict);
        }

    } // MUPM_FillSelectTableDepartment

//========= MUPM_FillSelectRow  ============= PR2020--09-30
    function MUPM_FillSelectRow(tblBody_select, dict, select_all_text) {
        console.log("===== MUPM_FillSelectRowDepartment ===== ");
        // add_select_all when not isEmpty(dict)
        //console.log("dict", dict);
        let pk_int = null, map_id = null, abbrev = null
        if (isEmpty(dict)){
            pk_int = 0;
            map_id = "sel_depbase_selectall";
            abbrev = select_all_text
        } else {
            pk_int = dict.base_id;
            map_id = "sel_depbase_" + dict.base_id;
            abbrev = (dict.abbrev) ? dict.base_code : "";
        };
        // check if this dep is in mod_MUPM_dict.depbases. Set tickmark if yes
        let selected_int = 0;
        if(mod_MUPM_dict.depbases){
            const arr = mod_MUPM_dict.depbases.split(";");
            arr.forEach((obj, i) => {
                 if (pk_int === Number(obj)) { selected_int = 1}
             });
        }
        const tickmark_class = (selected_int === 1) ? "tickmark_2_2" : "tickmark_0_0";

        const tblRow = tblBody_select.insertRow(-1);
        tblRow.id = map_id;
        tblRow.setAttribute("data-pk", pk_int);
        tblRow.setAttribute("data-selected", selected_int);

//- add hover to select row
        add_hover(tblRow)

// --- add first td to tblRow.
        let td = tblRow.insertCell(-1);
        let el_div = document.createElement("div");
            el_div.classList.add("tw_032", tickmark_class)
              td.appendChild(el_div);

// --- add second td to tblRow.
        td = tblRow.insertCell(-1);
        el_div = document.createElement("div");
            el_div.classList.add("tw_150")
            el_div.innerText = abbrev;
            td.appendChild(el_div);

        td.classList.add("tw_200", "px-2", "pointer_show") // , "tsa_bc_transparent")

//--------- add addEventListener
        tblRow.addEventListener("click", function() {MUPM_SelectDepartment(tblRow)}, false);
    } // MUPM_FillSelectRow

//========= MUPM_SelectDepartment  ============= PR2020-10-01
    function MUPM_SelectDepartment(tblRow){
        console.log( "===== MUPM_SelectDepartment  ========= ");
        //console.log( "event_key", event_key);

        if(tblRow){
            let is_selected = (!!get_attr_from_el_int(tblRow, "data-selected"));
            let pk_int = get_attr_from_el_int(tblRow, "data-pk");
            const is_select_all = (!pk_int);
        console.log( "is_selected", is_selected);
        console.log( "pk_int", pk_int);
// ---  toggle is_selected
            is_selected = !is_selected;

            const tblBody_selectTable = tblRow.parentNode;
            if(is_select_all){
// ---  if is_select_all: select/ deselect all rows
                for (let i = 0, row, el, set_tickmark; row = tblBody_selectTable.rows[i]; i++) {
                    MUPM_set_selected(row, is_selected)
                }
            } else {
// ---  put new value in this tblRow, show/hide tickmark
                MUPM_set_selected(tblRow, is_selected)

// ---  select row 'select_all' if all other rows are selected, deselect otherwise
                // set 'select_all' true when all other rows are clicked
                let has_rows = false, unselected_rows_found = false;
                for (let i = 0, row; row = tblBody_selectTable.rows[i]; i++) {
                    let row_pk = get_attr_from_el_int(row, "data-pk");
                    // skip row 'select_all'
                    if(row_pk){
                        has_rows = true;
                        if(!get_attr_from_el_int(row, "data-selected")){
                            unselected_rows_found = true;
                            break;
                        }
                    }
                }
// ---  set tickmark in row 'select_all'when has_rows and no unselected_rows_found
                const tblRow_selectall = document.getElementById("sel_depbase_selectall")
                MUPM_set_selected(tblRow_selectall, (has_rows && !unselected_rows_found))
            }
// check for double abbrev in deps
            const fldName = "abbrev";
            const msg_err = validate_duplicates_in_department(loc, "school", fldName, loc.Abbreviation, mod_MUPM_dict.mapid, mod_MUPM_dict.abbrev)
            const el_msg = document.getElementById("id_MUPM_msg_" + fldName);
            el_msg.innerText = msg_err;
            add_or_remove_class(el_msg, cls_hide, !msg_err)

            el_MUPM_btn_save.disabled = (!!msg_err);
        }
    }  // MUPM_SelectDepartment

//========= MUPM_set_selected  ============= PR2020-10-01
    function MUPM_set_selected(tblRow, is_selected){
        //console.log( "  ---  MUPM_set_selected  --- ", is_selected);
// ---  put new value in tblRow, show/hide tickmark
        if(tblRow){
            tblRow.setAttribute("data-selected", ( (is_selected) ? 1 : 0) )
            const img_class = (is_selected) ? "tickmark_2_2" : "tickmark_0_0"
            const el = tblRow.cells[0].children[0];
            //if (el){add_or_remove_class(el, "tickmark_2_2", is_selected , "tickmark_0_0")}
            if (el){el.className = img_class}
        }
    }  // MUPM_set_selected

//========= MUPM_get_selected_depbases  ============= PR2020-10-07
    function MUPM_get_selected_depbases(){
        console.log( "  ---  MUPM_get_selected_depbases  --- ")
        const tblBody_select = document.getElementById("id_MUPM_tbody_select");
        let dep_list_arr = [];
        for (let i = 0, row; row = tblBody_select.rows[i]; i++) {
            let row_pk = get_attr_from_el_int(row, "data-pk");
            // skip row 'select_all'
            if(row_pk){
                if(!!get_attr_from_el_int(row, "data-selected")){
                    dep_list_arr.push(row_pk);
                }
            }
        }
        dep_list_arr.sort((a, b) => a - b);
        const dep_list_str = dep_list_arr.join(";");
        console.log( "dep_list_str", dep_list_str)
        return dep_list_str;
    }  // MUPM_get_selected_depbases

//^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


//========= HandleInputChange  ===============PR2021-03-20
    function HandleInputChange(el_input){
        console.log(" --- HandleInputChange ---")

        const tblRow = get_tablerow_selected(el_input)
        const map_id = tblRow.id
        if (map_id){
            const map_dict = get_mapdict_from_datamap_by_id(permit_map, map_id)
        console.log("map_dict", map_dict)
            const fldName = get_attr_from_el(el_input, "data-field")
            const userpermit_pk = map_dict.id;
            const map_value = map_dict[fldName];
            let new_value = el_input.value;
            if(fldName === "sequence"){
                 new_value = (Number(new_value)) ? Number(new_value) : 1;
            }

            if(new_value !== map_value){
        // ---  create mod_dict
                const url_str = urls.url_userpermit_upload;
                const upload_dict = {mode: "update",
                                    userpermit_pk: userpermit_pk};
                upload_dict[fldName] = new_value;
                console.log("upload_dict: ", upload_dict);

        // ---  upload changes
                UploadChanges(upload_dict, url_str);
            }
        }
    };  // HandleInputChange

// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2020-08-03 PR2021-06-30
    function ModConfirmOpen(tblName, mode, el_input) {
        console.log(" -----  ModConfirmOpen   ----")
        // values of mode are : "delete", "is_active" or "resend_activation_email", "permission_admin"

        console.log("mode", mode )
        console.log("tblName", tblName )

// ---  get selected_pk
        let selected_pk = null;
        // tblRow is undefined when clicked on delete btn in submenu btn or form (no inactive btn)
        const tblRow = get_tablerow_selected(el_input);
        if(tblRow){
            selected_pk = get_attr_from_el_int(tblRow, "data-pk")
        } else {
            selected_pk = (tblName === "userpermit") ? selected_userpermit_pk : selected_user_pk;
        }
        console.log("tblRow", tblRow )
        console.log("selected_pk", selected_pk )

// --- get data_dict from tblName and selected_pk
        const data_dict = get_datadict_from_pk(tblName, selected_pk)
        console.log("data_dict", data_dict);

// ---  get info from data_dict
        const is_request_user = (data_dict && permit_dict.requsr_pk && permit_dict.requsr_pk === data_dict.id)
        //console.log("permit_map", permit_map)
        //console.log("data_dict", data_dict)

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
        }

// ---  put text in modal form
        let dont_show_modal = false;
        const is_mode_permission_admin = (mode === "permission_admin");
        const is_mode_send_activation_email = (mode === "send_activation_email");
        //console.log("mode", mode)
        const inactive_txt = (mod_dict.current_isactive) ? loc.Make_user_inactive : loc.Make_user_active;
        const header_text = (mode === "delete") ? (tblName === "userpermit") ? loc.Delete_permission : loc.Delete_user :
                            (mode === "is_active") ? inactive_txt :
                            (is_mode_send_activation_email) ? loc.Send_activation_email :
                            (is_mode_permission_admin) ? loc.Set_permissions : "";

        let msg_list = [];
        let hide_save_btn = false;
        if(!has_selected_item){
            msg_list = [loc.No_user_selected];
            hide_save_btn = true;
        } else {
            if(tblName === "userpermit"){
                const action = (data_dict.action) ? data_dict.action  : "-";
                const page = (data_dict.page) ? data_dict.page  : "-";
                const msg_txt = [loc.Action, " '", action, "'", loc.on_page, "'",page, "'", loc.will_be_deleted].join("");
                msg_list = [msg_txt, loc.Do_you_want_to_continue];

            } else {

                const username = (data_dict.username) ? data_dict.username  : "-";
                if(mode === "delete"){
                    if(is_request_user){
                        msg_list = [loc.Sysadm_cannot_delete_own_account];
                        hide_save_btn = true;
                    } else {
                        msg_list = [loc.User + " '" + username + "'" + loc.will_be_deleted,
                                    loc.Do_you_want_to_continue];
                    }
                } else if(mode === "is_active"){
                    if(is_request_user && mod_dict.current_isactive){
                        msg_list = [loc.Sysadm_cannot_set_inactive];
                        hide_save_btn = true;
                    } else {
                        const inactive_txt = (mod_dict.current_isactive) ? loc.will_be_made_inactive : loc.will_be_made_active
                        msg_list = [loc.User + " '" + username + "'" + inactive_txt,
                                    loc.Do_you_want_to_continue];
                    }
                } else if(is_mode_permission_admin){
                    hide_save_btn = true;
                    const fldName = get_attr_from_el(el_input, "data-field")
                    if (fldName === "group_admin") {
                        msg_list = [loc.Sysadm_cannot_remove_sysadm_perm]
                    }
                } else if (is_mode_send_activation_email) {
                    const is_expired = activationlink_is_expired(data_dict.date_joined);
                    dont_show_modal = (data_dict.activated);
                    if(!dont_show_modal){
                        if(is_expired) {
                            msg_list.push(loc.Activationlink_expired);
                        };
                        msg_list.push(loc.We_will_send_an_email_to_user + " '" + username + "'.");
                        msg_list.push(loc.Do_you_want_to_continue);
                    }
                }



            }
        }
        if(!dont_show_modal){
            el_confirm_header.innerText = header_text;
            el_confirm_loader.classList.add(cls_visible_hide)
            el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");

            const msg_html = (msg_list.length) ? msg_list.join("<br>") : null;
            el_confirm_msg_container.innerHTML = msg_html;

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
        }

    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2019-06-23
    function ModConfirmSave() {
        console.log(" --- ModConfirmSave --- ");
        console.log("mod_dict: ", mod_dict);
        let tblRow = document.getElementById(mod_dict.mapid);

// ---  when delete: make tblRow red, before uploading
        if (tblRow && mod_dict.mode === "delete"){
            ShowClassWithTimeout(tblRow, "tsa_tr_error");
        }

        let close_modal = false, url_str = null;
        const upload_dict = {mode: mod_dict.mode, mapid: mod_dict.mapid};

        if(mod_dict.table === "userpermit"){
            if (mod_dict.mode === "delete"){
                url_str = urls.url_userpermit_upload;
                upload_dict.userpermit_pk = mod_dict.userpermit_pk;
            }
        } else {
            if(["delete", 'resend_activation_email'].includes(mod_dict.mode)) {
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
                    }
                }
            }

    // ---  Upload Changes
            url_str = urls.url_user_upload;
            upload_dict.user_pk = mod_dict.user_pk;
            upload_dict.schoolbase_pk = mod_dict.user_ppk;
            if (mod_dict.mode === "is_active") {
                upload_dict.is_active = mod_dict.new_isactive;
            };
        };
// ---  Upload changes
        UploadChanges(upload_dict, url_str);
// ---  hide modal
        if(close_modal) {
            $("#id_mod_confirm").modal("hide");
        }
    }  // ModConfirmSave

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
            let msg_list = [];
            if ("msg_err" in response) {
                msg_list.push(get_dict_value(response, ["msg_err", "msg01"], ""));
                if (mod_dict.mode === "resend_activation_email") {
                     msg_list.push(loc.Activation_email_not_sent);
                }
                el_confirm_msg_container.classList.add("border_bg_invalid");
            } else if ("msg_ok" in response){
                msg_list.push(get_dict_value(response, ["msg_ok", "msg01"]));
                msg_list.push(get_dict_value(response, ["msg_ok", "msg02"]));
                msg_list.push(get_dict_value(response, ["msg_ok", "msg03"]));
                el_confirm_msg_container.classList.add("border_bg_valid");
            }

            const msg_html = (msg_list.length) ? msg_list.join("<br>") : null;
            el_confirm_msg_container.innerHTML = msg_html;
            el_confirm_btn_cancel.innerText = loc.Close
            el_confirm_btn_save.classList.add(cls_hide);
        } else {
        // hide mod_confirm when no message
            $("#id_mod_confirm").modal("hide");
        }
    }  // ModConfirmResponse

//###########################################################################

//=========  RefreshDataRowsAfterUpload  ================ PR2021-08-05
function RefreshDataRowsAfterUpload(response) {
    console.log(" --- RefreshDataRowsAfterUpload  ---");
    console.log("response:", response);
    const is_test = (!!response && !!response.is_test) ;
    if(!is_test && response && "updated_user_rows" in response) {
        RefreshDataRows("user", response.updated_user_rows, user_rows, true)  // true = update
    }

}  // RefreshDataRowsAfterUpload

//=========  RefreshDataRowsPermitsAfterUpload  ================ PR2021-07-20
    function RefreshDataRowsPermitsAfterUpload(response) {
        console.log(" --- RefreshDataRowsPermitsAfterUpload  ---");
        console.log( "response", response);

        const is_test = (response && response.is_test);
        console.log( "is_test", is_test);
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
        console.log(" --- RefreshDataRows  ---");
        console.log("page_tblName", page_tblName);
        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length

        if (update_rows && update_rows.length ) {
            const field_setting = field_settings[page_tblName];
            console.log("field_setting", field_setting);
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
        console.log(" --- RefreshDatarowItem  ---");
        //console.log("page_tblName", page_tblName);
        //console.log("update_dict", update_dict);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);
            console.log("is_created", is_created);

            let field_error_list = []
            const error_list = get_dict_value(update_dict, ["error"], []);
            console.log("error_list", error_list);

            if(error_list && error_list.length){
    // - show modal messages
                b_ShowModMessages(error_list);

    // - add fields with error in field_error_list, to put old value back in field
                for (let i = 0, msg_dict ; msg_dict = error_list[i]; i++) {
                    if ("field" in msg_dict){field_error_list.push(msg_dict.field)};
                };
            //} else {
            // close modal MSJ when no error --- already done in modal
                //$("#id_mod_subject").modal("hide");
            }

            const col_hidden = (columns_hidden[page_tblName]) ? columns_hidden[page_tblName] : [];

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

// --- get existing data_dict from map_id
                const [dict, index] = get_datadict_with_index_from_mapid(map_id);
                const data_dict = dict;
                const datarow_index = index;

// ++++ deleted ++++
                if(is_deleted){
                    // delete row from data_rows. Splice returns array of deleted rows
                    const deleted_row_arr = data_rows.splice(datarow_index, 1)
                    const deleted_row_dict = deleted_row_arr[0];
        console.log("deleted_row_dict", deleted_row_dict);
        console.log("deleted_row_dict.mapid", deleted_row_dict.mapid);

        //--- delete tblRow
                    if(deleted_row_dict && deleted_row_dict.mapid){
                        const tblRow_tobe_deleted = document.getElementById(deleted_row_dict.mapid);
        console.log("tblRow_tobe_deleted", tblRow_tobe_deleted);
                        if (tblRow_tobe_deleted ){tblRow_tobe_deleted.parentNode.removeChild(tblRow_tobe_deleted)};
                    }
                } else {

// +++++++++++ updated row +++++++++++
    // ---  check which fields are updated, add to list 'updated_columns'
                    if(!isEmpty(data_dict) && field_names){
                        let updated_columns = [];
        //console.log("update_dict", update_dict);
                        // skip first column (is margin)
                        // col_field is the name of the column on page, not the db_field
                        for (let i = 1, col_field, old_value, new_value; col_field = field_names[i]; i++) {

                            let has_changed = false;
                            if (col_field.slice(0, 5) === "group") {
                            // data_dict.usergroups example: "anlz;auth1;auth2;auth3;edit;read"
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
        //console.log("updated_columns", updated_columns);

// ---  update fields in data_row
                        for (const [key, new_value] of Object.entries(update_dict)) {
                            if (key in data_dict){
                                if (new_value !== data_dict[key]) {
                                    data_dict[key] = new_value
                        }}};

        // ---  update field in tblRow
                        // note: when updated_columns is empty, then updated_columns is still true.
                        // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
                        if(updated_columns.length){

// --- get existing tblRow
                            let tblRow = document.getElementById(map_id);
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
                                        }
                                    }
                                };  //  for (let i = 1, el_fldName, el; el = tblRow.cells[i]; i++) {
                            };  // if(tblRow){
                        }; //  if(updated_columns.length){
                    };  //  if(!isEmpty(data_dict) && field_names){
                };  // if(is_deleted){
            };  // if(is_created)
        };
    }  // RefreshDatarowItem


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
            Filter_TableRows(tblBody_datatable);
        }
    }; // function HandleFilterKeyup


//========= HandleFilterToggle  =============== PR2020-07-21 PR2020-09-14 PR2021-03-23
    function HandleFilterToggle(el_input) {
        //console.log( "===== HandleFilterToggle  ========= ");

    // - get col_index and filter_tag from  el_input
        const col_index = get_attr_from_el(el_input, "data-colindex")
        const filter_tag = get_attr_from_el(el_input, "data-filtertag")
        const field_name = get_attr_from_el(el_input, "data-field")

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
        Filter_TableRows(tblBody_datatable);

    };  // HandleFilterToggle

//========= Filter_TableRows  ====================================
    function Filter_TableRows() {  // PR2019-06-09 PR2020-08-31
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

        for (let i = 0, tblRow, show_row; tblRow = tblBody_datatable.rows[i]; i++) {
            tblRow = tblBody_datatable.rows[i]
            show_row = t_ShowTableRowExtended(filter_dict, tblRow);
            add_or_remove_class(tblRow, cls_hide, !show_row)
        }
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
                        } else if(filter_tag === "activated"){
                            const el_value = get_attr_from_el_int(el, "data-value")
                            if (filter_text && el_value !== filter_text ) {hide_row = true};
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

        Filter_TableRows(tblBody_datatable);

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

//=========  MSED_Response  ================ PR2020-12-18 PR2021-05-10
    function MSED_Response(new_setting) {
        //console.log( "===== MSED_Response ========= ");

// ---  upload new selected_pk
// also retrieve the tables that have been changed because of the change in examyear / dep
        const datalist_request = {
                setting: new_setting,
                user_rows: {get: true},
                school_rows: {get: true}
            };
        DatalistDownload(datalist_request);

    }  // MSED_Response
//###########################################################################
//=========  MSSSS_Response  ================ PR2021-04-23  PR2021-07-26
    function MSSSS_Response(tblName, selected_dict, selected_pk) {
        console.log( "===== MSSSS_Response ========= ");

        // Note: when tblName = school: pk_int = schoolbase_pk
        if(selected_pk === -1) { selected_pk = null};

// ---  put new selected_pk in setting_dict
        setting_dict.sel_schoolbase_pk = selected_pk;

// ---  upload new setting and refresh page
        let datalist_request = {setting: {page: "page_user", sel_schoolbase_pk: selected_pk}};
        DatalistDownload(datalist_request);

    }  // MSSSS_Response

//###########################################################################
//========= set_columns_hidden  ====== PR2021-04-26
    function set_columns_hidden() {
        //console.log( "===== set_columns_hidden  === ");
        //console.log( "permit_dict", permit_dict);

        if (permit_dict.requsr_role_system) {
            columns_hidden =  [];
        } else if (permit_dict.requsr_role_admin) {
            columns_hidden = ["group_auth1", "group_auth2", "group_auth3"];
        } else if (permit_dict.requsr_role_insp) {
            columns_hidden =  ["group_auth3"];
        } else if (permit_dict.requsr_role_comm) {
            columns_hidden =  ["group_edit", "group_auth1", "group_auth2", "group_anlz"];
        } else if (permit_dict.requsr_role_school) {
            columns_hidden = ["sb_code", "school_abbrev", "group_auth3", "group_anlz"];
        }

    };  // set_columns_hidden


//###########################################################################

//========= get_datadict_with_index_from_mapid  ====== PR2021-08-01
    function get_datadict_with_index_from_mapid(map_id) {
        //console.log( "===== get_datadict_with_index_from_mapid  === ");
        let data_dict = null, row_index = null;
        if(map_id){
            const arr = get_tblName_pk_from_mapid(map_id);
            if(arr && arr[1] && Number(arr[1])){
                const data_rows = get_data_rows(arr[0]) ;
                const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", Number(arr[1]));
                if (!isEmpty(found_dict)) {data_dict = found_dict};
                row_index = index;
            };
        };
        return [data_dict, row_index];
    };  // get_datadict_with_index_from_mapid

//========= get_datadict_from_mapid  ====== PR2021-08-01
    function get_datadict_from_mapid(map_id) {
        console.log( "===== get_datadict_from_mapid  === ");
        let data_dict = null;
        if(map_id){
            const arr = get_tblName_pk_from_mapid(map_id);
        console.log( "arr", arr);
            data_dict = get_datadict_from_pk(arr[0], arr[1]);
        };
        return data_dict;
    };  // get_datadict_from_mapid

    function get_datadict_from_pk(tblName, pk_int) {
        console.log( "===== get_datadict_from_pk  === ");
        console.log( "tblName", tblName);
        console.log( "pk_int", pk_int, typeof pk_int );
        let data_dict = null;
        if(tblName && pk_int){
            const data_rows = get_data_rows(tblName) ;
        console.log( "data_rows", data_rows, typeof data_rows );
            const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);
            if (!isEmpty(found_dict)) {data_dict = found_dict};

        };
        return data_dict;
    };  // get_datadict_from_pk

    function get_tblName_from_selectedBtn() {  //P R2021-08-01
        // HandleBtnSelect sets tblName to default "user" when there is no selected_btn
        // this happens when user visits page for the first time
        return  (selected_btn === "btn_user") ? "user" :
                (selected_btn === "btn_usergroup") ? "usergroup" :
                (selected_btn === "btn_userpermit") ? "userpermit" : null;
    }

    function get_data_rows(tblName) {  //PR2021-08-01
        return (tblName === "userpermit") ? permit_rows :
                (tblName === "usergroup") ? user_rows :
                (tblName === "user") ? user_rows : null;
    }

    function get_tblName_from_mapid(map_id) {  //PR2021-08-01
        const arr = (map_id) ? map_id.split("_") : null;
        return (arr) ? arr[0] : null;
    };

    function get_tblName_pk_from_mapid(map_id) {  //PR2021-08-01
        const arr = (map_id) ? map_id.split("_") : null;
        let tblName = null, pk_int = null;
        if(arr && arr.length){
            tblName = arr[0];
            pk_int = (arr[1] && Number(arr[1])) ? Number(arr[1]) : null;
        };
        return [tblName, pk_int]
    };  // get_tblName_pk_from_mapid
})  // document.addEventListener('DOMContentLoaded', function()