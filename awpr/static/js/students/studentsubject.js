
// PR2019-02-07 deprecated: $(document).ready(function() {
$(function() {
//console.log("document.ready");

    const cls_tr = "tr_base";
    /* const cls_td = "search_table_td";*/
    const cls_hover = "tr_hover";
    const cls_highlighted = "tr_highlighted";
    const cls_disabled = "tr_disabled";

    let schemeitems = [];
    let studentsubjects = [];
    let student = {};
    let sel_studsubj_id = 0;
    let sel_studsubj = {}

    let databox = $("#id_data");
    const student_list = databox.data("student_list");

// ---  add 'onclick' event handler to all table bodies
    // PR2019-02-09 debug. jQ fired event twice, JS works fine.
    // was: sel_tbody.on("click", HandleTableRowClicked);
    document.getElementById("id_search_tbody").addEventListener("click", HandleTableRowClicked);
    document.getElementById("id_picker_tbody").addEventListener("click", HandleTableRowClicked);
    document.getElementById("id_data_tbody").addEventListener("click", HandleTableRowClicked);

// ---  add 'keyup' event handler to filter input
    document.getElementById("id_search_filter").addEventListener("keyup", function() {
                delay(function(){HandleSearchFilterEvent("search");}, 250 );});
    document.getElementById("id_picker_filter").addEventListener("keyup", function() {
                delay(function(){HandleSearchFilterEvent("picker");}, 250 );});

    document.getElementById("id_btn_save").addEventListener("click", UploadStudentSubjects);


        $("#id_mod_btn_ok").on("click", function(){handle_mod_btn_ok();});
        $("#id_mod_btn_del").on("click", function(){handle_mod_btn_del();});
        $("#id_select_sjtp, #id_select_grtp").on("click", function(){
            SetButtonOkDisabled();
            });

// ---  disable save button
    //$("#id_btn_save").prop("disabled", true);

// ---  fill search

    FillTableRows("search", student_list);

//========= HandleSearchFilterEvent  ====================================
    function HandleSearchFilterEvent(TableName) {
        let filter_str = document.getElementById("id_" + TableName + "_filter").value;

        let item_list = [];
        switch (TableName){
        case "search":
            item_list = student_list;
            break;
        case "picker":
            item_list = schemeitems;
        }

        FillTableRows(TableName, item_list, filter_str);
    };

//========= HandleTableRowClicked  ====================================
    function HandleTableRowClicked(e) {
console.log("===  HandleTableRowClicked  =====") ;
        // PR2019-02-09 function gets id of clicked tablerow, highlights this tablerow

        // currentTarget refers to the element to which the event handler has been attached
        // event.target identifies the element on which the event occurred.

// ---  get clicked tablerow
        let tr_clicked = get_tablerow_clicked(e)
        if(!!tr_clicked) {

// NOT IN USE
// ---  get tr_clicked_id_str (attribute is always string)
//            let tr_clicked_id_str = "";
//            if(tr_clicked.hasAttribute("id")){tr_clicked_id_str = tr_clicked.getAttribute("id");}

// ---  extract TableName from "id_data_tr_4"
            const TableName = get_tablename(tr_clicked);

// ---  remove class 'highlighted' from all rows in this table
            let tbody_clicked = document.getElementById(tr_clicked.parentNode.id);
            for (let i = 0, len = tbody_clicked.rows.length, row; i <len; i++) {
                tbody_clicked.rows[i].classList.remove (cls_highlighted);
            }

            let btn_save_disabled = true;
            switch (TableName){
            case "search":
// ---  add class 'highlighted' to this tablerow
                tr_clicked.classList.add(cls_highlighted);
                SelectStudent(tr_clicked);
                break;
            case "picker":
// ---  skip if tablerow is disabled
                if (!tr_clicked.classList.contains(cls_disabled)){
// ---  add class 'highlighted' to this tablerow
                    tr_clicked.classList.add(cls_highlighted);
// ---  add StudentSubject to this tablerow
                    StudentSubject_add(tr_clicked);
                    btn_save_disabled = false;
                }
                break;
            case "data":
// ---  open Modal Form when clicked on data table (skip when disabled)
                if (!tr_clicked.classList.contains(cls_disabled)){
                // ---  add class 'highlighted' to this row
                //    tr_clicked.classList.add(cls_highlighted);
                //    StudentSubject_remove(tr_clicked);
                //    btn_save_disabled = false;
                    //OpenModal(item_list, tr_clicked_subj_id, sel_ssi_id, tblContainer, tableName);
                    OpenModal(tr_clicked)
                }
            }
// ---  set button 'Save' disabled
           // $("#id_btn_save").prop("disabled", btn_save_disabled);
        }  // if(!!tr_clicked)
        // from https://medium.com/@jacobwarduk/how-to-correctly-use-preventdefault-stoppropagation-or-return-false-on-events-6c4e3f31aedb
        return false;
    }; //function HandleTableRowClicked()


//========= OpenModal  ====================================
    function OpenModal(tr_clicked) {
console.log("===  OpenModal  =====") ;
console.log("tr_clicked", tr_clicked);

// ---  reset variables of selected studentsubject
        sel_studsubj_id = 0;
        sel_studsubj = {};


// ---  empty input boxes
        document.getElementById("id_input_pws_title").value = "";
        document.getElementById("id_input_pws_subjects").value = "";

// ---  get attr 'studsubj_id' of tr_clicked (attribute is always string, function converts it to number)
        // new new_studsubj_id is negative ssi_id: -1592
        sel_studsubj_id = get_attr_from_tablerow(tr_clicked, "studsubj_id");

// ---  get selected studentsubject object
        sel_studsubj = get_studentsubject (sel_studsubj_id);

console.log("sel_studsubj");
console.log( sel_studsubj);

        if (!!sel_studsubj){
// ---  set header
            let subj_name = "";
            if (!!sel_studsubj.subj_name){subj_name = sel_studsubj.subj_name;} // subject.name
            if (!!sel_studsubj.sjtp_name){subj_name = subj_name + " (" + sel_studsubj.sjtp_name.toLowerCase() + ")";};
            $("#id_mod_header").html(subj_name);

            document.getElementById("id_input_pws_title").value = sel_studsubj.pws_title;
            document.getElementById("id_input_pws_subjects").value = sel_studsubj.pws_subjects;


            let extra_counts = true // (!!sel_studsubj.extra_counts && sel_studsubj.extra_counts === 1);
            let mod_checkbox = $("#id_mod_checkbox");
            // remove all checkboxes
            mod_checkbox.empty();
            // check if "chal" in scheme.fields, if so: add checkbox

            // CreateCheckbox(sel_checkbox, field, caption, is_checked, disabled, tooltiptext)
            CreateCheckbox(mod_checkbox, "extracounts", databox.data("chk_extracounts_cap"), sel_studsubj.extra_counts, false);
            CreateCheckbox(mod_checkbox, "extranocount", databox.data("chk_extranocount_cap"), sel_studsubj.extra_nocount, false);
            CreateCheckbox(mod_checkbox, "choicecombi", databox.data("chk_choicecombi_cap"), sel_studsubj.choice_combi, false);



// ---  show modal
            $("#id_modal_cont").modal({backdrop: true});
        }

}; // function OpenModal

//========= function closeModal  =============
    function closeModal() {
        $('#id_modal_cont').modal('hide');
    }

//========= SelectStudent  ====================================
    function SelectStudent(tr_clicked) {
        // PR2019-01-15 function gets tr_clicked.id, row_other_id, tr_clicked_key, row_other_key
        // sets class 'highlighted' and 'hover'

        let tr_clicked_stud_id = "",  tr_clicked_stud_name = "";
        if(tr_clicked.hasAttribute("stud_id")){tr_clicked_stud_id = tr_clicked.getAttribute("stud_id");}
        if(tr_clicked.hasAttribute("stud_name")){tr_clicked_stud_name = tr_clicked.getAttribute("stud_name");}
console.log("-------------- SelectStudent  --------------");

// ---  reset tables
        student = {};
        studentsubjects = [];
        schemeitems = [];
        sel_studsubj_id = 0;
        sel_studsubj = {};

        $("#id_content_header_name").html("...");
        $("#id_content_header_level_sector").html("");
        $("#id_data_tbody").html("");
        $("#id_picker_tbody").html("");

// ---  get scheme-item when all required id's are entered
        let parameters = {"stud_id": tr_clicked_stud_id};
        let url_str = $("#id_data").data("ajax_studsubj_download_url");

console.log("parameters", parameters);
console.log("url_str", url_str);
        response = "";
        $.ajax({
            type: "POST",
            url: url_str,
            data: parameters,
            dataType:'json',
            success: function (response) {
console.log("-------------- response  --------------");
console.log(response);

                student = {};
                studentsubjects = [];
                schemeitems = [];
                if (response.hasOwnProperty("student")){student = response.student;}
                if (response.hasOwnProperty("studentsubjects")){studentsubjects = response.studentsubjects;}
                if (response.hasOwnProperty("schemeitems")){schemeitems = response.schemeitems;}

                if (!!student.name){$("#id_content_header_name").html(student.name);}
                if (!!student.level_sector){$("#id_content_header_level_sector").html(student.level_sector);}

// ---  fill TableRows
                FillTableRows("picker", schemeitems);
                FillTableRows("data", studentsubjects);
            },
            error: function (xhr, msg) {
                alert(msg + '\n' + xhr.responseText);
            }
        });
    }; // function SelectStudent

//========= StudentSubject_add  ====================================
    function StudentSubject_add(tr_clicked) {
console.log("===  StudentSubject_add  =====") ;
        // PR2019-02-11 add studsubj to studentsubjects
        // tr_clicked from table pickers, has ssi_id (string type), does not have studsubj_id
console.log("tr_clicked:", tr_clicked);

// ---  reset variables
        sel_studsubj_id = 0;
        sel_studsubj = {};

// ---  get ssi_id from tr_clicked
        const tr_clicked_ssi_id = get_attr_from_tablerow(tr_clicked, "ssi_id");
console.log("tr_clicked_ssi_id:", tr_clicked_ssi_id);

// ---  check if studentsubject with the same ssi exists in studentsubjects
        // PR2019-02-10 DEBUG: !!sel_studsubj = true when sel_studsubj = {}, therefore check sel_studsubj.studsubj_id
        // changed to found_id_in_studsub
        let ssi_id_exists = found_id_in_studsub(tr_clicked_ssi_id, "ssi_id", false); //skip_del = false: include deleted records

console.log("ssi_id_exists", ssi_id_exists);

        if (ssi_id_exists) {
            // if  ssi_id exists in studsubj it must be a deleted row. Set mode to 'c'.
            sel_studsubj = get_studentsubject_by_id(tr_clicked_ssi_id, "ssi_id")
            sel_studsubj.mode = "c";
        } else {
// ---   add row
            // new new_studsubj_id is negative ssi_id
            let new_studsubj_id = tr_clicked_ssi_id * -1;

// ---  create new studentsubject object
            // lookup schemeitem with this ssi_id
            let schemeitem = get_schemeitem(tr_clicked_ssi_id)
            if (!!schemeitem.ssi_id){
                let new_studentsubject = {
                    "mode": "c",
                    "studsubj_id": new_studsubj_id,
                    "stud_id": student.stud_id,
                    "ssi_id": schemeitem.ssi_id,
                    "subj_id": schemeitem.subj_id,
                    "subj_name": schemeitem.subj_name,
                    "sjtp_id": schemeitem.sjtp_id,
                    "sjtp_name": schemeitem.sjtp_name,
                    "sjtp_one": 0,
                    "sequence": schemeitem.sequence,
                    "extra_nocount": 0,
                    "extra_counts": 0,
                    "choice_combi": 0,
                    "pws_title": "",
                    "pws_subjects": ""
                }
//console.log("new_studentsubject", new_studentsubject);

// ---  lookup sequence in studentsubjects, to insert new row in right order
                let selected_index = 0, found = false;
                for (let x = 0, len = studentsubjects.length; x < len; x++) {
                    let row = studentsubjects[x];
                    if (!!row.sequence  && !!schemeitem.sequence && row.sequence > schemeitem.sequence) {
                        selected_index = x;
                        found = true;
                        break;
                }}
                if(found){
// ---  add row at selected index
                    studentsubjects.splice(selected_index, 0, new_studentsubject);
                } else {
// ---  add row at end of list
                    studentsubjects.push(new_studentsubject);
                }
            }
        }

        FillTableRows("picker", schemeitems, "", tr_clicked_ssi_id);
        FillTableRows("data", studentsubjects, "", tr_clicked_ssi_id);

    }; // function StudentSubject_add


//========= handle_mod_btn_ok  ====================================
    function handle_mod_btn_ok() {
console.log("===  handle_mod_btn_ok  =====") ;

        // check for changes, save to studentsubj when modified
        if (!!sel_studsubj) {
            sel_studsubj.pws_title = document.getElementById("id_input_pws_title").value
            sel_studsubj.pws_subjects = document.getElementById("id_input_pws_subjects").value

        }

        closeModal();
    }; // function handle_mod_btn_ok

//========= handle_mod_btn_del  ====================================
    function handle_mod_btn_del() {
console.log("===  handle_mod_btn_del  =====") ;
        // PR2019-02-11 removes tr_clicked from studentsubjects
        // by setting 'mode' = 'd'

        if (!!sel_studsubj) {
            // make mode 'deleted'
            sel_studsubj["mode"] = "d"
    console.log("sel_studsubj", sel_studsubj);
        let tr_clicked_ssi_id = ""
            FillTableRows("picker", schemeitems, "", tr_clicked_ssi_id);
            FillTableRows("data", studentsubjects, "", tr_clicked_ssi_id);
        };

        closeModal();
    }; // function handle_mod_btn_del

//========= UploadStudentSubjects  ====================================
    function UploadStudentSubjects(tr_clicked) {
console.log("===  UploadStudentSubjects  =====") ;
        // PR2019-02-10 function uploads StudentSubjects

// ---  disable save button
    //$("#id_btn_save").prop("disabled", true);

        let parameters = {"studentsubjects": JSON.stringify (studentsubjects)};

console.log("parameters");
console.log(parameters);

        response = "";
        msg_txt = "";

console.log('----ajax_studsubj_upload_url');
        $.ajax({
            type: "POST",
            url: $("#id_data").data("ajax_studsubj_upload_url"),
            data: parameters,
            dataType:'json',
            success: function (response) {
console.log("========== response UploadStudentSubject ==>", typeof response,  response);

                studentsubjects = response["studentsubjects"];
                schemeitems = response["schemeitems"];
                err_code = response["err_code"];

console.log("========== studentsubjects ==<",typeof studentsubjects, ">", studentsubjects);
console.log("========== schemeitems ==<",typeof schemeitems, ">", schemeitems);
//console.log("========== err_code ==<",typeof err_code, ">", err_code);

// ---  fill TableRows
                FillTableRows("picker", schemeitems);
                FillTableRows("data", studentsubjects);

                if (!!err_code){
                    err_msg =  databox.data("err_msg01") + " " + databox.data(err_code);
                    alert(err_msg);
                }
            },
            error: function (xhr, msg) {
                alert(msg + '\n' + xhr.responseText);
            }
        });
//console.log("+++++++++ schemeitems ==>", schemeitems);

    }; // function AddSubject

//========= FillTableRows  ==================================== PR2019-02-07
    function FillTableRows(TableName, item_list, filter_str, just_clicked_ssi_id) {
console.log("++++++++ FillTableRows +++++++++", TableName);
console.log(item_list);

// ---  remove all tablerows
        let tblBody = $("#id_" + TableName + "_tbody");
        tblBody.html("");
        let sel_id_found = false;

// ---  store stud_id in sel_stud_id
        let sel_stud_id = "";
        if (TableName === "search"){
            if(!!student){sel_stud_id = student.stud_id;};
        };

// ---  loop through array item_list
        if (!!item_list){
            for (let i = 0, len = item_list.length; i <len; i++) {
                let row = item_list[i];

// ---  when filter: filter by filter_str
                let skip_row = false;
                if (!!filter_str && !!row.name) {
                    // make search case insensitive
                    let add_row = row.name.toLowerCase().indexOf(filter_str.toLowerCase()) >= 0;
                    skip_row = !add_row;
                }

// ---  when picker: skip items who's ssi_id are already in studentsubjects and are not deleted
                let subj_id_exists = false, sjtp_one_allowed = false;
                switch (TableName) {
                case "picker":
                    skip_row = (found_id_in_studsub(row.ssi_id, "ssi_id", true)); //skip_del = true
                    break;
// ---  when data: skip deleted items
                case "data":
                    if (row.mode === "d"){
                        skip_row = true;
                    }
                }

// ---  add tablerow if not skip
                if (!skip_row){
                    const idTableRow = "id_" + TableName + "_tr_" + i.toString();
                    const XidTableRow = "#" + idTableRow;

                // set attributes of <tr>
                    let attrib = {};
                    attrib ["id"] = idTableRow;
                    if (!!row.id){attrib ["stud_id"] = row.id;}
                    if (!!row.name){attrib ["stud_name"] = row.name;}
                    if (!!row.ssi_id){attrib ["ssi_id"] = row.ssi_id;}
                    if (!!row.studsubj_id){attrib ["studsubj_id"] = row.studsubj_id;}

    // ---  add <tr>
                    $("<tr>").appendTo(tblBody)  // .appendTo( "#id_lnk_tbody_lvl" )
                        .attr(attrib)
                        .addClass(cls_tr);
                    let TableRow = $(XidTableRow);

    // ---  add class cld_hi if it is the selected row
                    if (!!sel_stud_id && row.id === sel_stud_id){
                        TableRow.addClass(cls_highlighted);
                        sel_id_found = true;
                    };

// ---  disable picker TableRow when subject is already in studentsubjects or  sjtp_one_allowed
                    if (TableName === "picker"){
                        if (subj_id_exists || sjtp_one_allowed){
                            TableRow.addClass(cls_disabled);
                        } else {
                            TableRow.mouseenter(function(){TableRow.addClass(cls_hover);});
                            TableRow.mouseleave(function(){TableRow.removeClass(cls_hover);});
                        };
                    } else {

// ---  add class hover if not disabled
                        TableRow.mouseenter(function(){TableRow.addClass(cls_hover);});
                        TableRow.mouseleave(function(){TableRow.removeClass(cls_hover);});
                    }  //  if (TableName === "picker")

// --- if new appended row: highlight row for 2 seconds (just_clicked_ssi_id only used in picker and data table)
                    if (!!just_clicked_ssi_id && !!row.ssi_id) {
                        let row_ssi_id_str = row.ssi_id.toString();
                        if (just_clicked_ssi_id === row_ssi_id_str) {
                           $(XidTableRow).addClass(cls_highlighted);
                           setTimeout(function (){$(XidTableRow).removeClass(cls_highlighted);}, 2000);
                        }
                    }
// ---  add <td>
                    switch (TableName){
                    case "search":
                        $("<td>").appendTo(XidTableRow)
                            .html(row.name);
                            //.addClass(cls_td); class "search_table_td" replaced by ".search_table_tr > td"
                        break;
                    case "picker":
                        $("<td>").appendTo(XidTableRow)
                            .html(row.subj_name);
                            //.addClass(cls_td); class "search_table_td" replaced by ".search_table_tr > td"
                        $("<td>").appendTo(XidTableRow)
                            .html(row.sjtp_name);
                            //.addClass(cls_td); class "search_table_td" replaced by ".search_table_tr > td"
                        break;
                    case "data":
                        $("<td>").appendTo(XidTableRow)
                            .html(row.subj_name);
                            //.addClass(cls_td); class "search_table_td" replaced by ".search_table_tr > td"
                        $("<td>").appendTo(XidTableRow)
                            .html(row.sjtp_name);
                            //.addClass(cls_td); class "search_table_td" replaced by ".search_table_tr > td"

                        break;
                    };
                };
            }
        }
     }; //function FillTableRows()


//========= CreateCheckbox  ============= PR2019-02-11
    function CreateCheckbox(sel_checkbox, field, caption, is_checked, disabled, tooltiptext) {
        const id_chk = "id_mod_" + field;
        $("<div>").appendTo(sel_checkbox)
            .attr({"id": id_chk + "_div"})
            .addClass("checkbox ");
        let chk_div = $("#" +id_chk + "_div");

        // add tooltip
        if (!!tooltiptext){
            chk_div.attr({"data-toggle": "tooltip", "title": tooltiptext});
            chk_div.tooltip();
        }

        $("<input>").appendTo(chk_div)
                    .attr({"id": id_chk + "_chk",  "type": "checkbox", "checked": is_checked})
                    .prop("disabled", disabled)
                    .addClass("check_list mr-2");
                    //.html("<input id='" + id_chk + "' class='check_list mr-2' type='checkbox' checked='false'>" + caption );

        $("<label>").appendTo("#" + id_chk + "_div")
                    .attr({"id": id_chk + "_lbl", "for": id_chk + "_chk" })
                    .html(caption);

    }

//========= get_schemeitem  =============
    function get_schemeitem(sel_ssi_id_int) {
//console.log("==== get_schemeitem  ====")
//console.log("sel_ssi_id_int", sel_ssi_id_int, typeof sel_ssi_id_int)
        // function loops through schemeitems to find selected schemeitem  PR2019-02-12
        let return_row = {};
        for (let i = 0, row = {}, len = schemeitems.length ; i < len; i++) {
            row = schemeitems[i];
            if (!!sel_ssi_id_int && !!row.ssi_id){
                if (row.ssi_id === sel_ssi_id_int){
                    return_row = row
                    break;
                };
        }};
//console.log("return_row", return_row)
        return return_row;
    }

//========= get_studentsubject  =============
    function get_studentsubject(studsubj_id) {
        // function loops through studentsubjects to find selected studentsubject  PR2019-02-12
        let return_row = {};
        // studsubj_id is number, therefore studsubj_id = 0 is skipped!
        if(!!studsubj_id){
            for (let i = 0, row = {}, len = studentsubjects.length ; i < len; i++) {
                row = studentsubjects[i];
                if (!!studsubj_id && !!row.studsubj_id && row.studsubj_id === studsubj_id){
                    return_row = row
                    break;
            }};
        }
        return return_row;
    };

//========= get_studentsubject_by_id  =============
    function get_studentsubject_by_id(sel_id, key) {
//console.log("---- get_studentsubject  ---- ")
//console.log("sel_id: ", sel_id, typeof sel_id)
        // function loops through studentsubjects to find selected studentsubject  PR2019-02-12
        // returns first found row when multiple rows with the same ssi_id found (should not be possible)
        // NB:   !!studentsubject = true when studentsubject = {}, check for studentsubject.studsubj_id
        //       !!sel_id = false when sel_id = 0
        let return_row = {};
        if (!!sel_id){
            for (let i = 0, row = {}, len = studentsubjects.length ; i < len; i++) {
                row = studentsubjects[i];
                if (!!row[key]){
                    if (row[key] === sel_id){
                        return_row = row;
                        break;
        }}}};
//console.log("return_row", return_row)
        return return_row;
    };

//========= ExistsInStudentsubjects  ============= PR2019-02-11
    function ExistsInStudentsubjects(sel_subj_id, sel_ssi_id, sjtp_id, sjtp_one) {
        // function loops through studentsubjects to find subject of selected schemeitems
        // subjects that are already in studentsubjects will be disabled in list available subjects
        // subjects with type 'one-allowed' will be disabled if there is already one in studentsubjects

        let subj_id_exists = false, ssi_id_exists = false, sjtp_one_allowed = false;
        for (let i = 0, len = studentsubjects.length ; i < len; i++) {
            let row = studentsubjects[i];


// ---  check if sel_subj_id exists in studentsubjects - check also the deleted items
            if (!!sel_subj_id && !!row.subj_id && row.subj_id === sel_subj_id) {
                subj_id_exists = true;
            };
// ---  skip deleted studentsubjects
            if (!!row.mode && row.mode !== 'd'){

// ---  check if ssi exists
                if (!!sel_ssi_id && !!row.ssi_id && row.ssi_id === sel_ssi_id) {
                    ssi_id_exists = true;
                };
// ---  check if this subject had subjecttype 'one_allowed' sjtp_one
                if (!!sjtp_id && !!row.sjtp_id && row.sjtp_id === sjtp_id){
                    if (!!sjtp_one && sjtp_one === 1) {
                        sjtp_one_allowed = true;
                    };
                };
            }
        };
        return {"subj_id_exists": subj_id_exists,
                "ssi_id_exists": ssi_id_exists,
                "sjtp_one_allowed": sjtp_one_allowed};
    }




//========= found_ssi_in_studsub  ============= PR2019-02-12
    function found_id_in_studsub(sel_ssi_id, key, skip_del) {
        // function loops through studentsubjects to find ssi_id of selected schemeitems
        // subjects that are already in studentsubjects will be disabled in list available subjects
        // subjects with type 'one-allowed' will be disabled if there is already one in studentsubjects
//console.log("found_id_in_studsub", sel_ssi_id, key, skip_del  )
        let found = false;
        if (!!sel_ssi_id) {
            for (let i = 0, len = studentsubjects.length ; i < len; i++) {
                let row = studentsubjects[i];
//console.log("row", row)
                if (!!row[key] ){
// ---  skip deleted studentsubjects, only if skip_del = true
                    let skip = (skip_del && !!row.mode && row.mode === 'd');
// ---  skip deleted studentsubjects
                    if (!skip){
// ---  check if value of key exists
                        if (row[key] === sel_ssi_id) {
                            found = true;
                            break;
                        };
                    };
                };
            };
        };
//console.log("found", found)
        return found;
    };

//========= get_tablename  =============
    function get_tablename(idTableRow){
    // ---  get tableName PR2018-02-09
            // extract 'search' from "id_search_tr_4"
            let tableName = "";
            if (!!idTableRow){
                let arr_id = idTableRow.id.split("_");
                if (!!arr_id){tableName = arr_id[1];};
            };
            return tableName;
    };

//========= get_attr_from_tablerow  =============
    function get_attr_from_tablerow(tr_clicked, key){
    // ---  get attr value from key = "ssi_id" or "studsubj_id PR2018-02-12
        let id = 0;
        if(tr_clicked.hasAttribute(key)){
            const id_str = tr_clicked.getAttribute(key);
            if (!Number.isNaN(id_str)) {id = Number(id_str)};
        };
        return id;
    };

//========= get_tablerow_clicked  =============
    function get_tablerow_clicked(e){
        // PR2019-02-09 function gets id of clicked tablerow, highlights this tablerow
        // currentTarget refers to the element to which the event handler has been attached
        // event.target identifies the element on which the event occurred.
        let tr_clicked;
        if(!!e.target) {
            // e.target can either be TR or TD (when clicked 2nd time, apparently)
            switch(e.target.nodeName){
             case "TD":
                tr_clicked =  e.target.parentNode;
                break;
             case "TR":
                tr_clicked =  e.target;
            }
        };
        return tr_clicked;
        };
}); //$(document).ready(function()