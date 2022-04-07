
    let mod_MSESD_dict = {};
// ++++++++++++  TABLE  +++++++++++++++++++++++++++++++++++++++
    "use strict";
    const cls_hide = "display_hide";
    const cls_hover = "tr_hover";
    const cls_selected = "tsa_tr_selected";
    const cls_bc_transparent = "tsa_bc_transparent";


// ++++++++++++  MODAL SELECT EXAMYEAR OR DEPARTMENT   +++++++++++++++++++++++++++++++++++++++

//=========  t_MSED_Open  ================ PR2020-10-27 PR2020-12-25 PR2021-04-23  PR2021-05-10
    function t_MSED_Open(loc, tblName, data_map, setting_dict, permit_dict, MSED_Response, all_countries) {
        //console.log( "===== t_MSED_Open ========= ", tblName);
        //console.log( "setting_dict", setting_dict);
        //console.log( "permit_dict", permit_dict);
        // PR2021-09-24 all_countries is added for copy subjects to other examyear/ country
        if (!isEmpty(loc)) {
            let may_open_modal = false, selected_pk = null;
            if (tblName === "examyear") {
                may_open_modal = permit_dict.may_select_examyear;
                selected_pk = setting_dict.sel_examyear_pk;
            } else if (tblName === "department") {
                const allowed_depbases_count = (permit_dict.allowed_depbases) ? permit_dict.allowed_depbases.length : 0
                may_open_modal = (allowed_depbases_count > 1);
                may_open_modal = permit_dict.may_select_department;
                selected_pk = setting_dict.sel_depbase_pk;
             }
    //console.log( "may_open_modal", may_open_modal);
            //PR2020-10-28 debug: modal gives 'NaN' and 'undefined' when  loc not back from server yet
            if (may_open_modal) {

// set header text
                const el_MSED_header_text = document.getElementById("id_MSED_header_text");
                const header_text = (tblName === "examyear") ? loc.Select_examyear :// PR2021-11-16 debug was:  loc.Copy_to_examyear :
                                    (tblName === "department") ? loc.Select_department : null;
                el_MSED_header_text.innerText = header_text;

// ---  fill select table
                t_MSED_FillSelectTable(loc, tblName, data_map, permit_dict, MSED_Response, selected_pk, all_countries);

// ---  show modal
                $("#id_mod_select_examyear_or_depbase").modal({backdrop: true});
            }
        }
    }  // t_MSED_Open

    //=========  t_MSED_Save  ================ PR2021-05-10 PR2021-08-13 PR2021-09-24
    function t_MSED_Save(MSED_Response, tblRow) {
        console.log("===  t_MSED_Save =========");
    // --- put tblName, sel_pk and value in MSED_Response, MSED_Response handles uploading

        const tblName = get_attr_from_el(tblRow, "data-table");
        const selected_pk_int = get_attr_from_el_int(tblRow, "data-pk");

        // PR2021-09-24 all_countries is added for copy subjects to other examyear/ country
        const all_countries = get_attr_from_el(tblRow, "data-all_countries", false);

// ---  upload new selected_pk
        // new_setting = {page: sel_page}; sel_page will be added in MSED_Response PR2021-09-24
        const new_setting = {};
        if (tblName === "examyear") {
            //PR2021-11-16 this isn't right. TODO check: new_setting.copyto_examyear_pk = (selected_pk_int) ? selected_pk_int : null;
            new_setting.sel_examyear_pk = (selected_pk_int) ? selected_pk_int : null;
            if(all_countries){new_setting.all_countries = true};
        } else if (tblName === "department") {
            new_setting.sel_depbase_pk = (selected_pk_int) ? selected_pk_int : null;
            // PR2022-01-08 debug: set level, sector, subject and student null when changing depbase
            new_setting.sel_lvlbase_pk = null;
            new_setting.sel_sctbase_pk = null;
            // also reset setting_dict - setting_dict must be a global variable;
            setting_dict.sel_lvlbase_pk = null;
            setting_dict.sel_level_abbrev = null;
            setting_dict.sel_sctbase_pk = null;
            setting_dict.sel_sector_abbrev = null;

        };
        // always reset student and subject when changing dep or ey
        new_setting.sel_student_pk = null;
        new_setting.sel_subject_pk = null;

        setting_dict.sel_student_pk = null;
        setting_dict.sel_student_name = null;
        setting_dict.sel_student_name_init = null;

        setting_dict.sel_subject_pk = null;
        setting_dict.sel_subject_code = null;
        setting_dict.sel_subject_name = null;

        //console.log("new_setting", new_setting);
        MSED_Response(new_setting)

// hide modal
        $("#id_mod_select_examyear_or_depbase").modal("hide");

    }  // t_MMSED_Save

//=========  t_MSED_FillSelectTable  ================ PR2020-08-21 PR2020-12-18 PR2021-05-10 PR2021-09-24
    function t_MSED_FillSelectTable(loc, tblName, data_map, permit_dict, MSED_Response, selected_pk, all_countries) {
        //console.log( "===== t_MSED_FillSelectTable ========= ");

        const tblBody_select = document.getElementById("id_MSED_tblBody_select");
        tblBody_select.innerText = null;

// --- loop through data_map
        if(data_map){
            for (const [map_id, map_dict] of data_map.entries()) {
                const pk_int = (tblName === "examyear") ? map_dict.examyear_id :
                               (tblName === "department") ? map_dict.base_id : null;

    // permit_dict.requsr_country_pk
                let code_value = "---", country = "---";
                const locked = (map_dict.locked) ? map_dict.locked : false;
                const activated = (map_dict.activated) ? map_dict.activated : false;

                if(tblName === "examyear") {
                    code_value = (map_dict.examyear_code) ? map_dict.examyear_code : "---";
                    if (all_countries && map_dict.country) {country = map_dict.country};
                } else if(tblName === "department") {
                    code_value = (map_dict.base_code) ? map_dict.base_code : "---"
                }

                let skip_row = false;
                if(tblName === "examyear") {
                    if(all_countries){
                        skip_row = (setting_dict.sel_examyear_pk === map_dict.examyear_id || map_dict.locked);
                    } else {
                        skip_row = (permit_dict.requsr_country_pk !== map_dict.country_id);
                    };
                } else if(tblName === "department"){
                    if (permit_dict.allowed_depbases){
                        skip_row = !permit_dict.allowed_depbases.includes(pk_int);
                    } else {
                        skip_row = true;
                    }
                }
                if(!skip_row){
                    t_MSED_CreateSelectRow(loc, tblName, tblBody_select, pk_int, code_value, country, all_countries, activated, locked, MSED_Response, selected_pk);
                }
            };
        }  // if(!!data_map)
        const row_count = (tblBody_select.rows) ? tblBody_select.rows.length : 0;
        if(!row_count){
            const caption_none = (tblName === "examyear") ? loc.No_examyears :
                                 (tblName === "department") ? loc.No_departments : null;
            t_MSED_CreateSelectRow(loc, tblName, tblBody_select, null, caption_none, null, false, false, MSED_Response, selected_pk);
        }
    }  // t_MSED_FillSelectTable

//=========  t_MSED_CreateSelectRow  ================ PR2020-10-27 PR2020-12-18 PR2021-05-10 PR2021-09-24
    function t_MSED_CreateSelectRow(loc, tblName, tblBody_select, pk_int, code_value, country, all_countries, activated, locked, MSED_Response, selected_pk) {
        //console.log( "===== t_MSED_CreateSelectRow ========= ");

        const is_selected_pk = (selected_pk != null && pk_int === selected_pk)

// ---  insert tblRow  //index -1 results in that the new row will be inserted at the last position.
        let tblRow = tblBody_select.insertRow(-1);
        tblRow.setAttribute("data-table", tblName)
        tblRow.setAttribute("data-pk", pk_int);
        if(all_countries){
            tblRow.setAttribute("data-all_countries", true);
        };

// ---  add EventListener to tblRow
        if(pk_int){
            tblRow.addEventListener("click", function() { t_MSED_Save(MSED_Response, tblRow) }, false )
// ---  add hover to tblRow
            add_hover(tblRow);
// ---  highlight clicked row
            if (is_selected_pk){ tblRow.classList.add(cls_selected)}
        }
        const col_width = "tw_120"
// ---  add country td to tblRow, only when may_select_all_countries
        let td = null, el_div = null;
        if(all_countries){
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                el_div.innerText = country;
                el_div.classList.add(col_width, "px-2")
            td.appendChild(el_div);
        }

// --- add a element with code_value to td
        td = tblRow.insertCell(-1);
        el_div = document.createElement("div");
            el_div.innerText = code_value;
            el_div.classList.add(col_width, "px-2")
        td.appendChild(el_div);

// --- add td to tblRow with icon locked, published or activated.
        if  (tblName === "examyear") {
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                const class_locked = (locked) ? "appr_2_6" : (activated) ? "appr_0_1" : "appr_0_0";
                el_div.classList.add("tw_032", class_locked)
                el_div.title = (locked) ? loc.This_school + loc.is_locked : (activated) ? loc.This_school + loc.is_activated : "";
            td.appendChild(el_div);
        }
    }  // t_MSED_CreateSelectRow

// ++++++++++++  END OF MODAL SELECT SCHOOL OR DEPARTMENT   +++++++++++++++++++++++++++++++++++++++

// +++++++++++++++++ MODAL SELECT SCHOOL SUBJECT STUDENT ++++++++++++++++++++++++++++++++
//========= t_MSSSS_Open ====================================  PR2020-12-17 PR2021-01-23 PR2021-04-23 PR2021-07-23
    function t_MSSSS_Open (loc, tblName, data_rows, add_all, setting_dict, permit_dict, MSSSS_Response) {
        //console.log(" ===  t_MSSSS_Open  =====", tblName) ;
        //console.log( "setting_dict", setting_dict);
        //console.log( "permit_dict", permit_dict);
        //console.log( "tblName", tblName );
        //console.log( "data_rows", data_rows, typeof data_rows );
        // tblNames are: "school", "subject", "student"

        // PR2021-04-27 debug: opening modal before loc and setting_dict are loaded gives 'NaN' on modal.
        // allow opening only when loc has value
        if(!isEmpty(permit_dict)){
            const may_select = (tblName === "school") ? !!permit_dict.may_select_school : true;
        //console.log( "may_select", may_select);
            if (may_select){
                const selected_pk = (tblName === "school") ? setting_dict.sel_school_pk :
                                   (tblName === "subject") ? setting_dict.sel_subject_pk :
                                   (tblName === "student") ? setting_dict.sel_student_pk : null;
                const el_MSSSS_input = document.getElementById("id_MSSSS_input")
                el_MSSSS_input.setAttribute("data-table", tblName);
        //console.log( "el_MSSSS_input", el_MSSSS_input);
        // --- fill select table
                t_MSSSS_Fill_SelectTable(loc, tblName, data_rows, setting_dict, el_MSSSS_input, MSSSS_Response, selected_pk, add_all)
                el_MSSSS_input.value = null;
        // ---  set focus to input element
                set_focus_on_el_with_timeout(el_MSSSS_input, 50);
        // ---  show modal
                 $("#id_mod_select_school_subject_student").modal({backdrop: true});
             };
         };
    }; // t_MSSSS_Open

//=========  t_MSSSS_Save  ================ PR2020-01-29 PR2021-01-23 PR2022-02-26
    function t_MSSSS_Save(el_input, MSSSS_Response) {
        //console.log("===  t_MSSSS_Save =========");
        //console.log("el_input", el_input);
    // --- put tblName, sel_pk and value in MSSSS_Response, MSSSS_Response handles uploading

        const tblName = get_attr_from_el(el_input, "data-table");

        // Note: when tblName = school: pk_int = schoolbase_pk
        // Note: when tblName = subject: pk_int = subject_pk
        const selected_pk_int = get_attr_from_el_int(el_input, "data-pk");
        const selected_code = get_attr_from_el(el_input, "data-code");
        const selected_name = get_attr_from_el(el_input, "data-name");

// +++ get existing map_dict from data_rows
        const data_rows = (tblName === "school") ? school_rows :
                        (tblName === "subject") ? subject_rows :
                        (tblName === "cluster") ? cluster_rows :
                        (tblName === "student") ? student_rows : null;
        const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", selected_pk_int);
        const selected_dict = (!isEmpty(found_dict)) ? found_dict : null;

        //console.log("selected_pk_int", selected_pk_int);
        //console.log("selected_code", selected_code);
        //console.log("selected_name", selected_name);
        //console.log( "selected_dict", selected_dict);

        //console.log( "===== t_MSSSS_display_in_sbr  ========= ");
        t_MSSSS_display_in_sbr(tblName, selected_pk_int);
        // reset other select elements
        if (tblName === "subject") {
            t_MSSSS_display_in_sbr("cluster", null);
            t_MSSSS_display_in_sbr("student", null);
        } else if (tblName === "cluster") {
            t_MSSSS_display_in_sbr("subject", null);
            t_MSSSS_display_in_sbr("student", null);
        } else if (tblName === "student") {
            t_MSSSS_display_in_sbr("subject", null);
            t_MSSSS_display_in_sbr("cluster", null);
        };

        MSSSS_Response(tblName, selected_dict, selected_pk_int);
// hide modal
        $("#id_mod_select_school_subject_student").modal("hide");
    }  // t_MSSSS_Save

//========= t_MSSSS_Fill_SelectTable  ============= PR2021-01-23  PR2021-07-23
    function t_MSSSS_Fill_SelectTable(loc, tblName, data_rows, setting_dict, el_input, MSSSS_Response, selected_pk, add_all) {
        //console.log("===== t_MSSSS_Fill_SelectTable ===== ", tblName);
        //console.log("data_rows", data_rows, typeof data_rows);

// set header text
        const label_text = loc.Select + (
                                    (tblName === "student") ?  loc.a_candidate :
                                    (tblName === "subject") ?  loc.a_subject :
                                    (tblName === "school") ?  loc.a_school : ""
                                     );
        const item = (tblName === "student") ? loc.a_candidate :
                     (tblName === "subject") ? loc.a_subject :
                     (tblName === "school") ? loc.a_school : "";
        const placeholder = loc.Type_few_letters_and_select + item + loc.in_the_list;

        document.getElementById("id_MSSSS_header").innerText = label_text;
        document.getElementById("id_MSSSS_input_label").innerText = label_text;
        document.getElementById("id_MSSSS_msg_input").innerText = placeholder

        const tblBody_select = document.getElementById("id_MSSSS_tblBody_select");
        tblBody_select.innerText = null;

// ---  add All to list when multiple subject / students exist
        if(data_rows && data_rows.length && add_all){
            const add_all_dict = t_MSSSS_AddAll_dict(tblName);
            t_MSSSS_Create_SelectRow(loc, tblName, tblBody_select, add_all_dict, selected_pk, el_input, MSSSS_Response)
        }

// ---  loop through dictlist
        //PR 2021-07-23 was: for (const [map_id, map_dict] of data_map.entries()) {
        for (let i = 0, map_dict; map_dict = data_rows[i]; i++) {
            t_MSSSS_Create_SelectRow(loc, tblName, tblBody_select, map_dict, selected_pk, el_input, MSSSS_Response);
        }
    } // t_MSSSS_Fill_SelectTable

    function t_MSSSS_AddAll_txt(tblName){
        const caption = (tblName === "student") ? loc.Candidates.toLowerCase() :
                        (tblName === "subject") ? loc.Subjects.toLowerCase() :
                        (tblName === "cluster") ? loc.Clusters.toLowerCase() :
                        (tblName === "school") ? loc.Schools.toLowerCase() : "";
        return "<" + loc.All_ + caption + ">";
    }

    function t_MSSSS_AddAll_dict(tblName){
        const add_all_text = t_MSSSS_AddAll_txt(tblName);
        return (tblName === "student") ? {id: -1, examnumber: "", fullname: add_all_text} :
               (tblName === "subject") ? {id: -1,  code: "", name: add_all_text} :
               (tblName === "cluster") ? {id: -1,  subj_code: "", name: add_all_text} :
               (tblName === "school") ? {id: -1,  code: "", name: add_all_text} : {};
    }

//========= t_MSSSS_Create_SelectRow  ============= PR2020-12-18 PR2020-07-14
    function t_MSSSS_Create_SelectRow(loc, tblName, tblBody_select, map_dict, selected_pk, el_input, MSSSS_Response) {
        //console.log("===== t_MSSSS_Create_SelectRow ===== ");
        //console.log("..........tblName", tblName);
        //console.log("map_dict", map_dict);

//--- get info from map_dict
        // when tblName = school: pk_int = schoolbase_pk
        const pk_int = (tblName === "school") ? map_dict.base_id :
                    (tblName === "subject") ? map_dict.id :
                    (tblName === "cluster") ? map_dict.id :
                    (tblName === "student") ? map_dict.id : "";

        const code = (tblName === "school") ? map_dict.sb_code :
                    (tblName === "subject") ? map_dict.code :
                    (tblName === "cluster") ? map_dict.subj_code :
                    (tblName === "student") ? map_dict.name_first_init : "";

        const name =  (tblName === "school") ? map_dict.abbrev :
                    (tblName === "subject") ? map_dict.name :
                    (tblName === "cluster") ? map_dict.name :
                    (tblName === "student") ? map_dict.fullname  : "";
        const is_selected_row = (pk_int === selected_pk);

// ---  lookup index where this row must be inserted
        let ob1 = "", ob2 = "", row_index = -1;
        if(tblName === "student"){
            if (map_dict.lastname) { ob1 = map_dict.lastname.toLowerCase()};
            if (map_dict.firstname) { ob2 = map_dict.firstname.toLowerCase()};
            row_index = b_recursive_tblRow_lookup(tblBody_select, loc.user_lang, ob1, ob2);
        } else if(tblName === "subject"){
            if (code) { ob1 = code.toLowerCase()};
            row_index = b_recursive_tblRow_lookup(tblBody_select, loc.user_lang, ob1);
        } else if(tblName === "cluster"){
            if (code) { ob1 = code.toLowerCase()};
            if (name) { ob2 = name.toLowerCase()};
            row_index = b_recursive_tblRow_lookup(tblBody_select, loc.user_lang, ob1, ob2);
        } else if(tblName === "school"){
            if (code) { ob1 = code.toLowerCase()};
            row_index = b_recursive_tblRow_lookup(tblBody_select, loc.user_lang, ob1);
        }

//--------- insert tblBody_select row at row_index
        const map_id = "sel_" + tblName + "_" + pk_int
        const tblRow = tblBody_select.insertRow(row_index);

        tblRow.id = map_id;
        tblRow.setAttribute("data-pk", pk_int);
        tblRow.setAttribute("data-code", code);
        tblRow.setAttribute("data-name", name);
        tblRow.setAttribute("data-table", tblName);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);
        tblRow.setAttribute("data-ob2", ob2);
        //tblRow.setAttribute("data-ob3", ob3);

        const class_selected = (is_selected_row) ? cls_selected: cls_bc_transparent;
        tblRow.classList.add(class_selected);

//- add hover to select row
        add_hover(tblRow)

// --- add td to tblRow.
        let td = null, el_div = null;
        if (["school", "subject", "cluster"].includes(tblName)) {
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                el_div.classList.add("pointer_show")
                el_div.innerText = code;
                el_div.classList.add("tw_075", "px-1")
                td.appendChild(el_div);
            td.classList.add("tsa_bc_transparent");
        };

// --- add td to tblRow.
        td = tblRow.insertCell(-1);
        el_div = document.createElement("div");
            el_div.classList.add("pointer_show")
            el_div.innerText = name;
            el_div.classList.add("tw_240", "px-1")
            td.appendChild(el_div);
        td.classList.add("tsa_bc_transparent");

// --- add second td to tblRow with icon locked, published or activated.
        if (tblName === "school") {
            const locked = (map_dict.locked) ? map_dict.locked : false;
            const activated = (map_dict.activated) ? map_dict.activated : false;
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                const class_locked = (locked) ? "appr_2_6" : (activated) ? "appr_0_1" : "appr_0_0";
                el_div.classList.add("tw_032", class_locked)
                el_div.title = (locked) ? loc.This_school + loc.is_locked : (activated) ? loc.This_school + loc.is_activated : "";
            td.appendChild(el_div);
        };
//--------- add addEventListener
        tblRow.addEventListener("click", function() {t_MSSSS_SelectItem(MSSSS_Response, tblRow, el_input)}, false);
    }; // t_MSSSS_Create_SelectRow

//=========  t_MSSSS_SelectItem  ================ PR2020-12-17
    function t_MSSSS_SelectItem(MSSSS_Response, tblRow, el_input) {
        //console.log( "===== t_MSSSS_SelectItem ========= ");
        //console.log( tblRow);
        // all data attributes are now in tblRow, not in el_select = tblRow.cells[0].children[0];
        // after selecting row, values are stored in input box

// ---  get clicked tablerow
        if(tblRow) {
// ---  deselect all highlighted rows
            DeselectHighlightedRows(tblRow, cls_selected)
// ---  highlight clicked row
            tblRow.classList.add(cls_selected)
// ---  get pk code and value from tblRow, put values in input box
            const data_pk = get_attr_from_el_int(tblRow, "data-pk")
            const data_code = get_attr_from_el(tblRow, "data-code")
            const data_name = get_attr_from_el(tblRow, "data-name")

            el_input.setAttribute("data-pk", data_pk);
            el_input.setAttribute("data-code", data_code);
            el_input.setAttribute("data-name", data_name);

// ---  save and close
            t_MSSSS_Save(el_input, MSSSS_Response);
        }
    }  // t_MSSSS_SelectItem

//=========  t_MSSSS_InputKeyup  ================ PR2020-09-19  PR2021-07-14
    function t_MSSSS_InputKeyup(el_input) {
        //console.log( "===== t_MSSSS_InputKeyup  ========= ");

// ---  get value of new_filter
        let new_filter = el_input.value

        const el_MSSSS_tblBody = document.getElementById("id_MSSSS_tblBody_select");
        let tblBody = el_MSSSS_tblBody;
        const len = tblBody.rows.length;
        if (len){
// ---  filter rows in table select_employee
            const filter_dict = t_Filter_SelectRows(tblBody, new_filter);
        //console.log( "filter_dict", filter_dict);

// ---  if filter results have only one item: put selected item in el_input
            const selected_pk = (filter_dict.selected_pk) ? filter_dict.selected_pk : null;
            if (selected_pk) {
// ---  get pk code and value from filter_dict, put values in input box
                const data_code = (filter_dict.selected_code) ? filter_dict.selected_code : null;
                const data_name = (filter_dict.selected_name) ? filter_dict.selected_name : null;

                el_input.value = data_name;
                el_input.setAttribute("data-pk", selected_pk);
                el_input.setAttribute("data-code", data_code);
                el_input.setAttribute("data-name", data_name);

// ---  Set focus to btn_save
                const el_MSSSS_btn_save = document.getElementById("id_MSSSS_btn_save")
                set_focus_on_el_with_timeout(el_MSSSS_btn_save, 50);
            }  //  if (!!selected_pk) {
        }
    }; // t_MSSSS_InputKeyup

//========= t_MSSSS_display_in_sbr  ====================================
    function t_MSSSS_display_in_sbr(tblName, selected_pk) {
        //console.log( "===== t_MSSSS_display_in_sbr  ========= ");
        //console.log( "tblName", tblName);
        //console.log( "selected_pk", selected_pk);

        const add_all_txt = t_MSSSS_AddAll_txt(tblName);
        //console.log( "add_all_txt", add_all_txt);

        if (tblName === "school") {

        } else if (["subject", "student", "cluster"].includes(tblName)) {
            // PR2022-01-11 debug: skip when el_SBR not defined
            const el_SBR_select_id = (tblName === "student") ? "id_SBR_select_student" :
                                     (tblName === "subject") ? "id_SBR_select_subject" :
                                     (tblName === "cluster") ? "id_SBR_select_cluster" : "xxxxx";
            const el_SBR_select = document.getElementById(el_SBR_select_id);

            if(el_SBR_select){
                const data_rows = (tblName === "student") ? student_rows :
                                  (tblName === "subject") ? subject_rows :
                                  (tblName === "cluster") ? cluster_rows : [];
        //console.log( "data_rows", data_rows);
                let display_txt = null;
                // selected_pk = -1 when clicked on All
                if(selected_pk > 0){
                    const data_dict = b_get_datadict_by_integer_from_datarows(data_rows, "id", selected_pk)
        //console.log( "data_dict", data_dict);
                    const name_field = (tblName === "student") ? "name_first_init" : "name";
                    const code_field = (tblName === "student") ? "name_first_init" : "code";
                    display_txt = (data_dict && name_field in data_dict && data_dict[name_field].length < 25) ? data_dict[name_field] :
                                  (data_dict && code_field in data_dict) ? data_dict[code_field] : "---";

                } else {
                    display_txt = add_all_txt;
                };

                el_SBR_select.value = display_txt;
                add_or_remove_class(el_SBR_select.parentNode, cls_hide, false)
            }
            const el_SBR_container_showall = document.getElementById("id_SBR_container_showall");
            add_or_remove_class(el_SBR_container_showall, cls_hide, false)
        };
    }; // MSSSS_display_in_sbr

// +++++++++++++++++ END OF MODAL SELECT SUBJECT STUDENT ++++++++++++++++++++++++++++++++

// ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

//=========   handle_table_row_clicked   ======================
    function handle_table_row_clicked(e) {  //// EAL: Excel Awp Linked table
        // function gets row_clicked.id, row_other_id, row_clicked_key, row_other_key
        // sets class 'highlighted' and 'hover'
        // and calls 'linkColumns' or 'unlinkColumns'
// currentTarget refers to the element to which the event handler has been attached
// event.target which identifies the element on which the event occurred.
//console.log("=========   handle_table_row_clicked   ======================") ;
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

//========= get_arrayRow_by_keyValue  ====================================
    function get_arrayRow_by_keyValue (dict_list, arrKey, keyValue) {
        // Function returns row of array that contains keyValue in arrKey PR2019-01-05 PR2020-12-28
        // stored_columns[3]: {awpCol: "lastname", caption: "Last name", excCol: "ANAAM" }
        // excel_columns[0]:    {excCol: "ANAAM", awpCol: "lastname", awpCaption: "Achternaam"}
        // PR2020-12-27 do not use Object.entries because it does not allow break
        //console.log("----- get_arrayRow_by_keyValue -----")
        //console.log("dict_list", dict_list)

        let row = null;
        if (dict_list && arrKey && keyValue != null){
            for (let i = 0, dict; dict = dict_list[i]; i++) {
                // dict =  {awpKey: "examnumber", caption: "Examennummer", linkfield: true, excKey: "exnr"}
                const value = dict[arrKey];
                if (!!dict && value != null){
                    // convert number to string for text comparison
                    let isEqual = false;
                    if (typeof(keyValue) === "string"){
                        const value_str = (typeof(value) === "number") ? value.toString() : value;
                        isEqual = (keyValue.toLowerCase() === value_str.toLowerCase());
                    } else {
                        isEqual = (keyValue === value);
                    }
                    if (isEqual){
                        row = dict;
                        break;
        }}}}
        return row;
    }  // get_arrayRow_by_keyValue

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
            found = list_str.includes(";" + value + ";");
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
    //PR2019-01-13 PR2021-01-25 from https://stackoverflow.com/questions/10067094/how-does-this-delay-function-works
    let delay = function(){
    // set timer
        let timer = 0;
    // return setTimeout function
        return function(callback, ms){
            clearTimeout(timer);
            timer = setTimeout(callback, ms);
        };
    };

    //////////////////////////////////

//========= t_get_rowindex_by_sortby  ================= PR2020-06-30
    function t_get_rowindex_by_sortby(tblBody, search_sortby) {
        //console.log(" ===== t_get_rowindex_by_sortby =====");
        //console.log("search_sortby", search_sortby);
        // TODO to be deprecated, only used in schools.js, To be replaced by b_recursive_tblRow_lookup
        let row_index = -1;
// --- loop through rows of tblBody_datatable
        if(search_sortby){
            if (typeof search_sortby === 'string' || search_sortby instanceof String) {
                search_sortby = search_sortby.toLowerCase()};
            for (let i = 0, tblRow; tblRow = tblBody.rows[i]; i++) {
                let row_sortby = get_attr_from_el(tblRow, "data-sortby");
        //console.log("tblRow", tblRow);
        //console.log("rowIndex", tblRow.rowIndex);
        //console.log("i", i, "row_sortby", row_sortby);
                if(row_sortby){
                    if (typeof row_sortby === 'string' || row_sortby instanceof String) {
                        row_sortby = row_sortby.toLowerCase()};
                    if(search_sortby < row_sortby) {
    // --- search_rowindex = row_index - 1, to put new row above row with higher row_sortby
                        row_index = tblRow.rowIndex - 1;
        //console.log("search_sortby < row_sortby: row_index = ", row_index);
                        break;
        }}}}
        if(!row_index){row_index = 0}
        if(row_index >= 0){ row_index -= 1 }
        return row_index
    }  // t_get_rowindex_by_sortby

//=========  t_clear_td_selected  ================ PR2021-11-18
    function t_td_selected_clear(tableBody) {
        //console.log("=========  t_clear_td_selected =========");
        //console.log("cls_selected", cls_selected, "cls_background", cls_background);

        if(tableBody){
            let tblrows = tableBody.getElementsByClassName(cls_selected);
            for (let i = 0, tblRow; tblRow = tblrows[i]; i++) {
                tblRow.classList.remove(cls_selected)
                const td_01 = tblRow.cells[0];
                if(td_01){
                    const el_select = td_01.children[0];
                    if(el_select){
                        el_select.innerHTML = null;
                    };
                };
            };
        };
    }  // t_clear_td_selected

//=========  t_td_selected_set  ================ PR2021-11-18
    function t_td_selected_set(tblRow) {
        //console.log("=========  t_clear_td_selectedy =========");
        //console.log("cls_selected", cls_selected, "cls_background", cls_background);

        tblRow.classList.add(cls_selected)

        const td_01 = tblRow.cells[0];
        if(td_01){
            const el_select = td_01.children[0];
            if(el_select){
                el_select.innerHTML = "&#9658;";  // black pointer right
            };
        };

    }  // t_td_selected_set

//=========  t_td_selected_toggle  ================ PR2021-11-18
    function t_td_selected_toggle(tblRow) {
        //console.log("=========  t_td_selected_toggle =========");
        //console.log("cls_selected", cls_selected, "cls_background", cls_background);
        if(tblRow){
            const new_is_selected = !tblRow.classList.contains(cls_selected);
            if (new_is_selected) {
                tblRow.classList.add(cls_selected)
            } else {
                tblRow.classList.remove(cls_selected)
            };
            const td_01 = tblRow.cells[0];
            if(td_01){
                const el_select = td_01.children[0];
                if(el_select){
                    el_select.innerHTML = (new_is_selected) ? "&#9658;" : null   // "&#9658;" is black pointer right
                };
            };
        };
    }  // t_td_selected_toggle

//=========  t_HighlightSelectedTblRowByPk  ================ PR2019-10-05 PR2020-06-01
    function t_HighlightSelectedTblRowByPk(tblBody, selected_pk, cls_selected, cls_background) {
        //console.log(" --- t_HighlightSelectedTblRowByPk ---")
        //console.log("selected_pk", selected_pk, typeof selected_pk)
        let selected_row;
        if(!cls_selected){cls_selected = "tsa_tr_selected"}
        if(!!tblBody){
            let tblrows = tblBody.rows;
            for (let i = 0, tblRow, len = tblrows.length; i < len; i++) {
                tblRow = tblrows[i];
                if(!!tblRow){
                    const pk_str = tblRow.getAttribute("data-pk");
                    if (selected_pk && pk_str && pk_str === selected_pk.toString()){
                        if(!!cls_background){tblRow.classList.remove(cls_background)};
                        tblRow.classList.add(cls_selected)
                        selected_row = tblRow;
                        //tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' });
                    } else if(tblRow.classList.contains(cls_selected)) {
                        tblRow.classList.remove(cls_selected);
                        if(!!cls_background){tblRow.classList.add(cls_background)}
            }}}
// ---  deselect new row in tblFoot
            let tblFoot = tblBody.parentNode.tFoot
            if(!!tblFoot){
                let firstRow = tblFoot.rows[0]
                if(!!firstRow){
                    firstRow.classList.remove(cls_selected);
            }}
        }
        return selected_row
    }  // t_HighlightSelectedTblRowByPk

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

//========= t_get_tablerow_selected  =============
    function t_get_tablerow_selected(el){
        // PR2019-04-16 function 'bubbles up' till tablerow element is found
        // currentTarget refers to the element to which the event handler has been attached
        // event.target identifies the element on which the event occurred.
        let tr_selected = null;
        let break_it = false;
        while(!break_it){
            if (el){
                if (el.nodeName === "TR"){
                    tr_selected = el;
                    break_it = true
                } else if (el.parentNode){
                    el = el.parentNode;
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
//=========  t_SBR_FillSelectOptionsDepbaseLvlbaseSctbase  ================ PR2021-03-06  PR2021-05-21 PR2021-08-27
    function t_SBR_FillSelectOptionsDepbaseLvlbaseSctbase(tblName, rows, setting_dict) {
        // used in studsubj.js
        const display_rows = []
        const has_items = (!!rows && !!rows.length);
        const has_profiel = setting_dict.sel_dep_has_profiel;

        //console.log("=== t_SBR_FillSelectOptionsDepbaseLvlbaseSctbase");
        //console.log("tblName", tblName);
        //console.log("rows", rows);
        //console.log("loc", loc);
        //console.log("setting_dict", setting_dict);
        //console.log("has_items", has_items);
        //console.log("has_profiel", has_profiel);

        // when label has no id the text is Sector / Profiel, set in .html file
        const el_SBR_select_sector_label = document.getElementById("id_SBR_select_sector_label");
        const all_sectors_profielen_txt = (!el_SBR_select_sector_label) ? loc.All_sectors_profielen : (has_profiel) ? loc.All_profielen :loc.All_sectors;
        let caption_all = null;
        const all_txt = "&#60" + (
                (tblName === "depbase") ? loc.All_departments :
                (tblName === "lvlbase") ? loc.All_levels :
                (tblName === "sctbase") ? all_sectors_profielen_txt : "---"
             ) + "&#62";

        if (has_items){
            if (rows.length === 1){
                // if only 1 level: make that the selected one
                if (tblName === "department"){
                    setting_dict.sel_depbase_pk = rows.base_id;
                } else if (tblName === "lvlbase"){
                    setting_dict.sel_lvlbase_pk = rows.base_id;
                } else if (tblName === "sctbase"){
                    setting_dict.sel_sctbase_pk = rows.base_id
                }
            } else if (rows.length > 1){
                //PR2022-01-08 caption_all = all_txt is necessary to skip all_txt in setting_dict.sel_sector_abbrev
                caption_all = all_txt;

                // add row 'Alle leerwegen' / Alle profielen / Alle sectoren in first row
                // HTML code "&#60" = "<" HTML code "&#62" = ">";
                display_rows.push({value: 0, caption: caption_all })
            };
            for (let i = 0, row; row = rows[i]; i++) {
                display_rows.push({
                    value: row.base_id,
                    caption: (tblName === "department") ?  row.base_code :
                             (tblName === "sctbase") ? row.name : row.abbrev
                });
            };
            const selected_pk = (tblName === "department") ? setting_dict.sel_depbase_pk : (tblName === "lvlbase") ? setting_dict.sel_lvlbase_pk : (tblName === "sctbase") ? setting_dict.sel_sctbase_pk : null;
            const id_SBR_select = (tblName === "department") ? "id_SBR_select_department" : (tblName === "lvlbase") ? "id_SBR_select_level" : (tblName === "sctbase") ? "id_SBR_select_sector" : null;
            const el_SBR_select = (id_SBR_select) ? document.getElementById(id_SBR_select) : null;
            t_FillOptionsFromList(el_SBR_select, display_rows, "value", "caption", null, null, selected_pk);

            // put displayed text in setting_dict - PR2022-01-08 dont show 'All profielen' etc

            //PR2022-01-08 dont put 'All profielen' etc in setting_dict > skip when caption_all has value
            if (!caption_all){
                const sel_abbrev = (el_SBR_select.options[el_SBR_select.selectedIndex]) ? el_SBR_select.options[el_SBR_select.selectedIndex].text : null;
                if (tblName === "lvlbase"){
                    setting_dict.sel_level_abbrev = sel_abbrev;
                } else if (tblName === "sctbase"){
                    setting_dict.sel_sector_abbrev = sel_abbrev;
                };
            };
        };
        // show select level and sector
        if (tblName === "lvlbase"){
            add_or_remove_class(document.getElementById("id_SBR_container_level"), cls_hide, !has_items);
        // set label of profiel
         } else if (tblName === "sctbase"){
            add_or_remove_class(document.getElementById("id_SBR_container_sector"), cls_hide, false);
            // when label has no id the text is Sector / Profiel, set in .html file
            if(el_SBR_select_sector_label){el_SBR_select_sector_label.innerText = ( (has_profiel) ? loc.Profiel : loc.Sector ) + ":"};
        };
    };  // t_SBR_FillSelectOptionsDepbaseLvlbaseSctbase

//========= t_FillOptionLevelSectorFromMap  ============= PR2020-12-11 from tsa PR2021-07-18
    function t_FillOptionLevelSectorFromMap(tblName, pk_field, data_map, depbase_pk, selected_pk, firstoption_txt) {
         //console.log( "===== t_FillOptionLevelSectorFromMap  ========= ");
         //console.log( "data_map", data_map);
         // used in page schemes
// add empty option on first row, put firstoption_txt in < > (placed here to escape \< and \>
        let option_text = "";
        if(firstoption_txt){
            option_text = "<option value=\"0\" data-ppk=\"0\">" + firstoption_txt + "</option>";
        }
// --- loop through data_map, fill only items with department_pk in depbases
        for (const [map_id, item_dict] of data_map.entries()) {
         //console.log( "item_dict", item_dict);
            if(item_dict.depbases && depbase_pk && item_dict.depbases.includes(depbase_pk)){
                option_text += FillOptionText(tblName, pk_field, item_dict, selected_pk);
            }
        }
        return option_text
    }  // t_FillOptionLevelSectorFromMap

//========= FillOptionText  ============= PR2020-12-11 from tsa
    function FillOptionText(tblName, pk_field, item_dict, selected_pk) {
        //console.log( "===== FillOptionText  ========= ");
        const value = (tblName === "level") ? (item_dict.abbrev) ? item_dict.abbrev : "---"
                                            : (item_dict.name) ? item_dict.name : "---" ;
        const pk_int = item_dict[pk_field];
        const pk_str = (pk_int != null) ? pk_int.toString() : "";
        const selected_pk_str = (selected_pk != null) ? selected_pk.toString() : "";
        const is_selected =  (selected_pk && pk_int === selected_pk);
        let item_text = "<option value=\"" + pk_str + "\"";
        if (is_selected) {item_text += " selected=true" };
        item_text +=  ">" + value + "</option>";
        return item_text
    }  // FillOptionText

//========= t_FillSelectOptions  =======  // PR2020-09-30 PR2021-05-12
    function t_FillSelectOptions(el_select, data_map, id_field, display_field, hide_none,
                selected_pk, selectall_text, select_text_none, select_text) {
        console.log( "===== t_FillSelectOptions  ===== ");
        // called by page exam MEXQ_FillSelectTableLevel  and page_subject SBR_Select_scheme
        console.log( "selected_pk", selected_pk, typeof selected_pk);

// ---  fill options of select box
        let option_text = "";
        let row_count = 0

// --- loop through data_map
        if(!!data_map){
            for (const [map_id, map_dict] of data_map.entries()) {
                const pk_int = map_dict[id_field];
                const display_value = (map_dict[display_field]) ?  map_dict[display_field] : "---";

        console.log( "map_dict", map_dict);
        console.log( "pk_int", pk_int, typeof pk_int);
        console.log( "display_value", display_value);
                option_text += "<option value=\"" + pk_int + "\"";
                if (pk_int === selected_pk) {option_text += " selected=true" };
                option_text +=  ">" + display_value + "</option>";
                row_count += 1;
            }
        }  //   if(!!data_map){
        let select_first_option = false;

        // when 'all customers is selected (selected_customer_pk): there are no orders in selectbox 'orders'
        // to display 'all orders' instead of 'no orders' we make have boolean 'hide_none' = true
        if (!row_count && select_text_none && !hide_none){
            option_text = "<option value=\"\" disabled selected hidden>" + select_text_none + "...</option>"
        } else if (!!selectall_text){
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

//========= t_FillOptionFromList  ============= PR2020-01-08
    function t_FillOptionFromList(data_list, selected_pk, firstoption_txt) {
         //console.log( "===== t_FillOptionFromList  ========= ");
         // add empty option on first row, put firstoption_txt in < > (placed here to escape \< and \>
         // used in page customers
        let option_text = "";
        if(!!firstoption_txt){
            option_text = "<option value=\"0\" data-ppk=\"0\">" + firstoption_txt + "</option>";
        }
        for (let i = 0, len = data_list.length; i < len; i++) {
            const item_dict = data_list[i];
            const item_text = FillOptionText(item_dict, selected_pk);
            option_text += item_text;
        }
        return option_text
    }  // t_FillOptionFromList

//========= t_FillOptionsFromList  =======  PR2020-12-17
    function t_FillOptionsFromList(el_select, data_list, value_field, caption_field,
                                    select_text, select_text_none, selected_value, filter_field, filter_value) {
        //console.log( "=== t_FillOptionsFromList ");
        //console.log( "data_list", data_list);
        //console.log( "value_field", value_field);
        //console.log( "selected_value", selected_value);
        //console.log( "filter_field", filter_field);
        //console.log( "filter_value", filter_value, typeof filter_value);

// ---  fill options of select box
        let option_text = "";
        let row_count = 0;

// --- loop through data_list
        if(data_list){
            for (let i = 0, len = data_list.length; i < len; i++) {
                const item_dict = data_list[i];

                const item_value = (item_dict[value_field]) ? item_dict[value_field] : null;
                const item_caption = (item_dict[caption_field]) ? item_dict[caption_field] : "---";
                // if filter_field has no value: all items are shown,
                // otherwise only items with matching filter_value are shown PR2021-04-21
                let show_row = false;
                if(!filter_field) {
                    show_row = true;
                } else {
                    const item_filter = item_dict[filter_field];
                    if (item_filter && filter_value && item_filter === filter_value) {
                        show_row = true;
                    };
                };

                if(show_row){
                    option_text += t_FillOptionTextNew(item_value, item_caption, selected_value);
                    row_count += 1;
                };
            };
        };  //   if(!!data_list){
        let select_first_option = false;

// show text "No items found" when no rows and select_text_none has value
        if (!row_count){
            if(select_text_none){
                option_text = "<option value=\"\" disabled selected hidden>" + select_text_none + "</option>";
            }
        } else if (row_count === 1) {
            select_first_option = true;
        } else if (row_count > 1 && select_text){
            option_text = "<option value=\"\" disabled selected hidden>" + select_text + "</option>" + option_text;
        };
        el_select.innerHTML = option_text;

// if there is only 1 option: select first option
        if (select_first_option){
            el_select.selectedIndex = 0;
        };
// disable element if it has none or one rows
        el_select.disabled = (row_count <= 1);
    };  // t_FillOptionsFromList

//========= t_FillOptionTextNew  ============= PR2020-12-11 from tsa
    function t_FillOptionTextNew(value, caption, selected_value) {
        //console.log( "===== t_FillOptionTextNew  ========= ");
        let item_text = "<option value=\"" + value + "\"";
        if (selected_value && value === selected_value) {item_text += " selected=true" };
        item_text +=  ">" + caption + "</option>";
        return item_text;
    };  // t_FillOptionTextNew


// +++++++++++++++++ FILTER ++++++++++++++++++++++++++++++++++++++++++++++++++
//========= t_Filter_SelectRows  ==================================== PR2020-01-17 PR2021-01-23
    function t_Filter_SelectRows(tblBody_select, filter_text, filter_show_inactive, has_ppk_filter, selected_ppk, col_index_list) {
        //console.log( "===== t_Filter_SelectRows  ========= ");
        //console.log( "filter_text: <" + filter_text + ">");
        //console.log( "has_ppk_filter: " + has_ppk_filter);
        //console.log( "selected_ppk: " + selected_ppk, typeof selected_ppk);

        const filter_text_lower = (filter_text) ? filter_text.toLowerCase() : "";
        if(!col_index_list){col_index_list = []};
        let has_selection = false, has_multiple = false;
        let sel_pk = null, sel_ppk = null, sel_code = null, sel_name = null, sel_value = null;
        let sel_display = null, sel_rowid = null, sel_innertext = null;
        let row_count = 0;
        for (let i = 0, tblRow; tblRow = tblBody_select.rows[i]; i++) {
            if (!!tblRow){
                let hide_row = false
// ---  show only rows of selected_ppk_str, only if has_ppk_filter = true
                if(has_ppk_filter){
                    const ppk_str = tblRow.dataset.ppk;
                    if(selected_ppk){
                        hide_row = (ppk_str !== selected_ppk.toString())
                    } else {
                        hide_row = true;
                }};
// ---  hide inactive rows when filter_show_inactive = false
                if(!hide_row && !filter_show_inactive){
                    const inactive_str = tblRow.dataset.inactive;
                    if (!!inactive_str) {
                        hide_row = (inactive_str.toLowerCase() === "true")
                }};
// ---  show all rows if filter_text = ""
                if (!hide_row && filter_text_lower){
                    let found = false;
                    // check columns in col_index_list, check all if list is empty PR2020-12-17
                    for (let i = 0, el, cell, len = tblRow.cells.length; i < len; i++) {
                        if(!col_index_list.length || col_index_list.includes(i)){
                            cell = tblRow.cells[i];
                            if(cell){
                                const el_div = cell.children[0];
                                if(el_div){
                                    let el_value = el_div.innerText;
                                    if(el_value){
                                        el_value = el_value.toLowerCase();
                                        if (el_value.includes(filter_text_lower)) {
                                            found = true;
                                            break;
                    }}}}}}
                    hide_row = (!found);
                };
                if (hide_row) {
                    tblRow.classList.add(cls_hide)
                } else {
                    tblRow.classList.remove(cls_hide);
                    row_count += 1;
// ---  put values from first row that is shown in select_value etc
                    if(!has_selection ) {
                        sel_pk = tblRow.dataset.pk;
                        sel_ppk = tblRow.dataset.ppk;
                        sel_code = tblRow.dataset.code;
                        sel_name = tblRow.dataset.name;
                        sel_value = tblRow.dataset.value;
                        sel_display = tblRow.dataset.display;
                        sel_rowid = tblRow.id;
                    } else {
                        has_multiple = true;
                    }
                    has_selection = true;
                    sel_innertext = [];
                    for (let i = 0, cell; cell = tblRow.cells[i]; i++) {
                        sel_innertext[i] = cell.innerText
                    }
        }}};
// ---  set select_value etc null when multiple items found
        if (has_multiple){
            sel_pk = null;
            sel_ppk = null;
            sel_code = null;
            sel_name = null;
            sel_value = null,
            sel_display = null;
            sel_rowid = null;
            sel_innertext = null;
        }
        const filter_dict = {row_count: row_count}
        // (value == null) equals to (value === undefined || value === null)
        if(sel_pk != null) {filter_dict.selected_pk = sel_pk};
        if(sel_ppk != null) {filter_dict.selected_ppk = sel_ppk};
        if(sel_code != null) {filter_dict.selected_code = sel_code};
        if(sel_name != null) {filter_dict.selected_name = sel_name};
        if(sel_value != null) {filter_dict.selected_value = sel_value};
        if(sel_display != null) {filter_dict.selected_display = sel_display};
        if(sel_pk != null) {filter_dict.selected_rowid = sel_rowid};
        if(sel_innertext != null) {filter_dict.selected_innertext = sel_innertext};
        return filter_dict
    }; // t_Filter_SelectRows

//========= t_ShowTableRow  ==================================== PR2020-01-17
    function t_ShowTableRow(tblRow, tblName, filter_dict, filter_show_inactive, has_ppk_filter, selected_ppk) {  // PR2019-09-15
        //console.log( "===== t_ShowTableRow  ========= ", tblName);
        //console.log("filter_show_inactive", filter_show_inactive);
        //console.log("tblRow", tblRow);

        // function filters by inactive and substring of fields
        // also filters selected customer pk in table order
        //  - iterates through cells of tblRow
        //  - skips filter of new row (new row is always visible) -> 'data-addnew' = 'true'
        //  - filters on parent-pk -> 'data-ppk' = selected_ppk
        //  - if filter_name is not null:
        //       - checks tblRow.cells[i].children[0], gets value, in case of select element: data-value
        //       - returns show_row = true when filter_name found in value
        // filters on blank when filter_text = "#"
        //  - if col_inactive has value >= 0 and hide_inactive = true:
        //       - checks -> 'data-inactive' = 'true'
        //       - hides row if inactive = true
        // gets value of :
        // when tag = 'select': value = selectedIndex.text
        // when tag = 'input': value = el.value
        // else: (excl tag = 'a'): value = el.innerText
        // when not found:  value = 'data-value'
        let hide_row = false;
        if (tblRow){

// 1. skip new row
    // check if row is_addnew_row. This is the case when pk is a string ('new_3'). Not all search tables have "id" (select customer has no id in tblrow)
            const is_addnew_row = (get_attr_from_el(tblRow, "data-addnew") === "true");
            if(!is_addnew_row){

        // show only rows of selected_ppk, only if selected_ppk has value
                if(has_ppk_filter){
                    if(!selected_ppk){
                        hide_row = true;
                    } else {
                        const ppk_str = get_attr_from_el(tblRow, "data-ppk")
        //console.log("ppk_str", ppk_str);
                        if(!ppk_str){
                            hide_row = true;
                        } else if (ppk_str !== selected_ppk.toString()) {
                            hide_row = true;
                        }
                    }
                }
        //console.log( "hide_row after selected_ppk: ", has_ppk_filter, selected_ppk,  hide_row);

// hide inactive rows if filter_show_inactive
        //console.log("filter_show_inactive", filter_show_inactive);
                if(!hide_row && !filter_show_inactive){
                    const inactive_str = get_attr_from_el(tblRow, "data-inactive")
        //console.log("inactive_str", inactive_str);
                    if (inactive_str && (inactive_str.toLowerCase() === "true")) {
                        hide_row = true;
                    }
                }
        //console.log( "hide_row after filter_show_inactive: ", hide_row);

// show all rows if filter_name = ""
        //console.log("filter_dict", filter_dict);
                if (!hide_row && !isEmpty(filter_dict)){
                    //Object.keys(filter_dict).forEach(function(key) {
                    for (const [key, value] of Object.entries(filter_dict)) {
                        // key = col_index
                        // filter_dict is either a dict of lists ( when created by t_SetExtendedFilterDict)
                        // filter_dict[col_index] = [filter_tag, filter_value, mode] modes are: 'blanks_only', 'no_blanks', 'lte', 'gte', 'lt', 'gt'
                        // otherwise filter_dict is a dict of strings
                        const filter_text = (Array.isArray(value)) ? value[1] : value;

        //console.log("key", key);
        //console.log("filter_text", filter_text);
                        const filter_blank = (filter_text === "#")
                        const filter_non_blank = (filter_text === "@")
                        let tbl_cell = tblRow.cells[key];
                        if (tbl_cell){
                            let el = tbl_cell.children[0];
                            if (el) {
                        // skip if no filter on this colums
                                if(filter_text){
                        // get value from el.value, innerText or data-value
                                    const el_tagName = el.tagName.toLowerCase()
        //console.log("el_tagName", el_tagName);
                                    let el_value = null;
                                    if (el_tagName === "select"){
                                        el_value = el.options[el.selectedIndex].text;
                                    } else if (el_tagName === "input"){
                                        el_value = el.value;
                                    } else if (el_tagName === "a"){
                                        // skip
                                    } else {
                                        el_value = el.innerText;
                                    }
                                    if (!el_value){el_value = get_attr_from_el(el, "data-value")}
        //console.log("el_value",  el_value);

                                    // PR2020-06-13 debug: don't use: "hide_row = (!el_value)", once hide_row = true it must stay like that
                                    if (filter_blank){
                                        if (el_value){hide_row = true};
                                    } else if (filter_non_blank){
                                        if (!el_value){hide_row = true};
                                    } else if (!el_value){
                                        hide_row = true;
                                    } else {
                                        const el_value_lc = el_value.toLowerCase() ;
        //console.log("el_value_lc",  el_value_lc);
                                        // hide row if filter_text not found
                                        if (!el_value_lc.includes(filter_text)) {hide_row = true};
                                    }
                                }  //  if(!!filter_text)
                            }  // if (!!el) {
                        }  //  if (!!tbl_cell){
                    };  // Object.keys(filter_dict).forEach(function(key) {
                }  // if (!hide_row)
        //console.log( "hide_row after filter_dict: ", hide_row);
            } //  if(!is_addnew_row){
        }  // if (!!tblRow)
        return !hide_row
    }; // t_ShowTableRow
// ++++++++++++  END OF FILTER +++++++++++++++++++++++++++++++++++++++


// ++++++++++++  FILTER TABLES +++++++++++++++++++++++++++++++++++++++
//========= t_SetExtendedFilterDict  ======================== PR2020-07-12 PR2020-08-29
    function t_SetExtendedFilterDict(el, col_index, filter_dict, event_key) {
       //console.log( "===== t_SetExtendedFilterDict  ========= ");
       //console.log( "col_index ", col_index, "event_key ", event_key);
        // filter_dict = [ ["text", "m", ""], ["number", 180, "gt"] ]

        //  filter_dict[col_index] = [filter_tag, filter_value, mode]
        //  modes are: 'blanks_only', 'no_blanks', 'lte', 'gte', 'lt', 'gt'

// --- get filter tblRow and tblBody
        let tblRow = t_get_tablerow_selected(el);
        const filter_tag = get_attr_from_el(el, "data-filtertag")
        //console.log( "filter_tag ", filter_tag);

        const col_count = tblRow.cells.length
        //console.log( "col_count ", col_count);
        let mode = "", filter_value = null, skip_filter = false;
// --- skip filter row when clicked on Shift, Control, Alt, Tab. Filter is set by the other key that is pressed
        if (["Shift", "Control", "Alt", "Tab"].includes(event.key)) {
            skip_filter = true
// --- reset filter row when clicked on 'Escape'
        // PR2020-09-03 don't use event.which = 27. Is deprecated. Use event_key === "Escape" instead
        } else if (event_key === "Escape") {
            filter_dict = {};
            for (let i = 0, len = tblRow.cells.length; i < len; i++) {
                let el = tblRow.cells[i].children[0];
                if(el){ el.value = null};
            }
        } else if ( filter_tag === "toggle") {
            let arr = (filter_dict && filter_dict[col_index]) ? filter_dict[col_index] : "";
            const old_value = (arr && arr[1] ) ? arr[1] : 0;
            // subtract 1, to get order V, X, -
            let new_value = old_value - 1;
            if(new_value < 0) { new_value = 2};
            filter_dict[col_index] = [filter_tag, new_value];
        } else if ( filter_tag === "inactive") {
            let arr = (filter_dict && filter_dict[col_index]) ? filter_dict[col_index] : "";
            const old_value = (arr && arr[1] ) ? arr[1] : 0;
            // subtract 1, to get order V, X, -
            let new_value = old_value - 1;
            if(new_value < 0) { new_value = 1};
            filter_dict[col_index] = [filter_tag, new_value];

        } else if ( ["boolean", "toggle", "toggle_2", "toggle_3"].includes(filter_tag)) {
            // //filter_dict = [ ["boolean", "1"] ];
            // toggle value "0" / "1" when boolean
            let arr = (filter_dict && filter_dict[col_index]) ? filter_dict[col_index] : null;
            const value = (arr && arr[1] ) ? arr[1] : "0";
            let new_value = "0";
            if ( ["boolean", "toggle", "toggle_2"].includes(filter_tag)) {
                new_value = (value === "0") ? "1" : "0";
            } else if ( ["inactive", "activated", ].includes(filter_tag)) {
                new_value = (value === "0") ? "1" : (value === "1") ? "2" : "0";
            }
            if (!new_value){
                if (filter_dict[col_index]){
                    delete filter_dict[col_index];
                }
            } else {
                filter_dict[col_index] = [filter_tag, new_value]
            }
        } else {
            let filter_dict_value = (filter_dict && filter_dict[col_index]) ? filter_dict[col_index] : "";
            let el_value_str = (el.value) ? el.value.toString() : "";
            let filter_text = el_value_str.trim().toLowerCase();
            if (!filter_text){
                if (filter_dict_value){
                    delete filter_dict[col_index];
                }
            } else if (filter_text !== filter_dict_value) {
                // filter text is already trimmed and lowercase
                if(filter_text === "#"){
                    mode = "blanks_only";
                } else if(filter_text === "@" || filter_text === "!"){
                    mode = "no_blanks";
                } else if (filter_tag === "text") {
                    // employee/rosterdate and order columns, no special mode on these columns
                    filter_value = filter_text;
                } else if (filter_tag === "number") {
                    // lt and gt sign must be followed by number. Skip filter when only lt or gt sign is entered
                    if ( [">", ">=", "<", "<="].includes(filter_text) ) {
                       skip_filter = true;
                    }
                    if(!skip_filter) {
                        const first_two_char = filter_text.slice(0, 2);
                        const remainder = filter_text.slice(2);
                        mode = (first_two_char === "<=" && remainder) ? "lte" : (first_two_char === ">="  && remainder) ? "gte" : "";
                        if (!mode){
                            const first_char = filter_text.charAt(0);
                            const remainder = filter_text.slice(1);
                            mode = (first_char === "<" && remainder) ? "lt" : (first_char === ">" && remainder) ? "gt" : "";
                        }
                        // remove "<" , "<=", ">" or ">=" from filter_text
                        let filter_str = (["lte", "gte"].includes(mode)) ? filter_text.slice(2) :
                                         (["lt", "gt"].includes(mode)) ? filter_text.slice(1) : filter_text;
                        filter_value = 0;
                        const value_number = Number(filter_str.replace(/\,/g,"."));
                        filter_value = (value_number) ? value_number : null;

                        //console.log( "filter_tag ", filter_tag);
                        //console.log( "filter_str ", filter_str);
                        //console.log( "value_number ", value_number);

                    }
                }; // other
                if (!skip_filter) {
                    filter_dict[col_index] = [filter_tag, filter_value, mode]
                };
            }
        }
        //console.log( "filter_dict ", filter_dict);
        return skip_filter;
    }  // t_SetExtendedFilterDict

//========= t_Filter_TableRows  ==================================== PR2020-08-17  PR2021-08-10
    function t_Filter_TableRows(tblBody_datatable, filter_dict, selected, count_unit_sing, count_unit_plur ) {
        //console.log( "===== t_Filter_TableRows  ========= ");
        //console.log( "filter_dict", filter_dict);

        selected.item_count = 0
// ---  loop through tblBody.rows
        for (let i = 0, tblRow, show_row; tblRow = tblBody_datatable.rows[i]; i++) {
            tblRow = tblBody_datatable.rows[i]
            show_row = t_ShowTableRowExtended(filter_dict, tblRow);
            add_or_remove_class(tblRow, cls_hide, !show_row);
            if (show_row) {selected.item_count += 1};
        }
// ---  show total in sidebar
        t_set_sbr_itemcount_txt(loc, selected.item_count, count_unit_sing, count_unit_plur, setting_dict.user_lang);
    }; // t_Filter_TableRows

//========= t_set_sbr_itemcount_txt  ==================================== PR2021-12-20
    function t_set_sbr_itemcount_txt(loc, item_count, count_unit_sing, count_unit_plur, user_lang) {
        //console.log( "===== t_set_sbr_itemcount_txt  ========= ");
        //console.log( "item_count", item_count);

// ---  show total in sidebar
        const el_SBR_item_count = document.getElementById("id_SBR_item_count");

        if (el_SBR_item_count){
            let inner_text = null;
            if (selected.item_count){
                const count_txt = f_format_count(user_lang, item_count);
                const unit_sing = (count_unit_sing) ? count_unit_sing.toLowerCase() : "";
                const unit_plur = (count_unit_plur) ? count_unit_plur.toLowerCase() : "";
                const unit_txt = (item_count === 1) ? unit_sing : unit_plur;
                inner_text = [loc.Total, count_txt, unit_txt].join(" ");
            }
            el_SBR_item_count.innerText = inner_text;
        //console.log( "inner_text", inner_text);
        };
    }; // t_set_sbr_itemcount_txt

//========= t_ShowTableRowExtended  ==================================== PR2020-07-12 PR2020-09-12 PR2021-10-28
    function t_ShowTableRowExtended(filter_dict, tblRow, data_inactive_field) {
        //console.log( "===== t_ShowTableRowExtended  ========= ");
        //console.log( "filter_dict", filter_dict);
        //console.log( "filter_dict", filter_dict);
        // filter_dict = {2: ["text", "r", ""], 4: ["text", "y", ""] }
        //  filter_row = [empty × 2, "acu - rif", empty, "agata mm"]

        // PR2020-11-20 from https://thecodebarbarian.com/for-vs-for-each-vs-for-in-vs-for-of-in-javascript
        // - With the other two constructs, forEach() and for/of, you get access to the array element itself.
        //   With forEach() you can access the array index i, with for/of you cannot.
        // - for/in will include non-numeric properties. (Assign to a non-numeric property: arr.test = 'bad')
        // - Avoid using for/in over an array unless you're certain you mean to iterate over non-numeric keys and inherited keys.
        // - forEach() and for/in skip empty elements, also known as "holes" in the array, for and for/of do not.
        // - Generally, for/of is the most robust way to iterate over an array in JavaScript.
        // - It is more concise than a conventional for loop and doesn't have as many edge cases as for/in and forEach().
        let hide_row = false;

// ---  show all rows if filter_dict is empty - except for inactive ones
        if (tblRow){

// --- PR2021-10-28 new way of filtering inactive rows: (for now: only used in mailbox - deleted)
            // - set filter inactive before other filters, inactive value is stored in tblRow, "data-inactive", skio when data_inactive_field is null
            // - filter_dict has key 'showinactive', value is integer.
            // values of showinactive are:  '0'; is show all, '1' is show active only, '2' is show inactive only
            if (data_inactive_field){
                const filter_showinactive = (filter_dict && filter_dict.showinactive != null) ? filter_dict.showinactive : 1;
                const is_inactive = !!get_attr_from_el_int(tblRow, data_inactive_field);

                hide_row = (filter_showinactive === 1) ? (is_inactive) :
                           (filter_showinactive === 2) ? (!is_inactive) : false
            };

            if (!isEmpty(filter_dict)){
    // ---  loop through filter_dict key = index_str, value = filter_arr
               for (const [index_str, filter_arr] of Object.entries(filter_dict)) {

    // ---  skip column if no filter on this column, also if hide_row is already true
                    if(!hide_row && filter_arr){
                        // filter text is already trimmed and lowercase
                        const col_index = Number(index_str);
                        const filter_tag = filter_arr[0];
                        const filter_value = filter_arr[1];
                        const filter_mode = filter_arr[2];

            //console.log( "filter_tag", filter_tag)
            //console.log( "filter_value", filter_value)
            //console.log( "col_index", col_index)
                        const cell = tblRow.cells[col_index];
            //console.log( "cell", cell)
                        if(cell){
                            const el = cell.children[0];
            //console.log( "el", el)
                            if (el){
                                const cell_value = get_attr_from_el(el, "data-filter")
            //console.log( "cell_value", cell_value)
                                if (filter_tag === "toggle"){
                                    // default filter toggle '0'; is show all, '1' is show tickmark, '2' is show without tickmark
                                    if (filter_value === "2"){
                                        // only show rows without tickmark
                                         if (cell_value === "1") { hide_row = true };
                                    } else if (filter_value === "1"){
                                        // only show rows with tickmark
                                         if (cell_value !== "1") { hide_row = true };
                                    }
                                } else if(filter_tag === "multitoggle"){  // PR2021-08-21
                                    if (filter_value){
                                        hide_row = (cell_value !== filter_value);
                                    };
                                } else if(filter_mode === "blanks_only"){  // # : show only blank cells
                                    if (cell_value) { hide_row = true };
                                } else if(filter_mode === "no_blanks"){  // # : show only non-blank cells
                                    if (!cell_value) {hide_row = true};
                                } else if( filter_tag === "text") {
                                    // hide row if filter_value not found or when cell is empty
                                     if (cell_value) {
                                        if (!cell_value.includes(filter_value)) { hide_row = true };
                                     } else {
                                        hide_row = true;
                                     }
                                } else if( filter_tag === "number") {
                                    // numeric columns: make blank cells zero

                                    if(!Number(filter_value)) {
                                        // hide all rows when filter is not numeric
                                        hide_row = true;
                                    } else {
                                        const filter_number = Number(filter_value);
                                        const cell_number = (Number(cell_value)) ? Number(cell_value) : 0;
            //console.log( "cell_number", cell_number, typeof cell_number);
                                        if ( filter_mode === "lte") {
                                            if (cell_number > filter_number) {hide_row = true};
                                        } else if ( filter_mode === "lt") {
                                            if (cell_number >= filter_number) {hide_row = true};
                                        } else if (filter_mode === "gte") {
                                            if (cell_number < filter_number) {hide_row = true};
                                        } else if (filter_mode === "gt") {
                                            if (cell_number <= filter_number) {hide_row = true};
                                        } else {
                                            if (cell_number !== filter_number) {hide_row = true};
                                        }
                                    }

                                } else if( filter_tag === "status") {

                                    // TODO
                                    if(filter_value === 1) {
                                        if(cell_value){
                                            // cell_value = "status_1_5", '_1_' means data_has_changed
                                            const arr = cell_value.split('_')
                                            hide_row = (arr[1] && arr[1] !== "1")
                                        }
                                    }
                                }
                            }
                        };  // if(cell)
                    };  //  if(filter_arr)
                };  // for (const [index_str, filter_arr] of Object.entries(filter_dict))
            }  // if (!isEmpty(filter_dict)
        }  // if (tblRow)
        //console.log("hide_row", hide_row);
        return !hide_row
    }; // t_ShowTableRowExtended

//========= t_create_filter_row  ====================================
    function t_create_filter_row(tblRow, filter_dict) {  // PR2020-09-14 PR2021-03-23
        //console.log( "===== t_create_filter_row  ========= ");
        //console.log( "filter_dict", filter_dict);
        let filter_row = [];
        if (tblRow){
            for (const index_str of Object.keys(filter_dict)) {
                const col_index = (Number(index_str)) ? Number(index_str) : 0;
                const el = tblRow.cells[col_index].children[0];
                if(el){
                    let data_filter = get_attr_from_el(el, "data-filter")
                    if( ["number", "duration", "amount"].includes(filter_dict[index_str][0])){
                        data_filter = (Number(data_filter)) ? Number(data_filter) : null;
                    }
                    if (data_filter) {
                        filter_row[col_index] = data_filter
                    }
                }
            };
        }
        return filter_row
    }; // t_create_filter_row
// ++++++++++++  END OF FILTER PAYROLL TABLES +++++++++++++++++++++++++++++++++++++++


// +++++++++++++++++ MODAL SELECT COLUMNS ++++++++++++++++++++++++++++++++++++++++++ PR2021-08-18 PR2021-12-16

//  columns_tobe_hidden        is a fixed array of fields that may be hidden, per page and tab, set on loading page

//  setting_dict.cols_hidden   contains saved list of hidden columns, retrieved on opening page

//  mod_MCOL_dict.cols_hidden  is deep copy of setting_dict.cols_hidden, fields are added / removed from this array

// mod_MCOL_dict is only used in this script for modal. pages use columns_hidden and columns_tobe_hidden
// mod_MCOL_dict.cols_hidden holds fields in modal before they are saved, columns_hidden holds saved fields

// these function use selected_btn, columns_hidden[tblName], columns_tobe_hidden[tblName].fields;

const columns_tobe_hidden = {};
const mod_MCOL_dict = {selected_btn: null, cols_hidden: []}


//=========  t_MCOL_Open  ================ PR2021-08-02 PR2021-12-02
    function t_MCOL_Open(page) {
        console.log(" -----  t_MCOL_Open   ----")
        console.log("selected_btn", selected_btn)
        console.log("columns_tobe_hidden", columns_tobe_hidden)
        console.log("mod_MCOL_dict.cols_hidden", mod_MCOL_dict.cols_hidden)

        mod_MCOL_dict.page = page;
        mod_MCOL_dict.selected_btn = selected_btn;

        // mod_MCOL_dict.cols_hidden is filled after loading page by b_copy_array_noduplicates(setting_dict.cols_hidden, mod_MCOL_dict.cols_hidden);
        mod_MCOL_dict.col_tobe_hidden_fields = [];
        mod_MCOL_dict.col_tobe_hidden_captions = [];
        // only get values from key 'all' and key selected_btn
        const merged_fields = [], merged_captions = [];
        for (const [key, col_tobe_hidden_dict] of Object.entries(columns_tobe_hidden)) {
            if (key === mod_MCOL_dict.selected_btn || key === 'all'){
                // PR2022-03-01 extend existing array with new one
                // was:  (doesn't add arrays)
                //mod_MCOL_dict.col_tobe_hidden_fields = col_tobe_hidden_dict.fields;
                //mod_MCOL_dict.col_tobe_hidden_captions = col_tobe_hidden_dict.captions;
                // from https://stackoverflow.com/questions/1374126/how-to-extend-an-existing-javascript-array-with-another-array-without-creating
                merged_fields.push(...col_tobe_hidden_dict.fields);
                merged_captions.push(...col_tobe_hidden_dict.captions);
            };
        };
        // remove dulplicates
        b_copy_array_noduplicates(merged_fields, mod_MCOL_dict.col_tobe_hidden_fields);
        b_copy_array_noduplicates(merged_captions, mod_MCOL_dict.col_tobe_hidden_captions);

        t_MCOL_FillSelectTable();
        const el_MCOL_btn_save = document.getElementById("id_MCOL_btn_save")
        el_MCOL_btn_save.disabled = true

// ---  show modal, set focus on save button
       $("#id_mod_select_columns").modal({backdrop: true});
    }  // t_MCOL_Open

//=========  t_MCOL_Save  ================ PR2021-08-02 PR2021-12-02
    function t_MCOL_Save(url_usersetting_upload, HandleBtnSelect) {
        console.log(" -----  t_MCOL_Save   ----")
        const upload_dict = {};
        const upload_colhidden_list = []
        if (mod_MCOL_dict.cols_hidden && mod_MCOL_dict.cols_hidden.length){
            for (let i = 0, field; field = mod_MCOL_dict.cols_hidden[i]; i++) {
                if (!upload_colhidden_list.includes(field)){
                    upload_colhidden_list.push(field);
                };
            };
        };
        upload_dict[mod_MCOL_dict.page] = {cols_hidden: upload_colhidden_list}
    console.log("upload_dict", upload_dict);
    console.log("url_usersetting_upload", url_usersetting_upload);

        b_UploadSettings (upload_dict, url_usersetting_upload);

        HandleBtnSelect(selected_btn, true)  // true = skip_upload
// hide modal
        // in HTML: data-dismiss="modal"
    }  // t_MCOL_Save

//=========  t_MCOL_FillSelectTable  ================ PR2021-07-07 PR2021-08-02 PR2021-12-14
    function t_MCOL_FillSelectTable() {
        //console.log("===  t_MCOL_FillSelectTable == ");
        //console.log("selected_btn", selected_btn);
        //console.log("field_settings", field_settings);
        //console.log("mod_MCOL_dict.cols_hidden", mod_MCOL_dict.cols_hidden);
        //console.log("columns_tobe_hidden", columns_tobe_hidden);

        const el_MCOL_tblBody_available = document.getElementById("id_MCOL_tblBody_available");
        const el_MCOL_tblBody_show = document.getElementById("id_MCOL_tblBody_show");
        el_MCOL_tblBody_available.innerHTML = null;
        el_MCOL_tblBody_show.innerHTML = null;

//+++ loop through list of fields
        if(mod_MCOL_dict.col_tobe_hidden_fields && mod_MCOL_dict.col_tobe_hidden_fields.length){
            for (let j = 0, field; field = mod_MCOL_dict.col_tobe_hidden_fields[j]; j++) {
                const captions = mod_MCOL_dict.col_tobe_hidden_captions;

    // - skip column 'Leerweg' when not sel_dep_level_req  || setting_dict.sel_dep_level_req
                const skip_level = (["lvlbase_id", "lvl_abbrev"].includes(field) && !setting_dict.sel_dep_level_req);
                if(!skip_level){

    // - display 'Profiel' when sel_dep_has_profiel
                    const caption = (field === "sct_abbrev") ?
                                    (setting_dict.sel_dep_has_profiel) ? loc.Profiel : loc.Sector :
                                    (captions[j]) ? loc[captions[j]] : null;
                    const is_hidden = (field && mod_MCOL_dict.cols_hidden.includes(field));
                    const tBody = (is_hidden) ? el_MCOL_tblBody_available : el_MCOL_tblBody_show;

// +++ insert tblRow into tBody
                    const tblRow = tBody.insertRow(-1);
                    tblRow.setAttribute("data-field", field);
                    tblRow.addEventListener("click", function() {MCOL_SelectItem(tblRow);}, false )
    //- add hover to tableBody row
                    add_hover(tblRow)
    // - insert td into tblRow
                    const td = tblRow.insertCell(-1);
                    td.innerText = caption;
                    td.classList.add("tw_240")
                }
            }
        }
    } // t_MCOL_FillSelectTable

//=========  MCOL_SelectItem  ================ PR2021-07-07
    function MCOL_SelectItem(tr_clicked) {
        //console.log("===  MCOL_SelectItem == ");

        const field_name = get_attr_from_el(tr_clicked, "data-field")
        const is_hidden = (field_name && mod_MCOL_dict.cols_hidden.includes(field_name));
        if (is_hidden){
            b_remove_item_from_array(mod_MCOL_dict.cols_hidden, field_name);
        } else {
            mod_MCOL_dict.cols_hidden.push(field_name)
        }
        t_MCOL_FillSelectTable();
        // enable save btn
        const el_MCOL_btn_save = document.getElementById("id_MCOL_btn_save")
        el_MCOL_btn_save.disabled = false;

    }  // MCOL_SelectItem

// +++++++++++++++++ END OF MODAL SELECT COLUMNS ++++++++++++++++++++++++++++++++++++++++++

// +++++++++++++++++ SBR SELECT LEVEL SECTOR ++++++++++++++++++++++++++++++++++++++++++
//=========  t_SBR_select_and_update_level_sector  ================ PR2021-11-17
    function t_SBR_select_and_update_level_sector(tblName, el_select, Response_from_SBR_select_level_sector) {
        console.log("===== t_SBR_select_and_update_level_sector =====");
        //console.log( "tblName: ", tblName)
        //console.log( "el_select: ", el_select)
        //console.log( "el_select.value: ", el_select.value)

        // function is used in results.js, to test
        // function downloads students again with this filter, stores selected value in usersettings
        //

        const selected_base_pk = (Number(el_select.value)) ? Number(el_select.value) : null;

        Response_from_SBR_select_level_sector(tblName, selected_base_pk);
    }  // t_SBR_select_and_update_level_sector


//=========  t_SBR_select_level_sector  ================ PR2021-08-02
    function t_SBR_select_level_sector(mode, el_select, FillTblRows) {
        //console.log("===== t_SBR_select_level_sector =====");
        //console.log( "mode: ", mode)
        //console.log( "el_select.value: ", el_select.value, typeof el_select.value)
        let upload_dict = {};
        if (mode === "level"){
            setting_dict.sel_lvlbase_pk = (Number(el_select.value)) ? Number(el_select.value) : null;
            setting_dict.sel_level_abbrev = (el_select.options[el_select.selectedIndex]) ? el_select.options[el_select.selectedIndex].text : null;

            upload_dict = {selected_pk: {sel_lvlbase_pk: setting_dict.sel_lvlbase_pk}};
        } else if (mode === "sector"){
            setting_dict.sel_sctbase_pk = (Number(el_select.value)) ? Number(el_select.value) : null;
            setting_dict.sel_sector_abbrev = (el_select.options[el_select.selectedIndex]) ? el_select.options[el_select.selectedIndex].text : null;

            upload_dict = {selected_pk: {sel_sctbase_pk: setting_dict.sel_sctbase_pk}};
        }
        //console.log( "upload_dict.value: ", upload_dict)
// ---  upload new setting
        b_UploadSettings (upload_dict, urls.url_usersetting_upload);
        //UpdateHeaderLeft();

        FillTblRows();
    }  // t_SBR_select_level_sector

//=========  t_SBR_filloptions_level_sector  ================ PR2021-08-02
    function t_SBR_filloptions_level_sector(tblName, rows) {
        //console.log("=== t_SBR_filloptions_level_sector");
        //console.log("tblName", tblName);
        //console.log("rows", rows);

        const display_rows = []
        const has_items = (!!rows && !!rows.length);
        const has_profiel = !!setting_dict.sel_dep_has_profiel;
        const show_select_element = (tblName !== "level" || setting_dict.sel_dep_level_req);

        //console.log("show_select_element", show_select_element);

        const caption_all = "&#60" + ( (tblName === "level") ? loc.All_levels :
                                        (has_profiel) ? loc.All_profielen : loc.All_sectors ) + "&#62";
        if (!has_items){
             const caption_none = (tblName === "level") ? loc.No_level_found :
                                  (has_profiel) ? loc.No_profiel_found : loc.No_sector_found ;
            display_rows.push({value: 0, caption: caption_none})
        } else {
            if (rows.length === 1){
                // if only 1 level: make that the selected one
                if (tblName === "level"){
                    setting_dict.sel_lvlbase_pk = rows.base_id;
                } else if (tblName === "sector"){
                    setting_dict.sel_sctbase_pk = rows.base_id
                }
            } else if (rows.length > 1){
                // add row 'Alle leerwegen' / Alle profielen / Alle sectoren in first row
                display_rows.push({value: 0, caption: caption_all })
            }
            for (let i = 0, row; row = rows[i]; i++) {
                display_rows.push({
                value: row.base_id,
                caption: (tblName === "sector") ? row.name : row.abbrev
                })
            }
        }  // if (!has_items)

        //console.log("display_rows", display_rows);

        const selected_pk = (tblName === "level") ? setting_dict.sel_lvlbase_pk :
                            (tblName === "sector") ? setting_dict.sel_sctbase_pk : 0;
        //console.log("setting_dict", setting_dict);
        //console.log("selected_pk", selected_pk);

        const id_str = (tblName === "level") ? "id_SBR_select_level" :
                        (tblName === "sector") ? "id_SBR_select_sector" : null;
        const el_SBR_select = document.getElementById(id_str)
        t_FillOptionsFromList(el_SBR_select, display_rows, "value", "caption", null, null, selected_pk);

        // put displayed text in setting_dict
        const sel_abbrev = (el_SBR_select.options[el_SBR_select.selectedIndex]) ? el_SBR_select.options[el_SBR_select.selectedIndex].text : null;
        if (tblName === "level"){
            setting_dict.sel_level_abbrev = sel_abbrev;
        } else if (tblName === "sector"){
            setting_dict.sel_sector_abbrev = sel_abbrev;
        }
        //console.log("el_SBR_select.parentNode", el_SBR_select.parentNode);
        add_or_remove_class(el_SBR_select.parentNode, cls_hide, !show_select_element);

        const el_SBR_select_showall = document.getElementById("id_SBR_select_showall")
        add_or_remove_class(el_SBR_select_showall, cls_hide, false);
        // show select level and sector
        if (tblName === "sector"){

            // when label has no id the text is Sector / Profiel, set in .html file
            const el_SBR_select_sector_label = document.getElementById("id_SBR_select_sector_label")
            if(el_SBR_select_sector_label){el_SBR_select_sector_label.innerText = ( (has_profiel) ? loc.Profiel : loc.Sector ) + ":"};
        }


    }  // t_SBR_filloptions_level_sector

//=========  t_SBR_show_all  ================ PR2021-08-02 PR2022-03-03
    function t_SBR_show_all(FillTblRows) {
        //console.log("===== t_SBR_show_all =====");

        setting_dict.sel_depbase_pk = null;
        setting_dict.sel_depbase_code = null;

        setting_dict.sel_lvlbase_pk = null;
        setting_dict.sel_level_abbrev = null;

        setting_dict.sel_sctbase_pk = null;
        setting_dict.sel_sector_abbrev = null;

        setting_dict.sel_subject_pk = null;
        setting_dict.sel_subject_code = null;
        setting_dict.sel_subject_name = null;

        setting_dict.sel_cluster_pk = null;
        setting_dict.sel_cluster_name = null;

        setting_dict.sel_classname = null;

        setting_dict.sel_student_pk = null;
        setting_dict.sel_student_name = null;
        setting_dict.sel_student_name_init = null;

        const el_SBR_select_department = document.getElementById("id_SBR_select_department");
        const el_SBR_select_level = document.getElementById("id_SBR_select_level");
        const el_SBR_select_sector = document.getElementById("id_SBR_select_sector");
        const el_SBR_select_subject = document.getElementById("id_SBR_select_subject");
        const el_SBR_select_cluster = document.getElementById("id_SBR_select_cluster");
        const el_SBR_select_class = document.getElementById("id_SBR_select_class");
        const el_SBR_select_student = document.getElementById("id_SBR_select_student");

        if (el_SBR_select_department){ el_SBR_select_department.value = null};
        if (el_SBR_select_level){ el_SBR_select_level.value = null};
        if (el_SBR_select_sector){ el_SBR_select_sector.value = null};
        if (el_SBR_select_subject){ t_MSSSS_display_in_sbr("subject", null)};
        if (el_SBR_select_cluster){ t_MSSSS_display_in_sbr("cluster", null) };
        if (el_SBR_select_class){ el_SBR_select_class.value = "0"};
        if (el_SBR_select_student){t_MSSSS_display_in_sbr("student", null)};


// ---  upload new setting
        const upload_dict = {selected_pk: {
            sel_depbase_pk: null,
            sel_lvlbase_pk: null,
            sel_sctbase_pk: null,
            sel_classname: null,
            sel_subject_pk: null,
            sel_cluster_pk: null,
            sel_student_pk: null}};
        b_UploadSettings (upload_dict, urls.url_usersetting_upload);

        FillTblRows();
    }  // t_SBR_show_all


// +++++++++++++++++ END OF SBR SELECT LEVEL SECTOR ++++++++++++++++++++++++++++++++++++++++++

//========= t_InputToggle  ============= PR2021-09-03
    function t_InputToggle(el_input){
        //console.log( "===== t_InputToggle  ========= ");
        //console.log( "el_input", el_input);
        if (el_input){
            const data_value = get_attr_from_el(el_input, "data-value")
            const new_data_value = (data_value === "1") ? "0" : "1";
            el_input.setAttribute("data-value", new_data_value);
        //console.log( "el_input.children[0]", el_input.children[0]);
            add_or_remove_class(el_input.children[0], "tickmark_2_2", new_data_value === "1", "tickmark_1_1")
        };
    }; // t_InputToggle