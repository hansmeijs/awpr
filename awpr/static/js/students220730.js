// PR2020-09-29 added

// PR2021-07-23  declare variables outside function to make them global variables
//let setting_dict = {};
//let permit_dict = {};
//let loc = {};
//let urls = {};

// selected_btn is also used in t_MCOL_Open
//let selected_btn = "btn_student";
const selected = {
    student_dict: {},
    student_pk: null,
    item_count: 0
    };

let student_rows = [];
let school_rows = [];

const field_settings = {};

document.addEventListener('DOMContentLoaded', function() {
    "use strict";

// ---  check if user has permit to view this page. If not: el_loader does not exist PR2020-10-02
    const el_loader = document.getElementById("id_loader");
    const el_hdr_left = document.getElementById("id_header_left");
    const may_view_page = (!!el_loader);

    const cls_hide = "display_hide";
    const cls_hover = "tr_hover";
    const cls_visible_hide = "visibility_hide";
    const cls_selected = "tsa_tr_selected";

// ---  id of selected customer and selected order
    // declared as global: //let selected_btn = "btn_student";
    ////let setting_dict = {};
    ////let permit_dict = {};

    let mod_dict = {};
    let mod_MSTUD_dict = {};

    let mod_MSTUDSUBJ_dict = {}; // stores general info of selected candidate in MSTUDSUBJ PR2020-11-21
    //let mod_studsubj_dict = {};  // stores studsubj of selected candidate in MSTUDSUBJ
    //let mod_schemeitem_dict = {};   // stores available studsubj for selected candidate in MSTUDSUBJ
    let mod_studsubj_map = new Map();  // stores studsubj of selected candidate in MSTUDSUBJ
    let mod_schemeitem_map = new Map();

    let examyear_map = new Map();
    let school_map = new Map();
    // PR2020-12-26 These variable defintions are moved to import.js, so they can also be used in that file
    //let department_map = new Map();
    //let level_map = new Map();
    //let sector_map = new Map();
    //let selected = {student_pk: null,
    //                student_dict: {}};

    // PR2021-07-23 moved outside this function, to make it available in import.js
    // let student_rows = [];
    // //let loc = {};

    let subject_map = new Map();
    let studentsubject_map = new Map()
    let scheme_map = new Map()
    let schemeitem_map = new Map()

    //let filter_dict = {};

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    urls.url_user_modmsg_hide = get_attr_from_el(el_data, "data-url_user_modmsg_hide");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    urls.url_usersetting_upload = get_attr_from_el(el_data, "data-url_usersetting_upload");
    urls.url_student_upload = get_attr_from_el(el_data, "data-url_student_upload");
    urls.url_download_student_xlsx = get_attr_from_el(el_data, "data-url_download_student_xlsx");
    urls.url_studsubj_validate_scheme = get_attr_from_el(el_data, "data-url_studsubj_validate_scheme");

    //const url_studsubj_upload = get_attr_from_el(el_data, "data-url_studsubj_upload");
    // url_importdata_upload is stored in id_MIMP_data of modimport.html

    mod_MCOL_dict.columns.all = {
        idnumber: "ID_number", prefix: "Prefix", gender: "Gender",
        birthdate: "Birthdate", birthcountry: "Country_of_birth", birthcity: "Place_of_birth",
        lvlbase_id:  "Leerweg", sctbase_id: "Sector",classname: "Class",
        examnumber: "Examnumber", regnumber: "Regnumber", bis_exam: "Bis_exam"
    };

// --- get field_settings
    // declared as global: let field_settings = {};
    field_settings.student = {
        field_caption: ["", "ID_number", "Last_name", "First_name", "Prefix_twolines", "Gender", "Birthdate", "Country_of_birth", "Place_of_birth", "Leerweg", "Sector", "Class", "Examnumber_twolines", "Regnumber_twolines", "Bis_exam"],
        field_names: ["select", "idnumber", "lastname", "firstname", "prefix", "gender", "birthdate", "birthcountry", "birthcity", "lvlbase_id", "sctbase_id", "classname", "examnumber", "regnumber", "bis_exam"],
        filter_tags: ["select", "text", "text",  "text", "text", "text", "text", "text", "text", "text", "text", "text","text", "text", "toggle"],
        field_width:  ["020", "120", "220", "240", "090", "090", "120", "180", "180", "090", "090", "090", "090", "120","090"],
        field_align: ["c", "l", "l", "l", "l", "c", "l", "l", "l", "l", "l", "l","l", "l","c"]}

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
        const el_hdrbar_department = document.getElementById("id_hdrbar_department");
        if (el_hdrbar_department){
            el_hdrbar_department.addEventListener("click", function() {
                t_MSED_Open(loc, "department", department_map, setting_dict, permit_dict, MSED_Response)}, false );
        }
        const el_hdrbar_school = document.getElementById("id_hdrbar_school");
        if (el_hdrbar_school){
            el_hdrbar_school.addEventListener("click",
                function() {t_MSSSS_Open(loc, "school", school_rows, false, setting_dict, permit_dict, MSSSS_Response)}, false );
        }

// ---  SIDEBAR ------------------------------------
        const el_SBR_select_level = document.getElementById("id_SBR_select_level");
        if(el_SBR_select_level){
            el_SBR_select_level.addEventListener("change", function() {t_SBR_select_level_sector("level", el_SBR_select_level, FillTblRows)}, false)}
        const el_SBR_select_sector = document.getElementById("id_SBR_select_sector");
        if(el_SBR_select_sector){
            el_SBR_select_sector.addEventListener("change", function() {t_SBR_select_level_sector("sector", el_SBR_select_sector, FillTblRows)}, false)};
        //const el_SBR_select_class = document.getElementById("id_SBR_select_class");
        //if(el_SBR_select_class){
        //    el_SBR_select_class.addEventListener("click", function() {t_MSSSS_Open(loc, "class", classname_rows, true, setting_dict, permit_dict, MSSSS_Response)}, false)};
        const el_SBR_select_student = document.getElementById("id_SBR_select_student");
        if(el_SBR_select_student){
            el_SBR_select_student.addEventListener("click", function() {t_MSSSS_Open(loc, "student", student_rows, true, setting_dict, permit_dict, MSSSS_Response)}, false)};
        const el_SBR_select_showall = document.getElementById("id_SBR_select_showall");
        if(el_SBR_select_showall){
            el_SBR_select_showall.addEventListener("click", function() {t_SBR_show_all(FillTblRows)}, false);
            add_hover(el_SBR_select_showall);
        };
        const el_SBR_item_count = document.getElementById("id_SBR_item_count")


// ---  MODAL SIDEBAR FILTER ------------------------------------
        const el_SBR_filter = document.getElementById("id_SBR_filter")
        if(el_SBR_filter){
            el_SBR_filter.addEventListener("keyup", function() {MSTUD_InputKeyup(el_SBR_filter)}, false );
        }

// ---  MODAL SELECT COLUMNS ------------------------------------
        const el_MCOL_btn_save = document.getElementById("id_MCOL_btn_save")
        if(el_MCOL_btn_save){
            el_MCOL_btn_save.addEventListener("click", function() {
                t_MCOL_Save(urls.url_usersetting_upload, HandleBtnSelect)}, false )
        };

// ---  MODAL STUDENT
        const el_MSTUD_div_form_controls = document.getElementById("id_MSTUD_div_form_controls")
        if(el_MSTUD_div_form_controls){
            const form_elements = el_MSTUD_div_form_controls.querySelectorAll(".form-control")
            for (let i = 0, el; el = form_elements[i]; i++) {
                if(el.tagName === "INPUT"){
                    el.addEventListener("keyup", function() {MSTUD_InputKeyup(el)}, false )
                } else if(el.tagName === "SELECT"){
                    el.addEventListener("change", function() {MSTUD_InputSelect(el)}, false )
                } else if(el.tagName === "DIV"){
                    el.addEventListener("click", function() {MSTUD_InputToggle(el)}, false );
                };
            };
        };
        const el_MSTUD_abbrev = document.getElementById("id_MSTUD_abbrev");
        const el_MSTUD_name = document.getElementById("id_MSTUD_name");

        const el_MSTUD_bis_exam = document.getElementById("id_MSTUD_bis_exam");
        const el_MSTUD_iseveningstudent = document.getElementById("id_MSTUD_iseveningstudent");

        const el_MSTUD_tbody_select = document.getElementById("id_MSTUD_tblBody_department");
        const el_MSTUD_btn_delete = document.getElementById("id_MSTUD_btn_delete");
        //if(el_MSTUD_btn_delete){el_MSTUD_btn_delete.addEventListener("click", function() {MSTUD_Save("delete")}, false)}
        if(el_MSTUD_btn_delete){el_MSTUD_btn_delete.addEventListener("click", function() {ModConfirmOpen("delete")}, false)}

        // TODO add log
        const el_MSTUD_btn_log = document.getElementById("id_MSTUD_btn_log");
        const el_MSTUD_btn_save = document.getElementById("id_MSTUD_btn_save");
        if(el_MSTUD_btn_save){ el_MSTUD_btn_save.addEventListener("click", function() {MSTUD_Save("save")}, false)}

// ---  MODAL STUDENT SUBJECTS
        const el_MSTUDSUBJ_hdr = document.getElementById("id_MSTUDSUBJ_hdr")
        const el_MSTUDSUBJ_btn_add_selected = document.getElementById("id_MSTUDSUBJ_btn_add_selected")
        if(el_MSTUDSUBJ_btn_add_selected){
            el_MSTUDSUBJ_btn_add_selected.addEventListener("click", function() {MSTUDSUBJ_AddRemoveSubject("add")}, false);
        }

        const el_MSTUDSUBJ_btn_remove_selected = document.getElementById("id_MSTUDSUBJ_btn_remove_selected")
        if(el_MSTUDSUBJ_btn_remove_selected){
            el_MSTUDSUBJ_btn_remove_selected.addEventListener("click", function() {MSTUDSUBJ_AddRemoveSubject("remove")}, false);
        };
        const el_MSTUDSUBJ_btn_add_package = document.getElementById("id_MSTUDSUBJ_btn_add_package")
        if(el_MSTUDSUBJ_btn_add_package){
            el_MSTUDSUBJ_btn_add_package.addEventListener("click", function() {MSTUDSUBJ_AddPackage()}, false);
        };
        const el_MSTUDSUBJ_div_form_controls = document.getElementById("id_MSTUDSUBJ_div_form_controls");
        if(el_MSTUDSUBJ_div_form_controls){
            const el_input_controls = el_MSTUDSUBJ_div_form_controls.querySelectorAll(".awp_input_text, .awp_input_checkbox")
            if(el_input_controls){
                for (let i = 0, el; el = el_input_controls[i]; i++) {
                    const key_str = (el.classList.contains("awp_input_checkbox")) ? "change" : "keyup";
                    el.addEventListener(key_str, function() {MSTUDSUBJ_InputboxEdit(el)}, false)
                }
            };
        };
        const el_MSTUDSUBJ_btn_save = document.getElementById("id_MSTUDSUBJ_btn_save")
        if(el_MSTUDSUBJ_btn_save){
            el_MSTUDSUBJ_btn_save.addEventListener("click", function() {MSTUDSUBJ_Save()}, false);
        };
        const el_tblBody_studsubjects = document.getElementById("id_MSTUDSUBJ_tblBody_studsubjects");
        const el_tblBody_schemeitems = document.getElementById("id_MSTUDSUBJ_tblBody_schemeitems");

// ---  MODAL IMPORT ------------------------------------
// --- create EventListener for buttons in btn_container
    const el_MIMP_btn_container = document.getElementById("id_MIMP_btn_container");
    if(el_MIMP_btn_container){
        const btns = el_MIMP_btn_container.children;
        for (let i = 0, btn; btn = btns[i]; i++) {
            //PR2021-12-05 debug: data_btn as argument doesn't work, don't know why, use btn as argument instead
            // was: const data_btn = get_attr_from_el(btn, "data-btn")
            btn.addEventListener("click", function() {MIMP_btnSelectClicked(btn)}, false )
        }
    }
    const el_MIMP_filedialog = document.getElementById("id_MIMP_filedialog");
    if(el_MIMP_filedialog){
        el_MIMP_filedialog.addEventListener("change", function() {MIMP_HandleFiledialog(el_MIMP_filedialog, loc)}, false )
    };
    const el_MIMP_btn_filedialog = document.getElementById("id_MIMP_btn_filedialog");
    if (el_MIMP_filedialog && el_MIMP_btn_filedialog){
        el_MIMP_btn_filedialog.addEventListener("click", function() {MIMP_OpenFiledialog(el_MIMP_filedialog)}, false)};
    const el_MIMP_filename = document.getElementById("id_MIMP_filename");

    const el_worksheet_list = document.getElementById("id_MIMP_worksheetlist");
    if(el_worksheet_list){
        el_worksheet_list.addEventListener("change", MIMP_SelectWorksheet, false);
    };
    const el_MIMP_checkboxhasheader = document.getElementById("id_MIMP_hasheader");
    if(el_MIMP_checkboxhasheader){
        el_MIMP_checkboxhasheader.addEventListener("change", MIMP_CheckboxHasheaderChanged) //, false);
    };

   const el_MIMP_btn_prev = document.getElementById("id_MIMP_btn_prev");
    if(el_MIMP_btn_prev){
        el_MIMP_btn_prev.addEventListener("click", function() {MIMP_btnPrevNextClicked("prev")}, false )
    };
   const el_MIMP_btn_next = document.getElementById("id_MIMP_btn_next");
    if(el_MIMP_btn_next){
        el_MIMP_btn_next.addEventListener("click", function() {MIMP_btnPrevNextClicked("next")}, false )
    };
   const el_MIMP_btn_test = document.getElementById("id_MIMP_btn_test");
    if(el_MIMP_btn_test){
        el_MIMP_btn_test.addEventListener("click", function() {MIMP_Save("test", RefreshDataRowsAfterUpload)}, false )
    };
   const el_MIMP_btn_upload = document.getElementById("id_MIMP_btn_upload");
   if(el_MIMP_btn_upload){
        el_MIMP_btn_upload.addEventListener("click", function() {MIMP_Save("save", RefreshDataRowsAfterUpload)}, false )
    };

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

// ---  MOD MESSAGE ------------------------------------
        const el_mod_message_btn_hide = document.getElementById("id_mod_message_btn_hide");
        if(el_mod_message_btn_hide){
            el_mod_message_btn_hide.addEventListener("click", function() {ModMessageHide()});
        };

// ---  set selected menu button active
        const btn_clicked = document.getElementById("id_plg_page_student")

        //console.log("btn_clicked: ", btn_clicked)
        SetMenubuttonActive(document.getElementById("id_plg_page_student"));

    if(may_view_page){
        // period also returns emplhour_list
        const datalist_request = {
                setting: {page: "page_student"},
                schoolsetting: {setting_key: "import_student"},
                locale: {page: ["page_student", "upload"]},
                examyear_rows: {get: true},
                school_rows: {get: true},
                department_rows: {get: true},
                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},
                student_rows: {cur_dep_only: true}
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
        el_hdr_left.classList.add(cls_hide)

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

// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                el_hdr_left.classList.remove(cls_hide)

                let must_update_headerbar = false;
                let check_status = false;
                let isloaded_loc = false, isloaded_settings = false, isloaded_permits = false;

                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                    isloaded_loc = true;
                };

                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict
                    selected_btn = (setting_dict.sel_btn)
                    isloaded_settings = true;

        // ---  fill cols_hidden
                    if("cols_hidden" in setting_dict){
                        //  setting_dict.cols_hidden was dict with key 'all' or se_btn, changed to array PR2021-12-14
                        //  skip when setting_dict.cols_hidden is not an array,
                        // will be changed into an array when saving with t_MCOL_Save
                        b_copy_array_noduplicates(setting_dict.cols_hidden, mod_MCOL_dict.cols_hidden);
                    };
                    must_update_headerbar = true;
                };

                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    // get_permits must come before CreateSubmenu and FiLLTbl
                    b_get_permits_from_permitlist(permit_dict);
                    isloaded_permits = true;
                    must_update_headerbar = true;
                }
                if ("schoolsetting_dict" in response) {
                    i_UpdateSchoolsettingsImport(response.schoolsetting_dict)
                };
                // both 'loc' and 'setting_dict' are needed for CreateSubmenu
                if (isloaded_loc && isloaded_settings) {CreateSubmenu()};
                if(isloaded_settings || isloaded_permits){
                    b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);
                };
                if ("messages" in response) {
                    b_show_mod_message_dictlist(response.messages);
                }

                if ("examyear_rows" in response) { b_fill_datamap(examyear_map, response.examyear_rows)};
                if ("school_rows" in response)  {
                    school_rows =  response.school_rows;
                    b_fill_datamap(school_map, response.school_rows)};
                if ("department_rows" in response) { b_fill_datamap(department_map, response.department_rows)};

                if ("level_rows" in response)  {
                    b_fill_datamap(level_map, response.level_rows);
                    t_SBR_filloptions_level_sector("level", response.level_rows)

                };
                if ("sector_rows" in response) {
                    b_fill_datamap(sector_map, response.sector_rows);
                    t_SBR_filloptions_level_sector("sector", response.sector_rows);
                };

                if ("student_rows" in response) {
                    student_rows = response.student_rows;
                }

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
        //console.log("===  CreateSubmenu == ");
        //console.log("loc.Add_subject ", loc.Add_subject);
        //console.log("loc ", loc);

        let el_submenu = document.getElementById("id_submenu")
        if(permit_dict.permit_crud){
            AddSubmenuButton(el_submenu, loc.Add_candidate, function() {MSTUD_Open()});
            AddSubmenuButton(el_submenu, loc.Delete_candidate, function() {ModConfirmOpen("delete")});
        };
        if(permit_dict.requsr_role_system){
            AddSubmenuButton(el_submenu, loc.Validate_candidate_schemes, function() {ModConfirmOpen("validate_scheme")});
            AddSubmenuButton(el_submenu, loc.Correct_candidate_schemes, function() {ModConfirmOpen("correct_scheme")});
        };
        if(permit_dict.permit_crud){
            AddSubmenuButton(el_submenu, loc.Upload_candidates, function() {MIMP_Open(loc, "import_student")}, null, "id_submenu_import");
            AddSubmenuButton(el_submenu, loc.Download_candidate_data, null, [], "id_submenu_download_studentxlsx", urls.url_download_student_xlsx, true);  // true = download
        };

        AddSubmenuButton(el_submenu, loc.Hide_columns, function() {t_MCOL_Open("page_student")}, [], "id_submenu_columns")
        el_submenu.classList.remove(cls_hide);

    };//function CreateSubmenu

//###########################################################################
//=========  HandleBtnSelect  ================ PR2020-09-19  PR2020-11-14
    function HandleBtnSelect(data_btn, skip_upload) {
        //console.log( "===== HandleBtnSelect ========= ", data_btn);
        selected_btn = data_btn
        if(!selected_btn){selected_btn = "btn_student"}

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_student: {sel_btn: selected_btn}};
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);
        };

// ---  highlight selected button
        b_highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn)

// ---  show only the elements that are used in this tab
        b_show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

// ---  fill sidebar selecttable students
        //SBR_FillSelectTable();

// ---  fill datatable
        FillTblRows();

// --- update header text
        UpdateHeaderText();
    }  // HandleBtnSelect

//=========  HandleTblRowClicked  ================ PR2020-08-03
    function HandleTblRowClicked(tr_clicked) {
        //console.log("=== HandleTblRowClicked");
        //console.log( "tr_clicked: ", tr_clicked, typeof tr_clicked);

// ---  get selected.student_dict
        selected.student_pk = get_attr_from_el_int(tr_clicked, "data-pk");
        selected.student_dict = b_get_datadict_by_integer_from_datarows(student_rows, "id", selected.student_pk);
        //console.log( "selected.student_pk: ", selected.student_pk);
        //console.log( "selected.student_dict: ", selected.student_dict);

// --- get existing data_dict from data_rows
        const pk_int = get_attr_from_el_int(tr_clicked, "data-pk");
        const [index, found_dict, compare] = b_recursive_integer_lookup(student_rows, "id", pk_int);
        const data_dict = (!isEmpty(found_dict)) ? found_dict : null;
        selected.student_pk = (data_dict) ? data_dict.id : null


// ---  deselect all highlighted rows - also tblFoot , highlight selected row
        DeselectHighlightedRows(tr_clicked, cls_selected);
        tr_clicked.classList.add(cls_selected)

    }  // HandleTblRowClicked


//========= UpdateHeaderText  ================== PR2020-07-31
    function UpdateHeaderText(){
        //console.log(" --- UpdateHeaderText ---" )
        // TODO
        //let header_text = null;
        //if(selected_btn === "btn_user"){
        //   header_text = loc.User_list;
        //} else {
        //    header_text = loc.Permissions;
        //}
        //document.getElementById("id_hdr_text").innerText = header_text;
    }   //  UpdateHeaderText

//========= FillTblRows  ============== PR2021-06-16  PR2021-12-14
    function FillTblRows() {
        //console.log( "===== FillTblRows  === ");
        //console.log( "setting_dict", setting_dict);

        const tblName = "student";
        const field_setting = field_settings[tblName];
        const data_rows = student_rows;

// ---  get list of hidden columns
        const col_hidden = b_copy_array_to_new_noduplicates(mod_MCOL_dict.cols_hidden);
        // hide level when not level_req
        if(!setting_dict.sel_dep_level_req){col_hidden.push("lvlbase_id")};

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null;

// --- create table header
        CreateTblHeader(field_setting, col_hidden);

// --- loop through data_rows
        if(data_rows && data_rows.length){
            for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {

        // --- set SBR_filter
        // Note: filter of filterrow is done by Filter_TableRows
                let show_row = true;
                if (show_row && setting_dict.sel_lvlbase_pk){
                    show_row = (setting_dict.sel_lvlbase_pk === data_dict.lvlbase_id)
                }
                if (show_row && setting_dict.sel_sctbase_pk){
                    show_row = (setting_dict.sel_sctbase_pk === data_dict.sctbase_id)
                }
                if(show_row){
                    CreateTblRow(tblName, field_setting, data_dict, col_hidden);
                };
            };
        };
// --- filter tblRows
        Filter_TableRows();
    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-07-31 PR2021-06-15 PR2021-08-02
    function CreateTblHeader(field_setting, col_hidden) {
        //console.log("===  CreateTblHeader ===== ");
        //console.log("field_setting", field_setting);
        //console.log("col_hidden", col_hidden);

//--- get info from selected department_map
        let sct_caption = null, has_profiel = false,  lvl_req = false, sct_req = false;
        const dep_dict = get_mapdict_from_datamap_by_tblName_pk(department_map, "department", setting_dict.sel_department_pk);
        if(dep_dict){
            has_profiel = (!!dep_dict.has_profiel);
            lvl_req = (!!dep_dict.lvl_req);
            sct_req = (!!dep_dict.sct_req);
        }

        const column_count = field_setting.field_names.length;

// +++  insert header and filter row ++++++++++++++++++++++++++++++++
        let tblRow_header = tblHead_datatable.insertRow (-1);
        let tblRow_filter = tblHead_datatable.insertRow (-1);

    // --- loop through columns
        for (let j = 0; j < column_count; j++) {
            const field_name = field_setting.field_names[j];

    // --- skip column if in columns_hidden
            const is_hidden = col_hidden.includes(field_name);
            if (!is_hidden){

        // --- get field_caption from field_setting, display 'Profiel' in column sctbase_id if has_profiel
                const key = field_setting.field_caption[j];
                const field_caption = (field_name === "sctbase_id" && has_profiel) ? loc.Profiel : (loc[key]) ? loc[key] : key;
                const filter_tag = field_setting.filter_tags[j];
                const class_width = "tw_" + field_setting.field_width[j] ;
                const class_align = "ta_" + field_setting.field_align[j];

// ++++++++++ insert columns in header row +++++++++++++++
        // --- add th to tblRow_header
                let th_header = document.createElement("th");
        // --- add div to th, margin not working with th
                    const el_header = document.createElement("div");
        // --- add innerText to el_header
                    el_header.innerText = field_caption;
        // --- add width, text_align, right padding in examnumber
                    th_header.classList.add(class_width, class_align);
                    el_header.classList.add(class_width, class_align);
                    // if(field_name === "examnumber"){el_header.classList.add("pr-2")};

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

        // --- add EventListener to el_filter / th_filter
                if (filter_tag === "text") {
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
                // PR2021-05-30 debug. Google chrome not setting width without th_filter class_width
                th_filter.classList.add(class_width, class_align);
                // el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");
                th_filter.appendChild(el_filter)
                tblRow_filter.appendChild(th_filter);
            }  //  if (!columns_hidden[field_name])
        }  // for (let j = 0; j < column_count; j++)
    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09 PR2021-06-21 PR2021-12-14
    function CreateTblRow(tblName, field_setting, data_dict, col_hidden) {
        //console.log("=========  CreateTblRow =========", tblName);
        //console.log("col_hidden", col_hidden);

        const field_names = field_setting.field_names;
        //const field_tags = field_setting.field_tags;
        const field_tag = "div";
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;

// ---  lookup index where this row must be inserted
        const ob1 = (data_dict.lastname) ? data_dict.lastname : "";
        const ob2 = (data_dict.firstname) ? data_dict.firstname : "";
        // NIU:  const ob3 = (data_dict.firstname) ? data_dict.firstname : "";

        const row_index = b_recursive_tblRow_lookup(tblBody_datatable, setting_dict.user_lang, ob1, ob2);

// --- insert tblRow into tblBody at row_index
        const tblRow = tblBody_datatable.insertRow(row_index);
        if (data_dict.mapid) {tblRow.id = data_dict.mapid};

// --- add data attributes to tblRow
        tblRow.setAttribute("data-pk", data_dict.id);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);
        tblRow.setAttribute("data-ob2", ob2);
        // NIU: tblRow.setAttribute("data-ob3", ---);

// --- add EventListener to tblRow
        tblRow.addEventListener("click", function() {HandleTblRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
        for (let j = 0; j < column_count; j++) {
            const field_name = field_names[j];

    // --- skip columns if in columns_hidden
            const col_is_hidden = col_hidden.includes(field_name);
            if (!col_is_hidden){
                const class_width = "tw_" + field_width[j];
                const class_align = "ta_" + field_align[j];

    // --- insert td element,
                const td = tblRow.insertCell(-1);

    // --- create element with tag from field_tags
                const el = document.createElement(field_tag);

        // --- add data-field attribute
                el.setAttribute("data-field", field_name);

        // --- add  text_align
                el.classList.add(class_width, class_align);

        // --- append element
                td.appendChild(el);

    // --- add EventListener to td
                if (["examnumber", "regnumber", "lastname", "firstname", "prefix", "gender",
                            "birthdate", "birthcountry", "birthcity",
                "idnumber", "db_code", "lvlbase_id", "sctbase_id", "classname",
                            "fullname", "subj_code", "subj_name", "sjtp_abbrev"].includes(field_name)){
                    td.addEventListener("click", function() {MSTUD_Open(el)}, false)
                    td.classList.add("pointer_show");
                    add_hover(td);
                } else if (field_name === "bis_exam") {
                    if(permit_dict.permit_crud && permit_dict.requsr_same_school){
                        td.addEventListener("click", function() {UploadToggle(el)}, false)
                        td.classList.add("pointer_show");
                        add_hover(td);
                    };
                };


    // --- put value in field
               UpdateField(el, data_dict)
           }  // if (!columns_hidden[field_name])
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

//=========  UpdateField  ================ PR2020-08-16 PR2021-06-16
    function UpdateField(el_div, data_dict) {
        //console.log("=========  UpdateField =========");
        //console.log("data_dict", data_dict);

        if(el_div){
            const field_name = get_attr_from_el(el_div, "data-field");
            const fld_value = data_dict[field_name];

            if(field_name){
                let filter_value = null;
                if (field_name === "select") {
                    // TODO add select multiple users option PR2020-08-18
                } else if (field_name === "bis_exam") {
                    el_div.className = (data_dict.bis_exam) ? "tickmark_2_2" : "tickmark_0_0";
                    filter_value = (data_dict.bis_exam) ? "1" : "0";

                } else if (["lvlbase_id", "sctbase_id"].includes(field_name)){
                    // put hard return in el_div, otherwise green border doesnt show in update PR2021-06-16
                    let abbrev = null;
                    if (field_name === "lvlbase_id"){
                        abbrev = (data_dict.lvl_abbrev) ? data_dict.lvl_abbrev : null;
                    } else if (field_name === "sctbase_id"){
                        abbrev = (data_dict.sct_abbrev) ? data_dict.sct_abbrev : null;
                    }
                    el_div.innerText = (abbrev) ? abbrev : "\n";
                    filter_value = (abbrev) ? abbrev.toLowerCase() : null;

                } else if (field_name === "birthdate"){
                    // PR2022-03-09 debug: date_JS gives birthdate one day before birthdat, becasue of timezone
                    // data_dict.birthdate 2004-05-30 becomes date_JS = Sat May 29 2004 20:00:00 GMT-0400 (Venezuela Time)
                    // use format_date_from_dateISO instead
                    // was:
                    // const date_JS = parse_dateJS_from_dateISO(data_dict.birthdate);
                    // const date_formatted = format_dateJS_vanilla (loc, date_JS, true, false, false, false);

                    const date_formatted = format_date_from_dateISO(loc, data_dict.birthdate);

                    el_div.innerText = (date_formatted) ? date_formatted : "\n";
                    filter_value = date_formatted;

                } else if (["examnumber", "regnumber", "lastname", "firstname", "prefix", "gender",
                             "birthcountry", "birthcity",
                            "idnumber", "db_code", "classname",
                            "fullname", "subj_code", "subj_name", "sjtp_abbrev"].includes(field_name)){
                    // put hard return in el_div, otherwise green border doesnt show in update PR2021-06-16
                    el_div.innerText = (fld_value) ? fld_value : "\n";
                    filter_value = (fld_value) ? fld_value.toLowerCase() : null;
                }
    // ---  add attribute filter_value
                add_or_remove_attr (el_div, "data-filter", !!filter_value, filter_value);
            }  // if(field_name)
        }  // if(el_div)
    };  // UpdateField


// +++++++++++++++++ UPLOAD CHANGES +++++++++++++++++ PR2020-08-03

//========= UploadToggle  ============= PR2022-03-05

    function UploadToggle(el_input) {
        console.log( " ==== UploadToggle ====");
        console.log( "el_input", el_input);
        // only called by table field bis_exam
        if (permit_dict.permit_crud && permit_dict.requsr_same_school){

            const tblRow = t_get_tablerow_selected(el_input);
            const fldName = get_attr_from_el(el_input, "data-field");
            const pk_int = get_attr_from_el_int(tblRow, "data-pk");

// --- get existing data_dict from data_rows
            const [index, found_dict, compare] = b_recursive_integer_lookup(student_rows, "id", pk_int);
            const data_dict = (!isEmpty(found_dict)) ? found_dict : null;
            if (data_dict){
    console.log( "fldName", fldName);
    console.log( "data_dict", data_dict);
                const old_value = data_dict.bis_exam;
            console.log( "old_value", old_value);

                const new_value = (!old_value) ? true : false;
            console.log( "new_value", new_value);
                if(new_value){
         // ---  change icon, before uploading
                    // don't, because of validation on server side
                    add_or_remove_class(el_input, "tickmark_1_2", new_value, "tickmark_0_0");

        // ---  upload changes
                    const upload_dict = {
                        student_pk: data_dict.id,
                    };
                    upload_dict[fldName] = new_value;
            console.log( "upload_dict", upload_dict);
                    UploadChanges(upload_dict, urls.url_student_upload);
                } else {
        // open mod confirm when deleting exemption, reex, reex3
                    ModConfirmOpen(fldName, el_input);
                };
            };
        }; //   if(permit_dict.permit_approve_subject)
    };  // UploadToggle



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
                        RefreshDataRows(tblName, response.updated_student_rows, student_rows, true)  // true = update
                    };

                    if("messages" in response){
                        b_show_mod_message_dictlist(response.messages);
                    }
                    if ("validate_scheme_response" in response) {
                        ValidateScheme_Response(response.validate_scheme_response)
                    }
                    $("#id_mod_student").modal("hide");

                },  // success: function (response) {
                error: function (xhr, msg) {
                    // ---  hide loader
                    el_loader.classList.add(cls_visible_hide)
                    console.log(msg + '\n' + xhr.responseText);
                }  // error: function (xhr, msg) {
            });  // $.ajax({
        }  //  if(!!row_upload)
    };  // UploadChanges

// +++++++++++++++++ UPDATE +++++++++++++++++++++++++++++++++++++++++++

//###########################################################################
// +++++++++++++++++ REFRESH DATA ROWS ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataRowsAfterUpload  ================ PR2021-07-20
function RefreshDataRowsAfterUpload(response) {
    //console.log(" --- RefreshDataRowsAfterUpload  ---");
    //console.log("response:", response);
    const is_test = (!!response && !!response.is_test) ;
    if(!is_test && response && "updated_student_rows" in response) {
        RefreshDataRows("student", response.updated_student_rows, student_rows, true)  // true = update
    }

}  // RefreshDataRowsAfterUpload

//=========  RefreshDataRows  ================ PR2020-08-16 PR2021-06-16
    function RefreshDataRows(tblName, update_rows, data_rows, is_update) {
        //console.log(" --- RefreshDataRows  ---");
        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length

        if (update_rows && update_rows.length ) {
            const field_setting = field_settings[tblName];
            for (let i = 0, update_dict; update_dict = update_rows[i]; i++) {
                RefreshDatarowItem(tblName, field_setting, update_dict, data_rows);
            }
        } else if (!is_update) {
            // empty the data_rows when update_rows is empty PR2021-01-13 debug forgot to empty data_rows
            // PR2021-03-13 debug. Don't empty de data_rows when is update. Returns [] when no changes made
           data_rows = [];
        }
    }  //  RefreshDataRows

//=========  RefreshDatarowItem  ================ PR2020-08-16 PR2020-09-30 PR2021-06-16
    function RefreshDatarowItem(tblName, field_setting, update_dict, data_rows) {
        console.log(" --- RefreshDatarowItem  ---");
        //console.log("tblName", tblName);
        console.log("update_dict", update_dict);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);

// ---  get list of hidden columns
            const col_hidden = b_copy_array_to_new_noduplicates(mod_MCOL_dict.cols_hidden);

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

    // ---  insert new item at end
                data_rows.push(update_dict)

    // ---  create row in table., insert in alphabetical order
                const new_tblRow = CreateTblRow(tblName, field_setting, update_dict, col_hidden)

                if(new_tblRow){
    // --- add1 to item_count
                    selected.item_count += 1;
    // ---  show total in sidebar
                    t_set_sbr_itemcount_txt(loc, selected.item_count, loc.Candidate, loc.Candidates, setting_dict.user_lang);

    // ---  scrollIntoView,
                    new_tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' })

    // ---  make new row green for 2 seconds,
                    ShowOkElement(new_tblRow);
                }
            } else {

// --- get existing data_dict from data_rows
                const pk_int = (update_dict && update_dict.id) ? update_dict.id : null;
                const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", pk_int);
                const data_dict = (!isEmpty(found_dict)) ? found_dict : null;
                const datarow_index = index;
        console.log("pk_int", pk_int);
        console.log("data_dict", data_dict);

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
                            tblRow_tobe_deleted.parentNode.removeChild(tblRow_tobe_deleted);
                        };
                    }

    // --- subtract 1 from item_count
                    selected.item_count -= 1;
    // ---  show total in sidebar
                    t_set_sbr_itemcount_txt(loc, selected.item_count, loc.Candidate, loc.Candidates, setting_dict.user_lang);
                } else {

// +++++++++++ updated row +++++++++++
    // ---  check which fields are updated, add to list 'updated_columns'
                    if(!isEmpty(data_dict) && field_names){

        //console.log("data_dict", data_dict);
                        let updated_columns = [];
                        // skip first column (is margin)
                        for (let i = 1, col_field, old_value, new_value; col_field = field_names[i]; i++) {
                            if (col_field in data_dict && col_field in update_dict){
                                if (data_dict[col_field] !== update_dict[col_field] ) {
        // ---  add field to updated_columns list
                                    updated_columns.push(col_field)
                                }};
                        };
        //console.log("updated_columns", updated_columns);

// ---  update fields in data_row
                        for (const [key, new_value] of Object.entries(update_dict)) {
                            if (key in data_dict){
                                if (new_value !== data_dict[key]) {
                                    data_dict[key] = new_value
                        }}};
        //console.log("data_dict", data_dict);

        // ---  update field in tblRow
                        // note: when updated_columns is empty, then updated_columns is still true.
                        // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
                        if(updated_columns.length){

// --- get existing tblRow
                            let tblRow = document.getElementById(map_id);
                            if(tblRow){
                                // to make it perfect: move row when first or last name have changed
                                if (updated_columns.includes("lastname") || updated_columns.includes("firstname")){
                                //--- delete current tblRow
                                    tblRow.parentNode.removeChild(tblRow);
                                //--- insert row new at new position
                                    tblRow = CreateTblRow(tblName, field_setting, update_dict, col_hidden)
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

                // make field green when field name is in updated_columns
                                        if(updated_columns.includes(el_fldName)){
                                            ShowOkElement(el);
                                        };
                                    };
                                };  //  for (let i = 1, el_fldName
                            };  // if(tblRow)
                        }; // if(updated_columns.length)
                    };  //  if(!isEmpty(data_dict) && field_names){
                };  // if(is_deleted)
            };  // if(is_created)
        //console.log("student_rows", student_rows);
        };  // if(!isEmpty(update_dict))
    };  // RefreshDatarowItem

// +++++++++ MOD STUDENT ++++++++++++++++ PR2020-09-30 PR2021-12-17
// --- also used for level, sector,
    function MSTUD_Open(el_input){
        console.log(" -----  MSTUD_Open   ----")
        console.log("permit_dict.permit_crud", permit_dict.permit_crud)
        console.log("el_input", el_input)

        mod_MSTUD_dict = {};

        if (permit_dict.permit_crud){
            const focus_fldName = get_attr_from_el(el_input, "data-field", "lastname");

            // el_input is undefined when called by submenu btn 'Add new'
            const is_addnew = (!el_input);

            const tblName = "student";
            if(is_addnew){
                mod_MSTUD_dict = {is_addnew: is_addnew,
                    db_code: setting_dict.sel_depbase_code}
            } else {
                const tblRow = t_get_tablerow_selected(el_input);
// --- get existing data_dict from data_rows
                const pk_int = get_attr_from_el_int(tblRow, "data-pk");
                const [index, found_dict, compare] = b_recursive_integer_lookup(student_rows, "id", pk_int);
                mod_MSTUD_dict = (!isEmpty(found_dict)) ? found_dict : null;
            }

        console.log("mod_MSTUD_dict", mod_MSTUD_dict)
    // ---  fill level and sector options, set select team in selectbox
            const selected_pk = null;
            const department_pk = (is_addnew) ? setting_dict.sel_department_pk : mod_MSTUD_dict.dep_id;
            const dep_dict = get_mapdict_from_datamap_by_tblName_pk(department_map, "department", department_pk);
            const depbase_pk = dep_dict.base_id;
            const lvl_req = (dep_dict.lvl_req) ? dep_dict.lvl_req : false;
            const sct_req = (dep_dict.sct_req) ? dep_dict.sct_req : false;

            //console.log("dep_dict", dep_dict)
            //console.log("sct_req", sct_req)
            const sct_caption = (dep_dict.has_profiel) ? loc.Profiel : loc.Sector;

            document.getElementById("id_MSTUD_level_label").innerText = loc.Leerweg + ':';
            document.getElementById("id_MSTUD_sector_label").innerText = sct_caption + ':';
            document.getElementById("id_MSTUD_level_select").innerHTML = t_FillOptionLevelSectorFromMap("level", "base_id", level_map, depbase_pk, selected_pk)
            document.getElementById("id_MSTUD_sector_select").innerHTML = t_FillOptionLevelSectorFromMap("sector", "base_id", sector_map, depbase_pk, selected_pk)

            const el_MSTUD_level_div = document.getElementById("id_MSTUD_level_div")
            add_or_remove_class(el_MSTUD_level_div, cls_hide, !lvl_req)
            add_or_remove_class(el_MSTUD_level_div, "flex_2", !sct_req, "flex_1")

            const el_MSTUD_sector_div = document.getElementById("id_MSTUD_sector_div")
            add_or_remove_class(el_MSTUD_sector_div, cls_hide, !sct_req)
            add_or_remove_class(el_MSTUD_sector_div, "flex_2", !lvl_req, "flex_1")

// show fields isdayeve student only when school is both dayschool and eveningschool
            const show_el_eveningstudent = (setting_dict.sel_school_isdayschool && setting_dict.sel_school_iseveningschool);
            add_or_remove_class(el_MSTUD_iseveningstudent.parentNode, cls_hide, !show_el_eveningstudent )

    // ---  remove value from el_mod_employee_input, set focus to selected field
            MSTUD_SetElements(focus_fldName);

            if (!is_addnew){
                //el_MSTUD_abbrev.value = (mod_MSTUD_dict.abbrev) ? mod_MSTUD_dict.abbrev : null;
                //el_MSTUD_name.value = (mod_MSTUD_dict.name) ? mod_MSTUD_dict.name : null;

                const modified_dateJS = parse_dateJS_from_dateISO(mod_MSTUD_dict.modifiedat);
                const modified_date_formatted = format_datetime_from_datetimeJS(loc, modified_dateJS)
                const modified_by = (mod_MSTUD_dict.modby_username) ? mod_MSTUD_dict.modby_username : "-";
                const display_txt = loc.Last_modified_on + modified_date_formatted + loc.by + modified_by;
                document.getElementById("id_MSTUD_msg_modified").innerText = display_txt;
            }

    // ---  disable btn submit, hide delete btn when is_addnew
        //console.log( "el_MSTUD_btn_delete: ", el_MSTUD_btn_delete);
        //console.log( "is_addnew: ", is_addnew);
            add_or_remove_class(el_MSTUD_btn_delete, cls_hide, is_addnew )
            //const disable_btn_save = (!el_MSTUD_abbrev.value || !el_MSTUD_name.value  )
            //el_MSTUD_btn_save.disabled = disable_btn_save;

            MSTUD_validate_and_disable();

    // ---  show modal
            $("#id_mod_student").modal({backdrop: true});
        }
    };  // MSTUD_Open

//=========  MSTUD_Save  ================  PR2020-10-01
    function MSTUD_Save(crud_mode) {
        console.log(" -----  MSTUD_save  ----", crud_mode);
        console.log( "mod_MSTUD_dict: ", mod_MSTUD_dict);

        if (permit_dict.permit_crud){
            const is_create = (mod_MSTUD_dict.is_addnew);
            const is_delete = (crud_mode === "delete");
            const upload_mode = (is_create) ? "create" : (is_delete) ? "delete" : "update"

            let upload_dict = {table: 'student', mode: upload_mode}
            if(mod_MSTUD_dict.id){upload_dict.student_pk = mod_MSTUD_dict.id};
            if(mod_MSTUD_dict.mapid){upload_dict.mapid = mod_MSTUD_dict.mapid};

    // ---  put changed values of input elements in upload_dict
            let new_level_pk = null, new_sector_pk = null, level_or_sector_has_changed = false;
            //let form_elements = document.getElementById("id_MSTUDSUBJ_div_form_controls").querySelectorAll(".awp_input_text, .awp_input_select")
            let el_MSTUD_div_form_controls = document.getElementById("id_MSTUD_div_form_controls")
            let form_elements = el_MSTUD_div_form_controls.getElementsByClassName("form-control")
            for (let i = 0, el_input; el_input = form_elements[i]; i++) {
                const fldName = get_attr_from_el(el_input, "data-field");
                let new_value = null, old_value = null;

                if(["lvlbase_id", "sctbase_id"].includes(fldName)){
                    new_value = (el_input.value && Number(el_input.value)) ? Number(el_input.value) : null;
                    old_value = (mod_MSTUD_dict[fldName] && Number(mod_MSTUD_dict[fldName])) ? Number(mod_MSTUD_dict[fldName]) : null;
                } else if(["bis_exam", "partial_exam", "iseveningstudent"].includes(fldName)){
                    // mod_MSTUD_dict[fldName] contains old value, a boolean
                    // el.attribute 'data-value' contains new value, a string "1" or "0"

                    const data_value = get_attr_from_el(el_input, "data-value")
                    new_value = (data_value === "1");
                    old_value = !!mod_MSTUD_dict[fldName];

    console.log( ".....fldName: ", fldName);
    console.log( ".... mod_MSTUD_dict[fldName]", mod_MSTUD_dict[fldName]);
    console.log( ".....old_value: ", old_value, typeof old_value);
    console.log( ".....data_value: ", data_value);
    console.log( ".....new_value: ", new_value, typeof new_value);
                } else {
                    new_value = (el_input.value) ? el_input.value : null;
                    old_value = (mod_MSTUD_dict[fldName]) ? mod_MSTUD_dict[fldName] : null;
                }
                if (new_value !== old_value) {
                    const field = (fldName === "lvlbase_id") ? "level" :
                                  (fldName === "sctbase_id") ? "sector" : fldName;
                    upload_dict[field] = new_value;
    console.log( ".....upload_dict[field]: ", upload_dict[field], typeof upload_dict[field]);
                    if(fldName === "lvlbase_id"){
                        new_level_pk = new_value;
                        level_or_sector_has_changed = true;
                    } else if(fldName === "sctbase_id"){
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

    //console.log( "upload_dict.student_pk: ", upload_dict.student_pk);
    //console.log( "level_or_sector_has_changed: ", level_or_sector_has_changed);
    //console.log( "new_level_pk: ", new_level_pk);
    //console.log( "new_sector_pk: ", new_sector_pk);
    // ---  check if schemeitems must be changed when level or sector changes
            if (upload_dict.student_pk){
                    // TODO move to server
                //if (level_or_sector_has_changed){
                   // check_new_scheme(upload_dict.student_pk, new_level_pk, new_sector_pk)
                //}
            }
    //console.log( "upload_dict: ", upload_dict);
            // TODO add loader
            //document.getElementById("id_MSTUD_loader").classList.remove(cls_visible_hide)
            // modal is closed by data-dismiss="modal"
            UploadChanges(upload_dict, urls.url_student_upload);
        };

    // ---  hide modal
            $("#id_mod_student").modal("hide");
    }  // MSTUD_Save

//========= MSTUD_get_selected_depbases  ============= PR2020-10-07
    function MSTUD_get_selected_depbases(){
        //console.log( "  ---  MSTUD_get_selected_depbases  --- ")
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

//========= MSTUD_InputSelect  ============= PR2020-12-11
    function MSTUD_InputSelect(el_input){
        //console.log( "===== MSTUD_InputSelect  ========= ");
        MSTUD_validate_and_disable();
    }; // MSTUD_InputSelect

//========= MSTUD_InputToggle  ============= PR2021-06-15 PR2022-04-11
    function MSTUD_InputToggle(el_input){
        console.log( "===== MSTUD_InputToggle  ========= ");
        const data_field = get_attr_from_el(el_input, "data-field")
        const data_value = get_attr_from_el(el_input, "data-value")
        const new_data_value = (data_value === "1") ? "0" : "1";
    // note: don't put new value in mod_MSTUD_dict - it contains the old value and must be unchanged

        let show_warning = false;
        // show warning that exemption grades will be deleted:
        // - when new_value = false
        // - only when old value of bis_exam OR evelex student is True
        // - and new value of of bis_exam AND evelex student is False
        if (new_data_value !== "1"){
            if (mod_MSTUD_dict.bis_exam || mod_MSTUD_dict.iseveningstudent || mod_MSTUD_dict.islexstudent){
                if(["bis_exam", "iseveningstudent"].includes(data_field)){
                    // show warning only when other element is also false
                    const other_el = (data_field === "bis_exam") ? el_MSTUD_iseveningstudent : el_MSTUD_bis_exam
                    show_warning = (get_attr_from_el(other_el, "data-value") !== "1");
                };
            };
        };

        // open mod confirm when deleting exemption, reex, reex3
        if (show_warning){
            ModConfirmOpen("MSTUD_" + data_field);
        } else {
            // data-value is attached to parentNode
            el_input.setAttribute("data-value", new_data_value);
            const el_img = el_input.children[0];
            add_or_remove_class(el_img, "tickmark_2_2", (new_data_value === "1"), "tickmark_1_1")

            MSTUD_SetLabelPartialAdditionalExam();
        };
    }; // MSTUD_InputToggle

//=========  MSTUD_validate_and_disable  ================  PR2020-10-01
    function MSTUD_validate_and_disable() {
        //console.log(" -----  MSTUD_validate_and_disable   ----")
        let disable_save_btn = false;
// ---  loop through input fields on MSTUD_Open
        let form_elements = el_MSTUD_div_form_controls.querySelectorAll(".awp_input_text")
        for (let i = 0, el_input; el_input = form_elements[i]; i++) {
            const fldName = get_attr_from_el(el_input, "data-field");
            const msg_err = MSTUD_validate_field(el_input, fldName);
// ---  show / hide error message NOT IN USE
            const el_msg = document.getElementById("id_MSTUD_msg_" + fldName);
            if(el_msg){
                el_msg.innerText = msg_err;
                disable_save_btn = true;
                add_or_remove_class(el_msg, cls_hide, !msg_err)
            };
        };
// ---  disable save button on error
        el_MSTUD_btn_save.disabled = disable_save_btn;
    };  // MSTUD_validate_and_disable

//=========  MSTUD_validate_field  ================  PR2020-10-01
    function MSTUD_validate_field(el_input, fldName) {
        //console.log(" -----  MSTUD_validate_field   ----")
        let msg_err = null;
        if (el_input){
            const value = el_input.value;
            if(["sequence"].includes(fldName)){
                const arr = b_get_number_from_input(loc, fldName, el_input.value);
                msg_err = arr[1];
            } else {
                 const caption = (fldName === "abbrev") ? loc.Abbreviation :
                                (fldName === "name") ? loc.Name  : loc.This_field;
                if (["abbrev", "name"].includes(fldName) && !value) {
                    msg_err = caption + loc.cannot_be_blank;
                } else if (["abbrev"].includes(fldName) && value.length > 10) {
                    msg_err = caption + loc.is_too_long_MAX10;
                } else if (["name"].includes(fldName) &&
                    value.length > 50) {
                        msg_err = caption + loc.is_too_long_MAX50;
                } else if (["abbrev", "name"].includes(fldName)) {
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
                            //console.log(" =====  validate_duplicates_in_department =====")

                            // check if they have at least one department in common
                            let depbase_in_common = false;
                            const selected_depbases = MSTUD_get_selected_depbases();
                            const lookup_departments = map_dict.depbases;
                            //console.log("selected_depbases", selected_depbases)
                            //console.log("lookup_departments", lookup_departments)
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
    function MSTUD_SetElements(focus_field){
        console.log( "===== MSTUD_SetElements  ========= ");
        console.log( "mod_MSTUD_dict", mod_MSTUD_dict);
        //console.log( "focus_field", focus_field);
// --- loop through input elements
        let form_elements = el_MSTUD_div_form_controls.querySelectorAll(".form-control")
        for (let i = 0, el, fldName, fldValue; el = form_elements[i]; i++) {
            fldName = get_attr_from_el(el, "data-field");
            fldValue = (mod_MSTUD_dict[fldName]) ? mod_MSTUD_dict[fldName] : null;

            if(["bis_exam", "partial_exam", "iseveningstudent"].includes(fldName)){
                el.setAttribute("data-value", (fldValue) ? "1" : "0");
                const el_img = el.children[0];
                add_or_remove_class(el_img, "tickmark_2_2", !!fldValue, "tickmark_1_1")
            } else {
                el.value = fldValue;
            }
            if(focus_field ){
                if( (fldName === focus_field) ||
                    (fldName === "lvl_id" && focus_field === "lvlbase_id") ||
                    (fldName === "sct_id" && focus_field === "sctbase_id")){
                    set_focus_on_el_with_timeout(el, 150);
                };
            }
        }

        let full_name = (mod_MSTUD_dict.fullname) ? mod_MSTUD_dict.lastname : "";
        document.getElementById("id_MSTUD_hdr").innerText = (mod_MSTUD_dict.fullname) ? mod_MSTUD_dict.fullname : loc.Add_candidate;

// set label partial / additional exam
        MSTUD_SetLabelPartialAdditionalExam()

    }  // MSTUD_SetElements


//========= MSTUD_SetLabelPartialAdditionalExam  ============= PR2021-12-17
    function MSTUD_SetLabelPartialAdditionalExam(){
// set label partial / additional exam
        // is partial exam if:
        //  - is lex school
        //  - is evening schol and not a dayschool
        //  - is day-eveningschool and student iseveningstudent
        const is_partial_exam = ( (setting_dict.sel_school_islexschool) ||
                        (setting_dict.sel_school_iseveningschool && !setting_dict.sel_school_isdayschool ) ||
                        (setting_dict.sel_school_iseveningschool && mod_MSTUD_dict.iseveningstudent) );
        const el_MSTUD_partaddexam_label = document.getElementById("id_MSTUD_partial_exam_label");
        el_MSTUD_partaddexam_label.innerText = ((is_partial_exam) ? loc.Partial_exam : loc.Additional_exam) + ":";

    };  // MSTUD_SetLabelPartialAdditionalExam

//========= MSTUD_SetMsgElements  ============= PR2020-08-02
    function MSTUD_SetMsgElements(response){
        //console.log( "===== MSTUD_SetMsgElements  ========= ");

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
// +++++++++ END MOD STUDENT +++++++++++++++++++++++++++++++++++++++++

// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++
//=========  ModConfirmOpen  ================ PR2020-08-03 PR2021-06-15 PR2021-07-23 PR2022-04-11
    function ModConfirmOpen(mode, el_input) {
        console.log(" -----  ModConfirmOpen   ----")
        // called by menubtn Delete_candidate and mod MSTUD btn delete and MSTUD_InputToggle
        // values of mode are : "delete", "validate_scheme", "correct_scheme",
        //  in UploadToggle:  fldName, in MSTUD_InputToggle: "MSTUD_" + data_field)
        //  el_input has only value when called by UploadToggle

        console.log("mode", mode)
        console.log("el_input", el_input)
        const tblName = "student";
        let show_modal = false;

// ---  get selected.student_dict
        // selected.student_pk got value in HandleTblRowClicked
        if(el_input){
            const tblRow = t_get_tablerow_selected(el_input);
            selected.student_pk = get_attr_from_el_int(tblRow, "data-pk");
        };

// --- get existing data_dict from data_rows
        const [index, found_dict, compare] = b_recursive_integer_lookup(student_rows, "id", selected.student_pk);
        const has_data_dict = (!isEmpty(found_dict));
        const data_dict = (has_data_dict) ? found_dict : {};
        selected.student_pk = (has_data_dict) ? data_dict.id : null

    console.log("data_dict", data_dict)

        const may_edit = (permit_dict.permit_crud && permit_dict.requsr_same_school);

// ---  create mod_dict
        mod_dict = {mode: mode};

        if (el_input) { mod_dict.el_input = el_input};

        if (["delete", "bis_exam", "MSTUD_bis_exam", "MSTUD_iseveningstudent"].includes(mode)){
            show_modal = may_edit;
            if(has_data_dict ){
                mod_dict.student_pk = data_dict.id;
                mod_dict.mapid = data_dict.mapid;
                mod_dict.fullname = data_dict.fullname;
            }
        } else if (["validate_scheme", "correct_scheme"].includes(mode)){
            show_modal = permit_dict.requsr_role_system;
        };

// ---  put text in modal for
        let header_text = "";

        let msg01_txt = null, msg02_txt = null, msg03_txt = null;
        let hide_save_btn = false;

        if (["delete", "bis_exam", "MSTUD_bis_exam", "MSTUD_iseveningstudent"].includes(mode)){
            header_text = (mode === "delete") ? loc.Delete_candidate :
                           (mode === "bis_exam") ? loc.Remove_bis_exam : null;
            if(!has_data_dict){
                msg01_txt = loc.Please_select_candidate_first;
                hide_save_btn = true;
            } else {
                const full_name = (has_data_dict && data_dict.fullname) ? data_dict.fullname  : "---";
                if (mode === "bis_exam") {
                    msg01_txt = loc.The_bis_exam + loc._of_ + " '" + full_name + "'" + loc.will_be_removed
                    // PR2022-04-11 Richard westerink ATC: not when also evening / lex student

                    if (has_data_dict && data_dict.bis_exam && !data_dict.iseveningstudent && !data_dict.islexstudent){
                        msg02_txt = loc.Possible_exemptions_willbe_deleted;
                    };
                    msg03_txt = loc.Do_you_want_to_continue;
                } else if (["MSTUD_bis_exam", "MSTUD_iseveningstudent"].includes(mode)){
                    msg02_txt = loc.Possible_exemptions_willbe_deleted;
                    msg03_txt = loc.Do_you_want_to_continue;
                } else {
                    msg01_txt = loc.Candidate + " '" + full_name + "'" + loc.will_be_deleted
                    msg02_txt = loc.Do_you_want_to_continue;
                };
            };
        } else if(mode === "validate_scheme"){
            header_text = loc.Validate_candidate_schemes;
            msg01_txt = loc.Schemes_of_candidates_willbe_validated;
            msg02_txt = loc.Do_you_want_to_continue;

        } else if(mode === "correct_scheme"){
            header_text = loc.Correct_candidate_schemes;
            msg01_txt = loc.Schemes_of_candidates_willbe_corrected;
            msg02_txt = loc.Do_you_want_to_continue;
        };

        el_confirm_header.innerText = header_text;
        el_confirm_loader.classList.add(cls_visible_hide);
        el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");

        //el_confirm_msg01.innerText = msg01_txt;
        //el_confirm_msg02.innerText = msg02_txt;
        //el_confirm_msg03.innerText = msg03_txt;

        let msg_html = "";
        if (msg01_txt) {msg_html += "<p>" + msg01_txt + "</p>"};
        if (msg02_txt) {msg_html += "<p>" + msg02_txt + "</p>"};
        if (msg03_txt) {msg_html += "<p>" + msg03_txt + "</p>"};
        el_confirm_msg_container.innerHTML = msg_html

        const caption_save = (mode === "delete") ? loc.Yes_delete : (mode === "bis_exam") ? loc.Yes_remove : loc.OK;
        el_confirm_btn_save.innerText = caption_save;
        add_or_remove_class (el_confirm_btn_save, cls_hide, hide_save_btn);

        //add_or_remove_class (el_confirm_btn_save, "btn-primary", (mode !== "delete"));
        add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", (mode === "delete"), "btn-primary");

        el_confirm_btn_cancel.innerText = (has_data_dict) ? loc.No_cancel : loc.Close;

// set focus to cancel button
        set_focus_on_el_with_timeout(el_confirm_btn_cancel, 150);

// show modal
        if (show_modal) {
            $("#id_mod_confirm").modal({backdrop: true});
        };
    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2019-06-23
    function ModConfirmSave() {
        console.log(" --- ModConfirmSave --- ");
        console.log("mod_dict: ", mod_dict);

        const may_edit = (permit_dict.permit_crud && permit_dict.requsr_same_school);
// ---  Upload Changes
        let url_str = null;
        const upload_dict = { table: "student", mode: mod_dict.mode}
        if(mod_dict.mode === "delete"){
            if(may_edit){
// ---  when delete: make tblRow red, before uploading
                let tblRow = document.getElementById(mod_dict.mapid);
                ShowClassWithTimeout(tblRow, "tsa_tr_error");
                url_str = urls.url_student_upload;
                upload_dict.student_pk = mod_dict.student_pk;
                upload_dict.mapid = mod_dict.mapid;
                UploadChanges(upload_dict, url_str);
            }

        } else if(mod_dict.mode === "bis_exam"){
            if(may_edit){
// ---  when remove bis_exam: delete tickmark, before uploading
                // TODO must restore old value. Till then don't upate field before uploading
                //if (mod_dict.el_input) {
                //    mod_dict.el_input.className = "tickmark_0_0";
                //};

        // ---  upload changes
                const upload_dict = {
                    student_pk: mod_dict.student_pk,
                    mapid: mod_dict.mapid,
                    bis_exam: false
                };
                UploadChanges(upload_dict, urls.url_student_upload);
            }

        } else if (["MSTUD_bis_exam", "MSTUD_iseveningstudent"].includes(mod_dict.mode)){
            const el_input = (mod_dict.mode === "MSTUD_bis_exam") ? el_MSTUD_bis_exam : el_MSTUD_iseveningstudent;
            el_input.setAttribute("data-value", false);
            add_or_remove_class(el_input.children[0], "tickmark_2_2", false, "tickmark_1_1")

        } else if (["validate_scheme", "correct_scheme"].includes(mod_dict.mode)){
            if(permit_dict.requsr_role_system){
                url_str = urls.url_studsubj_validate_scheme;
                if(mod_dict.mode === "correct_scheme"){
                    upload_dict.correct_errors = true;
                };
                UploadChanges(upload_dict, url_str);
        // show loader
                el_confirm_loader.classList.remove(cls_visible_hide)
            };
        };
// ---  hide modal
        $("#id_mod_confirm").modal("hide");
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
                        const tblRow = document.getElementById(updated_dict.mapid);
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
            el_confirm_msg01.innerText = msg01_txt;
            el_confirm_msg02.innerText = msg02_txt;
            el_confirm_msg03.innerText = msg03_txt;
            el_confirm_btn_cancel.innerText = loc.Close
            el_confirm_btn_save.classList.add(cls_hide);
        } else {
        // hide mod_confirm when no message
            $("#id_mod_confirm").modal("hide");
        }
    }  // ModConfirmResponse

//=========  ModMessageHide  ================ PR2022-05-28
    function ModMessageHide() {
        console.log(" --- ModMessageHide --- ");
        const upload_dict = {hide_msg: true};
        UploadChanges(upload_dict, urls.url_user_modmsg_hide)
    }  // ModMessageHide

// #################################

//=========   ValidateScheme_Response   ====================== PR2021-08-29
    function ValidateScheme_Response(response_dict) {
        console.log(" ========== ValidateScheme_Response ===========");
        console.log("response_dict", response_dict);

        const today = new Date();
        const this_month_index = 1 + today.getMonth();
        const date_str = today.getFullYear() + "-" + this_month_index + "-" + today.getDate();
        const filename = "ValidateScheme_Response dd " + date_str + ".pdf";

        const response_list = [];
        if ("stud_row_count" in response_dict) {response_list.push("stud_row_count: " + response_dict.stud_row_count)};
        if ("stud_row_error" in response_dict) {response_list.push("stud_row_error: " + response_dict.stud_row_error)};
        if ("student_rows" in response_dict) {
            if (response_dict.student_rows.length) {
                for (let i = 0, dict; dict = response_dict.student_rows[i]; i++) {
                    console.log("dict", dict);
                    for (const [key, value] of Object.entries(dict)) {
                    console.log("key", key, 'value', value);
                        response_list.push("    " + key + ": " + value);
                    };
                };
            };
        };
        response_list.push("---------------");
        if ("studsubj_row_count" in response_dict) {response_list.push("studsubj_row_count: " + response_dict.studsubj_row_count)};
        if ("studsubj_row_error" in response_dict) {response_list.push("studsubj_row_error: " + response_dict.studsubj_row_error)};
        if ("studsubj_rows" in response_dict) {
            if (response_dict.studsubj_rows.length) {
                for (let i = 0, dict; dict = response_dict.studsubj_rows[i]; i++) {
                    for (const [key, value] of Object.entries(dict)) {
                        response_list.push("    " + key + ": " + value);
                    };
                };
            };
        };

        printPDFlogfile(response_list, filename )
    };  // ValidateScheme_Response

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

//###########################################################################
// +++++++++++++++++ FILTER TABLE ROWS ++++++++++++++++++++++++++++++++++++++

//========= HandleFilterKeyup  ================= PR2021-06-16
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

//========= HandleFilterToggle  =============== PR2021-06-16
    function HandleFilterToggle(el_input) {
        //console.log( "===== HandleFilterToggle  ========= ");

    // - get col_index and filter_tag from  el_input
        // PR2021-05-30 debug: use cellIndex instead of attribute data-colindex,
        // because data-colindex goes wrong with hidden columns
        // was:  const col_index = get_attr_from_el(el_input, "data-colindex")
        const col_index = el_input.parentNode.cellIndex;

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

        // default filter triple '0'; is show all, '1' is show tickmark, '2' is show without tickmark
// - toggle filter value
        new_value = (filter_value === "2") ? "0" : (filter_value === "1") ? "2" : "1";
// - get new icon_class
        icon_class =  (new_value === "2") ? "tickmark_2_1" : (new_value === "1") ? "tickmark_2_2" : "tickmark_0_0";

    // - put new filter value in filter_dict
        filter_dict[col_index] = [filter_tag, new_value]
        //console.log( "filter_dict", filter_dict);
        el_input.className = icon_class;

        Filter_TableRows();

    };  // HandleFilterToggle


//========= Filter_TableRows  ==================================== PR2020-08-17 PR22021-12-20
    function Filter_TableRows() {
        //console.log( "===== Filter_TableRows  ========= ");
        t_Filter_TableRows(tblBody_datatable, filter_dict, selected, loc.Candidate, loc.Candidates);
    }; // Filter_TableRows

//========= ResetFilterRows  ====================================
    function ResetFilterRows() {  // PR2019-10-26 PR2020-06-20
       //console.log( "===== ResetFilterRows  ========= ");

        selected.student_pk = null;
        selected.student_dict = {};
        filter_dict = {};

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

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL SELECT EXAMYEAR OR DEPARTMENT  ++++++++++++++++++++
// functions are in table.js, except for MSED_Response

//=========  MSED_Response  ================ PR2020-12-18 PR2021-05-10
    function MSED_Response(new_setting) {
        console.log( "===== MSED_Response ========= ");
        console.log( "new_setting", new_setting);

// --- reset table
        tblBody_datatable.innerText = null;

// ---  upload new selected_pk
        new_setting.page = setting_dict.sel_page;

// also retrieve the tables that have been changed because of the change in examyear / dep
        const datalist_request = {
                setting: new_setting,
                schoolsetting: {setting_key: "import_student"},
                examyear_rows: {get: true},
                school_rows: {get: true},
                department_rows: {get: true},
                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},
                student_rows: {get: true}
            };
        DatalistDownload(datalist_request);

    }  // MSED_Response


//###########################################################################
//=========  MSSSS_Response  ================ PR2021-01-23 PR2021-02-05 PR2021-07-26
    function MSSSS_Response(tblName, selected_dict, selected_pk) {
        console.log( "===== MSSSS_Response ========= ");
        //console.log( "selected_pk", selected_pk);
        //console.log( "selected_code", selected_code);
        //console.log( "selected_name", selected_name);

// --- reset table
        tblBody_datatable.innerText = null;

// ---  upload new setting and refresh page
        const datalist_request = {
                setting: {page: "page_student",
                          sel_schoolbase_pk: selected_pk  },
                school_rows: {get: true},
                department_rows: {get: true},
                level_rows: {cur_dep_only: true},
                sector_rows: {cur_dep_only: true},
                student_rows: {get: true},
            };

        DatalistDownload(datalist_request);

    }  // MSSSS_Response

//###########################################################################
// TODO move to studentsubject
//========= check_new_scheme  ======== // PR2021-03-13
    function check_new_scheme(student_pk, new_level_pk, new_sector_pk) {
        //console.log( "check_new_scheme ");

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
        //console.log( "====================== new_scheme_pk", new_scheme_pk);
        //console.log( "====================== new_scheme_name", new_scheme_name);

//--- loop through studsubj of this student
        if(student_pk){
            for (const [map_id, map_dict] of studentsubject_map.entries()) {
                if (map_dict.stud_id === student_pk) {
                    const subject_pk = map_dict.subj_id;
                    const subj_name = (map_dict.subj_name) ? map_dict.subj_name : "---";
                    const sjtp_abbrev = (map_dict.sjtp_abbrev) ? map_dict.sjtp_abbrev : "";
                    //console.log( "subj_name", subj_name);
                    if (new_scheme_pk == null) {
                        // delete studsub when no scheme
                        // skip when studsub scheme equals new_scheme
                    } else if (map_dict.scheme_id !== new_scheme_pk){
                        // check how many times this subject occurs in new scheme
                        const [count, count_same_subjecttype, new_schemeitem_pk] = count_subject_in_newscheme(new_scheme_pk, subject_pk)
                    //console.log( "count", count);
                    //console.log( "count_same_subjecttype", count_same_subjecttype);
                    //console.log( "new_schemeitem_pk", new_schemeitem_pk);
                        if (!count) {
                    //console.log( "delete studsub , subject does not exist in new_scheme");
                        } else if (count === 1 ) {
                            // if subject occurs only once in mew_scheme: replace schemeitem by new schemeitem
                    //console.log( "subject occurs only once in mew_scheme: replace schemeitem by new schemeitem");
                        } else {
                            // if subject occurs multiple times in mew_scheme: check if one exist with same subjecttype
                            if (count_same_subjecttype === 1) {
                                // if only one exist with same subjecttype: replace schemeitem by new schemeitem
                    //console.log( "only one exist with same subjecttype");
                            } else {
                                // if no schemeitem exist with same subjecttype: get schemeitem with lowest sequence
                    //console.log( "no schemeitem exist with same subjecttype");
                            }
                        }
                    }
                }
            }
        }
    }
//========= count_subject_in_newscheme  ======== // PR2021-03-13
    function count_subject_in_newscheme(scheme_pk, subject_pk, subjecttype_pk) {
        //console.log( " =====  count_subject_in_newscheme  ===== ");
        //console.log( "scheme_pk", scheme_pk);
        //console.log( "subject_pk", subject_pk);
        // check how many times this subject occurs in new scheme
        let count = 0, count1_schemeitem_pk = null;
        let count_same_subjecttype = 0, samesubjecttype_schemeitem_pk = null;
        let lowestsequence_schemeitem_pk = null, lowest_sequence = null;
        if(scheme_pk && subject_pk){
            for (const [map_id, map_dict] of schemeitem_map.entries()) {
                if (map_dict.scheme_id === scheme_pk && map_dict.subj_id === subject_pk) {
                    count += 1;
                    count1_schemeitem_pk = (count === 1) ? map_dict.id : null;
                    if (subjecttype_pk && map_dict.sjtp_id === subjecttype_pk) {
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
        //console.log( " =====  get_schemeitem_with_same_subjtype  ===== ");
        //console.log( "scheme_pk", scheme_pk);
        //console.log( "subject_pk", subject_pk);
        // check how many times this subject occurs in new scheme
        let count = 0;
        if(scheme_pk && subject_pk){
            for (const [map_id, map_dict] of schemeitem_map.entries()) {
        //console.log( "map_dict", map_dict);
                if (map_dict.scheme_id === scheme_pk && map_dict.subject_id === subject_pk) {
                    count += 1;
                }
            }
        }
    }


//========= get_regnr_info  ======== // PR2021-07-23
    function get_regnr_info(scheme_pk, subject_pk) {
        //console.log( " =====  get_regnr_info  ===== ");
/*
        'PR2015-06-13 Regnr hoeft hier niet opnieuw berekend te worden. Laat toch maar staan, maar dan wel opslaan (gebeurt in Property Let Kand_Registratienr
        strNewRegistratienr = pblKand.Kand_Registratienr_Generate(Nz(Me.pge00_txtGeslacht.Value, ""), Nz(Me.pge00_txtExamenNr.Value, ""), Nz(Me.pge00_txtStudierichtingID.Value, 0)) 'PR2014-11-09
        pblKand.Kand_RegistratieNr = strNewRegistratienr
        Me.pge00_txtRegistratieNr.Value = strNewRegistratienr

        strMsgText = "In examenjaar " & CStr(pblAfd.CurSchoolExamenjaar) & " bestaat het registratienummer van een kandidaat" & vbCrLf
        Select Case pblAfd.CurSchoolExamenjaar
        Case Is >= 2015
            strMsgText = strMsgText & "uit 13 tekens en is als volgt opgebouwd:" & vbCrLf & vbCrLf
            If Not strNewRegistratienr = vbNullString Then
                strMsgText = strMsgText & "            " & Left(strNewRegistratienr, 5) & " - " & _
                                 Mid(strNewRegistratienr, 6, 1) & " - " & _
                                 Mid(strNewRegistratienr, 7, 2) & " - " & _
                                 Mid(strNewRegistratienr, 9, 4) & " - " & _
                                 Mid(strNewRegistratienr, 13, 1) & vbCrLf & vbCrLf
            End If
            strMsgText = strMsgText & "1 tm 5:     Schoolregistratienr:   " & pblAfd.CurSchoolRegnr & vbCrLf & _
                                     "6:             Geslacht:                    M=1, V = 2" & vbCrLf & _
                                     "7 tm 8:     Examenjaar                " & Right(CStr(pblAfd.CurSchoolExamenjaar), 2) & " (schooljaar " & pblAfd.CurSchoolSchooljaar & ")" & vbCrLf & _
                                     "9 tm 12:   Examennummer        0001 etc. (001b voor bis examen) " & vbCrLf & _
                                     "13:           Studierichting:          1=Havo, 2=Vwo, 3=Tkl, 4=Pkl, 5 = Pbl."
*/
    };  // get_regnr_info


})  // document.addEventListener('DOMContentLoaded', function()