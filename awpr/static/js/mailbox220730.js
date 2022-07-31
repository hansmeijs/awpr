// PR2021-09-12 added

//let selected_btn = "btn_received";
//let setting_dict = {};
//let permit_dict = {};
//let loc = {};
//let urls = {};

let mailmessage_draft_rows = [];
let mailmessage_received_rows = [];
let mailmessage_sent_rows = [];
let mailattachment_rows = [];

let mailbox_recipients_rows = [];
let mailbox_user_rows = [];
let mailbox_school_rows = [];
let mailbox_usergroup_rows = [];
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

    const mod_dict = {};
    const mod_MMM_dict = {};
    let time_stamp = null; // used in mod add user

    let user_list = [];
    let user_rows = [];
    let permit_rows = [];
    let school_rows = [];

    let examyear_map = new Map();

    let department_map = new Map();

    let permit_map = new Map();

    const filter_dict = {showinactive: false};

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    urls.url_usersetting_upload = get_attr_from_el(el_data, "data-url_usersetting_upload");
    urls.url_mailmessage_upload = get_attr_from_el(el_data, "data-url_mailmessage_upload");
    urls.url_mailbox_upload = get_attr_from_el(el_data, "data-url_mailbox_upload");
    urls.url_recipients_download = get_attr_from_el(el_data, "data-url_recipients_download");
    urls.url_mailattachment_upload = get_attr_from_el(el_data, "data-url_mailattachment_upload");
    urls.url_mailinglist_upload = get_attr_from_el(el_data, "data-url_mailinglist_upload");
    const has_new_mail = (get_attr_from_el(el_data, "data-class_has_mail") === "envelope_0_2")

// --- get field_settings
    const field_settings = {
        btn_received: { field_caption: ["", "Subject", "From", "Sender", "Date_sent", "Attachment", ""],
                    field_names: ["read", "header", "sender_school_abbrev", "sender_lastname", "sentdate", "has_att", "deleted"],
                    field_tags: ["div", "div", "div", "div", "div", "div", "div"],
                    filter_tags: ["toggle", "text", "text",  "text",  "text", "toggle", "inactive"],
                    field_width:  ["020", "360", "150", "180", "180", "090", "020"],
                    field_align: ["c", "l", "l", "l", "l",  "c",  "c"]},
        btn_sent: { field_caption: ["", "Subject", "Date_sent", "Attachment"],
                    field_names: ["select", "header", "sentdate", "has_att"],
                    field_tags: ["div", "div", "div", "div"],
                    filter_tags: ["toggle", "text", "text", "toggle"],
                    field_width:  ["020", "360", "180", "090", "020"],
                    field_align: ["c", "l", "l",  "c"]},
        btn_draft: { field_caption: ["", "Subject", "Attachment"],
                    field_names: ["select", "header", "has_att"],
                    field_tags: ["div", "div", "div"],
                    filter_tags: ["toggle", "text", "toggle"],
                    field_width:  ["020", "360", "090"],
                    field_align: ["c", "l", "c"]},
        btn_mailinglist: { field_caption: ["", "Name_of_the_mailinglist", "For_general_use"],
                    field_names: ["select", "name", "ispublic"],
                    field_tags: ["div", "div", "div"],
                    filter_tags: ["select", "text", "toggle"],
                    field_width:  ["020", "480", "180"],
                    field_align: ["c", "l", "c"]}
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

// ---  MOD MAIL MESSAGE READER ------------------------------------
        const el_MMR_message_title = document.getElementById("id_MMR_message_title");
        const el_MMR_tblBody_recipients = document.getElementById("id_MMR_tblBody_recipients");
        const el_MMR_message_txt = document.getElementById("id_MMR_message_txt");

        const el_MMR_tblBody_recipients_container = document.getElementById("id_MMR_tblBody_recipients_container");
        if (el_MMR_tblBody_recipients_container){
            el_MMR_tblBody_recipients_container.parentNode.addEventListener("click", function() {MMR_GetRecipients()}, false);
            add_hover(el_MMR_tblBody_recipients_container.parentNode);
        };
        const el_MMR_loader = document.getElementById("id_MMR_loader");
        const el_MMR_attachment_container = document.getElementById("id_MMR_attachment_container");
        const el_MMR_btn_download = document.getElementById("id_MMR_btn_download");
        if (el_MMR_btn_download){
            el_MMR_btn_download.addEventListener("click", function() {MMR_download()}, false);
        };

// ---  MOD MAIL MESSAGE  ------------------------------------
        const el_MMM_header = document.getElementById("id_MMM_header");
        const el_MMM_input_container = document.getElementById("id_MMM_input_container");

        const el_MMM_tblBody_mailinglist = document.getElementById("id_MMM_tblBody_mailinglist");
        const el_MMM_tblBody_mailinglist_container = document.getElementById("id_MMM_tblBody_mailinglist_container");
        if (el_MMM_tblBody_mailinglist_container){
            el_MMM_tblBody_mailinglist_container.addEventListener("click", function() {MMMselect_Open("ml")}, false);
            add_hover(el_MMM_tblBody_mailinglist_container);
        };

        const el_MMM_tblBody_organization = document.getElementById("id_MMM_tblBody_organization");
        const el_MMM_tblBody_organization_label = document.getElementById("id_MMM_tblBody_organization_label");
        if (el_MMM_tblBody_organization_label){
            el_MMM_tblBody_organization_label.addEventListener("click", function() {MMMselect_Open("sb")}, false);
            add_hover(el_MMM_tblBody_organization_label);
        };
        const el_MMM_tblBody_organization_table = document.getElementById("id_MMM_tblBody_organization_table");
        if (el_MMM_tblBody_organization_table){
            el_MMM_tblBody_organization_table.addEventListener("click", function() {MMMselect_Open("sb")}, false);
            add_hover(el_MMM_tblBody_organization_table);
        };
        const el_MMM_tblBody_usergroup = document.getElementById("id_MMM_tblBody_usergroup");
        const el_MMM_tblBody_usergroup_container = document.getElementById("id_MMM_tblBody_usergroup_container");
        const el_MMM_tblBody_usergroup_label = document.getElementById("id_MMM_tblBody_usergroup_label");
        if (el_MMM_tblBody_usergroup_container){
            el_MMM_tblBody_usergroup_container.addEventListener("click", function() {MMMselect_Open("ug")}, false);
            add_hover(el_MMM_tblBody_usergroup_container);
        };

        const el_MMM_tblBody_users = document.getElementById("id_MMM_tblBody_user");
        const el_MMM_tblBody_user_container = document.getElementById("id_MMM_tblBody_user_container");
        if (el_MMM_tblBody_user_container){
            el_MMM_tblBody_user_container.addEventListener("click", function() {MMMselect_Open("us")}, false);
            add_hover(el_MMM_tblBody_user_container);
        };

        const el_MMM_input_title = document.getElementById("id_MMM_input_title");
        if (el_MMM_input_title){
            el_MMM_input_title.addEventListener("keyup", function() {MMM_input_Keyup()}, false );
        };
        const el_MMM_input_message = document.getElementById("id_MMM_input_message");
        if (el_MMM_input_message){
            el_MMM_input_message.addEventListener("keyup", function() {MMM_input_Keyup()}, false );
        };

        const el_MMM_attachment_container = document.getElementById("id_MMM_attachment_container");

        const el_MMM_filedialog = document.getElementById("id_MMM_filedialog");
        if (el_MMM_filedialog){
            el_MMM_filedialog.addEventListener("change", function(){ MMM_SaveAttachment("create", el_MMM_filedialog) });
        };
        const el_MMM_add_attachment = document.getElementById("id_MMM_add_attachment");
        if (el_MMM_add_attachment){
            el_MMM_add_attachment.addEventListener("click", function(){ el_MMM_filedialog.click() });
        };

        const el_MMM_loader = document.getElementById("id_MMM_loader");
        const el_MMM_msg_error = document.getElementById("id_MMM_msg_error");
        const el_MMM_btn_delete = document.getElementById("id_MMM_btn_delete");
        if(el_MMM_btn_delete){el_MMM_btn_delete.addEventListener("click", function() {MMM_Delete()}, false)};
        const el_MMM_btn_cancel = document.getElementById("id_MMM_btn_cancel");
        const el_MMM_btn_save = document.getElementById("id_MMM_btn_save");
        if(el_MMM_btn_save){el_MMM_btn_save.addEventListener("click", function() {MMM_SaveOrSend()}, false)};
        const el_MMM_btn_send = document.getElementById("id_MMM_btn_send");
        if(el_MMM_btn_send){el_MMM_btn_send.addEventListener("click", function() {MMM_SaveOrSend(true)}, false)};

// ---  MOD MAIL MESSAGE SELECT RECIPIENT ------------------------------------
        const el_MMMselect_header = document.getElementById("id_MMMselect_header");

        const el_MMMselect_hdr_selected = document.getElementById("id_MMMselect_hdr_selected");
        const el_MMMselect_hdr_available = document.getElementById("id_MMMselect_hdr_available");

        const el_MMMselect_tblBody_select = document.getElementById("id_MMMselect_tblBody_select");
        const el_MMMselect_tblBody_available = document.getElementById("id_MMMselect_tblBody_available");

        const el_MMMselect_input_filter = document.getElementById("id_MMMselect_input_filter");
        if (el_MMMselect_input_filter){
            el_MMMselect_input_filter.addEventListener("keyup", function() {MMMselect_input_Keyup(el_MMMselect_input_filter)}, false );
        };

        const el_MMMselect_all_countries_label = document.getElementById("id_MMMselect_all_countries_label");
        const el_MMMselect_all_countries = document.getElementById("id_MMMselect_all_countries");
        if (el_MMMselect_all_countries){
            el_MMMselect_all_countries.addEventListener("change", function() {MMMselect_AllcountriesChanged(el_MMMselect_all_countries)}, false );
        };


// ---  MOD MAILING LIST  ------------------------------------
        const el_MML_header = document.getElementById("id_MML_header");
        const el_MML_input_name = document.getElementById("id_MML_input_name");
        if (el_MML_input_name){
            el_MML_input_name.addEventListener("keyup", function() {MML_name_Keyup(el_MMMselect_input_filter)}, false );
        };
        const el_MML_ispublic = document.getElementById("id_MML_ispublic");
        const el_MML_all_countries = document.getElementById("id_MML_all_countries");
        const el_MML_all_countries_label = document.getElementById("id_MML_all_countries_label");

        const el_MML_tblBody_organization = document.getElementById("id_MML_tblBody_organization");
        const el_MML_tblBody_organization_label = document.getElementById("id_MML_tblBody_organization_label");
        if (el_MML_tblBody_organization_label){
            el_MML_tblBody_organization_label.addEventListener("click", function() {MMMselect_Open("sb")}, false);
            add_hover(el_MML_tblBody_organization_label);
        };
        const el_MML_tblBody_organization_table = document.getElementById("id_MML_tblBody_organization_table");
        if (el_MML_tblBody_organization_table){
            el_MML_tblBody_organization_table.addEventListener("click", function() {MMMselect_Open("sb")}, false);
            add_hover(el_MML_tblBody_organization_table);
        };
        const el_MML_tblBody_usergroup = document.getElementById("id_MML_tblBody_usergroup");
        const el_MML_tblBody_usergroup_container = document.getElementById("id_MML_tblBody_usergroup_container");
        const el_MML_tblBody_usergroup_label = document.getElementById("id_MML_tblBody_usergroup_label");
        if (el_MML_tblBody_usergroup_container){
            el_MML_tblBody_usergroup_container.addEventListener("click", function() {MMMselect_Open("ug")}, false);
            add_hover(el_MML_tblBody_usergroup_container);
        };

        const el_MML_tblBody_users = document.getElementById("id_MML_tblBody_user");
        const el_MML_tblBody_user_container = document.getElementById("id_MML_tblBody_user_container");
        if (el_MML_tblBody_user_container){
            el_MML_tblBody_user_container.addEventListener("click", function() {MMMselect_Open("us")}, false);
            add_hover(el_MML_tblBody_user_container);
        };

        const el_MML_msg_error = document.getElementById("id_MML_msg_error");
        const el_MML_btn_delete = document.getElementById("id_MML_btn_delete");
        if(el_MML_btn_delete){el_MML_btn_delete.addEventListener("click", function() {ModConfirmOpen("mailinglist", "delete")}, false)};

        const el_MML_btn_cancel = document.getElementById("id_MML_btn_cancel");
        const el_MML_btn_save = document.getElementById("id_MML_btn_save");
        if(el_MML_btn_save){el_MML_btn_save.addEventListener("click", function() {MML_Save()}, false)};

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
                mailmessage_rows: {get: true}
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

                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    // get_permits must come before CreateSubmenu and FiLLTbl
                    isloaded_permits = true;
                }

                if(isloaded_loc && isloaded_settings){CreateSubmenu()};
                if(isloaded_settings || isloaded_permits){b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);};

                if ("messages" in response) {
                    b_show_mod_message_dictlist(response.messages);
                }

                if ("mailmessage_draft_rows" in response) {mailmessage_draft_rows = response.mailmessage_draft_rows};
                if ("mailmessage_received_rows" in response) {mailmessage_received_rows = response.mailmessage_received_rows};
                if ("mailmessage_sent_rows" in response) {mailmessage_sent_rows = response.mailmessage_sent_rows};

                if ("mailbox_user_rows" in response) {mailbox_user_rows = response.mailbox_user_rows};
                if ("mailbox_school_rows" in response) {mailbox_school_rows = response.mailbox_school_rows};
                if ("mailbox_usergroup_rows" in response) {mailbox_usergroup_rows = response.mailbox_usergroup_rows};
                if ("mailattachment_rows" in response) {mailattachment_rows = response.mailattachment_rows};
                if ("mailinglist_rows" in response) {mailinglist_rows = response.mailinglist_rows};

                HandleBtnSelect(selected_btn, true);  // true = skip_upload
            },
            error: function (xhr, msg) {
// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                console.log(msg + '\n' + xhr.responseText);
            }
        });
    }  // function DatalistDownload

//=========  CreateSubmenu  ===  PR2021-10-22
    function CreateSubmenu() {
        //console.log("===  CreateSubmenu == ");
        let el_submenu = document.getElementById("id_submenu")
        // hardcode access of system admin, to get access before action 'crud' is added to permits
        const permit_system_admin = (permit_dict.requsr_role_system && permit_dict.usergroup_list.includes("admin"));
        const permit_role_admin = (permit_dict.requsr_role_admin && permit_dict.usergroup_list.includes("admin"));

        if (permit_dict.permit_crud) {
            AddSubmenuButton(el_submenu, loc.Create_new_message, function() {MMM_Open()}, null, "id_submenu_new_message");
        }
        if (permit_dict.permit_crud) {
            AddSubmenuButton(el_submenu, loc.Create_new_mailing_list, function() {MML_Open()}, null, "id_submenu_new_mailinglist");
        }

         //el_submenu.classList.remove(cls_hide);
    };//function CreateSubmenu

//###########################################################################
// +++++++++++++++++ EVENT HANDLERS +++++++++++++++++++++++++++++++++++++++++
//=========  HandleBtnSelect  ================ PR2020-09-19 PR2021-08-01
    function HandleBtnSelect(data_btn, skip_upload) {
        //console.log( "===== HandleBtnSelect ========= ");
        //console.log( "skip_upload: ", skip_upload);

// ---  get  selected_btn
        // set to default "btn_user" when there is no selected_btn
        // this happens when user visits page for the first time
        // includes is to catch saved btn names that are no longer in use
        selected_btn = (data_btn && ["btn_received", "btn_sent", "btn_draft", "btn_mailinglist"].includes(data_btn)) ? data_btn : "btn_received"
        //console.log( "selected_btn: ", selected_btn);

// reset filter
        b_clear_dict(filter_dict);

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_mailbox: {sel_btn: selected_btn}};
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);
        };

// ---  highlight selected button
        b_highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  fill datatable
        FillTblRows();

    }  // HandleBtnSelect

//=========  HandleTblRowClicked  ================ PR2020-08-03 PR2021-08-01
    function HandleTblRowClicked(tr_clicked) {
        //console.log("=== HandleTblRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        DeselectHighlightedRows(tr_clicked, cls_selected);
        tr_clicked.classList.add(cls_selected)

    }  // HandleTblRowClicked

//========= FillTblRows  =================== PR2021-08-01
    function FillTblRows() {
        //console.log( "===== FillTblRows  === ");

        const field_setting = field_settings[selected_btn];
        const data_rows = get_data_rows_from_selected_btn();

        //console.log( "selected_btn", selected_btn);
        //console.log( "tblName", tblName);
        //console.log( "data_rows", data_rows);
        //console.log( "field_setting", field_setting);

// ---  get show_inactive - used for deleted mailbox items PR2021-10-28
        // values of showinactive are:  '0'; is show all, '1' is show active only, '2' is show inactive only

        const show_inactive = (filter_dict.showinactive) ? filter_dict.showinactive : 1;
        console.log("show_inactive", show_inactive);

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null

// --- create table header and filter row
        CreateTblHeader(field_setting);

// --- loop through data_rows
        if(data_rows && data_rows.length){
            for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
                const tblRow = CreateTblRow(selected_btn, field_setting, data_dict);
                UpdateTblRow(tblRow, selected_btn, data_dict, show_inactive);
            };
        };

// --- filter tblRows
        Filter_TableRows();
    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-07-31 PR2021-03-23  PR2021-08-01
    function CreateTblHeader(field_setting) {
        //console.log("===  CreateTblHeader ===== ");
        //console.log("field_setting", field_setting);

        const column_count = field_setting.field_names.length;

// +++  insert header and filter row ++++++++++++++++++++++++++++++++
        let tblRow_header = tblHead_datatable.insertRow (-1);
        let tblRow_filter = tblHead_datatable.insertRow (-1);

    // --- loop through columns
        for (let j = 0; j < column_count; j++) {
            const field_name = field_setting.field_names[j];

    // --- get field_caption from field_setting
            const field_caption = loc[field_setting.field_caption[j]];
            const field_tag = field_setting.field_tags[j];
            const filter_tag = field_setting.filter_tags[j];
            const class_width = "tw_" + field_setting.field_width[j] ;
            const class_align = "ta_" + field_setting.field_align[j];

// ++++++++++ create header row +++++++++++++++
    // --- add th to tblRow_header
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
                el_filter.setAttribute("data-colindex", j);

    // --- add EventListener to el_filter / th_filter
                if (["text", "number"].includes(filter_tag)) {
                    el_filter.addEventListener("keyup", function(event){HandleFilterKeyup(el_filter, event)});
                    add_hover(th_filter);

                } else if (filter_tag === "toggle"){
                    // add EventListener for icon to th_filter, not el_filter
                    th_filter.addEventListener("click", function(event){HandleFilterToggle(el_filter)});
                    th_filter.classList.add("pointer_show");

                    // default empty icon necessary to set pointer_show
                    el_filter.classList.add("tickmark_0_0");
                    add_hover(th_filter);

                } else if (filter_tag === "inactive"){
                    // add EventListener for icon to th_filter, not el_filter
                    th_filter.addEventListener("click", function(event){HandleFilterInactive(el_filter)});
                    th_filter.classList.add("pointer_show");
                    el_filter.classList.add("delete_0_1");
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

        }  // for (let j = 0; j < column_count; j++)
    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09 PR2021-08-01
    function CreateTblRow(tblName, field_setting, map_dict) {
        //console.log("=========  CreateTblRow =========");
        //console.log("tblName", tblName);
        //console.log("map_dict", map_dict);

        const field_names = field_setting.field_names;
        const field_tags = field_setting.field_tags;
        const filter_tags = field_setting.filter_tags;
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;

        const map_id = (map_dict.mapid) ? map_dict.mapid : null;

// ---  lookup index where this row must be inserted
        // sort by descending sent date
        const ob1 = (map_dict.sentdate) ? map_dict.sentdate : "";
        const ob2 = (map_dict.username) ? map_dict.username : "";

        const row_index = b_recursive_tblRow_lookup(tblBody_datatable, setting_dict.user_lang, ob1, ob2, "", true);

        //console.log("ob1", ob1);
        //console.log("ob2", ob2);
        //console.log("row_index", row_index);

// --- insert tblRow into tblBody at row_index
        const tblRow = tblBody_datatable.insertRow(row_index);
        if(map_dict.mapid){tblRow.id = map_dict.mapid};
        //console.log("tblRow", tblRow);

// --- add data attributes to tblRow
        tblRow.setAttribute("data-table", tblName);
        tblRow.setAttribute("data-pk", map_dict.id);
        tblRow.setAttribute("data-mailbox_pk", map_dict.mailbox_id);
        tblRow.setAttribute("data-mailinglist_pk", map_dict.mailinglist_id);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);
        tblRow.setAttribute("data-ob2", ob2);

// --- add EventListener to tblRow
        tblRow.addEventListener("click", function() {HandleTblRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
        for (let j = 0; j < column_count; j++) {
            const field_name = field_names[j];

    // - skip column if field_name in columns_hidden;
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

// --- add EventListener to td
            if (["read", "deleted"].includes(field_name)){
                td.addEventListener("click", function() {HandleBtnReadDelete(el)}, false)
                td.classList.add("pointer_show");
                if (field_name === "deleted"){
                    add_hover_delete_btn(el,"delete_0_2", "delete_0_2", "delete_0_1");
                } else {
                    add_hover(el);
                }

            } else if (["sender_school_abbrev", "sender_lastname", "header", "sentdate", "has_att", "status"].includes(field_name)){
                if(["btn_received", "btn_sent"].includes(tblName)){
                    el.addEventListener("click", function() {MMR_Open(el)}, false)
                } else {
                    el.addEventListener("click", function() {MMM_Open(el)}, false)
                };
                el.classList.add("pointer_show");
                add_hover(el);
            } else if (["name"].includes(field_name)){
                el.addEventListener("click", function() {MML_Open(el)}, false)
                el.classList.add("pointer_show");
                add_hover(el);
            };
        }  // for (let j = 0; j < 8; j++)
        return tblRow
    };  // CreateTblRow

//=========  UpdateTblRow  ================ PR2020-08-01 PR2021-10-28
    function UpdateTblRow(tblRow, tblName, map_dict, show_inactive) {
        //console.log("=========  UpdateTblRow =========");
        //console.log("tblName", tblName);
        //console.log("map_dict", map_dict);
        if (tblRow && tblRow.cells){

// ---  set tblRow attr data-deleted, hide tblRow when deleted and filter_inactive
            if (tblName === "mailbox") {

                const data_inactive_field = "data-deleted";
                const is_inactive = map_dict.deleted;
                tblRow.setAttribute(data_inactive_field, (is_inactive) ? 1 : 0);
                const hide_row = (!show_inactive && is_inactive);

        //console.log("is_inactive", is_inactive);
        //console.log("show_inactive", show_inactive);
        //console.log("hide_row", hide_row);
                add_or_remove_class(tblRow, cls_hide, hide_row)
            }
            for (let i = 0, td; td = tblRow.cells[i]; i++) {
                UpdateField(td.children[0], map_dict);
            }
        }
    };  // UpdateTblRow

//=========  UpdateField  ================ PR2020-08-16 PR2021-03-23 PR2021-08-01
    function UpdateField(el_div, map_dict) {
        //console.log("=========  UpdateField =========");
        //console.log("map_dict", map_dict);

        const field_name = get_attr_from_el(el_div, "data-field");
        //console.log("field_name", field_name);
        
        if(el_div && field_name){
            let inner_text = null, title_text = null, filter_value = null;
            if (field_name === "read") {
                // give value '1' when not_read, '0' when read
                filter_value = (!map_dict.read) ? "1" : "0";
                el_div.className = (!map_dict.read) ? "mail_0_2" : "tickmark_0_0";
            } else if (field_name === "deleted") {
                // give value '1' when deleted, '0' when not deleted
                filter_value = (map_dict.deleted) ? "1" : "0";
                el_div.className = (map_dict.deleted) ? "delete_0_2" : "delete_0_1";
                const el_td = el_div.parentNode;
                el_td.title = (map_dict.deleted) ? loc.Undelete_this_message : loc.Delete_this_message;
                el_td.parentNode.setAttribute("data-deleted", filter_value);
            } else if (field_name === "has_att") {
                // give value '1' when not_read, '0' when read
                filter_value = (map_dict.has_att) ? "1" : "0";
                el_div.className = (map_dict.has_att) ? "note_1_8" : "tickmark_0_0";

        //console.log("map_dict.has_att", map_dict.has_att);

            } else if (["sender_school_abbrev", "sender_lastname", "header", "status", "name"].includes(field_name)){
                inner_text = (map_dict[field_name]) ? map_dict[field_name] : "\xa0";  // Non-breakable space is char 0xa0 (160 dec), needed for eventhandler
                filter_value = (inner_text) ? inner_text.toLowerCase() : null;
                if ( field_name === "header" && map_dict.body) {
                    title_text = map_dict.body ;
                };
            } else if (field_name === "ispublic") {
        //console.log("map_dict", map_dict);
                const is_public = (!map_dict.user_id);
        //console.log("is_public", is_public);
                // give value '1' when is_public, '0' when private
                filter_value = (is_public) ? "1" : "0";
                el_div.className = (is_public) ? "tickmark_1_2" : "tickmark_0_0";

// ---  add title
                title_text = (is_public) ? loc.Mailinglist_canbe_used_byallusers : null;
            } else if (["sentdate", "modifiedat"].includes(field_name)) {
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
                    let refresh_page = false;
                    if("msg_dictlist" in response){
                        b_show_mod_message_dictlist(response.msg_dictlist);
                    }

                    const mode = get_dict_value(response, ["mode"]);
                    if(mode === "delete") {
                        ModConfirmResponse(response);
                    };

                    if("mailinglist_messages" in response){
                        ModConfirmResponseNEW(response);
                    }
                    if ("updated_mailinglist_rows" in response){
                         RefreshDataRows("btn_mailinglist", response.updated_mailinglist_rows, mailinglist_rows, true);
                    }
                    if ("updated_mailmessage_received_rows" in response){
                        // only used to change read and deleted
                        RefreshDataRows("btn_received", response.updated_mailmessage_received_rows, mailmessage_received_rows, true);
                    }
                    if ("updated_mailmessage_sent_rows" in response){
                        refresh_page = true;
                        RefreshDataRows("btn_sent", response.updated_mailmessage_sent_rows, mailmessage_sent_rows, true);
                    }
                    if ("updated_mailmessage_draft_rows" in response){
                        refresh_page = true;
                        RefreshDataRows("btn_draft", response.updated_mailmessage_draft_rows, mailmessage_draft_rows, true);
                    }

                    if ("mailbox_recipients_rows" in response) {
                        mailbox_recipients_rows = response.mailbox_recipients_rows;
                        MMR_FillRecipients();
                    };
                    if ("mailmessage_log_list" in response) {
                        refresh_page = true;
                        OpenLogfile(loc, response.mailmessage_log_list);

                    };
                    if ("class_has_mail" in response){
                        const el_hdrbar_has_mail = document.getElementById("id_hdrbar_has_mail")
                        if(el_hdrbar_has_mail && response.class_has_mail) {
                            el_hdrbar_has_mail.className = response.class_has_mail;
                         }
                    }

                    if(refresh_page){
                        // refresh the whole page when a message is sent.
                        const datalist_request = {mailmessage_rows: {get: true}};
                        DatalistDownload(datalist_request, "DOMContentLoaded");
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
//=========  ModConfirmOpen  ================ PR2021-10-24
    function ModConfirmOpen(tblName, mode) {
        console.log(" -----  ModConfirmOpen   ----")
        console.log(" -----  mod_MMM_dict   ----", mod_MMM_dict)
        console.log("permit_dict", permit_dict)
        // only called by  el_MML_btn_delete

        const header_txt = loc.Delete_mailing_list;
        let btn_cancel_txt = loc.Cancel;
        let btn_save_txt = loc.OK;
        let msg_list = [];
        let hide_save_btn = false;

        b_clear_dict(mod_dict);
        mod_dict.tblName = tblName;
        mod_dict.mode = mode;
        mod_dict.mailinglist_pk = mod_MMM_dict.mailinglist_pk;
        mod_dict.mapid = mod_MMM_dict.mapid;
        mod_dict.user_id = mod_MMM_dict.user_id;

        if (tblName === "mailinglist"){
            if (mode ==="delete"){
                if(!mod_MMM_dict.ispublic){
                    msg_list = [loc.Mailing_list + " '" + mod_MMM_dict.name + "'" + loc.will_be_deleted,
                        loc.Do_you_want_to_continue];
                        btn_cancel_txt = loc.No_cancel;
                        btn_save_txt = loc.Yes_delete;
                } else {
                    if(permit_dict.usergroup_list && permit_dict.usergroup_list.includes("admin")){
                        msg_list = [loc.Mailing_list + " '" + mod_MMM_dict.name + "' " + loc.is_general_mailinglist,
                                loc.canbe_usedby_allusers,
                                loc.Areyousure_youwantto_delete];
                        btn_cancel_txt = loc.No_cancel;
                        btn_save_txt = loc.Yes_delete;
                    } else {
                        msg_list = [loc.Mailing_list + " '" + mod_MMM_dict.name + "'" + loc.is_general_mailinglist,
                                loc.Can_only_delete_by_sysadm];
                        hide_save_btn = true;
                        btn_cancel_txt = loc.Close;
                    };
                };

                el_confirm_header.innerText = header_txt;
                el_confirm_loader.classList.add(cls_visible_hide)
                el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");

                const msg_html = (msg_list.length) ? msg_list.join("<br>") : null;
                el_confirm_msg_container.innerHTML = msg_html;

                //el_confirm_msg_container.classList.add("border_bg_transparent");

                add_or_remove_class (el_confirm_btn_save, cls_hide, hide_save_btn);
                add_or_remove_class (el_confirm_btn_save, "btn-primary", (mode !== "delete"));
                add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", (mode === "delete"));

                el_confirm_btn_cancel.innerText = btn_cancel_txt;
                el_confirm_btn_save.innerText = btn_save_txt;

        // set focus to cancel button
                set_focus_on_el_with_timeout(el_confirm_btn_cancel, 150);
            };
        };
// show modal
       $("#id_mod_confirm").modal({backdrop: true});
    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2021-10-24
    function ModConfirmSave() {
        //console.log(" --- ModConfirmSave --- ");
        //console.log("mod_dict: ", mod_dict);
        let tblRow = document.getElementById(mod_dict.mapid);
        //console.log("tblRow: ", tblRow);
        // only called by delete mailinglistow

// ---  when delete: make tblRow red, before uploading
        if (tblRow && mod_dict.mode === "delete"){
            ShowClassWithTimeout(tblRow, "tsa_tr_error");
        }

        let close_modal = false, url_str = null;
        const upload_dict = {
            mode: mod_dict.mode,
            mapid: mod_dict.mapid,
            mailinglist_pk: mod_dict.mailinglist_pk
        };

        if(mod_dict.mode === "delete") {
// show loader
            el_confirm_loader.classList.remove(cls_visible_hide)
        }

// ---  Upload Changes
        url_str = urls.url_mailinglist_upload;

// ---  Upload changes
        UploadChanges(upload_dict, url_str);

// ---  hide modal
        if(close_modal) {
            $("#id_mod_confirm").modal("hide");
        }
    }  // ModConfirmSave

//=========  ModConfirmResponseNEW  ================ PR2019-10-24
    function ModConfirmResponseNEW(response) {
        console.log(" --- ModConfirmResponseNEW --- ");
        console.log("mod_dict: ", mod_dict);

    // - hide loader
        el_confirm_loader.classList.add(cls_visible_hide)
        if ("mailinglist_messages" in response) {
            const msg_list = response.mailinglist_messages;
            if (msg_list && msg_list.length){
                // msg_list only contains 1 message
                const msg_dict = msg_list[0];
                if(msg_dict){
                    el_confirm_msg_container.classList.add(msg_dict.class);
                    el_confirm_msg_container.innerHTML = msg_dict.msg_html;
                }
            }
            el_confirm_btn_cancel.innerText = loc.Close
            el_confirm_btn_save.classList.add(cls_hide);

        } else {
        // hide mod_confirm when no message
            $("#id_mod_confirm").modal("hide");
        }
    }  // ModConfirmResponseNEW

//=========  ModConfirmResponse  ================ PR2019-06-23
    function ModConfirmResponse(response) {
        console.log(" --- ModConfirmResponse --- ");
        console.log("mod_dict: ", mod_dict);
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

// +++++++++++++++++ REFRESH DATA ROWS ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataRows  ================ PR2021-10-12
    function RefreshDataRows(tblName, update_rows, data_rows, is_update) {
        console.log(" --- RefreshDataRows  ---");
        console.log("tblName", tblName);
        console.log("update_rows", update_rows);
        console.log("is_update", is_update);
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

//=========  RefreshDatarowItem  ================ PR2021-08-01
    function RefreshDatarowItem(tblName, field_setting, update_dict, data_rows) {
        console.log(" --- RefreshDatarowItem  ---");
        console.log("tblName", tblName);
        console.log("field_setting", field_setting);
        console.log("update_dict", update_dict);
        console.log("data_rows", data_rows);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);
    //console.log("is_created", is_created);
    //console.log(".........update_dict.mapid", update_dict.mapid);

            // field_error_list is not in use (yet)
            let field_error_list = [];
            const error_list = get_dict_value(update_dict, ["error"], []);

            if(error_list && error_list.length){
    // - show modal messages
                b_show_mod_message_dictlist(error_list);

    // - add fields with error in field_error_list, to put old value back in field
                //for (let i = 0, msg_dict ; msg_dict = error_list[i]; i++) {
                //    if ("field" in msg_dict){field_error_list.push(msg_dict.field)};
                //};
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
                // not necessary:
                // rows are sorted by id int. new row always has a bigger int, therefore new dict can go at the end
                // was: insert new row in data_rows. Splice inserts row at index, 0 means deleting zero rows
                //      data_rows.splice(map_index, 0, update_dict);

    // ---  insert new item at end
                data_rows.push(update_dict)

    //console.log("data_rows pushed", data_rows);

    // ---  create row in table., insert in alphabetical order
                // TODO show_inactive
                const show_inactive = false;
                const new_tblRow = CreateTblRow(tblName, field_setting, update_dict);
                UpdateTblRow(new_tblRow, selected_btn, update_dict, show_inactive);

    // ---  scrollIntoView,
                if(new_tblRow){
                    new_tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' })

    // ---  make new row green for 2 seconds,
                    ShowOkElement(new_tblRow);
                }
            } else {

// --- get existing data_dict from map_id
                const data_rows = get_data_rows_from_selected_btn();

                const [middle_index, data_dict, compare] = b_recursive_integer_lookup(data_rows, "id", update_dict.id);
                const datarow_index = middle_index;

// ++++ deleted ++++ only used in draft messages and mailinglist
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
    // ---  loop through fields in update_dict
                        for (const [key, new_value] of Object.entries(update_dict)) {
                            if (key in data_dict){
                                if (new_value !== data_dict[key]) {
    // ---  update field in data_row
                                    data_dict[key] = new_value;

    // ---  add field to updated_columns list
                                    if (field_names.includes(key)) {
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
                        if(updated_columns.length || field_error_list.length){

// --- get existing tblRow
                            let tblRow = document.getElementById(map_id);

                            if(tblRow){

                // loop through cells of row
                                for (let i = 0, el_fldName, el, td; td = tblRow.cells[i]; i++) {
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

//========= HandleFilterInactive  =============== PR2021-11-03
    function HandleFilterInactive(el_filter) {
        console.log( "===== HandleFilterInactive  ========= ");

// --- PR2021-10-28 new way of filtering inactive rows( in this page 'deleted' rows):
        //  - filter_dict has key 'showinactive'
        //  - when showinactive is true: also inactive items are shown
        // values of showinactive are:  '0'; is show all, '1' is show active only, '2' is show inactive only
        const old_filter_showinactive = (filter_dict.showinactive) ? filter_dict.showinactive : 1;
        filter_dict.showinactive = (!old_filter_showinactive) ? 1 : 0;
        console.log( "filter_dict", filter_dict);

        el_filter.className = (filter_dict.showinactive) ? "delete_0_2" : "delete_0_1";

        Filter_TableRows();

    };  // HandleFilterInactive
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
            Filter_TableRows();
        }
    }; // function HandleFilterKeyup

//========= HandleFilterToggle  =============== PR2020-07-21 PR2020-09-14 PR2021-03-23  PR2021-10-28
    function HandleFilterToggle(el_filter) {
        console.log( "===== HandleFilterToggle  ========= ");

// --- PR2021-10-28 new way of filtering inactive rows( in this page 'deleted' rows):
        //  - filter_dict has key 'showinactive'
        //  - when showinactive is true: also inactive items are shown

        const tblName = get_attr_from_el(el_filter, "data-table");

    // - get col_index and filter_tag from  el_filter
        const col_index = get_attr_from_el(el_filter, "data-colindex")
        const filter_tag = get_attr_from_el(el_filter, "data-filtertag")
        const field_name = get_attr_from_el(el_filter, "data-field")

        console.log( "field_name", field_name);
        console.log( "filter_tag", filter_tag);

    // - get current value of filter from filter_dict, set to '0' if filter doesn't exist yet
        const filter_array = (col_index in filter_dict) ? filter_dict[col_index] : [];
        const filter_value = (filter_array[1]) ? filter_array[1] : "0";
        let new_value = "0", icon_class = "tickmark_0_0"
        if(field_name === "is_active") {
// - toggle filter value NOT IN USE
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
            if (field_name === "read"){
                icon_class =  (new_value === "2") ? "mail_0_1" : (new_value === "1") ? "mail_0_2" : "tickmark_0_0";
            } else if (field_name === "deleted"){
                icon_class =  (new_value === "2") ? "delete_0_1" : (new_value === "1") ? "delete_0_2" : "tickmark_0_0";
            } else {
                icon_class =  (new_value === "2") ? "tickmark_2_1" : (new_value === "1") ? "tickmark_2_2" : "tickmark_0_0";
            }
        }

        console.log( "new_value", new_value);
        console.log( "icon_class", icon_class);

    // - put new filter value in filter_dict
        filter_dict[col_index] = [filter_tag, new_value]
        //console.log( "filter_dict", filter_dict);
        el_filter.className = icon_class;

        Filter_TableRows();

    };  // HandleFilterToggle




//========= Filter_TableRows  ====================================
    function Filter_TableRows() {  // PR2019-06-09 PR2020-08-31 PR2021-10-24
        console.log( "===== Filter_TableRows=== ");
        console.log( "filter_dict", filter_dict);

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
        const data_inactive_field = "data-deleted";

// ---  loop through tblBody.rows
        for (let i = 0, tblRow, show_row; tblRow = tblBody_datatable.rows[i]; i++) {
            show_row = t_Filter_TableRow_Extended(filter_dict, tblRow, data_inactive_field);
            add_or_remove_class(tblRow, cls_hide, !show_row);
            if (show_row) {item_count += 1};
        }

// ---  show total in sidebar
        let inner_txt = null;
        if (el_SBR_item_count){
            if (item_count){
                const is_mailinglist = (selected_btn === "btn_mailinglist");
                const format_count = f_format_count(setting_dict.user_lang, item_count);
                const unit_txt = ((item_count === 1) ?
                                ( (is_mailinglist) ? loc.Mailing_list : loc.Message )  :
                                ( (is_mailinglist) ? loc.Mailing_lists : loc.Messages ) ).toLowerCase();
                inner_txt = [loc.Total, format_count, unit_txt].join(" ");
            };
        };
        el_SBR_item_count.innerText = inner_txt;
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

// - reset filter_dict
        b_clear_dict(filter_dict);

//- PR2021-10-29 debug. must also reset mod_MMM_dict.filter
        mod_MMM_dict.filter = null;

// - PR2021-10-28 shows inactive items when filter_dict.showinactive
        // values of showinactive are:  '0'; is show all, '1' is show active only, '2' is show inactive only
        filter_dict.showinactive = 1;

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
//========= HandleBtnReadDelete  ============= PR2021-05-12  PR2021-10-28
    function HandleBtnReadDelete (el_input, mark_as_read) {
        console.log("===  HandleBtnReadDelete  =====") ;

        let mailmessage_pk = null, mailbox_pk = null, fldName = null;
        if (mark_as_read){
            fldName = "read";
            mailmessage_pk = mod_MMM_dict.mailmessage_pk;
            mailbox_pk = mod_MMM_dict.mailbox_pk;
        } else if (el_input){
            const tblRow = t_get_tablerow_selected(el_input);
            fldName = get_attr_from_el(el_input, "data-field");
            mailmessage_pk = get_attr_from_el_int(tblRow, "data-pk");
            mailbox_pk = get_attr_from_el_int(tblRow, "data-mailbox_pk");

        };
        console.log("mailmessage_pk", mailmessage_pk) ;
        console.log("mailbox_pk", mailbox_pk) ;

        if(mailmessage_pk){
            const lookup_2_field = (mailbox_pk) ? "mailbox_id" : null;
            const search_2_int =  (mailbox_pk) ? mailbox_pk : null;
            const [middle_index, data_dict, compare] = b_recursive_integer_lookup(mailmessage_received_rows, "id", mailmessage_pk, lookup_2_field, search_2_int);
    console.log("data_dict", data_dict);

            if(!isEmpty(data_dict)){

                const old_value = data_dict[fldName];
    console.log("fldName", fldName) ;
                let update_dict = {};
                const new_value = (!old_value) ;

// ---  change icon, before uploading
                const class_str = (fldName === "read") ? "mail_0_2" : "delete_0_2"
                const class_default = (fldName === "read") ? "tickmark_0_0" : "delete_0_1"
                //add_or_remove_class(el_input, "mail_0_2", new_value, "tickmark_0_0");

                update_dict[fldName] = new_value;
                UpdateField(el_input, update_dict)

// ---  upload changes
                const upload_dict = {
                    mailbox_pk: data_dict.mailbox_id
                }
                upload_dict[fldName] = new_value;

                const url_str = urls.url_mailbox_upload
                UploadChanges(upload_dict, url_str);
            };  //  if(!isEmpty(data_dict)){
        }  //   if(!!tblRow)
    };  // HandleBtnReadDelete

//========= MOD MAIL MESSAGE READER Open===================== PR2021-10-14 PR2021-10-24
    function MMR_Open (el_input) {
        console.log("===  MMR_Open  =====") ;
        //console.log("el_input", el_input) ;

// reset mod_MMM_dict
        b_clear_dict(mod_MMM_dict);
        mod_MMM_dict.is_mod_MML = false;  // MML = mod mailing list

// reset input fields
        // reset tblBodies happens in MMM_FillSelectTables
        el_MMR_message_title.innerText = null;
        el_MMR_tblBody_recipients.innerText = null;
        el_MMR_message_txt.value = null;
        el_MMR_attachment_container.innerText = null;

        // reset attachments happens in MMM_FillAttachments

        const tblRow = t_get_tablerow_selected(el_input);
        const tblName = get_attr_from_el(tblRow, "data-table");
        const mailmessage_pk = get_attr_from_el_int(tblRow, "data-pk");
        const mailbox_pk = get_attr_from_el_int(tblRow, "data-mailbox_pk");

        console.log("tblRow", tblRow) ;
        console.log("mailmessage_pk", mailmessage_pk) ;
        console.log("mailbox_pk", mailbox_pk) ;

// --- get existing data_dict
        const data_rows = get_data_rows_from_selected_btn();
    console.log("tblName", tblName) ;
    console.log("data_rows", data_rows) ;

        const lookup_2_field = (mailbox_pk) ? "mailbox_id" : null;
        const search_2_int =  (mailbox_pk) ? mailbox_pk : null;
        const [middle_index, data_dict, compare] = b_recursive_integer_lookup(data_rows, "id", mailmessage_pk, lookup_2_field, search_2_int);
    console.log("data_dict", data_dict) ;

        if (!isEmpty(data_dict)) {
            mod_MMM_dict.mailmessage_pk = data_dict.id;
            mod_MMM_dict.mailbox_pk = data_dict.mailbox_id;
            mod_MMM_dict.header = data_dict.header;
            mod_MMM_dict.body = data_dict.body;
            mod_MMM_dict.sender_user_id = data_dict.sender_user_id;

            mod_MMM_dict.issaved = data_dict.issaved;
            mod_MMM_dict.sentdate = data_dict.sentdate;
            mod_MMM_dict.read = data_dict.read;

    // - hide table with recipients, hide loader
            mod_MMM_dict.show_recipients = false;
            add_or_remove_class(el_MMR_tblBody_recipients_container, cls_hide, !mod_MMM_dict.show_recipients);
            add_or_remove_class(el_MMR_loader, cls_hide, true);

    // - fill list with attachments
            MMM_FillAttachments(true);

    // - set message title and text
            el_MMR_message_title.innerText = (data_dict.header) ? data_dict.header : null;
            el_MMR_message_txt.value =  (data_dict.body) ? data_dict.body : null;

            $("#id_mod_mailmessagereader").modal({backdrop: true});

    // - mark this message as 'read'
            if (!mod_MMM_dict.read){
                HandleBtnReadDelete (null, true);
            };

        };
    }  // MMR_Open

//========= MMR_GetRecipients  ============= PR2021-11-01
    function MMR_GetRecipients() {
        console.log("===== MMR_GetRecipients ===== ");
        console.log("mod_MMM_dict.mailmessage_pk", mod_MMM_dict.mailmessage_pk);

// ---  toggle show_recipients
        mod_MMM_dict.show_recipients = !mod_MMM_dict.show_recipients

        add_or_remove_class(el_MMR_loader, cls_hide, !mod_MMM_dict.show_recipients);

// ---  hide table recipients for now - wil be shown after response from UploadChanges
        add_or_remove_class(el_MMR_tblBody_recipients_container, cls_hide, true);

        if (mod_MMM_dict.show_recipients){
            const upload_dict = {mailmessage_pk: mod_MMM_dict.mailmessage_pk}

    // ---  Upload changes
            const url_str = urls.url_recipients_download;
            UploadChanges(upload_dict, url_str);
// ---  FillRecipients happens after response from UploadChanges
        };
    };

//========= MMR_FillRecipients  ============= PR2021-10-31
    function MMR_FillRecipients() {
        console.log("===== MMR_FillRecipients ===== ");
        console.log("mod_MMM_dict.mailmessage_pk", mod_MMM_dict.mailmessage_pk);

// ---  reset tblBody selectuser, recipient and cc
        el_MMR_tblBody_recipients.innerText = null;
        add_or_remove_class(el_MMR_loader, cls_hide, true);

        console.log("mod_MMM_dict.show_recipients", mod_MMM_dict.show_recipients);
        console.log("mailbox_recipients_rows", mailbox_recipients_rows);
// ---  fill table
        if (mod_MMM_dict.show_recipients){
            if(mod_MMM_dict.mailmessage_pk && mailbox_recipients_rows){
                for (let i = 0, row; row = mailbox_recipients_rows[i]; i++) {
        console.log("row", row);
                    if (row.id === mod_MMM_dict.mailmessage_pk){
                        MMR_CreateSelectRow(row.school_name, row.school_code)
        console.log("row.school_name", row.school_name);
                        if ("au_lastname_arr" in row){
                            for (let j = 0, au_lastname; au_lastname = row.au_lastname_arr[j]; j++) {
                                MMR_CreateSelectRow(au_lastname)
        }}}}}};

        console.log("el_MMR_tblBody_recipients_container", el_MMR_tblBody_recipients_container);
        add_or_remove_class(el_MMR_tblBody_recipients_container, cls_hide, !mod_MMM_dict.show_recipients);
    }; // MMR_FillRecipients

//========= MMR_CreateSelectRow  ============= PR2021-10-31
    function MMR_CreateSelectRow(name, code) {
        console.log("===== MMR_CreateSelectRow ===== ");
        console.log("code", code);
        console.log("name", name);

// ---  insert tblBody_select row at the end ( rows are sorted)
        const tblRow = el_MMR_tblBody_recipients.insertRow(-1);

        console.log("tblRow", tblRow);

// ---  tblRow contains user when code = null
        const is_user = !code;

// --- add first td to tblRow.
        let td = tblRow.insertCell(-1);
        let el_div = document.createElement("div");
            if (!is_user) { el_div.innerHTML = "<b>" + code + "</b>"};
            el_div.classList.add("tw_075");
            td.appendChild(el_div);
        td.classList.add("tsa_bc_transparent");

// --- add second td to tblRow.
        td = tblRow.insertCell(-1);
        el_div = document.createElement("div");
            el_div.innerHTML = (is_user) ? name :  "<b>" + name + "</b>";
            el_div.classList.add("tw_360");
            td.appendChild(el_div);
        td.classList.add("tsa_bc_transparent");

    }; // MMR_CreateSelectRow

//###########################################################################
//========= MOD MAIL MESSAGE Open===================== PR2021-10-14 PR2021-10-24
    function MMM_Open (el_input) {
        console.log("===  MMM_Open  =====") ;
        console.log("el_input", el_input) ;

// NOT IN USE
        // get userpk_timestamp, used as identifier to save attachments before the message is saved
        // from https://stackoverflow.com/questions/221294/how-do-you-get-a-timestamp-in-javascript
        // + new Date() is the same as Number(Date.now())
        //  lifespan of variable 'timestamp' is only as long as the modal is open.
        // time_stamp is in miliseconds, get 0.1 second accuracy (leave out last 2 digits)
        // dont need more than 100.000 seconds (1 day is 84.000 seconds, leave out the rest
        //   const time_stamp = + new Date();
        //   const time_stamp_str = time_stamp.toString()
        //   const time_stamp_sliced = time_stamp_str.slice(-8, -2);
        //   const temp_id = permit_dict.requsr_pk + "_" + time_stamp_sliced

// reset mod_MMM_dict
        b_clear_dict(mod_MMM_dict);
        mod_MMM_dict.is_mod_MML = false;

// reset input fields
        // reset tblBodies happens in MMM_FillSelectTables
        el_MMM_input_title.value = null;
        el_MMM_input_message.value = null;
        // reset attachments happens in MMM_FillAttachments

        console.log("permit_dict.permit_write_message", permit_dict.permit_write_message);
// --- show modal, only when user has permit
        let may_open_modal = permit_dict.permit_write_message;
        console.log("may_open_modal", may_open_modal);

        if(may_open_modal){

            const tblRow = t_get_tablerow_selected(el_input);
            const tblName = get_attr_from_el(tblRow, "data-table");
            const mailmessage_pk = get_attr_from_el_int(tblRow, "data-pk");

            console.log("tblRow", tblRow) ;
            console.log("mailmessage_pk", mailmessage_pk) ;

    // --- get existing data_dict
            // this modal is only to add new messages and edit saved messages that are not sent.

            const data_rows = mailmessage_draft_rows;

            console.log("tblName", tblName) ;
            console.log("data_rows", data_rows) ;

            // lookup_2_field (mailbox_pk) is null
            const [middle_index, data_dict, compare] = b_recursive_integer_lookup(data_rows, "id", mailmessage_pk);

    console.log("data_dict", data_dict);

            mod_MMM_dict.issaved = !isEmpty(data_dict);
            if (mod_MMM_dict.issaved) {
                mod_MMM_dict.mailmessage_pk = data_dict.id;
                mod_MMM_dict.mailbox_pk = data_dict.mailbox_id;
                mod_MMM_dict.mapid = data_dict.mapid;
                mod_MMM_dict.header = data_dict.header;
                mod_MMM_dict.body = data_dict.body;
                mod_MMM_dict.sender_user_id = data_dict.sender_user_id;
                mod_MMM_dict.sentdate = data_dict.sentdate;
            };

// fill lists with mailiglists, schoolbases, usergroups and users. Add selected from data_dict
            MMM_Fill_Datalists(data_dict);

// - fill table with all users
            MMM_FillSelectTables();

// - fill list with attachments
            MMM_FillAttachments();

// - message can be edited when has_prmit,  new or created by this user and not sent
            const may_edit = ( (permit_dict.permit_write_message) &&
                      ((!mod_MMM_dict.mailmessage_pk) || (!mod_MMM_dict.sentdate && mod_MMM_dict.sender_user_id === permit_dict.requsr_pk)));

            add_or_remove_class(el_MMM_btn_save, cls_hide, !may_edit)
            add_or_remove_class(el_MMM_btn_send, cls_hide, !may_edit)

// - set header text
            const header_str = (mod_MMM_dict.mailmessage_pk) ? (mod_MMM_dict.header)
                                ?  loc.Message + ":  " + mod_MMM_dict.header : loc.Message
                                : loc.Create_new_message;
            el_MMM_header.innerText = header_str;

// - add footer in message when new and empty
            if (may_edit && !mod_MMM_dict.body )  {
                const user_sb_pk = permit_dict.requsr_schoolbase_pk;
                const [index, found_dict, compare] = b_recursive_integer_lookup(mailbox_school_rows, "id", permit_dict.requsr_schoolbase_pk);

                mod_MMM_dict.body = "\n\n" + permit_dict.requsr_name;
                if (!isEmpty(found_dict)) {mod_MMM_dict.body = mod_MMM_dict.body + "\n" + found_dict.name};
            }

            el_MMM_input_title.value = (mod_MMM_dict.header) ? mod_MMM_dict.header : null;
            el_MMM_input_message.value =  (mod_MMM_dict.body) ? mod_MMM_dict.body : null;

// make input boxes readonly when message is sent or received
            el_MMM_input_title.readOnly = !may_edit;
            el_MMM_input_message.readOnly = !may_edit;

// - display Cancel or Close on cancel btn
            el_MMM_btn_cancel.innerText = (may_edit) ? loc.Cancel : loc.Close;

// - show delete btn only when may_edit and mailmessage exists
            const show_delete_btn = (may_edit && !!mod_MMM_dict.mailmessage_pk);
            add_or_remove_class(el_MMM_btn_delete, cls_hide, !show_delete_btn)

// - reset message error
            el_MMM_msg_error.innerText = null;

// - setfocus to el_MMMselect_input_filter
            set_focus_on_el_with_timeout(el_MMM_input_title, 50);

            $("#id_mod_mailmessage").modal({backdrop: true});
        }
    }  // MMM_Open

//========= MMM_SaveOrSend============== PR2021-10-10=1
    function MMM_SaveOrSend (is_send) {
        console.log("===  MMM_SaveOrSend  =====");
        console.log("mod_MMM_dict", mod_MMM_dict);
        console.log("permit_dict.permit_write_message", permit_dict.permit_write_message);
        console.log("mod_MMM_dict.mailmessage_pk", mod_MMM_dict.mailmessage_pk);
        console.log("mod_MMM_dict.sender_user_id", mod_MMM_dict.sender_user_id);
        console.log("mod_MMM_dict.sentdate", mod_MMM_dict.sentdate);

// - message can be edited when has_prmit,  new or created by this user and not sent
        const may_edit = ( (permit_dict.permit_write_message) &&
                  ((!mod_MMM_dict.mailmessage_pk) || (!mod_MMM_dict.sentdate && mod_MMM_dict.sender_user_id === permit_dict.requsr_pk)));
        console.log("may_edit", may_edit);
        if (may_edit){
            const msg_list = [];
            const header_str = el_MMM_input_title.value;
            if (!header_str) {msg_list.push(loc.Title_cannot_be_blank)}

            const body_str = el_MMM_input_message.value;
            if (is_send && !body_str) {msg_list.push(loc.Text_cannot_be_blank)}

            const upload_dict = { mode: (is_send) ? "send" : "save",
                                  issaved: mod_MMM_dict.issaved,
                                  mailmessage_pk: ( (mod_MMM_dict.mailmessage_pk) ? mod_MMM_dict.mailmessage_pk : null ),
                                  header: header_str,
                                  body: body_str
                                };

// --- get recipient list
            const keys = ["ml", "sb", "us", "ug"];
            let has_recipients = false;
            const recipients_dict = {}
            for (let i = 0, key_dict, key; key = keys[i]; i++) {
                recipients_dict[key] = [];
                key_dict = mod_MMM_dict[key];

// ---  loop through key_dict
                if(key_dict){
                    for (const data_dict of Object.values(key_dict) ) {
                        if (data_dict && data_dict.selected ) {
                            if (data_dict.id < 0) {
                                // depbase_pk has negative value, store in key 'db when value < 0
                                if (!("db" in recipients_dict)){
                                    recipients_dict.db = []
                                };
                                const db_pk = data_dict.id * -1;
                                recipients_dict.db.push(db_pk);
                            } else {
                                recipients_dict[key].push(data_dict.id);
                            };
                        };
                    };
                };
                if(recipients_dict[key].length){
                    if(key === "ug"){
                        recipients_dict[key].sort();
                    } else {
                        recipients_dict[key].sort(b_comparator_sortby_integer);
                        has_recipients = true;
                    };
                };
            };
            if (is_send && !has_recipients){
                msg_list.push(loc.Mesage_musthave_atleast_one_recipient);
            };

            upload_dict.recipients = recipients_dict;

        console.log("upload_dict", upload_dict);
        console.log("msg_list", msg_list);
    // ---  upload changes
            if (!msg_list.length){
                el_MMM_msg_error.innerText = null;

// ---  Upload changes
                const url_str = urls.url_mailmessage_upload;
                UploadChanges(upload_dict, url_str);

// hide modal
                $("#id_mod_mailmessage").modal("hide");
            } else {
                el_MMM_msg_error.innerText = msg_list.join("\n")
            }
       }
    }  // MMM_SaveOrSend

//========= MMM_Delete============== PR2021-10-10=1
    function MMM_Delete (is_send) {
        console.log("===  MMM_Delete  =====");
        console.log("mod_MMM_dict", mod_MMM_dict);
        console.log("permit_dict.permit_write_message", permit_dict.permit_write_message);
        console.log("mod_MMM_dict.mailmessage_pk", mod_MMM_dict.mailmessage_pk);
        console.log("mod_MMM_dict.sender_user_id", mod_MMM_dict.sender_user_id);
        console.log("mod_MMM_dict.sentdate", mod_MMM_dict.sentdate);

// - message can be edited when has_prmit,  new or created by this user and not sent
        const may_edit = ( permit_dict.permit_write_message && !mod_MMM_dict.sentdate && mod_MMM_dict.sender_user_id === permit_dict.requsr_pk);
        console.log("may_edit", may_edit);
        if (may_edit){

        console.log("mod_MMM_dict", mod_MMM_dict);
        console.log("mod_MMM_dict.mapid", mod_MMM_dict.mapid);
    // ---  when delete: make tblRow red, before uploading
            const tblRow_tobe_deleted = document.getElementById(mod_MMM_dict.mapid);
        console.log("tblRow_tobe_deleted", tblRow_tobe_deleted);
            if (tblRow_tobe_deleted){
                ShowClassWithTimeout(tblRow_tobe_deleted, "tsa_tr_error");
            };

            const upload_dict = {
                mode: "delete",
                mailmessage_pk: mod_MMM_dict.mailmessage_pk
            };
// ---  Upload changes
            const url_str = urls.url_mailmessage_upload;
            UploadChanges(upload_dict, url_str);
        };
    };  // MMM_Delete

//========= MMM_Fill_Datalists  ============= PR2021-10-25
    function MMM_Fill_Datalists(data_dict) {
        //console.log("===== MMM_Fill_Datalists ===== ");
        //console.log("data_dict", data_dict);

        const keys = ["ml", "sb", "us", "ug"];

// - get msg_list - this is the the corresponding list of recipients in message
        const recipients = (data_dict && data_dict.recipients) ? JSON.parse(data_dict.recipients) : {};
        //console.log("recipients", recipients, typeof recipients);

// - get 'all countries' from recipients, only used in mailing list
        mod_MMM_dict.allcountries = get_dict_value(recipients, ["ac"], false);
        // mailinglist is public when user_id is null
        mod_MMM_dict.ispublic = !get_dict_value(recipients, ["user_id"], false);
// - loop through lists with all mailinglists, organization, users and usergroups
        // key 'db' depbase is handled in key 'sb'
        for (let i = 0, key; key = keys[i]; i++) {
            const data_rows = (key === "ml") ? mailinglist_rows :
                              (key === "sb") ? mailbox_school_rows :
                              (key === "us") ? mailbox_user_rows :
                              (key === "ug") ? mailbox_usergroup_rows : null;
            if(data_rows && data_rows.length){
                const key_dict = {};
                for (let j = 0, row; row = data_rows[j]; j++) {
        // check if item is in recipients. In that case: set selected=true

        //console.log("................key", key);
        //console.log("recipients", recipients);
        //console.log("recipients[key]", recipients[key]);
        //console.log("row.id", row.id);
                    const selected = (recipients[key] && recipients[key].includes(row.id));
                    const dict = { id: row.id,  // note: id = string in usergroups ("auth'), id = sb_id in key 'sb'
                            country: (row.country) ? row.country : null,
                            country_pk: (row.country_pk) ? row.country_pk : null,
                            role: (row.defaultrole) ? row.defaultrole : null,
                            code: (row.code) ? row.code : null,
                            name: (row.name) ? row.name : null,
                            selected: selected
                        }
                        if(row.abbrev) {dict.abbrev = row.abbrev};
                        if(row.username) {dict.username = row.username};
                        if(row.email) {dict.email = row.email};
                    key_dict[row.id] = dict;
                };
                mod_MMM_dict[key] = key_dict;
            };
        };
        //console.log("mod_MMM_dict", mod_MMM_dict);
    };  // MMM_Fill_Datalists

//========= MMM_FillSelectTables  ============= PR2021-10-11
    function MMM_FillSelectTables() {
        //console.log("===== MMM_FillSelectTables ===== ");
        //console.log("mod_MMM_dict.is_mod_MML", mod_MMM_dict.is_mod_MML);

// ---  reset tblBody selectuser, recipient and cc
        const selected_pk = null;

        const keys = (mod_MMM_dict.is_mod_MML) ?  ["sb", "us", "ug"] : ["ml", "sb", "us", "ug"];
        for (let i = 0, key; key = keys[i]; i++) {
            const key_dict = mod_MMM_dict[key];
       //console.log("key", key);
       //console.log("key_dict", key_dict);
            if (key_dict){
                const tblBody_select =
                (mod_MMM_dict.is_mod_MML) ?
                              (key === "sb") ? el_MML_tblBody_organization :
                              (key === "us") ? el_MML_tblBody_users :
                              (key === "ug") ? el_MML_tblBody_usergroup : null
                :
                              (key === "ml") ? el_MMM_tblBody_mailinglist :
                              (key === "sb") ? el_MMM_tblBody_organization :
                              (key === "us") ? el_MMM_tblBody_users :
                              (key === "ug") ? el_MMM_tblBody_usergroup : null
                if ( tblBody_select ) { tblBody_select.innerText = null};

        // ---  loop through key_dict
                for (const data_dict of Object.values(key_dict) ) {
       //console.log("data_dict", data_dict);
                    if (data_dict.selected){
                        MMM_CreateSelectRow("MMM", tblBody_select, key, data_dict, selected_pk);
                    };
                };
            };
            if (key === "sb") {
                if (mod_MMM_dict.is_mod_MML) {
                    const show_usergroups = (el_MML_tblBody_organization.rows && el_MML_tblBody_organization.rows.length);
                    add_or_remove_class(el_MML_tblBody_usergroup_container, cls_hide, !show_usergroups);
                } else {
                    const show_usergroups = (el_MMM_tblBody_organization.rows && el_MMM_tblBody_organization.rows.length);
                    add_or_remove_class(el_MMM_tblBody_usergroup_container, cls_hide, !show_usergroups);
                }
            };
        };
    } // MMM_FillSelectTables

//========= MMM_CreateSelectRow  ============= PR2020-12-18 PR2020-07-14
    function MMM_CreateSelectRow(form_name, tblBody_select, key, data_dict, selected_pk) {
        //console.log("===== MMM_CreateSelectRow ===== ");
        //console.log("form_name", form_name);
        //console.log("key", key);
        //console.log("data_dict", data_dict);

//--- get info from data_dict
        const user_pk_int = data_dict.id;
        const code =  data_dict.code;// data_dict.school_code;
        const name = data_dict.name;// data_dict.school_abbrev;
        const user_name = data_dict.username;

        const is_selected_row = (user_pk_int === selected_pk);
        const just_selected = (data_dict.just_selected) ? data_dict.just_selected : false;
        //console.log("is_selected_row", is_selected_row);
        //console.log("data_dict", data_dict);


// ---  lookup index where this row must be inserted
        let row_index = -1;
        const ob1 = (key === "ml") ? (data_dict.name) ? data_dict.name.toLowerCase() : "" :
                    (key === "sb") ? (data_dict.code) ? data_dict.code.toLowerCase() : "" :
                    (key === "us") ? (data_dict.code) ? data_dict.code.toLowerCase() : "" :
                    (key === "ug") ? (data_dict.name) ? data_dict.name.toLowerCase() : "" : "";
        const ob2 = (key === "sb") ? (data_dict.name) ? data_dict.name.toLowerCase() : "" :
                    (key === "us") ? (data_dict.username) ? data_dict.username.toLowerCase() : "" : "";

        row_index = b_recursive_tblRow_lookup(tblBody_select, loc.user_lang, ob1, ob2);

        //console.log("ob1", ob1);
        //console.log("ob2", ob2);
//--------- insert tblBody_select row at row_index
        const map_id = "userpk_" + user_pk_int
        const tblRow = tblBody_select.insertRow(row_index);

        tblRow.id = map_id;
        tblRow.setAttribute("data-key_str", key);
        tblRow.setAttribute("data-pk", user_pk_int);
        //tblRow.setAttribute("data-code", code);
        //tblRow.setAttribute("data-name", name);
        //tblRow.setAttribute("data-user_name", user_name);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);
        tblRow.setAttribute("data-ob2", ob2);
        //tblRow.setAttribute("data-ob3", ob3);

        const class_selected = (is_selected_row) ? cls_selected: cls_bc_transparent;
        tblRow.classList.add(class_selected);

//- add hover to select row
        add_hover(tblRow)

// --- add first td to tblRow.
        //let inner_txt = (["ml", "ug"].includes(key)) ? data_dict.name : data_dict.code;
        let inner_txt = (key === "ml") ? data_dict.name :(["sb", "us"].includes(key)) ? data_dict.code : null;
        let td_width = (key === "ml") ? "tw_360" : "tw_060";
        let td = tblRow.insertCell(-1);
        let el_div = document.createElement("div");
            el_div.classList.add("pointer_show")
            el_div.innerText = inner_txt;
            el_div.classList.add(td_width)
            td.appendChild(el_div);
        td.classList.add("tsa_bc_transparent")

// --- add second td to tblRow.
        if (["sb", "us", "ug"].includes(key)) {    // --- add third td to tblRow.
            td = tblRow.insertCell(-1);
            inner_txt = (key === "sb") ? data_dict.name :
                        (key === "us") ? data_dict.abbrev :
                        (key === "ug") ? data_dict.name : null;
            let td_width = (key === "us") ? "tw_120" : "tw_360";
            el_div = document.createElement("div");
                el_div.classList.add("pointer_show")
                el_div.innerText = inner_txt;
                el_div.classList.add(td_width)
                td.appendChild(el_div);
            td.classList.add("tsa_bc_transparent")
        }
        if ( key === "us") {    // --- add third td to tblRow.
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                el_div.classList.add("pointer_show")
                el_div.innerText = user_name;
                el_div.classList.add("tw_220")
                td.appendChild(el_div);
            td.classList.add("tsa_bc_transparent")
        }

//--------- add addEventListener
        // in form "MMM" EventListener is attached to el_MMM_tblBody_organization_table
        if (form_name === "MMMselect"){
            tblRow.addEventListener("click", function() {MMMselect_TblRowClicked(tblRow, data_dict)}, false);
        }
        //tblRow.addEventListener("click", function() {MMMselect_Open(key)}, false);

// --- if added / removed row highlight row for 1 second
        if (just_selected) {
            data_dict.just_selected = false;
            ShowClassWithTimeout(tblRow, "bg_selected_blue", 1000) ;
        };

    } // MMM_CreateSelectRow

//=========  MMM_input_filter_Keyup  ================ PR2020-09-19  PR2021-10-11
    function MMM_input_filter_KeyupNIU(el_input) {
        //console.log( "===== MMM_input_filter_Keyup  ========= ");
        //console.log( "el_input", el_input);
// ---  get value of new_filter
        mod_MMM_dict.filter = (el_input.value) ? el_input.value.toLowerCase() : null;
        MMM_FillSelectTables()

    }; // MMM_input_filter_Keyup

//=========  MMM_input_Keyup  ================ PR2020-09-19  PR2021-10-12
    function MMM_input_Keyup() {
        //console.log( "===== MMM_input_Keyup  ========= ");
// - enable /disable save btn
        MMM_enable_btn_send();
    }; // MMM_input_Keyup

//========= MMM_enable_btn_send  ============= PR2021-10-12
    function MMM_enable_btn_send() {
        //console.log( "===== MMM_enable_btn_send  ========= ");
        //console.log( "el_MMM_input_title", el_MMM_input_title);
        //console.log( "el_MMM_input_message", el_MMM_input_message);

// - message can be edited when has_permit,  new or created by this user and not sent
        const may_edit = ( (permit_dict.permit_write_message) &&
                  ((!mod_MMM_dict.mailmessage_pk) || (!mod_MMM_dict.sentdate && mod_MMM_dict.sender_user_id === permit_dict.requsr_pk)));
        if(may_edit){
            let disable_btn_save = false;
            let disable_btn_send = false;
            if (!el_MMM_input_title.value) {
                disable_btn_save = true;
                disable_btn_send = true;

            //console.log( "el_MMM_input_title disable_btn_send", disable_btn_send);
            } else if (!el_MMM_input_message.value) {
                disable_btn_send = true;
            //console.log( " el_MMM_input_message disable_btn_send", disable_btn_send);
            } else {
        // - check if there are any recipients
                let has_recipients = false;
                for (let i = 0, data_dict; data_dict = mailbox_user_rows[i]; i++) {
                    if(data_dict.selected === "to"){
                        has_recipients = true;
                    };
                };
            //console.log( "has_recipients", has_recipients);
                disable_btn_send = !has_recipients;
            }
            //el_MMM_btn_save.disabled = disable_btn_save;
            //el_MMM_btn_send.disabled = disable_btn_send;
        };
    };  // MMM_enable_btn_send

//========= MMM_validate  ============= PR2021-10-16
    function MMM_validate(mode) {
        //console.log( "===== MMM_validate  ========= ");
        //console.log( "el_MMM_input_title", el_MMM_input_title);
        //console.log( "el_MMM_input_message", el_MMM_input_message);

        const msg_list = [];

// - message can be edited when has_permit,  new or created by this user and not sent
        const may_edit = ( (permit_dict.permit_write_message) &&
                  ((!mod_MMM_dict.mailmessage_pk) || (!mod_MMM_dict.sentdate && mod_MMM_dict.sender_user_id === permit_dict.requsr_pk)));
        if(may_edit){
            let disable_btn_save = false;
            let disable_btn_send = false;
            if (!el_MMM_input_title.value) {
                disable_btn_save = true;
                disable_btn_send = true;

            //console.log( "el_MMM_input_title disable_btn_send", disable_btn_send);
            } else if (!el_MMM_input_message.value) {
                disable_btn_send = true;
            //console.log( " el_MMM_input_message disable_btn_send", disable_btn_send);
            } else {
        // - check if there are any recipients
                let has_recipients = false;
                for (let i = 0, data_dict; data_dict = mailbox_user_rows[i]; i++) {
                    if(data_dict.selected === "to"){
                        has_recipients = true;
                    };
                };
            //console.log( "has_recipients", has_recipients);
                disable_btn_send = !has_recipients;
            }
            //el_MMM_btn_save.disabled = disable_btn_save;
            //el_MMM_btn_send.disabled = disable_btn_send;
        };
    };  // MMM_validate

//========= MMM_SaveAttachment  ============= PR2021-10-15
    function MMM_SaveAttachment(mode, el_input) {
        console.log( "===== MMM_SaveAttachment  === ");
        const filename = el_input.value;
        // mode = "create" or "delete"

        //console.log( "mode", mode);
        //console.log( "mod_MMM_dict", mod_MMM_dict);
        //console.log( "mod_MMM_dict.mailattachment_pk", mod_MMM_dict.mailattachment_pk);
        //console.log( "el_input", el_input);
        let filesize_exceeded = false;
        const max_file_size_Mb = 1;
// - message can be edited when has_prmit,  new or created by this user and not sent
        const may_edit = ( (permit_dict.permit_write_message) &&
                  ((!mod_MMM_dict.mailmessage_pk) || (!mod_MMM_dict.sentdate && mod_MMM_dict.sender_user_id === permit_dict.requsr_pk)));
        if (may_edit){
            // from https://medium.com/typecode/a-strategy-for-handling-multiple-file-uploads-using-javascript-eb00a77e15f
            const file = (el_input.files && el_input.files.length) ? el_input.files[0] : null;

            const upload_dict = { mode: mode,
                mailmessage_pk: ( (mod_MMM_dict.mailmessage_pk) ? mod_MMM_dict.mailmessage_pk : null )
                };

            if (mode === "create"){
// get attachment info

                if(file){
                    if(file.size > max_file_size_Mb * 1000000) {
                        filesize_exceeded = true;
                    } else {
                        upload_dict.file_name = file.name;
                        upload_dict.file_type = file.type;
                        upload_dict.file_size = file.size;
                    }
                };

            } else if (mode === "delete"){

                const mailattachment_pk = get_attr_from_el_int(el_input, "data-mailattachment_pk")
                upload_dict.mailattachment_pk = (mailattachment_pk) ? mailattachment_pk : null;
                // refresh table with attachment, to make deleterow red (cannot find simpelere way)
                const [index, found_dict, compare] = b_recursive_integer_lookup(mailattachment_rows, "id", mailattachment_pk);
                if (!isEmpty(found_dict)) {
                    found_dict.deleted = true;
                    MMM_FillAttachments();
                }
                // this one doent work
        //console.log("el_input.parentNode:", el_input.parentNode);
                //if (el_input.parentNode) {
                //    ShowClassWithTimeout(el_input.parentNode, "border_bg_invalid", "note_flex_1");
                //}
            };
            if(filesize_exceeded){
                 const msg_html = ["<div class='border_bg_invalid'><p>", loc.Attachment_too_large, "<br>",
                                   loc.Maximum_size_is, (max_file_size_Mb), " Mb.", "</p></div>"].join('');
                b_show_mod_message_html(msg_html, loc.Upload_attachment)

            } else {
                el_MMM_loader.classList.remove(cls_hide);

                const upload_json = JSON.stringify (upload_dict)
                const url_str = urls.url_mailattachment_upload;
                //console.log("url_str", url_str);
                //console.log("upload_dict", upload_dict);

                const uploadFile = new b_UploadFile(upload_json, file, url_str);
                uploadFile.doUpload(MMM_RefreshAttachment);
            }
       };
    };  // MMM_SaveAttachment


//========= MMM_DownloadAttachment  ============= PR2021-10-31
    function MMM_DownloadAttachment(el_href) {
        //console.log( "===== MMM_DownloadAttachment  === ");
        el_href.click();
    };  // MMM_DownloadAttachment

//=========  MMM_FillAttachments  ================ PR2021-10-15
    function MMM_FillAttachments(MMR_reader) {
        console.log(" --- MMM_FillAttachments  ---");
        console.log("mod_MMM_dict.mailmessage_pk:", mod_MMM_dict.mailmessage_pk);
        console.log("mod_MMM_dict.mailattachment_pk:", mod_MMM_dict.mailattachment_pk);
        console.log("mailattachment_rows:", mailattachment_rows);
        const el_attachment_container = (MMR_reader) ? el_MMR_attachment_container : el_MMM_attachment_container
        el_attachment_container.innerHTML = null;

        console.log("el_attachment_container:", el_attachment_container);

        for (let i = 0, row_dict; row_dict = mailattachment_rows[i]; i++) {
            if(row_dict.mailmessage_id === mod_MMM_dict.mailmessage_pk){

                let div = document.createElement("div");
                    div.classList.add("note_flex_1", "mr-0", "mb-2");
                    // when write mailmessage, attach eventhandler to <a>, beacuse of del btn in
                    if (MMR_reader) {
                        div.classList.add("pointer_show");
                        add_hover(div);
                    };
                    if (row_dict.created) {
                        ShowClassWithTimeout(div, "border_bg_valid");
                        delete row_dict.created;
                    };
                    if (row_dict.deleted) {
                        ShowClassWithTimeout(div, "border_bg_invalid");
                        delete row_dict.deleted;
                    };
                el_attachment_container.appendChild(div);

                const el_icon = document.createElement("div");
                    el_icon.classList.add("note_1_8", "ml-2", "mr-0");
                div.appendChild(el_icon);

                const el_href = document.createElement("a");
                    el_href.classList.add("c_form_text", "m-0", "p-2");
                    el_href.innerText = row_dict.filename;
                    el_href.setAttribute("href", row_dict.url)
                    el_href.target = "_blank";
                div.appendChild(el_href);

                if (MMR_reader) {div.addEventListener("click", function() {MMM_DownloadAttachment(el_href)}, false)};

                if(!MMR_reader && !row_dict.issent){
                    const el_del = document.createElement("div");
                    el_del.setAttribute("data-mailattachment_pk", row_dict.id);
                    el_del.classList.add("delete_0_1", "mr-2", "ml-0");
                    add_hover(el_del, "delete_0_2", "delete_0_1" )
                    el_del.addEventListener("click", function() {MMM_SaveAttachment("delete", el_del)}, false);
                    div.appendChild(el_del);
                };
            };
        }
        //const html_str = (html_list.length) ? html_list.join(' ') : null
        //el_MMM_attachment_container.innerHTML = html_list.join(' ');

    }  // MMM_FillAttachments

//=========  MMM_RefreshAttachment  ================ PR2021-10-12
    function MMM_RefreshAttachment(response) {
        console.log(" --- MMM_RefreshAttachment  ---");
        console.log("response:", response);

        el_MMM_loader.classList.add(cls_hide);
        if ("messages" in response) {
            b_show_mod_message_dictlist(response.messages);
        }
        if (response && "updated_mailattachment_row" in response) {
            const row = response.updated_mailattachment_row;
        console.log("row:", row);
        console.log("row.id:", row.id);

            if (row) {
                if(!row.deleted){
                    mod_MMM_dict.mailattachment_pk = row.id;
                    mod_MMM_dict.mailmessage_pk = row.mailmessage_id;
                    mod_MMM_dict.sender_user_id = row.sender_user_id;
                    mailattachment_rows.push(row);
        //console.log("mailattachment_rows:", mailattachment_rows);
        //console.log("mod_MMM_dict:", mod_MMM_dict);
                } else {
                    const [index, found_dict, compare] = b_recursive_integer_lookup(mailattachment_rows, "id", row.id);
                    if (!isEmpty(found_dict)) {
                        // delete row from data_rows. Splice returns array of deleted rows
                        const deleted_row_arr = mailattachment_rows.splice(index, 1)
        //console.log("deleted_row_arr:", deleted_row_arr);
                        };
                };
                MMM_FillAttachments();
            };
        };
    }; // MMM_RefreshAttachment

//###########################################################################

//=========  MMMselect_Open  ================ PR2021-10-24
    function MMMselect_Open(key) {
        console.log( "===== MMMselect_Open  ========= ");
        console.log( "key", key);

        const caption_sing = (key === "ml") ? loc.Mailing_list :
                                (key === "sb") ? loc.Organization :
                                (key === "us") ? loc.User :
                                (key === "ug") ? loc.Usergroup : "";
        const caption_sing_lc = (caption_sing) ? caption_sing.toLowerCase() : "";
        const caption_plural = (key === "ml") ? loc.Mailing_lists :
                                (key === "sb") ? loc.Organizations :
                                (key === "us") ? loc.Users :
                                (key === "ug") ? loc.Usergroups : "";
        const caption_plural_lc = (caption_plural) ? caption_plural.toLowerCase() : "";

// - message can be edited when has_prmit,  new or created by this user and not sent
        const may_edit = ( (permit_dict.permit_write_message) &&
                  ((!mod_MMM_dict.mailmessage_pk) || (!mod_MMM_dict.sentdate && mod_MMM_dict.sender_user_id === permit_dict.requsr_pk)));
        if (may_edit) {
    //- PR2021-10-29 debug. must reset mod_MMM_dict.filter
            mod_MMM_dict.filter = null;

// ---  check if key_dict has values
            const has_rows = !isEmpty(mod_MMM_dict[key]);
            if (!has_rows){
                 const msg_html = ["<div class='border_bg_warning'><p>",
                                    loc.There_are_no_, caption_plural_lc, "</p></div>"
                                  ].join('');
                b_show_mod_message_html(msg_html, loc.Select + " " + caption_sing_lc)

            } else {

// ---  loop through key_dict
                mod_MMM_dict.key = key;

                el_MMMselect_header.innerText = loc.Select + " " + caption_sing_lc;
                el_MMMselect_hdr_selected.innerText = loc.Selected + " " + caption_plural_lc;
                el_MMMselect_hdr_available.innerText = loc.Available + " " + caption_plural_lc;

                const show_checkbox_all_countries = (["sb", "us"].includes(key));
                if (show_checkbox_all_countries) {

// set caption of label all_countries
                    const is_curacao = (permit_dict.requsr_country.slice(0, 3).toLowerCase() === "cur");
                    const country_txt = (is_curacao) ? "St. Maarten" : "Curaçao";
                    const sb_us_txt = (key === "sb") ? loc.Organizations.toLowerCase() :
                                      (key === "us") ? loc.Users.toLowerCase() : "";
                    el_MMMselect_all_countries_label.innerText = [loc.Include, sb_us_txt, loc._of_, country_txt].join(" ");

    // - check if there are rows of other countries. If so: set all_countries checked true, set false otherwise
                    let has_rows_from_other_countries = false;
                    const key_dict = mod_MMM_dict[key];
                    for (const data_dict of Object.values(key_dict) ) {
                        if (data_dict.selected){
                            if(data_dict.country_pk !== permit_dict.requsr_country_pk){
                                has_rows_from_other_countries = true;
                            };
                        };
                    };

                    mod_MMM_dict.allcountries = has_rows_from_other_countries;
                    el_MMMselect_all_countries.checked = mod_MMM_dict.allcountries;

                };
                add_or_remove_class(el_MMMselect_all_countries.parentNode, cls_hide, !show_checkbox_all_countries)

                MMMselect_FillSelectTable()

// - setfocus to el_MMMselect_input_filter
                el_MMMselect_input_filter.value = null;
                set_focus_on_el_with_timeout(el_MMMselect_input_filter, 50);

                $("#id_mod_select_mailinglist").modal({backdrop: true});
            };
        };
    }  // MMMselect_Open

//========= MMMselect_Save  ============= PR2021-10-27
        // there is no function MMMselect_Save - selecting item saves it in mod_MMM_dict

//========= MMMselect_FillSelectTable  ============= PR2021-10-29
    function MMMselect_FillSelectTable() {
        console.log("===== MMMselect_FillSelectTable ===== ");
        console.log("mod_MMM_dict", mod_MMM_dict);
        const key_str = mod_MMM_dict.key;

// ---  reset tblBody_select
        el_MMMselect_tblBody_select.innerText = null;
        el_MMMselect_tblBody_available.innerText = null;

        const key_dict = mod_MMM_dict[key_str];

        const selected_pk = null;

// ---  loop through key_dict -
        // empty dicts are already filtered out in MMMselect_Open
        if (key_dict){
            for (const data_dict of Object.values(key_dict) ) {
                let show_row = false;
                // skip rows of other countries, not when allcountries=true or key = 'ml' or 'ug'
                if (["ml", "ug"].includes(key_str) || mod_MMM_dict.allcountries || data_dict.country_pk === permit_dict.requsr_country_pk ) {
                    if (mod_MMM_dict.filter){
                        show_row = data_dict.code && data_dict.code.toLowerCase().includes(mod_MMM_dict.filter);

                        if (!show_row) {show_row = data_dict.abbrev && data_dict.abbrev.toLowerCase().includes(mod_MMM_dict.filter)};
                        //if (!show_row) {show_row = data_dict.schoolname && data_dict.schoolname.toLowerCase().includes(mod_MMM_dict.filter)};
                        if (!show_row) {show_row = data_dict.username && data_dict.username.toLowerCase().includes(mod_MMM_dict.filter)};
                        if (!show_row) {show_row = data_dict.name && data_dict.name.toLowerCase().includes(mod_MMM_dict.filter)};
                    } else {
                        show_row = true;
                    };
                };

                if(show_row){
                    const tblBody = (data_dict.selected) ? el_MMMselect_tblBody_select : el_MMMselect_tblBody_available;
                    MMM_CreateSelectRow("MMMselect", tblBody, key_str, data_dict, selected_pk);
                };
            };
        };
    } // MMMselect_FillSelectTable

//=========  MMMselect_TblRowClicked  ================ PR2020-12-17
    function MMMselect_TblRowClicked(tblRow, data_dict) {
        console.log( "===== MMMselect_TblRowClicked ========= ");
        //console.log( "tblRow", tblRow);
        //console.log( "data_dict", data_dict);
        // all data attributes are now in tblRow, not in el_select = tblRow.cells[0].children[0];
        // after selecting row, values are stored in input box

// ---  set data_dict.selected
        // data_dict.selected = (data_dict.selected  is "to", "cc" or null
        data_dict.selected = (!data_dict.selected);
        data_dict.just_selected = true;

// - fill tables with users
        mod_MMM_dict.key = get_attr_from_el(tblRow, "data-key_str");

        console.log("mod_MMM_dict.key", mod_MMM_dict.key);
        MMMselect_FillSelectTable();
        MMM_FillSelectTables();

// - enable /disable save btn
        MMM_enable_btn_send();

        if(selected_btn === "btn_mailinglist") {
            MML_disable_save_btn()
        } else {
            MMM_enable_btn_send();
        };

    }  // MMMselect_TblRowClicked

//=========  MMMselect_input_Keyup  ================ PR2021-10-24
    function MMMselect_input_Keyup(el_input) {
        //console.log( "===== MMMselect_input_Keyup  ========= ");
        //console.log( "el_input", el_input);

// ---  get value of new_filter
        mod_MMM_dict.filter = (el_input.value) ? el_input.value.toLowerCase() : null;
        //console.log( "mod_MMM_dict.filter", mod_MMM_dict.filter);

        MMMselect_FillSelectTable();

    }; // MMMselect_input_Keyup

//=========  MMMselect_AllcountriesChanged  ================ PR2021-10-29
    function MMMselect_AllcountriesChanged(el_input) {
        console.log( "===== MMMselect_AllcountriesChanged  ========= ");
        //console.log( "el_input", el_input);

// ---  get value of new_filter
        mod_MMM_dict.allcountries = el_input.checked

        console.log( "mod_MMM_dict.allcountries", mod_MMM_dict.allcountries);
// if allcountries is set to fale: remove all items from other countries from list
        let selected_has_changed = false;
        if (!mod_MMM_dict.allcountries) {
            const key = mod_MMM_dict.key;
            const key_dict = mod_MMM_dict[key];
            for (const data_dict of Object.values(key_dict) ) {
                if (data_dict.selected){
                    if(data_dict.country_pk !== permit_dict.requsr_country_pk){
                        data_dict.selected = false;
                        selected_has_changed = true;
                    };
                };
            };
        }

        MMMselect_FillSelectTable();
        if (selected_has_changed) {MMM_FillSelectTables() };
    }; // MMMselect_AllcountriesChanged

//###########################################################################

//========= MOD MAILINGLIST Open===================== PR2021-11-02
    function MML_Open (el_input) {
        //console.log("===  MML_Open  =====") ;
        //console.log("el_input", el_input) ;

// reset mod_MMM_dict
        b_clear_dict(mod_MMM_dict);
        mod_MMM_dict.is_mod_MML = true;

// reset input fields
        // reset tblBodies happens in MMM_FillSelectTables
        el_MML_input_name.value = null;
        el_MML_ispublic.checked = false;
        el_MML_all_countries.checked = false;

// --- show input element, only when user has permit
        let may_open_modal = permit_dict.permit_write_message;
        if(may_open_modal){

            let tblRow = t_get_tablerow_selected(el_input)
            const mailinglist_pk = get_attr_from_el_int(tblRow, "data-pk");

// --- get data_dict
            const [middle_index, data_dict, compare] = b_recursive_integer_lookup(mailinglist_rows, "id", mailinglist_pk);
           // console.log("data_dict", data_dict);

            if (isEmpty(data_dict)) {
                mod_MMM_dict.mode = "create";
            } else {
                mod_MMM_dict.mode = "update";
                mod_MMM_dict.mailinglist_pk = data_dict.id;
                mod_MMM_dict.mapid = data_dict.mapid;
                mod_MMM_dict.name = data_dict.name;
                mod_MMM_dict.is_public = (!data_dict.user_id);

                mod_MMM_dict.sb_list = data_dict.sb_list;
                mod_MMM_dict.us_list = data_dict.us_list;
                mod_MMM_dict.ug_list = data_dict.ug_list;
            };
// - fill lists with mailiglists, schoolbases, usergroups and users. Add selected from data_dict
            MMM_Fill_Datalists(data_dict);

// - fill table with all users
            MMM_FillSelectTables();

// - creator of the mailinglist may edit, also sysadmin when it is a public mailinglist
            mod_MMM_dict.may_edit = (mod_MMM_dict.mode = "create") ||
                                    (mod_MMM_dict.user_id === permit_dict.requsr_pk) ||
                                    (mod_MMM_dict.ispublic && permit_dict.usergroup_list && permit_dict.usergroup_list.includes('admin'));

            add_or_remove_class(el_MML_btn_save, cls_hide, !mod_MMM_dict.may_edit)

            el_MML_header.innerText = (mod_MMM_dict.name) ? loc.Mailing_list + ": " + mod_MMM_dict.name : loc.Create_new_mailing_list;

// make input boxes readonly when message is sent or received
            el_MML_input_name.readOnly = !mod_MMM_dict.may_edit;
            el_MML_ispublic.readOnly = !mod_MMM_dict.may_edit;
            el_MML_input_name.value = (mod_MMM_dict.name) ? mod_MMM_dict.name : null;
            el_MML_ispublic.checked = mod_MMM_dict.is_public;

            const is_curacao = (permit_dict.requsr_country.slice(0, 3).toLowerCase() === "cur");
            el_MML_all_countries_label.innerText = loc.Include_users_of_ + ( (is_curacao) ? "St. Maarten" : "Curaçao" );
            el_MML_all_countries.checked = !!mod_MMM_dict.allcountries;

// - display Cancel or Close on cancel btn
            el_MML_btn_cancel.innerText = (mod_MMM_dict.may_edit) ? loc.Cancel : loc.Close;

// - show delete btn only when may_edit and mailmessage exists
            const show_delete_btn = (mod_MMM_dict.may_edit && !!mod_MMM_dict.mailinglist_pk);
            add_or_remove_class(el_MML_btn_delete, cls_hide, !show_delete_btn)

// - setfocus to el_MML_input_name, only when addnew mode
            if (!mod_MMM_dict.name){
                set_focus_on_el_with_timeout(el_MML_input_name, 50);
            };

            $("#id_mod_mailinglist").modal({backdrop: true});
        }
    }  // MML_Open

//========= MML_Save============== PR2021-10-22
    function MML_Save () {
        console.log("===  MML_Save  =====");
        const disable_save_btn = MML_disable_save_btn();
        if (!disable_save_btn){
            const mode = (mod_MMM_dict.mailinglist_pk) ? "update" : "create" ;

            const name_str = el_MML_input_name.value;
            const is_public = el_MML_ispublic.checked;
            const all_countries = el_MML_all_countries.checked;

    // ---  upload changes
            const upload_dict = { mode: mode,
                                   mailinglist_pk: ( (mod_MMM_dict.mailinglist_pk) ? mod_MMM_dict.mailinglist_pk : null ),
                                   name: name_str,
                                   ispublic: is_public,
                                   allcountries: all_countries,
                                   };

// --- get recipient list
            const keys = ["sb", "us", "ug"];
            const recipients_dict = {}
            for (let i = 0, key_dict, key; key = keys[i]; i++) {
                recipients_dict[key] = [];
                key_dict = mod_MMM_dict[key];

// ---  loop through key_dict
                if(key_dict){
                    for (const data_dict of Object.values(key_dict) ) {
                        if (data_dict && data_dict.selected ) {
                            if (data_dict.id < 0) {
                                // depbase_pk has negative value, store in key 'db when value < 0
                                if (!("db" in recipients_dict)){
                                    recipients_dict.db = []
                                };
                                const db_pk = data_dict.id * -1;
                                recipients_dict.db.push(db_pk);
                            } else {
                                recipients_dict[key].push(data_dict.id);
                            };
                        };
                    };
                };
                if(recipients_dict[key].length){
                    if(key === "ug"){
                        recipients_dict[key].sort();
                    } else {
                        recipients_dict[key].sort(b_comparator_sortby_integer);
                    };
                };
            };
            recipients_dict.ac = all_countries;

            upload_dict.recipients = recipients_dict;

    // ---  Upload changes
            const url_str = urls.url_mailinglist_upload;
            UploadChanges(upload_dict, url_str);

    // hide modal
            $("#id_mod_mailinglist").modal("hide");
        };
    }  // MML_Save

//========= MML_Fill_Datalist  ============= PR2021-10-22
    function MML_Fill_Datalist() {
        //console.log("===== MML_Fill_Datalist ===== ");
        // create a list with a combination of schools, users and default 'all schools' etc
        const data_rows = (mod_MMM_dict.sel_btn === "btn_schoollist") ? mailbox_school_rows :
                          (mod_MMM_dict.sel_btn === "btn_userlist") ? mailbox_usergroup_rows :
                          (mod_MMM_dict.sel_btn === "btn_usergrouplist") ? mailbox_usergroup_rows : null;

        const lists = ["sb", "us", "ug"];
        for (let i = 0, list; list = lists[i]; i++) {
            const list_name = list + "_list";
            const data_rows = (list === "sb") ? mailbox_school_rows :
                              (list === "us") ? mailbox_user_rows :
                              (list === "ug") ? mailbox_usergroup_rows : null;

            if(data_rows && data_rows.length){
                const data_list = [];
                for (let j = 0, row; row = data_rows[j]; j++) {
                    const key_str = list + "_" +  row.id;
                    const dict = { id: row.id,
                            list: list,
                            key: key_str,
                            country: (row.country) ? row.country : null,
                            role: (row.defaultrole) ? row.defaultrole : null,
                            code: (row.code) ? row.code : null,
                            name: (row.name) ? row.name : null,
                            username: (row.username) ? row.username : null,
                            select_table: null
                        }
                    // check if item is in sb_list etc. In that case: set selected=true
                        dict.selected = (mod_MMM_dict[list_name] && mod_MMM_dict[list_name].includes(row.id))
                    data_list.push(dict);
                };
                mod_MMM_dict[list] = data_list;
            };
        };
        //console.log("mod_MMM_dict", mod_MMM_dict);
    };  // MML_Fill_Datalist

//========= MML_Fill_SelectTable  ============= PR2021-10-22
    function MML_Fill_SelectTable() {
        //console.log("===== MML_Fill_SelectTable ===== ");

// ---  reset tblBody selectuser, recipient and cc
        el_MML_tblBody_select.innerText = null;
        el_MML_tblBody_sb_to.innerText = null;
        el_MML_tblBody_ug_to.innerText = null;
        el_MML_tblBody_us_to.innerText = null;
        const selected_pk = null;

    //console.log("mod_MMM_dict", mod_MMM_dict);

        const lists = ["sb", "us", "ug"];
        for (let i = 0, list; list = lists[i]; i++) {
    //console.log("list", list);

    // get data_rows of schools, users or usergroups
            const data_rows = mod_MMM_dict[list];
            const is_select_list = (list === "sb" && mod_MMM_dict.sel_btn === "btn_schoollist") ||
                                   (list === "us" && mod_MMM_dict.sel_btn === "btn_userlist") ||
                                   (list === "ug" && mod_MMM_dict.sel_btn === "btn_usergrouplist");
    //console.log("data_rows", data_rows);
    //console.log("is_select_list", is_select_list);

    // ---  loop through data_rows
            if (data_rows){
                for (let i = 0, data_dict, tblBody_select; data_dict = data_rows[i]; i++) {
    //console.log("data_dict", data_dict);
            // don't show rows of other lists in table 'select'
                    const show_row = (!!data_dict.selected || is_select_list);
    //console.log("show_row", show_row);
                    if (show_row){
                        if(data_dict.selected){
                            tblBody_select = (list === "sb") ? el_MML_tblBody_sb_to :
                                            (list === "us") ? el_MML_tblBody_us_to :
                                            (list === "ug") ? el_MML_tblBody_ug_to : null;
                        } else {
                            tblBody_select = el_MML_tblBody_select;
                        };
                        if ( tblBody_select) {
                            MML_userlist_Create_SelectRow(tblBody_select, data_dict, selected_pk);
                        };
                    };
                };
            };
        };

    } // MML_Fill_SelectTable

//========= MML_userlist_Create_SelectRow  =============  PR2021-10-22
    function MML_userlist_Create_SelectRow(tblBody_select, data_dict, selected_pk) {
        //console.log("===== MML_userlist_Create_SelectRow ===== ");

        //console.log("data_dict", data_dict);

//--- get info from data_dict
        const user_pk_int = data_dict.id;
        const code = data_dict.code;
        const name = data_dict.name;
        const user_name = data_dict.username;
        const list = data_dict.list;
        //console.log("list", list);
        //console.log("user_name", user_name);

        const is_selected_row = (user_pk_int === selected_pk);
        const just_selected = (data_dict.just_selected) ? data_dict.just_selected : false;

        let show_row = false;
        if (mod_MMM_dict.filter){
            if (code && code.toLowerCase().includes(mod_MMM_dict.filter)) { show_row = true };
            if (!show_row && user_name && user_name.toLowerCase().includes(mod_MMM_dict.filter)) { show_row = true };
        } else {
            show_row = true;
        }
        if(show_row){

    // ---  lookup index where this row must be inserted
            let ob1 = "", ob2 = "", row_index = -1;
            if (data_dict.code) { ob1 = data_dict.code.toLowerCase()};
            if (data_dict.last_name) { ob2 = data_dict.last_name.toLowerCase()};
            row_index = b_recursive_tblRow_lookup(tblBody_select, loc.user_lang, ob1, ob2);

    //--------- insert tblBody_select row at row_index
            const map_id = "userpk_" + user_pk_int
            const tblRow = tblBody_select.insertRow(row_index);

            tblRow.id = map_id;
            tblRow.setAttribute("data-pk", user_pk_int);
            tblRow.setAttribute("data-code", code);
            tblRow.setAttribute("data-name", name);
            tblRow.setAttribute("data-user_name", user_name);

    // ---  add data-sortby attribute to tblRow, for ordering new rows
            tblRow.setAttribute("data-ob1", ob1);
            tblRow.setAttribute("data-ob2", ob2);
            //tblRow.setAttribute("data-ob3", ob3);

            const class_selected = (is_selected_row) ? cls_selected: cls_bc_transparent;
            tblRow.classList.add(class_selected);

    //- add hover to select row
            add_hover(tblRow)

    // --- add first td to tblRow.
            let td = tblRow.insertCell(-1);
            let el_div = document.createElement("div");
                el_div.classList.add("pointer_show")
                el_div.innerText = code;
                el_div.classList.add("tw_060")
                td.appendChild(el_div);
            td.classList.add("tsa_bc_transparent")

    // --- add second td to tblRow.
            const td_width = (list === "us") ? "tw_120" : "tw_360";
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                el_div.classList.add("pointer_show")
                el_div.innerText = name;
                el_div.classList.add(td_width)
                td.appendChild(el_div);
            td.classList.add("tsa_bc_transparent")

    // --- add third td to tblRow.
            if(list === "us"){
                td = tblRow.insertCell(-1);
                    el_div = document.createElement("div");
                        el_div.classList.add("pointer_show")
                        el_div.innerText = user_name;
                        el_div.classList.add("tw_220", "px-1")
                        td.appendChild(el_div);
                    td.classList.add("tsa_bc_transparent");

            };
    //--------- add addEventListener
            tblRow.addEventListener("click", function() {MML_userlist_SelectItem(tblRow, data_dict)}, false);

    // --- if added / removed row highlight row for 1 second
            if (just_selected) {
                data_dict.just_selected = false;
                ShowClassWithTimeout(tblRow, "bg_selected_blue", 1000) ;
            };
        };
    } // MML_userlist_Create_SelectRow

//=========  MML_userlist_SelectItem  ================ PR2021-10-22
    function MML_userlist_SelectItem(tblRow, data_dict) {
        console.log( "===== MML_userlist_SelectItem ========= ");
        console.log( "tblRow", tblRow);
        console.log( "data_dict", data_dict);
        // all data attributes are now in tblRow, not in el_select = tblRow.cells[0].children[0];
        // after selecting row, values are stored in input box

// ---  set data_dict.selected
        // data_dict.selected = (data_dict.selected  is "to", "cc" or null
        data_dict.selected = (!data_dict.selected) ? mod_MMM_dict.select_table : null;
        data_dict.just_selected = true;

// - fill tables with users
        MML_Fill_SelectTable()

    }  // MML_userlist_SelectItem

//=========  MML_input_filter_Keyup  ================ PR2021-10-22
    function MML_input_filter_Keyup(el_input) {
        console.log( "===== MML_input_filter_Keyup  ========= ");
        console.log( "el_input", el_input);
// ---  get value of new_filter
        mod_MMM_dict.filter = (el_input.value) ? el_input.value.toLowerCase() : null;
        MML_Fill_SelectTable()

    }; // MML_input_filter_Keyup

//=========  MML_name_Keyup  ================ PR2021-11-02
    function MML_name_Keyup() {
        MML_disable_save_btn();
    }; // MML_name_Keyup

//=========  MML_disable_save_btn  ================ PR2021-11-02
    function MML_disable_save_btn(skip_msg) {
        console.log( "===== MML_disable_save_btn  ========= ");

        let disable_btn_save = false;
        const msg_list = [];
        if (!mod_MMM_dict.may_edit){
            disable_btn_save = true;
        } else {
            if (!el_MML_input_name.value) {
                msg_list.push(loc.Name_of_the_mailinglist + loc.cannot_be_blank);
            };

// --- check if there are any recipients
            const keys = ["sb", "us"];
            let has_recipients = false;
            const recipients_dict = {}
            for (let i = 0, key_dict, key; key = keys[i]; i++) {
                recipients_dict[key] = [];
                key_dict = mod_MMM_dict[key];

// ---  loop through key_dict
                if(key_dict){
                    for (const data_dict of Object.values(key_dict) ) {
                        if (data_dict && data_dict.selected ) {
                            if (data_dict.id) {
                                has_recipients = true;
                                break;
                            };
                        };
                    };
                };
                if ( has_recipients) { break};
            };
            if (!has_recipients){
                disable_btn_save = true;
                msg_list.push(loc.Mailinglist_musthave_atleast_one_recipient);
            };
        };
        const msg_txt = (msg_list.length && !skip_msg) ? msg_list.join("\n") : null
        el_MML_msg_error.innerText = msg_txt;

        return disable_btn_save;
    }; // MML_disable_save_btn


//=========  MML_ConfirmSave  ================ PR2019-10-24
    function MML_ConfirmSave() {
        //console.log(" --- MML_ConfirmSave --- ");
        //console.log("mod_dict: ", mod_dict);
        let tblRow = document.getElementById(mod_dict.mapid);

// ---  when delete: make tblRow red, before uploading
        if (tblRow && mod_dict.mode === "delete"){
            ShowClassWithTimeout(tblRow, "tsa_tr_error");
        }

        let close_modal = false, url_str = null;
        const upload_dict = {mode: mod_dict.mode, mapid: mod_dict.mapid};

        if(mod_dict.mode === "delete") {
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
    }  // MML_ConfirmSave

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


//=========   MMR_download   ====================== PR2022-03-01
    function MMR_download(log_list) {
        console.log(" ========== MMR_download ===========");
        console.log("mod_MMM_dict", mod_MMM_dict);

        if (mod_MMM_dict.header || mod_MMM_dict.body) {
            const filename = (mod_MMM_dict.header) ? mod_MMM_dict.header : loc.AWP_message;
            const log_list = [];
            const max_len = 90
            if (mod_MMM_dict.body){
                const body_list = mod_MMM_dict.body.split("\n");
                for (let i = 0, len = body_list.length; i < len; i++) {
                    const line = (body_list[i]) ? body_list[i] : " ";
                    const line_len = line.length
                    if (line_len < max_len) {
                        log_list.push(line);
                    } else {
                        const word_list = line.split(" ");
                        console.log("word_list", word_list);
                        let total_len = 0;
                        let total_line = "";
                        for (let j = 0, len = word_list.length; j < len; j++) {
                            const word = (word_list[j]) ? word_list[j] + " " : " ";
                        console.log("word", word);
                            if (total_line.length + word.length < max_len){
                                total_line += word;
                            } else {
                                log_list.push(total_line);
                                total_line = word;
                            };
                        };
                        if (total_line){
                            log_list.push(total_line);
                        };
                        console.log("total_line", total_line);
                    };
                };
            };
            printPDFlogfile(log_list, filename )
        };
    }; //MMR_download


//=========   OpenLogfile   ====================== PR2021-11-02
    function OpenLogfile(loc, log_list) {
        console.log(" ========== OpenLogfile ===========");

        if (!!log_list && log_list) {
            const today = new Date();
            const this_month_index = 1 + today.getMonth();
            const date_str = today.getFullYear() + "-" + this_month_index + "-" + today.getDate();
            let filename = "Log dd " + date_str + ".pdf";

            printPDFlogfile(log_list, filename )
        };
    }; //OpenLogfile
//###########################################################################

    function get_data_rows_from_selected_btn() {  // PR2021-09-12 PR2021-10-11
        return  (selected_btn === "btn_received") ? mailmessage_received_rows :
                (selected_btn === "btn_sent") ? mailmessage_sent_rows :
                (selected_btn === "btn_draft") ? mailmessage_draft_rows :
                (selected_btn === "btn_mailinglist") ? mailinglist_rows : null;
    };

})  // document.addEventListener('DOMContentLoaded', function()