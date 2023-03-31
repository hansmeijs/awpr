// PR2020-09-29 added

// PR2021-07-23  these variables are declared in base.js to make them global variables

//console.log("PAGE VARIABLES")

const field_settings = {};

//let school_rows = [];
let student_rows = [];
let studsubj_rows = [];
let grade_rows = [];

//let subject_rows = [];
// PR2023-01-24 was: let cluster_rows = [];
//const cluster_dictsNEW = {}; //PR2023-01-05 new approach, dict instead of sorted list

let schemeitem_rows = [];
let all_exam_rows = [];

document.addEventListener("DOMContentLoaded", function() {
    "use strict";

    selected = {
        grade_pk: null,
        grade_dict: {},
        item_count: 0
    };

// ---  get el_loader
    let el_loader = document.getElementById("id_loader");

// ---  check if user has permit to view this page. If not: el_loader does not exist PR2020-10-02
    const may_view_page = (!!el_loader)

    let mod_dict = {};
    const mod_MAG_dict = {};
    const mod_MSELEX_dict = {};
    const mod_MLINKSTUD_dict = {};

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
    urls.url_user_modmsg_hide = get_attr_from_el(el_data, "data-url_user_modmsg_hide");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    urls.url_usersetting_upload = get_attr_from_el(el_data, "data-url_usersetting_upload");
    urls.url_subject_upload = get_attr_from_el(el_data, "data-url_subject_upload");
    urls.url_grade_upload = get_attr_from_el(el_data, "data-url_grade_upload");

    urls.url_grade_approve = get_attr_from_el(el_data, "data-url_grade_approve");
    urls.url_grade_approve_single = get_attr_from_el(el_data, "data-url_grade_approve_single");
    urls.url_grade_submit_ex2 = get_attr_from_el(el_data, "data-url_grade_submit_ex2");
    urls.url_send_email_verifcode = get_attr_from_el(el_data, "data-url_send_email_verifcode");
    urls.url_grade_block = get_attr_from_el(el_data, "data-url_grade_block");

    urls.url_download_grade_icons = get_attr_from_el(el_data, "data-download_grade_icons_url");
    urls.url_grade_download_ex2 = get_attr_from_el(el_data, "data-url_grade_download_ex2");
    urls.url_grade_download_ex2a = get_attr_from_el(el_data, "data-url_grade_download_ex2a");
    urls.url_download_published = get_attr_from_el(el_data, "data-download_published_url");
    urls.url_studentsubjectnote_upload = get_attr_from_el(el_data, "data-url_studentsubjectnote_upload");
    urls.url_studentsubjectnote_download = get_attr_from_el(el_data, "data-studentsubjectnote_download_url");
    urls.url_noteattachment_download = get_attr_from_el(el_data, "data-noteattachment_download_url");

    urls.url_student_multiple_occurrences = get_attr_from_el(el_data, "data-url_student_multiple_occurrences");
    urls.url_student_linkstudent = get_attr_from_el(el_data, "data-url_student_linkstudent");
    urls.url_student_enter_exemptions = get_attr_from_el(el_data, "data-url_student_enter_exemptions");

    urls.url_exam_download_conversion_pdf = get_attr_from_el(el_data, "data-url_exam_download_conversion_pdf");
    // url_importdata_upload is stored in id_MIMP_data of modimport.html

    // variable 'mod_MCOL_dict.columns' is initialized in tables.js
    mod_MCOL_dict.columns.all = {
        examnumber: "Examnumber", lvl_abbrev: "Learning_path", sct_abbrev: "Sector", cluster_name: "Cluster", subj_name_nl: "Subject"
    };
    mod_MCOL_dict.columns.btn_exem = {exemption_year: "Exemption_year"};
    mod_MCOL_dict.columns.btn_ep_01 = {ce_exam_name: "Exam"};
    mod_MCOL_dict.columns.btn_reex = {ce_exam_name: "Exam"};
    mod_MCOL_dict.columns.btn_reex03 = {ce_exam_name: "Exam"};

// --- get field_settings
    const field_settings = {
        btn_exem: {field_names: ["select", "examnumber", "fullname",  "lvl_abbrev", "sct_abbrev",
                                  "cluster_name", "subj_code", "subj_name_nl", "exemption_year",
                                  // PR2023-02-20 this one includes approve exemptions, turned off for now:
                                  // "segrade", "se_status", "cegrade", "ce_status",
                                   "segrade", "cegrade",
                                   "finalgrade", "note_status"],
                    field_caption: ["", "Ex_nr", "Candidate", "Learningpath_twolines", "Sector",
                                    "Cluster", "Abbrev_subject_2lines", "Subject", "Exemption_year_twolines",
                                    "Exem_SE_twolines", "Exem_CE_twolines",// PR2023-02-20 was: "Exem_SE_twolines", "", "Exem_CE_twolines", "",
                                    "Exem_FINAL_twolines", ""],
                    field_tags: ["div", "div", "div", "div", "div",
                                "div", "div", "div", "div",
                                "input", "input", // PR2023-02-20 was: "input", "div", "input", "div",
                                "div", "div"],
                    filter_tags: ["text", "text","text", "text", "text",
                                    "text", "text", "text", "text",
                                    "text",  "text", // PR2023-02-20 was: "text", "status", "text", "status",
                                    "text", "text"],
                    field_width: ["020", "060", "240", "060", "060",
                                    "120", "075", "240", "100",
                                    "090", "090", // PR2023-02-20 was: "090", "020", "090", "020",
                                    "090", "032"],
                    field_align: ["c", "r", "l", "c", "c",
                                    "l", "c", "l", "c",
                                    "c", "c", "c", "c", "c", "c"]},

        btn_ep_01: {field_names: ["select", "examnumber", "fullname", "lvl_abbrev", "sct_abbrev", "cluster_name", "subj_code", "subj_name_nl",
                                   "segrade", "se_status", "srgrade", "sr_status",
                                   "pescore", "pe_status", "pegrade",
                                    "cescore", "ce_status", "cegrade", "finalgrade",
                                   "note_status", "ce_exam_name", "download_conv_table"],
                    field_caption: ["", "Ex_nr", "Candidate", "Learningpath_twolines", "Sector", "Cluster", "Abbrev_subject_2lines", "Subject",
                                   "School_exam_2lines", "", "Herkansing_SE_grade_2lines", "",
                                  "PE_score", "", "PE_grade",
                                  "CE_score", "", "CE_grade", "Final_grade_twolines",
                                  "", "Exam", ""],
                    field_tags: ["div", "div", "div", "div", "div", "div", "div","div",
                                "input", "div",  "input", "div",
                                "input", "div", "input",
                                "input", "div", "div", "div",
                                "div", "div", "a"],
                    filter_tags: ["text", "text", "text", "text", "text", "text", "text", "text",
                                "text", "grade_status", "text", "grade_status",
                                "text", "grade_status", "text",
                                "text", "grade_status", "text",  "text",
                                "toggle", "text", "text" ],
                    field_width: ["020", "060", "240", "060", "060", "120", "075","240",
                                "090", "020", "090", "020",
                                "090", "020", "090",
                                "090", "020", "090", "090",
                                 "032", "240", "032"],
                    field_align: ["c", "r", "l", "c", "c", "l", "c","l",
                                "c", "c", "c", "c",
                                "c", "c", "c",
                                "c", "c", "c", "c",
                                "c", "l", "c"]},

        btn_reex:  {field_names: ["select", "examnumber", "fullname", "lvl_abbrev", "sct_abbrev", "cluster_name", "subj_code", "subj_name_nl",
                                  "cescore", "ce_status", "cegrade", "note_status", "ce_exam_name", "download_conv_table"],
                    field_caption: ["", "Ex_nr", "Candidate", "Learningpath_twolines", "Sector", "Cluster", "Abbrev_subject_2lines", "Subject",
                                  "Re_examination_score_2lines", "", "Re_examination_grade_2lines", "", "Exam", ""],
                    field_tags: ["div", "div", "div", "div", "div", "div", "div","div",
                                "input", "div",  "div", "div", "div", "a"],
                    filter_tags: ["text", "text", "text", "text", "text", "text", "text", "text",
                                "text", "grade_status", "text", "text", "toggle", "text", "text"],
                    field_width: ["020", "060", "240", "060", "060", "120", "075", "240", "090", "020", "090", "032", "240", "032"],
                    field_align: ["c", "r", "l", "c", "c", "l", "c", "l", "c", "c", "c", "c"]},

        btn_reex03:  {field_names: ["select", "examnumber", "fullname", "lvl_abbrev", "sct_abbrev", "cluster_name", "subj_code", "subj_name_nl",
                                  "cescore", "ce_status", "cegrade", "note_status", "ce_exam_name", "download_conv_table"],
                    field_caption: ["", "Ex_nr", "Candidate", "Learningpath_twolines", "Sector", "Cluster", "Abbrev_subject_2lines", "Subject",
                                  "Third_period_score_2lines", "", "Third_period_grade_2lines", "", "Exam", ""],
                    field_tags: ["div", "div", "div", "div", "div", "div", "div","div",
                                "input", "div",  "div", "div", "div", "a"],
                    filter_tags: ["text", "text", "text", "text", "text", "text", "text", "text",
                                "text", "grade_status", "text", "text", "toggle", "text", "text"],
                    field_width: ["020", "060", "240", "060", "060", "120", "075", "240", "090", "020", "090", "032", "240", "032"],
                    field_align: ["c", "r", "l", "c", "c", "l", "c", "l", "c", "c", "c", "c"]},

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
        if (el_hdrbar_examyear){
            el_hdrbar_examyear.addEventListener("click", function() {
                t_MSED_Open(loc, "examyear", examyear_map, setting_dict, permit_dict, MSED_Response)}, false );
        };
        const el_hdrbar_department = document.getElementById("id_hdrbar_department");
        if (el_hdrbar_department){
            el_hdrbar_department.addEventListener("click", function() {
                t_MSED_Open(loc, "department", department_map, setting_dict, permit_dict, MSED_Response)}, false );
        };
        const el_hdrbar_school = document.getElementById("id_hdrbar_school");
        if (el_hdrbar_school){
            el_hdrbar_school.addEventListener("click", function() {t_MSSSS_Open(loc, "school", school_rows, false, false, setting_dict, permit_dict, MSSSS_school_response)}, false );
        };

        const el_hdrbar_allowed_sections = document.getElementById("id_hdrbar_allowed_sections");
        if (el_hdrbar_allowed_sections){
            el_hdrbar_allowed_sections.addEventListener("click", function() {t_MUPS_Open()}, false );
        };

// ---  MODAL USER SET ALLOWED SECTIONS
        const el_MUPS_username = document.getElementById("id_MUPS_username");
        console.log("DOMContentLoaded TABLE.js el_MUPS_username", el_MUPS_username);
        const el_MUPS_loader = document.getElementById("id_MUPS_loader");

        const el_MUPS_tbody_container = document.getElementById("id_MUPS_tbody_container");
        const el_MUPS_tbody_select = document.getElementById("id_MUPS_tbody_select");

        const el_MUPS_btn_expand_all = document.getElementById("id_MUPS_btn_expand_all");
        if (el_MUPS_btn_expand_all){
            el_MUPS_btn_expand_all.addEventListener("click", function() {MUPS_ExpandCollapse_all()}, false);
        };
        const el_MUPS_btn_save = document.getElementById("id_MUPS_btn_save");
        if (el_MUPS_btn_save){
            el_MUPS_btn_save.addEventListener("click", function() {MUPS_Save("save")}, false);
        };
        const el_MUPS_btn_cancel = document.getElementById("id_MUPS_btn_cancel");

// ---  MSSS MOD SELECT SCHOOL / SUBJECT / STUDENT ------------------------------
        const el_MSSSS_tblBody = document.getElementById("id_MSSSS_tbody_select");
        const el_MSSSS_input = document.getElementById("id_MSSSS_input");
        if (el_MSSSS_input){
            el_MSSSS_input.addEventListener("keyup", function(event){
                setTimeout(function() {t_MSSSS_InputKeyup(el_MSSSS_input)}, 50)});
        };

// ---  SIDEBAR ------------------------------------
        const el_SBR_select_level = document.getElementById("id_SBR_select_level");
        if (el_SBR_select_level){
        console.log("el_SBR_select_level", el_SBR_select_level)
            //el_SBR_select_level.addEventListener("change", function() {HandleSbrLevelSector("level", el_SBR_select_level)}, false)};
            el_SBR_select_level.addEventListener("change", function() {t_SBR_select_level_sector("lvlbase", el_SBR_select_level, SBR_lvl_sct_response)}, false)
        };
        const el_SBR_select_sector = document.getElementById("id_SBR_select_sector");
        if (el_SBR_select_sector){
            //el_SBR_select_sector.addEventListener("change", function() {HandleSbrLevelSector("sector", el_SBR_select_sector)}, false)
            el_SBR_select_sector.addEventListener("change", function() {t_SBR_select_level_sector("sctbase", el_SBR_select_sector, SBR_lvl_sct_response)}, false);
        };
        const add_all = true;
        const el_SBR_select_subject = document.getElementById("id_SBR_select_subject");
        if (el_SBR_select_subject){
            el_SBR_select_subject.addEventListener("click", function() {t_MSSSS_Open(loc, "subject", subject_rows, add_all, false, setting_dict, permit_dict, MSSSS_subject_response)}, false);
        };

        const el_SBR_select_cluster = document.getElementById("id_SBR_select_cluster");
        if (el_SBR_select_cluster){
            el_SBR_select_cluster.addEventListener("click", function() {t_MSSSS_Open_NEW(loc, "cluster", cluster_dictsNEW, add_all, false, setting_dict, permit_dict, MSSSS_cluster_response)}, false);
        };

        const el_SBR_select_student = document.getElementById("id_SBR_select_student");
        if (el_SBR_select_student){
            el_SBR_select_student.addEventListener("click", function() {t_MSSSS_Open(loc, "student", student_rows, add_all, false, setting_dict, permit_dict, MSSSS_student_response)}, false);
        };

        const el_SBR_select_showall = document.getElementById("id_SBR_select_showall");
        if(el_SBR_select_showall){
            el_SBR_select_showall.addEventListener("click", function() {t_SBR_show_all(SBR_show_all_response)}, false);
            add_hover(el_SBR_select_showall);
        };


// ---  MOD APPROVE GRADE ------------------------------------
        const el_mod_approve_grade = document.getElementById("id_mod_approve_grade");

        const el_MAG_header = document.getElementById("id_MAG_header");
        const el_MAG_select_container = document.getElementById("id_MAG_select_container");
            const el_MAG_subheader = document.getElementById("id_MAG_subheader");
            const el_MAG_examperiod = document.getElementById("id_MAG_examperiod");

        const el_MAG_examtype = document.getElementById("id_MAG_examtype");
        if (el_MAG_examtype){
            el_MAG_examtype.addEventListener("change", function() {MAG_ExamtypeChange(el_MAG_examtype)}, false );
        };

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
        const el_MAG_info_container = document.getElementById("id_MAG_info_container");

        const el_MAG_info_request_verifcode = document.getElementById("id_MAG_info_request_verifcode");

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

// ---  MSELEX MOD SELECT EXAM ------------------------------
        const el_MSELEX_header = document.getElementById("id_MSELEX_header");
        const el_MSELEX_info_container = document.getElementById("id_MSELEX_info_container");

        const el_MSELEX_tblBody_select = document.getElementById("id_MSELEX_tblBody_select");
        const el_MSELEX_btn_cancel = document.getElementById("id_MSELEX_btn_cancel");
        const el_MSELEX_btn_save = document.getElementById("id_MSELEX_btn_save");
        if (el_MSELEX_btn_save){
            el_MSELEX_btn_save.addEventListener("click", function() {MSELEX_Save(false)}, false )
        }
        const el_MSELEX_btn_delete = document.getElementById("id_MSELEX_btn_delete");
        if (el_MSELEX_btn_delete){
            el_MSELEX_btn_delete.addEventListener("click", function() {MSELEX_Save(true)}, false )  // true = is_delete
        }

// ---  MOD CONFIRM ------------------------------------
        const el_confirm_header = document.getElementById("id_modconfirm_header");
        const el_confirm_loader = document.getElementById("id_modconfirm_loader");
        const el_confirm_msg_container = document.getElementById("id_modconfirm_msg_container");
        const el_confirm_btn_cancel = document.getElementById("id_modconfirm_btn_cancel");
        const el_confirm_btn_save = document.getElementById("id_modconfirm_btn_save");
        if(el_confirm_btn_save){
            el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()});
        };

// ---  MOD MESSAGE ------------------------------------
        const el_mod_message_btn_hide = document.getElementById("id_mod_message_btn_hide");
        if(el_mod_message_btn_hide){
            el_mod_message_btn_hide.addEventListener("click", function() {ModMessageHide()});
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

// ---  MODAL LINK STUDENTS ------------------------------------
   const el_MLINKSTUD_body = document.getElementById("id_MLINKSTUD_body");

// --- create EventListener for buttons in btn_container
    const el_MLINKSTUD_btn_container = document.getElementById("id_MLINKSTUD_btn_container");
    if(el_MLINKSTUD_btn_container){
        const btns = el_MLINKSTUD_btn_container.children;
        for (let i = 0, btn; btn = btns[i]; i++) {
        //PR2021-12-05 debug: data_btn as argument doesn't work, don't know why, use btn as argument instead
        // was: const data_btn = get_attr_from_el(btn, "data-btn")
            btn.addEventListener("click", function() {MLINKSTUD_btnSelectClicked(btn)}, false )
        };
    };

    const el_MLINKSTUD_loading = document.getElementById("id_MLINKSTUD_loading");
    const el_MLINKSTUD_no_data = document.getElementById("id_MLINKSTUD_no_data");
    const el_MLINKSTUD_has_data = document.getElementById("id_MLINKSTUD_has_data");
    const el_MLINKSTUD_has_unlinked_data = document.getElementById("id_MLINKSTUD_has_unlinked_data");
    const el_MLINKSTUD_all_linked_data = document.getElementById("id_MLINKSTUD_all_linked_data");



    const el_MLINKSTUD_data_container = document.getElementById("id_MLINKSTUD_data_container");

    const el_MLINKSTUD_btn_showall = document.getElementById("id_MLINKSTUD_btn_showall");
    if(el_MLINKSTUD_btn_showall){el_MLINKSTUD_btn_showall.addEventListener("click", function() {MLINKSTUD_toggle_showall()}, false )};

    const el_MLINKSTUD_btn_prev = document.getElementById("id_MLINKSTUD_btn_prev");
    if(el_MLINKSTUD_btn_prev){el_MLINKSTUD_btn_prev.addEventListener("click", function() {MLINKSTUD_btnPrevNextClicked("prev")}, false )};

    const el_MLINKSTUD_btn_next = document.getElementById("id_MLINKSTUD_btn_next");
    if(el_MLINKSTUD_btn_next){el_MLINKSTUD_btn_next.addEventListener("click", function() {MLINKSTUD_btnPrevNextClicked("next")}, false )};

    const el_MLINKSTUD_btn_save = document.getElementById("id_MLINKSTUD_btn_save");
    if(el_MLINKSTUD_btn_save){el_MLINKSTUD_btn_save.addEventListener("click", function() {MLINKSTUD_save()}, false )};

    const el_MLINKSTUD_btn_cancel = document.getElementById("id_MLINKSTUDP_btn_cancel");

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
            grade_rows: {cur_dep_only: true},

            all_exam_rows: {get: true}
        };

        DatalistDownload(datalist_request);
    };
//  #############################################################################################################

//========= DatalistDownload  ===================== PR2020-07-31
    function DatalistDownload(datalist_request, keep_loader_hidden) {
        console.log( "=== DatalistDownload ")
        console.log("    request: ", datalist_request)

// ---  Get today's date and time - for elapsed time
        let startime = new Date().getTime();

// --- reset table rows, also delete header
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

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


        // ---  fill cols_hidden
                    if("cols_hidden" in setting_dict){
                        b_copy_array_noduplicates(setting_dict.cols_hidden, mod_MCOL_dict.cols_hidden);
                    };

        // add level to cols_skipped when dep has no level, thumbrule_allowed PR2023-01-24
                    mod_MCOL_dict.cols_skipped = {};
                    const cols_skipped_all = [];
                    if (!setting_dict.sel_dep_level_req) {cols_skipped_all.push("lvl_abbrev") };
                    if (!setting_dict.sel_examyear_thumbrule_allowed) {cols_skipped_all.push("is_thumbrule")};
                    if (cols_skipped_all.length){mod_MCOL_dict.cols_skipped.all = cols_skipped_all};

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
                    examyear_rows = response.examyear_rows;
                    b_fill_datamap(examyear_map, response.examyear_rows);
                };
                if ("department_rows" in response) {
                    department_rows = response.department_rows;
                    b_fill_datamap(department_map, response.department_rows);
                };
                if ("school_rows" in response)  {
                    school_rows = response.school_rows;
                };
                if ("level_rows" in response) {
                    level_rows = response.level_rows;
                    b_fill_datamap(level_map, response.level_rows);

                    t_SBR_FillSelectOptionsDepbaseLvlbaseSctbase("lvlbase", response.level_rows, setting_dict);
                };
                if ("sector_rows" in response) {
                    sector_rows = response.sector_rows;
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
                    b_fill_datadicts("cluster", "id", null, response.cluster_rows, cluster_dictsNEW);
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

                if ("all_exam_rows" in response) {
                    all_exam_rows = response.all_exam_rows;
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

    function get_datadicts_keystr(tblName, pk_int) {  // PR2023-01-24
        let key_str = tblName + "_" + ((pk_int) ? pk_int : 0);
        return key_str
    };

//=========  CreateSubmenu  ===  PR2020-07-31 PR2021-01-19 PR2021-03-25
    function CreateSubmenu() {
        //console.log("===  CreateSubmenu == ");

        let el_submenu = document.getElementById("id_submenu")
        // sel_btns are btn_exem btn_ep_01 btn_reex btn_reex03
        if (permit_dict.permit_approve_grade){
            // PR2023-02-20 this one includes approve exemptions, turn off for now:
            //AddSubmenuButton(el_submenu, (selected_btn === "btn_exem") ? loc.Approve_exemptions : loc.Approve_grades, function() {MAG_Open("approve")}, [], "id_submenu_approve");
            AddSubmenuButton(el_submenu, loc.Approve_grades, function() {MAG_Open("approve")}, ["tab_show", "tab_btn_ep_01", "tab_btn_reex", "tab_btn_reex03"], "id_submenu_approve");
        };

        AddSubmenuButton(el_submenu, loc.Preliminary_Ex2, function() {ModConfirmOpen("prelim_ex2")}, ["tab_show", "tab_btn_ep_01"]);
        if (permit_dict.permit_submit_grade){
            // PR2023-02-28 turn off temporary
             AddSubmenuButton(el_submenu, loc.Submit_Ex2, function() {MAG_Open("submit_ex2")}, ["tab_show", "tab_btn_ep_01"]);
        };

        AddSubmenuButton(el_submenu, loc.Preliminary_Ex2A, function() {ModConfirmOpen("prelim_ex2a")}, ["tab_show", "tab_btn_ep_01", "tab_btn_reex", "tab_btn_reex03"]);
        if (permit_dict.permit_submit_grade){
            // PR2023-02-28 turn off temporary
            AddSubmenuButton(el_submenu, loc.Submit_Ex2A, function() {MAG_Open("submit_ex2a")}, ["tab_show", "tab_btn_ep_01", "tab_btn_reex", "tab_btn_reex03"]);
        };
        if (permit_dict.requsr_same_school){
            AddSubmenuButton(el_submenu, loc.Ex3_form, function() {ModConfirmOpen("ex3")}, ["tab_show", "tab_btn_ep_01", "tab_btn_reex", "tab_btn_reex03"]);
        };
        if(permit_dict.permit_crud){
            AddSubmenuButton(el_submenu, loc.Upload_grades, function() {MIMP_Open(loc, "import_grade")}, ["tab_show", "tab_btn_ep_01"]);
            AddSubmenuButton(el_submenu, loc.Lookup_exemptions, function() {MLINKSTUD_Open()}, ["tab_show", "tab_btn_exem"]);
            AddSubmenuButton(el_submenu, loc.Upload_exemptions, function() {MIMP_Open(loc, "import_grade")}, ["tab_show", "tab_btn_exem"]);
        };

        // true = save_in_all: when true: hidden columns are saved in 'all', otherwise they are saved separately for each selected_btn PR2021-12-02
        AddSubmenuButton(el_submenu, loc.Hide_columns, function() {t_MCOL_Open("page_grade")}, [], "id_submenu_columns");

        el_submenu.classList.remove(cls_hide);

    }; //function CreateSubmenu

//###########################################################################
//=========  HandleBtnSelect  ================ PR2020-09-19 PR2020-11-14 PR2021-03-15
    function HandleBtnSelect(data_btn, skip_upload) {
        //console.log( "===== HandleBtnSelect ========= ", data_btn);
        // function is called by select_btn.click, t_MCOL_Save, DatalistDownload after response.setting_dict
        // skip_upload = true when called by DatalistDownload
        //  PR2021-09-07 debug: gave error because old btn name was still in saved setting

        // check if data_btn exists, gave error because old btn name was still in saved setting PR2021-09-07 debug
        if (!data_btn) {data_btn = selected_btn};
        if (data_btn && ["btn_exem", "btn_ep_01", "btn_reex", "btn_reex03"].includes(data_btn)) {
            selected_btn = data_btn;
        } else {
            selected_btn = "btn_ep_01";
        };

        const el_submenu_approve = document.getElementById("id_submenu_approve");
        if (el_submenu_approve){
            el_submenu_approve.innerText = (selected_btn === "btn_exem") ? loc.Approve_exemptions : loc.Approve_grades;
        };
// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_grade: {sel_btn: selected_btn}};
    //console.log( "  upload_dict ", upload_dict);
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);

        };

// ---  highlight selected button
        b_highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  show only the elements that are used in this tab
        b_show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

        if(skip_upload){
        // skip_upload = true when called by DatalistDownload.
        //  - don't call DatalistDownload, otherwise it cretaed an indefinite loop
        //  - but fill table with new data

    // --- update header text
            UpdateHeader();

    // ---  fill datatable
            FillTblRows();
        } else {

            // skip showing warning messages when clicking select btn, (msg 'Not current examyear' kept showing) PR2021-12-01
            skip_warning_messages = true;
            const sel_examperiod = (selected_btn === "btn_exem") ? 4 :
                                   (selected_btn === "btn_reex03") ? 3 :
                                   (selected_btn === "btn_reex") ? 2 : 1;

        // - change sel_examtype if necessary
            let sel_examtype = null;
            if (sel_examperiod === 1){
                if( ["se", "sr", "pe", "ce"].includes(setting_dict.sel_examtype) ) {
                    sel_examtype = setting_dict.sel_examtype;
                } else {
                  sel_examtype = "se";
                };

            } else if([2, 3].includes(setting_dict.sel_examperiod) ) {
                sel_examtype = "ce";

            } else if (sel_examperiod === 4){
                if(["se", "ce"].includes(setting_dict.sel_examtype)) {
                    sel_examtype = setting_dict.sel_examtype;
                } else {
                  sel_examtype = "se";
                };
            }
            // upload new sel_examperiod and / or sel_examtype if changed
            const new_setting_dict = {
                    page: "page_grade",
                    sel_btn: selected_btn,
                    sel_examperiod: sel_examperiod,
                    sel_examtype: sel_examtype
                };
        console.log( "    new_setting_dict", new_setting_dict);
            const datalist_request = {
                setting: new_setting_dict,
                grade_rows: {cur_dep_only: true},
                all_exam_rows: {get: true}
            };
            DatalistDownload(datalist_request);
        };

    };  // HandleBtnSelect

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
        console.log("=== HandleSbrPeriod");
        //console.log( "el_select.value: ", el_select.value, typeof el_select.value)
        const sel_examperiod = (Number(el_select.value)) ? Number(el_select.value) : null;
        const filter_value = sel_examperiod;

// ---  upload new setting and retrieve the tables that have been changed because of the change in examperiod
        const datalist_request = {
            setting: {
                page: "page_grade",
                sel_examperiod: sel_examperiod
                },

            student_rows: {cur_dep_only: true},
            studentsubject_rows: {cur_dep_only: true},
            grade_rows: {cur_dep_only: true},

            all_exam_rows: {get: true}

        };
        DatalistDownload(datalist_request);
    };  // HandleSbrPeriod


//=========  SBR_lvl_sct_response  ================ PR2023-03-29
    function SBR_lvl_sct_response(tblName, selected_dict, selected_pk_int) {
        console.log("===== SBR_lvl_sct_response =====");
        console.log( "   tblName: ", tblName)
        console.log( "   selected_pk_int: ", selected_pk_int, typeof selected_pk_int)
        console.log( "   selected_dict: ", selected_dict)
        // tblName = "lvlbase" or "sctbase"

        //el_header_left.innerHTML = "&nbsp;";
        //el_header_right.innerHTML =  "&nbsp;";

// ---  using function UploadChanges not necessary, uploading new_setting_dict is part of DatalistDownload

// ---  upload new setting and download datarows
        const sel_pk_key_str = (tblName === "sctbase") ? "sel_sctbase_pk" : "sel_lvlbase_pk";

        const new_setting_dict = {page: "page_grade"}
        new_setting_dict[sel_pk_key_str] = selected_pk_int;

        // reset student and  cluster filter
        new_setting_dict.sel_student_pk = null;
        new_setting_dict.sel_cluster_pk = null;

        const datalist_request = {
                setting: new_setting_dict,

                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},

                scheme_rows: {cur_dep_only: true},
                schemeitem_rows: {cur_dep_only: true},

                subject_rows: {cur_dep_only: true},
                cluster_rows: {cur_dep_only: true},

                student_rows: {cur_dep_only: true},
                studentsubject_rows: {cur_dep_only: true},
                grade_rows: {cur_dep_only: true},

                all_exam_rows: {get: true}
            };

        // hide itemcount
        t_set_sbr_itemcount_txt(loc, 0)

        console.log("    datalist_request", datalist_request);
        DatalistDownload(datalist_request);
    };  // SBR_lvl_sct_response

//=========  HandleSbrLevelSector  ================ PR2021-03-06 PR2021-12-03
    function HandleSbrLevelSector(mode, el_select) {
        console.log("=== HandleSbrLevelSector");
        console.log( "  el_select.value: ", el_select.value, typeof el_select.value)
        // mode = "level" or "sector"

// --- reset table rows, also delete header, item_count
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

// ---  reset total in sidebar
        selected.item_count = 0;
        t_set_sbr_itemcount_txt(loc, selected.item_count, null, null, setting_dict.user_lang);

// - get new value from el_select
        const sel_pk_int = (Number(el_select.value)) ? Number(el_select.value) : null;
        const sel_code = (el_select.options[el_select.selectedIndex]) ? el_select.options[el_select.selectedIndex].innerText : null;

// - put new value in setting_dict
        const sel_pk_key_str = (mode === "sector") ? "sel_sctbase_pk" : "sel_lvlbase_pk";
        const sel_code_key_str = (mode === "sector") ? "sel_sctbase_code" : "sel_lvlbase_code";
        setting_dict[sel_pk_key_str] = sel_pk_int;
        setting_dict[sel_code_key_str] = sel_code;
        console.log("setting_dict", setting_dict);

// ---  upload new setting - not necessary, new setting will be saved in DatalistDownload
        //b_UploadSettings (upload_dict, urls.url_usersetting_upload);
        //UpdateHeaderRight();
       // FillTblRows();

        const new_setting_dict = {page: "page_grade"}
        new_setting_dict[sel_pk_key_str] = sel_pk_int;

        const datalist_request = {
            setting: new_setting_dict,

            // PR2022-05-12 debug. subject_rows etc added. needs refresh to show subjects of the new level
            subject_rows: {cur_dep_only: true},
            cluster_rows: {cur_dep_only: true, allowed_only: true},

            student_rows: {cur_dep_only: true},
            studentsubject_rows: {cur_dep_only: true},
            grade_rows: {cur_dep_only: true},

            all_exam_rows: {get: true}
        };

        DatalistDownload(datalist_request);

    }  // HandleSbrLevelSector

//=========  FillOptionsSelectLevelSector  ================ PR2021-03-06
    function FillOptionsSelectLevelSector(tblName, rows) {
        //console.log("=== FillOptionsSelectLevelSector");
        //console.log("tblName", tblName);

        const display_rows = []
        const has_items = (!!rows && !!rows.length);
        const has_profiel = setting_dict.sel_dep_has_profiel;

        const caption_all = "&#60" + ( (tblName === "level") ? loc.All_levels : (has_profiel) ? loc.All_profiles : loc.All_sectors ) + "&#62";
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
                const sel_code = (el_SBR_select.options[el_SBR_select.selectedIndex]) ? el_SBR_select.options[el_SBR_select.selectedIndex].innerText : null;
                if (tblName === "level"){
                    setting_dict.sel_lvlbase_code = sel_code;
                } else if (tblName === "sector"){
                    setting_dict.sel_sctbase_code = sel_code;
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
                el_SBR_select_sector_label.innerText = ( (has_profiel) ? loc.Profile : loc.Sector ) + ":";
            };
        }
    }  // FillOptionsSelectLevelSector

//========= UpdateHeader  ================== PR2021-03-14
    function UpdateHeader(){
        //console.log(" --- UpdateHeader ---" )
        //console.log("setting_dict", setting_dict)
        // sel_subject_txt gets value in MSSSS_display_in_sbr, therefore UpdateHeader comes after MSSSS_display_in_sbr

        //console.log(" --- UpdateHeaderRight ---" )
        let level_sector_txt = "";
        if (setting_dict.sel_lvlbase_pk) { level_sector_txt = setting_dict.sel_lvlbase_code }
        if (setting_dict.sel_sctbase_pk) {
            if(level_sector_txt) { level_sector_txt += " - " };
            level_sector_txt += setting_dict.sel_sctbase_code
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
        //console.log( "===== FillTblRows  === ");
        //console.log( "field_settings", field_settings);
        //console.log( "selected_btn", selected_btn);

        const tblName = get_tblName_from_selectedBtn()
        const field_setting = field_settings[selected_btn];
        const data_rows = get_datarows_from_selectedBtn()

// ---  get list of hidden columns
        const col_hidden = get_column_is_hidden();

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

        if (tblBody_datatable.rows.length){
            t_Filter_TableRows(tblBody_datatable, filter_dict, selected, loc.Subject, loc.Subjects);
        } else if (["btn_reex", "btn_reex03"].includes(selected_btn)) {
            let tblRow = tblBody_datatable.insertRow(-1);
            let td = tblRow.insertCell(-1);
            td = tblRow.insertCell(-1);
            td.setAttribute("colspan", 6);
            let el = document.createElement("p");
            el.className = "border_bg_transparent p-2 my-4"
            el.innerHTML = (selected_btn === "btn_reex03") ?
                                loc.reex03_msg_01 + "<br>" + loc.reex03_msg_02 + "<br>" + loc.reex03_msg_03 :
                                loc.reex_msg_01 + "<br>" + loc.reex_msg_02 + "<br>" + loc.reex_msg_03;
            td.appendChild(el);
        };
    };  // FillTblRows

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
            const skip_left_border = (field_name === "download_conv_table") ||  (field_name !== "note_status" && field_name.includes("_status"));

    // --- skip column if in col_hidden
            //example of mapped field
            //const mapped_field = (field_name === "subj_status") ? "subj_error" :
            //                     (field_name === "pok_validthru") ? "pok_status" : field_name;
            // const mapped_field = field_name;

    // skip columns if in col_hidden
            if (!col_hidden.includes(field_name)){
                const key = field_setting.field_caption[j];
                let field_caption = (loc[key]) ? loc[key] : key;
                if (field_name === "sct_abbrev") {
                    field_caption = (setting_dict.sel_dep_has_profiel) ? loc.Profile : loc.Sector;
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
                    } else if (["se_status", "sr_status", "pe_status", "ce_status"].includes(field_name)) {
                        el_header.classList.add("diamond_0_0")
                    } else if(field_name === "note_status"){
                         // dont show note icon when user has no permit_read_note
                        const class_str = (permit_dict.permit_read_note) ? "note_0_1" : "note_0_0"
                        el_header.classList.add(class_str)
                    }

        // --- add left border, not when status field or download_exam
                    if(j && !skip_left_border){th_header.classList.add("border_left")};

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

        // --- add left border, not when status field
                    if(j && !skip_left_border){th_filter.classList.add("border_left")};

        // --- add EventListener to el_filter
                    if (["text", "number"].includes(filter_tag)) {
                        el_filter.addEventListener("keyup", function(event){HandleFilterKeyup(el_filter, event)});
                        add_hover(th_filter);

                    } else if (filter_tag === "grade_status") {
                        // add EventListener for icon to th_filter, not el_filter
                        th_filter.addEventListener("click", function(event){HandleFilterStatus(el_filter)});
                        th_filter.classList.add("pointer_show");
                    // default empty icon is necessary to set pointer_show
                        el_filter.classList.add("diamond_3_4");  //  diamond_3_4 is blank img
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
            };
        };
    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09 PR2021-12-02 PR2022-05-24
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
            const skip_left_border = (field_name === "download_conv_table" || is_status_field);

    // --- skip columns if in col_hidden
            //example of mapped field
            //const mapped_field = (field_name === "subj_status") ? "subj_error" :
            //                     (field_name === "pok_validthru") ? "pok_status" : field_name;
            // const mapped_field = field_name;

    // skip columns if in col_hidden
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

// --- make el readonly when not requsr_requsr_same_school or when not edit permission
                    const may_edit = permit_dict.requsr_same_school && permit_dict.permit_crud;

                    let is_enabled = false;
                    if (may_edit){
                        // when exemption: only fields segrade and cegrade are visible
                        //      dont block when no ce: let server give message instead
                        // input fields are: "segrade", "srgrade", "pescore", "pegrade", "cescore", "cegrade",

                        if (data_dict.examperiod === 4) {
                            is_enabled = ["segrade", "cegrade"].includes(field_name) && !data_dict.exemption_imported;
                        } else if (data_dict.examperiod === 1) {
                            is_enabled = ["segrade", "srgrade", "pescore", "cescore"].includes(field_name)
                                //PR2022-06-30 in secret_exam you can also enter score
                                // was: if (data_dict.secret_exam) {
                                //    is_enabled = ["pegrade", "cegrade"].includes(field_name);
                                //} else {
                        } else if ([2, 3].includes(data_dict.examperiod)) {
                            is_enabled = ["pescore", "cescore"].includes(field_name);
                        };
                    };

                    el.readOnly = !is_enabled;

                    el.setAttribute("type", "text")
                    el.setAttribute("autocomplete", "off");
                    el.setAttribute("ondragstart", "return false;");
                    el.setAttribute("ondrop", "return false;");

// --- add class 'input_text' and text_align
                // class 'input_text' contains 'width: 100%', necessary to keep input field within td width
                    el.classList.add("input_text");

    // --- add EventListener
                    el.addEventListener("keydown", function(event){HandleArrowEvent(el, event)});
                    if (may_edit){
                        el.addEventListener("change", function(){HandleInputChange(el)});
                    };
                };

// --- add width, text_align, right padding in examnumber
                // >>> td.classList.add(class_width, class_align);
                if(["fullname", "subj_name_nl"].includes(field_name)){
                    // dont set width in field student and subject, to adjust width to length of name
                    // >>> el.classList.add(class_align);
                    el.classList.add(class_width, class_align);

                } else {
                    el.classList.add(class_width, class_align);
                };
                if(field_name === "examnumber"){
                    el.classList.add("pr-2");
                }

    // --- add left border, not when status field or download field
                if(j && !skip_left_border){td.classList.add("border_left")};
/*
// --- add column with status icon, only when weighing > 0
                if (["se_status", "sr_status"].includes(field_name)){
                    if(data_dict.weight_se){
                        el.classList.add("stat_0_0")
                    };

                } else if (["pe_status", "ce_status"].includes(field_name)){
                console.log("data_dict.weight_ce", data_dict.weight_ce, !!data_dict.weight_ce)
                    if(data_dict.weight_ce){
                        el.classList.add("stat_0_0")
                    };

                } else
      */
                if (field_name === "note_status"){
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
                } else if (field_name === "ce_exam_name"){
                    td.addEventListener("click", function() {MSELEX_Open(el)}, false);
                    add_hover(td);

                } else if (field_name === "download_conv_table"){
            // +++  create href and put it in button PR2021-05-07
                    if (data_dict.ce_exam_id) {
                        // td.class_align necessary to center align a-element
                        td.classList.add(class_align);
                        add_hover(td);
                        //el.innerHTML = "&emsp;&emsp;&emsp;&emsp;&#8681;&emsp;&emsp;&emsp;&emsp;";
                        el.innerHTML = "&emsp;&#8681;&emsp;";
                        td.title = loc.Download_conv_table;
                        // target="_blank opens file in new tab
                        el.target = "_blank";
                    };
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
                // only show status when weight > 0 and has value
                // TODO enable this next year . It is turned off so you can remove approved empty scores
                //const grade_has_value = get_grade_has_value(field_name, data_dict, true);
                //if (grade_has_value){
                if (is_status_field){
                    td.addEventListener("click", function() {UploadStatus(el)}, false)
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
            };
        };

        return tblRow;
    };  // CreateTblRow

//=========  UpdateTblRow  ================ PR2020-08-01
    function UpdateTblRow(tblRow, tblName, data_dict) {
        console.log("=========  UpdateTblRow =========");
        console.log("    data_dict", data_dict);
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
    //console.log("     field_name", field_name);
    //console.log("     fld_value", fld_value);

            if(field_name){
                let title_text = null, filter_value = null;
                if (["cescore", "pescore"].includes(field_name)){
                    el_div.value = fld_value;
                    filter_value = fld_value;

                } else if (el_div.nodeName === "INPUT"){

                    //PR2022-04-17 Sentry error: Object doesn't support property or method 'replaceAll'
                    // tried to solve by adding 'typeof, but
                    // replaceAll is not supported by Internet Explorere,
                    // changed to replace()
                    if (fld_value == null || fld_value === "" ){
                        el_div.value = null;
                        filter_value = null;
                    } else if (typeof fld_value === 'string' || fld_value instanceof String){
                    // replace dot with comma
                        el_div.value = fld_value.replace(".", ",");
                        filter_value = fld_value.toLowerCase();
                    } else {
                        el_div.value = fld_value;
                        filter_value = fld_value;
                    };

                } else if (field_name.includes("_status")){

                    // TODO enable this next year . It is turned off because empty scores were submitted
                    //const grade_has_value = get_grade_has_value(field_name, data_dict, true);
                    //if ( grade_has_value){
                    if (true){
                        const [status_className, status_title_text, filter_val] = UpdateFieldStatus(field_name, fld_value, data_dict);
                        filter_value = filter_val;
                        el_div.className = status_className;
                        title_text = status_title_text;
                    };
                } else if (field_name === "filename"){
                    //el_div.innerHTML = "&#8681;";
                } else if (field_name === "url"){
                    el_div.href = fld_value;

                } else if (field_name === "download_conv_table"){

    // +++  create href and put it in button PR2021-05-07
                    const has_exam = !!data_dict.ce_exam_id;
                    const href_str = (has_exam) ? urls.url_exam_download_conversion_pdf.replace("-", data_dict.ce_exam_id.toString()) : null;

                    el_div.innerHTML = (has_exam) ? "&emsp;&#8681;&emsp;" : "&emsp;&emsp;&emsp;";
                    add_or_remove_attr(el_div, "href", has_exam, href_str);
                    add_or_remove_attr(el_div, "target", has_exam, "_blank");
                    add_or_remove_attr(el_div.parentNode, "title", has_exam, loc.Download_conv_table);
                    add_or_remove_class(el_div.parentNode, "awp_pointer_show", has_exam, "awp_pointer_hide" )

                } else {
                    let inner_text = null;
                    if (field_name === "examperiod"){
                        inner_text = loc.examperiod_caption[data_dict.examperiod];
                    } else if (field_name === "examtype"){
                        inner_text = loc.examtype_caption[data_dict.examtype];

                    } else if (["segrade", "srgrade", "pegrade", "cegrade"].includes(field_name)){
                        if (fld_value){

                            inner_text = (loc.user_lang === "en") ? fld_value : fld_value.replace(".", ",");
                            filter_value = fld_value.toLowerCase();
                        };
                    //} else if (field_name === "datepublished"){
                    //    inner_text = format_dateISO_vanilla (loc, data_dict.datepublished, true, false, true, false);
                    } else {
                        inner_text = fld_value;
                        if (field_name === "ce_exam_name"){
                            title_text = fld_value
                            if(data_dict.secret_exam && loc.Designated_exam){
                                title_text += "\n" + loc.Designated_exam.toLowerCase();
                            };
                        };
                    };
                    el_div.innerText = (inner_text) ? inner_text : "\n"; // \n is necessary to show green field when blank
                    filter_value = (inner_text) ? inner_text.toString().toLowerCase() : null;
                };

                add_or_remove_class(el_div, "text_decoration_line_through_red", data_dict.studsubj_tobedeleted, "text_decoration_initial")
                if (!title_text && data_dict.studsubj_tobedeleted){
                    title_text = loc.This_subject_ismarked_fordeletion + "\n" + loc.You_cannot_make_changes;
                };

    // ---  add attribute title
                add_or_remove_attr (el_div, "title", !!title_text, title_text);
    // ---  add attribute filter_value
                add_or_remove_attr (el_div, "data-filter", !!filter_value, filter_value);
            };
        };
    };  // UpdateField

//=========  UpdateFieldStatus  ================ PR2021-12-19 PR2022-08-28 PR2023-01-24
    function UpdateFieldStatus(field_name, fld_value, data_dict) {
        //console.log("=========  UpdateFieldStatus =========");
        //console.log("    field_name", field_name);
        //console.log("    fld_value", fld_value);
        //console.log("    data_dict", data_dict);

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
            // only show status when weight > 0

            // TODO enable this next year. It is turned off because empty scores were submitted
            //const grade_has_value = get_grade_has_value(field_name, data_dict, true);
            //if (grade_has_value){

            const show_status = (["se_status", "sr_status"].includes(field_name) && data_dict.weight_se) ||
                                (["pe_status", "ce_status"].includes(field_name) && data_dict.weight_ce);
            if (true){
                const field_auth1by_id = prefix_str + "_auth1by_id";
                const field_auth2by_id = prefix_str + "_auth2by_id";
                const field_auth3by_id = prefix_str + "_auth3by_id";
                const field_auth4by_id = prefix_str + "_auth4by_id";
                const field_published_id = prefix_str + "_published_id";
                const field_blocked = prefix_str + "_blocked";
                const field_status = prefix_str + "_status";

                const auth1by_id = (data_dict[field_auth1by_id]) ? data_dict[field_auth1by_id] : null;
                const auth2by_id = (data_dict[field_auth2by_id]) ? data_dict[field_auth2by_id] : null;
                const auth3by_id = (data_dict[field_auth3by_id]) ? data_dict[field_auth3by_id] : null;
                const auth4by_id = (data_dict[field_auth4by_id]) ? data_dict[field_auth4by_id] : null;
                const published_id = (data_dict[field_published_id]) ? data_dict[field_published_id] : null;
                const is_blocked = (data_dict[field_blocked]) ? data_dict[field_blocked] : null;

                // - auth3 does not have to sign when secret exam (aangewezen examen)
                // - auth3 also does not have to sign when exemption (vrijstelling) PR2023-02-02

                // PR2023-02-07 debug: this is not correct value: !data_dict.examperiod === 4, must be: data_dict.examperiod !== 4
                const auth3_must_sign = (!data_dict.secret_exam && data_dict.examperiod !== 4);

                // - auth4 does not have to sign when secret exam (aangewezen examen) or when se-grade
                // - auth4 does not have to sign when se-grade
                // - auth4 also does not have to sign when exemption (vrijstelling) PR2023-02-02

                // PR2023-02-07 debug: this is not correct value: !data_dict.examperiod === 4, must be: data_dict.examperiod !== 4
                const auth4_must_sign = (!data_dict.secret_exam && data_dict.examperiod !== 4
                                            && ["pe_status", "ce_status"].includes(field_name));

                className = f_get_status_auth_iconclass(published_id, is_blocked, auth1by_id, auth2by_id, auth3_must_sign, auth3by_id, auth4_must_sign, auth4by_id);
                filter_value = className;

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

                } else if(auth1by_id || auth2by_id || auth3by_id || auth4by_id){
                    title_text = (data_dict.secret_exam) ? loc.Designated_exam + "\n" : "";
                    title_text += loc.Approved_by + ": ";
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
        };
        return [className, title_text, filter_value]
    };  // UpdateFieldStatus

//=========  UpdateFieldDownloadExam  ================ PR2022-05-17
    function UpdateFieldDownloadExamNIU(tblName, el_div, data_dict) {
        const show_href = (tblName === "ete_exam" || (data_dict.ce_exam_id && !data_dict.secret_exam && data_dict.ceex_published_id) );
        if (show_href){
            // EventListener "mouseenter" and "mouseleave" will be added each time this function is called.
            // better solution is class with and without hover. No time to figure this out yet PR2022-05-17
            add_hover(el_div.parentNode);
        };
        const inner_html = (show_href) ? "&emsp;&emsp;&emsp;&emsp;&#8681;&emsp;&emsp;&emsp;&emsp;" : null;
        el_div.innerHTML = inner_html;
        el_div.target = (show_href) ? "_blank" : null;

// +++  create href and put it in button PR2021-05-07
        const pk_str = (data_dict.id) ? data_dict.id.toString() : null;
        const href_str = (!show_href || !pk_str) ? null :
                            (tblName === "ete_exam") ? urls.url_exam_download_exam_pdf.replace("-", pk_str) :
                                                       urls.url_exam_download_grade_exam_pdf.replace("-", pk_str) ;
        el_div.href = href_str;
    };  // UpdateFieldDownloadExam

// +++++++++++++++++ UPLOAD CHANGES +++++++++++++++++ PR2020-12-15

//========= HandleArrowEvent  ================== PR2020-12-20
    function HandleArrowEvent(el, event){
        //console.log(" --- HandleArrowEvent ---")
        //console.log("event.key", event.key, "event.shiftKey", event.shiftKey)
        // This is not necessary: (event.key === "Tab" && event.shiftKey === true)
        // Tab and shift-tab move cursor already to next / prev element
        if (["Enter", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key)) {
// --- get move_horizontal and move_vertical based on event.key and event.shiftKey
            // in page grades cursor goes down when clicked om Emter key
            let move_horizontal = (event.key === "ArrowRight") ? 1 :
                                    (event.key === "ArrowLeft") ? -1 : 0
            let move_vertical = (event.key === "ArrowDown" || (event.key === "Enter" && !event.shiftKey)) ? 1 :
                                    (event.key === "ArrowUp" || (event.key === "Enter" && event.shiftKey)) ? -1 : 0

        //console.log("move_horizontal", move_horizontal, "move_vertical", move_vertical)
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
                const next_cell = new_tblRow.cells[new_col_index];
                if(next_cell){
                    const next_el = next_cell.children[0];
        //console.log("next_el", next_el)
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

            // TODO PR2023-02-18 : const is_allowed_cluster = get_is_allowed_cluster(data_dict.cluster_id);
        const is_allowed_cluster = true;
            const has_permit = (permit_dict.permit_crud && permit_dict.requsr_same_school);
            if (!is_allowed_cluster) {
        // show message no_permission_cluster
       // "This subject does not belong to the allowed clusters.")
       // "You don't have permission to edit this %(score)s.")
                const msg_html = ["<div class='p-2'>", loc.grade_err_list.no_permission_cluster_01, "<br>",
                        (fldName.includes("score")) ? loc.grade_err_list.no_permission_edit_score : loc.grade_err_list.no_permission_edit_grade,
                        "</div>"].join("");
                b_show_mod_message_html(msg_html);
        // put back old value  in el_input
                el_input.value = old_value;
            } else if (!has_permit){
        // show message no permission
                b_show_mod_message_html(loc.grade_err_list.no_permission);
        // put back old value  in el_input
                el_input.value = old_value;
            } else {
                const blocked_field = fldName.slice(0, 2) + "_blocked";
                const published_field = fldName.slice(0, 2) + "_published_id";
                const is_blocked = (data_dict[blocked_field]) ? data_dict[blocked_field] : false;
                const is_published = (data_dict[published_field]) ? true : false;
                const is_submitted = data_dict[published_field] ? true : false;

                if (is_submitted && false){
                    // Note: if grade blocked: this means the inspection has given permission to change grade
                    // when blocking by Inspection the published and auth fields are reset to null
                    const msg_html = (!is_blocked) ? loc.grade_err_list.grade_submitted + "<br>" + loc.grade_err_list.need_permission_inspection :
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
        //console.log( " ==== DownloadGradeStatusAndIcons ====");

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
//========= UploadStatus  ============= PR2020-07-31  PR2021-01-14 PR2022-03-20 PR2024-02-02
    function UploadStatus(el_input) {
        console.log( " ==== UploadStatus ====");
        console.log( "    permit_dict", permit_dict);
        //console.log( "permit_dict.permit_approve_grade", permit_dict.permit_approve_grade);

        // only called by field 'se_status', 'sr_status', 'pe_status', 'ce_status'
        mod_dict = {};

        if(permit_dict.permit_approve_grade || permit_dict.permit_block_grade){
            const tblName = "grade";
            const fldName = get_attr_from_el(el_input, "data-field");
            const tblRow = t_get_tablerow_selected(el_input);
            const grade_pk = get_attr_from_el_int(tblRow, "data-pk");
            const data_dict = get_gradedict_by_gradepk(grade_pk);
            console.log( "    data_dict", data_dict);

            if(!isEmpty(data_dict)){

// - get info of this grade
                const examtype_2char = fldName.substring(0,2);
                const is_published = (!!data_dict[examtype_2char + "_published_id"]);
                const is_blocked = (!!data_dict[examtype_2char + "_blocked"]);
                const examperiod = data_dict.examperiod;
                const grade_has_value = get_grade_has_value(fldName, data_dict);
                // is_allowed_cluster = true when allowed_clusters is empty or when cluster_id in allowed_clusters PR2023-03-27
                const is_allowed_cluster = (permit_dict.allowed_clusters && permit_dict.allowed_clusters.length) ?
                    (!!data_dict.cluster_id && permit_dict.allowed_clusters.includes(data_dict.cluster_id)) : true;

// +++ approve grades by school +++++++++++++++++++++
                if(permit_dict.permit_approve_grade){

        // - get auth_index of requsr ( statusindex = 1 when auth1 etc
                    // auth_index : 0 = None, 1 = auth1, 2 = auth2, 3 = auth3, 4 = auth4
                    // b_get_auth_index_of_requsr returns index of auth user, returns 0 when user has none or multiple auth usergroups
                    // this function gives err message when multiple found. (uses b_show_mod_message_html)

                    const permit_auth_list = b_get_multiple_auth_index_of_requsr(permit_dict)
                    const requsr_auth_index = setting_dict.sel_auth_index;

                    if(requsr_auth_index){
                        if(fldName in data_dict){
                            if (!is_allowed_cluster){
                                const  msg_html = ["<p class='border_bg_invalid p-2'>",
                                                    loc.approve_err_list.No_cluster_permission, "</p>"].join("");
                                b_show_mod_message_html(msg_html);
                            } else if (data_dict.studsubj_tobedeleted){
                                const  msg_html = ["<p class='border_bg_invalid p-2'>",
                                                    loc.This_subject_ismarked_fordeletion, "<br>",
                                                    loc.You_cannot_make_changes, "</p>"].join("");
                                b_show_mod_message_html(msg_html);

                            } else if (examperiod === 4 && requsr_auth_index > 2){
                                const msg_html = (requsr_auth_index === 3) ? loc.approve_err_list.Examiner_cannot_approve_exem : loc.approve_err_list.Corrector_cannot_approve_exem;
                                b_show_mod_message_html(msg_html);
                            } else {

        // - is_approved_by_requsr_auth = true when requsr_auth has approved in this function
                                // - auth_dict contains user_id of all auth_index
                                //   auth_dict:  {1: 146, 3: 157}
                                const auth_dict = {};
                                const is_approved_by_requsr_auth = get_is_approved_by_requsr_auth(data_dict, examtype_2char, requsr_auth_index, auth_dict);

        //console.log( "    is_approved_by_requsr_auth", is_approved_by_requsr_auth);
        // - give message and exit when corrector wants to approve se_grade, not when remove approved
                                if (fldName === "se_status" && requsr_auth_index === 4 && !is_approved_by_requsr_auth){
                                    b_show_mod_message_html(loc.approve_err_list.Corrector_cannot_approve_se);

        // - give message and exit when examiner or corrector wants to approve secret exam, not when remove approved
                                } else if(data_dict.secret_exam && [3, 4].includes(requsr_auth_index) && !is_approved_by_requsr_auth){
                                    b_show_mod_message_html(loc.approve_err_list.Cannot_approve_secret_exam);

        // - give message and exit when grade is published
                                } else if (is_published){
                                    const msg_html = [loc.approve_err_list.This_grade_is_submitted,
                                                      loc.approve_err_list.You_cannot_change_approval].join("<br>");
                                    b_show_mod_message_html(msg_html);
                                } else {

        // ---  toggle value of is_approved_by_requsr_auth
                                    const new_is_approved_by_requsr_auth = !is_approved_by_requsr_auth;
        //console.log( "    new_is_approved_by_requsr_auth", new_is_approved_by_requsr_auth);

        // also update requsr_pk in auth_dict;
                                    auth_dict[requsr_auth_index] = (new_is_approved_by_requsr_auth) ? permit_dict.requsr_pk : null;

        // give message when new_is_approved_by_requsr_auth = true and grade already approved by this user in different function
                                    // chairperson cannot also approve as secretary or as corrector
                                    // secretary cannot also approve as chairperson or as corrector
                                    // examiner cannot also approve as corrector
                                    // corrector cannot also approve as chairperson, secretary or examiner

                                    const already_approved_by_auth_index = get_already_approved_by_auth_index(auth_dict, new_is_approved_by_requsr_auth, requsr_auth_index);

        //console.log( "    already_approved_by_auth_index", already_approved_by_auth_index);
                                    if (already_approved_by_auth_index) {
                                        const auth_function = b_get_function_of_auth_index(loc, already_approved_by_auth_index);
                                        const msg_html = [loc.approve_err_list.Approved_in_function_of, auth_function.toLowerCase(), ".<br>",
                                                          loc.approve_err_list.You_cannot_approve_again].join("");
                                        b_show_mod_message_html(msg_html);

                                    } else {

        // - give message when grade /score  has no value, skip when removing approval
                                        // skip approve if this grade has no value - not when removing approval
                                        // PR2022-03-11 after tel with Nancy Josephina: blank grades can also be approved, give warning first
                                        // PR2022-05-31 after a corrector has blocked all empty scores by approving: skip approve when empty

                                        // no value of exemption is complicated, because of no CE in 2020 and partly in 2021.
                                        // skip no_grade_value of exemption, validate on server

                                        // is_approved_by_requsr_auth is used in approve: to allow removing approved, is_approved_by_requsr_auth = true in updatefield and createtblrow

        console.log( "    examtype_2char", examtype_2char);
        console.log( "    grade_has_value", grade_has_value);
                                        if (["pe", "ce"].includes(examtype_2char) &&
                                            [1, 2, 3].includes(data_dict.examperiod) &&
                                            !data_dict.weight_ce){
                                            b_show_mod_message_html(loc.approve_err_list.Subject_has_no_ce);

                            // give message when grade has no value, not when removing approved
                                        } else if (!grade_has_value && !is_approved_by_requsr_auth){
                                            const is_score = ( ["pe", "ce"].includes(examtype_2char) &&
                                                            [1, 2, 3].includes(data_dict.examperiod) &&
                                                                !data_dict.secret_exam);
                                            const msg_html = (is_score) ? loc.approve_err_list.Score_not_entered + "<br>" + loc.approve_err_list.Dont_haveto_approve_blank_scores :
                                                                loc.approve_err_list.Grade_not_entered + "<br>" + loc.approve_err_list.Dont_haveto_approve_blank_grades;
                                            b_show_mod_message_html(msg_html);

                                        } else {
                                            UploadApproveGrade(tblName, fldName, examtype_2char, data_dict, auth_dict, requsr_auth_index,
                                                                is_published, is_blocked, new_is_approved_by_requsr_auth, el_input) ;
                                        }; //  if (double_approved))
                                    };  // if (already_approved_by_auth_index)
                                };  // if (published_pk)
                            };  // if (examperiod === 4 and requsr_auth_index > 2){
                        };  // if(fldName in data_dict)
                    };  //  if(requsr_auth_index)

// ++++++++++++++++ Inspectorate can block grades +++++++++++++++++++++
                } else if(permit_dict.permit_block_grade ){

    // check if cluster is allowed
                    // TODO PR2023-02-18 : const is_allowed_cluster = get_is_allowed_cluster(data_dict.cluster_id);

                    if (is_published || is_blocked)  {
                        if (!is_allowed_cluster){
                            const msg_txt = (!is_blocked) ? loc.No_cluster_block_permission : loc.No_cluster_unblock_permission;
                            const msg_html = ["<div class='p-2'>", msg_txt, "</div>"].join("");
                            b_show_mod_message_html(msg_html);
                        } else {
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
                    };  //  if (is_published || is_blocked)
                };  // if(permit_dict.permit_approve_grade)
            }  //   if(!isEmpty(data_dict)){
        };  // if(permit_dict.permit_approve_grade){
    };  // UploadStatus

//========= get_is_approved_by_requsr_auth  ============= PR2022-06-13
    function get_is_approved_by_requsr_auth(data_dict, examtype_2char, requsr_auth_index, auth_dict){
        //console.log( " ==== get_is_approved_by_requsr_auth ====");
// - is_approved_by_requsr_auth = true when requsr_auth has approved in this function
        // - auth_dict contains user_id of all auth_index
        // auth_dict:  {1: 146, 3: 157}

        // TODO PR2022-11-28 Een goedkeuring kan ook worden verwijderd door de voorzitter of secretaris van de examencommissie , maar NIET door ee nandere gecommitteerde
        let is_approved_by_requsr_auth = false;
        for (let i = 1, key_str; i < 5; i++) {
            key_str = examtype_2char + "_auth" + i + "by_id";
            if (data_dict[key_str]){
                if (requsr_auth_index === i) {
                    is_approved_by_requsr_auth = true;
                };
                auth_dict[i] = data_dict[key_str];
            };
        };
        return is_approved_by_requsr_auth;
    };
// end of get_is_approved_by_requsr_auth


//========= get_already_approved_by_auth_index  ============= PR2022-06-13
    function get_already_approved_by_auth_index(auth_dict, new_is_approved_by_requsr_auth, requsr_auth_index){
        // chairperson cannot also approve as secretary or as corrector
        // secretary cannot also approve as chairperson or as corrector
        // examiner cannot also approve as corrector
        // corrector cannot also approve as chairperson, secretary or examiner

        let already_approved_by_auth_index = null;

        if(new_is_approved_by_requsr_auth){
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
        return already_approved_by_auth_index
    };
// end of get_already_approved_by_auth_index

//========= get_grade_has_value  ============= PR2022-05-31 PR2022-06-13
    function get_grade_has_value(fldName, data_dict){
        //console.log( " ==== get_grade_has_value ====");
        //console.log( "    fldName", fldName);
        //console.log( "    data_dict", data_dict);

        // only show status when weight > 0 and grade/score has value
        // PR2022-06-04 debug: Hans Vlinkervleugel KAP had student with score 0.
        // Make has-Value true when score = 0 by using cescore != null instead of !!cescore
        let grade_has_value = false;
        if (data_dict) {
            if (fldName === 'se_status' && [1, 4].includes(data_dict.examperiod) && data_dict.weight_se){
                grade_has_value = !(data_dict.segrade == null || data_dict.segrade === '');
            } else if (fldName === 'ce_status' && [1, 2, 3].includes(data_dict.examperiod) && data_dict.weight_ce){
                // PR 2022-06-13 removed, SXM gives scores to schools when secret_exam
                // was: grade_has_value = (data_dict.secret_exam) ?
                //       data_dict.cegrade != null : data_dict.cescore != null;

                // PR2023-03-26 score can be 0, therenfore use cescore === null instead of cescore == null
                grade_has_value = !(data_dict.cescore === null || data_dict.cescore === '');
            };
        };

        return grade_has_value;
    };
// end of get_grade_has_value

//========= UploadApproveGrade  ============= PR2022-03-12 PR2023-02-02
    function UploadApproveGrade(tblName, fldName, examtype_2char, data_dict, auth_dict, requsr_auth_index,
                                is_published, is_blocked, new_is_approved_by_requsr_auth, el_input) {
        console.log( " ==== UploadApproveGrade ====");
        console.log( "    data_dict", data_dict);

// ---  change icon, before uploading PR2023-02-09 dont, until undo after error is in place

        // TODO PR2023-02-18 : const is_allowed_cluster = get_is_allowed_cluster(data_dict.cluster_id);
        const is_allowed_cluster = true;
        if (!is_allowed_cluster){
            b_show_mod_message_html(loc.approve_err_list.No_cluster_permission);
        } else {

            // - auth3 does not have to sign when secret exam (aangewezen examen)
            // - auth3 also does not have to sign when exemption (vrijstelling) PR2023-02-02

            // PR2023-02-07 debug: this is not correct value: !data_dict.examperiod === 4, must be: data_dict.examperiod !== 4
            const auth3_must_sign = (!data_dict.secret_exam && data_dict.examperiod !== 4);

            // - auth4 does not have to sign when secret exam (aangewezen examen) or when se-grade
            // - auth4 does not have to sign when se-grade
            // - auth4 also does not have to sign when exemption (vrijstelling) PR2023-02-02

            // PR2023-02-07 debug: this is not correct value: !data_dict.examperiod === 4, must be: data_dict.examperiod !== 4
            // dont change icon, before uploading, until undo after error is in place
            const auth4_must_sign = (!data_dict.secret_exam && data_dict.examperiod !== 4
                                        && ["pe_status", "ce_status"].includes(fldName));

            //const new_class_str = f_get_status_auth_iconclass(is_published, is_blocked,
            //                        auth_dict[1], auth_dict[2],
            //                        auth3_must_sign, auth_dict[3],
            //                        auth4_must_sign, auth_dict[4]);
            //el_input.className = new_class_str;

    // ---  upload changes
            // value of 'mode' determines if status is set to 'approved' or 'not
            // instead of using value of new_is_approved_by_requsr_authe,
            const mode = (new_is_approved_by_requsr_auth) ? "approve_save" : "approve_reset"
            const upload_dict = { table: tblName,
                                   mode: mode,
                                   is_single_update: true, // PR2023-03-25 to show msgbox, when multiple approbeve msg is shown in modal window
                                   mapid: data_dict.mapid,
                                   grade_pk: data_dict.id,
                                   field: fldName,
                                   examperiod: data_dict.examperiod,
                                   examtype: examtype_2char,
                                   auth_index: requsr_auth_index
                                };
            // UploadChanges(upload_dict, urls.url_grade_approve_single);
            UploadChanges(upload_dict, urls.url_grade_approve);
        };
    }  // UploadApproveGrade

//========= UploadBlockGrade  ============= PR2022-04-16
    function UploadBlockGrade(new_is_blocked) {
        //console.log( " ==== UploadBlockGrade ====");
        //console.log("new_is_blocked: ", new_is_blocked);

// ---  change icon, before uploading

        // check if cluster is allowed
        // TODO PR2023-02-18 : const is_allowed_cluster = get_is_allowed_cluster(mod_dict.data_dict.cluster_id);
        const is_allowed_cluster = true;
        //console.log("is_allowed_cluster: ", is_allowed_cluster);
        if (!is_allowed_cluster){
            const msg_txt = (new_is_blocked) ? loc.No_cluster_block_permission : loc.No_cluster_unblock_permission ;
            const msg_html = ["<div class='p-2'>", msg_txt, "</div>"].join("");
            b_show_mod_message_html(msg_html);
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
                    if ("approve_msg_html" in response){
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
                    if("multiple_occurrences_list" in response){
                        MLINKSTUD_response(response);
                    };
                    if("updated_multiple_occurrences" in response){
                        MLINKSTUD_response_update(response.updated_multiple_occurrences);
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

    function SBR_show_all_response() {  // PR2023-03-21
        console.log("===== SBR_show_all_response =====");
        // this is response of t_SBR_show_all

// ---  upload new setting and refresh page
        const datalist_request = {
                setting: {page: "page_grade"},

                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},
                subject_rows: {get: true},
                cluster_rows: {cur_dep_only: true},

                student_rows: {get: true},
                studentsubject_rows: {get: true},
                grade_rows: {cur_dep_only: true},

                all_exam_rows: {get: true}
            };
            DatalistDownload(datalist_request);
    };  // SBR_show_all_response

//=========  SBR_display_subject_cluster_student  ================ PR2022-03-03 PR2023-01-25
    function SBR_display_subject_cluster_student() {
        //console.log("===== SBR_display_subject_cluster_student =====");

        t_MSSSS_display_in_sbr("subject", setting_dict.sel_subject_pk);
        t_MSSSS_display_in_sbr("student", setting_dict.sel_student_pk);

        // PR2023-01-25 t_MSSSS_display_in_sbr_NEW uses dict instead of dictlist
        t_MSSSS_display_in_sbr_NEW("cluster", setting_dict.sel_cluster_pk);

        // hide itemcount
        t_set_sbr_itemcount_txt(loc, 0)

    };  // SBR_display_subject_cluster_student

// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2020-08-03 PR2022-02-17 PR2022-04-17
    function ModConfirmOpen(mode, el_input) {
        console.log(" -----  ModConfirmOpen   ----")
        console.log("mode", mode )
        console.log("mod_dict", mod_dict )
        // values of mode are : "approve", "block_grade", "prelim_ex2", "prelim_ex2a"

        // mod_dict already has values, got it in UploadStatus

        mod_dict.mode = mode;
        let hide_btn_save = false;
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

        } else if (["prelim_ex2", "prelim_ex2a"].includes(mode)){
            el_confirm_header.innerText = loc.Download_Ex_form;
            el_confirm_loader.classList.add(cls_visible_hide)
            const exform_txt = (mode === "prelim_ex2") ? loc.The_preliminary_ex2_form : loc.The_preliminary_ex2a_form;

            let msg_html = ["<p>", exform_txt, loc.will_be_downloaded_sing, "</p><p>", loc.Do_you_want_to_continue, "</p>"].join("");
            if ((mode === "prelim_ex2a")){
                msg_html += ["<div class='m-2 p-2 border_bg_message'>", loc.MAG_info.subheader_submit_ex2a_2,
                             loc.MAG_info.subheader_submit_ex2a_3, "</div>"].join(" ");
            };
            el_confirm_msg_container.innerHTML = msg_html

            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            if (el_modconfirm_link) {
                const url_str = (mode === "prelim_ex2") ? urls.url_grade_download_ex2 : urls.url_grade_download_ex2a;
                el_modconfirm_link.setAttribute("href", url_str);
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

        } else if (mode === "ex3"){
            el_confirm_header.innerText = loc.Download_Ex_form;
            const msg_html = "<p>" + loc.Ex3_btn_info_01 + "</p><p>" + loc.Ex3_btn_info_02 + "</p>"
            el_confirm_msg_container.innerHTML = msg_html;
            hide_btn_save = true;
            el_confirm_btn_cancel.innerText = loc.Close;
        // show modal
            $("#id_mod_confirm").modal({backdrop: true});
        };

        add_or_remove_class (el_confirm_btn_save, cls_hide, hide_btn_save);
    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2019-06-23
    function ModConfirmSave() {
        console.log(" --- ModConfirmSave --- ");
        console.log("mod_dict: ", mod_dict);

        if (mod_dict.mode === "approve"){
                UploadApproveGrade(mod_dict.tblName, mod_dict.fldName, mod_dict.examtype,
                            mod_dict.data_dict, mod_dict.auth_dict, mod_dict.requsr_auth_index,
                            mod_dict.is_published, mod_dict.is_blocked, mod_dict.new_is_approved_by_requsr_auth,
                            mod_dict.el_input) ;

        } else if (mod_dict.mode === "block_grade"){
                const new_blocked = !mod_dict.is_blocked;
                UploadBlockGrade(new_blocked) ;

        } else if (["prelim_ex2", "prelim_ex2a"].includes(mod_dict.mode)){
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

//=========  ModMessageHide  ================ PR2022-05-28
    function ModMessageHide() {
        console.log(" --- ModMessageHide --- ");
        const upload_dict = {hide_msg: true};
        UploadChanges(upload_dict, urls.url_user_modmsg_hide)
    }  // ModMessageHide

//=========  ModMessageClose  ================ PR2020-12-20
    function ModMessageClose() {
        //console.log(" --- ModMessageClose --- ");
        //console.log("mod_dict.el_focus: ", mod_dict.el_focus);
        if (mod_dict.el_focus) { set_focus_on_el_with_timeout(mod_dict.el_focus, 150)};
    };  // ModMessageClose

//========= MOD APPROVE GRADE ==================================== PR2022-03-09
    function MAG_Open (open_mode ) {
        console.log("===  MAG_Open  =====") ;
        console.log("    open_mode", open_mode) ;
        //console.log("    selected_btn", selected_btn, typeof selected_btn) ;
        console.log("    setting_dict.sel_examperiod", setting_dict.sel_examperiod, typeof setting_dict.sel_examperiod) ;
        console.log("    setting_dict.sel_examtype", setting_dict.sel_examtype) ;
        //console.log("    setting_dict.sel_lvlbase_code", setting_dict.sel_lvlbase_code) ;

        // open_mode = 'approve' or 'submit_ex2' or 'submit_ex2a'

        // TODO PR2022-11-28 debug: corrector can select id_MAG_examtype, must only show central exam
        b_clear_dict(mod_MAG_dict);

// --- check sel_examperiod
        let msg_html = null;
        if ([1,2,3, 4].includes(setting_dict.sel_examperiod) ){
            mod_MAG_dict.examperiod = setting_dict.sel_examperiod;
        } else {
            mod_MAG_dict.examperiod = null;
            msg_html = loc.Please_select_examperiod;
        };

        const is_examperiod_exemption = (mod_MAG_dict.examperiod === 4);

        if (msg_html) {
            b_show_mod_message_html(msg_html);
        } else {

// PR2022-03-13 debug: also check on allowed subjects, levels and clusters

// put info in mod_MAG_dict
            // open_mode are 'approve' 'submit_test' 'submit_save'
            mod_MAG_dict.mode = open_mode;
            mod_MAG_dict.step = 0;

            mod_MAG_dict.auth_index = setting_dict.sel_auth_index;

            console.log(" ???   mod_MAG_dict.auth_index", mod_MAG_dict.auth_index);

            mod_MAG_dict.submit_is_ok = false;
            mod_MAG_dict.is_reset = false;

            mod_MAG_dict.is_approve_mode = (open_mode === "approve");
            mod_MAG_dict.is_submit_ex2_mode = (open_mode === "submit_ex2");
            mod_MAG_dict.is_submit_ex2a_mode = (open_mode === "submit_ex2a");

// get selected auth_index (user can be chairpeson / secretary and examiner at the same time)
            MAG_get_sel_auth_index();

            if (setting_dict.sel_auth_index === 4 && is_examperiod_exemption &&  !["pe", "ce"].includes(setting_dict.sel_examtype) ){
                setting_dict.sel_examtype = null;
                b_show_mod_message_html(loc.MAG_info.corrector_cannot_approve_exem);

            } else {
        // PRE2023-03-25 when corrector and examtype = 'se', change to 'ce' instead of giving message
                if (setting_dict.sel_auth_index === 4 && !["pe", "ce"].includes(setting_dict.sel_examtype) ){
                    setting_dict.sel_examtype = "ce";
                    mod_MAG_dict.examtype = "ce";
                };
        // --- get sel_examtype
                MAG_get_sel_examtype(open_mode);
                console.log("    mod_MAG_dict.examperiod", mod_MAG_dict.examperiod);
                console.log("    mod_MAG_dict.examtype", mod_MAG_dict.examtype);

    // get has_permit
                mod_MAG_dict.permit_same_school = (permit_dict.requsr_same_school) ?
                                            (mod_MAG_dict.is_approve_mode && permit_dict.permit_approve_grade) ||
                                            (mod_MAG_dict.is_submit_ex2_mode && permit_dict.permit_submit_grade) ||
                                            (mod_MAG_dict.is_submit_ex2a_mode && permit_dict.permit_submit_grade) : false;

                mod_MAG_dict.has_permit = false;
                if (mod_MAG_dict.auth_index) {
                    if( mod_MAG_dict.is_approve_mode && permit_dict.permit_approve_grade){
                        mod_MAG_dict.has_permit = (permit_dict.requsr_same_school || permit_dict.requsr_role_corr);
                    } else if (mod_MAG_dict.is_submit_ex2_mode || mod_MAG_dict.is_submit_ex2a_mode){
                        mod_MAG_dict.has_permit = (permit_dict.requsr_same_school && permit_dict.permit_submit_grade)
                    };
                };


                console.log("    mod_MAG_dict.has_permit", mod_MAG_dict.has_permit);
                console.log("    mod_MAG_dict.auth_index", mod_MAG_dict.auth_index);

                if (mod_MAG_dict.has_permit && mod_MAG_dict.auth_index){

    // --- get header_txt and subheader_txt
                    const header_txt = (mod_MAG_dict.is_approve_mode) ? (is_examperiod_exemption) ? loc.Approve_exemptions :  loc.Approve_grades :
                                        (mod_MAG_dict.is_submit_ex2_mode) ? loc.Submit_Ex2_form :
                                        (mod_MAG_dict.is_submit_ex2a_mode) ? loc.Submit_Ex2A_form : null;
                    el_MAG_header.innerText = header_txt;
                    const subheader_txt = (mod_MAG_dict.is_approve_mode) ? (is_examperiod_exemption) ? loc.MAG_info.subheader_approve_exem : loc.MAG_info.subheader_approve :
                                          (mod_MAG_dict.is_submit_ex2_mode) ? loc.MAG_info.subheader_submit_ex2 :
                                          (mod_MAG_dict.is_submit_ex2a_mode) ? loc.MAG_info.subheader_submit_ex2a : null;
                    el_MAG_subheader.innerText = subheader_txt;

    // --- get examperiod and examtype text
                    // sel_examperiod 4 shows "Vrijstelling" as examperiod, replace by "Eerste tijdvak"
                    // sel_examperiod 12 shows "Eerste tijdvak / Tweede tijdvak" replace by "---"
                    // replace by First period
                    el_MAG_examperiod.innerText = ([1, 2, 3, 4].includes(setting_dict.sel_examperiod)) ? loc.examperiod_caption[setting_dict.sel_examperiod] : "---";

    // --- fill selectbox examtype
                    if (el_MAG_examtype){
                        // sel_examtype = "se", "sr", "pe", "ce",   PR2023-02-03 deprecated:  "reex", "reex03", "exem"

                        const examtype_list = []
                        if (setting_dict.sel_examperiod === 1){
                            if (!mod_MAG_dict.is_submit_ex2a_mode) {
                                examtype_list.push({value: 'se', caption: loc.examtype_caption.se})
                            };
                            if (!mod_MAG_dict.is_submit_ex2_mode) {
                                examtype_list.push({value: 'ce', caption: loc.examtype_caption.ce})
                            };
                        } else if (setting_dict.sel_examperiod === 2){
                            examtype_list.push({value: 'ce', caption: loc.examtype_caption.reex})
                        } else if (setting_dict.sel_examperiod === 3){
                            examtype_list.push({value: 'ce', caption: loc.examtype_caption.reex03})
                        } else if (setting_dict.sel_examperiod === 4){
                                examtype_list.push({value: 'se', caption: loc.examtype_caption.se});
                                examtype_list.push({value: 'ce', caption: loc.examtype_caption.ce});
                        };
                        t_FillOptionsFromList(el_MAG_examtype, examtype_list, "value", "caption",
                            loc.Select_examtype, loc.No_examtypes_found, setting_dict.sel_examtype);
                    };

    // --- hide filter subject, level and cluster when submitting Ex2 Ex2a form. Leave level visible if sel_dep_level_req, MPC must be able to submit per level
                    const show_subj_lvl_cls_container = setting_dict.sel_dep_level_req || mod_MAG_dict.is_approve_mode;
                    add_or_remove_class(el_MAG_subj_lvl_cls_container, cls_hide, !show_subj_lvl_cls_container);

    // --- hide select subject and cluster when submit mode
                    add_or_remove_class(el_MAG_subject.parentNode, cls_hide, !mod_MAG_dict.is_approve_mode);

                    add_or_remove_class(el_MAG_cluster.parentNode, cls_hide, !mod_MAG_dict.is_approve_mode || is_examperiod_exemption);

                    const level_abbrev = (setting_dict.sel_lvlbase_pk) ? setting_dict.sel_lvlbase_code : "<" + loc.All_levels + ">";
                    el_MAG_lvlbase.innerText = level_abbrev;

    // - set subject_text and cluster_text
                    MAG_set_subject_cluster_txt();

    // --- get approved_by
                    if (el_MAG_approved_by_label){
                        el_MAG_approved_by_label.innerText = ( (mod_MAG_dict.is_submit_ex2_mode) ? loc.Submitted_by : loc.Approved_by ) + ":"
                    }
                    if (el_MAG_approved_by){
                        el_MAG_approved_by.innerText = permit_dict.requsr_name;
                    }

    // --- fill selectbox auth_index
                    MAG_fill_select_authindex ();

    // --- reset ok button

//----------------
    // ---  show info container and delete button only in approve mode
                //console.log("...........is_submit", is_submit) ;
                add_or_remove_class(el_MAG_select_container, cls_hide, !mod_MAG_dict.is_approve_mode);
                add_or_remove_class(el_MAG_btn_delete, cls_hide, mod_MAG_dict.is_submit_ex2_mode || mod_MAG_dict.is_submit_ex2a_mode);

    // ---  reset el_MAG_input_verifcode
                el_MAG_input_verifcode.value = null;

    // ---  show info and hide loader
                    // PR2021-01-21 debug 'display_hide' not working when class 'image_container' is in same div
                    add_or_remove_class(el_MAG_loader, cls_hide, true);
                    //add_or_remove_class(el_MAG_btn_save, cls_hide, true);
                    //add_or_remove_class(el_MAG_btn_delete, cls_hide, true);

                    MAG_Save ("save");

    // --- open modal
                    $("#id_mod_approve_grade").modal({backdrop: true});
                };
            };
        };
    };  // MAG_Open

//=========  MAG_Save  ================
    function MAG_Save (save_mode) {
        console.log("===  MAG_Save  =====") ;
        console.log("    save_mode", save_mode) ;
        console.log("    mod_MAG_dict", mod_MAG_dict) ;
        console.log("    mod_MAG_dict.examperiod", mod_MAG_dict.examperiod) ;
        console.log("    mod_MAG_dict.examtype", mod_MAG_dict.examtype) ;
        // save_mode = 'save' or 'delete'

        if (permit_dict.permit_approve_grade || permit_dict.permit_submit_grade) {

            mod_MAG_dict.is_reset = (save_mode === "delete");

    console.log("    mod_MAG_dict.step", mod_MAG_dict.step)

            //  upload_modes are: 'approve_test', 'approve_save', 'approve_reset', 'submit_test', 'submit_save'
            const upload_dict = {
                table: "grade",
                form: (mod_MAG_dict.is_submit_ex2a_mode) ? "ex2a" : "ex2",
                auth_index: mod_MAG_dict.auth_index,
                examperiod: mod_MAG_dict.examperiod,
                examtype: mod_MAG_dict.examtype,
                level_abbrev: mod_MAG_dict.sel_lvlbase_code,
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
                    url_str = urls.url_send_email_verifcode;


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

    // ---  hide info box and msg box and input verifcode
            //add_or_remove_class(el_MAG_info_container, cls_hide, true);
            //add_or_remove_class(el_MAG_input_verifcode.parentNode, cls_hide, true);

    // ---  hide delete btn
            add_or_remove_class(el_MAG_btn_delete, cls_hide, true);

    console.log("    upload_dict", upload_dict);

            UploadChanges(upload_dict, url_str);
// hide modal when clicked on save btn when test_is_ok
            if (mod_MAG_dict.test_is_ok){
                //$("#id_mod_approve_grade").modal("hide");
            };

        console.log("--- from MAG_Save");
            MAG_SetInfoboxesAndBtns();
        }  // if (permit_dict.permit_approve_grade || permit_dict.permit_submit_grade)
    };  // MAG_Save


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//=========  MAG_SetInfoboxesAndBtns  ================ PR2023-02-23 PR2023-02-23
     function MAG_SetInfoboxesAndBtns(response) {
        console.log("===  MAG_SetInfoboxesAndBtns  =====") ;
        // called by MAG_Save and MAG_UpdateFromResponse
        // response is undefined when opening modal

        console.log("   mod_MAG_dict.step", mod_MAG_dict.step);

        // mod_MAG_dict.step 0 : AWP is de cijfers van de kandidaten aan het controleren..
        // mod_MAG_dict.step 1 : De selectie bevat 10 cijfers.
        // mod_MAG_dict.step 2 : We hebben een e-mail gestuurd met een 6-cijferige verificatiecode

        mod_MAG_dict.is_test = (response) ? false : true;
        mod_MAG_dict.test_is_ok = (response && response.test_is_ok) ? true : false;
        mod_MAG_dict.verification_is_ok = (response && response.verification_is_ok) ? true : false;
        mod_MAG_dict.verificationkey = (response && response.verificationkey) ? response.verificationkey : null;

        console.log("    is_test", mod_MAG_dict.is_test) ;
        console.log("    test_is_ok", mod_MAG_dict.test_is_ok) ;
        console.log("    verification_is_ok", mod_MAG_dict.verification_is_ok) ;
        console.log("    verificationkey", mod_MAG_dict.verificationkey) ;

        // is_test = true when opening modal, gets false when response has value
        const show_save_btn = (mod_MAG_dict.is_test || mod_MAG_dict.test_is_ok);

        const show_input_verifcode = (!mod_MAG_dict.is_approve_mode && mod_MAG_dict.verificationkey);

// ===== el_MAG_select_container
        // ---  in MAG_Open: show el_MAG_select_container and delete button only in approve mode

// ++++++++++++++++ MAG_info_container ++++++++++++++++
        let msg_info_html = null;
        let show_loader = false;
        if(response && response.approve_msg_html){
            msg_info_html = response.approve_msg_html;
        } else {
            let msg_info_txt = null;
            if (mod_MAG_dict.step === 0) {
                // step 0: when form opens and request to check is sent to server
                // tekst: "AWP is checking the %(sc_gr)s of the candidates"
                msg_info_txt = (mod_MAG_dict.examtype === "ce") ? loc.MAG_info.awp_is_checking_scores : loc.MAG_info.awp_is_checking_grades;
                show_loader = true;

            } else {
                if(mod_MAG_dict.is_approve_mode){
                    // is approve
                    if (mod_MAG_dict.step === 1) {
                    // response with checked subjects
                    // step 1: when response after check comes back from server
                    // msg_info_txt is in response

                    } else if (mod_MAG_dict.step === 2) {
                        // clicked on 'Approve'
                        // tekst: 'AWP is approving the subjects of the candidates'
                        msg_info_txt = (mod_MAG_dict.examperiod === 1) ? loc.MAG_info.approving_studsubj_ex1 : loc.MAG_info.approving_studsubj_ex4;
                        show_loader = true;
                    } else if (mod_MAG_dict.step === 3) {
                        // response 'approved'
                        // msg_info_txt is in response
                    };
                } else {
                    // is submit
                    if (mod_MAG_dict.step === 1) {
                        // response with checked subjects
                        // msg_info_txt is in response

                    } else if (mod_MAG_dict.step === 2) {
                        // clicked on 'Request_verificationcode'
                        // tekst: 'AWP is sending an email with the verification code'
                        // show textbox with 'You need a 6 digit verification code to submit the Ex form'
                        msg_info_txt = loc.MAG_info.requesting_verifcode;
                        show_loader = true;
                    } else if (mod_MAG_dict.step === 3) {
                        // response 'email sent'
                        // msg_info_txt is in response
                        show_input_verifcode = true;
                        disable_save_btn = !el_MAG_input_verifcode.value;
                    } else if (mod_MAG_dict.step === 4) {
                        // clicked on 'Submit Ex form'
                        // msg_info_txt is in response
                        show_loader = true;
                    } else if (mod_MAG_dict.step === 5) {
                        // response 'Exform submittes'
                        // msg_info_txt is in response
                    };
                };
            };
            if (msg_info_txt){
                msg_info_html = "<div class='p-2 border_bg_transparent'><p class='pb-2'>" +  msg_info_txt + "...</p></div>";
            };
        };

        console.log("  ???  msg_info_html", msg_info_html) ;
        el_MAG_info_container.innerHTML = msg_info_html;
        add_or_remove_class(el_MAG_info_container, cls_hide, !msg_info_html)

// --- show / hide loader
        add_or_remove_class(el_MAG_loader, cls_hide, !show_loader)


// ++++++++++++++++  el_MAG_info_request_verifcode and el_MAG_input_verifcode ++++++++++++++++
        const show_input_verifcodex = (response && response.approve_msg_html);


        add_or_remove_class(el_MAG_input_verifcode.parentNode, cls_hide, !show_input_verifcode);
        if (show_input_verifcode){set_focus_on_el_with_timeout(el_MAG_input_verifcode, 150)};

// ---  show  el_MAG_info_request_verifcode with text 'You need a 6 digit verification code ...
        // text of el_MAG_info_request_verifcode is embedded in  template modapprovegrade
        let show_info_request_verifcode = false;
        if(!mod_MAG_dict.is_approve_mode){
            if (mod_MAG_dict.step === 1) {
                show_info_request_verifcode = mod_MAG_dict.test_is_ok;
            };
        }
        add_or_remove_class(el_MAG_info_request_verifcode, cls_hide, !show_info_request_verifcode);
        add_or_remove_class(el_MAG_input_verifcode.parentNode, cls_hide, !show_input_verifcode);



    //console.log("mod_MAG_dict.step", mod_MAG_dict.step);
    //console.log("show_input_verifcode.step", show_input_verifcode);

////////////////////////////////////////////////
//=========  MAG_SetMsgContainer  ================ PR2021-02-08 PR2022-04-17

// --- show info and hide loader
        add_or_remove_class(el_MAG_loader, cls_hide, true);

        let show_msg_container = false;

        if (show_input_verifcode){
            show_msg_container = true;

            mod_MAG_dict.verificationkey = response.verificationkey


        } else if (!response){
            if (mod_MAG_dict.mode === "submit_ex2a" && !mod_MAG_dict.step){
            //el_MAG_info_container.className = "mt-2 p-2 border_bg_warning";
                //.innerHTML = loc.MAG_info.subheader_submit_ex2a_2 + " " + loc.MAG_info.subheader_submit_ex2a_3;
                show_msg_container = true;
            };

        } else if (response && !isEmpty(response.approve_msg_dict)){
            const msg_dict = response.approve_msg_dict;
            console.log("msg_dict", msg_dict);
            console.log("response.test_is_ok", response.test_is_ok);



            //console.log("mod_MAG_dict", mod_MAG_dict);

            const test_is_ok = (!!response.test_is_ok)

    // ---  hide loader
            add_or_remove_class(el_MAG_loader, cls_hide, true);
            let msg01_txt = null,  msg02_txt = null, msg03_txt = null, msg_04_txt = null;

    // make message container green when grades can be published, red otherwise
            // msg_dict.saved > 0 when grades are approved or published

            mod_MAG_dict.has_already_approved = (msg_dict && !!msg_dict.already_approved)
            mod_MAG_dict.has_already_published = (msg_dict && !!msg_dict.already_published)
            mod_MAG_dict.has_saved = msg_dict && !!msg_dict.saved;
            mod_MAG_dict.submit_is_ok = msg_dict && !!msg_dict.now_saved;  // submit_is_ok when records are saved

            show_msg_container = true
           // const border_class = (mod_MAG_dict.test_is_ok) ? "border_bg_valid" : "border_bg_invalid";
            //console.log("mod_MAG_dict.test_is_ok", mod_MAG_dict.test_is_ok) ;
            //const bg_class = (mod_MAG_dict.test_is_ok) ? "border_bg_valid" : "border_bg_invalid" // "border_bg_message"
            //el_MAG_info_container.className = bg_class
            let bg_class_ok = (mod_MAG_dict.test_is_ok || mod_MAG_dict.has_saved );
            const bg_class = (!bg_class_ok) ? "border_bg_invalid" : (msg_dict.warning) ? "border_bg_warning" : "border_bg_valid";

        };

//=========  MAG_SetInfoContainer  ================ PR2022-04-17

// put info text in el_MAG_info_container, only on open modal
        // el_MAG_info_container contains: 'Klik op 'Cijfers controleren' om de cijfers te controleren voordat ze worden ingediend.
        // only visible on open modal
        // Klik op 'Verificatiecode aanvragen', dan sturen we je een e-mail met de verificatiecode. De verificatiecode blijft 30 minuten geldig.

        let inner_html = "";
        if (mod_MAG_dict.step === 0) {
            // step 0: when form opens
            const ex2_key =  (mod_MAG_dict.is_approve_mode && mod_MAG_dict.examperiod === 4) ? "exem" :
                            ( ["se", "sr"].includes(setting_dict.sel_examtype) ) ? "ex2" :
                            ( ["pe", "ce"].includes(setting_dict.sel_examtype) ) ? "ex2a" : "ex2";
        //console.log("    ex2_key", ex2_key) ;
            const keys = (mod_MAG_dict.is_approve_mode) ?
                            ["approve_0_" + ex2_key, "approve_1_" + ex2_key, "approve_2_" + ex2_key] :
                            ["submit_0", "submit_1", "submit_2"];
            for (let i = 0, el, key; key = keys[i]; i++) {
                if (loc.MAG_info[key]){
                    inner_html += "<div><small>" + loc.MAG_info[key] + "</div></small>";
                }

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
        //add_or_remove_class(el_MAG_info_container, cls_hide, !inner_html)
        //el_MAG_info_container.innerHTML = inner_html
  // MAG_SetInfoContainer

// ################################



// ===== MAG_SetBtnSaveDeleteCancel =====
// ---  hide save button when not can_publish
        let btn_save_txt = loc.Check_grades;
        if (mod_MAG_dict.step === 0) {
            // mod_MAG_dict.step 0: opening modal
        } else if (mod_MAG_dict.step === 1) {
        // mod_MAG_dict.step 1 + response : return after check
            if (mod_MAG_dict.test_is_ok){
                btn_save_txt = (mod_MAG_dict.is_approve_mode) ? loc.Approve_grades : loc.Request_verifcode;
            };
        } else if (mod_MAG_dict.step === 2) {
            if (mod_MAG_dict.test_is_ok){
                btn_save_txt = (mod_MAG_dict.is_approve_mode) ? loc.Approve_grades :
                                (mod_MAG_dict.is_submit_ex2_mode) ? loc.Submit_Ex2_form :
                                (mod_MAG_dict.is_submit_ex2a_mode) ? loc.Submit_Ex2A_form : loc.Check_grades ;
            };
        };
        el_MAG_btn_save.innerText = btn_save_txt;
        el_MAG_btn_cancel.innerText = (show_save_btn) ? loc.Cancel : loc.Close;

        add_or_remove_class(el_MAG_btn_save, cls_hide, !show_save_btn);

// ---  show only the elements that are used in this tab
        const show_class = "tab_step_" + mod_MAG_dict.step;
        b_show_hide_selected_elements_byClass("tab_show", show_class, el_mod_approve_grade);

// ---  hide delete btn when reset or publish mode
        const show_delete_btn = (mod_MAG_dict.step === 1 && mod_MAG_dict.is_approve_mode && !!mod_MAG_dict.has_already_approved);
        add_or_remove_class(el_MAG_btn_delete, cls_hide, !show_delete_btn);
// ===== end of MAG_SetBtnSaveDeleteCancel =====

};  // MAG_SetInfoboxesAndBtns

//=========  MAG_UpdateFromResponse  ================ PR2021-02-08 PR2022-04-18 PR2023-02-23
    function MAG_UpdateFromResponse (response) {
        console.log("===  MAG_UpdateFromResponse  =====") ;
        console.log("    response", response) ;
        console.log("    mod_MAG_dict", mod_MAG_dict);

        mod_MAG_dict.step += 1;
        console.log(" >>>>>>> increased  mod_MAG_dict.step", mod_MAG_dict.step) ;


        // this is not working correctly yet, turned off for now PR2021-09-10
        // if false verfcode entered: try again
        if (mod_MAG_dict.step === 5 && !mod_MAG_dict.verification_is_ok ){
            //mod_MAG_dict.step = 3;
        };

    console.log("--- from MAG_UpdateFromResponse");
        MAG_SetInfoboxesAndBtns (response);

// hide modal after submitting, only when is_approve_mode
        if(mod_MAG_dict.step === 2 && mod_MAG_dict.is_approve_mode){
            //$("#id_mod_approve_grade").modal("hide");
        };

    };  // MAG_UpdateFromResponse


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

//=========  MAG_get_sel_auth_index  ================
    function MAG_get_sel_auth_index() {// PR2023-02-03
        console.log("===  MAG_get_sel_auth  =====") ;
    console.log("    mod_MAG_dict.is_approve_mode", mod_MAG_dict.is_approve_mode);

    console.log("    permit_dict.usergroup_list", permit_dict.usergroup_list) ;
   // console.log("    setting_dict.sel_auth_index", setting_dict.sel_auth_index) ;
        // parameters of this function are:
        //      permit_dict.usergroup_list
        //      setting_dict.sel_auth_index
        //      mod_MAG_dict.is_approve_mode
        //      mod_MAG_dict.examperiod
        // output is:
        //      mod_MAG_dict.requsr_auth_list
        //      mod_MAG_dict.auth_index

        let sel_auth_index = null;

// --- get list of auth_index of requsr
        const requsr_auth_list = [];
        if (permit_dict.usergroup_list.includes("auth1")){
            requsr_auth_list.push(1)
        };
        if (permit_dict.usergroup_list.includes("auth2")){
            requsr_auth_list.push(2)
        };
       // add examiner and commissiner only when mode = approve
        if (mod_MAG_dict.is_approve_mode){
            if (permit_dict.usergroup_list.includes("auth3")){
                // examiner doesnt hav e to approve exemption
                if ([1, 2, 3].includes(mod_MAG_dict.examperiod)) {
                    requsr_auth_list.push(3);
                };
            };
            if (permit_dict.usergroup_list.includes("auth4")){
                // auth4 (corrector) dont have to approve exemption
                // auth 4 (corrector) doesnt have to approve se grade  >> moved to MAG_get_sel_examtype
                //  was: if ([1, 2, 3].includes(mod_MAG_dict.examperiod) && mod_MAG_dict.examtype === "ce") {
                if ([1, 2, 3].includes(mod_MAG_dict.examperiod)) {
                    requsr_auth_list.push(4);
                };
            };
        };
    console.log("    requsr_auth_list", requsr_auth_list) ;
        // get selected auth_index (user can be chairperson / secretary and examiner at the same time)
        if (requsr_auth_list.length) {
            if (requsr_auth_list.includes(setting_dict.sel_auth_index)) {
                sel_auth_index = setting_dict.sel_auth_index;
            } else {
                sel_auth_index = requsr_auth_list[0];
                setting_dict.sel_auth_index = sel_auth_index;
            };
        };
        mod_MAG_dict.requsr_auth_list = requsr_auth_list;
        mod_MAG_dict.auth_index = sel_auth_index;

    console.log(" >> mod_MAG_dict.requsr_auth_list", mod_MAG_dict.requsr_auth_list) ;
    console.log(" >> mod_MAG_dict.auth_index", mod_MAG_dict.auth_index) ;
    };   // MAG_get_sel_auth_index

//=========  MAG_fill_select_authindex  ================
    function MAG_fill_select_authindex () {  // PR2023-02-06
        //console.log("----- MAG_fill_select_authindex -----") ;
        //console.log("    mod_MAG_dict.examperiod", mod_MAG_dict.examperiod);
        //console.log("    mod_MAG_dict.requsr_auth_list", mod_MAG_dict.requsr_auth_list);

    // --- fill selectbox auth_index
        if (el_MAG_auth_index){
            // auth_list = [{value: 1, caption: 'Chairperson'}, {value: 3, caption: 'Examiner'} )
            const auth_list = [];
            const cpt_list = [null, loc.Chairperson, loc.Secretary, loc.Examiner, loc.Corrector];
            for (let i = 0, auth_index; auth_index = mod_MAG_dict.requsr_auth_list[i]; i++) {
                auth_list.push({value: auth_index, caption: cpt_list[auth_index]});
            };
            t_FillOptionsFromList(el_MAG_auth_index, auth_list, "value", "caption",
                loc.Select_function, loc.No_functions_found, setting_dict.sel_auth_index);
        };
    };  // MAG_fill_select_authindex

//=========  MAG_get_sel_examtype  ================
    function MAG_get_sel_examtype (mode) {  // PR2023-02-03
        console.log("===  MAG_get_sel_examtype  =====") ;
        console.log("    mod_MAG_dict.examperiod", mod_MAG_dict.examperiod);
        console.log("    mod_MAG_dict.auth_index", mod_MAG_dict.auth_index);

        // parameters of this function are:
        //      mode
        //      mod_MAG_dict.examperiod
        //      mod_MAG_dict.auth_index
        // output is:
        //      mod_MAG_dict.examtype

        // sel_examtype = "se", "sr", "pe", "ce",   PR2023-02-03 deprecated:  "reex", "reex03", "exem"

        let sel_examtype = null;
        if (mod_MAG_dict.examperiod){
            if (mode === 'approve'){
                if ([1, 2].includes(mod_MAG_dict.auth_index) ){
                    // chairperson / secretary can approve all se - ce
                    if ([1, 4].includes(mod_MAG_dict.examperiod) ){
                        sel_examtype = (["se", "ce"].includes(setting_dict.sel_examtype) ) ? setting_dict.sel_examtype : "se";
                    } else if ([2, 3].includes(mod_MAG_dict.examperiod) ){
                        sel_examtype = "ce";
                    };
                } else if (mod_MAG_dict.auth_index === 3) {
                    // examiner can approve se and  ce, except exemptiion-se-ce
                    if (mod_MAG_dict.examperiod === 1 ){
                        sel_examtype = (["se", "ce"].includes(setting_dict.sel_examtype) ) ? setting_dict.sel_examtype : "se";
                    } else if ([2, 3].includes(mod_MAG_dict.examperiod) ){
                        sel_examtype = "ce";
                    };
                } else if (mod_MAG_dict.auth_index === 4) {
                    // corrector can only approve ce, except exemptiion-ce
                    if ([1, 2, 3].includes(mod_MAG_dict.examperiod) ){
                        sel_examtype = "ce";
                    };
                };
            } else if (mode === "submit_ex2") {
                sel_examtype = "se";
            } else if (mode === "submit_ex2a") {
                sel_examtype = "ce";
            };
        };

        mod_MAG_dict.examtype = sel_examtype;

        console.log("    mod_MAG_dict.examtype", mod_MAG_dict.examtype);
    };  // MAG_get_sel_examtype

//=========  MAG_ExamtypeChange  ================ PR2022-05-29 PR2023-02-03
    function MAG_ExamtypeChange (el_select) {
        console.log("===  MAG_ExamtypeChange  =====") ;
        console.log("    el_select.value", el_select.value) ;

// ---  put new  auth_index in mod_MAG_dict and setting_dict
        mod_MAG_dict.examtype = el_select.value;
        setting_dict.sel_examtype = el_select.value;
        console.log("    mod_MAG_dict.examtype", mod_MAG_dict.examtype) ;

// clear infobox, reser save btn
        mod_MAG_dict.step = 0;
        mod_MAG_dict.is_test = true;

        MAG_get_sel_auth_index();
        MAG_fill_select_authindex();

        console.log("--- from MAG_ExamtypeChange");
        MAG_SetInfoboxesAndBtns();

    }; // MAG_ExamtypeChange

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

// clear infobox, reser save btn
        mod_MAG_dict.step = 0;
        mod_MAG_dict.is_test = true;

        console.log("--- from MAG_UploadAuthIndex");
        MAG_SetInfoboxesAndBtns();

    }; // MAG_UploadAuthIndex

    function MAG_set_subject_cluster_txt() { // PR2023-02-11
        //console.log("----- MAG_set_subject_cluster_txt -----") ;

        const allowed_subjectname_nl_arr = [];
        const allowed_clustername_arr = [];

    // loop through allowed_subjbases - contains allowed subjects of this department

// +++++++++ if there is a sel_subject_pk +++++++++++++++++++++
        if(setting_dict.sel_subject_pk){

    // - get sel_subjbase_pk from subject_rows
            // TODO: change setting_dict.sel_subject_pk to setting_dict.sel_subjbase_pk
            let sel_subjbase_pk = null, sel_subject_name_nl = null;
            const [middle_index, found_dict, compare] = b_recursive_integer_lookup(subject_rows, "id", setting_dict.sel_subject_pk);

            if (found_dict){
                sel_subjbase_pk = found_dict.base_id;
                sel_subject_name_nl = (found_dict.name_nl) ? found_dict.name_nl : "---";

    // - check if sel_subjbase_pk is in allowed_subjbases
                const is_allowed_subjbase_pk = (permit_dict.allowed_subjbases && permit_dict.allowed_subjbases.length) ?
                    (permit_dict.allowed_subjbases.includes(sel_subjbase_pk)) ? true : false : true;
                if (is_allowed_subjbase_pk ){

    // +++++++++ if there is a sel_cluster_pk +++++++++++++++++++++++++++
                    if(setting_dict.sel_cluster_pk){
                        const cluster = cluster_dictsNEW["cluster_" + cluster_pk];
                        if (cluster && cluster.subjbase_id === setting_dict.sel_cluster_pk) {
                   // check if sel_subsel_cluster_pkjbase_pk is in allowed_clusters
                            const is_allowed_cluster = (permit_dict.allowed_clusters && permit_dict.allowed_clusters.length) ?
                                (permit_dict.allowed_clusters.includes(setting_dict.sel_cluster_pk)) ? true : false : true;
                            if (is_allowed_cluster){
                                has_allowed_cluster = true;
                                allowed_subjectname_nl_arr.push(cluster.name)
                                allowed_clustername_arr.push(sel_subject_name_nl)

                            };
                        };

    // +++++++++ if there are allowed_clusters +++++++++++++++++++++++++++
                    } else if (permit_dict.allowed_clusters && permit_dict.allowed_clusters.length) {

                        for (let i = 0, cluster_pk; cluster_pk = permit_dict.allowed_clusters[i]; i++) {
                            const cluster = cluster_dictsNEW["cluster_" + cluster_pk];

                            if (cluster && cluster.subjbase_id === sel_subjbase_pk) {

                                allowed_subjectname_nl_arr.push(sel_subject_name_nl);
                                allowed_clustername_arr.push(cluster.name);
                                break;
                            };
                        };
    // +++++++++ if there is no selected cluster and no allowed_clusters +++++++++++++++++++++++++++
                    } else {
                console.log(" +++   sel_subject_name_nl", sel_subject_name_nl);
                        allowed_subjectname_nl_arr.push(sel_subject_name_nl);
                    };
                };

            };
// +++ end of if there is a sel_subject_pk

// +++++++++ if there are allowed_subjbases +++++++++++++++++++++
        } else if (permit_dict.allowed_subjbases && permit_dict.allowed_subjbases.length){

    console.log("  >>>>>>>>>>>>>>> +++  permit_dict.allowed_subjbases", permit_dict.allowed_subjbases);
            for (let i = 0, subjbase_pk; subjbase_pk = permit_dict.allowed_subjbases[i]; i++) {
                let sel_subjbase_pk = null, sel_subject_name_nl = null;
                for (let j = 0, subject_dict; subject_dict = subject_rows[j]; j++) {
                    if (subject_dict.base_id === subjbase_pk){
                        sel_subjbase_pk = subject_dict.base_id;
                        sel_subject_name_nl = subject_dict.name_nl;
                        break;
                    };
                };

                if (sel_subjbase_pk){

    // +++++++++ if there is a sel_cluster_pk +++++++++++++++++++++++++++
                    if(setting_dict.sel_cluster_pk){
                console.log(" +++ setting_dict.sel_cluster_pk", setting_dict.sel_cluster_pk);
                        const cluster = cluster_dictsNEW["cluster_" + cluster_pk];
                console.log("    cluster", cluster);
                        if (cluster && cluster.subjbase_id === setting_dict.sel_cluster_pk) {
                // check if sel_subsel_cluster_pkjbase_pk is in allowed_clusters
                            const is_allowed_cluster = (permit_dict.allowed_clusters && permit_dict.allowed_clusters.length) ?
                                (permit_dict.allowed_clusters.includes(setting_dict.sel_cluster_pk)) ? true : false : true;
                            if (is_allowed_cluster){
                                has_allowed_cluster = true;
                                allowed_subjectname_nl_arr.push(cluster.name)
                                allowed_clustername_arr.push(sel_subject_name_nl)
                console.log("    has_allowed_cluster", has_allowed_cluster);
                            };
                        };

    // +++++++++ if there are allowed_clusters +++++++++++++++++++++++++++
                    } else if (permit_dict.allowed_clusters && permit_dict.allowed_clusters.length) {
                console.log("  +++  permit_dict.allowed_clusters", permit_dict.allowed_clusters);
                        for (let i = 0, cluster_pk; cluster_pk = permit_dict.allowed_clusters[i]; i++) {
                            const cluster = cluster_dictsNEW["cluster_" + cluster_pk];
                console.log("    cluster", cluster);
                            if (cluster && cluster.subjbase_id === sel_subjbase_pk) {
                console.log("    sel_subject_name_nl", sel_subject_name_nl);
                                allowed_subjectname_nl_arr.push(sel_subject_name_nl);
                                allowed_clustername_arr.push(cluster.name);
                                break;
                            };
                        };

    // +++++++++ if there is no selected cluster and no allowed_clusters +++++++++++++++++++++++++++
                    } else {
                console.log(" +++   sel_subject_name_nl", sel_subject_name_nl);
                        if (!allowed_subjectname_nl_arr.includes(sel_subject_name_nl)){
                            allowed_subjectname_nl_arr.push(sel_subject_name_nl);
                        };
                    };

                };
            };



// +++ end of if there are allowed_subjbases

// +++++++++ if there is no selected subject and no allowed_subjbasess +++++++++++++++++++++++++++
        } else {

    // +++++++++ if there is a sel_cluster_pk +++++++++++++++++++++++++++
            if(setting_dict.sel_cluster_pk){
                console.log(" +++ setting_dict.sel_cluster_pk", setting_dict.sel_cluster_pk);

    // +++++++++ if there are allowed_clusters +++++++++++++++++++++++++++
            } else if (permit_dict.allowed_clusters && permit_dict.allowed_clusters.length) {

    // +++++++++ if there is no selected cluster and no allowed_clusters +++++++++++++++++++++++++++
            } else {
                allowed_subjectname_nl_arr.push(["<", loc.All_subjects, ">"].join(""));
            };
        };

        el_MAG_cluster.innerText = (allowed_clustername_arr.length) ? allowed_clustername_arr.join(", ") : null;

        el_MAG_subject.innerText = (allowed_subjectname_nl_arr.length) ? allowed_subjectname_nl_arr.join(", ") : "---";
    };  // MAG_set_subject_cluster_txt

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
                if(grade_dict.subj_code) { headertext += grade_dict.subj_name_nl};
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
                const is_selected_index = (index === mod_note_dict.sel_icon)
                add_or_remove_class(el, "note_1_" + index, is_selected_index, "note_0_" + index )
            };
        };

        // when internal, add schoolbase of request_user (NOT of selected school) to intern_schoolbase
        // when external, field intern_schoolbase is null
        mod_note_dict.intern_schoolbase_pk = (mod_note_dict.is_internal) ? setting_dict.requsr_schoolbase_pk : null;

        //console.log("mod_note_dict", mod_note_dict) ;
    };  // ModNote_SetInternalExternal

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

                student_rows: {cur_dep_only: true},
                studentsubject_rows: {cur_dep_only: true},
                grade_rows: {cur_dep_only: true},

                all_exam_rows: {get: true}
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
                RefreshDatarowItem(tblName, field_setting, data_rows, update_dict, skip_show_ok);
            }
        } else if (!is_update) {
            // empty the data_rows when update_rows is empty PR2021-01-13 debug forgot to empty data_rows
            // PR2021-03-13 debug. Don't empty de data_rows when is update. Returns [] when no changes made
           data_rows = [];
        }
    }  //  RefreshDataRows

//=========  RefreshDatarowItem  ================ PR2020-08-16 PR2020-09-30 PR2021-09-20 PR2022-03-03
    function RefreshDatarowItem(tblName, field_setting, data_rows, update_dict, skip_show_ok) {
        //console.log(" --- RefreshDatarowItem  ---");
        //console.log("tblName", tblName);
        //console.log("field_setting", field_setting);
   // console.log("update_dict", update_dict);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

            const is_created = (!!update_dict.created);

    // ---  get list of hidden columns
            const col_hidden = b_copy_array_to_new_noduplicates(mod_MCOL_dict.cols_hidden);

// ---  get list of columns that are not updated because of errors
            const error_columns = (update_dict.err_fields) ? update_dict.err_fields : [];
    //console.log("error_columns", error_columns);

            let updated_columns = [];

// ++++ created ++++
            // grades cannot be created on this page
            // PR2022-02-19 wrong: when uploading exemptioon it creates new grades

            // PR2021-06-16 from https://stackoverflow.com/questions/586182/how-to-insert-an-item-into-an-array-at-a-specific-index-javascript
            //arr.splice(index, 0, item); will insert item into arr at the specified index
            // (deleting 0 items first, that is, it's just an insert).

            if(is_created){
    // ---  first remove key 'created' from update_dict
                delete update_dict.created;

    // ---  add new item in data_rows at end
                data_rows.push(update_dict);

    // ---  create row in table., insert in alphabetical order
                const new_tblRow = CreateTblRow(tblName, field_setting, update_dict, col_hidden)

                if(new_tblRow){
    // --- add1 to item_count and show total in sidebar
                    selected.item_count += 1;
    // ---  scrollIntoView,
                    new_tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' });

    // ---  make new row green for 2 seconds,
                    ShowOkElement(new_tblRow);
                };

// ++++ deleted ++++
            // grades cannot be deleted on this page

            } else {
    // +++ get existing data_dict from data_rows. data_rows is ordered by grade.id'
                const grade_pk = update_dict.id;
                const data_dict = get_gradedict_by_gradepk(grade_pk);

    // ++++ updated row +++++++++++
    // ---  create list of updated fields
                if(!isEmpty(data_dict)){
                    for (const [key, new_value] of Object.entries(update_dict)) {

        // ---  if value has changed: add field to updated_columns before updating data_dict
                        // PR2022-05-25 this doesnt work: se_blocked is boolean, se_status is int.
                        //const mapped_key =  (key === "se_blocked") ? "se_status" :
                                                //(key === "sr_blocked") ? "sr_status" :
                                                //(key === "pe_blocked") ? "pe_status" :
                                                //(key === "ce_blocked") ? "ce_status" : key;
                        if (key in data_dict && new_value !== data_dict[key]) {


        // ---  first put key in updated_columns
                            updated_columns.push(key);
        // ---  then put updated value back in data_map
                            data_dict[key] = update_dict[key];
                            if(key === "ce_exam_id"){
                            // also update download_conv_table when ce_exam_id has changed
                                updated_columns.push("download_conv_table");
                            };
                            if(key === "exemption_imported"){
                                if (!("se_status" in updated_columns)) {updated_columns.push("se_status")};
                                if (!("ce_status" in updated_columns)) {updated_columns.push("ce_status")};
                            };
                        };
                    };
        //console.log("updated_columns", updated_columns);
        //console.log("data_dict", data_dict);

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
        //console.log("el_fldName", el_fldName);
                                    const is_updated_field = updated_columns.includes(el_fldName);
                                    const is_err_field = error_columns.includes(el_fldName);
        //console.log("     is_updated_field", is_updated_field);
        //console.log("     is_err_field", is_err_field);
            // update field and make field green when field name is in updated_columns
                                    if(is_updated_field){
                                        UpdateField(el, update_dict);
                                        if(!skip_show_ok){ShowOkElement(el)};
                                    } else if( is_err_field){
            // make field red when error and reset old value after 2 seconds
                                        reset_element_with_errorclass(el, update_dict)
                                    };
                                };
                            };
                        };  //  for (let i = 1, el_fldName, td
                     };  //  if(tblRow && (updated_columns.length || error_columns.length)){
                };  //  if(!isEmpty(data_dict))
            };
        };  //  if(!isEmpty(update_dict)){
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


//========= HandleFilterStatus  =============== PR2022-05-01
    function HandleFilterStatus(el_input) {
        console.log( "===== HandleFilterStatus  ========= ");
        console.log( "el_input", el_input);

    // - get col_index  from  el_input
        // PR2021-05-30 debug: use cellIndex instead of attribute data-colindex,
        // because data-colindex goes wrong with hidden columns
        // was:  const col_index = get_attr_from_el(el_input, "data-colindex")
        const col_index = el_input.parentNode.cellIndex;

    // - get filter_tag from  el_input
        const filter_tag =  get_attr_from_el(el_input, "data-filtertag")
        const field_name = get_attr_from_el(el_input, "data-field")
    console.log( "    col_index", col_index);
    console.log( "    field_name", field_name);
    console.log( "    filter_dict", filter_dict);

    // - get current value of filter from filter_dict, set to '0' if filter doesn't exist yet
        const filter_array = (col_index in filter_dict) ? filter_dict[col_index] : [];
        const filter_value = (filter_array[1]) ? filter_array[1] : 0;

    console.log( "filter_array", filter_array);
    console.log( "filter_value", filter_value);

        //let icon_class = "diamond_3_4", title = "";
        // default filter triple '0'; is show all, '1' is show not fully approved, '2' show fully approved / submitted '3' show blocked

// - toggle filter value
        let value_int = (Number(filter_value)) ? Number(filter_value) : 0;
console.log( "......filter_value", filter_value);
        value_int += 1;
        if (value_int > 8 ) { value_int = 0};

        // convert 0 to null, otherwise  "0" will not filter correctly
        let new_value = (value_int) ? value_int.toString() : null;
    console.log( "new_value", new_value);

// - get new icon_class
// - get new icon_class
        const icon_class =  (new_value === "8") ? "diamond_1_4" :   // blocked - full red diamond
                        (new_value === "7") ? "diamond_0_4" :   // submitted - full blue diamond
                        (new_value === "6") ? "diamond_3_3" : // all approved - full black diamond

                        (new_value === "5") ? "diamond_1_3" :  // not approved by second corrector

                        (new_value === "4") ? "diamond_2_3" :  // not approved by examiner
                        (new_value === "3") ? "diamond_3_1" :  // not approved by secretary
                        (new_value === "2") ? "diamond_3_2" :  // not approved by chairperson
                        (new_value === "1") ? "diamond_0_0" :  // none approved - outlined diamond
                        "tickmark_0_0";
        const title =  (new_value === "8") ? loc.grade_status["8"] : // blocked - full red diamond
                        (new_value === "7") ? loc.grade_status["7"] :   // submitted - full blue diamond
                        (new_value === "6") ? loc.grade_status["6"] : // all approved - full black diamond

                        (new_value === "5") ? loc.grade_status["5"] :  // not approved by second corrector

                        (new_value === "4") ? loc.grade_status["4"] :  // not approved by examiner
                        (new_value === "3") ? loc.grade_status["3"] :  // not approved by secretary
                        (new_value === "2") ? loc.grade_status["2"] :  // not approved by chairperson
                        (new_value === "1") ? loc.grade_status["1"] :  // none approved - outlined diamond
                        "tickmark_0_0";
        //icon_class = (new_value === 3) ? "diamond_1_4" : (new_value === 2) ? "diamond_3_3" : (new_value === 1) ? "diamond_1_1" : "diamond_3_4";
        //const title = (new_value === 3) ? loc.Show_blocked :
        //(new_value === 2) ? loc.Show_fully_approved : (new_value === 1) ?loc.Show_not_fully_approved : "";

        el_input.className = icon_class;
        el_input.title = title
    console.log( "icon_class", icon_class);

// - put new filter value in filter_dict
        filter_dict[col_index] = [filter_tag, new_value]
    console.log( "filter_dict", filter_dict);

        t_Filter_TableRows(tblBody_datatable, filter_dict, selected, loc.Subject, loc.Subjects);

    };  // HandleFilterStatus


//========= ResetFilterRows  ====================================
    function ResetFilterRows() {  // PR2019-10-26 PR2020-06-20 PR2022-01-26
        console.log( "===== ResetFilterRows  ========= ");
        console.log( "    filter_dict", filter_dict);

        b_clear_dict(filter_dict);
        t_reset_filterrow(tblHead_datatable);
            // ---  show total in sidebar
        t_set_sbr_itemcount_txt();

        t_Filter_TableRows(tblBody_datatable, filter_dict, selected, loc.Subject, loc.Subjects);
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
                grade_rows: {cur_dep_only: true},

                all_exam_rows: {get: true}
            };
        DatalistDownload(datalist_request);
    }  // MSED_Response

//=========  MSSSS_school_response  ================ PR2023-03-29
    function MSSSS_school_response(tblName, selected_dict, sel_schoolbase_pk) {
        console.log( "===== MSSSS_school_response ========= ");
        console.log( "tblName", tblName);
        console.log( "sel_schoolbase_pk", sel_schoolbase_pk, typeof sel_schoolbase_pk);
        console.log( "selected_dict", selected_dict);
        // arguments of MSSSS_response are set in t_MSSSS_Save or t_MSSSS_Save_NEW

// reset text dep and school in headerbar
        el_hdrbar_department.innerText = null;
        el_hdrbar_school.innerText = null;

// reset cluster and student
        setting_dict.sel_cluster_pk = null;
        setting_dict.sel_student_pk = null;

        SBR_display_subject_cluster_student();

// ---  upload new setting and refresh page
        const datalist_request = {
                setting: {page: "page_grade",
                        sel_schoolbase_pk: sel_schoolbase_pk,
                        sel_cluster_pk: null,
                        sel_student_pk: null
                        },
                school_rows: {get: true},
                department_rows: {get: true},
                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},
                subject_rows: {get: true},
                cluster_rows: {cur_dep_only: true},

                student_rows: {get: true},
                studentsubject_rows: {get: true},
                grade_rows: {get: true},

                all_exam_rows: {get: true}
            };
            DatalistDownload(datalist_request);

    };  // MSSSS_school_response

//=========  MSSSS_subject_response  ================ PR2023-03-30
    function MSSSS_subject_response(tblName, selected_dict, sel_subject_pk) {
        console.log( "===== MSSSS_subject_response ========= ");
        console.log( "tblName", tblName);
        console.log( "sel_subject_pk", sel_subject_pk, typeof sel_subject_pk);
        console.log( "selected_dict", selected_dict);
        // arguments of MSSSS_response are set in t_MSSSS_Save or t_MSSSS_Save_NEW
        // when changing subject, only update settings, dont use DatalistDownload but filter on page

        // 'all subjects' has value -1
        if(sel_subject_pk === -1) { sel_subject_pk = null};

        setting_dict.sel_subject_pk = sel_subject_pk;
        setting_dict.sel_subject_name = (selected_dict && selected_dict.name_nl) ? selected_dict.name_nl : null;

// when selecting cluster: also set subject to the subject of this cluster
        setting_dict.sel_cluster_pk = null;
        setting_dict.sel_cluster_name = null;
        setting_dict.sel_student_pk = null;
        setting_dict.sel_student_name = null;

// ---  upload new setting
        const upload_dict = {selected_pk: {
                                sel_subject_pk: sel_subject_pk,
                                sel_cluster_pk: null,
                                sel_student_pk: null
                            }};
        b_UploadSettings (upload_dict, urls.url_usersetting_upload);

        SBR_display_subject_cluster_student();

        FillTblRows();
        //HandleBtnSelect(null, true)  // true = skip_upload
        // also calls: FillTblRows(), UpdateHeader()

    };  // MSSSS_subject_response

//=========  MSSSS_cluster_response  ================ PR2023-03-30
    function MSSSS_cluster_response(tblName, selected_dict, sel_cluster_pk) {
        console.log( "===== MSSSS_cluster_response ========= ");
        console.log( "tblName", tblName);
        console.log( "sel_cluster_pk", sel_cluster_pk, typeof sel_cluster_pk);
        console.log( "selected_dict", selected_dict);
        // arguments of MSSSS_response are set in t_MSSSS_Save or t_MSSSS_Save_NEW
        // when changing cluster, only update settings, dont use DatalistDownload but filter on page

        // 'all clusters' has value -1
        if(sel_cluster_pk === -1) { sel_cluster_pk = null};

        setting_dict.sel_cluster_pk = sel_cluster_pk;
        setting_dict.sel_cluster_name = (selected_dict && selected_dict.name) ? selected_dict.name : null;

// when selecting cluster: also set subject to the subject of this cluster
        // dont reset subject when subject of selected cluster is the same as selected subject PR2023-03-30
        if (!selected_dict || selected_dict.subject_id !== setting_dict.sel_subject_pk){
            setting_dict.sel_subject_pk = null;
            setting_dict.sel_subject_name = null;
        };
        setting_dict.sel_student_pk = null;
        setting_dict.sel_student_name = null;

// ---  upload new setting
        const upload_dict = {selected_pk: {
                                sel_cluster_pk: sel_cluster_pk,
                                sel_subject_pk: null,
                                sel_student_pk: null
                            }};
        b_UploadSettings (upload_dict, urls.url_usersetting_upload);

        SBR_display_subject_cluster_student();

        FillTblRows();

    };  // MSSSS_cluster_response

//=========  MSSSS_student_response  ================ PR2023-03-30
    function MSSSS_student_response(tblName, selected_dict, sel_student_pk) {
        console.log( "===== MSSSS_student_response ========= ");
        console.log( "tblName", tblName);
        console.log( "sel_student_pk", sel_student_pk, typeof sel_student_pk);
        console.log( "selected_dict", selected_dict);
        // arguments of MSSSS_response are set in t_MSSSS_Save or t_MSSSS_Save_NEW
        // when changing student, only update settings, dont use DatalistDownload but filter on page

        // 'all clusters' has value -1
        if(sel_student_pk === -1) { sel_student_pk = null};

        setting_dict.sel_student_pk = sel_student_pk;
        setting_dict.sel_student_name = (selected_dict && selected_dict.fullname) ? selected_dict.fullname : null;

// when selecting cluster: also set subject to the subject of this cluster
        setting_dict.sel_subject_pk = null;
        setting_dict.sel_subject_name = null;
        setting_dict.sel_cluster_pk = null;
        setting_dict.sel_cluster_name = null;

// ---  upload new setting
        const upload_dict = {selected_pk: {
                                sel_student_pk: sel_student_pk,
                                sel_subject_pk: null,
                                sel_cluster_pk: null
                            }};
        b_UploadSettings (upload_dict, urls.url_usersetting_upload);

        SBR_display_subject_cluster_student();

        FillTblRows();

    };  // MSSSS_student_response


// +++++++++ MOD EX3 FORM++++++++++++++++ PR2021-10-06
    function MEX3_Open(){
        console.log(" -----  MEX3_Open   ----")
            console.log("setting_dict.sel_examperiod", setting_dict.sel_examperiod)
        mod_MEX3_dict = {};
        //PR2022-03-15 debug tel Richard Westerink: gives 'Ex3 Exemption'
        if (![1,2,3].includes(setting_dict.sel_examperiod)){
            b_show_mod_message_html("<div class='p-2'>" + loc.Please_select_examperiod + "</div>");

        } else {
            console.log("level_map", level_map)
    // ---  fill select level or hide
            if (setting_dict.sel_dep_level_req){
                // HTML code "&#60" = "<" HTML code "&#62" = ">";
                const first_item = ["&#60", loc.All_levels, "&#62"].join("");
                 el_MEX3_select_level.innerHTML = t_FillOptionLevelSectorFromMap("level", "base_id", level_map,
                    setting_dict.sel_depbase_pk, null, first_item);
            }
    // hide option 'level' when havo/vwo
            if(el_MEX3_layout_option_level){
                add_or_remove_class(el_MEX3_layout_option_level, cls_hide, !setting_dict.sel_dep_level_req);
            }
            if(el_MEX3_select_layout){
                const select_size = (setting_dict.sel_dep_level_req) ? "4" : "3";
                el_MEX3_select_layout.setAttribute("size", select_size);
            }
    // hide element 'select_level' when havo/vwo
            add_or_remove_class(el_MEX3_select_level.parentNode, cls_hide, !setting_dict.sel_dep_level_req);

    // - set header text
            el_id_MEX3_hdr.innerText = [loc.Ex3, loc.Proces_verbaal_van_Toezicht].join("  -  ");

    // ---  reset layout options
            MEX3_reset_layout_options();

    // ---  reset tblBody available and selected
            el_MEX3_tblBody_available.innerText = null;
            el_MEX3_tblBody_selected.innerText = null;

    // ---  disable save btn
            el_MEX3_btn_save.disabled = true;

    // ---  get info from server
            MEX3_getinfo_from_server()

    // ---  show modal
            $("#id_mod_selectex3").modal({backdrop: true});
        };
    };  // MEX3_Open

//========= MEX3_Save  ============= PR2021-10-07
    function MEX3_Save(){
        console.log(" -----  MEX3_Save   ----")
        const subject_list = [];

// ---  loop through id_MEX3_select_level and collect selected lvlbase_pk's
        const sel_lvlbase_pk_list = MEX3_get_sel_lvlbase_pk_list();
        console.log("mod_MEX3_dict.sel_lvlbase_pk_list", mod_MEX3_dict.sel_lvlbase_pk_list)

// ---  get de selected value of
        const selected_layout_value = (el_MEX3_select_layout.value) ? el_MEX3_select_layout.value : "none";

// ---  loop through mod_MEX3_dict.subject_rows and collect selected subject_pk's
        // PR2021-10-09 debug: also filter lvlbase_pk, because they stay selected when unselecting level
        for (let i = 0, subj_row; subj_row = mod_MEX3_dict.subject_rows[i]; i++) {
            if(subj_row.selected){
                let add_row = false;
                if (mod_MEX3_dict.lvlbase_pk_list && mod_MEX3_dict.lvlbase_pk_list.length){
                    if (subj_row.lvlbase_id_arr && subj_row.lvlbase_id_arr.length){
                         for (let x = 0, lvlbase_id; lvlbase_id = subj_row.lvlbase_id_arr[x]; x++) {
                            if (mod_MEX3_dict.lvlbase_pk_list.includes(lvlbase_id)){
                                add_row = true;
                                break
                    }}};
                } else {
                    add_row = true;
                }
                if (add_row){
                    subject_list.push(subj_row.subj_id);
                };
            }  ;
        };

        if(subject_list.length){
            const upload_dict = {
                subject_list: subject_list,
                sel_layout: selected_layout_value,
                lvlbase_pk_list: sel_lvlbase_pk_list
            };

        // convert dict to jason and add as parameter in link
            const upload_str = JSON.stringify(upload_dict);
            const href_str = urls.url_ex3_download.replace("-", upload_str);

        console.log("href_str", href_str)

            const el_MEX3_save_link = document.getElementById("id_MEX3_save_link");
            el_MEX3_save_link.href = href_str;

        console.log("el_MEX3_save_link", el_MEX3_save_link)

            el_MEX3_save_link.click();
        };

// ---  hide modal
        //$("#id_mod_selectex3").modal("hide");
    }  // MEX3_Save

//========= MEX3_getinfo_from_server  ============= PR2021-10-06
    function MEX3_getinfo_from_server() {
        console.log("  =====  MEX3_getinfo_from_server  =====");
        el_MEX3_loader.classList.remove(cls_hide);

        UploadChanges({get: true}, urls.url_ex3_getinfo);
    }  // MEX3_getinfo_from_server

//========= MEX3_UpdateFromResponse  ============= PR2021-10-08
    function MEX3_UpdateFromResponse(response) {
        console.log("  =====  MEX3_UpdateFromResponse  =====");
        console.log("response", response)

        el_MEX3_loader.classList.add(cls_hide);
        mod_MEX3_dict.subject_rows = (response.ex3_subject_rows) ? response.ex3_subject_rows : [];
        mod_MEX3_dict.sel_examperiod = (response.sel_examperiod) ? response.sel_examperiod : null;
        mod_MEX3_dict.examperiod_caption = (response.examperiod_caption) ? response.examperiod_caption : "---";
        mod_MEX3_dict.sel_layout = (response.sel_layout) ? response.sel_layout : "none";
        mod_MEX3_dict.lvlbase_pk_list = (response.lvlbase_pk_list) ? response.lvlbase_pk_list : [];

        el_MEX3_select_layout.value = mod_MEX3_dict.sel_layout;
        // el_MEX3_select_level is already reset in MEX#_Open with MEX3_reset_layout_options
        console.log("mod_MEX3_dict.lvlbase_pk_list", mod_MEX3_dict.lvlbase_pk_list)
        if (mod_MEX3_dict.lvlbase_pk_list && mod_MEX3_dict.lvlbase_pk_list.length){
            for (let i = 0, option; option = el_MEX3_select_level.options[i]; i++) {
                const lvlbase_pk_int = (Number(option.value)) ? Number(option.value) : null;
                option.selected = (lvlbase_pk_int && mod_MEX3_dict.lvlbase_pk_list && mod_MEX3_dict.lvlbase_pk_list.includes(lvlbase_pk_int));
            };
        } else {
            el_MEX3_select_level.value = "0";
        };

// - set header text
        el_id_MEX3_hdr.innerText = [loc.Ex3, loc.Proces_verbaal_van_Toezicht, mod_MEX3_dict.examperiod_caption].join("  -  ");

        MEX3_FillTbls()

    }  // MEX3_getinfo_from_server

//========= MEX3_SelectLevelHasChanged  ============= PR2021-10-09
    function MEX3_SelectLevelHasChanged() {
        mod_MEX3_dict.lvlbase_pk_list = MEX3_get_sel_lvlbase_pk_list();
        MEX3_FillTbls();
    }  // MEX3_SelectLevelHasChanged

//========= MEX3_FillTbls  ============= PR2021-10-06
    function MEX3_FillTbls() {
        console.log("===== MEX3_FillTbls ===== ");
        console.log("mod_MEX3_dict.subject_rows", mod_MEX3_dict.subject_rows);
        console.log("mod_MEX3_dict.lvlbase_pk_list", mod_MEX3_dict.lvlbase_pk_list, typeof mod_MEX3_dict.lvlbase_pk_list);

// ---  reset tblBody available and selected
        el_MEX3_tblBody_available.innerText = null;
        el_MEX3_tblBody_selected.innerText = null;

        let has_subject_rows = false;
        let has_selected_subject_rows = false;

// ---  loop through mod_MEX3_dict.subject_rows, show only subjects with lvlbase_pk in lvlbase_pk_list
        if (mod_MEX3_dict.subject_rows && mod_MEX3_dict.subject_rows.length){
            for (let i = 0, subj_row; subj_row = mod_MEX3_dict.subject_rows[i]; i++) {
                let show_row = false;
                if (mod_MEX3_dict.lvlbase_pk_list && mod_MEX3_dict.lvlbase_pk_list.length){
                    if (subj_row.lvlbase_id_arr && subj_row.lvlbase_id_arr.length){
                         for (let x = 0, lvlbase_id; lvlbase_id = subj_row.lvlbase_id_arr[x]; x++) {
                            if (mod_MEX3_dict.lvlbase_pk_list.includes(lvlbase_id)){
                                show_row = true;
                                break
                    }}};
                } else {
                    show_row = true;
                }
                if (show_row){
                    has_subject_rows = true;
                    const has_selected_subjects = MEX3_CreateSelectRow(subj_row);
                    if(has_selected_subjects) {has_selected_subject_rows = true };
                };
            };
        };

        if (!has_subject_rows){
            const no_students_txt = (mod_MEX3_dict.sel_examperiod === 3) ? loc.No_studenst_examperiod_03 :
                                    (mod_MEX3_dict.sel_examperiod === 2) ? loc.No_studenst_examperiod_02 :
                                    loc.No_studenst_with_subjects;
            el_MEX3_tblBody_available.innerHTML = [
                "<p class='text-muted px-2 pt-2'>", no_students_txt, "</p>"
            ].join("");

// --- addrow 'Please_select_one_or_more_subjects' if no subjects selected
        } else if(!has_selected_subject_rows){
            el_MEX3_tblBody_selected.innerHTML = [
                "<p class='text-muted px-2 pt-2'>", loc.Please_select_one_or_more_subjects,
                "</p><p class='text-muted px-2'>", loc.from_available_list, "</p>"
            ].join("");

        };

// ---  enable save btn
        el_MEX3_btn_save.disabled = !has_selected_subject_rows;

    }; // MEX3_FillTbls

//========= MEX3_CreateSelectRow  ============= PR2021-10-07
    function MEX3_CreateSelectRow(row_dict) {
        //console.log("===== MEX3_CreateSelectRow ===== ");

        let has_selected_subjects = false;

// - get ifo from dict
        const subj_id = (row_dict.subj_id) ? row_dict.subj_id : null;
        const subj_code = (row_dict.subj_code) ? row_dict.subj_code : "---";
        const subj_name_nl = (row_dict.subj_name_nl) ? row_dict.subj_name_nl : "---";
        const is_selected = (row_dict.selected) ? row_dict.selected : false;
        const just_selected = (row_dict.just_selected) ? row_dict.just_selected : false;

        if(is_selected) { has_selected_subjects = true};

        const tblBody = (is_selected) ? el_MEX3_tblBody_selected : el_MEX3_tblBody_available;

        const tblRow = tblBody.insertRow(-1);
        // bg_transparent added for transition - not working
        //tblRow.classList.add("bg_transparent");
        tblRow.id = subj_id;

//- add hover to select row
        add_hover(tblRow)

// --- add first td to tblRow.
        let td = tblRow.insertCell(-1);
        let el_div = document.createElement("div");
            el_div.classList.add("tw_060")
            el_div.innerText = subj_code;
            td.appendChild(el_div);

// --- add second td to tblRow.
        td = tblRow.insertCell(-1);
        el_div = document.createElement("div");
            el_div.classList.add("tw_240")
            el_div.innerText = subj_name_nl;
            td.appendChild(el_div);

        //td.classList.add("tw_200X", "px-2", "pointer_show") // , cls_bc_transparent)

//----- add addEventListener
        tblRow.addEventListener("click", function() {MEX3_AddRemoveSubject(tblRow)}, false);

// --- if added / removed row highlight row for 1 second
        if (just_selected) {
        row_dict.just_selected = false;
            ShowClassWithTimeout(tblRow, "bg_selected_blue", 1000) ;
        }
        return has_selected_subjects;
    } // MEX3_CreateSelectRow

//========= MEX3_AddRemoveSubject  ============= PR2020-11-18 PR2021-08-31
    function MEX3_AddRemoveSubject(tblRow) {
        console.log("  =====  MEX3_AddRemoveSubject  =====");
        console.log("tblRow", tblRow);

        const sel_subject_pk = (Number(tblRow.id)) ? Number(tblRow.id) : null;
        let has_changed = false;
    // lookup subject in mod_MEX3_dict.subject_rows
        for (let i = 0, row_dict; row_dict = mod_MEX3_dict.subject_rows[i]; i++) {
            if (row_dict.subj_id === sel_subject_pk){
                // set selected = true when clicked in list 'available', set false when clicked in list 'selected'
                const new_selected = (row_dict.selected) ? false : true;
                row_dict.selected = new_selected
                row_dict.just_selected = true;
                has_changed = true;
        console.log("new_selected", new_selected);
        console.log("row_dict", row_dict);
                break;
            }
        };

// ---  enable btn submit
        if(has_changed){
            el_MEX3_btn_save.disabled = false;
            MEX3_FillTbls();
        }

    }  // MEX3_AddRemoveSubject

    function MEX3_get_sel_lvlbase_pk_list(){  // PR2021-10-09
    // ---  loop through id_MEX3_select_level and collect selected lvlbase_pk's
        //console.log("  =====  MEX3_get_sel_lvlbase_pk_list  =====");
        let sel_lvlbase_pk_list = [];
        if(el_MEX3_select_level){
            const level_options = Array.from(el_MEX3_select_level.options);
            console.log("level_options", level_options);
            if(level_options && level_options.length){
                for (let i = 0, level_option; level_option = level_options[i]; i++) {
                    if (level_option.selected){
            console.log("level_option.selected", level_option);
                        if (level_option.value === "0"){
                            sel_lvlbase_pk_list = [];
                            break;
                        } else {
                            const lvlbase_pk = Number(level_option.value);
                            if (lvlbase_pk){
                                sel_lvlbase_pk_list.push(lvlbase_pk);
        }}}}}};
        //console.log("sel_lvlbase_pk_list", sel_lvlbase_pk_list);
        return sel_lvlbase_pk_list;
    }

    function MEX3_reset_layout_options(){  // PR2021-10-10
    // ---  remove 'se';lected' from layout options
        //console.log("  =====  MEX3_reset_layout_options  =====");
        if(el_MEX3_select_layout){
            const layout_options = Array.from(el_MEX3_select_layout.options);
            if(layout_options && layout_options.length){
                for (let i = 0, option; option = layout_options[i]; i++) {
                    option.selected = false;
                };
            };
        };
    };  // MEX3_reset_layout_options

///////////////////////////////////////
// +++++++++ MOD SELECT EXAM  ++++++++++++++++ PR2022-06-22
    function MSELEX_Open(el_input){
        console.log(" ===  MSELEX_Open  =====") ;
        console.log( "el_input", el_input);
        // only called in table "grades" when clicked on field "ceex_name"
        // cannot change exam when it is approved or published

        el_MSELEX_header.innerText = loc.Select_exam;

        b_clear_dict(mod_MSELEX_dict);
        mod_MSELEX_dict.exam_pk = null;

        if(permit_dict.permit_crud){
            const tblRow = t_get_tablerow_selected(el_input)
            const pk_int = get_attr_from_el_int(tblRow, "data-pk");
        console.log("pk_int", pk_int);
            const [index, found_dict, compare] = b_recursive_integer_lookup(grade_rows, "id", pk_int);
            const data_dict = (!isEmpty(found_dict)) ? found_dict : null;
            const datarow_index = index;
        console.log("data_dict", data_dict);

            if(!isEmpty(data_dict)){
                const auth1by_field =  "ce_exam_auth1by_id" ;
                const auth2by_field =  "ce_exam_auth2by_id" ;
                const publ_field = "ce_exam_published_id" ;

                if (!!data_dict.ce_exam_published_id){
    // exit and give message when grade is submitted
                    b_show_mod_message_html(loc.err_list.This_exam_is_submitted + "<br>" + loc.err_list.You_cannot_change_exam);
                } else if (!!data_dict.ce_exam_auth1by_id || !!data_dict.ce_exam_auth2by_id){
    // exit and give message when grade is submitted
                    b_show_mod_message_html(loc.err_list.This_exam_is_approved + "<br>" + loc.err_list.You_cannot_change_exam);

                } else {
                    mod_MSELEX_dict.exam_pk = data_dict.ce_exam_id;
                    mod_MSELEX_dict.mapid = data_dict.mapid;
                    mod_MSELEX_dict.grade_pk = data_dict.id;
                    mod_MSELEX_dict.student_pk = data_dict.student_id;
                    mod_MSELEX_dict.studsubj_pk = data_dict.studsubj_id;
                    mod_MSELEX_dict.subj_pk = data_dict.subj_id;
                    mod_MSELEX_dict.subjbase_pk = data_dict.subjbase_id;
                    mod_MSELEX_dict.student_lvlbase_pk = data_dict.lvlbase_id;
            console.log( "mod_MSELEX_dict", mod_MSELEX_dict);
            console.log( "mod_MSELEX_dict.exam_pk", mod_MSELEX_dict.exam_pk);

        // ---  fill select table
                    const row_count = MSELEX_FillSelectTable()
                    // hide remove button when grade has no exam
                    add_or_remove_class(el_MSELEX_btn_delete, cls_hide, !data_dict.ce_exam_id)
                    add_or_remove_class(el_MSELEX_btn_save, cls_hide, !row_count)
                    el_MSELEX_btn_cancel.innerText = (row_count) ? loc.Cancel : loc.Close;
                    MSELEX_validate_and_disable();

                    add_or_remove_class(el_MSELEX_info_container, cls_hide, true);

        // ---  show modal
                    $("#id_mod_select_exam").modal({backdrop: true});

                };  // if (is_published || is_authby){
            };  // if(!isEmpty(data_dict))
        };
    };  // MSELEX_Open

//=========  MSELEX_Save  ================ PR2021-05-22 PR2022-01-24
    function MSELEX_Save(is_delete){
        console.log(" ===  MSELEX_Save  =====") ;

        console.log( "mod_MSELEX_dict: ", mod_MSELEX_dict);
        const sel_exam_pk = (!is_delete && mod_MSELEX_dict.exam_pk) ? mod_MSELEX_dict.exam_pk : null;
        if(permit_dict.permit_crud){
            const upload_dict = {
                table: 'grade',
                mode: "update",
                return_grades_with_exam: true,
                examyear_pk: setting_dict.sel_examyear_pk,
                depbase_pk: setting_dict.sel_depbase_pk,
                examperiod: setting_dict.sel_examperiod,
                exam_pk: sel_exam_pk,
                student_pk: mod_MSELEX_dict.student_pk,
                lvlbase_pk: mod_MSELEX_dict.student_lvlbase_pk,
                studsubj_pk: mod_MSELEX_dict.studsubj_pk,
                grade_pk: mod_MSELEX_dict.grade_pk,
            };

            UploadChanges(upload_dict, urls.url_grade_upload);

        }  // if(permit_dict.permit_crud){
        $("#id_mod_select_exam").modal("hide");
    }  // MSELEX_Save

//=========  MSELEX_FillSelectTable  ================ PR2022-06-22
    function MSELEX_FillSelectTable() {
        console.log( "===== MSELEX_FillSelectTable ========= ");

        const tblBody_select = el_MSELEX_tblBody_select;
        tblBody_select.innerText = null;

        console.log( "all_exam_rows", all_exam_rows);
        let row_count = 0, add_to_list = false;
// ---  loop through all_exam_rows
        if(all_exam_rows && all_exam_rows.length){
            for (let i = 0, data_dict; data_dict = all_exam_rows[i]; i++) {

            // add only when exam has same subject as grade, and also the same depbase and lvlbase_id
            // also filter examperiod
            // PR2022-05-18 debug Mireille Peterson exam not showing
            // cause: sxm has different subj_pk, use subjbase_pk instead
                let show_row = false;
                if (mod_MSELEX_dict.subjbase_pk === data_dict.subjbase_id){
                    // PR2022-06-30 debug: showed wrong examperiod after switching examperiod in sel_btn
                    // solved by downloading all_exam_rows when switching sel_btn
                    // also added filter examperiod here, to be on the safe side
                    if (data_dict.examperiod === setting_dict.sel_examperiod){
                        if(mod_MSELEX_dict.student_lvlbase_pk){
                            show_row = (mod_MSELEX_dict.student_lvlbase_pk === data_dict.lvlbase_id);
                        } else {
                            show_row = true;
                        };
                    };
                };
                if (show_row){
        console.log( "data_dict", data_dict);
                    row_count += 1;
                    MSELEX_FillSelectRow(data_dict, tblBody_select, -1);
                };
            };
        };
        if(!row_count){
            let tblRow = tblBody_select.insertRow(-1);
            let td = tblRow.insertCell(-1);
            td.innerText = loc.No_exam_for_this_subject;

        } else if(row_count === 1){
            let tblRow = tblBody_select.rows[0]
            if(tblRow) {
// ---  make first row selected
                //tblRow.classList.add(cls_selected)

                MSELEX_SelectItem(tblRow);
            };
        };
        return row_count
    }; // MSELEX_FillSelectTable

//=========  MSELEX_FillSelectRow  ================ PR2020-10-27
    function MSELEX_FillSelectRow(exam_dict, tblBody_select, row_index) {
        //console.log( "===== MSELEX_FillSelectRow ========= ");
        //console.log( "exam_dict: ", exam_dict);

//--- loop through data_map
        const exam_pk_int = exam_dict.id;
        const code_value = (exam_dict.exam_name) ? exam_dict.exam_name : "---"
        const is_selected_pk = (mod_MSELEX_dict.exam_pk != null && exam_pk_int === mod_MSELEX_dict.exam_pk)
// ---  insert tblRow  //index -1 results in that the new row will be inserted at the last position.
        let tblRow = tblBody_select.insertRow(row_index);
        tblRow.setAttribute("data-pk", exam_pk_int);
// ---  add EventListener to tblRow
        tblRow.addEventListener("click", function() {MSELEX_SelectItem(tblRow)}, false )
// ---  add hover to tblRow
        add_hover(tblRow);
// ---  highlight clicked row
        if (is_selected_pk){ tblRow.classList.add(cls_selected)}
// ---  add first td to tblRow.
        let td = tblRow.insertCell(-1);
// --- add a element to td., necessary to get same structure as item_table, used for filtering
        let el_div = document.createElement("div");
            el_div.innerText = code_value;
            td.title = code_value;
            el_div.classList.add("tw_360", "px-2", "pointer_show" )
        td.appendChild(el_div);
    }  // MSELEX_FillSelectRow

//=========  MSELEX_SelectItem  ================ PR2021-04-05
    function MSELEX_SelectItem(tblRow) {
        console.log( "===== MSELEX_SelectItem ========= ");
        console.log( "tblRow", tblRow);
// ---  deselect all highlighted rows
        DeselectHighlightedRows(tblRow, cls_selected)
// ---  highlight clicked row
        tblRow.classList.add(cls_selected)
// ---  get pk code and value from tblRow in mod_MSELEX_dict
        mod_MSELEX_dict.exam_pk = get_attr_from_el_int(tblRow, "data-pk")
        console.log( "mod_MSELEX_dict", mod_MSELEX_dict);
        MSELEX_validate_and_disable();
    }  // MSELEX_SelectItem

//=========  MSELEX_Save  ================ PR2021-05-22
    function MSELEX_validate_and_disable(){
        el_MSELEX_btn_save.disabled = !mod_MSELEX_dict.exam_pk;
    }

///////////////////////////////////////


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
            };
        };

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
        };
    };  // ModalStatus_FillNotes


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL MULTIPLE OCCURRENCES ++++++++++++++++++++++++++++++++++++++++++
//=========  MLINKSTUD_Open  ================ PR2021-09-05
    function MLINKSTUD_Open() {
        console.log("===== MLINKSTUD_Open =====");

        if (permit_dict.permit_crud && permit_dict.requsr_same_school) {
        //console.log("mod_MLINKSTUD_dict", mod_MLINKSTUD_dict);

            mod_MLINKSTUD_dict.rows = [];
            mod_MLINKSTUD_dict.mode = "loading";

            // MLINKSTUD_fill_table is in MLINKSTUD_toggle_showall
            MLINKSTUD_toggle_showall(true); // hide_linked = true

            MLINKSTUD_btnSelectClicked(null, 1) ;

            MLINKSTUD_set_datatable_hidden();

            const url_str = urls.url_student_multiple_occurrences;
            const upload_dict = {studsubj_multiple_occurrences: {get: true}};
            UploadChanges(upload_dict, url_str);

            $("#id_mod_link_students").modal({backdrop: true});

        };

// ---  show modal
    };  // MLINKSTUD_Open

//=========  MLINKSTUD_save  ================ PR2023-01-20
    function MLINKSTUD_save() {
        console.log("===== MLINKSTUD_save =====");

        if (permit_dict.permit_crud && permit_dict.requsr_same_school) {

            const url_str = urls.url_student_enter_exemptions;
            const upload_dict = {mode: "enter",
                                 table: "student"};
            UploadChanges(upload_dict, url_str);
        };

        $("#id_mod_link_students").modal("hide");

    };  // MLINKSTUD_save

//=========  MLINKSTUD_btnPrevNextClicked  ================ PR2020-12-05  PR2021-12-05 PR2022-02-14
    function MLINKSTUD_btnPrevNextClicked(prev_next) {
        //console.log("=== MLINKSTUD_btnPrevNextClicked ===", prev_next);
        //console.log("mod_MLINKSTUD_dict.sel_btn_index: " + mod_MLINKSTUD_dict.sel_btn_index, typeof mod_MLINKSTUD_dict.sel_btn_index);

    // get btn_index
        let btn_index = (mod_MLINKSTUD_dict.sel_btn_index) ? mod_MLINKSTUD_dict.sel_btn_index : 1;

        // skip step 2 when not is_import_grade
        // skip step 4 when not is_import_username
        let step = 1;
        if (prev_next === "next"){
            btn_index += 1;
        } else if (prev_next === "prev"){
            btn_index -= 1;
        };
        if (btn_index < 1) {
            btn_index = 1;
        } else if (btn_index > 3) {
            btn_index = 3;
        };

        MLINKSTUD_btnSelectClicked(null, btn_index);
    }  // MLINKSTUD_btnPrevNextClicked

//=========  MLINKSTUD_set_datatable_hidden  ================ PR2022-03-22
    function MLINKSTUD_set_datatable_hidden() {

        console.log("===== MLINKSTUD_set_datatable_hidden =====");

        add_or_remove_class(el_MLINKSTUD_loading, cls_hide, mod_MLINKSTUD_dict.mode !== "loading");
        add_or_remove_class(el_MLINKSTUD_no_data, cls_hide, mod_MLINKSTUD_dict.mode !== "no_data");
        add_or_remove_class(el_MLINKSTUD_has_data, cls_hide, mod_MLINKSTUD_dict.mode !== "has_data");

        const has_unlinked_data = mod_MLINKSTUD_dict.mode === "has_data" && mod_MLINKSTUD_dict.has_unlinked_rows;
        console.log("    has_unlinked_data", has_unlinked_data);
        add_or_remove_class(el_MLINKSTUD_has_unlinked_data, cls_hide, !has_unlinked_data);
        add_or_remove_class(el_MLINKSTUD_all_linked_data, cls_hide, has_unlinked_data);
    };  // MLINKSTUD_set_datatable_hidden


//=========  MLINKSTUD_btnSelectClicked  ================ PR2020-12-05  PR2021-12-05 PR2022-03-19
    function MLINKSTUD_btnSelectClicked(el_btn, btn_index_int) {

        console.log("=== MLINKSTUD_btnSelectClicked ===");
        console.log("    el_btn", el_btn);
        console.log("    btn_index_int", btn_index_int);


        // get btn_index from el_btn if called bij eventhandler, from btn_index_int otherwise
        if (el_btn){
            mod_MLINKSTUD_dict.sel_btn_index = get_attr_from_el_int(el_btn, "data-btn_index")
        } else if (btn_index_int){
            mod_MLINKSTUD_dict.sel_btn_index = btn_index_int;
        };

        MLINKSTUD_set_datatable_hidden(mod_MLINKSTUD_dict.mode);

        console.log("    mod_MLINKSTUD_dict.mode", mod_MLINKSTUD_dict.mode);

// ---  show only the elements that are used in this mod_shift_option
        if(el_MLINKSTUD_body){
            const sel_btn = "btn_step" + mod_MLINKSTUD_dict.sel_btn_index;
            const els = el_MLINKSTUD_body.getElementsByClassName("btn_show");
            for (let i = 0, el; el = els[i]; i++) {
                const is_show = el.classList.contains(sel_btn);
                show_hide_element(el, is_show)
            };

// ---  highlight selected button
            MLINKSTUD_HighlightAndDisableButtons();
        };
    };  // MLINKSTUD_btnSelectClicked

//=========  MLINKSTUD_HighlightAndDisableButtons  ================ PR2019-05-25 PR2021-04-21
    function MLINKSTUD_HighlightAndDisableButtons() {
        console.log("=== MLINKSTUD_HighlightAndDisableButtons ===");
        // el_MLINKSTUD_btn_prev and el_MLINKSTUD_btn_next don't exists when user has no permission

        if (el_MLINKSTUD_btn_prev){
            el_MLINKSTUD_btn_prev.disabled = (mod_MLINKSTUD_dict.sel_btn_index <= 1);
        };
        if (el_MLINKSTUD_btn_next){
            el_MLINKSTUD_btn_next.disabled = (mod_MLINKSTUD_dict.sel_btn_index >= 3) ||
                                (mod_MLINKSTUD_dict.sel_btn_index >=2 && mod_MLINKSTUD_dict.mode !== "has_data");
        };

        console.log("    mod_MLINKSTUD_dict.mode", mod_MLINKSTUD_dict.mode);
        console.log("    mod_MLINKSTUD_dict.sel_btn_index", mod_MLINKSTUD_dict.sel_btn_index);

        if(el_MLINKSTUD_btn_container){
            let btns = el_MLINKSTUD_btn_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                const data_btn_index = get_attr_from_el_int(btn, "data-btn_index");

// ---  disable btn 3 when not has_data
                const btn3_disabled = (data_btn_index === 3 && mod_MLINKSTUD_dict.mode !== "has_data")
                btn.disabled = btn3_disabled;

// ---  highlight selected button
                const is_selected = (data_btn_index === mod_MLINKSTUD_dict.sel_btn_index && !btn3_disabled);
                add_or_remove_class (btn, cls_btn_selected, is_selected);

            };
        };

// ---  hide save btn  when not has_data
        if(el_MLINKSTUD_btn_save){
            add_or_remove_class (el_MLINKSTUD_btn_save, cls_hide, (mod_MLINKSTUD_dict.sel_btn_index !== 3 || mod_MLINKSTUD_dict.mode !== "has_data"));
        };

        if(el_MLINKSTUD_btn_cancel){
            el_MLINKSTUD_btn_cancel.innerText = (mod_MLINKSTUD_dict.sel_btn_index === 3) ? loc.Close : loc.Cancel;
        };

    };  // MLINKSTUD_HighlightAndDisableButtons

//=========  MLINKSTUD_response  ================ PR2023-01-22
    function MLINKSTUD_response(response) {
        console.log("===== MLINKSTUD_response =====");

        mod_MLINKSTUD_dict.student_pk_list = (response.multiple_occurrences_list) ? response.multiple_occurrences_list : [];
        mod_MLINKSTUD_dict.multiple_occurrences_dict = (response.multiple_occurrences_dict) ? response.multiple_occurrences_dict : {};

        mod_MLINKSTUD_dict.mode = (mod_MLINKSTUD_dict.student_pk_list && mod_MLINKSTUD_dict.student_pk_list.length) ? "has_data" : "no_data";

        console.log("    mod_MLINKSTUD_dict.mode", mod_MLINKSTUD_dict.mode);

        MLINKSTUD_fill_table();

        MLINKSTUD_btnSelectClicked();
    }; // MLINKSTUD_response

//=========  MLINKSTUD_fill_table  ================ PR2021-09-17
    function MLINKSTUD_fill_table() {
        console.log("===== MLINKSTUD_fill_table =====");

        let has_unlinked_rows = false;
        if(el_MLINKSTUD_data_container){
            el_MLINKSTUD_data_container.innerHTML = null;

            if (mod_MLINKSTUD_dict.student_pk_list && mod_MLINKSTUD_dict.student_pk_list.length){

// ++++ loop through student_pk_list - it is sorted by student lastname, firstname
                for (let i = 0, student_pk; student_pk = mod_MLINKSTUD_dict.student_pk_list[i]; i++) {

                    const student_dict = mod_MLINKSTUD_dict.multiple_occurrences_dict[student_pk];
                    if (student_dict){

                        const cur_stud_dict = student_dict.cur_stud;

                        const linked_arr = (cur_stud_dict.linked) ? cur_stud_dict.linked.split(";") : [];
                        const notlinked_arr = (cur_stud_dict.notlinked) ? cur_stud_dict.notlinked.split(";") : [];

                console.log("    cur_stud_dict", cur_stud_dict);
                console.log("    cur_stud_dict.linked", cur_stud_dict.linked);
                console.log("    cur_stud_dict.notlinked", cur_stud_dict.notlinked);
                // linked_arr = ['4643', '8501']
                // notlinked_arr  = []

                        let show_cur_box = false;

            // - check if student has linked students
                        const el_cur_box = document.createElement("div");
                        el_cur_box.classList.add("p-2", "my-1");

            // - add header line with cur_stud_dict name etc.
                        const el_stud_name = document.createElement("h6");
                        el_stud_name.innerText = [cur_stud_dict.fullname, " - ", cur_stud_dict.depbase_code, cur_stud_dict.lvlbase_code, cur_stud_dict.sctbase_code,].join(' ');
                        el_cur_box.appendChild(el_stud_name);
                        el_MLINKSTUD_data_container.appendChild(el_cur_box);

            // - loop through other students
                        const other_students = (student_dict.other_stud) ? student_dict.other_stud : {};
                        for (const other_stud_dict of Object.values(other_students)) {

                console.log(" ---- other_stud_dict", other_stud_dict);

                            const other_stud_dict_id_str = (other_stud_dict.student_id) ?  other_stud_dict.student_id.toString() : null;
                            const is_linked = (linked_arr && linked_arr.includes(other_stud_dict_id_str));
                            const is_notlinked = (notlinked_arr && notlinked_arr.includes(other_stud_dict_id_str));
                console.log("    is_linked", is_linked);
                console.log("    is_notlinked", is_notlinked);

                            const el_other_box = document.createElement("div");
                            el_cur_box.appendChild(el_other_box);

                            add_or_remove_attr(el_other_box, "data-linked", is_linked )
                            add_or_remove_attr(el_other_box, "data-notlinked", is_notlinked )

                            const show_other = (mod_MLINKSTUD_dict.show_all) || (!is_linked && !is_notlinked);
                            // Note: class 'display_hide' not working when classList has also 'note_flex_1'
                            add_or_remove_class(el_other_box, "note_flex_1", show_other, "display_hide")
                            if(show_other){
                                show_cur_box = true;
                                has_unlinked_rows = true;
                                }

                console.log("    show_other", show_other);

                            const el_cross = document.createElement("div");
                            el_cross.classList.add("p-1", "pointer_show")
                            el_cross.setAttribute("data-cur_stud_id", cur_stud_dict.student_id);
                            el_cross.setAttribute("data-oth_stud_id", other_stud_dict.student_id);
                            el_cross.addEventListener("click", function() {MLINKSTUD_tick_cross(el_cross, "unlink")}, false);
                            el_other_box.appendChild(el_cross);
                                const el_icon_cross = document.createElement("div");
                                el_icon_cross.className = (is_notlinked) ? "note_1_4" : "note_0_4";
                                // dont add hover when is_notlinked, it will return not_notlinked icon on mouseleave
                                if (!is_notlinked){
                                    el_icon_cross.addEventListener("mouseenter", function(){
                                        el_icon_cross.className = "note_1_4";
                                    });
                                    el_icon_cross.addEventListener("mouseleave", function(){
                                        el_icon_cross.className = "note_0_4";
                                    });
                                };
                                el_cross.appendChild(el_icon_cross);

                            const el_tick = document.createElement("div");
                            el_tick.classList.add("p-1", "pointer_show");
                            el_tick.setAttribute("data-cur_stud_id", cur_stud_dict.student_id);
                            el_tick.setAttribute("data-oth_stud_id", other_stud_dict.student_id);
                            el_tick.addEventListener("click", function() {MLINKSTUD_tick_cross(el_tick, "link")}, false);
                            el_other_box.appendChild(el_tick);
                                const el_icon_tick = document.createElement("div");
                                el_icon_tick.className = (is_linked) ?  "note_1_6" : "note_0_6";
                                // dont add hover when linked, it will return unlinked icon on mouseleave
                                if (!is_linked){
                                    el_icon_tick.addEventListener("mouseenter", function(){
                                        el_icon_tick.className = "note_1_6";
                                    });
                                    el_icon_tick.addEventListener("mouseleave", function(){
                                        el_icon_tick.className = "note_0_6";
                                    });
                                };
                                el_tick.appendChild(el_icon_tick);

                            const other_name = [other_stud_dict.examyear, other_stud_dict.fullname, other_stud_dict.school_name, other_stud_dict.deplvlsct, other_stud_dict.result_status,].join(' - ')
                            const el_info = document.createElement("div");
                            el_info.classList.add("p-1");
                            el_other_box.appendChild(el_info);
                                const el_info_small = document.createElement("small");
                                el_info_small.classList.add("c_form_text", "mx-2");
                                el_info_small.innerText = other_name;
                                el_info.appendChild(el_info_small);
                        };  //  for (let j = 0, other; other = dict.other_stud[j]; j++) {

                        // show row only if it has one one more other boxes that are shown
                        if(!show_cur_box){el_cur_box.classList.add("display_hide")};
                    };
                };  // for (let i = 0, dict; dict = mod_MLINKSTUD_dict[i]; i++)
            };  // if (mod_MLINKSTUD_dict.rows and mod_MLINKSTUD_dict.rows.length){
        };  // if(el_MLINKSTUD_data_container)

        console.log("  @@@  has_unlinked_rows", has_unlinked_rows);
        mod_MLINKSTUD_dict.has_unlinked_rows = has_unlinked_rows;
    };  //  MLINKSTUD_fill_table

//=========  MLINKSTUD_tick_cross  ================ PR2021-09-05
    function MLINKSTUD_tick_cross(el, mode) {
        console.log("===== MLINKSTUD_tick_cross =====");
        console.log("    el", el);
        console.log("    mode", mode);

        if (permit_dict.permit_crud && permit_dict.requsr_same_school) {
            const el_other_box = el.parentNode
            const is_linked = get_attr_from_el(el_other_box, "data-linked")
            const is_notlinked = get_attr_from_el(el_other_box, "data-notlinked")

            const cur_stud_id = get_attr_from_el_int(el, "data-cur_stud_id");
            const oth_stud_id = get_attr_from_el_int(el, "data-oth_stud_id");

        console.log("    cur_stud_id", cur_stud_id);
        console.log("    oth_stud_id", oth_stud_id);
            const cur_stud_dict = (mod_MLINKSTUD_dict.multiple_occurrences_dict) ? mod_MLINKSTUD_dict.multiple_occurrences_dict[cur_stud_id] : {}

            const linked_arr = (cur_stud_dict.linked) ? cur_stud_dict.linked.split(";") : [];
            const notlinked_arr = (cur_stud_dict.notlinked) ? cur_stud_dict.notlinked.split(";") : [];

            const oth_stud_dicts = (cur_stud_dict.other_stud) ? cur_stud_dict.other_stud : {};
            const other_stud_dict = (oth_stud_dicts[oth_stud_id]) ? oth_stud_dicts[oth_stud_id] : {};

            const other_stud_dict_id_str = (other_stud_dict.student_id) ?  other_stud_dict.student_id.toString() : null;
            const is_linkedX = (linked_arr && linked_arr.includes(other_stud_dict_id_str));
            const is_notlinkedX = (notlinked_arr && notlinked_arr.includes(other_stud_dict_id_str));

        console.log("    other_stud_dict", other_stud_dict);
            console.log("    is_linkedX", is_linkedX);
            console.log("    is_notlinkedX", is_notlinkedX);

    // ---  Upload Changes

            let upload_dict = {mode: mode,
                               cur_stud_id: cur_stud_id,
                               oth_stud_id: oth_stud_id,
                               table: "student"};

            if (mode === "link"){
                // set linked when clicked on 'tick' and is_linked = false
                // remove linked when clicked on 'tick' and is_linked = true
                upload_dict.linked = !is_linked;
                if (upload_dict.linked){ShowOkElement(el)};

            } else if (mode === "unlink"){
                // set notlinked when clicked on 'cross' and is_notlinked = false
                // remove notlinked when clicked on 'cross' and is_notlinked = true
                upload_dict.notlinked = !is_notlinked;
                if (upload_dict.notlinked){ShowOkElement(el)};
            };

            const url_str = urls.url_student_linkstudent;
            UploadChanges(upload_dict, url_str);
        };

    };  // MLINKSTUD_tick_cross

    function MLINKSTUD_response_update(updated_multiple_occurrences) {  // PR2023-01-20
        console.log("===== MLINKSTUD_response_update =====");
        console.log("    updated_multiple_occurrences", updated_multiple_occurrences);
        console.log("    mod_MLINKSTUD_dict.multiple_occurrences_dict", mod_MLINKSTUD_dict.multiple_occurrences_dict);
        if (updated_multiple_occurrences && updated_multiple_occurrences.length){
            for (let i = 0, updated_dict; updated_dict = updated_multiple_occurrences[i]; i++) {
                const cur_student_pk = (updated_dict.cur_stud) ? updated_dict.cur_stud.student_id : null;

                if (cur_student_pk in mod_MLINKSTUD_dict.multiple_occurrences_dict){
                    mod_MLINKSTUD_dict.multiple_occurrences_dict[cur_student_pk] = updated_dict;
                };
            };
        };

       MLINKSTUD_fill_table();
       MLINKSTUD_set_datatable_hidden();

    }; // MLINKSTUD_response_update

//=========  MLINKSTUD_toggle_showall  ================ PR2021-09-18 PR2023-01-19
    function MLINKSTUD_toggle_showall(hide_linked) {
        console.log("===== MLINKSTUD_toggle_showall =====");

        mod_MLINKSTUD_dict.show_all = (hide_linked) ? false : !mod_MLINKSTUD_dict.show_all;

        el_MLINKSTUD_btn_showall.innerText = (mod_MLINKSTUD_dict.show_all) ? loc.Hide_linked_candidates : loc.Show_all_matching_candidates

        MLINKSTUD_fill_table();
    };  // MLINKSTUD_toggle_showall


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

//========= ValidateGrade  =============== PR2020-12-20
    function ValidateGrade(loc, fldName, value, dict){
        //console.log(" --- ValidateGrade ---")
        //console.log("fldName", fldName, "value", value)
        //console.log("dict", dict)

        // PR2021-05-02 field "srgrade" added, TODO no validations yet
        const err_list = loc.grade_err_list
        const is_score = (["pescore", "cescore"].includes(fldName));
        const is_grade = (["segrade", "srgrade", "pegrade", "cegrade"].includes(fldName));
        const is_pe_or_ce = (["pescore", "pegrade", "cescore", "cegrade"].includes(fldName));
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
                    if([2, 3].includes(dict.examperiod)) {
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
                        } else if([2, 3].includes(dict.examperiod)) {
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
                    const value_with_dots = value.replace(",", ".");
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

//========= get_column_is_hidden  ====== PR2022-04-17 PR2022-06-22
    function get_column_is_hidden() {
        //console.log(" --- get_column_is_hidden ---")

// ---  get list of hidden columns

// ---  get list of hidden columns
        // copy col_hidden from mod_MCOL_dict.cols_hidden
        const col_hidden = ["srgrade", "sr_status", "pescore", "pe_status", "pegrade"];
        // can also add multiple values with push:
        // was:
        // col_hidden.push( "srgrade", "sr_status", "pescore", "pe_status", "pegrade");

        b_copy_array_noduplicates(mod_MCOL_dict.cols_hidden, col_hidden);

// - hide columns that are not in use this examyear or this department PR2021-12-04
        // PR2021-12-04 use spread operator. from https://stackoverflow.com/questions/4842993/javascript-push-an-entire-list
        // PR2022-04-19 Sentry debug: Syntax error
        // back from spread operator, is not supported bij IE

        // hide srgrade when not sr_allowed
        if(!setting_dict.sr_allowed){col_hidden.push("srgrade", "sr_status")};

        // hide pe or ce + pe when not allowed
        if(setting_dict.no_centralexam){
            col_hidden.push("pescore", "pe_status", "pegrade", "cescore", "ce_status", "cegrade");
        } else if(setting_dict.no_practexam){
            col_hidden.push("pescore", "pe_status", "pegrade");
        };

// - hide level when not level_req
        if(!setting_dict.sel_dep_level_req){col_hidden.push("lvl_abbrev")};

// - show or hide download column when ce_exam_name is shown hidden PR2022-06-22
        const fldName = "download_conv_table";
        if(col_hidden.includes("ce_exam_name")) {
            if(!col_hidden.includes(fldName)) { col_hidden.push(fldName) }
        } else {
            if(col_hidden.includes(fldName)) { b_remove_item_from_array(col_hidden, fldName)}
        };

// - show only columns of sel_examtype
        // in field_setting are only columns of the seelected exan type
        // dont show examtype, Richard Westerink ATC didn't see that select btn.

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
            const input_with_dots = imput_trim.replace(",", ".");

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
                        output_text = output_text.replace(".", ",");
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
    };

//========= get_is_allowed_cluster  ======== // PR2022-05-01
    function get_is_allowed_cluster(cluster_id) {
        console.log ("----- get_is_allowed_cluster -----")
        console.log ("permit_dict.allowed_clusters", permit_dict.allowed_clusters)
        console.log ("cluster_id", cluster_id, typeof cluster_id)
        // check if cluster is allowed
        // check for other allowed field not necessarybecause they are not downloaded
        const is_allowed_cluster =
            (permit_dict.allowed_clusters) ?
                (cluster_id) ?
                    permit_dict.allowed_clusters.includes(cluster_id)
                    : false
                : true;
        return is_allowed_cluster;
    };
})  // document.addEventListener('DOMContentLoaded', function()