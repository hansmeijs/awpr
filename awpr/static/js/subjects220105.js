// PR2020-09-29 added

// PR2021-07-23  declare variables outside function to make them global variables

let selected_btn = "btn_subject";

let setting_dict = {};
let permit_dict = {};
let loc = {};  // locale_dict
let urls = {};


const field_settings = {};

document.addEventListener('DOMContentLoaded', function() {
    "use strict";

    let el_loader = document.getElementById("id_loader");

// ---  get permits
    // permit dict gets value after downloading permit_list PR2021-03-27
    //  if user has no permit to view this page ( {% if no_access %} ): el_loader does not exist PR2020-10-02
    const may_view_page = (!!el_loader)

    const cls_hide = "display_hide";
    const cls_hover = "tr_hover";
    const cls_visible_hide = "visibility_hide";
    const cls_selected = "tsa_tr_selected";

    const selected = {
        scheme_dict: null,
        subject_dict:  null,
        schemeitem_dict: null,
        subjecttype_dict: null,
        depbase_pk: null,
        scheme_pk: null,
        package_pk: null
    };

    let mod_dict = {};
    let mod_MSUBJ_dict = {};
    let mod_MSJTP_dict = {};
    let mod_MSJTBASE_dict = {};

    let mod_MSI_dict = {
        subject_dict: {},
        schemeitem_dict: {},
        subjecttype_dict: {}
    };

    let subjecttype_rows = [];
    let subjecttypebase_rows = [];
    let subject_rows = [];
    let schemeitem_rows = [];
    let scheme_rows = [];
    let scheme_map = new Map();

    let examyear_map = new Map();
    let department_map = new Map();
    let level_map = new Map();
    let sector_map = new Map();
    let package_map = new Map();
    let packageitem_map = new Map();

    let filter_dict = {};

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    urls.url_usersetting_upload = get_attr_from_el(el_data, "data-url_usersetting_upload");
    urls.url_subject_upload = get_attr_from_el(el_data, "data-subject_upload_url");
    urls.url_subject_import = get_attr_from_el(el_data, "data-subject_import_url");
    urls.url_subjecttype_upload = get_attr_from_el(el_data, "data-subjecttype_upload_url");
    urls.url_subjecttypebase_upload = get_attr_from_el(el_data, "data-subjecttypebase_upload_url");
    urls.url_scheme_upload = get_attr_from_el(el_data, "data-scheme_upload_url");
    urls.url_schemeitem_upload = get_attr_from_el(el_data, "data-schemeitem_upload_url");
    urls.url_download_scheme_xlsx = get_attr_from_el(el_data, "data-url_download_scheme_xlsx");

// columns_hidden and columns_tobe_hidden are also used in t_MCOL_Open and t_MCOL_Save
    columns_tobe_hidden.btn_subject = {
        fields: ["name", "depbases", "sequence", "addedbyschool"],
        captions: ["Name", "Departments", "Sequence", "Added_by_school"]};
    columns_tobe_hidden.btn_scheme = {
        fields: ["depbase_code", "lvl_abbrev", "sct_abbrev", "min_subjects", "max_subjects",
                "min_mvt", "max_mvt", "min_wisk", "max_wisk", "min_combi", "max_combi", "max_reex",
                "rule_avg_pece_sufficient", "rule_avg_pece_notatevlex", "rule_core_sufficient", "rule_core_notatevlex",
        ],
        captions: ["Department", "Leerweg",  "SectorProfiel_twolines", "Minimum_subjects",  "Maximum_subjects",
                    "Minimum_MVT_subjects", "Maximum_MVT_subjects", "Minimum_Wisk_subjects", "Maximum_Wisk_subjects",
                    "Minimum_combi_subjects", "Maximum_combi_subjects", "Maximum_reex",
                    "Average_CE_grade_rule", "Not_at_evening_lex_school", "Core_subject_rule", "Not_at_evening_lex_school",
                    ]};
    columns_tobe_hidden.btn_schemeitem = {
        fields: ["subj_name", "sjtp_abbrev", "ete_exam", "otherlang",
                "gradetype", "weight_se", "weight_ce", "multiplier", "is_mandatory", "is_mand_subj", "is_combi", "is_core_subject", "is_mvt", "is_wisk",
                "rule_grade_sufficient", "rule_gradesuff_notatevlex",
                "extra_count_allowed",  "extra_nocount_allowed",
                 "has_practexam", "sr_allowed",
                "max_reex", "no_thirdperiod",  "no_exemption_ce"],
        captions: ["Subject", "Character", "ETE_exam", "Other_languages",
                "Grade_type", "SE_weighing",  "CE_weighing", "Counts_double", "Mandatory", "Mandatory_if_subject", "Combination_subject", "Is_core_subject", "Is_MVT_subject", "Is_wiskunde_subject",
                "Subject_must_be_sufficient", "Not_at_evening_lex_school",
                "Extra_count_allowed", "Extra_nocount_allowed",
                "Has_practical_exam", "Herkansing_SE_allowed",
                "Maximum_reex", "No_third_period", "Exemption_without_CE_allowed"]};

    columns_tobe_hidden.btn_subjecttype = {
        fields: ["name", "min_subjects",  "max_subjects", "min_extra_nocount" , "max_extra_nocount",
                "min_extra_counts", "max_extra_counts", "has_pws"],
        captions: ["Character_name", "Minimum_subjects",  "Maximum_subjects", "Minimum_extra_nocount",  "Maximum_extra_nocount",
                    "Minimum_extra_counts",  "Maximum_extra_counts", "Has_assignment"]};
    columns_tobe_hidden.btn_subjecttypebase = {
        fields: [ "name", "abbrev", "sequence"],
        captions: [ "Name", "Abbreviation",  "Sequence"]};

// --- get field_settings
    field_settings.btn_subject = {field_caption: ["", "Abbreviation", "Name", "Departments", "Sequence", "Added_by_school"],
                    field_names: ["select", "code", "name", "depbases", "sequence",  "addedbyschool"],
                    field_tags: ["div", "div", "div", "div", "div", "div"],
                    filter_tags: ["select", "text", "text",  "text", "number", "toggle"],
                    field_width:  ["020", "120", "300", "150", "120",  "120", "120"],
                    field_align: ["c", "l", "l", "l",  "r", "c"]};
    field_settings.btn_scheme = {
        field_caption: ["", "Subject_scheme_name", "Department", "Leerweg",  "SectorProfiel_twolines",
                        "Minimum_subjects", "Maximum_subjects", "Minimum_MVT_subjects", "Maximum_MVT_subjects",
                        "Minimum_Wisk_subjects", "Maximum_Wisk_subjects", "Minimum_combi_subjects", "Maximum_combi_subjects", "Maximum_reex",
                        "Average_CE_grade_rule", "Not_at_evening_lex_school", "Core_subject_rule", "Not_at_evening_lex_school",
                        ],
        field_names: ["select", "name", "depbase_code", "lvl_abbrev", "sct_abbrev",
                       "min_subjects", "max_subjects", "min_mvt", "max_mvt",
                       "min_wisk", "max_wisk", "min_combi", "max_combi", "max_reex",
                       "rule_avg_pece_sufficient", "rule_avg_pece_notatevlex", "rule_core_sufficient", "rule_core_notatevlex",
                     ],
        field_tags: ["div", "input", "div", "div", "div",
                    "input", "input", "input", "input",
                    "input","input", "input", "input","input",
                    "div", "div", "div", "div"
                    ],
        filter_tags: ["select", "text", "text", "text", "text",
                    "number", "number", "number", "number",
                    "number", "number", "number", "number","number",
                    "toggle", "toggle", "toggle", "toggle"
        ],
        field_width:  ["020", "280", "120", "120",  "120",
                    "150",  "150",  "150",  "150",
                    "150",  "150",  "150",  "150", "150",
                    "090", "120", "090", "120"
        ],
        field_align: ["c", "l", "l", "l",  "l",
                        "c", "c", "c", "c",
                        "c", "c", "c", "c", "c",
                        "c", "c", "c", "c"
        ]};
    field_settings.btn_schemeitem = { field_caption: ["", "Subject_scheme", "Abbreviation", "Subject", "Character", "ETE_exam", "Other_languages",
                            "Grade_type", "SE_weighing", "CE_weighing", "Counts_double",
                            "Mandatory", "Mandatory_if_subject", "Combination_subject",
                            "Is_core_subject", "Is_MVT_subject", "Is_wiskunde_subject",
                            "Extra_count_allowed",  "Extra_nocount_allowed",
                            "Has_practical_exam", "Herkansing_SE_allowed",
                            "Subject_must_be_sufficient", "Not_at_evening_lex_school",
                            ],
                    field_names: ["select", "scheme_name", "subj_code", "subj_name", "sjtp_abbrev", "ete_exam", "otherlang",
                            "gradetype", "weight_se", "weight_ce", "multiplier",
                            "is_mandatory", "is_mand_subj", "is_combi",
                            "is_core_subject", "is_mvt", "is_wisk",
                            "extra_count_allowed",  "extra_nocount_allowed",
                            "has_practexam", "sr_allowed",
                            "rule_grade_sufficient", "rule_gradesuff_notatevlex",
                            ],
                    field_tags: ["div", "div", "div", "div", "div", "div", "div",
                                "div", "div", "div", "div",
                                "div", "div", "div",
                                "div", "div", "div",
                                "div", "div",
                                "div", "div",
                                "div", "div",
                                 ],
                    filter_tags: ["select", "text", "text", "text",  "text", "toggle", "text",
                                "toggle", "toggle", "toggle", "toggle",
                                "toggle", "toggle", "toggle",
                                "toggle", "toggle", "toggle",
                                "toggle", "toggle",
                                "toggle", "toggle",
                                "toggle",  "toggle",
                                ],
                    field_width:  ["020", "180", "090", "300", "120", "090", "150",
                                    "090", "090", "090", "090",
                                    "090", "090", "090",
                                    "090", "090", "090",
                                    "090", "090",
                                    "090", "090",
                                    "090", "100",
                                     ],
                    field_align: ["c", "l", "l","l", "l", "c", "l",
                                    "c", "c", "c", "c",
                                    "c", "c", "c",
                                    "c", "c", "c",
                                    "c", "c",
                                    "c", "c",
                                    "c", "c",
                                    ]
                    };
    field_settings.btn_subjecttype = {field_caption: ["", "Subject_scheme", "Base_character", "Character_name",
                    "Minimum_subjects", "Maximum_subjects",
                    "Minimum_extra_nocount", "Maximum_extra_nocount",
                    "Minimum_extra_counts", "Maximum_extra_counts", "Has_assignment"
                    ],
                    field_names: ["select", "scheme_name", "sjtpbase_name", "name",
                                "min_subjects",  "max_subjects", "min_extra_nocount" , "max_extra_nocount",
                                "min_extra_counts", "max_extra_counts", "has_pws"
                    ],
                    field_tags: ["div", "div", "div", "input",
                                "input", "input",  "input", "input",
                                "input", "input", "div"],
                    filter_tags: ["select", "text", "text", "text",
                                "number", "number", "number", "number",
                                "number", "number", "toggle"],
                    field_width:  ["020", "180", "280", "240",
                                "100", "100", "100", "100",
                                "100", "100", "100"],
                    field_align: ["c", "l", "l", "l",
                                    "c", "c", "c", "c",
                                    "c", "c", "c"]};

    field_settings.btn_subjecttypebase = {field_caption: ["", "Code", "Name", "Abbreviation",  "Sequence"],
                    field_names: ["select", "code", "name", "abbrev", "sequence"],
                    field_tags: ["div", "input", "input", "input", "input"],
                    filter_tags: ["select", "text", "text", "text", "number"],
                    field_width:  ["020", "120", "280", "120", "120"],
                    field_align: ["c", "l", "l", "l", "l", "c"]};

    field_settings.btn_level = {  field_caption: ["", "Abbreviation", "Name", "Departments", "Sequence"],
                    field_names: ["select", "abbrev", "name", "depbases", "sequence"],
                    field_tags: ["div", "div", "div", "div",  "div"],
                    filter_tags: ["select", "text", "text",  "text", "number"],
                    field_width:  ["020", "120", "240", "240",  "120"],
                    field_align: ["c", "l", "l", "l",  "r", "c"]}

    field_settings.btn_sector = {  field_caption: ["", "Abbreviation", "Name", "Departments",  "Sequence"],
                    field_names: ["select", "abbrev", "name", "depbases", "sequence"],
                    field_tags: ["div", "div", "div", "div",  "div"],
                    filter_tags: ["select", "text", "text",  "text", "number"],
                    field_width:  ["020", "120", "240", "240",  "120"],
                    field_align: ["c", "l", "l", "l",  "r", "c"]};

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
        if (el_hdrbar_examyear){
            el_hdrbar_examyear.addEventListener("click", function() {
                t_MSED_Open(loc, "examyear", examyear_map, setting_dict, permit_dict, MSED_Response)}, false );
        }

// ---  SIDE BAR ------------------------------------
        const el_SBR_select_department = document.getElementById("id_SBR_select_department");
        if (el_SBR_select_department){
            el_SBR_select_department.addEventListener("change", function() {HandleSBRselect(el_SBR_select_department)}, false)};
        const el_SBR_select_level = document.getElementById("id_SBR_select_level");
        if(el_SBR_select_level){
            el_SBR_select_level.addEventListener("change", function() {HandleSBRselect(el_SBR_select_level)}, false)};
        const el_SBR_select_sector_label = document.getElementById("id_SBR_select_sector_label");
        const el_SBR_select_sector = document.getElementById("id_SBR_select_sector");
        if(el_SBR_select_sector){
            el_SBR_select_sector.addEventListener("change", function() {HandleSBRselect(el_SBR_select_sector)}, false)};
        const el_SBR_select_subject = document.getElementById("id_SBR_select_subject");

        const el_SBR_select_showall = document.getElementById("id_SBR_select_showall");
        if(el_SBR_select_showall){
            el_SBR_select_showall.addEventListener("click", function() {SBR_show_all()}, false);
            add_hover(el_SBR_select_showall);
        };
        const el_SBR_item_count = document.getElementById("id_SBR_item_count");

// ---  MODAL SUBJECT TYPE
        const el_MSJT_header = document.getElementById("id_MSJT_header")

        const el_MSJTP_department = document.getElementById("id_MSJT_department");
        if(el_MSJTP_department){el_MSJTP_department.addEventListener("change", function() {MSJT_SelectChange(el_MSJTP_department)}, false )};
        const el_MSJTP_level = document.getElementById("id_MSJT_level");
        if(el_MSJTP_level){el_MSJTP_level.addEventListener("change", function() {MSJT_SelectChange(el_MSJTP_level)}, false )};
        const el_MSJTP_sector = document.getElementById("id_MSJT_sector");
        if(el_MSJTP_sector){el_MSJTP_sector.addEventListener("change", function() {MSJT_SelectChange(el_MSJTP_sector)}, false )};

        const el_MSJT_tblBody_sjtpbase = document.getElementById("id_MSJT_tblBody_sjtpbase");
        const el_MSJT_tblBody_subjecttype = document.getElementById("id_MSJT_tblBody_subjecttype");

        const el_MSJT_btn_delete = document.getElementById("id_MSJT_btn_delete");
        if(el_MSJT_btn_delete){el_MSJT_btn_delete.addEventListener("click", function() {ModConfirmOpen("subjecttype", "delete")}, false )}
        const el_MSJT_btn_log = document.getElementById("id_MSJT_btn_log");
        const el_MSJT_btn_save = document.getElementById("id_MSJT_btn_save");
        if(el_MSJT_btn_save){ el_MSJT_btn_save.addEventListener("click", function() {MSJT_Save()}, false )}

// ---  MODAL SUBJECT TYPE BASE
        const el_MSJTBASE_header = document.getElementById("id_MSJTBASE_header")

        const el_MSJTBASE_btn_delete = document.getElementById("id_MSJTBASE_btn_delete");
        if(el_MSJTBASE_btn_delete){el_MSJTBASE_btn_delete.addEventListener("click", function() {ModConfirmOpen("subjecttypebase", "delete")}, false )}
        const el_MSJTBASE_btn_log = document.getElementById("id_MSJTBASE_btn_log");
        const el_MSJTBASE_btn_save = document.getElementById("id_MSJTBASE_btn_save");
        if(el_MSJTBASE_btn_save){ el_MSJTBASE_btn_save.addEventListener("click", function() {MSJTBASE_Save()}, false )}

// ---  MODAL SUBJECT
        const el_MSUBJ_loader = document.getElementById("id_MSUBJ_loader");
        const el_MSUBJ_div_form_controls = document.getElementById("id_MSUBJ_form_controls")
        if(el_MSUBJ_div_form_controls){
            const input_elements = el_MSUBJ_div_form_controls.querySelectorAll(".awp_input_text")
            for (let i = 0, el; el=input_elements[i]; i++) {
                const event_str = (el.tagName === "SELECT") ? "change" : "keyup";
                el.addEventListener(event_str, function() {MSUBJ_InputKeyup(el)}, false );
            }
        }
        const el_MSUBJ_code = document.getElementById("id_MSUBJ_code");
        const el_MSUBJ_name = document.getElementById("id_MSUBJ_name");
        const el_MSUBJ_sequence = document.getElementById("id_MSUBJ_sequence");
        const el_MSUBJ_etenorm = document.getElementById("id_MSUBJ_etenorm");
        if(el_MSUBJ_etenorm){el_MSUBJ_etenorm.addEventListener("click", function() {MSUBJ_Toggle(el_MSUBJ_etenorm)}, false )}

        const el_MSUBJ_message_container = document.getElementById("id_MSUBJ_message_container")
        const el_MSUBJ_btn_delete = document.getElementById("id_MSUBJ_btn_delete");
        if(el_MSUBJ_btn_delete){el_MSUBJ_btn_delete.addEventListener("click", function() {ModConfirmOpen("subject", "delete")}, false )}
        const el_MSUBJ_btn_log = document.getElementById("id_MSUBJ_btn_log");
        const el_MSUBJ_btn_save = document.getElementById("id_MSUBJ_btn_save");
        if(el_MSUBJ_btn_save){ el_MSUBJ_btn_save.addEventListener("click", function() {MSUBJ_Save("save")}, false )}

// ---  MODAL SCHEMEITEM
        const el_MSI_header = document.getElementById("id_MSI_header")

        const el_MSI_deplvlsct_container = document.getElementById("id_MSI_deplvlsct_container");
        const el_MSI_department = document.getElementById("id_MSI_department");
        const el_MSI_level = document.getElementById("id_MSI_level");
        const el_MSI_sector = document.getElementById("id_MSI_sector");
        if(el_MSI_department){el_MSI_department.addEventListener("change", function() {MSI_InputChange(el_MSI_department)}, false )}
        if(el_MSI_level){el_MSI_level.addEventListener("change", function() {MSI_InputChange(el_MSI_level)}, false )}
        if(el_MSI_sector){el_MSI_sector.addEventListener("change", function() {MSI_InputChange(el_MSI_sector)}, false )}

        const el_MSI_btn_save = document.getElementById("id_MSI_btn_save")
            el_MSI_btn_save.addEventListener("click", function() {MSI_Save()}, false);

        const el_tblBody_subjects = document.getElementById("id_MSI_tblBody_subjects");
        const el_tblBody_schemeitems = document.getElementById("id_MSI_tblBody_schemeitems");


// ---  MODAL OTHER LANGUAGE ------------------------------------
        const el_MOL_header = document.getElementById("id_MOL_header")
        const el_MOL_otherlang = document.getElementById("id_MOL_otherlang")
        if(el_MOL_otherlang){el_MOL_otherlang.addEventListener("change", function() {MOL_InputChange(el_MOL_otherlang)}, false )}
        const el_MOL_btn_save = document.getElementById("id_MOL_btn_save")
        if(el_MOL_otherlang){el_MOL_btn_save.addEventListener("click", function() {MOL_Save()}, false)};

// ---  MODAL SELECT COLUMNS ------------------------------------
        const el_MCOL_btn_save = document.getElementById("id_MCOL_btn_save")
        if(el_MCOL_btn_save){
            el_MCOL_btn_save.addEventListener("click", function() {
                t_MCOL_Save(urls.url_usersetting_upload, HandleBtnSelect)}, false )
        };;

// ---  MOD CONFIRM ------------------------------------
        let el_confirm_header = document.getElementById("id_modconfirm_header");
        let el_confirm_loader = document.getElementById("id_modconfirm_loader");
        let el_confirm_msg_container = document.getElementById("id_modconfirm_msg_container")

        let el_confirm_btn_cancel = document.getElementById("id_modconfirm_btn_cancel");
        let el_confirm_btn_save = document.getElementById("id_modconfirm_btn_save");
        if(el_confirm_btn_save){ el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()}) };

// ---  set selected menu button active
    SetMenubuttonActive(document.getElementById("id_hdr_users"));
    if(may_view_page){
        // period also returns emplhour_list
        const datalist_request = {
                setting: {page: "page_subject"},
                locale: {page: ["page_subject"]},

                scheme_rows: {cur_dep_only: false},
                subject_rows: {get: true},
                schemeitem_rows: {get: true},
                subjecttype_rows: {cur_dep_only: false},
                examyear_rows: {get: true},
                school_rows: {get: true},
                department_rows: {get: true},
                level_rows: {cur_dep_only: false},
                sector_rows: {cur_dep_only: false}
            };

        DatalistDownload(datalist_request);
    }
//  #############################################################################################################

//========= DatalistDownload  ===================== PR2020-07-31
    function DatalistDownload(datalist_request, keep_loader_hidden) {
        console.log( "===== DatalistDownload ===== ")
        console.log("request: ", datalist_request)

// ---  Get today's date and time - for elapsed time
        let startime = new Date().getTime();

// ---  show loader  // keep_loader_hidden not in use yet
        if(!keep_loader_hidden){el_loader.classList.remove(cls_visible_hide)}

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

                let must_create_submenu = false, must_update_headerbar = false;

                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                    must_create_submenu = true;
                };

                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict
                    selected_btn = (setting_dict.sel_btn)
                    selected.scheme_pk = (setting_dict.sel_scheme_pk) ? setting_dict.sel_scheme_pk : null;
                    //console.log("selected.scheme_pk", selected.scheme_pk)

// ---  fill cols_hidden
                    if("cols_hidden" in setting_dict){
                        //  setting_dict.cols_hidden was dict with key 'all' or se_btn, changed to array PR2021-12-14
                        //  skip when setting_dict.cols_hidden is not an array,
                        // will be changed into an array when saving with t_MCOL_Save
                        if (Array.isArray(setting_dict.cols_hidden)) {
                             b_copy_array_noduplicates(setting_dict.cols_hidden, mod_MCOL_dict.cols_hidden);
                        };
                    };
                    //console.log("columns_hidden", columns_hidden)
                    must_update_headerbar = true;
                }

                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    // get_permits must come before CreateSubmenu and FiLLTbl
                    b_get_permits_from_permitlist(permit_dict);
                    must_update_headerbar = true;
                }

                if(must_create_submenu){CreateSubmenu()};

                if(must_update_headerbar){
                    b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear);
                };
                // TODO remove response.msg_list
                if("msg_list" in response){
                    b_ShowModMessages(response.msg_list);
                }
                if ("messages" in response) {
                    b_ShowModMessages(response.messages);
                }
                if ("subjecttype_rows" in response) {subjecttype_rows = response.subjecttype_rows};
                if ("subjecttypebase_rows" in response) {subjecttypebase_rows = response.subjecttypebase_rows};
                if ("subject_rows" in response) {subject_rows = response.subject_rows};
                if ("schemeitem_rows" in response) {schemeitem_rows = response.schemeitem_rows};

                if ("scheme_rows" in response) {
                    scheme_rows = response.scheme_rows
                    b_fill_datamap(scheme_map, scheme_rows)
                };
                if ("examyear_rows" in response) {
                    b_fill_datamap(examyear_map, response.examyear_rows)
                };
                if ("department_rows" in response) {
                    b_fill_datamap(department_map, response.department_rows);
                    // PR2021-08-28 debug: dont use setting_dict to get saved depbasepk, clashes with allowed depbases
                    SBR_FillSelectOptions("department");
                };
                if ("level_rows" in response) {
                    b_fill_datamap(level_map, response.level_rows);
                    SBR_FillSelectOptions("level");
                };
                if ("sector_rows" in response) {
                    b_fill_datamap(sector_map, response.sector_rows);
                    SBR_FillSelectOptions("sector");
                };

                HandleBtnSelect(selected_btn, true)  // true = skip_upload
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
        console.log("===  CreateSubmenu == ");
        let el_submenu = document.getElementById("id_submenu")

        console.log("requsr_role_system", permit_dict.requsr_role_system);
        console.log("permit_crud", permit_dict.permit_crud);
        if (permit_dict.permit_crud){
                AddSubmenuButton(el_submenu, loc.Add_subject, function() {MSUBJ_Open()}, ["tab_show", "tab_btn_subject"]);
                AddSubmenuButton(el_submenu, loc.Delete_subject, function() {ModConfirmOpen("subject", "delete")}, ["tab_show", "tab_btn_subject"]);
                //AddSubmenuButton(el_submenu, loc.Copy_from_previous_year, function() {MSUBJ_Open()}, ["tab_show", "tab_btn_subject"]);
                //AddSubmenuButton(el_submenu, loc.Upload_subjects, null, ["tab_show", "tab_btn_subject"], "id_submenu_subjectimport", urls.url_subject_import);

                AddSubmenuButton(el_submenu, loc.Change_subjects_of_subject_scheme, function() {MSI_Open()}, ["tab_show", "tab_btn_scheme", "tab_btn_schemeitem"]);
                //AddSubmenuButton(el_submenu, loc.Copy_subject_scheme, function() {MSUBJ_Open()}, ["tab_show", "tab_btn_schemeitem"]);

                AddSubmenuButton(el_submenu, loc.Change_characters_of_subject_scheme, function() {MSJTP_Open()}, ["tab_show", "tab_btn_subjecttype"]);
                AddSubmenuButton(el_submenu, loc.Delete_character, function() {ModConfirmOpen("subjecttype", "delete")}, ["tab_show", "tab_btn_subjecttype"]);

                AddSubmenuButton(el_submenu, loc.Add_subjecttypebase, function() {MSJTBASE_Open()}, ["tab_show", "tab_btn_subjecttypebase"]);
                AddSubmenuButton(el_submenu, loc.Delete_characterbase, function() {ModConfirmOpen("subjecttypebase", "delete")}, ["tab_show", "tab_btn_subjecttypebase"]);

        }
        AddSubmenuButton(el_submenu, loc.Download_subject_scheme, null, ["tab_show", "tab_btn_scheme", "tab_btn_schemeitem", "tab_btn_subjecttype" ], "id_submenu_download_schemexlsx", urls.url_download_scheme_xlsx, false);  // true = download


        AddSubmenuButton(el_submenu, loc.Hide_columns, function() {t_MCOL_Open("page_subject")}, [], "id_submenu_columns")

        el_submenu.classList.remove(cls_hide);
    }; //function CreateSubmenu

//###########################################################################
//=========  HandleBtnSelect  ================ PR2020-09-19
    function HandleBtnSelect(data_btn, skip_upload) {
        //console.log( "===== HandleBtnSelect ========= ", data_btn);

        //  PR2021-09-07 debug: gave error because old btn name was still in saved setting
        if (data_btn && ["btn_subject", "btn_scheme", "btn_schemeitem", "btn_subjecttype", "btn_subjecttypebase", "btn_package"].includes(data_btn)) {
            selected_btn = data_btn;
        } else {
            selected_btn = "btn_subject";
        };

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_subject: {sel_btn: selected_btn}};
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);
        };

// ---  highlight selected button
        highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  show only the elements that are used in this tab
        b_show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

// ---  reset filter when tab = btn_subjecttypebase
        if (selected_btn === "btn_subjecttypebase"){
            SBR_show_all()
            // FillTblRows is included in SBR_show_all
        } else {

// ---  fill datatable
            FillTblRows();
        }
// --- update header text
        UpdateHeaderText();
    }  // HandleBtnSelect

//=========  HandleTblRowClicked  ================ PR2020-08-03  PR2021-06-22
    function HandleTblRowClicked(tr_clicked) {
        //console.log("=== HandleTblRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);
        //console.log( "tr_clicked.id: ", tr_clicked.id, typeof tr_clicked.id);
        //console.log( "selected_btn: ", selected_btn);

        selected.package_pk = null;

        selected.subject_dict = null;
        selected.schemeitem_dict = null;
        selected.subjecttype_dict = null;
        selected.copyto_examyear_dict = null;  // for Copy_subject_schemes PR2021-09-24

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        DeselectHighlightedRows(tr_clicked, cls_selected);
        tr_clicked.classList.add(cls_selected)

// ---  update selected_pk
        const data_dict = get_recursive_integer_lookup(tr_clicked);
        console.log( "data_dict: ", data_dict);

        if(selected_btn === "btn_subject"){
            selected.subject_dict = data_dict;
        } else if(selected_btn === "btn_scheme"){
            selected.scheme_dict = data_dict;
        } else if(selected_btn === "btn_schemeitem"){
            selected.schemeitem_dict = data_dict;
        } else if(selected_btn === "btn_subjecttype"){
            selected.subjecttype_dict = data_dict;
        } else if(selected_btn === "btn_subjecttypebase"){
            selected.subjecttypebase_dict = data_dict;
        };
    }  // HandleTblRowClicked

//========= UpdateHeaderText  ================== PR2020-07-31
    function UpdateHeaderText(){
        //console.log(" --- UpdateHeaderText ---" )
        let header_text = null;
        if(selected_btn === "subjects"){
            header_text = loc.Subjects;
        } else {
            header_text = null;
        }
        document.getElementById("id_header_left").innerText = header_text;
    }   //  UpdateHeaderText

//###########################################################################
// +++++++++++++++++ FILL TABLE ROWS ++++++++++++++++++++++++++++++++++++++++
//========= FillTblRows  ===================== PR2021-06-21
    function FillTblRows() {
        //console.log( "===== FillTblRows  === ");

        const tblName = get_tblName_from_selectedBtn();
        const field_setting = field_settings[selected_btn];

        const data_rows = get_datarows_from_selBtn();

    //console.log( "selected_btn", selected_btn);
    //console.log( "tblName", tblName);
    //console.log( "field_setting", field_setting);
    //console.log( "data_rows", data_rows);
    //console.log( "selected.scheme_pk", selected.scheme_pk);

// ---  get list of hidden columns
        // copy col_hidden from mod_MCOL_dict.cols_hidden
        const col_hidden = [];
        b_copy_array_noduplicates(mod_MCOL_dict.cols_hidden, col_hidden)

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

// --- create table header
        CreateTblHeader(field_setting, col_hidden);

// --- create table rows
        if(data_rows && data_rows.length){
            for (let i = 0, map_dict; map_dict = data_rows[i]; i++) {

                //console.log("map_dict", map_dict)
                //console.log("depbase_pk", selected.depbase_pk, map_dict.depbase_id)

        // only show rows of selected.depbase_pk etc
                let show_row = true;

                if (show_row && selected.depbase_pk && selected.depbase_pk !== map_dict.depbase_id) {show_row = false};
                if (show_row && selected.lvlbase_pk && selected.lvlbase_pk !== map_dict.lvlbase_id) {show_row = false};
                if (show_row && selected.sctbase_pk && selected.sctbase_pk !== map_dict.sctbase_id) {show_row = false};

                if(show_row){
                    CreateTblRow(tblName, field_setting, map_dict, col_hidden);
                };
          };
        }  // if(data_rows)
    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-07-31 PR2021-05-10
    function CreateTblHeader(field_setting, col_hidden) {
        //console.log("===  CreateTblHeader ===== ");
        //console.log("field_setting", field_setting);
        //console.log("columns_hidden", columns_hidden);

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
                const field_caption = (loc[field_setting.field_caption[j]]) ? loc[field_setting.field_caption[j]] : field_setting.field_caption[j] ;
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
        // --- add title of hdr is_mand_subj
                        if(field_name === "is_mand_subj"){
                            el_header.title = loc.Mandatory_if_subject_info;
                        }
        // --- add width, text_align
                        // not necessary: th_header.classList.add(class_width, class_align);
                        el_header.classList.add(class_width, class_align);

                if(filter_tag === "number"){el_header.classList.add("pr-3")}
if(j){th_header.classList.add("border_left")};
                        //if(["etenorm", "addedbyschool"].includes(field_name)){
                       //     el_header.classList.add("tickmark_2_2")
                        //}
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
if(j){th_filter.classList.add("border_left")};

        // --- add EventListener to el_filter
                    if (["text", "number"].includes(filter_tag)) {
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
                    // not necessary: th_filter.classList.add(class_width, class_align);
                    el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");
                th_filter.appendChild(el_filter)
                tblRow_filter.appendChild(th_filter);
            };
        }  // for (let j = 0; j < column_count; j++)

    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09 PR2021-05-10  PR2021-06-21
    function CreateTblRow(tblName, field_setting, map_dict, col_hidden) {
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
        let ob1 = "", ob2 = "", ob3 = "";
        if (tblName === "subject") {
            if (map_dict.name) { ob1 = map_dict.name.toLowerCase() };
        } else if (tblName === "scheme") {
            if (map_dict.name) { ob1 = map_dict.name.toLowerCase() };
        } else if (tblName === "schemeitem") {
            if (map_dict.scheme_name) { ob1 = map_dict.scheme_name.toLowerCase() };
            if (map_dict.subj_name) { ob2 = map_dict.subj_name.toLowerCase() };
            if (map_dict.sjtp_name) { ob3 = (map_dict.sjtp_name) };
        } else if (tblName === "subjecttype") {
            if (map_dict.scheme_name) { ob1 = map_dict.scheme_name.toLowerCase() };
            if (map_dict.sjtpbase_sequence) { ob2 = map_dict.sjtpbase_sequence.toString() };
        } else if (tblName === "subjecttypebase") {
            if (map_dict.name) { ob1 = map_dict.name.toLowerCase() };
        }
        const row_index = b_recursive_tblRow_lookup(tblBody_datatable, ob1, ob2, ob3, false, setting_dict.user_lang);

// --- insert tblRow into tblBody at row_index
        let tblRow = tblBody_datatable.insertRow(row_index);
        tblRow.id = map_id

// --- add data attributes to tblRow
        tblRow.setAttribute("data-pk", map_dict.id);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);
        tblRow.setAttribute("data-ob2", ob2);
        tblRow.setAttribute("data-ob3", ob3);

// --- add EventListener to tblRow
        tblRow.addEventListener("click", function() {HandleTblRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
        for (let j = 0; j < column_count; j++) {
            const field_name = field_names[j];

// --- skip columns if in columns_hidden
            if (!col_hidden.includes(field_name)){
                const field_tag = field_tags[j];
                const filter_tag = filter_tags[j];
                const class_width = "tw_" + field_width[j];
                const class_align = "ta_" + field_align[j];

        // --- insert td element,
                let td = tblRow.insertCell(-1);

        // --- create element with tag from field_tags
                let el = document.createElement(field_tag);

        // --- add data-field attribute
                el.setAttribute("data-field", field_name);

        // --- add width, text_align
                // not necessary: td.classList.add(class_width, class_align);
                el.classList.add(class_width, class_align);

if(j){td.classList.add("border_left")};

                if(filter_tag === "number"){el.classList.add("pr-3")}


        // --- append element
                td.appendChild(el);

    // --- add EventListener to td
                if (tblName === "subject"){
                    if (["code", "name", "depbases", "sequence"].includes(field_name)){
                        td.addEventListener("click", function() {MSUBJ_Open(el)}, false)
                        td.classList.add("pointer_show");
                        add_hover(td)
                    }

                } else if (tblName === "scheme"){
                     if (field_tag === "input"){
                        el.setAttribute("type", "text")
                        el.setAttribute("autocomplete", "off");
                        el.setAttribute("ondragstart", "return false;");
                        el.setAttribute("ondrop", "return false;");
                        el.classList.add("input_text");
        // --- add EventListener
                        el.addEventListener("change", function() {UploadInputChange(tblName, el)}, false)
                        el.addEventListener("keydown", function(event){HandleArrowEvent(el, event)});
                    } else if (filter_tag ==="toggle"){
                        // attach eventlisterener and hover to td, not to el. No need to add icon_class here
                        td.addEventListener("click", function() {HandleToggle(tblName, el)}, false)
                        td.classList.add("pointer_show");
                        add_hover(td)

                    }

                } else if (tblName === "schemeitem"){
                    if ( filter_tag ==="text"){
                        if(field_name === "otherlang"){
                            td.addEventListener("click", function() {MOL_Open(el)}, false);
                        } else {
                            td.addEventListener("click", function() {MSI_Open(el)}, false);
                        };
                            td.classList.add("pointer_show");
                            add_hover(td);
                    } else if (filter_tag ==="toggle"){
                        // skip max_reex and no_thirdperiod when weight_ce = 0
                        if(!["max_reex", "no_thirdperiod"].includes(field_name) || map_dict.weight_ce) {
                            td.addEventListener("click", function() {HandleToggle(tblName, el)}, false)
                            td.classList.add("pointer_show");
                            add_hover(td)
                        }
                    }
                } else if (tblName === "subjecttype"){
                    if (field_tag === "input"){
                        el.setAttribute("type", "text")
                        el.setAttribute("autocomplete", "off");
                        el.setAttribute("ondragstart", "return false;");
                        el.setAttribute("ondrop", "return false;");
                        el.classList.add("input_text");
        // --- add EventListener
                        el.addEventListener("change", function() {UploadInputChange(tblName, el)}, false)
                        el.addEventListener("keydown", function(event){HandleArrowEvent(el, event)});
                    } else if (filter_tag ==="toggle"){
                        td.addEventListener("click", function() {HandleToggle(tblName, el)}, false)
                        td.classList.add("pointer_show");
                        add_hover(td)
                    } else if (field_name !== "select"){
                        td.addEventListener("click", function() {MSJTP_Open(el)}, false)
                        td.classList.add("pointer_show");
                        add_hover(td)
                    }
                } else if (tblName === "subjecttypebase"){
                    if (field_tag === "input"){
                        el.setAttribute("type", "text")
                        el.setAttribute("autocomplete", "off");
                        el.setAttribute("ondragstart", "return false;");
                        el.setAttribute("ondrop", "return false;");
                        el.classList.add("input_text");
        // --- add EventListener
                        el.addEventListener("change", function() {UploadInputChange(tblName, el)}, false)
                    }
                }

// --- put value in field
               UpdateField(el, map_dict)
           };  // if (!columns_hidden[field_name]){
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

//=========  UpdateField  ================ PR2020-08-16 PR2021-05-10
    function UpdateField(el_div, map_dict) {
        //console.log("=========  UpdateField =========");
        //console.log("el_div", el_div);
        //console.log("map_dict", map_dict);

        if(el_div){
            const field_name = get_attr_from_el(el_div, "data-field");
            // '0' is a valid value, must be shown
            const fld_value = map_dict[field_name];

            if(field_name){
                let inner_text = null, title_text = null, filter_value = null;
                if (field_name === "select") {
                    // TODO add select multiple users option PR2020-08-18
                } else if (["scheme_name", "abbrev", "sjtpbase_name", "code", "name", "subj_code", "subj_name", "sjtp_abbrev", "depbase_code", "lvl_abbrev", "sct_abbrev"].includes(field_name)){
                    inner_text = fld_value;
                    filter_value = (inner_text) ? inner_text.toLowerCase() : null;
                } else if (["min_subjects", "max_subjects", "min_mvt", "max_mvt", "min_wisk", "max_wisk", "min_combi", "max_combi", "max_reex",
                            "min_extra_nocount" , "max_extra_nocount", "min_extra_counts", "max_extra_counts",
                            "weight_se", "weight_ce", "sequence"
                ].includes(field_name)){
                    inner_text = fld_value;
                    filter_value = (inner_text) ? inner_text : null;

                } else if ( field_name === "gradetype") {
                    inner_text = (fld_value === 2) ? "o/v/g" :
                                (fld_value === 1) ? loc.Grade : "---";
                    filter_value = (inner_text) ? inner_text.toLowerCase() : null;
                } else if ( field_name === "otherlang") {
                    // "\n" instead of null, otherwise green box not showing after removing lang
                    inner_text = (fld_value === "en;pa") ? loc.English_and_Papiamentu :
                                (fld_value === "pa") ? loc.Papiamentu :
                                (fld_value === "en") ? loc.English : "\n";
                    filter_value = (inner_text) ? inner_text.toLowerCase() : null;
                } else if ( field_name === "depbases") {
                    inner_text = b_get_depbases_display(department_map, "base_code", fld_value);
                    filter_value = (inner_text) ? inner_text.toLowerCase() : null;
                } else if (["ete_exam", "addedbyschool", "is_mandatory", "is_mand_subj", "is_combi", "is_core_subject", "is_mvt", "is_wisk",
                            "rule_avg_pece_sufficient", "rule_avg_pece_notatevlex",
                            "rule_grade_sufficient", "rule_gradesuff_notatevlex",
                            "rule_core_sufficient", "rule_core_notatevlex",
                            "extra_count_allowed", "extra_nocount_allowed",
                            "has_practexam", "has_pws", "sr_allowed", "reex_combi_allowed",
                            "no_reex", "no_exemption_ce"].includes(field_name)) {
                    filter_value = (fld_value) ? "1" : "0";
                    el_div.className = (fld_value) ? "tickmark_1_2" : "tickmark_0_0";

                } else if ( field_name === "multiplier") {
                    const counts_double = (fld_value === 2);
                    filter_value = (counts_double) ? "1" : "0";
                    el_div.className = (counts_double) ? "tickmark_1_2" : "tickmark_0_0";

                } else if ( field_name === "no_thirdperiod") {
                    if (map_dict.weight_ce){
                        const is_etenorm = fld_value;
                        filter_value = (is_etenorm) ? "1" : "0";
                        el_div.className = (is_etenorm) ? "tickmark_1_2" : "tickmark_0_0";
                    } else {
                        inner_text = "-";
                        filter_value = (inner_text) ? inner_text : null
                    }
                }
// ---  put value in innerText and title
                if (el_div.tagName === "INPUT"){
                    el_div.value = inner_text;
                } else {
                    el_div.innerText = inner_text;
                };
                // NIU yet: add_or_remove_attr (el_div, "title", !!title_text, title_text);

    // ---  add attribute filter_value
                add_or_remove_attr (el_div, "data-filter", !!filter_value, filter_value);
            }  // if(field_name)
        }  // if(el_div)
    };  // UpdateField

//###########################################################################
// +++++++++++++++++ UPLOAD CHANGES +++++++++++++++++++++++++++++++++++++++++

//========= UploadInputChange  ============= PR2021-06-27 PR2021-09-08
    function UploadInputChange(tblName, el_input) {
        console.log( " ==== UploadInputChange ====");
        console.log("el_input: ", el_input);

        const tblRow = get_tablerow_selected(el_input);
        if(tblRow){
            const data_dict = get_recursive_integer_lookup(tblRow);
        console.log("data_dict: ", data_dict);

            if(!isEmpty(data_dict)){
                const fldName = get_attr_from_el(el_input, "data-field");
                // note: el_input.value is a string, tharefore "0" is not falsy
                const new_value = el_input.value
        console.log("fldName: ", fldName);
        console.log("new_value: ", new_value, typeof new_value);

// ---  upload changes

                const upload_dict = {
                    mapid: data_dict.mapid,
                    scheme_pk: data_dict.scheme_id
                }
                if (tblName === "scheme"){
                    upload_dict.scheme_pk = data_dict.id;
                } else if (tblName === "schemeitem"){
                    upload_dict.si_pk = data_dict.id;
                    upload_dict.scheme_pk = data_dict.scheme_id;
                } else if (tblName === "subjecttype"){
                    upload_dict.subjecttype_pk = data_dict.id;
                    upload_dict.scheme_pk = data_dict.scheme_id;
                } else if (tblName === "subjecttypebase"){
                    upload_dict.sjtpbase_pk = data_dict.id;
                };
                upload_dict[fldName] = new_value

                const url_str = get_url_str();
                UploadChanges(upload_dict, url_str);
            }  //  if(!isEmpty(data_dict)){
        }  //   if(!!tblRow)
    }  // UploadInputChange

//========= HandleToggle  ============= PR2021-05-12  PR2021-06-21
    function HandleToggle(tblName, el_input) {
        console.log( " ==== HandleToggle ====");
        console.log("tblName: ", tblName);
        console.log("el_input: ", el_input);

        const tblRow = get_tablerow_selected(el_input);

        if(tblRow){
            if (setting_dict.sel_examyear_locked){
                const msg_html = loc.This_examyear + loc.is_locked + "<br>" + loc.You_cannot_make_changes
                b_ShowModMessages([{class: "border_bg_warning", msg_html: msg_html}]);
            } else {
                const data_dict = get_recursive_integer_lookup(tblRow);
                console.log("data_dict: ", data_dict);

                if(!isEmpty(data_dict)){
                    const fldName = get_attr_from_el(el_input, "data-field");
                    let new_value = null, update_dict = {};
                    if (fldName === "gradetype"){
                        new_value = (data_dict[fldName] === 1 ) ? 2 : 1;
                    } else if (fldName === "weight_se"){
                        new_value = (data_dict[fldName] === 1 ) ? 2 : 1;
                    } else if (fldName === "weight_ce"){
                        new_value = (data_dict[fldName] === 1 ) ? 0 : 1;
                    } else if (fldName === "multiplier"){
                        new_value = (data_dict[fldName] === 1 ) ? 2 : 1;
                    } else if (fldName === "max_reex"){
                        const old_value = (data_dict[fldName]) ? (data_dict[fldName]) : 0;
                        new_value = old_value + 1;
                        if (new_value > 3) {new_value = 0}
                    } else {
                        new_value = (data_dict[fldName] == true ) ? false : true;
    // ---  change icon, before uploading
                    //add_or_remove_class(el_input, "tickmark_1_2", new_value, "tickmark_0_0");
                    }
                    update_dict[fldName] = new_value;
                    UpdateField(el_input, update_dict)

    // ---  upload changes
                    const upload_dict = {
                        mode: "update",
                        mapid: data_dict.mapid,
                        table: tblName,
                    }
                    if (tblName === "subject"){
                        upload_dict.subject_pk = data_dict.id;
                    } else if (tblName === "scheme"){
                        upload_dict.scheme_pk = data_dict.id;
                    } else if (tblName === "subjecttype"){
                        upload_dict.subjecttype_pk = data_dict.id;
                        upload_dict.scheme_pk = data_dict.scheme_id;
                    } else if (tblName === "schemeitem"){
                        upload_dict.si_pk = data_dict.id;
                        upload_dict.scheme_pk = data_dict.scheme_id;
                    };
                    upload_dict[fldName] = new_value

                    const url_str = get_url_str();
                    UploadChanges(upload_dict, url_str);

                };  //  if(!isEmpty(data_dict)){
            };
        }  //   if(!!tblRow)
    }  // HandleToggle


//========= UploadChanges  ============= PR2020-08-03 PR2021-05-12
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
                        b_ShowModMessages(response.messages);
                    };

                    if ("updated_subject_rows" in response) {
                        if(el_MSUBJ_loader){ el_MSUBJ_loader.classList.add(cls_visible_hide)};
                        const tblName = "subject";
                        RefreshDataRows(tblName, response.updated_subject_rows, subject_rows, true)  // true = update
                    };
                    if ("updated_subjecttype_rows" in response) {
                        RefreshDataRows("subjecttype", response.updated_subjecttype_rows, subjecttype_rows, true)  // true = update
                    };
                    if ("updated_subjecttypebase_rows" in response) {
                        RefreshDataRows("subjecttypebase", response.updated_subjecttypebase_rows, subjecttypebase_rows, true)  // true = update
                    };
                    if ("updated_scheme_rows" in response) {
                        RefreshDataRows("scheme", response.updated_scheme_rows, scheme_rows, true)  // true = update
                    };
                    if ("updated_schemeitem_rows" in response) {
                        RefreshDataRows("schemeitem", response.updated_schemeitem_rows, schemeitem_rows, true)  // true = update
                    };
                    if ("log_list" in response) {
                       OpenLogfile(response.log_list);
                    };

                    $("#id_mod_subject").modal("hide");

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
// +++++++++++++++++ REFRESH DATA ROWS +++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataRows  ================  PR2021-06-21
    function RefreshDataRows(tblName, update_rows, data_rows, is_update) {
        console.log(" --- RefreshDataRows  ---");
        //console.log("tblName", tblName);
        //console.log("selected.scheme_pk", selected.scheme_pk);

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
        console.log("update_dict", update_dict);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);

            let updated_columns = [];
            let field_error_list = []

            const error_list = get_dict_value(update_dict, ["error"], []);
        //console.log("error_list", error_list);

            if(error_list && error_list.length){

    // - show modal messages
                // TODO cannot show error_list in b_ShowModMessages.Already shown by response.messages
                b_ShowModMessages(error_list);

                // TODO error_list is list of strings, not a dict with 'field
    // - add fields with error in updated_columns, to put old value back in field
                for (let i = 0, msg_dict ; msg_dict = error_list[i]; i++) {
                    if ("field" in msg_dict){field_error_list.push(msg_dict.field)};
                };

        //console.log("field_error_list", field_error_list);
            //} else {
            // close modal MSJ when no error --- already done in modal
                //$("#id_mod_subject").modal("hide");
            }

// ---  get list of hidden columns
        // copy col_hidden from mod_MCOL_dict.cols_hidden
        const col_hidden = [];
        b_copy_array_noduplicates(mod_MCOL_dict.cols_hidden, col_hidden)

// ---  get list of columns that are not updated because of errors
            const error_columns = (update_dict.err_fields) ? update_dict.err_fields : [];

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

    // ---  create row in table, insert in alphabetical order
                const new_tblRow = CreateTblRow(tblName, field_setting, update_dict, col_hidden)

    // ---  scrollIntoView,
                if(new_tblRow){
                    new_tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' })

    // ---  make new row green for 2 seconds,
                    ShowOkElement(new_tblRow);
                }
            } else {

// +++ get existing data_dict from data_rows
                const map_rows = (tblName === "subject") ? subject_rows :
                                (tblName === "scheme") ? scheme_rows :
                                (tblName === "schemeitem") ? schemeitem_rows :
                                (tblName === "subjecttype") ? subjecttype_rows :
                                (tblName === "subjecttypebase") ? subjecttypebase_rows : [];

                const pk_int = (update_dict && update_dict.id) ? update_dict.id : null;
                const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);
                const data_dict = (!isEmpty(found_dict)) ? found_dict : null;
                const datarow_index = index;

// ++++ deleted ++++
                if(is_deleted){
                    // delete row from data_rows. Splice returns array of deleted rows
                    const deleted_row_arr = data_rows.splice(datarow_index, 1)
                    const deleted_row_dict = deleted_row_arr[0];

    //--- delete tblRow
                    if(deleted_row_dict && deleted_row_dict.mapid){
                        const tblRow_tobe_deleted = document.getElementById(update_dict.mapid);
    // ---  when delete: make tblRow red for 2 seconds, before uploading
                        tblRow_tobe_deleted.classList.add("tsa_tr_error")
                        setTimeout(function() {
                            tblRow_tobe_deleted.parentNode.removeChild(tblRow_tobe_deleted)
                        }, 2000);
                    };
                } else {

// +++++++++++ updated row +++++++++++
    // ---  check which fields are updated, add to list 'updated_columns'
                    if(!isEmpty(data_dict) && field_names){

                        // skip first column (is margin)
                        for (let i = 1, col_field, old_value, new_value; col_field = field_names[i]; i++) {
                            if (col_field in data_dict && col_field in update_dict){
                                if (data_dict[col_field] !== update_dict[col_field] ) {
        // ---  add field to updated_columns list
                                    updated_columns.push(col_field)
        // ---  update field in data_row
                                    data_dict[col_field] = update_dict[col_field];
                        }}};

        // ---  update field in tblRow
                        // note: when updated_columns is empty, then updated_columns is still true.
                        // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
                        if(updated_columns.length || field_error_list.length){
        //console.log("updated_columns", updated_columns);
        //console.log("field_error_list", field_error_list);

// --- get existing tblRow
                            let tblRow = document.getElementById(map_id);
                            if(tblRow){
                // to make it perfect: move row when first or last name have changed
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
                                        el_fldName = get_attr_from_el(el, "data-field")
                                        const is_updated_field = updated_columns.includes(el_fldName);
                                        const is_err_field = error_columns.includes(el_fldName);
    // - update field and make field green when field name is in updated_columns
                                        if(is_updated_field){
                                                UpdateField(el, update_dict);
                                                ShowOkElement(el);
                                        } else if( is_err_field){
    // - make field red when error and reset old value after 2 seconds
                                            reset_element_with_errorclass(el, update_dict, tobedeleted)
                                        };
                                    }  //  if (el)
                                };  //  for (let i = 1, el_fldName, el; el = tblRow.cells[i]; i++) {
                            };  // if(tblRow){
                        }; //  if(updated_columns.length){
                    };  //  if(!isEmpty(update_dict))
                };  //  if(is_deleted)
            }; // if(is_created)
        };  // if(!isEmpty(update_dict))
    }  // RefreshDatarowItem

//=========  reset_element_with_errorclass  ================ PR2021-12-15
    function reset_element_with_errorclass(el_input, update_dict, tobedeleted) {
        // make field red when error and reset old value after 2 seconds
        const err_class = "border_bg_invalid";
        el_input.classList.add(err_class);
        setTimeout(function (){
            el_input.classList.remove(err_class);
            UpdateField(el_input, update_dict);
        }, 2000);
    }  //  reset_element_with_errorclass

//=========  fill_data_list  ================ PR2020-10-07
// TODO deprecate
    function fill_data_list(data_rows, key_field, value_field) {
        //console.log(" --- fill_data_list  ---");
        // datalist maps row.id with row.abbrev
        let data_list = {};
        if (data_rows) {
            for (let i = 0, row; row = data_rows[i]; i++) {
                const key = row[key_field];
                data_list[key] = row[value_field];
            }
        }
       //console.log( "data_list", data_list);
        return data_list
    }  //  fill_data_list

//###########################################################################
// +++++++++++++++++ FILTER TABLE ROWS ++++++++++++++++++++++++++++++++++++++

//========= HandleFilterKeyup  ================= PR2021-05-12
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

//========= HandleFilterToggle  =============== PR2020-07-21 PR2020-09-14 PR2021-03-23  PR2021-07-13
    function HandleFilterToggle(el_input) {
        //console.log( "===== HandleFilterToggle  ========= ");

        // PR2021-05-30 debug: use cellIndex instead of attribute data-colindex,
        // because data-colindex goes wrong with hidden columns
        // was:  const col_index = get_attr_from_el(el_input, "data-colindex")
        const col_index = el_input.parentNode.cellIndex;
    //console.log( "col_index", col_index, "event.key", event.key);

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
        if(filter_tag === "toggle") {
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

    function Filter_TableRows() {  // PR2019-06-09 PR2020-08-31
        console.log( "===== Filter_TableRows=== ");
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

        for (let i = 0, tblRow, show_row; tblRow = tblBody_datatable.rows[i]; i++) {
            tblRow = tblBody_datatable.rows[i]
            show_row = t_ShowTableRowExtended(filter_dict, tblRow);
            add_or_remove_class(tblRow, cls_hide, !show_row)
        }
    }; // Filter_TableRows

//========= ShowTableRow  ==================================== PR2020-08-17
    function ShowTableRow(tblRow, tblName_settings) {
        // only called by Filter_TableRows
    //console.log( "===== ShowTableRow  ========= ");
    //console.log( "tblName_settings", tblName_settings);
        let hide_row = false;
        if (tblRow){
// show all rows if filter_name = ""
            if (!isEmpty(filter_dict)){
                for (let i = 1, el_fldName, el; el = tblRow.cells[i]; i++) {
                    const filter_text = filter_dict[i];
                    const filter_tag = field_settings[selected_btn].filter_tags[i];
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
    function ResetFilterRows() {  // PR2019-10-26 PR2020-06-20
       //console.log( "===== ResetFilterRows  ========= ");

        selected.subject_pk = null;
        selected.subject_dict = null;
        selected.schemeitem_dict = null;
        selected.subjecttype_dict = null;
        selected.copyto_examyear_dict = null;  // for Copy_subject_schemes PR2021-09-24

        selected.depbase_pk = null;
        selected.scheme_pk = null;
        selected.scheme_dict = null;
        selected.package_pk = null;

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

//=========  MSSSS_Response  ================ PR2021-01-23 PR2021-07-26
    function MSSSS_Response(tblName, selected_dict, selected_pk) {
        console.log( "===== MSSSS_Response ========= ");
        console.log( "tblName", tblName);
        console.log( "selected_pk", selected_pk);
        console.log( "selected_dict", selected_dict);

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
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);

        }

        if (tblName === "school") {

        } else {
            //b_UploadSettings ({selected_pk: selected_pk_dict}, urls.url_usersetting_upload);

            //UpdateHeaderText(selected_name);

    // ---  fill datatable
       //console.log("function MSSSS_Response");
            FillTblRows()

            //MSSSS_display_in_sbr()
        }
    }  // MSSSS_Response




//###########################################################################
//========= HandleArrowEvent  ================== PR2020-12-20
    function HandleArrowEvent(el, event){
        //console.log(" --- HandleArrowEvent ---")
        //console.log("event.key", event.key, "event.shiftKey", event.shiftKey)
        // This is not necessary: (event.key === "Tab" && event.shiftKey === true)
        // Tab and shift-tab move cursor already to next / prev element
        if (["Enter", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].indexOf(event.key) > -1) {
// --- get move_horizontal and move_vertical based on event.key and event.shiftKey
            let move_horizontal = (event.key === "ArrowRight" || (event.key === "Enter" && !event.shiftKey)) ? 1 :
                                    (event.key === "ArrowLeft" || (event.key === "Enter" && event.shiftKey)) ? -1 : 0
            let move_vertical = (event.key === "ArrowDown") ? 1 :
                                    (event.key === "ArrowUp") ? -1 : 0

            const td = el.parentNode
            let tblRow = td.parentNode
            const tblBody = tblRow.parentNode
// --- get the first and last index of imput columns
            let max_colindex = null,  min_colindex = null;
            for (let i = 0, fldName, cell, td; td = tblRow.cells[i]; i++) {
                cell = td.children[0];
                fldName = get_attr_from_el(cell, "data-field")
                //if ( ["pescore", "cescore", "segrade", "pegrade", "cegrade", "pecegrade", "finalgrade"].includes(fldName) ) {
                    if(min_colindex == null) {min_colindex = td.cellIndex}
                    max_colindex = td.cellIndex;
                //}
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
                const next_el = new_tblRow.cells[new_col_index].children[0];
                if(next_el){next_el.focus()}
            }
        }
    }  // HandleArrowEvent
//###########################################################################
// +++++++++++++++++ SIDE BAR +++++++++++++++++++++++++++++++++++++++++++++++

//=========  HandleSBRselect  ================ PR2021-07-23 PR2021-08-28
    function HandleSBRselect(el_select) {
        //console.log("===== HandleSBRselect =====");
        //console.log( "el_select.value: ", el_select.value, typeof el_select.value)

        // dont use setting_dict but selected to store selecttion, will not be saned on server
        const is_dep = (el_select.id === "id_SBR_select_department");
        const is_level = (el_select.id === "id_SBR_select_level");
        const is_sector = (el_select.id === "id_SBR_select_sector");

        const pk_key_str = (is_dep) ? "depbase_pk" :
                           (is_level) ? "lvlbase_pk" :
                           (is_sector) ? "sctbase_pk" : null;
        const caption_key_str = (is_dep) ? "depbase_code" :
                                (is_level) ? "level_abbrev" :
                                (is_sector) ? "sector_abbrev" : null;
        const sel_value = (Number(el_select.value)) ? Number(el_select.value) : null;
        selected[pk_key_str] =  sel_value;
        selected[caption_key_str] = (el_select.options[el_select.selectedIndex]) ? el_select.options[el_select.selectedIndex].text : null;

    // check if level must be shown (only when depbase is null or vsbo
        if (is_dep) {
            // get_level_req stores level_req and has_profiel in selected dict
            get_level_req(sel_value);
            add_or_remove_class(el_SBR_select_level.parentNode, cls_hide, !selected.level_req )
    // reset leerweg and sector when dep set to havo / vwo
            if (!selected.level_req){
                selected.lvlbase_pk =  null;
                selected.sel_level_abbrev = null;
                if (el_SBR_select_level){ el_SBR_select_level.value = null};
                //upload_dict.page_subject.selected_pk.sel_lvlbase_pk = null;
            }
    // fill select table sector / profiel
            SBR_FillSelectOptions("sector")
        }

// ---  FillTblRows
        //UpdateHeaderLeft();
        FillTblRows();

    }  // HandleSBRselect

//=========  get_level_req  ================ PR2021-08-28
    function get_level_req(depbase_pk) {
        //console.log( "===== set_SBR_level_sector_visible ========= ");
        let level_req = true;
        let has_profiel = false;
        for (const [map_id, map_dict] of department_map.entries()) {
            if(depbase_pk === map_dict.base_id){
                level_req = map_dict.lvl_req;
                has_profiel = map_dict.has_profiel;
                break;
        }};
        selected.level_req = level_req;
        selected.has_profiel = has_profiel;
    }  // get_level_req

//=========  SBR_FillSelectOptions  ================ PR2021-03-06  PR2021-05-21 PR2021-08-27
    function SBR_FillSelectOptions(tblName) {
        //console.log("=== SBR_FillSelectOptions");
        //console.log("tblName", tblName);

        const is_dep = (tblName === "department");
        const is_level = (tblName === "level");
        const is_sector = (tblName === "sector");

        const data_map = (is_dep) ? department_map :
                        (is_level) ? level_map :
                        (is_sector) ? sector_map : null;

        const SBR_all_sectors_profielen_txt = ( (!selected.depbase_pk) ? loc.All_sectors_profielen :
                            (selected.has_profiel) ? loc.Profiel : loc.Sector) + ":";

        const all_sectors_profielen_txt = (!el_SBR_select_sector_label) ? loc.All_sectors_profielen : (selected.has_profiel) ? loc.All_profielen :loc.All_sectors;
        const caption_all = "&#60" + (
                (is_dep) ? loc.All_departments :
                (is_level) ? loc.All_levels :
                (is_sector) ? all_sectors_profielen_txt : "---"
             ) + "&#62";

        let found_in_new_list = false;
        const display_rows = [];
        let count = 0;
        for (const [map_id, map_dict] of data_map.entries()) {
            let add_row = true;
            if (is_sector) {
                if(map_dict.depbases && selected.depbase_pk) {
                    const depbases_delim = ";" + map_dict.depbases + ";";
                    const depbase_pk_delim = ";" + selected.depbase_pk + ";";
                    add_row = depbases_delim.includes(depbase_pk_delim);
                };
            };
            if (add_row){
                if (is_sector) {
                    if (selected.sctbase_pk === map_dict.base_id) {found_in_new_list = true};
                }
                display_rows.push({
                    value: map_dict.base_id,
                    caption: (is_dep) ?  map_dict.base_code :
                             (is_level) ? map_dict.abbrev :
                             (is_sector) ? map_dict.name : "---"
                });
                count += 1;
            };
        };
        // reset selected.sctbase_pk when not found in new list
        if (is_sector && !found_in_new_list) {
            selected.sctbase_pk = null;
        }

        if(count){
            if (count === 1){
            // if only 1 option: make that the selected one
                if (is_dep){
                    selected.depbase_pk = map_dict.base_id;
                } else if (is_level){
                    selected.lvlbase_pk = map_dict.base_id;
                } else if (is_sector){
                    selected.sctbase_pk = map_dict.base_id
                }
            } else {
                // add row 'Alle leerwegen' / Alle profielen / Alle sectoren in first row
                // HTML code "&#60" = "<" HTML code "&#62" = ">";
                // The unshift() method adds new items to the beginning of an array, and returns the new length.
                display_rows.unshift({value: 0, caption: caption_all })
            }
        }
        const selected_pk = (is_dep) ? selected.depbase_pk :
                            (is_level) ? selected.lvlbase_pk :
                            (is_sector) ? selected.sctbase_pk : null;
        const el_SBR_select = (is_dep) ? el_SBR_select_department :
                            (is_level) ? el_SBR_select_level :
                            (is_sector) ? el_SBR_select_sector : null;
        t_FillOptionsFromList(el_SBR_select, display_rows, "value", "caption", null, null, selected_pk)

        // show select level and sector
        if (is_level){
            add_or_remove_class(el_SBR_select_level.parentNode, cls_hide, !count);

        } else if (is_sector){
            // set label of sector / profiel
            const SBR_sector_label_txt = ( (!selected.depbase_pk) ? loc.Sector + " / " + loc.Profiel :
                                         (selected.has_profiel) ? loc.Profiel : loc.Sector ) + ":";
            el_SBR_select_sector_label.innerText = SBR_sector_label_txt;
            add_or_remove_class(el_SBR_select_sector.parentNode, cls_hide, !count);
        };
    };  // SBR_FillSelectOptionsDepartmentLevelSector

//=========  SBR_show_all  ================ PR2021-08-28
    function SBR_show_all() {
        //console.log("===== SBR_show_all =====");
        // dont use t_SBR_show_all

        selected.depbase_pk = null;
        selected.lvlbase_pk = null;
        selected.sctbase_pk = null;

        el_SBR_select_department.value = null;
        el_SBR_select_level.value = null;
        el_SBR_select_sector.value = null;

        SBR_FillSelectOptions("sector");

        // show select box level, except when btn_subject btn_subjecttypebase
        const hide_level_sector = (["btn_subject", "btn_subjecttypebase"].includes(selected_btn));
        add_or_remove_class(el_SBR_select_level.parentNode, cls_hide, hide_level_sector );
        add_or_remove_class(el_SBR_select_sector.parentNode, cls_hide, hide_level_sector );

        FillTblRows();
    }  // SBR_show_all

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL SELECT EXAMYEAR OR OR DEPARTMENT ++++++++++++++++++++
// functions are in table.js, except for MSED_Response

//=========  MSED_Response  ================ PR2020-12-18 PR2021-05-10
    function MSED_Response(new_setting) {
        console.log( "===== MSED_Response ========= ");

        if(new_setting.all_countries){
    // open modconfirm for Copy_subject_schemes PR2021-09-24
            // put selected examyear_pk in selected.copyto_examyear_dict
            selected.copyto_examyear_dict = get_mapdict_from_datamap_by_tblName_pk(examyear_map, "examyear", new_setting.copyto_examyear_pk);
            ModConfirmOpen("examyear", "copy_scheme")
        } else {
    // ---  upload new selected_pk
            new_setting.page = setting_dict.sel_page;
    // also retrieve the tables that have been changed because of the change in examyear / dep

            const datalist_request = {
                    setting: new_setting,
                    department_rows: {get: true},
                    subject_rows: {get: true},
                    level_rows: {cur_dep_only: true},
                    sector_rows: {cur_dep_only: true},
                    subjecttype_rows: {cur_dep_only: false},
                    scheme_rows: {get: true}
                };

            DatalistDownload(datalist_request);
        };
    }  // MSED_Response



//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL SELECT  ++++++++++++++++++++++++++++

//=========  ModSelect_Open  ================ PR2020-10-27
    function ModSelect_Open(tblName) {
        //console.log( "===== ModSelect_Open ========= ", tblName);

        // <PERMIT> PR2020-10-27
        // - every user may change examyear and department
        // -- only insp, admin and system may change school
        const may_open_modselect = (tblName === "school") ? has_permit_select_school : true;

        //PR2020-10-28 debug: modal gives 'NaN' and 'undefined' when  loc not back from server yet
        if (may_open_modselect && !isEmpty(loc)) {

        const base_pk = (tblName === "examyear" && setting_dict.sel_examyear_pk) ? setting_dict.sel_examyear_pk :
                     (tblName === "school" && setting_dict.requsr_schoolbase_pk) ? setting_dict.requsr_schoolbase_pk :
                     (tblName === "department" && setting_dict.requsr_depbase_pk) ? setting_dict.requsr_depbase_pk : 0;

        //console.log( "base_pk ", base_pk);
            mod_dict = {base_pk: base_pk, table: tblName};
            el_ModSelect_input.value = null;
            const item = (tblName === "examyear") ? loc.an_examyear :
                         (tblName === "school") ? loc.a_school :
                         (tblName === "department") ? loc.a_department : "";
            const placeholder = loc.Type_few_letters_and_select + item + loc.in_the_list + "..";
            el_ModSelect_input.setAttribute("placeholder", placeholder)

            //console.log( "mod_dict ", mod_dict);
    // ---  fill select table
            ModSelect_FillSelectTable(tblName, 0);

    // ---  set header text
            el_ModSelect_header.innerText = loc.Select + item

    // ---  Set focus to el_ModSelect_input
            //Timeout function necessary, otherwise focus wont work because of fade(300)
            setTimeout(function (){el_ModSelect_input.focus()}, 50);

        // show modal
            $("#id_mod_select_examyear").modal({backdrop: true});
            }
    }  // ModSelect_Open

//=========  ModSelect_Save  ================ PR2020-10-28
    function ModSelect_Save() {
        //console.log("===  ModSelect_Save =========");
        //console.log("mod_dict", mod_dict);
// selected_pk: {sel_examyear_pk: 23, sel_schoolbase_pk: 15, sel_depbase_pk: 1}

// ---  upload new setting
        const setting = {page_subject: {mode: "get"}};
        if (mod_dict.table === "examyear"){
            setting.sel_examyear_pk = mod_dict.base_pk
        }
        const datalist_request = {
                // page_subject is necessary, otherwise sel_btn will loose its value
                setting: setting,
                examyear_rows: {get: true},
                subject_rows: {get: true},
                school_rows: {get: true},
                department_rows: {get: true},
                level_rows: {get: true},
                sector_rows: {get: true},
                subjecttype_rows: {cur_dep_only: false},
                scheme_rows: {get: true}
            };

        DatalistDownload(datalist_request);

// hide modal
        $("#id_mod_select_examyear").modal("hide");

    }  // ModSelect_Save

//=========  ModSelect_SelectItem  ================ PR2020-10-28
    function ModSelect_SelectItem(tblName, tblRow) {
        //console.log( "===== ModSelect_SelectItem ========= ");
        //console.log( tblRow);
        // all data attributes are now in tblRow, not in el_select = tblRow.cells[0].children[0];
// ---  get clicked tablerow
        if(tblRow) {
// ---  deselect all highlighted rows
            DeselectHighlightedRows(tblRow, cls_selected)
// ---  highlight clicked row
            tblRow.classList.add(cls_selected)
// ---  get pk from id of select_tblRow
            let data_pk = get_attr_from_el(tblRow, "data-pk", 0)
            if(!Number(data_pk)){
               mod_dict.base_pk = 0;
            } else {
                mod_dict.base_pk = Number(data_pk)
            }
            ModSelect_Save()
        }
    }  // ModSelect_SelectItem

//=========  MSE_InputKeyup  ================ PR2020-03-01
    function MSE_InputKeyup() {
        //console.log( "===== MSE_InputKeyup  ========= ");

// ---  get value of new_filter
        let new_filter = el_ModSelect_input.value
        //console.log( "new_filter", new_filter);

        let tblBody = el_MSE_tblbody_select;
        //const len = tblBody.rows.length;
       // if (new_filter && len){
// ---  filter rows in table select_employee
            const filter_dict = t_Filter_SelectRows(tblBody, new_filter);
// ---  if filter results have only one employee: put selected employee in el_ModSelect_input
            const selected_pk = get_dict_value(filter_dict, ["selected_pk"])
            const selected_value = get_dict_value(filter_dict, ["selected_value"])
        //console.log( "selected_pk", selected_pk);
            if (selected_pk) {
                el_ModSelect_input.value = selected_value;
// ---  put pk of selected employee in mod_dict
                if(!Number(selected_pk)){
                    if(selected_pk === "addall" ) {
                        mod_dict.selected_employee_pk = 0;
                        mod_dict.selected_employee_code = null;
                    }
                } else {
                    mod_dict.selected_employee_pk =  Number(selected_pk);
                    mod_dict.selected_employee_code = selected_value;
                }

// ---  Set focus to btn_save
                el_MSE_btn_save.focus()
            }  //  if (!!selected_pk) {
      //  }
    }; // MSE_InputKeyup

//=========  ModSelect_FillSelectTable  ================ PR2020-08-21
    function ModSelect_FillSelectTable(tblName, selected_pk) {
        //console.log( "===== ModSelect_FillSelectTable ========= ");
        //console.log( "tblName: ", tblName);

        const caption_none = (tblName === "examyear") ? loc.No_exam_years :
                             (tblName === "school") ? loc.No_schools :
                             (tblName === "department") ?  loc.No_departments : "";
        const tblBody_select = (tblName === "examyear") ? el_MSEY_tblBody_select :
                             (tblName === "school") ? el_ModSelect_tblBody_select :
                             (tblName === "department") ?  el_ModSelect_tblBody_select : "";
        tblBody_select.innerText = null;

        let row_count = 0, add_to_list = false;
//--- loop through data_rows
        const data_rows = (tblName === "examyear") ? examyear_rows :
                         (tblName === "school") ? school_rows :
                         (tblName === "department") ? department_rows : null;
        //console.log( "data_rows: ", data_rows);
        for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
            add_to_list = ModSelect_FillSelectRow(data_dict, tblBody_select, tblName, -1, selected_pk);
            if(add_to_list){ row_count += 1};
        };

        if(!row_count){
            let tblRow = tblBody_select.insertRow(-1);
            const inner_text = (tblName === "order" && mod_dict.customer_pk === 0) ? loc.All_orders : caption_none

            let td = tblRow.insertCell(-1);
            td.innerText = inner_text;

        } else if(row_count === 1){
            let tblRow = tblBody_select.rows[0]
            if(tblRow) {
// ---  highlight first row
                tblRow.classList.add(cls_selected)
                if(tblName === "order") {
                    selected_period.order_pk = get_attr_from_el_int(tblRow, "data-pk");
                    MSE_SelectEmployee(tblName, tblRow)
                }
            }
        }
    }  // ModSelect_FillSelectTable

//=========  ModSelect_FillSelectRow  ================ PR2020-10-27
    function ModSelect_FillSelectRow(map_dict, tblBody_select, tblName, row_index, selected_pk) {
        //console.log( "===== ModSelect_FillSelectRow ========= ");
        //console.log("tblName: ", tblName);
        //console.log( "map_dict: ", map_dict);

//--- loop through data_map
        let pk_int = null, code_value = null, add_to_list = false, is_selected_pk = false;
        if(tblName === "examyear") {
            pk_int = map_dict.examyear_id;
            code_value = (map_dict.examyear) ? map_dict.examyear : "---"
            add_to_list = true;
       } else if(tblName === "school") {
            pk_int = map_dict.base_id;
            const code = (map_dict.sb_code) ? map_dict.sb_code : "---";
            const name = (map_dict.name) ? map_dict.name : "---";
            code_value = code + " - " + name;
            const shiftmap_order_pk = map_dict.o_id;
            // PR2020-06-11 debug: no matches because mod_dict.order_pk was str, not number.
            add_to_list = true

       } else if(tblName === "department") {
            pk_int = map_dict.base_id;
            code_value = (map_dict.abbrev) ? map_dict.abbrev : "---"
            add_to_list = true;

       }

       if (add_to_list){
            // selected_pk = 0 means: all customers / orders/ employees
            is_selected_pk = (selected_pk != null && pk_int === selected_pk)
// ---  insert tblRow  //index -1 results in that the new row will be inserted at the last position.
            let tblRow = tblBody_select.insertRow(row_index);
            tblRow.setAttribute("data-pk", pk_int);
            //tblRow.setAttribute("data-ppk", ppk_int);
            tblRow.setAttribute("data-value", code_value);
// ---  add EventListener to tblRow
            tblRow.addEventListener("click", function() {ModSelect_SelectItem(tblName, tblRow)}, false )
// ---  add hover to tblRow
            //tblRow.addEventListener("mouseenter", function(){tblRow.classList.add(cls_hover);});
            //tblRow.addEventListener("mouseleave", function(){tblRow.classList.remove(cls_hover);});
            add_hover(tblRow);
// ---  highlight clicked row
            //if (is_selected_pk){ tblRow.classList.add(cls_selected)}
// ---  add first td to tblRow.
            let td = tblRow.insertCell(-1);
// --- add a element to td., necessary to get same structure as item_table, used for filtering
            let el_div = document.createElement("div");
                el_div.innerText = code_value;
                el_div.classList.add("tw_090", "px-4", "pointer_show" )
            td.appendChild(el_div);
// --- add second td to tblRow with icon locked, published or activated.
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                el_div.classList.add("tw_032", "stat_1_6")
            td.appendChild(el_div);
        };
        return add_to_list;
    }  // ModSelect_FillSelectRow


//###########################################################################
// +++++++++ MOD SUBJECTTYPE ++++++++++++++++ PR2021-06-22 PR2021-09-08
// --- called by submenu btn Change_characters_of_subject_scheme and HandleTblRowClicked of subejecttype,
    function MSJTP_Open(el_input){
        console.log(" -----  MSJTP_Open   ----")

        if(permit_dict.permit_crud){
            const fldName = get_attr_from_el(el_input, "data-field");

            let tblName = "subjecttype";
            let data_dict = {};
            mod_MSJTP_dict = {};

            // el_input is undefined when called by submenu btn 'Add new'
            if(el_input){
                const tblRow = get_tablerow_selected(el_input);
                data_dict = get_recursive_integer_lookup(tblRow);
            } else {
                data_dict = selected.subjecttype_dict;
            }
            console.log( "data_dict: ", data_dict);

            const is_addnew = isEmpty(data_dict);
            if(is_addnew){
                mod_MSJTP_dict.is_addnew = true;
            } else {
                mod_MSJTP_dict.department_pk = data_dict.department_id;
                mod_MSJTP_dict.lvl_pk = data_dict.lvl_id;
                mod_MSJTP_dict.sct_pk = data_dict.sct_id;
                mod_MSJTP_dict.scheme_pk = data_dict.scheme_id;

                const scheme_dict = get_scheme_dict(data_dict.department_id, data_dict.lvl_id, data_dict.sct_id)
                if(scheme_dict){mod_MSJTP_dict.scheme_dict = scheme_dict}
            }

            //console.log("data_dict", data_dict)
            //console.log("mod_MSJTP_dict", mod_MSJTP_dict)

    // ---  set header text
            MSJT_set_headertext();

            el_MSJT_tblBody_subjecttype.innerText = null;
            el_MSJT_tblBody_sjtpbase.innerText = null;

            t_FillSelectOptions(el_MSJTP_department, department_map, "id", "base_code", false, null, null, loc.No_department_found, loc.Select_department);
            el_MSJTP_level.innerHTML = t_FillOptionLevelSectorFromMap("level", "id", level_map, mod_MSJTP_dict.department_pk, mod_MSJTP_dict.lvl_pk);
            el_MSJTP_sector.innerHTML = t_FillOptionLevelSectorFromMap("sector", "id", sector_map, mod_MSJTP_dict.department_pk, mod_MSJTP_dict.sct_pk);

            el_MSJTP_department.value = (mod_MSJTP_dict.department_pk) ? mod_MSJTP_dict.department_pk : null;
            MSI_MSJT_set_selectbox_level_sector("MSJT", mod_MSJTP_dict.department_pk);
            el_MSJTP_level.value = (mod_MSJTP_dict.lvl_pk) ? mod_MSJTP_dict.lvl_pk : null;
            el_MSJTP_sector.value = (mod_MSJTP_dict.sct_pk) ? mod_MSJTP_dict.sct_pk : null;

            MSJTP_FillDicts(mod_MSJTP_dict.scheme_pk);
            MSJTP_FillTbls();

    // ---  disable btn submit, hide delete btn when is_addnew
            add_or_remove_class(el_MSJT_btn_delete, cls_hide, is_addnew )
            add_or_remove_class(el_MSJT_btn_log, cls_hide, is_addnew )

            //el_MSJT_btn_save.disabled = true;

    // ---  show modal
            $("#id_mod_subjecttype").modal({backdrop: true});
        }
    };  // MSJTP_Open

//========= MSJT_Save  ============= PR2021-06-25
    function MSJT_Save(){
        //console.log(" -----  MSJT_Save   ----")

        if(permit_dict.permit_crud){
            const sjtp_dictlist = mod_MSJTP_dict.sjtp_dictlist
            //console.log( "sjtp_dictlist: ", sjtp_dictlist);

            const upload_sjtp_list = []
        // loop through sjtp_dictlist
            if (sjtp_dictlist && sjtp_dictlist.length) {
                for (let i = 0, sjtp_dict; sjtp_dict = sjtp_dictlist[i]; i++) {
                    //console.log( "sjtp_dict: ", sjtp_dict);
                    const sjtp_pk = sjtp_dict.sjtp_pk;
                    const sjtpbase_pk = sjtp_dict.sjtpbase_pk
                    //console.log( "sjtp_pk: ", sjtp_pk);
                    //console.log( "sjtpbase_pk: ",  sjtpbase_pk);
                    if(sjtp_dict.iscreated || sjtp_dict.isdeleted){
                        const upload_dict = {
                            sjtpbase_pk: sjtp_dict.sjtpbase_pk,
                            scheme_pk: sjtp_dict.scheme_pk,
                            name: sjtp_dict.name,
                            min_subjects: sjtp_dict.min_subjects,
                            max_subjects: sjtp_dict.max_subjects
                        };
                        if(sjtp_dict.iscreated){
                            upload_dict.create = true;
                        } else if(sjtp_dict.isdeleted){
                            upload_dict.sjtp_pk = sjtp_dict.sjtp_pk;
                            upload_dict.delete = true;
                        }
                        upload_sjtp_list.push(upload_dict);
            }}};

            if(upload_sjtp_list && upload_sjtp_list.length){
                const upload_dict = {
                    scheme_pk: mod_MSJTP_dict.scheme_pk,
                    sjtp_list: upload_sjtp_list
                }
                UploadChanges(upload_dict, urls.url_subjecttype_upload);
            }
        };  // if(permit_dict.permit_crud && mod_MSJTP_dict.stud_id){

// ---  hide modal
        $("#id_mod_subjecttype").modal("hide");

    }  // MSJT_Save

//========= MSJT_SelectChange  ============= PR2021-06-26
    function MSJT_SelectChange(el_input){
        //console.log( "===== MSJT_SelectChange  ========= ");
        //console.log( "el_input", el_input);
        const fldName = get_attr_from_el(el_input, "data-field");
        //console.log( "fldName", fldName);

        if(["department_pk", "lvl_pk", "sct_pk"].includes(fldName)){
            const fldValue = (Number(el_input.value)) ? Number(el_input.value) : null;
            const department_pk = (Number(el_MSJTP_department.value)) ? Number(el_MSJTP_department.value) : null;
            const dep_dict = get_mapdict_from_datamap_by_tblName_pk(department_map, "department", department_pk);
            const depbase_pk = get_dict_value(dep_dict, ["base_id"]);
            const lvl_pk = (el_MSJTP_level.value) ? Number(el_MSJTP_level.value) : null
            const sct_pk = (el_MSJTP_sector.value) ? Number(el_MSJTP_sector.value) : null

            if (fldName === "department_pk"){
                MSI_MSJT_set_selectbox_level_sector("MSJT", department_pk);
            }
            mod_MSJTP_dict.scheme_dict = get_scheme_dict(department_pk, lvl_pk, sct_pk);
            mod_MSJTP_dict.scheme_pk = (mod_MSJTP_dict.scheme_dict) ? mod_MSJTP_dict.scheme_dict.id : null;

            //MSJT_set_headertext();
            MSJTP_FillDicts(mod_MSJTP_dict.scheme_pk);
            MSJTP_FillTbls();

        } else if (fldName === "base_id"){
            document.getElementById("id_MSJT_name").value = el_input.options[el_input.selectedIndex].text;
        };

    }; // MSJT_SelectChange

//========= MSJT_InputKeyup  ============= PR2021-06-23
    function MSJT_InputKeyup(el_input){
        //console.log( "===== MSJT_InputKeyup  ========= ");
        //console.log( "el_input", el_input);
        el_input.classList.remove("border_bg_invalid");
        const fldName = get_attr_from_el(el_input, "data-field");
        //console.log( "fldName", fldName);
        // lookup scheme
        // only save scheme_dict in mod_MSJTP_dict, other variables are used to store 'old value'

        if(["department_pk", "lvl_pk", "sct_pk"].includes(fldName)){
            const fldValue = (Number(el_input.value)) ? Number(el_input.value) : null;
            mod_MSJTP_dict[fldName] = fldValue;

        //console.log( "fldValue", fldValue, typeof fldValue);
            if (fldName === "department_pk"){
                MSI_MSJT_set_selectbox_level_sector("MSJT", fldValue);
            }

            mod_MSJTP_dict.scheme_dict = MSJTP_get_scheme_from_input();
        //console.log("mod_MSJTP_dict.scheme_dict", mod_MSJTP_dict.scheme_dict)
            MSJT_set_headertext();

        } else if (fldName === "base_id"){
            document.getElementById("id_MSJT_name").value = el_input.options[el_input.selectedIndex].text;
        };
        //MSJT_validate_and_disable();
    }; // MSJT_InputKeyup

//=========  MSI_MSJT_set_selectbox_level_sector  ================  PR2021-06-24
    function MSI_MSJT_set_selectbox_level_sector(formName, department_pk) {
        //console.log(" -----  MSI_MSJT_set_selectbox_level_sector   ----")
        //console.log("department_pk", department_pk, typeof department_pk);
        //console.log("department_map", department_map, typeof department_map);
    // - get depbase_pk etc from department_map
        const dep_dict = get_mapdict_from_datamap_by_tblName_pk(department_map, "department", department_pk);
        //console.log("dep_dict", dep_dict, typeof dep_dict);
        const depbase_pk = (dep_dict) ? dep_dict.base_id : null;
        const lvl_req = (dep_dict) ? dep_dict.lvl_req : false;
        const sct_req = (dep_dict) ? dep_dict.sct_req : false;
        const has_profiel = (dep_dict) ? dep_dict.has_profiel : false;

        //console.log("depbase_pk", depbase_pk, typeof depbase_pk);
        //console.log("lvl_req", lvl_req, typeof lvl_req);
        //console.log("sct_req", sct_req, typeof sct_req);
        //console.log("has_profiel", has_profiel, typeof has_profiel);

    // - get lvl_pk and sct_pk from mod_MSI_dict / mod_MSJTP_dict
        //const el_select_level = document.getElementById("id_" + formName + "_level");
        //const el_select_sector = document.getElementById("id_" + formName + "_sector");
        const lvl_pk = (formName === "MSI") ? mod_MSI_dict.lvl_pk : (formName === "MSJT") ? mod_MSJTP_dict.lvl_pk : null;
        const sct_pk = (formName === "MSI") ? mod_MSI_dict.sct_pk : (formName === "MSJT") ? mod_MSJTP_dict.sct_pk : null;

        //console.log("lvl_pk", lvl_pk, typeof lvl_pk);
        //console.log("sct_pk", sct_pk, typeof sct_pk);

    // - set select options of level and sector
        const el_level_container = document.getElementById("id_" + formName + "_level_container");
        const el_sector_container = document.getElementById("id_" + formName + "_sector_container");
        add_or_remove_class(el_level_container, cls_hide, !lvl_req );
        add_or_remove_class(el_sector_container, cls_hide, !sct_req );

        const el_sector_label = document.getElementById("id_" + formName + "_sector_label");
        el_sector_label.innerText = (has_profiel) ? loc.Profiel : loc.Sector;

        const el_level = document.getElementById("id_" + formName + "_level");
        const el_sector = document.getElementById("id_" + formName + "_sector");
        el_level.innerHTML = t_FillOptionLevelSectorFromMap("level", "id", level_map, depbase_pk, lvl_pk);
        el_sector.innerHTML = t_FillOptionLevelSectorFromMap("sector", "id", sector_map, depbase_pk, sct_pk);

    }  // MSI_MSJT_set_selectbox_level_sector

//========= MSJTP_FillDicts  ============= PR2021-06-26
    function MSJTP_FillDicts(scheme_pk) {
        //console.log("===== MSJTP_FillDicts ===== ");
        //console.log("scheme_pk", scheme_pk);

        mod_MSJTP_dict.sjtp_dictlist = [];

// ---  loop through subjecttype_rows, add only subjecttypes from this scheme
        for (let i = 0, sjtp_dict; sjtp_dict = subjecttype_rows[i]; i++) {
            if(sjtp_dict.scheme_id && scheme_pk && sjtp_dict.scheme_id ===scheme_pk ){
                mod_MSJTP_dict.sjtp_dictlist.push( {
                    sjtp_pk: sjtp_dict.id,
                    sjtpbase_pk: sjtp_dict.base_id,
                    scheme_pk: sjtp_dict.scheme_id,
                    name: sjtp_dict.name,
                    abbrev: sjtp_dict.abbrev,
                    min_subjects: sjtp_dict.min_subjects,
                    max_subjects: sjtp_dict.max_subjects
                    } );
            };
        }
        //console.log("mod_MSJTP_dict", mod_MSJTP_dict);
    } // MSJTP_FillDicts

//========= MSJTP_FillTbls  ============= PR2021-06-26
    function MSJTP_FillTbls(justclicked_pk) {
        //console.log("===== MSJTP_FillTbls ===== ");
        //console.log("mod_MSJTP_dict", mod_MSJTP_dict);
        //console.log("justclicked_pk", justclicked_pk);

        el_MSJT_tblBody_subjecttype.innerText = null;
        el_MSJT_tblBody_sjtpbase.innerText = null;
        // function fills tblBody_subjecttype and tblBody_sjtpbase

// ---  fill subjects list with rows of mod_MSI_dict.subject_dict
        for (let i = 0, sjtpbase_dict; sjtpbase_dict=subjecttypebase_rows[i]; i++) {
            const sjtpbase_pk = sjtpbase_dict.id
            // check if sjtp exists in mod_MSJTP_dict.sjtp_dictlist
        //console.log("sjtpbase_dict", sjtpbase_dict);
        //console.log("sjtpbase_pk", sjtpbase_pk);
            const sjtp_dict = b_lookup_dict_in_dictlist(mod_MSJTP_dict.sjtp_dictlist, "sjtpbase_pk", sjtpbase_pk);
            const lookup_sjtpbase_pk = (sjtp_dict && sjtp_dict.sjtpbase_pk) ? sjtp_dict.sjtpbase_pk : null;
            const lookup_deleted =  (sjtp_dict && sjtp_dict.isdeleted) ? sjtp_dict.isdeleted : false;
        //console.log("sjtp_dict", sjtp_dict);
        //console.log("lookup_sjtpbase_pk", lookup_sjtpbase_pk);
        //console.log("lookup_deleted", lookup_deleted);
            if(lookup_sjtpbase_pk && !lookup_deleted){
                // MSI_MSJT_CreateSelectRow(tblName, tblBody_select, pk_int, dict, sjtp_pk, justclicked_pk)
                MSI_MSJT_CreateSelectRow("sjtp", el_MSJT_tblBody_subjecttype, sjtp_dict.sjtpbase_pk, sjtpbase_dict, null, justclicked_pk)
            } else {
                MSI_MSJT_CreateSelectRow("subjecttypebase", el_MSJT_tblBody_sjtpbase, sjtpbase_pk, sjtpbase_dict, null, justclicked_pk)
            }
        }
    } // MSJTP_FillTbls



//========= MSJT_SubjecttypebaseClicked  ============= PR2021-06-26
    function MSJT_SubjecttypebaseClicked(tr_clicked) {
        //console.log("===== MSJT_SubjecttypebaseClicked ===== ");
        //console.log("mod_MSJTP_dict", mod_MSJTP_dict);
        //console.log("mod_MSJTP_dict.sjtp_dictlist", mod_MSJTP_dict.sjtp_dictlist);

    // lookup sjtpbase in subjecttypebase_rows
        const sjtpbase_pk = get_attr_from_el_int(tr_clicked, "data-pk")
        const sjtpbase_dict = b_lookup_dict_in_dictlist(subjecttypebase_rows, "id", sjtpbase_pk);

        //console.log("sjtpbase_pk", sjtpbase_pk);
        //console.log("sjtpbase_dict", sjtpbase_dict);

        if(sjtpbase_dict){
    // check if sjtp exists in mod_MSJTP_dict.sjtp_dictlist
            const base_pk = sjtpbase_dict.id
            const sjtp_dict = b_lookup_dict_in_dictlist(mod_MSJTP_dict.sjtp_dictlist, "sjtpbase_pk", base_pk);
            const lookup_base_pk = (sjtp_dict && sjtp_dict.sjtpbase_pk) ? sjtp_dict.sjtpbase_pk : null;
            const lookup_deleted =  (sjtp_dict && sjtp_dict.isdeleted) ? sjtp_dict.isdeleted : false;

        //console.log("sjtp_dict", sjtp_dict);
        //console.log("lookup_base_pk", lookup_base_pk);
        //console.log("lookup_deleted", lookup_deleted);

            if(sjtp_dict){
            //  sjtp already exists in sjtp_dictlist
                if(lookup_deleted){
                    // undelete if deleted
                    sjtp_dict.isdeleted = false;
                }
            } else {
                // add subjecttype
                mod_MSJTP_dict.sjtp_dictlist.push( {
                    sjtp_pk: null,
                    sjtpbase_pk: sjtpbase_dict.id,
                    scheme_pk: mod_MSJTP_dict.scheme_pk,
                    name: sjtpbase_dict.name,
                    abbrev: sjtpbase_dict.abbrev,
                    sequence: sjtpbase_dict.sequence,
                    iscreated: true
                    } );
            }

        }
        const justclicked_pk = sjtpbase_pk;
        MSJTP_FillTbls(justclicked_pk);

    }  // MSJT_SubjecttypebaseClicked

//========= MSJT_SjtpClicked  ============= PR2021-06-26
    function MSJT_SjtpClicked(tr_clicked) {
        //console.log("  =====  MSJT_SjtpClicked  =====");

        const sjtpbase_pk = get_attr_from_el_int(tr_clicked, "data-pk")

        //console.log("tr_clicked", tr_clicked);
        //console.log("sjtpbase_pk", sjtpbase_pk);
        //console.log("mod_MSJTP_dict", mod_MSJTP_dict);


// lookup sjtp_dict in mod_MSJTP_dict.sjtp_dictlist,
// Note: lookup by base_pk, because new rows dont have sjtp_pk
        const sjtp_dictlist = mod_MSJTP_dict.sjtp_dictlist;
        //console.log("sjtp_dictlist", sjtp_dictlist);

        const [index, sjtp_dict] = b_lookup_dict_with_index_in_dictlist(sjtp_dictlist, "sjtpbase_pk", sjtpbase_pk)
        //console.log("index", index);
        //console.log("sjtp_dict", sjtp_dict);
        // sjtp_dict = {si_pk: null, sjtp_pk: 202, subj_pk: 759 ,name: "Franse taal", iscreated: true }

        if (sjtp_dict){
// ---  check if schemeitem_pk already exists in mod_MSJTP_dict.schemeitem_dict
            if(sjtp_dict.iscreated){
            // delete when si is created (is not saved yet)
                // splice(start, deleteCount, item1, item2, itemN)
                sjtp_dictlist.splice(index, 1)
            } else {
            // set deleted=true when it is a saved si
                sjtp_dict.isdeleted = true;
            }
        }
        const justclicked_pk = sjtpbase_pk;
        MSJTP_FillTbls(justclicked_pk);

    }  // MSJT_SjtpClicked


//=========  MSJTP_get_scheme_from_input  ================  PR2021-06-24
    function MSJTP_get_scheme_from_input() {
        //console.log(" -----  MSJTP_get_scheme_from_input   ----")
        let scheme_dict = null;
        const department_pk = (el_MSJTP_department.value) ? Number(el_MSJTP_department.value) : null
        const lvl_pk = (el_MSJTP_level.value) ? Number(el_MSJTP_level.value) : null
        const sct_pk = (el_MSJTP_sector.value) ? Number(el_MSJTP_sector.value) : null

        scheme_dict = get_scheme_dict(department_pk, lvl_pk, sct_pk);

        return scheme_dict;
    }  // MSJTP_get_scheme_from_input

//=========  get_scheme_dict  ================  PR2021-06-24
    function get_scheme_dict(department_pk, lvl_pk, sct_pk) {
        //console.log(" -----  get_scheme_dict   ----")
        let scheme_dict = null;
        const dep_dict = get_mapdict_from_datamap_by_tblName_pk(department_map, "department", department_pk);
        if(!isEmpty(dep_dict)){
            const lvl_req = (dep_dict.lvl_req) ? dep_dict.lvl_req : false;
            const sct_req = (dep_dict.sct_req) ? dep_dict.sct_req : false;

            for (let i = 0, row; row=scheme_rows[i]; i++) {
                const dep_found = (row.department_id === department_pk);
                const level_found = (!lvl_req || row.level_id === lvl_pk);
                const sector_found = (!sct_req || row.sector_id === sct_pk);

                if(dep_found && level_found && sector_found ){
                    scheme_dict = row;
                    break;
                };
            };  // for (let i = 0, row; row=scheme_rows[i]; i++)
        };  //  if(!isEmpty(dep_dict))
        return scheme_dict;
    }  // get_scheme_dict

//=========  MSJT_set_headertext  ================  PR2021-06-27
    function MSJT_set_headertext() {
        //console.log(" -----  MSJT_set_headertext   ----")
    // ---  set header text
        let header_text = loc.Subject_scheme + ": " ;
        if (mod_MSJTP_dict.scheme_dict) {
             header_text +=  (mod_MSJTP_dict.scheme_dict.name) ? mod_MSJTP_dict.scheme_dict.name : "---";
        }
        document.getElementById("id_MSJT_header").innerText = header_text;
    }  // MSJT_set_headertext

//=========  MSJT_validate_and_disable  ================  PR2021-06-23
    function MSJT_validate_and_disable() {
        //console.log(" -----  MSJT_validate_and_disable   ----")
        let disable_save_btn = false;
// ---  loop through input fields on  MSJTP_Open
        let input_elements = el_MSJT_form_controls.querySelectorAll(".form-control")
        for (let i = 0, el_input; el_input=input_elements[i]; i++) {
            const fldName = get_attr_from_el(el_input, "data-field");

            const msg_err = MSJT_validate_field(el_input, fldName);
            if(msg_err){disable_save_btn = true};
// ---  put border_bg_invalid in input box when error
            add_or_remove_class(el_input, "border_bg_invalid", msg_err)
// ---  put msg_err in msg_box or reset and hide
            b_render_msg_container("id_MSJT_msg_" + fldName, [msg_err])
        };
// ---  disable save button on error
        el_MSJT_btn_save.disabled = disable_save_btn;

    }  // MSJT_validate_and_disable

//=========  MSJT_validate_field  ================ PR2021-06-23
    function MSJT_validate_field(el_input, fldName) {
        //console.log(" -----  MSJT_validate_field   ----")
        //console.log("fldName", fldName)
        let msg_err = null;
        if (el_input){
            const value = el_input.value;
            //console.log("value", value)
            if (["code", "name"].includes(fldName)) {
                const caption = (fldName === "code") ? loc.Abbreviation : loc.Name;
                const max_length = (fldName === "code") ? 8 : 50;
                if (!value) {
                    msg_err = caption + loc.cannot_be_blank;
                } else if (value.length > max_length) {
                    msg_err = caption + ( (fldName === "code") ? loc.is_too_long_MAX10 : loc.is_too_long_MAX50 );
                }
            } else if(["sequence"].includes(fldName)){
                 if (!value) {
                    msg_err = loc.Sequence + loc.cannot_be_blank;
                 } else {
                    const arr = b_get_number_from_input(loc, fldName, el_input.value);
                    msg_err = arr[1];
                }
            }
        }
        return msg_err;
    }  // MSJT_validate_field


//###########################################################################
// +++++++++ MOD SUBJECTTYPE BASE ++++++++++++++++ PR2021-06-29
    function MSJTBASE_Open(el_input){
        //console.log(" -----  MSJTBASE_Open   ----")

        if (permit_dict.permit_crud){

            const fldName = get_attr_from_el(el_input, "data-field");
        //console.log("el_input", el_input)
        //console.log("fldName", fldName)

            // el_input is undefined when called by submenu btn 'Add new'
            const is_addnew = (!el_input);
            mod_MSJTBASE_dict = {}
            let tblName = "subjecttypebase";
            if(is_addnew){
                mod_MSJTBASE_dict = {is_addnew: is_addnew}
            } else {
                const tblRow = get_tablerow_selected(el_input);
                const map_dict = get_recursive_integer_lookup(tblRow);

                mod_MSJTBASE_dict = deepcopy_dict(map_dict);

        //console.log("mod_MSJTBASE_dict", mod_MSJTBASE_dict)
                const modified_dateJS = parse_dateJS_from_dateISO(mod_MSJTBASE_dict.modifiedat);
                const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
                const modified_by = (mod_MSJTBASE_dict.modby_username) ? mod_MSJTBASE_dict.modby_username : "-";
                const display_txt = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by;
                document.getElementById("id_MSJTBASE_msg_modified").innerText = display_txt;
            }

    // ---  set header text
            document.getElementById("id_MSJTBASE_header").innerText = mod_headertext(is_addnew, tblName, mod_MSJTBASE_dict.name);

    // ---  remove value from input elements
            MSJTBASE_ResetElements(true);  // true = also_remove_values

    // - sequence has value 5000 or max_sequence + 1 when  is_addnew
            //console.log("is_addnew", is_addnew)
            el_MSUBJ_sequence.value = (mod_MSJTBASE_dict.sequence) ? mod_MSJTBASE_dict.sequence : null;

            if (!is_addnew){
                el_MSUBJ_code.value = (mod_MSJTBASE_dict.code) ? mod_MSJTBASE_dict.code : null;
                el_MSUBJ_name.value = (mod_MSJTBASE_dict.name) ? mod_MSJTBASE_dict.name : null;

                const modified_dateJS = parse_dateJS_from_dateISO(mod_MSJTBASE_dict.modifiedat);
                const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
                const modified_by = (mod_MSJTBASE_dict.modby_username) ? mod_MSJTBASE_dict.modby_username : "-";

                document.getElementById("id_MSUBJ_msg_modified").innerText = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by
            }

  // put value of etenorm  as "1" or "0" in data-value
            const data_value = (!!mod_MSJTBASE_dict.etenorm) ? 1 : 0;
            el_MSUBJ_etenorm.setAttribute("data-value", data_value)
            const el_img = el_MSUBJ_etenorm.children[0];
            if(el_img){
                add_or_remove_class(el_img, "tickmark_2_2", !!data_value, "tickmark_0_0")
            }

            MSUBJ_FillSelectTableDepartment(mod_MSJTBASE_dict.depbases);

    // ---  set focus to  field that is clicked on el_MSUBJ_code
            const el_div_form_controls = document.getElementById("id_div_form_controls")
            let el_focus = el_div_form_controls.querySelector("[data-field=" + fldName + "]");
            if(!el_focus){ el_focus = el_MSUBJ_code};
            setTimeout(function (){el_focus.focus()}, 50);

            el_MSUBJ_message_container.innerHTML = null;

    // ---  disable btn submit, hide delete btn when is_addnew
            add_or_remove_class(el_MSUBJ_btn_delete, cls_hide, is_addnew )
            add_or_remove_class(el_MSUBJ_btn_log, cls_hide, is_addnew )

            el_MSUBJ_btn_save.disabled = true;

    // ---  show modal
            $("#id_mod_subjecttypebase").modal({backdrop: true});
        }
    };  // MSJTBASE_Open

//========= MSJTBASE_Save  ============= PR2021-06-25
    function MSJTBASE_Save(){
        //console.log(" -----  MSJTBASE_Save   ----")

        if(permit_dict.permit_crud){
            //console.log( "mod_MSJTBASE_dict: ", mod_MSJTBASE_dict);

            const sjtpbase_pk = mod_MSJTBASE_dict.sjtpbase_pk
            const upload_dict = {};
            if (sjtpbase_pk) {
                upload_dict.sjtpbase_pk = sjtpbase_pk
            } else {
                upload_dict.create = true;

            }
// ---  loop through input fields
            const el_form_controls = document.getElementById("id_MSJTBASE_form_controls")
            let input_elements = el_form_controls.querySelectorAll("input")
            for (let i = 0, el_input; el_input=input_elements[i]; i++) {
                const fldName = get_attr_from_el(el_input, "data-field");
                upload_dict[fldName] = el_input.value;

            };
            UploadChanges(upload_dict, urls.url_subjecttypebase_upload);
        };

// ---  hide modal
        $("#id_mod_subjecttypebase").modal("hide");

    }  // MSJTBASE_Save

//========= MSJTBASE_ResetElements  ============= PR2021-06-29
    function MSJTBASE_ResetElements(also_remove_values){
        //console.log( "===== MSJTBASE_ResetElements  ========= ");

// ---  loop through input fields
        const el_form_controls = document.getElementById("id_MSJTBASE_form_controls")
        let input_elements = el_form_controls.querySelectorAll("input")
        for (let i = 0, el_input; el_input=input_elements[i]; i++) {
            const fldName = get_attr_from_el(el_input, "data-field");
            el_input = document.getElementById("id_MSUBJ_" + fldName);
            if(el_input){
                el_input.classList.remove("border_bg_invalid", "border_bg_valid");
                if(also_remove_values){
                     el_input.value = null;
                };
            }
            const el_msg = document.getElementById("id_MSJTBASE_msg_" + fldName);
            if(el_msg){el_msg.innerText = null};
        };

        const el_msg_modified = document.getElementById("id_MSJTBASE_msg_modified")
        if(el_msg_modified){el_msg_modified.innertText = null;}

    }  // MSJTBASE_ResetElements

//###########################################################################
// +++++++++ MOD SUBJECT ++++++++++++++++ PR2020-09-30
// --- also used for level, sector,
    function MSUBJ_Open(el_input){
        //console.log(" -----  MSUBJ_Open   ----")

        //if(permit_dict.permit_crud){
        if(true){
            const fldName = get_attr_from_el(el_input, "data-field");
        //console.log("el_input", el_input)
        //console.log("fldName", fldName)

            // el_input is undefined when called by submenu btn 'Add new'
            const is_addnew = (!el_input);
            mod_MSUBJ_dict = {}
            let tblName = "subject";
            if(is_addnew){
                mod_MSUBJ_dict = {is_addnew: is_addnew,
                                    examyear_pk: setting_dict.sel_examyear_pk,
                                    sequence: 1 + MSUBJ_get_max_sequence()
                } // {is_addnew: is_addnew, db_code: setting_dict.sel_depbase_code}

            } else {
                const tblRow = get_tablerow_selected(el_input);
                const map_dict = get_recursive_integer_lookup(tblRow);
                mod_MSUBJ_dict = deepcopy_dict(map_dict);

                const modified_dateJS = parse_dateJS_from_dateISO(mod_MSUBJ_dict.modifiedat);
                const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
                const modified_by = (mod_MSUBJ_dict.modby_username) ? mod_MSUBJ_dict.modby_username : "-";
                const display_txt = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by;
                document.getElementById("id_MSUBJ_msg_modified").innerText = display_txt;
            }

// ---  set header text
            document.getElementById("id_MSUBJ_header").innerText = mod_headertext(is_addnew, tblName, mod_MSUBJ_dict.name);

// ---  remove value from input elements
            MSUBJ_ResetElements(true);  // true = also_remove_values

// - sequence has value 5000 or max_sequence + 1 when  is_addnew
            el_MSUBJ_sequence.value = (mod_MSUBJ_dict.sequence) ? mod_MSUBJ_dict.sequence : null;

            if (!is_addnew){
                el_MSUBJ_code.value = (mod_MSUBJ_dict.code) ? mod_MSUBJ_dict.code : null;
                el_MSUBJ_name.value = (mod_MSUBJ_dict.name) ? mod_MSUBJ_dict.name : null;
                el_MSUBJ_sequence.value = (mod_MSUBJ_dict.sequence) ? mod_MSUBJ_dict.sequence : null;

                const modified_dateJS = parse_dateJS_from_dateISO(mod_MSUBJ_dict.modifiedat);
                const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
                const modified_by = (mod_MSUBJ_dict.modby_username) ? mod_MSUBJ_dict.modby_username : "-";

                document.getElementById("id_MSUBJ_msg_modified").innerText = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by
            }

  // put value of etenorm  as "1" or "0" in data-value
            //const data_value = (!!mod_MSUBJ_dict.etenorm) ? 1 : 0;
            //el_MSUBJ_etenorm.setAttribute("data-value", data_value)
           //const el_img = el_MSUBJ_etenorm.children[0];
            //if(el_img){
            //    add_or_remove_class(el_img, "tickmark_2_2", !!data_value, "tickmark_0_0")
            //}

            MSUBJ_FillSelectTableDepartment(mod_MSUBJ_dict.depbases);

    // ---  set focus to  field that is clicked on el_MSUBJ_code
            const el_div_form_controls = document.getElementById("id_MSUBJ_form_controls")
            let el_focus = el_div_form_controls.querySelector("[data-field=" + fldName + "]");

        //console.log("el_focus", el_focus)
            if(!el_focus){ el_focus = el_MSUBJ_code};
            setTimeout(function (){el_focus.focus()}, 50);

            el_MSUBJ_message_container.innerHTML = null;

// ---  hide loader
            if(el_MSUBJ_loader){ el_MSUBJ_loader.classList.add(cls_visible_hide)};

// ---  disable btn submit, hide delete btn when is_addnew
            add_or_remove_class(el_MSUBJ_btn_delete, cls_hide, is_addnew )
            add_or_remove_class(el_MSUBJ_btn_log, cls_hide, is_addnew )

            el_MSUBJ_btn_save.disabled = true;

// ---  show modal
            $("#id_mod_subject").modal({backdrop: true});
        }
    };  // MSUBJ_Open

//=========  MSUBJ_Save  ================  PR2020-10-01
    function MSUBJ_Save(crud_mode) {
        //console.log(" -----  MSUBJ_save  ----", crud_mode);
        //console.log( "mod_MSUBJ_dict: ", mod_MSUBJ_dict);

        if(permit_dict.permit_crud){
            // delete is handled by ModConfirm("delete")
            let has_changes = false;
            let upload_dict = {table: 'subject', examyear_pk: mod_MSUBJ_dict.examyear_pk};
            if(mod_MSUBJ_dict.is_addnew) {
                upload_dict.mode = "create";
                has_changes = true;
            } else {
                upload_dict.subject_pk = mod_MSUBJ_dict.id;
                upload_dict.mapid = mod_MSUBJ_dict.mapid;
            }
    // ---  put changed values of input elements in upload_dict
            const form_elements = document.getElementById("id_MSUBJ_form_controls").querySelectorAll(".awp_input_text")
            for (let i = 0, el_input; el_input = form_elements[i]; i++) {
                const fldName = get_attr_from_el(el_input, "data-field");

                let new_value = (el_input.value) ? el_input.value : null;
                let old_value = (mod_MSUBJ_dict[fldName]) ? mod_MSUBJ_dict[fldName] : null;

                if(fldName === "sequence"){
                    new_value = (new_value && Number(new_value)) ? Number(new_value) : null;
                    old_value = (old_value && Number(old_value)) ? Number(old_value) : null;
                }
                if (new_value !== old_value) {
                    upload_dict[fldName] = new_value;
                    has_changes = true;
                };
            };
    // ---  get selected departments
            //let dep_list = MSUBJ_get_selected_depbases();
            //upload_dict['depbases'] = {value: dep_list, update: true}
            let new_depbases = MSUBJ_GetDepartmentsSelected();
            let old_depbases = (mod_MSUBJ_dict.depbases) ? mod_MSUBJ_dict.depbases : null;
            if (new_depbases !== old_depbases) {
                upload_dict['depbases'] = new_depbases;
                has_changes = true;
            }

    // ---  get etenorm from attribute 'data-value' in el_input
        const is_etenorm = (!!get_attr_from_el_int(el_MSUBJ_etenorm, "data-value"));
        if (is_etenorm !== mod_MSUBJ_dict.etenorm) {
            upload_dict['etenorm'] = is_etenorm;
            has_changes = true;
        }
        if(has_changes){
                if(el_MSUBJ_loader){ el_MSUBJ_loader.classList.remove(cls_visible_hide)};
                UploadChanges(upload_dict, urls.url_subject_upload);
            } else {
                $("#id_mod_subject").modal("hide");
            };
        };
    }  // MSUBJ_Save

//========= MSUBJ_FillSelectTableDepartment  ============= PR2021-05-10
    function MSUBJ_FillSelectTableDepartment(subject_depbases) {
        //console.log("===== MSUBJ_FillSelectTableDepartment ===== ");
        //console.log("department_map", department_map);

        const data_map = department_map;
        const tblBody_select = document.getElementById("id_MSUBJ_tblBody_department");
        tblBody_select.innerText = null;

// ---  loop through data_map
        const count_selected = {row_count: 0, selected_count: 0}
        for (const [map_id, dict] of data_map.entries()) {
            MSUBJ_FillSelectRowDepartment(tblBody_select, count_selected, dict);
        }
        if(data_map.size > 1) {
            MSUBJ_FillSelectRowDepartment(tblBody_select, count_selected, {}, "<" + loc.All_departments + ">");
        }
    }  // MSUBJ_FillSelectTableDepartment

//========= MSUBJ_FillSelectRowDepartment  ============= PR2021-05-10
    function MSUBJ_FillSelectRowDepartment(tblBody_select, count_selected, dict, select_all_text) {
        //console.log("===== MSUBJ_FillSelectRowDepartment ===== ");
        //console.log("dict", dict);

// add_select_all when not isEmpty(dict)
        let pk_int = null, map_id = null, base_code = null;
        let is_selected = false, row_index = -1;
        if (isEmpty(dict)){
            pk_int = 0;
            map_id = "sel_depbase_selectall";
            base_code = select_all_text
            row_index = 0;
// check 'selectall when all items are selected
            is_selected = (count_selected.row_count && count_selected.row_count === count_selected.selected_count)

        } else {
            pk_int = dict.base_id;
            map_id = "sel_depbase_" + dict.base_id;
            base_code = (dict.base_code) ? dict.base_code : "---";
            count_selected.row_count += 1
            row_index = -1;

// check if this department is in mod_MSUBJ_dict.depbases;. Set tickmark if yes
            if(mod_MSUBJ_dict.depbases){
                const arr = mod_MSUBJ_dict.depbases.split(";");
                arr.forEach((obj, i) => {
                     if (pk_int === Number(obj)) { is_selected = true}
                });
            }
        };

        if (is_selected){ count_selected.selected_count += 1 };
        const tickmark_class = (is_selected) ? "tickmark_2_2" : "tickmark_0_0";

        const tblRow = tblBody_select.insertRow(row_index);
        tblRow.id = map_id;
        tblRow.setAttribute("data-pk", pk_int);
        tblRow.setAttribute("data-selected", ((is_selected) ? 1 : 0) );

//- add hover to select row
        add_hover(tblRow)

// --- add first td to tblRow.
        let td = tblRow.insertCell(-1);
        let el_div = document.createElement("div");
            el_div.classList.add("tw_032", tickmark_class)
              td.appendChild(el_div);

// --- add second td to tblRow.
        td = tblRow.insertCell(-1);
        el_div = document.createElement("div");
            el_div.classList.add("tw_150")
            el_div.innerText = base_code;
            td.appendChild(el_div);

        td.classList.add("tw_200", "px-2", "pointer_show") // , "tsa_bc_transparent")

//--------- add addEventListener
        tblRow.addEventListener("click", function() {MSUBJ_SelectDepartment(tblRow)}, false);
    } // MSUBJ_FillSelectRowDepartment

//========= MSUBJ_SelectDepartment  ============= PR2021-05-10
    function MSUBJ_SelectDepartment(tblRow){
        //console.log( "===== MSUBJ_SelectDepartment  ========= ");

        if(tblRow){
            const old_is_selected = (!!get_attr_from_el_int(tblRow, "data-selected"));
            const pk_int = get_attr_from_el_int(tblRow, "data-pk");
            const is_select_all = (!pk_int);

// ---  toggle is_selected
            const new_is_selected = !old_is_selected;

            const tblBody_selectTable = tblRow.parentNode;
            if(is_select_all){
// ---  if is_select_all: select/ deselect all rows
                for (let i = 0, row, el, set_tickmark; row = tblBody_selectTable.rows[i]; i++) {
                    MSUBJ_SetDepartmentSelected(row, new_is_selected)
                }
            } else {
// ---  put new value in this tblRow, show/hide tickmark
                MSUBJ_SetDepartmentSelected(tblRow, new_is_selected)

// ---  select row 'select_all' if all other rows are selected, deselect otherwise
                // set 'select_all' true when all other rows are clicked
                let has_rows = false, unselected_rows_found = false;
                for (let i = 0, row; row = tblBody_selectTable.rows[i]; i++) {
                    let row_pk = get_attr_from_el_int(row, "data-pk");
                    //console.log( "row_pk", row_pk);
                    //console.log( "data-selected", get_attr_from_el_int(row, "data-selected"));
                    // skip row 'select_all'
                    if(row_pk){
                        has_rows = true;
                        if(!get_attr_from_el_int(row, "data-selected")){
                            unselected_rows_found = true;
                            break;
                }}};
                const selectall_is_selected = (has_rows && !unselected_rows_found)

// ---  set tickmark in row 'select_all'when has_rows and no unselected_rows_found
                const tblRow_selectall = document.getElementById("sel_depbase_selectall")
                MSUBJ_SetDepartmentSelected(tblRow_selectall, selectall_is_selected);

// ---  enable btn save
                MSUBJ_validate_and_disable()
            }
        }
    }  // MSUBJ_SelectDepartment

//========= MSUBJ_SetDepartmentSelected  ============= PR2020-10-01
    function MSUBJ_SetDepartmentSelected(tblRow, is_selected){
        //console.log( "  ---  MSUBJ_SetDepartmentSelected  --- ", is_selected);
// ---  put new value in tblRow, show/hide tickmark
        if(tblRow){
            tblRow.setAttribute("data-selected", ( (is_selected) ? 1 : 0) )
            const img_class = (is_selected) ? "tickmark_2_2" : "tickmark_0_0"
            const el = tblRow.cells[0].children[0];
             if (el){el.className = img_class}
        }
    }  // MSUBJ_SetDepartmentSelected

//========= MSUBJ_GetDepartmentsSelected  ============= PR2021-05-10
    function MSUBJ_GetDepartmentsSelected(){
        //console.log( "  ---  MSUBJ_GetDepartmentsSelected  --- ")
        let list_str = null;
        const tblBody_select = document.getElementById("id_MSUBJ_tblBody_department");
        let level_arr = [];
        for (let i = 0, row; row = tblBody_select.rows[i]; i++) {
            let row_pk = get_attr_from_el_int(row, "data-pk");
            // skip row 'select_all' with pk = 0, also skip when pk already in level_arr
            if(row_pk && !level_arr.includes(row_pk)){
                if(!!get_attr_from_el_int(row, "data-selected")){
                    level_arr.push(row_pk);
        }}};
        if (level_arr.length > 1) {
            level_arr.sort((a, b) => a - b);
        };
        if (level_arr.length) {
            list_str = level_arr.join(";");
        };
        return list_str;
    }  // MSUBJ_GetDepartmentsSelected

//========= MSUBJ_InputKeyup  ============= PR2020-10-01
    function MSUBJ_InputKeyup(el_input){
        //console.log( "===== MSUBJ_InputKeyup  ========= ");
        //console.log( "el_input", el_input);
        el_input.classList.remove("border_bg_invalid");
        MSUBJ_validate_and_disable();
    }; // MSUBJ_InputKeyup

//========= MSUBJ_Toggle  ============= PR2021-05-13
    function MSUBJ_Toggle(el_input){
        //console.log( "===== MSUBJ_Toggle  ========= ");

  // put value of etenorm  as "1" or "0" in data-value
        const old_data_value = get_attr_from_el_int(el_input, "data-value")
        const new_data_value = (!old_data_value) ? 1 : 0;
        el_MSUBJ_etenorm.setAttribute("data-value", new_data_value)

  // set img_class
        const el_img = el_MSUBJ_etenorm.children[0];
        if(el_img){
            add_or_remove_class(el_img, "tickmark_2_2", !!new_data_value, "tickmark_0_0")
        }
        MSUBJ_validate_and_disable();
    }; // MSUBJ_Toggle

//=========  MSUBJ_validate_and_disable  ================  PR2020-10-01
    function MSUBJ_validate_and_disable() {
        //console.log(" -----  MSUBJ_validate_and_disable   ----")
        let disable_save_btn = false;
// ---  loop through input fields on MSUBJ_Open
        let input_elements = el_MSUBJ_div_form_controls.querySelectorAll(".awp_input_text")
        for (let i = 0, el_input; el_input=input_elements[i]; i++) {
            const fldName = get_attr_from_el(el_input, "data-field");
            const msg_err = MSUBJ_validate_field(el_input, fldName);
            if(msg_err){disable_save_btn = true};
// ---  put border_bg_invalid in input box when error
            add_or_remove_class(el_input, "border_bg_invalid", msg_err)
// ---  put msg_err in msg_box or reset and hide
            b_render_msg_container("id_MSUBJ_msg_" + fldName, [msg_err])
        };
// ---  disable save button on error
        el_MSUBJ_btn_save.disabled = disable_save_btn;

        el_MSUBJ_message_container.innerHTML = null;
    }  // MSUBJ_validate_and_disable

//=========  MSUBJ_validate_field  ================  PR2020-10-01 PR2021-05-14
    function MSUBJ_validate_field(el_input, fldName) {
        //console.log(" -----  MSUBJ_validate_field   ----")
        //console.log("fldName", fldName)
        let msg_err = null;
        if (el_input){
            const value = el_input.value;
            //console.log("value", value)
            if (["code", "name"].includes(fldName)) {
                const caption = (fldName === "code") ? loc.Abbreviation : loc.Name;
                const max_length = (fldName === "code") ? 8 : 50;
                if (!value) {
                    msg_err = caption + loc.cannot_be_blank;
                } else if (value.length > max_length) {
                    msg_err = caption + ( (fldName === "code") ? loc.is_too_long_MAX10 : loc.is_too_long_MAX50 );
                }
            } else if(["sequence"].includes(fldName)){
                 if (!value) {
                    msg_err = loc.Sequence + loc.cannot_be_blank;
                 } else {
                    const arr = b_get_number_from_input(loc, fldName, el_input.value);
                    msg_err = arr[1];
                }
            }
        }
        return msg_err;
    }  // MSUBJ_validate_field

//========= MSUBJ_ResetElements  ============= PR2020-08-03
    function MSUBJ_ResetElements(also_remove_values){
        //console.log( "===== MSUBJ_ResetElements  ========= ");
        // --- loop through input elements
        const fields = ["code", "sequence", "name", "department", "modified"]
        for (let i = 0, field, el_input, el_msg; field = fields[i]; i++) {
            el_input = document.getElementById("id_MSUBJ_" + field);
            if(el_input){
                el_input.classList.remove("border_bg_invalid", "border_bg_valid");
                if(also_remove_values){
                    if (field === "modified"){
                        el_input.innertText = null;
                    } else {
                        el_input.value = null;
                    }
                };
            }
            el_msg = document.getElementById("id_MSUBJ_msg_" + field);
            if(el_msg){el_msg.innerText = null};
        }
        if(also_remove_values){
            document.getElementById("")
        }

    }  // MSUBJ_ResetElements

//========= MSUBJ_SetMsgElements  ============= PR2020-08-02
    function MSUBJ_SetMsgElements(response){
        //console.log( "===== MSUBJ_SetMsgElements  ========= ");

        const err_dict = ("msg_err" in response) ? response.msg_err : {}
        const validation_ok = get_dict_value(response, ["validation_ok"], false);

        //console.log( "err_dict", err_dict);
        //console.log( "validation_ok", validation_ok);

        const el_msg_container = document.getElementById("id_msg_container")
        let err_save = false;
        let is_ok = ("msg_ok" in response);
        if (is_ok) {
            const ok_dict = response["msg_ok"];
            document.getElementById("id_msg_01").innerText = get_dict_value(ok_dict, ["msg01"]);
            document.getElementById("id_msg_02").innerText = get_dict_value(ok_dict, ["msg02"]);
            document.getElementById("id_msg_03").innerText = get_dict_value(ok_dict, ["msg03"]);
            document.getElementById("id_msg_04").innerText = get_dict_value(ok_dict, ["msg04"]);

            el_msg_container.classList.remove("border_bg_invalid");
            el_msg_container.classList.add("border_bg_valid");

// ---  show only the elements that are used in this tab
            b_show_hide_selected_elements_byClass("tab_show", "tab_ok");

        } else {
            // --- loop through input elements
            if("save" in err_dict){
                err_save = true;
                document.getElementById("id_msg_01").innerText = get_dict_value(err_dict, ["save"]);
                document.getElementById("id_msg_02").innerText = null;
                document.getElementById("id_msg_03").innerText =  null;
                document.getElementById("id_msg_04").innerText =  null;

                el_msg_container.classList.remove("border_bg_valid");
                el_msg_container.classList.add("border_bg_invalid");
// ---  show only the elements that are used in this tab
                b_show_hide_selected_elements_byClass("tab_show", "tab_ok");

            } else {
                // TODO
                const fields = ["username",]
                for (let i = 0, field; field = fields[i]; i++) {
                    const msg_err = get_dict_value(err_dict, [field]);
                    const msg_info = loc.msg_user_info[i];

                    let el_input = document.getElementById("id_MSUBJ_" + field);
                    add_or_remove_class (el_input, "border_bg_invalid", (!!msg_err));
                    add_or_remove_class (el_input, "border_bg_valid", (!msg_err));

                    let el_msg = document.getElementById("id_MSUBJ_msg_" + field);
                    add_or_remove_class (el_msg, "text-danger", (!!msg_err));
                    el_msg.innerText = (!!msg_err) ? msg_err : msg_info
                }
            }
            el_MSUBJ_btn_save.disabled = !validation_ok;
            if(validation_ok){el_MSUBJ_btn_save.focus()}
        }
// ---  show message in footer when no error and no ok msg
        add_or_remove_class(el_MUA_info_footer01, cls_hide, !validation_ok )
        add_or_remove_class(el_MUA_info_footer02, cls_hide, !validation_ok )

// ---  set text on btn cancel
        const el_MUA_btn_cancel = document.getElementById("id_MUA_btn_cancel");
        el_MUA_btn_cancel.innerText = ((is_ok || err_save) ? loc.Close: loc.Cancel);
        if(is_ok || err_save){el_MUA_btn_cancel.focus()}

    }  // MUA_SetMsgElements

//========= mod_headertext  ======== // PR2020-09-30 PR2021-06-22
    function mod_headertext(is_addnew, tblName, name) {
        //console.log(" -----  mod_headertext   ----")
        //console.log("tblName", tblName, "is_addnew", is_addnew)
        let header_text = (tblName === "subject") ? (is_addnew) ? loc.Add_subject : loc.Subject :
                    (tblName === "subjecttype") ? (is_addnew) ? loc.Add_subjecttype : loc.Character :
                    (tblName === "subjecttypebase") ? (is_addnew) ? loc.Add_subjecttypebase : loc.Characterbase :
                    (tblName === "schemeitem") ? (is_addnew) ? loc.Add_schemeitem : loc.Schemeitem :
                    (tblName === "scheme") ? (is_addnew) ? loc.Add_subject_scheme : loc.Subject_scheme :
                    (tblName === "package") ? (is_addnew) ? loc.Add_package : loc.Package :
                    (tblName === "packageitem") ? (is_addnew) ? loc.Add_package_item : loc.Package_item : "---";
        if (!is_addnew) {
            header_text += ": " + ((name) ? name : "---")
        };
        return header_text;
    }  // mod_headertext

//========= MSUBJ_get_max_sequence  ============= PR2021-05-14
    function MSUBJ_get_max_sequence(){
        let max_sequence = 0;
        for (let i = 0, map_dict; map_dict = subject_rows[i]; i++) {
            if(map_dict.sequence && map_dict.sequence > max_sequence) { max_sequence = map_dict.sequence}
        };
        return max_sequence;
    }

//========= MSUBJ_render_messages  =================  PR2021-05-14
    function MSUBJ_render_messages(messages) {
        //console.log( "===== MSUBJ_render_messages -----")
        //console.log( "messages", messages)
        if (el_MSUBJ_message_container){
             el_MSUBJ_message_container.innerHTML = null;

            if (messages && messages.length) {
                for (let i = 0, msg_dict; msg_dict = messages[i]; i++) {
                    if (msg_dict && msg_dict.class){
                        let el_div = document.createElement("div");
                        el_div.classList.add("m-2", "p-2")
                        el_div.classList.add(msg_dict.class)

                        const msg_list = msg_dict.msg_list;
                        if(msg_list && msg_list.length){
                            for (let j = 0, msg, el_p; msg = msg_list[j]; j++) {
                                if(msg){
                                    el_p = document.createElement("p");
                                    el_p.innerHTML = msg
                                    el_div.appendChild(el_p);
                                }
                            }
                        }
                        el_MSUBJ_message_container.appendChild(el_div);
        }}}};
    }  // MSUBJ_render_messages

// +++++++++ END MOD SUBJECT ++++++++++++++++++++++++++++++++++++++++++++++++++++

//###########################################################################
// +++++++++ MOD SCHEMEITEM ++++++++++++++++ PR2021-06-22

    function MSI_Open(el_input){
        //console.log(" -----  MSI_Open   ----")
        //console.log("el_input", el_input)
        //console.log("permit_dict", permit_dict)

        if (permit_dict.permit_crud){

            mod_MSI_dict = {}; // stores general info of selected candidate in MSTUDSUBJ PR2020-11-21
            mod_MSI_dict.subject_dict = {};   // stores all subjects of this scheme
            mod_MSI_dict.schemeitem_dict = {};  // stores schemeitems of this scheme

            let tblName = "schemeitem";
            let map_dict = {};
            if (el_input){
                const tblRow = get_tablerow_selected(el_input);
                map_dict = get_recursive_integer_lookup(tblRow);
            } else {
                // dont get the scheme from selected.schemeitem_dict, but show the select boxes.
                // was: map_dict = selected.schemeitem_dict;

            }
        //console.log("map_dict", map_dict)
            const has_scheme = !isEmpty(map_dict);
            if(has_scheme) {
                mod_MSI_dict.department_pk = map_dict.department_id;
                mod_MSI_dict.depbase_pk = map_dict.depbase_id;
                mod_MSI_dict.lvl_pk = map_dict.level_id;
                mod_MSI_dict.sct_pk = map_dict.sector_id;
                mod_MSI_dict.scheme_pk = map_dict.scheme_id;
                mod_MSI_dict.scheme_name = map_dict.scheme_name;


    // ---  set header text
                MSI_set_headertext();

        // ---  remove value from el_mod_employee_input
                //MSTUD_SetElements();  // true = also_remove_values

                //document.getElementById("id_MSI_msg_modified").innerText = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by

                //console.log("mod_MSI_dict.department_pk", mod_MSI_dict.department_pk)
                //console.log("mod_MSI_dict.lvl_pk", mod_MSI_dict.lvl_pk)
                //console.log("mod_MSI_dict.sct_pk", mod_MSI_dict.sct_pk)

                t_FillSelectOptions(el_MSI_department, department_map, "id", "base_code", false, mod_MSI_dict.department_pk, null, loc.No_department_found, loc.Select_department);
                el_MSI_level.innerHTML = t_FillOptionLevelSectorFromMap("level", "id", level_map, mod_MSI_dict.depbase_pk, mod_MSI_dict.lvl_pk);
                el_MSI_sector.innerHTML = t_FillOptionLevelSectorFromMap("sector", "id", sector_map, mod_MSI_dict.depbase_pk, mod_MSI_dict.sct_pk);

                el_tblBody_subjects.innerText = null;
                el_tblBody_schemeitems.innerText = null;
                // hide selecrtboxes dep, lvl, sct when there is a scheme
                //console.log("has_scheme", has_scheme)
                add_or_remove_class(el_MSI_deplvlsct_container, cls_hide, has_scheme)

                MSI_SetInputFields(null, false);

                MSI_InputChange();
        // ---  set focus to el_MSTUD_abbrev
                //setTimeout(function (){el_MSTUD_abbrev.focus()}, 50);

        // ---  disable btn submit, hide delete btn when is_addnew
               // add_or_remove_class(el_MSTUD_btn_delete, cls_hide, is_addnew )
                //const disable_btn_save = (!el_MSTUD_abbrev.value || !el_MSTUD_name.value || !el_MSTUD_sequence.value )
                //el_MSTUD_btn_save.disabled = disable_btn_save;

                //MSTUD_validate_and_disable();
            }  // if(!isEmpty(map_dict)) {

// ---  show modal
            $("#id_mod_schemeitem").modal({backdrop: true});
        }  //  if (permit_dict.permit_crud){
    };  // MSI_Open

//========= MSI_Save  ============= PR2021-06-25
    function MSI_Save(){
        //console.log(" -----  MSI_Save   ----")


        if(permit_dict.permit_crud){
            const sjtp_dictlist = mod_MSI_dict.sjtp_dictlist
            //console.log( "sjtp_dictlist: ", sjtp_dictlist);

            const upload_si_list = []
        // loop through sjtp_dictlist
            if (sjtp_dictlist && sjtp_dictlist.length) {
                for (let i = 0, sjtp_dict; sjtp_dict = sjtp_dictlist[i]; i++) {
                    //console.log( "sjtp_dict: ", sjtp_dict);
                    const sjtp_pk = sjtp_dict.sjtp_pk;
                    //console.log( "sjtp_pk: ", sjtp_pk);
                    //console.log( "sjtp_pk: ", sjtp_pk);
                    if (sjtp_dict.si_list && sjtp_dict.si_list.length){
                        for (let i = 0, si_dict; si_dict = sjtp_dict.si_list[i]; i++) {
                            if(si_dict.iscreated || si_dict.isdeleted){
                                const dict = {subj_pk: si_dict.subj_pk, sjtp_pk: si_dict.sjtp_pk};
                                if(si_dict.iscreated){
                                    dict.create = true;
                                } else if(si_dict.isdeleted){
                                    dict.si_pk = si_dict.si_pk;
                                    dict.delete = true;
                                }
                                upload_si_list.push(dict);
            }}}}};

            if(upload_si_list && upload_si_list.length){
                const scheme_dict = mod_MSI_dict.scheme_dict;
                const scheme_pk = scheme_dict.id
                const upload_dict = {scheme_pk: scheme_pk, si_list: upload_si_list}
                //console.log("upload_dict: ", upload_dict)
                UploadChanges(upload_dict, urls.url_schemeitem_upload);
            }
        };  // if(permit_dict.permit_crud && mod_MSI_dict.stud_id){

// ---  hide modal
        $("#id_mod_schemeitem").modal("hide");

    }  // MSI_Save

//========= MSI_InputChange  ============= PR2021-06-24 PR2021-07-07
    function MSI_InputChange(){
        //console.log( "===== MSI_InputChange  ========= ");

        const department_pk = (Number(el_MSI_department.value)) ? Number(el_MSI_department.value) : null;
        const dep_dict = get_mapdict_from_datamap_by_tblName_pk(department_map, "department", department_pk);
        const depbase_pk = get_dict_value(dep_dict, ["base_id"]);
        const lvl_pk = (el_MSI_level.value) ? Number(el_MSI_level.value) : null
        const sct_pk = (el_MSI_sector.value) ? Number(el_MSI_sector.value) : null

        MSI_MSJT_set_selectbox_level_sector("MSI", department_pk);

        mod_MSI_dict.scheme_dict = get_scheme_dict(department_pk, lvl_pk, sct_pk);
        const scheme_pk = (mod_MSI_dict.scheme_dict) ? mod_MSI_dict.scheme_dict.id : null;

        MSI_set_headertext();
        MSI_FillDicts(depbase_pk, department_pk, scheme_pk);
        MSI_FillTblSubjects();
        MSI_FillTblSchemeitems();

        //MSI_validate_and_disable();
    }; // MSI_InputChange

//=========  MSI_set_headertext  ================  PR2021-06-24  PR2021-07-07
    function MSI_set_headertext() {
        //console.log(" -----  MSI_set_headertext   ----")
    // ---  set header text
        el_MSI_header.innerText =  (mod_MSI_dict.scheme_name) ? mod_MSI_dict.scheme_name : loc.Subject_scheme;
    }  // MSI_set_headertext

//========= MSI_FillDicts  ============= PR2021-06-22
    function MSI_FillDicts(depbase_pk, department_pk, scheme_pk) {
        //console.log("===== MSI_FillDicts ===== ");
        //console.log("subjecttype_rows", subjecttype_rows);
        //console.log("department_pk", department_pk, typeof department_pk);
        //console.log("depbase_pk", depbase_pk, typeof depbase_pk);
        //console.log("scheme_pk", scheme_pk);

//  list mod_MSI_dict.schemeitem_dict contains the existing, added and deleted schemeitem_dict of the scheme
//  list mod_MSI_dict.subject_dict contains all subjects of this departments
//  list mod_MSI_dict.subjecttype_dict contains all subjecttypes of this scheme
        mod_MSI_dict.schemeitem_dict = {};
        mod_MSI_dict.subject_dict = {}
        mod_MSI_dict.sjtp_dictlist = [];

// ---  loop through subject_rows, add only subjects from this department
        //console.log("subject_rows", subject_rows);
        for (let i = 0, subj_dict; subj_dict = subject_rows[i]; i++) {

            if(subj_dict.depbases && depbase_pk){
                //subj_dict.depbases: "2;3;"
                const db_wrapped = ";" + subj_dict.depbases + ";"
                const db_lookup = ";" + depbase_pk + ";"
                if (db_wrapped.includes(db_lookup)) {
                    mod_MSI_dict.subject_dict[subj_dict.id] = {subj_pk: subj_dict.id, name: subj_dict.name};
                };
            };
        }
        //console.log("mod_MSI_dict.subject_dict", mod_MSI_dict.subject_dict);

// ---  loop through subjecttype_rows, add only subjecttypes from this scheme
        for (let i = 0, sjtp_dict; sjtp_dict = subjecttype_rows[i]; i++) {
            if(sjtp_dict.scheme_id && scheme_pk && sjtp_dict.scheme_id ===scheme_pk ){
                mod_MSI_dict.sjtp_dictlist.push({
                    sjtp_pk: sjtp_dict.id,
                    name: sjtp_dict.name,
                    sequence: sjtp_dict.sjtpbase_sequence,
                    si_list: []
                });
            };
        }
        //console.log("mod_MSI_dict.sjtp_dictlist", mod_MSI_dict.sjtp_dictlist);

// ---  loop through schemeitem_map, add schemeitems from this scheme to mod_MSI_dict.sjtp_dictlist
         MSI_fill_si_list(scheme_pk)
    } // MSI_FillDicts

//========= MSI_FillTblSubjects  ============= PR2021-06-25
    function MSI_fill_si_list(scheme_pk) {
        //console.log("===== MSI_fill_si_list ===== ");

// ---  loop through schemeitem_rows, add schemeitems from this scheme with this subjecttype to si_list
        for (let i = 0, si_dict; si_dict=schemeitem_rows[i]; i++) {

        //console.log("si_dict", si_dict);
        // add only schemeitems from scheme of this student
            if (scheme_pk && scheme_pk === si_dict.scheme_id) {
                const sjtp_pk = get_dict_value(si_dict, ["sjtp_id"]);
                const sjtp_pk2 = si_dict.sjtp_id;
                // lookup sjtp_dict in mod_MSI_dict.sjtp_dictlist
                const sjtp_dict = b_lookup_dict_in_dictlist(mod_MSI_dict.sjtp_dictlist, "sjtp_pk", sjtp_pk)
                sjtp_dict.si_list.push({
                    si_pk: si_dict.id,
                    sjtp_pk: si_dict.sjtp_id,
                    subj_pk: si_dict.subj_id,
                    name: si_dict.subj_name,
                    sjtp_name: si_dict.sjtp_name,
                    sjtpbase_sequence: si_dict.sjtpbase_sequence
                    });
            }
        }
    };  // MSI_fill_si_list

//========= MSI_FillTblSubjects  ============= PR2021-06-24
    function MSI_FillTblSubjects() {
        //console.log("===== MSI_FillTblSubjects ===== ");

        el_tblBody_subjects.innerText = null;

// ---  fill subjects list with rows of mod_MSI_dict.subject_dict
        for (const [subject_pk_str, dict] of Object.entries(mod_MSI_dict.subject_dict)) {
        //console.log("dict", dict);
        //console.log("dict.subj_pk", dict.subj_pk);
                // MSI_MSJT_CreateSelectRow(tblName, tblBody_select, pk_int, dict, sjtp_pk, justclicked_pk)
            MSI_MSJT_CreateSelectRow("subject", el_tblBody_subjects, dict.subj_pk, dict);
        }

    } // MSI_FillTblSubjects

//========= MSI_FillTbls  ============= PR2021-06-22
    function MSI_FillTblSchemeitems(sel_schemeitem_pk_list) {
        //console.log("===== MSI_FillTblSchemeitems ===== ");

        // function fills table el_tblBody_schemeitems
        // with items of mod_MSI_dict.sjtp_dictlist
        // mod_MSI_dict.sjtp_dictlist also contains deleted subjects of scheme, with tag 'isdeleted'
        // sel_schemeitem_pk_list is a list of selected schemeitem_pk's, filled by MSI_AddRemoveSubject

        el_tblBody_schemeitems.innerText = null;

    //console.log("mod_MSI_dict", mod_MSI_dict);
    //console.log("mod_MSI_dict.sjtp_dictlist", mod_MSI_dict.sjtp_dictlist);

// ---  loop through the subjecttype dictlist (mod_MSI_dict.sjtp_dictlist)
        // mod_MSI_dict.sjtp_dictlist contains list of subjecttype dicts
        // each subjecttype dict contains list of schemitem dicts
        if(mod_MSI_dict.sjtp_dictlist && mod_MSI_dict.sjtp_dictlist.length){
            for (let i = 0, sjtp_dict; sjtp_dict = mod_MSI_dict.sjtp_dictlist[i]; i++) {

    // ---  add subjecttypes as subheader to list of schemeitems
                //console.log("sjtp_dict", sjtp_dict);
                //console.log("sjtp_dict.sjtp_pk", sjtp_dict.sjtp_pk);
                // MSI_MSJT_CreateSelectRow(tblName, tblBody_select, pk_int, dict, sjtp_pk, justclicked_pk)
                MSI_MSJT_CreateSelectRow("subjecttype", el_tblBody_schemeitems, sjtp_dict.sjtp_pk, sjtp_dict);

    // ---  add subjects of this subjecttype
                const si_list = sjtp_dict.si_list;
                //console.log("############ si_list", si_list);
                if (sjtp_dict.si_list && sjtp_dict.si_list.length){
                    for (let i = 0, si_dict; si_dict = sjtp_dict.si_list[i]; i++) {
                        //console.log("############", si_dict);
                        //console.log("si_dict", si_dict);
                        // skip when si_dict isdeleted
                        if(!si_dict.isdeleted){
                // MSI_MSJT_CreateSelectRow(tblName, tblBody_select, pk_int, dict, sjtp_pk, justclicked_pk)
                            MSI_MSJT_CreateSelectRow("schemeitem", el_tblBody_schemeitems, si_dict.subj_pk, si_dict, sjtp_dict.sjtp_pk);
                        }
                    }
                }
            };

    // ---  loop through mod_MSI_dict.schemeitem_dict
            // studsubj_si_list is list of schemeitem_id's of subjects of this student, that are not deleted
            const studsubj_si_list = [];
            let has_rows = false;

            for (const [studsubj_pk_str, dict] of Object.entries(mod_MSI_dict.schemeitem_dict)) {
                const studsubj_pk = Number(studsubj_pk_str);
            //console.log("studsubj_pk", studsubj_pk);
            //console.log("dict", dict);
                if (!dict.isdeleted) {
            // - add schemeitem_pk of  studsubj to studsubj_si_list
                    const schemeitem_pk = dict.schemeitem_id;
                    studsubj_si_list.push({si_pk: schemeitem_pk} )

                // MSI_MSJT_CreateSelectRow(tblName, tblBody_select, pk_int, dict, sjtp_pk, justclicked_pk)
                    MSI_MSJT_CreateSelectRow("schemeitem", el_tblBody_schemeitems, schemeitem_pk, dict);
                    has_rows = true;
                }
            }
        } else if(!isEmpty(mod_MSI_dict.scheme_dict)) {
            // show message when scheme does not have subjecttypes
            const html_list = ["<p>", loc.Scheme_doesnthave_subjecttypes, "</p><p>",
                            loc.Close_window,
                            " <i>", loc.Characters, "</i>,<br>",
                            loc.then_click,
                            " <i>", loc.Change_characters_of_subject_scheme, "</i><br>",
                            loc.Enter_subject_types, "</p>"]
            const html_str = html_list.join('')
        //console.log("html_str", html_str);
            el_tblBody_schemeitems.innerHTML = html_list.join('')
        };
    } // MSI_FillTblSchemeitems

//========= MSI_MSJT_CreateSelectRow  ============= PR2020--09-30
    function MSI_MSJT_CreateSelectRow(tblName, tblBody_select, pk_int, map_dict, sjtp_pk, justclicked_pk) {
        //console.log("===== MSI_MSJT_CreateSelectRow ===== ");
        //console.log("..........pk_int", pk_int);
        //console.log("..........tblName", tblName);
        //console.log("map_dict", map_dict);

        //console.log("justclicked_pk", justclicked_pk);

        if (!isEmpty(map_dict)){
            let subj_code = (map_dict.code) ? map_dict.code : "";
            if(map_dict.is_combi) { subj_code += " *" }
            let display_txt = (map_dict.name) ? map_dict.name : null;
            const sjtp_abbrev = (map_dict.sjtp_abbrev) ? map_dict.sjtp_abbrev : null;

// ---  lookup index where this row must be inserted
            let ob1 = "", row_index = -1;
            if(tblName === "subject"){
                if (map_dict.name) { ob1 = map_dict.name.toLowerCase()};
                row_index = b_recursive_tblRow_lookup(tblBody_select, ob1, "", "", false, setting_dict.user_lang);
            }

            const tblRow = tblBody_select.insertRow(row_index);
            tblRow.setAttribute("data-pk", pk_int);
            if(sjtp_pk){tblRow.setAttribute("data-sjtp_pk", sjtp_pk)};

            //if(dict.mapid) { tblRow.id = "MSI_" + dict.mapid }
            const selected_int = 0
            tblRow.setAttribute("data-selected", selected_int);

// ---  add data-sortby attribute to tblRow, for ordering new rows
            tblRow.setAttribute("data-ob1", ob1);
            //tblRow.setAttribute("data-ob2", ob2);
            //tblRow.setAttribute("data-ob3", ob3);


            if(tblName === "subjecttype"){
                tblRow.classList.add("bg_selected_blue")
            } else {

                //if(highlighted){ ShowClassWithTimeout(tblRow, "bg_selected_blue")};
            }
            if (justclicked_pk && justclicked_pk === pk_int) {
                tblRow.classList.add("bg_medium_blue")
                setTimeout(function (){tblRow.classList.remove("bg_medium_blue")  }, 500);
                setTimeout(function (){tblRow.classList.add("bg_transparent")  }, 500);
            }

            add_hover(tblRow)

    // --- add first td to tblRow.
            let td = tblRow.insertCell(-1);
            let el_div = document.createElement("div");
                el_div.classList.add("tw_020")
                el_div.className = "tickmark_0_0";
                  td.appendChild(el_div);

            tblRow.setAttribute("data-selected", 0)

    // --- add second td to tblRow.
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                //el_div.classList.add("tw_240")
                td.classList.add("tw_100perc")

                el_div.innerText = display_txt;
            td.appendChild(el_div);
    //--------- add addEventListener
            if(tblName === "subject"){
                tblRow.addEventListener("click", function() {MSI_SubjectClicked(tblName, tblRow)}, false);
            } else if(tblName === "subjecttype"){  // used in modal MSI
                tblRow.addEventListener("click", function() {MSI_SubjecttypeClicked(tblRow)}, false);
            } else if(tblName === "schemeitem"){  // used in modal MSI
                tblRow.addEventListener("click", function() {MSI_SchemeitemClicked(tblRow)}, false);
            } else if(tblName === "subjecttypebase"){  // used in modal MSJT
                tblRow.addEventListener("click", function() {MSJT_SubjecttypebaseClicked(tblRow)}, false);
            } else if(tblName === "sjtp"){  // used in modal MSJT
                tblRow.addEventListener("click", function() {MSJT_SjtpClicked(tblRow)}, false);
            }
        }
    } // MSI_MSJT_CreateSelectRow

//========= MSI_SubjectClicked  ============= PR2020-10-01 PR2021-03-05 PR2021-06-24
    function MSI_SubjectClicked(tblName, tblRow){
        //console.log( "===== MSI_SubjectClicked  ========= ");
        //console.log( "tblName", tblName);

        if(tblRow){

// ---  toggle is_selected
            let is_selected = (!!get_attr_from_el_int(tblRow, "data-selected"));
            is_selected = !is_selected;
            tblRow.setAttribute("data-selected", ( (is_selected) ? 1 : 0) )

// ---  show/hide blue color
            add_or_remove_class(tblRow, "bg_medium_blue", is_selected )  // was bg_selected_blue
// ---  show/hide tickmark
            const img_class = (is_selected) ? "tickmark_0_2" : "tickmark_0_0"
            const el = tblRow.cells[0].children[0];
            if (el){el.className = img_class}
        }
    }  // MSI_SubjectClicked

    function MSI_SetInputFields(schemitem_pk, is_selected){
// ---  put value in input box 'Characteristics of this subject
        //console.log( "===== MSI_SetInputFields  ========= ");
        //console.log( "schemitem_pk", schemitem_pk);
        //console.log( "is_selected", is_selected);

        let is_empty = true, is_combi = false,
            is_extra_counts = false, is_extra_nocount = false,
            pwstitle = null, pwssubjects = null,
            extra_count_allowed = false, extra_nocount_allowed = false;

        let sjtp_has_prac = false;

        let map_dict = {};

        if(is_selected && schemitem_pk && mod_MSI_dict.schemeitem_dict[schemitem_pk]){
            map_dict = mod_MSI_dict.schemeitem_dict[schemitem_pk];
            if(!isEmpty(map_dict)){
                is_empty = false;
                is_combi = map_dict.is_combi
                extra_count_allowed = map_dict.extra_count_allowed
                extra_nocount_allowed = map_dict.extra_nocount_allowed
                is_extra_counts = map_dict.is_extra_counts,
                is_extra_nocount = map_dict.is_extra_nocount,
                sjtp_has_prac = map_dict.sjtp_has_prac,
                pwstitle = map_dict.pws_title,
                pwssubjects = map_dict.pws_subjects;

            }
        }

    }  // MSI_SetInputFields

//========= MSI_SubjecttypeClicked  ============= PR2021-06-24
    function MSI_SubjecttypeClicked(tr_clicked) {
        //console.log("  =====  MSI_SubjecttypeClicked  =====");
        //console.log("tr_clicked", tr_clicked);

        const sel_sjtp_pk = get_attr_from_el_int(tr_clicked, "data-pk")
        //console.log("sel_sjtp_pk", sel_sjtp_pk, typeof sel_sjtp_pk);

        // mod_MSI_dict.sjtp_dictlist = [ {id: 200, name: "Gemeenschappelijk deel", si: [200, 245]}, ]

// add selected subjects to this subjecttype

// ---  lookup the dict of this subjecttype in sjtp_dictlist
        let sjtp_dict = null;
        for (let i = 0, dict; dict = mod_MSI_dict.sjtp_dictlist[i]; i++) {
            if (sel_sjtp_pk === dict.sjtp_pk) {
                sjtp_dict = dict;
            };
        };
        //console.log("sjtp_dict", sjtp_dict);

// ---  loop through tblBody with subjects and add selected subject_pk's to subjecttype list
        const tblBody = el_tblBody_subjects;
        for (let i = 0, tblRow, is_selected, sel_subj_pk_int; tblRow = tblBody.rows[i]; i++) {
            is_selected = !!get_attr_from_el_int(tblRow, "data-selected")
            if (is_selected) {
        //console.log("tblRow", tblRow);
                sel_subj_pk_int = get_attr_from_el_int(tblRow, "data-pk")
        //console.log("sel_subj_pk_int", sel_subj_pk_int);

                const justclicked_subj_pk = sel_subj_pk_int;
                MSI_AddSubjectToSubjecttype(sel_subj_pk_int, sjtp_dict, justclicked_subj_pk)
            }

// ---  remove data-selected from this tblRow, show/hide tickmark PR2020-11-21
            tblRow.setAttribute("data-selected", 0);
            tblRow.classList.remove("bg_medium_blue");
            const el = tblRow.cells[0].children[0];
            if (el){el.className = "tickmark_0_0"}
        }
        //console.log("===========mod_MSI_dict", mod_MSI_dict);

        //MSI_FillTblSubjects();
        MSI_FillTblSchemeitems();
    }  // MSI_SubjecttypeClicked

//========= MSI_AddSubjectToSubjecttype  ============= PR2021-06-24
    function MSI_AddSubjectToSubjecttype(subj_pk_int, sjtp_dict, justclicked_subj_pk) {
        //console.log("  =====  MSI_AddSubjectToSubjecttype  =====");
        //console.log("subj_pk_int", subj_pk_int);
        //console.log("sjtp_dict", sjtp_dict);
        //console.log("justclicked_subj_pk", justclicked_subj_pk);

// get subject_dict
        // subject_dict = {id: 759, name: "Franse taal}
        const subject_dict = (mod_MSI_dict.subject_dict[subj_pk_int]) ? mod_MSI_dict.subject_dict[subj_pk_int] : {};
        //console.log("subject_dict", subject_dict);

// ---  check if subject_pk already exists in sjtp_dict.si_list list
        let si_dict = null, found = false;
        for (let j = 0, dict; dict = sjtp_dict.si_list[j]; j++) {
            if (dict && dict.subj_pk === subj_pk_int){
                found = true
            // if subject has tag 'isdeleted': undelete it.
                if(dict.isdeleted) {
                    dict.isdeleted = false
                };
                break;
            };
        };
        //console.log("found", found);

        if (!found){
        // add subject to list if it is not in the list yet
              const si_dict = {
                  si_pk: null,
                  subj_pk: subj_pk_int,
                  sjtp_pk: sjtp_dict.sjtp_pk,
                  name: subject_dict.name,
                  iscreated: true
              };
              sjtp_dict.si_list.push(si_dict)
        }
        //console.log("sjtp_dict.si_list", sjtp_dict.si_list);

    }  // MSI_AddSubjectToSubjecttype

//========= MSI_SchemeitemClicked  ============= PR2021-06-24
    function MSI_SchemeitemClicked(tr_clicked) {
        //console.log("  =====  MSI_SchemeitemClicked  =====");
        const tblBody = el_tblBody_schemeitems;
        const sel_schemeitem_pk_list = []

        let map_dict = {};
        const subj_pk_int = get_attr_from_el_int(tr_clicked, "data-pk")
        const sjtp_pk_int = get_attr_from_el_int(tr_clicked, "data-sjtp_pk")

        //console.log("tr_clicked", tr_clicked);
        //console.log("subj_pk_int", subj_pk_int);
        //console.log("sjtp_pk_int", sjtp_pk_int);
        //console.log("mod_MSI_dict", mod_MSI_dict);

// lookup sjtp_dict in mod_MSI_dict.sjtp_dictlist
        const sjtp_dict = b_lookup_dict_in_dictlist(mod_MSI_dict.sjtp_dictlist, "sjtp_pk", sjtp_pk_int)
        //console.log("sjtp_dict", sjtp_dict);
        if(sjtp_dict){

// lookup si_dict in sjtp_dict.si_list
            const si_list = sjtp_dict.si_list;
            //console.log("si_list", si_list);
            const [index, si_dict] = b_lookup_dict_with_index_in_dictlist(si_list, "subj_pk", subj_pk_int)
            //console.log("index", index);
            //console.log("si_dict", si_dict);
            // si_dict = {si_pk: null, sjtp_pk: 202, subj_pk: 759 ,name: "Franse taal", iscreated: true }
            if (si_dict){
// ---  check if schemeitem_pk already exists in mod_MSI_dict.schemeitem_dict
                if(si_dict.iscreated){
                // delete when si is created (is not saved yet)
                    // splice(start, deleteCount, item1, item2, itemN)
                    si_list.splice(index, 1)
                } else {
                // set deleted=true when it is a saved si
                    si_dict.isdeleted = true;
                }
            }
        }
        const justclicked_pk = subj_pk_int;
        MSI_FillTblSchemeitems(sel_schemeitem_pk_list, justclicked_pk)

    }  // MSI_SchemeitemClicked

//========= MSI_AddPackage  ============= PR2020-11-18
    function MSI_AddPackage() {
        //console.log("  =====  MSI_AddPackage  =====");

    }  // MSI_AddPackage

// +++++++++ END MOD SCHEMEITEM ++++++++++++++++++++++++++++++++++++++++++++++++++++

// ++++++++ MODAL OTHER LANG ++++++++++++++++++++++++++++++++++

    function MOL_Open(el_input){
        console.log(" -----  MOL_Open   ----")
        console.log("el_input", el_input)
        //console.log("permit_dict", permit_dict)

        if (permit_dict.permit_crud){

            mod_MSI_dict = {el_input: el_input};

            if (el_input){
                const tblRow = get_tablerow_selected(el_input);
                const data_dict = get_recursive_integer_lookup(tblRow);
                if(!isEmpty(data_dict)) {
                    mod_MSI_dict.schemeitem_pk = data_dict.id;
                    mod_MSI_dict.mapid = data_dict.mapid;
                    mod_MSI_dict.scheme_name = data_dict.scheme_name;
                    mod_MSI_dict.scheme_pk = data_dict.scheme_id;
                    mod_MSI_dict.subj_pk = data_dict.subj_id;
                    mod_MSI_dict.subj_name = data_dict.subj_name;
                    mod_MSI_dict.otherlang = (data_dict.otherlang) ? data_dict.otherlang : "none";
                }  // if(!isEmpty(map_dict)) {

    // ---  set header text
                el_MOL_header.innerText = [(mod_MSI_dict.scheme_name) ? mod_MSI_dict.scheme_name : "",
                                            (mod_MSI_dict.subj_name) ? mod_MSI_dict.subj_name : ""].join("\n");
    // ---  set select box otherlang
                el_MOL_otherlang.value = mod_MSI_dict.otherlang
    // ---  disable btn save
                el_MOL_btn_save.disabled = true;
    // ---  show modal
                $("#id_mod_otherlang").modal({backdrop: true});
            };
        }  //  if (permit_dict.permit_crud){
    };  // MOL_Open

//========= MOL_Save  ============= PR2021-10-11
    function MOL_Save() {
        console.log( " ==== MOL_Save ====");
        if (setting_dict.sel_examyear_locked){
            const msg_html = loc.This_examyear + loc.is_locked + "<br>" + loc.You_cannot_make_changes
            b_ShowModMessages([{class: "border_bg_warning", msg_html: msg_html}]);
        } else {

            const fldName = "otherlang"
            let new_value = (!el_MOL_otherlang.value || el_MOL_otherlang.value === "none") ? null : el_MOL_otherlang.value;
            const update_dict = {otherlang: new_value};
            UpdateField(mod_MSI_dict.el_input, update_dict)

        console.log("mod_MSI_dict", mod_MSI_dict)
// ---  upload changes
            const upload_dict = {
                mode: "update",
                table: "schemeitem",
                mapid:  (mod_MSI_dict.mapid) ? mod_MSI_dict.mapid : null,
                si_pk: (mod_MSI_dict.schemeitem_pk) ? mod_MSI_dict.schemeitem_pk : null,
                subject_pk: (mod_MSI_dict.subj_pk) ? mod_MSI_dict.subj_pk : null,
                scheme_pk: (mod_MSI_dict.scheme_pk) ? mod_MSI_dict.scheme_pk : null,
                otherlang: new_value
            };
            const url_str = get_url_str();
            UploadChanges(upload_dict, url_str);
        };

            // ---  show modal
        $("#id_mod_otherlang").modal("hide");
    }  // MOL_Save

//========= MOL_InputChange  ============= PR2021-10-11
    function MOL_InputChange(el_input){
        //console.log( "===== MOL_InputChange  ========= ");
         mod_MSI_dict.otherlang = el_input.value;
         el_MOL_btn_save.disabled = false

    }; // MOL_InputChange

// ++++++++ END OF MODAL OTHER LANG ++++++++++++++++++++++++++++++++++


// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2020-08-03
    function ModConfirmOpen(tblName, mode) {
        console.log(" -----  ModConfirmOpen   ----")
        // values of mode are : "delete", "copy_scheme"
        console.log("mode", mode)

        if(permit_dict.permit_crud){
            el_confirm_msg_container.innerHTML = null;

    // ---  get selected_pk
            let selected_pk = null;
            let map_dict = {};

            if(tblName === "subject"){
                map_dict = selected.subject_dict;
            } else if(tblName === "schemeitem"){
                map_dict = selected.schemeitem_dict;
            } else if(tblName === "subjecttype"){
                map_dict = selected.subjecttype_dict;
            } else if(tblName === "subjecttypebase"){
                map_dict = selected.subjecttypebase_dict;
            } else if(tblName === "examyear"){
                map_dict =selected.copyto_examyear_dict;
            };

    // ---  get info from data_map or data_rows
            console.log("map_dict", map_dict)

    // ---  create mod_dict
            mod_dict = {mode: mode, table: tblName};
            const has_selected_item = (!isEmpty(map_dict));
            if(has_selected_item){
                mod_dict.mapid = map_dict.mapid;
                if (tblName === "examyear"){
                    mod_dict.copyto_mapid = map_dict.mapid;
                    mod_dict.copyto_examyear_id = map_dict.examyear_id;
                    mod_dict.copyto_country_id = map_dict.country_id;
                    mod_dict.copyto_examyear_code = map_dict.examyear_code;
                    mod_dict.copyto_country = map_dict.country;
                } else {
                    mod_dict.id = map_dict.id;
                    mod_dict.mapid = map_dict.mapid;
                    mod_dict.scheme_pk = map_dict.scheme_id;
                    mod_dict.abbrev = map_dict.abbrev;
                    mod_dict.name = map_dict.name;
                    mod_dict.sequence = map_dict.sequence;
                    mod_dict.depbases = map_dict.depbases;
                };
            };
            if (mode === "inactive") {
                mod_dict.current_isactive = map_dict.is_active;
            }
            console.log("mod_dict", mod_dict)
            console.log("has_selected_item", has_selected_item)

    // ---  put text in modal form
            let dont_show_modal = false;

            let header_text = (tblName === "subject") ? loc.Delete_subject :
                           (tblName === "subjecttype") ? loc.Delete_character :
                           (tblName === "subjecttypebase") ? loc.Delete_characterbase :
                           (tblName === "scheme") ? loc.Delete_scheme :
                           (tblName === "package") ? loc.Delete_package : "";

            const item = (tblName === "subject") ? loc.Subject :
                           (tblName === "subjecttype") ? loc.Character :
                           (tblName === "subjecttypebase") ? loc.Characterbase :
                           (tblName === "scheme") ? loc.Scheme :
                           (tblName === "package") ? loc.Package : "";

            let msg01_txt = null, msg02_txt = null, msg03_txt = null;
            let hide_save_btn = false;
            if(!has_selected_item){
                msg01_txt = loc.There_is_no__ + item.toLowerCase() + loc.__selected;
                hide_save_btn = true;
            } else {
                let item_name = (tblName === "subject") ? mod_dict.name :
                           (tblName === "subjecttype") ? mod_dict.name :
                           (tblName === "subjecttypebase") ? mod_dict.name :
                           (tblName === "scheme") ? mod_dict.name :
                           (tblName === "package") ? mod_dict.name : "";

            //console.log("item_name", item_name)
                msg01_txt = item + " '" + item_name + "'" + loc.will_be_deleted;
                msg02_txt = loc.Do_you_want_to_continue;

            }
            if(!dont_show_modal){
                el_confirm_header.innerText = header_text;
                el_confirm_loader.classList.add(cls_visible_hide)

                el_confirm_msg_container.className = "p-3";
                let msg_html = "";
                if (msg01_txt) {msg_html += "<p>" + msg01_txt + "</p>"};
                if (msg02_txt) {msg_html += "<p>" + msg02_txt + "</p>"};
                if (msg03_txt) {msg_html += "<p>" + msg03_txt + "</p>"};
                el_confirm_msg_container.innerHTML = msg_html

                const caption_save = (mode === "delete") ? loc.Yes_delete :
                                (mode === "inactive") ? ( (mod_dict.current_isactive) ? loc.Yes_make_inactive : loc.Yes_make_active ) :
                                loc.OK;
                el_confirm_btn_save.innerText = caption_save;
                add_or_remove_class (el_confirm_btn_save, cls_hide, hide_save_btn);

                add_or_remove_class (el_confirm_btn_save, "btn-primary", (mode !== "delete"));
                add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", (mode === "delete"));

        // set focus to cancel button
                setTimeout(function (){
                    el_confirm_btn_cancel.focus();
                }, 500);
    // show modal
                $("#id_mod_confirm").modal({backdrop: true});
            }
        }
    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2019-06-23
    function ModConfirmSave() {
        //console.log(" --- ModConfirmSave --- ");
        //console.log("mod_dict: ", mod_dict);

        let close_modal = true  // !permit_dict.permit_crud;
        if(mod_dict.mode === "copy_scheme") {

        } else if(permit_dict.permit_crud){
            let tblRow = document.getElementById(mod_dict.mapid);

    // ---  when delete: make tblRow red, before uploading
            if (tblRow && mod_dict.mode === "delete"){
                ShowClassWithTimeout(tblRow, "tsa_tr_error");
            }
            if(mod_dict.mode === "delete") {
    // show loader in mod confirm
                el_confirm_loader.classList.remove(cls_visible_hide)
            }

    // ---  Upload Changes
            let upload_dict = { table: mod_dict.table,
                                mapid: mod_dict.mapid};
            if(mod_dict.mode === "delete") {
                // TODO change to moede = delete
                upload_dict.delete = true;
                // this one is used in table 'SUbject'
                upload_dict.mode = mod_dict.mode;
            }
            if (selected_btn === "btn_subject"){
                upload_dict.subject_pk = mod_dict.id;
            } else if (selected_btn === "btn_subjecttype"){
                upload_dict.scheme_pk = mod_dict.scheme_pk;
                upload_dict.subjecttype_pk = mod_dict.id;
            } else if (selected_btn === "btn_subjecttypebase"){
                upload_dict.sjtbase_pk = mod_dict.id;
            }

            const url_str = get_url_str();
            UploadChanges(upload_dict, url_str);
        };
// ---  hide modal
        if(close_modal) {
            $("#id_mod_confirm").modal("hide");
        }
    }  // ModConfirmSave

//=========  ModConfirmResponse  ================ PR2019-06-23 PR2020-10-29
    function ModConfirmResponse(updated_row) {
        //console.log(" --- ModConfirmResponse --- ");
        //console.log("updated_row: ", updated_row);

//--- hide loader
        el_confirm_loader.classList.add(cls_visible_hide)
        let show_msg = false, msg01_txt = null, msg02_txt = null, msg03_txt = null;

        const mode = get_dict_value(updated_row, ["mode"])
        if ("err_delete" in updated_row) {
            show_msg = true;
            msg01_txt  = get_dict_value(updated_row, ["err_delete"]);
            el_confirm_msg_container.classList.add("border_bg_invalid");
        } else if ("msg_err" in updated_row ||"msg_ok" in updated_row) {
            show_msg = true;
            if ("msg_err" in updated_row) {
                msg01_txt = get_dict_value(updated_row, ["msg_err", "msg01"], "");
                el_confirm_msg_container.classList.add("border_bg_invalid");
            } else if ("msg_ok" in updated_row){
                msg01_txt  = get_dict_value(updated_row, ["msg_ok", "msg01"]);
                msg02_txt = get_dict_value(updated_row, ["msg_ok", "msg02"]);
                msg03_txt = get_dict_value(updated_row, ["msg_ok", "msg03"]);
                el_confirm_msg_container.classList.add("border_bg_valid");
            }
        }
        if (show_msg){
            el_confirm_msg_container.className = "p-3";
            let msg_html = "";
            if (msg01_txt) {msg_html += "<p>" + msg01_txt + "</p>"};
            if (msg02_txt) {msg_html += "<p>" + msg02_txt + "</p>"};
            if (msg03_txt) {msg_html += "<p>" + msg03_txt + "</p>"};
            el_confirm_msg_container.innerHTML = msg_html;

            el_confirm_btn_cancel.innerText = loc.Close
            el_confirm_btn_save.classList.add(cls_hide);
        } else {
        // hide mod_confirm when no message
            $("#id_mod_confirm").modal("hide");
        }
    }  // ModConfirmResponse


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


// +++++++++++++++++ MODAL SELECT EXAMYEAR, SCHOOL OR DEPARTMENT ++++++++++++++++++++
//=========  ModSelSchOrDep_Open  ================ PR2020-10-27 PR2020-11-17
    function ModSelSchOrDep_Open(tblName) {
        //console.log( "===== ModSelSchOrDep_Open ========= ");
        //PR2020-10-28 debug: modal gives 'NaN' and 'undefined' when  loc not back from server yet
        if (!isEmpty(loc)) {
            mod_dict = {base_id: setting_dict.requsr_schoolbase_pk, table: tblName};

// ---  fill select table
            ModSelSchOrDep_FillSelectTable(tblName, 0);  // 0 = selected_pk
// ---  show modal
            $("#id_mod_select_examyear_or_depbase").modal({backdrop: true});
            }
    }  // ModSelSchOrDep_Open

//=========  ModSelSchOrDep_Save  ================ PR2020-10-28
    function ModSelSchOrDep_Save(tblName) {
        //console.log("===  ModSelSchOrDep_Save =========");
        //console.log("mod_dict", mod_dict);

// ---  upload new setting
        let new_setting = {page_subject: {mode: "get"}};
        if (tblName === "school") {
            new_setting.requsr_schoolbase_pk = mod_dict.base_id;
        } else {
            new_setting.requsr_depbase_pk = mod_dict.base_id;
        }
        const datalist_request = {setting: new_setting};
        DatalistDownload(datalist_request);

// hide modal
        $("#id_mod_select_examyear_or_depbase").modal("hide");

    }  // ModSelSchOrDep_Save

//=========  ModSelSchOrDep_SelectItem  ================ PR2020-10-28
    function ModSelSchOrDep_SelectItem(tblName, tblRow) {
        //console.log( "===== ModSelSchOrDep_SelectItem ========= ");
        //console.log( tblRow);
        // all data attributes are now in tblRow, not in el_select = tblRow.cells[0].children[0];
// ---  get clicked tablerow
        if(tblRow) {
// ---  deselect all highlighted rows
            DeselectHighlightedRows(tblRow, cls_selected)
// ---  highlight clicked row
            tblRow.classList.add(cls_selected)
// ---  get pk from id of select_tblRow
            let data_pk = get_attr_from_el(tblRow, "data-pk", 0)
            if(!Number(data_pk)){
               mod_dict.base_id = 0;
            } else {
                mod_dict.base_id = Number(data_pk)
            }
            ModSelSchOrDep_Save(tblName)
        }
    }  // ModSelSchOrDep_SelectItem

//=========  ModSelSchOrDep_FillSelectTable  ================ PR2020-08-21
    function ModSelSchOrDep_FillSelectTable(tblName, selected_pk) {
        //console.log( "===== ModSelSchOrDep_FillSelectTable ========= ");

        const header_text = (tblName === "school") ? loc.Select_school :  loc.Select_department ;
        document.getElementById("id_MSED_header_text").innerText = header_text;

        const caption_none = (tblName === "school") ? loc.No_schools :  loc.No_departments ;
        const tblBody_select = el_ModSelSchOrDep_tblBody_select;
        tblBody_select.innerText = null;

        let row_count = 0, add_to_list = false;
// --- loop through data_map
        const data_map = (tblName === "school") ? school_map : department_map ;
        if(data_map){
            for (const [map_id, map_dict] of data_map.entries()) {
                add_to_list = ModSelSchOrDep_FillSelectRow(map_dict, tblBody_select, tblName, -1, selected_pk);
                if(add_to_list){ row_count += 1};
            };
        }  // if(!!data_map)

        if(!row_count){
            let tblRow = tblBody_select.insertRow(-1);
            let td = tblRow.insertCell(-1);
            td.innerText = caption_none;

        } else if(row_count === 1){
            let tblRow = tblBody_select.rows[0]
            if(tblRow) {
// ---  highlight first row
                tblRow.classList.add(cls_selected)
                if(tblName === "order") {
                    selected_period.order_pk = get_attr_from_el_int(tblRow, "data-pk");
                    MSE_SelectEmployee(tblName, tblRow)
                }
            }
        }
    }  // ModSelSchOrDep_FillSelectTable

//=========  ModSelSchOrDep_FillSelectRow  ================ PR2020-10-27
    function ModSelSchOrDep_FillSelectRow(map_dict, tblBody_select, tblName, row_index, selected_pk) {
        //console.log( "===== ModSelSchOrDep_FillSelectRow ========= ");
        //console.log("tblName: ", tblName);
        //console.log( "map_dict: ", map_dict);

//--- loop through data_map
        let pk_int = null, code_value = null, add_to_list = false, is_selected_pk = false;
        if(tblName === "school") {
            pk_int = map_dict.base_id;
            const code = (map_dict.sb_code) ? map_dict.sb_code : "---";
            const name = (map_dict.name) ? map_dict.name : "---";
            code_value = code + " - " + name;
            const shiftmap_order_pk = map_dict.o_id;
            // PR2020-06-11 debug: no matches because mod_dict.order_pk was str, not number.
            add_to_list = true

       } else if(tblName === "department") {
            pk_int = map_dict.base_id;
            code_value = (map_dict.abbrev) ? map_dict.abbrev : "---"
            add_to_list = true;
       }

       if (add_to_list){
            // selected_pk = 0 means: all customers / orders/ employees
            is_selected_pk = (selected_pk != null && pk_int === selected_pk)
// ---  insert tblRow  //index -1 results in that the new row will be inserted at the last position.
            let tblRow = tblBody_select.insertRow(row_index);
            tblRow.setAttribute("data-pk", pk_int);
            //tblRow.setAttribute("data-ppk", ppk_int);
            tblRow.setAttribute("data-value", code_value);
// ---  add EventListener to tblRow
            tblRow.addEventListener("click", function() {ModSelSchOrDep_SelectItem(tblName, tblRow)}, false )
// ---  add hover to tblRow
            add_hover(tblRow);
// ---  highlight clicked row
            //if (is_selected_pk){ tblRow.classList.add(cls_selected)}
// ---  add first td to tblRow.
            let td = tblRow.insertCell(-1);
// --- add a element to td., necessary to get same structure as item_table, used for filtering
            let el_div = document.createElement("div");
                el_div.innerText = code_value;
                el_div.classList.add("tw_420", "px-2", "pointer_show" )
            td.appendChild(el_div);
        };
        return add_to_list;
    }  // ModSelSchOrDep_FillSelectRow

//========= get_url_str  ========  PR2021-09-08
    function get_url_str() {
        const url_str = (selected_btn === "btn_subject") ? urls.url_subject_upload :
                (selected_btn === "btn_scheme") ? urls.url_scheme_upload :
                (selected_btn === "btn_schemeitem") ? urls.url_schemeitem_upload :
                (selected_btn === "btn_subjecttype") ? urls.url_subjecttype_upload :
                (selected_btn === "btn_subjecttypebase") ? urls.url_subjecttypebase_upload : null;
        return url_str;
    };  // get_url_str

//========= get_recursive_integer_lookup  ========  PR2021-09-08
    function get_recursive_integer_lookup(tblRow) {
        //console.log( "===== get_recursive_integer_lookup ========= ");
        // PR2021-09-08 debug: don't use b_get_mapdict_from_datarows with field 'mapid'.
        // It doesn't lookup mapid correctly: school_rows is sorted by id, therefore school_100 comes after school_99
        // instead b_recursive_integer_lookup with field 'id'.

// ---  lookup data_dict in data_rows, search by id
        const pk_int = get_attr_from_el_int(tblRow, "data-pk");
        const data_rows = (selected_btn === "btn_subject") ? subject_rows :
                            (selected_btn === "btn_scheme") ? scheme_rows :
                            (selected_btn === "btn_schemeitem") ? schemeitem_rows :
                            (selected_btn === "btn_subjecttype") ? subjecttype_rows :
                            (selected_btn === "btn_subjecttypebase") ? subjecttypebase_rows : null;
        const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);

        return found_dict;
    };  // get_recursive_integer_lookup


//========= get_datarows_from_selBtn  ======== // PR2021-06-22
    function get_datarows_from_selBtn() {
        const data_rows = (selected_btn === "btn_subject") ? subject_rows :
                        (selected_btn === "btn_scheme") ? scheme_rows :
                        (selected_btn === "btn_schemeitem") ? schemeitem_rows :
                        (selected_btn === "btn_subjecttype") ? subjecttype_rows :
                        (selected_btn === "btn_subjecttypebase") ? subjecttypebase_rows :
                        (selected_btn === "btn_package") ? packageitem_map  : null;
        return data_rows;
    }

//========= get_datamap_from_selBtn  ======== // PR2020-09-30
    function get_datamap_from_selBtn() {
        const data_map = (selected_btn === "btn_subject") ? subject_map :
                        (selected_btn === "btn_schemeitem") ? schemeitem_map :
                        (selected_btn === "btn_package") ? packageitem_map  : null;
        return data_map;
    }
//========= get_tblName_from_selectedBtn  ======== // PR2021-06-29
    function get_tblName_from_selectedBtn() {
        return (selected_btn) ? selected_btn.substring(4) : null;
    }


})  // document.addEventListener('DOMContentLoaded', function()