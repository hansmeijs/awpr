// PR2020-09-29 added
document.addEventListener('DOMContentLoaded', function() {
    "use strict";

// ---  get el_loader
    let el_loader = document.getElementById("id_loader");

// ---  get permits
    // permit dict gets value after downloading permit_list PR2021-03-27
    //  if user has no permit to view this page ( {% if no_access %} ): el_loader does not exist PR2020-10-02
    const may_view_page = (!!el_loader)
    let permit_dict = {};
    let setting_dict = {};
    let loc = {};  // locale_dict

    let usergroups = [];

    const cls_hide = "display_hide";
    const cls_hover = "tr_hover";
    const cls_visible_hide = "visibility_hide";
    const cls_selected = "tsa_tr_selected";

    const selected = {examyear_pk: null, btn: "btn_user_list"};

    let selected_department_pk = null;
    let selected_level_pk = null;
    let selected_sector_pk = null;
    let selected_subjecttype_pk = null;
    let selected_scheme_pk = null;
    let selected_package_pk = null;

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
    const url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    const url_settings_upload = get_attr_from_el(el_data, "data-url_settings_upload");
    const url_examyear_upload = get_attr_from_el(el_data, "data-url_examyear_upload");
    const url_school_upload = get_attr_from_el(el_data, "data-url_school_upload");

// --- get field_settings
    const field_settings = {
        //PR2020-06-02 dont use loc.Employee here, has no value yet. Use "Employee" here and loc in CreateTblHeader
        examyear: {
                    field_caption: ["", "Examyear", "Created_on", "Published", "Published_on", "Closed", "Closed_on"],
                    field_names: ["select", "examyear_code", "createdat", "published", "publishedat", "locked", "lockedat"],
                    filter_tags: ["select", "text", "text", "toggle", "text", "toggle", "text"],
                    field_width:  ["032", "120", "120", "120", "120", "120", "120"],
                    field_align: ["c", "l", "l", "c", "l", "c", "l"]},
        examyear_school: {
                    field_caption: ["", "Examyear", "Activated", "Activated_on", "Closed", "Closed_on"],
                    field_names: ["select", "examyear_code", "activated", "activatedat", "locked", "lockedat"],
                    filter_tags: ["select", "text",  "toggle", "text", "toggle", "text"],
                    field_width:  ["032", "120",  "120", "120", "120", "120"],
                    field_align: ["c", "l", "c", "l", "c", "l"]},

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

// NOT IN USE
// --- buttons in btn_container
/*
        const el_btn_container = document.getElementById("id_btn_container")
        if (may_view_page){
            const btns = el_btn_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                const data_btn = get_attr_from_el(btn,"data-btn")
                btn.addEventListener("click", function() {HandleBtnSelect(data_btn)}, false )
            };
        }
*/
// ---  MODAL EXAMYEAR
        const el_MEY_examyear = document.getElementById("id_MEY_examyear_code")
        const el_MEY_btn_delete = document.getElementById("id_MEY_btn_delete");
        const el_MEY_btn_save = document.getElementById("id_MEY_btn_save");
        const el_MEY_btn_cancel = document.getElementById("id_MEY_btn_cancel");

        if(el_MEY_btn_delete){
            el_MEY_btn_delete.addEventListener("click", function() {MEY_Save("undo")}, false );
        };
        if(el_MEY_btn_save){
            el_MEY_btn_save.addEventListener("click", function() {MEY_Save("save")}, false )
        };

// ---  MOD CONFIRM ------------------------------------
        let el_confirm_header = document.getElementById("id_modconfirm_header");
        let el_confirm_loader = document.getElementById("id_modconfirm_loader");
        let el_confirm_msg_container = document.getElementById("id_modconfirm_msg_container")
        let el_confirm_msg01 = document.getElementById("id_modconfirm_msg01")
        let el_confirm_msg02 = document.getElementById("id_modconfirm_msg02")
        let el_confirm_msg03 = document.getElementById("id_modconfirm_msg03")

        let el_confirm_btn_cancel = document.getElementById("id_modconfirm_btn_cancel");
        let el_confirm_btn_save = document.getElementById("id_modconfirm_btn_save");
        if(el_confirm_btn_save){
            el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()});
        };

// ---  set selected menu button active
    SetMenubuttonActive(document.getElementById("id_hdr_users"));
    if(may_view_page){
        // period also returns emplhour_list
        const datalist_request = {
                setting: {page: "page_examyear"},
                locale: {page: ["page_examyear"]},
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
                let must_create_submenu = false;
                let must_update_headerbar = false;
                let isloaded_loc = false, isloaded_settings = false, isloaded_permits = false;

                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                    isloaded_loc = true;
                    //mimp_loc = loc;
                };

                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict;
                    selected.btn = (setting_dict.sel_btn);
                    selected.examyear_pk = (setting_dict.sel_examyear_pk) ? setting_dict.sel_examyear_pk : null;
                    isloaded_settings = true;

                    UpdateSidebarExamyear(response.awp_messages);
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

        // call b_render_awp_messages also when there are no messages, to remove existing messages
                const awp_messages = (response.awp_messages) ? response.awp_messages : {};
                b_render_awp_messages(response.awp_messages);

                if ("examyear_rows" in response) {
                    const tblName = "examyear";
                    const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                    RefreshDataMap(tblName, field_names, response.examyear_rows, examyear_map)
                }
                if ("school_rows" in response) {

                console.log("response.school_rows", response.school_rows)
                    b_fill_datamap(school_map, response.school_rows)
                console.log("school_map", school_map)
                };
                if ("department_rows" in response) { b_fill_datamap(department_map, response.department_rows)};

                HandleBtnSelect(selected.btn, true)  // true = skip_upload
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
            el_submenu.innerHTML = null;
            if (permit_dict.requsr_role_school && permit_dict.requsr_same_school) {
                // may activate and lock own school (filter is in download create_examyear_rows)
                AddSubmenuButton(el_submenu, loc.Activate_examyear, function() {MEY_Open("activate")});
                AddSubmenuButton(el_submenu, loc.Close_examyear, function() {MEY_Open("close_school")});
            } else if (permit_dict.requsr_role_comm){
                // no permit to view this page
            } else if (permit_dict.requsr_role_insp){
                // view permit only
            } else if (permit_dict.requsr_role_admin || permit_dict.requsr_role_system){
                // may create, publish, lock exam year
                AddSubmenuButton(el_submenu, loc.Create_new_examyear, function() {MEY_Open("create")});
                AddSubmenuButton(el_submenu, loc.Publish_examyear, function() {MEY_Open("publish")});
                AddSubmenuButton(el_submenu, loc.Close_examyear, function() {MEY_Open("close_admin")});
                AddSubmenuButton(el_submenu, loc.Delete_examyear, function() {ModConfirmOpen("delete")});
            }

         el_submenu.classList.remove(cls_hide);
    };//function CreateSubmenu

//###########################################################################
// +++++++++++++++++ EVENT HANDLERS +++++++++++++++++++++++++++++++++++++++++

//=========  HandleBtnSelect  ================ PR2020-09-19
    function HandleBtnSelect(data_btn, skip_upload) {
        console.log( "===== HandleBtnSelect ========= ");
        selected.btn = data_btn
        if(!selected.btn){selected.btn = "btn_user_list"}

// ---  upload new selected.btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_examyear: {sel_btn: selected.btn}};
            UploadSettings (upload_dict, url_settings_upload);
        };

// ---  highlight selected button
        // NIU highlight_BtnSelect(document.getElementById("id_btn_container"), selected.btn)

// ---  show only the elements that are used in this tab
        //b_show_hide_selected_elements_byClass("tab_show", "tab_" + selected.btn);

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

        selected.examyear_pk = null;
        selected_department_pk = null;
        selected_level_pk = null;
        selected_sector_pk = null;
        selected_subjecttype_pk = null;
        selected_scheme_pk = null;
        selected_package_pk = null;

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        DeselectHighlightedRows(tr_clicked, cls_selected);
        tr_clicked.classList.add(cls_selected)

// ---  update selected.examyear_pk
        const row_id = tr_clicked.id
        if(row_id){
            const arr = row_id.split("_");  // rowid = mapid: "examyear_43"
            const tblName = arr[0];
            const map_dict = get_mapdict_from_datamap_by_id(examyear_map, row_id)

        console.log("map_dict", map_dict);
            if (tblName === "examyear") { selected.examyear_pk = map_dict.examyear_id } else
            if (tblName === "department") { selected_department_pk = map_dict.id } else
            if (tblName === "level") { selected_level_pk = map_dict.id } else
            if (tblName === "sector") { selected_sector_pk = map_dict.id } else
            if (tblName === "subjecttype") { selected_subjecttype_pk = map_dict.id } else
            if (tblName === "scheme") { selected_scheme_pk = map_dict.id } else
            if (tblName === "package") { selected_package_pk = map_dict.id };
        console.log("selected.examyear_pk", selected.examyear_pk);
        }
    }  // HandleTableRowClicked


//========= UpdateHeaderText  ================== PR2020-07-31
    function UpdateHeaderText(){
        console.log(" --- UpdateHeaderText ---" )
        let header_text = null;
        if(selected.btn === "examyear"){
            header_text = loc.Examyear;
        } else  if(selected.btn === "scheme"){
            header_text = loc.Subject_schemes;
        } else  if(selected.btn === "level"){
            header_text = loc.Levels;
        } else  if(selected.btn === "sector"){
            header_text = loc.SectorenProfielen;
        }
        document.getElementById("id_hdr_left").innerText = header_text;

    }   //  UpdateHeaderText


//========= UpdateSidebarExamyear  ================== PR2020-11-13
    function UpdateSidebarExamyear(awp_messages){
        //console.log(" --- UpdateSidebarExamyear ---" )
        //console.log("setting_dict", setting_dict )
        //console.log("permit_dict.requsr_examyear_text", permit_dict.requsr_examyear_text )
        // TODO code is not correct
        let examyer_txt = "";
        if (permit_dict.requsr_examyear_text){
           examyer_txt = loc.Examyear + " " + permit_dict.requsr_examyear_text
        } else {
            const examyear_str = (loc.Examyear) ? loc.Examyear.toLowerCase() : "-";
            examyer_txt = "<" + loc.There_is_no__ + examyear_str +  loc.__selected + ">"
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
                let el_msg_container = document.getElementById("id_mod_awpmessages")
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

        const tblName = (permit_dict.requsr_role <= 8) ? "examyear_school" : "examyear"

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
        console.log( "===== FillTblRows  === ");
        // display exyr_school when req_usr.role <= c.ROLE_008_SCHOOL:
        const tblName = (permit_dict.requsr_role <= 8) ? "examyear_school" : "examyear"
        const data_map = examyear_map;

// --- reset table
        tblBody_datatable.innerText = null
        if(data_map){
// --- loop through data_map
          for (const [map_id, map_dict] of data_map.entries()) {
                //console.log( "map_dict ", map_dict);
          // --- insert row at row_index
                const order_by = map_dict.examyear;
                const row_index = -1; // t_get_rowindex_by_sortby(tblBody_datatable, order_by)
                let tblRow = CreateTblRow(tblBody_datatable, tblName, map_id, map_dict, row_index)
                UpdateTblRow(tblRow, tblName, map_dict);
          };
        }  // if(!!data_map)

    }  // FillTblRows

//=========  CreateTblRow  ================ PR2020-06-09
    function CreateTblRow(tblBody, tblName, map_id, map_dict, row_index) {
        //console.log("=========  CreateTblRow =========", tblName);
        //console.log("map_dict", map_dict);
        let tblRow = null;

        const field_setting = field_settings[tblName]
        //console.log("field_setting", field_setting);
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
            tblRow.setAttribute("data-sortby", map_dict.examyear_int);

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

                    if (["published", "activated", "locked"].indexOf(field_name) > -1){
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
                } else if (["published", "activated", "locked"].indexOf(field_name) > -1){
                    const el_img = el_div.children[0];
                    const img_class = (fld_value) ? "tickmark_1_2" : "tickmark_0_0";
                    if(el_img) { el_img.className = img_class}

                } else if (["createdat", "publishedat", "activatedat", "lockedat"].indexOf(field_name) > -1){
                    let is_true = false, modat = null;
                    if (field_name === "createdat"){
                        modat = map_dict.createdat;
                        is_true = (!!modat);
                    } else if (field_name === "publishedat"){
                        is_true = map_dict.published;
                        modat = map_dict.publishedat;
                    } else if (field_name === "activatedat"){
                        is_true = map_dict.activated;
                        modat = map_dict.activatedat;
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
                } else {
                    el_div.innerText = map_dict[field_name];
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
                        MEY_update_after_response (response);
                    };
                    if ("updated_school_rows" in response) {
                        MEY_update_after_response (response);
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

// +++++++++ MOD EXAM YEAR ++++++++++++++++ PR2020-10-04
    function MEY_Open(mode, el_input){
        console.log(" -----  MEY_Open   ----")
        console.log("selected.examyear_pk", selected.examyear_pk)
        console.log("mode", mode)
        console.log("permit_dict", permit_dict)
        // mode = 'create, 'publish', 'activate', 'close_admin', 'close_school', 'edit' (with el_input)

        console.log("permit_dict", permit_dict)
        const is_addnew = (mode === "create");
        let has_permit = false, msg_no_permit = null;
        if (permit_dict.requsr_role_school && permit_dict.requsr_same_school) {
            has_permit = (mode === "activate" && !!permit_dict.permit_activate);
            if(!has_permit){msg_no_permit = loc.msg_info.activate_nopermit[0]}
        } else if (permit_dict.requsr_role_comm){
                // no permit to view this page
        } else if (permit_dict.requsr_role_insp){
                // view permit only
        } else if (permit_dict.requsr_role_admin || permit_dict.requsr_role_system){
            has_permit  =permit_dict.permit_crud;
        }
        console.log("has_permit", has_permit)
        console.log("msg_no_permit", msg_no_permit)
        if(msg_no_permit){
             b_show_mod_message(msg_no_permit)
        } else {

            //console.log("permit_dict", permit_dict)
            if(permit_dict.permit_crud){
                let selected_pk = null, map_id = null;
                const fldName = get_attr_from_el(el_input, "data-field");
                const tblName = "examyear";

            console.log("fldName", fldName)
                // el_input is undefined when called by submenu buttons
                if(el_input){
                    const tblRow = get_tablerow_selected(el_input);
                    selected_pk = get_attr_from_el(tblRow, "data-pk")
                    map_id = tblRow.id;
                } else if (!is_addnew) {
                    selected_pk = selected.examyear_pk;
                    map_id = (selected_pk) ? "examyear_" + selected_pk : null;
                }
                const map_dict = get_mapdict_from_datamap_by_id(examyear_map, map_id)
                mod_MEY_dict = {}
                if(!isEmpty(map_dict)){mod_MEY_dict = deepcopy_dict(map_dict)}
                mod_MEY_dict.mode = mode;
                mod_MEY_dict.is_addnew = is_addnew;
                if(is_addnew){
                    mod_MEY_dict.country_id = permit_dict.requsr_country_pk;
                    mod_MEY_dict.examyear_code = MEY_get_next_examyear()
                }

    // ---  set header text, input element and info box
                MEY_SetMsgElements()

        // ---  show modal
                $("#id_mod_examyear").modal({backdrop: true});
            }
        }
    };  // MEY_Open

//=========  MEY_Save  ================  PR2020-10-01 PR2021-04-26
    function MEY_Save(btn_clicked) {
        console.log(" -----  MEY_save  ----", btn_clicked);
        console.log( "mod_MEY_dict: ", mod_MEY_dict);

        // mode = 'create, 'publish', 'activate', 'close_admin', 'close_school', 'edit' (with el_input)
        const mode = mod_MEY_dict.mode;
        console.log( "mode: ", mode);

        if(!!permit_dict.permit_crud){
            let upload_changes = false;
            let upload_dict = {table: 'examyear', country_pk: mod_MEY_dict.country_id};
            if(btn_clicked === "undo"){

        console.log( "btn_clicked undo: ", btn_clicked);
                upload_dict.examyear_pk = mod_MEY_dict.examyear_id;
                upload_dict.mapid = mod_MEY_dict.mapid;
                if(mod_MEY_dict.locked){
                    upload_dict.locked = false;
                    upload_changes = true;
                } else if(mod_MEY_dict.published){
                    upload_dict.published = false;
                    upload_changes = true;
                } else if(!mod_MEY_dict.is_addnew){
                    // delete exam year
                    // TODO open confirm modal when delete
                    upload_dict.mode = "delete";
                    upload_changes = true;
                }
            } else {
                if (mode === "create") {
                    upload_dict.mode = "create";
                    upload_dict.examyear_code = mod_MEY_dict.examyear_code;
                } else if(mod_MEY_dict.is_delete) {
                    // handled by mod confirm
                    //upload_dict.examyear_pk = mod_MEY_dict.examyear_id;
                    //upload_dict.mapid = mod_MEY_dict.mapid;
                    //upload_dict.mode = "delete";
                } else if (mode === "activate") {
                    upload_dict.examyear_pk = mod_MEY_dict.examyear_id;
                    upload_dict.table = "school"
                    upload_dict.school_pk = mod_MEY_dict.school_id;
                    upload_dict.mode = "update";
                    upload_dict.activated = true;
                } else {
                    upload_dict.examyear_pk = mod_MEY_dict.examyear_id;
                    upload_dict.mapid = mod_MEY_dict.mapid;
                    upload_dict.mode = "update";
                    if(!mod_MEY_dict.published){
                        upload_dict.published = true;
                    } else if(!mod_MEY_dict.locked){
                        upload_dict.locked = true;
                    }
                }
                upload_changes = true
            };
            if(upload_changes){
                const url_str = (["activate", "close_school"].includes(mode)) ? url_school_upload : url_examyear_upload
                const el_MEY_loader =  document.getElementById("id_MEY_loader");
                if(el_MEY_loader){el_MEY_loader.classList.remove(cls_visible_hide)};
                UploadChanges(upload_dict, url_str);
            }
        }
    }  // MEY_Save

//=========  MEY_update_after_response  ================  PR2020-10-01 PR2021-06-20
    function MEY_update_after_response(response) {
        console.log(" -----  MEY_update_after_response  ----");
        console.log( "mod_MEY_dict: ", mod_MEY_dict);

        if ("updated_examyear_rows" in response) {
            const updated_examyear_rows = response.updated_examyear_rows
            if(updated_examyear_rows.length) {
                const tblName = "examyear";
                const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                RefreshDataMap(tblName, field_names, updated_examyear_rows, examyear_map);

                const updated_examyear_dict = updated_examyear_rows[0];
                if(!isEmpty(updated_examyear_dict)){
                    console.log( "updated_examyear_dict: ", updated_examyear_dict);
                    console.log( "updated_examyear_dict.error: ", updated_examyear_dict.error);

                    if ("error" in updated_examyear_dict){
                        const msg_list = updated_examyear_dict.error;
                        const border_class = "border_bg_invalid";
                        MEY_SetMsgContainer(border_class, msg_list);

                    } else if ("created" in updated_examyear_dict){
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

                    } else {
                        $("#id_mod_examyear").modal("hide");
                    }
                }
            }
        };

        if ("updated_school_rows" in response) {
            const updated_school_rows = response.updated_school_rows
            if(updated_school_rows.length) {
                const tblName = "examyear_school";
                const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                RefreshDataMap("school", field_names, updated_school_rows, school_map);

                const updated_school_dict = updated_school_rows[0];
                if(!isEmpty(updated_school_dict)){
                    console.log( "updated_school_dict: ", updated_school_dict);
                    if ("error" in updated_school_dict){
                        const err_dict = updated_school_dict.error;
                        if ("general" in err_dict){
                            const msg_list = err_dict.general;
                            const border_class = "border_bg_invalid";
                            MEY_SetMsgContainer(border_class, msg_list);
                            el_MEY_btn_save.classList.add(cls_hide);
                            el_MEY_btn_save.classList.add(cls_hide);
                            // ---  set text on btn Save Cancel, hide btn save on error  or after save
                            const hide_btn_save = true;
                            MEY_SetBtnOkCancel(mod_MEY_dict.mode, hide_btn_save);
                        }
                    } else {
                        $("#id_mod_examyear").modal("hide");
                    }
                }
            }
        };
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

//========= MEY_SetMsgElements  ============= PR2020-10-05 PR2021-04-24
    function MEY_SetMsgElements(response){
        console.log( "===== MEY_SetMsgElements  ========= ");
        console.log( "response", response);
        console.log( "mod_MEY_dict", mod_MEY_dict);
        const mode = mod_MEY_dict.mode;
        console.log( "mode", mode);
        // mode = 'create, 'publish', 'activate', 'close_admin', 'close_school', 'edit' (with el_input)

// ---  header text
        const header_part1 = (mode === "create") ? loc.Create_examyear_part1 :
                              (mode === "publish")  ? loc.Publish_examyear_part1 :
                              (mode === "activate")  ? loc.Activate_examyear_part1 :
                              (["close_admin", "close_school"].includes(mode))  ? loc.Close_examyear_part1 : null;
        const header_part2 = (mode === "create") ? loc.Create_examyear_part2 :
                              (mode === "publish")  ? loc.Publish_examyear_part2 :
                              (mode === "activate")  ? loc.Activate_examyear_part2 :
                              (["close_admin", "close_school"].includes(mode))  ? loc.Close_examyear_part2 : null;
        document.getElementById("id_MEY_header").innerText = header_part1 + mod_MEY_dict.examyear_code + header_part2;

// --- set input element
        el_MEY_examyear.value = (mod_MEY_dict.examyear_code) ? mod_MEY_dict.examyear_code : null;


// set msg elements
        const msg_list = (mode === "create") ? loc.msg_info.create :
                              (mode === "publish")  ? loc.msg_info.publish :
                              (mode === "activate")  ? loc.msg_info.activate :
                              (mode === "close_admin")  ? loc.msg_info.close :
                              (mode === "close_school")  ? loc.msg_info.close : [];

        const is_error = (response && "msg_error" in response);
        const is_ok = (response && "msg_ok" in response);
        const border_class = (is_error) ? "border_bg_invalid" : (is_ok) ? "border_bg_valid" : "border_bg_message";

        MEY_SetMsgContainer(border_class, msg_list) ;

        let err_save = false;

// ---  set text on msg_modified
        let modified_text = null;
        if (mode !== "create"){
            const modified_dateJS = parse_dateJS_from_dateISO(mod_MEY_dict.modifiedat);
            const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
            const modified_by = (mod_MEY_dict.modby_username) ? mod_MEY_dict.modby_username : "-";
            modified_text = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by
        }
        document.getElementById("id_MEY_msg_modified").innerText = modified_text;

// ---  set text on btn delete
        const btn_del_text = (mode === "publish")  ? loc.Delete_examyear :
                             (mode === "close_admin")  ? loc.Undo_publish_examyear :
                             (mode === "close_school")  ? loc.Undo_activate_examyear : null;
        el_MEY_btn_delete.innerText = btn_del_text;
        add_or_remove_class(el_MEY_btn_delete, cls_hide, !btn_del_text)

// ---  set text on btn Save Cancel, hide btn save on error  or after save
        const hide_btn_save = (is_ok || err_save);
        MEY_SetBtnOkCancel(mode, hide_btn_save);

    }  // MEY_SetMsgElements

//========= MEY_SetMsgContainer ======== // PR2021-06-20
    function MEY_SetBtnOkCancel(mode, hide_btn_save) {

// ---  btn_save_text
        const btn_save_text = (mode === "create") ? loc.Create_new_examyear :
                              (mode === "publish")  ? loc.Publish_examyear :
                              (mode === "activate")  ? loc.Activate_examyear :
                              (["close_admin", "close_school"].includes(mode))  ? loc.Close_examyear : null;
        el_MEY_btn_save.innerText = btn_save_text;

// ---  show / hide btn save
        add_or_remove_class(el_MEY_btn_save, cls_hide, hide_btn_save)

// ---  set text on btn cancel
        el_MEY_btn_cancel.innerText = ((hide_btn_save) ? loc.Close: loc.Cancel);
        if(hide_btn_save){el_MEY_btn_cancel.focus()}

    }

//========= MEY_SetMsgContainer ======== // PR2021-04-24
    function MEY_SetMsgContainer(border_class, msg_list) {
        console.log(" -----  MEY_SetMsgContainer   ----")
        console.log("msg_list", msg_list)

        const el_msg_container = document.getElementById("id_msg_container");

        // className removes all other classes from element
        el_msg_container.className = border_class;
        el_msg_container.classList.add("m-4", "p-2");

        let msg_html = "";
        for (let i = 0, msg; msg = msg_list[i]; i++) {
            msg_html += "<p class=\"py-1\">" + msg + "</p>"
        }
        el_msg_container.innerHTML = msg_html;

    }  // MEY_SetMsgContainer


//========= MEY_headertext  ======== // PR2020-10-04
    function MEY_headertext(mode) {
        //console.log(" -----  MEY_headertext   ----")


    }  // MEY_headertext

// +++++++++ END MOD EXAMYEAR ++++++++++++++++++++++++++++++++++++++++++++++++++++


// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2020-11-22 PR2021-06-29
    function ModConfirmOpen(mode) {
        console.log(" -----  ModConfirmOpen   ----")
        // called by el_MEY_btn_delete and submenu btn delete examyear
        // mode is always 'delete' (for now?)
        console.log("selected", selected)

        if(!!permit_dict.permit_crud){
            const tblName = "examyear";
            const data_map = examyear_map;
            let dont_show_modal = false;

    // ---  get info from data_map
            const map_id =  tblName + "_" + selected.examyear_pk;
            const map_dict = get_mapdict_from_datamap_by_id(examyear_map, map_id)
            const has_selected_item = (!isEmpty(map_dict));

            console.log("data_map", data_map)
            console.log("map_id", map_id)
            console.log("map_dict", map_dict)
            // mode
            /*
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
            */
    // ---  create mod_dict
            mod_dict = {mode: mode};

            if(has_selected_item){
                mod_dict.country_pk = map_dict.country_id;
                mod_dict.examyear_pk = map_dict.examyear_id;
                mod_dict.examyear_code = map_dict.examyear_code;
                mod_dict.mapid = map_id;
            };

        console.log("mod_dict", mod_dict);
// ---  get header text
            let header_text = "";
            const is_NL = (loc.user_lang === "nl");
            if(mode === "delete"){
                header_text =  loc.Delete_examyear ;
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
                    msg_list[0] = loc.Examyear + " '" + mod_dict.examyear_code + "'" + loc.will_be_deleted
                    msg_list[1] = loc.Do_you_want_to_continue;

                }
            }

            if(!dont_show_modal){
                el_confirm_header.innerText = header_text;
                el_confirm_loader.classList.add(cls_visible_hide)

                const msg_html = msg_list.join("<br>");
                el_confirm_msg_container.innerHTML = msg_html;

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

        }  // if(!!permit_dict.permit_crud)
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
            let upload_dict = {mode: mod_dict.mode,
                               mapid: mod_dict.mapid,
                               examyear_pk: mod_dict.examyear_pk};

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
            let msg_html = "", msg01_text = "", msg02_text = "",  msg03_text = "";
            if ("msg_err" in response) {
                msg01_text = get_dict_value(response, ["msg_err", "msg01"], "");
                el_confirm_msg_container.classList.add("border_bg_invalid");
            } else if ("msg_ok" in response){
                msg01_text  = get_dict_value(response, ["msg_ok", "msg01"], "");
                msg02_text = get_dict_value(response, ["msg_ok", "msg02"], "");
                msg03_text = get_dict_value(response, ["msg_ok", "msg03"], "");
                msg_html = [msg01_text, msg02_text, msg03_text].join("<br>");
                el_confirm_msg_container.classList.add("border_bg_valid");
            }
            el_confirm_msg_container.innerHTML = msg_html;
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
                const row_index = 0 //  t_get_rowindex_by_sortby(tblBody_datatable, order_by)
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

        selected.examyear_pk = null;

// ---  deselect all highlighted rows in tblBody
        DeselectHighlightedTblbody(tblBody_datatable, cls_selected)

    }  // function ResetFilterRows


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL SELECT EXAMYEAR OR DEPARTMENT ++++++++++++++++++++
// functions are in table.js, except for MSED_Response

//=========  MSED_Response  ================ PR2021-04-25  PR2021-05-10
    function MSED_Response(new_setting) {
        //console.log( "===== MSED_Response ========= ");

// ---  upload new selected_pk
// also retrieve the tables that have been changed because of the change in school / dep
        const datalist_request = {
                setting: new_setting,
                examyear_rows: {get: true},
                school_rows: {get: true},
                department_rows: {get: true}
            };
        DatalistDownload(datalist_request);

    }  // MSED_Response

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
            setting: {page: "page_examyear", sel_examyear_pk: mod_dict.examyear_pk},
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
        code_value = (map_dict.examyear_code) ? map_dict.examyear_code.toString() : "---"
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
            mod_dict = {base_id: permit_dict.requsr_schoolbase_pk, table: tblName};

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
        let new_setting = {page_examyear: {mode: "get"}};
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
                // TODO cahnge or delete
                if(tblName === "order") {
                    selected.order_pk = get_attr_from_el_int(tblRow, "data-pk");
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

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
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