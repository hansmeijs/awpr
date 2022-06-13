// PR2022-03-09 added

// PR2021-07-23  declare variables outside function to make them global variables

// selected_btn is also used in t_MCOL_Open
let selected_btn = "btn_exform";

let setting_dict = {};
let permit_dict = {};
let loc = {};
let urls = {};

let selected = {};

let school_rows = [];
let published_rows = [];

const field_settings = {};

document.addEventListener('DOMContentLoaded', function() {
    "use strict";

// ---  check if user has permit to view this page. If not: el_loader does not exist PR2020-10-02
    const el_loader = document.getElementById("id_loader");
    const el_hdr_left = document.getElementById("id_header_left");
    const may_view_page = (!!el_loader);

    const cls_hide = "display_hide";
    const cls_hover = "tr_hover";
    const cls_visible_hide = "visibility_hide";
    const cls_selected = "tsa_tr_selected";

// ---  id of selected customer and selected order
    // declared as global: let selected_btn = "btn_exform";
    //let setting_dict = {};
    //let permit_dict = {};

    let mod_dict = {};
    let mod_MSTUD_dict = {};

    let examyear_map = new Map();
    let school_map = new Map();
    // PR2020-12-26 These variable defintions are moved to import.js, so they can also be used in that file
    let department_map = new Map();
    let level_map = new Map();
    let sector_map = new Map();

    let filter_dict = {};

// --- get data stored in page
    const el_data = document.getElementById("id_data");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");

    // columns_hidden and columns_tobe_hidden are declared in tables.js, they are also used in t_MCOL_Open and t_MCOL_Save
    // columns_tobe_hidden contains the fields and captions that can be hidden
    // key 'all' contains fields that will be hidden in all buttons
    // key with btn name contains fields that will be hidden in this selected_btn
    // either 'all' or selected_btn are used in a page

    columns_tobe_hidden.all = {
        name: "Name_ex_form", datepublished: "Date_submitted", url: "Download_Exform"
    };

// --- get field_settings
    const field_settings = {
        published: {field_caption: ["", "Name_ex_form", "Date_submitted", "Download_Exform"],
                    field_names: ["select", "name", "datepublished", "url"],
                    field_tags: ["div", "div", "div", "a"],
                    filter_tags: ["text", "text","text", "toggle"],
                    field_width: ["020", "480",  "150", "120"],
                    field_align: ["c", "l", "c", "c"]}
        };

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
        }
        if (el_hdrbar_department){
            el_hdrbar_department.addEventListener("click", function() {
                t_MSED_Open(loc, "department", department_map, setting_dict, permit_dict, MSED_Response)}, false );
        }
        if (el_hdrbar_school){
            el_hdrbar_school.addEventListener("click",
                function() {t_MSSSS_Open(loc, "school", school_rows, false, setting_dict, permit_dict, MSSSS_Response)}, false );
        }

// ---  MODAL SELECT COLUMNS ------------------------------------
        const el_MCOL_btn_save = document.getElementById("id_MCOL_btn_save")
        if(el_MCOL_btn_save){
            el_MCOL_btn_save.addEventListener("click", function() {
                t_MCOL_Save(urls.url_usersetting_upload, HandleBtnSelect)}, false )
        };

// ---  set selected menu button active
        const btn_clicked = document.getElementById("id_plg_page_archive")

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

                published_rows: {get: true}
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
                    b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);
                };
                if (!skip_messages && "messages" in response) {
                    b_show_mod_message_dictlist(response.messages);
                }
                if ("examyear_rows" in response) { b_fill_datamap(examyear_map, response.examyear_rows)};
                if ("school_rows" in response)  {
                    school_rows =  response.school_rows;
                    b_fill_datamap(school_map, response.school_rows)};
                if ("department_rows" in response) {
                    b_fill_datamap(department_map, response.department_rows)
                    };
                if ("published_rows" in response) {
                    published_rows = response.published_rows;
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
        console.log("===  CreateSubmenu == ");
        //console.log("loc.Add_subject ", loc.Add_subject);
        //console.log("loc ", loc);

        const el_submenu = document.getElementById("id_submenu")
        //AddSubmenuButton(el_submenu, loc.Hide_columns, function() {t_MCOL_Open("page_archive")}, [], "id_submenu_columns");
        //el_submenu.classList.remove(cls_hide);

    };//function CreateSubmenu

//###########################################################################
//=========  HandleBtnSelect  ================ PR2020-09-19  PR2020-11-14
    function HandleBtnSelect(data_btn, skip_upload) {
        console.log( "===== HandleBtnSelect ========= ", data_btn);

        // check if data_btn exists, gave error because old btn name was still in saved setting PR2021-09-07 debug
        if (!data_btn) {data_btn = selected_btn};
        if (data_btn && ["btn_exform", "btn_diploma"].includes(data_btn)) {
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
        t_td_selected_clear(tr_clicked.parentNode);
        t_td_selected_set(tr_clicked);
        //t_td_selected_toggle(tr_clicked);

    }  // HandleTblRowClicked


//========= FillTblRows  ============== PR2021-06-16  PR2021-12-14
    function FillTblRows() {
        console.log( "===== FillTblRows  === ");
        console.log( "setting_dict", setting_dict);

        const tblName = "published";
        const field_setting = field_settings[tblName];
        const data_rows = published_rows;
        console.log( "data_rows", data_rows);

// ---  get list of hidden columns
        // copy col_hidden from mod_MCOL_dict.cols_hidden
        const col_hidden = [];
        b_copy_array_noduplicates(mod_MCOL_dict.cols_hidden, col_hidden)
        // hide level when not level_req
        if(!setting_dict.sel_dep_level_req){col_hidden.push("lvlbase_id")};

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

// --- create table header
        CreateTblHeader(field_setting, col_hidden);

// --- loop through data_rows
        if(data_rows && data_rows.length){
            for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
                CreateTblRow(tblName, field_setting, data_dict, col_hidden);
            };
        };
// --- filter tblRows
        Filter_TableRows();
    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-07-31 PR2021-06-15 PR2021-08-02 PR2021-12-14
    function CreateTblHeader(field_setting, col_hidden) {
        //console.log("===  CreateTblHeader ===== ");
        //console.log("field_setting", field_setting);
        //console.log("col_hidden", col_hidden);

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
                const field_caption = (field_name === "sctbase_id" && has_profiel) ? loc.Profiel : (loc[key]) ? loc[key] : key;
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
        console.log("=========  CreateTblRow =========", tblName);
        console.log("data_dict", data_dict);

        const field_names = field_setting.field_names;
        const field_tags = field_setting.field_tags;
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;

// ---  lookup index where this row must be inserted
        const ob1 = (data_dict.name) ? data_dict.name : "";
        const row_index = b_recursive_tblRow_lookup(tblBody_datatable, setting_dict.user_lang, ob1);

// --- insert tblRow into tblBody at row_index
        const tblRow = tblBody_datatable.insertRow(row_index);
        if (data_dict.mapid) {tblRow.id = data_dict.mapid};

// --- add data attributes to tblRow
        tblRow.setAttribute("data-pk", data_dict.id);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);

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
                };
        // --- add data-field attribute
                el.setAttribute("data-field", field_name);

        // --- add  text_align
                el.classList.add(class_width, class_align);

        // --- append element
                td.appendChild(el);

    // --- add EventListener to td
                if (["select", "name", "datepublished", "url"].includes(field_name)){
                    //td.addEventListener("click", function() {MSTUD_Open(el)}, false)
                    //td.classList.add("pointer_show");
                    add_hover(td);
                }
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
        console.log("data_dict", data_dict);

        if(el_div){
            const field_name = get_attr_from_el(el_div, "data-field");
            const fld_value = (data_dict[field_name]) ? data_dict[field_name] : null;

        console.log("field_name", field_name);
        console.log("fld_value", fld_value);

            if(field_name){
                let inner_text = null, h_ref = null, filter_value = null;
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


                } else if (field_name === "name"){
                    // put hard return in el_div, otherwise green border doesnt show in update PR2021-06-16
                    inner_text = (fld_value) ? fld_value : "\n";
                    filter_value = (fld_value) ? fld_value.toString().toLowerCase() : null;
                }

// ---  put value in innerText and title
                if (el_div.tagName === "A"){
                    // happens above
                } else {
                    el_div.innerHTML = inner_text;
                };

    // ---  add attribute filter_value
                add_or_remove_attr (el_div, "data-filter", !!filter_value, filter_value);

            }  // if(field_name)
        }  // if(el_div)
    };  // UpdateField

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

                    if("messages" in response){
                        b_show_mod_message_dictlist(response.messages);
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
            show_row = t_ShowTableRowExtended(filter_dict, tblRow);
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
    function MSSSS_Response(tblName, selected_dict, selected_pk) {
        //console.log( "===== MSSSS_Response ========= ");
        //console.log( "selected_pk", selected_pk);
        //console.log( "selected_code", selected_code);
        //console.log( "selected_name", selected_name);

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
        setting_dict.sel_level_abbrev = null;

        setting_dict.sel_sctbase_pk = null;
        setting_dict.sel_sector_abbrev = null;

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