// PR2020-09-29 added
document.addEventListener("DOMContentLoaded", function() {
    "use strict";

// ---  get el_loader
    let el_loader = document.getElementById("id_loader");

// ---  get permits
    // permit dict gets value after downloading permit_list PR2021-03-27
    //  if user has no permit to view this page ( {% if no_access %} ): el_loader does not exist PR2020-10-02
    // Note: may_view_page is the only permit that gets its value on DOMContentLoaded,
    // all other permits get their value in function get_permits, after downloading permit_list
    const may_view_page = (!!el_loader)

    //let usergroups = [];

    const cls_hide = "display_hide";
    const cls_hover = "tr_hover";
    const cls_visible_hide = "visibility_hide";
    const cls_selected = "tsa_tr_selected";

// ---  id of selected customer and selected order
    let selected_btn = "grade_by_subject";
    let setting_dict = {};
    let permit_dict = {};
    let loc = {};  // locale_dict

    let mod_dict = {};
    let mod_MSTUD_dict = {};
    let mod_MSSS_dict = {};
    let mod_MAG_dict = {};
    let mod_status_dict = {};
    let mod_note_dict = {};

    let time_stamp = null; // used in mod add user

    let user_list = [];

    let examyear_map = new Map();
    let school_map = new Map();
    let department_map = new Map();

    let level_map = new Map();
    let sector_map = new Map();

    let student_map = new Map();
    let subject_map = new Map();
    let grade_map = new Map();

    let published_map = new Map();
    let studentsubject_map = new Map();
    let studentsubjectnote_map = new Map();

    let filter_dict = {};
    let filter_mod_employee = false;

    let el_focus = null; // stores id of element that must get the focus after cloosing mod message PR2020-12-20

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    const url_datalist_download = get_attr_from_el(el_data, "data-datalist_download_url");
    const url_settings_upload = get_attr_from_el(el_data, "data-settings_upload_url");
    const url_subject_upload = get_attr_from_el(el_data, "data-subject_upload_url");
    const url_grade_upload = get_attr_from_el(el_data, "data-grade_upload_url");

    const url_grade_approve = get_attr_from_el(el_data, "data-grade_approve_url");
    const url_download_grade_icons = get_attr_from_el(el_data, "data-download_grade_icons_url");
    const url_grade_download_ex2a = get_attr_from_el(el_data, "data-grade_download_ex2a_url");
    const url_download_published = get_attr_from_el(el_data, "data-download_published_url");
    const url_studentsubjectnote_upload = get_attr_from_el(el_data, "data-studentsubjectnote_upload_url");
    const url_studentsubjectnote_download = get_attr_from_el(el_data, "data-studentsubjectnote_download_url");
    const url_noteattachment_download = get_attr_from_el(el_data, "data-noteattachment_download_url");

// --- get field_settings
    const columns_shown = {select: true, examnumber: true, fullname: true,
                            lvl_abbrev: true, sct_abbrev: true,
                            subj_code: true, subj_name: true,
                            pescore: true, cescore: true,
                            segrade: true, se_status: true,
                            pegrade: true, pe_status: true,
                            cegrade: true, ce_status: true,
                            pecegrade: true, weighing: true, finalgrade: true, note_status: true,
                            // in table published:
                            name: true, examperiod: true, examtype: true, datepublished: true,
                            filename: true, url: true
                           };
    const field_settings = {
        grades: { field_caption: ["", "Ex_nr", "Candidate", "Leerweg_twolines", "Sector", "Abbreviation", "Subject",
                                  "SE_grade_twolines", "",
                                  "PE_score_twolines", "PE_grade_twolines", "",
                                  "CE_score_twolines", "CE_grade_twolines", "",
                                  "PECE_grade_twolines", "SECE_weighing",  "Final_grade_twolines", ""],
                    field_names: ["select", "examnumber", "fullname",  "lvl_abbrev", "sct_abbrev", "subj_code", "subj_name",
                                  "segrade", "se_status",
                                  "pescore", "pegrade", "pe_status",
                                  "cescore", "cegrade","ce_status",
                                  "pecegrade", "weighing", "finalgrade", "note_status"],
                    field_tags: ["div", "div", "div", "div", "div", "div", "div",
                                "input", "div",
                                "input", "input", "div",
                                "input","input","div",
                                "div", "div", "div", "div"],
                    filter_tags: ["text", "text","text", "text", "text", "text", "text",
                                 "text", "text",
                                  "text","text", "text",
                                  "text", "text", "text",
                                  "text", "text", "text", "text"],
                    field_width: ["020", "060", "120", "060", "060", "060", "120",
                                 "075", "020",
                                "075", "075", "020",
                                "075","075","020",
                                "075", "075", "075", "020"],
                    field_align: ["c", "r", "l", "l", "l", "l", "l",
                                 "r", "c",
                                 "r","r","c",
                                 "r","r","c",
                                 "r", "c", "c", "c"]},
        published: {field_caption: ["", "Name_ex_form", "Exam_period", "Exam_type", "Date_submitted", "Download_Exform"],
                    field_names: ["select", "name", "examperiod",  "examtype", "datepublished", "url"],
                    field_tags: ["div", "div", "div", "div", "div", "a"],
                    filter_tags: ["text", "text","text", "text",  "text", "text"],
                    field_width: ["020", "480", "150", "150", "150", "120"],
                    field_align: ["c", "l", "l", "l", "l", "c"]}
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


// ---  SIDEBAR ------------------------------------
        const el_SBR_select_examperiod = document.getElementById("id_SBR_select_period");
        const el_SBR_select_examtype = document.getElementById("id_SBR_select_examtype");
        const el_SBR_select_level = document.getElementById("id_SBR_select_level");
        const el_SBR_select_sector = document.getElementById("id_SBR_select_sector");
        const el_SBR_select_subject = document.getElementById("id_SBR_select_subject");
        const el_SBR_select_student = document.getElementById("id_SBR_select_student");
        const el_SBR_select_showall = document.getElementById("id_SBR_select_showall");
        if (el_SBR_select_examperiod){el_SBR_select_examperiod.addEventListener("change", function() {HandleSbrPeriod(el_SBR_select_examperiod)}, false)};
        if (el_SBR_select_examtype){el_SBR_select_examtype.addEventListener("change", function() {HandleSbrExamtype(el_SBR_select_examtype)}, false)};
        if (el_SBR_select_level){el_SBR_select_level.addEventListener("change", function() {HandleSbrLevelSector("level", el_SBR_select_level)}, false)};
        if (el_SBR_select_sector){el_SBR_select_sector.addEventListener("change", function() {HandleSbrLevelSector("sector", el_SBR_select_sector)}, false)};
        if (el_SBR_select_subject){
            el_SBR_select_subject.addEventListener("click",
                function() {t_MSSSS_Open(loc, "subject", subject_map, true, setting_dict, permit_dict, MSSSS_Response)}, false)};
        if (el_SBR_select_student){
            el_SBR_select_student.addEventListener("click",
                function() {t_MSSSS_Open(loc, "student", student_map, true, setting_dict, permit_dict, MSSSS_Response)}, false)};
        if (el_SBR_select_showall){el_SBR_select_showall.addEventListener("click", function() {HandleShowAll()}, false )};

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
        if (el_MAG_btn_delete){
            el_MAG_btn_delete.addEventListener("click", function() {MAG_Save("delete")}, false )  // true = reset
        }
        if (el_MAG_btn_save){
            el_MAG_btn_save.addEventListener("click", function() {MAG_Save("save")}, false )
        }

// ---  MOD CONFIRM ------------------------------------
        const el_confirm_header = document.getElementById("id_confirm_header");
        const el_confirm_loader = document.getElementById("id_confirm_loader");
        const el_confirm_msg_container = document.getElementById("id_confirm_msg_container");
        const el_confirm_msg01 = document.getElementById("id_confirm_msg01");
        const el_confirm_msg02 = document.getElementById("id_confirm_msg02");
        const el_confirm_msg03 = document.getElementById("id_confirm_msg03");
        const el_confirm_btn_cancel = document.getElementById("id_confirm_btn_cancel");
        const el_confirm_btn_save = document.getElementById("id_confirm_btn_save");
        if(el_confirm_btn_save){
            el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()})
        };

// ---  MOD STATUS ------------------------------------
        const el_mod_status_btn_save =  document.getElementById("id_mod_status_btn_save");
        const el_mod_status_header = document.getElementById("id_mod_status_header");
        const el_mod_status_note_container = document.getElementById("id_mod_status_note_container");
        if(el_mod_status_btn_save){
            el_mod_status_btn_save.addEventListener("click", function() {ModalStatusSave()}, false );
        }

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
        }

// ---  MOD MESSAGE ------------------------------------
        const el_modmessage_btn_cancel = document.getElementById("id_modmessage_btn_cancel");
        const el_mod_message_text = document.getElementById("id_mod_message_text");
        //if(el_modmessage_btn_cancel){
       //     el_modmessage_btn_cancel.addEventListener("click", function() {ModMessageClose()}, false);
        //}

    if(may_view_page){
// ---  set selected menu button active
        SetMenubuttonActive(document.getElementById("id_hdr_users"));

        const datalist_request = {
                setting: {page: "page_grade"},
                locale: {page: ["page_grade"]},
                examyear_rows: {get: true},
                school_rows: {get: true},
                department_rows: {get: true},
                subject_rows: {get: true},
                student_rows: {get: true},
                studentsubject_rows: {get: true},
                grade_rows: {get: true},
                published_rows: {get: true},
                level_rows: {get: true},
                sector_rows: {get: true}
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
                let check_status = false;
                let isloaded_loc = false, isloaded_settings = false, isloaded_permits = false;

                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                    // mimp_loc = loc;
                    isloaded_loc = true;
                };

                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict;
                    selected_btn = setting_dict.sel_btn;
                    isloaded_settings = true;

                    // if sel_subject_pk has value, set sel_student_pk null
                    if (setting_dict.sel_subject_pk) {setting_dict.sel_student_pk = null;}

                    FillOptionsExamperiodExamtype();
                };
                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    isloaded_permits = true;
                    // get_permits must come before CreateSubmenu and FiLLTbl
                    b_get_permits_from_permitlist(permit_dict);
                    //set_columns_hidden();
                }
                if ("schoolsetting_dict" in response) {
                    i_UpdateSchoolsettingsImport(response.schoolsetting_dict)
                };
                // both 'loc' and 'setting_dict' are needed for CreateSubmenu
                if (isloaded_loc && isloaded_permits) {CreateSubmenu()};
                if(isloaded_settings || isloaded_permits){b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);};

                // call b_render_awp_messages also when there are no messages, to remove existing messages
                if ("awp_messages" in response) {
                    b_render_awp_messages(response.awp_messages);
                };

                if ("examyear_rows" in response) { b_fill_datamap(examyear_map, response.examyear_rows) };
                if ("school_rows" in response)  {b_fill_datamap(school_map, response.school_rows)};
                if ("department_rows" in response) { b_fill_datamap(department_map, response.department_rows) };

                if ("level_rows" in response) {
                    b_fill_datamap(level_map, response.level_rows)
                    FillOptionsSelectLevelSector("level", response.level_rows)
                };
                if ("sector_rows" in response) {
                    b_fill_datamap(sector_map, response.level_rows)
                    FillOptionsSelectLevelSector("sector", response.sector_rows)
                };
                if ("subject_rows" in response) { b_fill_datamap(subject_map, response.subject_rows) };
                if ("student_rows" in response) { b_fill_datamap(student_map, response.student_rows) };
                if ("studentsubject_rows" in response) { b_fill_datamap(studentsubject_map, response.studentsubject_rows) };
                if ("published_rows" in response) {b_fill_datamap(published_map, response.published_rows)};

                if ("grade_rows" in response) {
                    b_fill_datamap(grade_map, response.grade_rows);
        // get icons of notes and status PR2021-04-21
                    DownloadGradeStatusAndIcons();
                };

                HandleBtnSelect(null, true)  // true = skip_upload
                // also calls: FillTblRows(), MSSSS_display_in_sbr(), UpdateHeader()ect
            },
            error: function (xhr, msg) {
// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                console.log(msg + '\n' + xhr.responseText);
                alert(msg + '\n' + xhr.responseText);
            }
        });
    }  // function DatalistDownload

//=========  CreateSubmenu  ===  PR2020-07-31 PR2021-01-19 PR2021-03-25
    function CreateSubmenu() {
        //console.log("===  CreateSubmenu == ");

        let el_submenu = document.getElementById("id_submenu")
        AddSubmenuButton(el_submenu, loc.Preliminary_Ex2A_form, null, "id_submenu_download_ex2a", url_grade_download_ex2a, true);  // true = download
        if (permit_dict.approve_grade){
            AddSubmenuButton(el_submenu, loc.Approve_grades, function() {MAG_Open("approve")});
        }
        if (permit_dict.submit_grade){
            AddSubmenuButton(el_submenu, loc.Submit_Ex2A_form, function() {MAG_Open("submit")});
        };
        el_submenu.classList.remove(cls_hide);

    };//function CreateSubmenu

//###########################################################################
//=========  HandleBtnSelect  ================ PR2020-09-19  PR2020-11-14  PR2021-03-15
    function HandleBtnSelect(data_btn, skip_upload) {
        //console.log( "===== HandleBtnSelect ========= ", data_btn);
        // function is called by HandleShowAll, MSSSS_Response, select_btn.click, DatalistDownload after response.setting_dict

        if(data_btn){
            selected_btn = data_btn;
        } else {
            // data_btn only has no value response.setting_dict. Retrieve value from settings
            if(setting_dict.sel_subject_pk ) {
                selected_btn = "grade_by_subject"
                setting_dict.sel_student_pk = null;
                setting_dict.sel_student_name = null;
            } else if(setting_dict.sel_student_pk ) {
                selected_btn = "grade_by_student"
                setting_dict.sel_subject_pk = null;
                setting_dict.sel_subject_code = null;
            } else {
                selected_btn = setting_dict.sel_btn
            }
            if(!selected_btn){selected_btn = "grade_by_all"}
        }

// ---  upload new selected_btn, not after DatalistDownload or HandleShowAll (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_grade: {sel_btn: selected_btn}};
            UploadSettings (upload_dict, url_settings_upload);
        };

// ---  highlight selected button
        highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  show only the elements that are used in this tab
        // PR2021-02-08this page does not contain tab_show yet.
        // modapprovegrade does. Make sure they have different names
        //show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

// --- update header text
        MSSSS_display_in_sbr();

// --- update header text - comes after MSSSS_display_in_sbr
        UpdateHeaderLeft();
        UpdateHeaderRight();

// ---  fill datatable
        FillTblRows();

    }  // HandleBtnSelect

//=========  HandleTblRowClicked  ================ PR2020-08-03
    function HandleTblRowClicked(tr_clicked) {
        //console.log("=== HandleTblRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        DeselectHighlightedRows(tr_clicked, cls_selected);
        tr_clicked.classList.add(cls_selected)

// ---  update setting_dict.sel_student_pk
        // only select employee from select table
        const row_id = tr_clicked.id
        if(row_id){
            const map_dict = get_mapdict_from_datamap_by_id(student_map, row_id)
            //setting_dict.sel_student_pk = map_dict.id;
        }
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
        const sel_examperiod = (Number(el_select.value)) ? Number(el_select.value) : null;
        const filter_value = sel_examperiod;

// --- fill seelctbox examtype with examtypes of this period
        t_FillOptionsFromList(el_SBR_select_examtype, loc.options_examtype, "value", "caption",
            loc.Select_examtype, loc.No_examtypes_found, "filter", filter_value);

// ---  upload new setting
        let new_setting = {page_grade: {mode: "get"}};
        new_setting.selected_pk = {sel_examperiod: sel_examperiod}
        const datalist_request = {setting: new_setting};

// also retrieve the tables that have been changed because of the change in examperiod
        datalist_request.grade_rows = {get: true};
        DatalistDownload(datalist_request);

    }  // HandleSbrPeriod

//=========  HandleSbrExamtype  ================ PR2020-12-20
    function HandleSbrExamtype(el_select) {
        console.log("=== HandleSbrExamtype");
        console.log( "el_select.value: ", el_select.value, typeof el_select.value)
        // sel_examtype = "se", "pe", "ce", "re2", "re3", "exm"
        setting_dict.sel_examtype = el_select.value;
        const filter_value = Number(el_select.value);
        //t_FillOptionsFromList(el_SBR_select_examtype, loc.options_examtype, "value", "caption",
        //    loc.Select_examtype, loc.No_examtypes_found, setting_dict.sel_examtype, "filter", filter_value);

        console.log( "setting_dict.sel_examtype: ", setting_dict.sel_examtype, typeof setting_dict.sel_examtype)

// ---  upload new setting
        const upload_dict = {selected_pk: {sel_examtype: setting_dict.sel_examtype}};
        UploadSettings (upload_dict, url_settings_upload);

        FillTblRows();
    }  // HandleSbrExamtype

//=========  HandleSbrLevelSector  ================ PR2021-03-06
    function HandleSbrLevelSector(tblName, el_select) {
        console.log("=== HandleSbrLevelSector");
        console.log( "el_select.value: ", el_select.value, typeof el_select.value)

        // tblName = "level" or "sector"
        const sel_pk_int = (Number(el_select.value)) ? Number(el_select.value) : null;
        const sel_abbrev = (el_select.options[el_select.selectedIndex]) ? el_select.options[el_select.selectedIndex].text : null;
        const filter_value = sel_pk_int;
        const sel_dict = {};
        if (tblName === "level"){
            setting_dict.sel_level_pk = sel_pk_int;
            setting_dict.sel_level_abbrev = sel_abbrev;
            sel_dict.sel_level_pk = sel_pk_int;
        } else if (tblName === "sector"){
            setting_dict.sel_sector_pk = sel_pk_int;
            setting_dict.sel_sector_abbrev = sel_abbrev;
            sel_dict.sel_sector_pk = sel_pk_int;
        }
        console.log( "setting_dict: ", setting_dict)

// ---  upload new setting
        const upload_dict = {selected_pk: sel_dict};
        console.log( "upload_dict: ", upload_dict)
        UploadSettings (upload_dict, url_settings_upload);

        UpdateHeaderRight();

        FillTblRows();
    }  // HandleSbrLevelSector

//=========  FillOptionsExamperiodExamtype  ================ PR2021-03-08
    function FillOptionsExamperiodExamtype() {
        //console.log("=== FillOptionsExamperiodExamtype");

        const sel_examperiod = setting_dict.sel_examperiod;
        t_FillOptionsFromList(el_SBR_select_examperiod, loc.options_examperiod, "value", "caption",
            loc.Select_examperiod + "...", loc.No_examperiods_found, sel_examperiod);
        //document.getElementById("id_hdr_textright1").innerText = setting_dict.sel_examperiod_caption
        document.getElementById("id_SBR_container_examperiod").classList.remove(cls_hide);

        const filter_value = sel_examperiod;
        t_FillOptionsFromList(el_SBR_select_examtype, loc.options_examtype, "value", "caption",
            loc.Select_examtype + "...", loc.No_examtypes_found, setting_dict.sel_examtype, "filter", filter_value);
        document.getElementById("id_SBR_container_examtype").classList.remove(cls_hide);

        document.getElementById("id_SBR_container_showall").classList.remove(cls_hide);

    }  // FillOptionsExamperiodExamtype

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
                    setting_dict.sel_level_pk = rows.base_id;
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

            const selected_pk = (tblName === "level") ? setting_dict.sel_level_pk : (tblName === "sector") ? setting_dict.sel_sector_pk : null;
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
            add_or_remove_class(document.getElementById("id_SBR_container_level"), cls_hide, !has_items);
        // set label of profiel
         } else if (tblName === "sector"){
            add_or_remove_class(document.getElementById("id_SBR_container_sector"), cls_hide, false);

            document.getElementById("id_SBR_select_sector_label").innerText = ( (has_profiel) ? loc.Profiel : loc.Sector ) + ":";
        }
    }  // FillOptionsSelectLevelSector

//=========  HandleShowAll  ================ PR2020-12-17
    function HandleShowAll() {
        console.log("=== HandleShowAll");

        setting_dict.sel_level_pk = null;
        setting_dict.sel_level_abbrev = null;

        setting_dict.sel_sector_pk = null;
        setting_dict.sel_sector_abbrev = null;

        setting_dict.sel_subject_pk = null;
        setting_dict.sel_student_pk = null;

        el_SBR_select_level.value = "0";
        el_SBR_select_sector.value = "0";

// ---  upload new setting
        const selected_pk_dict = {sel_level_pk: null, sel_sector_pk: null, sel_subject_pk: null, sel_student_pk: null};
        const page_grade_dict = {sel_btn: "grade_by_all"}
        const upload_dict = {selected_pk: selected_pk_dict, page_grade: page_grade_dict};
        UploadSettings (upload_dict, url_settings_upload);

        HandleBtnSelect("grade_by_all", true) // true = skip_upload
        // also calls: FillTblRows(), MSSSS_display_in_sbr(), UpdateHeader()

    }  // HandleShowAll

//========= UpdateHeaderLeft  ================== PR2021-03-14
    function UpdateHeaderLeft(){
        //console.log(" --- UpdateHeaderLeft ---" )
        //console.log("setting_dict", setting_dict)
        // sel_subject_txt gets value in MSSSS_display_in_sbr, therefore UpdateHeader comes after MSSSS_display_in_sbr
        const header_left = (setting_dict.sel_subject_pk) ? setting_dict.sel_subject_txt :
                            (setting_dict.sel_student_pk) ? setting_dict.sel_student_name : loc.All_subjects_and_candidates;
        document.getElementById("id_hdr_left").innerText = header_left
    }   //  UpdateHeaderLeft

//========= UpdateHeaderRight  ================== PR2021-03-14
    function UpdateHeaderRight(){
        //console.log(" --- UpdateHeaderRight ---" )
        let header_right = "";
        if (setting_dict.sel_level_pk) { header_right = setting_dict.sel_level_abbrev }
        if (setting_dict.sel_sector_pk) {
            if(header_right) { header_right += " - " };
            header_right += setting_dict.sel_sector_abbrev
        }
        if(header_right) { header_right += " - " };

        if (setting_dict.sel_examperiod === 1){
            header_right += setting_dict.sel_examperiod_caption
        } else if (setting_dict.sel_examperiod === 2){
            header_right += loc.Re_examination
        } else if (setting_dict.sel_examperiod === 3){
            header_right += loc.Re_examination_3rd_period
        } else if (setting_dict.sel_examperiod === 4){
            header_right += setting_dict.sel_examperiod_caption
        } else {
            header_right += "---"
        }
        document.getElementById("id_hdr_textright1").innerText = header_right;
    }   //  UpdateHeaderRight

//========= FillTblRows  ====================================
    function FillTblRows() {
        //console.log( "===== FillTblRows  === ");

        const tblName = get_tblName_from_selectedBtn()
        const field_setting = field_settings[tblName];
        const data_map = get_datamap_from_tblName(tblName);

// --- show columns
        set_columns_shown();

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

// --- create table header
        CreateTblHeader(field_setting);

// --- loop through grade_map
        //console.log( "data_map", data_map);
        if(data_map){
            for (const [map_id, map_dict] of data_map.entries()) {

            // only show rows of selected student / subject
                let show_row = (tblName === "published") ? true :
                                (!setting_dict.sel_level_pk || map_dict.lvl_id === setting_dict.sel_level_pk) &&
                                (!setting_dict.sel_sector_pk || map_dict.sct_id === setting_dict.sel_sector_pk) &&
                                (!setting_dict.sel_student_pk || map_dict.student_id === setting_dict.sel_student_pk) &&
                                (!setting_dict.sel_subject_pk || map_dict.subject_id === setting_dict.sel_subject_pk);

                if(show_row){
          // --- insert row at row_index
                    //const schoolcode_lc_trail = ( (map_dict.sb_code) ? map_dict.sb_code.toLowerCase() : "" ) + " ".repeat(8) ;
                    //const schoolcode_sliced = schoolcode_lc_trail.slice(0, 8);
                    //const order_by = schoolcode_sliced +  ( (map_dict.username) ? map_dict.username.toLowerCase() : "");
                    const row_index = -1; // t_get_rowindex_by_sortby(tblBody_datatable, order_by)
                    let tblRow = CreateTblRow(tblName, field_setting, map_id, map_dict, row_index)
                }
          };
        }  // if(!!data_map)

    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-12-03 PR2020-12-18 PR2021-01-022
    function CreateTblHeader(field_setting) {
        //console.log("===  CreateTblHeader ===== ");

        const column_count = field_setting.field_names.length;

// +++  insert header and filter row ++++++++++++++++++++++++++++++++
        let tblRow_header = tblHead_datatable.insertRow (-1);
        let tblRow_filter = tblHead_datatable.insertRow (-1);

    // --- loop through columns
        for (let j = 0; j < column_count; j++) {
            const field_name = field_setting.field_names[j];
            const key = field_setting.field_caption[j];
            let field_caption = (loc[key]) ? loc[key] : key;

            if (field_name === "segrade") {
                if (setting_dict.sel_examperiod === 4){
                    field_caption = "Vrijstelling\nSE-cijfer"
                }
            } else if (field_name === "cescore") {
                if (setting_dict.sel_examperiod === 2){
                    field_caption = "Herexamen\nscore"
                } else if (setting_dict.sel_examperiod === 3){
                    field_caption = "Her 3e tv\nscore"
                }
            } else if (field_name === "cegrade") {
                if (setting_dict.sel_examperiod === 2){
                    field_caption = "Herexamen cijfer"
                } else if (setting_dict.sel_examperiod === 3){
                    field_caption = "Her 3e tv cijfer"
                } else if (setting_dict.sel_examperiod === 4){
                    field_caption = "Vrijstelling\nCE-cijfer"
                }
            }

            const field_tag = field_setting.field_tags[j];
            const filter_tag = field_setting.filter_tags[j];
            const class_width = "tw_" + field_setting.field_width[j] ;
            const class_align = "ta_" + field_setting.field_align[j];

    // - skip columns if not columns_shown[field_name]) = true;
            if (columns_shown[field_name]){

// ++++++++++ insert columns in header row +++++++++++++++
        // --- add th to tblRow_header +++
                let th_header = document.createElement("th");
        // --- add div to th, margin not working with th
                    const el_header = document.createElement("div");
                        el_header.innerText = field_caption;
        // --- add width, text_align, right padding in examnumber
                        th_header.classList.add(class_width, class_align);
                        el_header.classList.add(class_width, class_align);
                        if(field_name === "examnumber"){
                            el_header.classList.add("pr-2")
                        } else if (["se_status", "pe_status", "ce_status"].indexOf(field_name) > -1) {
                            el_header.classList.add("appr_0_1")
                        } else if(field_name === "note_status"){
                             // dont show note icon when user has no permit_read_note
                            const class_str = (permit_dict.read_note) ? "note_0_1" : "note_0_0"
                            el_header.classList.add(class_str)
                        }
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

                        //} else if (["toggle", "activated", "inactive"].includes(filter_tag)) {
                        //    // default empty icon necessary to set pointer_show
                        //    // default empty icon necessary to set pointer_show
                        //    append_background_class(el_filter, "tickmark_0_0");
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

//=========  CreateTblRow  ================ PR2020-06-09
    function CreateTblRow(tblName, field_setting, map_id, map_dict, row_index) {
        //console.log("=========  CreateTblRow =========");
        //console.log("map_dict", map_dict);

        const field_names = field_setting.field_names;
        const field_tags = field_setting.field_tags;
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;

// --- insert tblRow into tblBody at row_index
        let tblRow = tblBody_datatable.insertRow(row_index);
        tblRow.id = map_id

// --- add data attributes to tblRow
        const pk_int = map_dict.id
        tblRow.setAttribute("data-pk", map_dict.id);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        // happens in UpdateTblRow
        const order_by_stud = (map_dict.fullname) ? map_dict.fullname.toLowerCase() : null;
        const order_by_subj = (map_dict.subj_name) ? map_dict.subj_name.toLowerCase() : null;
        tblRow.setAttribute("data-sortby_stud", order_by_stud);
        tblRow.setAttribute("data-sortby_subj", order_by_subj);

// --- add EventListener to tblRow
        tblRow.addEventListener("click", function() {HandleTblRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
        for (let j = 0; j < column_count; j++) {
            const field_name = field_names[j];

// skip columns if not in columns_shown
            if (columns_shown[field_name]){
                const field_tag = field_tags[j];
                const class_width = "tw_" + field_width[j];
                const class_align = "ta_" + field_align[j];

        // --- insert td element,
                let td = tblRow.insertCell(-1);

        // --- add EventListener to td
                if (["se_status", "pe_status", "ce_status"].includes(field_name)) {
                    td.addEventListener("click", function() {UploadToggle(el)}, false)
                    add_hover(td);
                } else if (field_name === "note_status"){
                    if(permit_dict.read_note){
                        td.addEventListener("click", function() {ModNote_Open(el)}, false)
                        add_hover(td);
                    }
                //} else if (field_name === "filename"){
                   // const file_name = (map_dict.name) ? map_dict.name : "";
                    //add_hover(td);
                }
                //td.classList.add("pointer_show", "px-2");

        // --- create element with tag from field_tags
                let el = document.createElement(field_tag);

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

                    if (field_name.includes("status")){
    // --- add column with status icon
                        el.classList.add("stat_0_0")
                    } else if (field_name === "note_status"){
                        el.classList.add("note_0_0")

                    } else if (field_name === "filename"){
                        /*
                        const name = (map_dict.name) ? map_dict.name : null;
                        const file_path = (map_dict.filepath) ? map_dict.filepath : null;
                        console.log("file_path", file_path)
                        if (file_path){
                            // url_download_published = "/grades/download//0/"
                            const len = url_download_published.length;
                            const href = url_download_published.slice(0, len - 2) + map_dict.id +"/"
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

    // --- put value in field
                UpdateField(el, map_dict)
            }  //  if (columns_shown[field_name])
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

//=========  UpdateField  ================ PR2020-12-18 PR2021-05-30
    function UpdateField(el_div, map_dict) {
        //console.log("=========  UpdateField =========");
        //console.log("map_dict", map_dict);
        if(el_div){
            const field_name = get_attr_from_el(el_div, "data-field");
            const fld_value = map_dict[field_name];

            if(field_name){
                let title_text = null, filter_value = null;
                if (el_div.nodeName === "INPUT"){
                    el_div.value = (fld_value) ? fld_value : null;
                    filter_value = (fld_value) ? fld_value.toLowerCase() : null;
                } else if (["se_status", "pe_status", "ce_status"].includes(field_name)){
                    el_div.className = get_status_class(fld_value)
                } else if (field_name === "note_status"){
                    // dont show note icon when user has no permit_read_note
                    el_div.className = "note_" + ( (permit_dict.read_note && fld_value && fld_value !== "0") ?
                        (fld_value.length === 3) ? fld_value : "0_1" : "0_0" )
                 } else if (field_name === "filename"){
                    //el_div.innerHTML = "&#8681;";
                } else if (field_name === "url"){
                    el_div.href = fld_value;
                } else {
                    let inner_text = null;
                    if (field_name === "examperiod"){
                        inner_text = loc.examperiod_caption[map_dict.examperiod];
                    } else if (field_name === "examtype"){
                        inner_text = loc.examtype_caption[map_dict.examtype];
                    } else if (field_name === "datepublished"){
                        inner_text = format_dateISO_vanilla (loc, map_dict.datepublished, true, false, true, false);
                    } else {
                        inner_text = fld_value;
                    }
                    el_div.innerText = (inner_text) ? inner_text : null;
                    filter_value = (inner_text) ? inner_text.toLowerCase() : null;
                // NIU yet: add_or_remove_attr (el_div, "title", !!title_text, title_text);
                }

    // ---  add attribute filter_value
                add_or_remove_attr (el_div, "data-filter", !!filter_value, filter_value);
            }
        }
    };  // UpdateField

//========= set_columns_shown  ====== PR2021-03-08
    function set_columns_shown() {
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

                // sel_examtype = "se", "pe", "ce", "re2", "re3", "exm"
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
        } else if (sel_examtype === "re2"){
            columns_shown.cescore = true; columns_shown.cegrade = true; columns_shown.ce_status = true;
        } else if (sel_examtype === "re3"){
            columns_shown.cescore = true; columns_shown.cegrade = true; columns_shown.ce_status = true;
        } else if (sel_examtype === "exm"){
            columns_shown.segrade = true; columns_shown.se_status = true;
            columns_shown.cegrade = true; columns_shown.ce_status = true;
        }

        columns_shown.lvl_abbrev = (!!setting_dict.sel_level_pk);
        columns_shown.sct_abbrev = (!!setting_dict.sel_sector_pk);

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
                const next_el = new_tblRow.cells[new_col_index].children[0];
                if(next_el){next_el.focus()}
            }
        }
    }  // HandleArrowEvent

//========= HandleInputChange  ===============PR2020-08-16 PR2021-03-25
    function HandleInputChange(el_input){
        console.log(" --- HandleInputChange ---")

        const tblRow = get_tablerow_selected(el_input)
        const map_id = tblRow.id
        if (map_id){
            const map_dict = get_mapdict_from_datamap_by_id(grade_map, map_id)
            const fldName = get_attr_from_el(el_input, "data-field")
            const map_value = map_dict[fldName];
        console.log("fldName", fldName)
        console.log("map_dict", map_dict)

            if (!permit_dict.crud_grade){
        // show message no permission
                b_show_mod_message(loc.grade_err_list.no_permission);
        // put back old value  in el_input
                el_input.value = map_value;

            } else {
                const map_value = map_dict[fldName];
                const locked_field = fldName.slice(0, 2) + "_locked";
                const published_field = fldName.slice(0, 2) + "_published_id";
                const is_locked = map_dict[locked_field] ? map_dict[locked_field] : false;

                if (is_locked){
                    // Note: if grade is_published and not locked: this means the inspection has given permission to change grade
                    const is_submitted = map_dict[published_field] ? true : false;
                    const msg_html = (is_submitted) ? loc.grade_err_list.grade_submitted + "<br>" + loc.grade_err_list.need_permission_inspection :
                                                      loc.grade_err_list.grade_approved + "<br>" + loc.grade_err_list.needs_approvals_removed+ "<br>" + loc.grade_err_list.Then_you_can_change_it;

            // show message
                    b_show_mod_message(msg_html);
            // put back old value  in el_input
                    el_input.value = map_value;
                } else {
                    const new_value = el_input.value;
                    if(new_value !== map_value){
                        // FOR TESTING ONLY: turn validate of to test server validation
                        const validate_on = true;
                        let value_text = new_value, msg_html = null
                        if (validate_on){
                            const arr = ValidateGrade(loc, fldName, new_value, map_dict);
                            value_text = arr[0];
                            msg_html = arr[1];
                        }
                        if (msg_html){
            // ---  show modal MESSAGE
                            b_show_mod_message(msg_html);

                            el_focus = el_input;
                            el_input.value = null;

                        } else {

                            //>>>>>>>>>>>el_input.value = value_text;
                            let url_str = url_grade_upload;

                            // must loose focus, otherwise green / red border won't show
                            //el_input.blur();

                            //const el_loader =  document.getElementById("id_MSTUD_loader");
                           // el_loader.classList.remove(cls_visible_hide);

                    // ---  upload changes
                            const upload_dict = { table: map_dict.table,
                                                   mode: "update",
                                                   mapid: map_id,

                                                   examperiod: map_dict.examperiod,
                                                   grade_pk: map_dict.id,
                                                   student_pk: map_dict.student_id,
                                                   studsubj_pk: map_dict.studsubj_id,
                                                   examperiod_pk: map_dict.examperiod};
                            upload_dict[fldName] = value_text;
                            UploadChanges(upload_dict, url_grade_upload);
                        }
                    }
                }
            }  // if (!permit_dict.crud_grade)
        }
    };  // HandleInputChange

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
                    alert(msg + '\n' + xhr.responseText);
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
/////////////////////////////////////////////

//========= DownloadGradeStatusAndIcons ============= PR2021-04-30
    function DownloadGradeStatusAndIcons() {
        console.log( " ==== DownloadGradeStatusAndIcons ====");

        const url_str = url_download_grade_icons;
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
console.log("--------------- grade_note_icon_rows", response.grade_note_icon_rows)
//console.log("grade_note_icon_rows", response.grade_note_icon_rows)
                    const tblName = "grades";
                    const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                    RefreshDataMap(tblName, field_names, response.grade_note_icon_rows, grade_map, false);  // false = don't show green ok background
                }
               if ("grade_stat_icon_rows" in response) {
console.log("???????????????? grade_stat_icon_rows", response.grade_stat_icon_rows)
                    const tblName = "grades";
                    const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                    RefreshDataMap(tblName, field_names, response.grade_stat_icon_rows, grade_map, false);  // false = don't show green ok background
                }
            },
            error: function (xhr, msg) {
// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                console.log(msg + '\n' + xhr.responseText);
                alert(msg + '\n' + xhr.responseText);
            }
        });

     } // DownloadGradeStatusAndIcons

/////////////////////////////////////////////
//========= UploadToggle  ============= PR2020-07-31  PR2021-01-14
    function UploadToggle(el_input) {
        console.log( " ==== UploadToggle ====");
        //console.log( "usergroups", usergroups);
        // only called by field 'se_status', 'pe_status', 'ce_status'
        // mode = 'approve_submit' or ''approve_reset'
        mod_dict = {};
        if(permit_dict.approve_grade){
            const tblRow = get_tablerow_selected(el_input);
            if(tblRow){

                // get_statusindex_of_user returns index of auth user, returns 0 when user has none or multiple auth usergroups
                // gives err messages when multiple found.
                const status_index = get_statusindex_of_user();

                // if(status_index){
                if(true){
                    const map_id = tblRow.id
                    const map_dict = get_mapdict_from_datamap_by_id(grade_map, map_id);
        console.log( "map_dict", map_dict);
                    if(!isEmpty(map_dict)){
                        const tblName = "grade";
                        const fldName = get_attr_from_el(el_input, "data-field");
        console.log( "fldName", fldName);
                        if(fldName in map_dict ){
                            const examtype = fldName.substring(0,2);
                            const published_field = examtype + "_published"
                            const published_pk = (map_dict[published_field]) ? map_dict[published_field] : null;
        console.log( "published_pk", published_pk);
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

        console.log( "status_sum", status_sum);
        console.log( "status_bool_at_index", status_bool_at_index);
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

        console.log( "new_status_sum", new_status_sum);
        console.log( "get_status_class(new_status_sum)", get_status_class(new_status_sum));
                    // ---  upload changes
                                        // value of 'mode' determines if status is set to 'approved' or 'not
                                        // instead of using value of new_status_bool_at_index,
                                        const mode = (new_status_bool_at_index) ? "approve_submit" : "approve_reset"
                                        const upload_dict = { table: tblName,
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
        }  // if(permit_dict.approve_grade){
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

                    if ("updated_student_rows" in response) {
                        const el_MSTUD_loader = document.getElementById("id_MSTUD_loader");
                        if(el_MSTUD_loader){ el_MSTUD_loader.classList.add(cls_visible_hide)};
                        const tblName = "student";
                        const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                        RefreshDataMap(tblName, field_names, response.updated_student_rows, student_map, true);  // false = show green ok background
                    };
                    $("#id_mod_student").modal("hide");

                    if ("err_html" in response) {
                        b_show_mod_message(response.err_html)

                    }
                    if ("msg_dict" in response && !isEmpty(response.msg_dict)) {
                        //if (mod_dict.mode && ["submit_test", "approve"].indexOf(mod_dict.mode) > -1){
                            MAG_UpdateFromResponse (response.msg_dict);
                        //}
                    }
                    if ("updated_grade_rows" in response) {
                        const tblName = "grades";
                        const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                        RefreshDataMap(tblName, field_names, response.updated_grade_rows, grade_map, true);  // false = show green ok background
                    }
                    if ("updated_published_rows" in response) {
                        const tblName = "published";
                        const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                        RefreshDataMap(tblName, field_names, response.updated_published_rows, published_map, true);  // false = show green ok background
                    }

                    if ("studentsubjectnote_rows" in response) {
                        b_fill_datamap(studentsubjectnote_map, response.studentsubjectnote_rows)
                        ModNote_FillNotes(response.studentsubjectnote_rows);
                    };

                },  // success: function (response) {
                error: function (xhr, msg) {
                    // ---  hide loader
                    el_loader.classList.add(cls_visible_hide)
                    console.log(msg + '\n' + xhr.responseText);
                    alert(msg + '\n' + xhr.responseText);
                }  // error: function (xhr, msg) {
            });  // $.ajax({
        }  //  if(!!row_upload)
    };  // UploadChanges

// +++++++++++++++++ UPDATE +++++++++++++++++++++++++++++++++++++++++++



// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2020-08-03
    function ModConfirmOpen(mode, el_input) {
        console.log(" -----  ModConfirmOpen   ----")
        // values of mode are : "delete", "inactive" or "resend_activation_email", "permission_sysadm"

        if(may_edit){


    // ---  get selected_pk
            let tblName = null, selected_pk = null;
            // tblRow is undefined when clicked on delete btn in submenu btn or form (no inactive btn)
            const tblRow = get_tablerow_selected(el_input);
            if(tblRow){
                tblName = get_attr_from_el(tblRow, "data-table")
                selected_pk = get_attr_from_el(tblRow, "data-pk")
            } else {
                tblName = get_tblName_from_selectedBtn()
                selected_pk = (tblName === "student") ? setting_dict.sel_student_pk :
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
        let close_modal = !may_edit;

        if(may_edit){
            let tblRow = document.getElementById(mod_dict.mapid);

    // ---  when delete: make tblRow red, before uploading
            if (tblRow && mod_dict.mode === "delete"){
                ShowClassWithTimeout(tblRow, "tsa_tr_error");
            }

            if(["delete", 'resend_activation_email'].indexOf(mod_dict.mode) > -1) {
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

//=========  ModMessageClose  ================ PR2020-12-20
    function ModMessageClose() {
        console.log(" --- ModMessageClose --- ");
        //console.log("mod_dict: ", mod_dict);

    }  // ModMessageClose

//>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

//========= MOD APPROVE GRADE ====================================
    function MAG_Open (mode ) {
        console.log("===  MAG_Open  =====") ;
        console.log("mode", mode) ;
        console.log("permit_dict", permit_dict) ;
        // mode = 'approve' or 'submit

        mod_MAG_dict = {}

        const is_approve_mode = (mode === "approve");
        const is_submit_mode = (mode === "submit");

        // get_statusindex_of_user returns index of auth user, returns 0 when user has none or multiple auth usergroups
        // gives err messages when multiple found.
        const status_index = get_statusindex_of_user();
        if (permit_dict.approve_grade || permit_dict.submit_grade) {
            if(status_index){
                // modes are 'approve' 'submit_test' 'submit_submit'
                mod_MAG_dict = {mode: mode,
                            step: 0,
                            is_approve_mode: is_approve_mode,
                            is_submit_mode: is_submit_mode,
                            status_index: status_index,
                            may_test: true,
                            test_is_ok: false,
                            submit_is_ok: false,
                            is_reset: false}
                document.getElementById("id_MAG_header").innerText = (is_approve_mode) ? loc.Approve_grades : loc.Submit_Ex2A_form;
                document.getElementById("id_MAG_subheader").innerText = (is_approve_mode) ? loc.MAG_info.subheader_approve : loc.MAG_info.subheader_submit;

                el_MAG_examperiod.innerText = setting_dict.sel_examperiod_caption
                // sel_examtype = "se", "pe", "ce", "re2", "re3", "exm"
                let examtype_caption = null;
                for (let i = 0, dict; dict = loc.options_examtype[i]; i++) {
                    if(dict.value === setting_dict.sel_examtype) {
                        examtype_caption = dict.caption;
                        break;
                    }
                }
                el_MAG_examtype.innerText = examtype_caption

                add_or_remove_class(el_MAG_level_container, cls_hide, !setting_dict.sel_dep_level_req)
                el_MAG_level.innerText = (setting_dict.sel_level_abbrev) ? setting_dict.sel_level_abbrev : null;

                let subject_text = null;
                if(setting_dict.sel_subject_pk){
                    const dict = get_mapdict_from_datamap_by_tblName_pk(subject_map, "subject", setting_dict.sel_subject_pk);
                    subject_text =  (dict.name) ? dict.name : "---"
                } else {
                    subject_text = "<" + loc.All_subjects + ">";
                }
                el_MAG_subject.innerText = subject_text;

                const auth_by = (permit_dict.usergroup_list && permit_dict.usergroup_list.includes("auth1")) ? loc.President :
                                (permit_dict.usergroup_list && permit_dict.usergroup_list.includes("auth2")) ? loc.Secretary :
                                (permit_dict.usergroup_list && permit_dict.usergroup_list.includes("auth3")) ? loc.Commissioner : null;

                const caption = (is_submit_mode) ? loc.Submitted_by : loc.Approved_by;
                document.getElementById("id_MAG_approved_by_label").innerText = caption + ":";
                document.getElementById("id_MAG_approved_by").innerText = auth_by
                document.getElementById("id_MAG_approved_name").innerText = setting_dict.requsr_name

    // ---  show info and hide loader
                add_or_remove_class(el_MAG_info_container, cls_hide, false)
                // PR2021-01-21 debug 'display_hide' not working when class 'image_container' is in same div
                add_or_remove_class(el_MAG_loader, cls_hide, true);

    // --- reset ok button
                MAG_SetBtnSaveDeleteCancel();

                $("#id_mod_approve_grade").modal({backdrop: true});

            }  // if(status_index)
        }  // if (permit_dict.approve_grade || permit_dict.submit_grade)
    }  // MAG_Open

//=========  MAG_Save  ================
    function MAG_Save (mode) {
        //console.log("===  MAG_Save  =====") ;
        //console.log("mod_MAG_dict.mode", mod_MAG_dict.mode) ;

        if (permit_dict.approve_grade || permit_dict.submit_grade) {

            mod_MAG_dict.is_reset = (mode === "delete");

            //  upload_modes are: 'approve_test', 'approve_submit', 'approve_reset', 'submit_test', 'submit_submit'
            let upload_mode = null;
            if (mod_MAG_dict.is_approve_mode){
                if (mod_MAG_dict.is_reset) {
                    upload_mode = "approve_reset";
                } else {
                    upload_mode = (mod_MAG_dict.test_is_ok) ? "approve_submit" : "approve_test";
                }
            } else if (mod_MAG_dict.is_submit_mode){
                upload_mode = (mod_MAG_dict.test_is_ok) ? "submit_submit" : "submit_test";
            };

    // ---  show loader
            add_or_remove_class(el_MAG_loader, cls_hide, false)

    // ---  hide info box and msg box
            show_hide_selected_elements_byClass("tab_show", "-", el_mod_approve_grade);

    // ---  hide delete btn
            add_or_remove_class(el_MAG_btn_delete, cls_hide, true);

    // ---  upload changes
            const upload_dict = { table: "grade",
                                   subject_pk: setting_dict.sel_subject_pk,
                                   mode: upload_mode,
                                   status_index: mod_MAG_dict.status_index,
                                   now_arr: get_now_arr()  // only for timestamp on filename saved Ex-form
                                   }
            //console.log("upload_dict", upload_dict);
            UploadChanges(upload_dict, url_grade_approve);

        }  // if (permit_dict.approve_grade || permit_dict.submit_grade)
// hide modal
        //$("#id_mod_approve_grade").modal("hide");
    };  // MAG_Save

//=========  MAG_UpdateFromResponse  ================ PR2021-02-08
    function MAG_UpdateFromResponse (msg_dict) {
        console.log("===  MAG_UpdateFromResponse  =====") ;
        //console.log("msg_dict", msg_dict);
        //console.log("mod_MAG_dict", mod_MAG_dict);

        mod_MAG_dict.step += 1,

// ---  hide loader
        add_or_remove_class(el_MAG_loader, cls_hide, true);
        let msg_01_txt = null,  msg_02_txt = null, msg_03_txt = null, msg_04_txt = null;

// make message container green when grades can be published, red otherwise
        // msg_dict.saved > 0 when grades are approved or published

        mod_MAG_dict.may_test = false;
        mod_MAG_dict.test_is_ok = msg_dict.test_is_ok;
        mod_MAG_dict.has_already_approved_by_auth = (!!msg_dict.already_approved_by_auth)
        mod_MAG_dict.has_already_published = (!!msg_dict.already_published)
        mod_MAG_dict.has_saved = !!msg_dict.saved;
        mod_MAG_dict.submit_is_ok = !!msg_dict.now_saved;  // submit_is_ok when records are saved

       // const border_class = (mod_MAG_dict.test_is_ok) ? "border_bg_valid" : "border_bg_invalid";
        console.log("mod_MAG_dict.test_is_ok", mod_MAG_dict.test_is_ok) ;
        //const bg_class = (mod_MAG_dict.test_is_ok) ? "border_bg_valid" : "border_bg_invalid" // "border_bg_message"
        //el_MAG_msg_container.className = bg_class
        let bg_class_ok = (mod_MAG_dict.test_is_ok || mod_MAG_dict.has_saved )
        add_or_remove_class(el_MAG_msg_container, "border_bg_valid",bg_class_ok, "border_bg_invalid");

// hide ok button when not mod_MAG_dict.test_is_ok
        MAG_SetBtnSaveDeleteCancel ();

// create message in container
        el_MAG_msg_container.innerText = null

// --- create element with tag from field_tags

        const array = ["count_text", "skip_text", "already_published_text", "no_value_text", "auth_missing_text",
            "double_approved_text", "already_approved_by_auth_text", "saved_text"]
        for (let i = 0, el, key; key = array[i]; i++) {
            if(key in msg_dict) {
        console.log("key", key) ;
        console.log("msg_dict[key]", msg_dict[key]) ;
                el = document.createElement("p");
                el.innerText = msg_dict[key];
                el_MAG_msg_container.appendChild(el);
                if (key === "count_text") {
                    el.classList.add("pb-2")
                } else if (key === "saved_text") {
                    el.classList.add("pt-2")
                } else if (key === "skip_text") {
                } else {
                    el.classList.add("pl-4")
                }
            }
        }

       // msg_01_txt = "The selection contains " + msg_dict.count + " grades."
       // if (msg_dict.no_value){msg_02_txt = " -  " + msg_dict.no_value + " grades have no value. They will be skipped."}
       // if (msg_dict.auth_missing){msg_03_txt = " -  " + msg_dict.auth_missing + " grades are not completely authorized. They will be skipped"}
        //if (msg_dict.already_published){msg_03_txt = " -  " + msg_dict.already_published + " grades are already submitted.They will be skipped."}

// hide modal after submitting, only when is_approve_mode
        if(mod_MAG_dict.step === 2 && mod_MAG_dict.is_approve_mode){
            $("#id_mod_approve_grade").modal("hide");
        }

    };  // MAG_UpdateFromResponse

//=========  MAG_SetBtnSaveDeleteCancel  ================ PR2021-02-08
     function MAG_SetBtnSaveDeleteCancel() {
        console.log("===  MAG_SetBtnSaveDeleteCancel  =====") ;
//
        const is_approve_mode = mod_MAG_dict.is_approve_mode;
        const is_submit_mode = mod_MAG_dict.is_submit_mode;
        const is_reset = mod_MAG_dict.is_reset;

        const step = mod_MAG_dict.step;
        const may_test = mod_MAG_dict.may_test;
        const test_is_ok = mod_MAG_dict.test_is_ok;
        const submit_is_ok = mod_MAG_dict.submit_is_ok;

        const has_already_approved_by_auth = !!mod_MAG_dict.has_already_approved_by_auth;
        const has_already_published = !!mod_MAG_dict.has_already_published;
        const has_saved = !!mod_MAG_dict.has_saved;
/*
        console.log("mode", mod_MAG_dict.mode) ;
        console.log("is_approve_mode", is_approve_mode) ;
        console.log("is_submit_mode", is_submit_mode) ;
        console.log("is_reset", is_reset) ;

        console.log("may_test", may_test) ;
        console.log("test_is_ok", test_is_ok) ;
        console.log("submit_is_ok", submit_is_ok) ;

        console.log("has_already_approved_by_auth", has_already_approved_by_auth) ;
        console.log("has_already_published", has_already_published) ;
        console.log("has_saved", has_saved) ;
*/
// put info text in el_MAG_info_container, only on open modal
        let inner_html = "";
        if(!step){
            for (let i = 0, key, line; i < 3; i++) {
                key = ((mod_MAG_dict.is_approve_mode) ? "approve_" : "submit_") + i;
                inner_html += "<div><small>" + loc.MAG_info[key] + "</div></small>";
            }
        }
        el_MAG_info_container.innerHTML = inner_html

// ---  hide save button when not can_publish
        let show_save_btn = false;
        if (is_approve_mode){
            show_save_btn = (may_test || test_is_ok);
        } else {
            show_save_btn = (may_test || test_is_ok);
        }
        add_or_remove_class(el_MAG_btn_save, cls_hide, !show_save_btn);
        el_MAG_btn_save.innerText = (is_approve_mode && test_is_ok) ? loc.Approve_grades :
                                    (is_submit_mode && test_is_ok) ? loc.Submit_Ex2A_form : loc.Check_grades;
        let btn_text = (submit_is_ok || (!may_test && !test_is_ok) || (!submit_is_ok)) ? loc.Close : loc.Cancel;
        el_MAG_btn_cancel.innerText = btn_text;

// ---  show only the elements that are used in this tab
        let show_class = "tab_step_" + step;

        show_hide_selected_elements_byClass("tab_show", show_class, el_mod_approve_grade);

// ---  hide delete btn when reset or publish mode
        let show_delete_btn = false;
        if (is_approve_mode){
            if (has_already_approved_by_auth) {show_delete_btn = true}
        }
        //const show_delete_btn = (is_approve_mode && !is_reset && test_is_ok)
        add_or_remove_class(el_MAG_btn_delete, cls_hide, !show_delete_btn);

     } //  MAG_SetBtnSaveDeleteCancel

//========= MOD NOTE Open====================================
    function ModNote_Open (el_input) {
        console.log("===  ModNote_Open  =====") ;
        console.log("el_input", el_input) ;

    // get has_note from grade_map
        let grade_dict = get_itemdict_from_datamap_by_el(el_input, grade_map)
        const has_note = !!get_dict_value(grade_dict, ["note_status"])

// reset notes_container
        el_ModNote_notes_container.innerText = null;

// reset input_note
        el_ModNote_input_note.value = null;

// --- show input element for note, only when user has permit
        // TODO permit_dict.write_note_extern

        const has_permit_intern_extern = (permit_dict.write_note_intern || permit_dict.write_note_extern)
        let may_open_modnote = has_permit_intern_extern || (permit_dict.read_note && has_note);
        if(may_open_modnote){
            // only show input block when  has_permit_intern_extern
            add_or_remove_class(el_ModNote_input_container, cls_hide, !has_permit_intern_extern)
            // hide external note if no permit write_note_extern
            add_or_remove_class(el_ModNote_external, cls_hide, !permit_dict.write_note_extern)

            // hide 'x' option when not inspection
            const el_ModNote_memo_icon4 = document.getElementById("id_ModNote_memo_icon4")
            add_or_remove_class(el_ModNote_memo_icon4, cls_hide, !permit_dict.requsr_role_insp)

    // get tr_selected
            let tr_selected = get_tablerow_selected(el_input)

            if(!isEmpty(grade_dict)){
                let headertext = (grade_dict.fullname) ? grade_dict.fullname + "\n" : "";
                if(grade_dict.subj_code) { headertext += grade_dict.subj_name};
                el_ModNote_header.innerText = headertext;

        console.log("grade_dict", grade_dict) ;
                mod_note_dict.studsubj_pk = grade_dict.studsubj_id
                mod_note_dict.examperiod = grade_dict.examperiod

                ModNote_SetInternalExternal("internal");

    // download existing studentsubjectnote_rows of this studsubj
                // will be filled in ModNote_FillNotes

    // show loader
            const el_ModNote_loader = document.getElementById("id_ModNote_loader");
            add_or_remove_class(el_ModNote_loader, cls_hide, false);
                const upload_dict = {studsubj_pk: grade_dict.studsubj_id};
                UploadChanges(upload_dict, url_studentsubjectnote_download)

                if (el_input){ setTimeout(function (){ el_ModNote_input_note.focus() }, 50)};

    // get info from grade_map
                $("#id_mod_note").modal({backdrop: true});
            }
        }  // if(permit_dict.read_note)
    }  // ModNote_Open

//========= ModNote_Save============== PR2020-10-15
    function ModNote_Save () {
        console.log("===  ModNote_Save  =====");
        const filename = document.getElementById("id_ModNote_filedialog").value;

        if(permit_dict.write_note_intern || permit_dict.write_note_extern){
            const note = el_ModNote_input_note.value;
            const note_status = (!mod_note_dict.is_internal) ? "1_" + mod_note_dict.sel_icon : "0_1";

// get attachment info
            const file = document.getElementById("id_ModNote_filedialog").files[0];  // file from input
            const file_type = (file) ? file.type : null;
            const file_name = (file) ? file.name : null;
            const file_size = (file) ? file.size : 0;

           // may check size or type here with
            // ---  upload changes
            const upload_dict = { table: mod_note_dict.table,
                                   create: true,
                                   studsubj_pk: mod_note_dict.studsubj_pk,
                                   examperiod: mod_note_dict.examperiod,
                                   note: note,
                                   note_status: note_status,
                                   is_internal_note: mod_note_dict.is_internal,
                                   file_type: file_type,
                                   file_name: file_name,
                                   file_size: file_size
                                   };
            const upload_json = JSON.stringify (upload_dict)

            if(note || file_size){
                const upload = new Upload(upload_json, file, url_studentsubjectnote_upload);
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
        console.log( "attachment type",  this.getType())
        console.log( "attachment name", this.getName())

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
                    RefreshDataMap(tblName, field_names, response.grade_note_icon_rows, grade_map, false);  // false = don't show green ok background
                }

            },  // success: function (response) {


            error: function (xhr, msg) {
                // ---  hide loader
                el_loader.classList.add(cls_visible_hide)
                console.log(msg + '\n' + xhr.responseText);
                alert(msg + '\n' + xhr.responseText);
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
    console.log("progressHandling", event)
        let percent = 0;
        const position = event.loaded || event.position;
        const total = event.total;
        const progress_bar_id = "#progress-wrp";
        if (event.lengthComputable) {
            percent = Math.ceil(position / total * 100);
        }
    console.log("percent", percent)
        // update progressbars classes so it fits your code
        $(progress_bar_id + " .progress-bar").css("width", +percent + "%");
        $(progress_bar_id + " .status").text(percent + "%");
    };

//?????????????????????????????????????????????????????????????????


//========= ModNote_SetInternalExternal============== PR2021-01-17
    function ModNote_SetInternalExternal (mode, el_btn) {
        console.log("===  ModNote_SetInternalExternal  =====") ;
        console.log("mode", mode) ;
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

        console.log("mod_note_dict.sel_icon", mod_note_dict.sel_icon) ;
        console.log("mod_note_dict.is_internal", mod_note_dict.is_internal)

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

        console.log("mod_note_dict", mod_note_dict) ;
    }  // ModNote_SetInternalExternal

//========= ModNote_FillNotes============== PR2020-10-15
    function ModNote_FillNotes (note_rows) {
        console.log("===  ModNote_FillNotes  =====") ;
        console.log("note_rows", note_rows) ;
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
// +++++++++++++++++ REFRESH DATA MAP ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataMap  ================ PR2020-08-16 PR2020-09-30, PR2021-05-01
    function RefreshDataMap(tblName, field_names, data_rows, data_map, show_ok) {
        console.log(" --- RefreshDataMap  ---");
        console.log("data_rows", data_rows);
        if (data_rows) {
            const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
            for (let i = 0, update_dict; update_dict = data_rows[i]; i++) {
                RefreshDatamapItem(field_names, update_dict, data_map, show_ok);
            }
            console.log("data_map", data_map);
        }
    }  //  RefreshDataMap

//=========  RefreshDatamapItem  ================ PR2020-08-16 PR2020-09-30
    function RefreshDatamapItem(field_names, update_dict, data_map, show_ok) {
        //console.log(" --- RefreshDatamapItem  ---");
        //console.log("update_dict", update_dict);
        if(!isEmpty(update_dict)){

// ---  update or add update_dict in subject_map
            let updated_columns = [];
    // get existing map_item
            const tblName = update_dict.table;
            const map_id = update_dict.mapid;
            let tblRow = document.getElementById(map_id);
            //console.log("map_id", map_id);

            const is_deleted = get_dict_value(update_dict, ["deleted"], false)
            const is_created = get_dict_value(update_dict, ["created"], false)
            const err_dict = (update_dict.error) ? update_dict.error : null;
            //console.log("err_dict", err_dict);

// ++++ created ++++
            if(is_created){
    // ---  insert new item
                data_map.set(map_id, update_dict);
                updated_columns.push("created")
    // ---  create row in table., insert in alphabetical order
                let order_by = (update_dict.fullname) ? update_dict.fullname.toLowerCase() : ""
                const row_index = t_get_rowindex_by_sortby(tblBody_datatable, order_by)
                tblRow = CreateTblRow(map_id, update_dict, row_index)
    // ---  scrollIntoView,
                if(tblRow && show_ok){
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

/* old version
                const old_map_dict = (map_id) ? data_map.get(map_id) : null;
                //console.log("old_map_dict", old_map_dict);
    // ---  check which fields are updated, add to list 'updated_columns'
                if(!isEmpty(old_map_dict) && field_names){
                    // skip first column (is margin)
                    for (let i = 1, col_field, old_value, new_value; col_field = field_names[i]; i++) {
                        if (col_field in old_map_dict && col_field in update_dict){
                            old_value = old_map_dict[col_field];
                            new_value = update_dict[col_field];
                //console.log("old_value", old_value);
                //console.log("new_value", new_value);
                            if (old_value !== new_value) {
                                updated_columns.push(col_field)
                            }
                        }
                    }}
    // ---  update item
                data_map.set(map_id, update_dict)
*/
// new version PR2021-05-01 : first fill updated_columns, if any: deepcopy_dict and update data_map
                if(map_id){
                    const old_map_dict = data_map.get(map_id);
                    if(!isEmpty(old_map_dict)){
                        for (const [key, new_value] of Object.entries(update_dict)) {
                            if (key in old_map_dict){
                                if (new_value !== old_map_dict[key]) {
                                    updated_columns.push(key)
                        }}};
    // ---  put updated map_dict back in data_map
                        if(updated_columns.length){
// console.log("updated_columns", updated_columns);
                            const map_dict = deepcopy_dict(data_map.get(map_id));
                            for (let i = 0, key; key = updated_columns[i]; i++) {
                                map_dict[key] = update_dict[key];
                            }
                            data_map.set(map_id, map_dict);
                        }
                    }
                }
            }

    // ---  make update
            // note: when updated_columns is empty, then updated_columns is still true.
            // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
            if(tblRow && (updated_columns.length || err_dict)){
    // ---  make entire row green when row is created
                if(updated_columns.includes("created")){
                    if(show_ok){ShowOkElement(tblRow)};
                } else {
    // loop through cells of row
                    for (let i = 1, el_fldName, td, el; td = tblRow.cells[i]; i++) {
                        if (td){
                            el = td.children[0];
                            if(el){
                                el_fldName = get_attr_from_el(el, "data-field")

            //console.log("el_fldName", el_fldName);
                                if(err_dict && el_fldName in err_dict){
                                    //ShowOkElement(el);
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
                                    if(show_ok){ShowOkElement(el)};
                                }
                            }
                        }
             }}}
            //console.log("updated_columns", updated_columns);
        }
    }  // RefreshDatamapItem

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


//========= HandleFilterToggle  =============== PR2020-07-21 PR2020-09-14 PR2021-03-23
    function HandleFilterToggle(el_input) {
        console.log( "===== HandleFilterToggle  ========= ");

    // - get col_index and filter_tag from  el_input
        // PR2021-05-30 debug: use cellIndex instead of attribute data-colindex,
        // because data-colindex goes wrong with hidden columns
        // was:  const col_index = get_attr_from_el(el_input, "data-colindex")
        const col_index = el.parentNode.cellIndex;

    // - get filter_tag from  el_input
        const filter_tag = get_attr_from_el(el_input, "data-filtertag")
        const field_name = get_attr_from_el(el_input, "data-field")
        console.log( "col_index", col_index);
        console.log( "filter_tag", filter_tag);
        console.log( "field_name", field_name);

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
        }

    // - put new filter value in filter_dict
        filter_dict[col_index] = [filter_tag, new_value]
        console.log( "filter_dict", filter_dict);
        el_input.className = icon_class;
        Filter_TableRows(tblBody_datatable);

    };  // HandleFilterToggle

//========= HandleFilterField  ====================================
    function HandleFilterField(el, col_index, event) {
       //console.log( "===== HandleFilterField  ========= ");
        // skip filter if filter value has not changed, update variable filter_text

        //console.log( "el_key", el_key);
        //console.log( "col_index", col_index);
        const filter_tag = get_attr_from_el(el, "data-filtertag")
        //console.log( "filter_tag", filter_tag);

// --- get filter tblRow and tblBody
        const tblRow = get_tablerow_selected(el);
        const tblName = get_attr_from_el(tblRow, "data-table")

// --- reset filter row when clicked on 'Escape'
        const skip_filter = t_SetExtendedFilterDict(el, col_index, filter_dict, event.key);

         if ( ["toggle", "inactive"].indexOf(filter_tag) > -1) {
// ---  toggle filter_checked
            let filter_checked = (col_index in filter_dict) ? filter_dict[col_index] : 0;
    // ---  change icon
            let el_icon = el.children[0];
            if(el_icon){
                add_or_remove_class(el_icon, "tickmark_0_0", !filter_checked)
                if(filter_tag === "toggle"){
                    add_or_remove_class(el_icon, "tickmark_0_1", filter_checked === -1)
                    add_or_remove_class(el_icon, "tickmark_0_2", filter_checked === 1)
                } else  if(filter_tag === "inactive"){
                    add_or_remove_class(el_icon, "inactive_0_2", filter_checked === -1)
                    add_or_remove_class(el_icon, "inactive_1_3", filter_checked === 1)
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


        Filter_TableRows(tblBody_datatable);
    }; // HandleFilterField

//========= Filter_TableRows  ==================================== PR2020-08-17
    function Filter_TableRows(tblBody) {
        console.log( "===== Filter_TableRows  ========= ");

        const tblName_settings = (selected_btn === "grade_published") ? "published" : "grades";
        const field_setting = field_settings[tblName_settings];
        const filter_tags = field_setting.filter_tags;

        for (let i = 0, tblRow, show_row; tblRow = tblBody_datatable.rows[i]; i++) {
            tblRow = tblBody_datatable.rows[i]
            show_row = t_ShowTableRowExtended(filter_dict, tblRow);
            add_or_remove_class(tblRow, cls_hide, !show_row)
        }
    }; // Filter_TableRows

//========= ShowTableRow  ==================================== PR2020-08-17
    function ShowTableRow(tblRow, filter_tags) {
        // only called by Filter_TableRows
        console.log( "===== ShowTableRow  ========= ");
        console.log( "filter_dict", filter_dict);

        let hide_row = false;
        if (tblRow){
// show all rows if filter_name = ""
            if (!isEmpty(filter_dict)){
                for (let i = 1, el_fldName, el; el = tblRow.cells[i]; i++) {
                    const filter_text = filter_dict[i];
                    const filter_tag = filter_tags[i];

        console.log( "filter_text", filter_text);
        console.log( "filter_tag", filter_tag);
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
                                } else if(el_value.indexOf(filter_text) === -1){
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

        setting_dict.sel_student_pk = null;
        setting_dict.sel_student_name = null;

        filter_dict = {};
        filter_mod_employee = false;

        Filter_TableRows(tblBody_datatable);

        let filterRow = tblHead_datatable.rows[1];
        if(!!filterRow){
            for (let j = 0, cell, el; cell = filterRow.cells[j]; j++) {
                if(cell){
                    el = cell.children[0];
                    if(el){
                        const filter_tag = get_attr_from_el(el, "data-filtertag")
                        if(el.tag === "INPUT"){
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

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL SELECT EXAMYEAR OR DEPARTMENT ++++++++++++++++++++
// functions are in table.js, except for MSED_Response

//=========  MSED_Response  ================ PR2020-12-18  PR2021-05-10
    function MSED_Response(new_setting) {
        //console.log( "===== MSED_Response ========= ");

// ---  upload new selected_pk
// also retrieve the tables that have been changed because of the change in examyear / dep
        const datalist_request = {
                setting: new_setting,
                level_rows: {get: true},
                sector_rows: {get: true},
                student_rows: {get: true},
                studentsubject_rows: {get: true},
                grade_rows: {get: true}
            };
        DatalistDownload(datalist_request);

    }  // MSED_Response

//=========  MSSSS_Response  ================ PR2021-01-23 PR2021-02-05
    function MSSSS_Response(tblName, selected_pk, selected_code, selected_name) {
        console.log( "===== MSSSS_Response ========= ");
        console.log( "selected_pk", selected_pk);
        //console.log( "selected_code", selected_code);
        console.log( "selected_name", selected_name);

    // ---  upload new setting
        if(selected_pk === -1) { selected_pk = null};
        const upload_dict = {};
        const selected_pk_dict = {sel_student_pk: selected_pk};
        selected_pk_dict["sel_" + tblName + "_pk"] = selected_pk;
        let new_selected_btn = null;
        if (tblName === "school") {
// ---  put new selected_pk in setting_dict
            setting_dict.sel_schoolbase_pk = selected_pk;
    // reset selected student and subject is selected, in setting_dict and upload_dict
            if(selected_pk){
                selected_pk_dict.sel_student_pk = null;
                setting_dict.sel_student_pk = null;
                setting_dict.sel_student_name = null;

                selected_pk_dict.sel_subject_pk = null;
                setting_dict.sel_subject_pk = null;

                new_selected_btn = "grade_by_subject";
            }

        } else if (tblName === "subject") {
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
            setting_dict.sel_student_name = selected_name;
    // reset selected subject when student is selected, in setting_dict and upload_dict
            if(selected_pk){
                selected_pk_dict.sel_subject_pk = null;
                setting_dict.sel_subject_pk = null;
                new_selected_btn = "grade_by_student";
            }
        }

        if (tblName === "school") {
// ---  upload new setting and refresh page
            let datalist_request = {setting: {page: "page_grade", sel_schoolbase_pk: selected_pk}};
            DatalistDownload(datalist_request);
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
    }  // MSSSS_Response

//========= MSSSS_display_in_sbr  ====================================
    function MSSSS_display_in_sbr() {
        //console.log( "===== MSSSS_display_in_sbr  ========= ");
        //console.log( "setting_dict ", setting_dict);

// ---  put subject in el_SBR_select_subject and el_MAG_subject
        let subject_text = "";
        const sel_subject_pk = (setting_dict.sel_subject_pk) ? setting_dict.sel_subject_pk : null;
        console.log( "sel_subject_pk ", sel_subject_pk);
        if(sel_subject_pk){
            const dict = get_mapdict_from_datamap_by_tblName_pk(subject_map, "subject", sel_subject_pk);
            subject_text =  (dict.name) ? dict.name : "---"
        } else {
            subject_text = "<" + loc.All_subjects + ">";
        }
        setting_dict.sel_subject_txt = (subject_text) ? subject_text : null;

        el_SBR_select_subject.value = subject_text;
        el_MAG_subject.innerText = subject_text
        document.getElementById("id_SBR_container_subject").classList.remove(cls_hide);

// ---  put student_text in el_SBR_select_subject and el_MAG_subject
        let student_name = "";
        const sel_student_pk = (setting_dict.sel_student_pk) ? setting_dict.sel_student_pk : null;
        if(setting_dict.sel_student_pk){
            const dict = get_mapdict_from_datamap_by_tblName_pk(student_map, "student", setting_dict.sel_student_pk);
            student_name = (dict.fullname) ? dict.fullname : "---"
            setting_dict.sel_student_name = student_name;
        } else {
            student_name = "<" + loc.All_candidates + ">";
            setting_dict.sel_student_name = null;
        }
        el_SBR_select_student.value = student_name;
        document.getElementById("id_SBR_container_student").classList.remove(cls_hide);

    }; // MSSSS_display_in_sbr

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


//>>>>>>>>>> NOT IN USE YET >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
//========= ModalStatusOpen====================================
    function ModalStatusOpen (el_input) {
       console.log("===  ModalStatusOpen  =====") ;
       console.log("el_input", el_input) ;
        // PERMISSIONS: only hrman can unlock shifts, supervisor can only block shifts PR2020-08-05
        // TODO correct
       // return false
        mod_status_dict = {};
        let permit_lock_rows = true;
        let permit_unlock_rows = true;
// get tr_selected, fldName and grade_dict
        let tr_selected = get_tablerow_selected(el_input)
        const fldName = get_attr_from_el(el_input, "data-field");
        console.log("fldName", fldName) ;

// get status from field status, not from confirm start/end
        let grade_dict = get_itemdict_from_datamap_by_el(el_input, grade_map)
        console.log("grade_dict", grade_dict) ;

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

            let msg01_text = null;
            if(has_no_order){
                msg01_text = loc.You_must_first_select + loc.an_order + loc.select_before_confirm_shift;
            } else if(has_no_employee && !is_fldName_status){
                msg01_text = loc.You_must_first_select + loc.an_employee + loc.select_before_confirm_shift;
            } else if(has_overlap && !is_fldName_status){
                msg01_text = loc.You_cannot_confirm_overlapping_shift;
            } else if(has_no_time && !is_fldName_status){
                msg01_text = loc.You_must_first_enter +
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
                } else if (!msg01_text){
                    show_confirm_box = true;
                }
            }
            if(show_confirm_box) {
                el_mod_status_btn_save.innerText = btn_save_text;
    // ---  show modal
                $("#id_mod_status").modal({backdrop: true});
            } else {

// ---  show modal confirm with message 'First select employee'
                document.getElementById("id_confirm_header").innerText = loc.Confirm + " " + loc.Shift.toLowerCase();
                document.getElementById("id_confirm_msg01").innerText = msg01_text;
                document.getElementById("id_confirm_msg02").innerText = null;
                document.getElementById("id_confirm_msg03").innerText = null;

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
                    //console.log(msg + '\n' + xhr.responseText);
                    alert(msg + '\n' + xhr.responseText);
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
        console.log(" --- ValidateGrade ---")
        console.log("fldName", fldName, "value", value)
        console.log("dict", dict)

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
            if( (dict.se_locked && fldName === "segrade") ||
                (dict.sr_locked && fldName === "srgrade") ||
                (dict.pe_locked && fldName in ["pescore", "pegrade"]) ||
                (dict.ce_locked && fldName in ["cescore", "cegrade"]) ) {
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
                    if (!dict.weight_se) {
                        msg_html = err_list.weightse_is_zero+ "<br>" + err_list.cannot_enter_grade;
                    }
                } else if (["pescore", "cescore", "pegrade", "cegrade"].indexOf(fldName) > -1){
                    if (!dict.weight_ce) {
                        msg_html = err_list.weightce_is_zero + "<br>" + ( (is_score) ? err_list.cannot_enter_score : err_list.cannot_enter_grade )
                    }
                }
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

        console.log("output_text", output_text)
        console.log("msg_html", msg_html)
       return [output_text, msg_html]
    }  // ValidateGrade
////////////////////////////////////////////////


//========= GetNumberFromInputGrade  =============== PR2020-12-16
    function GetNumberFromInputGrade(loc, input_value){
        console.log(" --- GetNumberFromInputGrade ---")
        console.log("input_value", input_value)
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
            console.log("input_number", input_number)

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
        console.log("output_text", output_text)
        console.log("msg_err", msg_err)
        return [output_text, msg_err]
    }  // GetNumberFromInputGrade


//========= get_statusindex_of_user  ======== // PR2021-03-26
    function get_statusindex_of_user(){
        // function returns status_index of auth user, returns 0 when user has none or multiple auth usergroups
        // gives err messages when multiple found.
        // STATUS_01_AUTH1 = 2,  STATUS_02_AUTH2 = 4, STATUS_03_AUTH3 = 8
        let status_index = 0;
        const usrgrp = {auth1: false, auth2: false, auth3: false};
            const perm_auth1 = (permit_dict.usergroup_list && permit_dict.usergroup_list.includes("auth1"));
            const perm_auth2 = (permit_dict.usergroup_list && permit_dict.usergroup_list.includes("auth2"));
            const perm_auth3 = (permit_dict.usergroup_list && permit_dict.usergroup_list.includes("auth3"));

            if(!perm_auth1 && !perm_auth2 && !perm_auth3){
                // skip if user has no auth usergroup
            } else if(perm_auth1 + perm_auth2 + perm_auth3 > 1){
    // show msg error if user has multiple auth usergroups
                const functions = (perm_auth1 && perm_auth2 && perm_auth3) ? loc.President + ", " + loc.Secretary + loc.and + loc.Commissioner :
                                  (perm_auth1 && perm_auth2) ? loc.President + loc.and + loc.Secretary :
                                  (perm_auth1 && perm_auth3) ? loc.President + loc.and + loc.Commissioner :
                                  (perm_auth2 && perm_auth3) ? loc.Secretary + loc.and + loc.Commissioner : "";

                const msg_html = loc.approve_err_list.You_have_functions + functions + ". " + "<br>" +
                            loc.approve_err_list.Only_1_allowed + "<br>" + loc.approve_err_list.cannot_approve
                b_show_mod_message(msg_html);

            } else if(perm_auth1){
                status_index = 1;
            } else if(perm_auth2){
                status_index = 2;
            } else if(perm_auth3){
                status_index = 3;
            }
    return status_index;
    }  // get_statusindex_of_user

//========= get_tblName_from_selectedBtn  ======== // PR2021-01-22
    function get_tblName_from_selectedBtn() {
        const tblName = (selected_btn === "grade_published") ? "published" : "grades";
        return tblName;
    }
//========= get_datamap_from_tblName  ========  // PR2021-01-22
    function get_datamap_from_tblName(tblName) {
        const data_map = (tblName === "grades") ? grade_map :
                         (tblName === "published") ? published_map : null;
        return data_map;
    }



})  // document.addEventListener('DOMContentLoaded', function()