// PR2020-09-29 added
document.addEventListener('DOMContentLoaded', function() {
    "use strict";

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

    const cls_hide = "display_hide";
    const cls_hover = "tr_hover";
    const cls_visible_hide = "visibility_hide";
    const cls_selected = "tsa_tr_selected";

// ---  id of selected customer and selected order
    let selected_btn = "btn_user_list";
    let setting_dict = {};
    let permit_dict = {};
    let loc = {};  // locale_dict
    let selected_period = {};

    let selected_student_pk = null;

    let mod_dict = {};
    let mod_MSTUD_dict = {};

    let mod_MSTUDSUBJ_dict = {}; // stores general info of selected candidate in MSTUDSUBJ PR2020-11-21
    //let mod_studsubj_dict = {};  // stores studsubj of selected candidate in MSTUDSUBJ
    //let mod_schemeitem_dict = {};   // stores available studsubj for selected candidate in MSTUDSUBJ
    let mod_studsubj_map = new Map();  // stores studsubj of selected candidate in MSTUDSUBJ
    let mod_schemeitem_map = new Map();

    let time_stamp = null; // used in mod add user

    let user_list = [];
    let examyear_map = new Map();
    let school_map = new Map();
    // PR2020-12-26 These variable defintions are moved to import.js, so they can also be used in that file
    //let department_map = new Map();
    //let level_map = new Map();
    //let sector_map = new Map();
    let student_map = new Map();
    let subject_map = new Map();
    let studentsubject_map = new Map()
    let scheme_map = new Map()
    let schemeitem_map = new Map()

    let filter_dict = {};
    let filter_mod_employee = false;

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    const url_datalist_download = get_attr_from_el(el_data, "data-datalist_download_url");
    const url_settings_upload = get_attr_from_el(el_data, "data-settings_upload_url");
    const url_student_upload = get_attr_from_el(el_data, "data-student_upload_url");
    const url_studsubj_upload = get_attr_from_el(el_data, "data-studsubj_upload_url");
    // importdata_upload_url is stored in id_MIMP_data of modimport.html

// --- get field_settings
    const field_settings = {
        student: {  field_caption: ["", "Examnumber_twolines", "Last_name", "First_name", "Gender", "ID_number", "Department", "Leerweg", "SectorProfiel_twolines"],
                    field_names: ["select", "examnumber", "lastname", "firstname", "gender", "idnumber", "db_code", "lvl_abbrev", "sct_abbrev"],
                    filter_tags: ["select", "text", "text",  "text", "text", "text", "text", "text", "text"],
                    field_width:  ["020", "090", "180", "240", "090", "120", "120", "090", "090"],
                    field_align: ["c", "c", "l", "l", "c", "l", "c","c", "c"]},
        studsubj: { field_caption: ["", "Examnumber_twolines", "Candidate", "Abbreviation", "Subject", "Character"],
                    field_names: ["select", "examnumber", "fullname", "subj_code", "subj_name", "sjt_abbrev"],
                    filter_tags: ["select", "text", "text", "text", "text", "text", "text", "text", "text", "text"],
                    field_width:  ["032", "075", "360", "100", "240", "120"],
                    field_align: ["c", "r", "l", "l", "l"]}
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

// ---  MODAL SIDEBAR FILTER ------------------------------------

        const el_SBR_filter = document.getElementById("id_SBR_filter")
            el_SBR_filter.addEventListener("keyup", function() {MSTUD_InputKeyup(el_SBR_filter)}, false );

// ---  MODAL STUDENT
        const el_MSTUD_div_form_controls = document.getElementById("id_MSTUD_div_form_controls")
        let form_elements = el_MSTUD_div_form_controls.querySelectorAll(".awp_input_text")
        for (let i = 0, el, len = form_elements.length; i < len; i++) {
            el = form_elements[i];
            if(el){el.addEventListener("keyup", function() {MSTUD_InputKeyup(el)}, false )};
        }
        form_elements = el_MSTUD_div_form_controls.querySelectorAll(".awp_input_select")
        for (let i = 0, el, len = form_elements.length; i < len; i++) {
            el = form_elements[i];
            if(el){el.addEventListener("change", function() {MSTUD_InputSelect(el)}, false )};
        }
        const el_MSTUD_abbrev = document.getElementById("id_MSTUD_abbrev")
        const el_MSTUD_name = document.getElementById("id_MSTUD_name")

        const el_MSTUD_tbody_select = document.getElementById("id_MSTUD_tblBody_department")
        const el_MSTUD_btn_delete = document.getElementById("id_MSTUD_btn_delete");
        if(has_view_permit){el_MSTUD_btn_delete.addEventListener("click", function() {MSTUD_Save("delete")}, false)}
        const el_MSTUD_btn_save = document.getElementById("id_MSTUD_btn_save");
        if(has_view_permit){ el_MSTUD_btn_save.addEventListener("click", function() {MSTUD_Save("save")}, false)}

// ---  MODAL STUDENT SUBJECTS
        const el_MSTUDSUBJ_hdr = document.getElementById("id_MSTUDSUBJ_hdr")
        const el_MSTUDSUBJ_btn_add_selected = document.getElementById("id_MSTUDSUBJ_btn_add_selected")
            el_MSTUDSUBJ_btn_add_selected.addEventListener("click", function() {MSTUDSUBJ_AddRemoveSubject("add")}, false);
        const el_MSTUDSUBJ_btn_remove_selected = document.getElementById("id_MSTUDSUBJ_btn_remove_selected")
            el_MSTUDSUBJ_btn_remove_selected.addEventListener("click", function() {MSTUDSUBJ_AddRemoveSubject("remove")}, false);
        const el_MSTUDSUBJ_btn_add_package = document.getElementById("id_MSTUDSUBJ_btn_add_package")
            el_MSTUDSUBJ_btn_add_package.addEventListener("click", function() {MSTUDSUBJ_AddPackage()}, false);

        const el_input_controls = document.getElementById("id_MSTUDSUBJ_div_form_controls").querySelectorAll(".awp_input_text, .awp_input_checkbox")
        for (let i = 0, el; el = el_input_controls[i]; i++) {
            const key_str = (el.classList.contains("awp_input_checkbox")) ? "change" : "keyup";
            el.addEventListener(key_str, function() {MSTUDSUBJ_InputboxEdit(el)}, false)
        }

        const el_MSTUDSUBJ_btn_save = document.getElementById("id_MSTUDSUBJ_btn_save")
            el_MSTUDSUBJ_btn_save.addEventListener("click", function() {MSTUDSUBJ_Save()}, false);

        const el_tblBody_studsubjects = document.getElementById("id_MSTUDSUBJ_tblBody_studsubjects");
        const el_tblBody_schemeitems = document.getElementById("id_MSTUDSUBJ_tblBody_schemeitems");

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
    const el_worksheet_list = document.getElementById("id_MIMP_worksheetlist");
        el_worksheet_list.addEventListener("change", MIMP_SelectWorksheet, false);
    const el_MIMP_checkboxhasheader = document.getElementById("id_MIMP_hasheader");
        el_MIMP_checkboxhasheader.addEventListener("change", MIMP_CheckboxHasheaderChanged) //, false);
    const el_select_dateformat = document.getElementById("id_MIMP_dateformat");
        el_select_dateformat.addEventListener("change", function() {MIMP_Selectdateformat(el_select_dateformat)}, false )
   const el_MIMP_btn_prev = document.getElementById("id_MIMP_btn_prev");
        el_MIMP_btn_prev.addEventListener("click", function() {MIMP_btnPrevNextClicked("prev")}, false )
   const el_MIMP_btn_next = document.getElementById("id_MIMP_btn_next");
        el_MIMP_btn_next.addEventListener("click", function() {MIMP_btnPrevNextClicked("next")}, false )
   const el_MIMP_btn_test = document.getElementById("id_MIMP_btn_test");
        el_MIMP_btn_test.addEventListener("click", function() {MIMP_Save("test")}, false )
   const el_MIMP_btn_upload = document.getElementById("id_MIMP_btn_upload");
        el_MIMP_btn_upload.addEventListener("click", function() {MIMP_Save("save")}, false )


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

// ---  set selected menu button active
    SetMenubuttonActive(document.getElementById("id_hdr_users"));
    if(has_view_permit){
        // period also returns emplhour_list
        const datalist_request = {
                setting: {page: "page_student"},
                schoolsetting: {setting_key: "import_student"},
                locale: {page: ["students", "upload"]},
                examyear_rows: {get: true},
                school_rows: {get: true},
                department_rows: {get: true},
                level_rows: {get: true},
                sector_rows: {get: true},
                student_rows: {get: true},
                studentsubject_rows: {get: true},
                scheme_rows: {get: true},
                schemeitem_rows: {get: true}
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
                let isloaded_loc = false, isloaded_settings = false, isloaded_permits = false;

                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                    mimp_loc = loc;
                    isloaded_loc = true;
                };

                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict
                    selected_btn = (setting_dict.sel_btn)
                    isloaded_settings = true;
                };

                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    // get_permits must come before CreateSubmenu and FiLLTbl
                    b_get_permits_from_permitlist(permit_dict);
                    //get_permits(permit_dict.permit_list);
                    //usergroups = permit_dict.usergroup_list;
                    isloaded_permits = true;
                }
                if ("schoolsetting_dict" in response) {
                    i_UpdateSchoolsettingsImport(response.schoolsetting_dict)
                };
                // both 'loc' and 'setting_dict' are needed for CreateSubmenu
                if (isloaded_loc && isloaded_settings) {CreateSubmenu()};
                if(isloaded_settings || isloaded_permits){b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school)};

                if ("examyear_rows" in response) { b_fill_datamap(examyear_map, response.examyear_rows)};
                if ("school_rows" in response)  { b_fill_datamap(school_map, response.school_rows)};
                if ("department_rows" in response) { b_fill_datamap(department_map, response.department_rows)};

                if ("level_rows" in response)  {
                    b_fill_datamap(level_map, response.level_rows);
                };
                if ("sector_rows" in response) {
                    b_fill_datamap(sector_map, response.sector_rows);
                };

                if ("student_rows" in response) {
                    const tblName = "student";
                    const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                    RefreshDataMap(tblName, field_names, response.student_rows, student_map, false)  // false = no update
                }
                //if ("studentsubject_rows" in response)  { b_fill_datamap(studentsubject_map, response.studentsubject_rows) };
                //if ("scheme_rows" in response)  { b_fill_datamap(scheme_map, response.scheme_rows) };
                //if ("schemeitem_rows" in response)  { b_fill_datamap(schemeitem_map, response.schemeitem_rows) };

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

//=========  CreateSubmenu  ===  PR2020-07-31
    function CreateSubmenu() {
        //console.log("===  CreateSubmenu == ");
        //console.log("loc.Add_subject ", loc.Add_subject);
        //console.log("loc ", loc);

        let el_submenu = document.getElementById("id_submenu")
            AddSubmenuButton(el_submenu, loc.Add_candidate, function() {MSTUD_Open()});
            AddSubmenuButton(el_submenu, loc.Delete_candidate, function() {ModConfirmOpen("delete")});
            AddSubmenuButton(el_submenu, loc.Upload_candidates, function() {MIMP_Open("import_student")}, "id_submenu_import");

         el_submenu.classList.remove(cls_hide);
    };//function CreateSubmenu

//###########################################################################
//=========  HandleBtnSelect  ================ PR2020-09-19  PR2020-11-14
    function HandleBtnSelect(data_btn, skip_upload) {
        console.log( "===== HandleBtnSelect ========= ", data_btn);
        selected_btn = data_btn
        if(!selected_btn){selected_btn = "btn_student"}

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_student: {sel_btn: selected_btn}};
            UploadSettings (upload_dict, url_settings_upload);
        };

// ---  highlight selected button
        highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  show only the elements that are used in this tab
        show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

// ---  fill sidebar selecttable students
        SBR_FillSelectTable();

// ---  fill datatable
        CreateTblHeader();
        FillTblRows();

// --- update header text
        UpdateHeaderText();
    }  // HandleBtnSelect

//=========  HandleTableRowClicked  ================ PR2020-08-03
    function HandleTableRowClicked(tr_clicked) {
        //console.log("=== HandleTableRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

        selected_student_pk = null;

// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        DeselectHighlightedRows(tr_clicked, cls_selected);
        tr_clicked.classList.add(cls_selected)

// ---  update selected_student_pk
        // only select employee from select table
        const row_id = tr_clicked.id
        if(row_id){
            const map_dict = get_mapdict_from_datamap_by_id(student_map, row_id)
            selected_student_pk = map_dict.id;
        }
    }  // HandleTableRowClicked


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

//=========  CreateTblHeader  === PR2020-07-31
    function CreateTblHeader() {
        //console.log("===  CreateTblHeader ===== ");
        const tblName = get_tblName_from_selectedBtn();

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

        const field_setting = field_settings[tblName]
        //console.log("tblName", tblName);
        //console.log("field_setting", field_setting);
        if(field_setting){
            const column_count = field_setting.field_names.length;

//--- get info from selected department_map
            const dep_dict = get_mapdict_from_datamap_by_tblName_pk(department_map, "department", setting_dict.sel_department_pk);

            let sct_caption = null, lvl_req = false, sct_req = false;
            if(dep_dict){
                sct_caption = (dep_dict.sct_caption) ? dep_dict.sct_caption : null;
                lvl_req = (dep_dict.lvl_req) ? dep_dict.lvl_req : false;
                sct_req = (dep_dict.sct_req) ? dep_dict.sct_req : false;
            }

            // TODO hide col level when lvl_req = false, but implement col_hidden
//--- insert table rows
            let tblRow_header = tblHead_datatable.insertRow (-1);
            let tblRow_filter = tblHead_datatable.insertRow (-1);

//--- insert th's to tblHead_datatable
            for (let j = 0; j < column_count; j++) {
                const key = field_setting.field_caption[j];
                let caption = (loc[key]) ? loc[key] : key;

                const field_name = field_setting.field_names[j];
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
                        } else {
// --- add innerText to el_div
                            if(field_name === "sct_abbrev"){
                                const dep_dict = get_mapdict_from_datamap_by_tblName_pk(department_map, "department", setting_dict.sel_department_pk);
        console.log("dep_dict", dep_dict);
                                if(dep_dict && dep_dict.sct_caption){
        console.log("dep_dict.sct_caption", dep_dict.sct_caption);
                                   // const caption_text = (dep_dict.sct_caption.toLowerCase() === "sector") ? mimp_loc.Link_sectors :
                                    //(dep_dict.sct_caption.toLowerCase() === "profiel") ? mimp_loc.Link_profielen : null;
                                    //if(caption_text){ document.getElementById("id_MIMP_header_sector").innerText = caption_text};
                                }
                            }

                            if(caption) {el_header.innerText = caption};

                            if(field_name === "examnumber"){
                                el_header.classList.add("pr-2")
                            }
                        };
// --- add width, text_align
                        el_header.classList.add(class_width, class_align);
                    th_header.appendChild(el_header)
                tblRow_header.appendChild(th_header);

// ++++++++++ create filter row +++++++++++++++
                tblRow_filter.setAttribute("data-table", tblName);
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
                    } else if (["toggle", "activated", "inactive"].indexOf(filter_tag) > -1) {
                        // default empty icon necessary to set pointer_show
                        // default empty icon necessary to set pointer_show
                        append_background_class(el_filter,"tickmark_0_0");
                    }

// --- add width, text_align
                    el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");
                th_filter.appendChild(el_filter)
                tblRow_filter.appendChild(th_filter);
            }  // for (let j = 0; j < column_count; j++)

        }  // if(field_settings[tblName]){
    };  //  CreateTblHeader

//========= FillTblRows  ====================================
    function FillTblRows() {
        //console.log( "===== FillTblRows  === ");
        const tblName = get_tblName_from_selectedBtn()
        const data_map = get_datamap_from_tblName(tblName);
        //console.log( "tblName", tblName);
        //console.log( "data_map", data_map);

// --- reset table
        tblBody_datatable.innerText = null
        if(data_map){
// --- loop through data_map
          for (const [map_id, map_dict] of data_map.entries()) {

                //console.log( "map_dict ", map_dict);
          // --- insert row at row_index
                const schoolcode_lc_trail = ( (map_dict.sb_code) ? map_dict.sb_code.toLowerCase() : "" ) + " ".repeat(8) ;
                const schoolcode_sliced = schoolcode_lc_trail.slice(0, 8);
                const order_by = schoolcode_sliced +  ( (map_dict.username) ? map_dict.username.toLowerCase() : "");
                const row_index = -1; // t_get_rowindex_by_sortby(tblBody_datatable, order_by)
                let tblRow = CreateTblRow(tblBody_datatable, tblName, map_id, map_dict, row_index)
          };
        }  // if(!!data_map)

    }  // FillTblRows

//=========  CreateTblRow  ================ PR2020-06-09
    function CreateTblRow(tblBody, tblName, map_id, map_dict, row_index) {
        //console.log("=========  CreateTblRow =========", tblName);
        //console.log("map_dict", map_dict);

        let tblRow = null;

        const field_setting = field_settings[tblName]
        if(field_setting){
            const field_names = field_setting.field_names;
            const field_align = field_setting.field_align;
            const column_count = field_names.length;

// --- insert tblRow into tblBody at row_index
            tblRow = tblBody.insertRow(row_index);
            tblRow.id = map_id
            const order_by = (map_dict.fullname) ? map_dict.fullname.toLowerCase() : null;
// --- add data attributes to tblRow
            tblRow.setAttribute("data-table", tblName);
            if (tblName === "student"){
                tblRow.setAttribute("data-pk", map_dict.id);
                //tblRow.setAttribute("data-ppk", map_dict.company_id);
            }
            tblRow.setAttribute("data-sortby", order_by);

// --- add EventListener to tblRow
            tblRow.addEventListener("click", function() {HandleTableRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
            for (let j = 0; j < column_count; j++) {
                const field_name = field_names[j];
// --- insert td element,
                let el_td = tblRow.insertCell(-1);
// --- add data-field attribute
                el_td.setAttribute("data-field", field_name);

                if (field_name === "select") {
                    // TODO add select multiple users option PR2020-08-18
                } else if (["examnumber", "lastname", "firstname", "gender", "idnumber", "db_code", "lvl_abbrev", "sct_abbrev",
                            "fullname", "subj_code", "subj_name", "sjt_abbrev"].indexOf(field_name) > -1){
                    if(tblName === "student"){
                        el_td.addEventListener("click", function() {MSTUD_Open(el_td)}, false)
                    } else if(tblName === "studsubj"){
                        el_td.addEventListener("click", function() {MSTUDSUBJ_Open(el_td)}, false)

                    }
                    el_td.classList.add("pointer_show");
                    add_hover(el_td);

                    if(field_name === "examnumber"){el_td.classList.add("pr-4")}
                }
// --- add  text_align
               el_td.classList.add("ta_" + field_align[j]);
// --- put value in field
               UpdateField(el_td, map_dict)
            }  // for (let j = 0; j < 8; j++)
        }  // if(field_settings_table)
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
            const fld_value = map_dict[field_name];
            if(field_name){
                if (field_name === "select") {
                    // TODO add select multiple users option PR2020-08-18
                } else if (["examnumber", "lastname", "firstname", "gender", "idnumber", "db_code", "lvl_abbrev", "sct_abbrev",
                            "fullname", "subj_code", "subj_name", "sjt_abbrev"].indexOf(field_name) > -1){
                    el_div.innerText = (fld_value) ? fld_value : null;
                }
            }  // if(field_name)
        }  // if(el_div)
    };  // UpdateField


// +++++++++++++++++ UPLOAD CHANGES +++++++++++++++++ PR2020-08-03

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
                        RefreshDataMap(tblName, field_names, response.updated_student_rows, student_map, true)  // true = update
                    };
                    $("#id_mod_student").modal("hide");

                    if ("updated_studsubj_rows" in response) {
                        const tblName = "studsubj";
                        const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                        RefreshDataMap(tblName, field_names, response.updated_studsubj_rows, studentsubject_map, true)  // true = update
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
        console.log("permit_dict.crud_student", permit_dict.crud_student)
        if (permit_dict.crud_student){

            let user_pk = null, user_country_pk = null, user_schoolbase_pk = null, mapid = null;
            const fldName = get_attr_from_el(el_input, "data-field");

            // el_input is undefined when called by submenu btn 'Add new'
            const is_addnew = (!el_input);
            mod_MSTUD_dict = {}
            let tblName = "student";
            if(is_addnew){
                mod_MSTUD_dict = {is_addnew: is_addnew, db_code: setting_dict.sel_depbase_code}
            } else {
                const tblRow = get_tablerow_selected(el_input);
                const map_dict = get_mapdict_from_datamap_by_id(student_map, tblRow.id);
                mod_MSTUD_dict = deepcopy_dict(map_dict);
            }

    // ---  set header text
            MSTUD_headertext(is_addnew, tblName, mod_MSTUD_dict.name);

    // ---  fill level and sector options, set select team in selectbox
            const selected_pk = null;
            const department_pk = (is_addnew) ? setting_dict.sel_department_pk : mod_MSTUD_dict.dep_id;
            const dep_dict = get_mapdict_from_datamap_by_tblName_pk(department_map, "department", department_pk);
            const depbase_pk = dep_dict.base_id;
            const lvl_req = (dep_dict.lvl_req) ? dep_dict.lvl_req : false;
            const sct_req = (dep_dict.sct_req) ? dep_dict.sct_req : false;

            console.log("dep_dict", dep_dict)
            console.log(",,,,,,,,,,,,,,,,,,,sct_req", sct_req)
            const sct_caption = (dep_dict.has_profiel) ? loc.Profiel : loc.Sector;

            document.getElementById("id_MSTUD_level_label").innerText = loc.Leerweg + ':';
            document.getElementById("id_MSTUD_sector_label").innerText = sct_caption + ':';
            document.getElementById("id_MSTUD_level_select").innerHTML = t_FillOptionLevelSectorFromMap("level", level_map, depbase_pk, selected_pk)
            document.getElementById("id_MSTUD_sector_select").innerHTML = t_FillOptionLevelSectorFromMap("sector", sector_map, depbase_pk, selected_pk)

            const el_MSTUD_level_div = document.getElementById("id_MSTUD_level_div")
            add_or_remove_class(el_MSTUD_level_div, cls_hide, !lvl_req)
            add_or_remove_class(el_MSTUD_level_div, "flex_2", !sct_req, "flex_1")

            const el_MSTUD_sector_div = document.getElementById("id_MSTUD_sector_div")
            add_or_remove_class(el_MSTUD_sector_div, cls_hide, !sct_req)
            add_or_remove_class(el_MSTUD_sector_div, "flex_2", !lvl_req, "flex_1")

    // ---  remove value from el_mod_employee_input
            MSTUD_SetElements();  // true = also_remove_values

            if (!is_addnew){
                //el_MSTUD_abbrev.value = (mod_MSTUD_dict.abbrev) ? mod_MSTUD_dict.abbrev : null;
                //el_MSTUD_name.value = (mod_MSTUD_dict.name) ? mod_MSTUD_dict.name : null;

                const modified_dateJS = parse_dateJS_from_dateISO(mod_MSTUD_dict.modifiedat);
                const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
                const modified_by = (mod_MSTUD_dict.modby_username) ? mod_MSTUD_dict.modby_username : "-";

                document.getElementById("id_MSTUD_msg_modified").innerText = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by
            }

    // ---  set focus to el_MSTUD_abbrev
            //setTimeout(function (){el_MSTUD_abbrev.focus()}, 50);

    // ---  disable btn submit, hide delete btn when is_addnew
           // add_or_remove_class(el_MSTUD_btn_delete, cls_hide, is_addnew )
            //const disable_btn_save = (!el_MSTUD_abbrev.value || !el_MSTUD_name.value  )
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

        if (permit_dict.crud_student){
            const is_delete = (crud_mode === "delete")
            let new_level_pk = null, new_sector_pk = null, level_or_sector_has_changed = false;;
            let upload_dict = {
                table: 'student',
                sel_examyear_pk: setting_dict.sel_examyear_pk,
                sel_schoolbase_pk: setting_dict.sel_schoolbase_pk,
                sel_department_pk: setting_dict.sel_department_pk,
                }
            if(mod_MSTUD_dict.is_addnew) {
                upload_dict.create = true;
            } else {
                upload_dict.student_pk = mod_MSTUD_dict.id;
                upload_dict.mapid = mod_MSTUD_dict.mapid;
                if(is_delete) {upload_dict.delete = true}
            }
    // ---  put changed values of input elements in upload_dict
            //let form_elements = document.getElementById("id_MSTUDSUBJ_div_form_controls").querySelectorAll(".awp_input_text, .awp_input_select")
            let el_MSTUD_div_form_controls = document.getElementById("id_MSTUD_div_form_controls")
            let form_elements = el_MSTUD_div_form_controls.getElementsByClassName("form-control")

            for (let i = 0, el_input; el_input = form_elements[i]; i++) {
                const fldName = get_attr_from_el(el_input, "data-field");
                let new_value = (el_input.value) ? el_input.value : null;
                let old_value = (mod_MSTUD_dict[fldName]) ? mod_MSTUD_dict[fldName] : null;
                if(["lvl_id", "sct_id"].indexOf(fldName) > -1){
                    new_value = (new_value && Number(new_value)) ? Number(new_value) : null;
                    old_value = (old_value && Number(old_value)) ? Number(old_value) : null;
                }
                if (new_value !== old_value) {
                    const field = (fldName === "lvl_id") ? "level" :
                                  (fldName === "sct_id") ? "sector" : fldName;
                    upload_dict[field] = {value: new_value, update: true}
                    if(fldName === "lvl_id"){
                        new_level_pk = new_value;
                        level_or_sector_has_changed = true;
                    } else if(fldName === "sct_id"){
                        new_sector_pk = new_value;
                        level_or_sector_has_changed = true;
                    }
    // put changed new value in tblRow before uploading
                    //const tblRow = document.getElementById(mod_MSTUD_dict.mapid);
                    //if(tblRow){
                    //    const el_tblRow = tblRow.querySelector("[data-field=" + fldName + "]");
                    //    if(el_tblRow){el_tblRow.innerText = new_value };
                    //}
                };
            };

    console.log( "upload_dict.student_pk: ", upload_dict.student_pk);
    console.log( "level_or_sector_has_changed: ", level_or_sector_has_changed);
    console.log( "new_level_pk: ", new_level_pk);
    console.log( "new_sector_pk: ", new_sector_pk);
    // ---  check if schemeitems must be changed when level or sector changes
            if (upload_dict.student_pk){
                if (level_or_sector_has_changed){
                    check_new_scheme(upload_dict.student_pk, new_level_pk, new_sector_pk)
                }
            }
    // ---  get selected departments
            //let dep_list = MSTUD_get_selected_depbases();
            //upload_dict['depbases'] = {value: dep_list, update: true}
    console.log( "upload_dict: ", upload_dict);
            // TODO add loader
            //document.getElementById("id_MSTUD_loader").classList.remove(cls_visible_hide)
            // modal is closed by data-dismiss="modal"
            UploadChanges(upload_dict, url_student_upload);
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
        console.log( "===== MSTUD_InputKeyup  ========= ");
        MSTUD_validate_and_disable();
    }; // MSTUD_InputKeyup

//========= MSTUD_InputSelect  ============= PR2020-12-11
    function MSTUD_InputSelect(el_input){
        console.log( "===== MSTUD_InputSelect  ========= ");
        MSTUD_validate_and_disable();
    }; // MSTUD_InputSelect

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
                const arr = b_get_number_from_input(loc, fldName, el_input.value);
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
    function MSTUD_SetElements(){
        //console.log( "===== MSTUD_SetElements  ========= ");
        //console.log( "mod_MSTUD_dict", mod_MSTUD_dict);
// --- loop through input elements
        let form_elements = el_MSTUD_div_form_controls.querySelectorAll(".form-control")
        for (let i = 0, el, fldName, fldValue, len = form_elements.length; i < len; i++) {
            el = form_elements[i];
            if(el){
                fldName = get_attr_from_el(el, "data-field");
                fldValue = (mod_MSTUD_dict[fldName]) ? mod_MSTUD_dict[fldName] : null;
                el.value = fldValue;
            };
        }

        let full_name = (mod_MSTUD_dict.lastname) ? mod_MSTUD_dict.lastname : "";
        if (mod_MSTUD_dict.prefix) {full_name = mod_MSTUD_dict.prefix + " " + full_name}
        if (mod_MSTUD_dict.firstname) {full_name += ", " + mod_MSTUD_dict.firstname}
        document.getElementById("id_MSTUD_hdr").innerText = full_name;
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
        //document.getElementById("id_MSTUD_label_dep").innerText = loc.Departments_with + this_dep_text + loc.occurs + ":";
    }  // MSTUD_headertext

// +++++++++ END MOD STUDENT +++++++++++++++++++++++++++++++++++++++++


// +++++++++ MOD STUDENT SUBJECT++++++++++++++++ PR2020-11-16
    function MSTUDSUBJ_Open(el_input){
        console.log(" -----  MSTUDSUBJ_Open   ----")
        if(el_input && permit_dict.crud_student){

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

            console.log("stud_pk_int", stud_pk_int)
            console.log("map_dict", map_dict)
            if(!isEmpty(map_dict)) {
                mod_MSTUDSUBJ_dict.stud_id = map_dict.id;
                mod_MSTUDSUBJ_dict.scheme_id = map_dict.scheme_id;

    // ---  set header text
                let header_text = loc.Subjects + loc._of_ + map_dict.fullname
                let dep_lvl_sct_text = (map_dict.db_code) ? map_dict.db_code + " - " : "";
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
                //const disable_btn_save = (!el_MSTUD_abbrev.value || !el_MSTUD_name.value  )
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

        if(permit_dict.crud_student && mod_MSTUDSUBJ_dict.stud_id){
            const upload_dict = {
            table: 'studentsubject',
            sel_examyear_pk: setting_dict.sel_examyear_pk,
            sel_schoolbase_pk: setting_dict.sel_schoolbase_pk,
            sel_depbase_pk: setting_dict.sel_depbase_pk,
            sel_student_pk: mod_MSTUDSUBJ_dict.stud_id
            }
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
                                sel_examyear_pk: setting_dict.sel_examyear_pk,
                                sel_schoolbase_pk: setting_dict.sel_schoolbase_pk,
                                studsubj_id: ss_dict.studsubj_id,
                                schemeitem_id: ss_dict.schemeitem_id,
                                stud_id: ss_dict.stud_id,
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
            }  //  for (const [studsubj_pk, ss_dict] of Object.entries(mod_studsubj_dict)


            if(studsubj_list && studsubj_list.length){
                upload_dict.studsubj_list = studsubj_list;
                console.log("upload_dict: ", upload_dict)
                UploadChanges(upload_dict, url_studsubj_upload);
            }
        };  // if(permit_dict.crud_student && mod_MSTUDSUBJ_dict.stud_id){

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

        const student_pk = mod_MSTUDSUBJ_dict.stud_id
        const scheme_pk = mod_MSTUDSUBJ_dict.scheme_id

        //mod_studsubj_dict = {};
        mod_studsubj_map.clear();
// ---  loop through studentsubject_map
        for (const [map_id, ss_dict] of studentsubject_map.entries()) {

        // add only studsubj from this student
            if (student_pk === ss_dict.stud_id) {
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
            //if(dict.mapid) { tblRow.id = "MSTUDSUBJ_" + dict.mapid }
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
                el_div.classList.add("tw_120")
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

        let sjt_has_prac = false, sjt_has_pws = false;

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

//========= MSTUDSUBJ_AddRemoveSubject  ============= PR2020-11-18
    function MSTUDSUBJ_AddRemoveSubject(mode) {
        console.log("  =====  MSTUDSUBJ_AddRemoveSubject  =====");
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
                    const student_pk = mod_MSTUDSUBJ_dict.stud_id
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

    }  // MSTUDSUBJ_AddRemoveSubject

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
// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2020-08-03
    function ModConfirmOpen(mode, el_input) {
        console.log(" -----  ModConfirmOpen   ----")
        // values of mode are : "delete", "inactive" or "resend_activation_email", "permission_sysadm"

        if(permit_dict.crud_student){


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
        let close_modal = !permit_dict.crud_student;

        if(permit_dict.crud_student){
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

//###########################################################################
// +++++++++++++++++ REFRESH DATA MAP ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataMap  ================ PR2020-08-16 PR2020-09-30
    function RefreshDataMap(tblName, field_names, data_rows, data_map, is_update) {
        //console.log(" --- RefreshDataMap  ---");
        // PR2021-01-13 debug: when data_rows = [] then !!data_rows = true. Must add !!data_rows.length
        if (data_rows && data_rows.length ) {
            const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
            for (let i = 0, update_dict; update_dict = data_rows[i]; i++) {
                RefreshDatamapItem(tblName, field_names, update_dict, data_map);
            }
        } else {
            // empty the datamap when data_rows is empty PR2021-01-13 debug forgot to empty data_map
            // PR2021-03-13 debug. Don't empty de data_map when is update. Returns [] when no changes made
           if(!is_update) {data_map.clear()};
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

// ++++ created ++++
            if(is_created){
    // ---  insert new item
                data_map.set(map_id, update_dict);
                updated_columns.push("created")
    // ---  create row in table., insert in alphabetical order
                let order_by = (update_dict.fullname) ? update_dict.fullname.toLowerCase() : ""
                const row_index = t_get_rowindex_by_sortby(tblBody_datatable, order_by)
                tblRow = CreateTblRow(tblBody_datatable, tblName, map_id, update_dict, row_index)

    // ---  scrollIntoView,
                if(tblRow){
                    tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' })
    // ---  make new row green for 2 seconds,
                    ShowOkElement(tblRow);
                }
                // ---  remove the row without subject, if it exists
                remove_studsubjrow_without_subject(map_id);

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
    // ---  make update
            // note: when updated_columns is empty, then updated_columns is still true.
            // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
            if(tblRow && updated_columns.length){
    // ---  make entire row green when row is created
                if(updated_columns.includes("created")){
                    ShowOkElement(tblRow);
                } else {
    // loop through cells of row
                    for (let i = 1, el_fldName, el; el = tblRow.cells[i]; i++) {
                        if (el){
                            el_fldName = get_attr_from_el(el, "data-field")
                            UpdateField(el, update_dict);
    // make gield green when field name is in updated_columns
                            if(updated_columns.includes(el_fldName)){
                                ShowOkElement(el);
                            }}}}}
        }
    }  // RefreshDatamapItem


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


//###########################################################################
// +++++++++++++++++ SIDEBAR SELECT TABLE STUDENTS ++++++++++++++++++++++++++

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
                tblRow.setAttribute("data-sortby", order_by);
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
        console.log( "===== HandleFilterField  ========= ");
        // skip filter if filter value has not changed, update variable filter_text

        //console.log( "el_key", el_key);
        //console.log( "col_index", col_index);
        const filter_tag = get_attr_from_el(el, "data-filtertag")
        //console.log( "filter_tag", filter_tag);

// --- get filter tblRow and tblBody
        const tblRow = get_tablerow_selected(el);
        const tblName = get_attr_from_el(tblRow, "data-table")
        //console.log( "tblRow", tblRow);
        //console.log( "tblName", tblName);

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

        t_Filter_TableRows(tblBody_datatable, tblName, filter_dict, false, false, null)
        //Filter_TableRows(tblBody_datatable);
    }; // HandleFilterField

//========= Filter_TableRows  ==================================== PR2020-08-17
    function Filter_TableRows(tblBody) {
        //console.log( "===== Filter_TableRows  ========= ");

        const tblName_settings = (selected_btn === "btn_studsubj") ? "studsubj" : "student";

// ---  loop through tblBody.rows
        for (let i = 0, tblRow, show_row; tblRow = tblBody.rows[i]; i++) {
            show_row = ShowTableRow(tblRow, tblName_settings)
            add_or_remove_class(tblRow, cls_hide, !show_row)
        }
    }; // Filter_TableRows

//========= ShowTableRow  ==================================== PR2020-08-17
    function ShowTableRow(tblRow, tblName_settings) {
        // only called by Filter_TableRows
        console.log( "===== ShowTableRow  ========= ");
        console.log( "filter_dict", filter_dict);
        console.log( "field_settings", field_settings);
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
// +++++++++++++++++ MODAL SELECT EXAMYEAR OR DEPARTMENT  ++++++++++++++++++++
// functions are in table.js, except for MSED_Response

//=========  MSED_Response  ================ PR2020-12-18 PR2021-05-10
    function MSED_Response(new_setting) {
        //console.log( "===== MSED_Response ========= ");

// ---  upload new selected_pk
// also retrieve the tables that have been changed because of the change in examyear / dep
        const datalist_request = {
                setting: new_setting,
                student_rows: {get: true},
                studentsubject_rows: {get: true},
                grade_rows: {get: true},
                schemeitem_rows: {get: true},
                schoolsetting: {setting_key: "import_student"}
            };
        DatalistDownload(datalist_request);

    }  // MSED_Response
//###########################################################################

//========= check_new_scheme  ======== // PR2021-03-13
    function check_new_scheme(student_pk, new_level_pk, new_sector_pk) {
        console.log( "check_new_scheme ");
        console.log( "studentsubject_map", studentsubject_map);
/*
    'PR 3 okt 09:
        'Deze functie controleert VakSchemaItemID in vakkenlijst van kandidaat, nodig wanneer leerweg of sector gewijzigd wordt
            'elk KandVak heeft een VakSchemaItem, dat hoort bij het VakSchema van de leerweg en sector van deze kandidaat
            'Als de leerweg of sector gewijzigd wordt, moet ook het VakSchemaItem van dit KandVak worden aangepast
            'Deze functie controleert:
            '- of het vak ook voorkomt in het nieuwe vakschema. Zo niet, zet een vlag om het vak te wissen
            '- zo ja, of het vak in het nieuwe vakschema ook voorkomt met hetzelfde vaktype.

        'strMsgText = IIf(pblAfd.CurIsHavoVwo, "Het profiel van ", "De leerweg van ") & GetKandidaatNaam(lngKandidaatID) & vbCrLf & "wordt gewijzigd in '" & strAfk_Studierichting & IIf(pblAfd.CurIsHavoVwo, "'.", "', sector  " & strAfk_Sector & ".") & vbCrLf & vbCrLf

*/
// get new scheme
        const lookup_level_pk = (new_level_pk) ? new_level_pk : mod_MSTUD_dict.lvl_id;
        const lookup_sector_pk = (new_sector_pk) ? new_sector_pk : mod_MSTUD_dict.sct_id;
        let new_scheme_pk = null, new_scheme_name = null;
        for (const [map_id, map_dict] of scheme_map.entries()) {
            if (map_dict.department_id === mod_MSTUD_dict.dep_id &&
                map_dict.level_id === lookup_level_pk &&
                map_dict.sector_id === lookup_sector_pk) {
                    new_scheme_pk = map_dict.id;
                    new_scheme_name = map_dict.name;
                    break;
            }
        }
        console.log( "====================== new_scheme_pk", new_scheme_pk);
        console.log( "====================== new_scheme_name", new_scheme_name);

//--- loop through studsubj of this student
        if(student_pk){
            for (const [map_id, map_dict] of studentsubject_map.entries()) {
                if (map_dict.stud_id === student_pk) {
                    const subject_pk = map_dict.subj_id;
                    const subj_name = (map_dict.subj_name) ? map_dict.subj_name : "---";
                    const sjt_abbrev = (map_dict.sjt_abbrev) ? map_dict.sjt_abbrev : "";
                    console.log( "subj_name", subj_name);
                    if (new_scheme_pk == null) {
                        // delete studsub when no scheme
                        // skip when studsub scheme equals new_scheme
                    } else if (map_dict.scheme_id !== new_scheme_pk){
                        // check how many times this subject occurs in new scheme
                        const [count, count_same_subjecttype, new_schemeitem_pk] = count_subject_in_newscheme(new_scheme_pk, subject_pk)
                    console.log( "count", count);
                    console.log( "count_same_subjecttype", count_same_subjecttype);
                    console.log( "new_schemeitem_pk", new_schemeitem_pk);
                        if (!count) {
                    console.log( "delete studsub , subject does not exist in new_scheme");
                        } else if (count === 1 ) {
                            // if subject occurs only once in mew_scheme: replace schemeitem by new schemeitem
                    console.log( "subject occurs only once in mew_scheme: replace schemeitem by new schemeitem");
                        } else {
                            // if subject occurs multiple times in mew_scheme: check if one exist with same subjecttype
                            if (count_same_subjecttype === 1) {
                                // if only one exist with same subjecttype: replace schemeitem by new schemeitem
                    console.log( "only one exist with same subjecttype");
                            } else {
                                // if no schemeitem exist with same subjecttype: get schemeitem with lowest sequence
                    console.log( "no schemeitem exist with same subjecttype");
                            }
                        }
                    }
                }
            }
        }
    }
//========= count_subject_in_newscheme  ======== // PR2021-03-13
    function count_subject_in_newscheme(scheme_pk, subject_pk, subjecttype_pk) {
        console.log( " =====  count_subject_in_newscheme  ===== ");
        console.log( "scheme_pk", scheme_pk);
        console.log( "subject_pk", subject_pk);
        // check how many times this subject occurs in new scheme
        let count = 0, count1_schemeitem_pk = null;
        let count_same_subjecttype = 0, samesubjecttype_schemeitem_pk = null;
        let lowestsequence_schemeitem_pk = null, lowest_sequence = null;
        if(scheme_pk && subject_pk){
            for (const [map_id, map_dict] of schemeitem_map.entries()) {
                if (map_dict.scheme_id === scheme_pk && map_dict.subj_id === subject_pk) {
                    count += 1;
                    count1_schemeitem_pk = (count === 1) ? map_dict.id : null;
                    if (subjecttype_pk && map_dict.sjt_id === subjecttype_pk) {
                        count_same_subjecttype += 1;
                        samesubjecttype_schemeitem_pk = (count_same_subjecttype === 1) ? map_dict.id : null;
                    }
                    if (lowest_sequence == null || map_dict.sequence < lowest_sequence) {
                        lowest_sequence = map_dict.sjt_sequence;
                        lowestsequence_schemeitem_pk = map_dict.id;
                    }
                }
            }
        }
        let new_schemeitem_pk = null;
        if (count === 1){
            new_schemeitem_pk = count1_schemeitem_pk;
        } else if (count_same_subjecttype === 1){
            new_schemeitem_pk = samesubjecttype_schemeitem_pk;
        } else if (lowestsequence_schemeitem_pk){
            new_schemeitem_pk = lowestsequence_schemeitem_pk;
        }
        return [count, count_same_subjecttype, new_schemeitem_pk ]
    }

//========= get_schemeitem_with_same_subjtype  ======== // PR2021-03-13
    function get_schemeitem_with_same_subjtype(scheme_pk, subject_pk) {
        console.log( " =====  get_schemeitem_with_same_subjtype  ===== ");
        console.log( "scheme_pk", scheme_pk);
        console.log( "subject_pk", subject_pk);
        // check how many times this subject occurs in new scheme
        let count = 0;
        if(scheme_pk && subject_pk){
            for (const [map_id, map_dict] of schemeitem_map.entries()) {
        console.log( "map_dict", map_dict);
                if (map_dict.scheme_id === scheme_pk && map_dict.subject_id === subject_pk) {
                    count += 1;
                }
            }
        }
    }


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

})  // document.addEventListener('DOMContentLoaded', function()