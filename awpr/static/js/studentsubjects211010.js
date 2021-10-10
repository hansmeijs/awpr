// PR2020-09-29 added

// PR2021-07-23  declare variables outside function to make them global variables

// selected_btn is also used in t_MCOL_Open
let selected_btn = "btn_studsubj";
let setting_dict = {};
let permit_dict = {};
let loc = {};
let urls = {};

const field_settings = {};

const selected = {
    studsubj_dict: null,
    student_pk: null,
    subject_pk: null,
    item_count: 0
};

let school_rows = [];
let student_rows = [];
let subject_rows = [];
let studsubj_rows = [];

let schemeitem_rows = [];
let published_rows = [];

document.addEventListener('DOMContentLoaded', function() {
    "use strict";

    // <PERMIT> PR220-10-02
    //  - can view page: only 'role_school', 'role_insp', 'role_admin', 'role_system'
    //  - can add/delete/edit only 'role_admin', 'role_system' plus 'perm_edit'
    //  roles are:   'role_student', 'role_teacher', 'role_school', 'role_insp', 'role_admin', 'role_system'
    //  permits are: 'perm_read', 'perm_edit', 'perm_auth1', 'perm_auth2', 'perm_docs', 'perm_admin', 'perm_system'

// ---  check if user has permit to view this page. If not: el_loader does not exist PR2020-10-02
    const el_loader = document.getElementById("id_loader");
    const el_hdr_left = document.getElementById("id_hdr_left");
    const may_view_page = (!!el_loader)

    const cls_hide = "display_hide";
    const cls_hover = "tr_hover";
    const cls_visible_hide = "visibility_hide";
    const cls_selected = "tsa_tr_selected";

// ---  id of selected customer and selected order

    let mod_dict = {};
    let mod_MSTUD_dict = {};
// mod_MSTUDSUBJ_dict stores available studsubj for selected candidate in MSTUDSUBJ
    let mod_MSTUDSUBJ_dict = {
        schemeitem_dict: {}, // stores available studsubj for selected candidate in MSTUDSUBJ
        studsubj_dict: {}  // stores studsubj of selected candidate in MSTUDSUBJ
    };

    let mod_MASS_dict = {};
    let mod_MMUOC = {};
    let mod_MEX3_dict = {};

    let user_list = [];
    let examyear_map = new Map();
    let department_map = new Map();
    let level_map = new Map();
    let sector_map = new Map();

    // PR2021-07-23 moved outside this function, on top of this script:
    //let student_rows = [];
    //let subject_rows = [];
    //let studsubj_rows = [];
    //let schemeitem_rows = [];
    //let loc = {};

    let filter_dict = {};
    let filter_mod_employee = false;

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    urls.url_settings_upload = get_attr_from_el(el_data, "data-url_settings_upload");
    urls.url_student_biscand = get_attr_from_el(el_data, "data-url_student_biscand");
    urls.url_studsubj_upload = get_attr_from_el(el_data, "data-url_studsubj_upload");
    urls.url_studsubj_single_update = get_attr_from_el(el_data, "data-url_studsubj_single_update");

    urls.url_studsubj_validate = get_attr_from_el(el_data, "data-url_studsubj_validate");
    urls.url_studsubj_validate_test = get_attr_from_el(el_data, "data-url_studsubj_validate_test");

    urls.url_studsubj_validate_all = get_attr_from_el(el_data, "data-url_studsubj_validate_all");
    urls.url_studsubj_multiple_occurrences = get_attr_from_el(el_data, "data-url_studsubj_multiple_occurrences");
    urls.url_studsubj_approve = get_attr_from_el(el_data, "data-url_studsubj_approve");
    urls.url_studsubj_approve_multiple = get_attr_from_el(el_data, "data-url_studsubj_approve_multiple");
    urls.url_studsubj_send_email_exform = get_attr_from_el(el_data, "data-url_studsubj_send_email_exform");
    urls.url_grade_download_ex1 = get_attr_from_el(el_data, "data-url_grade_download_ex1");

    urls.url_ex3_getinfo = get_attr_from_el(el_data, "data-url_ex3_getinfo");
    urls.url_ex3_download = get_attr_from_el(el_data, "data-url_ex3_download");

    // url_importdata_upload is stored in id_MIMP_data of modimport.html

// columns_hidden and columns_tobe_hidden are also used in t_MCOL_Open and t_MCOL_Save
    columns_tobe_hidden.btn_studsubj = {
        fields: ["examnumber", "lvl_abbrev", "sct_abbrev", "subj_name", "sjtp_abbrev", "subj_status"],
        captions: ["Examnumber", "Leerweg", "SectorProfiel_twolines", "Subject", "Character", "Approved"]}
    columns_tobe_hidden.btn_exemption = {
        fields: ["examnumber", "lvl_abbrev", "sct_abbrev", "subj_name"],
        captions: ["Examnumber_twolines",  "Leerweg", "SectorProfiel_twolines", "Subject"]}
    columns_tobe_hidden.btn_published = {
        fields: ["examperiod", "datepublished", "url"],
        captions: ["Exam_period",  "Date_submitted", "Download_Exform"]}
// --- get field_settings
    const field_settings = {
        btn_studsubj: {field_caption: ["subj_error", "Examnumber_twolines", "Candidate",  "Leerweg", "SectorProfiel_twolines",
                                "Abbreviation_twolines", "Subject", "Character",  "",
                                "Exemption", "", "Re_examination", "", "Re_exam_3rd_2lns", "",
                                "Proof_of_knowledge_2lns", "", ""],
                    field_names: ["subj_error", "examnumber", "fullname", "lvl_abbrev", "sct_abbrev",
                                "subj_code", "subj_name", "sjtp_abbrev", "subj_status",
                                ],
                                // TODO add has_exemption etc
                                //"has_exemption", "exm_status", "has_reex", "re2_status", "has_reex03", "re3_status",
                                //"pok_validthru", "pok_status", "notes"],
                    field_tags: ["div", "div", "div", "div", "div",
                                "div", "div", "div", "div",
                                "div", "div", "div", "div", "div", "div",
                                "div", "div", "div"],

                    filter_tags: ["toggle", "text", "text",  "text",  "text",
                                "text", "text", "text", "multitoggle",
                                 "toggle", "text", "toggle", "text", "toggle", "text",
                                 "toggle", "toggle", "toggle"],
                    field_width:  ["020", "075", "180",  "075", "075",
                                    "075", "180","090", "032",
                                    "090", "032", "090", "032", "090", "032",
                                    "090", "032", "032"],
                    field_align: ["c", "r", "l", "c", "c",
                                    "l", "l", "l", "c",
                                    "c", "c", "c", "c", "c", "c", "c",
                                    "c", "c"]},
        btn_exemption: {  field_caption: ["subj_error", "Examnumber_twolines", "Candidate",  "Leerweg", "SectorProfiel_twolines",
                                "Abbreviation_twolines", "Subject", "Exemption", "", ],
                    field_names: ["subj_error", "examnumber", "fullname", "lvl_abbrev", "sct_abbrev",
                                "subj_code", "subj_name", "has_exemption", "exm_status"],
                    field_tags: ["div", "div", "div", "div", "div", "div", "div", "div", "div"],
                    filter_tags: ["toggle", "text", "text", "text", "text", "text", "text",  "toggle", "multitoggle"],
                    field_width:  ["020", "075", "180",  "075", "075", "075", "180", "090", "032"],
                    field_align: ["c", "r", "l", "c", "c", "l", "l", "c", "c"]},

        btn_published: {field_caption: ["", "Name_ex_form", "Exam_period",  "Date_submitted", "Download_Exform"],
                    field_names: ["select", "name", "examperiod", "datepublished", "url"],
                    field_tags: ["div", "div", "div", "div", "a"],
                    filter_tags: ["text", "text","text", "text", "text"],
                    field_width: ["020", "480", "150", "150", "120"],
                    field_align: ["c", "l", "l", "l", "c"]}
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

// ---  SIDEBAR ------------------------------------
        const el_SBR_select_level = document.getElementById("id_SBR_select_level");
        if(el_SBR_select_level){
            el_SBR_select_level.addEventListener("change", function() {HandleSbrLevelSector("level", el_SBR_select_level)}, false)}
        const el_SBR_select_sector = document.getElementById("id_SBR_select_sector");
        if(el_SBR_select_sector){
            el_SBR_select_sector.addEventListener("change", function() {HandleSbrLevelSector("sector", el_SBR_select_sector)}, false)};
        const el_SBR_select_subject = document.getElementById("id_SBR_select_subject");
        if(el_SBR_select_subject){
            el_SBR_select_subject.addEventListener("click", function() {t_MSSSS_Open(loc, "subject", subject_rows, true, setting_dict, permit_dict, MSSSS_Response)}, false)};
        const el_SBR_select_student = document.getElementById("id_SBR_select_student");
        if(el_SBR_select_student){
            el_SBR_select_student.addEventListener("click", function() {t_MSSSS_Open(loc, "student", student_rows, true, setting_dict, permit_dict, MSSSS_Response)}, false)};
        const el_SBR_select_showall = document.getElementById("id_SBR_select_showall");
        if(el_SBR_select_showall){
            el_SBR_select_showall.addEventListener("click", function() {HandleShowAll()}, false);
            // TODO switch to t_SBR_show_all
            //el_SBR_select_showall.addEventListener("click", function() {t_SBR_show_all(FillTblRows)}, false);
            add_hover(el_SBR_select_showall);
        };
        const el_SBR_item_count = document.getElementById("id_SBR_item_count");

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

// ---  MODAL SELECT COLUMNS ------------------------------------
        const el_MCOL_btn_save = document.getElementById("id_MCOL_btn_save")
        if(el_MCOL_btn_save){
            el_MCOL_btn_save.addEventListener("click", function() {
                t_MCOL_Save(urls.url_settings_upload, HandleBtnSelect)}, false )
        };

// ---  MODAL STUDENT SUBJECTS
        const el_MSTUDSUBJ_hdr = document.getElementById("id_MSTUDSUBJ_hdr")
        const el_MSTUDSUBJ_btn_add_selected = document.getElementById("id_MSTUDSUBJ_btn_add_selected")
        if(el_MSTUDSUBJ_btn_add_selected){
            el_MSTUDSUBJ_btn_add_selected.addEventListener("click", function() {MSTUDSUBJ_AddRemoveSubject("add")}, false)};
        const el_MSTUDSUBJ_btn_remove_selected = document.getElementById("id_MSTUDSUBJ_btn_remove_selected")
        if(el_MSTUDSUBJ_btn_remove_selected){
            el_MSTUDSUBJ_btn_remove_selected.addEventListener("click", function() {MSTUDSUBJ_AddRemoveSubject("remove")}, false)};
        const el_MSTUDSUBJ_btn_add_package = document.getElementById("id_MSTUDSUBJ_btn_add_package")
        if(el_MSTUDSUBJ_btn_add_package){
            el_MSTUDSUBJ_btn_add_package.addEventListener("click", function() {MSTUDSUBJ_AddPackage()}, false)};
        const el_MSTUDSUBJ_char_header = document.getElementById("id_MSTUDSUBJ_char_header");

        const el_MSTUDSUBJ_input_controls = document.getElementById("id_MSTUDSUBJ_div_form_controls").querySelectorAll(".awp_input_text, .awp_input_checkbox")
        if(el_MSTUDSUBJ_input_controls){
            for (let i = 0, el; el = el_MSTUDSUBJ_input_controls[i]; i++) {
                const key_str = (el.classList.contains("awp_input_checkbox")) ? "change" : "keyup";
                el.addEventListener(key_str, function() {MSTUDSUBJ_InputboxEdit(el)}, false)
            };
        };
        const el_MSTUDSUBJ_msg_container = document.getElementById("id_MSTUDSUBJ_msg_container");
        const el_MSTUDSUBJ_loader = document.getElementById("id_MSTUDSUBJ_loader");
        const el_MSTUDSUBJ_btn_save = document.getElementById("id_MSTUDSUBJ_btn_save");
        if(el_MSTUDSUBJ_btn_save){el_MSTUDSUBJ_btn_save.addEventListener("click", function() {MSTUDSUBJ_Save()}, false)};
        const el_MSTUDSUBJ_btn_cancel = document.getElementById("id_MSTUDSUBJ_btn_cancel");

        const el_tblBody_studsubjects = document.getElementById("id_MSTUDSUBJ_tblBody_studsubjects");
        const el_tblBody_schemeitems = document.getElementById("id_MSTUDSUBJ_tblBody_schemeitems");

// ---  MOD APPROVE STUDENT SUBJECT ------------------------------------
        const el_MASS_header = document.getElementById("id_MASS_header");

        const el_MASS_select_container = document.getElementById("id_MASS_select_container");
            const el_MASS_subheader = document.getElementById("id_MASS_subheader");
            const el_MASS_level = document.getElementById("id_MASS_level");
            const el_MASS_sector = document.getElementById("id_MASS_sector");
            const el_MASS_subject = document.getElementById("id_MASS_subject");
            //const el_MASS_cluster = document.getElementById("id_MASS_cluster");
        const el_MASS_info_container = document.getElementById("id_MASS_info_container");
        const el_MASS_loader = document.getElementById("id_MASS_loader");

        const el_MASS_info_request_verifcode = document.getElementById("id_MASS_info_request_verifcode");

        const el_MASS_input_verifcode = document.getElementById("id_MASS_input_verifcode");
        if (el_MASS_input_verifcode){
            el_MASS_input_verifcode.addEventListener("keyup", function() {MASS_InputVerifcode(el_MASS_input_verifcode, event.key)}, false);
            el_MASS_input_verifcode.addEventListener("change", function() {MASS_InputVerifcode(el_MASS_input_verifcode)}, false);
        };
        const el_MASS_btn_delete = document.getElementById("id_MASS_btn_delete");
        if (el_MASS_btn_delete){
            el_MASS_btn_delete.addEventListener("click", function() {MASS_Save("delete")}, false )  // true = reset
        };
        const el_MASS_btn_save = document.getElementById("id_MASS_btn_save");
        if (el_MASS_btn_save){
            el_MASS_btn_save.addEventListener("click", function() {MASS_Save("save")}, false )
        };
        const el_MASS_btn_cancel = document.getElementById("id_MASS_btn_cancel");

// ---  MOD IMPORT ------------------------------------
// --- create EventListener for select dateformat element
// --- create EventListener for buttons in btn_container
    const el_MIMP_btn_container = document.getElementById("id_MIMP_btn_container");
    if(el_MIMP_btn_container){
        const btns = el_MIMP_btn_container.children;
        for (let i = 0, btn; btn = btns[i]; i++) {
            const data_btn = get_attr_from_el(btn,"data-btn")
            btn.addEventListener("click", function() {MIMP_btnSelectClicked(data_btn)}, false )
        }
    }
    const el_MIMP_filedialog = document.getElementById("id_MIMP_filedialog");
    if (el_MIMP_filedialog){el_MIMP_filedialog.addEventListener("change", function() {MIMP_HandleFiledialog(el_MIMP_filedialog)}, false)};
    const el_MIMP_btn_filedialog = document.getElementById("id_MIMP_btn_filedialog");
    if (el_MIMP_filedialog && el_MIMP_btn_filedialog){
        el_MIMP_btn_filedialog.addEventListener("click", function() {MIMP_OpenFiledialog(el_MIMP_filedialog)}, false)};
    const el_MIMP_filename = document.getElementById("id_MIMP_filename");

    const el_MIMP_tabular = document.getElementById("id_MIMP_tabular");
    if (el_MIMP_tabular){
        el_MIMP_tabular.addEventListener("change", function() {MIMP_CheckboxCrosstabTabularChanged(el_MIMP_tabular)}, false )
    };
    const el_MIMP_crosstab = document.getElementById("id_MIMP_crosstab");
    if (el_MIMP_crosstab){
        el_MIMP_crosstab.addEventListener("change", function() {MIMP_CheckboxCrosstabTabularChanged(el_MIMP_crosstab)}, false )
    };

    const el_worksheet_list = document.getElementById("id_MIMP_worksheetlist");
        el_worksheet_list.addEventListener("change", MIMP_SelectWorksheet, false);
    const el_MIMP_checkboxhasheader = document.getElementById("id_MIMP_hasheader");
        el_MIMP_checkboxhasheader.addEventListener("change", MIMP_CheckboxHasheaderChanged) //, false);

   const el_MIMP_btn_prev = document.getElementById("id_MIMP_btn_prev");
        el_MIMP_btn_prev.addEventListener("click", function() {MIMP_btnPrevNextClicked("prev")}, false )
   const el_MIMP_btn_next = document.getElementById("id_MIMP_btn_next");
        el_MIMP_btn_next.addEventListener("click", function() {MIMP_btnPrevNextClicked("next")}, false )
   const el_MIMP_btn_test = document.getElementById("id_MIMP_btn_test");
        el_MIMP_btn_test.addEventListener("click", function() {MIMP_Save("test", RefreshDataRowsAfterUploadFromExcel, setting_dict)}, false )
   const el_MIMP_btn_upload = document.getElementById("id_MIMP_btn_upload");
        el_MIMP_btn_upload.addEventListener("click", function() {MIMP_Save("save", RefreshDataRowsAfterUploadFromExcel, setting_dict)}, false )

// ---  MODAL MULTIPLE OCCURRENCES ------------------------------------
   const el_MMUOC_data_container = document.getElementById("id_MMUOC_data_container")
   const el_MMUOC_btn_showall = document.getElementById("id_MMUOC_btn_showall");
        el_MMUOC_btn_showall.addEventListener("click", function() {MMUOC_toggle_showall()}, false )

// ---  MOD EX3 FORM ------------------------------------
    const el_id_MEX3_hdr = document.getElementById("id_MEX3_hdr");
    const el_MEX3_loader = document.getElementById("id_MEX3_loader");
    const el_MEX3_select_layout = document.getElementById("id_MEX3_select_layout");
    const el_MEX3_layout_option_level = document.getElementById("id_MEX3_layout_option_level");

    const el_MEX3_select_level = document.getElementById("id_MEX3_select_level");
    if (el_MEX3_select_level){
        el_MEX3_select_level.addEventListener("change", function() {MEX3_SelectLevelHasChanged()}, false )
    }
    const el_MEX3_tblBody_available = document.getElementById("id_MEX3_tblBody_available");
    const el_MEX3_tblBody_selected = document.getElementById("id_MEX3_tblBody_selected");
    const el_MEX3_btn_save = document.getElementById("id_MEX3_btn_save");
    if (el_MEX3_btn_save){
        el_MEX3_btn_save.addEventListener("click", function() {MEX3_Save()}, false )
    }

// ---  MOD CONFIRM ------------------------------------
        let el_confirm_header = document.getElementById("id_modconfirm_header");
        let el_confirm_loader = document.getElementById("id_modconfirm_loader");
        let el_confirm_msg_container = document.getElementById("id_modconfirm_msg_container")

        let el_confirm_btn_cancel = document.getElementById("id_modconfirm_btn_cancel");
        let el_confirm_btn_save = document.getElementById("id_modconfirm_btn_save");
        if(el_confirm_btn_save){ el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()}) };

// ---  set selected menu button active
        //SetMenubuttonActive(document.getElementById("id_hdr_users"));
    if(may_view_page){
        const datalist_request = {
                setting: {page: "page_studsubj"},
                schoolsetting: {setting_key: "import_studsubj"},
                locale: {page: ["page_studsubj", "page_subject", "page_student", "upload"]},
                examyear_rows: {get: true},
                school_rows: {get: true},

                department_rows: {get: true},
                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},

                scheme_rows: {cur_dep_only: true},
                schemeitem_rows: {cur_dep_only: true},

                student_rows: {cur_dep_only: true},
                subject_rows: {cur_dep_only: true},
                studentsubject_rows: {cur_dep_only: true},

                published_rows: {get: true}
            };

        DatalistDownload(datalist_request, "DOMContentLoaded");
    }
//  #############################################################################################################

//========= DatalistDownload  ===================== PR2020-07-31
    function DatalistDownload(datalist_request, called_by) {
        console.log( "=== DatalistDownload ", called_by)
        console.log("request: ", datalist_request)

// ---  Get today's date and time - for elapsed time
        let startime = new Date().getTime();

// ---  show loader
        el_loader.classList.remove(cls_hide)
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
                el_loader.classList.add(cls_hide)
                el_hdr_left.classList.remove(cls_hide)

                let must_create_submenu = false, must_update_headerbar = false;
                let check_validation = false;

                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                    must_create_submenu = true;
                };
                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict;
                    selected_btn = (setting_dict.sel_btn);

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
                        }
                    }
                    must_update_headerbar = true;
                };

                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    // get_permits must come before CreateSubmenu and FiLLTbl
                    b_get_permits_from_permitlist(permit_dict);
                    must_update_headerbar = true;
                }
                //if ("usergroup_list" in response) {
                //    usergroups = response.usergroup_list;
                //};
                if ("level_rows" in response)  {
                    b_fill_datamap(level_map, response.level_rows)
                    t_SBR_FillSelectOptionsDepartmentLevelSector("level", response.level_rows, setting_dict)
                };
                if ("sector_rows" in response) {
                    b_fill_datamap(sector_map, response.sector_rows);
                    t_SBR_FillSelectOptionsDepartmentLevelSector("sector", response.sector_rows, setting_dict);
                };

                if(must_create_submenu){CreateSubmenu()};
                if(must_update_headerbar){
                    b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);
                };

                if ("schoolsetting_dict" in response) { i_UpdateSchoolsettingsImport(response.schoolsetting_dict) };
                if ("messages" in response) {
                    b_ShowModMessages(response.messages);
                }
                if ("examyear_rows" in response) { b_fill_datamap(examyear_map, response.examyear_rows) };
                if ("school_rows" in response)  {
                    school_rows = response.school_rows;
                };
                if ("department_rows" in response) { b_fill_datamap(department_map, response.department_rows) };

                if ("student_rows" in response) {
                    student_rows = response.student_rows;
                }
                if ("subject_rows" in response) {
                    subject_rows = response.subject_rows;
                }
                if ("studentsubject_rows" in response) {
                    studsubj_rows = response.studentsubject_rows;
                    check_validation = true;
                };
                if ("schemeitem_rows" in response)  {
                    schemeitem_rows = response.schemeitem_rows;
                };
                if ("published_rows" in response)  {
                    published_rows = response.published_rows;
                };
                SBR_display_subject_student();
                HandleBtnSelect(selected_btn, true)  // true = skip_upload

                if (check_validation) {
                    DownloadValidationStatusNotes();
                }
            },
            error: function (xhr, msg) {
// ---  hide loader
                el_loader.classList.add(cls_hide);
                el_hdr_left.classList.remove(cls_hide)
                console.log(msg + '\n' + xhr.responseText);
            }
        });
    }  // function DatalistDownload

//=========  CreateSubmenu  ===  PR2020-07-31
    function CreateSubmenu() {
        //console.log("===  CreateSubmenu == ");
        //console.log("permit_dict", permit_dict);
        let el_submenu = document.getElementById("id_submenu")
        if(el_submenu){
            if(permit_dict.requsr_same_school){
                if(permit_dict.permit_crud){
                    AddSubmenuButton(el_submenu, loc.Upload_subjects, function() {MIMP_Open(loc, "import_studsubj")}, null, "id_submenu_import");
                    AddSubmenuButton(el_submenu, loc.Preliminary_Ex1_form, function() {ModConfirmOpen("prelim_ex1")});
                };
                if (permit_dict.permit_approve_subject){
                    AddSubmenuButton(el_submenu, loc.Approve_subjects, function() {MASS_Open("approve")});
                }
                if (permit_dict.permit_submit_subject){
                    AddSubmenuButton(el_submenu, loc.Submit_Ex1_form, function() {MASS_Open("submit")});
                };
                AddSubmenuButton(el_submenu, loc.Ex3_form, function() {MEX3_Open()});
            };
            AddSubmenuButton(el_submenu, loc.Hide_columns, function() {t_MCOL_Open("page_studsubj")}, [], "id_submenu_columns")
            el_submenu.classList.remove(cls_hide);
        };
    };//function CreateSubmenu

//###########################################################################
// +++++++++++++++++ EVENT HANDLERS +++++++++++++++++++++++++++++++++++++++++
//=========  HandleBtnSelect  ================ PR2020-09-19  PR2020-11-14 PR2021-08-07
    function HandleBtnSelect(data_btn, skip_upload) {
        //console.log( "===== HandleBtnSelect ========= ", data_btn);

// ---  get  selected_btn
        selected_btn = data_btn;
        if(!selected_btn){selected_btn = "btn_studsubj"}
        //console.log( "selected_btn: ", selected_btn);

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_studsubj: {sel_btn: selected_btn}};
            b_UploadSettings (upload_dict, urls.url_settings_upload);
        };

// ---  check for multiple occurrences when btn = exemption
        if(selected_btn === 'btn_exemption'){
            DownloadMultipleOccurrences();
        };


// ---  highlight selected button
        highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  show only the elements that are used in this tab
        b_show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

       //console.log("selected_btn", selected_btn);
        FillTblRows(true);  // true = refresh_headerrow

    }  // HandleBtnSelect

//=========  HandleTableRowClicked  ================ PR2020-08-03
    function HandleTableRowClicked(tr_clicked) {
        //console.log("=== HandleTableRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

// ---  update selected student_pk
        selected.studsubj_dict = null;
        selected.student_pk = null;
        selected.subject_pk = null;

// get data_dict from data_rows
        const data_dict = get_datadict_from_tblRow(tr_clicked);
        //console.log( "data_dict", data_dict);

        if (selected_btn === "btn_published"){
            //TODO
        } else {
            selected.studsubj_dict = data_dict;
            selected.studsubj_pk = (data_dict.studsubj_id) ? data_dict.studsubj_id : null;
            if (selected.studsubj_dict){
                selected.student_pk = selected.studsubj_dict.stud_id;
                selected.subject_pk = selected.studsubj_dict.subj_id;
            };
        }

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        DeselectHighlightedRows(tr_clicked, cls_selected);
        tr_clicked.classList.add(cls_selected)
    }  // HandleTableRowClicked

//========= UpdateHeaderText  ================== PR2020-07-31 PR2021-07-23
    function UpdateHeaderText(header_text){
        //console.log(" --- UpdateHeaderText ---" )
        //console.log( "header_text", header_text);
        //console.log( "el_hdr_left", el_hdr_left);
        if (el_hdr_left) {
            el_hdr_left.innerText = (header_text) ? header_text : null;
        }
    }   //  UpdateHeaderText


//========= FillTblRows  ==================== PR2021-07-01 PR2021-08-16
    function FillTblRows(refresh_headerrow) {
        //console.log( "===== FillTblRows  === ");
        //console.log( "setting_dict", setting_dict);

        const tblName = get_tblName_from_selectedBtn()
        const field_setting = field_settings[selected_btn]
        const data_rows = get_datarows_from_tblName(tblName)

// ---  filter subject or student
        const filter_field = (setting_dict.sel_subject_pk) ? "subject" : (setting_dict.sel_student_pk) ? "student" : null;
        const filter_pk = (setting_dict.sel_subject_pk) ? setting_dict.sel_subject_pk :
                            (setting_dict.sel_student_pk) ? setting_dict.sel_student_pk : null;

// --- update header text
        let selected_name = null;
        if (filter_pk){
            const data_rows = (filter_field === "subject") ? subject_rows :
                                  (filter_field === "student") ? student_rows : null;
            const data_dict = b_get_datadict_by_integer_from_datarows(data_rows, "id", filter_pk)
            if(!isEmpty(data_dict)){
                selected_name = (filter_field === "subject") ? data_dict.name :
                                  (filter_field === "student") ? data_dict.fullname : null;
            } else {
                selected_name = null;
            }
        }
        UpdateHeaderText(selected_name);

// --- create table header
        if (refresh_headerrow) {
            tblHead_datatable.innerText = null;
            CreateTblHeader(field_setting);
        }
// --- reset table
        tblBody_datatable.innerText = null;
// --- loop through data_rows
        if(data_rows && data_rows.length){
            for (let i = 0, map_dict; map_dict = data_rows[i]; i++) {
                const map_id = map_dict.mapid;
                let show_row = true;
                if (tblName !== "published"){
                    if (filter_field && filter_pk){
                        if (filter_field === "subject"){
                            show_row = (filter_pk === map_dict.subj_id)
                        } else if (filter_field === "student"){
                            show_row = (filter_pk === map_dict.stud_id)
                        }
                    }
                }
                if (show_row){
                    let tblRow = CreateTblRow(tblName, field_setting, map_id, map_dict)
                }
          };
        }  // if(data_rows)

        Filter_TableRows()
    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-07-31 PR2021-07-22
    function CreateTblHeader(field_setting) {
        //console.log("===  CreateTblHeader ===== ");
        //console.log("field_setting", field_setting);
        //console.log("columns_hidden", columns_hidden);

        const column_count = field_setting.field_names.length;

// +++  insert header and filter row ++++++++++++++++++++++++++++++++
        let tblRow_header = tblHead_datatable.insertRow (-1);
        let tblRow_filter = tblHead_datatable.insertRow (-1);

    // --- loop through columns
        for (let j = 0; j < column_count; j++) {
            const field = field_setting.field_names[j];

    // ---skip columns if in columns_hidden
            const col_is_hidden = get_column_is_hidden(field);
            if (!col_is_hidden){

        // --- get field_caption from field_setting, diplay 'Profiel' in column sctbase_id if has_profiel
                const key = field_setting.field_caption[j];
                let field_caption = (loc[key]) ? loc[key] : key;
                if (field === "sct_abbrev") {
                    field_caption = (setting_dict.sel_dep_has_profiel) ? loc.Profiel : loc.Sector;
                }

                const filter_tag = field_setting.filter_tags[j];
                const class_width = "tw_" + field_setting.field_width[j] ;
                const class_align = "ta_" + field_setting.field_align[j];
// ++++++++++ create header row +++++++++++++++
        // --- add th to tblRow.
                let th_header = document.createElement("th");
        // --- add div to th, margin not working with th
                    const el_header = document.createElement("div");
                        if (j === 0 ){
        // --- add checked image to first column
                           // TODO add multiple selection
                            //AppendChildIcon(el_header, imgsrc_stat00);
                        } else  if (field.includes("_status")){
                            // --- add  statud icon.
                            el_header.classList.add("diamond_0_0")
                        } else if(field === "notes"){
                             // dont show note icon when user has no permit_read_note
                            //const class_str = (permit_dict.permit_read_note) ? "note_0_1" : "note_0_0"
                            el_header.classList.add("note_0_1")

                        } else if(field === "subj_error"){
                             // dont show note icon when user has no permit_read_note
                            //const class_str = (permit_dict.permit_read_note) ? "note_0_1" : "note_0_0"
                            el_header.classList.add("note_0_0")
                        } else {
// --- add innerText to el_div
                            if(field_caption) {el_header.innerText = field_caption};
                            if(field === "examnumber"){el_header.classList.add("pr-2")}
                        };
// --- add width, text_align
                        el_header.classList.add(class_width, class_align);
                    th_header.appendChild(el_header)
                tblRow_header.appendChild(th_header);

// ++++++++++ create filter row +++++++++++++++
// --- add th to tblRow_filter.
                const th_filter = document.createElement("th");
                th_filter.id = "id_th_filter";  // to reset icons when clicked on show_all
// --- create element with tag from field_tags
                const el_tag = (filter_tag === "text") ? "input" : "div";
                const el_filter = document.createElement(el_tag);
// --- add EventListener to el_filter
                    if (filter_tag === "text") {
                        el_filter.addEventListener("keyup", function(event){HandleFilterKeyup(el_filter, event)});
                    } else if (["toggle", "multitoggle"].includes(filter_tag)) {
                        // add EventListener for icon to th_filter, not el_filter
                        th_filter.addEventListener("click", function(event){HandleFilterToggle(el_filter)});
                        th_filter.classList.add("pointer_show", "awp_filter_toggle");
                    }
// --- add data-field Attribute.
                    el_filter.setAttribute("data-field", field);
                    el_filter.setAttribute("data-filtertag", filter_tag);
// --- add other attributes
                    if (filter_tag === "text") {
                        el_filter.setAttribute("type", "text")
                        el_filter.classList.add("input_text");

                        el_filter.setAttribute("autocomplete", "off");
                        el_filter.setAttribute("ondragstart", "return false;");
                        el_filter.setAttribute("ondrop", "return false;");
                    } else if (["toggle", "multitoggle"].includes(filter_tag)) {
                        // default empty icon necessary to set pointer_show
                        append_background_class(el_filter,"tickmark_0_0");
                    }

// --- add width, text_align
                    el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");
                th_filter.appendChild(el_filter)
                tblRow_filter.appendChild(th_filter);
            }  //  if (columns_hidden.inludes(field))
        }  // for (let j = 0; j < column_count; j++)

    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09 PR2021-03-15
    function CreateTblRow(tblName, field_setting, map_id, map_dict) {
        //console.log("=========  CreateTblRow =========", tblName);
        //console.log("map_dict", map_dict);

        const field_names = field_setting.field_names;
        const field_tags = field_setting.field_tags;
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;

        let tobedeleted = false;

// ---  lookup index where this row must be inserted
        let ob1 = "", ob2 = "", ob3 = "";
        if (tblName === "studsubj") {
            if (map_dict.lastname) { ob1 = map_dict.lastname.toLowerCase() };
            if (map_dict.firstname) { ob2 = map_dict.firstname.toLowerCase() };
            if (map_dict.sjtp_name) { ob3 = (map_dict.subj_name.toLowerCase()) };

            tobedeleted = (map_dict.tobedeleted) ? map_dict.tobedeleted : false;
        } else if (tblName === "published") {
             if (map_dict.datepublished) { ob1 = map_dict.datepublished};
        }
        const row_index = b_recursive_tblRow_lookup(tblBody_datatable, ob1, ob2, ob3, setting_dict.user_lang);

// --- insert tblRow into tblBody at row_index
        let tblRow = tblBody_datatable.insertRow(row_index);
        tblRow.id = map_id

// --- add data attributes to tblRow
        tblRow.setAttribute("data-table", tblName);
        tblRow.setAttribute("data-pk", map_dict.studsubj_id);
        tblRow.setAttribute("data-studsubj_pk", map_dict.studsubj_id);
        tblRow.setAttribute("data-stud_pk", map_dict.stud_id);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);
        tblRow.setAttribute("data-ob2", ob2);
        tblRow.setAttribute("data-ob3", ob3);

// --- add EventListener to tblRow
        // PR2021-08-31 debug. modal didnt open becausue sometimes it comes before HandleTableRowClicked.
        // In that case there is no map_dict yet and modal will not open.
        // solved by moving function HandleTableRowClicked to MSTUSUBJ_Open,
        //tblRow.addEventListener("click", function() {HandleTableRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
        for (let j = 0; j < column_count; j++) {
            const field = field_names[j];

// skip columns if in columns_hidden
            // skip column if in columns_hidden
            const col_is_hidden = get_column_is_hidden(field);
            if (!col_is_hidden){
                const field_tag = field_tags[j];
                const class_width = "tw_" + field_width[j];
                const class_align = "ta_" + field_align[j];

        // --- insert td element,
                let td = tblRow.insertCell(-1);

        // --- create element with tag from field_tags
                let el = document.createElement(field_tag);

        // --- add data-field attribute
                el.setAttribute("data-field", field);

    // --- add classList to td
                if (tblName === "studsubj"){
                    if(field === "examnumber"){
                        td.classList.add("pr-4")
                    } else if (field.includes("has_")){
                        el.classList.add("tickmark_0_0")
                    } else  if (field === "subj_error"){
                        el.classList.add("note_0_3")
                    } else  if (field.includes("_status")){
                        el.classList.add("tickmark_0_0")
                    };
                } else if (tblName === "published"){
                    if (field === "url"){
                         el.innerHTML = "download &#8681;";
                         // el.target = "_blank";
                         //console.log("????????el", el)
                        //const el_attment = document.createElement("a");
                        //el_attment.innerText = att_name;
                        //el_attment.setAttribute("href", att_url)
                        //el_note_btn_attment.appendChild(el_attment);
                    }
                }

                td.appendChild(el);

    // --- add EventListener to td
                if (field === "select") {
                    // pass
                } else if (field.includes("has_")){
                    if(permit_dict.permit_crud && permit_dict.requsr_same_school){
                        td.addEventListener("click", function() {UploadToggle(el)}, false)
                        add_hover(td);
                    };
                } else if ( field.includes("_status")){
                    // skip when no permit or row has no studsubj_id or when it is published
                    if(permit_dict.permit_approve_subject && permit_dict.requsr_same_school && map_dict.studsubj_id){
                        const prefix = field.replace("_status", "");
                        const field_publ_id = prefix + "_publ_id" // subj_publ_id
                        const publ_id = (map_dict[field_publ_id]) ? map_dict[field_publ_id] : null;
                        if(!publ_id){
                            td.addEventListener("click", function() {UploadToggleStatus(el)}, false)
                            add_hover(td);
                        };
                    };
                } else {
                    // everyone that can view the page can open it, only permit_crud from same_school can edit PR2021-08-31
                    td.addEventListener("click", function() {MSTUDSUBJ_Open(td)}, false)
                    td.classList.add("pointer_show");
                    add_hover(td);
                };

        // --- add width, text_align, right padding in examnumber
                // not necessary: td.classList.add(class_width, class_align);

                if(["name", "fullname", "subj_name"].includes(field)){
                    // dont set width in field student and subject, to adjust width to length of name
                    el.classList.add(class_align);
                } else {
                    el.classList.add(class_width, class_align);
                }
                if(field === "examnumber"){el.classList.add("pr-2")}

// --- put value in field
               UpdateField(el, map_dict, tobedeleted);
            }  //  if (columns_hidden[field])
        }  // for (let j = 0; j < 8; j++)

        return tblRow
    };  // CreateTblRow

//=========  UpdateTblRow  ================ PR2020-08-01
    function UpdateTblRow(tblRow, tblName, map_dict) {
        console.log("=========  UpdateTblRow =========");
        if (tblRow && tblRow.cells){
            const tobedeleted = (mapdict.tobedeleted) ? mapdict.tobedeleted : false;
        console.log("map_dict", map_dict);
        console.log("tobedeleted", tobedeleted);
            for (let i = 0, td; td = tblRow.cells[i]; i++) {
                UpdateField(td.children[0], map_dict, tobedeleted);
            }
        }
    };  // UpdateTblRow

//=========  UpdateField  ================ PR2020-08-16 PR2021-09-28
    function UpdateField(el_div, map_dict, tobedeleted) {
        //console.log("=========  UpdateField =========");
        //console.log("map_dict", map_dict);
        //console.log("el_div", el_div);
        //console.log("tobedeleted", tobedeleted);

        if(el_div){
            const field = get_attr_from_el(el_div, "data-field");
            const fld_value = (map_dict[field]) ? map_dict[field] : null;

            if(field){
                let inner_text = null, h_ref = null, title_text = null, filter_value = null;
                if (field === "select") {
                    // TODO add select multiple users option PR2020-08-18
                } else if (["examnumber", "fullname", "lvl_abbrev", "sct_abbrev",
                            "subj_code", "subj_name", "sjtp_abbrev", "name"
                             ].includes(field)){
                    inner_text = fld_value;
                    filter_value = (inner_text) ? inner_text.toLowerCase() : null;

        //console.log("field", field, "fld_value", fld_value);

                } else if (field.includes("has_")){
                    filter_value = (fld_value) ? "1" : "0";
                    el_div.className = (fld_value) ? "tickmark_1_2" : "tickmark_0_0";
                    el_div.setAttribute("data-value", filter_value);

                } else if(field === "subj_error"){
                    filter_value = (fld_value) ? "1" : "0";
                    el_div.className = (fld_value) ? "note_1_3" : "note_0_0";
                    if(fld_value) {
                        if(!map_dict.studsubj_id){
                            title_text = loc.This_candidate_has_nosubjects;
                        } else {
                            title_text = loc.validation_error + "."
                        }
                    };

                } else if (field.includes("_status")){
                    const [status_className, status_title_text, filter_val] = UpdateFieldStatus(field, map_dict);
                    filter_value = filter_val;
                    el_div.className = status_className;
                    title_text = status_title_text;

                } else if (field === "examperiod"){
                    inner_text = loc.examperiod_caption[map_dict.examperiod];
                } else if (field === "datepublished"){
                     inner_text = format_dateISO_vanilla (loc, map_dict.datepublished, true, false, true, false);
                } else if (field === "url"){
                    h_ref = fld_value;
                };  // if (field === "select")

    // ---  mark tobedeleted row with line-through red
                add_or_remove_class(el_div, "text_decoration_line_through_red", !!tobedeleted, "text_decoration_initial")
                if (!title_text && tobedeleted){
                    title_text = loc.This_subject_ismarked_fordeletion + "\n" + loc.You_must_submit_additional_ex1form;
                }

// ---  put value in innerText and title
                if (el_div.tagName === "INPUT"){
                    el_div.value = inner_text;
                } else if (el_div.tagName === "A"){
                    el_div.href = h_ref;
                } else {
                    el_div.innerText = inner_text;
                };
                add_or_remove_attr (el_div, "title", !!title_text, title_text);

    // ---  add attribute filter_value
                add_or_remove_attr (el_div, "data-filter", !!filter_value, filter_value);
            }  // if(field)
        }  // if(el_div)
    };  // UpdateField

//=========  UpdateFieldStatus  ================ PR2021-07-25
    function UpdateFieldStatus(field, map_dict) {
        //console.log("=========  UpdateFieldStatus =========");
        //console.log("map_dict", map_dict);
        let className = "tickmark_0_0";  // tickmark_0_0 is blank img
        let title_text = null, filter_value = null;
        if (field.includes("_status")){
            // skip when row has no studsubj_id
            if (map_dict.studsubj_id) {

                //const prefix_mapped = {btn_studsubj: "subj_", btn_exemption: "exem_", btn_reex: "reex_", btn_reex3: "reex3_", btn_pok: "pok_", }
                const prefix = field.replace("_status", "");

                const field_auth1_id = prefix + "_auth1_id" // subj_auth1_id
                const field_auth2_id = prefix + "_auth2_id" // subj_auth2_id
                const field_publ_id = prefix + "_publ_id" // subj_publ_id
                const field_publ_modat = prefix + "_publ_modat" // subj_publ_modat

                const auth1_id = (map_dict[field_auth1_id]) ? map_dict[field_auth1_id] : null;
                const auth2_id = (map_dict[field_auth2_id]) ? map_dict[field_auth2_id] : null;
                const publ_id = (map_dict[field_publ_id]) ? map_dict[field_publ_id] : null;

                const class_str = (publ_id) ? "diamond_0_4" :
                                  (auth1_id && auth2_id) ? "diamond_3_3" :
                                  (auth1_id) ? "diamond_2_1" :
                                  (auth2_id) ? "diamond_1_2" : "diamond_0_0"; // diamond_0_0 is outlined diamond
                // filter_values are: '0'; is show all, 1: not approved, 2: auth1 approved, 3: auth2 approved, 4: auth1+2 approved, 5: submitted,   TODO '6': tobedeleted '7': locked

                filter_value = (publ_id) ? "5" :
                                  (auth1_id && auth2_id) ? "4" :
                                  (auth2_id ) ? "3" :
                                  (auth1_id) ? "2" : "1"; // diamond_0_0 is outlined diamond

                className = class_str;

                const field_auth1by = prefix + "_auth1by" // subj_auth1by
                const field_auth2by = prefix + "_auth2by" // subj_auth2by
                const field_published = prefix + "_published" // subj_published

                if (publ_id){
                    const modified_dateJS = parse_dateJS_from_dateISO(map_dict[field_publ_modat]);
                    title_text = loc.Submitted_at + ":\n" + format_datetime_from_datetimeJS(loc, modified_dateJS)

                } else if(auth1_id || auth2_id){
                    title_text = loc.Approved_by + ": "
                    for (let i = 1; i < 3; i++) {
                        const auth_id = (i === 1) ?  auth1_id : auth2_id;
                        const prefix_auth = prefix + "_auth" + i;
                        if(auth_id){
                            const function_str = (i === 1) ?  loc.President.toLowerCase() : loc.Secretary.toLowerCase();
                            const field_usr = prefix_auth + "_usr";
                            const auth_usr = (map_dict[field_usr]) ?  map_dict[field_usr] : "-";
                            title_text += "\n" + function_str + ": " + auth_usr;
                        };
                    }
                }
                //const data_value = (auth_id) ? "1" : "0";
                //el_div.setAttribute("data-value", data_value);
            }
        };  // if (field === "select") {
        return [className, title_text, filter_value]
    }  // UpdateFieldStatus

//========= get_column_is_hidden  ====== PR2021-03-15 PR2021-07-22
    function get_column_is_hidden(field) {
        //console.log( "===== get_column_is_hidden  === ");
        //console.log( "selected_btn", selected_btn);
        //console.log( "field", field);
        //console.log("setting_dict.sel_dep_level_req", setting_dict.sel_dep_level_req);

        const mapped_field = (field === "exm_status") ? "has_exemption" :
                             (field === "re2_status") ? "has_reex" :
                             (field === "re3_status") ? "has_reex03" :
                             (field === "pok_validthru") ? "pok_status" : field;
        //console.log( "mapped_field", mapped_field);

// --- set cols_hidden
        const cols_hidden = (columns_hidden[selected_btn]) ? columns_hidden[selected_btn] : [];

        let is_hidden = cols_hidden.includes(mapped_field);
        //console.log("is_hidden", is_hidden)

        if(!is_hidden){
            if (mapped_field === "lvl_abbrev") {
                is_hidden = (!setting_dict.sel_dep_level_req);
            } else if (mapped_field === "subj_error") {
                is_hidden = (selected_btn !== "btn_studsubj");
            } else if (mapped_field === "has_exemption") {
                is_hidden = (selected_btn !== "btn_exemption");
            } else if (mapped_field === "has_reex") {
                is_hidden = (selected_btn !== "btn_reex");
            } else if (mapped_field === "has_reex03") {
                is_hidden = (selected_btn !== "btn_reex3");
            } else if (mapped_field === "pok_validthru") {
                is_hidden = (selected_btn !== "btn_pok");
            };
        }
        //console.log( "is_hidden", is_hidden);
        return is_hidden;
    };  // get_column_is_hidden

// +++++++++++++++++ UPLOAD CHANGES +++++++++++++++++ PR2020-08-03

//========= UploadToggleStatus  ============= PR2020-07-31
    function UploadToggleStatus(el_input) {
        //console.log( " ==== UploadToggleStatus ====");
        //console.log( "el_input", el_input);

        if (permit_dict.permit_approve_subject){

            const tblRow = get_tablerow_selected(el_input);
            const data_dict = get_datadict_from_tblRow(tblRow);
            //console.log( "data_dict", data_dict);
/*
// +++ get existing data_dict from data_rows. data_rows is ordered by: studsubj_id, stud_id'
            const studsubj_pk = (update_dict && update_dict.studsubj_id) ? update_dict.studsubj_id : null;
            const student_pk = (update_dict && update_dict.stud_id) ? update_dict.stud_id : null;
            const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "studsubj_id", studsubj_pk, "stud_id", student_pk);
            let data_dict = (!isEmpty(found_dict)) ? found_dict : null;
            const datarow_index = index;
        //console.log(".....data_dict", data_dict);
*/

            if(!isEmpty(data_dict)){
                const fldName = get_attr_from_el(el_input, "data-field");
                const prefix = fldName.replace("_status", "");
                const auth = (permit_dict.usergroup_auth1 && !permit_dict.usergroup_auth2) ? "_auth1" :
                             (!permit_dict.usergroup_auth1 && permit_dict.usergroup_auth2) ? "_auth2" : null;

        //console.log( "permit_dict.usergroup_auth1", permit_dict.usergroup_auth1);
        //console.log( "permit_dict.usergroup_auth2", permit_dict.usergroup_auth2);
        //console.log( "auth", auth);
                const field_auth_id = prefix + auth +  "_id";
                const auth_id = (data_dict[field_auth_id]) ? data_dict[field_auth_id] : null;
                const model_field = (auth === "_auth1") ? "subj_auth1by" : (auth === "_auth2") ? "subj_auth2by" : null;
                if (model_field) {
// - get new_auth_id - remove oif already filled in
                    // TODO remove requsr_pk from client
                    const new_auth_id = (!auth_id) ? permit_dict.requsr_pk : null;

    // ---  upload changes
                    const studsubj_dict = {
                        student_pk: data_dict.stud_id,
                        studsubj_pk: data_dict.studsubj_id
                    };
                    studsubj_dict[model_field] = new_auth_id;

                    const upload_dict = {
                        table: "studsubj",
                        studsubj_list: [studsubj_dict]
                    };

                    UploadChanges(upload_dict, urls.url_studsubj_approve);
                };
            }  //  if(!isEmpty(data_dict)){

        } //   if(permit_dict.permit_approve_subject)
    }  // UploadToggleStatus

//========= UploadToggle  ============= PR2020-07-31 PR2021-09-18
    function UploadToggle(el_input) {
        console.log( " ==== UploadToggle ====");
        console.log( "el_input", el_input);
        // (still) only called in brn Exemptions
        if (permit_dict.permit_crud && permit_dict.requsr_same_school){

            const tblRow = get_tablerow_selected(el_input);
            const stud_pk = get_attr_from_el_int(tblRow, "data-stud_pk");
            const studsubj_pk = get_attr_from_el_int(tblRow, "data-studsubj_pk");

            const fldName = get_attr_from_el(el_input, "data-field");
            const old_value = get_attr_from_el_int(el_input, "data-value");

            const new_value = (!old_value);
            if(new_value){
     // ---  change icon, before uploading
                add_or_remove_class(el_input, "tickmark_1_2", new_value, "tickmark_0_0");
    // ---  upload changes
                const upload_dict = {
                    student_pk: stud_pk,
                    studsubj_pk: studsubj_pk
                };
                upload_dict[fldName] = new_value;
                UploadChanges(upload_dict, urls.url_studsubj_single_update);
            } else {
    // open mod confirm when deleting exemption, reex, reex3
            ModConfirmOpen(fldName, el_input);

            }
        }; //   if(permit_dict.permit_approve_subject)
    }  // UploadToggle

//========= UploadChanges  ============= PR2020-08-03 PR2021-07-26
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
                    el_loader.classList.add(cls_hide)
                    el_hdr_left.classList.remove(cls_hide)
                    console.log( "response");
                    console.log( response);
                    if ("validate_studsubj_list" in response) {
                        ResponseValidationAll(response.validate_studsubj_list)
                    }

                    if ("updated_studsubj_approve_rows" in response) {
                        RefreshDataRows("studsubj", response.updated_studsubj_approve_rows, studsubj_rows, true); // true = is_update
                    }

                    if ("updated_studsubj_rows" in response) {
                        RefreshDataRows("studsubj", response.updated_studsubj_rows, studsubj_rows, true)  // true = update
                    }

                    add_or_remove_class(el_MSTUDSUBJ_loader, cls_hide, true);
                    if ("studsubj_validate_html" in response) {
                         MSTUDSUBJ_Response(response)
                    };

                    if ( "approve_msg_html" in response){
                        MASS_UpdateFromResponse(response)
                    };
                    // this one is in MASS_UpdateFromResponse:
                    //if ( "updated_studsubj_approve_rows" in response){

                    if ("messages" in response){
                        b_ShowModMessages(response.messages);
                        $("#id_mod_studentsubject").modal("hide");
                    };

                    if("validate_multiple_occurrences" in response){
                        mod_MMUOC.rows = response.validate_multiple_occurrences

                        MMUOC_Open();
                    };
                    if("updated_multiple_occurrences" in response){
                        MMUOC_response(response.updated_multiple_occurrences);
                    };
                    if ("ex3_subject_rows" in response) {
                        MEX3_UpdateFromResponse (response);
                    }
                },  // success: function (response) {
                error: function (xhr, msg) {
                    // ---  hide loader
                    el_loader.classList.add(cls_hide)
                    el_hdr_left.classList.remove(cls_hide)

                    //console.log(msg + '\n' + xhr.responseText);
                }  // error: function (xhr, msg) {
            });  // $.ajax({
        }  //  if(!!row_upload)
    };  // UploadChanges

// +++++++++++++++++ UPDATE +++++++++++++++++++++++++++++++++++++++++++

// +++++++++ MOD STUDENT SUBJECT++++++++++++++++ PR2020-11-16
    function MSTUDSUBJ_Open(el_input){
        console.log(" -----  MSTUDSUBJ_Open   ----")
        console.log("el_input", el_input)
        console.log("permit_dict", permit_dict)

        // everyone that can view the page can open it, only permit_crud from same_school can edit PR2021-08-31

        if(el_input){

        // mod_MSTUDSUBJ_dict stores general info of selected candidate in MSTUDSUBJ PR2020-11-21
            mod_MSTUDSUBJ_dict = {
                studsubj_dict: {},  // stores studsubj of selected candidate in MSTUDSUBJ
                schemeitem_dict: {},
                sel_studsubj_mapid: null,
                sel_schemeitem_pk: null,
                new_studsubj_pk: 0
            };

            const tblRow = get_tablerow_selected(el_input);
            HandleTableRowClicked(tblRow);

        console.log("selected.studsubj_dict", selected.studsubj_dict)
            // selected.studsubj_dict gets value in HandleTableRowClicked
            if(!isEmpty(selected.studsubj_dict)) {
                mod_MSTUDSUBJ_dict.stud_id = selected.studsubj_dict.stud_id;
                mod_MSTUDSUBJ_dict.scheme_id = selected.studsubj_dict.scheme_id;

    // ---  set header text
                let header_text = loc.Subjects + loc._of_ + selected.studsubj_dict.fullname
                let dep_lvl_sct_text = (selected.studsubj_dict.dep_abbrev) ? selected.studsubj_dict.dep_abbrev + " - " : "";
                if(selected.studsubj_dict.lvl_abbrev) {dep_lvl_sct_text += selected.studsubj_dict.lvl_abbrev + " - "};
                if(selected.studsubj_dict.sct_abbrev) {dep_lvl_sct_text += selected.studsubj_dict.sct_abbrev};
                if (dep_lvl_sct_text) {header_text += " (" + dep_lvl_sct_text + ")"};

                el_MSTUDSUBJ_hdr.innerText = header_text
        // ---  remove value from el_mod_employee_input
                //MSTUD_SetElements();  // true = also_remove_values

                //document.getElementById("id_MSTUDSUBJ_msg_modified").innerText = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by

                const has_studsubj_rows = MSTUDSUBJ_FillDicts();
                MSTUDSUBJ_FillTbls();

                MSTUDSUBJ_SetInputFields(null, false);
        // hide loader and msg_box
                el_MSTUDSUBJ_msg_container.innerHTML = null
                add_or_remove_class(el_MSTUDSUBJ_msg_container, cls_hide, true)
                add_or_remove_class(el_MSTUDSUBJ_loader, cls_hide, true);

        // ---  set focus to el_MSTUD_abbrev
                //setTimeout(function (){el_MSTUD_abbrev.focus()}, 50);

        // ---  hide btn submit when not may_edit
                const may_edit = (permit_dict.permit_crud && permit_dict.requsr_same_school);
                add_or_remove_class(el_MSTUDSUBJ_btn_save, cls_hide, !may_edit);

        // ---  change cancel btn to close when not may_edit
                if(el_MSTUDSUBJ_btn_cancel) {
                    el_MSTUDSUBJ_btn_cancel.innerText = (may_edit) ? loc.Cancel : loc.Close;
                }
        // ---  disable btn submit on opening modal
                el_MSTUDSUBJ_btn_save.disabled = true;

        // ---  set input boxes readonly when not may_edit
                const el_MSTUDSUBJ_pwstitle = document.getElementById("id_MSTUDSUBJ_pwstitle");
                add_or_remove_attr (el_MSTUDSUBJ_pwstitle, "readonly", !may_edit, true);
                const el_MSTUDSUBJ_pwssubjects = document.getElementById("id_MSTUDSUBJ_pwssubjects");
                add_or_remove_attr (el_MSTUDSUBJ_pwssubjects, "readonly", !may_edit, true);

        // ---  show modal
                $("#id_mod_studentsubject").modal({backdrop: true});

        // validate student_subjects
                add_or_remove_class(el_MSTUDSUBJ_loader, cls_hide, false);
                MSTUDSUBJ_ValidateSubjects();

            }  // if(!isEmpty(map_dict)) {
        }
    };  // MSTUDSUBJ_Open

//========= MSTUDSUBJ_Save  ============= PR2020-11-18
    function MSTUDSUBJ_Save(){
        console.log(" -----  MSTUDSUBJ_Save   ----")
        console.log( "mod_MSTUDSUBJ_dict.studsubj_dict: ", mod_MSTUDSUBJ_dict.studsubj_dict);
        console.log( "mod_MSTUDSUBJ_dict: ", mod_MSTUDSUBJ_dict);
                    console.log("mod_MSTUDSUBJ_dict.stud_id: ", mod_MSTUDSUBJ_dict.stud_id)

        const may_edit = (permit_dict.permit_crud && permit_dict.requsr_same_school);
        if(may_edit){
            if(mod_MSTUDSUBJ_dict.stud_id){
                const upload_dict = {
                    table: 'studentsubject',
                    sel_examyear_pk: setting_dict.sel_examyear_pk,
                    sel_schoolbase_pk: setting_dict.sel_schoolbase_pk,
                    sel_depbase_pk: setting_dict.sel_depbase_pk,
                    student_pk: mod_MSTUDSUBJ_dict.stud_id
                }
console.log("upload_dict: ", upload_dict)
                const studsubj_list = []
    // ---  loop through mod_MSTUDSUBJ_dict.studsubj_dict
                for (const [studsubj_pk_str, ss_dict] of Object.entries(mod_MSTUDSUBJ_dict.studsubj_dict)) {
                    //const studsubj_pk = Number(studsubj_pk_str);
                     const studsubj_pk = (ss_dict.studsubj_id) ? ss_dict.studsubj_id : null

console.log("studsubj_pk_str: ", studsubj_pk_str)
console.log("studsubj_pk: ", studsubj_pk)
console.log("ss_dict: ", ss_dict)
                    if(!isEmpty(ss_dict)){
                        let mode = null;
                        if(ss_dict.tobedeleted){
                            mode = "delete";
                        } else if(ss_dict.undelete){
                            mode = "undelete";
                        } else  if(ss_dict.tobecreated){
                            mode = "create";
                        } else  if(ss_dict.tobechanged){
                            mode = "update";
                        }
console.log("mode: ", mode)
                        if (mode){
                            const studsubj_dict = {
                                    mode: mode,
                                    student_pk: ss_dict.stud_id,
                                    studsubj_pk: ss_dict.studsubj_id,
                                    schemeitem_pk: ss_dict.schemeitem_id,
                                    is_extra_nocount: ss_dict.is_extra_nocount,
                                    is_extra_counts: ss_dict.is_extra_counts,
                                    pws_title: ss_dict.pws_title,
                                    pws_subjects: ss_dict.pws_subjects
                                };

                            // PR2021-0930 debug: when deleting went wrong subj_publ_id still has value (see MSTUDSUBJ_AddRemoveSubject)
                            // in that case set tobechanged = true and set tobedeleted = false
                            if (ss_dict.tobechanged){
                                studsubj_dict.tobedeleted = false;
                            }
                            studsubj_list.push(studsubj_dict)
                        };  //  if (mode)
                        if (mode === "delete"){
    // - make to_be_deleted tblRow red
                            const row_id = "studsubj_" + ss_dict.stud_id + "_" + ss_dict.studsubj_id
                            const tblRow = document.getElementById(row_id);

                            ShowClassWithTimeout(tblRow, "tsa_tr_error")
                        };
                    };  // if(!isEmpty(ss_dict))
                };
                if(studsubj_list && studsubj_list.length){
                    upload_dict.studsubj_list = studsubj_list;
                    console.log("upload_dict: ", upload_dict)
                    UploadChanges(upload_dict, urls.url_studsubj_upload);
                };
            };  // if(mod_MSTUDSUBJ_dict.stud_id)
        };  // if(may_edit)

// ---  hide modal
        $("#id_mod_studentsubject").modal("hide");
    }  // MSTUDSUBJ_Save

//========= MSTUDSUBJ_Response  ============= PR2021-07-09 PR2021-08-17
    function MSTUDSUBJ_Response(response) {
        console.log("===== MSTUDSUBJ_Response ===== ");
        console.log("response", response);

        const is_test = (!!response.is_test);
        const oneonly_subj_error = (!!response.subj_error);
        const oneonly_student_pk = (response.stud_pk);

        const studsubj_validate_html = response.studsubj_validate_html;

        // studsubj_validate_html comes after updated_studsubj_rows, to refresh datarows before filling lists
        if (studsubj_validate_html){

            el_MSTUDSUBJ_msg_container.innerHTML = studsubj_validate_html
            add_or_remove_class(el_MSTUDSUBJ_msg_container, cls_hide, false)
            if(!is_test){
                MSTUDSUBJ_FillDicts();
                MSTUDSUBJ_FillTbls();
            }
        } else if(!is_test){
            $("#id_mod_studentsubject").modal("hide");

        console.log("response.updated_MSTUDSUBJ_rows", response.updated_MSTUDSUBJ_rows);

            ResponseValidationAll(null, oneonly_student_pk, oneonly_subj_error)
        };

    };  // MSTUDSUBJ_Response

//========= MSTUDSUBJ_FillDicts  ============= PR2020-11-17
    function MSTUDSUBJ_FillDicts() {
        //console.log("===== MSTUDSUBJ_FillDicts ===== ");
        //console.log("mod_MSTUDSUBJ_dict", mod_MSTUDSUBJ_dict);
        // called by MSTUDSUBJ_Open and MSTUDSUBJ_Response ( after save)

        //  mod_MSTUDSUBJ_dict.schemeitem_dict contains all schemitems of the student's scheme
        //  mod_MSTUDSUBJ_dict.studsubj_dict contains the existing, added and deleted subjects of the student
        mod_MSTUDSUBJ_dict.schemeitem_dict = {};
        mod_MSTUDSUBJ_dict.studsubj_dict = {};

        const student_pk = mod_MSTUDSUBJ_dict.stud_id
        const scheme_pk = mod_MSTUDSUBJ_dict.scheme_id

// ---  loop through schemeitem_rows add schemeitems from scheme of this student to mod_MSTUDSUBJ_dict.schemeitem_dict
        el_tblBody_schemeitems.innerText = null;
        if (schemeitem_rows && schemeitem_rows.length ) {
            for (let i = 0, row_dict; row_dict = schemeitem_rows[i]; i++) {
                if (scheme_pk && scheme_pk === row_dict.scheme_id) {
                    // keys are schemeitem_id
                    mod_MSTUDSUBJ_dict.schemeitem_dict[row_dict.id] = {
                        mapid: row_dict.mapid,
                        schemeitem_id: row_dict.id,
                        scheme_id: row_dict.scheme_id,

                        sjtp_id: row_dict.sjtp_id,
                        sjtp_abbrev: row_dict.sjtp_abbrev,
                        sjtp_has_prac: row_dict.sjtp_has_prac,
                        sjtp_has_pws: row_dict.sjtp_has_pws,

                        subj_id: row_dict.subj_id,
                        subj_code: row_dict.subj_code,
                        subj_name: row_dict.subj_name,
                        weight_ce: row_dict.weight_ce,
                        weight_se: row_dict.weight_se,

                        extra_count_allowed: row_dict.extra_count_allowed,
                        extra_nocount_allowed: row_dict.extra_nocount_allowed,
                        has_practexam: row_dict.has_practexam,
                        is_combi: row_dict.is_combi,
                        is_mandatory: row_dict.is_mandatory
                    };
                };
            };
        };


// ---  loop through studsubj_rows
        let has_studsubj_rows = false;
        for (let i = 0, row_dict; row_dict = studsubj_rows[i]; i++) {
            const map_id = row_dict.mapid;
        // add only studsubj from this student
            if (student_pk === row_dict.stud_id) {
                has_studsubj_rows = true;
        // add dict of subject (schemeitem_id) to mod_MSTUDSUBJ_dict.studsubj_dict
                if(row_dict.schemeitem_id){
                    // keys are mapid
                    mod_MSTUDSUBJ_dict.studsubj_dict[row_dict.mapid] = {
                        mapid: row_dict.mapid,
                        stud_id: row_dict.stud_id,
                        scheme_id: row_dict.scheme_id,
                        studsubj_id: row_dict.studsubj_id,
                        schemeitem_id: row_dict.schemeitem_id,
                        subj_id: row_dict.subj_id,
                        subj_publ_id: row_dict.subj_publ_id,

                        is_extra_counts: row_dict.is_extra_counts,
                        is_extra_nocount: row_dict.is_extra_nocount,
                        pws_subjects: row_dict.pws_subjects,
                        pws_title: row_dict.pws_title,

                        tobecreated: false,
                        tobedeleted: row_dict.tobedeleted,
                        undelete: false,
                        tobechanged: false

                        // PR2021-09-28 debug: dont put schemeitem info here, it changes when schemeitem_id changes
                    };
                }
            }
        }

        console.log("..................");
        console.log("mod_MSTUDSUBJ_dict.studsubj_dict:", mod_MSTUDSUBJ_dict.studsubj_dict);
        console.log("mod_MSTUDSUBJ_dict.schemeitem_dict:", mod_MSTUDSUBJ_dict.schemeitem_dict);
        console.log("..................");

        return has_studsubj_rows;
    } // MSTUDSUBJ_FillDicts

//========= MSTUDSUBJ_FillTbls  ============= PR2020-11-17 PR2021-08-31 PR2021-09-29
    function MSTUDSUBJ_FillTbls() {
        console.log("===== MSTUDSUBJ_FillTbls ===== ");
        // function fills table el_tblBody_studsubjects and el_tblBody_schemeitems
        // with items of mod_MSTUDSUBJ_dict.studsubj_dict and mod_MSTUDSUBJ_dict.schemeitem_dict
        // mod_MSTUDSUBJ_dict.studsubj_dict also contains deleted subjects of student, with tag 'deleted'
        // called by MSTUDSUBJ_Open, MSTUDSUBJ_AddRemoveSubject and MSTUDSUBJ_FillTbls(after save)

        el_tblBody_studsubjects.innerText = null;

        // studsubj_si_list is list of schemeitem_id's of subjects of this student, that are not deleted
        const studsubj_si_list = [];
        // studsubj_subj_list is list of subj_id's of subjects of this student, that are not deleted
        const studsubj_subj_list = [];

// ---  create a list of schemeitem_pk's and subject_pk's of this student, not tobedeleted
        let ss_si_pk_list = [], ss_subj_pk_list = [];
        for (const ss_dict of Object.values(mod_MSTUDSUBJ_dict.studsubj_dict)) {
            if (!ss_dict.tobedeleted) {
                if (!ss_si_pk_list.includes(ss_dict.schemeitem_id)){
                    ss_si_pk_list.push(ss_dict.schemeitem_id);
                };
                if (!ss_subj_pk_list.includes(ss_dict.subj_id)){
                    ss_subj_pk_list.push(ss_dict.subj_id);
                };
            };
        };
        const has_studsubj_rows = !!ss_si_pk_list.length;

// ---  loop through mod_MSTUDSUBJ_dict.schemeitem_dict
        // mod_MSTUDSUBJ_dict.schemeitem_dict is a dict with schemeitems of the scheme of this candidate, key = schemeitem_pk
        el_tblBody_schemeitems.innerText = null;
        for (const si_dict of Object.values(mod_MSTUDSUBJ_dict.schemeitem_dict)) {
            const si_schemeitem_pk = si_dict.schemeitem_id;
            const si_subj_pk = si_dict.subj_id;
            let subj_code = (si_dict.subj_code) ? si_dict.subj_code : "";
            if(si_dict.is_mandatory) {subj_code += " ^" };
            if(si_dict.is_combi) { subj_code += " *" };
            const subj_name = (si_dict.subj_name) ? si_dict.subj_name : null;
            const sjtp_abbrev = (si_dict.sjtp_abbrev) ? si_dict.sjtp_abbrev : null;

    // lookup if schemitem_pk exists in studsubj_dictlist
            const add_to_studsubj = ss_si_pk_list.includes(si_schemeitem_pk);
    // lookup if subj_pk exists in studsubj_dictlist, to disable same subject with different subjectype
            const subj_exists_in_ss = ss_subj_pk_list.includes(si_subj_pk);

            let ss_mapid = null, ss_tobedeleted = false;
            if(add_to_studsubj){
                for (const ss_dict of Object.values(mod_MSTUDSUBJ_dict.studsubj_dict)) {
                    if(ss_dict.schemeitem_id === si_schemeitem_pk){
                        ss_mapid = ss_dict.mapid;
                        ss_tobedeleted = ss_dict.tobedeleted;
                        break;
                    };
                };  // for (const ss_dict of Object.values(mod_MSTUDSUBJ_dict.studsubj_dict))
            }
            if (add_to_studsubj){
    // add studsubj to tblBody_studsubjects if it exists in studsubj_dict, not tobedeleted
                MSTUDSUBJ_CreateSelectRow("studsubj", el_tblBody_studsubjects, ss_mapid, si_schemeitem_pk, subj_code, subj_name,
                    si_dict.is_mandatory, si_dict.is_combi, sjtp_abbrev,  true, false, ss_tobedeleted)
            } else {
    // add schemeitem to tblBody_schemeitems if it does not exist in studsubj_dict, or when it is tobedeleted
                MSTUDSUBJ_CreateSelectRow("schemeitem", el_tblBody_schemeitems, null, si_schemeitem_pk, subj_code, subj_name,
                    // enable subject in tblBody_schemeitems when not subj_exists_in_ss
                    si_dict.is_mandatory, si_dict.is_combi, sjtp_abbrev, !subj_exists_in_ss, false, ss_tobedeleted)
            };  // if (add_to_studsubj){
        };  // for (const si_dict] of Object.values(mod_MSTUDSUBJ_dict.schemeitem_dict)) {

// --- addrow 'This_candidate_has_nosubjects' if student has no subjects
        if(!has_studsubj_rows){
            const tblRow = el_tblBody_studsubjects.insertRow(-1);
                const td = tblRow.insertCell(-1);
                    const el_div = document.createElement("div");
                        el_div.classList.add("tw_300", "px-2")
                        el_div.innerText = loc.This_candidate_has_nosubjects;
                td.appendChild(el_div);
        };
    }; // MSTUDSUBJ_FillTbls

//========= MSTUDSUBJ_CreateSelectRow  ============= PR2020--09-30
    function MSTUDSUBJ_CreateSelectRow(tblName, tblBody_select,
            map_id, schemeitem_id, subj_code, subj_name, is_mandatory, is_combi, sjtp_abbrev,
            enabled, highlighted, tobedeleted) {
        //console.log("===== MSTUDSUBJ_CreateSelectRow ===== ");

        //console.log("tblName", tblName);

// ---  lookup index where this row must be inserted
        let ob1 = "", ob2 = "", ob3 = "";
        if (subj_name) { ob1 = subj_name.toLowerCase() };
        if (sjtp_abbrev) { ob2 = sjtp_abbrev.toString()};

        const row_index = b_recursive_tblRow_lookup(tblBody_select, ob1, ob2, ob3, setting_dict.user_lang);

        const tblRow = tblBody_select.insertRow(row_index);
        if (tblName === "studsubj") {
            //PR2021-09-30 debug: don't use tblRow.id to store map_id, already used in tbody of page, couldn't find right tblrow after update
            tblRow.setAttribute("data-mapid", map_id)
        } else {
            tblRow.id = schemeitem_id;
        }

        // bg_transparent added for transition - not working
        //tblRow.classList.add("bg_transparent");

        tblRow.setAttribute("data-selected", 0);

// ---  add title
        let title_txt =subj_name;
        if(is_mandatory) {title_txt += "\n   ^  " + loc.mandatory_subject };
        if(is_combi) {title_txt += "\n   *   " + loc.combination_subject };
        tblRow.title = title_txt;

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);
        tblRow.setAttribute("data-ob2", ob2);
        //tblRow.setAttribute("data-ob3", ob3);

//- add hover to select row
        if(enabled) {add_hover(tblRow)}

        add_or_remove_class(tblRow, "awp_tr_disabled", !enabled )
        if(highlighted){ ShowClassWithTimeout(tblRow, "bg_selected_blue")};

// --- add first td to tblRow.
        let td = tblRow.insertCell(-1);
        let el_div = document.createElement("div");
            el_div.classList.add("tw_020")
            el_div.className = "tickmark_0_0";
              td.appendChild(el_div);

// --- add second td to tblRow.
        td = tblRow.insertCell(-1);
        el_div = document.createElement("div");
            el_div.classList.add("tw_120")
            el_div.innerText = subj_code;
            td.appendChild(el_div);

// --- add second td to tblRow.
        td = tblRow.insertCell(-1);
        el_div = document.createElement("div");
            el_div.classList.add("tw_120")
            el_div.innerText = sjtp_abbrev;
            td.appendChild(el_div);

        //td.classList.add("tw_200X", "px-2", "pointer_show") // , "tsa_bc_transparent")

//--------- add addEventListener
        if(enabled) {
            //tblRow.addEventListener("click", function() {MSTUDSUBJ_SelectSubject(tblName, tblRow)}, false);
            tblRow.addEventListener("click", function() {MSTUDSUBJ_ClickedOrDoubleClicked(tblName, tblRow, event)}, false);

        };

    //console.log("mod_MSTUDSUBJ_dict.sel_studsubj_list", mod_MSTUDSUBJ_dict.sel_studsubj_list);
    //console.log("mod_MSTUDSUBJ_dict.sel_schemeitem_list", mod_MSTUDSUBJ_dict.sel_schemeitem_list);
    //console.log("map_id", map_id);

// --- if added / removed row highlight row for 1 second
        let show_justLinked = false;
        if (tblName === "studsubj" && mod_MSTUDSUBJ_dict.sel_studsubj_list ){
            show_justLinked = mod_MSTUDSUBJ_dict.sel_studsubj_list.includes(map_id);
            // remove map_id from sel_studsubj_list
            if(show_justLinked) { b_remove_item_from_array(mod_MSTUDSUBJ_dict.sel_studsubj_list, map_id)};
        } else if (tblName === "schemeitem"  && mod_MSTUDSUBJ_dict.sel_schemeitem_list ){
            const schemeitem_pk = (schemeitem_id) ? schemeitem_id : null;
            show_justLinked = mod_MSTUDSUBJ_dict.sel_schemeitem_list.includes(schemeitem_pk);
            // remove schemeitem_pk from sel_schemeitem_list
            if(show_justLinked) { b_remove_item_from_array(mod_MSTUDSUBJ_dict.sel_schemeitem_list, schemeitem_pk)};
        }
    //console.log("show_justLinked", show_justLinked);
        if (show_justLinked) {
            //td_first.classList.add(cls_just_linked_unlinked)
            //setTimeout(function (){ td_first.classList.remove(cls_just_linked_unlinked)}, 1000);
            ShowClassWithTimeout(tblRow, "bg_selected_blue", 2000) ;
        }

    } // MSTUDSUBJ_CreateSelectRow

//=========  MSTUDSUBJ_ClickedOrDoubleClicked  ================ PR2019-03-30 PR2021-03-05 PR2021-08-31
    function MSTUDSUBJ_ClickedOrDoubleClicked(tblName, tblRow, event) {
        //console.log("=== MSTUDSUBJ_ClickedOrDoubleClicked");
        //console.log("event.target", event.target);
        //console.log("event.detail", event.detail);
        // PR2020-02-24 dont use doubleclick event, wil also trigger click twice. Use this function instead
        // from https://stackoverflow.com/questions/880608/prevent-click-event-from-firing-when-dblclick-event-fires#comment95729771_29993141

        // currentTarget refers to the element to which the event handler has been attached
        // event.target which identifies the element on which the event occurred.

        // event.detail: for mouse click events: returns the number of clicks.

        switch (event.detail) {
            case 1:
                MSTUDSUBJ_SelectSubject(tblName, tblRow);
                break;
            case 2:
                const may_edit = (permit_dict.permit_crud && permit_dict.requsr_same_school);
                if(may_edit){
                    const mode = (tblName === "studsubj") ? "remove" : "add";
                    MSTUDSUBJ_AddRemoveSubject(mode);
                };
        };

    }  // MSTUDSUBJ_ClickedOrDoubleClicked

//========= MSTUDSUBJ_SelectSubject  ============= PR2020-10-01 PR2021-03-05
    function MSTUDSUBJ_SelectSubject(tblName, tblRow){
        //console.log( "===== MSTUDSUBJ_SelectSubject  ========= ");
        //console.log( "tblRow", tblRow);

        mod_MSTUDSUBJ_dict.sel_studsubj_mapid = null;
        mod_MSTUDSUBJ_dict.sel_schemeitem_pk = null;
        if (tblName === "studsubj"){
            mod_MSTUDSUBJ_dict.sel_studsubj_mapid = get_attr_from_el(tblRow, "data-mapid");
        } else if (tblName === "schemeitem"){
            mod_MSTUDSUBJ_dict.sel_schemeitem_pk = (tblRow.id) ? Number(tblRow.id) : null;
        }
        let is_selected = (!!get_attr_from_el_int(tblRow, "data-selected"));

// ---  toggle is_selected
        is_selected = !is_selected;

// ---  in tbl "studsubj" and when selected: deselect all other rows
        if (tblName === "studsubj" && is_selected){
            MSTUDSUBJ_SetInputFields(mod_MSTUDSUBJ_dict.sel_studsubj_mapid, is_selected)
        }

// ---  put new value in this tblRow, show/hide tickmark PR2020-11-21
        tblRow.setAttribute("data-selected", ( (is_selected) ? 1 : 0) )
        add_or_remove_class(tblRow, "bg_selected_blue", is_selected )
        const img_class = (is_selected) ? "tickmark_0_2" : "tickmark_0_0"
        const el = tblRow.cells[0].children[0];
        if (el){el.className = img_class}
    }  // MSTUDSUBJ_SelectSubject

    function MSTUDSUBJ_SetInputFields(sel_studsubj_mapid, is_selected){
// ---  put value in input box 'Characteristics of this subject
        //console.log( "===== MSTUDSUBJ_SetInputFields  ========= ");
        //console.log( "sel_studsubj_mapid", sel_studsubj_mapid);
        //console.log( "is_selected", is_selected);

        let is_empty = true, is_mand = false, is_mand_subj = false, is_combi = false,
            extra_count_allowed = false, extra_nocount_allowed = false,
            is_extra_counts = false, is_extra_nocount = false,
            sjtp_has_prac = false, sjtp_has_pws = false,
            pwstitle = null, pwssubjects = null,
            subj_name = null;
        let ss_dict = {}, si_dict = {};

        if(is_selected && sel_studsubj_mapid && mod_MSTUDSUBJ_dict.studsubj_dict[sel_studsubj_mapid]){
            ss_dict = mod_MSTUDSUBJ_dict.studsubj_dict[sel_studsubj_mapid];

        //console.log( "ss_dict", ss_dict);
            if(!isEmpty(ss_dict)){
                is_empty = false;
                is_mand = ss_dict.is_mandatory;
                is_mand_subj = ss_dict.is_mand_subj;
                is_combi = ss_dict.is_combi;
                is_extra_counts = ss_dict.is_extra_counts;
                is_extra_nocount = ss_dict.is_extra_nocount;
                pwstitle = ss_dict.pws_title;
                pwssubjects = ss_dict.pws_subjects;

                si_dict = mod_MSTUDSUBJ_dict.schemeitem_dict[ss_dict.schemeitem_id];
                if(!isEmpty(si_dict)){
                    extra_count_allowed = si_dict.extra_count_allowed;
                    extra_nocount_allowed = si_dict.extra_nocount_allowed;
                    sjtp_has_prac = si_dict.sjtp_has_prac;
                    sjtp_has_pws = si_dict.sjtp_has_pws;
                    subj_name = si_dict.subj_name
                }
        //console.log( "si_dict", si_dict);
            }
        }
        el_MSTUDSUBJ_char_header.innerText = (is_empty) ?  loc.No_subject_selected : subj_name;

    // ---  put changed values of input elements in upload_dict
        for (let i = 0, el; el = el_MSTUDSUBJ_input_controls[i]; i++) {
            const el_wrap = el.parentNode.parentNode.parentNode

            const field = get_attr_from_el(el, "data-field")
            const hide_element = (field === "is_mandatory") ? is_empty :
                                (field === "is_mand_subj") ? is_mand_subj :
                                (field === "is_combi") ? is_empty :
                                 (field === "is_extra_nocount") ? !extra_nocount_allowed :
                                 (field === "is_extra_counts") ? !extra_count_allowed :
                                 (["pws_title", "pws_subjects"].includes(field) ) ? !sjtp_has_pws : true;
            if(el_wrap){ add_or_remove_class(el_wrap, cls_hide, hide_element )}

           if(el.classList.contains("awp_input_text")){
                el.value = ss_dict[field];
           } else if(el.classList.contains("awp_input_checkbox")){
                el.checked = (ss_dict[field]) ? ss_dict[field] : false;
           }
        }
    }  // MSTUDSUBJ_SetInputFields

//========= MSTUDSUBJ_AddRemoveSubject  ============= PR2020-11-18 PR2021-08-31
    function MSTUDSUBJ_AddRemoveSubject(mode) {
        console.log("  =====  MSTUDSUBJ_AddRemoveSubject  =====");
        console.log("mode", mode);

        const may_edit = (permit_dict.permit_crud && permit_dict.requsr_same_school);
        if(may_edit){

            let must_validate_subjects = false;

            // for highlighting row in other table after addd/remove
            mod_MSTUDSUBJ_dict.sel_studsubj_list = [];
            mod_MSTUDSUBJ_dict.sel_schemeitem_list = [];

            const tblBody = (mode === "add") ? el_tblBody_schemeitems : el_tblBody_studsubjects;

    // ---  loop through selected schemeitem_pk's of tblBody
            for (let i = 0, tblRow, is_selected; tblRow = tblBody.rows[i]; i++) {
                is_selected = !!get_attr_from_el_int(tblRow, "data-selected")
                if (is_selected) {

// +++++++ add subject
                    if(mode === "add"){
                        const sel_schemeitem_pk = (tblRow.id) ? Number(tblRow.id) : null;
                        // get sel_subject_pk from si_map_dict
                        const si_map_dict = (mod_MSTUDSUBJ_dict.schemeitem_dict[sel_schemeitem_pk]) ? mod_MSTUDSUBJ_dict.schemeitem_dict[sel_schemeitem_pk] : {};
                        const sel_subject_pk = (si_map_dict.subj_id) ? si_map_dict.subj_id : null;
        console.log("............... add subject");
        console.log("sel_schemeitem_pk", sel_schemeitem_pk);
        console.log("sel_subject_pk", sel_subject_pk);

        // ---  loop through studsubj_dict and check if sel_subject_pk already exists
                        let subject_found = false;
                        for (const ss_dict of Object.values(mod_MSTUDSUBJ_dict.studsubj_dict)) {
                   // get ss_subj_id from schemeitem_dict
                            const ss_schemeitem_id = ss_dict.schemeitem_id;
                            const si_dict = (mod_MSTUDSUBJ_dict.schemeitem_dict[ss_schemeitem_id])
                            const ss_subj_id = si_dict.subj_id;

        console.log("ss_dict", ss_dict);
        console.log("si_dict", si_dict);
                            if(ss_subj_id === sel_subject_pk){
                                if (!subject_found) {
                            // this is the first occurrence of sel_subject_pk in ss_dict
                                    subject_found = true;
        console.log("ss_dict.tobedeleted", ss_dict.tobedeleted);
                                    if (ss_dict.tobedeleted){

                           // if the schemeitem_pk of the studsubj_dict is the same as the schemeitem_pk in the selected si_dict
                                        if (ss_dict.schemeitem_id === sel_schemeitem_pk){
                                // if 'tobedeleted' has already been saved, then subj_publ_id = null
                                // in that case: set undelete = true, to undo saved tobedeleted
                                // if it has not been saved yet: just remove tobedeleted

                                // PR2021-0930 debug: when deleting went wrong subj_publ_id still has value
                                // in that case set tobechanged = true
                                            ss_dict.tobecreated = false;
                                            ss_dict.tobedeleted = false;
                                            ss_dict.tobechanged = false;

                                            if(!ss_dict.subj_publ_id){
                                                ss_dict.undelete = true;
                                            } else {
                                                ss_dict.tobechanged = true;
                                            };

                           // change this schemeitem_pk if it is different from the schemeitem_pk in the selected studsubj_dict
                                        } else {
                                            ss_dict.schemeitem_id = sel_schemeitem_pk;
                                            ss_dict.subj_id = sel_subject_pk;

                                            ss_dict.tobecreated = false;
                                            ss_dict.tobedeleted = false;
                                            ss_dict.tobechanged = true;
                                            ss_dict.undelete = false;
                                        };
                                        must_validate_subjects = true;

                            // add to sel_studsubj_list, to highlight subject after adding
                                mod_MSTUDSUBJ_dict.sel_studsubj_list.push(ss_dict.mapid)
                                    } else {
                                        // ss_subject is not deleted - this should not be possible - do nothing
                                    }
                                } else {
                // if student has subject multiple times - delete others  -  this should not be possible
                                    // better not delete others when multiple found
                                    //  maybe the wrong one will be deleted - let the user delete multiple subjects
                                };
                            };
                        };  // for (const ss_dict of Object.values(mod_MSTUDSUBJ_dict.studsubj_dict))

        // - add row to studsubj_dict if it does not yet exist
                        if (!subject_found){
                            const student_pk = mod_MSTUDSUBJ_dict.stud_id;
                            const si_dict = mod_MSTUDSUBJ_dict.schemeitem_dict[sel_schemeitem_pk];

        console.log("add if not exists .si_dict", si_dict);
                            if(!isEmpty(si_dict)){
                                // mapid: "studsubj_29_2" = "studsubj_" + stud_id + "_" + studsubj_id
                                mod_MSTUDSUBJ_dict.new_studsubj_pk += 1;
                                const new_map_id = "studsubj_" + student_pk + "_new" + mod_MSTUDSUBJ_dict.new_studsubj_pk;

                                mod_MSTUDSUBJ_dict.studsubj_dict[new_map_id] = {
                                    mapid: new_map_id,
                                    stud_id: student_pk,
                                    scheme_id: si_dict.scheme_id,
                                    studsubj_id: null,
                                    schemeitem_id: si_dict.schemeitem_id,

                                    subj_id: si_dict.subj_id,
                                    subj_code: si_dict.subj_code,
                                    subj_name: si_dict.subj_name,
                                    subj_publ_id: null,

                                    sjtp_id: si_dict.sjtp_id,
                                    sjtp_abbrev: si_dict.sjtp_abbrev,
                                    sjtp_has_prac: si_dict.sjtp_has_prac,
                                    sjtp_has_pws: si_dict.sjtp_has_pws,

                                    is_combi: si_dict.is_combi,
                                    is_extra_counts: false,
                                    is_extra_nocount: false,
                                    is_mandatory: si_dict.is_mandatory,

                                    pws_subjects: null,
                                    pws_title: null,

                                    tobecreated: true,
                                    tobedeleted: false,
                                    tobechanged: false,
                                    undelete: false
                                };

                                must_validate_subjects = true;
                        // add to sel_studsubj_list, to highlight subject after adding
                                mod_MSTUDSUBJ_dict.sel_studsubj_list.push(new_map_id)
                            };
                        };  // if (!subject_found){

    // +++++++ remove subject
                    } else {
        // ---  set 'tobedeleted' = true if schemeitem_pk already exists in studsubj_dict
                        const sel_map_id = get_attr_from_el(tblRow, "data-mapid");
                        const ss_map_dict = (mod_MSTUDSUBJ_dict.studsubj_dict[sel_map_id]) ? mod_MSTUDSUBJ_dict.studsubj_dict[sel_map_id] : {};

        console.log("ss_map_dict", ss_map_dict);
                        if (!isEmpty(ss_map_dict)) {
                            if (ss_map_dict.tobecreated){
            // when it is a created, not saved, subject: just remove subject from studsubj_dict
                                delete mod_MSTUDSUBJ_dict.studsubj_dict[sel_map_id];
                                must_validate_subjects = true;

                            } else {
                                // when undelete = true:
                                //  - when 'tobedeleted' has already been saved, then subj_publ_id = null
                                //  - when added again: undelete is set 'true'
                                //  - to remove it: set undelete = false and tobedeleted = tru

                                // when tobechanged = true:
                                // - changes have been made, either schemeitem or pws title etc
                                // - when removing this subject: set tobechanged = false, tobedeleted = true
                                //  - note: the new information of schemeitem or pws title etc stays in ss_map_dict

                                ss_map_dict.tobedeleted = true;
                                ss_map_dict.tobechanged = false;
                                ss_map_dict.undelete = false
                            }

                            must_validate_subjects = true;
                        }
                        // to highlight subject after removing
                        mod_MSTUDSUBJ_dict.sel_schemeitem_list.push(ss_map_dict.schemeitem_id)
                    };  //  if(mode === "add"){

                    MSTUDSUBJ_SetInputFields()
                }
            }

        console.log("...............");
        console.log("mod_MSTUDSUBJ_dict.studsubj_dict", mod_MSTUDSUBJ_dict.studsubj_dict);
        console.log("mod_MSTUDSUBJ_dict.schemeitem_dict", mod_MSTUDSUBJ_dict.schemeitem_dict);
        console.log("...............");

    // ---  enable btn submit
            el_MSTUDSUBJ_btn_save.disabled = false;
    // create uploaddict to validate subjects PR2021-08-17
            if (must_validate_subjects){
                MSTUDSUBJ_ValidateSubjects()
            };
            MSTUDSUBJ_FillTbls();
        };  //  if(may_edit){
    }  // MSTUDSUBJ_AddRemoveSubject

//========= MSTUDSUBJ_ValidateSubjects  ============= PR2021-08-29
    function MSTUDSUBJ_ValidateSubjects() {
        //console.log("  =====  MSTUDSUBJ_ValidateSubjects  =====");
// create uploaddict to validate subjects PR2021-08-17
            // ---  loop through studentsubjects
            // studsubj_si_list is list of schemeitem_id's of subjects of this student, that are not deleted
            const studsubj_dictlist = [];
            for (const [studsubj_pk_str, dict] of Object.entries(mod_MSTUDSUBJ_dict.studsubj_dict)) {

            // - add schemeitem_pk of studsubj to studsubj_dictlist
        // also add the choices that are stored in studsubj: is_extra_counts is_extra_nocount
                const studsubj_dict = {
                    tobecreated: !!dict.tobecreated,
                    tobedeleted: !!dict.tobedeleted,
                    tobechanged: !!dict.tobechanged,
                    schemeitem_id: dict.schemeitem_id,
                    studsubj_id: dict.studsubj_id,
                    subj_id: dict.subj_id,
                    subj_code: dict.subj_code,
                    is_extra_counts: dict.is_extra_counts,
                    is_extra_nocount: dict.is_extra_nocount
                }
                studsubj_dictlist.push(studsubj_dict)
            };
            const upload_dict = {
                student_pk: mod_MSTUDSUBJ_dict.stud_id,
                studsubj_dictlist: studsubj_dictlist
            }
           UploadChanges(upload_dict, urls.url_studsubj_validate_test);
    }  // MSTUDSUBJ_ValidateSubjects

//========= MSTUDSUBJ_AddPackage  ============= PR2020-11-18
    function MSTUDSUBJ_AddPackage() {
        //console.log("  =====  MSTUDSUBJ_AddPackage  =====");

        const may_edit = (permit_dict.permit_crud && permit_dict.requsr_same_school);
        if(may_edit){

    // ---  enable btn submit
            el_MSTUDSUBJ_btn_save.disabled = false;
        };
    }  // MSTUDSUBJ_AddPackage

//========= MSTUDSUBJ_InputboxEdit  ============= PR2020-12-01 PR22021-08-31
    function MSTUDSUBJ_InputboxEdit(el_input) {
        console.log("  =====  MSTUDSUBJ_InputboxEdit  =====");
        if(el_input){
            const may_edit = (permit_dict.permit_crud && permit_dict.requsr_same_school);

// ---  get dict of selected schemitem from mod_MSTUDSUBJ_dict.studsubj_dict
            const field = get_attr_from_el(el_input, "data-field")
            const sel_studsubj_dict = mod_MSTUDSUBJ_dict.studsubj_dict[mod_MSTUDSUBJ_dict.sel_studsubj_mapid];

    //console.log("sel_studsubj_dict", sel_studsubj_dict);
            if(sel_studsubj_dict){
    // ---  put new value of el_input in sel_studsubj_dict
                if(el_input.classList.contains("awp_input_text")) {
            //console.log("awp_input_text");
                    if(may_edit){
                        sel_studsubj_dict[field] = el_input.value;
                        sel_studsubj_dict.tobechanged = true;
                    };
    // ---  if checkbox: put checked value in sel_studsubj_dict
                } else if(el_input.classList.contains("awp_input_checkbox")) {
                    if (["is_combi", "is_mandatory", "is_mand_subj"].includes(field)){
                        // is_combi and is_mandatory and is_mand_subj cannot be changed.
                        // setting disabled makes checkbox grey, is not what we want
                        // therefore always undo changes after clicked om this checkbox
                        // also when not may_edit
                        el_input.checked = !el_input.checked;
                    } else {
            //console.log("awp_input_checkbox");
                        if(!may_edit){
                            // undo clicked when not may_edit
                            el_input.checked = !el_input.checked;
                        } else {
                            const is_checked = el_input.checked;
                            sel_studsubj_dict[field] = is_checked;
                            sel_studsubj_dict.tobechanged = true;
        // ---  if element is checked: uncheck other 'extra subject' element if that one is also checked
                            if(is_checked){
                                const other_field = (field === "is_extra_nocount") ? "is_extra_counts" : "is_extra_nocount";
                                const other_el = document.getElementById("id_MSTUDSUBJ_" + other_field)
                                if(other_el && other_el.checked){
                                    other_el.checked = false;
                                    sel_studsubj_dict[other_field] = false;
                                };
                            };
                        };
                    };  // if (field === "is_combi")
                }
    // ---  enable btn submit
        console.log("sel_studsubj_dict.tobechanged", sel_studsubj_dict.tobechanged);
                if (sel_studsubj_dict.tobechanged){
                    el_MSTUDSUBJ_btn_save.disabled = false;
                }
            }  // if(sel_studsubj_dict){
        };
    }  // MSTUDSUBJ_InputboxEdit

//========= MSTUDSUBJ_CheckboxEdit  ============= PR2020-12-01
    function MSTUDSUBJ_CheckboxEdit_NIU(el_input) {
        console.log("  =====  MSTUDSUBJ_CheckboxEdit  =====");
        if(el_input){
            const field = get_attr_from_el(el_input, "data-field")
            const is_checked = el_input.checked;
            const sel_studsubj_dict = mod_MSTUDSUBJ_dict.studsubj_dict[mod_MSTUDSUBJ_dict.sel_schemitem_pk];
            if (sel_studsubj_dict) {
                sel_studsubj_dict[field] = is_checked;
                sel_studsubj_dict.tobechanged = true;
    // if element is checked: uncheck other 'extra subject' element if that one is also checked
                if(is_checked){
                    const other_field = (field === "is_extra_nocount") ? "is_extra_counts" : "is_extra_nocount";
                    const other_el = document.getElementById("id_MSTUDSUBJ_" + other_field)
                //console.log("other_el", other_el);
                    if(other_el && other_el.checked){
                        other_el.checked = false;
                        sel_studsubj_dict[other_field] = false;
                    }
                }
            }
        }
    }  // MSTUDSUBJ_CheckboxEdit

// +++++++++ END MOD STUDENT SUBJECT +++++++++++++++++++++++++++++++++

// +++++++++++++++++ MODAL MULTIPLE OCCURRENCES ++++++++++++++++++++++++++++++++++++++++++

//=========  MMUOC_Open  ================ PR2021-09-05
    function MMUOC_Open() {
        //console.log("===== MMUOC_Open =====");

        if (permit_dict.permit_crud && permit_dict.requsr_same_school) {
             if (mod_MMUOC.rows && mod_MMUOC.rows.length){
        //console.log("mod_MMUOC", mod_MMUOC);
                // MMUOC_fill_table is in MMUOC_toggle_showall
                const show_modal = MMUOC_toggle_showall(true);
                //if(show_modal){
                    $("#id_mod_multiple_occurrences").modal({backdrop: true});
               // };
            };
        };
// ---  show modal
    };
//=========  MMUOC_toggle_showall  ================ PR2021-09-18
    function MMUOC_toggle_showall(hide_linked) {
        //console.log("===== MMUOC_toggle_showall =====");
        if (hide_linked){
            mod_MMUOC.show_all = false
        } else {
            mod_MMUOC.show_all = !mod_MMUOC.show_all;
        }
        el_MMUOC_btn_showall.innerText = (mod_MMUOC.show_all) ? loc.Hide_linked_candidates : loc.Show_all_matching_candidates
        const has_unlinked_rows = MMUOC_fill_table();
        const show_modal = has_unlinked_rows || mod_MMUOC.show_all;
        return show_modal;
    };  // MMUOC_toggle_showall

//=========  MMUOC_fill_table  ================ PR2021-09-17
    function MMUOC_fill_table() {
        let has_unlinked_rows = false;
        if(el_MMUOC_data_container){
            el_MMUOC_data_container.innerHTML = null;
            if (mod_MMUOC.rows && mod_MMUOC.rows.length){
                for (let i = 0, dict; dict = mod_MMUOC.rows[i]; i++) {
                    const cur = dict.cur_stud;
                    const other = dict.other_stud;

                    const cur_student_id_delim = (cur.student_id) ? ";" + cur.student_id + ";" : "";
            //console.log("cur_student_id_delim", cur_student_id_delim);

                    const linked_arr_str = (cur.linked) ? ";" + cur.linked + ";" : null;
                    const notlinked_arr_str = (cur.notlinked) ? ";" + cur.notlinked + ";" : null;
            //console.log("linked_arr_str", linked_arr_str);
            //console.log("notlinked_arr_str", notlinked_arr_str);

                    let show_cur_box = false;

        // - check if student has linked students
                    const el_cur_box = document.createElement("div");
                    el_cur_box.classList.add("p-2", "my-1");

                    const el_stud_name = document.createElement("h6");
                    el_stud_name.innerText = [cur.fullname, " - ", cur.depbase_code, cur.lvlbase_code, cur.sctbase_code,].join(' ');
                    el_cur_box.appendChild(el_stud_name);
                    el_MMUOC_data_container.appendChild(el_cur_box);

                    for (let j = 0, other; other = dict.other_stud[j]; j++) {
                        const other_student_id_delim = (other.student_id) ? ";" + other.student_id + ";" : "";

                        const el_other_box = document.createElement("div");
                        el_cur_box.appendChild(el_other_box);

                        const is_linked = (!!linked_arr_str && linked_arr_str.includes(other_student_id_delim));
                        const is_notlinked = (!!notlinked_arr_str && notlinked_arr_str.includes(other_student_id_delim));
                        add_or_remove_attr(el_other_box, "data-linked", is_linked )
                        add_or_remove_attr(el_other_box, "data-notlinked", is_notlinked )

                        const show_other = (mod_MMUOC.show_all) || (!is_linked && !is_notlinked);
                        // Note: class 'display_hide' not working when classList has also 'note_flex_1'
                        add_or_remove_class(el_other_box, "note_flex_1", show_other, "display_hide")
                        if(show_other){
                            show_cur_box = true;
                            has_unlinked_rows = true;
                            }

                        const el_cross = document.createElement("div");
                        el_cross.classList.add("p-1", "pointer_show")
                        el_cross.setAttribute("data-cur_stud_id", cur.student_id);
                        el_cross.setAttribute("data-oth_stud_id", other.student_id);
                        el_cross.addEventListener("click", function() {MMUOC_tick_cross(el_cross, "cross")}, false);
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
                        el_tick.setAttribute("data-cur_stud_id", cur.student_id);
                        el_tick.setAttribute("data-oth_stud_id", other.student_id);
                        el_tick.addEventListener("click", function() {MMUOC_tick_cross(el_tick, "tick")}, false);
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

                        const other_name = [other.examyear, other.fullname, other.school_name, other.deplvlsct, other.result_info,].join(' - ')
                        const el_info = document.createElement("div");
                        el_info.classList.add("p-1");
                        el_other_box.appendChild(el_info);
                            const el_info_small = document.createElement("small");
                            el_info_small.classList.add("c_form_text", "mx-2");
                            el_info_small.innerText = other_name;
                            el_info.appendChild(el_info_small);
                    };  //  for (let j = 0, other; other = dict.other_stud[j]; j++) {

                    // show row only if it has one one more orther boxes that are shown
                    if(!show_cur_box){el_cur_box.classList.add("display_hide")};
                };  // for (let i = 0, dict; dict = mod_MMUOC[i]; i++)
            };  // if (mod_MMUOC.rows and mod_MMUOC.rows.length){
        };  // if(el_MMUOC_data_container)
        return has_unlinked_rows;
    };  //  MMUOC_fill_table

//=========  MMUOC_tick_cross  ================ PR2021-09-05
    function MMUOC_tick_cross(el, mode) {
        //console.log("===== MMUOC_tick_cross =====");
        //console.log("el", el);
        //console.log("mode", mode);

        if (permit_dict.permit_crud && permit_dict.requsr_same_school) {
            const el_other_box = el.parentNode
            const is_linked = get_attr_from_el(el_other_box, "data-linked")
            const is_notlinked = get_attr_from_el(el_other_box, "data-notlinked")

            const cur_stud_id = get_attr_from_el_int(el, "data-cur_stud_id");
            const oth_stud_id = get_attr_from_el_int(el, "data-oth_stud_id");

    // ---  Upload Changes
            let upload_dict = {mode: mode,
                               cur_stud_id: cur_stud_id,
                               oth_stud_id: oth_stud_id,
                               table: "student"};
            if (mode === "tick"){
                // set linked when clicked on 'tick' and is_linked = false
                // remove linked when clicked on 'tick' and is_linked = true
                upload_dict.linked = !is_linked;
            } else if (mode === "cross"){
                // set notlinked when clicked on 'cross' and is_notlinked = false
                // remove notlinked when clicked on 'cross' and is_notlinked = true
                upload_dict.notlinked = !is_notlinked;
            }

            UploadChanges(upload_dict, urls.url_student_biscand);
        };

    };  // MMUOC_tick_cross

//=========  MMUOC_response  ================ PR2021-09-18
    function MMUOC_response(updated_rows) {
        //console.log("===== MMUOC_response =====");
        if (updated_rows && updated_rows.length){
            const updated_dict = updated_rows[0]
            //console.log("updated_dict: ", updated_dict);
            if(updated_dict.cur_stud && updated_dict.cur_stud.student_id){
                for (let i = 0, dict; dict = mod_MMUOC.rows[i]; i++) {
                    if (dict.cur_stud && dict.cur_stud.student_id){
                        if (dict.cur_stud.student_id === updated_dict.cur_stud.student_id){
                            mod_MMUOC.rows[i] = deepcopy_dict(updated_dict);
                            break;
                }}};
                MMUOC_fill_table();
            };
        };
    }; // MMUOC_response

// +++++++++++++++++ MODAL SIDEBAR SELECT ++++++++++++++++++++++++++++++++++++++++++
//=========  SBR_display_subject_student  ================ PR2021-07-24
    function SBR_display_subject_student() {
        //console.log("===== SBR_display_subject_student =====");
        let subject_code = null, subject_name = null, student_code = null, student_name = null;
        if(setting_dict.sel_subject_pk){
            if(setting_dict.sel_subject_code){subject_code = setting_dict.sel_subject_code};
            if(setting_dict.sel_subject_name){subject_name = setting_dict.sel_subject_name};
        } else if (setting_dict.sel_student_pk){
            if(setting_dict.sel_student_name_init){student_code = setting_dict.sel_student_name_init};
            if(setting_dict.sel_student_name){student_name = setting_dict.sel_student_name};
        }
        t_MSSSS_display_in_sbr("subject", setting_dict.sel_subject_pk);
        t_MSSSS_display_in_sbr("student", setting_dict.sel_student_pk);
    };  // SBR_display_subject_student

//=========  HandleSbrLevelSector  ================ PR2021-07 - 23
    function HandleSbrLevelSector(mode, el_select) {
        //console.log("===== HandleSbrLevelSector =====");
        //console.log( "el_select.value: ", el_select.value, typeof el_select.value)
        let upload_dict = {};
        const new_setting = {page: "page_studsubj"}
        if (mode === "level"){
            setting_dict.sel_lvlbase_pk = (Number(el_select.value)) ? Number(el_select.value) : null;
            setting_dict.sel_level_abbrev = (el_select.options[el_select.selectedIndex]) ? el_select.options[el_select.selectedIndex].text : null;

            upload_dict = {selected_pk: {sel_lvlbase_pk: setting_dict.sel_lvlbase_pk}};

            new_setting.sel_lvlbase_pk = setting_dict.sel_lvlbase_pk;

        } else if (mode === "sector"){
            setting_dict.sel_sctbase_pk = (Number(el_select.value)) ? Number(el_select.value) : null;
            setting_dict.sel_sector_abbrev = (el_select.options[el_select.selectedIndex]) ? el_select.options[el_select.selectedIndex].text : null;

            upload_dict = {selected_pk: {sel_sctbase_pk: setting_dict.sel_sctbase_pk}};

            new_setting.sel_sctbase_pk = setting_dict.sel_sctbase_pk;
        }

// ---  upload new setting - done in DatalistDownload
        //b_UploadSettings (upload_dict, urls.url_settings_upload);

        //UpdateHeaderLeft();
       // FillTblRows();

// --- reset table rows, dont delete  header
        tblBody_datatable.innerText = null;

        const datalist_request = {
            setting: new_setting,
            studentsubject_rows: {cur_dep_only: true},
        };
        //console.log("datalist_request", datalist_request);
        DatalistDownload(datalist_request);
    }  // HandleSbrLevelSector

//=========  HandleShowAll  ================ PR2020-12-17
    function HandleShowAll() {
        //console.log("=== HandleShowAll");
        //console.log("setting_dict", setting_dict);

        setting_dict.sel_lvlbase_pk = null;
        setting_dict.sel_level_abbrev = null;

        setting_dict.sel_sctbase_pk = null;
        setting_dict.sel_sector_abbrev = null;

        setting_dict.sel_subject_pk = null;
        setting_dict.sel_student_pk = null;

        el_SBR_select_level.value = null;
        el_SBR_select_sector.value = null;

        filter_dict = {};
        const el_th_filter = document.getElementById("id_th_filter");
        //console.log("el_th_filter", el_th_filter);
        if (el_th_filter){
             let filter_toggle_elements = el_th_filter.querySelectorAll(".awp_filter_toggle");
             for (let i = 0, el; el = filter_toggle_elements[i]; i++) {
        //console.log("el", el);
                el.className = "tickmark_2_2";
             }
        }

// ---  upload new setting
        const selected_pk_dict = {sel_lvlbase_pk: null, sel_sctbase_pk: null, sel_subject_pk: null, sel_student_pk: null};
        //const page_grade_dict = {sel_btn: "grade_by_all"}
       //const upload_dict = {selected_pk: selected_pk_dict, page_grade: page_grade_dict};
        const upload_dict = {selected_pk: selected_pk_dict};
        b_UploadSettings (upload_dict, urls.url_settings_upload);
        HandleBtnSelect(selected_btn, true) // true = skip_upload
        // also calls: FillTblRows(), MSSSS_display_in_sbr(), UpdateHeader()

        const datalist_request = {
                setting: {
                    page: "page_studsubj",
                    sel_lvlbase_pk: null,
                    sel_sctbase_pk: null,
                    sel_subject_pk: null,
                    sel_student_pk: null
                },
                studentsubject_rows: {cur_dep_only: true},
            };
        DatalistDownload(datalist_request);
    }  // HandleShowAll

// +++++++++++++++++ END OF MODAL SIDEBAR SELECT +++++++++++++++++++++++++++++++++++

// +++++++++ MOD EX3 FORM++++++++++++++++ PR2021-10-06
    function MEX3_Open(){
        console.log(" -----  MEX3_Open   ----")
        mod_MEX3_dict = {};

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
        const subj_name = (row_dict.subj_name) ? row_dict.subj_name : "---";
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
            el_div.innerText = subj_name;
            td.appendChild(el_div);

        //td.classList.add("tw_200X", "px-2", "pointer_show") // , "tsa_bc_transparent")

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




// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2021-08-13
    function ModConfirmOpen(mode, el_input) {
        console.log(" -----  ModConfirmOpen   ----")
        console.log("mode", mode)
        // values of mode are : "delete", "inactive" or "send_activation_email", "permission_sysadm"
            //AddSubmenuButton(el_submenu, loc.Preliminary_Ex1_form, null, null, "id_submenu_download_ex1", urls.url_grade_download_ex1, true);  // true = download
            //AddSubmenuButton(el_submenu, loc.Preliminary_Ex1_form, null, null, "id_submenu_download_ex1", urls.url_grade_download_ex1, true);  // true = download

        mod_dict = {mode: mode};

        if (mode === "prelim_ex1"){
            el_confirm_header.innerText = loc.Download_Ex_form;
            el_confirm_loader.classList.add(cls_visible_hide)
            el_confirm_msg_container.className = "p-3";

            const msg_html = "<p>" + loc.The_preliminary_Ex1_form + loc.will_be_downloaded + "</p><p>" + loc.Do_you_want_to_continue + "</p>"
            el_confirm_msg_container.innerHTML = msg_html;
            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            if (el_modconfirm_link) {
                el_modconfirm_link.setAttribute("href", urls.url_grade_download_ex1);
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

        } else if (mode === "has_exemption"){
            if (permit_dict.permit_crud && permit_dict.requsr_same_school) {
                const tblRow = get_tablerow_selected(el_input);
                mod_dict.map_id = tblRow.id;
                mod_dict.stud_pk = get_attr_from_el_int(tblRow, "data-stud_pk");
                mod_dict.studsubj_pk = get_attr_from_el_int(tblRow, "data-studsubj_pk");
                mod_dict.fldName = get_attr_from_el(el_input, "data-field");

                const [index, found_dict] = get_datadict_by_studpk_studsubjpk(mod_dict.stud_pk, mod_dict.studsubj_pk)
                const data_dict = (!isEmpty(found_dict)) ? found_dict : null;
                const subj_name = data_dict.subj_name;
        console.log("data_dict", data_dict)
        // ---  put text in modal form
                let dont_show_modal = false;

                let header_text = loc.Delete_exemption;
                el_confirm_header.innerText = header_text;
                const msg_html = ["<p>", loc.This_exemption, loc._of_, data_dict.fullname, loc.will_be_deleted,
                                    "<ul><li>", data_dict.subj_name, "</li></ul></p><p>",
                                loc.Do_you_want_to_continue, "</p>"].join("")
                el_confirm_msg_container.innerHTML = msg_html;
                el_confirm_msg_container.className = "p-3";

                el_confirm_loader.className = cls_hide;

                el_confirm_btn_save.innerText = loc.Yes_delete;
                el_confirm_btn_cancel.innerText = loc.No_cancel;
                add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", true, "btn-primary");

        // set focus to cancel button
                setTimeout(function (){
                    el_confirm_btn_cancel.focus();
                }, 500);
    // show modal
                $("#id_mod_confirm").modal({backdrop: true});

            }
        }  //  if (mode === "prelim_ex1"){
    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2019-06-23
    function ModConfirmSave() {
        //console.log(" --- ModConfirmSave --- ");
        //console.log("mod_dict: ", mod_dict);

        let close_modal = false;
        if (mod_dict.mode === "prelim_ex1"){
            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            if (el_modconfirm_link) {
                el_modconfirm_link.click();
            // show loader
                el_confirm_loader.classList.remove(cls_visible_hide)

            // close modal after 5 seconds
                setTimeout(function (){ $("#id_mod_confirm").modal("hide") }, 5000);
            };
        } else if (mod_dict.mode === "has_exemption"){
            const tblRow = document.getElementById(mod_dict.map_id);
            const fldName = mod_dict.mode;
            const el_input = tblRow.querySelector("[data-field=" + fldName + "]");

            const new_value = false;
     // ---  change icon, before uploading
            add_or_remove_class(el_input, "tickmark_1_2", new_value, "tickmark_0_0");
// ---  upload changes
            const upload_dict = {
                student_pk: mod_dict.stud_pk,
                studsubj_pk: mod_dict.studsubj_pk
            };
            upload_dict[fldName] = new_value;
            UploadChanges(upload_dict, urls.url_studsubj_single_update);

            close_modal = true;

            UploadChanges(upload_dict, urls.url_subject_upload);
        }  //     if (mode === "prelim_ex1"){

// ---  hide modal
        if(close_modal) {
            $("#id_mod_confirm").modal("hide");
        }
    }  // ModConfirmSave

//=========  ModConfirmResponse  ================ PR2019-06-23
    // NOT IN USE
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
            //el_confirm_msg01.innerText = msg01_txt;
            //el_confirm_msg02.innerText = msg02_txt;
            //el_confirm_msg03.innerText = msg03_txt;
            el_confirm_btn_cancel.innerText = loc.Close
            el_confirm_btn_save.classList.add(cls_hide);
        } else {
        // hide mod_confirm when no message
            $("#id_mod_confirm").modal("hide");
        }
    }  // ModConfirmResponse

//###########################################################################
// +++++++++++++++++ REFRESH DATA ROWS +++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataRowsAfterUploadFromExcel  ================ PR2021-07-20
    function RefreshDataRowsAfterUploadFromExcel(response) {
        //console.log(" --- RefreshDataRowsAfterUploadFromExcel  ---");
        //console.log( "response", response);
        const is_test = (!!response && !!response.is_test) ;
        //if(!is_test && response && "updated_studsubj_rows" in response) {
        //    RefreshDataRows("studsubj", response.updated_studsubj_rows, studsubj_rows, true)  // true = update
        //
        //    DownloadValidationStatusNotes();
        //}
        //console.log( "is_test", is_test);
        if(!is_test) {
            const datalist_request = {
                setting: {page: "page_studsubj"},
                studentsubject_rows: {cur_dep_only: true},
                published_rows: {get: true}
            };
            DatalistDownload(datalist_request);
        }

    }  //  RefreshDataRowsAfterUploadFromExcel

//=========  RefreshDataRows  ================  PR2021-06-21
    function RefreshDataRows(tblName, update_rows, data_rows, is_update) {
        console.log(" --- RefreshDataRows  ---");
        console.log("update_rows", update_rows);
        console.log("is_update", is_update);

        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length
        if (update_rows && update_rows.length ) {
            const field_setting = field_settings[selected_btn];
            for (let i = 0, update_dict; update_dict = update_rows[i]; i++) {
                RefreshDatarowItem(tblName, field_setting, update_dict, data_rows);
            }
        } else if (!is_update) {
            // empty the data_rows when update_rows is empty PR2021-01-13 debug forgot to empty data_rows
            // PR2021-03-13 debug. Don't empty de data_rows when is update. Returns [] when no changes made
           data_rows = [];
        }
    }  //  RefreshDataRows


//=========  RefreshDatarowItem  ================ PR2020-08-16 PR2020-09-30 PR2021-06-21
    function RefreshDatarowItem(tblName, field_setting, update_dict, data_rows) {
        console.log(" --- RefreshDatarowItem  ---");
        //console.log("tblName", tblName);
        //console.log("field_setting", field_setting);
        console.log("update_dict", update_dict);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);
    console.log(".........update_dict.mapid", update_dict.mapid);

            let field_error_list = [];
            const error_list = get_dict_value(update_dict, ["error"], []);
            if(error_list && error_list.length){

    // - show modal messages
                b_ShowModMessages(error_list);

    // - add fields with error in field_error_list, to put old value back in field
                for (let i = 0, msg_dict ; msg_dict = error_list[i]; i++) {
                    if ("field" in msg_dict){field_error_list.push(msg_dict.field)};
                };
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
    //console.log("data_rows", data_rows);

    // ---  create row in table., insert in alphabetical order
                const new_tblRow = CreateTblRow(tblName, field_setting, map_id, update_dict)

                if(new_tblRow){
    // --- add1 to item_count and show total in sidebar
                    selected.item_count += 1;
                    set_sbr_itemcount_txt();
    // ---  scrollIntoView,
                    new_tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' })
    // ---  make new row green for 2 seconds,
                    ShowOkElement(new_tblRow);
                }
            } else {

// +++ get existing data_dict from data_rows. data_rows is ordered by: stud_id, studsubj_id'
                // 'ORDER BY st.id, studsubj.studsubj_id NULLS FIRST'
                const student_pk = (update_dict && update_dict.stud_id) ? update_dict.stud_id : null;
                const studsubj_pk = (update_dict && update_dict.studsubj_id) ? update_dict.studsubj_id : null;
                const [index, found_dict] = get_datadict_by_studpk_studsubjpk(student_pk, studsubj_pk);

                const data_dict = (!isEmpty(found_dict)) ? found_dict : null;
        console.log(".........data_dict", data_dict);
        console.log(".........data_dict.mapid", data_dict.mapid);
                const datarow_index = index;


        //console.log(".........student_pk", student_pk);
        //console.log(".........studsubj_pk", studsubj_pk);
        //console.log(".........data_dict", data_dict);


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
                            set_sbr_itemcount_txt();
                        };
                    }
                } else {

// +++++++++++ updated row +++++++++++
    // ---  check which fields are updated, add to list 'updated_columns'
                    if(!isEmpty(data_dict) && field_names){

        console.log("......... updated data_dict", data_dict);
// ---  first add updated fields to updated_columns list, before updating data_row
                        let updated_columns = [];
                        // first column subj_error
                        for (let i = 0, col_field, old_value, new_value; col_field = field_names[i]; i++) {
// ---  'status' fields are not in data_row
                            if (col_field.includes("_status")){
                                const [old_status_className, old_status_title] = UpdateFieldStatus(col_field, data_dict);
                                const [new_status_className, new_status_title] = UpdateFieldStatus(col_field, update_dict);
                                if (old_status_className !== new_status_className || old_status_title !== new_status_title ) {
                                    updated_columns.push(col_field)
                                };
                            } else if (col_field in data_dict && col_field in update_dict){
                                if (data_dict[col_field] !== update_dict[col_field] ) {
                                    updated_columns.push(col_field)
                                };
                            };
                        };
        console.log("updated_columns", updated_columns);

// ---  update fields in data_row
                        for (const [key, new_value] of Object.entries(update_dict)) {
                            if (key in data_dict){
                                const old_value = data_dict[key]

                                if (new_value !== data_dict[key]) {
                                    data_dict[key] = new_value
        //console.log("----- key: ", key);
        //console.log("old_value: ",old_value, typeof old_value );
        //console.log("new_value: ",new_value, typeof new_value );
                        }}};

// ---  update field in tblRow
                        // note: when updated_columns is empty, then updated_columns is still true.
                        // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
                        // PR2021-09-29 always update all comuns, to remove striketrhrough after undelete
                        // was: if(updated_columns.length || field_error_list.length){
    //console.log("updated_columns", updated_columns);
    //console.log("field_error_list", field_error_list);

// --- get existing tblRow
                            let tblRow = document.getElementById(map_id);
    console.log("tblRow", tblRow);
                            if(tblRow){
                // to make it perfect: move row when first or last name have changed
                                if (updated_columns.includes("name")){
                                //--- delete current tblRow
                                    tblRow.parentNode.removeChild(tblRow);
                                //--- insert row new at new position
                                    tblRow = CreateTblRow(tblName, field_setting, map_id, update_dict)
                                };

                // loop through cells of row
                                const tobedeleted = (update_dict.tobedeleted) ? update_dict.tobedeleted : false;
    console.log("tobedeleted", tobedeleted);
                                for (let i = 1, el_fldName, el, td; td = tblRow.cells[i]; i++) {
                                    el = td.children[0];
                                    if (el){
                                        el_fldName = get_attr_from_el(el, "data-field")
                                        UpdateField(el, update_dict, tobedeleted);

    // get list of error messages for this field
    /*
                                        let msg_list = null;
                                        if (field_error_list.includes(el_fldName)) {
                                            for (let i = 0, msg_dict ; msg_dict = error_list[i]; i++) {
                                                if (msg_dict && "field" in msg_dict) {
                                                    msg_list = msg_dict.msg_list;
                                                    break;
                                                }
                                            }
                                        }
                                        if(el_fldName && msg_list && msg_list.length){
                                        // mage input box red
                                            const el_MSUBJ_input = document.getElementById("id_MSUBJ_" + el_fldName);
                                            if(el_MSUBJ_input){el_MSUBJ_input.classList.add("border_bg_invalid")};

                                        // put msgtext in msg box
                                            b_render_msg_container("id_MSUBJ_msg_" + el_fldName, msg_list)
                                        }
    */
                // make field green when field name is in updated_columns
                                        if(updated_columns.includes(el_fldName)){
    console.log("ShowOkElement(el)", el);
                                            ShowOkElement(el);
                                        };
                                    }  //  if (el){
                                };  //  for (let i = 1, el_fldName, el; el = tblRow.cells[i]; i++) {
                            };  // if(tblRow){
                        //}; //  if(updated_columns.length){
                    };  //  if(!isEmpty(update_dict))
                };  //  if(is_deleted)
            }; // if(is_created)
        };  // if(!isEmpty(update_dict))
    }  // RefreshDatarowItem

//###########################################################################

//=========  remove_studsubjrow_without_subject  ================ PR2020-12-20
    function remove_studsubjrow_without_subject(map_id) {
        //console.log(" --- remove_studsubjrow_without_subject  ---");
        //console.log("map_id", map_id);
        // function removes row of this student without subject (if it exists)
        if (map_id) {
            const arr = map_id.split("_");
            if (arr.length === 3){
                const mapid_empty_row =  arr[0] + "_" + arr[1] + "_"
                const tblRow = document.getElementById(mapid_empty_row);
    //--- delete tblRow
                if (tblRow){
                    const tblBody = tblRow.parentNode
                    if (tblBody){ tblBody.removeChild(tblRow) };
                }
            }
        }
    }  //  remove_studsubjrow_without_subject

//=========  make_studsubjrow_empty  ================ PR2020-12-23
    // TODO not in use yet
    function make_studsubjrow_empty(map_id) {
        //console.log(" --- make_studsubjrow_empty  ---");
        //console.log("map_id", map_id);
        // isteda of deleting last row of a student: make it empty
        if (map_id) {
            const arr = map_id.split("_");
            if (arr.length === 3){
                const mapid_empty_row =  arr[0] + "_" + arr[1] + "_"
                const tblRow = document.getElementById(mapid_empty_row);
    //--- empty tblRow
                if (tblRow){
                    //const tblBody = tblRow.parentNode
                    //if (tblBody){ tblBody.removeChild(tblRow) };
                }
            }
        }
    }  //  make_studsubjrow_empty


//###########################################################################
// +++++++++++++++++ FILTER ++++++++++++++++++++++++++++++++++++++++++++++++++
//========= HandleFilterKeyup  ================= PR2021-08-21
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

//========= HandleFilterToggle  =============== PR2021-08-21
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
        console.log( "col_index", col_index);
        console.log( "filter_tag", filter_tag);
        console.log( "field_name", field_name);
        console.log( "filter_dict", filter_dict);

    // - get current value of filter from filter_dict, set to '0' if filter doesn't exist yet
        const filter_array = (col_index in filter_dict) ? filter_dict[col_index] : [];
        const filter_value = (filter_array[1]) ? filter_array[1] : "0";
        console.log( "filter_array", filter_array);
        console.log( "filter_value", field_name);

        let new_value = "0", icon_class = "tickmark_0_0"
        if(filter_tag === "toggle") {
            // default filter triple '0'; is show all, '1' is show tickmark, '2' is show without tickmark
    // - toggle filter value
            new_value = (filter_value === "2") ? "0" : (filter_value === "1") ? "2" : "1";
    // - get new icon_class
            icon_class =  (new_value === "2") ? "tickmark_2_1" : (new_value === "1") ? "tickmark_2_2" : "tickmark_0_0";
        // default filter triple '0'; is show all, '1' is show tickmark, '2' is show without tickmark
        } else if (field_name === "subj_error"){
// - toggle filter value
            new_value = (filter_value === "2") ? "0" : (filter_value === "1") ? "2" : "1";
// - get new icon_class
            icon_class =  (new_value === "2") ? "note_2_6" : (new_value === "1") ? "note_1_3" : "note_0_0";

        } else if (field_name === "subj_status"){
            // filter_values are: '0'; is show all, 1: not approved, 2: auth1 approved, 3: auth2 approved, 4: auth1+2 approved, 5: submitted,   TODO '6': tobedeleted '7': locked
// - toggle filter value
            let value_int = (Number(filter_value)) ? Number(filter_value) : 0;
        console.log( "......filter_value", filter_value);
            value_int += 1;
        console.log( "......value_int", value_int, typeof  value_int);
            if (value_int > 5 ) { value_int = 0};
            // convert 0 to null, otherwise  "0" will not filter correctly
            new_value = (value_int) ? value_int.toString() : null;
        console.log( "......new_value", new_value, typeof  new_value);
// - get new icon_class
            icon_class =  (new_value === "5") ? "diamond_0_4" :
                            (new_value === "4") ? "diamond_3_3" :
                            (new_value === "3") ? "diamond_1_2" :
                            (new_value === "2") ? "diamond_2_1" :
                            (new_value === "1") ? "diamond_0_0" : "tickmark_0_0";
        console.log( "......icon_class", icon_class);
        }
        console.log( ">>>>>>>> col_index", col_index);
    // - put new filter value in filter_dict
        filter_dict[col_index] = [filter_tag, new_value]

        el_input.className = icon_class;

        Filter_TableRows();

    };  // HandleFilterToggle

//========= Filter_TableRows  ==================================== PR2020-08-17  PR2021-08-10
    function Filter_TableRows() {
        //console.log( "===== Filter_TableRows  ========= ");
        //console.log( "filter_dict", filter_dict);
        t_Filter_TableRows(tblBody_datatable, filter_dict, selected, loc.Subject, loc.Subjects.toLowerCase() );
/*
        selected.item_count = 0
// ---  loop through tblBody.rows
        for (let i = 0, tblRow, show_row; tblRow = tblBody_datatable.rows[i]; i++) {
            tblRow = tblBody_datatable.rows[i]
            show_row = t_ShowTableRowExtended(filter_dict, tblRow);
            add_or_remove_class(tblRow, cls_hide, !show_row);
            if (show_row) {selected.item_count += 1};
        }
// ---  show total in sidebar
        set_sbr_itemcount_txt();
*/
    }; // Filter_TableRows

//========= set_sbr_itemcount_txt  ======= PR2021-08-21
    function set_sbr_itemcount_txt() {
        if (el_SBR_item_count){
            let inner_text = null;
            if (selected.item_count){
                const format_count = f_format_count(setting_dict.user_lang, selected.item_count);
                const cand_txt = ((selected.item_count === 1) ? loc.Subject : loc.Subjects).toLowerCase();
                inner_text = [loc.Total, format_count, cand_txt].join(" ");
            }
            el_SBR_item_count.innerText = inner_text;
        };
    } // set_sbr_itemcount_txt

//========= ResetFilterRows  ====================================
    function ResetFilterRows() {  // PR2019-10-26 PR2020-06-20 PR2021-08-21
        //console.log( "===== ResetFilterRows  ========= ");

        selected.studsubj_dict = null;
        selected.student_pk = null;
        selected.subject_pk = null;

        filter_dict = {};
        filter_mod_employee = false;

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
                            el.className = "tickmark_0_0";
                        }
                    }
                }
            }
       };
       //console.log("function ResetFilterRows");
        FillTblRows();
    }  // function ResetFilterRows

//###########################################################################
// +++++++++++++++++ MODAL SELECT EXAMYEAR OR DEPARTMENT  ++++++++++++++++++++
// functions are in table.js, except for MSED_Response

//=========  MSED_Response  ================ PR2020-12-18 PR2021-05-10
    function MSED_Response(new_setting) {
        //console.log( "===== MSED_Response ========= ");
        //console.log( "new_setting", new_setting);

// ---  upload new selected_pk
        new_setting.page = setting_dict.sel_page;
// also retrieve the tables that have been changed because of the change in examyear / dep
        const datalist_request = {
                setting: new_setting,
                student_rows: {get: true},
                studentsubject_rows: {get: true},
                grade_rows: {get: true},
                schemeitem_rows: {get: true}
            };
        DatalistDownload(datalist_request);

    }  // MSED_Response


//###########################################################################
//=========  MSSSS_Response  ================ PR2021-01-23 PR2021-07-26
    function MSSSS_Response(tblName, selected_dict, selected_pk) {
        //console.log( "===== MSSSS_Response ========= ");
        //console.log( "tblName", tblName);
        //console.log( "selected_pk", selected_pk);
        //console.log( "selected_dict", selected_dict);

        if(selected_pk === -1) { selected_pk = null};

// +++ get existing data_dict from data_rows
        //const data_rows = (tblName === "subject") ? subject_rows : (tblName === "student") ? student_rows : null;
        //const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", selected_pk);
        //const data_dict = selected_dict
        //const datarow_index = index;

        if (tblName === "school") {

// ---  upload new setting and refresh page
            const datalist_request = {
                    setting: {page: "page_studsubj",
                        sel_schoolbase_pk: selected_pk
                    },
                    school_rows: {get: true},
                    department_rows: {get: true},
                    level_rows: {cur_dep_only: true},
                    sector_rows: {cur_dep_only: true},
                    student_rows: {cur_dep_only: true},
                    studentsubject_rows: {cur_dep_only: true},
                    schemeitem_rows: {cur_dep_only: true}
                };

            DatalistDownload(datalist_request);

        } else if (tblName === "subject") {
            setting_dict.sel_subject_pk = selected_pk;
    // reset selected student when subject is selected, in setting_dict and upload_dict
            if(selected_pk){
                setting_dict.sel_student_pk = null;
            }
// ---  upload new setting
            const upload_dict = {selected_pk: {sel_subject_pk: setting_dict.sel_subject_pk, sel_student_pk: null}};
            b_UploadSettings (upload_dict, urls.url_settings_upload);

        } else if (tblName === "student") {
            setting_dict.sel_student_pk = selected_pk;
    // reset selected subject when student is selected, in setting_dict and upload_dict
            if(selected_pk){
                setting_dict.sel_subject_pk = null;
            }
            // ---  upload new setting
            const upload_dict = {selected_pk: {sel_student_pk: setting_dict.sel_student_pk, sel_subject_pk: null}};
            b_UploadSettings (upload_dict, urls.url_settings_upload);
        }

        if (tblName === "school") {

        } else {
            //b_UploadSettings ({selected_pk: selected_pk_dict}, urls.url_settings_upload);
//console.log("selected_dict", selected_dict)
    // --- update header text
            const selected_name = (selected_dict) ?
                                    (tblName === "subject") ? selected_dict.name :
                                    (tblName === "student") ? selected_dict.fullname : null
                                  : null;
            UpdateHeaderText(selected_name);

    // ---  fill datatable
       //console.log("function MSSSS_Response");
            FillTblRows()

            //MSSSS_display_in_sbr()
    // --- update header text - comes after MSSSS_display_in_sbr
            //UpdateHeaderLeft();
        }
    }  // MSSSS_Response

//////////////////////////////////////////////
//========= MOD APPROVE STUDENT SUBJECTS ====================================
    function MASS_Open (open_mode ) {
        //console.log("===  MASS_Open  =====") ;
        //console.log("setting_dict", setting_dict) ;
        mod_MASS_dict = {}

        const is_approve = (open_mode === "approve");
        const is_submit = (open_mode === "submit");

        // b_get_statusindex_of_requsr returns index of auth user, returns 0 when user has none or multiple auth usergroups
        // gives err messages when multiple found.
        // status_index 1 = auth1, 2 = auth2
        const status_index = b_get_statusindex_of_requsr(loc, permit_dict);
        //console.log("status_index", status_index);

        if (permit_dict.permit_approve_subject || permit_dict.permit_submit_subject) {
            if(status_index){
                // modes are 'approve' 'submit_test' 'submit_submit'
                mod_MASS_dict = {is_approve: is_approve,
                            is_submit: is_submit,
                            status_index: status_index,
                            test_is_ok: false,
                            submit_is_ok: false,
                            step: -1,  // gets value 1 in MASS_Save
                            is_reset: false}

                const function_str = (permit_dict.usergroup_list && permit_dict.usergroup_list.includes("auth1")) ? loc.President :
                                (permit_dict.usergroup_list && permit_dict.usergroup_list.includes("auth2")) ? loc.Secretary :
                                (permit_dict.usergroup_list && permit_dict.usergroup_list.includes("auth3")) ? loc.Commissioner : "-";

                let header_txt = (is_approve) ? loc.Approve_subjects : loc.Submit_Ex1_form;
                header_txt += loc._by_ + permit_dict.requsr_name + " (" + function_str.toLowerCase() + ")"
                el_MASS_header.innerText = header_txt;
                el_MASS_subheader.innerText = (is_approve) ? loc.MASS_info.subheader_approve : loc.MASS_info.subheader_submit;

                add_or_remove_class(el_MASS_level.parentNode, cls_hide, !setting_dict.sel_dep_level_req)
                el_MASS_level.innerText = (setting_dict.sel_level_abbrev) ? setting_dict.sel_level_abbrev : null;

                el_MASS_sector.innerText = (setting_dict.sel_sector_abbrev) ? setting_dict.sel_sector_abbrev : null;

                let subject_text = null;
                if(setting_dict.sel_subject_pk){
                    const data_dict = b_get_datadict_by_integer_from_datarows(subject_rows, "id", setting_dict.sel_subject_pk)
                    subject_text =  (data_dict.name) ? data_dict.name : "---"
                } else {
                    subject_text = "<" + loc.All_subjects + ">";
                }
                el_MASS_subject.innerText = subject_text;

    // ---  show info container and delete button only in approve mode
                //console.log("...........is_submit", is_submit) ;
                add_or_remove_class(el_MASS_select_container, cls_hide, !is_approve)
                add_or_remove_class(el_MASS_btn_delete, cls_hide, is_submit)

    // ---  reset el_MASS_input_verifcode
                el_MASS_input_verifcode.value = null;

    // ---  show info and hide loader
                // PR2021-01-21 debug 'display_hide' not working when class 'image_container' is in same div
                add_or_remove_class(el_MASS_loader, cls_hide, true);

                MASS_Save ("save", true);  // true = is_test
                // this one is also in MASS_Save:
                // MASS_SetInfoboxesAndBtns();

                $("#id_mod_approve_studsubj").modal({backdrop: true});

            }  // if(status_index)
        }  // if (permit_dict.permit_approve_subject || permit_dict.permit_submit_subject)
    }  // MASS_Open


//=========  MASS_Save  ================
    function MASS_Save (save_mode) {
        console.log("===  MASS_Save  =====") ;
        console.log("save_mode", save_mode) ;

        console.log("mod_MASS_dict.step", mod_MASS_dict.step) ;
        // save_mode = 'save' or 'delete'
        // mod_MASS_dict.mode = 'approve' or 'submit'
        if (permit_dict.permit_approve_subject || permit_dict.permit_submit_subject) {

            mod_MASS_dict.is_reset = (save_mode === "delete");

            mod_MASS_dict.step += 1;

            //  upload_dict.modes are: 'approve_test', 'approve_submit', 'approve_reset', 'submit_test', 'submit_submit'
            let url_str = urls.url_studsubj_approve_multiple;
            const upload_dict = { table: "studsubj",
                                    now_arr: get_now_arr()  // only for timestamp on filename saved Ex-form
                                };

            if (mod_MASS_dict.is_approve){
                if (mod_MASS_dict.step === 0){
                    url_str = urls.url_studsubj_approve_multiple;
                    upload_dict.mode = "approve_test";
                } else if (mod_MASS_dict.step === 2){
                    upload_dict.mode = (mod_MASS_dict.is_reset) ? "approve_reset" : "approve_submit";
                }
            } else if (mod_MASS_dict.is_submit){
                if (mod_MASS_dict.step === 0){
                    url_str = urls.url_studsubj_approve_multiple;
                    upload_dict.mode = "submit_test";
                } else if (mod_MASS_dict.step === 2){
                    url_str = urls.url_studsubj_send_email_exform;
                } else if (mod_MASS_dict.step === 4){
                    upload_dict.mode = "submit_submit";
                    upload_dict.verificationcode = el_MASS_input_verifcode.value
                    upload_dict.verificationkey = mod_MASS_dict.verificationkey;
                }
            }

    // ---  upload changes
            console.log("upload_dict", upload_dict) ;
            console.log("url_str", url_str) ;
            UploadChanges(upload_dict, url_str);

            MASS_SetInfoboxesAndBtns() ;

        }  // if (permit_dict.permit_approve_subject || permit_dict.permit_submit_subject)
// hide modal
        //if (!mod_MASS_dict.is_test){
        //    $("#id_mod_approve_studsubj").modal("hide");
        //}
    };  // MASS_Save


//========= MASS_UpdateFromResponse ============= PR2021-07-25
    function MASS_UpdateFromResponse(response) {
        console.log( " ==== MASS_UpdateFromResponse ====");
        console.log( "response", response);
        console.log("mod_MASS_dict", mod_MASS_dict);
        mod_MASS_dict.step += 1;

        mod_MASS_dict.test_is_ok = !!response.test_is_ok;
        mod_MASS_dict.verificationkey = response.verificationkey;
        mod_MASS_dict.verification_is_ok = !!response.verification_is_ok;

        // this is not working correctly yet, turned off for now PR2021-09-10
        // if false verfcode entered: try again
        if (mod_MASS_dict.step === 5 && !mod_MASS_dict.verification_is_ok ){
            //mod_MASS_dict.step = 3;
        };

        const count_dict = (response.approve_count_dict) ? response.approve_count_dict : {};

        mod_MASS_dict.has_already_approved_by_auth = (!!count_dict.already_approved_by_auth)
        mod_MASS_dict.submit_is_ok = (!!count_dict.saved)
        //mod_MASS_dict.has_already_published = (!!msg_dict.already_published)
        //mod_MASS_dict.has_saved = !!msg_dict.saved;


        MASS_SetInfoboxesAndBtns (response);

        //if ("updated_studsubj_approve_rows" in response){
        //    RefreshDataRows("studsubj", response.updated_studsubj_approve_rows, studsubj_rows, true);
        //}
        if ( (mod_MASS_dict.is_approve && mod_MASS_dict.step === 3) || (mod_MASS_dict.is_submit && mod_MASS_dict.step === 5)){
                const datalist_request = { setting: {page: "page_studsubj"},
                                studentsubject_rows: {cur_dep_only: true},
                                published_rows: {get: true}
                                }
                DatalistDownload(datalist_request);
        };
    };  // MASS_UpdateFromResponse

//=========  MASS_SetInfoboxesAndBtns  ================ PR2021-02-08
     function MASS_SetInfoboxesAndBtns(response) {
        console.log("===  MASS_SetInfoboxesAndBtns  =====") ;

        const step = mod_MASS_dict.step;
        const is_response = (!!response);
        console.log("......................step", step) ;
        console.log("is_response", is_response) ;
        console.log("test_is_ok", mod_MASS_dict.test_is_ok) ;
        console.log("verification_is_ok", mod_MASS_dict.verification_is_ok) ;

        mod_MASS_dict.test_is_ok
        // step 0: opening modal
        // step 1 + response : return after check
        // step 1 without response: save clicked approve or request verifcode
        // step 2 + response : return after approve or after email sent
        // step 2 without response: submit Exform wit hverifcode
        // step 3 + response: return from submit Exform

        // TODO is_reset
        const is_reset = mod_MASS_dict.is_reset;


////////////////////////////////////////////////////////////////////////
// ---  select_container
////////////////////////////////////////////////////////////////////////
// ---  info_container, loader, info_verifcode and input_verifcode
        let msg_info_txt = null, show_loader = false;
        let show_info_request_verifcode = false, show_input_verifcode = false;
        let show_delete_btn = false;
        let disable_save_btn = false, save_btn_txt = null;

        if (response && response.approve_msg_html) {
            mod_MASS_dict.msg_html = response.approve_msg_html;
        };
        //console.log("msg_html", msg_html);

        if (step === 0) {
            // step 0: when form opens and request to check is sent to server
            // tekst: 'The subjects of the candidates are checked'
            msg_info_txt = loc.MASS_info.checking_studsubj;
            show_loader = true;
        } else {
            if(mod_MASS_dict.is_approve){
                // is approve
                if (step === 1) {
                // response with checked subjects
                // msg_info_txt is in response
                    show_delete_btn =mod_MASS_dict.has_already_approved_by_auth;
                    if (mod_MASS_dict.test_is_ok){
                        save_btn_txt = loc.Approve_subjects;
                    };
                } else if (step === 2) {
                    // clicked on 'Approve'
                    // tekst: 'AWP is approving the subjects of the candidates'
                    msg_info_txt = loc.MASS_info.approving_studsubj;
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
                    show_info_request_verifcode = mod_MASS_dict.test_is_ok;
                    if (mod_MASS_dict.test_is_ok){
                        save_btn_txt = loc.Apply_verificationcode;
                    };
                } else if (step === 2) {
                    // clicked on 'Apply_verificationcode'
                    // tekst: 'AWP is sending an email with the verification code'
                    // show textbox with 'You need a 6 digit verification code to submit the Ex form'
                    msg_info_txt = loc.MASS_info.requesting_verifcode;
                    show_loader = true;
                } else if (step === 3) {
                    // response 'email sent'
                    // msg_info_txt is in response
                    show_info_request_verifcode = mod_MASS_dict.test_is_ok;
                    show_input_verifcode = true;
                    disable_save_btn = !el_MASS_input_verifcode.value;
                    save_btn_txt = loc.Submit_Ex1_form;
                } else if (step === 4) {
                    // clicked on 'Submit Ex form'
                    // msg_info_txt is in response
                    show_loader = true;
                } else if (step === 5) {
                    // response 'Exform submittes'
                    // msg_info_txt is in response
                }
            }  // if(mod_MASS_dict.is_approve)
        }  // if (step === 0)

        console.log("msg_info_txt", msg_info_txt) ;
        if (msg_info_txt){
            mod_MASS_dict.msg_html = "<div class='p-2 border_bg_transparent'><p class='pb-2'>" +  msg_info_txt + " ...</p></div>";
        }
        //console.log("mod_MASS_dict.msg_html", mod_MASS_dict.msg_html) ;
        el_MASS_info_container.innerHTML = mod_MASS_dict.msg_html;
        add_or_remove_class(el_MASS_info_container, cls_hide, !mod_MASS_dict.msg_html)

        add_or_remove_class(el_MASS_loader, cls_hide, !show_loader)

        add_or_remove_class(el_MASS_info_request_verifcode, cls_hide, !show_info_request_verifcode);
        add_or_remove_class(el_MASS_input_verifcode.parentNode, cls_hide, !show_input_verifcode);
        if (show_input_verifcode){set_focus_on_el_with_timeout(el_MASS_input_verifcode, 150); };

// ---  show / hide delete btn
        add_or_remove_class(el_MASS_btn_delete, cls_hide, !show_delete_btn);
// - hide save button when there is no save_btn_txt
        add_or_remove_class(el_MASS_btn_save, cls_hide, !save_btn_txt)
// ---  disable save button till test is finished or input_verifcode has value
        el_MASS_btn_save.disabled = disable_save_btn;;
// ---  set innerText of save_btn
        el_MASS_btn_save.innerText = save_btn_txt;

// ---  set innerText of cancel_btn
        el_MASS_btn_cancel.innerText = (step === 0 || !!save_btn_txt) ? loc.Cancel : loc.Close;

     } //  MASS_SetInfoboxesAndBtns

//=========  MASS_InputVerifcode  ================ PR2021-07-30
     function MASS_InputVerifcode(el_input, event_key) {
        //console.log("===  MASS_InputVerifcode  =====") ;

        if(event_key && event_key === "Enter"){

        }
        // enable save btn when el_input has value
        const disable_save_btn = !el_input.value;
        //console.log("disable_save_btn", disable_save_btn) ;
        el_MASS_btn_save.disabled = disable_save_btn;

        if(!disable_save_btn && event_key && event_key === "Enter"){
            MASS_Save("save")
        }
     };  // MASS_InputVerifcode

/////////////////////////////////////////////

//========= DownloadGradeStatusAndIcons ============= PR2021-07-24
    function DownloadValidationStatusNotes() {
        //console.log( " ==== DownloadGradeStatusAndIcons ====");
        const url_str = urls.url_studsubj_validate_all;
        const upload_dict = {studsubj_validate: {get: true}};
        UploadChanges(upload_dict, url_str);
     } // DownloadGradeStatusAndIcons

//========= DownloadMultipleOccurrences ============= PR2021-09-05
    function DownloadMultipleOccurrences() {
        //console.log( " ==== DownloadMultipleOccurrences ====");
        const url_str = urls.url_studsubj_multiple_occurrences;
        const upload_dict = {studsubj_multiple_occurrences: {get: true}};
        UploadChanges(upload_dict, url_str);
     } // DownloadMultipleOccurrences

//========= ResponseValidationAll ============= PR2021-07-24 PR2021-08-17
    function ResponseValidationAll(validate_studsubj_list, oneonly_student_pk, oneonly_subj_error) {
        //console.log( " ==== ResponseValidationAll ====");
        //console.log( "oneonly_student_pk", oneonly_student_pk);
        //console.log( "oneonly_subj_error", oneonly_subj_error);

// ---  loop through validate_studsubj_list and add key 'subj_error'
        for (let i = 0, row; row = studsubj_rows[i]; i++) {
            if(oneonly_student_pk){
                if(row.stud_id === oneonly_student_pk){
                    row.subj_error = oneonly_subj_error;
                };
            } else {
                row.subj_error = (validate_studsubj_list && row.stud_id && validate_studsubj_list.includes(row.stud_id))
            }
        }

       // update first column "subj_error"
       if (oneonly_student_pk) {
            for (let i = 0, tblRow; tblRow = tblBody_datatable.rows[i]; i++) {
                const row_stud_pk = get_attr_from_el_int(tblRow, "data-stud_pk");
                if (row_stud_pk === oneonly_student_pk){
                    const el_div = tblRow.cells[0].children[0];
                    if (el_div){
                        const row_studsubj_pk = get_attr_from_el_int(tblRow, "data-studsubj_pk");
                        const map_dict = {subj_error: oneonly_subj_error, studsubj_id: row_studsubj_pk};
                        UpdateField(el_div, map_dict);
                    };
                };
            };
       } else {
            FillTblRows();
            Filter_TableRows();
       };
    };  // ResponseValidationAll

//========= get_datadict_from_tblRow ============= PR2021-07-25 PR2021-08-08
    function get_datadict_from_tblRow(tblRow) {
        //console.log( " ==== get_datadict_by_integer_from_tblRow ====");
// get student_pk and studsubj_pk from tr_clicked.id
        let student_pk = null, studsubj_pk = null;
        if (tblRow){
            const arr = tblRow.id.split("_");
            student_pk = (arr[1] && Number(arr[1])) ? Number(arr[1]) : 0;
            studsubj_pk = (arr[2] && Number(arr[2])) ? Number(arr[2]) : 0;
        };

        const [index, found_dict] = get_datadict_by_studpk_studsubjpk(student_pk, studsubj_pk);
        const data_dict = (!isEmpty(found_dict)) ? found_dict : null;

        return data_dict;
    }  //  get_datadict_from_tblRow


//========= get_datadict_by_studpk_studsubjpk ============= PR2021-07-25 PR2021-08-08
    function get_datadict_by_studpk_studsubjpk(student_pk, studsubj_pk) {
        //console.log( " ==== get_datadict_by_studpk_studsubjpk ====");

        const data_rows = (selected_btn === "btn_published") ? published_rows : studsubj_rows;
        const lookup_1_field = (selected_btn === "btn_published") ? null : "stud_id";
        const lookup_2_field = (selected_btn === "btn_published") ? "id" : "studsubj_id";
        const search_1_int = student_pk;
        const search_2_int = studsubj_pk;
        const [middle_index, found_dict, compare] = b_recursive_integer_lookup(data_rows, lookup_1_field, search_1_int, lookup_2_field, search_2_int);
        const data_dict = found_dict;
        const row_index = middle_index;

        return [row_index, data_dict];
    };  // get_datadict_by_studpk_studsubjpk

////////////////////
//========= get_tblName_from_selectedBtn  ======== // PR2021-07-28
    function get_tblName_from_selectedBtn() {
        const tblName = (selected_btn === "btn_published") ? "published" : "studsubj";
        return tblName;
    }

//========= get_datamap_from_tblName  ========  // PR2021-07-28 PR2021-09-05
    function get_datarows_from_tblName(tblName) {
        const data_map = (tblName === "published") ? published_rows : studsubj_rows;
        return data_map;
    }

})  // document.addEventListener('DOMContentLoaded', function()

