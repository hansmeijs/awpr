

//========= CreateTable  ====================================
    function CreateTable(tableBase, header1, header2, headExc, headAwp, headLnk ) {
console.log("==== CreateMapTableSub  =========>>>", tableBase, header1, header2, headExc, headAwp, headLnk);
        let base_div = $("#id_basediv_" + tableBase);  // BaseDivID = "sct", "lvl", "col"
        // delete existing rows of tblColExcel, tblColAwp, tblColLinked
        base_div.html("");


        //append column header to base_div
        if(!!header1 || !!header2) {
            $("<div>").appendTo(base_div)
                .attr({id: "id_div_hd_" + tableBase})
                .addClass("c_columns_header");

            if(!!header1) {
                $("<p>").appendTo( "#id_div_hd_" + tableBase)
                    //header1 = "Link sectors"
                    .html("<b>" + header1 + "</b>");
            }
            if(!!header2) {
                $("<p>").appendTo( "#id_div_hd_" + tableBase)
                    //header2 = "Click to link or unlink sector"
                    .html("<b>###" + header2 + "</b>");
            }
        }
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
                        .on("click", handle_table_row_clicked);

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
                        .on("click", handle_table_row_clicked);
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
                        .on("click", handle_table_row_clicked);
                    $("<thead>").appendTo("#id_lnk_table_" + tableBase)
                            .attr({id: "id_sct_th_lnk_" + tableBase})
                            .html("<tr><td colspan=2>" + headLnk + "</td></tr>"); // headLnk: "Linked sectors"
                    $("<tbody>").appendTo("#id_lnk_table_" + tableBase)
                            .attr({id: "id_lnk_tbody_" + tableBase});

         }; //function CreateTable()
// ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
//========= CreateTableRows  ====================================
    function CreateTableRows(tableBase, stored_items, excel_items,
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
     }; //function CreateTableRows()



//=========   handle_table_row_clicked   ======================
    function handle_table_row_clicked(e) {  //// EAL: Excel Awp Linked table
        // function gets row_clicked.id, row_other_id, row_clicked_key, row_other_key
        // sets class 'highlighted' and 'hover'
        // and calls 'linkColumns' or 'unlinkColumns'
// currentTarget refers to the element to which the event handler has been attached
// event.target which identifies the element on which the event occurred.
console.log("=========   handle_table_row_clicked   ======================") ;
//console.log("e.target.currentTarget.id", e.currentTarget.id) ;

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








//========= function get_index_by_awpkey  ====================================
    function get_index_by_awpkey (objArray, awpKeyValue) {
    // function serches for awpKey "sector" or "level" in excel_columns
    // column is linked when awpKey exists in excel_columns
    // and returns row_index 12 PR2019-01-10
    // excCol_row: {index: 12, excKey: "Profiel", awpKey: "level", awpCaption: "Leerweg"}
        let col_index;
        if (!!objArray && !!awpKeyValue ) {
            for (let i = 0 ; i < objArray.length; i++) {
                let row = objArray [i];
                if (!!row.awpKey){
                    if (row.awpKey === awpKeyValue){
                        col_index = row.index;
                    break;
        }}}}
        return col_index;
    }

//========= function get_arrayRow_by_keyValue  ====================================
    function get_arrayRow_by_keyValue (objArray, arrKey, keyValue) {
        // Function returns row of array that contains Value in objKey PR2019-01-05
        // stored_columns[3]: {awpCol: "lastname", caption: "Last name", excCol: "ANAAM" }
        // excel_columns[0]:    {excCol: "ANAAM", awpCol: "lastname", awpCaption: "Achternaam"}
        let row;
        if (!!arrKey && !!keyValue){
            for (let i = 0 ; i < objArray.length; i++) {
                let obj = objArray[i];
                if (!!obj && !!obj[arrKey] ){
                    // convert number to string for text comparison
                    let obj_value;
                    if (typeof(obj[arrKey]) === "number"){
                        obj_value = obj[arrKey].toString();
                    } else {
                        obj_value = obj[arrKey];
                    }
                    let isEqual = false;

                    if (typeof(keyValue) === "string" && typeof(obj_value) === "string"){
                        isEqual = (keyValue.toLowerCase() === obj_value.toLowerCase())
                    } else {
                        isEqual = (keyValue === obj_value)
                    }
                    if (isEqual){
                        row = obj;
                        break;
        }}}}
        return row;
    }


//========= function get_object_value_by_key  ====================================
    function get_obj_value_by_key (obj, objKey) {
        // Function returns value of key in obj PR2019-02-19
        // obj:  {excCol: "ANAAM", awpCol: "lastname", awpCaption: "Achternaam"}
        let obj_value;
        if (!!obj && !!objKey){
            if (objKey in obj) {
                obj_value = obj[objKey];
            }
        }
        return obj_value;
    }




//========= function found_in_list_str  ======== PR2019-01-22
    function found_in_list_str(value, list_str ){
        // PR2019-01-22 returns true if ;value; is found in list_str
        let found = false;
        if (!!value && !!list_str ) {
            let n = list_str.indexOf(";" + value + ";");
            found = (n > -1);
        }
        return (found);
    }

//========= function found_in_list_str  ======== PR2019-01-28
    function found_in_array(array, value ){
        // PR2019-01-28 returns true if ;value; is found in array
        let found = false;
        if (!!array && !!value) {
            for (let x = 0 ; x < array.length; x++) {
            if (array[x] === value){
                found = true;
                break;
        }}}
        return found;
    }

//========= function replaceChar  ====================================
    function replaceChar(value){
        let newValue = '';
        if (!!value) {
            newValue = value.replace(/ /g, "_"); // g modifier replaces all occurances
            newValue = newValue.replace(/"/g, "_"); // replace " with _
            newValue = newValue.replace(/'/g, "_"); // replace ' with _
            newValue = newValue.replace(/\./g,"_"); // replace . with _
            newValue = newValue.replace(/\//g, "_"); // replace / with _
            newValue = newValue.replace(/\\/g, "_"); // replace \ with _
        }
        return newValue;
    }
//========= delay  ====================================
    //PR2019-01-13
    var delay = (function(){
      var timer = 0;
      return function(callback, ms){
      clearTimeout (timer);
      timer = setTimeout(callback, ms);
     };
    })();


    //////////////////////////////////

    //========= t_get_rowindex_by_orderby  ================= PR2020-06-30
    function t_get_rowindex_by_orderby(tblBody, search_orderby) {
        console.log(" ===== t_get_rowindex_by_orderby =====");
        console.log("search_orderby", search_orderby);
        let row_index = -1;
// --- loop through rows of tblBody_datatable
        if(search_orderby){
            if (typeof search_orderby === 'string' || search_orderby instanceof String) {
                search_orderby = search_orderby.toLowerCase()};
       //console.log("search_orderby", search_orderby);
            for (let i = 0, tblRow; tblRow = tblBody.rows[i]; i++) {
                let row_orderby = get_attr_from_el(tblRow, "data-orderby");
                console.log("row_orderby", row_orderby);
                if(row_orderby){
                    if (typeof row_orderby === 'string' || row_orderby instanceof String) {
                        row_orderby = row_orderby.toLowerCase()};
       //console.log("row_orderby", row_orderby);
                    if(search_orderby < row_orderby) {
    // --- search_rowindex = row_index - 1, to put new row above row with higher row_orderby
                        row_index = tblRow.rowIndex - 1;
        //console.log("search_orderby < row_orderby: row_index = ", row_index);
                        break;
        }}}}
        if(!row_index){row_index = 0}
        if(row_index >= 0){ row_index -= 1 }
        return row_index
    }  // t_get_rowindex_by_orderby


//========= HighlightSelectRow  ============= PR2019-10-22
    function HighlightSelectRow(tblBody_select, selectRow, cls_selected, cls_background){
        //console.log(" === HighlightSelectRow ===")
        // ---  highlight selected row in select table
        if(!!tblBody_select){
            // tblBody_select necessary. When selectRow = null all other rows must be deselected
            DeselectHighlightedTblbody(tblBody_select, cls_selected, cls_background)
            if(!!selectRow){
                // yelllow won/t show if you dont first remove background color
                selectRow.classList.remove(cls_background)
                selectRow.classList.add(cls_selected)
            }
        }
    }  //  HighlightSelectRow

//=========  DeselectHighlightedRows  ================ PR2019-04-30 PR2019-09-23
    function DeselectHighlightedRows(tr_selected, cls_selected, cls_background) {
        if(!!tr_selected){
            DeselectHighlightedTblbody(tr_selected.parentNode, cls_selected, cls_background)
        }
    }

//=========  DeselectHighlightedTblbody  ================ PR2019-04-30 PR2019-09-23
    function DeselectHighlightedTblbody(tableBody, cls_selected, cls_background) {
        //console.log("=========  DeselectHighlightedTblbody =========");
        //console.log("cls_selected", cls_selected, "cls_background", cls_background);

        if(!cls_selected){cls_selected = "tsa_tr_selected"}

        if(!!tableBody){
            let tblrows = tableBody.getElementsByClassName(cls_selected);
            for (let i = 0, tblRow, len = tblrows.length; i < len; i++) {
                tblRow = tblrows[i];
                if(!!tblRow){
                    tblRow.classList.remove(cls_selected)
                    if(!!cls_background){
                        tblRow.classList.add(cls_background)
                    };
                }
            }
        }
    }  // DeselectHighlightedTblbody

//========= get_tablerow_selected  =============
    function get_tablerow_selected(el_selected){
        // PR2019-04-16 function 'bubbles up' till tablerow element is found
        // currentTarget refers to the element to which the event handler has been attached
        // event.target identifies the element on which the event occurred.
        let tr_selected;
        let el = el_selected
        let break_it = false
        while(!break_it){
            if (!!el){
                if (el.nodeName === "TR"){
                    tr_selected = el;
                    break_it = true
                } else if (!!el.parentNode){
                    el =  el.parentNode;
                } else {
                    break_it = true
                }
            } else {
                break_it = true
            }
        }
        return tr_selected;
    };


//>>>>>>>>>>> FILL OPTIONS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

//========= t_FillSelectOptions  =======  // PR2020-09-30
    function t_FillSelectOptions(el_select, data_map, tblName, fldName, has_selectall, hide_none,
                selected_pk, selectall_text, select_text_none, select_text) {
        //console.log( "=== t_FillSelectOptions ", tblName);

// ---  fill options of select box
        let option_text = "";
        let row_count = 0

// --- loop through data_map
        if(!!data_map){
            for (const [map_id, map_dict] of data_map.entries()) {
                const pk_int = map_dict.id;
                const value = (map_dict[fldName]) ?  map_dict[fldName] : "---";

                option_text += "<option value=\"" + pk_int + "\"";
                if (pk_int === selected_pk) {option_text += " selected=true" };
                option_text +=  ">" + value + "</option>";
                row_count += 1

            }
        }  //   if(!!data_map){
        let select_first_option = false;

        // when 'all customers is selected (selected_customer_pk): there are no orders in selectbox 'orders'
        // to display 'all orders' instead of 'no orders' we make have boolean 'hide_none' = true
        if (!row_count && select_text_none && !hide_none){
            option_text = "<option value=\"\" disabled selected hidden>" + select_text_none + "...</option>"
        } else if (!!has_selectall){
            option_text = "<option value=\"0\">" + selectall_text + "</option>" + option_text;
        } else if (row_count === 1) {
            select_first_option = true
        } else if (select_text){
            option_text = "<option value=\"\" disabled selected hidden>" + select_text + "...</option>" + option_text;
        }
        el_select.innerHTML = option_text;
        // if there is only 1 option: select first option
        if (select_first_option){
            el_select.selectedIndex = 0
        }
        el_select.disabled = (!row_count)
    }  // t_FillSelectOptions