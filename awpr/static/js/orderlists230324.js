// PR2020-09-29 added

let envelopsubject_rows = []; // PR2022-10-09

// envelopbundle_rows is made global to show in t_MSSSS_Save
let envelopbundle_rows = [];
//let subject_rows = [];

document.addEventListener('DOMContentLoaded', function() {
    "use strict";

// ---  check if user has permit to view this page. If not: el_loader does not exist PR2020-10-02
    let el_loader = document.getElementById("id_loader");
    const may_view_page = (!!el_loader)

    let mod_dict = {};
    let mod_MPUBORD_dict = {};
    let mod_MENV_dict = {};

// mod_MSTUDSUBJ_dict stores available studsubj for selected candidate in MSTUDSUBJ
    //let mod_MSTUDSUBJ_dict = {
    //    schemeitem_dict: {}, // stores available studsubj for selected candidate in MSTUDSUBJ
    //    studentsubject_dict: {}  // stores studsubj of selected candidate in MSTUDSUBJ
    //};

    let user_list = [];
    let examyear_map = new Map();
    let school_map = new Map();

    //let level_rows = [];

    //let ete_exam_rows = [];
    let orderlist_rows = [];
    // envelopbundle_rows is made global to show in t_MSSSS_Save
    //let envelopbundle_rows = [];
    let enveloplabel_rows = [];
    let envelopitem_rows = [];
    let enveloplabelitem_rows = [];
    let envelopbundlelabel_rows = [];
    let enveloporderlist_rows = []; //PR2023-03-02 added

    //let filter_dict = {};
    let filter_mod_employee = false;

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    urls.url_usersetting_upload = get_attr_from_el(el_data, "data-url_usersetting_upload");
    urls.url_orderlist_download = get_attr_from_el(el_data, "data-orderlist_download_url");
    urls.orderlist_per_school_download_url = get_attr_from_el(el_data, "data-orderlist_per_school_download_url");
    urls.url_orderlist_parameters = get_attr_from_el(el_data, "data-url_orderlist_parameters");
    urls.url_orderlist_request_verifcode = get_attr_from_el(el_data, "data-url_orderlist_request_verifcode");
    urls.url_orderlist_publish = get_attr_from_el(el_data, "data-url_orderlist_publish");

    urls.url_envelopsubject_upload = get_attr_from_el(el_data, "data-url_envelopsubject_upload");
    urls.url_envelopbundle_upload = get_attr_from_el(el_data, "data-url_envelopbundle_upload");
    urls.url_enveloplabel_upload = get_attr_from_el(el_data, "data-url_enveloplabel_upload");
    urls.url_envelopitem_upload = get_attr_from_el(el_data, "data-url_envelopitem_upload");

    urls.url_envelop_print_check = get_attr_from_el(el_data, "data-url_envelop_print_check");
    urls.url_envelop_print = get_attr_from_el(el_data, "data-url_envelop_print");
    urls.url_envelop_receipt = get_attr_from_el(el_data, "data-url_envelop_receipt");
    urls.url_exam_upload = get_attr_from_el(el_data, "data-url_exam_upload");

    mod_MCOL_dict.columns.btn_orderlist = {
        school_abbrev: "School_name", total_students: "Number_of_candidates",
        total: "Number_of_entered_subjects", publ_count: "Number_of_submitted_subjects", datepublished: "Date_submitted"
    };
    mod_MCOL_dict.columns.btn_envelopsubject = {
        subj_name_nl : "Subject",
        examperiod : "Exam_period",
        depbase_code: "Department",
        lvl_abbrev: "Learning_path",
        firstdate : "Date",
        lastdate : "Thru_date",
        starttime : "Start_time",
        endtime : "End_time",
        has_errata: "Has_errata"
    };
    mod_MCOL_dict.columns.btn_enveloplabel = {
        is_variablenumber: "Variable_number_envelops",
        numberinenvelop: "Number_of_envelops",
        numberofenvelops: "Items_per_envelop",
        is_errata: "Is_errata_label"
    };

// --- get field_settings
    const field_settings = {
        orderlist: {field_caption: ["", "School_code", "School_name", "Number_of_candidates",
                                 "Number_of_entered_subjects", "Number_of_submitted_subjects", "Date_submitted", "Download_Exform"],
                    field_names: ["", "schbase_code", "school_abbrev", "total_students",
                                 "total", "publ_count", "datepublished", "url"],
                    field_tags: ["div", "div", "div",
                                 "div", "div","div", "div", "a"],
                    filter_tags: ["select", "text", "text",
                                  "number", "number", "number", "text", "text"],
                    field_width:  ["020", "090", "180",
                                   "120", "120", "120", "150", "120"],
                    field_align: ["c", "l", "l",
                                    "r", "r", "r", "l", "c"]
                     },
        envelopsubject: { field_caption: ["", "Abbrev_subject_2lines", "Subject", "Department", "Learning_path", "Exam_period",
                                "Date", "Thru_date", "Start_time_Duration", "End_time", "Has_errata", "Label_bundle", ""],
                field_names: ["select", "subjbase_code", "subj_name_nl", "depbase_code", "lvl_abbrev", "examperiod",
                                "firstdate", "lastdate", "starttime", "endtime", "has_errata", "bundle_name", "download"],
                field_tags: ["div", "div", "div", "div", "div", "div",
                                "input", "input", "input", "input", "div", "div", "div"],
                filter_tags: ["text", "text", "text", "text", "text", "text",
                                "text", "text", "text", "text", "toggle", "text", ""],
                field_width: ["020", "075", "240", "120", "120", "150",
                                "150", "150",  "120", "120", "090", "240", "060"],
                field_align: ["c", "c", "l", "c", "c", "c",
                                "l", "l", "l", "l", "c", "l", "c"]
                },

        envelopbundle: {field_caption: ["", "Bundle_name"],
                    field_names: ["select", "name"],
                    field_tags: ["div", "div"],
                    filter_tags: ["", "text"],
                    field_width:  ["020", "240"],
                    field_align: ["c", "l"]
                    },
        enveloplabel: {field_caption: ["", "Label_name", "Variable_number_envelops_2lines", "Number_of_envelops", "Items_per_envelop", "Is_errata_label",],
                    field_names: ["select", "name", "is_variablenumber", "numberofenvelops", "numberinenvelop", "is_errata"],
                    field_tags: ["div", "div", "div", "div", "div", "div"],
                    filter_tags: ["", "text", "text","text", "text","text"],
                    field_width:  ["020", "240", "090", "120", "120", "090"],
                    field_align: ["c", "l", "c",  "c", "c",  "c"]
                     },
        envelopitem: {field_caption: ["", "Content", "Instruction"],
                    field_names: ["select", "content_nl", "instruction_nl"],
                    field_tags: ["div", "div", "div"],
                    filter_tags: ["", "text", "text"],
                    field_width:  ["020", "360", "720"],
                    field_align: ["c", "l", "l"]
                     },
        };

        const tblHead_datatable = document.getElementById("id_tblHead_datatable");
        const tblBody_datatable = document.getElementById("id_tblBody_datatable");

// === EVENT HANDLERS ===
// === reset filter when ckicked on Escape button ===
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") { ResetFilterRows()}
        });

// --- buttons in btn_container
        const el_btn_container = document.getElementById("id_btn_container")
        if (el_btn_container){
            const btns = el_btn_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                const data_btn = get_attr_from_el(btn,"data-btn")
                btn.addEventListener("click", function() {HandleBtnSelect(data_btn)}, false )
            };
        };

// ---  HEADER BAR ------------------------------------
        const el_hdrbar_examyear = document.getElementById("id_hdrbar_examyear");
        if (el_hdrbar_examyear){
            el_hdrbar_examyear.addEventListener("click", function() {
                t_MSED_Open(loc, "examyear", examyear_map, setting_dict, permit_dict, MSED_Response)}, false );
        };
        // there is no btn select department in headerbar of page_orderlist
        // there is no btn select school in headerbar of page_orderlist

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

// ---  SIDEBAR ------------------------------------
        const el_SBR_select_examperiod = document.getElementById("id_SBR_select_period");
        if (el_SBR_select_examperiod){el_SBR_select_examperiod.addEventListener("change", function() {HandleSBRselect("examperiod", el_SBR_select_examperiod)}, false )};

        const el_SBR_select_department = document.getElementById("id_SBR_select_department");
        if (el_SBR_select_department){el_SBR_select_department.addEventListener("change", function() {HandleSBRselect("department", el_SBR_select_department)}, false)};

        const el_SBR_select_level = document.getElementById("id_SBR_select_level");
        if(el_SBR_select_level){el_SBR_select_level.addEventListener("change", function() {HandleSBRselect("level", el_SBR_select_level)}, false )};

        const el_SBR_select_subject = document.getElementById("id_SBR_select_subject");
        if(el_SBR_select_subject){el_SBR_select_subject.addEventListener("click",
                function() {t_MSSSS_Open(loc, "subject", subject_rows, true, false, setting_dict, permit_dict, HandleSbrSubject_Response)}, false)};

        //const el_SBR_select_showall = document.getElementById("id_SBR_select_showall");
        //if(el_SBR_select_showall){el_SBR_select_showall.addEventListener("click", function() {HandleShowAll()}, false)};

        //const el_SBR_item_count = document.getElementById("id_SBR_item_count")

// ---  MSSS MOD SELECT SCHOOL / SUBJECT / STUDENT ------------------------------

        const el_MSSSS_input = document.getElementById("id_MSSSS_input");
        if (el_MSSSS_input){
            el_MSSSS_input.addEventListener("keyup", function(event){
                setTimeout(function() {t_MSSSS_InputKeyup(el_MSSSS_input)}, 50)});
        };
        const el_MSSSS_btn_delete = document.getElementById("id_MSSSS_btn_delete");
        if (el_MSSSS_btn_delete){
            el_MSSSS_btn_delete.addEventListener("click", function() {ModSelEnvBundle_remove_bundle()}, false );
        }

// ---  MOD PUBLISH ORDERLIST ------------------------------------
        const el_MPUBORD_info_container = document.getElementById("id_MPUBORD_info_container");
        const el_MPUBORD_loader = document.getElementById("id_MPUBORD_loader");
        const el_MPUBORD_input_verifcode = document.getElementById("id_MPUBORD_input_verifcode");
        if (el_MPUBORD_input_verifcode){
            el_MPUBORD_input_verifcode.addEventListener("keyup", function() {MPUBORD_InputVerifcode(el_MPUBORD_input_verifcode, event.key)}, false);
            el_MPUBORD_input_verifcode.addEventListener("change", function() {MPUBORD_InputVerifcode(el_MPUBORD_input_verifcode)}, false);
        };

        const el_MPUBORD_send_email = document.getElementById("id_MPUBORD_send_email");

        const el_MPUBORD_btn_save = document.getElementById("id_MPUBORD_btn_save");
        if (el_MPUBORD_btn_save){
            el_MPUBORD_btn_save.addEventListener("click", function() {MPUBORD_Save("save")}, false )
        };
        const el_MPUBORD_btn_cancel = document.getElementById("id_MPUBORD_btn_cancel");

// ---  MODAL ENVELOP LABELS
        const el_MENVLAB_header = document.getElementById("id_MENVLAB_header");

        const el_MENVLAB_label_available = document.getElementById("id_MENVLAB_label_available");
        const el_MENVLAB_label_selected = document.getElementById("id_MENVLAB_label_selected");
        const el_MENVLAB_label_name = document.getElementById("id_MENVLAB_label_name");
        const el_MENVLAB_name_err = document.getElementById("id_MENVLAB_name_err");

        const el_MENVLAB_number_container = document.getElementById("id_MENVLAB_number_container");
        const el_MENVLAB_number_err = document.getElementById("id_MENVLAB_number_err");

        const el_MENVLAB_tblBody_available = document.getElementById("id_MENVLAB_tblBody_available");
        const el_MENVLAB_tblBody_selected = document.getElementById("id_MENVLAB_tblBody_selected");

        const el_MENVLAB_name = document.getElementById("id_MENVLAB_name");
        el_MENVLAB_name.addEventListener("keyup", function() {MENVLAB_InputKeyup(el_MENVLAB_name)}, false);

        const el_MENVLAB_variable_number = document.getElementById("id_MENVLAB_variable_number");
        el_MENVLAB_variable_number.addEventListener("click", function() {MENVLAB_InputToggle(el_MENVLAB_variable_number)}, false);
        const el_MENVLAB_errata = document.getElementById("id_MENVLAB_errata");
        el_MENVLAB_errata.addEventListener("click", function() {MENVLAB_InputToggle(el_MENVLAB_errata)}, false);

        const el_MENVLAB_numberinenvelop_label = document.getElementById("id_MENVLAB_numberinenvelop_label");

        const el_MENVLAB_numberinenvelop = document.getElementById("id_MENVLAB_numberinenvelop");
        el_MENVLAB_numberinenvelop.addEventListener("keyup", function() {MENVLAB_InputKeyup(el_MENVLAB_numberinenvelop)}, false);
        const el_MENVLAB_numberofenvelops = document.getElementById("id_MENVLAB_numberofenvelops");
        el_MENVLAB_numberofenvelops.addEventListener("keyup", function() {MENVLAB_InputKeyup(el_MENVLAB_numberofenvelops)}, false);

        const el_MENVLAB_btn_delete = document.getElementById("id_MENVLAB_btn_delete");
        if(el_MENVLAB_btn_delete){el_MENVLAB_btn_delete.addEventListener("click", function() {ModConfirmOpen("delete_bundle_or_label")}, false)}
        const el_MENVLAB_btn_save = document.getElementById("id_MENVLAB_btn_save");
        if(el_MENVLAB_btn_save){ el_MENVLAB_btn_save.addEventListener("click", function() {MENVLAB_Save("save")}, false)}

// ---  MODAL ENVELOP ITEMS
        const el_MENVIT_hdr = document.getElementById("id_MENVIT_hdr");
        const el_MENVIT_form_controls = document.getElementById("id_MENVIT_form_controls")
        if(el_MENVIT_form_controls){
            const form_elements = el_MENVIT_form_controls.querySelectorAll(".form-control")
            for (let i = 0, el; el = form_elements[i]; i++) {
                if(el.tagName === "INPUT"){
                    el.addEventListener("keyup", function() {MENVIT_InputKeyup(el)}, false )
                } else if(el.tagName === "SELECT"){
                    el.addEventListener("change", function() {MENVIT_InputSelect(el)}, false )
                } else if(el.tagName === "DIV"){
                    el.addEventListener("click", function() {MENVIT_InputToggle(el)}, false );
                };
            };
        };
        const el_MENVIT_msg_modified = document.getElementById("id_MENVIT_msg_modified")
        const el_MENVIT_loader = document.getElementById("id_MENVIT_loader")
        const el_MENVIT_btn_delete = document.getElementById("id_MENVIT_btn_delete");
        if(el_MENVIT_btn_delete){el_MENVIT_btn_delete.addEventListener("click", function() {ModConfirmOpen("delete_envelopitem")}, false)}
        const el_MENVIT_btn_save = document.getElementById("id_MENVIT_btn_save");
        if(el_MENVIT_btn_save){ el_MENVIT_btn_save.addEventListener("click", function() {MENVIT_Save("save")}, false)}

// ---  MOD PRINT ENVELOP LABELS ------------------------------------
        const el_MENVPR_header = document.getElementById("id_MENVPR_header");
        const el_MENVPR_loader = document.getElementById("id_MENVPR_loader");
        const el_MENVPR_select_errata = document.getElementById("id_MENVPR_select_errata");
            el_MENVPR_select_errata.addEventListener("change", function() {MENVPR_SelectHasChanged("errata")}, false )

        const el_MENVPR_select_exam = document.getElementById("id_MENVPR_select_exam");
            el_MENVPR_select_exam.addEventListener("change", function() {MENVPR_SelectHasChanged("exam")}, false )

        const el_MENVPR_layout_option_level = document.getElementById("id_MENVPR_layout_option_level");

        const el_MENVPR_tblBody_school = document.getElementById("id_MENVPR_tblBody_school");
        const el_MENVPR_tblBody_exam = document.getElementById("id_MENVPR_tblBody_exam");

        const el_MENVPR_msg_modified = document.getElementById("id_MENVPR_msg_modified");

        const el_MENVPR_btn_save = document.getElementById("id_MENVPR_btn_save");
        if (el_MENVPR_btn_save){
            el_MENVPR_btn_save.addEventListener("click", function() {MENVPR_Save()}, false )
        }


// ---  MOD PRINT ENVELOP RECEIPT ------------------------------------
        const el_MENVRECEIPT_header = document.getElementById("id_MENVRECEIPT_header");
        const el_MENVRECEIPT_loader = document.getElementById("id_MENVRECEIPT_loader");
        const el_MENVRECEIPT_select_errata = document.getElementById("id_MENVRECEIPT_select_errata");
        const el_MENVRECEIPT_layout_option_level = document.getElementById("id_MENVRECEIPT_layout_option_level");

        const el_MENVRECEIPT_tblBody_school = document.getElementById("id_MENVRECEIPT_tblBody_school");

        const el_MENVRECEIPT_msg_modified = document.getElementById("id_MENVRECEIPT_msg_modified");

        const el_MENVRECEIPT_btn_save = document.getElementById("id_MENVRECEIPT_btn_save");
        if (el_MENVRECEIPT_btn_save){
            el_MENVRECEIPT_btn_save.addEventListener("click", function() {MENVRECEIPT_Save()}, false )
        }

// ---  MOD SELECT COLUMNS  ------------------------------------
        const el_MCOL_btn_save = document.getElementById("id_MCOL_btn_save")
        if(el_MCOL_btn_save){
            el_MCOL_btn_save.addEventListener("click", function() {
                t_MCOL_Save(urls.url_usersetting_upload, HandleBtnSelect)}, false )
        };

// ---  MOD CONFIRM ------------------------------------
        let el_confirm_header = document.getElementById("id_modconfirm_header");
        let el_confirm_loader = document.getElementById("id_modconfirm_loader");
        let el_confirm_msg_container = document.getElementById("id_modconfirm_msg_container")
        let el_confirm_btn_cancel = document.getElementById("id_modconfirm_btn_cancel");
        let el_confirm_btn_save = document.getElementById("id_modconfirm_btn_save");
        if (el_confirm_btn_save){ el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()}) };

// ---  MOD MODAL ORDERLIST EXTRA ------------------------------------
        let el_MOLEX_btn_save = document.getElementById("id_MOLEX_btn_save");
        if (el_MOLEX_btn_save){ el_MOLEX_btn_save.addEventListener("click", function() {MOLEX_Save()}) };

// ---  set selected menu button active
        //SetMenubuttonActive(document.getElementById("id_hdr_users"));
    if(may_view_page){
        // period also returns emplhour_list
        const datalist_request = {
                setting: {page: "page_orderlist"},
                schoolsetting: {setting_key: "import_studsubj"},
                //locale: {page: ["page_studsubj", "page_subject", "page_student", "upload", "page_orderlist"]},
                locale: {page: ["page_orderlist"]},
                examyear_rows: {get: true},
                school_rows: {get: true},
                department_rows: {show_all_deps: true},
                level_rows: {get: true},
                subject_rows: {get: true},

                //ete_exam_rows: {show_all: true},
                orderlist_rows: {get: true},

                envelopsubject_rows: {get: true},
                envelopbundle_rows: {get: true},
                enveloplabel_rows: {get: true},
                envelopitem_rows: {get: true},
                enveloplabelitem_rows: {get: true},
                envelopbundlelabel_rows: {get: true},
                enveloporderlist_rows: {get: true}
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

                let must_create_submenu = false, must_update_headerbar = false;

                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                    must_create_submenu = true;
                };
                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict
                    selected_btn = (setting_dict.sel_btn);

                    selected.examperiod = (setting_dict.sel_examperiod) ? setting_dict.sel_examperiod : 1;
                    selected.depbase_pk = (setting_dict.sel_depbase_pk) ? setting_dict.sel_depbase_pk : null;
                    selected.lvlbase_pk = (setting_dict.sel_lvlbase_pk) ? setting_dict.sel_lvlbase_pk : null;

                    must_update_headerbar = true;

// ---  fill cols_hidden
                    if("cols_hidden" in setting_dict){
                        //  setting_dict.cols_hidden was dict with key 'all' or se_btn, changed to array PR2021-12-14
                        //  skip when setting_dict.cols_hidden is not an array,
                        // will be changed into an array when saving with t_MCOL_Save
                        b_copy_array_noduplicates(setting_dict.cols_hidden, mod_MCOL_dict.cols_hidden);
                    };
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
                if(must_create_submenu){CreateSubmenu()};
                if(must_update_headerbar){
                    b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear);
                    FillOptionsExamperiod();
                };

                if ("examyear_rows" in response) {
                    examyear_rows = response.examyear_rows;
                    b_fill_datamap(examyear_map, response.examyear_rows);
                };
                if ("department_rows" in response) {
                    department_rows = response.department_rows;
                    SBR_FillSelectOptions("department");
                };

                if ("school_rows" in response)  {
                    b_fill_datamap(school_map, response.school_rows)
                };
                if ("level_rows" in response)  {
                    level_rows = response.level_rows;
                    SBR_FillSelectOptions("level");
                };
                if ("subject_rows" in response)  {
                    subject_rows = response.subject_rows;
                };
                //if ("ete_exam_rows" in response) {
               //     ete_exam_rows = response.ete_exam_rows
                //};
                if ("orderlist_rows" in response)  {
                    orderlist_rows = response.orderlist_rows;
                };

                if ("envelopsubject_rows" in response)  {
                    envelopsubject_rows = response.envelopsubject_rows;
                };
                if ("envelopbundle_rows" in response)  {
                    envelopbundle_rows = response.envelopbundle_rows;
                };
                if ("enveloplabel_rows" in response)  {
                    enveloplabel_rows = response.enveloplabel_rows;
                };
                if ("envelopitem_rows" in response)  {
                    envelopitem_rows = response.envelopitem_rows;
                };
                if ("enveloplabelitem_rows" in response)  {
                    enveloplabelitem_rows = response.enveloplabelitem_rows;
                };
                if ("envelopbundlelabel_rows" in response)  {
                    envelopbundlelabel_rows = response.envelopbundlelabel_rows;
                };
                if ("enveloporderlist_rows" in response)  {
                    enveloporderlist_rows = response.enveloporderlist_rows;
                };

                SBR_display_subject();
                HandleBtnSelect(selected_btn, true)  // true = skip_upload
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
        let el_submenu = document.getElementById("id_submenu")
        if(el_submenu){
            AddSubmenuButton(el_submenu, loc.Preliminary_orderlist, function() {ModConfirmOpen("prelim_orderlist")}, ["tab_show", "tab_btn_orderlist"]);
            AddSubmenuButton(el_submenu, loc.Preliminary_orderlist + loc.per_school, function() {ModConfirmOpen("orderlist_per_school")}, ["tab_show", "tab_btn_orderlist"]);

            if (permit_dict.permit_submit_orderlist){
                AddSubmenuButton(el_submenu, loc.Publish_orderlist, function() {MPUBORD_Open()}, ["tab_show", "tab_btn_orderlist"]);
            };
            if (permit_dict.permit_crud){
                AddSubmenuButton(el_submenu, loc.Variables_for_extra_exams, function() {MOLEX_Open()}, ["tab_show", "tab_btn_orderlist"]);

                AddSubmenuButton(el_submenu, loc.New_bundle, function() {MENVLAB_Open("envelopbundle")}, ["tab_show", "tab_btn_bundle"]);
                AddSubmenuButton(el_submenu, loc.Delete_bundle, function() {ModConfirmOpen("delete_envelopbundle")}, ["tab_show", "tab_btn_bundle"]);

                AddSubmenuButton(el_submenu, loc.New_label, function() {MENVLAB_Open("enveloplabel")}, ["tab_show", "tab_btn_label"]);
                AddSubmenuButton(el_submenu, loc.Delete_label, function() {ModConfirmOpen("delete_enveloplabel")}, ["tab_show", "tab_btn_label"]);

                AddSubmenuButton(el_submenu, loc.New_label_item, function() {MENVIT_Open()}, ["tab_show", "tab_btn_item"]);
                AddSubmenuButton(el_submenu, loc.Delete_label_item, function() {ModConfirmOpen("delete_envelopitem")}, ["tab_show", "tab_btn_item"]);

                AddSubmenuButton(el_submenu, loc.Print_labels, function() {MENVPR_Open("label")}, ["tab_show", "tab_btn_envelopsubject"]);
                AddSubmenuButton(el_submenu, loc.Print_receipt, function() {MENVPR_Open("receipt")}, ["tab_show", "tab_btn_envelopsubject"]);
            };
            AddSubmenuButton(el_submenu, loc.Hide_columns, function() {t_MCOL_Open("page_orderlist")}, [], "id_submenu_columns")

            el_submenu.classList.remove(cls_hide);
        };

    };//function CreateSubmenu

//###########################################################################
//=========  HandleBtnSelect  ================ PR2020-09-19 PR2020-11-14 PR2022-08-1
    function HandleBtnSelect(data_btn, skip_upload) {
        //console.log( "===== HandleBtnSelect ========= ", data_btn);

// - to prevent error when not in use button retrieved from saved setting
        if(!["btn_orderlist", "btn_envelopsubject", "btn_bundle", "btn_label", "btn_item"].includes(data_btn)){
            data_btn = "btn_orderlist";
        };

        selected_btn = data_btn
        if(!selected_btn){selected_btn = "btn_orderlist"}

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_orderlist: {sel_btn: selected_btn}};
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);
        };

// ---  highlight selected button
        b_highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  show only the elements that are used in this tab
    //console.log( "selected_btn", selected_btn);
        b_show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

// ---  set sbr select elements, gets examperiod value from usersetting;
        HandleSBRselect();

// ---  fill datatable -- happens in HandleSBRselect
        //FillTblRows();

// --- update header text
        UpdateHeaderText();
    }  // HandleBtnSelect

//=========  HandleTblRowClicked  ================ PR2020-08-03 PR2022-08-04
    function HandleTblRowClicked(tr_clicked) {
        //console.log("=== HandleTblRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

// ---  deselect all highlighted rows, select clicked row
        t_td_selected_toggle(tr_clicked, true);  // select_single = true

// --- get existing data_dict from data_rows
        const pk_int = get_attr_from_el_int(tr_clicked, "data-pk");
        const tblName = get_attr_from_el_int(tr_clicked, "data-table");
        const data_rows = get_datarows_from_selectedbtn();
    //console.log( "pk_int: ", pk_int, typeof pk_int);
    //console.log( "data_rows: ", data_rows, typeof data_rows);

        const [index, data_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);
    //console.log( "data_dict: ", data_dict, typeof data_dict);

        if (selected_btn === "btn_orderlist") {
            selected.envelopitem_pk = (!isEmpty(data_dict)) ? data_dict.id : null;
        } else if (selected_btn === "btn_envelopsubject") {
            selected.envelopsubject_pk = (!isEmpty(data_dict)) ? data_dict.id : null;

        } else if(!["envelopbundle", "enveloplabel", "envelopitem"].includes(tblName)){
            selected.envelop_bundle_label_item_pk = (!isEmpty(data_dict)) ? data_dict.id : null;
        };
    //console.log( "selected: ", selected);
    };  // HandleTblRowClicked

//=========  HandleSBRselect  ================ PR2022-08-16 PR2022-10-21
    function HandleSBRselect(tblName, el_select) {
        console.log("===== HandleSBRselect =====");
    //console.log( "    tblName: ", tblName);
    //console.log( "    selected_btn: ", selected_btn);

        // values of tblName are: examperiod, department, level, undefined
        const selected_pk_int = (el_select && Number(el_select.value)) ? Number(el_select.value) : null;

        // tblName is undefined when called by download, get info from setting_dict
        if (!tblName){
            if(!isEmpty(setting_dict)){
                selected.depbase_pk = setting_dict.sel_depbase_pk;
                selected.lvlbase_pk = setting_dict.sel_lvlbase_pk;
                selected.level_req = setting_dict.sel_dep_level_req;
                selected.subject_pk = setting_dict.sel_subject_pk;
            };

        } else {
            const upload_selected_dict = {};
            // PR2023-03-04 debug: reste selected school, when vsbo school is selected the selected dep will go to vsbo
            setting_dict.sel_schoolbase_pk = null;
            upload_selected_dict.sel_schoolbase_pk = null;

            if (tblName === "examperiod") {
                selected.examperiod = selected_pk_int;
                setting_dict.sel_examperiod = selected_pk_int;

                upload_selected_dict.sel_examperiod = setting_dict.sel_examperiod;

            } else if (tblName === "department") {
                selected.depbase_pk = null;
                selected.level_req = false;
                setting_dict.sel_depbase_pk = null;
                setting_dict.sel_dep_level_req = false;


                let data_dict = null;
                if (selected_pk_int){
                    for (let i = 0, row; row = department_rows[i]; i++) {
                        if(row.base_id === selected_pk_int){
                            data_dict = row;
                            break;
                        };
                    };
                };
                if (isEmpty(data_dict)){
                // PR2022-10-18 use -1 for 'all', to distinguish from null
                    upload_selected_dict.sel_depbase_pk = -1;

                    selected.depbase_pk = null;
                    selected.level_req = false;

                    setting_dict.sel_depbase_pk = null;
                    setting_dict.sel_dep_level_req = false;


                } else {
                    selected.depbase_pk = data_dict.base_id;
                    setting_dict.sel_depbase_pk = data_dict.base_id;
                    selected.level_req = (!!data_dict.lvl_req);
                    setting_dict.sel_dep_level_req = selected.level_req;
                // PR2022-10-18 use -1 for 'all', to distinguish from null
                    upload_selected_dict.sel_depbase_pk = setting_dict.sel_depbase_pk;
                };
            } else if (tblName === "level") {
                selected.lvlbase_pk = null;
                setting_dict.sel_lvlbase_pk = null;

                let data_dict = null;
                if (selected_pk_int){
                    for (let i = 0, row; row = level_rows[i]; i++) {
                        if(row.base_id === selected_pk_int){
                            data_dict = row;
                            break;
                }}};
                if (!isEmpty(data_dict)){
                    selected.lvlbase_pk = data_dict.base_id;
                    setting_dict.sel_lvlbase_pk = data_dict.base_id;
                }
                upload_selected_dict.sel_lvlbase_pk = setting_dict.sel_lvlbase_pk;
            };

    console.log( "    upload_selected_dict: ", upload_selected_dict);
    // ---  upload new setting
            if (!isEmpty(upload_selected_dict)){
                const upload_dict = {selected_pk: upload_selected_dict};
    console.log( "    upload_dict: ", upload_dict);
                b_UploadSettings (upload_dict, urls.url_usersetting_upload);
            };
        };

    // show sbr level only when dep is set to vsbo
        if (!selected.level_req){
            selected.lvlbase_pk =  null;
            setting_dict.sel_lvlbase_pk = null;
            if (el_SBR_select_level){ el_SBR_select_level.value = null};
        };

        const show_sbr_level = selected_btn === "btn_envelopsubject" && selected.level_req;
        add_or_remove_class(el_SBR_select_level.parentNode, cls_hide, !show_sbr_level );

        FillTblRows();
    } ; // HandleSBRselect

//=========  HandleSbrSubject_Response  ================  PR2022-08-12 PR2022-10-10
    function HandleSbrSubject_Response(tblName, selected_dict, selected_pk_int) {
        console.log(" ----- HandleSbrSubject_Response ----")
    //console.log("tblName", tblName)
    //console.log("selected_dict", selected_dict)
    //console.log("selected_pk_int", selected_pk_int)
    //console.log("subject_rows", subject_rows)

        selected.subject_pk = null;

// --- get selected subject
        const [index, data_dict, compare] = b_recursive_integer_lookup(subject_rows, "id", selected_pk_int);
    //console.log( "data_dict: ", data_dict);
    //console.log( "selected: ", selected);
        selected.subject_pk = null;
        setting_dict.sel_subject_pk = null;
        if (!isEmpty(data_dict)){
            selected.subject_pk = data_dict.id;
            setting_dict.sel_subject_pk = selected.subject_pk;
        }
// ---  upload new setting
        const upload_dict = {selected_pk: {sel_subject_pk: selected.subject_pk}};
        b_UploadSettings (upload_dict, urls.url_usersetting_upload);

        FillTblRows();
    };  // HandleSbrSubject_Response


//=========  FillOptionsExamperiod  ================ PR2021-03-08 PR2022-08-16
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


//=========  SBR_FillSelectOptions  ================ PR2021-03-06  PR2021-05-21 PR2022-08-16 PR2022-10-18
    function SBR_FillSelectOptions(tblName) {
        //console.log("=== SBR_FillSelectOptions");
    //console.log("tblName", tblName);
        if(["department", "level"].includes(tblName)){
            const is_dep = (tblName === "department");
            const data_rows = (is_dep) ? department_rows : level_rows;

    //console.log("data_rows", data_rows);
            //const caption_all = "&#60" + ((is_dep) ? loc.All_departments : loc.All_levels) + "&#62";
            const caption_all = "&#60" + loc.All_ + ((is_dep) ? loc.Departments.toLowerCase() : loc.Levels.toLowerCase()) + "&#62";

            let found_in_new_list = false;
            const display_rows = [];
            let count = 0;
            if (data_rows){
                for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
                    display_rows.push({
                        // value is dep_id or lvl_is, not depbase_id / levelbase_id
                        // this is necessary to lookup selected item in data_rows in HandleSBRselect
                        // but base_id will be put in 'selected' variable and sent to server
                        value: data_dict.base_id,
                        caption: (is_dep) ? data_dict.base_code : data_dict.abbrev
                    });
                    count += 1;
                };
            };
            if(count){
                if (count === 1){
                // if only 1 option: make that the selected one
                    if (is_dep){
                        selected.depbase_pk = map_dict.base_id;
                    } else {
                        selected.lvlbase_pk = map_dict.base_id;
                    }
                } else {
                    // add row 'Alle leerwegen' / Alle profielen / Alle sectoren in first row
                    // HTML code "&#60" = "<" HTML code "&#62" = ">";
                    // The unshift() method adds new items to the beginning of an array, and returns the new length.
                    display_rows.unshift({value: null, caption: caption_all})
                };
            };
            const selected_pk = (is_dep) ? selected.depbase_pk : selected.lvlbase_pk;
            const el_SBR_select = (is_dep) ? el_SBR_select_department : el_SBR_select_level;
            t_FillOptionsFromList(el_SBR_select, display_rows, "value", "caption", null, null, selected_pk)

        // show select level
            if (!is_dep){
                // TODO: add_or_remove_class(el_SBR_select_level.parentNode, cls_hide, !count);
            };
        };
    };  // SBR_FillSelectOptions


//=========  HandleShowAll  ================ PR2020-12-17
    function HandleShowAll() {
        //console.log("=== HandleShowAll");

        setting_dict.sel_level_pk = null;
        setting_dict.sel_department_pk = null;

        setting_dict.sel_lvlbase_pk = null;
        setting_dict.sel_lvlbase_code = null;

        setting_dict.sel_subject_pk = null;
        setting_dict.sel_cluster_pk = null;
        setting_dict.sel_student_pk = null;

        setting_dict.sel_exam_pk = null;

    // don't reset sel_examperiod
        //setting_dict.sel_examperiod = 12;
        //if (el_SBR_select_examperiod){
            //el_SBR_select_examperiod.value = "12";
        //};

        if (el_SBR_select_level){
            el_SBR_select_level.value = "null";
        };
        if (el_SBR_select_subject){
            el_SBR_select_subject.value = "null";
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
        //console.log("upload_dict", upload_dict);

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
                envelopsubject_rows: {get: true}
                };

        DatalistDownload(datalist_request);
    }; // HandleShowAll

//========= UpdateHeaderText  ================== PR2020-07-31
    function UpdateHeaderText(){
        //console.log(" --- UpdateHeaderText ---" )
        let header_text = null;
        if(selected_btn === "btn_user"){
            header_text = loc.User_list;
        } else {
            header_text = loc.Permissions;
        }
        //document.getElementById("id_hdr_text").innerText = header_text;
    };   //  UpdateHeaderText

//========= FillTblRows  ==================== PR2021-07-01
    function FillTblRows() {
        console.log( "===== FillTblRows  === ");
        //console.log( "setting_dict", setting_dict);

        const data_rows = get_datarows_from_selectedbtn();
        const tblName = get_tblName_from_selectedbtn();
        const field_setting = field_settings[tblName]

    //console.log( "field_settings", field_settings);
    //console.log( "tblName", tblName);
    //console.log( "data_rows", data_rows);

// ---  get list of hidden columns
        const col_hidden = b_copy_array_to_new_noduplicates(mod_MCOL_dict.cols_hidden);

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

// --- create table header
        CreateTblHeader(field_setting, col_hidden);

// --- create table rows
        if(data_rows && data_rows.length){
            for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
                const show_row = (tblName === "envelopsubject") ? ShowTableRow(data_dict) : true;
                if (show_row){
                    CreateTblRow(tblName, field_setting, col_hidden, data_dict);
                };
            };
        }  // if(data_rows)
    } ; // FillTblRows

//=========  CreateTblHeader  === PR2020-07-31
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

    // - skip columns if in columns_hidden
            if (!col_hidden.includes(field_name)){

    // --- get field_caption from field_setting,
                const field_caption = (loc[field_setting.field_caption[j]]) ? loc[field_setting.field_caption[j]] : field_setting.field_caption[j] ;
                const field_tag = field_setting.field_tags[j];
                const filter_tag = field_setting.filter_tags[j];
                const class_width = "tw_" + field_setting.field_width[j] ;
                const class_align = "ta_" + field_setting.field_align[j];

// ++++++++++ insert columns in header row +++++++++++++++
    // --- add th to tblRow_header
                let th_header = document.createElement("th");
    // --- add div to th, margin not working with th
                    const el_header = document.createElement("div");
                        if (j === 0 ){
// --- add checked image to first column
                           // TODO add multiple selection
                            //AppendChildIcon(el_header, imgsrc_stat00);
                        } else  if (field_name.includes("_status")){
                            // --- add  statud icon.
                            el_header.classList.add("stat_0_4")

                        } else {
// --- add innerText to el_div
                            if(field_caption) {el_header.innerText = field_caption};
                            if(filter_tag === "number"){el_header.classList.add("pr-2")}
                        };
// --- add width, text_align
                        el_header.classList.add(class_width, class_align);
                    th_header.appendChild(el_header)
                tblRow_header.appendChild(th_header);

// ++++++++++ create filter row +++++++++++++++
        // --- add th to tblRow_filter.
                const th_filter = document.createElement("th");
        // --- create element with tag from field_tags
                const filter_field_tag = (["text", "number"].includes(filter_tag)) ? "input" : "div";
                const el_filter = document.createElement(filter_field_tag);

        // --- add data-field Attribute.
                el_filter.setAttribute("data-field", field_name);
                el_filter.setAttribute("data-filtertag", filter_tag);

        // --- add EventListener to el_filter
                if (["text", "number"].includes(filter_tag)) {
                    el_filter.addEventListener("keyup", function(event){HandleFilterKeyup(el_filter, event)});
                    add_hover(th_filter);
                }

        // --- add other attributes
                if (filter_tag === "text") {
                    el_filter.setAttribute("type", "text")
                    el_filter.classList.add("input_text");

                    el_filter.setAttribute("autocomplete", "off");
                    el_filter.setAttribute("ondragstart", "return false;");
                    el_filter.setAttribute("ondrop", "return false;");
                };

// --- add width, text_align
                el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");
                th_filter.appendChild(el_filter);
                tblRow_filter.appendChild(th_filter);
            };  //  if (columns_hidden.inludes(field_name))

        };  // for (let j = 0; j < column_count; j++)
    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09 PR2021-03-15 PR2022-08-04
    function CreateTblRow(tblName, field_setting, col_hidden, data_dict) {
        //console.log("=========  CreateTblRow =========", tblName);
        //console.log("tblName", tblName);
        //console.log("data_dict", data_dict);

        const field_names = field_setting.field_names;
        const field_tags = field_setting.field_tags;
        const filter_tags = field_setting.filter_tags;
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;

// ---  lookup index where this row must be inserted
        const ob1 = (tblName === "orderlist") ? (data_dict.schbase_code) ? data_dict.schbase_code : "" :
                    (tblName === "envelopsubject") ? (data_dict.subjbase_code) ? data_dict.subjbase_code : "" :
                    (tblName === "envelopbundle") ? (data_dict.name) ? data_dict.name : "" :
                    (tblName === "enveloplabel") ? (data_dict.name) ? data_dict.name : "" :
                    (tblName === "envelopitem") ? (data_dict.content_nl) ? data_dict.content_nl : "" : "";

        const ob2 = (tblName === "envelopsubject") ? (data_dict.depbase_code) ? data_dict.depbase_code : "" :
                    (tblName === "envelopitem") ? (data_dict.instruction_nl) ? data_dict.instruction_nl : "" : "";

        const ob3 = (tblName === "envelopsubject") ? (data_dict.lvl_abbrev) ? data_dict.lvl_abbrev : ""  : "";

        const row_index = b_recursive_tblRow_lookup(tblBody_datatable, setting_dict.user_lang, ob1, ob2, ob3);

// --- insert tblRow into tblBody at row_index
        let tblRow = tblBody_datatable.insertRow(row_index);
        if (data_dict.mapid) {tblRow.id = data_dict.mapid};

// --- add data attributes to tblRow
        tblRow.setAttribute("data-table", tblName);
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

// skip columns if in columns_hidden
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

        // --- add width, text_align, right padding in examnumber
                // not necessary: td.classList.add(class_width, class_align);
                el.classList.add(class_width, class_align);

                if(filter_tag === "number"){el.classList.add("pr-3")}
                td.appendChild(el);

        // --- add EventListener to td
                if (["firstdate", "lastdate", "starttime", "endtime"].includes(field_name)){
                    const el_type = (["firstdate", "lastdate"].includes(field_name)) ? "date" : "text";

                    el.setAttribute("type", el_type)
                    el.setAttribute("autocomplete", "off");
                    el.setAttribute("ondragstart", "return false;");
                    el.setAttribute("ondrop", "return false;");
                    el.classList.add("input_text");

                    el.addEventListener("change", function() {UploadInputChange(tblName, el)}, false);
                    //el.addEventListener("keydown", function(event){HandleArrowEvent(el, event)});

                } else if (field_name === "has_errata"){
                    td.addEventListener("click", function() {UploadInputToggle(el)}, false);
                                        td.classList.add("pointer_show");
                    add_hover(td);

                } else if (["content_nl", "instruction_nl"].includes(field_name)){
                    td.addEventListener("click", function() {MENVIT_Open(el)}, false)
                    td.classList.add("pointer_show");
                    add_hover(td);

                } else if (["name", "is_variablenumber", "numberofenvelops", "numberinenvelop", "is_errata"].includes(field_name)){
                    td.addEventListener("click", function() {MENVLAB_Open(tblName, el)}, false)
                    td.classList.add("pointer_show");
                    add_hover(td);

                } else if (field_name === "bundle_name"){
                    td.addEventListener("click", function() {ModSelEnvBundle_Open(td)}, false)
                    td.classList.add("pointer_show");
                    add_hover(td);

                } else if (field_name === "download"){
                    td.addEventListener("click", function() {ModConfirmOpen("download", tblRow)}, false)
                    td.classList.add("pointer_show");
                    add_hover(td);
                } else  if (field_name === "url"){
                    el.innerHTML = "&emsp;&emsp;&emsp;&emsp;&#8681;&emsp;&emsp;&emsp;&emsp;";
                };

// --- put value in field
               UpdateField(el, data_dict)
            }  //  if (columns_hidden[field_name])
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

//=========  UpdateField  ================ PR2020-08-16
    function UpdateField(el_div, data_dict) {
        //console.log("=========  UpdateField =========");
        //console.log("data_dict", data_dict);

        if(el_div){
            const field_name = get_attr_from_el(el_div, "data-field");
            const fld_value = data_dict[field_name];

    //console.log("field_name", field_name);
    //console.log("fld_value", fld_value);
            if(field_name){
                let filter_value = null;

                if (["secret_exam", "has_errata", "is_variablenumber", "is_errata"].includes(field_name)){
                    filter_value = (fld_value) ? "1" : "0";
                    el_div.className = (fld_value) ? "tickmark_1_2" : "tickmark_0_0";

                } else  if (["firstdate", "lastdate", "starttime", "endtime"].includes(field_name)){
                    el_div.value = fld_value;

                } else if (field_name === "url"){
                    if (fld_value){
                        el_div.href = fld_value;
                    } else {
                        el_div.innerHTML = "&emsp;&emsp;&emsp;&emsp;-&emsp;&emsp;&emsp;&emsp;";
                        el_div.title = loc.File_not_found;
                    }

                } else if (field_name === "download"){
                    el_div.innerHTML = (data_dict.envelopbundle_id) ? "&emsp;&#8681;&emsp;" : "&emsp;";

                } else {
                    el_div.innerText = (fld_value) ? fld_value : "\n";
                    if (["content_nl", "instruction_nl"].includes(field_name)){
                        const hex_color = (field_name === "content_nl" && data_dict.content_hexcolor) ?
                                data_dict.content_hexcolor :
                            (field_name === "instruction_nl" && data_dict.instruction_hexcolor) ?
                                data_dict.instruction_hexcolor :
                                "#000000";
                        el_div.style.color = hex_color;

                        el_div.style.fontWeight = ((field_name === "content_nl" && data_dict.content_font && data_dict.content_font.includes("Bold")) ||
                                             (field_name === "instruction_nl" && data_dict.instruction_font && data_dict.instruction_font.includes("Bold")))
                                                ? "bold" : "normal";

                        el_div.style.fontStyle = ((field_name === "content_nl" && data_dict.content_font && data_dict.content_font.includes("Italic")) ||
                                             (field_name === "instruction_nl" && data_dict.instruction_font && data_dict.instruction_font.includes("Italic")))
                                                ? "italic" : "normal";
                    };
            // ---  add attribute filter_value
                    filter_value = (fld_value) ? (typeof fld_value === 'string' || fld_value instanceof String) ?
                                     fld_value.toLowerCase() : fld_value  : null;
                                    //} else if (field_name === "download"){
                };

                add_or_remove_attr (el_div, "data-filter", !!filter_value, filter_value);
            }  // if(field_name)
        }  // if(el_div)
    };  // UpdateField

//###########################################################################
// +++++++++++++++++ UPLOAD CHANGES +++++++++++++++++ PR2022-08-13
    function UploadInputChange(tblName, el_input) {
        console.log( " ==== UploadInputChange ====");
        console.log("el_input: ", el_input);

// ---  upload changes
        if (permit_dict.permit_crud){
            const tblRow = t_get_tablerow_selected(el_input);
            if(tblRow){

    // --- get selected ete_exam
                const pk_int = get_attr_from_el_int(tblRow, "data-pk");
                selected.envelopsubject_pk = pk_int
                const [index, data_dict, compare] = b_recursive_integer_lookup(envelopsubject_rows, "id", pk_int);
            console.log("data_dict: ", data_dict);

                if (data_dict){

                const data_field = get_attr_from_el(el_input, "data-field");
        //console.log("data_field: ", data_field, typeof data_field);
    // --- get new_value
                    const new_value = el_input.value
        //console.log("new_value: ", new_value, typeof new_value);

                    let upload_dict = {
                        table: "envelopsubject",
                        mode: "update",
                        examyear_pk: data_dict.subj_examyear_id,
                        envelopsubject_pk: data_dict.id,
                    };
                    upload_dict[data_field] = new_value;

                    UploadChanges(upload_dict, urls.url_envelopsubject_upload);
                };
            };
        };
    }  // UploadInputChange

//========= UploadInputToggle  ============= PR2022-05-16 PR2022-08-20 PR2022-10-10
    function UploadInputToggle(el_input) {
        console.log( " ==== UploadInputToggle ====");
        console.log( "el_input", el_input);

        // only called in secret_exam, can be duo and ete exam
        if (permit_dict.permit_crud){
            const tblRow = t_get_tablerow_selected(el_input);
            const exam_pk = get_attr_from_el_int(tblRow, "data-pk");
            const fldName = get_attr_from_el(el_input, "data-field");

            const data_rows = envelopsubject_rows;
            const data_dict = b_get_datadict_by_integer_from_datarows(data_rows, "id", exam_pk);
            if(!isEmpty(data_dict)){
                const old_value = data_dict[fldName];
                const subject_pk = data_dict.subj_id;
                const examyear_pk = data_dict.ey_id;
                console.log( "data_dict", data_dict);

                const new_value = (!old_value);

                // ---  change icon, before uploading
                add_or_remove_class(el_input, "tickmark_1_2", new_value, "tickmark_0_0");

                // ---  upload changes
                const upload_dict = {
                    table: "envelopsubject",
                    examyear_pk: examyear_pk,
                    envelopsubject_pk: data_dict.id,
                };
                upload_dict[fldName] = new_value;
                UploadChanges(upload_dict, urls.url_envelopsubject_upload);
            };
        };
    }  // UploadInputToggle

//========= UploadChanges  ============= PR2020-08-03
    function UploadChanges(upload_dict, url_str) {
        console.log("=== UploadChanges");
        console.log("    url_str: ", url_str);
        console.log("    upload_dict: ", upload_dict);

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

                    if ("msg_html" in response) {
                        b_show_mod_message_html(response.msg_html);
                    };

                    if ("updated_examyear_rows" in response) {
                        const el_MSTUD_loader = document.getElementById("id_MSTUD_loader");
                        if(el_MSTUD_loader){ el_MSTUD_loader.classList.add(cls_visible_hide)};
                        const tblName = "orderlist";
                        const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                        RefreshDataMap(tblName, field_names, response.updated_examyear_rows, examyear_map);
                    };
                    $("#id_mod_student").modal("hide");

                    if ("updated_envelopbundle_rows" in response) {
                        RefreshDataRows("envelopbundle", envelopbundle_rows, response.updated_envelopbundle_rows, true)  // true = update
                    };
                    if ("updated_enveloplabel_rows" in response) {
                        RefreshDataRows("enveloplabel", enveloplabel_rows, response.updated_enveloplabel_rows, true)  // true = update
                    };
                    if ("updated_envelopitem_rows" in response) {
                        RefreshDataRows("envelopitem", envelopitem_rows, response.updated_envelopitem_rows, true)  // true = update
                    };
                    if ("updated_envelopbundlelabel_rows" in response) {
                        // all envelopbundlelabel_rows are retrieved after update. Therefore you can replace envelopbundlelabel_rows
                        envelopbundlelabel_rows = response.updated_envelopbundlelabel_rows
                    };
                    if ("updated_enveloplabelitem_rows" in response) {
                        // all enveloplabelitem_rows are retrieved after update. Therefore you can replace enveloplabelitem_rows
                        enveloplabelitem_rows = response.updated_enveloplabelitem_rows;
                    };

                    if ("updated_envelopsubject_rows" in response) {
                        RefreshDataRows("envelopsubject", envelopsubject_rows, response.updated_envelopsubject_rows, true)  // true = update
                    };

                    if ("publish_orderlist_msg_html" in response) {
                        MPUBORD_UpdateFromResponse(response);
                    };

                    if ("checked_envelopsubject_rows" in response  || "checked_envelop_school_rows" in response) {
                        MENVPR_UpdateFromResponse(response);
                    };

                },  // success: function (response) {
                error: function (xhr, msg) {
                    // ---  hide loader
                    el_loader.classList.add(cls_visible_hide);
                    console.log(msg + '\n' + xhr.responseText);
                     b_show_mod_message_html(["<p class='border_bg_invalid p-2'>",
                                 loc.An_error_occurred, ":<br><i>", msg, "<br><i>", xhr.responseText, '</i><br>',
                                "</p>"].join(""));
                    $("#id_mod_envelop_print").modal("hide");

                }  // error: function (xhr, msg) {
            });  // $.ajax({
        }  //  if(!!row_upload)
    };  // UploadChanges

//=========  SBR_display_subject  ================ PR2022-10-20
    function SBR_display_subject() {
        console.log("===== SBR_display_subject =====");
        t_MSSSS_display_in_sbr("subject", setting_dict.sel_subject_pk);
    };  // SBR_display_subject

// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2021-08-22 PR2022-08-04
    function ModConfirmOpen(mode, tblRow) {
        console.log(" -----  ModConfirmOpen   ----")
        console.log("mode", mode)
        console.log("tblRow", tblRow)
        // values of mode are : "prelim_orderlist", "orderlist_per_school",
        // "download", "delete_envelopbundle", "delete_enveloplabel", "delete_envelopitem"
        // "delete_bundle_or_label"
    //console.log("mod_MENV_dict", mod_MENV_dict)

    // when modal is called by MENVLAB delete btnm it can be bundle or label
        if (mode === "delete_bundle_or_label"){
            mode = (mod_MENV_dict.is_bundle) ? "delete_envelopbundle" : "delete_enveloplabel";
        };

        if (["prelim_orderlist", "orderlist_per_school"].includes(mode)){
            mod_dict = {mode: mode}

            let header_txt = null, html_list = null, url_str = null;

            if (mode === "orderlist_per_school"){
    // set focus to cancel button
                header_txt = loc.Preliminary_orderlist + loc.per_school;
                html_list = ["<div class='flex_1 mx-1'>",
                                "<p>", loc.The_preliminary_orderlist, loc.per_school, loc.will_be_downloaded_sing, "</p>",
                                "<p>", loc.Do_you_want_to_continue, "</p>",
                             "</div>"]

                url_str = urls.orderlist_per_school_download_url;


            } else if (mode === "prelim_orderlist"){

    // set focus to cancel button
                header_txt = loc.Downlaod_preliminary_orderlist;

                html_list = ["<div class='flex_1 mx-1'>",
                                "<label for='id_MCONF_select' class='label_margin_top_m3'> ",
                                loc.Downlaod_preliminary_orderlist, ":</label>",
                                 "<select id='id_MCONF_select' class='form-control'",
                                       "autocomplete='off' ondragstart='return false;' ondrop='return false;'>",
                                     "<option value='totals_only'>", loc.Totals_only , "</option>",
                                     "<option value='extra_separate'>", loc.Extra_separate, "</option>",
                                "</select>",
                             "</div>"]
                url_str = urls.url_orderlist_download;

            };

            el_confirm_header.innerText = header_txt;
            el_confirm_loader.classList.add(cls_visible_hide)
            el_confirm_msg_container.className = "p-3";

            const msg_html =  html_list.join("");
            el_confirm_msg_container.innerHTML = msg_html;

            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            if (el_modconfirm_link) {
                el_modconfirm_link.setAttribute("href", urls.url_orderlist_download);
            };
// set focus to save button
            setTimeout(function (){
                el_confirm_btn_save.focus();
            }, 500);
        // show modal
            $("#id_mod_confirm").modal({backdrop: true});

// +++ delete envelopbundle, enveloplabel, envelopitem +++
        } else if (["delete_envelopbundle", "delete_enveloplabel", "delete_envelopitem"].includes(mode)) {
            const is_bundle = (mode === "delete_envelopbundle");
            const is_label = (mode === "delete_enveloplabel");
            //console.log( "is_bundle: ", is_bundle);
            //console.log( "is_label: ", is_label);

            const header_txt = (is_bundle) ? loc.Delete_bundle : (is_label) ? loc.Delete_label : loc.Delete_label_item;

// --- get existing data_dict from data_rows

        //console.log("selected", selected)
            // envelop_bundle_label_item_pk, contains bundle, label or item pk;
            const pk_int = selected.envelop_bundle_label_item_pk;
            const data_rows = (is_bundle) ? envelopbundle_rows : (is_label) ? enveloplabel_rows : envelopitem_rows;

            const [index, data_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);
            //console.log( "data_dict: ", data_dict);

            if (isEmpty(data_dict)){
                const msg_txt = (is_bundle) ? loc.Please_select_bundle : (is_label) ? loc.Please_select_label : loc.Please_select_label_item;
                b_show_mod_message_html(msg_txt, header_txt);

            } else {
                const tblName = (is_bundle) ?  "envelopbundle" : (is_label) ?  "enveloplabel" : "envelopitem";
                mod_dict = {
                    mode: mode,
                    table: tblName,
                    pk_int: data_dict.id,
                    map_id: data_dict.mapid
                };

                const caption = (is_bundle) ? loc.Bundle : (is_label) ?  loc.Label : loc.Label_item;
                const name_txt = (is_bundle) ?  (data_dict.name) ? data_dict.name : "---"  :
                             (is_label) ?  (data_dict.name) ? data_dict.name : "---"  : (data_dict.content_nl) ? data_dict.content_nl : "---";

                const msg_html = ["<div class='mx-2'>",
                                "<p>", caption, " '", name_txt, "' ", loc.will_be_deleted, "</p>",
                                "<p>", loc.Do_you_want_to_continue, "</p>",
                             "</div>"].join("")

                el_confirm_header.innerText = header_txt;
                el_confirm_loader.classList.add(cls_visible_hide)
                el_confirm_msg_container.className = "p-3";

                el_confirm_msg_container.innerHTML = msg_html;

    // set focus to save button
                setTimeout(function (){
                    el_confirm_btn_save.focus();
                }, 500);
        // show modal
                $("#id_mod_confirm").modal({backdrop: true});
            };

// +++ download +++
        } else if (mode === "download") {
            const is_bundle = (mode === "delete_envelopbundle");
            const is_label = (mode === "delete_enveloplabel");
            //console.log( "is_bundle: ", is_bundle);
            //console.log( "is_label: ", is_label);

            const header_txt = loc.Print_labels;

// --- get existing data_dict from data_rows
            const pk_int = get_attr_from_el_int(tblRow, "data-pk");
            const [index, data_dict, compare] = b_recursive_integer_lookup(envelopsubject_rows, "id", pk_int);
            console.log( "envelopsubject_rows: ", envelopsubject_rows);
            console.log( "pk_int: ", pk_int), typeof pk_int;
            console.log( "data_dict: ", data_dict);

// skip if no tblRow selected or if exam has no envelopbundle
            if (!isEmpty(data_dict)){
                if (data_dict.envelopbundle_id){
                    const tblName = (is_bundle) ?  "envelopsubject" : (is_label) ?  "enveloplabel" : "envelopitem";
                    mod_dict = {
                        mode: mode,
                        table: "envelopsubject",
                        envelopsubject_pk: data_dict.id,
                        envelopbundle_pk: data_dict.envelopbundle_id
                    };
                    const msg_html = ["<div class='mx-2'>",
                                    "<p>", loc.An_example_of_labels_of_thisbundle,  " ", loc.will_be_downloaded_sing, "</p>",
                                    "<p>", loc.Do_you_want_to_continue, "</p>",
                                 "</div>"].join("")

                    el_confirm_header.innerText = header_txt;
                    el_confirm_loader.classList.add(cls_visible_hide)
                    el_confirm_msg_container.className = "p-3";

                    el_confirm_msg_container.innerHTML = msg_html;

        // set focus to save button
                    setTimeout(function (){
                        el_confirm_btn_save.focus();
                    }, 500);
            // show modal
                    $("#id_mod_confirm").modal({backdrop: true});
                };
            };
        };
    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2021-08-22 PR2022-10-10
    function ModConfirmSave() {
        console.log(" --- ModConfirmSave --- ");
        console.log("mod_dict: ", mod_dict);
        let close_modal_with_timout = false;

        if (["prelim_orderlist", "orderlist_per_school"].includes(mod_dict.mode)){
            let href = null;
            if (mod_dict.mode === "orderlist_per_school"){
                href = urls.orderlist_per_school_download_url;
            } else if (mod_dict.mode === "prelim_orderlist"){
                const el_id_MCONF_select = document.getElementById("id_MCONF_select")
                const href_str = (el_id_MCONF_select.value) ? el_id_MCONF_select.value : "-"
                href = urls.url_orderlist_download.replace("-", href_str);
            };
            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            el_modconfirm_link.href = href;
            el_modconfirm_link.click();
    // show loader
            el_confirm_loader.classList.remove(cls_visible_hide)
            //close_modal_with_timout = true;
            $("#id_mod_confirm").modal("hide");

        } else if (["delete_envelopbundle", "delete_enveloplabel", "delete_envelopitem"].includes(mod_dict.mode)) {
            if (permit_dict.permit_crud){
                const is_bundle = (mod_dict.mode === "delete_envelopbundle");
                const is_label = (mod_dict.mode === "delete_enveloplabel");
                let upload_dict = {
                    table: mod_dict.table,
                    mode: "delete",
                    pk_int: mod_dict.pk_int
                };

                const url_str = (is_bundle) ? urls.url_envelopbundle_upload :
                                (is_label) ? urls.url_enveloplabel_upload : urls.url_envelopitem_upload;
                UploadChanges(upload_dict, url_str);

                const tblRow = document.getElementById(mod_dict.map_id)
                ShowClassWithTimeout(tblRow, "tsa_tr_error")
            };
            $("#id_mod_confirm").modal("hide");

        } else if (mod_dict.mode === "download") {

            const upload_dict = {
                envelopsubject_pk_list: [mod_dict.envelopsubject_pk],
                sel_layout: "all"
            };

        //console.log("upload_dict", upload_dict)
        // convert dict to json and add as parameter in link
            const upload_str = JSON.stringify(upload_dict);
            const href_str = urls.url_envelop_print.replace("-", upload_str);
        console.log("href_str", href_str)

            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            el_modconfirm_link.href = href_str;
        //console.log("el_modconfirm_link", el_modconfirm_link)

            el_modconfirm_link.click();

    // ---  hide modal
            if(close_modal_with_timout) {
            // close modal after 5 seconds
                setTimeout(function (){ $("#id_mod_confirm").modal("hide") }, 5000);
            } else {
                $("#id_mod_confirm").modal("hide");
        //console.log("close_modal_with_timout", close_modal_with_timout)
            };
        };
    };  // ModConfirmSave

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
    };  // ModConfirmResponse


//========= MODAL PUBLISH ORDERLIST ================ PR2021-09-08 PR2022-10-13
    function MPUBORD_Open (open_mode ) {
        console.log("===  MPUBORD_Open  =====") ;
        //console.log("setting_dict", setting_dict) ;
        mod_MPUBORD_dict = {}

        if (permit_dict.permit_submit_orderlist) {

            mod_MPUBORD_dict = {step: -1} // increases value 1 in MPUBORD_Save

// ---  reset and hide el_MPUBORD_input_verifcode
            add_or_remove_class(el_MPUBORD_input_verifcode.parentNode, cls_hide, true);
            el_MPUBORD_input_verifcode.value = null;

// ---  reset el_MPUBORD_send_email
            el_MPUBORD_send_email.checked = false;

// ---   hide loader
            // PR2021-01-21 debug 'display_hide' not working when class 'image_container' is in same div
            add_or_remove_class(el_MPUBORD_loader, cls_hide, true);

            MPUBORD_Save ("save", true);  // true = is_test
            // this one is also in MPUBORD_Save:
            // MPUBORD_SetInfoboxesAndBtns();

            $("#id_mod_publish_orderlist").modal({backdrop: true});
        }
    };  // MPUBORD_Open

//=========  MPUBORD_Save  ================ PR2021-09-08 PR2022-10-13
    function MPUBORD_Save () {
        console.log("===  MPUBORD_Save  =====") ;

        if (permit_dict.permit_submit_orderlist) {
            mod_MPUBORD_dict.step += 1;

            const upload_dict = {
                table: "orderlist",
                now_arr: get_now_arr()
                };


            if (mod_MPUBORD_dict.step === 1){
                UploadChanges(upload_dict, urls.url_orderlist_request_verifcode);
            } else if (mod_MPUBORD_dict.step === 3){

                upload_dict.mode = "submit_save";
                upload_dict.verificationcode = el_MPUBORD_input_verifcode.value
                upload_dict.verificationkey = mod_MPUBORD_dict.verificationkey;

                upload_dict.mode = "submit_save";

                upload_dict.send_email = !!el_MPUBORD_send_email.checked;

                UploadChanges(upload_dict, urls.url_orderlist_publish);
            };
            MPUBORD_SetInfoboxesAndBtns() ;
        } ;
    };  // MPUBORD_Save


//========= MPUBORD_UpdateFromResponse ================ PR2021-09-08
    function MPUBORD_UpdateFromResponse(response) {
        //console.log( " ==== MPUBORD_UpdateFromResponse ====");
        //console.log( "response", response);
        //console.log("mod_MPUBORD_dict", mod_MPUBORD_dict);
        mod_MPUBORD_dict.step += 1;

        mod_MPUBORD_dict.error = !!response.error;
        mod_MPUBORD_dict.verificationkey = response.verificationkey;
        mod_MPUBORD_dict.verification_is_ok = !!response.verification_is_ok;

        if ("log_list" in response){
            mod_MPUBORD_dict.log_list = response.log_list;
        };

       // mod_MPUBORD_dict.submit_is_ok = (!!count_dict.saved)
        //mod_MPUBORD_dict.has_already_published = (!!msg_dict.already_published)
        //mod_MPUBORD_dict.has_saved = !!msg_dict.saved;

        MPUBORD_SetInfoboxesAndBtns(response);

        if ( (mod_MPUBORD_dict.is_approve && mod_MPUBORD_dict.step === 3) || (mod_MPUBORD_dict.is_submit && mod_MPUBORD_dict.step === 5)){
                const datalist_request = { setting: {page: "page_studsubj"},
                                //studentsubject_rows: {cur_dep_only: true},
                                }
                DatalistDownload(datalist_request);
        };
    };  // MPUBORD_UpdateFromResponse

//=========  MPUBORD_SetInfoboxesAndBtns  ================ PR2021-09-08
     function MPUBORD_SetInfoboxesAndBtns(response) {
        console.log("===  MPUBORD_SetInfoboxesAndBtns  =====") ;
        console.log("response", response);

        const step = mod_MPUBORD_dict.step;
        const is_response = (!!response);
        const has_error = (is_response && response.error);
        console.log("has_error", has_error) ;

        console.log("step", step) ;
        console.log("response", response) ;

// ---  info_container, loader, info_verifcode and input_verifcode
        let msg_html = null, msg_info_txt = null, show_loader = false;
        let show_info_request_verifcode = false, show_input_verifcode = false, show_input_sendemail = false;
        let disable_save_btn = false, save_btn_txt = null;

        if (response && response.publish_orderlist_msg_html) {
            msg_html = response.publish_orderlist_msg_html;
        };
        //console.log("msg_html", msg_html);

        if (step === 0) {
            // step 0: when form opens
            msg_info_txt = [loc.MPUBORD_info.request_verifcode_01,
                loc.MPUBORD_info.request_verifcode_02,
                " ",
                loc.MPUBORD_info.request_verifcode_03,
                " ",
                loc.MPUBORD_info.request_verifcode_04,
                loc.MPUBORD_info.request_verifcode_05,
                loc.MPUBORD_info.request_verifcode_06
            ].join("<br>");
            save_btn_txt = loc.Request_verifcode;
            show_input_sendemail = true;
        console.log(" step === 0 save_btn_txt", save_btn_txt) ;
        console.log(" loc", loc) ;

        } else if (step === 1) {
            // when clicked on 'Request_verificationcode'
            // tekst: 'AWP is sending an email with the verification code'
            // show textbox with 'You need a 6 digit verification code to submit the Ex form'
            msg_info_txt = loc.MPUBORD_info.requesting_verifcode + "...";
            disable_save_btn = true;
            save_btn_txt = loc.Request_verifcode;

        } else if (step === 2) {
            // when response 'email sent' is received
            // msg_html is in response
            show_info_request_verifcode = mod_MPUBORD_dict.test_is_ok;
            show_input_verifcode = !has_error;
            disable_save_btn = !el_MPUBORD_input_verifcode.value;
            if (!has_error){save_btn_txt = loc.MPUBORD_info.Publish_orderlist};

            show_input_sendemail = true;

        } else if (step === 3) {
            // when clicked on 'Publish orderlist'
            msg_info_txt = loc.MPUBORD_info.Publishing_orderlist + "...";
            show_loader = true;
        } else if (step === 4) {
            // when response 'orderlist submitted' is received
            // msg_html is in response
            show_loader = false;
            show_input_verifcode = false;
        };

        //console.log("msg_info_txt", msg_info_txt) ;
        if (msg_info_txt){
            msg_html = "<div class='p-2 border_bg_transparent'><p class='pb-2'>" +  msg_info_txt + "</p></div>";
        };
        //console.log("msg_html", msg_html) ;
        el_MPUBORD_info_container.innerHTML = msg_html;
        add_or_remove_class(el_MPUBORD_info_container, cls_hide, !msg_html)

        add_or_remove_class(el_MPUBORD_loader, cls_hide, !show_loader)

        add_or_remove_class(el_MPUBORD_input_verifcode.parentNode, cls_hide, !show_input_verifcode);
        if (show_input_verifcode){set_focus_on_el_with_timeout(el_MPUBORD_input_verifcode, 150); };

// ---  show or hide  el_MPUBORD_send_email
        add_or_remove_class(el_MPUBORD_send_email.parentNode, cls_hide, !show_input_sendemail);

// - hide save button when there is no save_btn_txt
        console.log("save_btn_txt", save_btn_txt) ;
        add_or_remove_class(el_MPUBORD_btn_save, cls_hide, !save_btn_txt)
// ---  disable save button till test is finished or input_verifcode has value
        el_MPUBORD_btn_save.disabled = disable_save_btn;;
// ---  set innerText of save_btn
        el_MPUBORD_btn_save.innerText = save_btn_txt;

// ---  set innerText of cancel_btn
        el_MPUBORD_btn_cancel.innerText = (step === 0 || !!save_btn_txt) ? loc.Cancel : loc.Close;

// ---  add eventlistener to href element
        if (step === 4) {
            const el_MPUBORD_OpenLogfile = document.getElementById("id_MPUBORD_OpenLogfile");
            if(el_MPUBORD_OpenLogfile){
                el_MPUBORD_OpenLogfile.addEventListener("click", function() {MPUBORD_OpenLogfile()}, false);
            };
        };

// ---  set innerText of cancel_btn
     }; //  MPUBORD_SetInfoboxesAndBtns

//=========  MPUBORD_InputVerifcode  ================ PR2021-09-08
     function MPUBORD_InputVerifcode(el_input, event_key) {
        //console.log("===  MPUBORD_InputVerifcode  =====") ;
// enable save btn when el_input has value
        el_MPUBORD_btn_save.disabled = !el_input.value;
        if(!el_MPUBORD_btn_save.disabled && event_key && event_key === "Enter"){
            MPUBORD_Save("save")
        }
     };  // MPUBORD_InputVerifcode



/////////////////////////////////////////////
//=========  ModSelEnvBundle_Open  ================  PR2022-08-12
    function ModSelEnvBundle_Open(td) {
        console.log(" ----- ModSelEnvBundle_Open ----")
        console.log("td", td)
        const tblRow = t_get_tablerow_selected(td);

// --- get existing data_dict from data_rows
        const pk_int = get_attr_from_el_int(tblRow, "data-pk");
        console.log("pk_int", pk_int)
        selected.envelopsubject_pk = pk_int

        const [index, data_dict, compare] = b_recursive_integer_lookup(envelopsubject_rows, "id", pk_int);
        setting_dict.envelopbundle_pk = (data_dict.envelopbundle_id) ? data_dict.envelopbundle_id : null;

        t_MSSSS_Open(loc, "envelopbundle", envelopbundle_rows, false, true, setting_dict, permit_dict, ModSelEnvBundle_Response);

    };  // ModSelEnvBundle_Open

//=========  ModSelEnvBundle_Response  ================  PR2022-08-12 PR2022-10-10
    function ModSelEnvBundle_Response(tblName, selected_dict, selected_pk_int) {

        console.log(" ----- ModSelEnvBundle_Response ----")
        console.log("tblName", tblName)
        console.log("selected_dict", selected_dict)
        console.log("selected_pk_int", selected_pk_int)
        console.log("subject_rows", subject_rows)

        if (permit_dict.permit_crud){
    // --- get selected ete_exam
            const pk_int = selected.envelopsubject_pk;
            const [index, data_dict, compare] = b_recursive_integer_lookup(envelopsubject_rows, "id", pk_int);
        console.log( "data_dict: ", data_dict);
        console.log( "selected: ", selected);
            if (data_dict){
                let upload_dict = {
                    table: "envelopsubject",
                    mode: "update",
                    examyear_pk: data_dict.subj_examyear_id,
                    envelopsubject_pk: data_dict.id,
                    envelopbundle_pk: selected_pk_int,

                };
                UploadChanges(upload_dict, urls.url_envelopsubject_upload);
            };
        };
    };  // ModSelEnvBundle_Response

//=========  ModSelEnvBundle_remove_bundle  ================  PR2022-08-13
    function ModSelEnvBundle_remove_bundle() {
        //console.log(" ----- ModSelEnvBundle_remove_bundle ----")
        //console.log("selected", selected)

        if (permit_dict.permit_crud){
// --- get selected ete_exam
            const pk_int = selected.envelopsubject_pk;
            const [index, data_dict, compare] = b_recursive_integer_lookup(envelopsubject_rows, "id", pk_int);

// --- set envelopbundle_pk null
            if (data_dict){
                let upload_dict = {
                    table: "envelopsubject",
                    mode: "update",
                    examyear_pk: data_dict.subj_examyear_id,
                    envelopsubject_pk: data_dict.id,
                    envelopbundle_pk: null
                };
                UploadChanges(upload_dict, urls.url_envelopsubject_upload);
            };
        };
    };  // ModSelEnvBundle_remove_bundle

// ++++++++++++  MODAL ENVELOP LABEL  +++++++++++++++++++++++++++++++++++++++

//=========  MENVLAB_Open  ================  PR2022-08-06
    function MENVLAB_Open(tblName, el_input) {
        //console.log(" -----  MENVLAB_Open   ----")

        //console.log("permit_dict.permit_crud", permit_dict.permit_crud)
        //console.log("el_input", el_input)

        mod_MENV_dict = {};

        if (permit_dict.permit_crud){
            // el_input is undefined when called by submenu btn 'Add new'
            mod_MENV_dict.is_addnew = (!el_input);
            mod_MENV_dict.is_bundle = (tblName === "envelopbundle")
        //console.log("mod_MENV_dict", mod_MENV_dict)
// --- get existing data_dict from enveloplabel_rows
            if(mod_MENV_dict.is_addnew){
                if (!mod_MENV_dict.is_bundle){
                    mod_MENV_dict.is_errata = false;
                    mod_MENV_dict.is_variablenumber = false;
                    mod_MENV_dict.numberinenvelop = 1;
                    mod_MENV_dict.numberofenvelops = 1;
                    mod_MENV_dict.max_sequence = 0;
                };
            } else {
                const tblRow = t_get_tablerow_selected(el_input);
                const pk_int = get_attr_from_el_int(tblRow, "data-pk");

                const data_rows = (mod_MENV_dict.is_bundle) ? envelopbundle_rows : enveloplabel_rows;
                const [index, data_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);
        //console.log("data_dict", data_dict)

                if (!isEmpty(data_dict)) {
                    mod_MENV_dict.parent_pk = data_dict.id;
                    mod_MENV_dict.parent_name = data_dict.name;
                    mod_MENV_dict.is_errata = !!data_dict.is_errata;
                    mod_MENV_dict.is_variablenumber = !!data_dict.is_variablenumber;
                    mod_MENV_dict.numberinenvelop = data_dict.numberinenvelop;
                    mod_MENV_dict.numberofenvelops = data_dict.numberofenvelops;
                    mod_MENV_dict.max_sequence = 0;
                    mod_MENV_dict.modby_username = data_dict.modby_username;
                    mod_MENV_dict.modifiedat = data_dict.modifiedat;
                }
            };
            // used in ModConfirm to delete, contains bundle, label or item pk
            selected.envelop_bundle_label_item_pk = (mod_MENV_dict.parent_pk) ? mod_MENV_dict.parent_pk : null;

        //console.log("mod_MENV_dict", mod_MENV_dict)
            MENVLAB_FillDictlist();
            MENVLAB_FillTable();
            MENVLAB_SetInputElements();

            el_MENVLAB_header.innerText = (mod_MENV_dict.is_bundle) ?
                                            (mod_MENV_dict.is_addnew) ? loc.New_bundle : loc.Edit_bundle :
                                            (mod_MENV_dict.is_addnew) ? loc.New_label : loc.Edit_label;

            el_MENVLAB_label_available.innerText = (mod_MENV_dict.is_bundle) ? loc.Available_labels : loc.Available_label_items;
            el_MENVLAB_label_selected.innerText = (mod_MENV_dict.is_bundle) ? loc.Labels : loc.Label_items;
            el_MENVLAB_label_name.innerText = (mod_MENV_dict.is_bundle) ? loc.Bundle_name : loc.Label_name;

            el_MENVLAB_name.value = (mod_MENV_dict.parent_name) ? mod_MENV_dict.parent_name : null;
            add_or_remove_class(el_MENVLAB_number_container, cls_hide, mod_MENV_dict.is_bundle);

            let modified_txt = null;
            if (!mod_MENV_dict.is_addnew){
                const modified_dateJS = parse_dateJS_from_dateISO(mod_MENV_dict.modifiedat);
                const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
                const modified_by = (mod_MENV_dict.modby_username) ? mod_MENV_dict.modby_username : "-";
                modified_txt = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by;
            };
            el_MENVIT_msg_modified.innerText = modified_txt;

    // ---  disable btn submit, hide delete btn when is_addnew
            el_MENVLAB_btn_delete.innerText = (mod_MENV_dict.is_bundle) ?loc.Delete_bundle : loc.Delete_label;
            add_or_remove_class(el_MENVLAB_btn_delete, cls_hide, mod_MENV_dict.is_addnew );

            MENVLAB_validate_and_disable(!!mod_MENV_dict.is_addnew);

            set_focus_on_el_with_timeout(el_MENVLAB_name, 50);
// show modal
            $("#id_mod_enveloplabel").modal({backdrop: true});
        };
    };  // MENVLAB_Open

//=========  MENVLAB_Save  ================   PR2022-08-06
    function MENVLAB_Save(crud_mode) {
        console.log(" -----  MENVLAB_save  ----", crud_mode);
        console.log( "mod_MENV_dict: ", mod_MENV_dict);

        if (permit_dict.permit_crud){
            const is_create = (mod_MENV_dict.is_addnew);
            const is_delete = (crud_mode === "delete");
            const upload_mode = (is_create) ? "create" : (is_delete) ? "delete" : "update";

    // ---  put values of input elements in upload_dict
            let upload_dict = {
                table: (mod_MENV_dict.is_bundle) ? "envelopbundle" : "enveloplabel",
                mode: upload_mode,
                name: mod_MENV_dict.parent_name,
                pk_int: mod_MENV_dict.parent_pk
            };

            const uniontable_list = [];

// loop through uniontable items (envelopbundlelabel or enveloplabelitem)
            for (let i = 0, picklis_dict; picklis_dict = mod_MENV_dict.picklist[i]; i++) {
                // only add items that:
                //  - have uniontable_pk is null and selected = true (these are created items)
                //  - have uniontable_pk not null ( to catch removed items and also items whose sequence has changed)
                const add_to_list = ( (!picklis_dict.uniontable_pk && !!picklis_dict.selected) || (!!picklis_dict.uniontable_pk));

    //console.log( "picklis_dict.uniontable_pk: ", picklis_dict.uniontable_pk);
    //console.log( "picklis_dict.selected: ", picklis_dict.selected);
    //console.log( "add_to_list: ", add_to_list);
                if (add_to_list){
                    const item_dict = {
                        picklist_pk: picklis_dict.picklist_pk,
                        uniontable_pk: picklis_dict.uniontable_pk,
                        sequence: picklis_dict.uniontable_sequence,
                        selected: picklis_dict.selected
                    };
                    uniontable_list.push(item_dict);
                };
            };
            if (!mod_MENV_dict.is_bundle) {
                upload_dict.is_errata = mod_MENV_dict.is_errata;
                upload_dict.is_variablenumber = mod_MENV_dict.is_variablenumber;
                upload_dict.numberinenvelop = mod_MENV_dict.numberinenvelop;
                upload_dict.numberofenvelops = mod_MENV_dict.numberofenvelops;
                if (uniontable_list && uniontable_list.length){
                    upload_dict.uniontable = uniontable_list;
                };
            };
            if (uniontable_list && uniontable_list.length){
                upload_dict.uniontable = uniontable_list;
            };

            const url_str = (mod_MENV_dict.is_bundle) ? urls.url_envelopbundle_upload : urls.url_enveloplabel_upload;
    //console.log( "url_str: ", url_str);
    //console.log( "upload_dict: ", upload_dict);
            UploadChanges(upload_dict, url_str);
        };
    // ---  hide modal
            $("#id_mod_enveloplabel").modal("hide");
    } ; // MENVLAB_Save

//========= MENVLAB_FillDictlist  ============= PR2022-08-18 PR2022-09-29
    function MENVLAB_FillDictlist(){
       //console.log(" -----  MENVLAB_FillDictlist   ----")

// - reset picklist
        mod_MENV_dict.picklist = [];
        mod_MENV_dict.max_sequence = 0;

// - get parent_pk, this is the pk of the current bundle or current label
        const parent_pk = mod_MENV_dict.parent_pk;
    //console.log("parent_pk", parent_pk)

// - loop through picklist rows, this is label_rows when parent is bundle and is item rows when parent is label
        const picklist_rows = (mod_MENV_dict.is_bundle) ? enveloplabel_rows : envelopitem_rows;

// - unionlist, is bundlelabel_rows when parent is bundle and is labelitem_rows when parent is label
        const unionlist = (mod_MENV_dict.is_bundle) ? envelopbundlelabel_rows : enveloplabelitem_rows;

        for (let i = 0, picklist_dict; picklist_dict = picklist_rows[i]; i++) {
            const picklist_pk = picklist_dict.id;
            const picklist_name = (picklist_dict.name) ? picklist_dict.name : "";
            const picklist_sortby = (mod_MENV_dict.is_bundle) ? picklist_dict.name : picklist_dict.content_nl;

            let is_selected = false, uniontable_pk = null, uniontable_sequence = null;
            if (picklist_pk){

// - check if this picklist item is in unionlist list of this parent
                if(unionlist && unionlist.length){
                    for (let j = 0, union_dict; union_dict = unionlist[j]; j++) {
                    // only check unionlist of this parent
                        const uniontable_parent_pk = (mod_MENV_dict.is_bundle) ? union_dict.envelopbundle_id : union_dict.enveloplabel_id;
                        if(uniontable_parent_pk === parent_pk) {
                            const uniontable_picklist_pk = (mod_MENV_dict.is_bundle) ? union_dict.enveloplabel_id : union_dict.envelopitem_id;
                            if (uniontable_picklist_pk === picklist_pk) {
                                is_selected = true;
                                uniontable_pk = union_dict.id;
                                uniontable_sequence = union_dict.sequence;
                                break;
                }}}};
            };
            if (uniontable_sequence) {
                if (uniontable_sequence > mod_MENV_dict.max_sequence) {
                    mod_MENV_dict.max_sequence = uniontable_sequence;
                };
            } else {
                mod_MENV_dict.max_sequence += 1;
                uniontable_sequence = mod_MENV_dict.max_sequence;
            };
            mod_MENV_dict.picklist.push({
                picklist_pk: picklist_pk,
                uniontable_pk: uniontable_pk,
                uniontable_sequence: uniontable_sequence,
                sortby: (picklist_sortby) ? picklist_sortby : "",

                content_nl: (picklist_dict.content_nl) ? picklist_dict.content_nl : "---",
                content_en: (picklist_dict.content_en) ? picklist_dict.content_en : "---",
                content_pa: (picklist_dict.content_pa) ? picklist_dict.content_pa : "---",

                instruction_nl: (picklist_dict.instruction_nl) ? picklist_dict.instruction_nl : "---",
                instruction_en: (picklist_dict.instruction_en) ? picklist_dict.instruction_en : "---",
                instruction_pa: (picklist_dict.instruction_pa) ? picklist_dict.instruction_pa : "---",

                selected: is_selected
            });
        };
        mod_MENV_dict.picklist.sort(b_comparator_sortby);
    };  // MENVLAB_FillDictlist

//========= MENVLAB_FillTable  ============= PR2022-08-06 PR2022-10-20
    function MENVLAB_FillTable(just_linked_unlinked_pk) {
        //console.log("===== MENVLAB_FillTable ===== ");

        el_MENVLAB_tblBody_available.innerText = null;
        el_MENVLAB_tblBody_selected.innerText = null;

        // increase height of tblBody_selected when is_bundle PR2022-10-20
        add_or_remove_class(el_MENVLAB_tblBody_selected.parentNode, "tbl_h320_w_auto",  mod_MENV_dict.is_bundle, "tbl_h180_w_auto" )

        const data_rows = mod_MENV_dict.picklist;
        if (data_rows && data_rows.length) {
            for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
                const tblBody = (data_dict.selected) ? el_MENVLAB_tblBody_selected : el_MENVLAB_tblBody_available;
                MENVLAB_CreateTblRow(tblBody, data_dict, data_dict.selected,  just_linked_unlinked_pk);
            };
        } else {
            const data_dict = {sortby: (mod_MENV_dict.is_bundle) ? loc.No_labels : loc.No_label_items};
            MENVLAB_CreateTblRow(el_MENVLAB_tblBody_available, data_dict);
        };
    }; // MENVLAB_FillTable

//========= MENVLAB_CreateTblRow  ============= PR2022-08-06
    function MENVLAB_CreateTblRow(tblBody, data_dict, is_table_selected, just_linked_unlinked_pk) {
        //console.log("===== MENVLAB_CreateTblRow ===== ");
        //console.log("   data_dict", data_dict);
        //console.log("   just_linked_unlinked_pk", just_linked_unlinked_pk);

//--- get info from data_dict
        const pk_int = (data_dict.picklist_pk) ? data_dict.picklist_pk : null;
        const caption = (data_dict.sortby) ? data_dict.sortby : "---";

        const is_just_linked = (pk_int === just_linked_unlinked_pk);

// ---  lookup index where this row must be inserted
        // available items are sorted by name (sortby), selected items are sorted by sequence
        const ob1 = (data_dict.selected && data_dict.uniontable_sequence) ? ("0000" + data_dict.uniontable_sequence).slice(-4) : "0000";
        const ob2 = (caption) ? caption.toLowerCase() : "";
        const row_index = b_recursive_tblRow_lookup(tblBody, loc.user_lang, ob1, ob2);

//--------- insert tblBody row at row_index
        const tblRow = tblBody.insertRow(row_index);
        tblRow.setAttribute("data-pk", pk_int);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);
        tblRow.setAttribute("data-ob2", ob2);

//- add hover to select row
        add_hover(tblRow)

// --- add td to tblRow.
        let td = null, el_div = null;
// --- add td to tblRow.
        const tw = (data_dict.selected) ? "tw_240" : "tw_360";
        td = tblRow.insertCell(-1);
        el_div = document.createElement("div");
            el_div.classList.add("pointer_show");
            el_div.innerText = caption;
            el_div.classList.add("tw_240", "px-1");
            if (!mod_MENV_dict.is_bundle){
                el_div.title = [
                    data_dict.content_nl, "     " + data_dict.instruction_nl,
                    data_dict.content_en, "     " + data_dict.instruction_en,
                    data_dict.content_pa, "     " + data_dict.instruction_pa
                ].join("\n");
            };

            td.appendChild(el_div);
            td.addEventListener("click", function() {MENVLAB_SelectItem(tblRow)}, false);

        //td.classList.add(cls_bc_transparent);

        if (data_dict.selected){

// --- add black triangle up tblRow when selected table
          // &#9650 black triangle up symbol
          // &#9651 outline black triangle up symbol
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                el_div.classList.add("tw_020")
                el_div.innerHTML = "&#9651;"
                el_div.title = loc.Click_to_move_item_up;
            td.appendChild(el_div);
            td.addEventListener("click", function() {MENVLAB_UpDown("up", tblRow)}, false);
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                el_div.classList.add("tw_020")
                el_div.innerHTML = "&#9661;"
                el_div.title = loc.Click_to_move_item_down;
            td.appendChild(el_div);
            td.addEventListener("click", function() {MENVLAB_UpDown("down", tblRow)}, false);
        };

    // --- if new appended row or position has changed: highlight row for 1 second
        if (is_just_linked) {
            let cell = tblRow.cells[0];
            tblRow.classList.add("tsa_td_unlinked_selected");
            setTimeout(function (){  tblRow.classList.remove("tsa_td_unlinked_selected")  }, 1000);
        };
    }; // MENVLAB_CreateTblRow

//=========  MENVLAB_SelectItem  ================ PR2022-08-07
    function MENVLAB_SelectItem(tblRow) {
        //console.log( "===== MENVLAB_SelectItem ========= ");
        //console.log( "tblRow", tblRow);
        // all data attributes are now in tblRow, not in el_select = tblRow.cells[0].children[0];

// ---  get clicked tablerow
        if(tblRow) {
            let just_linked_unlinked_pk = null;
            const pk_int = get_attr_from_el_int(tblRow, "data-pk");

            const data_rows = mod_MENV_dict.picklist;
            for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
                if (data_dict.picklist_pk === pk_int){
                    data_dict.selected = !data_dict.selected;
                    if (data_dict.selected){
                        mod_MENV_dict.max_sequence += 1;
                        data_dict.uniontable_sequence = mod_MENV_dict.max_sequence;
                    } else {
                        data_dict.uniontable_sequence = null;
                    }
                    just_linked_unlinked_pk = data_dict.picklist_pk;
                    break;
                };
            };
    //console.log( "just_linked_unlinked_pk", just_linked_unlinked_pk);

        MENVLAB_FillTable(just_linked_unlinked_pk);
        MENVLAB_validate_and_disable();

// ---  save and close
            //MENVLAB_Save();
        };
    };  // MENVLAB_SelectItem

//=========  MENVLAB_InputKeyup  ================ PR2022-08-18
    function MENVLAB_InputKeyup(el_input) {
        console.log( "===== MENVLAB_InputKeyup  ========= ");
        const fldName = get_attr_from_el(el_input, "data-field");

        const err_fields = MENVLAB_validate_and_disable();

        let new_value = el_input.value;
        let new_value_number = Number(new_value);

    console.log( "new_value", new_value, typeof new_value);
    console.log( "new_value_number", new_value_number, typeof new_value_number);

        if (fldName === "name" && !err_fields.includes(fldName)) {
            mod_MENV_dict.parent_name = (new_value) ? new_value : null;
        } else if (fldName === "numberofenvelops" && !err_fields.includes(fldName)) {
            mod_MENV_dict.numberofenvelops = (new_value_number) ? new_value_number : null;
        } else if (fldName === "numberinenvelop" && !err_fields.includes(fldName)) {
            mod_MENV_dict.numberinenvelop = (new_value_number || new_value_number === 0 ) ? new_value_number : null;
        };
    console.log( "mod_MENV_dict.numberinenvelop", mod_MENV_dict.numberinenvelop, typeof mod_MENV_dict.numberinenvelop);
    }; // MENVLAB_InputKeyup

//========= MENVLAB_InputToggle  ============= PR2022-08-18
    function MENVLAB_InputToggle(el_input){
        //console.log( "===== MENVLAB_InputToggle  ========= ");
        const data_field = get_attr_from_el(el_input, "data-field")
    // toggle value
        if (data_field === "is_variablenumber"){
            mod_MENV_dict.is_variablenumber = !mod_MENV_dict.is_variablenumber;

            if (mod_MENV_dict.is_variablenumber){
                mod_MENV_dict.numberinenvelop = 15;
                mod_MENV_dict.numberofenvelops = null;
            } else {
                mod_MENV_dict.numberinenvelop = 1;
                mod_MENV_dict.numberofenvelops = 1;
            };
            el_MENVLAB_numberinenvelop.value = mod_MENV_dict.numberinenvelop;
            el_MENVLAB_numberofenvelops.value = mod_MENV_dict.numberofenvelops;

        } else {
            mod_MENV_dict.is_errata = !mod_MENV_dict.is_errata;
        };
        MENVLAB_validate_and_disable();
        MENVLAB_SetInputElements();
    }; // MENVLAB_InputToggle

//========= MENVLAB_UpDown  ============= PR2022-08-18
    function MENVLAB_UpDown(mode, tblRow){
        //console.log( "===== MENVLAB_UpDown  ========= ");

        const this_picklist_dict = MENVLAB_get_picklist_dict(tblRow);
        const pk_int = get_attr_from_el_int(tblRow, "data-pk");
        const row_index = (tblRow) ? tblRow.rowIndex : 0

        const tblBody = el_MENVLAB_tblBody_selected;

        const rows_length = tblBody.rows.length;

    //console.log( "this_picklist_dict", this_picklist_dict);
        let target_picklist_dict = null;
        let this_sequence = (this_picklist_dict) ? this_picklist_dict.uniontable_sequence : null;

        let target_index = null;
        if (mode === "up"){
            if (row_index > 0){target_index = row_index - 1};
        } else if (row_index < rows_length -1){
            target_index = row_index + 1;
        };

        if  (target_index != null){
            target_picklist_dict = MENVLAB_get_picklist_dict(tblBody.rows[target_index]);
    //console.log( "target_picklist_dict", target_picklist_dict);
            if (target_picklist_dict){
                const target_sequence = target_picklist_dict.uniontable_sequence;
    //console.log( "target_sequence", target_sequence);
                target_picklist_dict.uniontable_sequence = this_sequence;
                this_picklist_dict.uniontable_sequence = target_sequence;

    //console.log( "mod_MENV_dict.picklist", mod_MENV_dict.picklist);
                mod_MENV_dict.sequence_has_changed = true;
                MENVLAB_FillTable(pk_int);
                MENVLAB_validate_and_disable();
            };
        };
    }; // MENVLAB_UpDown

//========= MENVLAB_UpDown  ============= PR2022-08-18
    function MENVLAB_get_picklist_dict(tblRow){
    // ---  get clicked tablerow
        let picklist_dict = null;
        if(tblRow) {
            let just_linked_unlinked_pk = null;
            const pk_int = get_attr_from_el_int(tblRow, "data-pk");

            const data_rows = mod_MENV_dict.picklist;
            for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
                if (data_dict.picklist_pk === pk_int){
                    picklist_dict = data_dict;
                    break;
                };
            };
        };
        return picklist_dict;
    };

//=========  MENVLAB_validate_and_disable  ================  PR2022-08-18
    function MENVLAB_validate_and_disable(is_addnew) {
        console.log(" -----  MENVLAB_validate_and_disable  ----", is_addnew);
        console.log( "mod_MENV_dict: ", mod_MENV_dict);
        // is_addnew = true only on opening new bundle / babel; is_addnew is always false after MENVLAB_InputKeyup
        let err_fields = [];

// ---  bundle name or label name
        let value = el_MENVLAB_name.value;
        let caption = (mod_MENV_dict.is_bundle) ? loc.Bundle_name : loc.Label_name;
        let msg_err_name = null;
        if (!value) {
            if (!is_addnew) {msg_err_name = caption + loc.cannot_be_blank};
        } else if (value.length > 50) {
            msg_err_name = caption + loc.is_too_long_MAX50;
        };
        if (msg_err_name){
            err_fields.push("name");
        };

        add_or_remove_class(el_MENVLAB_name, "border_bg_invalid", msg_err_name);
        add_or_remove_class(el_MENVLAB_name_err.parentNode, cls_hide, !msg_err_name);
        el_MENVLAB_name_err.innerText = msg_err_name;

        if (!mod_MENV_dict.is_bundle){
        //console.log( "mod_MENV_dict.is_variablenumber: ", mod_MENV_dict.is_variablenumber);

// ---  number of envelops
            value = el_MENVLAB_numberofenvelops.value;
            let msg_err_numberof = null;
            if (!mod_MENV_dict.is_variablenumber){
                caption = loc.Number_of_envelops;
                if(!value){
                    if (!is_addnew) {msg_err_numberof = loc.Number_of_envelops + loc.cannot_be_blank};
                } else {
                    const value_number = Number(value);
                    if(!value_number || !Number.isInteger(value_number)){
                        msg_err_numberof = [caption, " '", value, "' ", loc.err_msg_is_invalid_number].join("");
                    };
                };
            };
        //console.log( "msg_err_numberof: ", msg_err_numberof);
            if (msg_err_numberof){
                err_fields.push("numberofenvelops");
            };
            add_or_remove_class(el_MENVLAB_numberofenvelops, "border_bg_invalid", msg_err_numberof);

// ---  number in envelops - may be null
            value = el_MENVLAB_numberinenvelop.value;
            let msg_err_numberin = null;
            caption = (mod_MENV_dict.is_variablenumber) ?  loc.Max_number_in_envelop : loc.Number_in_envelop;
            if(!value){
                // numberinenvelop can not be null
                if (!is_addnew) {msg_err_numberin = caption + loc.cannot_be_blank};
            } else {
                const value_number = Number(value);
                let not_valid = false;
                if(!Number.isInteger(value_number)) {
                    not_valid = true;
                } else if (!value_number){
                // numberinenvelop can be 0 when not is_variablenumber
                    if (value_number === 0) {
                        not_valid = mod_MENV_dict.is_variablenumber;
                    } else {
                        not_valid = true;
                    };
                };
                if (not_valid){
                    msg_err_numberin = [caption, " '", value, "' ", loc.err_msg_is_invalid_number].join("");
                };
            };
            if (msg_err_numberin){
                err_fields.push("numberinenvelop");
            };
            add_or_remove_class(el_MENVLAB_numberinenvelop, "border_bg_invalid", msg_err_numberin);

            add_or_remove_class(el_MENVLAB_number_err.parentNode, cls_hide, (!msg_err_numberof && !msg_err_numberin))
            let msg_html = null;
            if (msg_err_numberof){
                if (msg_err_numberin) {
                    msg_html = [msg_err_numberof, msg_err_numberin].join("<br>");
                } else {
                    msg_html =  msg_err_numberof;
                };
            } else {
                if (msg_err_numberin) {
                    msg_html = msg_err_numberin;
                };
            }
            el_MENVLAB_number_err.innerHTML = msg_html;

        };

        el_MENVLAB_btn_save.disabled = (err_fields.length || is_addnew);

        return err_fields;
    };  // MENVLAB_validate_and_disable

//=========  MENVLAB_SetInputElements  ================  PR2022-08-18 PR2022-10-09
    function MENVLAB_SetInputElements() {
        console.log(" -----  MENVLAB_SetInputElements  ----");
        //console.log("mod_MENV_dict.parent_name", mod_MENV_dict.parent_name);
        //console.log("mod_MENV_dict", mod_MENV_dict);

        el_MENVLAB_name.value = (mod_MENV_dict.parent_name) ? mod_MENV_dict.parent_name : null;
        // numberinenvelop can be 0, only trap undefined or null with numberinenvelop != null
        el_MENVLAB_numberinenvelop.value = (mod_MENV_dict.numberinenvelop != null) ? mod_MENV_dict.numberinenvelop : null;
        el_MENVLAB_numberofenvelops.value = (mod_MENV_dict.numberofenvelops) ? mod_MENV_dict.numberofenvelops : null;

        add_or_remove_class(el_MENVLAB_variable_number.children[0], "tickmark_2_2", (mod_MENV_dict.is_variablenumber), "tickmark_1_1");
        add_or_remove_class(el_MENVLAB_errata.children[0], "tickmark_2_2", (mod_MENV_dict.is_errata), "tickmark_1_1");
        el_MENVLAB_numberinenvelop_label.innerText = ((mod_MENV_dict.is_variablenumber) ? loc.Max_number_in_envelop : loc.Number_in_envelop) + ":";
        el_MENVLAB_numberofenvelops.readOnly = (mod_MENV_dict.is_variablenumber);
    };  // MENVLAB_SetInputElements

    function MENVLAB_NoItems_txt(tblName){
        // PR2022-05-01
        const caption = (tblName === "student") ? (loc.Candidates) ? loc.Candidates.toLowerCase() : "" :
                        (tblName === "subject") ? (loc.Subjects) ? loc.Subjects.toLowerCase() : "" :
                        (tblName === "cluster") ? (loc.Clusters) ? loc.Clusters.toLowerCase() : "" :
                        (tblName === "school") ? (loc.Schools) ? loc.Schools.toLowerCase() : "" : "";
        return "<" + loc.No_ + caption + ">";
    }

// ++++++++++++  END OF MODAL ENVELOP LABEL  +++++++++++++++++++++++++++++++++++++++

//=========  MENVIT_Open  ================ PR2022-08-04 PR2022-09-21
    function MENVIT_Open(el_input) {
        console.log(" -----  MENVIT_Open   ----")

        //console.log("permit_dict.permit_crud", permit_dict.permit_crud)
        //console.log("el_input", el_input)

        // PR2022-09-13 debug. row in envelopitem_rows got empty because of b_clear_dict(mod_MENV_dict),
        // since mod_MENV_dict is referenced to row in envelopitem_rows.
        // using  b_clear_dict(mod_MENV_dict) clesrs row row in envelopitem_rows
        // setting mod_MENV_dict = {} breaks the reference
        // was: b_clear_dict(mod_MENV_dict);

        mod_MENV_dict = {};
        if (permit_dict.permit_crud){

            // el_input is undefined when called by submenu btn 'Add new'
            const is_addnew = (!el_input);

    //console.log("is_addnew", is_addnew)
            const tblName = "envelopitem";
            if(is_addnew){
                mod_MENV_dict = {is_addnew: is_addnew}
            } else {
                const tblRow = t_get_tablerow_selected(el_input);
// --- get existing data_dict from data_rows
                const pk_int = get_attr_from_el_int(tblRow, "data-pk");
                const [index, found_dict, compare] = b_recursive_integer_lookup(envelopitem_rows, "id", pk_int);
                if(!isEmpty(found_dict)) {
                    mod_MENV_dict = found_dict;
                    mod_MENV_dict.content_bold = (mod_MENV_dict.content_font && mod_MENV_dict.content_font.includes("Bold"));
                    mod_MENV_dict.content_italic = (mod_MENV_dict.content_font && mod_MENV_dict.content_font.includes("Italic"));
                    mod_MENV_dict.instruction_bold = (mod_MENV_dict.instruction_font && mod_MENV_dict.instruction_font.includes("Bold"));
                    mod_MENV_dict.instruction_italic = (mod_MENV_dict.instruction_font && mod_MENV_dict.instruction_font.includes("Italic"));
                };
            };

        console.log("mod_MENV_dict", mod_MENV_dict);

            // used in ModConfirm to delete, contains bundle, label or item pk
            selected.envelop_bundle_label_item_pk = (mod_MENV_dict && mod_MENV_dict.id) ? mod_MENV_dict.id : null;

            el_MENVIT_hdr.innerText = (mod_MENV_dict && mod_MENV_dict.content_nl) ? loc.Edit_label_item : loc.New_label_item;

            MENVIT_SetInputElements();
            MENVIT_SetMsgElements();
            MENVIT_SetFontElements();

            let modified_txt = null;
            if (!is_addnew){
                const modified_dateJS = parse_dateJS_from_dateISO(mod_MENV_dict.modifiedat);
                const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
                const modified_by = (mod_MENV_dict.modby_username) ? mod_MENV_dict.modby_username : "-";
                modified_txt = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by;
            };
            el_MENVIT_msg_modified.innerText = modified_txt;

    // ---  disable btn submit, hide delete btn when is_addnew
            el_MENVIT_btn_save.disabled = true;
            add_or_remove_class(el_MENVIT_btn_delete, cls_hide, is_addnew );

            MENVIT_disable_save_btn(true);

// show modal
            $("#id_mod_envelopitem").modal({backdrop: true});
        };
    };  // MENVIT_Open


//=========  MENVIT_Save  ================  PR2020-10-01 PR2022-09-21 PR2022-10-20
    function MENVIT_Save(crud_mode) {
        console.log(" -----  MENVIT_save  ----", crud_mode);
        console.log( "mod_MENV_dict: ", mod_MENV_dict);

        if (permit_dict.permit_crud){
            const is_create = (mod_MENV_dict.is_addnew);
            const is_delete = (crud_mode === "delete");
            const upload_mode = (is_create) ? "create" : (is_delete) ? "delete" : "update"

            let upload_dict = {table: 'envelopitem', mode: upload_mode}
            if(mod_MENV_dict.id){upload_dict.pk_int = mod_MENV_dict.id};
            //if(mod_MENV_dict.mapid){upload_dict.mapid = mod_MENV_dict.mapid};

    // ---  put changed values of input elements in upload_dict
            let new_level_pk = null, new_sector_pk = null, level_or_sector_has_changed = false;
            //let form_elements = document.getElementById("id_MSTUDSUBJ_div_form_controls").querySelectorAll(".awp_input_text, .awp_input_select")
            let form_elements = el_MENVIT_form_controls.getElementsByClassName("form-control")
            for (let i = 0, el_input; el_input = form_elements[i]; i++) {
                if (el_input.tagName !== "DIV"){
                    const fldName = get_attr_from_el(el_input, "data-field");
                    const new_value = (el_input.value) ? el_input.value : null;
                    const old_value = (mod_MENV_dict[fldName]) ? mod_MENV_dict[fldName] : null;

                    if (new_value !== old_value) {
                        upload_dict[fldName] = new_value;
                    };
                };
            };

    // ---  put changed values of DIV elements in upload_dict
            if (mod_MENV_dict.content_font_haschanged){
                 upload_dict.content_font =  (mod_MENV_dict.content_bold)
                                            ? (mod_MENV_dict.content_italic) ? "Bold_Italic" : "Bold"
                                            : (mod_MENV_dict.content_italic) ? "Italic" : null;
            };

            if (mod_MENV_dict.instruction_font_haschanged){
                 upload_dict.instruction_font =  (mod_MENV_dict.instruction_bold)
                                            ? (mod_MENV_dict.instruction_italic) ? "Bold_Italic" : "Bold"
                                            : (mod_MENV_dict.instruction_italic) ? "Italic" : null;
            };

            add_or_remove_class(el_MENVIT_loader, cls_hide, false);
            UploadChanges(upload_dict, urls.url_envelopitem_upload);
        };

    // ---  hide modal
            //$("#id_mod_envelopitem").modal("hide");
    } ; // MENVIT_Save

//========= MENVIT_InputKeyup  ============= PR2020-10-01
    function MENVIT_InputKeyup(el_input){
        //console.log( "===== MENVIT_InputKeyup  ========= ");
        MENVIT_disable_save_btn(false);
    }; // MENVIT_InputKeyup

//========= MENVIT_InputSelect  ============= PR2020-12-11
    function MENVIT_InputSelect(el_input){
        //console.log( "===== MENVIT_InputSelect  ========= ");
        MENVIT_disable_save_btn(false);
    }; // MENVIT_InputSelect


//========= MENVIT_InputToggle  ============= PR2022-10-19
    function MENVIT_InputToggle(el_input){
        console.log( "===== MENVIT_InputToggle  ========= ");
        console.log( "el_input", el_input);
        // only called by el with data-field content_bold,content_italic, instruction_bold, instruction_italic
        const fldName = get_attr_from_el(el_input, "data-field");
        const fldValue = (mod_MENV_dict[fldName]) ? mod_MENV_dict[fldName] : false;

        // toggle fldValue, put new value in mod_MENV_dict and el_input
        mod_MENV_dict[fldName] = !fldValue;
        add_or_remove_class(el_input.children[0], "tickmark_2_2", !fldValue, "tickmark_1_1")

        // put 'haschanged' in mod_MENV_dict, used when saving font
        if (fldName.includes("content")){
            mod_MENV_dict.content_font_haschanged = true;
        } else if (fldName.includes("instruction")){
            mod_MENV_dict.instruction_font_haschanged = true;
        };

        MENVIT_disable_save_btn(false);
    }; // MENVIT_InputToggle


//=========  MENVIT_disable_save_btn  ================  PR2022-09-28
    function MENVIT_disable_save_btn(disable_save_btn) {
        //console.log(" -----  MENVIT_disable_save_btn   ----")
// ---  disable save button on opening modal or on error
        el_MENVIT_btn_save.disabled = disable_save_btn;
    };  // MENVIT_disable_save_btn

//========= MENVIT_SetInputElements  ============= PR2022-08-04
    function MENVIT_SetInputElements(error_dict){
        //console.log( "===== MENVIT_SetInputElements  ========= ");
        //console.log( "mod_MENV_dict", mod_MENV_dict);

// --- loop through input elements
        let form_elements = el_MENVIT_form_controls.querySelectorAll(".form-control")
        for (let i = 0, el, fldName, fldValue; el = form_elements[i]; i++) {

            fldName = get_attr_from_el(el, "data-field");
            fldValue = (mod_MENV_dict[fldName]) ? mod_MENV_dict[fldName] : null;

            if(["bis_exam", "partial_exam", "iseveningstudent"].includes(fldName)){
                el.setAttribute("data-value", (fldValue) ? "1" : "0");
                const el_img = el.children[0];
                add_or_remove_class(el_img, "tickmark_2_2", !!fldValue, "tickmark_1_1")
            } else {
                el.value = fldValue;
            };
        };
    };  // MENVIT_SetInputElements


//========= MENVIT_SetFontElements  ============= PR2022-10-20
    function MENVIT_SetFontElements(){
        console.log( "===== MENVIT_SetFontElements  ========= ");
        console.log( "mod_MENV_dict", mod_MENV_dict);

// --- loop through input elements
        let form_elements = el_MENVIT_form_controls.querySelectorAll(".form-control")
        for (let i = 0, el, fldName, fldValue; el = form_elements[i]; i++) {
            fldName = get_attr_from_el(el, "data-field");
            if (["content_bold", "content_italic", "instruction_bold", "instruction_italic"].includes(fldName)){
                fldValue = !!mod_MENV_dict[fldName]
                add_or_remove_class(el.children[0], "tickmark_2_2", fldValue, "tickmark_1_1")
            };
        };
    };  // MENVIT_SetFontElements


//========= MENVIT_SetMsgElements  ============= PR2022-09-27
    function MENVIT_SetMsgElements(update_dict){
        //console.log( "===== MENVIT_SetMsgElements  ========= ");
        //console.log( "update_dict", update_dict);
        const error_dict = get_dict_value(update_dict, ["error"], []);
        const errordict_not_empty = !isEmpty(error_dict);

// --- loop through msg_err elements
        let els_msg = el_MENVIT_form_controls.querySelectorAll(".awp_msg_err")
        for (let i = 0, el, fldName; el = els_msg[i]; i++) {
            fldName = get_attr_from_el(el, "data-field");
            let err_txt = null;
            if(errordict_not_empty && fldName && fldName in error_dict){
                err_txt = error_dict[fldName];
            };
            el.innerHTML = err_txt;
        };

// --- loop through input elements
        const els_input = el_MENVIT_form_controls.querySelectorAll(".form-control")
        for (let i = 0, el, fldName; el = els_input[i]; i++) {
            fldName = get_attr_from_el(el, "data-field");
            const field_has_error = (errordict_not_empty && fldName && fldName in error_dict);
            add_or_remove_class(el, "border_bg_invalid", field_has_error)
        };

// ---  hide loader
        add_or_remove_class(el_MENVIT_loader, cls_hide, true);
// ---  disable save button on error
        MENVIT_disable_save_btn(!isEmpty(error_dict));

    };  // MENVIT_SetMsgElements

// +++++++++ MOD ENVELOP PRINT FORM++++++++++++++++ PR2022-08-20 PR2022-10-22 PR2023-03-16
    function MENVPR_Open(mode){
        console.log(" -----  MENVPR_Open   ----")
        console.log("    setting_dict.sel_examperiod", setting_dict.sel_examperiod)

        b_clear_dict(mod_MENV_dict);
        mod_MENV_dict.mode = mode;

// ---  reset tblBody available and selected
        if (mod_MENV_dict.mode !== "receipt" && ![1,2,3].includes(setting_dict.sel_examperiod)){
        // function b_show_mod_message_html(msg_html, header_text, ModMessageClose){
            b_show_mod_message_html("<div class='p-2'>" + loc.Please_select_examperiod_sbr + "</div>", loc.Download_envelop_labels);

        } else {
            mod_MENV_dict.sel_examperiod = setting_dict.sel_examperiod;
            let sel_department = null, sel_dep_lvl_req = false, sel_level = null;
            if (selected.depbase_pk){
                for (let i = 0, row; row = department_rows[i]; i++) {
                    if(row.base_id === selected.depbase_pk){
                        sel_department = row.base_code;
                        sel_dep_lvl_req = row.lvl_req;
                        break;
            }}};
            if (sel_dep_lvl_req){
                if (selected.lvlbase_pk && level_rows){
                    for (let i = 0, row; row = level_rows[i]; i++) {
                        if(row.base_id === selected.lvlbase_pk){
                            sel_level = row.lvlbase_code;
                            break;
                        }
                    };
                };
            };
            let header_txt = null;
            if (mod_MENV_dict.mode === "receipt"){
                header_txt = loc.Download_receipts;
                if (sel_department){header_txt += " - " + sel_department};
            } else if (mod_MENV_dict.mode === "label"){
                const examperiod_txt = (mod_MENV_dict.sel_examperiod) ? loc.examperiod_caption[mod_MENV_dict.sel_examperiod] : null;
                header_txt = loc.Download_envelop_labels
                if (sel_department){header_txt += " - " + sel_department};
                if (sel_level){header_txt += " " + sel_level};

                if (examperiod_txt){header_txt += " - " + examperiod_txt};;
            };
            el_MENVPR_header.innerText = header_txt;

    // ---  reset tblBody and layout options
            el_MENVPR_tblBody_school.innerHTML = null;
            el_MENVPR_tblBody_exam.innerHTML = null;
            el_MENVPR_select_errata.value = null;
            el_MENVPR_select_exam.value = null;
            el_MENVPR_msg_modified.innerText = null;

    // set focus to el_MENVPR_select_errata
            set_focus_on_el_with_timeout(el_MENVPR_select_errata)

    // ---  disable save btn
            el_MENVPR_btn_save.disabled = true;

    // ---  show only element for label or receipt
            const el_mod_envelop_print = document.getElementById("id_mod_envelop_print")
            const show_class = "mod_" + mod_MENV_dict.mode;
            b_show_hide_selected_elements_byClass("mod_show", show_class, el_mod_envelop_print);

    // ---  show modal
            $("#id_mod_envelop_print").modal({backdrop: true});
        };
    };  // MENVPR_Open

//========= MENVPR_Save  ============= PR2021-10-07 PR2022-10-10
    function MENVPR_Save(){
        console.log(" -----  MENVPR_Save   ----")
        const schoolbase_pk_list = [];
        const subjbase_pk_list = [];
        const envelopsubject_pk_list = [];

// ---  get de selected value of
        const selected_layout_value = (el_MENVPR_select_errata.value) ? el_MENVPR_select_errata.value : null;
    console.log("    selected_layout_value", selected_layout_value);

        const upload_dict = {mode: mod_MENV_dict.mode};

// ---  loop through mod_MENV_dict.school_rows and collect selected subject_pk's
        // PR2021-10-09 debug: also filter lvlbase_pk, because they stay selected when unselecting level
        if (mod_MENV_dict.school_rows && mod_MENV_dict.school_rows.length){
            if (mod_MENV_dict.all_schools_selected) {
                schoolbase_pk_list.push(-1);
            } else {
                for (let i = 0, school_row; school_row = mod_MENV_dict.school_rows[i]; i++) {
                    if(school_row.selected){
                        schoolbase_pk_list.push(school_row.sbase_id);
            }}};
        };
        upload_dict.schoolbase_pk_list = schoolbase_pk_list;

        if (mod_MENV_dict.mode === "receipt"){
            upload_dict.sel_exam = el_MENVPR_select_exam.value;
        } else {

    // ---  loop through mod_MENV_dict.envelopsubject_rows and collect selected subject_pk's
            // PR2021-10-09 debug: also filter lvlbase_pk, because they stay selected when unselecting level

            // envelopsubject_pk_list stays empty when all_envelopsubjects_selected
            if (!mod_MENV_dict.all_envelopsubjects_selected) {
                if (mod_MENV_dict.envelopsubject_rows && mod_MENV_dict.envelopsubject_rows.length){
                        for (let i = 0, exam_row; exam_row = mod_MENV_dict.envelopsubject_rows[i]; i++) {
                            if(exam_row.selected){
                                envelopsubject_pk_list.push(exam_row.id);
            }}}};
            upload_dict.envelopsubject_pk_list = envelopsubject_pk_list;
            upload_dict.sel_layout = selected_layout_value;
        };

        const url_str = (mod_MENV_dict.mode === "receipt") ? urls.url_envelop_receipt :
                        (mod_MENV_dict.mode === "label") ? urls.url_envelop_print : null;

    // convert dict to json and add as parameter in link
        const upload_str = JSON.stringify(upload_dict);
        const href_str = url_str.replace("-", upload_str);

        const el_MENVPR_save_link = document.getElementById("id_MENVPR_save_link");
        el_MENVPR_save_link.href = href_str;

        el_MENVPR_save_link.click();

// ---  hide modal
        //$("#id_mod_envelop_print").modal("hide");
    };  // MENVPR_Save

//========= MENVPR_getinfo_from_server  ============= PR2021-10-06 PR2023-03-24
    function MENVPR_getinfo_from_server(mode) {
        console.log("  =====  MENVPR_getinfo_from_server  =====");

        el_MENVPR_tblBody_school.innerHTML = null;
        el_MENVPR_tblBody_exam.innerHTML = null;

        el_MENVPR_loader.classList.remove(cls_hide);
        el_MENVPR_btn_save.disabled = true;

        UploadChanges({mode: mode}, urls.url_envelop_print_check);
    }  // MENVPR_getinfo_from_server

//========= MENVPR_UpdateFromResponse  ============= PR2022-08-19
    function MENVPR_UpdateFromResponse(response) {
        console.log("  =====  MENVPR_UpdateFromResponse  =====");
        console.log("response", response)

        el_MENVPR_loader.classList.add(cls_hide);

        mod_MENV_dict.envelopsubject_rows = (response.checked_envelopsubject_rows) ? response.checked_envelopsubject_rows : [];
        mod_MENV_dict.school_rows = (response.checked_envelop_school_rows) ? response.checked_envelop_school_rows : [];

        console.log("    mod_MENV_dict.school_rows", mod_MENV_dict.school_rows)
        console.log("    mod_MENV_dict.envelopsubject_rows", mod_MENV_dict.envelopsubject_rows)
        // = (response.sel_examperiod) ? response.sel_examperiod : null;
        //mod_MENV_dict.emod_MENV_dict.sel_examperiodxamperiod_caption = (response.examperiod_caption) ? response.examperiod_caption : "---";

        //mod_MENV_dict.lvlbase_pk_list = (response.lvlbase_pk_list) ? response.lvlbase_pk_list : [];

        // TODO save sel_layout in usersettings
       // el_MENVPR_select_errata.value = (response.sel_layout) ? response.sel_layout : null;

        MENVPR_FillTblSchool();
        MENVPR_FillTblExams();

// ---  set text on msg_modified
        let modified_text = null;
        if ("updated_enveloporderlist_modifiedat" in response){
            const modified_dateJS = parse_dateJS_from_dateISO(response.updated_enveloporderlist_modifiedat);
            const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS, true, false, true);
            modified_text = loc.The_orderlist_is_published_at + modified_date_formatted + ". " + loc.The_published_numbers_willbe_used;
        } else {
            modified_text = loc.The_orderlist_is_not_published + " " + loc.The_actual_numbers_willbe_used;
        };
        el_MENVPR_msg_modified.innerText = modified_text;

// ---  enable save btn
        MENVPR_EnableBtnSave();

    }  // MENVPR_UpdateFromResponse

//========= MENVPR_EnableBtnSave  ============= PR2023-03-16
    function MENVPR_EnableBtnSave() {

        const selected_school_rows = get_elements_by_classname_with_qsAll(el_MENVPR_tblBody_school, ".bg_selected_blue");
        const has_selected_school_rows = (selected_school_rows && selected_school_rows.length);

// ---  enable save btn
        let btn_save_disabled = true;
        if (has_selected_school_rows){
            if (mod_MENV_dict.mode === "receipt"){
                if (el_MENVPR_select_exam.value){
                    btn_save_disabled = false;
                };
            } else {
                const selected_subject_rows = get_elements_by_classname_with_qsAll(el_MENVPR_tblBody_exam, ".bg_selected_blue");
                const has_selected_subject_rows = (selected_subject_rows && selected_subject_rows.length);

                if (has_selected_subject_rows){
                    if (el_MENVPR_select_errata.value){
                        btn_save_disabled = false;
                    };
                };
            };
        };

       el_MENVPR_btn_save.disabled = btn_save_disabled;
    }  // MENVPR_EnableBtnSave


//========= MENVPR_SelectHasChanged  ============= PR2023-03-16
    function MENVPR_SelectHasChanged(mode) {
        if (mode === "errata"){
    // ---  get info from server when errata_only is checked
            const mode = (el_MENVPR_select_errata.value === "errata_only") ? "errata_only" : "check";
            MENVPR_getinfo_from_server(mode);
        };

        MENVPR_EnableBtnSave();
    }  // MENVPR_SelectHasChanged

//========= MENVPR_FillTblSchool  ============= PR2022-08-19
    function MENVPR_FillTblSchool() {
        //console.log("===== MENVPR_FillTblSchool ===== ");
        //console.log("mod_MENV_dict.school_rows", mod_MENV_dict.school_rows)

        const tblBody = el_MENVPR_tblBody_school
// ---  reset tblBody available and selected
        tblBody.innerText = null;

// ---  loop through mod_MENV_dict.school_rows
        let has_selected_school_rows = false;

        if (mod_MENV_dict.school_rows && mod_MENV_dict.school_rows.length){
            if (mod_MENV_dict.school_rows.length > 1){
                const all_row = {
                    sbase_id: -1,
                    sbase_code: " ",
                    sch_name: "<" + loc.All_ + loc.Schools.toLowerCase() + ">"
                };
                MENVPR_CreateSelectRow("schools", tblBody, all_row);
            }
            for (let i = 0, school_row; school_row = mod_MENV_dict.school_rows[i]; i++) {
                const depbases_list = (school_row.depbases) ? school_row.depbases.split(";") : []
                const show_row = (!selected.depbase_pk || depbases_list.includes(selected.depbase_pk.toString()));
                if (show_row){
                    const has_selected_schools = MENVPR_CreateSelectRow("schools", tblBody, school_row);
                    if(has_selected_schools) {has_selected_school_rows = true };
                };
            };
        };
    }; // MENVPR_FillTblSchool

//========= MENVPR_FillTblExams  ============= PR2022-08-23
    function MENVPR_FillTblExams() {
/*
        console.log("===== MENVPR_FillTblExams ===== ");
        console.log("    mod_MENV_dict.envelopsubject_rows", mod_MENV_dict.envelopsubject_rows);
        console.log("    mod_MENV_dict.sel_examperiod", mod_MENV_dict.sel_examperiod);
        console.log("    selected.depbase_pk", selected.depbase_pk);
        console.log("    selected.lvlbase_pk", selected.lvlbase_pk);
*/
        const tblBody = el_MENVPR_tblBody_exam;

// ---  reset tblBody available and selected
        tblBody.innerHTML = null;

// ---  loop through mod_MENV_dict.envelopsubject_rows
        if (mod_MENV_dict.envelopsubject_rows && mod_MENV_dict.envelopsubject_rows.length){
            if (mod_MENV_dict.envelopsubject_rows.length > 1){
                const all_row = {
                    id: -1,
                    depbase_code: " ",
                    subj_name_nl: "<" + loc.All_ + loc.Subjects.toLowerCase() + ">",
                    version: "",
                    examperiod: ""
                };
                MENVPR_CreateSelectRow("exams", tblBody, all_row);
            }
        //console.log("mod_MENV_dict.sel_examperiod", mod_MENV_dict.sel_examperiod);
            for (let i = 0, row; row = mod_MENV_dict.envelopsubject_rows[i]; i++) {
                const show_row = (row.examperiod === mod_MENV_dict.sel_examperiod) &&
                                (!selected.depbase_pk || row.depbase_id === selected.depbase_pk) &&
                                (!selected.lvlbase_pk || row.lvlbase_id === selected.lvlbase_pk);

        //console.log("row", row);
                if (show_row){
                    const has_selected_exams = MENVPR_CreateSelectRow("exams", tblBody, row);
                    if(has_selected_exams) {exam_rows = true };
                };
            };
        };
    }; // MENVPR_FillTblExams

//========= MENVPR_CreateSelectRow  ============= PR2022-08-19
    function MENVPR_CreateSelectRow(tblName, tblBody, row_dict) {
        //console.log("===== MENVPR_CreateSelectRow ===== ");
    //console.log("row_dict", row_dict);

        const is_schools = (tblName === "schools");
// - get ifo from dict
        const pk_int = (is_schools) ? row_dict.sbase_id : row_dict.id;

        let code = (is_schools) ?  (row_dict.sbase_code) ? row_dict.sbase_code : "---" :
                                   (row_dict.depbase_code) ? row_dict.depbase_code : "---";
        if (!is_schools && row_dict.lvl_abbrev) { code += " " + row_dict.lvl_abbrev }

        const name = (is_schools) ? (row_dict.sch_name) ? row_dict.sch_name : "---" :
                                   (row_dict.subj_name_nl) ? row_dict.subj_name_nl : "---";
        const version = (!is_schools && row_dict.version) ? row_dict.version : "";
        const is_selected = (row_dict.selected) ? row_dict.selected : false;

// ---  lookup index where this row must be inserted
        const dep_sequence = (row_dict.dep_sequence) ? row_dict.dep_sequence : 0;
        const lvl_sequence = (row_dict.lvl_sequence) ? row_dict.lvl_sequence : 0;
        const ob1 = (is_schools) ? code : dep_sequence.toString();
        const ob2 = name;
        const ob3 = (is_schools) ? "" : lvl_sequence.toString();
        const row_index = b_recursive_tblRow_lookup(tblBody, setting_dict.user_lang, ob1, ob2, ob3);

// --- insert tblRow into tblBody at row_index
        const tblRow = tblBody.insertRow(row_index);

// --- add data attributes to tblRow
        tblRow.setAttribute("data-table", tblName);
        tblRow.setAttribute("data-pk", pk_int);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);
        tblRow.setAttribute("data-ob2", ob2);
        tblRow.setAttribute("data-ob3", ob3);

        //add_or_remove_class(tblRow, cls_selected, is_selected)
        add_or_remove_class(tblRow, "bg_selected_blue", is_selected)

//- add hover to select row
        add_hover(tblRow)

// --- add first td to tblRow.
        let td = tblRow.insertCell(-1);
        let el_div = document.createElement("div");
            el_div.classList.add("tw_090")
            el_div.innerText = code;
            td.appendChild(el_div);

// --- add second td to tblRow.
        const tw = (is_schools) ? "tw_360" : "tw_240";
        td = tblRow.insertCell(-1);
        el_div = document.createElement("div");
            el_div.classList.add(tw)
            el_div.innerText = name;
            td.appendChild(el_div);

        if (!is_schools){

// --- add examperiod td to tblRow.
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                el_div.classList.add("tw_060", "ta_c")
                el_div.innerText = (row_dict.examperiod) ? "tv " + row_dict.examperiod : null;
                td.appendChild(el_div);
        }

//----- add addEventListener
        tblRow.addEventListener("click", function() {MENVPR_SelectDeselectRow(is_schools, tblRow)}, false);

    } // MENVPR_CreateSelectRow

//========= MENVPR_SelectDeselectRow  ============= PR2022-08-19
    function MENVPR_SelectDeselectRow(is_schools, tblRow) {
        //console.log("  =====  MENVPR_SelectDeselectRow  =====");
        //console.log("tblRow", tblRow);

        const tblBody = tblRow.parentNode;
        const pk_int = get_attr_from_el_int(tblRow, "data-pk");

        let has_changed = false;
        const data_rows = (is_schools) ? mod_MENV_dict.school_rows : mod_MENV_dict.envelopsubject_rows;
        const set_all_rows = (pk_int === -1);

        if (set_all_rows) {
            const new_selected = !tblRow.classList.contains("bg_selected_blue");

            if (is_schools) {
                mod_MENV_dict.all_schools_selected = new_selected;
            } else {
                mod_MENV_dict.all_envelopsubjects_selected = new_selected;
            };

            for (let i = 0, row_dict; row_dict = data_rows[i]; i++) {
                row_dict.selected = new_selected
            };
            //add_or_remove_class(tblRow, "bg_selected_blue", new_selected)

            for (let j = 0, row; row = tblBody.rows[j]; j++) {
                add_or_remove_class(row, "bg_selected_blue", new_selected);
            };

        } else {
            for (let i = 0, row_dict; row_dict = data_rows[i]; i++) {
                const row_pk_int = (is_schools) ? row_dict.sbase_id : row_dict.id;
                if (row_pk_int === pk_int){
                    // set selected = true when clicked in list 'available', set false when clicked in list 'selected'
                    const new_selected = (row_dict.selected) ? false : true;
                    row_dict.selected = new_selected
                    row_dict.just_selected = true;
                    has_changed = true;

                    add_or_remove_class(tblRow, "bg_selected_blue", new_selected)
                    // when deselect and all-schools is selected: als deselct all_schools
                    if (!new_selected){
                        if (is_schools) {
                            mod_MENV_dict.all_schools_selected = false;
                        } else {
                            mod_MENV_dict.all_envelopsubjects_selected = false;
                        };
                        const first_row = tblBody.rows[0];
                        if (first_row){
                            const first_row_pk_int = get_attr_from_el_int(first_row, "data-pk")
                            if (first_row_pk_int === -1){
                                add_or_remove_class(first_row, "bg_selected_blue", false);
                            };
                        };
                    };
                    break;
                };
            };
        };
        MENVPR_EnableBtnSave();
    };  // MENVPR_SelectDeselectRow


// +++++++++++++++++ MODAL ORDERLIST EXTRA EXAMS +++++++++++++++++++++++++++++++++++++++++++
//=========  MOLEX_Open  ================ PR2021-08-31
    function MOLEX_Open() {
        //console.log(" -----  MOLEX_Open   ----")

        if(permit_dict.permit_crud && setting_dict.sel_examyear_pk){
            const map_dict = get_mapdict_from_datamap_by_tblName_pk(examyear_map, "examyear", setting_dict.sel_examyear_pk)

            mod_dict = deepcopy_dict(map_dict);

            const el_MOLEX_form_controls = document.getElementById("id_MOLEX_form_controls")
            if(el_MOLEX_form_controls){
                const form_elements = el_MOLEX_form_controls.querySelectorAll(".awp_input_number")
                for (let i = 0, el; el = form_elements[i]; i++) {
                    const field = get_attr_from_el(el, "data-field");
                    el.value = mod_dict[field];
                };
            };


// --- loop through school_map, to look up ETE /DEX school PR2021-09-26
            let admin_name = null;
            for (const [map_id, map_dict] of school_map.entries()) {
                if(map_dict.country_id === permit_dict.requsr_country_pk && map_dict.defaultrole === 64) {
                    admin_name = (map_dict.article) ? map_dict.article + ' ' + map_dict.name : map_dict.name;
                    break;
                };
            };
            if(!admin_name) {admin_name = loc.the_exam_bureau}

            const el_MOLEX_admin_label = document.getElementById("id_MOLEX_admin_label")
        //console.log("el_MOLEX_admin_label", el_MOLEX_admin_label)
        //console.log("loc.Extra_exams + loc._for_ + admin_name", loc.Extra_exams + loc._for_ + admin_name)
            el_MOLEX_admin_label.innerText = loc.Extra_exams + loc._for_ + admin_name;
        };

// show modal
        $("#id_mod_orderlist_extra").modal({backdrop: true});

    };  // MOLEX_Open

//=========  MOLEX_Save  ================  PR2021-08-31
    function MOLEX_Save() {
        //console.log(" -----  MOLEX_Save   ----")

        if(permit_dict.permit_crud && setting_dict.sel_examyear_pk){
            const upload_dict = {};
            const el_MOLEX_form_controls = document.getElementById("id_MOLEX_form_controls")
            if(el_MOLEX_form_controls){
                const form_elements = el_MOLEX_form_controls.querySelectorAll(".awp_input_number")
                for (let i = 0, el; el = form_elements[i]; i++) {
                    const field = get_attr_from_el(el, "data-field");
                    const value_int = Number(el.value)
                    if (value_int !== mod_dict[field]){
                        upload_dict[field] = value_int;
                    }
                };
// ---  Upload Changes
                if (!isEmpty(upload_dict)){
                    UploadChanges(upload_dict, urls.url_orderlist_parameters);
                };
            };
        };

// hide modal
        $("#id_mod_orderlist_extra").modal("hide");

    };  // MOLEX_Save
//###########################################################################
// +++++++++++++++++ REFRESH DATA ROWS +++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataRows  ================  PR2021-06-21 PR2022-08-04 PR2022-09-28
    function RefreshDataRows(tblName, data_rows, update_rows, is_update) {
        // called by  UploadChanges response  "updated_envelopbundle_rows",  "updated_enveloplabel_rows",  "updated_envelopitem_rows", updated_envelopsubject_rows

        //console.log(" --- RefreshDataRows  ---");
        //console.log("    tblName", tblName);
        //console.log("    data_rows", data_rows);
        //console.log("    update_rows", update_rows);

        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length
        if (update_rows && update_rows.length ) {
            const field_setting = field_settings[tblName];
            for (let i = 0, update_dict; update_dict = update_rows[i]; i++) {
                RefreshDatarowItem(tblName, field_setting, data_rows, update_dict);
            }
        } else if (!is_update) {
            // empty the data_rows when update_rows is empty PR2021-01-13 debug forgot to empty data_rows
            // PR2021-03-13 debug. Don't empty de data_rows when is update. Returns [] when no changes made
           data_rows = [];
        };
    };  //  RefreshDataRows


//=========  RefreshDatarowItem  ================
    //PR2020-08-16 PR2020-09-30 PR2021-06-21 PR2022-08-14 PR2022-09-27
    function RefreshDatarowItem(tblName, field_setting, data_rows, update_dict) {
        //console.log(" --- RefreshDatarowItem  ---");
    //console.log("    data_rows", data_rows);
    //console.log("    update_dict", update_dict);
    //console.log("    field_setting.field_names", field_setting.field_names);

        if(!isEmpty(update_dict)){
            // add color fields to fieldnames when tblName = "envelopitem"
            // _color is used in modal from, _hexcol is used in tblRow
            const field_names = (tblName === "envelopitem") ?
                ["content_color", "instruction_color", "content_hexcolor", "instruction_hexcolor", "content_font", "instruction_font"] : [];
            if(field_setting.field_names && field_setting.field_names.length){
                // use i < len, otherwise loop stops at first blank item ""
                for (let i = 0, len = field_setting.field_names.length; i < len; i++) {
                    const field_name = field_setting.field_names[i];
                    if (field_name){
                        field_names.push(field_name);
                    };
                };
            };

    //console.log("  >>>  field_names", field_names);
            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);

            let updated_columns = [];
            let field_error_list = []

            const error_dict = get_dict_value(update_dict, ["error"], []);
            if(!isEmpty(error_dict)){
                MENVIT_SetMsgElements(update_dict);
            } else {
// hide modal when no error
                $("#id_mod_envelopitem").modal("hide");
            };

// ---  get list of hidden columns
            const col_hidden = b_copy_array_to_new_noduplicates(mod_MCOL_dict.cols_hidden);

// ---  get list of columns that are not updated because of errors
            // NIU??
            const error_columns = (update_dict.err_fields) ? update_dict.err_fields : [];

// ++++ created ++++
            // PR2021-06-16 from https://stackoverflow.com/questions/586182/how-to-insert-an-item-into-an-array-at-a-specific-index-javascript
            // arr.splice(index, 0, item); will insert item into arr at the specified index
            // (deleting 0 items first, that is, it's just an insert).

            if(is_created){
    // ---  first remove key 'created' from update_dict
                delete update_dict.created;

    // --- lookup index where new row must be inserted in data_rows
                // PR2021-06-21 not necessary, new row has always pk higher than existing. Add at end of rows

    // ---  add new item in data_rows at end
                data_rows.push(update_dict);

    // ---  create row in table., insert in alphabetical order
                const new_tblRow = CreateTblRow(tblName, field_setting, col_hidden, update_dict)

    // ---  scrollIntoView,
                if(new_tblRow){
                    new_tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' })

    // ---  make new row green for 2 seconds,
                    ShowOkElement(new_tblRow);
                };
            } else {

// +++ get existing data_dict from data_rows
                const pk_int = (update_dict && update_dict.id) ? update_dict.id : null;
                const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);
                const data_dict = (!isEmpty(found_dict)) ? found_dict : null;
                const datarow_index = index;

    //console.log("    data_dict", data_dict);
// ++++ deleted ++++
                if(is_deleted){
    // --- delete row from data_rows. Splice returns array of deleted rows
                    const deleted_row_arr = data_rows.splice(datarow_index, 1)
                    const deleted_row_dict = deleted_row_arr[0];

    // ---  when delete: make tblRow red for 2 seconds, before uploading
                    // is done in ModConfirmSave

    // --- delete tblRow
                    const tblRow_tobe_deleted = document.getElementById(update_dict.mapid);
                    tblRow_tobe_deleted.parentNode.removeChild(tblRow_tobe_deleted)

                } else {

    //console.log("    +++++++++++ updated row +++++++++++");

// +++++++++++ updated row +++++++++++
    // ---  check which fields are updated, add to list 'updated_columns'
                    if(!isEmpty(data_dict) && field_names){

                        copy_updatedict_to_datadict(data_dict, update_dict, field_names, updated_columns);
    //console.log("    updated_columns", updated_columns);
    //console.log("    data_dict", data_dict);


    // -- when font field has changed: also add textfield to update_dict, to show green
                        if (updated_columns.includes("content_font")){
                            updated_columns.push("content_nl");
                        };
                        if (updated_columns.includes("instruction_font")){
                            updated_columns.push("instruction_nl");
                        };

    // -- when color field has changed: also add textfield to update_dict, to show green
                        if (updated_columns.includes("content_hexcolor")){
                            updated_columns.push("content_nl");
                        };
                        if (updated_columns.includes("instruction_hexcolor")){
                            updated_columns.push("instruction_nl");
                        };
       // - also update field download when bundle_name has changed
                        if (updated_columns.includes("bundle_name")){
                            updated_columns.push("download");
                        };
        // ---  update field in tblRow
                        // note: when updated_columns is empty, then updated_columns is still true.
                        // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
                        if(updated_columns.length || field_error_list.length){

// --- get existing tblRow
                            let tblRow = document.getElementById(map_id);
                            if(tblRow){

    // - loop through cells of row
                                for (let i = 1, el_fldName, el, td; td = tblRow.cells[i]; i++) {
                                    el = td.children[0];
                                    if (el){
        //console.log("el", el);
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
                                    };  //  if (el){
                                };  //  for (let i = 1, el_fldName, el; el = tblRow.cells[i]; i++) {
                            };  // if(tblRow){
                        }; //  if(updated_columns.length){
                    };  //  if(!isEmpty(update_dict))
                };  //  if(is_deleted)
            }; // if(is_created)
        };  // if(!isEmpty(update_dict))
    };  // RefreshDatarowItem

//###########################################################################
// +++++++++++++++++ REFRESH DATA MAP ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataMap  ================ PR2020-08-16 PR2020-09-30 PR2021-08-31
    function RefreshDataMap(tblName, field_names, data_rows, data_map) {
        //console.log(" --- RefreshDataMap  ---");
        //console.log("data_rows", data_rows);
        if (data_rows) {
            const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
            for (let i = 0, update_dict; update_dict = data_rows[i]; i++) {
                RefreshDatamapItem(tblName, field_names, update_dict, data_map);
            };
        };
    };  //  RefreshDataMap

//=========  RefreshDatamapItem  ================ PR2020-08-16 PR2020-09-30 PR2021-03-15
    function RefreshDatamapItem(tblName, field_names, update_dict, data_map) {
        //console.log(" --- RefreshDatamapItem  ---");
        //console.log("update_dict", update_dict);
        if(!isEmpty(update_dict)){
            const map_id = update_dict.mapid;
            data_map.set(map_id, update_dict)
        //console.log("data_map", data_map);
        }
    };  // RefreshDatamapItem


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
            Filter_TableRows();
        }
    }; // function HandleFilterKeyup

//========= HandleFilterField  ====================================
    function HandleFilterField(el_filter, col_index, event) {
        //console.log( "===== HandleFilterField  ========= ");
        // skip filter if filter value has not changed, update variable filter_text

        //console.log( "el_filter", el_filter);
        //console.log( "col_index", col_index);
        const filter_tag = get_attr_from_el(el_filter, "data-filtertag")
        //console.log( "filter_tag", filter_tag);

// --- get filter tblRow and tblBody
        const tblRow = t_get_tablerow_selected(el_filter);
        const tblName = "orderlist"  // tblName = get_attr_from_el(tblRow, "data-table")
        //console.log( "tblName", tblName);

// --- reset filter row when clicked on 'Escape'
        const skip_filter = t_SetExtendedFilterDict(el_filter, col_index, filter_dict, event.key);

        Filter_TableRows();
    }; // HandleFilterField

//========= ShowTableRow  ==================================== PR2022-08-16
    function ShowTableRow(envelopsubject_dict) {
        // this function filters rows when they are created, called bij SBR examperiod, department level
        // it uses 'selected' dict, filter is not stored in settings
        // only used in envelopsubject_rows
/*
        console.log( "===== ShowTableRow  ========= ");
        console.log( "selected", selected);
        console.log( "    selected.examperiod", selected.examperiod, typeof selected.examperiod);
        console.log( "    selected.depbase_pk", selected.depbase_pk, typeof selected.depbase_pk);
        console.log( "    selected.lvlbase_pk", selected.lvlbase_pk, typeof selected.lvlbase_pk);
        console.log( "    selected.subject_pk", selected.subject_pk, typeof selected.subject_pk);
        console.log( "    envelopsubject_dict", envelopsubject_dict);
*/
        if (envelopsubject_dict.examperiod > 1){
            console.log( "  >>>>>>>  envelopsubject_dict.examperiod", envelopsubject_dict.examperiod, typeof envelopsubject_dict.examperiod);

        };
        let hide_row = false;

    //console.log( "    envelopsubject_dict.examperiod", envelopsubject_dict.examperiod, typeof envelopsubject_dict.examperiod);
        // 12 is used to select all exam periods
        if (!hide_row && selected.examperiod && selected.examperiod !== 12){
            hide_row = (selected.examperiod !== envelopsubject_dict.examperiod);
        };
        if (!hide_row && selected.depbase_pk){
            hide_row = (selected.depbase_pk !== envelopsubject_dict.depbase_id);
        };
        if (!hide_row && selected.lvlbase_pk){
            hide_row = (selected.lvlbase_pk !== envelopsubject_dict.lvlbase_id);
        };
        if (!hide_row && selected.subject_pk){
            hide_row = (selected.subject_pk !== envelopsubject_dict.subject_id);
        };
    //console.log( "hide_row", hide_row, typeof hide_row);
       return !hide_row
    }; // ShowTableRow


//========= Filter_TableRows  ==================================== PR2021-07-08
    function Filter_TableRows() {
        //console.log( "===== Filter_TableRows  ========= ");

        for (let i = 0, tblRow, show_row; tblRow = tblBody_datatable.rows[i]; i++) {
            tblRow = tblBody_datatable.rows[i]
            show_row = t_Filter_TableRow_Extended(filter_dict, tblRow);
            add_or_remove_class(tblRow, cls_hide, !show_row)
        };

    }; // Filter_TableRows

//========= ResetFilterRows  ====================================
    function ResetFilterRows() {  // PR2019-10-26 PR2020-06-20 PR2022-08-04
        //console.log( "===== ResetFilterRows  ========= ");

        b_clear_dict(selected);
        b_clear_dict(filter_dict);
        b_clear_dict(mod_MENV_dict);

        filter_mod_employee = false;

        el_SBR_select_examperiod.value = 12;
        el_SBR_select_department.value = null;
        el_SBR_select_level.value = null;

        // resetting usersettin not working properly dont know why, not necessary PR2022-09-04
        //const upload_dict = {selected_pk: {sel_depbase_pk: null, sel_lvlbase_pk: null, sel_examperiod: null}};
        //console.log( "upload_dict", upload_dict);
        //b_UploadSettings (upload_dict, urls.url_usersetting_upload);

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
            }}}}};
        };

        FillTblRows();
    };  // function ResetFilterRows

///////////////////////////////////////////////////////////////////

//=========   MPUBORD_OpenLogfile   ====================== PR2021-07-17
    function MPUBORD_OpenLogfile() {
        //console.log(" ========== MPUBORD_OpenLogfile ===========");

        if (!!mod_MPUBORD_dict.log_list && mod_MPUBORD_dict.log_list) {
            const today = new Date();
            const this_month_index = 1 + today.getMonth();
            const date_str = today.getFullYear() + "-" + this_month_index + "-" + today.getDate();
            let filename = "Log bestellijst dd " + date_str + ".pdf";
        //console.log("filename", filename);
            printPDFlogfile(mod_MPUBORD_dict.log_list, filename )
        };
    }; //MPUBORD_OpenLogfile



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
                //student_rows: {get: true},
                //studentsubject_rows: {get: true},
                //schemeitem_rows: {get: true}
            };
        DatalistDownload(datalist_request);

    };  // MSED_Response

//=========  get_datarows_from_selectedbtn  ================ PR2022-08-04 PR2022-10-09
    function get_datarows_from_selectedbtn() {
        const data_rows = (selected_btn === "btn_orderlist") ? orderlist_rows :
                        (selected_btn === "btn_envelopsubject") ? envelopsubject_rows :
                        (selected_btn === "btn_bundle") ? envelopbundle_rows :
                        (selected_btn === "btn_label") ? enveloplabel_rows :
                        (selected_btn === "btn_item") ? envelopitem_rows : [];
        return data_rows;
    };

//=========  get_tblName_from_selectedbtn  ================ PR2022-08-04 PR2022-10-09
    function get_tblName_from_selectedbtn() {
        //console.log("selected_btn", selected_btn)
        const tblName = (selected_btn === "btn_orderlist") ? "orderlist" :
                        (selected_btn === "btn_envelopsubject") ? "envelopsubject" :
                        (selected_btn === "btn_bundle") ? "envelopbundle" :
                        (selected_btn === "btn_label") ? "enveloplabel" :
                        (selected_btn === "btn_item") ? "envelopitem" : null;
        return tblName;
    };

})  // document.addEventListener('DOMContentLoaded', function()