// PR2020-12-03 added
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
    let mimp_loc = {};
    // PR2002-12-26 these variables are used to get info from student.js into this file. Any better solution?
    let mimp_setting_dict = {};

    let department_map = new Map();
    let level_map = new Map();
    let sector_map = new Map();

    // MIME xls: application/vnd.ms-excel
    // MIME xlsx: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    // MIME csv: text/csv
     const excelMIMEtypes = {
            xls: "application/vnd.ms-excel",
            xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        };

//####################################################################
// +++++++++++++++++ MODAL IMPORT ++++++++++++++++++++
//=========  MIMP_Open  ================ PR2020-12-03
    function MIMP_Open(tblName) {
        console.log( "===== MIMP_Open ========= ");
        console.log( "mimp_stored", mimp_stored);

        Object.keys(mimp).forEach(function(key,index) {
            // from https://stackoverflow.com/questions/8312459/iterate-through-object-properties
            // key: the name of the object key, index: the ordinal position of the key within the object
            mimp[key] = null;
        });
        mimp.table = tblName
        const el_filedialog = document.getElementById("id_MIMP_filedialog");
        //PR2020-12-05. THis one doesn't work: if(el_filedialog){el_filedialog.files = null};
        if(el_filedialog){el_filedialog.value = null};

        // default value of el_MIMP_hasheader is 'true'
        const el_MIMP_hasheader = document.getElementById("id_MIMP_hasheader");
        if(el_MIMP_hasheader){el_MIMP_hasheader.checked = true};

        //PR2020-10-28 debug: modal gives 'NaN' and 'undefined' when  loc not back from server yet
        if (!isEmpty(mimp_loc)) {
            //mod_dict = {base_id: setting_dict.requsr_schoolbase_pk, table: tblName};
            document.getElementById("id_MIMP_header").innerText = mimp_loc.Upload_candidates;
            document.getElementById("id_MIMP_filedialog_label").innerText = "A. " + mimp_loc.Select_Excelfile_with_students;
            document.getElementById("id_MIMP_upload_label").innerText = mimp_loc.Upload_candidates;

            MIMP_btnSelectClicked("btn_step1");

// ---  fill select table
            //ModSelSchOrDep_FillSelectTable(tblName, 0);  // 0 = selected_pk
// ---  show modal
            $("#id_modimport").modal({backdrop: true});
            }

    }  // MIMP_Open

//####################################################################

//=========   HandleFiledialog   ======================
    function HandleFiledialog(el_filedialog) { // functie wordt alleen doorlopen als file is geselecteerd
        //console.log(" ========== HandleFiledialog ===========");

        mimp.excel_coldefs = [];
        mimp.excel_dateformat = null;
        mimp.has_linked_datefields = false;
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
        //mimp_stored.coldef = [];

// ---  get curfiles from filedialog
        // curfiles is list of files: PR2020-04-16
        // curFiles[0]: {name: "tsa_import_orders.xlsx", lastModified: 1577989274259, lastModifiedDate: Thu Jan 02 2020 14:21:14 GMT-0400 (Bolivia Time) {}
       // webkitRelativePath: "", size: 9622, type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}, length: 1}

        let curFiles = el_filedialog.files; //This one doesn't work in Firefox: let curFiles = event.target.files;

// ---  validate selected file
        let curFile = null, msg_err = null
        if(curFiles.length === 0) {
            msg_err = mimp_loc.Select_valid_Excelfile;
        } else if(!is_valid_filetype(curFiles[0])) {
            msg_err = mimp_loc.Not_valid_Excelfile + " " + mimp_loc.Only + ".xls " + mimp_loc.and + ".xlsx" + mimp_loc.are_supported;
        } else {
            curFile = curFiles[0];
        }

// ---  display error message when error
        let el_msg_err = document.getElementById("id_MIMP_msg_filedialog")
        el_msg_err.innerText = msg_err;
        show_hide_element(el_msg_err, (!!msg_err));

        GetWorkbook(curFile);
    }  // HandleFiledialog

//=========  GetWorkbook  ====================================
    function GetWorkbook(curFile) {
        //console.log("======  GetWorkbook  =====");
        // curWorkbook.SheetNames = ["Sheet2", "Compleetlijst", "Sheet1"]
        // curWorkbook.Sheets = { Sheet1: {!margins: {left: 0.7, right: 0.7, top: 0.75, bottom: 0.75, header: 0.3, …},
        //                                 !ref: "A1"
        //                                 A1: {t: "s", v: "test", r: "<t>test</t>", h: "test", w: "test"}, ... }

        mimp.sel_file = curFile;
        if(curFile){
            let reader = new FileReader();
            mimp.curWorkbook = null;
            let rABS = false; // false: readAsArrayBuffer,  true: readAsBinaryString
            if (rABS) {
                reader.readAsBinaryString(curFile);
            } else {
                reader.readAsArrayBuffer(curFile);}
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
                if (curFile.type === excelMIMEtypes.xls){
                    mimp.curWorkbook = XLS.read(data, {type: rABS ? "binary" : "array"});
                } else {
                    mimp.curWorkbook = XLSX.read(data, {type: rABS ? "binary" : "array"});
                }
    // ---  make list of worksheets in workbook
                if (mimp.curWorkbook){
                    mimp.curWorkSheets = mimp.curWorkbook.Sheets;
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
    // ---  fill table excel_coldefs
                                    FillExcelColdefArray();
    // ---  fill lists with linked values
                                    FillExcelValueLists();
    // ---  fill link-tables column, department, level, sector
                                    Fill_AEL_Tables();
    // ---  fill DataTable
                                    FillDataTable();
                                    UpdateDatatableHeader();
    // ---  upload new settings awpCaption
                                    UploadImportSetting ("workbook");
                    }}}}
                    let el_msg_err = document.getElementById("id_msg_worksheet")
                    el_msg_err.innerText = msg_err;
                    show_hide_element(el_msg_err, (!!msg_err));
                }  // if (!!workbook){
                // PR2020-04-16 debug: must be in reader.onload, will not be reached when ik HandleFiledialog
                MIMP_HighlightAndDisableButtons();
            }; // reader.onload = function(event) {
        }; // if(!!mimp.selected_file){
    }  // function GetWorkbook())

//=========  MIMP_SelectWorksheet   ======================
    function MIMP_SelectWorksheet() {
        console.log(" ========== MIMP_SelectWorksheet ===========");
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
                        FillExcelValueLists();
    // ---  fill link-tables column, department, level, sector
                        Fill_AEL_Tables();
    // ---  fill DataTable
                        FillDataTable();
                        UpdateDatatableHeader();
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
            FillExcelValueLists();
            Fill_AEL_Tables();

// ---  fill tables with linked values
            //const JustLinkedValueAwpId = null, JustUnlinkedValueAwpId = null, JustUnlinkedValueExcId = null;
            //FillValueLinkTables(JustLinkedValueAwpId, JustUnlinkedValueAwpId, JustUnlinkedValueExcId);

// ---  fill DataTable
            FillDataTable();
            UpdateDatatableHeader();
            // upload new settings awpCaption
            UploadImportSetting ("noheader");
        }  // if(mimp.curWorkSheet){
    }; //MIMP_CheckboxHasheaderChanged

//=========  FillExcelColdefArray  ===========
    function FillExcelColdefArray() {
        //console.log("=========  FillExcelColdefArray ========= ");
        // function - creates list mimp.excel_coldefs: [{index: idx, excColdef: colName}, ...]
        //          - loops through stored_coldef and excel_coldefs and add links and caption in these arrays
        // stored_coldef: [ {awpColdef: "idnumber", caption: "ID nummer", excColdef: "ID"}, 1: ...]
        // excel_coldefs: [ {index: 10, excColdef: "ID", awpColdef: "idnumber", awpCaption: "ID nummer"}} ]

        // function is called by GetWorkbook, MIMP_SelectWorksheet, MIMP_CheckboxHasheaderChanged
        let colindex;
        let itemlist = [];
        mimp.excel_coldefs = [];
        mimp.excel_dateformat = null;
        mimp.has_linked_datefields = false;

// ---  create array 'excel_coldefs' with Excel column names, replaces spaces, ", ', /, \ and . with _
        const range = mimp.curWorksheetRange

        if(mimp.curWorkSheet && range) {
// ---  get headers if Not SelectedSheetHasNoHeader: from first row, otherwise: F01 etc ");
            let row_number = range.StartRowNumber;
            for (let col_number = range.StartColNumber, idx = 0, colName = ""; col_number <= range.EndColNumber; ++col_number){
                if (mimp.curNoHeader){
                    const index = "00" + col_number;
                    colName = "F" + index.slice(-2);
                } else {
                    const cellName = GetCellName (col_number,row_number);
                    const excColdef = GetExcelValue(mimp.curWorkSheet, cellName, "w");
                    colName = replaceChar(excColdef);
                }
                mimp.excel_coldefs.push ({excColIndex: idx, excColdef: colName});
                idx += 1;
        }}

// ---  loop through array stored_coldef
//console.log("mimp_stored.coldef", mimp_stored.coldef)
        if(mimp_stored.coldef) {
            for (let i = 0, stored_row; stored_row = mimp_stored.coldef[i]; i++) {
                let is_linked = false;
                // when table = 'column': awpColdef = field name "examnumber" etc
                // when table = department, level or sector: awpColdef = base_id
                if (!!stored_row.awpColdef && !!stored_row.excColdef){
// ---  check if excColdef also exists in excel_coldefs
                    let excel_row_byKey = get_arrayRow_by_keyValue(mimp.excel_coldefs, "excColdef", stored_row.excColdef);
// ---  if excColdef is found in excel_coldefs: add awpColdef and awpCaption to excel_row
                    if (!!excel_row_byKey){
                        excel_row_byKey.awpColdef = stored_row.awpColdef;
                        excel_row_byKey.awpCaption = stored_row.caption;
                        is_linked = true;
                    } else {
// ---  if excColdef is not found in excel_coldefs remove excColdef from stored_row
                        delete stored_row.excColdef;
                }}
// ---  if column not linked, check if awpCaption and Excel name are the same, if so: link anyway
                if (!is_linked){
                    let excel_row_byCaption = get_arrayRow_by_keyValue (mimp.excel_coldefs, "excColdef", stored_row.caption)
                    if (!!excel_row_byCaption){
                        stored_row.excColdef = excel_row_byCaption.excColdef;
                        excel_row_byCaption.awpColdef = stored_row.awpColdef;
                        excel_row_byCaption.awpCaption = stored_row.caption;
                        is_linked = true;
                }}
            };
        }
        // TODO:
        // ---  detect dateformat of fields: 'datefirst', 'datelast' PR2020-06-04
        // has_linked_datefields and excel_dateformat are global variables, are set in GetExcelDateformat
        //GetExcelDateformat(["datefirst", "datelast"]);

    }  // FillExcelColdefArray

//=========  fill worksheet_data  ========================================================================
    function FillWorksheetData() {
    // fills the list 'worksheet_data' with data from 'worksheet'
        let sheet_data = [];
        const range = mimp.curWorksheetRange;
        if(range){
            let row_index = range.StartRowNumber;
            // skip first row when first row is header row
            if (!mimp.curNoHeader) {row_index += 1};
            for (; row_index <= range.EndRowNumber; row_index++){
                let NewRow = [];
                for (let col_index = range.StartColNumber; col_index <= range.EndColNumber; col_index++){
                    let CellName = GetCellName (col_index, row_index);
                    let CellValue = GetExcelValue(mimp.curWorkSheet, CellName,"w");
                    NewRow.push (CellValue);
                };
                sheet_data.push (NewRow);
            }
        }
        return sheet_data;
    }  // FillWorksheetData

//=========  FillDataTable  ========================================================================
    function FillDataTable() {
        //console.log("=========  function FillDataTable =========");
//--------- delete existing rows
        const tblHead = document.getElementById("id_MIMP_thead_data");
        const tblBody = document.getElementById("id_MIMP_tbody_data");
        tblHead.innerText = null;
        tblBody.innerText = null;

        const range = mimp.curWorksheetRange;
        const no_excel_data = (! mimp.curWorksheetData || !mimp.excel_coldefs || !range);
        if (!no_excel_data){
//--------- insert tblHead row of datatable
            let tblHeadRow = tblHead.insertRow();
            //PR2017-11-21 debug: error when StartColNumber > 1, j must start at 0
            //var EndIndexPlusOne = (sheet_range.EndColNumber) - (sheet_range.StartColNumber -1)
            //index j goes from 0 to ColCount-1, excel_coldefs index starts at 0, last index is ColCount-1
            for (let j = 0 ; j < range.ColCount; j++) {
                let cell = tblHeadRow.insertCell(-1);
                let excKey = mimp.excel_coldefs[j].excKey;
                cell.innerHTML = excKey;
                cell.setAttribute("id", "idTblCol_" + excKey);
            };
// ---  insert DataSet rows
            let LastRowIndex = range.RowCount -1;
            // worksheet_data has no header row, start allways at 0
            if (!mimp.curNoHeader) { LastRowIndex -= 1;}
            //if (EndRow-1 < EndRowIndex) { EndRowIndex = EndRow-1;};
// ---  insert row
            for (let i = 0; i <= LastRowIndex; i++) {
                let tblRow = tblBody.insertRow(-1);
                tblRow.setAttribute("data-row_index", tblRow.rowIndex );
// ---  alternate row background color
                const class_background = (i%2 === 0) ? cls_cell_unchanged_even : cls_cell_unchanged_odd;
                tblRow.classList.add(class_background);
// ---  insert cells
                for (let j = 0 ; j < range.ColCount; j++) {
                    let cell = tblRow.insertCell(-1);
                    if(!!mimp.curWorksheetData[i][j]){
                        cell.innerHTML = mimp.curWorksheetData[i][j];
                    };
                } //for (let j = 0; j < 2; j++)
            } //for (let i = 0; i < 2; i++)
        }; // if(has_data){
    };  //  FillDataTable

//========= function UdateDatatableHeader  ====================================================
    function UpdateDatatableHeader() {
        //console.log("---------  function UpdateDatatableHeader ---------");
        //console.log("mimp.excel_coldefs", mimp.excel_coldefs);
        //----- set awpCaption in linked header colomn of datatable
//----- loop through array excel_coldefs from row index = 0
        for (let i = 0, excel_column; excel_column = mimp.excel_coldefs[i]; i++) {
            // only rows that are not linked are added to tblColExcel
            const awpCaption = excel_column.awpCaption;
            const excKey = excel_column.excKey;
            let theadCol = document.getElementById("idTblCol_" + excKey);
            theadCol.innerText = (!!awpCaption) ? awpCaption : excKey;

            add_or_remove_class(theadCol, cls_linked_selected, !!awpCaption);
            add_or_remove_class(theadCol, cls_unlinked_selected, !awpCaption);
        }
   } // function UpdateDatatableHeader

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
// console.log("ColNumber: " + ColNumber + " RowNumber: " + RowNumber);
        var col_name = "";
        if (ColNumber>0 && RowNumber>0){

            for (let exp=2; exp>=0; --exp){
                const divisor = Math.pow(26, exp);
                let dividend = ColNumber;
                // subtract 1 (otherwise 26=AA instead of Z, except for last character (exp=0)
                if (exp > 0 ){--dividend;};
// console.log("exp: " + exp + ", dividend: " + dividend +", divisor: " + divisor);
                const mod = Math.floor((dividend)/divisor);
                const frac = ColNumber - mod * divisor;
// console.log("mod: " + mod + ", frac: " + frac);
                if (mod>0){
                    col_name += String.fromCharCode(mod + 64);
                };// if (mod>0){
                ColNumber = frac;
            }; //for (let exp=2; exp>=0; --exp)
            col_name = col_name + RowNumber;
// console.log("col_name " + col_name);
        }; //if (ColNumber>0 && RowNumber>0)
        return col_name;
    }; //function GetCellName (ColIndex, RowIndex )

//========= GetExcelValue  ====================================
    // PR2017-11-04 from: https://stackoverflow.com/questions/2693021/how-to-count-javascript-array-objects
    function GetExcelValue(Sheet, CellName, ValType) {
// console.log("--------------GetExcelValue");
// console.log("GetExcelValue CellName: " + CellName + "ValType: " + ValType);
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
//console.log("result " + ValType + ": " + result);
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

//=========  GetExcelDateformat  ================ PR2020-06-04
    function GetExcelDateformatXXX(datefield_list){
        //console.log(" -----  GetExcelDateformat   ----")

// ---  detect dateformat of fields: 'datefirst', 'datelast'
        // has_linked_datefields and excel_dateformat are global variables
        mimp.has_linked_datefields = false;
        mimp.excel_dateformat = null;

        if (mimp.excel_coldefs){
            let field_index_list = [];
            for (let i = 0, coldef; coldef = mimp.excel_coldefs[i]; i++) {
                const fldName = get_dict_value(coldef, ["awpKey"])
                if(datefield_list.indexOf(fldName) > -1){
                    const excKey = get_dict_value(coldef, ["excKey"]);
                    if(excKey){
                        mimp.has_linked_datefields = true;
                        field_index_list.push(i)
            }}};
            if (mimp.has_linked_datefields){
                mimp.excel_dateformat = detect_dateformat(mimp.curWorksheetData, field_index_list)
            }
        }
    }  // GetExcelDateformat

//=========  GetTELrowId  ================ PR2020-04-18 PR2020-12-27
    function GetTELrowId(tblName, key, i){
        // function created row_id for table TSA-columns, Exc-columns and Lnk-columns
        // PR2020-12-27 was: return "id_tr_" + tblName  + "_" + i.toString();
        // tblName = columns, department, level, sector; key = awp. exc. lnk
        return "id_tr_" + tblName + "_" + key  + "_" + i.toString();
    }

//=========  MIMP_Selectdateformat  ================ PR2019-06-04
    function MIMP_Selectdateformat(el) {
        console.log( " ===== MIMP_Selectdateformat ========= ");

        const el_msg_dateformat = document.getElementById("id_msg_dateformat");
        add_or_remove_class(el_msg_dateformat, cls_visible_hide, el_select_dateformat.value)

        MIMP_HighlightAndDisableButtons();
    }  // MIMP_Selectdateformat

//=========  MIMP_btnPrevNextClicked  ================ PR2020-12-05
    function MIMP_btnPrevNextClicked(prev_next) {
        console.log("=== MIMP_btnPrevNextClicked ===", prev_next);

        let data_btn = mimp.sel_btn;
        if (prev_next === "next"){
            data_btn = (data_btn === "btn_step1") ? "btn_step2" :
                       (data_btn === "btn_step2") ? "btn_step3" : "btn_step4";
        } else if (prev_next === "prev"){
            data_btn = (data_btn === "btn_step4") ? "btn_step3" :
                       (data_btn === "btn_step3") ? "btn_step2" : "btn_step1";
        }
        MIMP_btnSelectClicked(data_btn);
    }

//=========  MIMP_btnSelectClicked  ================ PR2020-12-05
    function MIMP_btnSelectClicked(data_btn) {
        //console.log("=== MIMP_btnSelectClicked ===", data_btn);
        mimp.sel_btn = data_btn

// ---  show only the elements that are used in this mod_shift_option
        const el_MIMP_body = document.getElementById("id_MIMP_body")
        const els = el_MIMP_body.getElementsByClassName("btn_show");
        for (let i = 0, el; el = els[i]; i++) {
            const is_show = el.classList.contains(mimp.sel_btn)
            show_hide_element(el, is_show)
        }


// ---  highlight selected button
        MIMP_HighlightAndDisableButtons();
    }  // MIMP_btnSelectClicked

//=========  MIMP_HighlightAndDisableButtons  ================ PR2019-05-25
    function MIMP_HighlightAndDisableButtons() {
        //console.log("=== MIMP_HighlightAndDisableButtons ===");
        // el_MIMP_btn_prev and el_MIMP_btn_next don't exists when user has no permission

        const el_filedialog = document.getElementById("id_MIMP_filedialog");
        const el_MIMP_btn_prev = document.getElementById("id_MIMP_btn_prev");
        const el_MIMP_btn_next = document.getElementById("id_MIMP_btn_next");
        const el_worksheet_list = document.getElementById("id_MIMP_worksheetlist");
        const el_btn_mod_prev = document.getElementById("id_MIMP_btn_prev");
        const el_btn_mod_next = document.getElementById("id_MIMP_btn_next");

// ---  set mimp.sel_btn
        if(!mimp.sel_btn){ mimp.sel_btn = "btn_step1"};

// ---  check if unique field is linked
        const has_linked_identifier = MIMP_ValidateUniquefield()
// ---  check if there are date fields in mimp_stored.coldef
        const [datefields_awpKeys, datefields_caption] = MIMP_GetLinkedDatefields()
// ---  detect dateformat of datefields_awpKeys
        mimp.excel_dateformat = detect_dateformat(mimp.curWorksheetData, datefields_awpKeys)
        const has_linked_datefields = (!!mimp.excel_dateformat)

        // only show select format when has_linked_datefields and  excel_dateformat = null
        const show_select_dateformat = (has_linked_datefields && !mimp.excel_dateformat)
        const el_div_dateformat = document.getElementById("id_MIMP_div_dateformat");
        add_or_remove_class(el_div_dateformat, cls_hide, !show_select_dateformat)

        if(show_select_dateformat ){
            // only show error msg when when no format is selected
            const show_msg_err = (show_select_dateformat && !el_select_dateformat.value)
            const el_msg_dateformat = document.getElementById("id_MIMP_msg_dateformat");
            add_or_remove_class(el_msg_dateformat, cls_hide, !show_msg_err )
            if(show_msg_err){
                setTimeout(function() {el_select_dateformat.focus()}, 50);
            }
        }

        const no_worksheet_with_data = !(el_worksheet_list && el_worksheet_list.options && el_worksheet_list.options.length);
        const no_linked_columns =  !(mimp.excel_coldefs && mimp.excel_coldefs.length)
        const no_excel_data = !(mimp.curWorksheetData && mimp.curWorksheetData.length);
        const no_dateformat = ((no_excel_data) || (mimp.has_linked_datefields && !mimp.excel_dateformat && !el_select_dateformat.value))


        //console.log("no_identifier_linked", no_identifier_linked);
        const step2_disabled = (no_worksheet_with_data);
        const step3_disabled = (step2_disabled || no_linked_columns || !has_linked_identifier || no_excel_data);
        //const step4_disabled = (step3_disabled || el_select_code_calc.selectedIndex < 0 || no_dateformat);
        const step4_disabled = (step3_disabled || no_dateformat);

        const btn_prev_disabled = (mimp.sel_btn === "btn_step1")
        const btn_next_disabled = ( (mimp.sel_btn === "btn_step4") ||
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

// ---  make el_msg_novalidfile visible
        let el_msg_novalidfile = document.getElementById("id_msg_novalidfile");
        add_or_remove_class (el_msg_novalidfile, cls_hide, mimp.sel_file);

// ---  make id_MIMP_msg_link_unique visible
        let el_msg_link_unique = document.getElementById("id_MIMP_msg_link_unique");
        add_or_remove_class (el_msg_link_unique, cls_hide, has_linked_identifier);

// ---  focus on next element
        if (mimp.sel_btn === "btn_step1"){
            if (!mimp.sel_file) {
                if(el_filedialog){ el_filedialog.focus()};
            } else if (!mimp.curWorksheetName) {
                if(el_filedialog){ el_worksheet_list.focus()};
            } else {
                if(el_filedialog){ el_btn_mod_next.focus()};
            }
        } else if(mimp.sel_btn === "btn_step4"){
            //const el_MIMP_btn_test = document.getElementById("id_MIMP_btn_test");
            //const el_MIMP_btn_upload = document.getElementById("id_MIMP_btn_upload");
            //if(el_MIMP_btn_test){ el_MIMP_btn_test.focus()};
        }
    }  // MIMP_HighlightAndDisableButtons

//========= MIMP_ValidateUniquefield  ==================================== PR2020-12-06
    function MIMP_ValidateUniquefield() {
        //console.log("=== MIMP_ValidateUniquefield ===");
// ---  check if unique field is linked
        let has_linked_identifier = false, linkfields_caption = [];
        if(mimp_stored.coldef) {
            for (let i = 0, stored_row; stored_row = mimp_stored.coldef[i]; i++) {
                // stored_row = {awpKey: "examnumber", caption: "Examennummer", linkfield: true}
                if (stored_row.linkfield ) {
                    linkfields_caption.push(stored_row.caption);
                    if (stored_row.excColdef) {
                        has_linked_identifier = true;
        }}}};

        let msg_text = null;
        const len = linkfields_caption.length;
        if (len){
            if (len === 1) {
                msg_text = mimp_loc.linkunique_The_field + "'" + linkfields_caption[0] + "'" + mimp_loc.linkunique_mustbelinked_and_unique;
            } else {
                let fields_text = '';
                for (let i = 0, caption; caption = linkfields_caption[i]; i++) {
                    if(linkfields_caption[i]){
                        const caption = "'" + linkfields_caption[i] + "'";
                        if (!i){
                            fields_text = caption ;
                        } else if (i === len - 1){
                            fields_text += mimp_loc._or_ + caption;
                        } else {
                            fields_text += ", " + caption ;
                }}};
                msg_text = mimp_loc.linkunique_One_ofthe_fields + fields_text + mimp_loc.linkunique_mustbelinked_and_unique;
        }};
        if (msg_text){
            document.getElementById("id_MIMP_msg_link_unique").innerText = msg_text;
        }
        return has_linked_identifier;
    }

//========= MIMP_GetLinkedDatefields  ==================================== PR2020-12-06
    function MIMP_GetLinkedDatefields() {
// ---  get linked date fields from mimp_stored.coldef
        let datefields_awpKeys = [], datefields_caption = [];
        if(mimp_stored.coldef) {
            for (let i = 0, stored_row; stored_row = mimp_stored.coldef[i]; i++) {
                // stored_row = {awpKey: "examnumber", caption: "Examennummer", linkfield: true}

                // when table = 'column': awpKey = field name "examnumber" etc
                // when table = department, level or sector: awpKey = base_id
                if (stored_row.datefield && stored_row.excColdef){
                    datefields_awpKeys.push(stored_row.awpColdef);
                    datefields_caption.push(stored_row.caption);
        }}};
        if (datefields_awpKeys.length){
            mimp.excel_dateformat = detect_dateformat(mimp.curWorksheetData, datefields_awpKeys)
        }

        return [datefields_awpKeys, datefields_caption];
    }


//========= Fill_AEL_Tables  ====================================
    function Fill_AEL_Tables(JustLinkedAwpId, JustUnLinkedAwpId, JustUnlinkedExcId) {
        //console.log("==== Fill_AEL_Tables  =========>> ");
        //console.log("mimp_stored.coldef ", mimp_stored.coldef);
       // console.log("mimp.excel_coldefs ", mimp.excel_coldefs);

        const tbl_list = ["coldef", "department", "level", "sector"];
        for (let i = 0, tbodyTblName; tbodyTblName = tbl_list[i]; i++) {
            Fill_AEL_Table(tbodyTblName, JustLinkedAwpId, JustUnLinkedAwpId, JustUnlinkedExcId)
        }
    }  // Fill_AEL_Tables


//========= Fill_AEL_Table  ==================================== PR2020-12-29
    function Fill_AEL_Table(tbodyTblName, JustLinkedAwpId, JustUnLinkedAwpId, JustUnlinkedExcId) {
        //console.log("==== Fill_AEL_Table  ========= ", tbodyTblName);
        //console.log("mimp.linked_exc_values[tbodyTblName] ", deepcopy_dict(mimp.linked_exc_values[tbodyTblName]));

        // tbodyTblNames are: "coldef", "department", "level", "sector"

        // stored_coldef: [ {awpColdef: "examnumber", caption: "Examennummer", linkfield: true, excColdef: "exnr"}, ...]

        const is_tbl_coldef = (tbodyTblName === "coldef");

// ---  reset tables
        const el_tbody_awp = document.getElementById("id_MIMP_tbody_" + tbodyTblName + "_awp")
        const el_tbody_exc = document.getElementById("id_MIMP_tbody_" + tbodyTblName + "_exc")
        const el_tbody_lnk = document.getElementById("id_MIMP_tbody_" + tbodyTblName + "_lnk")
        el_tbody_awp.innerText = null
        el_tbody_exc.innerText = null
        el_tbody_lnk.innerText = null

        //const awp_rows = (tbodyTblName === "coldef") ? mimp_stored.coldef : mimp.linked_awp_values[tbodyTblName];
        //const awp_key  = (tbodyTblName === "coldef") ? "awpColdef" :  "awpBasePk";
        //const awp_row_key = (tbodyAEL === "awp") ? row_clicked_key : (tbodyAEL === "exc") ? row_other_key : null;
        //const awp_row = get_arrayRow_by_keyValue (awp_rows, awp_key, awp_row_key);

// ---  hide table department, level, sector when their column is not linked
        // lookup awpColdef 'department' etc in mimp_stored.coldef. If it exists: show table 'department' etc.
        const lookup_row = get_arrayRow_by_keyValue(mimp_stored.coldef, "awpColdef", tbodyTblName);
        // check if it is a linked column by checking if 'excColdef' exists in row
        const show_table = ( is_tbl_coldef || (!!lookup_row && "excColdef" in lookup_row) );

// --- hide tables that are not linked
        const el_container = document.getElementById("id_MIMP_container_" + tbodyTblName);
        if(el_container) {add_or_remove_class(el_container, cls_hide, !show_table)};

        if(show_table){
// ---  first loop through array of awp_columns, then through array of excel_coldefs
            // key: 0 = "awp", 1: "lnk" or "awp"
            for (let j = 0; j < 2; j++) {
                const key =  (!j) ? "awp" : "exc";
                const rows = (is_tbl_coldef) ? (!j) ? mimp_stored.coldef : mimp.excel_coldefs :
                                               (!j) ? mimp.linked_awp_values[tbodyTblName] : mimp.linked_exc_values[tbodyTblName];

            //console.log("----- tbodyTblName ", tbodyTblName, "key", key);
                if(rows){
                    for (let i = 0, row ; row = rows[i]; i++) {
                        // mimp_stored.coldef row = {awpColdef: "examnumber", caption: "Examennummer", linkfield: true, excColdef: "exnr"}
                        //                    row = {awpBasePk: 7, awpValue: "n&t", excColdef: "Profiel", excValue: "NT"}
                        // {awpBasePk: 5, awpValue: "e&m", excColdef: "Profiel", excValue: "EM"}
                        const row_id = GetTELrowId(tbodyTblName, key, i); // row_id: id_tr_level_exc_2
                        // add rowId to dict of this row
                        row.rowId = row_id;
                        // awp row is linked when it has an excColdef and excValue -> add to linked table
                        //const row_is_linked = (!!row.excColdef);
                        const row_is_linked = (is_tbl_coldef) ? (!j) ? !!row.excColdef : !!row.awpColdef :
                                                                (!j) ? !!row.excValue : !!row.awpBasePk;
                        const row_cls = (row_is_linked) ? cls_tbl_td_linked : cls_tbl_td_unlinked;
                        const cls_width = (row_is_linked) ? "tsa_tw_50perc" : "tsa_tw_100perc";
                        const row_awpBasePk = get_dict_value(row, ["awpBasePk"])

                        // dont add row when excel_row is linked (has awpBasePk)
                        // PR2020-12-27 debug: must use (!!j); (j) will return 0 instead of false;
                        // skip linked excel row, linked row is already added by key 'awp'
                        //const skip_linked_exc_row = (is_tbl_coldef) ? !!j && row_is_linked : (!!j && !!row_awpBasePk);
                        const skip_linked_exc_row = (!!j && row_is_linked)

                        const awpCaption = (is_tbl_coldef) ? row.caption : row.awpValue;
                        const excCaption = (is_tbl_coldef) ? row.excColdef : row.excValue;
/*
        if(tbodyTblName === "sector" &&  key === "awp") {
            console.log("........... ");
            console.log("row ", row);
            console.log("row_is_linked ", row_is_linked);
            console.log("row_awpBasePk ", row_awpBasePk);
            console.log("row_awpBasePk ", row_awpBasePk);
            console.log("skip_linked_exc_row ", skip_linked_exc_row);
            console.log("awpCaption ", awpCaption);
            console.log("excCaption ", excCaption);
        }
*/
                        if(!skip_linked_exc_row){
        // ---  if excColdef and excValue exist: append row to table ColLinked
                            //  append row to table Tsa if excValue does not exist in items
                            // add linked row to linked table, add to awp / excel tab;le otherwise
                            let el_tbody = (row_is_linked) ? el_tbody_lnk : (!j) ? el_tbody_awp : el_tbody_exc;

        // --- insert tblRow into tbody_lnk
                            let tblRow = el_tbody.insertRow(-1);
                                tblRow.id = row_id;

                                const row_key = (is_tbl_coldef) ? (!j) ? row.awpColdef : row.excColdef :
                                                                  (!j) ? row.awpBasePk : row.excValue;
                                tblRow.setAttribute("data-key", row_key)

                                tblRow.classList.add(row_cls)
                                tblRow.classList.add(cls_width)
                                tblRow.addEventListener("click", function(event) {Handle_AEL_row_clicked(event)}, false);

        // --- if new appended row: highlight row for 1 second
                                const cls_just_linked_unlinked = (row_is_linked) ? "tsa_td_linked_selected" : "tsa_td_unlinked_selected";

                                let show_justLinked = false;
                                if(row_is_linked)  {
                                    show_justLinked = (!!JustLinkedAwpId && !!row_id && JustLinkedAwpId === row_id)
                                } else  if (!j) {
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
                                // row {awpKey: 2, caption: "PKL", excKey: "Omar TEST"}
                                let td_first = tblRow.insertCell(-1);
                                td_first.classList.add(row_cls)
                                const text = (!j) ? awpCaption : excCaption;
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
     }; // Fill_AEL_Table()

//========= has_awpKeys =====================================
    function has_awpKeys(){
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

//=========   Handle_AEL_row_clicked   ======================
    function Handle_AEL_row_clicked(event) {
        // function gets row_clicked.id, row_other_id, row_clicked_key, row_other_key
        // sets class 'highlighted' and 'hover'
        // and calls 'LinkColumns' or 'UnlinkColumns'
        // currentTarget refers to the element to which the event handler has been attached
        // event.target which identifies the element on which the event occurred.
        console.log("=========   Handle_AEL_row_clicked   ======================") ;

        if(!!event.currentTarget) {
            let tr_selected = event.currentTarget;
            let table_body_clicked = tr_selected.parentNode;
            const tbodyAEL = get_attr_from_el(table_body_clicked, "data-AEL");
            const tbodyTblName = get_attr_from_el(table_body_clicked, "data-table");
            const cls_selected = (tbodyAEL === "lnk") ? cls_linked_selected : cls_unlinked_selected;

        console.log("tbodyAEL", tbodyAEL) ;

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
            if (["awp", "exc"].indexOf(tbodyAEL) > -1) {
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
        console.log("==========  LinkColumns ========== ", tbodyTblName, tbodyAEL);
        // function adds 'excCol' to awp_columns and 'awpCaption' to excel_coldefs
        console.log("row_clicked_id", row_clicked_id, "row_other_id", row_other_id);
        console.log("row_clicked_key", row_clicked_key, "row_other_key", row_other_key);
        // row_clicked_id =  'id_tr_sector_exc_1'   row_other_id = 'id_tr_sector_awp_1'
        // row_clicked_key = 'EM'  row_other_key =  '5'

// --- get awp_row_id from row_clicked_id or row_other_id, depends on which row is clicked
        const awp_row_id = (tbodyAEL === "awp") ? row_clicked_id : (tbodyAEL === "exc") ? row_other_id : null;

// --- get awp / exc key. WHen tbl = 'coldef' key is coldef, otherwise excKey -= value and awpKey = awpBasePk
        // awp_row_key = '5'  excel_row_key  = 'EM'

        const awp_rows = (tbodyTblName === "coldef") ? mimp_stored.coldef : mimp.linked_awp_values[tbodyTblName];
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

// --- add linked info to other row
        if(!!awp_row && !!excel_row){
            if(!!awp_row.awpColdef){excel_row.awpColdef = awp_row.awpColdef};
            if(!!awp_row.awpBasePk){excel_row.awpBasePk = awp_row.awpBasePk};
            if(!!awp_row.awpValue){excel_row.awpValue = awp_row.awpValue};
            if(!!awp_row.caption){excel_row.awpCaption = awp_row.caption};

            if(!!excel_row.excColdef){awp_row.excColdef = excel_row.excColdef};
            if(!!excel_row.excColIndex){awp_row.excColIndex = excel_row.excColIndex};
            if(!!excel_row.excValue){awp_row.excValue = excel_row.excValue};
        }


        console.log("mimp.linked_awp_values",  deepcopy_dict(mimp.linked_awp_values));
        console.log("mimp.linked_exc_values", deepcopy_dict(mimp.linked_exc_values));

        UploadImportSetting(tbodyTblName);

// ---  fill lists with linked values and update AEL-tables
        FillExcelValueLists();
        Fill_AEL_Tables(awp_row_id);

        UpdateDatatableHeader();
        MIMP_HighlightAndDisableButtons();
    };  // LinkColumns

//========= UnlinkColumns ===================================== PR2020-12-29
    function UnlinkColumns(tbodyTblName, tbodyAEL, row_clicked_id, row_clicked_key) {
        console.log("==========  UnlinkColumns ========== ", tbodyTblName, tbodyAEL);
        // function deletes attribute 'excColdef' from awp_columns
        // and deletes attributes 'awpColdef' and 'awpCaption' from excel_coldefs

        console.log("row_clicked_id", row_clicked_id);
        console.log("row_clicked_key", row_clicked_key);
        // row_clicked_id:   id_tr_level_awp_1
        // row_clicked_key:  '2' (awpBasePk)

        const awp_rows = (tbodyTblName === "coldef") ? mimp_stored.coldef : mimp.linked_awp_values[tbodyTblName];
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
            console.log("awp_row[exc_key]", awp_row[exc_key]);
            console.log("excel_row", excel_row);
            console.log("excel_row.excColIndex", excel_row.excColIndex);

// ---  delete excColdef, excColIndex, excValue from awp_row
             if(!!awp_row.excColdef){ delete awp_row.excColdef};
             if(!!awp_row.excColIndex){ delete awp_row.excColIndex};
             if(!!awp_row.excValue){ delete awp_row.excValue};

            if (!!excel_row) {
                JustUnlinkedExcId = GetTELrowId(tbodyTblName, "exc", excel_row.excColIndex);
// ---  delete awpColdef, awpBasePk, awpValue, caption from excel_row]

                if(!!excel_row.awpColdef){ delete excel_row.awpColdef};
                if(!!excel_row.awpBasePk){ delete excel_row.awpBasePk};
                if(!!excel_row.awpValue){ delete excel_row.awpValue};
                if(!!excel_row.awpCaption){ delete excel_row.awpCaption};

            }
        }  // if (!!awp_row)

console.log("mimp.linked_awp_values[tbodyTblName];", deepcopy_dict(mimp.linked_awp_values[tbodyTblName]));
console.log("mimp.linked_exc_values[tbodyTblName];", deepcopy_dict(mimp.linked_exc_values[tbodyTblName]));


// ---  upload new settings
        UploadImportSetting(tbodyTblName);

// ---  fill lists with linked values and update AEL-tables
        FillExcelValueLists();
        Fill_AEL_Tables(null, JustUnLinkedAwpId, JustUnlinkedExcId);

        UpdateDatatableHeader();
        MIMP_HighlightAndDisableButtons();
    }  // UnlinkColumns


//========= UPLOAD SETTING COLUMNS =====================================
    function UploadImportSetting (tbodyTblName) {
        console.log ("==========  UploadImportSetting ========= tbodyTblName: ", tbodyTblName);
        let awp_rows = (tbodyTblName === "coldef") ? mimp_stored.coldef : (mimp.linked_awp_values[tbodyTblName]) ? mimp.linked_awp_values[tbodyTblName] : null;
        //let excel_rows = (tbodyTblName === "coldef") ? mimp.excel_coldefs : (mimp.linked_exc_values[tbodyTblName]) ? mimp.linked_exc_values[tbodyTblName] : null;

        let upload_dict = {
            importtable: mimp_stored.import_table,
            sel_schoolbase_pk: mimp_stored.sel_schoolbase_pk,
            sel_examyear_pk: mimp_stored.sel_examyear_pk
        };
        if (["workbook", "worksheetlist", "noheader"].indexOf(tbodyTblName) > -1){
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

        } else  if (["department", "level", "sector"].indexOf(tbodyTblName) > -1){
            console.log(">>>>>>>>>> tbodyTblName", tbodyTblName)
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
            console.log("linked_values", linked_values)
            upload_dict[tbodyTblName] = linked_values;
        };

        if (!isEmpty(upload_dict)){
            const parameters = {"upload": JSON.stringify (upload_dict)};
            const el_data = document.getElementById("id_MIMP_data")
            const url_str = get_attr_from_el(el_data, "data-importsettings_upload_url");

            console.log("url_str", url_str)
            console.log("upload_dict", upload_dict)

            let response = "";
            $.ajax({
                type: "POST",
                url: url_str,
                data: parameters,
                dataType:'json',
                success: function (response) {
                    console.log("UploadImportSetting response: ", response);

                    //if ("schoolsetting_dict" in response) { i_UpdateSchoolsettingsImport(response.schoolsetting_dict) };



                },
                error: function (xhr, msg) {
                    console.log(msg + '\n' + xhr.responseText);
                }
            });  // $.ajax
        };
    }; // function (UploadImportSetting)

//========= i_UpdateSchoolsettingsImport  ================ PR2020-04-17
    function i_UpdateSchoolsettingsImport(schoolsetting_dict){
        console.log("===== i_UpdateSchoolsettingsImport ===== ")
        console.log("schoolsetting_dict", deepcopy_dict(schoolsetting_dict))

        let import_table = null;
        if (!isEmpty(schoolsetting_dict)){
            if("import_student" in schoolsetting_dict ){
                import_table = "import_student";
            } else if("import_subject" in schoolsetting_dict ){
                import_table = "import_subject";
            }
        };
        const import_table_dict = schoolsetting_dict[import_table];
        mimp_stored = deepcopy_dict(import_table_dict)

        mimp_stored.sel_schoolbase_pk = get_dict_value(schoolsetting_dict, ["sel_schoolbase_pk"]);
        mimp_stored.sel_examyear_pk = get_dict_value(schoolsetting_dict, ["sel_examyear_pk"]);
        mimp_stored.import_table = import_table;
/*
        mimp_stored.worksheetname = get_dict_value(schoolsetting_dict, [import_table, "worksheetname"])
        mimp_stored.noheader = get_dict_value(schoolsetting_dict, [import_table, "noheader"])
        mimp_stored.coldef = get_dict_value(schoolsetting_dict, [import_table, "coldef"])
        mimp_stored.department = get_dict_value(schoolsetting_dict, [import_table, "department"])
        mimp_stored.level = get_dict_value(schoolsetting_dict, [import_table, "level"])
        mimp_stored.sector = get_dict_value(schoolsetting_dict, [import_table, "sector"])
*/
        console.log("mimp_stored", mimp_stored)
    }  // i_UpdateSchoolsettingsImport

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
    }

//========= UPLOAD DATA =====================================
    function MIMP_Save(mode, setting_dict){
        console.log ("==========  MIMP_Save ==========");
        const is_test_upload = (mode === "test")
        let rowLength = 0, colLength = 0;
        if(mimp.curWorksheetData){rowLength = mimp.curWorksheetData.length;};
        if(mimp_stored.coldef){colLength = mimp_stored.coldef.length;};
        if(rowLength > 0 && colLength > 0){

console.log ("mimp.excel_coldefs", deepcopy_dict(mimp.excel_coldefs));
console.log ("mimp.linked_exc_values", deepcopy_dict(mimp.linked_exc_values));

//  ---  loop through excel_coldefs to get linked awpColdefs
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
                    // rowindex is index of tablerow. Index 0 is header, therefore rowindex starts with 1
                    let dict = {rowindex: i};
                    for (let j = 0, exc_col; exc_col = mimp.excel_coldefs[j]; j++) {
                        const awpColdef = exc_col.awpColdef;

                        if (awpColdef){
                            let value = (row[j]) ? row[j] : null;
                            let mapped_value = null;
                            if (["department", "level", "sector"].indexOf(awpColdef) > -1){
                // mimp.linked_exc_values = { sector: [ {excColIndex: 0, excValue: "CM", awpBasePk: 4, awpValue: "c&m", rowId: "id_tr_sector_exc_0"}]

                // ---  check if value exists in linked_exc_values
                                const linked_values = mimp.linked_exc_values[awpColdef];
                                const excel_row = get_arrayRow_by_keyValue(linked_values, "excValue", value);
                // ---  if found: replace excel_value by base_id, that is stored in mimp.linked_exc_values
                                if(excel_row && "awpBasePk" in excel_row){
                                    mapped_value = excel_row.awpBasePk;
                                }
                            } else {
                                mapped_value = value
                            }
                            dict[awpColdef] = mapped_value;
                        }
                    }; //for (let col = 1 ; col <colLength; col++)
                    dict_list.push(dict);
                }

                if(!dict_list || !dict_list.length){
                    alert("No data found")
                } else {
// --- Upload Data
                    const el_data = document.getElementById("id_MIMP_data");
                    const url_str = get_attr_from_el(el_data, "data-importdata_upload_url");
                    const request = {sel_examyear_pk: mimp_setting_dict.sel_examyear_pk,
                                    sel_schoolbase_pk: mimp_setting_dict.sel_schoolbase_pk,
                                    sel_depbase_pk: mimp_setting_dict.sel_depbase_pk,
                    importtable: mimp.table,
                                     awpColdef_list: awpColdef_list,
                                     test: is_test_upload,
                                     data_list: dict_list
                                     }

                    UploadData(url_str, request);
                }
            }
        };
    }

//========= UPLOAD DATA =====================================
    function UploadData(url_str, request){
        console.log ("==========  UploadData ==========");
        console.log("url_str", url_str);
        console.log("request", request);

// --- show loader
        document.getElementById("id_MIMP_loader").classList.remove(cls_visible_hide)

        const parameters = {"upload": JSON.stringify (request)};
        $.ajax({
            type: "POST",
            url: url_str,
            data: parameters,
            dataType:'json',
            success: function (response) {
                console.log( "response");
                console.log(response);

//--------- hide loading gif
                document.getElementById("id_MIMP_loader").classList.add(cls_visible_hide)
                if("subject_list" in response){
                    const subject_list = response.subject_list;
                    FillDataTableAfterUpload(subject_list, worksheet_range);
                }

//--------- print log file
                const log_list = get_dict_value(response, ["logfile"])
                if (!!log_list && log_list.length > 0) {
                    printPDFlogfile(log_list, "log_import_subjects")
                }
            },
            error: function (xhr, msg) {

//--------- hide loading gif
                document.getElementById("id_MIMP_loader").classList.add(cls_visible_hide)

                console.log(msg + '\n' + xhr.responseText);
                //alert(msg + '\n' + xhr.responseText);
            }  // error: function (xhr, msg) {
        });


    }; //  UploadData
//========= END UploadData =====================================


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

//=========  FillExcelValueLists  ================ PR2020-12-26
    function FillExcelValueLists(){
        console.log("@@@@@@@@@@@==== FillExcelValueLists  =========>> ");
        // mimp_stored.coldef = {awpKey: "examnumber", caption: "Examennummer", linkfield: true, excKey: "exnr"}
        // excel_column = {index: 1, excKey: "exnr", awpKey: "examnumber", awpCaption: "Examennummer"}
        // function fills mimp.linked_exc_values with excel_values of department, level and sector

// mimp.excel_coldefs = [ {excColIndex: 1, excColdef: "exnr", awpColdef: "examnumber", awpCaption: "Examennummer", rowId: "id_tr_coldef_exc_1"}

        const awp_col_names = ["department", "level", "sector"];
// ---  loop through list of excel_coldefs
        if(mimp.excel_coldefs){
            for (let i = 0, row; row = mimp.excel_coldefs[i]; i++) {
                const awpColdef = row.awpColdef;
                const excColIndex = row.excColIndex;
                const excColdef = row.excColdef;

// ---  only add to value_list when  table 'department', 'level', 'sector' is linked
                const add_to_list = (awpColdef && awp_col_names.includes(awpColdef))
                if(add_to_list) {

// ---  add awpColdef dict to mimp.linked_awp_values
                    // sector: [ {awpBasePk: 4, awpValue: "c&m", rowId: "id_tr_sector_awp_0"}
                    //           {awpBasePk: 5, awpValue: "e&m", excColdef: "Profiel", excValue: "EM", rowId: "id_tr_sector_awp_1"}
                    //mimp.linked_awp_values[awpColdef] = deepcopy_dict(mimp_stored[awpColdef]);
                    mimp.linked_awp_values[awpColdef] = mimp_stored[awpColdef];

// ---  loop through curWorksheetData, create a list of excel values and add to mimp.linked_exc_values
                    // excel_value_list = ["EM", "NT", "CM"]
                    let excel_value_list = [];
                    if(mimp.curWorksheetData){
                        for (let i = 0, data_row; data_row = mimp.curWorksheetData[i]; i++) {
                            // data_row: ["576", "112", "Regales", .... , "NT", "4", "40", "21", "W4"]
// ---  get value of column with index 'excColIndex' and add value to excel_value_list if it doesn't yet exist in this list
                            const value = data_row[excColIndex];
                            if (value && !excel_value_list.includes(value)) {
                                excel_value_list.push(value)
                            }
                        };
                    }

                    if (excel_value_list.length){

// ---  sort the excel_value_list
                        // from https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/sort
                        excel_value_list.sort(function (a, b) {return a.localeCompare(b);});

// ---  convert the excel_value_list to a dict_list, add linked awpValue and
                        const dict_list = []
                        for (let j = 0, excel_value; excel_value = excel_value_list[j]; j++) {
                            const exc_dict = {excColIndex: j, excValue: excel_value}

            // lookup excel_value in mimp_stored awpColdef
                            if(mimp_stored[awpColdef]){
                                for (let x = 0, awp_dict; awp_dict = mimp_stored[awpColdef][x]; x++) {
                                if (awp_dict){

            // if is linked value (when excValue exists in awp_dict): add awpBasePk and awpValue to exc_dict
                                    if (awp_dict.excValue) {
                                        if (awp_dict.excValue.toLowerCase() === excel_value.toLowerCase() ){
                                            if(awp_dict.awpBasePk){ exc_dict.awpBasePk = awp_dict.awpBasePk }
                                            if(awp_dict.awpValue){ exc_dict.awpValue = awp_dict.awpValue }

                                        }
                                    } else if (awp_dict.awpValue && excel_value) {
            //TODO this is not working properly yet. Links again when clicked on unlink  PR2020-12-31
            // if not a linked value: check if awpValue and excValue are the same. If so: add to linked list
                     //console.log("awp_dict.awpValue", awp_dict.awpValue, "excel_value", excel_value);
                                        // skip when already linked
                                        //let awp_val_stripped = awp_dict.awpValue.toLowerCase()
                                        //awp_val_stripped = awp_val_stripped.replaceAll("&", "");
                                        //awp_val_stripped = awp_val_stripped.replaceAll(" ", "");
                                        //awp_val_stripped = awp_val_stripped.replaceAll("-", "");

                                       // let exc_val_stripped = excel_value.toLowerCase()
                                        //exc_val_stripped = exc_val_stripped.replaceAll("&", "");
                                        //exc_val_stripped = exc_val_stripped.replaceAll(" ", "");
                                        //exc_val_stripped = exc_val_stripped.replaceAll("-", "");
                                        //if (awp_val_stripped && exc_val_stripped && awp_val_stripped === exc_val_stripped){
                                        // add to exc_dict when stripped values are the same
                                        //    if(awp_dict.awpBasePk){ exc_dict.awpBasePk = awp_dict.awpBasePk }
                                        //    if(awp_dict.awpValue) {exc_dict.awpValue = awp_dict.awpValue};
                                        // also add to awp_dict
                                       //     if(excColdef){ awp_dict.excColdef = excColdef }
                                       //     awp_dict.excValue = excel_value
                                       // }
                                    }
                                }

                                }
                            }
                            dict_list.push(exc_dict)
                        }
// ---  add the dict_list to mimp.linked_exc_values
                        // mimp.linked_exc_values = { sector: [ {excColIndex: 0, excValue: "CM"},
                        //                                      {excColIndex: 1, excValue: "EM"},
                        //                                      {excColIndex: 2, excValue: "NT"} ] }
                        mimp.linked_exc_values[awpColdef] = dict_list
                        console.log("mimp.linked_exc_values", deepcopy_dict(mimp.linked_exc_values));
                        console.log("mimp.linked_awp_values", deepcopy_dict(mimp.linked_awp_values));
                    }
                }
            }
        }
        //console.log("mimp.linked_exc_values", deepcopy_dict(mimp.linked_exc_values));
    }  // FillExcelValueLists
