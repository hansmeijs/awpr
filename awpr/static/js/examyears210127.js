// PR2020-09-29 added
document.addEventListener('DOMContentLoaded', function() {
    "use strict";

    // <PERMIT> PR220-10-02
    //  - can view page: only 'role_school', 'role_insp', 'role_admin', 'role_system'
    //  - can add/delete/edit only 'role_admin', 'role_system' plus 'perm_edit'
    //  roles are:   'role_student', 'role_teacher', 'role_school', 'role_insp', 'role_admin', 'role_system'
    //  permits are: 'perm_read', 'perm_edit', 'perm_auth1', 'perm_auth2', 'perm_docs', 'perm_admin', 'perm_system'

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

    let user_list = [];

    let examyear_map = new Map();
    let school_map = new Map();
    let department_map = new Map();

    let filter_dict = {};
    let filter_mod_employee = false;

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    const url_datalist_download = get_attr_from_el(el_data, "data-datalist_download_url");
    const url_settings_upload = get_attr_from_el(el_data, "data-settings_upload_url");
    const url_examyear_upload = get_attr_from_el(el_data, "data-examyear_upload_url");
    const url_examyears = get_attr_from_el(el_data, "data-examyears_url");

// --- get field_settings
    const field_settings = {
        examyear: { //PR2020-06-02 dont use loc.Employee here, has no value yet. Use "Employee" here and loc in CreateTblHeader
                    field_caption: ["", "Examyear", "Created_on", "Published", "Published_on", "Closed", "Closed_on"],
                    field_names: ["select", "examyear_int", "createdat", "published", "publishedat", "locked", "lockedat"],
                    filter_tags: ["select", "text", "text", "toggle", "text", "toggle", "text"],
                    field_width:  ["032", "120", "120", "120", "120", "120", "120"],
                    field_align: ["c", "l", "l", "c", "l", "c", "l"]}
        };
    const tblHead_datatable = document.getElementById("id_tblHead_datatable");
    const tblBody_datatable = document.getElementById("id_tblBody_datatable");

// ---  get elements
    let el_loader = document.getElementById("id_loader");

// ---  check if user has permit to view this page. If not: el_loader does not exist PR2020-10-02
    const has_view_permit = (!!el_loader);
    // has_edit_permit gets value after downloading settings
    let has_edit_permit = false;
    let has_permit_select_school = false;

// === EVENT HANDLERS ===
// === reset filter when ckicked on Escape button ===
        document.addEventListener("keydown", function (event) {
             if (event.key === "Escape") { ResetFilterRows()}
        });

// --- header bar elements
        const el_hdrbar_examyear = document.getElementById("id_hdrbar_examyear");
            el_hdrbar_examyear.addEventListener("click", function() {ModSelectExamyear_Open()}, false )
        const el_hdrbar_school = document.getElementById("id_hdrbar_school")
            el_hdrbar_school.addEventListener("click", function() {ModSelSchOrDep_Open("school")}, false )
        const el_hdrbar_department = document.getElementById("id_hdrbar_department")
            el_hdrbar_department.addEventListener("click", function() {ModSelSchOrDep_Open("department")}, false )

// ---  MOD SELECT EXAM YEAR ------------------------------------
        let el_MSEY_tblBody_select = document.getElementById("id_MSEY_tblBody_select");
// ---  MOD SELECT SCHOOL OR DEPARTMENT ------------------------------------
        let el_ModSelSchOrDep_tblBody_select = document.getElementById("id_MSESD_tblBody_select");

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
        const el_MEY_examyear = document.getElementById("id_MEY_examyear_int")
        const el_MEY_btn_delete = document.getElementById("id_MEY_btn_delete");
        if(has_view_permit){el_MEY_btn_delete.addEventListener("click", function() {MEY_Save("undo")}, false )}
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
                locale: {page: ["examyear"]},
                examyear_rows: {get: true},
                school_rows: {get: true},
                department_rows: {get: true}
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
                    setting_dict = response.setting_dict;

                    // <PERMIT> PR220-10-02
                    //  - can view page: only 'role_school', 'role_insp', 'role_admin', 'role_system'
                    //  - can add/delete/edit only 'role_admin', 'role_system' plus 'perm_edit'
                    has_edit_permit = (setting_dict.requsr_role_admin && setting_dict.requsr_perm_edit) ||
                                      (setting_dict.requsr_role_system && setting_dict.requsr_perm_edit);
                    // <PERMIT> PR2020-10-27
                    // - every user may change examyear and department
                    // -- only insp, admin and system may change school
                    has_permit_select_school = (setting_dict.requsr_role_insp ||
                                                setting_dict.requsr_role_admin ||
                                                setting_dict.requsr_role_system);
                    selected_btn = (setting_dict.sel_btn)

                    b_UpdateHeaderbar(loc, setting_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);

                    UpdateSidebarExamyear(response.awp_messages);
                };
                // both 'loc' and 'setting_dict' are needed for CreateSubmenu
                if (!isEmpty(loc) && !isEmpty(setting_dict)) {CreateSubmenu()};

                if ("examyear_rows" in response) {
                    const tblName = "examyear";
                    const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                    RefreshDataMap(tblName, field_names, response.examyear_rows, examyear_map)
                }
                if ("school_rows" in response)  { b_fill_datamap(school_map, response.school_rows)};
                if ("department_rows" in response) { b_fill_datamap(department_map, response.department_rows)};


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
            el_submenu.innerHTML = null;
            const is_NL = (setting_dict.user_lang === "nl");
            const examyear_lc = (loc.Examyear) ? loc.Examyear.toLowerCase() : "";
            const create_lc = (loc.Create) ? loc.Create.toLowerCase() : "";
            const publish_lc = (loc.Publish) ? loc.Publish.toLowerCase() : "";
            const close_lc = (loc.Close_NL_afsluiten) ? loc.Close_NL_afsluiten.toLowerCase() : "";
            const delete_lc = (loc.Delete) ? loc.Delete.toLowerCase() : "";

            const create_caption = (is_NL) ? loc.Examyear + " " + create_lc : loc.Create + " " + examyear_lc;
            const publish_caption = (is_NL) ? loc.Examyear + " " + publish_lc : loc.Publish + " " + examyear_lc;
            const close_caption = (is_NL) ? loc.Examyear + " " + close_lc : loc.Close_NL_afsluiten + " " + examyear_lc;
            const delete_caption = (is_NL) ? loc.Examyear + " " + delete_lc : loc.Delete + " " + examyear_lc;

            AddSubmenuButton(el_submenu, create_caption, function() {MEY_Open("create")});
            AddSubmenuButton(el_submenu, publish_caption, function() {MEY_Open("publish")},  ["ml-2"]);
            AddSubmenuButton(el_submenu, close_caption, function() {MEY_Open("close")},  ["ml-2"]);
            AddSubmenuButton(el_submenu, delete_caption, function() {ModConfirmOpen()}, ["ml-2"]);
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
        console.log("=== HandleTableRowClicked");
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
        const row_id = tr_clicked.id
        if(row_id){
            const arr = row_id.split("_");  // rowid = mapid: "examyear_43"
            const tblName = arr[0];
            const map_dict = get_mapdict_from_datamap_by_id(examyear_map, row_id)

        console.log("map_dict", map_dict);
            if (tblName === "examyear") { selected_examyear_pk = map_dict.examyear_id } else
            if (tblName === "department") { selected_department_pk = map_dict.id } else
            if (tblName === "level") { selected_level_pk = map_dict.id } else
            if (tblName === "sector") { selected_sector_pk = map_dict.id } else
            if (tblName === "subjecttype") { selected_subjecttype_pk = map_dict.id } else
            if (tblName === "scheme") { selected_scheme_pk = map_dict.id } else
            if (tblName === "package") { selected_package_pk = map_dict.id };
        console.log("selected_examyear_pk", selected_examyear_pk);
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


//========= UpdateSidebarExamyear  ================== PR2020-11-13
    function UpdateSidebarExamyear(awp_messages){
        console.log("########### --- UpdateSidebarExamyear ---" )
        console.log("setting_dict", setting_dict )
        console.log("setting_dict.requsr_examyear_text", setting_dict.requsr_examyear_text )
        let examyer_txt = "";
        if (setting_dict.requsr_examyear_text){
           examyer_txt = loc.Examyear + " " + setting_dict.requsr_examyear_text
        } else {
            const examyear_str = (loc.Examyear) ? loc.Examyear.toLowerCase() : "-";
            examyer_txt = "<" + loc.No__ + examyear_str +  loc.__selected + ">"
        }
        //if(el_SBR_examyear) { el_SBR_examyear.value = examyer_txt};
        //if(el_hdrbar_examyear) { el_hdrbar_examyear.innerText = examyer_txt};

// update message 'diff_exyr'
    // check if message 'diff_exyr' exists in awp_messages.
        let msg_dict_info = null, msg_dict_class = null;
        if (awp_messages && awp_messages.length){
            for (let i = 0, msg_dict; msg_dict = awp_messages[i]; i++) {
                if(msg_dict.id === "id_diff_exyr"){
                    msg_dict_info = msg_dict.info;
                    msg_dict_class = msg_dict.class;
                    break;
                }
            }
        }
    // check if el_msg 'id_diff_exyr' exists.
        let el_msg = document.getElementById("id_diff_exyr")
        if(!msg_dict_info){
            if (el_msg) {el_msg.parentNode.removeChild(el_msg)};


       /*
            // Adding msg is not working
        } else {

            if (!el_msg){
                let el_msg_container = document.getElementById("id_awpmsg_container")
                const el_msg = document.createElement("div");
                    el_msg.id = "id_diff_exyr"
                    const el_btn = document.createElement("button");
                        el_btn.classList.add("close")
                        el_btn.setAttribute("data-dismiss", "alert")
                        el_btn.setAttribute("aria-label", "Close")
                        const el_span = document.createElement("span");
                            el_span.setAttribute("aria-hidden", "true")
                            el_span.innerText = "&times"
                        el_btn.appendChild(el_span);
                    el_msg.appendChild(el_btn);
                    el_msg.innerText = "msg_dict_info"
                el_msg_container.appendChild(el_msg);
            } else {
                el_msg.innerText = msg_dict_info
                el_msg.classList.add(msg_dict_class)
            }
        */
        }

    }   //  UpdateSidebarExamyear



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
            tblRow.id = map_id;
// --- add data attributes to tblRow
            tblRow.setAttribute("data-pk", map_dict.examyear_id);
            tblRow.setAttribute("data-ppk", map_dict.country_id);
            tblRow.setAttribute("data-table", tblName);
            tblRow.setAttribute("data-orderby", map_dict.examyear_int);

            //console.log("tblRow", tblRow);
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
                if (j){  // skip first column (margin to select without opening mod)
                    el_td.addEventListener("click", function() {MEY_Open("edit", el_td)}, false)
                    el_td.classList.add("pointer_show");
                    add_hover(el_td);

                    if (["published", "locked"].indexOf(field_name) > -1){
                        let el_div = document.createElement("div");
                            //el_div.className = "tickmark_0_0"
                            el_td.appendChild(el_div);
                    }
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
        //console.log("map_dict", map_dict);
        if(el_div){
            const field_name = get_attr_from_el(el_div, "data-field");
            const fld_value = map_dict[field_name];
            if(field_name){
                if (field_name === "select") {
                    // TODO add select multiple users option PR2020-08-18
                } else if (["examyear_int"].indexOf(field_name) > -1){
                    el_div.innerText = map_dict[field_name];

                } else if (["published", "locked"].indexOf(field_name) > -1){
                    const el_img = el_div.children[0];
                    const img_class = (fld_value) ? "tickmark_1_2" : "tickmark_0_0";
                    if(el_img) { el_img.className = img_class}

                } else if (["createdat", "publishedat", "lockedat"].indexOf(field_name) > -1){
                    let is_true = false, modat = null;
                    if (field_name === "createdat"){
                        modat = map_dict.createdat;
                        is_true = (!!modat);
                    } else if (field_name === "publishedat"){
                        is_true = map_dict.published;
                        modat = map_dict.publishedat;
                    } else   if (field_name === "lockedat"){
                        is_true = map_dict.locked;
                        modat = map_dict.lockedat;
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
        console.log("selected_examyear_pk", selected_examyear_pk)
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
        console.log("selected_pk", selected_pk)
        console.log("map_id", map_id)
            const map_dict = get_mapdict_from_datamap_by_id(examyear_map, map_id)
        console.log("map_dict", map_dict)

            const is_addnew = (isEmpty(map_dict));
            mod_MEY_dict = {is_addnew: is_addnew}
            if(is_addnew){
                mod_MEY_dict.is_addnew = true;
                mod_MEY_dict.country_id = setting_dict.requsr_country_pk;

                mod_MEY_dict.examyear_int = MEY_get_next_examyear()
                mod_MEY_dict.published = false;
                mod_MEY_dict.locked = false;
            } else {
                mod_MEY_dict.examyear_id = map_dict.examyear_id
                mod_MEY_dict.country_id = map_dict.country_id
                mod_MEY_dict.mapid = map_dict.mapid

                mod_MEY_dict.examyear_int = map_dict.examyear_int
                mod_MEY_dict.published = map_dict.published
                mod_MEY_dict.locked = map_dict.locked;

                mod_MEY_dict.createdat = map_dict.createdat
                mod_MEY_dict.publishedat = map_dict.publishedat
                mod_MEY_dict.lockedat = map_dict.lockedat;

                mod_MEY_dict.modby_username = map_dict.modby_username
                mod_MEY_dict.modifiedat = map_dict.modifiedat
            }
            /*
            mod_MEY_dict = {mapid: "examyear_1", id: 1, country_id: 1, examyear: 2019, createdat: "2020-10-04T04:00:00Z",
                            is_addnew: false, locked: false, lockedat: null, published: false, publishedat: null,
                            modby_username: null, modifiedat: "2019-03-03T20:27:37.051Z"
            */

// ---  set header text, input element and info box
            MEY_SetMsgElements()

    // ---  show modal
            $("#id_mod_examyear").modal({backdrop: true});
        }
    };  // MEY_Open

//=========  MEY_Save  ================  PR2020-10-01
    function MEY_Save(btn_clicked) {
        console.log(" -----  MEY_save  ----", btn_clicked);
        console.log( "mod_MEY_dict: ", mod_MEY_dict);

        if(has_edit_permit){
            let upload_changes = false;
            let upload_dict = {id: {table: 'examyear', country_pk: mod_MEY_dict.country_id} }
            if(btn_clicked === "undo"){
                upload_dict.id.examyear_pk = mod_MEY_dict.examyear_id;
                upload_dict.id.mapid = mod_MEY_dict.mapid;
                if(mod_MEY_dict.locked){
                    upload_dict.locked = {value: false, update: true};
                    upload_changes = true;
            console.log( "upload_dict", upload_dict);
                } else if(mod_MEY_dict.published){
                    upload_dict.published = {value: false, update: true};
                    upload_changes = true;
                } else if(!mod_MEY_dict.is_addnew){
                    // delete exam year
                    upload_dict.id.mode = "delete";
                    upload_changes = true;
                }
            } else {
                if(mod_MEY_dict.is_addnew) {
                    upload_dict.id.mode = "create";
                    upload_dict.examyear = {value: mod_MEY_dict.examyear_int, update: true}
                } else if(is_delete) {
                    upload_dict.id.examyear_pk = mod_MEY_dict.examyear_id;
                    upload_dict.id.mapid = mod_MEY_dict.mapid;
                    upload_dict.id.mode = "delete";
                } else {
                    upload_dict.id.examyear_pk = mod_MEY_dict.examyear_id;
                    upload_dict.id.mapid = mod_MEY_dict.mapid;
                    upload_dict.id.mode = "update";
                    if(!mod_MEY_dict.published){
                        upload_dict.published = {value: true, update: true}
                    } else if(!mod_MEY_dict.locked){
                        upload_dict.locked = {value: true, update: true}
                    }
                }
                upload_changes = true
            };
            if(upload_changes){
                const el_MEY_loader =  document.getElementById("id_MEY_loader");
                if(el_MEY_loader){el_MEY_loader.classList.remove(cls_visible_hide)};
                UploadChanges(upload_dict, url_examyear_upload);
            }
        }
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
        console.log( "===== MEY_get_next_examyear  ========= ");

        let max_examyear_int = 0, new_examyear_int = 0;
        for (const [map_id, item_dict] of examyear_map.entries()) {
        console.log( "item_dict", item_dict);
            if(item_dict.examyear_code && item_dict.examyear_code > max_examyear_int) {
                max_examyear_int = item_dict.examyear_code;
            }
        }
        console.log( "max_examyear_int", max_examyear_int);
        if (max_examyear_int){
            new_examyear_int = max_examyear_int + 1;
        } else {
            const today = new Date();
            const this_month_index = 1 + today.getMonth();
            const this_year = today.getFullYear()
            new_examyear_int = (this_month_index < 8) ? this_year : 1 + this_year;
        }
        return new_examyear_int;
    }; // MEY_get_next_examyear

//========= MEY_SetMsgElements  ============= PR2020-10-05
    function MEY_SetMsgElements(response){
        console.log( "===== MEY_SetMsgElements  ========= ");
        console.log( "mod_MEY_dict", mod_MEY_dict);

        let status = (mod_MEY_dict.locked) ? "locked" :
             (mod_MEY_dict.published) ? "published" :
             (mod_MEY_dict.is_addnew) ? "addnew" : "created";
        console.log( "status", status);

// --- set input element
        el_MEY_examyear.value = mod_MEY_dict.examyear_int;

// reset msg elements
        const msg_list = (status === "addnew") ? loc.msg_info.create :
                         (status === "created")  ? loc.msg_info.publish :
                         (status === "published")  ? loc.msg_info.close :
                         (status === "locked")  ? loc.msg_info.locked : [];

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
        const btn_save_text = (status === "addnew") ? loc.Create_examyear :
                                (status === "created")  ? loc.Publish_examyear :
                            (status === "published")  ? loc.Close_examyear : null;
        let header_text = (btn_save_text) ? btn_save_text : ""
        if (mod_MEY_dict.examyear_int) { header_text += " " + mod_MEY_dict.examyear_int.toString()};
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
        el_MEY_btn_cancel.innerText = ((is_ok || err_save) ? loc.Close: loc.Cancel);
        if(is_ok || err_save){el_MUA_btn_cancel.focus()}
// ---  set text on btn save
        el_MEY_btn_save.innerText = btn_save_text;
        add_or_remove_class(el_MEY_btn_save, cls_hide, !btn_save_text)
// ---  set text on btn delete
        const btn_del_text = (status === "created")  ? loc.Delete_examyear :
                             (status === "published")  ? loc.Undo_publish_examyear :
                             (status === "locked")  ? loc.Undo_closure_examyear : null;
        el_MEY_btn_delete.innerText = btn_del_text;
        add_or_remove_class(el_MEY_btn_delete, cls_hide, !btn_del_text)

    }  // MEY_SetMsgElements

//========= MEY_headertext  ======== // PR2020-10-04
    function MEY_headertext(mode) {
        //console.log(" -----  MEY_headertext   ----")


    }  // MEY_headertext

// +++++++++ END MOD EXAMYEAR ++++++++++++++++++++++++++++++++++++++++++++++++++++


// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2020-11-22
    function ModConfirmOpen() {
        console.log(" -----  ModConfirmOpen   ----")
        // called by el_MEY_btn_delete and submenu btn delete examyear

        if(has_edit_permit){
            const tblName = "examyear";
            const data_map = examyear_map;
            let dont_show_modal = false;

    // ---  get info from data_map
            const map_id =  tblName + "_" + selected_examyear_pk;
            const map_dict = get_mapdict_from_datamap_by_id(examyear_map, map_id)
            const has_selected_item = (!isEmpty(map_dict));

            console.log("data_map", data_map)
            console.log("map_id", map_id)
            console.log("map_dict", map_dict)

            let mode = null;
            if(has_selected_item){
                if(map_dict.locked) {
                    mode = "locked"
                } else if(map_dict.published) {
                    mode = "published"
                } else if(map_dict.examyear_id) {
                    mode = "created"
                }
            }

    // ---  create mod_dict
            mod_dict = {mode: "delete"};

            if(has_selected_item){
                mod_dict.pk = map_dict.id;
                mod_dict.ppk = map_dict.country_id;
                mod_dict.examyear = map_dict.examyear;
                mod_dict.mapid = map_id;
            };

        console.log("mod_dict", mod_dict);
// ---  get header text
            let header_text = "";
            const is_NL = (loc.user_lang === "nl");
            if(mode === "delete"){
                header_text =  (is_NL) ? loc.Examyear + " " + loc.Delete.toLowerCase() :
                                         loc.Delete + " " + + examyear_str;
            }
// ---  put text in modal form
            const item = (tblName === "examyear") ? loc.Examyear : "";

            let msg_list = [];
            const hide_save_btn = !has_selected_item;
            if(!has_selected_item){
                msg_list[0] = loc.No_examyer_selected;
            } else {
                const username = (map_dict.username) ? map_dict.username  : "-";
                if(mode === "delete"){
                    msg_list[0] = loc.Examyear + " '" + mod_dict.examyear + "'" + loc.will_be_deleted
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
            el_confirm_btn_cancel.innerText = loc.Close;
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
        //console.log(" --- RefreshDataMap  ---");
        //console.log("tblName", tblName);
        if (data_rows) {
            const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
            for (let i = 0, update_dict; update_dict = data_rows[i]; i++) {
                RefreshDatamapItem(tblName, field_names, update_dict, data_map);
            }
        }
    }  //  RefreshDataMap

//=========  RefreshDatamapItem  ================ PR2020-08-16 PR2020-09-30
    function RefreshDatamapItem(tblName, field_names, update_dict, data_map) {
        //console.log(" --- RefreshDatamapItem  ---");
        //console.log("update_dict", update_dict);

        //console.log("data_map", data_map);
        //console.log("data_map.size before: " + data_map.size);


        if(!isEmpty(update_dict)){
// ---  update or add update_dict in examyear_map
            let updated_columns = [];
    // get existing map_item
            const map_id = update_dict.mapid;
            let tblRow = document.getElementById(map_id);

            const is_deleted = get_dict_value(update_dict, ["deleted"], false)
            const is_created = get_dict_value(update_dict, ["created"], false)

        //console.log("is_created", is_created);
        //console.log("map_id", map_id);
// ++++ created ++++
            if(is_created){
    // ---  insert new item
                data_map.set(map_id, update_dict);
                updated_columns.push("created")
        //console.log("updated_columns", updated_columns);
    // ---  create row in table., insert in alphabetical order
                //const order_by = (update_dict.examyear) ? update_dict.examyear: 0;
                const row_index = 0 //  t_get_rowindex_by_orderby(tblBody_datatable, order_by)
                tblRow = CreateTblRow(tblBody_datatable, tblName, map_id, update_dict, row_index)
        //console.log("tblRow", tblRow);
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

        //console.log("data_map.size after: " + data_map.size);
        //console.log("data_map", data_map);
    }  // RefreshDatamapItem

//========= ResetFilterRows  ====================================
    function ResetFilterRows() {  // PR2019-10-26 PR2020-10-06
       //console.log( "===== ResetFilterRows  ========= ");

        selected_examyear_pk = null;

// ---  deselect all highlighted rows in tblBody
        DeselectHighlightedTblbody(tblBody_datatable, cls_selected)

    }  // function ResetFilterRows


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL SELECT EXAMYEAR ++++++++++++++++++++
//=========  ModSelectExamyear_Open  ================ PR2020-10-27
    function ModSelectExamyear_Open() {
        //console.log( "===== ModSelectExamyear_Open ========= ");

        //PR2020-10-28 debug: modal gives 'NaN' and 'undefined' when  loc not back from server yet
        if (!isEmpty(loc)) {
            mod_dict = {examyear_pk: setting_dict.sel_examyear_pk, table: "examyear"};
    // ---  fill select table
            ModSelectExamyear_FillSelectTable(0);  // 0 = selected_pk
    // ---  show modal
            $("#id_mod_select_examyear").modal({backdrop: true});
            }
    }  // ModSelectExamyear_Open

//=========  ModSelectExamyear_Save  ================ PR2020-10-28
    function ModSelectExamyear_Save() {
        console.log("===  ModSelectExamyear_Save =========");
        console.log("mod_dict", mod_dict);
// selected_pk: {sel_examyear_pk: 23, sel_schoolbase_pk: 15, sel_depbase_pk: 1}

// ---  upload new setting
        const datalist_request = {
            setting: {page_examyear: {mode: "get"}, sel_examyear_pk: mod_dict.examyear_pk},
            examyear_rows: {get: true}
        };
        DatalistDownload(datalist_request);

// hide modal
        $("#id_mod_select_examyear").modal("hide");

    }  // ModSelectExamyear_Save

//=========  ModSelectExamyear_SelectItem  ================ PR2020-10-28
    function ModSelectExamyear_SelectItem(tblRow) {
        //console.log( "===== ModSelectExamyear_SelectItem ========= ");
        //console.log( tblRow);
        // all data attributes are now in tblRow, not in el_select = tblRow.cells[0].children[0];
// ---  get clicked tablerow
        if(tblRow) {
// ---  deselect all highlighted rows
            DeselectHighlightedRows(tblRow, cls_selected)
// ---  highlight clicked row
            tblRow.classList.add(cls_selected)
// ---  get pk from id of select_tblRow
            let data_pk = get_attr_from_el(tblRow, "data-pk", 0)
            mod_dict.examyear_pk = (Number(data_pk)) ? Number(data_pk) : 0

            ModSelectExamyear_Save()
        }
    }  // ModSelectExamyear_SelectItem

//=========  ModSelectExamyear_FillSelectTable  ================ PR2020-08-21
    function ModSelectExamyear_FillSelectTable(selected_pk) {
        console.log( "===== ModSelectExamyear_FillSelectTable ========= ");
        console.log( "selected_pk", selected_pk);
        const tblBody_select = el_MSEY_tblBody_select;
        tblBody_select.innerText = null;

        let row_count = 0;
// --- loop through data_map
        const data_map = examyear_map;
        if(data_map){
            for (const [map_id, map_dict] of data_map.entries()) {
                ModSelectExamyear_FillSelectRow(map_dict, tblBody_select, selected_pk);
                row_count += 1;
            };
        }  // if(!!data_map)

        if(!row_count){
            let tblRow = tblBody_select.insertRow(-1);
            let td = tblRow.insertCell(-1);
            td.innerText = loc.No_exam_years;

        } else if(row_count === 1){
            let tblRow = tblBody_select.rows[0]
            if(tblRow) {
// ---  highlight first row
                tblRow.classList.add(cls_selected)
            }
        }
    }  // ModSelectExamyear_FillSelectTable

//=========  ModSelectExamyear_FillSelectRow  ================ PR2020-10-27
    function ModSelectExamyear_FillSelectRow(map_dict, tblBody_select, selected_pk) {
        //console.log( "===== ModSelectExamyear_FillSelectRow ========= ");
        //console.log( "map_dict: ", map_dict);

//--- loop through data_map
        let pk_int = null, code_value = null, is_selected_pk = false;
        pk_int = map_dict.examyear_id;
        code_value = (map_dict.examyear_int) ? map_dict.examyear_int.toString() : "---"
        is_selected_pk = (selected_pk != null && pk_int === selected_pk)
// ---  insert tblRow  //index -1 results in that the new row will be inserted at the last position.
        let tblRow = tblBody_select.insertRow(-1);
        tblRow.setAttribute("data-pk", pk_int);
        //tblRow.setAttribute("data-ppk", ppk_int);
        tblRow.setAttribute("data-value", code_value);
// ---  add EventListener to tblRow
        tblRow.addEventListener("click", function() {ModSelectExamyear_SelectItem(tblRow)}, false )
// ---  add hover to tblRow
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
    }  // ModSelectExamyear_FillSelectRow
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL SELECT SCHOOL OR DEPARTMENT ++++++++++++++++++++
//=========  ModSelSchOrDep_Open  ================ PR2020-10-27 PR2020-11-17
    function ModSelSchOrDep_Open(tblName) {
        //console.log( "===== ModSelSchOrDep_Open ========= ");
        //PR2020-10-28 debug: modal gives 'NaN' and 'undefined' when  loc not back from server yet
        if (!isEmpty(loc)) {
            mod_dict = {base_id: setting_dict.requsr_schoolbase_pk, table: tblName};

// ---  fill select table
            ModSelSchOrDep_FillSelectTable(tblName, 0);  // 0 = selected_pk
// ---  show modal
            $("#id_mod_select_school_or_dep").modal({backdrop: true});
            }
    }  // ModSelSchOrDep_Open

//=========  ModSelSchOrDep_Save  ================ PR2020-10-28
    function ModSelSchOrDep_Save(tblName) {
        //console.log("===  ModSelSchOrDep_Save =========");
        //console.log("mod_dict", mod_dict);

// ---  upload new setting
        let new_setting = {page_examyear: {mode: "get"}};
        if (tblName === "school") {
            new_setting.requsr_schoolbase_pk = mod_dict.base_id;
        } else {
            new_setting.requsr_depbase_pk = mod_dict.base_id;
        }
        const datalist_request = {setting: new_setting};
        DatalistDownload(datalist_request);

// hide modal
        $("#id_mod_select_school_or_dep").modal("hide");

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
        document.getElementById("id_MSESD_header_text").innerText = header_text;

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

//========= UpdateHeaderbar  ================== PR2020-11-14 PR2020-12-02
    function UpdateHeaderbar(){
        console.log(" --- UpdateHeaderbar ---" )

        let examyer_txt = "";
        if (setting_dict.requsr_examyear_text){
           examyer_txt = loc.Examyear + " " + setting_dict.requsr_examyear_text
        } else {
            const examyear_str = (loc.Examyear) ? loc.Examyear.toLowerCase() : "-";
            examyer_txt = "<" + loc.No__ + examyear_str +  loc.__selected + ">"
        }
        if(el_hdrbar_examyear) { el_hdrbar_examyear.innerText = examyer_txt};

        console.log("examyer_txt", examyer_txt )
        const may_select_school = (setting_dict.requsr_role_insp || setting_dict.requsr_role_admin || setting_dict.requsr_role_system);
        const class_select_school = (may_select_school) ? "awp_navbaritem_may_select" : "awp_navbar_item";
        let schoolname_txt = null;
        if (!setting_dict.requsr_schoolbase_pk){
            if (may_select_school) {
                schoolname_txt = " <" + loc.Select_school + ">";
            } else {
                schoolname_txt = " <" + loc.No_school_selected + ">";
            }
        } else {
            schoolname_txt = setting_dict.requsr_schoolbase_code;
            if (!setting_dict.sel_examyear_pk) {
                schoolname_txt += " <" + loc.No_examyear_selected + ">"
            } else {
                if (!setting_dict.requsr_school_pk){
                    schoolname_txt += " <" + loc.School_notfound_thisexamyear + ">"
                } else {
                    schoolname_txt += " " + setting_dict.requsr_school_name
                }
            }
        }
        el_hdrbar_school.innerText = schoolname_txt;
    }  // UpdateHeaderbar

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@




})  // document.addEventListener('DOMContentLoaded', function()