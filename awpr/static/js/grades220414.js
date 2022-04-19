// PR2020-09-29 added

// PR2021-07-23  declare variables outside function to make them global variables

// selected_btn is also used in t_MCOL_Open
let selected_btn = "btn_ep_01";

let permit_dict = {};
let setting_dict = {};
let filter_dict = {};
let loc = {};
let urls = {};

const field_settings = {};

let selected = {
    grade_pk: null,
    grade_dict: {},
    item_count: 0
};

let school_rows = [];
let student_rows = [];
let studsubj_rows = [];
let grade_rows = [];

let subject_rows = [];
let cluster_rows = [];

let schemeitem_rows = [];

document.addEventListener("DOMContentLoaded", function() {
    "use strict";

// ---  get el_loader
    let el_loader = document.getElementById("id_loader");

// ---  check if user has permit to view this page. If not: el_loader does not exist PR2020-10-02
    const may_view_page = (!!el_loader)

    const cls_hide = "display_hide";
    const cls_hover = "tr_hover";
    const cls_visible_hide = "visibility_hide";
    const cls_selected = "tsa_tr_selected";

    let mod_dict = {};
    const mod_MAG_dict = {};
    let mod_status_dict = {};
    let mod_note_dict = {};

    let time_stamp = null; // used in mod add user
    let skip_warning_messages = false; // used to hide b_show_mod_message_dictlist when switching btn in handleBtnSelect PR2021-12-01

    let user_list = [];

    let examyear_map = new Map();
    let department_map = new Map();

    let level_map = new Map();
    let sector_map = new Map();

    let student_map = new Map();

    let published_map = new Map();
    let studentsubject_map = new Map();
    let studentsubjectnote_map = new Map();


    let el_focus = null; // stores id of element that must get the focus after cloosing mod message PR2020-12-20

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    urls.url_usersetting_upload = get_attr_from_el(el_data, "data-url_usersetting_upload");
    urls.url_subject_upload = get_attr_from_el(el_data, "data-url_subject_upload");
    urls.url_grade_upload = get_attr_from_el(el_data, "data-url_grade_upload");

    urls.url_grade_approve = get_attr_from_el(el_data, "data-url_grade_approve");
    urls.url_grade_approve_single = get_attr_from_el(el_data, "data-url_grade_approve_single");
    urls.url_grade_submit_ex2 = get_attr_from_el(el_data, "data-url_grade_submit_ex2");
    urls.url_studsubj_send_email_exform = get_attr_from_el(el_data, "data-url_studsubj_send_email_exform");
    urls.url_grade_block = get_attr_from_el(el_data, "data-url_grade_block");

    urls.url_download_grade_icons = get_attr_from_el(el_data, "data-download_grade_icons_url");
    urls.url_grade_download_ex2 = get_attr_from_el(el_data, "data-url_grade_download_ex2");
    urls.url_grade_download_ex2a = get_attr_from_el(el_data, "data-url_grade_download_ex2a");
    urls.url_download_published = get_attr_from_el(el_data, "data-download_published_url");
    urls.url_studentsubjectnote_upload = get_attr_from_el(el_data, "data-url_studentsubjectnote_upload");
    urls.url_studentsubjectnote_download = get_attr_from_el(el_data, "data-studentsubjectnote_download_url");
    urls.url_noteattachment_download = get_attr_from_el(el_data, "data-noteattachment_download_url");

    // url_importdata_upload is stored in id_MIMP_data of modimport.html

    columns_tobe_hidden.all = {
        fields: ["examnumber", "lvl_abbrev", "sct_abbrev", "cluster_name", "subj_name"],
        captions: ["Examnumber", "Leerweg", "Sector", "Cluster", "Subject"]};
    columns_tobe_hidden.btn_exem = {
        fields: ["exemption_year"],
        captions: ["Exemption_year"]};
// --- get field_settings
    const field_settings = {
        btn_exem: {field_names: ["select", "examnumber", "fullname",  "lvl_abbrev", "sct_abbrev", "cluster_name", "subj_code", "subj_name",
                                  "exemption_year",  "segrade", "cegrade", "finalgrade", "note_status"], //  "ce_status" not in use yet PR2022-03-03
                    field_caption: ["", "Ex_nr", "Candidate", "Leerweg_twolines", "Sector", "Cluster", "Abbreviation_subject", "Subject",
                                  "Exemption_year_twolines", "Exem_SE_twolines", "Exem_CE_twolines", "Exem_FINAL_twolines", ""],
                    field_tags: ["div", "div", "div", "div", "div", "div", "div", "div",
                                "div", "input", "input", "div", "div"],
                    filter_tags: ["text", "text","text", "text", "text", "text", "text", "text",
                                 "text", "text", "text", "text", "text"],
                    field_width: ["020", "060", "240", "060", "060", "120", "075", "240",
                                 "100", "090", "090", "090", "032"],
                    field_align: ["c", "r", "l", "c", "c", "l", "c", "l",
                                 "c", "c", "c", "c", "c"]},

        btn_ep_01: { field_names: ["select", "examnumber", "fullname", "lvl_abbrev", "sct_abbrev", "cluster_name", "subj_code", "subj_name",
                                   "segrade", "se_status", "srgrade", "sr_status",
                                   "pescore", "pe_status", "pegrade",
                                    "cescore", "ce_status", "cegrade", "finalgrade",
                                   "note_status"],
                    field_caption: ["", "Ex_nr", "Candidate", "Leerweg_twolines", "Sector", "Cluster", "Abbreviation_subject", "Subject",
                                   "School_exam_2lines", "", "Herkansing_SE_grade_2lines", "",
                                  "PE_score", "", "PE_grade",
                                  "CE_score", "", "CE_grade", "Final_grade_twolines",
                                  ""],

                    field_tags: ["div", "div", "div", "div", "div", "div", "div","div",
                                "input", "div",  "input", "div",
                                "input", "div", "input",
                                "input", "div", "div", "div",  // PR2022-03-03 entering cegrades not allowed:  set from input to div
                                "div"],
                    filter_tags: ["text", "text", "text", "text", "text", "text", "text", "text",
                                "text", "toggle", "text", "toggle",
                                "text", "toggle", "text",
                                "text", "toggle", "text",  "text",
                                "toggle"],
                    field_width: ["020", "060", "240", "060", "060", "120", "075","240",
                                "090", "020", "090", "020",
                                "090", "020", "090",
                                "090", "020", "090", "090",
                                 "032"],
                    field_align: ["c", "r", "l", "c", "c", "l", "c","l",
                                "c", "c", "c", "c",
                                "c", "c", "c",
                                "c", "c", "c", "c",
                                "c"]},

        btn_reex:  { field_caption: ["", "Ex_nr", "Candidate", "Leerweg_twolines", "Sector", "Cluster", "Abbreviation_subject", "Subject",
                                  "Re-examination_score", "", "Re-examination_grade", ""],
                    field_names: ["select", "examnumber", "fullname", "lvl_abbrev", "sct_abbrev", "cluster_name", "subj_code", "subj_name",
                                  "cescore", "ce_status", "cegrade", "note_status"],
                    field_tags: ["div", "div", "div", "div", "div", "div", "div","div",
                                "input", "div",  "input", "div"],
                    filter_tags: ["text", "text", "text", "text", "text", "text", "text","text",
                                "text", "text", "text", "text"],
                    field_width: ["020", "060", "240", "060", "060", "120", "075", "240", "090", "020", "090", "032"],
                    field_align: ["c", "r", "l", "c", "c", "l", "c", "l", "c", "c", "c"]},
        btn_reex03:  { field_caption: ["", "Ex_nr", "Candidate", "Leerweg_twolines", "Sector", "Cluster", "Abbreviation_subject", "Subject",
                                  "Third_period_score", "", "Third_period_grade", ""],
                    field_names: ["select", "examnumber", "fullname", "lvl_abbrev", "sct_abbrev",  "cluster_name","subj_code", "subj_name",
                                  "cescore", "ce_status", "cegrade", "note_status"],
                    field_tags: ["div", "div", "div", "div", "div", "div", "div", "div",
                                    "input", "div",  "input", "div"],
                    filter_tags: ["text", "text","text", "text", "text", "text", "text", "text",
                                    "text", "text", "text", "text"],
                    field_width: ["020", "060", "240", "060", "060", "120", "075","240", "090", "020", "090", "032"],
                    field_align: ["c", "r", "l", "c", "c", "l", "c", "l", "c", "c", "c"]},

        published: {field_caption: ["", "Name_ex_form", "Exam_period", "Exam_type", "Date_submitted", "Download_Exform"],
                    field_names: ["select", "name", "examperiod",  "examtype", "datepublished", "url"],
                    field_tags: ["div", "div", "div", "div", "div", "a"],
                    filter_tags: ["text", "text","text", "text",  "text", "text"],
                    field_width: ["020", "480", "150", "150", "150", "120"],
                    field_align: ["c", "r", "l", "c", "c", "c", "l"]}
        };

    const tblHead_datatable = document.getElementById("id_tblHead_datatable");
    const tblBody_datatable = document.getElementById("id_tblBody_datatable");

// === EVENT HANDLERS ===
// === reset filter when ckicked on Escape button ===
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") { ResetFilterRows()};
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
        };

// --- BUTTON CONTAINER ------------------------------------
        const el_btn_container = document.getElementById("id_btn_container");
        if (el_btn_container){
            const btns = el_btn_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                const data_btn = get_attr_from_el(btn,"data-btn");
                btn.addEventListener("click", function() {HandleBtnSelect(data_btn)}, false );
            };
        };

// ---  HEADER BAR ------------------------------------
        const el_hdrbar_examyear = document.getElementById("id_hdrbar_examyear");
        const el_hdrbar_school = document.getElementById("id_hdrbar_school");
        const el_hdrbar_department = document.getElementById("id_hdrbar_department");
        if (el_hdrbar_examyear){
            el_hdrbar_examyear.addEventListener("click", function() {
                t_MSED_Open(loc, "examyear", examyear_map, setting_dict, permit_dict, MSED_Response)}, false );
        };
        if (el_hdrbar_department){
            el_hdrbar_department.addEventListener("click", function() {
                t_MSED_Open(loc, "department", department_map, setting_dict, permit_dict, MSED_Response)}, false );
        };
        if (el_hdrbar_school){
            el_hdrbar_school.addEventListener("click",
                function() {t_MSSSS_Open(loc, "school", school_rows, false, setting_dict, permit_dict, MSSSS_Response)}, false );
        };

// ---  MSSS MOD SELECT SCHOOL / SUBJECT / STUDENT ------------------------------
        const el_MSSSS_input = document.getElementById("id_MSSSS_input");
        const el_MSSSS_tblBody = document.getElementById("id_MSSSS_tbody_select");
        const el_MSSSS_btn_save = document.getElementById("id_MSSSS_btn_save");
        if (el_MSSSS_input){
            el_MSSSS_input.addEventListener("keyup", function(event){
                setTimeout(function() {t_MSSSS_InputKeyup(el_MSSSS_input)}, 50)});
        };
        if (el_MSSSS_btn_save){
            // TODO when school selected in headerbar it should refer to MSSSS_Response, change to MSSSubjStud_Response
            //el_MSSSS_btn_save.addEventListener("click", function() {t_MSSSS_Save(el_MSSSS_input, MSSSS_Response)}, false );
            el_MSSSS_btn_save.addEventListener("click", function() {t_MSSSS_Save(el_MSSSS_input, MSSSubjStud_Response)}, false );
        };

// ---  SIDEBAR ------------------------------------
        // select_examtype, select_level, select_sector and select_showall refresh the page
        const el_SBR_select_examtype = document.getElementById("id_SBR_select_examtype");
        if (el_SBR_select_examtype){
            el_SBR_select_examtype.addEventListener("change", function() {HandleSbrExamtype(el_SBR_select_examtype)}, false)};
        const el_SBR_select_level = document.getElementById("id_SBR_select_level");
        if (el_SBR_select_level){
            el_SBR_select_level.addEventListener("change", function() {HandleSbrLevelSector("level", el_SBR_select_level)}, false)};
        const el_SBR_select_sector = document.getElementById("id_SBR_select_sector");
        if (el_SBR_select_sector){
            el_SBR_select_sector.addEventListener("change", function() {HandleSbrLevelSector("sector", el_SBR_select_sector)}, false)};

        const add_all = true;
        const el_SBR_select_subject = document.getElementById("id_SBR_select_subject");
        if (el_SBR_select_subject){
            el_SBR_select_subject.addEventListener("click",
                function() {t_MSSSS_Open(loc, "subject", subject_rows, add_all, setting_dict, permit_dict, MSSSubjStud_Response)}, false)};

        const el_SBR_select_cluster = document.getElementById("id_SBR_select_cluster");
        if (el_SBR_select_cluster){
            el_SBR_select_cluster.addEventListener("click",
                function() {t_MSSSS_Open(loc, "cluster", cluster_rows, add_all, setting_dict, permit_dict, MSSSubjStud_Response)}, false)};

        const el_SBR_select_student = document.getElementById("id_SBR_select_student");
        if (el_SBR_select_student){
            el_SBR_select_student.addEventListener("click",
                function() {t_MSSSS_Open(loc, "student", student_rows, add_all, setting_dict, permit_dict, MSSSubjStud_Response)}, false)};

        const el_SBR_select_showall = document.getElementById("id_SBR_select_showall");
        if (el_SBR_select_showall){
            el_SBR_select_showall.addEventListener("click", function() {HandleShowAll()}, false )};
        const el_SBR_item_count = document.getElementById("id_SBR_item_count")

// ---  MOD APPROVE GRADE ------------------------------------
        const el_mod_approve_grade = document.getElementById("id_mod_approve_grade");

        const el_MAG_header = document.getElementById("id_MAG_header");
        const el_MAG_select_container = document.getElementById("id_MAG_select_container");
            const el_MAG_subheader = document.getElementById("id_MAG_subheader");
            const el_MAG_examperiod = document.getElementById("id_MAG_examperiod");
            const el_MAG_examtype = document.getElementById("id_MAG_examtype");
        const el_MAG_subj_lvl_cls_container = document.getElementById("id_MAG_subj_lvl_cls_container");
            const el_MAG_subject = document.getElementById("id_MAG_subject");
            const el_MAG_lvlbase = document.getElementById("id_MAG_lvlbase");
            const el_MAG_cluster = document.getElementById("id_MAG_cluster");

        const el_MAG_approved_by_label = document.getElementById("id_MAG_approved_by_label");
        const el_MAG_approved_by = document.getElementById("id_MAG_approved_by");
        const el_MAG_auth_index = document.getElementById("id_MAG_auth_index");
        if (el_MAG_auth_index){
            el_MAG_auth_index.addEventListener("change", function() {MAG_UploadAuthIndex(el_MAG_auth_index)}, false );
        };

        const el_MAG_loader = document.getElementById("id_MAG_loader");
        const el_MAG_msg_container = document.getElementById("id_MAG_msg_container");
        const el_MAG_info_container = document.getElementById("id_MAG_info_container");

        const el_MAG_input_verifcode = document.getElementById("id_MAG_input_verifcode");
        if (el_MAG_input_verifcode){
            el_MAG_input_verifcode.addEventListener("keyup", function() {MAG_InputVerifcode(el_MAG_input_verifcode, event.key)}, false);
            el_MAG_input_verifcode.addEventListener("change", function() {MAG_InputVerifcode(el_MAG_input_verifcode)}, false);
        };

        const el_MAG_btn_delete = document.getElementById("id_MAG_btn_delete");
        if (el_MAG_btn_delete){
            el_MAG_btn_delete.addEventListener("click", function() {MAG_Save("delete")}, false );  // true = reset
        };
        const el_MAG_btn_save = document.getElementById("id_MAG_btn_save");
        if (el_MAG_btn_save){
            el_MAG_btn_save.addEventListener("click", function() {MAG_Save("save")}, false );
        };
        const el_MAG_btn_cancel = document.getElementById("id_MAG_btn_cancel");

// ---  MOD CONFIRM ------------------------------------
        const el_confirm_header = document.getElementById("id_modconfirm_header");
        const el_confirm_loader = document.getElementById("id_modconfirm_loader");
        const el_confirm_msg_container = document.getElementById("id_modconfirm_msg_container");
        const el_confirm_btn_cancel = document.getElementById("id_modconfirm_btn_cancel");
        const el_confirm_btn_save = document.getElementById("id_modconfirm_btn_save");
        if(el_confirm_btn_save){
            el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()});
        };

// ---  MOD STATUS ------------------------------------
        const el_mod_status_btn_save =  document.getElementById("id_mod_status_btn_save");
        const el_mod_status_header = document.getElementById("id_mod_status_header");
        const el_mod_status_note_container = document.getElementById("id_mod_status_note_container");
        if(el_mod_status_btn_save){
            el_mod_status_btn_save.addEventListener("click", function() {ModalStatusSave()}, false );
        };

// ---  MOD NOTE ------------------------------------
        const el_ModNote_header = document.getElementById("id_ModNote_header");
        const el_ModNote_input_container = document.getElementById("id_ModNote_input_container");
        const el_ModNote_input_note = document.getElementById("id_ModNote_input_note");
        const el_ModNote_notes_container = document.getElementById("id_ModNote_notes_container");
        const el_ModNote_btn_save = document.getElementById("id_ModNote_btn_save");
        const el_ModNote_internal = document.getElementById("id_ModNote_memo_internal");
        const el_ModNote_external = document.getElementById("id_ModNote_memo_external");
        if(el_ModNote_btn_save){
            el_ModNote_btn_save.addEventListener("click", function() {ModNote_Save()}, false )};
        if(el_ModNote_internal){
            el_ModNote_internal.addEventListener("click", function() {ModNote_SetInternalExternal("internal", el_ModNote_internal)}, false)};
        if(el_ModNote_external){
            el_ModNote_external.addEventListener("click", function() {ModNote_SetInternalExternal("external_btn", el_ModNote_external)}, false );
            for (let i = 0, el; el = el_ModNote_external.children[i]; i++) {
                el.addEventListener("click", function() {ModNote_SetInternalExternal("external_icon", el)}, false );
                add_hover(el)
            };
        };

// ---  MOD IMPORT ------------------------------------
// --- create EventListener for select dateformat element
// --- create EventListener for buttons in btn_container
    const el_MIMP_btn_container = document.getElementById("id_MIMP_btn_container");
    if(el_MIMP_btn_container){
        const btns = el_MIMP_btn_container.children;
        for (let i = 0, btn; btn = btns[i]; i++) {
            //PR2021-12-05 debug: data_btn as argument doesn't work, don't know why, use btn as argument instead
            // was: const data_btn = get_attr_from_el(btn, "data-btn")
            btn.addEventListener("click", function() {MIMP_btnSelectClicked(btn)}, false )
        };
    };
    const el_MIMP_filedialog = document.getElementById("id_MIMP_filedialog");
    if (el_MIMP_filedialog){el_MIMP_filedialog.addEventListener("change", function() {MIMP_HandleFiledialog(el_MIMP_filedialog)}, false)};
    const el_MIMP_btn_filedialog = document.getElementById("id_MIMP_btn_filedialog");
    if (el_MIMP_filedialog && el_MIMP_btn_filedialog){
        el_MIMP_btn_filedialog.addEventListener("click", function() {MIMP_OpenFiledialog(el_MIMP_filedialog)}, false)};
    const el_MIMP_filename = document.getElementById("id_MIMP_filename");

    //const el_MIMP_tabular = document.getElementById("id_MIMP_tabular");
    //if (el_MIMP_tabular){
    //    el_MIMP_tabular.addEventListener("change", function() {MIMP_CheckboxCrosstabTabularChanged(el_MIMP_tabular)}, false )
    //};
    //const el_MIMP_crosstab = document.getElementById("id_MIMP_crosstab");
    //if (el_MIMP_crosstab){
    //    el_MIMP_crosstab.addEventListener("change", function() {MIMP_CheckboxCrosstabTabularChanged(el_MIMP_crosstab)}, false )
    //};

    const el_worksheet_list = document.getElementById("id_MIMP_worksheetlist");
    if (el_worksheet_list){el_worksheet_list.addEventListener("change", function() {MIMP_SelectWorksheet(el_worksheet_list)}, false )};

    const el_MIMP_checkboxhasheader = document.getElementById("id_MIMP_hasheader");
    if (el_MIMP_checkboxhasheader){el_MIMP_checkboxhasheader.addEventListener("change", function() {MIMP_CheckboxHasheaderChanged(el_MIMP_checkboxhasheader)}, false )};

   const el_MIMP_examgradetype = document.getElementById("id_MIMP_examgradetype");
   if (el_MIMP_examgradetype){el_MIMP_examgradetype.addEventListener("change", function() {MIMP_ExamgradetypeChange(el_MIMP_examgradetype)}, false)};
   const el_MIMP_btn_prev = document.getElementById("id_MIMP_btn_prev");
   if (el_MIMP_btn_prev){el_MIMP_btn_prev.addEventListener("click", function() {MIMP_btnPrevNextClicked("prev")}, false)};
   const el_MIMP_btn_next = document.getElementById("id_MIMP_btn_next");
   if (el_MIMP_btn_next){el_MIMP_btn_next.addEventListener("click", function() {MIMP_btnPrevNextClicked("next")}, false)};
   const el_MIMP_btn_test = document.getElementById("id_MIMP_btn_test");
   if (el_MIMP_btn_test){el_MIMP_btn_test.addEventListener("click", function() {MIMP_Save("test", RefreshDataRowsAfterUploadFromExcel, setting_dict)}, false)};
   const el_MIMP_btn_upload = document.getElementById("id_MIMP_btn_upload");
   if (el_MIMP_btn_upload){el_MIMP_btn_upload.addEventListener("click", function() {MIMP_Save("save", RefreshDataRowsAfterUploadFromExcel, setting_dict)}, false)};

// ---  MOD MESSAGE ------------------------------------
    const el_mod_message_text = document.getElementById("id_mod_message_text");
    //$('#id_mod_message').on('hide.bs.modal', function (e) {
    //  ModMessageClose();
    //})

// ---  MODAL SELECT COLUMNS ------------------------------------
    const el_MCOL_btn_save = document.getElementById("id_MCOL_btn_save")
    if(el_MCOL_btn_save){
        el_MCOL_btn_save.addEventListener("click", function() {
            t_MCOL_Save(urls.url_usersetting_upload, HandleBtnSelect)}, false )
    };

    if(may_view_page){
// ---  set selected menu button active
        SetMenubuttonActive(document.getElementById("id_hdr_users"));

        const datalist_request = {
            setting: {page: "page_grade"},
            schoolsetting: {setting_key: "import_grade"},
            locale: {page: ["page_grade", "upload"]},
            examyear_rows: {get: true},
            school_rows: {get: true},

            department_rows: {get: true},
            level_rows: {cur_dep_only: true},
            sector_rows: {cur_dep_only: true},
            subject_rows: {cur_dep_only: true},
            cluster_rows: {cur_dep_only: true, allowed_only: true},

            student_rows: {cur_dep_only: true},
            studentsubject_rows: {cur_dep_only: true},
            grade_rows: {cur_dep_only: true}
        };

        DatalistDownload(datalist_request);
    };
//  #############################################################################################################

//========= DatalistDownload  ===================== PR2020-07-31
    function DatalistDownload(datalist_request, keep_loader_hidden) {
        console.log( "=== DatalistDownload ")
        console.log("request: ", datalist_request)

// ---  Get today's date and time - for elapsed time
        let startime = new Date().getTime();

// ---  show loader
        if(!keep_loader_hidden){el_loader.classList.remove(cls_visible_hide)}

        let param = {"download": JSON.stringify (datalist_request)};
        let response = "";
        $.ajax({
            type: "POST",
            url: urls.url_datalist_download,
            data: param,
            dataType: "json",
            success: function (response) {
                console.log("response - elapsed time:", (new Date().getTime() - startime) / 1000 );
                console.log(response);

        // hide loader
                el_loader.classList.add(cls_visible_hide);
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

                    // if sel_subject_pk has value, set sel_student_pk null
                    if (setting_dict.sel_subject_pk) {setting_dict.sel_student_pk = null;}

                    FillOptionsExamtype();
                    MSSSS_display_in_sbr_reset();

        // ---  fill cols_hidden
                    if("cols_hidden" in setting_dict){
                        //  setting_dict.cols_hidden was dict with key 'all' or se_btn, changed to array PR2021-12-14
                        //  skip when setting_dict.cols_hidden is not an array,
                        // will be changed into an array when saving with t_MCOL_Save
                        if (Array.isArray(setting_dict.cols_hidden)) {
                             b_copy_array_noduplicates(setting_dict.cols_hidden, mod_MCOL_dict.cols_hidden);
                        };
                    };
                };
                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    isloaded_permits = true;
                    // get_permits must come before CreateSubmenu and FiLLTbl
                    b_get_permits_from_permitlist(permit_dict);
                };
                if ("schoolsetting_dict" in response) {
                    i_UpdateSchoolsettingsImport(response.schoolsetting_dict)
                };

                // both 'loc' and 'setting_dict' are needed for CreateSubmenu
                if (isloaded_loc && isloaded_permits) {CreateSubmenu()};
                if(isloaded_settings || isloaded_permits){
                    b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);
                };
                if ("messages" in response) {
                    // skip showing warning messages when clicking selectbtn,
                    // msg 'Not current examyear' kept showing) PR2021-12-01
                    // skip_warning_messages will be reset in  b_show_mod_message_dictlist

                    b_show_mod_message_dictlist(response.messages, skip_warning_messages);
                };
                if ("examyear_rows" in response) {
                    b_fill_datamap(examyear_map, response.examyear_rows);
                };
                if ("school_rows" in response)  {
                    school_rows = response.school_rows;
                };
                if ("department_rows" in response) {
                    b_fill_datamap(department_map, response.department_rows);
                };
                if ("level_rows" in response) {
                    b_fill_datamap(level_map, response.level_rows);

                    t_SBR_FillSelectOptionsDepbaseLvlbaseSctbase("lvlbase", response.level_rows, setting_dict);
                };
                if ("sector_rows" in response) {
                    b_fill_datamap(sector_map, response.level_rows);
                    //FillOptionsSelectLevelSector("sector", response.sector_rows);
                    t_SBR_FillSelectOptionsDepbaseLvlbaseSctbase("sctbase", response.sector_rows, setting_dict);
                };
                if ("student_rows" in response) {
                    student_rows = response.student_rows;
                };
                if ("subject_rows" in response) {
                    subject_rows = response.subject_rows;
                };
                if ("cluster_rows" in response) {
                    cluster_rows = response.cluster_rows;
                };
                if ("studentsubject_rows" in response) {
                    studsubj_rows = response.studentsubject_rows;
                    //check_validation = true;
                };
                if ("grade_rows" in response) {
                    grade_rows = response.grade_rows;
        // get icons of notes and status PR2021-04-21
                    DownloadGradeStatusAndIcons();
                };

                SBR_display_subject_cluster_student();
                HandleBtnSelect(selected_btn, true)  // true = skip_upload
                // also calls: FillTblRows(), UpdateHeader()ect
            },
            error: function (xhr, msg) {
// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                console.log(msg + '\n' + xhr.responseText);
            }
        });
    }  // function DatalistDownload

//=========  CreateSubmenu  ===  PR2020-07-31 PR2021-01-19 PR2021-03-25
    function CreateSubmenu() {
        //console.log("===  CreateSubmenu == ");

        let el_submenu = document.getElementById("id_submenu")

        AddSubmenuButton(el_submenu, loc.Preliminary_Ex2, function() {ModConfirmOpen("prelim_ex2")});

        //AddSubmenuButton(el_submenu, loc.Preliminary_Ex2A, null, null, "id_submenu_download_ex2a", urls.url_grade_download_ex2a, true);  // true = download
        //AddSubmenuButton(el_submenu, loc.Ex3_form, function() {MEX3_Open()});
        if (permit_dict.permit_approve_grade){
            AddSubmenuButton(el_submenu, loc.Approve_grades, function() {MAG_Open("approve")});
        }
        if (permit_dict.permit_submit_grade){
            AddSubmenuButton(el_submenu, loc.Submit_Ex2_form, function() {MAG_Open("submit_ex2")});
            //AddSubmenuButton(el_submenu, loc.Submit_Ex2A_form, function() {MAG_Open("submit_ex2a")});
        };
        if(permit_dict.permit_crud){
            AddSubmenuButton(el_submenu, loc.Upload_grades, function() {MIMP_Open(loc, "import_grade")}, null, "id_submenu_import");
        };

        // true = save_in_all: when true: hidden columns are saved in 'all', otherwise they are saved separately for each selected_btn PR2021-12-02
        AddSubmenuButton(el_submenu, loc.Hide_columns, function() {t_MCOL_Open("page_grade")}, [], "id_submenu_columns")

        el_submenu.classList.remove(cls_hide);

    }; //function CreateSubmenu

//###########################################################################
//=========  HandleBtnSelect  ================ PR2020-09-19 PR2020-11-14 PR2021-03-15
    function HandleBtnSelect(data_btn, skip_upload) {
        //console.log( "===== HandleBtnSelect ========= ", data_btn);
        // function is called by HandleShowAll, MSSSS_Response, select_btn.click, t_MCOL_Save, DatalistDownload after response.setting_dict
        // skip_upload = true when called by DatalistDownload, MSSSS_Response, HandleShowAll
        //  PR2021-09-07 debug: gave error because old btn name was still in saved setting

        // check if data_btn exists, gave error because old btn name was still in saved setting PR2021-09-07 debug
        if (!data_btn) {data_btn = selected_btn};
        if (data_btn && ["btn_exem", "btn_ep_01", "btn_reex", "btn_reex03"].includes(data_btn)) {
            selected_btn = data_btn;
        } else {
            selected_btn = "btn_ep_01";
        };

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_grade: {sel_btn: selected_btn}};
        console.log( "upload_dict ", upload_dict);
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);
        };

// ---  highlight selected button
        b_highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  show only the elements that are used in this tab
        // PR2021-02-08this page does not contain tab_show yet.
        // modapprovegrade does. Make sure they have different names
        //b_show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

/*
        setting_dict.sel_subject_pk = null;
        setting_dict.sel_subject_code = null;
        setting_dict.sel_cluster_pk = null;
        setting_dict.sel_cluster_code = null;
        setting_dict.sel_student_pk = null;
        setting_dict.sel_student_name = null;

        if(setting_dict.sel_subject_pk ) {
            setting_dict.sel_cluster_pk = null;
            setting_dict.sel_cluster_name = null;
            setting_dict.sel_student_pk = null;
            setting_dict.sel_student_name = null;

        } else if(setting_dict.sel_cluster_pk ) {
            setting_dict.sel_subject_pk = null;
            setting_dict.sel_subject_code = null;
            setting_dict.sel_student_pk = null;
            setting_dict.sel_student_name = null;
        } else if(setting_dict.sel_student_pk ) {
            setting_dict.sel_subject_pk = null;
            setting_dict.sel_subject_code = null;
            setting_dict.sel_cluster_pk = null;
            setting_dict.sel_cluster_name = null;
        };
*/
        if(skip_upload){
        // skip_upload = true when called by DatalistDownload.
        //  - don't call DatalistDownload, otherwise it cretaed an indefinite loop
        //  - but fill table with new data

    // --- update header text
            UpdateHeader();

    // ---  fill datatable
            FillTblRows();
        } else {

            // skip showing warning messages when clicking selectbtn, (msg 'Not current examyear' kept showing) PR2021-12-01
            skip_warning_messages = true;
            const sel_examperiod = (selected_btn === "btn_exem") ? 4 :
                                    (selected_btn === "btn_reex03") ? 3 :
                                    (selected_btn === "btn_reex") ? 2: 1;

        // - change sel_examtype if necessary
            if (sel_examperiod === 1){
                if( !["se", "sr", "pe", "ce"].includes(setting_dict.sel_examtype) ) {setting_dict.sel_examtype = "se"};
            } else if (sel_examperiod === 2){
                if (setting_dict.sel_examtype !== "reex") {setting_dict.sel_examtype = "reex"};
            } else if (sel_examperiod === 3){
                if (setting_dict.sel_examtype !== "reex03") {setting_dict.sel_examtype = "reex03"};
            } else if (sel_examperiod === 4){
                if( !["se", "ce"].includes(setting_dict.sel_examtype) ) {setting_dict.sel_examtype = "se"};
            }
            setting_dict.sel_examperiod = (setting_dict.sel_examtype === "reex03") ? 3 :
                           (setting_dict.sel_examtype === "reex") ? 2 :
                           (setting_dict.sel_examtype === "reex") ? 2 :
                           (setting_dict.sel_examtype && ["se", "sr", "pe", "ce"].includes(setting_dict.sel_examtype) ) ? 1 : null;

            const datalist_request = {
                setting: {
                    page: "page_grade",
                    sel_btn: selected_btn,
                    sel_examperiod: sel_examperiod
                },
                grade_rows: {cur_dep_only: true}
            };
            DatalistDownload(datalist_request);
        };

    }  // HandleBtnSelect

//=========  HandleTblRowClicked  ================ PR2020-08-03
    function HandleTblRowClicked(tr_clicked) {
        //console.log("=== HandleTblRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        //DeselectHighlightedRows(tr_clicked, cls_selected);
        //tr_clicked.classList.add(cls_selected)

// ---  deselect all highlighted rows, select clicked row
       // t_td_selected_clear(tr_clicked.parentNode);
       // t_td_selected_set(tr_clicked);
        t_td_selected_toggle(tr_clicked, true);  // select_single = true

// ---  update setting_dict.sel_student_pk
        // only select employee from select table
        const row_id = tr_clicked.id
        if(row_id){
            const map_dict = get_mapdict_from_datamap_by_id(student_map, row_id)
            //setting_dict.sel_student_pk = map_dict.id;
        }
    }  // HandleTblRowClicked


//=========  HandleSbrPeriod  ================ PR2020-12-20
    function HandleSbrPeriod(el_select) {
        //console.log("=== HandleSbrPeriod");
        //console.log( "el_select.value: ", el_select.value, typeof el_select.value)
        const sel_examperiod = (Number(el_select.value)) ? Number(el_select.value) : null;
        const filter_value = sel_examperiod;

// --- fill selectbox examtype with examtypes of this period
        t_FillOptionsFromList(el_SBR_select_examtype, loc.options_examtype, "value", "caption",
            loc.Select_examtype, loc.No_examtypes_found, "filter", filter_value);

// ---  upload new setting and retrieve the tables that have been changed because of the change in examperiod
        const datalist_request = {
            setting: {
                page: "page_grade",
                sel_examperiod: sel_examperiod
                },
            grade_rows: {cur_dep_only: true}
        };
        DatalistDownload(datalist_request);
    };  // HandleSbrPeriod

//=========  HandleSbrExamtype  ================ PR2020-12-20
    function HandleSbrExamtype(el_select) {
        console.log("=== HandleSbrExamtype");
        console.log( "el_select.value: ", el_select.value, typeof el_select.value)
        // sel_examtype = "se", "pe", "ce", "reex", "reex03", "exem"
        setting_dict.sel_examtype = el_select.value;
        const filter_value = Number(el_select.value);
        //t_FillOptionsFromList(el_SBR_select_examtype, loc.options_examtype, "value", "caption",
        //    loc.Select_examtype, loc.No_examtypes_found, setting_dict.sel_examtype, "filter", filter_value);

        //console.log( "setting_dict.sel_examtype: ", setting_dict.sel_examtype, typeof setting_dict.sel_examtype)

// - not necessary, but to be on the safe side:
        setting_dict.sel_examperiod = (setting_dict.sel_examtype === "reex03") ? 3 :
                           (setting_dict.sel_examtype === "reex") ? 2 :
                           (setting_dict.sel_examtype === "reex") ? 2 :
                           (setting_dict.sel_examtype && ["se", "sr", "pe", "ce"].includes(setting_dict.sel_examtype) ) ? 1 :
                           setting_dict.sel_examperiod;

// ---  upload new setting
        const upload_dict = {selected_pk: {sel_examtype: setting_dict.sel_examtype,
                                         sel_examperiod: setting_dict.sel_examperiod}};
        console.log( "upload_dict: ", upload_dict);

        b_UploadSettings (upload_dict, urls.url_usersetting_upload);

        FillTblRows();
    }  // HandleSbrExamtype

//=========  HandleSbrLevelSector  ================ PR2021-03-06 PR2021-12-03
    function HandleSbrLevelSector(mode, el_select) {
        //console.log("=== HandleSbrLevelSector");
        //console.log( "el_select.value: ", el_select.value, typeof el_select.value)
        // mode = "level" or "sector"

// --- reset table rows, dont delete  header
        tblBody_datatable.innerText = null;

// - get new value from el_select
        const sel_pk_int = (Number(el_select.value)) ? Number(el_select.value) : null;
        const sel_abbrev = (el_select.options[el_select.selectedIndex]) ? el_select.options[el_select.selectedIndex].text : null;

// - put new value in setting_dict
        const sel_pk_key_str = (mode === "sector") ? "sel_sctbase_pk" : "sel_lvlbase_pk";
        const sel_abbrev_key_str = (mode === "sector") ? "sel_sector_abbrev" : "sel_level_abbrev";
        setting_dict[sel_pk_key_str] = sel_pk_int;
        setting_dict[sel_abbrev_key_str] = sel_abbrev;
        //console.log("setting_dict", setting_dict);

// ---  upload new setting - not necessary, new setting will be saved in DatalistDownload
        //b_UploadSettings (upload_dict, urls.url_usersetting_upload);
        //UpdateHeaderRight();
       // FillTblRows();

        const new_setting_dict = {page: "page_grade"}
        new_setting_dict[sel_pk_key_str] = sel_pk_int;

        const datalist_request = {
            setting: new_setting_dict,
            grade_rows: {cur_dep_only: true}
        };
        DatalistDownload(datalist_request);

    }  // HandleSbrLevelSector

//=========  FillOptionsExamtype  ================ PR2021-03-08 PR2021-12-02 PR2022-04-13
    function FillOptionsExamtype() {
        //console.log("=== FillOptionsExamtype");
        const has_practexam = !setting_dict.no_practexam;
        const sr_allowed = !!setting_dict.sr_allowed;
        const has_centralexam = !setting_dict.no_centralexam;
        const has_thirdperiod = !setting_dict.no_thirdperiod;
        // set examperiod = 1 when sel_examperiod -= 12 or null
        const examperiod = ([1, 2, 3, 4].includes(setting_dict.sel_examperiod)) ? setting_dict.sel_examperiod : 1;

// change sel_examperiod if it is not allowed in sel_btn
        let must_upload = false;
        if (setting_dict.sel_btn === "btn_ep_01" && setting_dict.sel_examperiod !== 1) {
            setting_dict.sel_examperiod = 1;
            must_upload = true;
        } else if (setting_dict.sel_btn === "btn_reex" && setting_dict.sel_examperiod !== 2) {
            setting_dict.sel_examperiod = 2;
            must_upload = true;
        } else if (setting_dict.sel_btn === "btn_reex03" && setting_dict.sel_examperiod !== 3) {
            setting_dict.sel_examperiod = 3;
            must_upload = true;
        } else if (setting_dict.sel_btn === "btn_exem" && setting_dict.sel_examperiod !== 4) {
            setting_dict.sel_examperiod = 4;
            must_upload = true;
        };

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(must_upload){
            const upload_dict = {selected_pk: {sel_examperiod: setting_dict.sel_examperiod}};
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);
        };

    //console.log("setting_dict.sel_btn", setting_dict.sel_btn);
    //console.log("setting_dict.sel_examperiod", setting_dict.sel_examperiod);
    //console.log("loc.options_examtype", loc.options_examtype);
    //console.log("examperiod", examperiod);

        if (el_SBR_select_examtype) {

            const display_rows = [];
            for (let i = 0, row; row = loc.options_examtype[i]; i++) {
                    if ( (row.value === "se" && examperiod === 1) ||
                        (row.value === "sr"  && examperiod === 1 && sr_allowed) ||
                        (row.value === "pe" && examperiod === 1 && has_practexam) ||
                        (row.value === "ce" && examperiod === 1 && has_centralexam) ||
                        (row.value === "reex" && examperiod === 2 && has_centralexam) ||
                        (row.value === "reex03" && examperiod === 3 && has_centralexam && has_thirdperiod) ||
                        (row.value === "exem" && examperiod === 4) ||
                        (row.value === "all" && examperiod === 1)
                    ){
                        display_rows.push(row);
                };
            };
        //console.log("display_rows", display_rows);
            t_FillOptionsFromList(el_SBR_select_examtype, display_rows, "value", "caption",
                loc.Select_examtype + "...", loc.No_examtypes_found, setting_dict.sel_examtype);
            document.getElementById("id_SBR_container_examtype").classList.remove(cls_hide);
        };

    }  // FillOptionsExamtype

//=========  FillOptionsSelectLevelSector  ================ PR2021-03-06
    function FillOptionsSelectLevelSector(tblName, rows) {
        //console.log("=== FillOptionsSelectLevelSector");
        //console.log("tblName", tblName);

        const display_rows = []
        const has_items = (!!rows && !!rows.length);
        const has_profiel = setting_dict.sel_dep_has_profiel;

        const caption_all = "&#60" + ( (tblName === "level") ? loc.All_levels : (has_profiel) ? loc.All_profielen : loc.All_sectors ) + "&#62";
        if (has_items){
            if (rows.length === 1){
                // if only 1 level: make that the selected one
                if (tblName === "level"){
                    setting_dict.sel_lvlbase_pk = rows.base_id;
                } else if (tblName === "sector"){
                    setting_dict.sel_sctbase_pk = rows.base_id
                }
            } else if (rows.length > 1){
                // add row 'Alle leerwegen' / Alle profielen / Alle sectoren in first row
                // HTML code "&#60" = "<" HTML code "&#62" = ">";
                display_rows.push({value: 0, caption: caption_all })
            }

            for (let i = 0, row; row = rows[i]; i++) {
                display_rows.push({value: row.base_id, caption: row.abbrev})
            }

            const selected_pk = (tblName === "level") ? setting_dict.sel_lvlbase_pk : (tblName === "sector") ? setting_dict.sel_sctbase_pk : null;
            const el_SBR_select = (tblName === "level") ? el_SBR_select_level : (tblName === "sector") ? el_SBR_select_sector : null;
            if (el_SBR_select){
                t_FillOptionsFromList(el_SBR_select, display_rows, "value", "caption", null, null, selected_pk);

            // put displayed text in setting_dict
                const sel_abbrev = (el_SBR_select.options[el_SBR_select.selectedIndex]) ? el_SBR_select.options[el_SBR_select.selectedIndex].text : null;
                if (tblName === "level"){
                    setting_dict.sel_level_abbrev = sel_abbrev;
                } else if (tblName === "sector"){
                    setting_dict.sel_sector_abbrev = sel_abbrev;
                };
            };
        };
        // hide select level when department has no levels
        if (tblName === "level"){
            add_or_remove_class(document.getElementById("id_SBR_container_level"), cls_hide, !has_items);
        // set label of profiel
         } else if (tblName === "sector"){
            add_or_remove_class(document.getElementById("id_SBR_container_sector"), cls_hide, false);
            const el_SBR_select_sector_label = document.getElementById("id_SBR_select_sector_label");
            if (el_SBR_select_sector_label) {
                el_SBR_select_sector_label.innerText = ( (has_profiel) ? loc.Profiel : loc.Sector ) + ":";
            };
        }
    }  // FillOptionsSelectLevelSector

//=========  HandleShowAll  ================ PR2020-12-17
    function HandleShowAll() {
        console.log("=== HandleShowAll");

        //t_SBR_show_all(FillTblRows);

        setting_dict.sel_lvlbase_pk = null;
        setting_dict.sel_level_abbrev = null;

        setting_dict.sel_sctbase_pk = null;
        setting_dict.sel_sector_abbrev = null;

        setting_dict.sel_subject_pk = null;
        setting_dict.sel_subject_code = null;
        setting_dict.sel_subject_name = null;

        setting_dict.sel_cluster_pk = null;
        setting_dict.sel_cluster_name = null;

        setting_dict.sel_student_pk = null;
        setting_dict.sel_student_name = null;

        el_SBR_select_level.value = "0";
        el_SBR_select_sector.value = "0";

        t_MSSSS_display_in_sbr("subject", null);
        t_MSSSS_display_in_sbr("cluster", null);
        t_MSSSS_display_in_sbr("student", null);

        ResetFilterRows();

/*
// ---  upload new setting
        const selected_pk_dict = {sel_lvlbase_pk: null, sel_sctbase_pk: null, sel_subject_pk: null, sel_student_pk: null};
        const page_grade_dict = {sel_btn: "grade_by_all"}
        const upload_dict = {selected_pk: selected_pk_dict, page_grade: page_grade_dict};
        b_UploadSettings (upload_dict, urls.url_usersetting_upload);

        HandleBtnSelect("grade_by_all", true) // true = skip_upload
        // also calls: FillTblRows(), UpdateHeader()
*/

// ---  upload new setting and refresh page
        const datalist_request = {
                setting: {
                    page: "page_grade",
                    sel_lvlbase_pk: null,
                    sel_sctbase_pk: null,
                    sel_subject_pk: null,
                    sel_cluster_pk: null,
                    sel_cluster_name: null,
                    sel_student_pk: null
                },

                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},
                subject_rows: {get: true},
                cluster_rows: {cur_dep_only: true},

                student_rows: {get: true},
                studentsubject_rows: {get: true},
                grade_rows: {cur_dep_only: true}
            };

            DatalistDownload(datalist_request);
    };  // HandleShowAll

//========= UpdateHeader  ================== PR2021-03-14
    function UpdateHeader(){
        console.log(" --- UpdateHeader ---" )
        //console.log("setting_dict", setting_dict)
        // sel_subject_txt gets value in MSSSS_display_in_sbr, therefore UpdateHeader comes after MSSSS_display_in_sbr

        //console.log(" --- UpdateHeaderRight ---" )
        let level_sector_txt = "";
        if (setting_dict.sel_lvlbase_pk) { level_sector_txt = setting_dict.sel_level_abbrev }
        if (setting_dict.sel_sctbase_pk) {
            if(level_sector_txt) { level_sector_txt += " - " };
            level_sector_txt += setting_dict.sel_sector_abbrev
        }
        const exam_txt = (setting_dict.sel_btn === "btn_exemption") ? loc.Exemptions :
                        (setting_dict.sel_btn === "btn_reex03") ? loc.Re_examination_3rd_period :
                        (setting_dict.sel_btn === "btn_reex") ? loc.Re_examination :
                        (setting_dict.sel_btn === "btn_se") ? loc.School_exam :
                        (setting_dict.sel_btn === "btn_ce") ? loc.Central_exam : "";

        const subject_student_txt = (setting_dict.sel_subject_pk) ? setting_dict.sel_subject_txt :
                                (setting_dict.sel_student_pk) ? setting_dict.sel_student_name : "";
        let header_txt = "";
        if(level_sector_txt) {
            header_txt += level_sector_txt;
        }
        if(exam_txt) {
            if (header_txt) { header_txt += " - "}
            header_txt += exam_txt;
        }
        if(subject_student_txt) {
            if (header_txt) { header_txt += " - "}
            header_txt += subject_student_txt;
        }
        document.getElementById("id_header_left").innerText = header_txt;

    }   //  UpdateHeader

//========= FillTblRows  ====================================
    function FillTblRows() {
        console.log( "===== FillTblRows  === ");
        //console.log( "field_settings", field_settings);
        //console.log( "selected_btn", selected_btn);

        const tblName = get_tblName_from_selectedBtn()
        const field_setting = field_settings[selected_btn];
        const data_rows = get_datarows_from_selectedBtn()

// ---  get list of hidden columns
        // copy col_hidden from mod_MCOL_dict.cols_hidden
        const col_hidden = [];
        b_copy_array_noduplicates(mod_MCOL_dict.cols_hidden, col_hidden)

// - hide columns that are not in use this examyear or this department PR2021-12-04
        // PR2021-12-04 use spread operator. from https://stackoverflow.com/questions/4842993/javascript-push-an-entire-list

        // hide srgrade when not sr_allowed
        if(!setting_dict.sr_allowed){col_hidden.push(...["srgrade", "sr_status"])};

        // hide pe or ce + pe when not allowed
        if(setting_dict.no_centralexam){
            col_hidden.push(...["pescore", "pe_status", "pegrade", "cescore", "ce_status", "cegrade"]);
        } else if(setting_dict.no_practexam){
            col_hidden.push(...["pescore", "pe_status", "pegrade"]);
        };

// - hide level when not level_req
        if(!setting_dict.sel_dep_level_req){col_hidden.push("lvl_abbrev")};

// - show only columns of sel_examtype
        //console.log( "setting_dict.sel_examtype", setting_dict.sel_examtype);
        if(setting_dict.sel_examtype === "se"){
            col_hidden.push(...["srgrade", "sr_status",
                               "pescore", "pe_status", "pegrade",
                                "cescore", "ce_status", "cegrade", "finalgrade"]);
        } else if(setting_dict.sel_examtype === "sr"){
            col_hidden.push(...["segrade", "se_status",
                               "pescore", "pe_status", "pegrade",
                                "cescore", "ce_status", "cegrade", "finalgrade"]);
        } else if(setting_dict.sel_examtype === "pe"){
            col_hidden.push(...["segrade", "se_status", "srgrade", "sr_status",
                                    "cescore", "ce_status", "cegrade", "finalgrade"]);
        } else if(  ["ce", "reex", "reex03"].includes(setting_dict.sel_examtype)){
            col_hidden.push(...["segrade", "se_status", "srgrade", "sr_status",
                                   "pescore", "pe_status", "pegrade",
                                    "finalgrade"]);
        };
        //console.log( "col_hidden", col_hidden);

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

// --- create table header
        CreateTblHeader(field_setting, col_hidden);

// --- create table rows
        if(data_rows && data_rows.length){

            for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
            // only show rows of selected level / sector / student / subject
            // show only rows that has_practexam when sel_examtype = "pe"
                // Note: filter of filterrow is done by t_Filter_TableRows
                //       sel_lvlbase_pk and sel_sctbase_pk are filtered on server
                const show_row = (tblName === "published") ? true :
                                //(!setting_dict.sel_lvlbase_pk || data_dict.lvlbase_id === setting_dict.sel_lvlbase_pk) &&
                                //(!setting_dict.sel_sctbase_pk || data_dict.sctbase_id === setting_dict.sel_sctbase_pk) &&
                                (!setting_dict.sel_student_pk || data_dict.student_id === setting_dict.sel_student_pk) &&
                                (!setting_dict.sel_subject_pk || data_dict.subject_id === setting_dict.sel_subject_pk) &&
                                (!setting_dict.sel_cluster_pk || data_dict.cluster_id === setting_dict.sel_cluster_pk) &&
                                (setting_dict.sel_examtype !== "pe" || data_dict.has_practexam);

                if(show_row){
                    CreateTblRow(tblName, field_setting, data_dict, col_hidden);
                };
          };
        };
        t_Filter_TableRows(tblBody_datatable, filter_dict, selected, loc.Subject, loc.Subjects);
    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-12-03 PR2020-12-18 PR2021-01-22 PR2021-12-01
    function CreateTblHeader(field_setting, col_hidden) {
        //console.log("===  CreateTblHeader ===== ");
        //console.log("field_setting", field_setting);
        //console.log("col_hidden", col_hidden);

        const column_count = field_setting.field_names.length;

// +++  insert header and filter row ++++++++++++++++++++++++++++++++
        let tblRow_header = tblHead_datatable.insertRow (-1);
        let tblRow_filter = tblHead_datatable.insertRow (-1);

    // --- loop through columns
        for (let j = 0; j < column_count; j++) {
            const field_name = field_setting.field_names[j];
            const is_status_field = (field_name !== "note_status" && field_name.includes("_status"));

    // --- skip column if in columns_hidden
            //example of mapped field
            //const mapped_field = (field_name === "subj_status") ? "subj_error" :
            //                     (field_name === "pok_validthru") ? "pok_status" : field_name;
            // const mapped_field = field_name;

    // skip columns if in columns_hidden
            if (!col_hidden.includes(field_name)){
                const key = field_setting.field_caption[j];
                let field_caption = (loc[key]) ? loc[key] : key;
                if (field_name === "sct_abbrev") {
                    field_caption = (setting_dict.sel_dep_has_profiel) ? loc.Profiel : loc.Sector;
                }

                const field_tag = field_setting.field_tags[j];
                const filter_tag = field_setting.filter_tags[j];
                const class_width = "tw_" + field_setting.field_width[j] ;
                const class_align = "ta_" + field_setting.field_align[j];

// ++++++++++ insert columns in header row +++++++++++++++
        // --- add th to tblRow_header +++
                let th_header = document.createElement("th");
        // --- add div to th, margin not working with th
                    const el_header = document.createElement("div");
        // --- add innerText to el_header
                    el_header.innerText = field_caption;
        // --- add width, text_align, right padding in examnumber
                    th_header.classList.add(class_width, class_align);
                    el_header.classList.add(class_width, class_align);
        // --- add right padding in examnumber
                    if(field_name === "examnumber"){
                        el_header.classList.add("pr-2")
                    } else if (["se_status", "sr_status", "pe_status", "ce_status"].indexOf(field_name) > -1) {
                        el_header.classList.add("diamond_0_0")
                    } else if(field_name === "note_status"){
                         // dont show note icon when user has no permit_read_note
                        const class_str = (permit_dict.permit_read_note) ? "note_0_1" : "note_0_0"
                        el_header.classList.add(class_str)
                    }
if(j && !is_status_field){th_header.classList.add("border_left")};
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
if(j && !is_status_field){th_filter.classList.add("border_left")};
        // --- add EventListener to el_filter
                    if (["text", "number"].includes(filter_tag)) {
                        el_filter.addEventListener("keyup", function(event){HandleFilterKeyup(el_filter, event)});
                        add_hover(th_filter);
                    } else if (filter_tag === "toggle") {
                        // add EventListener for icon to th_filter, not el_filter
                        th_filter.addEventListener("click", function(event){HandleFilterToggle(el_filter)});
                        th_filter.classList.add("pointer_show");
                    // default empty icon is necessary to set pointer_show
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
                        // >>> el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");
                    th_filter.appendChild(el_filter)
                tblRow_filter.appendChild(th_filter);

            }  //  if (columns_shown.inludes(field_name))
        }  // for (let j = 0; j < column_count; j++)

    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09 PR2021-12-02
    function CreateTblRow(tblName, field_setting, data_dict, col_hidden) {
        //console.log("=========  CreateTblRow =========");
        //console.log("data_dict", data_dict);

        const field_names = field_setting.field_names;
        const field_tags = field_setting.field_tags;
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;

// ---  lookup index where this row must be inserted
        const ob1 = (data_dict.lastname) ? data_dict.lastname : "";
        const ob2 = (data_dict.firstname) ? data_dict.firstname : "";
        const ob3 = (data_dict.subj_code) ? data_dict.subj_code : "";

        const row_index = b_recursive_tblRow_lookup(tblBody_datatable, setting_dict.user_lang, ob1, ob2, ob3);

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
            const is_status_field = (field_name !== "note_status" && field_name.includes("_status"));

    // --- skip columns if in columns_hidden
            //example of mapped field
            //const mapped_field = (field_name === "subj_status") ? "subj_error" :
            //                     (field_name === "pok_validthru") ? "pok_status" : field_name;
            // const mapped_field = field_name;

    // skip columns if in columns_hidden
            if (!col_hidden.includes(field_name)){
                const field_tag = field_tags[j];
                const class_width = "tw_" + field_width[j];
                const class_align = "ta_" + field_align[j];

        // --- insert td element,
                const td = tblRow.insertCell(-1);

        // --- create element with tag from field_tags
                const el = document.createElement(field_tag);

        // --- add data-field attribute
                    el.setAttribute("data-field", field_name);

        // --- add data-field Attribute when input element
                    if (field_tag === "input") {
                        el.setAttribute("type", "text")
                        el.setAttribute("autocomplete", "off");
                        el.setAttribute("ondragstart", "return false;");
                        el.setAttribute("ondrop", "return false;");
        // --- add EventListener
                        el.addEventListener("change", function(){HandleInputChange(el)});
                        el.addEventListener("keydown", function(event){HandleArrowEvent(el, event)});

    // --- add class 'input_text' and text_align
                    // class 'input_text' contains 'width: 100%', necessary to keep input field within td width
                        el.classList.add("input_text");

    // --- make el readonly when not requsr_requsr_same_school
                        el.readOnly = !permit_dict.requsr_same_school;
                    }

    // --- add width, text_align, right padding in examnumber
                    // >>> td.classList.add(class_width, class_align);
                    if(["fullname", "subj_name"].indexOf(field_name) > -1){
                        // dont set width in field student and subject, to adjust width to length of name
                        // >>> el.classList.add(class_align);
                        el.classList.add(class_width, class_align);
                    } else {
                        el.classList.add(class_width, class_align);
                    };
                    if(field_name === "examnumber"){
                        el.classList.add("pr-2");
                    }

if(j && !is_status_field){td.classList.add("border_left")};

                    if (field_name.includes("status")){
    // --- add column with status icon
                        el.classList.add("stat_0_0")
                    } else if (field_name === "note_status"){
                        el.classList.add("note_0_0")

                    } else if (field_name === "filename"){
                        /*
                        const name = (map_dict.name) ? map_dict.name : null;
                        const file_path = (map_dict.filepath) ? map_dict.filepath : null;
                        //console.log("file_path", file_path)
                        if (file_path){
                            // urls.url_download_published = "/grades/download//0/"
                            const len = urls.url_download_published.length;
                            const href = urls.url_download_published.slice(0, len - 2) + map_dict.id +"/"
                            //el.setAttribute("href", href);
                            //el.setAttribute("download", name);
                            el.title = loc.Download_Exform;
                            el.classList.add("btn", "btn-add")
                            el.addEventListener("click", function() {DownloadPublished(el)}, false)
                            add_hover(td);
                        }
                        */
                    } else if (field_name === "url"){
                         el.innerHTML = "download &#8681;";
                         el.target = "_blank";
                         //console.log("????????el", el)
                        //const el_attment = document.createElement("a");
                        //el_attment.innerText = att_name;
                        //el_attment.setAttribute("href", att_url)
                        //el_note_btn_attment.appendChild(el_attment);
                    }

                td.appendChild(el);

        // --- add EventListener to td
                if (["se_status", "sr_status", "pe_status", "ce_status"].includes(field_name)) {
                    td.addEventListener("click", function() {UploadToggle(el)}, false)
                    add_hover(td);
                } else if (field_name === "note_status"){
                    if(permit_dict.permit_read_note){
                        td.addEventListener("click", function() {ModNote_Open(el)}, false)
                        add_hover(td);
                    }
                }
                //td.classList.add("pointer_show", "px-2");
    // --- put value in field
                UpdateField(el, data_dict)
            }  //  if (columns_shown[field_name])
        }  // for (let j = 0; j < 8; j++)

        return tblRow
    };  // CreateTblRow

//=========  UpdateTblRow  ================ PR2020-08-01
    function UpdateTblRow(tblRow, tblName, data_dict) {
        console.log("=========  UpdateTblRow =========");
        console.log("data_dict", data_dict);
        if (tblRow && tblRow.cells){
            for (let i = 0, td; td = tblRow.cells[i]; i++) {
                UpdateField(td.children[0], data_dict);
            }
        }
    };  // UpdateTblRow

//=========  UpdateField  ================ PR2020-12-18 PR2021-05-30
    function UpdateField(el_div, data_dict) {
        //console.log("=========  UpdateField =========");
        if(el_div){
            const field_name = get_attr_from_el(el_div, "data-field");
            const fld_value = data_dict[field_name];
        //console.log("field_name", field_name);
        //console.log("fld_value", fld_value);

            if(field_name){
                let title_text = null, filter_value = null;
                if (["cescore", "pescore"].includes(field_name)){
                    el_div.value = (fld_value) ? fld_value : null;
                    filter_value = (fld_value) ? fld_value : null;
                } else if (el_div.nodeName === "INPUT"){
                    // replace dot with comma
                    el_div.value = (fld_value) ? fld_value.replaceAll(".", ",") : null;
                    filter_value = (fld_value) ? fld_value.toLowerCase() : null;

                } else if (field_name.includes("_status")){
                    const [status_className, status_title_text, filter_val] = UpdateFieldStatus(field_name, fld_value, data_dict);
                    filter_value = filter_val;
                    el_div.className = status_className;
                    title_text = status_title_text;

                 } else if (field_name === "filename"){
                    //el_div.innerHTML = "&#8681;";
                } else if (field_name === "url"){
                    el_div.href = fld_value;
                } else {
                    let inner_text = null;
                    if (field_name === "examperiod"){
                        inner_text = loc.examperiod_caption[data_dict.examperiod];
                    } else if (field_name === "examtype"){
                        inner_text = loc.examtype_caption[data_dict.examtype];
                    } else if (field_name === "datepublished"){
                        inner_text = format_dateISO_vanilla (loc, data_dict.datepublished, true, false, true, false);
                    } else {
                        inner_text = fld_value;
                    }
                    //el_div.innerText = (inner_text) ? inner_text : null;
                    el_div.innerText = (inner_text) ? inner_text : "\n"; // \n is necessary to show green field when blank
                    filter_value = (inner_text) ? inner_text.toString().toLowerCase() : null;
                }

    // ---  add attribute title
                add_or_remove_attr (el_div, "title", !!title_text, title_text);
    // ---  add attribute filter_value
                add_or_remove_attr (el_div, "data-filter", !!filter_value, filter_value);
            }
        }
    };  // UpdateField


//=========  UpdateFieldStatus  ================ PR2021-12-19
    function UpdateFieldStatus(field_name, fld_value, data_dict) {
        //console.log("=========  UpdateFieldStatus =========");
        //console.log("field_name", field_name);
        //console.log("fld_value", fld_value);
        //console.log("data_dict", data_dict);

        const field_arr = field_name.split("_");
        const prefix_str = field_arr[0];
        // field_name = "se_status", "sr_status", "pe_status", "ce_status", "note_status"
        let className = "diamond_3_4";  // diamond_3_4 is blank img
        let title_text = null, filter_value = null;
        if (prefix_str === "note"){
            // dont show note icon when user has no permit_read_note
            className = "note_" + ( (permit_dict.permit_read_note && fld_value && fld_value !== "0") ?
            (fld_value.length === 3) ? fld_value : "0_1" : "0_0" )

        } else {
            const field_auth1by_id = prefix_str + "_auth1by_id"
            const field_auth2by_id = prefix_str + "_auth2by_id"
            const field_auth3by_id = prefix_str + "_auth3by_id"
            const field_auth4by_id = prefix_str + "_auth4by_id"
            const field_published_id = prefix_str + "_published_id";
            const field_blocked = prefix_str + "_blocked"
            const field_status = prefix_str + "_status"

            const auth1by_id = (data_dict[field_auth1by_id]) ? data_dict[field_auth1by_id] : null;
            const auth2by_id = (data_dict[field_auth2by_id]) ? data_dict[field_auth2by_id] : null;
            const auth3by_id = (data_dict[field_auth3by_id]) ? data_dict[field_auth3by_id] : null;
            const auth4by_id = (data_dict[field_auth4by_id]) ? data_dict[field_auth4by_id] : null;
            const published_id = (data_dict[field_published_id]) ? data_dict[field_published_id] : null;
            const is_blocked = (data_dict[field_blocked]) ? data_dict[field_blocked] : null;
            const auth4_must_sign = ["pe_status", "ce_status"].includes(field_name);


    //console.log("field_blocked", field_blocked);
    //console.log("is_blocked", is_blocked);

            className = b_get_status_auth1234_iconclass(published_id, is_blocked, auth1by_id, auth2by_id, auth3by_id, auth4_must_sign, auth4by_id);

    //console.log("className", className);
            // default filter toggle '0'; is show all, '1' is show tickmark, '2' is show without tickmark
            //filter_value = (published_id) ? "5" :
            //                  (auth1by_id && auth2by_id) ? "4" :
            //                  (auth2by_id ) ? "3" :
            //                  (auth1by_id) ? "2" : "1"; // diamond_0_0 is outlined diamond

            if(published_id){
                filter_value = "2";
            } else if (auth4_must_sign) {
                filter_value = (auth1by_id && auth2by_id && auth3by_id && auth4by_id)  ? "2" : "1";
            } else {
                filter_value = (auth1by_id && auth2by_id && auth3by_id)  ? "2" : "1";
            };

    //console.log("auth1by_id", auth1by_id);
    //console.log("auth2by_id", auth2by_id);
    //console.log("auth3by_id", auth3by_id);
    //console.log("filter_value", filter_value);

            let formatted_publ_modat = "";
            if (published_id){
                const field_publ_modat = prefix_str + "_publ_modat" // subj_publ_modat
                const publ_modat = (data_dict[field_publ_modat]) ? data_dict[field_publ_modat] : null;
                const modified_dateJS = parse_dateJS_from_dateISO(publ_modat);
                formatted_publ_modat = format_datetime_from_datetimeJS(loc, modified_dateJS);
            };
            if (is_blocked) {
                if (published_id){
                    title_text = loc.blocked_11 + "\n" + loc.blocked_12 + formatted_publ_modat + "\n" + loc.blocked_13;
                } else {
                    title_text = loc.blocked_01 + "\n" + loc.blocked_02 + "\n" + loc.blocked_03;
                };
            } else if (published_id){

                title_text = loc.Submitted_at + ":\n" + formatted_publ_modat;

            } else if(auth1by_id || auth2by_id || auth3by_id || auth4by_id){
                title_text = loc.Approved_by + ": ";
                for (let i = 1; i < 5; i++) {
                    const auth_id = (i === 1) ? auth1by_id :
                                    (i === 2) ? auth2by_id :
                                    (i === 3) ? auth3by_id :
                                    (i === 4) ?  auth4by_id : null;
                    const prefix_auth = prefix_str + "_auth" + i;
                    if(auth_id){
                        const function_str = (i === 1) ?  loc.Chairperson :
                                            (i === 2) ? loc.Secretary :
                                            (i === 3) ?  loc.Examiner :
                                            (i === 4) ? loc.Corrector : "";
                        const field_usr = prefix_auth + "by_usr";
                        const auth_usr = (data_dict[field_usr]) ?  data_dict[field_usr] : "-";

                        title_text += "\n" + function_str.toLowerCase() + ": " + auth_usr;
                    };
                };
            };
        };
        return [className, title_text, filter_value]
    };  // UpdateFieldStatus

//========= set_columns_shown  ====== PR2021-03-08
    function set_columns_shown() {
        return false;
        //console.log( "===== set_columns_shown  === ");
        /*/
            const columns_shown = {select: true, examnumber: true, fullname: true,
                            lvl_abbrev: true,
                            sct_abbrev: true,
                            subj_code: true, subj_name: true,
                            pescore: true, cescore: true,
                            segrade: true, se_status: true,
                            pegrade: true, pe_status: true,
                            cegrade: true, ce_status: true,
                            pecegrade: true, finalgrade: true, note_status: true,
        */

                // sel_examtype = "se", "pe", "ce", "reex", "reex03", "exem"
        // first reset shown
        const show_all_grades = (selected_btn === "grade_by_all")
        columns_shown.pescore = show_all_grades; columns_shown.cescore = show_all_grades;
        columns_shown.segrade = show_all_grades; columns_shown.pegrade = show_all_grades;  columns_shown.cegrade = show_all_grades;
        columns_shown.pecegrade = show_all_grades; columns_shown.weighing = show_all_grades; columns_shown.finalgrade = show_all_grades;
        columns_shown.se_status = show_all_grades; columns_shown.pe_status = show_all_grades; columns_shown.ce_status = show_all_grades;
        columns_shown.note_status = true;
        const sel_examperiod = setting_dict.sel_examperiod;
        const sel_examtype = setting_dict.sel_examtype;

        //console.log( "show_all_grades", show_all_grades);
        //console.log( "sel_examperiod", sel_examperiod);
        //console.log( "sel_examtype", sel_examtype);

        if (sel_examtype === "se"){
            columns_shown.segrade = true; columns_shown.se_status = true;
        } else if (sel_examtype === "pe"){
            columns_shown.pescore = true; columns_shown.pe_status = true;
        } else if (sel_examtype === "ce"){
            columns_shown.cescore = true; columns_shown.ce_status = true;
        } else if (sel_examtype === "reex"){
            columns_shown.cescore = true; columns_shown.cegrade = true; columns_shown.ce_status = true;
        } else if (sel_examtype === "reex03"){
            columns_shown.cescore = true; columns_shown.cegrade = true; columns_shown.ce_status = true;
        } else if (sel_examtype === "exem"){
            columns_shown.segrade = true; columns_shown.se_status = true;
            columns_shown.cegrade = true; columns_shown.ce_status = true;
        }

        columns_shown.lvl_abbrev = (!!setting_dict.sel_lvlbase_pk);
        columns_shown.sct_abbrev = (!!setting_dict.sel_sctbase_pk);

        if(setting_dict.sel_subject_pk){
            // if sel_subject_pk has value: show subject in header, hide subject columns
            columns_shown.examnumber = true;
            columns_shown.fullname = true;
            columns_shown.subj_code = false;
            columns_shown.subj_name = false;
        } else if (setting_dict.sel_student_pk){
            // if sel_student_pk has value: show student in header, hide student columns
            columns_shown.examnumber = false;
            columns_shown.fullname = false;
            columns_shown.subj_code = true;
            columns_shown.subj_name = true;
        } else {
            // if no subject or student selected: show subject and studentcolumns
            columns_shown.examnumber = true;
            columns_shown.fullname = true;
            columns_shown.subj_code = true;
            columns_shown.subj_name = true;
        }
    }  // set_columns_shown

// +++++++++++++++++ UPLOAD CHANGES +++++++++++++++++ PR2020-12-15

//========= HandleArrowEvent  ================== PR2020-12-20
    function HandleArrowEvent(el, event){
        console.log(" --- HandleArrowEvent ---")
        console.log("event.key", event.key, "event.shiftKey", event.shiftKey)
        // This is not necessary: (event.key === "Tab" && event.shiftKey === true)
        // Tab and shift-tab move cursor already to next / prev element
        if (["Enter", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].indexOf(event.key) > -1) {
// --- get move_horizontal and move_vertical based on event.key and event.shiftKey
            // in page grades cursor goes down when clicked om Emter key
            let move_horizontal = (event.key === "ArrowRight") ? 1 :
                                    (event.key === "ArrowLeft") ? -1 : 0
            let move_vertical = (event.key === "ArrowDown" || (event.key === "Enter" && !event.shiftKey)) ? 1 :
                                    (event.key === "ArrowUp" || (event.key === "Enter" && event.shiftKey)) ? -1 : 0

        console.log("move_horizontal", move_horizontal, "move_vertical", move_vertical)
            const td = el.parentNode
            let tblRow = td.parentNode
            const tblBody = tblRow.parentNode
// --- get the first and last index of imput columns
            let max_colindex = null,  min_colindex = null;
            for (let i = 0, fldName, cell, td; td = tblRow.cells[i]; i++) {
                cell = td.children[0];
                fldName = get_attr_from_el(cell, "data-field")
                if ( ["pescore", "cescore", "segrade", "pegrade", "cegrade", "pecegrade", "finalgrade"].includes(fldName) ) {
                    if(min_colindex == null) {min_colindex = td.cellIndex}
                    max_colindex = td.cellIndex;
                }
            }
// --- set move up / down 1 row when min / max index is reached
            let new_col_index = td.cellIndex + move_horizontal;
            if(new_col_index > max_colindex) {
                new_col_index = min_colindex
                move_vertical += 1
            } else  if(new_col_index < min_colindex) {
                new_col_index = max_colindex
                move_vertical -= 1
            }
// --- set focus to next / previous cell
            // apparently you must deduct number of header rows from row_index
            let new_row_index = tblRow.rowIndex + move_vertical - 2;
            const new_tblRow = tblBody.rows[new_row_index]
            if(new_tblRow){
        console.log("new_tblRow", new_tblRow)
        console.log("new_col_index", new_col_index)
                const next_cell = new_tblRow.cells[new_col_index];
        console.log("next_cell", next_cell)
                if(next_cell){
                    const next_el = next_cell.children[0];
        console.log("next_el", next_el)
                    if(next_el){next_el.focus()}
                }
            }
        }
    }  // HandleArrowEvent

//========= HandleInputChange  ===============PR2020-08-16 PR2021-03-25 PR2021-09-20
    function HandleInputChange(el_input){
        console.log(" --- HandleInputChange ---")

        const tblRow = t_get_tablerow_selected(el_input)
        const map_id = tblRow.id
        if (map_id){
// ---  get selected.data_dict
            const grade_pk = get_attr_from_el_int(tblRow, "data-pk");
            const data_dict = b_get_datadict_by_integer_from_datarows(grade_rows, "id", grade_pk);

            const fldName = get_attr_from_el(el_input, "data-field")
            const old_value = data_dict[fldName];
    //console.log("fldName", fldName)
    //console.log("data_dict", data_dict)

            const has_permit = (permit_dict.permit_crud && permit_dict.requsr_same_school);
            if (!has_permit){
        // show message no permission
                b_show_mod_message_html(loc.grade_err_list.no_permission);
        // put back old value  in el_input
                el_input.value = old_value;

            } else {
                const blocked_field = fldName.slice(0, 2) + "_blocked";
                const published_field = fldName.slice(0, 2) + "_published_id";
                const is_blocked = (data_dict[blocked_field]) ? data_dict[blocked_field] : false;
                const is_published = (data_dict[published_field]) ? true : false;

    //console.log("old_value", old_value)
    //console.log("blocked_field", blocked_field)
    //console.log("published_field", published_field)
    //console.log("is_blocked", is_blocked)
    //console.log("is_published", is_published)

                if (is_blocked){
                    // Note: if grade is_published and not blocked: this means the inspection has given permission to change grade
                    const is_submitted = data_dict[published_field] ? true : false;
                    const msg_html = (is_submitted) ? loc.grade_err_list.grade_submitted + "<br>" + loc.grade_err_list.need_permission_inspection :
                                                      loc.grade_err_list.grade_approved + "<br>" + loc.grade_err_list.needs_approvals_removed+ "<br>" + loc.grade_err_list.Then_you_can_change_it;

            // show message
                    b_show_mod_message_html(msg_html);
            // put back old value  in el_input
                    el_input.value = old_value;
                } else {
                    const new_value = el_input.value;
                    if(new_value !== old_value){
                        // TODO FOR TESTING ONLY: turn validate off to test server validation
                        const validate_on = false;
                        let value_text = new_value, msg_html = null
                        if (validate_on){
                            const arr = ValidateGrade(loc, fldName, new_value, data_dict);
                            value_text = arr[0];
                            msg_html = arr[1];
                        }
                        if (msg_html){
            // ---  show modal MESSAGE
                            mod_dict = {el_focus: el_input}
                            b_show_mod_message_html(msg_html, null, ModMessageClose);
        // make field red when error and reset old value after 2 seconds
                            reset_element_with_errorclass(el_input, data_dict)

                        } else {

                            //>>>>>>>>>>>el_input.value = value_text;
                            let url_str = urls.url_grade_upload;

                            // must loose focus, otherwise green / red border won't show
                            //el_input.blur();

                            //const el_loader =  document.getElementById("id_MSTUD_loader");
                           // el_loader.classList.remove(cls_visible_hide);

                    // ---  upload changes
                            const upload_dict = { table: data_dict.table,
                                                   mode: "update",
                                                   mapid: map_id,

                                                   examperiod: data_dict.examperiod,
                                                   grade_pk: data_dict.id,
                                                   student_pk: data_dict.student_id,
                                                   studsubj_pk: data_dict.studsubj_id,
                                                   //examperiod_pk: data_dict.examperiod
                                                   examgradetype: fldName
                                                   };
                            upload_dict[fldName] = value_text;
                            UploadChanges(upload_dict, urls.url_grade_upload);
                        }
                    }
                }
            }  // if (!permit_dict.permit_crud)
        }
    };  // HandleInputChange

//========= DownloadPublished  ============= PR2020-07-31  PR2021-01-14
    function DownloadPublished(el_input) {
        //console.log( " ==== DownloadPublished ====");
        const tblRow = t_get_tablerow_selected(el_input);
        const pk_int = get_attr_from_el_int(tblRow, "data-pk");

        const map_dict = get_mapdict_from_datamap_by_id(published_map, tblRow.id);
        const filepath = map_dict.filepath
        const filename = map_dict.filename
        //console.log( "filepath", filepath);
        //console.log( "filename", filename);

       // window.open = '/ticket?orderId=' + pk_int;

        // UploadChanges(upload_dict, url_download_published);
        const upload_dict = { published_pk: pk_int};
        if(!isEmpty(upload_dict)) {
            const parameters = {"upload": JSON.stringify (upload_dict)}
            let response = "";
            $.ajax({
                type: "POST",
                url: urls.url_download_published,
                data: parameters,
                dataType:'json',
            success: function (response) {
            var a = document.createElement('a');
            var url = window.urls.createObjectURL(response);
            a.href = url;
            a.download = 'myfile.pdf';
            document.body.append(a);
            a.click();
            a.remove();
            window.urls.revokeObjectURL(url);
        },


    /*
                success: function (data) {
                    //const a = document.createElement('a');
                    //const url = window.urls.createObjectURL(data);
                    //console.log( "data");
                    //console.log( data);
                    /*
                    a.href = url;
                    a.download = 'myfile.pdf';
                    document.body.append(a);
                    a.click();
                    a.remove();
                    window.urls.revokeObjectURL(url);
                    */
                    /*
                    var blob = new Blob(data, { type: 'application/pdf' });
                    var a = document.createElement('a');
                    a.href = window.urls.createObjectURL(blob);
                    a.download = filename;
                    a.click();
                    window.urls.revokeObjectURL(url);

                },
*/

                error: function (xhr, msg) {
                    // ---  hide loader
                    el_loader.classList.add(cls_visible_hide)
                    console.log(msg + '\n' + xhr.responseText);
                }  // error: function (xhr, msg) {
            });  // $.ajax({
        }  //  if(!!row_upload)





        // PR2021-03-06 from https://stackoverflow.com/questions/1999607/download-and-open-pdf-file-using-ajax
        //$.ajax({
        //    url: urls.url_download_published,
        //    success: download.bind(true, "<FILENAME_TO_SAVE_WITH_EXTENSION>", "application/pdf")
        //    });

        //PR2021-03-07 from https://codepen.io/chrisdpratt/pen/RKxJNo
        //This one works, the demo does at least
        /*
        $.ajax({
            url: 'https://s3-us-west-2.amazonaws.com/s.cdpn.io/172905/test.pdf',
            method: 'GET',
            xhrFields: {
                responseType: 'blob'
            },
            success: function (data) {
                var a = document.createElement('a');
                var url = window.urls.createObjectURL(data);
                a.href = url;
                a.download = 'myfile.pdf';
                document.body.append(a);
                a.click();
                a.remove();
                window.urls.revokeObjectURL(url);
            }
        });
        */

     } // DownloadPublished
/////////////////////////////////////////////

//========= DownloadGradeStatusAndIcons ============= PR2021-04-30
    function DownloadGradeStatusAndIcons() {
        console.log( " ==== DownloadGradeStatusAndIcons ====");

        const url_str = urls.url_download_grade_icons;
        const datalist_request = {grade_note_icons: {get: true}, grade_stat_icon: {get: true}};
        let param = {"download": JSON.stringify (datalist_request)};
        let response = "";
        $.ajax({
            type: "POST",
            url: url_str,
            data: param,
            dataType: "json",
            success: function (response) {
                console.log("response", response)
                if ("grade_note_icon_rows" in response) {
                    const is_update = true, skip_show_ok = true;
                    RefreshDataRows("grades", response.grade_note_icon_rows, grade_rows, is_update, skip_show_ok);
                }
               if ("grade_stat_icon_rows" in response) {
                    const tblName = "grades", is_update = true;
                    RefreshDataRows(tblName, response.grade_stat_icon_rows, grade_rows, is_update);
                }
            },
            error: function (xhr, msg) {
// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                console.log(msg + '\n' + xhr.responseText);
            }
        });

     } // DownloadGradeStatusAndIcons

/////////////////////////////////////////////
//========= UploadToggle  ============= PR2020-07-31  PR2021-01-14 PR2022-03-20
    function UploadToggle(el_input) {
        console.log( " ==== UploadToggle ====");
        console.log( "permit_dict", permit_dict);
        //console.log( "permit_dict.permit_approve_grade", permit_dict.permit_approve_grade);

        // only called by field 'se_status', 'sr_status', 'pe_status', 'ce_status'
        mod_dict = {};

        if(permit_dict.permit_approve_grade || permit_dict.permit_block_grade){
            const tblName = "grade";
            const fldName = get_attr_from_el(el_input, "data-field");
            const tblRow = t_get_tablerow_selected(el_input);
            const grade_pk = get_attr_from_el_int(tblRow, "data-pk");
            const data_dict = get_gradedict_by_gradepk(grade_pk);
            //console.log( "data_dict", data_dict);

            if(!isEmpty(data_dict)){

// - get info of this grade
                const examtype_2char = fldName.substring(0,2);
                const is_published = (!!data_dict[examtype_2char + "_published_id"]);
                const is_blocked = (!!data_dict[examtype_2char + "_blocked"]);
                const examperiod = data_dict.examperiod;

// +++ approve grades by school +++++++++++++++++++++
                if(permit_dict.permit_approve_grade){

        // - get auth_index of requsr ( statusindex = 1 when auth1 etc
                    // auth_index : 0 = None, 1 = auth1, 2 = auth2, 3 = auth3, 4 = auth4
                    // b_get_auth_index_of_requsr returns index of auth user, returns 0 when user has none or multiple auth usergroups
                    // this function gives err message when multiple found. (uses b_show_mod_message_html)
                    // get value of highest index
                    const permit_auth_list = b_get_multiple_auth_index_of_requsr(permit_dict)
                    const requsr_auth_index = setting_dict.sel_auth_index;

                    if(requsr_auth_index){

                        if(fldName in data_dict){


    // give message and exit when grade is published
                            if (fldName === "se_status" && requsr_auth_index === 4 ){
                                const msg_html = loc.approve_err_list.Corrector_cannot_approve_se;
                                b_show_mod_message_html(msg_html);
                            } else if (is_published){
                                const msg_html = loc.approve_err_list.This_grade_is_submitted + "<br>" + loc.approve_err_list.You_cannot_change_approval;
                                b_show_mod_message_html(msg_html);
                            } else {

    // - requsr_auth_approved = true when requsr_auth has approved in this function
                                // - auth_dict contains user_id of all auth_index
                                // auth_dict:  {1: 146, 3: 157}
                                let requsr_auth_approved = false;
                                const auth_dict = {};
                                for (let i = 1, key_str; i < 5; i++) {
                                    key_str = examtype_2char + "_auth" + i + "by_id";
                                    if (data_dict[key_str]){
                                        if (requsr_auth_index === i) {
                                            requsr_auth_approved = true;
                                        };
                                        auth_dict[i] = data_dict[key_str];
                                    };
                                };
                                //console.log("auth_dict", auth_dict)
                                //console.log("requsr_auth_approved", requsr_auth_approved)

    // ---  toggle value of requsr_auth_approved
                                const new_requsr_auth_approved = !requsr_auth_approved;

    // also update requsr_pk in auth_dict;
                                auth_dict[requsr_auth_index] = (new_requsr_auth_approved) ? permit_dict.requsr_pk : null;
                                //console.log("auth_dict", auth_dict)

    // give message when status_bool = true and grade already approved by this user in different function
                                // chairperson may also approve as examiner
                                // secretary may alo approve as examiner

                                let already_approved_by_auth_index = null;
                                if(new_requsr_auth_approved){
                                    // chairperson cannot also approve as secretary or as corrector
                                    // secretary cannot also approve as chairperson or as corrector
                                    // examiner cannot also approve as corrector
                                    // corrector cannot also approve as chairperson, secretary or examiner
                                    const no_double_auth_index_list = (requsr_auth_index === 1) ? [2, 4] :
                                                                 (requsr_auth_index === 2) ? [1, 4] :
                                                                 (requsr_auth_index === 3) ? [4] :
                                                                 (requsr_auth_index === 4) ? [1, 2, 3] : [];

                                    for (let i = 0, no_double_auth_index; no_double_auth_index = no_double_auth_index_list[i]; i++) {
                                        if (auth_dict[no_double_auth_index] === auth_dict[requsr_auth_index]) {
                                            already_approved_by_auth_index = no_double_auth_index;
                                            break;
                                        };
                                    };
                                };
                                if (already_approved_by_auth_index) {
                                    const auth_function = b_get_function_of_auth_index(loc, already_approved_by_auth_index);
                                    const msg_html = loc.approve_err_list.Approved_in_function_of + auth_function.toLowerCase() + ".<br>" + loc.approve_err_list.You_cannot_approve_again;
                                    b_show_mod_message_html(msg_html);

                                } else {

    // - give message when grade /score  has no value
                                    // PR2022-03-11 after tel with Nancy Josephina: blank grades can also be approved, give warning first
                                    // no value of exemption is complicated, because of no CE in 2020 and partly in 2021.
                                    // skip no_grade_value of exemption, validate on server
                                    const key_grade = (examtype_2char + "grade");
                                    const no_grade_value = (examperiod !== 4 && !data_dict[key_grade]);
                                    const key_score = (examtype_2char + "score");
                                    const no_score_value = (examtype_2char === "se") ? true : !data_dict[key_score];
                                    // skip msg when removing approved
                                    if (new_requsr_auth_approved && no_grade_value && no_score_value){
                                        mod_dict = {tblName: tblName, fldName: fldName, examtype_2char: examtype_2char,
                                                    data_dict: data_dict, auth_dict: auth_dict, requsr_auth_index: requsr_auth_index,
                                                    is_published: is_published, is_blocked: is_blocked,
                                                    new_requsr_auth_approved: new_requsr_auth_approved, el_input: el_input};

                console.log("mod_dict)", mod_dict);
                                        ModConfirmOpen("approve", el_input);
                                    } else {
                                        UploadApproveGrade(tblName, fldName, examtype_2char, data_dict, auth_dict, requsr_auth_index,
                                                            is_published, is_blocked, new_requsr_auth_approved, el_input) ;
                                    }; //  if (double_approved))
                                };  // if (already_approved_by_auth_index)
                            };  // if (published_pk)
                        };  // if(fldName in data_dict)
                    };  //  if(requsr_auth_index)

    // +++ Inspectorate can block grades +++++++++++++++++++++
                } else if(permit_dict.permit_block_grade ){
                    if (is_published || is_blocked)  {
                        mod_dict = {tblName: tblName,
                                    fldName: fldName,
                                    grade_pk: grade_pk,
                                    examtype_2char: examtype_2char,
                                    examperiod: examperiod,
                                    is_published: is_published,
                                    is_blocked: is_blocked,
                                    data_dict: data_dict,
                                    el_input: el_input};

                        ModConfirmOpen("block_grade")
                    };
                };  // if(permit_dict.permit_approve_grade)
            }  //   if(!isEmpty(data_dict)){
        };  // if(permit_dict.permit_approve_grade){
    };  // UploadToggle

//========= UploadApproveGrade  ============= PR2022-03-12
    function UploadApproveGrade(tblName, fldName, examtype_2char, data_dict, auth_dict, requsr_auth_index,
                                is_published, is_blocked, new_requsr_auth_approved, el_input) {
        console.log( " ==== UploadApproveGrade ====");
// ---  change icon, before uploading
        // check for allowed cluster - othet allowed not nedded because they are not downloaded
        //const is_allowed_cluster = (!data_dict.cluster_id ||
        //                            !permit_dict.requsr_allowed_clusters ||
        //                            !permit_dict.requsr_allowed_clusters.length ||
        //                            permit_dict.requsr_allowed_clusters.includes(data_dict.cluster_id));
        let is_allowed_cluster = true;
        if (permit_dict.requsr_allowed_clusters && permit_dict.requsr_allowed_clusters.length) {
            if (!permit_dict.requsr_allowed_clusters.includes(data_dict.cluster_id)){
                //is_allowed_cluster = false;
            };
        };
        if (!is_allowed_cluster){
            b_show_mod_message_html(loc.approve_err_list.No_cluster_permission);
        } else {

            console.log("auth_dict)", auth_dict);
            const auth4_must_sign = ["pe_status", "ce_status"].includes(fldName);
            const new_class_str = b_get_status_auth1234_iconclass(is_published, is_blocked,
                                    auth_dict[1], auth_dict[2], auth_dict[3], auth4_must_sign, auth_dict[4]);
            el_input.className = new_class_str;
            console.log( "new_class_str)", new_class_str);

    // ---  upload changes
            // value of 'mode' determines if status is set to 'approved' or 'not
            // instead of using value of new_requsr_auth_approvede,
            const mode = (new_requsr_auth_approved) ? "approve_save" : "approve_reset"
            const upload_dict = { table: tblName,
                                   mode: mode,
                                   mapid: data_dict.mapid,
                                   grade_pk: data_dict.id,
                                   field: fldName,
                                   examtype: examtype_2char,
                                   auth_index: requsr_auth_index
                                };
            // UploadChanges(upload_dict, urls.url_grade_approve_single);
            UploadChanges(upload_dict, urls.url_grade_approve);
        };
    }  // UploadApproveGrade


//========= UploadBlockGrade  ============= PR2022-04-16
    function UploadBlockGrade(new_is_blocked) {
        console.log( " ==== UploadBlockGrade ====");

// ---  change icon, before uploading
        // check for allowed cluster - othet allowed not nedded because they are not downloaded
        //const is_allowed_cluster = (!data_dict.cluster_id ||
        //                            !permit_dict.requsr_allowed_clusters ||
        //                            !permit_dict.requsr_allowed_clusters.length ||
        //                            permit_dict.requsr_allowed_clusters.includes(data_dict.cluster_id));
        let is_allowed_cluster = true;
        if (permit_dict.requsr_allowed_clusters && permit_dict.requsr_allowed_clusters.length) {
            if (!permit_dict.requsr_allowed_clusters.includes(data_dict.cluster_id)){
                //is_allowed_cluster = false;
            };
        };
        if (!is_allowed_cluster){
            b_show_mod_message_html(loc.approve_err_list.No_cluster_permission);
        } else {
            // "diamond_1_4" = red diamond: blocked by Inspectorate, published is removed to enable correction
            // "diamond_2_4" = orange diamond: published after blocked by Inspectorate
            //const new_class_str =  (new_is_blocked) ?  "diamond_1_4" : "diamond_2_4";
            //mod_dict.el_input.className = new_class_str;
            //console.log("new_class_str)", new_class_str);

    // ---  upload changes
            const mode = (new_is_blocked) ? "block" : "unblock"
            const upload_dict = { mode: mode,
                                  grade_pk: mod_dict.data_dict.id,
                                  examtype: mod_dict.examtype_2char,
                                  examperiod: mod_dict.examperiod
                                };
            console.log("upload_dict)", upload_dict);

            UploadChanges(upload_dict, urls.url_grade_block);
        };
    }  // UploadBlockGrade


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

                    $("#id_mod_student").modal("hide");

                    if ("msg_html" in response) {
                        b_show_mod_message_html(response.msg_html)
                    };
                    if ("messages" in response) {
                        b_show_mod_message_dictlist(response.messages)
                    };
                    if ("approve_msg_dict" in response && !isEmpty(response.msg_dict)) {
                        MAG_UpdateFromResponse (response);
                    };
                    if ( "approve_msg_html" in response){
                        MAG_UpdateFromResponse(response)
                    };
                    if ("updated_grade_rows" in response) {
                        RefreshDataRows("grades", response.updated_grade_rows, grade_rows, true); // true = is_update
                        //$("#id_mod_approve_grade").modal("hide");
                    };
                    if ("studentsubjectnote_rows" in response) {
                        b_fill_datamap(studentsubjectnote_map, response.studentsubjectnote_rows)
                        ModNote_FillNotes(response.studentsubjectnote_rows);
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


// +++++++++++++++++ MODAL SIDEBAR SELECT ++++++++++++++++++++++++++++++++++++++++++
//=========  SBR_display_subject_cluster_student  ================ PR2022-03-03
    function SBR_display_subject_cluster_student() {
        //console.log("===== SBR_display_subject_cluster_student =====");
        let subject_code = null, subject_name = null, student_code = null, student_name = null;
        if(setting_dict.sel_subject_pk){
            if(setting_dict.sel_subject_code){subject_code = setting_dict.sel_subject_code};
            if(setting_dict.sel_subject_name){subject_name = setting_dict.sel_subject_name};
        } else if (setting_dict.sel_student_pk){
            if(setting_dict.sel_student_name_init){student_code = setting_dict.sel_student_name_init};
            if(setting_dict.sel_student_name){student_name = setting_dict.sel_student_name};
        }
        t_MSSSS_display_in_sbr("subject", setting_dict.sel_subject_pk);
        t_MSSSS_display_in_sbr("cluster", setting_dict.sel_cluster_pk);
        t_MSSSS_display_in_sbr("student", setting_dict.sel_student_pk);
    };  // SBR_display_subject_cluster_student


// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2020-08-03 PR2022-02-17 PR2022-04-17
    function ModConfirmOpen(mode, el_input) {
        console.log(" -----  ModConfirmOpen   ----")
            console.log("mode", mode )
        // values of mode are : "approve", "block_grade", "prelim_ex2"

        // mode already has values, got it in UploadToggle

        mod_dict.mode = mode;

        if (mode === "approve"){
            el_confirm_header.innerText = loc.Approve_grade;
            el_confirm_loader.classList.add(cls_visible_hide)
            el_confirm_msg_container.className = "p-3";

            const msg_html = ["<p class='p-2 border_bg_warning'><b>",
            loc.approve_err_list.Warning,":</b> ",
            loc.approve_err_list.This_grade_has_no_value, "<br>",
            loc.approve_err_list.Need_permission_of_inspectorate, "</p>"].join("");
            el_confirm_msg_container.innerHTML = msg_html;

            el_confirm_loader.className = cls_hide;

            el_confirm_btn_save.innerText = loc.OK;
            el_confirm_btn_cancel.innerText = loc.Cancel;
            add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", false, "btn-primary");

        // set focus to save button
            setTimeout(function (){
                el_confirm_btn_save.focus();
            }, 500);
        // show modal
            $("#id_mod_confirm").modal({backdrop: true});

        } else if (mode === "block_grade"){
            el_confirm_header.innerText = (mod_dict.is_blocked) ? loc.Unblock_grade : loc.Block_grade;
            el_confirm_msg_container.className = "p-3";
            let msg_html = null;
            if (mod_dict.is_blocked) {
                msg_html = ["<p>", loc.MAG_info.unblock_01, "</p>",
                                    "<p>", loc.Do_you_want_to_continue, "</p>"].join("");
            } else {
                msg_html = ["<p>", loc.MAG_info.block_01, "</p>",
                                    "<p class='p-2'><small>",
                                        loc.MAG_info.block_02, " ",
                                        loc.MAG_info.block_03, " ",
                                        loc.MAG_info.block_04, "</small></p>",
                                    "<p>", loc.MAG_info.block_05, " ",
                                        loc.MAG_info.block_06, "</p>",
                                    "<p>", loc.Do_you_want_to_continue, "</p>"].join("");
            }
            el_confirm_msg_container.innerHTML = msg_html;

            el_confirm_loader.className = cls_hide;

            el_confirm_btn_save.innerText = loc.OK;
            el_confirm_btn_cancel.innerText = loc.Cancel;
            add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", false, "btn-primary");

            console.log("mod_dict", mod_dict )

        // set focus to save button
            setTimeout(function (){
                el_confirm_btn_save.focus();
            }, 500);
        // show modal
            $("#id_mod_confirm").modal({backdrop: true});

        } else if (mode === "prelim_ex2"){
            el_confirm_header.innerText = loc.Download_Ex_form;
            el_confirm_loader.classList.add(cls_visible_hide)
            el_confirm_msg_container.className = "p-3";

            const msg_html = "<p>" + loc.The_preliminary_Ex2_form + loc.will_be_downloaded + "</p><p>" + loc.Do_you_want_to_continue + "</p>"
            el_confirm_msg_container.innerHTML = msg_html;
            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            if (el_modconfirm_link) {
                el_modconfirm_link.setAttribute("href", urls.url_grade_download_ex2);
            };

            el_confirm_loader.className = cls_hide;

            el_confirm_btn_save.innerText = loc.OK;
            el_confirm_btn_cancel.innerText = loc.Cancel;
            add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", false, "btn-primary");

        // set focus to save button
            setTimeout(function (){
                el_confirm_btn_save.focus();
            }, 500);
        // show modal
            $("#id_mod_confirm").modal({backdrop: true});
        };
    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2019-06-23
    function ModConfirmSave() {
        console.log(" --- ModConfirmSave --- ");
        console.log("mod_dict: ", mod_dict);

        if (mod_dict.mode === "approve"){
                UploadApproveGrade(mod_dict.tblName, mod_dict.fldName, mod_dict.examtype,
                            mod_dict.data_dict, mod_dict.auth_dict, mod_dict.requsr_auth_index,
                            mod_dict.is_published, mod_dict.is_blocked, mod_dict.new_requsr_auth_approved,
                            mod_dict.el_input) ;

        } else if (mod_dict.mode === "block_grade"){
                const new_blocked = !mod_dict.is_blocked;

                UploadBlockGrade(new_blocked) ;

        } else if (mod_dict.mode === "prelim_ex2"){
            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            if (el_modconfirm_link) {
                el_modconfirm_link.click();
            // show loader
                el_confirm_loader.classList.remove(cls_visible_hide)

            };
        };

    // close modal
        $("#id_mod_confirm").modal("hide");
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
                    };
                };
            };
        };
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

//=========  ModMessageClose  ================ PR2020-12-20
    function ModMessageClose() {
        //console.log(" --- ModMessageClose --- ");
        //console.log("mod_dict.el_focus: ", mod_dict.el_focus);
        if (mod_dict.el_focus) { set_focus_on_el_with_timeout(mod_dict.el_focus, 150)}

    }  // ModMessageClose


//========= MOD APPROVE GRADE ==================================== PR2022-03-09
    function MAG_Open (mode ) {
        console.log("===  MAG_Open  =====") ;
        console.log("mode", mode) ;
        console.log("setting_dict", setting_dict) ;
        // mode = 'approve' or 'submit_ex2' or 'submit_ex2a'

        b_clear_dict(mod_MAG_dict);

// --- check sel_examperiod
        if (![1,2,3].includes(setting_dict.sel_examperiod) ){
            b_show_mod_message_html(loc.Please_select_examperiod);
        // sel_examtype = "se", "pe", "ce", "reex", "reex03", "exem"
        } else if (!["se", "pe", "ce", "reex", "reex03", "exem"].includes(setting_dict.sel_examtype) ){
            b_show_mod_message_html(loc.Please_select_examtype);
        } else if (mode === "submit_ex2" && setting_dict.sel_examtype !== "se") {
            b_show_mod_message_html(loc.Please_select_schoolexam);
        } else if (mode === "submit_ex2a" && !["ce", "reex", "reex03"].includes(setting_dict.sel_examtype) ){
            b_show_mod_message_html(loc.Please_select_correct_exam);
        } else {

// PR2022-03-13 debug: also check on allowed subjects, levels and clusters

// put info in mod_MAG_dict
            // modes are 'approve' 'submit_test' 'submit_save'
            mod_MAG_dict.mode = mode;
            mod_MAG_dict.step = 0;

            mod_MAG_dict.auth_index = setting_dict.sel_auth_index;

            mod_MAG_dict.may_test = true;
            mod_MAG_dict.test_is_ok = false;
            mod_MAG_dict.submit_is_ok = false;
            mod_MAG_dict.is_reset = false;

            mod_MAG_dict.is_approve_mode = (mode === "approve");
            mod_MAG_dict.is_submit_ex2_mode = (mode === "submit_ex2");
            mod_MAG_dict.is_submit_ex2a_mode = (mode === "submit_ex2a");

// --- get list of auth_index of requsr
            const requsr_auth_list = [];
            if (permit_dict.usergroup_list.includes("auth1")){requsr_auth_list.push(1)};
            if (permit_dict.usergroup_list.includes("auth2")){requsr_auth_list.push(2)};
           // add examiner and commissiner only when mode = approve
            if (mod_MAG_dict.is_approve_mode){
                if (permit_dict.usergroup_list.includes("auth3")){requsr_auth_list.push(3)};
                if (permit_dict.usergroup_list.includes("auth4")){requsr_auth_list.push(4)};
            };
            console.log("requsr_auth_list", requsr_auth_list) ;

// get selected auth_index (user can be pres / secr and examiner at the same time)
            if (requsr_auth_list.length) {
                if(!setting_dict.sel_auth_index || !requsr_auth_list.includes(setting_dict.sel_auth_index)){
                    // when sel_auth_index is null or not in requsr_auth_list: make first item of requsr_auth_list the sel_auth_index
                    setting_dict.sel_auth_index = requsr_auth_list[0];
                };
            } else {
                // reset sel_auth_index when user has no auth
                setting_dict.sel_auth_index = null;
            };
            console.log("setting_dict.sel_auth_index", setting_dict.sel_auth_index) ;

            if (setting_dict.sel_auth_index === 4 && !["pe", "ce", "reex", "reex03"].includes(setting_dict.sel_examtype) ){
                setting_dict.sel_auth_index = null;
                const info_txt = (setting_dict.sel_examtype === "exem") ?
                                loc.MAG_info.corrector_cannot_approve_exem :
                                loc.MAG_info.corrector_cannot_approve_se;
                b_show_mod_message_html(info_txt);
            };

// get has_permit
            mod_MAG_dict.permit_same_school = (permit_dict.requsr_same_school) ?
                                        (mod_MAG_dict.is_approve_mode && permit_dict.permit_approve_grade) ||
                                        (mod_MAG_dict.is_submit_ex2_mode && permit_dict.permit_submit_grade) ||
                                        (mod_MAG_dict.is_submit_ex2a_mode && permit_dict.permit_submit_grade) : false;

            mod_MAG_dict.has_permit =
                    (mod_MAG_dict.auth_index)
                    ? (mod_MAG_dict.is_approve_mode && permit_dict.permit_approve_grade)
                        ? (permit_dict.requsr_same_school || permit_dict.requsr_role_comm)
                        : (mod_MAG_dict.is_submit_ex2_mode || mod_MAG_dict.is_submit_ex2a_mode)
                            ? (permit_dict.requsr_same_school && permit_dict.permit_submit_grade)
                            : false
                    : false;

            if (mod_MAG_dict.has_permit && mod_MAG_dict.auth_index){

// --- get header_txt and subheader_txt
                const header_txt = (mod_MAG_dict.is_approve_mode) ? loc.Approve_grades :
                                    (mod_MAG_dict.is_submit_ex2_mode) ? loc.Submit_Ex2_form :
                                    (mod_MAG_dict.is_submit_ex2a_mode) ? loc.Submit_Ex2A_form : null;
                el_MAG_header.innerText = header_txt;
                const subheader_txt = (mod_MAG_dict.is_approve_mode) ? loc.MAG_info.subheader_approve :
                                      (mod_MAG_dict.is_submit_ex2_mode) ? loc.MAG_info.subheader_submit_ex2 :
                                      (mod_MAG_dict.is_submit_ex2a_mode) ? loc.MAG_info.subheader_submit_ex2a : null;
                el_MAG_subheader.innerText = subheader_txt;

// --- get examperiod and examtype text
                // sel_examperiod 4 shows "Vrijstelling" as examperiod, replace by "Eerste tijdvak"
                // sel_examperiod 12 shows "Eerste tijdvak / Tweede tijdvak" replace by "---"
                // replace by First period
                el_MAG_examperiod.innerText = (setting_dict.sel_examperiod === 3) ? loc.examperiod_caption[3] :
                                (setting_dict.sel_examperiod === 2) ? loc.examperiod_caption[2] :
                                ([1, 4].includes(setting_dict.sel_examperiod)) ? loc.examperiod_caption[1] : "---"

                // sel_examtype = "se", "pe", "ce", "reex", "reex03", "exem"
                let examtype_caption = null;
                for (let i = 0, dict; dict = loc.options_examtype[i]; i++) {
                    if(dict.value === setting_dict.sel_examtype) {
                        examtype_caption = dict.caption;
                        break;
                    }
                }
                el_MAG_examtype.innerText = examtype_caption

// --- hide filter subject, cluster when submitting Ex2 Ex2a form. Leave level visible if exists, MPC must be able to submit per level
                const show_subj_lvl_cls_container = setting_dict.sel_dep_level_req || mod_MAG_dict.is_approve_mode;
                add_or_remove_class(el_MAG_subj_lvl_cls_container, cls_hide, !show_subj_lvl_cls_container);

// --- hide level textbox when not sel_dep_level_req
                add_or_remove_class(el_MAG_lvlbase.parentNode, cls_hide, !setting_dict.sel_dep_level_req);

                const level_abbrev = (setting_dict.sel_lvlbase_pk) ? setting_dict.sel_level_abbrev : "<" + loc.All_levels + ">";
                el_MAG_lvlbase.innerText = level_abbrev;


// --- get cluster_text
                let cluster_text = "---";
                if(setting_dict.sel_cluster_pk){
                    const [middle_index, found_dict, compare] = b_recursive_integer_lookup(cluster_rows, "id", setting_dict.sel_cluster_pk);
                    if (found_dict){
                        cluster_text = (found_dict.name) ? found_dict.name : "---";
                    };
                } else {
                    cluster_text = "<" + loc.All_clusters + ">";
                };
                el_MAG_cluster.innerText = cluster_text;

// get subject_text
                let subject_text = null;
                if(setting_dict.sel_subject_pk){
                    const [middle_index, found_dict, compare] = b_recursive_integer_lookup(subject_rows, "id", setting_dict.sel_subject_pk);
                    if (found_dict){ subject_text = (found_dict.name) ? found_dict.name : "---" };

                } else {
                    subject_text = "<" + loc.All_subjects + ">";
                };
                el_MAG_subject.innerText = subject_text;

// --- get approved_by
                if (el_MAG_approved_by_label){
                    el_MAG_approved_by_label.innerText = ( (mod_MAG_dict.is_submit_ex2_mode) ? loc.Submitted_by : loc.Approved_by ) + ":"
                }
                if (el_MAG_approved_by){
                    el_MAG_approved_by.innerText = permit_dict.requsr_name;
                }

// --- fill selectbox auth_index
                if (el_MAG_auth_index){
                    // auth_list = [{value: 1, caption: 'Chairperson'}, {value: 3, caption: 'Examiner'} )
                    const auth_list = [];
                    const cpt_list = [null, loc.Chairperson, loc.Secretary, loc.Examiner, loc.Corrector];
                    for (let i = 0, auth_index; auth_index = requsr_auth_list[i]; i++) {
                        auth_list.push({value: auth_index, caption: cpt_list[auth_index]});
                    };
                    t_FillOptionsFromList(el_MAG_auth_index, auth_list, "value", "caption",
                        loc.Select_function, loc.No_functions_found, setting_dict.sel_auth_index);
                };

// --- reset ok button
                MAG_SetMsgContainer()
                MAG_SetInfoContainer();
                MAG_SetBtnSaveDeleteCancel();

// --- open modal
                $("#id_mod_approve_grade").modal({backdrop: true});

            };  // if (permit_dict.permit_approve_grade || permit_dict.permit_submit_grade)
        };
    };  // MAG_Open

//=========  MAG_Save  ================
    function MAG_Save (save_mode) {
        console.log("===  MAG_Save  =====") ;
        console.log("save_mode", save_mode) ;
        // save_mode = 'save' or 'delete'

        if (permit_dict.permit_approve_grade || permit_dict.permit_submit_grade) {

            mod_MAG_dict.is_reset = (save_mode === "delete");

    console.log("mod_MAG_dict.step", mod_MAG_dict.step)

            //  upload_modes are: 'approve_test', 'approve_save', 'approve_reset', 'submit_test', 'submit_save'
            const upload_dict = {
                table: "grade",
                form: (mod_MAG_dict.is_submit_ex2a_mode) ? "ex2a" : "ex2",
                auth_index: mod_MAG_dict.auth_index,
                now_arr: get_now_arr()  // only for timestamp on filename saved Ex-form
                };

            let url_str = null;
            if (mod_MAG_dict.is_approve_mode){
                url_str = urls.url_grade_approve;
                if (mod_MAG_dict.is_reset) {
                    upload_dict.mode = "approve_reset";
                } else {
                    upload_dict.mode = (mod_MAG_dict.test_is_ok) ? "approve_save" : "approve_test";
                };
            } else {
                if (mod_MAG_dict.step === 1 && mod_MAG_dict.test_is_ok){
                    url_str = urls.url_studsubj_send_email_exform;
                } else if (mod_MAG_dict.is_submit_ex2_mode || mod_MAG_dict.is_submit_ex2a_mode){
                    url_str = urls.url_grade_submit_ex2;

                    if (mod_MAG_dict.test_is_ok){
                        upload_dict.mode = "submit_save";

                        upload_dict.verificationcode = el_MAG_input_verifcode.value
                        upload_dict.verificationkey = mod_MAG_dict.verificationkey;
                    } else {
                        upload_dict.mode = "submit_test";
                    };
                };
            };

    // ---  show loader
            add_or_remove_class(el_MAG_loader, cls_hide, false)

    // ---  disable select auth_index after clicking save button
            if (el_MAG_auth_index){
                el_MAG_auth_index.disabled = true;
            };

    // ---  hide info box and msg box
            add_or_remove_class(el_MAG_msg_container, cls_hide, true)
            add_or_remove_class(el_MAG_info_container, cls_hide, true)

    // ---  hide delete btn
            add_or_remove_class(el_MAG_btn_delete, cls_hide, true);

    console.log("upload_dict", upload_dict);

            UploadChanges(upload_dict, url_str);
// hide modal when clicked on save btn when test_is_ok
            if (mod_MAG_dict.test_is_ok){
                //$("#id_mod_approve_grade").modal("hide");
            };
        }  // if (permit_dict.permit_approve_grade || permit_dict.permit_submit_grade)
    };  // MAG_Save

//=========  MAG_UploadAuthIndex  ================ PR2022-03-13
    function MAG_UploadAuthIndex (el_select) {
        //console.log("===  MAG_UploadAuthIndex  =====") ;

// ---  put new  auth_index in mod_MAG_dict and setting_dict
        mod_MAG_dict.auth_index = (Number(el_select.value)) ? Number(el_select.value) : null;
        setting_dict.sel_auth_index = mod_MAG_dict.auth_index;
        setting_dict.sel_auth_function = b_get_function_of_auth_index(loc, mod_MAG_dict.auth_index);
        //console.log( "setting_dict.sel_auth_function: ", setting_dict.sel_auth_function);

// ---  upload new setting
        const upload_dict = {selected_pk: {sel_auth_index: setting_dict.sel_auth_index}};
        b_UploadSettings (upload_dict, urls.url_usersetting_upload);

    }; // MAG_UploadAuthIndex


//=========  MAG_UpdateFromResponse  ================ PR2021-02-08 PR2022-04-18
    function MAG_UpdateFromResponse (response) {
        console.log("===  MAG_UpdateFromResponse  =====") ;

        mod_MAG_dict.step += 1;
        console.log("mod_MAG_dict.step", mod_MAG_dict.step) ;

        mod_MAG_dict.verification_is_ok = !!response.verification_is_ok;
        mod_MAG_dict.verificationkey = (mod_MAG_dict.verification_is_ok) ? response.verificationkey : null;

// create message in el_MAG_msg_container
        MAG_SetMsgContainer(response);
        MAG_SetInfoContainer();
// hide ok button when not mod_MAG_dict.test_is_ok
        MAG_SetBtnSaveDeleteCancel ();
// hide modal after submitting, only when is_approve_mode
        if(mod_MAG_dict.step === 2 && mod_MAG_dict.is_approve_mode){
            $("#id_mod_approve_grade").modal("hide");
        };

    };  // MAG_UpdateFromResponse

//=========  MAG_SetBtnSaveDeleteCancel  ================ PR2021-02-08
     function MAG_SetBtnSaveDeleteCancel() {
        console.log("===  MAG_SetBtnSaveDeleteCancel  =====") ;

        const is_approve_mode = mod_MAG_dict.is_approve_mode;
        const is_submit_ex2_mode = mod_MAG_dict.is_submit_ex2_mode;
        const is_submit_ex2a_mode = mod_MAG_dict.is_submit_ex2a_mode;
        const is_reset = mod_MAG_dict.is_reset;

        const step = mod_MAG_dict.step;
        const may_test = mod_MAG_dict.may_test;
        const test_is_ok = mod_MAG_dict.test_is_ok;
        const submit_is_ok = mod_MAG_dict.submit_is_ok;

        const has_already_approved = !!mod_MAG_dict.has_already_approved;
        const has_already_published = !!mod_MAG_dict.has_already_published;
        const has_saved = !!mod_MAG_dict.has_saved;

        console.log("mod_MAG_dict.step", mod_MAG_dict.step) ;
        console.log("is_approve_mode", is_approve_mode) ;
        console.log("is_submit_ex2_mode", is_submit_ex2_mode) ;
        console.log("is_submit_ex2a_mode", is_submit_ex2a_mode) ;
        console.log("may_test", may_test) ;
        console.log("test_is_ok", test_is_ok) ;
        console.log("submit_is_ok", submit_is_ok) ;

// ---  hide save button when not can_publish
        let show_save_btn = false;
        if (is_approve_mode){
            show_save_btn = (may_test || test_is_ok);
        } else {
            show_save_btn = (may_test || test_is_ok);
        }
        add_or_remove_class(el_MAG_btn_save, cls_hide, !show_save_btn);

        let save_btn_txt = loc.Check_grades;
        if (step === 0) {

        } else if (step === 1) {
            if (test_is_ok){
                save_btn_txt = (is_approve_mode) ? loc.Approve_grades : loc.Request_verifcode;
            };
        } else if (step === 2) {
            if (test_is_ok){
                save_btn_txt = (is_approve_mode) ? loc.Approve_grades :
                                (is_approve_mode) ? loc.Approve_grades :
                                (is_approve_mode) ? loc.Approve_grades : loc.Check_grades ;
            } else {

            }
        }
        el_MAG_btn_save.innerText = save_btn_txt;

        let btn_cancel_text = (submit_is_ok || (!may_test && !test_is_ok) || (!submit_is_ok)) ? loc.Close : loc.Cancel;
        el_MAG_btn_cancel.innerText = btn_cancel_text;

// ---  show only the elements that are used in this tab
        let show_class = "tab_step_" + step;

        b_show_hide_selected_elements_byClass("tab_show", show_class, el_mod_approve_grade);

// ---  hide delete btn when reset or publish mode
        let show_delete_btn = false;
        if (is_approve_mode){
            if (has_already_approved) {show_delete_btn = true}
        }
        //const show_delete_btn = (is_approve_mode && !is_reset && test_is_ok)
        add_or_remove_class(el_MAG_btn_delete, cls_hide, !show_delete_btn);

     } //  MAG_SetBtnSaveDeleteCancel

//=========  MAG_SetMsgContainer  ================ PR2021-02-08 PR2022-04-17
     function MAG_SetMsgContainer(response) {
        console.log("===  MAG_SetMsgContainer  =====") ;

// --- show info and hide loader
        add_or_remove_class(el_MAG_loader, cls_hide, true);

        el_MAG_msg_container.innerHTML = null;
        let show_msg_container = false;


        console.log("mod_MAG_dict.step", mod_MAG_dict.step);

        const show_input_verifcode = (response && !!response.approve_msg_html);
        add_or_remove_class(el_MAG_input_verifcode.parentNode, cls_hide, !show_input_verifcode);


        console.log("show_input_verifcode", show_input_verifcode);
        if (show_input_verifcode){
            show_msg_container = true;

            mod_MAG_dict.verificationkey = response.verificationkey

            el_MAG_msg_container.className = "mt-2";
            el_MAG_msg_container.innerHTML = response.approve_msg_html

            console.log("response.approve_msg_html", response.approve_msg_html);
            if (show_input_verifcode){set_focus_on_el_with_timeout(el_MAG_input_verifcode, 150)};

        } else if (response && !isEmpty(response.msg_dict)){

            const msg_dict = response.msg_dict;
            console.log("msg_dict", msg_dict);
            console.log("response.test_is_ok", response.test_is_ok);
            //console.log("mod_MAG_dict", mod_MAG_dict);

            const test_is_ok = (!!response.test_is_ok)

    // ---  hide loader
            add_or_remove_class(el_MAG_loader, cls_hide, true);
            let msg01_txt = null,  msg02_txt = null, msg03_txt = null, msg_04_txt = null;

    // make message container green when grades can be published, red otherwise
            // msg_dict.saved > 0 when grades are approved or published

            mod_MAG_dict.may_test = false;
            mod_MAG_dict.test_is_ok = !!response.test_is_ok;
            mod_MAG_dict.has_already_approved = (msg_dict && !!msg_dict.already_approved)
            mod_MAG_dict.has_already_published = (msg_dict && !!msg_dict.already_published)
            mod_MAG_dict.has_saved = msg_dict && !!msg_dict.saved;
            mod_MAG_dict.submit_is_ok = msg_dict && !!msg_dict.now_saved;  // submit_is_ok when records are saved



            show_msg_container = true
           // const border_class = (mod_MAG_dict.test_is_ok) ? "border_bg_valid" : "border_bg_invalid";
            //console.log("mod_MAG_dict.test_is_ok", mod_MAG_dict.test_is_ok) ;
            //const bg_class = (mod_MAG_dict.test_is_ok) ? "border_bg_valid" : "border_bg_invalid" // "border_bg_message"
            //el_MAG_msg_container.className = bg_class
            let bg_class_ok = (mod_MAG_dict.test_is_ok || mod_MAG_dict.has_saved );
            const bg_class = (!bg_class_ok) ? "border_bg_invalid" : (msg_dict.warning) ? "border_bg_warning" : "border_bg_valid";

        console.log("bg_class", bg_class) ;
            el_MAG_msg_container.className = "mt-2 p-2 " + bg_class;

    // create message in container
            const array = ["count_text", "skip_text", "already_published_text", "no_value_text", "auth_missing_text",
                "double_approved_text", "already_approved_text", "saved_text", "saved_text2"]
            for (let i = 0, el, key; key = array[i]; i++) {
                if(key in msg_dict) {
        //console.log("key", key) ;
        //console.log("msg_dict[key]", msg_dict[key]) ;
                    el = document.createElement("p");
                    el.innerText = msg_dict[key];
                    if (key === "count_text") {
                        el.classList.add("pb-2");
                    } else if (key === "saved_text") {
                        el.classList.add("pt-2");
                    } else if (key === "saved_text2") {
                        el.classList.add("pt-0");
                    } else if (key === "skip_text") {
                    } else {
                        el.classList.add("pl-4");
                    };
                    el_MAG_msg_container.appendChild(el);
                };
            };
            if(msg_dict.file_name) {
                const el = document.createElement("p");
                el.innerHTML = msg_dict.file_name;
                el_MAG_msg_container.appendChild(el);
            };

            if(msg_dict.warning) {
                const el = document.createElement("div");
                el.innerHTML = msg_dict.warning;
                el_MAG_msg_container.appendChild(el);
            };

           // msg01_txt = "The selection contains " + msg_dict.count + " grades."
           // if (msg_dict.no_value){msg02_txt = " -  " + msg_dict.no_value + " grades have no value. They will be skipped."}
           // if (msg_dict.auth_missing){msg03_txt = " -  " + msg_dict.auth_missing + " grades are not completely authorized. They will be skipped"}
            //if (msg_dict.already_published){msg03_txt = " -  " + msg_dict.already_published + " grades are already submitted.They will be skipped."}
        };

        add_or_remove_class(el_MAG_msg_container, cls_hide, !show_msg_container)
    };  // MAG_SetMsgContainer

//=========  MAG_SetInfoContainer  ================ PR2022-04-17
     function MAG_SetInfoContainer() {
        console.log("===  MAG_SetInfoContainer  =====") ;
        console.log("mod_MAG_dict.step", mod_MAG_dict.step) ;
        console.log("mod_MAG_dict.test_is_ok", mod_MAG_dict.test_is_ok) ;

        el_MAG_info_container.innerHTML = null;

// put info text in el_MAG_info_container, only on open modal
        // el_MAG_info_container contains: 'Klik op 'Cijfers controleren' om de cijfers te controleren voordat ze worden ingediend.
        // only visible on open modal
        // Klik op 'Verificatiecode aanvragen', dan sturen we je een e-mail met de verificatiecode. De verificatiecode blijft 30 minuten geldig.

        let inner_html = "";
        if (mod_MAG_dict.step === 0) {
            // step 0: when form opens
            const ex2_key = ( ["se", "sr"].includes(setting_dict.sel_examtype) ) ? "ex2" :
                            ( ["pe", "ce"].includes(setting_dict.sel_examtype) ) ? "ex2a" : "ex2";
        console.log("ex2_key", ex2_key) ;
            const keys = (mod_MAG_dict.is_approve_mode) ?
                            ["approve_0", "approve_1_" + ex2_key, "approve_2_" + ex2_key] :
                            ["submit_0", "submit_1", "submit_2"];
            for (let i = 0, el, key; key = keys[i]; i++) {
                inner_html += "<div><small>" + loc.MAG_info[key] + "</div></small>";
            }
        } else if (mod_MAG_dict.step === 1) {
            if(mod_MAG_dict.is_submit_ex2_mode || mod_MAG_dict.is_submit_ex2a_mode){
                if(mod_MAG_dict.test_is_ok){
                    inner_html = ["<div class='py-0'><small>", loc.MAG_info.verif_01,
                                "<br>", loc.MAG_info.verif_02,
                                "<br>", loc.MAG_info.verif_03,
                                "</small></div>"].join("");
                };
            };
        };
        add_or_remove_class(el_MAG_info_container, cls_hide, !inner_html)
        el_MAG_info_container.innerHTML = inner_html
    };  // MAG_SetInfoContainer


//=========  MAG_InputVerifcode  ================ PR2022-04-18
     function MAG_InputVerifcode(el_input, event_key) {
        console.log("===  MAG_InputVerifcode  =====") ;

        if(event_key && event_key === "Enter"){

        }
        // enable save btn when el_input has value
        const disable_save_btn = !el_input.value;
        //console.log("disable_save_btn", disable_save_btn) ;
        el_MAG_btn_save.disabled = disable_save_btn;

        if(!disable_save_btn && event_key && event_key === "Enter"){
            MAG_Save("save")
        }
     };  // MAG_InputVerifcode

/////////////////////////////////////////////

//========= MOD NOTE Open====================================
    function ModNote_Open (el_input) {
        console.log("===  ModNote_Open  =====") ;
        console.log("el_input", el_input) ;

    // get has_note from grade_map
        const grade_dict = get_datadict_by_el(el_input);
        const has_note = !!get_dict_value(grade_dict, ["note_status"])

// reset notes_container
        el_ModNote_notes_container.innerText = null;

// reset input_note
        el_ModNote_input_note.value = null;

// --- show input element for note, only when user has permit
        const has_permit_intern_extern = (permit_dict.permit_write_note_intern || permit_dict.permit_write_note_extern)
        let may_open_modnote = has_permit_intern_extern || (permit_dict.permit_read_note && has_note);
        if(may_open_modnote){
            // only show input block when  has_permit_intern_extern
            add_or_remove_class(el_ModNote_input_container, cls_hide, !has_permit_intern_extern)
            // hide external note if no permit write_note_extern
            add_or_remove_class(el_ModNote_external, cls_hide, !permit_dict.permit_write_note_extern)

            // hide option icons when not inspection
            const el_ModNote_memo_icon4 = document.getElementById("id_ModNote_memo_external")
            const icon_els = el_ModNote_external.children
            if (!permit_dict.requsr_role_insp){
                for (let i = 0, el; el = el_ModNote_external.children[i]; i++) {
                    const data_icon = el.getAttribute("data-icon")
                    if (["3", "4", "6"].includes(data_icon)){
                        el.classList.add(cls_hide)
                    };
                };
            };

    // get tr_selected
            let tr_selected = t_get_tablerow_selected(el_input)

            if(!isEmpty(grade_dict)){

                let headertext = (grade_dict.fullname) ? grade_dict.fullname + "\n" : "";
                if(grade_dict.subj_code) { headertext += grade_dict.subj_name};
                el_ModNote_header.innerText = headertext;

        //console.log("grade_dict", grade_dict) ;
                mod_note_dict.studsubj_pk = grade_dict.studsubj_id
                mod_note_dict.examperiod = grade_dict.examperiod

                ModNote_SetInternalExternal("internal");

    // download existing studentsubjectnote_rows of this studsubj
                // will be filled in ModNote_FillNotes

    // show loader
            const el_ModNote_loader = document.getElementById("id_ModNote_loader");
            add_or_remove_class(el_ModNote_loader, cls_hide, false);
                const upload_dict = {studsubj_pk: grade_dict.studsubj_id};
                UploadChanges(upload_dict, urls.url_studentsubjectnote_download)

                if (el_input){ setTimeout(function (){ el_ModNote_input_note.focus() }, 50)};

    // get info from grade_map
                $("#id_mod_note").modal({backdrop: true});
            }
        }  // if(permit_dict.permit_read_note)
    }  // ModNote_Open

//========= ModNote_Save============== PR2020-10-15
    function ModNote_Save () {
        console.log("===  ModNote_Save  =====");
        const filename = document.getElementById("id_ModNote_filedialog").value;

        if(permit_dict.permit_write_note_intern || permit_dict.permit_permit_write_note_extern){
            const note = el_ModNote_input_note.value;
            const note_status = (!mod_note_dict.is_internal) ? "1_" + mod_note_dict.sel_icon : "0_1";

// get attachment info
            const file = document.getElementById("id_ModNote_filedialog").files[0];  // file from input
            const file_type = (file) ? file.type : null;
            const file_name = (file) ? file.name : null;
            const file_size = (file) ? file.size : 0;

        console.log("file_name", file_name);
           // may check size or type here with
            // ---  upload changes
            const upload_dict = { table: mod_note_dict.table,
                                   create: true,
                                   studsubj_pk: mod_note_dict.studsubj_pk,
                                   examperiod: mod_note_dict.examperiod,
                                   note: note,
                                   is_internal_note: mod_note_dict.is_internal,
                                   note_status: note_status,
                                   file_type: file_type,
                                   file_name: file_name,
                                   file_size: file_size
                                   };
            const upload_json = JSON.stringify (upload_dict)

            if(note || file_size){
                const upload = new Upload(upload_json, file, urls.url_studentsubjectnote_upload);
                upload.doUpload();
           }
       }
// hide modal
        $("#id_mod_note").modal("hide");
    }  // ModNote_Save

//?????????????????????????????????????????????????????????????????

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
        //console.log( "attachment type",  this.getType())
        //console.log( "attachment name", this.getName())

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

        //const parameters = {"upload": JSON.stringify (upload_dict)}
        const parameters = formData;
        $.ajax({
            type: "POST",
            url: this.url_str,
                //xhr: function () {
                //     var myXhr = $.ajaxSettings.xhr();
                //      if (myXhr.upload) {
                //         myXhr.upload.addEventListener('progress', that.progressHandling, false);
                //      }
                //     return myXhr;
                //   },
            data: parameters,
            dataType:'json',
            success: function (response) {
                // ---  hide loader
                el_loader.classList.add(cls_visible_hide)

                if ("grade_note_icon_rows" in response) {
                    const tblName = "grades";
                    const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                    //RefreshDataMap(tblName, field_names, response.grade_note_icon_rows, grade_map, false);  // false = don't show green ok background


                    RefreshDataRows("grades", response.grade_note_icon_rows, grade_rows, true); // true = is_update
                }

            },  // success: function (response) {


            error: function (xhr, msg) {
                // ---  hide loader
                el_loader.classList.add(cls_visible_hide)
                console.log(msg + '\n' + xhr.responseText);
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
    //console.log("progressHandling", event)
        let percent = 0;
        const position = event.loaded || event.position;
        const total = event.total;
        const progress_bar_id = "#progress-wrp";
        if (event.lengthComputable) {
            percent = Math.ceil(position / total * 100);
        }
    //console.log("percent", percent)
        // update progressbars classes so it fits your code
        $(progress_bar_id + " .progress-bar").css("width", +percent + "%");
        $(progress_bar_id + " .status").text(percent + "%");
    };

//?????????????????????????????????????????????????????????????????

//========= ModNote_SetInternalExternal============== PR2021-01-17
    function ModNote_SetInternalExternal (mode, el_btn) {
        //console.log("===  ModNote_SetInternalExternal  =====") ;
        //console.log("mode", mode) ;
        // when opening form el_btn = undefined, set is_internal = True and icon = "1"
        mod_note_dict.is_internal = (mode === "internal")
        if(mod_note_dict.is_internal){
            mod_note_dict.sel_icon = "";
        } else {
            // set sel_icon when clicked on icon
            if (mode === "external_icon") {
                mod_note_dict.sel_icon = get_attr_from_el(el_btn, "data-icon")
            } else {
            // set default icon = "1" when clicked on button
                if(!mod_note_dict.sel_icon) {mod_note_dict.sel_icon = "1"};
            }
        }

        //console.log("mod_note_dict.sel_icon", mod_note_dict.sel_icon) ;
        //console.log("mod_note_dict.is_internal", mod_note_dict.is_internal)

        add_or_remove_class(el_ModNote_internal, "tr_hover", mod_note_dict.is_internal);
        add_or_remove_class(el_ModNote_external, "tr_hover", !mod_note_dict.is_internal);

        const el_internal_icon = document.getElementById("id_ModNote_internal_icon");
        add_or_remove_class(el_internal_icon, "note_1_1", mod_note_dict.is_internal, "note_0_1");
        // skip when clicked on button instead of icon (in that case sel_icon is null)

        // set selected icon in btn ( note_1_2 is colored, note_0_2 is grey
        for (let i = 0, el; el = el_ModNote_external.children[i]; i++) {
            const index = get_attr_from_el(el, "data-icon")
            if(index){
                const selected = (index === mod_note_dict.sel_icon)
                add_or_remove_class(el, "note_1_" + index, selected, "note_0_" + index )
            }
        }

        // when internal, add schoolbase of request_user (NOT of selected school) to intern_schoolbase
        // when external, field intern_schoolbase is null
        mod_note_dict.intern_schoolbase_pk = (mod_note_dict.is_internal) ? setting_dict.requsr_schoolbase_pk : null;

        //console.log("mod_note_dict", mod_note_dict) ;
    }  // ModNote_SetInternalExternal

//========= ModNote_FillNotes============== PR2020-10-15
    function ModNote_FillNotes (note_rows) {
        //console.log("===  ModNote_FillNotes  =====") ;
        //console.log("note_rows", note_rows) ;
/*
id: 21
intern_schoolbase_id: 1
modifiedat: "2021-03-16T19:41:25.620Z"
modifiedby: "Hans"
note: "int"
note_status: "0_1"
schoolcode: "CURSYS"
studentsubject_id: 129
attachments: [{id: 2, attachment: "aarst1.png", contenttype: null}]
*/

// hide loader
        const el_ModNote_loader = document.getElementById("id_ModNote_loader");
        add_or_remove_class(el_ModNote_loader, cls_hide, true);

// reset notes_container
        el_ModNote_notes_container.innerText = null;

        if(note_rows && note_rows.length){
            for (let i = 0, row; row = note_rows[i]; i++) {
                const note_text = (row.note) ? row.note : "";
                const note_len = (note_text) ? note_text.length : 0;
                const modified_dateJS = parse_dateJS_from_dateISO(row.modifiedat);
                const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
                let modified_by = (row.sch_abbrev) ? row.sch_abbrev + " - " : "";
                modified_by += (row.modifiedby) ? row.modifiedby : "-";
                const mod_text = modified_by + ", " + modified_date_formatted + ":"

                const note_icon = (row.note_status) ? "note_" + row.note_status : "note_0_1";

                const numberOfLineBreaks = (note_text.match(/\n/g)||[]).length;
                let numberOfLines = 1 + numberOfLineBreaks;
                if (note_len > 3 * 75 ){
                    if (numberOfLines <= 3 ) {numberOfLines = 3 + 1}
                } else if (note_len > 2 * 75){
                    if (numberOfLines <= 2) {numberOfLines = 2 + 1}
                } else if (note_len > 1 * 75){
                    if (numberOfLines <= 1) {numberOfLines = 1 + 1}
                }

        // --- create div element 'ss_note_container'
                const el_note_container = document.createElement("div");
                el_note_container.classList.add("ss_note_container");
                el_ModNote_notes_container.appendChild(el_note_container);

        // --- create div element 'ss_note_titlebar' --------------------------------------
                    const el_note_titlebar = document.createElement("div");
                    el_note_titlebar.classList.add("ss_note_titlebar");
                    el_note_container.appendChild(el_note_titlebar);
            // --- create div element 'ss_note_icon_modby'
                        const el_note_icon_modby = document.createElement("div");
                        el_note_icon_modby.classList.add("ss_note_icon_modby");
                        el_note_titlebar.appendChild(el_note_icon_modby);
            // --- create icon element
                            const el_icon_modby = document.createElement("div");
                            el_icon_modby.classList.add(note_icon);
                            el_note_icon_modby.appendChild(el_icon_modby);
            // --- create small modby text element
                            const el_modby = document.createElement("small");
                            el_modby.innerText = mod_text;
                            el_note_icon_modby.appendChild(el_modby);

            // --- create div element 'note_textarea' --------------------------------------
                    const el_note_textarea = document.createElement("div");
                    el_note_textarea.classList.add("ss_note_textarea");
                    el_note_container.appendChild(el_note_textarea);

            // --- create textarea element
                        const el_textarea = document.createElement("textarea");
                        el_textarea.classList.add("ss_note_btn_attment");
                        el_textarea.setAttribute("rows", numberOfLines);
                        el_textarea.setAttribute("readonly", "true");
                        el_textarea.classList.add("form-control", "tsa_textarea_resize");
                        el_textarea.value = note_text
                        el_note_textarea.appendChild(el_textarea);

// loop through attachments
                if ("attachments" in row && row.attachments.length){
                    const att_rows = row.attachments;
                    for (let i = 0, att_row; att_row = att_rows[i]; i++) {
                         const att_id = att_row.id;
                         const att_name = (att_row.file_name) ? att_row.file_name : loc.Attachment;
                         const att_url = (att_row.url) ? att_row.url : null;
                        if (att_id){
        // --- create div element 'ss_note_attachment' --------------------------------------
                            const el_note_attachment = document.createElement("div");
                            el_note_attachment.classList.add("ss_note_titlebar");
                            el_note_container.appendChild(el_note_attachment);
                    // --- create div element 'ss_note_btn_attment'
                                const el_note_btn_attment = document.createElement("div");
                                el_note_btn_attment.classList.add("ss_note_btn_attment");
                                el_note_attachment.appendChild(el_note_btn_attment);
                    // --- create icon element
                                    const el_icon_attment = document.createElement("div");
                                    el_icon_attment.classList.add("note_1_8");
                                    el_note_btn_attment.appendChild(el_icon_attment);
                            // --- create href
                                    const el_attment = document.createElement("a");
                                    el_attment.innerText = att_name;
                                    el_attment.setAttribute("href", att_url)
                                    el_attment.target = "_blank";
                                    el_note_btn_attment.appendChild(el_attment);

                        }  //  if (att_id){
                    }  // for (let i = 0, att_row; att_row = att_rows[i]; i++) {
                }  // if ("attachments" in row && row.attachments.length){

            }
        }
    }  // ModNote_FillNotes

//###########################################################################
// +++++++++++++++++ REFRESH DATA ROWS ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataRowsAfterUploadFromExcel  ================ PR2021-07-20
    function RefreshDataRowsAfterUploadFromExcel(response) {
        console.log(" --- RefreshDataRowsAfterUploadFromExcel  ---");
        console.log( "response", response);
        const is_test = (!!response && !!response.is_test);
        console.log( "is_test", is_test);

        if(!is_test && response && "updated_grade_rows" in response) {
            //RefreshDataRows("grade", response.updated_grade_rows, grade_rows, true)  // true = update

            //DownloadValidationStatusNotes();
        }
        if(!is_test) {
            const datalist_request = {
                setting: {page: "page_grade"},
                grade_rows: {cur_dep_only: true}
            };
            DatalistDownload(datalist_request);
        };
    };  //  RefreshDataRowsAfterUploadFromExcel


//=========  RefreshDataRows  ================ PR2020-08-16 PR2020-09-30, PR2021-05-01 PR2021-09-20 PR2022-03-03
    function RefreshDataRows(tblName, update_rows, data_rows, is_update, skip_show_ok) {
        console.log(" --- RefreshDataRows  ---");
        console.log("is_update", is_update);
        console.log("update_rows", update_rows);

        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length
        if (update_rows && update_rows.length ) {
            const field_setting = field_settings[selected_btn];
            for (let i = 0, update_dict; update_dict = update_rows[i]; i++) {
                RefreshDatarowItem(tblName, field_setting, update_dict, data_rows, skip_show_ok);
            }
        } else if (!is_update) {
            // empty the data_rows when update_rows is empty PR2021-01-13 debug forgot to empty data_rows
            // PR2021-03-13 debug. Don't empty de data_rows when is update. Returns [] when no changes made
           data_rows = [];
        }
    }  //  RefreshDataRows

//=========  RefreshDatarowItem  ================ PR2020-08-16 PR2020-09-30 PR2021-09-20 PR2022-03-03
    function RefreshDatarowItem(tblName, field_setting, update_dict, data_rows, skip_show_ok) {
        console.log(" --- RefreshDatarowItem  ---");
        //console.log("tblName", tblName);
        //console.log("field_setting", field_setting);
        //console.log("update_dict", update_dict);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

// ---  get list of columns that are not updated because of errors
            const error_columns = (update_dict.err_fields) ? update_dict.err_fields : [];
    //console.log("error_columns", error_columns);

// ---  update or add update_dict in subject_map
            let updated_columns = [];

// ++++ created ++++
            // grades cannot be created on this page
            // PR2022-02-19 wrong: when uploading exemptioon it creates new grades
// ++++ deleted ++++
            // grades cannot be deleted on this page

// +++ get existing data_dict from data_rows. data_rows is ordered by grade.id'
            const grade_pk = update_dict.id;
            const data_dict = get_gradedict_by_gradepk(grade_pk);
    console.log("data_dict", data_dict);

// ---  create list of updated fields
            if(!isEmpty(data_dict)){
                for (const [key, new_value] of Object.entries(update_dict)) {
                    const mapped_key = (key === "se_blocked") ? "se_status" :
                                        (key === "sr_blocked") ? "sr_status" :
                                        (key === "pe_blocked") ? "pe_status" :
                                        (key === "ce_blocked") ? "ce_status" : key;

                    if (mapped_key in data_dict){
                        if (new_value !== data_dict[mapped_key]) {
                            updated_columns.push(mapped_key)

        // ---  put updated map_dict back in data_map
                        if(key in data_dict){
                            data_dict[key] = update_dict[key];
                        };

                }}};
    console.log("updated_columns", updated_columns);


        // ---  make update in tblRow
                const tblRow = document.getElementById(data_dict.mapid);
                // note: when updated_columns is empty, then updated_columns is still true.
                // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
                if(tblRow && (updated_columns.length || error_columns.length)){
        // loop through cells of row
                    for (let i = 1, el_fldName, td, el; td = tblRow.cells[i]; i++) {
                        if (td){
                            el = td.children[0];
                            if(el){
                                el_fldName = get_attr_from_el(el, "data-field")
    console.log(",,,,,,,,,,,,el_fldName", el_fldName);
                                const is_updated_field = updated_columns.includes(el_fldName);
                                const is_err_field = error_columns.includes(el_fldName);
    console.log(",,,,,,,,,,,,is_updated_field", el_fldName);
        // update field and make field green when field name is in updated_columns
                                if(is_updated_field){
                                    UpdateField(el, update_dict);
                                    if(!skip_show_ok){ShowOkElement(el)};
                                } else if( is_err_field){
        // make field red when error and reset old value after 2 seconds
                                    reset_element_with_errorclass(el, update_dict)
                                }
                            }
                        }
                    }  //  for (let i = 1, el_fldName, td
                 }  //  if(tblRow && (updated_columns.length || error_columns.length)){
            }  //  if(!isEmpty(data_dict))
        }  //  if(!isEmpty(update_dict)){
    };  // RefreshDatarowItem

//========= get_gradedict_by_gradepk =============  PR2021-09-20
    function get_gradedict_by_gradepk(grade_pk) {
        //console.log( " ==== get_gradedict_by_gradepk ====");
        const [middle_index, found_dict, compare] = b_recursive_integer_lookup(grade_rows, "id", grade_pk);
        return  found_dict;
    };  // get_gradedict_by_gradepk

//========= get_datadict_by_el =============  PR2021-09-20
    function get_datadict_by_el(el) {
        //console.log( " ==== get_datadict_by_el ====");
        const tblRow = t_get_tablerow_selected(el);
        const grade_pk = get_attr_from_el_int(tblRow, "data-pk")
        const [middle_index, found_dict, compare] = b_recursive_integer_lookup(grade_rows, "id", grade_pk);
        return  found_dict;
    };  // get_datadict_by_el

//=========  fill_data_list  ================ PR2020-10-07
    function fill_data_list(data_rows) {
        //console.log(" --- fill_data_list  ---");
        let data_list = [];
        if (data_rows) {
            for (let i = 0, row; row = data_rows[i]; i++) {
                data_list[row.id] = row.abbrev;
            }
        }
        return data_list
    }  //  fill_data_list


//=========  reset_element_with_errorclass  ================ PR2021-09-20
    function reset_element_with_errorclass(el_input, update_dict) {
        // make field red when error and reset old value after 2 seconds
        const err_class = "border_bg_invalid";
        el_input.classList.add(err_class);
        setTimeout(function (){
            el_input.classList.remove(err_class);
            UpdateField(el_input, update_dict);
        }, 2000);
    }  //  reset_element_with_errorclass
//###########################################################################
// +++++++++++++++++ FILTER TABLE ROWS ++++++++++++++++++++++++++++++++++++++

//========= HandleFilterKeyup  ================= PR2021-05-12
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
            t_Filter_TableRows(tblBody_datatable, filter_dict, selected, loc.Subject, loc.Subjects);
        }
    }; // function HandleFilterKeyup


//========= HandleFilterToggle  =============== PR2020-07-21 PR2020-09-14 PR2021-03-23 PR2022-03-09
    function HandleFilterToggle(el_input) {
        console.log( "===== HandleFilterToggle  ========= ");
        //console.log( "el_input", el_input);

    // - get col_index and filter_tag from  el_input
        // PR2021-05-30 debug: use cellIndex instead of attribute data-colindex,
        // because data-colindex goes wrong with hidden columns
        // was:  const col_index = get_attr_from_el(el_input, "data-colindex")
        const col_index = el_input.parentNode.cellIndex;

    // - get filter_tag from  el_input
        const filter_tag = get_attr_from_el(el_input, "data-filtertag");
        const field_name = get_attr_from_el(el_input, "data-field");
        const is_status_field = (field_name && field_name.includes("status"))

    console.log( "col_index", col_index);
    console.log( "filter_tag", filter_tag);
    console.log( "field_name", field_name);
    console.log( "is_status_field", is_status_field);

    // - get current value of filter from filter_dict, set to '0' if filter doesn't exist yet
        const filter_array = (col_index in filter_dict) ? filter_dict[col_index] : [];
        const filter_value = (filter_array[1]) ? filter_array[1] : "0";

    console.log( "filter_array", filter_array);
    console.log( "filter_value", field_name);

        let new_value = "0", icon_class = "tickmark_0_0", title = "";
        if(filter_tag === "toggle") {
            // default filter triple '0'; is show all, '1' is show tickmark, '2' is show without tickmark
// - toggle filter value
            new_value = (filter_value === "2") ? "0" : (filter_value === "1") ? "2" : "1";
    console.log( "new_value", new_value);

// - get new icon_class
            if (field_name === "note_status"){
                icon_class = (new_value === "2") ? "tickmark_2_1" : (new_value === "1") ? "note_0_1" : "tickmark_0_0";

            } else if (is_status_field){
                icon_class = (new_value === "2") ? "diamond_3_3" : (new_value === "1") ? "diamond_0_0" : "tickmark_0_0";
                title = (new_value === "2") ? loc.Show_fully_approved : (new_value === "1") ?loc.Show_not_fully_approved : "";
            };
        };
        el_input.className = icon_class;
        el_input.title = title
    console.log( "icon_class", icon_class);

// - put new filter value in filter_dict
        filter_dict[col_index] = [filter_tag, new_value]
    console.log( "filter_dict", filter_dict);

        t_Filter_TableRows(tblBody_datatable, filter_dict, selected, loc.Subject, loc.Subjects);

    };  // HandleFilterToggle


//========= ResetFilterRows  ====================================
    function ResetFilterRows() {  // PR2019-10-26 PR2020-06-20 PR2022-01-26
        console.log( "===== ResetFilterRows  ========= ");
        console.log( "filter_dict", filter_dict);

        setting_dict.sel_student_pk = null;
        setting_dict.sel_student_name = null;

        b_clear_dict(filter_dict);

        t_Filter_TableRows(tblBody_datatable, filter_dict, selected, loc.Subject, loc.Subjects);

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
                                };
                                el_icon.classList.add("tickmark_0_0")
                            };
                        };
                    };
                };
            };
       };
       FillTblRows();
    }  // function ResetFilterRows

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL SELECT EXAMYEAR OR DEPARTMENT ++++++++++++++++++++
// functions are in table.js, except for MSED_Response

//=========  MSED_Response  ================ PR2020-12-18  PR2021-05-10
    function MSED_Response(new_setting) {
        //console.log( "===== MSED_Response ========= ");

// ---  upload new selected_pk
        new_setting.page = setting_dict.sel_page;
// also retrieve the tables that have been changed because of the change in examyear / dep
        const datalist_request = {
                setting: new_setting,
                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},
                subject_rows: {get: true},
                cluster_rows: {cur_dep_only: true},

                student_rows: {get: true},
                studentsubject_rows: {get: true},
                grade_rows: {cur_dep_only: true}
            };
        DatalistDownload(datalist_request);
    }  // MSED_Response

//=========  MSSSubjStud_Response  ================ PR2021-01-23 PR2021-02-05 PR2021-07-26
    function MSSSubjStud_Response(mode, selected_dict, sel_pk_int) {
        console.log( "===== MSSSubjStud_Response ========= ");
        console.log( "mode", mode);
        console.log( "selected_dict", selected_dict);
        console.log( "sel_pk_int", sel_pk_int, typeof sel_pk_int);
        // mode = "subject" or "cluster" or "student"

        if(sel_pk_int === -1) { sel_pk_int = null};

        const selected_pk_dict = {};
        if (mode === "subject") {
            // Note: when tblName = subject: sel_pk_int = subject_pk

            setting_dict.sel_subject_pk = sel_pk_int;
            setting_dict.sel_subject_name = (selected_dict && selected_dict.name) ? selected_dict.name : null;

            if(sel_pk_int) {
                setting_dict.sel_cluster_pk = null;
                setting_dict.sel_cluster_name = null;
                setting_dict.sel_student_pk = null;
                setting_dict.sel_student_name = null;
            };

            selected_pk_dict.sel_subject_pk = sel_pk_int;
            if(sel_pk_int) {selected_pk_dict.sel_student_pk = null};

    // ---  upload new setting
            const upload_dict = {selected_pk: {
                sel_subject_pk: setting_dict.sel_subject_pk,
                sel_student_pk: null,
                sel_cluster_pk: null}};
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);

        } else if (mode === "cluster") {
            setting_dict.sel_cluster_pk = sel_pk_int;
            setting_dict.sel_cluster_name = (selected_dict && selected_dict.name) ? selected_dict.name : null;

            // when selecting cluster: also set subject to the subject of this cluster
            setting_dict.sel_subject_pk =  (selected_dict && selected_dict.subject_id) ? selected_dict.subject_id : null;
            setting_dict.sel_subject_name = (selected_dict && selected_dict.subj_name) ? selected_dict.subj_name : null;

            if(sel_pk_int) {
                setting_dict.sel_student_pk = null;
                setting_dict.sel_student_name = null;
            };
    // ---  upload new setting
            const upload_dict = {selected_pk: {
                sel_cluster_pk: setting_dict.sel_cluster_pk,
                sel_student_pk: null,
                sel_subject_pk: null}};
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);

        } else if (mode === "student") {
            setting_dict.sel_student_pk = sel_pk_int;
            setting_dict.sel_student_name = (selected_dict && selected_dict.fullname) ? selected_dict.fullname : null;
            if(sel_pk_int) {
                setting_dict.sel_subject_pk = null;
                setting_dict.sel_subject_name = null;
                setting_dict.sel_cluster_pk = null;
                setting_dict.sel_cluster_name = null
            };
    // ---  upload new setting
            const upload_dict = {selected_pk: {
                sel_student_pk: setting_dict.sel_student_pk,
                sel_subject_pk: null,
                sel_cluster_pk: null}};
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);
        };
        console.log("setting_dict", setting_dict);
        UpdateHeader();

        SBR_display_subject_cluster_student();

        FillTblRows();
        //HandleBtnSelect(null, true)  // true = skip_upload
        // also calls: FillTblRows(), UpdateHeader()

    }  // MSSSubjStud_Response


//=========  MSSSS_Response  ================ PR2021-01-23 PR2021-02-05 PR2021-07-26
    function MSSSS_Response(tblName, selected_dict, selected_pk) {
        console.log( "===== MSSSS_Response ========= ");
        console.log( "tblName", tblName);
        console.log( "selected_pk", selected_pk, typeof selected_pk);
        console.log( "selected_dict", selected_dict);


// ---  upload new setting
        if(selected_pk === -1) { selected_pk = null};
        const upload_dict = {};
        const selected_pk_dict = {sel_student_pk: selected_pk};
        selected_pk_dict["sel_" + tblName + "_pk"] = selected_pk;
        let new_selected_btn = null;

        if (tblName === "school") {
        // Note: when tblName = school: selected_pk = schoolbase_pk

// ---  upload new setting and refresh page
        const datalist_request = {
                setting: {page: "page_grade",
                        sel_schoolbase_pk: selected_pk
                    },
                school_rows: {get: true},
                department_rows: {get: true},
                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},
                subject_rows: {get: true},
                cluster_rows: {cur_dep_only: true},

                student_rows: {get: true},
                studentsubject_rows: {get: true},
                grade_rows: {get: true}
            };

            DatalistDownload(datalist_request);

        } else if (tblName === "subject") {
        // Note: when tblName = subject: selected_pk = subject_pk
            setting_dict.sel_subject_pk = selected_pk;

    // reset selected student when subject is selected, in setting_dict and upload_dict
            if(selected_pk){
                selected_pk_dict.sel_student_pk = null;
                setting_dict.sel_student_pk = null;
                setting_dict.sel_student_name = null;
            }

        } else if (tblName === "student") {
            setting_dict.sel_student_pk = selected_pk;
            //setting_dict.sel_student_name = selected_name;
    // reset selected subject when student is selected, in setting_dict and upload_dict
            if(selected_pk){
                selected_pk_dict.sel_subject_pk = null;
                setting_dict.sel_subject_pk = null;
            }
        }

        if (tblName === "school") {

        } else {
            b_UploadSettings ({selected_pk: selected_pk_dict}, urls.url_usersetting_upload);

    // fill datatable
            FillTblRows();
            SBR_display_subject_cluster_student();
    // --- update header text - comes after MSSSS_display_in_sbr
            UpdateHeader();

        }
    }  // MSSSS_Response

//========= MSSSS_display_in_sbr_reset  ====================================
    function MSSSS_display_in_sbr_reset() {
        //console.log( "===== MSSSS_display_in_sbr_reset  ========= ");

        t_MSSSS_display_in_sbr("subject");
        t_MSSSS_display_in_sbr("student");
        t_MSSSS_display_in_sbr("cluster");

    }; // MSSSS_display_in_sbr_reset

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


//>>>>>>>>>> NOT IN USE YET >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
//========= ModalStatusOpen====================================
    function ModalStatusOpen (el_input) {
       //console.log("===  ModalStatusOpen  =====") ;
       //console.log("el_input", el_input) ;
        // PERMISSIONS: only hrman can unlock shifts, supervisor can only block shifts PR2020-08-05
        // TODO correct
       // return false
        mod_status_dict = {};
        let permit_lock_rows = true;
        let permit_unlock_rows = true;
// get tr_selected, fldName and grade_dict
        let tr_selected = t_get_tablerow_selected(el_input)
        const fldName = get_attr_from_el(el_input, "data-field");
        //console.log("fldName", fldName) ;

// get status from field status, not from confirm start/end
        const grade_dict = get_datadict_by_el(el_input);
        //console.log("grade_dict", grade_dict) ;

        const status_sum = grade_dict.ispublished_ce;

        let btn_save_text = loc.Confirm;

        let time_col_index = 0
        let is_fldName_status = false;

        let field_is_locked = (grade_dict.stat_locked || grade_dict.stat_pay_locked || grade_dict.stat_inv_locked )

        const allow_lock_status = (!field_is_locked);
// only HR-man can unlock, only when not stat_pay_locked and not stat_inv_locked
        const allow_unlock_status = (!grade_dict.stat_pay_locked && !grade_dict.stat_inv_locked && permit_unlock_rows);

        let field_is_confirmed = false;
        if (fldName === "stat_start_conf" && grade_dict.stat_start_conf) {
            field_is_locked = true;
            field_is_confirmed = true;
        } else if (fldName === "stat_start_end" && grade_dict.stat_start_end) {
            field_is_locked = true;
            field_is_confirmed = true;
        }

        const child_el = el_input.children[0];

        const col_index = (fldName === "stat_start_conf") ? 5 : 7;
        const time_el = tr_selected.cells[col_index].children[0]
        const has_overlap = (time_el.classList.contains("border_bg_invalid"));

        //const has_overlap = ("overlap" in time_fielddict)
        const has_no_employee = (!grade_dict.employee_id)
        const has_no_order = (!grade_dict.o_id)
        const has_no_time = ( (fldName === "stat_start_conf" && !grade_dict.offsetstart) || (fldName === "stat_end_conf" && !grade_dict.offsetend) )

       //console.log("has_no_order", has_no_order) ;
// put values in mod_status_dict
        mod_status_dict = {
            emplhour_pk: grade_dict.id,
            emplhour_ppk: grade_dict.comp_id,
            field: grade_dict.fldName,
            status_sum: grade_dict.status,
            locked: field_is_locked,
            confirmed: field_is_confirmed
        }

        let header_text = null;
        if (fldName === "stat_start_conf") {
            header_text = (field_is_confirmed) ? loc.Undo_confirmation : loc.Confirm_start_of_shift;
            btn_save_text = (field_is_confirmed) ? loc.Undo : loc.Confirm;

            time_col_index = 5
        } else if (fldName === "stat_start_end") {
            header_text = (field_is_confirmed) ? loc.Undo_confirmation : loc.Confirm_end_of_shift;
            btn_save_text = (field_is_confirmed) ? loc.Undo : loc.Confirm;
            time_col_index = 7
        } else if (fldName === "status") {
            is_fldName_status = true;

            if (grade_dict.stat_locked) {
                header_text = loc.Unlock + " " + loc.Shift.toLowerCase();
                btn_save_text = loc.Unlock;
            } else {
                header_text = loc.Lock + " " + loc.Shift.toLowerCase();
                btn_save_text = loc.Lock;
            }
            time_col_index = 9
        }


// don't open modal when locked and confirmstart / confirmend
        let allow_open = false;
        if (is_fldName_status){
            allow_open = (grade_dict.stat_locked) ? permit_unlock_rows : permit_lock_rows;
        } else {
            // PERMITS confirm field can only be opened by supervisor
            if (permit_lock_rows){
                // cannot open confirm field when time field is locked
                if (!field_is_locked){
                // when field is not confirmed: can only confirm when has employee and has no overlap:
                    if (!field_is_confirmed && !has_overlap) {
                        allow_open = true;
                    } else {
                    // when field is not confirmed: can undo,
                    // also when has_overlap or has_no_employee (in case not allowing confirmation has gone wrong)
                        allow_open = true;
                    }
                }
            }
        }
        //console.log("allow_open", allow_open)

        if (allow_open) {

            el_mod_status_header.innerText = header_text
            let time_label = null, time_display = null;
            if(fldName === "stat_start_conf"){
                time_label = loc.Start_time + ":";
                time_display = format_time_from_offset_JSvanilla( loc, grade_dict.rosterdate, grade_dict.offsetstart, true, false, false)
            } else if (fldName === "stat_start_end") {
                time_label = loc.End_time + ":";
                time_display = format_time_from_offset_JSvanilla( loc, grade_dict.rosterdate, grade_dict.offsetend, true, false, false)
            }
            let emplhour_pk = null;
            ModalStatus_FillNotes (emplhour_pk)


            /*
            document.getElementById("id_mod_status_time_label").innerText = time_label;
            document.getElementById("id_mod_status_time").value = time_display;

            document.getElementById("id_mod_status_order").innerText = grade_dict.c_o_code;
            document.getElementById("id_mod_status_employee").innerText = grade_dict.employeecode;
            document.getElementById("id_mod_status_shift").innerText = (grade_dict.shiftcode);
            */

            let msg01_txt = null;
            if(has_no_order){
                msg01_txt = loc.You_must_first_select + loc.an_order + loc.select_before_confirm_shift;
            } else if(has_no_employee && !is_fldName_status){
                msg01_txt = loc.You_must_first_select + loc.an_employee + loc.select_before_confirm_shift;
            } else if(has_overlap && !is_fldName_status){
                msg01_txt = loc.You_cannot_confirm_overlapping_shift;
            } else if(has_no_time && !is_fldName_status){
                msg01_txt = loc.You_must_first_enter +
                             ( (fldName === "stat_start_conf") ? loc.a_starttime : loc.an_endtime ) +
                             loc.enter_before_confirm_shift;
            }

           //console.log("is_fldName_status", is_fldName_status) ;
           //console.log("allow_lock_status", allow_lock_status) ;

            let show_confirm_box = false;
            if (fldName === "status" && allow_lock_status) {
                show_confirm_box = true;
            } else {
                if(field_is_confirmed) {
                    // when field is confirmed: can undo
                    show_confirm_box = true;
                } else if (!msg01_txt){
                    show_confirm_box = true;
                }
            }
            if(show_confirm_box) {
                el_mod_status_btn_save.innerText = btn_save_text;
    // ---  show modal
                $("#id_mod_status").modal({backdrop: true});
            } else {

// ---  show modal confirm with message 'First select employee'
                document.getElementById("id_modconfirm_header").innerText = loc.Confirm + " " + loc.Shift.toLowerCase();
                document.getElementById("id_modconfirm_msg01").innerText = msg01_txt;
                document.getElementById("id_modconfirm_msg02").innerText = null;
                document.getElementById("id_modconfirm_msg03").innerText = null;

                add_or_remove_class (el_confirm_btn_save, cls_hide, true) // args: el, classname, is_add
                el_confirm_btn_cancel.innerText = loc.Close;
                setTimeout(function() {el_confirm_btn_cancel.focus()}, 50);

                 $("#id_mod_confirm").modal({backdrop: true});
             }  // if (allow_lock_status) || (!field_text) {
        };  // if (allow_open) {
    }; // function ModalStatusOpen

//=========  ModalStatusSave  ================ PR2019-07-11
    function ModalStatusSave() {
        //console.log("===  ModalStatusSave =========");

        // put values in el_body
        let el_body = document.getElementById("id_mod_status_body")
        //const tblName = get_attr_from_el(el_body, "data-table")
        const data_ppk = get_attr_from_el(el_body, "data-ppk")
        const data_field = get_attr_from_el(el_body, "data-field")
        const field_is_confirmed = (get_attr_from_el(el_body, "data-confirmed", false) === "true")
        const status_value = get_attr_from_el_int(el_body, "data-value")

        //console.log("el_body: ", el_body);
        //console.log("field_is_confirmed: ", field_is_confirmed);
        //console.log("data_field: ", data_field);

        const data_pk = get_attr_from_el(el_body, "data-pk")
        let tr_changed = document.getElementById(data_pk)

        const id_dict = get_iddict_from_element(el_body);
        // period_datefirst and period_datelast necessary for check_emplhour_overlap PR2020-07-22
        let upload_dict = {id: id_dict,
                            //period_datefirst: selected_period.period_datefirst,
                            //period_datelast: selected_period.period_datelast
                            }

        //console.log("---------------status_value: ", status_value);
        //console.log("---------------data_field: ", data_field);
        //console.log("---------------field_is_confirmed: ", field_is_confirmed, typeof field_is_confirmed);
        let status_dict = {}, confirmstart_dict = null, confirmend_dict = null;
        if(data_field === "confirmstart"){
            confirmstart_dict  = {"value": field_is_confirmed, "update": true};
            if (field_is_confirmed) {
                status_dict = {"value": 2, "remove": true, "update": true}  // STATUS_004_START_CONFIRMED = 2
                //console.log("confirmstart field_is_confirmed ", status_dict);
            } else {
                status_dict = {"value": 2, "update": true}  // STATUS_004_START_CONFIRMED = 2
                //console.log("confirmstart field_is_NOT confirmed ", status_dict);
            }
        } else if(data_field === "confirmend"){
            confirmend_dict  = {"value": field_is_confirmed, "update": true};
            if (field_is_confirmed) {
                 status_dict = {"value": 4, "remove": true, "update": true}  // STATUS_016_END_CONFIRMED = 4
                //console.log("confirmend field_is_confirmed ", status_dict);
            } else {
                 status_dict = {"value": 4, "update": true}  // STATUS_016_END_CONFIRMED = 4
                //console.log("confirmend field_is_NOT_confirmed ", status_dict);
            }
        } else if(data_field === "status"){
            if(status_value >= 8){
                status_dict = {"value": 8, "remove": true, "update": true}  // STATUS_032_LOCKED = 8
                //console.log("status status_value >= 8 ", status_dict);
            } else {
                status_dict = {"value": 8, "update": true}   // STATUS_032_LOCKED = 8
                //console.log("status status_value < 8 ", status_dict);
            }
        }
        //console.log("---------------status_dict: ", status_dict);
        upload_dict["status"] = status_dict
        if(!!confirmstart_dict){
            upload_dict["confirmstart"] = confirmstart_dict
        }
        if(!!confirmend_dict){
            upload_dict["confirmend"] = confirmend_dict
        }

        $("#id_mod_status").modal("hide");

        if(!!upload_dict) {
            //console.log( "upload_dict", upload_dict);
            let parameters = {"upload": JSON.stringify(upload_dict)};

            let response = "";
            $.ajax({
                type: "POST",
                url: url_emplhour_upload,
                data: parameters,
                dataType:'json',
                success: function (response) {
                    //console.log( "response");
                    //console.log( response);

                    if ("item_update" in response) {
                        let item_dict =response["item_update"]
                        //const tblName = get_dict_value (item_dict, ["id", "table"], "")

                        UpdateTblRow(tr_changed, item_dict)
                    }
                },
                error: function (xhr, msg) {
                    console.log(msg + '\n' + xhr.responseText);
                }
            });
        }  //  if(!!new_item)
    }  // ModalStatusSave


//========= ModalStatus_FillNotes=====  NOT IN USE YET ========= PR2020-10-15
    function ModalStatus_FillNotes (emplhour_pk) {
        //console.log("===  ModalStatus_FillNotes  =====") ;
        el_mod_status_note_container.innerText = null;
        let studentsubjectnote_map = []
        const note = get_dict_value(studentsubjectnote_map, [emplhour_pk]);
        if(note){
            const len = note.ehn_id_agg.length;
            for (let i = 0; i < len; i++) {
                const note_text = (note.note_agg[i]) ? note.note_agg[i] : "";
                const note_len = (note_text) ? note_text.length : 0;
                const modified_dateJS = parse_dateJS_from_dateISO(note.modifiedat_agg[i]);
                const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
                const modified_by = (note.modifiedby_agg[i]) ? note.modifiedby_agg[i] : "-";
                const mod_text = modified_by + ", " + modified_date_formatted + ":"
        // --- create div element with note
                const el_div = document.createElement("div");
                el_div.classList.add("tsa_textarea_div");
                    const el_small = document.createElement("small");
                    el_small.classList.add("tsa_textarea_div");
                    el_small.innerText = mod_text;
                    el_div.appendChild(el_small);

                    const el_textarea = document.createElement("textarea");
                    const numberOfLineBreaks = (note_text.match(/\n/g)||[]).length;
                    let numberOfLines = 1 + numberOfLineBreaks;
                    if (note_len > 3 * 75 ){
                        if (numberOfLines <= 3 ) {numberOfLines = 3 + 1}
                    } else if (note_len > 2 * 75){
                        if (numberOfLines <= 2) {numberOfLines = 2 + 1}
                    } else if (note_len > 1 * 75){
                        if (numberOfLines <= 1) {numberOfLines = 1 + 1}
                    }

                    el_textarea.setAttribute("rows", numberOfLines);
                    el_textarea.setAttribute("readonly", "true");
                    el_textarea.classList.add("form-control", "tsa_textarea_resize", "tsa_tr_ok");
                    el_textarea.value = note_text
                    el_div.appendChild(el_textarea);
                el_mod_status_note_container.appendChild(el_div);
            }
        }

        // --- create input element for note, only when permit_edit_rows
        if(has_permit_add_notes){
            const el_div = document.createElement("div");
            el_div.classList.add("tsa_textarea_div");
            el_div.classList.add("tsa_textarea_div", "mt-4", );

                const el_textarea = document.createElement("textarea");
                el_textarea.id = "id_ModNote_input_note";
                el_textarea.setAttribute("rows", "4");
                el_textarea.classList.add("form-control", "tsa_textarea_resize", );
                el_textarea.placeholder = loc.Type_your_note_here + "..."
                el_div.appendChild(el_textarea);

            el_mod_status_note_container.appendChild(el_div);
        }

    }  // ModalStatus_FillNotes



//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

//========= ValidateGrade  =============== PR2020-12-20
    function ValidateGrade(loc, fldName, value, dict){
        //console.log(" --- ValidateGrade ---")
        //console.log("fldName", fldName, "value", value)
        //console.log("dict", dict)

        // PR2021-05-02 field "srgrade" added, TODO no validations yet
        const err_list = loc.grade_err_list
        const is_score = (["pescore", "cescore"].indexOf(fldName) > -1);
        const is_grade = (["segrade", "srgrade", "pegrade", "cegrade"].indexOf(fldName) > -1);
        const is_pe_or_ce = (["pescore", "pegrade", "cescore", "cegrade"].indexOf(fldName) > -1);
        //const is_se = (fldName in ["segrade", "srgrade"]);
        //console.log("is_score", is_score, "is_grade", is_grade)

// 1. reset output parameters
        let output_text = null, msg_html = null;

// 2. exit als strInputValue niet ingevuld (strMsgText = vbNullString, geen foutmelding)
        if(value){

// 3. exit als kandidaat is vergrendeld 'PR2016-03-27
            if (dict.ey_locked) { msg_html = err_list.examyear_locked} else
            if (dict.school_locked) { msg_html = err_list.school_locked} else
            if (dict.stud_locked) {msg_html = err_list.candidate_locked};
            if( (dict.se_blocked && fldName === "segrade") ||
                (dict.sr_blocked && fldName === "srgrade") ||
                (dict.pe_blocked && fldName in ["pescore", "pegrade"]) ||
                (dict.ce_blocked && fldName in ["cescore", "cegrade"]) ) {
                    msg_html = err_list.grade_locked;
            }
            if(!msg_html){
// 4. exit als dit vak bewijs van kennis heeft. Dan is invoer gegevens geblokkeerd. Ga naar Rpt_Ex6_BewijsKennis om Bewijs van Kennis te wissen. 'PR2017-01-04
        // PR2010-06-10 mail Lorraine Wieske: kan geen PE cjfers corrigeren. Weghalen
        //If KvHasBewijsKennis Then
        //    strMsgText = "Vak heeft Bewijs van Kennis en is daarom vergrendeld." & vbCrLf & "Ga naar Rapportages Ex6 om Bewijs van Kennis zo nodig te wissen."
// 5. exit als VakSchemaItemID niet ingevuld
        // not possible because of foreign key required

// 6. Corona: check if no_centralexam
                if (is_pe_or_ce) {
                    if(dict.no_centralexam) {
                        msg_html = err_list.no_ce_this_ey;
                    } else if(dict.no_thirdperiod) {
// 6. Corona: check if no_thirdperiod
                        msg_html = err_list.no_3rd_period;
                    }
                } else if(dict.is_combi){
// 6. Corona: reexamination not allowed for combination subjects, except when combi_reex_allowed
                    if([2, 3].indexOf(dict.examperiod) > -1) {
                        if(!combi_reex_allowed){
                            msg_html = err_list.reex_combi_notallowed;
                        }
                    }
                }
            }
            if(!msg_html){
// 6. afterCorona: check if exemption has no_centralexam,  PR2020-12-16
                // skip when iseveningstudent school or islexschool
                if(dict.examperiod === 4) {
                    if(is_pe_or_ce && dict.no_exemption_ce) {
                        if(!dict.iseveningstudent && !islexschool) {
                            msg_html = err_list.exemption_no_ce;
                        }
                    }
                }
            }
            if(!msg_html){
// 6. controleer Praktijkexamen 'PR2019-02-22 'PR2015-12-08
                //wordt ook ingesteld buiten deze functie, in Form_K_BL_Resultaten.Form_Current en Form_C_CL_Resultaten.Form_Current  'PR2016-03-04
                if (fldName === "pegrade") {
                    if(dict.no_practexam) {
                        msg_html = err_list.no_pe_examyear;
                    } else if (!dict.has_practexam) {
                        msg_html = err_list.subject_no_pe;
                    }
                }
            }

// 7. controleer Herexamen 'PR2015-12-13  NOT NECESSARY
            /*
            'PR2019-01-16 KvHasVrst kan alleen als conExamen01_SE of conExamen02_CE
            If bytSoortExamen = conExamen04_HER Then
                If Not booIsImportCijfers Then 'PR2016-04-30 toegevoegd. Debug: import her werd overgeslagen vanwege deze check
                    If Not KvIsHerTv02 Then
                        'PR2020-05-15 Corona: "herkansing" ipv "herexamenvak"
                        strMsgText = IIf(pblAfd.IsCorona, "Dit is geen herkansing.", "Dit is geen herexamenvak.")
            If bytSoortExamen = conExamen05_HerTv03 Then 'PR2019-02-08
                If Not booIsImportCijfers Then  'PR2016-04-30 toegevoegd. Debug: import her werd overgeslagen vanwege deze check
                    If Not KvIsHerTv03 Then
                        strMsgText = "Dit is geen herexamenvak van het 3e tijdvak."
                    ElseIf pblAfd.IsCorona Then
                        strMsgText = "Er is dit examenjaar geen 3e tijdvak."
            */

            if(!msg_html){
// 8. controleer ce cijfer van combivak
                // 'PR2019-05-03 keuze-combi weer uitgeschakeld. Was:   Or KvIsKeuzeCombiVak Then 'PR2016-05-30 KeuzeCombi toegevoegd. Was: If VsiIsCombinatieVak Then
                if (is_pe_or_ce){
                    if(dict.is_combi){
            // 6. reexamination not allowed for combination subjects, except when Corona
                        if(dict.examperiod === 1) {
                            const caption = (fldName ==="pescore") ? "Praktijkscore" :
                                (fldName ==="cescore") ? "CE-score" :
                                (fldName ==="pegrade") ? "Praktijkcijfer" :
                                (fldName ==="cegrade") ? "CE-cijfer" : null;
                            msg_html = caption +  err_list.notallowed_in_combi;
                        } else if([2, 3].indexOf(dict.examperiod) > -1) {
                            // 'PR2020-05-15 Corona: herkansing wel mogelijk bij combivakken
                            if(!combi_reex_allowed){
                                msg_html = err_list.reex_notallowed_in_combi;
                            }
                        }
                    }
                }
            }
            if(!msg_html){
// 8. controleer weging
                if (fldName === "segrade") {
                    if (!dict.weight_se) {msg_html = err_list.weightse_is_zero + "<br>" + err_list.cannot_enter_SE_grade};
                } else if (fldName === "srgrade") {
                    if (!dict.weight_se) {msg_html = err_list.weightse_is_zero + "<br>" + err_list.cannot_enter_SR_grade};
                } else if (fldName === "pegrade") {
                    if (!dict.weight_ce) {msg_html = err_list.weightce_is_zero + "<br>" + err_list.cannot_enter_PE_grade};
                } else if (fldName === "cegrade") {
                    if (!dict.weight_ce) {msg_html = err_list.weightce_is_zero + "<br>" + err_list.cannot_enter_CE_grade};
                } else if (fldName === "pescore") {
                    if (!dict.weight_ce) {msg_html = err_list.weightce_is_zero + "<br>" + err_list.cannot_enter_PE_score};
                } else if (fldName === "cescore") {
                    if (!dict.weight_ce) {msg_html = err_list.weightce_is_zero + "<br>" + err_list.cannot_enter_CE_score};
                };
            }
            if(!msg_html){
// A. SCORE
    // 1. controleer score PR2015-12-27 PR2016-01-03
                if (is_score){
                    // this is already covered by 'no_practexam' and 'no_centralexam'
                    // 'PR2020-05-15 Corona: geen scores
                    // strMsgText = "Er kunnen geen scores ingevuld worden in examenjaar " & ExkExamenjaar & "."

                    //PR2015-12-27 debug: vervang komma door punt, anders wordt komma genegeerd
                    const value_with_dots = value.replaceAll(",", ".");
                    const value_number = Number(value_with_dots);
                    if(!value_number){
                        msg_html = err_list.score_mustbe_number;
                    } else if (value_number < 0) {
                        msg_html = err_list.score_mustbe_gt0; // "Score moet een getal groter dan nul zijn."
                    } else if (value_number % 1 !== 0 ) {
                        // the remainder / modulus operator (%) returns the remainder after (integer) division.
                        msg_html = err_list.score_mustbe_wholenumber;
                    }
                    // TODO check if score is within scalelength of norm

                    if (! msg_html ) {output_text = value_number.toString()};
                //dict.scalelength_ce, dict.scalelength_pe, dict.scalelength_reex

                  //  If Not VsiLschaal = vbNullString Then
                  //      If IsNumeric(VsiLschaal) Then
                  //          If CCur(strInputValue) > CCur(VsiLschaal) Then
                  //              strMsgText = "Score moet kleiner of gelijk zijn aan " & IIf(VsiIsETEnorm, "max. score", "schaallengte") & " (" & VsiLschaal & ")."

//B. CIJFER
                } else if (is_grade){
                //1. exit als CijferType VoldoendeOnvoldoende is en inputcijfer niet booIsOvg is
               //         'PR2014-12-10 debug: gaf fout bij importeren cijfers omdat daar gebruik wordt gemaakt van pssVakSchema, niet van pblVakSchema
                //            'Was: If pblVakSchema.Vsi_CijferTypeID = conCijferType02_VoldoendeOnvoldoende Then 'PR 3 okt 09 was: Me.cijferTypeID = 2 Then

        //GRADETYPE_00_NONE = 0
        //GRADETYPE_01_NUMBER = 1
        //GRADETYPE_02_CHARACTER = 2  # goed / voldoende / onvoldoende
                    if(value)
                        if (dict.gradetype === 0) {//GRADETYPE_00_NONE = 0
                            msg_html = err_list.gradetype_no_value + "<br>" + err_list.cannot_enter_grade;//  "Cijfertype 'Geen cijfer'. Er kan geen cijfer ingevuld worden." 'PR2016-02-14
                        } else if (dict.gradetype === 2) {  //GRADETYPE_02_CHARACTER = 2  # goed / voldoende / onvoldoende
                            const value_lc = value.toLowerCase();
                            if (!["o", "v", "g"].includes(value_lc)){
                                msg_html = err_list.gradetype_ovg;  //"Het cijfer kan alleen g, v of o zijn."
                            } else {
                                output_text = value_lc;
                            }
                        } else if (dict.gradetype === 1) {  //GRADETYPE_01_NUMBER = 1
                            // GetNumberFromInputGrade wordt alleen gebruikt om te controleren of cijfer een correct getal is, strMsgText<>"" als fout   'PR2016-03-04
                            const arr = GetNumberFromInputGrade(loc, value);
                            output_text = arr[0];
                            msg_html = arr[1];
                        }
                    }  //   if (["segrade",
                }
        }  // if(value)

        //console.log("output_text", output_text)
        //console.log("msg_html", msg_html)
       return [output_text, msg_html]
    }  // ValidateGrade
////////////////////////////////////////////////

//========= get_column_is_hidden  ====== PR2022-04-17
    function get_column_is_hidden() {
    // ---  get list of hidden columns
        // copy col_hidden from mod_MCOL_dict.cols_hidden
        const col_hidden = [];
        b_copy_array_noduplicates(mod_MCOL_dict.cols_hidden, col_hidden)

// - hide columns that are not in use this examyear or this department PR2021-12-04
        // PR2021-12-04 use spread operator. from https://stackoverflow.com/questions/4842993/javascript-push-an-entire-list

        // hide srgrade when not sr_allowed
        if(!setting_dict.sr_allowed){col_hidden.push(...["srgrade", "sr_status"])};

        // hide pe or ce + pe when not allowed
        if(setting_dict.no_centralexam){
            col_hidden.push(...["pescore", "pe_status", "pegrade", "cescore", "ce_status", "cegrade"]);
        } else if(setting_dict.no_practexam){
            col_hidden.push(...["pescore", "pe_status", "pegrade"]);
        };

// - hide level when not level_req
        if(!setting_dict.sel_dep_level_req){col_hidden.push("lvl_abbrev")};

// - hide exemption_year when not evening or lex school
         if(!setting_dict.sel_school_iseveningschool && !setting_dict.sel_school_islexschool){col_hidden.push("exemption_year")};

// - show only columns of sel_examtype
        //console.log( "setting_dict.sel_examtype", setting_dict.sel_examtype);
        if(setting_dict.sel_examtype === "se"){
            col_hidden.push(...["srgrade", "sr_status",
                               "pescore", "pe_status", "pegrade",
                                "cescore", "ce_status", "cegrade", "finalgrade"]);
        } else if(setting_dict.sel_examtype === "sr"){
            col_hidden.push(...["segrade", "se_status",
                               "pescore", "pe_status", "pegrade",
                                "cescore", "ce_status", "cegrade", "finalgrade"]);
        } else if(setting_dict.sel_examtype === "pe"){
            col_hidden.push(...["segrade", "se_status", "srgrade", "sr_status",
                                    "cescore", "ce_status", "cegrade", "finalgrade"]);
        } else if(  ["ce", "reex", "reex03"].includes(setting_dict.sel_examtype)){
            col_hidden.push(...["segrade", "se_status", "srgrade", "sr_status",
                                   "pescore", "pe_status", "pegrade",
                                    "finalgrade"]);
        };
        //console.log( "col_hidden", col_hidden);
        return col_hidden;
    };


//========= GetNumberFromInputGrade  =============== PR2020-12-16
    function GetNumberFromInputGrade(loc, input_value){
        //console.log(" --- GetNumberFromInputGrade ---")
        //console.log("input_value", input_value)
        const err_list = loc.grade_err_list
        //Functie maakt getal van string 15 jan 07, 29 jan 12, 3 mei 13
        //string heeft formaat "5,6", "5.6", "56"  1 cijfer achter de komma, exit als Cijfer <= 0 of  > 100
        //Functie wordt aangeroepen door  CalcPassedFailed.Calculations, CalcEindcijfer, CalcEindcijfer_Cijfer, k_v_Calc02_Count 'PR2016-02-07 PR2016-04-16 PR2017-02-28
        //Functie wordt ook aangeroepen door Functions_ValidateValues.Validate_InputCijfer, alleen om te controleren of cijfer een correct getal is  'PR2016-03-04

        // zowel punt als komma zijn toegestaan als delimiter (delimiter wordt niet meer gebruikt in deze functie PR2016-03-04

        //NB: gebruikt geen Regional Settings meer. Andere benadering, omdat de functie CDbl in Access 2010 foutmelding geeft... PR 3 mei 13
        //PR2015-06-12 debug: rekenfout bij Double> omgezet in Currency. Was: GetNumericFromInputCijfer(ByVal strNumber As String) As Double en Dim crcNumber As Double
        //PR2019-03-28 strCaptionText toegevoegd voor Form_C_N_Normen
        //Functie maakt getal van gemidCSE PR2015-10-04
        //zowel punt als komma zijn toegestaan als delimiter
        //PR2016-03-04 debug HvD: LET OP REGIONAL SETTINGS: Access werkt met komma's bij Nederlandse setting. Opgelost door niet meer met decimalen te werken

// 1. reset output variables
        let output_text = 0, msg_err = null;

// 2. remove spaces before and after input_value
        const imput_trim = (input_value) ? input_value.trim() : null;

// 3. exit if imput_trim has no value, without msg_err
        if (imput_trim) {

// 5. vervang komma's door punten
            const input_with_dots = imput_trim.replaceAll(",", ".");

// 6. exit als strCijfer niet Numeric is
            if(!Number(input_with_dots)){
                msg_err = loc.Grade +  " '" + imput_trim + "' " + err_list.is_not_allowed + "<br>" +err_list.Grade_mustbe_between_1_10
            } else {

// 7. zet strCijfer om in Currency (crcCijfer is InputCijfer * 10 bv: 5,6 wordt 56 en .2 wordt 2
                let input_number = Number(input_with_dots);

// 8. replace '67' bij '6.7', only when it has no decimal places and is between 11 thru 99
                // the remainder / modulus operator (%) returns the remainder after (integer) division.
                if (input_number % 1 === 0  && input_number > 10  && input_number < 100  ) {
                    input_number = input_number / 10;
                }
            //console.log("input_number", input_number)

// 8. exit als crcCijfer < 10 of als  crcCijfer > 100
                // allowed numbers are: 1 thru 10, with 1 decimal
                 if(input_number < 1 || input_number > 10){
                     msg_err = loc.Grade +  " '" + imput_trim + "' " + err_list.is_not_allowed + "<br>" +err_list.Grade_mustbe_between_1_10
                } else {

// 10. exit als more than 1 digit after the dot.
                    // multiply by 10, get remainder after division by 1, check if remainder has value
                    // the remainder / modulus operator (%) returns the remainder after (integer) division.
                    if ((input_number * 10) % 1) {
                        msg_err = loc.Grade +  " '" + imput_trim + "' " + err_list.is_not_allowed + "<br>" +err_list.Grade_may_only_have_1_decimal
                    } else {
                        output_text = input_number.toString()
                        // replace dot by comma
                        output_text = output_text.replaceAll(".", ",");
                        // add ",0" if integer
                        if (!output_text.includes(",")){
                            output_text += ",0";
                        }
                    }
                }  // if(input_number < 0 || input_number > 10)
            }  // if(!Number(input_with_dots))
        } // if (imput_trim)

// 11.return array with output number and msg_err
        //console.log("output_text", output_text)
        //console.log("msg_err", msg_err)
        return [output_text, msg_err]
    }  // GetNumberFromInputGrade

//========= get_datarows_from_selectedBtn  ======== // PR2021-09-20
    function get_datarows_from_selectedBtn() {
        const data_rows = (selected_btn === "btn_published") ? published_rows : grade_rows;
        return data_rows;
    }

//========= get_tblName_from_selectedBtn  ======== // PR2021-01-22 PR2021-09-20
    function get_tblName_from_selectedBtn() {
        const tblName = (selected_btn === "btn_published") ? "published" : "grades";
        return tblName;
    }

})  // document.addEventListener('DOMContentLoaded', function()