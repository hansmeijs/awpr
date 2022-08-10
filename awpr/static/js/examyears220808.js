// PR2020-09-29 added

document.addEventListener('DOMContentLoaded', function() {
    "use strict";

    selected = {
        examyear_pk: null
    };

// ---  get el_loader
    let el_loader = document.getElementById("id_loader");

// ---  get permits
    // permit dict gets value after downloading permit_list PR2021-03-27
    //  if user has no permit to view this page ( {% if no_access %} ): el_loader does not exist PR2020-10-02
    const may_view_page = (!!el_loader)

    let usergroups = [];

    let mod_dict = {};
    let mod_MCREY_dict = {};

    let selected_copyto_examyear_dict = {};

    let user_list = [];

    let examyear_map = new Map();

    //let filter_dict = {};
    let filter_mod_employee = false;

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    urls.url_usersetting_upload = get_attr_from_el(el_data, "data-url_usersetting_upload");
    urls.url_examyear_upload = get_attr_from_el(el_data, "data-url_examyear_upload");
    urls.url_examyear_copytosxm = get_attr_from_el(el_data, "data-url_examyear_copytosxm");
    urls.url_subjectscheme_copyfrom = get_attr_from_el(el_data, "data-url_subjectscheme_copyfrom");

    urls.url_school_upload = get_attr_from_el(el_data, "data-url_school_upload");

// --- get field_settings
    const field_settings = {
        //PR2020-06-02 dont use loc.Examyear here, has no value yet. Use "Examyear" here and loc in CreateTblHeader
        examyear: {
                    field_caption: ["", "Examyear", "Created_at", "Published", "Published_at", "Closed", "Closed_on"],
                    field_names: ["select", "examyear_code", "createdat", "published", "publishedat", "locked", "lockedat"],
                    filter_tags: ["select", "text", "text", "toggle", "text", "toggle", "text"],
                    field_width:  ["032", "120", "120", "120", "120", "120", "120"],
                    field_align: ["c", "l", "l", "c", "l", "c", "l"]}

        };
    const tblHead_datatable = document.getElementById("id_tblHead_datatable");
    const tblBody_datatable = document.getElementById("id_tblBody_datatable");

    let has_permit_select_school = false;

// === EVENT HANDLERS ===
// === reset filter when ckicked on Escape button ===
        document.addEventListener("keydown", function (event) {
             if (event.key === "Escape") { ResetFilterRows()}
        });

// ---  HEADER BAR ------------------------------------
        const el_hdrbar_examyear = document.getElementById("id_hdrbar_examyear");
        const el_hdrbar_school = document.getElementById("id_hdrbar_school");
        const el_hdrbar_department = document.getElementById("id_hdrbar_department");
        if (el_hdrbar_examyear){
            el_hdrbar_examyear.addEventListener("click", function() {
                t_MSED_Open(loc, "examyear", examyear_map, setting_dict, permit_dict, MSED_Response)}, false );
        }

// ---  MODAL CREATE EXAMYEAR
        const el_MCREY_input_code = document.getElementById("id_MCREY_examyear_code");
        if(el_MCREY_input_code){
            el_MCREY_input_code.addEventListener("change", function() {MCREY_Input(el_MCREY_input_code)}, false )};

        const el_MCREY_loader = document.getElementById("id_MCREY_loader");
        const el_MCREY_msg_container = document.getElementById("id_MCREY_msg_container");

        const el_MCREY_btn_save = document.getElementById("id_MCREY_btn_save");
        if(el_MCREY_btn_save){
            el_MCREY_btn_save.addEventListener("click", function() {MCREY_Save("save")}, false )};
        const el_MCREY_btn_cancel = document.getElementById("id_MCREY_btn_cancel");

// ---  MODAL EDIT EXAMYEAR
        const el_MODEY_form_controls = document.getElementById("id_MODEY_form_controls")
        if(el_MODEY_form_controls){
            const form_elements = el_MODEY_form_controls.querySelectorAll(".awp_input_select, .awp_input_checkbox")
            for (let i = 0, el; el = form_elements[i]; i++) {
                const even_str = (el.classList.contains("awp_input_checkbox")) ? "click" : "change";
                el.addEventListener(even_str, function() {MODEY_InputChanged(el)}, false);
            };
        };
        const el_MODEY_btn_save = document.getElementById("id_MODEY_btn_save");
        if(el_MODEY_btn_save){
            el_MODEY_btn_save.addEventListener("click", function() {MODEY_Save()}, false )};
        //const el_MODEY_btn_cancel = document.getElementById("id_MODEY_btn_cancel");

// ---  MOD CONFIRM ------------------------------------
        let el_modconfirm_header = document.getElementById("id_modconfirm_header");
        let el_modconfirm_loader = document.getElementById("id_modconfirm_loader");
        let el_modconfirm_msg_container = document.getElementById("id_modconfirm_msg_container")
        let el_modconfirm_btn_cancel = document.getElementById("id_modconfirm_btn_cancel");
        let el_modconfirm_btn_save = document.getElementById("id_modconfirm_btn_save");
        if(el_modconfirm_btn_save){
            el_modconfirm_btn_save.addEventListener("click", function() {ModConfirmSave()});
        };

// ---  set selected menu button active
    //SetMenubuttonActive(document.getElementById("id_hdr_users"));
    if(may_view_page){
        const datalist_request = {
                setting: {page: "page_examyear"},
                locale: {page: ["page_examyear"]},
                examyear_rows: {get: true}
            };

        DatalistDownload(datalist_request, "DOMContentLoaded");
    }

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
                let must_create_submenu = false;
                let must_update_headerbar = false;
                let isloaded_loc = false, isloaded_settings = false, isloaded_permits = false;

                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                    isloaded_loc = true;
                };

                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict;
                    isloaded_settings = true;
                };
                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    // b_get_permits_from_permitlist must come before CreateSubmenu and FiLLTbl
                    b_get_permits_from_permitlist(permit_dict);
                    usergroups = permit_dict.usergroup_list;
                    isloaded_permits = true;
                }
                // both 'loc' and 'setting_dict' are needed for CreateSubmenu
                if (isloaded_loc && isloaded_settings) {CreateSubmenu()};
                if(isloaded_settings || isloaded_permits){
                    b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);
                };
                if ("messages" in response) {
                    console.log("response.messages", response.messages)
                    b_show_mod_message_dictlist(response.messages);
                };
                if ("examyear_rows" in response) {
                    examyear_rows = response.examyear_rows;
                    //const tblName = "examyear";
                    //const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                    //RefreshDataMap(tblName, field_names, response.examyear_rows, examyear_map)
                };
                if(isloaded_settings){
            // ---  fill datatable
                    CreateTblHeader();
                    FillTblRows();
                };
            },
            error: function (xhr, msg) {
// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                //console.log(msg + '\n' + xhr.responseText);
            }
        });
    }  // function DatalistDownload

//=========  CreateSubmenu  ===  PR2020-07-31
    function CreateSubmenu() {
        //console.log("===  CreateSubmenu == ");
        let el_submenu = document.getElementById("id_submenu")
            el_submenu.innerHTML = null;

            if (permit_dict.requsr_role_admin && permit_dict.permit_crud){
                // may create, publish, lock exam year
                AddSubmenuButton(el_submenu, loc.Create_new_examyear, function() {MCREY_Open("create")});
                AddSubmenuButton(el_submenu, loc.Publish_examyear, function() {MCREY_Open("publish")});
                AddSubmenuButton(el_submenu, loc.Undo_publish_examyear, function() {ModConfirmUndoOrDelete_Open("undo_published")});
                AddSubmenuButton(el_submenu, loc.Close_examyear, function() {MCREY_Open("lock")});
                AddSubmenuButton(el_submenu, loc.Undo_closure_examyear, function() {ModConfirmUndoOrDelete_Open("undo_locked")});
                AddSubmenuButton(el_submenu, loc.Delete_last_examyear, function() {ModConfirmUndoOrDelete_Open("delete")});
                if (permit_dict.requsr_role_system){

                    AddSubmenuButton(el_submenu, loc.Copy_subject_schemes, function() {
                     t_MSED_Open(loc, "examyear", examyear_map, setting_dict, permit_dict, MSED_Response, true) }); // true = all_countries

                    AddSubmenuButton(el_submenu, loc.Upload_awpdata, function() {ModUploadAwp_open()}, null, "id_submenu_importawp");
                };
            };
         el_submenu.classList.remove(cls_hide);
    };//function CreateSubmenu

//###########################################################################
// +++++++++++++++++ EVENT HANDLERS +++++++++++++++++++++++++++++++++++++++++


//=========  HandleTblRowClicked  ================ PR2020-08-03
    function HandleTblRowClicked(tr_clicked) {
        console.log("=== HandleTblRowClicked");
        console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

// ---  deselect all highlighted rows, select clicked row
        t_td_selected_clear(tr_clicked.parentNode);
        t_td_selected_set(tr_clicked);

// ---  update selected.examyear_pk
        const pk_int = get_attr_from_el_int(tr_clicked, "data-pk");
        const [index, data_dict, compare] = b_recursive_integer_lookup(examyear_rows, "id", pk_int);
        selected.examyear_pk = (!isEmpty(data_dict)) ? data_dict.id : null;
        console.log( "data_dict: ", data_dict);
        console.log( "selected: ", selected);
    } ; // HandleTblRowClicked


//=========  CreateTblHeader  === PR2020-07-31
    function CreateTblHeader() {
        //console.log("===  CreateTblHeader ===== ");

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
                    } else if (filter_tag === "toggle") {
                        // default empty icon necessary to set pointer_show
                        append_background_class(el_filter,"tickmark_0_0");
                    };

// --- add width, text_align
                    el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");
                th_filter.appendChild(el_filter)
                tblRow_filter.appendChild(th_filter);
            }  // for (let j = 0; j < column_count; j++)

        }  // if(field_settings[tblName]){
    };  //  CreateTblHeader

//========= FillTblRows  ====================================
    function FillTblRows() {
        console.log( "===== FillTblRows  === ");
        // display exyr_school when req_usr.role <= c.ROLE_008_SCHOOL:
        const tblName = "examyear";
        const field_setting = field_settings[tblName]

// --- reset table
        tblBody_datatable.innerText = null;

        if(examyear_rows){
// --- loop through data_map

            for (let i = 0, data_dict; data_dict = examyear_rows[i]; i++) {
    //console.log( "data_dict ", data_dict);
        // --- insert tblRow into tblBody at row_index
                let tblRow = CreateTblRow(tblName, field_setting, data_dict);
          };
        };
    };  // FillTblRows

//=========  CreateTblRow  ================ PR2020-06-09
    function CreateTblRow(tblName, field_setting, data_dict) {
        //console.log("=========  CreateTblRow =========", tblName);
        //console.log("data_dict", data_dict);

        const field_names = field_setting.field_names;
        const field_tag = "div";
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;

// ---  lookup index where this row must be inserted
        const ob1 = (data_dict.examyear_code) ? data_dict.examyear_code.toString() : "";

        const row_index = b_recursive_tblRow_lookup(tblBody_datatable, setting_dict.user_lang, ob1, null, null, true);

// --- insert tblRow into tblBody at row_index
        const tblRow = tblBody_datatable.insertRow(row_index);
        tblRow.id = data_dict.mapid

// --- add data attributes to tblRow
        tblRow.setAttribute("data-pk", data_dict.id);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);

// --- add EventListener to tblRow
        tblRow.addEventListener("click", function() {HandleTblRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
        for (let j = 0; j < column_count; j++) {
            const field_name = field_names[j];
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

    // --- append element
            td.appendChild(el);

    // --- add EventListener to td
            if (j){ // skip first column (margin to select without opening mod)
                if (field_name === "examyear_code"){
                    td.addEventListener("click", function() {MODEY_Open(td)}, false);
                    td.classList.add("pointer_show");
                    add_hover(td);
                };
            };
// --- put value in field
           UpdateField(el, data_dict)
        };

        return tblRow
    };  // CreateTblRow

//=========  UpdateTblRow  ================ PR2020-08-01
    function UpdateTblRow(tblRow, tblName, data_dict) {
        console.log("=========  UpdateTblRow =========");
        if (tblRow && tblRow.cells){
            for (let i = 0, td; td = tblRow.cells[i]; i++) {
        console.log("td", td);
        console.log("    td.children[0]", td.children[0]);
                UpdateField(td.children[0], data_dict);
            }
        }
    };  // UpdateTblRow

//=========  UpdateField  ================ PR2020-08-16
    function UpdateField(el_div, data_dict) {
        //console.log("=========  UpdateField =========");
        //console.log("data_dict", data_dict);
    //console.log("el_div", el_div);
        if(el_div){
            const field_name = get_attr_from_el(el_div, "data-field");
            const fld_value = data_dict[field_name];

            if(field_name){
                if (field_name === "select") {
                    // TODO add select multiple users option PR2020-08-18
                } else if (["published", "locked"].includes(field_name)){
                    //const el_img = el_div.children[0];
                    //const img_class = (fld_value) ? "tickmark_1_2" : "tickmark_0_0";
                    //if(el_img) { el_img.className = img_class}
                    el_div.className = (fld_value) ? "tickmark_1_2" : "tickmark_0_0";

                } else if (["createdat", "publishedat", "lockedat"].includes(field_name)){
                    let is_true = false, modat = null;
                    if (field_name === "createdat"){
                        modat = data_dict.createdat;
                        is_true = (!!modat);
                    } else if (field_name === "publishedat"){
                        is_true = data_dict.published;
                        modat = data_dict.publishedat;
                    } else   if (field_name === "lockedat"){
                        is_true = data_dict.locked;
                        modat = data_dict.lockedat;
                    }
                    const data_value = (is_true) ? 1: 0;
                    el_div.setAttribute("data-value", data_value);
                    let display_text = "";
                    if (is_true){
                        const datetimeUTCiso = modat;
        //console.log("datetimeUTCiso", datetimeUTCiso);
                        const datetimeLocalJS = (datetimeUTCiso) ? new Date(datetimeUTCiso) : null;
        //console.log("datetimeLocalJS", datetimeLocalJS);
                        //format_datetime_from_datetimeJS(loc, datetimeJS, hide_weekday, hide_year, hide_time, hide_suffix)
                        display_text = format_datetime_from_datetimeJS(loc, datetimeLocalJS, false, false, true)
        //console.log("display_text", display_text);
                    }
                    el_div.innerText = (display_text) ? display_text : "\n";
                } else {
                    el_div.innerText = (data_dict[field_name]) ? data_dict[field_name] : "\n";
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
                    el_loader.classList.add(cls_visible_hide);
                    el_modconfirm_loader.classList.add(cls_hide);

                    el_MCREY_loader.classList.add(cls_visible_hide);

                    console.log( "response");
                    console.log( response);
                    const mode = get_dict_value(response, ["mode"]);

                    if ("updated_examyear_rows" in response) {
                        MCREY_update_after_response (response);
                    };
                    if ("updated_school_rows" in response) {
                        MCREY_update_after_response (response);
                    };
                    if ("SXM_added_list" in response) {
                        $("#id_mod_confirm").modal("hide");
                    };
                    if ("SXM_deletedlist" in response) {
                        $("#id_mod_confirm").modal("hide");
                    };
                    if ("checked_examyear" in response) {
                        ModConfirmUndoOrDelete_Checked(response.checked_examyear)
                    };

                    if ("messages" in response) {
                        console.log("response.messages", response.messages)
                        b_show_mod_message_dictlist(response.messages);
                    }
                    if ("log_list" in response) {
                       OpenLogfile(loc, response.log_list);
                    };
                },  // success: function (response) {
                error: function (xhr, msg) {
                    // ---  hide loader
                    el_loader.classList.add(cls_visible_hide)
                    //console.log(msg + '\n' + xhr.responseText);
                }  // error: function (xhr, msg) {
            });  // $.ajax({
        }  //  if(!!row_upload)
    };  // UploadChanges

// +++++++++++++++++ UPDATE +++++++++++++++++++++++++++++++++++++++++++


// +++++++++ MOD EXAM YEAR ++++++++++++++++ PR2020-10-04  PR2022-08-02
    function MCREY_Open(mode, el_input){
        console.log(" -----  MCREY_Open   ----")
        console.log("selected.examyear_pk", selected.examyear_pk)
        console.log("mode", mode)
        console.log("el_input", el_input)
        //console.log("permit_dict", permit_dict)
        // mode = 'create, 'publish', 'lock', 'edit' (with el_input)

        const is_addnew = (mode === "create");
        let show_modal = false;

        if(permit_dict.permit_crud){
            if(is_addnew){
                mod_MCREY_dict = {
                    mode: mode,
                    is_addnew: is_addnew,
                    country_id: permit_dict.requsr_country_pk,
                    examyear_code: MCREY_get_next_examyear()
                };
                show_modal = true;
            } else {
                let selected_pk = null, map_id = null;
                // el_input is undefined when called by submenu buttons
                if(el_input){
                    const tblRow = t_get_tablerow_selected(el_input);
                    selected_pk = get_attr_from_el(tblRow, "data-pk")
                    map_id = tblRow.id;
                } else {
                    selected_pk = selected.examyear_pk;
                    map_id = (selected_pk) ? "examyear_" + selected_pk : null;
                }
                const [index, data_dict, compare] = b_recursive_integer_lookup(examyear_rows, "id", selected_pk);

            console.log("   data_dict", data_dict)
                if(isEmpty(data_dict)){
                    const header_txt = (mode === "publish") ? loc.Publish_examyear :
                                       (mode === "undo_published") ? loc.Undo_publish_examyear :
                                       (mode === "lock") ? loc.Close_examyear :
                                       (mode === "undo_locked") ? loc.Undo_closure_examyear :
                                        null;
                    b_show_mod_message_html(loc.Select_examyear_first, header_txt);
                } else {
                    mod_MCREY_dict = deepcopy_dict(data_dict);
                    mod_MCREY_dict.mode = mode;
                    show_modal = true;
                };
            };
        };
        if (show_modal) {
            el_MCREY_loader.classList.add(cls_visible_hide);
// ---  set header text, input element and info box
            MCREY_SetMsgElements();
// ---  show modal
            $("#id_mod_create_examyear").modal({backdrop: true});
        };
    };  // MCREY_Open

//=========  MCREY_Save  ================  PR2020-10-01 PR2021-04-26
    function MCREY_Save(btn_clicked) {
        console.log(" -----  MCREY_save  ----", btn_clicked);
        console.log( "mod_MCREY_dict: ", mod_MCREY_dict);

        // mode = 'create, 'publish', 'lock', 'edit' (with el_input)
        const mode = mod_MCREY_dict.mode;
        //console.log( "mode: ", mode);

        if(!!permit_dict.permit_crud){
            let upload_changes = false;
            let upload_dict = {table: 'examyear', country_pk: mod_MCREY_dict.country_id};
            if(btn_clicked === "undo"){

        //console.log( "btn_clicked undo: ", btn_clicked);
                upload_dict.examyear_pk = mod_MCREY_dict.id;
                upload_dict.mapid = mod_MCREY_dict.mapid;
                if(mod_MCREY_dict.locked){
                    upload_dict.locked = false;
                    upload_changes = true;
                } else if(mod_MCREY_dict.published){
                    upload_dict.published = false;
                    upload_changes = true;
                } else if(!mod_MCREY_dict.is_addnew){
                    // delete exam year
                    // TODO open confirm modal when delete
                    upload_dict.mode = "delete";
                    upload_changes = true;
                }
            } else {
                if (mode === "create") {
                    upload_dict.mode = "create";
                    upload_dict.examyear_code = mod_MCREY_dict.examyear_code;
                } else if(mod_MCREY_dict.is_delete) {
                    // handled by mod confirm
                    //upload_dict.examyear_pk = mod_MCREY_dict.id;
                    //upload_dict.mapid = mod_MCREY_dict.mapid;
                    //upload_dict.mode = "delete";
                } else {
                    upload_dict.examyear_pk = mod_MCREY_dict.id;
                    upload_dict.mapid = mod_MCREY_dict.mapid;
                    upload_dict.mode = "update";
                    if(!mod_MCREY_dict.published){
                        upload_dict.published = true;
                    } else if(!mod_MCREY_dict.locked){
                        upload_dict.locked = true;
                    }
                }
                upload_changes = true
            };
            if(upload_changes){
                const url_str = urls.url_examyear_upload
                el_MCREY_loader.classList.remove(cls_visible_hide);
                UploadChanges(upload_dict, url_str);
                el_MCREY_btn_save.disabled = true;
            }
        }
    }  // MCREY_Save

//=========  MCREY_Input  ================  PR2021-08-30
    function MCREY_Input(el_input) {
        console.log(" -----  MCREY_Input  ----");
        if(el_input.value && Number(el_input.value)){
            mod_MCREY_dict.examyear_code = Number(el_input.value);
        };
        console.log( "mod_MCREY_dict: ", mod_MCREY_dict);
    };

//=========  MCREY_update_after_response  ================  PR2020-10-01 PR2021-06-20 PR2022-08-10
    function MCREY_update_after_response(response) {
        console.log(" -----  MCREY_update_after_response  ----");
        console.log( "mod_MCREY_dict: ", mod_MCREY_dict);
        console.log( "response: ", response);

/*
checked_examyear: {created: true, msg_html: 'Exam year 2023 has been created.'}
updated_examyear_rows: [{…}]
*/
        let msg_html_created = null;
        if ("checked_examyear" in response) {
            const checked_examyear_dict = response.checked_examyear;
            if (!isEmpty(checked_examyear_dict)){
                if ("created" in checked_examyear_dict) {
                    if ("msg_html" in checked_examyear_dict) {
                        msg_html_created = checked_examyear_dict.msg_html;
                    }
                }
            }
        };

        if ("updated_examyear_rows" in response) {

            const updated_examyear_rows = response.updated_examyear_rows
        console.log( "updated_examyear_rows: ", updated_examyear_rows);
            // {created: true, msg_html: "<div class='p-2 b
            if(updated_examyear_rows.length) {
                const tblName = "examyear";
                //const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                //RefreshDataMap(tblName, field_names, updated_examyear_rows, examyear_map);

                const updated_examyear_dict = updated_examyear_rows[0];

        console.log( "updated_examyear_rows: ", updated_examyear_rows);
                if(!isEmpty(updated_examyear_dict)){
                    console.log( "updated_examyear_dict: ", updated_examyear_dict);
                    //console.log( "updated_examyear_dict.error: ", updated_examyear_dict.error);

                    if ("error" in updated_examyear_dict){
                        const msg_list = updated_examyear_dict.error;
                        const border_class = "border_bg_invalid";
                        MCREY_SetMsgContainer(border_class, msg_list);
                        el_MCREY_btn_save.classList.add(cls_hide);;
                        el_MCREY_btn_cancel.innerText = loc.Close
                    } else if ("created" in updated_examyear_dict){
                        //const msg_list = updated_examyear_dict.msg_html;
                        //MCREY_SetMsgContainer("border_bg_valid", msg_list);

                        //el_MCREY_msg_container.innerHTML = msg_html_created;
                        MCREY_SetMsgContainer("border_bg_valid", [msg_html_created]);

                        el_MCREY_btn_save.classList.add(cls_hide);
                        el_MCREY_btn_cancel.innerText = loc.Close;

                        RefreshDataRows("examyear", examyear_rows, updated_examyear_rows, true, false);
                    } else {
                        $("#id_mod_create_examyear").modal("hide");
                        RefreshDataRows("examyear", examyear_rows, updated_examyear_rows, true, false); // is_update=true, skip_show_ok=false
                    };
                };
            };
        };
    }  // MCREY_update_after_response

//========= MCREY_get_next_examyear  ============= PR2020-10-04 PR2020-08-08
    function MCREY_get_next_examyear(){
        //console.log( "===== MCREY_get_next_examyear  ========= ");

        let max_examyear_int = 0, new_examyear_int = 0;

// ---  get highest examyear
        for (let i = 0, data_dict; data_dict = examyear_rows[i]; i++) {
            if(data_dict.examyear_code && data_dict.examyear_code > max_examyear_int) {
                max_examyear_int = data_dict.examyear_code;
            };
        };
        //console.log( "max_examyear_int", max_examyear_int);
        if (max_examyear_int){
            new_examyear_int = max_examyear_int + 1;
        } else {
            const today = new Date();
            const this_month_index = 1 + today.getMonth();
            const this_year = today.getFullYear()
            new_examyear_int = (this_month_index < 8) ? this_year : 1 + this_year;
        }
        return new_examyear_int;
    }; // MCREY_get_next_examyear

//========= MCREY_SetMsgElements  ============= PR2020-10-05 PR2021-04-24
    function MCREY_SetMsgElements(response){
        //console.log( "===== MCREY_SetMsgElements  ========= ");
        //console.log( "response", response);
        //console.log( "mod_MCREY_dict", mod_MCREY_dict);
        const mode = mod_MCREY_dict.mode;
        //console.log( "mode", mode);
        // mode = 'create, 'publish', 'lock', 'edit' (with el_input)

// ---  header text
        const header_part1 = (mode === "create") ? loc.Create_examyear_part1 :
                              (mode === "publish")  ? loc.Publish_examyear_part1 :
                              (["lock"].includes(mode))  ? loc.Close_examyear_part1 : null;
        const header_part2 = (mode === "create") ? loc.Create_examyear_part2 :
                              (mode === "publish")  ? loc.Publish_examyear_part2 :
                              (["lock"].includes(mode))  ? loc.Close_examyear_part2 : null;
        document.getElementById("id_MCREY_header").innerText = header_part1 + mod_MCREY_dict.examyear_code + header_part2;

// --- set input element
        el_MCREY_input_code.value = (mod_MCREY_dict.examyear_code) ? mod_MCREY_dict.examyear_code : null;

// set msg elements
        const msg_list = (mode === "create") ? loc.msg_info.create :
                              (mode === "publish")  ? loc.msg_info.publish :
                              (mode === "lock")  ? loc.msg_info.close : [];

        const is_error = (response && "msg_error" in response);
        const is_ok = (response && "msg_ok" in response);
        const border_class = (is_error) ? "border_bg_invalid" : (is_ok) ? "border_bg_valid" : "border_bg_message";

        MCREY_SetMsgContainer(border_class, msg_list) ;

        let err_save = false;

// ---  set text on msg_modified
        let modified_text = null;
        if (mode !== "create"){
            const modified_dateJS = parse_dateJS_from_dateISO(mod_MCREY_dict.modifiedat);
            const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
            const modified_by = (mod_MCREY_dict.modby_username) ? mod_MCREY_dict.modby_username : "-";
            modified_text = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by
        }
        document.getElementById("id_MCREY_msg_modified").innerText = modified_text;

// ---  set text on btn Save Cancel, hide btn save on error or after save
        const hide_btn_save = (is_ok || err_save);
        if (!hide_btn_save) { el_MCREY_btn_save.disabled = false };
        MCREY_SetBtnOkCancel(mode, hide_btn_save);

    }  // MCREY_SetMsgElements

//========= MCREY_SetBtnOkCancel ======== // PR2021-06-20
    function MCREY_SetBtnOkCancel(mode, hide_btn_save) {

// ---  btn_save_text
        const btn_save_text = (mode === "create") ? loc.Create_new_examyear :
                              (mode === "publish")  ? loc.Publish_examyear :
                              (mode === "lock")  ? loc.Close_examyear : null;
        el_MCREY_btn_save.innerText = btn_save_text;

// ---  show / hide btn save
        add_or_remove_class(el_MCREY_btn_save, cls_hide, hide_btn_save)

// ---  set text on btn cancel
        el_MCREY_btn_cancel.innerText = ((hide_btn_save) ? loc.Close: loc.Cancel);
        if(hide_btn_save){el_MCREY_btn_cancel.focus()}

    };  // MCREY_SetBtnOkCancel

//========= MCREY_SetMsgContainer ======== // PR2021-04-24
    function MCREY_SetMsgContainer(border_class, msg_list) {
        //console.log(" -----  MCREY_SetMsgContainer   ----")
        //console.log("msg_list", msg_list)

        // className removes all other classes from element
        el_MCREY_msg_container.className = border_class;
        el_MCREY_msg_container.classList.add("m-4", "p-2");

        let msg_html = "";
        for (let i = 0, msg; msg = msg_list[i]; i++) {
            msg_html += "<p class=\"py-1\">" + msg + "</p>"
        }
        el_MCREY_msg_container.innerHTML = msg_html;

    }  // MCREY_SetMsgContainer


//========= MCREY_headertext  ======== // PR2020-10-04
    function MCREY_headertext(mode) {
        //console.log(" -----  MCREY_headertext   ----")


    }  // MCREY_headertext

// +++++++++ END MOD EXAMYEAR ++++++++++++++++++++++++++++++++++++++++++++++++++++

// +++++++++ MOD EDIT EXAM YEAR ++++++++++++++++ PR2021-08-30
    function MODEY_Open(el_input){
        console.log(" -----  MODEY_Open   ----")
        console.log("permit_dict.permit_crud", permit_dict.permit_crud)

        if(!permit_dict.permit_crud){
            const msh_html = "<div class='p-2 border_bg_invalid'>" + loc.msg_info.nopermit[0] + "</div>";
            b_show_mod_message_html(msh_html, loc.Edit_examyear);
        } else {
            let pk_int = null, map_id = null;
            const fldName = get_attr_from_el(el_input, "data-field");
            const tblName = "examyear";

            // el_input is undefined when called by submenu buttons
            if(el_input){
                const tblRow = t_get_tablerow_selected(el_input);
                pk_int = get_attr_from_el_int(tblRow, "data-pk")
                map_id = tblRow.id;
            }

            const [index, data_dict, compare] = b_recursive_integer_lookup(examyear_rows, "id", pk_int);
            selected.examyear_pk = (!isEmpty(data_dict)) ? data_dict.id : null;

            b_clear_dict(mod_MCREY_dict);
            if(!isEmpty(data_dict)){mod_MCREY_dict = deepcopy_dict(data_dict)}

// ---  set header text, input element and info box
            MODEY_SetElements()

    // ---  show modal
            $("#id_mod_edit_examyear").modal({backdrop: true});
        }
    };  // MODEY_Open

//=========  MODEY_Save  ================  PR2020-10-01 PR2022-08-02
    function MODEY_Save() {
        //console.log(" -----  MODEY_Save  ----");
        //console.log( "mod_MCREY_dict: ", mod_MCREY_dict);

        if (permit_dict.permit_crud){
            const is_create = (mod_MCREY_dict.is_addnew);
            const upload_mode = (is_create) ? "create" : "update";

            let upload_dict = {table: 'examyear', mode: upload_mode}
            if(mod_MCREY_dict.id){upload_dict.examyear_pk = mod_MCREY_dict.id};
            if(mod_MCREY_dict.mapid){upload_dict.mapid = mod_MCREY_dict.mapid};

    // ---  put changed values of input elements in upload_dict
            let has_changed = false;
            if(el_MODEY_form_controls){
                const form_elements = el_MODEY_form_controls.querySelectorAll(".awp_input_select, .awp_input_checkbox");
                for (let i = 0, el; el = form_elements[i]; i++) {
                    const fldName = get_attr_from_el(el, "data-field");
                    const data_value = get_attr_from_el(el, "data-value");
                    const new_value = (data_value === "1");
                    const old_value = (mod_MCREY_dict[fldName]) ? mod_MCREY_dict[fldName] : false;
                    if (new_value !== old_value) {
                        upload_dict[fldName] = new_value;
                        has_changed = true;
                    };
                };
            };
            if (has_changed){
                UploadChanges(upload_dict, urls.url_examyear_upload);
            };
        };
// ---  hide modal
        $("#id_mod_edit_examyear").modal("hide");
    }  // MODEY_Save

//========= MODEY_InputChanged  ============= PR2021-09-03 PR2021-12-02
    function MODEY_InputChanged(el_input){
        //console.log( "===== MODEY_InputChanged  ========= ");

        if (el_input.tagName === "SELECT") {
            MODEY_select_toggle(el_input)
        } else {
            t_InputToggle(el_input);
        };

        el_MODEY_btn_save.disabled = false;
    };  // MODEY_InputChanged

//========= MODEY_select_toggle  ============= PR2021-12-02
    function MODEY_select_toggle(el_input){
        //console.log( "===== MODEY_select_toggle  ========= ");

        el_input.setAttribute("data-value", el_input.value);

        const value_bool = (el_input.value === "1");
        const fldName = get_attr_from_el_str(el_input, "data-field");
        const hide_msg = (["no_practexam", "no_centralexam"].includes(fldName)) ? value_bool : !value_bool;

        const el_msg = document.getElementById("id_MODEY_msg_" + fldName);
        add_or_remove_class(el_msg, cls_hide, hide_msg);
        if (fldName === "no_centralexam"){
            const el_no_third_period = document.getElementById("id_MODEY_no_thirdperiod");
            el_no_third_period.disabled = value_bool;
            // also set el_no_third_period = true when no central exam
            if(value_bool){
                el_no_third_period.value = "1";
                el_no_third_period.setAttribute("data-value", el_input.value);
            }
        }
    };  // MODEY_select_toggle

//========= MODEY_SetElements  ============= PR2021-08-30
    function MODEY_SetElements(){
        //console.log( "===== MODEY_SetElements  ========= ");

// ---  header text
        const el_MODEY_header = document.getElementById("id_MODEY_header");
        el_MODEY_header.innerText = loc.Examyear + " " + mod_MCREY_dict.examyear_code;

        //console.log( "mod_MCREY_dict: ", mod_MCREY_dict);
        if(el_MODEY_form_controls){
            const form_elements = el_MODEY_form_controls.querySelectorAll(".awp_input_select, .awp_input_checkbox")

            for (let i = 0, el; el = form_elements[i]; i++) {
                const field = get_attr_from_el(el, "data-field");
                const value_bool = mod_MCREY_dict[field];
                const value_bool_str = (value_bool) ? "1" : "0";

                el.setAttribute("data-value", value_bool_str);
                if(el.classList.contains("awp_input_checkbox")){
                el.setAttribute("data-value", value_bool_str);
                    add_or_remove_class(el.children[0], "tickmark_2_2", value_bool, "tickmark_1_1");
                } else {
                    el.value = value_bool_str;
                    // this one is in MODEY_select_toggle:  el.setAttribute("data-value", value_bool_str);
                    MODEY_select_toggle(el);
                };
            };
        };

// ---  set text on msg_modified
        let modified_text = null;
        if (mod_MCREY_dict.modifiedat){
            const modified_dateJS = parse_dateJS_from_dateISO(mod_MCREY_dict.modifiedat);
            const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
            const modified_by = (mod_MCREY_dict.modby_username) ? mod_MCREY_dict.modby_username : "-";
            modified_text = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by
        };
        document.getElementById("id_MODEY_modified").innerText = modified_text;

// ---  set text on btn Save Cancel, hide btn save on error  or after save
        el_MODEY_btn_save.disabled=true;
        //MCREY_SetBtnOkCancel(mode, hide_btn_save);

    }  // MODEY_SetElements
//////////////////////////////////////////////////

// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++

//=========  ModConfirmUndoOrDelete_Open  ================ PR2022-07-31
    function ModConfirmUndoOrDelete_Open(mode) {
        console.log(" -----  ModConfirmUndoOrDelete_Open   ----")
        // called by submenu btn delete examyear
        // modes are : undo_published,  undo_locked , delete
        console.log("selected", selected)
        console.log("permit_dict", permit_dict)

        if (permit_dict.requsr_role_admin && permit_dict.permit_crud){
// ---  create mod_dict
            mod_dict = {mode: mode};

            let msg_html = null;
            const no_examyear = (["undo_published", "undo_locked"].includes(mode) && !selected.examyear_pk);

            const header_txt = (mode === "undo_published") ? loc.Undo_publish_examyear :
                               (mode === "undo_locked") ? loc.Undo_closure_examyear :
                                loc.Delete_last_examyear;

            const btn_cancel_txt = (no_examyear) ? loc.Close : loc.Cancel;
            const btn_save_txt = (mode === "delete") ? loc.Yes_delete : loc.Yes_undo;

            if (no_examyear){
                msg_html = loc.Select_examyear_first;
            } else {

                let upload_dict = {};
    // --- check if last examyear exists, is locked or is published
                if (mode === "undo_published") {
                    mod_dict.examyear_pk = selected.examyear_pk;
                    upload_dict = {mode: "update", check: true, examyear_pk: selected.examyear_pk, published: false};
                } else if (mode === "undo_locked") {
                    mod_dict.examyear_pk = selected.examyear_pk;
                    upload_dict = {mode: "update", check: true, examyear_pk: selected.examyear_pk, locked: false};
                } else if (mode === "delete") {
                    upload_dict = {mode: "delete", check: true};
                };
                UploadChanges(upload_dict, urls.url_examyear_upload);
                // UploadChanges returns function ModConfirmDelete_checked
            };

            el_modconfirm_header.innerText = header_txt;
            add_or_remove_class(el_modconfirm_loader, cls_hide, no_examyear) ;
            el_modconfirm_msg_container.innerHTML = msg_html;

            el_modconfirm_btn_cancel.innerText = btn_cancel_txt;

            el_modconfirm_btn_save.innerText = btn_save_txt;
            el_modconfirm_btn_save.disabled = true;
            add_or_remove_class(el_modconfirm_btn_save, cls_hide, true);
            add_or_remove_class(el_modconfirm_btn_save, "btn-outline-danger", (mode === "delete"), "btn-primary");

    // set focus to cancel button
            setTimeout(function (){
                el_modconfirm_btn_cancel.focus();
            }, 500);
    // show modal
            $("#id_mod_confirm").modal({backdrop: true});
        };
    };  // ModConfirmUndoOrDelete_Open

//=========  ModConfirmUndoOrDelete_Checked  ================ PR2022-07-31
    function ModConfirmUndoOrDelete_Checked(checked_examyear) {
        console.log(" -----  ModConfirmUndoOrDelete_Checked   ----");
        console.log("checked_examyear", checked_examyear);

        if ("examyear_tobedeleted" in checked_examyear){
            const examyear_tobedeleted = checked_examyear.examyear_tobedeleted
            mod_dict.mapid = examyear_tobedeleted.mapid
        };

        const btn_cancel_txt = (checked_examyear.error) ? loc.Close : loc.No_cancel;

        el_modconfirm_loader.classList.add(cls_hide);
        el_modconfirm_msg_container.innerHTML = checked_examyear.msg_html;

        add_or_remove_class(el_modconfirm_btn_save, cls_hide, checked_examyear.error)
        el_modconfirm_btn_save.disabled = checked_examyear.error;

        el_modconfirm_btn_cancel.innerText = btn_cancel_txt;

    };  // ModConfirmUndoOrDelete_Checked

//=========  ModConfirmOpen  ================ PR2020-11-22 PR2021-06-29 PR2021-08-21 PR2022-07-31
    function ModConfirmOpen(mode) {
        console.log(" -----  ModConfirmOpen   ----")
        // called by submenu btn delete examyear and copyfrom_
        // mode is 'delete', 'delete_subjects_from_sxm', 'copy_scheme
        console.log("selected", selected)
        console.log("permit_dict", permit_dict)


        if(!!permit_dict.permit_userpage){
            const tblName = "examyear";
            const data_map = examyear_map;
            let dont_show_modal = false;

    // ---  get info from data_map
            let map_dict = {};
            if (mode === "copy_scheme"){
                 if (permit_dict.requsr_role_system){
                    map_dict = selected_copyto_examyear_dict;
                }
            } else {
                const map_id = tblName + "_" + selected.examyear_pk;
                map_dict = get_mapdict_from_datamap_by_id(examyear_map, map_id)
            };
            const has_selected_item = (!isEmpty(map_dict));

        console.log("has_selected_item", has_selected_item)
    // ---  create mod_dict
            mod_dict = {mode: mode};

            if(has_selected_item){
                if (mode === "copy_scheme"){
                    mod_dict.copyto_mapid = map_dict.mapid;
                    mod_dict.copyto_examyear_pk = map_dict.id;
                    mod_dict.copyto_country_id = map_dict.country_id;
                    mod_dict.copyto_examyear_code = map_dict.examyear_code;
                    mod_dict.copyto_country = map_dict.country;
                } else {
                    mod_dict.country_pk = map_dict.country_id;
                    mod_dict.examyear_pk = map_dict.id;
                    mod_dict.examyear_code = map_dict.examyear_code;
                    //mod_dict.mapid = map_id;
                };
            };

        console.log("mod_dict", mod_dict);
// ---  get header text
            let header_text = "";
            const is_NL = (loc.user_lang === "nl");
            if(mode === "delete"){
                header_text = loc.Delete_examyear;
            } else if (mode === "copy_scheme"){
                header_text = loc.Copy_subject_schemes;
            }

// ---  put text in modal form
            const item = (mode === "copy_scheme") ? loc.Subjectschemes_of_ey_willbe_copiedto_ey : loc.Examyear;

            let msg_list = [];
            const hide_save_btn = !has_selected_item;
            if(!has_selected_item){
                msg_list[0] = loc.No_examyer_selected;
            } else {
                if(mode === "delete"){
                    msg_list[0] = loc.Examyear + " '" + mod_dict.examyear_code + "'" + loc.will_be_deleted;
                } else if (mode === "copy_scheme"){
                    msg_list[0] = loc.Subjectschemes_of_ey_willbe_copiedto_ey + " '" + mod_dict.copyto_country +  " " + mod_dict.copyto_examyear_code + "'.";
                }
                msg_list[1] = loc.Do_you_want_to_continue;
            }
            if(!dont_show_modal){
                el_modconfirm_header.innerText = header_text;
                el_modconfirm_loader.classList.add(cls_hide)

                const msg_html = msg_list.join("<br>");
                el_modconfirm_msg_container.innerHTML = msg_html;

                const caption_save = (mode.includes("delete")) ? loc.Yes_delete : loc.OK;
                el_modconfirm_btn_save.innerText = caption_save;
                add_or_remove_class (el_modconfirm_btn_save, cls_hide, hide_save_btn);

                add_or_remove_class (el_modconfirm_btn_save, "btn-outline-danger", (mode === "delete"), "btn-primary");

        // set focus to cancel button
                setTimeout(function (){
                    el_modconfirm_btn_cancel.focus();
                }, 500);
    // show modal
                $("#id_mod_confirm").modal({backdrop: true});
            };  // if(!dont_show_modal)

        } ; // if(!!permit_dict.permit_crud)

    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2019-06-23 PR2021-06-15
    function ModConfirmSave() {
        console.log(" --- ModConfirmSave --- ");
        console.log("mod_dict: ", mod_dict);
        let close_modal = (!permit_dict.permit_crud)

        if(!!permit_dict.permit_crud){
            let tblRow = document.getElementById(mod_dict.mapid);

    // ---  when delete: make tblRow red, before uploading
            if (tblRow && mod_dict.mode === "delete"){
                ShowClassWithTimeout(tblRow, cls_error, 4000);
            }

            if(mod_dict.mode === "delete"){
    // show loader
                el_modconfirm_loader.classList.remove(cls_hide)
            }

    // ---  Upload Changes
            let upload_dict = {};
            if (mod_dict.mode === "delete"){
                upload_dict = {mode: mod_dict.mode};
                close_modal = true;
            } else if (mod_dict.mode === "undo_published"){
                upload_dict = {mode: 'update', examyear_pk: mod_dict.examyear_pk, published: false};
                close_modal = true;
            } else if (mod_dict.mode === "undo_locked"){
                upload_dict = {mode: 'update', examyear_pk: mod_dict.examyear_pk, locked: false}
                close_modal = true;
            } else if (mod_dict.mode === "copy_scheme"){
                upload_dict = {
                    mode: mod_dict.mode,
                    table: mod_dict.table,
                    mapid: mod_dict.mapid,
                    copyto_mapid: mod_dict.copyto_mapid,
                    copyto_examyear_pk: mod_dict.copyto_examyear_pk,
                    copyto_country_id: mod_dict.copyto_country_id,
                    copyto_country: mod_dict.copyto_country
                };
            };
            const url_str = (mod_dict.mode === "copy_scheme") ? urls.url_subjectscheme_copyfrom : urls.url_examyear_upload;

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
        el_modconfirm_loader.classList.add(cls_hide)
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
            let msg01_txt = "", msg02_txt = "",  msg03_txt = "";
            if ("msg_err" in response) {
                msg01_txt = get_dict_value(response, ["msg_err", "msg01"], "");
                el_modconfirm_msg_container.classList.add("border_bg_invalid");
            } else if ("msg_ok" in response){
                msg01_txt  = get_dict_value(response, ["msg_ok", "msg01"], "");
                msg02_txt = get_dict_value(response, ["msg_ok", "msg02"], "");
                msg03_txt = get_dict_value(response, ["msg_ok", "msg03"], "");
                el_modconfirm_msg_container.classList.add("border_bg_valid");
            }

            let msg_html = "";
            if (msg01_txt) {msg_html += "<p>" + msg01_txt + "</p>"};
            if (msg02_txt) {msg_html += "<p>" + msg02_txt + "</p>"};
            if (msg03_txt) {msg_html += "<p>" + msg03_txt + "</p>"};
            el_modconfirm_msg_container.innerHTML = msg_html;

            el_modconfirm_btn_cancel.innerText = loc.Close;
            el_modconfirm_btn_save.classList.add(cls_hide);
        } else {
        // hide mod_confirm when no message
            $("#id_mod_confirm").modal("hide");
        }
    }  // ModConfirmResponse

//###########################################################################
// +++++++++++++++++ REFRESH DATA ROWS ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataRows  ================
// PR2022-08-02
    function RefreshDataRows(tblName, data_rows, update_rows, is_update, skip_show_ok) {
        //console.log(" --- RefreshDataRows  ---");
        //console.log("    is_update", is_update);
        //console.log("    update_rows", update_rows);

        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length
        if (update_rows && update_rows.length ) {
            const field_setting = field_settings.examyear;
            for (let i = 0, update_dict; update_dict = update_rows[i]; i++) {
                RefreshDatarowItem(tblName, field_setting, data_rows, update_dict, skip_show_ok);
            }
        } else if (!is_update) {
            // empty the data_rows when update_rows is empty PR2021-01-13 debug forgot to empty data_rows
            // PR2021-03-13 debug. Don't empty de data_rows when is update. Returns [] when no changes made
           data_rows = [];
        }
    }  //  RefreshDataRows

//=========  RefreshDatarowItem  ================ PR2022-08-02
    function RefreshDatarowItem(tblName, field_setting, data_rows, update_dict, skip_show_ok) {
        console.log(" --- RefreshDatarowItem  ---");
        //console.log("tblName", tblName);
    console.log("update_dict", update_dict);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;
    console.log("field_names", field_names);

            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);

// ---  get list of hidden columns
            const col_hidden = b_copy_array_to_new_noduplicates(mod_MCOL_dict.cols_hidden);

// ---  get list of columns that are not updated because of errors
            const error_columns = (update_dict.err_fields) ? update_dict.err_fields : [];

// ++++ created ++++
            // PR2021-06-16 from https://stackoverflow.com/questions/586182/how-to-insert-an-item-into-an-array-at-a-specific-index-javascript
            //arr.splice(index, 0, item); will insert item into arr at the specified index
            // (deleting 0 items first, that is, it's just an insert).

            if(is_created){
    // ---  first remove key 'created' from update_dict
                delete update_dict.created;

    // --- lookup index where new row must be inserted in data_rows
                // PR2021-06-21 not necessary, new row has always pk higher than existing. Add at end of rows

    // ---  insert new item at end
                data_rows.push(update_dict)

    // ---  create row in table., insert in alphabetical order
                const new_tblRow = CreateTblRow(tblName, field_setting, update_dict)

                if(new_tblRow){
    // ---  scrollIntoView,
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
        console.log("    pk_int", pk_int);
        console.log("    data_dict", data_dict);

// ++++ deleted ++++
                if(is_deleted){
                    // delete row from data_rows. Splice returns array of deleted rows
                    const deleted_row_arr = data_rows.splice(datarow_index, 1)
                    const deleted_row_dict = deleted_row_arr[0];

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
        console.log("data_dict", data_dict);
                        let updated_columns = [];
                        // skip first column (is margin)
                        for (let i = 1, col_field; col_field = field_names[i]; i++) {
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
        console.log("tblRow", tblRow);
                // loop through cells of row
                                for (let i = 1, fldName, td; td = tblRow.cells[i]; i++) {
                                    const el = td.children[0];
                                    if (el){
        console.log("td", td);
                                        fldName = get_attr_from_el(el, "data-field")
        console.log("fldName", fldName);
                                        UpdateField(el, update_dict);

                // make field green when field name is in updated_columns
                                        if(updated_columns.includes(fldName)){
                                            ShowOkElement(el);
                                        };
                                    };
                                };  //  for (let i = 1, el_fldName
                            };  // if(tblRow)
                        }; // if(updated_columns.length)
                    };  //  if(!isEmpty(data_dict) && field_names){
                };  // if(is_deleted)
            };  // if(is_created)
        };  // if(!isEmpty(update_dict))
    };  // RefreshDatarowItem

//###########################################################################

//========= ResetFilterRows  ====================================
    function ResetFilterRows() {  // PR2019-10-26 PR2020-10-06 PR2022-07-31
       //console.log( "===== ResetFilterRows  ========= ");

        selected.examyear_pk = null;

// ---  deselect all highlighted rows
        t_td_selected_clear(tblBody_datatable);

    };  // function ResetFilterRows


// +++++++++++++++++ MODAL SELECT EXAMYEAR OR DEPARTMENT ++++++++++++++++++++
// functions are in table.js, except for MSED_Response

//=========  MSED_Response  ================ PR2021-04-25  PR2021-05-10 PR2021-09-25
    function MSED_Response(new_setting) {
        console.log( "===== MSED_Response ========= ");
        console.log( "new_setting", new_setting);

        if(new_setting.all_countries){
    // open modconfirm for Copy_subject_schemes PR2021-09-24
            // put selected examyear_pk in selected_copyto_examyear_dict
            selected_copyto_examyear_dict = get_mapdict_from_datamap_by_tblName_pk(examyear_map, "examyear", new_setting.copyto_examyear_pk);
            ModConfirmOpen("copy_scheme")
        } else {
    // ---  upload new selected_pk
            new_setting.page = setting_dict.sel_page;
    // also retrieve the tables that have been changed because of the change in school / dep
            const datalist_request = {
                    setting: new_setting,
                    examyear_rows: {get: true},
                    school_rows: {get: true},
                    department_rows: {get: true}
                };
            DatalistDownload(datalist_request);
        };
    }  // MSED_Response

//=========   OpenLogfile   ====================== PR2021-09-24
    function OpenLogfile(loc, log_list) {
        console.log(" ========== OpenLogfile examyears===========");

        if (!!log_list && log_list) {
            const today = new Date();
            const this_month_index = 1 + today.getMonth();
            const date_str = today.getFullYear() + "-" + this_month_index + "-" + today.getDate();
            let filename = "Log dd " + date_str + ".pdf";

            printPDFlogfile(log_list, filename )
        };
    }; //OpenLogfile


//========= get_permits  ======== // PR2021-04-24
    function get_permits(permit_list) {
        //console.log(" --- get_permits ---" )
        //console.log("permit_list: ", permit_list )
        for (let i = 0, action; action = permit_list[i]; i++) {
            permit_dict[action] = true;
        }
        //console.log("permit_dict: ", permit_dict )
    }  // get_permits

})  // document.addEventListener('DOMContentLoaded', function()