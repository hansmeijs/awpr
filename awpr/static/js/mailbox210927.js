// PR2021-09-12 added

let selected_btn = "btn_received";
let setting_dict = {};
let permit_dict = {};
let loc = {};
let urls = {};

let mailbox_rows = [];
let mailinglist_rows = [];

const field_settings = {};

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

    let mod_dict = {};
    let time_stamp = null; // used in mod add user

    let user_list = [];
    let user_rows = [];
    let permit_rows = [];
    let school_rows = [];

    let examyear_map = new Map();

    let department_map = new Map();

    let permit_map = new Map();

    let filter_dict = {};

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    urls.url_settings_upload = get_attr_from_el(el_data, "data-url_settings_upload");

    let columns_hidden = [];

// --- get field_settings
    const field_settings = {
        btn_received: { field_caption: ["", "Sender", "From", "Subject", "Date_sent", "Attachment", "Status"],
                    field_names: ["select", "school_abbrev", "user_lastname", "header", "modifiedat"], //, "attachment", "status"],
                    field_tags: ["div", "div", "div", "div", "div", "div", "div"],
                    filter_tags: ["select", "text", "text",  "text",  "text", "toggle", "toggle"],
                    field_width:  ["020", "150", "240", "480",  "180", "090", "090"],
                    field_align: ["c", "l", "l", "l", "l",  "c",  "c"]},
        btn_sent:  { field_caption: ["", "Sent_to", "Attn", "Subject", "Date_sent", "Attachment", "Status"],
                    field_names: ["select", "school_abbrev", "user_lastname", "header", "modifiedat"], //, "attachment", "status"],
                    field_tags: ["div", "div", "div", "div", "div", "div", "div"],
                    filter_tags: ["select", "text", "text",  "text",  "text", "toggle", "toggle"],
                    field_width:  ["020", "150", "240", "480",  "180", "090", "090"],
                    field_align: ["c", "l", "l", "l", "l",  "c",  "c"]},
        btn_mailinglist:  { field_caption: ["", "Organization", "From", "Subject", "Sent", "Attachment", "Status"],
                    field_names: ["select", "sender_school", "sender_user", "header", "modifiedat"], //, "attachment", "status"],
                    field_tags: ["div", "div", "div", "div", "div", "div", "div"],
                    filter_tags: ["select", "text", "text",  "text",  "text", "toggle", "toggle"],
                    field_width:  ["020", "150", "240", "240",  "180", "090", "090"],
                    field_align: ["c", "l", "l", "l", "l",  "c",  "c"]}
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
            el_hdrbar_examyear.addEventListener("click",
                function() {t_MSED_Open(loc, "examyear", examyear_map, setting_dict, permit_dict, MSED_Response)}, false );
        }
        if (el_hdrbar_department){
            el_hdrbar_department.addEventListener("click",
                function() {t_MSED_Open(loc, "department", department_map, setting_dict, permit_dict, MSED_Response)}, false );
        }
        if (el_hdrbar_school){
            el_hdrbar_school.addEventListener("click",
                function() {t_MSSSS_Open(loc, "school", school_rows, false, setting_dict, permit_dict, MSSSS_Response)}, false );
        }

// ---  SIDEBAR ------------------------------------
        const el_SBR_item_count = document.getElementById("id_SBR_item_count")


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

// ---  MOD CONFIRM ------------------------------------
        let el_confirm_header = document.getElementById("id_modconfirm_header");
        let el_confirm_loader = document.getElementById("id_modconfirm_loader");
        let el_confirm_msg_container = document.getElementById("id_modconfirm_msg_container")
        let el_confirm_btn_cancel = document.getElementById("id_modconfirm_btn_cancel");
        let el_confirm_btn_save = document.getElementById("id_modconfirm_btn_save");
        if (el_confirm_btn_save){el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()}, false)};

    if(may_view_page){
// ---  set selected menu button active
        SetMenubuttonActive(document.getElementById("id_hdr_users"));

        const datalist_request = {
                setting: {page: "page_mailbox"},
                schoolsetting: {setting_key: "import_username"},
                locale: {page: ["page_mailbox"]},
                mailbox_rows: {get: true}
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
            url: urls.url_datalist_download,
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
                    isloaded_loc = true;
                };

                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict;
                    selected_btn = setting_dict.sel_btn;
                    isloaded_settings = true;
                };

// ---  fill cols_hidden
                if("cols_hidden" in setting_dict){
                   // clear the array columns_hidden
                   // reset all arrays of key to [], keep the keys.
                    for (const key of Object.keys(columns_hidden)) {
                        b_clear_array(columns_hidden[key]);
                    };
                // fill the arrays in  columns_hidden
                    for (const [key, value] of Object.entries(setting_dict.cols_hidden)) {
                        columns_hidden[key] = value;
                    };
                };
                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    // get_permits must come before CreateSubmenu and FiLLTbl
                    b_get_permits_from_permitlist(permit_dict);
                    isloaded_permits = true;
                }

                if(isloaded_loc && isloaded_settings){CreateSubmenu()};
                if(isloaded_settings || isloaded_permits){b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);};

                if ("messages" in response) {
                    b_ShowModMessages(response.messages);
                }
                if ("mailbox_rows" in response) {
                    mailbox_rows = response.mailbox_rows
                console.log("mailbox_rows", mailbox_rows);
                };

                HandleBtnSelect(selected_btn, true);  // true = skip_upload
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
        // hardcode access of system admin, to get access before action 'crud' is added to permits
        const permit_system_admin = (permit_dict.requsr_role_system && permit_dict.usergroup_list.includes("admin"));
        const permit_role_admin = (permit_dict.requsr_role_admin && permit_dict.usergroup_list.includes("admin"));

        if (permit_dict.permit_crud) {
            //AddSubmenuButton(el_submenu, loc.Create_message, function() {ModConfirmOpen("user","delete")});
        }

         //el_submenu.classList.remove(cls_hide);
    };//function CreateSubmenu

//###########################################################################
// +++++++++++++++++ EVENT HANDLERS +++++++++++++++++++++++++++++++++++++++++
//=========  HandleBtnSelect  ================ PR2020-09-19 PR2021-08-01
    function HandleBtnSelect(data_btn, skip_upload) {
        console.log( "===== HandleBtnSelect ========= ");
        console.log( "skip_upload: ", skip_upload);

// ---  get  selected_btn
        // set to default "btn_user" when there is no selected_btn
        // this happens when user visits page for the first time
        // includes is to catch saved btn names that are no longer in use
        selected_btn = (data_btn && ["btn_received", "btn_sent", "btn_mailinglist"].includes(data_btn)) ? data_btn : "btn_received"
        console.log( "selected_btn: ", selected_btn);

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_mailbox: {sel_btn: selected_btn}};
            b_UploadSettings (upload_dict, urls.url_settings_upload);
        };

// ---  highlight selected button
        highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  show only the elements that are used in this tab
        b_show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

// ---  fill datatable
        FillTblRows();

    }  // HandleBtnSelect

//=========  HandleTableRowClicked  ================ PR2020-08-03 PR2021-08-01
    function HandleTableRowClicked(tr_clicked) {
        console.log("=== HandleTableRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);
        //console.log( "tr_clicked.id: ", tr_clicked, typeof tr_clicked.id);

        selected_user_dict = get_datadict_from_mapid(tr_clicked.id);
        console.log( "selected_user_dict: ", selected_user_dict);

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        DeselectHighlightedRows(tr_clicked, cls_selected);
        tr_clicked.classList.add(cls_selected)

// --- get existing data_dict from data_rows
        //console.log( "tr_clicked.id: ", tr_clicked.id);
        const data_dict = get_datadict_from_mapid(tr_clicked.id)
        //console.log( "data_dict: ", data_dict);

// ---  update selected_user_pk
        const tblName = get_tblName_from_mapid(data_dict.mapid);

        selected_user_pk = data_dict.id;

        //console.log( "selected_userpermit_pk: ", selected_userpermit_pk, typeof selected_userpermit_pk);
        //console.log( "selected_user_pk: ", selected_user_pk, typeof selected_user_pk);
    }  // HandleTableRowClicked

//========= FillTblRows  =================== PR2021-08-01
    function FillTblRows() {
        console.log( "===== FillTblRows  === ");
        const tblName = get_tblName_from_selectedBtn();

        const field_setting = field_settings[selected_btn];
        const data_rows = get_data_rows(tblName);

        console.log( "selected_btn", selected_btn);
        console.log( "tblName", tblName);
        console.log( "data_rows", data_rows);
        console.log( "field_setting", field_setting);

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null

// --- create table header and filter row
        CreateTblHeader(field_setting);

// --- loop through data_rows
        if(data_rows && data_rows.length){
            for (let i = 0, map_dict; map_dict = data_rows[i]; i++) {
            // skip sent items in inbox, skip inbox item in sent box
                const skip_row = (selected_btn === "btn_received") ? !!map_dict.issentmail :
                                 (selected_btn === "btn_sent") ? !map_dict.issentmail : false;
                if(!skip_row){
                    CreateTblRow(tblName, field_setting, map_dict);
                }
            };
        };

// --- filter tblRows
        Filter_TableRows
    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-07-31 PR2021-03-23  PR2021-08-01
    function CreateTblHeader(field_setting) {
        console.log("===  CreateTblHeader ===== ");
        console.log("field_setting", field_setting);

        const column_count = field_setting.field_names.length;

// +++  insert header and filter row ++++++++++++++++++++++++++++++++
        let tblRow_header = tblHead_datatable.insertRow (-1);
        let tblRow_filter = tblHead_datatable.insertRow (-1);

    // --- loop through columns
        for (let j = 0; j < column_count; j++) {
            const field_name = field_setting.field_names[j];
    // - skip column if field_name in columns_hidden;
            const hide_column = columns_hidden.includes(field_name);
            if (!hide_column){

        // --- get field_caption from field_setting
                const field_caption = loc[field_setting.field_caption[j]];
                const field_tag = field_setting.field_tags[j];
                const filter_tag = field_setting.filter_tags[j];
                const class_width = "tw_" + field_setting.field_width[j] ;
                const class_align = "ta_" + field_setting.field_align[j];

// ++++++++++ insert columns in header row +++++++++++++++
        // --- add th to tblRow.
                let th_header = document.createElement("th");
        // --- add div to th, margin not working with th
                    const el_header = document.createElement("div");
        // --- add innerText to el_header
                    el_header.innerText = (field_caption) ? field_caption : null;
        // --- add width, text_align
                        // not necessary: th_header.classList.add(class_width, class_align);
                    th_header.classList.add(class_width, class_align);
                    el_header.classList.add(class_width, class_align);

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
                    //el_filter.setAttribute("data-colindex", j);

        // --- add EventListener to el_filter / th_filter
                    if (["text", "number"].includes(filter_tag)) {
                        el_filter.addEventListener("keyup", function(event){HandleFilterKeyup(el_filter, event)});
                        add_hover(th_filter);
                    } else if (["toggle", "activated"].includes(filter_tag)) {
                        // add EventListener for icon to th_filter, not el_filter
                        th_filter.addEventListener("click", function(event){HandleFilterToggle(el_filter)});
                        th_filter.classList.add("pointer_show");

                        // default empty icon necessary to set pointer_show
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

                    el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");
                th_filter.appendChild(el_filter)
                tblRow_filter.appendChild(th_filter);
            }  // if (!columns_hidden.includes(field_name))
        }  // for (let j = 0; j < column_count; j++)
    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09 PR2021-08-01
    function CreateTblRow(tblName, field_setting, map_dict) {
        //console.log("=========  CreateTblRow =========", tblName);
        //console.log("map_dict", map_dict);

        const field_names = field_setting.field_names;
        const field_tags = field_setting.field_tags;
        const filter_tags = field_setting.filter_tags;
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;

        const map_id = (map_dict.mapid) ? map_dict.mapid : null;

// ---  lookup index where this row must be inserted
        const ob1 = (map_dict.sb_code) ? map_dict.sb_code : "";
        const ob2 = (map_dict.username) ? map_dict.username : "";

        const row_index = b_recursive_tblRow_lookup(tblBody_datatable,
                                     ob1, ob2, "", setting_dict.user_lang);

// --- insert tblRow into tblBody at row_index
        const tblRow = tblBody_datatable.insertRow(row_index);
        tblRow.id = map_id

// --- add data attributes to tblRow
        tblRow.setAttribute("data-pk", map_dict.id);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);
        tblRow.setAttribute("data-ob2", ob2);
        // NIU: tblRow.setAttribute("data-ob3", ---);

// --- add EventListener to tblRow
        tblRow.addEventListener("click", function() {HandleTableRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
        for (let j = 0; j < column_count; j++) {
            const field_name = field_names[j];

    // - skip column if field_name in columns_hidden;
            const hide_column = columns_hidden.includes(field_name);
            if (!hide_column){
                const field_tag = field_tags[j];
                const class_width = "tw_" + field_width[j];
                const class_align = "ta_" + field_align[j];

        // --- insert td element,
                let td = tblRow.insertCell(-1);

        // --- create element with tag from field_tags
                let el = document.createElement(field_tag);

        // --- add data-field attribute
                    el.setAttribute("data-field", field_name);

        // --- add  text_align
                el.classList.add(class_width, class_align);

        // --- append element
                td.appendChild(el);

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

    // --- add EventListener to td
                    if (field_name === "select") {
                        // TODO add select multiple users option PR2020-08-18

                    } else if (["school_abbrev", "user_lastname", "header", "modifiedat", "attachment", "status"].includes(field_name)){
                        el.addEventListener("click", function() {MUA_Open("update", el)}, false)
                        el.classList.add("pointer_show");
                        add_hover(el);
                    } else if (field_name === "is_active") {
                        el.addEventListener("click", function() {ModConfirmOpen("user", "is_active", el)}, false )
                        el.classList.add("inactive_0_2")
                        add_hover(el);
                    } else if ( field_name === "last_login") {
                        // pass
                    }

// --- put value in field
                UpdateField(el, map_dict)

            }  // if (!columns_hidden.includes(field_name))
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

//=========  UpdateField  ================ PR2020-08-16 PR2021-03-23 PR2021-08-01
    function UpdateField(el_div, map_dict) {
        //console.log("=========  UpdateField =========");

        const field_name = get_attr_from_el(el_div, "data-field");
        if(el_div && field_name){
            let inner_text = null, title_text = null, filter_value = null;
            if (field_name === "select") {
                // TODO add select multiple users option PR2020-08-18
            } else if (["school_abbrev", "user_lastname", "header", "attachment", "status"].includes(field_name)){
                inner_text = map_dict[field_name];
                filter_value = (inner_text) ? inner_text.toLowerCase() : null;
                if ( field_name === "header" && map_dict.body) {
                    title_text = map_dict.body ;
                };
            } else if ( field_name === "activated") {
                const is_activated = (map_dict[field_name]) ? map_dict[field_name] : false;
                let is_expired = false;
                if(!is_activated) {
                    is_expired = activationlink_is_expired(map_dict.date_joined);
                }
                filter_value = (is_expired) ? "2" : (is_activated) ? "1" : "0"
                el_div.className = (is_activated) ? "tickmark_2_2" : (is_expired) ? "exclamation_0_2" : "tickmark_0_0" ;
// ---  add pointer when not is_activatd
                add_or_remove_class(el_div, "pointer_show", !is_activated)

// ---  add title
                title_text = (is_expired) ? loc.Activationlink_expired + "\n" + loc.Send_activationlink : null
            } else if (field_name === "is_active") {
                const is_inactive = !( (map_dict[field_name]) ? map_dict[field_name] : false );
                // give value '0' when inactive, '1' when active
                filter_value = (is_inactive) ? "0" : "1";

                el_div.className = (is_inactive) ? "inactive_1_3" : "inactive_0_2";

// ---  add title
                title_text = (is_inactive) ? loc.This_user_is_inactive : null;
            } else if ( field_name === "modifiedat") {
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

                    if("msg_dictlist" in response){
                        b_ShowModMessages(response.msg_dictlist);
                    }

                    const mode = get_dict_value(response, ["mode"]);
                    if(["delete", "send_activation_email"].includes(mode)) {
                        ModConfirmResponse(response);
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
//=========  ModConfirmOpen  ================ PR2020-08-03 PR2021-06-30
    function ModConfirmOpen(tblName, mode, el_input) {
        //console.log(" -----  ModConfirmOpen   ----")
        // values of mode are : "delete", "is_active" or "send_activation_email", "permission_admin"

        //console.log("mode", mode )
        //console.log("tblName", tblName )

// ---  get selected_pk
        let selected_pk = null;
        // tblRow is undefined when clicked on delete btn in submenu btn or form (no inactive btn)
        const tblRow = get_tablerow_selected(el_input);
        if(tblRow){
            selected_pk = get_attr_from_el_int(tblRow, "data-pk")
        } else {
            selected_pk = selected_user_pk;
        }
        //console.log("tblRow", tblRow )
        //console.log("selected_pk", selected_pk )

// --- get data_dict from tblName and selected_pk
        const data_dict = get_datadict_from_pk(tblName, selected_pk)
        //console.log("data_dict", data_dict);

// ---  get info from data_dict
        // TODO remove requsr_pk from client
        const is_request_user = (data_dict && permit_dict.requsr_pk && permit_dict.requsr_pk === data_dict.id)
        //console.log("permit_map", permit_map)
        //console.log("data_dict", data_dict)

// ---  create mod_dict
        mod_dict = {mode: mode, table: tblName};
        const has_selected_item = (!isEmpty(data_dict));
        if(has_selected_item){
            mod_dict.mapid = data_dict.mapid;
            mod_dict.user_pk = data_dict.id;
            mod_dict.user_ppk = data_dict.schoolbase_id;
        };
        if (mode === "is_active") {
              mod_dict.current_isactive = data_dict.is_active;
        }

// ---  put text in modal form
        let dont_show_modal = false;
        const is_mode_permission_admin = (mode === "permission_admin");
        const is_mode_send_activation_email = (mode === "send_activation_email");
        //console.log("mode", mode)
        const inactive_txt = (mod_dict.current_isactive) ? loc.Make_user_inactive : loc.Make_user_active;
        const header_text = (mode === "delete") ? loc.Delete_user :
                            (mode === "is_active") ? inactive_txt :
                            (is_mode_send_activation_email) ? loc.Send_activation_email :
                            (is_mode_permission_admin) ? loc.Set_permissions : "";

        let msg_list = [];
        let hide_save_btn = false;
        if(!has_selected_item){
            msg_list = [loc.No_user_selected];
            hide_save_btn = true;
        } else {
            const username = (data_dict.username) ? data_dict.username  : "-";
            if(mode === "delete"){
                if(is_request_user){
                    msg_list = [loc.Sysadm_cannot_delete_own_account];
                    hide_save_btn = true;
                } else {
                    msg_list = [loc.User + " '" + username + "'" + loc.will_be_deleted,
                                loc.Do_you_want_to_continue];
                }
            } else if(mode === "is_active"){
                if(is_request_user && mod_dict.current_isactive){
                    msg_list = [loc.Sysadm_cannot_set_inactive];
                    hide_save_btn = true;
                } else {
                    const inactive_txt = (mod_dict.current_isactive) ? loc.will_be_made_inactive : loc.will_be_made_active
                    msg_list = [loc.User + " '" + username + "'" + inactive_txt,
                                loc.Do_you_want_to_continue];
                }
            } else if(is_mode_permission_admin){
                hide_save_btn = true;
                const fldName = get_attr_from_el(el_input, "data-field")
                if (fldName === "group_admin") {
                    msg_list = [loc.Sysadm_cannot_remove_sysadm_perm]
                }
            } else if (is_mode_send_activation_email) {
                const is_expired = activationlink_is_expired(data_dict.date_joined);
                dont_show_modal = (data_dict.activated);
                if(!dont_show_modal){
                    if(is_expired) {
                        msg_list.push(loc.Activationlink_expired);
                    };
                    msg_list.push("<p>" + loc.We_will_send_an_email_to_user + " '" + username + "'.</p>");
                    msg_list.push("<p>" + loc.Do_you_want_to_continue + "</p>");
                }
            }

        }
        if(!dont_show_modal){
            el_confirm_header.innerText = header_text;
            el_confirm_loader.classList.add(cls_visible_hide)
            el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");

            const msg_html = (msg_list.length) ? msg_list.join("<br>") : null;
            el_confirm_msg_container.innerHTML = msg_html;

                        el_confirm_msg_container.classList.add("border_bg_transparent");

            const caption_save = (mode === "delete") ? loc.Yes_delete :
                            (mode === "is_active") ? ( (mod_dict.current_isactive) ? loc.Yes_make_inactive : loc.Yes_make_active ) :
                            (is_mode_send_activation_email) ? loc.Yes_send_email : loc.OK;
            el_confirm_btn_save.innerText = caption_save;
            add_or_remove_class (el_confirm_btn_save, cls_hide, hide_save_btn);

            add_or_remove_class (el_confirm_btn_save, "btn-primary", (mode !== "delete"));
            add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", (mode === "delete"));

            const caption_cancel = (mode === "delete") ? loc.No_cancel :
                            (mode === "is_active") ? loc.No_cancel :
                            (is_mode_send_activation_email) ? loc.No_cancel : loc.Cancel;
            el_confirm_btn_cancel.innerText = (has_selected_item && !is_mode_permission_admin) ? caption_cancel : loc.Close;

    // set focus to cancel button
            set_focus_on_el_with_timeout(el_confirm_btn_cancel, 150);

// show modal
            $("#id_mod_confirm").modal({backdrop: true});
        }

    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2019-06-23
    function ModConfirmSave() {
        //console.log(" --- ModConfirmSave --- ");
        //console.log("mod_dict: ", mod_dict);
        let tblRow = document.getElementById(mod_dict.mapid);

// ---  when delete: make tblRow red, before uploading
        if (tblRow && mod_dict.mode === "delete"){
            ShowClassWithTimeout(tblRow, "tsa_tr_error");
        }

        let close_modal = false, url_str = null;
        const upload_dict = {mode: mod_dict.mode, mapid: mod_dict.mapid};

        if(["delete", "send_activation_email"].includes(mod_dict.mode)) {
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
        url_str = urls.url_user_upload;
        upload_dict.user_pk = mod_dict.user_pk;
        upload_dict.schoolbase_pk = mod_dict.user_ppk;
        if (mod_dict.mode === "is_active") {
            upload_dict.is_active = mod_dict.new_isactive;
        };

// ---  Upload changes
        UploadChanges(upload_dict, url_str);
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
            let msg_list = [];
            if ("msg_err" in response) {
                msg_list.push(get_dict_value(response, ["msg_err", "msg01"], ""));
                if (mod_dict.mode === "send_activation_email") {
                     msg_list.push(loc.Activation_email_not_sent);
                }
                el_confirm_msg_container.classList.add("border_bg_invalid");
            } else if ("msg_ok" in response){
                const msg01 = get_dict_value(response, ["msg_ok", "msg01"]);
                const msg02 = get_dict_value(response, ["msg_ok", "msg02"]);
                const msg03 = get_dict_value(response, ["msg_ok", "msg03"]);
                if (msg01) { msg_list.push("<p>" + msg01 + "</p>")};
                if (msg02) msg_list.push("<p>" + msg02 + "</p>");
                if (msg03) msg_list.push("<p>" + msg03 + "</p>");
                el_confirm_msg_container.classList.add("border_bg_valid");
            }

            const msg_html = (msg_list.length) ? msg_list.join("<br>") : null;
            el_confirm_msg_container.innerHTML = msg_html;

            el_confirm_btn_cancel.innerText = loc.Close
            el_confirm_btn_save.classList.add(cls_hide);
        } else {
        // hide mod_confirm when no message
            $("#id_mod_confirm").modal("hide");
        }
    }  // ModConfirmResponse

//###########################################################################

//=========  RefreshDataRowsAfterUpload  ================ PR2021-08-05
function RefreshDataRowsAfterUpload(response) {
    //console.log(" --- RefreshDataRowsAfterUpload  ---");
    //console.log("response:", response);
    const is_test = (!!response && !!response.is_test) ;
    if(!is_test && response && "updated_user_rows" in response) {
        RefreshDataRows("user", response.updated_user_rows, user_rows, true)  // true = update
    }

}  // RefreshDataRowsAfterUpload

//=========  RefreshDataRowsPermitsAfterUpload  ================ PR2021-07-20
    function RefreshDataRowsPermitsAfterUpload(response) {
        //console.log(" --- RefreshDataRowsPermitsAfterUpload  ---");
        //console.log( "response", response);

        const is_test = (response && response.is_test);
        //console.log( "is_test", is_test);
        if (response && "updated_user_rows" in response) {
            const updated_user_rows = response.updated_user_rows;
        }

    }  //  RefreshDataRowsPermitsAfterUpload

// +++++++++++++++++ REFRESH PERMIT MAP ++++++++++++++++++++++++++++++++++++++++++++++++++
//=========  refresh_permit_map  ================ PR2021-03-18
    function refresh_permit_map(updated_permitlist) {
        //console.log(" --- refresh_permit_map  ---");
        //console.log( "updated_permitlist", updated_permitlist);
        if (updated_permitlist) {
            for (let i = 0, update_dict; update_dict = updated_permitlist[i]; i++) {
               // refresh_usermap_item(permit_map, update_dict);
               //RefreshDatarowItem(tblName, field_setting, update_dict, data_rows)
            }
        }
    }  //  refresh_permit_map


// +++++++++++++++++ REFRESH DATA ROWS ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataRows  ================ PR2021-08-01
    function RefreshDataRows(page_tblName, update_rows, data_rows, is_update) {
        //console.log(" --- RefreshDataRows  ---");
        //console.log("page_tblName", page_tblName);
        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length

        if (update_rows && update_rows.length ) {
            const field_setting = field_settings[page_tblName];
            //console.log("field_setting", field_setting);
            for (let i = 0, update_dict; update_dict = update_rows[i]; i++) {
                RefreshDatarowItem(page_tblName, field_setting, update_dict, data_rows);
            }
        } else if (!is_update) {
            // empty the data_rows when update_rows is empty PR2021-01-13 debug forgot to empty data_rows
            // PR2021-03-13 debug. Don't empty de data_rows when is update. Returns [] when no changes made
           data_rows = [];
        }
    }  //  RefreshDataRows


//=========  RefreshDatarowItem  ================ PR2021-08-01
    function RefreshDatarowItem(page_tblName, field_setting, update_dict, data_rows) {
        //console.log(" --- RefreshDatarowItem  ---");
        //console.log("page_tblName", page_tblName);
        //console.log("update_dict", update_dict);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);
            //console.log("is_created", is_created);

            // field_error_list is not in use (yet)
            let field_error_list = [];
            const error_list = get_dict_value(update_dict, ["error"], []);
            //console.log("error_list", error_list);

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

            // NIU: const col_hidden = (columns_hidden[page_tblName]) ? columns_hidden[page_tblName] : [];

// ++++ created ++++
            // PR2021-06-16 from https://stackoverflow.com/questions/586182/how-to-insert-an-item-into-an-array-at-a-specific-index-javascript
            //arr.splice(index, 0, item); will insert item into arr at the specified index
            // (deleting 0 items first, that is, it's just an insert).

            if(is_created){
    // ---  first remove key 'created' from update_dict
                delete update_dict.created;

    // --- lookup index where new row must be inserted in data_rows
                // not necessary:
                // rows are sorted by id int. new row always has a bigger int, therefore new dict can go at the end
                // was: insert new row in data_rows. Splice inserts row at index, 0 means deleting zero rows
                //      data_rows.splice(map_index, 0, update_dict);

    // ---  insert new item at end
                data_rows.push(update_dict)

    // ---  create row in table., insert in alphabetical order
                const new_tblRow = CreateTblRow(page_tblName, field_setting, update_dict)

    // ---  scrollIntoView,
                if(new_tblRow){
                    new_tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' })

    // ---  make new row green for 2 seconds,
                    ShowOkElement(new_tblRow);
                }
            } else {

// --- get existing data_dict from map_id
                const [dict, index] = get_datadict_with_index_from_mapid(map_id);
                const data_dict = dict;
                const datarow_index = index;

// ++++ deleted ++++
                if(is_deleted){
                    // delete row from data_rows. Splice returns array of deleted rows
                    const deleted_row_arr = data_rows.splice(datarow_index, 1)
                    const deleted_row_dict = deleted_row_arr[0];

        //--- delete tblRow
                    if(deleted_row_dict && deleted_row_dict.mapid){
                        const tblRow_tobe_deleted = document.getElementById(deleted_row_dict.mapid);
        //console.log("tblRow_tobe_deleted", tblRow_tobe_deleted);
                        if (tblRow_tobe_deleted ){tblRow_tobe_deleted.parentNode.removeChild(tblRow_tobe_deleted)};
                    }
                } else {

// +++++++++++ updated row +++++++++++
    // ---  check which fields are updated, add to list 'updated_columns'
                    if(!isEmpty(data_dict) && field_names){
                        let updated_columns = [];

                        // skip first column (is margin)
                        // col_field is the name of the column on page, not the db_field
                        for (let i = 1, col_field, old_value, new_value; col_field = field_names[i]; i++) {
                            let has_changed = false;
                            if (col_field.slice(0, 5) === "group") {
                            // data_dict.usergroups example: "anlz;auth1;auth2;auth3;edit;read"
                                const usergroup = col_field.slice(6);
                                // usergroup_in_data_dict and usergroup_in_update_dict are necessary to catch empty usergroup field
                                const usergroup_in_data_dict = (!!data_dict.usergroups && data_dict.usergroups.includes(usergroup));
                                const usergroup_in_update_dict = (!!update_dict.usergroups && update_dict.usergroups.includes(usergroup));
                                has_changed = usergroup_in_data_dict != usergroup_in_update_dict;

                            } else if (col_field in data_dict && col_field in update_dict){
                                has_changed = (data_dict[col_field] !== update_dict[col_field] );
                            };
                            if (has_changed){
        // ---  add field to updated_columns list
                                updated_columns.push(col_field)
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
                                // to make it perfect: move row when username have changed
                                if (updated_columns.includes("username")){
                                //--- delete current tblRow
                                    tblRow.parentNode.removeChild(tblRow);
                                //--- insert row new at new position
                                    tblRow = CreateTblRow(page_tblName, field_setting, update_dict)
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
        };  // if(!isEmpty(update_dict)){
    }  // RefreshDatarowItem


//###########################################################################
// +++++++++++++++++ FILTER ++++++++++++++++++++++++++++++++++++++++++++++++++

//========= HandleFilterKeyup  ================= PR2021-03-23
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
            Filter_TableRows(tblBody_datatable);
        }
    }; // function HandleFilterKeyup


//========= HandleFilterToggle  =============== PR2020-07-21 PR2020-09-14 PR2021-03-23
    function HandleFilterToggle(el_input) {
        //console.log( "===== HandleFilterToggle  ========= ");

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

        } else if(filter_tag === "toggle") {
            // default filter triple '0'; is show all, '1' is show tickmark, '2' is show without tickmark
// - toggle filter value
            new_value = (filter_value === "2") ? "0" : (filter_value === "1") ? "2" : "1";
// - get new icon_class
            icon_class =  (new_value === "2") ? "tickmark_2_1" : (new_value === "1") ? "tickmark_2_2" : "tickmark_0_0";
        }

    // - put new filter value in filter_dict
        filter_dict[col_index] = [filter_tag, new_value]
        //console.log( "filter_dict", filter_dict);
        el_input.className = icon_class;
        Filter_TableRows(tblBody_datatable);

    };  // HandleFilterToggle

//========= Filter_TableRows  ====================================
    function Filter_TableRows() {  // PR2019-06-09 PR2020-08-31
        console.log( "===== Filter_TableRows=== ");
        //console.log( "filter_dict", filter_dict);

        // function filters by inactive and substring of fields
        //  - iterates through cells of tblRow
        //  - skips filter of new row (new row is always visible)
        //  - if filter_name is not null:
        //       - checks tblRow.cells[i].children[0], gets value, in case of select element: data-value
        //       - returns show_row = true when filter_name found in value
        //  - if col_inactive has value >= 0 and hide_inactive = true:
        //       - checks data-value of column 'inactive'.
        //       - hides row if inactive = true
        let item_count = 0

// ---  loop through tblBody.rows
        for (let i = 0, tblRow, show_row; tblRow = tblBody_datatable.rows[i]; i++) {
            show_row = t_ShowTableRowExtended(filter_dict, tblRow);
            add_or_remove_class(tblRow, cls_hide, !show_row);
            if (show_row) {item_count += 1};
        }
// ---  show total in sidebar
        if (el_SBR_item_count){
            let inner_text = null;
            if (item_count){
                const format_count = f_format_count(setting_dict.user_lang, item_count);
                const unit_txt = ((item_count === 1) ? loc.Message : loc.Messages).toLowerCase();
                inner_text = [loc.Total, format_count, unit_txt].join(" ");
            }
            el_SBR_item_count.innerText = inner_text;
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

        Filter_TableRows(tblBody_datatable);

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
        //console.log( "===== MSED_Response ========= ");

// ---  upload new selected_pk
        new_setting.page = setting_dict.sel_page;
// also retrieve the tables that have been changed because of the change in examyear / dep
        const datalist_request = {
                setting: new_setting,
                user_rows: {get: true},
                school_rows: {get: true}
            };
        DatalistDownload(datalist_request);

    }  // MSED_Response
//###########################################################################
//=========  MSSSS_Response  ================ PR2021-04-23  PR2021-07-26
    function MSSSS_Response(tblName, selected_dict, selected_pk) {
        //console.log( "===== MSSSS_Response ========= ");

        // Note: when tblName = school: pk_int = schoolbase_pk
        if(selected_pk === -1) { selected_pk = null};

// ---  put new selected_pk in setting_dict
        setting_dict.sel_schoolbase_pk = selected_pk;

// ---  upload new setting and refresh page
        let datalist_request = {setting: {page: "page_user", sel_schoolbase_pk: selected_pk}};
        DatalistDownload(datalist_request);

    }  // MSSSS_Response


//###########################################################################

//========= get_datadict_with_index_from_mapid  ====== PR2021-08-01
    function get_datadict_with_index_from_mapid(map_id) {
        //console.log( "===== get_datadict_with_index_from_mapid  === ");
        let data_dict = null, row_index = null;
        if(map_id){
            const arr = get_tblName_pk_from_mapid(map_id);
            if(arr && arr[1] && Number(arr[1])){
                const data_rows = get_data_rows(arr[0]) ;
                const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", Number(arr[1]));
                if (!isEmpty(found_dict)) {data_dict = found_dict};
                row_index = index;
            };
        };
        return [data_dict, row_index];
    };  // get_datadict_with_index_from_mapid

//========= get_datadict_from_mapid  ====== PR2021-08-01
    function get_datadict_from_mapid(map_id) {
        //console.log( "===== get_datadict_from_mapid  === ");
        let data_dict = null;
        if(map_id){
            const arr = get_tblName_pk_from_mapid(map_id);
        //console.log( "arr", arr);
            data_dict = get_datadict_from_pk(arr[0], arr[1]);
        };
        return data_dict;
    };  // get_datadict_from_mapid

    function get_datadict_from_pk(tblName, pk_int) {
        //console.log( "===== get_datadict_from_pk  === ");
        //console.log( "tblName", tblName);
        //console.log( "pk_int", pk_int, typeof pk_int );
        let data_dict = null;
        if(tblName && pk_int){
            const data_rows = get_data_rows(tblName) ;
        //console.log( "data_rows", data_rows, typeof data_rows );
            const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);
            if (!isEmpty(found_dict)) {data_dict = found_dict};

        };
        return data_dict;
    };  // get_datadict_from_pk

    function get_tblName_from_selectedBtn() {  // PR2021-09-12
        // HandleBtnSelect sets tblName to default "user" when there is no selected_btn
        // this happens when user visits page for the first time
        return  (selected_btn === "btn_received") ? "mailbox" :
                (selected_btn === "btn_sent") ? "mailbox" :
                (selected_btn === "btn_mailinglist") ? "mailinglist" : null;
    }

    function get_data_rows(tblName) {  //PR2021-09-12
        return (tblName === "mailbox") ? mailbox_rows :
                (tblName === "mailinglist") ? mailinglist_rows : null;
    }

    function get_tblName_from_mapid(map_id) {  //PR2021-08-01
        const arr = (map_id) ? map_id.split("_") : null;
        return (arr) ? arr[0] : null;
    };

    function get_tblName_pk_from_mapid(map_id) {  //PR2021-08-01
        const arr = (map_id) ? map_id.split("_") : null;
        let tblName = null, pk_int = null;
        if(arr && arr.length){
            tblName = arr[0];
            pk_int = (arr[1] && Number(arr[1])) ? Number(arr[1]) : null;
        };
        return [tblName, pk_int]
    };  // get_tblName_pk_from_mapid
})  // document.addEventListener('DOMContentLoaded', function()