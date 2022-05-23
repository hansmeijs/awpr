// PR2020-09-29 added

// PR2021-12-16 declare variables outside function to make them global variables

// from https://stackoverflow.com/questions/11558025/do-browsers-propagate-javascript-variables-across-tabs
// variable values should not propagate between tabs - each tab should have its own global namespace,
// there would be all kinds of security issues if one tab could affect the JavaScript in another

// selected_btn is also used in t_MCOL_Open
let selected_btn = "btn_ep_01";

let setting_dict = {};
let permit_dict = {};
let loc = {};  // locale_dict
let urls = {};

const selected = {
    item_count: 0
};

let school_rows = [];
let subject_rows = [];
let cluster_rows = [];
let student_rows = [];

// ---  id_new assigns fake id to new records
let id_new = 0;

document.addEventListener("DOMContentLoaded", function() {
    "use strict";

    let el_loader = document.getElementById("id_loader");

// ---  get permits
    // permit dict gets value after downloading permit_list PR2021-03-27
    //  if user has no permit to view this page ( {% if no_access %} ): el_loader does not exist PR2020-10-02

// - NOTE: school ETE must have departments, because they are needed in the headerbar to select department PR2022-01-17

    const may_view_page = (!!el_loader);

    const cls_hide = "display_hide";
    const cls_hover = "tr_hover";
    const cls_visible_hide = "visibility_hide";
    const cls_selected = "tsa_tr_selected";

    const cls_selected_item = "tsa_td_unlinked_selected";

    let mod_dict = {};
    let mod_MSELEX_dict = {};
    const mod_MEX_dict = {};
    const mod_MASE_dict = {};
    const mod_MDUO_dict = {};

    let mod_MSSS_dict = {};
    let mod_status_dict = {};
    let mod_note_dict = {};

    let examyear_map = new Map();
    let department_map = new Map();
    let level_map = new Map();
    let sector_map = new Map();

    let ete_exam_rows = [];
    let duo_subject_rows = [];
    let duo_exam_rows = [];
    let ntermentable_rows = [];

    let grade_exam_rows = [];
    let grade_exam_result_rows = [];

    let filter_dict = {};

    let el_focus = null; // stores id of element that must get the focus after closing mod message PR2020-12-20

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    urls.url_usersetting_upload = get_attr_from_el(el_data, "data-url_usersetting_upload");
    urls.url_subject_upload = get_attr_from_el(el_data, "data-url_subject_upload");
    urls.url_exam_upload = get_attr_from_el(el_data, "data-url_exam_upload");
    urls.url_duo_exam_upload = get_attr_from_el(el_data, "data-url_duo_exam_upload");

    urls.url_exam_copy = get_attr_from_el(el_data, "data-url_exam_copy");
    urls.url_approve_publish_exam = get_attr_from_el(el_data, "data-url_approve_publish_exam");
    urls.url_approve_submit_grade_exam = get_attr_from_el(el_data, "data-url_approve_submit_grade_exam");
    urls.url_send_email_verifcode = get_attr_from_el(el_data, "data-url_send_email_verifcode");

    urls.url_grade_upload = get_attr_from_el(el_data, "data-url_grade_upload");

    urls.url_exam_download_exam_pdf = get_attr_from_el(el_data, "data-url_exam_download_exam_pdf");
    urls.url_exam_download_grade_exam_pdf = get_attr_from_el(el_data, "data-url_exam_download_grade_exam_pdf");
    urls.url_exam_download_conversion_pdf = get_attr_from_el(el_data, "data-url_exam_download_conversion_pdf");

    urls.url_exam_download_exam_json = get_attr_from_el(el_data, "data-url_exam_download_exam_json");

    urls.url_download_published = get_attr_from_el(el_data, "data-download_published_url");

    // const columns_tobe_hidden and mod_MCOL_dict are defined in tables.js
    //const mod_MCOL_dict = {selected_btn: null, cols_hidden: [], cols_skipped: {}}
    // PR2022-05-15 cols_skipped is dict with key: sel_btn and value: list of fieldnames to be skipped when filling tables with columns

    columns_tobe_hidden.btn_ete_exams = {
        subj_name: "Subject", lvl_abbrev: "Leerweg", version: "Version",
        examperiod: "Exam_type", blanks: "Blanks", secret_exam: "Secret_exam", status: "Status", download_exam: "Download_exam",
        cesuur: "Cesuur", scalelength: "Maximum_score", download_conv_table: "Download_conv_table"
    };
    columns_tobe_hidden.btn_duo_exams = {
        subjbase_code: "Abbreviation", subj_name: "Subject", lvl_abbrev: "Leerweg", version: "Version",
        ntb_omschrijving: "DUO_description", examperiod: "Exam_type", nterm: "N_term", scalelength: "schaallengte",
    };
    columns_tobe_hidden.btn_ntermen = {
        opl_code: "opl_code", leerweg: "leerweg", ext_code: "ext_code", tijdvak: "tijdvak", nex_id: "nex_id",
        omschrijving: "omschrijving", schaallengte: "schaallengte", n_term: "N_term",
        afnamevakid: "afnamevakid", extra_vakcodes_tbv_wolf: "extra_vakcodes_tbv_wolf",
        datum: "datum", begintijd: "begintijd", eindtijd: "eindtijd"
    };
    columns_tobe_hidden.btn_results = {
        subj_name: "Subject", lvl_abbrev: "Leerweg", version: "Version", school_name: "School",
        grd_count: "Number_of_exams", result_count: "Submitted_exams",
        result_avg: "Average_score_percentage", download_conv_table: "Download_conv_table"
    };
    columns_tobe_hidden.btn_ep_01 = {
        examnumber: "Examnumber", lvl_abbrev: "Leerweg", cluster_name: "Cluster",
        subj_name: "Subject", blanks: "Blanks", ce_exam_score: "Score", download_exam: "Download_exam"
    };
    columns_tobe_hidden.btn_reex = columns_tobe_hidden.btn_ep_01;

// --- get field_settings
    const field_settings = {
        ete_exam: { field_caption: ["", "Abbrev_subject_2lines", "Subject", "Leerweg", "Version",
                                "Exam_type", "Secret_exam", "Blanks", "Maximum_score_2lines", "",
                                "Download_exam", "Cesuur", "Download_conv_table_2lines"],
                field_names: ["select", "subjbase_code", "subj_name", "lvl_abbrev", "version",
                            "examperiod", "secret_exam", "blanks", "scalelength", "status",
                            "download_exam", "cesuur", "download_conv_table"],
                field_tags: ["div", "div", "div", "div", "div",
                            "div", "div", "div", "div", "div", "a", "input", "a"],
                filter_tags: ["text",  "text", "text", "text", "text",
                              "text", "toggle", "text", "text","status", "text", "text", "text"],
                field_width: ["020", "075", "240", "120", "120",
                                "150", "075", "075", "075","032", "090", "075", "100"],
                field_align: ["c",  "c", "l", "l", "l",
                                "l", "c", "c","c", "c", "c", "c", "c"]},

        duo_exam: { field_caption: ["", "Abbrev_subject_2lines", "Subject", "Leerweg", "DUO_description",
                                "Exam_type", "N_term", "schaallengte_2lines", ""],
                field_names: ["select", "subjbase_code", "subj_name", "lvl_abbrev", "ntb_omschrijving",
                            "examperiod", "nterm", "scalelength", "status"],
                field_tags: ["div", "div", "div", "div", "div", "div", "input", "input","div"],
                filter_tags: ["text",  "text", "text", "text", "text", "text",  "text", "text","status"],
                field_width: ["020", "075", "240", "120",  "300", "120", "090","090", "032"],
                field_align: ["c",  "c", "l", "l", "l", "l", "c", "c", "c"]},

        grades: {field_caption: ["", "Examnumber_twolines", "Candidate",  "Leerweg", "Cluster", "Abbrev_subject_2lines",
                                "Subject", "Exam", "Blanks", "Score", "", "Download_exam"],
            field_names: ["select", "examnumber", "fullname", "lvl_abbrev", "cluster_name", "subj_code",
                          "subj_name", "ceex_name", "blanks", "ce_exam_score", "status", "download_exam"],
            field_tags: ["div", "div", "div", "div", "div", "div",
                        "div", "div", "div", "div","div", "a"],
            filter_tags: ["select", "text", "text",  "text", "text", "text",
                            "text", "text",  "text", "text", "status", "text"],
            field_width:  ["020", "075", "240",  "075", "120", "075",
                            "300", "180", "075", "075","032", "090"],
            field_align: ["c", "l", "l", "l", "l", "c",
                         "l", "l", "c", "c", "c", "c"]},

        results: {field_caption: ["", "Abbrev_subject_2lines", "Exam", "Exam_type",
                                "Schoolcode_2lines", "School", "Number_of_exams", "Submitted_exams", "Average_score_percentage", "Download_conv_table_2lines"],
            field_names: ["select", "subj_code", "exam_name", "examperiod",
                          "schoolbase_code", "school_name", "grd_count", "result_count", "result_avg", "download_conv_table"],

            field_tags: ["div", "div", "div", "div",
                        "div", "div", "div", "div", "div", "a"],
            filter_tags: ["select", "text", "text","text",
                            "text", "text",  "text", "text", "text", "text"],
            field_width:  ["020", "075", "360", "120",
                            "075", "280", "090", "090", "090", "100"],
            field_align: ["c", "c", "l", "l",
                         "c", "l", "c", "c", "c", "c"]},

        ntermen: {  field_caption: ["", "opl_code", "leerweg", "ext_code", "tijdvak", "nex_id",
                          "omschrijving", "schaallengte", "N_term", "afnamevakid", "extra_vakcodes_tbv_wolf",
                          "datum", "begintijd", "eindtijd"],
            field_names: ["select", "opl_code", "leerweg", "ext_code", "tijdvak", "nex_id",
                          "omschrijving", "schaallengte", "n_term", "afnamevakid", "extra_vakcodes_tbv_wolf",
                          "datum", "begintijd", "eindtijd"],
            field_tags: ["div", "div", "div", "div","div","div",
                        "div", "div", "div", "div","div",
                        "div", "div", "div"],
            filter_tags: ["select", "text", "text",  "text", "text", "text",
                            "text", "text",  "text", "text", "text",
                            "text", "text",  "text"],
            field_width:  ["020", "075", "075", "075", "075", "075",
                            "480", "110", "090", "110", "180",
                            "090", "075", "075"],
            field_align: ["c", "l", "l", "l", "c", "c",
                            "l", "c", "c", "c", "l",
                            "c", "c", "c"]}
        };

    const tblHead_datatable = document.getElementById("id_tblHead_datatable");
    const tblBody_datatable = document.getElementById("id_tblBody_datatable");

// === EVENT HANDLERS ===
// === reset filter when clicked on Escape button ===
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") { ResetFilterRows();};
        });

 // freeze table header PR2022-01-19
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
                // true = 'all_counties = true', used to let ETE select all deps, schools must only be able to select their deps
                const all_countries = permit_dict.requsr_role_admin;
                t_MSED_Open(loc, "department", department_map, setting_dict, permit_dict, MSED_Response, all_countries)}, false );
        };
        const el_hdrbar_school = document.getElementById("id_hdrbar_school");
        if (el_hdrbar_school){
            // PR2022-04-19 Sentry error: school_map is not defined
            // solved by replacing school_map by school_rows
            el_hdrbar_school.addEventListener("click",
                function() {t_MSSSS_Open(loc, "school", school_rows, false, setting_dict, permit_dict, MSSSS_Response)}, false );
        };

        const el_header_left = document.getElementById("id_header_left");

// ---  SIDEBAR ------------------------------------
        // el_SBR_select_examperiod only exists when not is_requsr_same_school
        const el_SBR_select_examperiod = document.getElementById("id_SBR_select_period");
        if (el_SBR_select_examperiod){
            el_SBR_select_examperiod.addEventListener("change", function() {HandleSbrPeriod(el_SBR_select_examperiod)}, false );
        };
        const el_SBR_select_level = document.getElementById("id_SBR_select_level");
        if (el_SBR_select_level){
            el_SBR_select_level.addEventListener("change", function() {HandleSbrLevel(el_SBR_select_level)}, false );
        };
        const add_all = true;
        const el_SBR_select_subject = document.getElementById("id_SBR_select_subject");
        if (el_SBR_select_subject){
            el_SBR_select_subject.addEventListener("click",
                function() {t_MSSSS_Open(loc, "subject", subject_rows, add_all, setting_dict, permit_dict, MSSSubjStud_Response)}, false)};

        // el_SBR_select_cluster only exists when is_requsr_same_school
        const el_SBR_select_cluster = document.getElementById("id_SBR_select_cluster");
        if (el_SBR_select_cluster){
            el_SBR_select_cluster.addEventListener("click",
                function() {t_MSSSS_Open(loc, "cluster", cluster_rows, add_all, setting_dict, permit_dict, MSSSubjStud_Response)}, false)};

        // el_SBR_select_student only exists when is_requsr_same_school
        const el_SBR_select_student = document.getElementById("id_SBR_select_student");
        if (el_SBR_select_student){
            el_SBR_select_student.addEventListener("click",
                function() {t_MSSSS_Open(loc, "student", student_rows, add_all, setting_dict, permit_dict, MSSSubjStud_Response)}, false)};

        const el_SBR_select_showall = document.getElementById("id_SBR_select_showall");
        if (el_SBR_select_showall){
            el_SBR_select_showall.addEventListener("click", function() {HandleShowAll()}, false )};
        const el_SBR_item_count = document.getElementById("id_SBR_item_count")

// ---  MSSS MOD SELECT SCHOOL / SUBJECT / STUDENT ------------------------------
        const el_MSSSS_input = document.getElementById("id_MSSSS_input");
        const el_MSSSS_tblBody = document.getElementById("id_MSSSS_tbody_select");
        const el_MSSSS_btn_save = document.getElementById("id_MSSSS_btn_save");
        if (el_MSSSS_input){
            el_MSSSS_input.addEventListener("keyup", function(event){
                setTimeout(function() {t_MSSSS_InputKeyup(el_MSSSS_input)}, 50)});
        }
        if (el_MSSSS_btn_save){
            el_MSSSS_btn_save.addEventListener("click", function() {t_MSSSS_Save(el_MSSSS_input, MSSSubjStud_Response)}, false );
        }

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

// ---  MEX MOD EXAM ------------------------------
        const el_MEXQ_questions = document.getElementById("id_mod_exam_questions");
        const el_MEXQ_header1 = document.getElementById("id_MEXQ_header1");
        const el_MEXQ_header2 = document.getElementById("id_MEXQ_header2");
        const el_MEXQ_header3_student = document.getElementById("id_MEXQ_header3");
        const el_MEXQ_tblBody_subjects = document.getElementById("id_MEXQ_tblBody_subjects");

        const el_MEXQ_select_subject = document.getElementById("id_MEXQ_select_subject");
        if (el_MEXQ_select_subject){el_MEXQ_select_subject.addEventListener("click", function() {MEXQ_BtnSelectSubjectClick()}, false);};

        const el_MEXQ_select_level = document.getElementById("id_MEXQ_select_level");
        if (el_MEXQ_select_level){
            el_MEXQ_select_level.addEventListener("change", function() {MEXQ_InputLevel(el_MEXQ_select_level)}, false );
        };

        const el_MEXQ_input_version = document.getElementById("id_MEXQ_input_version");
        if (el_MEXQ_input_version){
            el_MEXQ_input_version.addEventListener("change", function() {MEXQ_InputVersion(el_MEXQ_input_version)}, false );
        };

        const el_MEXQ_checkbox_ep01 = document.getElementById("id_MEXQ_checkbox_ep01");
        if (el_MEXQ_checkbox_ep01){
            el_MEXQ_checkbox_ep01.addEventListener("change", function() {MEXQ_ExamperiodCheckboxChange(1, el_MEXQ_checkbox_ep01)}, false );
        };
        const el_MEXQ_checkbox_ep02 = document.getElementById("id_MEXQ_checkbox_ep02");
        if (el_MEXQ_checkbox_ep02){
            el_MEXQ_checkbox_ep02.addEventListener("change", function() {MEXQ_ExamperiodCheckboxChange(2, el_MEXQ_checkbox_ep02)}, false );
        };
        const el_MEXQ_checkbox_ep03 = document.getElementById("id_MEXQ_checkbox_ep03");
        if (el_MEXQ_checkbox_ep03){
            el_MEXQ_checkbox_ep03.addEventListener("change", function() {MEXQ_ExamperiodCheckboxChange(3, el_MEXQ_checkbox_ep03)}, false );
        };
        const el_MEXQ_has_partex_checkbox = document.getElementById("id_MEXQ_has_partex_checkbox");
        if (el_MEXQ_has_partex_checkbox){
            el_MEXQ_has_partex_checkbox.addEventListener("change", function() {MEXQ_HasPartexCheckboxChange(el_MEXQ_has_partex_checkbox)}, false );
        };

        const el_MEXQ_input_amount = document.getElementById("id_MEXQ_input_amount");
        if (el_MEXQ_input_amount){
            el_MEXQ_input_amount.addEventListener("keyup", function(){
                setTimeout(function() {MEXQ_InputAmount(el_MEXQ_input_amount)}, 50)})
        };
        const el_MEX_err_amount = document.getElementById("id_MEXQ_err_amount");

        const el_MEXQ_input_scalelength = document.getElementById("id_MEXQ_input_scalelength");

        const el_MEX_btn_tab_container = document.getElementById("id_MEXQ_btn_tab_container");
        if (el_MEX_btn_tab_container){
            const btns = el_MEX_btn_tab_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                btn.addEventListener("click", function() {MEX_BtnTabClicked(btn)}, false );
            };
        };
        const el_MEX_btn_pge_container = document.getElementById("id_MEXQ_btn_pge_container");
        if (el_MEX_btn_pge_container){
            const btns = el_MEX_btn_pge_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                btn.addEventListener("click", function() {MEX_BtnPageClicked(btn)}, false );
            };
        };
        const el_MEXQ_btn_save = document.getElementById("id_MEXQ_btn_save");
        if (el_MEXQ_btn_save){
            el_MEXQ_btn_save.addEventListener("click", function() {MEX_Save()}, false )
        }

        const el_MEXQ_partex1_container = document.getElementById("id_MEXQ_partex1_container");
        const el_MEXQ_partex2_container = document.getElementById("id_MEXQ_partex2_container");

        const el_MEXQ_tblBody_partex1 = document.getElementById("id_MEXQ_tblBody_partex1");

        // id_MEXQ_tblBody_partex2 is list of partex in tab questions, keys, minscore
        const el_MEXQ_tblBody_partex2 = document.getElementById("id_MEXQ_tblBody_partex2");

        const el_MEXQ_btngroup_add_partex = document.getElementById("id_MEXQ_btngroup_add_partex");

        const el_MEXQ_btn_partex_add = document.getElementById("id_MEXQ_btn_partex_add");
        if(el_MEXQ_btn_partex_add){el_MEXQ_btn_partex_add.addEventListener("click", function() {MEXQ_BtnPartexClick("add")}, false)};
        const el_MEXQ_btn_partex_edit = document.getElementById("id_MEXQ_btn_partex_edit");
        if(el_MEXQ_btn_partex_edit){el_MEXQ_btn_partex_edit.addEventListener("click", function() {MEXQ_BtnPartexClick("update")}, false)};
        const el_MEXQ_btn_partex_delete = document.getElementById("id_MEXQ_btn_partex_delete");
        if(el_MEXQ_btn_partex_delete){el_MEXQ_btn_partex_delete.addEventListener("click", function() {MEXQ_BtnPartexClick("delete")}, false)};

        const el_MEXQ_group_partex_name = document.getElementById("id_MEXQ_group_partex_name");

        const el_MEXQ_input_partex_name = document.getElementById("id_MEXQ_input_partex_name");
        const el_MEXQ_err_partex_name = document.getElementById("id_MEXQ_err_partex_name");
        const el_MEXQ_input_partex_amount = document.getElementById("id_MEXQ_partex_amount");
        const el_MEXQ_err_partex_amount = document.getElementById("id_MEXQ_err_partex_amount");

        const el_MEXQ_btn_partex_cancel = document.getElementById("id_MEXQ_btn_partex_cancel");
        if(el_MEXQ_btn_partex_cancel){el_MEXQ_btn_partex_cancel.addEventListener("click", function() {MEXQ_BtnPartexClick("cancel")}, false)};
        const el_MEXQ_btn_partex_save = document.getElementById("id_MEXQ_btn_partex_save");
        if(el_MEXQ_btn_partex_save){el_MEXQ_btn_partex_save.addEventListener("click", function() {MEXQ_BtnPartexClick("save")}, false)};

        const el_MEXQ_msg_modified = document.getElementById("id_MEXQ_msg_modified");

// ---  MODAL APPROVE EXAM ------------------------------------
        const el_MASE_header = document.getElementById("id_MASE_header");

        const el_MASE_select_container = document.getElementById("id_MASE_select_container");
            const el_MASE_subheader = document.getElementById("id_MASE_subheader");
            const el_MASE_examperiod = document.getElementById("id_MASE_examperiod");

        const el_MASE_subj_lvl_cls_container = document.getElementById("id_MASE_subj_lvl_cls_container");
            const el_MASE_subject = document.getElementById("id_MASE_subject");
            const el_MASE_lvlbase = document.getElementById("id_MASE_lvlbase");
            const el_MASE_cluster = document.getElementById("id_MASE_cluster");

        const el_MASE_info_request_msg1 = document.getElementById("id_MASE_info_request_msg1");
        const el_MASE_info_request_verifcode = document.getElementById("id_MASE_info_request_verifcode");

        const el_MASE_approved_by_label = document.getElementById("id_MASE_approved_by_label");
        const el_MASE_approved_by = document.getElementById("id_MASE_approved_by");
        const el_MASE_auth_index = document.getElementById("id_MASE_auth_index");
        if (el_MASE_auth_index){
            el_MASE_auth_index.addEventListener("change", function() {MASE_UploadAuthIndex(el_MASE_auth_index)}, false );
        };

        const el_MASE_loader = document.getElementById("id_MASE_loader");
        const el_MASE_info_container = document.getElementById("id_MASE_info_container");
        const el_MASE_msg_container = document.getElementById("id_MASE_msg_container");

        const el_MASE_input_verifcode = document.getElementById("id_MASE_input_verifcode");
        if (el_MASE_input_verifcode){
            el_MASE_input_verifcode.addEventListener("keyup", function() {MASE_InputVerifcode(el_MASE_input_verifcode, event.key)}, false);
            el_MASE_input_verifcode.addEventListener("change", function() {MASE_InputVerifcode(el_MASE_input_verifcode)}, false);
        };
        const el_MASE_btn_delete = document.getElementById("id_MASE_btn_delete");
        if (el_MASE_btn_delete){
            el_MASE_btn_delete.addEventListener("click", function() {MASE_Save("delete")}, false )  // true = reset
        };
        const el_MASE_btn_save = document.getElementById("id_MASE_btn_save");
        if (el_MASE_btn_save){
            el_MASE_btn_save.addEventListener("click", function() {MASE_Save("save")}, false )
        };
        const el_MASE_btn_cancel = document.getElementById("id_MASE_btn_cancel");

// ---  MODAL LINK DUO EXAMS ------------------------------------
        const el_MDUO_examperiod = document.getElementById("id_MDUO_examperiod");
        const el_MDUO_level = document.getElementById("id_MDUO_level");

        const el_MDUO_tblBody_subjects = document.getElementById("id_MDUO_tblBody_subjects");
        const el_MDUO_tblBody_duo_exams = document.getElementById("id_MDUO_tblBody_duo_exams");

        const el_MDUO_filter_subjects = document.getElementById("id_MDUO_filter_subjects");
        const el_MDUO_filter_exams = document.getElementById("id_MDUO_filter_exams");

        const el_MDUO_btn_save = document.getElementById("id_MDUO_btn_save");
        if (el_MDUO_btn_save){
            el_MDUO_btn_save.addEventListener("click", function() {MDUO_Save("save")}, false )
        };

// ---  MOD UPLOAD N-termen TABLE ------------------------------------
        const el_MDNT_filedialog = document.getElementById("id_MDNT_filedialog");
        if (el_MDNT_filedialog){
            el_MDNT_filedialog.addEventListener("change", function() {MDNT_HandleFiledialog(el_MDNT_filedialog)}, false)};
        const el_MDNT_btn_filedialog = document.getElementById("id_MDNT_btn_filedialog");
        if (el_MDNT_filedialog && el_MDNT_btn_filedialog){
            el_MDNT_btn_filedialog.addEventListener("click", function() {MDNT_OpenFiledialog(el_MDNT_filedialog)}, false)};
        const el_MDNT_filename = document.getElementById("id_MDNT_filename");
        const el_MDNT_btn_save = document.getElementById("id_MDNT_btn_save");
        if (el_MDNT_btn_save){
            el_MDNT_btn_save.addEventListener("click", function() {MDNT_Save(RefreshDataRowsAfterUpload, setting_dict)}, false )};

// ---  MOD CONFIRM ------------------------------------
        const el_confirm_header = document.getElementById("id_modconfirm_header");
        const el_confirm_loader = document.getElementById("id_modconfirm_loader");
        const el_confirm_msg_container = document.getElementById("id_modconfirm_msg_container");
        const el_confirm_msg01 = document.getElementById("id_modconfirm_msg01");
        const el_confirm_msg02 = document.getElementById("id_modconfirm_msg02");
        const el_confirm_msg03 = document.getElementById("id_modconfirm_msg03");
        const el_confirm_btn_cancel = document.getElementById("id_modconfirm_btn_cancel");
        const el_confirm_btn_save = document.getElementById("id_modconfirm_btn_save");
        if(el_confirm_btn_save){
            el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()})
        };

// ---  MOD STATUS ------------------------------------
        const el_mod_status_btn_save =  document.getElementById("id_mod_status_btn_save");
        const el_mod_status_header = document.getElementById("id_mod_status_header");
        const el_mod_status_note_container = document.getElementById("id_mod_status_note_container");
        if(el_mod_status_btn_save){el_mod_status_btn_save.addEventListener("click", function() {ModalStatusSave()}, false )};

// ---  MOD MESSAGE ------------------------------------
        const el_mod_message_btn_cancel = document.getElementById("id_mod_message_btn_cancel");
        const el_mod_message_container = document.getElementById("id_mod_message_container");
        if(el_mod_message_btn_cancel){
            el_mod_message_btn_cancel.addEventListener("click", function() {ModMessageClose()}, false);
        }

// ---  MODAL SELECT COLUMNS ------------------------------------
        const el_MCOL_btn_save = document.getElementById("id_MCOL_btn_save")
        if(el_MCOL_btn_save){
            el_MCOL_btn_save.addEventListener("click", function() {
                t_MCOL_Save(urls.url_usersetting_upload, HandleBtnSelect)}, false )
        };

    if(may_view_page){
// ---  set selected menu button active
       // SetMenubuttonActive(document.getElementById("id_hdr_users"));

        const datalist_request = {
                setting: {page: "page_exams"},
                locale: {page: ["page_exams", "page_grade"]},
                examyear_rows: {get: true},
                school_rows: {get: true},
                department_rows: {get: true},
                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},
                subject_rows: {etenorm_only: true, cur_dep_only: true},
                cluster_rows: {cur_dep_only: true},

                student_rows: {cur_dep_only: true},

                duo_subject_rows: {get: true},
                ete_exam_rows: {get: true},
                duo_exam_rows: {get: true},
                grade_exam_rows: {get: true},
                grade_exam_result_rows: {get: true},
                ntermentable_rows: {get: ntermentable_rows},

                published_rows: {get: true}
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
        if(!keep_loader_hidden){
            el_loader.classList.remove(cls_visible_hide);
        };
        add_or_remove_class(el_header_left.parentNode, cls_visible_hide, !keep_loader_hidden);

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

                let must_create_submenu = false, must_update_headerbar = false;

                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                    must_create_submenu = true;
                };

                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    // get_permits must come before CreateSubmenu and FiLLTbl
                    b_get_permits_from_permitlist(permit_dict);
                    must_update_headerbar = true;

                }
                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict;

                    selected_btn = setting_dict.sel_btn;

                    // if sel_subject_pk has value, set sel_student_pk null
                    if (setting_dict.sel_subject_pk) {setting_dict.sel_student_pk = null;}

                    MSSSS_display_in_sbr_reset()

            // ---  fill cols_hidden
                    if("cols_hidden" in setting_dict){
                        //  setting_dict.cols_hidden was dict with key 'all' or se_btn, changed to array PR2021-12-14
                        //  skip when setting_dict.cols_hidden is not an array,
                        // will be changed into an array when saving with t_MCOL_Save
                        if (Array.isArray(setting_dict.cols_hidden)) {
                             b_copy_array_noduplicates(setting_dict.cols_hidden, mod_MCOL_dict.cols_hidden);
                        };

                        // PR2022-05-15 remove field "download_conv_table" from columns_tobe_hidden.btn_results when role != ROLE_008_SCHOOL
                        // because this field is removed from table 'results' when user is admin
                        if(permit_dict.requsr_role === 8 ){
                            // when school: skip column 'school_name'
                            mod_MCOL_dict.cols_skipped = {btn_results: ["school_name"]}
                        } else {
                            // when admin col 'download_conv_table' is shown in table exam, skip in table results
                            mod_MCOL_dict.cols_skipped = {btn_results: ["download_conv_table"]}
                        };
                    };
                    must_update_headerbar = true;
                };

                if(must_create_submenu){CreateSubmenu()};

                if(must_update_headerbar){
                    b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);
                    FillOptionsExamperiod();
                };
                if ("messages" in response) {
                    b_show_mod_message_dictlist(response.messages);
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
                };

                // hide select level when department has no levels, also hide in modal approve exam
                add_or_remove_class(el_SBR_select_level.parentNode, cls_hide, !setting_dict.sel_dep_level_req);
                add_or_remove_class(el_MASE_lvlbase.parentNode, cls_hide, !setting_dict.sel_dep_level_req);

                if (el_SBR_select_level && setting_dict.sel_dep_level_req){
                    t_SBR_FillSelectOptionsDepbaseLvlbaseSctbase("lvlbase", response.level_rows, setting_dict);
                    // also display selected level in modal approve exam. This code must come here, not in MASE_Open,
                    // to update el_MASE_lvlbase when MASE is opened immediately after changing level in SBR
                    // PR2022-04-07 debug: options not filled yet
                    if (el_MASE_lvlbase && el_SBR_select_level.options){
                        el_MASE_lvlbase.innerText = el_SBR_select_level.options[el_SBR_select_level.selectedIndex].innerText;
                    };
                };
                if ("student_rows" in response) {
                    student_rows = response.student_rows;
                };
                if ("subject_rows" in response) {subject_rows = response.subject_rows};
                t_MSSSS_display_in_sbr("subject", setting_dict.sel_subject_pk);

                if ("cluster_rows" in response) {cluster_rows = response.cluster_rows};

                if ("ete_exam_rows" in response) {ete_exam_rows = response.ete_exam_rows};
                if ("duo_subject_rows" in response) {duo_subject_rows = response.duo_subject_rows};
                if ("duo_exam_rows" in response) {duo_exam_rows = response.duo_exam_rows};
                if ("grade_exam_rows" in response) {grade_exam_rows = response.grade_exam_rows};
                if ("grade_exam_result_rows" in response) {grade_exam_result_rows = response.grade_exam_result_rows};

                if ("ntermentable_rows" in response) {ntermentable_rows = response.ntermentable_rows};

                HandleBtnSelect(null, true)  // true = skip_upload
                // also calls: FillTblRows(), MSSSS_display_in_sbr(), UpdateHeader()ect
            },
            error: function (xhr, msg) {
// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                console.log(msg + '\n' + xhr.responseText);
            }
        });
    }  // function DatalistDownload

//=========  CreateSubmenu  ===  PR2020-07-31 PR2021-01-19 PR2021-03-25 PR2021-05-25
    function CreateSubmenu() {
        //console.log("===  CreateSubmenu == ");
        //console.log("permit_dict.permit_submit_exam", permit_dict.permit_submit_exam);
        //console.log("permit_dict.requsr_same_school", permit_dict.requsr_same_school);

        let el_submenu = document.getElementById("id_submenu")
        // PR2022-05-19 Only CUR admin can add exams!!! It will get messed-up if SXM starts enetering stuff here
        if(permit_dict.permit_crud && permit_dict.requsr_role_admin && permit_dict.requsr_country_pk === 1){
            AddSubmenuButton(el_submenu, loc.Add_exam, function() {MEXQ_Open()}, ["tab_show", "tab_btn_ete_exams"]);
            AddSubmenuButton(el_submenu, loc.Delete_exam, function() {ModConfirmOpen("ete_exam", "delete")}, ["tab_show", "tab_btn_ete_exams"]);
            AddSubmenuButton(el_submenu, loc.Copy_exam, function() {ModConfirmOpen("ete_exam", "copy")}, ["tab_show", "tab_btn_ete_exams"]);
            AddSubmenuButton(el_submenu, loc.Link_DUO_exams, function() {MDUO_Open()}, ["tab_show", "tab_btn_duo_exams"]);
            AddSubmenuButton(el_submenu, loc.Unlink_DUO_exam, function() {ModConfirmOpen("duo_exam", "delete")}, ["tab_show", "tab_btn_duo_exams"]);
            //AddSubmenuButton(el_submenu, loc.Link_DUO_to_grade_exam, function() {ModConfirm_LinkDuo_exam_grade_Open()}, ["tab_show", "tab_btn_duo_exams"]);
            //AddSubmenuButton(el_submenu, loc.Calculate_grades, function() {ModConfirm_calculate_grades_Open()}, ["tab_show", "tab_btn_ete_exams", "tab_btn_duo_exams"]);
        }

        if (permit_dict.requsr_role_admin && permit_dict.requsr_country_pk === 1){
            if (permit_dict.permit_approve_exam ){
                AddSubmenuButton(el_submenu, loc.Approve_exams, function() {MASE_Open("approve_admin")}, ["tab_show", "tab_btn_ete_exams"]);
            };
            if (permit_dict.permit_publish_exam ){
                AddSubmenuButton(el_submenu, loc.Publish_exams, function() {MASE_Open("submit_admin")}, ["tab_show", "tab_btn_ete_exams"]);
                AddSubmenuButton(el_submenu, loc.Undo_published, function() {ModConfirmOpen("ete_exam", "undo_published")}, ["tab_show", "tab_btn_ete_exams"]);
            };
        } else if (permit_dict.requsr_role_school){
            if (permit_dict.permit_approve_exam ){
                AddSubmenuButton(el_submenu, loc.Approve_exams, function() {MASE_Open("approve_school")}, ["tab_showXX", "tab_btn_ete_exams"]);
            };
            if (permit_dict.permit_submit_exam ){
                AddSubmenuButton(el_submenu, loc.Submit_exams, function() {MASE_Open("submit_school")}, ["tab_showXX", "tab_btn_ete_exams"]);
                AddSubmenuButton(el_submenu, loc.Undo_submitted, function() {ModConfirmOpen("grades", "undo_submitted")}, ["tab_showXX", "tab_btn_ete_exams"]);
            };
        };

        if(permit_dict.permit_crud && permit_dict.requsr_role_admin && permit_dict.requsr_country_pk === 1){
            AddSubmenuButton(el_submenu, loc.Upload_ntermen, function() {MDNT_Open()}, ["tab_show", "tab_btn_ntermen"], "id_submenu_upload_dnt");
            AddSubmenuButton(el_submenu, loc.Download_JSON, function() {ModConfirmOpen("ete_exam", "json")}, ["tab_show", "tab_btn_results"]);
        };

        AddSubmenuButton(el_submenu, loc.Hide_columns, function() {t_MCOL_Open("page_exams")}, [], "id_submenu_columns")

        //AddSubmenuButton(el_submenu, loc.Preliminary_Ex2A, null, "id_submenu_download_ex2a", urls.url_grade_download_ex2a, true);  // true = download
        //if (permit.approve_grade){
        //    AddSubmenuButton(el_submenu, loc.Approve_grades, function() {MASE_Open("approve")});
        //}
        //if (permit.submit_grade){
        //    AddSubmenuButton(el_submenu, loc.Submit_Ex_form, function() {MASE_Open("submit")});
        //};
        el_submenu.classList.remove(cls_hide);

    };//function CreateSubmenu

//###########################################################################
// +++++++++++++++++ EVENT HANDLERS +++++++++++++++++++++++++++++++++++++++++
//=========  HandleBtnSelect  ================ PR2020-09-19  PR2020-11-14  PR2021-03-15 PR2022-01-31 PR2022-02-28
    function HandleBtnSelect(data_btn, skip_upload) {
        //console.log( "===== HandleBtnSelect ========= ");
        //console.log( "data_btn", data_btn);
        //console.log( "skip_upload", skip_upload);

        // function is called by MSSSS_Response, select_btn.click, DatalistDownload after response.setting_dict
        //  data_btn only inm use when requsr_role_admin

        // value of data_btn are:
        // when admin: "btn_ete_exams" "btn_duo_exams" "btn_ntermen" "btn_results"
        // when school: "btn_ep_01" "btn_reex"
        // PR20220-05-04 debug: also change examperiod when setting "btn_ep_01" or "btn_reex"

// ---  get data_btn from selected_btn when null;
        if (!data_btn) {data_btn = selected_btn};

// check if data_btn exists, gave error because old btn name was still in saved setting PR2021-09-07 debug
        if (!permit_dict.requsr_role_admin){
            const btns_allowed = ["btn_ep_01", "btn_reex", "btn_results"];
            if (data_btn && btns_allowed.includes(data_btn)) {
                selected_btn = data_btn;
            } else {
                selected_btn = btns_allowed[0];
            };

        } else {
            const btns_allowed = ["btn_ete_exams", "btn_duo_exams", "btn_ntermen", "btn_results"];
            if (data_btn && btns_allowed.includes(data_btn)) {
                selected_btn = data_btn;
            } else if (btns_allowed.length) {
                selected_btn = btns_allowed[0];
            } else {
                selected_btn = null;
            };
        };

    //console.log( "btns_allowed", btns_allowed);
    //console.log( "data_btn", data_btn);
    //console.log( "selected_btn", selected_btn);
        setting_dict.sel_btn = selected_btn;

    //console.log( "selected_btn", selected_btn);

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
    // ---  upload new setting

            // request_item_setting: {'page': 'page_exams', 'page_exams': {'sel_btn': 'btn_reex'}, 'sel_examperiod': 2}

            let new_setting = {page: 'page_exams'};

            new_setting.page_exams = {sel_btn: selected_btn};
            if (selected_btn === "btn_ep_01"){
                new_setting.sel_examperiod = 1;
            } else if (selected_btn === "btn_reex"){
                new_setting.sel_examperiod = 2;
            };

    // also retrieve the tables that have been changed because of the change in examperiod
            const datalist_request = {setting: new_setting,
                    ete_exam_rows: {get: true},
                    duo_subject_rows: {get: true},
                    duo_exam_rows: {get: true},
                    ntermentable_rows: {get: true},
                    published_rows: {get: true}
            };
            if (permit_dict.requsr_same_school){
                datalist_request.grade_exam_rows = {get: true};
            };
            DatalistDownload(datalist_request);
        };

// ---  highlight selected button
        b_highlight_BtnSelect(el_btn_container, selected_btn);

// ---  show only the elements that are used in this tab
        // Note Mexq has also tab_classes. Make sure they have different names
        b_show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

// --- update header text - comes after MSSSS_display_in_sbr
        UpdateHeaderLeftRight(skip_upload);

// ---  fill datatable
        FillTblRows();

    };  // HandleBtnSelect

//=========  HandleTblRowClicked  ================ PR2020-08-03 PR2021-05-22
    function HandleTblRowClicked(tblRow) {
        console.log("=== HandleTblRowClicked");
        console.log( "tblRow: ", tblRow);

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        //DeselectHighlightedRows(tblRow, cls_selected);
        //tblRow.classList.add(cls_selected);

// ---  deselect all highlighted rows, select clicked row
        t_td_selected_toggle(tblRow, true);  // select_single = True

// ---  lookup exam_dict in exam_rows
        const tblName = get_attr_from_el(tblRow, "data-table")
        const data_rows = get_datarows_from_tblName(tblName);

        // PR2022-05-11 Sentry debug: Unhandled Expected identifier with IE11 on Windows 7
        // leave it as it is, maybe error caused by IE 11
        const data_pk = get_attr_from_el_int(tblRow, "data-pk")
        const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", data_pk);
        const pk_int = (!isEmpty(found_dict)) ? found_dict.id : null;

    //console.log( "found_dict: ", found_dict);
    console.log( "tblName: ", tblName);
    console.log( "data_pk: ", pk_int, typeof data_pk);
    console.log( "found_dict: ", found_dict);

// ---  update setting_dict.pk_int
        if (tblName === "duo_exam"){
            setting_dict.sel_duo_exam_pk = (pk_int) ? pk_int : null;
        } else if (tblName === "ete_exam"){
            setting_dict.sel_exam_pk = (pk_int) ? pk_int : null;
        } else if (tblName === "grades"){
            setting_dict.sel_grade_exam_pk = (pk_int) ? pk_int : null;
        };
    };  // HandleTblRowClicked

//=========  HandleSbrPeriod  ================ PR2020-12-20 PR2022-02-21
    function HandleSbrPeriod(el_select) {
        console.log("=== HandleSbrPeriod");

        setting_dict.sel_examperiod = (Number(el_select.value)) ? Number(el_select.value) : null;

// ---  upload new setting
        let new_setting = {page: 'page_exams',
                           sel_examperiod: setting_dict.sel_examperiod};
// also retrieve the tables that have been changed because of the change in examperiod
        const datalist_request = {setting: new_setting,
                ete_exam_rows: {get: true},
                duo_subject_rows: {get: true},
                duo_exam_rows: {get: true},
                ntermentable_rows: {get: true},
                grade_exam_rows: {get: true},
                grade_exam_result_rows: {get: true},
                published_rows: {get: true}
        };

        DatalistDownload(datalist_request);

    }  // HandleSbrPeriod

//=========  HandleSbrExamtype  ================ PR2020-12-20
    function HandleSbrExamtype(el_select) {
        console.log("=== HandleSbrExamtype");
        //console.log( "el_select.value: ", el_select.value, typeof el_select.value)
        // sel_examtype = "se", "pe", "ce", "reex", "reex03", "exem"
        setting_dict.sel_examtype = el_select.value;

// ---  upload new setting
        const upload_dict = {selected_pk: {sel_examtype: setting_dict.sel_examtype}};
        b_UploadSettings (upload_dict, urls.url_usersetting_upload);

        FillTblRows();
    }  // HandleSbrExamtype

//=========  HandleSbrLevel  ================ PR2021-03-06 PR2021-05-07
    function HandleSbrLevel(el_select) {
        console.log("=== HandleSbrLevel");

        setting_dict.sel_lvlbase_pk = (Number(el_select.value)) ? Number(el_select.value) : null;
        setting_dict.sel_level_abbrev = (el_select.options[el_select.selectedIndex]) ? el_select.options[el_select.selectedIndex].innerText : null;

// ---  upload new setting
        let new_setting = {page: 'page_exams',
                           sel_lvlbase_pk: setting_dict.sel_lvlbase_pk};
// also retrieve the tables that have been changed because of the change in examperiod
        const datalist_request = {setting: new_setting,
                duo_subject_rows: {get: true},
                ete_exam_rows: {get: true},
                duo_exam_rows: {get: true},
                grade_exam_rows: {get: true},
                grade_exam_result_rows: {get: true},
                ntermentable_rows: {get: true},
                published_rows: {get: true}
        };

        DatalistDownload(datalist_request);
    };  // HandleSbrLevel

//=========  FillOptionsExamperiod  ================ PR2021-03-08 PR2022-02-20
    function FillOptionsExamperiod() {
        //console.log("=== FillOptionsExamperiod");
        //console.log("el_SBR_select_examperiod", el_SBR_select_examperiod);
        if (el_SBR_select_examperiod){

        // examperiod is selected with sel_btn when grades, hide sbr btn when is_permit_same_school
            const is_permit_admin = (permit_dict.requsr_role_admin && permit_dict.permit_crud);
            add_or_remove_class(el_SBR_select_examperiod.parentNode, cls_hide, !is_permit_admin);

            if (is_permit_admin){
                const sel_examperiod = setting_dict.sel_examperiod;

                // don't show 'all exam periods' (loc.options_examperiod_exam[0]] when is_requsr_same_school;
                const option_list = loc.options_examperiod_exam;

                //let option_list = [];
                //if (permit_dict.requsr_role_admin) {
                //    option_list = loc.options_examperiod_exam;
                //} else {
                //    for (let i = 1, option_dict; option_dict = loc.options_examperiod_exam[i]; i++) {
                //        option_list.push(option_dict);
                //    };
                //};

                t_FillOptionsFromList(el_SBR_select_examperiod, option_list, "value", "caption",
                    loc.Select_examperiod + "...", loc.No_examperiods_found, sel_examperiod);

            }  //  if (is_permit_same_school)
        };
    };  // FillOptionsExamperiod

//=========  FillOptionsSelectLevelSector  ================ PR2021-03-06  PR2021-05-22
    function FillOptionsSelectLevelSector(tblName, rows) {
    // NIU PR2022-02-23
        //console.log("=== FillOptionsSelectLevelSector");
        //console.log("tblName", tblName);
        //console.log("rows", rows);

    // sector not in use
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
                    setting_dict.sel_sector_pk = rows.base_id
                }
            } else if (rows.length > 1){
                // add row 'Alle leerwegen' / Alle profielen / Alle sectoren in first row
                // HTML code "&#60" = "<" HTML code "&#62" = ">";
                display_rows.push({value: 0, caption: caption_all })
            }

            for (let i = 0, row; row = rows[i]; i++) {
                display_rows.push({value: row.base_id, caption: row.abbrev})
            }

            const selected_pk = (tblName === "level") ? setting_dict.sel_lvlbase_pk : (tblName === "sector") ? setting_dict.sel_sector_pk : null;
            const el_SBR_select = (tblName === "level") ? el_SBR_select_level : null;
            t_FillOptionsFromList(el_SBR_select, display_rows, "value", "caption", null, null, selected_pk);

            // put displayed text in setting_dict
            const sel_abbrev = (el_SBR_select.options[el_SBR_select.selectedIndex]) ? el_SBR_select.options[el_SBR_select.selectedIndex].innerText : null;
            if (tblName === "level"){
                setting_dict.sel_level_abbrev = sel_abbrev;
            } else if (tblName === "sector"){
                setting_dict.sel_sector_abbrev = sel_abbrev;
            };
        };
    };  // FillOptionsSelectLevelSector

//=========  HandleShowAll  ================ PR2020-12-17
    function HandleShowAll() {
        console.log("=== HandleShowAll");

        setting_dict.sel_lvlbase_pk = null;
        setting_dict.sel_level_abbrev = null;
        setting_dict.sel_lvlbase_pk = null;

        setting_dict.sel_subject_pk = null;
        setting_dict.sel_cluster_pk = null;
        setting_dict.sel_student_pk = null;

        setting_dict.sel_exam_pk = null;
        setting_dict.sel_duo_exam_pk = null;

    // don't reset sel_examperiod
        //setting_dict.sel_examperiod = 12;
        //if (el_SBR_select_examperiod){
            //el_SBR_select_examperiod.value = "12";
        //};

        if (el_SBR_select_level){
            el_SBR_select_level.value = "null";
        };
        if (el_SBR_select_subject){
            el_SBR_select_level.value = "null";
        };

// ---  upload new setting
        const selected_pk_dict = {
        sel_lvlbase_pk: null,
        sel_sctbase_pk: null,
        sel_subject_pk: null,
        sel_cluster_pk: null,
        sel_student_pk: null,
        sel_examperiod: 12};
        //const page_grade_dict = {sel_btn: "grade_by_all"}
       //const upload_dict = {selected_pk: selected_pk_dict, page_grade: page_grade_dict};
        const upload_dict = {selected_pk: selected_pk_dict};
        console.log("upload_dict", upload_dict);

        b_UploadSettings (upload_dict, urls.url_usersetting_upload);

        HandleBtnSelect(null, true) // true = skip_upload
        // also calls: FillTblRows(), MSSSS_display_in_sbr(), UpdateHeader()

// also retrieve the tables that have been changed because of the change in examperiod
// ---  upload new setting
        let new_setting = {page: 'page_exams',
                            sel_examperiod: null,
                            sel_lvlbase_pk: null,
                            sel_sctbase_pk: null,
                            sel_subject_pk: null,
                            sel_cluster_pk: null,
                            sel_student_pk: null
                          };

        const datalist_request = {setting: new_setting,
                duo_subject_rows: {get: true},
                ete_exam_rows: {get: true},
                duo_exam_rows: {get: true},
                grade_exam_rows: {get: true},
                grade_exam_result_rows: {get: true},
                ntermentable_rows: {get: true},
                published_rows: {get: true}
        }

        DatalistDownload(datalist_request);
    }  // HandleShowAll

//========= UpdateHeaderLeftRight  ================== PR2021-03-14 PR2022-01-17
    function UpdateHeaderLeftRight(skip_upload){
        //console.log(" --- UpdateHeaderLeftRight ---" )
        //console.log("setting_dict", setting_dict)
        //console.log("setting_dict.sel_examperiod", setting_dict.sel_examperiod)

        const examperiod_caption = (setting_dict.sel_examperiod === 1) ? loc.Central_exam :
                                    (setting_dict.sel_examperiod === 2) ? loc.Re_examination : "";
                                    (setting_dict.sel_examperiod === 12) ? [loc.Central_exam, loc.Re_examination].join(" / ") : "";

        const depbase_code = (setting_dict.sel_depbase_code) ? " " + setting_dict.sel_depbase_code : "";
        const level_abbrev = (setting_dict.sel_lvlbase_pk && setting_dict.sel_level_abbrev) ? " " + setting_dict.sel_level_abbrev : "";

        el_header_left.innerText = examperiod_caption + depbase_code + level_abbrev;
        add_or_remove_class(el_header_left.parentNode, cls_visible_hide, !skip_upload);
    };   //  UpdateHeaderLeftRight

//###########################################################################
// +++++++++++++++++ FILL TABLE ROWS ++++++++++++++++++++++++++++++++++++++++
//========= FillTblRows  ====================================
    function FillTblRows() {
        console.log( "===== FillTblRows  === ");

        const tblName = get_tblName_from_selectedBtn();
        const field_setting = field_settings[tblName];
    console.log( "tblName", tblName);
    //console.log( "field_setting", field_setting);

// --- get data_rows
        const data_rows = get_datarows_from_tblName(tblName);

// ---  get list of hidden columns
        // copy col_hidden from mod_MCOL_dict.cols_hidden
        const col_hidden = [];
        b_copy_array_noduplicates(mod_MCOL_dict.cols_hidden, col_hidden)

// - hide level when not level_req
        if(!setting_dict.sel_dep_level_req){col_hidden.push("lvl_abbrev")};

// - hide columns in mod_MCOL_dict.cols_skipped. cols_skipped got value in DatalistDownload
        if (mod_MCOL_dict.cols_skipped.hasOwnProperty(selected_btn)){
            const cols_skipped_list = mod_MCOL_dict.cols_skipped[selected_btn];
            col_hidden.push(...cols_skipped_list);
        };

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;
        selected.item_count = 0;

// --- create table header
        CreateTblHeader(field_setting, col_hidden);

// --- create table rows
        if(data_rows && data_rows.length){
            for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {

            // only show rows of selected student / subject
                let show_row = true;
                if (tblName === "ete_exam"){
                    show_row = (!setting_dict.sel_lvlbase_pk || data_dict.lvlbase_id === setting_dict.sel_lvlbase_pk) &&
                                (!setting_dict.sel_subject_pk || data_dict.subj_id === setting_dict.sel_subject_pk) &&
                                (  (selected_btn === "btn_ete_exams" && data_dict.examtype !== "duo") ||
                                   (selected_btn === "btn_duo_exams" && data_dict.examtype === "duo") );

                } else if (tblName === "btn_duo_exams"){
                    show_row = (!setting_dict.sel_lvlbase_pk || data_dict.lvlbase_id === setting_dict.sel_lvlbase_pk) &&
                               (!setting_dict.sel_subject_pk || data_dict.subj_id === setting_dict.sel_subject_pk);

                } else if (tblName === "grades"){

                    show_row =  (!setting_dict.sel_lvlbase_pk || data_dict.lvlbase_id === setting_dict.sel_lvlbase_pk) &&
                                (!setting_dict.sel_sector_pk || data_dict.sct_id === setting_dict.sel_sector_pk) &&
                                (!setting_dict.sel_subject_pk || data_dict.subj_id === setting_dict.sel_subject_pk) &&
                                (!setting_dict.sel_cluster_pk || data_dict.cluster_id === setting_dict.sel_cluster_pk) &&
                                (!setting_dict.sel_student_pk || data_dict.student_id === setting_dict.sel_student_pk);
                };
                if(show_row){
          // --- insert row
                    let tblRow = CreateTblRow(tblName, field_setting, data_dict, col_hidden)

                    selected.item_count += 1;
                };
            };
        };
    // ---  show total in sidebar
        t_set_sbr_itemcount_txt(loc, selected.item_count, loc.Exam, loc.Exams, setting_dict.user_lang);
    };  // FillTblRows

//=========  CreateTblHeader  === PR2020-12-03 PR2020-12-18 PR2021-01-22
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

    // --- skip column if in columns_hidden
            if (!col_hidden.includes(field_name)){

    // --- get field_caption from field_setting,
                const field_caption = loc[field_setting.field_caption[j]];
                const field_tag = field_setting.field_tags[j];
                const filter_tag = field_setting.filter_tags[j];
                const class_width = "tw_" + field_setting.field_width[j] ;
                const class_align = "ta_" + field_setting.field_align[j];

// ++++++++++ insert columns in header row +++++++++++++++
        // --- add th to tblRow_header +++
                let th_header = document.createElement("th");
        // --- add div to th, margin not working with th
                    const el_header = document.createElement("div");
                        el_header.innerText = (field_caption) ? field_caption : null;
        // --- add left border
                        if(j){th_header.classList.add("border_left")};
        // --- add width, text_align
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
        // --- add EventListener to el_filter
                    if (["text", "number"].includes(filter_tag)) {
                        el_filter.addEventListener("keyup", function(event){HandleFilterKeyup(el_filter, event)});
                        add_hover(th_filter);
                    } else if (filter_tag === "status") {
                        // add EventListener for icon to th_filter, not el_filter
                        th_filter.addEventListener("click", function(event){HandleFilterStatus(el_filter)});
                        th_filter.classList.add("pointer_show");
                        el_filter.classList.add("diamond_3_4");  //  diamond_3_4 is blank img
                        add_hover(th_filter);
                    };
        // --- add other attributes
                    if (filter_tag === "text") {
                        el_filter.setAttribute("type", "text")
                        el_filter.classList.add("input_text");

                        el_filter.setAttribute("autocomplete", "off");
                        el_filter.setAttribute("ondragstart", "return false;");
                        el_filter.setAttribute("ondrop", "return false;");
                    };

        // --- add left border
                if(j){th_filter.classList.add("border_left")};
        // --- add width, text_align, color
                    el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");

                th_filter.appendChild(el_filter)
                tblRow_filter.appendChild(th_filter);
            }  //  if (!columns_hidden[field_name])
        }  // for (let j = 0; j < column_count; j++)

    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09 PR2021-05-23 PR2022-01-19 PR2022-05-20
    function CreateTblRow(tblName, field_setting, data_dict, col_hidden) {
        //console.log("=========  CreateTblRow =========");
        //console.log("tblName", tblName);
        //console.log("field_setting", field_setting);
        //console.log("data_dict", data_dict);
        //console.log("col_hidden", col_hidden, typeof col_hidden);

        const field_names = field_setting.field_names;
        const field_tags = field_setting.field_tags;
        const filter_tags = field_setting.filter_tags;
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;

        const map_id = (data_dict.mapid) ? data_dict.mapid : null;
        const permit_ete_admin_crud_only = (permit_dict.permit_crud && permit_dict.requsr_role_admin && permit_dict.requsr_country_pk === 1)

// ---  lookup index where this row must be inserted
        let ob1 = "", ob2 = "", ob3 = "";
        if (tblName === "ete_exam") {
            ob1 = data_dict.subjbase_code;
            if (data_dict.lvl_abbrev) {ob2 = data_dict.lvl_abbrev};
            ob3 = data_dict.examperiod;
        } else if (tblName === "duo_exam") {
            ob1 = data_dict.subjbase_code;
            if (data_dict.lvl_abbrev) {ob2 = data_dict.lvl_abbrev};
        } else if (tblName === "grades") {
            ob1 = data_dict.lastname;
            ob2 = data_dict.firstname;
            ob3 = data_dict.subj_code;
        } else if (tblName === "results") {
            ob1 = data_dict.exam_name;
            ob2 = data_dict.schoolbase_code;
            ob3 = data_dict.lvl_abbrev;
        } else if (tblName === "ntermen") {
            ob1 = data_dict.omschrijving;
        };

        const row_index = b_recursive_tblRow_lookup(tblBody_datatable, setting_dict.user_lang, ob1, ob2, ob3);

// --- insert tblRow into tblBody at row_index
        const tblRow = tblBody_datatable.insertRow(row_index);
        tblRow.id = map_id;

// --- add data attributes to tblRow
        tblRow.setAttribute("data-pk", data_dict.id);
        tblRow.setAttribute("data-table", tblName);

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
                const filter_tag = filter_tags[j];
                const class_width = "tw_" + field_width[j];
                const class_align = "ta_" + field_align[j];

        // --- insert td element,
                const td = tblRow.insertCell(-1);

        // --- create element with tag from field_tags
                let el = document.createElement(field_tag);

        // --- add data-field attribute
                el.setAttribute("data-field", field_name);

        // --- add EventListener to td
                if (field_name === "select"){
                    // pass
                } else if (["cesuur", "nterm", "scalelength"].includes(field_name)){
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

// --- make el readonly when not requsr_role_admin
                    el.readOnly = !permit_ete_admin_crud_only;

                } else if (field_name === "secret_exam"){
                    if(permit_ete_admin_crud_only){
                        td.addEventListener("click", function() {UploadToggle(el)}, false)
                        add_hover(td);
                    };

                } else if (field_name === "status"){
                    if ( (permit_dict.permit_approve_exam) &&
                       ( (tblName === "ete_exam" && permit_ete_admin_crud_only) ||
                         (tblName === "duo_exam" && permit_ete_admin_crud_only) ||
                         (tblName === "grades" && permit_dict.requsr_same_school && data_dict.ce_exam_id) ) ){
                        td.addEventListener("click", function() {HandleToggleApprove(tblName, el)}, false)
                        add_hover(td);
                    };
                // --- add column with status icon
                    el.classList.add("stat_0_1")

                } else if (field_name === "download_exam"){
                    // td.class_align necessary to center align a-element
                    td.classList.add(class_align);

                } else if (field_name === "download_conv_table"){
            // +++  create href and put it in button PR2021-05-07
                    if (tblName === "ete_exam") {
                        // td.class_align necessary to center align a-element
                        td.classList.add(class_align);
                        add_hover(td);
                        el.innerHTML = "&emsp;&emsp;&emsp;&emsp;&#8681;&emsp;&emsp;&emsp;&emsp;";
                        // target="_blank opens file in new tab
                        el.target = "_blank";
                    } else if (tblName === "results" && data_dict.exam_id && data_dict.result_count) {
                        // td.class_align necessary to center align a-element
                        td.classList.add(class_align);
                        add_hover(td);
                        el.innerHTML = "&emsp;&emsp;&emsp;&emsp;&#8681;&emsp;&emsp;&emsp;&emsp;";
                        // target="_blank opens file in new tab
                        el.target = "_blank";
                    };
                } else if (field_name === "ceex_name"){
                    td.addEventListener("click", function() {MSELEX_Open(el)}, false);
                    add_hover(td);

                } else {
                    if (tblName === "ete_exam"){
                        if (permit_ete_admin_crud_only) {
                            td.addEventListener("click", function() {MEXQ_Open(el)}, false);
                            add_hover(td);
                        };
                    } else if (tblName === "grades"){
                        if(permit_dict.requsr_same_school){
                            td.addEventListener("click", function() {MEXA_Open(el)}, false);
                            add_hover(td);
                        };
                    };
                };
                //td.classList.add("pointer_show", "px-2");

    // --- add left border
                if(j){td.classList.add("border_left")};
    // --- add width, text_align
                el.classList.add(class_width, class_align);

                td.appendChild(el);

    // --- put value in field
                UpdateField(tblName, el, data_dict)
            }  // if (!columns_hidden[field_name])
        }  // for (let j = 0; j < 8; j++)

        return tblRow
    };  // CreateTblRow

//=========  UpdateTblRow  ================ PR2020-08-01
    function UpdateTblRow(tblRow, tblName, data_dict) {
        //console.log("=========  UpdateTblRow =========");
        //console.log("data_dict", data_dict);
        if (tblRow && tblRow.cells){
            for (let i = 0, td; td = tblRow.cells[i]; i++) {
                UpdateField(tblName, td.children[0], data_dict);
            }
        }
    };  // UpdateTblRow

//=========  UpdateField  ================ PR2020-12-18 PR2022-01-25  PR2022-04-21
    function UpdateField(tblName, el_div, data_dict) {
        //console.log("=========  UpdateField =========");
        if(el_div){
            const field_name = get_attr_from_el(el_div, "data-field");

            if(field_name){
                let inner_text = null, title_text = null, filter_value = null;
                if (field_name ==="select"){
                    // pass
                } else if (field_name ==="status"){
                    const [status_className, status_title_text, filter_val] = UpdateFieldStatus(tblName, data_dict);
                    filter_value = filter_val;
                    el_div.className = status_className;
                    title_text = status_title_text;

                } else if (field_name === "examperiod"){
                    inner_text = (data_dict.examperiod === 1) ? loc.Central_exam :
                                 (data_dict.examperiod === 2) ? loc.Re_examination :
                                 (data_dict.examperiod === 3) ? loc.Re_examination_3rd_period : "---";
                    el_div.innerText = inner_text;
                    filter_value = (inner_text) ? inner_text.toLowerCase() : null;

                } else if (field_name === "nterm"){
                    // show '0', therefore don't use ( data_dict.ce_exam_score) ?  data_dict.ce_exam_score : null
                    inner_text = (data_dict[field_name] != null) ? data_dict[field_name].replace(".", ",") : null;
                    el_div.value = inner_text;
                    filter_value = inner_text;

                } else if (["cesuur", "scalelength"].includes(field_name)){
                    // show '0', therefore don't use ( data_dict.ce_exam_score) ?  data_dict.ce_exam_score : null
                    inner_text = (data_dict[field_name] != null) ? data_dict[field_name] : null;
                    if (tblName === "duo_exam"){
                        el_div.value = inner_text;
                    } else {
                        el_div.innerHTML = (inner_text) ? inner_text : "&nbsp";
                    };
                    filter_value = inner_text;

                } else if (field_name === "ce_exam_score"){
                    const [inner_txt, title_txt] = UpdateFieldScore(loc, data_dict)
                    el_div.innerHTML = (inner_txt) ? inner_txt : "&nbsp";
                    title_text = title_txt;
                    filter_value = (inner_txt) ? inner_txt : null;

                } else if (field_name === "blanks"){
                    const [inner_txt, title_txt, filter_val] = UpdateFieldBlanks(tblName, data_dict);
                    el_div.innerHTML = (inner_txt) ? inner_txt : "&nbsp";
                    title_text = title_txt;
                    filter_value = filter_val;

                } else if (field_name === "result_avg"){
                    inner_text = f_format_percentage (loc.user_lang, data_dict[field_name], 0);
                    el_div.innerText = inner_text
                    filter_value = (inner_text) ? inner_text : null;

                } else if (field_name === "secret_exam"){
                    filter_value = (data_dict[field_name]) ? "1" : "0";
                    el_div.className = (data_dict[field_name]) ? "tickmark_1_2" : "tickmark_0_0";
                    el_div.setAttribute("data-value", filter_value);

                } else if (field_name === "download_exam"){
            // +++  create href and put it in button PR2021-05-07
                    UpdateFieldDownloadExam(tblName, el_div, data_dict)

                } else if (field_name === "download_conv_table"){
            // +++  create href and put it in button PR2021-05-07
                    if (tblName === "ete_exam") {
                        const href_str = data_dict.id.toString();
                        el_div.href = urls.url_exam_download_conversion_pdf.replace("-", href_str);
                    } else if (tblName === "results") {
                        if (data_dict.exam_id && data_dict.result_count) {
                            const href_str = data_dict.exam_id.toString();
                            el_div.href = urls.url_exam_download_conversion_pdf.replace("-", href_str);
                        };
                    };

                //} else if (field_name === "printjson"){
            // +++  create href and put it in button PR2021-05-07
                    //const href_str = data_dict.id.toString()
                    //let href = urls.url_exam_download_exam_json.replace("-", href_str);
                    //el_div.href = href;

                } else if (field_name === "filename"){
                    const name = (data_dict.name) ? data_dict.name : null;
                    const file_path = (data_dict.filepath) ? data_dict.filepath : null;
                    if (file_path){
                        // urls.url_download_published = "/grades/download//0/"
                        const len = urls.url_download_published.length;
                        const href = urls.url_download_published.slice(0, len - 2) + data_dict.id +"/"
                        //el_div.setAttribute("href", href);
                        //el_div.setAttribute("download", name);
                        el_div.title = loc.Download_Exform;
                        el_div.classList.add("btn", "btn-add")
                        add_hover(td);
                    };
                } else {
                    inner_text = (data_dict[field_name]) ? data_dict[field_name] : null;
                    el_div.innerHTML = (inner_text) ? inner_text : "&nbsp";
                    filter_value = (inner_text) ? inner_text.toString().toLowerCase() : null;
                    if (field_name === "exam_name"){
                        title_text = inner_text;
                    }
                }
                add_or_remove_attr (el_div, "title", !!title_text, title_text);
// ---  add attribute filter_value
                add_or_remove_attr (el_div, "data-filter", !!filter_value, filter_value);
            };
        }
    };  // UpdateField


//=========  UpdateFieldDownloadExam  ================ PR2022-05-17
    function UpdateFieldDownloadExam(tblName, el_div, data_dict) {

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



//=========  UpdateFieldScore  ================ PR2022-05-17
    function UpdateFieldScore(loc, data_dict) {

        const inner_text = (data_dict.secret_exam) ? loc.not_applicable :
               (data_dict.ce_exam_score != null) ? data_dict.ce_exam_score.toString() : null;

        const title_text = (data_dict.secret_exam) ?
                            [loc.This_is_a_secret_exam_01, loc.This_is_a_secret_exam_02,
                            loc.This_is_a_secret_exam_03, loc.This_is_a_secret_exam_04].join("\n")
                            : null;

        return [inner_text, title_text];
    };  // UpdateFieldScore

//=========  UpdateFieldBlanks  ================ PR2022-04-30
    function UpdateFieldBlanks(tblName, data_dict) {
        //console.log("=========  UpdateFieldBlanks =========");
        //console.log("tblName", tblName);
        //console.log("data_dict", data_dict);

        let inner_text = null, title_text = null, filter_value = null;
        const amount = (tblName === "ete_exam") ? (Number(data_dict.amount)) ? Number(data_dict.amount) : 0 :
                                                   (Number(data_dict.ceex_amount)) ? Number(data_dict.ceex_amount) : 0;
        const blanks = (tblName === "ete_exam") ? (Number(data_dict.blanks)) ? Number(data_dict.blanks) : 0 :
                                                   (Number(data_dict.ce_exam_blanks)) ? Number(data_dict.ce_exam_blanks) : 0;
        //console.log("amount", amount, typeof amount);
        //console.log("blanks", blanks, typeof blanks);

        if (tblName === "ete_exam") {
            // "NBSP (non-breaking space)" is necessary to show green box when field is empty
            if (!amount) {
                inner_text = "0 / 0";
                title_text = loc.This_exam_has_no_questions;
            } else if (!blanks) {
                title_text = loc.All_questions_are_entered;
            } else {
                inner_text = blanks + " / " + amount;
                if (blanks === amount) {
                    title_text = loc.No_questions_of + amount + loc.is_entered;
                } else  if (blanks === "1") {
                    title_text = loc.One_question_of + amount + loc.is_not_entered;
                } else {
                    title_text = blanks + loc.questions_of + amount + loc.are_not_entered;
                };
            };

        } else {
            // don't display text when there is no exam selected

            if(data_dict.ce_exam_id){
                // "NBSP (non-breaking space)" is necessary to show green box when field is empty
                if (data_dict.secret_exam){
                    // leave field blank when secret_exam
                } else if (!amount){
                    inner_text = "0 / 0";
                    title_text = loc.This_exam_has_no_questions;
                } else {
                    if (!data_dict.ce_exam_result ) {
                        inner_text = amount + " / " + amount;
                        title_text = loc.No_questions_of + amount + loc.is_entered;
                    } else if (!blanks ) {
                        title_text = loc.All_questions_are_entered;
                    } else if (blanks == amount){
                        inner_text = blanks + " / " + amount;
                        title_text = loc.No_questions_of + amount + loc.is_entered;
                    } else if (blanks === 1) {
                        inner_text = blanks + " / " + amount;
                        title_text = loc.One_question_of + amount + loc.is_not_entered;
                    } else {
                        inner_text = blanks + " / " + amount;
                        title_text = blanks + loc.questions_of + amount + loc.are_not_entered;
                    };
                };
            } else {
                title_text = loc.No_exam_linked_to_this_subject;
            };
        };
        filter_value = (inner_text) ? inner_text : null;

        return [inner_text, title_text, filter_value];
    };  // UpdateFieldBlanks

//=========  UpdateFieldStatus  ================ PR2022-01-25
    function UpdateFieldStatus(tblName, data_dict) {
        //console.log("=========  UpdateFieldStatus =========");
        //console.log("tblName", tblName);
        //console.log("data_dict", data_dict);
        let className = "diamond_3_4";  // diamond_0_0 is empty diamond img  // diamond_3_4 is blank img
        let title_text = null, filter_value = null;

        // skip when row has no exam
        const exam_exists = (tblName === "grades") ? (!!data_dict && !!data_dict.ce_exam_id) : (!!data_dict && !!data_dict.id);
        const no_data = (!exam_exists || tblName === "duo_exam") ? false :
                        (tblName === "ete_exam") ? !data_dict.partex :
                        (tblName === "grades") ? !data_dict.ceex_partex : false;
    //console.log("exam_exists", exam_exists);
    //console.log("no_data", no_data);

        if (exam_exists) {
            const prefix = (tblName === "grades") ? "ce_exam_" : "";

            const field_auth1by_id = prefix + "auth1by_id" // auth1by_id or ce_exam_auth1by_id
            const field_auth2by_id = prefix + "auth2by_id"
            const field_published_id = prefix + "published_id"
            const field_publ_modat = prefix + "publ_modat"

            const auth1by_id = (data_dict[field_auth1by_id]) ? data_dict[field_auth1by_id] : null;
            const auth2by_id = (data_dict[field_auth2by_id]) ? data_dict[field_auth2by_id] : null;
            const published_id = (data_dict[field_published_id]) ? data_dict[field_published_id] : null;
    //console.log("auth1by_id", auth1by_id);
    //console.log("auth2by_id", auth2by_id);
    //console.log("field_published_id", field_published_id);

            const class_str = (published_id) ? "diamond_0_4" :
                              (auth1by_id && auth2by_id) ? "diamond_3_3" :
                              (auth1by_id) ? "diamond_2_1" :
                              (auth2by_id) ? "diamond_1_2" : "diamond_0_0"; // diamond_0_0 is outlined diamond
            // filter_values are: '0'; is show all, 1: not approved, 2: auth1 approved, 3: auth2 approved, 4: auth1+2 approved, 5: submitted,   TODO '6': tobedeleted '7': locked

    //console.log("class_str", class_str);

            filter_value = (published_id) ? "5" :
                              (auth1by_id && auth2by_id) ? "4" :
                              (auth2by_id ) ? "3" :
                              (auth1by_id) ? "2" : "1";

    //console.log("filter_value", filter_value);

            className = class_str;

            const field_auth1by = prefix + "_auth1by" // subj_auth1by
            const field_auth2by = prefix + "_auth2by" // subj_auth2by
            const field_published = prefix + "_published" // subj_published

            if (published_id){
                const modified_dateJS = parse_dateJS_from_dateISO(data_dict[field_publ_modat]);
                const subm_publ_at_txt = (tblName === "ete_exam") ? loc.Published_at : loc.Submitted_at;
                title_text = subm_publ_at_txt + ":\n" + format_datetime_from_datetimeJS(loc, modified_dateJS)

            } else if(auth1by_id || auth2by_id){
                title_text = loc.Approved_by + ": "
                for (let i = 1; i < 3; i++) {
                    const auth_id = (i === 1) ?  auth1by_id : auth2by_id;
                    const prefix_auth = prefix + "auth" + i;
                    if(auth_id){
                        const function_str = (i === 1) ?  loc.Chairperson.toLowerCase() : loc.Secretary.toLowerCase();
                        const field_usr = prefix_auth + "_usr";
    //console.log("field_usr", field_usr);
                        const auth_usr = (data_dict[field_usr]) ?  data_dict[field_usr] : "-";
    //console.log("auth_usr", auth_usr);
                        title_text += "\n" + function_str + ": " + auth_usr;
                    };
                };
            };
            //const data_value = (auth_id) ? "1" : "0";
            //el_div.setAttribute("data-value", data_value);

        };  // if (exam_exists) {
    //console.log("title_text", title_text);
        return [className, title_text, filter_value]
    };  // UpdateFieldStatus


//###########################################################################
// +++++++++++++++++ UPLOAD CHANGES +++++++++++++++++++++++++++++++++++++++++

//========= UploadToggle  ============= PR2022-05-16
    function UploadToggle(el_input) {
        console.log( " ==== UploadToggle ====");
        console.log( "el_input", el_input);
        // only called in secret_exam
        if (permit_dict.permit_crud && permit_dict.requsr_role_admin && permit_dict.requsr_country_pk === 1){

            const tblRow = t_get_tablerow_selected(el_input);
            const exam_pk = get_attr_from_el_int(tblRow, "data-pk");
            const fldName = get_attr_from_el(el_input, "data-field");

            const data_dict = b_get_datadict_by_integer_from_datarows(ete_exam_rows, "id", exam_pk);
            const old_value = data_dict[fldName];
            const subject_pk = data_dict.subj_id;

            console.log( "tblRow", tblRow);
            console.log( "exam_pk", exam_pk);
            console.log( "fldName", fldName);
            console.log( "old_value", old_value);
            console.log( "subject_pk", subject_pk);

            const new_value = (!old_value);

            // ---  change icon, before uploading
            add_or_remove_class(el_input, "tickmark_1_2", new_value, "tickmark_0_0");

            // ---  upload changes
            const upload_dict = {
                table: "ete_exam",
                exam_pk: exam_pk,
                subject_pk: subject_pk
            };
            upload_dict[fldName] = new_value;
            UploadChanges(upload_dict, urls.url_exam_upload);
        };
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

                    if ("updated_ete_exam_rows" in response) {
                        RefreshDataRows("ete_exam", response.updated_ete_exam_rows, ete_exam_rows, true)  // true = update
                    };
                    if ("updated_duo_exam_rows" in response) {
                        RefreshDataRows("duo_exam", response.updated_duo_exam_rows, duo_exam_rows, true)  // true = update
                    };
                    if ("updated_grade_rows" in response) {
                        RefreshDataRows("grades", response.updated_grade_rows, grade_exam_rows, true)  // true = update
                    };
                    if ("messages" in response) {
                        b_show_mod_message_dictlist(response.messages);
                    };
                    if ("err_html" in response) {
                        b_show_mod_message_html(response.err_html)
                    };
                    if ("msg_dict" in response && !isEmpty(response.msg_dict)) {
                        //if (mod_dict.mode && ["submit_test", "approve"].indexOf(mod_dict.mode) > -1){
                            MASE_UpdateFromResponse (response.msg_dict);
                        //};
                    };
                    if ( "approve_msg_html" in response){
                        MASE_UpdateFromResponse(response)
                    };
                    if ("updated_published_rows" in response) {
                        RefreshDataRows("published", response.updated_published_rows, published_map);
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

//========= HandleToggleApprove  ============= PR2022-01-24 PR2022-04-29
    function HandleToggleApprove(tblName, el_input) {
        console.log( " ==== HandleToggleApprove ====");
        // called by field "status' in table "ete_exam", "duo_exam", "grades"

// ---  lookup exam_dict in ete_exam_rows or in grade_exam_rows
        const data_dict = get_datadict_from_table_element(tblName, el_input)

        if (!isEmpty(data_dict)){
    // b_get_auth_index_of_requsr returns index of auth user, returns 0 when user has none or multiple auth usergroups
            // gives err messages when multiple found.

            const auth_index = b_get_auth_index_pres_secr_of_requsr(loc, permit_dict)
            // values of auth_index are 0, 1, 2. Zero means req_usr is not charman and not secretary.
            // b_get_auth_index_pres_secr_of_requsr calls msgbox when error

            if (auth_index){
                const auth1by_field = (tblName === "grades") ? "ce_exam_auth1by_id" : "auth1by_id"
                const auth2by_field = (tblName === "grades") ? "ce_exam_auth2by_id" : "auth2by_id"
                const publ_field = (tblName === "grades") ? "ce_exam_published_id" : "published_id"

                const is_published = (!!data_dict[publ_field]);
                let auth1by_id = (data_dict[auth1by_field]) ? data_dict[auth1by_field] : null;
                let auth2by_id = (data_dict[auth2by_field]) ? data_dict[auth2by_field] : null;

                // format of ce_exam_result_str is:
                //    grade_dict.ce_exam_result = "1;35# ...
                //    ce_exam_result starts with blanks; total_amount #
                // parseInt() parses a string and returns an integer of the specified radix
                //    If parseInt encounters a character that is not a numeral in the specified radix (radix=10),
                //    it ignores it and all succeeding characters and returns the integer value parsed up to that point.

                const no_data = (tblName === "ete_exam") ? !data_dict.partex :
                                (tblName === "duo_exam") ? false :
                                (tblName === "grades") ? isEmpty(data_dict) :
                                !data_dict.ce_exam_result;

                const has_blanks = (no_data || tblName === "duo_exam") ? false :
                                   (tblName === "ete_exam") ? !!data_dict.blanks :
                                   (tblName === "grades") ? (!data_dict.ce_exam_result || parseInt(data_dict.ce_exam_result, 10)) :
                                   false;

    // ---  get value of auth_bool_at_index
                const old_is_approved = (auth_index === 1)  ? !!auth1by_id :
                                        (auth_index === 2)  ? !!auth2by_id : null;

            // format of ce_exam_result_str is:
            // grade_dict.ce_exam_result = "1;35#2|2;a|3;a|4;a|5;a|6;1|7;x|8;a|9;0#4|1;1|2;a|3;1|4;a|5;a|6;a|7;a|8;x|9;a|10;1#6|1;a|2;a|3;1|4;a|5;1|6;a|7;1|8;a|9;1|10;1#7|1;1|2;1|3;1#8|1;1#9|1;5#10|1;7"
            //  - ce_exam_result starts with blanks; total_amount #
            //  - Note: total score was stored in pescore, is moved to ce_exam_score PR2022-05-15
            //  - partal exams are separated with #
            //  - partex = "2;2;4|1;C;;|2;D;3;"
            //      first array between || contains partex info : # partex_pk ; blanks ; total_amount /
            //      others contain answers info: | q_number ; char ; score ; blank |

                if (is_published){
    // exit and give message when grade is published
                    const msg_txt = (tblName === "grades")  ? loc.err_list.This_exam_is_submitted : loc.err_list.This_exam_is_published;
                    const msg_html = msg_txt + "<br>" + loc.approve_err_list.You_cannot_change_approval;
                    b_show_mod_message_html(msg_html);
                } else if (no_data && !old_is_approved) {
    // exit and give message when exam has no_data - not when duo_exam
                // when exam already approved you must be able to remove approval, also when exam has no_data
                    const msg_html = loc.err_list.This_exam_has_no_data + "<br>" + loc.err_list.You_cannot_approve_the_exam;
                    b_show_mod_message_html(msg_html);
    // exit and give message when there are blank questions - not when duo_exam
                // when exam already approved you must be able to remove approval, also when there are blank answers
                } else if (has_blanks && !old_is_approved){
                    const msg_html = loc.err_list.This_exam_has_blank_questions + "<br>" + loc.err_list.You_cannot_approve_the_exam;
                    b_show_mod_message_html(msg_html);
                } else {
    // ---  toggle value of auth_bool_at_index
                    let new_is_approved = false;
                    if (auth_index === 1) {
                        auth1by_id = (!old_is_approved) ? permit_dict.requsr_pk : null;
                        new_is_approved = !!auth1by_id;
                    } else  if (auth_index === 2) {
                        auth2by_id = (!old_is_approved) ? permit_dict.requsr_pk : null;
                        new_is_approved = !!auth2by_id;
                    }
                console.log( "new_is_approved", new_is_approved);

    // give message when status_bool = true and exam already approved but this user in different function
                    let double_approved = false;
                    if (new_is_approved){
                        if (auth_index === 1){
                            double_approved = (auth2by_id === permit_dict.requsr_pk);
                        } else if (auth_index === 2){
                            double_approved = (auth1by_id === permit_dict.requsr_pk);
                        };
                    };
                    if (double_approved && false) {
                        const msg_html = loc.err_list.Approved_different_function + "<br>" + loc.err_list.You_cannot_approve_again;
                        b_show_mod_message_html(msg_html);
                    } else {

    // ---  change icon, before uploading
        console.log( "is_published", is_published);
        console.log( "auth1by_id", auth1by_id);
        console.log( "auth2by_id", auth2by_id);

                        const new_class_str = b_get_status_auth1_auth2_iconclass(is_published, false, auth1by_id, auth2by_id);

                        el_input.className = new_class_str;
                        console.log( "new_class_str)", new_class_str);

    // ---  upload changes
                        const url_str = (tblName === "grades") ? urls.url_grade_upload : urls.url_exam_upload;
                        // value of 'mode' determines if status is set to 'approved' or 'not
                        // instead of using value of new_is_approved,
                        const mode = "update"  // : "approve_reset"

                        if (tblName === "grades") {
                            const upload_dict = { table: tblName,
                               mode: mode,
                               grade_pk: data_dict.id,
                               exam_pk: data_dict.ce_exam_id,
                               examperiod: data_dict.examperiod,
                               student_pk: data_dict.student_id,
                               auth_index: auth_index,
                               auth_bool_at_index: new_is_approved,
                               return_grades_with_exam: true
                            };
                            UploadChanges(upload_dict, url_str);
                        } else {
                            const upload_dict = { table: tblName,
                                                   mode: mode,
                                                   examyear_pk: data_dict.ey_id,
                                                   depbase_pk: data_dict.depbase_id,
                                                   lvlbase_pk: data_dict.lvlbase_id,
                                                   exam_pk: data_dict.id,
                                                   subject_pk: data_dict.subj_id,
                                                   auth_index: auth_index,
                                                   auth_bool_at_index: new_is_approved,
                                                   };
                            UploadChanges(upload_dict, url_str);
                        };
                    }; //  if (double_approved))

                };  // if (is_published)

                mod_dict = {};

                if (tblName === "ete_exam"){
                    if(permit_dict.permit_approve_exam && permit_dict.requsr_same_school && data_dict.studsubj_id){
                        const map_id = tblRow.id
                        const data_dict = get_mapdict_from_datamap_by_id(grade_map, map_id);
                        console.log( "data_dict", data_dict);
                        if(!isEmpty(data_dict)){
                            const fldName = get_attr_from_el(el_input, "data-field");
                            if(fldName in data_dict ){
                                const examtype = fldName.substring(0,2);
                                const published_field = examtype + "_published"
                                let publ_pk = (data_dict[published_field]) ? data_dict[published_field] : null;
                            };  //   if(fldName in data_dict ){
                        };  //  if(!isEmpty(data_dict))
                    };
                };
            };  //  if (auth_index)
        };  // if (!isEmpty(data_dict))
    }  // HandleToggleApprove



//========= DownloadPublished  ============= PR2020-07-31  PR2021-01-14
    function DownloadPublished(el_input) {
        console.log( " ==== DownloadPublished ====");
        const tblRow = t_get_tablerow_selected(el_input);
        const pk_int = get_attr_from_el_int(tblRow, "data-pk");

        const data_dict = get_mapdict_from_datamap_by_id(published_map, tblRow.id);
        const filepath = data_dict.filepath
        const filename = data_dict.filename
        console.log( "filepath", filepath);
        console.log( "filename", filename);

       // window.open = '/ticket?orderId=' + pk_int;

        // UploadChanges(upload_dict, urls.url_download_published);
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
            var url = window.URL.createObjectURL(response);
            a.href = url;
            a.download = 'myfile.pdf';
            document.body.append(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        },


    /*
                success: function (data) {
                    //const a = document.createElement('a');
                    //const url = window.URL.createObjectURL(data);
                    console.log( "data");
                    console.log( data);
                    /*
                    a.href = url;
                    a.download = 'myfile.pdf';
                    document.body.append(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                    */
                    /*
                    var blob = new Blob(data, { type: 'application/pdf' });
                    var a = document.createElement('a');
                    a.href = window.URL.createObjectURL(blob);
                    a.download = filename;
                    a.click();
                    window.URL.revokeObjectURL(url);

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
                var url = window.URL.createObjectURL(data);
                a.href = url;
                a.download = 'myfile.pdf';
                document.body.append(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            }
        });
        */

     }; // DownloadPublished

//###########################################################################
// +++++++++++++++++ REFRESH DATA MAP +++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataRows  ================ PR2020-08-16 PR2020-09-30 PR2021-05-11 PR2022-01-23 PR2022-04-13
    function RefreshDataRows(tblName, update_rows, data_rows, is_update) {
        //console.log(" --- RefreshDataRows  ---");
        //console.log("tblName", tblName);
        //console.log("update_rows", update_rows);

        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length
        if (update_rows && update_rows.length ) {
            const field_setting = field_settings[tblName];

    // ---  get list of hidden columns
            // copy col_hidden from mod_MCOL_dict.cols_hidden
            const col_hidden = [];
            b_copy_array_noduplicates(mod_MCOL_dict.cols_hidden, col_hidden)

    // - hide level when not level_req
            if(!setting_dict.sel_dep_level_req){col_hidden.push("lvl_abbrev")};

            for (let i = 0, update_dict; update_dict = update_rows[i]; i++) {
                RefreshDatarowItem(tblName, field_setting, col_hidden, update_dict, data_rows);
            };
        } else if (!is_update) {
            // empty the data_rows when update_rows is empty PR2021-01-13 debug forgot to empty data_rows
            // PR2021-03-13 debug. Don't empty de data_rows when is update. Returns [] when no changes made
           data_rows = [];
        };
        if (tblName === "duo_exam" && el_MDUO_btn_save){
            MDUO_FillSelectTables();
            el_MDUO_btn_save.disabled = true;
        };
    };  //  RefreshDataRows

//=========  RefreshDatarowItem  ================ PR2020-08-16 PR2020-09-30 PR2022-01-23 PR2022-04-13 PR2022-05-17
    function RefreshDatarowItem(tblName, field_setting, col_hidden, update_dict, data_rows) {
        //console.log(" --- RefreshDatarowItem  ---");
        //console.log("tblName", tblName);
        //console.log("update_dict", update_dict);
        //console.log("data_rows", data_rows);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);

    // ---  get list of hidden columns
            // copy col_hidden from mod_MCOL_dict.cols_hidden
            const col_hidden = [];
            b_copy_array_noduplicates(mod_MCOL_dict.cols_hidden, col_hidden)

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

    // --- lookup index where new row must be inserted in data_rows
                // PR2021-06-21 not necessary, new row has always pk higher than existing. Add at end of rows

    // ---  add new item in data_rows at end
                data_rows.push(update_dict);

    // ---  create row in table., insert in alphabetical order
                const new_tblRow = CreateTblRow(tblName, field_setting, update_dict, col_hidden)

                if(new_tblRow){
    // --- add1 to item_count and show total in sidebar
                    selected.item_count += 1;

    // ---  show total in sidebar
                    t_set_sbr_itemcount_txt(loc, selected.item_count, loc.Exam, loc.Exams, setting_dict.user_lang);

    // ---  scrollIntoView,
                    new_tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' });

    // ---  make new row green for 2 seconds,
                    ShowOkElement(new_tblRow);
                };
            } else {

// +++ get existing data_dict from data_rows.
                const data_rows = (tblName === "ete_exam") ? ete_exam_rows :
                                  (tblName === "duo_exam") ? duo_exam_rows :
                                  (tblName === "grades") ? grade_exam_rows : [];
                const pk_int = (update_dict && update_dict.id) ? update_dict.id : null;
                const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);
                const data_dict = (!isEmpty(found_dict)) ? found_dict : null;
                const datarow_index = index;
    //console.log("data_dict", data_dict);

                if(!isEmpty(data_dict)){

// ++++ deleted ++++
                    if(is_deleted){
                        // delete row from data_rows. Splice returns array of deleted rows
                        const deleted_row_arr = data_rows.splice(datarow_index, 1)
                        const deleted_row_dict = deleted_row_arr[0];

            //--- delete tblRow
                        if(deleted_row_dict && deleted_row_dict.mapid){
                            const tblRow_tobe_deleted = document.getElementById(deleted_row_dict.mapid);
                            if (tblRow_tobe_deleted ){
                                tblRow_tobe_deleted.parentNode.removeChild(tblRow_tobe_deleted);
            // --- subtract 1 from item_count and show total in sidebar
                                selected.item_count -= 1;
        // ---  show total in sidebar
                                t_set_sbr_itemcount_txt(loc, selected.item_count, loc.Exam, loc.Exams, setting_dict.user_lang);
                            };
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

    // ---  add field to updated_columns list when field exists in field_names
                                    if (field_names && field_names.includes(key)) {
        // ---  add field to updated_columns list
                                        updated_columns.push(key);
                                    };
                                };
                            };
                        };

    //console.log("updated_columns", updated_columns);


/*
        // fields 'amount', 'assignment', 'partex' and 'ce_exam_result' are not in fieldlist. Check for changes and make whole row green when changed
                        const other_fieldnames = ["amount", "scalelength", "assignment", "partex", "ce_exam_result"]
        //console.log("other_fieldnames", other_fieldnames);
                        for (let i = 0, col_field, old_value, new_value; col_field = other_fieldnames[i]; i++) {

        //console.log("col_field", col_field);
                            if (col_field in data_dict && col_field in update_dict){
        //console.log("data_dict[col_field]", data_dict[col_field])
        //console.log("update_dict[col_field]", update_dict[col_field])
                                if (data_dict[col_field] !== update_dict[col_field] ) {
        // ---  update field in data_row
                                    data_dict[col_field] = update_dict[col_field];
                // ---  update field 'blanks'
                                    updated_columns.push("blanks");
    // ---  make new row green for 2 seconds,
                                    const tblRow = document.getElementById(update_dict.mapid);
                                    ShowOkElement(tblRow);
                                };
                            };
                        };
*/
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
                                    tblRow = CreateTblRow(tblName, field_setting, update_dict, col_hidden)
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

//========= HandleArrowEvent  ================== PR2020-12-20 PR2022-05-07
    function HandleArrowEvent(el, event){
        //console.log(" --- HandleArrowEvent ---")
        //console.log("event.key", event.key, "event.shiftKey", event.shiftKey)
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
// --- get the first and last index of input columns
            let max_colindex = null,  min_colindex = null;
            for (let i = 0, fldName, cell, td; td = tblRow.cells[i]; i++) {
                cell = td.children[0];
                fldName = get_attr_from_el(cell, "data-field")
                if ( ["cesuur"].includes(fldName) ) {
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

//========= HandleInputChange  ===============PR2020-08-16 PR2021-03-25 PR2021-09-20 PR2022-05-07
    function HandleInputChange(el_input){
        console.log(" --- HandleInputChange ---")
        // function is only called by field 'cesuur', table 'ete_exam
        const tblRow = t_get_tablerow_selected(el_input);
        const tblName = get_attr_from_el(tblRow, "data-table");
        const fldName = get_attr_from_el(el_input, "data-field");
        console.log("fldName", fldName)

// ---  get selected.data_dict
        const exam_pk = get_attr_from_el_int(tblRow, "data-pk");
        const data_rows = (tblName === "duo_exam") ? duo_exam_rows : ete_exam_rows;
        const data_dict = b_get_datadict_by_integer_from_datarows(data_rows, "id", exam_pk);

        console.log("data_dict", data_dict)
        const old_value = data_dict[fldName];

        const has_permit = (permit_dict.permit_crud && permit_dict.requsr_role_admin && permit_dict.requsr_country_pk === 1);
        if (!has_permit){
            b_show_mod_message_html(loc.grade_err_list.no_permission);
    // put back old value in el_input
            el_input.value = old_value;

        } else if (fldName === "cesuur" && !data_dict.published_id){
                const msg_html = [loc.err_list.Exam_is_not_published, loc.err_list.Must_publish_before_enter_cesuur].join("<br>")
                b_show_mod_message_html(msg_html);
        // put back old value  in el_input
                el_input.value = old_value;

        } else {
            const new_value = el_input.value;
            if(new_value !== old_value){
                // TODO FOR TESTING ONLY: turn validate off to test server validation
                const validate_on = true;
                let msg_html = null;
                let value_with_dots = null;
                if (validate_on){
                    // el_input.value is string, therefore '0' is truish
                    if (new_value){
                        //PR2015-12-27 debug: vervang komma door punt, anders wordt komma genegeerd
                        value_with_dots = new_value.replace(",", ".");
                        const value_number = Number(value_with_dots);
                        if (fldName === "cesuur"){
                            if(!value_number && value_number != 0){
                                msg_html = loc.err_list.cesuur_mustbe;
                            } else if (value_number < 0) {
                                msg_html = loc.err_list.cesuur_mustbe; // "Score moet een getal groter dan nul zijn."
                            } else if (value_number % 1 !== 0 ) {
                                // the remainder / modulus operator (%) returns the remainder after (integer) division.
                                msg_html = loc.err_list.cesuur_mustbe;
                            } else if (data_dict.scalelength && value_number > data_dict.scalelength) {
                                msg_html = loc.err_list.cesuur_mustbe;
                            };
                        } else if (fldName === "scalelength"){
                            if(!value_number && value_number != 0){
                                msg_html = loc.err_list.scalelength_mustbe;
                            } else if (value_number < 0) {
                                msg_html = loc.err_list.scalelength_mustbe; // "Score moet een getal groter dan nul zijn."
                            } else if (value_number % 1 !== 0 ) {
                                // the remainder / modulus operator (%) returns the remainder after (integer) division.
                                msg_html = loc.err_list.scalelength_mustbe;

                            };
                        } else if (fldName === "nterm"){
                            if(!value_number && value_number != 0){
                                msg_html = loc.err_list.nterm_mustbe;
                            } else if (value_number < 0) {
                                msg_html = loc.err_list.nterm_mustbe; // "Score moet een getal groter dan nul zijn."
                            } else if ((value_number * 10) % 1 !== 0 ) {
                                // the remainder / modulus operator (%) returns the remainder after (integer) division.
                                msg_html = loc.err_list.nterm_mustbe;
                            };
                        }
                    };
                }
                if (msg_html){
    // ---  show modal MESSAGE
                    mod_dict = {el_focus: el_input}
                    b_show_mod_message_html(msg_html, null, ModMessageClose);
// make field red when error and reset old value after 2 seconds
                    reset_element_with_errorclass(tblName, el_input, data_dict)

                } else {
                    if (fldName === "cesuur"){
                        mod_dict = {mode: "cesuur",
                                    exam_pk: data_dict.id,
                                    examyear_pk: data_dict.ey_id,
                                    subject_pk: data_dict.subj_id,
                                    exam_name: data_dict.exam_name,
                                    cesuur: new_value,
                                    old_value: old_value,
                                    el_input: el_input
                                    };
                        ModConfirm_Cesuur_Open(el_input)

                    } else if (["nterm", "scalelength"].includes(fldName)){
                        const upload_dict = {
                            table: "duo_exam",
                            mode: "update",
                            exam_pk: data_dict.id,
                            examyear_pk: data_dict.ey_id,
                            subject_pk: data_dict.subj_id
                        };
                        upload_dict[fldName] = value_with_dots
                        UploadChanges(upload_dict, urls.url_exam_upload);
                    };
                };
            };
        };  // if (!permit_dict.permit_crud)
    };  // HandleInputChange

//=========  reset_element_with_errorclass  ================ PR2022-05-07
    function reset_element_with_errorclass(tblName, el_input, update_dict) {
        // make field red when error and reset old value after 2 seconds
        const err_class = "border_bg_invalid";
        el_input.classList.add(err_class);
        setTimeout(function (){
            el_input.classList.remove(err_class);
            UpdateField(tblName, el_input, update_dict);
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
            Filter_TableRows(tblBody_datatable);
        }
    }; // function HandleFilterKeyup

//========= HandleFilterStatus  =============== PR2020-07-21 PR2020-09-14 PR2021-03-23

    function HandleFilterStatus(el_input) {
        //console.log( "===== HandleFilterStatus  ========= ");

    // - get col_index and filter_tag from  el_input
        const col_index = get_attr_from_el(el_input, "data-colindex")
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
        if(filter_tag === "toggle") {
            // default filter triple '0'; is show all, '1' is show tickmark, '2' is show without tickmark
// - toggle filter value
            new_value = (filter_value === "2") ? "0" : (filter_value === "1") ? "2" : "1";
// - get new icon_class
            icon_class =  (new_value === "2") ? "tickmark_2_1" : (new_value === "1") ? "tickmark_2_2" : "tickmark_0_0";
        }

    // - put new filter value in filter_dict
        filter_dict[col_index] = [filter_tag, new_value]
        console.log( "filter_dict", filter_dict);
        el_input.className = icon_class;
        Filter_TableRows(tblBody_datatable);

    };  // HandleFilterStatus

    function Filter_TableRows() {  // PR2019-06-09 PR2020-08-31
        //console.log( "===== Filter_TableRows=== ");
        //console.log( "filter_dict", filter_dict);
                //console.log( "filter_array", filter_array);
        // function filters by inactive and substring of fields
        //  - iterates through cells of tblRow
        //  - skips filter of new row (new row is always visible)
        //  - if filter_name is not null:
        //       - checks tblRow.cells[i].children[0], gets value, in case of select element: data-value
        //       - returns show_row = true when filter_name found in value
        //  - if col_inactive has value >= 0 and hide_inactive = true:
        //       - checks data-value of column 'inactive'.
        //       - hides row if inactive = true
        selected.item_count = 0;
        for (let i = 0, tblRow, show_row; tblRow = tblBody_datatable.rows[i]; i++) {
            tblRow = tblBody_datatable.rows[i];
            show_row = t_ShowTableRowExtended(filter_dict, tblRow);
            add_or_remove_class(tblRow, cls_hide, !show_row);
            if (show_row){ selected.item_count += 1};
        };

    // ---  show total in sidebar
        t_set_sbr_itemcount_txt(loc, selected.item_count, loc.Exam, loc.Exams, setting_dict.user_lang);

    }; // Filter_TableRows

//========= ShowTableRow  ==================================== PR2020-08-17
    function ShowTableRow(tblRow, tblName_settings) {
        // only called by Filter_TableRows
        console.log( "===== ShowTableRow  ========= ");
        console.log( "tblName_settings", tblName_settings);
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
    function ResetFilterRows() {  // PR2019-10-26 PR2020-06-20 PR2022-05-19
       //console.log( "===== ResetFilterRows  ========= ");

        setting_dict.sel_exam_pk = null;
        setting_dict.sel_duo_exam_pk = null;

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

///////////////////////////////////////
// +++++++++ MOD SELECT EXAM  ++++++++++++++++ PR2021-05-22 PR2022-01-19 PR2022-04-29
    function MSELEX_Open(el_input){
        console.log(" ===  MSELEX_Open  =====") ;
        console.log( "el_input", el_input);
        // only called in table "grades" when clicked on field "ceex_name"
        // cannot change exam when it is approved or published

        el_MSELEX_header.innerText = loc.Select_exam;

        mod_MSELEX_dict = {exam_pk: null};
        if(permit_dict.permit_crud){
            const tblRow = t_get_tablerow_selected(el_input)
            const pk_int = get_attr_from_el_int(tblRow, "data-pk");
        console.log("pk_int", pk_int);
            const [index, found_dict, compare] = b_recursive_integer_lookup(grade_exam_rows, "id", pk_int);
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


                    const hide_info_container = !row_count || !data_dict.ce_exam_id;
                    add_or_remove_class(el_MSELEX_info_container, cls_hide, hide_info_container);

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

//=========  MSELEX_FillSelectTable  ================ PR2020-08-21 PR2022-01-19
    function MSELEX_FillSelectTable() {
        console.log( "===== MSELEX_FillSelectTable ========= ");

        const tblBody_select = el_MSELEX_tblBody_select;
        tblBody_select.innerText = null;

        let row_count = 0, add_to_list = false;
// ---  loop through ete_exam_rows
        if(ete_exam_rows && ete_exam_rows.length){
            for (let i = 0, data_dict; data_dict = ete_exam_rows[i]; i++) {

    console.log( "data_dict: ", data_dict);
    console.log( "mod_MSELEX_dict.subj_pk", mod_MSELEX_dict.subj_pk, typeof mod_MSELEX_dict.subj_pk);
    console.log( "    data_dict.subj_id", data_dict.subj_id, typeof data_dict.subj_id);
    console.log( "    mod_MSELEX_dict.subj_pk", mod_MSELEX_dict.subj_pk, typeof mod_MSELEX_dict.subj_pk);

    console.log( "    data_dict.subjbase_id", data_dict.subjbase_id, typeof data_dict.subjbase_id);
    console.log( "    mod_MSELEX_dict.subjbase_pk", mod_MSELEX_dict.subjbase_pk, typeof mod_MSELEX_dict.subjbase_pk);

            // add only when eam has same subject as grade, and also the same depbase and lvlbase_id
            // PR2022-05-18 debug Mireille Peterson exam not showing
            // cause: sxm has different subj_pk, use subjbase_pk instead
                let show_row = false;
                if (mod_MSELEX_dict.subjbase_pk === data_dict.subjbase_id){
                    if(mod_MSELEX_dict.student_lvlbase_pk){
                        show_row = (mod_MSELEX_dict.student_lvlbase_pk === data_dict.lvlbase_id);
                    } else {
                        show_row = true;
                    };
                };
                if (show_row){
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
// +++++++++ MOD EXAM QUESTIONS ++++++++++++++++ PR2021-04-05 PR2021-05-22
    function MEXQ_Open(el_input){
        console.log(" ===  MEXQ_Open  =====") ;

// - reset mod_MEX_dict
        const is_addnew = (!el_input);
        const is_result_page = false;
        MEX_reset_mod_MEX_dict(is_addnew, is_result_page);
    console.log("mod_MEX_dict.is_permit_admin", mod_MEX_dict.is_permit_admin) ;

        // mod_MEX_dict.is_permit_admin gets value in MEX_reset_mod_MEX_dict
        // is_permit_admin = (permit_dict.requsr_role_admin && permit_dict.requsr_country_pk === 1 && permit_dict.permit_crud);
        if(mod_MEX_dict.is_permit_admin){
            // el_input is undefined when called by submenu btn 'Add new'

            let sel_subject_pk = null, ete_exam_dict = {};
            if (el_input){
                const tblRow = t_get_tablerow_selected(el_input);

// ---  lookup ete_exam_dict in ete_exam_rows
                const pk_int = get_attr_from_el_int(tblRow, "data-pk")
                const [index, found_dict, compare] = b_recursive_integer_lookup(ete_exam_rows, "id", pk_int);
                if (!isEmpty(found_dict)){
                    ete_exam_dict = found_dict;
                    if (ete_exam_dict.subj_id) { sel_subject_pk = ete_exam_dict.subj_id};
                };
            };
            const is_addnew = (isEmpty(ete_exam_dict));
    console.log("ete_exam_dict", ete_exam_dict) ;

// -- lookup selected.subject_pk in subject_rows and get sel_subject_dict
            MEX_get_subject(sel_subject_pk);
            MEX_get_ete_exam_dict_info(ete_exam_dict);

// update text in headertext2_subject
            MEX_set_headertext2_subject();

            MEX_FillDictPartex(ete_exam_dict);
            MEX_FillDictAssignment(ete_exam_dict);
            MEXQ_FillDictKeys(ete_exam_dict);

            MEXQ_FillTablePartex();

// ---  set text last modified
            //el_MEXQ_msg_modified.innerText = (!is_addnew) ? f_format_last_modified_txt(loc, ete_exam_dict.modifiedat, ete_exam_dict.modby_username) : null;
            el_MEXQ_msg_modified.innerText = f_format_last_modified_txt(loc, ete_exam_dict.modifiedat, ete_exam_dict.modby_username);

            // update text in select subject div ( not when entering answers)
            // set input subject readOnly when existing exam
            if (el_MEXQ_select_subject) {
                el_MEXQ_select_subject.innerText = (mod_MEX_dict.is_addnew && !mod_MEX_dict.subject_name) ? loc.Click_here_to_select_subject :
                                                (mod_MEX_dict.subject_name) ? mod_MEX_dict.subject_name : null;
                add_or_remove_attr (el_MEXQ_select_subject, "readOnly", (!mod_MEX_dict.is_addnew), true);
            };
    // --- set select table level disabled
            MEXQ_FillSelectTableLevel();
            if (el_MEXQ_select_level){
                el_MEXQ_select_level.disabled = (!mod_MEX_dict.is_addnew || !mod_MEX_dict.subject_name);
            };
    // ---  set el_MEXQ_input_version
            if (el_MEXQ_input_version){
                el_MEXQ_input_version.value = (mod_MEX_dict.version) ? mod_MEX_dict.version : null;
            };
    // ---  set examperiod_checkboxes
            MEX_set_examperiod_checkboxes();

    // ---  set el_MEXQ_has_partex_checkbox, show/hide partial exam container
            if (el_MEXQ_has_partex_checkbox){
                el_MEXQ_has_partex_checkbox.checked = (mod_MEX_dict.has_partex) ? mod_MEX_dict.has_partex : false;
            };
            if (el_MEXQ_partex1_container){
                add_or_remove_class(el_MEXQ_partex1_container, cls_hide, !mod_MEX_dict.has_partex);
            };
            // also hide list of partex in section question, answer, keys
            if (el_MEXQ_partex2_container){
                add_or_remove_class(el_MEXQ_partex2_container, cls_hide, !mod_MEX_dict.has_partex);
            };
    // ---  set el_MEXQ_input_amount
            if (el_MEXQ_input_amount){
                el_MEXQ_input_amount.value = (mod_MEX_dict.amount) ? mod_MEX_dict.amount : null;
            };
    // ---  set el_MEXQ_input_scalelength
            if (el_MEXQ_input_scalelength){
                el_MEXQ_input_scalelength.value = (mod_MEX_dict.scalelength) ? mod_MEX_dict.scalelength : null;
            };
    // ---  set header text
            MEX_set_headertext1_examperiod();
            el_MEXQ_header3_student.innerText = null //  header3_text

    // ---  set focus to input element
            const el_focus = (is_addnew && el_MEXQ_select_subject) ? el_MEXQ_select_subject : el_MEXQ_input_amount;
            set_focus_on_el_with_timeout(el_focus, 50);

    // ---  set buttons
            add_or_remove_class(el_MEX_btn_tab_container, cls_hide, mod_MEX_dict.is_permit_same_school);
            MEX_BtnTabClicked();
            MEX_SetPages();
            // only show btn_pge when there are multiple pages
            MEXQ_show_btnpage();
            MEX_BtnPageClicked();
            //el_MEX_btn_keys.classList.remove("tsa_btn_selected");

    // --- hide partex_input_elements
            MEXQ_ShowPartexInputEls(false);

    // ---  disable save button when not all required fields have value
            MEXQ_validate_and_disable();

    // ---  show modal
            $("#id_mod_exam_questions").modal({backdrop: true});
        } ; //  if(is_permit_admin)

    };  // MEXQ_Open

//========= MEX_set_examperiod_checkboxes  ============= PR2022-01-23 PR22-03-23 PR22-05-16
    function MEX_set_examperiod_checkboxes() {
    // ---  set el_MEXQ_input_examperiod, default = 1, values can be 1 (1st period) , 2 (2nd period)
        el_MEXQ_checkbox_ep01.checked = (mod_MEX_dict.examperiod === 1);
        el_MEXQ_checkbox_ep02.checked = (mod_MEX_dict.examperiod === 2);
        el_MEXQ_checkbox_ep03.checked = (mod_MEX_dict.examperiod === 3);
    }  // MEX_set_examperiod_checkboxes

//========= MEX_Save  ============= PR2021-05-24
    function MEX_Save() {
        if(mod_MEX_dict.is_permit_same_school){
            MEXA_Save();
        } else if (mod_MEX_dict.is_permit_admin){
            MEXQ_Save();
        }
    }  // MEX_Save

//========= MEXQ_Save  ============= PR2021-04-05 PR2022-01-22
    function MEXQ_Save() {
        console.log("===== MEXQ_Save ===== ");
        console.log( "mod_MEX_dict: ", mod_MEX_dict);
/*
    partex: "1;1;4;20;Praktijkexamen onderdeel A # 3;1;8;12;Minitoets 1 BLAUW onderdeel A # ...
    format of partex_str is:
        partex are divided by "#"
            each item of partex contains: partex_pk ; partex_examperiod ; partex_amount ; max_score ; partex_name #

    assignment: "1;4;20|1;;6;|2;;4;|3;;4;|4;;6; # 3;8;12|1;D;3;|2;C;2;|3;C;;|4;;1;|5;;1;|6;;1;|7;D;;|8;;2; # ...
    format of assignment_str is:
        partex are divided by "#"
            first item of partex contains partex info: partex_pk ; partex_amount ; max_score |
            other items =  | q_number ; max_char ; max_score ; min_score |

    keys: "1 # 3|1;ac|2;b|3;ab|7;d # ...
    format of keys_str is:
        partex are divided by "#"
            first item of partex contains partex_pk |
            other items =  | q_number ; keys |

*/

        if(mod_MEX_dict.is_permit_admin){
            const upload_dict = {
                table: "ete_exam",
                mode: ((mod_MEX_dict.is_addnew) ? "create" : "update"),
                examyear_pk: mod_MEX_dict.examyear_pk,
                depbase_pk: mod_MEX_dict.depbase_pk,
                lvlbase_pk: mod_MEX_dict.lvlbase_pk,
                examtype: mod_MEX_dict.examtype,
                exam_pk: mod_MEX_dict.exam_pk,
                subject_pk: mod_MEX_dict.subject_pk,
                subject_code: mod_MEX_dict.subject_code,

                examperiod: mod_MEX_dict.examperiod,
                version: mod_MEX_dict.version,
                has_partex: mod_MEX_dict.has_partex
                // amount and blanks will be added further on
            };

            let partex_str = "", assignment_str = "", keys_str = "";
            let total_amount = 0, non_blanks = 0;

    console.log( "mod_MEX_dict.partex_dict: ", mod_MEX_dict.partex_dict, typeof mod_MEX_dict.partex_dict);
            for (const data_dict of Object.values(mod_MEX_dict.partex_dict)) {
                const partex_pk = data_dict.pk;
                if (partex_pk) {
                    // calc max score
                    const partex_name = (data_dict.name) ? data_dict.name : "";
                    const partex_examperiod = (data_dict.examperiod) ? data_dict.examperiod : 1;
                    const partex_amount = (data_dict.amount) ? data_dict.amount : 0;
                    const max_score = MEXQ_calc_max_score(partex_pk);
                    partex_str += ["#", partex_pk, ";",
                                        partex_examperiod, ";",
                                        partex_amount, ";",
                                        max_score, ";",
                                        partex_name
                                   ].join("");
                    if (partex_amount){
                        total_amount += partex_amount;

// --- add partex to assignment_str
                        assignment_str += "#" + partex_pk + ";" + partex_amount + ";" + max_score;
                        keys_str += "#" + partex_pk;

                        const p_dict = mod_MEX_dict.partex_dict[partex_pk];
                        if (p_dict.a_dict){
                            for (let q_number = 1, dict; q_number <= partex_amount; q_number++) {
                                const value_dict = p_dict.a_dict[q_number];
                                if(value_dict){
                                    // value_dict:  {max_score: '', max_char: 'B', min_score: ''}
                                    const max_char = (value_dict.max_char) ? value_dict.max_char : "";
                                    const max_score = (value_dict.max_score) ? value_dict.max_score : "";
                                    const min_score = (value_dict.min_score) ? value_dict.min_score : "";
                                    if (max_char || max_score) {
                                        assignment_str += [
                                            "|", q_number,
                                            ";", max_char,
                                            ";", max_score,
                                             ";", min_score
                                             ].join("");
                                        non_blanks += 1;
                                    };
                                    if (value_dict.keys) {
                                        keys_str += [
                                            "|", q_number,
                                            ";", value_dict.keys
                                             ].join("");
                                    };
                        }}};
                    };
                };
            };
            // remove first # from string
            if(partex_str) {partex_str = partex_str.slice(1)};
            if(assignment_str) {assignment_str = assignment_str.slice(1)};
            if(keys_str) {keys_str = keys_str.slice(1)};

            upload_dict.partex = (partex_str) ? partex_str : null;
            upload_dict.assignment = (assignment_str) ? assignment_str : null;
            upload_dict.keys = (keys_str) ? keys_str : null;
            upload_dict.amount = (total_amount) ? total_amount : 0;
            upload_dict.blanks = (total_amount > non_blanks) ? (total_amount - non_blanks) : 0;

            upload_dict.scalelength = (mod_MEX_dict.scalelength) ? mod_MEX_dict.scalelength : null;

            UploadChanges(upload_dict, urls.url_exam_upload);
        };  // if(mod_MEX_dict.is_permit_admin)
// ---  hide modal
        $("#id_mod_exam_questions").modal("hide");
    }  // MEXQ_Save

//=========  MEX_get_subject  ================ PR2022-01-12
    function MEX_get_subject(sel_subject_pk) {
        //console.log("===== MEX_get_subject =====");
        //console.log("sel_subject_pk", sel_subject_pk);
        // called by MEXQ_Open and by MSSSS_Response after selecting subject

        setting_dict.sel_subject_pk = sel_subject_pk;
// reset selected student when subject is selected, in setting_dict
        if(sel_subject_pk){
            setting_dict.sel_student_pk = null;
            setting_dict.sel_student_name = null;
        }
// -- lookup selected.subject_pk in subject_rows and get sel_subject_dict
        const [index, found_dict, compare] = b_recursive_integer_lookup(subject_rows, "id", sel_subject_pk);

    //console.log("subject_rows", subject_rows);
    //console.log("found_dict", found_dict);

        //console.log("found_dict", found_dict);
        if (!isEmpty(found_dict)){
            mod_MEX_dict.subject_pk = found_dict.id;
            //mod_MEX_dict.subject_dict = found_dict;
            mod_MEX_dict.subject_name = (found_dict.name) ? found_dict.name : null;
            mod_MEX_dict.subject_code = (found_dict.code) ? found_dict.code : null;
        }
    }  // MEX_get_subject

// ------- event handlers
//=========  MEXQ_BtnPartexClick  ================ PR2022-01-12
    function MEXQ_BtnPartexClick(mode) {
        console.log("===== MEXQ_BtnPartexClick =====");
        console.log("mode", mode);
        console.log("mod_MEX_dict", mod_MEX_dict);
        // values of 'mode' are: "add", "delete", "update", "ok", "cancel"

        const header_txt = (mode === "add") ? loc.Add_partial_exam :
                           (mode === "delete") ? loc.Delete_partial_exam :
                           (mode === "update") ? loc.Edit_partial_exam : null;

        if (mode === "cancel"){
    // - hide partex_input_elements
            MEXQ_ShowPartexInputEls(false);

        } else if (mode === "add"){
        // new partex will be created in mode 'save'
            const new_partex_name = MEXQ_get_next_partexname();
            mod_MEX_dict.sel_partex_pk = "new";

            // - show partex_input_elements
            MEXQ_ShowPartexInputEls(true);
            el_MEXQ_input_partex_name.value = new_partex_name;

    // ---  set focus to input element
            set_focus_on_el_with_timeout(el_MEXQ_input_partex_name, 50);

        } else {
            const sel_partex_pk = (mod_MEX_dict.sel_partex_pk) ? mod_MEX_dict.sel_partex_pk : null;
            const sel_partex_dict = mod_MEX_dict.partex_dict[sel_partex_pk];
        console.log("sel_partex_pk", sel_partex_pk);
        console.log("sel_partex_dict", sel_partex_dict);

            if(!sel_partex_dict && sel_partex_pk !== "new"){
                // no partex selected - give msg - not when is_create
                b_show_mod_message_html("<div class='p-2'>" + loc.No_partex_selected + "</div>", header_txt);

            } else if (mode === "update"){

                el_MEXQ_input_partex_name.value = null;
                el_MEXQ_input_partex_amount.value = null;
                if(sel_partex_dict){
                    el_MEXQ_input_partex_name.value = sel_partex_dict.name;
                    el_MEXQ_input_partex_amount.value = sel_partex_dict.amount;
                };

        // - show partex_input_elements
                MEXQ_ShowPartexInputEls(true);

    // ---  set focus to input element
                set_focus_on_el_with_timeout(el_MEXQ_input_partex_name, 50);

            } else if (mode === "delete"){

        console.log("delete", mode);
                delete mod_MEX_dict.partex_dict[sel_partex_pk];
                mod_MEX_dict.sel_partex_pk = null;

 // recalc amount and max score
                MEXQ_calc_amount_maxscore();

        console.log("mod_MEX_dict.partex_dict", mod_MEX_dict.partex_dict);
        // - hide partex_input_elements
                MEXQ_ShowPartexInputEls(false);
                MEXQ_FillTablePartex();
                // MEXQ_FillPage(); is called by MEXQ_FillTablePartex

                MEX_SetPages();
                // only show btn_pge when there are multiple pages
                MEXQ_show_btnpage();

// +++++ SAVE
            } else if (mode === "save"){
                const new_partex_name = el_MEXQ_input_partex_name.value
                const new_partex_amount = (Number(el_MEXQ_input_partex_amount.value)) ? Number(el_MEXQ_input_partex_amount.value) : null;
                const new_examperiod = (el_MEXQ_checkbox_ep02.checked) ? 2 : 1;

        console.log("new_examperiod", new_examperiod);
                if (!new_partex_name){
                    const msh_html = "<div class='p-2'>" + loc.Partexname_cannot_be_blank + "</div>";
                    b_show_mod_message_html(msh_html);

                } else if (!new_partex_amount){
                    const msh_html = "<div class='p-2'>" + loc.err_list.amount_mustbe_between_1_and_100 + "</div>";
                    b_show_mod_message_html(msh_html);

                } else if (new_partex_name.includes(";") || new_partex_name.includes("#") || new_partex_name.includes("|") ) {
                    // semicolon and pipe are used in partex_str, therefore they are not allowed
                    const msh_html = "<div class='p-2'>" + loc.err_list.characters_not_allowed + "</div>";
                    b_show_mod_message_html(msh_html);
                } else {

    // --- add new partex

        // format of exam_dict.partex = [ partex_pk, examperiod, amount, max_score, partex_name]
        // format of partex_dict = { 1: {pk: 1, examperiod: 2, name: "Deelexamen 1", amount: 3, max_score: 0, a_dict: {}}}

                    // sel_partex_pk "new" will be replaced by new_partex_pk
                    if (mod_MEX_dict.sel_partex_pk === "new"){
                        const new_partex_pk = MEXQ_get_next_partex_pk();
                        const new_partex_dict = {
                            pk: new_partex_pk,
                            examperiod: new_examperiod,
                            name: new_partex_name,
                            amount: new_partex_amount,
                            max_score: 0,
                            a_dict: {}

                        };
                        mod_MEX_dict.partex_dict[new_partex_pk] = new_partex_dict;
                        mod_MEX_dict.sel_partex_pk = new_partex_pk;

                    } else {

                // remove_excessive_items_from_assignment_dict
                        MEXQ_remove_excessive_items_from_assignment_dict(mod_MEX_dict.sel_partex_pk, new_partex_amount);

                // - calculate sum of max_scores
                        const new_max_score = MEXQ_calc_max_score(mod_MEX_dict.sel_partex_pk);

                        sel_partex_dict.name = new_partex_name;
                        sel_partex_dict.examperiod = new_examperiod;
                        sel_partex_dict.amount = new_partex_amount;
                        sel_partex_dict.max = new_max_score;
                        sel_partex_dict.mode = "update";
                    };

 // recalc amount and max score
                    MEXQ_calc_amount_maxscore();

 // reset input elements
                    el_MEXQ_input_partex_name.value = null
                    el_MEXQ_input_partex_amount.value = null;

    // - hide partex_input_elements
                    MEXQ_ShowPartexInputEls(false);
                    MEXQ_FillTablePartex();
                    // MEXQ_FillPage(); is called by MEXQ_FillTablePartex

                    MEX_SetPages();
                    // only show btn_pge when there are multiple pages
                    MEXQ_show_btnpage();
                };
            };
        };
    };  // MEXQ_BtnPartexClick

//=========  MEXQ_remove_excessive_items_from_assignment_dict  ================ PR2022-01-16
    function MEXQ_remove_excessive_items_from_assignment_dict(partex_pk, partex_amount) {
        //console.log("===== MEXQ_remove_excessive_items_from_assignment_dict =====");
        //console.log("partex_amount", partex_amount);
        //console.log("mod_MEX_dict.partex_dict", mod_MEX_dict.partex_dict);

        const p_dict = mod_MEX_dict.partex_dict[partex_pk];
        const a_dict = p_dict.a_dict;

// - delete items with number higher than amount
        for (const key in a_dict) {
            if (a_dict.hasOwnProperty(key)) {
                const q_number = (Number(key)) ? Number(key) : null;
                if (q_number && q_number > partex_amount){
                    delete a_dict[key];
                };
            };
        };

    };  // MEXQ_remove_excessive_items_from_assignment_dict

//=========  MEXQ_BtnSelectSubjectClick  ================ PR2022-01-11
    function MEXQ_BtnSelectSubjectClick(el) {
        console.log("===== MEXQ_BtnSelectSubjectClick =====");

        if (mod_MEX_dict.is_addnew){
// - hide partex_input_elements
            MEXQ_ShowPartexInputEls(false);

            t_MSSSS_Open(loc, "subject", subject_rows, false, setting_dict, permit_dict, MSSSS_Response);
        };
    };  // MEXQ_BtnSelectSubjectClick

//=========  MEXQ_PartexSelect  ================ PR2022-01-07
    function MEXQ_PartexSelect(tblRow, is_selected) {
        console.log("===== MEXQ_PartexSelect =====");
        //console.log("tblRow", tblRow);
        const partex_pk = get_attr_from_el(tblRow, "data-pk");
        //console.log("partex_pk", partex_pk);
        // cluster_pk is number or 'new_1' when created
        mod_MEX_dict.sel_partex_pk = (!partex_pk) ? null :
                                      (Number(partex_pk)) ? Number(partex_pk) : partex_pk;

// ---  reset highlighted partex and highlight selected partex in both tables
        // el_MEXQ_tblBody_partex1 does not exist in MEXA, put that one last in list
        const tblBody_list = [];
        if (el_MEXQ_tblBody_partex2) { tblBody_list.push(el_MEXQ_tblBody_partex2) };
        if (el_MEXQ_tblBody_partex1) { tblBody_list.push(el_MEXQ_tblBody_partex1) };

        for (let j = 0, tblBody; tblBody = tblBody_list[j]; j++) {
            for (let i = 0, tblRow; tblRow = tblBody.rows[i]; i++) {
                const data_pk = get_attr_from_el_int(tblRow,"data-pk")
                const is_selected = (mod_MEX_dict.sel_partex_pk && data_pk === mod_MEX_dict.sel_partex_pk)
                add_or_remove_class(tblRow, "bg_selected_blue",is_selected )
            };
        };

// - hide partex_input_elements
        MEXQ_ShowPartexInputEls(false);
        MEX_SetPages();
        // only show btn_pge when there are multiple pages
        MEXQ_show_btnpage();
        MEX_BtnPageClicked();

        console.log( "MEXQ_PartexSelect >>>> MEXQ_FillPage ========= ");
        MEXQ_FillPage();

        //console.log("mod_MEX_dict", mod_MEX_dict);

    };  // MEXQ_PartexSelect

//=========  MEXA_PartexSelect  ================ PR2022-01-19
    function MEXA_PartexSelect(tblRow, is_selected) {
        //console.log("===== MEXA_PartexSelect =====");

        const partex_pk = get_attr_from_el_int(tblRow, "data-pk");
        const partex_dict = mod_MEX_dict.partex_dict[partex_pk];

// +++ make tblRow selected
        mod_MEX_dict.sel_partex_pk = (partex_pk) ? partex_pk : null;

// ---  highlight selected partex, deselect others
        const tblBody = el_MEXQ_tblBody_partex2;
        for (let i = 0, tblRow; tblRow = tblBody.rows[i]; i++) {
            const data_pk = get_attr_from_el_int(tblRow,"data-pk")
            const is_selected = (mod_MEX_dict.sel_partex_pk && data_pk === mod_MEX_dict.sel_partex_pk)
            add_or_remove_class(tblRow, "bg_selected_blue",is_selected )
        };

// - hide partex_input_elements
        MEX_SetPages();
        // only show btn_pge when there are multiple pages
        MEXQ_show_btnpage();
        MEX_BtnPageClicked();
        MEXQ_FillPage();

        //console.log("mod_MEX_dict", mod_MEX_dict);

// - hide partex_input_elements

    };  // MEXA_PartexSelect

//=========  MEX_BtnTabClicked  ================ PR2021-05-25 PR2022-01-13
    function MEX_BtnTabClicked(btn) {
        //console.log( "===== MEX_BtnTabClicked ========= ");
        //console.log( "mod_MEX_dict.partex_dict", mod_MEX_dict.partex_dict);

        if(btn){
            const data_btn = get_attr_from_el(btn,"data-btn");
            mod_MEX_dict.sel_tab = (data_btn) ? data_btn : "tab_start";
        }
    //console.log( "mod_MEX_dict.sel_tab", mod_MEX_dict.sel_tab);

// ---  highlight selected button
        if(el_MEX_btn_tab_container){
            b_highlight_BtnSelect(el_MEX_btn_tab_container, mod_MEX_dict.sel_tab)
        }
// ---  show only the elements that are used in this option
        let tab_show = (mod_MEX_dict.is_permit_same_school) ? "tab_answers" : mod_MEX_dict.sel_tab;

        mod_MEX_dict.is_keys_mode = (mod_MEX_dict.sel_tab === "tab_keys");

        b_show_hide_selected_elements_byClass("tab_show", tab_show, el_MEXQ_questions);

        MEXQ_show_btnpage();

        if (["tab_assign", "tab_answers", "tab_keys", "tab_minscore"].includes(tab_show)) {
           MEX_BtnPageClicked()
        };

    //console.log( "mod_MEX_dict.partex_dict", mod_MEX_dict.partex_dict);
    }  // MEX_BtnTabClicked

//=========  MEX_BtnPageClicked  ================ PR2021-04-04 PR2021-05-25 PR2022-01-13
    function MEX_BtnPageClicked(btn, pge_index) {
        //console.log( "===== MEX_BtnPageClicked ========= ");

        console.log( "btn", btn, typeof btn);
        if (btn){
            const data_btn = get_attr_from_el(btn,"data-btn");
            mod_MEX_dict.pge_index = (data_btn) ? Number(data_btn.slice(4)) : 1;
        } else {
            mod_MEX_dict.pge_index = pge_index;
        }
        if (!mod_MEX_dict.pge_index) {mod_MEX_dict.pge_index = 1};
        console.log("mod_MEX_dict.pge_index", mod_MEX_dict.pge_index)

// ---  highlight selected button
        b_highlight_BtnSelect(el_MEX_btn_pge_container, "pge_" + mod_MEX_dict.pge_index)

    //console.log( "mod_MEX_dict.partex_dict", mod_MEX_dict.partex_dict);
        MEXQ_FillPage()
    }  // MEX_BtnPageClicked

// ------- fill functions
//========= MEX_reset_mod_MEX_dict  ============= PR2022-01-21
    function MEX_reset_mod_MEX_dict(is_addnew, is_result_page) {
        //console.log("===== MEX_reset_mod_MEX_dict =====");

        const is_permit_admin = (permit_dict.requsr_role_admin && permit_dict.requsr_country_pk === 1 && permit_dict.permit_crud);
        const is_permit_same_school = (permit_dict.requsr_same_school && permit_dict.permit_crud);

        //console.log("permit_dict", permit_dict);
        //console.log("is_permit_admin", is_permit_admin);

        b_clear_dict(mod_MEX_dict);

        mod_MEX_dict.is_permit_admin = is_permit_admin;
        mod_MEX_dict.is_permit_same_school = is_permit_same_school;

        mod_MEX_dict.sel_tab = "tab_start";
        mod_MEX_dict.pge_index = 1;
        mod_MEX_dict.examyear_pk = setting_dict.sel_examyear_pk;
        mod_MEX_dict.depbase_pk = setting_dict.sel_depbase_pk;
        mod_MEX_dict.examperiod = setting_dict.sel_examperiod;
        mod_MEX_dict.examtype = null;

        mod_MEX_dict.examtype = (selected_btn === "btn_duo_exam") ? "duo" : "ete";

        mod_MEX_dict.version = null;
        mod_MEX_dict.amount  = 0;
        mod_MEX_dict.maxscore = 0;

        mod_MEX_dict.has_partex = false;
        mod_MEX_dict.show_partex_input_els = false;
        mod_MEX_dict.is_keys_mode = false;
        mod_MEX_dict.is_addnew = is_addnew;
        mod_MEX_dict.is_result_page = is_result_page;

        mod_MEX_dict.lvlbase_pk = (setting_dict.sel_lvlbase_pk) ? setting_dict.sel_lvlbase_pk : null;

        mod_MEX_dict.partex_dict = {};

    //console.log("mod_MEX_dict", mod_MEX_dict);
    };  // MEX_reset_mod_MEX_dict

//=========  MEX_FillDictPartex  ================ PR2022-01-21
    function MEX_FillDictPartex(exam_dict, grade_dict) {
        //console.log("===== MEX_FillDictPartex =====");
        //console.log("exam_dict", exam_dict);
        // called by MEXQ_Open and MEXA_Open
        // format of exam_dict.partex = [ partex_pk, examperiod, amount, max_score, partex_name]
        // format of partex_dict = { 1: {pk: 1, examperiod: 2, name: "Deelexamen 1", amount: 3, max_score: 0, a_dict: {}}}

        const is_addnew = (isEmpty(exam_dict));

        mod_MEX_dict.partex_dict = {};

        if (is_addnew){
            const partex_pk = 1
            mod_MEX_dict.partex_dict[partex_pk] = {
                pk: 1,
                examperiod: 1,
                name: "Deelexamen " + partex_pk,
                amount: 0,
                max_score: 0,
                a_dict: {},
                //r_dict: {} // results (answers) > results are added in a_dict
            };

        } else if (exam_dict && exam_dict.partex) {
            const e_arr = exam_dict.partex.split("#");
            // not in use any more:
            // const partex_taken_pk_list = [];

    // get list of exams taken from grade_dict
            if (mod_MEX_dict.is_permit_same_school){
                if (grade_dict && grade_dict.ce_exam_result){
                    const ce_exam_arr = grade_dict.ce_exam_result.split("#");
                    for (let i = 0, ce_exam_str; ce_exam_str = ce_exam_arr[i]; i++) {
                        const result_arr = ce_exam_str.split("|");
                        const result_praktex_pk = (result_arr && result_arr.length) ? Number(result_arr[0]) : null;
                        // not in use any more:
                        //if (result_praktex_pk){
                        //    partex_taken_pk_list.push(result_praktex_pk)
                        //};
                    };
                };
            };

    // loop through partial exams
            for (let i = 0, arr_str; arr_str = e_arr[i]; i++) {
                const arr = arr_str.split(";")
                // arr (5) ['1', '1', '12', '0', 'Deelexamen 1']

                // format of exam_dict.partex = [ partex_pk, examperiod, amount, max_score, partex_name]
                // format of partex_dict = { 1: {pk: 1, examperiod: 2, name: "Deelexamen 1", amount: 3, max_score: 0, a_dict: {}}}

                if(arr.length === 5){
                    const partex_pk = (Number(arr[0])) ? Number(arr[0]) : null;
                    // get examperiod, but check if it is allowed
                    let partex_examperiod = null;
                    if (mod_MEX_dict.examperiod === 12) {
                        partex_examperiod = (Number(arr[1])) ? Number(arr[1]) : 1;
                    } else if (mod_MEX_dict.examperiod === 2) {
                        partex_examperiod = 2;
                    } else {
                        partex_examperiod = 1;
                    };

                    const partex_amount = (Number(arr[2])) ? Number(arr[2]) : 0;
                    const partex_max_score = (Number(arr[3])) ? Number(arr[3]) : 0;
                    const partex_name = (arr[4]) ? arr[4] : null;
                    if (partex_pk){
                        mod_MEX_dict.partex_dict[partex_pk] = {
                            pk: partex_pk,
                            examperiod: partex_examperiod,
                            name: partex_name,
                            amount: partex_amount,
                            max_score: partex_max_score,
                            a_dict: {}, // assignments
                            // r_dict: {} // results (answers) > results are added in a_dict
                        };
                        // not in use any more:
                        // add partex_taken when partex_pk is in grade_dict.ce_exam_result
                        //if (mod_MEX_dict.is_permit_same_school){
                        //    mod_MEX_dict.partex_dict[partex_pk].partex_taken = (partex_taken_pk_list.includes(partex_pk)) ? 1 : 0;
                        //};
                    };
                };
            };
        };
        //console.log("mod_MEX_dict",  deepcopy_dict(mod_MEX_dict));
    };  // MEX_FillDictPartex

//========= MEX_FillDictAssignment  ============= PR2022-01-17
    function MEX_FillDictAssignment(exam_dict) {
        //console.log("=====  MEX_FillDictAssignment  =====");
        if(exam_dict && exam_dict.assignment){

            // exam_dict.assignment = "1;3;0|1;;;|2;;;|3;;4;#2;2;4|1;C;;|2;D;3;"
            // format of assignment_str is:
            //  - partal exams are separated with #
            //  - partex = "2;2;4|1;C;;|2;D;3;"
            //  first array between || contains partex info, others contain assignment info
            //  #  |partex_pk ; partex_amount ; max_score |
            //     | q_number ; max_char ; max_score ; min_score |

            // fortmat of keys: 1:ba | 2:cd  q_number:keys

       //console.log( "exam_dict.assignment", exam_dict.assignment);

// - get array of partial exams
            const p_arr = exam_dict.assignment.split("#");
            // p_arr = ['1;3;0|1;;;|2;;;|3;;4;', '2;2;4|1;C;;|2;D;3;']

// +++ loop through array of partial exams
            for (let j = 0, p_str; p_str = p_arr[j]; j++) {
                // p_str = "2;2;4|1;C;;|2;D;3;"

// - get array of questions
                const q_arr = p_str.split("|");
                // q_arr = ['2;2;4', '1;C;;', '2;D;3;']

// --- get partex_pk, - arr[0] contains [partex_pk, amount, max]
                const q_str = q_arr[0];
                const arr = q_str.split(";");
                // arr[0] = ['2;2;4']
                const partex_pk = (Number(arr[0])) ? Number(arr[0]) : null;
// --- get p_dict
                const p_dict = mod_MEX_dict.partex_dict[partex_pk];
                if (p_dict){
// +++ loop through array of question - arr[0] contains [partex_pk, amount, max]
                    for (let i = 1, arr, q_str; q_str = q_arr[i]; i++) {
                        // arr_str = "1;3;0"
                        const arr = q_str.split(";");
                        // arr = ['1', '3', '0']
                        if (partex_pk) {
                            // arr_str = "2;D;3;"
                            const q_number = (Number(arr[0])) ? Number(arr[0]) : null;
                            if (p_dict.a_dict && q_number){
                                const max_char = (arr[1]) ? arr[1] : "";
                                const max_score = (Number(arr[2])) ? Number(arr[2]) : 0;
                                const min_score = (Number(arr[3])) ? Number(arr[3]) : 0;
                                const keys = ""; // TODO keys
                                if (max_char || max_score || min_score || keys) {
                                    p_dict.a_dict[q_number] = {
                                        max_char: max_char,
                                        max_score: max_score,
                                        min_score: min_score,
                                        keys: keys,
                                        result: null
                                    };
                                };
                            };
                        };
                    };  // for (let j = 0, partex; partex = arr[j]; j++)
                };
            };
        };
       //console.log( "mod_MEX_dict", mod_MEX_dict);
    };  // MEX_FillDictAssignment

//========= MEXQ_FillDictKeys  ============= PR2022-01-18
    function MEXQ_FillDictKeys(exam_dict) {
        //console.log("=====  MEXQ_FillDictKeys  =====");

        if(exam_dict && exam_dict.keys){
// - get array of partial exams
            const k_partex_arr = exam_dict.keys.split("#");
            // k_partex_arr = ['1|7;ab|8;c']

        //console.log("k_partex_arr", k_partex_arr);

// +++ loop through array of partial exams
            for (let j = 0, p_str; p_str = k_partex_arr[j]; j++) {
                // p_str = "1|7;ab|8;c"

// - get array of questions
                const q_arr = p_str.split("|");
                // q_arr = ['1', '7;ab', '8;c']

// --- get partex_pk, this is the first item of  q_arr
                const partex_pk = (Number(q_arr[0])) ? Number(q_arr[0]) : null;

// --- get p_dict from mod_MEX_dict.partex_dict
                const p_dict = mod_MEX_dict.partex_dict[partex_pk];
                if (p_dict){

// +++ loop through array of question -  skip arr[0], it contains partex_pk
                    for (let i = 1, arr, q_str; q_str = q_arr[i]; i++) {
                        // q_str = "1;3;0"
                        const arr = q_str.split(";");
// --- get question number
                        const q_number = (Number(arr[0])) ? Number(arr[0]) : null;
                        const keys = (arr[1]) ? arr[1] : "";
                        // arr = ['7', 'ab']

                        if (q_number){
                            const q_dict = p_dict.a_dict[q_number];
                            if (q_dict) {
                                q_dict.keys = keys;
                            };
                        };
                    };  // for (let j = 0, partex; partex = arr[j]; j++)
                };
            };
        };
        //console.log( "mod_MEX_dict", mod_MEX_dict);
    };  // MEXQ_FillDictKeys

//========= MEXA_FillDictResults  ============= PR2022-01-21
    function MEXA_FillDictResults(grade_dict) {
        //console.log("=====  MEXA_FillDictResults  =====");
        //console.log("grade_dict", grade_dict);

        if(grade_dict && grade_dict.ce_exam_result){
            // format of ce_exam_result_str is:
            // grade_dict.ce_exam_result = "1;35#2|2;a|3;a|4;a|5;a|6;1|7;x|8;a|9;0#4|1;1|2;a|3;1|4;a|5;a|6;a|7;a|8;x|9;a|10;1#6|1;a|2;a|3;1|4;a|5;1|6;a|7;1|8;a|9;1|10;1#7|1;1|2;1|3;1#8|1;1#9|1;5#10|1;7"
            //  - ce_exam_result starts with blanks; total_amount #
            //  - Note: total score was stored in pescore, is moved to ce_exam_score PR2022-05-15
            //  - partal exams are separated with #
            //  - partex = "2;2;4|1;C;;|2;D;3;"
            //      first array between || contains partex info : # partex_pk ; blanks ; total_amount /
            //      others contain answers info: | q_number ; char ; score ; blank |


// - get array of partial exams
            const ce_partex_arr = grade_dict.ce_exam_result.split("#");
            // ce_partex_arr = [ "|1;4|2;x|3;4", "2|2;b|3;b|4;x|5;3" ]

            let total_amount = 0, nonblanks = 0;
// +++ loop through array of partial exams
            for (let j = 0, p_str; p_str = ce_partex_arr[j]; j++) {
                // p_str = "2|2;b|3;b|4;x|5;3"

// - get array of questions
                const q_arr = p_str.split("|");
                // q_arr = ["2", "2;b", "3;b", "4;x", "5;3"]

// --- get partex_pk, this is the first item of  q_arr
                const partex_pk = (Number(q_arr[0])) ? Number(q_arr[0]) : null;

// --- get p_dict from mod_MEX_dict.partex_dict
                const p_dict = mod_MEX_dict.partex_dict[partex_pk];
                if (p_dict){
    // add number of question of this partex to total_questions
                    total_amount += p_dict.amount;

// +++ loop through array of questions - start with 1, q_arr[0] contains partex_pk
                    for (let i = 1, q_str; q_str = q_arr[i]; i++) {
                        // q_str = "3;b"
                        const arr = q_str.split(";");
                        // arr = ['3', 'b']

// --- get question number
                        const q_number = (Number(arr[0])) ? Number(arr[0]) : null;
                        if (q_number){
                            const q_dict = p_dict.a_dict[q_number];
                            if (q_dict) {
                                q_dict.result = (arr[1]) ? arr[1] : null ;
                                if (arr[1]) {nonblanks += 1}
                            };
                        };
                    };  // for (let j = 0, partex; partex = arr[j]; j++)
                }; // if (p_dict)
            };  //  for (let j = 0, p_str; p_str = ce_partex_arr[j]; j++)
            mod_MEX_dict.total_amount = total_amount;
            mod_MEX_dict.blanks = total_amount = nonblanks;
       };
       //console.log( "mod_MEX_dict", mod_MEX_dict);
    };  // MEXA_FillDictResults

//=========  MEXQ_FillTablePartex  ================ PR2022-01-07
    function MEXQ_FillTablePartex() {
        //console.log("===== MEXQ_FillTablePartex =====");
        //console.log("mod_MEX_dict.partex_dict", mod_MEX_dict.partex_dict);

    // show only clusters of this subject - is filtered in MCL_FillClusterList

        // el_MEXQ_tblBody_partex1 does not exist in MEXA, put that one last in list
        const tblBody_list = [];
        if (el_MEXQ_tblBody_partex2) { tblBody_list.push(el_MEXQ_tblBody_partex2) };
        if (el_MEXQ_tblBody_partex1) { tblBody_list.push(el_MEXQ_tblBody_partex1) };

        for (let j = 0, tblBody; tblBody = tblBody_list[j]; j++) {
            tblBody.innerHTML = null;
        };

        let has_selected_pk = false;

// ---  loop through mod_MEX_dict.partex_dict

        // format of exam_dict.partex = [ partex_pk, examperiod, amount, max_score, partex_name]
        // format of partex_dict = { 1: {pk: 1, examperiod: 2, name: "Deelexamen 1", amount: 3, max_score: 0, a_dict: {}}}

        for (const p_dict of Object.values(mod_MEX_dict.partex_dict)) {
            const partex_name = p_dict.name; // cluster_name
            const partex_examperiod = (p_dict.examperiod === 1) ? "ce" : (p_dict.examperiod === 2) ? loc.reex_abbrev : "-";
            const amount_str = (p_dict.amount) ? p_dict.amount : 0;
            const partex_amount_txt = [amount_str, loc.Q_abbrev ].join(" ");

            const partex_max_score_txt = "max: " + ( (!!p_dict.max_score) ? p_dict.max_score : 0 );
    //console.log("partex_examperiod", partex_examperiod);

            for (let j = 0, tblBody; tblBody = tblBody_list[j]; j++) {
                const row_index = b_recursive_tblRow_lookup(tblBody, setting_dict.user_lang, p_dict.name);

// +++ insert tblRow into tblBody1
                const tblRow = tblBody.insertRow(row_index);
                tblRow.setAttribute("data-pk", p_dict.pk)
    // - add data-sortby attribute to tblRow, for ordering new rows
                tblRow.setAttribute("data-ob1", p_dict.name);
    // - add EventListener
                tblRow.addEventListener("click", function() {MEXQ_PartexSelect(tblRow)}, false );
    //- add hover to tableBody1 row
                add_hover(tblRow)
    // - insert td into tblRow1
                let td = tblRow.insertCell(-1);
                td.innerText = p_dict.name;
                td.classList.add("tw_280")

                td = tblRow.insertCell(-1);
                td.innerText = partex_examperiod;
                td.classList.add("tw_060");
                td.classList.add("ta_l");
    // - insert second td into tblRow, only in el_MEXQ_tblBody_partex1
                if (j){
                    td = tblRow.insertCell(-1);
                    td.innerText = partex_amount_txt;
                    td.classList.add("tw_060");
                    td.classList.add("ta_r");

                    td = tblRow.insertCell(-1);
                    td.innerText = partex_max_score_txt;
                    td.classList.add("tw_090");
                    td.classList.add("ta_r");
                };

    // ---  highlight selected partex
                if (mod_MEX_dict.sel_partex_pk && mod_MEX_dict.sel_partex_pk === p_dict.pk){
                    has_selected_pk = true;
                    tblRow.classList.add("bg_selected_blue");
                };
            };
        };
        if(!has_selected_pk && tblBody_list.length){
            for (let j = 0, tblBody; tblBody = tblBody_list[j]; j++) {
                const firstRow = tblBody.rows[0];
                if (firstRow){
                    has_selected_pk = true;
                    mod_MEX_dict.sel_partex_pk = get_attr_from_el_int(firstRow, "data-pk");
                    firstRow.classList.add("bg_selected_blue")
                };
            };
        };
        if (has_selected_pk){
            MEXQ_FillPage();
        };
    };  // MEXQ_FillTablePartex

//=========  MEXA_FillTablePartex  ================ PR2022-01-07 PR2022-03-23
    function MEXA_FillTablePartex() {
        //console.log("===== MEXA_FillTablePartex =====");
        //console.log("mod_MEX_dict.partex_dict", mod_MEX_dict.partex_dict);

        const tblBody = el_MEXQ_tblBody_partex2;
        tblBody.innerHTML = null;

        let has_selected_pk = false;
        let selected_tblRow = null;
// ---  loop through mod_MEX_dict.partex_dict
        for (const p_dict of Object.values(mod_MEX_dict.partex_dict)) {
            const partex_name = p_dict.name;
            const row_index = b_recursive_tblRow_lookup(tblBody, setting_dict.user_lang, p_dict.name);

// +++ insert tblRow into tblBody1
            const tblRow = tblBody.insertRow(row_index);
            tblRow.setAttribute("data-pk", p_dict.pk);

// - add data-sortby attribute to tblRow, for ordering new rows
            tblRow.setAttribute("data-ob1", p_dict.name);

// - add EventListener
            tblRow.addEventListener("click", function() {MEXA_PartexSelect(tblRow)}, false );
//- add hover to tableBody1 row
            add_hover(tblRow)
// - insert td into tblRow1
            let td = tblRow.insertCell(-1);
            td.innerText = p_dict.name;
            td.classList.add("tw_280")

    //console.log("mod_MEX_dict.sel_partex_pk", mod_MEX_dict.sel_partex_pk);
    //console.log("p_dict.pk", p_dict.pk);

// ---  highlight selected partex
            if (mod_MEX_dict.sel_partex_pk && mod_MEX_dict.sel_partex_pk === p_dict.pk){
                has_selected_pk = true;
                tblRow.classList.add("bg_selected_blue");
                selected_tblRow = tblRow
            };
        };

        if(!has_selected_pk && tblBody){
            const firstRow = tblBody.rows[0];
    //console.log("firstRow", firstRow);
            if (firstRow){
                has_selected_pk = true;
                mod_MEX_dict.sel_partex_pk = get_attr_from_el_int(firstRow, "data-pk");
                firstRow.classList.add("bg_selected_blue")
                selected_tblRow = firstRow
            };
        };
        //console.log("has_selected_pk", has_selected_pk);
        if (selected_tblRow){
            MEXA_PartexSelect(selected_tblRow, true)
        };

    };  // MEXA_FillTablePartex

//========= MEXQ_FillSelectTableLevel  ============= PR2021-05-07 PR202-01-15
    function MEXQ_FillSelectTableLevel() {
        //console.log("===== MEXQ_FillSelectTableLevel ===== ");
        //console.log("level_map", level_map);

        const level_container = document.getElementById("id_MEXQ_level_container");
        add_or_remove_class(level_container, cls_hide, !setting_dict.sel_dep_level_req);
        if (el_MEXQ_select_level){
            el_MEXQ_select_level.innerHTML = null;
            if (setting_dict.sel_dep_level_req && mod_MEX_dict.subject_pk){
                //el_MEXQ_select_level.value = null;
                t_FillSelectOptions(el_MEXQ_select_level, level_map, "base_id", "abbrev", false,
                    mod_MEX_dict.lvlbase_pk, null, loc.No_leerwegen_found, loc.Select_level)
            };
        };
    } // MEXQ_FillSelectTableLevel

//=========  MEX_SetPages  ================ PR2021-04-04 PR2021-05-23 PR2022-01-16
    function MEX_SetPages() {
        //console.log( "===== MEX_SetPages ========= ");
        //console.log( "mod_MEX_dict", mod_MEX_dict);

        const p_dict = mod_MEX_dict.partex_dict[mod_MEX_dict.sel_partex_pk];
        //console.log( "p_dict", p_dict);

        const partex_amount = (p_dict) ? p_dict.amount : 0;

        mod_MEX_dict.total_rows = Math.ceil((partex_amount) / 5);
        mod_MEX_dict.pages_visible = Math.ceil((partex_amount) / 50);
        mod_MEX_dict.max_rows_per_page = (partex_amount > 200) ? 10 :
                            (partex_amount > 160) ? 10 :
                            (partex_amount > 150) ? 8 :
                            (partex_amount > 120) ? 10 :
                            (partex_amount > 100) ? 8 :
                            (partex_amount > 80) ? 10 :
                            (partex_amount > 60) ? 8 :
                            (partex_amount > 50) ? 6 : 10;
        mod_MEX_dict.page_min_max = {}

        const btns = el_MEX_btn_pge_container.children;
        for (let j = 0, btn; btn = btns[j]; j++) {
            const el_data_btn = get_attr_from_el(btn, "data-btn");
            // note: pge_index is different from j
            const pge_index = (el_data_btn) ? Number(el_data_btn.slice(4)) : 0

            add_or_remove_class(btn, cls_hide, (pge_index > mod_MEX_dict.pages_visible));
            if (pge_index) {
                let blank_questions_found = false;
                let blank_answers_found = false;
                let max_value = pge_index * mod_MEX_dict.max_rows_per_page * 5;
                if (max_value > partex_amount) {max_value = partex_amount}
                const min_value = ((pge_index - 1) * mod_MEX_dict.max_rows_per_page * 5) + 1;
                btn.innerText  = min_value + "-" + max_value;
                // check for blank values, make pge btn orange when blank values found
                for (let q = min_value, btn; q <= max_value; q++) {
                    if (!blank_questions_found && p_dict && p_dict.a_dict && !p_dict.a_dict[q]) {
                        blank_questions_found = true;
                    };

                    if (!blank_answers_found && mod_MEX_dict.answers_dict && !mod_MEX_dict.answers_dict[q]) {
                        blank_answers_found = true;
                    };
                };
                const class_warning = (permit_dict.requsr_same_school) ? blank_answers_found :
                                      (permit_dict.requsr_role_admin) ? blank_questions_found : false;
                add_or_remove_class(btn, "color_orange", class_warning);
                if(pge_index <= mod_MEX_dict.pages_visible) {
                    mod_MEX_dict.page_min_max[pge_index] = {min: min_value, max: max_value}
                };
            };
        };
        //console.log( "mod_MEX_dict", mod_MEX_dict);
    }  // MEX_SetPages

//=========  MEXQ_FillPage  ================ PR2021-04-04 PR2022-01-21
    function MEXQ_FillPage() {
        //console.log( " ===== MEXQ_FillPage ========= ");
        //console.log( ".........mod_MEX_dict.sel_partex_pk", mod_MEX_dict.sel_partex_pk);
        //console.log( ".........mod_MEX_dict", mod_MEX_dict);
        // assignment = { partex_pk: { q_number: {max_char: 'D', max_score: 2, min_score: null, keys: "ba"] } } }

        const partex_pk = mod_MEX_dict.sel_partex_pk;
        const partex_dict = mod_MEX_dict.partex_dict;
        //console.log( ".........partex_dict", partex_dict);

// reset columns
        for (let col_index = 0; col_index < 5; col_index++) {
        //console.log( ".........id_MEXQ_col_ + col_index", "id_MEXQ_col_" + col_index);

            const el_col_container = document.getElementById("id_MEXQ_col_" + col_index)
        //console.log( ".........el_col_container", el_col_container);
            el_col_container.innerHTML = null;
        }

        //console.log( ".........partex_pk", partex_pk);
        if (partex_pk){
            const p_dict = partex_dict[partex_pk];
        //console.log( ".........p_dict", p_dict);
            if (p_dict){
                // p_dict = { pk: 2, name: "Deelexamen 2", amount: 3, max: 0, mode: "create" }
                const p_amount = p_dict.amount;

                const a_dict = p_dict.a_dict;
                //const r_dict = p_dict.r_dict; // results (answers) > results are added in a_dict

                if (a_dict){

                    let q_number = (mod_MEX_dict.pge_index - 1) * mod_MEX_dict.max_rows_per_page * 5;

                    let first_q_number_of_page = 0;
                    for (let col_index = 0; col_index < 5; col_index++) {
                        const el_col_container = document.getElementById("id_MEXQ_col_" + col_index)

                        el_col_container.innerHTML = null;
                        if (q_number < p_amount){
                            for (let row_index = 0; row_index < mod_MEX_dict.max_rows_per_page; row_index++) {
                                q_number += 1;
                                if (q_number <= p_amount){
                                    if(!first_q_number_of_page) {first_q_number_of_page = q_number};
                                    const q_dict = (a_dict[q_number]) ? a_dict[q_number] : {};

                                    const max_char = (q_dict && q_dict.max_char) ? q_dict.max_char : "";
                                    const max_score = (q_dict && q_dict.max_score) ? q_dict.max_score : "";
                                    const keys = (q_dict && q_dict.keys) ? q_dict.keys : "";
                                    const result = (q_dict && q_dict.result) ? q_dict.result : null;
                                    // min_score is not in use
                                        //const min_score = (q_dict && q_dict.min_score) ? q_dict.min_score : "";

                                    let display_value = null, is_read_only = false, is_invalid = false, footnote_multiple_choice = "";
                                    if(mod_MEX_dict.is_result_page){
                                        is_read_only = (!max_char && !max_score);
                                        if(max_char){footnote_multiple_choice = "*"};

                                        display_value = result;
                                        is_invalid = (!display_value && !is_read_only);
                                    } else {
                                        if(mod_MEX_dict.is_keys_mode){
                                            display_value = keys;

                                            is_read_only = (!max_char);
                                            is_invalid = (!display_value && !is_read_only);
                                        } else {
                                            display_value = max_char + max_score;
                                            is_invalid = (!display_value)
                                        }
                                    };

                                    const el_flex_container = document.createElement("div");
                                    el_flex_container.classList.add("flex_container", "flex_1");
                                        const el_flex_0 = document.createElement("div");
                                        el_flex_0.className = "flex_1";
                                            const el_label = document.createElement("label");
                                            el_label.className = "mex_label";
                                            el_label.innerText = q_number + footnote_multiple_choice + ":";
                                        el_flex_0.appendChild(el_label);
                                    el_flex_container.appendChild(el_flex_0);

                                    const el_flex_1 = document.createElement("div");
                                        el_flex_1.classList.add("flex_1", "mx-1");
                                            const el_input = document.createElement("input");
                                            el_input.id = "idMEXq_" + mod_MEX_dict.sel_partex_pk + "_" + q_number;
                                            mod_MEX_dict.sel_partex_pk
                                            el_input.value = display_value;
                    //console.log( ".=========..display_value", display_value);
                                            el_input.className = "form-control";
                                            if(is_invalid) { el_input.classList.add("border_invalid")}
                                            el_input.setAttribute("type", "text")
                                            el_input.setAttribute("autocomplete", "off");
                                            el_input.setAttribute("ondragstart", "return false;");
                                            el_input.setAttribute("ondrop", "return false;");
                    // --- add EventListener
                                            el_input.addEventListener("change", function(){MEXQ_InputChange(el_input)});
                                            el_input.addEventListener("keydown", function(event){MEXQ_InputKeyDown(el_input, event)});

                                            // set readOnly=true when mode = 'keys' and question is not multiple choice
                                            // also when is_locked
                                            if (is_read_only ||mod_MEX_dict.is_locked) {el_input.readOnly = true}
                                        el_flex_1.appendChild(el_input);
                                    el_flex_container.appendChild(el_flex_1);
                                    el_col_container.appendChild(el_flex_container);
                                }  // if (q_number <= p_amount){
                            }  //  for (let row_index = 0;
                        }  // if (q_number < p_amount){
                    }  // for (let col_index = 0; col_index < 5; col_index++) {

                    if(first_q_number_of_page){

                        const q_id = "idMEXq_" + mod_MEX_dict.sel_partex_pk + "_" + first_q_number_of_page;
                        const el_focus = document.getElementById(q_id);
                        if (el_focus) { set_focus_on_el_with_timeout(el_focus, 50)}
                    };
                };  // if (a_dict){
            };  //  if (p_dict){
        };  // if (mod_MEX_dict.sel_partex_pk)

        //console.log( "mod_MEX_dict.partex_dict", mod_MEX_dict.partex_dict);
    }; // MEXQ_FillPage

// ------- show hide validate functions
//=========  MEXQ_ShowPartexInputEls  ================ PR2022-01-12 PR2022-03-23
    function MEXQ_ShowPartexInputEls(show_input_els) {
        console.log("===== MEXQ_ShowPartexInputEls =====");
// ---  reset and hide input_partex_name and partex_amount
        if (!show_input_els){
            el_MEXQ_input_partex_name.value = null;
            el_MEXQ_input_partex_amount.value = null;
        }
        add_or_remove_class(el_MEXQ_btngroup_add_partex, cls_hide, show_input_els)
        add_or_remove_class(el_MEXQ_group_partex_name, cls_hide, !show_input_els)
    };  // MEXQ_ShowPartexInputEls

//=========  MEXQ_show_btnpage  ================ PR2022-01-13
    function MEXQ_show_btnpage() {
        //console.log( "===== MEXQ_show_btnpage  ========= ");
                // only show btn_pge when there are multiple pages
        const show_btn_pge = (["tab_assign", "tab_answers", "tab_keys", "tab_minscore"].includes(mod_MEX_dict.sel_tab)
                            && mod_MEX_dict.pages_visible > 1);
        //console.log( "show_btn_pge", show_btn_pge);
        add_or_remove_class(el_MEX_btn_pge_container, cls_hide, !show_btn_pge)
    };  // MEXQ_show_btnpage

//=========  MEXQ_validate_and_disable  ================  PR2021-05-21 PR2022-01-15
    function MEXQ_validate_and_disable() {
        console.log(" -----  MEXQ_validate_and_disable   ----")
        console.log("mod_MEX_dict", mod_MEX_dict)
        let disable_save_btn = false;

        const is_locked = mod_MEX_dict.is_locked;
        const no_subject = !mod_MEX_dict.subject_pk;
        // no_level is only true when vsbo and no level
        const no_level = (setting_dict.sel_dep_level_req && !mod_MEX_dict.lvlbase_pk);
        // when has_partex: show el_MEXQ_input_scalelength, otherwise: show amount
        const show_input_scalelength = (mod_MEX_dict.has_partex);

// ---  disable save_btn when is_locked or no subject
        if (is_locked || no_subject) {
            disable_save_btn = true;

// ---  disable save_btn when amount has no value, only when not has_partex
        // because of secret exams you can save exam without questions PR2022-05-16
        } else if (!mod_MEX_dict.amount && !mod_MEX_dict.has_partex) {
            //disable_save_btn = true;

// ---  disable save_btn when level has no value - only when level required
        } else if(no_level){
            disable_save_btn = true;

        } else {
// ---  check if there are multiple exams of this subject and this level
            let multiple_exams_found = false;
        // skip when there are no other exams yet
            if(ete_exam_rows && ete_exam_rows.length){
        // loop through exams
                for (let i = 0, data_dict; data_dict = ete_exam_rows[i]; i++) {
        // skip the current exam
                    if(data_dict.map_id !== mod_MEX_dict.map_id){
        // skip other levels - only when level required
                        if(!!columns_hidden.lvl_abbrev || data_dict.lvlbase_pk !== mod_MEX_dict.lvlbase_pk){
                            multiple_exams_found = true;
            }}}};
            if (multiple_exams_found){
// ---  disable save_btn when multiple exams are found and version has no value
                // TODO give message, it doesnt work yet
                disable_save_btn = !el_MEXQ_input_version.value;
            };
        };

// ---  disable level_select when no subject or when not add_new
        if (el_MEXQ_select_level){
            el_MEXQ_select_level.disabled = (is_locked || no_subject || !mod_MEX_dict.is_addnew);
        };
        if (el_MEXQ_input_version){
            el_MEXQ_input_version.disabled = (is_locked || no_subject || no_level);
        };
// ---  disable partex checkbox when no subject or no level
        if (el_MEXQ_input_version){
            el_MEXQ_input_version.disabled = (is_locked || no_subject || no_level);
        };
        if (el_MEXQ_input_amount){
            el_MEXQ_input_amount.disabled = (is_locked || no_subject || no_level);
        };
        if (el_MEXQ_input_scalelength){
            el_MEXQ_input_scalelength.disabled = (is_locked || no_subject || no_level);
        };
        const msg_txt = (mod_MEX_dict.has_partex) ? loc.Awp_calculates_amount : loc.err_list.amount_mustbe_between_1_and_100;
        add_or_remove_class(el_MEX_err_amount, "text-danger", false, "text-muted" );

console.log("???? el_MEX_err_amount", el_MEX_err_amount)
        //if (el_MEX_err_amount){
            el_MEX_err_amount.innerHTML = msg_txt;
        //};
        add_or_remove_attr(el_MEXQ_input_amount, "readOnly", mod_MEX_dict.has_partex, true);

// ---  disable save button on error
        if (el_MEXQ_btn_save){
            el_MEXQ_btn_save.disabled = disable_save_btn;
        };
// ---  disable tab buttons
        if (el_MEX_btn_tab_container){
            const btns = el_MEX_btn_tab_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                const data_btn = get_attr_from_el(btn, "data-btn");
                if (["tab_assign", "tab_minscore", "tab_keys"].includes(data_btn)){
                    //add_or_remove_attr(btn, "disabled", disable_save_btn);
                };
            };
        };
    };  // MEXQ_validate_and_disable

//--------- input functions
//========= MEXQ_InputKeyDown  ================== PR2021-04-07
    function MEXQ_InputKeyDown(el_input, event){
        //console.log(" --- MEXQ_InputKeyDown ---")
        //console.log("event.key", event.key, "event.shiftKey", event.shiftKey)
        // This is not necessary: (event.key === "Tab" && event.shiftKey === true)
        // Tab and shift-tab move cursor already to next / prev element
        if (["Enter", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].indexOf(event.key) > -1) {
// --- get move_vertical based on event.key and event.shiftKey
            let move_vertical = (["Enter", "Tab", "ArrowDown"].includes(event.key) ) ? 1 :
                                    (event.key === "ArrowUp") ? -1 : 0;
            let move_horizontal = (event.key === "ArrowLeft") ? -1 :
                                  (event.key === "ArrowRight") ? 1 : 0;

    //console.log("move_horizontal", move_horizontal)
        // el_input.id = idMEXq_2_15
            const q_arr = el_input.id.split("_")
            const q_number_str = q_arr[2];
            const q_number = (Number(q_number_str)) ? Number(q_number_str) : null;

            let pge_index = mod_MEX_dict.pge_index;
            const q_min = mod_MEX_dict.page_min_max[pge_index].min;
            const q_max = mod_MEX_dict.page_min_max[pge_index].max;

// --- set move up / down 1 row when min / max index is reached
            let new_q_number = q_number + move_vertical + move_horizontal * mod_MEX_dict.max_rows_per_page;
            if(new_q_number > q_max) {
                if (pge_index < mod_MEX_dict.pages_visible){
                    pge_index += 1;
                    MEX_BtnPageClicked(null, pge_index);
                }
            } else if(new_q_number < q_min) {
                if (pge_index > 1){
                    pge_index -= 1;
                    MEX_BtnPageClicked(null, pge_index);
                };
            }
// --- set focus to next / previous cell
            const next_id = "idMEXq_" + mod_MEX_dict.sel_partex_pk + "_" + new_q_number;
    //console.log("next_id", next_id)
            const next_el = document.getElementById(next_id)
            set_focus_on_el_with_timeout(next_el, 50);
        }
    }  // MEXQ_InputKeyDown

//=========  MEXQ_InputLevel  ================ PR2021-05-21
    function MEXQ_InputLevel(el_input) {
        //console.log( "===== MEXQ_InputLevel  ========= ");
        //console.log( "el_input.value", el_input.value, typeof el_input.value);

        mod_MEX_dict.lvlbase_pk = (Number(el_input.value)) ? Number(el_input.value) : null;
        mod_MEX_dict.lvl_abbrev = (el_input.options[el_input.selectedIndex]) ? el_input.options[el_input.selectedIndex].innerText : null;

// ---  disable buttons and input elements when not all required fields have value
        //console.log( "mod_MEX_dict.lvlbase_pk", mod_MEX_dict.lvlbase_pk, typeof mod_MEX_dict.lvlbase_pk);
        //console.log( "mod_MEX_dict.sel_level_abbrev", mod_MEX_dict.sel_level_abbrev, typeof mod_MEX_dict.sel_level_abbrev);
        //console.log( "el_input.options", el_input.options);

        MEXQ_validate_and_disable();
        MEX_set_headertext2_subject();
// ---  Set focus to el_MEXQ_input_version
        set_focus_on_el_with_timeout(el_MEXQ_input_version, 50);
    }; // MEXQ_InputLevel

//=========  MEXQ_InputVersion  ================ PR2021-05-21
    function MEXQ_InputVersion(el_input) {
       //console.log( "===== MEXQ_InputVersion  ========= ");
        mod_MEX_dict.version = el_input.value;
        //console.log( "mod_MEX_dict.version", mod_MEX_dict.version);
// ---  disable save button when not all required fields have value
        MEXQ_validate_and_disable();
// --- update text in header 2
        MEX_set_headertext2_subject();
// ---  Set focus to el_MEXQ_input_amount
        set_focus_on_el_with_timeout(el_MEXQ_input_amount, 50);
    }; // MEXQ_InputVersion

//=========  MEXQ_InputAmount  ================ PR2021-04-04 PR2021-04-15
    function MEXQ_InputAmount(el_input) {
        //console.log( "===== MEXQ_InputAmount  ========= ");
        const new_value = el_input.value;
        //console.log( "new_value", new_value, typeof new_value);

        let new_number = null, msg_err = "", has_error = false;
        if (!new_value){
            // if loc.Amount_cannot_be_blank is not defined msg_err -= false. Therefore has_error = true added.
            has_error = true;
            msg_err = loc.err_list.Amount_cannot_be_blank + "<br>";
        } else {
            new_number = Number(new_value);
            // the remainder / modulus operator (%) returns the remainder after (integer) division.
            if(!new_number || (new_number % 1) || (new_number < 1) || (new_number > 100) ) {
                has_error = true;
                msg_err = loc.err_list.Amount + " '" + new_value + "' " + loc.err_list.not_allowed + "<br>";
            }
        }
        add_or_remove_class(el_MEX_err_amount, "text-danger", has_error, "text-muted" )
        if (has_error) { msg_err += loc.err_list.amount_mustbe_between_1_and_100};
        el_MEX_err_amount.innerHTML = msg_err;

        if (has_error) {
            el_input.value = (mod_MEX_dict.amount) ? mod_MEX_dict.amount : null;
            set_focus_on_el_with_timeout(el_input, 50)
        } else {
            mod_MEX_dict.amount = new_number;
            // InputAmount is only in use when not has_partex
            if (!mod_MEX_dict.has_partex){
                // get partex_pk (there should only be one)
                let partex_pk = null;
                for (const p_dict of Object.values(mod_MEX_dict.partex_dict)) {
                    if(!partex_pk){
                        partex_pk = p_dict.pk;
                    };
                };
                if (partex_pk){
                    const p_dict = mod_MEX_dict.partex_dict[partex_pk];
                    if (p_dict){
                        if (p_dict.amount !== new_number){
                            p_dict.amount = new_number;
                            MEXQ_remove_excessive_items_from_assignment_dict(partex_pk, new_number);
                            MEX_SetPages();
                            // only show btn_pge when there are multiple pages
                            MEXQ_show_btnpage();
                            MEX_BtnPageClicked();
                        };
                    };
                };
            };
        };

// ---  disable save button when not all required fields have value
        MEXQ_validate_and_disable();
    }; // MEXQ_InputAmount

//=========  MEXQ_HasPartexCheckboxChange  ================ PR2022-01-22
    function MEXQ_HasPartexCheckboxChange(el_input) {
        console.log( "===== MEXQ_HasPartexCheckboxChange  ========= ");
        console.log( "mod_MEX_dict", mod_MEX_dict);

// count the number of partex, only when setting has_partex to false
        let count_partex = 0;
        if (!el_input.checked){
            for (const p_dict of Object.values(mod_MEX_dict.partex_dict)) {
                count_partex += 1;
            };
        };

        if (count_partex > 1) {
            el_input.checked = true;
            ModConfirm_PartexCheck_Open();
        } else {
            mod_MEX_dict.has_partex = el_input.checked;
            add_or_remove_class(el_MEXQ_partex1_container, cls_hide, !mod_MEX_dict.has_partex);
            // also hide list of partex in section question, aanswer, keys
            add_or_remove_class(el_MEXQ_partex2_container, cls_hide, !mod_MEX_dict.has_partex);

            MEXQ_FillTablePartex();
        };
        MEXQ_ShowPartexInputEls(false);
// ---  disable buttons and input elements when not all required fields have value
        MEXQ_validate_and_disable();

            const msg_txt = (mod_MEX_dict.has_partex) ? loc.Awp_calculates_amount : loc.err_list.amount_mustbe_between_1_and_100;
            add_or_remove_class(el_MEX_err_amount, "text-danger", false, "text-muted" )
            el_MEX_err_amount.innerHTML = msg_txt;
            add_or_remove_attr(el_MEXQ_input_amount, "readOnly", mod_MEX_dict.has_partex, true);

    }; // MEXQ_HasPartexCheckboxChange

//=========  MEXQ_ExamperiodCheckboxChange  ================ PR2022-01-14
    function MEXQ_ExamperiodCheckboxChange(examperiod, el_input) {
        console.log( "===== MEXQ_ExamperiodCheckboxChange  ========= ");
        console.log( "mod_MEX_dict", mod_MEX_dict);

        if (el_input.checked){
            mod_MEX_dict.examperiod = examperiod;
            if (examperiod === 1){
                el_MEXQ_checkbox_ep02.checked = false;
                el_MEXQ_checkbox_ep03.checked = false;
            } else if (examperiod === 2){
                el_MEXQ_checkbox_ep01.checked = false;
                el_MEXQ_checkbox_ep03.checked = false;
            } else if (examperiod === 3){
                el_MEXQ_checkbox_ep01.checked = false;
                el_MEXQ_checkbox_ep02.checked = false;
            }
        } else {
            // one checkbox must be ticked off
            if (examperiod === 1){
                el_MEXQ_checkbox_ep02.checked = true;
                el_MEXQ_checkbox_ep03.checked = false;
                mod_MEX_dict.examperiod = 2;
            } else if (examperiod === 2){
                el_MEXQ_checkbox_ep01.checked = true;
                el_MEXQ_checkbox_ep03.checked = false;
                mod_MEX_dict.examperiod = 1;
            } else if (examperiod === 3){
                el_MEXQ_checkbox_ep01.checked = true;
                el_MEXQ_checkbox_ep02.checked = false;
                mod_MEX_dict.examperiod = 1;
            };
        }

        MEX_set_headertext1_examperiod();
    };  // MEXQ_ExamperiodCheckboxChange

//========= MEXQ_InputChange  =============== PR2022-01-14
    function MEXQ_InputChange(el_input){
        //console.log(" --- MEXQ_InputChange ---")

        if (mod_MEX_dict.is_permit_same_school){
            MEXA_InputAnswer(el_input, event);
        } else if(mod_MEX_dict.is_permit_admin){
            MEXQ_InputQuestion(el_input);
        }
    };

//========= MEXQ_InputQuestion  ===============PR2020-08-16 PR2021-03-25 PR2022-01-14
    function MEXQ_InputQuestion(el_input){
        console.log("--- MEXQ_InputQuestion ---")
        //console.log("el_input.id: ", el_input.id)
        // el_input.id = el_input.id:  idMEXq_1_1
        //const q_number_str = (el_input.id) ? el_input.id[10] : null;
        const el_id_arr = el_input.id.split("_")
        const partex_pk = (el_id_arr && el_id_arr[1]) ? Number(el_id_arr[1]) : null;
        const q_number = (el_id_arr && el_id_arr[2]) ? Number(el_id_arr[2]) : null;

        if (partex_pk && q_number){
            // open-question input has a number (8)
            // multiplechoice-question has one letter, may be followed by a number as score (D3)
            let new_max_char = "", new_max_score_str = "", new_max_score = "", msg_err = "";
            const input_value = el_input.value;

            // lookup assignment, create if it does not exist
            const p_dict = mod_MEX_dict.partex_dict[partex_pk];
            if (!(q_number in p_dict.a_dict)){
                p_dict.a_dict[q_number] = {};
            };
            const q_dict = p_dict.a_dict[q_number];

// - split input_value in first charactes and the rest
            const first_char = input_value.charAt(0);
            const remainder = input_value.slice(1);

// check if first character is a letter or a number => is multiple choice when a letter
            // !!Number(0) = false, therefore "0" must be filtered out with Number(first_char) !== 0
            const is_multiple_choice = (!Number(first_char) && Number(first_char) !== 0 );

            if(is_multiple_choice){
                new_max_char = (first_char) ? first_char.toUpperCase() : "";
                const remainder_int = (Number(remainder)) ? Number(remainder) : 0;
                new_max_score_str = (remainder_int > 1) ? remainder : "";
            } else {
                new_max_score_str = input_value;
            };

// +++++ when input is question:
            if (!mod_MEX_dict.is_keys_mode){
                if (new_max_char){
                    // Letter 'A' not allowed, only 1 choice doesn't make sense,
                    // also X,Y,Z not allowed because 'x' value is used for blank
                    if(!"BCDEFGHIJKLMNOPQRSTUVW".includes(new_max_char)){
                        msg_err = loc.err_list.Character + " '" + first_char  + "'" + loc.err_list.not_allowed +
                            "<br>" + loc.err_list.character_mustbe_between;
                    };
                };
// - validate max_score
                if (new_max_score_str){
                    new_max_score = Number(new_max_score_str);
                    // the remainder / modulus operator (%) returns the remainder after (integer) division.
                    if (!new_max_score || new_max_score % 1 !== 0 || new_max_score < 1 || new_max_score > 99) {
                        if (msg_err) {msg_err += "<br><br>"}
                        msg_err += loc.Maximum_score + " '" + new_max_score_str  + "'" + loc.err_list.not_allowed +
                                            "<br>" + loc.err_list.maxscore_mustbe_between;
                    };
                };

// - show message when error, restore input in element
                if (msg_err) {
                    const old_max_char = (q_dict.max_char) ? q_dict.max_char : "";
                    const old_max_score = (q_dict.max_char) ?
                // '1' is default max_score when max_char, don't show a_dict
                            (q_dict.max_score > 1) ? q_dict.max_score : "" :
                            (q_dict.max_score) ? q_dict.max_score : "";
                    const old_value = old_max_char + old_max_score;
                    el_input.value = (old_value) ? old_value : null;

                    el_mod_message_container.innerHTML = msg_err;
                    $("#id_mod_message").modal({backdrop: false});
                    set_focus_on_el_with_timeout(el_mod_message_btn_cancel, 150 )
                } else {

// - put new value in element
                    const new_value = new_max_char + ( (new_max_score) ? new_max_score : "" );

                    el_input.value = new_value;
                    add_or_remove_class(el_input, "border_invalid", !el_input.value)

// - put new value in mod_MEX_dict.p_dict.a_dict.q_dict
                    q_dict.max_char = (new_max_char) ? new_max_char : "";
                    q_dict.max_score = (new_max_score) ? new_max_score : 0;
                }

                MEXQ_calc_max_score(partex_pk);

// +++++ when input is keys:
    // admin mode - keys - possible answers entered by requsr_role_admin
            } else {

    //console.log("q_dict: ", q_dict)

                const max_char_lc = (q_dict.max_char) ? q_dict.max_char.toLowerCase() : "";

    //console.log("max_char_lc", max_char_lc)
    //console.log("is_multiple_choice", is_multiple_choice)
    //console.log("mod_MEX_dict.partex_dict", mod_MEX_dict.partex_dict)

// answer only has value when multiple choice question. one or more letters, may be followed by a number as minimum score (ca3)
                if (!q_dict.max_char){
                    el_mod_message_container.innerHTML = loc.err_list.This_isnota_multiplechoice_question;
                    $("#id_mod_message").modal({backdrop: false});
                    set_focus_on_el_with_timeout(el_mod_message_btn_cancel, 150 )
                } else {

                    if (input_value){
                        let new_keys = "", min_score = null, pos = -1;
                        for (let i = 0, len=input_value.length; i < len; i++) {
                            const char = input_value[i];
                            // !!Number(0) = false, therefore "0" must be filtered out with Number(first_char) !== 0
                            const is_char = (!Number(char) && Number(char) !== 0 )
                            if(!is_char){
                                msg_err += loc.Key + " '" + char  + "'" + loc.err_list.not_allowed + "<br>";
                            } else {
                                const char_lc = char.toLowerCase();
    //console.log("char_lc", char_lc)
    //console.log("max_char_lc", max_char_lc)
                                // y, z are not allowed because 'x' value is used for blank
                                if(!"abcdefghijklmnopqrstuvwx".includes(char_lc)){
                                    msg_err += loc.Key + " '" + char  + "'" + loc.err_list.not_allowed + "<br>";
                                } else if ( new_keys.includes(char_lc)) {
                                    msg_err += loc.Key + " '" + char  + "' " + loc.err_list.exists_multiple_times + "<br>";
                                } else if (char_lc > max_char_lc ) {
                                    msg_err += loc.Key + " '" + char  + "'" + loc.err_list.not_allowed + "<br>";
                                } else {
                                    new_keys += char_lc;
                                }
                            }
                        }  // for (let i = 0, len=input_value.length; i < len; i++) {
// - show message when error, delete input in element and in mod_MEX_dict.keys_dict
                        if (msg_err){
                            msg_err += loc.err_list.key_mustbe_between_and_ + max_char_lc + "'.";
                            el_input.value = null;
                            q_dict.keys = ";"

                            el_mod_message_container.innerHTML = msg_err;
                            $("#id_mod_message").modal({backdrop: false});
                            set_focus_on_el_with_timeout(el_mod_message_btn_cancel, 150 )

                        } else {
// - put new new_keys in element and in mod_MEX_dict.keys_dict
                            el_input.value = (new_keys) ? new_keys : null;
                            q_dict.keys = (new_keys) ? new_keys : "";
                        }
// - delete if input_value is empty
                    } else {
                        q_dict.keys = "";
                    };
                };  // if (!is_multiple_choice)
            };
            MEXQ_calc_amount_maxscore()
        } ; //  if (q_number)
    };  // MEXQ_InputQuestion


//--------- calc functions
//========= MEX_get_ete_exam_dict_info  ============= PR2021-05-23 PR2022-01-21
    function MEX_get_ete_exam_dict_info(exam_dict) {
        //console.log("===== MEX_get_ete_exam_dict_info =====");
        //console.log("exam_dict", exam_dict);
        //console.log("grade_dict", grade_dict);

        if(exam_dict) {
            mod_MEX_dict.exam_pk = exam_dict.id;
            mod_MEX_dict.version = (exam_dict.version) ? exam_dict.version : null;
            // examperiod: 1 = ce, 2 = reex, 12 = ce + reex
            mod_MEX_dict.examperiod = (exam_dict.examperiod) ? exam_dict.examperiod : 1;
            // examtype previously contained 'ce', filter out other values than 'ete' and 'duo'
            mod_MEX_dict.examtype = (exam_dict.examtype && ["ete", "duo"].includes(exam_dict.examtype)) ? exam_dict.examtype : null;

            mod_MEX_dict.has_partex = (exam_dict.has_partex) ? exam_dict.has_partex : false;

            mod_MEX_dict.amount = (exam_dict.amount) ? exam_dict.amount : 0;
            mod_MEX_dict.scalelength = (exam_dict.scalelength) ? exam_dict.scalelength : null;

            // not necessary ??
                // mod_MEX_dict.department_pk = exam_dict.department_id;

            mod_MEX_dict.lvlbase_pk = exam_dict.lvlbase_id;
            mod_MEX_dict.lvl_abbrev = exam_dict.lvl_abbrev;

            mod_MEX_dict.is_locked = (permit_dict.requsr_role_admin) ?
            // when admin: lock exam when approved or published or locked
                    ( exam_dict.locked || !!exam_dict.auth1by_id || !!exam_dict.auth2by_id || !!exam_dict.published_id ) :
                (permit_dict.requsr_same_school) ?
            // when admin: lock exam when NOT published or locked
                    ( exam_dict.locked || !exam_dict.published_id ) :
            // lock otherwise
                    true;
       };
       console.log( "mod_MEX_dict", mod_MEX_dict);
       console.log( "permit_dict.requsr_role_admin", permit_dict.requsr_role_admin);
       console.log( "mod_MEX_dict.is_locked", mod_MEX_dict.is_locked);
    };  // MEX_get_ete_exam_dict_info

//========= MEX_get_result_dict  ============= PR2021-05-23 PR2022-01-14
    function MEX_get_result_dict(grade_dict) {
        console.log("===== MEX_get_result_dict =====");
        //console.log("grade_dict", grade_dict);

        if(permit_dict.requsr_same_school && grade_dict){
            if (grade_dict.ce_exam_result){
            // fortmat of keys: "1:3 | 2:c"  q_number: answer
                const arr = grade_dict.ce_exam_result.split("|");
                // arr: ["1:3", "2:c"]
                for (let i = 0, q, q_arr; q = arr[i]; i++) {
                    q_arr = q.split(":");
                    // q_arr = ["1", "3"]
                    const q_number = q_arr[0];
                    const q_answer = (q_arr[1]) ? q_arr[1] : "";
                    // don't use value, because it needs reference in inputkeyup, not value
                    mod_MEX_dict.answers_dict[q_number] = {answer: q_answer};
                };
            };
        };

       //console.log( "mod_MEX_dict", mod_MEX_dict);
    }  // MEX_get_result_dict


//=========  MEXQ_remove_partex  ================ PR2022-01-14
    function MEXQ_remove_partex() {
        //console.log( "===== MEXQ_remove_partex ========= ");
        el_MEXQ_has_partex_checkbox.checked = false;
        mod_MEX_dict.has_partex = false;

        add_or_remove_class(el_MEXQ_partex1_container, cls_hide, !mod_MEX_dict.has_partex);
        // also hide list of partex in section question, aanswer, keys
        add_or_remove_class(el_MEXQ_partex2_container, cls_hide, !mod_MEX_dict.has_partex);

// - delete all partex that are not selected, also delete assighnments an keys of deleted partex
        let remaining_partex_pk = null, remaining_examperiod = null;
        const deleted_partex_pk_list = [];
        for (const key in mod_MEX_dict.partex_dict) {
            if (mod_MEX_dict.partex_dict.hasOwnProperty(key)) {
                const partex_pk = (Number(key)) ? Number(key) : null;
                if (partex_pk !== mod_MEX_dict.sel_partex_pk ){
                    delete mod_MEX_dict.partex_dict[key];
                } else {
                    remaining_partex_pk = mod_MEX_dict.sel_partex_pk;
                };
            };
        };
        if (remaining_partex_pk){
            const remaining_p_dict = mod_MEX_dict.partex_dict[remaining_partex_pk];
    //console.log( "remaining_p_dict", remaining_p_dict);
            remaining_examperiod =  remaining_p_dict.examperiod
        };

// set exam_examperiod to remaining_examperiod
        if (remaining_examperiod) {
            mod_MEX_dict.examperiod = remaining_examperiod;
        } else if (mod_MEX_dict.examperiod === 12) {
            mod_MEX_dict.examperiod = 1;
        };
        MEX_set_examperiod_checkboxes();

// get amount from sel_partex_pk and put it in mod_MEX_dict.amount
        const sel_p_dict = mod_MEX_dict.partex_dict[mod_MEX_dict.sel_partex_pk];
        mod_MEX_dict.amount = (sel_p_dict && sel_p_dict.amount) ? sel_p_dict.amount : 0;
        mod_MEX_dict.scalelength =  (sel_p_dict && sel_p_dict.scalelength) ? sel_p_dict.scalelength : 0;

        el_MEXQ_input_amount.value = mod_MEX_dict.amount;
        el_MEXQ_input_scalelength.value = mod_MEX_dict.scalelength;

        MEXQ_FillTablePartex();
        MEXQ_validate_and_disable();
    };  // MEXQ_remove_partex

//=========  MEXQ_get_next_partexname  ================ PR2022-01-14
    function MEXQ_get_next_partexname() {
        //console.log("===== MEXQ_get_next_partexname =====");
        let max_number = 0, list_count = 0;
        if (mod_MEX_dict.partex_dict){
            for (const p_dict of Object.values(mod_MEX_dict.partex_dict)) {
                list_count += 1;
                const partex_name = p_dict.name;
                //check if end of name is number
                if (partex_name && partex_name.includes(" ")){
                    const arr = partex_name.split(" ");
                    if (arr.length){
                        const last_chunk = arr[arr.length-1];
                        const last_number = Number(last_chunk);
                        if (last_number && last_number > max_number){
                            max_number = last_number;
                        };
                    };
                };
            };
            if (list_count > max_number) { max_number = list_count};
        };
        const next_number = max_number + 1;
        const next_partex_name = "Deelexamen " + next_number;
        //console.log("next_partex_name", next_partex_name);
        return next_partex_name
    };  // MEXQ_get_next_partexname

//=========  MEXQ_get_next_partex_pk  ================ PR2022-01-14
    function MEXQ_get_next_partex_pk() {
        //console.log("===== MEXQ_get_next_partex_pk =====");
        let max_partex_pk = 0;
        if (mod_MEX_dict.partex_dict){
            for (const data_dict of Object.values(mod_MEX_dict.partex_dict)) {
                // key = pk but string type, get data_dict.pk instead
                const partex_pk = (data_dict.pk) ? data_dict.pk : null;
                // dont skip deleted partex
                if (partex_pk && partex_pk > max_partex_pk){
                    max_partex_pk = partex_pk;
                };
            };
        }
        const next_partex_pk = max_partex_pk + 1;
        //console.log("next_partex_pk", next_partex_pk);
        return next_partex_pk
    };  // MEXQ_get_next_partex_pk



//=========  MEX_set_headertext1_examperiod  ================ PR2022-05-16
    function MEX_set_headertext1_examperiod() {
        //console.log("===== MEX_set_headertext1_examperiod =====");
    // ---  set header text
        let header1_text = loc.Exam, header2_text = null;

        if (loc.examtype_caption && mod_MEX_dict.examtype){
            header1_text = loc.examtype_caption[mod_MEX_dict.examtype]
        };
        const depbase_code = (setting_dict.sel_depbase_code) ? setting_dict.sel_depbase_code : "---";
        header1_text += " " + depbase_code;
        const examperiod_caption = (loc.examperiod_caption && mod_MEX_dict.examperiod) ? loc.examperiod_caption[mod_MEX_dict.examperiod] : "---"

        header1_text += " " + examperiod_caption;

        el_MEXQ_header1.innerText = header1_text

    };  // MEX_set_headertext1_examperiod


//=========  MEX_set_headertext2_subject  ================ PR2022-01-12
    function MEX_set_headertext2_subject() {
        console.log("===== MEX_set_headertext2_subject =====");
        console.log("mod_MEX_dict", mod_MEX_dict);
        console.log("mod_MEX_dict.subject_name", mod_MEX_dict.subject_name);
        console.log("mod_MEX_dict.lvl_abbrev", mod_MEX_dict.lvl_abbrev);

// update text in headertext2_subject
        let header2_text = null;
        if(!mod_MEX_dict.subject_pk) {
            header2_text = (mod_MEX_dict.is_addnew) ? loc.Add_exam : loc.No_subject_selected;
        } else {
            header2_text = (mod_MEX_dict.subject_name) ? mod_MEX_dict.subject_name : "---";
            if(mod_MEX_dict.lvl_abbrev) { header2_text += " - " + mod_MEX_dict.lvl_abbrev; }
            if(mod_MEX_dict.version) { header2_text += " - " + mod_MEX_dict.version; }
        }
        el_MEXQ_header2.innerText = header2_text
    };  // MEX_set_headertext2_subject

//========= MEX_goto_next  ================== PR2021-04-07
    function MEX_goto_next(q_number, event){
        //console.log(" --- MEX_goto_next ---")
        //console.log("event.key", event.key, "event.shiftKey", event.shiftKey)
        // This is not necessary: (event.key === "Tab" && event.shiftKey === true)
        // Tab and shift-tab move cursor already to next / prev element
        if (["Enter", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].indexOf(event.key) > -1) {
// --- get move_vertical based on event.key and event.shiftKey
            let move_vertical = (["Enter", "Tab", "ArrowDown"].includes(event.key) ) ? 1 :
                                    (event.key === "ArrowUp") ? -1 : 0

            let pge_index = mod_MEX_dict.pge_index;
            const q_min = mod_MEX_dict.page_min_max[pge_index].min;
            const q_max = mod_MEX_dict.page_min_max[pge_index].max;

// --- set move up / down 1 row when min / max index is reached
            let new_q_number = q_number + move_vertical;
            if(new_q_number > q_max) {
                pge_index += 1;
                MEX_BtnPageClicked(null, pge_index);

                new_q_number = q_min
            } else if(new_q_number < q_min) {
                pge_index -= 1;
                MEX_BtnPageClicked(null, pge_index);
            }
            mod_MEX_dict.pge_index = pge_index

// --- set focus to next / previous cell
            const next_id = "idMEXq_" + mod_MEX_dict.sel_partex_pk + "_" + new_q_number;
            set_focus_on_el_with_timeout(document.getElementById(next_id), 50);
        }
    }  // MEX_goto_next

//=========  MEXQ_CalcScalelength  ================ PR2022-03-23
    //TODO calc
    function MEXQ_CalcScalelength(el_input) {
        console.log( "===== MEXQ_CalcScalelength  ========= ");
        const new_value = el_input.value;
        console.log( "new_value", new_value, typeof new_value);
        // InputScalelength is only used when has_partex
        let new_number = null, msg_err = "", has_error = false;
        if (!new_value){
            has_error = true;
            msg_err = loc.err_list.Max_score_cannot_be_blank + "<br>";
        } else {
            new_number = Number(new_value);
            // the remainder / modulus operator (%) returns the remainder after (integer) division.
            if(!new_number || (new_number % 1) || (new_number < 1) || (new_number > 250) ) {
                has_error = true;
                msg_err = loc.Maximum_score + " '" + new_value + "' " + loc.err_list.not_allowed + "<br>";
            };
        };

        if (has_error) {
            el_input.value = (mod_MEX_dict.scalelength) ? mod_MEX_dict.scalelength : null;
            set_focus_on_el_with_timeout(el_input, 50)
        } else if (new_number) {
            mod_MEX_dict.scalelength = new_number;
            //MEX_SetPages();
            // only show btn_pge when there are multiple pages
            //MEXQ_show_btnpage();
            //MEX_BtnPageClicked();
        }

// ---  disable save button when not all required fields have value
        //MEXQ_validate_and_disable();

    }; // MEXQ_CalcScalelength


//=========  MEXQ_calc_max_score  ================ PR2022-01-16 PR2022-05-20
    function MEXQ_calc_max_score(partex_pk) {
        console.log(" ===  MEXQ_calc_max_score  =====") ;

        // PR2022-05-20 Exams were published with missing in multiple choice question
        // total_max_score is the total score of this partex
        let total_max_score = 0;
        let total_keys_missing = 0;
        let total_maxscore_missing = 0;

        if (partex_pk){
            const p_dict = mod_MEX_dict.partex_dict[partex_pk];
            // p_amount is entered value of number of questions in partex
            const p_amount = p_dict.amount;
// ---  loop through all questions. Dont use "for (const q_dict of Object.values(p_dict.a_dict))" in case some q_dicts are missing
            for (let q = 1; q <= p_amount; q++) {
// ---  loop through mod_MEX_dict.partex_dict
                //q_dict = {max_char: 'C', max_score: 0, min_score: 0, keys: 'a', result: null}
                const q_dict = p_dict.a_dict[q];
                if (!q_dict){
                    total_maxscore_missing += 1;
                } else {
                    // q is a multiple choice question when max_char has value
                    if (q_dict.max_char){
                        // check if keys exists when multiple choice question
                        if(!q_dict.keys){
                            total_keys_missing += 1;
                        } else {
                            if (q_dict.max_score){
                                total_max_score += q_dict.max_score
                            } else {
                                // default max_score of character is 1 when q_dict.max_score has no value
                                total_max_score += 1;
                            };
                        };
                    } else {
                        if (q_dict.max_score) {
                            total_max_score += q_dict.max_score
                        } else {
                            total_maxscore_missing += 1;
                        }
                    };
                };
            };
            if(total_maxscore_missing || total_keys_missing){
                total_max_score = 0;
            }
            p_dict.missing_maxscore = total_maxscore_missing;
            p_dict.missing_keys = total_keys_missing;
            p_dict.max_score = total_max_score;
        };

        return total_max_score;
    };  // MEXQ_calc_max_score

//=========  MEXQ_calc_amount_maxscore  ================ PR2022-03-23
    function MEXQ_calc_amount_maxscore() {
        //console.log("===== MEXQ_calc_amount_maxscore =====");

        //console.log( "mod_MEX_dict.partex_dict: ", mod_MEX_dict.partex_dict, typeof mod_MEX_dict.partex_dict);

        let total_amount = 0, total_max_score = 0;
        for (const p_dict of Object.values(mod_MEX_dict.partex_dict)) {

            const partex_amount = (p_dict.amount) ? p_dict.amount : 0;
            total_amount += partex_amount;


            // number of questions of pertex (p_amount) is entered value, not the counted questions
            const p_amount = (p_dict.amount) ? p_dict.amount : 0;
            let p_max_score = 0;
    // ---  loop through questions of p_dict
            for (const q_dict of Object.values(p_dict.a_dict)) {
                let q_max_score = 0;
                if (q_dict.max_score) {
                    q_max_score += q_dict.max_score
                } else if (q_dict.max_char){
                    // default max_score of character is 1 when q_dict.max_score has no value
                    q_max_score += 1;
                };
                p_max_score += q_max_score;
            };
            // put max_score back in p_dict
            p_dict.max_score = p_max_score
            total_max_score += p_max_score
        };

    //console.log("total_amount", total_amount, typeof total_amount);
    //console.log("total_max_score", total_max_score, typeof total_max_score);

        mod_MEX_dict.amount = total_amount;
        mod_MEX_dict.scalelength = total_max_score;
        el_MEXQ_input_amount.value = (total_amount) ? total_amount : null;
        el_MEXQ_input_scalelength.value = (total_max_score) ? total_max_score : null;
    };  // MEXQ_calc_amount_maxscore

///////////////////////////////////////
// +++++++++ MOD EXAM ANSWERS ++++++++++++++++ PR2021-05-23 PR2022-01-21 PR2022-04-20
    function MEXA_Open(el_input){
        console.log(" ===  MEXA_Open  =====");

// - reset mod_MEX_dict
        const is_addnew = false;
        const is_result_page = true;
        MEX_reset_mod_MEX_dict(is_addnew, is_result_page);

// el_input must always have value
        // mod_MEX_dict.is_permit_admin gets value in MEX_reset_mod_MEX_dict
        // is_permit_same_school = (permit_dict.requsr_same_school && permit_dict.permit_crud);
        if(mod_MEX_dict.is_permit_same_school){

            const tblRow = t_get_tablerow_selected(el_input)
            const pk_int = get_attr_from_el_int(tblRow, "data-pk");
            const [index, found_dict, compare] = b_recursive_integer_lookup(grade_exam_rows, "id", pk_int);
            const data_dict = (!isEmpty(found_dict)) ? found_dict : null;
            const datarow_index = index;
        console.log("grade_with_exam_dict", data_dict);

            if(data_dict) {
            // check if grade_exam is approved or publishesd -if so: return msg
            // get exam questions
                if(data_dict.ce_exam_id){

            // check if grade_exam is approved or publishesd -if so: return msg
                    if(data_dict.secret_exam){
                        const msg_html = [loc.This_is_a_secret_exam_01, loc.This_is_a_secret_exam_02, loc.This_is_a_secret_exam_03, loc.This_is_a_secret_exam_04].join("<br>");
                        b_show_mod_message_html(msg_html);
                    } else if(data_dict.ce_exam_published_id){
                        const msg_html = [loc.err_list.This_exam_is_submitted, loc.err_list.You_cannot_make_changes].join("<br>");
                        b_show_mod_message_html(msg_html);
                    } else if (data_dict.ce_exam_auth1by_id || data_dict.ce_exam_auth2by_id) {
                        const msg_html = [loc.err_list.This_exam_is_approved, loc.err_list.You_cannot_make_changes].join("<br>");
                        b_show_mod_message_html(msg_html);
                    } else {
                        const sel_subject_pk = (data_dict.subj_id) ? data_dict.subj_id : null;
                        const fullname = (data_dict.fullname) ? data_dict.fullname : "---";

                        mod_MEX_dict.grade_map_id = data_dict.mapid;
                        mod_MEX_dict.grade_pk = data_dict.id;
                        mod_MEX_dict.student_pk = data_dict.student_id;
                        mod_MEX_dict.lvlbase_pk = data_dict.lvlbase_id;
                        mod_MEX_dict.lvl_abbrev = data_dict.lvl_abbrev;

                        mod_MEX_dict.has_partex = data_dict.ceex_has_partex;

                        mod_MEX_dict.partex_dict = {};

    // ---  lookup ete_exam_dict in ete_exam_rows
                        const exam_pk = data_dict.ce_exam_id;
                        const [index, found_dict, compare] = b_recursive_integer_lookup(ete_exam_rows, "id", exam_pk);
                        const ete_exam_dict = found_dict;
            console.log( "ete_exam_dict", ete_exam_dict );

                        if(ete_exam_dict){
                            MEX_get_subject(sel_subject_pk);
                            MEX_get_ete_exam_dict_info(ete_exam_dict);

                            MEX_FillDictPartex(ete_exam_dict, data_dict);
                            MEX_FillDictAssignment(ete_exam_dict);
                            MEXA_FillDictResults(data_dict);

                            MEXA_FillTablePartex();

                            mod_MEX_dict.sel_tab = "tab_answers";
                            mod_MEX_dict.examyear_pk = setting_dict.sel_examyear_pk;
                            mod_MEX_dict.depbase_pk = setting_dict.sel_depbase_pk;
                            mod_MEX_dict.examperiod = setting_dict.sel_examperiod;
                            mod_MEX_dict.examtype = setting_dict.sel_examtype;

                            const exam_name = (ete_exam_dict.ceex_name) ? ete_exam_dict.ceex_name : "---";

                            // these are entered in MEX_get_ete_exam_dict_info
                                //mod_MEX_dict.exam_pk = exam_dict.id;
                                //mod_MEX_dict.department_pk = exam_dict.department_id;
                                //const version = (exam_dict.version) ? exam_dict.version : null;
                                //mod_MEX_dict.version = version;
                                //const amount = (exam_dict.amount) ? exam_dict.amount : "---";
                                //mod_MEX_dict.amount = amount;

                            // these are entered in MEX_get_subject
                                //mod_MEX_dict.subject_pk = (exam_dict.subj_id) ? exam_dict.subj_id : null;
                                // mod_MEX_dict.subject_code = (exam_dict.subjbase_code) ? exam_dict.subjbase_code : null;
                                //mod_MEX_dict.subject_name = (exam_dict.subj_name) ? exam_dict.subj_name : null;

                    // ---  set header text
                            const examtype = (loc.examtype_caption && mod_MEX_dict.examtype) ? loc.examtype_caption[mod_MEX_dict.examtype] : loc.Exam;
                            const depbase_code = (setting_dict.sel_depbase_code) ? setting_dict.sel_depbase_code : "---";
                            const examperiod_caption = (loc.examperiod_caption && mod_MEX_dict.examperiod) ? loc.examperiod_caption[mod_MEX_dict.examperiod] : "---"
                            const header1_text = examtype + " " + depbase_code + " " + examperiod_caption;

            console.log("mod_MEX_dict", mod_MEX_dict);
            console.log("examtype", examtype);
            console.log("................header1_text", header1_text);

                            el_MEXQ_header1.innerText = header1_text;
                            el_MEXQ_header3_student.innerText = fullname;

                    // also update text in header 2
                            MEX_set_headertext2_subject();

        // - hide list of partex in section question, answer, keys when has_partex = false;
                            add_or_remove_class(el_MEXQ_partex2_container, cls_hide, !mod_MEX_dict.has_partex);

        // ---  set buttons
                            add_or_remove_class(el_MEX_btn_tab_container, cls_hide, mod_MEX_dict.is_permit_same_school);
                            MEX_BtnTabClicked();
                            MEX_SetPages();
                            // only show btn_pge when there are multiple pages
                            //MEXQ_show_btnpage();
                            //MEX_BtnPageClicked();

                    // ---  disable save button when not all required fields have value
                            // TODOMEXQ_validate_and_disable();

                    // ---  show modal
                            $("#id_mod_exam_questions").modal({backdrop: true});
                        }  //  if(ete_exam_dict)


                    }  //  if(data_dict.ce_exam_published_id){
                }  // if(data_dict.exam_id)
            }  // if(data_dict)
        }  //  if(is_permit_same_school)
    };  // MEXA_Open

//========= MEXA_Save  ============= PR2021-05-24
    function MEXA_Save() {
        console.log("===== MEXA_Save ===== ");
        console.log( "mod_MEX_dict: ", mod_MEX_dict);

        if(mod_MEX_dict.is_permit_same_school){
            const upload_dict = {
                table: 'grade',
                mode: "update",
                return_grades_with_exam: true,
                examyear_pk: mod_MEX_dict.examyear_pk,
                depbase_pk: mod_MEX_dict.depbase_pk,
                //lvlbase_pk: mod_MEX_dict.lvlbase_pk,
                examperiod: mod_MEX_dict.examperiod,

                examtype: mod_MEX_dict.examtype,
                exam_pk: mod_MEX_dict.exam_pk,
                grade_pk: mod_MEX_dict.grade_pk,
                student_pk: mod_MEX_dict.student_pk,
                //subject_pk: mod_MEX_dict.subject_pk,
                //subject_code: mod_MEX_dict.subject_code
            }

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
            // partex_dict = { 1: {pk: 1, name: 'Deelexamen 1', amount: 7, max: 0, mode: 'create' } ]  }
            let partex_str = "", result_str = "";
            let total_amount = 0, non_blanks = 0;

            for (const p_dict of Object.values(mod_MEX_dict.partex_dict)) {

                const partex_pk = p_dict.pk;
                const partex_amount = p_dict.amount
                // not in use any more:
                const partex_taken = p_dict.partex_taken;

// skip partex that is not taken
                // not in use any more:
                // if (partex_taken){
                if (true){

// --- create result_str
            // format of ce_exam_result_str is:
            // grade_dict.ce_exam_result = "1;35#2|2;a|3;a|4;a|5;a|6;1|7;x|8;a|9;0#4|1;1|2;a|3;1|4;a|5;a|6;a|7;a|8;x|9;a|10;1#6|1;a|2;a|3;1|4;a|5;1|6;a|7;1|8;a|9;1|10;1#7|1;1|2;1|3;1#8|1;1#9|1;5#10|1;7"
            //  - ce_exam_result starts with blanks; total_amount #
            //  - Note: total score was stored in pescore, is moved to ce_exam_score PR2022-05-15
            //  - partal exams are separated with #
            //  - partex = "2;2;4|1;C;;|2;D;3;"
            //      first array between || contains partex info : # partex_pk ; blanks ; total_amount /
            //      others contain answers info: | q_number ; char ; score ; blank |

                    total_amount += partex_amount

                    result_str += "#" + partex_pk;
                    const a_dict = p_dict.a_dict;

                    if (a_dict){
    //console.log( "a_dict: ", a_dict);
                        for (let q_number = 1, dict; q_number <= partex_amount; q_number++) {
                            const value_dict = a_dict[q_number];

    //console.log( "value_dict: ", value_dict);
            // value_dict:  {keys: "", max_char: "D", max_score: 2, min_score: 0, result: 'b''}

                            if(value_dict){
                                if (value_dict.result) {
                                    result_str += [
                                        "|", q_number,
                                        ";", value_dict.result
                                         ].join("");

                                    non_blanks += 1;
                                };
                    }}};
                };
            };

// add blanks and total_amount at the beginning of the string
            if(result_str) {
                const blanks = (total_amount > non_blanks) ? (total_amount - non_blanks) : 0;
                result_str = blanks + ";" + total_amount + result_str  // result_str starts with #
            };
    console.log( "result_str: ", result_str);
            upload_dict.ce_exam_result = (result_str) ? result_str : null;

            UploadChanges(upload_dict, urls.url_grade_upload);
        };  // if(has_permit_edit

// ---  hide modal
        $("#id_mod_exam_questions").modal("hide");
    }  // MEXA_Save

//========= MEXA_InputAnswer  =============== PR2021-05-25
    function MEXA_InputAnswer(el_input, event){
        console.log(" --- MEXA_InputAnswer ---");
        //console.log("el_input.id: ", el_input.id);
        //console.log("event.key", event.key, "event.shiftKey", event.shiftKey);
        // el_input.id = 'idMEXq_1_24'

        const el_id_arr = el_input.id.split("_")
        const partex_pk = (el_id_arr && el_id_arr[1]) ? Number(el_id_arr[1]) : null;
        const q_number = (el_id_arr && el_id_arr[2]) ? Number(el_id_arr[2]) : null;

    console.log("el_id_arr", el_id_arr)
    console.log("partex_pk", partex_pk)
    console.log("q_number", q_number)

        if (partex_pk && q_number){
            if (mod_MEX_dict.is_permit_same_school){
                // lookup assignment and question
                const p_dict = mod_MEX_dict.partex_dict[partex_pk];
                const q_dict = p_dict.a_dict[q_number];
    console.log("p_dict", p_dict)
    console.log("q_dict", q_dict)
                // q_dict = {blank: null, char: null, keys: "", max_char: "", max_score: 4, min_score: 0, result: "2", score: "2"}

            // open question input has a number (8)
            // multiple choice question has one letter
//================================================================
// when input is answer, entered by requsr_same_school
                if (isEmpty(q_dict)){
                    msg_err = loc.err_list.Exam_assignment_does_notexist + "<br>" + loc.err_list.Contact_divison_of_exams
    console.log("msg_err", msg_err)
                } else {
                    let char_str = null, is_blank = false, msg_err = "";
                    const input_value = el_input.value;

                    const max_score = (q_dict.max_score) ? q_dict.max_score : "";
                    const max_char = (q_dict.max_char) ? q_dict.max_char : "";
                    const is_multiple_choice = (!!max_char);
    //console.log("max_score", max_score)
    //console.log("max_char", max_char)
    //console.log("is_multiple_choice", is_multiple_choice)

        // reset answer values
                    q_dict.char = null;
                    q_dict.score = null;
                    q_dict.blank = null;
                    q_dict.result = null;

                    if (input_value){
                        const input_number = Number(input_value);

    console.log("input_value", input_value, typeof input_value);
    console.log("input_number", input_number, typeof input_number);
    console.log("max_score", max_score, typeof max_score);

                        if (input_number || input_number === 0){
                            // check if is integer
                            if (is_multiple_choice){
                                msg_err =  loc.err_list.This_isa_multiplechoice_question  +
                                "<br>" + loc.err_list.must_enter_letter_between_a_and_ + max_char.toLowerCase() + "'," +
                                "<br>" + loc.err_list.or_an_x_if_blank;
                            } else if (input_number < 0 || input_number > max_score){
                                msg_err += " '" + input_value  + "'" + loc.err_list.not_allowed +
                                "<br>" + loc.err_list.must_enter_whole_number_between_0_and_ + max_score + "," +
                                "<br>" + loc.err_list.or_an_x_if_blank;
                            } else {
                                char_str = input_number.toString();
                            };
                        } else {
                            const input_lc = input_value.toLowerCase();
    console.log("input_lc", input_lc)
                            if (input_lc === "x"){
                                // pass, enter x for blank answer, also when not multiple choice
                                is_blank = true;
                                char_str = "x";
                            } else if (!is_multiple_choice){
                                msg_err += " '" + input_value  + "'" + loc.err_list.not_allowed +
                                "<br>" + loc.err_list.must_enter_whole_number_between_0_and_ + max_score + "," +
                                "<br>" + loc.err_list.or_an_x_if_blank;
                            } else if (input_value.length > 1){
                                msg_err += " '" + input_value  + "'" + loc.err_list.not_allowed +
                                "<br>" + loc.err_list.must_enter_letter_between_a_and_ + max_char.toLowerCase() + "'," +
                                "<br>" + loc.err_list.or_an_x_if_blank;
                            // y, z are not allowed because 'x' value is used for blank
                            } else if(!"abcdefghijklmnopqrstuvwx".includes(input_lc)){
                                msg_err += " '" + input_value  + "'" + loc.err_list.not_allowed +
                                "<br>" + loc.err_list.must_enter_letter_between_a_and_ + max_char.toLowerCase() + "'," +
                                "<br>" + loc.err_list.or_an_x_if_blank;
                            } else {
                                const max_char_lc = max_char.toLowerCase();
    console.log("max_char_lc", max_char_lc)
                                if (input_lc > max_char_lc ) {
    console.log("input_lc > max_char_lc", max_char_lc)
                                    msg_err += "'" + input_value  + "'" + loc.err_list.not_allowed +
                                    "<br>" + loc.err_list.must_enter_letter_between_a_and_ + max_char.toLowerCase() + "'," +
                                    "<br>" + loc.err_list.or_an_x_if_blank;
                                } else {
                                    char_str = input_lc;
                                };
                            };
                        };
                    };

                    q_dict.result = char_str;
                    el_input.value = char_str;

    console.log("q_dict", q_dict)
    console.log("p_dict", p_dict)
    console.log("mod_MEX_dict", mod_MEX_dict)
    console.log("is_multiple_choice", is_multiple_choice)

                    if (!msg_err) {
                        if(char_str){
                            // use answers_dict = {blank: char_str} instead of answers_dict.blank = char_str, in order to remove other answers
                            if (is_blank){
                                q_dict.blank = char_str;
                            } else if (is_multiple_choice){
                                q_dict.char = char_str;
                            } else {
                                q_dict.score = char_str;
                            };
                        };

                        //if(char_str){
                        // set focus to net input element, got btn save after last question

                            const next_question = q_number + 1;
                            const next_id = (next_question > mod_MEX_dict.amount) ? "id_MEXQ_btn_save" :
                                            "idMEXq_" + mod_MEX_dict.sel_partex_pk + "_" + (q_number + 1);
                            const el_focus = document.getElementById(next_id);
                            if(el_focus) {set_focus_on_el_with_timeout(el_focus, 50)};
                        //}

                    } else {
                //  on error: set input_value null and delete answer from mod_MEX_dict.answers_dict

                        el_mod_message_container.innerHTML = msg_err;
                        $("#id_mod_message").modal({backdrop: false});

                // set focus to current input element
                        el_mod_message_btn_cancel.setAttribute("data-nextid", "idMEXq_" + mod_MEX_dict.sel_partex_pk + "_" + q_number);
                        set_focus_on_el_with_timeout(el_mod_message_btn_cancel, 150 );

                    };  //  if (!msg_err)
                };  //  if (isEmpty(q_dict))
            };  // if (mod_MEX_dict.is_permit_same_school)

    //console.log("mod_MEX_dict", mod_MEX_dict);

            MEX_goto_next(q_number, event);
        };  // if (partex_pk && q_number)
    };  // MEXA_InputAnswer

///////////////////////////////////////
// +++++++++ MOD DUO EXAMS ++++++++++++++++ PR2022-02-28
    function MDUO_Open(el_input){
        console.log(" ===  MDUO_Open  =====") ;
        const is_permit_admin = (permit_dict.requsr_role_admin && permit_dict.requsr_country_pk === 1 && permit_dict.permit_crud);
        if(is_permit_admin){

        console.log("setting_dict.sel_examperiod", setting_dict.sel_examperiod);
        console.log("loc.options_examperiod_exam", loc.options_examperiod_exam);

            const ep_int = ([1,2].includes(setting_dict.sel_examperiod)) ? setting_dict.sel_examperiod : 12; // value 12 = all examperiods
            const ep_dict = b_lookup_dict_in_dictlist(loc.options_examperiod_exam, "value", ep_int);
            el_MDUO_examperiod.innerHTML = (!isEmpty(ep_dict)) ? ep_dict.caption : "---";

            add_or_remove_class(el_MDUO_level.parentNode, cls_hide, !setting_dict.sel_dep_level_req);
            const level_txt = (setting_dict.sel_lvlbase_pk) ? (setting_dict.sel_level_abbrev) ? setting_dict.sel_level_abbrev : "---": "<" + loc.All_levels + ">";
            el_MDUO_level.innerText = level_txt

            MDUO_FillDict();
            MDUO_FillSelectTables();
            el_MDUO_btn_save.disabled = true;
    // ---  show modal
            $("#id_mod_duoexams").modal({backdrop: true});
        } ; //  if(is_permit_admin)

    };  // MDUO_Open


//=========  MDUO_FillDict  ================ PR2022-02-28
    function MDUO_FillDict() {
        console.log("===== MDUO_FillDict =====");

        b_clear_dict(mod_MDUO_dict);
        mod_MDUO_dict.duo_subject_list = [];
        if(subject_rows && subject_rows.length){

    // loop through subject_rows
            for (let i = 0, data_dict; data_dict = duo_subject_rows[i]; i++) {
                const dict = {
                    subj_id: data_dict.id,
                    subjbase_id: data_dict.subjbase_id,
                    subjbase_code: data_dict.subjbase_code,
                    subj_name: data_dict.subj_name,
                    lvl_id: data_dict.lvl_id,
                    lvlbase_id: data_dict.lvlbase_id,
                    lvl_abbrev: data_dict.lvl_abbrev,
                    dep_id: data_dict.dep_id,
                    depbase_id: data_dict.depbase_id,
                    depbase_code: data_dict.depbase_code
                };
                mod_MDUO_dict.duo_subject_list.push(dict);
            };
            //console.log("mod_MDUO_dict.duo_subject_list", mod_MDUO_dict.duo_subject_list);
        };

        mod_MDUO_dict.nterm_list = [];
        if(ntermentable_rows && ntermentable_rows.length){
            for (let i = 0, data_dict; data_dict = ntermentable_rows[i]; i++) {
                const dict = {
                    nterm_id: data_dict.id,
                    leerweg: data_dict.leerweg,
                    n_term: data_dict.n_term,
                    nex_id: data_dict.nex_id,
                    omschrijving: data_dict.omschrijving,
                    opl_code: data_dict.opl_code,
                    sty_id: data_dict.sty_id,
                    tijdvak: data_dict.tijdvak
                };
                mod_MDUO_dict.nterm_list.push(dict);
            };
        };

        mod_MDUO_dict.duo_exam_list = [];
        if(duo_exam_rows && duo_exam_rows.length){
    // loop through subject_rows
            for (let i = 0, data_dict; data_dict = duo_exam_rows[i]; i++) {
                // show only DUO exams
                //if (!data_dict.ete_exam){
                    const dict = {
                        ndsl_pk: data_dict.ndsl_pk,
                        id: data_dict.id,
                        dep_id: data_dict.dep_id,
                        depbase_code: data_dict.depbase_code,
                        nex_id: data_dict.nex_id,
                        lvl_abbrev: data_dict.lvl_abbrev,
                        lvl_id: data_dict.lvl_abbrev,
                        subj_id: data_dict.subj_id,
                        subjbase_code: data_dict.subjbase_code,
                        ntb_omschrijving: data_dict.ntb_omschrijving,
                    };
                //};
                mod_MDUO_dict.duo_exam_list.push(dict);
            };
        };
        console.log("mod_MDUO_dict.duo_exam_list", mod_MDUO_dict.duo_exam_list);


        //const JustLinkedAwpId = null, JustUnLinkedAwpId = null, JustUnlinkedExcId = null;
        //Fill_AEL_Table(JustLinkedAwpId, JustUnLinkedAwpId, JustUnlinkedExcId)

    };  // MDUO_FillDict

//=========  MDUO_FillSelectTables  ================ PR2022-04-07
    function MDUO_FillSelectTables() {
        //console.log( "===== MDUO_FillSelectTables ========= ")

        const table_list = ["subject", "ntermentable"];
        for (let i = 0, tblName; tblName = table_list[i]; i++) {
            MDUO_FillSelectTable(tblName);
        };
    };

//=========  MDUO_FillSelectTable  ================ PR2022-04-05
    function MDUO_FillSelectTable(tblName) {
        //console.log( "===== MDUO_FillSelectTable ========= ");
        //console.log( "tblName: ", tblName);

        const tblBody_select = (tblName === "subject") ? el_MDUO_tblBody_subjects :
                               (tblName === "ntermentable") ? el_MDUO_tblBody_duo_exams : null;
        const data_rows = (tblName === "subject") ? mod_MDUO_dict.duo_subject_list :
                          (tblName === "ntermentable") ? mod_MDUO_dict.nterm_list : null;

        const col_width_list = (tblName === "subject") ? (setting_dict.sel_dep_level_req) ? ["tw_090", "tw_090", "tw_090"] : ["tw_090", "tw_090"] :
                               (tblName === "ntermentable") ? ["tw_280"] :[];

        //console.log("data_rows", data_rows);
        tblBody_select.innerText = null;

        let row_count = 0, add_to_list = false;

// ---  loop through duo_subject_rows
        const mapped_nterm_level = {tkl: ["gl", "tl"], pkl: ["kb"], pbl: ["bb"]}
        if(data_rows && data_rows.length){
            for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
    //console.log("data_dict", data_dict);

            //console.log( "mod_MDUO_dict.subj_pk", mod_MDUO_dict.subj_pk, typeof mod_MDUO_dict.subj_pk);
            //console.log( "data_dict.subj_id", data_dict.subj_id, typeof data_dict.subj_id);
            // add only when eam has same subject as grade, and also the same depbase and lvlbase_id
                let show_row = false;
                if (setting_dict.sel_dep_level_req){
                    if (tblName === "subject"){
                        // filter by lvlbase_id is also done at server
                        show_row = (!setting_dict.sel_lvlbase_pk || setting_dict.sel_lvlbase_pk === data_dict.lvlbase_id)
                    } else if (tblName === "ntermentable") {
                        if (!setting_dict.sel_lvlbase_pk ){
                            show_row = true;
                        } else {
                            if (data_dict.leerweg){
                                const leerweg_lc = data_dict.leerweg.toLowerCase();
                                const level_abbrev_lc = (setting_dict.sel_level_abbrev) ? setting_dict.sel_level_abbrev.toLowerCase() : null;
                                if (level_abbrev_lc){
                                    const lookup_array = mapped_nterm_level[level_abbrev_lc];
                                    if(lookup_array && lookup_array.length){
                                        for (let j = 0, lw; lw = lookup_array[j]; j++) {
                                            if (leerweg_lc.includes(lw)){
                                                show_row = true;
                                                break;
                            }}}}};
                        };
                    };
                } else {
                    show_row = true;
                };

        // check if row is already linked in duo_exam_rows
                let is_linked = false;
                 if (tblName === "subject"){
                    for (let j = 0, row; row = duo_exam_rows[j]; j++) {
                         if(data_dict.dep_id === row.dep_id && data_dict.subj_id === row.subj_id){
                            if (!data_dict.lvl_id || data_dict.lvl_id === row.lvl_id){
                                is_linked = true;
                                break;
                    }}};

                } else if (tblName === "ntermentable") {
                    for (let i = 0, row; row = duo_exam_rows[i]; i++) {
    //console.log("row", row);
    //console.log("  data_dict.nterm_id", data_dict.nterm_id, typeof data_dict.ntb_id ,"row.nterm_id", row.ntb_id, typeof row.ntb_id);
                        if (data_dict.nterm_id === row.ntb_id){
    //console.log("  >> equals data_dict.id", data_dict.id)
                            is_linked = true;
                            console.log("  >> is_linked", row.is_linked)
                            break;
                    }};
                };

    //console.log("is_linked", is_linked);
                if (show_row && !is_linked){
                    row_count += 1;
                    MDUO_FillSelectRow(tblName, data_dict, tblBody_select, col_width_list);
                };
            };
        };
        if(!row_count){
            let tblRow = tblBody_select.insertRow(-1);
            let td = tblRow.insertCell(-1);
            td.innerText = loc.No_exam_for_this_subject;
            td.innerText = (tblName === "subject") ? loc.No_subjects_found :
                               (tblName === "ntermentable") ? loc.No_exams_found : null;

        } else if(row_count === 1){
            let tblRow = tblBody_select.rows[0]
            if(tblRow) {
// ---  make first row selected
                //tblRow.classList.add(cls_selected_item)

                MDUO_SelectItem(tblRow);
            };
        };
        return row_count
    }; // MDUO_FillSelectTable

//=========  MDUO_FillSelectRow  ================ PR2022-04-05
    function MDUO_FillSelectRow(tblName, data_dict, tblBody_select, col_width_list) {
        //console.log( "===== MDUO_FillSelectRow ========= ");
        //console.log( "data_dict: ", data_dict);

//--- loop through data_map
        let pk_int = null;
        let col_txt_list = [];

        let ob1 = (data_dict.subjbase_code) ? data_dict.subjbase_code : "---";
        let ob2 = (data_dict.lvl_abbrev) ? data_dict.lvl_abbrev : "---";
        let ob3 = "---";

        if (tblName === "subject") {
            pk_int = data_dict.subj_id;
            ob3 = (data_dict.depbase_code) ? data_dict.depbase_code : "---";
            col_txt_list = (setting_dict.sel_dep_level_req) ?  [ob1, ob2, ob3] : [ob1, ob3];
        } else if (tblName === "ntermentable") {
            pk_int = data_dict.nterm_id;
            ob1 = (data_dict.omschrijving) ? data_dict.omschrijving : "---";
            col_txt_list = [ob1];
        };

        //console.log( "tblName: ", tblName);
        //console.log( "ob1: ", ob1);
        //console.log( "col_txt_list: ", col_txt_list);
        //console.log( "data_dict: ", data_dict);

        const is_selected_pk = (mod_MDUO_dict.exam_pk != null && exam_pk_int === mod_MDUO_dict.exam_pk)

// ---  lookup index where this row must be inserted
        const row_index = b_recursive_tblRow_lookup(tblBody_select, setting_dict.user_lang, ob1, ob2, ob3);

        //console.log( "row_index: ", row_index);

// ---  insert tblRow  //index -1 results in that the new row will be inserted at the last position.
        let tblRow = tblBody_select.insertRow(row_index);
        tblRow.setAttribute("data-pk", pk_int);
        tblRow.setAttribute("data-ob1", ob1);
        if(ob2){tblRow.setAttribute("data-ob2", ob2)};
        if(ob3){tblRow.setAttribute("data-ob3", ob3)};

        if (tblName === "ntermentable"){
            tblRow.title = ob1;
        } else if (tblName === "subject") {
             tblRow.title = data_dict.subj_name;
        }
// ---  add EventListener to tblRow
        tblRow.addEventListener("click", function() {MDUO_SelectItem(tblName, tblRow)}, false )
// ---  add hover to tblRow
        add_hover(tblRow);
// ---  highlight clicked row
        if (is_selected_pk){ tblRow.classList.add(cls_selected_item)}

        // loop through columns
        for (let i = 0, td, el_div, col_width; col_width = col_width_list[i]; i++) {
    // ---  add first td to tblRow.
            td = tblRow.insertCell(-1);
    // --- add a element to td., necessary to get same structure as item_table, used for filtering
            el_div = document.createElement("div");
                el_div.innerText = col_txt_list[i];
                el_div.classList.add(col_width, "px-4X", "pointer_show" )
            td.appendChild(el_div);
        };
    }  // MDUO_FillSelectRow

//=========  MDUO_SelectItem  ================ PR2022-04-06
    function MDUO_SelectItem(tblName, tblRow) {
        //console.log( "===== MDUO_SelectItem ========= ");
        //console.log( "tblName", tblName);  // "subject", "ntermentable"

// check if other row is selected
        const other_is_selected = (tblName === "subject") ? !!mod_MDUO_dict.sel_nterm_pk :
                                  (tblName === "ntermentable") ? !!mod_MDUO_dict.sel_subject_pk : false;

    //console.log( "other_is_selected", other_is_selected);

// ---  deselect all highlighted rows
        DeselectHighlightedRows(tblRow, cls_selected_item)

// ---  get pk from tblRow and store in in mod_MDUO_dict
        let tblRow_is_selected = false;
        const pk_int = get_attr_from_el_int(tblRow, "data-pk");
        const key_str = (tblName === "subject") ? "sel_subject_pk" : (tblName === "ntermentable") ? "sel_nterm_pk" : null;
        if(key_str){
            mod_MDUO_dict[key_str] = pk_int;
            tblRow_is_selected = true
// ---  highlight clicked row
            tblRow.classList.add(cls_selected_item);
        };
    //console.log( "pk_int", pk_int);
    //console.log( "mod_MDUO_dict", mod_MDUO_dict);

// ---  enable save button when both tables have selected item
        const enable_save_btn =  (tblRow_is_selected && other_is_selected);
        el_MDUO_btn_save.disabled = !enable_save_btn;

    }  // MDUO_SelectItem

//=========  MDUO_link_exam  ================ PR2022-04-06
    function MDUO_link_exam(){
        console.log("===  MDUO_link_exam  =====") ;

// deselect highlighted items
        setTimeout(function (){
           DeselectHighlightedTblbody(el_MDUO_tblBody_subjects, cls_selected_item)
           DeselectHighlightedTblbody(el_MDUO_tblBody_duo_exams, cls_selected_item)
        }, 350);

// get info from subject_list and nterm_list
        let subject_dict = null, nterm_dict = null;
        if (mod_MDUO_dict.sel_subject_pk){
            subject_dict = b_lookup_dict_in_dictlist(mod_MDUO_dict.duo_subject_list, "subj_id", mod_MDUO_dict.sel_subject_pk)
        };
        if (mod_MDUO_dict.sel_nterm_pk){
            nterm_dict = b_lookup_dict_in_dictlist(mod_MDUO_dict.nterm_list, "nterm_id", mod_MDUO_dict.sel_nterm_pk)
        };

        if (subject_dict && nterm_dict){

            const subject_pk = subject_dict.subj_id;
            const dep_pk = subject_dict.dep_id;
            const level_pk = subject_dict.lvl_id;

            const nterm_pk = nterm_dict.nterm_id

        // loop through duo_exam_rows to see if exam already exists
            const ndsl_pk = get_ndsl_pk(nterm_pk, dep_pk, subject_pk, level_pk );
            const duo_exam_dict = get_duo_exam_dict(nterm_pk, dep_pk, subject_pk, level_pk );

            if (!duo_exam_dict){
                id_new += 1;
                const pk_new = "new" + id_new.toString()

                const new_dict = {
                    create: true,
                    id: pk_new,
                    ndsl_pk: ndsl_pk,

                    dep_id: subject_dict.dep_id,
                    depbase_code: subject_dict.depbase_code,
                    lvl_abbrev: subject_dict.lvl_abbrev,
                    lvl_id: subject_dict.lvl_abbrev,
                    subj_id: subject_dict.subj_id,
                    subjbase_code: subject_dict.subjbase_code,

                    ntb_omschrijving: nterm_dict.omschrijving,
                };
                mod_MDUO_dict.duo_exam_list.push(new_dict);
            }; // if (!duo_exam_dict)
            MDUO_FillSelectTables();
        }; // if (subject_dict && nterm_dict)
    };  // MDUO_link_exam

//=========  MDUO_Save  ================ PR2022-04-06
    function MDUO_Save(){
        console.log("===  MDUO_Save  =====") ;

        setTimeout(function (){
           DeselectHighlightedTblbody(el_MDUO_tblBody_subjects, cls_selected_item)
           DeselectHighlightedTblbody(el_MDUO_tblBody_duo_exams, cls_selected_item)
        }, 350);
        // get info from subject

        MDUO_link_exam();

        let subject_dict = null, nterm_dict = null;
        if (mod_MDUO_dict.sel_subject_pk){
            subject_dict = b_lookup_dict_in_dictlist(mod_MDUO_dict.duo_subject_list, "subj_id", mod_MDUO_dict.sel_subject_pk)
        };
        if (mod_MDUO_dict.sel_nterm_pk){
            nterm_dict = b_lookup_dict_in_dictlist(mod_MDUO_dict.nterm_list, "nterm_id", mod_MDUO_dict.sel_nterm_pk)
        };

        if (subject_dict && nterm_dict){
    console.log("subject_dict", subject_dict) ;
    console.log("nterm_dict", nterm_dict) ;

            const subject_pk = subject_dict.subj_id;
            const dep_pk = subject_dict.dep_id;
            const level_pk = subject_dict.lvl_id;

            const nterm_pk = nterm_dict.nterm_id

        // loop through duo_exam_rows to see if exam already exists
            const ndsl_pk = get_ndsl_pk(nterm_pk, dep_pk, subject_pk, level_pk )
    console.log("ndsl_pk", ndsl_pk) ;
            const duo_exam_dict = get_duo_exam_dict(nterm_pk, dep_pk, subject_pk, level_pk )
    console.log("duo_exam_dict", duo_exam_dict) ;

            if (!duo_exam_dict){
                id_new += 1;
                const pk_new = "new" + id_new.toString()

                const upload_dict = {
                    mode: "create",
                    exam_pk: pk_new,
                    subject_pk: subject_pk,
                    department_pk: dep_pk,
                    level_pk: level_pk,
                    ntermentable_pk: nterm_pk,
                };
    // ---  upload changes
                const url_str = urls.url_duo_exam_upload;
                console.log("upload_dict", upload_dict) ;
                console.log("url_str", url_str) ;
                UploadChanges(upload_dict, url_str);
            }; // if (!duo_exam_dict)
        }; // if (subject_dict && nterm_dict)
    };  // MDUO_Save

    function get_ndsl_pk(nterm_pk, dep_pk, subject_pk, level_pk ){
        return ["n", nterm_pk, "d", dep_pk, "s", subject_pk, "l", (level_pk) ? level_pk : ""].join("");
    };

    function get_duo_exam_dict(nterm_pk, dep_pk, subject_pk, level_pk ){
        const ndsl_pk = get_ndsl_pk(nterm_pk, dep_pk, subject_pk, level_pk )
        for (let i = 0, row; row = duo_exam_rows[i]; i++) {
            if (ndsl_pk === row.ndsl_pk) {
                return row;
                break;
            };
        };
        return null;
    };

//////////////////////////////////////////////////////////////////////

//========= MOD UPLOAD N-termen TABLE ====================================
    function MDNT_Open (open_mode ) {  // PR2022-02-25
        console.log("===  MDNT_Open  =====") ;
                $("#id_mod_import_dnt").modal({backdrop: true});
    };

//////////////////////////////////////////////
//========= MOD APPROVE SUBMIT EXAMS ====================================
    function MASE_Open(mode ) {  // PR2022-03-10
        console.log("===  MASE_Open  =====") ;
        console.log("mode", mode) ;
        //console.log("setting_dict", setting_dict) ;
        // modes are: "approve_admin", "submit_admin", "approve_school", "submit_school"
        const is_approve_mode = (mode.includes("approve"));
        const is_submit_mode = (mode.includes("submit"));
        const is_admin_mode = (mode.includes("admin"));
        const is_school_mode = (mode.includes("school"));

        b_clear_dict(mod_MASE_dict);

// check sel_examperiod
        // PR2022-04-24 debug when school: set sel_examperiod to firstperiod when not filled in
        if (is_school_mode && ![1, 2].includes(setting_dict.sel_examperiod) ){
            setting_dict.sel_examperiod = 1
// ---  upload new setting
            const upload_dict = {selected_pk: {sel_examperiod: setting_dict.sel_examperiod}};
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);
        };
        if (![1, 2].includes(setting_dict.sel_examperiod) ){
            b_show_mod_message_html(loc.Please_select_examtype);

        } else {

// put examperiod in el_MASE_examperiod
            el_MASE_examperiod.innerText = (setting_dict.sel_examperiod === 1) ? loc.Central_exam :
                                    (setting_dict.sel_examperiod === 2) ? loc.Re_examination : null;

    //console.log("is_approve_mode", is_approve_mode) ;
    //console.log("is_submit_mode", is_submit_mode) ;
    //console.log("permit_dict.usergroup_list", permit_dict.usergroup_list) ;

// get list of auth_index of requsr
            const requsr_auth_list = [];
            if (permit_dict.usergroup_list.includes("auth1")){requsr_auth_list.push(1)};
            if (permit_dict.usergroup_list.includes("auth2")){requsr_auth_list.push(2)};

           // add examiner only when mode = approve_school
            if (is_approve_mode && is_school_mode){
                if (permit_dict.usergroup_list.includes("auth3")){requsr_auth_list.push(3)};
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

// show cluster only in school mode
            add_or_remove_class(el_MASE_cluster.parentNode, cls_hide, !is_school_mode);

// put info in mod_MASE_dict
            // modes are 'approve' 'submit_test' 'submit_save'
            mod_MASE_dict.mode = mode;
            mod_MASE_dict.step = 0;
            mod_MASE_dict.is_approve_mode = is_approve_mode;
            mod_MASE_dict.is_submit_mode = is_submit_mode;

            mod_MASE_dict.auth_index = setting_dict.sel_auth_index;

            mod_MASE_dict.may_test = true;
            mod_MASE_dict.test_is_ok = false;
            mod_MASE_dict.submit_is_ok = false;
            mod_MASE_dict.is_reset = false;

// get has_permit
            mod_MASE_dict.permit_admin = (permit_dict.requsr_role_admin) ?
                                        (is_approve_mode && permit_dict.permit_approve_exam) ||
                                        (is_submit_mode && permit_dict.permit_publish_exam) : false;
            mod_MASE_dict.permit_same_school = (permit_dict.requsr_same_school) ?
                                        (is_approve_mode && permit_dict.permit_approve_exam) ||
                                        (is_submit_mode && permit_dict.permit_submit_exam) : false;
            mod_MASE_dict.has_permit = mod_MASE_dict.permit_admin || mod_MASE_dict.permit_same_school;

            console.log("mod_MASE_dict.has_permit", mod_MASE_dict.has_permit) ;
            console.log("mod_MASE_dict.auth_index", mod_MASE_dict.auth_index) ;
            if (mod_MASE_dict.has_permit && mod_MASE_dict.auth_index){
                mod_MASE_dict.step = -1; // gets value 1 in MASE_Save

// --- get header_txt and subheader_txt
                const header_txt = (is_approve_mode) ? loc.Approve_exams :
                                 (mod_MASE_dict.permit_admin) ? loc.Publish_exams :
                                 (mod_MASE_dict.permit_same_school) ? loc.Submit_exams : "---";
                el_MASE_header.innerText = header_txt;

                // note: must use loc.MASE_info, not loc.MASE_info
                const subheader_txt = (is_approve_mode) ? loc.MASE_info.subheader_approve :
                                              (is_submit_mode) ?
                                              (mod_MASE_dict.permit_admin) ? loc.MASE_info.subheader_publish :
                                              (mod_MASE_dict.permit_same_school) ? loc.MASE_info.subheader_submit_exam
                                              : null : null;
                el_MASE_subheader.innerText = subheader_txt;

// get subject_text
                let subject_text = null;
                if(setting_dict.sel_subject_pk){
                    const data_dict = b_get_datadict_by_integer_from_datarows(subject_rows, "id", setting_dict.sel_subject_pk)
                    subject_text =  (data_dict.name) ? data_dict.name : "---"
                } else {
                    subject_text = "<" + loc.All_subjects + ">";
                }
                el_MASE_subject.innerText = subject_text;

    // ---  show info container and delete button only in approve mode

                //console.log("...........is_submit_mode", is_submit_mode) ;
                //add_or_remove_class(el_MASE_select_container, cls_hide, !is_approve_mode)
                add_or_remove_class(el_MASE_select_container, cls_hide, false)
                add_or_remove_class(el_MASE_btn_delete, cls_hide, is_submit_mode)

    // ---  reset el_MASE_input_verifcode
                el_MASE_input_verifcode.value = null;

// --- hide level textbox when not sel_dep_level_req
                add_or_remove_class(el_MASE_lvlbase.parentNode, cls_hide, !setting_dict.sel_dep_level_req)
                // updating happens after DatalistDownload, not here in MASE_Open,
                // to update el_MASE_lvlbase when MAG is opened immediately after changing level in SBR

// --- hide filter subject, level, cluster when submitting grade_exam
                add_or_remove_class(el_MASE_subj_lvl_cls_container, cls_hide, !is_approve_mode && !mod_MASE_dict.permit_admin)


// --- get approved_by
                if (el_MASE_approved_by_label){
                    let inner_text = (is_approve_mode) ? loc.Approved_by : (is_admin_mode) ? loc.Published_by : loc.Submitted_by;
                    el_MASE_approved_by_label.innerText = inner_text + ":"
                }
                if (el_MASE_approved_by){
                    el_MASE_approved_by.innerText = permit_dict.requsr_name;
                }

// --- fill selectbox auth_index
                if (el_MASE_auth_index){
                    // auth_list = [{value: 1, caption: 'Chairperson'}, {value: 3, caption: 'Examiner'} )
                    const auth_list = [];
                    const cpt_list = [null, loc.Chairperson, loc.Secretary, loc.Examiner, loc.Corrector];
                    for (let i = 0, auth_index; auth_index = requsr_auth_list[i]; i++) {
                        auth_list.push({value: auth_index, caption: cpt_list[auth_index]});
                    };
                    t_FillOptionsFromList(el_MASE_auth_index, auth_list, "value", "caption",
                        loc.Select_function, loc.No_functions_found, setting_dict.sel_auth_index);
                };

// ---  show info and hide loader
                // PR2021-01-21 debug 'display_hide' not working when class 'image_container' is in same div
                add_or_remove_class(el_MASE_info_container, cls_hide, false)
                add_or_remove_class(el_MASE_loader, cls_hide, true);

                MASE_Save ("save", true);  // true = is_test
                // this one is also in MASE_Save:
                // MASE_SetInfoboxesAndBtns();

                $("#id_mod_approve_exam").modal({backdrop: true});

// --- open modal
            };  // if (mod_MASE_dict.has_permit && mod_MASE_dict.auth_index)
        };  // if (![1,2].includes(setting_dict.sel_examperiod) )
    };  // MASE_Open

//=========  MASE_Save  ================
    function MASE_Save (save_mode, is_test) {
        console.log("===  MASE_Save  =====") ;
        console.log("save_mode", save_mode) ;
        console.log("permit_dict", permit_dict) ;

        // save_mode = 'save' or 'delete'
        // mod_MASE_dict.mode = 'approve' or 'submit'

        const has_permit = (permit_dict.requsr_role_admin && permit_dict.permit_approve_exam) ||
                            (permit_dict.requsr_role_admin && permit_dict.publish_exam) ||
                            (permit_dict.requsr_same_school && permit_dict.permit_approve_exam) ||
                            (permit_dict.requsr_same_school && permit_dict.submit_exam);
    console.log("has_permit", has_permit) ;

        if (has_permit) {

            mod_MASE_dict.is_reset = (save_mode === "delete");

            mod_MASE_dict.step += 1;

    console.log("mod_MASE_dict.is_approve_mode", mod_MASE_dict.is_approve_mode) ;
    console.log("mod_MASE_dict.is_submit_mode", mod_MASE_dict.is_submit_mode) ;
    console.log("mod_MASE_dict.step", mod_MASE_dict.step) ;

            //  upload_dict.modes are: 'approve_test', 'approve_save', 'approve_reset', 'submit_test', 'submit_save'
            let url_str = (permit_dict.requsr_role_admin) ? urls.url_approve_publish_exam : urls.url_approve_submit_grade_exam;
            const form_name = (permit_dict.requsr_role_admin) ? "ete_exam" : "grade_exam";
            const upload_dict = {form: form_name, now_arr: get_now_arr()};
            if (mod_MASE_dict.is_approve_mode){
                if (mod_MASE_dict.step === 0){
                    upload_dict.mode = "approve_test";
                } else if (mod_MASE_dict.step === 2){
                    upload_dict.mode = (mod_MASE_dict.is_reset) ? "approve_reset" : "approve_save";
                };
            } else if (mod_MASE_dict.is_submit_mode){
                if (mod_MASE_dict.step === 0){
                    upload_dict.mode = "submit_test";
                } else if (mod_MASE_dict.step === 2){
                    url_str = urls.url_send_email_verifcode;
                    upload_dict.mode = (permit_dict.requsr_role_admin) ? "publish_exam" : "submit_grade_exam";
                } else if (mod_MASE_dict.step === 4){
                    upload_dict.mode = "submit_save";

                    upload_dict.verificationcode = el_MASE_input_verifcode.value;
                    upload_dict.verificationkey = mod_MASE_dict.verificationkey;
                };
            };

    // ---  upload changes
            console.log("upload_dict", upload_dict) ;
            console.log("url_str", url_str) ;
            UploadChanges(upload_dict, url_str);

            MASE_SetInfoboxesAndBtns();

        };  // if (permit_dict.permit_approve_subject || permit_dict.permit_submit_subject)
// hide modal
        //if (!mod_MASE_dict.is_test){
        //    $("#id_mod_approve_studsubj").modal("hide");
        //}
    };  // MASE_Save

//=========  MASE_UploadAuthIndex  ================ PR2022-04-19
    function MASE_UploadAuthIndex (el_select) {
        //console.log("===  MASE_UploadAuthIndex  =====") ;

// ---  put new  auth_index in mod_MASE_dict and setting_dict
        mod_MASE_dict.auth_index = (Number(el_select.value)) ? Number(el_select.value) : null;
        setting_dict.sel_auth_index = mod_MASE_dict.auth_index;
        setting_dict.sel_auth_function = b_get_function_of_auth_index(loc, mod_MASE_dict.auth_index);
        //console.log( "setting_dict.sel_auth_function: ", setting_dict.sel_auth_function);

// ---  upload new setting
        const upload_dict = {selected_pk: {sel_auth_index: setting_dict.sel_auth_index}};
        b_UploadSettings (upload_dict, urls.url_usersetting_upload);

    }; // MASE_UploadAuthIndex

//========= MASE_UpdateFromResponse ============= PR2021-07-25
    function MASE_UpdateFromResponse(response) {
        console.log( " ==== MASE_UpdateFromResponse ====");
        console.log( "response", response);
        mod_MASE_dict.step += 1;

        mod_MASE_dict.test_is_ok = !!response.test_is_ok;
        mod_MASE_dict.saved_is_ok = !!response.saved_is_ok;

        mod_MASE_dict.verificationkey = response.verificationkey;
        mod_MASE_dict.verification_is_ok = !!response.verification_is_ok;

        console.log("mod_MASE_dict", mod_MASE_dict);

        // this is not working correctly yet, turned off for now PR2021-09-10
        // if false verfcode entered: try again
        if (mod_MASE_dict.step === 5 && !mod_MASE_dict.verification_is_ok ){
            //mod_MASE_dict.step = 3;
        };

        const count_dict = (response.approve_count_dict) ? response.approve_count_dict : {};

        mod_MASE_dict.has_already_approved = (!!count_dict.already_approved)
        mod_MASE_dict.submit_is_ok = (!!count_dict.saved)
        //mod_MASE_dict.has_already_published = (!!msg_dict.already_published)
        //mod_MASE_dict.has_saved = !!msg_dict.saved;

        MASE_SetInfoboxesAndBtns (response);

        //if ("updated_studsubj_approve_rows" in response){
        //    RefreshDataRows("studsubj", response.updated_studsubj_approve_rows, studsubj_rows, true);
        //}
        console.log("mod_MASE_dict.is_approve_mode", mod_MASE_dict.is_approve_mode);
        console.log("mod_MASE_dict.is_submit_mode", mod_MASE_dict.is_submit_mode);
        console.log("mod_MASE_dict.step", mod_MASE_dict.step);

// MASE_UpdateFromResponse refreshes the table, therefore no need for DatalistDownload
/* if ( (mod_MASE_dict.is_approve_mode && mod_MASE_dict.step === 3) || (mod_MASE_dict.is_submit_mode && mod_MASE_dict.step === 5)){
// ---  download page again
            //let new_setting = {page: 'page_exams'};
            //const datalist_request = {setting: new_setting,
            //    duo_subject_rows: {get: true},
            //    ete_exam_rows: {get: true},
            //    duo_exam_rows: {get: true},
           //     grade_exam_rows: {get: true},
            //    ntermentable_rows: {get: true},
            //    published_rows: {get: true}
            //};
            //DatalistDownload(datalist_request);
        };
*/
    };  // MASE_UpdateFromResponse

//=========  MASE_SetInfoboxesAndBtns  ================ PR2021-02-08
     function MASE_SetInfoboxesAndBtns(response) {
        console.log("===  MASE_SetInfoboxesAndBtns  =====") ;

        const step = mod_MASE_dict.step;
        const is_response = (!!response);

    console.log("......................step", step) ;
    console.log("is_response", is_response) ;
    console.log("test_is_ok", mod_MASE_dict.test_is_ok) ;
    console.log("saved_is_ok", mod_MASE_dict.saved_is_ok) ;
    console.log("is_approve_mode", mod_MASE_dict.is_approve_mode) ;
    console.log("verification_is_ok", mod_MASE_dict.verification_is_ok) ;

        // step 0: opening modal
        // step 1 + response : return after check
        // step 1 without response: save clicked approve or request verifcode
        // step 2 + response : return after approve or after email sent
        // step 2 without response: submit Exform wit hverifcode
        // step 3 + response: return from submit Exform

        // TODO is_reset
        const is_reset = mod_MASE_dict.is_reset;

//////////////////////////////////////////////////////////
// ---  select_container                                //
//////////////////////////////////////////////////////////
// ---  info_container, loader, info_verifcode and input_verifcode
        let msg_info_txt = null, show_loader = false;
        let show_info_request_verifcode = false, show_input_verifcode = false;
        let show_delete_btn = false;
        let disable_save_btn = false, save_btn_txt = null;

        if (response && response.approve_msg_html) {
            mod_MASE_dict.msg_html = response.approve_msg_html;
        };

    console.log("step", step);

        if (step === 0) {
            // step 0: when form opens and request to check is sent to server
            // tekst: 'The subjects of the candidates are checked'
            msg_info_txt = loc.MASE_info.checking_studsubj;
            show_loader = true;
        } else {
            if(mod_MASE_dict.is_approve_mode){
                // is approve
                if (step === 1) {
                // response with checked exams
                // msg_info_txt is in response
                    show_delete_btn = mod_MASE_dict.has_already_approved;
                    if (mod_MASE_dict.test_is_ok){
                        save_btn_txt = loc.MASE_info.Approve_exams;
                    };
                } else if (step === 2) {
                    // clicked on 'Approve'
                    // tekst: 'AWP is approving the subjects of the candidates'
                    msg_info_txt = loc.MASE_info.approving_exams;
                    show_loader = true;
                } else if (step === 3) {
                    // response 'approved'
                    // msg_info_txt is in response
                };
            } else {
                // is submit
                if (step === 1) {
                    // response with checked subjects
                    // msg_info_txt is in response
                    show_info_request_verifcode = mod_MASE_dict.test_is_ok;
                    if (mod_MASE_dict.test_is_ok){
                        save_btn_txt = loc.Request_verifcode;
                    };
                } else if (step === 2) {
                    // clicked on 'Request_verificationcode'
                    // tekst: 'AWP is sending an email with the verification code'
                    // show textbox with 'You need a 6 digit verification code to submit the Ex form'
                    msg_info_txt = loc.MASE_info.requesting_verifcode;
                    show_loader = true;
                } else if (step === 3) {
                    // response 'email sent'
                    // msg_info_txt is in response
                    show_info_request_verifcode = mod_MASE_dict.test_is_ok;
                    show_input_verifcode = true;
                    disable_save_btn = !el_MASE_input_verifcode.value;
                    save_btn_txt = loc.Submit_Ex1_form;
                } else if (step === 4) {
                    // clicked on 'Submit Ex form'
                    // msg_info_txt is in response
                    show_loader = true;
                } else if (step === 5) {
                    // response 'Exform submittes'
                    // msg_info_txt is in response
                }
            }  // if(mod_MASE_dict.is_approve_mode)
        }  // if (step === 0)

    //console.log("msg_info_txt", msg_info_txt) ;

        if (msg_info_txt){
            mod_MASE_dict.msg_html = "<div class='pt-2 border_bg_transparent'><p class='pb-2'>" +  msg_info_txt + " ...</p></div>";
        }

        const hide_info_container = (!msg_info_txt || show_loader)
        add_or_remove_class(el_MASE_info_container, cls_hide, hide_info_container)

        el_MASE_msg_container.innerHTML = mod_MASE_dict.msg_html;
        add_or_remove_class(el_MASE_msg_container, cls_hide, !mod_MASE_dict.msg_html)

        add_or_remove_class(el_MASE_loader, cls_hide, !show_loader)

        add_or_remove_class(el_MASE_info_request_verifcode, cls_hide, !show_info_request_verifcode);
        add_or_remove_class(el_MASE_input_verifcode.parentNode, cls_hide, !show_input_verifcode);

        if (el_MASE_info_request_msg1){
            el_MASE_info_request_msg1.innerText = loc.MASE_info.need_verifcode +
                ((permit_dict.requsr_role_admin) ? loc.MASE_info.to_publish_exams : loc.MASE_info.to_submit_exams);
        };

        if (show_input_verifcode){set_focus_on_el_with_timeout(el_MASE_input_verifcode, 150); };

// ---  show / hide delete btn
        add_or_remove_class(el_MASE_btn_delete, cls_hide, !show_delete_btn);

        console.log("save_btn_txt", save_btn_txt) ;
// - hide save button when there is no save_btn_txt
        add_or_remove_class(el_MASE_btn_save, cls_hide, !save_btn_txt)
// ---  disable save button till test is finished or input_verifcode has value
        el_MASE_btn_save.disabled = disable_save_btn;;
// ---  set innerText of save_btn
        el_MASE_btn_save.innerText = save_btn_txt;

// ---  set innerText of cancel_btn
        el_MASE_btn_cancel.innerText = (step === 0 || !!save_btn_txt) ? loc.Cancel : loc.Close;

     } //  MASE_SetInfoboxesAndBtns

//=========  MASE_InputVerifcode  ================ PR2021-07-30
     function MASE_InputVerifcode(el_input, event_key) {
        //console.log("===  MASE_InputVerifcode  =====") ;
        //console.log("event_key", event_key) ;

        // enable save btn when el_input has value
        const disable_save_btn = !el_input.value;
        //console.log("disable_save_btn", disable_save_btn) ;
        el_MASE_btn_save.disabled = disable_save_btn;

        if(!disable_save_btn && event_key && event_key === "Enter"){

            // hide info box
            el_MASE_info_container

            MASE_Save("save")
        }
     };  // MASE_InputVerifcode

/////////////////////////////////////////

// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++

//=========  ModConfirm_PartexCheck_Open  ================ PR2022-01-14
    function ModConfirm_PartexCheck_Open() {
        console.log(" -----  ModConfirm_PartexCheck_Open   ----")

    // ---  create mod_dict
        mod_dict = {mode: "remove_partex"};

        const data_dict = mod_MEX_dict.partex_dict[mod_MEX_dict.sel_partex_pk];
        const partex_name = (data_dict) ? data_dict.name : "-";

        const msg_html = ["<p class=\"p-2\">", loc.All_partex_willbe_removed, "<br>",
                            loc.except_for_selected_exam, " '", partex_name, "'.",
                            "</p><p class=\"p-2\">", loc.Do_you_want_to_continue, "</p>"].join("")
        el_confirm_msg_container.innerHTML = msg_html;

        el_confirm_header.innerText = loc.Remove_partial_exams;
        el_confirm_loader.classList.add(cls_visible_hide);
        el_confirm_msg_container.className = "";
        el_confirm_btn_save.innerText = loc.Yes_remove;
        add_or_remove_class(el_confirm_btn_save, "btn-outline-secondary", true, "btn-primary")

        el_confirm_btn_cancel.innerText = loc.No_cancel;

// set focus to cancel button
        setTimeout(function (){
            el_confirm_btn_cancel.focus();
        }, 500);

// show modal
        $("#id_mod_confirm").modal({backdrop: true});

    };  // ModConfirm_PartexCheck_Open


//=========  ModConfirm_calculate_grades_Open  ================ PR2022-05-20
    function ModConfirm_calculate_grades_Open() {
            console.log(" -----  ModConfirm_calculate_grades_Open   ----")

        // values of mode are : "delete", 'json', 'copy', 'save'
        // values of table are : "ete_exam" "duo_exam" 'duo_grade_exam'

        mod_dict = {mode: "calc_grades"};
        if (permit_dict.permit_crud && permit_dict.requsr_role_admin && permit_dict.requsr_country_pk === 1 ) {

            let hide_save_btn = false, has_selected_item = false;

    // ---  get header_text
            const header_text = loc.Calculate_grades;

            const tblName = get_tblName_from_selectedBtn();
            const selected_pk = setting_dict.sel_duo_exam_pk;

            mod_dict.table = tblName;

console.log("tblName", tblName );
console.log("selected_pk", selected_pk );

// ---  lookup data_dict in exam_rows
            const data_rows = (tblName === "ete_exam") ? ete_exam_rows :
                              (tblName === "duo_exam") ? duo_exam_rows : null;
            const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", selected_pk);
            const data_dict = (!isEmpty(found_dict)) ? found_dict : null;
console.log("data_dict", data_dict);

    // ---  create mod_dict
            has_selected_item = (!isEmpty(data_dict));
            if(has_selected_item){
                mod_dict.examyear_pk = setting_dict.sel_examyear_pk;
                mod_dict.depbase_pk = setting_dict.sel_depbase_pk;
                    mod_dict.mapid = data_dict.mapid;
                    mod_dict.exam_pk = data_dict.id;
                if (tblName === "ete_exam") {
                    mod_dict.subject_pk = data_dict.subj_id;
                    mod_dict.subj_name = data_dictdata_dict.subj_name;
                } else  if (tblName === "duo_exam") {
                    mod_dict.department_id = data_dict.department_id;
                    mod_dict.subject_pk = data_dict.subj_id;
                    mod_dict.subj_name = data_dict.subj_name;
                };
            };
//console.log("mod_dict", mod_dict);
    // ---  put text in modal form

            const msg_list = [];
            if(!has_selected_item){
                msg_list.push( ["<p class='pb-2'>", loc.No_exam_selected, "</p>"].join("") );
                hide_save_btn = true;
            } else {
                msg_list.push( ["<p class='pb-2'>", loc.Calculate_grades_01, "</p><p>",
                                "&emsp;", data_dict.exam_name, "<br>",
                                "&emsp;", data_dict.ntb_omschrijving, "</p><p class='py-2'>",
                                loc.Calculate_grades_02, "</p><p>",
                                loc.Do_you_want_to_continue, "</p>"
                                ].join(""));
            };
            const msg_html = msg_list.join("");

            el_confirm_loader.classList.add(cls_visible_hide);

            const btn_save_txt = (has_selected_item) ? loc.Yes_calculate : loc.OK;
            const btn_cancel_txt = (has_selected_item) ? loc.No_cancel : loc.Close;

            el_confirm_header.innerText = header_text;

            el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");
            el_confirm_msg_container.innerHTML = msg_html;

            el_confirm_btn_save.innerText = btn_save_txt;
            add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", false, "btn-primary");
            add_or_remove_class (el_confirm_btn_save, cls_hide, hide_save_btn);
            el_confirm_btn_cancel.innerText = btn_cancel_txt;


    // set focus to cancel button
            setTimeout(function (){
                el_confirm_btn_cancel.focus();
            }, 500);

    // show modal
            $("#id_mod_confirm").modal({backdrop: true});


        };  //  if (permit_dict.permit_crud && permit_dict.requsr_role_admin )

    };  // ModConfirm_calculate_grades_Open

//=========  ModConfirm_LinkDuo_exam_grade_Open  ================ PR2022-05-19
    function ModConfirm_LinkDuo_exam_grade_Open() {
            console.log(" -----  ModConfirm_LinkDuo_exam_grade_Open   ----")

        // values of mode are : "delete", 'json', 'copy', 'save'
        // values of table are : "ete_exam" "duo_exam" 'duo_grade_exam'

        mod_dict = {mode: "link_duo_exam_grade"};
        if (permit_dict.permit_crud && permit_dict.requsr_role_admin && permit_dict.requsr_country_pk === 1 ) {

            let hide_save_btn = false, has_selected_item = false;

    // ---  get header_text
            const header_text = loc.Link_DUO_to_grade_exam;

            const tblName = "duo_exam";
            const selected_pk = setting_dict.sel_duo_exam_pk;

            mod_dict.table = tblName;

console.log("tblName", tblName );
console.log("selected_pk", selected_pk );

// ---  lookup exam_dict in exam_rows
            const [index, found_dict, compare] = b_recursive_integer_lookup(duo_exam_rows, "id", selected_pk);
            const exam_dict = (!isEmpty(found_dict)) ? found_dict : null;
console.log("exam_dict", exam_dict);

    // ---  create mod_dict
            has_selected_item = (!isEmpty(exam_dict));
            if(has_selected_item){
                mod_dict.examyear_pk = setting_dict.sel_examyear_pk;
                mod_dict.depbase_pk = setting_dict.sel_depbase_pk;
                    mod_dict.mapid = exam_dict.mapid;
                    mod_dict.exam_pk = exam_dict.id;
                if (tblName === "ete_exam") {
                    mod_dict.subject_pk = exam_dict.subj_id;
                    mod_dict.subj_name = exam_dict.subj_name;
                } else  if (tblName === "duo_exam") {
                    mod_dict.department_id = exam_dict.department_id;
                    mod_dict.subject_pk = exam_dict.subj_id;
                    mod_dict.subj_name = exam_dict.subj_name;
                };
            };
//console.log("mod_dict", mod_dict);
    // ---  put text in modal form

            const msg_list = [];
            if(!has_selected_item){
                msg_list.push( ["<p class='pb-2'>", loc.No_exam_selected, "</p>"].join("") );
                hide_save_btn = true;
            } else {
                msg_list.push( ["<p class='pb-2'>", loc.Link_DUO_to_grade_exam_01, "</p><p>",
                                "&emsp;", exam_dict.exam_name, "<br>",
                                "&emsp;", exam_dict.ntb_omschrijving, "</p><p class='py-2'>",
                                loc.Link_DUO_to_grade_exam_02, "</p><p>",
                                loc.Do_you_want_to_continue, "</p>"
                                ].join(""));
            };
            const msg_html = msg_list.join("");

            el_confirm_loader.classList.add(cls_visible_hide);

            const btn_save_txt = (has_selected_item) ? loc.Yes_link : loc.OK;
            const btn_cancel_txt = (has_selected_item) ? loc.No_cancel : loc.Close;

            el_confirm_header.innerText = header_text;

            el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");
            el_confirm_msg_container.innerHTML = msg_html;

            el_confirm_btn_save.innerText = btn_save_txt;
            add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", false, "btn-primary");
            add_or_remove_class (el_confirm_btn_save, cls_hide, hide_save_btn);
            el_confirm_btn_cancel.innerText = btn_cancel_txt;


    // set focus to cancel button
            setTimeout(function (){
                el_confirm_btn_cancel.focus();
            }, 500);

    // show modal
            $("#id_mod_confirm").modal({backdrop: true});

        };  //  if (permit_dict.permit_crud && permit_dict.requsr_role_admin )

    };  // ModConfirm_LinkDuo_exam_grade_Open

//=========  ModConfirm_Cesuur_Open  ================ PR2022-05-19
    function ModConfirm_Cesuur_Open(el_input) {
            console.log(" -----  ModConfirm_Cesuur_Open   ----")
        if (permit_dict.permit_crud && permit_dict.requsr_role_admin && permit_dict.requsr_country_pk === 1 ) {
            let hide_save_btn = false, has_selected_item = false;

    // ---  put text in modal form
            const msg_list = [];
            if (mod_dict.cesuur){
                msg_list.push( ["<p class='pb-2'>", loc.Enter_cesuur_01,
                                (mod_dict.cesuur) ? mod_dict.cesuur : '-',
                                loc.Enter_cesuur_02, "</p><p>",
                                "&emsp;", mod_dict.exam_name, "</p><p class='py-2'>",
                                loc.Enter_cesuur_03, "</p>"].join("")
                            );
            } else {
                msg_list.push( ["<p class='pb-2'>", loc.Enter_cesuur_01,
                                (mod_dict.cesuur) ? mod_dict.cesuur : '-',
                                loc.Enter_cesuur_02, "</p><p>",
                                "&emsp;", mod_dict.exam_name, "</p><p class='py-2'>",
                                loc.Enter_cesuur_03, "</p>"].join("")
                            );
            }
            msg_list.push("<p>" + loc.Do_you_want_to_continue + "</p>")
            const msg_html = msg_list.join("");

            const header_text =loc.Enter_cesuur;
            const btn_cancel_txt = loc.No_cancel;
            const btn_save_txt = loc.Yes_save;

            el_confirm_header.innerText = header_text;
            el_confirm_loader.classList.add(cls_visible_hide);
            el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");
            el_confirm_msg_container.innerHTML = msg_html;

            el_confirm_btn_save.innerText = btn_save_txt;
            add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", false, "btn-primary");
            add_or_remove_class (el_confirm_btn_save, cls_hide, false);
            el_confirm_btn_cancel.innerText = btn_cancel_txt;

    // set focus to cancel button
            setTimeout(function (){
                el_confirm_btn_cancel.focus();
            }, 500);

    // show modal
            $("#id_mod_confirm").modal({backdrop: true})

        };
    };  // ModConfirm_Cesuur_Open


//=========  On close ModConfirm  ================ PR2022-05-19
    $('#id_mod_confirm').on('hide.bs.modal', function (e) {
        try {
            if (mod_dict.mode === "cesuur" && !mod_dict.dont_rest_input_value)
                if (mod_dict.el_input ){
                    mod_dict.el_input.value = mod_dict.old_value
                }
         } catch (error) {
        }
    });

//=========  ModConfirmOpen  ================ PR2021-05-06
    function ModConfirmOpen(table, mode, el_input) {
        console.log(" -----  ModConfirmOpen   ----")
        //console.log("mode", mode)
        console.log("table", table)
        // values of mode are : "delete", 'json', 'copy', 'save' 'undo_published' 'undo_submitted'
        // values of table are : "ete_exam" "duo_exam" 'duo_grade_exam' "results"
        // TODO print_exam not in use: remove, add 'publish'

        const is_delete = (mode === "delete");
        const is_json = (mode === "json");
        const is_copy = (mode === "copy");
        const is_undo_published = (mode === "undo_published");
        mod_dict = {mode: mode};

        let hide_save_btn = false, has_selected_item = false;
        let msg_html = "";
        let header_text = null;
        let btn_save_txt = loc.Save, btn_cancel_txt = loc.Cancel;

        if (permit_dict.permit_crud && permit_dict.requsr_same_school) {
            header_text = loc.Remove_submitted_from_exam;

            let tblName = null, selected_pk = null;
            // tblRow is undefined when clicked on delete btn in submenu btn or form (no inactive btn)
            const tblRow = t_get_tablerow_selected(el_input);
            if(tblRow){
                // not in use
                tblName = get_attr_from_el(tblRow, "data-table")
                selected_pk = get_attr_from_el(tblRow, "data-pk")
            } else {
                tblName = table;
                selected_pk = setting_dict.sel_grade_exam_pk;
            }
            mod_dict.table = tblName;

// ---  lookup data_dict in data_rows
            const data_rows = grade_exam_rows;
            const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", selected_pk);
            const data_dict = (!isEmpty(found_dict)) ? found_dict : null;

    // ---  create mod_dict
            has_selected_item = (!isEmpty(data_dict));
            if(has_selected_item){
                mod_dict.examyear_pk = setting_dict.sel_examyear_pk;
                mod_dict.depbase_pk = setting_dict.sel_depbase_pk;
                    mod_dict.mapid = data_dict.mapid;
                    mod_dict.grade_pk = data_dict.id;

                    mod_dict.subject_pk = data_dict.subj_id;
                    mod_dict.subj_name = data_dict.subj_name;
                    mod_dict.ceex_name = data_dict.ceex_name;
                    mod_dict.fullname = data_dict.fullname;
                    mod_dict.student_pk = data_dict.student_id;
            };
    //console.log("mod_dict", mod_dict);
        // ---  put text in modal form
            if(!has_selected_item){
                msg_html = ["<p class='pb-2'>", loc.No_exam_selected, "</p>"].join("");;
                hide_save_btn = true;
            } else {
                msg_html = ["<p class='pb-2'>", loc.Submitted_will_be_removed_from_exam, "</p><p>",
                        "&emsp;", mod_dict.ceex_name, "<br>",
                        "&emsp;", mod_dict.subj_name, "<br>",
                        "&emsp;", mod_dict.fullname, "</p><p class='py-2'>",
                        loc.Do_you_want_to_continue, "</p>"].join("");;
            };

            el_confirm_loader.classList.add(cls_visible_hide);

            btn_save_txt = !has_selected_item ? loc.OK : loc.Yes_remove ;
            btn_cancel_txt = (has_selected_item) ? loc.No_cancel : loc.Close;

            el_confirm_header.innerText = header_text;

            el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");
            el_confirm_msg_container.innerHTML = msg_html;

            el_confirm_btn_save.innerText = btn_save_txt;
            add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", is_delete, "btn-primary");
            add_or_remove_class (el_confirm_btn_save, cls_hide, hide_save_btn);
            el_confirm_btn_cancel.innerText = btn_cancel_txt;

    // set focus to cancel button
            setTimeout(function (){
                el_confirm_btn_cancel.focus();
            }, 500);

    // show modal
            $("#id_mod_confirm").modal({backdrop: true});

        } else if (permit_dict.permit_crud && permit_dict.requsr_role_admin && permit_dict.requsr_country_pk === 1 ) {

    // ---  get header_text
            if (is_json){
                header_text = loc.Download_JSON;
                if (loc.examperiod_caption && setting_dict.sel_examperiod) {
                    header_text += " - " + loc.examperiod_caption[setting_dict.sel_examperiod];
                }
        // ---  put text in modal form
                msg_html = ["<p class='pb-2'>", loc.JSON_will_be_downloaded, "</p><p class='py-2'>",
                            loc.Do_you_want_to_continue, "</p>"].join("");

    // +++  create href and put it in save button PR2021-05-06
                btn_save_txt = loc.Yes_download;
                btn_cancel_txt = loc.No_cancel;

    // +++  create href and put it inel_modconfirm_link
                const el_modconfirm_link = document.getElementById("id_modconfirm_link");
                if (el_modconfirm_link) {
                    el_modconfirm_link.setAttribute("href", urls.url_exam_download_exam_json);
                };
                btn_cancel_txt = loc.No_cancel;

            } else if(is_delete || is_copy || is_undo_published){
                header_text = (is_undo_published) ? loc.Remove_published_from_exam :
                              (is_copy) ? loc.Copy_exam :
                              (table === "ete_exam") ? loc.Delete_exam : loc.Unlink_DUO_exam;

                let tblName = null, selected_pk = null;
                // tblRow is undefined when clicked on delete btn in submenu btn or form (no inactive btn)
                const tblRow = t_get_tablerow_selected(el_input);
                if(tblRow){
                    tblName = get_attr_from_el(tblRow, "data-table")
                    selected_pk = get_attr_from_el(tblRow, "data-pk")
                } else {
                    tblName = table;
                    selected_pk = (tblName === "ete_exam") ? setting_dict.sel_exam_pk : (tblName === "duo_exam") ? setting_dict.sel_duo_exam_pk : null;;
                }
                mod_dict.table = tblName;

    // ---  lookup exam_dict in exam_rows
                const data_rows = (tblName === "duo_exam") ? duo_exam_rows : ete_exam_rows;
                const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", selected_pk);
                const exam_dict = (!isEmpty(found_dict)) ? found_dict : null;

        // ---  create mod_dict
                has_selected_item = (!isEmpty(exam_dict));
                if(has_selected_item){
                    mod_dict.examyear_pk = setting_dict.sel_examyear_pk;
                    mod_dict.depbase_pk = setting_dict.sel_depbase_pk;
                        mod_dict.mapid = exam_dict.mapid;
                        mod_dict.exam_pk = exam_dict.id;
                    if (tblName === "ete_exam") {
                        mod_dict.subject_pk = exam_dict.subj_id;
                        mod_dict.subj_name = exam_dict.subj_name;
                        mod_dict.exam_name = exam_dict.exam_name;
                    } else  if (tblName === "duo_exam") {
                        mod_dict.department_id = exam_dict.department_id;
                        mod_dict.subject_pk = exam_dict.subj_id;
                        mod_dict.subj_name = exam_dict.subj_name;
                        mod_dict.exam_name = exam_dict.exam_name;
                    };
                };
    //console.log("mod_dict", mod_dict);
        // ---  put text in modal form
                if(!has_selected_item){
                    msg_html = ["<p class='pb-2'>", loc.No_exam_selected, "</p>"].join("");;
                    hide_save_btn = true;
                } else {
                    if (is_undo_published){
                        msg_html = ["<p class='pb-2'>", loc.Published_will_be_removed_from_exam, "</p><p>",
                                "&emsp;", mod_dict.exam_name, "</p><p class='py-2'>",
                                loc.Do_you_want_to_continue, "</p>"].join("");;
                    } else {
                        const will_be_deleted_copied_txt = (is_copy) ? loc.will_be_copied : (tblName === "duo_exam") ? loc.will_be_unlinked : loc.will_be_deleted;

                        msg_html = ["<p class='pb-2'>", loc.Exam, " '", mod_dict.subj_name, "'",
                                    will_be_deleted_copied_txt, "</p><p class='py-2'>",
                                loc.Do_you_want_to_continue, "</p>"].join("");;
                    };
                };

                el_confirm_loader.classList.add(cls_visible_hide);

                btn_save_txt = !has_selected_item ? loc.OK :
                                (is_copy) ? loc.Yes_copy :
                                (is_undo_published) ? loc.Yes_remove :
                                (tblName === "duo_exam") ? loc.Yes_unlink : loc.Yes_delete;
                btn_cancel_txt = (has_selected_item) ? loc.No_cancel : loc.Close;

            };  //  if(is_delete)

            el_confirm_header.innerText = header_text;

            el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");
            el_confirm_msg_container.innerHTML = msg_html;

            el_confirm_btn_save.innerText = btn_save_txt;
            add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", is_delete, "btn-primary");
            add_or_remove_class (el_confirm_btn_save, cls_hide, hide_save_btn);
            el_confirm_btn_cancel.innerText = btn_cancel_txt;


    // set focus to cancel button
            setTimeout(function (){
                el_confirm_btn_cancel.focus();
            }, 500);

    // show modal
            $("#id_mod_confirm").modal({backdrop: true});

        };  //  if (permit_dict.permit_crud && permit_dict.requsr_role_admin )

    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2019-06-23
    function ModConfirmSave() {
        console.log(" --- ModConfirmSave --- ");
        console.log("mod_dict: ", mod_dict);


        if (permit_dict.permit_crud && permit_dict.requsr_same_school) {

            console.log("mod_dict.mode: ", mod_dict.mode);
            if (mod_dict.mode === "undo_submitted"){
                const upload_dict = { table: "grades",
                                       mode: "update",
                                       grade_pk: mod_dict.grade_pk,
                                       examyear_pk: mod_dict.examyear_pk,
                                       subject_pk: mod_dict.subject_pk,
                                       student_pk: mod_dict.student_pk,
                                       ce_exam_published: null,
                                       return_grades_with_exam: true
                                    };
        console.log("upload_dict: ", upload_dict);

                UploadChanges(upload_dict, urls.url_grade_upload);
            };
        } else if (permit_dict.permit_crud && permit_dict.requsr_role_admin && permit_dict.requsr_country_pk === 1 ) {

        console.log("mod_dict.mode: ", mod_dict.mode);
            if (mod_dict.mode === "undo_published"){
                const upload_dict = { table: "ete_exam",
                                       mode: "update",
                                       exam_pk: mod_dict.exam_pk,
                                       examyear_pk: mod_dict.examyear_pk,
                                       subject_pk: mod_dict.subject_pk,
                                       published: null
                                    };
        console.log("upload_dict: ", upload_dict);
                UploadChanges(upload_dict, urls.url_exam_upload);

            } else if (mod_dict.mode === "link_duo_exam_grade"){

            // mod_dict gets value in HandleInputChanged
                const upload_dict = { table: "ete_exam",
                                       mode: "update",
                                       exam_pk: mod_dict.exam_pk,
                                       examyear_pk: mod_dict.examyear_pk,
                                       subject_pk: mod_dict.subject_pk,
                                       cesuur: mod_dict.cesuur // cesuur is string, will be converted on server
                                    };

                UploadChanges(upload_dict, urls.url_exam_upload);
                // mod_dict.save_value prevents putting back the old value in el_input
                mod_dict.dont_rest_input_value = true;

            } else if (mod_dict.mode === "cesuur") {
                // must loose focus, otherwise green / red border won't show
                //el_input.blur();
                //const el_loader =  document.getElementById("id_MSTUD_loader");
               // el_loader.classList.remove(cls_visible_hide);

        // ---  upload changes

            // mod_dict gets value in HandleInputChanged
                const upload_dict = { table: "ete_exam",
                                       mode: "update",
                                       exam_pk: mod_dict.exam_pk,
                                       examyear_pk: mod_dict.examyear_pk,
                                       subject_pk: mod_dict.subject_pk,
                                       cesuur: mod_dict.cesuur // cesuur is string, will be converted on server
                                    };

                UploadChanges(upload_dict, urls.url_exam_upload);
                // mod_dict.save_value prevents putting back the old value in el_input
                mod_dict.dont_rest_input_value = true;

            } else if (mod_dict.mode === "json") {
                const el_modconfirm_link = document.getElementById("id_modconfirm_link");
                if (el_modconfirm_link) {
                    el_modconfirm_link.click();
                };
            } else if (mod_dict.mode === "copy") {
        // ---  Upload Changes
                let upload_dict = { table:mod_dict.table,
                                    mode: mod_dict.mode,
                                    exam_pk: mod_dict.exam_pk,
                                    examyear_pk: mod_dict.examyear_pk,
                                    subject_pk: mod_dict.subject_pk,
                                    };
                UploadChanges(upload_dict, urls.url_exam_copy);

            } else if (mod_dict.mode === "delete") {

    // ---  when delete: make tblRow red, before uploading
                let tblRow = document.getElementById(mod_dict.mapid);
                if (tblRow && mod_dict.mode === "delete"){
                    ShowClassWithTimeout(tblRow, "tsa_tr_error");
                }

        console.log("tblRow: ", tblRow);
        console.log("mod_dict.mapid: ", mod_dict.mapid);

        // ---  Upload Changes
                const url_str = (mod_dict.table === "duo_exam") ? urls.url_duo_exam_upload : urls.url_exam_upload;
                let upload_dict = { mode: mod_dict.mode};
                if (mod_dict.table === "duo_exam") {
                    upload_dict.exam_pk = mod_dict.exam_pk;
                    upload_dict.examyear_pk = mod_dict.examyear_pk;
                    upload_dict.depbase_pk = mod_dict.depbase_pk;
                    upload_dict.subject_pk = mod_dict.subject_pk;
                } else {
                    upload_dict.exam_pk = mod_dict.exam_pk;
                    upload_dict.examyear_pk = mod_dict.examyear_pk;
                    upload_dict.depbase_pk = mod_dict.depbase_pk;
                    upload_dict.subject_pk = mod_dict.subject_pk;
                };
        console.log("upload_dict: ", upload_dict);

                UploadChanges(upload_dict, url_str);
            };
        };
// ---  hide modal
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
            el_confirm_msg01.innerText = msg01_txt;
            el_confirm_msg02.innerText = msg02_txt;
            el_confirm_msg03.innerText = msg03_txt;
            el_confirm_btn_cancel.innerText = loc.Close
            el_confirm_btn_save.classList.add(cls_hide);
        } else {
        // hide mod_confirm when no message
            $("#id_mod_confirm").modal("hide");
        }
    }  // ModConfirmResponse

//=========  ModMessageClose  ================ PR2020-12-20 PR2022-05-07
    function ModMessageClose() {
        console.log(" --- ModMessageClose --- ");
        // el_focus is stored in mod_dict
        if (mod_dict.el_focus){
            set_focus_on_el_with_timeout(mod_dict.el_focus, 150 );
        };
    }  // ModMessageClose

//>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

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
            success: function (data) {
                // your callback here
            },
            error: function (error) {
                // handle error
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

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL SELECT EXAMYEAR OR DEPARTMENT ++++++++++++++++++++
// functions are in table.js, except for MSED_Response

//=========  MSED_Response  ================ PR2020-12-18 PR2021-05-10 PR2022-04-11
    function MSED_Response(new_setting) {
        //console.log( "===== MSED_Response ========= ");

// ---  upload new selected_pk
        new_setting.page = setting_dict.sel_page;
// also retrieve the tables that have been changed because of the change in examyear / dep
        // PR2022-04-07 debug: when changing dep, levels must also be retrieved again. Added: level_rows: {cur_dep_only: true},
        const datalist_request = {
                setting: new_setting,
                level_rows: {cur_dep_only: true},
                subject_rows: {etenorm_only: true, cur_dep_only: true},
                duo_subject_rows: {get: true},
                ete_exam_rows: {get: true},
                duo_exam_rows: {get: true},
                grade_exam_rows: {get: true},
                grade_exam_result_rows: {get: true},
                ntermentable_rows: {get: true},
                published_rows: {get: true}
            };
        DatalistDownload(datalist_request);

    }  // MSED_Response

//=========  MSSSS_Response  ================ PR2021-01-23 PR2021-02-05 PR2021-07-26
    function MSSSS_Response(tblName, selected_dict, selected_pk) {
        console.log( "===== MSSSS_Response ========= ");
        console.log( "selected_dict", selected_dict);
        console.log( "selected_pk", selected_pk);
        console.log( "tblName", tblName);

    // ---  upload new setting
        if(selected_pk === -1) { selected_pk = null};

        if (tblName === "school") {
        // Note: when tblName = school: selected_pk = schoolbase_pk

// ---  upload new setting and refresh page
        // PR2022-04-07 debug: when changing dep, levels must also be retrieved again. Added: level_rows: {cur_dep_only: true},
        const datalist_request = {
                setting: {page: "page_exams",
                        sel_schoolbase_pk: selected_pk
                    },
                school_rows: {get: true},
                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},
                subject_rows: {etenorm_only: true, cur_dep_only: true},
                duo_subject_rows: {get: true},
                ete_exam_rows: {get: true},
                duo_exam_rows: {get: true},
                grade_exam_rows: {get: true},
                grade_exam_result_rows: {get: true},
                ntermentable_rows: {get: true},
                published_rows: {get: true}
            };

            DatalistDownload(datalist_request);
        } else if (tblName === "subject") {

// -- lookup selected.subject_pk in subject_rows and get sel_subject_dict
            // only when modal is open - not necessary, is only called when modal is open
            //const modal_MEXQ_is_open = (!!el_MEXQ_questions && el_modal.classList.contains("show"));

            MEX_get_subject(selected_pk);

// update text in select subject div ( not when entering answers)
            if (el_MEXQ_select_subject) {
                el_MEXQ_select_subject.innerText = (mod_MEX_dict.subject_pk) ?
                mod_MEX_dict.subject_name : loc.Click_here_to_select_subject;
            };
// also update text in header 2
            MEX_set_headertext2_subject();

    // --- fill select table
            MEXQ_FillSelectTableLevel()

            MEXQ_validate_and_disable();

// ---  upload new setting
            const upload_dict = {selected_pk: {sel_subject_pk: selected_pk, sel_student_pk: null}};
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);

        } else if (tblName === "student") {

            const selected_pk_dict = {sel_student_pk: selected_pk};
            selected_pk_dict["sel_" + tblName + "_pk"] = selected_pk;

            b_UploadSettings ({selected_pk: selected_pk_dict}, urls.url_usersetting_upload);
        // --- update header text - comes after MSSSS_display_in_sbr
            UpdateHeaderLeftRight();

            setting_dict.sel_student_pk = selected_pk;
            //setting_dict.sel_student_name = selected_name;
    // reset selected subject when student is selected, in setting_dict
            if(selected_pk){
                selected_pk_dict.sel_subject_pk = null;
                setting_dict.sel_subject_pk = null;
                new_selected_btn = "grade_by_student";
            };
        };
    };  // MSSSS_Response


//=========  MSSSubjStud_Response  ================ PR2022-02-01
    function MSSSubjStud_Response(mode, selected_dict, sel_pk_int) {
        console.log( "===== MSSSubjStud_Response ========= ");
        console.log( "sel_pk_int", sel_pk_int, typeof sel_pk_int);
        console.log( "selected_dict", selected_dict);
        console.log( "mode", mode);
        // mode = "subject" or "student"

// - put new value in setting_dict


        // reset sel_student_pk when selecting sel_subject_pk and vice versa
        if(sel_pk_int === -1) { sel_pk_int = null};

        const upload_pk_dict = {};
        if (mode === "subject") {
            setting_dict.sel_subject_pk = sel_pk_int;
            setting_dict.sel_subject_name = (selected_dict && selected_dict.name) ? selected_dict.name : null;
            if(sel_pk_int) {
                setting_dict.sel_cluster_pk = null;
                setting_dict.sel_cluster_name = null;
                setting_dict.sel_student_pk = null;
                setting_dict.sel_student_name = null;
            };

            upload_pk_dict.sel_subject_pk = sel_pk_int;
            if(sel_pk_int) {
                upload_pk_dict.sel_cluster_pk = null;
                upload_pk_dict.sel_student_pk = null;
            };

        } else if (mode === "cluster") {
            setting_dict.sel_cluster_pk = sel_pk_int;
            setting_dict.sel_cluster_name = (selected_dict && selected_dict.name) ? selected_dict.name : null;

            // when selecting cluster: also set subject to the subject of this cluster
            setting_dict.sel_subject_pk =  (selected_dict && selected_dict.subject_id) ? selected_dict.subject_id : null;
            setting_dict.sel_subject_name = (selected_dict && selected_dict.subj_name) ? selected_dict.subj_name : null;
            setting_dict.sel_student_pk = null;
            setting_dict.sel_student_name = null;

            upload_pk_dict.sel_cluster_pk = sel_pk_int;
            if(sel_pk_int) {
                upload_pk_dict.sel_subject_pk = selected_dict.subject_id;
                upload_pk_dict.sel_student_pk = null;
            };

        } else if (mode === "student") {
            setting_dict.sel_student_pk = sel_pk_int;
            setting_dict.sel_student_name = (selected_dict && selected_dict.fullname) ? selected_dict.fullname : null;

            setting_dict.sel_subject_pk = null;
            setting_dict.sel_subject_name = null;
            setting_dict.sel_cluster_pk = null;
            setting_dict.sel_cluster_name = null;

            upload_pk_dict.sel_student_pk = sel_pk_int;
            if(sel_pk_int) {
                upload_pk_dict.sel_subject_pk = null;
                setting_dict.sel_cluster_pk = null;
            };
        };
    //console.log("setting_dict", setting_dict);

        t_MSSSS_display_in_sbr("student", upload_pk_dict.sel_student_pk);
        t_MSSSS_display_in_sbr("subject", upload_pk_dict.sel_subject_pk);

// ---  upload new setting
        const upload_dict = {selected_pk: upload_pk_dict};
    //console.log("upload_dict", upload_dict);
        b_UploadSettings (upload_dict, urls.url_usersetting_upload);

        FillTblRows();
    };  // MSSSubjStud_Response

//========= MSSSS_display_in_sbr_reset  ====================================
    function MSSSS_display_in_sbr_reset() {
        //console.log( "===== MSSSS_display_in_sbr_reset  ========= ");

        t_MSSSS_display_in_sbr("subject");
        t_MSSSS_display_in_sbr("student");
        t_MSSSS_display_in_sbr("cluster");

    }; // MSSSS_display_in_sbr_reset

//========= get_tblName_from_selectedBtn  ======== // PR2022-02-26
    function get_tblName_from_selectedBtn() {
        return (["btn_ep_01", "btn_reex"].includes(selected_btn)) ? "grades" :
                   (selected_btn === "btn_ete_exams") ? "ete_exam" :
                   (selected_btn === "btn_duo_exams") ? "duo_exam" :
                   (selected_btn === "btn_ntermen") ? "ntermen" :
                   (selected_btn === "btn_results") ? "results" : null ;
    };

//========= get_datarows_from_tblName  ======== // PR2022-02-26
    function get_datarows_from_tblName(tblName) {
        return (tblName === "grades") ?  grade_exam_rows :
                            (tblName === "ete_exam") ? ete_exam_rows :
                            (tblName === "duo_exam") ? duo_exam_rows :
                            (tblName === "ntermen") ? ntermentable_rows :
                            (tblName === "results") ? grade_exam_result_rows : null;
    };

//========= get_datadict_from_table_element  ============= PR2022-04-29
    function get_datadict_from_table_element(tblName, el){
// ---  lookup exam_dict in ete_exam_rows or in grade_exam_rows
        const tblRow = t_get_tablerow_selected(el);
        const pk_int = get_attr_from_el_int(tblRow, "data-pk");
        const data_rows = get_datarows_from_tblName(tblName);
        const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);
        const data_dict = (!isEmpty(found_dict)) ? found_dict : null;
        return data_dict;
    };  // get_datadict_from_table_element

//=========  RefreshDataRowsAfterUpload  ================ PR2022-02-26
    function RefreshDataRowsAfterUpload(response) {
        console.log(" --- RefreshDataRowsAfterUploadFromExcel  ---");
        console.log( "response", response);
        const is_test = (!!response && !!response.is_test);
        console.log( "is_test", is_test);

        if(!is_test) {
            const datalist_request = {
                setting: {page: "page_exams"},
                grade_exam_rows: {get: true}
            };
            //DatalistDownload(datalist_request);
        };
    }; //  RefreshDataRowsAfterUpload

})  // document.addEventListener('DOMContentLoaded', function()