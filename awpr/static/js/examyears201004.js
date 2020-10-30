// PR2020-09-29 added
document.addEventListener('DOMContentLoaded', function() {
    "use strict";

    // <PERMIT> PR220-10-02
    //  - can view page: only 'role_school', 'role_insp', 'role_admin', 'role_system'
    //  - can add/delete/edit only 'role_admin', 'role_system' plus 'perm_write'
    //  roles are:   'role_student', 'role_teacher', 'role_school', 'role_insp', 'role_admin', 'role_system'
    //  permits are: 'perm_read', 'perm_write', 'perm_auth1', 'perm_auth2', 'perm_docs', 'perm_admin', 'perm_system'

    const cls_hide = "display_hide";
    const cls_hover = "tr_hover";
    const cls_visible_hide = "visibility_hide";
    const cls_selected = "tsa_tr_selected";

// ---  id of selected customer and selected order
    let selected_btn = "btn_user_list";
    let selected_period = {};
    let setting_dict = {};

    let selected_examyear_pk = null;
    let selected_department_pk = null;
    let selected_level_pk = null;
    let selected_sector_pk = null;
    let selected_subjecttype_pk = null;
    let selected_scheme_pk = null;
    let selected_package_pk = null;

    let loc = {};  // locale_dict
    let mod_dict = {};
    let mod_MEY_dict = {};
    let time_stamp = null; // used in mod add user

    let company_dict = {};
    let user_list = [];
    let school_rows = [];
    let examyear_map = new Map();

    let filter_dict = {};
    let filter_mod_employee = false;

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    const url_datalist_download = get_attr_from_el(el_data, "data-datalist_download_url");
    const url_settings_upload = get_attr_from_el(el_data, "data-settings_upload_url");
    const url_examyear_upload = get_attr_from_el(el_data, "data-examyear_upload_url");

// --- get field_settings
    const field_settings = {
        examyear: { //PR2020-06-02 dont use loc.Employee here, has no value yet. Use "Employee" here and loc in CreateTblHeader
                    field_caption: ["", "Exam_year", "Created_on", "Published_on", "Closed_on"],
                    field_names: ["select", "examyear", "createdat", "publishedat", "lockedat"],
                    filter_tags: ["select", "text", "text", "text", "text",],
                    field_width:  ["032", "120", "180", "180", "180"],
                    field_align: ["c", "l", "l", "l", "l"]}
        };
    const tblHead_datatable = document.getElementById("id_tblHead_datatable");
    const tblBody_datatable = document.getElementById("id_tblBody_datatable");

// ---  get elements
    let el_loader = document.getElementById("id_loader");

// ---  check if user has permit to view this page. If not: el_loader does not exist PR2020-10-02
    const has_view_permit = (!!el_loader);
    // has_edit_permit gets value after downloading settings
    let has_edit_permit = false;

// === EVENT HANDLERS ===
// === reset filter when ckicked on Escape button ===
        document.addEventListener("keydown", function (event) {
             if (event.key === "Escape") { ResetFilterRows()}
        });

// --- buttons in btn_container
        const el_btn_container = document.getElementById("id_btn_container")
        if (has_view_permit){
            const btns = el_btn_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                const data_btn = get_attr_from_el(btn,"data-btn")
                btn.addEventListener("click", function() {HandleBtnSelect(data_btn)}, false )
            };
        }
// ---  MODAL EXAMYEAR
        const el_MEY_examyear = document.getElementById("id_MEY_examyear")
        const el_MEY_btn_delete = document.getElementById("id_MEY_btn_delete");
        //if(has_view_permit){el_MEY_btn_delete.addEventListener("click", function() {ModConfirmOpen("delete")}, false )}
        const el_MEY_btn_save = document.getElementById("id_MEY_btn_save");
        if(has_view_permit){ el_MEY_btn_save.addEventListener("click", function() {MEY_Save("save")}, false )}
        const el_MEY_btn_cancel = document.getElementById("id_MEY_btn_cancel");

// ---  MOD CONFIRM ------------------------------------
        let el_confirm_header = document.getElementById("id_confirm_header");
        let el_confirm_loader = document.getElementById("id_confirm_loader");
        let el_confirm_msg_container = document.getElementById("id_confirm_msg_container")
        let el_confirm_msg01 = document.getElementById("id_confirm_msg01")
        let el_confirm_msg02 = document.getElementById("id_confirm_msg02")
        let el_confirm_msg03 = document.getElementById("id_confirm_msg03")

        let el_confirm_btn_cancel = document.getElementById("id_confirm_btn_cancel");
        let el_confirm_btn_save = document.getElementById("id_confirm_btn_save");
        if(has_view_permit){ el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()}) };

// ---  set selected menu button active
    SetMenubuttonActive(document.getElementById("id_hdr_users"));
    if(has_view_permit){
        // period also returns emplhour_list
        const datalist_request = {
                setting: {page_examyear: {mode: "get"}, },
                locale: {page: "examyear"},
                examyear_rows: {get: true}
            };

        DatalistDownload(datalist_request, "DOMContentLoaded");
    }
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
                let call_DisplayCustomerOrderEmployee = true;

                if ("locale_dict" in response) {loc = response.locale_dict};
                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict
                    // <PERMIT> PR220-10-02
                    //  - can view page: only 'role_school', 'role_insp', 'role_admin', 'role_system'
                    //  - can add/delete/edit only 'role_admin', 'role_system' plus 'perm_write'
                    has_edit_permit = (setting_dict.requsr_role_admin && setting_dict.requsr_perm_edit) ||
                                      (setting_dict.requsr_role_system && setting_dict.requsr_perm_edit);

                    if (!isEmpty(setting_dict) && "sel_btn" in setting_dict) { selected_btn = setting_dict.sel_btn}
                };
                // both 'loc' and 'setting_dict' are needed for CreateSubmenu
                CreateSubmenu();
                //if ("company_dict" in response) { company_dict = response.company_dict}

                if ("examyear_rows" in response) {
                    const tblName = "examyear";
                    const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                    RefreshDataMap(tblName, field_names, response.examyear_rows, examyear_map)
                }
                if ("school_rows" in response) { school_rows = response.school_rows}
                HandleBtnSelect(selected_btn, true)  // true = skip_upload

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
        //console.log("===  CreateSubmenu == ");
        let el_submenu = document.getElementById("id_submenu")
            const is_NL = (setting_dict.user_lang === "nl");
            const examyear_lc = (loc.Exam_year) ? loc.Exam_year.toLowerCase() : "";
            const create_lc = (loc.Create) ? loc.Create.toLowerCase() : "";
            const publish_lc = (loc.Publish) ? loc.Publish.toLowerCase() : "";
            const close_lc = (loc.Close_NL_afsluiten) ? loc.Close_NL_afsluiten.toLowerCase() : "";
            const delete_lc = (loc.Delete) ? loc.Delete.toLowerCase() : "";
            const goto_caption = loc.Goto_other_examyear;
            const create_caption = (is_NL) ? loc.Exam_year + " " + create_lc : loc.Create + " " + examyear_lc;
            const publish_caption = (is_NL) ? loc.Exam_year + " " + publish_lc : loc.Publish + " " + examyear_lc;
            const close_caption = (is_NL) ? loc.Exam_year + " " + close_lc : loc.Close_NL_afsluiten + " " + examyear_lc;
            const delete_caption = (is_NL) ? loc.Exam_year + " " + delete_lc : loc.Delete + " " + examyear_lc;

            AddSubmenuButton(el_submenu, goto_caption, function() {ModConfirmOpen("goto")});
            AddSubmenuButton(el_submenu, create_caption, function() {MEY_Open("create")},  ["ml-2"]);
            AddSubmenuButton(el_submenu, publish_caption, function() {MEY_Open("publish")},  ["ml-2"]);
            AddSubmenuButton(el_submenu, close_caption, function() {MEY_Open("close")},  ["ml-2"]);
            AddSubmenuButton(el_submenu, delete_caption, function() {ModConfirmOpen("delete")}, ["ml-2"]);
         el_submenu.classList.remove(cls_hide);
    };//function CreateSubmenu

//###########################################################################
// +++++++++++++++++ EVENT HANDLERS +++++++++++++++++++++++++++++++++++++++++
//=========  HandleBtnSelect  ================ PR2020-09-19
    function HandleBtnSelect(data_btn, skip_upload) {
        console.log( "===== HandleBtnSelect ========= ");
        selected_btn = data_btn
        if(!selected_btn){selected_btn = "btn_user_list"}

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_examyear: {sel_btn: selected_btn}};
            UploadSettings (upload_dict, url_settings_upload);
        };

// ---  highlight selected button
        highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  show only the elements that are used in this tab
        //show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

// ---  fill datatable
        CreateTblHeader();
        FillTblRows();

// --- update header text
        UpdateHeaderText();
    }  // HandleBtnSelect

//=========  HandleTableRowClicked  ================ PR2020-08-03
    function HandleTableRowClicked(tr_clicked) {
        //console.log("=== HandleTableRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

        selected_examyear_pk = null;
        selected_department_pk = null;
        selected_level_pk = null;
        selected_sector_pk = null;
        selected_subjecttype_pk = null;
        selected_scheme_pk = null;
        selected_package_pk = null;

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        DeselectHighlightedRows(tr_clicked, cls_selected);
        tr_clicked.classList.add(cls_selected)

// ---  update selected_examyear_pk
        // only select employee from select table
        const row_id = tr_clicked.id
        if(row_id){
            const arr = row_id.split("_");
            const tblName = arr[0];
            const map_dict = get_mapdict_from_datamap_by_id(examyear_map, row_id)
            if (tblName === "examyear") { selected_examyear_pk = map_dict.id } else
            if (tblName === "department") { selected_department_pk = map_dict.id } else
            if (tblName === "level") { selected_level_pk = map_dict.id } else
            if (tblName === "sector") { selected_sector_pk = map_dict.id } else
            if (tblName === "subjecttype") { selected_subjecttype_pk = map_dict.id } else
            if (tblName === "scheme") { selected_scheme_pk = map_dict.id } else
            if (tblName === "package") { selected_package_pk = map_dict.id };
        }
    }  // HandleTableRowClicked


//========= UpdateHeaderText  ================== PR2020-07-31
    function UpdateHeaderText(){
        //console.log(" --- UpdateHeaderText ---" )
        let header_text = null;
        if(selected_btn === "btn_user_list"){
            header_text = loc.User_list;
        } else {
            header_text = loc.Permissions;
        }
        document.getElementById("id_hdr_text").innerText = header_text;
    }   //  UpdateHeaderText

//=========  CreateTblHeader  === PR2020-07-31
    function CreateTblHeader() {
        console.log("===  CreateTblHeader ===== ");
        const tblName = "examyear";

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

        const field_setting = field_settings[tblName]
        if(field_setting){
            const column_count = field_setting.field_names.length;

//--- insert table rows
            let tblRow_header = tblHead_datatable.insertRow (-1);
            let tblRow_filter = tblHead_datatable.insertRow (-1);

//--- insert th's to tblHead_datatable
            for (let j = 0; j < column_count; j++) {
                const key = field_setting.field_caption[j];
                const caption = (loc[key]) ? loc[key] : key;
                const field_name = field_setting.field_names[j];
                const filter_tag = field_setting.filter_tags[j];
                const class_width = "tw_" + field_setting.field_width[j] ;
                const class_align = "ta_" + field_setting.field_align[j];

// ++++++++++ create header row +++++++++++++++
// --- add th to tblRow.
                let th_header = document.createElement("th");
// --- add div to th, margin not working with th
                    const el_header = document.createElement("div");
                        if (j === 0 ){
// --- add checked image to first column
                           // TODO add multiple selection
                            //AppendChildIcon(el_header, imgsrc_stat00);
                        } else {
// --- add innerText to el_div
                            if(caption) {el_header.innerText = caption};
                        };
// --- add width, text_align
                        el_header.classList.add(class_width, class_align);
                    th_header.appendChild(el_header)
                tblRow_header.appendChild(th_header);

// ++++++++++ create filter row +++++++++++++++
// --- add th to tblRow_filter.
                const th_filter = document.createElement("th");
// --- create element with tag from field_tags
                const el_tag = (filter_tag === "text") ? "input" : "div";
                const el_filter = document.createElement(el_tag);
// --- add EventListener to el_filter
                    const event_str = (filter_tag === "text") ? "keyup" : "click";
                    el_filter.addEventListener(event_str, function(event){HandleFilterField(el_filter, j, event)});
// --- add data-field Attribute.
                    el_filter.setAttribute("data-field", field_name);
                    el_filter.setAttribute("data-filtertag", filter_tag);
// --- add other attributes
                    if (filter_tag === "text") {
                        el_filter.setAttribute("type", "text")
                        el_filter.classList.add("input_text");

                        el_filter.setAttribute("autocomplete", "off");
                        el_filter.setAttribute("ondragstart", "return false;");
                        el_filter.setAttribute("ondrop", "return false;");
                    } else if (["toggle", "activated", "inactive"].indexOf(filter_tag) > -1) {
                        // default empty icon necessary to set pointer_show
                        // default empty icon necessary to set pointer_show
                        append_background_class(el_filter,"tickmark_0_0");
                    }

// --- add width, text_align
                    el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");
                th_filter.appendChild(el_filter)
                tblRow_filter.appendChild(th_filter);
            }  // for (let j = 0; j < column_count; j++)

        }  // if(field_settings[tblName]){
    };  //  CreateTblHeader

//========= FillTblRows  ====================================
    function FillTblRows() {
        //console.log( "===== FillTblRows  === ");
        const tblName = "examyear"
        const data_map =  examyear_map;
        //console.log( "data_map ", data_map);

// --- reset table
        tblBody_datatable.innerText = null
        if(data_map){
// --- loop through data_map
          for (const [map_id, map_dict] of data_map.entries()) {
                //console.log( "map_dict ", map_dict);
          // --- insert row at row_index
                const order_by = map_dict.examyear;
                const row_index = -1; // t_get_rowindex_by_orderby(tblBody_datatable, order_by)
                let tblRow = CreateTblRow(tblBody_datatable, tblName, map_id, map_dict, row_index)
          };
        }  // if(!!data_map)

    }  // FillTblRows

//=========  CreateTblRow  ================ PR2020-06-09
    function CreateTblRow(tblBody, tblName, map_id, map_dict, row_index) {
        console.log("=========  CreateTblRow =========", tblName);
        console.log("map_dict", map_dict);
        let tblRow = null;

        const field_setting = field_settings[tblName]
        console.log("field_setting", field_setting);
        if(field_setting){
            const field_names = field_setting.field_names;
            const field_align = field_setting.field_align;
            const column_count = field_names.length;
            //console.log("field_names", field_names);

// --- insert tblRow into tblBody at row_index
            tblRow = tblBody.insertRow(row_index);
            tblRow.id = map_id
// --- add data attributes to tblRow
            tblRow.setAttribute("data-pk", map_dict.id);
            tblRow.setAttribute("data-ppk", map_dict.country_id);
            tblRow.setAttribute("data-table", tblName);
            tblRow.setAttribute("data-orderby", map_dict.examyear);

            console.log("tblRow", tblRow);
// --- add EventListener to tblRow
            tblRow.addEventListener("click", function() {HandleTableRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
            for (let j = 0; j < column_count; j++) {
                const field_name = field_names[j];
            //console.log("field_name", field_name);
// --- insert td element,
                let el_td = tblRow.insertCell(-1);
// --- add data-field attribute
                el_td.setAttribute("data-field", field_name);
                if (["examyear", "createdat", "publishedat", "locked"].indexOf(field_name) > -1){
                    el_td.addEventListener("click", function() {MEY_Open("edit", el_td)}, false)
                    el_td.classList.add("pointer_show");
                    add_hover(el_td);
                }
// --- add  text_align
               el_td.classList.add("ta_" + field_align[j]);
// --- put value in field
               UpdateField(el_td, map_dict)
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

//=========  UpdateField  ================ PR2020-08-16
    function UpdateField(el_div, map_dict) {
        //console.log("=========  UpdateField =========");
        if(el_div){
            const field_name = get_attr_from_el(el_div, "data-field");
            const fld_value = map_dict[field_name];
            if(field_name){
                if (field_name === "select") {
                    // TODO add select multiple users option PR2020-08-18
                } else if (["examyear"].indexOf(field_name) > -1){
                    el_div.innerText = map_dict[field_name];

                } else if (["createdat", "publishedat", "lockedat"].indexOf(field_name) > -1){
                    const is_true = (!!map_dict[field_name]);
                    const data_value = (is_true) ? 1: 0;
                    el_div.setAttribute("data-value", data_value);
                    let display_text = "";
                    if (is_true){
                        const datetimeUTCiso = map_dict[field_name]
                        const datetimeLocalJS = (datetimeUTCiso) ? new Date(datetimeUTCiso) : null;
                        //format_datetime_from_datetimeJS(loc, datetimeJS, hide_weekday, hide_year, hide_time, hide_suffix)
                        display_text = format_datetime_from_datetimeJS(loc, datetimeLocalJS, false, false, true)
                    } else {
                        display_text = (field_name === "createdat") ? loc.Not_created :
                                        (field_name === "publishedat") ? loc.Not_published :
                                        (field_name === "lockedat") ? loc.Not_closed : "";
                    }
                    el_div.innerText = display_text;
                }
            }  // if(field_name)
        }  // if(el_div)
    };  // UpdateField

// +++++++++++++++++ UPLOAD CHANGES +++++++++++++++++ PR2020-08-03

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

                    const el_MEY_loader = document.getElementById("id_MEY_loader");
                    el_MEY_loader.classList.add(cls_visible_hide);

                    console.log( "response");
                    console.log( response);
                    const mode = get_dict_value(response, ["mode"]);

                    if ("updated_examyear_rows" in response) {
                        MEY_update_after_response (response.updated_examyear_rows);
                    };

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

// +++++++++ MOD EXAM YEAR ++++++++++++++++ PR2020-10-04
// --- also used for level, sector,
    function MEY_Open(mode, el_input){
        console.log(" -----  MEY_Open   ----")
        // mode = 'create, 'publish', 'close', 'edit' (with el_input)
        if(has_edit_permit){
            let selected_pk = null, map_id = null;
            const fldName = get_attr_from_el(el_input, "data-field");
            const tblName = "examyear";

            // el_input is undefined when called by submenu buttons
            if(el_input){
                const tblRow = get_tablerow_selected(el_input);
                selected_pk = get_attr_from_el(tblRow, "data-pk")
                map_id = tblRow.id;
            } else if (mode !== "create") {
                selected_pk = selected_examyear_pk;
                map_id = (selected_pk) ? "examyear_" + selected_pk : null;
            }
            const map_dict = get_mapdict_from_datamap_by_id(examyear_map, map_id)
            const is_addnew = (isEmpty(map_dict));
            mod_MEY_dict = {is_addnew: is_addnew}
            if(is_addnew){
                mod_MEY_dict.country_id = setting_dict.requsr_country_pk;

                mod_MEY_dict.examyear = MEY_get_next_examyear()
                mod_MEY_dict.published = false;
                mod_MEY_dict.locked = false;
            }
            if(!isEmpty(map_dict)){
                mod_MEY_dict.id = map_dict.id
                mod_MEY_dict.mapid = map_dict.mapid
                mod_MEY_dict.country_id = map_dict.country_id

                mod_MEY_dict.examyear = map_dict.examyear
                mod_MEY_dict.published = map_dict.published
                mod_MEY_dict.locked = map_dict.locked;

                mod_MEY_dict.createdat = map_dict.createdat
                mod_MEY_dict.publishedat = map_dict.publishedat
                mod_MEY_dict.lockedat = map_dict.lockedat;

                mod_MEY_dict.modby_username = map_dict.modby_username
                mod_MEY_dict.modifiedat = map_dict.modifiedat
            }

// ---  set header text, input element and info box

            const status = (is_addnew) ? "addnew" : (mod_MEY_dict.locked) ? "locked" : (mod_MEY_dict.published) ? "published" : "created"
            MEY_SetMsgElements(status)

    // ---  show modal
            $("#id_mod_examyear").modal({backdrop: true});
        }
    };  // MEY_Open

//=========  MEY_Save  ================  PR2020-10-01
    function MEY_Save(crud_mode) {
        console.log(" -----  MEY_save  ----", crud_mode);
        console.log( "mod_MEY_dict: ", mod_MEY_dict);

        if(has_edit_permit){
            const is_delete = (crud_mode === "delete")

            let upload_dict = {id: {table: 'examyear', ppk: mod_MEY_dict.country_id} }
            if(mod_MEY_dict.is_addnew) {
                upload_dict.id.mode = "create";
                upload_dict.examyear = {value: mod_MEY_dict.examyear, update: true}
            } else {
                upload_dict.id.pk = mod_MEY_dict.id;
                upload_dict.id.mapid = mod_MEY_dict.mapid;
                upload_dict.id.mode = (is_delete) ? "delete" : "update";
            };

            const el_MEY_loader =  document.getElementById("id_MEY_loader");
            el_MEY_loader.classList.remove(cls_visible_hide);

            // modal is closed by data-dismiss="modal"
            UploadChanges(upload_dict, url_examyear_upload);
        };
    }  // MEY_Save

//=========  MEY_update_after_response  ================  PR2020-10-01
    function MEY_update_after_response(updated_examyear_rows) {
        console.log(" -----  MEY_update_after_response  ----");
        console.log( "mod_MEY_dict: ", mod_MEY_dict);

        if(updated_examyear_rows[0]) {
            const tblName = "examyear";
            const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
            RefreshDataMap(tblName, field_names, updated_examyear_rows, examyear_map);

            const updated_examyear_dict = updated_examyear_rows[0];
            if(!isEmpty(updated_examyear_dict)){
                console.log( "updated_examyear_dict: ", updated_examyear_dict);

                if ("created" in updated_examyear_dict){
                    let msg_list = [loc.Examyear_successfully_created];
                    const el_msg_container = document.getElementById("id_msg_container")
                    const el_list = select_elements_in_container_byClass(el_msg_container)
                    for (let i = 0, el; el = el_list[i]; i++) {
                        const index = get_attr_from_el_int(el, "data-index")
                        el.innerText = (msg_list && msg_list[index]) ? msg_list[index] : null
                    }
                    add_or_remove_class(el_msg_container, "border_bg_valid", true, "border_bg_message")
                    el_MEY_btn_save.classList.add(cls_hide)
                    el_MEY_btn_cancel.innertext = loc.Close

                } else if ("error" in updated_examyear_dict){
                    const err_dict = updated_examyear_dict.error;
                    let msg_list = [null, null, null, null], index = 1
                    if(!isEmpty(err_dict)){
                        for (const [ key, value ] of Object.entries(err_dict)) {
                            if(value) {
                                 msg_list[index] = value;
                                 index += 1;
                            }
                        }
                    }
                    for (let i = 1, el, msg_text; i < 5; i++) {
                        msg_text = (msg_list[i]) ? msg_list[i] : null;
                        el = document.getElementById("id_MEY_msg_0" + i)
                        if(el) {
                            el.innerText = msg_text;
                        }
                    }
                    const el_msg_container = document.getElementById("id_msg_container")
                    add_or_remove_class(el_msg_container, "border_bg_invalid", true, "border_bg_message")
                } else {
                    $("#id_mod_examyear").modal("hide");
                }
            }
        }
    }  // MEY_update_after_response

//========= MEY_get_next_examyear  ============= PR2020-10-04
    function MEY_get_next_examyear(){
        //console.log( "===== MEY_get_next_examyear  ========= ");

        let max_examyear = 0, new_examyear = 0;
        for (const [map_id, item_dict] of examyear_map.entries()) {
            if(item_dict.examyear && item_dict.examyear > max_examyear) {
                max_examyear = item_dict.examyear;
            }
        }
        if (max_examyear){
            new_examyear = max_examyear + 1;
        } else {
            const today = new Date();
            const this_month_index = 1 + today.getMonth();
            const this_year = today.getFullYear()
            new_examyear = (this_month_index < 8) ? this_year : 1 + this_year;
        }
        return new_examyear;
    }; // MEY_get_next_examyear

//========= MEY_SetMsgElements  ============= PR2020-10-05
    function MEY_SetMsgElements(status, response){
        console.log( "===== MEY_SetMsgElements  ========= ");
        console.log( "mod_MEY_dict", mod_MEY_dict);
        console.log( "status", status);
        //  const status = (is_addnew) ? "addnew" : (mod_MEY_dict.locked) ? "locked" : (mod_MEY_dict.published) ? "published" : "created"
// --- set input element
        document.getElementById("id_MEY_examyear").value = mod_MEY_dict.examyear;

// reset msg elements
        const msg_list = (status === "addnew") ? loc.msg_info.create :
                         (status === "created")  ? loc.msg_info.publish :
                         (status === "published")  ? loc.msg_info.close : [];

        const is_error = (response && "msg_error" in response);
        const is_ok = (response && "msg_ok" in response);
        const border_class = (is_error) ? "border_bg_invalid" : (is_ok) ? "border_bg_valid" : "border_bg_message";
        const el_msg_container = document.getElementById("id_msg_container");

        // className removes all other classes from element
        el_msg_container.className = border_class;
        el_msg_container.classList.add("m-4", "px-4", "py-2");

        const el_list = select_elements_in_container_byClass(el_msg_container);
        for (let i = 0, el; el = el_list[i]; i++) {
            const index = get_attr_from_el_int(el, "data-index")
            el.innerText = (msg_list && msg_list[index]) ? msg_list[index] : null
        }

        let err_save = false;
        if (is_ok) {

        } else {
            // --- loop through input elements
            //if("save" in err_dict){
            //    err_save = true;

            //} else {
            //}
            //el_MEY_btn_save.disabled = !validation_ok;
            //if(validation_ok){el_MEY_btn_save.focus()}
        }


// ---  header text
        let header_text = "";
        const examyear_str = (mod_MEY_dict.examyear) ? mod_MEY_dict.examyear.toString() : "---";
        const is_NL = (loc.user_lang === "nl")
        const verb_str = (status === "addnew") ? loc.Create :
                         (status === "created")  ? loc.Publish :
                         (status === "published")  ? loc.Close_NL_afsluiten : "";

        const verb_lc = verb_str.toLowerCase();
        const examyear_lc = loc.Exam_year.toLowerCase();
        header_text =  (is_NL) ? loc.Exam_year + " " + examyear_str + " " + verb_lc :
                                 verb_str + " " + examyear_lc + " " + examyear_str;
        document.getElementById("id_MEY_header").innerText = header_text;

// ---  set text on msg_modified
        let modified_text = null;
        if (status !== "addnew"){
            const modified_dateJS = parse_dateJS_from_dateISO(mod_MEY_dict.modifiedat);
            const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
            const modified_by = (mod_MEY_dict.modby_username) ? mod_MEY_dict.modby_username : "-";
            modified_text = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by
        }
        document.getElementById("id_MEY_msg_modified").innerText = modified_text;

// ---  set text on btn cancel

        el_MEY_btn_cancel.innerText = ((is_ok || err_save) ? loc.Close_NL_sluiten: loc.Cancel);
        if(is_ok || err_save){el_MUA_btn_cancel.focus()}
// ---  set text on btn save
        el_MEY_btn_save.innerText = (is_NL) ? loc.Exam_year + " " + verb_lc :
                                verb_str + " " + + examyear_str;
// ---  set text on btn delete
        el_MEY_btn_delete.innerText = (is_NL) ? loc.Exam_year + " " + loc.Delete.toLowerCase() :
                                loc.Delete + " " + + examyear_str;

    }  // MEY_SetMsgElements

//========= MEY_headertext  ======== // PR2020-10-04
    function MEY_headertext(mode) {
        //console.log(" -----  MEY_headertext   ----")


    }  // MEY_headertext

// +++++++++ END MOD EXAMYEAR ++++++++++++++++++++++++++++++++++++++++++++++++++++

// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2020-08-03
    function ModConfirmOpen(mode, el_input) {
        console.log(" -----  ModConfirmOpen   ----")
        // values of mode are : "delete", "inactive" or "resend_activation_email", "permission_sysadm"

        console.log("mode", mode);
        if(has_edit_permit){
            const tblName = "examyear";
            const data_map = examyear_map;
            let dont_show_modal = false;

    // ---  get selected_pk
            // tblRow is undefined when clicked on delete btn in submenu btn or form (no inactive btn)
            let selected_pk = null;
            const tblRow = get_tablerow_selected(el_input);
            selected_pk = (tblRow) ? get_attr_from_el_int(tblRow, "data-pk") : selected_examyear_pk;

    // ---  get info from data_map
            const map_id =  tblName + "_" + selected_pk;
            const map_dict = get_mapdict_from_datamap_by_id(examyear_map, map_id)

            console.log("data_map", data_map)
            console.log("map_id", map_id)
            console.log("map_dict", map_dict)

    // ---  create mod_dict
            mod_dict = {mode: mode};
            const has_selected_item = (!isEmpty(map_dict));
            if(has_selected_item){
                mod_dict.pk = map_dict.id;
                mod_dict.ppk = map_dict.country_id;
                mod_dict.examyear = map_dict.examyear;
                mod_dict.mapid = map_id;
            };
            if (mode === "inactive") {mod_dict.current_isactive = map_dict.is_active;}

        console.log("mod_dict", mod_dict);
// ---  get header text
            let header_text = "";
            const is_NL = (loc.user_lang === "nl");
            if(mode === "delete"){
                header_text =  (is_NL) ? loc.Exam_year + " " + loc.Delete.toLowerCase() :
                                         loc.Delete + " " + + examyear_str;
            }
// ---  put text in modal form
            const item = (tblName === "examyear") ? loc.Exam_year : "";

            let msg_list = [];
            const hide_save_btn = !has_selected_item;
            if(!has_selected_item){
                msg_list[0] = loc.No_examyer_selected;
            } else {
                const username = (map_dict.username) ? map_dict.username  : "-";
                if(mode === "delete"){
                    msg_list[0] = loc.Exam_year + " '" + mod_dict.examyear + "'" + loc.will_be_deleted
                    msg_list[1] = loc.Do_you_want_to_continue;
                }
            }

            if(!dont_show_modal){
                el_confirm_header.innerText = header_text;
                el_confirm_loader.classList.add(cls_visible_hide)

                const el_list = select_elements_in_containerId_byClass("id_confirm_msg_container");
                for (let i = 0, el; el = el_list[i]; i++) {
                    const index = get_attr_from_el_int(el, "data-index")
                    el.innerText = (msg_list && msg_list[index]) ? msg_list[index] : null
                }





                const caption_save = (mode === "delete") ? loc.Yes_delete : loc.OK;
                el_confirm_btn_save.innerText = caption_save;
                add_or_remove_class (el_confirm_btn_save, cls_hide, hide_save_btn);

                add_or_remove_class (el_confirm_btn_save, "btn-primary", (mode !== "delete"));
                add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", (mode === "delete"));

        // set focus to cancel button
                setTimeout(function (){
                    el_confirm_btn_cancel.focus();
                }, 500);
    // show modal
                $("#id_mod_confirm").modal({backdrop: true});
            }  // if(!dont_show_modal)

        }  // if(has_edit_permit){
    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2019-06-23
    function ModConfirmSave() {
        console.log(" --- ModConfirmSave --- ");
        console.log("mod_dict: ", mod_dict);
        let close_modal = !has_edit_permit;

        if(has_edit_permit){
            let tblRow = document.getElementById(mod_dict.mapid);

    // ---  when delete: make tblRow red, before uploading
            if (tblRow && mod_dict.mode === "delete"){
                ShowClassWithTimeout(tblRow, "tsa_tr_error");
            }

            if(["delete", 'resend_activation_email'].indexOf(mod_dict.mode) > -1) {
    // show loader
                el_confirm_loader.classList.remove(cls_visible_hide)
            } else if (mod_dict.mode === "inactive") {
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
            let upload_dict = { id: {pk: mod_dict.pk,
                                     ppk: mod_dict.ppk,
                                     table: "examyear",
                                     mode: mod_dict.mode,
                                     mapid: mod_dict.mapid}};
            if (mod_dict.mode === "inactive") {
                upload_dict.is_active = {value: mod_dict.new_isactive, update: true}
            };

            console.log("upload_dict: ", upload_dict);
            UploadChanges(upload_dict, url_examyear_upload);
        };
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
            el_confirm_btn_cancel.innerText = loc.Close_NL_sluiten;
            el_confirm_btn_save.classList.add(cls_hide);
        } else {
        // hide mod_confirm when no message
            $("#id_mod_confirm").modal("hide");
        }
    }  // ModConfirmResponse

//###########################################################################
// +++++++++++++++++ REFRESH DATA MAP ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataMap  ================ PR2020-08-16 PR2020-09-30
    function RefreshDataMap(tblName, field_names, data_rows, data_map) {
        console.log(" --- RefreshDataMap  ---");
        console.log("tblName", tblName);
        if (data_rows) {
            const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
            for (let i = 0, update_dict; update_dict = data_rows[i]; i++) {
                RefreshDatamapItem(tblName, field_names, update_dict, data_map);
            }
        }
    }  //  RefreshDataMap

//=========  RefreshDatamapItem  ================ PR2020-08-16 PR2020-09-30
    function RefreshDatamapItem(tblName, field_names, update_dict, data_map) {
        console.log(" --- RefreshDatamapItem  ---");
        console.log("update_dict", update_dict);

        console.log("data_map", data_map);
        console.log("data_map.size before: " + data_map.size);


        if(!isEmpty(update_dict)){
// ---  update or add update_dict in examyear_map
            let updated_columns = [];
    // get existing map_item
            const map_id = update_dict.mapid;
            let tblRow = document.getElementById(map_id);

            const is_deleted = get_dict_value(update_dict, ["deleted"], false)
            const is_created = get_dict_value(update_dict, ["created"], false)

        console.log("is_created", is_created);
        console.log("map_id", map_id);
// ++++ created ++++
            if(is_created){
    // ---  insert new item
                data_map.set(map_id, update_dict);
                updated_columns.push("created")
        console.log("updated_columns", updated_columns);
    // ---  create row in table., insert in alphabetical order
                //const order_by = (update_dict.examyear) ? update_dict.examyear: 0;
                const row_index = 0 //  t_get_rowindex_by_orderby(tblBody_datatable, order_by)
                tblRow = CreateTblRow(tblBody_datatable, tblName, map_id, update_dict, row_index)
        console.log("tblRow", tblRow);
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
                if (tblRow){tblRow.parentNode.removeChild(tblRow)};
            } else {
                const old_map_dict = (map_id) ? data_map.get(map_id) : null;
    // ---  check which fields are updated, add to list 'updated_columns'
                if(!isEmpty(old_map_dict) && field_names){
                    // skip first column (is margin)
                    for (let i = 1, col_field, old_value, new_value; col_field = field_names[i]; i++) {
                        if (col_field in old_map_dict && col_field in update_dict){
                            if (old_map_dict[col_field] !== update_dict[col_field] ) {
                                updated_columns.push(col_field)
                            }}}}
    // ---  update item
                data_map.set(map_id, update_dict)
            }
    // ---  make update
            // note: when updated_columns is empty, then updated_columns is still true.
            // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
            if(tblRow && updated_columns.length){
    // ---  make entire row green when row is created
                if(updated_columns.includes("created")){
                    ShowOkElement(tblRow);
                } else {
    // loop through cells of row
                    for (let i = 1, el_fldName, el; el = tblRow.cells[i]; i++) {
                        if (el){
                            el_fldName = get_attr_from_el(el, "data-field")
                            UpdateField(el, update_dict);
    // make gield green when field name is in updated_columns
                            if(updated_columns.includes(el_fldName)){
                                ShowOkElement(el);
                            }}}}}
        }

        console.log("data_map.size after: " + data_map.size);
        console.log("data_map", data_map);
    }  // RefreshDatamapItem

//========= ResetFilterRows  ====================================
    function ResetFilterRows() {  // PR2019-10-26 PR2020-10-06
       //console.log( "===== ResetFilterRows  ========= ");

        selected_examyear_pk = null;

// ---  deselect all highlighted rows in tblBody
        DeselectHighlightedTblbody(tblBody_datatable, cls_selected)

    }  // function ResetFilterRows
})  // document.addEventListener('DOMContentLoaded', function()