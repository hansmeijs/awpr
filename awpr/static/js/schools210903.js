// PR2020-09-29 added

let selected_btn = "btn_school";
let setting_dict = {};
let permit_dict = {};
let loc = {};  // locale_dict
let urls = {};

let selected_period = {};

const selected = {
    school_pk: null,
    school_dict: {}
}


document.addEventListener('DOMContentLoaded', function() {
    "use strict";

    let el_loader = document.getElementById("id_loader");

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
    let selected_btn = "btn_school";

    let selected_period = {};
    let setting_dict = {};
    let permit_dict = {};

    let mod_dict = {};
    let mod_MSCH_dict = {};

    let examyear_map = new Map();
    let department_map = new Map();

    let school_map = new Map();
    let school_rows = [];

    let filter_dict = {};

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    urls.url_settings_upload = get_attr_from_el(el_data, "data-url_settings_upload");
    urls.url_school_upload = get_attr_from_el(el_data, "data-url_school_upload");
    //urls.url_school_import = get_attr_from_el(el_data, "data-school_import_url");
    urls.url_school_awpupload = get_attr_from_el(el_data, "data-school_awpupload_url");

    let columns_hidden = {};

// --- get field_settings
    const field_settings = {
        school: {field_caption: ["", "Code", "Article", "Name", "Short_name", "Departments", "Day_Evening_LEXschool",  "Other_language",  "Not_on_DUOorderlist_2lines",  "Activated",  "Locked"],
                 field_names: ["select", "sb_code", "article", "name", "abbrev", "depbases", "dayevelex", "otherlang", "no_order", "activated", "locked"],
                 filter_tags: ["select", "text", "text",  "text", "text",  "text", "text", "text", "toggle", "toggle", "toggle"],
                 field_width:  ["020", "075", "075", "360", "180", "120","120", "090","100", "100", "100"],
                 field_align: ["c", "l", "l", "l","l", "l", "l", "l", "c", "c", "c"]}
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

// ---  MSSS MOD SELECT SCHOOL / SUBJECT / STUDENT ------------------------------
        const el_MSSSS_input = document.getElementById("id_MSSSS_input");
        const el_MSSSS_tblBody = document.getElementById("id_MSSSS_tbody_select");
        const el_MSSSS_btn_save = document.getElementById("id_MSSSS_btn_save");
        if (el_MSSSS_input){
            el_MSSSS_input.addEventListener("keyup", function(event){
                setTimeout(function() {t_MSSSS_InputKeyup(el_MSSSS_input)}, 50)});
        }
        if (el_MSSSS_btn_save){
            el_MSSSS_btn_save.addEventListener("click", function() {t_MSSSS_Save(el_MSSSS_input, MSSSS_Response)}, false );
        }

// ---  MOD SELECT EXAM YEAR ------------------------------------
        const el_SBR_school = document.getElementById("id_SBR_school")
        const el_SBR_department = document.getElementById("id_SBR_department")
        if (el_SBR_school){
            el_SBR_school.addEventListener("click", function() {ModSelSchOrDep_Open()}, false )
            add_hover(el_SBR_school);
        }
        if (el_SBR_department){
            el_SBR_department.addEventListener("click", function() {ModSelect_Open("department")}, false )
        }

// ---  MOD SELECT SCHOOL ------------------------------------
        let el_ModSelSch_tblBody_select = document.getElementById("id_MSED_tblBody_select");

// ---  MODAL SCHOOL
        const el_MSCH_code = document.getElementById("id_MSCH_code")
        const el_MSCH_abbrev = document.getElementById("id_MSCH_abbrev")
        const el_MSCH_article = document.getElementById("id_MSCH_article")
        const el_MSCH_name = document.getElementById("id_MSCH_name")
        const el_MSCH_tbody_select = document.getElementById("id_MSCH_tbody_select")

        const el_MSCH_btn_delete = document.getElementById("id_MSCH_btn_delete");
        const el_MSCH_btn_save = document.getElementById("id_MSCH_btn_save");
        if(el_MSCH_btn_delete){el_MSCH_btn_delete.addEventListener("click", function() {MSCH_Save("delete")}, false )};
        if(el_MSCH_btn_save){el_MSCH_btn_save.addEventListener("click", function() {MSCH_Save("save")}, false );};

        const el_MSCH_div_form_controls = document.getElementById("id_MSCH_form_controls")
        if(el_MSCH_div_form_controls){
            const form_elements = el_MSCH_div_form_controls.querySelectorAll(".form-control")
            for (let i = 0, el; el = form_elements[i]; i++) {
                if(el.tagName === "INPUT"){
                    el.addEventListener("keyup", function() {MSCH_InputKeyup(el)}, false )
                } else if(el.tagName === "SELECT"){
                    el.addEventListener("change", function() {MSCH_InputSelect(el)}, false )
                } else if(el.tagName === "DIV"){
                    el.addEventListener("click", function() {MSCH_InputToggle(el)}, false )
                };
            };
        };
        const el_MSCH_defaultrole_container = document.getElementById("id_MSCH_defaultrole_container");
        const el_MSCH_select_defaultrole = document.getElementById("id_MSCH_defaultrole");
        const el_MSCH_select_otherlang = document.getElementById("id_MSCH_otherlang");
        const el_MSCH_no_order = document.getElementById("id_MSCH_no_order");



// ---  MODAL UPLOAD DATA - MIMP
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
        let el_confirm_header = document.getElementById("id_modconfirm_header");
        let el_confirm_loader = document.getElementById("id_modconfirm_loader");
        let el_confirm_msg_container = document.getElementById("id_modconfirm_msg_container")
        let el_confirm_btn_cancel = document.getElementById("id_modconfirm_btn_cancel");
        let el_confirm_btn_save = document.getElementById("id_modconfirm_btn_save");
        if (el_confirm_btn_save){el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()}, false)};

// ---  MOD UPLOAD AWP-upload FILE ------------------------------------
        const el_ModUploadAwp_filedialog = document.getElementById("id_ModUploadAwp_filedialog");
        const el_ModUploadAwp_btn_save = document.getElementById("id_ModUploadAwp_btn_save");
        if (el_ModUploadAwp_btn_save){el_ModUploadAwp_btn_save.addEventListener("click", function() {ModUploadAwp_Save()}, false)};

    if(may_view_page){
// ---  set selected menu button active
        //SetMenubuttonActive(document.getElementById("id_hdr_school"));

        const datalist_request = {
                setting: {page: "page_school"},
                locale: {page: ["page_school", "upload"]},
                examyear_rows: {get: true},
                department_rows: {get: true},
                school_rows: {get: true}
            };

        DatalistDownload(datalist_request, "DOMContentLoaded");
    }

//######################################################################################################
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

                let must_create_submenu = false, must_update_headerbar = false;

                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                    must_create_submenu = true;
                };
                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict
                    selected_btn = (setting_dict.sel_btn)
                    must_update_headerbar = true;
                };
                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    // get_permits must come before CreateSubmenu and FiLLTbl
                    b_get_permits_from_permitlist(permit_dict);
                    set_columns_hidden();
                    must_update_headerbar = true;
                }

                if ("usergroup_list" in response) {
                    usergroups = response.usergroup_list;
                };

                if(must_create_submenu){
                    CreateSubmenu();
                };
                if(must_update_headerbar){
                    b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);
                };
                if ("schoolsetting_dict" in response) {
                    i_UpdateSchoolsettingsImport(response.schoolsetting_dict);
                };
                if ("examyear_rows" in response) {
                    b_fill_datamap(examyear_map, response.examyear_rows);
                };

                if ("department_rows" in response) {
                    const tblName = "department";
                    const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                    RefreshDataMap(tblName, field_names, response.department_rows, department_map)
                    }
                if ("school_rows" in response) {
                    school_rows = response.school_rows;
                    //const tblName = "school";
                    //const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                    //RefreshDataMap(tblName, field_names, response.school_rows, school_map)
                }

                HandleBtnSelect(selected_btn, true)  // true = skip_upload
            },
            error: function (xhr, msg) {
// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                console.log(msg + '\n' + xhr.responseText);
            }
        });
    }  // function DatalistDownload

//=========  CreateSubmenu  ===  PR2020-07-31 PR2021-06-20
    function CreateSubmenu() {
        //console.log("===  CreateSubmenu == ");
        //console.log("permit_dict:", permit_dict);

        let el_submenu = document.getElementById("id_submenu")
        if(el_submenu){
            if (permit_dict.permit_crud){
                AddSubmenuButton(el_submenu, loc.Add_school, function() {MSCH_Open()});
                AddSubmenuButton(el_submenu, loc.Delete_school, function() {ModConfirmOpen("delete")});
            };
            if (permit_dict.permit_upload_awpfile){
                AddSubmenuButton(el_submenu, loc.Upload_awpdata, function() {ModUploadAwp_open()}, null, "id_submenu_importawp");
            };
            const hide_submenu =  (!permit_dict.permit_crud && !permit_dict.permit_upload_awpfile);
            add_or_remove_class(el_submenu, cls_hide, hide_submenu);
        };
    };//function CreateSubmenu

//###########################################################################
// +++++++++++++++++ EVENT HANDLERS +++++++++++++++++++++++++++++++++++++++++
//=========  HandleBtnSelect  ================ PR2020-09-19
    function HandleBtnSelect(data_btn, skip_upload) {
        //console.log( "===== HandleBtnSelect ========= ", data_btn);
        selected_btn = data_btn
        if(!selected_btn){selected_btn = "btn_school"}

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_school: {sel_btn: selected_btn}};
            UploadSettings (upload_dict, urls.url_settings_upload);
        };

// ---  highlight selected button
        highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  show only the elements that are used in this tab
        //b_show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

// ---  fill datatable
        FillTblRows();

    }  // HandleBtnSelect

//=========  HandleTableRowClicked  ================ PR2020-08-03
    function HandleTableRowClicked(tr_clicked) {
        console.log("=== HandleTableRowClicked");
        console.log( "school_rows: ", school_rows);

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        DeselectHighlightedRows(tr_clicked, cls_selected);
        tr_clicked.classList.add(cls_selected)
        const pk_int = get_attr_from_el_int(tr_clicked, "data-pk");
        console.log( "pk_int: ", pk_int, typeof pk_int);

// ---  update selected_pk
        const [index, found_dict, compare] = b_recursive_integer_lookup(school_rows, "id", pk_int);
        selected.school_dict = (found_dict) ?  found_dict : {};
        selected.school_pk = (selected.school_dict) ?  selected.school_dict.id : null;

        console.log( "selected.school_dict: ", selected.school_dict, typeof selected.school_dict);
        console.log( "selected.school_pk: ", selected.school_pk, typeof selected.school_pk);

    }  // HandleTableRowClicked

//========= FillTblRows  ====================================
    function FillTblRows() {
        console.log( "===== FillTblRows  === ");

        const tblName = "school" //  tblName = get_tblName_from_selectedBtn()
        const field_setting = field_settings[tblName]
        const data_rows = school_rows;

// --- show columns
        set_columns_hidden();

// --- get data_map
        const data_map = get_datamap_from_tblName(tblName);
        //console.log( "data_map", data_map);

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

// --- create table header
        CreateTblHeader(field_setting);

// --- loop through data_rows
        if(data_rows && data_rows.length){
            for (let i = 0, map_dict; map_dict = data_rows[i]; i++) {
                const map_id = map_dict.mapid;
                let tblRow = CreateTblRow(tblName, field_setting, map_id, map_dict);
          };
        }  // if(!!data_map)
    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-07-31 PR2021-05-10
    function CreateTblHeader(field_setting) {
        //console.log("===========  CreateTblHeader ======== ");

        const column_count = field_setting.field_names.length;

// +++  insert header and filter row ++++++++++++++++++++++++++++++++
        let tblRow_header = tblHead_datatable.insertRow (-1);
        let tblRow_filter = tblHead_datatable.insertRow (-1);

    // --- loop through columns
        for (let j = 0; j < column_count; j++) {
            const field_name = field_setting.field_names[j];

            const key = field_setting.field_caption[j];
            const field_caption = (loc[key]) ? loc[key] : key;

            const filter_tag = field_setting.filter_tags[j];
            const class_width = "tw_" + field_setting.field_width[j] ;
            const class_align = "ta_" + field_setting.field_align[j];

// ++++++++++ insert columns in header row +++++++++++++++
        // --- add th to tblRow_header
            let th_header = document.createElement("th");
        // --- add div to th, margin not working with th
                const el_header = document.createElement("div");
        // --- add innerText to el_div
                el_header.innerText = field_caption;
        // --- add width, text_align
                th_header.classList.add(class_width, class_align);
                el_header.classList.add(class_width, class_align);
                th_header.appendChild(el_header)
            tblRow_header.appendChild(th_header);

// ++++++++++ create filter row +++++++++++++++
    // --- add th to tblRow_filter.
            const th_filter = document.createElement("th");

    // --- create element with tag from field_tags
            const el_tag = (filter_tag === "text") ? "input" : "div";
            const el_filter = document.createElement(el_tag);

    // --- add data-field Attribute.
                el_filter.setAttribute("data-field", field_name);
                el_filter.setAttribute("data-filtertag", filter_tag);

    // --- add EventListener to el_filter
                if (filter_tag === "text") {
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
                //el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");
            th_filter.appendChild(el_filter)
            tblRow_filter.appendChild(th_filter);
        }  // for (let j = 0; j < column_count; j++)
    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09 PR2021-06-21
    function CreateTblRow(tblName, field_setting, map_id, map_dict) {
        //console.log("=========  CreateTblRow =========", tblName);
        //console.log("map_dict", map_dict);

        const field_names = field_setting.field_names;
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;

// ---  lookup index where this row must be inserted
        const ob1 = (map_dict.sb_code) ? map_dict.sb_code : "";
        // NIU:  const ob2 = (map_dict.firstname) ? map_dict.firstname : "";
        // NIU:  const ob3 = (map_dict.firstname) ? map_dict.firstname : "";

        const row_index = b_recursive_tblRow_lookup(tblBody_datatable, ob1, "", "", setting_dict.user_lang);

// --- insert tblRow into tblBody at row_index
        let tblRow = tblBody_datatable.insertRow(row_index);
        tblRow.id = map_id

// --- add data attributes to tblRow
        tblRow.setAttribute("data-pk", map_dict.id);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);
        // NIU: tblRow.setAttribute("data-ob2", ob2);
        // NIU: tblRow.setAttribute("data-ob3", ---);

// --- add EventListener to tblRow
        tblRow.addEventListener("click", function() {HandleTableRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
        for (let j = 0; j < column_count; j++) {
            const field_name = field_names[j];

            const field_tag = "div";
            const class_width = "tw_" + field_width[j];
            const class_align = "ta_" + field_align[j];

    // --- insert td element,
            let td = tblRow.insertCell(-1);

    // --- create element with tag from field_tags
            const el = document.createElement(field_tag);

    // --- add data-field attribute
            el.setAttribute("data-field", field_name);

    // --- add  text_align
            el.classList.add(class_width, class_align);

            td.appendChild(el);

    // --- add EventListener to td
            if (["code", "abbrev", "name", "last_name", "depbases", "dayevelex", "otherlang", "no_order"].includes(field_name)){
                td.addEventListener("click", function() {MSCH_Open(el)}, false)
                td.classList.add("pointer_show");
                add_hover(td);
            }

// --- put value in field
           UpdateField(el, map_dict)
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

//=========  UpdateField  ================ PR2020-08-16
    function UpdateField(el_div, map_dict) {
        //console.log("=========  UpdateField =========");
        //console.log("map_dict", map_dict);

        if(el_div){
            const field_name = get_attr_from_el(el_div, "data-field");
            const fld_value = map_dict[field_name];

            if(field_name){
                let filter_value = null, display_txt = null;
                if (field_name === "select") {
                    // TODO add select multiple users option PR2020-08-18
                } else if (["activated", "locked", "no_order"].includes(field_name)){
                    el_div.className = (fld_value) ? "tickmark_2_2" : "tickmark_0_0";
                    filter_value = (fld_value) ? "1" : "0";
                } else if (["sb_code", "article", "name", "abbrev"].indexOf(field_name) > -1){
                    el_div.innerText = map_dict[field_name];
                    filter_value = (fld_value) ? fld_value.toLowerCase() : null;
                } else if ( field_name === "otherlang") {
                    display_txt = (fld_value === "pa") ? loc.Papiamentu : (fld_value === "en") ? loc.English : "\n";
                    el_div.innerText = display_txt;
                    filter_value = (display_txt) ? display_txt.toLowerCase() : null;
                } else if ( field_name === "depbases") {
                    display_txt = b_get_depbases_display(department_map, "base_code", fld_value);
                    el_div.innerText = display_txt;
                    filter_value = (display_txt) ? display_txt.toLowerCase() : null;
               } else if ( field_name === "dayevelex") {
                     display_txt = get_dayevelex_display(map_dict);
                     el_div.innerText = display_txt;
                    filter_value = (display_txt) ? display_txt.toLowerCase() : null;
                }
    // ---  add attribute filter_value
                add_or_remove_attr (el_div, "data-filter", !!filter_value, filter_value);
            }  // if(field_name)
        }  // if(el_div)
    };  // UpdateField

//========= set_columns_hidden  ====== PR2021-07-05
    function set_columns_hidden() {
        //console.log( "===== set_columns_hidden  === ");
        //console.log("setting_dict.sel_dep_level_req", setting_dict.sel_dep_level_req);
        //columns_hidden.lvl_abbrev = (!setting_dict.sel_dep_level_req);
    }  // set_columns_hidden



// +++++++++++++++++ UPLOAD CHANGES +++++++++++++++++ PR2020-08-03

//========= UploadToggle  ============= PR2020-07-31
    function UploadToggle(el_input) {
        //console.log( " ==== UploadToggle ====");

        mod_dict = {};
        const tblRow = get_tablerow_selected(el_input);
        if(tblRow){
            const tblName = get_attr_from_el(tblRow, "data-table")
            const map_id = tblRow.id
            const map_dict = get_mapdict_from_datamap_by_id(school_map, map_id);

            if(!isEmpty(map_dict)){
                const fldName = get_attr_from_el(el_input, "data-field");
                let permit_value = get_attr_from_el_int(el_input, "data-value");
                let has_permit = (!!permit_value);

                const is_request_user = (permit_dict.requsr_pk === map_dict.id)

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
                                               ppk: map_dict.company_id,
                                               table: "user",
                                               mode: "update",
                                               mapid: map_id},
                                          permits: {value: new_permit_sum, update: true}};
                    UploadChanges(upload_dict, urls.url_school_upload);
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

                    if ("updated_school_rows" in response) {
                        const el_MSCH_loader = document.getElementById("id_MSCH_loader");
                        if(el_MSCH_loader){ el_MSCH_loader.classList.add(cls_visible_hide)};

                        $("#id_mod_confirm").modal("hide");

                        const tblName = "school";
                        const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                        //RefreshDataMap(tblName, field_names, response.updated_school_rows, school_map);
                        RefreshDataRows(tblName, response.updated_school_rows, school_rows, true)  // true = update
                    };
                    $("#id_mod_school").modal("hide");

                },  // success: function (response) {
                error: function (xhr, msg) {
                    // ---  hide loader
                    el_loader.classList.add(cls_visible_hide)
                    console.log(msg + '\n' + xhr.responseText);
                }  // error: function (xhr, msg) {
            });  // $.ajax({
        }  //  if(!!row_upload)
    };  // UploadChanges

//###########################################################################
// +++++++++++++++++ REFRESH DATA ROWS ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataRows  ================ PR2021-07-05
    function RefreshDataRows(tblName, update_rows, data_rows, is_update) {
        console.log(" --- RefreshDataRows  ---");
        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length
        if (update_rows && update_rows.length ) {
            const field_setting = field_settings[tblName];
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
        console.log("update_dict", update_dict);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);

            const error_list = get_dict_value(update_dict, ["error"], []);
            //console.log("error_list", error_list);
            // field_error_list is not in use (yet)
            let field_error_list = []

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

// ++++ created ++++
            // PR2021-06-16 from https://stackoverflow.com/questions/586182/how-to-insert-an-item-into-an-array-at-a-specific-index-javascript
            //arr.splice(index, 0, item); will insert item into arr at the specified index
            // (deleting 0 items first, that is, it's just an insert).

            if(is_created){
    // ---  first remove key 'created' from update_dict
                delete update_dict.created;

    // --- lookup index where new row must be inserted in data_rows
                // PR2021-06-21 not necessary, new row has always pk higher than existing. Add at end of rows

    // ---  add new item in data_rows at end
                data_rows.push(update_dict);

    // ---  create row in table., insert in alphabetical order
                const new_tblRow = CreateTblRow(tblName, field_setting, map_id, update_dict)

    // ---  scrollIntoView,
                if(new_tblRow){
                    new_tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' })

    // ---  make new row green for 2 seconds,
                    ShowOkElement(new_tblRow);
                }
            } else {

// --- get existing data_dict from data_rows
                const pk_int = update_dict.pk;
                const [index, found_dict, compare] = b_recursive_integer_lookup(school_rows, "id", pk_int);
                const data_dict = (found_dict) ?  found_dict : {};
                const datarow_index = index;

// ++++ deleted ++++
                if(is_deleted){
                    // delete row from data_rows. Splice returns array of deleted rows
                    const deleted_row_arr = data_rows.splice(datarow_index, 1)
                    const deleted_row_dict = deleted_row_arr[0];

        //--- delete tblRow
                    if(deleted_row_dict && deleted_row_dict.mapid){
                        const tblRow_tobe_deleted = document.getElementById(deleted_row_dict.mapid);
    // ---  when delete: make tblRow red for 2 seconds, before uploading
                        if (tblRow_tobe_deleted ){tblRow_tobe_deleted.parentNode.removeChild(tblRow_tobe_deleted)};
                    };
                } else {

// +++++++++++ updated row +++++++++++
        // ---  check which fields are updated, add to list 'updated_columns'
                    if(!isEmpty(data_dict) && field_names){
                        let updated_columns = [];

                        // skip first column (is margin)
                        // col_field is the name of the column on page, not the db_field
                        for (let i = 1, col_field, old_value, new_value; col_field = field_names[i]; i++) {
                            let has_changed = false;
                            if (col_field in data_dict && col_field in update_dict){
                                has_changed = (data_dict[col_field] !== update_dict[col_field] );
                            };
        // ---  add field to updated_columns list
                            if (has_changed){
                                updated_columns.push(col_field);
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
                            let tblRow = document.getElementById(map_id);
                            if(tblRow){
                                // to make it perfect: move row when school code changed
                                if (updated_columns.includes("sb_code")){
                                //--- delete current tblRow
                                    tblRow.parentNode.removeChild(tblRow);
                                //--- insert row new at new position
                                    tblRow = CreateTblRow(tblName, field_setting, map_id, update_dict)
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
        }  // if(!isEmpty(update_dict)){
    }  // RefreshDatarowItem


// +++++++++++++++++++++++++++ MOD SCHOOL +++++++++++++++++++++++++ PR2020-09-30 PR2021-08-26
// --- also used for level, sector,
    function MSCH_Open(el_input){
        console.log(" -----  MSCH_Open   ----")
        console.log("el_input", el_input)
        if(permit_dict.permit_crud){
            let user_pk = null, user_country_pk = null, user_schoolbase_pk = null, mapid = null;
            const fldName = get_attr_from_el(el_input, "data-field");

            // el_input is undefined when called by submenu btn 'Add new'
            const is_addnew = (!el_input);
            mod_MSCH_dict = {is_addnew: is_addnew}
            console.log("is_addnew", is_addnew)

            let tblName = null;
            if(is_addnew){
                tblName = get_tblName_from_selectedBtn();
                mod_MSCH_dict.examyear_id = setting_dict.sel_examyear_pk;
                // default setting: role = school, type = dayschool
                mod_MSCH_dict.no_order = false;
                mod_MSCH_dict.defaultrole = 8;
                mod_MSCH_dict.isdayschool = true;
                mod_MSCH_dict.iseveningschool = false;
                mod_MSCH_dict.islexschool = false;

            } else {
                const tblRow = get_tablerow_selected(el_input);
                //tblName = get_attr_from_el(tblRow, "data-table")
                tblName = "school"
                const map_dict = b_get_mapdict_from_datarows(school_rows, tblRow.id, setting_dict.user_lang);
                mod_MSCH_dict = deepcopy_dict(map_dict);

            console.log("tblName", tblName)
            console.log("school_rows", school_rows)
            console.log("map_dict", map_dict)
                if(!isEmpty(map_dict)){

                    mod_MSCH_dict.id = map_dict.id;
                    mod_MSCH_dict.mapid = map_dict.mapid;
                    mod_MSCH_dict.base_id = map_dict.base_id;
                    mod_MSCH_dict.examyear_id = map_dict.examyear_id;

                    mod_MSCH_dict.code = map_dict.sb_code;
                    mod_MSCH_dict.abbrev = map_dict.abbrev;
                    mod_MSCH_dict.article = map_dict.article;
                    mod_MSCH_dict.name = map_dict.name;
                    mod_MSCH_dict.depbases = map_dict.depbases;
                    mod_MSCH_dict.otherlang = map_dict.otherlang;
                    mod_MSCH_dict.no_order = map_dict.no_order;
                    mod_MSCH_dict.defaultrole = map_dict.defaultrole,

                    mod_MSCH_dict.isdayschool = map_dict.isdayschool,
                    mod_MSCH_dict.iseveningschool = map_dict.iseveningschool,
                    mod_MSCH_dict.islexschool = map_dict.islexschool,

                    mod_MSCH_dict.modby_username = map_dict.modby_username;
                    mod_MSCH_dict.modifiedat = map_dict.modifiedat;
                }
            }
    // ---  set header text
            MSCH_headertext(is_addnew, tblName, mod_MSCH_dict.code, mod_MSCH_dict.name);

    // ---  remove value from el_mod_employee_input
            MSCH_ResetElements(true);  // true = also_remove_values

    // ---  remove value from el_mod_employee_input, set focus to selected field
            MSCH_SetElements(fldName);

            //if(permit_dict.requsr_role_system){
                t_FillOptionsFromList(el_MSCH_select_defaultrole, loc.options_role, "value", "caption",
                            loc.Select_organization + "...", loc.No_organizations_found, mod_MSCH_dict.defaultrole);
            //};
            //add_or_remove_class(el_MSCH_defaultrole_container, cls_hide, !permit_dict.requsr_role_system);
            el_MSCH_select_defaultrole.disabled = !permit_dict.requsr_role_system
        //console.log("mod_MSCH_dict", mod_MSCH_dict)
            if (!is_addnew){
                el_MSCH_code.value = (mod_MSCH_dict.code) ? mod_MSCH_dict.code : null;
                el_MSCH_abbrev.value = (mod_MSCH_dict.abbrev) ? mod_MSCH_dict.abbrev : null;
                el_MSCH_name.value = (mod_MSCH_dict.name) ? mod_MSCH_dict.name : null;
                el_MSCH_article.value = (mod_MSCH_dict.article) ? mod_MSCH_dict.article : null;
                el_MSCH_select_defaultrole.value = (mod_MSCH_dict.defaultrole) ? mod_MSCH_dict.defaultrole : null;
                el_MSCH_select_otherlang.value = (mod_MSCH_dict.otherlang) ? mod_MSCH_dict.otherlang : "none";
                el_MSCH_no_order.value = (mod_MSCH_dict.no_order) ? "1" : "0";

                const modified_dateJS = parse_dateJS_from_dateISO(mod_MSCH_dict.modifiedat);
                const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
                const modified_by = (mod_MSCH_dict.modby_username) ? mod_MSCH_dict.modby_username : "-";

                document.getElementById("id_MSCH_msg_modified").innerText = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by
            }

            MSCH_FillSelectTableDepartment();

    // ---  set focus to el_MSCH_code
            setTimeout(function (){el_MSCH_code.focus()}, 50);

    // ---  disable btn submit, hide delete btn when is_addnew
           // add_or_remove_class(el_MSCH_btn_delete, cls_hide, is_addnew )
            const disable_btn_save = (!el_MSCH_abbrev.value || !el_MSCH_name.value || !el_MSCH_code.value  || !el_MSCH_article.value )
            el_MSCH_btn_save.disabled = disable_btn_save;

            MSCH_validate_and_disable();

    // ---  show modal
            $("#id_mod_school").modal({backdrop: true});
        }
    };  // MSCH_Open

//=========  MSCH_Save  ================  PR2020-10-01
    function MSCH_Save(crud_mode) {
        console.log(" -----  MSCH_save  ----", crud_mode);
        console.log( "mod_MSCH_dict: ", mod_MSCH_dict);

        if(permit_dict.permit_crud){
            const is_delete = (crud_mode === "delete")

            let upload_dict = {table: 'school', examyear_pk: setting_dict.sel_examyear_pk}

            if(mod_MSCH_dict.is_addnew) {
                upload_dict.mode = "create";
            } else {
                upload_dict.school_pk = mod_MSCH_dict.id;
                upload_dict.mapid = mod_MSCH_dict.mapid;
                if(is_delete) {upload_dict.mode = "delete"}
            }
    // ---  put changed values of input elements in upload_dict
            let form_elements = el_MSCH_div_form_controls.querySelectorAll(".form-control")
            for (let i = 0, el, fldName, old_value, new_value; el = form_elements[i]; i++) {
                fldName = get_attr_from_el(el, "data-field");
                if(fldName === "dayevelex"){
                    const new_isdayschool = ["day", "dayeve"].includes(el.value);
                    if (new_isdayschool !== mod_MSCH_dict.isdayschool) {
                        upload_dict.isdayschool = new_isdayschool;
                    }
                    const new_iseveningschool = ["eve", "dayeve"].includes(el.value);
                    if (new_iseveningschool !== mod_MSCH_dict.iseveningschool) {
                        upload_dict.iseveningschool = new_iseveningschool;
                    }
                    const new_islexschool = (el.value === "lex");
                    if (new_islexschool !== mod_MSCH_dict.islexschool) {
                        upload_dict.islexschool = new_islexschool;
                    }
                } else if(fldName === "otherlang"){;
            console.log("fldName", fldName)
                    old_value = (!!mod_MSCH_dict[fldName])
                    new_value = (el.value === "none") ? null : el.value;
            console.log("new_value", new_value)
                    if (new_value !== old_value) {
                        upload_dict[fldName] = new_value
                    };
            console.log("upload_dict", upload_dict)
                } else if(fldName === "no_order"){;
                    old_value = (!!mod_MSCH_dict[fldName])
                    new_value = (el.value === "1") ? true : false;
                    if (new_value !== old_value) {
                        upload_dict[fldName] = new_value
                    };

                } else {
                    old_value = (mod_MSCH_dict[fldName]) ? mod_MSCH_dict[fldName] : null;
                    new_value = (el.value) ? el.value : null;
                    if (new_value !== old_value) {
                        upload_dict[fldName] = new_value
                    };
                };
            };
    // ---  get selected departments
            let dep_list = MSCH_get_selected_depbases();

            upload_dict['depbases'] = dep_list;

            document.getElementById("id_MSCH_loader").classList.remove(cls_visible_hide)
            // modal is closed by data-dismiss="modal"
            UploadChanges(upload_dict, urls.url_school_upload);
        };
        $("#id_mod_school").modal("hide");
    }  // MSCH_Save

//========= MSCH_FillSelectTableDepartment  ============= PR2020--09-30
    function MSCH_FillSelectTableDepartment() {
        console.log("===== MSCH_FillSelectTableDepartment ===== ");
        //console.log("department_map", department_map);

        const data_map = department_map;
        const tblBody_select = document.getElementById("id_MSCH_tbody_select");
        tblBody_select.innerText = null;

// ---  loop through data_map
        let row_count = 0
        if(data_map.size > 1) {
            MSCH_FillSelectRow(tblBody_select, {}, "<" + loc.All_departments + ">");
        }
        for (const [map_id, dict] of data_map.entries()) {
            MSCH_FillSelectRow(tblBody_select, dict);
        }

    } // MSCH_FillSelectTableDepartment

//========= MSCH_FillSelectRow  ============= PR2020--09-30
    function MSCH_FillSelectRow(tblBody_select, dict, select_all_text) {
        //console.log("===== MSCH_FillSelectRowDepartment ===== ");
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
        // check if this dep is in mod_MSCH_dict.depbases. Set tickmark if yes
        let selected_int = 0;
        if(mod_MSCH_dict.depbases){
            const arr = mod_MSCH_dict.depbases.split(";");
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
        tblRow.addEventListener("click", function() {MSCH_SelectDepartment(tblRow)}, false);
    } // MSCH_FillSelectRow

//========= MSCH_SelectDepartment  ============= PR2020-10-01
    function MSCH_SelectDepartment(tblRow){
        console.log( "===== MSCH_SelectDepartment  ========= ");
        console.log( "tblRow", tblRow);

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
                    MSCH_set_selected(row, is_selected)
                }
            } else {
// ---  put new value in this tblRow, show/hide tickmark
                MSCH_set_selected(tblRow, is_selected)

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
                MSCH_set_selected(tblRow_selectall, (has_rows && !unselected_rows_found))
            }
// check for double abbrev in deps
            const fldName = "abbrev";
            const msg_err = validate_duplicates_in_department(loc, "school", fldName, loc.Abbreviation, mod_MSCH_dict.mapid, mod_MSCH_dict.abbrev)
            const el_msg = document.getElementById("id_MSCH_msg_" + fldName);
            el_msg.innerText = msg_err;
            add_or_remove_class(el_msg, cls_hide, !msg_err)

            el_MSCH_btn_save.disabled = (!!msg_err);
        }
    }  // MSCH_SelectDepartment

//========= MSCH_set_selected  ============= PR2020-10-01
    function MSCH_set_selected(tblRow, is_selected){
        console.log( "  ---  MSCH_set_selected  --- ", is_selected);
        console.log( "tblRow", tblRow);
// ---  put new value in tblRow, show/hide tickmark
        if(tblRow){
            tblRow.setAttribute("data-selected", ( (is_selected) ? 1 : 0) )
            const img_class = (is_selected) ? "tickmark_2_2" : "tickmark_0_0"
            const el = tblRow.cells[0].children[0];
        console.log( "el", el);
            //if (el){add_or_remove_class(el, "tickmark_2_2", is_selected , "tickmark_0_0")}
            if (el){el.className = img_class}
        }
    }  // MSCH_set_selected

//========= MSCH_get_selected_depbases  ============= PR2020-10-07
    function MSCH_get_selected_depbases(){
        console.log( "  ---  MSCH_get_selected_depbases  --- ")
        const tblBody_select = document.getElementById("id_MSCH_tbody_select");
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
    }  // MSCH_get_selected_depbases

//========= MSCH_InputKeyup  ============= PR2020-10-01
    function MSCH_InputKeyup(el_input){
        //console.log( "===== MSCH_InputKeyup  ========= ");
        MSCH_validate_and_disable();
    }; // MSCH_InputKeyup


//========= MSCH_InputSelect  ============= PR2020-12-11
    function MSCH_InputSelect(el_input){
        //console.log( "===== MSCH_InputSelect  ========= ");
        MSCH_validate_and_disable();
    }; // MSCH_InputSelect

//========= MSCH_InputToggle  ============= PR2021-08-26
    function MSCH_InputToggle(el_input){
        console.log( "===== MSCH_InputToggle  ========= ");
        const data_value = get_attr_from_el(el_input, "data-value")
        const new_data_value = (data_value === "1") ? "0" : "1";
        el_input.setAttribute("data-value", new_data_value);
        const el_img = el_input.children[0];
        add_or_remove_class(el_img, "tickmark_2_2", (new_data_value === "1"), "tickmark_1_1")
    }; // MSCH_InputToggle

//=========  MSCH_validate_and_disable  ================  PR2020-10-01
    function MSCH_validate_and_disable() {
        //console.log(" -----  MSCH_validate_and_disable   ----")
        let disable_save_btn = false;
// ---  loop through input fields on MSCH_Open
        let form_elements = el_MSCH_div_form_controls.querySelectorAll(".form-control")
        for (let i = 0, el_input; el_input = form_elements[i]; i++) {

            const fldName = get_attr_from_el(el_input, "data-field")
            const msg_err = MSCH_validate_field(el_input, fldName)
        //console.log("msg_err", msg_err)
// ---  show / hide error message
            const el_msg = document.getElementById("id_MSCH_msg_" + fldName);
            if(el_msg){
                el_msg.innerText = msg_err;
                add_or_remove_class(el_msg, cls_hide, !msg_err)
            }
            if (msg_err){ disable_save_btn = true};
        };

        //console.log("disable_save_btn", disable_save_btn)
// ---  disable save button on error
        el_MSCH_btn_save.disabled = disable_save_btn;
    }  // MSCH_validate_and_disable

//=========  MSCH_validate_field  ================  PR2020-10-01
    function MSCH_validate_field(el_input, fldName) {
        //console.log(" -----  MSCH_validate_field   ----")
        let msg_err = null;
        if (el_input){
            const value = el_input.value;
             const caption = (fldName === "sb_code") ? loc.School_code :
                             (fldName === "abbrev") ? loc.Short_name :
                             (fldName === "name") ? loc.Name  :
                             (fldName === "defaultrole") ? loc.Organization  : loc.This_field;


        //console.log("fldName", fldName)
        //console.log("value", value)
            if (["sb_code", "abbrev", "name", "defaultrole"].indexOf(fldName) > -1 && !value) {
                msg_err = caption + loc.cannot_be_blank;
            } else if (fldName === "abbrev" && value.length > 30) {
                msg_err = caption + loc.is_too_long_max_schoolcode;
            } else if (fldName === "name" && value.length > 50) {
                    msg_err = caption + loc.is_too_long_max_name;
            } else if (["abbrev", "name"].indexOf(fldName) > -1) {
                    msg_err = validate_duplicates_in_department(loc, "school", fldName, caption, mod_MSCH_dict.mapid, value)
            }
        }
        return msg_err;
    }  // MSCH_validate_field

//=========  validate_duplicates_in_department  ================ PR2020-09-11
    function validate_duplicates_in_department(loc, tblName, fldName, caption, selected_mapid, selected_code) {
        //console.log(" =====  validate_duplicates_in_department =====")
        //console.log("fldName", fldName)
        let msg_err = null;
        if (tblName && fldName && selected_code){
            const data_map = (tblName === "school") ? school_map : null;
            if (data_map && data_map.size){
                const selected_code_lc = selected_code.trim().toLowerCase()
    //--- loop through schools
                for (const [map_id, map_dict] of data_map.entries()) {
                    // skip current item
                    if(map_id !== selected_mapid) {
                        const lookup_value = (map_dict[fldName]) ? map_dict[fldName].trim().toLowerCase() : null;
                        if(lookup_value && lookup_value === selected_code_lc){
                            console.log(" =====  validate_duplicates_in_department =====")

                            // check if they have at least one department in common
                            let depbase_in_common = false;
                            const selected_depbases = MSCH_get_selected_depbases();
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

//========= MSCH_ResetElements  ============= PR2020-08-03
    function MSCH_ResetElements(also_remove_values){
        //console.log( "===== MSCH_ResetElements  ========= ");
        // --- loop through input elements

        const form_elements = el_MSCH_div_form_controls.querySelectorAll("INPUT, SELECT, SMALL");
        for (let i = 0, el; el = form_elements[i]; i++) {
            if(["INPUT", "SELECT"].includes(el.tagName) ){
                el.classList.remove("border_bg_invalid", "border_bg_valid");
                if(also_remove_values){ el.value = null};
            } else if(el.tagName === "SMALL"){
                if(also_remove_values){ el.innerText = "\n"};
            };
        };
    }  // MSCH_ResetElements

//========= MSCH_SetElements  ============= PR2021-06-20
    function MSCH_SetElements(focus_field){
        //console.log( "===== MSCH_SetElements  ========= ");
        //console.log( "mod_MSCH_dict", mod_MSCH_dict);
        //console.log( "focus_field", focus_field);
// --- loop through input elements
        let form_elements = el_MSCH_div_form_controls.querySelectorAll(".form-control")
        for (let i = 0, el, fldName, fldValue; el = form_elements[i]; i++) {
            fldName = get_attr_from_el(el, "data-field");
            fldValue = (mod_MSCH_dict[fldName]) ? mod_MSCH_dict[fldName] : null;
            if(fldName === "dayevelex"){
                el.value = (mod_MSCH_dict.isdayschool && mod_MSCH_dict.iseveningschool) ? "dayeve" :
                            (mod_MSCH_dict.islexschool)  ? "lex" :
                            (mod_MSCH_dict.iseveningschool)  ? "eve" :
                            (mod_MSCH_dict.isdayschool)  ? "day" : null
            } else {
                el.value = fldValue;
            }
        //console.log( "fldName", fldName);
            if(focus_field ){
                if( (fldName === focus_field) ||
                    (fldName === "lvl_id" && focus_field === "lvl_abbrev") ||
                    (fldName === "sct_id" && focus_field === "sct_abbrev")){
            console.log( "set_focus_on_el_with_timeout", fldName);
                    set_focus_on_el_with_timeout(el, 150);
                };
            }
        }

        //let full_name = (mod_MSCH_dict.fullname) ? mod_MSCH_dict.lastname : "";
        //document.getElementById("id_MSCH_hdr").innerText = (mod_MSCH_dict.fullname) ? mod_MSCH_dict.fullname : loc.Add_candidate;
    }  // MSCH_SetElements



//========= MSCH_SetMsgElements  ============= PR2020-08-02
    function MSCH_SetMsgElements(response){
        //console.log( "===== MSCH_SetMsgElements  ========= ");

        const err_dict = ("msg_err" in response) ? response.msg_err : {}
        const validation_ok = get_dict_value(response, ["validation_ok"], false);

        //console.log( "err_dict", err_dict);
        //console.log( "validation_ok", validation_ok);

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
            b_show_hide_selected_elements_byClass("tab_show", "tab_ok");

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
                b_show_hide_selected_elements_byClass("tab_show", "tab_ok");

            } else {
                const fields = ["username", "last_name", "email"]
                for (let i = 0, field; field = fields[i]; i++) {
                    const msg_err = get_dict_value(err_dict, [field]);
                    const msg_info = loc.msg_user_info[i];

                    let el_input = document.getElementById("id_MSCH_" + field);
                    add_or_remove_class (el_input, "border_bg_invalid", (!!msg_err));
                    add_or_remove_class (el_input, "border_bg_valid", (!msg_err));

                    let el_msg = document.getElementById("id_MSCH_msg_" + field);
                    add_or_remove_class (el_msg, "text-danger", (!!msg_err));
                    el_msg.innerText = (!!msg_err) ? msg_err : msg_info
                }
            }
            el_MSCH_btn_save.disabled = !validation_ok;
            if(validation_ok){el_MSCH_btn_save.focus()}
        }
// ---  show message in footer when no error and no ok msg
        add_or_remove_class(el_MUA_info_footer01, cls_hide, !validation_ok )
        add_or_remove_class(el_MUA_info_footer02, cls_hide, !validation_ok )

// ---  set text on btn cancel
        const el_MUA_btn_cancel = document.getElementById("id_MUA_btn_cancel");
        el_MUA_btn_cancel.innerText = ((is_ok || err_save) ? loc.Close: loc.Cancel);
        if(is_ok || err_save){el_MUA_btn_cancel.focus()}

    }  // MUA_SetMsgElements

//========= MSCH_headertext  ======== // PR2020-10-22
    function MSCH_headertext(is_addnew, tblName, code, name) {
        //console.log(" -----  MSCH_headertext   ----")
        //console.log("tblName", tblName, "is_addnew", is_addnew)

        let header_text = null;  (is_addnew) ? loc.Add_school : loc.School;

        if (is_addnew) {
            header_text = loc.Add_school;
        } else {
            header_text = ((code) ? code : "---") + " - " + ((name) ? name : "---");

        };
        document.getElementById("id_MSCH_header").innerText = header_text;

        //document.getElementById("id_MSCH_label_dep").innerText = loc.Departments_of_this_school + ":";
    }  // MSCH_headertext

// +++++++++ END MOD SCHOOL ++++++++++++++++++++++++++++++++++++++++++++++++++++

// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2020-08-03  PR2020-10-23
    function ModConfirmOpen(mode, el_input) {
        console.log(" -----  ModConfirmOpen   ----")
        console.log("mode", mode)
        // values of mode are : "delete", "inactive" or "send_activation_email", "permission_sysadm"

        if(permit_dict.permit_crud){
            el_confirm_msg_container.innerHTML = null;

    // ---  get selected_pk
            let tblName = null, selected_pk = null;
            // tblRow is undefined when clicked on delete btn in submenu btn or form (no inactive btn)
            const tblRow = get_tablerow_selected(el_input);
            if(tblRow){
                tblName = get_attr_from_el(tblRow, "data-table")
                const pk_int = get_attr_from_el_int(tblRow, "data-pk")
                const [index, found_dict, compare] = b_recursive_integer_lookup(school_rows, "id", pk_int);
                selected.school_dict = (found_dict) ?  found_dict : {};
                selected.school_pk = (selected.school_dict) ?  selected.school_dict.id : null;

            } else {
                // get map_dict from selected.school_dict
                tblName = get_tblName_from_selectedBtn()
            }
            console.log("tblName", tblName )
            console.log("selected_pk", selected_pk )
            // TODO change to selected.school_dict

    // ---  get info from data_map
            const map_dict = selected.school_dict;
            const map_id = (selected.school_dict) ? selected.school_dict.mapid : null;;
            console.log("map_id", map_id)
            console.log("map_dict", map_dict)

    // ---  create mod_dict
            mod_dict = {mode: mode};
            const has_selected_item = (!isEmpty(map_dict));
            if(has_selected_item){
                mod_dict = {mode: mode,
                            id: map_dict.id,
                            examyear_id: map_dict.examyear_id,
                            abbrev: map_dict.abbrev,
                            name: map_dict.name,
                            depbases: map_dict.depbases,
                            mapid: map_id
                }
            };
            if (mode === "inactive") {
                  mod_dict.is_active = map_dict.is_active;
            }

    // ---  put text in modal form
            let dont_show_modal = false;

            let header_text = (tblName === "school") ? loc.Delete_school : loc.Delete;

            let msg01_txt = null, msg02_txt = null, msg03_txt = null;
            let hide_save_btn = false;
            if(!has_selected_item){

                msg01_txt = loc.Please_select__ + ( (tblName === "school") ? loc.a_school : loc.an_item ).toLowerCase() + loc.__first;
                hide_save_btn = true;
            } else {
                const name =  (tblName === "school") ? ((mod_dict.name) ? mod_dict.name  : "-") : "-";
                if(mode === "delete"){
                    msg01_txt = loc.School + " '" + name + "'" + loc.will_be_deleted
                    msg02_txt = loc.Do_you_want_to_continue;
                }
            }
            if(!dont_show_modal){
                el_confirm_header.innerText = header_text;
                el_confirm_loader.classList.add(cls_visible_hide)

                let msg_html = "";
                if (msg01_txt) {msg_html += "<p>" + msg01_txt + "</p>"};
                if (msg02_txt) {msg_html += "<p>" + msg02_txt + "</p>"};
                if (msg03_txt) {msg_html += "<p>" + msg03_txt + "</p>"};
                el_confirm_msg_container.innerHTML = msg_html

                el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");

                const caption_save = (mode === "delete") ? loc.Yes_delete :
                                (mode === "inactive") ? ( (mod_dict.is_active) ? loc.Yes_make_inactive : loc.Yes_make_active ) :
                                loc.OK;
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
        let close_modal = !permit_dict.permit_crud;

        if(permit_dict.permit_crud){
            let tblRow = document.getElementById(mod_dict.mapid);
            let upload_dict = {};

            if(mod_dict.mode === "delete") {
                upload_dict = { school_pk: mod_dict.id,
                                table: "school",
                                mode: "delete",
                                mapid: mod_dict.mapid
                                };
// ---  show loader
                el_confirm_loader.classList.remove(cls_visible_hide)
// ---  when delete: make tblRow red, before uploading, close moadl
                ShowClassWithTimeout(tblRow, "tsa_tr_error");
                close_modal = true;

            } else if (mod_dict.mode === "inactive") {
                const new_isactive = !mod_dict.is_active
                close_modal = true;
                upload_dict = { id: {pk: mod_dict.id,
                                         table: "school",
                                         mode: mod_dict.mode,
                                         mapid: mod_dict.mapid},
                                is_active: {value: new_isactive, update: true} };

    // ---  change inactive icon, before uploading, not when new_inactive = true
                const el_input = document.getElementById(mod_dict.mapid)
                for (let i = 0, cell, el; cell = tblRow.cells[i]; i++) {
                    const cell_fldName = get_attr_from_el(cell, "data-field")
                    if (cell_fldName === "is_active"){
    // ---  change icon, before uploading
                        let el_icon = cell.children[0];
                        if(el_icon){add_or_remove_class (el_icon, "inactive_1_3", new_isactive,"inactive_0_2" )};
                        break;
                    }
                }
            }
// ---  Upload Changes
            console.log("upload_dict: ", upload_dict);
            UploadChanges(upload_dict, urls.url_school_upload);
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
        }
    }  // ModConfirmResponse

//#########################################################################
// +++++++++++++++++ REFRESH DATA MAP ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataMap  ================ PR2020-08-16 PR2020-10-22
    function RefreshDataMap(tblName, field_names, data_rows, data_map) {
        //console.log(" --- RefreshDataMap  ---");
        //console.log("data_rows", data_rows);
        if (data_rows) {
            const field_setting = field_settings[tblName];
            for (let i = 0, update_dict; update_dict = data_rows[i]; i++) {
                RefreshDatamapItem(tblName, field_setting, update_dict, data_map);
            }
        }
    }  //  RefreshDataMap

//=========  RefreshDatamapItem  ================ PR2020-08-16 PR2020-09-30
    function RefreshDatamapItem(tblName, field_setting, update_dict, data_map) {
        //console.log(" --- RefreshDatamapItem  ---");
        //console.log("update_dict", update_dict);
        if(!isEmpty(update_dict)){
// ---  update or add update_dict in school_map
            let updated_columns = [];
    // get existing map_item
            const tblName = update_dict.table;
        //console.log("tblName", tblName);
            const map_id = update_dict.mapid;
        //console.log("map_id", map_id);
            const code = (tblName === "school") ? update_dict.sb_code : null;
        //console.log("code", code);
            let tblRow = document.getElementById(map_id);

            const is_deleted = get_dict_value(update_dict, ["deleted"], false)
            const is_created = get_dict_value(update_dict, ["created"], false)

// ++++ created ++++
            if(is_created){
    // ---  insert new item
                data_map.set(map_id, update_dict);
                updated_columns.push("created")
        //console.log("updated_columns", updated_columns);
    // ---  create row in table., insert in alphabetical order
                const order_by = (code) ? code.toLowerCase() : null;
        //console.log("order_by", order_by);
                const row_index = t_get_rowindex_by_sortby(tblBody_datatable, order_by)
        //console.log("row_index", row_index);
                tblRow = CreateTblRow(tblName, field_setting, map_id, update_dict, row_index)
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
    }  // RefreshDatamapItem


//###########################################################################
// +++++++++++++++++ FILTER ++++++++++++++++++++++++++++++++++++++++++++++++++

//========= HandleFilterKeyup  ================= PR2021-06-16
    function HandleFilterKeyup(el, event) {
        console.log( "===== HandleFilterKeyup  ========= ");
        // skip filter if filter value has not changed, update variable filter_text

        // PR2021-05-30 debug: use cellIndex instead of attribute data-colindex,
        // because data-colindex goes wrong with hidden columns
        // was:  const col_index = get_attr_from_el(el_input, "data-colindex")
        const col_index = el.parentNode.cellIndex;
        console.log( "col_index", col_index, "event.key", event.key);

        const skip_filter = t_SetExtendedFilterDict(el, col_index, filter_dict, event.key);
        console.log( "filter_dict", filter_dict);

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
        console.log( "col_index", col_index);
        console.log( "filter_tag", filter_tag);
        console.log( "field_name", field_name);

    // - get current value of filter from filter_dict, set to '0' if filter doesn't exist yet
        const filter_array = (col_index in filter_dict) ? filter_dict[col_index] : [];
        const filter_value = (filter_array[1]) ? filter_array[1] : "0";
        console.log( "filter_array", filter_array);
        console.log( "filter_value", field_name);

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


        Filter_TableRows();
    }; // HandleFilterField

//========= Filter_TableRows  ==================================== PR2020-08-17
    function Filter_TableRows() {
        //console.log( "===== Filter_TableRows  ========= ");

        const tblName_settings = "school";
        const field_setting = field_settings[tblName_settings];
        const filter_tags = field_setting.filter_tags;

// ---  loop through tblBody.rows
        for (let i = 0, tblRow, show_row; tblRow = tblBody_datatable.rows[i]; i++) {
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

        selected.school_pk = null;

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
    }  // function ResetFilterRows


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL SELECT EXAMYEAR SCHOOL DEPARTMENT  ++++++++++++++++++++
// functions are in table.js, except for MSED_Response

//=========  MSED_Response  ================ PR2020-12-18 PR2021-05-10
    function MSED_Response(new_setting) {
        console.log( "===== MSED_Response ========= ");

// ---  upload new selected_pk
// also retrieve the tables that have been changed because of the change in examyear / dep
        const datalist_request = {
                setting: new_setting,
                school_rows: {get: true},
                studentsubject_rows: {get: true},
                grade_rows: {get: true},
                schemeitem_rows: {get: true}
            };
        DatalistDownload(datalist_request);

    }  // MSED_Response

//=========  MSSSS_Response  ================ PR2021-01-23 PR2021-02-05 PR2021-07-26
    function MSSSS_Response(tblName, selected_dict, selected_pk) {
        console.log( "===== MSSSS_Response ========= ");
        console.log( "selected_pk", selected_pk);

    // ---  upload new setting
        if(selected_pk === -1) { selected_pk = null};
        const upload_dict = {};
        const selected_pk_dict = {sel_student_pk: selected_pk};
        selected_pk_dict["sel_" + tblName + "_pk"] = selected_pk;
        let new_selected_btn = null;

        if (tblName === "school") {
// ---  put new selected_pk in setting_dict
            setting_dict.sel_schoolbase_pk = selected_pk;

// ---  upload new setting and refresh page
            let datalist_request = {setting: {page: "page_grade", sel_schoolbase_pk: selected_pk}};
            DatalistDownload(datalist_request);
        } else {
            UploadSettings ({selected_pk: selected_pk_dict}, urls.url_settings_upload);
            if (new_selected_btn) {
        // change selected_button
                HandleBtnSelect(new_selected_btn, true)  // true = skip_upload
                // also calls: FillTblRows(), MSSSS_display_in_sbr(), UpdateHeader()
            }  else {
        // fill datatable
                FillTblRows();
                MSSSS_display_in_sbr()
        // --- update header text - comes after MSSSS_display_in_sbr
                UpdateHeaderLeft();
            }
        }
    }  // MSSSS_Response

//###########################################################################

//========= MOD NOTE Open====================================
    function ModUploadAwp_open () {
        console.log("===  ModUploadAwp_open  =====") ;
// reset filedialog
        el_ModUploadAwp_filedialog.value = null;
// hide loader
        const el_ModUploadAwp_loader = document.getElementById("id_ModUploadAwp_loader");
        add_or_remove_class(el_ModUploadAwp_loader, cls_hide, true);

        $("#id_mod_uploadawp").modal({backdrop: true});

    }  // ModUploadAwp_open

//========= ModUploadAwp_Save============== PR2020-10-15
    function ModUploadAwp_Save () {
        console.log("===  ModUploadAwp_Save  =====");
        const filename = el_ModUploadAwp_filedialog.value;

       // if(permit.write_note_intern || permit.write_note_extern){
// get attachment info
            const file = el_ModUploadAwp_filedialog.files[0];  // file from input
            const file_type = (file) ? file.type : null;
            const file_name = (file) ? file.name : null;
            const file_size = (file) ? file.size : 0;

           // may check size or type here with
            // ---  upload changes
            const upload_dict = { table: "awp_upload",
                                   file_type: file_type,
                                   file_name: file_name,
                                   file_size: file_size
                                   };
            const upload_json = JSON.stringify (upload_dict)

            if(file_size){

// show loader
                const el_ModUploadAwp_loader = document.getElementById("id_ModUploadAwp_loader");
                add_or_remove_class(el_ModUploadAwp_loader, cls_hide, false);

                console.log("file", file);
                const upload = new Upload(upload_json, file, urls.url_school_awpupload);
            console.log("upload_dict", upload_dict);

                // execute upload
                upload.doUpload();

                console.log("after upload.doUpload()");

           }
      // }
// hide modal
        $("#id_mod_note").modal("hide");
    }  // ModUploadAwp_Save

// PR2021-03-16 from https://stackoverflow.com/questions/2320069/jquery-ajax-file-upload
    const Upload = function (upload_json, file, url_str) {
        this.upload_json = upload_json;
        this.file = file;
        this.url_str = url_str;
    };

    Upload.prototype.getType = function() {
        return (this.file) ? this.file.type : null;
    };
    Upload.prototype.getSize = function() {
        return (this.file) ? this.file.size : 0;
    };
    Upload.prototype.getName = function() {
        return (this.file) ? this.file.name : null;
    };
    Upload.prototype.doUpload = function () {
        var that = this;
        var formData = new FormData();
        // from https://blog.filestack.com/thoughts-and-knowledge/ajax-file-upload-formdata-examples/
        // add to input html:  <input id="id_ModNote_filedialog" type="file" multiple="multiple"
        // Loop through each of the selected files.
        //for(var i = 0; i < files.length; i++){
        //  var file = files[i];
        // formData.append('myfiles[]', file, file.name);

        // add assoc key values, this will be posts values
        console.log( this.getType())
        console.log( this.getName())

        formData.append("upload_file", true);
        formData.append("filename", this.getName());
        formData.append("contenttype", this.getType());

        if (this.file){
            formData.append("file", this.file, this.getName());
        }
        // from https://stackoverflow.com/questions/16761987/jquery-post-formdata-and-csrf-token-together
        const csrftoken = Cookies.get('csrftoken');
        formData.append('csrfmiddlewaretoken', csrftoken);
        formData.append('upload', this.upload_json);

        console.log(formData)
        $.ajax({
            type: "POST",
            url: this.url_str,
            xhr: function () {
                var myXhr = $.ajaxSettings.xhr();
                if (myXhr.upload) {
                    myXhr.upload.addEventListener('progress', that.progressHandling, false);
                }
                return myXhr;
            },
            success: function (response) {
                $("#id_mod_uploadawp").modal("hide");
                console.log(response)

                const log_list = get_dict_value(response, ["logfile"]);
                if (!!log_list && log_list.length > 0) {
                    printPDFlogfile(log_list, "log_AWP_upload");
                }

            },
            error: function (error) {
                $("#id_mod_uploadawp").modal("hide");
                console.log(error)
            },
            async: true,
            data: formData,
            cache: false,
            contentType: false,
            processData: false,
            timeout: 60000
        });

    };

    Upload.prototype.progressHandling = function (event) {
        let percent = 0;
        const position = event.loaded || event.position;
        const total = event.total;
        const progress_bar_id = "#progress-wrp";
        if (event.lengthComputable) {
            percent = Math.ceil(position / total * 100);
        }
        // update progressbars classes so it fits your code
        $(progress_bar_id + " .progress-bar").css("width", +percent + "%");
        $(progress_bar_id + " .status").text(percent + "%");
    };


//?????????????????????????????????????????????????????????????????

//========= get_dayevelex_display  ======== // PR2021-06-20
    function get_dayevelex_display(dict) {
        let display_txt = null;
        if(!isEmpty(dict)){
            display_txt = (dict.isdayschool && dict.iseveningschool) ? loc.Day_Eveningschool :
                        (dict.islexschool)  ? loc.Landsexamen :
                        (dict.iseveningschool)  ? loc.Evening_school :
                        (dict.isdayschool)  ? loc.Day_school : null
        };
        return display_txt
    };
//========= get_tblName_from_selectedBtn  ======== // PR2020-09-30
    function get_tblName_from_selectedBtn() {
        const tblName = (selected_btn === "btn_school") ? "school" : null;

        return tblName;
    }
//========= get_datamap_from_tblName  ======== // PR2020-09-30
    function get_datamap_from_tblName(tblName) {
        const data_map = (tblName === "school") ? school_map : null;
        return data_map;
    }

//###########################################################################
//========= get_permits  ======== PR2021-03-27
    function get_permits(permit_list) {

        // <PERMIT> PPR2021-03-27
        //  edit permits can only be true if:
        //   - country is not locked
        //   - AND examyear is published AND not locked
        //   - AND school is activated AND not locked

        // reset permits -- not necessary. Function is only called once in first DatalistDownload
        // user cannot open page when no view-permit or country_locked or not examyear_published  or not school_activated
        // no_access is set on server when user has no view-permit or country_locked or not examyear_published  or not school_activated

        // permit.view_page: (!!el_loader), got value at start of script

        const locked = (setting_dict.sel_examyear_locked || setting_dict.sel_school_locked);
        //permit_dict.permit_crud = (!locked && permit_list.includes("crud"));
    }  // get_permits



})  // document.addEventListener('DOMContentLoaded', function()