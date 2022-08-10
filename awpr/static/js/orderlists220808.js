// PR2020-09-29 added

//let selected_btn = "btn_user";
//let setting_dict = {};
//let permit_dict = {};
//let loc = {};
//let urls = {};

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
    let department_map = new Map();
    let level_map = new Map();
    let sector_map = new Map();
    let student_map = new Map();
    let subject_map = new Map();

    let student_rows = [];
    let subject_rows = [];
    //let studentsubject_rows = [];
    let schemeitem_rows = [];

    let orderlist_rows = [];
    let envelopbundle_rows = [];
    let enveloplabel_rows = [];
    let envelopbundlelabel_rows = [];
    let envelopitem_rows = [];
    let enveloplabelitem_rows = [];

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

    mod_MCOL_dict.columns.btn_orderlist = {
        school_abbrev: "School_name", total_students: "Number_of_candidates",
        total: "Number_of_entered_subjects", publ_count: "Number_of_submitted_subjects", datepublished: "Date_submitted"
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

        ete_exam: { field_caption: ["", "Abbrev_subject_2lines", "Subject", "Learning_path", "Version",
                                "Exam_type", "Designated_exam_2lines", "Blanks", "Maximum_score_2lines", "",
                                "Download_exam", "Cesuur", "Download_conv_table_2lines"],
                field_names: ["select", "subjbase_code", "subj_name", "lvl_abbrev", "version",
                                "examperiod", "secret_exam", "blanks", "scalelength", "status",
                                "download_exam", "cesuur", "download_conv_table"],
                field_tags: ["div", "div", "div", "div", "div",
                            "div", "div", "div", "div", "div",
                            "a", "input", "a"],
                filter_tags: ["text",  "text", "text", "text", "text",
                              "text", "toggle", "text", "text", "status",
                              "text", "text", "text"],
                field_width: ["020", "075", "240", "120", "120",
                              "150", "090", "075", "075","032",
                              "090", "075", "100"],
                field_align: ["c",  "c", "l", "l", "l",
                               "l", "c", "c","c", "c",
                               "c", "c", "c"]},

        enveloplabel: {field_caption: ["", "Label_name", "Exams_per_envelop", "Number_of_envelops"],
                    field_names: ["select", "name", "numberperexam", "numberfixed"],
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
            // TODO replace school_map by school_rows
            el_hdrbar_school.addEventListener("click",
                function() {t_MSSSS_Open(loc, "school", school_map, false, setting_dict, permit_dict, MSSSS_Response)}, false );
        }

// ---  SIDEBAR ------------------------------------
        const el_SBR_select_level = document.getElementById("id_SBR_select_level");
        if(el_SBR_select_level){el_SBR_select_level.addEventListener("change", function() {HandleSbrLevelSector("level", el_SBR_select_level)}, false )};
        const el_SBR_select_sector = document.getElementById("id_SBR_select_sector");
        if(el_SBR_select_sector){el_SBR_select_sector.addEventListener("change", function() {HandleSbrLevelSector("sector", el_SBR_select_sector)}, false)};
        const el_SBR_select_subject = document.getElementById("id_SBR_select_subject");
        if(el_SBR_select_subject){el_SBR_select_subject.addEventListener("click",
                function() {t_MSSSS_Open(loc, "subject", subject_map, true, setting_dict, permit_dict, MSSSS_Response)}, false)};
        const el_SBR_select_student = document.getElementById("id_SBR_select_student");
        if(el_SBR_select_student){el_SBR_select_student.addEventListener("click",
                function() {t_MSSSS_Open(loc, "student", student_map, true, setting_dict, permit_dict, MSSSS_Response)}, false)};
        const el_SBR_select_showall = document.getElementById("id_SBR_select_showall");
        if(el_SBR_select_showall){el_SBR_select_showall.addEventListener("click", function() {HandleShowAll()}, false)};

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
        const el_MENVLAB_tblBody_available = document.getElementById("id_MENVLAB_tblBody_available");
        const el_MENVLAB_tblBody_selected = document.getElementById("id_MENVLAB_tblBody_selected");

        const el_MENVLAB_name = document.getElementById("id_MENVLAB_name");
        if(el_MENVLAB_name){el_MENVLAB_name.addEventListener("keyup", function() {MENVLAB_InputKeyup(el_MENVLAB_name)}, false)}
        const el_MENVLAB_numberfixed = document.getElementById("id_MENVLAB_numberfixed");
        if(el_MENVLAB_numberfixed){el_MENVLAB_numberfixed.addEventListener("keyup", function() {MENVLAB_InputKeyup(el_MENVLAB_numberfixed)}, false)}
        const el_MENVLAB_numberperexam = document.getElementById("id_MENVLAB_numberperexam");
        if(el_MENVLAB_numberperexam){el_MENVLAB_numberperexam.addEventListener("keyup", function() {MENVLAB_InputKeyup(el_MENVLAB_numberperexam)}, false)}

        const el_MENVLAB_btn_delete = document.getElementById("id_MENVLAB_btn_delete");
        if(el_MENVLAB_btn_delete){el_MENVLAB_btn_delete.addEventListener("click", function() {ModConfirmOpen("delete_envelopitem")}, false)}
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

// ---  MOD SELECT COLUMNS  ------------------------------------
        let el_MCOL_tblBody_available = document.getElementById("id_MCOL_tblBody_available");
        let el_MCOL_tblBody_show = document.getElementById("id_MCOL_tblBody_show");

        const el_MCOL_btn_save = document.getElementById("id_MCOL_btn_save");
        if (el_MCOL_btn_save){ el_MCOL_btn_save.addEventListener("click", function() {ModColumns_Save()}, false )};

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
                department_rows: {get: true},
                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},
                //student_rows: {cur_dep_only: true},
                //studentsubject_rows: {cur_dep_only: true},
                schemeitem_rows: {cur_dep_only: true},

                orderlist_rows: {get: true},
                envelopbundle_rows: {get: true},
                enveloplabel_rows: {get: true},
                envelopbundlelabel_rows: {get: true},
                envelopitem_rows: {get: true},
                enveloplabelitem_rows: {get: true}
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

// ---  fill col_hidden
                    if("col_hidden" in setting_dict){
                        b_clear_array(columns_hidden);
                        for (const [key, value] of Object.entries(setting_dict.col_hidden)) {
                            console.log("key", key)
                            console.log("value", value)
                            console.log("!!value", !!value)
                            if(value){ columns_hidden[key] = value } ;
                        }
                    }
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
                if(must_update_headerbar){b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);};

                if ("examyear_rows" in response) {
                    examyear_rows = response.examyear_rows;
                    b_fill_datamap(examyear_map, response.examyear_rows);
                };
                if ("department_rows" in response) {
                    department_rows = response.department_rows;
                    b_fill_datamap(department_map, response.department_rows)
                };

                if ("school_rows" in response)  { b_fill_datamap(school_map, response.school_rows) };
                if ("level_rows" in response)  { b_fill_datamap(level_map, response.level_rows) };
                if ("sector_rows" in response) { b_fill_datamap(sector_map, response.sector_rows) };

                if ("student_rows" in response) {
                    student_rows = response.student_rows;
                }
                //if ("studentsubject_rows" in response) {
                //    studentsubject_rows = response.studentsubject_rows;
                //};
                if ("schemeitem_rows" in response)  {
                    schemeitem_rows = response.schemeitem_rows;
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
                if ("envelopbundlelabel_rows" in response)  {
                    envelopbundlelabel_rows = response.envelopbundlelabel_rows;
                };
                if ("envelopitem_rows" in response)  {
                    envelopitem_rows = response.envelopitem_rows;
                };
                if ("enveloplabelitem_rows" in response)  {
                    enveloplabelitem_rows = response.enveloplabelitem_rows;
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
            AddSubmenuButton(el_submenu, loc.Preliminary_orderlist, function() {ModConfirmOpen("prelim_orderlist")});
            AddSubmenuButton(el_submenu, loc.Preliminary_orderlist + loc.per_school, function() {ModConfirmOpen("orderlist_per_school")});

            if (permit_dict.permit_submit_orderlist){
                AddSubmenuButton(el_submenu, loc.Publish_orderlist, function() {MPUBORD_Open()});
            };
            if (permit_dict.permit_crud){
                AddSubmenuButton(el_submenu, loc.Variables_for_extra_exams, function() {MOLEX_Open()});

                AddSubmenuButton(el_submenu, loc.New_label_item, function() {MENVIT_Open()});
                AddSubmenuButton(el_submenu, loc.Delete_label_item, function() {ModConfirmOpen("delete_envelopitem")});

                AddSubmenuButton(el_submenu, loc.New_label, function() {MENVLAB_Open()});
                AddSubmenuButton(el_submenu, loc.Delete_label, function() {ModConfirmOpen("delete_enveloplabel")});

            };
            AddSubmenuButton(el_submenu, loc.Hide_columns, function() {t_MCOL_Open("page_orderlist")}, [], "id_submenu_columns")

            el_submenu.classList.remove(cls_hide);
        };

    };//function CreateSubmenu

//###########################################################################
//=========  HandleBtnSelect  ================ PR2020-09-19  PR2020-11-14
    function HandleBtnSelect(data_btn, skip_upload) {
        console.log( "===== HandleBtnSelect ========= ", data_btn);
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
        b_show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

// ---  fill datatable
        FillTblRows();

// --- update header text
        UpdateHeaderText();
    }  // HandleBtnSelect

//=========  HandleTblRowClicked  ================ PR2020-08-03 PR2022-08-04
    function HandleTblRowClicked(tr_clicked) {
        console.log("=== HandleTblRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

// ---  deselect all highlighted rows, select clicked row
        t_td_selected_toggle(tr_clicked, true);  // select_single = true

// --- get existing data_dict from data_rows
        const pk_int = get_attr_from_el_int(tr_clicked, "data-pk");
        const [index, data_dict, compare] = b_recursive_integer_lookup(envelopitem_rows, "id", pk_int);
        selected.envelopitem_pk = (!isEmpty(data_dict)) ? data_dict.id : null;

        console.log( "data_dict: ", data_dict);
        console.log( "selected: ", selected);
    };  // HandleTblRowClicked

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
        console.log( "setting_dict", setting_dict);

        const data_rows = get_datarows_from_selectedbtn();
        const tblName = get_tblName_from_selectedbtn();
        const field_setting = field_settings[tblName]

        console.log( "data_rows", data_rows);
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
                const map_id = data_dict.mapid;
                let tblRow = CreateTblRow(tblName, field_setting, col_hidden, map_id, data_dict)
          };
        }  // if(data_rows)
    } ; // FillTblRows

//=========  CreateTblHeader  === PR2020-07-31
    function CreateTblHeader(field_setting, col_hidden) {
        //console.log("===  CreateTblHeader ===== ");
        //console.log("field_setting", field_setting);

        const column_count = field_setting.field_names.length;

// +++  insert header and filter row ++++++++++++++++++++++++++++++++
        let tblRow_header = tblHead_datatable.insertRow (-1);
        let tblRow_filter = tblHead_datatable.insertRow (-1);

    // --- loop through columns
        for (let j = 0; j < column_count; j++) {
            const field_name = field_setting.field_names[j];
            const field_caption = (loc[field_setting.field_caption[j]]) ? loc[field_setting.field_caption[j]] : field_setting.field_caption[j] ;
            const field_tag = field_setting.field_tags[j];
            const filter_tag = field_setting.filter_tags[j];
            const class_width = "tw_" + field_setting.field_width[j] ;
            const class_align = "ta_" + field_setting.field_align[j];

    // - skip columns if in columns_hidden
            if (!col_hidden.includes(field_name)){

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
                    }

// --- add width, text_align
                    el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");
                th_filter.appendChild(el_filter)
                tblRow_filter.appendChild(th_filter);
            }  //  if (columns_hidden.inludes(field_name))
        }  // for (let j = 0; j < column_count; j++)
    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09 PR2021-03-15 PR2022-08-04
    function CreateTblRow(tblName, field_setting, col_hidden, map_id, data_dict) {
        //console.log("=========  CreateTblRow =========", tblName);
        //console.log("data_dict", data_dict);

        const field_names = field_setting.field_names;
        const field_tags = field_setting.field_tags;
        const filter_tags = field_setting.filter_tags;
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;
    //console.log("field_names", field_names);

// ---  lookup index where this row must be inserted
        const ob1 = (data_dict.content_nl) ? data_dict.content_nl : "";
        const ob2 = (data_dict.instruction_nl) ? data_dict.instruction_nl : "";

        const row_index = b_recursive_tblRow_lookup(tblBody_datatable, setting_dict.user_lang, ob1, ob2);

// --- insert tblRow into tblBody at row_index
        let tblRow = tblBody_datatable.insertRow(row_index);
        if (data_dict.mapid) {tblRow.id = data_dict.mapid};

// --- add data attributes to tblRow
        tblRow.setAttribute("data-table", tblName);
        tblRow.setAttribute("data-pk", data_dict.id);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);
        tblRow.setAttribute("data-ob2", ob2);

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
                if (["content_nl", "instruction_nl"].includes(field_name)){
                    td.addEventListener("click", function() {MENVIT_Open(el)}, false)
                    td.classList.add("pointer_show");
                    add_hover(td);
                } else if (["name", "numberperexam", "numberfixed"].includes(field_name)){
                    td.addEventListener("click", function() {MENVLAB_Open(el)}, false)
                    td.classList.add("pointer_show");
                    add_hover(td);
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
                el_div.innerText = (fld_value) ? fld_value : "\n";
                if (["content_nl", "instruction_nl"].includes(field_name)){
                    const hex_color = (field_name === "content_nl" && data_dict.content_hexcolor) ?
                            data_dict.content_hexcolor :
                        (field_name === "instruction_nl" && data_dict.instruction_hexcolor) ?
                            data_dict.instruction_hexcolor :
                            "#000000";
                    el_div.style.color = hex_color;
                };
    // ---  add attribute filter_value
                const filter_value = (fld_value) ? (typeof fld_value === 'string' || fld_value instanceof String) ?
                                     fld_value.toLowerCase() : fld_value  : null;
                add_or_remove_attr (el_div, "data-filter", !!filter_value, filter_value);
            }  // if(field_name)
        }  // if(el_div)
    };  // UpdateField

//###########################################################################
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

                    if ("updated_envelopitem_rows" in response) {
                        RefreshDataRows("envelopitem", envelopitem_rows, response.updated_envelopitem_rows, true)  // true = update
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
    function ModConfirmOpen(mode) {
        console.log(" -----  ModConfirmOpen   ----")
        console.log("mode", mode)
        // values of mode are : "prelim_orderlist", "orderlist_per_school", "delete_envelopitem

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
        } else if (mode === "delete_envelopitem") {

            const header_txt = loc.Delete_label_item;

// --- get existing data_dict from data_rows
            const pk_int = selected.envelopitem_pk;
            const [index, data_dict, compare] = b_recursive_integer_lookup(envelopitem_rows, "id", pk_int);
            console.log( "data_dict: ", data_dict);
            console.log( "selected: ", selected);

            if (isEmpty(data_dict)){
                b_show_mod_message_html(loc.Please_select_label_item, header_txt);
            } else {
                mod_dict = {
                    mode: mode,
                    table: "envelopitem",
                    envelopitem_pk: data_dict.id,
                    map_id: data_dict.mapid
                };

                const content_nl = (data_dict.content_nl) ? data_dict.content_nl : "---";
                const msg_html = ["<div class='mx-2'>",
                                "<p>", loc.Label_item, " '", content_nl, "' ", loc.will_be_deleted, "</p>",
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

        } else if (mod_dict.mode === "delete_envelopitem") {
            if (permit_dict.permit_crud){
                let upload_dict = {
                    table: "envelopitem",
                    mode: "delete",
                    envelopitem_pk: mod_dict.envelopitem_pk,
                    map_id: mod_dict.map_id
                };
                UploadChanges(upload_dict, urls.url_envelopitem_upload);

                const tblRow = document.getElementById(mod_dict.map_id)
                ShowClassWithTimeout(tblRow, "tsa_tr_error")
            };
        };

// ---  hide modal
        if(close_modal_with_timout) {
        // close modal after 5 seconds
            setTimeout(function (){ $("#id_mod_confirm").modal("hide") }, 5000);
        } else {
            $("#id_mod_confirm").modal("hide");
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
                                published_rows: {get: true}
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

// ++++++++++++  MODAL ENVELOP LABEL  +++++++++++++++++++++++++++++++++++++++

//=========  MENVLAB_Open  ================  PR2022-08-06
    function MENVLAB_Open(el_input) {
        console.log(" -----  MENVLAB_Open   ----")

        console.log("permit_dict.permit_crud", permit_dict.permit_crud)
        console.log("el_input", el_input)

        mod_MENV_dict = {};

        if (permit_dict.permit_crud){
            // el_input is undefined when called by submenu btn 'Add new'
            mod_MENV_dict.is_addnew = (!el_input);

// --- get existing data_dict from enveloplabel_rows
            if(!mod_MENV_dict.is_addnew){
                const tblRow = t_get_tablerow_selected(el_input);
                const pk_int = get_attr_from_el_int(tblRow, "data-pk");
        console.log("pk_int", pk_int)
                const [index, data_dict, compare] = b_recursive_integer_lookup(enveloplabel_rows, "id", pk_int);
        console.log("data_dict", data_dict)
                if (!isEmpty(data_dict)) {
                    mod_MENV_dict.enveloplabel_pk = data_dict.id;
                    mod_MENV_dict.name = data_dict.name;
                    mod_MENV_dict.numberperexam = data_dict.numberperexam;
                    mod_MENV_dict.modby_username = data_dict.modby_username;
                    mod_MENV_dict.modifiedat = data_dict.modifiedat;
                    mod_MENV_dict.numberfixed = data_dict.numberfixed;
                }
            };

            MENVLAB_FillDictlist();
            MENVLAB_FillTable();
            MENVLAB_SetInputElements();
        console.log("mod_MENV_dict", mod_MENV_dict)

            el_MENVLAB_header.innerText = (mod_MENV_dict.is_addnew) ? loc.New_label : loc.Edit_label;

            if (!mod_MENV_dict.is_addnew){

                const modified_dateJS = parse_dateJS_from_dateISO(mod_MENV_dict.modifiedat);
                const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
                const modified_by = (mod_MENV_dict.modby_username) ? mod_MENV_dict.modby_username : "-";
                const display_txt = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by;
                document.getElementById("id_MENVIT_msg_modified").innerText = display_txt;
            };

    // ---  disable btn submit, hide delete btn when is_addnew
        //console.log( "el_MENVLAB_btn_delete: ", el_MENVLAB_btn_delete);
        //console.log( "is_addnew: ", is_addnew);
            add_or_remove_class(el_MENVLAB_btn_delete, cls_hide, mod_MENV_dict.is_addnew );
            //const disable_btn_save = (!el_MENVLAB_abbrev.value || !el_MENVLAB_name.value  )
            //el_MENVLAB_btn_save.disabled = disable_btn_save;

            MENVLAB_validate_and_disable();

            set_focus_on_el_with_timeout(el_MENVLAB_name, 50);
// show modal
            $("#id_mod_enveloplabel").modal({backdrop: true});
        };
    };  // MENVLAB_Open


    function MENVLAB_FillDictlist(){
       console.log(" -----  MENVLAB_FillDictlist   ----")
// - fill columns_excl_skipped
        mod_MENV_dict.envelopitems = [];

// - loop through envelopitem_rows and add to mod_MENV_dict
       for (let i = 0, envelopitem; envelopitem = envelopitem_rows[i]; i++) {

            const enveloplabel_pk = (mod_MENV_dict.enveloplabel_pk) ? mod_MENV_dict.enveloplabel_pk : null;
            const envelopitem_pk = (envelopitem.id) ? envelopitem.id : null;
            let is_selected = false, labelitem_pk = null, labelitem_sequence = null;
            if (envelopitem_pk){

// - check if this item is in list of labelitems of this label
                for (let j = 0, labelitem_dict; labelitem_dict = enveloplabelitem_rows[j]; j++) {
                // only check labelitems of this label
                    if(labelitem_dict.enveloplabel_id === enveloplabel_pk &&
                        labelitem_dict.envelopitem_id === envelopitem_pk
                        ) {
                            is_selected = true;
                            labelitem_pk = labelitem_dict.id
                            labelitem_sequence = labelitem_dict.sequence
                            break;
                    };
                }
            };

            mod_MENV_dict.envelopitems.push({
                envelopitem_pk: envelopitem_pk,
                labelitem_pk: labelitem_pk,
                labelitem_sequence: labelitem_sequence,
                sortby: envelopitem.content_nl,
                selected: is_selected
            });
        };
        mod_MENV_dict.envelopitems.sort(b_comparator_sortby);
        console.log("mod_MENV_dict", mod_MENV_dict)
    };  // MENVLAB_FillDictlist

//=========  MENVLAB_Save  ================   PR2022-08-06
    function MENVLAB_Save(crud_mode) {
        console.log(" -----  MENVLAB_save  ----", crud_mode);
        console.log( "mod_MENV_dict: ", mod_MENV_dict);

        if (permit_dict.permit_crud){
            const is_create = (mod_MENV_dict.is_addnew);
            const is_delete = (crud_mode === "delete");
            const upload_mode = (is_create) ? "create" : (is_delete) ? "delete" : "update"

    // ---  put changed values of input elements in upload_dict
            const name = el_MENVLAB_name.value;
            const numberfixed = (el_MENVLAB_numberfixed.value && Number(el_MENVLAB_numberfixed.value)) ? Number(el_MENVLAB_numberfixed.value) : null;
            const numberperexam = (el_MENVLAB_numberperexam.value && Number(el_MENVLAB_numberperexam.value)) ? Number(el_MENVLAB_numberperexam.value) : null;

            let upload_dict = {
                table: 'enveloplabel',
                mode: upload_mode,
                enveloplabel_pk: mod_MENV_dict.enveloplabel_pk,
                name: name,
                numberfixed: numberfixed,
                numberperexam: numberperexam,
                labelitem_list: []
            };


// loop through envelopitems
            for (let i = 0, menv_dict; menv_dict = mod_MENV_dict.envelopitems[i]; i++) {
                upload_dict.labelitem_list.push({
                    envelopitem_pk: menv_dict.envelopitem_pk,
                    labelitem_pk: menv_dict.labelitem_pk,
                    labelitem_sequence: menv_dict.labelitem_sequence,
                    selected: menv_dict.selected
                });
            };
            UploadChanges(upload_dict, urls.url_enveloplabel_upload);
        };
    // ---  hide modal
            $("#id_mod_enveloplabel").modal("hide");
    } ; // MENVLAB_Save

//========= MENVLAB_FillTable  ============= PR2022-08-06
    function MENVLAB_FillTable(just_linked_unlinked_pk) {
        console.log("===== MENVLAB_FillTable ===== ");

        el_MENVLAB_tblBody_available.innerText = null;
        el_MENVLAB_tblBody_selected.innerText = null;

// ---  loop through mod_MENV_dict.envelopitems
        //mod_MENV_dict.envelopitems = [ {envelopitem_pk: data_dict.id, sortby: data_dict.content_nl, selected: false } ]
        for (let i = 0, data_dict; data_dict = mod_MENV_dict.envelopitems[i]; i++) {
        console.log("data_dict", data_dict);
        console.log("data_dict.selected", data_dict.selected);
            const tblBody = (data_dict.selected) ? el_MENVLAB_tblBody_selected : el_MENVLAB_tblBody_available;
            MENVLAB_CreateTblRow(tblBody, data_dict, data_dict.selected,  just_linked_unlinked_pk);
        };
    }; // MENVLAB_FillTable


//========= MENVLAB_CreateTblRow  ============= PR2022-08-06
    function MENVLAB_CreateTblRow(tblBody, data_dict, is_table_selected, just_linked_unlinked_pk) {
        //console.log("===== MENVLAB_CreateTblRow ===== ");
        //console.log("data_dict", data_dict);

//--- get info from data_dict
        const pk_int = (data_dict.envelopitem_pk) ? data_dict.envelopitem_pk : null;
        const caption = (data_dict.sortby) ? data_dict.sortby : null;

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
                el_div.title = "Click to move this item up."
            td.appendChild(el_div);
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                el_div.classList.add("tw_020")
                el_div.innerHTML = "&#9661;"
                el_div.title = "Click to move this item down."
            td.appendChild(el_div);
        };
//--------- add addEventListener

    }; // MENVLAB_CreateTblRow

//=========  MENVLAB_SelectItem  ================ PR2022-08-07
    function MENVLAB_SelectItem(tblRow) {
        console.log( "===== MENVLAB_SelectItem ========= ");
        console.log( "tblRow", tblRow);
        // all data attributes are now in tblRow, not in el_select = tblRow.cells[0].children[0];

// ---  get clicked tablerow
        if(tblRow) {
            let just_linked_unlinked_pk = null;
            const pk_int = get_attr_from_el_int(tblRow, "data-pk");
            for (let i = 0, data_dict; data_dict = mod_MENV_dict.envelopitems[i]; i++) {
        console.log( "data_dict.envelopitem_pk", data_dict.envelopitem_pk);
        console.log( "pk_int", pk_int);
                if(data_dict.envelopitem_pk === pk_int){
                    data_dict.selected = !data_dict.selected;
        console.log( "data_dict.selected", data_dict.selected);
                    just_linked_unlinked_pk = data_dict.envelopitem_pk;
                    break;
                };
            };
        console.log( "just_linked_unlinked_pk", just_linked_unlinked_pk);

        MENVLAB_FillTable(just_linked_unlinked_pk);

        console.log( "mod_MENV_dict.envelopitems", mod_MENV_dict.envelopitems);
// ---  save and close
            //MENVLAB_Save();
        }
    }  // MENVLAB_SelectItem

//=========  MENVLAB_InputKeyup  ================ PR2022-08-08
    function MENVLAB_InputKeyup(el_input) {
        console.log( "===== MENVLAB_InputKeyup  ========= ");
        const fldName = get_attr_from_el(el_input, "data-field");
// ---  get value of new_filter
        let new_value = el_input.value;
        console.log( "new_value", new_value);
        if(!new_value) {

        } else {

            if (["numberperexam", "numberfixed"].includes(fldName)) {
                if(!Number(new_value)){
                    el_input.value = null;
        console.log( "not Number");
                } else {
                    const value_number = Number(new_value);
        console.log( "value_number", value_number);
                    if(!Number.isInteger(value_number)){
                        el_input.value = null;
        console.log( "not Number.isInteger");
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
                }

            } else {
            //el_MENVLAB_name
            }
        }
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


//=========  RefreshDatarowItem  ================ PR2020-08-16 PR2020-09-30 PR2021-06-21
    function RefreshDatarowItem(tblName, field_setting, data_rows, update_dict) {
        console.log(" --- RefreshDatarowItem  ---");
        //console.log("tblName", tblName);
        console.log("update_dict", update_dict);
        console.log("field_setting.field_names", field_setting.field_names);

        if(!isEmpty(update_dict)){
            // add color fields to fieldnames
            // _color is used in modal from, _hexcol is used in tblRow
            const field_names = ["content_color", "instruction_color", "content_hexcolor", "instruction_hexcolor"]
            if(field_setting.field_names && field_setting.field_names.length){
                // use i < lenn, otherwise loop stops at first blank item ""
                for (let i = 0, len = field_setting.field_names.length; i < len; i++) {
                    const field_name = field_setting.field_names[i];
                    if (field_name){
                        field_names.push(field_name);
                    };
                };
            };
        console.log("field_names", field_names);

            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);

        console.log("map_id", map_id);
        console.log("is_deleted", is_deleted);
        console.log("is_created", is_created);

            const error_list = get_dict_value(update_dict, ["error"], []);
        console.log("error_list", error_list);

            const data_rows = get_datarows_from_selectedbtn()

            let updated_columns = [];
            let field_error_list = []
            if(error_list && error_list.length){

    // - show modal messages
                b_show_mod_message_dictlist(error_list);

    // - add fields with error in field_error_list, to put old value back in field
                for (let i = 0, msg_dict ; msg_dict = error_list[i]; i++) {
                    if ("field" in msg_dict){field_error_list.push(msg_dict.field)};
                };
            //} else {
            // close modal MSJ when no error --- already done in modal
                //$("#id_mod_subject").modal("hide");
            }
// ---  get list of hidden columns
            const col_hidden = b_copy_array_to_new_noduplicates(mod_MCOL_dict.cols_hidden);
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
    // ---  create row in table., insert in alphabetical order
                const new_tblRow = CreateTblRow(tblName, field_setting, col_hidden, map_id, update_dict)
    // ---  scrollIntoView,
                if(new_tblRow){
                    new_tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' })
    // ---  make new row green for 2 seconds,
                    ShowOkElement(new_tblRow);
                }
            } else {

// +++ get existing data_dict from data_rows
                const [datarow_index, data_dict, compare] = b_recursive_lookup(data_rows, map_id, setting_dict.user_lang);

// ++++ deleted ++++
                if(is_deleted){
                    // delete row from data_rows. Splice returns array of deleted rows
                    const deleted_row_arr = data_rows.splice(datarow_index, 1)
                    const deleted_row_dict = deleted_row_arr[0];
    //--- delete tblRow
                    const tblRow_tobe_deleted = document.getElementById(update_dict.mapid);
    // ---  when delete: make tblRow red for 2 seconds, before uploading
                    //ShowClassWithTimeout(tblRow_tobe_deleted, "tsa_tr_error");
                    tblRow_tobe_deleted.classList.add("tsa_tr_error")
                    setTimeout(function() {
                        tblRow_tobe_deleted.parentNode.removeChild(tblRow_tobe_deleted)
                    }, 2000);
                } else {

// +++++++++++ updated row +++++++++++
    // ---  check which fields are updated, add to list 'updated_columns'
                    if(!isEmpty(data_dict) && field_names){
            console.log("data_dict", data_dict);

                        for (let i = 0, col_field, old_value, new_value; col_field = field_names[i]; i++) {

            console.log("col_field", col_field);
            console.log("old_value", data_dict[col_field]);
            console.log("new_value", update_dict[col_field]);

                            if (col_field in data_dict && col_field in update_dict){
                                if (data_dict[col_field] !== update_dict[col_field] ) {
        // ---  add field to updated_columns list
                                    updated_columns.push(col_field)
        // ---  update field in data_row
                                    data_dict[col_field] = update_dict[col_field];
        // -- when color fiels has changed: also add textfield to update_dict, to show green
                                    if (col_field === "content_hexcolor"){
                                        updated_columns.push("content_nl");
                                    } else if (col_field === "instruction_hexcolor"){
                                        updated_columns.push("instruction_nl");
                                    };
                                }};
                        };

        // ---  update field in tblRow
                        // note: when updated_columns is empty, then updated_columns is still true.
                        // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
                        if(updated_columns.length || field_error_list.length){
        console.log("updated_columns", updated_columns);
        console.log("field_error_list", field_error_list);

// --- get existing tblRow
                            let tblRow = document.getElementById(map_id);
                            if(tblRow){

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
                student_rows: {get: true},
                //studentsubject_rows: {get: true},
                grade_rows: {get: true},
                schemeitem_rows: {get: true}
            };
        DatalistDownload(datalist_request);

    };  // MSED_Response

//=========  get_datarows_from_selectedbtn  ================ PR2022-08-04
    function get_datarows_from_selectedbtn() {
        const data_rows = (selected_btn === "btn_orderlist") ? orderlist_rows :
                        (selected_btn === "btn_exam") ? envelopbundle_rows :
                        (selected_btn === "btn_bundle") ? envelopbundlelabel_rows :
                        (selected_btn === "btn_label") ? enveloplabel_rows :
                        (selected_btn === "btn_item") ? envelopitem_rows : [];
        return data_rows;
    };

//=========  get_tblName_from_selectedbtn  ================ PR2022-08-04
    function get_tblName_from_selectedbtn() {
        const tblName = (selected_btn === "btn_orderlist") ? "orderlist" :
                        (selected_btn === "btn_exam") ? "ete_exam" :
                        (selected_btn === "btn_bundle") ? "envelopbundlelabel" :
                        (selected_btn === "btn_label") ? "enveloplabel" :
                        (selected_btn === "btn_item") ? "envelopitem" : null;
        return tblName;
    };

})  // document.addEventListener('DOMContentLoaded', function()