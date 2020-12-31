

var file_types = {
    xls:"application/vnd.ms-excel",
    xlsx:"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"};

$(document).ready(function() {

// set global variables
    var div_info = document.getElementById('div_infoID');
    var para = document.createElement('p');

    var file_dialog = document.getElementById("filedialogID");
    file_dialog.addEventListener("change", handle_file_dialog, false);

    var worksheet_list = document.getElementById("SheetListID");
    worksheet_list.addEventListener("change", handle_worksheet_list, false);

    var checkbox_noheader = document.getElementById("checkBoxID");
    checkbox_noheader.addEventListener("change", handle_checkbox_noheader_changed); //, false);

    document.getElementById("btn_import").addEventListener("click", handle_upload_data) ;//, false);


    var selected_file = null;
    var workbook;
    var worksheet;
    var worksheet_range;
    var worksheet_data = [];

    var selected_no_header = false;
    var stored_worksheetname = "";
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
    };

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

//--------- fill DataTable
                        FillDataTable(worksheet_range);

            }}}
        }  // if(!!workbook)
    };  // function handle_worksheet_list()

//=========   handle_checkbox_noheader_changed   ======================
    function handle_checkbox_noheader_changed() {
        if(!!worksheet && !!worksheet_range) {
            selected_no_header = checkbox_noheader.checked;
            worksheet_data = FillWorksheetData(worksheet, worksheet_range, selected_no_header);
            FillDataTable(worksheet_range);
        }
    };

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
            // Thisway code executing stops till loading has finuished.
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
        //--------- fill DataTable
                                    FillDataTable(worksheet_range);

               }}}}}
            }; // reader.onload = function(event) {
       }; // if(!!sel_file){
    };  // function Get_Workbook(sel_file))


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
    };

//=========  FillDataTable  ========================================================================
    function FillDataTable(sheet_range) {
console.log("=========  function FillDataTable =========");

//--------- delete existing rows
        $("#theadID,#tbodyID ").html("");

        if(!!worksheet_data && !!excel_columns){
            // create a <tblHead> element
            var tblHead = document.getElementById('theadID');
            var tblBody = document.getElementById('tbodyID');

//--------- insert tblHead row of datatable
            var tblHeadRow = tblHead.insertRow();

            //PR2017-11-21 debug: error when StartColNumber > 1, j must start at 0
            //var EndIndexPlusOne = (sheet_range.EndColNumber) - (sheet_range.StartColNumber -1)

            //index j goes from 0 to ColCount-1, excel_columns index starts at 0, last index is ColCount-1
            for (let j = 0 ; j <sheet_range.ColCount; j++) {
                let cell = tblHeadRow.insertCell(-1);
                cell.innerHTML = "F" + j.toString();
                cell.setAttribute("id", "idTblCol_" + j.toString());
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
    };

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
    }; //function GetExcelValue

// +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

//========= UPLOAD DATA ===================================== 2019-02-14
    function handle_upload_data () {
console.log ("==========  UPLOAD DATA ==========");

        const ajax_importssi_upload_url = $(this).data("ajax_importssi_upload_url"); // get the url of the

        if(!!worksheet_data){
            var parameters = {
              "schemeitems": JSON.stringify (worksheet_data)
            };

            $.ajax({
                type: "POST",
                url: ajax_importssi_upload_url,
                data: parameters,
                success: function (msg) {
                    alert (msg);
                },
                error: function (xhr, msg) {
                    //console.log(msg + '\n' + xhr.responseText);
                }
            });
        }; //if(rowLength > 0 && colLength > 0)
    }; //$("#btn_import").on("click", function ()
//========= END UPLOAD =====================================

}); //$(document).ready(function() {
