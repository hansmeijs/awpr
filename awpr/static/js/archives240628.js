// PR2022-03-09 added

// PR2021-07-23  these variables are declared in base.js to make them global variables

// selected_btn is also used in t_MCOL_Open
//let selected_btn = "btn_exform";

//let school_rows = [];
const published_dicts = {};
const diplomagradelist_dicts = {};
//const field_settings = {};  // PR2023-04-20 made global

document.addEventListener('DOMContentLoaded', function() {
    "use strict";

// ---  check if user has permit to view this page. If not: el_loader does not exist PR2020-10-02
    const el_loader = document.getElementById("id_loader");
    const el_hdr_left = document.getElementById("id_header_left");
    const may_view_page = (!!el_loader);

// ---  id of selected customer and selected order
    // declared as global: //let selected_btn = "btn_exform";
    ////let setting_dict = {};
    ////let permit_dict = {};

    let mod_dict = {};
    let mod_MSTUD_dict = {};

    let examyear_map = new Map();
    let school_map = new Map();
    // PR2020-12-26 These variable defintions are moved to import.js, so they can also be used in that file
    let department_map = new Map();
    let level_map = new Map();
    let sector_map = new Map();

    //let filter_dict = {};

// --- get data stored in page
    const el_data = document.getElementById("id_data");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    urls.url_archive_upload = get_attr_from_el(el_data, "data-url_archive_upload");
    urls.url_lookup_document = get_attr_from_el(el_data, "data-url_lookup_document");

    urls.url_usersetting_upload = get_attr_from_el(el_data, "data-url_usersetting_upload");

    // columns_hidden and mod_MCOL_dict.columns are declared in tables.js, they are also used in t_MCOL_Open and t_MCOL_Save
    // mod_MCOL_dict.columns contains the fields and captions that can be hidden
    // key 'all' contains fields that will be hidden in all buttons
    // key with btn name contains fields that will be hidden in this selected_btn
    // either 'all' or selected_btn are used in a page

    mod_MCOL_dict.columns.published = {
        name: "Name_ex_form",
        datepublished: "Date_submitted",
        url: "Download_Exform"
    };

    mod_MCOL_dict.columns.diplomagradelist = {
        regnumber: "Regnumber",
        datepublished: "Date_submitted",
        modifiedby: "Submitted_by",
        url: "Download_Exform"
    };
// --- get field_settings
    field_settings.published = {field_caption: ["", "Name_ex_form", "Date_submitted", "Submitted_by", "Download_Exform", ""],
                    field_names: ["select", "name", "datepublished", "modifiedby", "url", "delete"],
                    field_tags: ["div", "div", "div", "div", "a", "div"],
                    filter_tags: ["text", "text", "text",  "text", "toggle", ""],
                    field_width: ["020", "480",  "150", "180", "120", "032"],
                    field_align: ["c", "l", "c", "l", "c", "c"]};

    field_settings.diplomagradelist = {field_caption: ["", "Candidate", "Document", "Regnumber_2lines", "Created_at", "Created_by", "Download"],
                    field_names: ["select", "full_name", "doctype", "regnumber", "modifiedat", "modifiedby", "url"],
                    field_tags: ["div", "div", "div", "div", "div", "div", "a"],
                    filter_tags: ["text", "text", "text", "text", "text", "text", "toggle"],
                    field_width: ["020", "360", "090", "150", "220", "180", "120"],
                    field_align: ["c", "l", "l", "l",  "l", "l", "c"]};

    const tblHead_datatable = document.getElementById("id_tblHead_datatable");
    const tblBody_datatable = document.getElementById("id_tblBody_datatable");

// === EVENT HANDLERS ===
// === reset filter when ckicked on Escape button ===
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") { ResetFilterRows()}
        });

 // freeze table header PR2021-08-03
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
        }

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
        };

// ---  MODAL SELECT COLUMNS ------------------------------------
        const el_MCOL_btn_save = document.getElementById("id_MCOL_btn_save")
        if(el_MCOL_btn_save){
            el_MCOL_btn_save.addEventListener("click", function() {
                t_MCOL_Save(urls.url_usersetting_upload, HandleBtnSelect)}, false )
        };

// ---  MOD CONFIRM ------------------------------------
        const el_confirm_header = document.getElementById("id_modconfirm_header");
        const el_confirm_loader = document.getElementById("id_modconfirm_loader");
        const el_confirm_msg_container = document.getElementById("id_modconfirm_msg_container");
        const el_confirm_info_container = document.getElementById("id_modconfirm_info_container");
        const el_modconfirm_input_label = document.getElementById("id_modconfirm_input_label");
        const el_modconfirm_input = document.getElementById("id_modconfirm_input");
        if (el_modconfirm_input){
            el_modconfirm_input.addEventListener("keyup", function() {ModConfirm_InputKeyup(el_modconfirm_input, event)}, false);
        };

        const el_confirm_btn_cancel = document.getElementById("id_modconfirm_btn_cancel");
        const el_confirm_btn_save = document.getElementById("id_modconfirm_btn_save");
        if (el_confirm_btn_save){ el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()}) };

// ---  set selected menu button active
        const btn_clicked = document.getElementById("id_plg_page_archive");

        //console.log("btn_clicked: ", btn_clicked)
        SetMenubuttonActive(document.getElementById("id_plg_page_archive"));

    if(may_view_page){
        // period also returns emplhour_list
        const datalist_request = {
                setting: {page: "page_archive"},
                schoolsetting: {setting_key: "page_archive"},
                locale: {page: ["page_archive"]},
                examyear_rows: {get: true},
                school_rows: {get: true},
                department_rows: {get: true},
                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},

                published_rows: {get: true},
                diplomagradelist_rows: {get: true}
            };

        DatalistDownload(datalist_request);
    }
//  #############################################################################################################

//========= DatalistDownload  ===================== PR2020-07-31 PR2021-11-18
    function DatalistDownload(datalist_request, skip_messages) {
        console.log( "=== DatalistDownload ")
        console.log("request: ", datalist_request)

// ---  Get today's date and time - for elapsed time
        let startime = new Date().getTime();

// ---  show loader
        el_loader.classList.remove(cls_visible_hide)
        el_hdr_left.classList.add(cls_hide)

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

// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                el_hdr_left.classList.remove(cls_hide)

                let must_update_headerbar = false;
                let check_status = false;
                let isloaded_loc = false, isloaded_settings = false, isloaded_permits = false;

                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                    isloaded_loc = true;
                };

                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict
                    selected_btn = (setting_dict.sel_btn)
                    isloaded_settings = true;

            // ---  fill cols_hidden
                    if("cols_hidden" in setting_dict){
                        //  setting_dict.cols_hidden was dict with key 'all' or se_btn, changed to array PR2021-12-14
                        //  skip when setting_dict.cols_hidden is not an array,
                        // will be changed into an array when saving with t_MCOL_Save
                        if (Array.isArray(setting_dict.cols_hidden)) {
                             b_copy_array_noduplicates(setting_dict.cols_hidden, mod_MCOL_dict.cols_hidden);
                        };
                    };
                    must_update_headerbar = true;
                };

                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    // get_permits must come before CreateSubmenu and FiLLTbl
                    b_get_permits_from_permitlist(permit_dict);
                    isloaded_permits = true;
                    must_update_headerbar = true;
                }
                if ("schoolsetting_dict" in response) {

                };
                // both 'loc' and 'setting_dict' are needed for CreateSubmenu
                if (isloaded_loc && isloaded_settings) {CreateSubmenu()};
                if(isloaded_settings || isloaded_permits){
                    h_UpdateHeaderBar(el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);
                };
                if (!skip_messages && "messages" in response) {
                    b_show_mod_message_dictlist(response.messages);
                }
                if ("examyear_rows" in response) {
                    examyear_rows = response.examyear_rows;
                    b_fill_datamap(examyear_map, response.examyear_rows);
                };
                if ("department_rows" in response) {
                    department_rows = response.department_rows;
                    b_fill_datamap(department_map, response.department_rows)
                };
                if ("school_rows" in response)  {
                    school_rows =  response.school_rows;
                    b_fill_datamap(school_map, response.school_rows)
                };
                if ("published_rows" in response) {
                    b_fill_datadicts("published", "id", null, response.published_rows, published_dicts);
                };
                if ("diplomagradelist_rows" in response) {
                    b_fill_datadicts("diplomagradelist", "id", null, response.diplomagradelist_rows, diplomagradelist_dicts);
                };
                HandleBtnSelect(selected_btn, true);  // true = skip_upload
            },
            error: function (xhr, msg) {
// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                console.log(msg + '\n' + xhr.responseText);
            }
        });
    };  // function DatalistDownload

//=========  CreateSubmenu  ===  PR2020-07-31
    function CreateSubmenu() {
        //console.log("===  CreateSubmenu == ");
        //console.log("loc.Add_subject ", loc.Add_subject);
        //console.log("loc ", loc);

        const el_submenu = document.getElementById("id_submenu")
        AddSubmenuButton(el_submenu, loc.Lookup_diploma_gradelist, function() {ModConfirmOpen("lookup")}, ["tab_show", "tab_btn_diploma"]);

        AddSubmenuButton(el_submenu, loc.Hide_columns, function() {t_MCOL_Open("page_archive")}, [], "id_submenu_columns");


        el_submenu.classList.remove(cls_hide);

    };//function CreateSubmenu

//###########################################################################
//=========  HandleBtnSelect  ================ PR2020-09-19  PR2020-11-14 PR2023-04-18
    function HandleBtnSelect(data_btn, skip_upload) {
        //console.log( "===== HandleBtnSelect ========= ", data_btn);

        // check if data_btn exists, gave error because old btn name was still in saved setting PR2021-09-07 debug
        if (!data_btn) {data_btn = selected_btn};
        if (data_btn && ["btn_orderlist", "btn_exform", "btn_diploma"].includes(data_btn)) {
            selected_btn = data_btn;
        } else {
            selected_btn = "btn_exform";
        };

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_archive: {sel_btn: selected_btn}};
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);
        };

// ---  highlight selected button
        b_highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  show only the elements that are used in this tab
        b_show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

// ---  fill sidebar selecttable students
        //SBR_FillSelectTable();

// ---  fill datatable
        FillTblRows();

    }  // HandleBtnSelect

//=========  HandleTblRowClicked  ================ PR2020-08-03
    function HandleTblRowClicked(tr_clicked) {
        //console.log("=== HandleTblRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

// ---  get selected.student_dict
        //selected.student_pk = get_attr_from_el_int(tr_clicked, "data-pk");
        //selected.student_dict = b_get_datadict_by_integer_from_datarows(student_rows, "id", selected.student_pk);
        //console.log( "selected.student_pk: ", selected.student_pk);
        //console.log( "selected.student_dict: ", selected.student_dict);

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        //DeselectHighlightedRows(tr_clicked, cls_selected);
       //tr_clicked.classList.add(cls_selected)


// ---  deselect all highlighted rows, select clicked row
        t_tbody_selected_clear(tr_clicked.parentNode);
        t_tr_selected_set(tr_clicked);
        //t_td_selected_toggle(tr_clicked);

    }  // HandleTblRowClicked


//========= FillTblRows  ============== PR2021-06-16  PR2021-12-14
    function FillTblRows() {
        console.log( "===== FillTblRows  === ");
        //console.log( "setting_dict", setting_dict);

        const tblName = (selected_btn === "btn_diploma") ? "diplomagradelist" : "published";
        const field_setting = field_settings[tblName];
        const data_dicts = (selected_btn === "btn_diploma") ? diplomagradelist_dicts : published_dicts;
    console.log( "data_dicts", data_dicts);

// ---  get list of hidden columns
        // copy col_hidden from mod_MCOL_dict.cols_hidden
        const col_hidden = b_copy_array_to_new_noduplicates(mod_MCOL_dict.cols_hidden);

        // hide level when not level_req
        if(!setting_dict.sel_dep_level_req){col_hidden.push("lvlbase_id")};

        // hide delete btn when not req_usr is admin PR2022-11-21
        if(!permit_dict.requsr_role_admin){col_hidden.push("delete")};

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

// --- create table header
        CreateTblHeader(field_setting, col_hidden);

// --- loop through data_dicts
        if(data_dicts){
            for (const data_dict of Object.values(data_dicts)) {
                const show_row =  (selected_btn === "btn_diploma") ?
                                        // show only latest dpgl? not for now PR2023-06-21
                                        (data_dict.is_latest_dpgl || true) :
                                  (selected_btn === "btn_orderlist") ?
                                        (data_dict.filename && data_dict.filename.charAt(0).toLowerCase() ==='b') :
                                  (selected_btn === "btn_exform") ?
                                        (data_dict.filename && ["e", "v"].includes(data_dict.filename.charAt(0).toLowerCase())) :
                                        false;
                if (show_row){
                    CreateTblRow(tblName, field_setting, data_dict, col_hidden);
                };
            };
        };
// --- filter tblRows
        Filter_TableRows();
    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-07-31 PR2021-06-15 PR2021-08-02 PR2021-12-14
    function CreateTblHeader(field_setting, col_hidden) {
        console.log("===  CreateTblHeader ===== ");
        console.log("field_setting", field_setting);
        console.log("col_hidden", col_hidden);

//--- get info from selected department_map
        let sct_caption = null, has_profiel = false,  lvl_req = false, sct_req = false;
        const dep_dict = get_mapdict_from_datamap_by_tblName_pk(department_map, "department", setting_dict.sel_department_pk);
        if(dep_dict){
            has_profiel = (!!dep_dict.has_profiel);
            lvl_req = (!!dep_dict.lvl_req);
            sct_req = (!!dep_dict.sct_req);
        }

        const column_count = field_setting.field_names.length;

// +++  insert header and filter row ++++++++++++++++++++++++++++++++
        let tblRow_header = tblHead_datatable.insertRow (-1);
        let tblRow_filter = tblHead_datatable.insertRow (-1);

    // --- loop through columns
        for (let j = 0; j < column_count; j++) {
            const field_name = field_setting.field_names[j];

    // skip columns if in columns_hidden
            if (!col_hidden.includes(field_name)){

        // --- get field_caption from field_setting, display 'Profiel' in column sctbase_id if has_profiel
                const key = field_setting.field_caption[j];
                const field_caption = (field_name === "sctbase_id" && has_profiel) ? loc.Profile : (loc[key]) ? loc[key] : key;
                const filter_tag = field_setting.filter_tags[j];
                const class_width = "tw_" + field_setting.field_width[j] ;
                const class_align = "ta_" + field_setting.field_align[j];

// ++++++++++ insert columns in header row +++++++++++++++
        // --- add th to tblRow_header
                let th_header = document.createElement("th");
        // --- add div to th, margin not working with th
                    const el_header = document.createElement("div");
        // --- add innerText to el_header
                    el_header.innerText = field_caption;
        // --- add width, text_align, right padding in examnumber
                    th_header.classList.add(class_width, class_align);
                    el_header.classList.add(class_width, class_align);
                    // if(field_name === "examnumber"){el_header.classList.add("pr-2")};

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

        // --- add EventListener to el_filter / th_filter
                if (filter_tag === "select") {
                    th_filter.addEventListener("click", function(event){HandleFilterSelect(el_filter)});
                    add_hover(th_filter);
                } else if (filter_tag === "text") {
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
                // el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");
                th_filter.appendChild(el_filter)
                tblRow_filter.appendChild(th_filter);
            }  //  if (!columns_hidden[field_name])
        }  // for (let j = 0; j < column_count; j++)
    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09 PR2021-06-21 PR2021-12-14
    function CreateTblRow(tblName, field_setting, data_dict, col_hidden) {
        //console.log("=========  CreateTblRow =========", tblName);
        //console.log("data_dict", data_dict);

        const field_names = field_setting.field_names;
        const field_tags = field_setting.field_tags;
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;

// ---  lookup index where this row must be inserted
        const ob1 = (selected_btn === "btn_diploma") ?
                        (data_dict.full_name) ? data_dict.full_name : "" :
                        (data_dict.name) ? data_dict.name : "";
        const ob2 = (selected_btn === "btn_diploma" && data_dict.doctype) ? (data_dict.doctype) : "zz";
        const ob3 = (selected_btn === "btn_diploma") ? (data_dict.modifiedat) : "";
        const row_index = b_recursive_tblRow_lookup(tblBody_datatable, setting_dict.user_lang, ob1, ob2, ob3, false, false, true);

// --- insert tblRow into tblBody at row_index
        const tblRow = tblBody_datatable.insertRow(row_index);
        if (data_dict.mapid) {tblRow.id = data_dict.mapid};

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

    // skip columns if in columns_hidden
            if (!col_hidden.includes(field_name)){
                const field_tag = field_tags[j];
                const class_width = "tw_" + field_width[j];
                const class_align = "ta_" + field_align[j];

    // --- insert td element,
                const td = tblRow.insertCell(-1);

    // --- create element with tag from field_tags
                const el = document.createElement(field_tag);

                if (field_name === "url"){
                    //el.innerHTML = "download &#8681;";
                    el.innerHTML = "&emsp;&emsp;&emsp;&emsp;&#8681;&emsp;&emsp;&emsp;&emsp;";

                } else if (field_name === "delete"){
                    el.classList.add("delete_0_1")
                    add_hover(el, "delete_0_2", "delete_0_1")
                };

        // --- add data-field attribute
                el.setAttribute("data-field", field_name);

        // --- make row gray when not is_latest_dpgl PR2023-06-19
                if (!data_dict.is_latest_dpgl) {
                    el.classList.add("text-muted");
                };

        // --- add  text_align
                el.classList.add(class_width, class_align);

        // --- append element
                td.appendChild(el);

    // --- add EventListener to td
                if (["select", "name", "datepublished", "url"].includes(field_name)){
                    //td.addEventListener("click", function() {MSTUD_Open(el)}, false)
                    //td.classList.add("pointer_show");
                    add_hover(td);
                } else if (field_name === "delete"){
                    td.addEventListener("click", function() {ModConfirmOpen("delete", tblRow)}, false);
                };
    // --- put value in field
               UpdateField(el, data_dict)
           }  // if (!columns_hidden[field_name])
        }  // for (let j = 0; j < 8; j++)
        return tblRow
    };  // CreateTblRow

//=========  UpdateTblRow  ================ PR2020-08-01
    function UpdateTblRow(tblRow, tblName, data_dict) {
        //console.log("=========  UpdateTblRow =========");
        if (tblRow && tblRow.cells){
            for (let i = 0, td; td = tblRow.cells[i]; i++) {
                UpdateField(td.children[0], data_dict);
            }
        }
    };  // UpdateTblRow

//=========  UpdateField  ================ PR2020-08-16 PR2021-06-16
    function UpdateField(el_div, data_dict) {
        //console.log("=========  UpdateField =========");
        //console.log("data_dict", data_dict);

        if(el_div){
            const field_name = get_attr_from_el(el_div, "data-field");
            const fld_value = (data_dict[field_name]) ? data_dict[field_name] : null;

        //console.log("field_name", field_name);
        //console.log("fld_value", fld_value);

            if(field_name){
                let inner_text = null, h_ref = null, title_text = null, filter_value = null;
                if (field_name === "select") {

                } else if (field_name === "url"){
                    if (fld_value){
                        el_div.href = fld_value;
                    } else {
                        el_div.innerHTML = "&emsp;&emsp;&emsp;&emsp;-&emsp;&emsp;&emsp;&emsp;";
                        el_div.title = loc.File_not_found;
                    }

                } else if (field_name === "datepublished"){
                    const date_formatted = format_date_from_dateISO(loc, fld_value);

                    inner_text = (date_formatted) ? date_formatted : "\n";
                    filter_value = date_formatted;

                } else if (field_name === "doctype"){
                    inner_text = (fld_value === "dp") ? loc.diploma : (fld_value === "gl") ? loc.grade_list :"\n";
                    filter_value = inner_text;

                } else if (field_name === "regnumber"){
                    inner_text = (fld_value) ? fld_value : "\n";
                    filter_value = (fld_value) ? fld_value.toString().toLowerCase() : null;
                    if (fld_value) {
                        const title_list =  [
                            loc.regnumber_info[0],
                            fld_value.substring(0,2) + " " + loc.regnumber_info[1],
                            fld_value.substring(2,5) + " " + loc.regnumber_info[2],
                            fld_value.substring(5,6) + "   " + loc.regnumber_info[3],
                            fld_value.substring(6,12) + " " + loc.regnumber_info[4]
                        ];
                        if (fld_value.slice(-1) === 'b') {
                            title_list.push(loc.regnumber_info[5])
                        }
                        title_text = title_list.join("\n");
                    };

                } else if (["full_name",  "name", , "modifiedby"].includes(field_name)){
                    // put hard return in el_div, otherwise green border doesnt show in update PR2021-06-16
                    inner_text = (fld_value) ? fld_value : "\n";
                    filter_value = (fld_value) ? fld_value.toString().toLowerCase() : null;

                } else if (field_name === "modifiedat"){
                    const modified_dateJS = parse_dateJS_from_dateISO(fld_value);
                    inner_text = format_datetime_from_datetimeJS(loc, modified_dateJS);
                    filter_value = inner_text;
                };

// ---  put value in innerText and title
                if (el_div.tagName === "A"){
                    // happens above
                } else {
                    el_div.innerHTML = inner_text;
                };

    // ---  add attribute title
                add_or_remove_attr (el_div, "title", !!title_text, title_text);
    // ---  add attribute filter_value
                add_or_remove_attr (el_div, "data-filter", !!filter_value, filter_value);

            };  // if(field_name)
        };  // if(el_div)
    };  // UpdateField

//========= UploadChanges  ============= PR2022-11-03
    // only called by ModConfirmSave
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

                    if("updated_published_rows" in response){
                        ModConfirmResponseNEW(response);
                    };

                    if("lookup_document_has_error" in response){
                        ModConfirmResponseLookupDocument(response);
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


// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2022-11-02 PR2024-07-07
    function ModConfirmOpen(mode, tblRow) {
        console.log(" -----  ModConfirmOpen   ----")
        //console.log("mode", mode)
        //console.log("tblRow", tblRow)
        // valuesof mode are: "delete", "lookup"

// reset  modal
         add_or_remove_class(document.getElementById("id_mod_confirm_size"), "modal-lg", (mode === "lookup"), "modal-md");

        el_confirm_header.innerText = null;
        el_confirm_msg_container.innerHTML = null;
        el_confirm_info_container.innerHTML = null;

        el_modconfirm_input_label.innerText = null;
        el_modconfirm_input.value = null;
        add_or_remove_class (el_modconfirm_input.parentNode, cls_hide, (mode !== "lookup"));

        el_confirm_loader.classList.add(cls_hide);

        add_or_remove_class (el_confirm_btn_save, cls_hide, false);
        el_confirm_btn_save.disabled = (mode === "lookup");

        el_confirm_btn_cancel.innerText = loc.Cancel;

        mod_dict = {mode: mode};

        if (mode === "delete"){
            el_confirm_header.innerText = loc.Delete_document;

// --- get existing data_dict from data_rows
            const pk_int = get_attr_from_el_int(tblRow, "data-pk");
            const data_dict = published_dicts[pk_int];

// skip if no tblRow selected or if exam has no envelopbundle
            if (!isEmpty(data_dict)){
                const tblName = "published";
                mod_dict = {
                    mode: mode,
                    table: tblName,
                    published_pk: data_dict.id,
                    map_id: data_dict.mapid,
                };
                const msg_html = ["<div class='mx-2'>",
                                "<p>", loc.This_document_willbe_deleted,  ":</p><p class='pl-3'>", data_dict.name, "</p>",
                                "<p>", loc.Do_you_want_to_continue, "</p>",
                             "</div>"].join("")

                el_confirm_loader.classList.add(cls_hide)

                el_confirm_msg_container.className = "p-3";
                el_confirm_msg_container.innerHTML = msg_html;

                el_confirm_btn_save.innerText = loc.Yes_delete;

                el_confirm_btn_cancel.innerText = loc.No_cancel;
                add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", true, "btn-primary");


    // set focus to cancel button
                set_focus_on_el_with_timeout(el_confirm_btn_save);
        // show modal
                $("#id_mod_confirm").modal({backdrop: true});
            };

        } else if (mode === "lookup"){
                el_confirm_header.innerText = loc.Lookup_diploma_gradelist;
                const msg_html = ["<div class='mx-2 px-2 pt-2'>",
                        loc.Enter_registrationnumber, "<br>",  loc.AWP_will_lookup_document,
                     "</div>",
                     ].join("");
                el_confirm_msg_container.innerHTML = msg_html;

                el_modconfirm_input_label.innerText = loc.Regnumber + ":";

    // set focus to input element
                set_focus_on_el_with_timeout(el_modconfirm_input);
                // show modal
                $("#id_mod_confirm").modal({backdrop: true});
        };
    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2021-08-22 PR2022-10-10
    function ModConfirmSave() {
        console.log(" --- ModConfirmSave --- ");
        console.log("mod_dict: ", mod_dict);
        let close_modal_with_timout = false;

        if (mod_dict.mode === "delete"){
            // remove msg
            el_confirm_msg_container.innerHTML = null;
            // show loader
            el_confirm_loader.classList.remove(cls_hide);
            // hide save btn
            el_confirm_btn_save.classList.add(cls_hide);
            // rename cancel btn
            el_confirm_btn_cancel.innerText = loc.Close;

            let upload_dict = {
                table: mod_dict.table,
                mode: "delete",
                published_pk: mod_dict.published_pk
            };
            UploadChanges(upload_dict, urls.url_archive_upload);

            const tblRow = document.getElementById(mod_dict.map_id)
            ShowClassWithTimeout(tblRow, "tsa_tr_error")

        } else if (mod_dict.mode === "lookup"){

            // remove msg
            el_confirm_msg_container.innerHTML = null;
            el_confirm_info_container.innerHTML = null;
            // show loader
            add_or_remove_class(el_confirm_loader, cls_hide, false);

            // hide save btn, input element
            add_or_remove_class(el_confirm_btn_save, cls_hide, false);
            //add_or_remove_class(el_modconfirm_input.parentNode, cls_hide, true);

            // rename cancel btn
            //el_confirm_btn_cancel.innerText = loc.Close;

            let upload_dict = {
                mode: "lookup_document",
                regnumber:  el_modconfirm_input.value
            };
            UploadChanges(upload_dict, urls.url_lookup_document);

        };

    };  // ModConfirmSave

//=========  ModConfirmResponseNEW  ================ PR2022-11-03
    function ModConfirmResponseNEW(response) {
        // only called by UploadChanges after ModConfirmSave
        console.log(" --- ModConfirmResponseNEW --- ");
        console.log("response: ", response);

    // - hide loader
        el_confirm_loader.classList.add(cls_hide);
        if ("message_list" in response) {
            const msg_list = response.message_list;
        console.log("msg_list: ", msg_list, typeof msg_list);
            if (msg_list && msg_list.length){
                // msg_list only contains 1 message
                const msg_dict = msg_list[0];
                if(msg_dict){
                    el_confirm_msg_container.classList.add(msg_dict.class, "m-4");
                    el_confirm_msg_container.innerHTML = msg_dict.msg_html;
                };
            };
        } else {
            $("#id_mod_confirm").modal("hide");
            RefreshDataRows("published", response.updated_published_rows, published_rows, true); // true = is_update
        };
    };  // ModConfirmResponseNEW

//=========  ModConfirmResponseLookupDocument  ================ PR2024-07-07
    function ModConfirmResponseLookupDocument(response) {
        // only called by UploadChanges after ModConfirmSave
        console.log(" --- ModConfirmResponseLookupDocument --- ");
        console.log("response: ", response);

    // - hide loader
        el_confirm_loader.classList.add(cls_hide);

        if ("msg_html" in response) {
            el_confirm_info_container.innerHTML = response.msg_html;
            add_or_remove_class(el_confirm_info_container, cls_hide, false);
        } else {
            $("#id_mod_confirm").modal("hide");
        };
    };  // ModConfirmResponseLookupDocument

//=========  ModConfirm_InputKeyup ================ PR2024=07-07
    function ModConfirm_InputKeyup(el_modconfirm_input, event) {
        console.log(" --- ModConfirm_InputKeyup --- ");

        if (el_confirm_btn_save){
            const save_btn_enabled = (el_modconfirm_input.value && el_modconfirm_input.value.length >= 12);
            el_confirm_btn_save.disabled = !save_btn_enabled;

            if (event.key === "Enter" && !event.shiftKey) {
                ModConfirmSave();
            };
        };
    };  // ModConfirm_InputKeyup
////////////////////////

//=========  RefreshDataRows  ================ R2022-11-03
    function RefreshDataRows(tblName, update_rows, data_rows, is_update, skip_show_ok) {
        console.log(" --- RefreshDataRows  ---");
        console.log("is_update", is_update);
        console.log("update_rows", update_rows);

        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length
        if (update_rows && update_rows.length ) {
            const field_setting = field_settings[tblName];
            for (let i = 0, update_dict; update_dict = update_rows[i]; i++) {
                RefreshDatarowItem(tblName, field_setting, data_rows, update_dict, skip_show_ok);
            }
        } else if (!is_update) {
            // empty the data_rows when update_rows is empty PR2021-01-13 debug forgot to empty data_rows
            // PR2021-03-13 debug. Don't empty de data_rows when is update. Returns [] when no changes made
           data_rows = [];
        }
    }  //  RefreshDataRows

//=========  RefreshDatarowItem  ================ PR2022-11-03
    function RefreshDatarowItem(tblName, field_setting, data_rows, update_dict) {
        console.log(" --- RefreshDatarowItem  ---");
        console.log("tblName", tblName);
        console.log("field_setting", field_setting);
        console.log("update_dict", update_dict);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);

// ---  get list of hidden columns
            const col_hidden = b_copy_array_to_new_noduplicates(mod_MCOL_dict.cols_hidden);

// ---  get list of columns that are not updated because of errors
            const error_columns = (update_dict.err_fields) ? update_dict.err_fields : [];

// --- get existing data_dict from data_rows
            const pk_int = (update_dict && update_dict.id) ? update_dict.id : null;
            const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);
            const data_dict = (!isEmpty(found_dict)) ? found_dict : null;
            const datarow_index = index;
    console.log("pk_int", pk_int);
    console.log("data_dict", data_dict);

// ++++ deleted ++++
            if(is_deleted){
                // delete row from data_rows. Splice returns array of deleted rows
                const deleted_row_arr = data_rows.splice(datarow_index, 1)
                const deleted_row_dict = deleted_row_arr[0];
    //console.log("deleted_row_dict", deleted_row_dict);
    //console.log("deleted_row_dict.mapid", deleted_row_dict.mapid);

    //--- delete tblRow
                if(deleted_row_dict && deleted_row_dict.mapid){
                    const tblRow_tobe_deleted = document.getElementById(deleted_row_dict.mapid);
    //console.log("tblRow_tobe_deleted", tblRow_tobe_deleted);
                    if (tblRow_tobe_deleted ){
                        tblRow_tobe_deleted.parentNode.removeChild(tblRow_tobe_deleted);
                    };
                };
// --- subtract 1 from item_count
                selected.item_count -= 1;
// ---  show total in sidebar
                t_set_sbr_itemcount_txt(loc, selected.item_count, loc.Candidate, loc.Candidates, setting_dict.user_lang);
            };  // if(is_deleted)
        //console.log("student_rows", student_rows);
        };  // if(!isEmpty(update_dict))
    };  // RefreshDatarowItem

////////////////////////

//###########################################################################
// +++++++++++++++++ FILTER TABLE ROWS ++++++++++++++++++++++++++++++++++++++

//========= HandleFilterKeyup  ================= PR2021-06-16
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
        //console.log( "col_index", col_index);
        //console.log( "filter_tag", filter_tag);
        //console.log( "field_name", field_name);

    // - get current value of filter from filter_dict, set to '0' if filter doesn't exist yet
        const filter_array = (col_index in filter_dict) ? filter_dict[col_index] : [];
        const filter_value = (filter_array[1]) ? filter_array[1] : "0";
        //console.log( "filter_array", filter_array);
        //console.log( "filter_value", field_name);

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

//========= HandleFilterSelect  =============== PR2021-06-16
    function HandleFilterSelect(el_input) {
        //console.log( "===== HandleFilterSelect  ========= ");
        //console.log( "el_input", el_input);

    // - get col_index and filter_tag from  el_input
        // PR2021-05-30 debug: use cellIndex instead of attribute data-colindex,
        // because data-colindex goes wrong with hidden columns
        // was:  const col_index = get_attr_from_el(el_input, "data-colindex")
        const col_index = el_input.parentNode.cellIndex;
        //console.log( "col_index", col_index);

    // - get filter_tag from  el_input
        const filter_tag = get_attr_from_el(el_input, "data-filtertag")
        const field_name = get_attr_from_el(el_input, "data-field")
        //console.log( "filter_tag", filter_tag);
        //console.log( "field_name", field_name);

    // - get current value of filter from filter_dict, set to '0' if filter doesn't exist yet
        const filter_array = (col_index in filter_dict) ? filter_dict[col_index] : [];
        const filter_value = (filter_array[1]) ? filter_array[1] : "0";
        //console.log( "filter_array", filter_array);
        //console.log( "filter_value", field_name);

        let new_value = "0", html_str = null;

        // default filter triple '0'; is show all, '1' is show tickmark, '2' is show without tickmark
// - toggle filter value
        new_value = (filter_value === "1") ? "0" : "1";
// - set el_input.innerHTML
        el_input.innerHTML = (new_value === "1") ? "&#9658;" : null
        if (new_value === "1") {
            // set all visible students selected
             let filter_toggle_elements = tblBody_datatable.querySelectorAll("tr:not(.display_hide:not(.tsa_tr_selected)");
        //console.log("filter_toggle_elements", filter_toggle_elements);
            let count = 0;
             for (let i = 0, tr, el; tr = filter_toggle_elements[i]; i++) {
                tr.classList.add(cls_selected)
                el = tr.cells[0].children[0];
                if (el){ el.innerHTML = "&#9658;"};
                count += 1;
             }
        //console.log("made se;lected: count", count);

        } else {
            // unselect all visible student
             // set all visible students selected
             //let filter_toggle_elements = tblBody_datatable.querySelectorAll("tr.tsa_tr_selected");
             let filter_toggle_elements = tblBody_datatable.querySelectorAll("tr:not(.display_hide).tsa_tr_selected");
        //console.log("filter_toggle_elements", filter_toggle_elements);
            let count = 0;
            for (let i = 0, tr, el; tr = filter_toggle_elements[i]; i++) {
                tr.classList.remove(cls_selected)
                el = tr.cells[0].children[0];
                if (el){ el.innerHTML = null};
                count += 1;
            }
        //console.log("removed selected: count", count);
        }
    // - put new filter value in filter_dict
        // filter_dict = { 0: ['select', '2'], 2: ['text', 'f', ''] }

        filter_dict[col_index] = [filter_tag, new_value]
        //console.log( "filter_dict", filter_dict);

        Filter_TableRows();

    };  // HandleFilterSelect

//========= Filter_TableRows  ==================================== PR2020-08-17
    function Filter_TableRows() {
        //console.log( "===== Filter_TableRows  ========= ");

        const tblName_settings = "published";
        const field_setting = field_settings[tblName_settings];
        const filter_tags = field_setting.filter_tags;


// ---  loop through tblBody.rows
        for (let i = 0, tblRow, show_row; tblRow = tblBody_datatable.rows[i]; i++) {
            show_row = t_Filter_TableRow_Extended(filter_dict, tblRow);
            add_or_remove_class(tblRow, cls_hide, !show_row);
        }

    }; // Filter_TableRows

//========= ResetFilterRows  ====================================
    function ResetFilterRows() {  // PR2019-10-26 PR2020-06-20
       //console.log( "===== ResetFilterRows  ========= ");

        selected.student_pk = null;
        selected.student_dict = {};
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
// +++++++++++++++++ MODAL SELECT EXAMYEAR OR DEPARTMENT  ++++++++++++++++++++
// functions are in table.js, except for MSED_Response

//=========  MSED_Response  ================ PR2020-12-18 PR2021-05-10
    function MSED_Response(new_setting) {
        console.log( "===== MSED_Response ========= ");
        console.log( "new_setting", new_setting);

// ---  upload new selected_pk
        new_setting.page = setting_dict.sel_page;
// also retrieve the tables that have been changed because of the change in examyear / dep
        const datalist_request = {
                setting: new_setting,
                student_rows: {get: true},
                studentsubject_rows: {get: true},
                grade_rows: {get: true},
                schemeitem_rows: {get: true},
                schoolsetting: {setting_key: "import_student"}
            };
        DatalistDownload(datalist_request);

    }  // MSED_Response


//###########################################################################
//=========  MSSSS_Response  ================ PR2021-01-23 PR2021-02-05 PR2021-07-26
    function MSSSS_Response(modalName, tblName, selected_dict, selected_pk) {
        //console.log( "===== MSSSS_Response ========= ");
        //console.log( "selected_pk", selected_pk);
        //console.log( "selected_code", selected_code);
        //console.log( "selected_name", selected_name);

        // arguments are set in t_MSSSS_Save_NEW: MSSSS_Response(modalName, tblName, selected_dict, selected_pk_int)

// ---  upload new setting and refresh page
        const datalist_request = {
                setting: {page: "page_archive",
                          sel_schoolbase_pk: selected_pk  },
                school_rows: {get: true},
                department_rows: {get: true},
                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},
                student_rows: {get: true},
                subject_rows: {get: true},
                studentsubject_rows: {get: true},
                scheme_rows: {cur_dep_only: true},
            };

        DatalistDownload(datalist_request);

    }  // MSSSS_Response

//=========  SBR_show_all  ================ PR2021-11-18
    function SBR_show_all(FillTblRows) {
        console.log("===== SBR_show_all =====");

        setting_dict.sel_lvlbase_pk = null;
        setting_dict.sel_lvlbase_code = null;

        setting_dict.sel_sctbase_pk = null;
        setting_dict.sel_sctbase_code = null;

        setting_dict.sel_classname = null;

        setting_dict.sel_student_pk = null;

        const el_SBR_select_department = document.getElementById("id_SBR_select_department");
        const el_SBR_select_level = document.getElementById("id_SBR_select_level");
        const el_SBR_select_sector = document.getElementById("id_SBR_select_sector");
        const el_SBR_select_class = document.getElementById("id_SBR_select_class");

        if (el_SBR_select_department){ el_SBR_select_department.value = null};
        if (el_SBR_select_level){ el_SBR_select_level.value = null};
        if (el_SBR_select_sector){ el_SBR_select_sector.value = null};
        if (el_SBR_select_class){ el_SBR_select_class.value = "0"};

// ---  upload new setting
        const selected_pk_dict = {};
        if (el_SBR_select_department){selected_pk_dict.sel_depbase_pk = null};
        if (el_SBR_select_level){selected_pk_dict.sel_lvlbase_pk = null};
        if (el_SBR_select_sector){selected_pk_dict.sel_sctbase_pk = null};
        if (el_SBR_select_class){selected_pk_dict.sel_classname = null};

        const new_setting = {page: "page_archive", sel_lvlbase_pk: null, sel_sctbase_pk: null };
        const datalist_request = {
                setting: new_setting,
                student_rows: {cur_dep_only: true}
            };
        DatalistDownload(datalist_request, true); // true = skip_message

    }  // SBR_show_all


})  // document.addEventListener('DOMContentLoaded', function()