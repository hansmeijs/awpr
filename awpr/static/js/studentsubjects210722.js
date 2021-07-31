// PR2020-09-29 added

// PR2021-07-23  declare variables outside function to make them global variables
let school_rows = [];
let student_rows = [];
let subject_rows = [];
let studsubj_rows = [];
let schemeitem_rows = [];
let published_rows = [];

let loc = {};

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
    let selected_btn = "btn_user_list";
    let setting_dict = {};
    let permit_dict = {};

    const selected = {
        studentsubject_dict: null,
        student_pk: null,
        subject_pk: null
    };

    let mod_dict = {};
    let mod_MSTUD_dict = {};
// mod_MSTUDSUBJ_dict stores available studsubj for selected candidate in MSTUDSUBJ
    let mod_MSTUDSUBJ_dict = {
        schemeitem_dict: {}, // stores available studsubj for selected candidate in MSTUDSUBJ
        studentsubject_dict: {}  // stores studsubj of selected candidate in MSTUDSUBJ
    };

    let mod_MASS_dict = {};
    let mod_MCOL_dict = {};

    let user_list = [];
    let examyear_map = new Map();
    let department_map = new Map();
    let level_map = new Map();
    let sector_map = new Map();

    // PR2021-07-23 moved outside this function, on top of this acript:
    //let student_rows = [];
    //let subject_rows = [];
    //let studsubj_rows = [];
    //let schemeitem_rows = [];
    //let loc = {};

    let filter_dict = {};
    let filter_mod_employee = false;

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    const url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    const url_settings_upload = get_attr_from_el(el_data, "data-url_settings_upload");
    const url_student_upload = get_attr_from_el(el_data, "data-url_student_upload");
    const url_studsubj_upload = get_attr_from_el(el_data, "data-url_studsubj_upload");
    const url_studsubj_validate = get_attr_from_el(el_data, "data-url_studsubj_validate");
    const url_studsubj_validate_all = get_attr_from_el(el_data, "data-url_studsubj_validate_all");
    const url_studsubj_approve = get_attr_from_el(el_data, "data-url_studsubj_approve");
    const url_studsubj_approve_multiple = get_attr_from_el(el_data, "data-url_studsubj_approve_multiple");
    const url_studsubj_send_email_exform = get_attr_from_el(el_data, "data-url_studsubj_send_email_exform");

    const url_grade_download_ex1 = get_attr_from_el(el_data, "data-url_grade_download_ex1");

    // url_importdata_upload is stored in id_MIMP_data of modimport.html

    const columns_tobe_hidden =  ["examnumber", "lvl_abbrev", "sct_abbrev", "subj_name", "sjtp_abbrev", "notes"];
    const columns_tobe_hidden_caption =  ["", "Examnumber", "", "Leerweg", "SectorProfiel_twolines", "", "Subject", "Character", "",
                                    "", "", "","",  "", "", "", "", "Notes"];

    const columns_hidden = {};

// --- get field_settings
    const field_settings = {
        studsubj: {  field_caption: ["", "Examnumber_twolines", "Candidate",  "Leerweg", "SectorProfiel_twolines",
                                "Abbreviation", "Subject", "Character", "subj_error", "",
                                "Exemption", "", "Re_examination","",  "Re_exam_3rd_2lns", "",
                                "Proof_of_knowledge_2lns", "", ""],
                    field_names: ["select", "examnumber", "fullname", "lvl_abbrev", "sct_abbrev",
                                "subj_code", "subj_name", "sjtp_abbrev", "subj_error", "subj_status",
                                ],
                                // TODO add has_exemption etc
                                //"has_exemption", "exm_status", "has_reex", "re2_status", "has_reex03", "re3_status",
                                //"has_pok", "pok_status", "notes"],
                    field_tags: ["div", "div", "div", "div", "div",
                                "div", "div", "div", "div", "div",
                                "div", "div", "div", "div", "div", "div",
                                "div", "div", "div"],

                    filter_tags: ["select", "text", "text",  "text",  "text",
                                "text", "text", "text", "toggle",  "toggle",
                                 "toggle", "text", "toggle", "text", "toggle", "text",
                                 "toggle", "toggle", "toggle"],
                    field_width:  ["020", "075", "180",  "075", "075",
                                    "075", "180","090", "032",  "032",
                                    "090", "032", "090", "032", "090", "032",
                                    "090", "032", "032"],
                    field_align: ["c", "r", "l", "c", "c",
                                    "l", "l", "l", "c", "c",
                                    "c", "c", "c", "c", "c", "c", "c",
                                    "c", "c"]},
        published: {field_caption: ["", "Name_ex_form", "Exam_period",  "Date_submitted", "Download_Exform"],
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
            el_SBR_select_showall.addEventListener("click", function() {HandleShowAll()}, false)};

// ---  MSED - MOD SELECT EXAMYEAR OR DEPARTMENT ------------------------------
        const el_MSED_input = document.getElementById("id_MSED_input");
        const el_MSED_btn_save = document.getElementById("id_MSED_btn_save");
        if (el_MSED_input){
            el_MSED_input.addEventListener("keyup", function(event){
                setTimeout(function() {t_MSED_InputName(el_MSED_input)}, 50)});
        }
        if (el_MSED_btn_save){
            el_MSED_btn_save.addEventListener("click", function() {t_MSED_Save(MSED_Response)}, false);
        }

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

        const el_input_controls = document.getElementById("id_MSTUDSUBJ_div_form_controls").querySelectorAll(".awp_input_text, .awp_input_checkbox")
        for (let i = 0, el; el = el_input_controls[i]; i++) {
            const key_str = (el.classList.contains("awp_input_checkbox")) ? "change" : "keyup";
            el.addEventListener(key_str, function() {MSTUDSUBJ_InputboxEdit(el)}, false)
        }

        const el_MSTUDSUBJ_msg_container = document.getElementById("id_MSTUDSUBJ_msg_container");
        const el_MSTUDSUBJ_loader = document.getElementById("id_MSTUDSUBJ_loader");
        const el_MSTUDSUBJ_btn_save = document.getElementById("id_MSTUDSUBJ_btn_save")
            el_MSTUDSUBJ_btn_save.addEventListener("click", function() {MSTUDSUBJ_Save()}, false);

        const el_tblBody_studsubjects = document.getElementById("id_MSTUDSUBJ_tblBody_studsubjects");
        const el_tblBody_schemeitems = document.getElementById("id_MSTUDSUBJ_tblBody_schemeitems");

// ---  MOD APPROVE STUDENT SUBJECT ------------------------------------
        const el_mod_approve_studsubj = document.getElementById("id_mod_approve_studsubj");

        const el_MASS_header = document.getElementById("id_MASS_header");

        const el_MASS_select_container = document.getElementById("id_MASS_select_container");
            const el_MASS_subheader = document.getElementById("id_MASS_subheader");
            const el_MASS_level = document.getElementById("id_MASS_level");
            const el_MASS_sector = document.getElementById("id_MASS_sector");
            const el_MASS_subject = document.getElementById("id_MASS_subject");
            //const el_MASS_cluster = document.getElementById("id_MASS_cluster");
        const el_MASS_info_container = document.getElementById("id_MASS_info_container");
        const el_MASS_loader = document.getElementById("id_MASS_loader");

        const el_MASS_apply_code_container = document.getElementById("id_MASS_apply_code_container");

        const el_MASS_input_verifcode = document.getElementById("id_MASS_input_verifcode");
        if (el_MASS_input_verifcode){
            el_MASS_input_verifcode.addEventListener("keyup", function() {MASS_InputVerifcode(el_MASS_input_verifcode)}, false )
        }

        const el_MASS_btn_delete = document.getElementById("id_MASS_btn_delete");
        const el_MASS_btn_save = document.getElementById("id_MASS_btn_save");
        const el_MASS_btn_cancel = document.getElementById("id_MASS_btn_cancel");
        if (el_MASS_btn_delete){
            el_MASS_btn_delete.addEventListener("click", function() {MASS_Save("delete")}, false )  // true = reset
        }
        if (el_MASS_btn_save){
            el_MASS_btn_save.addEventListener("click", function() {MASS_Save("save")}, false )
        }




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
    const el_filedialog = document.getElementById("id_MIMP_filedialog");
        el_filedialog.addEventListener("change", function() {MIMP_HandleFiledialog(el_filedialog, loc)}, false )

    const el_select_unique = document.getElementById("id_MIMP_select_unique");
    if (el_select_unique){
        el_select_unique.addEventListener("change", function() {MIMP_SelectUniqueChanged(el_select_unique)}, false )
    };
    const el_MIMP_tabular = document.getElementById("id_MIMP_tabular");
    if (el_MIMP_tabular){
        el_MIMP_tabular.addEventListener("change", function() {MIMP_CheckboxCrosstabTabularChanged(el_MIMP_tabular)}, false )
    };
    const el_MIMP_crosstab = document.getElementById("id_MIMP_crosstab");
    if (el_MIMP_crosstab){
        el_MIMP_crosstab.addEventListener("change", function() {MIMP_CheckboxCrosstabTabularChanged(el_MIMP_crosstab)}, false )
    };

    //const el_worksheet_list = document.getElementById("id_MIMP_worksheetlist");
    //    el_worksheet_list.addEventListener("change", MIMP_SelectWorksheet, false);
   // const el_MIMP_checkboxhasheader = document.getElementById("id_MIMP_hasheader");
   //     el_MIMP_checkboxhasheader.addEventListener("change", MIMP_CheckboxHasheaderChanged) //, false);
    //const el_select_dateformat = document.getElementById("id_MIMP_dateformat");
   //     el_select_dateformat.addEventListener("change", function() {MIMP_Selectdateformat(el_select_dateformat)}, false )
   const el_MIMP_btn_prev = document.getElementById("id_MIMP_btn_prev");
        el_MIMP_btn_prev.addEventListener("click", function() {MIMP_btnPrevNextClicked("prev")}, false )
   const el_MIMP_btn_next = document.getElementById("id_MIMP_btn_next");
        el_MIMP_btn_next.addEventListener("click", function() {MIMP_btnPrevNextClicked("next")}, false )
   const el_MIMP_btn_test = document.getElementById("id_MIMP_btn_test");
        el_MIMP_btn_test.addEventListener("click", function() {MIMP_Save("test", RefreshDataRowsStudsubjAfterUpload, setting_dict)}, false )
   const el_MIMP_btn_upload = document.getElementById("id_MIMP_btn_upload");
        el_MIMP_btn_upload.addEventListener("click", function() {MIMP_Save("save", RefreshDataRowsStudsubjAfterUpload, setting_dict)}, false )


// ---  MOD SELECT COLUMNS  ------------------------------------
        let el_MCOL_tblBody_available = document.getElementById("id_MCOL_tblBody_available");
        let el_MCOL_tblBody_show = document.getElementById("id_MCOL_tblBody_show");
        const el_MCOL_btn_save = document.getElementById("id_MCOL_btn_save");
            el_MCOL_btn_save.addEventListener("click", function() {ModColumns_Save()}, false );

// ---  MOD CONFIRM ------------------------------------
        let el_confirm_header = document.getElementById("id_modconfirm_header");
        let el_confirm_loader = document.getElementById("id_modconfirm_loader");
        let el_confirm_msg_container = document.getElementById("id_modconfirm_msg_container")
        let el_confirm_msg01 = document.getElementById("id_modconfirm_msg01")
        let el_confirm_msg02 = document.getElementById("id_modconfirm_msg02")
        let el_confirm_msg03 = document.getElementById("id_modconfirm_msg03")

        let el_confirm_btn_cancel = document.getElementById("id_modconfirm_btn_cancel");
        let el_confirm_btn_save = document.getElementById("id_modconfirm_btn_save");
        if(el_confirm_btn_save){ el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()}) };

// ---  set selected menu button active
        //SetMenubuttonActive(document.getElementById("id_hdr_users"));
    if(may_view_page){
        // period also returns emplhour_list
        const datalist_request = {
                setting: {page: "page_studsubj"},
                schoolsetting: {setting_key: "import_studsubj"},
                locale: {page: ["page_studsubj", "page_subject", "page_student", "upload"]},
                examyear_rows: {get: true},
                school_rows: {get: true},
                department_rows: {get: true},
                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},

                student_rows: {cur_dep_only: true},
                subject_rows: {cur_dep_only: true},
                studentsubject_rows: {cur_dep_only: true},
                scheme_rows: {cur_dep_only: true},
                schemeitem_rows: {cur_dep_only: true},
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

// ---  show loader  // don't use cls_hide, use cls_visible_hide
        el_loader.classList.remove(cls_hide)
        el_hdr_left.classList.add(cls_hide)

        let param = {"download": JSON.stringify (datalist_request)};
        let response = "";
        $.ajax({
            type: "POST",
            url: url_datalist_download,
            data: param,
            dataType: 'json',
            success: function (response) {
                console.log("response - elapsed time:", (new Date().getTime() - startime) / 1000 )
                console.log(response)

                // hide loader
                el_loader.classList.add(cls_hide)
                el_hdr_left.classList.remove(cls_hide)

                let must_create_submenu = false, must_update_headerbar = false;
                let check_validation = false;

                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                    mimp_loc = loc;
                    must_create_submenu = true;
                };
                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict;
                    selected_btn = (setting_dict.sel_btn);

            // ---  fill col_hidden
                    if("col_hidden" in setting_dict){
                       // clear the array columns_hidden
                       // reset all arrays of key to [], keep the keys.
                        for (const key of Object.keys(columns_hidden)) {
                            b_clear_array(columns_hidden[key]);
                        };
                       // fill the arrays in  columns_hidden
                        for (const [key, value] of Object.entries(setting_dict.col_hidden)) {
                            columns_hidden[key] = value;
                        }
                    }
                    console.log("columns_hidden", columns_hidden)

                    must_update_headerbar = true;

                console.log("setting_dict", setting_dict)

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
                    FillOptionsSelectLevelSector("level", response.level_rows)
                };
                if ("sector_rows" in response) {
                    b_fill_datamap(sector_map, response.sector_rows);
                    FillOptionsSelectLevelSector("sector", response.sector_rows);
                };

                if(must_create_submenu){CreateSubmenu()};
                if(must_update_headerbar){
                    b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);
                };

                if ("schoolsetting_dict" in response) { i_UpdateSchoolsettingsImport(response.schoolsetting_dict) };


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

            AddSubmenuButton(el_submenu, loc.Preliminary_Ex1_form, null, null, "id_submenu_download_ex1", url_grade_download_ex1, false);  // true = download
            if (permit_dict.permit_approve_subject){
                AddSubmenuButton(el_submenu, loc.Approve_subjects, function() {MASS_Open("approve")});
            }
            if (permit_dict.permit_submit_subject){
                AddSubmenuButton(el_submenu, loc.Submit_Ex1_form, function() {MASS_Open("submit")});
            };
            if(permit_dict.permit_crud){
                AddSubmenuButton(el_submenu, loc.Upload_subjects, function() {MIMP_Open("import_studsubj")}, null, "id_submenu_import");
            }
            // TODO  add Show_hide_columns
            // AddSubmenuButton(el_submenu, loc.Show_hide_columns, function() {MCOL_Open()}, [], "id_submenu_columns")
         el_submenu.classList.remove(cls_hide);
        };
    };//function CreateSubmenu

//###########################################################################
//=========  HandleBtnSelect  ================ PR2020-09-19  PR2020-11-14
    function HandleBtnSelect(data_btn, skip_upload) {
        //console.log( "===== HandleBtnSelect ========= ", data_btn);
        selected_btn = data_btn
        if(!selected_btn){selected_btn = "btn_student"}

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_studsubj: {sel_btn: selected_btn}};
            UploadSettings (upload_dict, url_settings_upload);
        };

// ---  highlight selected button
        highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  show only the elements that are used in this tab
        b_show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);


// ---  fill datatable
        const filter_field = (setting_dict.sel_subject_pk) ? "subject" : (setting_dict.sel_student_pk) ? "student" : null;
        const filter_pk = (setting_dict.sel_subject_pk) ? setting_dict.sel_subject_pk :
                            (setting_dict.sel_student_pk) ? setting_dict.sel_student_pk : null;
        FillTblRows(filter_field, filter_pk);

// --- update header text
        const data_rows = (filter_field === "subject") ? subject_rows :
                              (filter_field === "student") ? student_rows : null;
        const data_dict = b_get_mapdict_by_integer_from_datarows(data_rows, "id", filter_pk)
        const selected_name = (filter_field === "subject") ? data_dict.name :
                              (filter_field === "student") ? data_dict.fullname : null;
        UpdateHeaderText(selected_name);

    }  // HandleBtnSelect

//=========  HandleTableRowClicked  ================ PR2020-08-03
    function HandleTableRowClicked(tr_clicked) {
        //console.log("=== HandleTableRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

// ---  update selected student_pk
        selected.studentsubject_dict = null;
        selected.student_pk = null;
        selected.subject_pk = null
        const data_rows = (selected_btn === "btn_published")? published_rows : studsubj_rows;
        const data_dict = get_mapdict_by_integer_from_datarows(data_rows, tr_clicked);

        if (selected_btn === "btn_published"){
            //TODO
        } else {
            selected.studentsubject_dict = data_dict;
            selected.studsubj_pk = (data_dict.studsubj_id) ? data_dict.studsubj_id : null;
            if (selected.studentsubject_dict){
                selected.student_pk = selected.studentsubject_dict.stud_id;
                selected.subject_pk = selected.studentsubject_dict.subj_id;
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



//========= FillTblRows  ==================== PR2021-07-01
    function FillTblRows(filter_field, filter_pk) {
        //console.log( "===== FillTblRows  === ");
        //console.log( "setting_dict", setting_dict);

        const tblName = get_tblName_from_selectedBtn()
        const field_setting = field_settings[tblName]
        const data_rows = get_datarows_from_tblName(tblName)

        //console.log( "tblName", tblName);
        //console.log( "field_setting", field_setting);
        //console.log( "data_rows", data_rows);

// --- show columns
        //set_columns_hidden();

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

// --- create table header
        CreateTblHeader(field_setting);

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
    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-07-31 PR2021-07-22
    function CreateTblHeader(field_setting) {
        //console.log("===  CreateTblHeader ===== ");
        //console.log("field_setting", field_setting);

        //console.log("columns_hidden", columns_hidden);
        const column_count = field_setting.field_names.length;

//--- insert table rows
        let tblRow_header = tblHead_datatable.insertRow (-1);
        let tblRow_filter = tblHead_datatable.insertRow (-1);

//--- insert th's to tblHead_datatable
        for (let j = 0; j < column_count; j++) {

            const field_name = field_setting.field_names[j];
            const filter_tag = field_setting.filter_tags[j];
            const class_width = "tw_" + field_setting.field_width[j] ;
            const class_align = "ta_" + field_setting.field_align[j];

            // skip columns if in columns_hidden
            const col_is_hidden = get_column_hidden(field_name);
            if (!col_is_hidden){
                const key = field_setting.field_caption[j];
                let field_caption = (loc[key]) ? loc[key] : key;
                if (field_name === "sct_abbrev") {
                    field_caption = (setting_dict.sel_dep_has_profiel) ? loc.Profiel : loc.Sector;
                }

// ++++++++++ create header row +++++++++++++++
        // --- add th to tblRow.
                let th_header = document.createElement("th");
        // --- add div to th, margin not working with th
                    const el_header = document.createElement("div");
                        if (j === 0 ){
        // --- add checked image to first column
                           // TODO add multiple selection
                            //AppendChildIcon(el_header, imgsrc_stat00);
                        } else  if (field_name.includes("_status")){
                            // --- add  statud icon.
                            el_header.classList.add("diamond_0_0")
                        } else if(field_name === "notes"){
                             // dont show note icon when user has no permit_read_note
                            //const class_str = (permit_dict.permit_read_note) ? "note_0_1" : "note_0_0"
                            el_header.classList.add("note_0_1")

                        } else if(field_name === "subj_error"){
                             // dont show note icon when user has no permit_read_note
                            //const class_str = (permit_dict.permit_read_note) ? "note_0_1" : "note_0_0"
                            el_header.classList.add("note_0_0")
                        } else {
// --- add innerText to el_div
                            if(field_caption) {el_header.innerText = field_caption};
                            if(field_name === "examnumber"){el_header.classList.add("pr-2")}
                        };
// --- add width, text_align
                        el_header.classList.add(class_width, class_align);
                    th_header.appendChild(el_header)
                tblRow_header.appendChild(th_header);

// ++++++++++ create filter row +++++++++++++++
// --- add th to tblRow_filter.
                const th_filter = document.createElement("th");
// --- create element with tag from field_tags
                const el_tag = (filter_tag === "text") ? "input" : "div";
                const el_filter = document.createElement(el_tag);
// --- add EventListener to el_filter
                    const event_str = (filter_tag === "text") ? "keyup" : "click";
                    el_filter.addEventListener(event_str, function(event){HandleFilterField(el_filter, j, event)});
// --- add data-field Attribute.
                    el_filter.setAttribute("data-field", field_name);
                    el_filter.setAttribute("data-filtertag", filter_tag);
// --- add other attributes
                    if (filter_tag === "text") {
                        el_filter.setAttribute("type", "text")
                        el_filter.classList.add("input_text");

                        el_filter.setAttribute("autocomplete", "off");
                        el_filter.setAttribute("ondragstart", "return false;");
                        el_filter.setAttribute("ondrop", "return false;");
                    } else if (["toggle"].includes(filter_tag)) {
                        // default empty icon necessary to set pointer_show
                        append_background_class(el_filter,"tickmark_0_0");
                    }

// --- add width, text_align
                    el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");
                th_filter.appendChild(el_filter)
                tblRow_filter.appendChild(th_filter);
            }  //  if (columns_hidden.inludes(field_name))
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

// ---  lookup index where this row must be inserted
        let ob1 = "", ob2 = "", ob3 = "";
        if (tblName === "studsubj") {
            if (map_dict.lastname) { ob1 = map_dict.lastname.toLowerCase() };
            if (map_dict.firstname) { ob2 = map_dict.firstname.toLowerCase() };
            if (map_dict.sjtp_name) { ob3 = (map_dict.subj_name.toLowerCase()) };
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
        tblRow.addEventListener("click", function() {HandleTableRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
        for (let j = 0; j < column_count; j++) {
            const field_name = field_names[j];

// skip columns if in columns_hidden
            // skip columns if in columns_hidden
            const col_is_hidden = get_column_hidden(field_name);
            if (!col_is_hidden){
                const field_tag = field_tags[j];
                const class_width = "tw_" + field_width[j];
                const class_align = "ta_" + field_align[j];

        // --- insert td element,
                let td = tblRow.insertCell(-1);

        // --- create element with tag from field_tags
                let el = document.createElement(field_tag);

        // --- add data-field attribute
                el.setAttribute("data-field", field_name);

    // --- add classList to td
                if (tblName === "studsubj"){
                    if(field_name === "examnumber"){
                        td.classList.add("pr-4")
                    } else if (field_name.includes("has_")){
                        el.classList.add("tickmark_0_0")
                    } else  if (field_name === "subj_error"){
                        el.classList.add("note_0_3")
                    } else  if (field_name.includes("_status")){
                        el.classList.add("diamond_3_4")
                    };
                } else if (tblName === "published"){
                    if (field_name === "url"){
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

                if (field_name === "select") {
                    // pass
                } else if (field_name.includes("has_")){
                //<PERMIT>
                    td.addEventListener("click", function() {UploadToggle(el)}, false)
                    add_hover(td);
                } else if ( field_name.includes("_status")){
                    // skip when no permit or row has no studsubj_id or when it is published
                    if(permit_dict.permit_approve_subject && map_dict.studsubj_id){
                        const prefix = field_name.replace("_status", "");
                        const field_publ_id = prefix + "_publ_id" // subj_publ_id
                        const publ_id = (map_dict[field_publ_id]) ? map_dict[field_publ_id] : null;
                        if(!publ_id){
                            td.addEventListener("click", function() {UploadToggleStatus(el)}, false)
                            add_hover(td);
                        };
                    };
                } else {
                    td.addEventListener("click", function() {MSTUDSUBJ_Open(td)}, false)
                    td.classList.add("pointer_show");
                    add_hover(td);
                }

        // --- add width, text_align, right padding in examnumber
                // not necessary: td.classList.add(class_width, class_align);

                if(["name", "fullname", "subj_name"].includes(field_name)){
                    // dont set width in field student and subject, to adjust width to length of name
                    el.classList.add(class_align);
                } else {
                    el.classList.add(class_width, class_align);
                }
                if(field_name === "examnumber"){el.classList.add("pr-2")}

// --- put value in field
               UpdateField(el, map_dict)
            }  //  if (columns_hidden[field_name])
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

//=========  UpdateField  ================ PR2020-08-16
    function UpdateField(el_div, map_dict) {
        //console.log("=========  UpdateField =========");
        //console.log("map_dict", map_dict);

        if(el_div){
            const field_name = get_attr_from_el(el_div, "data-field");
            const fld_value = (map_dict[field_name]) ? map_dict[field_name] : null;

        //console.log(".......map_dict[" + field_name + "]", map_dict[field_name]);

            if(field_name){
                let inner_text = null, h_ref = null, title_text = null, filter_value = null;
                if (field_name === "select") {
                    // TODO add select multiple users option PR2020-08-18
                 } else if (["examnumber", "fullname", "lvl_abbrev", "sct_abbrev", "subj_code", "subj_name", "sjtp_abbrev",
                 "name", "name", "name", "name",
                             ].includes(field_name)){
                    inner_text = fld_value;
                    filter_value = (inner_text) ? inner_text.toLowerCase() : null;
                } else if (field_name.includes("has_")){
                    filter_value = (fld_value) ? "1" : "0";
                    const is_etenorm = false
                    el_div.className = (is_etenorm) ? "tickmark_1_2" : "tickmark_0_0";

                } else if(field_name === "subj_error"){
                    filter_value = (fld_value) ? "1" : "0";
                    el_div.className = (fld_value) ? "note_1_3" : "note_0_0";
                    if(fld_value) {
                        if(!map_dict.studsubj_id){
                            title_text = loc.This_candidate_has_nosubjects;
                        } else {
                            title_text = loc.validation_error + "."
                        }
                    };

                } else if (field_name.includes("_status")){
                    const [status_className, status_title_text] = UpdateFieldStatus(field_name, map_dict);
                    el_div.className = status_className;
                    title_text = status_title_text;

                } else if (field_name === "examperiod"){
                    inner_text = loc.examperiod_caption[map_dict.examperiod];
                } else if (field_name === "datepublished"){
                     inner_text = format_dateISO_vanilla (loc, map_dict.datepublished, true, false, true, false);
                } else if (field_name === "url"){
                    h_ref = fld_value;
                };  // if (field_name === "select")

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
            }  // if(field_name)
        }  // if(el_div)
    };  // UpdateField

//=========  UpdateFieldStatus  ================ PR2021-07-25
    function UpdateFieldStatus(field_name, map_dict) {
        //console.log("=========  UpdateFieldStatus =========");
        //console.log("map_dict", map_dict);
        let className = "diamond_0_4";  // diamond_0_4 is blank img
        let title_text = null;

        if (field_name.includes("_status")){
            // skip when row has no studsubj_id
            if (map_dict.studsubj_id) {

                //const prefix_mapped = {btn_studsubj: "subj_", btn_exemption: "exem_", btn_reex: "reex_", btn_reex3: "reex3_", btn_pok: "pok_", }
                const prefix = field_name.replace("_status", "");

                const field_auth1_id = prefix + "_auth1_id" // subj_auth1_id
                const field_auth2_id = prefix + "_auth2_id" // subj_auth2_id
                const field_publ_id = prefix + "_publ_id" // subj_publ_id

                const auth1_id = (map_dict[field_auth1_id]) ? map_dict[field_auth1_id] : null;
                const auth2_id = (map_dict[field_auth2_id]) ? map_dict[field_auth2_id] : null;
                const publ_id = (map_dict[field_publ_id]) ? map_dict[field_publ_id] : null;

                const class_str = (publ_id) ? "diamond_3_4" :
                                  (auth1_id && auth2_id) ? "diamond_3_3" :
                                  (auth1_id ) ? "diamond_2_1" :
                                  (auth2_id) ? "diamond_1_2" : "diamond_0_0" // diamond_0_0 is outlined diamond
                className = class_str;

                const field_auth1by = prefix + "_auth1by" // subj_auth1by
                const field_auth2by = prefix + "_auth2by" // subj_auth2by
                const field_published = prefix + "_published" // subj_published

                if (publ_id){
                    const field_modat = prefix + "_publ_modat";
                    //title_text = loc.Submitted_at + " " + get_date_formatted(field_modat, map_dict);
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
        };  // if (field_name === "select") {
        return [className, title_text]
    }  // UpdateFieldStatus

//========= get_column_hidden  ====== PR2021-03-15 PR2021-07-22
    function get_column_hidden(field_name) {
        //console.log( "===== get_column_hidden  === ");
        //console.log( "selected_btn", selected_btn);
        //console.log( "field_name", field_name);
        //console.log("setting_dict.sel_dep_level_req", setting_dict.sel_dep_level_req);

        const mapped_field = (field_name === "subj_status") ? "subj_error" :
                             (field_name === "exm_status") ? "has_exemption" :
                             (field_name === "re2_status") ? "has_reex" :
                             (field_name === "re3_status") ? "has_reex03" :
                             (field_name === "has_pok") ? "pok_status" : field_name;
        //console.log( "mapped_field", mapped_field);

// --- set col_hidden
        const tblName = (selected_btn === "btn_published")? "published" : "studsubj";
        const col_hidden = (columns_hidden[tblName]) ? columns_hidden[tblName] : [];

        let is_hidden = col_hidden.includes(mapped_field);
        //console.log("is_hidden", is_hidden)

/*
field_names: ["select", "examnumber", "fullname", "lvl_abbrev", "sct_abbrev",
            "subj_code", "subj_name", "sjtp_abbrev", "subj_status",
            "has_exemption", "exm_status", "has_reex", "re2_status", "has_reex03", "re3_status",
            "has_pok", "pok_status", "notes"],
*/

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
            } else if (mapped_field === "has_pok") {
                is_hidden = (selected_btn !== "btn_pok");
            };
        }
        //console.log( "is_hidden", is_hidden);
        return is_hidden;
    };  // get_column_hidden




// +++++++++++++++++ UPLOAD CHANGES +++++++++++++++++ PR2020-08-03

//========= UploadToggleStatus  ============= PR2020-07-31
    function UploadToggleStatus(el_input) {
        console.log( " ==== UploadToggleStatus ====");
        console.log( "el_input", el_input);

        if (permit_dict.permit_approve_subject){

            mod_dict = {};
            const tblName = (selected_btn === "btn_published")? "published" : "studsubj";

            const tblRow = get_tablerow_selected(el_input);
            const data_rows = (selected_btn === "btn_published")? published_rows : studsubj_rows;
            const map_dict = get_mapdict_by_integer_from_datarows(data_rows, tblRow);
            console.log( "map_dict", map_dict);
/*
// +++ get existing data_dict from data_rows. data_rows is ordered by: studsubj_id, stud_id'
            const studsubj_pk = (update_dict && update_dict.studsubj_id) ? update_dict.studsubj_id : null;
            const student_pk = (update_dict && update_dict.stud_id) ? update_dict.stud_id : null;
            const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "studsubj_id", studsubj_pk, "stud_id", student_pk);
            let data_dict = (!isEmpty(found_dict)) ? found_dict : null;
            const datarow_index = index;
        console.log(".....data_dict", data_dict);
*/

            if(!isEmpty(map_dict)){
                const fldName = get_attr_from_el(el_input, "data-field");
                const prefix = fldName.replace("_status", "");
                const auth = (permit_dict.usergroup_auth1 && !permit_dict.usergroup_auth2) ? "_auth1" :
                             (!permit_dict.usergroup_auth1 && permit_dict.usergroup_auth2) ? "_auth2" : null;

        console.log( "permit_dict.usergroup_auth1", permit_dict.usergroup_auth1);
        console.log( "permit_dict.usergroup_auth2", permit_dict.usergroup_auth2);
        console.log( "auth", auth);
                const field_auth_id = prefix + auth +  "_id";
                const auth_id = (map_dict[field_auth_id]) ? map_dict[field_auth_id] : null;
                const model_field = (auth === "_auth1") ? "subj_auth1by" : (auth === "_auth2") ? "subj_auth2by" : null;
                if (model_field) {
// - get new_auth_id - remove oif already filled in
                    const new_auth_id = (!auth_id) ? permit_dict.requsr_pk : null;

    // ---  upload changes
                    const studsubj_dict = {
                        student_pk: map_dict.stud_id,
                        studsubj_pk: map_dict.studsubj_id
                    };
                    studsubj_dict[model_field] = new_auth_id;

                    const upload_dict = {
                        table: "studsubj",
                        studsubj_list: [studsubj_dict]
                    };

                    UploadChanges(upload_dict, url_studsubj_approve);
                };
            }  //  if(!isEmpty(map_dict)){

        } //   if(permit_dict.permit_approve_subject)
    }  // UploadToggleStatus

//========= UploadToggle  ============= PR2020-07-31
    function UploadToggle(el_input) {
        console.log( " ==== UploadToggleStatus ====");
        console.log( "el_input", el_input);

        if (permit_dict.permit_crud){
            mod_dict = {};

            const tblRow = get_tablerow_selected(el_input);
            const data_rows = (selected_btn === "btn_published")? published_rows : studsubj_rows;
            const map_dict = get_mapdict_by_integer_from_datarows(data_rows, tblRow);

// ---  upload changes
            const studsubj_dict = {
                studsubj_pk: map_dict.studsubj_id,
                schemeitem_pk: map_dict.schemeitem_pk,
                mode: "update"
            };
            studsubj_dict[fldName] = new_value;

            const studsubj_list = [studsubj_dict];

            const upload_dict = {
                sel_examyear_pk: setting_dict.sel_examyear_pk,
                sel_schoolbase_pk: setting_dict.sel_schoolbase_pk,
                sel_depbase_pk: setting_dict.sel_depbase_pk,
                table: "studsubj",
                mapid: map_dict.mapid,
                student_pk: map_dict.stud_id,
                studsubj_list: studsubj_list};
            UploadChanges(upload_dict, url_studsubj_upload);

        } //   if(permit_dict.permit_approve_subject)
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
                    add_or_remove_class(el_MSTUDSUBJ_loader, cls_hide, true);
                    if ("updated_studsubj_rows" in response || "studsubj_validate_html" in response) {
                         MSTUDSUBJ_Response(response)
                    };

                    if ( "approve_msg_html" in response){
                        MASS_UpdateFromResponse(response)
                    }
                    // this one is in MASS_UpdateFromResponse:
                    //if ( "updated_studsubj_approve_rows" in response){

                    if ("messages" in response){
                        b_ShowModMessages(response.messages);
                        $("#id_mod_studentsubject").modal("hide");
                    }



                },  // success: function (response) {
                error: function (xhr, msg) {
                    // ---  hide loader
                    el_loader.classList.add(cls_hide)
                    el_hdr_left.classList.remove(cls_hide)

                    console.log(msg + '\n' + xhr.responseText);
                }  // error: function (xhr, msg) {
            });  // $.ajax({
        }  //  if(!!row_upload)
    };  // UploadChanges

// +++++++++++++++++ UPDATE +++++++++++++++++++++++++++++++++++++++++++

// +++++++++ MOD STUDENT SUBJECT++++++++++++++++ PR2020-11-16
    function MSTUDSUBJ_Open(el_input){
        console.log(" -----  MSTUDSUBJ_Open   ----")
        console.log("el_input", el_input)
        //console.log("permit_dict", permit_dict)
        // TODO === FIXIT === set permit
        //if(el_input && permit_dict.permit_crud){
        if (true){
        // mod_MSTUDSUBJ_dict stores general info of selected candidate in MSTUDSUBJ PR2020-11-21
            mod_MSTUDSUBJ_dict = {
                mod_schemeitem_dict: {},  // stores available studsubj for selected candidate in MSTUDSUBJ
                studentsubject_dict: {}  // stores studsubj of selected candidate in MSTUDSUBJ
            };

            let tblName = "studsubj";

            const tblRow = get_tablerow_selected(el_input);
            const map_id = tblRow.id;
            const arr = map_id.split("_");
            const stud_pk_int = (Number(arr[1])) ? Number(arr[1]) : null;
            const studsubj_pk_int = (Number(arr[2])) ? Number(arr[2]) : null;

            const student_map_id = "student_" + arr[1];
            const map_dict = b_get_mapdict_from_datarows(student_rows, student_map_id, setting_dict.user_lang);
            console.log("map_dict", map_dict)

            if(!isEmpty(map_dict)) {
                mod_MSTUDSUBJ_dict.stud_id = map_dict.id;
                mod_MSTUDSUBJ_dict.scheme_id = map_dict.scheme_id;

    // ---  set header text
                let header_text = loc.Subjects + loc._of_ + map_dict.fullname
                let dep_lvl_sct_text = (map_dict.dep_abbrev) ? map_dict.dep_abbrev + " - " : "";
                if(map_dict.lvl_abbrev) {dep_lvl_sct_text += map_dict.lvl_abbrev + " - "};
                if(map_dict.sct_abbrev) {dep_lvl_sct_text += map_dict.sct_abbrev};
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

        // ---  disable btn submit, hide delete btn when is_addnew
               // add_or_remove_class(el_MSTUD_btn_delete, cls_hide, is_addnew )
                //const disable_btn_save = (!el_MSTUD_abbrev.value || !el_MSTUD_name.value || !el_MSTUD_sequence.value )
                //el_MSTUD_btn_save.disabled = disable_btn_save;

                //MSTUD_validate_and_disable();
        // validate student_subjects
                if(has_studsubj_rows){
                    const upload_dict = {student_pk: mod_MSTUDSUBJ_dict.stud_id};
                    UploadChanges(upload_dict, url_studsubj_validate);
                    add_or_remove_class(el_MSTUDSUBJ_loader, cls_hide, false);
                }


        // ---  show modal
                $("#id_mod_studentsubject").modal({backdrop: true});

            }  // if(!isEmpty(map_dict)) {
        }
    };  // MSTUDSUBJ_Open

//========= MSTUDSUBJ_Save  ============= PR2020-11-18
    function MSTUDSUBJ_Save(){
        console.log(" -----  MSTUDSUBJ_Save   ----")
        console.log( "mod_MSTUDSUBJ_dict.studentsubject_dict: ", mod_MSTUDSUBJ_dict.studentsubject_dict);
        console.log( "mod_MSTUDSUBJ_dict: ", mod_MSTUDSUBJ_dict);
        // TODO === FIXIT === set permit
        //if(permit_dict.permit_crud && mod_MSTUDSUBJ_dict.stud_id){
        if(true){
            const upload_dict = {
                table: 'studentsubject',
                sel_examyear_pk: setting_dict.sel_examyear_pk,
                sel_schoolbase_pk: setting_dict.sel_schoolbase_pk,
                sel_depbase_pk: setting_dict.sel_depbase_pk,
                student_pk: mod_MSTUDSUBJ_dict.stud_id
            }
            const studsubj_list = []
// ---  loop through mod_MSTUDSUBJ_dict.studentsubject_dict
            for (const [studsubj_pk_str, ss_dict] of Object.entries(mod_MSTUDSUBJ_dict.studentsubject_dict)) {
                const studsubj_pk = Number(studsubj_pk_str);
                if(!isEmpty(ss_dict)){
                    let mode = null;
                    if(ss_dict.isdeleted){
                        mode = "delete"
                    } else  if(ss_dict.iscreated){
                        mode = "create"
                    } else  if(ss_dict.haschanged){
                        mode = "update"
                    }
                    if (mode){
                        studsubj_list.push({
                                mode: mode,
                                student_pk: ss_dict.stud_id,
                                studsubj_pk: ss_dict.studsubj_id,
                                schemeitem_pk: ss_dict.schemeitem_id,
                                is_extra_nocount: ss_dict.is_extra_nocount,
                                is_extra_counts: ss_dict.is_extra_counts,
                                is_elective_combi: ss_dict.is_elective_combi,
                                pws_title: ss_dict.pws_title,
                                pws_subjects: ss_dict.pws_subjects
                            });
                    }  //  if (mode)
                    if (mode === "delete"){
// - make to_be_deleted tblRow red
                        const row_id = "studsubj_" + ss_dict.stud_id + "_" + ss_dict.studsubj_id
                        const tblRow = document.getElementById(row_id);

                        ShowClassWithTimeout(tblRow, "tsa_tr_error")
                    }
                }  // if(!isEmpty(ss_dict)){
            }

            if(studsubj_list && studsubj_list.length){
                upload_dict.studsubj_list = studsubj_list;
                console.log("upload_dict: ", upload_dict)
                UploadChanges(upload_dict, url_studsubj_upload);
                // show laoder
                add_or_remove_class(el_MSTUDSUBJ_loader, cls_hide, false);
            }
        };  // if(permit_dict.permit_crud && mod_MSTUDSUBJ_dict.stud_id){

// ---  hide modal
        //$("#id_mod_studentsubject").modal("hide");

    }  // MSTUDSUBJ_Save

//========= MSTUDSUBJ_Response  ============= PR2021-07-09
    function MSTUDSUBJ_Response(response) {
        console.log("===== MSTUDSUBJ_Response ===== ");

        const studsubj_validate_html = response.studsubj_validate_html;
        if ("updated_studsubj_rows" in response) {
            const tblName = (selected_btn === "btn_published")? "published" : "studsubj";
            RefreshDataRows(tblName, response.updated_studsubj_rows, studsubj_rows, true)  // true = update
        }

        // studsubj_validate_html comes after updated_studsubj_rows, to refresh datarows before filling lists
        if (studsubj_validate_html){

            el_MSTUDSUBJ_msg_container.innerHTML = studsubj_validate_html
            add_or_remove_class(el_MSTUDSUBJ_msg_container, cls_hide, false)

            MSTUDSUBJ_FillDicts();
            MSTUDSUBJ_FillTbls();

        } else {
             $("#id_mod_studentsubject").modal("hide");
        };

    };

//========= MSTUDSUBJ_FillDicts  ============= PR2020-11-17
    function MSTUDSUBJ_FillDicts() {
        console.log("===== MSTUDSUBJ_FillDicts ===== ");
        console.log("mod_MSTUDSUBJ_dict", mod_MSTUDSUBJ_dict);

//  list mod_MSTUDSUBJ_dict.studentsubject_dict contains the existing, added and deleted subjects of the student
//  list mod_MSTUDSUBJ_dict.schemeitem_dict contains all schemitems of the student's scheme
        mod_MSTUDSUBJ_dict.studentsubject_dict = {};
        mod_MSTUDSUBJ_dict.schemeitem_dict = {}

        const student_pk = mod_MSTUDSUBJ_dict.stud_id
        const scheme_pk = mod_MSTUDSUBJ_dict.scheme_id

// ---  loop through studsubj_rows
        let has_studsubj_rows = false;
        for (let i = 0, row_dict; row_dict = studsubj_rows[i]; i++) {
            const map_id = row_dict.mapid;
        // add only studsubj from this student
            if (student_pk === row_dict.stud_id) {
                const item = deepcopy_dict(row_dict);
                has_studsubj_rows = true;
        // add dict of subject (schemeitem_id) to mod_MSTUDSUBJ_dict.studentsubject_dict
                if(item.schemeitem_id){
                    mod_MSTUDSUBJ_dict.studentsubject_dict[item.schemeitem_id] = item;
                }
            }
        }

// ---  loop through schemeitem_rows add schemeitems from scheme of this student to mod_MSTUDSUBJ_dict.schemeitem_dict
        el_tblBody_schemeitems.innerText = null;
        if (schemeitem_rows && schemeitem_rows.length ) {
            for (let i = 0, row_dict; row_dict = schemeitem_rows[i]; i++) {
                if (scheme_pk && scheme_pk === row_dict.scheme_id) {
                    const item = deepcopy_dict(row_dict);
                    mod_MSTUDSUBJ_dict.schemeitem_dict[item.id] = item;
                }
            }
        }

        console.log("..................");
        console.log("mod_MSTUDSUBJ_dict.studentsubject_dict:", mod_MSTUDSUBJ_dict.studentsubject_dict);
        console.log("mod_MSTUDSUBJ_dict.schemeitem_dict:", mod_MSTUDSUBJ_dict.schemeitem_dict);
        console.log("..................");
        return has_studsubj_rows;
    } // MSTUDSUBJ_FillDicts

//========= MSTUDSUBJ_FillTbls  ============= PR2020-11-17
    function MSTUDSUBJ_FillTbls(sel_schemeitem_pk_list) {
        console.log("===== MSTUDSUBJ_FillTbls ===== ");
        // function fills table el_tblBody_studsubjects and el_tblBody_schemeitems
        // with items of mod_MSTUDSUBJ_dict.studentsubject_dict and mod_MSTUDSUBJ_dict.schemeitem_dict
        // mod_MSTUDSUBJ_dict.studentsubject_dict also contains deleted subjects of student, with tag 'deleted'
        // sel_schemeitem_pk_list is a list of selected schemeitem_pk's, filled by MSTUDSUBJ_AddRemoveSubject

        // TODO also show deleted subjects in studsubject list, create undelete option PR2021-07-11

// ---  loop through studentsubjects
        el_tblBody_studsubjects.innerText = null;
        // studsubj_si_list is list of schemeitem_id's of subjects of this student, that are not deleted
        const studsubj_si_list = [];
        const studsubj_subj_list = [];
        let has_rows = false;

        for (const [studsubj_pk_str, dict] of Object.entries(mod_MSTUDSUBJ_dict.studentsubject_dict)) {
            const studsubj_pk = Number(studsubj_pk_str);
            if (!dict.isdeleted) {
        // - add schemeitem_pk of  studsubj to studsubj_si_list
                studsubj_si_list.push(dict.schemeitem_id)
                studsubj_subj_list.push(dict.subj_id)

                MSTUDSUBJ_CreateSelectRow("studsubj", el_tblBody_studsubjects, dict.schemeitem_id, dict, true, false);  // true = enabled
                has_rows = true;
            }
        }

        //console.log("studsubj_si_list", studsubj_si_list);
        //console.log("studsubj_subj_list", studsubj_subj_list);
// --- addrow 'This_candidate_has_nosubjects' if student has no subjects
        if(!has_rows){
            const tblRow = el_tblBody_studsubjects.insertRow(-1);
                const td = tblRow.insertCell(-1);
                    const el_div = document.createElement("div");
                        el_div.classList.add("tw_300", "px-2")
                        el_div.innerText = loc.This_candidate_has_nosubjects;
                td.appendChild(el_div);
        };

// ---  loop through mod_MSTUDSUBJ_dict.schemeitem_dict
        // mod_MSTUDSUBJ_dict.schemeitem_dict is a deepcopy dict with schemeitems of the scheme of this candidate, key = schemeitem_pk
        el_tblBody_schemeitems.innerText = null;
        for (const [schemeitem_pk_str, dict] of Object.entries(mod_MSTUDSUBJ_dict.schemeitem_dict)) {
            const schemeitem_pk = dict.id;
// skip subjects with 'sjt_one_allowed' when NIU

    // - skip subjects that are already in table of subjects of this student
            const skip_row = (studsubj_si_list.includes(schemeitem_pk))
            if (!skip_row ) {
    // - disable subject if subject is already in table of subjects of this student
                const enabled = !(studsubj_subj_list.includes(dict.subj_id));
                MSTUDSUBJ_CreateSelectRow("schemeitem", el_tblBody_schemeitems, schemeitem_pk, dict, enabled, false);
            }
        }
    } // MSTUDSUBJ_FillTbls

//========= MSTUDSUBJ_CreateSelectRow  ============= PR2020--09-30
    function MSTUDSUBJ_CreateSelectRow(tblName, tblBody_select, schemeitem_pk, dict, enabled, highlighted) {
        //console.log("===== MSTUDSUBJ_CreateSelectRow ===== ");
        //console.log("..........schemeitem_pk", schemeitem_pk);
        //console.log("dict", dict);
        //console.log("tblName", tblName);

        if (!isEmpty(dict)){
            let subj_code = (dict.subj_code) ? dict.subj_code : "";
            if(dict.is_combi) { subj_code += " *" }
            let subj_name = (dict.subj_name) ? dict.subj_name : null;
            const sjtp_abbrev = (dict.sjtp_abbrev) ? dict.sjtp_abbrev : null;
        //console.log("sjtp_abbrev", sjtp_abbrev);

// ---  lookup index where this row must be inserted
        let ob1 = "", ob2 = "", ob3 = "";

            if (dict.subj_name) { ob1 = dict.subj_name.toLowerCase() };
            if (dict.sjtpbase_code) { ob2 = dict.sjtpbase_code.toString()};

            const row_index = b_recursive_tblRow_lookup(tblBody_select, ob1, ob2, ob3, setting_dict.user_lang);

            const tblRow = tblBody_select.insertRow(row_index);
            tblRow.id = dict.mapid
            tblRow.setAttribute("data-pk", schemeitem_pk);

            const selected_int = 0
            tblRow.setAttribute("data-selected", selected_int);

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

            tblRow.setAttribute("data-selected", 0)

    // --- add second td to tblRow.
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                el_div.classList.add("tw_120")
                el_div.innerText = subj_code;
                tblRow.title = subj_name;
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
            }
        }
    } // MSTUDSUBJ_CreateSelectRow

//=========  MSTUDSUBJ_ClickedOrDoubleClicked  ================ PR2019-03-30 PR2021-03-05
    function MSTUDSUBJ_ClickedOrDoubleClicked(tblName, tblRow, event) {
        console.log("=== MSTUDSUBJ_ClickedOrDoubleClicked");
        console.log("event.target", event.target);
        console.log("event.detail", event.detail);
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
                const mode = (tblName === "studsubj") ? "remove" : "add";
                MSTUDSUBJ_AddRemoveSubject(mode)
        }
    }  // MSTUDSUBJ_ClickedOrDoubleClicked

//========= MSTUDSUBJ_SelectSubject  ============= PR2020-10-01 PR2021-03-05
    function MSTUDSUBJ_SelectSubject(tblName, tblRow){
        console.log( "===== MSTUDSUBJ_SelectSubject  ========= ");
        console.log( "tblName", tblName);

        if(tblRow){
            let is_selected = (!!get_attr_from_el_int(tblRow, "data-selected"));
            let pk_int = get_attr_from_el_int(tblRow, "data-pk");

        console.log( "is_selected", is_selected);
        console.log( "pk_int", pk_int);

// ---  toggle is_selected
            is_selected = !is_selected;

            const tblBody_selectTable = tblRow.parentNode;

// ---  in tbl "studsubj" and when selected: deselect all other rows
            if (tblName === "studsubj" && is_selected){
                // fill characteristics
                mod_MSTUDSUBJ_dict.sel_schemitem_pk = get_attr_from_el_int(tblRow, "data-pk")
                MSTUDSUBJ_SetInputFields(mod_MSTUDSUBJ_dict.sel_schemitem_pk, is_selected)
            }
// ---  put new value in this tblRow, show/hide tickmark PR2020-11-21
        tblRow.setAttribute("data-selected", ( (is_selected) ? 1 : 0) )
        add_or_remove_class(tblRow, "bg_selected_blue", is_selected )
        const img_class = (is_selected) ? "tickmark_0_2" : "tickmark_0_0"
        const el = tblRow.cells[0].children[0];
        if (el){el.className = img_class}
        }
    }  // MSTUDSUBJ_SelectSubject

    function MSTUDSUBJ_SetInputFields(schemitem_pk, is_selected){
// ---  put value in input box 'Characteristics of this subject
        console.log( "===== MSTUDSUBJ_SetInputFields  ========= ");
        console.log( "schemitem_pk", schemitem_pk);
        //console.log( "is_selected", is_selected);

        let is_empty = true, is_mand = false, is_combi = false, is_elective_combi = false,
            is_extra_counts = false, is_extra_nocount = false,
            pwstitle = null, pwssubjects = null,
            extra_count_allowed = false, extra_nocount_allowed = false, elective_combi_allowed = false;

        let sjtp_has_prac = false, sjtp_has_pws = false;

        let map_dict = {};

        if(is_selected && schemitem_pk && mod_MSTUDSUBJ_dict.studentsubject_dict[schemitem_pk]){
            map_dict = mod_MSTUDSUBJ_dict.studentsubject_dict[schemitem_pk];

        console.log( "map_dict", map_dict);
            if(!isEmpty(map_dict)){
                is_empty = false;
                is_mand = map_dict.is_mandatory
                is_combi = map_dict.is_combi
                extra_count_allowed = map_dict.extra_count_allowed
                extra_nocount_allowed = map_dict.extra_nocount_allowed
                elective_combi_allowed = map_dict.elective_combi_allowed
                is_extra_counts = map_dict.is_extra_counts,
                is_extra_nocount = map_dict.is_extra_nocount,
                is_elective_combi = map_dict.is_elective_combi,
                sjtp_has_prac = map_dict.sjtp_has_prac,
                sjtp_has_pws = map_dict.sjtp_has_pws,
                pwstitle = map_dict.pws_title,
                pwssubjects = map_dict.pws_subjects;

            }
        }
        document.getElementById("id_MSTUDSUBJ_char_header").innerText = (is_empty) ?  loc.No_subject_selected : map_dict.subj_name;

    // ---  put changed values of input elements in upload_dict
        const el_form_controls = document.getElementById("id_MSTUDSUBJ_div_form_controls").querySelectorAll(".awp_input_text, .awp_input_checkbox")
        for (let i = 0, el; el = el_form_controls[i]; i++) {
            const el_wrap = el.parentNode.parentNode.parentNode

            const field = get_attr_from_el(el, "data-field")
            const hide_element = (field === "is_mandatory") ? is_empty :
                                (field === "is_combi") ? is_empty :
                                 (field === "is_elective_combi") ? !map_dict.elective_combi_allowed :
                                 (field === "is_extra_nocount") ? !map_dict.extra_nocount_allowed :
                                 (field === "is_extra_counts") ? !map_dict.extra_count_allowed :
                                 (["pws_title", "pws_subjects"].includes(field) ) ? !map_dict.sjtp_has_pws : true;
            if(el_wrap){ add_or_remove_class(el_wrap, cls_hide, hide_element )}

           if(el.classList.contains("awp_input_text")){
                el.value = map_dict[field];
           } else if(el.classList.contains("awp_input_checkbox")){
                el.checked = (map_dict[field]) ? map_dict[field] : false;
           }
        }
    }  // MSTUDSUBJ_SetInputFields

//========= MSTUDSUBJ_AddRemoveSubject  ============= PR2020-11-18
    function MSTUDSUBJ_AddRemoveSubject(mode) {
        console.log("  =====  MSTUDSUBJ_AddRemoveSubject  =====");
        console.log("mode", mode);
        const tblBody = (mode === "add") ? el_tblBody_schemeitems : el_tblBody_studsubjects;
        const sel_schemeitem_pk_list = []

// ---  loop through tblBody and create list of selected schemeitem_pk's
        for (let i = 0, tblRow, is_selected, pk_int; tblRow = tblBody.rows[i]; i++) {
            is_selected = !!get_attr_from_el_int(tblRow, "data-selected")
            if (is_selected) {
                pk_int = get_attr_from_el_int(tblRow, "data-pk")
                sel_schemeitem_pk_list.push(pk_int);
            }
        }
        console.log("sel_schemeitem_pk_list", sel_schemeitem_pk_list);

// ---  loop through sel_schemeitem_pk_list
        for (let i = 0, pk_int; pk_int = sel_schemeitem_pk_list[i]; i++) {
            let map_dict = {};
            if(mode === "add"){
// ---  check if schemeitem_pk already exists in mod_MSTUDSUBJ_dict.studentsubject_dict
                const ss_map_dict = (mod_MSTUDSUBJ_dict.studentsubject_dict[pk_int]) ? mod_MSTUDSUBJ_dict.studentsubject_dict[pk_int] : {};
        console.log("mod_MSTUDSUBJ_dict.studentsubject_dict", mod_MSTUDSUBJ_dict.studentsubject_dict);
        console.log("ss_map_dict", deepcopy_dict(ss_map_dict));
                if (!isEmpty(ss_map_dict) ){
// if it exists it must be a deleted row, remove 'isdeleted'
                    ss_map_dict.isdeleted = false;
                } else {
                    const student_pk = mod_MSTUDSUBJ_dict.stud_id
// add row to mod_MSTUDSUBJ_dict.studentsubject_dict if it does not yet exist
                    const si_dict = mod_MSTUDSUBJ_dict.schemeitem_dict[pk_int];
                    if(!isEmpty(si_dict)){
                        const si_map_dict = deepcopy_dict(si_dict);
                          // in si_dict schemeitem_id = si_dict.id, in mod_MSTUDSUBJ_dict.studentsubject_dict it is mod_MSTUDSUBJ_dict.studentsubject_dict.schemeitem_id
                        si_map_dict.schemeitem_id = si_dict.id;
                        delete si_map_dict.id;
                        // si_map_dict.mapid overrides si_dict.mapid
                        si_map_dict.mapid = "studsubj_" + student_pk + "_"// mapid: "studsubj_29_2" = "studsubj_" + stud_id + "_" + studsubj_id
                        // adding keys that do't exist in si_dict
                        si_map_dict.stud_id = mod_MSTUDSUBJ_dict.student_pk;
                        si_map_dict.studsubj_id = null;

                        si_map_dict.is_elective_combi = false;
                        si_map_dict.is_extra_counts = false
                        si_map_dict.is_extra_nocount = false;
                        si_map_dict.pws_subjects = null;
                        si_map_dict.pws_title = null;

                        si_map_dict.modby_username = "---";
                        si_map_dict.modifiedat = "---";

                        si_map_dict.iscreated = true;
                        si_map_dict.isdeleted = false;
                        si_map_dict.haschanged = false;

                        mod_MSTUDSUBJ_dict.studentsubject_dict[pk_int] = si_map_dict;
                    }
                }
            }  else if(mode === "remove"){

    // ---  check if schemeitem_pk already exists in mod_MSTUDSUBJ_dict.studentsubject_dict
                const ss_map_dict = (mod_MSTUDSUBJ_dict.studentsubject_dict[pk_int]) ? mod_MSTUDSUBJ_dict.studentsubject_dict[pk_int] : {};
                console.log("ss_map_dict", deepcopy_dict(ss_map_dict));

                if (!isEmpty(ss_map_dict)) {
    // set 'isdeleted' = true
                    ss_map_dict.isdeleted = true;
                }

                MSTUDSUBJ_SetInputFields()
            }
        }  //  for (let i = 0, pk_int; pk_int = sel_schemeitem_pk_list[i]; i++)

        MSTUDSUBJ_FillTbls(sel_schemeitem_pk_list)

    }  // MSTUDSUBJ_AddRemoveSubject

//========= MSTUDSUBJ_AddPackage  ============= PR2020-11-18
    function MSTUDSUBJ_AddPackage() {
        console.log("  =====  MSTUDSUBJ_AddPackage  =====");

    }  // MSTUDSUBJ_AddPackage

//========= MSTUDSUBJ_InputboxEdit  ============= PR2020-12-01
    function MSTUDSUBJ_InputboxEdit(el_input) {
        console.log("  =====  MSTUDSUBJ_InputboxEdit  =====");
        if(el_input){
// ---  get dict of selected schemitem from mod_MSTUDSUBJ_dict.studentsubject_dict
            const field = get_attr_from_el(el_input, "data-field")
                const sel_studsubj_dict = mod_MSTUDSUBJ_dict.studentsubject_dict[mod_MSTUDSUBJ_dict.sel_schemitem_pk];
        console.log("sel_studsubj_dict", sel_studsubj_dict);
                if(sel_studsubj_dict){
        // ---  put new value of el_input in sel_studsubj_dict
                    if(el_input.classList.contains("awp_input_text")) {
                //console.log("awp_input_text");
                        sel_studsubj_dict[field] = el_input.value;
                        sel_studsubj_dict.haschanged = true;
        // ---  if checkbox: put checked value in sel_studsubj_dict
                    } else if(el_input.classList.contains("awp_input_checkbox")) {
                        if (["is_combi", "is_mandatory"].includes(field)){
                            // is_combi and is_mandatory cannot be changed.
                            // setting disabled makes checkbox grey, is not what we want
                            // therefore always undo changes after clicked om this checkbox
                            el_input.checked = !el_input.checked;
                        } else {
                //console.log("awp_input_checkbox");
                            const is_checked = el_input.checked;
                            sel_studsubj_dict[field] = is_checked;
                            sel_studsubj_dict.haschanged = true;
        // ---  if element is checked: uncheck other 'extra subject' element if that one is also checked
                            if(is_checked){
                                const other_field = (field === "is_extra_nocount") ? "is_extra_counts" : "is_extra_nocount";
                                const other_el = document.getElementById("id_MSTUDSUBJ_" + other_field)
                                if(other_el && other_el.checked){
                                    other_el.checked = false;
                                    sel_studsubj_dict[other_field] = false;
                                }
                            }
                        }  // if (field === "is_combi")

                    }
                }
        }
    }  // MSTUDSUBJ_InputboxEdit

//========= MSTUDSUBJ_CheckboxEdit  ============= PR2020-12-01
    function MSTUDSUBJ_CheckboxEdit(el_input) {
        //console.log("  =====  MSTUDSUBJ_CheckboxEdit  =====");
        if(el_input){
            const field = get_attr_from_el(el_input, "data-field")
            const is_checked = el_input.checked;
            const sel_studsubj_dict = mod_MSTUDSUBJ_dict.studentsubject_dict[mod_MSTUDSUBJ_dict.sel_schemitem_pk];
            if (sel_studsubj_dict) {
                sel_studsubj_dict[field] = is_checked;
                sel_studsubj_dict.haschanged = true;
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
        if (mode === "level"){
            setting_dict.sel_lvlbase_pk = (Number(el_select.value)) ? Number(el_select.value) : null;
            setting_dict.sel_level_abbrev = (el_select.options[el_select.selectedIndex]) ? el_select.options[el_select.selectedIndex].text : null;

            upload_dict = {selected_pk: {sel_lvlbase_pk: setting_dict.sel_lvlbase_pk}};
        } else if (mode === "sector"){
            setting_dict.sel_sctbase_pk = (Number(el_select.value)) ? Number(el_select.value) : null;
            setting_dict.sel_sector_abbrev = (el_select.options[el_select.selectedIndex]) ? el_select.options[el_select.selectedIndex].text : null;

            upload_dict = {selected_pk: {sel_sctbase_pk: setting_dict.sel_sctbase_pk}};

        }
            // ---  upload new setting

        UploadSettings (upload_dict, url_settings_upload);

        //UpdateHeaderLeft();

        FillTblRows();
    }  // HandleSbrLevelSector

//=========  FillOptionsSelectLevelSector  ================ PR2021-03-06  PR2021-05-22
    function FillOptionsSelectLevelSector(tblName, rows) {
        //console.log("=== FillOptionsSelectLevelSector");
        //console.log("tblName", tblName);
        //console.log("rows", rows);

    // sector not in use
        const display_rows = []
        const has_items = (!!rows && !!rows.length);
        const has_profiel = setting_dict.sel_dep_has_profiel;
        //console.log("has_items", has_items);
        //console.log("has_profiel", has_profiel);

        const caption_all = "&#60" + ( (tblName === "level") ? loc.All_leerwegen : (has_profiel) ? loc.All_profielen : loc.All_sectors ) + "&#62";
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
                display_rows.push({
                value: row.base_id,
                caption: (tblName === "sector") ? row.name : row.abbrev
                })
            }

            const selected_pk = (tblName === "level") ? setting_dict.sel_lvlbase_pk : (tblName === "sector") ? setting_dict.sel_sctbase_pk : null;
            const el_SBR_select = (tblName === "level") ? el_SBR_select_level : (tblName === "sector") ? el_SBR_select_sector : null;
            t_FillOptionsFromList(el_SBR_select, display_rows, "value", "caption", null, null, selected_pk);

            // put displayed text in setting_dict
            const sel_abbrev = (el_SBR_select.options[el_SBR_select.selectedIndex]) ? el_SBR_select.options[el_SBR_select.selectedIndex].text : null;
            if (tblName === "level"){
                setting_dict.sel_level_abbrev = sel_abbrev;
            } else if (tblName === "sector"){
                setting_dict.sel_sector_abbrev = sel_abbrev;
            }
        }
        // show select level and sector
        if (tblName === "level"){
            add_or_remove_class(document.getElementById("id_SBR_container_level"), cls_hide, false);
        // set label of profiel
         } else if (tblName === "sector"){
            add_or_remove_class(document.getElementById("id_SBR_container_sector"), cls_hide, false);

            document.getElementById("id_SBR_select_sector_label").innerText = ( (has_profiel) ? loc.Profiel : loc.Sector ) + ":";
        }
    }  // FillOptionsSelectLevelSector

//=========  HandleShowAll  ================ PR2020-12-17
    function HandleShowAll() {
        console.log("=== HandleShowAll");
        console.log("setting_dict", setting_dict);

        setting_dict.sel_lvlbase_pk = null;
        setting_dict.sel_level_abbrev = null;

        setting_dict.sel_sctbase_pk = null;
        setting_dict.sel_sector_abbrev = null;

        setting_dict.sel_subject_pk = null;
        setting_dict.sel_student_pk = null;

        el_SBR_select_level.value = "0";
        el_SBR_select_sector.value = "0";

// ---  upload new setting
        const selected_pk_dict = {sel_lvlbase_pk: null, sel_sctbase_pk: null, sel_subject_pk: null, sel_student_pk: null};
        //const page_grade_dict = {sel_btn: "grade_by_all"}
       //const upload_dict = {selected_pk: selected_pk_dict, page_grade: page_grade_dict};
        const upload_dict = {selected_pk: selected_pk_dict};
        UploadSettings (upload_dict, url_settings_upload);

        HandleBtnSelect("grade_by_all", true) // true = skip_upload
        // also calls: FillTblRows(), MSSSS_display_in_sbr(), UpdateHeader()

    }  // HandleShowAll


// +++++++++++++++++ END OF MODAL SIDEBAR SELECT +++++++++++++++++++++++++++++++++++

// +++++++++++++++++ MODAL SELECT COLUMNS ++++++++++++++++++++++++++++++++++++++++++
//=========  MCOL_Open  ================ PR2021-07-07
    function MCOL_Open() {
       //console.log(" -----  MCOL_Open   ----")
        mod_MCOL_dict = {col_hidden: []}

        const tblName = (selected_btn === "btn_published")? "published" : "studsubj";
        const col_hidden = (columns_hidden[tblName]) ? columns_hidden[tblName] : [];
        for (let i = 0, field; field = col_hidden[i]; i++) {
            mod_MCOL_dict.col_hidden.push(field);
        };

        MCOL_FillSelectTable();

        el_MCOL_btn_save.disabled = true
// ---  show modal, set focus on save button
       $("#id_mod_select_columns").modal({backdrop: true});
    }  // MCOL_Open

//=========  ModColumns_Save  ================ PR2021-07-07
    function ModColumns_Save() {
        console.log(" -----  ModColumns_Save   ----")

// ---  get hidden columns from mod_MCOL_dict.col_hidden and put them  in columns_hidden[tblName]
        const tblName = (selected_btn === "btn_published")? "published" : "studsubj";
        console.log("tblName", tblName)
        if (!(tblName in columns_hidden)){
            columns_hidden[tblName] = [];
        }
        const col_hidden = columns_hidden[tblName];
        console.log("col_hidden", col_hidden)
   // clear the array
        b_clear_array(col_hidden);
   // add hidden columns to col_hidden
        for (let i = 0, field; field = mod_MCOL_dict.col_hidden[i]; i++) {
            col_hidden.push(field);
        };
// upload the new list of hidden columns
        const page_dict = {};
        page_dict[tblName] = col_hidden;
        const upload_dict = {page_studsubj: {col_hidden: page_dict }};
        console.log("upload_dict", upload_dict)
        UploadSettings (upload_dict, url_settings_upload);

        HandleBtnSelect(selected_btn, true)  // true = skip_upload

// hide modal
        // in HTML: data-dismiss="modal"
    }  // ModColumns_Save

//=========  MCOL_FillSelectTable  ================ PR2021-07-07
    function MCOL_FillSelectTable() {
        console.log("===  MCOL_FillSelectTable == ");

        el_MCOL_tblBody_available.innerHTML = null;
        el_MCOL_tblBody_show.innerHTML = null;

        const tblName = (selected_btn === "btn_published")? "published" : "studsubj";
        const field_names = field_settings[tblName].field_names;
        const field_captions = field_settings[tblName].field_caption;

//+++ loop through list of field_names
        if(field_names && field_names.length){

        console.log("columns_tobe_hidden", columns_tobe_hidden);
        console.log("columns_tobe_hidden_caption", columns_tobe_hidden_caption);
            const len = field_names.length;
            for (let j = 0; j < len; j++) {
                const field_name = field_names[j];

        console.log(j, " field_name", field_name);
                if (columns_tobe_hidden.includes(field_name))  {
                    const field_caption = (field_name === "sct_abbrev") ?
                                    (setting_dict.sel_dep_has_profiel) ? loc.Profiel : loc.Sector :
                                    (columns_tobe_hidden_caption[j]) ? loc[columns_tobe_hidden_caption[j]] : null;

        console.log("columns_tobe_hidden_caption[j]", columns_tobe_hidden_caption[j]);
        console.log("loc[columns_tobe_hidden_caption[j]]", loc[columns_tobe_hidden_caption[j]]);
                    const is_hidden = (field_name && mod_MCOL_dict.col_hidden.includes(field_name));
                    const tBody = (is_hidden) ? el_MCOL_tblBody_available : el_MCOL_tblBody_show;

        //+++ insert tblRow into tBody
                    const tblRow = tBody.insertRow(-1);
                    tblRow.setAttribute("data-field", field_name);

            // --- add EventListener to tblRow.
                    tblRow.addEventListener("click", function() {MCOL_SelectItem(tblRow);}, false )
            //- add hover to tableBody row
                    add_hover(tblRow)

                    const td = tblRow.insertCell(-1);
                    td.innerText = field_caption;
            //- add data-tag  to tblRow
                    td.classList.add("tw_240")

                    tblRow.setAttribute("data-field", field_name);
                }
            }
        }  // if(field_captions && field_captions.length)
    } // MCOL_FillSelectTable

//=========  MCOL_SelectItem  ================ PR2021-07-07
    function MCOL_SelectItem(tr_clicked) {
        console.log("===  MCOL_SelectItem == ");
        if(!!tr_clicked) {
            const field_name = get_attr_from_el(tr_clicked, "data-field")
            const is_hidden = (field_name && mod_MCOL_dict.col_hidden.includes(field_name));
            if (is_hidden){
                b_remove_item_from_array(mod_MCOL_dict.col_hidden, field_name);
            } else {
                mod_MCOL_dict.col_hidden.push(field_name)
            }
            MCOL_FillSelectTable();
            // enable sasave btn
            el_MCOL_btn_save.disabled = false;
        }
    }  // MCOL_SelectItem


// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2020-08-03
    function ModConfirmOpen(mode, el_input) {
        console.log(" -----  ModConfirmOpen   ----")
        // values of mode are : "delete", "inactive" or "resend_activation_email", "permission_sysadm"

        if(permit_dict.permit_crud){


    // ---  get selected_pk
            let tblName = null, selected_pk = null;
            // tblRow is undefined when clicked on delete btn in submenu btn or form (no inactive btn)
            const tblRow = get_tablerow_selected(el_input);
            if(tblRow){
                tblName = get_attr_from_el(tblRow, "data-table")
                selected_pk = get_attr_from_el(tblRow, "data-pk")
            } else {
                tblName = "studsubj";
                selected_pk = (tblName === "student") ? selected.student_pk :
                            (tblName === "department") ? selected_department_pk :
                            (tblName === "level") ? selected_level_pk :
                            (tblName === "sector") ? selected_sector_pk :
                            (tblName === "subjecttype") ? selected_subjecttype_pk :
                            (tblName === "scheme") ? selected_scheme_pk :
                            (tblName === "package") ? selected_package_pk : null;
            }
            console.log("selected_pk", selected_pk )

    // ---  get info from data_map
            const data_map = get_datamap_from_tblName(tblName)
            const map_id =  tblName + "_" + selected_pk;
            const map_dict = get_mapdict_from_datamap_by_id(subject_map, map_id)

            console.log("data_map", data_map)
            console.log("map_id", map_id)
            console.log("map_dict", map_dict)

    // ---  create mod_dict
            mod_dict = {mode: mode};
            const has_selected_item = (!isEmpty(map_dict));
            if(has_selected_item){
                mod_dict.id = map_dict.id;
                mod_dict.abbrev = map_dict.abbrev;
                mod_dict.name = map_dict.name;
                mod_dict.sequence = map_dict.sequence;
                mod_dict.depbases = map_dict.depbases;
                mod_dict.mapid = map_id;
            };
            if (mode === "inactive") {
                  mod_dict.current_isactive = map_dict.is_active;
            }

    // ---  put text in modal form
            let dont_show_modal = false;

            let header_text = loc.Delete + " ";
            const item = (tblName === "subject") ? loc.Subject :
                           (tblName === "department") ? loc.Department :
                           (tblName === "level") ? loc.Level :
                           (tblName === "sector") ? loc.Sector :
                           (tblName === "subjecttype") ? loc.Subjecttype :
                           (tblName === "scheme") ? loc.Scheme :
                           (tblName === "package") ? loc.Package : "";

            let msg_01_txt = null, msg_02_txt = null, msg_03_txt = null;
            let hide_save_btn = false;
            if(!has_selected_item){
                msg_01_txt = loc.No_user_selected;
                hide_save_btn = true;
            } else {
                const username = (map_dict.username) ? map_dict.username  : "-";
                if(mode === "delete"){
                    msg_01_txt = loc.User + " '" + username + "'" + loc.will_be_deleted
                    msg_02_txt = loc.Do_you_want_to_continue;
                }
            }
            if(!dont_show_modal){
                el_confirm_header.innerText = header_text;
                el_confirm_loader.classList.add(cls_visible_hide)
                el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");
                el_confirm_msg01.innerText = msg_01_txt;
                el_confirm_msg02.innerText = msg_02_txt;
                el_confirm_msg03.innerText = msg_03_txt;

                const caption_save = (mode === "delete") ? loc.Yes_delete :
                                (mode === "inactive") ? ( (mod_dict.current_isactive) ? loc.Yes_make_inactive : loc.Yes_make_active ) : loc.OK;
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
        console.log(" --- ModConfirmSave --- ");
        console.log("mod_dict: ", mod_dict);
        let close_modal = !permit_dict.permit_crud;

        if(permit_dict.permit_crud){
            let tblRow = document.getElementById(mod_dict.mapid);

    // ---  when delete: make tblRow red, before uploading
            if (tblRow && mod_dict.mode === "delete"){
                ShowClassWithTimeout(tblRow, "tsa_tr_error");
            }

            if(["delete", 'resend_activation_email'].includes(mod_dict.mode)) {
    // show loader
                el_confirm_loader.classList.remove(cls_visible_hide)
            } else if (mod_dict.mode === "inactive") {
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
            let upload_dict = { id: {pk: mod_dict.user_pk,
                                     ppk: mod_dict.user_ppk,
                                     table: "user",
                                     mode: mod_dict.mode,
                                     mapid: mod_dict.mapid}};
            if (mod_dict.mode === "inactive") {
                upload_dict.is_active = {value: mod_dict.new_isactive, update: true}
            };

            console.log("upload_dict: ", upload_dict);
            UploadChanges(upload_dict, url_subject_upload);
        };
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
            let msg01_text = null, msg02_text = null, msg03_text = null;
            if ("msg_err" in response) {
                msg01_text = get_dict_value(response, ["msg_err", "msg01"], "");
                if (mod_dict.mode === "resend_activation_email") {
                    msg02_text = loc.Activation_email_not_sent;
                }
                el_confirm_msg_container.classList.add("border_bg_invalid");
            } else if ("msg_ok" in response){
                msg01_text  = get_dict_value(response, ["msg_ok", "msg01"]);
                msg02_text = get_dict_value(response, ["msg_ok", "msg02"]);
                msg03_text = get_dict_value(response, ["msg_ok", "msg03"]);
                el_confirm_msg_container.classList.add("border_bg_valid");
            }
            el_confirm_msg01.innerText = msg01_text;
            el_confirm_msg02.innerText = msg02_text;
            el_confirm_msg03.innerText = msg03_text;
            el_confirm_btn_cancel.innerText = loc.Close
            el_confirm_btn_save.classList.add(cls_hide);
        } else {
        // hide mod_confirm when no message
            $("#id_mod_confirm").modal("hide");
        }
    }  // ModConfirmResponse

//###########################################################################
// +++++++++++++++++ REFRESH DATA ROWS +++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataRowsStudsubjAfterUpload  ================ PR2021-07-20
    function RefreshDataRowsStudsubjAfterUpload(response) {
        console.log(" --- RefreshDataRowsStudsubjAfterUpload  ---");
        console.log( "response", response);
        // TODO
    }  //  RefreshDataRowsStudsubjAfterUpload

//=========  RefreshDataRows  ================  PR2021-06-21
    function RefreshDataRows(tblName, update_rows, data_rows, is_update) {
        //console.log(" --- RefreshDataRows  ---");
        //console.log("update_rows", update_rows);
        //console.log("data_rows", data_rows);
        //console.log("is_update", is_update);

        const field_names = ["subj_error", "subj_status",
                    "has_exemption", "exm_status", "has_reex", "re2_status", "has_reex03", "re3_status",
                    "has_pok", "pok_status", "notes"]

        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length
        if (update_rows && update_rows.length ) {
            const field_setting = field_settings[tblName];
            for (let i = 0, update_dict; update_dict = update_rows[i]; i++) {
                RefreshDatarowItem(tblName, field_setting, field_names, update_dict, data_rows);
            }
        } else if (!is_update) {
            // empty the data_rows when update_rows is empty PR2021-01-13 debug forgot to empty data_rows
            // PR2021-03-13 debug. Don't empty de data_rows when is update. Returns [] when no changes made
           data_rows = [];
        }
    }  //  RefreshDataRows


//=========  RefreshDatarowItem  ================ PR2020-08-16 PR2020-09-30 PR2021-06-21
    function RefreshDatarowItem(tblName, field_setting, field_names, update_dict, data_rows) {
        //console.log(" --- RefreshDatarowItem  ---");
        //console.log("tblName", tblName);
    //console.log("update_dict", update_dict);

        if(!isEmpty(update_dict)){

            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);

            let updated_columns = [];
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

    //console.log("field_error_list", field_error_list);
            //} else {
            // close modal MSJ when no error --- already done in modal
                //$("#id_mod_subject").modal("hide");
            }

            const col_hidden = (columns_hidden[tblName]) ? columns_hidden[tblName] : [];

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

    // ---  scrollIntoView,
                if(new_tblRow){
                    new_tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' })
    // ---  make new row green for 2 seconds,
                    ShowOkElement(new_tblRow);
                }
            } else {

// +++ get existing data_dict from data_rows. data_rows is ordered by: studsubj_id, stud_id'
                // studsubj_id can be None, sort them first so it can be given the value of 0 in b_recursive_integer_lookup
                // field with nulls must be ordered first
                const data_rows = (selected_btn === "btn_published") ? published_rows : studsubj_rows;
                const student_pk = (update_dict.stud_id) ? update_dict.stud_id : 0;
                const studsubj_pk = (update_dict.studsubj_id) ? update_dict.studsubj_id : 0;
                let data_dict = get_mapdict_by_integer_from_datarows(data_rows, null, student_pk, studsubj_pk)
    //console.log( "data_dict", data_dict);
    //console.log( "data_rows", data_rows);

// ++++ deleted ++++
                if(is_deleted){
                    // delete row from data_rows. Splice returns array of deleted rows
                    const deleted_row_arr = data_rows.splice(datarow_index, 1)
                    const deleted_row_dict = deleted_row_arr[0];
    //console.log("deleted_row_dict", deleted_row_dict);
    //console.log("deleted_row_dict.mapid", deleted_row_dict.mapid);

        //--- delete tblRow
                    if(deleted_row_dict && deleted_row_dict.mapid){
                        const tblRow_tobe_deleted = document.getElementById(deleted_row_dict.mapid);
    //console.log("tblRow_tobe_deleted", tblRow_tobe_deleted);
                        if (tblRow_tobe_deleted ){
                            tblRow_tobe_deleted.parentNode.removeChild(tblRow_tobe_deleted)
                        };
                    }
                } else {

    //console.log(".....field_names", field_names);

// +++++++++++ updated row +++++++++++
    // ---  check which fields are updated, add to list 'updated_columns'
                    if(!isEmpty(data_dict) && field_names){

// ---  first add updated fields to updated_columns list, before updating data_row
                        let updated_columns = [];
                        // skip first column (is margin)
                        for (let i = 1, col_field, old_value, new_value; col_field = field_names[i]; i++) {
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
        //console.log("updated_columns", updated_columns);

// ---  update fields in data_row
                        for (const [key, new_value] of Object.entries(update_dict)) {
                            if (key in data_dict){
                                if (new_value !== data_dict[key]) {
                                    data_dict[key] = new_value
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
                                    tblRow = CreateTblRow(tblName, field_setting, map_id, update_dict)
                                };

    //console.log("tblRow", tblRow);
                // loop through cells of row
                                for (let i = 1, el_fldName, el, td; td = tblRow.cells[i]; i++) {
                                    el = td.children[0];
                                    if (el){
    //console.log("el", el);
                                        el_fldName = get_attr_from_el(el, "data-field")
    //console.log("el_fldName", el_fldName);
                                        UpdateField(el, update_dict);

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
                                            ShowOkElement(el);
                                        };
                                    }  //  if (el){
                                };  //  for (let i = 1, el_fldName, el; el = tblRow.cells[i]; i++) {
                            };  // if(tblRow){
                        }; //  if(updated_columns.length){
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

//========= HandleFilterField  ====================================
    function HandleFilterField(el_filter, col_index, event) {
        //console.log( "===== HandleFilterField  ========= ");
        // skip filter if filter value has not changed, update variable filter_text

        //console.log( "el_filter", el_filter);
        //console.log( "col_index", col_index);
        //const filter_tag = get_attr_from_el(el_filter, "data-filtertag")
        //console.log( "filter_tag", filter_tag);

// --- get filter tblRow and tblBody
        const tblRow = get_tablerow_selected(el_filter);
        const tblName = get_attr_from_el(tblRow, "data-table")

// --- reset filter row when clicked on 'Escape'
        const skip_filter = t_SetExtendedFilterDict(el_filter, col_index, filter_dict, event.key);
        //console.log( "skip_filter", skip_filter);

        if (filter_tag === "toggle") {
// ---  toggle filter_checked
            let filter_checked = (col_index in filter_dict) ? filter_dict[col_index] : 0;
    // ---  change icon
            let el_icon = el_filter.children[0];
            if(el_icon){
                add_or_remove_class(el_icon, "tickmark_0_0", !filter_checked)
                if(filter_tag === "toggle"){
                    add_or_remove_class(el_icon, "tickmark_0_1", filter_checked === -1)
                    add_or_remove_class(el_icon, "tickmark_0_2", filter_checked === 1)
                }
            }

        } else if (filter_tag === "activated") {
// ---  toggle activated
            let filter_checked = (col_index in filter_dict) ? filter_dict[col_index] : 0;
            filter_checked += 1
            if (filter_checked > 1) { filter_checked = -2 }
            if (!filter_checked){
                delete filter_dict[col_index];
            } else {
                filter_dict[col_index] = filter_checked;
            }
    // ---  change icon
            let el_icon = el.children[0];
            if(el_icon){
                add_or_remove_class(el_icon, "tickmark_0_0", !filter_checked)
                add_or_remove_class(el_icon, "exclamation_0_2", filter_checked === -2)
                add_or_remove_class(el_icon, "tickmark_0_1", filter_checked === -1)
                add_or_remove_class(el_icon, "tickmark_0_2", filter_checked === 1)
            }
        }

        Filter_TableRows();
    }; // HandleFilterField

//========= Filter_TableRows  ==================================== PR2020-08-17
    function Filter_TableRows() {
        //console.log( "===== Filter_TableRows  ========= ");

        const tblName = (selected_btn === "btn_published")? "published" : "studsubj";

// ---  loop through tblBody.rows
        for (let i = 0, tblRow, show_row; tblRow = tblBody_datatable.rows[i]; i++) {
            show_row = ShowTableRow(tblRow, tblName_settings)
            add_or_remove_class(tblRow, cls_hide, !show_row)
        }
    }; // Filter_TableRows

//========= ShowTableRow  ==================================== PR2020-08-17
    function ShowTableRow(tblRow, tblName_settings) {
        // only called by Filter_TableRows
        //console.log( "===== ShowTableRow  ========= ");
        //console.log( "filter_dict", filter_dict);
        let hide_row = false;
        if (tblRow){
// show all rows if filter_name = ""
            if (!isEmpty(filter_dict)){
                for (const [col_index, item_arr] of Object.entries(filter_dict)) {
                    if (item_arr && item_arr.length){
                        const el = tblRow.cells[col_index];
                        const filter_tag = item_arr[0];
                        const filter_text = item_arr[1];
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
                                        hide = true
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

                    }  //  if (item_dict){
                } // for (const [ key, value ] of Object.entries(filter_dict))
            }  // if if (!isEmpty(filter_dict))
        }  // if (!!tblRow)
        return !hide_row
    }; // ShowTableRow

//========= ResetFilterRows  ====================================
    function ResetFilterRows() {  // PR2019-10-26 PR2020-06-20
       //console.log( "===== ResetFilterRows  ========= ");

        selected.studentsubject_dict = null;
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

//###########################################################################
// +++++++++++++++++ MODAL SELECT EXAMYEAR OR DEPARTMENT  ++++++++++++++++++++
// functions are in table.js, except for MSED_Response

//=========  MSED_Response  ================ PR2020-12-18 PR2021-05-10
    function MSED_Response(new_setting) {
        console.log( "===== MSED_Response ========= ");
        console.log( "new_setting", new_setting);

// ---  upload new selected_pk
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
        console.log( "===== MSSSS_Response ========= ");
        console.log( "tblName", tblName);
        console.log( "selected_pk", selected_pk);
        console.log( "selected_dict", selected_dict);

        if(selected_pk === -1) { selected_pk = null};

// +++ get existing map_dict from data_rows
        const data_rows = (tblName === "subject") ? subject_rows :  (tblName === "student") ? student_rows : null;
        const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", selected_pk);
        const map_dict = selected_dict
        const datarow_index = index;

        console.log( "map_dict", map_dict);

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
            UploadSettings (upload_dict, url_settings_upload);

        } else if (tblName === "student") {
            setting_dict.sel_student_pk = selected_pk;
    // reset selected subject when student is selected, in setting_dict and upload_dict
            if(selected_pk){
                //selected_pk_dict.sel_subject_pk = null;
                setting_dict.sel_subject_pk = null;
            }
            // ---  upload new setting
            const upload_dict = {selected_pk: {sel_student_pk: setting_dict.sel_student_pk, sel_subject_pk: null}};
            UploadSettings (upload_dict, url_settings_upload);
        }

        if (tblName === "school") {

        } else {
            //UploadSettings ({selected_pk: selected_pk_dict}, url_settings_upload);
console.log("selected_dict", selected_dict)
    // --- update header text
            const selected_name = (selected_dict) ?
                                    (tblName === "subject") ? selected_dict.name :
                                    (tblName === "student") ? selected_dict.fullname : null
                                  : null;
            UpdateHeaderText(selected_name);

    // ---  fill datatable
            FillTblRows(tblName, selected_pk)

    // fill datatable

            //MSSSS_display_in_sbr()
    // --- update header text - comes after MSSSS_display_in_sbr
            //UpdateHeaderLeft();

        }
    }  // MSSSS_Response
//////////////////////////////////////////////
//>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

//========= MOD APPROVE SUBJECTS ====================================
    function MASS_Open (open_mode ) {
        console.log("===  MASS_Open  =====") ;
        console.log("open_mode", open_mode) ;
        mod_MASS_dict = {}

        const is_approve = (open_mode === "approve");
        const is_submit = (open_mode === "submit");

        // b_get_statusindex_of_requsr returns index of auth user, returns 0 when user has none or multiple auth usergroups
        // gives err messages when multiple found.
        // status_index 1 = auth1, 2 = auth2
        const status_index = b_get_statusindex_of_requsr(loc, permit_dict);
        console.log("status_index", status_index);

        if (permit_dict.permit_approve_subject || permit_dict.permit_submit_subject) {
            if(status_index){
                // modes are 'approve' 'submit_test' 'submit_submit'
                mod_MASS_dict = {is_approve: is_approve,
                            is_submit: is_submit,
                            status_index: status_index,
                            test_is_ok: false,
                            submit_is_ok: false,
                            step: 0,
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
                    const data_dict = b_get_mapdict_by_integer_from_datarows(subject_rows, "id", setting_dict.sel_subject_pk)
                    subject_text =  (data_dict.name) ? data_dict.name : "---"
                } else {
                    subject_text = "<" + loc.All_subjects + ">";
                }
                el_MASS_subject.innerText = subject_text;

    // ---  show info container and delete button only in approve mode
                console.log("...........is_submit", is_submit) ;
                add_or_remove_class(el_MASS_select_container, cls_hide, is_submit)
                add_or_remove_class(el_MASS_btn_delete, cls_hide, is_submit)

                add_or_remove_class(el_MASS_info_container, cls_hide, true)

    // ---  show info and hide loader
                // PR2021-01-21 debug 'display_hide' not working when class 'image_container' is in same div
                add_or_remove_class(el_MASS_loader, cls_hide, true);

                MASS_Save ("save", true);  // true = is_test

    // --- reset ok button
                MASS_SetBtnSaveDeleteCancel();

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

            //  upload_dict.modes are: 'approve_test', 'approve_submit', 'approve_reset', 'submit_test', 'submit_submit'
            let url_str = url_studsubj_approve_multiple;
            const upload_dict = { table: "studsubj",
                                    now_arr: get_now_arr()  // only for timestamp on filename saved Ex-form
                                };

            if (mod_MASS_dict.step === 0){
                url_str = url_studsubj_approve_multiple;
                upload_dict.mode = (mod_MASS_dict.is_submit) ? "submit_test" : "approve_test";
            } else if (mod_MASS_dict.step === 1){
                if (mod_MASS_dict.is_approve){
                    upload_dict.mode = (mod_MASS_dict.is_reset) ? "approve_reset" : "approve_submit";
                 } else if (mod_MASS_dict.is_submit){
                    url_str = url_studsubj_send_email_exform;
                 }
            } else if (mod_MASS_dict.step === 2){
                if (mod_MASS_dict.is_submit){
                    upload_dict.mode = "submit_submit";
                    upload_dict.verificationcode = el_MASS_input_verifcode.value
                    upload_dict.verificationkey = mod_MASS_dict.verificationkey;
                }
            } else if (mod_MASS_dict.step === 3){
                if (mod_MASS_dict.is_submit){

                }
            }

    // ---  show loader
            add_or_remove_class(el_MASS_loader, cls_hide, false)

    // ---  upload changes
            UploadChanges(upload_dict, url_str);

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

        mod_MASS_dict.step += 1,
        mod_MASS_dict.test_is_ok = response.test_is_ok;
        mod_MASS_dict.verificationkey = response.verificationkey;
        const count_dict = (response.approve_count_dict) ? response.approve_count_dict : {};

/*
already_approved_by_auth: 5
already_published: 31
auth_missing: 0
committed: 0
count: 36
double_approved: 0
reset: 0
save_error: 0
saved: 0
student_committed_count: 0
student_count: 4
student_saved_count: 0
test_is_ok: false
*/
        mod_MASS_dict.has_already_approved_by_auth = (!!count_dict.already_approved_by_auth)
        mod_MASS_dict.submit_is_ok = (!!count_dict.saved)
        //mod_MASS_dict.has_already_published = (!!msg_dict.already_published)
        //mod_MASS_dict.has_saved = !!msg_dict.saved;

        add_or_remove_class(el_MASS_loader, cls_hide, true)
        add_or_remove_class(el_MASS_info_container, cls_hide, false)

        console.log("response.approve_count_dict", response.approve_count_dict);
        el_MASS_info_container.innerHTML = (response.approve_msg_html) ? response.approve_msg_html : null;




        MASS_SetBtnSaveDeleteCancel ();
        if ("updated_studsubj_approve_rows" in response){
            RefreshDataRows("studsubj", response.updated_studsubj_approve_rows, studsubj_rows, true);
        }

    };  // MASS_UpdateFromResponse

//=========  MASS_InputVerifcode  ================ PR2021-07-30
     function MASS_InputVerifcode(el_input) {
        console.log("===  MASS_InputVerifcode  =====") ;

        const value =  el_input.value
        console.log("value", value) ;
        MASS_SetBtnSaveDeleteCancel() ;
     };  // MASS_InputVerifcode

//=========  MASS_SetBtnSaveDeleteCancel  ================ PR2021-02-08
     function MASS_SetBtnSaveDeleteCancel() {
        console.log("===  MASS_SetBtnSaveDeleteCancel  =====") ;

        const is_approve = mod_MASS_dict.is_approve;
        const is_submit = mod_MASS_dict.is_submit;
        const is_reset = mod_MASS_dict.is_reset;

        const step = mod_MASS_dict.step;
        const test_is_ok = mod_MASS_dict.test_is_ok;
        const submit_is_ok = mod_MASS_dict.submit_is_ok;

        const has_already_published = !!mod_MASS_dict.has_already_published;
        const has_saved = !!mod_MASS_dict.has_saved;

        console.log("is_approve", is_approve) ;
        console.log("is_submit", is_submit) ;
        console.log("is_reset", is_reset) ;

        console.log("test_is_ok", test_is_ok) ;
        console.log("submit_is_ok", submit_is_ok) ;

        console.log("has_already_published", has_already_published) ;
        console.log("has_saved", has_saved) ;
        console.log("........step", step) ;

// ---  hide save button when not can_publish
        let hide_save_btn = true, disable_save_btn = false, save_btn_txt = null, hide_delete_btn = true;
        let hide_select_container = true, hide_apply_code = true;
        if (step === 0) {
        } else if (step === 1) {
            hide_select_container = (is_submit);
            hide_apply_code = (!is_submit || !test_is_ok);
            hide_delete_btn = (is_submit || !mod_MASS_dict.has_already_approved_by_auth);
            hide_save_btn = (!test_is_ok);
            save_btn_txt = (is_submit) ? loc.Apply_verificationcode : loc.Approve_subjects;
        } else if (step === 2) {
            if ( is_approve && submit_is_ok) {
                $("#id_mod_approve_studsubj").modal("hide");
            } else {
                disable_save_btn = !el_MASS_input_verifcode.value
                hide_save_btn = false;
                save_btn_txt = (is_submit) ? loc.Submit_Ex1_form : loc.Approve_grades
            }
        } else if (step === 3) {
        }
// - hide el_MASS_select_container
        add_or_remove_class(el_MASS_select_container, cls_hide, hide_select_container);
// - hide el_MASS_apply_code_container
        add_or_remove_class(el_MASS_apply_code_container, cls_hide, hide_apply_code);

// - hide save button in step 0 and 3
        add_or_remove_class(el_MASS_btn_save, cls_hide, hide_save_btn);
// ---  disable save button till test is finished
        el_MASS_btn_save.disabled = disable_save_btn;
// ---  set innerText of save_btn
        el_MASS_btn_save.innerText = save_btn_txt;
// ---  hide delete btn
        add_or_remove_class(el_MASS_btn_delete, cls_hide, hide_delete_btn);

// ---  set innerText of cancel_btn
        el_MASS_btn_cancel.innerText = (submit_is_ok || (!test_is_ok) || (!submit_is_ok)) ? loc.Close : loc.Cancel;

// show input verifcode on step 2, set focus
        add_or_remove_class(el_MASS_input_verifcode.parentNode, cls_hide, (step !== 2));
        if (step === 2){set_focus_on_el_with_timeout(el_MASS_input_verifcode, 150); };


     } //  MASS_SetBtnSaveDeleteCancel

/////////////////////////////////////////////

//========= DownloadGradeStatusAndIcons ============= PR2021-07-24
    function DownloadValidationStatusNotes() {
        //console.log( " ==== DownloadGradeStatusAndIcons ====");
        const url_str = url_studsubj_validate_all;
        const upload_dict = {studsubj_validate: {get: true}};
        UploadChanges(upload_dict, url_str);

     } // DownloadGradeStatusAndIcons

//========= ResponseValidationAll ============= PR2021-07-24
    function ResponseValidationAll(validate_studsubj_list) {
        //console.log( " ==== ResponseValidationAll ====");

// ---  loop through validate_studsubj_list and add key 'subj_error'
        for (let i = 0, row; row = studsubj_rows[i]; i++) {
            row.subj_error = (validate_studsubj_list && row.stud_id && validate_studsubj_list.includes(row.stud_id))
        }
        FillTblRows()

    };  // ResponseValidationAll

///////////////////

//========= get_mapdict_by_integer_from_datarows ============= PR2021-07-25
    function get_mapdict_by_integer_from_datarows(data_rows, tblRow, student_pk, studsubj_pk) {
        console.log( " ==== get_mapdict_by_integer_from_datarows ====");
        // if tblRow has value: get student_pk, studsubj_pk from tblRow.id
        if (tblRow){
            const arr = tblRow.id.split("_");
            student_pk = (arr[1] && Number(arr[1])) ? Number(arr[1]) : 0;
            studsubj_pk = (arr[2] && Number(arr[2])) ? Number(arr[2]) : 0;
        };
// +++ get existing data_dict from data_rows. data_rows is ordered by: studsubj_id, stud_id'
        // studsubj_id can be None, sort them first so it can be given the value of 0 in b_recursive_integer_lookup
        // field with nulls must be ordered first
        const lookup_1_field = (selected_btn === "btn_published") ? "id" : "studsubj_id";
        const lookup_2_field = (selected_btn === "btn_published") ? null : "stud_id";
        const data_dict = b_get_mapdict_by_integer_from_datarows(data_rows, lookup_1_field, studsubj_pk, lookup_2_field, student_pk)

        console.log( "data_dict", data_dict);

        return data_dict;
    };  // get_mapdict_by_integer_from_datarows

////////////////////
//========= get_tblName_from_selectedBtn  ======== // PR2021-07-28
    function get_tblName_from_selectedBtn() {
        const tblName = (selected_btn === "btn_published") ? "published" : "studsubj";
        return tblName;
    }
//========= get_datamap_from_tblName  ========  // PR2021-07-28
    function get_datarows_from_tblName(tblName) {
        const data_map = (tblName === "studsubj") ? studsubj_rows :
                         (tblName === "published") ? published_rows : null;
        return data_map;
    }



})  // document.addEventListener('DOMContentLoaded', function()

