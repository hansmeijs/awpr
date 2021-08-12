// PR2020-12-03 added
// PR2021-07-18 debug: don't use document.addEventListener('DOMContentLoaded', function()
// it will make the variables private and give error in students.js etc.
    "use strict";

// ============================ MOD IMPORT ============================ PR2020-12-03
    //const cls_hide = "display_hide";
    const cls_visible_hide = "visibility_hide";
    const cls_btn_selected = "tsa_btn_selected";

    const cls_unlinked = "tsa_td_unlinked"
    const cls_linked =  "tsa_td_linked"
    const cls_unlinked_selected = "tsa_td_unlinked_selected"
    const cls_linked_selected =  "tsa_td_linked_selected"

    const cls_tbl_td_unlinked = "tsa_td_unlinked";
    const cls_columns_header = "c_columns_header";
    const cls_tbl_td_linked = "tsa_td_linked";
    const cls_cell_saved_even = "cell_saved_even";
    const cls_cell_saved_odd = "cell_saved_odd";
    const cls_cell_unchanged_even = "cell_unchanged_even";
    const cls_cell_unchanged_odd = "cell_unchanged_odd";

    const cls_cell_error_even = "cell_error_even";
    const cls_cell_error_odd = "cell_error_odd";

    const mimp = {};
    let mimp_stored = {};
    let mimp_logfile = [];
    let mimp_loc = {};

    let department_map = new Map();
    let level_map = new Map();
    let sector_map = new Map();

    // PR2021-07-18 moved to import.js:
    //let student_rows = [];
    //let subject_rows = [];
    //let studentsubject_rows = [];
    //let schemeitem_rows = [];

    // MIME xls: application/vnd.ms-excel
    // MIME xlsx: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    // MIME csv: text/csv
     const excelMIMEtypes = {
            xls: "application/vnd.ms-excel",
            xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        };

//####################################################################
// +++++++++++++++++ MODAL IMPORT ++++++++++++++++++++
//=========  MIMP_Open  ================ PR2020-12-03 PR2021-01-12
    function MIMP_Open(loc, import_table) {
        //console.log( "===== MIMP_Open ========= ");
        //console.log( "import_table: ", import_table);
        //console.log( "loc: ", loc);

         // mimp_stored.coldefs gets value from schoolsetting_dict in i_UpdateSchoolsettingsImport(schoolsetting_dict)
// reset all values of mimp to null, keep the keys.
        // was: Object.keys(mimp).forEach(function(key, index) {
        for (const key of Object.keys(mimp)) {
            mimp[key] = null;
        };
        mimp.import_table = import_table
        mimp.skip_open_filedialog = true;
        mimp_loc = loc;

        //PR2020-12-05. This one doesn't work: if(el_filedialog){el_filedialog.files = null};

        const el_MIMP_filedialog = document.getElementById("id_MIMP_filedialog");
        const el_MIMP_filename = document.getElementById("id_MIMP_filename");
        if(el_MIMP_filedialog){el_MIMP_filedialog.value = null};
        if(el_MIMP_filename){el_MIMP_filename.innerText = null};

        // default value of el_MIMP_hasheader is 'true'
        const el_MIMP_hasheader = document.getElementById("id_MIMP_hasheader");
        if(el_MIMP_hasheader){el_MIMP_hasheader.checked = true};

        //PR2020-10-28 debug: modal gives 'NaN' and 'undefined' when  loc not back from server yet
        if (!isEmpty(mimp_loc)) {
            //mod_dict = {base_id: setting_dict.requsr_schoolbase_pk, table: import_table};
            mimp.header_text = (import_table === "import_student") ? mimp_loc.Upload_candidates :
                                (["import_subject", "import_studsubj"].includes(import_table)) ? mimp_loc.Upload_subjects :
                                (import_table === "import_grade") ? mimp_loc.Upload_grades :
                                (import_table === "import_permit") ? mimp_loc.Upload_permissions :
                                (import_table === "import_username") ? mimp_loc.Upload_usernames : null;

            const subheader_a = ((import_table === "import_student") ? mimp_loc.Select_Excelfile_with_students :
                                (["import_subject", "import_studsubj"].includes(import_table)) ? mimp_loc.Select_Excelfile_with_subjects :
                                (import_table === "import_grade") ? mimp_loc.Select_Excelfile_with_grades :
                                (import_table === "import_permit") ? mimp_loc.Select_Excelfile_with_permits :
                                (import_table === "import_username") ? mimp_loc.Select_Excelfile_with_usernames : "") + ":";

            document.getElementById("id_MIMP_header").innerText = mimp.header_text;
            document.getElementById("id_MIMP_filedialog_label").innerText = "A. " + subheader_a;
            // >>>>>>>>>document.getElementById("id_MIMP_upload_label").innerText = header_text;

            document.getElementById("id_MIMP_msg_filedialog").innerText = mimp_loc.First_select_valid_excelfile;

// show crosstab_container only when import subjects  NOT IN USE PR2021-08-11
            //const el_MIMP_crosstab_container = document.getElementById("id_MIMP_crosstab_container");
            //const hide_crosstab_container = (!["import_subject", "import_studsubj"].includes(mimp.import_table))
            //add_or_remove_class(el_MIMP_crosstab_container, cls_hide, hide_crosstab_container)

            const el_MIMP_crosstab = document.getElementById("id_MIMP_crosstab");
            const el_MIMP_tabular = document.getElementById("id_MIMP_tabular");

            add_or_remove_class(document.getElementById("id_MIMP_loader"), cls_hide, true);

            const el_MIMP_msg_container = document.getElementById("id_MIMP_msg_container");
            add_or_remove_class(el_MIMP_msg_container, cls_hide, true)

// show msg "You don't have to link the subjects yet." only when importing studsubjects
            show_hide_element_by_id("id_MIMP_msg_dontlinksubjects", (import_table === "import_studsubj"));

            MIMP_btnSelectClicked("btn_step1");

// ---  fill select unique option
            //const el_selectunique_container = document.getElementById("id_MIMP_selectunique_container");
            //add_or_remove_class(el_selectunique_container, cls_hide, !mimp_stored.one_unique_identifier);
            //if (mimp_stored.one_unique_identifier) {
            //    const el_select_unique = document.getElementById("id_MIMP_select_unique");
            //    let selected_value = null;
            //    const filter_field = "linkfield",  filter_value = true;
                // mimp_loc.options_examtype: {'value': 'se', 'filter': EXAMPERIOD_FIRST, 'caption': _('School exam')},
                // mimp_stored.coldefs {awpColdef: "page", caption: "Pagina", linkfield: true, excColdef: "page"}

               // t_FillOptionsFromList(el_select_unique, mimp_stored.coldefs, "awpColdef", "caption",
               //     mimp_loc.Select_column + "...", mimp_loc.No_column_found,
               //     selected_value, filter_field, filter_value);
               // el_selectunique_container.classList.remove(cls_hide);
            //}
// ---  show modal
            $("#id_mod_import").modal({backdrop: true});
        }
    }  // MIMP_Open

//=========   MIMP_Save   ======================
    function MIMP_Save(mode, RefreshDataRowsAfterUpload, setting_dict){
        //console.log ("==========  MIMP_Save ==========");
        //console.log ("mimp.import_table", mimp.import_table);
        //console.log ("mimp.is_crosstab", mimp.is_crosstab);
        //console.log ("setting_dict", setting_dict);
        //console.log ("mode", mode);
        //console.log("mimp.import_table", mimp.import_table);

        // was: if(mimp.import_table === "import_studsubj" && mimp.is_crosstab){
        if(mimp.import_table === "import_studsubj"){
            upload_studentsubjects_crosstab(mode, RefreshDataRowsAfterUpload)
        } else if(mimp.import_table === "import_permit"){
            //upload_permits();
            upload_student(mode, RefreshDataRowsAfterUpload);
        } else if(mimp.import_table === "import_student"){
            upload_student(mode, RefreshDataRowsAfterUpload);

        } else if(mimp.import_table === "import_username"){
            upload_username(mode, RefreshDataRowsAfterUpload);
        };
        add_or_remove_class(document.getElementById("id_MIMP_loader"), cls_hide, false)
        add_or_remove_class(document.getElementById("id_MIMP_msg_container"), cls_hide, true)

    }  // MIMP_Save

//####################################################################

//=========   upload_studentsubjects   ======================
    function upload_studentsubjects_crosstab(mode, RefreshDataRowsAfterUpload) {
        //console.log(" ========== upload_studentsubjects_crosstab ===========");
/*
upload_dict: {'sel_examyear_pk': 1, 'sel_schoolbase_pk': 13, 'sel_depbase_pk': 1,
            'sel_depbase_code': 'Vsbo', 'sel_school_abbrev': 'ATC',
            'importtable': 'import_student',
            'awpColdef_list': ['idnumber', 'sector', 'level'],
            'test': True,
            'data_list': [
                {'rowindex': 0, 'idnumber': '1999112405', 'sector': None, 'level': 1},
                {'rowindex': 8, 'idnumber': '1997053111', 'sector': None, 'level': 1}]}
*/
        const is_test_upload = (mode === "test")

        let rowLength = 0, colLength = 0;
        if(mimp.curWorksheetData){rowLength = mimp.curWorksheetData.length;};
        if(mimp_stored.coldefs){colLength = mimp_stored.coldefs.length;};
        if(rowLength > 0 && colLength > 0){
    //console.log ("mimp.linked_exc_values", deepcopy_dict(mimp.linked_exc_values));
    //console.log ("mimp.linked_awp_values", deepcopy_dict(mimp.linked_awp_values));

// --- put all excColIndexes as key in mapped_subjects, maps ColIndex to awpBasePk {excColIndex: [awpBasePk, subj_code}
            const mapped_subjects = {};
            if(mimp.linked_awp_values.subject && mimp.linked_awp_values.subject.length){
                // dict = {awpBasePk: 39, awpValue: "adm&co", excColIndex: 5, excValue: "adm&co", sortby: "adm&co", rowId: "id_tr_subject_awp_21"
                for (let i = 0, dict; dict = mimp.linked_awp_values.subject[i]; i++) {
                    if (dict.excColIndex && dict.excColIndex != null){ // key can be 0, dont use (!key)
                        const subj_code = (dict.awpValue) ? dict.awpValue : "-";
                        mapped_subjects[dict.excColIndex] = [dict.awpBasePk, subj_code];
                    }
                }
            }
            // mapped_subjects = {5: [143, "bi"], 7: [137, "cav"],  ... }
    //console.log ("mapped_subjects", mapped_subjects);
    //console.log ("mimp",mimp);

// ---  get list of linked awpColdefs mapped colIndex to awpColdef
            // loop through excel_coldefs to get list of linked awpColdefs
            // excel_coldefs = [ {excColIndex: 0, excColdef: "Ex_nr_", awpColdef: "examnumber", awpCaption: "Examennummer"} ]
            // mapped_awpColdefs = {0: "examnumber", 1: "idnumber"}
            let has_awpColdef_examnumber = false,  has_awpColdef_idnumber = false;
            let mapped_awpColdefs = {}
            if(mimp.excel_coldefs){
                for (let i = 0, coldef; coldef = mimp.excel_coldefs[i]; i++) {
                    if (coldef.awpColdef){
                        if (coldef.awpColdef === "examnumber") { has_awpColdef_examnumber = true };
                        if (coldef.awpColdef === "idnumber") { has_awpColdef_idnumber = true };
                        mapped_awpColdefs[coldef.excColIndex] = coldef.awpColdef;
                    }
                }
            }
            // mapped_awpColdefs = {0: "examnumber", 1: "idnumber"}
    //console.log ("mapped_awpColdefs",mapped_awpColdefs);

            if(isEmpty(mapped_awpColdefs)){
                alert("No linked columns")
            } else {
                //PR2021-07-20 only idnumber is lookupfield. Was
                //const lookup_field = (has_awpColdef_examnumber) ? "examnumber" :
                //                     (has_awpColdef_idnumber) ? "idnumber" : null;
                const lookup_field = "idnumber"
    //console.log ("lookup_field", lookup_field);
    //console.log ("mapped_awpColdefs", mapped_awpColdefs);
// ---  loop through all rows of worksheet_data
                let dict_list = [];
                for (let i = 0; i < rowLength; i++) {
                    const row = mimp.curWorksheetData[i];
    //console.log ("row", i,  row);

//------ loop through cells of row
                    // rowindex is index of tablerow. Index 0 is header, therefore rowindex starts with 1
                    // ?? PR2021-02-26 not true: first row of curWorksheetData is first datarow, not header
                    const dict = {};
                    let subject_dict = {}
                    for (let j = 0, len = row.length; j < len; j++) {
                        const cell_value = row[j];
        // skip if cell is empty
                        if(cell_value) {  // cell_value is string , no need for cell_value != null
    //console.log ("    col_index", j, "cell_value", cell_value, typeof cell_value);
// check if column is in mapped_awpColdefs
                            if(j in mapped_awpColdefs){
        // add cellvalue to dict with key awpColdef
                                const awpColdef = mapped_awpColdefs[j];
    //console.log ("    awpColdef", awpColdef);
                                dict[awpColdef] = cell_value
        // check if column is subject column

                            } else if(j in mapped_subjects){

                // ---  check if value exists in linked_exc_values
                                // ---  check if value exists in linked_exc_values
                                // subj_arr = [143, "bi"]
                                const subj_arr = mapped_subjects[j];
                                let subjectBasePk = null, subject_code = null;
                                if (subj_arr) {
                                    subjectBasePk = (Number(subj_arr[0])) ? Number(subj_arr[0]) : null;
                                    if (subjectBasePk){
                                        subject_code = (subj_arr[1]) ? subj_arr[1] : null;
                                        subject_dict[subjectBasePk] = subject_code;
                                    };
                                };
                            }  // if(j in mapped_subjects)
                        }  // if(!row[j])
                    }; // for (let j = 0, excel_coldef_dict; excel_coldef_dict = mimp.excel_coldefs[j]; j++)
                    if(!isEmpty(subject_dict)) { dict.subjects = subject_dict }
                    dict_list.push(dict);
                }  // for (let i = 0; i < rowLength; i++) {

    //console.log ("    dict_list", dict_list);
                if(!dict_list || !dict_list.length){
                    alert("No data found")
                } else {
    // --- Upload Data
                    const el_data = document.getElementById("id_MIMP_data");
                    const url_str = get_attr_from_el(el_data, "data-url_importstudentsubject_upload");
                    const upload_dict = {
                        importtable: mimp.import_table,
                        test: is_test_upload,
                        is_crosstab: mimp.is_crosstab,
                        sel_examyear_pk: mimp_stored.sel_examyear_pk,
                        sel_schoolbase_pk: mimp_stored.sel_schoolbase_pk,
                        sel_depbase_pk: mimp_stored.sel_depbase_pk,
                        filename: mimp.sel_filename,
                        lookup_field: lookup_field,
                        data_list: dict_list
                    }
                    UploadData(url_str, upload_dict, RefreshDataRowsAfterUpload);
                }
            }  // if(!awpColdef_list || !awpColdef_list.length){
        }  // if(rowLength > 0 && colLength > 0){
    }  // upload_studentsubjects_crosstab

//=========   upload_student   ======================
    function upload_student(mode, RefreshDataRowsAfterUpload) {
        //console.log(" ========== upload_student ===========");

        const is_test_upload = (mode === "test")
        let rowLength = 0, colLength = 0;
        if(mimp.curWorksheetData){rowLength = mimp.curWorksheetData.length;};
        if(mimp_stored.coldefs){colLength = mimp_stored.coldefs.length;};

            //console.log ("mimp.rowLength", rowLength);
            //console.log ("colLength", colLength);

        if(rowLength > 0 && colLength > 0){

            //console.log ("mimp.excel_coldefs", deepcopy_dict(mimp.excel_coldefs));
            //console.log ("mimp.linked_exc_values", deepcopy_dict(mimp.linked_exc_values));

// ---  loop through excel_coldefs to get linked awpColdefs
        // excel_coldefs = [ {excColIndex: 1, excColdef: "exnr", rowId: "id_tr_coldef_exc_1", awpColdef: "examnumber", awpCaption: "Examennummer"} ]
            let awpColdef_list = []
            if(mimp.excel_coldefs){
                for (let i = 0, coldef; coldef = mimp.excel_coldefs[i]; i++) {
                    if (!!coldef.awpColdef){awpColdef_list.push(coldef.awpColdef)}
                }
            }
            if(!awpColdef_list || !awpColdef_list.length){
                alert("No linked columns")
            } else {

// ---  loop through all rows of worksheet_data
                let dict_list = [];
                for (let i = 0; i < rowLength; i++) {
                    let row = mimp.curWorksheetData[i];

            //console.log ("row", deepcopy_dict(row));
//------ loop through excel_coldefs
                    // rowindex is index of tablerow. Index 0 is header, therefore rowindex starts with 1
                    let dict = {rowindex: i};
                    for (let j = 0, exc_col; exc_col = mimp.excel_coldefs[j]; j++) {
                        const awpColdef = exc_col.awpColdef;
                        if (awpColdef){
                            let value = (row[j]) ? row[j] : null;
                            let mapped_value = null;
                            if (["department", "level", "sector", "profiel"].includes(awpColdef)){
                // mimp.linked_exc_values = [{excColIndex: 0, excValue: "CM", awpBasePk: 4, awpValue: "c&m", rowId: "id_tr_profiel_exc_0"}]

// ---  check if value exists in linked_exc_values
                                const linked_values = mimp.linked_exc_values[awpColdef];
                                // excel_row = {excColIndex: 3, excValue: "pkl", rowId: "id_tr_profiel_exc_3"}
                                const excel_row = get_arrayRow_by_keyValue(linked_values, "excValue", value);
                // ---  if found: replace excel_value by base_id, that is stored in mimp.linked_exc_values
                                if(excel_row && "awpBasePk" in excel_row){
                                    mapped_value = excel_row.awpBasePk;
                                }

                                //console.log("------- awpColdef:", awpColdef)
                                //console.log("      linked_values:", linked_values)
                                //console.log("      excel_row:", excel_row)
                                //console.log("      mapped_value:", mapped_value)

                            } else if (awpColdef === "birthdate"){
                                mapped_value = Number(value)



                            } else if (["role", "sequence"].includes(awpColdef)){
                                mapped_value = Number(value)
                            } else {
                                mapped_value = value
                            }
                            dict[awpColdef] = mapped_value;
                        }
                    }; //for (let col = 1 ; col <colLength; col++)
                    dict_list.push(dict);
                }
                //console.log("======== dict_list:", dict_list)
                if(!dict_list || !dict_list.length){
                    alert("No data found")
                } else {
// --- Upload Data
                    const el_data = document.getElementById("id_MIMP_data");
                    //const url_str = get_attr_from_el(el_data, "data-url_importdata_upload");

                    const url_str = get_attr_from_el(el_data, "data-url_importstudent_upload");
                    const upload_dict = {sel_examyear_pk: mimp_stored.sel_examyear_pk,
                                    sel_schoolbase_pk: mimp_stored.sel_schoolbase_pk,
                                    sel_depbase_pk: mimp_stored.sel_depbase_pk,
                                    sel_depbase_code: (mimp_stored.sel_depbase_code) ? mimp_stored.sel_depbase_code : "---",
                                    sel_school_abbrev: (mimp_stored.sel_school_abbrev) ? mimp_stored.sel_school_abbrev : "---",
                                    importtable: mimp.import_table,
                                    filename: mimp.sel_filename,
                                     awpColdef_list: awpColdef_list,
                                     test: is_test_upload,
                                     data_list: dict_list
                                     }

                    UploadData(url_str, upload_dict, RefreshDataRowsAfterUpload);
                }
            }
        };
    }  // upload_student

//=========   upload_username   ======================
    function upload_username(mode, RefreshDataRowsAfterUpload) {
        //console.log(" ========== upload_username ===========");

        const is_test_upload = (mode === "test")
        let rowLength = 0, colLength = 0;
        if(mimp.curWorksheetData){rowLength = mimp.curWorksheetData.length;};
        if(mimp_stored.coldefs){colLength = mimp_stored.coldefs.length;};

        if(rowLength > 0 && colLength > 0){

// ---  loop through excel_coldefs to get linked awpColdefs
        // excel_coldefs = [ {excColIndex: 1, excColdef: "exnr", rowId: "id_tr_coldef_exc_1", awpColdef: "examnumber", awpCaption: "Examennummer"} ]
            let awpColdef_list = []
            if(mimp.excel_coldefs){
                for (let i = 0, coldef; coldef = mimp.excel_coldefs[i]; i++) {
                    if (!!coldef.awpColdef){awpColdef_list.push(coldef.awpColdef)}
                }
            }
            if(!awpColdef_list || !awpColdef_list.length){
                alert("No linked columns")
            } else {

// ---  loop through all rows of worksheet_data
                let dict_list = [];
                for (let i = 0; i < rowLength; i++) {
                    let row = mimp.curWorksheetData[i];

//------ loop through excel_coldefs
                    let dict = {};
                    for (let j = 0, exc_col; exc_col = mimp.excel_coldefs[j]; j++) {
                        const awpColdef = exc_col.awpColdef;
                        if (awpColdef){
                            dict[awpColdef] = (row[j]) ? row[j] : null;
                        }
                    };
                    dict_list.push(dict);
                }
    //console.log("dict_list:", dict_list)
                if(!dict_list || !dict_list.length){
                    $("#id_mod_import").modal("hide");
                    const msg_dictlist = [{'header': mimp.header_text, 'class': 'border_bg_invalid', 'msg_html': mimp_loc.No_data_found}];
                    b_ShowModMessages(msg_dictlist);
                } else {
// --- Upload Data
                    const el_data = document.getElementById("id_MIMP_data");
                    //const url_str = get_attr_from_el(el_data, "data-url_importdata_upload");

                    const url_str = get_attr_from_el(el_data, "data-url_importusername_upload");
                    const upload_dict = {
                        importtable: mimp.import_table,
                        filename: mimp.sel_filename,
                         awpColdef_list: awpColdef_list,
                         test: is_test_upload,
                         data_list: dict_list
                    };

    //console.log("======== upload_dict:", upload_dict)
                    UploadData(url_str, upload_dict, RefreshDataRowsAfterUpload);
                }
            }
        };
    }  // upload_username


//####################################################################

//=========   MIMP_OpenFiledialog   ======================
    function MIMP_OpenFiledialog(el_filedialog) { // PR2021-08-04
        //console.log(" ========== MIMP_OpenFiledialog ===========");
        el_filedialog.click();
    };
//=========   MIMP_HandleFiledialog   ======================
    function MIMP_HandleFiledialog(el_filedialog) { // functie wordt alleen doorlopen als file is geselecteerd
        //console.log(" ========== MIMP_HandleFiledialog ===========");

        mimp.excel_coldefs = [];
        mimp.linked_exc_values = {};
        mimp.linked_awp_values = {};
        mimp.curWorkbook = null;
        mimp.curWorkSheets = null
        mimp.curWorkSheet = null;
        mimp.curWorksheetName = null;
        mimp.curWorksheetRange = null;
        mimp.curWorksheetData = [];
        mimp.curNoHeader = false;
        // mimp.sel_btn gets default value in MIMP_Open

        // dont reset these. They get value after download schoolsetting_dict PR2020-12-04
        // mimp_stored.worksheetname = null;
        //mimp_stored.noheader = false;
        //mimp_stored.coldefs = [];

// ---  get curfiles from filedialog
        // curfiles is list of files: PR2020-04-16
        // curFiles[0]: {name: "tsa_import_orders.xlsx", lastModified: 1577989274259, lastModifiedDate: Thu Jan 02 2020 14:21:14 GMT-0400 (Bolivia Time) {}
       // webkitRelativePath: "", size: 9622, type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}, length: 1}

        let curFiles = el_filedialog.files; //This one doesn't work in Firefox: let curFiles = event.target.files;

// ---  validate selected file
        let curFile = null, msg_err = null
        if(curFiles.length === 0) {
            msg_err = mimp_loc.First_select_valid_excelfile;
        } else if(!is_valid_filetype(curFiles[0])) {
            msg_err = mimp_loc.Not_valid_Excelfile + " " + mimp_loc.Only + ".xls " + mimp_loc._and_ + ".xlsx" + mimp_loc.are_supported;
        } else {
            curFile = curFiles[0];
        }
        mimp.sel_file = curFile;
        mimp.sel_filename = (curFile) ? curFile.name : null;
        //console.log("mimp.sel_filename: ", mimp.sel_filename);
        //console.log("curFile", curFile);

// ---  display sel_filename in elid_MIMP_filename, make btn 'outline' when filename existst
        const el_MIMP_filename = document.getElementById("id_MIMP_filename");
        if(el_MIMP_filename && mimp.sel_filename){el_MIMP_filename.innerText = mimp.sel_filename};
        const el_MIMP_btn_filedialog = document.getElementById("id_MIMP_btn_filedialog");
        add_or_remove_class(el_MIMP_btn_filedialog, "btn-outline-secondary", !!mimp.sel_filename, "btn-secondary" )

// ---  display error message when error
        let el_msg_err = document.getElementById("id_MIMP_msg_filedialog")

        el_msg_err.innerText = msg_err;
        show_hide_element(el_msg_err, (!!msg_err));

        MIMP_GetWorkbook(curFile);

    }  // MIMP_HandleFiledialog

//=========  MIMP_GetWorkbook  ====================================
    function MIMP_GetWorkbook(curFile) {
        //console.log("======  MIMP_GetWorkbook  =====");
        // curWorkbook.SheetNames = ["Sheet2", "Compleetlijst", "Sheet1"]
        // curWorkbook.Sheets = { Sheet1: {!margins: {left: 0.7, right: 0.7, top: 0.75, bottom: 0.75, header: 0.3, …},
        //                                 !ref: "A1"
        //                                 A1: {t: "s", v: "test", r: "<t>test</t>", h: "test", w: "test"}, ... }


        if(mimp.sel_file){

            let reader = new FileReader();
            mimp.curWorkbook = null;
            let rABS = false; // false: readAsArrayBuffer,  true: readAsBinaryString
            if (rABS) {
                reader.readAsBinaryString(mimp.sel_file);
            } else {
                reader.readAsArrayBuffer(mimp.sel_file);}
           // PR2017-11-08 debug: reader.onload didn't work when reader.readAsBinaryString was placed after reader.onload

    // ---  read file into workbook
            // PR2018-12-09 debug: leave functions that depend on reading file within onload.
            // This way code executing stops till loading has finished.
            // Otherwise use Promise. See: https://javascript.info/promise-basics
            reader.onload = function(event) {
                let data = event.target.result;
                if(!rABS) {
                    data = new Uint8Array(data);
                };
                if (mimp.sel_file.type === excelMIMEtypes.xls){
                    mimp.curWorkbook = XLS.read(data, {type: rABS ? "binary" : "array"});
                } else {
                    mimp.curWorkbook = XLSX.read(data, {type: rABS ? "binary" : "array"});
                }

        //console.log("mimp.curWorkbook: ", mimp.curWorkbook);
    // ---  make list of worksheets in workbook
                if (mimp.curWorkbook){
                    mimp.curWorkSheets = mimp.curWorkbook.Sheets;

        //console.log("mimp.curWorkSheets: ", mimp.curWorkSheets);
                    let msg_err = null
    // ---  reset el_worksheet_list.options
                    const el_worksheet_list = document.getElementById("id_MIMP_worksheetlist");
                    el_worksheet_list.options.length = 0;
    // ---  give message when workbook has no worksheets, reset mimp.curWorksheetName
                    if (!(mimp.curWorkbook.SheetNames && mimp.curWorkbook.SheetNames.length)) {
                        msg_err = mimp_loc.No_worksheets;
                    } else {
    // ---  fill el_worksheet_list.options with sheets that are not empty
                        let option_count = 0, has_selected_option = false;
                        for (let x = 0, sheet_name; sheet_name = mimp.curWorkbook.SheetNames[x]; ++x){
    // ---  if workbook.SheetNames[x] has range: add to el_worksheet_list
                            const worksheet = mimp.curWorkSheets[sheet_name];
                            const has_range = SheetHasRange(worksheet);
                            if (has_range) {
                                const option = document.createElement("option");
                                option.value = sheet_name;
                                //option.innerHTML = sheet_name;
                                option.innerText = sheet_name;
    // ---  make selected if name equals stored_worksheetname
                                if (mimp_stored.worksheetname) { // if x = '' then !!x evaluates to false.
                                    if(sheet_name.toLowerCase() === mimp_stored.worksheetname.toLowerCase() ){
                                        option.selected = true;
                                        mimp.curWorksheetName = mimp_stored.worksheetname;
                                        mimp.curNoHeader = mimp_stored.noheader
                                        has_selected_option = true;
                                }}
                                el_worksheet_list.appendChild(option);
                                option_count += 1;
                            }
                        } //for (let x=0;

        //console.log("el_worksheet_list: ", el_worksheet_list);

    // ---  give message when no data in worksheets
                        if (!option_count ){
                            msg_err = mimp_loc.No_worksheets_with_data;
    // ---  if not has_selected_option: make first selected = True
                        } else if (!has_selected_option){
                            const first_option = el_worksheet_list.options[0];
                            first_option.selected = true;
                            mimp.curWorksheetName = first_option.value;
                        };
    // ---  get selected worksheet, if any
                        if(mimp.curWorksheetName){
                            mimp.curWorkSheet = mimp.curWorkSheets[mimp.curWorksheetName];
                            if(mimp.curWorkSheet){
    // ---  get Column and Rownumber of upper left cell and lower right cell of SheetRange
                                GetSheetRange();
                                if (mimp.curWorksheetRange) {
    // ---  set el_MIMP_hasheader checked
                                    const el_MIMP_hasheader = document.getElementById("id_MIMP_hasheader");
                                    el_MIMP_hasheader.checked = !mimp.curNoHeader;
    // ---  fill worksheet_data with data from worksheet
                                    mimp.curWorksheetData = FillWorksheetData();
        //console.log("mimp.curWorksheetData: ", mimp.curWorksheetData);
    // ---  fill table excel_coldefs
                                    FillExcelColdefArray();
    // ---  fill lists with linked values
                                    FillExcelValueLists(true);  // true = link_same_names
    // ---  fill link-tables column, department, level, sector
                                    Fill_AEL_Tables();
    // ---  upload new settings awpCaption
                                    UploadImportSetting ("workbook");
                    }}}}
                    let el_msg_err = document.getElementById("id_msg_worksheet")
                    el_msg_err.innerText = msg_err;
                    show_hide_element(el_msg_err, (!!msg_err));
                }  // if (!!workbook){
                // PR2020-04-16 debug: must be in reader.onload, will not be reached when in MIMP_HandleFiledialog
                MIMP_HighlightAndDisableButtons();
            }; // reader.onload = function(event) {
        }; // if(!!mimp.selected_file){
    }  // function MIMP_GetWorkbook())

//=========  MIMP_SelectWorksheet   ======================
    function MIMP_SelectWorksheet() {
        //console.log(" ========== MIMP_SelectWorksheet ===========");
        if(mimp.curWorkbook && mimp.curWorkSheets){
            const el_worksheet_list = document.getElementById("id_MIMP_worksheetlist");
            if(el_worksheet_list.value){
                mimp.curWorksheetName = el_worksheet_list.value;
    // ---  get selected worksheet
                mimp.curWorkSheet = mimp.curWorkSheets[mimp.curWorksheetName];
                if(mimp.curWorkSheet){
    // ---  get Column and Rownumber of upper left cell and lower right cell of SheetRange
                    GetSheetRange ();
                    if (mimp.curWorksheetRange) {
    // ---  set el_MIMP_hasheader checked
                        const el_MIMP_hasheader = document.getElementById("id_MIMP_hasheader");
                        el_MIMP_hasheader.checked = !mimp.curNoHeader;
    // ---  fill worksheet_data with data from worksheet
                        mimp.curWorksheetData = FillWorksheetData();
                        const show_data_table = (mimp.curWorksheetData.length)
    // ---  fill table excel_coldefs
                        FillExcelColdefArray();
    // ---  fill lists with linked values
                        FillExcelValueLists(true);  // true = link_same_names
    // ---  fill link-tables column, department, level, sector
                        Fill_AEL_Tables();
// ---  upload new settings
                        UploadImportSetting ("worksheetlist");
            }}}
        }
        MIMP_HighlightAndDisableButtons();
    }  // MIMP_SelectWorksheet()

//=========   MIMP_CheckboxHasheaderChanged   ======================
    function MIMP_CheckboxHasheaderChanged() {
        //console.log(" ========== MIMP_CheckboxHasheaderChanged ===========");
        if(mimp.curWorkSheet && mimp.curWorksheetRange) {
            const el_MIMP_hasheader = document.getElementById("id_MIMP_hasheader");
            mimp.curNoHeader = !el_MIMP_hasheader.checked;
// ---  fill worksheet_data with data from worksheet
            mimp.curWorksheetData = FillWorksheetData();
// ---  fill table excel_coldefs
            FillExcelColdefArray();
// ---  fill lists with linked values
            FillExcelValueLists(true);  // true = link_same_names
            Fill_AEL_Tables();

// ---  fill tables with linked values
            //const JustLinkedValueAwpId = null, JustUnlinkedValueAwpId = null, JustUnlinkedValueExcId = null;
            //FillValueLinkTables(JustLinkedValueAwpId, JustUnlinkedValueAwpId, JustUnlinkedValueExcId);

// ---  fill DataTable NIU
            // FillDataTable();
            // UpdateDatatableHeader();

// upload new settings awpCaption
            UploadImportSetting ("noheader");
        }  // if(mimp.curWorkSheet){
    }; //MIMP_CheckboxHasheaderChanged


//=========   MIMP_OpenLogfile   ====================== PR2021-07-17
    function MIMP_OpenLogfile() {
        //console.log(" ========== MIMP_OpenLogfile ===========");
        //console.log("mimp_stored", mimp_stored);

            if (!!mimp_logfile && mimp_logfile.length) {
                const today = new Date();
                const this_month_index = 1 + today.getMonth();
                const date_str = today.getFullYear() + "-" + this_month_index + "-" + today.getDate();
                let filename = "Log upload ";
                if (mimp_stored.import_table === "import_permit"){
                    filename += "permits dd " + date_str + ".pdf";
                } else if (mimp_stored.import_table === "import_student"){
                    const schoolname =  [mimp_stored.sel_examyear_code, mimp_stored.sel_school_name, mimp_stored.sel_depbase_code].join(" ");
                    filename += "kandidaten " +  schoolname + " dd " + date_str + ".pdf";
                }
            //console.log("filename", filename);
                printPDFlogfile(mimp_logfile, filename )
                    }
    }; //MIMP_OpenLogfile

//=========  FillExcelColdefArray  ===========
    function FillExcelColdefArray(skip_update_iscrosstab, skip_link_same_values) {
        //console.log("=========  FillExcelColdefArray ========= ");
        // function - creates list mimp.excel_coldefs: [{index: idx, excColdef: colName}, ...]
        //          - loops through stored_coldef and excel_coldefs and add links and caption in these arrays
        // PR20221-02-24 debug: when is_crosstab must not link col subject and subjecttype
        // stored_coldef: [ {awpColdef: "idnumber", caption: "ID nummer", excColdef: "ID"}, 1: ...]
        // excel_coldefs: [ {index: 10, excColdef: "ID", awpColdef: "idnumber", awpCaption: "ID nummer"}} ]

        // function is called by MIMP_GetWorkbook, MIMP_SelectWorksheet, MIMP_CheckboxHasheaderChanged
        let itemlist = [];
        mimp.excel_coldefs = [];
        let has_subject_field = false;


// ---  create array 'excel_coldefs' with Excel column names, replaces spaces, ", ', /, \ and . with _
        const range = mimp.curWorksheetRange

// ---  get column headers if Not SelectedSheetHasNoHeader: from first row, otherwise: F01 etc ");
        if(mimp.curWorkSheet && range) {
            let row_number = range.StartRowNumber;
            for (let col_number = range.StartColNumber, idx = 0, colName = ""; col_number <= range.EndColNumber; ++col_number){
                if (mimp.curNoHeader){
                    const index = "00" + col_number;
                    colName = "F" + index.slice(-2);
                } else {
                    const cellName = GetCellName (col_number,row_number);
                    const excColdef = GetExcelValue(mimp.curWorkSheet, cellName, "w");
                    colName = replaceChar(excColdef);
                    // set has_subject_field = True when colName 'Subject' or 'Subjects' exist
                    if(!has_subject_field && colName){
                        const colName_lc = colName.toLowerCase();
                        has_subject_field = (mimp_loc.Subject && mimp_loc.Subject.toLowerCase() === colName_lc);
                        if(!has_subject_field){has_subject_field = (mimp_loc.Subjects && mimp_loc.Subjects.toLowerCase() === colName_lc)}
                    }
                }
                mimp.excel_coldefs.push ({excColIndex: idx, excColdef: colName});
                idx += 1;
        }}

        //console.log("mimp.excel_coldefs", mimp.excel_coldefs);

// ---  loop through array mimp_stored.coldefs
        // mimp_stored.coldefs gets value from schoolsetting_dict in i_UpdateSchoolsettingsImport(schoolsetting_dict)
        if(mimp_stored.coldefs) {
        //console.log("loop through array mimp_stored.coldefs");
            for (let i = 0, stored_coldef; stored_coldef = mimp_stored.coldefs[i]; i++) {
        //console.log("stored_coldef", stored_coldef);
        //console.log("awpColdef", stored_coldef.awpColdef, "excColdef", stored_coldef.excColdef);
                let is_linked = false;
                // when table = 'column': awpColdef = field name "examnumber" etc
                // when table = department, level or sector etc: awpColdef = base_id
                if (stored_coldef.awpColdef && stored_coldef.excColdef){
// ---  check if excColdef also exists in excel_coldefs
                    let excel_row_byKey = get_arrayRow_by_keyValue(mimp.excel_coldefs, "excColdef", stored_coldef.excColdef);
        //console.log("excel_row_byKey", excel_row_byKey);
                    //if(mimp.import_table === "import_studsubj" &&
                    //    ["subject", "subjecttype"].includes(stored_coldef.awpColdef) && mimp.is_crosstab ){
// skip link fields 'subject' and 'subjecttype' when import studsubjects and is_crosstab
                        // excColdef from stored_coldef
                        //delete stored_coldef.excColdef;
                    //} else if (!!excel_row_byKey){
                    if (excel_row_byKey){
// ---  if excColdef is found in excel_coldefs: add awpColdef and awpCaption to excel_row
                        excel_row_byKey.awpColdef = stored_coldef.awpColdef;
                        excel_row_byKey.awpCaption = stored_coldef.caption;
        //console.log(">>> excColdef is found in excel_coldefs");
                        is_linked = true;
                    } else {
// ---  if excColdef is not found in excel_coldefs remove excColdef from stored_coldef
                        delete stored_coldef.excColdef;
                }}
// ---  if column not linked, check if awpCaption and Excel name are the same, if so: link anyway
                if (!is_linked && !skip_link_same_values){
                    let excel_row_byCaption = get_arrayRow_by_keyValue (mimp.excel_coldefs, "excColdef", stored_coldef.caption)
        //console.log("excel_row_byCaption", excel_row_byCaption);
                    if (excel_row_byCaption){
                        stored_coldef.excColdef = excel_row_byCaption.excColdef;
                        excel_row_byCaption.awpColdef = stored_coldef.awpColdef;
                        excel_row_byCaption.awpCaption = stored_coldef.caption;
                }}
            };  // for (let i = 0, stored_coldef; stored_coldef = mimp_stored.coldefs[i]; i++)
        }

        //console.log("mimp.excel_coldefs", mimp.excel_coldefs);
    }  // FillExcelColdefArray

//=========  FillWorksheetData  ========================================================================
    function FillWorksheetData() {
        //console.log("=========  function FillWorksheetData =========");
        //console.log("mimp.excel_coldefs", mimp.excel_coldefs);
    // fills the list 'worksheet_data' with data from 'worksheet'
            // TODO: change to dict, add date 'w' value to show erro date in result

        let sheet_data = [];
        const range = mimp.curWorksheetRange;
        if(range){
            let row_index = range.StartRowNumber;
            // skip first row when first row is header row
            if (!mimp.curNoHeader) {row_index += 1};
            for (; row_index <= range.EndRowNumber; row_index++){
                let NewRow = [];
                let has_values = false;
                for (let col_index = range.StartColNumber; col_index <= range.EndColNumber; col_index++){
                    let CellName = GetCellName (col_index, row_index);
                    let CellValue = GetExcelValue(mimp.curWorkSheet, CellName,"v");
                    if (CellValue) {has_values = true}
                    NewRow.push (CellValue);
                };
                if (has_values){
                    sheet_data.push (NewRow);
                };
            }
        }
    //console.log("sheet_data", sheet_data);
        return sheet_data;
    }  // FillWorksheetData


//========= is_valid_filetype  ====================================
    function is_valid_filetype(File) {
        // MIME xls: application/vnd.ms-excel
        // MIME xlsx: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
        // MIME csv: text/csv

        let is_valid = false
        for (const value of Object.values(excelMIMEtypes)) {
            if(File.type === value) {
                is_valid = true;
                break;
            }
        }
        return is_valid;
    }

//========= SheetHasRange  ====================================
    function SheetHasRange(worksheet) {
    // PR2017-11-04 from: https://stackoverflow.com/questions/2693021/how-to-count-javascript-array-objects
        //function checks if property "!ref" exists in Sheet. If so, it has a range
        //console.log("==========  SheetHasRange: ==========");
        //console.log("WorkSheet", WorkSheet);
        // range_found = true when WorkSheet has property '!ref'
        let range_found = false;
        for (let prop in worksheet) {
            if (worksheet.hasOwnProperty(prop)) {
                if (prop === "!ref") {
                    range_found = true;
                    break;
                }
            }
        }
        return range_found;
    } //  SheetHasRange

//========= GetSheetRange  ====================================
    function GetSheetRange () {
        //Function gets Column and Rownumber of upper left cell and lower right cell of SheetRange
        // return false if Sheet or !ref not found, otherwise retrun object with col/row start/end
        //console.log("==========  GetSheetRange: ==========");

        mimp.curWorksheetRange = null;
        if (mimp.curWorkSheet) {
            const SheetRef = mimp.curWorkSheet["!ref"];
            if (SheetRef){
                //check if range contains :, if not: range has 1 cell
                let range_split = [];
                if (SheetRef.search(":") === -1) {
                    range_split = [SheetRef, SheetRef];
                } else {
                    //split range_split: Name of StartCell = range_split[0], Name of EndCell = range_split[1];
                    range_split = SheetRef.split(":");
                };
                //console.log("Range: " + range_split[0] + " - " + range_split[1]);
                let strColName, pos;
                const ColNumber = []; //1-based index of colums
                const RowNumber = []; //1-based index of rows
                //range_split[0] is string of Range Start (upper left cell)
                //range_split[1] is string of Range End  (lower right cell
                for (let x=0; x<2; ++x) {
                    // get position of first digit pos is 0-based
                    const pos  = range_split[x].search(/[0-9]/);
                    // get column letters (0 till pos)
                    const strColName  = range_split[x].slice(0,pos);
                    // get row digits (pos till end)
                    RowNumber[x]  = range_split[x].slice(pos);
                    //give ColNumber value =0, otherwise adding values will not work and gives NaN error
                    ColNumber[x] = 0;
                    // iterate through letters of strColName
                    for (let j=0; j<strColName.length ; ++j) {
                        //make letters uppercase (maybe not necessary, but let it stay)
                        let strColNameUpperCase = strColName.toUpperCase();
                        //give letter a number: A=1 - Z=26
                        let CharIndex = -64 + strColNameUpperCase.charCodeAt(j);
                        //calculate power (exponent): Last ltter has exp=0, second last has exp=1, third last has exp=2
                        let exp = strColName.length -j -1;
                        //calculate power (exponent): strColName ABC = 1*26^2 + 2*26^1 + 3*26^0
                        ColNumber[x] += CharIndex *  Math.pow(26, exp);
                    };//for (let j=0; j<strColName.length ; ++j)
                };//for (let x=0; x<2; ++x)
                // extra var necessary otherwise calculation RowCount doesnt work properly PR2017-11-22
                const StartRowNumber = Number(RowNumber[0]);
                const EndRowNumber = Number(RowNumber[1]);
                const RowCount = EndRowNumber - StartRowNumber + 1;
                const StartColNumber = Number(ColNumber[0]);
                const EndColNumber = Number(ColNumber[1]);
                const ColCount = EndColNumber - StartColNumber + 1;

                // range B2:C5 with header gives the following values:
                // StartRowNumber = 3 (header not included)
                // EndRowNumber   = 5
                // RowCount       = 3 (EndRowNumber - StartRowNumber +1)
                mimp.curWorksheetRange = {StartRowNumber: StartRowNumber,
                                        EndRowNumber: EndRowNumber,
                                        RowCount: RowCount,
                                        StartColNumber: StartColNumber,
                                        EndColNumber: EndColNumber,
                                        ColCount: ColCount};
            } //if (!!Sheet["!ref"])
        };// if (!!Sheet)
    }; //function GetSheetRange (Sheet)

//========= GetCellName  ====================================
    function GetCellName (ColNumber, RowNumber ) {
        //PR2017-11-12
        //calculate power (exponent): strColName ABC = 1*26^2 + 2*26^1 + 3*26^0
        //ColNumber[x] += CharIndex *  Math.pow(26, exp);
// //console.log("ColNumber: " + ColNumber + " RowNumber: " + RowNumber);
        var col_name = "";
        if (ColNumber>0 && RowNumber>0){

            for (let exp=2; exp>=0; --exp){
                const divisor = Math.pow(26, exp);
                let dividend = ColNumber;
                // subtract 1 (otherwise 26=AA instead of Z, except for last character (exp=0)
                if (exp > 0 ){--dividend;};
// //console.log("exp: " + exp + ", dividend: " + dividend +", divisor: " + divisor);
                const mod = Math.floor((dividend)/divisor);
                const frac = ColNumber - mod * divisor;
// //console.log("mod: " + mod + ", frac: " + frac);
                if (mod>0){
                    col_name += String.fromCharCode(mod + 64);
                };// if (mod>0){
                ColNumber = frac;
            }; //for (let exp=2; exp>=0; --exp)
            col_name = col_name + RowNumber;
// //console.log("col_name " + col_name);
        }; //if (ColNumber>0 && RowNumber>0)
        return col_name;
    }; //function GetCellName (ColIndex, RowIndex )

//========= GetExcelValue  ====================================
    // PR2017-11-04 from: https://stackoverflow.com/questions/2693021/how-to-count-javascript-array-objects
    function GetExcelValue(Sheet, CellName, ValType) {
//console.log("--------------GetExcelValue");
//console.log("GetExcelValue CellName: " + CellName + "ValType: " + ValType);
        var result = "";
        for(let prop in Sheet) {
            if (Sheet.hasOwnProperty(prop)) {
                if (prop === CellName) {
                    let Cell = Sheet[CellName];
                    let propFound = false;
                    for(let prop2 in Cell) {
                        if (Cell.hasOwnProperty(prop2)) {
                            if (prop2 === ValType) {
                                propFound = true;
                                result = Cell[ValType];
//console.log("result " + ValType + " : " + result);
                                break;
                            } //if (prop2 === ValType)
                        }; //if (Cell.hasOwnProperty(prop2))

                    } //for(let prop2 in Cell)
                    //// in case of csv file property 'w' not available, get 'v' (value) instead
                    if (!propFound) {
                        result = Cell["v"];
                    };
                    break;
                } //if (prop === CellName)
            } //if (Sheet.hasOwnProperty(prop)
        };//for(let prop in Sheet)
        return result;
    }; //function GetExcelValue

//=========  get_AEL_rowId  ================ PR2020-04-18 PR2020-12-27
    function get_AEL_rowId(tblName, key, i){
        // function created row_id for table TSA-columns, Exc-columns and Lnk-columns
        // PR2020-12-27 was: return "id_tr_" + tblName  + "_" + i.toString();
        // tblName = columns, department, level, sector; key = awp. exc. lnk
        return "id_tr_" + tblName + "_" + key  + "_" + i.toString();
    }

//=========  MIMP_btnPrevNextClicked  ================ PR2020-12-05
    function MIMP_btnPrevNextClicked(prev_next) {
        //console.log("=== MIMP_btnPrevNextClicked ===", prev_next);

        let data_btn = mimp.sel_btn;
        const index_str = (data_btn) ? data_btn.slice(-1) : "1";
        let index = (Number(index_str)) ? Number(index_str) : 1;

        if (prev_next === "next"){
            index += 1;
        } else if (prev_next === "prev"){
            index -= 1;
        }
        if (index < 1) {
            index = 1;
        } else if (index > 5) {
            index = 5;
        };
        data_btn = "btn_step" + index;

        MIMP_btnSelectClicked(data_btn);
    }

//=========  MIMP_btnSelectClicked  ================ PR2020-12-05
    function MIMP_btnSelectClicked(data_btn) {
        //console.log("=== MIMP_btnSelectClicked ===", data_btn);
        mimp.sel_btn = data_btn

// ---  show only the elements that are used in this mod_shift_option
        const el_MIMP_body = document.getElementById("id_MIMP_body")
        //PR2021-04-20 mod_upload_permits has no el_MIMP_body and no step buttons
        if(el_MIMP_body){
            const els = el_MIMP_body.getElementsByClassName("btn_show");
            for (let i = 0, el; el = els[i]; i++) {
                const is_show = el.classList.contains(mimp.sel_btn)
                show_hide_element(el, is_show)
            }

// ---  hide loader,  msg_container
            add_or_remove_class(document.getElementById("id_MIMP_loader"), cls_hide, true);
            add_or_remove_class(document.getElementById("id_MIMP_msg_container"), cls_hide, true)

// ---  highlight selected button
            MIMP_HighlightAndDisableButtons();
            // open filedialog when clicked on 'step1 btn, not when opening modal, not when sel_fileexists
            if(!mimp.skip_open_filedialog && data_btn === "btn_step1" && !mimp.sel_file){
                const el_MIMP_filedialog = document.getElementById("id_MIMP_filedialog");
                el_MIMP_filedialog.click();
            }
            mimp.skip_open_filedialog = false;
        }
    }  // MIMP_btnSelectClicked

//=========  MIMP_HighlightAndDisableButtons  ================ PR2019-05-25 PR2021-04-21
    function MIMP_HighlightAndDisableButtons() {
        //console.log("=== MIMP_HighlightAndDisableButtons ===");
        // el_MIMP_btn_prev and el_MIMP_btn_next don't exists when user has no permission

        const el_filedialog = document.getElementById("id_MIMP_filedialog");
        const el_MIMP_btn_prev = document.getElementById("id_MIMP_btn_prev");
        const el_MIMP_btn_next = document.getElementById("id_MIMP_btn_next");
        const el_worksheet_list = document.getElementById("id_MIMP_worksheetlist");
        const el_select_unique = document.getElementById("id_MIMP_select_unique");
        const el_MIMP_crosstab = document.getElementById("id_MIMP_crosstab");

// ---  set mimp.sel_btn
        if(!mimp.sel_btn){ mimp.sel_btn = "btn_step1"};

        const no_worksheet_with_data = !(el_worksheet_list && el_worksheet_list.options && el_worksheet_list.options.length);
        const no_linked_columns =  !(mimp.excel_coldefs && mimp.excel_coldefs.length)
        const no_excel_data = !(mimp.curWorksheetData && mimp.curWorksheetData.length);

// ---  check if selected unique field is linked to an excel column
        const not_all_required_fields_are_linked = !MIMP_RequredFieldsAreLinked();

        const step2_disabled = (no_worksheet_with_data);
        const step3_disabled = (step2_disabled || no_linked_columns || not_all_required_fields_are_linked || no_excel_data);
        const step4_disabled = (step3_disabled);
        const step5_disabled = (step4_disabled || !mimp.is_tested);

        const btn_prev_disabled = (mimp.sel_btn === "btn_step1")
        const btn_next_disabled = ( (mimp.sel_btn === "btn_step5") ||
                                    (mimp.sel_btn === "btn_step4" && step5_disabled) ||
                                    (mimp.sel_btn === "btn_step3" && step4_disabled) ||
                                    (mimp.sel_btn === "btn_step2" && step3_disabled) ||
                                    (mimp.sel_btn === "btn_step1" && step2_disabled))
        el_MIMP_btn_prev.disabled = btn_prev_disabled;
        el_MIMP_btn_next.disabled = btn_next_disabled;

// ---  disable selected button
        let step_text = null;
        let el_btn_container = document.getElementById("id_MIMP_btn_container")
        if(!!el_btn_container){
            let btns = el_btn_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                const data_btn = get_attr_from_el(btn, "data-btn")
                if (data_btn === "btn_step1"){
                    // button step 1 is alway enabled
                    btn.disabled = false;
                } else if (data_btn === "btn_step2"){
                    btn.disabled = step2_disabled;
                } else if (data_btn === "btn_step3"){
                    btn.disabled = step3_disabled;
                } else if (data_btn === "btn_step4"){
                    btn.disabled = step4_disabled;
                } else if (data_btn === "btn_step5"){
                    btn.disabled = step5_disabled;
                }
// ---  highlight selected button
                const is_selected = (data_btn === mimp.sel_btn);
                add_or_remove_class (btn, cls_btn_selected, is_selected);
                if(is_selected){
                    step_text = btn.innerText;
                }
        }};

// ---  set subheader text 'Step 1. Select file' etc
        document.getElementById("id_MIMP_step_text").innerText = step_text

// ---  make el_MIMP_msg_linkrequired visible
        //let el_MIMP_msg_linkrequired = document.getElementById("id_MIMP_msg_linkrequired");
        //add_or_remove_class (el_MIMP_msg_linkrequired, cls_hide, required_identifiers_are_linked);

// ---  focus on next element
        if (mimp.sel_btn === "btn_step1"){
            if (!mimp.sel_file) {
                if(el_filedialog){ el_filedialog.focus()};
            } else if (!mimp.curWorksheetName) {
                if(el_filedialog){ el_worksheet_list.focus()};
            } else {
                if(el_filedialog){ el_MIMP_btn_next.focus()};
            }
        } else if(mimp.sel_btn === "btn_step4"){
            //const el_MIMP_btn_test = document.getElementById("id_MIMP_btn_test");
            //const el_MIMP_btn_upload = document.getElementById("id_MIMP_btn_upload");
            //if(el_MIMP_btn_test){ el_MIMP_btn_test.focus()};
        }
        const el_MIMP_btn_cancel = document.getElementById("id_MIMP_btn_cancel");
        if(el_MIMP_btn_cancel){
            el_MIMP_btn_cancel.innerText = (mimp.sel_btn === "btn_step5") ? mimp_loc.Close : mimp_loc.Cancel;
        };
    }  // MIMP_HighlightAndDisableButtons

//========= MIMP_RequredFieldsAreLinked  ==================================== PR2020-12-06 PR2021-04-21 PR2021-08-01
    function MIMP_RequredFieldsAreLinked() {
        //console.log("=== MIMP_RequredFieldsAreLinked ===");
        //console.log("mimp_stored.coldefs", mimp_stored.coldefs);

        let has_unlinked_fields = false, unique_field_caption = "";
        const unlinked_fields_list = [],  linkrequired_fieldlist = [];
        let msg_text = null;
        if(mimp_stored.coldefs) {
// ---  check if linkrequired field are linked, if an unlinked field is found: add field to unlinked_fields_list
            for (let i = 0, stored_row; stored_row = mimp_stored.coldefs[i]; i++) {
                // stored_row =  {awpColdef: "page", caption: "Pagina", linkfield: true, excColdef: "page"}
                if (stored_row.linkrequired) {
                    linkrequired_fieldlist.push(stored_row.caption);
                    if (!stored_row.excColdef) {
                        has_unlinked_fields = true;
                        unlinked_fields_list.push(stored_row.caption);
            }}};
        }  // if(mimp_stored.coldefs) {
        //console.log("mimp_stored.coldefs", mimp_stored.coldefs);

        // get list of has_unlinked_fields, get all linkrequired_fields is no unlinked_fields
        const field_list = (has_unlinked_fields) ? unlinked_fields_list : linkrequired_fieldlist;
        //console.log("field_list", field_list);
        const list_length = field_list.length;
        if (field_list && field_list.length) {
            let field_names = "";
            for (let i = 0, fldName; fldName = field_list[i]; i++) {
                if (i){ field_names += (i === list_length - 1) ? mimp_loc._and_ : ", "};
                field_names += "'" + fldName + "'"
            }
            msg_text = (list_length > 1) ? mimp_loc.link_The_columns : mimp_loc.link_The_column;

            msg_text += field_names;
            msg_text += (has_unlinked_fields) ? (list_length > 1) ? mimp_loc.link_mustbelinked_plural_zijn : mimp_loc.link_mustbelinked_single_zijn
                            : (list_length > 1) ? mimp_loc.link_mustbelinked_plural_worden : mimp_loc.link_mustbelinked_single_worden;
        }
        const el_MIMP_msg_linkrequired = document.getElementById("id_MIMP_msg_linkrequired")
        el_MIMP_msg_linkrequired.innerText = msg_text;
        add_or_remove_class(el_MIMP_msg_linkrequired, "text-danger", has_unlinked_fields)

        return !has_unlinked_fields;
    }  // MIMP_RequredFieldsAreLinked

//=========  FillExcelValueLists  ================ PR2020-12-26 PR2021-02-23
    function FillExcelValueLists(link_same_names){
        //console.log(" ===== FillExcelValueLists  =====");
        //console.log("mimp_stored", mimp_stored);
        //console.log("mimp.excel_coldefs", mimp.excel_coldefs);
        //console.log("mimp.awp_coldefs", mimp.awp_coldefs);
        //console.log("mimp.import_table", mimp.import_table);
        //console.log("mimp", mimp);

        // function is called by MIMP_GetWorkbook, MIMP_SelectWorksheet, MIMP_CheckboxHasheaderChanged, LinkColumns, UnlinkColumns
        // function fills mimp.linked_exc_values with excel_values of department, level, sector, subject, NIU: subjecttype
        // links same names, not after LinkColumns / UnlinkColumns
        // mimp_stored contains saved links
        // mimp_stored gets value from schoolsetting_dict in i_UpdateSchoolsettingsImport(schoolsetting_dict)
        // mimp_stored.coldefs = {awpColdef: "idnumber", caption: "ID-nummer", linkfield: true, excColdef: "ID-nummer"}
        // excel_column = {index: 1, excValue: "exnr", awpValue: "examnumber", awpCaption: "Examennummer"}

// ---  loop through list of tables that must be filled
        const awp_colNames_dict = {import_student: ["department", "level", "sector", "profiel"],
                                   // PR2021-08-11 was: import_studsubj: ["subject", "subjecttype"],
                                   import_studsubj: ["subject"],
                                   import_permit: ["permits"],
                                   import_awp: ["awpdata"],
                                // TODO
                               import_subject: [],
                               import_grade: []}
        const awp_colNames_list = awp_colNames_dict[mimp.import_table];
// skip when import_table = import_studsubj and is_crosstab, fill lists by .... instead

        if(awp_colNames_list && awp_colNames_list.length){
            for (let x = 0, awpColdef; awpColdef = awp_colNames_list[x]; x++) {

    // ---  skip when awpColdef not linked
                    // lookup excel_coldef_row with awpColdef in it, the awpColdef is not linked when no row found
                    const excel_coldef_row = get_arrayRow_by_keyValue(mimp.excel_coldefs, "awpColdef", awpColdef);

    // --- hide awp-exc-lnk lists when table is not linked
                    const container_id = "id_MIMP_container_" + awpColdef;
                    const el_container = document.getElementById(container_id);
                    add_or_remove_class(el_container, cls_hide, !excel_coldef_row);

// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
// skip when import_table = import_studsubj , get subject names from coldefs instead
                // PR2021-08-11 is_crosstab NIU. WAS: if (mimp.import_table === "import_studsubj" && mimp.is_crosstab) {
                if (mimp.import_table === "import_studsubj") {
                    if (awpColdef === "subject"){
// --- get subject names from unlinked coldefs
                         let excel_value_list = get_unlinked_excel_coldefs();
                         //excel_value_list = [{excColIndex: 5, excColdef: "adm&co", sortby: "adm&co"}, ...]
                         create_mimp_linked_values_list(awpColdef, excel_value_list);
                    }
                } else {
// xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

                    if(excel_coldef_row){
    // --- get excColIndex and excColdef
                        const excColIndex = excel_coldef_row.excColIndex;
                        const excColdef = excel_coldef_row.excColdef;

        // ---  add awpColdef dict to mimp.linked_awp_values
                        // sector: [ {awpBasePk: 4, awpValue: "c&m", rowId: "id_tr_sector_awp_0"}
                        //           {awpBasePk: 5, awpValue: "e&m", excColdef: "Profiel", excValue: "EM", rowId: "id_tr_sector_awp_1"}
                        //mimp.linked_awp_values[awpColdef] = deepcopy_dict(mimp_stored[awpColdef]);
                        mimp.linked_awp_values[awpColdef] = mimp_stored[awpColdef];

    // ---  loop through curWorksheetData, create a list of excel values and add to mimp.linked_exc_values
                        // excel_value_list = ["EM", "NT", "CM"]
                        const excel_value_list = get_excel_valuelist_from_tablecolumn([excColIndex]); // [excColIndex] is a list
                        if (excel_value_list && excel_value_list.length){
    // ---  convert the excel_value_list to a dict_list, add linked awpBasePk and awpValue to exc_dict
                            const dict_list = convert_excelvaluelist_to_dictlist(
                                        excColIndex, excColdef, awpColdef, excel_value_list, link_same_names);
                            mimp.linked_exc_values[awpColdef] = dict_list
                        }  // if (excel_value_list.length){
                    }  // if(excel_coldef_row){
                }  //  if (mimp.import_table !== "import_studsubj" && is_crosstab)

            }  //  for (let x = 0, awp_colName; awp_colName = awp_col_names[x]; x++)
        }  // if(awp_col_names.length){

        //console.log("mimp.linked_exc_values", deepcopy_dict(mimp.linked_exc_values));
        //console.log("mimp.linked_awp_values", deepcopy_dict(mimp.linked_awp_values));
    }  // FillExcelValueLists

//=========  create_mimp_linked_values_list  ================   PR2021-02-28
    function create_mimp_linked_values_list(awpColdef, excel_value_list){
        //console.log("================ create_mimp_linked_values_list  ========= ");
        //console.log("awpColdef", awpColdef);
        //console.log("excel_value_list", excel_value_list);

// --- create new_awpDict_list
        const new_awpDict_list = []
        const stored_awp_coldefs = mimp_stored[awpColdef];
        // stored_awp_coldefs = [{awpBasePk: 42, awpValue: "zwi", excValue: "leerweg"},... ]
        if(stored_awp_coldefs){
            for (let i = 0, dict; dict = stored_awp_coldefs[i]; i++) {
                const sortby = (dict.awpValue) ? dict.awpValue.toLowerCase() : "zzzzz";
                const row_id = get_AEL_rowId(awpColdef, "awp", i); // row_id: id_tr_subject_awp_2
                const new_awpDict = {awpBasePk: dict.awpBasePk, awpValue: dict.awpValue, rowId: row_id, sortby: sortby}
                if(dict.excValue) {new_awpDict.excValue = dict.excValue};
                new_awpDict_list.push(new_awpDict);
            }
            if(new_awpDict_list.length){new_awpDict_list.sort(b_comparator_sortby)}
        }

        //new_awpDict_list = [ {awpBasePk: 39, awpValue: "adm&co", excColIndex: 5, excValue: "adm&co", sortby: "adm&co", rowId: "id_tr_subject_awp_21"}, ...]
        const new_excDict_list = [];
        if(excel_value_list && new_awpDict_list){
// ---------- loop through excel_value_list
            // excDict = {excColIndex: 9, excColdef: "bw", sortby: "bw"}
            for (let j = 0, excDict; excDict = excel_value_list[j]; j++) {
                let excDict_excValue = null;
                if (excDict && excDict.excColdef) {excDict_excValue = excDict.excColdef};

// ---  lookup excel_value in mimp_stored awpColdef
        // ---  skip when awpColdef not linked
                // lookup row with awpColdef in it, the awpColdef is not linked when no row found
                if (excDict_excValue){
                    const sortby = (excDict.excColdef) ? excDict.excColdef.toLowerCase() : "zzzzz";
                    const row_id = get_AEL_rowId(awpColdef, "exc", j); // row_id: id_tr_subject_exc_2
                    const new_excDict = {excColIndex: excDict.excColIndex, excValue: excDict.excColdef, rowId: row_id, sortby: sortby}
                    const excDict_excValue_lc = excDict_excValue.toLowerCase();

// ---------- loop through new_awpDict_list
                    // awpDict = {awpBasePk: 34, awpValue: "bw", rowId: undefined, sortby: "bw", excValue: "bw"}
                    for (let x = 0, awpDict; awpDict = new_awpDict_list[x]; x++) {
                        const awpDict_excValue = (awpDict && awpDict.excValue) ? awpDict.excValue : null;
                        if(awpDict_excValue){
                            const awpDict_excValue_lc = awpDict_excValue.toLowerCase();
    // link if awpdict has key 'excValue' and excValue in awpdict and excdict are the same in lowercase
                            if(awpDict_excValue_lc === excDict_excValue_lc){
                                new_excDict.awpValue = awpDict.awpValue;
                                new_excDict.awpBasePk = awpDict.awpBasePk;
                                awpDict.excValue = new_excDict.excValue;
                                awpDict.excColIndex = new_excDict.excColIndex;
                                break;
                            }
                        } else {
                        // also link when 'excValue' in excdict equals awpValue in awpDict
                            const awpDict_awpValue = (awpDict.awpValue) ? awpDict.awpValue : null;
                            if (awpDict_awpValue && awpDict_awpValue.toLowerCase() === excDict_excValue_lc){
                                new_excDict.awpValue = awpDict.awpValue;
                                new_excDict.awpBasePk = awpDict.awpBasePk;
                                awpDict.excValue = new_excDict.excValue;
                                awpDict.excColIndex = new_excDict.excColIndex;
                                break;
                            }
                        }
                    }  // for (let x = 0, awpDict; awpDict = new_awpDict_list[x]; x++)
                    new_excDict_list.push(new_excDict)
                }
            }  // for (let j = 0, excel_value; excel_value = excel_value_list[j]; j++)

        }  //   if(excel_value_list)
        mimp.linked_exc_values[awpColdef] = new_excDict_list
        mimp.linked_awp_values[awpColdef] = new_awpDict_list;
        //console.log("============ mimp.linked_exc_values[awpColdef]", new_excDict_list);
        //console.log("============ mimp.linked_awp_values[awpColdef] ", new_awpDict_list);
        //console.log("-----------------------------------------------------------------");
    }  // create_mimp_linked_values_list

//=========  get_unlinked_excel_coldefs  ================   PR2021-02-25
    function get_unlinked_excel_coldefs(){
        //console.log("==== get_unlinked_excel_coldefs  ========= ");
        //
// ---  loop through list of excel_coldefs en put unlinked ones in list
        const excel_value_list = [];
        if(mimp.excel_coldefs){
            for (let i = 0, row; row = mimp.excel_coldefs[i]; i++) {
                const excColIndex = row.excColIndex;
                const excColdef = row.excColdef;
                const awpColdef = row.awpColdef;
                if(excColdef && !awpColdef){
                    const excColdef_lc = excColdef.toLowerCase();
// ---  create a list of excel values and add to mimp.linked_exc_values
                    // excel_value_list = ["en", "pa", ...]
                    // do not convert to lowercase
                    // leave doubles, they have different col_index
// ---  get value of column with index 'excColIndex' and add value to excel_value_list if it doesn't yet exist in this list
                    if (!excel_value_list.includes(excColdef_lc)) {
                        const dict = {excColIndex: excColIndex, excColdef: excColdef, sortby: excColdef_lc}
                        excel_value_list.push(dict);
                    }
                }
            }
            if (excel_value_list.length){
// ---  sort dictlist by key 'sortby' PR2021-02-25
                excel_value_list.sort(b_comparator_sortby);
            }
        }``
        return excel_value_list;
    }  // get_unlinked_excel_coldefs

//=========  get_excel_valuelist_from_tablecolumn  ================  PR2021-02-24
    function get_excel_valuelist_from_tablecolumn(excColIndex_list){
        //console.log("==== get_excel_valuelist_from_tablecolumn  ========= ");
        //console.log("excColIndex_list", excColIndex_list);

// ---  loop through rows of curWorksheetData,
        // loop only through columns that are in excColIndex_list
        //  (in crosstab it is the list vof subjects, in tablular it is one column 'Subject' or 'Subjecttype'
        // create a list of excel values and add to mimp.linked_exc_values
        // excel_value_list = ["EM", "NT", "CM"]
        let excel_value_list = [];
        if(mimp.curWorksheetData && excColIndex_list.length ){
            for (let i = 0, data_row; data_row = mimp.curWorksheetData[i]; i++) {
                // data_row: ["576", "112", "Regales", .... , "NT", "4", "40", "21", "W4"]
// ---  get value of column with index 'excColIndex' and add value to excel_value_list if it doesn't yet exist in this list

// ---  loop through columns of data_row, onluy the columns that are in excColIndex_list
                for (let j = 0, excColIndex; excColIndex = excColIndex_list[j]; j++) {
                    const value = data_row[excColIndex];
                    if (value && !excel_value_list.includes(value)) {
                        excel_value_list.push(value)
                    }
                }
            };
        }
        //console.log("excel_value_list", excel_value_list);
        const excel_value_dictlist = []
        if (excel_value_list.length){

// ---  sort the excel_value_list
            // from https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/sort
            excel_value_list.sort(function (a, b) {return a.localeCompare(b);});

        //console.log("..............excel_value_list", excel_value_list);
// --- convert to dictlist
            for (let i = 0, value; value = excel_value_list[i]; i++) {
                if(value){
                    // PR2021-08-10 debug: when value is integer toLowerCase() gives error, convert to string first
                    const value_lc = value.toString().toLowerCase();
        //console.log("............value_lc", value_lc);
                    excel_value_dictlist.push( {excColdef: value, sortby: value_lc} )
                }
            };
        //console.log("excel_value_dictlist", excel_value_dictlist);
        //console.log(".............................................");
        }
        return excel_value_dictlist;
    }  // get_excel_valuelist_from_tablecolumn

//=========  convert_excelvaluelist_to_dictlist  ================  PR2021-02-24
    function convert_excelvaluelist_to_dictlist(excColIndex, excColdef, awpColdef, excel_value_list, link_same_names){
        //console.log(" ----- convert_excelvaluelist_to_dictlist ----- ");
        //console.log("excColIndex", excColIndex);
        //console.log("excColdef", excColdef);
        //console.log("awpColdef", awpColdef);
        //console.log("excel_value_list", excel_value_list);
        //console.log("link_same_names", link_same_names);
        // ---  convert the excel_value_list to a dict_list, add linked awpValue and
        const dict_list = [];
        for (let j = 0, excel_value_dict; excel_value_dict = excel_value_list[j]; j++) {
            const excel_value = excel_value_dict.excColdef;
            const exc_dict = {excColIndex: j, excValue: excel_value}
        //console.log("%%%%%%%%%%%%%%%%% excel_value", excel_value);
        //console.log("%%%%%%%%%%%%%%%% exc_dict", exc_dict);

// ---  lookup excel_value in mimp_stored awpColdef
            if(mimp_stored[awpColdef]){
                for (let x = 0, awp_dict; awp_dict = mimp_stored[awpColdef][x]; x++) {
        //console.log("awp_dict", awp_dict);
                    // awp_dict {awpBasePk: 1, awpValue: "Vsbo"}
                    if (awp_dict){
// ---  if is linked value (when excValue exists in awp_dict): add awpBasePk and awpValue to exc_dict
                        if (awp_dict.excValue) {
        //console.log("awp_dict.excValue", awp_dict.excValue);
                            if (awp_dict.excValue.toLowerCase() === excel_value.toLowerCase() ){
                                if(awp_dict.awpBasePk){ exc_dict.awpBasePk = awp_dict.awpBasePk }
                                if(awp_dict.awpValue){ exc_dict.awpValue = awp_dict.awpValue }
                            }
                        } else if (awp_dict.awpValue && excel_value && !!link_same_names) {
// ---  if not a linked value: check if awpValue and excValue are the same. If so: add to linked list
                            // PR2021-02-23 note:
                            // same value links are not saved in settings at this moment.
                            // but if you make changes in linked fields these same value linkes will also be stored
// ---  add to exc_dict when stripped values are the same
        //console.log("excel_value ", excel_value);
        //console.log("awp_dict.awpValue ", awp_dict.awpValue);

                            if (same_awp_exc_values(excel_value, awp_dict.awpValue)){
                                if(awp_dict.awpBasePk){ exc_dict.awpBasePk = awp_dict.awpBasePk }
                                if(awp_dict.awpValue) {exc_dict.awpValue = awp_dict.awpValue};
                            // also add to awp_dict
                                if(excColdef){ awp_dict.excColdef = excColdef }
                                awp_dict.excValue = excel_value
                            }
                        }
                    }  // if (awp_dict){
                }  // for (let x = 0, awp_dict; awp_dict = mimp_stored[awpColdef][x]; x++)
            }  // if(mimp_stored[awpColdef]){
            dict_list.push(exc_dict)
        }  // for (let j = 0, excel_value; excel_value = excel_value_list[j]; j++)
// ---  add the dict_list to mimp.linked_exc_values
        // mimp.linked_exc_values = { sector: [ {excColIndex: 0, excValue: "CM"},
        //                                      {excColIndex: 1, excValue: "EM"},
        //                                      {excColIndex: 2, excValue: "NT"} ] }

        //console.log("dict_list ", dict_list);
        return dict_list;
    }  // convert_excelvaluelist_to_dictlist

//========= same_awp_exc_values  ========  PR2021-02-25
    function same_awp_exc_values(excValue, awpValue) {
        //console.log("==== same_awp_exc_values  =========>> ");
        //console.log("excValue ", excValue);
        //console.log("awpValue ", awpValue);
// ---  functions checks if awpValue and excValue are the same.
        // characters '&', ' ', and '-' are omitted
        // converted to lowercase

        let is_same_val_stripped = false;
        if (awpValue && excValue ) {

            // PR2021-08-10 debug: when value is integer toLowerCase() gives error, convert to string first
            let awp_val_stripped = awpValue.toString().toLowerCase()
            awp_val_stripped = awp_val_stripped.replaceAll("&", "");
            awp_val_stripped = awp_val_stripped.replaceAll(" ", "");
            awp_val_stripped = awp_val_stripped.replaceAll("-", "");

            let exc_val_stripped = excValue.toString().toLowerCase()
            exc_val_stripped = exc_val_stripped.replaceAll("&", "");
            exc_val_stripped = exc_val_stripped.replaceAll(" ", "");
            exc_val_stripped = exc_val_stripped.replaceAll("-", "");

// ---  add to exc_dict when stripped values are the same
            is_same_val_stripped = (awp_val_stripped && exc_val_stripped && awp_val_stripped === exc_val_stripped)
        }
        return is_same_val_stripped;
    }  // same_awp_exc_values

//========= Fill_AEL_Tables  ====================================
    function Fill_AEL_Tables(JustLinkedAwpId, JustUnLinkedAwpId, JustUnlinkedExcId) {
        //console.log("==== Fill_AEL_Tables  =========>> ");
        //console.log("mimp_stored.coldefs ", mimp_stored.coldefs);
        //console.log("mimp_stored.tablelist ", mimp_stored.tablelist);
        //console.log("mimp.excel_coldefs ", mimp.excel_coldefs);
        // called by MIMP_GetWorkbook, MIMP_SelectWorksheet, MIMP_CheckboxHasheaderChanged, LinkColumns, UnlinkColumns

        // only fill tables that are in mimp_stored.tablelist
        if(mimp_stored.tablelist){
            for (let i = 0, tbodyTblName; tbodyTblName = mimp_stored.tablelist[i]; i++) {
                Fill_AEL_Table(tbodyTblName, JustLinkedAwpId, JustUnLinkedAwpId, JustUnlinkedExcId)
            }
        }
    }  // Fill_AEL_Tables

//========= Fill_AEL_Table  ==================================== PR2020-12-29
    function Fill_AEL_Table(tbodyTblName, JustLinkedAwpId, JustUnLinkedAwpId, JustUnlinkedExcId) {
        //console.log("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ ==== Fill_AEL_Table  ========= ");
        //console.log("tbodyTblName", tbodyTblName);
        //console.log("mimp.import_table", mimp.import_table);
        //console.log("mimp.linked_awp_values[tbodyTblName] ", deepcopy_dict(mimp.linked_awp_values[tbodyTblName]));
        //console.log("mimp.linked_exc_values[tbodyTblName] ", deepcopy_dict(mimp.linked_exc_values[tbodyTblName]));

        // tbodyTblNames are: "coldef", "department", "level", "sector", "profiel", "subject", "subjecttype"
        // tbody id's are: id_MIMP_tbody_coldef_awp, id_MIMP_tbody_coldef_exc, id_MIMP_tbody_coldef_lnk etc.

        // stored_coldef: [ {awpColdef: "examnumber", caption: "Examennummer", linkfield: true, excColdef: "exnr"}, ...]

        const is_tbl_coldef = (tbodyTblName === "coldef");

// ---  reset tables
        const el_tbody_awp = document.getElementById("id_MIMP_tbody_" + tbodyTblName + "_awp")
        const el_tbody_exc = document.getElementById("id_MIMP_tbody_" + tbodyTblName + "_exc")
        const el_tbody_lnk = document.getElementById("id_MIMP_tbody_" + tbodyTblName + "_lnk")

        if (el_tbody_awp && el_tbody_exc && el_tbody_lnk){
            el_tbody_awp.innerText = null
            el_tbody_exc.innerText = null
            el_tbody_lnk.innerText = null

    // ---  show or hide tables
            // tbodyTblName gets value from mimp_stored.tablelist
            // hide table department, level, sector when their column is not linked, only when table = student
            let show_table = false;
            if (is_tbl_coldef){
                show_table = true;
            } else {
                if(mimp.import_table === "import_student"){
                    // --- hide tables that are not linked
                    // lookup awpColdef 'department' etc in mimp_stored.coldefs. If it exists: show table 'department' etc.
                    const lookup_row = get_arrayRow_by_keyValue(mimp_stored.coldefs, "awpColdef", tbodyTblName);
                    // check if it is a linked column by checking if 'excColdef' exists in row
                    show_table = (!!lookup_row && "excColdef" in lookup_row) ;

                } else if(mimp.import_table === "import_studsubj"){
                    // PR2021-08-11 NIU. Was: show_table = (["subject", "subjecttype"].includes(tbodyTblName));
                    show_table = (tbodyTblName === "subject");
                }
            }
            const el_container = document.getElementById("id_MIMP_container_" + tbodyTblName);
            if(el_container) {add_or_remove_class(el_container, cls_hide, !show_table)};

             // mimp_stored.coldefs gets value from schoolsetting_dict in i_UpdateSchoolsettingsImport(schoolsetting_dict)

            if(show_table){
    // ---  first loop through array of awp_columns, then through array of excel_coldefs
                // key: 0 = "awp", 1: "lnk" or "awp"
                for (let j = 0; j < 2; j++) {
                    const key =  (!j) ? "awp" : "exc";
                    const rows = (is_tbl_coldef) ? (key === "awp") ? mimp_stored.coldefs : mimp.excel_coldefs :
                                                   (key === "awp") ? mimp.linked_awp_values[tbodyTblName] : mimp.linked_exc_values[tbodyTblName];
                    const rows_name = (is_tbl_coldef) ? (key === "awp") ? "mimp_stored.coldefs" : "mimp.excel_coldefs" :
                                                   (key === "awp") ? "mimp.linked_awp_values[" + tbodyTblName + "]" : "mimp.linked_exc_values[" + tbodyTblName + "]";
            //console.log("=============== key", key, "==================");
            //console.log("------------- rows_name", rows_name);
            //console.log("------------- rows", rows);


            //console.log("mimp.linked_exc_values[subject] ", deepcopy_dict(mimp.linked_awp_values["subject"]));

                    if(rows){
                        for (let i = 0, row ; row = rows[i]; i++) {
                            // mimp_stored.coldefs row = {awpColdef: "examnumber", caption: "Examennummer", linkfield: true, excColdef: "exnr"}
                            //                    row = {awpBasePk: 7, awpValue: "n&t", excColdef: "Profiel", excValue: "NT"}
                            // {awpBasePk: 5, awpValue: "e&m", excColdef: "Profiel", excValue: "EM"}
                            // >>>>> give value to rowid when creating dictlist
                            let row_id = row.rowId;
                            //if(!row_id) { row_id = get_AEL_rowId(tbodyTblName, key, i)}; // row_id: id_tr_level_exc_2
                            // add rowId to dict of this row
                            //row.rowId = row_id;
                            // awp row is linked when it has an excColdef and excValue -> add to linked table
                            //const row_is_linked = (!!row.excColdef);


            //console.log("------------- row ------------- ");
            //console.log( row);
            //console.log("row.excColdef", row.excColdef, "row.awpColdef", row.awpColdef);

                            // short version:
                            //const row_is_linked = (is_tbl_coldef) ? (key === "awp") ? !!row.excColdef : !!row.awpColdef :
                            //                                        (key === "awp") ? !!row.excValue : !!row.awpBasePk;

                            let row_is_linked = false;
                            if (is_tbl_coldef) {
                                if (key === "awp") {
                                    row_is_linked = !!row.excColdef;
                                } else {
                                    row_is_linked = !!row.awpColdef;
                                    if(!row_is_linked){
                                        if (mimp.import_table === "import_studsubj"){
                                            // all subject show up in excel coldef table, too confusing
                                            // skip subjects in excel coldef table when they exist in mimp.linked_exc_values[subject]
                                            const lookup_dict = b_lookup_dict_in_dictlist(mimp.linked_awp_values["subject"], "excValue", row.excColdef);

            //console.log(".lookup_dict", !!lookup_dict, lookup_dict);
                                            if(lookup_dict){
                                                row_is_linked = true;
                                            }
                                        }
                                    }
                                };
                            } else {
                                if (key === "awp") {
                                    row_is_linked = !!row.excValue;
                                } else {
                                    row_is_linked = !!row.awpBasePk;
                                };
                            }
                            const row_cls = (row_is_linked) ? cls_tbl_td_linked : cls_tbl_td_unlinked;
                            const cls_width = (row_is_linked) ? "tsa_tw_50perc" : "tsa_tw_100perc";
                            const row_awpBasePk = (row.awpBasePk) ? row.awpBasePk : null;


                // ---  dont add row when excel_row is linked (has awpBasePk)
                            // PR2020-12-27 debug: must use (!!j); (j) will return 0 instead of false;
                            // skip linked excel row, linked row is already added by key 'awp'
                            //const skip_linked_exc_row = (is_tbl_coldef) ? !!j && row_is_linked : (!!j && !!row_awpBasePk);
                            const skip_linked_exc_row = (key === "exc" && row_is_linked)

            //console.log("=========> .row_is_linked", row_is_linked);

                            const awpCaption = (is_tbl_coldef) ? row.caption : row.awpValue;
                            const excCaption = (is_tbl_coldef) ? row.excColdef : row.excValue;
            //console.log("....awpCaption", awpCaption);
            //console.log("....excCaption", excCaption);

                            if(!skip_linked_exc_row){
            // ---  if excColdef and excValue exist: append row to table ColLinked
                                //  append row to table Awp if excValue does not exist in items
                                // add linked row to linked table, add to awp / excel tab;le otherwise
                                let el_tbody = (row_is_linked) ? el_tbody_lnk : (key === "awp") ? el_tbody_awp : el_tbody_exc;

            // --- insert tblRow into tbody_lnk
                                let tblRow = el_tbody.insertRow(-1);
                                    tblRow.id = row_id;

                                    const row_key = (is_tbl_coldef) ? (key === "awp") ? row.awpColdef : row.excColdef :
                                                                      (key === "awp") ? row.awpBasePk : row.excValue;
                                    tblRow.setAttribute("data-key", row_key)

                                    tblRow.classList.add(row_cls)
                                    tblRow.classList.add(cls_width)
                                    tblRow.addEventListener("click", function(event) {Handle_AEL_row_clicked(event)}, false);

            // --- if new appended row: highlight row for 1 second
                                    const cls_just_linked_unlinked = (row_is_linked) ? "tsa_td_linked_selected" : "tsa_td_unlinked_selected";

                                    let show_justLinked = false;
                                    if(row_is_linked)  {
                                        show_justLinked = (!!JustLinkedAwpId && !!row_id && JustLinkedAwpId === row_id)
                                    } else  if (key === "awp") {
                                        show_justLinked = (!!JustUnLinkedAwpId && !!row_id && JustUnLinkedAwpId === row_id)
                                    } else {
                                        show_justLinked = (!!JustUnlinkedExcId && !!row_id && JustUnlinkedExcId === row_id)
                                    }
                                    if (show_justLinked) {
                                        let cell = tblRow.cells[0];
                                        tblRow.classList.add(cls_just_linked_unlinked)
                                        setTimeout(function (){  tblRow.classList.remove(cls_just_linked_unlinked)  }, 1000);
                                    }

            // --- append td with row.caption
                                    // row {awpKey: 2, caption: "PKL", excValue: "Omar TEST"}
                                    let td_first = tblRow.insertCell(-1);
                                    td_first.classList.add(row_cls)
                                    const text = (key === "awp") ? awpCaption : excCaption;
                                    td_first.innerText = text;

            // --- if new appended row: highlight row for 1 second
                                    if (show_justLinked) {
                                        //td_first.classList.add(cls_just_linked_unlinked)
                                        //setTimeout(function (){ td_first.classList.remove(cls_just_linked_unlinked)}, 1000);
                                        ShowClassWithTimeout(td_first, cls_just_linked_unlinked, 1000) ;
                                    }

            // --- if linked row: also append td with excValue
                                    if (row_is_linked) {
                                        let td_second = tblRow.insertCell(-1);
                                        td_second.classList.add(row_cls)
                                        td_second.innerText = excCaption;

            // --- if new appended row: highlight row for 1 second
                                        if (show_justLinked) {
                                           //td_second.classList.add(cls_just_linked_unlinked)
                                           //setTimeout(function (){  td_second.classList.remove(cls_just_linked_unlinked)  }, 1000);
                                           ShowClassWithTimeout(td_second, cls_just_linked_unlinked, 1000) ;
                                        }
                                    }
            // --- add mouseenter/mouseleave EventListener to tblRow
                                    const cls_linked_hover = (row_is_linked) ? "tsa_td_linked_hover" : "tsa_td_unlinked_hover";
                                        // cannot use pseudo class :hover, because all td's must change color, hover doesn't change children
                                    tblRow.addEventListener("mouseenter", function(event) {
                                        for (let i = 0, td; td = tblRow.children[i]; i++) {
                                            td.classList.add(cls_linked_hover)
                                    }});
                                    tblRow.addEventListener("mouseleave", function() {
                                        for (let i = 0, td; td = tblRow.children[i]; i++) {
                                            td.classList.remove(cls_linked_hover)
                                    }});
                            } //  if(!skip_linked_exc_row)
                        };  // for (let i = 0, row ; row = items[i]; i++)
                    };  // if(items){
                }  // for (let j = 0; j < 2; j++)
            }  // if(show_table)

        }  // if (el_tbody_awp && el_tbody_exc && el_tbody_lnk)
     }; // Fill_AEL_Table()

//=========   Handle_AEL_row_clicked   ======================
    function Handle_AEL_row_clicked(event) {
        // function gets row_clicked.id, row_other_id, row_clicked_key, row_other_key
        // sets class 'highlighted' and 'hover'
        // and calls 'LinkColumns' or 'UnlinkColumns'
        // currentTarget refers to the element to which the event handler has been attached
        // event.target which identifies the element on which the event occurred.
        //console.log("=========   Handle_AEL_row_clicked   ======================") ;

        if(!!event.currentTarget) {
            let tr_selected = event.currentTarget;
            let table_body_clicked = tr_selected.parentNode;
            const tbodyAEL = get_attr_from_el(table_body_clicked, "data-AEL");
            const tbodyTblName = get_attr_from_el(table_body_clicked, "data-table");
            const cls_selected = (tbodyAEL === "lnk") ? cls_linked_selected : cls_unlinked_selected;

            const row_clicked_id = tr_selected.id;
            const row_clicked_key = get_attr_from_el(tr_selected, "data-key");
            let row_other_id = null, row_other_key = null;

// ---  check if clicked row is already selected
            const tr_is_not_yet_selected = (!get_attr_from_el(tr_selected, "data-selected", false))
/*
        console.log("tbodyAEL", tbodyAEL) ;
        console.log("tbodyTblName", tbodyTblName) ;
        console.log("tr_selected", tr_selected) ;
        console.log("row_clicked_id", row_clicked_id) ;
        console.log("row_clicked_key", row_clicked_key) ;
        console.log("tr_is_not_yet_selected", tr_is_not_yet_selected) ;
*/
// ---  if tr_is_not_yet_selected: add data-selected and class selected, remove class selected from all other rows in this table
            const cls_linked_unlinked_hover = (tbodyAEL === "lnk") ? "tsa_td_linked_hover" : "tsa_td_unlinked_hover";
            for (let i = 0, row; row = table_body_clicked.rows[i]; i++) {
                if(tr_is_not_yet_selected && row === tr_selected){
                    row.setAttribute("data-selected", true);
                    for (let i = 0, td; td = row.children[i]; i++) {
                        td.classList.add(cls_selected)
                        td.classList.remove(cls_linked_unlinked_hover)};
                } else {
// ---  remove data-selected and class selected from all other rows in this table, also this row if already selected
                    row.removeAttribute("data-selected");
                    for (let i = 0, td; td = row.children[i]; i++) {
                        td.classList.remove(cls_selected);
                        td.classList.remove(cls_linked_unlinked_hover)};
                }
            }
// ---  only if clicked on tsa or exc row:
            if (["awp", "exc"].includes(tbodyAEL)) {
// ---  if clicked row was not yet selected: check if other table has also selected row, if so: link
                if(tr_is_not_yet_selected) {
// ---  check if other table has also selected row, if so: link
                    const other_tbodyAEL = (tbodyAEL === "awp") ? "exc" : "awp";
                    const id_tbody_other = "id_MIMP_tbody_" + tbodyTblName + "_" + other_tbodyAEL
                    let table_body_other = document.getElementById(id_tbody_other)
//console.log("tbodyTblName", tbodyTblName)
//console.log("id_tbody_other", id_tbody_other)
// ---  loop through rows of other table
                    let link_rows = false;
                    //for testing:
                    let row_other_caption = null;
                    for (let j = 0, row_other; row_other = table_body_other.rows[j]; j++) {
                       const other_tr_is_selected = get_attr_from_el(row_other, "data-selected", false)
        //console.log("other_tr_is_selected", other_tr_is_selected) ;
// ---  set link_rows = true if selected row is found in other table
                       if(other_tr_is_selected) {
                           link_rows = true;
                           row_other_id = get_attr_from_el(row_other, "id");
                           row_other_key = get_attr_from_el(row_other, "data-key");
                           row_other_caption = row_other.innerText;
                           break;
                        }
                    }

// ---  link row_clicked with delay of 250ms (to show selected Tsa and Excel row)
                    if (link_rows){
                        setTimeout(function () {
                            LinkColumns(tbodyTblName, tbodyAEL, row_clicked_id, row_other_id, row_clicked_key, row_other_key);
                        }, 250);
                    }
                }
            } else if (tr_is_not_yet_selected) {
// ---  unlink tr_selected  with delay of 250ms (to show selected Tsa and Excel row)
                setTimeout(function () {
                    UnlinkColumns(tbodyTblName, tbodyAEL, row_clicked_id, row_clicked_key);
                    }, 250);
            }
       }  // if(!!event.currentTarget) {
    };  // Handle_AEL_row_clicked

//========= LinkColumns  ===================================== PR2020-12-29
    function LinkColumns(tbodyTblName, tbodyAEL, row_clicked_id, row_other_id, row_clicked_key, row_other_key) {
        //console.log("==========  LinkColumns ========== ", tbodyTblName, tbodyAEL);
        // function adds 'excCol' to awp_columns and 'awpCaption' to excel_coldefs
        //console.log("row_clicked_id", row_clicked_id, "row_other_id", row_other_id);
        //console.log("row_clicked_key", row_clicked_key, "row_other_key", row_other_key);
        // row_clicked_id =  'id_tr_sector_exc_1'   row_other_id = 'id_tr_sector_awp_1'
        // row_clicked_key = 'EM'  row_other_key =  '5'

// --- get awp_row_id from row_clicked_id or row_other_id, depends on which row is clicked
        const awp_row_id = (tbodyAEL === "awp") ? row_clicked_id : (tbodyAEL === "exc") ? row_other_id : null;

// --- get awp / exc key. WHen tbl = 'coldef' key is coldef, otherwise excValue -= value and awpValue = awpBasePk
        // awp_row_key = '5'  excel_row_key  = 'EM'

        const awp_rows = (tbodyTblName === "coldef") ? mimp_stored.coldefs : mimp.linked_awp_values[tbodyTblName];
        const excel_rows = (tbodyTblName === "coldef") ? mimp.excel_coldefs : mimp.linked_exc_values[tbodyTblName];

        // awp_row = {awpColdef: "birthdate", caption: "Geboortedatum", datefield: true, excColdef: "GEB_DAT", excColIndex: 9}
        // awp_row = {awpBasePk: 5, awpValue: "e&m", excColIndex: 1, excValue: "EM"}
        const awp_key  = (tbodyTblName === "coldef") ? "awpColdef" :  "awpBasePk";
        const awp_row_key = (tbodyAEL === "awp") ? row_clicked_key : (tbodyAEL === "exc") ? row_other_key : null;
        const awp_row = get_arrayRow_by_keyValue (awp_rows, awp_key, awp_row_key);

        // excel_row = {excColIndex: 9, excColdef: "GEB_DAT", awpColdef: "birthdate", awpCaption: "Geboortedatum"}
        // excel_row = {excColIndex: 1, excValue: "EM", awpBasePk: 5, awpValue: "e&m"}
        const exc_key  = (tbodyTblName === "coldef") ? "excColdef" :  "excValue";
        const excel_row_key = (tbodyAEL === "awp") ? row_other_key : (tbodyAEL === "exc") ? row_clicked_key : null;
        const excel_row = get_arrayRow_by_keyValue (excel_rows, exc_key, excel_row_key);

        //console.log("awp_row",  awp_row);
        //console.log("excel_row", excel_row);
// --- add linked info to other row
        if(awp_row && excel_row){
            if(!!awp_row.awpColdef){excel_row.awpColdef = awp_row.awpColdef};
            if(!!awp_row.awpBasePk){excel_row.awpBasePk = awp_row.awpBasePk};
            if(!!awp_row.awpValue){excel_row.awpValue = awp_row.awpValue};
            if(!!awp_row.caption){excel_row.awpCaption = awp_row.caption};

            if(!!excel_row.excColdef){awp_row.excColdef = excel_row.excColdef};
            if(!!excel_row.excColIndex){awp_row.excColIndex = excel_row.excColIndex};
            if(!!excel_row.excValue){awp_row.excValue = excel_row.excValue};
        }

        //console.log("mimp.linked_awp_values",  deepcopy_dict(mimp.linked_awp_values));
        //console.log("mimp.linked_exc_values", deepcopy_dict(mimp.linked_exc_values));

        UploadImportSetting(tbodyTblName);

// ---  fill lists with linked values and update AEL-tables
        //FillExcelValueLists();
        Fill_AEL_Tables(awp_row_id);

        MIMP_HighlightAndDisableButtons();
    };  // LinkColumns

//========= UnlinkColumns ===================================== PR2020-12-29
    function UnlinkColumns(tbodyTblName, tbodyAEL, row_clicked_id, row_clicked_key) {
        //console.log("==========  UnlinkColumns ========== ", tbodyTblName, tbodyAEL);
        // function deletes attribute 'excColdef' from awp_columns
        // and deletes attributes 'awpColdef' and 'awpCaption' from excel_coldefs

        //console.log("row_clicked_id", row_clicked_id);
        //console.log("row_clicked_key", row_clicked_key);
        // row_clicked_id:   id_tr_level_awp_1
        // row_clicked_key:  '2' (awpBasePk)

        const awp_rows = (tbodyTblName === "coldef") ? mimp_stored.coldefs : mimp.linked_awp_values[tbodyTblName];
        const excel_rows = (tbodyTblName === "coldef") ? mimp.excel_coldefs : mimp.linked_exc_values[tbodyTblName];

        const JustUnLinkedAwpId = row_clicked_id;

        // in unlink: row_clicked_key = awpColdef
        // stored_coldef: {awpColdef: "examnumber", caption: "Examennummer", linkfield: true, excColdef: "exnr"}
        // excel_coldefs: {index: 1, excColdef: "exnr", awpColdef: "examnumber", awpCaption: "Examennummer"}
        let excel_row = null, JustUnlinkedExcId = null;
        //let awp_row = get_arrayRow_by_keyValue (awp_rows, "awpColdef", row_clicked_key);

        // awp_row = {awpColdef: "birthdate", caption: "Geboortedatum", datefield: true, excColdef: "GEB_DAT", excColIndex: 9}
        // awp_row = {awpBasePk: 5, awpValue: "e&m", excColIndex: 1, excValue: "EM"}
        const awp_key = (tbodyTblName === "coldef") ? "awpColdef" :  "awpBasePk";
        const awp_row = get_arrayRow_by_keyValue (awp_rows, awp_key, row_clicked_key);

        const exc_key = (tbodyTblName === "coldef") ? "excColdef" :  "excValue";
        // excel_row =  {index: 8, excColdef: "geboorte_land", awpColdef: "birthcountry", awpCaption: "Geboorteland"}
        if (!!awp_row && !!awp_row[exc_key]) {
// ---  look up excColdef in excel_coldefs
            excel_row = get_arrayRow_by_keyValue (excel_rows, exc_key, awp_row[exc_key])

        //console.log("awp_row", awp_row);
        //console.log("excel_row", excel_row);

// ---  delete excColdef, excColIndex, excValue from awp_row
             if(!!awp_row.excColdef){ delete awp_row.excColdef};
             if(!!awp_row.excColIndex){ delete awp_row.excColIndex};
             if(!!awp_row.excValue){ delete awp_row.excValue};

            if (!!excel_row) {
                //JustUnlinkedExcId = get_AEL_rowId(tbodyTblName, "exc", excel_row.excColIndex);
                JustUnlinkedExcId = excel_row.rowId;
// ---  delete awpColdef, awpBasePk, awpValue, caption from excel_row]
                if(!!excel_row.awpColdef){ delete excel_row.awpColdef};
                if(!!excel_row.awpBasePk){ delete excel_row.awpBasePk};
                if(!!excel_row.awpValue){ delete excel_row.awpValue};
                if(!!excel_row.awpCaption){ delete excel_row.awpCaption};
            }
        }  // if (!!awp_row)

// ---  upload new settings
        UploadImportSetting(tbodyTblName);

        //console.log("JustUnLinkedAwpId", JustUnLinkedAwpId);
        //console.log("JustUnlinkedExcId", JustUnlinkedExcId);
// ---  fill lists with linked values and update AEL-tables
        //FillExcelValueLists();
        Fill_AEL_Tables(null, JustUnLinkedAwpId, JustUnlinkedExcId);

        MIMP_HighlightAndDisableButtons();
    }  // UnlinkColumns

//========= UPLOAD  =====================================
    function UploadImportSetting (tbodyTblName) {
        //console.log ("==========  UploadImportSetting ========= tbodyTblName: ", tbodyTblName);


        let awp_rows = (tbodyTblName === "coldef") ? mimp_stored.coldefs : (mimp.linked_awp_values[tbodyTblName]) ? mimp.linked_awp_values[tbodyTblName] : null;
        //let excel_rows = (tbodyTblName === "coldef") ? mimp.excel_coldefs : (mimp.linked_exc_values[tbodyTblName]) ? mimp.linked_exc_values[tbodyTblName] : null;

        let upload_dict = {
            importtable: mimp_stored.import_table,
            sel_examyear_pk: mimp_stored.sel_examyear_pk,
            sel_schoolbase_pk: mimp_stored.sel_schoolbase_pk,
            sel_depbase_pk: mimp_stored.sel_depbase_pk
        };
        if (["workbook", "worksheetlist", "noheader", "select_unique"].includes(tbodyTblName)){
// ---  upload worksheetname and noheader
            if (mimp.curWorksheetName){
                upload_dict.worksheetname = mimp.curWorksheetName;
            }
            upload_dict.noheader = mimp.curNoHeader;

        } else if (tbodyTblName === "coldef"){
            let linked_row = {};
                // awp_row = {awpColdef: "examnumber", caption: "Examennummer", linkfield: true, excColdef: "exnr"}
            if (awp_rows){
            // also upload when linked_coldef is empty, to delete existing links from database
                for (let i = 0, row; row = awp_rows[i]; i++) {
                    if(row.awpColdef && row.excColdef){
                        linked_row[row.awpColdef] = row.excColdef;
                    }
                }
            };
            // upload_dict = { importtable: "student", coldef: {code: "abbrev", name: "name"} }
            upload_dict.coldef = linked_row;

        } else  if (["department", "level", "sector", "profiel", "subject", "subjecttype"].includes(tbodyTblName)){
            //console.log("tbodyTblName", tbodyTblName)
            let linked_values = {};
            if (awp_rows){
                for (let i = 0, row; row = awp_rows[i]; i++) {
                    // row = {awpBasePk: 5, awpValue: "e&m", excColIndex: 1, excValue: "EM"}
                    if(!!row.excValue && !!row.awpBasePk){
                        linked_values[row.excValue] = row.awpBasePk;
                    }
                }
            };
            // also upload when linked_values is empty, to delete existing links from database
            // linked_values = {CM: 4, EM: 5}
            //console.log("linked_values", linked_values)
            upload_dict[tbodyTblName] = linked_values;
        };

        if (!isEmpty(upload_dict)){
            const parameters = {"upload": JSON.stringify (upload_dict)};
            const el_data = document.getElementById("id_MIMP_data")
            const url_str = get_attr_from_el(el_data, "data-url_import_settings_upload");

            //console.log("url_str", url_str)
            //console.log("upload_dict", upload_dict)

            let response = "";
            $.ajax({
                type: "POST",
                url: url_str,
                data: parameters,
                dataType:'json',
                success: function (response) {
                    //console.log("UploadImportSetting response: ", response);
                    //if ("schoolsetting_dict" in response) { i_UpdateSchoolsettingsImport(response.schoolsetting_dict) };

                },
                error: function (xhr, msg) {
                    console.log(msg + '\n' + xhr.responseText);
                }
            });  // $.ajax
        };

    }; // function (UploadImportSetting)

//========= i_UpdateSchoolsettingsImport  ================ PR2020-04-17 PR2021-01-12
    function i_UpdateSchoolsettingsImport(schoolsetting_dict){
        //console.log("===== i_UpdateSchoolsettingsImport ===== ")
        //console.log("schoolsetting_dict", deepcopy_dict(schoolsetting_dict))

        let import_table = null;
        if (!isEmpty(schoolsetting_dict)){
            if("import_student" in schoolsetting_dict ){
                import_table = "import_student";
            } else if("import_subject" in schoolsetting_dict ){
                import_table = "import_subject";
            } else if("import_studsubj" in schoolsetting_dict ){
                import_table = "import_studsubj";
            } else if("import_grade" in schoolsetting_dict ){
                import_table = "import_grade";
            } else if("import_permit" in schoolsetting_dict ){
                import_table = "import_permit";
            } else if("import_username" in schoolsetting_dict ){
                import_table = "import_username";
            }
        };

        const import_table_dict = schoolsetting_dict[import_table];
        //console.log("import_table_dict", import_table_dict)
        mimp_stored = deepcopy_dict(import_table_dict);
        mimp_stored.import_table = import_table;

        mimp_stored.sel_examyear_pk = schoolsetting_dict.sel_examyear_pk;
        mimp_stored.sel_examyear_code = schoolsetting_dict.sel_examyear_code;
        mimp_stored.sel_schoolbase_pk = schoolsetting_dict.sel_schoolbase_pk;
        mimp_stored.sel_schoolbase_code = schoolsetting_dict.sel_schoolbase_code;
        mimp_stored.sel_depbase_pk = schoolsetting_dict.sel_depbase_pk;
        mimp_stored.sel_depbase_code = schoolsetting_dict.sel_depbase_code;
        mimp_stored.sel_school_pk = schoolsetting_dict.sel_school_pk;
        mimp_stored.sel_school_name = schoolsetting_dict.sel_school_name;

        //console.log("mimp_stored", mimp_stored)
    }  // i_UpdateSchoolsettingsImport

    function UploadData(url_str, upload_dict, RefreshDataRowsAfterUpload){
        //console.log ("==========  UploadData ==========");
        //console.log("url_str", url_str);
        //console.log("upload_dict", upload_dict);

// --- reset logfile
        mimp_logfile = []

        const parameters = {"upload": JSON.stringify (upload_dict)};
        $.ajax({
            type: "POST",
            url: url_str,
            data: parameters,
            dataType:'json',
            success: function (response) {
                console.log( "response");
                console.log(response);

//--------- hide loader
                add_or_remove_class(document.getElementById("id_MIMP_loader"), cls_hide, true);

                if("subject_list" in response){
                    const subject_list = response.subject_list;
                    FillDataTableAfterUpload(subject_list, worksheet_range);
                }

                if("updated_student_rows" in response){
                    RefreshDataRowsAfterUpload(response);
                };

                if("updated_studsubj_rows" in response){
                    RefreshDataRowsAfterUpload(response);
                };

                if("updated_user_rows" in response){
                console.log("RefreshDataRowsAfterUpload >>> updated_user_rows");
                    RefreshDataRowsAfterUpload(response);
                };
                if("result" in response){
                    ResponseResult(response);
                };

//--------- print log file
                if("log_list" in response){
                    mimp_logfile = response.log_list;
                };
            },
            error: function (xhr, msg) {

//--------- hide loading gif
                add_or_remove_class(document.getElementById("id_MIMP_loader"), cls_hide, true)

                console.log(msg + '\n' + xhr.responseText);

            }  // error: function (xhr, msg) {
        });


    }; //  UploadData

    function ResponseResult(response) {
        //console.log ("==========  ResponseResult ==========");
        //console.log("response", response);
        const result = (response.result) ? response.result : null;
        const is_test = (response.is_test) ? response.is_test : false;
        const table = (response.table) ? response.table : null;

        //console.log("result", result);
        //console.log("is_test", is_test);
        //console.log("table", table);
        add_or_remove_class(document.getElementById("id_MIMP_loader"), cls_hide, true);

        const el_MIMP_msg_container = document.getElementById("id_MIMP_msg_container");
        add_or_remove_class(el_MIMP_msg_container, cls_hide, false)
        //console.log("el_MIMP_msg_container", el_MIMP_msg_container);

        const el_MIMP_result_container = document.getElementById("id_MIMP_result_container");
        el_MIMP_result_container.innerHTML = result;
        el_MIMP_result_container.classList.remove(cls_hide)

        mimp.is_tested = true;
        MIMP_HighlightAndDisableButtons();

    }

//========= END UploadData =====================================

//=====import CSV file ===== PR2020-04-16
    // TODO add csv filetype
    // from https://www.quora.com/What-is-the-best-way-to-read-a-CSV-file-using-JavaScript-not-JQuery
    function UploadCSV() {
        var fileUpload = document.getElementById("fileUpload");
        var regex = /^([a-zA-Z0-9\s_\\.\-:])+(.csv|.txt)$/;
        // shouldnt it be const regex = RegExp('foo*');
        // see https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/RegExp/test
        if (regex.test(fileUpload.value.toLowerCase())) {
            if (typeof (FileReader) != "undefined") {
                var reader = new FileReader();
                reader.onload = function (e) {
                    var table = document.createElement("table");
                    var rows = e.target.result.split("\n");
                    for (var i = 0; i < rows.length; i++) {
                        var row = table.insertRow(-1);
                        var cells = rows[i].split(",");
                        for (var j = 0; j < cells.length; j++) {
                            var cell = row.insertCell(-1);
                            cell.innerHTML = cells[j];
                        }
                    }
                    var dvCSV = document.getElementById("dvCSV");
                    dvCSV.innerHTML = "";
                    dvCSV.appendChild(table);
                }
                reader.readAsText(fileUpload.files[0]);
            } else {
                alert("This browser does not support HTML5.");
            }
        } else {
            alert("Please upload a valid CSV file.");
        }
    }  // UploadCSV

// ============================ FUNCTIONS ============================ PR2021-01-12

//========= has_awpKeys =====================================
    function has_awpKeys_NIU(){
//  ---  loop through excel_coldefs to get linked awpKeys
        let has_awpKeys = false
        if(!!excel_coldefs){
            for (let i = 0, col; col = excel_coldefs[i]; i++) {
                const awpKey = get_dict_value(col, ["awpKey"])
                if (!!awpKey){
                    has_awpKeys = true
                    break;
        }}}
        return has_awpKeys;
    }

//=========  detect_dateformat  ================ PR2020-06-04
    function detect_dateformat(dict_list, col_index_index_list){
        //console.log(' --- detect_dateformat ---')
        //console.log('col_index_index_list: ' + col_index_index_list)
        // detect date format PR2019-08-05  PR2020-06-04

        let arr00_max = 0
        let arr01_max = 0
        let arr02_max = 0
        let dateformat = null;
        if(dict_list){
            for (let i = 0, dict; i < dict_list.length; i++) {
                dict = dict_list[i];
            //console.log('dict: ' + dict)
                for (let j = 0, col_index; j < col_index_index_list.length; j++) {
                    col_index = col_index_index_list[j];
                    let arr00 = 0, arr01 = 0, arr02 = 0
                    const date_string = dict[col_index];
                    if (date_string) {
                        let arr = get_array_from_ISOstring(date_string)
    // - skip when date has an unrecognizable format
                        let isok = false;
                        if (arr.length > 2){
                            if (Number(arr[0])) {
                                arr00 = Number(arr[0]);
                                if(Number(arr[1])) {
                                    arr01 = Number(arr[1]);
                                    if (Number(arr[2])){
                                        arr02 = Number(arr[2]);
                                        isok = true;
                        }}}};
    // ---  get max values
                        if (isok){
                            if (arr00 > arr00_max){arr00_max = arr00};
                            if (arr01 > arr01_max){arr01_max = arr01};
                            if (arr02 > arr02_max){arr02_max = arr02};
            }}}};
    // ---  get position of year and day
            let year_pos = -1, day_pos = -1;
            if (arr00_max > 31 && arr01_max <= 31 && arr02_max <= 31){
                year_pos = 0;
                if (arr01_max > 12 && arr02_max <= 12){
                    day_pos = 1;
                } else if (arr02_max > 12 && arr01_max <= 12){
                    day_pos = 2
                }
            } else if (arr02_max > 31 && arr00_max <= 31 && arr01_max <= 31) {
                year_pos = 2;
                if (arr00_max > 12 && arr01_max <= 12){
                    day_pos = 0;
                } else if (arr01_max > 12 && arr00_max <= 12){
                    day_pos = 1;
            }};
            if (day_pos === -1){
                if (year_pos === 0){
                    day_pos = 2
                } else if (year_pos === 2) {
                    day_pos = 0
            }};
    // ---  format
            if (year_pos > -1 && day_pos > -1){
                if (year_pos === 0 && day_pos === 2){
                    dateformat = 'yyyy-mm-dd'
                } else if (year_pos === 2){
                    if (day_pos === 0){
                        dateformat = 'dd-mm-yyyy'
                    } else if (day_pos === 1) {
                        dateformat = 'mm-dd-yyyy'
            }}};
        }
        return dateformat;
    }  // detect_dateformat

//=========  i_get_name_from_fullanme  ================ PR2021-01-12
    function i_get_name_from_fullanme(input_value){
        //console.log("==== i_get_name_from_fullanme  =========>> ");
        let last_name = null, first_name = null, prefix = null;
        const full_name = (input_value) ? input_value.trim() : null
        if (full_name) {
            const pos_comma = full_name.indexOf(",");
            // if name contains a comma, structure is: prefix lastname, firstname OR  lastname, firstname prefix
            if(pos_comma > -1 ){
                last_name = input_name.slice(0, pos_comma)

    //  check if there is a prefix in front of last_name
                let has_prefix = false, name_remainder = null, prefix = null;
                if(last_name){
                    const arr = i_split_prefix_from_name(last_name, false); // false = don't split_from_first_name
                    has_prefix = arr[0];
                    name_remainder = arr[1];
                    prefix = arr[2];
                }
                first_name = input_name.slice(pos_comma);
                if(first_name){ first_name = first_name.trim();
    //  check if there is a prefix at the end of first_name
                if(!has_prefix && first_name){
                    const arr = i_split_prefix_from_name(first_name, true);  // true = split_from_first_name
                    has_prefix = arr[0];
                    name_remainder = arr[1];
                    prefix = arr[2];
                }
            } else {
    // if name does not have a comma, structure is: firstname prefix lastname

            }
            }  // if(pos_int > -1 ){
        } else {
            last_name = full_name
        }  //  if (full_name && full_name.includes(","){
        return [last_name]
    }  // i_get_name_from_fullanme


//=========  i_split_prefix_from_name  ================ PR2021-01-12
    function i_split_prefix_from_name(input_value, split_from_first_name){
        //console.log("==== i_split_prefix_from_name  =========>> ");
        // PR2016-04-01 aparte functie van gemaakt
        //Functie splitst tussenvoegsel voor Achternaam (IsPrefix=True) of achter Voornamen (IsPrefix=False)

        let name_remainder = null, prefix = null, has_prefix = false;
        const prefix_dict_before = {
            2: ["d'", "l'"],
            3: ["al ", "d' ", "da ", "de ", "do ", "el ", "l' ", "la ", "le ", "te "],
            4: ["del ", "den ", "der ", "dos ", "ten ", "ter ", "van "],
            6: ["de la "],
            7: ["van de ", "van 't "],
            8: ["van den ", "van der "],
            9: ["voor den "]
         }
        const prefix_dict_after = {
            2: ["d'", "l'"],
            3: [" al", " d'", " da", " de", " do", " el", " l'", " la", " le", " te"],
            4: [" del", " den", " der", " dos", " ten", " ter", " van"],
            6: [" de la"],
            7: [" van de", " van 't"],
            8: [" van den", " van der"],
            9: [" voor den"]
         }
        const prefix_dict = (split_from_first_name)  ? prefix_dict_after : prefix_dict_before;
        let remainder_name = (input_value) ? input_value.trim() : null
        if (input_name){
        //Achternaam met tussenvoegsel ervoor
            //van groot naar klein, anders wordt 'van den' niet bereikt, maar 'den' ingevuld
            for (let len = 9; len > 1; len--) {
                let first_part = (!split_from_first_name) ? input_name.slice(0, len) : input_name.slice( len * -1) ;
                // get prefixes with length = len
                if( len in prefix_dict) {
                    const prefix_list = prefix_dict[len];
                    // check if first_part is in prefix_list
                    if (prefix_list && prefix_list.includes(first_part)){
                        // remove trailing space from first_part
                        prefix = first_part.trim();
                        remainder_name = input_name.slice(len);
                        has_prefix = true;
                        break;
                    }
                }
            }  // for (let len = 9; len > 1; len--)
            if(!is_found){
                remainder_name = input_name;
            }
        }
        return [has_prefix, name_remainder, prefix];
    }  // i_split_prefix_from_name