// PR2020-07-30 added

// PR2021-09-22  these variables are declared in base.js to make them global variables
//let selected_btn = "btn_user";
//let setting_dict = {};
//let permit_dict = {};
//let loc = {};
//let urls = {};
//const field_settings = {};  // PR2023-04-20 made global

//let corrector_rows = [];

const user_dicts = {};
const permit_dicts = {};

document.addEventListener('DOMContentLoaded', function() {
    "use strict";

    let el_loader = document.getElementById("id_loader");

// ---  get permits
    // permit dict gets value after downloading permit_list PR2021-03-27
    //  if user has no permit to view this page ( {% if no_access %} ): el_loader does not exist PR2020-10-02

    // Note: may_view_page is the only permit that gets its value on DOMContentLoaded,
    // all other permits get their value in function get_permits, after downloading permit_list
    const may_view_page = (!!el_loader)

    let mod_dict = {};
    let mod_MUA_dict = {};
    let mod_MUPM_dict = {};
    const mod_MSM_dict = {};
    let time_stamp = null; // used in mod add user

    let examyear_map = new Map();
    let department_map = new Map();

    //let filter_dict = {};
    let filter_mod_employee = false;

// --- get data stored in page
    let el_data = document.getElementById("id_data");
    urls.url_datalist_download = get_attr_from_el(el_data, "data-url_datalist_download");
    urls.url_usersetting_upload = get_attr_from_el(el_data, "data-url_usersetting_upload");
    urls.url_user_upload = get_attr_from_el(el_data, "data-url_user_upload");
    urls.url_user_upload_multiple = get_attr_from_el(el_data, "data-url_user_upload_multiple");

    urls.url_user_allowedsections_upload = get_attr_from_el(el_data, "data-url_user_allowedsections_upload");

    urls.url_userpermit_upload = get_attr_from_el(el_data, "data-userpermit_upload_url");
    urls.url_download_permits = get_attr_from_el(el_data, "data-user_download_permits_url");
    urls.url_download_userdata_xlsx = get_attr_from_el(el_data, "data-url_download_userdata_xlsx");

    // url_importdata_upload is stored in id_MIMP_data of modimport.html
    let columns_hidden = [];

// --- get field_settings
    field_settings.btn_user = {
        field_caption: ["", "School_code", "School", "User", "Name", "Email_address",  "Activated", "Last_loggedin", "Exam_years", "Inactive"],
        field_names: ["select", "sb_code", "school_abbrev", "username", "last_name", "email", "activated", "last_login", "ey_arr", "is_active"],
        field_tags: ["div", "div", "div", "div", "div",  "div", "div","div", "div", "div"],
        filter_tags: ["select", "text", "text",  "text",  "text", "text",  "toggle", "text","text",  "inactive"],
        field_width:  ["020", "090", "150", "150",  "180", "240",  "100", "200", "120", "090"],
        field_align: ["c", "l", "l", "l","l",  "l",  "c", "l", "l", "c"]
        };
    field_settings.btn_usergroup = {
        field_caption: ["", "School_code", "School", "User", "Edit", "Edit_wolf_2lines",
                        "Chairperson", "Secretary", "Examiner", "Second_corrector_2lines",
                        "Receive_messages", "Send_messages", "Access_to_archive",
                        "System_administrator_2lines"],
                        //"Download", "Archive", "System_administrator_2lines"],
        field_names: ["select", "sb_code", "school_abbrev", "username", "group_edit", "group_wolf",
                        "group_auth1", "group_auth2", "group_auth3", "group_auth4",
                        "group_msgreceive", "group_msgsend", "group_archive", "group_admin"],
                        //"group_download", "group_archive", "group_admin"],
        field_tags: ["div", "div", "div", "div", "div", "div", "div", "div", "div", "div", "div", "div", "div", "div", "div", "div"],
        filter_tags: ["select", "text", "text", "text", "toggle", "toggle", "toggle", "toggle", "toggle", "toggle",
                        "toggle", "toggle", "toggle", "toggle", "toggle", "toggle"],
        field_width:  ["020", "090", "150", "150", "090", "090",
                        "090", "090", "090", "090",
                        "090", "090", "090", "110"],
        field_align: ["c", "l", "l","l", "c", "c", "c", "c", "c", "c", "c", "c", "c","c", "c", "c"]
    };
    field_settings.btn_allowed = {
        field_caption: ["", "School_code", "School", "Username", "Allowed_schools", "Allowed_departments",
                        "Allowed_levels", "Allowed_subjects", "Allowed_clusters"],
        field_names: ["select", "sb_code", "school_abbrev", "username", "allowed_schoolbases", "allowed_depbases",
                        "allowed_lvlbases", "allowed_subjbases", "allowed_clusters"],
        field_tags: ["div", "div", "div", "div", "div", "div", "div", "div", "div"],
        filter_tags: ["select", "text", "text", "text", "text", "text", "text", "text", "text"],
        field_width:  ["032", "090", "150", "150", "180", "180", "180", "180", "180"],
        field_align: ["c", "l", "l", "l", "l", "l",  "l", "l", "l"]
    };
    field_settings.btn_userpermit = {
        field_caption: ["", "Organization", "Page", "Action", "Edit", "Edit_wolf_2lines",
                        "Chairperson", "Secretary", "Examiner", "Second_corrector_2lines",
                        "Receive_messages", "Send_messages", "Access_to_archive",
                        "Analyze", "System_administrator_2lines"],
        field_names: ["select", "role", "page", "action", "group_edit", "group_wolf",
                        "group_auth1", "group_auth2", "group_auth3", "group_auth4",
                        "group_msgreceive", "group_msgsend", "group_archive",
                         "group_anlz", "group_admin"],
        field_tags: ["div", "div", "div", "input", "div", "div",
                        "div", "div", "div", "div", "div", "div", "div", "div", "div"],
        filter_tags: ["select", "text", "text", "text", "toggle","toggle",
                        "toggle", "toggle", "toggle", "toggle", "toggle", "toggle", "toggle", "toggle", "toggle"],
        field_width:  ["020", "090", "120","150", "075", "075",
                        "075", "075", "090", "075", "090", "075", "075", "090", "075"],
        field_align: ["c", "l", "l", "l", "c", "c",  "c", "c", "c",  "c", "c", "c", "c", "c", "c"]
    };

    const tblHead_datatable = document.getElementById("id_tblHead_datatable");
    const tblBody_datatable = document.getElementById("id_tblBody_datatable");

// === EVENT HANDLERS ===
// === reset filter when ckicked on Escape button ===
        document.addEventListener("keydown", function (event) {
             if (event.key === "Escape") { ResetFilterRows()}
        });

 // freeze table header PR2022-01-19
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
        };

// --- BUTTON CONTAINER ------------------------------------
        const el_btn_container = document.getElementById("id_btn_container");
        if (el_btn_container){
            const btns = el_btn_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                const data_btn = get_attr_from_el(btn,"data-btn")
                btn.addEventListener("click", function() {HandleBtnSelect(data_btn)}, false )
            };
        };

// ---  HEADER BAR ------------------------------------
        const el_hdrbar_examyear = document.getElementById("id_hdrbar_examyear");
        const el_hdrbar_school = document.getElementById("id_hdrbar_school");
        const el_hdrbar_department = document.getElementById("id_hdrbar_department");

        if (el_hdrbar_examyear){
            el_hdrbar_examyear.addEventListener("click",
                function() {t_MSED_Open(loc, "examyear", examyear_map, setting_dict, permit_dict, MSED_Response)}, false );
        };
        if (el_hdrbar_department){
            el_hdrbar_department.addEventListener("click",
                function() {t_MSED_Open(loc, "department", department_map, setting_dict, permit_dict, MSED_Response)}, false );
        };
        if (el_hdrbar_school){
            el_hdrbar_school.addEventListener("click",
                function() {t_MSSSS_Open(loc, "school", school_rows, false, false, setting_dict, permit_dict, MSSSS_Response)}, false );
        };

        const el_hdrbar_allowed_sections = document.getElementById("id_hdrbar_allowed_sections");
        if (el_hdrbar_allowed_sections){
            el_hdrbar_allowed_sections.addEventListener("click", function() {t_MUPS_Open()}, false );
        };

// ---  SIDEBAR ------------------------------------
        const el_SBR_select_showall = document.getElementById("id_SBR_select_showall");
        if (el_SBR_select_showall){
            el_SBR_select_showall.addEventListener("click", function() {HandleShowAll()}, false )};
        const el_SBR_item_count = document.getElementById("id_SBR_item_count")

// ---  MODAL USER SET ALLOWED SECTIONS
        const el_MUPS_username = document.getElementById("id_MUPS_username");
        const el_MUPS_loader = document.getElementById("id_MUPS_loader");

        const el_MUPS_tbody_container = document.getElementById("id_MUPS_tbody_container");
        const el_MUPS_tbody_select = document.getElementById("id_MUPS_tbody_select");

        const el_MUPS_btn_expand_all = document.getElementById("id_MUPS_btn_expand_all");
        if (el_MUPS_btn_expand_all){
            el_MUPS_btn_expand_all.addEventListener("click", function() {MUPS_ExpandCollapse_all()}, false);
        };
        const el_MUPS_msg_modified = document.getElementById("id_MUPS_msg_modified");
        const el_MUPS_btn_save = document.getElementById("id_MUPS_btn_save");
        if (el_MUPS_btn_save){
            el_MUPS_btn_save.addEventListener("click", function() {MUPS_Save("save")}, false);
        };
        const el_MUPS_btn_cancel = document.getElementById("id_MUPS_btn_cancel");

// ---  MSSS MOD SELECT SCHOOL SUBJECT STUDENT ------------------------------
        const el_MSSSS_input = document.getElementById("id_MSSSS_input");
        const el_MSSSS_tblBody = document.getElementById("id_MSSSS_tbody_select");
        if (el_MSSSS_input){
            el_MSSSS_input.addEventListener("keyup", function(event){
                setTimeout(function() {t_MSSSS_InputKeyup(el_MSSSS_input)}, 50)});
        };
        if (el_MSSSS_input){
            el_MSSSS_input.addEventListener("click", function() {t_MSSSS_Save(el_MSSSS_input, MSSSS_Response)}, false );
        };

// ---  MODAL USER
        const el_MUA_schoolname = document.getElementById("id_MUA_schoolname");
        const el_MUA_username = document.getElementById("id_MUA_username");
        const el_MUA_last_name = document.getElementById("id_MUA_last_name");
        const el_MUA_email = document.getElementById("id_MUA_email");
        const el_MUA_btn_delete = document.getElementById("id_MUA_btn_delete");
        const el_MUA_btn_submit = document.getElementById("id_MUA_btn_submit");
        const el_MUA_btn_cancel = document.getElementById("id_MUA_btn_cancel");
        const el_MUA_footer_container = document.getElementById("id_MUA_footer_container");
        const el_MUA_footer01 = document.getElementById("id_MUA_footer01");
        const el_MUA_footer02 = document.getElementById("id_MUA_footer02");
        const el_MUA_loader = document.getElementById("id_MUA_loader");
        const el_MUA_msg_modified = document.getElementById("id_MUA_msg_modified");

        if (el_MUA_schoolname){
            el_MUA_schoolname.addEventListener("keyup", function() {MUA_InputSchoolname(el_MUA_schoolname, event.key)}, false);
        };
        if (el_MUA_username){
            el_MUA_username.addEventListener("keyup", function() {MUA_InputKeyup(el_MUA_username, event.key)}, false);
        };
        if (el_MUA_last_name){
            el_MUA_last_name.addEventListener("keyup", function() {MUA_InputKeyup(el_MUA_last_name, event.key)}, false);
        };
        if (el_MUA_email){
            el_MUA_email.addEventListener("keyup", function() {MUA_InputKeyup(el_MUA_email, event.key)}, false);
        };
        if (el_MUA_btn_delete){
            el_MUA_btn_delete.addEventListener("click", function() {ModConfirmOpen("user", "delete")}, false);
        };
        if (el_MUA_btn_submit){
            el_MUA_btn_submit.addEventListener("click", function() {MUA_Save("validate")}, false);
        };

// ---  MODAL USER PERMIT
        const el_MUPM_role = document.getElementById("id_MUPM_role");
        const el_MUPM_page = document.getElementById("id_MUPM_page");
        const el_MUPM_action = document.getElementById("id_MUPM_action");

        const el_MUPM_btn_delete = document.getElementById("id_MUPM_btn_delete");
        if (el_MUPM_btn_delete){
            el_MUPM_btn_delete.addEventListener("click", function() {MUPM_Save("delete")}, false);
        };
        const el_MUPM_btn_submit = document.getElementById("id_MUPM_btn_submit");
        if (el_MUPM_btn_submit){
            el_MUPM_btn_submit.addEventListener("click", function() {MUPM_Save("save")}, false);
        };

// ---  MOD SELECT MULTIPLE  ------------------------------
        const el_MSM_tblbody_select = document.getElementById("id_MSM_tbody_select");
        const el_MSM_input = document.getElementById("id_MSM_input")
            el_MSM_input.addEventListener("keyup", function(){
                setTimeout(function() {MSM_InputKeyup(el_MSM_input)}, 50)});
        const el_MSM_btn_save = document.getElementById("id_MSM_btn_save")
            el_MSM_btn_save.addEventListener("click", function() {MSM_Save()}, false )

// ---  MODAL IMPORT ------------------------------------
    // --- create EventListener for buttons in btn_container
        const el_MIMP_btn_container = document.getElementById("id_MIMP_btn_container");
        if(el_MIMP_btn_container){
            const btns = el_MIMP_btn_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                //PR2021-12-05 debug: data_btn as argument doesn't work, don't know why, use btn as argument instead
                // was: const data_btn = get_attr_from_el(btn, "data-btn")
                btn.addEventListener("click", function() {MIMP_btnSelectClicked(btn)}, false )
            };
        };
        const el_MIMP_filedialog = document.getElementById("id_MIMP_filedialog");
        if (el_MIMP_filedialog){el_MIMP_filedialog.addEventListener("change", function() {MIMP_HandleFiledialog(el_MIMP_filedialog)}, false)};
        const el_MIMP_btn_filedialog = document.getElementById("id_MIMP_btn_filedialog");

        if (el_MIMP_filedialog && el_MIMP_btn_filedialog){
            el_MIMP_btn_filedialog.addEventListener("click", function() {MIMP_OpenFiledialog(el_MIMP_filedialog)}, false)};
        const el_MIMP_filename = document.getElementById("id_MIMP_filename");

        const el_worksheet_list = document.getElementById("id_MIMP_worksheetlist");
        if (el_worksheet_list){el_worksheet_list.addEventListener("change", function() {MIMP_SelectWorksheet()}, false)};
        const el_MIMP_checkboxhasheader = document.getElementById("id_MIMP_hasheader");
        if (el_MIMP_checkboxhasheader){el_MIMP_checkboxhasheader.addEventListener("change", function() {MIMP_CheckboxHasheaderChanged()}, false)};
        const el_MIMP_btn_prev = document.getElementById("id_MIMP_btn_prev");
        if (el_MIMP_btn_prev){el_MIMP_btn_prev.addEventListener("click", function() {MIMP_btnPrevNextClicked("prev")}, false)};
        const el_MIMP_btn_next = document.getElementById("id_MIMP_btn_next");
        if (el_MIMP_btn_next){el_MIMP_btn_next.addEventListener("click", function() {MIMP_btnPrevNextClicked("next")}, false)};
        const el_MIMP_btn_test = document.getElementById("id_MIMP_btn_test");
        if (el_MIMP_btn_test){el_MIMP_btn_test.addEventListener("click", function() {MIMP_Save("test", RefreshDataRowsAfterUpload)}, false)};
        const el_MUP_btn_upload = document.getElementById("id_MIMP_btn_upload");
        if (el_MUP_btn_upload){el_MUP_btn_upload.addEventListener("click", function() {MIMP_Save("save", RefreshDataRowsAfterUpload)}, false)};

// ---  MOD CONFIRM ------------------------------------
        let el_confirm_header = document.getElementById("id_modconfirm_header");
        let el_confirm_loader = document.getElementById("id_modconfirm_loader");
        let el_confirm_msg_container = document.getElementById("id_modconfirm_msg_container")
        let el_confirm_btn_cancel = document.getElementById("id_modconfirm_btn_cancel");
        let el_confirm_btn_save = document.getElementById("id_modconfirm_btn_save");
        if (el_confirm_btn_save){el_confirm_btn_save.addEventListener("click", function() {ModConfirmSave()}, false)};

    if(may_view_page){
// ---  set selected menu button active
        SetMenubuttonActive(document.getElementById("id_hdr_users"));

        const datalist_request = {
                setting: {page: "page_user"},
                schoolsetting: {setting_key: "import_username"},
                locale: {page: ["page_user", "upload"]},
                examyear_rows: {get: true},
                user_rows: {get: true},
                //corrector_rows: {get: true},
                //usercompensation_rows: {get: true},
                department_rows: {skip_allowed_filter: true},
                school_rows: {skip_allowed_filter: true},
                level_rows: {skip_allowed_filter: true},
                subject_rows_page_users: {get: true},
                cluster_rows: {page: "page_user"}
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
                let check_status = false;
                let isloaded_loc = false, isloaded_settings = false, isloaded_permits = false;
                if ("locale_dict" in response) {
                    loc = response.locale_dict;
                    isloaded_loc = true;
        //console.log("loc: ", loc)
                };
                if ("setting_dict" in response) {
                    setting_dict = response.setting_dict;
                    selected_btn = setting_dict.sel_btn;
                    isloaded_settings = true;
                };
                if ("permit_dict" in response) {
                    permit_dict = response.permit_dict;
                    isloaded_permits = true;
                    // get_permits must come before CreateSubmenu and FiLLTbl
                    b_get_permits_from_permitlist(permit_dict);
                    set_columns_hidden();
                }

                if(isloaded_loc && isloaded_permits){CreateSubmenu()};
                if(isloaded_settings || isloaded_permits){b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school);};
                if ("schoolsetting_dict" in response) { i_UpdateSchoolsettingsImport(response.schoolsetting_dict) };

                if ("examyear_rows" in response) {
                    examyear_rows = response.examyear_rows;
                    b_fill_datamap(examyear_map, response.examyear_rows);
                };
                if ("user_rows" in response) {
                    //user_rows = response.user_rows;
                    b_fill_datadicts("user", "id", null, response.user_rows, user_dicts);
console.log("user_dicts",user_dicts)
                };

                //if ("corrector_rows" in response) {
                //    corrector_rows = response.corrector_rows;
                //};
                if ("permit_rows" in response) {
                    b_fill_datadicts("userpermit",  "id", null, response.permit_rows, permit_dicts);
                };
                if ("examyear_rows" in response) {
                    examyear_rows = response.examyear_rows;
                    b_fill_datamap(examyear_map, response.examyear_rows) ;
                };
                if ("department_rows" in response){
                    department_rows = response.department_rows
                };
                if ("school_rows" in response)  {
                    school_rows = response.school_rows;
                };
                if ("level_rows" in response)  {
                    level_rows = response.level_rows
                };
                if ("subject_rows_page_users" in response)  {subject_rows = response.subject_rows_page_users};
                if ("cluster_rows" in response) {
                    b_fill_datadicts("cluster", "id", null, response.cluster_rows, cluster_dictsNEW);
                };

                HandleBtnSelect(selected_btn, true);  // true = skip_upload

            },
            error: function (xhr, msg) {
// ---  hide loader
                el_loader.classList.add(cls_visible_hide);
                //console.log(msg + '\n' + xhr.responseText);
            }
        });
    }  // function DatalistDownload

    function get_datadicts_keystr(tblName, pk_int, studsubj_pk) {  // PR2023-01-05
        let key_str = tblName + "_" + ((pk_int) ? pk_int : 0);
        //if (tblName === "studsubj") {key_str += "_" + ((studsubj_pk) ? studsubj_pk : 0)};
        return key_str
    };

//=========  CreateSubmenu  ===  PR2020-07-31
    function CreateSubmenu() {
        //console.log("===  CreateSubmenu == ");
        let el_submenu = document.getElementById("id_submenu");
        // hardcode access of system admin, to get access before action 'crud' is added to permits
        const permit_system_admin = (permit_dict.requsr_role_system && permit_dict.usergroup_list.includes("admin"));
        const permit_role_admin = (permit_dict.requsr_role_admin && permit_dict.usergroup_list.includes("admin"));

        if (permit_dict.permit_crud_sameschool || permit_dict.requsr_role_admin || permit_dict.permit_crud_otherschool) {
            AddSubmenuButton(el_submenu, loc.Add_user, function() {MUA_Open("addnew")}, ["tab_show", "tab_btn_user", "tab_btn_usergroup", "tab_btn_allowed"]);
        };
        if (permit_dict.permit_crud_sameschool) {
            AddSubmenuButton(el_submenu, loc.Add_users_from_prev_year, function() {ModConfirmOpen_AddFromPreviousExamyears()}, ["tab_show", "tab_btn_user", "tab_btn_usergroup", "tab_btn_allowed"]);
            AddSubmenuButton(el_submenu, loc.Delete_user, function() {ModConfirmOpen("user","delete")}, ["tab_show", "tab_btn_user", "tab_btn_usergroup", "tab_btn_allowed"]);
            AddSubmenuButton(el_submenu, loc.Upload_usernames, function() {MIMP_Open(loc, "import_username")}, ["tab_show", "tab_btn_user", "tab_btn_usergroup", "tab_btn_allowed"], "id_submenu_import");

        };
        AddSubmenuButton(el_submenu, loc.Download_user_data, function() {ModConfirmOpen_DownloadUserdata("download_userdata_xlsx")}, ["tab_show", "tab_btn_user", "tab_btn_usergroup", "tab_btn_allowed"]);

        // hardcode access of system admin`
        if (permit_system_admin){
            AddSubmenuButton(el_submenu, loc.Add_permission, function() {MUPM_Open("addnew")}, ["tab_show", "tab_btn_userpermit"]);
            AddSubmenuButton(el_submenu, loc.Delete_permission, function() {ModConfirmOpen("userpermit","delete")}, ["tab_show", "tab_btn_userpermit"]);
            AddSubmenuButton(el_submenu, loc.Download_permissions, null, ["tab_show", "tab_btn_userpermit"], "id_submenu_download_perm", urls.url_download_permits, false);  // true = download
            AddSubmenuButton(el_submenu, loc.Upload_permissions, function() {MIMP_Open(loc, "import_permit")}, ["tab_show", "tab_btn_userpermit"], "id_submenu_import");
        };
        el_submenu.classList.remove(cls_hide);
    };  //function CreateSubmenu

//###########################################################################
// +++++++++++++++++ EVENT HANDLERS +++++++++++++++++++++++++++++++++++++++++
//=========  HandleBtnSelect  ================ PR2020-09-19 PR2021-08-01
    function HandleBtnSelect(data_btn, skip_upload) {
        //console.log( "===== HandleBtnSelect ========= ");
        //console.log( "skip_upload", skip_upload);

// ---  get  selected_btn
        // set to default "btn_user" when there is no selected_btn
        // this happens when user visits page for the first time
        // includes is to catch saved btn names that are no longer in use
        selected_btn = (data_btn && ["btn_user", "btn_usergroup", "btn_allowed", "btn_userpermit"].includes(data_btn)) ? data_btn : "btn_user"
    //console.log( "selected_btn: ", selected_btn);

// ---  upload new selected_btn, not after loading page (then skip_upload = true)
        if(!skip_upload){
            const upload_dict = {page_user: {sel_btn: selected_btn}};
            b_UploadSettings (upload_dict, urls.url_usersetting_upload);
        };

// ---  highlight selected button
        b_highlight_BtnSelect(document.getElementById("id_btn_container"), selected_btn);

// ---  show only the elements that are used in this tab
        b_show_hide_selected_elements_byClass("tab_show", "tab_" + selected_btn);

// ---  fill datatable
        FillTblRows(skip_upload);

    };  // HandleBtnSelect

//=========  HandleTblRowClicked  ================ PR2020-08-03 PR2021-08-01 PR2023-04-04
    function HandleTblRowClicked(tblRow) {

// ---  toggle select clicked row
        t_td_selected_toggle(tblRow, false);  // select_single = false: multiple selected is possible

// get data_dict from data_rows
        const data_dict = get_datadict_from_tblRow(tblRow);
        console.log( "data_dict", data_dict);

// ---  update selected studsubj_dict / student_pk / subject pk
        selected.data_dict = (data_dict) ? data_dict : null;

        console.log( "   selected", selected);
    };  // HandleTblRowClicked

//========= FillTblRows  =================== PR2021-08-01 PR2022-02-28 PR2023-04-04
    function FillTblRows(skip_upload) {
        //console.log( "===== FillTblRows  === ");

        const tblName = get_tblName_from_selectedBtn();
        const data_dicts = get_data_dicts(tblName);

        const field_setting = field_settings[selected_btn];

    //console.log( "    selected_btn", selected_btn);
    //console.log( "    tblName", tblName);
    //console.log( "    data_dicts", data_dicts);
    //console.log( "    field_setting", field_setting);

// --- show columns
        set_columns_hidden();
        //console.log( "columns_hidden", columns_hidden);

// --- reset table
        tblHead_datatable.innerText = null;
        tblBody_datatable.innerText = null

// --- create table header and filter row
        CreateTblHeader(field_setting);

// --- loop through data_dicts
        if(data_dicts){
            for (const data_dict of Object.values(data_dicts)) {
                let tblRow = CreateTblRow(tblName, field_setting, data_dict);
            };
        };

// --- filter tblRow
        // set filterdict isactive after loading page (then skip_upload = true)
        // const set_filter_isactive = skip_upload;
        Filter_TableRows(skip_upload)
    }  // FillTblRows

//=========  CreateTblHeader  === PR2020-07-31 PR2021-03-23  PR2021-08-01
    function CreateTblHeader(field_setting) {
        //console.log("===  CreateTblHeader ===== ");
        //console.log("field_setting", field_setting);
        const column_count = field_setting.field_names.length;

        //console.log("filter_dict", filter_dict);

// +++  insert header and filter row ++++++++++++++++++++++++++++++++
        let tblRow_header = tblHead_datatable.insertRow (-1);
        let tblRow_filter = tblHead_datatable.insertRow (-1);

    // --- loop through columns
        for (let j = 0; j < column_count; j++) {
            const field_name = field_setting.field_names[j];
    // - skip column if field_name in columns_hidden;
            const hide_column = columns_hidden.includes(field_name);
            if (!hide_column){

        // --- get field_caption from field_setting
                const field_caption = loc[field_setting.field_caption[j]];
                const field_tag = field_setting.field_tags[j];
                const filter_tag = field_setting.filter_tags[j];
                const class_width = "tw_" + field_setting.field_width[j] ;
                const class_align = "ta_" + field_setting.field_align[j];

// ++++++++++ insert columns in header row +++++++++++++++
        // --- add th to tblRow.
                let th_header = document.createElement("th");
        // --- add div to th, margin not working with th
                    const el_header = document.createElement("div");
        // --- add innerText to el_header
                    el_header.innerText = (field_caption) ? field_caption : null;
        // --- add width, text_align
                        // not necessary: th_header.classList.add(class_width, class_align);
                    th_header.classList.add(class_width, class_align);
                    el_header.classList.add(class_width, class_align);

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
                    // PR2021-05-30 debug: use cellIndex instead of attribute data-colindex,
                    //el_filter.setAttribute("data-colindex", j);

        // --- add EventListener to el_filter / th_filter
                    if (filter_tag === "select") {
                        th_filter.addEventListener("click", function(event){HandleFilterSelect(el_filter)});
                        add_hover(th_filter);
                    } else  if (["text", "number"].includes(filter_tag)) {
                        el_filter.addEventListener("keyup", function(event){HandleFilterKeyup(el_filter, event)});
                        add_hover(th_filter);

                    } else if (["toggle", "activated"].includes(filter_tag)) {
                        // add EventListener for icon to th_filter, not el_filter
                        th_filter.addEventListener("click", function(event){HandleFilterToggle(el_filter)});
                        th_filter.classList.add("pointer_show");

                        // default empty icon necessary to set pointer_show
                        el_filter.classList.add("tickmark_0_0");
                        add_hover(th_filter);

                    } else if (filter_tag === "inactive") {
                        // add EventListener for icon to th_filter, not el_filter
                        th_filter.addEventListener("click", function(event){HandleFilterInactive(el_filter)});
                        th_filter.classList.add("pointer_show");
                        // set inactive icon
                        const filter_showinactive = (filter_dict && filter_dict.showinactive != null) ? filter_dict.showinactive : 1;
                        const icon_class = (filter_showinactive === 2) ? "inactive_1_3" : (filter_showinactive === 1) ? "inactive_0_2" : "inactive_0_0";

                        el_filter.classList.add(icon_class);
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

                    el_filter.classList.add(class_width, class_align, "tsa_color_darkgrey", "tsa_transparent");
                th_filter.appendChild(el_filter);
                tblRow_filter.appendChild(th_filter);
            };  // if (!columns_hidden.includes(field_name))
        };  // for (let j = 0; j < column_count; j++)
    };  //  CreateTblHeader

//=========  CreateTblRow  ================ PR2020-06-09 PR2021-08-01 PR2023-04-04
    function CreateTblRow(tblName, field_setting, data_dict) {
        console.log("=========  CreateTblRow =========", tblName);
    console.log("    data_dict", data_dict);

        const field_names = field_setting.field_names;
        const field_tags = field_setting.field_tags;
        const filter_tags = field_setting.filter_tags;
        const field_align = field_setting.field_align;
        const field_width = field_setting.field_width;
        const column_count = field_names.length;

        const map_id = (data_dict.mapid) ? data_dict.mapid : null;

// ---  lookup index where this row must be inserted
        const ob1 = (data_dict.sb_code) ? data_dict.sb_code : "";
        const ob2 = (data_dict.username) ? data_dict.username : "";

        const row_index = b_recursive_tblRow_lookup(tblBody_datatable, setting_dict.user_lang, ob1, ob2);

// --- insert tblRow into tblBody at row_index
        const tblRow = tblBody_datatable.insertRow(row_index);
        tblRow.id = map_id;

    console.log("    tblRow", tblRow);
// --- add data attributes to tblRow
        tblRow.setAttribute("data-pk", data_dict.id);
        if (!data_dict.is_active){
            tblRow.setAttribute("data-inactive", "1");
        };

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);
        tblRow.setAttribute("data-ob2", ob2);
        // NIU: tblRow.setAttribute("data-ob3", ---);

// --- add EventListener to tblRow
        tblRow.addEventListener("click", function() {HandleTblRowClicked(tblRow)}, false);

// +++  insert td's into tblRow
        for (let j = 0; j < column_count; j++) {
            const field_name = field_names[j];

    // - skip column if field_name in columns_hidden;
            const hide_column = columns_hidden.includes(field_name);
            if (!hide_column){
                const field_tag = field_tags[j];
                const class_width = "tw_" + field_width[j];
                const class_align = "ta_" + field_align[j];

        // --- insert td element,
                let td = tblRow.insertCell(-1);

        // --- create element with tag from field_tags
                let el = document.createElement(field_tag);

        // --- add data-field attribute
                    el.setAttribute("data-field", field_name);

        // --- add  text_align
                el.classList.add(class_width, class_align);

        // --- append element
                td.appendChild(el);

        // --- add data-field Attribute when input element
                    if (field_tag === "input") {
                        el.setAttribute("type", "text")
                        el.setAttribute("autocomplete", "off");
                        el.setAttribute("ondragstart", "return false;");
                        el.setAttribute("ondrop", "return false;");
                // --- add class 'input_text' and text_align
                    // class 'input_text' contains 'width: 100%', necessary to keep input field within td width
                        el.classList.add("input_text");
                    }

    // --- add EventListener to td
                    if (field_name === "select") {
                        // select multiple users option added PR2023-04-12
                    } else if (field_name === "username"){
                        if(tblName ==="userallowed"){
                            el.addEventListener("click", function() {MUPS_Open(el)}, false)
                        } else {
                            el.addEventListener("click", function() {MUA_Open("update", el)}, false)
                        };
                        el.classList.add("pointer_show");
                        add_hover(el);

                    } else if (["sb_code", "school_abbrev", "username", "last_name", "email"].includes(field_name)){
                        el.addEventListener("click", function() {MUA_Open("update", el)}, false)
                        el.classList.add("pointer_show");
                        add_hover(el);

                    } else if (["role", "page"].includes(field_name)){
                        el.addEventListener("click", function() {MUPM_Open("update", el)}, false)
                        el.classList.add("pointer_show");
                        add_hover(el);

                    } else if (["role", "page", "action", "sequence"].includes(field_name)){
                        el.addEventListener("change", function(){HandleInputChange(el)});

                    } else if (field_name.slice(0, 5) === "group") {
                        // attach eventlistener and hover to td, not to el. No need to add icon_class here
                        td.addEventListener("click", function() {UploadToggleMultiple(el)}, false)
                        add_hover(td);

                    } else if (field_name.includes("allowed")) {
                        if (field_name === "allowed_clusters") {
                            if (permit_dict.permit_crud && permit_dict.requsr_same_school) {
                                td.addEventListener("click", function() {MSM_Open(el)}, false);
                                add_hover(td);
                            };
                        } else {
                            // users may always view allowed_sections
                            el.addEventListener("click", function() {MUPS_Open(el)}, false);
                            add_hover(td);
                        };

                    } else if (field_name === "activated") {
                        el.addEventListener("click", function() {ModConfirmOpen("user", "send_activation_email", el)}, false)

                    } else if (field_name === "is_active") {
                        el.addEventListener("click", function() {ModConfirmOpen("user", "is_active", el)}, false)
                        el.classList.add("inactive_0_2")
                        add_hover(el);

                    } else if ( field_name === "last_login") {
                        // pass
                    };

// --- put value in field
                UpdateField(el, data_dict);

            }  // if (!columns_hidden.includes(field_name))
        }  // for (let j = 0; j < 8; j++)

        return tblRow;
    };  // CreateTblRow

//=========  UpdateTblRow  ================ PR2020-08-01
    function UpdateTblRow(tblRow, tblName, data_dict) {
        //console.log("=========  UpdateTblRow =========");
        if (tblRow && tblRow.cells){
            for (let i = 0, td; td = tblRow.cells[i]; i++) {
                UpdateField(td.children[0], data_dict);
            };
        };
    };  // UpdateTblRow

//=========  UpdateField  ================ PR2020-08-16 PR2021-03-23 PR2021-08-01 PR2023-04-04
    function UpdateField(el_div, data_dict) {
        //console.log("=========  UpdateField =========");
        //console.log("data_dict", data_dict);

        const field_name = get_attr_from_el(el_div, "data-field");

        if(el_div && field_name){
            let inner_text = null, title_text = null, filter_value = null;
            if (field_name === "select") {
                // TODO add select multiple users option PR2020-08-18

            } else if (["sb_code", "username", "last_name", "email", "page"].includes(field_name)){
                inner_text = data_dict[field_name];
                filter_value = (inner_text) ? inner_text.toLowerCase() : null;

            } else if (field_name === "ey_arr") {
                inner_text = data_dict[field_name];
                filter_value = (inner_text) ? inner_text : null;

            } else if (field_name === "school_abbrev") {
                // schoolname cannot be put in user table, because it has no examyear PR2021-07-05
                // lookup schoolname in school_rows instead
                if (data_dict.schoolbase_id){
                    for (let i = 0, dict; dict = school_rows[i]; i++){
                        if(dict.base_id && dict.base_id === data_dict.schoolbase_id) {
                            inner_text = (dict.abbrev)  ? dict.abbrev : "---";
                            filter_value = (inner_text) ? inner_text.toLowerCase() : null;
                            break;
                }}};

            } else if (field_name.includes("allowed")){

    //console.log( "data_dict", data_dict);
    //console.log( "field_name", field_name);
    //console.log( "data_dict[field_name]", data_dict[field_name]);
    //console.log( "display", display);
    //console.log( "title", title);

                const field_value = (data_dict[field_name]) ? data_dict[field_name] : null;
                inner_text = (field_value) ? field_value : "&nbsp";
                if (field_name === "allowed_schoolbases") {
                    inner_text = (field_value) ? field_value : "&nbsp";
                    title_text = (data_dict.allowed_schoolbases_title) ? data_dict.allowed_schoolbases_title : null;
                    filter_value = (field_value) ? field_value.toLowerCase() : null;
                } else if (field_name === "allowed_subjbases") {
                    inner_text = (field_value) ? field_value : "&nbsp";
                    title_text = (data_dict.allowed_subjbases_title) ? data_dict.allowed_subjbases_title : null;
                    filter_value = (field_value) ? field_value.toLowerCase() : null;
                } else  if (field_name === "allowed_clusters") {
                    inner_text = (field_value && field_value.length) ? field_value.join(", ") : "&nbsp";
                    title_text = (field_value && field_value.length) ? field_value.join("\n") : null;
                    filter_value = (field_value && field_value.length) ? field_value.join(" ") : "&nbsp";
                } else {
                    inner_text = (field_value) ? field_value : "&nbsp";
                    filter_value = (field_value) ? field_value.toLowerCase() : null;
                };

            } else if (field_name === "role") {
                const role = data_dict[field_name];
                inner_text = (loc.role_caption && loc.role_caption[role])  ? loc.role_caption[role] : role;
                filter_value = inner_text;

            } else if (field_name === "action"){
                el_div.value = data_dict[field_name];
                filter_value = data_dict[field_name];

            } else if (field_name.slice(0, 5) === "group") {
                //  field_name is "group_edit", "group_wolf", "group_edit",  "group_auth1", "group_auth2", etc

                // data_dict[field_name] example: perm_system: true
                const db_field = field_name.slice(6);
                //  db_field is "edit", "wolf", "auth1", "auth2", etc

                // const permit_bool = (data_dict[field_name]) ? data_dict[field_name] : false;
                const permit_bool = (data_dict.usergroups) ? data_dict.usergroups.includes(db_field) : false;

    //console.log("    field_name", field_name);
    //console.log("    db_field", db_field);
    //console.log("    data_dict.usergroups", data_dict.usergroups);
    //console.log("    permit_bool", permit_bool);

                filter_value = (permit_bool) ? "1" : "0";
                el_div.className = (permit_bool) ? "tickmark_2_2" : "tickmark_0_0" ;

            } else if ( field_name === "activated") {
                const is_activated = (data_dict[field_name]) ? data_dict[field_name] : false;
                let is_expired = false;
                if(!is_activated) {
                    is_expired = activationlink_is_expired(data_dict.activationlink_sent);

// ---  add title when not activated
                    if (is_expired)  {
                        title_text = [f_format_last_modified_txt(loc.Activation_email_sent, data_dict.activationlink_sent),
                            loc.Activationlink_expired, loc.Send_activationlink].join("\n");
                    } else if(data_dict.activationlink_sent){
                        title_text = f_format_last_modified_txt(loc.Activation_email_sent, data_dict.activationlink_sent);
                    } else {
                        title_text = loc.Send_activationlink;
                    };
                }
                filter_value = (is_expired) ? "2" : (is_activated) ? "1" : "0"
                el_div.className = (is_activated) ? "tickmark_2_2" : (is_expired) ? "exclamation_0_2" : "tickmark_0_0" ;
// ---  add pointer when not is_activatd
                add_or_remove_class(el_div, "pointer_show", !is_activated)

            } else if (field_name === "is_active") {
                const is_inactive = !( (data_dict[field_name]) ? data_dict[field_name] : false );
                // give value '0' when inactive, '1' when active
                filter_value = (is_inactive) ? "0" : "1";

                el_div.className = (is_inactive) ? "inactive_1_3" : "inactive_0_2";

// ---  add title
                title_text = (is_inactive) ? loc.This_user_is_inactive : null;

            } else if ( field_name === "last_login") {
                const datetimeUTCiso = data_dict[field_name]
                const datetimeLocalJS = (datetimeUTCiso) ? new Date(datetimeUTCiso) : null;
                inner_text = format_datetime_from_datetimeJS(loc, datetimeLocalJS);
                filter_value = inner_text;
            };
// ---  put value in innerText and title
            el_div.innerHTML = inner_text;
            add_or_remove_attr (el_div, "title", !!title_text, title_text);

// ---  add attribute filter_value
        //console.log("filter_value", filter_value);
            add_or_remove_attr (el_div, "data-filter", !!filter_value, filter_value);

// ---  mark tobedeleted row with line-through red
            if (field_name !== "select") {
                add_or_remove_class(el_div, "text_decoration_line_through_red", data_dict.ey_other, "text_decoration_initial")
            };
        };  // if(el_div && field_name){
    };  // UpdateField

//=========  activationlink_is_expired  ================ PR2020-08-18
    function activationlink_is_expired(datetime_linksent_ISO){
        let is_expired = false;
        const days_valid = 7;
        if(datetime_linksent_ISO){
            const datetime_linksent_LocalJS = new Date(datetime_linksent_ISO);
            const datetime_linkexpires_LocalJS = add_daysJS(datetime_linksent_LocalJS, days_valid);
            const now = new Date();
            const time_diff_in_ms = now.getTime() - datetime_linkexpires_LocalJS.getTime();
            is_expired = (time_diff_in_ms > 0);
        };
        return is_expired;
    };

// +++++++++++++++++ UPLOAD CHANGES +++++++++++++++++ PR2020-08-03

//========= UploadToggleMultiple  ============= PR2023-04-13
    function UploadToggleMultiple(el_input) {
        console.log( " ==== UploadToggleMultiple ====");
        //console.log( "el_input", el_input);
        console.log( "  ??? permit_dict", permit_dict);
        // only called by fields starting qith  "group"

// ---  get  data_dict
        const tblRow = t_get_tablerow_selected(el_input);
        const data_dict = get_datadict_from_tblRow(tblRow);
        const tblName = get_tblName_from_mapid(data_dict.mapid);
        const fldName = get_attr_from_el(el_input, "data-field");
        const arr = (fldName) ? fldName.split("_") : null;
        const sel_usergroup = (arr && arr[1]) ? arr[1] : null;

// ---  get permit
        if (data_dict && sel_usergroup){
            if (!permit_dict.permit_crud) {
                // no permit
            } else if (data_dict.schoolbase_id !== permit_dict.requsr_schoolbase_pk && !permit_dict.requsr_role_system){
                b_show_mod_message_html(loc.cannot_change_other_organizations);
            } else {

                const has_sel_usergroup = (data_dict.usergroups) ?  data_dict.usergroups.includes(sel_usergroup) : false;
                // permit_bool = true means that the user has this usergroup
                const new_permit_bool = !has_sel_usergroup
        // ---  create mod_dict
                mod_dict = {mode: "update_usergroup_multiple",
                            table: tblName,
                            usergroup: sel_usergroup,
                            permit_bool: new_permit_bool
                            };

    // ---  loop through tblBody.rows and fill user_pk_list, skip user of tr_clicked
                let other_org_count = 0
                mod_dict.user_pk_list = [];
                for (let i = 0, tr; tr = tblBody_datatable.rows[i]; i++) {
                    if (tr.classList.contains(cls_selected) ) {
                        const tr_dict = user_dicts[tr.id];
                        // skip user of tr_clicked
                        if (tr_dict && tr_dict.id !== data_dict.id){
                            const tr_has_sel_usergroup = (tr_dict.usergroups) ?  tr_dict.usergroups.includes(sel_usergroup) : false;
                        // add only when value of has_sel_usergroup is same as value of tr_clicked
                            if (has_sel_usergroup === tr_has_sel_usergroup){

                            // skip users of other organizations
                                if (tr_dict.schoolbase_id !== permit_dict.requsr_schoolbase_pk){
                                    other_org_count += 1;
                                } else {
                                    mod_dict.user_pk_list.push(tr_dict.id);
                                };
                            };
                        };
                    };
                };
                if (!mod_dict.user_pk_list.length){
                    //use UploadToggleSingle when no other rows are selected
                     UploadToggleSingle(el_input)
                } else {
                    // add tr_clicked to user_pk_list
                    mod_dict.user_pk_list.push(data_dict.id);
                    mod_dict.user_pk_count = (mod_dict.user_pk_list) ? mod_dict.user_pk_list.length : 0;

                    const msg_list = ["<p>"];
                    if (!mod_dict.user_pk_count){
                        // this should not be possible, but let it stay
                        hide_save_btn = true
                        msg_list.push(...[loc.There_are_no, loc.users_selected, "</p>"]);
                    } else {
                        // mod_dict.user_pk_list always contains more than 1 user
                        const added_removed_txt = (has_sel_usergroup) ? loc.willbe_removed_from_users : loc.willbe_added_to_users;
                        msg_list.push(...["<p>", loc.There_are, mod_dict.user_pk_count, loc.users_selected, "</p><p>",
                                           loc.Usergroup, " '", loc.usergroupcaption[sel_usergroup], "' ", added_removed_txt]);
                        if (other_org_count){
                            const msg_list = (other_org_count === 1) ? ["</p><p>", loc.users_selected_other_org_sing] :
                                            ["</p><p>", loc.There_are, other_org_count, loc.users_selected_other_org_plur];
                            msg_list.push(...msg_list);
                        };
                        msg_list.push(...["</p><p class='pt-2'>",  loc.Do_you_want_to_continue + "</p>"]);
                    };

                    el_confirm_header.innerText = (has_sel_usergroup) ? loc.Remove_usergroup : loc.Add_usergroup;
                    el_confirm_loader.classList.add(cls_visible_hide)
                    el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");

                    el_confirm_msg_container.innerHTML = (msg_list.length) ? msg_list.join("") : null;

                    el_confirm_btn_save.innerText = loc.OK;
                    add_or_remove_class (el_confirm_btn_save, cls_hide, false);

                    add_or_remove_class (el_confirm_btn_save, "btn-primary", true, "btn-outline-danger")

                    el_confirm_btn_cancel.innerText = loc.Cancel;

            // set focus to cancel button
                    set_focus_on_el_with_timeout(el_confirm_btn_cancel, 150);

                    // show modal
                    $("#id_mod_confirm").modal({backdrop: true});
                };
            };
        };
    }; // UploadToggleMultiple

//========= UploadToggleSingle  ============= PR2020-07-31 PR2023-04-13
    function UploadToggleSingle(el_input) {
        console.log( " ==== UploadToggleSingle ====");
        console.log( "el_input", el_input);
        console.log( "permit_dict", permit_dict);
        // only called by fields starting qith  "group"
        mod_dict = {};

        const tblRow = t_get_tablerow_selected(el_input);
        const tblName = get_tblName_from_mapid(tblRow.id);
        const data_dict = get_datadict_from_tblRow(tblRow);

        if(isEmpty(data_dict)){
        } else if (!permit_dict.permit_crud) {
            // no permit
        } else if (data_dict.schoolbase_id !== permit_dict.requsr_schoolbase_pk && !permit_dict.requsr_role_system){
            b_show_mod_message_html(loc.cannot_change_other_organizations);
        } else {

            if(!isEmpty(data_dict)){
                const fldName = get_attr_from_el(el_input, "data-field");
                let permit_bool = (get_attr_from_el(el_input, "data-filter") === "1");

// show message when sysadmin tries to delete sysadmin permit
                // TODO remove requsr_pk from client
                const is_request_user = (permit_dict.requsr_pk && permit_dict.requsr_pk === data_dict.id);
                if(fldName === "group_admin" && is_request_user && permit_bool ){
                    ModConfirmOpen("usergroup", "permission_admin", el_input)
                } else {

        // ---  toggle permission el_input
                    permit_bool = (!permit_bool);

        // ---  put new permission in el_input
                    el_input.setAttribute("data-filter", (permit_bool) ? "1" : "0")
       // ---  change icon, before uploading
                    el_input.className = (permit_bool) ? "tickmark_1_2" : "tickmark_0_0";

                    const url_str = (tblName === "userpermit") ? urls.url_userpermit_upload : urls.url_user_upload;
                    const upload_dict = {mode: "update", mapid: data_dict.mapid};
                    if (tblName === "userpermit"){
                        upload_dict.userpermit_pk = data_dict.id;
                    } else {
                        // use this both for table 'user' and 'usergroup'
                        upload_dict.user_pk = data_dict.id,
                        upload_dict.schoolbase_pk = data_dict.schoolbase_id;
                    }
                    const usergroupname = fldName.substr(6);
                    upload_dict.usergroups = {}
                    upload_dict.usergroups[usergroupname] = permit_bool;
console.log( "upload_dict", upload_dict);

                    UploadChanges(upload_dict, url_str);
                }  // if(fldName === "group_admin" && is_request_user && permit_bool ){
            }  //  if(!isEmpty(data_dict)){

        }  // if(permit_dict.usergroup_system)
    }  // UploadToggleSingle

//========= UploadChanges  ============= PR2020-08-03 PR2023-01-01
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

                    console.log("response");
                    console.log( response);
                    if ("msg_html" in response) {
                        b_show_mod_message_html(response.msg_html)
                    };
                    // PR2023-09-03 mot in use
                    //if("msg_dictlist" in response){
                    //    b_show_mod_message_dictlist(response.msg_dictlist);
                    //}
                   // only used in MUPS allowes schools
                    if("msg_html" in response){
                        b_show_mod_message_html(response.msg_html, null, MUPS_MessageClose);
                    };

                    const mode = get_dict_value(response, ["mode"]);
                    if(["delete", "send_activation_email"].includes(mode)) {
                        ModConfirmResponse(response);
                    };

                    if ("updated_user_rows" in response) {
                        // must get  tblName from selectedBtn, to get 'usergroup' instead of 'user'
                        const tblName = get_tblName_from_selectedBtn();
                        RefreshDataRows(tblName, response.updated_user_rows, user_dicts, true)  // true = update
                    };
                    if ("updated_permit_rows" in response){
                        RefreshDataRows("userpermit", response.updated_permit_rows, permit_dicts, true)  // true = is_update
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

// +++++++++++++++++ UPDATE +++++++++++++++++++++++++++++++++++++++++++

// +++++++++ MOD USER ADD ++++++++++++++++ PR2020-09-18
    function MUA_Open(mode, el_input){
        console.log(" -----  MUA_Open   ---- mode: ", mode)  // modes are: addnew, update
        //console.log("permit_dict: ", permit_dict)
        //console.log("permit_dict.permit_crud_sameschool: ", permit_dict.permit_crud_sameschool)
        //console.log("permit_dict.permit_crud_otherschool: ", permit_dict.permit_crud_otherschool)
        //console.log("permit_dict.permit_addto_otherschool: ", permit_dict.permit_addto_otherschool)
        // mode = 'addnew' when called by SubmenuButton
        // mode = 'update' when called by tblRow event

        if (permit_dict.permit_crud_sameschool || permit_dict.permit_crud_otherschool || permit_dict.permit_addto_otherschool){
            let data_dict = {}, user_pk = null;
            let user_schoolbase_pk = null, user_schoolbase_code = null, user_mapid = null, user_name = null,
            user_lastname = null, user_email = null;

            let modifiedat = null, modby_name = null;
            const fldName = get_attr_from_el(el_input, "data-field");
            const is_addnew = (mode === "addnew");

        //console.log("fldName: ", fldName)

// --- get existing data_dict from data_rows
            if(el_input){
                const tblRow = t_get_tablerow_selected(el_input);
                const data_dict = get_datadict_from_tblRow(tblRow);
    console.log("    data_dict: ", data_dict)

    //console.log("data_dict", data_dict)
                if(!isEmpty(data_dict)){
                    user_mapid = data_dict.mapid;
                    user_pk = data_dict.id;
                    user_name = data_dict.username;
                    user_lastname = data_dict.last_name;
                    user_email = data_dict.email;
                    user_schoolbase_pk = data_dict.schoolbase_id;
                    user_schoolbase_code = data_dict.sb_code;
                    modifiedat= data_dict.modifiedat;
                    modby_name = data_dict.modby_name;
                };

        // when el_input is not defined: function is mode 'addnew'
            } else if (!permit_dict.permit_crud_otherschool && !permit_dict.permit_addto_otherschool){
                // when new user and not role_admin or role_system: : get user_schoolbase_pk from request_user
                user_schoolbase_pk = permit_dict.requsr_schoolbase_pk;
                user_schoolbase_code = permit_dict.requsr_schoolbase_code;
            }

            let user_schoolname = null;
            if(user_schoolbase_pk){
                user_schoolname = user_schoolbase_code
                for(let i = 0, tblRow, dict; dict = school_rows[i]; i++){
                    if (!isEmpty(dict)) {
                        if(user_schoolbase_pk === dict.base_id ) {
                            if (dict.abbrev) {user_schoolname += " - " + dict.abbrev};
                            break;
            }}}};

    console.log("    user_schoolbase_code: ", user_schoolbase_code)
    console.log("    user_schoolname: ", user_schoolname)
            mod_MUA_dict = {
                mode: mode, // modes are: addnew, update
                //skip_validate_username: is_addnew,
                //skip_validate_last_name: is_addnew,
                //skip_validate_email: is_addnew,
                user_pk: user_pk,
                user_schoolbase_pk: user_schoolbase_pk,
                user_schoolbase_code: user_schoolbase_code,
                user_schoolname: user_schoolname,
                user_mapid: user_mapid,
                username: user_name,
                last_name: user_lastname,
                email: user_email
                };
            //console.log("mod_MUA_dict: ", mod_MUA_dict)

    // ---  show only the elements that are used in this tab
            const container_element = document.getElementById("id_mod_user");
            //PR2023-05-17 was: let tab_str = (is_addnew) ? (permit_dict.permit_crud_otherschool) ? "mua_addnew_may_select_school" : "mua_addnew_noschool" : "mua_update";
            const tab_str = (is_addnew) ? (permit_dict.permit_crud_otherschool || permit_dict.permit_addto_otherschool) ? "mua_addnew_may_select_school" : "mua_addnew_noschool" : "mua_update";
            b_show_hide_selected_elements_byClass("mua_show", tab_str, container_element)
    console.log("    tab_str: ", tab_str)

    // ---  set header text
            const header_text = (is_addnew) ? loc.Add_user : loc.User + ":  " + mod_MUA_dict.username;
            const el_MUA_header = document.getElementById("id_MUA_header");
            el_MUA_header.innerText = header_text;

// ---  set text last modified
            el_MUA_msg_modified.innerText = (!is_addnew) ? f_format_last_modified_txt(loc.Last_modified, modifiedat, modby_name) : null;

    // ---  fill selecttable
            //PR2023-05-17 was: if(permit_dict.permit_crud_otherschool || permit_dict.permit_addto_otherschool){
            if(permit_dict.permit_addto_otherschool){
                MUA_FillSelectTableSchool();
            }

    // ---  remove values from elements
            MUA_ResetElements(true);  // true = also_remove_values

    // ---  put values in input boxes
            el_MUA_schoolname.value = user_schoolname;
            if (mode === "update"){
                el_MUA_username.value = mod_MUA_dict.username;
                el_MUA_last_name.value = mod_MUA_dict.last_name;
                el_MUA_email.value = mod_MUA_dict.email;
            }
    // ---  set focus to next el
            //PR2023-05-17 was:
            //const el_focus = (is_addnew && permit_dict.permit_crud_otherschool) ? el_MUA_schoolname :
            //                 ( (is_addnew && !permit_dict.permit_crud_otherschool) || (fldName === "username") ) ? el_MUA_username:
            const el_focus = (is_addnew && (permit_dict.permit_crud_otherschool || permit_dict.permit_addto_otherschool)) ? el_MUA_schoolname :
                             (is_addnew || fldName === "username") ? el_MUA_username:

                             (fldName === "last_name") ? el_MUA_last_name :
                             (fldName === "email") ? el_MUA_email : null;
            if(el_focus){setTimeout(function (){el_focus.focus()}, 50)};

    // ---  set text and hide info footer
            //el_MUA_footer01.innerText = loc.Click_to_register_new_user;
            //el_MUA_footer02.innerText = loc.We_will_send_an_email_to_the_new_user;
            //el_MUA_footer_container.classList.add(cls_hide);

    // ---  hide loader
            el_MUA_loader.classList.add(cls_hide);

    // ---  hide btn delete when addnew mode
            add_or_remove_class(el_MUA_btn_delete, cls_hide, is_addnew)

    // ---  disable btn submit
            MUA_DisableBtnSave()

    // ---  show modal
            $("#id_mod_user").modal({backdrop: true});

        }  //  if(permit_dict.permit_crud)
    };  // MUA_Open

//========= MUA_DisableBtnSave  ============= PR2021-06-30
   function MUA_DisableBtnSave(is_ok){
// ---  disable btn submit

        const disable_btn_save = (!mod_MUA_dict.user_schoolbase_pk || !el_MUA_username.value ||
                                  !el_MUA_last_name.value || !el_MUA_email.value )
        el_MUA_btn_submit.disabled = disable_btn_save;
        el_MUA_btn_submit.innerText = (mod_MUA_dict.mode === "update") ? loc.Save : loc.Create_user_account;

// ---  hide submit btn when is_ok
        add_or_remove_class(el_MUA_btn_submit, cls_hide, is_ok)

   }  // MUA_DisableBtnSave

//========= MUA_Save  ============= PR2020-08-02 PR2020-08-15 PR2021-06-30 PR2023-04-04
   function MUA_Save(mode) {
        console.log("=== MUA_Save === ");
        //console.log("mode: ", mode);
        //  mode = 'validate' when called by el_MUA_btn_submit
        //  mode = "save" after response OK

        // NOT IN USE:
        // send schoolbase, username and email to server after 1500 ms
        // abort if within that period a new value is entered.
        // checked by comparing the timestamp
        // 'args' is either 'save' or a time_stamp number
        // variable 'time_stamp' gets new value 'now' whenever a 'keyup' event occurs
        // MUA_Save has a time-out of 1500 ms
        // parameter 'args' (init_time_stamp) contains the value of time_stamp at the time this 'keyup' event occurred
        // when time_stamp = init_time_stamp, it means that there are no new keyup events within the time-out period

// ---  skip if one of the fields is blank
        let skip = !(el_MUA_username.value && el_MUA_last_name.value && el_MUA_email.value)
        if(!skip){
            // mod_MUA_dict. modes are: 'addnew', 'update'

            // in ModConfirmSave upload_dict.mode can get value "delete" or "send_activation_email"
            // in this function value of 'mode' is only 'save'

            const upload_mode = (mode === "validate") ? "validate" :
                                //(mode === "send_activation_email" ) ? "send_activation_email" :
                                (mode === "save") ? "create" :
                                (mod_MUA_dict.mode === "update") ? "update" : null;

            //console.log("mode: ", mode);
            //console.log("mod_MUA_dict.mode", mod_MUA_dict.mode);
            //console.log("................upload_mode", upload_mode);

   // ---  create mod_dict
            let upload_dict = {}
            if (upload_mode === "send_activation_email" ){
                upload_dict = { user_pk: data_dict.id,
                               schoolbase_pk: data_dict.schoolbase_pk,
                               mode: upload_mode,
                               mapid: "user_" + data_dict.id,
                                username: {value: data_dict.username}
                              };
            } else if (upload_mode === "update" ){
                upload_dict = { schoolbase_pk: mod_MUA_dict.user_schoolbase_pk,
                                mode: upload_mode,
                                username: el_MUA_username.value,
                                last_name: el_MUA_last_name.value,
                                email: el_MUA_email.value
                              };
            } else if (["validate", "create"].includes(upload_mode)){
                upload_dict = { user_pk: mod_MUA_dict.user_pk,
                                schoolbase_pk: mod_MUA_dict.user_schoolbase_pk,
                                mode: upload_mode,
                                username: el_MUA_username.value,
                                last_name: el_MUA_last_name.value,
                                email: el_MUA_email.value
                              };
            }
            console.log("upload_dict: ", upload_dict);

            // must lose focus, otherwise green / red border won't show
            //el_input.blur();
            // show loader, hide msg_info
            el_MUA_loader.classList.remove(cls_hide);
            el_MUA_footer_container.classList.add(cls_hide);
            // remove modified text
            el_MUA_msg_modified.innerText = null;

            const parameters = {"upload": JSON.stringify (upload_dict)}
            let response = "";
            $.ajax({
                type: "POST",
                url: urls.url_user_upload,
                data: parameters,
                dataType:'json',
                success: function (response) {
                    console.log( "response");
                    console.log( response);

                    // hide loader
                    el_MUA_loader.classList.add(cls_hide);

                    MUA_SetMsgElements(response);

                    if ("updated_user_rows" in response) {
                        // must get  tblName from selectedBtn, to get 'usergroup' instead of 'user'
                        const tblName = get_tblName_from_selectedBtn();
                        RefreshDataRows(tblName, response.updated_user_rows, user_dicts, true)  // true = update
                    };

                    if ("validation_ok" in response){
                        if(response.validation_ok){
                            MUA_CreateOrUpdate();
                        };
                    };

                },  // success: function (response) {
                error: function (xhr, msg) {
                    console.log(msg + '\n' + xhr.responseText);
                }  // error: function (xhr, msg) {
            });  // $.ajax({
        }
    };  // MUA_Save

//========= MUA_CreateOrUpdate  ============= PR2021-07-05
   function MUA_CreateOrUpdate() {
        //console.log("=== MUA_Save === ");
        //  mode = 'validate' when called by el_MUA_btn_submit
        //  mode = "save" after response OK
        // create new user or update existing user

// ---  skip if one of the fields is blank
        let skip = !(el_MUA_username.value && el_MUA_last_name.value && el_MUA_email.value)
        if(!skip){
            //console.log("mod_MUA_dict.mode", mod_MUA_dict.mode);
   // ---  create upload_dict
            const upload_mode = (mod_MUA_dict.user_pk) ? "update" : "create";
            const upload_dict = { mode:  upload_mode,
                                schoolbase_pk: mod_MUA_dict.user_schoolbase_pk,
                                username: el_MUA_username.value,
                                last_name: el_MUA_last_name.value,
                                email: el_MUA_email.value
                              };
            if (mod_MUA_dict.user_pk){upload_dict.user_pk = mod_MUA_dict.user_pk}
            //console.log("upload_dict: ", upload_dict);

            // must lose focus, otherwise green / red border won't show
            //el_input.blur();
            // show loader, hide msg_info
            el_MUA_loader.classList.remove(cls_hide);
            el_MUA_footer_container.classList.add(cls_hide);

            const parameters = {"upload": JSON.stringify (upload_dict)}
            let response = "";
            $.ajax({
                type: "POST",
                url: urls.url_user_upload,
                data: parameters,
                dataType:'json',
                success: function (response) {
                    //console.log( "response");
                    //console.log( response);

                    // hide loader
                    el_MUA_loader.classList.add(cls_hide);

                    MUA_SetMsgElements(response);

                    if ("updated_user_rows" in response) {
                        // must get  tblName from selectedBtn, to get 'usergroup' instead of 'user'
                        const tblName = get_tblName_from_selectedBtn();
                        RefreshDataRows(tblName, response.updated_user_rows, user_dicts, true)  // true = update
                    };

                },  // success: function (response) {
                error: function (xhr, msg) {
                    console.log(msg + '\n' + xhr.responseText);
                }  // error: function (xhr, msg) {
            });  // $.ajax({
        }
    };  // MUA_CreateOrUpdate

//========= MUA_FillSelectTableSchool  ============= PR2020--09-17
    function MUA_FillSelectTableSchool() {
        console.log("===== MUA_FillSelectTableSchool ===== ");

        const data_rows = school_rows;
        const tblBody_select = document.getElementById("id_MUA_tbody_select");
        tblBody_select.innerText = null;

// ---  loop through dictlist
        let row_count = 0

        if(data_rows && data_rows.length){
            const tblName = "school";
            for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {

        console.log("    data_dict", data_dict);
                if (!isEmpty(data_dict)) {
                    const defaultrole = (data_dict.defaultrole) ? data_dict.defaultrole : 0;
        console.log("    defaultrole", defaultrole);
        console.log("    permit_dict.requsr_role", permit_dict.requsr_role);
    // only add schools to list whith sme or lower role
                    if (defaultrole <= permit_dict.requsr_role){
        // ---  get info from data_dict
                        const base_id = data_dict.base_id;
                        const country_id = data_dict.country_id;
                        const code = (data_dict.sb_code) ? data_dict.sb_code : "";
                        const abbrev = (data_dict.abbrev) ? data_dict.abbrev : "";
        console.log("    abbrev", abbrev);

// ---  lookup index where this row must be inserted
                        let ob1 = "", row_index = -1;
                        if (code) { ob1 = code.toLowerCase()};
                        row_index = b_recursive_tblRow_lookup(tblBody_select, loc.user_lang, ob1);

//--------- insert tblBody_select row at row_index
                        const map_id = "sel_" + tblName + "_" + base_id
                        const tblRow = tblBody_select.insertRow(row_index);

                        row_count += 1;

                        tblRow.id = map_id;
                        tblRow.setAttribute("data-pk", base_id);
                        tblRow.setAttribute("data-ppk", country_id);
                        tblRow.setAttribute("data-value", code + " - " + abbrev);

// ---  add data-sortby attribute to tblRow, for ordering new rows
                        tblRow.setAttribute("data-ob1", ob1);

        // ---  add hover to select row
                        add_hover(tblRow)

        // ---  add first td to tblRow.
                        let td = tblRow.insertCell(-1);
                        let el_div = document.createElement("div");
                            el_div.classList.add("tw_075")
                            el_div.innerText = code;
                            td.appendChild(el_div);

        // ---  add second td to tblRow.
                        td = tblRow.insertCell(-1);
                        el_div = document.createElement("div");
                            el_div.classList.add("tw_150")
                            el_div.innerText = abbrev;
                            td.appendChild(el_div);

                        //td.classList.add("tw_200", "px-2", "pointer_show", cls_bc_transparent)

        // ---  add addEventListener
                        tblRow.addEventListener("click", function() {MUA_SelectSchool(tblRow, event.target)}, false);
                    } //  if (defaultrole < permit_dict.requsr_role)
                }  //  if (!isEmpty(item_dict))
            }  // for (const [map_id, data_dict] of data_map.entries())
        }  // if(data_map)

    } // MUA_FillSelectTableSchool

//========= MUA_ResetElements  ============= PR2020-08-03
    function MUA_ResetElements(also_remove_values){
        //console.log( "===== MUA_ResetElements  ========= ");
// ---  loop through input elements
        const fields = ["username", "last_name", "email", "schoolname"]
        for (let i = 0, field, el_input, el_msg; field = fields[i]; i++) {
            el_input = document.getElementById("id_MUA_" + field);
            if(el_input){
                el_input.classList.remove("border_bg_invalid", "border_bg_valid");
                if(also_remove_values){ el_input.value = null};
                let is_enabled = false;
                if  (field === "schoolname") {
                // disable field 'schoolname' when is_update or when not requsr_role_admin and not requsr_role_system
                    if (permit_dict.requsr_role_admin || permit_dict.requsr_role_system) {
                        is_enabled = (mod_MUA_dict.mode === "addnew");
                    }
                } else {
                // disable other fields when no school selected
                    is_enabled = mod_MUA_dict.user_schoolbase_pk;
                }
                add_or_remove_attr (el_input, "readonly", !is_enabled, true);
            }
            el_msg = document.getElementById("id_MUA_msg_" + field);
            if(el_msg){
                el_msg.innerText = (loc.msg_user_info[i]) ? loc.msg_user_info[i] : null;
                el_msg.classList.remove("text-danger")
            }
        }
        el_MUA_footer_container.classList.add(cls_hide);

// ---  reset text on btn cancel
        if(el_MUA_btn_cancel) {el_MUA_btn_cancel.innerText = loc.Cancel};

    }  // MUA_ResetElements

//========= MUA_SetMsgElements  ============= PR2020-08-02 PR2022-12-31
    function MUA_SetMsgElements(response){
        console.log( "===== MUA_SetMsgElements  ========= ");
        // TODO switch to render msg box
        const err_dict = (response && "msg_err" in response) ? response.msg_err : {};
        // was const validation_ok = get_dict_value(response, ["validation_ok"], false);
        const validation_ok = (response && "validation_ok" in response) ? response.validation_ok : false;


        if("user_without_userallowed" in response){

            // ---  hide modal
            $("#id_mod_user").modal("hide");
            // function ModConfirmOpen(tblName, mode, el_input, user_without_userallowed) {
            ModConfirmOpen(null, "user_without_userallowed", null, response.user_without_userallowed);

        } else {


            const el_msg_container = document.getElementById("id_MUA_msg_container")
            let err_save = false;
            let is_ok = (response && "msg_ok" in response);
            if (is_ok) {
                const ok_dict = response.msg_ok;
                document.getElementById("id_msg_01").innerText = get_dict_value(ok_dict, ["msg01"]);
                document.getElementById("id_msg_02").innerText = get_dict_value(ok_dict, ["msg02"]);
                document.getElementById("id_msg_03").innerText = get_dict_value(ok_dict, ["msg03"]);
                document.getElementById("id_msg_04").innerText = get_dict_value(ok_dict, ["msg04"]);

                el_msg_container.classList.remove("border_bg_invalid");
                el_msg_container.classList.add("border_bg_valid");
    // ---  show only the elements that are used in this tab
                b_show_hide_selected_elements_byClass("mua_show", "mua_ok");

            } else {
                // --- loop through input elements
                if("save" in err_dict){

            //console.log( "err_dict", err_dict);
                    const save_dict = err_dict.save
            //console.log( "save_dict", save_dict);
                    err_save = true;

                    document.getElementById("id_msg_01").innerText = get_dict_value(save_dict, ["msg01"]);
                    document.getElementById("id_msg_02").innerText = get_dict_value(save_dict, ["msg02"]);
                    document.getElementById("id_msg_03").innerText = get_dict_value(save_dict, ["msg03"]);
                    document.getElementById("id_msg_04").innerText = get_dict_value(save_dict, ["msg04"]);

                    el_msg_container.classList.remove("border_bg_valid");
                    el_msg_container.classList.add("border_bg_invalid");
    // ---  show only the elements that are used in this tab
                    b_show_hide_selected_elements_byClass("mua_show", "mua_ok");

                } else {
                    const fields = ["username", "last_name", "email"]
                    for (let i = 0, field; field = fields[i]; i++) {
                        const msg_err = get_dict_value(err_dict, [field]);
                        const msg_info = loc.msg_user_info[i];
            //console.log( "-----------field", field);
            //console.log( "msg_err", msg_err);
            //console.log( "msg_info", msg_info);
                        let el_input = document.getElementById("id_MUA_" + field);

                        const must_blur = ( (!!msg_err && !el_input.classList.contains("border_bg_invalid")) ||
                                            (!msg_err && !el_input.classList.contains("border_bg_valid")) );
                        if( must_blur) { el_input.blur() };
                        add_or_remove_class (el_input, "border_bg_invalid", (!!msg_err));
                        add_or_remove_class (el_input, "border_bg_valid", (!msg_err));

                        let el_msg = document.getElementById("id_MUA_msg_" + field);
                        add_or_remove_class (el_msg, "text-danger", (!!msg_err));
                        el_msg.innerText = (!!msg_err) ? msg_err : msg_info
                    }
                }

                el_MUA_btn_submit.disabled = !validation_ok;
                if(validation_ok){el_MUA_btn_submit.focus()}
            }

    // ---  show message in footer when no error and no ok msg
            add_or_remove_class(el_MUA_footer_container, cls_hide, !validation_ok )

    // ---  hide submit btn and delete btnwhen is_ok or when error
            add_or_remove_class(el_MUA_btn_submit, cls_hide, is_ok || err_save)
            add_or_remove_class(el_MUA_btn_delete, cls_hide, is_ok || err_save)

    // ---  set text on btn cancel
            if (el_MUA_btn_cancel){
                el_MUA_btn_cancel.innerText = ((is_ok || err_save) ? loc.Close : loc.Cancel);
                if(is_ok || err_save){el_MUA_btn_cancel.focus()}
            };
        };
    }  // MUA_SetMsgElements

//=========  MUA_SelectSchool  ================ PR2020-09-25
    function MUA_SelectSchool(tblRow) {
        //console.log( "===== MUA_SelectSchool ========= ");
        //console.log( tblRow);
// ---  get clicked tablerow
        if(tblRow) {
// ---  deselect all highlighted rows
            DeselectHighlightedRows(tblRow, cls_selected)
// ---  highlight clicked row
            tblRow.classList.add(cls_selected)
// ---  get pk from id of select_tblRow
            mod_MUA_dict.user_schoolbase_pk = get_attr_from_el_int(tblRow, "data-pk");
            mod_MUA_dict.country_pk = get_attr_from_el_int(tblRow, "data-ppk");
            mod_MUA_dict.user_schoolname = get_attr_from_el(tblRow, "data-value");
// ---  put value in input box
            el_MUA_schoolname.value = mod_MUA_dict.user_schoolname
            MUA_headertext();
            MUA_ResetElements();

            el_MUA_username.focus()
        }
    }  // MUA_SelectSchool

//=========  MUA_InputSchoolname  ================ PR2020-09-24 PR2021-01-01
    function MUA_InputSchoolname(el_input, event_key) {
        //console.log( "===== MUA_InputSchoolname  ========= ");
        //console.log( "event_key", event_key);

        if(el_input){
// ---  filter rows in table select_school
            const filter_dict = MUA_Filter_SelectRows(el_input.value);
            //console.log( "filter_dict", filter_dict);
// ---  if filter results have only one school: put selected school in el_MUA_schoolname
            const selected_pk = Number(filter_dict.selected_pk);
            if (selected_pk) {
                el_input.value = filter_dict.selected_value
    // ---  put pk of selected school in mod_MUA_dict
                mod_MUA_dict.user_schoolbase_pk = selected_pk;
                mod_MUA_dict.user_schoolname = filter_dict.selected_value;

                MUA_headertext();
                MUA_ResetElements();
    // ---  Set focus to flied 'username'
                el_MUA_username.focus()
            }  // if (!!selected_pk)
        }
    }; // MUA_InputSchoolname

//=========  MUA_InputKeyup  ================ PR2020-09-24
    function MUA_InputKeyup(el_input, event_key) {
        //console.log( "===== MUA_InputKeyup  ========= ");
        //console.log( "event_key", event_key);

        const fldName = get_attr_from_el(el_input, "data-field");
        if(el_input){
            if(event_key === "Shift"){
                // pass
            } else if(event_key === "Enter" && fldName === "username"){
                el_MUA_last_name.focus();
            } else if(event_key === "Enter" && fldName === "last_name"){
                el_MUA_email.focus();
            } else {
                let field_value = el_input.value;
            //console.log( "fldName", fldName);
            //console.log( "field_value", field_value);
                // fldName is 'username', 'last_name' or 'email' . fldName "schoolname" is handled in MUA_InputSchoolname
                if (fldName === "username" && field_value){
                    field_value = field_value.replace(/, /g, "_"); // replace comma or space with "_"
                    field_value = replaceChar(field_value)
                    if (field_value !== el_input.value) { el_input.value = field_value}
                }
                mod_MUA_dict[fldName] = (field_value) ? field_value : null
                mod_MUA_dict["has_changed_" + fldName] = true;

                MUA_ResetElements();
                // send schoolbase, username and email to server after 1000 ms
                // abort if within that period a new value is entered.
                // checked by comparing the timestamp
                //time_stamp = Number(Date.now())
                //setTimeout(MUA_Save, 1500, time_stamp);  // time_stamp is an argument passed to the function  MUA_Save.

                MUA_DisableBtnSave()

            }
        }
    }; // MUA_InputKeyup

//========= MUA_Filter_SelectRows  ======== PR2020-09-19
    function MUA_Filter_SelectRows(filter_text) {
        //console.log( "===== MUA_Filter_SelectRows  ========= ");
        //console.log( "filter_text: <" + filter_text + ">");
        const filter_text_lower = (filter_text) ? filter_text.toLowerCase() : "";
        let has_selection = false, has_multiple = false;
        let sel_value = null, sel_pk = null, sel_mapid = null;
        let row_count = 0;

        let tblBody_select = document.getElementById("id_MUA_tbody_select");
        for (let i = 0, tblRow; tblRow = tblBody_select.rows[i]; i++) {
            if (tblRow){
                let hide_row = false
// ---  show all rows if filter_text = ""
                if (filter_text_lower){
                    const data_value = get_attr_from_el(tblRow, "data-value")
// ---  show row if filter_text_lower is found in data_value, hide when data_value is blank
                    hide_row = (data_value) ? hide_row = (!data_value.toLowerCase().includes(filter_text_lower)) : true;
                };
                if (hide_row) {
                    tblRow.classList.add(cls_hide)
                } else {
                    tblRow.classList.remove(cls_hide);
                    row_count += 1;
// ---  put values from first row that is shown in select_value etc
                    if(!has_selection ) {
                        sel_pk = get_attr_from_el(tblRow, "data-pk");
                        sel_value = get_attr_from_el(tblRow, "data-value");
                        sel_mapid = tblRow.id;
                    } else {
                        has_multiple = true;
                    }
                    has_selection = true;
        }}};
// ---  set select_value etc null when multiple items found
        if (has_multiple){
            sel_pk = null;
            sel_value = null,
            sel_mapid = null;
        }
        return {selected_pk: sel_pk, selected_value: sel_value, selected_mapid: sel_mapid};
    }; // MUA_Filter_SelectRows

//=========  MUA_headertext  ================ PR2020-09-25
    function MUA_headertext(mode) {
        let header_text = (mode === "update") ? loc.User + ":  " + mod_MUA_dict.username : loc.Add_user;
        if(mod_MUA_dict.user_schoolbase_pk){ header_text = loc.Add_user_to + mod_MUA_dict.user_schoolname;}
        document.getElementById("id_MUA_header").innerText = header_text;
    }  // MUA_headertext
// +++++++++ END MOD USER ADD ++++++++++++++++++++++++++++++++++++++++++++++++++++

// +++++++++ MOD USER PERMIT SUBJECTS ++++++++++++++++ PR2022-10-23 PR2022-11-21 PR2022-12-04 PR2023-01-06
    function MUPS_Open(el_input){
        console.log(" -----  MUPS_Open   ---- ")

        let data_dict = {}, user_pk = null, user_role = null;
        let user_schoolbase_pk = null, user_schoolbase_code = null, user_mapid = null;
        let user_allowed_sections = {};
        let modifiedat = null, modby_name = null;

        const tblRow = t_get_tablerow_selected(el_input);

        if(tblRow){
            user_mapid = tblRow.id;

// --- get existing data_dict from data_rows
            data_dict = get_datadict_from_tblRow(tblRow);
            if(!isEmpty(data_dict)){
                user_pk = data_dict.id;
                user_role = data_dict.role;
                user_schoolbase_pk = data_dict.schoolbase_id;
                user_schoolbase_code = data_dict.sb_code;
                user_allowed_sections = (data_dict.allowed_sections) ? data_dict.allowed_sections : {};

                modifiedat= data_dict.modifiedat;
                modby_name = data_dict.modby_name;
            };

        console.log("  data_dict: ", data_dict);

            let user_schoolname = null;
            if(user_schoolbase_pk){
                user_schoolname = user_schoolbase_code
                for(let i = 0, tblRow, dict; dict = school_rows[i]; i++){
                    if (!isEmpty(dict)) {
                        if(user_schoolbase_pk === dict.base_id ) {
                            if (dict.abbrev) {user_schoolname += " - " + dict.abbrev};
                            break;
            }}}};

            // all users may view this modal PPR2023-01-26
            // only users of the same organization and permit_crud may edit
            const may_edit = (permit_dict.permit_crud && permit_dict.requsr_schoolbase_pk === user_schoolbase_pk);

        console.log("  permit_dict.requsr_schoolbase_pk: ", permit_dict.requsr_schoolbase_pk);
        console.log("  user_schoolbase_pk: ", user_schoolbase_pk);
        console.log("  may_edit: ", may_edit);

            add_or_remove_class(el_MUPS_btn_save, cls_hide, !may_edit);
            if (el_MUPS_btn_cancel){
                el_MUPS_btn_cancel.innerText = (may_edit) ? loc.Cancel : loc.Close;
            };
            mod_MUPS_dict = {
                may_edit: may_edit,
                user_pk: user_pk,
                user_role: user_role,
                user_schoolbase_pk: user_schoolbase_pk,
                user_schoolbase_code: user_schoolbase_code,
                user_schoolname: user_schoolname,
                user_mapid: user_mapid,
                allowed_sections: user_allowed_sections,
                username: (data_dict.username) ? data_dict.username : null,
                last_name: (data_dict.last_name) ? data_dict.last_name : null,
                requsr_same_school: (permit_dict.requsr_same_school) ? permit_dict.requsr_same_school : false,
                expanded: {}
                };
        //console.log("    mod_MUPS_dict: ", mod_MUPS_dict);

    // - create ordered list of all schools with schoolbase.role = c.ROLE_008_SCHOOL:
            MUPS_CreateSchoolDepLvlSubjlist();

    // ---  remove values from elements
            //add_or_remove_class(el_MUPS_loader, cls_hide, false);
            //add_or_remove_class( el_MUPS_tbody_container, cls_hide, true);
            //add_or_remove_class(el_MUPS_btn_expand_all.parentNode, cls_hide, true);

    // --- get urls.url_user_allowedsections_upload
            //const upload_dict = {
            //    mode: "get_allowed_sections",
            //    user_pk: mod_MUPS_dict.user_pk
            //}
           //UploadChanges(upload_dict, urls.url_user_allowedsections_upload);

           el_MUPS_username.value = mod_MUPS_dict.last_name;

            add_or_remove_class(el_MUPS_loader, cls_hide, true);
            add_or_remove_class( el_MUPS_tbody_container, cls_hide, false);
            add_or_remove_class(el_MUPS_btn_expand_all.parentNode, cls_hide, false);

    // ---  fill selecttable
            MUPS_FillSelectTable();

// ---  set text last modified
            el_MUPS_msg_modified.innerText = (modifiedat) ? f_format_last_modified_txt(loc.Last_modified, modifiedat, modby_name) : null;

    // ---  expand all rows
            MUPS_ExpandCollapse_all();
    // ---  show modal
            $("#id_mod_userallowedsection").modal({backdrop: true});
        };
    };  // MUPS_Open

//========= MUPS_Save  ============= PR2022-11-04
    function MUPS_Save(mode, el_input){
        console.log(" ----- MUPS_Save ---- mode: ", mode);

    // --- get urls.url_user_allowedsections_upload
        const upload_dict = {
            mode: "update",
            user_pk: mod_MUPS_dict.user_pk,
            allowed_sections: mod_MUPS_dict.allowed_sections
        }
        const url_str = urls.url_user_allowedsections_upload;
        console.log("  url_str: ", url_str);

        UploadChanges(upload_dict, url_str);

    // ---  show modal
       $("#id_mod_userallowedsection").modal("hide");
    };  // MUPS_Save

//========= MUPS_CreateSchoolDepLvlSubjlist  ============= PR2022-11-04
    function MUPS_CreateSchoolDepLvlSubjlist() {
        //console.log("===== MUPS_CreateSchoolDepLvlSubjlist ===== ");

    // create ordered list of all schools with schoolbase.role = c.ROLE_008_SCHOOL:
        mod_MUPS_dict.sorted_school_list = [];

// ---  loop through school_rows
        if(school_rows && school_rows.length ){
            //let all_depbases = "";
            //if(department_rows && department_rows.length ){
            //    for (let i = 0, data_dict; data_dict = department_rows[i]; i++) {
            //        if (all_depbases){all_depbases += ";"};
            //        all_depbases += data_dict.base_id.toString();
            //    }};

    //console.log("    mod_MUPS_dict.user_role ", mod_MUPS_dict.user_role);
            // Add 'All Schools' if req_usr is Inspectorate or Admin has multiple departments PR2023-01-26
            if (permit_dict.requsr_role >= 32 && mod_MUPS_dict.user_role >= 32) {  // ROLE_032_INSP}
                const depbases_arr = [];
                for (let i = 0, dep_row; dep_row = department_rows[i]; i++) {
                    depbases_arr.push(dep_row.base_id.toString());
                };
                const depbases = (depbases_arr.length) ? depbases_arr.join(";") : null

                // PR2023-03-26 'All schools' -9 is not in use
                //mod_MUPS_dict.sorted_school_list.push({
                //    base_id: -9,
                //    sb_code: (setting_dict.sel_country_is_sxm) ? "SXM00" : "CUR00",
                //    name: loc.All_schools,
                //    depbases: depbases
                //});
            };

            for (let i = 0, data_dict; data_dict = school_rows[i]; i++) {
                if (!isEmpty(data_dict)) {
    // - only add schools to list when schoolbase.defaultrole = c.ROLE_008_SCHOOL
                    if (data_dict.defaultrole === 8){
    // - when user_role = school: only add school of the user to the list PR2023-01-26
                        if ( (mod_MUPS_dict.user_role === 8 && mod_MUPS_dict.user_schoolbase_pk === data_dict.base_id ) ||
                            (mod_MUPS_dict.user_role > 8) ) {
                        // Note: structure must containe structure in t_MSSSS_Create_SelectRow (base_id, sb_code, name
                            mod_MUPS_dict.sorted_school_list.push({
                                base_id: data_dict.base_id,
                                sb_code: data_dict.sb_code,
                                name: data_dict.name,
                                depbases: data_dict.depbases
                            });
                        };
                    };
                };
            };
            // how to sort a list of dicts from https://stackoverflow.com/questions/979256/sorting-an-array-of-objects-by-property-values
            // PR2022-11-04
            mod_MUPS_dict.sorted_school_list.sort((a, b) => a.sb_code.localeCompare(b.sb_code) );

    //console.log("    mod_MUPS_dict.sorted_school_list", mod_MUPS_dict.sorted_school_list);
        };

// ---  loop through department_rows
        mod_MUPS_dict.sorted_department_list = [];
        if(department_rows && department_rows.length ){
            // Add 'All Departments' if school has multiple departments PR2023-01-26
            const all_dep_dict = {base_id: -9, base_code: loc.All_departments, name: loc.All_departments, sequence: 0};
            mod_MUPS_dict.sorted_department_list.push(all_dep_dict);

            for (let i = 0, data_dict; data_dict = department_rows[i]; i++) {
                if (!isEmpty(data_dict)) {
                    // Note: structure must containe structure in t_MSSSS_Create_SelectRow (base_id, sb_code, name
                    mod_MUPS_dict.sorted_department_list.push({
                        base_id: data_dict.base_id,
                        base_code: data_dict.base_code,
                        name: data_dict.name,
                        lvl_req: data_dict.lvl_req,
                        sequence: data_dict.sequence
                    });
            }};
            // how to sort a list of dicts from https://stackoverflow.com/questions/979256/sorting-an-array-of-objects-by-property-values
            // PR2022-11-04
            mod_MUPS_dict.sorted_department_list.sort((a, b) => a.sequence - b.sequence);
        };

// ---  loop through level_rows
        mod_MUPS_dict.sorted_level_list = [];

        if(level_rows && level_rows.length ){
            const all_level_dict = {base_id: -9, name: loc.All_levels, sequence: 0};
            mod_MUPS_dict.sorted_level_list.push(all_level_dict);

            for (let i = 0, level_dict; level_dict = level_rows[i]; i++) {
                if (!isEmpty(level_dict)) {
                    // Note: structure must containe structure in t_MSSSS_Create_SelectRow (base_id, sb_code, name
                    mod_MUPS_dict.sorted_level_list.push({
                        base_id: level_dict.base_id,
                        name: level_dict.name,
                        sequence: level_dict.sequence
                    });
            }};
            // how to sort a list of dicts from https://stackoverflow.com/questions/979256/sorting-an-array-of-objects-by-property-values
            // PR2022-11-04
            mod_MUPS_dict.sorted_level_list.sort((a, b) => a.sequence - b.sequence);
        };
    //console.log("    mod_MUPS_dict.sorted_level_list", mod_MUPS_dict.sorted_level_list);

// ---  loop through subject_rows
        mod_MUPS_dict.sorted_subject_list = [];
        if(subject_rows && subject_rows.length ){
            for (let i = 0, subject_dict; subject_dict = subject_rows[i]; i++) {
                if (!isEmpty(subject_dict)) {
                    // Note: structure must containe structure in t_MSSSS_Create_SelectRow (base_id, sb_code, name
                    mod_MUPS_dict.sorted_subject_list.push({
                        id: subject_dict.id,
                        base_id: subject_dict.base_id,
                        code: subject_dict.code,
                        name_nl: subject_dict.name_nl,
                        depbase_id_arr: (subject_dict.depbase_id_arr) ? subject_dict.depbase_id_arr : [],
                        lvlbase_id_arr: (subject_dict.lvlbase_id_arr) ? subject_dict.lvlbase_id_arr : []
                    });
            }};
            // how to sort a list of dicts from https://stackoverflow.com/questions/979256/sorting-an-array-of-objects-by-property-values
            // PR2022-11-04
            mod_MUPS_dict.sorted_subject_list.sort((a, b) => a.name_nl.localeCompare(b.name_nl) );
        };
    //console.log("    mod_MUPS_dict.sorted_subject_list", mod_MUPS_dict.sorted_subject_list);

    }; // MUPS_CreateSchoolDepLvlSubjlist

//========= MUPS_FillSelectTable  ============= PR2022-10-24 PR2023-01-06
    function MUPS_FillSelectTable() {
        //console.log("===== MUPS_FillSelectTable ===== ");

        const data_rows = school_rows;

        el_MUPS_tbody_select.innerText = null;

// ---  loop through mod_MUPS_dict.sorted_school_list
        if(mod_MUPS_dict.sorted_school_list.length){
            if (mod_MUPS_dict.may_edit) {

                // Select school only allowed if req_usr and user have both role greater than ROLE_008_SCHOOL PR2023-01-26
                const select_schools_allowed = (permit_dict.requsr_role > 8 && mod_MUPS_dict.user_role > 8) // ROLE_008_SCHOOL}

    // - check if there are unselected schools
                let has_unselected_schools = false, first_unselected_schoolbase_id = null, first_unselected_schoolbase_depbase_arr = null;
                if (mod_MUPS_dict.allowed_sections){
                    for (let i = 0, school_dict; school_dict = mod_MUPS_dict.sorted_school_list[i]; i++) {
                        if(!(school_dict.base_id.toString() in mod_MUPS_dict.allowed_sections)){
                            has_unselected_schools = true;
                            first_unselected_schoolbase_id = school_dict.base_id;
                            if (school_dict.depbases){
                                first_unselected_schoolbase_depbase_arr = school_dict.depbases.split(";");
                            };
                            break;
                        };
                    };
                } else {
                   has_unselected_schools = true;
                };

    // - add row 'Add school' when there are unselected schools
                if (has_unselected_schools) {
                    // if requsr_same_school and the school is not in allowed_sections: add this school to allowed_sections
                    if (mod_MUPS_dict.requsr_same_school) {
                        if (first_unselected_schoolbase_id){
                            const allowed_dict = {};
                            // if his school has only 1 dep: add to allowed_deps
                            if (first_unselected_schoolbase_depbase_arr && first_unselected_schoolbase_depbase_arr.length === 1){
                                const depbase_pk_str = first_unselected_schoolbase_depbase_arr[0];
                                const depbase_pk_int = (Number(depbase_pk_str)) ? Number(depbase_pk_str) : null;
                                if (depbase_pk_int){
                                    allowed_dict[depbase_pk_int] = {'-9': []}
                                };
                            };
                            mod_MUPS_dict.allowed_sections[first_unselected_schoolbase_id] = allowed_dict;
                        };
                    } else {
                        const addnew_dict = {base_id: -1, name: "< " + loc.Add_school + " >"};
                        MUPS_CreateTblrowSchool(addnew_dict);
                    };
                };
            };

    // -  add selected schools to table
            for (let i = 0, sb_pk_str, school_dict; school_dict = mod_MUPS_dict.sorted_school_list[i]; i++) {
                //sb_pk_str = (school_dict.base_id) ? school_dict.base_id.toString() : "0"
                if(mod_MUPS_dict.allowed_sections && school_dict.base_id.toString() in mod_MUPS_dict.allowed_sections){
                    MUPS_CreateTblrowSchool(school_dict);
                };
            };
        };
    }; // MUPS_FillSelectTable

    function MUPS_CreateTblrowSchool(school_dict) {
        //console.log("-----  MUPS_CreateTblrowSchool   ----");
        //console.log("    school_dict", school_dict);
        // PR2022-11-05

// ---  get info from school_dict
        const schoolbase_pk = school_dict.base_id;
        const code = (school_dict.sb_code) ? school_dict.sb_code : "";
        const name = (school_dict.name) ? school_dict.name : "";
        const depbases = (school_dict.depbases) ? school_dict.depbases : null;

//--------- insert tblBody_select row at end
        const tblRow = el_MUPS_tbody_select.insertRow(-1);

        tblRow.setAttribute("data-table", "school");
        tblRow.setAttribute("data-schoolbase_pk", schoolbase_pk);

// ---  add first td to tblRow.
        let td = tblRow.insertCell(-1);
            td.classList.add("awp_bg_blue")

        let el_div = document.createElement("div");
            el_div.classList.add("tw_075")
            el_div.innerText = code;
            td.appendChild(el_div);

// ---  add second td to tblRow.
        td = tblRow.insertCell(-1);
        td.classList.add("awp_bg_blue")
        el_div = document.createElement("div");
            el_div.classList.add("tw_480")
            el_div.innerText = name;
            el_div.classList.add("awp_modselect_school")

    // ---  add addEventListener
            if (schoolbase_pk === -1){
                td.addEventListener("click", function() {MUPS_SelectSchool(tblRow)}, false);
            } else {
                td.addEventListener("click", function() {MUPS_ExpandTblrows(tblRow)}, false);
            };
            td.appendChild(el_div);

// ---  add delete icon td to tblRow.
        td = tblRow.insertCell(-1);
        td.classList.add("awp_bg_blue");
        // skip when add_new
        if (schoolbase_pk !== -1){
            // only add delete btn when may_edit and not requsr_same_school and not user_role = school
            if (mod_MUPS_dict.may_edit && !mod_MUPS_dict.requsr_same_school && mod_MUPS_dict.user_role > 8) {
                el_div = document.createElement("div");
                el_div.classList.add("tw_060")
                el_div.classList.add("delete_0_0")
                //b_add_hover_delete_btn(el_div,"delete_0_2", "delete_0_2", "delete_0_0");
                add_hover(el_div, "delete_0_2", "delete_0_0")

    // ---  add addEventListener
                td.addEventListener("click", function() {MUPS_DeleteTblrow(tblRow)}, false);

                td.appendChild(el_div);
            };
// ---  add department rows
            const expanded_schoolbase_dict = mod_MUPS_dict.expanded[schoolbase_pk.toString()];

            const show_item = (!!expanded_schoolbase_dict && expanded_schoolbase_dict.expanded);
            if (show_item){
                MUPS_CreateTableDepartment(school_dict);
            };
        };
    };  // MUPS_CreateTblrowSchool

    function MUPS_CreateTableDepartment(school_dict) { // PR2022-11-04
        console.log("===== MUPS_CreateTableDepartment ===== ");
    //console.log("    school_dict", school_dict);

// ---  get info from school_dict
        const schoolbase_pk = school_dict.base_id;
        const schoolbase_pk_str = schoolbase_pk.toString();

        const sb_depbases = (school_dict.depbases) ? school_dict.depbases : "";
        const sb_depbases_arr = (school_dict.depbases) ? school_dict.depbases.split(";") : [];

// -  get allowed_depbases from this school from mod_MUPS_dict.allowed_sections
        const allowed_depbases = (mod_MUPS_dict.allowed_sections && schoolbase_pk_str in mod_MUPS_dict.allowed_sections) ?  mod_MUPS_dict.allowed_sections[schoolbase_pk_str] : {};

    console.log("    allowed_depbases", JSON.stringify(allowed_depbases));
    console.log("    mod_MUPS_dict.may_edit", mod_MUPS_dict.may_edit);

// -  add row 'Add_department' in first row if school has multipe deps and has unselected deps and may_edit
        if (mod_MUPS_dict.may_edit){
            let has_unselected_departments = false;
            if (sb_depbases_arr.length > 1){

    // - check if there are unselected departments
                for (let i = 0, dep_dict; dep_dict = mod_MUPS_dict.sorted_department_list[i]; i++) {
                    const depbase_pk_str = dep_dict.base_id.toString();
                    if (sb_depbases_arr.includes(depbase_pk_str)){
                        if (!(depbase_pk_str in allowed_depbases )) {
                            has_unselected_departments = true;
                            break;
                }}};
            };
    // - add row 'Adddep' when there are unselected departments
            if (has_unselected_departments){
                const addnew_dict = {base_id: -1, name: "< " + loc.Add_department + " >"};
                MUPS_CreateTblrowDep(addnew_dict, schoolbase_pk, sb_depbases, false); // allow_delete = false
            };
        };

// add rows with department if there is only 1
    console.log("  @@@   sb_depbases_arr", JSON.stringify(sb_depbases_arr));
    console.log("    mod_MUPS_dict.sorted_department_list", mod_MUPS_dict.sorted_department_list);

        if (sb_depbases_arr.length === 1){
// add rows with the only department of s to school
            for (let i = 0, dep_dict; dep_dict = mod_MUPS_dict.sorted_department_list[i]; i++) {
    console.log("    dep_dict", dep_dict);
    console.log("    dep_dict.base_id", dep_dict.base_id);
                if (sb_depbases_arr.includes(dep_dict.base_id.toString())){
    console.log("    MUPS_CreateTblrowDep");
                    MUPS_CreateTblrowDep(dep_dict, schoolbase_pk, sb_depbases, false); // allow_delete = false
                };
            };

        } else if (mod_MUPS_dict.sorted_department_list.length > 1){
//console.log("    mod_MUPS_dict.sorted_department_list", mod_MUPS_dict.sorted_department_list);

// add rows with selected departments to school
            for (let i = 0, dep_dict; dep_dict = mod_MUPS_dict.sorted_department_list[i]; i++) {
                if (dep_dict.base_id.toString() in allowed_depbases){
                    MUPS_CreateTblrowDep(dep_dict, schoolbase_pk, sb_depbases, true); // allow_delete = true
                };
            };
        };
    };  // MUPS_CreateTableDepartment

    function MUPS_CreateTblrowDep(department_dict, schoolbase_pk, sb_depbases, allow_delete) {
        //console.log("===== MUPS_CreateTblrowDep ===== ");
        //console.log("    department_dict", department_dict);
        //console.log("    schoolbase_pk", schoolbase_pk);
        //console.log("    sb_depbases", sb_depbases);
        // PR2022-11-05

// ---  get info from department_dict
        const depbase_pk = department_dict.base_id;
        const name = (department_dict.name) ? department_dict.name : "";
        const lvl_req = (department_dict.lvl_req) ? department_dict.lvl_req : false;
        const class_bg_color = "bg_medium_blue";
        //console.log("lvl_req", lvl_req);

//--------- insert tblBody_select row at end
        const tblRow = el_MUPS_tbody_select.insertRow(-1);

        tblRow.setAttribute("data-table", "department");
        tblRow.setAttribute("data-depbase_pk", depbase_pk);
        tblRow.setAttribute("data-schoolbase_pk", schoolbase_pk);
        tblRow.setAttribute("data-sb_depbases", sb_depbases);

// ---  add first td to tblRow.
        let td = tblRow.insertCell(-1);
            td.classList.add(class_bg_color)

        let el_div = document.createElement("div");
            el_div.classList.add("tw_075")
            td.appendChild(el_div);

// ---  add second td to tblRow.
        td = tblRow.insertCell(-1);
        td.classList.add(class_bg_color)
        el_div = document.createElement("div");
            el_div.classList.add("tw_480")
            el_div.innerHTML = "&emsp;" + name;
            td.appendChild(el_div);

            el_div.classList.add("awp_modselect_department")

    // ---  add addEventListener
            if (depbase_pk === -1){
                td.addEventListener("click", function() {MUPS_SelectDepartment(tblRow)}, false);
            } else {
                td.addEventListener("click", function() {MUPS_ExpandTblrows(tblRow)}, false);
            };

// ---  add third td to tblRow.
        td = tblRow.insertCell(-1);
        td.classList.add(class_bg_color)
        // skip when add_new or not may_edit
        if (allow_delete && mod_MUPS_dict.may_edit){
            el_div = document.createElement("div");
            el_div.classList.add("tw_060");
            el_div.classList.add("delete_0_0");
            add_hover(el_div, "delete_0_2", "delete_0_0");

// ---  add addEventListener
            td.addEventListener("click", function() {MUPS_DeleteTblrow(tblRow)}, false);

            td.appendChild(el_div);
        };

    //console.log("   depbase_pk", depbase_pk);
// ---  add level rows
        if (depbase_pk !== -1){
            let is_expanded = false;
            const expanded_schoolbase_dict = mod_MUPS_dict.expanded[schoolbase_pk.toString()];
             if (expanded_schoolbase_dict) {
                const expanded_depbase_dict = expanded_schoolbase_dict[depbase_pk.toString()];
                if (expanded_depbase_dict) {
                    is_expanded = expanded_depbase_dict.expanded;
            }};

    //console.log("   is_expanded", is_expanded);
            if (is_expanded) {
                if (lvl_req) {
                    MUPS_CreateTableLevel(department_dict, schoolbase_pk);
                } else {
                    // in Havo Vwo there is no level, use lvlbase_pk = -9 to show all subjects PR2022-22-21
                    MUPS_CreateTableSubject(-9, depbase_pk, schoolbase_pk);
                };
            };
        };
    };  // MUPS_CreateTblrowDep

//========= MUPS_CreateTableLevel  =============
    function MUPS_CreateTableLevel(dep_dict, schoolbase_pk) { // PR2022-11-06
        //console.log("===== MUPS_CreateTableLevel ===== ");
        //console.log("    dep_dict", dep_dict);

// ---  get info from dep_dict
        const schoolbase_pk_str = schoolbase_pk.toString();
        const depbase_pk = dep_dict.base_id;
        const depbase_pk_str = depbase_pk.toString();
        const lvl_req = (dep_dict.lvl_req) ? dep_dict.lvl_req : false;

// -  get levels from this department from mod_MUPS_dict.allowed_sections
        const allowed_depbases = (mod_MUPS_dict.allowed_sections && schoolbase_pk_str in mod_MUPS_dict.allowed_sections) ?  mod_MUPS_dict.allowed_sections[schoolbase_pk_str] : {};
        const allowed_lvlbases = (allowed_depbases && depbase_pk_str in allowed_depbases) ?  allowed_depbases[depbase_pk_str] : {};

// ---  loop through mod_MUPS_dict.sorted_level_list
        if(lvl_req){
            if(mod_MUPS_dict.sorted_level_list.length ){

// - check if there are unselected levels
                let has_unselected_levels = false;
                for (let i = 0, level_dict; level_dict = mod_MUPS_dict.sorted_level_list[i]; i++) {
                    if (!(level_dict.base_id.toString() in allowed_lvlbases )) {
                        has_unselected_levels = true;
                        break;
                }};

                if (has_unselected_levels && mod_MUPS_dict.may_edit){
                    const addnew_dict = {base_id: -1, name: "< " + loc.Add_level + " >"};
                    MUPS_CreateTblrowLvl(addnew_dict, depbase_pk, schoolbase_pk, false); // allow_delete = false
                };

                for (let i = 0, lvlbase_pk_str, level_dict; level_dict = mod_MUPS_dict.sorted_level_list[i]; i++) {
                    lvlbase_pk_str = level_dict.base_id.toString();
                    if(lvlbase_pk_str in allowed_lvlbases){
                        MUPS_CreateTblrowLvl(level_dict, depbase_pk, schoolbase_pk, true);
                    };
                };
            };
        };
    };  // MUPS_CreateTableLevel

//========= MUPS_CreateTblrowLvl  =============
    function MUPS_CreateTblrowLvl(level_dict, depbase_pk, schoolbase_pk, allow_delete) { // PR2022-11-05
        //console.log("===== MUPS_CreateTblrowLvl ===== ");
        //console.log("  level_dict", level_dict);

// ---  get info from level_dict
        const lvlbase_pk = level_dict.base_id;
        const name = (level_dict.name) ? level_dict.name : "";
        const class_bg_color = "c_columns_tr";

//--------- insert tblBody_select row at end
        const tblRow = el_MUPS_tbody_select.insertRow(-1);

        tblRow.setAttribute("data-table", "level");
        tblRow.setAttribute("data-schoolbase_pk", schoolbase_pk);
        tblRow.setAttribute("data-depbase_pk", depbase_pk);
        tblRow.setAttribute("data-lvlbase_pk", lvlbase_pk);

// ---  add first td to tblRow.
        let td = tblRow.insertCell(-1);
            td.classList.add(class_bg_color)

        let el_div = document.createElement("div");
            el_div.classList.add("tw_075")
            td.appendChild(el_div);

// ---  add second td to tblRow.
        td = tblRow.insertCell(-1);
        td.classList.add(class_bg_color)
        el_div = document.createElement("div");
            el_div.classList.add("tw_480")
            el_div.innerHTML = "&emsp;&emsp;" + name;

            td.appendChild(el_div);

            el_div.classList.add("awp_modselect_level")

    // ---  add addEventListener
            if (lvlbase_pk === -1){
                td.addEventListener("click", function() {MUPS_SelectLevel(tblRow)}, false);
            } else {
                td.addEventListener("click", function() {MUPS_ExpandTblrows(tblRow)}, false);
            };

// ---  add third td to tblRow.
        td = tblRow.insertCell(-1);
        td.classList.add(class_bg_color)
        // skip when add_new or not may_edit
        if (lvlbase_pk !== -1){
            // oly add delete btn when may_edit
            if (mod_MUPS_dict.may_edit) {
                el_div = document.createElement("div");
                el_div.classList.add("tw_060");
                el_div.classList.add("delete_0_0");
                add_hover(el_div, "delete_0_2", "delete_0_0");

    // ---  add addEventListener
                td.addEventListener("click", function() {MUPS_DeleteTblrow(tblRow)}, false);
                td.appendChild(el_div);
            };
        };

// ---  add subject rows
        if (lvlbase_pk !== -1){
            let show_item = false;
            const expanded_schoolbase_dict = mod_MUPS_dict.expanded[schoolbase_pk.toString()];
            if (expanded_schoolbase_dict) {
                const expanded_depbase_dict = expanded_schoolbase_dict[depbase_pk.toString()];
                if (expanded_depbase_dict) {
                    const expanded_lvlbase_dict = expanded_depbase_dict[lvlbase_pk.toString()];
                    if (expanded_lvlbase_dict) {
                        show_item = expanded_lvlbase_dict.expanded;
            }}};
            if (show_item){
                MUPS_CreateTableSubject(lvlbase_pk, depbase_pk, schoolbase_pk);
            };
        };
    };  // MUPS_CreateTblrowLvl

//========= MUPS_CreateTableSubject  ============= PR2022-11-05
    function MUPS_CreateTableSubject(lvlbase_pk, depbase_pk, schoolbase_pk) { // PR2022-11-05
        //console.log("===== MUPS_CreateTableSubject ===== ");
        //console.log("    lvlbase_pk", lvlbase_pk, typeof lvlbase_pk);

// -  get levels from this department from mod_MUPS_dict.allowed_sections
        const schoolbase_pk_str = schoolbase_pk.toString();
        const depbase_pk_str = depbase_pk.toString();
        const lvlbase_pk_str = lvlbase_pk.toString();
        const allowed_depbases = (mod_MUPS_dict.allowed_sections && schoolbase_pk_str in mod_MUPS_dict.allowed_sections) ?  mod_MUPS_dict.allowed_sections[schoolbase_pk_str] : {};
        const allowed_lvlbases = (allowed_depbases && depbase_pk_str in allowed_depbases) ?  allowed_depbases[depbase_pk_str] : {};
        const allowed_subjbase_arr = (allowed_lvlbases && lvlbase_pk_str in allowed_lvlbases) ?  allowed_lvlbases[lvlbase_pk_str] : [];

// - add row 'Add_subject' in first row if may_edit
        if (mod_MUPS_dict.may_edit){
            const addnew_dict = {base_id: -1, name_nl: "< " + loc.Add_subject + " >"};
            MUPS_CreateTblrowSubject(addnew_dict, lvlbase_pk, depbase_pk, schoolbase_pk);
        };
// ---  loop through mod_MUPS_dict.sorted_subject_list
        //console.log("    mod_MUPS_dict.sorted_subject_list", mod_MUPS_dict.sorted_subject_list);
        if(mod_MUPS_dict.sorted_subject_list.length ){
            for (let i = 0, subject_dict; subject_dict = mod_MUPS_dict.sorted_subject_list[i]; i++) {
                if (subject_dict.depbase_id_arr.includes(depbase_pk) || depbase_pk === -9 ){
                    // add when lvlbase_pk is in lvlbase_id_arr or when lvlbase_pk = -9 ('all levels')
                    if (subject_dict.lvlbase_id_arr.includes(lvlbase_pk) || lvlbase_pk === -9){
                        if (allowed_subjbase_arr && allowed_subjbase_arr.includes(subject_dict.base_id)){
                            MUPS_CreateTblrowSubject(subject_dict, lvlbase_pk, depbase_pk, schoolbase_pk);
                        };
                    };
                };
            };
        };
    };  // MUPS_CreateTableSubject

//========= MUPS_CreateTblrowSubject  =============
    function MUPS_CreateTblrowSubject(subject_dict, lvlbase_pk, depbase_pk, schoolbase_pk) {
    // PR2022-11-05
        //console.log("===== MUPS_CreateTblrowSubject ===== ");
        //console.log("    subject_dict", subject_dict);

// ---  get info from subject_dict
        const base_id = subject_dict.base_id;
        const code = (subject_dict.code) ? subject_dict.code : "";
        const name_nl = (subject_dict.name_nl) ? subject_dict.name_nl : "";

//--------- insert tblBody_select row at end
        const tblRow = el_MUPS_tbody_select.insertRow(-1);

        tblRow.setAttribute("data-table", "subject");
        tblRow.setAttribute("data-subjbase_pk", base_id);
        tblRow.setAttribute("data-schoolbase_pk", schoolbase_pk);
        tblRow.setAttribute("data-depbase_pk", depbase_pk);
        tblRow.setAttribute("data-lvlbase_pk", lvlbase_pk);

// ---  add first td to tblRow.
        let td = tblRow.insertCell(-1);
            //td.classList.add(class_bg_color)

        let el_div = document.createElement("div");
            el_div.classList.add("tw_075")
            el_div.innerText = code;
            td.appendChild(el_div);

// ---  add second td to tblRow.
        td = tblRow.insertCell(-1);
        //td.classList.add(class_bg_color)
        el_div = document.createElement("div");
            el_div.classList.add("tw_480")
            el_div.innerHTML = "&emsp;&emsp;&emsp;" + name_nl;
            td.appendChild(el_div);

            if (base_id === -1){
                el_div.classList.add("awp_modselect_subject")
                td.addEventListener("click", function() {MUPS_SelectSubject(tblRow)}, false);
                td.appendChild(el_div);
            };

// ---  add third td to tblRow.
        td = tblRow.insertCell(-1);
        //td.classList.add(class_bg_color)
        // skip when add_new or not may_edit
        if (base_id !== -1 && mod_MUPS_dict.may_edit){
            el_div = document.createElement("div");
            el_div.classList.add("tw_060")
            el_div.classList.add("delete_0_1")
            //b_add_hover_delete_btn(el_div,"delete_0_2", "delete_0_2", "delete_0_0");
            add_hover(el_div, "delete_0_2", "delete_0_1")

// ---  add addEventListener
            td.addEventListener("click", function() {MUPS_DeleteTblrow(tblRow)}, false);
            td.appendChild(el_div);
        };
    };  // MUPS_CreateTblrowSubject

    function MUPS_SelectSchool(tblRow ) {
        //console.log(" -----  MUPS_SelectSchool   ----");
        const tblName = get_attr_from_el(tblRow, "data-table");
        const pk_int = get_attr_from_el_int(tblRow, "data-schoolbase_pk");

        //console.log("    tblRow", tblRow);
        //console.log("    pk_int", pk_int);
        //console.log("    tblName", tblName);
        //console.log("    mod_MUPS_dict.allowed_sections", mod_MUPS_dict.allowed_sections);

// ---  get unselected_school_list
        const unselected_school_list = MUPS_get_unselected_school_list();
        //console.log("    unselected_school_list", unselected_school_list);

        t_MSSSS_Open(loc, "school", unselected_school_list, false, false, setting_dict, permit_dict, MUPS_SelectSchool_Response);
    };

    function MUPS_SelectDepartment(tblRow ) {
        //console.log(" -----  MUPS_SelectDepartment   ----");
        //console.log("    tblRow", tblRow);

        const tblName = get_attr_from_el(tblRow, "data-table");
        const pk_int = get_attr_from_el_int(tblRow, "data-depbase_pk");
        const schoolbase_pk = get_attr_from_el_int(tblRow, "data-schoolbase_pk");
        const sb_depbases = get_attr_from_el(tblRow, "data-sb_depbases");
        const sb_depbases_arr = (sb_depbases) ? sb_depbases.split(";") : [];

        const allowed_depbases = (!isEmpty(mod_MUPS_dict.allowed_sections)) ? mod_MUPS_dict.allowed_sections[schoolbase_pk] : {}

        //console.log("    ??? mod_MUPS_dict.sorted_department_list", mod_MUPS_dict.sorted_department_list);
        //console.log("    tblRow sb_depbases_arr", sb_depbases_arr);
        //console.log("    mod_MUPS_dict.allowed_sections", mod_MUPS_dict.allowed_sections);
        //console.log("    schoolbase_pk", schoolbase_pk);
        //console.log("    allowed_depbases", allowed_depbases);

// ---  get unselected_dep_list
        const unselected_dep_list = [];
        if(mod_MUPS_dict.sorted_department_list.length ){
            for (let i = 0, depbase_pk_str, data_dict; data_dict = mod_MUPS_dict.sorted_department_list[i]; i++) {
                depbase_pk_str = (data_dict.base_id) ? data_dict.base_id.toString() : "0";
                if ( (sb_depbases_arr && sb_depbases_arr.includes(depbase_pk_str)) || (depbase_pk_str === "-9")  ){
                    if(isEmpty(allowed_depbases) || !(depbase_pk_str in allowed_depbases)){
                        unselected_dep_list.push(data_dict);
            }}};
        };
        //console.log("  ????  unselected_dep_list", unselected_dep_list);
        t_MSED_OpenDepLvlFromRows(tblName, unselected_dep_list, schoolbase_pk, null, MUPS_DepFromRows_Response)
    };  // MUPS_SelectDepartment

    function MUPS_SelectLevel(tblRow ) {
        //console.log(" -----  MUPS_SelectLevel   ----");
        //console.log("    tblRow", tblRow);

        const tblName = get_attr_from_el(tblRow, "data-table");
        const schoolbase_pk = get_attr_from_el_int(tblRow, "data-schoolbase_pk");
        const schoolbase_pk_str = schoolbase_pk.toString();
        const depbase_pk = get_attr_from_el_int(tblRow, "data-depbase_pk");
        const depbase_pk_str = depbase_pk.toString();

        const allowed_sections = (mod_MUPS_dict.allowed_sections) ? mod_MUPS_dict.allowed_sections : {};
        const allowed_schoolbase = (schoolbase_pk_str in allowed_sections) ? allowed_sections[schoolbase_pk_str] : {};
        const allowed_depbase = (depbase_pk_str in allowed_schoolbase) ? allowed_schoolbase[depbase_pk_str] : {};

        //console.log("    allowed_depbase", allowed_depbase);

// ---  get unselected_level_list
        // row 'All_levels' is already added to mod_MUPS_dict.sorted_level_list
        //const unselected_level_list = [{base_id: -9, name: "< " + loc.All_levels + " >", sequence: 0}];
        const unselected_level_list = [];
        if(mod_MUPS_dict.sorted_level_list.length ){
            for (let i = 0, lvlbase_pk_str, data_dict; data_dict = mod_MUPS_dict.sorted_level_list[i]; i++) {
                lvlbase_pk_str = (data_dict.base_id) ? data_dict.base_id.toString() : "0";
                if(isEmpty(allowed_depbase) || !(lvlbase_pk_str in allowed_depbase)){
                    unselected_level_list.push(data_dict);
            }};
        };
        t_MSED_OpenDepLvlFromRows(tblName, unselected_level_list, schoolbase_pk, depbase_pk, MUPS_LvlFromRows_Response)
    };  // MUPS_SelectLevel

    function MUPS_SelectSubject(tblRow ) {
        //console.log(" -----  MUPS_SelectSubject   ----");
        //console.log("    tblRow", tblRow);

        const schoolbase_pk = get_attr_from_el_int(tblRow, "data-schoolbase_pk");
        const depbase_pk = get_attr_from_el_int(tblRow, "data-depbase_pk");
        const lvlbase_pk = get_attr_from_el_int(tblRow, "data-lvlbase_pk");

        mod_MUPS_dict.sel_schoolbase_pk_str = schoolbase_pk.toString();
        mod_MUPS_dict.sel_depbase_pk_str = depbase_pk.toString();
        mod_MUPS_dict.sel_lvlbase_pk_str = lvlbase_pk.toString();

// ---  get unselected_subject_list
        const unselected_subject_list = MUPS_get_unselected_subject_list(schoolbase_pk, depbase_pk, lvlbase_pk);

        //console.log("    unselected_subject_list", unselected_subject_list);
        // PR2024-05-02 was: t_MSSSS_Open(loc, "subject", unselected_subject_list, false, false, {}, permit_dict, MUPS_SelectSubject_Response);
        t_MSSSS_Open_NEW("mups", "subject", unselected_subject_list, MUPS_SelectSubject_Response, false, false, true); // false = not is_MEX

    };  // MUPS_SelectSubject

    function MUPS_get_unselected_school_list() {
// ---  get unselected_school_list
        const unselected_school_list = [];
        if(mod_MUPS_dict.sorted_school_list.length ){
            for (let i = 0, sb_pk_str, data_dict; data_dict = mod_MUPS_dict.sorted_school_list[i]; i++) {
                sb_pk_str = (data_dict.base_id) ? data_dict.base_id.toString() : "0";
                if(mod_MUPS_dict.allowed_sections && sb_pk_str in mod_MUPS_dict.allowed_sections){
                    console.log("    sb_pk_str in mod_MUPS_dict.allowed_sections", sb_pk_str);
                } else {
                    unselected_school_list.push(data_dict);
                };
            };
        };
        return unselected_school_list;
    };

    function MUPS_get_unselected_subject_list(schoolbase_pk, depbase_pk, lvlbase_pk) { //PR2022-11-07 PR2023-03-27
        console.log(" -----  MUPS_get_unselected_subject_list   ----");
        console.log("    depbase_pk", depbase_pk);
        console.log("    lvlbase_pk", lvlbase_pk);

// ---  get unselected_subject_list
        // only add subject with this depbase and lvlbase
        // skip subject thta are already in list
        const unselected_subject_list = [];
        if(mod_MUPS_dict.sorted_subject_list.length ){

            const schoolbase_pk_str = schoolbase_pk.toString();
            const depbase_pk_str = depbase_pk.toString();
            const lvlbase_pk_str = lvlbase_pk.toString();

            const allowed_sections = (mod_MUPS_dict.allowed_sections) ? mod_MUPS_dict.allowed_sections : {};
            const allowed_schoolbase = (schoolbase_pk_str in allowed_sections) ? allowed_sections[schoolbase_pk_str] : {};
            const allowed_depbase = (depbase_pk_str in allowed_schoolbase) ? allowed_schoolbase[depbase_pk_str] : {};
            const allowed_lvlbase = (lvlbase_pk_str in allowed_depbase) ? allowed_depbase[lvlbase_pk_str] : [];

            for (let i = 0, subjectbase_pk_str, data_dict; data_dict = mod_MUPS_dict.sorted_subject_list[i]; i++) {
        // check if subject exists in this dep and level
                // add when depbase_pk is in depbase_id_arr or when depbase_pk = -9 ('all levels')
                if (data_dict.depbase_id_arr.includes(depbase_pk) || depbase_pk === -9) {
                    // add when lvlbase_pk is in lvlbase_id_arr or when lvlbase_pk = -9 ('all levels')
                    if (data_dict.lvlbase_id_arr.includes(lvlbase_pk) || lvlbase_pk === -9) {
                        subjectbase_pk_str = (data_dict.base_id) ? data_dict.base_id.toString() : "0";
                        if(!(subjectbase_pk_str in allowed_lvlbase)){
                            unselected_subject_list.push(data_dict);
                        };
                    };
                };
            };
        };
        return unselected_subject_list;
    };

    function MUPS_DeleteTblrow(tblRow ) {
        console.log(" ###########-----  MUPS_DeleteTblrow   ----");
        console.log("    tblRow", tblRow);
        const tblName = get_attr_from_el(tblRow, "data-table");
        console.log("    tblName", tblName);

        const schoolbase_pk_str = get_attr_from_el_int(tblRow, "data-schoolbase_pk").toString();
        const depbase_pk_str = get_attr_from_el_int(tblRow, "data-depbase_pk").toString();
        const lvlbase_pk_str = get_attr_from_el_int(tblRow, "data-lvlbase_pk").toString();

        const allowed_sections = (mod_MUPS_dict.allowed_sections) ? mod_MUPS_dict.allowed_sections : {};
        const allowed_schoolbase = (schoolbase_pk_str in allowed_sections) ? allowed_sections[schoolbase_pk_str] : {};
        const allowed_depbase = (depbase_pk_str in allowed_schoolbase) ? allowed_schoolbase[depbase_pk_str] : {};

        console.log("    allowed_sections", allowed_sections);
        console.log("    allowed_schoolbase", allowed_schoolbase);
        console.log("    allowed_depbase", allowed_depbase);

        if (tblName === "school"){
            if (schoolbase_pk_str in mod_MUPS_dict.allowed_sections){
                delete mod_MUPS_dict.allowed_sections[schoolbase_pk_str];
            };
        } else if (tblName === "department"){
            if (depbase_pk_str in allowed_schoolbase){
                delete allowed_schoolbase[depbase_pk_str];
            };
        } else if (tblName === "level"){
            if (lvlbase_pk_str in allowed_depbase){
                delete allowed_depbase[lvlbase_pk_str];
            };
        } else if (tblName === "subject"){
            const subjbase_pk_int = get_attr_from_el_int(tblRow, "data-subjbase_pk");
            if (allowed_depbase && lvlbase_pk_str in allowed_depbase){
                const allowed_subjbase_arr = allowed_depbase[lvlbase_pk_str];
                if (allowed_subjbase_arr.length && allowed_subjbase_arr.includes(subjbase_pk_int)){
                    b_remove_item_from_array(allowed_subjbase_arr, subjbase_pk_int);
                };
            };
        };

        MUPS_FillSelectTable() ;
    };  // MUPS_DeleteTblrow

    function MUPS_LvlFromRows_Response(sel_lvlbase_pk, schoolbase_pk, depbase_pk) {
        console.log(" -----  MUPS_LvlFromRows_Response   ----");
        console.log("    sel_lvlbase_pk", sel_lvlbase_pk);
        console.log("    schoolbase_pk", schoolbase_pk);
        console.log("    depbase_pk", depbase_pk);

        if (sel_lvlbase_pk && schoolbase_pk && depbase_pk){
            const schoolbase_pk_str = schoolbase_pk.toString();
            const depbase_pk_str = depbase_pk.toString();
            const lvlbase_pk_str = sel_lvlbase_pk.toString();

            const allowed_sections = (mod_MUPS_dict.allowed_sections) ? mod_MUPS_dict.allowed_sections : {};
            const allowed_schoolbase = (schoolbase_pk_str in allowed_sections) ? allowed_sections[schoolbase_pk_str] : {};
            const allowed_depbase = (depbase_pk_str in allowed_schoolbase) ? allowed_schoolbase[depbase_pk_str] : {};

        console.log("    lvlbase_pk_str", lvlbase_pk_str);
        console.log("    allowed_depbase", allowed_depbase);
            if( isEmpty(allowed_depbase) || !(lvlbase_pk_str in allowed_depbase) ){
                allowed_depbase[lvlbase_pk_str] = [];
        console.log("    allowed_depbase[lvlbase_pk_str]", allowed_depbase[lvlbase_pk_str]);

                // when lvl added and mode = showall: show 'add subject' PR20223-01-26
                if (mod_MUPS_dict.expand_all) {
                    const expanded_schoolbase_dict = mod_MUPS_dict.expanded[schoolbase_pk_str];
                console.log("    expanded_schoolbase_dict", expanded_schoolbase_dict);
                    if (expanded_schoolbase_dict) {
                        const expanded_depbase_dict = expanded_schoolbase_dict[depbase_pk_str];
                console.log("    expanded_depbase_dict", expanded_depbase_dict);
                        if (expanded_depbase_dict) {
                            if (!(lvlbase_pk_str in expanded_depbase_dict)){
                                expanded_depbase_dict[lvlbase_pk_str] = {"expanded": true}
                            };
                        };
                    };
                };
            };
        };

        MUPS_FillSelectTable();
    };

    function MUPS_DepFromRows_Response(sel_depbase_pk, schoolbase_pk, depbase_pkNIU) {
        console.log(" -----  MUPS_DepFromRows_Response   ----");
        console.log("    sel_depbase_pk", sel_depbase_pk, typeof sel_depbase_pk);
        console.log("    schoolbase_pk", schoolbase_pk, typeof schoolbase_pk);

        if (sel_depbase_pk && schoolbase_pk){
            // lookup depbase, get lvl_req
             let lvl_req = false;
             for (let i = 0, data_dict; data_dict = mod_MUPS_dict.sorted_department_list[i]; i++) {
                if (data_dict.base_id == sel_depbase_pk) {
                    lvl_req = data_dict.lvl_req;
                    break;
                };
            };
            console.log("    lvl_req", lvl_req)

            const allowed_sections = mod_MUPS_dict.allowed_sections[schoolbase_pk.toString()];
            console.log("    allowed_sections", allowed_sections, typeof allowed_sections);
            const schoolbase_pk_str = schoolbase_pk.toString();
            const depbase_pk_str = sel_depbase_pk.toString();
            if( isEmpty(allowed_sections) || !(depbase_pk_str in allowed_sections) ){
                // add 'all levels' (-9) when lvl_req is false (Havo Vwo)
                allowed_sections[depbase_pk_str] = (!lvl_req) ? {"-9": []} : {};

                // when dep added and mode = showall: show 'add level' PR20223-01-26
                if (mod_MUPS_dict.expand_all) {
                    const expanded_schoolbase_dict = mod_MUPS_dict.expanded[schoolbase_pk_str];
                console.log("    expanded_schoolbase_dict", expanded_schoolbase_dict);
                    if (expanded_schoolbase_dict) {
                        const expanded_depbase_dict = expanded_schoolbase_dict[depbase_pk_str];
                console.log("    expanded_depbase_dict", expanded_depbase_dict);
                        if (!(depbase_pk_str in expanded_schoolbase_dict)){
                            expanded_schoolbase_dict[depbase_pk_str] = {"expanded": true}
                        };
                    };
                };
            };
            const allowed_depbases = allowed_sections[depbase_pk_str];
            console.log("    allowed_depbases", allowed_depbases);
        };
        console.log("@@@ mod_MUPS_dict.allowed_sections", mod_MUPS_dict.allowed_sections);

// ---  fill selecttable
        MUPS_FillSelectTable();
    };

//=========  MUPS_SelectSchool_Response  ================ PR2022-10-26 PR2022-11-21
    function MUPS_SelectSchool_Response(tblName, selected_dict, selected_pk) {
        console.log( "===== MUPS_SelectSchool_Response ========= ");
        console.log( "    tblName", tblName);
        console.log( "    selected_dict", selected_dict);
        console.log( "    selected_pk", selected_pk, typeof selected_pk);

        // Note: when tblName = school: pk_int = schoolbase_pk
        if (selected_pk === -1) { selected_pk = null};
        if (selected_pk){
            const schoolbase_pk_str = selected_pk.toString();

            // skip when schoolbase_pk_str in allowed_sections
            if (!(schoolbase_pk_str in mod_MUPS_dict.allowed_sections)){
                const sb_dict = {};
                // add key depbase_pk_str if this school has only 1 department
                if (selected_dict.depbases){
                    const sb_depbases_arr = selected_dict.depbases.split(";");
                    if (sb_depbases_arr.length === 1){
                        const depbase_pk_str =  sb_depbases_arr[0];
                        sb_dict[depbase_pk_str] = {};
                    } else {

                        // when dep added and mode = showall: show 'add level' PR20223-01-26
                        if (mod_MUPS_dict.expand_all) {
                            const expanded_schoolbase_dict = mod_MUPS_dict.expanded[schoolbase_pk_str];
                        console.log("   @@@@@@@@@@@@  schoolbase_pk_str", schoolbase_pk_str);
                        console.log("   @@@@@@@@@@@@  mod_MUPS_dict.expanded", mod_MUPS_dict.expanded);
                        console.log("   @@@@@@@@@@@@  expanded_schoolbase_dict", expanded_schoolbase_dict);
                            if (expanded_schoolbase_dict) {

                            // PR2023-05-11 Sentry debug: ReferenceError depbase_pk_str is not defined
                            // TODO solve this error

                                const expanded_depbase_dict = expanded_schoolbase_dict[depbase_pk_str];
                        console.log("    expanded_depbase_dict", expanded_depbase_dict);
                                if (!(depbase_pk_str in expanded_schoolbase_dict)){
                                    expanded_schoolbase_dict[depbase_pk_str] = {"expanded": true}
                                };
                            };
                        };
                    };
                };
                mod_MUPS_dict.allowed_sections[schoolbase_pk_str] = sb_dict;
            };

    // ---  fill selecttable
            MUPS_FillSelectTable();
        };
    }  // MUPS_SelectSchool_Response

//=========  MUPS_SelectSubject_Response  ================ PR2022-10-26 PR2022-11-21 PR2024-05-02
    function MUPS_SelectSubject_Response(modalName, tblName, selected_dict, selected_pk) {
        console.log( "===== MUPS_SelectSubject_Response ========= ");
        console.log( "    tblName", tblName);
        console.log( "    selected_dict", selected_dict);
        console.log( "    selected_pk", selected_pk, typeof selected_pk);

        // Note: when tblName = school: pk_int = schoolbase_pk
        if (selected_pk === -1) { selected_pk = null};
        if (selected_pk){
            const selected_pk_str = selected_pk.toString();

            const subjbase_pk = selected_dict.base_id;
        console.log( "    subjbase_pk", subjbase_pk, typeof subjbase_pk);
        console.log( "    mod_MUPS_dict.sel_schoolbase_pk_str", mod_MUPS_dict.sel_schoolbase_pk_str, typeof mod_MUPS_dict.sel_schoolbase_pk_str);
        console.log( "    mod_MUPS_dict.sel_depbase_pk_str", mod_MUPS_dict.sel_depbase_pk_str, typeof mod_MUPS_dict.sel_depbase_pk_str);
        console.log( "    mod_MUPS_dict.sel_lvlbase_pk_str", mod_MUPS_dict.sel_lvlbase_pk_str, typeof mod_MUPS_dict.sel_lvlbase_pk_str);

            if (subjbase_pk){
                const allowed_sections = (mod_MUPS_dict.allowed_sections) ? mod_MUPS_dict.allowed_sections : {};
                const allowed_depbases = (mod_MUPS_dict.sel_schoolbase_pk_str in allowed_sections) ? allowed_sections[mod_MUPS_dict.sel_schoolbase_pk_str] : {};

        console.log( "    allowed_depbases", allowed_depbases);
                const allowed_lvlbases = (mod_MUPS_dict.sel_depbase_pk_str in allowed_depbases) ? allowed_depbases[mod_MUPS_dict.sel_depbase_pk_str] : {};

        console.log( "    allowed_lvlbases", allowed_lvlbases);
                // allowed_subjbase_arr contains integers, not strings PR2022-12-04
                const allowed_subjbase_arr = (mod_MUPS_dict.sel_lvlbase_pk_str in allowed_lvlbases) ? allowed_lvlbases[mod_MUPS_dict.sel_lvlbase_pk_str] : [];

        console.log( "    allowed_subjbase_arr", allowed_subjbase_arr);
                if (allowed_subjbase_arr && !allowed_subjbase_arr.includes(subjbase_pk)){
                    allowed_subjbase_arr.push(subjbase_pk);
                };
            };

    // ---  fill selecttable
            MUPS_FillSelectTable();
        };
    }  // MUPS_SelectSubject_Response

//=========  MUPS_MessageClose  ================ PR2022-10-26
    function MUPS_MessageClose() {
        console.log(" --- MUPS_MessageClose --- ");

        $("#id_mod_userallowedsection").modal("hide");
    }  // MUPS_MessageClose

    function MUPS_ExpandTblrows(tblRow ) {
        console.log("-----  MUPS_ExpandTblrows   ----");
        console.log("    tblRow", tblRow);

        const tblName = get_attr_from_el(tblRow, "data-table");
        console.log("    tblName", tblName);

        const schoolbase_pk = get_attr_from_el_int(tblRow, "data-schoolbase_pk");
        console.log("    schoolbase_pk", schoolbase_pk);
        if (schoolbase_pk){
            const schoolbase_pk_str = schoolbase_pk.toString();

            if (!(schoolbase_pk_str in mod_MUPS_dict.expanded)){
                mod_MUPS_dict.expanded[schoolbase_pk_str] = {expanded: false};
            };
            const expanded_school_dict = mod_MUPS_dict.expanded[schoolbase_pk_str];

            if (tblName === "school"){
                expanded_school_dict.expanded = !expanded_school_dict.expanded;

        console.log("     expanded_school_dict", JSON.stringify ( expanded_school_dict));
        // ABel tasman {"2":{"expanded":false,"-9":{"expanded":false}},"expanded":true}
        // St Jozef    {"1":{"expanded":false},"expanded":true}

            } else {
                const depbase_pk = get_attr_from_el_int(tblRow, "data-depbase_pk");
                if (depbase_pk){
                    const depbase_pk_str = depbase_pk.toString();
                    if (!(depbase_pk_str in expanded_school_dict)){
                        expanded_school_dict[depbase_pk_str] = {expanded: false};
                    };
                    const expanded_depbase_dict = expanded_school_dict[depbase_pk_str];

                    if (tblName === "department"){
                        expanded_depbase_dict.expanded = !expanded_depbase_dict.expanded;
                    } else {
                        const lvlbase_pk = get_attr_from_el_int(tblRow, "data-lvlbase_pk");
                        if (lvlbase_pk){
                            const lvlbase_pk_str = lvlbase_pk.toString();
                            if (!(lvlbase_pk_str in expanded_depbase_dict)){
                                expanded_depbase_dict[lvlbase_pk_str] = {expanded: false};
                            };
                            const expanded_lvlbase_dict = expanded_depbase_dict[lvlbase_pk_str];
                            if (tblName === "level"){
                                expanded_lvlbase_dict.expanded = !expanded_lvlbase_dict.expanded;
                            };
                        };
                    };
                };
            };

        console.log("  **********  mod_MUPS_dict.expanded", mod_MUPS_dict.expanded);
            MUPS_FillSelectTable();
        };
    };  // MUPS_ExpandTblrows

    function MUPS_ExpandCollapse_all(){
     // PR2022-11-06
        //console.log("===== MUPS_ExpandCollapse_all ===== ");
        //console.log("    mod_MUPS_dict.allowed_sections", mod_MUPS_dict.allowed_sections);

        const is_expand = !mod_MUPS_dict.expand_all;
        mod_MUPS_dict.expand_all = is_expand;
        // remove all expanded items when setting 'Collapse_all'
        if (!is_expand){
            mod_MUPS_dict.expanded = {};
        };

        el_MUPS_btn_expand_all.innerText = (is_expand) ? loc.Collapse_all : loc.Expand_all;

// ---  loop through mod_MUPS_dict.allowed_sections and create mod_MUPS_dict.expanded with all items expanded
        for (const [schoolbase_pk_str, allowed_schoolbase] of Object.entries(mod_MUPS_dict.allowed_sections)) {

            if (!(schoolbase_pk_str in mod_MUPS_dict.expanded)){
                mod_MUPS_dict.expanded[schoolbase_pk_str] = {};
            }
            const expanded_schoolbase = mod_MUPS_dict.expanded[schoolbase_pk_str];
            expanded_schoolbase.expanded = is_expand;

            for (const [depbase_pk_str, allowed_depbase] of Object.entries(allowed_schoolbase)) {
                if (!(depbase_pk_str in expanded_schoolbase)){
                    expanded_schoolbase[depbase_pk_str] = {};
                }
                const expanded_depbase = expanded_schoolbase[depbase_pk_str];
                expanded_depbase.expanded = is_expand;

                for (const [lvlbase_pk_str, allowed_lvlbases] of Object.entries(allowed_depbase)) {
                    if (!(lvlbase_pk_str in expanded_depbase)){
                        expanded_depbase[lvlbase_pk_str] = {};
                    }
                    const expanded_lvlbase = expanded_depbase[lvlbase_pk_str];
                    expanded_lvlbase.expanded = is_expand;
                };
            };
        };
    //console.log("     mod_MUPS_dict.expanded", mod_MUPS_dict.expanded);

        MUPS_FillSelectTable();
    };  // MUPS_ExpandCollapse_all

/////////////////////

// +++++++++ END OF MOD USER PERMIT SECTIONS ++++++++++++++++ PR20220-10-23


// +++++++++ MOD UPLOAD PERMITS ++++++++++++++++ PR2021-04-20
    function MUP_Open(){
        //console.log(" -----  MUP_Open   ----")

    // ---  show modal
        $("#id_mod_upload_permits").modal({backdrop: true});
   } //  MUP_Open
// +++++++++ END MOD UPLOAD PERMITS ++++++++++++++++++++++++++++++++++++++++++++++++++++

// +++++++++ MOD GROUP PERMIT ++++++++++++++++ PR2021-03-19
    function MUPM_Open(mode, el_input){
        console.log(" -----  MUPM_Open   ---- mode: ", mode)  // modes are: addnew, update
        // mode = 'addnew' when called by SubmenuButton
        // mode = 'update' when called by tblRow event

        const is_addnew = (mode === "addnew");
        mod_MUPM_dict = {is_addnew: (is_addnew) ? "create" : "update" };
        mod_MUPM_dict = {mode: mode};

        let userpermit_pk = null, role = null, permit_page = null, permit_action = null, permit_sequence = null;
        if(el_input){
            const tblRow = t_get_tablerow_selected(el_input);
            const data_dict = get_datadict_from_tblRow(tblRow);
        console.log("data_dict", data_dict)
            if(!isEmpty(data_dict)){
                userpermit_pk = data_dict.id;
                role = data_dict.role;
                permit_page = data_dict.page;
                permit_action = data_dict.action;
                permit_sequence = data_dict.sequence;
            }
        }
        mod_MUPM_dict.userpermit_pk = userpermit_pk;
        if (el_MUPM_page) {el_MUPM_page.value = permit_page};
        if (el_MUPM_role) {el_MUPM_role.value = role};
        if (el_MUPM_action) {el_MUPM_action.value = permit_action};

    // ---  show modal
        $("#id_mod_userpermit").modal({backdrop: true});
    };  // MUPM_Open

    function MUPM_Save(mode){ //PR2021-03-20
        //console.log("=== MUPM_Save === ");
        //  mode = 'save', 'delete'
        const upload_mode = (mode === "delete") ? "delete" :
                            (mod_MUPM_dict.mode === "addnew") ? "create" : "update";

        //const sequence_value = true; //document.getElementById("id_MUPM_sequence").value;
        //const permit_sequence_int = 0; //(Number(sequence_value)) ? Number(sequence_value) : 1;

// ---  create mod_dict
        const url_str = urls.url_userpermit_upload;
        const upload_dict = {mode: upload_mode,
                            userpermit_pk: mod_MUPM_dict.userpermit_pk,
                            role: (el_MUPM_role && el_MUPM_role.value) ? el_MUPM_role.value : null,
                            page: (el_MUPM_page && el_MUPM_page.value) ? el_MUPM_page.value : null,
                            action: (el_MUPM_action && el_MUPM_action.value) ? el_MUPM_action.value : null,
                            sequence: 0
                            };
        //console.log("upload_dict: ", upload_dict);

        const parameters = {"upload": JSON.stringify (upload_dict)}
        let response = "";
        $.ajax({
            type: "POST",
            url: url_str,
            data: parameters,
            dataType:'json',
            success: function (response) {
                console.log( "response");
                console.log( response);

                // hide loader
                el_MUA_loader.classList.add(cls_hide);

                if ("updated_permit_rows" in response){
                    RefreshDataRows("userpermit", response.updated_permit_rows, permit_dicts, true)  // true = is_update
                };

            },  // success: function (response) {
            error: function (xhr, msg) {
                console.log(msg + '\n' + xhr.responseText);
            }  // error: function (xhr, msg) {
        });  // $.ajax({

        $("#id_mod_userpermit").modal("hide");
    }  // MUPM_Save

//========= MUPM_FillSelectTableDepartment  ============= PR2020--09-30
    function MUPM_FillSelectTableDepartment() {
        //console.log("===== MUPM_FillSelectTableDepartment ===== ");
        //console.log("department_map", department_map);

        const data_map = department_map;
        const tblBody_select = document.getElementById("id_MUPM_tbody_select");
        tblBody_select.innerText = null;

// ---  loop through data_map
        let row_count = 0
        if(data_map.size > 1) {
            MUPM_FillSelectRow(tblBody_select, {}, "<" + loc.All_departments + ">");
        }
        for (const [map_id, dict] of data_map.entries()) {
            MUPM_FillSelectRow(tblBody_select, dict);
        }

    } // MUPM_FillSelectTableDepartment

//========= MUPM_FillSelectRow  ============= PR2020--09-30
    function MUPM_FillSelectRow(tblBody_select, dict, select_all_text) {
        //console.log("===== MUPM_FillSelectRowDepartment ===== ");
        // add_select_all when not isEmpty(dict)
        //console.log("dict", dict);
        let pk_int = null, map_id = null, abbrev = null
        if (isEmpty(dict)){
            pk_int = 0;
            map_id = "sel_depbase_selectall";
            abbrev = select_all_text
        } else {
            pk_int = dict.base_id;
            map_id = "sel_depbase_" + dict.base_id;
            abbrev = (dict.abbrev) ? dict.base_code : "";
        };
        // check if this dep is in mod_MUPM_dict.depbases. Set tickmark if yes
        let selected_int = 0;
        if(mod_MUPM_dict.depbases){
            const arr = mod_MUPM_dict.depbases.split(";");
            arr.forEach((obj, i) => {
                 if (pk_int === Number(obj)) { selected_int = 1}
             });
        }
        const tickmark_class = (selected_int === 1) ? "tickmark_2_2" : "tickmark_0_0";

        const tblRow = tblBody_select.insertRow(-1);
        tblRow.id = map_id;
        tblRow.setAttribute("data-pk", pk_int);
        tblRow.setAttribute("data-selected", selected_int);

// --- add first td to tblRow.
        let td = tblRow.insertCell(-1);
        let el_div = document.createElement("div");
            el_div.classList.add("tw_032", tickmark_class)
              td.appendChild(el_div);

// --- add second td to tblRow.
        td = tblRow.insertCell(-1);
        el_div = document.createElement("div");
            el_div.classList.add("tw_150")
            el_div.innerText = abbrev;
            td.appendChild(el_div);

        td.classList.add("tw_200", "px-2", "pointer_show") // , cls_bc_transparent)

//--------- add addEventListener
        tblRow.addEventListener("click", function() {MUPM_SelectDepartment(tblRow)}, false);
    } // MUPM_FillSelectRow

//========= MUPM_SelectDepartment  ============= PR2020-10-01
    function MUPM_SelectDepartment(tblRow){
        //console.log( "===== MUPM_SelectDepartment  ========= ");
        //console.log( "event_key", event_key);

        if(tblRow){
            let is_selected = (!!get_attr_from_el_int(tblRow, "data-selected"));
            let pk_int = get_attr_from_el_int(tblRow, "data-pk");
            const is_select_all = (!pk_int);
        //console.log( "is_selected", is_selected);
        //console.log( "pk_int", pk_int);
// ---  toggle is_selected
            is_selected = !is_selected;

            const tblBody_selectTable = tblRow.parentNode;
            if(is_select_all){
// ---  if is_select_all: select/ deselect all rows
                for (let i = 0, row, el, set_tickmark; row = tblBody_selectTable.rows[i]; i++) {
                    MUPM_set_selected(row, is_selected)
                }
            } else {
// ---  put new value in this tblRow, show/hide tickmark
                MUPM_set_selected(tblRow, is_selected)

// ---  select row 'select_all' if all other rows are selected, deselect otherwise
                // set 'select_all' true when all other rows are clicked
                let has_rows = false, unselected_rows_found = false;
                for (let i = 0, row; row = tblBody_selectTable.rows[i]; i++) {
                    let row_pk = get_attr_from_el_int(row, "data-pk");
                    // skip row 'select_all'
                    if(row_pk){
                        has_rows = true;
                        if(!get_attr_from_el_int(row, "data-selected")){
                            unselected_rows_found = true;
                            break;
                        }
                    }
                }
// ---  set tickmark in row 'select_all'when has_rows and no unselected_rows_found
                const tblRow_selectall = document.getElementById("sel_depbase_selectall")
                MUPM_set_selected(tblRow_selectall, (has_rows && !unselected_rows_found))
            }
// check for double abbrev in deps
            const fldName = "abbrev";
            const msg_err = validate_duplicates_in_department(loc, "school", fldName, loc.Abbreviation, mod_MUPM_dict.mapid, mod_MUPM_dict.abbrev)
            const el_msg = document.getElementById("id_MUPM_msg_" + fldName);
            el_msg.innerText = msg_err;
            add_or_remove_class(el_msg, cls_hide, !msg_err)

            el_MUPM_btn_save.disabled = (!!msg_err);
        }
    }  // MUPM_SelectDepartment

//========= MUPM_set_selected  ============= PR2020-10-01
    function MUPM_set_selected(tblRow, is_selected){
        //console.log( "  ---  MUPM_set_selected  --- ", is_selected);
// ---  put new value in tblRow, show/hide tickmark
        if(tblRow){
            tblRow.setAttribute("data-selected", ( (is_selected) ? 1 : 0) )
            const img_class = (is_selected) ? "tickmark_2_2" : "tickmark_0_0"
            const el = tblRow.cells[0].children[0];
            //if (el){add_or_remove_class(el, "tickmark_2_2", is_selected , "tickmark_0_0")}
            if (el){el.className = img_class}
        }
    }  // MUPM_set_selected

//========= MUPM_get_selected_depbases  ============= PR2020-10-07
    function MUPM_get_selected_depbases(){
        //console.log( "  ---  MUPM_get_selected_depbases  --- ")
        const tblBody_select = document.getElementById("id_MUPM_tbody_select");
        let dep_list_arr = [];
        for (let i = 0, row; row = tblBody_select.rows[i]; i++) {
            let row_pk = get_attr_from_el_int(row, "data-pk");
            // skip row 'select_all'
            if(row_pk){
                if(!!get_attr_from_el_int(row, "data-selected")){
                    dep_list_arr.push(row_pk);
                }
            }
        }
        dep_list_arr.sort((a, b) => a - b);
        const dep_list_str = dep_list_arr.join(";");
        //console.log( "dep_list_str", dep_list_str)
        return dep_list_str;
    }  // MUPM_get_selected_depbases


// +++++++++++++++++ MODAL SELECT MULTIPLE CLUSTERS ++++++++++++++++++++++++++++++++++++++++++
//========= MSM_Open ====================================  PR2022-01-26 PR2023-01-26
    function MSM_Open (el_input) {
        console.log(" ===  MSM_Open  =====") ;

        b_clear_dict(mod_MSM_dict)

        const has_permit = (permit_dict.permit_crud && permit_dict.requsr_same_school);

        const tblRow = t_get_tablerow_selected(el_input);
        const data_dict = user_dicts[tblRow.id];
    console.log("    data_dict", data_dict)

        if(data_dict && has_permit){

// --- get existing data_dict from data_rows
            // fldName = allowed_clusters

            mod_MSM_dict.user_pk = data_dict.id;
            mod_MSM_dict.schoolbase_pk = data_dict.schoolbase_id;
            mod_MSM_dict.mapid = data_dict.mapid;

            // allowed_clusters = ""ac - 4A1, ac - 4VA1, ac - 4VA2,"
            mod_MSM_dict.allowed_clusters = data_dict.allowed_clusters;
            mod_MSM_dict.allowed_clusters_pk_arr = data_dict.allowed_clusters_pk;

    // ---  set header text
            const header_text = loc.Select + loc.Clusters.toLowerCase() + ":";
            document.getElementById("id_MSM_hdr_multiple").innerText = header_text;

            const hide_msg = (get_attr_from_el(el_input, "data-field") === "allowed_clusters");

            add_or_remove_class_by_id ("id_MSM_message_container", cls_hide, hide_msg);

            el_MSM_input.value = null;

    // ---  fill select table 'customer'
            MSM_FillSelectTable();

    // ---  Set focus to el_MSM_input
            //Timeout function necessary, otherwise focus wont work because of fade(300)
            setTimeout(function (){ el_MSM_input.focus() }, 50);
    // ---  show modal
             $("#id_mod_select_multiple").modal({backdrop: true});
        }
    }; // MSM_Open

//=========  MSM_Save  ================ PR2022-01-26 PR2023-01-27
    function MSM_Save() {
        console.log("===  MSM_Save =========");

        const has_permit = permit_dict.permit_crud_sameschool;

        if(has_permit){

            let new_array = [];
            let allowed_str = ""
            const tblBody_select = el_MSM_tblbody_select;
            for (let i = 0, row; row = tblBody_select.rows[i]; i++) {
                const base_pk_int = get_attr_from_el_int(row, "data-pk")
                if(base_pk_int > 0) {
                    const is_selected = (!!get_attr_from_el_int(row, "data-selected"))
                    if(is_selected){
                        new_array.push(base_pk_int);

                    };
                }
            }
            if(new_array){
                // PR2020-11-02 from https://www.w3schools.com/js/js_array_sort.asp
                new_array.sort(function(a, b){return a - b});
            };

    // ---  upload changes
            // mod_MSM_dict = user_data_dict with additional keys
            const upload_dict = { user_pk: mod_MSM_dict.user_pk,
                                    schoolbase_pk: mod_MSM_dict.schoolbase_pk,
                                    mapid: mod_MSM_dict.mapid,
                                    mode: "update",
                                    allowed_clusters: (new_array.length) ? new_array : null };

            UploadChanges(upload_dict, urls.url_user_upload);
        };
// hide modal
        $("#id_mod_select_multiple").modal("hide");
    }  // MSM_Save

//=========  MSM_InputKeyup  ================ PR2020-11-02
    function MSM_InputKeyup(el_input) {
        //console.log( "=== MSM_InputKeyup === ")
        //console.log( "el_input.value:  ", el_input.value)

        let tblBody_select = el_MSM_tblbody_select;

        const new_filter = el_input.value
        if (tblBody_select.rows.length){
// ---  filter select rows
            const col_index_list = [1];
            t_Filter_SelectRows(tblBody_select, new_filter, false, false, null, col_index_list);
        }
    }  // MSM_InputKeyup

//=========  MSM_FillSelectTable  ================ PR2022-01-26 PR23-01-26
    function MSM_FillSelectTable() {
        console.log( "===== MSM_FillSelectTable ========= ");

        // check if school has multiple departments, needed for allowed_clusters
        let school_has_multiple_deps = false;
        if (setting_dict.sel_school_depbases ){
            const depbase_arr = setting_dict.sel_school_depbases.split(";");
            school_has_multiple_deps = depbase_arr && depbase_arr.length > 1;
        };
        console.log( "    setting_dict.sel_school_depbases: ", setting_dict.sel_school_depbases);
        console.log( "    school_has_multiple_deps: ", school_has_multiple_deps);

        // cluster has no base table
        const base_pk_field = "id"
        const caption_none = loc.No_ + loc.Clusters.toLowerCase();

        let tblBody_select = el_MSM_tblbody_select;
        tblBody_select.innerText = null;

        let has_selected_rows = false;

// --- loop through data_rows
        // data_array contains a list of strings with cluster_id's
        console.log( "    mod_MSM_dict.allowed_clusters: ", mod_MSM_dict.allowed_clusters);
        const allowed_clusters_pk_arr = (mod_MSM_dict.allowed_clusters_pk_arr) ? mod_MSM_dict.allowed_clusters_pk_arr : [];

        console.log( "    allowed_clusters_pk_arr: ", allowed_clusters_pk_arr);

        for (const data_dict of Object.values(cluster_dictsNEW)) {
    console.log( "    data_dict: ", data_dict)
            const pk_int = data_dict.id;
            const row_is_selected = (pk_int && allowed_clusters_pk_arr && allowed_clusters_pk_arr.includes(pk_int));

    console.log( "    pk_int: ", pk_int);
    console.log( "   ==== row_is_selected: ", row_is_selected);
            if(row_is_selected){
                has_selected_rows = true;
            };

            const row_index = -1;
            MSM_FillSelectRow(tblBody_select, data_dict, row_is_selected);
        };

    console.log( "  >>>>>>>>>>   has_selected_rows: ", has_selected_rows);

// ---  add 'all' at the beginning of the list, with id = 0, make selected if no other rows are selected
        const data_dict = {};
        data_dict.id = -9;
        data_dict.name = "<" + loc.All_ + loc.Clusters.toLowerCase() + ">"

        const row_index = 0;
        // select <All> when has_selected_rows = false;
        MSM_FillSelectRow(tblBody_select, data_dict, !has_selected_rows, true)  // true = insert_at_index_zero

    }  // MSM_FillSelectTable

//=========  MSM_FillSelectRow  ================ PR2022-01-26
    function MSM_FillSelectRow(tblBody_select, data_dict, row_is_selected, insert_at_index_zero) {
        //console.log( "===== MSM_FillSelectRow ========= ");
        //console.log("data_dict: ", data_dict);

        // cluster has no base table
        const pk_int = data_dict.id;
        const display_name = (data_dict.name) ? data_dict.name : "-";

    //console.log( "display_name: ", display_name);

        const map_id = (data_dict.mapid) ? data_dict.mapid : null;

// ---  lookup index where this row must be inserted
        const ob1 = (data_dict.dep_sequence) ? "00000" + data_dict.dep_sequence.toString() : "";
        const ob2 = (data_dict.name) ? data_dict.name.toLowerCase() : "";

        const row_index = (insert_at_index_zero) ? 0 :
            b_recursive_tblRow_lookup(tblBody_select, setting_dict.user_lang, ob1, ob2);

// --- insert tblRow into tblBody at row_index
        const tblRow = tblBody_select.insertRow(row_index);
        tblRow.id = map_id;

        tblRow.setAttribute("data-pk", pk_int);
        tblRow.setAttribute("data-selected", (row_is_selected) ? "1" : "0")

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);
        tblRow.setAttribute("data-ob2", ob2);
// ---  add EventListener to tblRow, not when 'no items' (pk_int is then -1, ''all clusters = -9
        if (pk_int !== -1) {
            tblRow.addEventListener("click", function() {MSM_SelecttableClicked(tblRow)}, false )
// ---  add hover to tblRow
            add_hover(tblRow);
        }
        let td, el;

// ---  add select td to tblRow.
        td = tblRow.insertCell(-1);
            td.classList.add("mx-1", "tw_032")

// --- add a element to td., necessary to get same structure as item_table, used for filtering
            el = document.createElement("div");
                el.className = (row_is_selected) ? "tickmark_2_2" : "tickmark_0_0";
            td.appendChild(el);

// ---  add td with display_name to tblRow
        td = tblRow.insertCell(-1);
            td.classList.add("mx-1", "tw_270")
// --- add a element to td., necessary to get same structure as item_table, used for filtering
        el = document.createElement("div");
            el.innerText = display_name;
        td.appendChild(el);
        if (display_name) { tblRow.title = display_name};

    };  // MSM_FillSelectRow

//=========  MSM_SelecttableClicked  ================ PR2022-01-26
    function MSM_SelecttableClicked(tblRow) {
        //console.log( "===== MSM_SelecttableClicked ========= ");
        //console.log("tblRow: ", tblRow);
        if(tblRow) {
            // toggle is_selected
            const is_selected = (!get_attr_from_el_int(tblRow, "data-selected"))

            tblRow.setAttribute("data-selected", (is_selected) ? "1" : "0")
            tblRow.cells[0].children[0].className = (is_selected) ? "tickmark_2_2" : "tickmark_0_0";

            // row 'all' has pk = -9
            if(is_selected){
                const selected_pk_int = get_attr_from_el_int(tblRow, "data-pk");
                const selected_is_all = (selected_pk_int === -9);
                const tblBody_select = tblRow.parentNode;
                for (let i = 0, lookup_row; lookup_row = tblBody_select.rows[i]; i++) {
                    const lookup_pk_int = get_attr_from_el_int(lookup_row, "data-pk");
                    if (lookup_pk_int !== selected_pk_int){
                        const lookup_is_all = (lookup_pk_int === -9);

                        // remove tickmark on all other items when 'all' is selected
                        // remove  tickmark on 'all' when other item is selected
                        //let remove_selected = (base_is_all) ? (lookup_base_pk_int !== -9) : (lookup_base_pk_int === -9);;
                        let remove_selected = (selected_is_all && !lookup_is_all) || (!selected_is_all && lookup_is_all);
                        if(remove_selected){
                            lookup_row.setAttribute("data-selected", "0");
                            lookup_row.cells[0].children[0].className = "tickmark_0_0";
                        };
                    };
                };
            };
        };
    };  // MSM_SelecttableClicked

// +++++++++++++++++ END OF MODAL SELECT MULTIPLE DEPS / LEVELS/ SUBJECTS / CLUSTERS  +++++++++++++++++++++++++++++++

//////////////////////////////////////

//========= HandleInputChange  =============== PR2021-03-20 PR2022-02-21 PR2023-05-24
    function HandleInputChange(el_input){
        console.log(" --- HandleInputChange ---")

        const tblRow = t_get_tablerow_selected(el_input);
        const data_dict = get_datadict_from_tblRow(tblRow);

        if (data_dict){
            const fldName = get_attr_from_el(el_input, "data-field");
            const userpermit_pk = data_dict.id;
            const map_value = data_dict[fldName];
            let new_value = el_input.value;
            if(fldName === "sequence"){
                 new_value = (Number(new_value)) ? Number(new_value) : 1;
            };

            if(new_value !== map_value){
        // ---  create mod_dict
                const url_str = urls.url_userpermit_upload;
                const upload_dict = {mode: "update",
                                    userpermit_pk: userpermit_pk};
                upload_dict[fldName] = new_value;

        // ---  upload changes
                UploadChanges(upload_dict, url_str);
            };
        };
    };  // HandleInputChange

// +++++++++++++++++ MODAL CONFIRM +++++++++++++++++++++++++++++++++++++++++++

//=========  ModConfirmOpen_AddFromPreviousExamyears  ================ PR2023-04-1
    function ModConfirmOpen_AddFromPreviousExamyears() {
        //console.log(" -----  ModConfirmOpen_AddFromPreviousExamyears   ----")

        mod_dict = {mode: "add_from_prev_examyears"};
        mod_dict.user_pk_list = [];
        if(permit_dict.permit_crud_sameschool){

    // ---  loop through tblBody.rows and fill user_pk_list, only users of other years
            for (let i = 0, tblRow; tblRow = tblBody_datatable.rows[i]; i++) {
                if (tblRow.classList.contains(cls_selected)) {
                    const data_dict = user_dicts[tblRow.id];
                    if (data_dict){
                        if (data_dict.ey_other){
                            mod_dict.user_pk_list.push(data_dict.id);
                        };
                    };
                };
            };
            mod_dict.user_pk_count = (mod_dict.user_pk_list) ? mod_dict.user_pk_list.length : 0;

            const header_txt = loc.Add_users_from_prev_year;
            el_confirm_header.innerText = header_txt

            el_confirm_btn_save.innerText = loc.OK;
            add_or_remove_class (el_confirm_btn_save, cls_hide, !mod_dict.user_pk_count);

            el_confirm_btn_cancel.innerText = (mod_dict.user_pk_count) ? loc.Cancel : loc.Close ;

            const msg_list = ["<p>"];
            if (!mod_dict.user_pk_count){
                msg_list.push(...[loc.There_are_no_users_of_prev_ey, "</p><p class='pt-2'>",
                                    loc.Click_show_all_users, loc.to_show_users_of_prev_years,"</p>"]);
            } else {
                 if (mod_dict.user_pk_count === 1){
                    const data_dict = user_dicts["user_" + mod_dict.user_pk_list[0]]
                    if (data_dict){
                        msg_list.push(...[loc.User, " '", data_dict.last_name, "' "]);
                    } else {
                        msg_list.push(...[loc.There_is_1_user_selected, "</p><p>", loc.That_user])
                    };
                    msg_list.push(loc.willbe_added_to_this_examyear_sing);
                } else {
                    msg_list.push(...["<p>", loc.There_are, mod_dict.user_pk_count, loc.users_of_prev_years_selected, "</p><p>",
                                   loc.Those_users, loc.willbe_added_to_this_examyear_plur]);
                };
                msg_list.push(...["</p><p class='pt-2'>",  loc.Do_you_want_to_continue + "</p>"]);
            };
            el_confirm_msg_container.innerHTML = msg_list.join("");

            $("#id_mod_confirm").modal({backdrop: true});
        };
    };

//=========  ModConfirmOpen_DownloadUserdata  ================ PR2023-01-31
    function ModConfirmOpen_DownloadUserdata(mode ) {
        console.log(" -----  ModConfirmOpen_DownloadUserdata   ----")

// variables for future use in other functions
        console.log("    mode", mode);
        const may_edit = true;
        const show_modal = true;
        const show_large_modal = true;

// ---  create mod_dict
        mod_dict = {mode: mode};

 // ---  put text in modal for
        let header_txt = "";
        const msg_list = [];
        let caption_save = loc.OK;
        let hide_save_btn = false;

        header_txt = loc.Download_user_data;
        caption_save = loc.Yes_download;
        msg_list.push("<p>" + loc.The_user_data + loc.will_be_downloaded_plur + "</p><p>");
        msg_list.push("<p>" +  loc.Do_you_want_to_continue + "</p>");

        el_confirm_header.innerText = header_txt;
        el_confirm_loader.classList.add(cls_visible_hide);
        el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");

        el_confirm_msg_container.innerHTML = msg_list.join("");

        el_confirm_btn_save.innerText = caption_save;
        add_or_remove_class (el_confirm_btn_save, cls_hide, hide_save_btn);

        //add_or_remove_class (el_confirm_btn_save, "btn-primary", (mode !== "delete"));
        add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", (mode === "delete_candidate"), "btn-primary");

        el_confirm_btn_cancel.innerText = (hide_save_btn) ? loc.Close : loc.No_cancel;

// set focus to cancel button
        set_focus_on_el_with_timeout(el_confirm_btn_cancel, 150);

// show modal
        if (show_modal) {
            $("#id_mod_confirm").modal({backdrop: true});

            // this code must come after $("#id_mod_confirm"), otherwise it will not work
            add_or_remove_class(document.getElementById("id_mod_confirm_size"), "modal-md", show_large_modal, "modal-md");
        };
    };  // ModConfirmOpen_DownloadUserdata

//=========  ModConfirmOpen  ================ PR2020-08-03 PR2021-06-30 PR2022-12-31 PR2023-04-11
    function ModConfirmOpen(tblName, mode, el_input, user_without_userallowed) {
        console.log(" -----  ModConfirmOpen   ----")
        // values of mode are : "delete", "is_active" or "send_activation_email", "permission_admin", "user_without_userallowed"
        // "add_from_prev_yr"
        // ModConfirmOpen(null, "user_without_userallowed", null, response.user_without_userallowed);
        console.log("    mode", mode )
        console.log("    tblName", tblName )
        console.log("    el_input", el_input )

// ---  get selected_pk
        let selected_pk = null;
        // tblRow is undefined when clicked on delete btn in submenu btn or form (no inactive btn)
        const tblRow = t_get_tablerow_selected(el_input);
        const data_dict = (tblRow) ? get_datadict_from_tblRow(tblRow) : selected.data_dict;
        const user_name = (data_dict && data_dict.username) ? data_dict.username  : "-";
    console.log("   tblRow", tblRow);
    console.log("   data_dict", data_dict);

// ---  get info from data_dict
        // TODO remove requsr_pk from client
        const is_request_user = (data_dict && permit_dict.requsr_pk && permit_dict.requsr_pk === data_dict.id)
        console.log("    is_request_user", is_request_user)

// ---  create mod_dict
        mod_dict = {mode: mode, table: tblName};
        const has_selected_item = (!isEmpty(data_dict));
        if(has_selected_item){
            mod_dict.mapid = data_dict.mapid;
            if (tblName === "userpermit"){
                mod_dict.userpermit_pk = data_dict.id
            } else {
                mod_dict.user_pk = data_dict.id;
                mod_dict.user_ppk = data_dict.schoolbase_id;
            }
        };
        if (mode === "is_active") {
            mod_dict.current_isactive = data_dict.is_active;
        } else if (mode === "user_without_userallowed") {
            if (!isEmpty(user_without_userallowed)) {
                mod_dict.user_pk = user_without_userallowed.user_pk;
                mod_dict.schoolbase_pk = user_without_userallowed.schoolbase_pk;
                mod_dict.username = user_without_userallowed.username;
                mod_dict.last_name = user_without_userallowed.last_name;
            };
        };
       console.log("    mod_dict", mod_dict);

// ---  put text in modal form
        let dont_show_modal = false;
        const is_mode_permission_admin = (mode === "permission_admin");
        const is_mode_send_activation_email = (mode === "send_activation_email");

        const inactive_txt = (mod_dict.current_isactive) ? loc.Make_user_inactive : loc.Make_user_active;
        const header_text = (mode === "delete") ? (tblName === "userpermit") ? loc.Delete_permission : loc.Delete_user :
                            (mode === "is_active") ? inactive_txt :
                            (mode === "user_without_userallowed") ? loc.Add_user :
                            (is_mode_send_activation_email) ? loc.Send_activation_email :
                            (is_mode_permission_admin) ? loc.Set_permissions : "";

        let msg_list = [];
        let hide_save_btn = false;
        if(mode === "user_without_userallowed"){
            // PR2023-01-01 from https://stackoverflow.com/questions/4842993/javascript-push-an-entire-list
            // use push.apply instead of joining the list before pushing
            msg_list.push(["<p>", loc.Username, " '", mod_dict.username,  "' ", loc._of_, loc.User.toLowerCase()," '" , mod_dict.last_name, "'</p>"].join(""));
            msg_list.push(["<p>", loc.already_exists_in_previous_examyear, "</p>"].join(""));

            msg_list.push(["<p class='mt-3'>", loc.Doyou_wantto_add_to_this_examyear, "</p>"].join(""));
        } else if (!has_selected_item){
            msg_list.push("<p>" + loc.No_user_selected + "</p>");
            hide_save_btn = true;

        } else if (tblName === "userpermit"){
            const action = (data_dict.action) ? data_dict.action  : "-";
            const page = (data_dict.page) ? data_dict.page  : "-";
            msg_list.push(["<p>", loc.Action, " '", action, "'", loc.on_page, "'",page, "'", loc.will_be_deleted, "</p>"].join(""));
            msg_list.push("<p>" + loc.Do_you_want_to_continue + "</p>");

        } else if(mode === "delete"){
            if(is_request_user){
                msg_list.push("<p>" + loc.Sysadm_cannot_delete_own_account + "</p>");
                hide_save_btn = true;
            } else {
                msg_list.push(["<p>", loc.User + " '" + user_name + "'", loc.will_be_deleted, "</p>"].join(""));
                msg_list.push("<p>" + loc.Do_you_want_to_continue + "</p>");
            }

        } else if(mode === "is_active"){
            if(is_request_user && mod_dict.current_isactive){
                msg_list.push("<p>" + loc.Sysadm_cannot_set_inactive + "</p>");
                hide_save_btn = true;
            } else {
                const inactive_txt = (mod_dict.current_isactive) ? loc.will_be_made_inactive : loc.will_be_made_active
                msg_list.push(["<p>", loc.User + " '" + user_name + "'", inactive_txt, "</p>"].join(""));
                msg_list.push("<p>" + loc.Do_you_want_to_continue + "</p>");
            }

        } else if(is_mode_permission_admin){
            hide_save_btn = true;
            const fldName = get_attr_from_el(el_input, "data-field")
            if (fldName === "group_admin") {
                msg_list.push("<p>" + loc.Sysadm_cannot_remove_sysadm_perm + "</p>");
            };

        } else if (is_mode_send_activation_email) {
            const is_expired = activationlink_is_expired(data_dict.activationlink_sent);
            dont_show_modal = (data_dict.activated);
            if(!dont_show_modal){
                mod_dict.user_pk_list = [];
        // ---  loop through tblBody.rows and fill user_pk_list, only users of other years
                for (let i = 0, tr; tr = tblBody_datatable.rows[i]; i++) {
                    if (tr.classList.contains(cls_selected) ) {
                        const tr_dict = user_dicts[tr.id];
                        if (tr_dict){
                            if (!tr_dict.activated){
                                mod_dict.user_pk_list.push(tr_dict.id);
                            };
                        };
                    };
                };
                // tr_clicked is not yet selected when clicked on icon, add data_dict.id to user_pk_list
                if (data_dict && !mod_dict.user_pk_list.includes(data_dict.id)){
                    mod_dict.user_pk_list.push(data_dict.id);
                };
                mod_dict.user_pk_count = (mod_dict.user_pk_list) ? mod_dict.user_pk_list.length : 0;

                msg_list = ["<p>"];
                if (!mod_dict.user_pk_count){
                    // this should not be possible, but let it stay
                    hide_save_btn = true
                    msg_list.push(...[loc.There_are_no, loc.users_selected_not_activated, "</p>"]);
                } else {
                     if (mod_dict.user_pk_count === 1){
                        if(is_expired) {msg_list.push("<p>" + loc.Activationlink_expired + "</p>");};
                        msg_list.push(...["<p>", loc.We_will_send_an_email_to, ":<br>&emsp;",loc.User, ":&emsp;&emsp;", user_name,
                        "<br>&emsp;", loc.Email_address, ":&emsp;", data_dict.email, "</p>"]);

                    } else {
                        msg_list.push(...["<p>", loc.There_are, mod_dict.user_pk_count, loc.users_selected_not_activated, "</p><p>",
                                       loc.We_will_send_an_email_to, " ", loc.Those_users.toLowerCase(), "."]);
                    };
                    msg_list.push(...["</p><p class='pt-2'>",  loc.Do_you_want_to_continue + "</p>"]);
                };
            };
        };

        if(!dont_show_modal){
            el_confirm_header.innerText = header_text;
            el_confirm_loader.classList.add(cls_visible_hide)
            el_confirm_msg_container.classList.remove("border_bg_invalid", "border_bg_valid");

            el_confirm_msg_container.innerHTML = (msg_list.length) ? msg_list.join("") : null;

            const caption_save = (mode === "delete") ? loc.Yes_delete :
                            (mode === "is_active") ? ( (mod_dict.current_isactive) ? loc.Yes_make_inactive : loc.Yes_make_active ) :
                            (is_mode_send_activation_email) ? loc.Yes_send_email : loc.OK;
            el_confirm_btn_save.innerText = caption_save;
            add_or_remove_class (el_confirm_btn_save, cls_hide, hide_save_btn);

            add_or_remove_class (el_confirm_btn_save, "btn-primary", (mode !== "delete"));
            add_or_remove_class (el_confirm_btn_save, "btn-outline-danger", (mode === "delete"));

            const caption_cancel = (mode === "delete") ? loc.No_cancel :
                            (mode === "is_active") ? loc.No_cancel :
                            (is_mode_send_activation_email) ? loc.No_cancel : loc.Cancel;

            el_confirm_btn_cancel.innerText = (!hide_save_btn && has_selected_item && !is_mode_permission_admin) ? caption_cancel : loc.Close;

    // set focus to cancel button
            set_focus_on_el_with_timeout(el_confirm_btn_cancel, 150);

// show modal
            $("#id_mod_confirm").modal({backdrop: true});
        };
    };  // ModConfirmOpen

//=========  ModConfirmSave  ================ PR2019-06-23 PR2023-04-12
    function ModConfirmSave() {
        console.log(" --- ModConfirmSave --- ");
        console.log("    mod_dict: ", mod_dict);
        let tblRow = document.getElementById(mod_dict.mapid);

// ---  when delete: make tblRow red, before uploading
        if (tblRow && mod_dict.mode === "delete"){
            ShowClassWithTimeout(tblRow, "tsa_tr_error");
        }

        let close_modal = false, skip_uploadchanges = false, url_str = null;
        const upload_dict = {
            mode: mod_dict.mode,
            mapid: mod_dict.mapid,
            user_pk: mod_dict.user_pk,
            schoolbase_pk: mod_dict.user_ppk
        };

        if (mod_dict.mode === "add_from_prev_examyears"){
            url_str = urls.url_user_upload_multiple;

            upload_dict.user_pk_list = mod_dict.user_pk_list;

            close_modal = true;

        } else if (mod_dict.mode === "user_without_userallowed"){
            url_str = urls.url_user_upload;

            upload_dict.user_pk = mod_dict.user_pk;
            upload_dict.schoolbase_pk = mod_dict.schoolbase_pk;
            upload_dict.username = mod_dict.username;
            upload_dict.schoolbase_pk

            close_modal = true;

        } else if(mod_dict.mode === "download_userdata_xlsx"){
            const el_modconfirm_link = document.getElementById("id_modconfirm_link");
            if (el_modconfirm_link) {
                const href_str = urls.url_download_userdata_xlsx;
                el_modconfirm_link.setAttribute("href", href_str);
                el_modconfirm_link.click();

                close_modal = true;
            };
            skip_uploadchanges = true;

        } else if(mod_dict.table === "userpermit"){
            if (mod_dict.mode === "delete"){
                url_str = urls.url_userpermit_upload;
                upload_dict.userpermit_pk = mod_dict.userpermit_pk;

                close_modal = true;
            }

        } else if( mod_dict.mode === "send_activation_email") {
            url_str = urls.url_user_upload_multiple;
            el_confirm_loader.classList.remove(cls_visible_hide);

            upload_dict.user_pk_list = mod_dict.user_pk_list;
            // TODO create msg when ok
            close_modal = true;

        } else if (mod_dict.mode === "update_usergroup_multiple"){
            url_str = urls.url_user_upload_multiple;
            el_confirm_loader.classList.remove(cls_visible_hide);

            upload_dict.user_pk_list = mod_dict.user_pk_list;
            upload_dict.usergroup = mod_dict.usergroup;
            upload_dict.permit_bool = mod_dict.permit_bool;

            // TODO create msg when ok
            close_modal = true;

        } else if( mod_dict.mode === "delete") {
            url_str = urls.url_user_upload;
            el_confirm_loader.classList.remove(cls_visible_hide);

        } else if (mod_dict.mode === "is_active") {
            url_str = urls.url_user_upload;
            mod_dict.new_isactive = !mod_dict.current_isactive;
            upload_dict.is_active = mod_dict.new_isactive;
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
                };
            };
        };

// ---  Upload changes
        if (!skip_uploadchanges){
            UploadChanges(upload_dict, url_str);
        };

// ---  hide modal
        if(close_modal) {
            $("#id_mod_confirm").modal("hide");
        };
    };  // ModConfirmSave

//=========  ModConfirmResponse  ================ PR2019-06-23
    function ModConfirmResponse(response) {
        //console.log(" --- ModConfirmResponse --- ");
        //console.log("mod_dict: ", mod_dict);
        // hide loader
        el_confirm_loader.classList.add(cls_visible_hide);
        const mode = get_dict_value(response, ["mode"]);
        if(mode === "delete"){
//--- delete tblRow. Multiple deleted rows not in use yet, may be added in the future PR2020-08-18
            if ("updated_list" in response) {
                for (let i = 0, updated_dict; updated_dict = response.updated_list[i]; i++) {
                    if(updated_dict.deleted) {
                        const tblRow = document.getElementById(updated_dict.mapid);
                        if (tblRow){ tblRow.parentNode.removeChild(tblRow) };
                    };
                };
            };
        };
        if ("msg_err" in response || "msg_ok" in response) {
            let msg_list = [];
            if ("msg_err" in response) {
                const msg_err = get_dict_value(response, ["msg_err", "msg01"]);
                if (msg_err) {msg_list.push("<p>" + msg_err + "</p>")};
                if (mod_dict.mode === "send_activation_email") {
                    msg_list.push("<p>" + loc.Activation_email_not_sent + "</p>")
                };
                el_confirm_msg_container.classList.add("border_bg_invalid");
            } else if ("msg_ok" in response){
                const msg01 = get_dict_value(response, ["msg_ok", "msg01"]);
                const msg02 = get_dict_value(response, ["msg_ok", "msg02"]);
                const msg03 = get_dict_value(response, ["msg_ok", "msg03"]);
                if (msg01) {msg_list.push("<p>" + msg01 + "</p>")};
                if (msg02) {msg_list.push("<p>" + msg02 + "</p>")};
                if (msg03) {msg_list.push("<p>" + msg03 + "</p>")};
                el_confirm_msg_container.classList.add("border_bg_valid");
            };

            const msg_html = (msg_list.length) ? msg_list.join("") : null;
            el_confirm_msg_container.innerHTML = msg_html;

            el_confirm_btn_cancel.innerText = loc.Close;
            el_confirm_btn_save.classList.add(cls_hide);
        } else {
        // hide mod_confirm when no message
            $("#id_mod_confirm").modal("hide");
        };
    };  // ModConfirmResponse

//###########################################################################

//=========  RefreshDataRowsAfterUpload  ================ PR2021-08-05
function RefreshDataRowsAfterUpload(response) {
    //console.log(" --- RefreshDataRowsAfterUpload  ---");
    //console.log("response:", response);
    const is_test = (!!response && !!response.is_test) ;
    if(!is_test && response && "updated_user_rows" in response) {
        RefreshDataRows("user", response.updated_user_rows, user_dicts, true)  // true = update
    }

}  // RefreshDataRowsAfterUpload


// +++++++++++++++++ REFRESH DATA ROWS ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  RefreshDataRows  ================ PR2021-08-01 PR2023-04-04
    function RefreshDataRows(page_tblName, update_rows, data_dicts, is_update) {
        console.log(" --- RefreshDataRows  ---");
        //console.log("page_tblName", page_tblName);
        //console.log("update_rows", update_rows);
        console.log("data_dicts", data_dicts);
        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length

        if (update_rows && update_rows.length ) {
            //const field_setting = field_settings[page_tblName];

            const field_setting = field_settings[selected_btn];
            //console.log("field_setting", field_setting);
            for (let i = 0, update_dict; update_dict = update_rows[i]; i++) {
                RefreshDatarowItem(page_tblName, field_setting, update_dict, data_dicts);
            }
        } else if (!is_update) {
            // empty the data_dicts when update_rows is empty PR2021-01-13 debug forgot to empty data_dicts
            // PR2021-03-13 debug. Don't empty de data_dicts when is update. Returns [] when no changes made
           b_clear_dict(data_dicts);
        }
    }  //  RefreshDataRows


//=========  RefreshDatarowItem  ================ PR2021-08-01
    function RefreshDatarowItem(page_tblName, field_setting, update_dict, data_dicts) {
        console.log(" --- RefreshDatarowItem  ---");
        console.log("    page_tblName", page_tblName);
        console.log("    update_dict", update_dict);
        //console.log("field_setting", field_setting);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);
            //console.log("is_created", is_created);

            // field_error_list is not in use (yet)
            let field_error_list = [];
            const error_list = get_dict_value(update_dict, ["error"], []);
    console.log("    error_list", error_list);

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

// NIU:
// ---  get list of hidden columns
            //const col_hidden = b_copy_array_to_new_noduplicates(mod_MCOL_dict.cols_hidden);

// ++++ created ++++
            // PR2021-06-16 from https://stackoverflow.com/questions/586182/how-to-insert-an-item-into-an-array-at-a-specific-index-javascript
            //arr.splice(index, 0, item); will insert item into arr at the specified index
            // (deleting 0 items first, that is, it's just an insert).

            if(is_created){
    // ---  first remove key 'created' from update_dict
                delete update_dict.created;

    // ---  add new item to data_dicts
                data_dicts[update_dict.mapid] = update_dict;

    // ---  create row in table., insert in alphabetical order
                const new_tblRow = CreateTblRow(page_tblName, field_setting, update_dict)

    // ---  scrollIntoView,
                if(new_tblRow){
                    new_tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' })

    // ---  make new row green for 2 seconds,
                    ShowOkElement(new_tblRow);
                }
            } else {

// --- get existing data_dict
                const map_id = update_dict.mapid;
                const data_dict = data_dicts[map_id];

                if(data_dict){
    // ++++ deleted ++++
                    if(is_deleted){
        console.log("   is_deleted", is_deleted);
            // delete row from data_dicts
                        delete data_dicts[map_id];
            //--- delete tblRow

                        const tblRow_tobe_deleted = document.getElementById(map_id);
        //console.log("tblRow_tobe_deleted", tblRow_tobe_deleted);
                        if (tblRow_tobe_deleted ){tblRow_tobe_deleted.parentNode.removeChild(tblRow_tobe_deleted)};

                    } else {

        console.log("   updated");
    // +++++++++++ updated row +++++++++++
        // ---  check which fields are updated, add to list 'updated_columns'
                        if(field_names){
                            let updated_columns = [];

                            // skip first column (is margin)
                            // col_field is the name of the column on page, not the db_field
                            for (let i = 1, col_field, old_value, new_value; col_field = field_names[i]; i++) {

                                let has_changed = false;
                                if (col_field.slice(0, 5) === "group") {
                                // data_dict.usergroups example: "anlz;auth1;auth2;auth3;auth4;edit;read"
                                    const usergroup = col_field.slice(6);
                                    // usergroup_in_data_dict and usergroup_in_update_dict are necessary to catch empty usergroup field
                                    const usergroup_in_data_dict = (!!data_dict.usergroups && data_dict.usergroups.includes(usergroup));
                                    const usergroup_in_update_dict = (!!update_dict.usergroups && update_dict.usergroups.includes(usergroup));
                                    has_changed = usergroup_in_data_dict != usergroup_in_update_dict;
                                } else {
                                    has_changed = (data_dict[col_field] !== update_dict[col_field] );
                                };

                                if (has_changed){
            // ---  add field to updated_columns list
                                    updated_columns.push(col_field)
                                };
                            };
    // ---  update fields in data_row
                            for (const [key, new_value] of Object.entries(update_dict)) {
                                if (key in data_dict){
                                    if (new_value !== data_dict[key]) {
                                        data_dict[key] = new_value;
                            }}};

            // ---  update field in tblRow
                            // note: when updated_columns is empty, then updated_columns is still true.
                            // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
                            if(updated_columns.length || field_error_list.length){

    // --- get existing tblRow
                                let tblRow = document.getElementById(data_dict.mapid);
                                if(tblRow){
                                    // to make it perfect: move row when username have changed
                                    if (updated_columns.includes("username")){
                                    //--- delete current tblRow
                                        tblRow.parentNode.removeChild(tblRow);
                                    //--- insert row new at new position
                                        tblRow = CreateTblRow(page_tblName, field_setting, update_dict)
                                    }

                    // loop through cells of row
                                    for (let i = 1, el_fldName, el, td; td = tblRow.cells[i]; i++) {
                                        el = td.children[0];
                                        if (el){
                                            el_fldName = get_attr_from_el(el, "data-field")
                                            UpdateField(el, update_dict);

                    // make field green when field name is in updated_columns
                                            if(updated_columns.includes(el_fldName)){
                                                ShowOkElement(el);
                                            };
                                        };
                                    };  //  for (let i = 1, el_fldName, el; el = tblRow.cells[i]; i++) {
                                };  // if(tblRow){
                            }; //  if(updated_columns.length){
                        };  //  if(!isEmpty(data_dict) && field_names){
                    };  // if(is_deleted){
                };
            };  // if(is_created)
        };  // if(!isEmpty(update_dict)){
    };  // RefreshDatarowItem

//###########################################################################
// +++++++++++++++++ FILTER ++++++++++++++++++++++++++++++++++++++++++++++++++
//========= HandleFilterSelect  =============== PR2023-04-11
    function HandleFilterSelect(el_input) {
        console.log( "===== HandleFilterSelect  ========= ");
        //console.log( "el_input", el_input);

    // - get current value of filter from filter_dict, set to '0' if filter doesn't exist yet
        const col_index = el_input.parentNode.cellIndex;
        const filter_array = (col_index in filter_dict) ? filter_dict[col_index] : [];
        const filter_value = (filter_array[1]) ? filter_array[1] : "0";

        const filter_tag = get_attr_from_el(el_input, "data-filtertag");
        const field_name = get_attr_from_el(el_input, "data-field");

    console.log( "filter_array", filter_array);
    console.log( "filter_value", field_name);
// - toggle filter value
            // default filter triple '0'; is show all, '1' is show tickmark, '2' is show without tickmark
        const new_value = (filter_value === "1") ? "0" : "1";
console.log( "new_value", new_value);
        el_input.innerHTML = (new_value === "1") ? "&#9658;" : null;   // "&#9658;" is black pointer right

// - put new filter value in filter_dict
        filter_dict[col_index] = [filter_tag, new_value]
    console.log( "filter_dict", filter_dict);

        // select or deselect all visible rows of tblrow
        // ---  loop through tblBody.rows
        for (let i = 0, tblRow, show_row; tblRow = tblBody_datatable.rows[i]; i++) {
            if (!tblRow.classList.contains("display_hide")){
                if (new_value === "1"){
                    t_tr_selected_set(tblRow);
                } else {
                    t_tr_selected_remove(tblRow);
                };
            };
        };
    };  // HandleFilterSelect



//========= HandleFilterKeyup  ================= PR2021-03-23
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
        };
    }; // function HandleFilterKeyup


//========= HandleFilterToggle  =============== PR2020-07-21 PR2020-09-14 PR2021-03-23 PR2022-02-28
    function HandleFilterToggle(el_input) {
        //console.log( "===== HandleFilterToggle  ========= ");

        // PR2021-05-30 debug: use cellIndex instead of attribute data-colindex,
        // because data-colindex goes wrong with hidden columns
        // was:  const col_index = get_attr_from_el(el_input, "data-colindex")
        const col_index = el_input.parentNode.cellIndex;
    //console.log( "col_index", col_index);

    // - get col_index and filter_tag from  el_input
        const filter_tag = get_attr_from_el(el_input, "data-filtertag")
        const field_name = get_attr_from_el(el_input, "data-field")
    //console.log( "filter_tag", filter_tag);
    //console.log( "field_name", field_name);

    // - get current value of filter from filter_dict, set to '0' if filter doesn't exist yet
        const filter_array = (col_index in filter_dict) ? filter_dict[col_index] : [];
        const filter_value = (filter_array[1]) ? filter_array[1] : "0";
        let new_value = "0", icon_class = "tickmark_0_0"
        if(field_name === "is_active") {
// - toggle filter value
            // default filter inactive '0'; is show all, '1' is show active only, '2' is show inactive only
            // default filter inactive '0'; is show active only, '1' is show all, '2' is show inactive only
            new_value = (filter_value === "2") ? "0" : (filter_value === "1") ? "2" : "1";
// - get new icon_class
            icon_class =  (new_value === "2") ? "inactive_1_3" : (new_value === "1") ? "inactive_0_2" : "inactive_0_0";

        } else if(filter_tag === "toggle") {
            // default filter triple '0'; is show all, '1' is show tickmark, '2' is show without tickmark
// - toggle filter value
            new_value = (filter_value === "2") ? "0" : (filter_value === "1") ? "2" : "1";
// - get new icon_class
            icon_class =  (new_value === "2") ? "tickmark_2_1" : (new_value === "1") ? "tickmark_2_2" : "tickmark_0_0";
        }

    // - put new filter value in filter_dict
        filter_dict[col_index] = [filter_tag, new_value]

    //console.log( "filter_dict", filter_dict);
        el_input.className = icon_class;
        Filter_TableRows();
    };  // HandleFilterToggle

//========= HandleFilterInactive  =============== PR2022-03-03
    function HandleFilterInactive(el_filter) {
        //console.log( "===== HandleFilterInactive  ========= ");
        //console.log( "el_filter", el_filter);

        // show active only when opening page
        const filter_showinactive = (filter_dict && filter_dict.showinactive != null) ? filter_dict.showinactive : 1;
    //console.log( "filter_dict", filter_dict);
    //console.log( "filter_showinactive", filter_showinactive, typeof filter_showinactive);

// - toggle filter value
        // filter inactive '0'; is show all, '1' is show active only, '2' is show inactive only
        // filter inactive '0'; is show active only, '1' is show all, '2' is show inactive only
        // set to default 1 when opening page (el_filter is then undefined
        const new_value = (!el_filter) ? 1 : (filter_showinactive === 2) ? 0 : (filter_showinactive === 1) ? 2 : (filter_showinactive === 0) ? 1 : 1;
// - get new icon_class
        const icon_class =  (new_value === 2) ? "inactive_1_3" : (new_value === 1) ? "inactive_0_2" : "inactive_0_0";

    // - put new filter value in filter_dict
        filter_dict.showinactive = new_value
    //console.log( "filter_dict", filter_dict);

        if( el_filter ) {el_filter.className = icon_class};
        Filter_TableRows();

    };  // HandleFilterInactive

//========= Filter_TableRows  ====================================
    function Filter_TableRows(set_filter_isactive) {  // PR2019-06-09 PR2020-08-31 PR2022-03-03
        //console.log( "===== Filter_TableRows=== ");
        //console.log( "filter_dict", filter_dict);

        // function filters by inactive and substring of fields
        //  - iterates through cells of tblRow
        //  - skips filter of new row (new row is always visible)
        //  - if filter_name is not null:
        //       - checks tblRow.cells[i].children[0], gets value, in case of select element: data-value
        //       - returns show_row = true when filter_name found in value
        //  - if col_inactive has value >= 0 and hide_inactive = true:
        //       - checks data-value of column 'inactive'.
        //       - hides row if inactive = true

        if (set_filter_isactive){
            HandleFilterInactive();
        };
        selected.item_count = 0;
        const data_inactive_field = (selected_btn !== "btn_userpermit") ? "data-inactive" : null;
        for (let i = 0, tblRow, show_row; tblRow = tblBody_datatable.rows[i]; i++) {
            tblRow = tblBody_datatable.rows[i]
            show_row = t_Filter_TableRow_Extended(filter_dict, tblRow, data_inactive_field);

    //console.log( "show_row", show_row);

            add_or_remove_class(tblRow, cls_hide, !show_row);
            if (show_row) {selected.item_count += 1};
        }

// ---  show total in sidebar
        t_set_sbr_itemcount_txt(loc, selected.item_count, loc.User, loc.Users, setting_dict.user_lang);
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

        filter_dict = {};
        filter_mod_employee = false;

        Filter_TableRows(true);  // true = set filter isactive

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

//=========  HandleShowAll  ================ PR2023-04-11
    function HandleShowAll() {
        console.log("=== HandleShowAll");

        const datalist_request = {
                setting: {page: "page_user"},
                user_rows: {get_all_users: true},
                //corrector_rows: {get: true},
                //usercompensation_rows: {get: true},
            };
        console.log("    datalist_request", datalist_request);

        DatalistDownload(datalist_request, "DOMContentLoaded");
    };


//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
// +++++++++++++++++ MODAL SELECT EXAMYEAR OR DEPARTMENT  ++++++++++++++++++++
// functions are in table.js, except for MSED_Response

//=========  MSED_Response  ================ PR2020-12-18 PR2021-05-10 PR2022-12-02
    function MSED_Response(new_setting) {
        console.log( "===== MSED_Response ========= ");
        console.log( "new_setting", new_setting);

// ---  upload new selected_pk
        new_setting.page = setting_dict.sel_page;
// also retrieve the tables that have been changed because of the change in examyear / dep
        const datalist_request = {
                setting: new_setting,
                user_rows: {get: true},
                //corrector_rows: {get: true},
                department_rows: {skip_allowed_filter: true},
                school_rows: {skip_allowed_filter: true},
                level_rows: {skip_allowed_filter: true},
                subject_rows_page_users: {get: true},
                cluster_rows: {page: "page_user"}
            };

        DatalistDownload(datalist_request);

    }  // MSED_Response

//###########################################################################
//=========  MSSSS_Response  ================ PR2021-04-23  PR2021-07-26
    function MSSSS_Response(modalName, tblName, selected_dict, selected_pk) {
        //console.log( "===== MSSSS_Response ========= ");

        // Note: when tblName = school: pk_int = schoolbase_pk
        if(selected_pk === -1) { selected_pk = null};

// ---  put new selected_pk in setting_dict
        setting_dict.sel_schoolbase_pk = selected_pk;

// ---  upload new setting and refresh page
        let datalist_request = {setting: {page: "page_user", sel_schoolbase_pk: selected_pk}};
        DatalistDownload(datalist_request);

    }  // MSSSS_Response

//###########################################################################
//========= set_columns_hidden  ====== PR2021-04-26 PR2022-03-03 PR2023-05-30
    function set_columns_hidden() {
        //console.log( "===== set_columns_hidden  === ");
        //console.log( "    permit_dict", permit_dict);

        if (permit_dict.requsr_role_system) {
            columns_hidden =  [];
        } else if (permit_dict.requsr_role_admin) {
            //  PR2023-05-30 admin must approve secret exams, dont hide auth3 auth4
            //columns_hidden = ["group_auth3", "group_auth4"];
        } else if (permit_dict.requsr_role_insp) {
            columns_hidden =  ["group_auth3", "group_auth4"];
        } else if (permit_dict.requsr_role_corr) {
            columns_hidden =  ["sb_code", "school_abbrev", "group_auth3", "group_anlz"];
        } else if (permit_dict.requsr_role_school) {
            columns_hidden = ["sb_code", "school_abbrev", "group_anlz", "allowed_schoolbases"];
        };
    };  // set_columns_hidden


//###########################################################################

//========= get_datadict_from_tblRow ============= PR2023-04-04
    function get_datadict_from_tblRow(tblRow) {
        const map_id = (tblRow && tblRow.id) ? tblRow.id : null;
        const tblName = get_tblName_from_mapid(map_id);
        const data_dicts = get_data_dicts(tblName);
        return (data_dicts && data_dicts[map_id]) ? data_dicts[map_id] : null;
    };

//========= get_datadict_from_tblRow ============= PR2021-08-01 PR2023-04-04
    function get_data_dicts(tblName) {
        return (tblName === "userpermit") ? permit_dicts : user_dicts;
    };

//========= get_tblName_from_mapid ============= PR2021-08-01
    function get_tblName_from_mapid(map_id) {
        const arr = (map_id) ? map_id.split("_") : null;
        return (arr && arr.length) ? arr[0] : null;
    };
//////////////////////

    function get_tblName_from_selectedBtn() {  //P R2021-08-01
        // HandleBtnSelect sets tblName to default "user" when there is no selected_btn
        // this happens when user visits page for the first time
        return  (selected_btn === "btn_user") ? "user" :
                (selected_btn === "btn_usergroup") ? "usergroup" :
                (selected_btn === "btn_userpermit") ? "userpermit" :
                (selected_btn === "btn_allowed") ? "userallowed" : null;
    };

})  // document.addEventListener('DOMContentLoaded', function()