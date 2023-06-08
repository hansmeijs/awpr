// PR2020-09-29 added

// PR2021-12-16 these variables are declared in base.js to make them global variables

// from https://stackoverflow.com/questions/11558025/do-browsers-propagate-javascript-variables-across-tabs
// variable values should not propagate between tabs - each tab should have its own global namespace,
// there would be all kinds of security issues if one tab could affect the JavaScript in another

// selected_btn is also used in t_MCOL_Open
//let selected_btn = "btn_ete_exams";

//let school_rows = [];
//let subject_rows = [];

// ---  id_new assigns fake id to new records
let id_new = 0;

document.addEventListener("DOMContentLoaded", function() {
    "use strict";

    selected = {
        item_count: 0
    };

    let el_loader = document.getElementById("id_loader");

// ---  get permits
    // permit dict gets value after downloading permit_list PR2021-03-27
    //  if user has no permit to view this page ( {% if no_access %} ): el_loader does not exist PR2020-10-02

// - NOTE: school ETE must have departments, because they are needed in the headerbar to select department PR2022-01-17

    const may_view_page = (!!el_loader);

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

    const ete_exam_dicts = {}; // PR2023-05-04 ete_exam_rows changed to ete_exam_dicts
    const duo_exam_dicts = {};  // PR2023-03-18 duo_exam_rows changed to duo_exam_dicts
    const duo_subject_dicts = {};  // PR2023-03-18 duo_subject_rows changed to duo_subject_dicts
    const ete_subject_dicts = {};  // PR2023-05-05 added
    const ntermentable_dicts = {};  // PR2023-03-18 ntermentable_rows changed to ntermentable_dicts
    const grade_exam_result_dicts = {};

    let el_focus = null; // stores id of element that must get the focus after closing mod message PR2020-12-20

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    urls.url_user_modmsg_hide = get_attr_from_el(el_data, "data-url_user_modmsg_hide");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    urls.url_usersetting_upload = get_attr_from_el(el_data, "data-url_usersetting_upload");
    urls.url_subject_upload = get_attr_from_el(el_data, "data-url_subject_upload");
    urls.url_exam_upload = get_attr_from_el(el_data, "data-url_exam_upload");
    urls.url_duo_exam_upload = get_attr_from_el(el_data, "data-url_duo_exam_upload");

    urls.url_exam_copy = get_attr_from_el(el_data, "data-url_exam_copy");
    urls.url_exam_copy_ntermen = get_attr_from_el(el_data, "data-url_exam_copy_ntermen");
    urls.url_approve_publish_exam = get_attr_from_el(el_data, "data-url_approve_publish_exam");
    urls.url_send_email_verifcode = get_attr_from_el(el_data, "data-url_send_email_verifcode");

    urls.url_link_exam_to_grades = get_attr_from_el(el_data, "data-url_link_exam_to_grades");

    urls.url_grade_upload = get_attr_from_el(el_data, "data-url_grade_upload");

    urls.url_exam_download_exam_pdf = get_attr_from_el(el_data, "data-url_exam_download_exam_pdf");
    urls.url_download_wolf_pdf = get_attr_from_el(el_data, "data-url_download_wolf_pdf");
    urls.url_exam_download_conversion_pdf = get_attr_from_el(el_data, "data-url_exam_download_conversion_pdf");

    urls.url_exam_download_exam_json = get_attr_from_el(el_data, "data-url_exam_download_exam_json");

    urls.url_download_published = get_attr_from_el(el_data, "data-download_published_url");

    // mod_MCOL_dict is defined in tables.js
    mod_MCOL_dict.columns.btn_ete_exams = {
        subj_name_nl: "Subject", lvl_abbrev: "Learning_path", version: "Version",
        examperiod: "Exam_type", blanks: "Blanks", secret_exam: "Designated_exam", status: "Status", download_exam: "Download_exam",
        cesuur: "Cesuur", scalelength: "Maximum_score", download_conv_table: "Download_conv_table"
    };
    mod_MCOL_dict.columns.btn_duo_exams = {
        subjbase_code: "Abbreviation", subj_name_nl: "Subject", lvl_abbrev: "Learning_path", version: "Version",
        ntb_omschrijving: "CVTE_description", examperiod: "Exam_type", nterm: "N_term", scalelength: "schaallengte",
        download_conv_table: "Download_conv_table"
    };
    mod_MCOL_dict.columns.btn_ntermen = {
        opl_code: "opl_code", leerweg: "leerweg", ext_code: "ext_code", tijdvak: "tijdvak", nex_id: "nex_id",
        omschrijving: "omschrijving", schaallengte: "schaallengte", n_term: "N_term",
        afnamevakid: "afnamevakid", extra_vakcodes_tbv_wolf: "extra_vakcodes_tbv_wolf",
        datum: "datum", begintijd: "begintijd", eindtijd: "eindtijd"
    };
    mod_MCOL_dict.columns.btn_results = {
        lvl_abbrev: "Learning_path", school_name: "School",
        grd_count: "Number_of_exams", result_count: "Submitted_exams",
        result_avg: "Average_score_percentage", download_conv_table: "Download_conv_table"
    };

// --- get field_settings
        field_settings.ete_exam =
                { field_caption: ["", "Abbrev_subject_2lines", "Subject", "Learning_path", "Version",
                                "Exam_type", "Designated_exam_2lines", "Blanks", "Maximum_score_2lines", "",
                                "Download_exam", "Cesuur", "Download_conv_table_2lines"],
                field_names: ["select", "subjbase_code", "subj_name_nl", "lvl_abbrev", "version",
                                "examperiod", "secret_exam", "blanks", "scalelength", "status",
                                "download_exam", "cesuur", "download_conv_table"],
                field_tags: ["div", "div", "div", "div", "div",
                            "div", "div", "div", "div", "div",
                            "a", "input", "a"],
                filter_tags: ["text",  "text", "text", "text", "text",
                              "text", "toggle", "text", "text", "status",
                              "text", "text", "text"],
                field_width: ["020", "075", "240", "120", "120",
                              "150", "090", "075", "075","032",
                              "090", "075", "100"],
                field_align: ["c",  "c", "l", "l", "l",
                               "l", "c", "c","c", "c",
                               "c", "c", "c"]};

        field_settings.duo_exam =
                { field_caption: ["", "Abbrev_subject_2lines", "Subject", "Learning_path", "Version", "CVTE_description",
                                "Exam_type", "Designated_exam_2lines", "schaallengte_2lines", "N_term", "Download_conv_table_2lines"],
                field_names: ["select", "subjbase_code", "subj_name_nl", "lvl_abbrev", "version", "ntb_omschrijving",
                            "examperiod", "secret_exam", "scalelength", "nterm", "download_conv_table"],
                field_tags: ["div", "div", "div", "div", "div", "div",
                             "div", "div", "input", "input", "a"],
                filter_tags: ["text", "text", "text", "text", "text", "text",
                             "text", "toggle", "text", "text", "text"],
                field_width: ["020", "075", "240", "120", "120", "300",
                                "150", "090", "075", "075", "100"],
                field_align: ["c",  "c", "l", "l", "l", "l","l", "c", "c", "c", "c"]};

        field_settings.results =
            {field_caption: ["", "Abbrev_subject_2lines", "Learning_path", "Exam", "Exam_type",
                                "Schoolcode_2lines", "School", "Number_of_exams", "Submitted_exams", "Average_score_percentage",
                                "Download_conv_table_2lines"],
            field_names: ["select", "subj_code", "lvl_abbrev", "exam_name", "examperiod",
                          "schoolbase_code", "school_name", "grd_count", "result_count", "result_avg", "download_conv_table"],

            field_tags: ["div", "div", "div", "div",  "div",
                        "div", "div", "div", "div", "div", "a"],
            filter_tags: ["select", "text", "text", "text",  "text",
                            "text", "text",  "text", "text", "text", "text"],
            field_width:  ["020", "075", "075","360", "120",
                            "075", "280", "090", "090", "090", "100"],
            field_align: ["c",  "c", "c", "l", "l",
                         "c", "l", "c", "c", "c", "c"]};

        field_settings.ntermen =
            {field_caption: ["", "opl_code", "leerweg", "ext_code", "tijdvak", "nex_id",
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
                            "c", "c", "c"]};

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

        const el_hdrbar_allowed_sections = document.getElementById("id_hdrbar_allowed_sections");
        if (el_hdrbar_allowed_sections){
            el_hdrbar_allowed_sections.addEventListener("click", function() {t_MUPS_Open()}, false );
        };

        const el_header_left = document.getElementById("id_header_left");

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
                function() {t_MSSSS_Open(loc, "subject", subject_rows, add_all, false, setting_dict, permit_dict, MSSSS_subject_response)}, false)};

        const el_SBR_select_showall = document.getElementById("id_SBR_select_showall");
        if (el_SBR_select_showall){
            el_SBR_select_showall.addEventListener("click", function() {t_SBR_show_all(SBR_show_all_response)}, false )};
        const el_SBR_item_count = document.getElementById("id_SBR_item_count")

// ---  MSSS MOD SELECT SCHOOL / SUBJECT / STUDENT ------------------------------
        const el_MSSSS_input = document.getElementById("id_MSSSS_input");
        const el_MSSSS_tblBody = document.getElementById("id_MSSSS_tbody_select");
        if (el_MSSSS_input){
            el_MSSSS_input.addEventListener("keyup", function(event){
                setTimeout(function() {t_MSSSS_InputKeyup(el_MSSSS_input)}, 50)});
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
        };

// ---  MEX MOD EXAM ------------------------------
        const el_MEXQ_questions = document.getElementById("id_mod_exam_questions");
        const el_MEXQ_header1 = document.getElementById("id_MEXQ_header1");
        const el_MEXQ_header2 = document.getElementById("id_MEXQ_header2");
        //const el_MEXQ_header3_student = document.getElementById("id_MEXQ_header3");
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
        const el_MDUO_header = document.getElementById("id_MDUO_header");

        const el_MDUO_tblBody_subjects = document.getElementById("id_MDUO_tblBody_subjects");
        const el_MDUO_tblBody_ntermentable = document.getElementById("id_MDUO_tblBody_ntermentable");
        const el_MDUO_tblBody_linked = document.getElementById("id_MDUO_tblBody_linked");

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
        //const el_MDNT_filename = document.getElementById("id_MDNT_filename");
        const el_MDNT_btn_save = document.getElementById("id_MDNT_btn_save");
        if (el_MDNT_btn_save){
            el_MDNT_btn_save.addEventListener("click", function() {MDNT_Save(RefreshDataRowsAfterUpload, setting_dict)}, false )};

// ---  MODAL CREATE DUO EXAM ------------------------------------
        const el_MDEC_header1 = document.getElementById("id_MDEC_header1");
        const el_MDEC_header2 = document.getElementById("id_MDEC_header2");
        const el_MDEC_select_subject = document.getElementById("id_MDEC_select_subject");
        if (el_MDEC_select_subject) {el_MDEC_select_subject.addEventListener("click", function() {MDEC_BtnSelectSubjectClick()}, false)};
        add_hover(el_MDEC_select_subject);
        const el_MDEC_err_subject = document.getElementById("id_MDEC_err_subject");
        const el_MDEC_select_level = document.getElementById("id_MDEC_select_level");
        if (el_MDEC_select_level) {el_MDEC_select_level.addEventListener("change", function() {MDEC_SelectLevelChange(el_MDEC_select_level)}, false)};

        const el_MDEC_err_level = document.getElementById("id_MDEC_err_level");
        const el_MDEC_input_version = document.getElementById("id_MDEC_input_version");
        if (el_MDEC_input_version) {el_MDEC_input_version.addEventListener("change", function() {MDEC_InputVersionChange(el_MDEC_input_version)}, false)};


        const el_MDEC_err_version = document.getElementById("id_MDEC_err_version");
        const el_MDEC_checkbox_secret_exam = document.getElementById("id_MEXQ_checkbox_secret_exam");

        const el_MDEC_btn_save = document.getElementById("id_MDEC_btn_save");
        if (el_MDEC_btn_save) {el_MDEC_btn_save.addEventListener("click", function() {MDEC_Save()})};
        const el_MDEC_btn_delete = document.getElementById("id_MDEC_btn_delete");
        if (el_MDEC_btn_delete) {el_MDEC_btn_delete.addEventListener("click", function() {ModConfirmOpen("duo_exam", "delete")})};

        const el_MDEC_msg_modified = document.getElementById("id_MDEC_msg_modified");

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

// ---  MOD MESSAGE ------------------------------------
        const el_mod_message_btn_hide = document.getElementById("id_mod_message_btn_hide");
        if(el_mod_message_btn_hide){
            el_mod_message_btn_hide.addEventListener("click", function() {ModMessageHide()});
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
        DatalistDownload({page: "page_exams"});
        //ResetFilterRows();
    };
//  #############################################################################################################

//========= DatalistDownload  ===================== PR2020-07-31
    function DatalistDownload(request_item_setting, keep_loader_hidden) {
        console.log( "=== DatalistDownload ")
        console.log("    request_item_setting: ", request_item_setting)

// ---  Get today's date and time - for elapsed time
        let startime = new Date().getTime();

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;
        selected.item_count = 0;

// ---  show loader
        if(!keep_loader_hidden){
            el_loader.classList.remove(cls_visible_hide);
        };
        add_or_remove_class(el_header_left.parentNode, cls_visible_hide, !keep_loader_hidden);

        const datalist_request = {
                setting: request_item_setting,
                locale: {page: ["page_exams", "page_grade", "upload"]},
                examyear_rows: {get: true},
                school_rows: {get: true},
                department_rows: {get: true},
                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},
                subject_rows: {with_ce_only: true, cur_dep_only: true},

                duo_ete_subject_rows: {get: true},
                ete_exam_rows: {get: true},
                duo_exam_rows: {get: true},
                grade_exam_rows: {get: true},
                grade_exam_result_rows: {get: true},
                ntermentable_rows: {get: true}
            };



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
                 // PR2022-05-15 remove field "download_conv_table" from mod_MCOL_dict.columns.btn_results when role != ROLE_008_SCHOOL
                    // because this field is removed from table 'results' when user is admin
                    if(permit_dict.requsr_same_school ){
                        // when school: skip column 'school_name'
                        mod_MCOL_dict.cols_skipped = {btn_results: ["schoolbase_code", "school_name"]}

                    } else {
                        // when admin col 'download_conv_table' is shown in table exam, skip in table results
                        //mod_MCOL_dict.cols_skipped = {btn_results: ["download_conv_table"]}
                    };

                };
                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict;

                    selected_btn = setting_dict.sel_btn;
                    must_update_headerbar = true;

                    // if sel_subject_pk has value, set sel_student_pk null
                    if (setting_dict.sel_subject_pk) {setting_dict.sel_student_pk = null;}

                    MSSSS_display_in_sbr_reset()

            // ---  fill cols_hidden
                    if("cols_hidden" in setting_dict){
                        //  setting_dict.cols_hidden was dict with key 'all' or se_btn, changed to array PR2021-12-14
                        //  skip when setting_dict.cols_hidden is not an array,
                        // will be changed into an array when saving with t_MCOL_Save
                        b_copy_array_noduplicates(setting_dict.cols_hidden, mod_MCOL_dict.cols_hidden);
                    };
                };

                if(must_create_submenu){CreateSubmenu()};

                if(must_update_headerbar){
                    b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department);
                    FillOptionsExamperiod();
                };
                if ("messages" in response) {
                    b_show_mod_message_dictlist(response.messages);
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
                };
                if ("loglist_copied_ntermen" in response) {

                    b_fill_datamap(level_map, response.loglist_copied_ntermen);
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
                        el_MASE_lvlbase.innerText = (el_SBR_select_level.options[el_SBR_select_level.selectedIndex]) ?
                                                el_SBR_select_level.options[el_SBR_select_level.selectedIndex].innerText : null;
                    };
                };

                if ("subject_rows" in response) {
                    subject_rows = response.subject_rows
                };
                t_MSSSS_display_in_sbr("subject", setting_dict.sel_subject_pk);

                if ("ete_exam_rows" in response) {
                    b_fill_datadicts("exam", "id", null, response.ete_exam_rows, ete_exam_dicts);
                };
                if ("duo_exam_rows" in response) {
                    b_fill_datadicts("exam", "id", null, response.duo_exam_rows, duo_exam_dicts);
                };
                if ("duo_subject_rows" in response) {
                    b_fill_datadicts("subject", "id", null, response.duo_subject_rows, duo_subject_dicts);
                };

                if ("ete_subject_rows" in response) {
                    b_fill_datadicts("subject", "id", null, response.ete_subject_rows, ete_subject_dicts);
                };
                if ("grade_exam_result_rows" in response) {
                    b_fill_datadicts("gradeexamresult", "exam_id", "school_id", response.grade_exam_result_rows, grade_exam_result_dicts);
                };
                if ("ntermentable_rows" in response) {
                    b_fill_datadicts("ntermentable", "id", null, response.ntermentable_rows, ntermentable_dicts);
                };
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

//=========  CreateSubmenu  ===  PR2020-07-31 PR2021-01-19 PR2021-03-25 PR2021-05-25 PR2023-05-05
    function CreateSubmenu() {
        console.log("===  CreateSubmenu == ");
        //console.log("permit_dict.requsr_same_school", permit_dict.requsr_same_school);

        let el_submenu = document.getElementById("id_submenu")
        // PR2022-05-19 Only CUR admin can add exams!!! It will get messed-up if SXM starts enetering stuff here
        // PR2022-06-02 sp DUO must be added by SXM, anble SXM to enter exams.
        // was: if (permit_dict.requsr_role_admin && permit_dict.requsr_country_pk === 1){

        //PR2023-06-08 debug: to prevent creating submenu multiple times: skip if btn columns exists
        if (!document.getElementById("id_submenu_columns")){
            if(permit_dict.permit_crud && permit_dict.requsr_role_admin ){
                if (permit_dict.requsr_country_is_cur){
                    AddSubmenuButton(el_submenu, loc.Add_ETE_exam, function() {MEXQ_Open()}, ["tab_show", "tab_btn_ete_exams"]);
                };
                AddSubmenuButton(el_submenu, loc.Add_CVTE_exam, function() {MDEC_Open()}, ["tab_show", "tab_btn_duo_exams"]);
                if (permit_dict.requsr_country_is_cur){
                    AddSubmenuButton(el_submenu, loc.Delete_ETE_exam, function() {ModConfirmOpen_delete("ete_exam", "delete")}, ["tab_show", "tab_btn_ete_exams"]);
                };
                AddSubmenuButton(el_submenu, loc.Delete_CVTE_exam, function() {ModConfirmOpen_delete("duo_exam", "delete")}, ["tab_show", "tab_btn_duo_exams"]);
                if (permit_dict.requsr_country_is_cur){
                    AddSubmenuButton(el_submenu, loc.Copy_exam, function() {ModConfirmOpen("ete_exam", "copy")}, ["tab_show", "tab_btn_ete_exams"]);
                };
                AddSubmenuButton(el_submenu, loc.Link_CVTE_exams, function() {MDUO_Open()}, ["tab_show", "tab_btn_duo_exams"]);
                AddSubmenuButton(el_submenu, loc.Link_exam_to_grades, function() {ModConfirm_link_exam_to_grades_Open()}, ["tab_show", "tab_btn_ete_exams", "tab_btn_duo_exams"]);
             }
            if (permit_dict.requsr_role_admin){
                if (permit_dict.permit_approve_exam && permit_dict.requsr_country_is_cur){
                    AddSubmenuButton(el_submenu, loc.Approve_exams, function() {MASE_Open("approve_admin")}, ["tab_show", "tab_btn_ete_exams"]);
                };
                if (permit_dict.permit_publish_exam && permit_dict.requsr_country_is_cur){
                    AddSubmenuButton(el_submenu, loc.Publish_exams, function() {MASE_Open("submit_admin")}, ["tab_show", "tab_btn_ete_exams"]);
                    AddSubmenuButton(el_submenu, loc.Undo_published, function() {ModConfirmOpen("ete_exam", "undo_published")}, ["tab_show", "tab_btn_ete_exams"]);
                };
           // } else if (permit_dict.requsr_role_school){
           //     if (permit_dict.permit_approve_exam ){
           //         AddSubmenuButton(el_submenu, loc.Approve_exams, function() {MASE_Open("approve_school")}, ["tab_showXX", "tab_btn_ete_exams"]);
           //     };
            };

            if(permit_dict.permit_crud && permit_dict.requsr_role_admin){
                AddSubmenuButton(el_submenu, loc.Upload_ntermen, function() {MDNT_Open()}, ["tab_show", "tab_btn_ntermen"], "id_submenu_upload_dnt");
                AddSubmenuButton(el_submenu, loc.Copy_ntermen_to_exams, function() {ModConfirmOpen("results", "copy_ntermen")}, ["tab_show", "tab_btn_ntermen"]);

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
        };
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

        // value of data_btn are: "btn_ete_exams" "btn_duo_exams" "btn_ntermen" "btn_results"

// ---  get data_btn from selected_btn when null;
        if (!data_btn) {data_btn = selected_btn};

// check if data_btn exists, gave error because old btn name was still in saved setting PR2021-09-07 debug
        const btns_allowed = ["btn_ete_exams", "btn_duo_exams", "btn_ntermen", "btn_results"];
        if (data_btn && btns_allowed.includes(data_btn)) {
            selected_btn = data_btn;
        } else {
            selected_btn = btns_allowed[0];
        };

        setting_dict.sel_btn = selected_btn;

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
    // ---  upload new setting
            const upload_dict = {page_exams: {sel_btn: selected_btn}};
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);
        };

// ---  fill datatable
        FillTblRows();

// --- update header text - comes after MSSSS_display_in_sbr
        UpdateHeaderLeftRight(skip_upload);
// ---  highlight selected button
        b_highlight_BtnSelect(el_btn_container, selected_btn);

// ---  show only the elements that are used in this tab
        // Note Mexq has also tab_classes. Make sure they have different names
        b_show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

    };  // HandleBtnSelect

//=========  HandleTblRowClicked  ================ PR2020-08-03 PR2021-05-22
    function HandleTblRowClicked(tblRow) {
        console.log("=== HandleTblRowClicked");
        console.log( "    tblRow: ", tblRow);

// ---  deselect all highlighted rows, select clicked row
        t_td_selected_toggle(tblRow, true);  // select_single = True

// ---  lookup exam_dict in exam_rows
        const tblName = get_attr_from_el(tblRow, "data-table")
        const data_dicts = get_datadicts_from_sel_btn();

        // PR2022-05-11 Sentry debug: Unhandled Expected identifier with IE11 on Windows 7
        // leave it as it is, maybe error caused by IE 11
        const data_pk = get_attr_from_el_int(tblRow, "data-pk")
        const school_pk = get_attr_from_el_int(tblRow, "data-school_pk")
        const lookup_1_field = (tblName === "results") ? "exam_id" : "id";
        const lookup_2_field = (tblName === "results") ? "school_id" : null;

        //const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, lookup_1_field, data_pk, lookup_2_field, school_pk);
        const pk_int = null; // (!isEmpty(found_dict)) ?  (tblName === "results") ? found_dict.exam_id : found_dict.id : null;

// ---  update setting_dict.pk_int
        if (["duo_exam", "ete_exam"].includes(tblName)){
            setting_dict.sel_exam_pk = (pk_int) ? pk_int : null;
        } else if (tblName === "grades"){
            setting_dict.sel_grade_exam_pk = (pk_int) ? pk_int : null;

        } else if (tblName === "results"){
            setting_dict.sel_exam_pk = (pk_int) ? pk_int : null;
        };

        selected.map_id = (tblRow) ? tblRow.id : null;
        console.log( "    selected.map_id: ", selected.map_id);
    };  // HandleTblRowClicked

//=========  HandleSbrPeriod  ================ PR2020-12-20 PR2022-02-21
    function HandleSbrPeriod(el_select) {
        console.log("=== HandleSbrPeriod");

        setting_dict.sel_examperiod = (Number(el_select.value)) ? Number(el_select.value) : null;

        el_SBR_item_count.innerText = null;

// ---  upload new setting
        const request_item_setting = {
            page: 'page_exams',
            sel_examperiod: setting_dict.sel_examperiod
        };
        DatalistDownload(request_item_setting);

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
        setting_dict.sel_lvlbase_code = (el_select.options[el_select.selectedIndex]) ? el_select.options[el_select.selectedIndex].innerText : null;

        el_SBR_item_count.innerText = null;

// ---  upload new setting
        const request_item_setting = {
            page: 'page_exams',
            sel_lvlbase_pk: setting_dict.sel_lvlbase_pk
        };
        DatalistDownload(request_item_setting);
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

        const caption_all = "&#60" + ( (tblName === "level") ? loc.All_levels : (has_profiel) ? loc.All_profiles : loc.All_sectors ) + "&#62";
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
            const sel_code = (el_SBR_select.options[el_SBR_select.selectedIndex]) ? el_SBR_select.options[el_SBR_select.selectedIndex].innerText : null;
            if (tblName === "level"){
                setting_dict.sel_lvlbase_code = sel_code;
            } else if (tblName === "sector"){
                setting_dict.sel_sctbase_code = sel_code;
            };
        };
    };  // FillOptionsSelectLevelSector

//=========  HandleShowAll  ================ PR2020-12-17
    function HandleShowAll() {
        console.log("=== HandleShowAll");

        setting_dict.sel_exam_pk = null;

    // don't reset sel_examperiod
        //setting_dict.sel_examperiod = 12;
        //if (el_SBR_select_examperiod){
            //el_SBR_select_examperiod.value = "12";
        //};

        if (el_SBR_select_level){
            el_SBR_select_level.value = -9;
        };
        if (el_SBR_select_subject){
             el_SBR_select_subject.value = "<" + loc.All_subjects + ">";
        };

// ---  upload new setting
        const selected_pk_dict = {
        sel_lvlbase_pk: null,
        sel_sctbase_pk: null,
        sel_subject_pk: null,
        sel_cluster_pk: null,
        sel_student_pk: null
        //sel_examperiod: 12
        };
        //const page_grade_dict = {sel_btn: "grade_by_all"}
       //const upload_dict = {selected_pk: selected_pk_dict, page_grade: page_grade_dict};
        const upload_dict = {selected_pk: selected_pk_dict};
        console.log("upload_dict", upload_dict);

        b_UploadSettings (upload_dict, urls.url_usersetting_upload);

        HandleBtnSelect(null, true) // true = skip_upload
        // also calls: FillTblRows(), MSSSS_display_in_sbr(), UpdateHeader()

// also retrieve the tables that have been changed because of the change in examperiod
// ---  upload new setting
        const request_item_setting = {page: 'page_exams',
                            sel_examperiod: null,
                            sel_lvlbase_pk: null,
                            sel_sctbase_pk: null,
                            sel_subject_pk: null,
                            sel_cluster_pk: null,
                            sel_student_pk: null
                          };
        DatalistDownload(request_item_setting);
    }  // HandleShowAll


    function SBR_show_all_response() {
        console.log("===== SBR_show_all_response =====");
        // this is response of t_SBR_show_all

// ---  upload new setting and refresh page
// also retrieve the tables that have been changed because of the change in examperiod
        const request_item_setting = {page: 'page_exams',
                            sel_examperiod: null,
                            sel_lvlbase_pk: null,
                            sel_sctbase_pk: null,
                            sel_subject_pk: null,
                            sel_cluster_pk: null,
                            sel_student_pk: null
                          };
        DatalistDownload(request_item_setting);
    };  // SBR_show_all_response

//========= UpdateHeaderLeftRight  ================== PR2021-03-14 PR2022-01-17 PR2022-08-28
    function UpdateHeaderLeftRight(skip_upload){
        //console.log(" --- UpdateHeaderLeftRight ---" )
        //console.log("setting_dict", setting_dict)
        el_header_left.innerText = get_dep_lvl_examperiod_txt();
        add_or_remove_class(el_header_left.parentNode, cls_visible_hide, !skip_upload);
    };   //  UpdateHeaderLeftRight

    function get_dep_lvl_examperiod_txt(){
        // PR2022-08-28

        const examperiod_caption = (setting_dict && [1, 2, 3].includes(setting_dict.sel_examperiod) && loc.examperiod_caption[setting_dict.sel_examperiod]) ?
            "- " + loc.examperiod_caption[setting_dict.sel_examperiod] : null;

        const depbase_code = (setting_dict && setting_dict.sel_depbase_code) ? " " + setting_dict.sel_depbase_code : "";
        const level_abbrev = (setting_dict && setting_dict.sel_lvlbase_pk && setting_dict.sel_lvlbase_code) ? " " + setting_dict.sel_lvlbase_code : "";

        return [depbase_code, level_abbrev, examperiod_caption].join(" ");
    };

//###########################################################################
// +++++++++++++++++ FILL TABLE ROWS ++++++++++++++++++++++++++++++++++++++++
//========= FillTblRows  ====================================
    function FillTblRows() {
        console.log( "===== FillTblRows  === ");

        const tblName = get_tblName_from_selectedBtn();
        const field_setting = field_settings[tblName];

    //console.log( "    tblName", tblName);
    //console.log( "    field_setting", field_setting);
    //console.log( "    setting_dict.sel_subject_pk", setting_dict.sel_subject_pk);

// --- get data_rows
        const data_dicts = get_datadicts_from_sel_btn();

// ---  get list of hidden columns
        const col_hidden = b_copy_array_to_new_noduplicates(mod_MCOL_dict.cols_hidden);

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
        let item_count = 0;

// --- create table header
        CreateTblHeader(field_setting, col_hidden);

// --- create table rows
        if(data_dicts){
            for (const data_dict of Object.values(data_dicts)) {
            // only show rows of selected student / subject
            // selected_btns are: "btn_ete_exams", "btn_duo_exams", "btn_ntermen", "btn_results"

                let show_row = false;
                if (selected_btn === "btn_ntermen") {
                    show_row = true;
                } else if (!setting_dict.sel_lvlbase_pk || data_dict.lvlbase_id === setting_dict.sel_lvlbase_pk) {
                    show_row = (!setting_dict.sel_subject_pk || data_dict.subj_id === setting_dict.sel_subject_pk);
                };

                if(show_row){
          // --- insert row
                    let tblRow = CreateTblRow(tblName, field_setting, data_dict, col_hidden)
                    item_count += 1;
                };
            };
        };
        selected.no_items = !item_count;
        if (selected.no_items){
            if (["btn_ete_exams", "btn_duo_exams", "btn_results"].includes(selected_btn)) {
                let msg_html = (selected_btn === "btn_duo_exams") ?  loc.no_CVTE_exams :loc.no_ETE_exams;
                if (setting_dict.sel_dep_level_req && setting_dict.sel_lvlbase_code) {
                    msg_html += " " + setting_dict.sel_lvlbase_code;
                }
                if (setting_dict.sel_subject_pk && setting_dict.sel_subject_name) {
                    msg_html += " " + setting_dict.sel_subject_name;
                }
                msg_html += ((setting_dict.sel_examperiod === 1) ? loc.in_the_1st_examperiod :
                            (setting_dict.sel_examperiod === 2) ? loc.in_the_2nd_examperiod :
                            (setting_dict.sel_examperiod === 3) ? loc.in_the_3rd_examperiod : "") + ".";

                let tblRow = tblBody_datatable.insertRow(-1);
                let td = tblRow.insertCell(-1);
                td = tblRow.insertCell(-1);
                td.setAttribute("colspan", 6);
                let el = document.createElement("p");
                el.className = "border_bg_transparent p-2 my-4"
                el.innerHTML = msg_html;
                td.appendChild(el);
            };
        }
        Filter_TableRows();
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
                    //el_filter.setAttribute("data-colindex", j);
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

                } else if (filter_tag === "toggle") {
                    // add EventListener for icon to th_filter, not el_filter
                    th_filter.addEventListener("click", function(event){HandleFilterToggle(el_filter)});
                    th_filter.classList.add("pointer_show");
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
        // only admin with crud permit may change, ete exams only when user is cur PR2023-05-12
        const permit_admin_crud_only = (permit_dict.permit_crud && permit_dict.requsr_role_admin
                && (data_dict.ete_exam && permit_dict.requsr_country_is_cur) || (!data_dict.ete_exam));

        const permit_admin_approve_exam = (permit_dict.permit_approve_exam && permit_dict.requsr_role_admin
                && (data_dict.ete_exam && permit_dict.requsr_country_is_cur) || (!data_dict.ete_exam));
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
        const pk_int = (tblName === "results") ? data_dict.exam_id : data_dict.id;
        tblRow.setAttribute("data-pk", pk_int);
        if (tblName === "results") {
            tblRow.setAttribute("data-school_pk", data_dict.school_id);
        };
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
                    if (permit_admin_crud_only){
                        el.addEventListener("change", function(){HandleInputChange(el)});
                        el.addEventListener("keydown", function(event){HandleArrowEvent(el, event)});
                    };
// --- add class 'input_text' and text_align
                // class 'input_text' contains 'width: 100%', necessary to keep input field within td width
                    el.classList.add("input_text");

// --- make el readonly when not requsr_role_admin
                    el.readOnly = !permit_admin_crud_only;

                } else if (field_name === "secret_exam"){
                    if(permit_admin_crud_only){
                        td.addEventListener("click", function() {UploadToggle(el)}, false)
                        add_hover(td);
                    };

                } else if (field_name === "status"){
                    if (permit_admin_approve_exam){
                        td.addEventListener("click", function() {HandleToggleApprove(tblName, el)}, false)
                        add_hover(td);
                    };
                // --- add column with status icon
                    el.classList.add("stat_0_1");

                } else if (field_name === "download_exam"){
                    // td.class_align necessary to center align a-element
                    td.classList.add(class_align);

                } else if (field_name === "download_conv_table"){
            // +++  create href and put it in button PR2021-05-07
                    if (["ete_exam", "duo_exam"].includes(tblName)) {
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
                    if (permit_admin_crud_only) {
                        td.addEventListener("click", function() {MSELEX_Open(el)}, false);
                        add_hover(td);
                    };
                } else {
                    if (permit_admin_crud_only) {
                        if (tblName === "duo_exam"){
                            td.addEventListener("click", function() {MDEC_Open(el)}, false);
                        } else if (tblName === "ete_exam"){
                            td.addEventListener("click", function() {MEXQ_Open(el)}, false);
                        };
                        add_hover(td);
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
        console.log("=========  UpdateTblRow =========");
        console.log("data_dict", data_dict);
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

                } else if (field_name === "cesuur"){
                    el_div.value = data_dict[field_name];
                    filter_value = data_dict[field_name];

                } else if (field_name === "scalelength"){
                    // show '0', therefore don't use ( data_dict.ce_exam_score) ?  data_dict.ce_exam_score : null
                    inner_text = (data_dict[field_name] != null) ? data_dict[field_name] : null;
                    if (tblName === "duo_exam"){
                        el_div.value = inner_text;
                    } else {
                        el_div.innerHTML = (inner_text) ? inner_text : "&nbsp";
                    };
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
                    if (["ete_exam", "duo_exam"].includes(tblName)) {
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
                    };
                };
                add_or_remove_attr (el_div, "title", !!title_text, title_text);
// ---  add attribute filter_value
                add_or_remove_attr (el_div, "data-filter", !!filter_value, filter_value);
            };
        };
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
                                                       urls.url_download_wolf_pdf.replace("-", pk_str) ;
        el_div.href = href_str;
    };  // UpdateFieldDownloadExam


//=========  UpdateFieldScore  ================ PR2022-05-17
    function UpdateFieldScore(loc, data_dict) {
        //console.log("=========  UpdateFieldScore =========");
        //console.log("data_dict.ce_exam_score", data_dict.ce_exam_score);

        const inner_text = (data_dict.secret_exam) ? loc.not_applicable :
               (data_dict.ce_exam_score != null) ? data_dict.ce_exam_score.toString() : null;

        const title_text = (!data_dict.secret_exam) ?
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

//========= UploadToggle  ============= PR2022-05-16 PR2022-06-15 PR2023-06-08
    function UploadToggle(el_input) {
        console.log( " ==== UploadToggle ====");
        // only called by field 'secret_exam', can be duo and ete exam

        if (permit_dict.permit_crud && permit_dict.requsr_role_admin){
            const fldName = get_attr_from_el(el_input, "data-field");

            const tblName = get_tblName_from_selectedBtn();
            const data_dict = get_datadict_from_table_element(el_input);

            if(!isEmpty(data_dict)){
                const exam_pk = data_dict.id;
                const published_id = data_dict.published_id;
                if (data_dict.published_id){
                    b_show_mod_message_html(loc.err_list.This_exam_is_published + "<br>" + loc.err_list.Remove_published_first);

                // PR2023-06-08 TODO: block when exam is (partly approved, but let ETE first add secret_exams
               // } else if (data_dict.auth1by_id || data_dict.auth2by_id){
               //     b_show_mod_message_html(loc.err_list.This_exam_is_approved + "<br>" + loc.err_list.Remove_approvals_first);

                } else {
                    // subj_id is used in ete_exam_dicts,  subj_id is used PR2023-06-02
                    const subject_pk = data_dict.subj_id;
                    const examyear_pk = data_dict.ey_id;

                    console.log( "data_dict", data_dict);

                    const old_value = data_dict[fldName];
                    const new_value = (!old_value);

        // ---  change icon, before uploading
                    add_or_remove_class(el_input, "tickmark_1_2", new_value, "tickmark_0_0");

                    // ---  upload changes
                    const upload_dict = {
                        table: tblName,
                        examyear_pk: examyear_pk,
                        examperiod: setting_dict.sel_examperiod,
                        exam_pk: exam_pk,
                        subject_pk: subject_pk
                    };
                    upload_dict[fldName] = new_value;
                    UploadChanges(upload_dict, urls.url_exam_upload);
                };
            };
        };
    }  // UploadToggle

//========= UploadChanges  ============= PR2020-08-03
    function UploadChanges(upload_dict, url_str) {
        console.log("=== UploadChanges");
        console.log("     url_str: ", url_str);
        console.log("     upload_dict: ", upload_dict);

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
                        RefreshDataRowsNEW("ete_exam", response.updated_ete_exam_rows, ete_exam_dicts, true)  // true = update
                    };
                    if ("updated_duo_exam_rows" in response) {
                        RefreshDataRowsNEW("duo_exam", response.updated_duo_exam_rows, duo_exam_dicts, true)  // true = update
                    };

                    if ("loglist_copied_ntermen" in response) {
                       OpenLogfile(loc, response.loglist_copied_ntermen);
                    };

                    if ("response_link_exam_to_grades" in response) {
                       ModConfirmResponseLinkExamToGrades(response);
                    };
                    if ("response_link_exam_to_grades_loglist" in response) {
                       OpenLogfile(loc, response.response_link_exam_to_grades_loglist);
                    };
                    if ("messages" in response) {
                        b_show_mod_message_dictlist(response.messages);
                    };
                    if ("msg_html" in response) {
                        b_show_mod_message_html(response.msg_html)
                    };
                    if ( "approve_msg_html" in response){
                        MASE_UpdateFromResponse(response)
                    };
                    if ("updated_published_rows" in response) {
                        RefreshDataRows("published", response.updated_published_rows, published_map);
                    };
                },  // success: function (response) {
                error: function (xhr, msg) {
                    el_loader.classList.add(cls_visible_hide);
                    console.log(msg + '\n' + xhr.responseText);
                     b_show_mod_message_html(["<p class='border_bg_invalid p-2'>",
                                 loc.An_error_occurred, "<br><i>", msg, "<br><i>", xhr.responseText, '</i><br>',
                                "</p>"].join(""));
                    $("#id_mod_approve_exam").modal("hide");
                }  // error: function (xhr, msg) {
            });  // $.ajax({
        }  //  if(!!row_upload)
    };  // UploadChanges

//========= HandleToggleApprove  ============= PR2022-01-24 PR2022-04-29
    function HandleToggleApprove(tblName, el_input) {
        console.log( " ==== HandleToggleApprove ====");
        // called by field "status' in table "ete_exam", "duo_exam", "grades"

// ---  lookup exam_dict in ete_exam_rows or in grade_exam_rows
        const data_dict = get_datadict_from_table_element(el_input)

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

                        const new_class_str = f_get_status_auth12_iconclass(is_published, false, auth1by_id, auth2by_id);

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
// +++++++++++++++++ REFRESH DATA DICTS +++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataRowsNEW  ================ PR2020-08-16 PR2020-09-30 PR2021-05-11 PR2022-01-23 PR2022-04-13 PR2024-05-04
    function RefreshDataRowsNEW(tblName, update_rows, data_dicts, is_update) {
        console.log(" --- RefreshDataRowsNEW  ---");
        //console.log("    tblName", tblName);
        //console.log("    update_rows", update_rows);

        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length
        if (update_rows && update_rows.length ) {
            const field_setting = field_settings[tblName];

    // ---  get list of hidden columns
            const col_hidden = b_copy_array_to_new_noduplicates(mod_MCOL_dict.cols_hidden);

    // - hide level when not level_req
            if(!setting_dict.sel_dep_level_req){col_hidden.push("lvl_abbrev")};

            for (let i = 0, update_dict; update_dict = update_rows[i]; i++) {
                RefreshDatarowItemNEW(tblName, field_setting, col_hidden, update_dict, data_dicts);
            };
        } else if (!is_update) {
            // empty the data_rows when update_rows is empty PR2021-01-13 debug forgot to empty data_rows
            // PR2021-03-13 debug. Don't empty de data_rows when is update. Returns [] when no changes made

           b_clear_dict(data_dicts);
        };
        if (tblName === "duo_exam" && el_MDUO_btn_save){
            MDUO_FillTables();
            //el_MDUO_btn_save.disabled = true;
        };
    };  //  RefreshDataRowsNEW

//=========  RefreshDatarowItemNEW  ================ PR2020-08-16 PR2020-09-30 PR2022-01-23 PR2022-04-13 PR2022-05-17
    function RefreshDatarowItemNEW(tblName, field_setting, col_hidden, update_dict, data_dicts) {
        //console.log(" --- RefreshDatarowItemNEW  ---");
        //console.log("    tblName", tblName);
        //console.log("    update_dict", update_dict);
        //console.log("    data_dicts", data_dicts);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

        const map_id = update_dict.mapid;

    //console.log("    map_id", map_id);

            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);

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
    //console.log("    error_columns", error_columns);

// ++++ created ++++
            // PR2021-06-16 from https://stackoverflow.com/questions/586182/how-to-insert-an-item-into-an-array-at-a-specific-index-javascript
            //arr.splice(index, 0, item); will insert item into arr at the specified index
            // (deleting 0 items first, that is, it's just an insert).

            if(is_created){
    // ---  first remove key 'created' from update_dict
                delete update_dict.created;

    // --- lookup index where new row must be inserted in data_dicts
                // PR2021-06-21 not necessary, new row has always pk higher than existing. Add at end of rows

    // ---  add new item in data_dicts at end
                if (!data_dicts.hasOwnProperty(map_id)){
                    data_dicts[map_id] = update_dict;
                };

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

// +++ get existing data_dict from data_dicts.
                const data_dict = (data_dicts.hasOwnProperty(map_id)) ? data_dicts[map_id] : null;

    //console.log("    data_dicts", data_dicts)
    //console.log("    map_id", map_id)
    //console.log("    data_dict", data_dict);

                if(data_dict){

// ++++ deleted ++++
                    if(is_deleted){
                        // delete row from data_dicts
                        delete data_dicts[map_id];
            //--- delete tblRow

                        const tblRow_tobe_deleted = document.getElementById(map_id);
                        if (tblRow_tobe_deleted ){
                            tblRow_tobe_deleted.parentNode.removeChild(tblRow_tobe_deleted);
        // --- subtract 1 from item_count and show total in sidebar
                            selected.item_count -= 1;
    // ---  show total in sidebar
                            t_set_sbr_itemcount_txt(loc, selected.item_count, loc.Exam, loc.Exams, setting_dict.user_lang);
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
    }; // RefreshDatarowItemNEW

// ##########################################################################
//###########################################################################
// +++++++++++++++++ REFRESH DATA MAP +++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataRows  ================ PR2020-08-16 PR2020-09-30 PR2021-05-11 PR2022-01-23 PR2022-04-13
    function RefreshDataRows(tblName, update_rows, data_rows, is_update) {
        console.log(" --- RefreshDataRows  ---");
        console.log("    tblName", tblName);
        console.log("    update_rows", update_rows);

        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length
        if (update_rows && update_rows.length ) {
            const field_setting = field_settings[tblName];

    // ---  get list of hidden columns
            const col_hidden = b_copy_array_to_new_noduplicates(mod_MCOL_dict.cols_hidden);

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
            MDUO_FillTables();
            //el_MDUO_btn_save.disabled = true;
        };
    };  //  RefreshDataRows

//=========  RefreshDatarowItem  ================ PR2020-08-16 PR2020-09-30 PR2022-01-23 PR2022-04-13 PR2022-05-17
    function RefreshDatarowItem(tblName, field_setting, col_hidden, update_dict, data_rows) {
        console.log(" --- RefreshDatarowItem  ---");
        //console.log("tblName", tblName);
        console.log("update_dict", update_dict);
        //console.log("data_rows", data_rows);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);

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
                const data_dicts = get_datadicts_from_sel_btn();
                const data_rows = [];
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
        console.log(" --- HandleInputChange ---");

        // function is only called by field 'cesuur' in table 'ete_exam

        const data_dict = get_datadict_from_table_element(el_input);
        console.log("data_dict", data_dict);

        const old_value = data_dict[fldName];

        const has_permit = (permit_dict.permit_crud && permit_dict.requsr_role_admin);
        if (!has_permit){
            b_show_mod_message_html(loc.grade_err_list.no_permission);
    // put back old value in el_input
            el_input.value = old_value;
    // check if changes are made by same country that created exam -- done on server
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
                            } else if (value_number <= 0) {
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
                            } else if (value_number <= 0) {
                                msg_html = loc.err_list.scalelength_mustbe; // "Score moet een getal groter dan nul zijn."
                            } else if (value_number % 1 !== 0 ) {
                                // the remainder / modulus operator (%) returns the remainder after (integer) division.
                                msg_html = loc.err_list.scalelength_mustbe;
                            };
                        } else if (fldName === "nterm"){
                            if(!value_number && value_number != 0){
                                msg_html = loc.err_list.nterm_mustbe;
                            } else if (value_number < 0 || value_number > 9) {
                                msg_html = loc.err_list.nterm_mustbe; // "N-term moet een getal groter dan nul zijn."
                            } else if ((value_number * 10) % 1 !== 0 ) {
                                // the remainder / modulus operator (%) returns the remainder after (integer) division.
                                msg_html = loc.err_list.nterm_mustbe;
                            };
                        };
                    };
                }
                if (msg_html){
    // ---  show modal MESSAGE
                    mod_dict = {el_focus: el_input}
                    b_show_mod_message_html(msg_html, null, null, ModMessageClose);
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
                        ModConfirm_Cesuur_Nterm_Open("cesuur", el_input)

                    } else if (fldName === "nterm"){
                        mod_dict = {mode: "nterm",
                                    exam_pk: data_dict.id,
                                    examyear_pk: data_dict.ey_id,
                                    subject_pk: data_dict.subj_id,
                                    exam_name: data_dict.exam_name,
                                    nterm: new_value,
                                    old_value: old_value,
                                    el_input: el_input
                                    };
                        ModConfirm_Cesuur_Nterm_Open("nterm", el_input)

                    } else if (fldName === "scalelength"){
                        const upload_dict = {
                            table: "duo_exam",
                            mode: "update",
                            exam_pk: data_dict.id,
                            examyear_pk: data_dict.ey_id,
                            subject_pk: data_dict.subj_id,
                            examperiod: data_dict.examperiod
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
        if (!skip_filter) {
            Filter_TableRows();
        };
    }; // function HandleFilterKeyup

//========= HandleFilterToggle  =============== PR2023-03-31
    function HandleFilterToggle(el_input) {
        console.log( "===== HandleFilterToggle  ========= ");

    // - get col_index and filter_tag from  el_input
        // PR2021-05-30 debug: use cellIndex instead of attribute data-colindex,
        // because data-colindex goes wrong with hidden columns
        // was:  const col_index = get_attr_from_el(el_input, "data-colindex")
        const col_index = el_input.parentNode.cellIndex;

    // - get filter_tag from  el_input
        const filter_tag = get_attr_from_el(el_input, "data-filtertag")
        const field_name = get_attr_from_el(el_input, "data-field")
    console.log( "    col_index", col_index);
    console.log( "    filter_tag", filter_tag);
    console.log( "    field_name", field_name);
    console.log( "    filter_dict", filter_dict);

    // - get current value of filter from filter_dict, set to '0' if filter doesn't exist yet
        const filter_array = (col_index in filter_dict) ? filter_dict[col_index] : [];
        const filter_value = (filter_array[1]) ? filter_array[1] : "0";
    console.log( "    filter_array", filter_array);


        // default filter triple '0'; is show all, '1' is show tickmark, '2' is show without tickmark
        // - toggle filter value
        const new_value = (filter_value === "2") ? "0" : (filter_value === "1") ? "2" : "1";
        // - get new icon_class
        const icon_class =  (new_value === "2") ? "tickmark_2_1" : (new_value === "1") ? "tickmark_2_2" : "tickmark_0_0";
        // default filter triple '0'; is show all, '1' is show tickmark, '2' is show without tickmark

    // - put new filter value in filter_dict
        filter_dict[col_index] = [filter_tag, new_value]

        el_input.className = icon_class;

        Filter_TableRows();
    };  // HandleFilterToggle

//========= HandleFilterStatus  =============== PR2023-02-21
    function HandleFilterStatus(el_input) {
        console.log( "===== HandleFilterStatus  ========= ");

    // - get col_index and filter_tag from  el_input
        // PR2021-05-30 debug: use cellIndex instead of attribute data-colindex,
        // because data-colindex goes wrong with hidden columns
        // was:  const col_index = get_attr_from_el(el_input, "data-colindex")
        const col_index = el_input.parentNode.cellIndex;

    // - get filter_tag from  el_input
        const filter_tag = get_attr_from_el(el_input, "data-filtertag")
        const field_name = get_attr_from_el(el_input, "data-field")
    console.log( "    col_index", col_index);
    console.log( "    filter_tag", filter_tag);
    console.log( "    field_name", field_name);
    console.log( "    filter_dict", filter_dict);

    // - get current value of filter from filter_dict, set to '0' if filter doesn't exist yet
        const filter_array = (col_index in filter_dict) ? filter_dict[col_index] : [];
        const filter_value = (filter_array[1]) ? filter_array[1] : "0";
    console.log( "    filter_array", filter_array);

        let new_value = "0", icon_class = "tickmark_0_0";

        // filter_values are: '0'; is show all, 1: not approved, 2: auth1 approved, 3: auth2 approved, 4: auth1+2 approved, 5: submitted,   TODO '6': tobedeleted '7': locked

// - toggle filter value
        let value_int = (Number(filter_value)) ? Number(filter_value) : 0;
console.log( "......filter_value", filter_value);
        value_int += 1;
        if (value_int > 5 ) { value_int = 0};

        // convert 0 to null, otherwise  "0" will not filter correctly
        new_value = (value_int) ? value_int.toString() : null;
// - get new icon_class
        icon_class =  (new_value === "5") ? "diamond_0_4" :
                        (new_value === "4") ? "diamond_3_3" :
                        (new_value === "3") ? "diamond_1_2" :
                        (new_value === "2") ? "diamond_2_1" :
                        (new_value === "1") ? "diamond_0_0" : "tickmark_0_0";

    // - put new filter value in filter_dict
        filter_dict[col_index] = [filter_tag, new_value];

console.log( "......new_value", new_value, typeof  new_value);
console.log( "......icon_class", icon_class);
console.log( "......filter_dict", filter_dict);

        el_input.className = icon_class;

        Filter_TableRows();
    };  // HandleFilterStat


//========= HandleFilterStatus  =============== PR2020-07-21 PR2020-09-14 PR2021-03-23
    function HandleFilterStatusXXX(el_input) {
        console.log( "===== HandleFilterStatus  ========= ");

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
        Filter_TableRows();

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
            show_row = t_Filter_TableRow_Extended(filter_dict, tblRow);
            add_or_remove_class(tblRow, cls_hide, !show_row);
            if (show_row){ selected.item_count += 1};
        };
        if (selected.no_items) {selected.item_count = 0 };
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
       console.log( "===== ResetFilterRows  ========= ");

        setting_dict.sel_exam_pk = null;
        selected.map_id = null; //PR2023-05-16 added

        filter_dict = {};


        t_reset_filterrow(tblHead_datatable);
        t_tbody_selected_clear(tblBody_datatable);
// ---  show total in sidebar
        t_set_sbr_itemcount_txt();

        t_Filter_TableRows(tblBody_datatable, filter_dict, selected, loc.Exam, loc.Exams);

        //Filter_TableRows(tblBody_datatable);
        //FillTblRows();
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
            el_div.classList.add("tw_480", "px-2", "pointer_show" )
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
// +++++++++ MOD DUO EXAM CREATE ++++++++++++++++ PR2022-08-27 PR2023-03-20
    function MDEC_Open(el_input){
        console.log(" ===  MDEC_Open  =====") ;

        if(permit_dict.permit_crud && permit_dict.requsr_role_admin){
            b_clear_dict(mod_MEX_dict);

            el_MDEC_select_subject.innerText = null;
            el_MDEC_input_version.innerText = null;
            el_MDEC_select_level.value = null;
            el_MDEC_msg_modified.innerText = null;

    // el_input is undefined when called by submenu btn 'Add new'
            mod_MEX_dict.is_addnew = (!el_input);

            if (mod_MEX_dict.is_addnew) {

                if (![1, 2, 3].includes(setting_dict.sel_examperiod)) {
                    b_show_mod_message_html(loc.Please_select_examperiod_first);
                } else {
                    mod_MEX_dict.examperiod = setting_dict.sel_examperiod;
                    mod_MEX_dict.examyear_pk = setting_dict.sel_examyear_pk;
                    mod_MEX_dict.depbase_pk = setting_dict.sel_depbase_pk;
                    mod_MEX_dict.sel_dep_level_req = setting_dict.sel_dep_level_req;

                    mod_MEX_dict.lvlbase_pk = setting_dict.sel_lvlbase_pk;
                };
            } else {
    // ---  lookup ete_exam_dict in ete_exam_rows
                const data_dict = get_datadict_from_table_element(el_input);
        console.log("    data_dict", data_dict);

                if (!isEmpty(data_dict)){

                    mod_MEX_dict.examperiod = data_dict.examperiod;

                    mod_MEX_dict.exam_pk = data_dict.id;
                    mod_MEX_dict.exam_name = data_dict.exam_name;
                    mod_MEX_dict.version = data_dict.version;

                    mod_MEX_dict.lvlbase_pk = data_dict.lvlbase_id;

                    mod_MEX_dict.sel_subject_pk = data_dict.subj_id;
                    mod_MEX_dict.sel_subject_name = data_dict.subj_name_nl;
                    mod_MEX_dict.secret_exam = data_dict.secret_exam;
                    mod_MEX_dict.version = data_dict.version;

        // - set text in subject, version and secret_exam field
                    el_MDEC_select_subject.innerText = (mod_MEX_dict.sel_subject_pk) ? mod_MEX_dict.sel_subject_name : loc.Click_here_to_select_subject;
                    el_MDEC_input_version.value = (mod_MEX_dict.version) ? mod_MEX_dict.version : null;
                    el_MDEC_checkbox_secret_exam.checked = (mod_MEX_dict.secret_exam) ? mod_MEX_dict.secret_exam : false;

        // - set text last modified
                    const modifiedat = (data_dict) ? data_dict.modifiedat : null;  // PR20023-05-05
                    const modby_username = (data_dict) ? data_dict.modby_username : null;
                    el_MDEC_msg_modified.innerText = f_format_last_modified_txt(loc.Last_modified, modifiedat, modby_username);
                };

            }

            el_MDEC_header1.innerText = (mod_MEX_dict.is_addnew) ? loc.Add_CVTE_exam : mod_MEX_dict.exam_name;
            el_MDEC_header2.innerText = get_dep_lvl_examperiod_txt();

            add_or_remove_class(el_MDEC_btn_delete, cls_hide, mod_MEX_dict.is_addnew)

    // --- fill select table
            MDEC_FillSelectTableLevel();

            MDEC_enable_btn_save();
    // ---  show modal
            $("#id_mod_duo_exam_create").modal({backdrop: true});

        };
    }; // MDEC_Open

//=========  MDEC_Save  ================ PR2022-07-27
    function MDEC_Save(){
        console.log(" ===  MDEC_Save  =====") ;
        console.log( "mod_MEX_dict: ", mod_MEX_dict);

        if(permit_dict.permit_crud && permit_dict.requsr_role_admin){

            const upload_dict = {
                table: "duo_exam",
                mode: ((mod_MEX_dict.is_addnew) ? "create" : "update"),

                exam_pk: mod_MEX_dict.exam_pk,
                examyear_pk: mod_MEX_dict.examyear_pk,
                depbase_pk: mod_MEX_dict.depbase_pk,
                lvlbase_pk: mod_MEX_dict.lvlbase_pk,

                examtype: "duo",
                exam_pk: mod_MEX_dict.exam_pk,

                subject_pk: mod_MEX_dict.sel_subject_pk,
                subject_code: mod_MEX_dict.sel_subject_name,

                examperiod: mod_MEX_dict.examperiod,
                version: el_MDEC_input_version.value,
                secret_exam: el_MDEC_checkbox_secret_exam.checked,
            };
            UploadChanges(upload_dict, urls.url_exam_upload);
        };

// ---  hide modal
        $("#id_mod_duo_exam_create").modal("hide");
    }; //

//=========  MDEC_BtnSelectSubjectClick  ================ PR2022-08-27
    function MDEC_BtnSelectSubjectClick(el) {
        console.log("===== MDEC_BtnSelectSubjectClick =====");

        if (mod_MEX_dict.is_addnew){

        console.log("    duo_subject_dicts", duo_subject_dicts);
            // PR2023-03-20 was: t_MSSSS_Open(loc, "subject", subject_rows, false, false, setting_dict, permit_dict, MDEC_Response);
            t_MSSSS_Open_NEW (loc, "subject", duo_subject_dicts, false, false, setting_dict, permit_dict, MDEC_Response);
        };
    };

//=========  MDEC_SelectLevelChange  ================ PR2023-03-20
    function MDEC_SelectLevelChange(el_select) {
        console.log("===== MDEC_SelectLevelChange =====");

        mod_MEX_dict.lvlbase_pk = (el_select.value && Number(el_select.value)) ? Number(el_select.value) : null;
        MDEC_enable_btn_save();

    };  // MDEC_SelectLevelChange

//=========  MDEC_InputVersionChange  ================ PR2023-05-05
    function MDEC_InputVersionChange(el_input) {
        console.log("===== MDEC_InputVersionChange =====");

        mod_MEX_dict.version = (el_input.value) ? el_input.value : null;
        MDEC_enable_btn_save();
    };  // MDEC_InputVersionChange

//=========  MDEC_Response  ================ PR2022-08-27
    function MDEC_Response(tblName, selected_dict, selected_pk_int) {
        console.log("===== MDEC_Response =====");
        console.log("    tblName", tblName);
        console.log("    selected_dict", selected_dict);
        console.log("    selected_pk_int", selected_pk_int);

        mod_MEX_dict.sel_subject_pk = null;
        mod_MEX_dict.sel_subject_name = null;
        if (!isEmpty(selected_dict)){
            mod_MEX_dict.sel_subject_pk = selected_pk_int;
            mod_MEX_dict.sel_subject_name = selected_dict.name_nl;
        }
        el_MDEC_select_subject.innerText = mod_MEX_dict.sel_subject_name;

        MDEC_enable_btn_save();
    };  // MDEC_BtnSelectSubjectClick

//========= MDEC_FillSelectTableLevel  ============= PR2022-08-27
    function MDEC_FillSelectTableLevel() {
        console.log("===== MDEC_FillSelectTableLevel ===== ");
        console.log("    level_map", level_map);
        console.log("    mod_MEX_dict.lvlbase_pk", mod_MEX_dict.lvlbase_pk);

        if (el_MEXQ_select_level){
        // hide if not Vsbo
            add_or_remove_class(el_MDEC_select_level.parentNode, cls_hide, !setting_dict.sel_dep_level_req);
            el_MDEC_select_level.innerHTML = null;
            if (setting_dict.sel_dep_level_req){
                t_FillSelectOptions(el_MDEC_select_level, level_map, "base_id", "abbrev", false,
                    mod_MEX_dict.lvlbase_pk, null, loc.No_learningpaths_found, loc.Select_level)
            };
        };
    } // MDEC_FillSelectTableLevel

//=========  MDEC_ExamperiodCheckboxChange  ================ PR2022-08-27
    function MDEC_ExamperiodCheckboxChange(el_input) {
        console.log( "===== MDEC_ExamperiodCheckboxChange  ========= ");
        console.log( "el_input", el_input);

        if (el_input.checked) {
            mod_MEX_dict.examperiod = get_attr_from_el_int(el_input, "data-field")
        };
        const form_elements = el_MDEC_form_controls.querySelectorAll(".awp_input_checkbox")
        if (form_elements){
            for (let i = 0, el; el = form_elements[i]; i++) {
                const ep_int = get_attr_from_el_int(el, "data-field");
                 el.checked = (ep_int === mod_MEX_dict.examperiod);
            };
        };

        MEX_set_headertext1_examperiod();

        MDEC_enable_btn_save();
    };  // MDEC_ExamperiodCheckboxChange

    function MDEC_enable_btn_save() {  // PR2023-03-20
        console.log("===== MDEC_enable_btn_save =====");

        console.log("    mod_MEX_dict.sel_subject_pk", mod_MEX_dict.sel_subject_pk);
        console.log("    mod_MEX_dict.examperiod", mod_MEX_dict.examperiod);

        const enabled = (mod_MEX_dict.sel_subject_pk && mod_MEX_dict.examperiod ) &&
                        ( (setting_dict.sel_dep_level_req && mod_MEX_dict.lvlbase_pk) || (!setting_dict.sel_dep_level_req) ) &&
                (mod_MEX_dict.is_addnew || mod_MEX_dict.exam_pk);

        el_MDEC_btn_save.disabled = !enabled;
    };  // MDEC_enable_btn_save


///////////////////////////////////////
// +++++++++ MOD EXAM QUESTIONS ++++++++++++++++ PR2021-04-05 PR2021-05-22
    function MEXQ_Open(el_input){
        console.log(" ===  MEXQ_Open  =====") ;

// - reset mod_MEX_dict
        const is_addnew = (!el_input);
        const is_result_page = false;
        MEXQ_reset_mod_MEX_dict(is_addnew, is_result_page);

        // mod_MEX_dict.is_permit_admin gets value in MEXQ_reset_mod_MEX_dict
        // is_permit_admin = (permit_dict.requsr_role_admin && permit_dict.requsr_country_pk === 1 && permit_dict.permit_crud);
        if(mod_MEX_dict.is_permit_admin){
            // el_input is undefined when called by submenu btn 'Add new'

// ---  lookup ete_exam_dict in ete_exam_dicts
            const ete_exam_dict = get_datadict_from_table_element(el_input);
            const sel_subject_pk = (ete_exam_dict && ete_exam_dict.subj_id) ? ete_exam_dict.subj_id : null;
            const is_addnew = (!ete_exam_dict);

            console.log("    ete_exam_dict", ete_exam_dict) ;
            console.log("    sel_subject_pk", sel_subject_pk) ;
            console.log("    is_addnew", is_addnew) ;

            if (![1,2, 3].includes(setting_dict.sel_examperiod)) {
                b_show_mod_message_html(loc.Please_select_examperiod_sbr);

            } else if (setting_dict.sel_dep_level_req && !setting_dict.sel_lvlbase_pk) {
                b_show_mod_message_html(loc.Please_select_level_sbr);

            } else {
    // -- lookup selected.subject_pk in subject_rows and get sel_subject_dict
                MEX_get_subject(sel_subject_pk);
                MEX_get_ete_exam_dict_info(ete_exam_dict);

                MEX_FillDictPartex(ete_exam_dict);
                MEX_FillDictAssignment(ete_exam_dict);
                MEXQ_FillDictKeys(ete_exam_dict);

                MEXQ_FillTablePartex();

    // ---  set text last modified
                const modifiedat = (ete_exam_dict) ? ete_exam_dict.modifiedat : null;  // PR20023-05-04
                const modby_username = (ete_exam_dict) ? ete_exam_dict.modby_username : null;
                el_MEXQ_msg_modified.innerText = f_format_last_modified_txt(loc.Last_modified, modifiedat, modby_username);

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
                MEX_set_headertext2_subject();
                //el_MEXQ_header3_student.innerText = null //  header3_text

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
            };
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
        if (mod_MEX_dict.is_permit_admin){
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
                examtype: "ete",
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

        //console.log("found_dict", found_dict);
        if (!isEmpty(found_dict)){
            mod_MEX_dict.subject_pk = found_dict.id;
            //mod_MEX_dict.subject_dict = found_dict;
            mod_MEX_dict.subject_name = (found_dict.name_nl) ? found_dict.name_nl : null;
            mod_MEX_dict.subject_code = (found_dict.code) ? found_dict.code : null;
        }
    //console.log("    mod_MEX_dict", mod_MEX_dict);
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

            t_MSSSS_Open_NEW(loc, "subject", ete_subject_dicts, false, false, setting_dict, permit_dict, MSSSS_Response);
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
        console.log( "===== MEX_BtnTabClicked ========= ", btn);
        console.log( "mod_MEX_dict.partex_dict", mod_MEX_dict.partex_dict);

        if(btn){
            const data_btn = get_attr_from_el(btn,"data-btn");
            mod_MEX_dict.sel_tab = (data_btn) ? data_btn : "tab_start";
        }
    console.log( "mod_MEX_dict.sel_tab", mod_MEX_dict.sel_tab);

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
        console.log( "===== MEX_BtnPageClicked ========= ");

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
//========= MEXQ_reset_mod_MEX_dict  ============= PR2022-01-21
    function MEXQ_reset_mod_MEX_dict(is_addnew, is_result_page) {
        console.log("===== MEXQ_reset_mod_MEX_dict =====");

        const is_permit_admin = (permit_dict.requsr_role_admin && permit_dict.permit_crud);

        b_clear_dict(mod_MEX_dict);

        mod_MEX_dict.is_permit_admin = is_permit_admin;

        mod_MEX_dict.sel_tab = "tab_start";
        mod_MEX_dict.pge_index = 1;
        mod_MEX_dict.examyear_pk = setting_dict.sel_examyear_pk;
        mod_MEX_dict.depbase_pk = setting_dict.sel_depbase_pk;
        mod_MEX_dict.examperiod = setting_dict.sel_examperiod;

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
    };  // MEXQ_reset_mod_MEX_dict

//=========  MEX_FillDictPartex  ================ PR2022-01-21
    function MEX_FillDictPartex(exam_dict, grade_dict) {
        //console.log("===== MEX_FillDictPartex =====");
        //console.log("exam_dict", exam_dict);
        // called by MEXQ_Open and MEXA_Open
        // format of exam_dict.partex = [ partex_pk, examperiod, amount, max_score, partex_name]
        // format of partex_dict = { 1: {pk: 1, examperiod: 2, name: "Deelexamen 1", amount: 3, max_score: 0, a_dict: {}}}

        // PR2022-08-25 debug: when it is i copied exam from last year, exam_dict exists.
        // must also check if partex is null
        const is_addnew = (isEmpty(exam_dict) || exam_dict.partex == null);

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
        /*
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
        */
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
        console.log("===== MEXA_FillTablePartex =====");
        console.log("mod_MEX_dict.partex_dict", mod_MEX_dict.partex_dict);

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

//========= MEXQ_FillSelectTableLevel  ============= PR2021-05-07 PR2022-01-15
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
                    mod_MEX_dict.lvlbase_pk, null, loc.No_learningpaths_found, loc.Select_level)
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
        //console.log("===== MEXQ_ShowPartexInputEls =====");
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
        //console.log("mod_MEX_dict", mod_MEX_dict)

        let disable_save_btn = false;

        const is_locked = mod_MEX_dict.is_locked;
        const no_subject = !mod_MEX_dict.subject_pk;
        // no_level is only true when vsbo and no level
        const no_level = (setting_dict.sel_dep_level_req && !mod_MEX_dict.lvlbase_pk);
        // when has_partex: show el_MEXQ_input_scalelength, otherwise: show amount
        const show_input_scalelength = (mod_MEX_dict.has_partex);
        let multiple_exams_found = false;
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

        // skip when there are no other exams yet
            for (const data_dict of Object.values(ete_exam_dicts)) {
    // loop through exams
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
        //console.log( "mod_MEX_dict.sel_lvlbase_code", mod_MEX_dict.sel_lvlbase_code, typeof mod_MEX_dict.sel_lvlbase_code);
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

        //if (mod_MEX_dict.is_permit_same_school){
        //    MEXA_InputAnswer(el_input, event);
        //} else if(mod_MEX_dict.is_permit_admin){
            MEXQ_InputQuestion(el_input);
        //}
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

        console.log("    input_value: ", input_value)
            // lookup assignment, create if it does not exist
            const p_dict = mod_MEX_dict.partex_dict[partex_pk];
            if (!(q_number in p_dict.a_dict)){
                p_dict.a_dict[q_number] = {};
            };
            const q_dict = p_dict.a_dict[q_number];

// - split input_value in first charactes and the rest
            const first_char = input_value.charAt(0);
            const remainder = input_value.slice(1);

        console.log("    first_char: ", first_char)
        console.log("    remainder: ", remainder)
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

        console.log("    is_multiple_choice: ", is_multiple_choice)
        console.log(" >>   new_max_score_str: ", new_max_score_str)
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
//========= MEX_get_ete_exam_dict_info  ============= PR2021-05-23 PR2022-01-21 PR2023-05-05
    function MEX_get_ete_exam_dict_info(exam_dict) {
        //console.log("===== MEX_get_ete_exam_dict_info =====");
        //console.log("exam_dict", exam_dict);

        if(exam_dict) {
            mod_MEX_dict.exam_pk = exam_dict.id;
            mod_MEX_dict.version = (exam_dict.version) ? exam_dict.version : null;
            // examperiod: 1 = ce, 2 = reex, 12 = ce + reex
            mod_MEX_dict.examperiod = (exam_dict.examperiod) ? exam_dict.examperiod : 1;

            mod_MEX_dict.has_partex = (exam_dict.has_partex) ? exam_dict.has_partex : false;

            mod_MEX_dict.amount = (exam_dict.amount) ? exam_dict.amount : 0;
            mod_MEX_dict.scalelength = (exam_dict.scalelength) ? exam_dict.scalelength : null;

            // not necessary ??
                // mod_MEX_dict.department_pk = exam_dict.department_id;

            mod_MEX_dict.lvlbase_pk = exam_dict.lvlbase_id;
            mod_MEX_dict.lvl_abbrev = exam_dict.lvl_abbrev;

            mod_MEX_dict.is_locked = (permit_dict.requsr_role_admin && permit_dict.requsr_country_is_cur) ?
            // when admin curacao: lock exam when approved or published or locked
                    ( exam_dict.locked || !!exam_dict.auth1by_id || !!exam_dict.auth2by_id || !!exam_dict.published_id ) :
            // lock otherwise
                    true;
       };
       console.log( "    mod_MEX_dict", mod_MEX_dict);
       console.log( "    permit_dict.requsr_role_admin", permit_dict.requsr_role_admin);
       console.log( "    mod_MEX_dict.is_locked", mod_MEX_dict.is_locked);
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



//=========  MEX_set_headertext1_examperiod  ================ PR2022-05-16 PR2023-05-04
    function MEX_set_headertext1_examperiod() {
        //console.log("===== MEX_set_headertext1_examperiod =====");
    // ---  set header text
        const depbase_code = (setting_dict.sel_depbase_code) ? setting_dict.sel_depbase_code : "---";
        const examperiod_caption = (loc.examperiod_caption && mod_MEX_dict.examperiod) ? loc.examperiod_caption[mod_MEX_dict.examperiod] : "---"

        el_MEXQ_header1.innerText = [loc.ETE_exam, depbase_code, examperiod_caption].join(" ");
    };  // MEX_set_headertext1_examperiod

//=========  MEX_set_headertext2_subject  ================ PR2022-01-12
    function MEX_set_headertext2_subject() {
        //console.log("===== MEX_set_headertext2_subject =====");
        //console.log("mod_MEX_dict", mod_MEX_dict);
        //console.log("mod_MEX_dict.subject_name", mod_MEX_dict.subject_name);
        //console.log("mod_MEX_dict.lvl_abbrev", mod_MEX_dict.lvl_abbrev);

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


    console.log( "    p_dict: ", p_dict);
            const p_amount = p_dict.amount;
// ---  loop through all questions. Dont use "for (const q_dict of Object.values(p_dict.a_dict))" in case some q_dicts are missing
            for (let q = 1; q <= p_amount; q++) {
// ---  loop through mod_MEX_dict.partex_dict
                //q_dict = {max_char: 'C', max_score: 0, min_score: 0, keys: 'a', result: null}
                const q_dict = p_dict.a_dict[q];
    console.log( "    q_dict: ", q_dict);
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

    console.log( "    total_max_score: ", total_max_score);
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
// +++++++++ MOD DUO EXAMS ++++++++++++++++ PR2022-02-28 PR2023-03-18
    function MDUO_Open(el_input){
        console.log(" ===  MDUO_Open  =====") ;
        const is_permit_admin = (permit_dict.requsr_role_admin && permit_dict.permit_crud);
        if(is_permit_admin){

            console.log("    setting_dict.sel_dep_level_req", setting_dict.sel_dep_level_req) ;
            console.log("    setting_dict.sel_lvlbase_pk", setting_dict.sel_lvlbase_pk) ;

            if (![1,2, 3].includes(setting_dict.sel_examperiod)) {
                b_show_mod_message_html(loc.Please_select_examperiod_sbr);

            } else if (setting_dict.sel_dep_level_req && !setting_dict.sel_lvlbase_pk) {
                b_show_mod_message_html(loc.Please_select_level_sbr);

            } else {
                const depbase_txt = (setting_dict.sel_depbase_code) ? setting_dict.sel_depbase_code : " ---";
                const lvlbase_txt = (setting_dict.sel_dep_level_req && setting_dict.sel_lvlbase_pk) ? setting_dict.sel_lvlbase_code : "";

                const ep_int = setting_dict.sel_examperiod;
                const ep_dict = b_lookup_dict_in_dictlist(loc.options_examperiod_exam, "value", ep_int);
                const ep_txt =  (!isEmpty(ep_dict)) ? ep_dict.caption : "---";

                const header_txt = [loc.Link_CVTE_exams, "-", depbase_txt, lvlbase_txt, "-", ep_txt].join(" ");
                el_MDUO_header.innerHTML = header_txt

                MDUO_FillDict();
                MDUO_FillTables();
                el_MDUO_btn_save.disabled = true;
        // ---  show modal
                $("#id_mod_duoexams").modal({backdrop: true});
            }; //  if(is_permit_admin)
        };
    };  // MDUO_Open

//=========  MDUO_Save  ================ PR2022-04-06 PR2023-03-19
    function MDUO_Save(){
        console.log("===  MDUO_Save  =====") ;
        // save subject that have exam_id or ntb_id
        // - when exam_id has value and ntb_id = null: this means that ntb is removed
        // - when exam_id is null and ntb_id has value: this means that there is no exam record yet
        // - when exam_id and ntb_id both have value: this means that ntb_id is unchanged or chganegd
        const exam_list = [];
        if(mod_MDUO_dict.duo_subject_dicts){
            for (const data_dict of Object.values(mod_MDUO_dict.duo_subject_dicts)) {

                if (data_dict.exam_id || data_dict.ntb_id){
                    exam_list.push({
                        subj_id: data_dict.subj_id,
                        ntb_id: data_dict.ntb_id,
                        dep_pk: data_dict.dep_id,
                        level_pk: data_dict.lvl_id,
                        subj_name_nl: data_dict.subj_name_nl,
                        exam_id: data_dict.exam_id,
                        ntb_omschrijving: data_dict.ntb_omschrijving
                    });
                };
            };
        };
        if (exam_list.length) {
            const upload_dict = {
                examperiod: setting_dict.sel_examperiod,
                exam_list: exam_list
            };
// ---  upload changes
            const url_str = urls.url_duo_exam_upload;
            console.log("upload_dict", upload_dict) ;
            console.log("url_str", url_str) ;

            UploadChanges(upload_dict, url_str);
        };
        $("#id_mod_duoexams").modal("hide");
    };  // MDUO_Save

//=========  MDUO_FillDict  ================ PR2022-02-28 PR2023-03-19
    function MDUO_FillDict() {
        console.log("===== MDUO_FillDict =====");

        b_clear_dict(mod_MDUO_dict);

        mod_MDUO_dict.duo_subject_dicts = {};

        if(!isEmpty(duo_subject_dicts)){
            for (const [mapid, data_dict] of Object.entries(duo_subject_dicts)) {
                mod_MDUO_dict.duo_subject_dicts[mapid] = {
                    subj_id: data_dict.id,
                    subjbase_id: data_dict.subjbase_id,
                    subjbase_code: data_dict.code,
                    subj_name_nl: data_dict.name_nl,
                    lvl_id: data_dict.lvl_id,
                    lvlbase_id: data_dict.lvlbase_id,
                    lvl_abbrev: data_dict.lvl_abbrev,
                    dep_id: data_dict.dep_id,
                    depbase_id: data_dict.depbase_id,
                    depbase_code: data_dict.depbase_code,
                    exam_id: null,
                    ntb_id: null,
                    ntb_omschrijving: null
                };
            };
        };

        mod_MDUO_dict.ntermentable_dicts = {};
        if(!isEmpty(ntermentable_dicts)){
            for (const [mapid, data_dict] of Object.entries(ntermentable_dicts)) {
               mod_MDUO_dict.ntermentable_dicts[mapid] = {
                    ntb_id: data_dict.id,
                    leerweg: data_dict.leerweg,
                    n_term: data_dict.n_term,
                    nex_id: data_dict.nex_id,
                    ntb_omschrijving: data_dict.omschrijving,
                    opl_code: data_dict.opl_code,
                    sty_id: data_dict.sty_id,
                    tijdvak: data_dict.tijdvak,
                    exam_id: null,
                    subj_id: null,
                    subj_name_nl: null
                };
            };
        };

    // - loop through duo_exam_dicts, to check which subjects are already linked. Exam is linked when ntb_id has value
        if(!isEmpty(duo_exam_dicts)){
            for (const data_dict of Object.values(duo_exam_dicts)) {
                // show only DUO exams, is filtered on server

                // exam may exist, but without ntb_id. Put exam_id in duo_subject_dicts
                // exam always has subjbase_id, subj_id, depbase_id and dep_id

        // - lookup duo_subject_dict, add exam_id if found
                const duo_subject_dict = mod_MDUO_dict.duo_subject_dicts["subject_" + data_dict.subj_id];
                if (duo_subject_dict){
                    duo_subject_dict.exam_id = data_dict.id;
                // subject is linked when duo_exam_dict.ntb_id has value
                    duo_subject_dict.ntb_id = data_dict.ntb_id;
                    duo_subject_dict.ntb_omschrijving = data_dict.ntb_omschrijving;
                };

        // - lookup ntermentable_dict, put subj_id and subj_name_nl in ntermentable_dict
                // subject is linked when duo_exam_dict.ntb_id has value
                if (data_dict.ntb_id){
                    const ntermentable_dict = mod_MDUO_dict.ntermentable_dicts["ntermentable_" + data_dict.ntb_id];
                    if (ntermentable_dict){
                        duo_subject_dict.exam_id = data_dict.id;
                        ntermentable_dict.subj_id = data_dict.subj_id;
                        ntermentable_dict.subj_name_nl = data_dict.subj_name_nl;
                    };
                };
            };
        };

        console.log("    mod_MDUO_dict.duo_subject_dicts", mod_MDUO_dict.duo_subject_dicts);
        console.log("    mod_MDUO_dict.ntermentable_dicts", mod_MDUO_dict.ntermentable_dicts);
        console.log("    duo_exam_dicts", duo_exam_dicts);

    };  // MDUO_FillDict

//=========  MDUO_FillTables  ================ PR2023-03-18
    function MDUO_FillTables() {
        console.log( "===== MDUO_FillTables ========= ");

        el_MDUO_tblBody_subjects.innerText = null;
        el_MDUO_tblBody_ntermentable.innerText = null;
        el_MDUO_tblBody_linked.innerText = null;

        let has_linked_rows = false;

// ---  loop through duo_subject_dicts
        if(mod_MDUO_dict.duo_subject_dicts){

            for (const data_dict of Object.values(mod_MDUO_dict.duo_subject_dicts)) {
                if (data_dict.ntb_id){
                    has_linked_rows = true;
                    MDUO_FillSelectRow("linked", data_dict, el_MDUO_tblBody_linked);
                } else {
                    MDUO_FillSelectRow("subject", data_dict, el_MDUO_tblBody_subjects);
                };
            };
        };
        if (!has_linked_rows){
            const data_dict = {subj_id: 0, subj_name_nl: loc.No_linked_CVTE_exams }
            MDUO_FillSelectRow("linked", data_dict, el_MDUO_tblBody_linked);
        };

// ---  loop through ntermentable_dicts
        const mapped_nterm_level = {tkl: ["gl", "tl"], pkl: ["kb"], pbl: ["bb"]}
        if(mod_MDUO_dict.ntermentable_dicts){
            for (const data_dict of Object.values(mod_MDUO_dict.ntermentable_dicts)) {
                // skip linked rows
                if (!data_dict.subj_id){
                    MDUO_FillSelectRow("ntermentable", data_dict, el_MDUO_tblBody_ntermentable);
                };
            };
        };
    }; // MDUO_FillTables

//=========  MDUO_FillSelectRow  ================ PR2022-04-05
    function MDUO_FillSelectRow(tblName, data_dict, tblBody_select) {
        //console.log( "===== MDUO_FillSelectRow ========= ");
        //console.log( "    data_dict: ", data_dict);

//--- loop through data_map
        let pk_int = null, lvl_pk = null;
        let col_txt_list = [];

        const is_selected_pk = (mod_MDUO_dict.exam_pk != null && exam_pk_int === mod_MDUO_dict.exam_pk)

        let ob1 = "---";
        if (tblName === "subject") {
            pk_int = data_dict.subj_id;
            lvl_pk = data_dict.lvl_id;
            ob1 = (data_dict.subj_name_nl) ? data_dict.subj_name_nl : "---";
            col_txt_list = [ob1];

        } else if (tblName === "ntermentable") {
            pk_int = data_dict.ntb_id;
            ob1 = (data_dict.ntb_omschrijving) ? data_dict.ntb_omschrijving : "---";
            col_txt_list = [ob1];

        } else if (tblName === "linked") {
            pk_int = data_dict.subj_id;
            ob1 = (data_dict.subj_name_nl) ? data_dict.subj_name_nl : "---";
            const ntb_omschrijving = (data_dict.ntb_omschrijving) ? data_dict.ntb_omschrijving : "";
            col_txt_list = [ob1, ntb_omschrijving];
        };

// ---  lookup index where this row must be inserted
        const row_index = b_recursive_tblRow_lookup(tblBody_select, setting_dict.user_lang, ob1);

// ---  insert tblRow  //index -1 results in that the new row will be inserted at the last position.
        let tblRow = tblBody_select.insertRow(row_index);

        tblRow.setAttribute("data-pk", pk_int);
        tblRow.setAttribute("data-ob1", ob1);

        if (tblName === "ntermentable"){
            tblRow.title = ob1;
        } else if (tblName === "subject") {
             tblRow.title = data_dict.subj_name_nl;
        };

// - add class with background color
        const selected_class = (tblName === "linked") ? "awp_mod_exam_linked_selected" : "awp_mod_exam_selected" ;
        const default_class = (tblName === "linked") ? "awp_mod_exam_linked" : "awp_mod_exam";
        let just_linked_unlinked = false;
        if (tblName === "ntermentable"){
            if (mod_MDUO_dict.just_linked_ntb_id === pk_int){
                just_linked_unlinked = true;
                mod_MDUO_dict.just_linked_ntb_id = null;
            };
        } else {
            if (mod_MDUO_dict.just_linked_unlinked_subj_id === pk_int) {
                just_linked_unlinked = true;
                mod_MDUO_dict.just_linked_unlinked_subj_id = null;
            };
        };

        const cls_str = (is_selected_pk || just_linked_unlinked) ? selected_class : default_class;
        tblRow.classList.add(cls_str);
        // just_linked_unlinked will be highlighted for 1 second, remobeve highlighted after 1 second
        if (just_linked_unlinked){
            setTimeout(function () {
                add_or_remove_class (tblRow, default_class, true, selected_class);
            }, 1000);
        };
// ---  add EventListener to tblRow
        tblRow.addEventListener("click", function() {MDUO_handleTblrowClicked(tblName, tblRow)}, false )

        const col_width_list = (tblName === "subject") ? ["tw_280"] :
                               (tblName === "ntermentable") ? ["tw_320"] : ["tw_360", "tw_360"];

// loop through columns
        for (let i = 0, td, el_div, col_width; col_width = col_width_list[i]; i++) {
    // ---  add first td to tblRow.
            td = tblRow.insertCell(-1);
            td.classList.add(col_width)
            td.innerText = col_txt_list[i];
        };
    }  // MDUO_FillSelectRow

//=========  MDUO_handleTblrowClicked  ================ PR2022-04-06 PR2023-03-18
    function MDUO_handleTblrowClicked(tblName, tr_clicked) {
        //console.log( "===== MDUO_handleTblrowClicked ========= ");
        //console.log( "    tblName", tblName);  // "subject", "ntermentable", "linked"

        const tblBody_clicked = (tblName === "subject") ? el_MDUO_tblBody_subjects :
                                (tblName === "ntermentable") ? el_MDUO_tblBody_ntermentable : el_MDUO_tblBody_linked;

        if (tblName === "linked"){
            add_or_remove_class (tr_clicked, "awp_mod_exam_linked_selected", true, "awp_mod_exam_linked");
            setTimeout(function () {
                MDUO_unlink_exam(tr_clicked);
            }, 350);
        } else {
            const tblBody_other = (tblName === "subject") ? el_MDUO_tblBody_ntermentable :
                                  (tblName === "ntermentable") ? el_MDUO_tblBody_subjects : null;

    // ---  check if clicked row is already selected
            const tr_clicked_is_selected = (!!get_attr_from_el(tr_clicked, "data-selected", false));

    // ---  check if other row is selected
            const tr_other_selected = (tblBody_other) ? tblBody_other.querySelector("[data-selected=true]") : null;
            const tr_other_is_selected = (!!tr_other_selected);

    // - first deselect all rows in tblBody_clicked
            MDUO_deselect_selected_tblrows(tblBody_clicked);

    // - unselect if tr_clicked is selected - happens in deselect all rows
            if(!tr_clicked_is_selected){

    // - select tr_clicked if tr_clicked and tr_other are not selected
                tr_clicked.setAttribute("data-selected", true);
                for (let i = 0, td; td = tr_clicked.children[i]; i++) {
                    add_or_remove_class (td, "awp_mod_exam_selected", true, "awp_mod_exam")
                };

    // - link subject if tr_clicked is not selected and tr_other is selected
                if(tr_other_is_selected){
                    setTimeout(function () {
                        MDUO_link_exam(tr_clicked, tr_other_selected);
                    }, 350);
                };
            };
        };
    };  // MDUO_handleTblrowClicked

//=========  MDUO_unlink_exam  ================ PR2023-03-19
    function MDUO_unlink_exam(tr_clicked){
        //console.log(" =====  MDUO_unlink_exam  ======")

        tr_clicked.removeAttribute("data-selected");

        const subj_pk_str = get_attr_from_el(tr_clicked, "data-pk");
        const subject_dict = mod_MDUO_dict.duo_subject_dicts["subject_" + subj_pk_str];

        if (subject_dict){
            const ntb_id = subject_dict.ntb_id;
            const ntermentable_dict = mod_MDUO_dict.ntermentable_dicts["ntermentable_" + subject_dict.ntb_id];

            if (ntermentable_dict){
                ntermentable_dict.exam_id = null;
                ntermentable_dict.subj_id = null;
                ntermentable_dict.subj_name_nl = null;
            };
            subject_dict.ntb_id = null;
            subject_dict.ntb_omschrijving = null;

            mod_MDUO_dict.just_linked_unlinked_subj_id = subject_dict.subj_id;
            mod_MDUO_dict.just_linked_ntb_id = ntb_id;
        };

        el_MDUO_btn_save.disabled = false;

        MDUO_FillTables();
    };  // MDUO_unlink_exam

//=========  MDUO_link_exam  ================ PR2022-04-06 PR2023-03-19
    function MDUO_link_exam(tr_clicked, tr_other_selected){
        //console.log(" =====  MDUO_link_exam  ======") ;

        const tbl_clicked = tr_clicked.parentNode;
        const tbl_other = tr_other_selected.parentNode;

        const tbl_clicked_is_subjects = (tbl_clicked.id === "id_MDUO_tblBody_subjects");

        const subj_pk_str = get_attr_from_el((tbl_clicked_is_subjects) ? tr_clicked : tr_other_selected, "data-pk");
        const ntb_pk_str  = get_attr_from_el((tbl_clicked_is_subjects) ? tr_other_selected : tr_clicked, "data-pk");

        const subject_dict = mod_MDUO_dict.duo_subject_dicts["subject_" + subj_pk_str];
        const ntermentable_dict = mod_MDUO_dict.ntermentable_dicts["ntermentable_" + ntb_pk_str];

// deselect highlighted items
        setTimeout(function (){
            MDUO_deselect_selected_tblrows(el_MDUO_tblBody_subjects);
            MDUO_deselect_selected_tblrows(el_MDUO_tblBody_ntermentable);
            MDUO_deselect_selected_tblrows(el_MDUO_tblBody_linked);
        }, 500);

// get info from subject_list and nterm_list
        if (subject_dict && ntermentable_dict){
            ntermentable_dict.exam_id = subject_dict.exam_id;
            ntermentable_dict.subj_id = subject_dict.subj_id;
            ntermentable_dict.subj_name_nl = subject_dict.subj_name_nl;

            subject_dict.ntb_id = ntermentable_dict.ntb_id;
            subject_dict.ntb_omschrijving = ntermentable_dict.ntb_omschrijving;

            mod_MDUO_dict.just_linked_unlinked_subj_id = subject_dict.subj_id;

            el_MDUO_btn_save.disabled = false;

            MDUO_FillTables();
        };
    };  // MDUO_link_exam

//=========  MDUO_select_tblrow  ================ PR2023-03-19
    function MDUO_select_tblrow(tr_clicked){
        tr_clicked.setAttribute("data-selected", true);
        for (let i = 0, td; td = tr_clicked.children[i]; i++) {
            add_or_remove_class (td, "awp_mod_exam_selected", true, "awp_mod_exam")
        };
    };  // MDUO_select_tblrow

//=========  MDUO_deselect_selected_tblrows  ================ PR2023-03-19
    function MDUO_deselect_selected_tblrows(tblBody){
        console.log("==========  MDUO_deselect_selected_tblrows ========== ");
        console.log("    tblBody", tblBody);
        if (tblBody){
            const selected_tablerows = tblBody.querySelectorAll("[data-selected=true]")
        console.log("    selected_tablerows", selected_tablerows);
            if (selected_tablerows){
                for (let i = 0, row; row = selected_tablerows[i]; i++) {
                    row.removeAttribute("data-selected");
                    for (let i = 0, td; td = row.children[i]; i++) {
                        add_or_remove_class (td, "awp_mod_exam", true, "awp_mod_exam_selected")
        }}}};
    };  // MDUO_deselect_selected_tblrows


//////////////////////////
//========= MDUO_LinkColumns  ===================================== PR2020-12-29
    function MDUO_LinkColumns(tbodyTblName, tbodyAEL, row_clicked_id, row_other_id, row_clicked_key, row_other_key) {
        console.log("==========  MDUO_LinkColumns ========== ", tbodyTblName, tbodyAEL);
        // function adds 'excCol' to awp_columns and 'awpCaption' to excel_coldefs
        console.log("row_clicked_id", row_clicked_id, "row_other_id", row_other_id);
        console.log("row_clicked_key", row_clicked_key, "row_other_key", row_other_key);
        // row_clicked_id =  'id_tr_sector_exc_1'   row_other_id = 'id_tr_sector_awp_1'
        // row_clicked_key = 'EM'  row_other_key =  '5'

console.log("    mimp.import_table", mimp.import_table);
// --- get JustLinkedAwpId from row_clicked_id or row_other_id, depends on which row is clicked
        const JustLinkedAwpId = (tbodyAEL === "awp") ? row_clicked_id : (tbodyAEL === "exc") ? row_other_id : null;
        //console.log("JustLinkedAwpId", JustLinkedAwpId);

// --- get awp / exc key. WHen tbl = 'coldef' key is coldef, otherwise excValue -= value and awpValue = awpBasePk
        // awp_row_key = '5'  excel_row_key  = 'EM'

        const awp_rows = (tbodyTblName === "coldef") ? mimp_stored.coldefs : mimp.linked_awp_values[tbodyTblName];
        const excel_rows = (tbodyTblName === "coldef") ? mimp.excel_coldefs : mimp.linked_exc_values[tbodyTblName];

        console.log("awp_rows",  awp_rows);
        console.log("excel_rows", excel_rows);

        // awp_row = {awpColdef: "birthdate", caption: "Geboortedatum", datefield: true, excColdef: "GEB_DAT", excColIndex: 9}
        // awp_row = {awpBasePk: 5, awpValue: "e&m", excColIndex: 1, excValue: "EM"}
        const awp_key  = (tbodyTblName === "coldef") ? "awpColdef" :  "awpBasePk";
        const awp_row_key = (tbodyAEL === "awp") ? row_clicked_key : (tbodyAEL === "exc") ? row_other_key : null;
        const awp_row = get_arrayRow_by_keyValue (awp_rows, awp_key, awp_row_key);

        // excel_row = {excColIndex: 9, excColdef: "GEB_DAT", awpColdef: "birthdate", awpCaption: "Geboortedatum"}
        // excel_row = {excColIndex: 1, excValue: "EM", awpBasePk: 5, awpValue: "e&m"}
        const exc_key  = (tbodyTblName === "coldef") ? "excColdef" :  "excValue";
        const excel_row_key = (tbodyAEL === "awp") ? row_other_key : (tbodyAEL === "exc") ? row_clicked_key : null;
        const excel_row = get_arrayRow_by_keyValue (excel_rows, exc_key, excel_row_key);

        console.log("awp_row",  awp_row);
        console.log("excel_row", excel_row);
// --- add linked info to other row
        if(awp_row && excel_row){
            if(!!awp_row.awpColdef){excel_row.awpColdef = awp_row.awpColdef};
            if(!!awp_row.awpBasePk){excel_row.awpBasePk = awp_row.awpBasePk};
            if(!!awp_row.awpValue){excel_row.awpValue = awp_row.awpValue};
            if(!!awp_row.caption){excel_row.awpCaption = awp_row.caption};

            if(!!excel_row.excColdef){awp_row.excColdef = excel_row.excColdef};
            if(!!excel_row.excColIndex){awp_row.excColIndex = excel_row.excColIndex};
            if(!!excel_row.excValue){awp_row.excValue = excel_row.excValue};
        }

        console.log("mimp.linked_awp_values",  deepcopy_dict(mimp.linked_awp_values));
        console.log("mimp.linked_exc_values", deepcopy_dict(mimp.linked_exc_values));

        UploadImportSetting(tbodyTblName);

// ---  fill lists with linked values
        // must fill exccelvalues list again, after linking sector, profiel, level, department
        // PR2022-08-21 debug : NOT when linking subjects!!
        //??? >> ??? FillExcelValueLists(true);  // true = link_same_names

// ---  update AEL-tables
        Fill_AEL_Tables(JustLinkedAwpId);

        MIMP_HighlightAndDisableButtons();
    };  // MDUO_LinkColumns

//========= MDUO_UnlinkColumns ===================================== PR2020-12-29
    function MDUO_UnlinkColumns(tbodyTblName, tbodyAEL, row_clicked_id, row_clicked_key) {
        console.log("==========  MDUO_UnlinkColumns ========== ", tbodyTblName, tbodyAEL);
        // function deletes attribute 'excColdef' from awp_columns
        // and deletes attributes 'awpColdef' and 'awpCaption' from excel_coldefs

        console.log("row_clicked_id", row_clicked_id);
        console.log("row_clicked_key", row_clicked_key);
        // row_clicked_id:   id_tr_level_awp_1
        // row_clicked_key:  '2' (awpBasePk)

        const awp_rows = (tbodyTblName === "coldef") ? mimp_stored.coldefs : mimp.linked_awp_values[tbodyTblName];
        const excel_rows = (tbodyTblName === "coldef") ? mimp.excel_coldefs : mimp.linked_exc_values[tbodyTblName];

        const JustUnLinkedAwpId = row_clicked_id;

        // in unlink: row_clicked_key = awpColdef
        // stored_coldef: {awpColdef: "examnumber", caption: "Examennummer", linkfield: true, excColdef: "exnr"}
        // excel_coldefs: {index: 1, excColdef: "exnr", awpColdef: "examnumber", awpCaption: "Examennummer"}
        let excel_row = null, JustUnlinkedExcId = null;
        //let awp_row = get_arrayRow_by_keyValue (awp_rows, "awpColdef", row_clicked_key);

        // awp_row = {awpColdef: "birthdate", caption: "Geboortedatum", datefield: true, excColdef: "GEB_DAT", excColIndex: 9}
        // awp_row = {awpBasePk: 5, awpValue: "e&m", excColIndex: 1, excValue: "EM"}
        const awp_key = (tbodyTblName === "coldef") ? "awpColdef" :  "awpBasePk";
        const awp_row = get_arrayRow_by_keyValue (awp_rows, awp_key, row_clicked_key);

        const exc_key = (tbodyTblName === "coldef") ? "excColdef" :  "excValue";
        // excel_row =  {index: 8, excColdef: "geboorte_land", awpColdef: "birthcountry", awpCaption: "Geboorteland"}
        if (!!awp_row && !!awp_row[exc_key]) {
// ---  look up excColdef in excel_coldefs
            excel_row = get_arrayRow_by_keyValue (excel_rows, exc_key, awp_row[exc_key]);

        //console.log("awp_row", awp_row);
        //console.log("excel_row", excel_row);

// ---  delete excColdef, excColIndex, excValue from awp_row
             if(!!awp_row.excColdef){ delete awp_row.excColdef};
             if(!!awp_row.excColIndex){ delete awp_row.excColIndex};
             if(!!awp_row.excValue){ delete awp_row.excValue};

            if (!!excel_row) {
                //JustUnlinkedExcId = get_AEL_rowId(tbodyTblName, "exc", excel_row.excColIndex);
                JustUnlinkedExcId = excel_row.rowId;
// ---  delete awpColdef, awpBasePk, awpValue, caption from excel_row]
                if(!!excel_row.awpColdef){ delete excel_row.awpColdef};
                if(!!excel_row.awpBasePk){ delete excel_row.awpBasePk};
                if(!!excel_row.awpValue){ delete excel_row.awpValue};
                if(!!excel_row.awpCaption){ delete excel_row.awpCaption};
            }
        }  // if (!!awp_row)

// ---  upload new settings
        UploadImportSetting(tbodyTblName);

        //console.log("JustUnLinkedAwpId", JustUnLinkedAwpId);
        //console.log("JustUnlinkedExcId", JustUnlinkedExcId);
// ---  fill lists with linked values and update AEL-tables
        //FillExcelValueLists();
        Fill_AEL_Tables(null, JustUnLinkedAwpId, JustUnlinkedExcId);

        MIMP_HighlightAndDisableButtons();
    }  // MDUO_UnlinkColumns

////////////////////
    function get_ndsl_pk(nterm_pk, dep_pk, subject_pk, level_pk ){
        return ["N", nterm_pk, "D", dep_pk, "S", subject_pk, "L", (level_pk) ? level_pk : ""].join("");
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
    function MDNT_Open (open_mode ) {  // PR2022-02-25 PR 2023-03-29
        console.log("===  MDNT_Open  =====") ;
        // put locale info in global variable mimp_loc
        mimp_loc = loc;
        // disable  el_MDNT_btn_save, reset textbox
        el_MDNT_btn_save.disabled = true;
        //el_MDNT_filename.innerText = null;
        $("#id_mod_import_dnt").modal({backdrop: true});
    };

//////////////////////////////////////////////
//========= MOD APPROVE SUBMIT EXAMS ====================================
    function MASE_Open(mode ) {  // PR2022-03-10
        console.log("===  MASE_Open  =====") ;
        console.log("mode", mode) ;
        console.log("setting_dict", setting_dict) ;
        // modes are: "approve_admin", "submit_admin", "approve_school", "submit_school"
        const is_approve_mode = (mode.includes("approve"));
        const is_submit_mode = (mode.includes("submit"));
        const is_admin_mode = (mode.includes("admin"));
        const is_school_mode = (mode.includes("school"));

        b_clear_dict(mod_MASE_dict);

// check sel_examperiod
        // PR2022-04-24 debug when school: set sel_examperiod to firstperiod when not filled in
        if (is_school_mode && ![1, 2, 3].includes(setting_dict.sel_examperiod) ){
            setting_dict.sel_examperiod = 1
// ---  upload new setting
            const upload_dict = {selected_pk: {sel_examperiod: setting_dict.sel_examperiod}};
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);
        };
        if (![1, 2, 3].includes(setting_dict.sel_examperiod) ){
            b_show_mod_message_html(loc.Please_select_examperiod);

        } else {

// put examperiod in el_MASE_examperiod
            el_MASE_examperiod.innerText = (setting_dict.sel_examperiod === 1) ? loc.Central_exam :
                                    (setting_dict.sel_examperiod === 2) ? loc.Re_examination :
                                    (setting_dict.sel_examperiod === 3) ? loc.Re_examination_3rd_period : null;

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
                                        (is_approve_mode && permit_dict.permit_approve_exam) : false;
            mod_MASE_dict.has_permit = mod_MASE_dict.permit_admin || mod_MASE_dict.permit_same_school;

            console.log("mod_MASE_dict.has_permit", mod_MASE_dict.has_permit) ;
            console.log("mod_MASE_dict.auth_index", mod_MASE_dict.auth_index) ;
            if (mod_MASE_dict.has_permit && mod_MASE_dict.auth_index){
                mod_MASE_dict.step = -1; // gets value 1 in MASE_Save

// --- get header_txt and subheader_txt
                const header_txt = (is_approve_mode) ? loc.Approve_exams :
                                 (mod_MASE_dict.permit_admin) ? loc.Publish_exams : "---";
                el_MASE_header.innerText = header_txt;

                // note: must use loc.MASE_info, not loc.MASE_info
                const subheader_txt = (is_approve_mode) ? loc.MASE_info.subheader_approve :
                           (is_submit_mode && mod_MASE_dict.permit_admin) ? loc.MASE_info.subheader_publish : null;
                el_MASE_subheader.innerText = subheader_txt;

// get subject_text
                let subject_text = null;
                if(setting_dict.sel_subject_pk){
                    const data_dict = b_get_datadict_by_integer_from_datarows(subject_rows, "id", setting_dict.sel_subject_pk)
                    subject_text =  (data_dict.name_nl) ? data_dict.name_nl : "---"
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

        const has_permit = ((permit_dict.requsr_role_admin && permit_dict.permit_approve_exam) ||
                            (permit_dict.requsr_role_admin && permit_dict.publish_exam));
    console.log("has_permit", has_permit) ;

        if (has_permit) {

            mod_MASE_dict.is_reset = (save_mode === "delete");

            mod_MASE_dict.step += 1;

    console.log("mod_MASE_dict.is_approve_mode", mod_MASE_dict.is_approve_mode) ;
    console.log("mod_MASE_dict.is_submit_mode", mod_MASE_dict.is_submit_mode) ;
    console.log("mod_MASE_dict.step", mod_MASE_dict.step) ;

            //  upload_dict.modes are: 'approve_test', 'approve_save', 'approve_reset', 'submit_test', 'submit_save'
            let url_str = urls.url_approve_publish_exam;
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

// ---  info_container, loader, info_verifcode and input_verifcode
        let msg_info_txt = null, show_loader = false;
        let show_info_request_verifcode = false, show_input_verifcode = false;
        let show_delete_btn = false;
        let disable_save_btn = false, save_btn_txt = null;

        if (response && response.approve_msg_html) {
            mod_MASE_dict.msg_html = response.approve_msg_html;
        };

    console.log("  >> step:", step);

        if (step === 0) {
            // step 0: when form opens and request to check is sent to server
            // tekst: 'The subjects of the candidates are checked'
            msg_info_txt = loc.MASE_info.checking_exams;
            show_loader = true;
        } else {
            if(mod_MASE_dict.is_approve_mode){
    // --- is approve
                if (step === 1) {
                // response with checked exams
                // msg_info_txt is in response
                    show_delete_btn = mod_MASE_dict.has_already_approved;
                    if (mod_MASE_dict.test_is_ok){
                        save_btn_txt = loc.MASE_info.Approve_exams;
                    };
                } else if (step === 2) {
                    // clicked on 'Approve'
                    msg_info_txt = (is_reset) ? loc.MASE_info.removing_approval_exams : loc.MASE_info.approving_exams;
                    show_loader = true;
                } else if (step === 3) {
                    // response 'approved'
                    // msg_info_txt is in response
                };
            } else {
    // --- is submit
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
                    msg_info_txt = loc.MASE_info.sending_verifcode;
                    show_loader = true;
                } else if (step === 3) {
                    // response 'email sent'
                    // msg_info_txt is in response
                    show_info_request_verifcode = mod_MASE_dict.test_is_ok;
                    show_input_verifcode = true;
                    disable_save_btn = !el_MASE_input_verifcode.value;
                    save_btn_txt = loc.Publish_exams;
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
                ((permit_dict.requsr_role_admin) ? loc.MASE_info.to_publish_exams : "");
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
        el_confirm_loader.classList.add(cls_hide);
        el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");
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


//=========  ModConfirm_link_exam_to_grades_Open  ================ PR2022-05-19 PR2022-06-14  PR2023-05-02
    function ModConfirm_link_exam_to_grades_Open() {
        console.log(" -----  ModConfirm_link_exam_to_grades_Open   ----")

        // values of mode are : "delete", 'json', 'copy', 'save'
        // values of table are : "ete_exam" "duo_exam" 'duo_grade_exam'

        mod_dict = {mode: "link_exam_to_grades"};
        if (permit_dict.permit_crud && permit_dict.requsr_role_admin) {

            let has_selected_item = false;

    // ---  get header_text
            const header_text = loc.Link_exam_to_grades;

            const tblName = get_tblName_from_selectedBtn();

            mod_dict.table = tblName;

// ---  lookup exam_dict in exam_rows
            const data_dicts = get_datadicts_from_sel_btn();
            const exam_dict = (data_dicts && selected.map_id && data_dicts.hasOwnProperty(selected.map_id)) ? data_dicts[selected.map_id] : null;
console.log("exam_dict", exam_dict);

    // ---  create mod_dict
            has_selected_item = (!isEmpty(exam_dict));
            if(has_selected_item){
                mod_dict.depbase_pk = setting_dict.sel_depbase_pk;
                mod_dict.mapid = exam_dict.mapid;
                mod_dict.exam_pk = exam_dict.id;
                mod_dict.examyear_pk = exam_dict.ey_id;
                mod_dict.subject_pk = exam_dict.subj_id;
                mod_dict.subj_name_nl = exam_dict.subj_name_nl;
            };
//console.log("mod_dict", mod_dict);
    // ---  put text in modal form

            const msg_html = (!has_selected_item) ? ["<p class='pb-2'>", loc.No_exam_selected, "</p>"].join("") : null;

            const btn_save_txt = (has_selected_item) ? loc.Yes_link : loc.OK;
            const btn_cancel_txt = (has_selected_item) ? loc.No_cancel : loc.Close;

            el_confirm_header.innerText = header_text;

            el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");
            el_confirm_msg_container.innerHTML = msg_html;

            el_confirm_btn_save.innerText = btn_save_txt;

            add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", false, "btn-primary");
            add_or_remove_class (el_confirm_btn_save, cls_hide, !has_selected_item);
            el_confirm_btn_cancel.innerText = btn_cancel_txt;

    // show loader, disable save btn
            el_confirm_btn_save.disabled = true;
            add_or_remove_class(el_confirm_loader, cls_hide, !has_selected_item)

    // test link
            const upload_dict = { mode: "link_exam_to_grades",
                                   exam_pk: mod_dict.exam_pk,
                                   examyear_pk: mod_dict.examyear_pk,
                                   subject_pk: mod_dict.subject_pk,
                                   subj_name_nl: mod_dict.subj_name_nl,
                                   exam_examyear_pk: mod_dict.exam_examyear_pk,
                                   is_test: true
                                };

            UploadChanges(upload_dict, urls.url_link_exam_to_grades);
            // mod_dict.save_value prevents putting back the old value in el_input
            mod_dict.dont_rest_input_value = true;

    // set focus to cancel button
            setTimeout(function (){
                el_confirm_btn_cancel.focus();
            }, 500);

    // show modal
            $("#id_mod_confirm").modal({backdrop: true});

        };  //  if (permit_dict.permit_crud && permit_dict.requsr_role_admin )

    };  // ModConfirm_link_exam_to_grades_Open

//=========  ModConfirm_Cesuur_Nterm_Open  ================ PR2022-05-19
    function ModConfirm_Cesuur_Nterm_Open(mode, el_input) {
            console.log(" -----  ModConfirm_Cesuur_Nterm_Open   ----")
        if (permit_dict.permit_crud && permit_dict.requsr_role_admin) {
            let hide_save_btn = false, has_selected_item = false;

    // ---  put text in modal form
            const msg_list = [];
            if (mode === "cesuur"){
                msg_list.push( ["<p class='pb-2'>", loc.Enter_cesuur_01,
                                (mod_dict.cesuur) ? mod_dict.cesuur : '-',
                                loc.Enter_cesuur_02, "</p><p>",
                                "&emsp;", mod_dict.exam_name, "</p><p class='py-2'>",
                                loc.Enter_cesuur_03, "</p>"].join("")
                            );
            } else if (mode ===  "nterm"){
                msg_list.push( ["<p class='pb-2'>", loc.Enter_nterm_01,
                                (mod_dict.nterm) ? mod_dict.nterm : '-',
                                loc.Enter_cesuur_02, "</p><p>",
                                "&emsp;", mod_dict.exam_name, "</p><p class='py-2'>",
                                loc.Enter_cesuur_03, "</p>"].join("")
                            );
            }
            msg_list.push("<p>" + loc.Do_you_want_to_continue + "</p>")
            const msg_html = msg_list.join("");

            const header_text = (mode ===  "nterm") ? loc.Enter_nterm : loc.Enter_cesuur;
            const btn_cancel_txt = loc.No_cancel;
            const btn_save_txt = loc.Yes_save;

            el_confirm_header.innerText = header_text;
            el_confirm_loader.classList.add(cls_hide);
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
    };  // ModConfirm_Cesuur_Nterm_Open

//=========  On close ModConfirm  ================ PR2022-05-19
    $('#id_mod_confirm').on('hide.bs.modal', function (e) {
        try {
            if (["cesuur", "nterm"].includes(mod_dict.mode) && !mod_dict.dont_rest_input_value)
                if (mod_dict.el_input ){
                    mod_dict.el_input.value = mod_dict.old_value
                }
         } catch (error) {
        }
    });


//=========  ModConfirmOpen_delete  ================ PR2023-05-04
    function ModConfirmOpen_delete(table, el_input) {
        console.log(" -----  ModConfirmOpen   ----")
        // values of table are : "ete_exam" "duo_exam"

        b_clear_dict(mod_dict);

        if (permit_dict.permit_crud && permit_dict.requsr_role_admin) {

            const header_text = (table === "duo_exam") ? loc.Delete_CVTE_exam : loc.Delete_ETE_exam;

            // tblRow is undefined when clicked on delete btn in submenu
            const tblRow = t_get_tablerow_selected(el_input);
            const tblName = (tblRow) ? get_attr_from_el(tblRow, "data-table") : table;
            const selected_mapid =  (tblRow) ? tblRow.id : selected.map_id;

            const data_dicts = (tblName === "duo_exam") ? duo_exam_dicts : ete_exam_dicts;
            const data_dict = (data_dicts.hasOwnProperty(selected_mapid)) ? data_dicts[selected_mapid] : null;

    console.log("    data_dicts", data_dicts)
    console.log("    selected_mapid", selected_mapid)
    console.log("    data_dict", data_dict)

            const header_txt = (tblName === "duo_exam") ? loc.Delete_CVTE_exam : loc.Delete_ETE_exam;
            if (!data_dict){
                b_show_mod_message_html(loc.No_exam_selected, header_txt);
            } else if (data_dict.published_id) {
                const msg_txt = loc.Exam_is_published + "<br>" + loc.Remove_publication_first;
                b_show_mod_message_html(msg_txt, header_txt);
            } else {

                mod_dict.mode = "delete";
                mod_dict.examyear_pk = setting_dict.sel_examyear_pk;
                mod_dict.depbase_pk = setting_dict.sel_depbase_pk;
                mod_dict.mapid = data_dict.mapid;
                mod_dict.exam_pk = data_dict.id;
                mod_dict.department_id = data_dict.department_id;
                mod_dict.subject_pk = data_dict.subj_id;
                mod_dict.subj_name_nl = data_dict.subj_name_nl;
                mod_dict.exam_name = data_dict.exam_name;

                const msg_html = ["<p class='pb-2'>",
                            (table === "duo_exam") ? loc.CVTE_exam : loc.ETE_exam,
                            " '", mod_dict.exam_name, "'",
                            loc.will_be_deleted, "</p><p class='py-2'>",
                        loc.Do_you_want_to_continue, "</p>"].join("");;

                el_confirm_loader.classList.add(cls_hide);

                el_confirm_header.innerText = header_text;

                el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");
                el_confirm_msg_container.innerHTML = msg_html;

                el_confirm_btn_save.innerText = loc.Yes_delete;
                add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", true, "btn-primary");
                add_or_remove_class (el_confirm_btn_save, cls_hide, false);
                el_confirm_btn_cancel.innerText = loc.No_cancel;

        // set focus to cancel button
                setTimeout(function (){
                    el_confirm_btn_cancel.focus();
                }, 500);

        // show modal
                $("#id_mod_confirm").modal({backdrop: true});
            };
        };
    };  // ModConfirmOpen_delete

//=========  ModConfirmOpen  ================ PR2021-05-06 PR2022-06-02 PR2023-03-20
    function ModConfirmOpen(table, mode, el_input) {
        console.log(" -----  ModConfirmOpen   ----")
        console.log("    mode", mode)
        console.log("    table", table)
        // values of mode are : "delete", 'json', 'copy', 'copy_ntermen', 'save' 'undo_published'
        // values of table are : "exam" (when delete exam), "ete_exam" "duo_exam" 'duo_grade_exam' "results"
        // TODO print_exam not in use: remove, add 'publish'

        const is_delete = (mode === "delete");
        const is_copy = (mode === "copy");
        const is_undo_published = (mode === "undo_published");
        mod_dict = {mode: mode};

        let hide_save_btn = false, has_selected_item = false;
        let msg_html = "";
        let header_text = null;
        let btn_save_txt = loc.Save, btn_cancel_txt = loc.Cancel;

        if (permit_dict.permit_crud && permit_dict.requsr_role_admin) {

            if (mode === "copy_ntermen"){
                header_text = loc.Copy_ntermen_to_exams;
                msg_html = ["<div class='pb-2'>", loc.Ntermen_will_be_copied, "</div>",
                                    "<div class='py-2'>", loc.Do_you_want_to_continue, "</div>"].join("");
                btn_save_txt = loc.Yes_copy;
                btn_cancel_txt = loc.No_cancel;
    // ---  get header_text
            } if (mode === "json"){
                header_text = loc.Download_JSON;

                if (loc.examperiod_caption && setting_dict.sel_examperiod) {
                    header_text += " - " + loc.examperiod_caption[setting_dict.sel_examperiod];
                };
        // ---  put text in modal form
                let dep_lvl_str = setting_dict.sel_depbase_code;
                if (setting_dict.sel_dep_level_req){
                    const lvl_str = (setting_dict.sel_lvlbase_pk) ? setting_dict.sel_lvlbase_code : loc.All_levels;
                    dep_lvl_str += " - " + lvl_str;
                }
                const subject_name = (setting_dict.sel_subject_pk) ?
                                    (setting_dict.sel_subject_name) ? setting_dict.sel_subject_name : "---" : loc.All_subjects;
                msg_html = ["<div class='pb-2'>", loc.JSON_will_be_downloaded, "</div>",
                                    "<div>&emsp;", dep_lvl_str, "</div>",
                                    "<div>&emsp;", subject_name, "</div>",
                                    "<div class='py-2'>", loc.Do_you_want_to_continue, "</div>"].join("");

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
                              (table === "duo_exam") ? loc.Delete_CVTE_exam : loc.Delete_ETE_exam;

                let tblName = null, selected_pk = null;
                // tblRow is undefined when clicked on delete btn in submenu btn or form (no inactive btn)
                const tblRow = t_get_tablerow_selected(el_input);

        console.log("    tblRow", tblRow)
                if(tblRow){
                    tblName = get_attr_from_el(tblRow, "data-table")
                    selected_pk = get_attr_from_el(tblRow, "data-pk")
                } else {
                    tblName = table;
                    selected_pk = setting_dict.sel_exam_pk;


                }
        console.log("    selected_pk", selected_pk)
                mod_dict.table = tblName;

    // ---  lookup exam_dict in exam_rows
                const data_dicts = (tblName === "duo_exam") ? duo_exam_dicts : ete_exam_dicts;
                const mapid = selected.map_id;
                const exam_dict = (data_dicts.hasOwnProperty(mapid)) ? data_dicts[mapid] : null;
        console.log("    data_dicts", data_dicts)
        console.log("    mapid", mapid)
        console.log("    exam_dict", exam_dict)

        // ---  create mod_dict
                has_selected_item = (!isEmpty(exam_dict));
                if(has_selected_item){
                    mod_dict.examyear_pk = setting_dict.sel_examyear_pk;
                    mod_dict.depbase_pk = setting_dict.sel_depbase_pk;
                        mod_dict.mapid = exam_dict.mapid;
                        mod_dict.exam_pk = exam_dict.id;
                    if (tblName === "ete_exam") {
                        mod_dict.subject_pk = exam_dict.subj_id;
                        mod_dict.subj_name_nl = exam_dict.subj_name_nl;
                        mod_dict.exam_name = exam_dict.exam_name;
                    } else  if (tblName === "duo_exam") {
                        mod_dict.department_id = exam_dict.department_id;
                        mod_dict.subject_pk = exam_dict.subj_id;
                        mod_dict.subj_name_nl = exam_dict.subj_name_nl;
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
                        const will_be_deleted_copied_txt = (is_copy) ? loc.will_be_copied : loc.will_be_deleted;
                        const exam_txt = (table === "duo_exam") ? loc.CVTE_exam : loc.ETE_exam;
                        msg_html = ["<p class='pb-2'>", exam_txt, " '", mod_dict.exam_name, "'",
                                    will_be_deleted_copied_txt, "</p><p class='py-2'>",
                                loc.Do_you_want_to_continue, "</p>"].join("");;
                    };
                };

                btn_save_txt = !has_selected_item ? loc.OK :
                                (is_copy) ? loc.Yes_copy :
                                (is_undo_published) ? loc.Yes_remove : loc.Yes_delete;
                btn_cancel_txt = (has_selected_item) ? loc.No_cancel : loc.Close;

            };

            el_confirm_loader.classList.add(cls_hide);

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

        mod_dict.dont_hide_modal = false;
        if (permit_dict.permit_crud && permit_dict.requsr_role_admin) {

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

            } else if (mod_dict.mode === "link_exam_to_grades"){

                const upload_dict = { mode: "link_exam_to_grades",
                                       exam_pk: mod_dict.exam_pk,
                                       examyear_pk: mod_dict.examyear_pk,
                                       subject_pk: mod_dict.subject_pk,
                                       subject_name: mod_dict.subject_name,
                                       is_test: false
                                    };

                UploadChanges(upload_dict, urls.url_link_exam_to_grades);
                // mod_dict.save_value prevents putting back the old value in el_input
                mod_dict.dont_rest_input_value = true;
                mod_dict.dont_hide_modal = true;

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

            } else if (mod_dict.mode === "nterm") {
                // must loose focus, otherwise green / red border won't show
                //el_input.blur();
                //const el_loader =  document.getElementById("id_MSTUD_loader");
               // el_loader.classList.remove(cls_visible_hide);

        // ---  upload changes

            // mod_dict gets value in HandleInputChanged
                const upload_dict = { table: "duo_exam",
                                       mode: "update",
                                       exam_pk: mod_dict.exam_pk,
                                       examyear_pk: mod_dict.examyear_pk,
                                       subject_pk: mod_dict.subject_pk,
                                       nterm: mod_dict.nterm // nterm is string, will be converted on server
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

            } else if (mod_dict.mode === "copy_ntermen") {
        // ---  Upload Changes
                let upload_dict = { mode: mod_dict.mode,
                                    examyear_pk: setting_dict.sel_examyear_pk
                                    };
                UploadChanges(upload_dict, urls.url_exam_copy_ntermen);

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
                let upload_dict = {mode: mod_dict.mode};
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
        if (!mod_dict.dont_hide_modal){
            $("#id_mod_confirm").modal("hide");
        };
    }  // ModConfirmSave

//=========  ModConfirmResponse  ================ PR2019-06-23
    function ModConfirmResponse(response) {
        //console.log(" --- ModConfirmResponse --- ");
        //console.log("mod_dict: ", mod_dict);
        // hide loader
        el_confirm_loader.classList.add(cls_hide)
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

//=========  ModConfirmResponseLinkExamToGrades  ================ PR2022-06-14 PR2023-05-02
    function ModConfirmResponseLinkExamToGrades(response) {
        console.log(" --- ModConfirmResponseLinkExamToGrades --- ");

    // hide loader
        el_confirm_loader.classList.add(cls_hide)

        const has_grades = response.response_link_exam_has_grades

        // el_confirm_msg_container.classList.add("border_bg_valid");
        el_confirm_msg_container.innerHTML = response.response_link_exam_to_grades;

        const hide_save_btn = (!response.response_link_exam_has_grades || response.response_link_exam_is_saved);
        el_confirm_btn_cancel.innerText = (hide_save_btn) ? loc.Close : loc.Cancel;

        add_or_remove_class(el_confirm_btn_save, cls_hide, hide_save_btn)
        el_confirm_btn_save.disabled = false;

    }  // ModConfirmResponse

//=========  ModMessageHide  ================ PR2022-05-28
    function ModMessageHide() {
        console.log(" --- ModMessageHide --- ");
        const upload_dict = {hide_msg: true};
        UploadChanges(upload_dict, urls.url_user_modmsg_hide)
    }  // ModMessageHide

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

//=========  MSED_Response  ================ PR2020-12-18 PR2021-05-10 PR2022-04-11 PR2023-06-02
    function MSED_Response(request_item_setting) {
        //console.log( "===== MSED_Response ========= ");
        el_SBR_item_count.innerText = null;

// ---  upload new selected_pk
        request_item_setting.page = setting_dict.sel_page;

        DatalistDownload(request_item_setting);
    }  // MSED_Response

//=========  MSSSS_Response  ================ PR2021-01-23 PR2021-02-05 PR2021-07-26  PR2023-04-17
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
            const request_item_setting = {
                page: "page_exams",
                sel_schoolbase_pk: selected_pk
            };
            DatalistDownload(request_item_setting);

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
            MEXQ_FillSelectTableLevel();

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


//=========  MSSSS_subject_response  ================ PR2023-05-04
    function MSSSS_subject_response(tblName, selected_dict, sel_subject_pk) {
        console.log( "===== MSSSS_subject_response ========= ");
        console.log( "tblName", tblName);
        console.log( "    sel_subject_pk", sel_subject_pk, typeof sel_subject_pk);
        console.log( "    selected_dict", selected_dict);
        // arguments of MSSSS_response are set in t_MSSSS_Save or t_MSSSS_Save_NEW
        // when changing subject, only update settings, dont use DatalistDownload but filter on page

        el_SBR_item_count.innerText = null;

        const request_item_setting = {page: 'page_exams'};

        // 'all subjects' has value -1 in mod select, -9 in allowed
        if(sel_subject_pk === -1) {
            request_item_setting.sel_subject_pk = -9;
            setting_dict.sel_subject_pk = null;
            setting_dict.sel_subject_name = null;
        } else {
            request_item_setting.sel_subject_pk = sel_subject_pk;
            request_item_setting.ssel_cluster_pk = null;
            request_item_setting.sel_student_pk = null;

            setting_dict.sel_subject_pk = sel_subject_pk;
            setting_dict.sel_subject_name = (selected_dict && selected_dict.name_nl) ? selected_dict.name_nl : null;
            setting_dict.sel_cluster_pk = null;
            setting_dict.sel_student_pk = null;
        };
        DatalistDownload(request_item_setting);

    };  // MSSSS_subject_response

//=========  SBR_display_subject  ================ PR2023-05-04
    function SBR_display_subject() {
        //console.log("===== SBR_display_subject =====");

        t_MSSSS_display_in_sbr("subject", setting_dict.sel_subject_pk);

        // hide itemcount
        t_set_sbr_itemcount_txt(loc, 0)

    };  // SBR_display_subject


//========= MSSSS_display_in_sbr_reset  ====================================
    function MSSSS_display_in_sbr_reset() {
        //console.log( "===== MSSSS_display_in_sbr_reset  ========= ");

        t_MSSSS_display_in_sbr("subject");
        t_MSSSS_display_in_sbr("student");
        t_MSSSS_display_in_sbr("cluster");

    }; // MSSSS_display_in_sbr_reset

//========= get_tblName_from_selectedBtn  ======== // PR2022-02-26
    function get_tblName_from_selectedBtn() {
        return  (selected_btn === "btn_ete_exams") ? "ete_exam" :
                   (selected_btn === "btn_duo_exams") ? "duo_exam" :
                   (selected_btn === "btn_ntermen") ? "ntermen" :
                   (selected_btn === "btn_results") ? "results" : null ;
    };

//========= get_datadicts_from_sel_btn  ======== // PR2023-05-04
    function get_datadicts_from_sel_btn() {
        return (selected_btn === "btn_ete_exams") ? ete_exam_dicts :
                (selected_btn === "btn_duo_exams") ? duo_exam_dicts :
                (selected_btn === "btn_ntermen") ? ntermentable_dicts :
                (selected_btn === "btn_results") ? grade_exam_result_dicts : null;
    };

//========= get_datadict_from_table_element  ============= PR2022-04-29  PR2023-06-08
    function get_datadict_from_table_element(el){
// ---  lookup exam_dict in ete_exam_rows or in grade_exam_rows
        const tblRow = t_get_tablerow_selected(el);
        const map_id = (tblRow) ? tblRow.id : null;

        selected.map_id = tblRow.id;

        const data_dicts = get_datadicts_from_sel_btn();
        const data_dict = (data_dicts && data_dicts.hasOwnProperty(map_id)) ? data_dicts[map_id] : null;
        return data_dict;
    };  // get_datadict_from_table_element

//=========  RefreshDataRowsAfterUpload  ================ PR2022-02-26
    function RefreshDataRowsAfterUpload(response) {
        console.log(" --- RefreshDataRowsAfterUploadFromExcel  ---");
        console.log( "response", response);
        const is_test = (!!response && !!response.is_test);
        console.log( "is_test", is_test);

        if(!is_test) {
            DatalistDownload({page: "page_exams"});
        };
    }; //  RefreshDataRowsAfterUpload

})  // document.addEventListener('DOMContentLoaded', function()