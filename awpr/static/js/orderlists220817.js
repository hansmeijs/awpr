// PR2020-09-29 added

// envelopbundle_rows is made global to show in t_MSSSS_Save
let envelopbundle_rows = [];

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

    let level_rows = [];

    let subject_map = new Map();
    let subject_rows = [];

    let ete_exam_rows = [];
    let orderlist_rows = [];
    // envelopbundle_rows is made global to show in t_MSSSS_Save
    //let envelopbundle_rows = [];
    let enveloplabel_rows = [];
    let envelopitem_rows = [];
    let enveloplabelitem_rows = [];
    let envelopbundlelabel_rows = [];

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
    urls.url_envelopitem_upload = get_attr_from_el(el_data, "data-url_envelopitem_upload");
    urls.url_enveloplabel_upload = get_attr_from_el(el_data, "data-url_enveloplabel_upload");
    urls.url_envelopbundle_upload = get_attr_from_el(el_data, "data-url_envelopbundle_upload");
    urls.url_envelop_print = get_attr_from_el(el_data, "data-url_envelop_print");
    urls.url_exam_upload = get_attr_from_el(el_data, "data-url_exam_upload");

    mod_MCOL_dict.columns.btn_orderlist = {
        school_abbrev: "School_name", total_students: "Number_of_candidates",
        total: "Number_of_entered_subjects", publ_count: "Number_of_submitted_subjects", datepublished: "Date_submitted"
    };
    mod_MCOL_dict.columns.btn_ete_exam = {
        subj_name_nl : "Subject",
        depbase_code : "Department",
        lvl_abbrev : "Learning_path",
        version : "Version",
        secret_exam : "Designated_exam",
        datum : "Date",
        begintijd : "Start_time",
        eindtijd : "End_time"
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

        ete_exam: { field_caption: ["", "Abbrev_subject_2lines", "Subject", "Department", "Learning_path", "Version",
                                "Exam_period", "Designated_exam_2lines", "Date", "Start_time", "End_time",  "Label_bundle", ""],
                field_names: ["select", "subjbase_code", "subj_name_nl", "depbase_code", "lvl_abbrev", "version",
                                "examperiod", "secret_exam", "datum", "begintijd", "eindtijd", "bundle_name", "download"],
                field_tags: ["div", "div", "div", "div", "div", "div", "div", "div", "input", "input", "input", "div", "div", "div"],
                filter_tags: ["text",  "text", "text", "text", "text", "text", "text", "toggle", "text", "text", "text", "text", ""],
                field_width: ["020", "075", "240", "120", "120", "120", "150", "090", "120", "120", "120", "240", "060"],
                field_align: ["c", "c", "l", "c", "c", "l", "c", "c", "c", "c", "c", "l", "c"]
                },

        envelopbundle: {field_caption: ["", "Bundle_name"],
                    field_names: ["select", "name"],
                    field_tags: ["div", "div"],
                    filter_tags: ["", "text"],
                    field_width:  ["020", "240"],
                    field_align: ["c", "l"]
                    },
        enveloplabel: {field_caption: ["", "Label_name", "Number_of_envelops", "Exams_per_envelop"],
                    field_names: ["select", "name", "numberfixed", "numberperexam"],
                    field_tags: ["div", "div", "div", "div"],
                    filter_tags: ["", "text", "text","text"],
                    field_width:  ["020", "240", "120", "120"],
                    field_align: ["c", "l", "c",  "c"]
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

// ---  SIDEBAR ------------------------------------
        const el_SBR_select_examperiod = document.getElementById("id_SBR_select_period");
        if (el_SBR_select_examperiod){el_SBR_select_examperiod.addEventListener("change", function() {HandleSBRselect("examperiod", el_SBR_select_examperiod)}, false )};

        const el_SBR_select_department = document.getElementById("id_SBR_select_department");
        if (el_SBR_select_department){el_SBR_select_department.addEventListener("change", function() {HandleSBRselect("department", el_SBR_select_department)}, false)};

        const el_SBR_select_level = document.getElementById("id_SBR_select_level");
        if(el_SBR_select_level){el_SBR_select_level.addEventListener("change", function() {HandleSBRselect("level", el_SBR_select_level)}, false )};

        const el_SBR_select_subject = document.getElementById("id_SBR_select_subject");
        if(el_SBR_select_subject){el_SBR_select_subject.addEventListener("click",
                function() {t_MSSSS_Open(loc, "subject", subject_map, true, false, setting_dict, permit_dict, MSSSS_Response)}, false)};

        const el_SBR_select_showall = document.getElementById("id_SBR_select_showall");
        if(el_SBR_select_showall){el_SBR_select_showall.addEventListener("click", function() {HandleShowAll()}, false)};

// ---  MSSS MOD SELECT SCHOOL / SUBJECT / STUDENT ------------------------------
        const el_MSSSS_btn_delete = document.getElementById("id_MSSSS_btn_delete");
        if (el_MSSSS_btn_delete){
            el_MSSSS_btn_delete.addEventListener("click", function() {MSSSS_remove_bundle()}, false );
        }

// ---  MOD PUBLISH ORDERLIST ------------------------------------
        const el_MPUBORD_info_container = document.getElementById("id_MPUBORD_info_container");
        const el_MPUBORD_loader = document.getElementById("id_MPUBORD_loader");
        const el_MPUBORD_input_verifcode = document.getElementById("id_MPUBORD_input_verifcode");
        if (el_MPUBORD_input_verifcode){
            el_MPUBORD_input_verifcode.addEventListener("keyup", function() {MPUBORD_InputVerifcode(el_MPUBORD_input_verifcode, event.key)}, false);
            el_MPUBORD_input_verifcode.addEventListener("change", function() {MPUBORD_InputVerifcode(el_MPUBORD_input_verifcode)}, false);
        };
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
        const el_MENVLAB_number_container = document.getElementById("id_MENVLAB_number_container");

        const el_MENVLAB_tblBody_available = document.getElementById("id_MENVLAB_tblBody_available");
        const el_MENVLAB_tblBody_selected = document.getElementById("id_MENVLAB_tblBody_selected");

        const el_MENVLAB_name = document.getElementById("id_MENVLAB_name");
        if(el_MENVLAB_name){el_MENVLAB_name.addEventListener("keyup", function() {MENVLAB_InputKeyup(el_MENVLAB_name)}, false)}
        const el_MENVLAB_numberfixed = document.getElementById("id_MENVLAB_numberfixed");
        if(el_MENVLAB_numberfixed){el_MENVLAB_numberfixed.addEventListener("keyup", function() {MENVLAB_InputKeyup(el_MENVLAB_numberfixed)}, false)}
        const el_MENVLAB_numberperexam = document.getElementById("id_MENVLAB_numberperexam");
        if(el_MENVLAB_numberperexam){el_MENVLAB_numberperexam.addEventListener("keyup", function() {MENVLAB_InputKeyup(el_MENVLAB_numberperexam)}, false)}

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
                //} else if(el.tagName === "DIV"){
                //    el.addEventListener("click", function() {MENVIT_InputToggle(el)}, false );
                };
            };
        };
        const el_MENVIT_btn_delete = document.getElementById("id_MENVIT_btn_delete");
        if(el_MENVIT_btn_delete){el_MENVIT_btn_delete.addEventListener("click", function() {ModConfirmOpen("delete_envelopitem")}, false)}
        const el_MENVIT_btn_save = document.getElementById("id_MENVIT_btn_save");
        if(el_MENVIT_btn_save){ el_MENVIT_btn_save.addEventListener("click", function() {MENVIT_Save("save")}, false)}


// ---  MOD EX3 FORM ------------------------------------
    const el_MENVPR_hdr = document.getElementById("id_MENVPR_hdr");
    const el_MENVPR_loader = document.getElementById("id_MENVPR_loader");
    const el_MENVPR_select_layout = document.getElementById("id_MENVPR_select_layout");
    const el_MENVPR_layout_option_level = document.getElementById("id_MENVPR_layout_option_level");

    const el_MENVPR_select_level = document.getElementById("id_MENVPR_select_level");
    if (el_MENVPR_select_level){
        el_MENVPR_select_level.addEventListener("change", function() {MENVPR_SelectLevelHasChanged()}, false )
    }
    const el_MENVPR_tblBody_available = document.getElementById("id_MENVPR_tblBody_available");
    const el_MENVPR_tblBody_selected = document.getElementById("id_MENVPR_tblBody_selected");
    const el_MENVPR_btn_save = document.getElementById("id_MENVPR_btn_save");
    if (el_MENVPR_btn_save){
        el_MENVPR_btn_save.addEventListener("click", function() {MENVPR_Save()}, false )
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
                locale: {page: ["page_studsubj", "page_subject", "page_student", "upload", "page_orderlist"]},
                examyear_rows: {get: true},
                school_rows: {get: true},
                department_rows: {show_all_deps: true},
                level_rows: {get: true},

                ete_exam_rows: {show_all: true},
                orderlist_rows: {get: true},
                envelopbundle_rows: {get: true},
                enveloplabel_rows: {get: true},
                envelopitem_rows: {get: true},
                enveloplabelitem_rows: {get: true},
                envelopbundlelabel_rows: {get: true}
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
                    selected_btn = (setting_dict.sel_btn)
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

                if ("ete_exam_rows" in response) {
                    ete_exam_rows = response.ete_exam_rows
                };
                if ("orderlist_rows" in response)  {
                    orderlist_rows = response.orderlist_rows;
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

                //AddSubmenuButton(el_submenu, loc.Print_labels, function() {MENVPR_Open()}, ["tab_show", "tab_btn_ete_exam", "tab_btn_bundle"]);
            };
            AddSubmenuButton(el_submenu, loc.Hide_columns, function() {t_MCOL_Open("page_orderlist")}, [], "id_submenu_columns")

            el_submenu.classList.remove(cls_hide);
        };

    };//function CreateSubmenu

//###########################################################################
//=========  HandleBtnSelect  ================ PR2020-09-19  PR2020-11-14 PR2022-08-12
    function HandleBtnSelect(data_btn, skip_upload) {
        //console.log( "===== HandleBtnSelect ========= ", data_btn);

// - to prevent error when not in use button retrieved from saved setting
        if(!["btn_orderlist", "btn_ete_exam", "btn_bundle", "btn_label", "btn_item"].includes(data_btn)){
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
        HandleSBRselect()

// ---  fill datatable
        FillTblRows();

// --- update header text
        UpdateHeaderText();
    }  // HandleBtnSelect

//=========  HandleTblRowClicked  ================ PR2020-08-03 PR2022-08-04
    function HandleTblRowClicked(tr_clicked) {
        console.log("=== HandleTblRowClicked");
        console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

// ---  deselect all highlighted rows, select clicked row
        t_td_selected_toggle(tr_clicked, true);  // select_single = true

// --- get existing data_dict from data_rows
        const pk_int = get_attr_from_el_int(tr_clicked, "data-pk");
        const tblName = get_attr_from_el_int(tr_clicked, "data-table");
        const data_rows = get_datarows_from_selectedbtn();
    //console.log( "pk_int: ", pk_int, typeof pk_int);
    //console.log( "data_rows: ", data_rows, typeof data_rows);

        const [index, data_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);
    console.log( "data_dict: ", data_dict, typeof data_dict);

        if (selected_btn === "btn_orderlist") {
            selected.envelopitem_pk = (!isEmpty(data_dict)) ? data_dict.id : null;
        } else if (selected_btn === "btn_ete_exam") {
            selected.ete_exam_pk = (!isEmpty(data_dict)) ? data_dict.id : null;

        } else if(!["envelopbundle", "enveloplabel", "envelopitem"].includes(tblName)){
            selected.envelop_bundle_label_item_pk = (!isEmpty(data_dict)) ? data_dict.id : null;
        };
    console.log( "selected: ", selected);
    };  // HandleTblRowClicked

//=========  HandleSBRselect  ================ PR2022-08-16
    function HandleSBRselect(tblName, el_select) {
        console.log("===== HandleSBRselect =====");
    console.log( "tblName: ", tblName);

        if (tblName === "examperiod") {

            selected.examperiod = (el_select && Number(el_select.value)) ? Number(el_select.value) : null;
            setting_dict.sel_examperiod = selected.examperiod;

    // ---  upload new setting
            const upload_dict = {selected_pk: {sel_examperiod: setting_dict.sel_examperiod}};
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);
        };


        const is_dep = (tblName === "department");
        const is_lvl = (tblName === "level");
        const pk_int = (el_select && Number(el_select.value)) ? Number(el_select.value) : null;
        const data_rows = (is_dep) ? department_rows : level_rows;
        const [index, data_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);
        console.log( "data_dict: ", data_dict)

        selected.level_req = is_lvl;

        // reset sbr department when tblName is blank, otherwise: update
        if (is_dep || tblName == null ) {
            selected.department_pk = null;
            if (!isEmpty(data_dict)) {
                selected.department_pk = data_dict.id;
                if(data_dict.lvl_req) { selected.level_req = true };
            };
        };

        // show leerweg only when dep is set to vsbo
        if (!selected.level_req){
            selected.level_pk =  null;
            if (el_SBR_select_level){ el_SBR_select_level.value = null};
        };
        add_or_remove_class(el_SBR_select_level.parentNode, cls_hide, !selected.level_req );

        // reset sbr level when tblName is blank, otherwise: update
        if (is_lvl || tblName == null ){
            selected.level_pk = null;
            if (!isEmpty(data_dict)) {
                selected.level_pk = data_dict.id;
            };
        };
        FillTblRows();
    } ; // HandleSBRselect


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
                ete_exam_rows: {get: true}
        };

        DatalistDownload(datalist_request);
    };  // HandleSbrLevel

//=========  FillOptionsExamperiod  ================ PR2021-03-08 PR2022-08-16
    function FillOptionsExamperiod() {
        console.log("=== FillOptionsExamperiod");
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
            const sel_abbrev = (el_SBR_select.options[el_SBR_select.selectedIndex]) ? el_SBR_select.options[el_SBR_select.selectedIndex].innerText : null;
            if (tblName === "level"){
                setting_dict.sel_level_abbrev = sel_abbrev;
            } else if (tblName === "sector"){
                setting_dict.sel_sector_abbrev = sel_abbrev;
            };
        };
    };  // FillOptionsSelectLevelSector


//=========  SBR_FillSelectOptions  ================ PR2021-03-06  PR2021-05-21 PR2022-08-16
    function SBR_FillSelectOptions(tblName) {
        //console.log("=== SBR_FillSelectOptions");
        //console.log("tblName", tblName);
        if(["department", "level"].includes(tblName)){
            const is_dep = (tblName === "department");
            const data_rows = (is_dep) ? department_rows : level_rows;

            const caption_all = "&#60" + ((is_dep) ? loc.All_departments : loc.All_levels) + "&#62";

            let found_in_new_list = false;
            const display_rows = [];
            let count = 0;
            if (data_rows){
                for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
                    display_rows.push({
                        // value is dep_id or lvl_is, not depbase_id / levelbase_id
                        // this is necessary to lookup selected item in rows
                        // but base_id will be put in 'selected' variable and sent to server
                        value: data_dict.id,
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
                    display_rows.unshift({value: 0, caption: caption_all })
                };
            };
            const selected_pk = (is_dep) ? selected.depbase_pk : selected.lvlbase_pk;
            const el_SBR_select = (is_dep) ? el_SBR_select_department : el_SBR_select_level;
            t_FillOptionsFromList(el_SBR_select, display_rows, "value", "caption", null, null, selected_pk)

        // show select level
            if (!is_dep){
                add_or_remove_class(el_SBR_select_level.parentNode, cls_hide, !count);
            };
        };
    };  // SBR_FillSelectOptions


//=========  HandleShowAll  ================ PR2020-12-17
    function HandleShowAll() {
        console.log("=== HandleShowAll");

        setting_dict.sel_level_pk = null;
        setting_dict.sel_department_pk = null;

        setting_dict.sel_lvlbase_pk = null;
        setting_dict.sel_level_abbrev = null;
        setting_dict.sel_lvlbase_pk = null;

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
                ete_exam_rows: {get: true}
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
        //console.log( "===== FillTblRows  === ");
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
                const show_row = (tblName === "ete_exam") ? ShowTableRow(data_dict) : true;
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
    //console.log("field_names", field_names);

// ---  lookup index where this row must be inserted
        const ob1 = (tblName === "orderlist") ? (data_dict.schbase_code) ? data_dict.schbase_code : "" :
                    (tblName === "ete_exam") ? (data_dict.subjbase_code) ? data_dict.subjbase_code : "" :
                    (tblName === "envelopbundle") ? (data_dict.name) ? data_dict.name : "" :
                    (tblName === "enveloplabel") ? (data_dict.name) ? data_dict.name : "" :
                    (tblName === "envelopitem") ? (data_dict.content_nl) ? data_dict.content_nl : "" : "";

        const ob2 = (tblName === "ete_exam") ? (data_dict.depbase_code) ? data_dict.depbase_code : "" :
                    (tblName === "envelopitem") ? (data_dict.instruction_nl) ? data_dict.instruction_nl : "" : "";

        const ob3 = (tblName === "ete_exam") ? (data_dict.lvl_abbrev) ? data_dict.lvl_abbrev : ""  : "";

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
                if (["datum", "begintijd", "eindtijd"].includes(field_name)){
                    const el_type = (field_name === "datum") ? "date" : "text";
                    el.setAttribute("type", el_type)
                    el.setAttribute("autocomplete", "off");
                    el.setAttribute("ondragstart", "return false;");
                    el.setAttribute("ondrop", "return false;");
                    el.classList.add("input_text");

                    el.addEventListener("change", function() {UploadInputChange(tblName, el)}, false);
                    //el.addEventListener("keydown", function(event){HandleArrowEvent(el, event)});

                } else if (["content_nl", "instruction_nl"].includes(field_name)){
                    td.addEventListener("click", function() {MENVIT_Open(el)}, false)
                    td.classList.add("pointer_show");
                    add_hover(td);
                } else if (["name", "numberperexam", "numberfixed"].includes(field_name)){
                    td.addEventListener("click", function() {MENVLAB_Open(tblName, el)}, false)
                    td.classList.add("pointer_show");
                    add_hover(td);
                } else if (field_name === "bundle_name"){
                    td.addEventListener("click", function() {MSSSS_Open(td)}, false)
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
                if (field_name === "secret_exam"){
                    filter_value = (fld_value) ? "1" : "0";
                    el_div.className = (fld_value) ? "tickmark_1_2" : "tickmark_0_0";
                } else  if (["datum", "begintijd", "eindtijd"].includes(field_name)){
                    el_div.value = fld_value;

                } else if (field_name === "url"){
                    if (fld_value){
                        el_div.href = fld_value;
                    } else {
                        el_div.innerHTML = "&emsp;&emsp;&emsp;&emsp;-&emsp;&emsp;&emsp;&emsp;";
                        el_div.title = loc.File_not_found;
                    }

                } else if (field_name === "download"){
                    el_div.innerHTML = (data_dict.bundle_id) ? "&emsp;&#8681;&emsp;" : "&emsp;";
                } else {
                    el_div.innerText = (fld_value) ? fld_value : "\n";
                    if (["content_nl", "instruction_nl"].includes(field_name)){
                        const hex_color = (field_name === "content_nl" && data_dict.content_hexcolor) ?
                                data_dict.content_hexcolor :
                            (field_name === "instruction_nl" && data_dict.instruction_hexcolor) ?
                                data_dict.instruction_hexcolor :
                                "#000000";
    //console.log("hex_color", hex_color);
                        el_div.style.color = hex_color;
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
                selected.ete_exam_pk = pk_int
                const [index, data_dict, compare] = b_recursive_integer_lookup(ete_exam_rows, "id", pk_int);
            console.log("data_dict: ", data_dict);

                if (data_dict){

                const data_field = get_attr_from_el(el_input, "data-field");
        console.log("data_field: ", data_field, typeof data_field);
    // --- get new_value
                    const new_value = el_input.value
        console.log("new_value: ", new_value, typeof new_value);

                    let upload_dict = {
                        table: "ete_exam",
                        mode: "update",
                        examyear_pk: data_dict.subj_examyear_id,
                        exam_pk: data_dict.id,
                        subject_pk: data_dict.subj_id,
                    };
                    upload_dict[data_field] = new_value;
                    console.log( "upload_dict: ", upload_dict);
                    const url_str = urls.url_exam_upload ;
                    UploadChanges(upload_dict, url_str);
                };
            };
        };
    }  // UploadInputChange


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

                    if ("messages" in response) {
                        b_show_mod_message_dictlist(response.messages);
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

                    if ("updated_ete_exam_rows" in response) {
                        RefreshDataRows("ete_exam", ete_exam_rows, response.updated_ete_exam_rows, true)  // true = update
                    };

                    if ("publish_orderlist_msg_html" in response) {
                        MPUBORD_UpdateFromResponse(response);
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
//=========  ModConfirmOpen  ================ PR2021-08-22 PR2022-08-04
    function ModConfirmOpen(mode, tblRow) {
        console.log(" -----  ModConfirmOpen   ----")
        console.log("mode", mode)
        // values of mode are : "prelim_orderlist", "orderlist_per_school",
        // "download", "delete_envelopbundle", "delete_enveloplabel", "delete_envelopitem"
        // "delete_bundle_or_label"
        console.log("mod_MENV_dict", mod_MENV_dict)
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

// +++ delete_envelopitem +++
        } else if (["delete_envelopbundle", "delete_enveloplabel", "delete_envelopitem"].includes(mode)) {
            const is_bundle = (mode === "delete_envelopbundle");
            const is_label = (mode === "delete_enveloplabel");
            console.log( "is_bundle: ", is_bundle);
            console.log( "is_label: ", is_label);

            const header_txt = (is_bundle) ? loc.Delete_bundle : (is_label) ? loc.Delete_label : loc.Delete_label_item;

// --- get existing data_dict from data_rows

        console.log("selected", selected)
            // envelop_bundle_label_item_pk, contains bundle, label or item pk;
            const pk_int = selected.envelop_bundle_label_item_pk;
            const data_rows = (is_bundle) ? envelopbundle_rows : (is_label) ? enveloplabel_rows : envelopitem_rows;

            const [index, data_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);
            console.log( "data_dict: ", data_dict);

            if (isEmpty(data_dict)){
                const msg_txt = (is_bundle) ? loc.Please_select_bundle : (is_label) ? loc.Please_select_label : loc.Please_select_label_item;
                b_show_mod_message_html(msg_txt, header_txt);

            } else {
                const tblName = (is_bundle) ?  "envelopbundle" : (is_label) ?  "enveloplabel" : "envelopitem";
                mod_dict = {
                    mode: mode,
                    table: tblName,
                    parent_pk: data_dict.id,
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

// +++ delete_envelopitem +++
        } else if (mode === "download") {
            const is_bundle = (mode === "delete_envelopbundle");
            const is_label = (mode === "delete_enveloplabel");
            console.log( "is_bundle: ", is_bundle);
            console.log( "is_label: ", is_label);

            const header_txt = loc.Print_labels;

// --- get existing data_dict from data_rows
            const pk_int = get_attr_from_el_int(tblRow, "data-pk");
            const [index, data_dict, compare] = b_recursive_integer_lookup(ete_exam_rows, "id", pk_int);
            console.log( "data_dict: ", data_dict);

// skip if no tblRow selected or if exam has no envelopbundle
            if (!isEmpty(data_dict) || !data_dict.bundle_id){
                const tblName = (is_bundle) ?  "ete_exam" : (is_label) ?  "enveloplabel" : "envelopitem";
                mod_dict = {
                    mode: mode,
                    table: "ete_exam",
                    exam_pk: data_dict.id,
                    subject_pk: data_dict.subj_id,
                    envelopbundle_pk: data_dict.bundle_id
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
    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2021-08-22
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
            close_modal_with_timout = true;

        } else if (["delete_envelopbundle", "delete_enveloplabel", "delete_envelopitem"].includes(mod_dict.mode)) {
            if (permit_dict.permit_crud){
                const is_bundle = (mod_dict.mode === "delete_envelopbundle");
                const is_label = (mod_dict.mode === "delete_enveloplabel");
                let upload_dict = {
                    table: mod_dict.table,
                    mode: "delete",
                    parent_pk: mod_dict.parent_pk
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
                exam_pk: mod_dict.exam_pk
                //subject_list: [mod_dict.subject_pk],
                //lvlbase_pk_list: sel_lvlbase_pk_list
            };

        console.log("upload_dict", upload_dict)
        // convert dict to json and add as parameter in link
            const upload_str = JSON.stringify(upload_dict);
            const href_str = urls.url_envelop_print.replace("-", upload_str);
        console.log("href_str", href_str)

            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            el_modconfirm_link.href = href_str;
        console.log("el_modconfirm_link", el_modconfirm_link)

            el_modconfirm_link.click();

    // ---  hide modal
            if(close_modal_with_timout) {
            // close modal after 5 seconds
                setTimeout(function (){ $("#id_mod_confirm").modal("hide") }, 5000);
            } else {
                $("#id_mod_confirm").modal("hide");
        console.log("close_modal_with_timout", close_modal_with_timout)
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


//========= MODAL PUBLISH ORDERLIST ================ PR2021-09-08
    function MPUBORD_Open (open_mode ) {
        console.log("===  MPUBORD_Open  =====") ;
        console.log("setting_dict", setting_dict) ;
        mod_MPUBORD_dict = {}

        if (permit_dict.permit_submit_orderlist) {

            mod_MPUBORD_dict = {step: -1} // increases value 1 in MPUBORD_Save

// ---  reset and hide el_MPUBORD_input_verifcode
            add_or_remove_class(el_MPUBORD_input_verifcode.parentNode, cls_hide, true);
            el_MPUBORD_input_verifcode.value = null;

// ---   hide loader
            // PR2021-01-21 debug 'display_hide' not working when class 'image_container' is in same div
            add_or_remove_class(el_MPUBORD_loader, cls_hide, true);

            MPUBORD_Save ("save", true);  // true = is_test
            // this one is also in MPUBORD_Save:
            // MPUBORD_SetInfoboxesAndBtns();

            $("#id_mod_publish_orderlist").modal({backdrop: true});
        }
    };  // MPUBORD_Open

//=========  MPUBORD_Save  ================ PR2021-09-08
    function MPUBORD_Save () {
        //console.log("===  MPUBORD_Save  =====") ;

        if (permit_dict.permit_submit_orderlist) {
            mod_MPUBORD_dict.step += 1;
            const upload_dict = { table: "orderlist", now_arr: get_now_arr()};
            if (mod_MPUBORD_dict.step === 1){
                UploadChanges(upload_dict, urls.url_orderlist_request_verifcode);
            } else if (mod_MPUBORD_dict.step === 3){
                upload_dict.mode = "submit_save";
                upload_dict.verificationcode = el_MPUBORD_input_verifcode.value
                upload_dict.verificationkey = mod_MPUBORD_dict.verificationkey;
                UploadChanges(upload_dict, urls.url_orderlist_publish);
            }
            MPUBORD_SetInfoboxesAndBtns() ;
        } ;
    };  // MPUBORD_Save


//========= MPUBORD_UpdateFromResponse ================ PR2021-09-08
    function MPUBORD_UpdateFromResponse(response) {
        console.log( " ==== MPUBORD_UpdateFromResponse ====");
        console.log( "response", response);
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

        MPUBORD_SetInfoboxesAndBtns (response);

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
        const step = mod_MPUBORD_dict.step;
        const is_response = (!!response);
        const has_error = (is_response && response.error);

        console.log("step", step) ;
        console.log("response", response) ;

// ---  info_container, loader, info_verifcode and input_verifcode
        let msg_html = null, msg_info_txt = null, show_loader = false;
        let show_info_request_verifcode = false, show_input_verifcode = false;
        let disable_save_btn = false, save_btn_txt = null;

        if (response && response.publish_orderlist_msg_html) {
            msg_html = response.publish_orderlist_msg_html;
        };
        console.log("msg_html", msg_html);

        if (step === 0) {
            // step 0: when form opens
            msg_info_txt = [loc.MPUBORD_info.request_verifcode_01,
                loc.MPUBORD_info.request_verifcode_02,
                loc.MPUBORD_info.request_verifcode_03,
                " ",
                loc.MPUBORD_info.request_verifcode_04,
                loc.MPUBORD_info.request_verifcode_05,
                loc.MPUBORD_info.request_verifcode_06
            ].join("<br>");
            save_btn_txt = loc.Request_verifcode;
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
        } else if (step === 3) {
            // when clicked on 'Publish orderlist'
            msg_info_txt = loc.MPUBORD_info.Publishing_orderlist + "...";
            show_loader = true;
        } else if (step === 4) {
            // when response 'orderlist submitted' is received
            // msg_html is in response

            show_loader = false;
            show_input_verifcode = false;

        }

        console.log("save_btn_txt", save_btn_txt) ;
        console.log("msg_info_txt", msg_info_txt) ;
        if (msg_info_txt){
            msg_html = "<div class='p-2 border_bg_transparent'><p class='pb-2'>" +  msg_info_txt + "</p></div>";
        }
        //console.log("msg_html", msg_html) ;
        el_MPUBORD_info_container.innerHTML = msg_html;
        add_or_remove_class(el_MPUBORD_info_container, cls_hide, !msg_html)

        add_or_remove_class(el_MPUBORD_loader, cls_hide, !show_loader)

        add_or_remove_class(el_MPUBORD_input_verifcode.parentNode, cls_hide, !show_input_verifcode);
        if (show_input_verifcode){set_focus_on_el_with_timeout(el_MPUBORD_input_verifcode, 150); };

// - hide save button when there is no save_btn_txt
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
//=========  MSSSS_Open  ================  PR2022-08-12
    function MSSSS_Open(td) {
        console.log(" ----- MSSSS_Open ----")
        console.log("td", td)
        const tblRow = t_get_tablerow_selected(td);

// --- get existing data_dict from data_rows
        const pk_int = get_attr_from_el_int(tblRow, "data-pk");
        console.log("pk_int", pk_int)
        selected.ete_exam_pk = pk_int

        const [index, data_dict, compare] = b_recursive_integer_lookup(ete_exam_rows, "id", pk_int);
        setting_dict.envelopbundle_pk = (data_dict.bundle_id) ? data_dict.bundle_id : null;

        t_MSSSS_Open(loc, "envelopbundle", envelopbundle_rows, false, true, setting_dict, permit_dict, MSSSS_Response);

    };  // MSSSS_Open

//=========  MSSSS_Response  ================  PR2022-08-12
    function MSSSS_Response(tblName, selected_dict, selected_pk_int) {
        console.log(" ----- MSSSS_Response ----")
        console.log("tblName", tblName)
        console.log("selected_dict", selected_dict)
        console.log("selected_pk_int", selected_pk_int)
        console.log("selected", selected)

        if (permit_dict.permit_crud){
    // --- get selected ete_exam
            const pk_int = selected.ete_exam_pk;
            const [index, data_dict, compare] = b_recursive_integer_lookup(ete_exam_rows, "id", pk_int);
            console.log( "data_dict: ", data_dict);
            console.log( "selected: ", selected);
            if (data_dict){
                let upload_dict = {
                    table: "ete_exam",
                    mode: "update",
                    examyear_pk: data_dict.subj_examyear_id,
                    exam_pk: data_dict.id,
                    subject_pk: data_dict.subj_id,
                    envelopbundle_pk: selected_pk_int
                };
                console.log( "upload_dict: ", upload_dict);
                const url_str = urls.url_exam_upload ;
                UploadChanges(upload_dict, url_str);
            };
        };
    };

//=========  MSSSS_remove_bundle  ================  PR2022-08-13
    function MSSSS_remove_bundle() {
        console.log(" ----- MSSSS_remove_bundle ----")
        console.log("selected", selected)

        if (permit_dict.permit_crud){
// --- get selected ete_exam
            const pk_int = selected.ete_exam_pk;
            const [index, data_dict, compare] = b_recursive_integer_lookup(ete_exam_rows, "id", pk_int);

// --- set envelopbundle_pk null
            if (data_dict){
                let upload_dict = {
                    table: "ete_exam",
                    mode: "update",
                    examyear_pk: data_dict.subj_examyear_id,
                    exam_pk: data_dict.id,
                    subject_pk: data_dict.subj_id,
                    envelopbundle_pk: null
                };
                console.log( "upload_dict: ", upload_dict);
                const url_str = urls.url_exam_upload ;
                UploadChanges(upload_dict, url_str);
            };
        };
    };  // MSSSS_remove_bundle

// ++++++++++++  MODAL ENVELOP LABEL  +++++++++++++++++++++++++++++++++++++++

//=========  MENVLAB_Open  ================  PR2022-08-06
    function MENVLAB_Open(tblName, el_input) {
        console.log(" -----  MENVLAB_Open   ----")

        console.log("permit_dict.permit_crud", permit_dict.permit_crud)
        console.log("el_input", el_input)

        mod_MENV_dict = {};

        if (permit_dict.permit_crud){
            // el_input is undefined when called by submenu btn 'Add new'
            mod_MENV_dict.is_addnew = (!el_input);
            mod_MENV_dict.is_bundle = (tblName === "envelopbundle")
        console.log("mod_MENV_dict", mod_MENV_dict)
// --- get existing data_dict from enveloplabel_rows
            if(!mod_MENV_dict.is_addnew){
                const tblRow = t_get_tablerow_selected(el_input);
                const pk_int = get_attr_from_el_int(tblRow, "data-pk");

                const data_rows = (mod_MENV_dict.is_bundle) ? envelopbundle_rows : enveloplabel_rows;
                const [index, data_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);
        console.log("data_dict", data_dict)

                if (!isEmpty(data_dict)) {
                    mod_MENV_dict.parent_pk = data_dict.id;
                    mod_MENV_dict.parent_name = data_dict.name;
                    mod_MENV_dict.numberfixed = data_dict.numberfixed;
                    mod_MENV_dict.numberperexam = data_dict.numberperexam;
                    mod_MENV_dict.modby_username = data_dict.modby_username;
                    mod_MENV_dict.modifiedat = data_dict.modifiedat;
                }
            };
            // used in ModConfirm to delete, contains bundle, label or item pk
            selected.envelop_bundle_label_item_pk = (mod_MENV_dict.parent_pk) ? mod_MENV_dict.parent_pk : null;

        console.log("mod_MENV_dict", mod_MENV_dict)
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

            if (!mod_MENV_dict.is_addnew){
                const modified_dateJS = parse_dateJS_from_dateISO(mod_MENV_dict.modifiedat);
                const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
                const modified_by = (mod_MENV_dict.modby_username) ? mod_MENV_dict.modby_username : "-";
                const display_txt = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by;
                document.getElementById("id_MENVIT_msg_modified").innerText = display_txt;
            };

    // ---  disable btn submit, hide delete btn when is_addnew
            el_MENVLAB_btn_delete.innerText = (mod_MENV_dict.is_bundle) ?loc.Delete_bundle : loc.Delete_label;
            add_or_remove_class(el_MENVLAB_btn_delete, cls_hide, mod_MENV_dict.is_addnew );

            MENVLAB_validate_and_disable();

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
            const upload_mode = (is_create) ? "create" : (is_delete) ? "delete" : "update"

    // ---  put changed values of input elements in upload_dict
            const parent_name = el_MENVLAB_name.value;
            const numberfixed = (el_MENVLAB_numberfixed.value && Number(el_MENVLAB_numberfixed.value)) ? Number(el_MENVLAB_numberfixed.value) : null;
            const numberperexam = (el_MENVLAB_numberperexam.value && Number(el_MENVLAB_numberperexam.value)) ? Number(el_MENVLAB_numberperexam.value) : null;

            let upload_dict = {
                table: (mod_MENV_dict.is_bundle) ? "envelopbundle" : "enveloplabel",
                mode: upload_mode,
                parent_pk: mod_MENV_dict.parent_pk,
                name: parent_name
            };

            const uniontable_list = [];

// loop through uniontable items (envelopbundlelabel or enveloplabelitem)
            for (let i = 0, picklis_dict; picklis_dict = mod_MENV_dict.picklist[i]; i++) {
                // only add items that:
                //  - have uniontable_pk is null and selected = true (these are created items)
                // when bundle: have uniontable_pk not null and selected = false (these are deleted items)
                // when label:  have uniontable_pk not null ( to catch removed items and also items whose sequence has changed)
                const add_to_list = ( (!picklis_dict.uniontable_pk && !!picklis_dict.selected) || (
                                     (mod_MENV_dict.is_bundle) ? (!!picklis_dict.uniontable_pk && !picklis_dict.selected) :
                                                                 (!!picklis_dict.uniontable_pk) ) );

    //console.log( "picklis_dict.uniontable_pk: ", picklis_dict.uniontable_pk);
    //console.log( "picklis_dict.selected: ", picklis_dict.selected);
    //console.log( "add_to_list: ", add_to_list);
                if (add_to_list){
                    const item_dict = {
                        picklist_pk: picklis_dict.picklist_pk,
                        uniontable_pk: picklis_dict.uniontable_pk,
                        selected: picklis_dict.selected
                    };
                    if (!mod_MENV_dict.is_bundle) {
                        item_dict.sequence = picklis_dict.uniontable_sequence;
                    };
                    uniontable_list.push(item_dict);
                };
            };
            if (!mod_MENV_dict.is_bundle) {
                upload_dict.numberfixed = numberfixed;
                upload_dict.numberperexam = numberperexam;
                if (uniontable_list && uniontable_list.length){
                    upload_dict.uniontable = uniontable_list;
                };
            } else {
                if (uniontable_list && uniontable_list.length){
                    upload_dict.uniontable = uniontable_list;
                };
            };

            const url_str = (mod_MENV_dict.is_bundle) ? urls.url_envelopbundle_upload : urls.url_enveloplabel_upload;
            UploadChanges(upload_dict, url_str);
        };
    // ---  hide modal
            $("#id_mod_enveloplabel").modal("hide");
    } ; // MENVLAB_Save

    function MENVLAB_FillDictlist(){
       //console.log(" -----  MENVLAB_FillDictlist   ----")

// - reset picklist
        mod_MENV_dict.picklist = [];

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
    //console.log("    picklist_pk", picklist_pk)
    //console.log("    picklist_sortby", picklist_sortby)

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
            mod_MENV_dict.picklist.push({
                picklist_pk: picklist_pk,
                uniontable_pk: uniontable_pk,
                uniontable_sequence: uniontable_sequence,
                sortby: (picklist_sortby) ? picklist_sortby : "",
                selected: is_selected
            });
        };
        mod_MENV_dict.picklist.sort(b_comparator_sortby);

    //console.log("mod_MENV_dict", mod_MENV_dict)
    };  // MENVLAB_FillDictlist

//========= MENVLAB_FillTable  ============= PR2022-08-06
    function MENVLAB_FillTable(just_linked_unlinked_pk) {
        console.log("===== MENVLAB_FillTable ===== ");

        el_MENVLAB_tblBody_available.innerText = null;
        el_MENVLAB_tblBody_selected.innerText = null;

        const data_rows = mod_MENV_dict.picklist;
        if (data_rows && data_rows.length) {
            for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
            console.log("data_dict", data_dict);
            console.log("data_dict.selected", data_dict.selected);
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

//--- get info from data_dict
        const pk_int = (data_dict.picklist_pk) ? data_dict.picklist_pk : null;
        const caption = (data_dict.sortby) ? data_dict.sortby : "---";

    //console.log("   pk_int", pk_int);
    //console.log("   caption", caption);
        const is_just_linked = (pk_int === just_linked_unlinked_pk);

// ---  lookup index where this row must be inserted
        // available items are sorted by name (sortby), selected items are sorted by sequence
        const ob1 = (data_dict.selected && data_dict.sequence) ? ("0000" + data_dict.sequence).slice(-4) : "0000";
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
            el_div.classList.add("pointer_show")
            el_div.innerText = caption;
            el_div.classList.add("tw_240", "px-1")
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
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                el_div.classList.add("tw_020")
                el_div.innerHTML = "&#9661;"
                el_div.title = loc.Click_to_move_item_down;
            td.appendChild(el_div);
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
                    just_linked_unlinked_pk = data_dict.picklist_pk;
                    break;
                };
            };
    //console.log( "just_linked_unlinked_pk", just_linked_unlinked_pk);

        MENVLAB_FillTable(just_linked_unlinked_pk);

        console.log( "mod_MENV_dict.items", mod_MENV_dict.items);
// ---  save and close
            //MENVLAB_Save();
        }
    }  // MENVLAB_SelectItem

//=========  MENVLAB_InputKeyup  ================ PR2022-08-08
    function MENVLAB_InputKeyup(el_input) {
        //console.log( "===== MENVLAB_InputKeyup  ========= ");
        const fldName = get_attr_from_el(el_input, "data-field");
// ---  get value of new_filter
        let new_value = el_input.value;
        console.log( "new_value", new_value);
        if(!new_value) {

        } else {

            if (["numberperexam", "numberfixed"].includes(fldName)) {
                if(!Number(new_value)){
                    el_input.value = null;
        //console.log( "not Number");
                } else {
                    const value_number = Number(new_value);
        //console.log( "value_number", value_number);
                    if(!Number.isInteger(value_number)){
                        el_input.value = null;
        //console.log( "not Number.isInteger");
                    } else {
                        if (!value_number){
                            el_input.value = null;
                        } else {
                            if (fldName === "numberperexam") {
                                mod_MENV_dict.numberperexam = value_number;
                                mod_MENV_dict.numberfixed = null;
                                el_MENVLAB_numberfixed.value = null;
                            } else if (fldName === "numberfixed") {
                                mod_MENV_dict.numberfixed = value_number;
                                mod_MENV_dict.el_MENVLAB_numberperexam = null;
                                el_MENVLAB_numberperexam.value = null;
                            };
                        };
                    };
                };
            } else {
            //el_MENVLAB_name
            };
        };
    }; // MENVLAB_InputKeyup

//=========  MENVLAB_validate_and_disable  ================  PR2022-08-06
    function MENVLAB_validate_and_disable(crud_mode) {
        console.log(" -----  MENVLAB_validate_and_disable  ----", crud_mode);
        console.log( "mod_MENV_dict: ", mod_MENV_dict);
    };  // MENVLAB_validate_and_disable

//=========  MENVLAB_SetInputElements  ================  PR2022-08-08
    function MENVLAB_SetInputElements() {
        el_MENVLAB_name.value = (mod_MENV_dict.name) ? mod_MENV_dict.name : null;
        el_MENVLAB_numberfixed.value = (mod_MENV_dict.numberfixed) ? mod_MENV_dict.numberfixed : null;
        el_MENVLAB_numberperexam.value = (mod_MENV_dict.numberperexam) ? mod_MENV_dict.numberperexam : null;
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

//=========  MENVIT_Open  ================ PR2022-08-04
    function MENVIT_Open(el_input) {
        //console.log(" -----  MENVIT_Open   ----")

        console.log("permit_dict.permit_crud", permit_dict.permit_crud)
        console.log("el_input", el_input)

        mod_MENV_dict = {};

        if (permit_dict.permit_crud){

            // el_input is undefined when called by submenu btn 'Add new'
            const is_addnew = (!el_input);

            const tblName = "envelopitem";
            if(is_addnew){
                mod_MENV_dict = {is_addnew: is_addnew}
            } else {
                const tblRow = t_get_tablerow_selected(el_input);
// --- get existing data_dict from data_rows
                const pk_int = get_attr_from_el_int(tblRow, "data-pk");
                const [index, found_dict, compare] = b_recursive_integer_lookup(envelopitem_rows, "id", pk_int);
                mod_MENV_dict = (!isEmpty(found_dict)) ? found_dict : null;
            };
            // used in ModConfirm to delete, contains bundle, label or item pk
            selected.envelop_bundle_label_item_pk = (mod_MENV_dict.id) ? mod_MENV_dict.id : null;

        console.log("mod_MENV_dict", mod_MENV_dict)

            el_MENVIT_hdr.innerText = (mod_MENV_dict.content_nl) ? loc.Edit_label_item : loc.New_label_item;

            MENVIT_SetElements();

            if (!is_addnew){

                const modified_dateJS = parse_dateJS_from_dateISO(mod_MENV_dict.modifiedat);
                const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
                const modified_by = (mod_MENV_dict.modby_username) ? mod_MENV_dict.modby_username : "-";
                const display_txt = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by;
                document.getElementById("id_MENVIT_msg_modified").innerText = display_txt;
            };

    // ---  disable btn submit, hide delete btn when is_addnew
        //console.log( "el_MENVIT_btn_delete: ", el_MENVIT_btn_delete);
        //console.log( "is_addnew: ", is_addnew);
            add_or_remove_class(el_MENVIT_btn_delete, cls_hide, is_addnew );
            //const disable_btn_save = (!el_MENVIT_abbrev.value || !el_MENVIT_name.value  )
            //el_MENVIT_btn_save.disabled = disable_btn_save;

            MENVIT_validate_and_disable();

// show modal
            $("#id_mod_envelopitem").modal({backdrop: true});
        };
    };  // MENVIT_Open


//=========  MENVIT_Save  ================  PR2020-10-01
    function MENVIT_Save(crud_mode) {
        console.log(" -----  MENVIT_save  ----", crud_mode);
        console.log( "mod_MENV_dict: ", mod_MENV_dict);

        if (permit_dict.permit_crud){
            const is_create = (mod_MENV_dict.is_addnew);
            const is_delete = (crud_mode === "delete");
            const upload_mode = (is_create) ? "create" : (is_delete) ? "delete" : "update"

            let upload_dict = {table: 'envelopitem', mode: upload_mode}
            if(mod_MENV_dict.id){upload_dict.envelopitem_pk = mod_MENV_dict.id};
            if(mod_MENV_dict.mapid){upload_dict.mapid = mod_MENV_dict.mapid};

    // ---  put changed values of input elements in upload_dict
            let new_level_pk = null, new_sector_pk = null, level_or_sector_has_changed = false;
            //let form_elements = document.getElementById("id_MSTUDSUBJ_div_form_controls").querySelectorAll(".awp_input_text, .awp_input_select")
            let form_elements = el_MENVIT_form_controls.getElementsByClassName("form-control")
            for (let i = 0, el_input; el_input = form_elements[i]; i++) {
                const fldName = get_attr_from_el(el_input, "data-field");
                let new_value = null, old_value = null;
                //if(el_input.tagName === "INPUT"){
                //} else if(el_input.tagName === "SELECT"){
                //}

                new_value = (el_input.value) ? el_input.value : null;
                old_value = (mod_MENV_dict[fldName]) ? mod_MENV_dict[fldName] : null;

                if (new_value !== old_value) {
                    upload_dict[fldName] = new_value;
                };
            };

            UploadChanges(upload_dict, urls.url_envelopitem_upload);
        };

    // ---  hide modal
            $("#id_mod_envelopitem").modal("hide");
    } ; // MENVIT_Save





//========= MENVIT_InputKeyup  ============= PR2020-10-01
    function MENVIT_InputKeyup(el_input){
        //console.log( "===== MENVIT_InputKeyup  ========= ");
        MENVIT_validate_and_disable();
    }; // MENVIT_InputKeyup

//========= MENVIT_InputSelect  ============= PR2020-12-11
    function MENVIT_InputSelect(el_input){
        //console.log( "===== MENVIT_InputSelect  ========= ");
        MENVIT_validate_and_disable();
    }; // MENVIT_InputSelect

//=========  MENVIT_validate_and_disable  ================  PR2020-10-01
    function MENVIT_validate_and_disable() {
        //console.log(" -----  MENVIT_validate_and_disable   ----")
        let disable_save_btn = false;
// ---  loop through input fields on MENVIT_Open
        let form_elements = el_MENVIT_form_controls.querySelectorAll(".awp_input_text")
        for (let i = 0, el_input; el_input = form_elements[i]; i++) {
            const fldName = get_attr_from_el(el_input, "data-field");
            const msg_err = MENVIT_validate_field(el_input, fldName);
// ---  show / hide error message NOT IN USE
            const el_msg = document.getElementById("id_MENVIT_msg_" + fldName);
            if(el_msg){
                el_msg.innerText = msg_err;
                disable_save_btn = true;
                add_or_remove_class(el_msg, cls_hide, !msg_err)
            };
        };
// ---  disable save button on error
        el_MENVIT_btn_save.disabled = disable_save_btn;
    };  // MENVIT_validate_and_disable

//========= MENVIT_SetElements  ============= PR2022-08-04
    function MENVIT_SetElements(focus_field){
        //console.log( "===== MENVIT_SetElements  ========= ");
        //console.log( "mod_MENV_dict", mod_MENV_dict);
        //console.log( "focus_field", focus_field);
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
    };  // MENVIT_SetElements

// +++++++++ MOD EX3 FORM++++++++++++++++ PR2021-10-06
    function MENVPR_Open(){
        console.log(" -----  MENVPR_Open   ----")
            console.log("setting_dict.sel_examperiod", setting_dict.sel_examperiod)
        mod_MENV_dict = {};
        //PR2022-03-15 debug tel Richard Westerink: gives 'Ex3 Exemption'
    setting_dict.sel_examperiod = 1;
        if (![1,2,3].includes(setting_dict.sel_examperiod)){
            b_show_mod_message_html("<div class='p-2'>" + loc.Please_select_examperiod + "</div>");

        } else {
            console.log("level_map", level_map)
    // ---  fill select level or hide
            if (setting_dict.sel_dep_level_req){
                // HTML code "&#60" = "<" HTML code "&#62" = ">";
                const first_item = ["&#60", loc.All_levels, "&#62"].join("");
                el_MENVPR_select_level.innerHTML = t_FillOptionLevelSectorFromMap("level", "base_id", level_map,
                    setting_dict.sel_depbase_pk, null, first_item);
            }
    // hide option 'level' when havo/vwo
            if(el_MENVPR_layout_option_level){
                add_or_remove_class(el_MENVPR_layout_option_level, cls_hide, !setting_dict.sel_dep_level_req);
            }
            if(el_MENVPR_select_layout){
                const select_size = (setting_dict.sel_dep_level_req) ? "4" : "3";
                el_MENVPR_select_layout.setAttribute("size", select_size);
            }
    // hide element 'select_level' when havo/vwo
            add_or_remove_class(el_MENVPR_select_level.parentNode, cls_hide, !setting_dict.sel_dep_level_req);

    // - set header text
            el_MENVPR_hdr.innerText = [loc.Ex3, loc.Proces_verbaal_van_Toezicht].join("  -  ");

    // ---  reset layout options
            MENVPR_reset_layout_options();

    // ---  reset tblBody available and selected
            el_MENVPR_tblBody_available.innerText = null;
            el_MENVPR_tblBody_selected.innerText = null;

    // ---  disable save btn
            el_MENVPR_btn_save.disabled = true;

    // ---  get info from server
            MENVPR_getinfo_from_server()

    // ---  show modal
            $("#id_mod_envelop_print").modal({backdrop: true});
        };
    };  // MENVPR_Open

//========= MENVPR_Save  ============= PR2021-10-07
    function MENVPR_Save(){
        console.log(" -----  MENVPR_Save   ----")
        const subject_list = [];

// ---  loop through id_MENVPR_select_level and collect selected lvlbase_pk's
        const sel_lvlbase_pk_list = MENVPR_get_sel_lvlbase_pk_list();
        console.log("mod_MENV_dict.sel_lvlbase_pk_list", mod_MENV_dict.sel_lvlbase_pk_list)

// ---  get de selected value of
        const selected_layout_value = (el_MENVPR_select_layout.value) ? el_MENVPR_select_layout.value : "none";

// ---  loop through mod_MENV_dict.subject_rows and collect selected subject_pk's
        // PR2021-10-09 debug: also filter lvlbase_pk, because they stay selected when unselecting level
        if (mod_MENV_dict.subject_rows && mod_MENV_dict.subject_rows.length){
            for (let i = 0, subj_row; subj_row = mod_MENV_dict.subject_rows[i]; i++) {
                if(subj_row.selected){
                    let add_row = false;
                    if (mod_MENV_dict.lvlbase_pk_list && mod_MENV_dict.lvlbase_pk_list.length){
                        if (subj_row.lvlbase_id_arr && subj_row.lvlbase_id_arr.length){
                             for (let x = 0, lvlbase_id; lvlbase_id = subj_row.lvlbase_id_arr[x]; x++) {
                                if (mod_MENV_dict.lvlbase_pk_list.includes(lvlbase_id)){
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
        };
        // just for testing
        subject_list.push(12);

        if(subject_list.length){
            const upload_dict = {
                subject_list: subject_list,
                sel_layout: selected_layout_value,
                lvlbase_pk_list: sel_lvlbase_pk_list
            };

        console.log("upload_dict", upload_dict)
        // convert dict to json and add as parameter in link
            const upload_str = JSON.stringify(upload_dict);
            const href_str = urls.url_envelop_print.replace("-", upload_str);

        console.log("href_str", href_str)

            const el_MENVPR_save_link = document.getElementById("id_MENVPR_save_link");
            el_MENVPR_save_link.href = href_str;

        console.log("el_MENVPR_save_link", el_MENVPR_save_link)

            el_MENVPR_save_link.click();
        };

// ---  hide modal
        //$("#id_mod_selectex3").modal("hide");
    }  // MENVPR_Save

//========= MENVPR_getinfo_from_server  ============= PR2021-10-06
    function MENVPR_getinfo_from_server() {
        console.log("  =====  MENVPR_getinfo_from_server  =====");
        //el_MENVPR_loader.classList.remove(cls_hide);
            el_MENVPR_btn_save.disabled = false;

        //UploadChanges({check: true}, urls.url_envelop_print);
    }  // MENVPR_getinfo_from_server

//========= MENVPR_UpdateFromResponse  ============= PR2021-10-08
    function MENVPR_UpdateFromResponse(response) {
        console.log("  =====  MENVPR_UpdateFromResponse  =====");
        console.log("response", response)

        el_MENVPR_loader.classList.add(cls_hide);
        mod_MENV_dict.subject_rows = (response.ex3_subject_rows) ? response.ex3_subject_rows : [];
        mod_MENV_dict.sel_examperiod = (response.sel_examperiod) ? response.sel_examperiod : null;
        mod_MENV_dict.examperiod_caption = (response.examperiod_caption) ? response.examperiod_caption : "---";
        mod_MENV_dict.sel_layout = (response.sel_layout) ? response.sel_layout : "none";
        mod_MENV_dict.lvlbase_pk_list = (response.lvlbase_pk_list) ? response.lvlbase_pk_list : [];

        el_MENVPR_select_layout.value = mod_MENV_dict.sel_layout;
        // el_MENVPR_select_level is already reset in MEX#_Open with MENVPR_reset_layout_options
        console.log("mod_MENV_dict.lvlbase_pk_list", mod_MENV_dict.lvlbase_pk_list)
        if (mod_MENV_dict.lvlbase_pk_list && mod_MENV_dict.lvlbase_pk_list.length){
            for (let i = 0, option; option = el_MENVPR_select_level.options[i]; i++) {
                const lvlbase_pk_int = (Number(option.value)) ? Number(option.value) : null;
                option.selected = (lvlbase_pk_int && mod_MENV_dict.lvlbase_pk_list && mod_MENV_dict.lvlbase_pk_list.includes(lvlbase_pk_int));
            };
        } else {
            el_MENVPR_select_level.value = "0";
        };

// - set header text
        el_MENVPR_hdr.innerText = [loc.Ex3, loc.Proces_verbaal_van_Toezicht, mod_MENV_dict.examperiod_caption].join("  -  ");

        MENVPR_FillTbls()

    }  // MENVPR_getinfo_from_server

//========= MENVPR_SelectLevelHasChanged  ============= PR2021-10-09
    function MENVPR_SelectLevelHasChanged() {
        mod_MENV_dict.lvlbase_pk_list = MENVPR_get_sel_lvlbase_pk_list();
        MENVPR_FillTbls();
    }  // MENVPR_SelectLevelHasChanged

//========= MENVPR_FillTbls  ============= PR2021-10-06
    function MENVPR_FillTbls() {
        console.log("===== MENVPR_FillTbls ===== ");
        console.log("setting_dict", setting_dict);
        console.log("permit_dict", permit_dict);
        console.log("mod_MENV_dict.subject_rows", mod_MENV_dict.subject_rows);
        console.log("mod_MENV_dict.lvlbase_pk_list", mod_MENV_dict.lvlbase_pk_list, typeof mod_MENV_dict.lvlbase_pk_list);

// ---  reset tblBody available and selected
        el_MENVPR_tblBody_available.innerText = null;
        el_MENVPR_tblBody_selected.innerText = null;

        let has_subject_rows = false;
        let has_selected_subject_rows = false;

// ---  loop through mod_MENV_dict.subject_rows, show only subjects with lvlbase_pk in lvlbase_pk_list
        if (mod_MENV_dict.subject_rows && mod_MENV_dict.subject_rows.length){
            for (let i = 0, subj_row; subj_row = mod_MENV_dict.subject_rows[i]; i++) {
            // PR2022-06-13 tel Richard Westerink, Havo Vwo shows no subject.
            // setting_dict.sel_dep_level_req added to filter
                // subj_row.lvlbase_id_arr: [4]
                let show_row = false;
                if(!setting_dict.sel_dep_level_req){
                    // skip when dep has no level (Havo, Vwo)
                    show_row = true;
                } else if (!mod_MENV_dict.lvlbase_pk_list || !mod_MENV_dict.lvlbase_pk_list.length){
                    // skip when lvlbase_pk_list is empty ('all' levels selected)
                    show_row = true;
                } else {
                    // loop through subj_row.lvlbase_id_arr and check if subject.levelbase is in lvlbase_pk_list
                     for (let x = 0, lvlbase_id; lvlbase_id = subj_row.lvlbase_id_arr[x]; x++) {
                        if (mod_MENV_dict.lvlbase_pk_list.includes(lvlbase_id)){
                            show_row = true;
                            break;
                        };
                     };
                };
                if (show_row){
                    has_subject_rows = true;
                    const has_selected_subjects = MENVPR_CreateSelectRow(subj_row);
                    if(has_selected_subjects) {has_selected_subject_rows = true };
                };
            };
        };

        if (!has_subject_rows){
            const no_students_txt = (mod_MENV_dict.sel_examperiod === 3) ? loc.No_studenst_examperiod_03 :
                                    (mod_MENV_dict.sel_examperiod === 2) ? loc.No_studenst_examperiod_02 :
                                    loc.No_studenst_with_subjects;
            el_MENVPR_tblBody_available.innerHTML = [
                "<p class='text-muted px-2 pt-2'>", no_students_txt, "</p>"
            ].join("");

// --- addrow 'Please_select_one_or_more_subjects' if no subjects selected
        } else if(!has_selected_subject_rows){
            el_MENVPR_tblBody_selected.innerHTML = [
                "<p class='text-muted px-2 pt-2'>", loc.Please_select_one_or_more_subjects,
                "</p><p class='text-muted px-2'>", loc.from_available_list, "</p>"
            ].join("");

        };

// ---  enable save btn
        el_MENVPR_btn_save.disabled = !has_selected_subject_rows;

    }; // MENVPR_FillTbls

//========= MENVPR_CreateSelectRow  ============= PR2021-10-07
    function MENVPR_CreateSelectRow(row_dict) {
        //console.log("===== MENVPR_CreateSelectRow ===== ");

        let has_selected_subjects = false;

// - get ifo from dict
        const subj_id = (row_dict.subj_id) ? row_dict.subj_id : null;
        const subj_code = (row_dict.subj_code) ? row_dict.subj_code : "---";
        const subj_name_nl = (row_dict.subj_name_nl) ? row_dict.subj_name_nl : "---";
        const is_selected = (row_dict.selected) ? row_dict.selected : false;
        const just_selected = (row_dict.just_selected) ? row_dict.just_selected : false;

        if(is_selected) { has_selected_subjects = true};

        const tblBody = (is_selected) ? el_MENVPR_tblBody_selected : el_MENVPR_tblBody_available;

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
        tblRow.addEventListener("click", function() {MENVPR_AddRemoveSubject(tblRow)}, false);

// --- if added / removed row highlight row for 1 second
        if (just_selected) {
        row_dict.just_selected = false;
            ShowClassWithTimeout(tblRow, "bg_selected_blue", 1000) ;
        }
        return has_selected_subjects;
    } // MENVPR_CreateSelectRow

//========= MENVPR_AddRemoveSubject  ============= PR2020-11-18 PR2021-08-31
    function MENVPR_AddRemoveSubject(tblRow) {
        console.log("  =====  MENVPR_AddRemoveSubject  =====");
        console.log("tblRow", tblRow);

        const sel_subject_pk = (Number(tblRow.id)) ? Number(tblRow.id) : null;
        let has_changed = false;
    // lookup subject in mod_MENV_dict.subject_rows
        for (let i = 0, row_dict; row_dict = mod_MENV_dict.subject_rows[i]; i++) {
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
            el_MENVPR_btn_save.disabled = false;
            MENVPR_FillTbls();
        }

    }  // MENVPR_AddRemoveSubject

    function MENVPR_get_sel_lvlbase_pk_list(){  // PR2021-10-09
    // ---  loop through id_MENVPR_select_level and collect selected lvlbase_pk's
        //console.log("  =====  MENVPR_get_sel_lvlbase_pk_list  =====");
        let sel_lvlbase_pk_list = [];
        if(el_MENVPR_select_level){
            const level_options = Array.from(el_MENVPR_select_level.options);
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

    function MENVPR_reset_layout_options(){  // PR2021-10-10
    // ---  remove 'se';lected' from layout options
        //console.log("  =====  MENVPR_reset_layout_options  =====");
        if(el_MENVPR_select_layout){
            const layout_options = Array.from(el_MENVPR_select_layout.options);
            if(layout_options && layout_options.length){
                for (let i = 0, option; option = layout_options[i]; i++) {
                    option.selected = false;
                };
            };
        };
    };  // MENVPR_reset_layout_options

///////////////////////////////////////




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
        console.log("el_MOLEX_admin_label", el_MOLEX_admin_label)
        console.log("loc.Extra_exams + loc._for_ + admin_name", loc.Extra_exams + loc._for_ + admin_name)
            el_MOLEX_admin_label.innerText = loc.Extra_exams + loc._for_ + admin_name;
        };

// show modal
        $("#id_mod_orderlist_extra").modal({backdrop: true});

    };  // MOLEX_Open

//=========  MOLEX_Save  ================  PR2021-08-31
    function MOLEX_Save() {
        console.log(" -----  MOLEX_Save   ----")

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

//=========  RefreshDataRows  ================  PR2021-06-21 PR2022-08-04
    function RefreshDataRows(tblName, data_rows, update_rows, is_update) {
        console.log(" --- RefreshDataRows  ---");
        console.log("tblName", tblName);
        console.log("data_rows", data_rows);
        console.log("update_rows", update_rows);

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
    //PR2020-08-16 PR2020-09-30 PR2021-06-21 PR2022-08-14
    function RefreshDatarowItem(tblName, field_setting, data_rows, update_dict) {
        console.log(" --- RefreshDatarowItem  ---");
        console.log("tblName", tblName);
        console.log("update_dict", update_dict);
        console.log("field_setting.field_names", field_setting.field_names);

        if(!isEmpty(update_dict)){
            // add color fields to fieldnames when tblName = "envelopitem"
            // _color is used in modal from, _hexcol is used in tblRow
            const field_names = (tblName === "envelopitem") ? ["content_color", "instruction_color", "content_hexcolor", "instruction_hexcolor"] : [];
            if(field_setting.field_names && field_setting.field_names.length){
                // use i < len, otherwise loop stops at first blank item ""
                for (let i = 0, len = field_setting.field_names.length; i < len; i++) {
                    const field_name = field_setting.field_names[i];
                    if (field_name){
                        field_names.push(field_name);
                    };
                };
            };

            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);

            let updated_columns = [];
            let field_error_list = []

            const error_list = get_dict_value(update_dict, ["error"], []);

            if(error_list && error_list.length){

    // - show modal messages
                // TODO cannot show error_list in b_show_mod_message_dictlist. Already shown by response.messages
                b_show_mod_message_dictlist(error_list);

    // - add fields with error in field_error_list, to put old value back in field
                // TODO error_list is list of strings, not a dict with 'field
                for (let i = 0, msg_dict ; msg_dict = error_list[i]; i++) {
                    if ("field" in msg_dict){field_error_list.push(msg_dict.field)};
                };
    // - close modal MSJ when no error --- already done in modal
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

// +++++++++++ updated row +++++++++++
    // ---  check which fields are updated, add to list 'updated_columns'
                    if(!isEmpty(data_dict) && field_names){

                        copy_updatedict_to_datadict(data_dict, update_dict, field_names, updated_columns);

    // -- when color fiels has changed: also add textfield to update_dict, to show green
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
        console.log(" --- RefreshDataMap  ---");
        console.log("data_rows", data_rows);
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
        console.log( "col_index", col_index, "event.key", event.key);

        const skip_filter = t_SetExtendedFilterDict(el, col_index, filter_dict, event.key);
        //console.log( "filter_dict", filter_dict);

        if (!skip_filter) {
            Filter_TableRows();
        }
    }; // function HandleFilterKeyup

//========= HandleFilterField  ====================================
    function HandleFilterField(el_filter, col_index, event) {
        console.log( "===== HandleFilterField  ========= ");
        // skip filter if filter value has not changed, update variable filter_text

        //console.log( "el_filter", el_filter);
        //console.log( "col_index", col_index);
        const filter_tag = get_attr_from_el(el_filter, "data-filtertag")
        console.log( "filter_tag", filter_tag);

// --- get filter tblRow and tblBody
        const tblRow = t_get_tablerow_selected(el_filter);
        const tblName = "orderlist"  // tblName = get_attr_from_el(tblRow, "data-table")
        console.log( "tblName", tblName);

// --- reset filter row when clicked on 'Escape'
        const skip_filter = t_SetExtendedFilterDict(el_filter, col_index, filter_dict, event.key);

        Filter_TableRows();
    }; // HandleFilterField


//========= ShowTableRow  ==================================== PR2022-08-16
    function ShowTableRow(ete_exam_dict) {
        // this function filters rows when they are created, called bij SBR examperiod, department level
        // it uses 'selected' dict, filter is not stored in settings
        // only used in ete_exam_rows

        //console.log( "===== ShowTableRow  ========= ");
        //console.log( "selected", selected);
        //console.log( "selected.examperiod", selected.examperiod, typeof selected.examperiod);

        let hide_row = false;

    //console.log( "    ete_exam_dict.examperiod", ete_exam_dict.examperiod, typeof ete_exam_dict.examperiod);
        // 12 is used to select all exam periods
        if (!hide_row && selected.examperiod  && selected.examperiod !== 12){
            hide_row = (selected.examperiod !== ete_exam_dict.examperiod);
        };
        if (!hide_row && selected.department_pk){
            hide_row = (selected.department_pk !== ete_exam_dict.department_id);
        };
        if (!hide_row && selected.level_pk){
            hide_row = (selected.level_pk !== ete_exam_dict.level_id);
        };

        return !hide_row
    }; // ShowTableRow


//========= Filter_TableRows  ==================================== PR2021-07-08
    function Filter_TableRows() {
        console.log( "===== Filter_TableRows  ========= ");

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
        console.log(" ========== MPUBORD_OpenLogfile ===========");

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

//=========  get_datarows_from_selectedbtn  ================ PR2022-08-04
    function get_datarows_from_selectedbtn() {
        const data_rows = (selected_btn === "btn_orderlist") ? orderlist_rows :
                        (selected_btn === "btn_ete_exam") ? ete_exam_rows :
                        (selected_btn === "btn_bundle") ? envelopbundle_rows :
                        (selected_btn === "btn_label") ? enveloplabel_rows :
                        (selected_btn === "btn_item") ? envelopitem_rows : [];
        return data_rows;
    };

//=========  get_tblName_from_selectedbtn  ================ PR2022-08-04
    function get_tblName_from_selectedbtn() {
        //console.log("selected_btn", selected_btn)
        const tblName = (selected_btn === "btn_orderlist") ? "orderlist" :
                        (selected_btn === "btn_ete_exam") ? "ete_exam" :
                        (selected_btn === "btn_bundle") ? "envelopbundle" :
                        (selected_btn === "btn_label") ? "enveloplabel" :
                        (selected_btn === "btn_item") ? "envelopitem" : null;
        return tblName;
    };

})  // document.addEventListener('DOMContentLoaded', function()