
// deprecated: $(document).ready(function() {
// $(function() {
$(document).ready(function() {
console.log("ready");
    let databox = $("#id_data");
    const dep_list = databox.data("deps");
    const level_list = databox.data("levels");
    const sector_list = databox.data("sectors");

console.log("dep_list", dep_list);
console.log("level_list", level_list);
console.log("sector_list", sector_list);

        let sel_dep_id = "";
        let sel_lvl_id = "";
        let sel_sct_id = "";
        let sel_lvl_req = false;
        let sel_sct_req = false;

        let scheme = [];
        let subjects = [];
        let subjecttypes = [];
        let schemeitems = [];

        let mod_data = [];

        const cls_hover = "search_table_hover";

        $("#id_mod_btn_ok").on("click", function(){handle_mod_btn_ok();});
        $("#id_mod_btn_del").on("click", function(){handle_mod_btn_del();});
        $("#id_select_sjtp, #id_select_grtp").on("click", function(){
            SetButtonOkDisabled();
            });

        // PR2019-01-17
        // always set table 'department'

        CreateTable("sel", "dep", databox.data("txt_sel_dep"), dep_list, sel_dep_id, 120, 100, "blue");

//========= HandleSearchFilterEvent  ====================================
    function HandleSearchFilterEvent(tblContainer, tblName, item_list) {
        let filter_str = document.getElementById("id_" + tblContainer + "_" + tblName + "_filter").value;
console.log("=== HandleSearchFilterEvent  =====");
console.log(" filter_str  ", filter_str);
        CreateTableRows(tblContainer, tblName, item_list, 0, 0, filter_str);
    };

//========= HandleTableRowClicked  ====================================
    function HandleTableRowClicked(e) {
console.log("===>  HandleTableRowClicked  =====") ;
        // PR2019-01-15 function gets row_clicked.id, row_other_id, row_clicked_key, row_other_key
        // sets class 'highlighted' and 'hover'

// currentTarget refers to the element to which the event handler has been attached
// event.target identifies the element on which the event occurred.

// e.currentTarget.id: "id_sel_dep_table"
// e.target.id: "id_sel_dep_tr_0"

        const cls_tr = "search_table_tr";
        const cls_hv = "search_table_hover";
        const cls_hl = "search_table_highlighted";

        if(!!e.target) {
// ---  get tblContainer and tableName
            let cur_table = e.currentTarget;
            // extract 'sel' from "id_sel_dep_table"
            let arr_id = cur_table.id.split("_");
            const tblContainer = arr_id[1]; //'sel', 'subj'
            // extract 'dep' from "id_sel_dep_table"
            const tableName = arr_id[2]; //'dep', 'sct', 'lvl'

// ---  get row_clicked
            // e.target can either be TR or TD (when clicked 2nd time, apparently)
            let row_clicked;
            switch(e.target.nodeName){
             case "TD":
                row_clicked =  e.target.parentNode;
                break;
             case "TR":
                row_clicked =  e.target;
            }

// ---  get sel_id and table_body_clicked from TR
            if(!!row_clicked) {

//console.log("row_clicked:", row_clicked) ;
                let row_clicked_sel_id = "", row_clicked_subj_id = "",  row_clicked_ssid = "";

                // sel_id contains id of dep, lvl or sct
                if(row_clicked.hasAttribute("sel_id")){row_clicked_sel_id = row_clicked.getAttribute("sel_id");}
                if(row_clicked.hasAttribute("subj_id")){row_clicked_subj_id = row_clicked.getAttribute("subj_id");}
                if(row_clicked.hasAttribute("ssi_id")){row_clicked_ssid = row_clicked.getAttribute("ssi_id");}
                let table_body_clicked = document.getElementById(row_clicked.parentNode.id);

// ---  tblContainer 'Select subject scheme'
                switch (tblContainer){
                case "sel":

            // delete existing scheme-item tables
                    $("#id_ssi_header" ).empty(); // remove all child nodes
                    $("<p>").appendTo( $("#id_ssi_header"))
                        .html("<b>" + "Subject scheme items" + "</b>");

                    $("#id_ssi_subj_div" ).remove();
                    $("#id_ssi_ssis_div" ).remove();

                    switch (tableName){
                    case "dep":
            // reset select tables sel_lvl and sel_sct
                        sel_dep_id = "";
                        sel_lvl_id = "";
                        sel_sct_id = "";
                        sel_lvl_req = false;
                        sel_sct_req = false;
                        // delete existing table level
                        $("#id_sel_lvl_div" ).remove();
                        // delete existing table sector
                        $("#id_sel_sct_div" ).remove();
                        break;
                    case "lvl":
                        sel_lvl_id = "";
                        break;
                    case "sct":
                        sel_sct_id = "";
                        break;
                    };
                    break;

// ---  tblContainer "Subject Scheme Items"
                case "ssi":
                    let item_list = [] , sel_ssi_id;
                    if (tableName === "subj") {
                        item_list = subjects;
                    } else if ( tableName === "ssis") {
                        item_list = schemeitems;
                        sel_ssi_id = row_clicked_ssid;
                    };
                    openModal(item_list, row_clicked_subj_id, sel_ssi_id, tblContainer, tableName);
                };

// ---  if row is already selected: deselect row
                if(row_clicked.classList.contains(cls_hl)) {
                    row_clicked.classList.remove(cls_hl, cls_hv);
                    row_clicked.classList.add(cls_tr);

                } else {

// ---  remove class 'highlighted' from all other rows in this table
                    for (let i = 0, row; row = table_body_clicked.rows[i]; i++) {
                        if (row.classList.contains(cls_hl)) {row.classList.remove(cls_hl)}
                        if (!row.classList.contains(cls_tr)) {row.classList.add(cls_tr)}
                    }
// ---  add class 'highlighted' to this row - not for table subject or ssi
                    switch (tblContainer){
                    case "sel":
                        row_clicked.classList.add(cls_hl);
                    };

                    switch (tableName){
                    case "dep":
                        sel_dep_id = row_clicked_sel_id;

// ---  check if lvl and sct are required in new dep, if not: hide
                        let sel_lvl_caption = "Level";
                        let sel_sct_caption= "Sector";
                        // dep_list[0]: {abbrev: "Vsbo", id: 11, level_req: true, name: "V... S... B...", sector_req: true}
                        let dep = get_arrayItem_by_keyValue (dep_list, "id", row_clicked_sel_id);
                        if (!!dep){
                            if (!!dep["level_req"]){sel_lvl_req = dep["level_req"];}
                            if (!!dep["sector_req"]){sel_sct_req = dep["sector_req"];}

                            if (!!dep["level_caption"]){sel_lvl_caption = dep["level_caption"];}
                            if (!!dep["sector_caption"]){sel_sct_caption = dep["sector_caption"];}
                        }
                        let tblWidth = 120,tblHeight = 100;
                        if (!!sel_lvl_req){
                            CreateTable("sel", "lvl", sel_lvl_caption, level_list, sel_dep_id, tblWidth, tblHeight, "blue");
                        }
                        if (!!sel_sct_req){
                            // set tablewidth of profiel to 240
                            if (!sel_lvl_req){tblWidth = 240}
                            CreateTable("sel", "sct", sel_sct_caption, sector_list, sel_dep_id, tblWidth, tblHeight, "blue");
                        }

                        // check if selected lvl and sct are allowed, if not: deselect
                        // if dep, lvl and sct are selected: retrieve schemeitems
                        break;
                    case "lvl":
                        sel_lvl_id = row_clicked_sel_id;
                        // if dep, lvl and sct are selected: retrieve schemeitems

                        break;
                    case "sct":
                        sel_sct_id = row_clicked_sel_id;
                        break;
                    };

                }  // if(row_clicked.classList.contains(cls_hl))

// ---  if dep, lvl and sct are selected: retrieve schemeitems, if not
                switch (tblContainer){
                case "sel":
                    let dep_ok = false, lvl_ok = false, sct_ok = false;
                    dep_ok = (!!sel_dep_id);
                    if(!sel_lvl_req){
                        lvl_ok = true;
                    } else if(!!sel_lvl_id){
                        lvl_ok = true;
                    }
                    if(!sel_sct_req){
                        sct_ok = true;
                    } else if(!!sel_sct_id){
                        sct_ok = true;
                    }

// ------------get scheme-item when all required id's are entered
                    if(dep_ok && lvl_ok && sct_ok){
                        scheme = [];
                        schemeitems = [];
                        subjects = [];
                        subjecttypes = [];

                        const ajax_schemeitems_download_url = $("#id_data").data("ajax_schemeitems_download_url");
                        let parameters = {"dep_id": sel_dep_id, "lvl_id": sel_lvl_id, "sct_id": sel_sct_id };
// console.log(parameters);
                        response = "";
                        $.ajax({
                            type: "POST",
                            url: ajax_schemeitems_download_url,
                            data: parameters,
                            dataType:'json',
                            success: function (response) {
console.log("-------------- response  --------------");
                                scheme = [];
                                schemeitems = [];
                                subjects = [];
                                subjecttypes = [];
                                    if (response.hasOwnProperty("scheme")){scheme = response.scheme;}
                                    if (response.hasOwnProperty("schemeitems")){schemeitems = response.schemeitems;}
                                    if (response.hasOwnProperty("subjects")){subjects = response.subjects;}
                                    if (response.hasOwnProperty("subjecttypes")){subjecttypes = response.subjecttypes;}
                                    if (response.hasOwnProperty("gradetypes")){gradetypes = response.gradetypes;}

console.log('scheme', scheme, typeof scheme);
console.log('schemeitems', schemeitems, typeof schemeitems);
console.log('subjects', subjects, typeof subjects);
console.log('subjecttypes', subjecttypes, typeof subjecttypes);
console.log('gradetypes', gradetypes, typeof gradetypes);

                                    CreateTableSubjectsSsis ();
                            },
                            error: function (xhr, msg) {
                                console.log(msg + '\n' + xhr.responseText);
                            }
                        });
                    }
                    break;
                };
            } //  if(!!e.target.nodeName === "TR") {
        }  //  if(!!e.target) {
    };  // HandleTableRowClicked

//========= handle_mod_btn_ok  ====================================
    function handle_mod_btn_ok() {
        // PR2019-02-02
console.log("======== handle_mod_btn_ok  ===========");

// ---  get info of selected subjecttype
        //jQuery:
        //let selectedOption = $("#id_select_sjtp").children("option:selected");
        //let sjtp_name = selectedOption.text();
        //let sjtp_id = "", sjtp_sequ = 0;
        //if (selectedOption.hasAttribute("sjtp_id")){sjtp_id = selectedOption.getAttribute("sjtp_id")}
        //if (selectedOption.hasAttribute("sjtp_sequ")){sjtp_sequ = selectedOption.getAttribute("sjtp_sequ")}

// ---  get info of selected subject  type
        let sjtp_id = "";
        let sel_sjtp = document.getElementById('id_select_sjtp');
        let sel_sjtp_option = sel_sjtp.options[sel_sjtp.selectedIndex];
        if (!!sel_sjtp_option && sel_sjtp_option.hasAttribute("sjtp_id")){
            sjtp_id = sel_sjtp_option.getAttribute("sjtp_id");
        }
        mod_data["sjtp_id"] = sjtp_id;

// ---  get info of selected gradetype
        //let selectedGradetype = $("#id_select_grtp").children("option:selected");
        //let sel_grtp_id = selectedGradetype.val();
        ////let grtp_name = selectedGradetype.text();
        //mod_data["sel_grtp_id"] = sel_sjtp_id;

        let grtp_id = "";
        let sel_grtp = document.getElementById('id_select_grtp');
        let sel_grtp_option = sel_grtp.options[sel_grtp.selectedIndex];
        if (!!sel_grtp_option && sel_grtp_option.hasAttribute("grtp_id")){
            grtp_id = sel_grtp_option.getAttribute("grtp_id");
        }
        mod_data["grtp_id"] = grtp_id;

// ---  get info of weightSE, weightCE.  weightSE and weightCE are strings
        mod_data["ssi_wtse"] = document.getElementById("id_weightSE").value;
        mod_data["ssi_wtce"] = document.getElementById("id_weightCE").value;

// the checked attribute simply tells you whether the checkbox is checked or not by default when the page is rendered.
// To check the current state of the checkbox you must instead use the checked property.
        mod_data["ssi_mand"] = 0;
        let chk_mand  = document.getElementById("id_mod_mand_chk");
        if(!!chk_mand && chk_mand.checked){mod_data["ssi_mand"] = 1; }

        mod_data["ssi_comb"] = 0;
        let chk_comb = document.getElementById("id_mod_comb_chk");
        if(!!chk_comb && chk_comb.checked){mod_data["ssi_comb"] = 1; }

        mod_data["ssi_chal"] = 0;
        let chk_chal  = document.getElementById("id_mod_chal_chk");
        if(!!chk_chal && chk_chal.checked){mod_data["ssi_chal"] = 1; }

        mod_data["ssi_prac"] = 0;
        let chk_prac  = document.getElementById("id_mod_prac_chk");
        if(!!chk_prac && chk_prac.checked){ mod_data["ssi_prac"] = 1; }

console.log("mod_data: ", mod_data);

        upload_ssi();

        closeModal();
    }  //  function handle_mod_btn_ok()

//========= handle_mod_btn_del  =================== PR2019-02-02
    function handle_mod_btn_del() {
//console.log("======== handle_mod_btn_del  ===========")

// ---  set attribute mode of id_mod_data to "d"
         mod_data["mode"] = "d";

// ---  show message text
        body_msg = "<p>" + databox.data("msg_del01") + "</p>";  // >This subject wil be removed from the scheme.

        $("#id_div_mod_flex").hide();
        $("#id_mod_ftr_msg").hide();
        $("#id_mod_body_msg").show()
            .html(body_msg);
        $("#id_mod_btn_ok").show()
                          .html(databox.data("txt_btn_remove"))
                          .prop("disabled", false )
                          .addClass("btn-danger");

        $("#id_mod_btn_cancel").show();
        $("#id_mod_btn_del").hide();
       // closeModal()
    }  // function handle_mod_btn_del

//========= CreateTable  ====================================
    function CreateTable(tblContainer, tblName, thead_caption, item_list, sel_dep_id, tblWidth, tblHeight, tblColor) {
        // PR2019-01-12
//console.log("==== CreateTable  =========", tblContainer, tblName);
//console.log("item_list", item_list);

        // tblContainer = "sel", tblName = "dep",  "lvl",  "sct",
        // tblContainer = "ssi", tblName = "subj",  "ssis", (Subject scheme items)

        //div_tables 'id_select_tables' is container for tables
        let div_tables = $("#id_" + tblContainer + "_tables");
        // delete existing header and table
//console.log("div_tables", div_tables);

        $("<div>").appendTo(div_tables)
                .attr({id: "id_" + tblContainer + "_" + tblName + "_div"})
                .addClass("search_table_div");
        let sel_div = $("#id_" + tblContainer + "_" + tblName + "_div");
// console.log("sel_div", sel_div);


        $("<table>").appendTo(sel_div)
                .attr({id: "id_" + tblContainer + "_" + tblName + "_table"})
                .addClass("search_table");
        let sel_table = $("#id_" + tblContainer + "_" + tblName + "_table");
        sel_table.width(tblWidth);

        //sel_table.css.width = tblWidth;
        //sel_table.css.height = tblHeight;
// console.log("sel_table", sel_table);

        // thead_caption = "Department";
        $("<thead>").appendTo(sel_table)
                .attr({id: "id_" + tblContainer + "_" + tblName + "_thead"})
                .addClass("color_tblhead_"+ tblColor);
        let sel_thead = $("#id_" + tblContainer + "_" + tblName + "_thead");

        $("<td>").appendTo(sel_thead)
            .html(thead_caption);

        switch (tblContainer){
        case "ssi":
            switch (tblName){
            case "subj":
            case "ssis":

                $("<input type=\"text\" class=\"fieldname\" />").appendTo( sel_thead)
                    .attr({id: "id_" + tblContainer + "_" + tblName + "_filter"})
                    .addClass("pt-0 pb-0")
                    .attr({placeholder: "filter..."});

                $("#id_" + tblContainer + "_" + tblName + "_filter").keyup(function() {
                  delay(function(){HandleSearchFilterEvent(tblContainer,tblName, item_list);}, 250 );
                });

            }
        }

        $("<tbody>").appendTo(sel_table)
                .attr({id: "id_" + tblContainer + "_" + tblName + "_tbody"})
                //.addClass("search_table_tbody")
                .height(tblHeight)
                .on("click", HandleTableRowClicked);

        let sel_tbody = $("#id_" + tblContainer + "_" + tblName + "_tbody");
        sel_tbody.addClass("color_tblbody_"+ tblColor);

        //let sel_tbody = $("#id_" + tblContainer + "_" + tblName + "_tbody");
        //sel_tbody.height(tblHeight);

         CreateTableRows(tblContainer, tblName, item_list, sel_dep_id);

    }; //function CreateTable()

//========= CreateTableRows  ==================================== PR2019-01-13
    function CreateTableRows(tblContainer, tblName, item_list, sel_dep_id, JustAddedIndex, filter_str) {
console.log("++++++++ CreateTableRows", tblContainer, tblName, "+++++++++");

        const cls_tr = "search_table_tr";
        const cls_td = "search_table_td";
        const cli_hv = "c_colLinked_hover";

        // tblContainer = "sel", tblName = "dep",  "lvl",  "sct",
        // tblContainer = "ssi", tblName = "subj",  "ssis", (Subject scheme items)

        let tblBody = $("#id_" + tblContainer + "_" + tblName + "_tbody");

    // remove all tablerows
        tblBody.html("");

console.log("item_list ", item_list);
        if (!!item_list){

// ---  loop through array item_list
            for (let i = 0, len = item_list.length; i <len; i++) {
                // row = {id: 11, name: "Voorbereidend Secundair Beroepsonderwijs", abbrev: "Vsbo",
                //          level_req: true, level_caption: "Leerweg", sector_caption: "Sector", sector_req: true}
                let row = item_list[i];

// ---  if lvl or sct: show only rows if sel_dep_id is in depbase_list
                let skip_row = false;
                switch (tblContainer){
                case "sel":
                    switch (tblName){
                    case "lvl":
                        // fall through
                    case "sct":
                        if (!!row["depbase_list"]){
                            skip_row =  !found_in_list_str(sel_dep_id, row["depbase_list"]);
                        }
                        break;
                    };
                case "ssi":
                    switch (tblName){
                    case "subj":
                    case "ssis":
// ---  when filter: filter by filter_str (only for subjects list
                        if (!!filter_str && !!row.subj_name) {
                            // make search case insensitive
                            let add_row = row.subj_name.toLowerCase().indexOf(filter_str.toLowerCase()) >= 0;
                            skip_row = !add_row;
                        }
                    }
                };
// ---  add tablerow
                if (!skip_row){
                // {id: "104", scm_id: "154", subj_id: "327", sjtp_id: "13", grtp_id: "1", …}
                    const idSelectRow = "id_" + tblContainer + "_" + tblName + "_tr_" + i.toString();
                    const XidSelectRow = "#" + idSelectRow;

                    //$("<tr>").appendTo(tblBody)  // .appendTo( "#id_lnk_tbody_lvl" )
                    //    .attr({"id": idSelectRow, "sel_id": row.id})
                    //    .addClass(cls_tr)
                    //    .mouseenter(function(){$(XidSelectRow).addClass(cls_hover);})
                    //    .mouseleave(function(){$(XidSelectRow).removeClass(cls_hover);});

// ---  set attributes of  <tr>
                    let attrib = {};
                    attrib ["id"] = idSelectRow;
                    if (!!row.id){attrib ["sel_id"] = row.id;}
                    if (!!row.subj_id){attrib ["subj_id"] = row.subj_id;}
                    if (!!row.ssi_id){attrib ["ssi_id"] = row.ssi_id;}
                    if (!!row.sequ){attrib ["sequ"] = row.sequ;}

                    if(tblContainer === "ssi"){
                        attrib ["data-toggle"] = "modal";
                        attrib ["data-target"] = "#basicModal";
                    }
// ---  add <tr>
                    $("<tr>").appendTo(tblBody)  // .appendTo( "#id_lnk_tbody_lvl" )
                        .attr(attrib)
                        .addClass(cls_tr)
                        .mouseenter(function(){$(XidSelectRow).addClass(cls_hover);})
                        .mouseleave(function(){$(XidSelectRow).removeClass(cls_hover);});

                //if new appended row: highlight row for 2 seconds (JustAddedIndex only used in ssis table)
                    if (!!JustAddedIndex && JustAddedIndex === i) {
                       $(XidSelectRow).addClass(cli_hv);
                       setTimeout(function (){$(XidSelectRow).removeClass(cli_hv);}, 3000);
                    }

    // ---  add <td>
                    switch (tblContainer){
                    case "sel":
                        switch (tblName){
                        case "lvl":
                            // fall through
                        case "dep":
                            $("<td>").appendTo(XidSelectRow)
                                    .html(row.abbrev)
                                    .addClass(cls_td);
                            break
                        case "sct":
                            $("<td>").appendTo(XidSelectRow)
                                    .html(row.name)
                                    .addClass(cls_td);
                        };
                        break;
                    case "ssi":
                        switch (tblName){
                        case "subj":
                            $("<td>").appendTo(XidSelectRow)
                                        .html(row.subj_name)
                                        .addClass(cls_td);
                            break;
                        case "ssis":
                            $("<td>").appendTo(XidSelectRow)
                                        .html(row.subj_name);
                                        //.addClass(cls_td);
                            $("<td>").appendTo(XidSelectRow)
                                    .html(row.sjtp_name);
                                    //.addClass(cls_td);
                        };
                        break;
                    };
                };
            }
        }
     }; //function CreateTableRows()

//========= function CreateTableSubjectsSsis  ============================= PR2019-01-15
    function CreateTableSubjectsSsis () {
// console.log("=== function CreateTableSubjectsSsis  ===========")

    // scheme = {id: "165", depid: "12", lvlid: "", sctid: "33", name: "Havo - e&m", fields: ";chal;prac;"}
        let scheme_name = "";
        if (!!scheme.name){scheme_name = scheme.name;};
        let ssi_header =  $("#id_ssi_header");

        ssi_header.empty(); // remove all child nodes

        $("<p>").appendTo(ssi_header)
                .html("<b>" + scheme_name + "</b>");

        let tblWidth = 360, tblHeight = 360;
        CreateTable("ssi", "ssis", "Scheme subjects", schemeitems, sel_dep_id, tblWidth, tblHeight, "blue");

        tblWidth = 240;
        CreateTable("ssi", "subj", "Available subjects", subjects, sel_dep_id, tblWidth, tblHeight, "blue");


    }

//========= CreateCheckbox  ============= PR2019-01-22
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

//========= function openModal  ============================= PR2019-01-22
    function openModal(item_list, sel_subj_id_str, sel_ssi_id_str, tblContainer, tableName ) {
        console.log("=========  openModal ========= ");
        console.log("tblContainer:", tblContainer, "tableName:", tableName);
        console.log("sel_subj_id_str:", sel_subj_id_str, typeof sel_subj_id_str);
        console.log("sel_ssi_id_str:", sel_ssi_id_str, typeof sel_ssi_id_str);
        console.log("item_list:", item_list);

// convert to number
        let sel_subj_id = 0, sel_ssi_id = 0;
        if (!isNaN(sel_subj_id_str)) {sel_subj_id = parseInt(sel_subj_id_str)};
        if (!isNaN(sel_ssi_id_str)) {sel_ssi_id = parseInt(sel_ssi_id_str)};

// ---  loop through item_list (either subjects or schemeitems) to get selected item and put attr.values in variables

        // subjects[i] =  {subj_id: "319", subj_name: "Nederlandse taal en literatuur", subj_abbr: "ne", subj_sequ: 11}

        // schemeitems[i] = {mode: "-", ssi_id: "378, scm_id: "168", subj_id: "321", sjtp_id: "12", grtp_id: "2"
        //                   wtse: "1", wtce: "1", mand: "0", comb: "0", chal: "0", prac: "0",
        //                   subj_name: "Wiskunde A", subj_sequ: "121", sjtp_name: "Profiel deel"}


// ---  reset mod_data variable
        mod_data = []; // mode = "c" = create "u" = update (can be changed into "d" delete)
        if (tableName === "subj") {
            mod_data["mode"] = "c";
        } else if (tableName === "ssis") {
            mod_data["mode"] = "u";
        }
        if (!!scheme["scheme_id"]){mod_data["scheme_id"] = scheme["scheme_id"];};  // scheme.id

// ---  loop through item_list to get row of selected item (is either subject or ss1)
        let row = {};
        if (!!item_list) {
            for (let i = 0, len = item_list.length; i < len; i++) {
                let found = false;
                switch (tableName){
                case "subj":
                    if (!isNaN(sel_subj_id)) {
                        let subj_id_int = parseInt(sel_subj_id);
                        found = (!!item_list[i].subj_id && item_list[i].subj_id === subj_id_int);
                    };
                    break;
                case "ssis":
                    if (!isNaN(sel_ssi_id)) {
                        let ssi_id_int = parseInt(sel_ssi_id);
                        found = (!!item_list[i].ssi_id && item_list[i].ssi_id === ssi_id_int);
                    }
                }
                if(found){
                    row = item_list[i];
                    break;
        }}}

        if (!!row) {
console.log("row:", row);
    // ---  set header
            let subj_name = "";
            if (!!row.subj_name){subj_name = row.subj_name;} // subject.name
            if (!!row.sjtp_name){subj_name = subj_name + " (" + row.sjtp_name.toLowerCase() + ")";};
            $("#id_mod_header").html(subj_name);

    // ---  store values of 'row' in variable mod_data
            if (!!row.ssi_id){mod_data["ssi_id"] = row.ssi_id;};  // schemeitem.id
            if (!!row.scm_id){mod_data ["scm_id"] = row.scm_id;};  // schemeitem.scheme.id

            if (!!row.subj_id){mod_data ["subj_id"] = row.subj_id;} else {mod_data ["subj_name"] = '';};
            if (!!row.sjtp_id){mod_data ["sjtp_id"] = row.sjtp_id;};
            if (!!row.grtp_id){mod_data ["grtp_id"] = row.grtp_id;};

            if (!!row.subj_name){mod_data ["subj_name"] = row.subj_name;} else {mod_data ["subj_name"] = '';};
            if (!!row.subj_sequ){mod_data ["subj_sequ"] = row.subj_sequ;} else {mod_data ["subj_sequ"] = '';};
            if (!!row.sjtp_name){mod_data ["sjtp_name"] = row.sjtp_name;} else {mod_data ["sjtp_name"] = '';};

            if (!!row.ssi_wtse){mod_data ["ssi_wtse"] = row.ssi_wtse;} else {mod_data ["ssi_wtse"] = 0;};
            if (!!row.ssi_wtce){mod_data ["ssi_wtce"] = row.ssi_wtce;} else {mod_data ["ssi_wtce"] = 0;};
            if (!!row.ssi_mand){mod_data ["ssi_mand"] = row.ssi_mand;} else {mod_data ["ssi_mand"] = 0;};
            if (!!row.ssi_comb){mod_data ["ssi_comb"] = row.ssi_comb;} else {mod_data ["ssi_comb"] = 0;};
            if (!!row.chal){mod_data ["chal"] = row.chal;} else {mod_data ["chal"] = '0';};
            if (!!row.sjtp_hasprac){mod_data ["sjtp_hasprac"] = row.sjtp_hasprac;} else {mod_data ["sjtp_hasprac"] = 0;};

console.log("mod_data:", mod_data, typeof mod_data);

    // ---  get  lst_sjtp_occupied, lst_sjtp_occupied and is_subj_mand
            let returnvalue = GetListSjtpOccupied(schemeitems, sel_subj_id, sel_ssi_id);
            let lst_sjtp_occupied = returnvalue["lst_sjtp_occupied"];
            let is_subj_mand = returnvalue["is_subj_mand"];
            let current_sjtp_id = returnvalue["current_sjtp_id"];

    // ---  create body_msg if subject is mandatory - not when schemitem is selected
            let body_msg = "", footer_msg = "";
            let btn_ok_caption = databox.data("txt_btn_ok");
            if (mod_data["mode"] === "u"){
                btn_ok_caption = databox.data("txt_btn_save");
             } else if (mod_data["mode"] === "c") {
                btn_ok_caption = databox.data("txt_btn_add");
                if (is_subj_mand){
                    body_msg = "<p>" + databox.data("msg_mand01") + "</p><p>" + databox.data("msg_mand02") + "</p>";
                }
            }

    // show message text when subject is already mandatory
            if (!!body_msg ){
                $("#id_div_mod_flex").hide();
                $("#id_mod_ftr_msg").hide();
                $("#id_mod_body_msg").show()
                    .html(body_msg);
                $("#id_mod_btn_ok").hide();
                $("#id_mod_btn_cancel").show();
                $("#id_mod_btn_del").hide();

            } else {
                $("#id_mod_btn_cancel").hide();
                //footer_msg = "<p>Select a subject type and grade type, set the characteristics and click 'Add'.</p>";
                footer_msg = "<p>" + databox.data("msg_ftr01") + " '" + databox.data("txt_btn_add") + "'.</p>";
                // use this to escape single quote:
                //data-msg_ftr02= "{% blocktrans %}Select a subject type and ... click 'Add'.{% endblocktrans %}"


                $("#id_mod_body_msg").hide();
                $("#id_div_mod_flex").show();
                $("#id_mod_ftr_msg").show()
                                    .html(footer_msg);
                $("#id_mod_btn_ok").show()
                                   .html(btn_ok_caption)
                                   .removeClass("btn-danger")
                                   .addClass("btn-primary");

                $("#id_mod_btn_cancel").hide();
                if (mod_data["mode"] === "u"){
                    $("#id_mod_btn_del").show();
                } else {
                    $("#id_mod_btn_del").hide();
                }

        // ---  set selectbox subjecttype
                let sel_subjecttype_id = 0;
                if (!!mod_data ["sjtp_id"]){sel_subjecttype_id = mod_data ["sjtp_id"];};  // schemeitem.subjecttype.id
                FillListSubjectypes(lst_sjtp_occupied, sel_subjecttype_id, current_sjtp_id);

        // ---  set selectbox gradetypes
                FillListGradetypes(gradetypes, mod_data ["grtp_id"]);

        // ---  set input box id_weightSE and id_weightCE
                document.getElementById("id_weightSE").value = mod_data ["ssi_wtse"];
                document.getElementById("id_weightCE").value = mod_data ["ssi_wtce"];

        // ---  set check boxes
                let ssi_mand = (!!mod_data ["ssi_mand"] && mod_data ["ssi_mand"] === 1);
                let ssi_comb = (!!mod_data ["ssi_comb"] && mod_data ["ssi_comb"] === 1);
                let ssi_chal = (!!mod_data ["ssi_chal"] && mod_data ["ssi_chal"] === 1);
                let ssi_prac = (!!mod_data ["ssi_prac"] && mod_data ["ssi_prac"] === 1);

                let sel_checkbox = $("#id_sel_checkbox");
                sel_checkbox.empty();

        //console.log("lst_sjtp_occupied:", lst_sjtp_occupied, typeof lst_sjtp_occupied);
                // always add "mand" checkbox
                // disable "mand" checkbox when this subjecty already s=exists in scheme, exept for this sssi
                let chkbox_disabled = false;
                if (!!lst_sjtp_occupied){
                    let len = lst_sjtp_occupied.length;
                    if (mod_data["mode"] === "c"){
                        // disable when this subject already exists in scheme
                        chkbox_disabled = (len > 0);
                    } else if (mod_data["mode"] === "u") {
                        // disable when there are also other  subjects  in scheme
                        chkbox_disabled = (len > 1);
                    }
                };

                // always add "mandatory" checkbox
                let tooltip = "";
                if (chkbox_disabled){ tooltip = databox.data("chk_mand_tlt");}
                CreateCheckbox(sel_checkbox, "mand", databox.data("chk_mand_cap"), ssi_mand, chkbox_disabled, tooltip);

                // always add "combination" checkbox
                CreateCheckbox(sel_checkbox, "comb", databox.data("chk_comb_cap"), ssi_comb, false);

                // check if "chal" in scheme.fields, if so: add checkbox
                if (!!scheme.fields){
                    const field_chal = "chal";
                    if (found_in_list_str(field_chal, scheme.fields)){
                        CreateCheckbox(sel_checkbox, field_chal, databox.data("chk_chal_cap"), ssi_chal, false);
                }}

                // check if "prac" in scheme.fields, if so: add checkbox
                if (!!scheme.fields){
                    const field_prac = "prac";
                    if (found_in_list_str(field_prac, scheme.fields)){
                        CreateCheckbox(sel_checkbox, field_prac, databox.data("chk_prac_cap"), ssi_prac, false);
                }}
            }  // if (!!body_msg )

// ---  enable button OK when clicked on selecet subjecttype
        // moved to
        //$("#id_select_sjtp, #id_select_grtp").on("click", function(){
        //    SetButtonOkDisabled();
        //});

// ---  set button OK disabled
        SetButtonOkDisabled();


        }  // if (!!row)

// ---  show modal
        $("#id_modal_cont").modal({backdrop: true});

    }  // function openModal(sel_subj_or_ssid, tblContainer, tableName )

//========= function closeModal  =============
    function closeModal() {
        $('#id_modal_cont').modal('hide');
    }

//========= function upload_ssi  ====================================
    function upload_ssi() {
            // schemeitems[i] = {id: "9", scm_id: "155", subj_id: "319", name: "Nederlandse taal en literatuur",
            // sjtp_id: "10", type: "Gemeenschappelijk deel",
            // grtp_id: "1",  wtse: "1", wtce: "1", mand: "1", comb: "0", chal: "0", prac: "0", sequ: "30"}

console.log("======== function upload_ssi  ===========");

// mod_data = [mode: "c", scheme_id: "168", subj_id: "309", subj_sequ: 150, sjtp_id: "17", grtp_id: "1",
//              wtse: "1", wtce: "1", mand: "0", comb: "0", chal: "0", prac: "0"]

// mod_data = [mode: "u", scheme_id: "168", ssi_id: "398", scm_id: "168", subj_id: "312", sjtp_id: "10",  grtp_id: "1",
//              mand: "0", comb: "0", chal: "0", prac: "0", wtce: "1", wtse: "1"
//              subj_name: "Algemene Sociale Wetenschappen", subj_sequ: "600", subj_type: "Profiel deel"]


        let ssi = {"mode": mod_data["mode"]};
        if(!!mod_data["ssi_id"]){ ssi["ssi_id"] = mod_data["ssi_id"];};
        if(!!mod_data["scheme_id"]){ ssi["scheme_id"] = mod_data["scheme_id"];};
        if(!!mod_data["scm_id"]){ ssi["scm_id"] = mod_data["scm_id"];};

        if (mod_data["mode"] === "c" || mod_data["mode"] ==="u"){
            if(!!mod_data["subj_id"]){ ssi["subj_id"] = mod_data["subj_id"];};
            if(!!mod_data["sjtp_id"]){ ssi["sjtp_id"] = mod_data["sjtp_id"];};
            if(!!mod_data["grtp_id"]){ ssi["grtp_id"] = mod_data["grtp_id"];};
            if(!!mod_data["ssi_wtse"]){ ssi["ssi_wtse"] = mod_data["ssi_wtse"];};
            if(!!mod_data["ssi_wtce"]){ ssi["ssi_wtce"] = mod_data["ssi_wtce"];};
            if(!!mod_data["ssi_mand"]){ ssi["ssi_mand"] = mod_data["ssi_mand"];};
            if(!!mod_data["ssi_comb"]){ ssi["ssi_comb"] = mod_data["ssi_comb"];};
            if(!!mod_data["ssi_chal"]){ ssi["ssi_chal"] = mod_data["ssi_chal"];};
            if(!!mod_data["ssi_prac"]){ ssi["ssi_prac"] = mod_data["ssi_prac"];};
            if(!!mod_data["subj_name"]){ ssi["name"] = mod_data["subj_name"];};
            if(!!mod_data["subj_sequ"]){ ssi["sequ"] = mod_data["subj_sequ"];};
        }

console.log("ssi", ssi);

// parameters = {id: "new", scm_id: "155", subj_id: "283", sjtp_id: "16", grtp_id: "1", wtse: "1", wtce: "1", mand: "0", comb: "0", chal: "0", prac: "0"}

// scheneitem = {id: "9", scm_id: "155", subj_id: "319", name: "Nederlandse taal en literatuur", sjtp_id: "10",
// type: "Gemeenschappelijk deel", grtp_id: "1", wtse: "1", wtce: "1", mand: "1", comb: "0, "chal: "0, "prac: "0"
//console.log("schemeitems", typeof schemeitems);
//console.log(schemeitems);

// ---  lookup sequence in schemeitems , to insert new row in right order
            let selected_index = 0, found = false;
            for (let x = 0, len = schemeitems.length; x < len; x++) {
                let row = schemeitems[x];
            // count this subject in ssi
                if (!!row.sequ  && !!mod_data["subj_sequ"] && row.sequ > mod_data["subj_sequ"]) {
                    selected_index = x;
                    found = true;
                    break;
                }
            }

            if(found){
// ---  add row at selected index
                schemeitems.splice(selected_index, 0, ssi);
            } else {
// ---  add row at end of list
                schemeitems.push(ssi);
            }

            //CreateTableRows("ssi", "ssis", schemeitems, 0, selected_index)
CreateTableRows("ssi", "ssis", [], 0, selected_index);
            var parameters = {
                "ssi": JSON.stringify (ssi)
            };
console.log(">>>>> parameters", typeof parameters);
console.log(parameters);

            const ajax_ssi_upload_url = $("#id_data").data("ajax_ssi_upload_url");
            response = "";
            msg_txt = "";
            schemeitems = [];
console.log('--------ajax');
            $.ajax({
                type: "POST",
                url: ajax_ssi_upload_url,
                data: parameters,
                dataType:'json',
                success: function (response) {
console.log("========== response ==>", typeof response,  response);

                    schemeitems = response["schemeitems"];
                    err_code = response["err_code"];

console.log("========== schemeitems ==<",typeof schemeitems, ">", schemeitems);
console.log("========== err_code ==<",typeof err_code, ">", err_code);

                CreateTableRows("ssi", "ssis", schemeitems, 0, selected_index);
                    if (!!err_code){
                        err_msg =  databox.data("err_msg01") + " " + databox.data(err_code);
                        alert(err_msg);
                    }
                },
                error: function (xhr, msg) {
                    console.log(msg + '\n' + xhr.responseText);
                }
            });
console.log("+++++++++ schemeitems ==>", schemeitems);
    }  // function upload_ssi

//========= SetButtonOkDisabled  ============= PR2019-01-28
    function SetButtonOkDisabled() {
        // Button OK is enabled when both Subjecttype and Gradetype are selected
        let sjtp_option_selected = false, grtp_option_selected = false;
        $('#id_select_sjtp option').each(function() {
            if (!!this.selected) {
               sjtp_option_selected = true;
               return false;
            }
        });
        $('#id_select_grtp option').each(function() {
            if (!!this.selected) {
               grtp_option_selected = true;
               return false;
            }
        });
        let mod_btn_ok_disabled = (!sjtp_option_selected || !grtp_option_selected);

        let mod_btn_ok = $("#id_mod_btn_ok");
        mod_btn_ok.prop("disabled", mod_btn_ok_disabled);

    }

//========= FillListSubjectypes  ============= PR2019-01-28
    function FillListSubjectypes(lst_sjtp_occupied, sel_subjecttype_id, current_sjtp_id) {
//console.log("------- FillListSubjectypes  ---------")
//console.log("lst_sjtp_occupied: ", lst_sjtp_occupied, typeof lst_sjtp_occupied)
//console.log("sel_subjecttype_id: ", sel_subjecttype_id, typeof sel_subjecttype_id)
//console.log("current_sjtp_id: ", current_sjtp_id, typeof current_sjtp_id)

        let el_select_sjtp = $("#id_select_sjtp");

// ---  remove all options from select_subjecttype
        el_select_sjtp.empty();

// ---  loop through select_subjecttypes
        for (let i = 0, len = subjecttypes.length; i < len; i++) {
            let row = subjecttypes[i];
            if (!!row.sjtp_id ){
                let idSelectRow = "id_option_sjtp_" + row.sjtp_id;
// ---  disable if subj_type_id is found in lst_sjtp_occupied (except for selected ssi in editmode)
                let is_disabled = false, is_selected = false;
// ---  current_sjtp_id is always enabled
                if (!!current_sjtp_id && current_sjtp_id === row.sjtp_id){
                    is_selected = true;
                } else {
                    is_disabled = found_in_array(lst_sjtp_occupied, row.sjtp_id);
                }
                $("<option>").appendTo(el_select_sjtp)
                    .attr({"id": idSelectRow, "sjtp_id": row.sjtp_id, "sjtp_sequ": row.sequ})
                    .prop("selected", is_selected)
                    .prop("disabled", is_disabled)
                    .html(row.name);
                if (!is_disabled) {
                    $("#" + idSelectRow).mouseenter(function(){$("#" + idSelectRow).addClass(cls_hover);})
                                        .mouseleave(function(){$("#" + idSelectRow).removeClass(cls_hover);});
                }
            }
         }
    }

//========= FillListGradetypes  ============= PR2019-01-28
    function FillListGradetypes(gradetypes, sel_gradetype_id) {
    // fill list gradetypes
//console.log("------- FillListGradetypes  ---------")
//console.log("sel_gradetype_id: ", sel_gradetype_id, typeof sel_gradetype_id)
//console.log("gradetypes: ")
//console.log(gradetypes)
        let el_select_gradetype = $("#id_select_grtp");

// ---  remove all options from el_select_gradetype
        el_select_gradetype.empty();

    //  loop through gradetypes
        for (let i = 0, len = gradetypes.length ; i < len; i++) {
            let row = gradetypes[i];
            if (!!row.grtp_id ){
                let idSelectRow = "id_option_grtp_" + row.grtp_id;
// ---  select current gradetype
                let is_selected = (!!sel_gradetype_id && sel_gradetype_id === row.grtp_id);

                $("<option>").appendTo(el_select_gradetype)
                    .attr({"id": idSelectRow, "grtp_id": row.grtp_id})
                    .prop("selected", is_selected)
                    .html(row.name)
                    .mouseenter(function(){$("#" + idSelectRow).addClass(cls_hover);})
                    .mouseleave(function(){$("#" + idSelectRow).removeClass(cls_hover);});
            }
        }
    }

//========= function get_arrayItem_by_keyValue  ============================= PR2019-01-15
    function get_arrayItem_by_keyValue (objArray, arrKey, keyValue) {
        // Function returns item of array that contains Value in objKey
        // dep_list[0]: {abbrev: "Vsbo", id: 11, level_req: true, name: "Voorbereidend Secundair Beroepsonderwijs", sector_req: true}
        let item;
        if (!!objArray && !!arrKey && !!keyValue){
            for (let i = 0, len = objArray.length; i < len; i++) {
                let obj = objArray[i];
                if (!!obj && !!obj[arrKey] ){
                    // convert number to string for text comparison
                    let arrKey_value;
                    if (typeof(obj[arrKey]) === "number"){
                        arrKey_value = obj[arrKey].toString();
                    } else {
                        arrKey_value = obj[arrKey];
                    }
                    if (keyValue === arrKey_value){
                        item = obj;
                        break;
        }}}}
        return item;
    }

//========= GetListSjtpOccupied  ============= PR2019-01-28
    function GetListSjtpOccupied(schemeitems, sel_subj_id, sel_ssi_id) {
        // function loops through schemeitems and filters schemeitems of selected subject
        // the subjecttypes of this subject will be disabled in the subjecttypes list. They are stored in lst_sjtp_occupied
        // except for the subjecttypes of the selected schemeitem, because selected schemeitem is updatable

//console.log("schemeitems", schemeitems)
//console.log("sel_subj_id", sel_subj_id, "sel_ssi_id", sel_ssi_id)

        let lst_sjtp_occupied = [];
        let is_subj_mand = false;
        let current_sjtp_id = 0;
        let returnvalue = {};
        if(!!sel_subj_id){
            for (let i = 0, len = schemeitems.length ; i < len; i++) {
                let row = schemeitems[i];
// ---  only if row.subject equals selected subject
                if (!!row.subj_id && !!sel_subj_id && row.subj_id === sel_subj_id){

// ---  check if subject is mandatory
                    if (!!row.ssi_mand && row.ssi_mand === 1) {
                        is_subj_mand = true;
                    };
                    if (!!row.sjtp_id){
// ---  add  subjecttype to list of occupied subjecttypes
                        lst_sjtp_occupied.push(row.sjtp_id);
// ---  check if row is selected schemeitem. subjecttype of selected_schemeitem_is always updateble
                        if (!!row.ssi_id && !!sel_ssi_id & row.ssi_id === sel_ssi_id){
                            current_sjtp_id = row.sjtp_id;
                        }
         }}}}

         returnvalue["lst_sjtp_occupied"] = lst_sjtp_occupied;
         returnvalue["is_subj_mand"] = is_subj_mand;
         returnvalue["current_sjtp_id"] = current_sjtp_id;

// console.log("lst_sjtp_occupied", lst_sjtp_occupied)
         return returnvalue;
    }

}); //$(document).ready(function()