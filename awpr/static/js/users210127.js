// PR2020-07-30 added
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
    let selected_btn = "btn_user_list";
    let selected_user_pk = null;
    let selected_period = {};
    let setting_dict = {};
    let permit_dict = {};

    let loc = {};  // locale_dict
    let mod_dict = {};
    let mod_MUA_dict = {};
    let mod_MGP_dict = {};
    let time_stamp = null; // used in mod add user

    let user_list = [];
    let school_rows = [];

    let examyear_map = new Map();
    let school_map = new Map();
    let department_map = new Map();

    let user_map = new Map();
    let permit_map = new Map();

    let filter_dict = {};
    let filter_mod_employee = false;

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    const url_datalist_download = get_attr_from_el(el_data, "data-datalist_download_url");
    const url_settings_upload = get_attr_from_el(el_data, "data-settings_upload_url");
    const url_user_upload = get_attr_from_el(el_data, "data-user_upload_url");
    const url_group_permit_upload = get_attr_from_el(el_data, "data-group_permit_upload_url");
    const url_download_permits = get_attr_from_el(el_data, "data-user_download_permits_url");

    // importdata_upload_url is stored in id_MIMP_data of modimport.html
    let columns_hidden = [];

// --- get field_settings
    const field_settings = {
        users: { field_caption: ["", "School", "User", "Name", "Email_address",  "Activated", "Last_loggedin", "Inactive"],
                    field_names: ["select", "sb_code", "username", "last_name", "email",  "activated", "last_login", "is_active"],
                    field_tags: ["div", "div", "div", "div", "div",  "div", "div", "div"],
                    filter_tags: ["select", "text","text",  "text", "text",  "triple", "text", "triple"],
                    field_width:  ["020", "075", "150",  "180", "240",  "100", "180", "090"],
                    field_align: ["c", "l", "l", "l",  "l",  "c", "l", "c"]},
        usergroups: {
                    field_caption: ["", "School", "User", "Read_only_2lines", "Edit",
                                    "President", "Secretary", "Commissioner_2lines",
                                    "Analyze",  "System_manager_2lines"],
                    field_names: ["select", "sb_code", "username", "group_read", "group_edit",
                                    "group_auth1", "group_auth2", "group_auth3", "group_anlz", "group_admin"],
                    field_tags: ["div", "div", "div", "div", "div",
                                    "div", "div", "div",
                                    "div", "div"],
                    filter_tags: ["select", "text", "text",  "triple", "triple",
                                    "triple", "triple", "triple",
                                     "triple", "triple"],
                    field_width:  ["020", "075", "150", "090", "090",
                                    "090", "090", "090",
                                    "090", "090"],
                    field_align: ["c", "l", "l", "c", "c",
                     "c", "c", "c",
                     "c", "c"]},
        grouppermits: {
                    field_caption: ["", "Organization", "Page", "Action", "Sequence_2lines", "Read_only_2lines", "Edit",
                                    "President", "Secretary", "Commissioner_2lines",
                                    "Analyze", "System_manager_2lines"],
                    field_names: ["select", "role", "page", "action", "sequence",
                                    "group_read", "group_edit", "group_auth1", "group_auth2", "group_auth3", "group_anlz", "group_admin"],
                    field_tags: ["div", "div", "div", "input", "input", "div", "div",
                                    "div", "div", "div", "div", "div"],
                    filter_tags: ["select", "text", "text", "text", "number", "triple", "triple",
                                    "triple", "triple", "triple", "triple", "triple"],
                    field_width:  ["020", "090", "120","150", "075", "075", "075",
                                    "090", "090", "090", "090", "090"],
                    field_align: ["c", "l", "l", "l", "c", "c", "c", "c", "c", "c", "c", "c"]}
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
                function() {t_MSSSS_Open(loc, "school", school_map, false, setting_dict, permit_dict, MSSSS_Response)}, false );
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
            el_MUA_btn_delete.addEventListener("click", function() {ModConfirmOpen("delete")}, false);
        }
        if (el_MUA_btn_submit){
            el_MUA_btn_submit.addEventListener("click", function() {MUA_Save("save")}, false);
        };

// ---  MODAL GROUP PERMISSION
        const el_MGP_btn_delete = document.getElementById("id_MGP_btn_delete");
        const el_MGP_btn_submit = document.getElementById("id_MGP_btn_submit");
        if (el_MGP_btn_delete){
            el_MGP_btn_delete.addEventListener("click", function() {MGP_Save("delete")}, false);
        }
        if (el_MGP_btn_submit){
            el_MGP_btn_submit.addEventListener("click", function() {MGP_Save("save")}, false);
        };

// ---  MODAL UPLOAD PERMITS
    // --- create EventListener for buttons in btn_container
        const el_MIMP_btn_container = document.getElementById("id_MIMP_btn_container");
        if(el_MIMP_btn_container){
            const btns = el_MIMP_btn_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                const data_btn = get_attr_from_el(btn,"data-btn")
                btn.addEventListener("click", function() {MIMP_btnSelectClicked(data_btn)}, false )
            }
        }
        const el_filedialog = document.getElementById("id_MIMP_filedialog");
        if (el_filedialog){el_filedialog.addEventListener("change", function() {MIMP_HandleFiledialog(el_filedialog, loc)}, false)};
        const el_worksheet_list = document.getElementById("id_MIMP_worksheetlist");
        if (el_worksheet_list){el_worksheet_list.addEventListener("change", function() {MIMP_SelectWorksheet()}, false)};
        const el_MIMP_checkboxhasheader = document.getElementById("id_MIMP_hasheader");
        if (el_MIMP_checkboxhasheader){el_MIMP_checkboxhasheader.addEventListener("change", function() {MIMP_CheckboxHasheaderChanged()}, false)};
        const el_MIMP_btn_prev = document.getElementById("id_MIMP_btn_prev");
        if (el_MIMP_btn_prev){el_MIMP_btn_prev.addEventListener("click", function() {MIMP_btnPrevNextClicked("prev")}, false)};
        const el_MIMP_btn_next = document.getElementById("id_MIMP_btn_next");
        if (el_MIMP_btn_next){el_MIMP_btn_next.addEventListener("click", function() {MIMP_btnPrevNextClicked("next")}, false)};
        const el_MIMP_btn_test = document.getElementById("id_MIMP_btn_test");
        if (el_MIMP_btn_test){el_MIMP_btn_test.addEventListener("click", function() {MIMP_Save("test")}, false)};
        const el_MUP_btn_upload = document.getElementById("id_MIMP_btn_upload");
        if (el_MUP_btn_upload){el_MUP_btn_upload.addEventListener("click", function() {MIMP_Save("save")}, false)};


// ---  MOD CONFIRM ------------------------------------
        let el_confirm_header = document.getElementById("id_confirm_header");
        let el_confirm_loader = document.getElementById("id_confirm_loader");
        let el_confirm_msg_container = document.getElementById("id_confirm_msg_container")
        let el_confirm_msg01 = document.getElementById("id_confirm_msg01")
        let el_confirm_msg02 = document.getElementById("id_confirm_msg02")
        let el_confirm_msg03 = document.getElementById("id_confirm_msg03")
        let el_confirm_btn_cancel = document.getElementById("id_confirm_btn_cancel");
        let el_confirm_btn_save = document.getElementById("id_confirm_btn_save");
        if (el_confirm_btn_save){el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()}, false)};

    if(may_view_page){
// ---  set selected menu button active
        SetMenubuttonActive(document.getElementById("id_hdr_users"));

        const datalist_request = {
                setting: {page: "page_user"},
                schoolsetting: {setting_key: "import_permits"},
                locale: {page: ["page_user", 'upload']},
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
            url: url_datalist_download,
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
                    mimp_loc = loc;
                    isloaded_loc = true;
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

                if ("user_rows" in response) { refresh_user_map(response.user_rows)};
                if ("permit_rows" in response) { refresh_permit_map(response.permit_rows) };

                if ("examyear_rows" in response) { b_fill_datamap(examyear_map, response.examyear_rows) };
                if ("school_rows" in response)  { b_fill_datamap(school_map, response.school_rows) };
                if ("department_rows" in response) { b_fill_datamap(department_map, response.department_rows) };

                HandleBtnSelect(selected_btn, true);  // true = skip_upload

            },
            error: function (xhr, msg) {
// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                console.log(msg + '\n' + xhr.responseText);
                alert(msg + '\n' + xhr.responseText);
            }
        });
    }  // function DatalistDownload

//=========  CreateSubmenu  ===  PR2020-07-31
    function CreateSubmenu() {
        console.log("===  CreateSubmenu == ");
        let el_submenu = document.getElementById("id_submenu")

        // hardcode access of system admin, to get access before action 'crud_user' is added to permits
        const permit_system_admin = (permit_dict.requsr_role_system && permit_dict.usergroup_list.includes("admin"));
        if (permit_dict.crud_user || permit_system_admin){
            AddSubmenuButton(el_submenu, loc.Add_user, function() {MUA_Open("addnew")});
            AddSubmenuButton(el_submenu, loc.Delete_user, function() {ModConfirmOpen("delete")});
        }
        // hardcode access of system admin
        if (permit_dict.crud_permit || permit_system_admin){
            AddSubmenuButton(el_submenu, loc.Add_permission, function() {MGP_Open("addnew")});
            //AddSubmenuButton(el_submenu, loc.Upload_permissions, function() {MUP_Open("addnew")});
            AddSubmenuButton(el_submenu, loc.Download_permissions, null, "id_submenu_download_perm", url_download_permits, false);  // true = download
            AddSubmenuButton(el_submenu, loc.Upload_permissions, function() {MIMP_Open("import_permits")}, "id_submenu_import");
        };
         el_submenu.classList.remove(cls_hide);
    };//function CreateSubmenu

//###########################################################################
// +++++++++++++++++ EVENT HANDLERS +++++++++++++++++++++++++++++++++++++++++
//=========  HandleBtnSelect  ================ PR2020-09-19
    function HandleBtnSelect(data_btn, skip_upload) {
        //console.log( "===== HandleBtnSelect ========= ");
        selected_btn = data_btn
        if(!selected_btn){selected_btn = "btn_user_list"}

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_user: {sel_btn: selected_btn}};
            UploadSettings (upload_dict, url_settings_upload);
        };

// ---  highlight selected button
        highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  show only the elements that are used in this tab
        //show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

// ---  fill datatable
        FillTblRows();

    }  // HandleBtnSelect

//=========  HandleTableRowClicked  ================ PR2020-08-03
    function HandleTableRowClicked(tr_clicked) {
        //console.log("=== HandleTableRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

        selected_user_pk = null;

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        DeselectHighlightedRows(tr_clicked, cls_selected);
        tr_clicked.classList.add(cls_selected)

// ---  update selected_user_pk
        // only select employee from select table
        const row_id = tr_clicked.id

        //console.log( "row_id: ", row_id, typeof row_id);
        if(row_id){
            const map_dict = get_mapdict_from_datamap_by_id(user_map, row_id)
            selected_user_pk = map_dict.id;
        }
        //console.log( "selected_user_pk: ", selected_user_pk, typeof selected_user_pk);
    }  // HandleTableRowClicked

//========= FillTblRows  ====================================
    function FillTblRows() {
        //console.log( "===== FillTblRows  === ");
        const tblName = get_tblName_from_selectedBtn();
        const field_setting = field_settings[tblName];
        const data_map = get_data_map();

// --- reset table
        tblBody_datatable.innerText = null

// --- create table header and filter row
        CreateTblHeader(field_setting);

        if(data_map){
// --- loop through data_map
          for (const [map_id, map_dict] of data_map.entries()) {
            //console.log( "map_dict ", map_dict);
          // --- insert row at row_index
                const schoolcode_lc_trail = ( (map_dict.sb_code) ? map_dict.sb_code.toLowerCase() : "" ) + " ".repeat(8) ;
                const schoolcode_sliced = schoolcode_lc_trail.slice(0, 8);
                const order_by = schoolcode_sliced +  ( (map_dict.username) ? map_dict.username.toLowerCase() : "");
                const row_index = -1; // t_get_rowindex_by_sortby(tblBody_datatable, order_by)
                let tblRow = CreateTblRow(tblBody_datatable, tblName, field_setting, map_id, map_dict, row_index)

          // --- filter tblRow
                //const show_row = t_ShowTableRowExtended(filter_dict, tblRow);
                //add_or_remove_class(tblRow, cls_hide, !show_row);
          };
        }  // if(!!data_map)

    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-07-31 PR2021-03-23
    function CreateTblHeader(field_setting) {
        //console.log("===  CreateTblHeader ===== ");

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

// +++  create header and filter row ++++++++++++++++++++++++++++++++
        let tblRow_header = tblHead_datatable.insertRow (-1);
        let tblRow_filter = tblHead_datatable.insertRow (-1);
            tblRow_filter.setAttribute("data-filterrow", "1")

// - insert th's into header row
        const column_count = field_setting.field_names.length;
        for (let j = 0; j < column_count; j++) {
            const field_name = field_setting.field_names[j];

// skip columns if in columns_hidden
            if (!columns_hidden.includes(field_name)){
                const field_caption = loc[field_setting.field_caption[j]]
                const field_tag = field_setting.field_tags[j];
                const filter_tag = field_setting.filter_tags[j];
                const class_width = "tw_" + field_setting.field_width[j] ;
                const class_align = "ta_" + field_setting.field_align[j];

    // ++++++++++ create header row +++++++++++++++
        // --- add th to tblRow.
                let th_header = document.createElement("th");
        // --- add div to th, margin not working with th
                    const el_header = document.createElement("div");
                        el_header.innerText = (field_caption) ? field_caption : null;
        // --- add width, text_align
                        el_header.classList.add(class_width, class_align);
                    th_header.appendChild(el_header)
                tblRow_header.appendChild(th_header);

    // ++++++++++ create filter row +++++++++++++++
        // --- add th to tblRow_filter.
                const th_filter = document.createElement("th");
        // --- create element with tag from field_tags
                const filter_field_tag = (["text", "number"].includes(filter_tag)) ? "input" : "div";
                const el_filter = document.createElement(filter_field_tag);
        // --- add data-field Attribute.
                    el_filter.setAttribute("data-field", field_name);
                    el_filter.setAttribute("data-filtertag", filter_tag);
                    el_filter.setAttribute("data-colindex", j);
        // --- add EventListener to th_filter, not el_filter
                    if (["text", "number"].includes(filter_tag)) {
                        el_filter.addEventListener("keyup", function(event){HandleFilterKeyup(el_filter, event)});
                        add_hover(th_filter);
                    } else if (filter_tag === "triple") {
                        // add EventListener for icon to th_filter, not el_filter
                        th_filter.addEventListener("click", function(event){HandleFilterToggle(el_filter)});
                        th_filter.classList.add("pointer_show");
                        add_hover(th_filter);
                    }
        // --- add other attributes
                    if (filter_tag === "text") {
                        el_filter.setAttribute("type", "text")
                        el_filter.classList.add("input_text");

                        el_filter.setAttribute("autocomplete", "off");
                        el_filter.setAttribute("ondragstart", "return false;");
                        el_filter.setAttribute("ondrop", "return false;");

                    } else if (["toggle", "triple", "activated"].includes(filter_tag)) {
                        // default empty icon necessary to set pointer_show
                        el_filter.classList.add("tickmark_0_0");
                    }

    // --- add width, text_align
                    el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");
                th_filter.appendChild(el_filter)
                tblRow_filter.appendChild(th_filter);
            }  // if (!columns_hidden.includes(field_name))
        }  // for (let j = 0; j < column_count; j++)
    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09
    function CreateTblRow(tblBody, tblName, field_setting, map_id, map_dict, row_index) {
        //console.log("=========  CreateTblRow =========", tblName);
        //console.log("map_dict", map_dict);
        let tblRow = null;

        const tblName_settings = get_tblName_from_selectedBtn();
        if(field_setting){
            const field_names = field_setting.field_names;
            const field_tags = field_setting.field_tags;
            const field_align = field_setting.field_align;
            const field_width = field_setting.field_width;
            const column_count = field_names.length;

// --- insert tblRow into tblBody at row_index
            tblRow = tblBody.insertRow(row_index);
            tblRow.id = map_id

// --- add data attributes to tblRow
            tblRow.setAttribute("data-pk", map_dict.id);
            tblRow.setAttribute("data-ppk", map_dict.company_id);
            tblRow.setAttribute("data-table", tblName);
            tblRow.setAttribute("data-sortby", map_dict.username);

// --- add EventListener to tblRow
            tblRow.addEventListener("click", function() {HandleTableRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
            for (let j = 0; j < column_count; j++) {
                const field_name = field_names[j];

// skip columns if in columns_hidden
                if (!columns_hidden.includes(field_name)){
                    const field_tag = field_tags[j];
                    const class_width = "tw_" + field_width[j];
                    const class_align = "ta_" + field_align[j];

            // --- insert td element,
                    let td = tblRow.insertCell(-1);

            // --- create element with tag from field_tags
                    let el = document.createElement(field_tag);

            // --- add data-field attribute
                        el.setAttribute("data-field", field_name);

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
                        if (field_name === "select") {
                            // TODO add select multiple users option PR2020-08-18
                        } else if (["sb_code", "username", "last_name", "email", "employee_code"].includes(field_name)){
                            el.addEventListener("click", function() {MUA_Open("update", el)}, false)
                            el.classList.add("pointer_show");
                            add_hover(el);
                        } else if (["role", "page"].includes(field_name)){
                            el.addEventListener("click", function() {MGP_Open("update", el)}, false)
                            el.classList.add("pointer_show");
                            add_hover(el);
                        } else if (["role", "page", "action", "sequence"].includes(field_name)){
                            el.addEventListener("change", function(){HandleInputChange(el)});

                        } else if (field_name.slice(0, 5) === "group") {
                            // attach eventlisterener and hover to td, not to el. No need to add icon_class here
                            td.addEventListener("click", function() {UploadToggle(el)}, false)
                            add_hover(td);
                        } else if ( field_name === "activated") {
                            el.addEventListener("click", function() {ModConfirmOpen("resend_activation_email", el)}, false )
                        } else if (field_name === "is_active") {
                            el.addEventListener("click", function() {ModConfirmOpen("is_active", el)}, false )
                            el.classList.add("inactive_0_2")
                            add_hover(el);
                        } else if ( field_name === "last_login") {
                            // pass
                        }

            // --- add width, text_align
                        td.classList.add(class_width, class_align);
                        if (field_tag === "input") {
                            // dont set width in input field , to adjust width to length
                            el.classList.add(class_align);
                        } else {
                            el.classList.add(class_width, class_align);
                        }
            // --- append element
                    td.appendChild(el);
    // --- put value in field
                    UpdateField(el, map_dict)

                }  // if (!columns_hidden.includes(field_name))
            }  // for (let j = 0; j < 8; j++)
        }  // if(field_settings_table)
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

//=========  UpdateField  ================ PR2020-08-16 PR2021-03-23
    function UpdateField(el_div, map_dict) {
        //console.log("=========  UpdateField =========");

        const field_name = get_attr_from_el(el_div, "data-field");
        if(el_div && field_name){
            let inner_text = null, title_text = null, filter_value = null;
            if (field_name === "select") {
                // TODO add select multiple users option PR2020-08-18
            } else if (["sb_code", "username", "last_name", "email", "employee_code", "page", ].includes(field_name)){
                inner_text = map_dict[field_name];
                filter_value = inner_text;
            } else if (field_name === "role") {
                const role = map_dict[field_name];
                inner_text = (loc.role_caption && loc.role_caption[role])  ? loc.role_caption[role] : role;
                filter_value = inner_text;
            } else if (["action", "sequence"].includes(field_name)){
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

// ---  add EventListener
                if(!is_activated){
                    el_div.addEventListener("click", function() {ModConfirmOpen("resend_activation_email", el_div)}, false )
                }
// ---  add title
                title_text = (is_expired) ? loc.Activationlink_expired + "\n" + loc.Resend_activationlink : null
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
        console.log( " ==== UploadToggle ====");
        console.log( "el_input", el_input);
        console.log( "permit_dict", permit_dict);

        mod_dict = {};

        if(permit_dict.crud_user){
            const tblRow = get_tablerow_selected(el_input);
            if(tblRow){
                const tblName = get_attr_from_el(tblRow, "data-table")
                const map_id = tblRow.id
                const data_map = get_data_map();
                const map_dict = get_mapdict_from_datamap_by_id(data_map, map_id);
    console.log( "tblName", tblName);
    console.log( "map_dict", map_dict);

                if(!isEmpty(map_dict)){
                    const fldName = get_attr_from_el(el_input, "data-field");
                    let permit_bool = (get_attr_from_el(el_input, "data-filter") === "1");

    // show message when sysadmin tries to delete sysadmin permit
                    const is_request_user = (permit_dict.requsr_pk && permit_dict.requsr_pk === map_dict.id);
                    if(fldName === "group_admin" && is_request_user && permit_bool ){
                        ModConfirmOpen("permission_admin", el_input)
                    } else {

            // ---  toggle permission el_input
                        permit_bool = (!permit_bool);
    console.log( "new permit_bool", permit_bool);
            // ---  put new permission in el_input
                        el_input.setAttribute("data-filter", (permit_bool) ? "1" : "0")
           // ---  change icon, before uploading
                        el_input.className = (permit_bool) ? "tickmark_1_2" : "tickmark_0_0";

           //console.log( "fldName", fldName);
                        const url_str = (tblName === "grouppermits") ? url_group_permit_upload : url_user_upload;
                        const upload_dict = {mode: "update", mapid: map_id};
                        if (tblName === "grouppermits"){
                            upload_dict.permit_pk = map_dict.id;
                        } else if (tblName === "usergroups"){
                            upload_dict.user_pk = map_dict.id,
                            upload_dict.schoolbase_pk = map_dict.schoolbase_id;
                        }
                        const usergroupname = fldName.substr(6);
                        upload_dict.usergroups = {}
                        upload_dict.usergroups[usergroupname] = permit_bool;
                        UploadChanges(upload_dict, url_str);
                    }  // if(fldName === "group_admin" && is_request_user && permit_bool ){
                }  //  if(!isEmpty(map_dict)){
            }  //   if(!!tblRow)
        }  // if(permit_dict.requsr_group_system)
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
                    const mode = get_dict_value(response, ["mode"]);
                    if(["delete", 'resend_activation_email'].includes(mode)) {
                        ModConfirmResponse(response);
                    } else {
                        if ("updated_userlist" in response) {
                            refresh_user_map(response.updated_userlist);
                        };
                        if ("updated_permit_rows" in response){
                            refresh_permit_map(response.updated_permit_rows);
                        }
                    }
                },  // success: function (response) {
                error: function (xhr, msg) {
                    // ---  hide loader
                    el_loader.classList.add(cls_visible_hide)
                    console.log(msg + '\n' + xhr.responseText);
                    alert(msg + '\n' + xhr.responseText);
                }  // error: function (xhr, msg) {
            });  // $.ajax({
        }  //  if(!!row_upload)
    };  // UploadChanges

// +++++++++++++++++ UPDATE +++++++++++++++++++++++++++++++++++++++++++

// +++++++++ MOD ADD USER ++++++++++++++++ PR2020-09-18
    function MUA_Open(mode, el_input){
        console.log(" -----  MUA_Open   ---- mode: ", mode)  // modes are: addnew, update
        console.log("permit_dict: ", permit_dict)
        console.log("permit_dict.crud_user_otherschool: ", permit_dict.crud_user_otherschool)
        // mode = 'addnew' when called by SubmenuButton
        // mode = 'update' when called by tblRow event

        if(permit_dict.crud_user){
            let user_dict = {}, user_pk = null;
            let user_schoolbase_pk = null, user_schoolbase_code = null, user_mapid = null;
            const fldName = get_attr_from_el(el_input, "data-field");
            const is_addnew = (mode === "addnew");

            if(el_input){
                const tblRow = get_tablerow_selected(el_input);
                user_mapid = tblRow.id;
                user_dict = get_mapdict_from_datamap_by_id(user_map, user_mapid);
            //console.log("user_mapid", user_mapid)
            console.log("user_dict", user_dict)
                if(!isEmpty(user_dict)){
                    user_pk = user_dict.id;
                    user_schoolbase_pk = user_dict.schoolbase_id;
                    user_schoolbase_code = user_dict.sb_code;
                }
        // when el_input is not defined: function is mode 'addnew'
            } else if (!permit_dict.crud_user_otherschool){
                // when new user and not role_admin or role_system: : get user_schoolbase_pk from request_user
                user_schoolbase_pk = permit_dict.requsr_schoolbase_pk;
                user_schoolbase_code = permit_dict.requsr_schoolbase_code;
            }

            selected_user_pk = user_pk

            let user_schoolname = null;
            if(user_schoolbase_pk){
                user_schoolname = user_schoolbase_code
                // TODO cahnge to school_map
                for(let i = 0, tblRow, dict; dict = school_rows[i]; i++){
                    if (!isEmpty(dict)) {
                        if(user_schoolbase_pk === dict.base_id ) {
                            if (dict.abbrev) {user_schoolname += " - " + dict.abbrev};
                            break;
            }
            }
            }
            };

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
                username: get_dict_value(user_dict, ["username"]),
                last_name: get_dict_value(user_dict, ["last_name"]),
                email: get_dict_value(user_dict, ["email"])
                };
            console.log("mod_MUA_dict: ", mod_MUA_dict)

    // ---  show only the elements that are used in this tab
            const container_element = document.getElementById("id_mod_user");
            let tab_str = (is_addnew) ? (permit_dict.crud_user_otherschool) ? "tab_addnew_may_select_school" : "tab_addnew_noschool" : "tab_update";
            show_hide_selected_elements_byClass("tab_show", tab_str, container_element)

    // ---  set header text
            const header_text = (is_addnew) ? loc.Add_user : loc.User + ":  " + mod_MUA_dict.username;
            const el_MUA_header = document.getElementById("id_MUA_header");
            el_MUA_header.innerText = header_text;

    // ---  fill selecttable
            if(permit_dict.crud_user_otherschool){
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
            const el_focus = (is_addnew && permit_dict.crud_user_otherschool) ? el_MUA_schoolname :
                             ( (is_addnew && !permit_dict.crud_user_otherschool) || (fldName === "username") ) ? el_MUA_username :
                             (fldName === "last_name") ? el_MUA_last_name :
                             (fldName === "email") ? el_MUA_email : null;
            if(el_focus){setTimeout(function (){el_focus.focus()}, 50)};

    // ---  set text and hide info footer
            //el_MUA_footer01.innerText = loc.Click_to_register_new_user;
            //el_MUA_footer02.innerText = loc.We_will_send_an_email_to_the_new_user;
            el_MUA_footer_container.classList.add(cls_hide);

    // ---  hide loader
            el_MUA_loader.classList.add(cls_hide);

    // ---  hide btn delete when addnew mode
            add_or_remove_class(el_MUA_btn_delete, cls_hide, is_addnew)

    // ---  disable btn submit
            const disable_btn_save = (!el_MUA_username.value || !el_MUA_last_name.value || !el_MUA_email.value )
            el_MUA_btn_submit.disabled = disable_btn_save;
            el_MUA_btn_submit.innerText = (mode === "update") ? loc.Save : loc.Submit;

    // ---  show modal
            $("#id_mod_user").modal({backdrop: true});

        }  //  if(permit_dict.crud_user)
    };  // MUA_Open

//========= MUA_Save  ============= PR2020-08-02 PR2020-08-15
   function MUA_Save(args) {
        console.log("=== MUA_Save === ");
        //console.log("args: ", args);
        //console.log("time_stamp:     ", time_stamp);

        //  args = 'save'     when called by el_MUA_btn_submit
        //  args = time_stamp when called by MUA_InputKeyup

        let mode = null, skip = false;

        // send schoolbase, username and email to server after 1500 ms
        // abort if within that period a new value is entered.
        // checked by comparing the timestamp
        // 'args' is either 'save' or a time_stamp number
        // time_stamp gets new value 'now' whenever a 'keyup' event occurs
        // MUA_Save has a time-out of 1500 ms
        // init_time_stamp is the value of time_stamp at the time this 'keyup' event occurred
        // when time_stamp = init_time_stamp, it means that there are no new keyup events within the time-out period

        if(Number(args)){
// ---  skip if a new key is entered in the elapsed period of 1500 ms
            const init_time_stamp = Number(args)
            skip = (time_stamp !== init_time_stamp)
        } else {
            mode = args; // 'value can only be 'save'
        }
        if(!skip) {
// ---  skip if one of the fields is blank
            skip = !(el_MUA_username.value && el_MUA_last_name.value && el_MUA_email.value)
        }
        //console.log("skip: ", skip);
        if(!skip){
            // mod_MUA_dict. modes are: 'addnew', 'update'

            // in ModConfirmSave upload_dict.mode can get value "delete" or "resend_activation_email"
            // in this function value of 'mode' is only 'save'
            const upload_mode =  (mod_MUA_dict.mode === "addnew") ? "create" : "update";

                                // (mode === "validate") ? "validate" :
                                //(mode === "resend_activation_email" ) ? "resend_activation_email" :
                               // (mod_MUA_dict.mode === "update") ? "update" :
                               // (mod_MUA_dict.mode === "addnew") ? "create" : null;

            console.log("mod_MUA_dict", mod_MUA_dict);
            console.log("mode", mode);
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
                upload_dict = { schoolbase_pk: mod_MUA_dict.user_schoolbase_pk,
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
                url: url_user_upload,
                data: parameters,
                dataType:'json',
                success: function (response) {
                    console.log( "response");
                    console.log( response);

                    // hide loader
                    el_MUA_loader.classList.add(cls_hide);

                    MUA_SetMsgElements(response);

                    if ("updated_userlist" in response){
                        refresh_user_map(response.updated_userlist);
                    }

                },  // success: function (response) {
                error: function (xhr, msg) {
                    console.log(msg + '\n' + xhr.responseText);
                    alert(msg + '\n' + xhr.responseText);
                }  // error: function (xhr, msg) {
            });  // $.ajax({
        }
    };  // MUA_Save

//========= MUA_FillSelectTableSchool  ============= PR2020--09-17
    function MUA_FillSelectTableSchool() {
        console.log("===== MUA_FillSelectTableSchool ===== ");

        const data_map = school_map;
        const tblBody_select = document.getElementById("id_MUA_tbody_select");
        tblBody_select.innerText = null;

// ---  loop through dictlist
        //[ {pk: 2608, code: "Colpa de, William"} ]
        let row_count = 0

        if(data_map){
            for (const [map_id, map_dict] of data_map.entries()) {
                if (!isEmpty(map_dict)) {
                    const defaultrole = (map_dict.defaultrole) ? map_dict.defaultrole : 0;
    // only add schools to list whith sme or lower role
                    if (defaultrole <= permit_dict.requsr_role){
        // ---  get info from map_dict
                        const base_id = map_dict.base_id;
                        const country_id = map_dict.country_id;
                        const code = (map_dict.sb_code) ? map_dict.sb_code : "";
                        const abbrev = (map_dict.abbrev) ? map_dict.abbrev : "";

                        const tblRow = tblBody_select.insertRow(-1);
                        row_count += 1;

                        tblRow.id = map_id;
                        tblRow.setAttribute("data-pk", base_id);
                        tblRow.setAttribute("data-ppk", country_id);
                        tblRow.setAttribute("data-value", code + " - " + abbrev);

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
            }  // for (const [map_id, map_dict] of data_map.entries())
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
    }  // MUA_ResetElements

//========= MUA_SetMsgElements  ============= PR2020-08-02
    function MUA_SetMsgElements(response){
        //console.log( "===== MUA_SetMsgElements  ========= ");

        const err_dict = ("msg_err" in response) ? response.msg_err : {}
        const validation_ok = get_dict_value(response, ["validation_ok"], false);
    //console.log( "err_dict", err_dict);

        const el_msg_container = document.getElementById("id_msg_container")
        let err_save = false;
        let is_ok = ("msg_ok" in response);
        if (is_ok) {
            const ok_dict = response["msg_ok"];
    //console.log( "ok_dict", ok_dict);
            document.getElementById("id_msg_01").innerText = get_dict_value(ok_dict, ["msg01"]);
            document.getElementById("id_msg_02").innerText = get_dict_value(ok_dict, ["msg02"]);
            document.getElementById("id_msg_03").innerText = get_dict_value(ok_dict, ["msg03"]);
            document.getElementById("id_msg_04").innerText = get_dict_value(ok_dict, ["msg04"]);

            el_msg_container.classList.remove("border_bg_invalid");
            el_msg_container.classList.add("border_bg_valid");
// ---  show only the elements that are used in this tab
            show_hide_selected_elements_byClass("tab_show", "tab_ok");

        } else {
            // --- loop through input elements
            if("save" in err_dict){
                err_save = true;
                document.getElementById("id_msg_01").innerText = get_dict_value(err_dict, ["save"]);
                document.getElementById("id_msg_02").innerText = null;
                document.getElementById("id_msg_03").innerText =  null;
                document.getElementById("id_msg_04").innerText =  null;

                el_msg_container.classList.remove("border_bg_valid");
                el_msg_container.classList.add("border_bg_invalid");
// ---  show only the elements that are used in this tab
                show_hide_selected_elements_byClass("tab_show", "tab_ok");

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

// ---  hide submit btn when is_ok
        add_or_remove_class(el_MUA_btn_submit, cls_hide, is_ok)

// ---  set text on btn cancel
        const el_MUA_btn_cancel = document.getElementById("id_MUA_btn_cancel");
        el_MUA_btn_cancel.innerText = ((is_ok || err_save) ? loc.Close : loc.Cancel);
        if(is_ok || err_save){el_MUA_btn_cancel.focus()}

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
        console.log( "===== MUA_InputKeyup  ========= ");
        console.log( "event_key", event_key);

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
            console.log( "fldName", fldName);
            console.log( "field_value", field_value);
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
                time_stamp = Number(Date.now())
                setTimeout(MUA_Save, 1500, time_stamp);  // time_stamp is an argument passed to the function MUA_Save.
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
    function MGP_Open(mode, el_input){
        console.log(" -----  MGP_Open   ---- mode: ", mode)  // modes are: addnew, update
        // mode = 'addnew' when called by SubmenuButton
        // mode = 'update' when called by tblRow event

        const is_addnew = (mode === "addnew");
        mod_MGP_dict = {is_addnew: (is_addnew) ? "create" : "update" };
        mod_MGP_dict = {mode: mode};

        let permit_pk = null, permit_role = null, permit_page = null, permit_action = null, permit_sequence = null;
        if(el_input){
            const tblRow = get_tablerow_selected(el_input);
            const map_dict = get_mapdict_from_datamap_by_id(permit_map, tblRow.id);
        //console.log("user_mapid", user_mapid)
        console.log("map_dict", map_dict)
            if(!isEmpty(map_dict)){
                permit_pk = map_dict.id;
                permit_role = map_dict.role;
                permit_page = map_dict.page;
                permit_action = map_dict.action;
                permit_sequence = map_dict.sequence;
            }
        }
        mod_MGP_dict.permit_pk = permit_pk;
        document.getElementById("id_MGP_role").value = permit_role;
        document.getElementById("id_MGP_page").value = permit_page;
        document.getElementById("id_MGP_action").value = permit_action;
        document.getElementById("id_MGP_sequence").value = permit_sequence;

    // ---  show modal
        $("#id_mod_group_permit").modal({backdrop: true});
    };  // MGP_Open

    function MGP_Save(mode){ //PR2021-03-20
        console.log("=== MGP_Save === ");
        //  mode = 'save', 'delete'
        const upload_mode = (mode === "delete") ? "delete" :
                            (mod_MGP_dict.mode === "addnew") ? "create" : "update";

        const permit_role = document.getElementById("id_MGP_role").value;
        const permit_page = document.getElementById("id_MGP_page").value;
        const permit_action = document.getElementById("id_MGP_action").value;
        const sequence_value = document.getElementById("id_MGP_sequence").value;
        const permit_sequence_int = (Number(sequence_value)) ? Number(sequence_value) : 1;
// ---  create mod_dict
        const url_str = url_group_permit_upload;
        const upload_dict = {mode: upload_mode,
                            permit_pk: mod_MGP_dict.permit_pk,
                            role: permit_role,
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
                alert(msg + '\n' + xhr.responseText);
            }  // error: function (xhr, msg) {
        });  // $.ajax({

        $("#id_mod_group_permit").modal("hide");
    }  // MGP_Save

//========= HandleInputChange  ===============PR2021-03-20
    function HandleInputChange(el_input){
        console.log(" --- HandleInputChange ---")

        const tblRow = get_tablerow_selected(el_input)
        const map_id = tblRow.id
        if (map_id){
            const map_dict = get_mapdict_from_datamap_by_id(permit_map, map_id)
        console.log("map_dict", map_dict)
            const fldName = get_attr_from_el(el_input, "data-field")
            const permit_pk = map_dict.id;
            const map_value = map_dict[fldName];
            let new_value = el_input.value;
            if(fldName === "sequence"){
                 new_value = (Number(new_value)) ? Number(new_value) : 1;
            }

            if(new_value !== map_value){
        // ---  create mod_dict
                const url_str = url_group_permit_upload;
                const upload_dict = {mode: "update",
                                    permit_pk: permit_pk};
                upload_dict[fldName] = new_value;
                console.log("upload_dict: ", upload_dict);

        // ---  upload changes
                UploadChanges(upload_dict, url_str);
            }
        }
    };  // HandleInputChange

// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2020-08-03
    function ModConfirmOpen(mode, el_input) {
        console.log(" -----  ModConfirmOpen   ----")
        // values of mode are : "delete", "is_active" or "resend_activation_email", "permission_admin"

// ---  get selected_pk
        let selected_pk = null;
        // tblRow is undefined when clicked on delete btn in submenu btn or form (no inactive btn)
        const tblRow = get_tablerow_selected(el_input);
        if(tblRow){
            selected_pk = get_attr_from_el(tblRow, "data-pk")
        } else {
            selected_pk = selected_user_pk
        }
        //console.log("selected_pk", selected_pk )

// ---  get info from user_map
        const map_id = "user_" + selected_pk;
        const map_dict = get_mapdict_from_datamap_by_id(user_map, map_id)
        const is_request_user = (permit_dict.requsr_pk && permit_dict.requsr_pk === map_dict.id)

        //console.log("map_dict", map_dict)
// ---  create mod_dict
        mod_dict = {mode: mode};
        const has_selected_item = (!isEmpty(map_dict));
        if(has_selected_item){
            mod_dict.user_pk = map_dict.id;
            mod_dict.user_ppk = map_dict.schoolbase_id;
            mod_dict.mapid = map_id;
        };
        if (mode === "is_active") {
              mod_dict.current_isactive = map_dict.is_active;
        }

// ---  put text in modal form
        let dont_show_modal = false;
        const is_mode_permission_admin = (mode === "permission_admin");
        const is_mode_resend_activation_email = (mode === "resend_activation_email");
        //console.log("mode", mode)
        const inactive_txt = (mod_dict.current_isactive) ? loc.Make_user_inactive : loc.Make_user_active;
        const header_text = (mode === "delete") ? loc.Delete_user :
                            (mode === "is_active") ? inactive_txt :
                            (is_mode_resend_activation_email) ? loc.Resend_activation_email :
                            (is_mode_permission_admin) ? loc.Set_permissions : "";
        let msg_01_txt = null, msg_02_txt = null, msg_03_txt = null;
        let hide_save_btn = false;
        if(!has_selected_item){
            msg_01_txt = loc.No_user_selected;
            hide_save_btn = true;
        } else {
            const username = (map_dict.username) ? map_dict.username  : "-";
            if(mode === "delete"){
                if(is_request_user){
                    msg_01_txt = loc.Sysadm_cannot_delete_own_account;
                    hide_save_btn = true;
                } else {
                    msg_01_txt = loc.User + " '" + username + "'" + loc.will_be_deleted
                    msg_02_txt = loc.Do_you_want_to_continue;
                }
            } else if(mode === "is_active"){
                if(is_request_user && mod_dict.current_isactive){
                    msg_01_txt = loc.Sysadm_cannot_set_inactive;
                    hide_save_btn = true;
                } else {
                    const inactive_txt = (mod_dict.current_isactive) ? loc.will_be_made_inactive : loc.will_be_made_active
                    msg_01_txt = loc.User + " '" + username + "'" + inactive_txt
                    msg_02_txt = loc.Do_you_want_to_continue;
                }
            } else if(is_mode_permission_admin){
                hide_save_btn = true;
                const fldName = get_attr_from_el(el_input, "data-field")
                if (fldName === "group_admin") {
                    msg_01_txt = loc.Sysadm_cannot_remove_sysadm_perm
                }
            } else if (is_mode_resend_activation_email) {
                const is_expired = activationlink_is_expired(map_dict.date_joined);
                dont_show_modal = (map_dict.activated);
                if(!dont_show_modal){
                    if(is_expired) {
                        msg_01_txt = loc.Activationlink_expired
                        msg_02_txt = loc.We_will_resend_an_email_to_user + " '" + username + "'."
                        msg_03_txt = loc.Do_you_want_to_continue;
                    } else {
                        msg_01_txt = loc.We_will_resend_an_email_to_user + " '" + username + "'."
                        msg_02_txt = loc.Do_you_want_to_continue;
                    }
                }
            }
        }
        if(!dont_show_modal){
            el_confirm_header.innerText = header_text;
            el_confirm_loader.classList.add(cls_visible_hide)
            el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");
            el_confirm_msg01.innerText = msg_01_txt;
            el_confirm_msg02.innerText = msg_02_txt;
            el_confirm_msg03.innerText = msg_03_txt;

            const caption_save = (mode === "delete") ? loc.Yes_delete :
                            (mode === "is_active") ? ( (mod_dict.current_isactive) ? loc.Yes_make_inactive : loc.Yes_make_active ) :
                            (is_mode_resend_activation_email) ? loc.Yes_send_email : loc.OK;
            el_confirm_btn_save.innerText = caption_save;
            add_or_remove_class (el_confirm_btn_save, cls_hide, hide_save_btn);

            add_or_remove_class (el_confirm_btn_save, "btn-primary", (mode !== "delete"));
            add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", (mode === "delete"));

            const caption_cancel = (mode === "delete") ? loc.No_cancel :
                            (mode === "is_active") ? loc.No_cancel :
                            (is_mode_resend_activation_email) ? loc.No_cancel : loc.Cancel;
            el_confirm_btn_cancel.innerText = (has_selected_item && !is_mode_permission_admin) ? caption_cancel : loc.Close;

    // set focus to cancel button
            setTimeout(function (){
                el_confirm_btn_cancel.focus();
            }, 500);
// show modal
            $("#id_mod_confirm").modal({backdrop: true});
        }

    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2019-06-23
    function ModConfirmSave() {
        //console.log(" --- ModConfirmSave --- ");
        //console.log("mod_dict: ", mod_dict);
        let close_modal = false;
        let tblRow = document.getElementById(mod_dict.mapid);

// ---  when delete: make tblRow red, before uploading
        if (tblRow && mod_dict.mode === "delete"){
            ShowClassWithTimeout(tblRow, "tsa_tr_error");
        }

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
        let upload_dict = { user_pk: mod_dict.user_pk,
                             schoolbase_pk: mod_dict.user_ppk,
                             mode: mod_dict.mode,
                             mapid: mod_dict.mapid};
        if (mod_dict.mode === "is_active") {
            upload_dict.is_active = {value: mod_dict.new_isactive, update: true}
        };

        //console.log("upload_dict: ", upload_dict);
        UploadChanges(upload_dict, url_user_upload);

// ---  hide modal
        if(close_modal) {
            $("#id_mod_confirm").modal("hide");
        }
    }  // ModConfirmSave

//=========  ModConfirmResponse  ================ PR2019-06-23
    function ModConfirmResponse(response) {
        //console.log(" --- ModConfirmResponse --- ");
        //console.log("mod_dict: ", mod_dict);
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
            let msg01_text = null, msg02_text = null, msg03_text = null;
            if ("msg_err" in response) {
                msg01_text = get_dict_value(response, ["msg_err", "msg01"], "");
                if (mod_dict.mode === "resend_activation_email") {
                    msg02_text = loc.Activation_email_not_sent;
                }
                el_confirm_msg_container.classList.add("border_bg_invalid");
            } else if ("msg_ok" in response){
                msg01_text  = get_dict_value(response, ["msg_ok", "msg01"]);
                msg02_text = get_dict_value(response, ["msg_ok", "msg02"]);
                msg03_text = get_dict_value(response, ["msg_ok", "msg03"]);
                el_confirm_msg_container.classList.add("border_bg_valid");
            }
            el_confirm_msg01.innerText = msg01_text;
            el_confirm_msg02.innerText = msg02_text;
            el_confirm_msg03.innerText = msg03_text;
            el_confirm_btn_cancel.innerText = loc.Close
            el_confirm_btn_save.classList.add(cls_hide);
        } else {
        // hide mod_confirm when no message
            $("#id_mod_confirm").modal("hide");
        }
    }  // ModConfirmResponse

//###########################################################################

// +++++++++++++++++ REFRESH PERMIT MAP ++++++++++++++++++++++++++++++++++++++++++++++++++
//=========  refresh_permit_map  ================ PR2021-03-18
    function refresh_permit_map(updated_permitlist) {
        //console.log(" --- refresh_permit_map  ---");
        //console.log( "updated_permitlist", updated_permitlist);
        if (updated_permitlist) {
            for (let i = 0, update_dict; update_dict = updated_permitlist[i]; i++) {
                refresh_usermap_item(permit_map, update_dict);
            }
        }
    }  //  refresh_permit_map

// +++++++++++++++++ REFRESH USER MAP ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  refresh_user_map  ================ PR2020-08-16
    function refresh_user_map(updated_userlist) {
        //console.log(" --- refresh_user_map  ---");
        if (updated_userlist) {
            for (let i = 0, update_dict; update_dict = updated_userlist[i]; i++) {
                refresh_usermap_item(user_map, update_dict);
            }
        }
    }  //  refresh_user_map

//=========  refresh_usermap_item  ================ PR2020-08-16 PR2021-03-24
    function refresh_usermap_item(data_map, update_dict) {
        //console.log(" --- refresh_usermap_item  ---");
        //console.log("update_dict", update_dict);

        if(!isEmpty(update_dict)){
// ---  update or add update_dict in user_map
            let updated_columns = [];
    // get existing map_item
            const tblName = update_dict.table;
            const map_id = update_dict.mapid;
            let tblRow = document.getElementById(map_id);

            const is_deleted = get_dict_value(update_dict, ["deleted"], false);
            const is_created = get_dict_value(update_dict, ["created"], false);

            const tblName_settings = get_tblName_from_selectedBtn();
            const field_setting = field_settings[tblName_settings];
            const field_names = field_setting.field_names;

        //console.log("tblRow", tblRow);
        //console.log("is_deleted", is_deleted);
        //console.log("is_created", is_created);
// ++++ created ++++
            if(is_created){
    // ---  insert new item
                data_map.set(map_id, update_dict);
                updated_columns.push("created")
    // ---  create row in table., insert in alphabetical order
                const order_by = update_dict.username.toLowerCase();
                const row_index = t_get_rowindex_by_sortby(tblBody_datatable, order_by)
                tblRow = CreateTblRow(tblBody_datatable, tblName, field_setting, map_id, update_dict, row_index)
    // ---  scrollIntoView,
                if(tblRow){
                    tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' })
    // ---  make new row green for 2 seconds,
                    ShowOkElement(tblRow);
                }

// ++++ deleted ++++
            } else if(is_deleted){
                data_map.delete(map_id);
    //--- delete tblRow
                if (tblRow){
                    tblRow.parentNode.removeChild(tblRow)
               };
            } else {
// ++++ updated > fill updated_columns ++++
                const old_map_dict = (map_id) ? data_map.get(map_id) : null;
    // ---  check which fields are updated, add to list 'updated_columns'
                if(!isEmpty(old_map_dict)){
                    // skip first column (is margin)
                    for (let i = 1, col_field, old_value, new_value; col_field = field_names[i]; i++) {
                        let field_in_old_map = false, field_in_update = false;
                        if (col_field.slice(0, 5) === "group") {
                            // map_dict.usergroups example: "anlz;auth1;auth2;auth3;edit;read"
                            const db_field = col_field.slice(6);
                            // old_map_includes_field and update_includes_field are necessary to catch empty usergroups field
                            field_in_old_map = (!!old_map_dict.usergroups && old_map_dict.usergroups.includes(db_field));
                            field_in_update = (!!update_dict.usergroups && update_dict.usergroups.includes(db_field));
                        } else {
                            // map_dict[field_name] example: perm_system: true
                            field_in_old_map = (col_field in old_map_dict);
                            field_in_update = (col_field in update_dict);
                        }  // if (field_name.slice(0, 5) === "group")

        //console.log("col_field", col_field, "field_in_old_map", field_in_old_map,  "field_in_update", field_in_update);

                        if (field_in_old_map !== field_in_update ) {
                            updated_columns.push(col_field)
                        }
                    }
                }
    // ---  update item
                data_map.set(map_id, update_dict)
            }

        //console.log("updated_columns", updated_columns);
    // ---  make update
            // note: when updated_columns is empty, then updated_columns is still true.
            // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
            if(tblRow && updated_columns.length){
    // ---  make entire row green when row is created
                if(updated_columns.includes("created")){
                    ShowOkElement(tblRow);
        //console.log("ShowOkElement tblRow");
                } else {
    // loop through cells of row
                    for (let i = 1, el_fldName, el, td; td = tblRow.cells[i]; i++) {
                        const el = td.children[0];
                        if (el){
                            UpdateField(el, update_dict);
    // make field green when field name is in updated_columns
                            el_fldName = get_attr_from_el(el, "data-field")
                            if(updated_columns.includes(el_fldName)){
                                ShowOkElement(el);
        //console.log("ShowOkElement", el_fldName);
           }}}}}
        }
    }  // refresh_usermap_item

    function get_tblName_from_selectedBtn() {
        return  (selected_btn === "btn_usergroups") ? "usergroups" :
                (selected_btn === "btn_grouppermits") ? "grouppermits" : "users";
    }
    function get_data_map() {
        return (selected_btn === "btn_grouppermits") ? permit_map : user_map;
    }


//###########################################################################
// +++++++++++++++++ FILTER ++++++++++++++++++++++++++++++++++++++++++++++++++

//========= HandleFilterKeyup  ================= PR2021-03-23
    function HandleFilterKeyup(el, event) {
        console.log( "===== HandleFilterKeyup  ========= ");
        // skip filter if filter value has not changed, update variable filter_text
        const col_index = get_attr_from_el(el, "data-colindex")
        console.log( "col_index", col_index, "event.key", event.key);
        const skip_filter = t_SetExtendedFilterDict(el, col_index, filter_dict, event.key);
        console.log( "filter_dict", filter_dict);

        if (!skip_filter) {
            Filter_TableRows(tblBody_datatable);
        }
    }; // function HandleFilterKeyup


//========= HandleFilterToggle  =============== PR2020-07-21 PR2020-09-14 PR2021-03-23
    function HandleFilterToggle(el_input) {
        console.log( "===== HandleFilterToggle  ========= ");

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

        } else if(filter_tag === "triple") {
            // default filter triple '0'; is show all, '1' is show tickmark, '2' is show without tickmark
// - toggle filter value
            new_value = (filter_value === "2") ? "0" : (filter_value === "1") ? "2" : "1";
// - get new icon_class
            icon_class =  (new_value === "2") ? "tickmark_2_1" : (new_value === "1") ? "tickmark_2_2" : "tickmark_0_0";
        }

    // - put new filter value in filter_dict
        filter_dict[col_index] = [filter_tag, new_value]
        console.log( "filter_dict", filter_dict);
        el_input.className = icon_class;
        Filter_TableRows(tblBody_datatable);

    };  // HandleFilterToggle


//========= Filter_TableRows  ==================================== PR2020-08-17
    function Filter_TableRowsXXX(tblBody) {
        console.log( "===== Filter_TableRows  ========= ");

        const tblName_settings = get_tblName_from_selectedBtn();
        console.log( "tblName_settings", tblName_settings);

// ---  loop through tblBody.rows
        for (let i = 0, tblRow, show_row; tblRow = tblBody.rows[i]; i++) {
        console.log( "tblRow", tblRow);
            show_row = ShowTableRow(tblRow, tblName_settings)
        console.log( "show_row", show_row);
            add_or_remove_class(tblRow, cls_hide, !show_row)
        }
    }; // Filter_TableRows

    function Filter_TableRows() {  // PR2019-06-09 PR2020-08-31
        //console.log( "===== Filter_TableRows=== ");
        //console.log( "filter_dict", filter_dict);
                //console.log( "filter_array", filter_array);
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
                        if(el.tag === "INPUT"){
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
//=========  MSSSS_Response  ================ PR2021-04-23
    function MSSSS_Response(tblName, selected_pk, selected_code, selected_name) {
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
        console.log( "===== set_columns_hidden  === ");
        console.log( "permit_dict", permit_dict);

        if (permit_dict.requsr_role_system) {
            columns_hidden =  [];
        } else if (permit_dict.requsr_role_admin) {
            columns_hidden = ["group_auth1", "group_auth2", "group_auth3"];
        } else if (permit_dict.requsr_role_insp) {
            columns_hidden =  ["group_auth3"];
        } else if (permit_dict.requsr_role_comm) {
            columns_hidden =  ["group_edit", "group_auth1", "group_auth2", "group_anlz"];
        } else if (permit_dict.requsr_role_school) {
            columns_hidden = ["group_auth3", "group_anlz"];
        }

    };  // set_columns_hidden


})  // document.addEventListener('DOMContentLoaded', function()