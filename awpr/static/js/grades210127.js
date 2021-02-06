// PR2020-09-29 added
document.addEventListener('DOMContentLoaded', function() {
    "use strict";

console.log("document.addEventListener students" )
    // <PERMIT> PR220-10-02
    //  - can view page: only 'role_school', 'role_insp', 'role_admin', 'role_system'
    //  - can add/delete/edit only 'role_admin', 'role_system' plus 'perm_edit'
    //  roles are:   'role_student', 'role_teacher', 'role_school', 'role_insp', 'role_admin', 'role_system'
    //  permits are: 'perm_read', 'perm_edit', 'perm_auth1', 'perm_auth2', 'perm_docs', 'perm_admin', 'perm_system'

// ---  check if user has permit to view this page. If not: el_loader does not exist PR2020-10-02
    let el_loader = document.getElementById("id_loader");
    const has_view_permit = (!!el_loader);
    // has_permit_edit gets value after downloading settings
    let has_permit_edit = false;
    let has_permit_select_school = false;

    const cls_hide = "display_hide";
    const cls_hover = "tr_hover";
    const cls_visible_hide = "visibility_hide";
    const cls_selected = "tsa_tr_selected";
    const cls_bc_transparent = "tsa_bc_transparent";

// ---  id of selected customer and selected order
    let selected_btn = null;
    let setting_dict = {};

    let selected_student_pk = null;
    let selected_subject_pk = null;
    let selected_examtype = null; // "se", "pe", "ce", "re2", "re3", "exm"

    let loc = {};  // locale_dict
    let mod_dict = {};
    let mod_MSTUD_dict = {};
    let mod_MSSS_dict = {};
    let mod_MAG_dict = {};
    let mod_status_dict = {};

    let time_stamp = null; // used in mod add user

    let user_list = [];
    let examyear_map = new Map();
    let school_map = new Map();
    let department_map = new Map();
    let student_map = new Map();
    let subject_map = new Map();
    let grade_map = new Map()
    let published_map = new Map()
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
    const url_grade_download_ex2a = get_attr_from_el(el_data, "data-grade_download_ex2a_url");

    const url_studentsubjectnote_upload = get_attr_from_el(el_data, "data-studentsubjectnote_upload_url");

// --- get field_settings
    const columns_shown = {select: true, examnumber: true, fullname: true, subj_code: true, subj_name: true,
                           pescore: true, cescore: true,
                           segrade: true, se_status: true,
                           pegrade: true, pe_status: true,
                           cegrade: true, ce_status: true,
                           pecegrade: true, finalgrade: true, hasnote: true,
                            // in table published:
                           name: true, examperiod: true, examtype: true, datepublished: true, filename: true

                           }
    const field_settings = {
        grades: { field_caption: ["", "Ex_nr", "Candidate", "Abbreviation", "Subject",
                                  "SE_grade_twolines", "",
                                  "PE_score_twolines", "PE_grade_twolines", "",
                                  "CE_score_twolines", "CE_grade_twolines", "",
                                  "PECE_grade_twolines", "Final_grade_twolines", ""],
                    field_names: ["select", "examnumber", "fullname",  "subj_code", "subj_name",
                                  "segrade", "se_status",
                                  "pescore", "pegrade", "pe_status",
                                  "cescore", "cegrade","ce_status",
                                  "pecegrade", "finalgrade", "hasnote"],
                    field_tags: ["div", "div", "div", "div", "div",
                                "input", "div",
                                "input", "input", "div",
                                "input","input","div",
                                "div", "div", "div"],
                    filter_tags: ["text", "text","text", "text", "text",
                                 "text", "text",
                                  "text","text", "text",
                                  "text", "text", "text",
                                  "text", "text","text"],
                    field_width: ["020", "100", "120", "100", "120",
                                 "060", "020",
                                "060", "060", "020",
                                "060","060","020",
                                "060", "060", "020"],
                    field_align: ["c", "r", "l", "l", "l",
                                 "r", "c",
                                 "r","r","c",
                                 "r","r","c",
                                 "r", "r", "c"]},
            published: {field_caption: ["", "Name", "Exam_period", "Exam_type", "Date_submitted", "Download"],
                    field_names: ["select", "name", "examperiod",  "examtype", "datepublished", "filename"],
                    field_tags: ["div", "div", "div", "div", "div", "a"],
                    filter_tags: ["text", "text","text", "text",  "text", "text"],
                    field_width: ["020", "100", "120", "100", "120", "120"],
                    field_align: ["c", "l", "l", "l", "l", "l"]}
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
        if (has_view_permit){
            const btns = el_btn_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                const data_btn = get_attr_from_el(btn,"data-btn")
                btn.addEventListener("click", function() {HandleBtnSelect(data_btn)}, false )
            };
        }

// --- header bar elements
        const el_hdrbar_examyear = document.getElementById("id_hdrbar_examyear");
            el_hdrbar_examyear.addEventListener("click",
                function() {t_MSESD_Open(loc, "examyear", examyear_map, setting_dict, MSESD_Response)}, false )
        const el_hdrbar_school = document.getElementById("id_hdrbar_school")
            el_hdrbar_school.addEventListener("click",
                function() {t_MSESD_Open(loc, "school", school_map, setting_dict, MSESD_Response)}, false )
        const el_hdrbar_department = document.getElementById("id_hdrbar_department")
            el_hdrbar_department.addEventListener("click",
                function() {t_MSESD_Open(loc, "department", department_map, setting_dict, MSESD_Response)}, false )

// --- side bar elements
        const el_SBR_select_examperiod = document.getElementById("id_SBR_select_period");
            el_SBR_select_examperiod.addEventListener("change", function() {HandleSbrPeriod(el_SBR_select_examperiod)}, false )
        const el_SBR_select_examtype = document.getElementById("id_SBR_select_examtype");
            el_SBR_select_examtype.addEventListener("change", function() {HandleSbrExamtype(el_SBR_select_examtype)}, false )
        const el_SBR_select_subject = document.getElementById("id_SBR_select_subject");
            el_SBR_select_subject.addEventListener("click",
                function() {t_MSSS_Open(loc, "subject", subject_map, setting_dict, MSSS_Response)}, false )
        const el_SBR_select_student = document.getElementById("id_SBR_select_student");
            el_SBR_select_student.addEventListener("click",
                function() {t_MSSS_Open(loc, "student", student_map, setting_dict, MSSS_Response)}, false )
        const el_SBR_select_showall = document.getElementById("id_SBR_select_showall");
            el_SBR_select_showall.addEventListener("click", function() {HandleShowAll()}, false )

        //const el_SBR_filter = document.getElementById("id_SBR_filter")
        //    el_SBR_filter.addEventListener("keyup", function() {MSTUD_InputKeyup(el_SBR_filter)}, false );

// ---  MSSS MOD SELECT SUBJECT / STUDENT ------------------------------
        const el_MSSS_input = document.getElementById("id_MSSS_input")
            el_MSSS_input.addEventListener("keyup", function(event){
                setTimeout(function() {t_MSSS_InputKeyup(el_MSSS_input)}, 50)});
        const el_MSSS_tblBody = document.getElementById("id_MSSS_tbody_select");
        const el_MSSS_btn_save = document.getElementById("id_MSSS_btn_save")
            el_MSSS_btn_save.addEventListener("click", function() {t_MSSS_Save(el_MSSS_input, MSSS_Response)}, false )

// ---  MODAL STUDENT
        const el_MSTUD_div_form_controls = document.getElementById("id_MSTUD_div_form_controls")
        const form_elements = el_MSTUD_div_form_controls.querySelectorAll(".awp_input_text")
        for (let i = 0, el, len = form_elements.length; i < len; i++) {
            el = form_elements[i];
            if(el){el.addEventListener("keyup", function() {MSTUD_InputKeyup(el)}, false )};
        }

        const el_MSTUD_abbrev = document.getElementById("id_MSTUD_abbrev")
        const el_MSTUD_name = document.getElementById("id_MSTUD_name")
        const el_MSTUD_sequence = document.getElementById("id_MSTUD_sequence")

        const el_MSTUD_tbody_select = document.getElementById("id_MSTUD_tblBody_department")
        const el_MSTUD_btn_delete = document.getElementById("id_MSTUD_btn_delete");
        if(has_view_permit){el_MSTUD_btn_delete.addEventListener("click", function() {MSTUD_Save("delete")}, false)}
        const el_MSTUD_btn_save = document.getElementById("id_MSTUD_btn_save");
        if(has_view_permit){ el_MSTUD_btn_save.addEventListener("click", function() {MSTUD_Save("save")}, false)}

// ---  MOD APPROVE GRADE ------------------------------------
        const el_MAG_examperiod = document.getElementById("id_MAG_examperiod");
        const el_MAG_examtype = document.getElementById("id_MAG_examtype");
        const el_MAG_level_container = document.getElementById("id_MAG_level_container");
        const el_MAG_level = document.getElementById("id_MAG_level");
        const el_MAG_class_cluster = document.getElementById("id_MAG_class_cluster");
        const el_MAG_subject = document.getElementById("id_MAG_subject");
                    el_MAG_subject.addEventListener("click",
                function() {t_MSSS_Open(loc, "MAG_subject", subject_map, setting_dict, MSSS_Response)}, false )

        const el_MAG_info_container = document.getElementById("id_MAG_info_container");

        const el_MAG_loader = document.getElementById("id_MAG_loader");

        const  el_MAG_msg_container = document.getElementById("id_MAG_msg_container");
        const  el_MAG_btn_delete = document.getElementById("id_MAG_btn_delete");
            el_MAG_btn_delete.addEventListener("click", function() {MAG_Save(true)}, false )  // true = reset
        const  el_MAG_btn_save = document.getElementById("id_MAG_btn_save");
            el_MAG_btn_save.addEventListener("click", function() {MAG_Save()}, false )
        const  el_MAG_btn_cancel = document.getElementById("id_MAG_btn_cancel");

// ---  MOD CONFIRM ------------------------------------
        const el_confirm_header = document.getElementById("id_confirm_header");
        const el_confirm_loader = document.getElementById("id_confirm_loader");
        const el_confirm_msg_container = document.getElementById("id_confirm_msg_container")
        const el_confirm_msg01 = document.getElementById("id_confirm_msg01")
        const el_confirm_msg02 = document.getElementById("id_confirm_msg02")
        const el_confirm_msg03 = document.getElementById("id_confirm_msg03")

        const el_confirm_btn_cancel = document.getElementById("id_confirm_btn_cancel");
        const el_confirm_btn_save = document.getElementById("id_confirm_btn_save");
        if(has_view_permit){ el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()}) };

// ---  MOD STATUS ------------------------------------
        const el_mod_status_btn_save =  document.getElementById("id_mod_status_btn_save")
            el_mod_status_btn_save.addEventListener("click", function() {ModalStatusSave()}, false )
        const el_mod_status_header = document.getElementById("id_mod_status_header")
        const el_mod_status_note_container = document.getElementById("id_mod_status_note_container")

// ---  MOD NOTE ------------------------------------
        const el_ModNote_header = document.getElementById("id_ModNote_header")
        const el_ModNote_note_container = document.getElementById("id_ModNote_note_container")
        const el_ModNote_btn_save = document.getElementById("id_ModNote_btn_save")
            el_ModNote_btn_save.addEventListener("click", function() {ModNote_Save()}, false )
        const el_ModNote_memo_internal = document.getElementById("id_ModNote_memo_internal")
        const el_ModNote_internal = document.getElementById("id_ModNote_memo_internal");
        el_ModNote_internal.addEventListener("click", function() {ModNote_SetInternalExternal(el_ModNote_internal)}, false )
        for (let i = 0, el; el = el_ModNote_internal.children[i]; i++) {
            el.addEventListener("click", function() {ModNote_SetInternalExternal(el)}, false )
            add_hover(el)
        }
        const el_ModNote_external = document.getElementById("id_ModNote_memo_external");
        el_ModNote_external.addEventListener("click", function() {ModNote_SetInternalExternal(el_ModNote_external)}, false )
        for (let i = 0, el; el = el_ModNote_external.children[i]; i++) {
            el.addEventListener("click", function() {ModNote_SetInternalExternal(el)}, false )
            add_hover(el)
        }

// ---  MOD MESSAGE ------------------------------------
        const el_modmessage_btn_cancel = document.getElementById("id_modmessage_btn_cancel");
            el_modmessage_btn_cancel.addEventListener("click", function() {ModMessageClose()}, false);
        const el_mod_message_text = document.getElementById("id_mod_message_text");

// ---  set selected menu button active
    SetMenubuttonActive(document.getElementById("id_hdr_users"));
    if(has_view_permit){
        // period also returns emplhour_list
        const datalist_request = {
                setting: {page_grade: {mode: "get"}},
                locale: {page: ["grades"]},
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
    }
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
            dataType: 'json',
            success: function (response) {
                console.log("response - elapsed time:", (new Date().getTime() - startime) / 1000 )
                console.log(response)
                // hide loader
                el_loader.classList.add(cls_visible_hide)
                let check_status = false;
                let must_create_submenu = false;

                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                    must_create_submenu = true;
                };
                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict

        console.log("setting_dict: ", setting_dict)
                    // <PERMIT> PR2020-10-02 PPR2021-01-26
                    //  has_permit_edit = true if:
                    //   - school is activated, AND examyear is published, AND school, examyear, country are not locked
                    //   - AND user has perm_edit
                    //   - AND user has role school TODO activate rule, rule left out for testing PR2021-01-26

                    //  - can view page: only 'role_school', 'role_insp', 'role_admin', 'role_system'
                    //  - can add/delete/edit only 'role_admin', 'role_system' plus 'perm_edit'
                    has_permit_edit = false;
                     if (setting_dict.sel_examyear_published && setting_dict.sel_school_activated &&
                            !setting_dict.requsr_country_locked && !setting_dict.sel_examyear_locked &&
                            !setting_dict.sel_school_locked){
                        if (setting_dict.requsr_perm_edit){
                            // TODO activate rule, rule left out for testing PR2021-01-26
                            // TODO add role_teacher in the future
                            //if(setting_dict.requsr_role_school){has_permit_edit = true}
                            has_permit_edit = true
                        }
                    }
                    // <PERMIT> PR2020-10-27
                    // -- only insp, admin and system may change school
                    has_permit_select_school = (setting_dict.requsr_role_insp ||
                                                setting_dict.requsr_role_admin ||
                                                setting_dict.requsr_role_system);

                    selected_btn = (setting_dict.sel_btn)

                    b_UpdateHeaderbar(loc, setting_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school );

                    const sel_examperiod = setting_dict.sel_examperiod;
                    t_FillOptionsFromList(el_SBR_select_examperiod, loc.options_examperiod, null,
                        loc.Select_examperiod, loc.No_examperiods_found, sel_examperiod);
                    document.getElementById("id_hdr_textright1").innerText = setting_dict.sel_examperiod_caption

                    selected_examtype = setting_dict.sel_examtype;
                    const filter_value = sel_examperiod;
                    t_FillOptionsFromList(el_SBR_select_examtype, loc.options_examtype, filter_value,
                        loc.Select_examtype, loc.No_examtypes_found, selected_examtype);

                    selected_subject_pk = setting_dict.sel_subject_pk

                };
                if(must_create_submenu){CreateSubmenu()};

                // call render_messages also when there are no messages, to remove existing messages
                const awp_messages = (response.awp_messages) ? response.awp_messages : {};
                render_messages(response.awp_messages);

                if ("examyear_rows" in response) { b_fill_datamap(examyear_map, response.examyear_rows) };
                if ("school_rows" in response)  { b_fill_datamap(school_map, response.school_rows) };
                if ("department_rows" in response) { b_fill_datamap(department_map, response.department_rows) };

                if ("subject_rows" in response) { b_fill_datamap(subject_map, response.subject_rows) };
                if ("student_rows" in response) { b_fill_datamap(student_map, response.student_rows) };
                if ("studentsubject_rows" in response) { b_fill_datamap(studentsubject_map, response.studentsubject_rows) };
                if ("studentsubjectnote_rows" in response) {
                   // b_fill_datamap(studentsubjectnote_map, response.studentsubjectnote_rows)
                    ModNote_FillNotes(response.studentsubjectnote_rows);
                    };

                if ("grade_rows" in response) {b_fill_datamap(grade_map, response.grade_rows)};
                if ("published_rows" in response) {b_fill_datamap(published_map, response.published_rows)};

                HandleBtnSelect(selected_btn, true)  // true = skip_upload

                MSSS_display_in_sbr();

            },
            error: function (xhr, msg) {
// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                console.log(msg + '\n' + xhr.responseText);
                alert(msg + '\n' + xhr.responseText);
            }
        });
    }  // function DatalistDownload

//=========  CreateSubmenu  ===  PR2020-07-31 PR2021-01-19
    function CreateSubmenu() {
        //console.log("===  CreateSubmenu == ");

       if (setting_dict.requsr_perm_auth1 || setting_dict.requsr_perm_auth2 || setting_dict.requsr_perm_auth3){
        let el_submenu = document.getElementById("id_submenu")
            AddSubmenuButton(el_submenu, loc.Approve_grades, function() {MAG_Open("approve")});
            AddSubmenuButton(el_submenu, loc.Preliminary_Ex2A_form, null, ["mx-2"], "id_submenu_download_ex2a", url_grade_download_ex2a);
            AddSubmenuButton(el_submenu, loc.Submit_Ex2A_form, function() {MAG_Open("submit_test")});
        el_submenu.classList.remove(cls_hide);
        }
    };//function CreateSubmenu

//###########################################################################
//=========  HandleBtnSelect  ================ PR2020-09-19  PR2020-11-14
    function HandleBtnSelect(data_btn, skip_upload) {
        console.log( "===== HandleBtnSelect ========= ", data_btn);
        selected_btn = data_btn
        if(!selected_btn){selected_btn = "grade_by_subject"}

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_grade: {sel_btn: selected_btn}};
            UploadSettings (upload_dict, url_settings_upload);
        };

// ---  highlight selected button
        highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  show only the elements that are used in this tab
        show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

// ---  fill datatable
        FillTblRows();

// --- update header text
        UpdateHeaderText();
    }  // HandleBtnSelect

//=========  HandleTblRowClicked  ================ PR2020-08-03
    function HandleTblRowClicked(tr_clicked) {
        //console.log("=== HandleTblRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

        //selected_student_pk = null;

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        DeselectHighlightedRows(tr_clicked, cls_selected);
        tr_clicked.classList.add(cls_selected)

// ---  update selected_student_pk
        // only select employee from select table
        const row_id = tr_clicked.id
        if(row_id){
            const map_dict = get_mapdict_from_datamap_by_id(student_map, row_id)
            //selected_student_pk = map_dict.id;
        }
    }  // HandleTblRowClicked

//=========  HandleSelectRowClicked  ================ PR2020-12-16
    function HandleSelectRowClicked(tr_clicked) {
        console.log("=== HandleSelectRowClicked");
        console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);
        const tblName = get_attr_from_el(tr_clicked, "data-table")
        console.log( "tblName: ", tblName);

        if (tblName === "select_student") {
             selected_student_pk = null;
        } else if (tblName === "select_subject") {
            selected_subject_pk = null;
        }

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        DeselectHighlightedRows(tr_clicked, cls_selected);
        tr_clicked.classList.add(cls_selected)

// ---  update selected_student_pk or selected_subject_pk
        // only select employee from select table
        const row_id = tr_clicked.id
        if(row_id){
            const data_map = (tblName === "select_student") ? student_map :
                              (tblName === "select_subject") ? subject_map : null;
            const map_dict = get_mapdict_from_datamap_by_id(data_map, row_id)
            if (tblName === "select_student") {
                 selected_student_pk = map_dict.id;
            } else if (tblName === "select_subject") {
                selected_subject_pk = map_dict.id;
            }
        }
        console.log( "selected_student_pk: ", selected_student_pk);
        console.log( "selected_subject_pk: ", selected_subject_pk);

        FillTblRows();
    }  // HandleSelectRowClicked


//=========  HandleSbrPeriod  ================ PR2020-12-20
    function HandleSbrPeriod(el_select) {
        console.log("=== HandleSbrPeriod");
        console.log( "el_select.value: ", el_select.value, typeof el_select.value)
        const sel_examperiod = (Number(el_select.value)) ? Number(el_select.value) : null;
        const filter_value = sel_examperiod;

        console.log( "loc.options_examtype: ", loc.options_examtype)
// --- fill seelctbox examtype with examtypes of this period
        t_FillOptionsFromList(el_SBR_select_examtype, loc.options_examtype, filter_value,
            loc.Select_examtype, loc.No_examtypes_found);

// ---  upload new setting
        let new_setting = {page_grade: {mode: "get"}};
        new_setting.selected_pk = {sel_examperiod: sel_examperiod}
        const datalist_request = {setting: new_setting};

// also retrieve the tables that have been changed because of the change in school / dep
        datalist_request.grade_rows = {get: true};
        DatalistDownload(datalist_request);

    }  // HandleSbrPeriod

//=========  HandleSbrExamtype  ================ PR2020-12-20
    function HandleSbrExamtype(el_select) {
        console.log("=== HandleSbrExamtype");
        console.log( "el_select.value: ", el_select.value, typeof el_select.value)
        selected_examtype = el_select.value;
        const filter_value = Number(el_select.value);
        t_FillOptionsFromList(el_SBR_select_examtype, loc.options_examtype, filter_value,
            loc.Select_examtype, loc.No_examtypes_found, selected_examtype);

        console.log( "selected_examtype: ", selected_examtype, typeof selected_examtype)

// ---  upload new setting
        const upload_dict = {selected_pk: {sel_examtype: selected_examtype}};
        UploadSettings (upload_dict, url_settings_upload);

    }  // HandleSbrExamtype

//=========  HandleShowAll  ================ PR2020-12-17
    function HandleShowAll() {
        console.log("=== HandleShowAll");
        selected_student_pk =  null;
        selected_subject_pk =  null;
        MSSS_display_in_sbr();
        FillTblRows();
    }

//========= UpdateHeaderText  ================== PR2020-07-31
    function UpdateHeaderText(){
        //console.log(" --- UpdateHeaderText ---" )
        let header_text = null;
        if(selected_btn === "btn_user_list"){
            header_text = loc.User_list;
        } else {
            header_text = loc.Permissions;
        }
        //document.getElementById("id_hdr_text").innerText = header_text;
    }   //  UpdateHeaderText

//========= FillTblRows  ====================================
    function FillTblRows() {
        console.log( "===== FillTblRows  === ");
        console.log( "setting_dict", setting_dict);

        const tblName = get_tblName_from_selectedBtn()
        console.log( "tblName: ", tblName);

        const data_map = get_datamap_from_tblName(tblName);
        const field_setting = field_settings[tblName];
        console.log( "field_setting: ", field_setting);
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

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

// --- create table header
        CreateTblHeader(field_setting);

// --- loop through grade_map
        console.log( "data_map", data_map);
        if(data_map){
            for (const [map_id, map_dict] of data_map.entries()) {
            // only show rows of selected student / subject
                let show_row = (tblName === "published") ? true :
                                (!setting_dict.sel_student_pk || map_dict.student_id === setting_dict.sel_student_pk) &&
                                (!setting_dict.sel_subject_pk || map_dict.subject_id === setting_dict.sel_subject_pk);

                if(show_row){
          // --- insert row at row_index
                    //const schoolcode_lc_trail = ( (map_dict.sb_code) ? map_dict.sb_code.toLowerCase() : "" ) + " ".repeat(8) ;
                    //const schoolcode_sliced = schoolcode_lc_trail.slice(0, 8);
                    //const order_by = schoolcode_sliced +  ( (map_dict.username) ? map_dict.username.toLowerCase() : "");
                    const row_index = -1; // t_get_rowindex_by_orderby(tblBody_datatable, order_by)
                    let tblRow = CreateTblRow(tblName, field_setting, map_id, map_dict, row_index)
                }
          };
        }  // if(!!data_map)

    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-12-03 PR2020-12-18 PR2021-01-022
    function CreateTblHeader(field_setting) {
        console.log("===  CreateTblHeader ===== ");

        const column_count = field_setting.field_names.length;
        console.log("field_setting", field_setting);
// +++  insert header and filter row ++++++++++++++++++++++++++++++++
        let tblRow_header = tblHead_datatable.insertRow (-1);
        let tblRow_filter = tblHead_datatable.insertRow (-1);
    // --- loop through columns
        for (let j = 0; j < column_count; j++) {
            const key = field_setting.field_caption[j];
            const caption = (loc[key]) ? loc[key] : key;

            const field_name = field_setting.field_names[j];
            const field_tag = field_setting.field_tags[j];
            const filter_tag = field_setting.filter_tags[j];
            const class_width = "tw_" + field_setting.field_width[j] ;
            const class_align = "ta_" + field_setting.field_align[j];

            // skip columns if not columns_shown[field_name]) = true;
            if (columns_shown[field_name]){
    // ++++++++++ insert columns in header row +++++++++++++++
        // --- add th to tblRow_header +++
                let th_header = document.createElement("th");
        // --- add div to th, margin not working with th
                    const el_header = document.createElement("div");
                        el_header.innerText = caption;
        // --- add width, text_align, right padding in examnumber
                        el_header.classList.add(class_width, class_align);
                        if(field_name === "examnumber"){el_header.classList.add("pr-2")}
                    th_header.appendChild(el_header)
                tblRow_header.appendChild(th_header);

    // ++++++++++ create filter row +++++++++++++++
        // --- add th to tblRow_filter.
                const th_filter = document.createElement("th");
                    const el_filter = document.createElement(field_tag);
                        el_filter.setAttribute("data-field", field_name);
                        el_filter.setAttribute("data-filtertag", filter_tag);

        // --- add EventListener to el_filter
                        const event_str = (filter_tag === "text") ? "keyup" : "click";
                        el_filter.addEventListener(event_str, function(event){HandleFilterField(el_filter, j, event)});

        // --- add other attributes
                        if (filter_tag === "text") {
                            el_filter.setAttribute("type", "text")
                            el_filter.classList.add("input_text");

                            el_filter.setAttribute("autocomplete", "off");
                            el_filter.setAttribute("ondragstart", "return false;");
                            el_filter.setAttribute("ondrop", "return false;");
                        } else if (["toggle", "activated", "inactive"].indexOf(filter_tag) > -1) {
                            // default empty icon necessary to set pointer_show
                            // default empty icon necessary to set pointer_show
                            append_background_class(el_filter,"tickmark_0_0");
                        }

        // --- add width, text_align
                        el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");
                    th_filter.appendChild(el_filter)
                tblRow_filter.appendChild(th_filter);

            }  //  if (columns_shown.inludes(field_name))
        }  // for (let j = 0; j < column_count; j++)

    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09
    function CreateTblRow(tblName, field_setting, map_id, map_dict, row_index) {
        //console.log("=========  CreateTblRow =========");
        //console.log("map_dict", map_dict);
        //console.log("tblName", tblName);

        const field_names = field_setting.field_names;
        const field_tags = field_setting.field_tags;
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;
        //console.log("field_names", field_names);

// --- insert tblRow into tblBody at row_index
        let tblRow = tblBody_datatable.insertRow(row_index);
        tblRow.id = map_id

// --- add data attributes to tblRow
        tblRow.setAttribute("data-pk", map_dict.id);

// ---  add data-orderby attribute to tblRow, for ordering new rows
        // happens in UpdateTblRow
        const order_by_stud = (map_dict.fullname) ? map_dict.fullname.toLowerCase() : null;
        const order_by_subj = (map_dict.subj_name) ? map_dict.subj_name.toLowerCase() : null;
        tblRow.setAttribute("data-orderby_stud", order_by_stud);
        tblRow.setAttribute("data-orderby_subj", order_by_subj);

// --- add EventListener to tblRow
        tblRow.addEventListener("click", function() {HandleTblRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
        for (let j = 0; j < column_count; j++) {
            const field_name = field_names[j];
            //console.log("field_name", field_name);
      // skip columns if not in columns_shown
            if (columns_shown[field_name]){
        // --- insert td element,
                let td = tblRow.insertCell(-1);
        // --- create element with tag from field_tags
                const field_tag = field_tags[j];
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
                            //el.addEventListener("keyup", function() {delay(function(){HandleEventKey(el)}, 1000 );});
                            el.addEventListener("change", function(){HandleEventKey(el)});
                            el.addEventListener("keydown", function(event){HandleArrowEvent(el, event)});

        // --- add class 'input_text' and text_align
                        // class 'input_text' contains 'width: 100%', necessary to keep input field within td width
                            el.classList.add("input_text");
                        } else {
                        }
                        el.classList.add("ta_" + field_setting.field_align[j]);
                        if (field_name.includes("status")){
// --- add column with status icon
                            el.classList.add("tw_032", "stat_0_1")
                        } else if (field_name === "hasnote"){
                            el.classList.add("note_1_4")
                        } else if(field_name === "examnumber"){
                            el.classList.add("pr-4")
                        } else if (field_name === "filename"){
                            const file_path = (map_dict.filepath) ? map_dict.filepath : null;
                            const file_name = (map_dict.name) ? map_dict.name + ".pdf" : "";

                            const order_by_subj = (map_dict.subj_name) ? map_dict.subj_name.toLowerCase() : null;
                            el.setAttribute("href", file_path);
                            el.setAttribute("download", file_name);
                            add_hover(td);
                        }

                    td.appendChild(el);
               if (["examnumber", "fullname"].indexOf(field_name) > -1){
                    td.addEventListener("click", function() {MSTUD_Open(td)}, false)
                    add_hover(td);
               } else if (["subj_code", "subj_name"].indexOf(field_name) > -1){
                    td.addEventListener("click", function() {MSTUDSUBJ_Open(td)}, false)
                    add_hover(td);
               } else if (field_name.includes("status")){
                    td.addEventListener("click", function() {UploadToggle(el)}, false)
                    add_hover(td);
               } else if (field_name === "hasnote"){
                    td.addEventListener("click", function() {ModNote_Open(el)}, false)
                    add_hover(td);
               }
               //td.classList.add("pointer_show", "px-2");
    // --- add field_width and text_align
                //el.classList.add("tw_XX" + field_width[j], "ta_" + field_align[j]);
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

//=========  UpdateField  ================ PR2020-12-18
    function UpdateField(el, map_dict) {
        //console.log("=========  UpdateField =========");
        //console.log("map_dict", map_dict);
        if(el){
            const field_name = get_attr_from_el(el, "data-field");
            const fld_value = map_dict[field_name];
        console.log("field_name", field_name);
        console.log("fld_value", fld_value);
            if (el.nodeName === "INPUT"){
                 el.value = (fld_value) ? fld_value : null;
            } else if (field_name ==="se_status"){
                el.className = b_get_status_iconclass(map_dict.se_published_id, map_dict.se_auth1by_id, map_dict.se_auth2by_id, map_dict.se_auth3by_id);
            } else if (field_name ==="pe_status"){
                el.className = b_get_status_iconclass(map_dict.pe_published_id, map_dict.pe_auth1by_id, map_dict.pe_auth2by_id, map_dict.pe_auth3by_id);
            } else if (field_name ==="ce_status"){
                el.className = b_get_status_iconclass(map_dict.ce_published_id, map_dict.ce_auth1by_id, map_dict.ce_auth2by_id, map_dict.ce_auth3by_id);
            } else if (field_name === "hasnote"){
                //el.className = "tw032 note_1_1"
                el.className = "note_1_1"
            } else if (field_name === "filename"){
                el.innerHTML = "&#8681;";
            } else{
                 el.innerText = (fld_value) ? fld_value : null;
            }
        }
    };

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

//========= HandleEventKey  ===============PR2020-08-16
    function HandleEventKey(el_input){
        console.log(" --- HandleEventKey ---")

        // event_shiftKey = true when shift key is pressed. Used for Shift+Tab (not in use yet
        const tblRow = get_tablerow_selected(el_input)
        const map_id = tblRow.id
        if (map_id){
            const map_dict = get_mapdict_from_datamap_by_id(grade_map, map_id)
            const fldName = get_attr_from_el(el_input, "data-field")
            const map_value = map_dict[fldName];
            const new_value = el_input.value;
            if(new_value !== map_value){
                const arr = ValidateGrade(loc, fldName, new_value, map_dict);
                //const value_text = arr[0];
                //const msg_err = arr[1];
                // FOR TESTING ONLY: turn of validation
                const value_text =new_value
                const msg_err = null
                if (msg_err){
                    //alert(msg_err)
    // ---  show modal
                    const header_text = null;
                    b_show_mod_message(header_text, msg_err);

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

    };  // HandleEventKey


//========= UploadToggle  ============= PR2020-07-31  PR2021-01-14
    function UploadToggle(el_input) {
        console.log( " ==== UploadToggle ====");

        mod_dict = {};
        const tblRow = get_tablerow_selected(el_input);
        console.log( "tblRow", tblRow);
        if(tblRow){
            const perm_auth1 = (setting_dict.requsr_perm_auth1) ? setting_dict.requsr_perm_auth1 : false;
            const perm_auth2 = (setting_dict.requsr_perm_auth2) ? setting_dict.requsr_perm_auth2 : false;
            const perm_auth3 = (setting_dict.requsr_perm_auth3) ? setting_dict.requsr_perm_auth3 : false;

            if(perm_auth1 || perm_auth2 || perm_auth3){
                const map_id = tblRow.id
                const map_dict = get_mapdict_from_datamap_by_id(grade_map, map_id);
            console.log( "map_dict", map_dict);
                if(!isEmpty(map_dict)){
                    const fldName = get_attr_from_el(el_input, "data-field");
                    if(fldName in map_dict ){
                        const examtype = fldName.substring(0,2);
                        const published_field = examtype + "_published"
                        let published_pk = (map_dict[published_field]) ? map_dict[published_field] : null;

                        console.log( "fldName", fldName);
                        console.log( "published_field", published_field);
                        console.log( "published_pk", published_pk);

                // ---  index of auth1 = 1, index of auth2 = 2  ---  STATUS_01_AUTH1 = 2,  STATUS_02_AUTH2 = 4
                        const index = ( perm_auth1 ) ? 1 : ( perm_auth2 ) ? 2 : ( perm_auth3 ) ? 3 : null;
                        const status_sum = (map_dict[fldName]) ? map_dict[fldName] : 0;
                        const status_bool_at_index = b_get_status_bool_at_index(status_sum, index)
                console.log( "status_bool_at_index", status_bool_at_index);
                console.log( "status_sum", status_sum);

                // ---  toggle value of status_bool_at_index
                        const new_status_bool_at_index = !status_bool_at_index;
                console.log( "new_status_bool_at_index", new_status_bool_at_index);
                // ---  put new value in  value of status_bool_at_index

    // ---  change icon, before uploading
                        //const new_status_sum = b_set_status_bool_at_index(status_sum, index, new_status_bool_at_index);
                        //el_input.className = get_status_class(new_status_sum)

    // ---  upload changes
                        // value of 'mode' setermines if status is set to 'approved' or 'not
                        // instead of using value of new_status_bool_at_index,
                        const mode = (new_status_bool_at_index) ? "approve" : "reset"
                        const upload_dict = { table: map_dict.table,
                                               mode: mode,
                                               mapid: map_id,
                                               field: fldName,
                                               status_bool_at_index:  new_status_bool_at_index,
                                               examperiod: map_dict.examperiod,
                                               examtype: examtype,

                                               grade_pk: map_dict.id,
                                               student_pk: map_dict.student_id,
                                               studsubj_pk: map_dict.studsubj_id};
                        UploadChanges(upload_dict, url_grade_approve);

                    }  //   if(fldName in map_dict ){
                }  //  if(!isEmpty(map_dict))
            }  //if(perm_auth1 || perm_auth1)
        }  //   if(!!tblRow)
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
                        RefreshDataMap(tblName, field_names, response.updated_student_rows, student_map);
                    };
                    $("#id_mod_student").modal("hide");

                    if ("msg_dict" in response) {
                        //if (mod_dict.mode && ["submit_test", "approve"].indexOf(mod_dict.mode) > -1){
                            MAG_UpdateFromResponse (response.msg_dict);
                        //}
                    }
                    if ("updated_grade_rows" in response) {
                        const tblName = "grades";
                        const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                        RefreshDataMap(tblName, field_names, response.updated_grade_rows, grade_map);
                    }

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

// +++++++++ MOD STUDENT ++++++++++++++++ PR2020-09-30
// --- also used for level, sector,
    function MSTUD_Open(el_input){
        console.log(" -----  MSTUD_Open   ----")

        let user_pk = null, user_country_pk = null, user_schoolbase_pk = null, mapid = null;
        const fldName = get_attr_from_el(el_input, "data-field");

        // el_input is undefined when called by submenu btn 'Add new'
        mod_MSTUD_dict = {}
        let tblName = "student";

        const student_pk = get_attr_from_el(el_input, "data-student_pk")
        console.log("student_pk", student_pk)
        const map_dict = get_mapdict_from_datamap_by_tblName_pk(student_map, "student", student_pk);
        mod_MSTUD_dict = deepcopy_dict(map_dict);
        console.log("mod_MSTUD_dict", mod_MSTUD_dict)

// ---  set header text
        MSTUD_headertext(false, tblName, mod_MSTUD_dict.name);

// ---  remove value from el_mod_employee_input
        MSTUD_SetElements();  // true = also_remove_values

        const modified_dateJS = parse_dateJS_from_dateISO(mod_MSTUD_dict.modifiedat);
        const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
        const modified_by = (mod_MSTUD_dict.modby_username) ? mod_MSTUD_dict.modby_username : "-";

        document.getElementById("id_MSTUD_msg_modified").innerText = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by

// ---  hide save, delete, log buttons
        add_or_remove_class(document.getElementById("id_MSTUD_btn_save"), cls_hide, true);
        add_or_remove_class(document.getElementById("id_MSTUD_btn_delete"), cls_hide, true);
        add_or_remove_class(document.getElementById("id_MSTUD_btn_log"), cls_hide, true);
        document.getElementById("id_MSTUD_btn_cancel").innerText = loc.Close

// ---  show modal
        $("#id_mod_student").modal({backdrop: true});

    };  // MSTUD_Open

//========= MSTUD_SetElements  ============= PR2020-08-03
    function MSTUD_SetElements(also_remove_values){
        //console.log( "===== MSTUD_SetElements  ========= ");
// --- loop through input elements
        let form_elements = el_MSTUD_div_form_controls.querySelectorAll(".awp_input_text")
        for (let i = 0, el, fldName, fldValue, len = form_elements.length; i < len; i++) {
            el = form_elements[i];
            if(el){
                fldName = get_attr_from_el(el, "data-field");
                el.value = (mod_MSTUD_dict[fldName]) ? mod_MSTUD_dict[fldName] : null;
            };
        }
        const lastname = (mod_MSTUD_dict.lastname) ? mod_MSTUD_dict.lastname : "";
        const firstname = (mod_MSTUD_dict.firstname) ? mod_MSTUD_dict.firstname : "";
        document.getElementById("id_MSTUD_hdr").innerText = lastname + ", " + firstname;


    }  // MSTUD_SetElements

//========= MSTUD_headertext  ======== // PR2020-09-30
    function MSTUD_headertext(is_addnew, tblName, name) {
        //console.log(" -----  MSTUD_headertext   ----")
        //console.log("tblName", tblName, "is_addnew", is_addnew)

        let header_text = (tblName === "subject") ? (is_addnew) ? loc.Add_subject : loc.Subject :
                    (tblName === "level") ? (is_addnew) ? loc.Add_level : loc.Level :
                    (tblName === "sector") ? (is_addnew) ? loc.Add_sector : loc.Sector :
                    (tblName === "subjecttype") ? (is_addnew) ? loc.Add_subjecttype : loc.Subjecttype :
                    (tblName === "scheme") ? (is_addnew) ? loc.Add_scheme : loc.Scheme :
                    (tblName === "package") ? (is_addnew) ? loc.Add_package : loc.Package :
                    (tblName === "packageitem") ? (is_addnew) ? loc.Add_package_item : loc.Package_item : "---";

        if (!is_addnew) {
            header_text += ": " + ((name) ? name : "---")

            };
        document.getElementById("id_MSTUD_hdr").innerText = header_text;

        let this_dep_text = (tblName === "subject") ? loc.this_subject :
                    (tblName === "level") ? loc.this_level :
                    (tblName === "sector") ? loc.this_sector :
                    (tblName === "subjecttype") ? loc.this_subjecttype :
                    (tblName === "scheme") ? loc.this_scheme :
                    (tblName === "package") ? loc.this_package :
                    (tblName === "packageitem") ?  loc.this_package_item : "---";
        //document.getElementById("id_MSTUD_label_dep").innerText = loc.Departments_where + this_dep_text + loc.occurs + ":";
    }  // MSTUD_headertext

// +++++++++ END MOD STUDENT +++++++++++++++++++++++++++++++++++++++++



// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2020-08-03
    function ModConfirmOpen(mode, el_input) {
        console.log(" -----  ModConfirmOpen   ----")
        // values of mode are : "delete", "inactive" or "resend_activation_email", "permission_sysadm"

        if(has_permit_edit){


    // ---  get selected_pk
            let tblName = null, selected_pk = null;
            // tblRow is undefined when clicked on delete btn in submenu btn or form (no inactive btn)
            const tblRow = get_tablerow_selected(el_input);
            if(tblRow){
                tblName = get_attr_from_el(tblRow, "data-table")
                selected_pk = get_attr_from_el(tblRow, "data-pk")
            } else {
                tblName = get_tblName_from_selectedBtn()
                selected_pk = (tblName === "student") ? selected_student_pk :
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
        let close_modal = !has_permit_edit;

        if(has_permit_edit){
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
        console.log("selected_examtype", selected_examtype) ;

        console.log("loc.options_examtype", loc.options_examtype) ;
        // modes are 'approve' 'submit_test' 'submit_submit'
        mod_MAG_dict = {mode: mode}
        const is_approve_mode = (mode === "approve");
        let has_permit = (setting_dict.requsr_perm_auth1 || setting_dict.requsr_perm_auth2)
        if (!has_permit && is_approve_mode) {has_permit = (setting_dict.requsr_perm_auth3)}

        if (has_permit) {

            document.getElementById("id_MAG_header").innerText = (is_approve_mode) ? loc.Approve_grades : loc.Submit_Ex2A_form;
            document.getElementById("id_MAG_subheader").innerText = (is_approve_mode) ? loc.MAG_info.subheader_approve : loc.MAG_info.subheader_submit;

            document.getElementById("id_MAG_info_01").innerHTML = (is_approve_mode) ? loc.MAG_info.approve_01 : loc.MAG_info.submit_01;
            document.getElementById("id_MAG_info_02").innerHTML = (is_approve_mode) ? loc.MAG_info.approve_02 : loc.MAG_info.submit_02;
            document.getElementById("id_MAG_info_03").innerHTML = (is_approve_mode) ? loc.MAG_info.approve_03 : loc.MAG_info.submit_03;

            el_MAG_examperiod.innerText = setting_dict.sel_examperiod_caption

            let examtype_caption = null;
            for (let i = 0, dict; dict = loc.options_examtype[i]; i++) {
                if(dict.value === selected_examtype) {
                    examtype_caption = dict.caption;
                    break;
                }
            }
            el_MAG_examtype.innerText = examtype_caption

            add_or_remove_class(el_MAG_level_container, cls_hide, !setting_dict.sel_dep_level_req)
            el_MAG_level.innerText = setting_dict.sel_depbase_code
            let subject_text = null;
            if(selected_subject_pk){
                const dict = get_mapdict_from_datamap_by_tblName_pk(subject_map, "subject", selected_subject_pk);
                subject_text =  (dict.name) ? dict.name : "---"
            } else {
                subject_text = "<" + loc.All_subjects + ">";
            }
            el_MAG_subject.innerText = subject_text;

            const auth_by = (setting_dict.requsr_perm_auth1) ? loc.President :
                         (setting_dict.requsr_perm_auth2) ? loc.Secretary :
                         (setting_dict.requsr_perm_auth3) ? loc.Commissioner : null;
            document.getElementById("id_MAG_approved_by").innerText = auth_by
            document.getElementById("id_MAG_approved_name").innerText = setting_dict.requsr_name

            const btn_text = (is_approve_mode) ? loc.Approve : (mode === "submit_test") ? loc.Check_grades : loc.Submit_Ex2A_form;
            el_MAG_btn_save.innerText = btn_text
// ---  show info
        add_or_remove_class(el_MAG_info_container, cls_hide, false)
// ---  hide loader  // PR2021-01-21 debug 'display_hide' not working when class 'image_container' is in same div
         add_or_remove_class(el_MAG_loader, cls_hide, true);

// ---  hide delete btn when submit
        add_or_remove_class(el_MAG_btn_delete, cls_hide, !is_approve_mode);
// ---  show only the elements that are used in this tab
            const show_class = (is_approve_mode) ? "tab_approve" : "tab_submit";
            show_hide_selected_elements_byClass("tab_show", show_class);

            $("#id_mod_approve_grade").modal({backdrop: true});
        }  //  if (has_permit)
    }  // MAG_Open


//=========  MAG_Save  ================
    function MAG_Save (is_reset) {
        console.log("===  MAG_Save  =====") ;
        console.log("mod_MAG_dict.mode", mod_MAG_dict.mode) ;
        const mode = (is_reset) ? "reset" : mod_MAG_dict.mode;
// ---  hide info
        add_or_remove_class(el_MAG_info_container, cls_hide, true)

// ---  hide delete btn
        add_or_remove_class(el_MAG_btn_delete, cls_hide, true);

// ---  show loader
        add_or_remove_class(el_MAG_loader, cls_hide, false)

// ---  upload changes
        const upload_dict = { table: "grade",
                               mode: mode}
        console.log("upload_dict", upload_dict);
        UploadChanges(upload_dict, url_grade_approve);

// hide modal
        //$("#id_mod_approve_grade").modal("hide");
    };  // MAG_Save

    function MAG_UpdateFromResponse (msg_dict) {
        console.log("===  MAG_UpdateFromResponse  =====") ;
        console.log("msg_dict", msg_dict);
        console.log("mod_MAG_dict", mod_MAG_dict);

// ---  hide loader
        add_or_remove_class(el_MAG_loader, cls_hide, true);
        let msg_01_txt = null,  msg_02_txt = null, msg_03_txt = null, msg_04_txt = null;

// make message container green when grades can be published, red otherwise
        const can_publish = (!!msg_dict.saved);
        if(can_publish){mod_MAG_dict.mode = "submit_submit"}
        const border_class = (can_publish) ? "border_bg_valid" : "border_bg_invalid";
        console.log("can_publish", can_publish) ;
        add_or_remove_class(el_MAG_msg_container, "border_bg_valid", can_publish, "border_bg_invalid");
        console.log("el_MAG_msg_container", el_MAG_msg_container) ;

// hide ok button when not can_publish
        add_or_remove_class(el_MAG_btn_save, cls_hide, !can_publish);
        el_MAG_btn_save.innerText = (can_publish) ? loc.Submit_Ex2A_form : loc.Close;
        el_MAG_btn_cancel.innerText = (can_publish) ? loc.Cancel : loc.Close;

// create message in container
        el_MAG_msg_container.innerText = null

// --- create element with tag from field_tags

        const array = ["count_text", "skip_text", "already_published_text", "no_value_text", "auth_missing_text",
            "double_approved_text", "already_approved_by_auth_text", "saved_text"]
        for (let i = 0, el, key; key = array[i]; i++) {
            if(key in msg_dict) {
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

// ---  show only the elements that are used in this tab
        show_hide_selected_elements_byClass("tab_show", "tab_test");

// hide modal
        //$("#id_mod_approve_grade").modal("hide");
    };
//========= MOD NOTE Open====================================
    function ModNote_Open (el_input) {
        console.log("===  ModNote_Open  =====") ;

// reset note_container
        el_ModNote_note_container.innerText = null;
        mod_dict = {};
// get tr_selected
        let tr_selected = get_tablerow_selected(el_input)
        console.log("tr_selected", tr_selected) ;
// get info from grade_map
        let grade_dict = get_itemdict_from_datamap_by_el(el_input, grade_map)
        console.log("grade_dict", grade_dict) ;
        if(!isEmpty(grade_dict)){
            let headertext = (grade_dict.fullname) ? grade_dict.fullname + "\n" : "";
            if(grade_dict.subj_code) { headertext += grade_dict.subj_name};
            el_ModNote_header.innerText = headertext;

            // period also returns emplhour_list
            const datalist_request = {studentsubjectnote_rows: {studsubj_pk: grade_dict.studsubj_id}};
            DatalistDownload(datalist_request, true);  // true = keep_loader_hidden

            mod_dict = {
                studsubj_pk: grade_dict.studsubj_id,
                examperiod_int: setting_dict.sel_examperiod
                }

            const el_input = document.getElementById("id_ModNote_input_note")
            if (el_input){ setTimeout(function (){ el_input.focus() }, 50)};

// get info from grade_map
            $("#id_mod_note").modal({backdrop: true});
        }
    }  // ModNote_Open

//========= ModNote_Save============== PR2020-10-15
    function ModNote_Save () {
        console.log("===  ModNote_Save  =====");
        let permit_add_notes = true;
        if(permit_add_notes){
            const value = document.getElementById("id_ModNote_input_note").value;
            if(value){
                // put note in tblRow on response
                //let upload_dict = { id: {ppk: mod_dict.emplhour_pk,  table: "studentsubjectnote", create: true},
                //                    note: {value: note, update: true}};

        console.log("mod_dict", mod_dict) ;

            // ---  upload changes
                const upload_dict = { table: mod_dict.table,
                                       create: true,

                                       examperiod_int: mod_dict.examperiod_int,
                                       studsubj_pk: mod_dict.studsubj_pk,

                                       note: value,
                                       note_status: mod_dict.sel_index
                                       };

        console.log("upload_dict", upload_dict) ;
                UploadChanges(upload_dict, url_studentsubjectnote_upload) ;
           }
       }
// hide modal
        $("#id_mod_note").modal("hide");
    }  // ModNote_Save


//========= ModNote_SetInternalExternal============== PR2021-01-17
    function ModNote_SetInternalExternal (el) {
        console.log("===  ModNote_SetInternalExternal  =====") ;
        let data_index = get_attr_from_el(el, "data-index")
        console.log("data_index", data_index) ;
// if clicked om image, store index in mod_dict.sel_index, ModNote_SetInternalExternal is also called bij parent el.
        if(Number(data_index)) {
            mod_dict.sel_index = data_index
        } else if (["internal", "external"].indexOf(data_index) > -1){
            const is_external = (data_index === "external");
            const sel_index = (!is_external) ? "1" : (mod_dict.sel_index) ? mod_dict.sel_index : "2";
            mod_dict.sel_index = sel_index;

            add_or_remove_class(el_ModNote_internal, "tr_hover", !is_external)
            add_or_remove_class(el_ModNote_external, "tr_hover", is_external)

            for (let i = 0, el; el = el_ModNote_external.children[i]; i++) {
                const index = get_attr_from_el(el, "data-index")
                if(index){
                    const selected = (index === sel_index)
                    add_or_remove_class(el, "note_1_" + index, selected, "note_0_" + index )
                }
            }

        }
    }

//========= ModNote_FillNotes============== PR2020-10-15
    function ModNote_FillNotes (note_rows) {
        console.log("===  ModNote_FillNotes  =====") ;

        console.log("note_rows", note_rows) ;
        el_ModNote_note_container.innerText = null;
        let permit_add_notes = true;

// --- show input element for note, only when permit_edit_rows
        const el_container = document.getElementById("id_ModNote_input_container")
        add_or_remove_class(el_container, cls_hide, !permit_add_notes)

        if(note_rows && note_rows.length){
            for (let i = 0, row; row = note_rows[i]; i++) {
                const note_text = (row.note) ? row.note : "";
                const note_len = (note_text) ? note_text.length : 0;
                const modified_dateJS = parse_dateJS_from_dateISO(row.modifiedat);
                const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
                let modified_by = (row.schoolcode) ? row.schoolcode + " " : "";
                modified_by += (row.modifiedby) ? row.modifiedby : "-";
                const mod_text = modified_by + ", " + modified_date_formatted + ":"
        // --- create div element with note
                const el_div = document.createElement("div");
                el_div.classList.add("tsa_textarea_div");
                    const el_small = document.createElement("small");
                    el_small.classList.add("tsa_textarea_div", "px-2");
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


                el_ModNote_note_container.appendChild(el_div);
            }
        }


    }  // ModNote_FillNotes




//###########################################################################
// +++++++++++++++++ REFRESH DATA MAP ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataMap  ================ PR2020-08-16 PR2020-09-30
    function RefreshDataMap(tblName, field_names, data_rows, data_map) {
        console.log(" --- RefreshDataMap  ---");
        //console.log("data_rows", data_rows);
        if (data_rows) {
            const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
            for (let i = 0, update_dict; update_dict = data_rows[i]; i++) {
                RefreshDatamapItem(tblName, field_names, update_dict, data_map);
            }
        }
    }  //  RefreshDataMap

//=========  RefreshDatamapItem  ================ PR2020-08-16 PR2020-09-30
    function RefreshDatamapItem(tblName, field_names, update_dict, data_map) {
        //console.log(" --- RefreshDatamapItem  ---");
        //console.log("update_dict", update_dict);
        if(!isEmpty(update_dict)){
// ---  update or add update_dict in subject_map
            let updated_columns = [];
    // get existing map_item
            const tblName = update_dict.table;
            const map_id = update_dict.mapid;
            let tblRow = document.getElementById(map_id);

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
                const row_index = t_get_rowindex_by_orderby(tblBody_datatable, order_by)
                tblRow = CreateTblRow(map_id, update_dict, row_index)
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
            //console.log("updated_columns", updated_columns);
    // ---  make update
            // note: when updated_columns is empty, then updated_columns is still true.
            // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
            if(tblRow && (updated_columns.length || err_dict)){
    // ---  make entire row green when row is created
                if(updated_columns.includes("created")){
                    ShowOkElement(tblRow);
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


                                   // alert(err_dict[el_fldName]);
        // make gield green when field name is in updated_columns
                                } else if(updated_columns.includes(el_fldName)){
                                    UpdateField(el, update_dict);
                                    ShowOkElement(el);
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
// +++++++++++++++++ FILTER ++++++++++++++++++++++++++++++++++++++++++++++++++

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
        //console.log( "===== Filter_TableRows  ========= ");

        const tblName_settings = (selected_btn === "btn_user_list") ? "users" : "permissions";

// ---  loop through tblBody.rows
        for (let i = 0, tblRow, show_row; tblRow = tblBody.rows[i]; i++) {
            show_row = ShowTableRow(tblRow, tblName_settings)
            show_row = true
            add_or_remove_class(tblRow, cls_hide, !show_row)
        }
    }; // Filter_TableRows

//========= ShowTableRow  ==================================== PR2020-08-17
    function ShowTableRow(tblRow, tblName_settings) {
        // only called by Filter_TableRows
        //console.log( "===== ShowTableRow  ========= ");
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

        selected_student_pk = null;
        selected_school_depbases = [];
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
// +++++++++++++++++ MODAL SELECT EXAMYEAR, SCHOOL OR DEPARTMENT ++++++++++++++++++++
// functions are in table.js, except for MSESD_Response

//=========  MSESD_Response  ================ PR2020-12-18
    function MSESD_Response(tblName, pk_int) {
        console.log( "===== MSESD_Response ========= ");
        console.log( "tblName", tblName);
        console.log( "pk_int", pk_int);

// ---  upload new setting
        let new_setting = {page_grade: {mode: "get"}};
        if (tblName === "school") {
            new_setting.selected_pk = {sel_schoolbase_pk: pk_int, sel_depbase_pk: null}
        } else {
            new_setting.selected_pk = {sel_depbase_pk: pk_int}
        }
        const datalist_request = {setting: new_setting};

// also retrieve the tables that have been changed because of the change in school / dep
        datalist_request.student_rows = {get: true};
        datalist_request.studentsubject_rows = {get: true};
        datalist_request.grade_rows = {get: true};

        DatalistDownload(datalist_request);

    }  // MSESD_Response

//=========  MSSS_Response  ================ PR2021-01-23 PR2021-02-05
    function MSSS_Response(tblName, selected_pk, selected_code, selected_name) {
        console.log( "===== MSSS_Response ========= ");
        console.log( "selected_pk", selected_pk);
        //console.log( "selected_code", selected_code);
        console.log( "selected_name", selected_name);

        if (tblName === "MAG_subject") {
            // when called by modal approve grade: put new subject in textbox
            el_MAG_subject.innerText = selected_name
        } else {
        // ---  upload new setting
            if(selected_pk === -1) { selected_pk = null};
            const upload_dict = {};
            if (tblName === "subject") {
                upload_dict.selected_pk = {sel_subject_pk: selected_pk};
                setting_dict.sel_subject_pk = selected_pk;
            } else if (tblName === "student") {
                upload_dict.selected_pk = {sel_student_pk: selected_pk};
                setting_dict.sel_student_pk = selected_pk;
            }
            UploadSettings (upload_dict, url_settings_upload);
            MSSS_display_in_sbr()
        // ---  fill datatable
            FillTblRows();
        }
    }  // MSSS_Response

//========= MSSS_display_in_sbr  ====================================
    function MSSS_display_in_sbr() {
        console.log( "===== MSSS_display_in_sbr  ========= ");

        console.log( "setting_dict ", setting_dict);
        let student_text = "",  subject_text = "";

        const sel_subject_pk = (setting_dict.sel_subject_pk) ? setting_dict.sel_subject_pk : null;

        console.log( "selected_subject_pk ", selected_subject_pk);
        if(sel_subject_pk){
            const dict = get_mapdict_from_datamap_by_tblName_pk(subject_map, "subject", sel_subject_pk);
            subject_text =  (dict.name) ? dict.name : "---"
        } else {
            subject_text = "<" + loc.All_subjects + ">";
        }

        const sel_student_pk = (setting_dict.sel_student_pk) ? setting_dict.sel_student_pk : null;
        if(sel_student_pk){
            const dict = get_mapdict_from_datamap_by_tblName_pk(student_map, "student", sel_student_pk);
            student_text = (dict.fullname) ? dict.fullname : "---"

        } else {
            student_text = "<" + loc.All_candidates + ">";
        }

        const header_text = (sel_subject_pk) ? subject_text : (sel_student_pk) ? student_text : loc.All_subjects_and_candidates;

        el_SBR_select_student.value = student_text;
        el_SBR_select_subject.value = subject_text;
        document.getElementById("id_hdr_left").innerText = header_text

    }; // MSSS_display_in_sbr

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


//>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
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


//========= ModalStatus_FillNotes============== PR2020-10-15
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
        let permit_add_notes = true;
        if(permit_add_notes){
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
        const err_list = loc.grade_err_list
        const is_score = (["pescore", "cescore"].indexOf(fldName) > -1);
        const is_grade = (["segrade", "pegrade", "cegrade"].indexOf(fldName) > -1);
        //const is_se = (fldName === "segrade");
        const is_pe_or_ce = (["pescore", "pegrade", "cescore", "cegrade"].indexOf(fldName) > -1);
        //console.log("is_score", is_score, "is_grade", is_grade)
// 1. reset output parameters
        let output_text = null, msg_err = null;
// 2. exit als strInputValue  niet ingevuld (strMsgText = vbNullString, geen foutmelding)
        if(value){
// 3. exit als kandidaat is vergrendeld 'PR2016-03-27
            if (dict.ey_locked) { msg_err = err_list.examyear_locked} else
            if (dict.school_locked) { msg_err = err_list.school_locked} else
            if (dict.stud_locked) {msg_err = err_list.candidate_locked};

            if(!msg_err){
    // 4. exit als dit vak bewijs van kennis heeft. Dan is invoer gegevens geblokkeerd. Ga naar Rpt_Ex6_BewijsKennis om Bewijs van Kennis te wissen. 'PR2017-01-04
            // PR2010-06-10 mail Lorraine Wieske: kan geen PE cjfers corrigeren. Weghalen
            //If KvHasBewijsKennis Then
            //    strMsgText = "Vak heeft Bewijs van Kennis en is daarom vergrendeld." & vbCrLf & "Ga naar Rapportages Ex6 om Bewijs van Kennis zo nodig te wissen."
    // 5. exit als VakSchemaItemID niet ingevuld
            // not possible because of foreign key required

    // 6. Corona: check if no_centralexam
                if (is_pe_or_ce) {
                    if(dict.no_centralexam) {
                        msg_err = err_list.no_ce_this_ey;
                    } else if(dict.no_thirdperiod) {
    // 6. Corona: check if no_thirdperiod
                        msg_err = err_list.no_3rd_period;
                    }
                } else if(dict.is_combi){
    // 6. Corona: reexamination not allowed for combination subjects, except when combi_reex_allowed
                    if([2, 3].indexOf(dict.examperiod) > -1) {
                        if(!combi_reex_allowed){
                            msg_err = err_list.reex_combi_notallowed;
                        }
                    }
                }
            }
            if(!msg_err){
    // 6. afterCorona: check if exemption has no_centralexam,  PR2020-12-16
                // skip when iseveningstudent school or islexschool
                if(dict.examperiod === 4) {
                    if(is_pe_or_ce && dict.no_exemption_ce) {
                        if(!dict.iseveningstudent && !islexschool) {
                            msg_err = err_list.exemption_no_ce;
                        }
                    }
                }
            }
            if(!msg_err){
        // 6. controleer Praktijkexamen 'PR2019-02-22 'PR2015-12-08
                //wordt ook ingesteld buiten deze functie, in Form_K_BL_Resultaten.Form_Current en Form_C_CL_Resultaten.Form_Current  'PR2016-03-04
                if (fldName === "pegrade") {
                    if(dict.no_practexam) {
                        msg_err = err_list.no_pe_examyear;
                    } else if (!dict.has_practexam) {
                        msg_err = err_list.subject_no_pe;
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

            if(!msg_err){
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
                            msg_err = caption +  err_list.notallowed_in_combi;
                        } else if([2, 3].indexOf(dict.examperiod) > -1) {
                            // 'PR2020-05-15 Corona: herkansing wel mogelijk bij combivakken
                            if(!combi_reex_allowed){
                                msg_err = err_list.reex_notallowed_in_combi;
                            }
                        }
                    }
                }
            }
            if(!msg_err){
    // 8. controleer weging
                if (fldName === "segrade") {
                    if (!dict.weight_se) {
                        msg_err = err_list.weightse_is_0;
                    }
                } else if (["pescore", "cescore", "pegrade", "cegrade"].indexOf(fldName) > -1){
                    if (!dict.weight_ce) {
                        if (is_score){
                            msg_err = err_list.weightce_0_noscore;
                        } else {
                            msg_err = err_list.weightce_0_nograde;
                        }
                    }
                }
            }
            if(!msg_err){
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
                        msg_err = err_list.score_mustbe_number;
                    } else if (value_number < 0) {
                        msg_err = err_list.score_mustbe_gt0; // "Score moet een getal groter dan nul zijn."
                    } else if (value_number % 1 !== 0 ) {
                        // the remainder / modulus operator (%) returns the remainder after (integer) division.
                        msg_err = err_list.score_mustbe_wholenumber;
                    }
                    // TODO check if score is within scalelength of norm

                    if (! msg_err ) {output_text = value_number.toString()};
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
                            msg_err = err_list.gradetype_none;//  "Cijfertype 'Geen cijfer'. Er kan geen cijfer ingevuld worden." 'PR2016-02-14
                        } else if (dict.gradetype === 2) {  //GRADETYPE_02_CHARACTER = 2  # goed / voldoende / onvoldoende
                            const value_lc = value.toLowerCase();
                            if (!["o", "v", "g"].includes(value_lc)){
                                msg_err = err_list.gradetype_ovg;  //"Het cijfer kan alleen g, v of o zijn."
                            } else {
                                output_text = value_lc;
                            }
                        } else if (dict.gradetype === 1) {  //GRADETYPE_01_NUMBER = 1
                            // GetNumberFromInputGrade wordt alleen gebruikt om te controleren of cijfer een correct getal is, strMsgText<>"" als fout   'PR2016-03-04
                            const arr = GetNumberFromInputGrade(loc, value);
                            output_text = arr[0];
                            msg_err = arr[1];
                        }
                    }  //   if (["segrade",
                }
        }  // if(value)

        console.log("output_text", output_text)
        console.log("msg_err", msg_err)
       return [output_text, msg_err]
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
                msg_err = loc.Grade +  " '" + imput_trim + "' " + err_list.is_not_allowed + "\n" +err_list.Grade_mustbe_between_1_10
            } else {
// 7. zet strCijfer om in Currency (crcCijfer is InputCijfer * 10 bv: 5,6 wordt 56 en .2 wordt 2
                let input_number = Number(input_with_dots);
// 8. replace '67' bij '6.7', only when it has no decimal places and is between 11 thru 99
                // the remainder / modulus operator (%) returns the remainder after (integer) division.
                if (input_number % 1 === 0  && input_number > 10  && input_number < 100  ) {
                    input_number = input_number / 10;
                }
            console.log(">>>>>>>> input_number", input_number)
// 8. exit als crcCijfer < 10 of als  crcCijfer > 100
                // allowed numbers are: 1 thru 10, with 1 decimal
                 if(input_number < 1 || input_number > 10){
                     msg_err = loc.Grade +  " '" + imput_trim + "' " + err_list.is_not_allowed + "\n" +err_list.Grade_mustbe_between_1_10
                } else {
// 10. exit als more than 1 digit after the dot.
                    // multiply by 10, get remainder after division by 1, check if remainder has value
                    // the remainder / modulus operator (%) returns the remainder after (integer) division.
                    if ((input_number * 10) % 1) {
                        msg_err = loc.Grade +  " '" + imput_trim + "' " + err_list.is_not_allowed + "\n" +err_list.Grade_may_only_have_1_decimal
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
// 11.reurn array with output number and msg_err
        console.log("output_text", output_text)
        console.log("msg_err", msg_err)
        return [output_text, msg_err]
    }  // GetNumberFromInputGrade

//###########################################################################

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