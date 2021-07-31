// PR2020-09-29 added
document.addEventListener
("DOMContentLoaded", function() {
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

    let selected_btn = null;
    let setting_dict = {};
    let permit_dict = {};

    let loc = {};  // locale_dict
    let mod_dict = {};
    let mod_MSEX_dict = {};
    let mod_MEX_dict = {};

    let mod_MSSS_dict = {};
    let mod_MAG_dict = {};
    let mod_status_dict = {};
    let mod_note_dict = {};

    let examyear_map = new Map();
    let department_map = new Map();
    let level_map = new Map();
    let sector_map = new Map();
    let subject_map = new Map();
    let exam_map = new Map();
    let grade_with_exam_map = new Map();

    let filter_dict = {};

    let el_focus = null; // stores id of element that must get the focus after cloosing mod message PR2020-12-20

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    const url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    const url_settings_upload = get_attr_from_el(el_data, "data-url_settings_upload");
    const url_subject_upload = get_attr_from_el(el_data, "data-subject_upload_url");
    const url_exam_upload = get_attr_from_el(el_data, "data-exam_upload_url");
    const url_grade_upload = get_attr_from_el(el_data, "data-grade_upload_url");
    const url_grade_approve = get_attr_from_el(el_data, "data-grade_approve_url");

    const url_exam_download_exam_pdf = get_attr_from_el(el_data, "data-exam_download_exam_pdf_url");
    const url_exam_download_exam_json = get_attr_from_el(el_data, "data-exam_download_exam_json_url");

    const url_download_published = get_attr_from_el(el_data, "data-download_published_url");

    let columns_hidden = {lvl_abbrev: true};

// --- get field_settings
    const field_settings = {
        exam: { field_caption: ["", "Abbreviation", "Subject", "Leerweg", "Version", "Exam_period", "Exam_type",
                                "Blanks", "Download_PDF", "Download_JSON"],
                field_names: ["select", "subj_base_code", "subj_name", "lvl_abbrev", "version", "examperiod", "examtype",
                            "blanks", "printpdf", "printjson"],
                field_tags: ["div", "div", "div", "div", "div", "div",
                            "div", "div", "a", "a"],
                filter_tags: ["text",  "text", "text", "text", "text", "text",
                              "text", "text", "text","text"],
                field_width: ["020", "100", "240", "120", "120", "120",
                                "120", "075", "090", "090"],
                field_align: ["c",  "l", "l", "l", "l", "l",
                             "l", "c", "c", "c"]},
        grades: {  field_caption: ["", "Examnumber_twolines", "Candidate",  "Leerweg",
                        "Abbreviation", "Subject", "Exam", "Blanks"],
            field_names: ["select", "examnumber", "fullname", "lvl_abbrev",
                        "subj_code", "subj_name", "exam_name", "blanks"],
            field_tags: ["div", "div", "div", "div",
                            "div", "div", "div", "div"],
            filter_tags: ["select", "text", "text",  "text",
                        "text", "text", "text",  "text"],
            field_width:  ["020", "075", "240",  "075",
                            "075", "300", "150", "075"],
            field_align: ["c", "r", "l", "l",
                            "l", "l", "l", "c"]}
        };

    const tblHead_datatable = document.getElementById("id_tblHead_datatable");
    const tblBody_datatable = document.getElementById("id_tblBody_datatable");

// === EVENT HANDLERS ===
// === reset filter when ckicked on Escape button ===
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") { ResetFilterRows();};
        });

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
        }
        if (el_hdrbar_department){
            el_hdrbar_department.addEventListener("click", function() {
                t_MSED_Open(loc, "department", department_map, setting_dict, permit_dict, MSED_Response)}, false );
        }
        if (el_hdrbar_school){
            el_hdrbar_school.addEventListener("click",
                function() {t_MSSSS_Open(loc, "school", school_map, false, setting_dict, permit_dict, MSSSS_Response)}, false );
        }

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

// ---  SIDEBAR ------------------------------------
        const el_SBR_select_examperiod = document.getElementById("id_SBR_select_period");
        if (el_SBR_select_examperiod){
            el_SBR_select_examperiod.addEventListener("change", function() {HandleSbrPeriod(el_SBR_select_examperiod)}, false );
        }
        const el_SBR_select_examtype = document.getElementById("id_SBR_select_examtype");
        if (el_SBR_select_examtype){
            el_SBR_select_examtype.addEventListener("change", function() {HandleSbrExamtype(el_SBR_select_examtype)}, false );
        }
        const el_SBR_select_level = document.getElementById("id_SBR_select_level");
        if (el_SBR_select_level){
            el_SBR_select_level.addEventListener("change", function() {HandleSbrLevel(el_SBR_select_level)}, false );
        }

// ---  MSEX MOD SELECT EXAM ------------------------------
        const el_MSEX_tblBody_select = document.getElementById("id_MSEX_tblBody_select");
        const el_MSEX_btn_cancel = document.getElementById("id_MSEX_btn_cancel");
        const el_MSEX_btn_save = document.getElementById("id_MSEX_btn_save");
        if (el_MSEX_btn_save){
            el_MSEX_btn_save.addEventListener("click", function() {MSEX_Save()}, false )
        }
        const el_MSEX_btn_delete = document.getElementById("id_MSEX_btn_delete");
        if (el_MSEX_btn_delete){
            el_MSEX_btn_delete.addEventListener("click", function() {MSEX_Delete()}, false )
        }

// ---  MEX MOD EXAM ------------------------------
        const el_MEX_header1 = document.getElementById("id_MEX_header1");
        const el_MEX_header2 = document.getElementById("id_MEX_header2");
        const el_MEXQ_tblBody_subjects = document.getElementById("id_MEXQ_tblBody_subjects");

        const el_MEX_input_subject = document.getElementById("id_MEX_input_subject");
        if (el_MEX_input_subject){
            el_MEX_input_subject.addEventListener("keyup", function(event){
                setTimeout(function() {MEXQ_InputKeyup(el_MEX_input_subject)}, 50)});
        }

        const el_MEX_select_level = document.getElementById("id_MEXQ_select_level");
        if (el_MEX_select_level){
            el_MEX_select_level.addEventListener("change", function() {MEXQ_InputLevel(el_MEX_select_level)}, false );
        }

        const el_MEX_input_version = document.getElementById("id_MEX_input_version");
        if (el_MEX_input_version){
            el_MEX_input_version.addEventListener("change", function() {MEXQ_InputVersion(el_MEX_input_version)}, false );
        }
        const el_MEX_input_amount = document.getElementById("id_MEX_input_amount");
        if (el_MEX_input_amount){
            el_MEX_input_amount.addEventListener("keyup", function(){
                setTimeout(function() {MEXQ_InputAmount(el_MEX_input_amount)}, 50)});
        }
        const el_MEX_err_amount = document.getElementById("id_MEX_err_amount");

        const el_MEX_btn_tab_container = document.getElementById("id_MEX_btn_tab_container");
        if (el_MEX_btn_tab_container){
            const btns = el_MEX_btn_tab_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                const data_btn = get_attr_from_el(btn,"data-btn");
                btn.addEventListener("click", function() {MEX_BtnTabClicked(data_btn)}, false );
            };
        };
        const el_MEX_btn_pge_container = document.getElementById("id_MEX_btn_pge_container");
        if (el_MEX_btn_pge_container){
            const btns = el_MEX_btn_pge_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                const data_btn = get_attr_from_el(btn,"data-btn");
                const pge_index = (data_btn) ? Number(data_btn.slice(4)) : 1;
                btn.addEventListener("click", function() {MEX_BtnPageClicked(pge_index)}, false );
            };
        };

        const el_MEX_btn_save = document.getElementById("id_MEX_btn_save");
        if (el_MEX_btn_save){
            el_MEX_btn_save.addEventListener("click", function() {MEX_Save()}, false )
        }

// ---  MOD APPROVE GRADE ------------------------------------
        const el_mod_approve_grade = document.getElementById("id_mod_approve_grade");
        const el_MAG_examperiod = document.getElementById("id_MAG_examperiod");
        const el_MAG_examtype = document.getElementById("id_MAG_examtype");
        const el_MAG_level_container = document.getElementById("id_MAG_level_container");
        const el_MAG_level = document.getElementById("id_MAG_level");
        const el_MAG_class_cluster = document.getElementById("id_MAG_class_cluster");
        const el_MAG_subject = document.getElementById("id_MAG_subject");
        const el_MAG_info_container = document.getElementById("id_MAG_info_container");
        const el_MAG_loader = document.getElementById("id_MAG_loader");
        const el_MAG_msg_container = document.getElementById("id_MAG_msg_container");
        const el_MAG_btn_delete = document.getElementById("id_MAG_btn_delete");
        const el_MAG_btn_save = document.getElementById("id_MAG_btn_save");
        const el_MAG_btn_cancel = document.getElementById("id_MAG_btn_cancel");
        if (el_MAG_btn_delete){el_MAG_btn_delete.addEventListener("click", function() {MAG_Save("delete")}, false ) } // true = reset}
        if (el_MAG_btn_save){el_MAG_btn_save.addEventListener("click", function() {MAG_Save("save")}, false )}

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
        const el_modmessage_btn_cancel = document.getElementById("id_modmessage_btn_cancel");
        const el_mod_message_text = document.getElementById("id_mod_message_text");
        if(el_modmessage_btn_cancel){
            el_modmessage_btn_cancel.addEventListener("click", function() {ModMessageClose(el_modmessage_btn_cancel)}, false);
        }

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
                exam_rows: {cur_dep_only: true},
                subject_rows: {etenorm_only: true, cur_dep_only: true},
                grade_with_exam_rows: {get: true},
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
        if(!keep_loader_hidden){el_loader.classList.remove(cls_visible_hide)}

        let param = {"download": JSON.stringify (datalist_request)};
        let response = "";
        $.ajax({
            type: "POST",
            url: url_datalist_download,
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

                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict;
                    selected_btn = (setting_dict.sel_tab)
                    must_update_headerbar = true;
                };

                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    // get_permits must come before CreateSubmenu and FiLLTbl
                    b_get_permits_from_permitlist(permit_dict);
                    set_columns_hidden();
                    must_update_headerbar = true;
                }

                if(must_create_submenu){CreateSubmenu()};

                if(must_update_headerbar){
                    b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);
                    FillOptionsExamperiodExamtype();
                };

                // call b_render_awp_messages also when there are no messages, to remove existing messages
                const awp_messages = (response.awp_messages) ? response.awp_messages : {};
                b_render_awp_messages(response.awp_messages);

                if ("examyear_rows" in response) {
                    b_fill_datamap(examyear_map, response.examyear_rows)
                };
                if ("department_rows" in response) {
                    b_fill_datamap(department_map, response.department_rows)
                };
                 if ("level_rows" in response) {
                    b_fill_datamap(level_map, response.level_rows)
                    FillOptionsSelectLevelSector("level", response.level_rows)
                };

                //if ("sector_rows" in response) {
                //    b_fill_datamap(sector_map, response.sector_rows)
                //};
                if ("exam_rows" in response) {
                    b_fill_datamap(exam_map, response.exam_rows)
                };
                if ("subject_rows" in response) {
                    b_fill_datamap(subject_map, response.subject_rows)
                };
                if ("grade_with_exam_rows" in response) {
                    b_fill_datamap(grade_with_exam_map, response.grade_with_exam_rows);
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

//=========  CreateSubmenu  ===  PR2020-07-31 PR2021-01-19 PR2021-03-25 PR2021-05-25
    function CreateSubmenu() {
        //console.log("===  CreateSubmenu == ");
        //console.log("permit_dict.permit_crud", permit_dict.permit_crud);
        //console.log("permit_dict.requsr_same_school", permit_dict.requsr_same_school);

        let el_submenu = document.getElementById("id_submenu")

        if(permit_dict.permit_crud && permit_dict.requsr_role_admin){
            AddSubmenuButton(el_submenu, loc.Add_exam, function() {MEXQ_Open()});
            AddSubmenuButton(el_submenu, loc.Delete_exam, function() {ModConfirmOpen("exam", "delete")});
            AddSubmenuButton(el_submenu, loc.Publish_exam, function() {ModConfirmOpen("deleteXX")});
        }
         if(permit_dict.permit_crud && permit_dict.requsr_same_school){
            AddSubmenuButton(el_submenu, loc.Submit_exam, function() {ModConfirmOpen("deleteXX")});
        }
        //AddSubmenuButton(el_submenu, loc.Preliminary_Ex2A_form, null, "id_submenu_download_ex2a", url_grade_download_ex2a, true);  // true = download
        //if (permit.approve_grade){
        //    AddSubmenuButton(el_submenu, loc.Approve_grades, function() {MAG_Open("approve")});
        //}
        //if (permit.submit_grade){
        //    AddSubmenuButton(el_submenu, loc.Submit_Ex2A_form, function() {MAG_Open("submit")});
        //};
        el_submenu.classList.remove(cls_hide);

    };//function CreateSubmenu

//###########################################################################
// +++++++++++++++++ EVENT HANDLERS +++++++++++++++++++++++++++++++++++++++++
//=========  HandleBtnSelect  ================ PR2020-09-19  PR2020-11-14  PR2021-03-15
    function HandleBtnSelect(data_btn, skip_upload) {
        console.log( "===== HandleBtnSelect ========= ", data_btn);
        // function is called by MSSSS_Response, select_btn.click, DatalistDownload after response.setting_dict

        if(data_btn){selected_btn = data_btn;}
        if(!selected_btn){selected_btn = "btn_exams"}

// ---  highlight selected button
        //highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// --- update header text - comes after MSSSS_display_in_sbr
        UpdateHeaderLeft();

// ---  fill datatable
        FillTblRows();

    }  // HandleBtnSelect

//=========  HandleTblRowClicked  ================ PR2020-08-03 PR2021-05-22
    function HandleTblRowClicked(tr_clicked) {
        console.log("=== HandleTblRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        DeselectHighlightedRows(tr_clicked, cls_selected);
        tr_clicked.classList.add(cls_selected)

// ---  update setting_dict.sel_student_pk
        // only select employee from select table
        const row_id = tr_clicked.id
        if(row_id){
            const data_map = (!!permit_dict.requsr_role_school) ? grade_with_exam_map : exam_map;
            const map_dict = get_mapdict_from_datamap_by_id(data_map, row_id)
            setting_dict.sel_exam_pk = map_dict.id;
        }
        //console.log( "setting_dict.sel_exam_pk: ", setting_dict.sel_exam_pk);
    }  // HandleTblRowClicked

//=========  HandleSelectRowClicked  ================ PR2020-12-16
    function HandleSelectRowClicked_NIU(tr_clicked) {
        console.log("=== HandleSelectRowClicked");
        console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);
        const tblName = get_attr_from_el(tr_clicked, "data-table")
        console.log( "tblName: ", tblName);

        if (tblName === "select_student") {
             setting_dict.sel_student_pk = null;
        } else if (tblName === "select_subject") {
            setting_dict.sel_subject_pk = null;
        }

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        DeselectHighlightedRows(tr_clicked, cls_selected);
        tr_clicked.classList.add(cls_selected)

// ---  update setting_dict.sel_student_pk or setting_dict.sel_subject_pk
        // only select employee from select table
        const row_id = tr_clicked.id
        if(row_id){
            const data_map = (tblName === "select_student") ? student_map :
                              (tblName === "select_subject") ? subject_map : null;
            const map_dict = get_mapdict_from_datamap_by_id(data_map, row_id)
            if (tblName === "select_student") {
                 setting_dict.sel_student_pk = map_dict.id;
            } else if (tblName === "select_subject") {
                setting_dict.sel_subject_pk = map_dict.id;
            }
        }
        console.log( "setting_dict.sel_student_pk: ", setting_dict.sel_student_pk);
        console.log( "setting_dict.sel_subject_pk: ", setting_dict.sel_subject_pk);

        FillTblRows();
    }  // HandleSelectRowClicked_NIU

//=========  HandleSbrPeriod  ================ PR2020-12-20
    function HandleSbrPeriod(el_select) {
        console.log("=== HandleSbrPeriod");
        console.log( "el_select.value: ", el_select.value, typeof el_select.value)
        setting_dict.sel_examperiod = (Number(el_select.value)) ? Number(el_select.value) : null;

        console.log( "setting_dict.sel_examperiod: ", setting_dict.sel_examperiod, typeof setting_dict.sel_examperiod)

        console.log( "loc.options_examtype_exam: ", loc.options_examtype_exam)

// --- fill selectbox examtype with examtypes of this period PR2021-05-07
        const filter_value = setting_dict.sel_examperiod;
        const selected_value = setting_dict.sel_examtype;
        t_FillOptionsFromList(el_SBR_select_examtype, loc.options_examtype_exam, "value", "caption",
            loc.Select_examtype, loc.No_examtypes_found, selected_value, "filter", filter_value);

// ---  upload new setting
        //const upload_dict = {selected_pk: {sel_examperiod: setting_dict.sel_examperiod}};
        //UploadSettings (upload_dict, url_settings_upload);

// ---  upload new setting
        let new_setting = {page_exams: {mode: "get"},
                          selected_pk: {sel_examperiod: setting_dict.sel_examperiod}};

// also retrieve the tables that have been changed because of the change in examperiod
        const datalist_request = {setting: new_setting,
                exam_rows: {cur_dep_only: true},
                grade_with_exam_rows: {get: true},
                published_rows: {get: true}
        }

        DatalistDownload(datalist_request);

    }  // HandleSbrPeriod

//=========  HandleSbrExamtype  ================ PR2020-12-20
    function HandleSbrExamtype(el_select) {
        console.log("=== HandleSbrExamtype");
        //console.log( "el_select.value: ", el_select.value, typeof el_select.value)
        // sel_examtype = "se", "pe", "ce", "re2", "re3", "exm"
        setting_dict.sel_examtype = el_select.value;

// ---  upload new setting
        const upload_dict = {selected_pk: {sel_examtype: setting_dict.sel_examtype}};
        UploadSettings (upload_dict, url_settings_upload);

        FillTblRows();
    }  // HandleSbrExamtype

//=========  HandleSbrLevel  ================ PR2021-03-06 PR2021-05-07
    function HandleSbrLevel(el_select) {
        console.log("=== HandleSbrLevel");
        console.log( "el_select.value: ", el_select.value, typeof el_select.value)

        setting_dict.sel_lvlbase_pk = (Number(el_select.value)) ? Number(el_select.value) : null;
        setting_dict.sel_level_abbrev = (el_select.options[el_select.selectedIndex]) ? el_select.options[el_select.selectedIndex].text : null;

// ---  upload new setting
        const upload_dict = {selected_pk: {sel_lvlbase_pk: setting_dict.sel_lvlbase_pk}};
        UploadSettings (upload_dict, url_settings_upload);

        UpdateHeaderLeft();

        FillTblRows();
    }  // HandleSbrLevel

//=========  FillOptionsExamperiodExamtype  ================ PR2021-03-08
    function FillOptionsExamperiodExamtype() {
        //console.log("=== FillOptionsExamperiodExamtype");

        const sel_examperiod = setting_dict.sel_examperiod;
        const sel_examtype = setting_dict.sel_examtype;

    // check if sel_examtype is allowed in this examperiod
        if (loc.options_examtype_exam){
            let first_option = null, sel_examtype_found = false;
            for (let i = 0, dict; dict = loc.options_examtype_exam[i]; i++) {
                console.log("dict", dict);
                if(dict.filter === sel_examperiod){
                    if(!first_option) {first_option = dict.value}
                    if(dict.value === sel_examtype) {
                        sel_examtype_found = true;
            }}}
    // change selected examtype when not found in this examperiod
            if(!sel_examtype_found){
                setting_dict.sel_examtype = first_option;
    // ---  upload new setting
                const upload_dict = {selected_pk: {sel_examtype: setting_dict.sel_examtype}};
                UploadSettings (upload_dict, url_settings_upload);
            }
        }

        t_FillOptionsFromList(el_SBR_select_examperiod, loc.options_examperiod_exam, "value", "caption",
            loc.Select_examperiod + "...", loc.No_examperiods_found, sel_examperiod);
        //document.getElementById("id_hdr_textright1").innerText = setting_dict.sel_examperiod_caption
        document.getElementById("id_SBR_container_examperiod").classList.remove(cls_hide);

        const filter_value = sel_examperiod;
        t_FillOptionsFromList(el_SBR_select_examtype, loc.options_examtype_exam, "value", "caption",
            loc.Select_examtype + "...", loc.No_examtypes_found, setting_dict.sel_examtype, "filter", filter_value);
        document.getElementById("id_SBR_container_examtype").classList.remove(cls_hide);

        //document.getElementById("id_SBR_container_showall").classList.remove(cls_hide);

    }  // FillOptionsExamperiodExamtype

//=========  FillOptionsSelectLevelSector  ================ PR2021-03-06  PR2021-05-22
    function FillOptionsSelectLevelSector(tblName, rows) {
        //console.log("=== FillOptionsSelectLevelSector");
        //console.log("tblName", tblName);
        //console.log("rows", rows);

    // sector not in use
        const display_rows = []
        const has_items = (!!rows && !!rows.length);
        const has_profiel = setting_dict.sel_dep_has_profiel;
        console.log("has_items", has_items);
        console.log("has_profiel", has_profiel);
        const caption_all = "&#60" + ( (tblName === "level") ? loc.All_leerwegen : (has_profiel) ? loc.All_profielen : loc.All_sectors ) + "&#62";
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
        // hide select level when department has no levels
        if (tblName === "level"){
            //add_or_remove_class(document.getElementById("id_SBR_container_level"), cls_hide, !has_items);
            add_or_remove_class(document.getElementById("id_SBR_container_level"), cls_hide, true);
        // set label of profiel
         } else if (tblName === "sector"){
            add_or_remove_class(document.getElementById("id_SBR_container_sector"), cls_hide, false);

            document.getElementById("id_SBR_select_sector_label").innerText = ( (has_profiel) ? loc.Profiel : loc.Sector ) + ":";
        }
    }  // FillOptionsSelectLevelSector

//=========  HandleShowAll  ================ PR2020-12-17
    function HandleShowAll() {
        console.log("=== HandleShowAll");

        setting_dict.sel_lvlbase_pk = null;
        setting_dict.sel_level_abbrev = null;

        setting_dict.sel_sector_pk = null;
        setting_dict.sel_sector_abbrev = null;

        setting_dict.sel_subject_pk = null;
        setting_dict.sel_student_pk = null;

        el_SBR_select_level.value = "0";
        el_SBR_select_sector.value = "0";

// ---  upload new setting
        const selected_pk_dict = {sel_lvlbase_pk: null, sel_sector_pk: null, sel_subject_pk: null, sel_student_pk: null};
        //const page_grade_dict = {sel_btn: "grade_by_all"}
       //const upload_dict = {selected_pk: selected_pk_dict, page_grade: page_grade_dict};
        const upload_dict = {selected_pk: selected_pk_dict};
        UploadSettings (upload_dict, url_settings_upload);

        HandleBtnSelect("grade_by_all", true) // true = skip_upload
        // also calls: FillTblRows(), MSSSS_display_in_sbr(), UpdateHeader()

    }  // HandleShowAll

//========= UpdateHeaderLeft  ================== PR2021-03-14
    function UpdateHeaderLeft(){
        //console.log(" --- UpdateHeaderLeft ---" )
        //console.log("setting_dict", setting_dict)
        // sel_subject_txt gets value in MSSSS_display_in_sbr, therefore UpdateHeader comes after MSSSS_display_in_sbr
        let header_left = setting_dict.sel_examtype_caption + " " + setting_dict.sel_depbase_code;
        if (setting_dict.sel_lvlbase_pk) { header_left += " " + setting_dict.sel_level_abbrev }
        document.getElementById("id_hdr_left").innerText = header_left

        document.getElementById("id_hdr_textright1").innerText = setting_dict.sel_examperiod_caption
    }   //  UpdateHeaderLeft



//###########################################################################
// +++++++++++++++++ FILL TABLE ROWS ++++++++++++++++++++++++++++++++++++++++
//========= FillTblRows  ====================================
    function FillTblRows() {
        console.log( "===== FillTblRows  === ");

        const tblName = (!!permit_dict.requsr_role_school) ? "grades" : "exam"  // get_tblName_from_selectedBtn()
        const field_setting = field_settings[tblName];

// --- get data_map
        const data_map = (!!permit_dict.requsr_role_school) ? grade_with_exam_map : exam_map;

        console.log( "data_map", data_map);
// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

// --- create table header
        CreateTblHeader(field_setting);

// --- loop through data_map
        //console.log( "data_map", data_map);
        if(data_map){
            for (const [map_id, map_dict] of data_map.entries()) {

            // only show rows of selected student / subject
                let show_row = true;
                if (tblName === "exam"){
                    show_row = (!setting_dict.sel_lvlbase_pk || map_dict.levelbase_id === setting_dict.sel_lvlbase_pk)
                } else {
                    show_row =  (!setting_dict.sel_lvlbase_pk || map_dict.levelbase_id === setting_dict.sel_lvlbase_pk) &&
                                (!setting_dict.sel_sector_pk || map_dict.sct_id === setting_dict.sel_sector_pk) &&
                                (!setting_dict.sel_subject_pk || map_dict.subject_id === setting_dict.sel_subject_pk);
                }

                if(show_row){

          // --- insert row at row_index
                    //const schoolcode_lc_trail = ( (map_dict.sb_code) ? map_dict.sb_code.toLowerCase() : "" ) + " ".repeat(8) ;
                    //const schoolcode_sliced = schoolcode_lc_trail.slice(0, 8);
                    //const order_by = schoolcode_sliced +  ( (map_dict.username) ? map_dict.username.toLowerCase() : "");
                    const order_by = null; // TODO
                    const row_index = -1; // t_get_rowindex_by_sortby(tblBody_datatable, order_by)
                    let tblRow = CreateTblRow(tblName, field_setting, map_id, map_dict, order_by, row_index)
                };
          };
        };
    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-12-03 PR2020-12-18 PR2021-01-022
    function CreateTblHeader(field_setting) {
        //console.log("===  CreateTblHeader ===== ");

// +++  insert header and filter row ++++++++++++++++++++++++++++++++
        let tblRow_header = tblHead_datatable.insertRow (-1);
        let tblRow_filter = tblHead_datatable.insertRow (-1);
            tblRow_filter.setAttribute("data-filterrow", "1")

// - insert th's into header row
        const column_count = field_setting.field_names.length;
        for (let j = 0; j < column_count; j++) {
            const field_name = field_setting.field_names[j];

// skip columns if in columns_hidden
            if (!columns_hidden[field_name]){
                const field_caption = loc[field_setting.field_caption[j]]
                const field_tag = field_setting.field_tags[j];
                const filter_tag = field_setting.filter_tags[j];
                const class_width = "tw_" + field_setting.field_width[j] ;
                const class_align = "ta_" + field_setting.field_align[j];

    // ++++++++++ create header row +++++++++++++++
        // --- add th to tblRow_header +++
                let th_header = document.createElement("th");
        // --- add div to th, margin not working with th
                    const el_header = document.createElement("div");
                        el_header.innerText = (field_caption) ? field_caption : null;
        // --- add width, text_align, right padding in examnumber
                        el_header.classList.add(class_width, class_align);
                        if(field_name === "examnumber"){el_header.classList.add("pr-2")}
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
                    if(field_name === "examnumber"){el_filter.classList.add("pr-2")}
                th_filter.appendChild(el_filter)
                tblRow_filter.appendChild(th_filter);
            }  //  if (!columns_hidden[field_name])
        }  // for (let j = 0; j < column_count; j++)

    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09 PR2021-05-23
    function CreateTblRow(tblName, field_setting, map_id, map_dict, order_by, row_index) {
        //console.log("=========  CreateTblRow =========");
        //console.log("field_setting", field_setting);

        const field_names = field_setting.field_names;
        const field_tags = field_setting.field_tags;
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;

// --- insert tblRow into tblBody at row_index
        let tblRow = tblBody_datatable.insertRow(row_index);
        tblRow.id = map_id;

// --- add data attributes to tblRow
        const pk_int = map_dict.id
        tblRow.setAttribute("data-pk", map_dict.id);
        tblRow.setAttribute("data-table", tblName);
        tblRow.setAttribute("data-sortby", order_by);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        // happens in UpdateTblRow
        const order_by_subj = (map_dict.subj_name) ? map_dict.subj_name.toLowerCase() : null;
        tblRow.setAttribute("data-sortby", order_by_subj);

// --- add EventListener to tblRow
        tblRow.addEventListener("click", function() {HandleTblRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
        for (let j = 0; j < column_count; j++) {
            const field_name = field_names[j];

// skip columns if in columns_hidden
            if (!columns_hidden[field_name]){
                const field_tag = field_tags[j];
                const class_width = "tw_" + field_width[j];
                const class_align = "ta_" + field_align[j];

        // --- insert td element,
                let td = tblRow.insertCell(-1);

        // --- add EventListener to td
                if (["select", "status"].includes(field_name)){
                    // pass
                } else if ([ "printpdf", "printjson"].includes(field_name)){
                    // pass
                    add_hover(td);
                } else if ([ "exam_name", "printjson"].includes(field_name)){
                    td.addEventListener("click", function() {MSEX_Open(el)}, false)
                    add_hover(td);
                } else {
                    if(permit_dict.requsr_same_school){
                        td.addEventListener("click", function() {MEXA_Open(el)}, false)
                        add_hover(td);
                    } else if (permit_dict.requsr_role_admin) {
                        td.addEventListener("click", function() {MEXQ_Open(el)}, false)
                        add_hover(td);
                    }
                }
                //td.classList.add("pointer_show", "px-2");

        // --- create element with tag from field_tags
                let el = document.createElement(field_tag);

        // --- add data-field attribute
                    el.setAttribute("data-field", field_name);

    // --- add width, text_align, right padding in examnumber
                    td.classList.add(class_width, class_align);

                    el.classList.add(class_width, class_align);
                    if(field_name === "examnumber"){el.classList.add("pr-2")}

                    if (field_name === "status"){
    // --- add column with status icon
                        el.classList.add("stat_0_1")

                    } else if (field_name === "printpdf"){
                        el.innerHTML = "&#128438;";
                        // target="_blank opens file in new tab
                        el.target = "_blank";
                        el.title = "loc.Print_exam";
                        // add_hover(el);

                    } else if (field_name === "printjson"){
                        el.innerHTML = "&#8681;";
                        // target="_blank opens file in new tab
                        el.target = "_blank";
                        el.title = "loc.Download_Exform";
                        // add_hover(el);
                    }
                td.appendChild(el);

    // --- put value in field
                UpdateField(el, map_dict)
            }  // if (!columns_hidden[field_name])
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

//=========  UpdateField  ================ PR2020-12-18
    function UpdateField(el_div, map_dict) {
        //console.log("=========  UpdateField =========");
        //console.log("map_dict", map_dict);
        if(el_div){
            const field_name = get_attr_from_el(el_div, "data-field");
            const fld_value = map_dict[field_name];

            if(field_name){
                let inner_text = null, title_text = null, filter_value = null;
                if (field_name ==="select"){
                    // pass
                } else if (field_name ==="status"){
                    el_div.className = b_get_status_iconclass(map_dict.se_published_id, map_dict.se_auth1by_id, map_dict.se_auth2by_id, map_dict.se_auth3by_id);
                } else if (field_name === "examperiod"){
                    inner_text = loc.examperiod_caption[map_dict.examperiod];
                    el_div.innerText = inner_text;
                    filter_value = (inner_text) ? inner_text.toLowerCase() : null;
                } else if (field_name === "examtype"){
                    inner_text = loc.examtype_caption[map_dict.examtype];
                    el_div.innerText = inner_text;
                    filter_value = (inner_text) ? inner_text.toLowerCase() : null;
                } else if (field_name === "blanks"){
                    const blanks = (map_dict[field_name]) ? map_dict[field_name] : null;
                    const amount = (map_dict.amount) ? map_dict.amount : "-";
                    inner_text = (blanks) ? blanks + " / " + amount : "";
                    el_div.innerText = inner_text;
                    filter_value = (inner_text) ? inner_text : null;
                } else if (field_name === "printpdf"){
            // +++  create href and put it in button PR2021-05-07
                    const href_str = map_dict.id.toString()
                    let href = url_exam_download_exam_pdf.replace("-", href_str);
                    el_div.href = href;
                } else if (field_name === "printjson"){
            // +++  create href and put it in button PR2021-05-07
                    const href_str = map_dict.id.toString()
                    let href = url_exam_download_exam_json.replace("-", href_str);
                    el_div.href = href;

                } else if (field_name === "filename"){
                    const name = (map_dict.name) ? map_dict.name : null;
                    const file_path = (map_dict.filepath) ? map_dict.filepath : null;
                    if (file_path){
                        // url_download_published = "/grades/download//0/"
                        const len = url_download_published.length;
                        const href = url_download_published.slice(0, len - 2) + map_dict.id +"/"
                        //el_div.setAttribute("href", href);
                        //el_div.setAttribute("download", name);
                        el_div.title = loc.Download_Exform;
                        el_div.classList.add("btn", "btn-add")
                        add_hover(td);
                    }
                } else {
                    inner_text = map_dict[field_name];
                    el_div.innerText = inner_text;
                    filter_value = (inner_text) ? inner_text.toLowerCase() : null;
                }

// ---  add attribute filter_value
                add_or_remove_attr (el_div, "data-filter", !!filter_value, filter_value);
            };
        }
    };  // UpdateField

//========= set_columns_hidden  ====== PR2021-05-07
    function set_columns_hidden() {
        //console.log( "===== set_columns_hidden  === ");
        //console.log("setting_dict.sel_dep_level_req", setting_dict.sel_dep_level_req);
        columns_hidden.lvl_abbrev = (!setting_dict.sel_dep_level_req);
    }  // set_columns_hidden

//###########################################################################
// +++++++++++++++++ UPLOAD CHANGES +++++++++++++++++++++++++++++++++++++++++

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

                    if ("updated_exam_rows" in response) {
                        // TODO remove or rename
                        const el_MSTUD_loader = document.getElementById("id_MSTUD_loader");
                        if(el_MSTUD_loader){ el_MSTUD_loader.classList.add(cls_visible_hide)};
                        RefreshDataMap("exam", response.updated_exam_rows, exam_map);
                    };

                    if ("updated_grade_rows" in response) {
                        RefreshDataMap("grades", response.updated_grade_rows, grade_with_exam_map);
                    }

                    if ("err_html" in response) {
                        b_show_mod_message(response.err_html)
                    }
                    if ("msg_dict" in response && !isEmpty(response.msg_dict)) {
                        //if (mod_dict.mode && ["submit_test", "approve"].indexOf(mod_dict.mode) > -1){
                            MAG_UpdateFromResponse (response.msg_dict);
                        //}
                    }
                    if ("updated_published_rows" in response) {
                        RefreshDataMap("published", response.updated_published_rows, published_map);
                    }

                },  // success: function (response) {
                error: function (xhr, msg) {
                    // ---  hide loader
                    el_loader.classList.add(cls_visible_hide)
                    console.log(msg + '\n' + xhr.responseText);
                }  // error: function (xhr, msg) {
            });  // $.ajax({
        }  //  if(!!row_upload)
    };  // UploadChanges

//========= UploadToggle  ============= PR2020-07-31  PR2021-01-14
    function UploadToggle(el_input) {
        console.log( " ==== UploadToggle ====");
         // only called by field 'se_status', 'pe_status', 'ce_status'
        // mode = 'approve_submit' or ''approve_reset'
        mod_dict = {};
        const tblRow = get_tablerow_selected(el_input);
        if(tblRow){
            // b_get_statusindex_of_requsr returns index of auth user, returns 0 when user has none or multiple auth usergroups
            // gives err messages when multiple found.
            const status_index = b_get_statusindex_of_requsr(loc, permit_dict);

            // if(status_index){
            if(true){
                const map_id = tblRow.id
                const map_dict = get_mapdict_from_datamap_by_id(grade_map, map_id);
                console.log( "map_dict", map_dict);
                if(!isEmpty(map_dict)){
                    const fldName = get_attr_from_el(el_input, "data-field");
                    if(fldName in map_dict ){
                        const examtype = fldName.substring(0,2);
                        const published_field = examtype + "_published"
                        let published_pk = (map_dict[published_field]) ? map_dict[published_field] : null;
            // give message when grade is published
                        if (published_pk){
                            const msg_html = loc.approve_err_list.This_grade_is_submitted + "<br>" + loc.approve_err_list.You_cannot_remove_approval;
                            b_show_mod_message(msg_html);
                        } else {

            // give message when grade /score  has no value
                            const no_grade_value = (!map_dict[examtype + "grade"]);
                            const no_score_value = (['pe', 'ce'].includes(examtype) && !map_dict[examtype + "score"]);

                            if (no_grade_value || no_score_value){
                                const msg_html = loc.approve_err_list.This_grade_has_no_value + "<br>" + loc.approve_err_list.You_cannot_approve;
                                b_show_mod_message(msg_html);
                            } else {
                                const status_sum = (map_dict[fldName]) ? map_dict[fldName] : 0;
                                const status_bool_at_index = b_get_status_bool_at_index(status_sum, status_index)

                        // ---  toggle value of status_bool_at_index
                                const new_status_bool_at_index = !status_bool_at_index;

            // give message when status_bool = true and grade already approved bu this user in different function
                                let double_approved = false
                                if(new_status_bool_at_index){
                                    if (status_index === 1){
                                        double_approved = (map_dict.se_auth2by_id === setting_dict.requsr_pk || map_dict.se_auth3by_id === setting_dict.requsr_pk);
                                    } else if (status_index === 2){
                                        double_approved = (map_dict.se_auth1by_id === setting_dict.requsr_pk || map_dict.se_auth3by_id === setting_dict.requsr_pk);
                                    } else if (status_index === 3){
                                        double_approved = (map_dict.se_auth1by_id === setting_dict.requsr_pk || map_dict.se_auth2by_id === setting_dict.requsr_pk);
                                    }
                                }
                                if (double_approved) {
                                    const msg_html = loc.approve_err_list.Approved_different_function + "<br>" + loc.approve_err_list.You_cannot_approve_again;
                                    b_show_mod_message(msg_html);
                                } else {

                // ---  change icon, before uploading
                                    const new_status_sum = b_set_status_bool_at_index(status_sum, status_index, new_status_bool_at_index);
                                    el_input.className = get_status_class(new_status_sum)

                // ---  upload changes
                                    // value of 'mode' setermines if status is set to 'approved' or 'not
                                    // instead of using value of new_status_bool_at_index,
                                    const mode = (new_status_bool_at_index) ? "approve_submit" : "approve_reset"
                                    const upload_dict = { table: map_dict.table,
                                                           mode: mode,
                                                           mapid: map_id,
                                                           field: fldName,
                                                           status_index: status_index,
                                                           status_bool_at_index: new_status_bool_at_index,
                                                           //examperiod: map_dict.examperiod,
                                                           examtype: examtype,

                                                           grade_pk: map_dict.id};
                                    UploadChanges(upload_dict, url_grade_approve);
                                } //  if (double_approved))
                            }  // if (!grade_value)
                        }  // if (published_pk)
                    }  //   if(fldName in map_dict ){
                }  //  if(!isEmpty(map_dict))
            }  //if(perm_auth1 || perm_auth1)
        }  //   if(!!tblRow)
    }  // UploadToggle

//========= DownloadPublished  ============= PR2020-07-31  PR2021-01-14
    function DownloadPublished(el_input) {
        console.log( " ==== DownloadPublished ====");
        const tblRow = get_tablerow_selected(el_input);
        const pk_int = get_attr_from_el_int(tblRow, "data-pk");

        const map_dict = get_mapdict_from_datamap_by_id(published_map, tblRow.id);
        const filepath = map_dict.filepath
        const filename = map_dict.filename
        console.log( "filepath", filepath);
        console.log( "filename", filename);

       // window.open = '/ticket?orderId=' + pk_int;

        // UploadChanges(upload_dict, url_download_published);
        const upload_dict = { published_pk: pk_int};
        if(!isEmpty(upload_dict)) {
            const parameters = {"upload": JSON.stringify (upload_dict)}
            let response = "";
            $.ajax({
                type: "POST",
                url: url_download_published,
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
        //    url: url_download_published,
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

     } // DownloadPublished

//###########################################################################
// +++++++++++++++++ REFRESH DATA MAP +++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataMap  ================ PR2020-08-16 PR2020-09-30 PR2021-05-11
    function RefreshDataMap(tblName, data_rows, data_map) {
        console.log(" --- RefreshDataMap  ---");
        console.log("tblName", tblName);
        console.log("data_rows", data_rows);
        console.log("data_map", data_map);

        if (data_rows) {
            const field_setting = field_settings[tblName];
            const field_names = (field_setting) ? field_setting.field_names : null;
            for (let i = 0, update_dict; update_dict = data_rows[i]; i++) {
                RefreshDatamapItem(tblName, field_setting, field_names, update_dict, data_map);
            }
        }
    }  //  RefreshDataMap

//=========  RefreshDatamapItem  ================ PR2020-08-16 PR2020-09-30
    function RefreshDatamapItem(tblName, field_setting, field_names, update_dict, data_map) {
        console.log(" --- RefreshDatamapItem  ---");
        console.log("update_dict", update_dict);
        console.log("field_setting", field_setting);
        console.log("update_dict", update_dict);

        if(!isEmpty(update_dict)){

// ---  update or add update_dict in subject_map
            let updated_columns = [];
    // get existing map_item
            const map_id = update_dict.mapid;
            let tblRow = document.getElementById(map_id);

            const is_deleted = get_dict_value(update_dict, ["deleted"], false);
            const is_created = get_dict_value(update_dict, ["created"], false);

            const err_dict = get_dict_value(update_dict, ["error"], {});
            console.log("err_dict", err_dict);
            console.log("is_created", is_created);

// ++++ created ++++
            if(is_created){
    // ---  insert new item
                data_map.set(map_id, update_dict);
                updated_columns.push("created")
    // ---  create row in table., insert in alphabetical order
                //let order_by = (update_dict.fullname) ? update_dict.fullname.toLowerCase() : ""
                const order_by = null; // TODO
                const row_index = t_get_rowindex_by_sortby(tblBody_datatable, order_by);
                tblRow = CreateTblRow(tblName, field_setting, map_id, update_dict, order_by, row_index);
    // ---  scrollIntoView,
                if(tblRow){
                    tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' })
    // ---  make new row green for 2 seconds,
                    ShowOkElement(tblRow);
                }

// ++++ deleted ++++
            } else if(is_deleted){
                data_map.delete(map_id);
    //--- delete tblRow
                if (tblRow){tblRow.parentNode.removeChild(tblRow)};
            } else {
                const old_map_dict = (map_id) ? data_map.get(map_id) : null;
    // ---  check which fields are updated, add to list 'updated_columns'
                if(!isEmpty(old_map_dict) && field_names){
                    // skip first column (is margin)
                    for (let i = 1, col_field, old_value, new_value; col_field = field_names[i]; i++) {
                        if (col_field in old_map_dict && col_field in update_dict){
                            if (old_map_dict[col_field] !== update_dict[col_field] ) {
                                updated_columns.push(col_field)
                            }
                        }
                    }}
    // ---  update item
                data_map.set(map_id, update_dict)
            }

            console.log("updated_columns", updated_columns);
    // ---  make update
            // note: when updated_columns is empty, then updated_columns is still true.
            // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
            if(tblRow && (updated_columns.length || err_dict)){
    // ---  make entire row green when row is created
                if(updated_columns.includes("created")){
                    ShowOkElement(tblRow);
                } else {
    // loop through cells of row
                    for (let i = 1, td, el, el_fldName; td = tblRow.cells[i]; i++) {
                        if (td){
                            el = td.children[0];
                            if(el){
                                el_fldName = get_attr_from_el(el, "data-field")

                                if(err_dict && el_fldName in err_dict){

                            // ---  show modal
                                    // TODO header, set focus after closing messagebox
                                    // el_mod_message_header.innerText = loc.Enter_grade;
                                    const msg_err = err_dict[el_fldName]
                                    el_mod_message_text.innerText = msg_err;
                                    $("#id_mod_message").modal({backdrop: false});
                                    set_focus_on_el_with_timeout(el_modmessage_btn_cancel, 150 )
                                    el.value = null;

        // update field and make field green when field name is in updated_columns
                                } else if(updated_columns.includes(el_fldName)){
                                    UpdateField(el, update_dict);
                                    ShowOkElement(el);
                                }
                            }
                        }
             }}}
            console.log("updated_columns", updated_columns);
        }
    }  // RefreshDatamapItem

//=========  fill_data_list  ================ PR2020-10-07
// TODO deprecate
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


//###########################################################################
// +++++++++++++++++ FILTER TABLE ROWS ++++++++++++++++++++++++++++++++++++++

//========= HandleFilterKeyup  ================= PR2021-05-12
    function HandleFilterKeyup(el, event) {
        //console.log( "===== HandleFilterKeyup  ========= ");
        // skip filter if filter value has not changed, update variable filter_text
        const col_index = get_attr_from_el(el, "data-colindex")
        //console.log( "col_index", col_index, "event.key", event.key);
        const skip_filter = t_SetExtendedFilterDict(el, col_index, filter_dict, event.key);
        //console.log( "filter_dict", filter_dict);

        if (!skip_filter) {
            Filter_TableRows(tblBody_datatable);
        }
    }; // function HandleFilterKeyup

//========= HandleFilterToggle  =============== PR2020-07-21 PR2020-09-14 PR2021-03-23

    function HandleFilterToggle(el_input) {
        //console.log( "===== HandleFilterToggle  ========= ");

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

    };  // HandleFilterToggle

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

        for (let i = 0, tblRow, show_row; tblRow = tblBody_datatable.rows[i]; i++) {
            tblRow = tblBody_datatable.rows[i]
            show_row = t_ShowTableRowExtended(filter_dict, tblRow);
            add_or_remove_class(tblRow, cls_hide, !show_row)
        }
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
    function ResetFilterRows() {  // PR2019-10-26 PR2020-06-20
       //console.log( "===== ResetFilterRows  ========= ");

        selected_subject_pk = null;

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
// +++++++++ MOD EXAM  ++++++++++++++++ PR2021-05-22
    function MSEX_Open(el_input){
        console.log(" ===  MSEX_Open  =====") ;
        console.log( "el_input", el_input);
        mod_MSEX_dict = {exam_pk: null}
        if(permit_dict.permit_crud){
            const tblRow = get_tablerow_selected(el_input)
            const tblName = get_attr_from_el(tblRow, "data-table")
            const map_id = tblRow.id
            const grade_dict = get_mapdict_from_datamap_by_id(grade_with_exam_map, map_id);
            if(!isEmpty(grade_dict)){
                mod_MSEX_dict.exam_pk = grade_dict.exam_id;
                mod_MSEX_dict.mapid = grade_dict.mapid;
                mod_MSEX_dict.grade_pk = grade_dict.id;
                mod_MSEX_dict.student_pk = grade_dict.student_id;
                mod_MSEX_dict.studsubj_pk = grade_dict.studsubj_id;
                mod_MSEX_dict.subj_pk = grade_dict.subj_id;
                mod_MSEX_dict.student_levelbase_pk = grade_dict.levelbase_id;
            }
// ---  fill select table
            const row_count = MSEX_FillSelectTable(tblName)
            // hide remove button when grade has no exam
            add_or_remove_class(el_MSEX_btn_delete, cls_hide, !mod_MSEX_dict.exam_id)
            add_or_remove_class(el_MSEX_btn_save, cls_hide, !row_count)
            el_MSEX_btn_cancel.innerText = (row_count) ? loc.Cancel : loc.Close;
            MSEX_validate_and_disable();
// ---  show modal
            $("#id_mod_select_exam").modal({backdrop: true});
        }
    }  // MSEX_Open

//=========  MSEX_Save  ================ PR2021-05-22
    function MSEX_Save(){
        console.log(" ===  MSEX_Save  =====") ;

        console.log( "mod_MSEX_dict: ", mod_MSEX_dict);

        if(permit_dict.permit_crud){
            const upload_dict = {
                table: 'grade',
                mode: "update",
                return_grades_with_exam: true,
                examyear_pk: setting_dict.sel_examyear_pk,
                depbase_pk: setting_dict.sel_depbase_pk,
                examperiod: setting_dict.sel_examperiod,

                examtype: mod_MSEX_dict.examtype,
                exam_pk: mod_MSEX_dict.exam_pk,
                student_pk: mod_MSEX_dict.student_pk,
                levelbase_pk: mod_MSEX_dict.student_levelbase_pk,
                studsubj_pk: mod_MSEX_dict.studsubj_pk,
                grade_pk: mod_MSEX_dict.grade_pk,
            }
            const map_dict = get_mapdict_from_datamap_by_id(exam_map, mod_MEX_dict.map_id);

            UploadChanges(upload_dict, url_grade_upload);


        }  // if(permit_dict.permit_crud){
        $("#id_mod_select_exam").modal("hide");
    }  // MSEX_Save

//=========  MSEX_FillSelectTable  ================ PR2020-08-21
    function MSEX_FillSelectTable(tblName) {
        console.log( "===== MSEX_FillSelectTable ========= ");
        //console.log( "tblName: ", tblName);

        const tblBody_select = el_MSEX_tblBody_select;
        tblBody_select.innerText = null;

        let row_count = 0, add_to_list = false;
// ---  loop through exam_map
        for (const [map_id, exam_dict] of exam_map.entries()) {
            console.log( "exam_dict: ", exam_dict);
        // add only when eam has same subject as grade, and also the same depbase and levelbase_id
            let show_row = false;
            if (mod_MSEX_dict.subj_pk === exam_dict.subject_id){
                if(mod_MSEX_dict.student_levelbase_pk){
                    show_row = (mod_MSEX_dict.student_levelbase_pk === exam_dict.levelbase_id);
                } else {
                    show_row = true;
                }
            }
            if (show_row){
                row_count += 1;
                MSEX_FillSelectRow(exam_dict, tblBody_select, tblName, -1);
            }
        }

        if(!row_count){
            let tblRow = tblBody_select.insertRow(-1);
            let td = tblRow.insertCell(-1);
            td.innerText = loc.No_exam_for_this_subject;

        } else if(row_count === 1){
            let tblRow = tblBody_select.rows[0]
            if(tblRow) {
// ---  make first row selected
                //tblRow.classList.add(cls_selected)

                MSEX_SelectItem(tblRow);
            }
        }
        return row_count
    }  // MSEX_FillSelectTable

//=========  MSEX_FillSelectRow  ================ PR2020-10-27
    function MSEX_FillSelectRow(exam_dict, tblBody_select, tblName, row_index) {
        console.log( "===== MSEX_FillSelectRow ========= ");
        console.log("tblName: ", tblName);
        console.log( "exam_dict: ", exam_dict);

//--- loop through data_map
        const exam_pk_int = exam_dict.id;
        const code_value = (exam_dict.exam_name) ? exam_dict.exam_name : "---"
        const is_selected_pk = (mod_MSEX_dict.exam_pk != null && exam_pk_int === mod_MSEX_dict.exam_pk)
// ---  insert tblRow  //index -1 results in that the new row will be inserted at the last position.
        let tblRow = tblBody_select.insertRow(row_index);
        tblRow.setAttribute("data-pk", exam_pk_int);
// ---  add EventListener to tblRow
        tblRow.addEventListener("click", function() {MSEX_SelectItem(tblRow)}, false )
// ---  add hover to tblRow
        add_hover(tblRow);
// ---  highlight clicked row
        if (is_selected_pk){ tblRow.classList.add(cls_selected)}
// ---  add first td to tblRow.
        let td = tblRow.insertCell(-1);
// --- add a element to td., necessary to get same structure as item_table, used for filtering
        let el_div = document.createElement("div");
            el_div.innerText = code_value;
            el_div.classList.add("tw_360", "px-4", "pointer_show" )
        td.appendChild(el_div);

    }  // MSEX_FillSelectRow

//=========  MSEX_SelectItem  ================ PR2021-04-05
    function MSEX_SelectItem(tblRow) {
        console.log( "===== MSEX_SelectItem ========= ");
        console.log( "tblRow", tblRow);
// ---  deselect all highlighted rows
        DeselectHighlightedRows(tblRow, cls_selected)
// ---  highlight clicked row
        tblRow.classList.add(cls_selected)
// ---  get pk code and value from tblRow in mod_MSEX_dict
        mod_MSEX_dict.exam_pk = get_attr_from_el_int(tblRow, "data-pk")
        console.log( "mod_MSEX_dict", mod_MSEX_dict);
        MSEX_validate_and_disable();
    }  // MSEX_SelectItem

//=========  MSEX_Save  ================ PR2021-05-22
    function MSEX_validate_and_disable(){
        el_MSEX_btn_save.disabled = !mod_MSEX_dict.exam_pk;
    }

///////////////////////////////////////
// +++++++++ MOD EXAM QUESTIONS ++++++++++++++++ PR2021-04-05 PR2021-05-22
    function MEXQ_Open(el_input){
        console.log(" ===  MEXQ_Open  =====") ;
        const is_admin_mode = (permit_dict.requsr_role_admin && permit_dict.permit_crud);
        const is_same_school_mode = (permit_dict.requsr_same_school && permit_dict.permit_crud);

        mod_MEX_dict = {};
        if(is_admin_mode){
            // el_input is undefined when called by submenu btn 'Add new'
            const is_addnew = (!el_input);
            const tblName = "exam" // (permit_dict.)
            mod_MEX_dict = {
                sel_tab: "tab_start",
                pge_index: 1,
                examyear_pk: setting_dict.sel_examyear_pk,
                depbase_pk: setting_dict.sel_depbase_pk,
                examperiod: setting_dict.sel_examperiod,
                examtype: setting_dict.sel_examtype,
                version: null,
                amount : 0,
                maxscore: 0,
                assignment: {},
                keys: {},
                answers: {},
                is_admin_mode: is_admin_mode,
                is_same_school_mode: is_same_school_mode,
                is_keys_mode: false
            }

            if(is_addnew){
                mod_MEX_dict.is_addnew = true;
                mod_MEX_dict.levelbase_pk = (setting_dict.sel_lvlbase_pk) ? setting_dict.sel_lvlbase_pk : null;
            } else {
                const tblRow = get_tablerow_selected(el_input);
                const map_id = (tblRow) ? tblRow.id : null;
                const exam_dict = get_mapdict_from_datamap_by_id(exam_map, map_id);

                MEX_get_assignment(exam_dict);

            }
    // ---  hide select subject when existing exam
            const el_MEXQ_subjects_container = document.getElementById("id_MEXQ_subjects_container")
            add_or_remove_class(el_MEXQ_subjects_container, cls_hide, !is_addnew);

    // ---  set input subject readonly when existing exam, change label
            document.getElementById("id_MEX_input_subject_label").innerText = (is_addnew) ? loc.Select_subject : loc.Subject;
            add_or_remove_attr (el_MEX_input_subject, "readonly", !is_addnew, true);
            el_MEX_input_subject.value = (mod_MEX_dict.subject_name) ? mod_MEX_dict.subject_name : null;;

    // ---  set el_MEX_input_version
            el_MEX_input_version.value = (mod_MEX_dict.version) ? mod_MEX_dict.version : null;

    // ---  set el_MEX_input_amount
            el_MEX_input_amount.value = (mod_MEX_dict.amount) ? mod_MEX_dict.amount : null;

    // ---  set header text
            let header1_text = loc.Exam, header2_text = null;

            if (loc.examtype_caption && mod_MEX_dict.examtype){
                header1_text = loc.examtype_caption[mod_MEX_dict.examtype]
            }

            const depbase_code = (setting_dict.sel_depbase_code) ? setting_dict.sel_depbase_code : "---";
            header1_text += " " + depbase_code;

            const examperiod_caption = (loc.examperiod_caption && mod_MEX_dict.examperiod) ? loc.examperiod_caption[mod_MEX_dict.examperiod] : "---"
            header1_text += " " + examperiod_caption;

            if(is_addnew) {
                header2_text = loc.Add_exam;
            } else {
                header2_text = loc.Exam + " " + mod_MEX_dict.subject_name;
                if(mod_MEX_dict.lvl_abbrev) { header2_text += " - " + mod_MEX_dict.lvl_abbrev; }
                if(mod_MEX_dict.version) { header2_text += " - " + mod_MEX_dict.version; }
            }

            el_MEX_header1.innerText = header1_text
            el_MEX_header2.innerText = header2_text

    // --- fill select table
            MEXQ_Fill_SelectTableSubjects()
            MEXQ_FillSelectTableLevel()

    // ---  set focus to input element
            const el_focus = (is_addnew) ? el_MEX_input_subject : el_MEX_input_amount;
            set_focus_on_el_with_timeout(el_focus, 50);

            add_or_remove_class(el_MEX_err_amount, "text-danger", false, "text-muted" )
            el_MEX_err_amount.innerHTML = loc.err_list.amount_mustbe_between;

    // ---  set buttons
            add_or_remove_class(el_MEX_btn_tab_container, cls_hide, is_same_school_mode);
            MEX_BtnTabClicked(mod_MEX_dict.sel_tab);
            MEX_SetPages();
            //el_MEX_btn_keys.classList.remove("tsa_btn_selected");

    // ---  disable save button when not all required fields have value
            MEXQ_validate_and_disable();

    // ---  show modal
            $("#id_mod_exam_questions").modal({backdrop: true});
        }  //  if(is_admin_mode)
    };  // MEXQ_Open

//========= MEX_get_assignment  ============= PR2021-05-23
    function MEX_get_assignment(exam_dict, grade_dict) {
        //console.log("MEX_get_assignment");

        if(exam_dict) {
            mod_MEX_dict.exam_map_id = exam_dict.mapid;
            mod_MEX_dict.exam_pk = exam_dict.id;
            mod_MEX_dict.subject_pk = (exam_dict.subject_id) ? exam_dict.subject_id : null;
            mod_MEX_dict.subject_code = (exam_dict.subj_base_code) ? exam_dict.subj_base_code : null;
            mod_MEX_dict.subject_name = (exam_dict.subj_name) ? exam_dict.subj_name : null;
            mod_MEX_dict.version = (exam_dict.version) ? exam_dict.version : null;
            mod_MEX_dict.amount = (exam_dict.amount) ? exam_dict.amount : 0;

            mod_MEX_dict.department_pk = exam_dict.department_id;

            mod_MEX_dict.levelbase_pk = exam_dict.levelbase_id;
            mod_MEX_dict.lvl_abbrev = exam_dict.lvl_abbrev;

            if(exam_dict.assignment){
                // fortmat of assignment: 1:2;D;1 | 2:3;C;1 "  question_number: max_score; max_char;m in_score
                // fortmat of keys: 1:ba | 2:cd  question_number:keys
                const arr = exam_dict.assignment.split("|");
       //console.log( "arr", arr);
                // arr: ["1:2;D;1", "2:3;C;1"]
                for (let i = 0, q, q_arr; q = arr[i]; i++) {
                    // q_arr = ["1", "2;D;1"]
                    q_arr = q.split(":");
                    const question_number = q_arr[0];
                    const question_values = q_arr[1];
                    const values_arr = question_values.split(";");
       //console.log( "values_arr", values_arr);
                    // values_arr = ["D", "3", "ba", "1"]
                    if (values_arr && values_arr.length){
                        mod_MEX_dict.assignment[question_number] = {
                            max_score: (values_arr[0]) ? values_arr[0] : "",
                            max_char: (values_arr[1]) ? values_arr[1] : "",
                            min_score: (values_arr[2]) ? values_arr[2] : ""
                        }
                    }
       //console.log( "mod_MEX_dict.assignment[question_number]", mod_MEX_dict.assignment[question_number]);
                }
            }

            if(permit_dict.requsr_role_admin && exam_dict.keys){
                // fortmat of keys: "1:ba | 2:cd"  question_number: keys
                const arr = exam_dict.keys.split("|");
                // arr: ["1:ba", "2:cd"]
                for (let i = 0, q, q_arr; q = arr[i]; i++) {
                    q_arr = q.split(":");
                    // q_arr = ["1", "ba"]
                    const question_number = q_arr[0];
                    const question_keys = (q_arr[1]) ? q_arr[1] : "";
                    mod_MEX_dict.keys[question_number] = question_keys;
                    // don't use value, because it needs reference in inputkeyup, not value
                    mod_MEX_dict.keys[question_number] = {keys: question_keys}
                }
            }

            if(permit_dict.requsr_same_school && grade_dict && grade_dict.answers){
                // fortmat of keys: "1:3 | 2:c"  question_number: answer
                const arr = grade_dict.answers.split("|");
                // arr: ["1:3", "2:c"]
                for (let i = 0, q, q_arr; q = arr[i]; i++) {
                    q_arr = q.split(":");
                    // q_arr = ["1", "3"]
                    const question_number = q_arr[0];
                    const question_answer = (q_arr[1]) ? q_arr[1] : "";
                    // don't use value, because it needs reference in inputkeyup, not value
                    mod_MEX_dict.answers[question_number] = {answer: question_answer};
                }

            }
       }
       //console.log( "mod_MEX_dict.assignment", mod_MEX_dict.assignment);
       //console.log( "mod_MEX_dict.keys", mod_MEX_dict.keys);
       //console.log( "mod_MEX_dict.answers", mod_MEX_dict.answers);
    }  // MEX_get_assignment

//========= MEX_Save  ============= PR2021-05-24
    function MEX_Save() {
        if(mod_MEX_dict.is_same_school_mode){
            MEXA_Save();
        } else if (mod_MEX_dict.is_admin_mode){
            MEXQ_Save();
        }
    }  // MEX_Save

//========= MEXQ_Save  ============= PR2021-04-05
    function MEXQ_Save() {
        console.log("===== MEXQ_Save ===== ");
        console.log( "mod_MEX_dict: ", mod_MEX_dict);

        if(permit_dict.permit_crud){
            const upload_dict = {
                table: 'exam',
                mode: ((mod_MEX_dict.is_addnew) ? "create" : "update"),
                examyear_pk: mod_MEX_dict.examyear_pk,
                depbase_pk: mod_MEX_dict.depbase_pk,
                levelbase_pk: mod_MEX_dict.levelbase_pk,
                examperiod: mod_MEX_dict.examperiod,

                examtype: mod_MEX_dict.examtype,
                exam_pk: mod_MEX_dict.exam_pk,
                subject_pk: mod_MEX_dict.subject_pk,
                subject_code: mod_MEX_dict.subject_code
            }
            if (mod_MEX_dict.is_addnew) {
                upload_dict.mode = "create";
                if(el_MEX_input_version.value){
                    upload_dict.version = el_MEX_input_version.value;
                };
                if(mod_MEX_dict.amount){
                    upload_dict.amount = mod_MEX_dict.amount;
                };
            } else {
               const map_dict = get_mapdict_from_datamap_by_id(exam_map, mod_MEX_dict.map_id);
               if (el_MEX_input_version.value !== map_dict.version){
                    upload_dict.version = el_MEX_input_version.value;
               }
               if (mod_MEX_dict.amount !== map_dict.amount){
                    upload_dict.amount = mod_MEX_dict.amount;
               }
            }
            if(mod_MEX_dict.amount){
                // mod_MEX_dict assignment: {1: {max_char: "D", max_score: 3, min_score: 1, keys: "ba"], 2: ...}"
                // upload assignment: 1:D;3;ba;1 | 2:C;3;cd;1 "
                // 0: max character when multiple choice or @ for open question
                // 1: max score
                // 2: keys (answers)
                // 3: min score

                let assignments_str = "", non_blanks = 0;
                if (mod_MEX_dict.assignment && !isEmpty(mod_MEX_dict.assignment)){
                    for (let i = 1, dict; i <= mod_MEX_dict.amount; i++) {
                        if(i in mod_MEX_dict.assignment){
                            const value_dict = mod_MEX_dict.assignment[i];
                            if(!isEmpty(value_dict)){
                                const max_char = get_dict_value(value_dict, ["max_char"], "")
                                const max_score = get_dict_value(value_dict, ["max_score"], "")
                                const min_score = get_dict_value(value_dict, ["min_score"], "")
                                assignments_str += "|" + i + ":" + max_score + ";" + max_char + ";" + min_score;
                                non_blanks += 1;
                            }
                }}};
                if(assignments_str) { assignments_str = assignments_str.slice(1)};
                upload_dict.assignment = (assignments_str) ? assignments_str : null;
                upload_dict.blanks =  mod_MEX_dict.amount - non_blanks;

                let keys_str = "";
                if (mod_MEX_dict.keys && !isEmpty(mod_MEX_dict.keys)){
                    for (let i = 1, dict; i <= mod_MEX_dict.amount; i++) {
                        if(i in mod_MEX_dict.keys){
                            const value_dict = mod_MEX_dict.keys[i];
                            if(!isEmpty(value_dict)){
                                const keys = get_dict_value(value_dict, ["keys"], "")
                                keys_str += "|" + i + ":" + keys;
                            }
                }}};
                if(keys_str) {keys_str = keys_str.slice(1)};
                upload_dict.keys = (keys_str) ? keys_str : null;
            }
            UploadChanges(upload_dict, url_exam_upload);
        };  // if(has_permit_edit

// ---  hide modal
        $("#id_mod_exam_questions").modal("hide");
    }  // MEXQ_Save

//========= MEXA_Save  ============= PR2021-05-24
    function MEXA_Save() {
        console.log("===== MEXA_Save ===== ");
        console.log( "mod_MEX_dict: ", mod_MEX_dict);

        if(permit_dict.permit_crud){
            const upload_dict = {
                table: 'grade',
                mode: "update",
                return_grades_with_exam: true,
                examyear_pk: mod_MEX_dict.examyear_pk,
                depbase_pk: mod_MEX_dict.depbase_pk,
                //levelbase_pk: mod_MEX_dict.levelbase_pk,
                examperiod: mod_MEX_dict.examperiod,

                //examtype: mod_MEX_dict.examtype,
                //exam_pk: mod_MEX_dict.exam_pk,
                grade_pk: mod_MEX_dict.grade_pk,
                student_pk: mod_MEX_dict.student_pk,
                //subject_pk: mod_MEX_dict.subject_pk,
                //subject_code: mod_MEX_dict.subject_code
            }

            const map_dict = get_mapdict_from_datamap_by_id(grade_with_exam_map, mod_MEX_dict.grade_map_id);


        console.log( "mod_MEX_dict.answers: ", mod_MEX_dict.answers);
            let answers_str = "", non_blanks = 0;
            if (mod_MEX_dict.answers && !isEmpty(mod_MEX_dict.answers)){
                for (let i = 1, dict; i <= mod_MEX_dict.amount; i++) {
                    if(i in mod_MEX_dict.answers){
                        const value_dict = mod_MEX_dict.answers[i];
                        const value = get_dict_value(value_dict, ["answer"], "")
                        answers_str += "|" + i + ":" + value;
                        if(value) { non_blanks += 1};
            }}};
            if(answers_str) {answers_str = answers_str.slice(1)};
            upload_dict.answers = (answers_str) ? answers_str : null;
            upload_dict.blanks =  mod_MEX_dict.amount - non_blanks;

        console.log( "upload_dict: ", upload_dict);

            UploadChanges(upload_dict, url_grade_upload);
        };  // if(has_permit_edit

// ---  hide modal
        $("#id_mod_exam_questions").modal("hide");
    }  // MEXA_Save

//========= MEXQ_Fill_SelectTableSubjects  ============= PR2021-04-04
    function MEXQ_Fill_SelectTableSubjects() {
        console.log("===== MEXQ_Fill_SelectTableSubjects ===== ");

        const sel_subject_pk = (setting_dict.sel_subject_pk) ? setting_dict.sel_subject_pk : null;

        const tblBody_select = el_MEXQ_tblBody_subjects;
        tblBody_select.innerText = null;

// ---  loop through dictlist
        const tblName = "subject"
        const data_map = subject_map;
        console.log("data_map", data_map);
        for (const [map_id, map_dict] of data_map.entries()) {
            MEXQ_Create_SelectRow(tblName, tblBody_select, map_dict, sel_subject_pk);
        }
    } // MEXQ_Fill_SelectTableSubjects

//========= MEXQ_Create_SelectRow  ============= PR2020-12-18
    function MEXQ_Create_SelectRow(tblName, tblBody_select, dict, sel_subject_pk) {
        //console.log("===== MEXQ_Create_SelectRow ===== ", tblName);
        //console.log("map_dict", dict);
//--- get info from dict
        //[ {pk: 2608, code: "Colpa de, William"} ]
        const pk_int = dict.id;
        const code = dict.code
        const name = dict.name
        const is_selected_row = (pk_int === sel_subject_pk);

//--------- insert tblBody_select row at end
        const map_id = "sel_" + tblName + "_" + pk_int
        const tblRow = tblBody_select.insertRow(-1);

        tblRow.id = map_id;
        tblRow.setAttribute("data-pk", pk_int);
        tblRow.setAttribute("data-code", code);
        tblRow.setAttribute("data-name", name);
        const class_selected = (is_selected_row) ? cls_selected: cls_bc_transparent;
        tblRow.classList.add(class_selected);

//- add hover to select row
        add_hover(tblRow)

// --- add td to tblRow.
        let td = tblRow.insertCell(-1);
        let el_div = document.createElement("div");
            el_div.classList.add("pointer_show")
            el_div.innerText = code;
            el_div.classList.add("tw_075", "px-1")
            td.appendChild(el_div);

        td.classList.add("tsa_bc_transparent")

// --- add td to tblRow.
        td = tblRow.insertCell(-1);
        el_div = document.createElement("div");
            el_div.classList.add("pointer_show")
            el_div.innerText = name;
            el_div.classList.add("tw_240", "px-1")
            td.appendChild(el_div);
        td.classList.add("tsa_bc_transparent")

//--------- add addEventListener
        tblRow.addEventListener("click", function() {MEXQ_SelectItem(tblRow)}, false);
    } // MEXQ_Create_SelectRow

//========= MEXQ_FillSelectTableLevel  ============= PR2021-05-07
    function MEXQ_FillSelectTableLevel() {
        console.log("===== MEXQ_FillSelectTableLevel ===== ");
        //console.log("level_map", level_map);

        const level_container = document.getElementById("id_MEXQ_level_container");
        add_or_remove_class(level_container, cls_hide, columns_hidden.lvl_abbrev)

        if (!columns_hidden.lvl_abbrev){
            el_MEX_select_level.innerText = null;
            el_MEX_select_level.value = null;
            const select_text = loc.Select_leerweg
            const select_text_none = loc.No_leerwegen_found;
            const id_field = "base_id", display_field = "abbrev";
            const selected_pk = mod_MEX_dict.levelbase_pk;
        console.log( "mod_MEX_dict.levelbase_pk", mod_MEX_dict.levelbase_pk);
            t_FillSelectOptions(el_MEX_select_level, level_map, id_field, display_field, false,
                selected_pk, null, select_text_none, select_text)

        }
    } // MEXQ_FillSelectTableLevel

//=========  MEX_SetPages  ================ PR2021-04-04 PR2021-05-23
    function MEX_SetPages() {
        console.log( "===== MEX_SetPages ========= ");

        mod_MEX_dict.total_rows = Math.ceil((mod_MEX_dict.amount) / 5);
        mod_MEX_dict.pages_visible = Math.ceil((mod_MEX_dict.amount) / 50);
        mod_MEX_dict.max_rows_per_page = (mod_MEX_dict.amount > 200) ? 10 :
                            (mod_MEX_dict.amount > 160) ? 10 :
                            (mod_MEX_dict.amount > 150) ? 8 :
                            (mod_MEX_dict.amount > 120) ? 10 :
                            (mod_MEX_dict.amount > 100) ? 8 :
                            (mod_MEX_dict.amount > 80) ? 10 :
                            (mod_MEX_dict.amount > 60) ? 8 :
                            (mod_MEX_dict.amount > 50) ? 6 : 10;
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
                if (max_value > mod_MEX_dict.amount) {max_value = mod_MEX_dict.amount}
                const min_value = ((pge_index - 1) * mod_MEX_dict.max_rows_per_page * 5) + 1;
                btn.innerText  = min_value + "-" + max_value;
                // check for blank values
                for (let q = min_value, btn; q <= max_value; q++) {
                    if (!blank_questions_found && mod_MEX_dict.assignment && !mod_MEX_dict.assignment[q]) {
                        blank_questions_found = true;
                    }
                    if (!blank_answers_found && mod_MEX_dict.answers && !mod_MEX_dict.answers[q]) {
                        blank_answers_found = true;
                    }
                }
                const class_warning = (permit_dict.requsr_same_school) ? blank_answers_found :
                                      (permit_dict.requsr_role_admin) ? blank_questions_found : false;
                add_or_remove_class(btn, "color_orange", class_warning );
                if(pge_index <= mod_MEX_dict.pages_visible) {
                    mod_MEX_dict.page_min_max[pge_index] = {min: min_value, max: max_value}
                };
            }
        };

        MEX_BtnPageClicked();

        add_or_remove_class(el_MEX_btn_pge_container, cls_hide, mod_MEX_dict.pge_index <= 1)

        console.log( "mod_MEX_dict", mod_MEX_dict);
    }  // MEX_SetPages

//=========  MEXQ_SelectItem  ================ PR2021-04-05
    function MEXQ_SelectItem(tblRow) {
        //console.log( "===== MEXQ_SelectItem ========= ");
// ---  deselect all highlighted rows
        DeselectHighlightedRows(tblRow, cls_selected)
// ---  highlight clicked row
        tblRow.classList.add(cls_selected)
// ---  get pk code and value from tblRow in mod_MEX_dict
        mod_MEX_dict.subject_pk = tblRow.dataset.pk
        mod_MEX_dict.subject_code = tblRow.dataset.code
        mod_MEX_dict.subject_name = tblRow.dataset.name
// ---  put name in input box
        el_MEX_input_subject.value = mod_MEX_dict.subject_name
// ---  put name in header2
        el_MEX_header2.innerText = mod_MEX_dict.subject_code + " - " + mod_MEX_dict.subject_name;
// ---  Set focus to el_MEX_select_level isf exists , to el_MEX_input_amount otherwise
        const el_focus = (el_MEX_select_level) ? el_MEX_select_level : el_MEX_input_amount;
        set_focus_on_el_with_timeout(el_focus, 50);
// ---  disable save button when not all required fields have value
        MEXQ_validate_and_disable();

    }  // MEXQ_SelectItem

//=========  MEXQ_InputKeyup  ================ PR2021-04-04
    function MEXQ_InputKeyup(el_input) {
        console.log( "===== MEXQ_InputKeyup  ========= ");

// ---  get value of new_filter
        let new_filter = el_input.value

        let tblBody = el_MEXQ_tblBody_subjects;
        const len = tblBody.rows.length;
        if (len){ //  if (new_filter && len){
// ---  filter rows in table select_employee
            const filter_dict = t_Filter_SelectRows(tblBody, new_filter);
            mod_MEX_dict.subject_pk = (filter_dict.selected_pk) ? filter_dict.selected_pk : null;
            mod_MEX_dict.subject_code = (filter_dict.selected_code) ? filter_dict.selected_code : null;
            mod_MEX_dict.subject_name = (filter_dict.selected_name) ? filter_dict.selected_name : null;
// ---  if filter results have only one item: put selected item in el_input
            if (mod_MEX_dict.subject_pk) {
// ---  put pk code and value  in mod_MEX_dict
// ---  put name in el_input
                el_input.value = (mod_MEX_dict.subject_name) ? mod_MEX_dict.subject_name : null;;
// ---  Set focus to el_MEX_select_level isf exists , to el_MEX_input_amount otherwise
                const el_focus = (el_MEX_select_level) ? el_MEX_select_level : el_MEX_input_amount;
                set_focus_on_el_with_timeout(el_focus, 50);
            }  //  if (!!selected_pk) {
// ---  put name in header2
            el_MEX_header2.innerText = (mod_MEX_dict.subject_pk) ? mod_MEX_dict.subject_code + " - " + mod_MEX_dict.subject_name : loc.Add_exam;
        }

        console.log( "mod_MEX_dict.subject_pk", mod_MEX_dict.subject_pk, typeof mod_MEX_dict.subject_pk);
// ---  disable save button when not all required fields have value
        MEXQ_validate_and_disable();
    }; // MEXQ_InputKeyup

//========= MEX_InputKeyDown  ================== PR2021-04-07
    function MEX_InputKeyDown(el_input, event){
        console.log(" --- MEX_InputKeyDown ---")
        //console.log("event.key", event.key, "event.shiftKey", event.shiftKey)
        // This is not necessary: (event.key === "Tab" && event.shiftKey === true)
        // Tab and shift-tab move cursor already to next / prev element
        if (["Enter", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].indexOf(event.key) > -1) {
// --- get move_vertical based on event.key and event.shiftKey
            let move_vertical = (["Enter", "Tab", "ArrowDown"].includes(event.key) ) ? 1 :
                                    (event.key === "ArrowUp") ? -1 : 0
        // el_input.id = 'id_MEX_q_24'
            const q_number_str = (el_input.id) ? el_input.id.slice(9) : null;
            const q_number = (Number(q_number_str)) ? Number(q_number_str) : null;
            //console.log("q_number", q_number)
            let pge_index = mod_MEX_dict.pge_index;
            const q_min = mod_MEX_dict.page_min_max[pge_index].min;
            const q_max = mod_MEX_dict.page_min_max[pge_index].max;
            //console.log("q_min", q_min)
            //console.log("q_max", q_max)

// --- set move up / down 1 row when min / max index is reached
            let new_q_number = q_number + move_vertical;
            if(new_q_number > q_max) {
                pge_index += 1;
                MEX_BtnPageClicked(pge_index);

                new_q_number = q_min
            } else if(new_q_number < q_min) {
                pge_index -= 1;
                MEX_BtnPageClicked(pge_index);
            }
// --- set focus to next / previous cell

            const next_id = "id_MEX_q_" + new_q_number;
        console.log("next_id", next_id);
            set_focus_on_el_with_timeout(document.getElementById(next_id), 50);
        }
    }  // MEX_InputKeyDown

//=========  MEXQ_InputLevel  ================ PR2021-05-21
    function MEXQ_InputLevel(el_input) {
        //console.log( "===== MEXQ_InputLevel  ========= ");
        mod_MEX_dict.levelbase_pk = (Number(el_input.value)) ? Number(el_input.value) : null;
// ---  disable save button when not all required fields have value
        MEXQ_validate_and_disable();
// ---  Set focus to el_MEX_input_version
        set_focus_on_el_with_timeout(el_MEX_input_version, 50);
    }; // MEXQ_InputLevel

//=========  MEXQ_InputVersion  ================ PR2021-05-21
    function MEXQ_InputVersion(el_input) {
       //console.log( "===== MEXQ_InputVersion  ========= ");
        mod_MEX_dict.version = el_input.value;
        //console.log( "mod_MEX_dict.version", mod_MEX_dict.version);
// ---  disable save button when not all required fields have value
        MEXQ_validate_and_disable();
// ---  Set focus to el_MEX_input_amount
        set_focus_on_el_with_timeout(el_MEX_input_amount, 50);
    }; // MEXQ_InputVersion

//=========  MEXQ_InputAmount  ================ PR2021-04-04
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
        if (has_error) { msg_err += loc.err_list.amount_mustbe_between};
        el_MEX_err_amount.innerHTML = msg_err;

        if (has_error) {
            el_input.value = (mod_MEX_dict.amount) ? mod_MEX_dict.amount : null;
            set_focus_on_el_with_timeout(el_input, 50)
        }
        if (new_number) {
            mod_MEX_dict.amount = new_number;
            MEX_SetPages();
        }

// ---  disable save button when not all required fields have value
        MEXQ_validate_and_disable();

    }; // MEXQ_InputAmount


//=========  MEX_BtnTabClicked  ================ PR2021-05-25
    function MEX_BtnTabClicked(data_btn) {
        //console.log( "===== MEX_BtnTabClicked ========= ", data_btn);

        mod_MEX_dict.sel_tab = (data_btn) ? data_btn : "tab_start";

// ---  highlight selected button
        if(el_MEX_btn_tab_container){
            highlight_BtnSelect(el_MEX_btn_tab_container, mod_MEX_dict.sel_tab)
        }
// ---  show only the elements that are used in this option
        let tab_show = "";
        if (mod_MEX_dict.is_same_school_mode) {
            tab_show = "tab_answers";
        } else if (mod_MEX_dict.sel_tab === "tab_start" ){
            tab_show = "tab_start";
        } else if (mod_MEX_dict.sel_tab === "tab_assign" ){
            tab_show = "tab_assign";
        } else if (mod_MEX_dict.sel_tab === "tab_keys" ){
            tab_show = "tab_keys";
            mod_MEX_dict.is_keys_mode = true;
        } else if (mod_MEX_dict.sel_tab === "tab_minscore" ){
            tab_show = "tab_minscore";
        }
        mod_MEX_dict.is_keys_mode = (mod_MEX_dict.sel_tab === "tab_keys");

        b_show_hide_selected_elements_byClass("tab_show", tab_show);

        if (["tab_assign", "tab_keys", "tab_minscore", "tab_answers"].includes(tab_show)) {
           MEX_BtnPageClicked()
        };

    }  // MEX_BtnTabClicked

//=========  MEX_BtnPageClicked  ================ PR2021-04-04 PR2021-05-25
    function MEX_BtnPageClicked(pge_index) {
        console.log( "===== MEX_BtnPageClicked ========= ", pge_index);
        mod_MEX_dict.pge_index = (pge_index) ? pge_index : 1;

// ---  highlight selected button
        highlight_BtnSelect(el_MEX_btn_pge_container, "pge_" + mod_MEX_dict.pge_index)

        if (mod_MEX_dict.pge_index) {
            MEX_FillPage()
        };

    }  // MEX_BtnPageClicked

//=========  MEX_FillPage  ================ PR2021-04-04
    function MEX_FillPage() {
        console.log( "===== MEX_FillPage ========= ");
/*
        console.log( ".........total_rows", mod_MEX_dict.total_rows);
        console.log( ".........pages_visible", mod_MEX_dict.pages_visible);
        console.log( ".........max_rows_per_page", mod_MEX_dict.max_rows_per_page);
        console.log( ".........amount", mod_MEX_dict.amount);
        console.log( ".........mod_MEX_dict.amount", mod_MEX_dict.amount);
        console.log( ".........assignment", mod_MEX_dict.assignment);
        console.log( ".........keys", mod_MEX_dict.keys);
        console.log( ".........is_admin_mode", mod_MEX_dict.is_admin_mode);
        console.log( ".........is_keys_mode", mod_MEX_dict.is_keys_mode);
        console.log( ".........is_same_school_mode", mod_MEX_dict.is_same_school_mode);

*/

        //const len = mod_MEX_dict.max_rows_per_page
        let question_number = (mod_MEX_dict.pge_index - 1) * mod_MEX_dict.max_rows_per_page * 5;

        let first_q_number_of_page = 0;
        for (let col_index = 0; col_index < 5; col_index++) {
            const el_col_container = document.getElementById("id_MEX_col_" + col_index)
        //console.log( ".........el_col_container", el_col_container);
        //console.log( ".........col_index", col_index);
            el_col_container.innerHTML = null;
            if (question_number < mod_MEX_dict.amount){
                for (let row_index = 0; row_index < mod_MEX_dict.max_rows_per_page; row_index++) {
                    question_number += 1;
                    if (question_number <= mod_MEX_dict.amount){
                        if(!first_q_number_of_page) {first_q_number_of_page = question_number}

                        const assignment_dict = (mod_MEX_dict.assignment[question_number]) ? mod_MEX_dict.assignment[question_number] : null;

                // mod_MEX_dict assignment: {1: {max_char: "D", max_score: 3, min_score: 1, keys: "ba"], 2: ...}"
                        const max_char = get_dict_value(mod_MEX_dict.assignment, [question_number, "max_char"], '')
                        const max_score = get_dict_value(mod_MEX_dict.assignment, [question_number, "max_score"], '')
                        //const min_score = get_dict_value(mod_MEX_dict.assignment, [question_number, "min_score"], '')
        //console.log( ".........question_number", question_number);

                        let display_value = null, is_read_only = false, is_invalid = false, footnote_multiple_choice = "";
                        if(mod_MEX_dict.is_admin_mode){
                            if(mod_MEX_dict.is_keys_mode){
                                display_value = get_dict_value(mod_MEX_dict.keys, [question_number, "keys"], '')

                                is_read_only = (!max_char);
                                is_invalid = (!display_value && !is_read_only);
                            } else {
                                display_value = max_char + max_score;
                                is_invalid = (!display_value)
                            }
                        } else if(mod_MEX_dict.is_same_school_mode){
                            is_read_only = (!max_char && !max_score);
                            if(max_char){footnote_multiple_choice = "*"};
                            display_value = get_dict_value(mod_MEX_dict.answers, [question_number, "answer"], '')
                        }

                        const el_flex_container = document.createElement("div");
                        el_flex_container.classList.add("flex_container", "flex_1");
                            const el_flex_0 = document.createElement("div");
                            el_flex_0.className = "flex_1";
                                const el_label = document.createElement("label");
                                el_label.className = "mex_label";
                                el_label.innerText = question_number + footnote_multiple_choice + ":";
                            el_flex_0.appendChild(el_label);
                        el_flex_container.appendChild(el_flex_0);

                        const el_flex_1 = document.createElement("div");
                            el_flex_1.classList.add("flex_1", "mx-1");
                                const el_input = document.createElement("input");
                                el_input.id = "id_MEX_q_" + question_number;
                                el_input.value = display_value;
        //console.log( ".=========..display_value", display_value);
                                el_input.className = "form-control";
                                if(is_invalid) { el_input.classList.add("border_invalid")}
                                el_input.setAttribute("type", "text")
                                el_input.setAttribute("autocomplete", "off");
                                el_input.setAttribute("ondragstart", "return false;");
                                el_input.setAttribute("ondrop", "return false;");
        // --- add EventListener
                                if (mod_MEX_dict.is_same_school_mode){
                                    el_input.addEventListener("keyup", function(event){MEX_InputAnswer(el_input, event)});
                                } else {
                                    el_input.addEventListener("change", function(){MEX_InputChange(el_input)});
                                    el_input.addEventListener("keydown", function(event){MEX_InputKeyDown(el_input, event)});
                                }
                                // set readonly=true when mode = 'keys' and quesrion is not multiple choice
                                if (is_read_only) {el_input.readOnly = true}
                            el_flex_1.appendChild(el_input);
                        el_flex_container.appendChild(el_flex_1);
                        el_col_container.appendChild(el_flex_container);
                    }  // if (question_number <= mod_MEX_dict.amount){
                }  //  for (let row_index = 0;
            }  // if (question_number < mod_MEX_dict.amount){
        }  // for (let col_index = 0; col_index < 5; col_index++) {

        if(first_q_number_of_page){
            const el_focus = document.getElementById("id_MEX_q_" + first_q_number_of_page);
            if (el_focus) { set_focus_on_el_with_timeout(el_focus, 50)}
        }
    }  // MEX_FillPage


//========= MEX_InputChange  ===============PR2020-08-16 PR2021-03-25
    function MEX_InputChange(el_input){
        console.log(" --- MEX_InputChange ---")
        console.log("el_input.id: ", el_input.id)
        // el_input.id = 'id_MEX_q_24'
        //const q_number_str = (el_input.id) ? el_input.id[10] : null;
        const q_number_str = (el_input.id) ? el_input.id.slice(9) : null;
        const q_number = (Number(q_number_str)) ? Number(q_number_str) : null;
        console.log("q_number", q_number)

        if (q_number){
    // add key = q_number with empty values when not exists
            const answers_dict = mod_MEX_dict.answers;
            // open question input has a number (8)
            // multiple choice question has one letter, may be followed by a number as score (D3)
            let max_char = "", max_score_str = "", max_score = "", msg_err = "";
            const input_value = el_input.value;

// +++++ when input is question:
            if (mod_MEX_dict.is_admin_mode ){
                if (!mod_MEX_dict.is_keys_mode){

    // - add assignment_dict[q_number] if it does not yet exist
                    if (!(q_number in mod_MEX_dict.assignment)){
                        mod_MEX_dict.assignment[q_number] = {max_score: "", max_char: "", min_score: ""};
                    };
                    const assignment_dict = mod_MEX_dict.assignment[q_number];

                    if (input_value){
    // - split input_value in first charactes and the rest
                        const first_char = input_value.charAt(0);
                        const remainder = input_value.slice(1);

    // check if first character is a letter or a number => is multiple choice when a letter
                        // !!Number(0) = false, therefore "0" must be filtered out with Number(first_char) !== 0
                        const is_multiple_choice = (!Number(first_char) && Number(first_char) !== 0 )
                        if(is_multiple_choice){
                            max_char = first_char.toUpperCase();
                            max_score_str = remainder;
                        } else {
                            max_score_str = input_value;
                        }
                        if (max_char){
                            // Letter 'A' not allowed, only 1 choice doesn't make sense
                            if(!"BCDEFGHIJKLMNOPQRSTUVWXYZ".includes(max_char)){
                                msg_err = loc.err_list.Character + " '" + first_char  + "'" + loc.err_list.not_allowed +
                                    "<br>" + loc.err_list.character_mustbe_between;
                            }
                        }
    // - validate max_score
                        if (max_score_str){
                            max_score = Number(max_score_str);
                            // the remainder / modulus operator (%) returns the remainder after (integer) division.
                            if (!max_score || max_score % 1 !== 0 || max_score < 1 || max_score > 99) {
                                if (msg_err) {msg_err += "<br><br>"}
                                msg_err += loc.Maximum_score + " '" + max_score_str  + "'" + loc.err_list.not_allowed +
                                                    "<br>" + loc.err_list.maxscore_mustbe_between;
                            }
                        }
    // - show message when error, delete input in element and in mod_MEX_dict.assignment
                        if (msg_err) {
                            el_input.value = null;
                             if (q_number in mod_MEX_dict.assignment){
                                delete mod_MEX_dict.assignment[q_number];
                            }
                            // also delete keys
                             if (q_number in mod_MEX_dict.keys){
                                delete mod_MEX_dict.keys[q_number];
                            }
                            el_mod_message_text.innerHTML = msg_err;
                            $("#id_mod_message").modal({backdrop: false});
                            set_focus_on_el_with_timeout(el_modmessage_btn_cancel, 150 )
                        } else {
    // - put new value in element and in mod_MEX_dict.assignment
                            const new_value = max_char + ( (max_score) ? max_score : "" );
                            if (new_value !== el_input.value){
                                el_input.value = new_value
                            }
                            // mod_MEX_dict assignment: {1: {max_char: "D", max_score: 3, min_score: 1], 2: ...}"
                            assignment_dict.max_char = (max_char) ? max_char : "";
                            assignment_dict.max_score = (max_score) ? max_score : "";
                        }
    // - delete if input_value is empty
                    } else {
                        if (q_number in mod_MEX_dict.assignment){
                            delete mod_MEX_dict.assignment[q_number];
                        }
                        // also delete keys
                        if (q_number in mod_MEX_dict.keys){
                             delete mod_MEX_dict.keys[q_number];
                        }
                    }  // if (input_value)

// +++++ when input is keys:
// admin mode - keys - possible answers entered by requsr_role_admin
                } else {
                    const assignment_dict = mod_MEX_dict.assignment[q_number];
                    if (assignment_dict){
                        const max_char = (assignment_dict.max_char) ? assignment_dict.max_char : "";
                        const is_multiple_choice = (!!max_char);
        console.log("max_char", max_char)
        console.log("is_multiple_choice", is_multiple_choice)
    // answer only has value when multiple choice question. one or more letters, may be followed by a number as minimum score (ca3)
                        if (!is_multiple_choice){
                            el_mod_message_text.innerHTML = loc.err_list.This_isnota_multiplechoice_question;
                            $("#id_mod_message").modal({backdrop: false});
                            set_focus_on_el_with_timeout(el_modmessage_btn_cancel, 150 )
                        } else {
    // - add mod_MEX_dict.keys[q_number] if it does not yet exist
                            if (!(q_number in mod_MEX_dict.keys)){
                                mod_MEX_dict.keys[q_number] =  {keys: ""};
                            };
                            let keys_dict = mod_MEX_dict.keys[q_number];
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
                                        const max_char_lc = max_char.toLowerCase();
                                        if(!"abcdefghijklmnopqrstuvwxyz".includes(char_lc)){
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
        // - show message when error, delete input in element and in mod_MEX_dict.keys
                                if (msg_err){
                                    msg_err += loc.err_list.key_mustbe_between_and_ + max_char.toLowerCase() + "'.";
                                    el_input.value = null;
                                     if (q_number in mod_MEX_dict.keys){
                                        delete mod_MEX_dict.keys[q_number];
                                    }

                                    el_mod_message_text.innerHTML = msg_err;
                                    $("#id_mod_message").modal({backdrop: false});
                                    set_focus_on_el_with_timeout(el_modmessage_btn_cancel, 150 )

                                } else {
        // - put new new_keys in element and in mod_MEX_dict.keys
                                    if (new_keys !== el_input.value){
                                        el_input.value = new_keys
                                    }
                                    // mod_MEX_dict keys: {1: {keys: "ba"}, 2: ...}"
                                    keys_dict.keys = (new_keys) ? new_keys : "";
                                }
        // - delete if input_value is empty
                            } else {
                                if (q_number in mod_MEX_dict.keys){
                                     delete mod_MEX_dict.keys[q_number];
                                }
                            }
                        }  // if (!is_multiple_choice)
                    }  //   if (assignment_dict)
                }
            }
        }  //  if (q_number){
    };  // MEX_InputChange

//========= MEX_InputAnswer  =============== PR2021-05-25
    function MEX_InputAnswer(el_input, event){
        console.log(" --- MEX_InputAnswer ---")
        console.log("el_input.id: ", el_input.id)
        console.log("event.key", event.key, "event.shiftKey", event.shiftKey)
        // el_input.id = 'id_MEX_q_24'
        //const q_number_str = (el_input.id) ? el_input.id[10] : null;
        const q_number_str = (el_input.id) ? el_input.id.slice(9) : null;
        const q_number = (Number(q_number_str)) ? Number(q_number_str) : null;
        console.log("q_number", q_number)

        if (q_number){
            MEX_goto_next(q_number, event)

    // add key = q_number with empty values when not exists
            const answers_dict = mod_MEX_dict.answers;
            // open question input has a number (8)
            // multiple choice question has one letter, may be followed by a number as score (D3)
            let max_char = "", max_score_str = "", max_score = "", msg_err = "";
            const input_value = el_input.value;
            if (mod_MEX_dict.is_same_school_mode){
//================================================================
// when input is answer, entered by requsr_same_school
                const assignment_dict = mod_MEX_dict.assignment[q_number];
     //console.log("assignment_dict", assignment_dict)
                if (isEmpty(assignment_dict)){
                    msg_err = loc.err_list.Exam_assignment_does_notexist + "<br>" + loc.err_list.Contact_divison_of_exams
                    console.log("msg_err", msg_err)
                } else {
                    const max_score = (assignment_dict.max_score) ? assignment_dict.max_score : "";
                    const max_char = (assignment_dict.max_char) ? assignment_dict.max_char : "";
                    const is_multiple_choice = (!!max_char);
     // console.log("is_multiple_choice", is_multiple_choice)

    // - add mod_MEX_dict.answers[q_number] if it does not yet exist
                    if (!(q_number in mod_MEX_dict.answers)){
                        mod_MEX_dict.answers[q_number] =  {answer: ""};
                    };
                    const answers_dict = mod_MEX_dict.answers[q_number];
    //console.log("answers_dict", answers_dict)
                    let char_lc = null;
                    if (input_value){
                        const input_number = Number(input_value);
    //console.log("input_value", input_value, typeof input_value)
    //console.log("input_number", input_number, typeof input_number)
                        if (input_number || input_number === 0){
                            // check if is integer
                            char_lc = input_number.toString();
    //console.log("is integer char_lc", char_lc)
                            if (is_multiple_choice){
                                msg_err =  loc.err_list.This_isa_multiplechoice_question  +
                                "<br>" + loc.err_list.must_enter_letter_between_a_and_ + max_char.toLowerCase() + "'," +
                                "<br>" + loc.err_list.or_an_x_if_blank;
                            } else if (input_number < 0 || input_number > max_score){
                                msg_err += " '" + input_value  + "'" + loc.err_list.not_allowed +
                                "<br>" + loc.err_list.must_enter_whole_number_between_0_and_ + max_score + "," +
                                "<br>" + loc.err_list.or_an_x_if_blank;
                            }
                        } else {
                            char_lc = input_value.toLowerCase();
    //console.log("char_lc", char_lc)
                            if (char_lc === "x"){
                                // pass, enter x for blank answer, also when not multiple choice
                            } else if (!is_multiple_choice){
                                msg_err =  loc.err_list.This_isnota_multiplechoice_question  +
                                "<br>" + loc.err_list.must_enter_whole_number_between_0_and_ + max_score + "," +
                                "<br>" + loc.err_list.or_an_x_if_blank;
                            } else if (input_value.length > 1){
                                msg_err += " '" + max_score_str  + "'" + loc.err_list.not_allowed +
                                "<br>" + loc.err_list.must_enter_letter_between_a_and_ + max_char.toLowerCase() + "'," +
                                "<br>" + loc.err_list.or_an_x_if_blank;
                            } else {
                                if(!"abcdefghijklmnopqrstuvwxyz".includes(char_lc)){
                                    msg_err += " '" + input_value  + "'" + loc.err_list.not_allowed +
                                    "<br>" + loc.err_list.must_enter_letter_between_a_and_ + max_char.toLowerCase() + "'," +
                                    "<br>" + loc.err_list.or_an_x_if_blank;
                                } else {
                                    const max_char_lc = max_char.toLowerCase();
    //console.log("max_char_lc", max_char_lc)
                                    if (char_lc > max_char_lc ) {
    //console.log("char_lc > max_char_lc", max_char_lc)
                                        msg_err += "'" + input_value  + "'" + loc.err_list.not_allowed +
                                        "<br>" + loc.err_list.must_enter_letter_between_a_and_ + max_char.toLowerCase() + "'," +
                                        "<br>" + loc.err_list.or_an_x_if_blank;
                            }}}
                        }
                    }
                    if (!msg_err) {
                        if(char_lc){
                            answers_dict.answer = char_lc;
                        } else {
                            if (q_number in mod_MEX_dict.answers){
                                delete mod_MEX_dict.answers[q_number];
                            }
                        }
                        el_input.value = char_lc;
                        if(char_lc){
                        // set focus to net input element, got btn save after last question
                            const next_question = q_number + 1;
                            const next_id = (next_question > mod_MEX_dict.amount) ? "id_MEX_btn_save" :"id_MEX_q_" + (q_number + 1).toString();
                            const el_focus = document.getElementById(next_id)
                            if(el_focus) {set_focus_on_el_with_timeout(el_focus, 50)}
                        }

                    } else {
                //  on error: set input_value null and delete answer from mod_MEX_dict.answers
                        if (q_number in mod_MEX_dict.answers){
                            delete mod_MEX_dict.answers[q_number];
                        }
                        el_input.value = null;
                        el_mod_message_text.innerHTML = msg_err;
                        $("#id_mod_message").modal({backdrop: false});
                        // set focus to current input element
                        el_modmessage_btn_cancel.setAttribute("data-nextid", "id_MEX_q_" + q_number)
                        set_focus_on_el_with_timeout(el_modmessage_btn_cancel, 150 )

                    }  //  if (!msg_err)
                }  //  if (isEmpty(assignment_dict))
            }  // if (mod_MEX_dict.is_same_school_mode)
        }  //  if (q_number){
    }  // MEX_InputAnswer


//========= MEX_goto_next  ================== PR2021-04-07
    function MEX_goto_next(q_number, event){
        console.log(" --- MEX_goto_next ---")
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
            console.log("q_number", q_number)
            console.log("pge_index", pge_index)
            console.log("q_min", q_min)
            console.log("q_max", q_max)

// --- set move up / down 1 row when min / max index is reached
            let new_q_number = q_number + move_vertical;
            if(new_q_number > q_max) {
                pge_index += 1;
                MEX_BtnPageClicked(pge_index);

                new_q_number = q_min
            } else if(new_q_number < q_min) {
                pge_index -= 1;
                MEX_BtnPageClicked(pge_index);
            }
// --- set focus to next / previous cell

            const next_id = "id_MEX_q_" + new_q_number;
        console.log("next_id", next_id);
            set_focus_on_el_with_timeout(document.getElementById(next_id), 50);
        }
    }  // MEX_goto_next






//=========  MEXQ_validate_and_disable  ================  PR2021-05-21
    function MEXQ_validate_and_disable() {
        console.log(" -----  MEXQ_validate_and_disable   ----")
        let disable_save_btn = false;

// ---  disable save_btn when no subject
        if (!mod_MEX_dict.subject_pk) {
            disable_save_btn = true;
// ---  disable save_btn when amount has no value
        } else if (!mod_MEX_dict.amount) {
            disable_save_btn = true;
// ---  disable save_btn whenlevel has no value - only when level required
        } else if(!columns_hidden.lvl_abbrev && !mod_MEX_dict.levelbase_pk){
            disable_save_btn = true;
        } else {
// ---  check if there are multiple exams of this subject and this level
            let multiple_exams_found = false;
        // skip when there a no other exams yet
            if(exam_map.size){
        // loop through exams
                for (const [map_id, map_dict] of exam_map.entries()) {
        // skip the current exam
                    if(map_dict.map_id !== mod_MEX_dict.map_id){
        // skip other levels - only when level required
                        if(!!columns_hidden.lvl_abbrev || map_dict.levelbase_pk !== mod_MEX_dict.levelbase_pk){
                            multiple_exams_found = true;
            }}}};
            if (multiple_exams_found){
// ---  disable save_btn when multiple exams are found and varesion has no value
                disable_save_btn = !el_MEX_input_version.value;
            }
        }

// ---  disable save button on error
        el_MEX_btn_save.disabled = disable_save_btn;
    }  // MEXQ_validate_and_disable

///////////////////////////////////////
// +++++++++ MOD EXAM ANSWERS ++++++++++++++++ PR2021-05-23
    function MEXA_Open(el_input){
        //if(permit.crud){
        console.log(" ===  MEXA_Open  =====") ;
        const is_same_school_mode = (permit_dict.requsr_same_school && permit_dict.permit_crud);

        mod_MEX_dict = {};

        // el_input must always have value
        if(el_input && is_same_school_mode){
            // el_input is undefined when called by submenu btn 'Add new'
            const tblName = "grade" // (permit_dict.)
            const tblRow = get_tablerow_selected(el_input);
            const map_id = (tblRow) ? tblRow.id : null;
            const grade_dict = get_mapdict_from_datamap_by_id(grade_with_exam_map, map_id);

            console.log( "grade_dict", grade_dict );

            if(grade_dict) {
            // get exam questions
                if(grade_dict.exam_id){
                    const exam_dict = get_mapdict_from_datamap_by_id(exam_map, "exam_" + grade_dict.exam_id);
                    if(exam_dict){
            console.log( "exam_dict", exam_dict );
                        const fullname = (grade_dict.fullname) ? grade_dict.fullname : "---";
                        const exam_name = (exam_dict.exam_name) ? exam_dict.exam_name : "---";
                        const amount = (exam_dict.amount) ? exam_dict.amount : "---";
                        const version = (exam_dict.version) ? exam_dict.version : null;

                        mod_MEX_dict = {
                            sel_tab: "tab_answers",
                            examyear_pk: setting_dict.sel_examyear_pk,
                            depbase_pk: setting_dict.sel_depbase_pk,
                            examperiod: setting_dict.sel_examperiod,
                            examtype: setting_dict.sel_examtype,
                            version: version,
                            amount : amount,

                            grade_map_id: grade_dict.mapid,
                            grade_pk: grade_dict.id,
                            student_pk: grade_dict.student_id,
                            levelbase_pk: grade_dict.levelbase_id,
                            lvl_abbrev: grade_dict.lvl_abbrev,

                            exam_pk: exam_dict.id,
                            exam_map_id: exam_dict.mapid,
                            subject_pk: (exam_dict.subject_id) ? exam_dict.subject_id : null,
                            subject_code: (exam_dict.subj_base_code) ? exam_dict.subj_base_code : null,
                            subject_name: (exam_dict.subj_name) ? exam_dict.subj_name : null,
                            department_pk: exam_dict.department_id,

                            is_admin_mode: false,
                            is_keys_mode: false,
                            is_same_school_mode: is_same_school_mode,

                            assignment: {},
                            keys: {},
                            answers: {}
                        }
                        MEX_get_assignment(exam_dict, grade_dict);
            console.log( "mod_MEX_dict.assignment", mod_MEX_dict.assignment);

                // ---  set header text
                        const examtype = (loc.examtype_caption && mod_MEX_dict.examtype) ? loc.examtype_caption[mod_MEX_dict.examtype] : loc.Exam;
                        const depbase_code = (setting_dict.sel_depbase_code) ? setting_dict.sel_depbase_code : "---";
                        const examperiod_caption = (loc.examperiod_caption && mod_MEX_dict.examperiod) ? loc.examperiod_caption[mod_MEX_dict.examperiod] : "---"
                        const header1_text = examtype + " " + depbase_code + " " + examperiod_caption;

                        document.getElementById("id_MEX_header1").innerText = header1_text;
                        document.getElementById("id_MEX_header2").innerText = exam_name;
                        document.getElementById("id_MEX_header3").innerText = fullname;

    // ---  set buttons
                        add_or_remove_class(el_MEX_btn_tab_container, cls_hide, is_same_school_mode);
                        MEX_BtnTabClicked(mod_MEX_dict.sel_tab);
                        MEX_SetPages();

                // ---  disable save button when not all required fields have value
                        // TODOMEXQ_validate_and_disable();

                // ---  show modal
                        $("#id_mod_exam_questions").modal({backdrop: true});

                    }  //  if(exam_dict)
                }  // if(map_dict.exam_id)
            }  // if(grade_dict)
        }  //  if(is_same_school_mode)
    };  // MEXA_Open


/////////////////////////////////////////

// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2021-05-06
    function ModConfirmOpen(table, mode, el_input) {
        console.log(" -----  ModConfirmOpen   ----")
        console.log("mode", mode)
        // values of mode are : "delete",
        // TODO print_exam not in use: remove, add 'publish'
        if(permit_dict.permit_crud){

            const is_delete = (mode === "delete")

    // ---  get MEXQ_
            let tblName = null, selected_pk = null;
            // tblRow is undefined when clicked on delete btn in submenu btn or form (no inactive btn)
            const tblRow = get_tablerow_selected(el_input);
            console.log("tblRow", tblRow )
            if(tblRow){
                tblName = get_attr_from_el(tblRow, "data-table")
                selected_pk = get_attr_from_el(tblRow, "data-pk")
            } else {
                tblName = table;
                selected_pk = (tblName === "exam") ? setting_dict.sel_exam_pk : null;
            }
            console.log("tblName", tblName )
            console.log("selected_pk", selected_pk )

    // ---  get info from data_map
            const data_map = (tblName === "exam") ? exam_map : null;
            const map_id =  tblName + "_" + selected_pk;
            const map_dict = get_mapdict_from_datamap_by_id(data_map, map_id);
            let href_str = {};

            console.log("data_map", data_map)
            console.log("map_id", map_id)
            console.log("map_dict", map_dict)

    // ---  create mod_dict
            mod_dict = {mode: mode, table: tblName};
            const has_selected_item = (!isEmpty(map_dict));
            if(has_selected_item){
                mod_dict.mapid = map_id;
                mod_dict.exam_pk = map_dict.id;
                mod_dict.subject_pk = map_dict.subject_id;
                mod_dict.subj_name = map_dict.subj_name;
                mod_dict.examyear_pk = setting_dict.sel_examyear_pk;
                mod_dict.depbase_pk = setting_dict.sel_depbase_pk;
            };

    // ---  get header_text
            let header_text = (is_delete) ? loc.Delete_exam : null;

    // ---  put text in modal form
            let msg_html = "", msg_list = [];
            let hide_save_btn = false;
            if(!has_selected_item){
               // msg_01_txt = loc.No_user_selected;
                hide_save_btn = true;
            } else {

                msg_list.push(loc.Exam + " '" + mod_dict.subj_name + "'" + loc.will_be_deleted);
                msg_list.push(loc.Do_you_want_to_continue);

            }

            for (let i = 0, msg; msg = msg_list[i]; i++) {
                msg_html += "<p class=\"py-1\">" + msg + "</p>"
            }
            el_confirm_msg_container.innerHTML = msg_html;

            el_confirm_header.innerText = header_text;
            el_confirm_loader.classList.add(cls_visible_hide)
            el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");
            el_confirm_btn_save.innerText = is_delete ? loc.Yes_delete : loc.OK;
            add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", is_delete, "btn-primary");

            add_or_remove_class (el_confirm_btn_save, cls_hide, hide_save_btn);
            el_confirm_btn_cancel.innerText = (is_delete) ? loc.No_cancel : loc.Cancel;

// +++  create href and put it in save button PR2021-05-06
            if (href_str){
                let href = url_exam_download_exam_pdf.replace("-", href_str);
                console.log ("href_str", href_str)
                console.log ("url_exam_download_exam_pdf", url_exam_download_exam_pdf)
                console.log ("href", href)
                el_confirm_btn_save.setAttribute("href", href)
                // target="_blank opens file in new tab
                el_confirm_btn_save.setAttribute("target", "_blank")
            }

    // set focus to cancel button
            setTimeout(function (){
                el_confirm_btn_cancel.focus();
            }, 500);
// show modal
            $("#id_mod_confirm").modal({backdrop: true});

        }  // if(may_edit){
    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2019-06-23
    function ModConfirmSave() {
        console.log(" --- ModConfirmSave --- ");
        console.log("mod_dict: ", mod_dict);
        let close_modal = !permit_dict.permit_crud;

        if(permit_dict.permit_crud){

    // ---  Upload Changes
            let upload_dict = { mode: mod_dict.mode,
                                exam_pk: mod_dict.exam_pk,
                                examyear_pk: mod_dict.examyear_pk,
                                depbase_pk: mod_dict.depbase_pk,
                                subject_pk: mod_dict.subject_pk,
                                };
            UploadChanges(upload_dict, url_exam_upload);
        };
// ---  hide modal
        //if(close_modal) {
            $("#id_mod_confirm").modal("hide");
        //}
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

//=========  ModMessageClose  ================ PR2020-12-20
    function ModMessageClose(el_btn) {
        console.log(" --- ModMessageClose --- ");
        const next_id = get_attr_from_el(el_btn, "data-nextid")
        set_focus_on_el_with_timeout(document.getElementById(next_id), 150 )
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

//=========  MSED_Response  ================ PR2020-12-18 PR2021-05-10
    function MSED_Response(new_setting) {
        //console.log( "===== MSED_Response ========= ");

// ---  upload new MEXQ_
// also retrieve the tables that have been changed because of the change in examyear / dep
        const datalist_request = {
                setting: new_setting,
                exam_rows: {cur_dep_only: true},
                subject_rows: {etenorm_only: true, cur_dep_only: true},
                grade_with_exam_rows: {get: true},
                published_rows: {get: true}
            };
        DatalistDownload(datalist_request);

    }  // MSED_Response

//=========  MSSSS_Response  ================ PR2021-01-23 PR2021-02-05 PR2021-07-26
    function MSSSS_Response(tblName, selected_dict, selected_pk) {
        console.log( "===== MSSSS_Response ========= ");
        console.log( "selected_pk", selected_pk);

    // ---  upload new setting
        if(selected_pk === -1) { selected_pk = null};
        const upload_dict = {};
        const selected_pk_dict = {sel_student_pk: selected_pk};
        selected_pk__dict["sel_" + tblName + "_pk"] = selected_pk;
        let new_selected_btn = null;

        if (tblName === "school") {
            // not enabled on this page
        } else {
            UploadSettings ({selected_pk: selected_pk_dict}, url_settings_upload);
            if (new_selected_btn) {
        // change selected_button
                HandleBtnSelect(new_selected_btn, true)  // true = skip_upload
                // also calls: FillTblRows(), MSSSS_display_in_sbr(), UpdateHeader()
            }  else {
        // fill datatable
                FillTblRows();
                MSSSS_display_in_sbr()
        // --- update header text - comes after MSSSS_display_in_sbr
                UpdateHeaderLeft();
            }
        }

        if (tblName === "subject") {
            setting_dict.sel_subject_pk = selected_pk;
    // reset selected student when subject is selected, in setting_dict and upload_dict
            if(selected_pk){
                selected_pk_dict.sel_student_pk = null;
                setting_dict.sel_student_pk = null;
                setting_dict.sel_student_name = null;
                new_selected_btn = "grade_by_subject";
            }
        } else if (tblName === "student") {
            setting_dict.sel_student_pk = selected_pk;
            //setting_dict.sel_student_name = selected_name;
    // reset selected subject when student is selected, in setting_dict and upload_dict
            if(selected_pk){
                selected_pk_dict.sel_subject_pk = null;
                setting_dict.sel_subject_pk = null;
                new_selected_btn = "grade_by_student";
            }

        }
        UploadSettings ({selected_pk: selected_pk_dict}, url_settings_upload);

        if (new_selected_btn) {
    // change selected_button
            HandleBtnSelect(new_selected_btn, true)  // true = skip_upload
            // also calls: FillTblRows(), MSSSS_display_in_sbr(), UpdateHeader()
        }  else {
    // fill datatable
            FillTblRows();

    // --- update header text - comes after MSSSS_display_in_sbr
            UpdateHeaderLeft();
        }

    }  // MSSSS_Response

//========= get_tblName_from_selectedBtn  ======== // PR2021-01-22
    function get_tblName_from_selectedBtn() {
        const tblName = (selected_btn === "grade_published") ? "published" : "grades";
        return tblName;
    }


})  // document.addEventListener('DOMContentLoaded', function()