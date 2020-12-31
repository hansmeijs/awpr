// PR2020-09-29 added
document.addEventListener('DOMContentLoaded', function() {
    "use strict";

console.log("document.addEventListener students" )
    // <PERMIT> PR220-10-02
    //  - can view page: only 'role_school', 'role_insp', 'role_admin', 'role_system'
    //  - can add/delete/edit only 'role_admin', 'role_system' plus 'perm_write'
    //  roles are:   'role_student', 'role_teacher', 'role_school', 'role_insp', 'role_admin', 'role_system'
    //  permits are: 'perm_read', 'perm_write', 'perm_auth1', 'perm_auth2', 'perm_docs', 'perm_admin', 'perm_system'

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
    let selected_period = {};
    let setting_dict = {};

    let selected_student_pk = null;
    let selected_subject_pk = null;

    let loc = {};  // locale_dict
    let mod_dict = {};
    let mod_MSTUD_dict = {};
    let mod_MSSS_dict = {};

    let mod_MSTUDSUBJ_dict = {}; // stores general info of selected candidate in MSTUDSUBJ PR2020-11-21
    //let mod_studsubj_dict = {};  // stores studsubj of selected candidate in MSTUDSUBJ
    //let mod_schemeitem_dict = {};   // stores available studsubj for selected candidate in MSTUDSUBJ
    let mod_studsubj_map = new Map();  // stores studsubj of selected candidate in MSTUDSUBJ
    let mod_schemeitem_map = new Map();

    let time_stamp = null; // used in mod add user

    let user_list = [];
    let examyear_map = new Map();
    let school_map = new Map();
    let department_map = new Map();
    let level_map = new Map();
    let sector_map = new Map();
    let student_map = new Map();
    let subject_map = new Map();
    let grade_map = new Map()
    let schemeitem_map = new Map()

    let filter_dict = {};
    let filter_mod_employee = false;

    let el_focus = null; // stores id of element that must get the focus after cloosing mod message PR2020-12-20


// --- get data stored in page
    let el_data = document.getElementById("id_data");
    const url_datalist_download = get_attr_from_el(el_data, "data-datalist_download_url");
    const url_settings_upload = get_attr_from_el(el_data, "data-settings_upload_url");
    const url_subject_upload = get_attr_from_el(el_data, "data-subject_upload_url");
    const url_studsubj_upload = get_attr_from_el(el_data, "data-studsubj_upload_url");
    const url_grade_upload = get_attr_from_el(el_data, "data-grade_upload_url");
    const url_subject_import = get_attr_from_el(el_data, "data-subject_import_url");

// --- get field_settings
    const columns_shown = {examnumber: true, fullname: true, subj_code: true, subj_name: true,
                           pescore: false, cescore: false, segrade: true, pegrade: false, cegrade: false,
                            pecegrade: false, finalgrade: false}
    const field_settings = {
        grades: { field_caption: ["Ex_nr", "Candidate", "Abbreviation", "Subject",
                             "PE_score", "CE_score", "SE_grade", "PE_grade",
                             "CE_grade", "PECE_grade", "Final_grade"],
                    field_names: ["examnumber", "fullname",  "subj_code", "subj_name",
                             "pescore", "cescore", "segrade", "pegrade", "cegrade", "pecegrade", "finalgrade"],
                    field_tags: ["div", "div", "div", "div", "input", "input", "input", "input", "input", "div", "div"],
                    filter_tags: ["text", "text", "text", "text", "text", "text", "text", "text", "text", "text", "text"],
                    field_width:  ["100", "240", "100", "120", "075", "075", "075", "075", "075", "075", "075"],
                     field_align: ["r", "l", "l", "l", "l", "l", "l", "l", "l", "l", "l"]},
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
            el_hdrbar_examyear.addEventListener("click", function() {ModSelectExamyear_Open()}, false )
        const el_hdrbar_school = document.getElementById("id_hdrbar_school")
            el_hdrbar_school.addEventListener("click", function() {
                t_MSESD_Open(loc, "school", school_map, setting_dict, MSESD_Response)}, false )
        const el_hdrbar_department = document.getElementById("id_hdrbar_department")
            el_hdrbar_department.addEventListener("click", function() {
                t_MSESD_Open(loc, "department", department_map, setting_dict, MSESD_Response)}, false )

// --- side bar elements
        const el_SBR_select_examperiod = document.getElementById("id_SBR_select_period");
            el_SBR_select_examperiod.addEventListener("change", function() {HandleSbrPeriod(el_SBR_select_examperiod)}, false )
        const el_SBR_select_examtype = document.getElementById("id_SBR_select_examtype");
            el_SBR_select_examtype.addEventListener("change", function() {HandleSbrExamtype(el_SBR_select_examtype)}, false )
        const el_SBR_select_subject = document.getElementById("id_SBR_select_subject");
            el_SBR_select_subject.addEventListener("click", function() {MSSS_Open("subject")}, false )
        const el_SBR_select_student = document.getElementById("id_SBR_select_student");
            el_SBR_select_student.addEventListener("click", function() {MSSS_Open("student")}, false )
        const el_SBR_select_showall = document.getElementById("id_SBR_select_showall");
            el_SBR_select_showall.addEventListener("click", function() {HandleShowAll()}, false )

// ---  MOD SELECT EXAM YEAR ------------------------------------
        let el_MSEY_tblBody_select = document.getElementById("id_MSEY_tblBody_select");
        const el_SBR_filter = document.getElementById("id_SBR_filter")
        //    el_SBR_filter.addEventListener("keyup", function() {MSTUD_InputKeyup(el_SBR_filter)}, false );

// ---  MSSS MOD SELECT SUBJECT / STUDENT ------------------------------
        const el_MSSS_input = document.getElementById("id_MSSS_input")
            el_MSSS_input.addEventListener("keyup", function(event){
                setTimeout(function() {MSSS_InputKeyup()}, 50)});
        const el_MSSS_tblBody = document.getElementById("id_MSSS_tbody_select");
        const el_MSSS_btn_save = document.getElementById("id_MSSS_btn_save")
            el_MSSS_btn_save.addEventListener("click", function() {MSSS_Save()}, false )

// ---  MODAL STUDENT
        const el_MSTUD_div_form_controls = document.getElementById("id_MSTUD_div_form_controls")
        let form_elements = el_MSTUD_div_form_controls.querySelectorAll(".awp_input_text")
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

// ---  MODAL STUDENT SUBJECTS
        const el_MSTUDSUBJ_hdr = document.getElementById("id_MSTUDSUBJ_hdr")
        const el_MSTUDSUBJ_btn_add_selected = document.getElementById("id_MSTUDSUBJ_btn_add_selected")
            el_MSTUDSUBJ_btn_add_selected.addEventListener("click", function() {MSTUDSUBJ_AddRemoveSubjct("add")}, false);
        const el_MSTUDSUBJ_btn_remove_selected = document.getElementById("id_MSTUDSUBJ_btn_remove_selected")
            el_MSTUDSUBJ_btn_remove_selected.addEventListener("click", function() {MSTUDSUBJ_AddRemoveSubjct("remove")}, false);
        const el_MSTUDSUBJ_btn_add_package = document.getElementById("id_MSTUDSUBJ_btn_add_package")
            el_MSTUDSUBJ_btn_add_package.addEventListener("click", function() {MSTUDSUBJ_AddPackage()}, false);

        const el_input_controls = document.getElementById("id_MSTUDSUBJ_div_form_controls").querySelectorAll(".awp_input_text, .awp_input_checkbox")
        for (let i = 0, el; el = el_input_controls[i]; i++) {
            const key_str = (el.classList.contains("awp_input_checkbox")) ? "change" : "keyup";
            el.addEventListener(key_str, function() {MSTUDSUBJ_InputboxEdit(el)}, false)
        }

        const el_MSTUDSUBJ_btn_save = document.getElementById("id_MSTUDSUBJ_btn_save")
            el_MSTUDSUBJ_btn_save.addEventListener("click", function() {MSTUDSUBJ_Save()}, false);

        const el_tblBody_studsubjects = document.getElementById("id_tblBody_studsubjects");
        const el_tblBody_schemeitems = document.getElementById("id_tblBody_schemeitems");

// ---  MOD CONFIRM ------------------------------------
        let el_confirm_header = document.getElementById("id_confirm_header");
        let el_confirm_loader = document.getElementById("id_confirm_loader");
        let el_confirm_msg_container = document.getElementById("id_confirm_msg_container")
        let el_confirm_msg01 = document.getElementById("id_confirm_msg01")
        let el_confirm_msg02 = document.getElementById("id_confirm_msg02")
        let el_confirm_msg03 = document.getElementById("id_confirm_msg03")

        let el_confirm_btn_cancel = document.getElementById("id_confirm_btn_cancel");
        let el_confirm_btn_save = document.getElementById("id_confirm_btn_save");
        if(has_view_permit){ el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()}) };

// ---  MOD MESSAGE ------------------------------------
        let el_mod_message_header = document.getElementById("id_mod_message_header");
        let el_mod_message_text = document.getElementById("id_mod_message_text");
        let el_modmessage_btn_cancel = document.getElementById("id_modmessage_btn_cancel");
            el_modmessage_btn_cancel.addEventListener("click", function() {ModMessageClose()}, false);

// ---  set selected menu button active
    SetMenubuttonActive(document.getElementById("id_hdr_users"));
    if(has_view_permit){
        // period also returns emplhour_list
        const datalist_request = {
                setting: {page_grade: {mode: "get"}},
                locale: {page: "grades"},
                examyear_rows: {get: true},
                school_rows: {get: true},
                department_rows: {get: true},
                subject_rows: {get: true},
                student_rows: {get: true},
                studentsubject_rows: {get: true},
                grade_rows: {get: true},
                level_rows: {get: true},
                sector_rows: {get: true},
                schemeitem_rows: {get: true}
            };

        DatalistDownload(datalist_request);
    }
//  #############################################################################################################

//========= DatalistDownload  ===================== PR2020-07-31
    function DatalistDownload(datalist_request) {
        console.log( "=== DatalistDownload ")
        console.log("request: ", datalist_request)

// ---  Get today's date and time - for elapsed time
        let startime = new Date().getTime();

// ---  show loader
        el_loader.classList.remove(cls_visible_hide)

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
                let call_DisplayCustomerOrderEmployee = true;

                if ("locale_dict" in response) { refresh_locale(response.locale_dict)};
                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict
                    // <PERMIT> PR220-10-02
                    //  - can view page: only 'role_school', 'role_insp', 'role_admin', 'role_system'
                    //  - can add/delete/edit only 'role_admin', 'role_system' plus 'perm_write'
                    has_permit_edit = (setting_dict.requsr_role_admin && setting_dict.requsr_perm_edit) ||
                                      (setting_dict.requsr_role_system && setting_dict.requsr_perm_edit);
                    // <PERMIT> PR2020-10-27
                    // - every user may change examyear and department
                    // -- only insp, admin and system may change school
                    has_permit_select_school = (setting_dict.requsr_role_insp ||
                                                setting_dict.requsr_role_admin ||
                                                setting_dict.requsr_role_system);
                    selected_btn = (setting_dict.sel_btn)

                    UpdateHeaderbar(loc, setting_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school );

                    const sel_examperiod_pk = setting_dict.sel_examperiod_pk;
                    t_FillOptionsFromList(el_SBR_select_examperiod, loc.options_examperiod, null,
                        loc.Select_examperiod, loc.No_examperiods_found, sel_examperiod_pk);

                    const sel_examtype_pk = setting_dict.sel_examtype_pk;
                    const filter_value = sel_examperiod_pk;
                    t_FillOptionsFromList(el_SBR_select_examtype, loc.options_examtype, filter_value,
                        loc.Select_examtype, loc.No_examtypes_found, sel_examtype_pk);

                    document.getElementById("id_hdr_textright1").innerText = setting_dict.sel_examperiod_caption
                };

                if ("examyear_rows" in response) { b_fill_datamap(examyear_map, response.examyear_rows) };
                if ("school_rows" in response)  { b_fill_datamap(school_map, response.school_rows) };
                if ("department_rows" in response) { b_fill_datamap(department_map, response.department_rows) };

                if ("level_rows" in response)  { b_fill_datamap(level_map, response.level_rows) };
                if ("sector_rows" in response) { b_fill_datamap(sector_map, response.sector_rows) };
                if ("subject_rows" in response) { b_fill_datamap(subject_map, response.subject_rows) };
                if ("student_rows" in response) { b_fill_datamap(student_map, response.student_rows) };
/*
                if ("student_rows" in response) {
                    const tblName = "student";
                    const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                    RefreshDataMap(tblName, field_names, response.student_rows, student_map)
                }
*/
                if ("grade_rows" in response)  {
                    b_fill_datamap(grade_map, response.grade_rows)
                    console.log("response.grade_rows: ", response.grade_rows)
                    console.log("grade_map: ", grade_map)
                };
                if ("schemeitem_rows" in response)  { b_fill_datamap(schemeitem_map, response.schemeitem_rows) };

                HandleBtnSelect(selected_btn, true)  // true = skip_upload

            },
            error: function (xhr, msg) {
// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                console.log(msg + '\n' + xhr.responseText);
                alert(msg + '\n' + xhr.responseText);
            }
        });
    }  // function DatalistDownload

//=========  refresh_locale  ================  PR2020-07-31
    function refresh_locale(locale_dict) {
        //console.log ("===== refresh_locale ==== ")
        loc = locale_dict;
        CreateSubmenu()
    }  // refresh_locale

//=========  CreateSubmenu  ===  PR2020-07-31
    function CreateSubmenu() {
        //console.log("===  CreateSubmenu == ");
        //console.log("loc.Add_subject ", loc.Add_subject);
        //console.log("loc ", loc);
/*
        let el_submenu = document.getElementById("id_submenu")
            AddSubmenuButton(el_submenu, loc.Add_candidate, function() {MSTUD_Open()});
            AddSubmenuButton(el_submenu, loc.Delete_candidate, function() {ModConfirmOpen("delete")}, ["mx-2"]);
            AddSubmenuButton(el_submenu, loc.Upload_candidates, null, ["mx-2"], "id_submenu_subjectimport", url_subject_import);

         el_submenu.classList.remove(cls_hide);
*/
    };//function CreateSubmenu

//###########################################################################
//=========  HandleBtnSelect  ================ PR2020-09-19  PR2020-11-14
    function HandleBtnSelect(data_btn, skip_upload) {
        console.log( "===== HandleBtnSelect ========= ", data_btn);
        selected_btn = data_btn
        if(!selected_btn){selected_btn = "btn_student"}

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
        const sel_examperiod_pk = (Number(el_select.value)) ? Number(el_select.value) : null;
        const filter_value = sel_examperiod_pk;

        console.log( "loc.options_examtype: ", loc.options_examtype)
// --- fill seelctbox examtype with examtypes of this period
        t_FillOptionsFromList(el_SBR_select_examtype, loc.options_examtype, filter_value,
            loc.Select_examtype, loc.No_examtypes_found);

// ---  upload new setting
        let new_setting = {page_grade: {mode: "get"}};
        new_setting.selected_pk = {sel_examperiod_pk: sel_examperiod_pk}
        const datalist_request = {setting: new_setting};

// also retrieve the tables that have been changed because of the change in school / dep
        datalist_request.grade_rows = {get: true};
        DatalistDownload(datalist_request);

    }  // HandleSbrPeriod

//=========  HandleSbrExamtype  ================ PR2020-12-20
    function HandleSbrExamtype(el_select) {
        console.log("=== HandleSbrExamtype");
        console.log( "el_select.value: ", el_select.value, typeof el_select.value)
        const selected_value = el_select.value;
        const filter_value = Number(el_select.value);
        t_FillOptionsFromList(el_SBR_select_examtype, loc.options_examtype, filter_value,
            loc.Select_examtype, loc.No_examtypes_found, selected_value);

// ---  upload new setting
        const upload_dict = {page_grade: {sel_btn: selected_btn}};
        UploadSettings (upload_dict, url_settings_upload);

    }  // HandleSbrExamtype

//=========  HandleShowAll  ================ PR2020-12-17
    function HandleShowAll() {
        console.log("=== HandleShowAll");
        selected_student_pk =  null;
        selected_subject_pk =  null;
        //MSSS_display_in_sbr();
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
        //console.log( "===== FillTblRows  === ");
        //console.log( "selected_student_pk", selected_student_pk);
        //console.log( "selected_subject_pk", selected_subject_pk);

        columns_shown.examnumber = (!selected_student_pk);
        columns_shown.fullname = (!selected_student_pk);
        columns_shown.subj_code = (!selected_subject_pk);
        columns_shown.subj_name = (!selected_subject_pk);

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

// --- create table header
        CreateTblHeader();

// --- loop through grade_map
        if(grade_map){
          for (const [map_id, map_dict] of grade_map.entries()) {
          // only show rows of selected student / subject

                let show_row = (!selected_student_pk || map_dict.student_id === selected_student_pk) &&
                               (!selected_subject_pk ||map_dict.subject_id === selected_subject_pk);
                if(show_row){
          // --- insert row at row_index
                    //const schoolcode_lc_trail = ( (map_dict.sb_code) ? map_dict.sb_code.toLowerCase() : "" ) + " ".repeat(8) ;
                    //const schoolcode_sliced = schoolcode_lc_trail.slice(0, 8);
                    //const order_by = schoolcode_sliced +  ( (map_dict.username) ? map_dict.username.toLowerCase() : "");
                    const row_index = -1; // t_get_rowindex_by_orderby(tblBody_datatable, order_by)
                    let tblRow = CreateTblRow(map_id, map_dict, row_index)
                }
          };
        }  // if(!!grade_map)

    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-12-03 PR2020-12-18
    function CreateTblHeader() {
        //console.log("===  CreateTblHeader ===== ");

        const tblName = "grades";
        const field_setting = field_settings[tblName];
        const column_count = field_setting.field_names.length;


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

            // skip columns if not in columns_shown
            if (columns_shown[field_name]){
    // ++++++++++ insert columns in header row +++++++++++++++
        // --- add th to tblRow_header +++
                let th_header = document.createElement("th");
        // --- add div to th, margin not working with th
                    const el_header = document.createElement("div");
                        el_header.innerText = caption;
        // --- add width, text_align, right padding in examnumber
                        el_header.classList.add(class_width, class_align);
                        if(field_name === "examnumber"){el_header.classList.add("pr-4")}
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
    function CreateTblRow(map_id, map_dict, row_index) {
        //console.log("=========  CreateTblRow =========", tblName);
        //console.log("map_dict", map_dict);

        const tblName = "grades";

        const field_setting = field_settings[tblName]
        const field_names = field_setting.field_names;
        const field_tags = field_setting.field_tags;
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;

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
                        }

        // --- add class 'input_text' and text_align
                        // class 'input_text' contains 'width: 100%', necessary to keep input field within td width
                        el.classList.add("input_text", "ta_" + field_setting.field_align[j]);
                        if(field_name === "examnumber"){el.classList.add("pr-4")}

                    td.appendChild(el);
               if (["examnumber", "fullname"].indexOf(field_name) > -1){
                    td.addEventListener("click", function() {MSTUD_Open(td)}, false)
                    add_hover(td);
               } else if (["subj_code", "subj_name"].indexOf(field_name) > -1){
                    td.addEventListener("click", function() {MSTUDSUBJ_Open(td)}, false)
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
        console.log("=========  UpdateField =========");
        console.log("map_dict", map_dict);
        if(el){
            const field_name = get_attr_from_el(el, "data-field");
            const fld_value = map_dict[field_name];
        console.log("field_name", field_name);
        console.log("fld_value", fld_value);
            if (el.nodeName === "INPUT"){
                 el.value = (fld_value) ? fld_value : null;
            } else {
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
                const value_text = arr[0];
                const msg_err = arr[1];
                if (msg_err){
                    //alert(msg_err)
    // ---  show modal
                    // TODO header, set focus after clsing messagebox
                    // el_mod_message_header.innerText = loc.Enter_grade;
                    el_mod_message_text.innerText = msg_err;
                    $("#id_mod_message").modal({backdrop: false});
                    set_focus_on_el_with_timeout(el_modmessage_btn_cancel, 150 )

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

                                           sel_examyear_pk: setting_dict.sel_examyear_pk,
                                           sel_schoolbase_pk: setting_dict.sel_schoolbase_pk,
                                           sel_depbase_pk: setting_dict.sel_depbase_pk,
                                           sel_examperiod_pk: setting_dict.sel_examperiod_pk,

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

//========= UploadToggle  ============= PR2020-07-31
    function UploadToggle(el_input) {
        //console.log( " ==== UploadToggle ====");

        mod_dict = {};
        const tblRow = get_tablerow_selected(el_input);
        if(tblRow){
            const tblName = get_attr_from_el(tblRow, "data-table")
            const map_id = tblRow.id
            const map_dict = get_mapdict_from_datamap_by_id(subject_map, map_id);

            if(!isEmpty(map_dict)){
                const fldName = get_attr_from_el(el_input, "data-field");
                let permit_value = get_attr_from_el_int(el_input, "data-value");
                let has_permit = (!!permit_value);

                const requsr_pk = get_dict_value(selected_period, ["requsr_pk"])
                const is_request_user = (requsr_pk === map_dict.id)

// show message when sysadmin tries to delete sysadmin permit or add readonly
                if(fldName === "perm64_sysadmin" && is_request_user && has_permit ){
                    ModConfirmOpen("permission_sysadm", el_input)
                } else if(fldName === "perm01_readonly" && is_request_user && !has_permit ){
                    ModConfirmOpen("permission_sysadm", el_input)
                } else {
// loop through row cells to get value of permissions.
                    // Don't get them from map_dict, might not be correct while changing permissions
                    let new_permit_sum = 0, new_permit_value = 0
                    for (let i = 0, cell, cell_name, cell_value; cell = tblRow.cells[i]; i++) {
                        cell_name = get_attr_from_el(cell, "data-field");
                        if (cell_name.slice(0, 4) === "perm") {
                            cell_value = get_attr_from_el_int(cell, "data-value");
                // toggle value of clicked field
                            if (cell_name === fldName){
                                if(cell_value){
                                    cell_value = 0;
                                } else {
                                    const cell_permit = fldName.slice(4, 6);
                                    cell_value = (Number(cell_permit)) ? Number(cell_permit) : 0;
                                }
                                new_permit_value = cell_value;
                // put new value in cell attribute 'data-value'
                                cell.setAttribute("data-value", new_permit_value)
                            };
                            new_permit_sum += cell_value              }
                    }

// ---  change icon, before uploading
                    let el_icon = el_input.children[0];
                    if(el_icon){add_or_remove_class (el_icon, "tickmark_0_2", new_permit_value)};

// ---  upload changes
                    const upload_dict = { id: {pk: map_dict.id,
                                               ppk: map_dict.company_id,
                                               table: "user",
                                               mode: "update",
                                               mapid: map_id},
                                          permits: {value: new_permit_sum, update: true}};
                    UploadChanges(upload_dict, url_subject_upload);
                }
            }  //  if(!isEmpty(map_dict)){
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
        if( has_permit_edit){
            let user_pk = null, user_country_pk = null, user_schoolbase_pk = null, mapid = null;
            const fldName = get_attr_from_el(el_input, "data-field");

            // el_input is undefined when called by submenu btn 'Add new'
            const is_addnew = (!el_input);
            mod_MSTUD_dict = {}
            let tblName = "student";
            if(is_addnew){
                mod_MSTUD_dict = {is_addnew: is_addnew}
            } else {
                const tblRow = get_tablerow_selected(el_input);
                const map_dict = get_mapdict_from_datamap_by_id(student_map, tblRow.id);
                mod_MSTUD_dict = deepcopy_dict(map_dict);
            }
            console.log("mod_MSTUD_dict", mod_MSTUD_dict)
    // ---  set header text
            MSTUD_headertext(is_addnew, tblName, mod_MSTUD_dict.name);

    // ---  remove value from el_mod_employee_input
            MSTUD_SetElements();  // true = also_remove_values

            if (!is_addnew){
                //el_MSTUD_abbrev.value = (mod_MSTUD_dict.abbrev) ? mod_MSTUD_dict.abbrev : null;
                //el_MSTUD_name.value = (mod_MSTUD_dict.name) ? mod_MSTUD_dict.name : null;
                //el_MSTUD_sequence.value = (mod_MSTUD_dict.sequence) ? mod_MSTUD_dict.sequence : null;
               // el_MSTUD_sequence.value = mod_MSTUD_dict.sequence;

                const modified_dateJS = parse_dateJS_from_dateISO(mod_MSTUD_dict.modifiedat);
                const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
                const modified_by = (mod_MSTUD_dict.modby_username) ? mod_MSTUD_dict.modby_username : "-";

                document.getElementById("id_MSTUD_msg_modified").innerText = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by
            }

    // ---  set focus to el_MSTUD_abbrev
            //setTimeout(function (){el_MSTUD_abbrev.focus()}, 50);

    // ---  disable btn submit, hide delete btn when is_addnew
           // add_or_remove_class(el_MSTUD_btn_delete, cls_hide, is_addnew )
            //const disable_btn_save = (!el_MSTUD_abbrev.value || !el_MSTUD_name.value || !el_MSTUD_sequence.value )
            //el_MSTUD_btn_save.disabled = disable_btn_save;

            //MSTUD_validate_and_disable();

    // ---  show modal
            $("#id_mod_student").modal({backdrop: true});
        }
    };  // MSTUD_Open

//=========  MSTUD_Save  ================  PR2020-10-01
    function MSTUD_Save(crud_mode) {
        console.log(" -----  MSTUD_save  ----", crud_mode);
        console.log( "mod_MSTUD_dict: ", mod_MSTUD_dict);

        if(has_permit_edit){
            const is_delete = (crud_mode === "delete")

            let upload_dict = {id: {table: 'subject', ppk: mod_MSTUD_dict.examyear_id} }
            if(mod_MSTUD_dict.is_addnew) {
                upload_dict.id.create = true;
            } else {
                upload_dict.id.pk = mod_MSTUD_dict.id;
                upload_dict.id.mapid = mod_MSTUD_dict.mapid;
                if(is_delete) {upload_dict.id.delete = true}
            }
    // ---  put changed values of input elements in upload_dict
            let form_elements = document.getElementById("id_MSTUDSUBJ_div_form_controls").querySelectorAll(".awp_input_text")
            for (let i = 0, el_input; el_input = form_elements[i]; i++) {
                const fldName = get_attr_from_el(el_input, "data-field");
    //console.log( "fldName: ", fldName);
                let new_value = (el_input.value) ? el_input.value : null;
                let old_value = (mod_MSTUD_dict[fldName]) ? mod_MSTUD_dict[fldName] : null;
    //console.log( "new_value: ", new_value);
    //console.log( "old_value: ", old_value);
                if(fldName === "sequence"){
                    new_value = (new_value && Number(new_value)) ? Number(new_value) : null;
                    old_value = (old_value && Number(old_value)) ? Number(old_value) : null;
                }
                if (new_value !== old_value) {
                    upload_dict[fldName] = {value: new_value, update: true}

    // put changed new value in tblRow before uploading
                    const tblRow = document.getElementById(mod_MSTUD_dict.mapid);
                    if(tblRow){
                        const el_tblRow = tblRow.querySelector("[data-field=" + fldName + "]");
                        if(el_tblRow){el_tblRow.innerText = new_value };
                    }
                };
            };
    // ---  get selected departments
            let dep_list = MSTUD_get_selected_depbases();

            upload_dict['depbases'] = {value: dep_list, update: true}
            // TODO add loader
            //document.getElementById("id_MSTUD_loader").classList.remove(cls_visible_hide)
            // modal is closed by data-dismiss="modal"
            UploadChanges(upload_dict, url_subject_upload);
        };
    }  // MSTUD_Save


//========= MSTUD_get_selected_depbases  ============= PR2020-10-07
    function MSTUD_get_selected_depbases(){
        console.log( "  ---  MSTUD_get_selected_depbases  --- ")
        const tblBody_select = document.getElementById("id_MSTUD_tblBody_department");
        let dep_list = [];
        // TODO depbase cannot be changed
        /*
        for (let i = 0, row; row = tblBody_select.rows[i]; i++) {
            let row_pk = get_attr_from_el_int(row, "data-pk");
            // skip row 'select_all'
            if(row_pk){
                if(!!get_attr_from_el_int(row, "data-selected")){
                    dep_list.push(row_pk);
                }
            }
        }
        */
        return dep_list;
    }  // MSTUD_get_selected_depbases

//========= MSTUD_InputKeyup  ============= PR2020-10-01
    function MSTUD_InputKeyup(el_input){
        //console.log( "===== MSTUD_InputKeyup  ========= ");
        MSTUD_validate_and_disable();
    }; // MSTUD_InputKeyup

//=========  MSTUD_validate_and_disable  ================  PR2020-10-01
    function MSTUD_validate_and_disable() {
        console.log(" -----  MSTUD_validate_and_disable   ----")
        let disable_save_btn = false;
// ---  loop through input fields on MSTUD_Open
        let form_elements = el_MSTUD_div_form_controls.querySelectorAll(".awp_input_text")
        for (let i = 0, el_input; el_input = form_elements[i]; i++) {
            const fldName = get_attr_from_el(el_input, "data-field")
            const  msg_err = MSTUD_validate_field(el_input, fldName)
// ---  show / hide error message
            const el_msg = document.getElementById("id_MSTUD_msg_" + fldName);
            if(el_msg){
                el_msg.innerText = msg_err;
                disable_save_btn = true;
                add_or_remove_class(el_msg, cls_hide, !msg_err)
            }

        };

// ---  disable save button on error
        el_MSTUD_btn_save.disabled = disable_save_btn;
    }  // MSTUD_validate_and_disable

//=========  MSTUD_validate_field  ================  PR2020-10-01
    function MSTUD_validate_field(el_input, fldName) {
        console.log(" -----  MSTUD_validate_field   ----")
        let msg_err = null;
        if (el_input){
            const value = el_input.value;
            if(["sequence"].indexOf(fldName) > -1){
                const arr = get_number_from_input(loc, fldName, el_input.value);
                msg_err = arr[1];
            } else {
                 const caption = (fldName === "abbrev") ? loc.Abbreviation :
                                (fldName === "name") ? loc.Name  : loc.This_field;
                if (["abbrev", "name"].indexOf(fldName) > -1 && !value) {
                    msg_err = caption + loc.cannot_be_blank;
                } else if (["abbrev"].indexOf(fldName) > -1 && value.length > 10) {
                    msg_err = caption + loc.is_too_long_MAX10;
                } else if (["name"].indexOf(fldName) > -1 &&
                    value.length > 50) {
                        msg_err = caption + loc.is_too_long_MAX50;
                } else if (["abbrev", "name"].indexOf(fldName) > -1) {
                        msg_err = validate_duplicates_in_department(loc, "subject", fldName, caption, mod_MSTUD_dict.mapid, value)
                }
            }
        }
        return msg_err;
    }  // MSTUD_validate_field

//=========  validate_duplicates_in_department  ================ PR2020-09-11
    function validate_duplicates_in_department(loc, tblName, fldName, caption, selected_mapid, selected_code) {
        //console.log(" =====  validate_duplicates_in_department =====")
        //console.log("fldName", fldName)
        let msg_err = null;
        if (tblName && fldName && selected_code){
            const data_map = (tblName === "subject") ? subject_map : null;
            if (data_map && data_map.size){
                const selected_code_lc = selected_code.trim().toLowerCase()
    //--- loop through subjects
                for (const [map_id, map_dict] of data_map.entries()) {
                    // skip current item
                    if(map_id !== selected_mapid) {
                        const lookup_value = (map_dict[fldName]) ? map_dict[fldName].trim().toLowerCase() : null;
                        if(lookup_value && lookup_value === selected_code_lc){
                            console.log(" =====  validate_duplicates_in_department =====")

                            // check if they have at least one department in common
                            let depbase_in_common = false;
                            const selected_depbases = MSTUD_get_selected_depbases();
                            const lookup_departments = map_dict.depbases;
                            console.log("selected_depbases", selected_depbases)
                            console.log("lookup_departments", lookup_departments)
                            if(selected_depbases && lookup_departments){
                                selected_depbases.forEach((sel_dep_pk, i) => {
                                    lookup_departments.forEach((lookup_dep_pk, j) => {
                                        if (sel_dep_pk === lookup_dep_pk){depbase_in_common = true}
                                    });
                                });
                            }
                            if(depbase_in_common){
                                msg_err = caption + " '" + selected_code + "'" + loc.already_exists_in_departments
                                break;
                            }
                        }
                    }
                }
            }
        };
        return msg_err;
    }  // validate_duplicates_in_department

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

//========= MSTUD_SetMsgElements  ============= PR2020-08-02
    function MSTUD_SetMsgElements(response){
        console.log( "===== MSTUD_SetMsgElements  ========= ");

        const err_dict = ("msg_err" in response) ? response.msg_err : {}
        const validation_ok = get_dict_value(response, ["validation_ok"], false);

        console.log( "err_dict", err_dict);
        console.log( "validation_ok", validation_ok);

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
            show_hide_selected_elements_byClass("tab_show", "tab_ok");

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
                show_hide_selected_elements_byClass("tab_show", "tab_ok");

            } else {
                const fields = ["username", "last_name", "email"]
                for (let i = 0, field; field = fields[i]; i++) {
                    const msg_err = get_dict_value(err_dict, [field]);
                    const msg_info = loc.msg_user_info[i];

                    let el_input = document.getElementById("id_MSTUD_" + field);
                    add_or_remove_class (el_input, "border_bg_invalid", (!!msg_err));
                    add_or_remove_class (el_input, "border_bg_valid", (!msg_err));

                    let el_msg = document.getElementById("id_MSTUD_msg_" + field);
                    add_or_remove_class (el_msg, "text-danger", (!!msg_err));
                    el_msg.innerText = (!!msg_err) ? msg_err : msg_info
                }
            }
            el_MSTUD_btn_save.disabled = !validation_ok;
            if(validation_ok){el_MSTUD_btn_save.focus()}
        }
// ---  show message in footer when no error and no ok msg
        add_or_remove_class(el_MUA_info_footer01, cls_hide, !validation_ok )
        add_or_remove_class(el_MUA_info_footer02, cls_hide, !validation_ok )

// ---  set text on btn cancel
        const el_MUA_btn_cancel = document.getElementById("id_MUA_btn_cancel");
        el_MUA_btn_cancel.innerText = ((is_ok || err_save) ? loc.Close: loc.Cancel);
        if(is_ok || err_save){el_MUA_btn_cancel.focus()}

    }  // MUA_SetMsgElements

//========= MSTUD_headertext  ======== // PR2020-09-30
    function MSTUD_headertext(is_addnew, tblName, name) {
        //console.log(" -----  MSTUD_headertext   ----")
        //console.log("tblName", tblName, "is_addnew", is_addnew)

        let header_text = (tblName === "subject") ? (is_addnew) ? loc.Add_subject : loc.Subject :
                    (tblName === "level") ? (is_addnew) ? loc.Add_level : loc.Level :
                    (tblName === "sector") ? (is_addnew) ? loc.Add_sector : loc.Sector :
                    (tblName === "subjecttype") ? (is_addnew) ? loc.Add_subjecttype : loc.Subjecttype :
                    (tblName === "scheme") ? (is_addnew) ? loc.Add_scheme : loc.Scheme :
                    (tblName === "schemeitem") ? (is_addnew) ? loc.Add_schemeitem : loc.Schemeitem :
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
                    (tblName === "schemeitem") ? loc.this_schemeitem :
                    (tblName === "package") ? loc.this_package :
                    (tblName === "packageitem") ?  loc.this_package_item : "---";
        //document.getElementById("id_MSTUD_label_dep").innerText = loc.Departments_where + this_dep_text + loc.occurs + ":";
    }  // MSTUD_headertext

// +++++++++ END MOD STUDENT +++++++++++++++++++++++++++++++++++++++++


// +++++++++ MOD STUDENT SUBJECT++++++++++++++++ PR2020-11-16
    function MSTUDSUBJ_Open(el_input){
        console.log(" -----  MSTUDSUBJ_Open   ----")
        if(el_input && has_permit_edit){

            mod_MSTUDSUBJ_dict = {}; // stores general info of selected candidate in MSTUDSUBJ PR2020-11-21
            //mod_studsubj_dict = {};  // stores studsubj of selected candidate in MSTUDSUBJ
            //mod_schemeitem_dict = {};   // stores available studsubj for selected candidate in MSTUDSUBJ
            mod_studsubj_map.clear();
            mod_schemeitem_map.clear();

            let tblName = "studsubj";

            const tblRow = get_tablerow_selected(el_input);
            const map_id = tblRow.id;
            const arr = map_id.split("_");
            const stud_pk_int = (Number(arr[1])) ? Number(arr[1]) : null;
            const studsubj_pk_int = (Number(arr[2])) ? Number(arr[2]) : null;
            const map_dict = get_mapdict_from_datamap_by_tblName_pk(student_map, "student", stud_pk_int);

            if(!isEmpty(map_dict)) {
                mod_MSTUDSUBJ_dict.student_id = map_dict.id;
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

                MSTUDSUBJ_FillDicts();
                MSTUDSUBJ_FillTbls();

                MSTUDSUBJ_SetInputFields(null, false);

        // ---  set focus to el_MSTUD_abbrev
                //setTimeout(function (){el_MSTUD_abbrev.focus()}, 50);

        // ---  disable btn submit, hide delete btn when is_addnew
               // add_or_remove_class(el_MSTUD_btn_delete, cls_hide, is_addnew )
                //const disable_btn_save = (!el_MSTUD_abbrev.value || !el_MSTUD_name.value || !el_MSTUD_sequence.value )
                //el_MSTUD_btn_save.disabled = disable_btn_save;

                //MSTUD_validate_and_disable();

        // ---  show modal
                $("#id_mod_studentsubject").modal({backdrop: true});

            }  // if(!isEmpty(map_dict)) {
        }
    };  // MSTUDSUBJ_Open

//========= MSTUDSUBJ_Save  ============= PR2020-11-18
    function MSTUDSUBJ_Save(){
        console.log(" -----  MSTUDSUBJ_Save   ----")
        console.log( "mod_studsubj_map: ", mod_studsubj_map);

        if(has_permit_edit && mod_MSTUDSUBJ_dict.student_id){
            const upload_dict = {id: {table: 'studentsubject', student_pk: mod_MSTUDSUBJ_dict.student_id}}
            const studsubj_list = []
// ---  loop through mod_studsubj_map

            //for (const [studsubj_pk, ss_dict] of Object.entries(mod_studsubj_dict)) {

            for (const [studsubj_pk, ss_dict] of mod_studsubj_map.entries()) {

        console.log("studsubj_pk", studsubj_pk, "ss_dict", ss_dict);
                if(!isEmpty(ss_dict)){
                    let mode = null;
                    if(ss_dict.isdeleted){
                        mode = "delete"
                    } else  if(ss_dict.iscreated){
                        mode = "create"
                    } else  if(ss_dict.haschanged){
                        mode = "update"
                    }
        console.log("mode", mode);
                    // add only teammembers with mode 'create, 'delete' or 'update'
                    if (mode){
                        studsubj_list.push({
                                mode: mode,
                                studsubj_id: ss_dict.studsubj_id,
                                schemeitem_id: ss_dict.schemeitem_id,
                                student_id: ss_dict.student_id,
                                is_extra_nocount: ss_dict.is_extra_nocount,
                                is_extra_counts: ss_dict.is_extra_counts,
                                is_elective_combi: ss_dict.is_elective_combi,
                                pws_title: ss_dict.pws_title,
                                pws_subjects: ss_dict.pws_subjects
                            });
                    }  //  if (mode)
                    if (mode === "delete"){
// - make to_be_deleted tblRow red
                        const row_id = "studsubj_" + ss_dict.student_id + "_" + ss_dict.studsubj_id
        console.log("row_id", row_id);
                        const tblRow = document.getElementById(row_id);
        console.log("tblRow", tblRow);
                        ShowClassWithTimeout(tblRow, "tsa_tr_error")
                    }
                }  // if(!isEmpty(ss_dict)){
            }  //  for (const [studsubj_pk, ss_dict] of Object.entries(mod_studsubj_dict)


            if(studsubj_list && studsubj_list.length){
                upload_dict.studsubj_list = studsubj_list;
                console.log("upload_dict: ", upload_dict)
                UploadChanges(upload_dict, url_studsubj_upload);
            }
        };  // if(has_permit_edit && mod_MSTUDSUBJ_dict.student_id){

// ---  hide modal
        $("#id_mod_studentsubject").modal("hide");

    }  // MSTUDSUBJ_Save

//========= MSTUDSUBJ_FillDicts  ============= PR2020-11-17
    function MSTUDSUBJ_FillDicts() {
        console.log("===== MSTUDSUBJ_FillDicts ===== ");
        console.log("mod_MSTUDSUBJ_dict", mod_MSTUDSUBJ_dict);

// reset lists
        /*  PR2020-11-18 from https://love2dev.com/blog/javascript-remove-from-array/
            splice can be used to add or remove elements from an array.
            The first argument specifies the location at which to begin adding or removing elements.
            The second argument specifies the number of elements to remove.
            The third and subsequent arguments are optional; they specify elements to be added to the array
        mod_studsubj_dict.splice(0, mod_studsubj_dict.length)
        mod_schemeitem_dict.splice(0, mod_schemeitem_dict.length)
*/

//  list mod_studsubj_dict contains the existing, added and deleted subjects of the student
//  list mod_schemeitem_dict contains all schemitems of the student's scheme

        const student_pk = mod_MSTUDSUBJ_dict.student_id
        const scheme_pk = mod_MSTUDSUBJ_dict.scheme_id

        //mod_studsubj_dict = {};
        mod_studsubj_map.clear();
// ---  loop through grade_map
        for (const [map_id, ss_dict] of grade_map.entries()) {

        // add only studsubj from this student
            if (student_pk === ss_dict.student_id) {
                const item = deepcopy_dict(ss_dict);
                if(item.schemeitem_id){
                    //mod_studsubj_dict[item.schemeitem_id] = item
                    mod_studsubj_map.set(item.schemeitem_id, item);

                }
            }
        }
        console.log("mod_studsubj_map", mod_studsubj_map);

// ---  loop through schemeitem_map
        /*
        mod_schemeitem_dict = {};
        el_tblBody_schemeitems.innerText = null;
        for (const [map_id, dict] of schemeitem_map.entries()) {
        // add only schemitems from scheme of this student
            if (scheme_pk && scheme_pk === dict.scheme_id) {
                const item = deepcopy_dict(dict)
                mod_schemeitem_dict[item.id] = item
            }
        }
        */
        mod_schemeitem_map.clear();
        el_tblBody_schemeitems.innerText = null;
        for (const [map_id, dict] of schemeitem_map.entries()) {
        // add only schemitems from scheme of this student
            if (scheme_pk && scheme_pk === dict.scheme_id) {
                const item = deepcopy_dict(dict)
                mod_schemeitem_map.set(item.id, item);
            }
        }
        console.log("mod_schemeitem_map", mod_schemeitem_map);

    } // MSTUDSUBJ_FillDicts

//========= MSTUDSUBJ_FillTbls  ============= PR2020-11-17
    function MSTUDSUBJ_FillTbls(schemeitem_pk_list) {
        //console.log("===== MSTUDSUBJ_FillTbls ===== ");
        //console.log("mod_studsubj_dict", mod_studsubj_dict);
// ---  loop through mod_studsubj_dict dict
        el_tblBody_studsubjects.innerText = null;
        const subject_list = [];
        let has_rows = false;
        for (const [studsubj_pk, dict] of mod_studsubj_map.entries()) {

        //console.log("studsubj_pk", studsubj_pk);
        //console.log("dict", dict);
            if (!dict.isdeleted) {
                subject_list.push(dict.subj_id)
                const schemeitem_pk = dict.schemeitem_id;
                const highlighted = (schemeitem_pk_list && schemeitem_pk_list.includes(schemeitem_pk))
                MSTUDSUBJ_FillSelectRow("studsubj", el_tblBody_studsubjects, schemeitem_pk, dict, true, highlighted);
                has_rows = true;
            }
        }

// addrow 'This_candidate_has_nosubjects_yet'
        if(!has_rows){
            const tblRow = el_tblBody_studsubjects.insertRow(-1);
            const td = tblRow.insertCell(-1);
            const el_div = document.createElement("div");
                el_div.classList.add("tw_300", "px-2")
                el_div.innerText = loc.This_candidate_has_nosubjects_yet;
                td.appendChild(el_div);
        }

// ---  loop through mod_schemeitem_dict =
//      mod_schemeitem_dict is a deepcopy dict with schemeitems of the scheme of this candidate, key = schemeitem_pk
        el_tblBody_schemeitems.innerText = null;
        //for (const [schemeitem_pk, dict] of Object.entries(mod_schemeitem_dict)) {
        for (const [schemeitem_pk, dict] of mod_schemeitem_map.entries()) {
            const enabled = (dict.subj_id && !subject_list.includes(dict.subj_id))

            const highlighted = (schemeitem_pk_list && schemeitem_pk_list.includes(schemeitem_pk))
            MSTUDSUBJ_FillSelectRow("schemeitem", el_tblBody_schemeitems, schemeitem_pk, dict, enabled, highlighted);
        }

    } // MSTUDSUBJ_FillTbls

//========= MSTUDSUBJ_FillSelectRow  ============= PR2020--09-30
    function MSTUDSUBJ_FillSelectRow(tblName, tblBody_select, schemeitem_pk, dict, enabled, highlighted) {
        //console.log("===== MSTUDSUBJ_FillSelectRow ===== ");
        //console.log("..........schemeitem_pk", schemeitem_pk);
        //console.log("dict", dict);

        if (!isEmpty(dict)){
            let subj_code = (dict.subj_code) ? dict.subj_code : "";
            if(dict.is_combi) { subj_code += " *" }
            let subj_name = (dict.subj_name) ? dict.subj_name : null;
            const sjt_abbrev = (dict.sjt_abbrev) ? dict.sjt_abbrev : null;

            const tblRow = tblBody_select.insertRow(-1);
            tblRow.setAttribute("data-pk", schemeitem_pk);
            if(dict.mapid) { tblRow.id = dict.mapid }
            const selected_int = 0
            tblRow.setAttribute("data-selected", selected_int);

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
                el_div.classList.add("tw_120", "pl-4")
                el_div.innerText = subj_code;
                tblRow.title = subj_name;
                td.appendChild(el_div);

    // --- add second td to tblRow.
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                el_div.classList.add("tw_120")
                el_div.innerText = sjt_abbrev;
                td.appendChild(el_div);

            //td.classList.add("tw_200X", "px-2", "pointer_show") // , "tsa_bc_transparent")

    //--------- add addEventListener
            if(enabled) {
                tblRow.addEventListener("click", function() {MSTUDSUBJ_SelectSubject(tblName, tblRow)}, false);
            }
        }
    } // MSTUDSUBJ_FillSelectRow

//========= MSTUDSUBJ_SelectSubject  ============= PR2020-10-01
    function MSTUDSUBJ_SelectSubject(tblName, tblRow){
        //console.log( "===== MSTUDSUBJ_SelectSubject  ========= ");
        //console.log( "event_key", event_key);

        if(tblRow){
            let is_selected = (!!get_attr_from_el_int(tblRow, "data-selected"));
            let pk_int = get_attr_from_el_int(tblRow, "data-pk");
            const is_select_all = (!pk_int);
// ---  toggle is_selected
            is_selected = !is_selected;

            const tblBody_selectTable = tblRow.parentNode;


// ---  in tbl "studsubj" and when selected: deselect all other rows
            if (tblName === "studsubj" && is_selected){
                // fill characteristics
                mod_MSTUDSUBJ_dict.sel_schemitem_pk = get_attr_from_el_int(tblRow, "data-pk")
                MSTUDSUBJ_SetInputFields(mod_MSTUDSUBJ_dict.sel_schemitem_pk, is_selected)
                }
/*
                for (let i = 0, row; row = tblBody_selectTable.rows[i]; i++) {
                    let row_pk = get_attr_from_el_int(row, "data-pk");
                    // set only the current row selected, deselect others
                    const row_is_selected_row = (is_selected && row_pk === pk_int);
                    MSTUDSUBJ_set_selected(row, row_is_selected_row);
                }
                */
           // } else {
// ---  put new value in this tblRow, show/hide tickmark
                 MSTUDSUBJ_set_selected(tblRow, is_selected);
            //}
        }
    }  // MSTUDSUBJ_SelectSubject

    function MSTUDSUBJ_set_selected(tblRow, row_is_selected_row){
// ---  put new value in this tblRow, show/hide tickmark PR2020-11-21
        tblRow.setAttribute("data-selected", ( (row_is_selected_row) ? 1 : 0) )
        add_or_remove_class(tblRow, "bg_selected_blue", row_is_selected_row )
        const img_class = (row_is_selected_row) ? "tickmark_0_2" : "tickmark_0_0"
        const el = tblRow.cells[0].children[0];
        if (el){el.className = img_class}
    }

    function MSTUDSUBJ_SetInputFields(schemitem_pk, is_selected){
// ---  put value in input box 'Characteristics of this subject
        //console.log( "===== MSTUDSUBJ_SetInputFields  ========= ");
        //console.log( "schemitem_pk", schemitem_pk);
        //console.log( "is_selected", is_selected);

        let is_empty = true, is_combi = false, is_elective_combi = false,
            is_extra_counts = false, is_extra_nocount = false,
            pwstitle = null, pwssubjects = null,
            extra_count_allowed = false, extra_nocount_allowed = false, elective_combi_allowed = false;

        let sjt_has_prac = false, sjt_has_pws = false, sjt_one_allowed = false;

        let map_dict = {};

        //if(is_selected && schemitem_pk && mod_studsubj_dict[schemitem_pk]){
        if(is_selected && schemitem_pk && mod_studsubj_map.get(schemitem_pk)){
            //map_dict = mod_studsubj_dict[schemitem_pk];
            map_dict = mod_studsubj_map.get(schemitem_pk);
            if(!isEmpty(map_dict)){
                is_empty = false;
                is_combi = map_dict.is_combi
                extra_count_allowed = map_dict.extra_count_allowed
                extra_nocount_allowed = map_dict.extra_nocount_allowed
                elective_combi_allowed = map_dict.elective_combi_allowed
                is_extra_counts = map_dict.is_extra_counts,
                is_extra_nocount = map_dict.is_extra_nocount,
                is_elective_combi = map_dict.is_elective_combi,
                sjt_has_prac = map_dict.sjt_has_prac,
                sjt_has_pws = map_dict.sjt_has_pws,
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
            const hide_element = (field === "is_combi") ? is_empty :
                                 (field === "is_elective_combi") ? !map_dict.elective_combi_allowed :
                                 (field === "is_extra_nocount") ? !map_dict.extra_nocount_allowed :
                                 (field === "is_extra_counts") ? !map_dict.extra_count_allowed :
                                 (["pws_title", "pws_subjects"].indexOf(field) > -1 ) ? !map_dict.sjt_has_pws : true;
            if(el_wrap){ add_or_remove_class(el_wrap, cls_hide, hide_element )}

           if(el.classList.contains("awp_input_text")){
                el.value = map_dict[field];
           } else if(el.classList.contains("awp_input_checkbox")){
                el.checked = (map_dict[field]) ? map_dict[field] : false;
           }
        }
    }  // MSTUDSUBJ_SetInputFields

//========= MSTUDSUBJ_AddRemoveSubjct  ============= PR2020-11-18
    function MSTUDSUBJ_AddRemoveSubjct(mode) {
        console.log("  =====  MSTUDSUBJ_AddRemoveSubjct  =====");
        const tblBody = (mode === "add") ? el_tblBody_schemeitems : el_tblBody_studsubjects;
        const schemeitem_pk_list = []

// ---  loop through tblBody and create list of selected schemeitem_pk's
        for (let i = 0, tblRow, is_selected, pk_int; tblRow = tblBody.rows[i]; i++) {
            is_selected = !!get_attr_from_el_int(tblRow, "data-selected")
            if (is_selected) {
                pk_int = get_attr_from_el_int(tblRow, "data-pk")
                schemeitem_pk_list.push(pk_int);
            }
        }
        console.log("schemeitem_pk_list", schemeitem_pk_list);

// ---  loop through schemeitem_pk_list
        for (let i = 0, pk_int; pk_int = schemeitem_pk_list[i]; i++) {
            let map_dict = {};
            if(mode === "add"){
// ---  check if schemeitem_pk already exists in mod_studsubj_dict
                const ss_map_dict = (mod_studsubj_map.get(pk_int)) ? mod_studsubj_map.get(pk_int) : {};
        console.log("mod_studsubj_map", mod_studsubj_map);
        console.log("ss_map_dict", deepcopy_dict(ss_map_dict));
                //if (mod_studsubj_dict[pk_int]) {
                if (!isEmpty(ss_map_dict) ){
// if it exists it must be a deleted row, remove 'isdeleted'
                    ss_map_dict.isdeleted = false;
                } else {
                    const student_pk = mod_MSTUDSUBJ_dict.student_id
// add row to mod_studsubj_dict if it does not yet exist
                    //const si_dict = mod_schemeitem_dict[pk_int];
                    //const si_dict = get_mapdict_from_datamap_by_id(mod_schemeitem_map, pk_int)
                    const si_dict = mod_schemeitem_map.get(pk_int);
                    if(!isEmpty(si_dict)){
                        const si_map_dict = deepcopy_dict(si_dict);
                          // in si_dict schemeitem_id = si_dict.id, in mod_studsubj_dict it is mod_studsubj_dict.schemeitem_id
                        si_map_dict.schemeitem_id = si_dict.id;
                        delete si_map_dict.id;
                        // si_map_dict.mapid overrides si_dict.mapid
                        si_map_dict.mapid = "studsubj_" + student_pk + "_"// mapid: "studsubj_29_2" = "studsubj_" + student_id + "_" + studsubj_id
                        // adding keys that do't exist in si_dict
                        si_map_dict.student_id = mod_MSTUDSUBJ_dict.student_pk;
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

                        mod_studsubj_map.set(pk_int, si_map_dict);
                    }
                }
            }  else if(mode === "remove"){

    // ---  check if schemeitem_pk already exists in mod_studsubj_dict
                const ss_map_dict = (mod_studsubj_map.get(pk_int)) ? mod_studsubj_map.get(pk_int) : {};
                if (!isEmpty(ss_map_dict)) {
    // set 'isdeleted' = true
                    ss_map_dict.isdeleted = true;
                }

                MSTUDSUBJ_SetInputFields()
            }
        }  //  for (let i = 0, pk_int; pk_int = schemeitem_pk_list[i]; i++)
        //console.log("mod_studsubj_dict", mod_studsubj_dict);
        MSTUDSUBJ_FillTbls(schemeitem_pk_list)

    }  // MSTUDSUBJ_AddRemoveSubjct

//========= MSTUDSUBJ_AddPackage  ============= PR2020-11-18
    function MSTUDSUBJ_AddPackage() {
        console.log("  =====  MSTUDSUBJ_AddPackage  =====");

    }  // MSTUDSUBJ_AddPackage

//========= MSTUDSUBJ_InputboxEdit  ============= PR2020-12-01
    function MSTUDSUBJ_InputboxEdit(el_input) {
        //console.log("  =====  MSTUDSUBJ_InputboxEdit  =====");
        if(el_input){
// ---  get dict of selected schemitem from mod_studsubj_dict
            const field = get_attr_from_el(el_input, "data-field")
            //const sel_studsubj_dict = mod_studsubj_dict[mod_MSTUDSUBJ_dict.sel_schemitem_pk];
            const sel_studsubj_dict = mod_studsubj_map.get(mod_MSTUDSUBJ_dict.sel_schemitem_pk);
            if(sel_studsubj_dict){
                sel_studsubj_dict.haschanged = true;
    // ---  put new value of el_input in sel_studsubj_dict
                if(el_input.classList.contains("awp_input_text")) {
            //console.log("awp_input_text");
                    sel_studsubj_dict[field] = el_input.value;
    // ---  if checkbox: put checked value in sel_studsubj_dict
                } else if(el_input.classList.contains("awp_input_checkbox")) {
            //console.log("awp_input_checkbox");
                    const is_checked = el_input.checked;
                    sel_studsubj_dict[field] = is_checked;
    // ---  if element is checked: uncheck other 'extra subject' element if that one is also checked
                    if(is_checked){
                        const other_field = (field === "is_extra_nocount") ? "is_extra_counts" : "is_extra_nocount";
                        const other_el = document.getElementById("id_MSTUDSUBJ_" + other_field)
                        if(other_el && other_el.checked){
                            other_el.checked = false;
                            sel_studsubj_dict[other_field] = false;
                        }
                    }
                }
            }
        //console.log("sel_studsubj_dict", sel_studsubj_dict);
        }
    }  // MSTUDSUBJ_InputboxEdit

//========= MSTUDSUBJ_CheckboxEdit  ============= PR2020-12-01
    function MSTUDSUBJ_CheckboxEdit(el_input) {
        //console.log("  =====  MSTUDSUBJ_CheckboxEdit  =====");
        if(el_input){
            const field = get_attr_from_el(el_input, "data-field")
            const is_checked = el_input.checked;
            const sel_studsubj_dict = mod_studsubj_map.get(mod_MSTUDSUBJ_dict.sel_schemitem_pk);
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

// +++++++++++++++++ MODAL SELECT SUBJECT STUDENT ++++++++++++++++++++++++++++++++
//========= MSSS_Open ====================================  PR2020-12-17
    function MSSS_Open (tblName) {
        console.log(" ===  MSSS_Open  =====", tblName) ;
        // dont reset mod_MSSS_dict
        mod_MSSS_dict = {sel_table: tblName,
                         sel_pk:  -1,  // -1 = all, 0 = shift without employee
                         sel_code: null};

// fill select table
        MSSS_Fill_SelectTable(tblName)

// set header text
        const label_text = loc.Filter + ( (tblName === "student") ?  loc.Candidate.toLowerCase() : loc.Subject.toLowerCase() );
        document.getElementById("id_MSSS_header").innerText = label_text;
        document.getElementById("id_MSSS_input_label").innerText = label_text;
        const fields = (tblName === "student") ? loc.a_candidate : loc.a_subject;
        const msg_text = (tblName === "student") ? loc.Type_afew_letters_candidate : loc.Type_afew_letters_subject;
        document.getElementById("id_MSSS_msg_input").innerText = msg_text

        set_focus_on_el_with_timeout(el_MSSS_input, 50);
// ---  show modal
         $("#id_mod_select_subject_student").modal({backdrop: true});
    }; // MSSS_Open

//=========  MSSS_Save  ================ PR2020-01-29
    function MSSS_Save() {
        console.log("===  MSSS_Save =========");

        console.log("mod_MSSS_dict", mod_MSSS_dict);

        if (mod_MSSS_dict.sel_table === "student") {
            selected_student_pk = (mod_MSSS_dict.sel_pk) ? mod_MSSS_dict.sel_pk : null;
        } else if (mod_MSSS_dict.sel_table === "subject") {
            selected_subject_pk = (mod_MSSS_dict.sel_pk) ? mod_MSSS_dict.sel_pk : null;
        }

        console.log("selected_student_pk", selected_student_pk);
        console.log("selected_subject_pk", selected_subject_pk);
        MSSS_display_in_sbr();

        FillTblRows();

// hide modal
        $("#id_mod_select_subject_student").modal("hide");

    }  // MSSS_Save

//========= MSSS_Fill_SelectTable  ============= PR2020--09-17
    function MSSS_Fill_SelectTable(tblName) {
        console.log("===== MSSS_Fill_SelectTable ===== ", tblName);
        const data_map = (tblName === "subject") ? subject_map : student_map
        console.log("data_map", data_map);

        const tblBody_select = el_MSSS_tblBody;
        tblBody_select.innerText = null;

// ---  add All to list when multiple employees / functions exist
        if(data_map.size){
            const caption = (tblName === "student") ? loc.Candidates : loc.Subjects;
            const add_all_text = "<" + loc.All + caption.toLowerCase() + ">";
            const add_all_dict = (tblName === "student") ? {id: -1, examnumber: "", fullname: add_all_text} :  {id: -1,  code: "", name: add_all_text};
            MSSS_Create_SelectRow(tblName, tblBody_select, add_all_dict, mod_MSSS_dict.sel_pk)
        }
// ---  loop through dictlist
        for (const [map_id, map_dict] of data_map.entries()) {
            MSSS_Create_SelectRow(tblName, tblBody_select, map_dict, mod_MSSS_dict.sel_pk)

        }
    } // MSSS_Fill_SelectTable

//========= MSSS_Create_SelectRow  ============= PR2020-12-18
    function MSSS_Create_SelectRow(tblName, tblBody_select, dict, selected_pk) {
        console.log("===== MSSS_Create_SelectRow ===== ", tblName);

//--- get info from item_dict
        //[ {pk: 2608, code: "Colpa de, William"} ]
        const pk_int = dict.id;
        const code = (tblName === "student") ? dict.examnumber : dict.code
        const name = (tblName === "student") ? dict.fullname : dict.name
        const is_selected_row = (pk_int === selected_pk);

//--------- insert tblBody_select row at end
        const map_id = "sel_" + tblName + "_" + pk_int
        const tblRow = tblBody_select.insertRow(-1);

        tblRow.id = map_id;
        tblRow.setAttribute("data-pk", pk_int);
        tblRow.setAttribute("data-code", code);
        tblRow.setAttribute("data-value", name);
        tblRow.setAttribute("data-table", tblName);
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
            el_div.classList.add("tw_270", "px-1")
            td.appendChild(el_div);
        td.classList.add("tsa_bc_transparent")

//--------- add addEventListener
        tblRow.addEventListener("click", function() {MSSS_HandleSelectRow(tblRow, event.target)}, false);
    } // MSSS_Create_SelectRow

//========= MSSS_display_in_sbr  ====================================
    function MSSS_display_in_sbr() {
        console.log( "===== MSSS_display_in_sbr  ========= ");
        console.log( "mod_MSSS_dict ",mod_MSSS_dict);

        let student_text = "",  subject_text = "";
        if (mod_MSSS_dict.sel_table === "student") {
            selected_student_pk = (mod_MSSS_dict.sel_pk) ? mod_MSSS_dict.sel_pk: null;
            if (mod_MSSS_dict.sel_pk) { selected_subject_pk = null};
            student_text = (selected_student_pk) ? mod_MSSS_dict.sel_value : null;
        } else if (mod_MSSS_dict.sel_table === "subject") {
            selected_subject_pk =  (mod_MSSS_dict.sel_pk) ? mod_MSSS_dict.sel_pk : null;
            if (mod_MSSS_dict.sel_pk) {selected_student_pk = null};
            subject_text = (selected_subject_pk) ? mod_MSSS_dict.sel_code  : null;
        }

        el_SBR_select_student.value = student_text;
        el_SBR_select_subject.value = subject_text;

        let header_text = "";
        if (selected_student_pk){
            header_text = mod_MSSS_dict.sel_value
            if (selected_subject_pk){ header_text +=  " - " + mod_MSSS_dict.sel_value}
        } else if (selected_subject_pk){
            header_text = mod_MSSS_dict.sel_value;
        }
        document.getElementById("id_hdr_left").innerText = header_text

    }; // MSSS_display_in_sbr


//=========  MSSS_HandleSelectRow  ================ PR2020-12-17
    function MSSS_HandleSelectRow(tblRow) {
        console.log( "===== MSSS_HandleSelectRow ========= ");
        //console.log( tblRow);
        // all data attributes are now in tblRow, not in el_select = tblRow.cells[0].children[0];
// ---  get clicked tablerow
        if(tblRow) {
// ---  deselect all highlighted rows
            DeselectHighlightedRows(tblRow, cls_selected)
// ---  highlight clicked row
            tblRow.classList.add(cls_selected)
// ---  get pk en code from id of select_tblRow
            mod_MSSS_dict.sel_pk = get_attr_from_el_int(tblRow, "data-pk");
            mod_MSSS_dict.sel_code = get_attr_from_el(tblRow, "data-code");
            mod_MSSS_dict.sel_value = get_attr_from_el(tblRow, "data-value");
            mod_MSSS_dict.sel_table = get_attr_from_el(tblRow, "data-table");
// ---  filter rows wth selected pk
            MSSS_Save()
        }
// ---  put value in input box, reste when no tblRow
            el_MSSS_input.value = get_attr_from_el(tblRow, "data-value")

    }  // MSSS_HandleSelectRow

//=========  MSSS_InputKeyup  ================ PR2020-09-19
    function MSSS_InputKeyup() {
        console.log( "===== MSSS_InputKeyup  ========= ");

// ---  get value of new_filter
        let new_filter = el_MSSS_input.value

        let tblBody = el_MSSS_tblBody;
        const len = tblBody.rows.length;
        if (new_filter && len){
// ---  filter rows in table select_employee
            const filter_dict = t_Filter_SelectRows(tblBody, new_filter);
        console.log( "filter_dict", filter_dict);
// ---  if filter results have only one employee: put selected employee in el_MSSS_input
            const selected_pk = get_dict_value(filter_dict, ["selected_pk"])
            const selected_value = get_dict_value(filter_dict, ["selected_value"])
            if (selected_pk) {
                el_MSSS_input.value = selected_value;
// ---  put pk of selected employee mod_MSSS_dict.sel_pk
                mod_MSSS_dict.sel_pk = selected_pk;
                mod_MSSS_dict.sel_code = selected_value;
// ---  Set focus to btn_save
                el_MSSS_btn_save.focus()
            }  //  if (!!selected_pk) {
        }
    }; // MSSS_InputKeyup

// +++++++++++++++++ END OF MODAL SELECT SUBJECT STUDENT ++++++++++++++++++++++++++++++++



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
//###########################################################################
// +++++++++++++++++ REFRESH DATA MAP ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataMap  ================ PR2020-08-16 PR2020-09-30
    function RefreshDataMap(tblName, field_names, data_rows, data_map) {
        //console.log(" --- RefreshDataMap  ---");
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
        console.log(" --- RefreshDatamapItem  ---");
        console.log("update_dict", update_dict);
        if(!isEmpty(update_dict)){
// ---  update or add update_dict in subject_map
            let updated_columns = [];
    // get existing map_item
            const tblName = update_dict.table;
            const map_id = update_dict.mapid;
            let tblRow = document.getElementById(map_id);

            const is_deleted = get_dict_value(update_dict, ["deleted"], false)
            const is_created = get_dict_value(update_dict, ["created"], false)

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
                            }}}}
    // ---  update item
                data_map.set(map_id, update_dict)
            }

        console.log("tblRow", tblRow);
    // ---  make update
            // note: when updated_columns is empty, then updated_columns is still true.
            // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
            if(tblRow && updated_columns.length){
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
            console.log("updated_columns", updated_columns);
            console.log("el_fldName", el_fldName);
                                 if(updated_columns.includes(el_fldName)){
            console.log("el_fldName", el_fldName);
                                UpdateField(el, update_dict);
        // make gield green when field name is in updated_columns
                                if(updated_columns.includes(el_fldName)){
                                    ShowOkElement(el);
             }}}}}}}
        }
    }  // RefreshDatamapItem


//=========  fill_data_list  ================ PR2020-10-07
    function fill_data_list(data_rows) {
        console.log(" --- fill_data_list  ---");
        let data_list = [];
        if (data_rows) {
            for (let i = 0, row; row = data_rows[i]; i++) {
                data_list[row.id] = row.abbrev;
            }
        }
        return data_list
    }  //  fill_data_list


//###########################################################################
// +++++++++++++++++ SIDEBAR SELECT TABLE STUDENTS ++++++++++++++++++++++++++
/*
//========= SBR_FillSelectTable  ============= PR2020-11-14
    function SBR_FillSelectTable(selected_pk) {
        //console.log( "=== SBR_FillSelectTable === ");
        //console.log( "selected_pk", selected_pk);
        //console.log( "mod_SBR_dict", mod_SBR_dict);
        let tblBody = document.getElementById("id_SBR_tblbody_select");
        tblBody.innerText = null;

        const data_map = student_map;
        let row_count = 0
        if (data_map.size){
//--- loop through student_map
            for (const [map_id, map_dict] of data_map.entries()) {
                const pk_int = map_dict.id;
                const full_name = (map_dict.fullname) ? map_dict.fullname : "---";
                const first_name = (map_dict.firstname) ? map_dict.firstname : "";
                const last_name = (map_dict.firstname) ? map_dict.firstname : "";
                const order_by = (map_dict.fullname) ? map_dict.fullname.toLowerCase() : null;

//- insert tblBody row
                let tblRow = tblBody.insertRow(-1); //index -1 results in that the new row will be inserted at the last position.
                tblRow.setAttribute("data-pk", pk_int);
                tblRow.setAttribute("data-orderby", order_by);
// -  highlight selected row
                if (selected_pk && pk_int === selected_pk){
                    tblRow.classList.add(cls_selected)
                }
//- add hover to tblBody row
                add_hover(tblRow);
//- add EventListener to Modal SelectEmployee row
                tblRow.addEventListener("click", function() {SBR_SelectRowClicked(tblRow)}, false )
// - add first td to tblRow.
                let td = tblRow.insertCell(-1);
// --- add a element to td, necessary to get same structure as item_table, used for filtering
                let el = document.createElement("div");
                    el.innerText = full_name;
                    el.classList.add("mx-1")
                td.appendChild(el);
                row_count += 1;

            } // for (const [map_id, item_dict] of employee_map.entries())
        }  //  if (employee_map.size === 0)
//--- when no items found: show 'select_employee_none'
        if(!row_count){
            let tblRow = tblBody.insertRow(-1); //index -1 results in that the new row will be inserted at the last position.
            let td = tblRow.insertCell(-1);
            td.innerText = loc.No_candidates;
        }
    } // SBR_FillSelectTable
*/

//=========  SBR_SelectRowClicked  ================ PR2020-11-15
    function SBR_SelectRowClicked(sel_tblRow) {
        console.log( "===== SBR_SelectRowClicked ========= ");

// ---  deselect all highlighted rows
        DeselectHighlightedRows(sel_tblRow, cls_selected)

        if(sel_tblRow) {
// ---  highlight clicked row
            sel_tblRow.classList.add(cls_selected)
// ---  put value in input box, put employee_pk in mod_MAB_dict, set focus to select_abscatselect_abscat

// ---  update selected_student_pk
            selected_student_pk = null;
            // only select employee from select table
            const pk_int = get_attr_from_el_int(sel_tblRow, "data-pk");
            let student_name = null, student_level = null, student_sector = null, student_class = null;
            if(pk_int){
                const map_dict = get_mapdict_from_datamap_by_tblName_pk(student_map, "student", pk_int);
        console.log( "map_dict", map_dict);
                selected_student_pk = map_dict.id;
                const last_name = (map_dict.lastname) ? map_dict.lastname : "";
                const first_name = (map_dict.firstname) ? map_dict.firstname : "";
                student_name = last_name + ", " + first_name
                student_level = (map_dict.lvl_abbrev) ? map_dict.lvl_abbrev : null;
                student_sector = (map_dict.sct_abbrev) ? map_dict.sct_abbrev : null;
                student_class = (map_dict.classname) ? map_dict.classname : null;
            }
// ---  put info in header box
            document.getElementById("id_hdr_left").innerText = student_name;
            document.getElementById("id_hdr_textright1").innerText = student_level;
            document.getElementById("id_hdr_textright2").innerText = student_sector;

            let tblRow = t_HighlightSelectedTblRowByPk(tblBody_datatable, selected_student_pk)
            // ---  scrollIntoView, only in tblBody customer
            if (tblRow){
                tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' })
            };



// ---  enable btn_save and input elements
            //MAB_BtnSaveEnable();
        }  // if(!!tblRow) {
    }  // SBR_SelectRowClicked



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
//###########################################################################

//========= get_tblName_from_selectedBtn  ======== // PR2020-11-14
    function get_tblName_from_selectedBtn() {
        const tblName = (selected_btn === "btn_student") ? "student" :
                        (selected_btn === "btn_studsubj") ? "studsubj" : null;
        return tblName;
    }
//========= get_datamap_from_tblName  ======== // PR2020-11-14
    function get_datamap_from_tblName(tblName) {
        const data_map = (tblName === "student") ? student_map :
                         (tblName === "studsubj") ? studentsubject_map : null;
        return data_map;
    }

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL SELECT EXAMYEAR ++++++++++++++++++++
//=========  ModSelectExamyear_Open  ================ PR2020-10-27
    function ModSelectExamyear_Open() {
        //console.log( "===== ModSelectExamyear_Open ========= ");

        //PR2020-10-28 debug: modal gives 'NaN' and 'undefined' when  loc not back from server yet
        if (!isEmpty(loc)) {
            mod_dict = {examyear_pk: setting_dict.sel_examyear_pk, table: "examyear"};
    // ---  fill select table
            ModSelectExamyear_FillSelectTable(0);  // 0 = selected_pk
    // ---  show modal
            $("#id_mod_select_examyear").modal({backdrop: true});
            }
    }  // ModSelectExamyear_Open

//=========  ModSelectExamyear_Save  ================ PR2020-10-28
    function ModSelectExamyear_Save() {
        console.log("===  ModSelectExamyear_Save =========");
        console.log("mod_dict", mod_dict);
// selected_pk: {sel_examyear_pk: 23, sel_schoolbase_pk: 15, sel_depbase_pk: 1}

// ---  upload new setting
        const datalist_request = {
            setting: {page_grade: {mode: "get"}, sel_examyear_pk: mod_dict.examyear_pk},
            examyear_rows: {get: true}
        };
        DatalistDownload(datalist_request);

// hide modal
        $("#id_mod_select_examyear").modal("hide");

    }  // ModSelectExamyear_Save

//=========  ModSelectExamyear_SelectItem  ================ PR2020-10-28
    function ModSelectExamyear_SelectItem(tblRow) {
        //console.log( "===== ModSelectExamyear_SelectItem ========= ");
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
            mod_dict.examyear_pk = (Number(data_pk)) ? Number(data_pk) : 0

            ModSelectExamyear_Save()
        }
    }  // ModSelectExamyear_SelectItem

//=========  ModSelectExamyear_FillSelectTable  ================ PR2020-08-21
    function ModSelectExamyear_FillSelectTable(selected_pk) {
        console.log( "===== ModSelectExamyear_FillSelectTable ========= ");
        console.log( "selected_pk", selected_pk);
        const tblBody_select = el_MSEY_tblBody_select;
        tblBody_select.innerText = null;

        let row_count = 0;
// --- loop through data_map
        const data_map = examyear_map;
        if(data_map){
            for (const [map_id, map_dict] of data_map.entries()) {
                ModSelectExamyear_FillSelectRow(map_dict, tblBody_select, selected_pk);
                row_count += 1;
            };
        }  // if(!!data_map)

        if(!row_count){
            let tblRow = tblBody_select.insertRow(-1);
            let td = tblRow.insertCell(-1);
            td.innerText = loc.No_exam_years;

        } else if(row_count === 1){
            let tblRow = tblBody_select.rows[0]
            if(tblRow) {
// ---  highlight first row
                tblRow.classList.add(cls_selected)
            }
        }
    }  // ModSelectExamyear_FillSelectTable

//=========  ModSelectExamyear_FillSelectRow  ================ PR2020-10-27
    function ModSelectExamyear_FillSelectRow(map_dict, tblBody_select, selected_pk) {
        //console.log( "===== ModSelectExamyear_FillSelectRow ========= ");
        //console.log( "map_dict: ", map_dict);

//--- loop through data_map
        let pk_int = null, code_value = null, is_selected_pk = false;
        pk_int = map_dict.examyear_id;
        code_value = (map_dict.examyear_int) ? map_dict.examyear_int.toString() : "---"
        is_selected_pk = (selected_pk != null && pk_int === selected_pk)
// ---  insert tblRow  //index -1 results in that the new row will be inserted at the last position.
        let tblRow = tblBody_select.insertRow(-1);
        tblRow.setAttribute("data-pk", pk_int);
        //tblRow.setAttribute("data-ppk", ppk_int);
        tblRow.setAttribute("data-value", code_value);
// ---  add EventListener to tblRow
        tblRow.addEventListener("click", function() {ModSelectExamyear_SelectItem(tblRow)}, false )
// ---  add hover to tblRow
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
    }  // ModSelectExamyear_FillSelectRow

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL SELECT SCHOOL OR DEPARTMENT ++++++++++++++++++++
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
        datalist_request.schemeitem_rows = {get: true};

        DatalistDownload(datalist_request);

    }  // ModSelSchOrDep_Save

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
                    if(dict.no_exemption_ce) {
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

    // 7. controleer Herexamen 'PR2015-12-13
            // not necessary PR2020-12-16
            // if (dict.examperiod === 2){
            // } else if (dict.examperiod === 3)

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
/////////////////////////////////////////////////


})  // document.addEventListener('DOMContentLoaded', function()