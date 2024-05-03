// PR2023-04-18 added

const published_dicts = {};
//const field_settings = {};  // PR2023-04-20 made global

document.addEventListener('DOMContentLoaded', function() {
    "use strict";

// ---  check if user has permit to view this page. If not: el_loader does not exist PR2020-10-02
    const el_loader = document.getElementById("id_loader");
    const el_hdr_left = document.getElementById("id_header_left");
    const may_view_page = (!!el_loader);

    let col_hidden = [];
    const mod_dict = {};
    const mod_MEXPAPER_dict = {};

    let examyear_map = new Map();

    const max_file_size_Mb = 5;

// --- get data stored in page
    const el_data = document.getElementById("id_data");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    urls.url_usersetting_upload = get_attr_from_el(el_data, "data-url_usersetting_upload");
    urls.url_exampaper_upload = get_attr_from_el(el_data, "data-url_exampaper_upload");

    // columns_hidden and mod_MCOL_dict.columns are declared in tables.js, they are also used in t_MCOL_Open and t_MCOL_Save
    // mod_MCOL_dict.columns contains the fields and captions that can be hidden
    // key 'all' contains fields that will be hidden in all buttons
    // key with btn name contains fields that will be hidden in this selected_btn
    // either 'all' or selected_btn are used in a page

    mod_MCOL_dict.columns.all = {
        name: "Name_ex_form", datepublished: "Date_submitted", url: "Download_Exform"
    };

// --- get field_settings
    field_settings.btn_exampaper = {field_caption: ["", "Document_name", "Date_published", "Published_by", "Download"],
                    field_names: ["select", "filename", "datepublished", "school_name", "url"],
                    field_tags: ["div", "div", "div", "div", "a"],
                    filter_tags: ["text", "text", "text",  "text", "toggle"],
                    field_width: ["020", "420",  "180", "300", "120"],
                    field_align: ["c", "l", "r", "l", "c"]};

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

// ---  MODAL SELECT COLUMNS ------------------------------------
        const el_MCOL_btn_save = document.getElementById("id_MCOL_btn_save")
        if(el_MCOL_btn_save){
            el_MCOL_btn_save.addEventListener("click", function() {
                t_MCOL_Save(urls.url_usersetting_upload, HandleBtnSelect)}, false )
        };


// ---  MODAL EXAM PAPER --
        const el_MEXPAPER_input_title = document.getElementById("id_MEXPAPER_input_title");
        if (el_MEXPAPER_input_title){
            el_MEXPAPER_input_title.addEventListener("change", function() {MEXPAPER_input_change(el_MEXPAPER_input_title)}, false );
        };
        const el_MEXPAPER_input_date_published = document.getElementById("id_MEXPAPER_input_date_published");
        if (el_MEXPAPER_input_date_published){
            el_MEXPAPER_input_date_published.addEventListener("change", function() {MEXPAPER_input_change(el_MEXPAPER_input_date_published)}, false );
        };



        const el_MEXPAPER_input_message = document.getElementById("id_MEXPAPER_input_message");
        if (el_MEXPAPER_input_message){
            el_MEXPAPER_input_message.addEventListener("keyup", function() {MEXPAPER_input_Keyup()}, false );
        };

        const el_MEXPAPER_filedialog = document.getElementById("id_MEXPAPER_filedialog");
        if (el_MEXPAPER_filedialog){
            el_MEXPAPER_filedialog.addEventListener("change", function() {MEXPAPER_HandleFiledialog(el_MEXPAPER_filedialog)}, false)};

        const el_MEXPAPER_msg_container = document.getElementById("id_MEXPAPER_msg_container")

// ---  display sel_filename in elid_MEXPAPER_filename, make btn 'outline' when filename exists
        const el_MEXPAPER_filename = document.getElementById("id_MEXPAPER_filename");

        const el_MEXPAPER_btn_filedialog = document.getElementById("id_MEXPAPER_btn_filedialog");
        if (el_MEXPAPER_filedialog && el_MEXPAPER_btn_filedialog){
            el_MEXPAPER_btn_filedialog.addEventListener("click", function() {MEXPAPER_Filedialog_Open(el_MEXPAPER_filedialog)}, false)
        };

        const el_MEXPAPER_loader = document.getElementById("id_MEXPAPER_loader");
        const el_MEXPAPER_msg_error = document.getElementById("id_MEXPAPER_msg_error");

        const el_MEXPAPER_btn_save = document.getElementById("id_MEXPAPER_btn_save");
        if(el_MEXPAPER_btn_save){el_MEXPAPER_btn_save.addEventListener("click", function() {MEXPAPER_Save()}, false)};

// ---  MOD CONFIRM ------------------------------------
        let el_confirm_header = document.getElementById("id_modconfirm_header");
        let el_confirm_loader = document.getElementById("id_modconfirm_loader");
        let el_confirm_msg_container = document.getElementById("id_modconfirm_msg_container")
        let el_confirm_btn_cancel = document.getElementById("id_modconfirm_btn_cancel");
        let el_confirm_btn_save = document.getElementById("id_modconfirm_btn_save");
        if (el_confirm_btn_save){ el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()}) };

// ---  set selected menu button active
        const btn_clicked = document.getElementById("id_plg_page_archive")

        //console.log("btn_clicked: ", btn_clicked)
        SetMenubuttonActive(document.getElementById("id_plg_page_archive"));

    if(may_view_page){
        const datalist_request = {
                setting: {page: "page_exampaper"},
                schoolsetting: {setting_key: "page_exampaper"},
                locale: {page: ["page_exampaper", "page_archive"]},
                examyear_rows: {get: true},

                published_rows: {examtype: "exampaper"}
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
                if ("examyear_rows" in response) {
                    examyear_rows = response.examyear_rows;
                    b_fill_datamap(examyear_map, response.examyear_rows);
                };

                if ("published_rows" in response) {
                    b_fill_datadicts("published",  "id", null, response.published_rows, published_dicts);
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
        //AddSubmenuButton(el_submenu, loc.Hide_columns, function() {t_MCOL_Open("page_archive")}, [], "id_submenu_columns");
        //el_submenu.classList.remove(cls_hide);

        if ( (permit_dict.requsr_role_admin && permit_dict.permit_crud) ||
             (permit_dict.requsr_role_insp && permit_dict.permit_crud)   ) {
            AddSubmenuButton(el_submenu, loc.Upload_document, function() {MEXPAPER_Open()});
            AddSubmenuButton(el_submenu, loc.Delete_document, function() {ModConfirmOpen("delete")});
        };

    };//function CreateSubmenu

//###########################################################################
//=========  HandleBtnSelect  ================ PR2020-09-19  PR2020-11-14 PR2023-04-18
    function HandleBtnSelect(data_btn, skip_upload) {
        //console.log( "===== HandleBtnSelect ========= ", data_btn);

        // check if data_btn exists, gave error because old btn name was still in saved setting PR2021-09-07 debug
        if (!data_btn) {data_btn = selected_btn};
        if (data_btn && ["btn_exampaper"].includes(data_btn)) {
            selected_btn = data_btn;
        } else {
            selected_btn = "btn_exampaper";
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

//=========  HandleTblRowClicked  ================ PR2020-08-03 PR2023-04-19
    function HandleTblRowClicked(tr_clicked) {
        console.log("=== HandleTblRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

// ---  deselect all highlighted rows, select clicked row
        t_tbody_selected_clear(tr_clicked.parentNode);
        t_tr_selected_set(tr_clicked);

// ---  update selected studsubj_dict / student_pk / subject pk
        selected.map_id = (tr_clicked.id) ? tr_clicked.id : null;
        console.log( "selected: ", selected, typeof selected);

    } ; // HandleTblRowClicked

//=========  DownloadDocument  ================ PR2023-04-19
    function DownloadDocument(el) {
        console.log("=== DownloadDocument");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

// ---  deselect all highlighted rows, select clicked row
        const tblRow = t_get_tablerow_selected(el)
        const el_url = b_get_element_by_data_value(tblRow, "field", "url");
        if (el_url) {
            el_url.click();
        };
    }  // DownloadDocument

//========= FillTblRows  ============== PR2021-06-16  PR2021-12-14
    function FillTblRows() {
        //console.log( "===== FillTblRows  === ");
        //console.log( "setting_dict", setting_dict);

        const tblName = "published";
        const field_setting = field_settings[selected_btn];
        const data_dicts = published_dicts;

// ---  get list of hidden columns
        // copy col_hidden from mod_MCOL_dict.cols_hidden
        col_hidden = b_copy_array_to_new_noduplicates(mod_MCOL_dict.cols_hidden);

        // hide level when not level_req
        if(!setting_dict.sel_dep_level_req){col_hidden.push("lvlbase_id")};

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

// --- create table header
        CreateTblHeader(field_setting, col_hidden);

// --- loop through data_rows
        for (const data_dict of Object.values(published_dicts)) {
            CreateTblRow(tblName, field_setting, data_dict);
        };
// --- filter tblRows
        Filter_TableRows();
    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-07-31 PR2021-06-15 PR2021-08-02 PR2021-12-14
    function CreateTblHeader(field_setting) {
        console.log("===  CreateTblHeader ===== ");
        console.log("field_setting", field_setting);
        console.log("col_hidden", col_hidden);

        const column_count = field_setting.field_names.length;

// +++  insert header and filter row ++++++++++++++++++++++++++++++++
        let tblRow_header = tblHead_datatable.insertRow (-1);
        let tblRow_filter = tblHead_datatable.insertRow (-1);

    // --- loop through columns
        for (let j = 0; j < column_count; j++) {
            const field_name = field_setting.field_names[j];

    // skip columns if in columns_hidden
            if (!col_hidden.includes(field_name)){

        // --- get field_caption from field_setting
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
        // --- add innerText to el_header
                    el_header.innerText = field_caption;
        // --- add width, text_align, right padding in examnumber
                    th_header.classList.add(class_width, class_align);
                    el_header.classList.add(class_width, class_align);
                    if (field_name === "datepublished"){
                        el_header.classList.add("pr-4");
                    };
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
    function CreateTblRow(tblName, field_setting, data_dict) {
        //console.log("=========  CreateTblRow =========", tblName);
        //console.log("   data_dict", data_dict);

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
                    el.innerHTML = "&emsp;&emsp;&emsp;&emsp;&#8681;&emsp;&emsp;&emsp;&emsp;";
                };

        // --- add data-field attribute
                el.setAttribute("data-field", field_name);

        // --- add  text_align
                el.classList.add(class_width, class_align);
                if (field_name === "datepublished"){
                    el.classList.add("pr-4");
                };
        // --- append element
                td.appendChild(el);

    // --- add EventListener to td
                if (["filename", "datepublished", "school_name"].includes(field_name)){
                    add_hover(td);
                    td.addEventListener("click", function() {DownloadDocument(td)}, false);

                } else if (field_name === "url"){
                    add_hover(td);

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

            if(field_name){
                let inner_text = null, h_ref = null, filter_value = null;
                if (field_name === "select") {

                } else if (field_name === "url"){
                    if (fld_value){
                        el_div.href = fld_value;
                        el_div.target = "_blank";
                    } else {
                        el_div.innerHTML = "&emsp;&emsp;&emsp;&emsp;-&emsp;&emsp;&emsp;&emsp;";
                        el_div.title = loc.File_not_found;
                    }

                } else if (field_name === "datepublished"){
                    //const date_formatted = format_date_from_dateISO(loc, fld_value);
                    const date_formatted = format_dateISO_vanilla (loc, fld_value, false, false, false, false);
                    inner_text = (date_formatted) ? date_formatted : "\n";
                    filter_value = date_formatted;


                } else if (["filename", "school_name"].includes(field_name)){
                    // put hard return in el_div, otherwise green border doesnt show in update PR2021-06-16
                    inner_text = (fld_value) ? fld_value : "\n";
                    filter_value = (fld_value) ? fld_value.toString().toLowerCase() : null;
                };

// ---  put value in innerText and title
                if (el_div.tagName === "A"){
                    // happens above
                } else {
                    el_div.innerHTML = inner_text;
                };

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

                    if (response.hasOwnProperty("msg_html")){
                        b_show_mod_message_html(response.msg_html);
                    };

                    if (response.hasOwnProperty("updated_published_rows")) {
                        RefreshDataRows("published", response.updated_published_rows, published_dicts);

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


//###########################################################################
// +++++++++++++++++ REFRESH DATA MAP +++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataRows  ================ PR2023-04-24
    function RefreshDataRows(tblName, update_rows, data_dicts, is_update) {
        console.log(" --- RefreshDataRows  ---");
        console.log("tblName", tblName);
        console.log("update_rows", update_rows);

        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length
        if (update_rows && update_rows.length ) {
            const field_setting = field_settings[selected_btn];

        console.log("field_setting", field_setting);
    // ---  get list of hidden columns
            const col_hidden = b_copy_array_to_new_noduplicates(mod_MCOL_dict.cols_hidden);

    // - hide level when not level_req
            if(!setting_dict.sel_dep_level_req){col_hidden.push("lvl_abbrev")};

            for (let i = 0, update_dict; update_dict = update_rows[i]; i++) {
        console.log("update_dict", update_dict);
                RefreshDatarowItem(tblName, field_setting, col_hidden, update_dict, data_dicts);
            };
        } else if (!is_update) {
            // empty the data_dicts when update_rows is empty PR2021-01-13 debug forgot to empty data_dicts
            // PR2021-03-13 debug. Don't empty de data_dicts when is update. Returns [] when no changes made
           b_clear_dict(data_dicts);
        };
    };  //  RefreshDataRows

//=========  RefreshDatarowItem  ================ PR2020-08-16 PR2020-09-30 PR2022-01-23 PR2022-04-13 PR2022-05-17
    function RefreshDatarowItem(tblName, field_setting, col_hidden, update_dict, data_dicts) {
        console.log(" --- RefreshDatarowItem  ---");
        console.log("tblName", tblName);
        console.log("update_dict", update_dict);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);
        console.log("map_id", map_id);
        console.log("is_deleted", is_deleted);
        console.log("is_created", is_created);

    // ---  get list of columns that are not updated because of errors
            const error_columns = [];
            if (update_dict.err_fields){
                // replace field '_auth2by' by '_status'
                for (let i = 0, err_field; err_field = update_dict.err_fields[i]; i++) {
                    if (err_field && err_field.includes("_auth")){
                        const arr = err_field.split("_");
                        err_field = arr[0] + "_status";
                    };
                    error_columns.push(err_field);
                };
            };
        //console.log("error_columns", error_columns);

// ++++ created ++++
            // PR2021-06-16 from https://stackoverflow.com/questions/586182/how-to-insert-an-item-into-an-array-at-a-specific-index-javascript
            //arr.splice(index, 0, item); will insert item into arr at the specified index
            // (deleting 0 items first, that is, it's just an insert).

            if(is_created){
    // ---  first remove key 'created' from update_dict
                delete update_dict.created;
    // ---  add new item to  data_dictsNEW with key
                data_dicts[update_dict.mapid] = update_dict;
    // ---  create row in table., insert in alphabetical order
                const new_tblRow = CreateTblRow("published", field_setting, update_dict);

                if(new_tblRow){
    // --- add1 to item_count and show total in sidebar
                    selected.item_count += 1;
    // ---  scrollIntoView,
                    new_tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' });
    // ---  make new row green for 2 seconds,
                    ShowOkElement(new_tblRow);
                };
            } else {

    // +++ get existing data_dict from data_dicts
                const data_dict = data_dicts[update_dict.mapid]
    console.log("    data_dict", data_dict);

                if(!isEmpty(data_dict)){

// ++++ deleted ++++
                    if(is_deleted){

                        delete data_dict[map_id];

        //--- delete tblRow
                        const tblRow_tobe_deleted = document.getElementById(map_id);
                        if (tblRow_tobe_deleted ){
                            tblRow_tobe_deleted.parentNode.removeChild(tblRow_tobe_deleted);
        // --- subtract 1 from item_count and show total in sidebar
                            selected.item_count -= 1;
        // ---  show total in sidebar
                            t_set_sbr_itemcount_txt(loc, selected.item_count, loc.Document, loc.Documents, setting_dict.user_lang);
                        };
                    } else {

// ++++ updated row +++++++++++
        // loop through fields of update_dict, check which fields are updated, add to list 'updated_columns'

        // ---  first add updated fields to updated_columns list, before updating data_row
                        let updated_columns = [];

    // ---  add field 'ce_exam_score' to updated_columns when value has changed
                        const [old_ce_exam_score, old_title_niu] = UpdateFieldScore(loc, data_dict)
                        const [new_ce_exam_score, new_title_niu] = UpdateFieldScore(loc, update_dict)
                        if (old_ce_exam_score !== new_ce_exam_score ) {
                            updated_columns.push("ce_exam_score");
                            updated_columns.push("download_exam");
                        };

    // ---  add field 'blanks' to updated_columns when value has changed
                        const [old_inner_txt, old_title_txt, old_filter_val] = UpdateFieldBlanks(tblName, data_dict);
                        const [new_inner_txt, new_title_txt, new_filter_val] = UpdateFieldBlanks(tblName, update_dict);
                        if (old_inner_txt !== new_inner_txt || old_title_txt !== new_title_txt ) {
                            updated_columns.push("blanks");
                        };

    // ---  add field 'status' to updated_columns when value has changed
                        const [old_status_className, old_status_title] = UpdateFieldStatus(tblName, data_dict);
                        const [new_status_className, new_status_title] = UpdateFieldStatus(tblName, update_dict);
                        if (old_status_className !== new_status_className || old_status_title !== new_status_title ) {
                            updated_columns.push("status");
                        };

    // ---  loop through fields of update_dict
                        for (const [key, new_value] of Object.entries(update_dict)) {
                            if (key in data_dict){
                                if (new_value !== data_dict[key]) {
    // ---  update field in data_row when value has changed
                                    data_dict[key] = new_value;

                            console.log("   ", key, new_value);
                            console.log(">>> has changed");
                            console.log("field_names", field_names);
    // ---  add field to updated_columns list when field exists in field_names
                                    if (field_names && field_names.includes(key)) {
        // ---  add field to updated_columns list
                                        updated_columns.push(key);
                                    };
                                };
                            };
                        };

        //console.log("updated_columns", updated_columns);
        // ---  update field in tblRow
                        // note: when updated_columns is empty, then updated_columns is still true.
                        // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
                        if(updated_columns.length){

    // --- get existing tblRow
                            let tblRow = document.getElementById(map_id);
        //console.log("tblRow", tblRow);
        //console.log("updated_columns", updated_columns);
                            if(tblRow){

    // - to make it perfect: move row when first or last name have changed
                                if (updated_columns.includes("name")){
                                //--- delete current tblRow
                                    tblRow.parentNode.removeChild(tblRow);
                                //--- insert row new at new position
                                    tblRow = CreateTblRow(tblName, field_setting, update_dict)
                                };

    // - loop through cells of row
                                for (let i = 1, el_fldName, el, td; td = tblRow.cells[i]; i++) {
                                    el = td.children[0];
                                    if (el){
                                        el_fldName = get_attr_from_el(el, "data-field");
                                        const is_updated_field = updated_columns.includes(el_fldName);
                                        const is_err_field = error_columns.includes(el_fldName);

    // - update field and make field green when field name is in updated_columns
                                        if(is_updated_field){
                                            UpdateField(tblName, el, update_dict);
                                            ShowOkElement(el);
                                        };
                                        if(is_err_field){
    // - make field red when error and reset old value after 2 seconds
                                            reset_element_with_errorclass(tblName, el, update_dict, tobedeleted)
                                        };
                                    }  // if (el)
                                };  // for (let i = 1, el_fldName, el; el = tblRow.cells[i]; i++)
                            };  // if(tblRow)
                        };  // if(updated_columns.length || field_error_list.length)
                    };  //  if(is_deleted)
                }  // if(!isEmpty(data_dict))
            }; // if(is_created)

    // ---  show total in sidebar
            t_set_sbr_itemcount_txt(loc, selected.item_count, loc.Exam, loc.Exams, setting_dict.user_lang);

        }; // if(!isEmpty(update_dict))
    }; // RefreshDatarowItem

// ##########################################################################

// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2022-11-02 PR2023-04-24
    function ModConfirmOpen(mode) {
        console.log(" -----  ModConfirmOpen   ----")

// reset  modal
        el_confirm_header.innerText = loc.Delete_document;
        el_confirm_msg_container.innerHTML = null;
        el_confirm_loader.classList.add(cls_hide);
        el_confirm_btn_save.classList.remove(cls_hide);
        el_confirm_btn_cancel.innerText = loc.Cancel;

        b_clear_dict(mod_dict);
        mod_dict.mode = mode;
        if ( mode === "delete"){
// --- get existing data_dict from data_rows

            const data_dict = published_dicts[selected.map_id]

            console.log("    data_dict", data_dict)

            if (isEmpty(data_dict)){
            // no document selected - give msg - not when is_create
                b_show_mod_message_html("<div class='p-2'>" + loc.Please_select_a_document_first + "</div>");
            } else {
                mod_dict.table = "published";
                mod_dict.published_pk = data_dict.id;
                mod_dict.map_id = data_dict.mapid;

                const msg_html = ["<div class='mx-2'>",
                                "<p>", loc.Document, " '", data_dict.name, "'", loc.will_be_deleted, "</p>",
                                "<p class='mt-2'>", loc.Do_you_want_to_continue, "</p>",
                             "</div>"].join("")

                el_confirm_loader.classList.add(cls_hide)
                el_confirm_msg_container.className = "p-3";
                el_confirm_msg_container.innerHTML = msg_html;

                el_confirm_btn_save.innerText = loc.Yes_delete;
                el_confirm_btn_cancel.innerText = loc.No_cancel;
                add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", true, "btn-primary");

    // set focus to cancel button
                set_focus_on_el_with_timeout(el_confirm_btn_save)
            };
        } else if (mode ==="uploading"){
            const msg_html = ["<div class='mx-2'>",
                            "<p>", loc.AWP_is_uploading_document01, mod_MEXPAPER_dict.curFile_name, loc.AWP_is_uploading_document02, "</p>",
                         "</div>"].join("")

            el_confirm_loader.classList.remove(cls_hide)
            add_or_remove_class (el_confirm_loader, cls_hide, false);
            el_confirm_msg_container.className = "p-3";
            el_confirm_msg_container.innerHTML = msg_html;

            el_confirm_btn_save.innerText = loc.OK;
            add_or_remove_class (el_confirm_btn_save, cls_hide, true);
            el_confirm_btn_cancel.innerText = loc.Close;
        };
// show modal
        $("#id_mod_confirm").modal({backdrop: true});
    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2021-08-22 PR2022-10-10
    function ModConfirmSave() {
        console.log(" --- ModConfirmSave --- ");
        console.log("mod_dict: ", mod_dict);
        let close_modal_with_timout = false;

        el_confirm_msg_container.innerHTML = null;
        el_confirm_loader.classList.remove(cls_hide);
        el_confirm_btn_save.classList.add(cls_hide);
        el_confirm_btn_cancel.innerText = loc.Close;

        let upload_dict = {
            table: mod_dict.table,
            mode: "delete",
            published_pk: mod_dict.published_pk
        };
        UploadChanges(upload_dict, urls.url_exampaper_upload);

        const tblRow = document.getElementById(mod_dict.map_id)
        ShowClassWithTimeout(tblRow, "tsa_tr_error")

    // hide modal
            $("#id_mod_confirm").modal("hide");

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

            //t_Refresh_DataDicts("published", response.updated_published_rows, published_dicts, CreateTblRow);
            RefreshDataRows("published", response.updated_published_rows, published_dicts);

            Filter_TableRows();
        };
    };  // ModConfirmResponseNEW
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

        const field_setting = field_settings[selected_btn];
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



//###########################################################################
//========= MOD EXAMPAPEr Open===================== PR2023-04-18
    function MEXPAPER_Open (mode) {
        console.log("===  MEXPAPER_Open  =====") ;

        if ( (permit_dict.requsr_role_admin && permit_dict.permit_crud) ||
             (permit_dict.requsr_role_insp && permit_dict.permit_crud)   ) {

            b_clear_dict(mod_MEXPAPER_dict);

    // - reset input fields
            el_MEXPAPER_filedialog.value = null;
            el_MEXPAPER_filename.innerText = null;
            el_MEXPAPER_input_title.value = null;
            el_MEXPAPER_input_date_published.value = null;
            // accept is in modexampaper.html
           //   el_MEXPAPER_filedialog.setAttribute("accept", ".pdf");
           el_MEXPAPER_msg_container.innerHTML = null;

            $("#id_mod_exampaper").modal({backdrop: true});
        };
    };  // MEXPAPER_Open

//=========   MEXPAPER_Save   ====================== PR2023-04-18
    function MEXPAPER_Save(){
        console.log(" ========== MEXPAPER_Save ===========");

    console.log("  mod_MEXPAPER_dict", mod_MEXPAPER_dict);
        const filename = el_MEXPAPER_filedialog.value;

        console.log( "mod_MEXPAPER_dict", mod_MEXPAPER_dict);

        // from https://medium.com/typecode/a-strategy-for-handling-multiple-file-uploads-using-javascript-eb00a77e15f
        const date_published = (el_MEXPAPER_input_date_published && el_MEXPAPER_input_date_published.value) ? el_MEXPAPER_input_date_published.value : null;
        const file_title = (el_MEXPAPER_input_title && el_MEXPAPER_input_title.value) ? el_MEXPAPER_input_title.value : null;

        const upload_dict = {
            mode: "create",
            file_name: mod_MEXPAPER_dict.curFile_name,
            file_size: mod_MEXPAPER_dict.curFile_size,
            file_title: file_title,
            date_published: date_published
        };

// get attachment info

        el_MEXPAPER_loader.classList.remove(cls_hide);

        const upload_json = JSON.stringify (upload_dict)
        const url_str = urls.url_exampaper_upload;

        console.log("    url_str", url_str);
        console.log("    upload_dict", upload_dict);

        const uploadFile = new b_UploadFile(upload_json, mod_MEXPAPER_dict.curFile, url_str);
        uploadFile.doUpload(MEXPAPER_Refresh);

        $("#id_mod_exampaper").modal("hide");

        ModConfirmOpen("uploading")

    };  // MEXPAPER_Save

//=========   MEXPAPER_Filedialog_Open   ======================
    function MEXPAPER_Filedialog_Open(el_filedialog) { // PR2022-02-26
        console.log(" ========== MEXPAPER_Filedialog_Open ===========");
        el_filedialog.click();
    };

//=========   MEXPAPER_HandleFiledialog   ====================== PR2022-02-26  PR2023-04-18
    function MEXPAPER_HandleFiledialog(el_filedialog) { // functie wordt alleen doorlopen als file is geselecteerd
        console.log(" ========== MEXPAPER_HandleFiledialog ===========");

// ---  get curfiles from filedialog
        // curfiles is list of files: PR2020-04-16
        // curFiles[0]: {name: "tsa_import_orders.xlsx", lastModified: 1577989274259, lastModifiedDate: Thu Jan 02 2020 14:21:14 GMT-0400 (Bolivia Time) {}
       // webkitRelativePath: "", size: 9622, type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}, length: 1}

        let curFiles = el_filedialog.files; //This one doesn't work in Firefox: let curFiles = event.target.files;

        console.log("    curFiles", curFiles);

// ---  validate selected file
        let curFile = (curFiles && curFiles.length) ?  curFiles[0] : null;
        let msg_html = null;
        if(!curFile) {
             msg_html = ["<div class='p-2 border_bg_invalid'>", loc.First_select_valid_file, "</div>"].join('')
        } else if(!MEXPAPER_is_allowed_filetype(curFile)) {
             msg_html = ["<div class='p-2 border_bg_invalid'>'", curFile.name, "'", loc.is_not_a_valid_file, "<br>",
                               loc.Only, "PDF", loc.is_allowed, "</div>"].join('')
        } else if (curFile.size > max_file_size_Mb * 1000000) {
             msg_html = ["<div class='p-2 border_bg_invalid'>", loc.Document, " '",  curFile.name, "'", loc.is_too_large, "<br>",
                               loc.Maximum_size_is, (max_file_size_Mb), " Mb.", "</div>"].join('');
        };
        if (msg_html){
            el_MEXPAPER_msg_container.innerHTML = msg_html;
        } else {
            el_MEXPAPER_msg_container.innerHTML = null;

            el_MEXPAPER_filename.innerText = (curFile) ? curFile.name : null;

            const curFile_name_no_ext = (curFile) ? (curFile.name.includes(".")) ? curFile.name.split(".").slice(0, -1).join(".") : curFile.name : null;
            el_MEXPAPER_input_title.value = curFile_name_no_ext;

            const lastModifiedDate_iso = (curFile && curFile.lastModifiedDate) ? get_dateISO_from_dateJS(curFile.lastModifiedDate) : null;

            el_MEXPAPER_input_date_published.value = lastModifiedDate_iso;

            mod_MEXPAPER_dict.curFile = curFile;
            mod_MEXPAPER_dict.curFile_name = (curFile) ? curFile.name : null;
            mod_MEXPAPER_dict.curFile_size = (curFile) ? curFile.size : null;
        };
        el_MEXPAPER_btn_save.disabled = !mod_MEXPAPER_dict.curFile_name;

    };  // MEXPAPER_HandleFiledialog

//=========  MEXPAPER_input_change  ================ PR2023-04-19
    function MEXPAPER_input_change(el_input) {
        console.log(" --- MEXPAPER_input_change  ---");

    };  // MEXPAPER_input_change

//=========  MEXPAPER_Refresh  ================ PR2021-10-12 PR2023-04-17
    function MEXPAPER_Refresh(response) {
        console.log(" --- MEXPAPER_Refresh  ---");
        console.log("    response:", response);

        el_MEXPAPER_loader.classList.add(cls_hide);

        $("#id_mod_exampaper").modal("hide");

        if ("messages" in response) {
            b_show_mod_message_dictlist(response.messages);
        };
        if ("msg_html" in response) {
            b_show_mod_message_html(response.msg_html);
        };
        if (response && response.hasOwnProperty("updated_published_rows")) {
            //t_Refresh_DataDicts("published", response.updated_published_rows, published_dicts, CreateTblRow);
            RefreshDataRows("published", response.updated_published_rows, published_dicts);
            Filter_TableRows();
        };

        $("#id_mod_confirm").modal("hide");
    }; // MEXPAPER_Refresh


//========= MEXPAPER_is_allowed_filetype  ====================================
    function MEXPAPER_is_allowed_filetype(File) {
        // MIME xls: application/vnd.ms-excel
        // MIME xlsx: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
        // MIME csv: text/csv
        const allowed_MIMEtypes = {
            pdf: "application/pdf",
            //txt: "text/plain",
            //docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            //xls: "application/vnd.ms-excel",
            //xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        };
        let is_valid = false;
        for (const value of Object.values(allowed_MIMEtypes)) {
            if(File.type === value) {
                is_valid = true;
                break;
            };
        };
        return is_valid;
    };  // MEXPAPER_is_allowed_filetype



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


// ---  upload new setting and refresh page
        const datalist_request = {
                setting: {page: "page_archive",
                          sel_schoolbase_pk: selected_pk  },

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