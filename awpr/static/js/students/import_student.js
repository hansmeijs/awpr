//var file_types = {
//    xls:"application/vnd.ms-excel",
//    xlsx:"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"};

$(document).ready(function() {

// set global variables
    var div_info = document.getElementById('div_infoID');
    var para = document.createElement('p');

    var file_dialog = document.getElementById("filedialogID");
    file_dialog.addEventListener("change", handle_file_dialog, false);

    var worksheet_list = document.getElementById("SheetListID");
    worksheet_list.addEventListener("change", handle_worksheet_list, false);

    var checkbox_noheader = document.getElementById("checkBoxID");
    checkbox_noheader.addEventListener("change", handle_checkbox_noheader_changed) //, false);

    // add a click listener to rows of TableExcel TableAwp TableLinked
    // // EAL: Excel Awp Linked table
    //document.getElementById("id_exc_table_col").addEventListener("click", handle_EAL_row_clicked);
    //document.getElementById("id_awp_table_col").addEventListener("click", handle_EAL_row_clicked);
    //document.getElementById("id_lnk_table_col").addEventListener("click", handle_EAL_row_clicked);

    // get the url of the `StudentImportAwpcoldefView` view
    const upload_student_mapping_url = $("#btn_import").data("upload_student_mapping_url");

    var selected_file = null;
    var workbook;
    var worksheet;
    var worksheet_range;
    var worksheet_data = [];

    // get the mapped_coldefs from data-tag in btn_import
    var selected_no_header = false;
    var stored_worksheetname = "";
    var stored_columns = {};
    var stored_levels;
    var stored_sectors;

    var excel_columns = [];
    var excel_levels = [];
    var excel_sectors = [];

    const stored_settings = $("#btn_import").data("mapped_coldefs");
console.log("stored_settings: " , stored_settings);

    if (stored_settings.hasOwnProperty("no_header")){selected_no_header = !!stored_settings.no_header;}
    if (stored_settings.hasOwnProperty("worksheetname")){stored_worksheetname = stored_settings.worksheetname;}
    if (stored_settings.hasOwnProperty("mapped_coldef_list")){stored_columns = stored_settings.mapped_coldef_list;}
    if (stored_settings.hasOwnProperty("mapped_level_list")){stored_levels = stored_settings.mapped_level_list;}
    if (stored_settings.hasOwnProperty("mapped_sector_list")){stored_sectors = stored_settings.mapped_sector_list;}

    var selected_worksheetname = stored_worksheetname;

    var file_types = {
        xls:"application/vnd.ms-excel",
        xlsx:"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    };


//=========   handle_file_dialog   ======================
    function handle_file_dialog() { // functie wordt alleen doorlopen als file is geselecteerd
//console.log(" ========== handle_file_dialog ===========");
        var curFiles = file_dialog.files; //This one doesn't work in Firefox: var curFiles = event.target.files;

        selected_file = null;
        excel_columns = [];
        worksheet_data = [];

        if(curFiles.length === 0) {
            para.textContent = 'No file is currently selected';
        } else {
            if(!is_valid_filetype(curFiles[0])) {
                para.textContent = 'File name ' + curFiles[0].name + ': Not a valid file type. Update your selection.';
            } else {
                selected_file = curFiles[0];
                para.textContent = 'File name: '+ selected_file.name ;
            }
        }

        div_info.appendChild(para);

        Get_Workbook(selected_file);
    }

//=========  handle_worksheet_list   ======================
    function handle_worksheet_list() {
console.log(" ========== handle_worksheet_list ===========");
        if(!!workbook){
            if(!!worksheet_list.value){
                selected_worksheetname = worksheet_list.value;

//---------  get selected worksheet
                worksheet = workbook.Sheets[selected_worksheetname];
                if(!!worksheet){
//--------- get Column and Rownumber of upper left cell and lower right cell of SheetRange
                    worksheet_range = GetSheetRange (worksheet);
                    if (!!worksheet_range) {

//--------- set checkbox_noheader checked
                        checkbox_noheader.checked = selected_no_header;

//--------- fill worksheet_data with data from worksheet
                        worksheet_data = FillWorksheetData(worksheet, worksheet_range, selected_no_header);

//--------- fill table excel_columns
                        Fill_Excel_Items("col");
                        CreateMapTableWrap("col");

                        Fill_Excel_Items("lvl");
                        CreateMapTableWrap("lvl");

                        Fill_Excel_Items("sct");
                        CreateMapTableWrap("sct");

//--------- fill DataTable
                        FillDataTable(worksheet_range);
                        UpdateDatatableHeader();

                        // upload new settings awpCaption
                        UpdateSettings ();
            }}}
        }  // if(!!workbook)
    }  // function handle_worksheet_list()

//=========   handle_checkbox_noheader_changed   ======================
    function handle_checkbox_noheader_changed() {
console.log(" ========== handle_checkbox_noheader_changed ===========");
        if(!!worksheet && !!worksheet_range) {
            selected_no_header = checkbox_noheader.checked;

//--------- fill worksheet_data with data from worksheet
            worksheet_data = FillWorksheetData(worksheet, worksheet_range, selected_no_header);

//--------- fill table excel_columns
            Fill_Excel_Items("col");
            CreateMapTableWrap("col");

            Fill_Excel_Items("lvl");
            CreateMapTableWrap("lvl");

            Fill_Excel_Items("sct");
            CreateMapTableWrap("sct");

//--------- fill DataTable
            FillDataTable(worksheet_range);
            UpdateDatatableHeader();

            // upload new settings awpCaption
            UpdateSettings ();

        }  // if(!!worksheet){
    }; //handle_checkbox_noheader_changed

//=========   handle_EAL_row_clicked   ======================
    function handle_EAL_row_clicked(e) {  //// EAL: Excel Awp Linked table
        // function gets row_clicked.id, row_other_id, row_clicked_key, row_other_key
        // sets class 'highlighted' and 'hover'
        // and calls 'linkColumns' or 'unlinkColumns'
// currentTarget refers to the element to which the event handler has been attached
// event.target which identifies the element on which the event occurred.
console.log("=========   handle_EAL_row_clicked   ======================") ;
console.log("e.target.currentTarget.id", e.currentTarget.id) ;

        if(!!e.target && e.target.parentNode.nodeName === "TR") {
            let cur_table = e.currentTarget; // id_col_table_awp
            // extract 'col' from 'id_col_table_awp'
            const tableName = cur_table.id.substring(3,6); //'col', 'sct', 'lvl'
            // extract 'awp' from 'id_col_table_awp'
            const tableBase = cur_table.id.substring(13); //'exc', 'awp', 'lnk'
//console.log("tableBase ", tableBase, "tableName: ", tableName) ;

            let row_clicked =  e.target.parentNode;
            let row_clicked_key = "";
            if(row_clicked.hasAttribute("key")){
                row_clicked_key = row_clicked.getAttribute("key");
            }
//console.log("row_clicked.id: <",row_clicked.id, "> row_clicked_key: <",row_clicked_key, ">");

            let table_body_clicked = document.getElementById(row_clicked.parentNode.id);

            let link_rows = false;
            let row_other_id = "";
            let row_other_key = "";

            if((tableName === "exc")|| (tableName === "awp") ) {
                const cls_hl = "c_colAwpExcel_highlighted";
                const cls_hv = "c_colAwpExcel_hover";

                if(row_clicked.classList.contains(cls_hl)) {
                    row_clicked.classList.remove(cls_hl, cls_hv);
                } else {
                    row_clicked.classList.add(cls_hl);
                    // remove clas from all other rows in theis table
                    for (let i = 0, row; row = table_body_clicked.rows[i]; i++) {
                        if(row === row_clicked){
                            row.classList.add(cls_hl);
                        } else {
                            row.classList.remove(cls_hl, cls_hv);
                        }
                    }

                // check if other table has also selected row, if so: link
                    let tableName_other;
                    if(tableName === "exc") {tableName_other = "awp"} else {tableName_other = "exc"}
                    let row_other_tbody_id = "id_" + tableName_other + "_tbody_" + tableBase;
//console.log("row_other_tbody_id",row_other_tbody_id)
                    let table_body_other = document.getElementById(row_other_tbody_id);
//console.log("table_body_other",table_body_other)
                    for (let j = 0, row_other; row_other = table_body_other.rows[j]; j++) {
                       if(row_other.classList.contains(cls_hl)) {
                           link_rows = true;
                           if(row_other.hasAttribute("id")){row_other_id = row_other.getAttribute("id");}
                           if(row_other.hasAttribute("key")){row_other_key = row_other.getAttribute("key");}
                           break;
                        }
                    }
                    // link row_clicked with delay of 250ms (to show selected Awp and Excel row)
                    if (link_rows){
//console.log("row_other_id: <",row_other_id, "> row_other_key: <",row_other_key, ">");
                        setTimeout(function () {
                            linkColumns(tableBase, tableName, row_clicked.id, row_other_id, row_clicked_key, row_other_key);
                        }, 250);
                    }
                }

            } else if (tableName === "lnk") {
                const cls_hl = "c_colLinked_highlighted";
                const cls_hv = "c_colLinked_hover";

                if(row_clicked.classList.contains(cls_hl)) {
                    row_clicked.classList.remove(cls_hl, cls_hv);
                } else {
                    row_clicked.classList.add(cls_hl);
                   // remove clas from all other rows in theis table
                    for (let i = 0, row; row = table_body_clicked.rows[i]; i++) {
                        if(row === row_clicked){
                            row.classList.add(cls_hl);
                        } else {
                            row.classList.remove(cls_hl);
                        }
                    }
                    // unlink row_clicked  with delay of 250ms (to show selected Awp and Excel row)
                    setTimeout(function () {
                        unlinkColumns(tableBase, tableName, row_clicked.id, row_clicked_key);
                        }, 250);
       }}}
    };  // handle_EAL_row_clicked

//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//                 ExcelFile_Read
//+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  Get_Workbook  ====================================
    function Get_Workbook(sel_file) {
        //* download the data using jQuery.post( url [, data ] [, success ] [, dataType ] ) PR2017-10-29 uit: https://api.jquery.com/jquery.post/
       if(!!sel_file){
// console.log("sel_file.name" + sel_file.name );
            var reader = new FileReader();
            var rABS = false; // false: readAsArrayBuffer,  true: readAsBinaryString
            if (rABS) {reader.readAsBinaryString(sel_file);} else {reader.readAsArrayBuffer(sel_file);}
           // PR2017-11-08 debug: reader.onload didn't work when reader.readAsBinaryString was placed after reader.onload

            // PR2018-12-09 debug: leave functions that depend on reading file within onload.
            // This way code executing stops till loading has finished.
            // Otherwise use Promise. See: https://javascript.info/promise-basics
            reader.onload = function(event) {
                var data = event.target.result;

                if(!rABS) { data = new Uint8Array(data);}
                switch (sel_file.type) {
                    case file_types.xls:
                        workbook = XLS.read(data, {type: rABS ? "binary" : "array"});
                        break;
                    default:
                        workbook = XLSX.read(data, {type: rABS ? "binary" : "array"});
                }

//--------- make list of worksheets in workbook
                if (!!workbook){
    // reset worksheet_list.options
                    worksheet_list.options.length = 0;
    // give message when workbook has no worksheets, reset selected_worksheetname
                    if(workbook.SheetNames.length === 0) {
                        selected_worksheetname = "";
                        para.textContent = "There are no worksheets." ;
                        div_info.appendChild(para);
                    } else {
    // fill worksheet_list.options with sheets that are not empty
                        for (let x=0; x<workbook.SheetNames.length; ++x){
                            const sheetname = workbook.SheetNames[x];
    // if workbook.SheetNames[x] has range: add to worksheet_list
                            if (SheetHasRange(workbook.Sheets[sheetname])) {
                                let option = document.createElement("option");
                                option.value = sheetname;
                                option.innerHTML = sheetname;
    // make selected if name equals stored_worksheetname
                                if (!!stored_worksheetname) { // if x = '' then !!x evaluates to false.
                                    if(sheetname.toLowerCase() === stored_worksheetname.toLowerCase() ){
                                        option.selected = true;
                                }}
                                worksheet_list.appendChild(option);
                            }
                        } //for (let x=0;

//---------  gibve message when no data in worksheetse
                        if (!worksheet_list.options.length){
                            para.textContent = "There are no worksheets with data." ;
                            div_info.appendChild(para);
                        } else {
//---------  if only one sheet exists: makke selected = True
                            if (worksheet_list.options.length === 1){
                                worksheet_list.options[0].selected = true;
                                selected_worksheetname = worksheet_list.options[0].value;
                            }
                        } //if (!worksheet_list.options.length){

//---------  get selected worksheet, if any

                        if(!!selected_worksheetname){
                            worksheet = workbook.Sheets[selected_worksheetname];
                            if(!!worksheet){
//---------  get Column and Rownumber of upper left cell and lower right cell of SheetRange
                                worksheet_range = GetSheetRange (worksheet);
                                if (!!worksheet_range) {
    //--------- set checkbox_noheader checked
                                    checkbox_noheader.checked = selected_no_header;
        //--------- fill worksheet_data with data from worksheet
                                    worksheet_data = FillWorksheetData(worksheet, worksheet_range, selected_no_header);
        //--------- fill table excel_columns
                                    Fill_Excel_Items("col");
                                    CreateMapTableWrap("col");

                                    Fill_Excel_Items("lvl");
                                    CreateMapTableWrap("lvl");

                                    Fill_Excel_Items("sct");
                                    CreateMapTableWrap("sct");
        //--------- fill DataTable
                                    FillDataTable(worksheet_range);
                                    UpdateDatatableHeader();

                                    // upload new settings awpCaption
                                    UpdateSettings ();
               }}}}}
            }; // reader.onload = function(event) {
       }; // if(!!sel_file){
    }  // function Get_Workbook(sel_file))


//=========  fill worksheet_data  ========================================================================
    function FillWorksheetData(work_sheet, sheet_range, no_header) {
    // fills the list 'worksheet_data' with data from 'worksheet'
        let sheet_data = [];
        let row = sheet_range.StartRowNumber;
        // skip first row when first row is header row
        if (!no_header) {++row;};
        for (; row<=sheet_range.EndRowNumber; ++row){
            let NewRow = [];
            for (let col=sheet_range.StartColNumber; col <= sheet_range.EndColNumber; ++col){
                let CellName = GetCellName (col,row);
                let CellValue = GetExcelValue(work_sheet, CellName,"w");
                NewRow.push (CellValue);
            };
            NewRow.push (0); // cell added for mapped levelID
            NewRow.push (0); // cell added for mapped ectorID
            sheet_data.push (NewRow);
        }
        return sheet_data;
    }

//=========  Fill_Excel_Items  ========================================================================
    function Fill_Excel_Items(tableBase) {
console.log("=========  Fill_Excel_Items =========>>> ", tableBase);

    // fill the array excel_levels and excel_sectors with unique values of linked columns in table Students

        let colindex;
        let stored_items = [];
        let excel_items = [];
        // ItemList is the list of unique values in the Excel Column that is linked to 'level or 'sector'
        let itemlist =[];

        if (tableBase === "col"){
            stored_items = stored_columns;
            excel_columns = [];
        } else if (tableBase === "lvl"){
            //colindex = get_excelcolindex_by_awpkey ("level");
            colindex = get_index_by_awpkey (excel_columns, "level");
            stored_items = stored_levels;
            excel_levels = [];
        } else if (tableBase === "sct") {
            //colindex = get_excelcolindex_by_awpkey ("sector");
            colindex = get_index_by_awpkey (excel_columns, "sector");
            stored_items = stored_sectors;
            excel_sectors = [];
        }

//======= create array 'excel_items' =======
        if (tableBase === "col"){
    // create array 'excel_columns' with Excel column names, replaces spaces, ", ', /, \ and . with _
            if(!!worksheet && !!worksheet_range) {
// get headers if Not SelectedSheetHasNoHeader: from first row, otherwise: F01 etc ");
                let row_number = worksheet_range.StartRowNumber;
                for (let col_number=worksheet_range.StartColNumber, idx = 0, colName = ""; col_number<=worksheet_range.EndColNumber; ++col_number){
                    if (selected_no_header){
                        const index = "00" + col_number;
                        colName = "F" + index.slice(-2);
                    } else {
                        const cellName = GetCellName (col_number,row_number);
                        const excValue = GetExcelValue(worksheet, cellName,"w");
                        colName = replaceChar(excValue);
                    }
                    excel_items.push ({index: idx, excKey: colName});
                    ++idx;
            }}
        } else {
//----- create array 'excel_levels' or 'excel_sectors' ----------------------------
//----- insert tblColLinked and tblColAwp rows from stored_columns
        // colindex is undefined if Level/Sector not exists in this department
        // skip fill itemlist when worksheet_data is empty

            if (!!worksheet_data) {
                // make list of distinct values of row[colindex]
                for (let x = 0; x < worksheet_data.length; ++x){
                    let row = worksheet_data[x];

                    if(!!row[colindex]){
                        let excLevel = row[colindex].toLowerCase();
                        // replace forbidden characters with underscore

                        excLevel = replaceChar(excLevel);

                        // PR2019-01-12 debug: function .includes not wroking in IE11
                        let found = false;
                        if (!!itemlist){
                            for (let y = 0; y < itemlist.length; ++y){
                                let item = itemlist[y];
                                if(item === excLevel){
                                    found = true;
                                    break;
                                }}
                        }
                        if(!found){itemlist.push(excLevel)}

                }};
        // sort list of distinct values and add to array excel_items

console.log("itemlist ", itemlist);
                if (!!itemlist) {
                    itemlist.sort()
                    for (let x = 0; x < itemlist.length; ++x){
                        excel_items.push ({index: x.toString(), excKey: itemlist[x]});;
                }};
console.log("excel_items ", excel_items);
        }}

// =======  Map array 'excel_items' with 'stored_items' =======
    // function loops through stored_items and excel_items and add links and caption in these arrays

    // stored_columns: [ {awpKey: "idnumber", caption: "ID nummer", excKey: "ID"}, 1: ...]
    // excel_columns: [ {index: 10, excKey: "ID", awpKey: "idnumber", awpCaption: "ID nummer"}} ]

    // loop through array stored_items

        if(!!stored_items) {
            for (let i = 0; i < stored_items.length; i++) {
                let stored_row = stored_items[i];
                let is_linked = false;
                if (!!stored_row.awpKey && !!stored_row.excKey){
        //check if excKey also exists in excel_items
                    let excel_row_byKey = get_arrayRow_by_keyValue (excel_items, "excKey", stored_row.excKey);
        //if excKey is found in excel_items: add awpKey and awpCaption to excel_row
                    if (!!excel_row_byKey){
                        excel_row_byKey.awpKey = stored_row.awpKey;
                        excel_row_byKey.awpCaption = stored_row.caption;
                        is_linked = true;
                    } else {
        //if excKey is not found in excel_items remove excKey from stored_row
                        delete stored_row.excKey;
                }}
        // if column not linked, check if AWP caption and Excel name are the same, if so: link anyway
                if (!is_linked){
                    let excel_row_byCaption = get_arrayRow_by_keyValue (excel_items, "excKey", stored_row.caption)
                    if (!!excel_row_byCaption){
                        stored_row.excKey = excel_row_byCaption.excKey;
                        excel_row_byCaption.awpKey = stored_row.awpKey;
                        excel_row_byCaption.awpCaption = stored_row.caption;
                        is_linked = true;
                }}
            };
        }

        if (tableBase === "col"){
            stored_columns = stored_items;
            excel_columns = excel_items;
        } else if (tableBase === "lvl"){
            stored_levels = stored_items
            excel_levels = excel_items
        } else if (tableBase === "sct") {
            stored_sectors = stored_items;
            excel_sectors = excel_items;
        }

console.log("stored_columns ", stored_columns);
console.log("excel_columns ", excel_columns);

    }  // Fill_Excel_Items

//=========  FillDataTable  ========================================================================
    function FillDataTable(sheet_range) {
console.log("=========  function FillDataTable =========");

//--------- delete existing rows
        $("#id_thead, #id_tbody").html("");

        if(!!worksheet_data && !!excel_columns){
            // create a <tblHead> element
            let tblHead = document.getElementById('id_thead');
            let tblBody = document.getElementById('id_tbody');

//--------- insert tblHead row of datatable
            let tblHeadRow = tblHead.insertRow();

            //PR2017-11-21 debug: error when StartColNumber > 1, j must start at 0
            //var EndIndexPlusOne = (sheet_range.EndColNumber) - (sheet_range.StartColNumber -1)

            //index j goes from 0 to ColCount-1, excel_columns index starts at 0, last index is ColCount-1
            for (let j = 0 ; j <sheet_range.ColCount; j++) {
                let cell = tblHeadRow.insertCell(-1);
                let excKey = excel_columns[j].excKey;
                cell.innerHTML = excKey;
                cell.setAttribute("id", "idTblCol_" + excKey);
            }; //for (let j = 0; j < 2; j++)

//--------- insert DataSet rows
            //var EndRowIndex = 9;
            var LastRowIndex = sheet_range.RowCount -1;
            // worksheet_data has no header row, start allways at 0
            if (!selected_no_header) { --LastRowIndex;}
            //if (EndRow-1 < EndRowIndex) { EndRowIndex = EndRow-1;};
            for (let i = 0; i <= LastRowIndex; i++) {
                let tblRow = tblBody.insertRow(-1); //index -1 results in that the new row will be inserted at the last position.
                for (let j = 0 ; j < sheet_range.ColCount; j++) {
//console.log("worksheet_data[" + i + "][" + j + "]: <" + worksheet_data[i][j]) + ">";
                    let cell = tblRow.insertCell(-1); //index -1 results in that the new cell will be inserted at the last position.
                    if(!!worksheet_data[i][j]){
                        cell.innerHTML = worksheet_data[i][j];
                    };
                } //for (let j = 0; j < 2; j++)
            } //for (let i = 0; i < 2; i++)
            // sets the border attribute of tbl to 2;
            //table.setAttribute("border", "2");
        }; // if(!!worksheet_data && !!excel_columns){
    };//function DataTabel_Set() {


//=========  FillDataTableAfterUpload  ==============================
    function FillDataTableAfterUpload(response, sheet_range) {
console.log("=========  function FillDataTableAfterUpload =========");

//--------- delete existing rows
       // $("#id_thead, #id_tbody").html("");

        let tblBody =$("#id_tbody");
        tblBody.html("");

        if(!!worksheet_data && !!excel_columns){
            // create a <tblHead> element
            //let tblHead = document.getElementById('id_thead');
            //let tblBody = document.getElementById('id_tbody');

//--------- insert tblHead row of datatable
            //let tblHeadRow = tblHead.insertRow();

            //PR2017-11-21 debug: error when StartColNumber > 1, j must start at 0
            //var EndIndexPlusOne = (sheet_range.EndColNumber) - (sheet_range.StartColNumber -1)

            //index j goes from 0 to ColCount-1, excel_columns index starts at 0, last index is ColCount-1
            //for (let j = 0 ; j <sheet_range.ColCount; j++) {
            //    let cell = tblHeadRow.insertCell(-1);
            //    let excKey = excel_columns[j].excKey;
            //    cell.innerHTML = excKey;
            //    cell.setAttribute("id", "idTblCol_" + excKey);
            //}; //for (let j = 0; j < 2; j++)

//--------- iterate through response rows
            //var EndRowIndex = 9;
            var LastRowIndex = sheet_range.RowCount -1;
            // worksheet_data has no header row, start allways at 0
            if (!selected_no_header) { --LastRowIndex;}
            //if (EndRow-1 < EndRowIndex) { EndRowIndex = EndRow-1;};
            for (let i = 0, len = response.length; i <= len; i++) {
                let datarow = response[i];

console.log("datarow: ", i , datarow );
//e_idnumber: "ID number already exists."
//e_lastname: "Student name already exists."
//o_firstname: "Arlienne Marie Nedelie"
//o_fullname: "Arlienne Marie Nedelie Frans"
//o_idnumber: "1996011503"
//o_lastname: "Frans"

// if s_idnumber is not present, the record is not saved
                let s_idnumber = get_obj_value_by_key (datarow, "s_idnumber")
                let record_is_saved = !!s_idnumber

//--------- iterate through columns of response row

// ---  add <tr>
                let id_datarow =  "id_datarow_" + i.toString()
                let class_background;
                if (record_is_saved){
                    if (i%2 === 0) {
                        class_background = "cell_saved_even";
                    } else {
                        class_background = "cell_saved_odd";
                    }
                } else {
                    if (i%2 === 0) {
                        class_background = "cell_unchanged_even";
                    } else {
                        class_background = "cell_unchanged_odd";
                    }
                }
                $("<tr>").appendTo(tblBody)
                    .attr({"id": id_datarow})
                    .addClass(class_background);
                let tblRow = $("#" + id_datarow);
                for (let j = 0, len = excel_columns.length ; j < len; j++) {

//========= Create td
                    let id_datacell =  "id_datacell_" + i.toString() + "_" + + j.toString()
                    $("<td>").appendTo(tblRow)
                             .attr({"id": id_datacell});
                    let tblCell = $("#" + id_datacell);

                    let key = get_obj_value_by_key (excel_columns[j], "awpKey");
// ---  skip if column not linked
                    if (!!key) {

                        let o_value, e_value, s_value;
                        o_value = get_obj_value_by_key (datarow, "o_" + key);
                        e_value = get_obj_value_by_key (datarow, "e_" + key);
                        s_value = get_obj_value_by_key (datarow, "s_" + key);


                        if(!!o_value){
                            tblCell.html(o_value);
                        }
                        // add tooltip, set background color pink

                        if (!!e_value){
                            if (i%2 === 0) {class_background = "cell_error_even"; } else { class_background = "cell_error_odd"; }
                            tblCell.html(o_value);
                            tblCell.attr({"data-toggle": "tooltip", "title": e_value})
                                    .addClass(class_background);
                        } else {
                            tblCell.html(s_value);
                        }
                        tblCell.addClass(class_background);






                    }

//console.log("worksheet_data[" + i + "][" + j + "]: <" + worksheet_data[i][j]) + ">";







                } //for (let j = 0; j < 2; j++)
            } //for (let i = 0; i < 2; i++)
        }; // if(!!worksheet_data && !!excel_columns){
    };//function FillDataTableAfterUpload() {


//========= is_valid_filetype  ====================================
    function is_valid_filetype(File) {
        // MIME xls: application/vnd.ms-excel
        // MIME xlsx: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
        // MIME csv: text/csv

        var is_valid = false
        for (let prop in file_types) {
            if (file_types.hasOwnProperty(prop)) {
                if(File.type === file_types[prop]) {
                    is_valid = true;
                    break;
        }}}
        return is_valid;
    }

//========= GetSheetRange  ====================================
    function GetSheetRange (Sheet) {
        //Function gets Column and Rownumber of upper left cell and lower right cell of SheetRange
        // return false if Sheet or !ref not found, otherwise retrun object with col/row start/end
//console.log("==========  GetSheetRange: ==========");
//console.log(Sheet);
        var objRange = [];
        if (!!Sheet) {
            if (!!Sheet["!ref"]){
                var SheetRef = Sheet["!ref"];
//console.log("SheetRef: " + SheetRef);
                //check if range contains :, if not: range has 1 cell
                var RangeSplit =[];
                if (SheetRef.search(":")=== -1) {
                    RangeSplit = [SheetRef, SheetRef];
                } else {
                    //objRange = {Range: Sheet["!ref"]};
                    //split RangeSplit: Name of StartCell = RangeSplit[0], Name of EndCell = RangeSplit[1];
                    RangeSplit = SheetRef.split(":");
                };
//console.log(">> Range: " + RangeSplit[0] + " - " + RangeSplit[1]);
                var strColName, pos;
                var ColNumber = []; //1-based index of colums
                var RowNumber = []; //1-based index of rows
                //RangeSplit[0] is string of Range Start (upper left cell)
                //RangeSplit[1] is string of Range End  (lower right cell
                for (let x=0; x<2; ++x) {
                    // get position of first digit pos is 0-based
                    pos  =  RangeSplit[x].search(/[0-9]/);
                    // get column letters (0 till pos)
                    strColName  = RangeSplit[x].slice(0,pos);
                    // get row digits (pos till end)
                    RowNumber[x]  = RangeSplit[x].slice(pos);
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
                var StartColNumber = Number(ColNumber[0]);
                var EndColNumber = Number(ColNumber[1]);
                var ColCount = EndColNumber - StartColNumber + 1;

                var StartRowNumber = Number(RowNumber[0]);
                var EndRowNumber = Number(RowNumber[1]);
                var RowCount = EndRowNumber - StartRowNumber + 1;

                // range B2:C5 with header gives the following values:
                // StartRowNumber = 3 (header not included)
                // EndRowNumber   = 5
                // RowCount       = 3 (EndRowNumber - StartRowNumber +1)
                objRange ["StartRowNumber"] = StartRowNumber;
                objRange ["EndRowNumber"] = EndRowNumber;
                objRange ["RowCount"] = RowCount;
                objRange ["StartColNumber"] = StartColNumber;
                objRange ["EndColNumber"] = EndColNumber;
                objRange ["ColCount"] = ColCount;
            } else {
//console.log("Sheet[!ref] not found: " + Sheet["!ref"]);
            } //if (!!Sheet["!ref"])
        } else {
//console.log("Sheet not found: " + Sheet);
        };// if (!!Sheet)
//console.log("==========  GetSheetRange return objRange: " + (!!objRange));
//console.log(objRange);
        return objRange;
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

//========= SheetHasRange  ====================================
    function SheetHasRange(Sheet) {
    // PR2017-11-04 from: https://stackoverflow.com/questions/2693021/how-to-count-javascript-array-objects
        //function checks if property "!ref" existst in Sheet. If so, it has a range
        "use strict";
        var result = false;
        for (let prop in Sheet) {
            if (Sheet.hasOwnProperty(prop)) {
                if (prop === "!ref") {
                    result = true;
                    break;
                }
            }
        } //for(let prop in Sheet)
        return result;
    } //function GetExcelValue

// +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


//========= CreateMapTableWrap(tableBase))  ====================================
    function CreateMapTableWrap(tableBase) {
console.log("==== CreateMapTableWrap  =========> ", tableBase);
        // tableBase = "lvl" or "sct"
        let header1, header2, headExc, headAwp, headLnk, awpKey;
        let stored_items;
        let excel_items;

        // remove table
        $("#id_basediv_" + tableBase).html("");

        if (tableBase === "col"){
            header1 = "Link columns";
            header2 =  "Click items to link or unlink columns";
            headExc = "Excel columns";
            headAwp = "AWP columns";
            headLnk = "Linked columns" ;
             if (!!stored_columns){
                CreateMapTableSub(tableBase, header1, header2, headExc, headAwp, headLnk);
                CreateMapTableRows(tableBase, stored_columns, excel_columns);
            }

        } else if (tableBase === "lvl"){
            awpKey = "level";
            header1 = "Link levels";
            header2 =  "Click items to link or unlink level";
            headExc = "Excel levels";
            headAwp = "AWP levels";
            headLnk = "Linked levels" ;
            stored_items = stored_levels;
            excel_items = excel_levels;

            // create MapTable only if level/sctor is required in this department, otherwise stored_items does not exist
            if (!!stored_items){
            // create TableLevels only if column "level" is linked to Excel column
                //const colindex_item = get_excelcolindex_by_awpkey (awpKey);
                colindex_item = get_index_by_awpkey (excel_columns, awpKey);
                // PR2019-01-11 debug: (!!colindex_item) = False when zero
                if (!!colindex_item || colindex_item === 0){
            // only when level is required, i.e. when mapped_level_list exists
                    CreateMapTableSub(tableBase, header1, header2, headExc, headAwp, headLnk);
                    CreateMapTableRows(tableBase, stored_items, excel_items);
            }}

        } else if (tableBase === "sct") {
            awpKey = "sector";
            header1 = "Link sectors";
            header2 =  "Click items to link or unlink sector";
            headExc = "Excel sectors";
            headAwp = "AWP sectors";
            headLnk = "Linked sectors" ;
            stored_items = stored_sectors;
            excel_items = excel_sectors;

            // create MapTable only if level/sctor is required in this department, otherwise stored_items does not exist
            if (!!stored_items){
            // create TableLevels only if column "level" is linked to Excel column
                //const colindex_item = get_excelcolindex_by_awpkey (awpKey);
                const colindex_item = get_index_by_awpkey (excel_columns, awpKey);
            // create TableLevels only if column "level" is linked to Excel column
                if (!!colindex_item || colindex_item === 0){
            // only when level is required, i.e. when mapped_level_list exists
                    CreateMapTableSub(tableBase, header1, header2, headExc, headAwp, headLnk);
                    CreateMapTableRows(tableBase, stored_items, excel_items);
                };
            }
        }

    }

//========= CreateMapTableSub  ====================================
    function CreateMapTableSub(tableBase, header1, header2, headExc, headAwp, headLnk ) {
console.log("==== CreateMapTableSub  =========>>>", tableBase, header1, header2, headExc, headAwp, headLnk);
        let base_div = $("#id_basediv_" + tableBase);  // BaseDivID = "sct", "lvl", "col"
        // delete existing rows of tblColExcel, tblColAwp, tblColLinked
        base_div.html("");

        //append column header to base_div
        $("<div>").appendTo(base_div)
                .addClass("c_columns_header")
                //header1 = "Link sectors"
                //header2 = "Click to link or unlink sector"
                .html("<p><b>" + header1 + "</b></p><p>" + header2 + "</p>");

        // append flex div for table Excel and Awp
        $("<div>").appendTo(base_div)
                .attr({id: "id_ea_flex_" + tableBase})
                .addClass("ea_flex");

        // append div for table Excel
            $("<div>").appendTo("#id_ea_flex_" + tableBase)
                    .attr({id: "id_exc_div_" + tableBase});

                $("<table>").appendTo("#id_exc_div_" + tableBase)
                        .attr({id: "id_exc_table_" + tableBase})
                        .addClass("c_grid_colExcel")
                        .on("click", handle_EAL_row_clicked);

                    $("<thead>").appendTo("#id_exc_table_" + tableBase)
                            .html("<tr><td>" + headExc + "</td></tr>"); // headExc: "Excel sectors"
                    $("<tbody>").appendTo("#id_exc_table_" + tableBase)
                            .attr({id: "id_exc_tbody_" + tableBase});

        // append div for table Awp
            $("<div>").appendTo("#id_ea_flex_" + tableBase)
                    .attr({id: "id_awp_div_" + tableBase});
                $("<table>").appendTo("#id_awp_div_" + tableBase)
                        .attr({id: "id_awp_table_" + tableBase})
                        .addClass("c_grid_colExcel")
                        .on("click", handle_EAL_row_clicked);
                    $("<thead>").appendTo("#id_awp_table_" + tableBase)
                            .html("<tr><td>" + headAwp + "</td></tr>"); // headAwp: "AWP columns"
                    $("<tbody>").appendTo("#id_awp_table_" + tableBase)
                            .attr({id: "id_awp_tbody_" + tableBase});

        // append flex div for table Linked
        $("<div>").appendTo(base_div)
                .attr({id: "id_li_flex_" + tableBase})
                .addClass("li_flex");
            $("<div>").appendTo("#id_li_flex_" + tableBase)
                    .attr({id: "id_lnk_div_" + tableBase});
                $("<table>").appendTo("#id_lnk_div_" + tableBase)
                        .attr({id: "id_lnk_table_" + tableBase})
                        .addClass("c_grid_colLinked")
                        .on("click", handle_EAL_row_clicked);
                    $("<thead>").appendTo("#id_lnk_table_" + tableBase)
                            .attr({id: "id_sct_th_lnk_" + tableBase})
                            .html("<tr><td colspan=2>" + headLnk + "</td></tr>"); // headLnk: "Linked sectors"
                    $("<tbody>").appendTo("#id_lnk_table_" + tableBase)
                            .attr({id: "id_lnk_tbody_" + tableBase});

         }; //function CreateMapTableSub()
// ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//========= CreateMapTableRows  ====================================
    function CreateMapTableRows(tableBase, stored_items, excel_items,
                    JustLinkedAwpId, JustUnlinkedAwpId, JustUnlinkedExcId) {

    console.log("==== CreateMapTableRows  =========>> ", tableBase);
        const cae_hv = "c_colAwpExcel_hover";
        //const cae_hl = "c_colAwpExcel_highlighted";
        const cli_hv = "c_colLinked_hover";
        //const cli_hi = "c_colLinked_highlighted";

        const Xid_exc_tbody = "#id_exc_tbody_" + tableBase;
        const Xid_awp_tbody = "#id_awp_tbody_" + tableBase;
        const Xid_lnk_tbody = "#id_lnk_tbody_" + tableBase;

        // only when level is required, i.e. when mapped_level_list exists
// console.log("stored_items", stored_items, typeof stored_items);
// console.log("excel_items", excel_items, typeof excel_items);

        // JustUnlinkedAwpId = id_awp_tr_sct_1
        // JustUnlinkedExcId = id_exc_tr_sct_2
        // delete existing rows of tblColExcel, tblColAwp, tblColLinked
        $(Xid_exc_tbody).html("");
        $(Xid_awp_tbody).html("");
        $(Xid_lnk_tbody).html("");

    //======== loop through array stored_items ========
        for (let i = 0 ; i <stored_items.length; i++) {
            // row = {awpKey: "30", caption: "tech", excKey: "cm"}
            let row = stored_items[i];
            const idAwpRow = "id_awp_tr_" + tableBase + "_" + i.toString();
            const XidAwpRow = "#" + idAwpRow;

        //if excKey exists: append row to table ColLinked
            if (!!row.excKey){
                $("<tr>").appendTo(Xid_lnk_tbody)  // .appendTo( "#id_lnk_tbody_lvl" )
                    .attr({"id": idAwpRow, "key": row.awpKey})
                    .addClass("c_colLinked_tr")
                    .mouseenter(function(){$(XidAwpRow).addClass(cli_hv);})
                    .mouseleave(function(){$(XidAwpRow).removeClass(cli_hv);})
        // append cells to row Linked
                    .append("<td>" + row.excKey + "</td>")
                    .append("<td>" + row.caption + "</td>");

        //if new appended row: highlight row for 1 second
                if (!!JustLinkedAwpId && !!idAwpRow && JustLinkedAwpId === idAwpRow) {
                   $(XidAwpRow).addClass(cli_hv);
                   setTimeout(function (){$(XidAwpRow).removeClass(cli_hv);}, 1000);
                }
            } else {

        // append row to table Awp if excKey does not exist in stored_items
                $("<tr>").appendTo(Xid_awp_tbody)
                    .attr({"id": idAwpRow, "key": row.awpKey})
                    .addClass("c_colExcelAwp_tr")
                    .mouseenter(function(){$(XidAwpRow).addClass(cae_hv);})
                    .mouseleave(function(){$(XidAwpRow).removeClass(cae_hv);})
        // append cell to row ExcKey
                    .append("<td>" + row.caption + "</td>");
        // if new unlinked row: highlight row for 1 second
                if (!!JustUnlinkedAwpId && !!idAwpRow && JustUnlinkedAwpId === idAwpRow) {
                    $(XidAwpRow).addClass(cae_hv);
                    setTimeout(function () {$(XidAwpRow).removeClass(cae_hv);}, 1000);
            }}};

    //======== loop through array excel_items ========
        // excel_sectors [{excKey: "cm", {awpKey: "c&m"},}, {excKey: "em"}, {excKey: "ng"}, {excKey: "nt"}]
        for (let i = 0 ; i < excel_items.length; i++) {
            // only rows that are not linked are added to tblColExcel
            //  {excKey: "idSctExc_0", caption: "china"}
            let row = excel_items[i];
            const idExcRow = "id_exc_tr_" + tableBase + "_" + i.toString();
            const XidExcRow = "#" + idExcRow;

        // append row to table Excel if awpKey: does not exist in excel_items
            if (!row.awpKey){
                $("<tr>").appendTo(Xid_exc_tbody)
                    .attr({"id": idExcRow})
                    .attr({"id": idExcRow, "key": row.excKey})
                    .addClass("c_colExcelAwp_tr")
                    .mouseenter(function(){$(XidExcRow).addClass(cae_hv);})
                    .mouseleave(function(){$(XidExcRow).removeClass(cae_hv);})
        // append cell to row ExcKey
                    .append("<td>" + row.excKey + "</td>");
        // if new unlinked row: highlight row ColExc
                if (!!JustUnlinkedExcId && !!idExcRow && JustUnlinkedExcId === idExcRow) {
                    $(XidExcRow).addClass(cae_hv);
                    setTimeout(function () {$(XidExcRow).removeClass(cae_hv);}, 1000);
        }}};
     }; //function CreateMapTableRows()

//========= function UdateDatatableHeader  ====================================================
    function UpdateDatatableHeader() {
//----- set awpCaption in linked header colomn of datatable
console.log("---------  function UpdateDatatableHeader ---------");
//----- loop through array excel_columns from row index = 0
        for (let j = 0 ; j <excel_columns.length; j++) {
            // only rows that are not linked are added to tblColExcel
            let ExcCol = excel_columns[j].excKey;
            let AwpCaption = excel_columns[j].awpCaption;

            let tblColHead = document.getElementById("idTblCol_" + ExcCol);
            if (!!AwpCaption){
                tblColHead.innerHTML = AwpCaption;
                tblColHead.classList.add("c_table_stud_thead_td_selected");
            } else {
                tblColHead.innerHTML = ExcCol;
                tblColHead.classList.remove("c_table_stud_thead_td_selected");
            }
        }
   } // function UpdateDatatableHeader

//=========   Handle_TEL_row_clicked   ======================
    function Handle_TEL_row_clicked(event) {  //// EAL: Excel Tsa Linked table
        // function gets row_clicked.id, row_other_id, row_clicked_key, row_other_key
        // sets class 'highlighted' and 'hover'
        // and calls 'LinkColumns' or 'UnlinkColumns'
        // currentTarget refers to the element to which the event handler has been attached
        // event.target which identifies the element on which the event occurred.
        console.log("=========   Handle_TEL_row_clicked   ======================") ;
        //.log("event.currentTarget", event.currentTarget) ;

        if(!!event.currentTarget) {
            let tr_selected = event.currentTarget;
            let table_body_clicked = tr_selected.parentNode;
            const tbodyName = get_attr_from_el(table_body_clicked, "data-tbody");
            const cls_selected = (tbodyName === "lnk") ? cls_linked_selected : cls_unlinked_selected;

            const row_clicked_id = tr_selected.id;
            const row_clicked_key = get_attr_from_el(tr_selected, "data-key");
            let row_other_id = null, row_other_key = null;

// ---  check if clicked row is already selected
            const tr_is_not_yet_selected = (!get_attr_from_el(tr_selected, "data-selected", false))

// ---  if tr_is_not_yet_selected: add data-selected and class selected, remove class selected from all other rows in this table
            const cls_linked_unlinked_hover = (tbodyName === "lnk") ? "tsa_td_linked_hover" : "tsa_td_unlinked_hover";
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
            if (["tsa", "exc"].indexOf(tbodyName) > -1) {
// ---  if clicked row was not yet selected: check if other table has also selected row, if so: link
                if(tr_is_not_yet_selected) {
// ---  check if other table has also selected row, if so: link
                    let table_body_other = (tbodyName === "exc") ? el_tbody_tsa : el_tbody_exc;
// ---  loop through rows of other table
                    let link_rows = false;
                    for (let j = 0, row_other; row_other = table_body_other.rows[j]; j++) {
                       const other_tr_is_selected = get_attr_from_el(row_other, "data-selected", false)
// ---  set link_rows = true if selected row is found in other table
                       if(other_tr_is_selected) {
                           link_rows = true;
                           row_other_id = get_attr_from_el(row_other, "id");
                           row_other_key = get_attr_from_el(row_other, "data-key");
                           break;
                        }
                    }
// ---  link row_clicked with delay of 250ms (to show selected Tsa and Excel row)
                    if (link_rows){
                        setTimeout(function () {
                            LinkColumns(tbodyName, row_clicked_id, row_other_id, row_clicked_key, row_other_key);
                        }, 250);
                    }
                }
            } else if (tr_is_not_yet_selected) {
// ---  unlink tr_selected  with delay of 250ms (to show selected Tsa and Excel row)
                setTimeout(function () {
                    UnlinkColumns(tbodyName, row_clicked_id, row_clicked_key);
                    }, 250);
            }
       }  // if(!!event.currentTarget) {
    };  // Handle_TEL_row_clicked


//========= linkColumns  ====================================================
    function linkColumns(tableBase, tableName, row_clicked_id, row_other_id, row_clicked_key, row_other_key) {
//console.log("==========  linkColumns ==========>> ", tableBase, tableName, row_clicked_key, row_other_key);
// function adds 'excCol' to stored_columns and 'awpCaption' to excel_columns

//console.log("tableBase ", tableBase, "tableName: ", tableName);
//console.log("row_clicked_id: ", row_clicked_id, "row_other_id ", row_other_id );
//console.log("row_clicked_key ", row_clicked_key, "row_other_key ", row_other_key );

        let stored_items, excel_items;
        if (tableBase === "col") {
            stored_items = stored_columns;
            excel_items = excel_columns;
        } else if (tableBase === "lvl"){
            stored_items = stored_levels;
            excel_items = excel_levels;
        } else if (tableBase === "sct"){
            stored_items = stored_sectors;
            excel_items = excel_sectors;
        }

        let stored_row_id, stored_row_awpKey,excel_row_excKey;
        if (tableName ===  "awp") {
            stored_row_id = row_clicked_id;
            stored_row_awpKey = row_clicked_key;
            excel_row_excKey = row_other_key;
        } else if (tableName ===  "exc") {
            stored_row_id = row_other_id;
            stored_row_awpKey = row_other_key;
            excel_row_excKey = row_clicked_key;
        }

        let stored_row = get_arrayRow_by_keyValue (stored_items, "awpKey", stored_row_awpKey);
        let excel_row = get_arrayRow_by_keyValue (excel_items, "excKey", excel_row_excKey);

        if(!!stored_row && !!excel_row){
            if(!!excel_row.excKey){
                stored_row["excKey"] = excel_row.excKey;};
            if(!!stored_row.awpKey){
                excel_row["awpKey"] = stored_row.awpKey;};
            if(!!stored_row.caption){
                excel_row["awpCaption"] = stored_row.caption;};
        }

        // save changes in array stored_columns, excel_columns etc
        if (tableBase === "col") {
            stored_columns = stored_items;
            excel_columns = excel_items;
        } else if (tableBase === "lvl"){
            stored_levels = stored_items;
            excel_levels = excel_items;
        } else if (tableBase === "sct"){
            stored_sectors = stored_items;
            excel_sectors = excel_items;
        }

        // refresh linked levels / sector if this column linked
        // JustLinkedAwpId = stored_row_id;
        CreateMapTableRows(tableBase, stored_items, excel_items, stored_row_id);

        if (tableBase === "col") {
            if(stored_row_awpKey === "level"){
                Fill_Excel_Items("lvl");
                CreateMapTableWrap("lvl");
            } else if(stored_row_awpKey === "sector"){
                Fill_Excel_Items("sct");
                CreateMapTableWrap("sct");
            }

            UpdateDatatableHeader();
        }
    // upload new settings
       UpdateSettings();
    };

//========= unlinkColumns =======================================================
    function unlinkColumns(tableBase, tableName, row_clicked_id, row_clicked_key) {
        // function deletes attribute 'excKey' from stored_items
        // and deletes attributes 'awpKey' and 'awpCaption' from ExcelDef
        // if type= 'col': UpdateDatatableHeader
        // calls UpdateSettings and
//console.log("====== unlinkColumns =======================");

// function removes 'excKey' from stored_items and 'awpKey' from excel_items

        let stored_items, excel_items;
        if (tableBase === "col") {
            stored_items = stored_columns;
            excel_items = excel_columns;
        } else if (tableBase === "lvl"){
            stored_items = stored_levels;
            excel_items = excel_levels;
        } else if (tableBase === "sct"){
            stored_items = stored_sectors;
            excel_items = excel_sectors;
        }

        const JustUnlinkedAwpId = row_clicked_id;

        // in unlink: row_clicked_key = awpKey
        // stored_row = {awpKey: "gender", caption: "Geslacht", excKey: "MV"}
        let stored_row, excel_row, JustUnlinkedExcId;
        stored_row = get_arrayRow_by_keyValue (stored_items, "awpKey", row_clicked_key);
        // excel_row =  {index: 8, excKey: "geboorte_land", awpKey: "birthcountry", awpCaption: "Geboorteland"}
        if (!!stored_row) {
            if (!!stored_row.excKey) {
        // look up excKey in excel_items
                excel_row= get_arrayRow_by_keyValue (excel_items, "excKey", stored_row.excKey)
        // delete excKey from stored_row
                delete stored_row.excKey;
                if (!!excel_row) {
                    JustUnlinkedExcId = "id_exc_tr_" + tableBase + "_" + excel_row.index;
        // delete awpKey and awpCaption from excel_row]
                    delete excel_row.awpKey;
                    delete excel_row.awpCaption;
                }
        // reset excel_levels or excel_sectors, and hide table
                if (tableBase === "col") {
                    if(row_clicked_key === "level"){
                        excel_levels = []
                        CreateMapTableWrap("lvl");
                    } else if(row_clicked_key === "sector"){
                        excel_sectors = []
                        CreateMapTableWrap("sct");
                    }
                }
            }  // if (!!stored_row.excKey)
        }  // if (!!stored_row)

        CreateMapTableRows(tableBase, stored_items, excel_items,
                            "", JustUnlinkedAwpId, JustUnlinkedExcId);

        if (tableBase === "col") {
            stored_columns = stored_items;
            UpdateDatatableHeader();
        } else if (tableBase === "lvl"){
            stored_levels = stored_items;
        } else if (tableBase === "sct"){
            stored_sectors = stored_items;
        }

    // upload new settings
       UpdateSettings();

    }  // function unlinkColumns(idAwpCol)


//========= UPLOAD SETTING COLUMNS =====================================
    function UpdateSettings () {
// console.log ("==========  UPLOAD SETTING COLUMNS");
        if(!!stored_columns) {
            // stored_columns is an array and has a .length property
            if(stored_columns.length > 0){
// --- store worksheetname, no_header and has_multiple_settings in schoolsettings

                // settingsValue is an associative array
                var settingsValue = {};
                if (!!selected_worksheetname){
                    settingsValue["worksheetname"] = selected_worksheetname
                }
                settingsValue["no_header"] = selected_no_header;

// if field 'excKey' exists in stored_columns: add to settingsValue with prefix "col_"
                if (!!stored_columns){
                    for (let i = 0 ; i <stored_columns.length; i++) {
                        if (!!stored_columns[i].excKey){
                            settingsValue["col_" + stored_columns[i].awpKey] = stored_columns[i].excKey;
                }}};

// if field 'excKey' exists in stored_levels add to settingsValue with prefix "lvl_"
                if (!!stored_levels){
                    for (let x = 0 ; x <stored_levels.length; x++) {
                        if (!!stored_levels[x].excKey){
                            settingsValue["lvl_" + stored_levels[x].awpKey] = stored_levels[x].excKey;
                }}};

// if field 'excKey' exists in stored_sectors add to settingsValue with prefix "sct_"
                if (!!stored_sectors){
                    for (let y = 0 ; y <stored_sectors.length; y++) {
                        if (!!stored_sectors[y].excKey){
                            settingsValue["sct_" + stored_sectors[y].awpKey] = stored_sectors[y].excKey;
                }}};

// console.log("UpdateSettings settingsValue: " , settingsValue);
// console.log("upload_student_mapping_url " , upload_student_mapping_url);
                $.ajax({
                    type: "POST",
                    url: upload_student_mapping_url,
                    data: settingsValue,
                    success: function (msg) { console.log (msg);},
                    error: function (xhr, msg) {
                      console.log(msg + '\n' + xhr.responseText);
                    }
                });
            }; //if(stored_columns_length > 0)
        }
    }; // function (UpdateSettings)


//========= UPLOAD DATA =====================================
    $("#btn_import").on("click", function () {
console.log ("==========  UPLOAD DATA ==========");

        const import_student_load_url = $(this).data("import_student_load_url"); // get the url of the `Student_Import_Load` view

//--------- delete existing rows
        $("#id_tbody").html("");

//--------- shoq loading gif
        ShowLoadingGif(true);

        let rowLength = 0, colLength = 0;
        if(!!worksheet_data){rowLength = worksheet_data.length;};
        if(!!stored_columns){colLength = stored_columns.length;};
        if(rowLength > 0 && colLength > 0){

// ---  loop through all rows of worksheet_data
            let students = [];
// row <3 is for testing TODO: replace with rowLength
            for (let row = 0 ; row < rowLength; row++) {
                let DataRow = worksheet_data[row];

//------ loop through excel_columns
                let student = {};
                for (let idx = 0, len = excel_columns.length ; idx < len; idx++) {
                    if (!!excel_columns[idx].awpKey){
                        let awp_key = excel_columns[idx].awpKey;
                        if (!!DataRow[idx]){
                            let value = DataRow[idx];
                            let new_value;
                            if (awp_key === "level"){
                                new_value = get_awpkey_from_storeditems(stored_levels, value);
                                if (!!new_value) {
                                    student[awp_key] = new_value;
                                }
                            } else if (awp_key === "sector"){
                                new_value = get_awpkey_from_storeditems(stored_sectors, value);
                                if (!!new_value) {
                                    student[awp_key] = new_value;
                                }
                            } else {
                                student[awp_key] = value;
                            }
                        }
                    }
                }; //for (let col = 1 ; col <colLength; col++)
                students.push(student);
            }  // for (let row = 0 ; row < 5; row++)

console.log("students ==>");
console.log( students);
            let parameters = {"students": JSON.stringify (students)};

            $.ajax({
                type: "POST",
                url: import_student_load_url,
                data: parameters,
                dataType:'json',
                success: function (response) {
console.log("========== response Upload Students ==>", typeof response,  response);

//--------- hide loading gif
                    ShowLoadingGif(false);

                    FillDataTableAfterUpload(response, worksheet_range);
                },
                error: function (xhr, msg) {
//--------- hide loading gif
                    ShowLoadingGif(false);

                    console.log(msg + '\n' + xhr.responseText);
                }
            });
        }; //if(rowLength > 0 && colLength > 0)
    }); //$("#btn_import").on("click", function ()
//========= END UPLOAD =====================================


    function get_awpkey_from_storeditems(stored_items, excKey) {
    //--------- lookup awpKey in stored_items PR2019-02-22
    //stored_sectors:  {awpKey: "32", caption: "c&m", excKey: "cm"}
        let awp_key;
        if (!!stored_items && !!excKey){
            for (let i = 0, len = stored_items.length ; i < len; i++) {
                if (!!stored_items[i].excKey){
                    if (stored_items[i].excKey.toLowerCase()  === excKey.toLowerCase() ){
                        if (!!stored_items[i].awpKey){
                            awp_key = stored_items[i].awpKey;
                            break;
        }}}}};
        return awp_key
    }

    function ShowLoadingGif(show) {
    //--------- show / hide loading gif PR2019-02-19
        let loading_img = $("#id_loading_img");
        let datatable = $("#id_table");
        if (show){
            loading_img.removeClass("display_hide")
                        .addClass("display_show");
            datatable.removeClass("display_show")
                       .addClass("display_hide");
        } else {
            loading_img.removeClass("display_show")
                       .addClass("display_hide");
            datatable.removeClass("display_hide")
                        .addClass("display_show");
        }
    }
    }); //$(document).ready(function() {
