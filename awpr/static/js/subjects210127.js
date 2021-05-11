// PR2020-09-29 added
document.addEventListener('DOMContentLoaded', function() {
    "use strict";

    let el_loader = document.getElementById("id_loader");

// ---  get permits
    // permit dict gets value after downloading permit_list PR2021-03-27
    //  if user has no permit to view this page ( {% if no_access %} ): el_loader does not exist PR2020-10-02
    const may_view_page = (!!el_loader)

    const cls_hide = "display_hide";
    const cls_hover = "tr_hover";
    const cls_visible_hide = "visibility_hide";
    const cls_selected = "tsa_tr_selected";

    let selected_btn = "subject";
    let setting_dict = {};
    let permit_dict = {};

    let loc = {};  // locale_dict
    let mod_dict = {};
    let mod_MSJ_dict = {};

    let selected_subject_pk = null;
    let selected_department_pk = null;
    let selected_level_pk = null;
    let selected_sector_pk = null;
    let selected_subjecttype_pk = null;
    let selected_scheme_pk = null;
    let selected_package_pk = null;

    let examyear_map = new Map();
    let department_map = new Map();
    let level_map = new Map();
    let sector_map = new Map();
    let subjecttype_map = new Map();
    let subject_map = new Map();
    let scheme_map = new Map();
    let schemeitem_map = new Map();
    let package_map = new Map();
    let packageitem_map = new Map();

    let filter_dict = {};

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    const url_datalist_download = get_attr_from_el(el_data, "data-datalist_download_url");
    const url_settings_upload = get_attr_from_el(el_data, "data-settings_upload_url");
    const url_subject_upload = get_attr_from_el(el_data, "data-subject_upload_url");
    const url_subject_import = get_attr_from_el(el_data, "data-subject_import_url");

    let columns_hidden = {levelbases: true};

// --- get field_settings
    const field_settings = {
        subject: {  field_caption: ["", "Abbreviation", "Name", "Departments",  "Sequence"],
                    field_names: ["select", "code", "name", "depbases", "sequence"],
                    field_tags: ["div", "div", "div", "div", "div"],
                    filter_tags: ["select", "text", "text",  "text", "number",],
                    field_width:  ["032", "120", "tw_280", "240", "120",  "120"],
                    field_align: ["c", "l", "l", "l",  "r"]},
        scheme: {  field_caption: ["", "Abbreviation", "Name", "Departments",  "Sequence"],
                    field_names: ["select", "abbrev", "name", "depbases", "sequence"],
                    field_tags: ["div", "div", "div", "div",  "div"],
                    filter_tags: ["select", "text", "text",  "text", "number"],
                    field_width:  ["032", "120", "240", "240",  "120"],
                    field_align: ["c", "l", "l", "l",  "r", "c"]},
        level: {  field_caption: ["", "Abbreviation", "Name", "Departments", "Sequence"],
                    field_names: ["select", "abbrev", "name", "depbases", "sequence"],
                    field_tags: ["div", "div", "div", "div",  "div"],
                    filter_tags: ["select", "text", "text",  "text", "number"],
                    field_width:  ["032", "120", "240", "240",  "120"],
                    field_align: ["c", "l", "l", "l",  "r", "c"]},
        sector: {  field_caption: ["", "Abbreviation", "Name", "Departments",  "Sequence"],
                    field_names: ["select", "abbrev", "name", "depbases", "sequence"],
                    field_tags: ["div", "div", "div", "div",  "div"],
                    filter_tags: ["select", "text", "text",  "text", "number"],
                    field_width:  ["032", "120", "240", "240",  "120"],
                    field_align: ["c", "l", "l", "l",  "r", "c"]},
        };
    const tblHead_datatable = document.getElementById("id_tblHead_datatable");
    const tblBody_datatable = document.getElementById("id_tblBody_datatable");

// === EVENT HANDLERS ===
// === reset filter when ckicked on Escape button ===
        document.addEventListener("keydown", function (event) {
             if (event.key === "Escape") { ResetFilterRows()}
        });

// --- buttons in btn_container
        const el_btn_container = document.getElementById("id_btn_container")
        if (el_btn_container){
            const btns = el_btn_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                const data_btn = get_attr_from_el(btn,"data-btn")
                btn.addEventListener("click", function() {HandleBtnSelect(data_btn)}, false )
            };
        }

// ---  HEADER BAR ------------------------------------
        const el_hdrbar_examyear = document.getElementById("id_hdrbar_examyear");
        const el_hdrbar_school = document.getElementById("id_hdrbar_school");
        const el_hdrbar_department = document.getElementById("id_hdrbar_department");
        if (el_hdrbar_examyear){
            el_hdrbar_examyear.addEventListener("click", function() {
                t_MSED_Open(loc, "examyear", examyear_map, setting_dict, permit_dict, MSED_Response)}, false );
        }
        if (el_hdrbar_department){
            el_hdrbar_department.addEventListener("click", function() {
                t_MSED_Open(loc, "department", department_map, setting_dict, permit_dict, MSED_Response)}, false );
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
            el_MSED_btn_save.addEventListener("click", function() {t_MSED_Save(MSED_Response)}, false);
        }

// ---  MODAL SUBJECT
        const el_MSJ_div_form_controls = document.getElementById("id_div_form_controls")
        if(el_MSJ_div_form_controls){
            let form_elements = el_MSJ_div_form_controls.querySelectorAll(".awp_input_text")
            for (let i = 0, el, len = form_elements.length; i < len; i++) {
                el = form_elements[i];
                if(el){el.addEventListener("keyup", function() {MSJ_InputKeyup(el)}, false )};
            }
        }
        const el_MSJ_code = document.getElementById("id_MSJ_code");
        const el_MSJ_name = document.getElementById("id_MSJ_name");
        const el_MSJ_sequence = document.getElementById("id_MSJ_sequence");

        const el_MSJ_btn_delete = document.getElementById("id_MSJ_btn_delete");
        if(el_MSJ_btn_delete){el_MSJ_btn_delete.addEventListener("click", function() {ModConfirmOpen("delete")}, false )}
        const el_MSJ_btn_log = document.getElementById("id_MSJ_btn_log");
        const el_MSJ_btn_save = document.getElementById("id_MSJ_btn_save");
        if(el_MSJ_btn_save){ el_MSJ_btn_save.addEventListener("click", function() {MSJ_Save("save")}, false )}

// ---  MOD CONFIRM ------------------------------------
        let el_confirm_header = document.getElementById("id_confirm_header");
        let el_confirm_loader = document.getElementById("id_confirm_loader");
        let el_confirm_msg_container = document.getElementById("id_confirm_msg_container")
        let el_confirm_msg01 = document.getElementById("id_confirm_msg01")
        let el_confirm_msg02 = document.getElementById("id_confirm_msg02")
        let el_confirm_msg03 = document.getElementById("id_confirm_msg03")

        let el_confirm_btn_cancel = document.getElementById("id_confirm_btn_cancel");
        let el_confirm_btn_save = document.getElementById("id_confirm_btn_save");
        if(el_confirm_btn_save){ el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()}) };

// ---  set selected menu button active
    SetMenubuttonActive(document.getElementById("id_hdr_users"));
    if(may_view_page){
        // period also returns emplhour_list
        const datalist_request = {
                setting: {page: "page_subject"},
                locale: {page: ["page_subject"]},
                examyear_rows: {get: true},
                school_rows: {get: true},
                department_rows: {get: true},
                subject_rows: {get: true},
                level_rows: {get: true},
                sector_rows: {get: true},
                subjecttype_rows: {get: true},
                scheme_rows: {get: true}
            };

        DatalistDownload(datalist_request);
    }
//  #############################################################################################################

//========= DatalistDownload  ===================== PR2020-07-31
    function DatalistDownload(datalist_request, keep_loader_hidden) {
        console.log( "===== DatalistDownload ===== ")
        console.log("request: ", datalist_request)

// ---  Get today's date and time - for elapsed time
        let startime = new Date().getTime();

// ---  show loader  // keep_loader_hidden not in use yet
        if(!keep_loader_hidden){el_loader.classList.remove(cls_visible_hide)}

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

                let must_create_submenu = false, must_update_headerbar = false;

                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                    must_create_submenu = true;
                };

                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict
                    selected_btn = (setting_dict.sel_btn)
                    must_update_headerbar = true;
                }

                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    // get_permits must come before CreateSubmenu and FiLLTbl
                    b_get_permits_from_permitlist(permit_dict);
                    set_columns_hidden();
                    must_update_headerbar = true;
                }

                if(must_create_submenu){CreateSubmenu()};

                if(must_update_headerbar){
                    b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);
                };

                // call b_render_awp_messages also when there are no messages, to remove existing messages
                const awp_messages = (response.awp_messages) ? response.awp_messages : {};
                b_render_awp_messages(response.awp_messages);

                if ("examyear_rows" in response) {
                    b_fill_datamap(examyear_map, response.examyear_rows)
                };
                if ("department_rows" in response) {
                    b_fill_datamap(department_map, response.department_rows)
                };
                if ("level_rows" in response) {
                    b_fill_datamap(level_map, response.level_rows)
                };
                if ("sector_rows" in response) {
                    b_fill_datamap(sector_map, response.sector_rows)
                };
                if ("subjecttype_rows" in response) {
                    b_fill_datamap(subjecttype_map, response.subjecttype_rows)
                };
                if ("subject_rows" in response) {
                    b_fill_datamap(subject_map, response.subject_rows);
                }

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
            AddSubmenuButton(el_submenu, loc.Add_subject, function() {MSJ_Open()});
            AddSubmenuButton(el_submenu, loc.Delete_subject, function() {ModConfirmOpen("delete")});
            AddSubmenuButton(el_submenu, loc.Upload_subjects, null, "id_submenu_subjectimport", url_subject_import);
         el_submenu.classList.remove(cls_hide);
    };//function CreateSubmenu

//###########################################################################
// +++++++++++++++++ EVENT HANDLERS +++++++++++++++++++++++++++++++++++++++++
//=========  HandleBtnSelect  ================ PR2020-09-19
    function HandleBtnSelect(data_btn, skip_upload) {
        //console.log( "===== HandleBtnSelect ========= ", data_btn);
        selected_btn = data_btn
        if(!selected_btn){selected_btn = "btn_subject"}

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_subject: {sel_btn: selected_btn}};
            UploadSettings (upload_dict, url_settings_upload);
        };

// ---  highlight selected button
        highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  show only the elements that are used in this tab
        //show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

// ---  fill datatable
        FillTblRows();

// --- update header text
        UpdateHeaderText();
    }  // HandleBtnSelect

//=========  HandleTableRowClicked  ================ PR2020-08-03
    function HandleTableRowClicked(tr_clicked) {
        //console.log("=== HandleTableRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

        selected_subject_pk = null;
        selected_department_pk = null;
        selected_level_pk = null;
        selected_sector_pk = null;
        selected_subjecttype_pk = null;
        selected_scheme_pk = null;
        selected_package_pk = null;

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        DeselectHighlightedRows(tr_clicked, cls_selected);
        tr_clicked.classList.add(cls_selected)

// ---  update selected_subject_pk
        // only select employee from select table
        const row_id = tr_clicked.id
        if(row_id){
            const arr = row_id.split("_");
            const tblName = arr[0];
            const map_dict = get_mapdict_from_datamap_by_id(subject_map, row_id)
            if (tblName === "subject") { selected_subject_pk = map_dict.id } else
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
        if(selected_btn === "subjects"){
            header_text = loc.Subjects;
        } else {
            header_text = null;
        }
        document.getElementById("id_hdr_text").innerText = header_text;
    }   //  UpdateHeaderText

//========= FillTblRows  ====================================
    function FillTblRows() {
        //console.log( "===== FillTblRows  === ");
        const tblName = get_tblName_from_selectedBtn();
        const field_setting = field_settings[tblName];

// --- get data_map
        const data_map = get_datamap_from_selBtn();
        //console.log( "data_map", data_map);

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

// --- create table header
        CreateTblHeader(field_setting);

// --- loop through data_map
        if(data_map){
          for (const [map_id, map_dict] of data_map.entries()) {
        // only show rows of selected level / sector / subjecttype / subject
                let show_row = (tblName === "subject") ? true :
                                (!setting_dict.sel_level_pk || map_dict.lvl_id === setting_dict.sel_level_pk) &&
                                (!setting_dict.sel_sector_pk || map_dict.sct_id === setting_dict.sel_sector_pk) &&
                                (!setting_dict.sel_subjecttype_pk || map_dict.sel_subjecttype_pk === setting_dict.sel_subjecttype_pk) &&
                                (!setting_dict.sel_subjecttype_pk || map_dict.subject_id === setting_dict.sel_subject_pk);

                if(show_row){

          // --- insert row at row_index not necessary, map is ordered
                    const order_by = (map_dict.sequence) ? map_dict.sequence + 10000 : 90000;
                    const row_index = -1; // t_get_rowindex_by_sortby(tblBody_datatable, order_by)
                    let tblRow = CreateTblRow(tblBody_datatable, tblName, field_setting, map_id, map_dict, order_by, row_index)
                };
          };
        }  // if(!!data_map)
    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-07-31 PR2021-05-10
    function CreateTblHeader(field_setting) {
        //console.log("===  CreateTblHeader ===== ");

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

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

//=========  CreateTblRow  ================ PR2020-06-09 PR2021-05-10
    function CreateTblRow(tblBody, tblName, field_setting, map_id, map_dict, order_by, row_index) {
        //console.log("=========  CreateTblRow =========", tblName);
        //console.log("map_dict", map_dict);
        let tblRow = null;

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
            tblRow.setAttribute("data-ppk", map_dict.examyear_id);
            tblRow.setAttribute("data-table", tblName);
            tblRow.setAttribute("data-sortby", order_by);

// --- add EventListener to tblRow
            tblRow.addEventListener("click", function() {HandleTableRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
            for (let j = 0; j < column_count; j++) {
                const field_name = field_names[j];

// skip columns if in columns_hidden
                const column_hidden = (columns_hidden[field_name]) ? columns_hidden[field_name] : false;
                if (!column_hidden){
                    const field_tag = field_tags[j];
                    const class_width = "tw_" + field_width[j];
                    const class_align = "ta_" + field_align[j];

            // --- insert td element,
                    let td = tblRow.insertCell(-1);

            // --- create element with tag from field_tags
                    let el = document.createElement(field_tag);

            // --- add data-field attribute
                    el.setAttribute("data-field", field_name);

                    if (field_name === "select") {
                        // TODO add select multiple users option PR2020-08-18
                    } else {
                        el.addEventListener("click", function() {MSJ_Open(td)}, false)
                        el.classList.add("pointer_show");
                        add_hover(el);
                    }

            // --- add width, text_align
                        td.classList.add(class_width, class_align);
                        el.classList.add(class_width, class_align);

            // --- append element
                    td.appendChild(el);
    // --- put value in field
                   UpdateField(el, map_dict)
               };
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

//=========  UpdateField  ================ PR2020-08-16 PR2021-05-10
    function UpdateField(el_div, map_dict) {
        //console.log("=========  UpdateField =========");
        //console.log("el_div", el_div);

        if(el_div){
            const field_name = get_attr_from_el(el_div, "data-field");
            const fld_value = map_dict[field_name];

            if(field_name){
                if (field_name === "select") {
                    // TODO add select multiple users option PR2020-08-18
                } else if (["abbrev", "code", "name", "last_name", "sequence", "examyear"].indexOf(field_name) > -1){
                    el_div.innerText = map_dict[field_name];
                } else if ( field_name === "depbases") {
                    el_div.innerText = b_get_depbases_display(department_map, fld_value);
                } else if (field_name.slice(0, 4) === "perm") {
                    const is_true = (map_dict[field_name]) ? map_dict[field_name] : false;
                    const value_str = field_name.slice(4, 6);
                    const permit_value = (!is_true) ? 0 : (!Number(value_str)) ? 0 : Number(value_str);
                    el_div.setAttribute("data-value", permit_value);
                    let el_icon = el_div.children[0];
                    if(el_icon){add_or_remove_class (el_icon, "tickmark_0_2", is_true)};

                } else if ( field_name === "activated") {
                    const is_activated = (map_dict[field_name]) ? map_dict[field_name] : false;
                    let is_expired = false;

                    const data_value = (is_expired) ? "2" : (is_activated) ? "1" : "0"
                    el_div.setAttribute("data-value", data_value);
                    let el_icon = el_div.children[0];
                    if(el_icon){
                        add_or_remove_class (el_icon, "tickmark_0_2", is_activated);
                        add_or_remove_class (el_icon, "exclamation_0_2", is_expired);
                        add_or_remove_class (el_icon, "tickmark_0_0", !is_activated && !is_expired);
                    }
// ---  add EventListener
                    if(!is_activated){
                        el_div.addEventListener("click", function() {ModConfirmOpen("resend_activation_email", el_div)}, false )
                    }
// ---  add title
                    const title = (is_expired) ? loc.Activationlink_expired + "\n" + loc.Resend_activationlink : null
                    add_or_remove_attr (el_div, "title", title, title);

                } else if (field_name === "is_active") {
                    const is_inactive = !( (map_dict[field_name]) ? map_dict[field_name] : false );
                    el_div.setAttribute("data-value", ((is_inactive) ? 1 : 0) );
                    const img_class = (is_inactive) ? "inactive_1_3" : "inactive_0_2";
                    b_refresh_icon_class(el_div, img_class)
                    //let el_icon = el_div.children[0];
                    //if(el_icon){add_or_remove_class (el_icon, "inactive_1_3", is_inactive, "inactive_0_2")};
// ---  add title
                    add_or_remove_attr (el_div, "title", is_inactive, loc.This_user_is_inactive);
                } else if ( field_name === "last_login") {
                    const datetimeUTCiso = map_dict[field_name]
                    const datetimeLocalJS = (datetimeUTCiso) ? new Date(datetimeUTCiso) : null;
                    el_div.innerText = format_datetime_from_datetimeJS(loc, datetimeLocalJS)
                }
            }  // if(field_name)
        }  // if(el_div)
    };  // UpdateField

//========= set_columns_hidden  ====== PR2021-05-07
    function set_columns_hidden() {
        //console.log( "===== set_columns_hidden  === ");
        //console.log("setting_dict.sel_dep_level_req", setting_dict.sel_dep_level_req);
        columns_hidden.levelbases = (!setting_dict.sel_dep_level_req);
        //console.log("columns_hidden.levelbases", columns_hidden.levelbases);
    }  // set_columns_hidden


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL SELECT EXAMYEAR OR OR DEPARTMENT ++++++++++++++++++++
// functions are in table.js, except for MSED_Response

//=========  MSED_Response  ================ PR2020-12-18 PR2021-05-10
    function MSED_Response(new_setting) {
        //console.log( "===== MSED_Response ========= ");

// ---  upload new selected_pk
// also retrieve the tables that have been changed because of the change in examyear / dep

        const datalist_request = {
                setting: new_setting,
                department_rows: {get: true},
                subject_rows: {get: true},
                level_rows: {get: true},
                sector_rows: {get: true},
                subjecttype_rows: {get: true},
                scheme_rows: {get: true}
            };

        DatalistDownload(datalist_request);

    }  // MSED_Response

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL SELECT  ++++++++++++++++++++++++++++

//=========  ModSelect_Open  ================ PR2020-10-27
    function ModSelect_Open(tblName) {
        console.log( "===== ModSelect_Open ========= ", tblName);

        // <PERMIT> PR2020-10-27
        // - every user may change examyear and department
        // -- only insp, admin and system may change school
        const may_open_modselect = (tblName === "school") ? has_permit_select_school : true;

        //PR2020-10-28 debug: modal gives 'NaN' and 'undefined' when  loc not back from server yet
        if (may_open_modselect && !isEmpty(loc)) {

        const base_pk = (tblName === "examyear" && setting_dict.sel_examyear_pk) ? setting_dict.sel_examyear_pk :
                     (tblName === "school" && setting_dict.requsr_schoolbase_pk) ? setting_dict.requsr_schoolbase_pk :
                     (tblName === "department" && setting_dict.requsr_depbase_pk) ? setting_dict.requsr_depbase_pk : 0;

        console.log( "base_pk ", base_pk);
            mod_dict = {base_pk: base_pk, table: tblName};
            el_ModSelect_input.value = null;
            const item = (tblName === "examyear") ? loc.an_examyear :
                         (tblName === "school") ? loc.a_school :
                         (tblName === "department") ? loc.a_department : "";
            const placeholder = loc.Type_few_letters_and_select + item + loc.in_the_list + "..";
            el_ModSelect_input.setAttribute("placeholder", placeholder)

            console.log( "mod_dict ", mod_dict);
    // ---  fill select table
            ModSelect_FillSelectTable(tblName, 0);

    // ---  set header text
            el_ModSelect_header.innerText = loc.Select + item

    // ---  Set focus to el_ModSelect_input
            //Timeout function necessary, otherwise focus wont work because of fade(300)
            setTimeout(function (){el_ModSelect_input.focus()}, 50);

        // show modal
            $("#id_mod_select_examyear").modal({backdrop: true});
            }
    }  // ModSelect_Open

//=========  ModSelect_Save  ================ PR2020-10-28
    function ModSelect_Save() {
        console.log("===  ModSelect_Save =========");
        console.log("mod_dict", mod_dict);
// selected_pk: {sel_examyear_pk: 23, sel_schoolbase_pk: 15, sel_depbase_pk: 1}

// ---  upload new setting
        const setting = {page_subject: {mode: "get"}};
        if (mod_dict.table === "examyear"){
            setting.sel_examyear_pk = mod_dict.base_pk
        }
        const datalist_request = {
                // page_subject is necessary, otherwise sel_btn will loose its value
                setting: setting,
                examyear_rows: {get: true},
                subject_rows: {get: true},
                school_rows: {get: true},
                department_rows: {get: true},
                level_rows: {get: true},
                sector_rows: {get: true},
                subjecttype_rows: {get: true},
                scheme_rows: {get: true}
            };

        DatalistDownload(datalist_request);

// hide modal
        $("#id_mod_select_examyear").modal("hide");

    }  // ModSelect_Save

//=========  ModSelect_SelectItem  ================ PR2020-10-28
    function ModSelect_SelectItem(tblName, tblRow) {
        console.log( "===== ModSelect_SelectItem ========= ");
        console.log( tblRow);
        // all data attributes are now in tblRow, not in el_select = tblRow.cells[0].children[0];
// ---  get clicked tablerow
        if(tblRow) {
// ---  deselect all highlighted rows
            DeselectHighlightedRows(tblRow, cls_selected)
// ---  highlight clicked row
            tblRow.classList.add(cls_selected)
// ---  get pk from id of select_tblRow
            let data_pk = get_attr_from_el(tblRow, "data-pk", 0)
            if(!Number(data_pk)){
               mod_dict.base_pk = 0;
            } else {
                mod_dict.base_pk = Number(data_pk)
            }
            ModSelect_Save()
        }
    }  // ModSelect_SelectItem

//=========  MSE_InputKeyup  ================ PR2020-03-01
    function MSE_InputKeyup() {
        //console.log( "===== MSE_InputKeyup  ========= ");

// ---  get value of new_filter
        let new_filter = el_ModSelect_input.value
        //console.log( "new_filter", new_filter);

        let tblBody = el_MSE_tblbody_select;
        //const len = tblBody.rows.length;
       // if (new_filter && len){
// ---  filter rows in table select_employee
            const filter_dict = t_Filter_SelectRows(tblBody, new_filter);
// ---  if filter results have only one employee: put selected employee in el_ModSelect_input
            const selected_pk = get_dict_value(filter_dict, ["selected_pk"])
            const selected_value = get_dict_value(filter_dict, ["selected_value"])
        //console.log( "selected_pk", selected_pk);
            if (selected_pk) {
                el_ModSelect_input.value = selected_value;
// ---  put pk of selected employee in mod_dict
                if(!Number(selected_pk)){
                    if(selected_pk === "addall" ) {
                        mod_dict.selected_employee_pk = 0;
                        mod_dict.selected_employee_code = null;
                    }
                } else {
                    mod_dict.selected_employee_pk =  Number(selected_pk);
                    mod_dict.selected_employee_code = selected_value;
                }

// ---  Set focus to btn_save
                el_MSE_btn_save.focus()
            }  //  if (!!selected_pk) {
      //  }
    }; // MSE_InputKeyup

//=========  ModSelect_FillSelectTable  ================ PR2020-08-21
    function ModSelect_FillSelectTable(tblName, selected_pk) {
        console.log( "===== ModSelect_FillSelectTable ========= ");
        console.log( "tblName: ", tblName);

        const caption_none = (tblName === "examyear") ? loc.No_exam_years :
                             (tblName === "school") ? loc.No_schools :
                             (tblName === "department") ?  loc.No_departments : "";
        const tblBody_select = (tblName === "examyear") ? el_MSEY_tblBody_select :
                             (tblName === "school") ? el_ModSelect_tblBody_select :
                             (tblName === "department") ?  el_ModSelect_tblBody_select : "";
        tblBody_select.innerText = null;

        let row_count = 0, add_to_list = false;
//--- loop through data_rows
        const data_rows = (tblName === "examyear") ? examyear_rows :
                         (tblName === "school") ? school_rows :
                         (tblName === "department") ? department_rows : null;
        console.log( "data_rows: ", data_rows);
        for (let i = 0, map_dict; map_dict = data_rows[i]; i++) {
            add_to_list = ModSelect_FillSelectRow(map_dict, tblBody_select, tblName, -1, selected_pk);
            if(add_to_list){ row_count += 1};
        };

        if(!row_count){
            let tblRow = tblBody_select.insertRow(-1);
            const inner_text = (tblName === "order" && mod_dict.customer_pk === 0) ? loc.All_orders : caption_none

            let td = tblRow.insertCell(-1);
            td.innerText = inner_text;

        } else if(row_count === 1){
            let tblRow = tblBody_select.rows[0]
            if(tblRow) {
// ---  highlight first row
                tblRow.classList.add(cls_selected)
                if(tblName === "order") {
                    selected_period.order_pk = get_attr_from_el_int(tblRow, "data-pk");
                    MSE_SelectEmployee(tblName, tblRow)
                }
            }
        }
    }  // ModSelect_FillSelectTable

//=========  ModSelect_FillSelectRow  ================ PR2020-10-27
    function ModSelect_FillSelectRow(map_dict, tblBody_select, tblName, row_index, selected_pk) {
        //console.log( "===== ModSelect_FillSelectRow ========= ");
        //console.log("tblName: ", tblName);
        //console.log( "map_dict: ", map_dict);

//--- loop through data_map
        let pk_int = null, code_value = null, add_to_list = false, is_selected_pk = false;
        if(tblName === "examyear") {
            pk_int = map_dict.examyear_id;
            code_value = (map_dict.examyear) ? map_dict.examyear : "---"
            add_to_list = true;
       } else if(tblName === "school") {
            pk_int = map_dict.base_id;
            const code = (map_dict.sb_code) ? map_dict.sb_code : "---";
            const name = (map_dict.name) ? map_dict.name : "---";
            code_value = code + " - " + name;
            const shiftmap_order_pk = map_dict.o_id;
            // PR2020-06-11 debug: no matches because mod_dict.order_pk was str, not number.
            add_to_list = true

       } else if(tblName === "department") {
            pk_int = map_dict.base_id;
            code_value = (map_dict.abbrev) ? map_dict.abbrev : "---"
            add_to_list = true;

       }

       if (add_to_list){
            // selected_pk = 0 means: all customers / orders/ employees
            is_selected_pk = (selected_pk != null && pk_int === selected_pk)
// ---  insert tblRow  //index -1 results in that the new row will be inserted at the last position.
            let tblRow = tblBody_select.insertRow(row_index);
            tblRow.setAttribute("data-pk", pk_int);
            //tblRow.setAttribute("data-ppk", ppk_int);
            tblRow.setAttribute("data-value", code_value);
// ---  add EventListener to tblRow
            tblRow.addEventListener("click", function() {ModSelect_SelectItem(tblName, tblRow)}, false )
// ---  add hover to tblRow
            //tblRow.addEventListener("mouseenter", function(){tblRow.classList.add(cls_hover);});
            //tblRow.addEventListener("mouseleave", function(){tblRow.classList.remove(cls_hover);});
            add_hover(tblRow);
// ---  highlight clicked row
            //if (is_selected_pk){ tblRow.classList.add(cls_selected)}
// ---  add first td to tblRow.
            let td = tblRow.insertCell(-1);
// --- add a element to td., necessary to get same structure as item_table, used for filtering
            let el_div = document.createElement("div");
                el_div.innerText = code_value;
                el_div.classList.add("tw_090", "px-4", "pointer_show" )
            td.appendChild(el_div);
// --- add second td to tblRow with icon locked, published or activated.
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                el_div.classList.add("tw_032", "stat_1_6")
            td.appendChild(el_div);
        };
        return add_to_list;
    }  // ModSelect_FillSelectRow


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

// +++++++++++++++++ UPLOAD CHANGES +++++++++++++++++ PR2020-08-03

//========= UploadToggle  ============= PR2020-07-31
    function UploadToggle(el_input) {
        //console.log( " ==== UploadToggle ====");

        mod_dict = {};
        const tblRow = get_tablerow_selected(el_input);
        if(tblRow){
            const tblName = get_attr_from_el(tblRow, "data-table")
            const map_id = tblRow.id
            const map_dict = get_mapdict_from_datamap_by_id(subject_map, map_id);

            if(!isEmpty(map_dict)){
                const fldName = get_attr_from_el(el_input, "data-field");
                let permit_value = get_attr_from_el_int(el_input, "data-value");
                let has_permit = (!!permit_value);

                const requsr_pk = get_dict_value(selected_period, ["requsr_pk"])
                const is_request_user = (requsr_pk === map_dict.id)

// show message when sysadmin tries to delete sysadmin permit or add readonly
                if(fldName === "perm_system" && is_request_user && has_permit ){
                    ModConfirmOpen("permission_sysadm", el_input)
                } else if(fldName === "perm01_readonly" && is_request_user && !has_permit ){
                    ModConfirmOpen("permission_sysadm", el_input)
                } else {
// loop through row cells to get value of permissions.
                    // Don't get them from map_dict, might not be correct while changing permissions
                    let new_permit_sum = 0, new_permit_value = 0
                    for (let i = 0, cell, cell_name, cell_value; cell = tblRow.cells[i]; i++) {
                        cell_name = get_attr_from_el(cell, "data-field");
                        if (cell_name.slice(0, 4) === "perm") {
                            cell_value = get_attr_from_el_int(cell, "data-value");
                // toggle value of clicked field
                            if (cell_name === fldName){
                                if(cell_value){
                                    cell_value = 0;
                                } else {
                                    const cell_permit = fldName.slice(4, 6);
                                    cell_value = (Number(cell_permit)) ? Number(cell_permit) : 0;
                                }
                                new_permit_value = cell_value;
                // put new value in cell attribute 'data-value'
                                cell.setAttribute("data-value", new_permit_value)
                            };
                            new_permit_sum += cell_value              }
                    }

// ---  change icon, before uploading
                    let el_icon = el_input.children[0];
                    if(el_icon){add_or_remove_class (el_icon, "tickmark_0_2", new_permit_value)};

// ---  upload changes
                    const upload_dict = { id: {pk: map_dict.id,
                                               ppk: map_dict.examyear_id,
                                               table: "user",
                                               mode: "update",
                                               mapid: map_id},
                                          permits: {value: new_permit_sum, update: true}};
                    UploadChanges(upload_dict, url_subject_upload);
                }
            }  //  if(!isEmpty(map_dict)){
        }  //   if(!!tblRow)
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

                    if ("updated_subject_rows" in response) {
                        document.getElementById("id_MSJ_loader").classList.add(cls_visible_hide)
                        const tblName = "subject";
                        const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                        RefreshDataMap(tblName, response.updated_subject_rows, subject_map);
                        const updated_subject_row = response.updated_subject_rows[0]
                        ModConfirmResponse (updated_subject_row)

                    };
                    $("#id_mod_subject").modal("hide");



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

// +++++++++ MOD SUBJECT ++++++++++++++++ PR2020-09-30
// --- also used for level, sector,
    function MSJ_Open(el_input){
        console.log(" -----  MSJ_Open   ----")
        if(permit_dict.crud_subject){
            let user_pk = null, user_country_pk = null, user_schoolbase_pk = null, mapid = null;
            const fldName = get_attr_from_el(el_input, "data-field");

            // el_input is undefined when called by submenu btn 'Add new'
            const is_addnew = (!el_input);
            mod_MSJ_dict = {is_addnew: is_addnew}
            console.log("is_addnew", is_addnew)

            let tblName = null;
            if(is_addnew){
                tblName = selected_btn;
                mod_MSJ_dict.examyear_id = setting_dict.sel_examyear_pk;

            } else {
                const tblRow = get_tablerow_selected(el_input);
                tblName = get_attr_from_el(tblRow, "data-table")

                const data_map = get_datamap_from_selBtn();
                const map_dict = get_mapdict_from_datamap_by_id(data_map, tblRow.id);
                if(!isEmpty(map_dict)){

        console.log( "map_dict: ", map_dict);
                    mod_MSJ_dict.id = map_dict.id
                    mod_MSJ_dict.mapid = map_dict.mapid
                    mod_MSJ_dict.base_id = map_dict.base_id
                    mod_MSJ_dict.examyear_id = map_dict.examyear_id

                    mod_MSJ_dict.code = map_dict.code
                    mod_MSJ_dict.name = map_dict.name
                    mod_MSJ_dict.sequence = map_dict.sequence
                    mod_MSJ_dict.depbases = map_dict.depbases;

                    mod_MSJ_dict.modby_username = map_dict.modby_username
                    mod_MSJ_dict.modifiedat = map_dict.modifiedat
                }
            }
    // ---  set header text
            MSJ_headertext(is_addnew, tblName, mod_MSJ_dict.name);

    // ---  remove value from el_mod_employee_input
            MSJ_ResetElements(true);  // true = also_remove_values

            if (!is_addnew){
                el_MSJ_code.value = (mod_MSJ_dict.code) ? mod_MSJ_dict.code : null;
                el_MSJ_name.value = (mod_MSJ_dict.name) ? mod_MSJ_dict.name : null;
                el_MSJ_sequence.value = (mod_MSJ_dict.sequence) ? mod_MSJ_dict.sequence : null;
                el_MSJ_sequence.value = mod_MSJ_dict.sequence;

                const modified_dateJS = parse_dateJS_from_dateISO(mod_MSJ_dict.modifiedat);
                const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
                const modified_by = (mod_MSJ_dict.modby_username) ? mod_MSJ_dict.modby_username : "-";

                document.getElementById("id_MSJ_msg_modified").innerText = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by
            }

            MSJ_FillSelectTableDepartment(mod_MSJ_dict.depbases);

    // ---  set focus to  field that is clicked on el_MSJ_code
            const el_div_form_controls = document.getElementById("id_div_form_controls")
            let el_focus = el_div_form_controls.querySelector("[data-field=" + fldName + "]");
            if(!el_focus){ el_focus = el_MSJ_code};
            setTimeout(function (){el_focus.focus()}, 50);

    // ---  disable btn submit, hide delete btn when is_addnew
            add_or_remove_class(el_MSJ_btn_delete, cls_hide, is_addnew )
            add_or_remove_class(el_MSJ_btn_log, cls_hide, is_addnew )

            const disable_btn_save = (!el_MSJ_code.value || !el_MSJ_name.value || !el_MSJ_sequence.value )
            el_MSJ_btn_save.disabled = disable_btn_save;

            MSJ_validate_and_disable();

    // ---  show modal
            $("#id_mod_subject").modal({backdrop: true});
        }
    };  // MSJ_Open

//=========  MSJ_Save  ================  PR2020-10-01
    function MSJ_Save(crud_mode) {
        console.log(" -----  MSJ_save  ----", crud_mode);
        console.log( "mod_MSJ_dict: ", mod_MSJ_dict);

        if(permit_dict.crud_subject){
            // delete is handled by ModConfirm("delete")

            let upload_dict = {table: 'subject', examyear_pk: mod_MSJ_dict.examyear_id};
            if(mod_MSJ_dict.is_addnew) {
                upload_dict.mode = "create";
            } else {
                upload_dict.subject_pk = mod_MSJ_dict.id;
                upload_dict.mapid = mod_MSJ_dict.mapid;
            }
    // ---  put changed values of input elements in upload_dict
            let form_elements = document.getElementById("id_MSJ_form_controls").querySelectorAll(".awp_input_text")
            for (let i = 0, el_input; el_input = form_elements[i]; i++) {
                const fldName = get_attr_from_el(el_input, "data-field");

                let new_value = (el_input.value) ? el_input.value : null;
                let old_value = (mod_MSJ_dict[fldName]) ? mod_MSJ_dict[fldName] : null;

                if(fldName === "sequence"){
                    new_value = (new_value && Number(new_value)) ? Number(new_value) : null;
                    old_value = (old_value && Number(old_value)) ? Number(old_value) : null;
                }
                if (new_value !== old_value) {
                    upload_dict[fldName] = new_value;

    // put changed new value in tblRow before uploading
                    const tblRow = document.getElementById(mod_MSJ_dict.mapid);
                    if(tblRow){
                        const el_tblRow = tblRow.querySelector("[data-field=" + fldName + "]");
                        if(el_tblRow){el_tblRow.innerText = new_value };
                    }
                };
            };
    // ---  get selected departments
            //let dep_list = MSJ_get_selected_depbases();
            //upload_dict['depbases'] = {value: dep_list, update: true}
            let new_depbases = MSJ_GetDepartmentsSelected();
            let old_depbases = (mod_MSJ_dict.depbases) ? mod_MSJ_dict.depbases : null;
        console.log("new_depbases", new_depbases);
        console.log("old_depbases", old_depbases);
            if (new_depbases !== old_depbases) {
                upload_dict['depbases'] = new_depbases;
            }

        console.log("upload_dict", upload_dict);
            document.getElementById("id_MSJ_loader").classList.remove(cls_visible_hide)
// modal is closed by data-dismiss="modal"
            //UploadChanges(upload_dict, url_subject_upload);
        };
    }  // MSJ_Save

//========= MSJ_FillSelectTableDepartment  ============= PR2021-05-10
    function MSJ_FillSelectTableDepartment(subject_depbases) {
        console.log("===== MSJ_FillSelectTableDepartment ===== ");
        console.log("department_map", department_map);

        const data_map = department_map;
        const tblBody_select = document.getElementById("id_MSJ_tblBody_department");
        tblBody_select.innerText = null;

// ---  loop through data_map
        const count_selected = {row_count: 0, selected_count: 0}
        for (const [map_id, dict] of data_map.entries()) {
            MSJ_FillSelectRowDepartment(tblBody_select, count_selected, dict);
        }
        if(data_map.size > 1) {
            MSJ_FillSelectRowDepartment(tblBody_select, count_selected, {}, "<" + loc.All_departments + ">");
        }
    }  // MSJ_FillSelectTableDepartment

//========= MSJ_FillSelectRowDepartment  ============= PR2021-05-10
    function MSJ_FillSelectRowDepartment(tblBody_select, count_selected, dict, select_all_text) {
        console.log("===== MSJ_FillSelectRowDepartment ===== ");
        console.log("dict", dict);

// add_select_all when not isEmpty(dict)
        let pk_int = null, map_id = null, base_code = null;
        let is_selected = false, row_index = -1;
        if (isEmpty(dict)){
            pk_int = 0;
            map_id = "sel_depbase_selectall";
            base_code = select_all_text
            row_index = 0;
// check 'selectall when all items are selected
            is_selected = (count_selected.row_count && count_selected.row_count === count_selected.selected_count)

        } else {
            pk_int = dict.base_id;
            map_id = "sel_depbase_" + dict.base_id;
            base_code = (dict.base_code) ? dict.base_code : "---";
            count_selected.row_count += 1
            row_index = -1;

// check if this department is in mod_MSJ_dict.depbases;. Set tickmark if yes
            if(mod_MSJ_dict.depbases){
                const arr = mod_MSJ_dict.depbases.split(";");
                arr.forEach((obj, i) => {
                     if (pk_int === Number(obj)) { is_selected = true}
                });
            }
        };

        if (is_selected){ count_selected.selected_count += 1 };
        const tickmark_class = (is_selected) ? "tickmark_2_2" : "tickmark_0_0";

        const tblRow = tblBody_select.insertRow(row_index);
        tblRow.id = map_id;
        tblRow.setAttribute("data-pk", pk_int);
        tblRow.setAttribute("data-selected", ((is_selected) ? 1 : 0) );

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
            el_div.innerText = base_code;
            td.appendChild(el_div);

        td.classList.add("tw_200", "px-2", "pointer_show") // , "tsa_bc_transparent")

//--------- add addEventListener
        tblRow.addEventListener("click", function() {MSJ_SelectDepartment(tblRow)}, false);
    } // MSJ_FillSelectRowDepartment

//========= MSJ_SelectDepartment  ============= PR2021-05-10
    function MSJ_SelectDepartment(tblRow){
        console.log( "===== MSJ_SelectDepartment  ========= ");

        if(tblRow){
            const old_is_selected = (!!get_attr_from_el_int(tblRow, "data-selected"));
            const pk_int = get_attr_from_el_int(tblRow, "data-pk");
            const is_select_all = (!pk_int);

// ---  toggle is_selected
            const new_is_selected = !old_is_selected;

            const tblBody_selectTable = tblRow.parentNode;
            if(is_select_all){
// ---  if is_select_all: select/ deselect all rows
                for (let i = 0, row, el, set_tickmark; row = tblBody_selectTable.rows[i]; i++) {
                    MSJ_SetDepartmentSelected(row, new_is_selected)
                }
            } else {
// ---  put new value in this tblRow, show/hide tickmark
                MSJ_SetDepartmentSelected(tblRow, new_is_selected)

// ---  select row 'select_all' if all other rows are selected, deselect otherwise
                // set 'select_all' true when all other rows are clicked
                let has_rows = false, unselected_rows_found = false;
                for (let i = 0, row; row = tblBody_selectTable.rows[i]; i++) {
                    let row_pk = get_attr_from_el_int(row, "data-pk");
                    console.log( "row_pk", row_pk);
                    console.log( "data-selected", get_attr_from_el_int(row, "data-selected"));
                    // skip row 'select_all'
                    if(row_pk){
                        has_rows = true;
                        if(!get_attr_from_el_int(row, "data-selected")){
                            unselected_rows_found = true;
                            break;
                }}};
                const selectall_is_selected = (has_rows && !unselected_rows_found)

// ---  set tickmark in row 'select_all'when has_rows and no unselected_rows_found
                const tblRow_selectall = document.getElementById("sel_depbase_selectall")
                MSJ_SetDepartmentSelected(tblRow_selectall, selectall_is_selected)
            }
        }
    }  // MSJ_SelectDepartment

//========= MSJ_SetDepartmentSelected  ============= PR2020-10-01
    function MSJ_SetDepartmentSelected(tblRow, is_selected){
        //console.log( "  ---  MSJ_SetDepartmentSelected  --- ", is_selected);
// ---  put new value in tblRow, show/hide tickmark
        if(tblRow){
            tblRow.setAttribute("data-selected", ( (is_selected) ? 1 : 0) )
            const img_class = (is_selected) ? "tickmark_2_2" : "tickmark_0_0"
            const el = tblRow.cells[0].children[0];
             if (el){el.className = img_class}
        }
    }  // MSJ_SetDepartmentSelected

//========= MSJ_GetDepartmentsSelected  ============= PR2021-05-10
    function MSJ_GetDepartmentsSelected(){
        //console.log( "  ---  MSJ_GetDepartmentsSelected  --- ")
        let list_str = null;
        const tblBody_select = document.getElementById("id_MSJ_tblBody_department");
        let level_arr = [];
        for (let i = 0, row; row = tblBody_select.rows[i]; i++) {
            let row_pk = get_attr_from_el_int(row, "data-pk");
            // skip row 'select_all' with pk = 0, also skip when pk already in level_arr
            if(row_pk && !level_arr.includes(row_pk)){
                if(!!get_attr_from_el_int(row, "data-selected")){
                    level_arr.push(row_pk);
        }}};
        if (level_arr.length > 1) {
            level_arr.sort((a, b) => a - b);
        };
        if (level_arr.length) {
            list_str = level_arr.join(";");
        };
        return list_str;
    }  // MSJ_GetDepartmentsSelected


//========= MSJ_InputKeyup  ============= PR2020-10-01
    function MSJ_InputKeyup(el_input){
        //console.log( "===== MSJ_InputKeyup  ========= ");
        MSJ_validate_and_disable();
    }; // MSJ_InputKeyup

//=========  MSJ_validate_and_disable  ================  PR2020-10-01
    function MSJ_validate_and_disable() {
        console.log(" -----  MSJ_validate_and_disable   ----")
        let disable_save_btn = false;
// ---  loop through input fields on MSJ_Open
        let form_elements = el_MSJ_div_form_controls.querySelectorAll(".awp_input_text")
        for (let i = 0, el_input; el_input = form_elements[i]; i++) {
            const fldName = get_attr_from_el(el_input, "data-field")
            const  msg_err = MSJ_validate_field(el_input, fldName)
// ---  show / hide error message
            const el_msg = document.getElementById("id_MSJ_msg_" + fldName);
            el_msg.innerText = msg_err;
            add_or_remove_class(el_msg, cls_hide, !msg_err)
            if (msg_err){ disable_save_btn = true};
        };

// ---  disable save button on error
        el_MSJ_btn_save.disabled = disable_save_btn;
    }  // MSJ_validate_and_disable

//=========  MSJ_validate_field  ================  PR2020-10-01
    function MSJ_validate_field(el_input, fldName) {
        console.log(" -----  MSJ_validate_field   ----")
        let msg_err = null;
        if (el_input){
            const value = el_input.value;
            if(["sequence"].indexOf(fldName) > -1){
                const arr = get_number_from_input(loc, fldName, el_input.value);
                msg_err = arr[1];
            } else {
                 const caption = (fldName === "code") ? loc.Abbreviation :
                                (fldName === "name") ? loc.Name  : loc.This_field;
                if (["code", "name"].indexOf(fldName) > -1 && !value) {
                    msg_err = caption + loc.cannot_be_blank;
                } else if (["code"].indexOf(fldName) > -1 && value.length > 10) {
                    msg_err = caption + loc.is_too_long_MAX10;
                } else if (["name"].indexOf(fldName) > -1 &&
                    value.length > 50) {
                        msg_err = caption + loc.is_too_long_MAX50;
                } else if (["code", "name"].indexOf(fldName) > -1) {
                        msg_err = validate_duplicates_in_department(loc, "subject", fldName, caption, mod_MSJ_dict.mapid, value)
                }
            }
        }
        return msg_err;
    }  // MSJ_validate_field


//=========  validate_duplicates_in_department  ================ PR2020-09-11
    function validate_duplicates_in_department(loc, tblName, fldName, caption, selected_mapid, selected_code) {
        //console.log(" =====  validate_duplicates_in_department =====")
        //console.log("fldName", fldName)
        let msg_err = null;
        if (tblName && fldName && selected_code){
            const data_map = (tblName === "subject") ? subject_map : null;
            if (data_map && data_map.size){
                const selected_code_lc = selected_code.trim().toLowerCase()
    //--- loop through subjects
                for (const [map_id, map_dict] of data_map.entries()) {
                    // skip current item
                    if(map_id !== selected_mapid) {
                        const lookup_value = (map_dict[fldName]) ? map_dict[fldName].trim().toLowerCase() : null;
                        if(lookup_value && lookup_value === selected_code_lc){
                            console.log(" =====  validate_duplicates_in_department =====")

                            // check if they have at least one department in common
                            let depbase_in_common = false;
                            const selected_depbases = MSJ_GetDepartmentsSelected();
                            const lookup_departments = map_dict.depbases;
                            console.log("selected_depbases", selected_depbases)
                            console.log("lookup_departments", lookup_departments)
                            if(selected_depbases && lookup_departments){
                                selected_depbases.forEach((sel_dep_pk, i) => {
                                    lookup_departments.forEach((lookup_dep_pk, j) => {
                                        if (sel_dep_pk === lookup_dep_pk){depbase_in_common = true}
                                    });
                                });
                            }
                            if(depbase_in_common){
                                msg_err = caption + " '" + selected_code + "'" + loc.already_exists_in_departments
                                break;
                            }
                        }
                    }
                }
            }
        };
        return msg_err;
    }  // validate_duplicates_in_department

//========= MSJ_ResetElements  ============= PR2020-08-03
    function MSJ_ResetElements(also_remove_values){
        //console.log( "===== MSJ_ResetElements  ========= ");
        // --- loop through input elements
        const fields = ["abbrev", "sequence", "name", "department", "modified"]
        for (let i = 0, field, el_input, el_msg; field = fields[i]; i++) {
            el_input = document.getElementById("id_MSJ_" + field);
            if(el_input){
                el_input.classList.remove("border_bg_invalid", "border_bg_valid");
                if(also_remove_values){ el_input.value = null};
            }
            el_msg = document.getElementById("id_MSJ_msg_" + field);
            if(el_msg){el_msg.innerText = null};
        }
    }  // MSJ_ResetElements

//========= MSJ_SetMsgElements  ============= PR2020-08-02
    function MSJ_SetMsgElements(response){
        console.log( "===== MSJ_SetMsgElements  ========= ");

        const err_dict = ("msg_err" in response) ? response.msg_err : {}
        const validation_ok = get_dict_value(response, ["validation_ok"], false);

        console.log( "err_dict", err_dict);
        console.log( "validation_ok", validation_ok);

        const el_msg_container = document.getElementById("id_msg_container")
        let err_save = false;
        let is_ok = ("msg_ok" in response);
        if (is_ok) {
            const ok_dict = response["msg_ok"];
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

                    let el_input = document.getElementById("id_MSJ_" + field);
                    add_or_remove_class (el_input, "border_bg_invalid", (!!msg_err));
                    add_or_remove_class (el_input, "border_bg_valid", (!msg_err));

                    let el_msg = document.getElementById("id_MSJ_msg_" + field);
                    add_or_remove_class (el_msg, "text-danger", (!!msg_err));
                    el_msg.innerText = (!!msg_err) ? msg_err : msg_info
                }
            }
            el_MSJ_btn_save.disabled = !validation_ok;
            if(validation_ok){el_MSJ_btn_save.focus()}
        }
// ---  show message in footer when no error and no ok msg
        add_or_remove_class(el_MUA_info_footer01, cls_hide, !validation_ok )
        add_or_remove_class(el_MUA_info_footer02, cls_hide, !validation_ok )

// ---  set text on btn cancel
        const el_MUA_btn_cancel = document.getElementById("id_MUA_btn_cancel");
        el_MUA_btn_cancel.innerText = ((is_ok || err_save) ? loc.Close: loc.Cancel);
        if(is_ok || err_save){el_MUA_btn_cancel.focus()}

    }  // MUA_SetMsgElements

//========= MSJ_headertext  ======== // PR2020-09-30
    function MSJ_headertext(is_addnew, tblName, name) {
        //console.log(" -----  MSJ_headertext   ----")
        //console.log("tblName", tblName, "is_addnew", is_addnew)

        let header_text = (tblName === "subject") ? (is_addnew) ? loc.Add_subject : loc.Subject :
                    (tblName === "level") ? (is_addnew) ? loc.Add_level : loc.Level :
                    (tblName === "sector") ? (is_addnew) ? loc.Add_sector : loc.Sector :
                    (tblName === "subjecttype") ? (is_addnew) ? loc.Add_subjecttype : loc.Subjecttype :
                    (tblName === "scheme") ? (is_addnew) ? loc.Add_scheme : loc.Scheme :
                    (tblName === "schemeitem") ? (is_addnew) ? loc.Add_schemeitem : loc.Schemeitem :
                    (tblName === "package") ? (is_addnew) ? loc.Add_package : loc.Package :
                    (tblName === "packageitem") ? (is_addnew) ? loc.Add_package_item : loc.Package_item : "---";

        if (!is_addnew) {
            header_text += ": " + ((name) ? name : "---")

            };
        document.getElementById("id_MSJ_header").innerText = header_text;

        let this_dep_text = (tblName === "subject") ? loc.this_subject :
                    (tblName === "level") ? loc.this_level :
                    (tblName === "sector") ? loc.this_sector :
                    (tblName === "subjecttype") ? loc.this_subjecttype :
                    (tblName === "scheme") ? loc.this_scheme :
                    (tblName === "schemeitem") ? loc.this_schemeitem :
                    (tblName === "package") ? loc.this_package :
                    (tblName === "packageitem") ?  loc.this_package_item : "---";
        document.getElementById("id_MSJ_label_dep").innerText = loc.Departments_where + this_dep_text + loc.occurs + ":";
    }  // MSJ_headertext


// +++++++++ END MOD SUBJECT ++++++++++++++++++++++++++++++++++++++++++++++++++++

// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2020-08-03
    function ModConfirmOpen(mode, el_input) {
        console.log(" -----  ModConfirmOpen   ----")
        // values of mode are : "delete", "inactive" or "resend_activation_email", "permission_sysadm"

        if(permit_dict.crud_subject){
            el_confirm_msg01.innerText = null;
            el_confirm_msg02.innerText = null;
            el_confirm_msg03.innerText = null;

    // ---  get selected_pk
            let tblName = null, selected_pk = null;
            // tblRow is undefined when clicked on delete btn in submenu btn or form (no inactive btn)
            const tblRow = get_tablerow_selected(el_input);
            if(tblRow){
                tblName = get_attr_from_el(tblRow, "data-table")
                selected_pk = get_attr_from_el(tblRow, "data-pk")
            } else {
                tblName = selected_btn;
                selected_pk = (tblName === "subject") ? selected_subject_pk :
                            (tblName === "department") ? selected_department_pk :
                            (tblName === "level") ? selected_level_pk :
                            (tblName === "sector") ? selected_sector_pk :
                            (tblName === "subjecttype") ? selected_subjecttype_pk :
                            (tblName === "scheme") ? selected_scheme_pk :
                            (tblName === "package") ? selected_package_pk : null;
            }
            console.log("selected_pk", selected_pk )

    // ---  get info from data_map
            const data_map = get_datamap_from_selBtn()
            const map_id =  tblName + "_" + selected_pk;
            const map_dict = get_mapdict_from_datamap_by_id(subject_map, map_id)

            console.log("data_map", data_map)
            console.log("map_id", map_id)
            console.log("map_dict", map_dict)

    // ---  create mod_dict
            mod_dict = {mode: mode, table: tblName};
            const has_selected_item = (!isEmpty(map_dict));
            if(has_selected_item){
                mod_dict.id = map_dict.id;
                mod_dict.examyear_id = map_dict.examyear_id;
                mod_dict.abbrev = map_dict.abbrev;
                mod_dict.name = map_dict.name;
                mod_dict.sequence = map_dict.sequence;
                mod_dict.depbases = map_dict.depbases;
                mod_dict.mapid = map_id;
            };
            if (mode === "inactive") {
                  mod_dict.current_isactive = map_dict.is_active;
            }

    // ---  put text in modal form
            let dont_show_modal = false;

            const item = (tblName === "subject") ? loc.Subject :
                           (tblName === "department") ? loc.Department :
                           (tblName === "level") ? loc.Level :
                           (tblName === "sector") ? loc.Sector :
                           (tblName === "subjecttype") ? loc.Subjecttype :
                           (tblName === "scheme") ? loc.Scheme :
                           (tblName === "package") ? loc.Package : "";

            let header_text = (tblName === "subject") ? loc.Delete_subject :
                           (tblName === "department") ? loc.Delete_department :
                           (tblName === "level") ? loc.Delete_level :
                           (tblName === "sector") ? loc.Delete_sector :
                           (tblName === "subjecttype") ? loc.Delete_subjecttype :
                           (tblName === "scheme") ? loc.Delete_scheme :
                           (tblName === "package") ? loc.Delete_package : "";

            console.log("tblName", tblName)
            console.log("item", item)

            let msg_01_txt = null, msg_02_txt = null, msg_03_txt = null;
            let hide_save_btn = false;
            if(!has_selected_item){
                msg_01_txt = loc.There_is_no__ + item.toLowerCase() + loc.__selected;
                hide_save_btn = true;
            } else if(mode === "delete"){
                let item_name = (tblName === "subject") ? mod_dict.name :
                           (tblName === "department") ? mod_dict.name :
                           (tblName === "level") ? mod_dict.name :
                           (tblName === "sector") ? mod_dict.name :
                           (tblName === "subjecttype") ? mod_dict.name :
                           (tblName === "scheme") ? mod_dict.name :
                           (tblName === "package") ? mod_dict.name : "";
                msg_01_txt = item + " '" + item_name + "'" + loc.will_be_deleted
                msg_02_txt = loc.Do_you_want_to_continue;

            }
            if(!dont_show_modal){
                el_confirm_header.innerText = header_text;
                el_confirm_loader.classList.add(cls_visible_hide)
                el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");
                el_confirm_msg01.innerText = msg_01_txt;
                el_confirm_msg02.innerText = msg_02_txt;
                el_confirm_msg03.innerText = msg_03_txt;

                const caption_save = (mode === "delete") ? loc.Yes_delete :
                                (mode === "inactive") ? ( (mod_dict.current_isactive) ? loc.Yes_make_inactive : loc.Yes_make_active ) :
                                (is_mode_resend_activation_email) ? loc.Yes_send_email : loc.OK;
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
            }
        }
    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2019-06-23
    function ModConfirmSave() {
        console.log(" --- ModConfirmSave --- ");
        console.log("mod_dict: ", mod_dict);
        let close_modal = !permit_dict.crud_subject;

        if(permit_dict.crud_subject){
            let tblRow = document.getElementById(mod_dict.mapid);

    // ---  when delete: make tblRow red, before uploading
            if (tblRow && mod_dict.mode === "delete"){
                ShowClassWithTimeout(tblRow, "tsa_tr_error");
            }
            if(mod_dict.mode === "delete") {
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
            let upload_dict = { id: {pk: mod_dict.id,
                                     ppk: mod_dict.examyear_id,
                                     table: mod_dict.table,
                                     mode: mod_dict.mode,
                                     mapid: mod_dict.mapid}};
            if (mod_dict.mode === "inactive") {
                upload_dict.is_active = {value: mod_dict.new_isactive, update: true}
            };

            console.log("upload_dict: ", upload_dict);
            UploadChanges(upload_dict, url_subject_upload);
        };
// ---  hide modal
        if(close_modal) {
            $("#id_mod_confirm").modal("hide");
        }
    }  // ModConfirmSave

//=========  ModConfirmResponse  ================ PR2019-06-23 PR2020-10-29
    function ModConfirmResponse(updated_row) {
        console.log(" --- ModConfirmResponse --- ");
        console.log("updated_row: ", updated_row);

//--- hide loader
        el_confirm_loader.classList.add(cls_visible_hide)
        let show_msg = false, msg01_text = null, msg02_text = null, msg03_text = null;

        const mode = get_dict_value(updated_row, ["mode"])
        if ("err_delete" in updated_row) {
            show_msg = true;
            msg01_text  = get_dict_value(updated_row, ["err_delete"]);
            el_confirm_msg_container.classList.add("border_bg_invalid");
        } else if ("msg_err" in updated_row ||"msg_ok" in updated_row) {
            show_msg = true;
            if ("msg_err" in updated_row) {
                msg01_text = get_dict_value(updated_row, ["msg_err", "msg01"], "");
                if (mod_dict.mode === "resend_activation_email") {
                    msg02_text = loc.Activation_email_not_sent;
                }
                el_confirm_msg_container.classList.add("border_bg_invalid");
            } else if ("msg_ok" in updated_row){
                msg01_text  = get_dict_value(updated_row, ["msg_ok", "msg01"]);
                msg02_text = get_dict_value(updated_row, ["msg_ok", "msg02"]);
                msg03_text = get_dict_value(updated_row, ["msg_ok", "msg03"]);
                el_confirm_msg_container.classList.add("border_bg_valid");
            }
        }
        if (show_msg){
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
// +++++++++++++++++ REFRESH DATA MAP ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataMap  ================ PR2020-08-16 PR2020-09-30 PR2021-05-10
    function RefreshDataMap(tblName, data_rows, data_map) {

        console.log(" --- RefreshDataMap  ---");
        if (data_rows) {
            const field_setting = field_settings[tblName];
            const field_names = (field_setting) ? field_setting.field_names : null;
            for (let i = 0, update_dict; update_dict = data_rows[i]; i++) {
                RefreshDatamapItem(field_setting, field_names, update_dict, data_map);
            }
        }
    }  //  RefreshDataMap

//=========  RefreshDatamapItem  ================ PR2020-08-16 PR2020-09-30
    function RefreshDatamapItem(field_setting, field_names, update_dict, data_map) {
        console.log(" --- RefreshDatamapItem  ---");
        console.log("update_dict", update_dict);
        if(!isEmpty(update_dict)){
// ---  update or add update_dict in subject_map
            let updated_columns = [];
    // get existing map_item
            const tblName = update_dict.table;
            const map_id = update_dict.mapid;
            let tblRow = document.getElementById(map_id);

            const is_deleted = get_dict_value(update_dict, ["deleted"], false)
            const is_created = get_dict_value(update_dict, ["created"], false)

// ++++ created ++++
            if(is_created){
    // ---  insert new item
                data_map.set(map_id, update_dict);
                updated_columns.push("created")
    // ---  create row in table., insert in alphabetical order
                const order_by = (update_dict.sequence) ? update_dict.sequence + 10000 : 90000;
                const row_index = t_get_rowindex_by_sortby(tblBody_datatable, order_by)
                tblRow = CreateTblRow(tblBody_datatable, tblName, field_setting, map_id, update_dict, order_by, row_index)
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

            console.log("map_id", map_id);
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

            console.log("data_map", data_map);
    }  // RefreshDatamapItem

//=========  fill_data_list  ================ PR2020-10-07
// TODO deprecate
    function fill_data_list(data_rows, key_field, value_field) {
        console.log(" --- fill_data_list  ---");
        // datalist maps row.id with row.abbrev
        let data_list = {};
        if (data_rows) {
            for (let i = 0, row; row = data_rows[i]; i++) {
                const key = row[key_field];
                data_list[key] = row[value_field];
            }
        }
       //console.log( "data_list", data_list);
        return data_list
    }  //  fill_data_list

//###########################################################################
// +++++++++++++++++ FILTER ++++++++++++++++++++++++++++++++++++++++++++++++++

//========= HandleFilterField  ====================================
    function HandleFilterField(el, col_index, event) {
       //console.log( "===== HandleFilterField  ========= ");
        // skip filter if filter value has not changed, update variable filter_text

        //console.log( "el_key", el_key);
        //console.log( "col_index", col_index);
        const filter_tag = get_attr_from_el(el, "data-filtertag")
        //console.log( "filter_tag", filter_tag);

// --- get filter tblRow and tblBody
        const tblRow = get_tablerow_selected(el);
        const tblName = get_attr_from_el(tblRow, "data-table")

// --- reset filter row when clicked on 'Escape'
        const skip_filter = t_SetExtendedFilterDict(el, col_index, filter_dict, event.key);

         if ( ["toggle", "inactive"].indexOf(filter_tag) > -1) {
// ---  toggle filter_checked
            let filter_checked = (col_index in filter_dict) ? filter_dict[col_index] : 0;
    // ---  change icon
            let el_icon = el.children[0];
            if(el_icon){
                add_or_remove_class(el_icon, "tickmark_0_0", !filter_checked)
                if(filter_tag === "toggle"){
                    add_or_remove_class(el_icon, "tickmark_0_1", filter_checked === -1)
                    add_or_remove_class(el_icon, "tickmark_0_2", filter_checked === 1)
                } else  if(filter_tag === "inactive"){
                    add_or_remove_class(el_icon, "inactive_0_2", filter_checked === -1)
                    add_or_remove_class(el_icon, "inactive_1_3", filter_checked === 1)
                }
            }

        } else if (filter_tag === "activated") {
// ---  toggle activated
            let filter_checked = (col_index in filter_dict) ? filter_dict[col_index] : 0;
            filter_checked += 1
            if (filter_checked > 1) { filter_checked = -2 }
            if (!filter_checked){
                delete filter_dict[col_index];
            } else {
                filter_dict[col_index] = filter_checked;
            }
    // ---  change icon
            let el_icon = el.children[0];
            if(el_icon){
                add_or_remove_class(el_icon, "tickmark_0_0", !filter_checked)
                add_or_remove_class(el_icon, "exclamation_0_2", filter_checked === -2)
                add_or_remove_class(el_icon, "tickmark_0_1", filter_checked === -1)
                add_or_remove_class(el_icon, "tickmark_0_2", filter_checked === 1)

            }
        }


        Filter_TableRows(tblBody_datatable);
    }; // HandleFilterField

//========= Filter_TableRows  ==================================== PR2020-08-17
    function Filter_TableRows(tblBody) {
        //console.log( "===== Filter_TableRows  ========= ");

        const tblName_settings = (selected_btn === "btn_user_list") ? "users" : "permissions";

// ---  loop through tblBody.rows
        for (let i = 0, tblRow, show_row; tblRow = tblBody.rows[i]; i++) {
            show_row = ShowTableRow(tblRow, tblName_settings)
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
                                } else if(el_value.indexOf(filter_text) === -1){
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
                        } else if(filter_tag === "inactive"){
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

        selected_subject_pk = null;

        filter_dict = {};

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

//========= get_datamap_from_selBtn  ======== // PR2020-09-30
    function get_datamap_from_selBtn() {
        const data_map = (selected_btn === "btn_subject") ? subject_map :
                        (selected_btn === "btn_schemeitem") ? schemeitem_map :
                        (selected_btn === "btn_department") ? department_map :
                        (selected_btn === "btn_level") ? level_map :
                        (selected_btn === "btn_sector") ? sector_map :
                        (selected_btn === "btn_subjecttype") ? subjecttype_map :
                        (selected_btn === "btn_package") ? packageitem_map  : null;
        return data_map;
    }
//========= get_tblName_from_selectedBtn  ======== // PR2021-05-10
    function get_tblName_from_selectedBtn() {
        const data_map = (selected_btn === "btn_subject") ? "subject" :
                        (selected_btn === "btn_schemeitem") ? "schemeitem" :
                        (selected_btn === "btn_department") ? "department" :
                        (selected_btn === "btn_level") ? "level" :
                        (selected_btn === "btn_sector") ? "sector" :
                        (selected_btn === "btn_subjecttype") ? "subjecttype" :
                        (selected_btn === "btn_package") ? "packageitem"  : null;
        return data_map;
    }
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL SELECT EXAMYEAR, SCHOOL OR DEPARTMENT ++++++++++++++++++++
//=========  ModSelSchOrDep_Open  ================ PR2020-10-27 PR2020-11-17
    function ModSelSchOrDep_Open(tblName) {
        //console.log( "===== ModSelSchOrDep_Open ========= ");
        //PR2020-10-28 debug: modal gives 'NaN' and 'undefined' when  loc not back from server yet
        if (!isEmpty(loc)) {
            mod_dict = {base_id: setting_dict.requsr_schoolbase_pk, table: tblName};

// ---  fill select table
            ModSelSchOrDep_FillSelectTable(tblName, 0);  // 0 = selected_pk
// ---  show modal
            $("#id_mod_select_examyear_or_depbase").modal({backdrop: true});
            }
    }  // ModSelSchOrDep_Open

//=========  ModSelSchOrDep_Save  ================ PR2020-10-28
    function ModSelSchOrDep_Save(tblName) {
        //console.log("===  ModSelSchOrDep_Save =========");
        //console.log("mod_dict", mod_dict);

// ---  upload new setting
        let new_setting = {page_subject: {mode: "get"}};
        if (tblName === "school") {
            new_setting.requsr_schoolbase_pk = mod_dict.base_id;
        } else {
            new_setting.requsr_depbase_pk = mod_dict.base_id;
        }
        const datalist_request = {setting: new_setting};
        DatalistDownload(datalist_request);

// hide modal
        $("#id_mod_select_examyear_or_depbase").modal("hide");

    }  // ModSelSchOrDep_Save

//=========  ModSelSchOrDep_SelectItem  ================ PR2020-10-28
    function ModSelSchOrDep_SelectItem(tblName, tblRow) {
        console.log( "===== ModSelSchOrDep_SelectItem ========= ");
        console.log( tblRow);
        // all data attributes are now in tblRow, not in el_select = tblRow.cells[0].children[0];
// ---  get clicked tablerow
        if(tblRow) {
// ---  deselect all highlighted rows
            DeselectHighlightedRows(tblRow, cls_selected)
// ---  highlight clicked row
            tblRow.classList.add(cls_selected)
// ---  get pk from id of select_tblRow
            let data_pk = get_attr_from_el(tblRow, "data-pk", 0)
            if(!Number(data_pk)){
               mod_dict.base_id = 0;
            } else {
                mod_dict.base_id = Number(data_pk)
            }
            ModSelSchOrDep_Save(tblName)
        }
    }  // ModSelSchOrDep_SelectItem

//=========  ModSelSchOrDep_FillSelectTable  ================ PR2020-08-21
    function ModSelSchOrDep_FillSelectTable(tblName, selected_pk) {
        console.log( "===== ModSelSchOrDep_FillSelectTable ========= ");

        const header_text = (tblName === "school") ? loc.Select_school :  loc.Select_department ;
        document.getElementById("id_MSED_header_text").innerText = header_text;

        const caption_none = (tblName === "school") ? loc.No_schools :  loc.No_departments ;
        const tblBody_select = el_ModSelSchOrDep_tblBody_select;
        tblBody_select.innerText = null;

        let row_count = 0, add_to_list = false;
// --- loop through data_map
        const data_map = (tblName === "school") ? school_map : department_map ;
        if(data_map){
            for (const [map_id, map_dict] of data_map.entries()) {
                add_to_list = ModSelSchOrDep_FillSelectRow(map_dict, tblBody_select, tblName, -1, selected_pk);
                if(add_to_list){ row_count += 1};
            };
        }  // if(!!data_map)

        if(!row_count){
            let tblRow = tblBody_select.insertRow(-1);
            let td = tblRow.insertCell(-1);
            td.innerText = caption_none;

        } else if(row_count === 1){
            let tblRow = tblBody_select.rows[0]
            if(tblRow) {
// ---  highlight first row
                tblRow.classList.add(cls_selected)
                if(tblName === "order") {
                    selected_period.order_pk = get_attr_from_el_int(tblRow, "data-pk");
                    MSE_SelectEmployee(tblName, tblRow)
                }
            }
        }
    }  // ModSelSchOrDep_FillSelectTable

//=========  ModSelSchOrDep_FillSelectRow  ================ PR2020-10-27
    function ModSelSchOrDep_FillSelectRow(map_dict, tblBody_select, tblName, row_index, selected_pk) {
        //console.log( "===== ModSelSchOrDep_FillSelectRow ========= ");
        //console.log("tblName: ", tblName);
        //console.log( "map_dict: ", map_dict);

//--- loop through data_map
        let pk_int = null, code_value = null, add_to_list = false, is_selected_pk = false;
        if(tblName === "school") {
            pk_int = map_dict.base_id;
            const code = (map_dict.sb_code) ? map_dict.sb_code : "---";
            const name = (map_dict.name) ? map_dict.name : "---";
            code_value = code + " - " + name;
            const shiftmap_order_pk = map_dict.o_id;
            // PR2020-06-11 debug: no matches because mod_dict.order_pk was str, not number.
            add_to_list = true

       } else if(tblName === "department") {
            pk_int = map_dict.base_id;
            code_value = (map_dict.abbrev) ? map_dict.abbrev : "---"
            add_to_list = true;
       }

       if (add_to_list){
            // selected_pk = 0 means: all customers / orders/ employees
            is_selected_pk = (selected_pk != null && pk_int === selected_pk)
// ---  insert tblRow  //index -1 results in that the new row will be inserted at the last position.
            let tblRow = tblBody_select.insertRow(row_index);
            tblRow.setAttribute("data-pk", pk_int);
            //tblRow.setAttribute("data-ppk", ppk_int);
            tblRow.setAttribute("data-value", code_value);
// ---  add EventListener to tblRow
            tblRow.addEventListener("click", function() {ModSelSchOrDep_SelectItem(tblName, tblRow)}, false )
// ---  add hover to tblRow
            add_hover(tblRow);
// ---  highlight clicked row
            //if (is_selected_pk){ tblRow.classList.add(cls_selected)}
// ---  add first td to tblRow.
            let td = tblRow.insertCell(-1);
// --- add a element to td., necessary to get same structure as item_table, used for filtering
            let el_div = document.createElement("div");
                el_div.innerText = code_value;
                el_div.classList.add("tw_420", "px-2", "pointer_show" )
            td.appendChild(el_div);
        };
        return add_to_list;
    }  // ModSelSchOrDep_FillSelectRow


})  // document.addEventListener('DOMContentLoaded', function()