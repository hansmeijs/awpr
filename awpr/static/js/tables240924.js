
// ---  dictionaries to store info of modal forms
    let mod_MSESD_dict = {};
    let mod_MUPS_dict = {};  // PR2022-10-23
    const mod_MSSSS_dict = {};  // PR2023-03-20
    const mod_MCL_dict = {};  // modal cluster  PR2024-04-02 moved to table.js

// ++++++++++++  TABLE  +++++++++++++++++++++++++++++++++++++++
    "use strict";

// ++++++++++++  MODAL SELECT DEPARTMENT from rows  PR2022-11-05

//=========  t_MSED_OpenDepLvlFromDictsNIU  ================ PR2023-06-27
    function t_MSED_OpenDepLvlFromDictsNIU(tblName, data_dicts, schoolbase_pk, depbase_pk, MSED_Response) {
        //console.log( "===== t_MSED_OpenDepLvlFromDictsNIU ========= ");
        //console.log( "tblName", tblName);
        //console.log( "data_dicts", data_dicts);
        // only called by  page Home - for now

// set header text
        const el_MSED_header_text = document.getElementById("id_MSED_header_text");
        el_MSED_header_text.innerText = (tblName === "department") ? loc.Select_department :
                                        (tblName === "level") ? loc.Select_level : "---";

// ---  fill select table
        const tblBody_select = document.getElementById("id_MSED_tblBody_select");
        tblBody_select.innerText = null;
// --- loop through data_dicts
        if(data_dicts){
            for (const data_dict of Object.values(data_dicts)) {

        //console.log( "data_dict", data_dict);
                const pk_int = data_dict.base_id;
    // permit_dict.requsr_country_pk
                const display_value = (tblName === "department") ? data_dict.base_code :
                                        (tblName === "level") ? data_dict.name : "---"
                t_MSED_CreateDepRow(tblName, tblBody_select, pk_int, display_value, schoolbase_pk, depbase_pk, MSED_Response)
            };
        };

// ---  show modal
        $("#id_mod_select_examyear_or_depbase").modal({backdrop: true});
    };  // t_MSED_OpenDepLvlFromDictsNIU


// ++++++++++++  MODAL SELECT DEPARTMENT from rows  PR2022-11-05

//=========  t_MSED_OpenDepLvlFromRows  ================ PR2022-11-05
    function t_MSED_OpenDepLvlFromRows(tblName, data_rows, schoolbase_pk, depbase_pk, MSED_DepFromRows_Response) {
        //console.log( "===== t_MSED_OpenDepLvlFromRows ========= ");
        //console.log( "tblName", tblName);
        //console.log( "data_rows", data_rows);
        // only called by user, base, modallowed:  MUPS_SelectDepartment and t_MUPS_SelectLevel - for now

// set header text
        const el_MSED_header_text = document.getElementById("id_MSED_header_text");
        el_MSED_header_text.innerText = (tblName === "department") ? loc.Select_department :
                                        (tblName === "level") ? loc.Select_level : "---";

// ---  fill select table
        const tblBody_select = document.getElementById("id_MSED_tblBody_select");
        tblBody_select.innerText = null;
// --- loop through data_rows
        if(data_rows && data_rows.length){
            for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
        //console.log( "data_dict", data_dict);
                const pk_int = data_dict.base_id;
    // permit_dict.requsr_country_pk
                const display_value = (tblName === "department") ? data_dict.base_code :
                                        (tblName === "level") ? data_dict.name : "---"
                t_MSED_CreateDepRow(tblName, tblBody_select, pk_int, display_value, schoolbase_pk, depbase_pk, MSED_DepFromRows_Response)
            };
        };

// ---  show modal
        $("#id_mod_select_examyear_or_depbase").modal({backdrop: true});
    };  // t_MSED_OpenDepLvlFromRows

//=========  t_MSED_SaveDepFromRows  ================ PR2022-11-05
    function t_MSED_SaveDepFromRows(MSED_Response, tblRow, schoolbase_pk, depbase_pk) {
        //console.log("===  t_MSED_SaveDepFromRows =========");
    // --- put selected_pk_int in MSED_Response,
        const sel_pk_int = get_attr_from_el_int(tblRow, "data-pk");
        MSED_Response(sel_pk_int, schoolbase_pk, depbase_pk);

    // --- hide modal
        $("#id_mod_select_examyear_or_depbase").modal("hide");
    }  // t_MSED_SaveDepFromRows

//=========  t_MSED_CreateDepRow  ================ PR2022-11=05
    function t_MSED_CreateDepRow(tblName, tblBody_select, pk_int, code_value, schoolbase_pk, depbase_pk, MSED_Response) {
        //console.log( "===== t_MSED_CreateDepRow ========= ");
        //console.log( "code_value", code_value);

// ---  insert tblRow  //index -1 results in that the new row will be inserted at the last position.
        let tblRow = tblBody_select.insertRow(-1);
        tblRow.setAttribute("data-table", tblName)
        tblRow.setAttribute("data-pk", pk_int);

        //console.log( "pk_int", pk_int);
// ---  add EventListener to tblRow
        if(pk_int){
            tblRow.addEventListener("click", function() { t_MSED_SaveDepFromRows(MSED_Response, tblRow, schoolbase_pk, depbase_pk) }, false )
// ---  add hover to tblRow
            add_hover(tblRow);
        }
        const col_width = "tw_280"

// --- add a element with code_value to td
        td = tblRow.insertCell(-1);
        el_div = document.createElement("div");
            el_div.innerText = code_value;
            el_div.classList.add(col_width, "px-2")
        td.appendChild(el_div);

    }  // t_MSED_CreateDepRow

// ++++++++++++  MODAL SELECT EXAMYEAR OR DEPARTMENT   +++++++++++++++++++++++++++++++++++++++

//=========  t_MSED_Open  ================
    function t_MSED_Open(loc, tblName, data_map, setting_dict, permit_dict, MSED_Response, all_departments) {
        //PR2020-10-27 PR2020-12-25 PR2021-04-23  PR2021-05-10 PR2022-04-08 PR2023-01-08 PR2023-07-03 PR2024-08-31
        //console.log( "===== t_MSED_Open ========= ", tblName);
        //console.log( "    setting_dict", setting_dict);
        //console.log( "    permit_dict", permit_dict);
        //console.log( "data_map", data_map);
        //console.log( "all_departments", all_departments);
        //console.log( "    tblName", tblName);

        const skip_allowed_filter = (setting_dict && ["page_subject", "page_orderlist", "page_exams", "page_secretexam"].includes(setting_dict.sel_page));

        let may_open_modal = false, selected_pk = null;
        if (tblName === "examyear") {
            // PR2023-01-08 may_select_examyear = true when there are multiple allowed examyears
            may_open_modal = permit_dict.may_select_examyear;
            selected_pk = setting_dict.sel_examyear_pk;

        } else if (tblName === "department") {
            // argument 'all_departments' is used to show all deps in page exam and secret_exam only when used by ETE (requsr_role_admin)
            const allowed_depbases_count = (all_departments && permit_dict.requsr_role_admin) ? data_map.size : (permit_dict.allowed_depbases) ? permit_dict.allowed_depbases.length : 0

    //console.log( "allowed_depbases_count", allowed_depbases_count);
            //PR2023-07-03 may_select_department gets value in get_settings_departmentbase, (allowed_depbases_count > 1) is part of that function
            // was: may_open_modal = (allowed_depbases_count > 1);
            may_open_modal = permit_dict.may_select_department;
            selected_pk = setting_dict.sel_depbase_pk;
         };
    //console.log( "    may_open_modal", may_open_modal);

        //PR2020-10-28 debug: modal gives 'NaN' and 'undefined' when  loc not back from server yet
        if (may_open_modal) {

// set header text
            const el_MSED_header_text = document.getElementById("id_MSED_header_text");
            if (el_MSED_header_text) {
                const header_text = (tblName === "examyear") ? loc.Select_examyear :
                                    (tblName === "department") ? loc.Select_department : null;
        //console.log( "header_text", header_text);
                el_MSED_header_text.innerText = header_text;
            };

// ---  fill select table
            t_MSED_FillSelectRows(skip_allowed_filter, tblName, MSED_Response, selected_pk)
// ---  show modal
            $("#id_mod_select_examyear_or_depbase").modal({backdrop: true});
        };
    };  // t_MSED_Open

//=========  t_MSED_Save  ================ PR2021-05-10 PR2021-08-13 PR2021-09-24
    function t_MSED_Save(MSED_Response, tblRow) {
        //console.log("===  t_MSED_Save =========");

        // PR2024-03-31 only called by t_MSED_CreateSelectRowNew and t_MSED_CreateSelectRow_NIU

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

            //'argument 'all_countries' also used to show all deps in page exam, only when used by ETE (requsr_role_admin)
            // instead:
            // PR2023-03-04 debug: when sel_schoolbase_pk is a vsbo school, the selected dep will go to vsbo
            // solved by resetting sel_schoolbase_pk to null,
            // was:
            // PR2022-04-11 debug: ETE cannot change to all deps in exam page because sel_school is set to school with 1 dep
            // therefore must set sel_school = requsr_schoolbase_pk when all_countries = true
            // make sure that ETE school has all deps
            // was: if (all_countries){new_setting.sel_schoolbase_pk = permit_dict.requsr_schoolbase_pk;};

            new_setting.sel_schoolbase_pk = null;

            // was: if (all_countries){new_setting.sel_schoolbase_pk = permit_dict.requsr_schoolbase_pk;};

            // PR2022-01-08 debug: set level, sector, subject and student null when changing depbase
            new_setting.sel_lvlbase_pk = null;
            new_setting.sel_sctbase_pk = null;

            // also reset setting_dict - setting_dict must be a global variable;
            setting_dict.sel_lvlbase_pk = null;
            setting_dict.sel_lvlbase_code = null;
            setting_dict.sel_sctbase_pk = null;
            setting_dict.sel_sctbase_code = null;

            //PR2023-07-04 debug: must also reset subject
            setting_dict.sel_subjbase_code = null;
            setting_dict.sel_subjbase_pk = null;
            setting_dict.sel_subject_name = null;
            setting_dict.sel_subject_pk = null;

        };
        // always reset student and subject when changing dep or ey
        new_setting.sel_student_pk = null;

        setting_dict.sel_student_pk = null;
        setting_dict.sel_student_name = null;
        setting_dict.sel_student_name_init = null;

        new_setting.sel_subject_pk = null;
        setting_dict.sel_subject_pk = null;
        setting_dict.sel_subjbase_code = null;
        setting_dict.sel_subject_name = null;

        //console.log("new_setting", new_setting);
        MSED_Response(new_setting)

// hide modal
        $("#id_mod_select_examyear_or_depbase").modal("hide");

    }  // t_MMSED_Save

//=========  t_MSED_FillSelectRows  ================
//  PR2022-08-02 PR2023-01-08 PR2023-06-14
    function t_MSED_FillSelectRows(skip_allowed_filter, tblName, MSED_Response, selected_pk) {
        //console.log( "===== t_MSED_FillSelectRows ========= ");
        //console.log( "tblName", tblName);
        //console.log( "skip_allowed_filter", skip_allowed_filter);
        //console.log( "permit_dict", permit_dict);

        const tblBody_select = document.getElementById("id_MSED_tblBody_select");
    //console.log( "tblBody_select", tblBody_select);
        if (tblBody_select){
            tblBody_select.innerText = null;
            const data_rows = (tblName === "examyear") ? examyear_rows :
                              (tblName === "department") ? department_rows : null;
    //console.log( "    data_rows", data_rows);

    // --- loop through data_rows
            if(data_rows && data_rows.length){
                // PR2022-04-19 Sentry Error: Expected identifier
                // don't know why. Added: && data_rows.size to if clause

                for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
                    const pk_int = (tblName === "examyear") ? data_dict.id :
                                   (tblName === "department") ? data_dict.base_id : null;

        // permit_dict.requsr_country_pk
                    const is_locked = (data_dict && data_dict.examyear_locked);
                    const code_value = (tblName === "examyear") ? (data_dict.examyear_code) ? data_dict.examyear_code : "---" :
                                    (tblName === "department") ? (data_dict.base_code) ? data_dict.base_code : "---" : "---";

    //console.log( "    data_dict", data_dict);
    //console.log( "    code_value", code_value);
    //console.log( "    is_locked", is_locked);
                    let skip_row = false;
                    if(tblName === "examyear") {
                        skip_row = (permit_dict.requsr_country_pk !== data_dict.country_id);
                    } else if(tblName === "department"){
                        if (!skip_allowed_filter){
                            // all_countries is only used in exams.js
                            // all_countries = true, used to let ETE select all deps, schools must only be able to select their deps
                            if (permit_dict.allowed_depbases && permit_dict.allowed_depbases.length){
                                skip_row = !permit_dict.allowed_depbases.includes(pk_int);
                            } else {
                                // must set skip_row = false when allowed_depbases = []? Don't know, it seems to be OK like this
                                skip_row = true;
                            };
                        };
                    };
    //console.log( "permit_dict.allowed_depbases", permit_dict.allowed_depbases);
    //console.log( "skip_row", skip_row);
                    if(!skip_row){
                        t_MSED_CreateSelectRowNew(tblName, tblBody_select, pk_int, code_value, is_locked, MSED_Response, selected_pk)
                    };
                };
            };  // if(!!data_map)
            const row_count = (tblBody_select.rows) ? tblBody_select.rows.length : 0;
            if(!row_count){
                const caption_none = (tblName === "examyear") ? loc.No_examyears :
                                     (tblName === "department") ? loc.No_departments : null;
                t_MSED_CreateSelectRowNew(tblName, tblBody_select, null, caption_none, false, MSED_Response, null)
            };
        };
    };  // t_MSED_FillSelectRows

//=========  t_MSED_CreateSelectRowNew  ================ PR2020-10-27 PR2020-12-18 PR2021-05-10 PR2021-09-24 PR2022-08-02
    function t_MSED_CreateSelectRowNew(tblName, tblBody_select, pk_int, code_value, is_locked, MSED_Response, selected_pk) {
        //console.log( "===== t_MSED_CreateSelectRowNew ========= ");
        //console.log( "    code_value", code_value);
        //console.log( "    is_locked", is_locked);
        //console.log( "    tblName", tblName);

        const is_selected_pk = (selected_pk != null && pk_int === selected_pk)

// ---  insert tblRow  //index -1 results in that the new row will be inserted at the last position.
        // PR2023-06-07 order examyears descending
        const insert_index = (tblName === "examyear") ? 0 : -1;
        const tblRow = tblBody_select.insertRow(insert_index);
        tblRow.setAttribute("data-table", tblName)
        tblRow.setAttribute("data-pk", pk_int);

// ---  add EventListener to tblRow
        if(pk_int){
            tblRow.addEventListener("click", function() { t_MSED_Save(MSED_Response, tblRow) }, false )
// ---  add hover to tblRow
            add_hover(tblRow);
// ---  highlight clicked row
            if (is_selected_pk){ tblRow.classList.add(cls_selected)}
        }
        const col_width = "tw_150"

// --- add a element with code_value to td
        td = tblRow.insertCell(-1);
        el_div = document.createElement("div");
            el_div.innerText = code_value;
            el_div.classList.add(col_width, "px-2")
        td.appendChild(el_div);

// --- add td to tblRow with icon locked.
        if  (tblName === "examyear") {
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                const class_locked = (is_locked) ? "appr_2_6" :  "appr_0_0";
                el_div.classList.add("tw_032", class_locked)
                tblRow.title = (is_locked) ? loc.This_examyear + loc.is_locked : "";
            td.appendChild(el_div);
        }
    }  // t_MSED_CreateSelectRowNew

//=========  t_MSED_CreateSelectRow_NIU  ================ PR2020-10-27 PR2020-12-18 PR2021-05-10 PR2021-09-24
    function t_MSED_CreateSelectRow_NIU(loc, tblName, tblBody_select, pk_int, code_value, country, all_countries, activated, locked, MSED_Response, selected_pk) {
        //console.log( "===== t_MSED_CreateSelectRow_NIU ========= ");

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
    }  // t_MSED_CreateSelectRow_NIU

// ++++++++++++  END OF MODAL SELECT EXAMYEAR OR DEPARTMENT   +++++++++++++++++++++++++++++++++++++++

// +++++++++++++++++ MODAL SELECT SCHOOL SUBJECT CLUSTR STUDENT CLUSTER ++++++++++++++++++++++++++++++++
//PR2023-01-05 new approach: use data_dicts instead of data_rows

//========= t_MSSSS_Open_NEW ====================================
    function t_MSSSS_Open_NEW (modalName, tblName, data_dicts, MSSSS_Response, add_all, show_delete_btn) {
        //PR2022-08-13 PR2023-01-05 PR2023-03-20 PR2024-03-28
        console.log(" ===  t_MSSSS_Open_NEW  =====") ;
    console.log( "    permit_dict", permit_dict);
    console.log( "    setting_dict", setting_dict);
    console.log( "modalName", modalName );
    console.log( "tblName", tblName );
    console.log( "data_dicts", data_dicts, typeof data_dicts );

        // tblNames are: 'cluster', 'subject',  // tobe added:  "school", "student", "envelopbundle"
        // table "school", "student" use base_id as selected_pk

        // PR2024-03-28 use 'sel_subjbase_pk ' instead of 'sel_subject_pk
         // note: tblName = 'subject', not 'subjbase''used in grades el_SBR_select_subject

        // PR2024-03-27 called in page / function:
        // - exams.js:  MDEC_BtnSelectSubjectClick and MEXQ_BtnSelectSubjectClick(el)
        // - wolf, grades, studentsubject:  el_SBR_select_cluster.addEventListener

        // PR2024-03-26 debug: Ancilla Domini Yolande van Erven: teacher cannot see grades
        // becasue subject filter was still pointed at subject_pk of previous year
        // solve by using sel_subjbase_pk instead

        // PR2024-03-27 debug:  instead of using sel_subject_pk, must use sel_subjbase_pk
        //

        // PR2023-03-20 mod_MSSSS_dict added to store data_dicts, to return selected data_dict on save
        b_clear_dict(mod_MSSSS_dict);

        // PR024-04-02 modalName is used in exams.js, to make difference between MSSS and MEX response
        // modalName "sbr": update setting_dict and sidebar,
        // modalName "mex" : select subject for ete exam,
        // modalName "mdec": select subject for duo (cvte) exam,
        // modalName "hdr", "mcl", "mups" "envbndl" are not used in t_MSSSS_

        mod_MSSSS_dict.modalName = modalName;
        mod_MSSSS_dict.tblName = tblName;
        mod_MSSSS_dict.data_dicts = data_dicts;

        // PR2021-04-27 debug: opening modal before loc and setting_dict are loaded gives 'NaN' on modal.
        // allow opening only when loc has value
        if(!isEmpty(permit_dict)){
            const may_select = (tblName === "school") ? permit_dict.may_select_school : true;
    //console.log( "may_select", may_select);
            if (may_select){
                mod_MSSSS_dict.selected_pk = (tblName === "school") ? setting_dict.sel_school_pk :
                    (tblName === "subject") ? setting_dict.sel_subjbase_pk : // PR2024-03-28 added
                    (tblName === "cluster") ? setting_dict.sel_cluster_pk :
                    (tblName === "student") ? setting_dict.sel_student_pk :
                    (tblName === "envelopbundle") ? setting_dict.envelopbundle_pk : null;

                //PR2024-04-01 added, to keep or remove cluster when subjbase changes
                mod_MSSSS_dict.sel_subjbase_pk = setting_dict.sel_subjbase_pk;
                mod_MSSSS_dict.sel_cluster_pk = setting_dict.sel_cluster_pk;
                mod_MSSSS_dict.sel_student_pk = setting_dict.sel_student_pk;

                // PR2022-05-01 dont open modal when only 1 item in data_rows
                // PR2022-05-25 is confusing when modal doesn't open, > 1 removed
                //if (data_rows && data_rows.length > 1){

                if (isEmpty(data_dicts)){
                    const msg_html = (tblName === "school") ? loc.No_schools :
                        (tblName === "subject") ? loc.No_subjects_found :
                        (tblName === "student") ? loc.No_candidates :
                        (tblName === "envelopbundle") ? loc.No_bundles :
                        (tblName === "cluster") ? ["<p>", loc.No_clusters, "</p><p>", loc.Goto_subjects_to_create, "</p>"].join("")
                            : null;
                    b_show_mod_message_html(msg_html);
                } else {
        // --- fill select table
    //console.log( "    fill select table" );
                    t_MSSSS_Fill_SelectTable_NEW(loc, modalName, tblName, data_dicts, MSSSS_Response, add_all)

                    const el_MSSSS_input = document.getElementById("id_MSSSS_input")
                    el_MSSSS_input.value = null;

            // ---  set focus to input element
                    set_focus_on_el_with_timeout(el_MSSSS_input, 50);

            // ---  show delete btn, only in page orderlist when select bundle
                    const show_btn = show_delete_btn && mod_MSSSS_dict.selected_pk;
                    const el_MSSSS_btn_delete = document.getElementById("id_MSSSS_btn_delete");
                    const caption = (tblName === "envelopbundle") ? loc.Remove_bundle : loc.Delete;
                    el_MSSSS_btn_delete.innerText = caption;
                    add_or_remove_class(el_MSSSS_btn_delete, cls_hide, !show_btn )

            // ---  disable save button when no item selected
                    const el_MSSSS_btn_save = document.getElementById("id_MSSSS_btn_save");
                    el_MSSSS_btn_save.disabled = !mod_MSSSS_dict.selected_pk;

            // ---  show modal
                     $("#id_mod_select_school_subject_student").modal({backdrop: true});
                 };
             };
         };
    }; // t_MSSSS_Open_NEW

//=========  t_MSSSS_Save_NEW  ================ PR2020-01-29 PR2021-01-23 PR2022-02-26 PR2022-10-26 PR2023-01-05 PR2024-05-02
    function t_MSSSS_Save_NEW(MSSSS_Response) {
        console.log("=====  t_MSSSS_Save_NEW =========");
    // --- put tblName, sel_pk and value in MSSSS_Response, MSSSS_Response handles uploading

        const tblName = mod_MSSSS_dict.tblName;
        const modalName = mod_MSSSS_dict.modalName;

        // Note: when tblName = school: pk_int = schoolbase_pk
        // PR2024-03-28: when tblName = subjbase: pk_int = subjbase_pk
        const selected_pk_int = mod_MSSSS_dict.selected_pk;
        const selected_code = mod_MSSSS_dict.data_code;
        const selected_name = mod_MSSSS_dict.data_name;

    console.log( "   modalName", modalName );
    console.log("    tblName", tblName)
    //console.log("    mod_MSSSS_dict", mod_MSSSS_dict)
    console.log("    selected_pk_int", selected_pk_int, typeof selected_pk_int);
    //console.log("    selected_code", selected_code);
    //console.log("    selected_name", selected_name);

// +++ get existing map_dict from data_rows
        // when tblName = school: pk_int = base_pk, therefore can't use b_recursive_integer_lookup PR2022-10-26
        let selected_dict = {};

        if (["school", "subject", "student"].includes(tblName)) {
            const data_rows = (tblName === "school") ? school_rows :
                              (tblName === "subject") ? subject_rows :
                              (tblName === "student") ? student_rows : [];
                              (tblName === "student") ? student_rows : [];
            const pk_key = (tblName === "student") ? "id" : "base_id";

            for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
                if(data_dict[pk_key] === selected_pk_int){
                    selected_dict = data_dict;
                    break;
            }};
        } else {
            const map_id = tblName + "_" + selected_pk_int;
            // PR2024-09-24 was: selected_dict = (!isEmpty(mod_MSSSS_dict.data_dicts) && map_id in mod_MSSSS_dict.data_dicts ) ? mod_MSSSS_dict.data_dicts[map_id] : null;
            selected_dict = t_lookup_row_in_dictlist(mod_MSSSS_dict.data_dicts, "mapid", map_id);

        };
    //console.log("    selected_dict", selected_dict);

        // reset other select elements
        if (tblName === "subject") {
    //console.log("    setting_dict.sel_cluster_pk", setting_dict.sel_cluster_pk);

    // update mod_MSSSS_dict
            mod_MSSSS_dict.sel_subjbase_pk = selected_pk_int;

    // update setting_dict and sidebar, only when modal = sbr
            if (modalName == "sbr"){
                setting_dict.sel_subjbase_pk = selected_pk_int;
                t_MSSSS_display_in_sbr_NEW(tblName);
            };

    // if sel_cluster has value: check if it has the same subject
            if (!isEmpty(selected_dict) && setting_dict.sel_cluster_pk != null) {
                // lookup subjbase_id of selected cluster
                let sel_cluster_subjbase_id = null;
                for (const cluster_dict of Object.values(cluster_dictsNEW)) {
                    if(cluster_dict.id === setting_dict.sel_cluster_pk){
                       sel_cluster_subjbase_id = cluster_dict.subjbase_id;
                       break; // break works with for ... of
                    };
                };
                // if cluster_subjbase different from selected subjbase: reset sel_cluster_pk
                if (sel_cluster_subjbase_id && sel_cluster_subjbase_id !== selected_pk_int){
                    mod_MSSSS_dict.sel_cluster_pk = null;
                    setting_dict.sel_cluster_pk = null;

                    t_MSSSS_display_in_sbr_NEW("cluster");
                };
            };

    // if sel_student_pk has value: check if it has the same subject
            if (!isEmpty(selected_dict) && setting_dict.sel_student_pk != null) {
                // loop through studsubj to check if student has selected subject
                let student_has_this_subject = false;
                for (const studsubj_dict of Object.values(studsubj_dictsNEW)) {
                    if( studsubj_dict.stud_id === setting_dict.sel_student_pk &&
                        studsubj_dict.subjbase_id === selected_pk_int ){
                       student_has_this_subject = true;
                       break; // break works with for ... of
                    };
                };
                // if cluster_subjbase different from selected subjbase: reset sel_cluster_pk
                if (!student_has_this_subject){
                    mod_MSSSS_dict.sel_student_pk = null;
                    setting_dict.sel_student_pk = null;
                    t_MSSSS_display_in_sbr_NEW("student");
                };
            };

        } else if (tblName === "cluster") {
            // PR2024-04-01 don't remove selected subject, slected cluster is always of selected subject

            // update setting_dict and mod_MSSSS_dict
            mod_MSSSS_dict.sel_cluster_pk = selected_pk_int;
            setting_dict.sel_cluster_pk = selected_pk_int;

            t_MSSSS_display_in_sbr_NEW(tblName);

    //if selected student: check if it beongs to sleected cluster, if not: remove selected

    // if sel_student_pk has value: check if itbelongs to this cluster
            if (!isEmpty(selected_dict) && setting_dict.sel_student_pk != null) {
                // loop through studsubj to check if student has selected cluster
                let student_has_this_cluster = false;
                for (const studsubj_dict of Object.values(studsubj_dictsNEW)) {
                    if( studsubj_dict.stud_id === setting_dict.sel_student_pk &&
                        studsubj_dict.cluster_id === selected_pk_int ){
                       student_has_this_cluster = true;
                       break; // break works with for ... of
                    };
                };
                if (!student_has_this_cluster){
                    mod_MSSSS_dict.sel_student_pk = null;
                    setting_dict.sel_student_pk = null;
                    t_MSSSS_display_in_sbr_NEW("student");
                };
            };

        } else if (tblName === "student") {
            // update setting_dict and mod_MSSSS_dict
            mod_MSSSS_dict.sel_student_pk = selected_pk_int;
            setting_dict.sel_student_pk = selected_pk_int;
            t_MSSSS_display_in_sbr_NEW(tblName);

            mod_MSSSS_dict.sel_subjbase_pk = null;
            setting_dict.sel_subjbase_pk = null;
            t_MSSSS_display_in_sbr_NEW("subject");

            mod_MSSSS_dict.sel_cluster_pk = null;
            setting_dict.sel_cluster_pk = null;
            t_MSSSS_display_in_sbr_NEW("cluster");
        };

        MSSSS_Response(modalName, tblName, selected_dict, selected_pk_int);

// hide modal
        $("#id_mod_select_school_subject_student").modal("hide");
    }  // t_MSSSS_Save_NEW

//========= t_MSSSS_Fill_SelectTable_NEW  ============= PR2021-01-23  PR2021-07-23 PR2022-08-12 PR2023-01-05
    function t_MSSSS_Fill_SelectTable_NEW(loc, modalName, tblName, data_dicts, MSSSS_Response, add_all) {
        //console.log("===== t_MSSSS_Fill_SelectTable_NEW ===== ", tblName);
    //console.log("    data_dicts", data_dicts, typeof data_dicts);
    //console.log("    tblName", tblName, typeof tblName);

        const item_txt = (tblName === "cluster") ?  loc.a_cluster :
                     (tblName === "subject") ? loc.a_subject :
                     (tblName === "school") ? loc.a_school :
                     (tblName === "student") ? loc.a_candidate :
                     (tblName === "cluster") ?  loc.a_cluster :
                     (tblName === "envelopbundle") ? loc.a_label_bundle : "";

// set header text and placeholder
        const header_txt = loc.Select + item_txt;
        const placeholder = loc.Type_few_letters_and_select + item_txt + loc.in_the_list;
        document.getElementById("id_MSSSS_header").innerText = header_txt;
        document.getElementById("id_MSSSS_input_label").innerText = header_txt;
        document.getElementById("id_MSSSS_msg_input").innerText = placeholder;

        const tblBody_select = document.getElementById("id_MSSSS_tblBody_select");
        tblBody_select.innerText = null;

// ---  add All to list when multiple subject / students exist
        if(!isEmpty(data_dicts) && add_all){
            const add_all_dict = t_MSSSS_AddAll_dict(tblName);
            t_MSSSS_Create_SelectRow_NEW(loc, modalName, tblName, tblBody_select, add_all_dict, MSSSS_Response)
        };

// ---  loop through data_dicts
        //PR 2021-07-23 was: for (const [map_id, map_dict] of data_map.entries()) {
        //PR 2023-01-05 was: for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
        for (const data_dict of Object.values(data_dicts)) {
            // when filling clusters and a subject is selected: only show clusters of this subject;: PR2023-03-30
            let add_to_list = true;
            // PR2024-03-30 was:
            // if (tblName === "cluster" && setting_dict.sel_subject_pk){
            //    add_to_list = (data_dict.subject_id === setting_dict.sel_subject_pk);
            //};
            if (tblName === "cluster" && setting_dict.sel_subjbase_pk){
                add_to_list = (data_dict.subjbase_id === setting_dict.sel_subjbase_pk);
            };
            if (add_to_list){
                t_MSSSS_Create_SelectRow_NEW(loc, modalName, tblName, tblBody_select, data_dict, MSSSS_Response);
            };
        };
    }; // t_MSSSS_Fill_SelectTable_NEW

//========= t_MSSSS_Create_SelectRow_NEW  ============= PR2020-12-18 PR2020-07-14 PR2023-01-04 PR2024-03-28
    function t_MSSSS_Create_SelectRow_NEW(loc, modalName, tblName, tblBody_select, data_dict, MSSSS_Response) {
         //console.log("===== t_MSSSS_Create_SelectRow_NEW ===== ");
    //console.log("    modalName", modalName);
    //console.log("    tblName", tblName);
    //console.log("    data_dict", data_dict);
    //console.log("    mod_MSSSS_dict", mod_MSSSS_dict);

//--- get info from data_dict
        // when tblName = school: pk_int = schoolbase_pk
        // PR2024-03-28 added: subjbase:  pk_int = subjbase_pk
        const subjbase_key = (["mex", "mdec"].includes(modalName)) ? "subjbase_id" : "base_id";
        const pk_int = (tblName === "school") ? data_dict.base_id :
                    (tblName === "subject") ? data_dict[subjbase_key] :
                    (tblName === "student") ? data_dict.id :
                    (tblName === "cluster") ? data_dict.id :
                    (tblName === "envelopbundle") ? data_dict.id : null;
    //console.log("    pk_int", pk_int);

        const code = (tblName === "school") ? data_dict.sb_code :
                    (tblName === "subject") ? data_dict.code :
                    (tblName === "student") ? data_dict.name_first_init :
                    (tblName === "cluster") ? data_dict.subj_code : "";
                    // code not used in envelopbundle
    //console.log("    code", code);

        const name =  (tblName === "school") ? data_dict.name : // data_dict.abbrev
                    (tblName === "subject") ? data_dict.name_nl :
                    (tblName === "student") ? data_dict.fullname  :
                    (tblName === "cluster") ? data_dict.name :
                    (tblName === "envelopbundle") ? data_dict.name : "";
    //console.log("    name", name);

        const is_selected_row = (!!pk_int && pk_int === mod_MSSSS_dict.selected_pk);

// ---  lookup index where this row must be inserted
        let ob1 = "", ob2 = "", row_index = -1;
        if (tblName === "student"){
            if (data_dict.lastname) { ob1 = data_dict.lastname.toLowerCase()};
            if (data_dict.firstname) { ob2 = data_dict.firstname.toLowerCase()};
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
        } else if(tblName === "envelopbundle"){
            if (name) { ob1 = name.toLowerCase()};
            row_index = b_recursive_tblRow_lookup(tblBody_select, loc.user_lang, ob1);
        }

//--------- insert tblBody_select row at row_index
        const map_id = "sel_" + tblName + "_" + pk_int
        const tblRow = tblBody_select.insertRow(row_index);

        tblRow.id = map_id;
        tblRow.setAttribute("data-pk", pk_int);
        tblRow.setAttribute("data-code", code);
        tblRow.setAttribute("data-name", name);

// ---  add data-sortby attribute to tblRow, for ordering new rows
        tblRow.setAttribute("data-ob1", ob1);
        tblRow.setAttribute("data-ob2", ob2);
        //tblRow.setAttribute("data-ob3", ob3);

        const class_selected = (is_selected_row) ? cls_selected: cls_bc_transparent;
        tblRow.classList.add(class_selected);

//- add hover to select row
        add_hover(tblRow)

// --- add column with 'code'
        let td = null, el_div = null;
        if (["school", "subject", "cluster"].includes(tblName)) {
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                el_div.classList.add("pointer_show")
                el_div.innerText = code;
                el_div.classList.add("tw_075", "px-1")
                td.appendChild(el_div);
            td.classList.add(cls_bc_transparent);
        };

// --- add column with 'name'
        td = tblRow.insertCell(-1);
        el_div = document.createElement("div");
            el_div.classList.add("pointer_show")
            el_div.innerText = name;
            el_div.classList.add("tw_240", "px-1")
            td.appendChild(el_div);
        if (name) { tblRow.title = name};
        td.classList.add(cls_bc_transparent);

// --- add second td to tblRow with icon locked, published or activated.
        if (tblName === "school") {
            const locked = (data_dict.locked) ? data_dict.locked : false;
            const activated = (data_dict.activated) ? data_dict.activated : false;
            td = tblRow.insertCell(-1);
            el_div = document.createElement("div");
                const class_locked = (locked) ? "appr_2_6" : (activated) ? "appr_0_1" : "appr_0_0";
                el_div.classList.add("tw_032", class_locked)
                el_div.title = (locked) ? loc.This_school + loc.is_locked : (activated) ? loc.This_school + loc.is_activated : "";
            td.appendChild(el_div);
        };
//--------- add addEventListener
        tblRow.addEventListener("click", function() {t_MSSSS_SelectItem_NEW(tblRow, MSSSS_Response)}, false);
    }; // t_MSSSS_Create_SelectRow_NEW

//=========  t_MSSSS_SelectItem_NEW  ================ PR2020-12-17 PR2023-01-05 PR2024-03-30
    function t_MSSSS_SelectItem_NEW(tblRow, MSSSS_Response) {
        //console.log( "===== t_MSSSS_SelectItem_NEW ========= ");

        // all data attributes are now in tblRow, not in el_select = tblRow.cells[0].children[0];
        // after selecting row, values are stored in mod_MSSSS_dict

// ---  get clicked tablerow
        if(tblRow) {

// ---  deselect all highlighted rows
            DeselectHighlightedRows(tblRow, cls_selected)
// ---  highlight clicked row
            tblRow.classList.add(cls_selected)

// ---  get pk code and value from tblRow, put values in mod_MSSSS_dict
            // PR2024-03-30 don't use get_attr_from_el_int(tblRow, "data-pk"), it converts null to 0
            mod_MSSSS_dict.selected_pk = (tblRow.dataset.pk) ? parseInt(tblRow.dataset.pk, 10) : null;
            mod_MSSSS_dict.data_code = get_attr_from_el(tblRow, "data-code")
            mod_MSSSS_dict.data_name = get_attr_from_el(tblRow, "data-name")

// enable and set focus to save button
            t_MSSSS_Save_NEW(MSSSS_Response) ;
            //const el_MSSSS_btn_save = document.getElementById("id_MSSSS_btn_save");
            //el_MSSSS_btn_save.disabled = false;
            //set_focus_on_el_with_timeout(el_MSSSS_btn_save, 150);
        };
    };  // t_MSSSS_SelectItem_NEW

    //=========  t_MSSSS_InputKeyup_NEW  ================ PR2020-09-19  PR2021-07-14 PR2024-03-30
    function t_MSSSS_InputKeyup_NEW(el_input) {
        //console.log( "===== t_MSSSS_InputKeyup  ========= ");

// ---  get value of new_filter
        let new_filter = el_input.value

        const el_MSSSS_tblBody = document.getElementById("id_MSSSS_tblBody_select");
        let tblBody = el_MSSSS_tblBody;
        const len = tblBody.rows.length;
    //console.log( "    len", len);
        if (len){
// ---  filter rows in table select_employee
            const filter_dict = t_Filter_SelectRows(tblBody, new_filter);
    //console.log( "    filter_dict", filter_dict);

// ---  if filter results have only one item: put selected item in el_input
            /*
            filter_dict =
                row_count: 1,
                selected_code: "bi",
                selected_innertext: ["Biologie"],
                selected_name: "Biologie",
                selected_pk: "123",
                selected_rowid: "sel_subjbase_123"
            */
            const selected_pk = (filter_dict.selected_pk) ? filter_dict.selected_pk : null;
    //console.log( "    filter_dict.selected_pk", filter_dict.selected_pk);
            if (filter_dict.selected_pk) {
                mod_MSSSS_dict.selected_pk = (filter_dict.selected_pk) ? filter_dict.selected_pk : null;
// ---  get pk code and value from filter_dict, put values in input box
                mod_MSSSS_dict.data_code = (filter_dict.selected_code) ? filter_dict.selected_code : null;
                mod_MSSSS_dict.data_name = (filter_dict.selected_name) ? filter_dict.selected_name : null;

    //console.log( "    mod_MSSSS_dict.selected_pk", mod_MSSSS_dict.selected_pk);
    //console.log( "    mod_MSSSS_dict", mod_MSSSS_dict);
                el_input.value = mod_MSSSS_dict.data_name;

                const selected_row = document.getElementById(filter_dict.selected_rowid);
// ---  deselect all highlighted rows
                DeselectHighlightedRows(selected_row, cls_selected)
// ---  highlight clicked row
                selected_row.classList.add(cls_selected)

// enable and set focus to save button
                const el_btn_save = document.getElementById("id_MSSSS_btn_save");
                el_btn_save.disabled = false;
                set_focus_on_el_with_timeout(el_btn_save, 150);
            };
        };
    }; // t_MSSSS_InputKeyup_NEW

//========= t_MSSSS_display_in_sbr_NEW  ====================================
    function t_MSSSS_display_in_sbr_NEW(tblName) {
        // PR2024-04-01
        //console.log( "===== t_MSSSS_display_in_sbr_NEW  ========= ");
    //console.log( "    tblName", tblName);

        // Note: there is no select school element in sidebar
        const el_SBR_select_id = (tblName === "student") ? "id_SBR_select_student" :
                                 (tblName === "subject") ? "id_SBR_select_subject" :
                                 (tblName === "cluster") ? "id_SBR_select_cluster" : "xxxxx";
        const el_SBR_select = document.getElementById(el_SBR_select_id);

        // PR2022-01-11 debug: skip when el_SBR not defined
        if (el_SBR_select) {

        // Note: there is no select school element in sidebar
            let selected_pk_int = (tblName === "subject") ? setting_dict.sel_subjbase_pk :
                                    (tblName === "cluster") ? setting_dict.sel_cluster_pk :
                                    (tblName === "student") ? setting_dict.sel_student_pk : null;

    //console.log( "    selected_pk_int", selected_pk_int);
            const data_rows = (tblName === "subject") ? subject_rows :
                              (tblName === "cluster") ? cluster_dictsNEW :
                              (tblName === "student") ? student_rows :
                              null;

    // PR2024-06-18 to prevent empty list: check if selected_pk is in rows, set null if not found
            if (selected_pk_int){
                const lookup_field = (tblName === "subject") ? "base_id" : "id";
                const row = t_lookup_row_in_dictlist(data_rows, lookup_field, selected_pk_int);
                if(!row){
                    selected_pk_int = null;
                    const upload_pk_dict = {};
                    if (tblName === "subject") {
                        setting_dict.sel_subjbase_id = null;
                        upload_pk_dict.sel_subjbase_pk = null;
                    } else if  (tblName === "cluster") {
                        setting_dict.sel_cluster_id = null;
                        upload_pk_dict.sel_cluster_pk = null;
                    } else if (tblName === "student") {
                        setting_dict.sel_student_id = null;
                        upload_pk_dict.sel_student_pk = null;
                    };
            // ---  upload new setting
                    const upload_dict = {selected_pk: upload_pk_dict};
                    b_UploadSettings (upload_dict, urls.url_usersetting_upload);
                };
            };

            // PR2024-0-01 Object.keys.length works with lists and dictionaries
            const data_rows_length = (data_rows) ? Object.keys(data_rows).length : 0;
    //console.log( "    data_rows", data_rows);
    //console.log( "    data_rows_length", data_rows_length);
            let display_txt = null;
            const is_disabled = !data_rows_length;
            if (is_disabled) {
                display_txt = t_MSSSS_NoItems_txt(tblName);
            } else {
                // selected_pk_int = -1 when clicked on All
                if(selected_pk_int > 0){
                    // display selected item
                    const lookup_key = (tblName === "subject") ? "base_id" : "id";
                    let selected_dict = null;
                    // ---  loop through data_rows
                    for (const data_dict of Object.values(data_rows)) {
                        if(data_dict[lookup_key] === selected_pk_int){
                            selected_dict = data_dict;
                            break;
                        };
                    };
    //console.log( "    selected_dict", selected_dict);
                    display_txt = t_MSSSS_get_display_text(tblName, selected_dict);

                } else {
                    // display 'All' when no item selected
                    //PR2024-04-01 was: display item when there is only one. Don't, to show if any selected
                    display_txt = t_MSSSS_AddAll_txt(tblName);
                };
            };

    //console.log( "    display_txt", display_txt);
    //console.log( " ?????????   is_disabled", is_disabled);
            el_SBR_select.value = display_txt;
            add_or_remove_class(el_SBR_select.parentNode, cls_hide, false);

            el_SBR_select.disabled = is_disabled;

            const el_SBR_container_showall = document.getElementById("id_SBR_container_showall");
            add_or_remove_class(el_SBR_container_showall, cls_hide, false);
        };
    }; // t_MSSSS_display_in_sbr_NEW

    function t_SBR_display_subject_cluster_student() {
        //console.log("===== t_SBR_display_subject_cluster_student =====");
        t_MSSSS_display_in_sbr_NEW("subject");
        t_MSSSS_display_in_sbr_NEW("cluster");
        t_MSSSS_display_in_sbr_NEW("student");

        // hide itemcount, will be shwon after filling table
        t_set_sbr_itemcount_txt(loc, 0)

    };  // t_SBR_display_subject_cluster_student

// +++++++++++++++++ MODAL SELECT SCHOOL SUBJECT STUDENT ++++++++++++++++++++++++++++++++
//========= t_MSSSS_Open ====================================  PR2020-12-17 PR2021-01-23 PR2021-04-23 PR2021-07-23 PR2022-08-13
    function t_MSSSS_Open(loc, tblName, data_rows, add_all, show_delete_btn, setting_dict, permit_dict, MSSSS_Response) {
        //console.log(" ===  t_MSSSS_Open  =====", tblName) ;
    //console.log( "    permit_dict", permit_dict);
    //console.log( "tblName", tblName );
    //console.log( "data_rows", data_rows, typeof data_rows );
        // tblNames are: "school", "subject", "student", "envelopbundle
        // table "school", "student" use base_id as selected_pk

        // PR2021-04-27 debug: opening modal before loc and setting_dict are loaded gives 'NaN' on modal.
        // allow opening only when loc has value

        if(!isEmpty(permit_dict)){
            const may_select = (tblName === "school") ? !!permit_dict.may_select_school : true;
    //console.log( "    may_select", may_select);
            if (may_select){
                const selected_pk = (tblName === "school") ? setting_dict.sel_school_pk :
                                   (tblName === "subject") ? setting_dict.sel_subject_pk :
                                   (tblName === "student") ? setting_dict.sel_student_pk :
                                   (tblName === "envelopbundle") ? setting_dict.envelopbundle_pk : null;
    //console.log( "setting_dict", setting_dict );
    //console.log( "selected_pk", selected_pk, typeof selected_pk );
                const el_MSSSS_input = document.getElementById("id_MSSSS_input")
                el_MSSSS_input.setAttribute("data-table", tblName);
    //console.log( "el_MSSSS_input", el_MSSSS_input);

                // PR2022-05-01 dont open modal when only 1 item in data_rows
                // PR2022-05-25 is confusing when modal doesn't open, > 1 removed
                //if (data_rows && data_rows.length > 1){

    //console.log( "    data_rows", data_rows);
                if (data_rows && data_rows.length){
        // --- fill select table
    //console.log( "fill select table" );
                    t_MSSSS_Fill_SelectTable(loc, tblName, data_rows, setting_dict, el_MSSSS_input, MSSSS_Response, selected_pk, add_all)
                    el_MSSSS_input.value = null;
            // ---  set focus to input element
                    set_focus_on_el_with_timeout(el_MSSSS_input, 50);

            // ---  show delete btn, only in page orderlist when select bundle
                    const show_btn = show_delete_btn && selected_pk;
                    const el_MSSSS_btn_delete = document.getElementById("id_MSSSS_btn_delete");
                    const caption = (tblName === "envelopbundle") ? loc.Remove_bundle : loc.Delete;
                    el_MSSSS_btn_delete.innerText = caption;
                    add_or_remove_class(el_MSSSS_btn_delete, cls_hide, !show_btn);

            // ---  show modal
                     $("#id_mod_select_school_subject_student").modal({backdrop: true});
                 };
             };
         };
    }; // t_MSSSS_Open

//=========  t_MSSSS_Save  ================ PR2020-01-29 PR2021-01-23 PR2022-02-26 PR2022-10-26
    function t_MSSSS_SaveNIU(el_input, MSSSS_Response) {
        //console.log("=====  t_MSSSS_Save =========");
        //console.log("    el_input", el_input);
        //console.log("    MSSSS_Response", MSSSS_Response);

        // argument MSSS_Response gets value in - for instance - addEventListener("click", function() {t_MSSSS_Open(loc, "student", student_rows, add_all, false, setting_dict, permit_dict, MSSSubjStud_Response)}, false);

        // PR2024-04-01 TODO function to be deprecated

        // function is only called by el_MSSSS_input.addEventListener in page correctros, mailbox , users

    // --- put tblName, sel_pk and value in MSSSS_Response, MSSSS_Response handles uploading
    // function

        const tblName = get_attr_from_el(el_input, "data-table");
        //console.log("    tblName", tblName);

        // Note: when tblName = school: pk_int = schoolbase_pk
        // Note: when tblName = subject: pk_int = subject_pk
        const selected_pk_int = get_attr_from_el_int(el_input, "data-pk");
        const selected_code = get_attr_from_el(el_input, "data-code");
        const selected_name = get_attr_from_el(el_input, "data-name");

    //console.log("    tblName", tblName);
    //console.log("    selected_pk_int", selected_pk_int);
    //console.log("    selected_code", selected_code);
    //console.log("    selected_name", selected_name);

// +++ get existing map_dict from data_rows
        // when tblName = school: pk_int = base_pk, therefore can't use b_recursive_integer_lookup PR2022-10-26
        let selected_dict = {};
        if (tblName === "school") {
            for (let i = 0, data_dict; data_dict = school_rows[i]; i++) {
                if(data_dict.base_id === selected_pk_int){
                    selected_dict = data_dict;
                    break;
            }};
        } else {
            const data_rows =(tblName === "subject") ? (subject_rows) ? subject_rows : [] :
                            (tblName === "cluster") ? (cluster_rows) ? cluster_rows : [] :
                            (tblName === "student") ? (student_rows) ? student_rows : [] :
                            (tblName === "envelopbundle") ? (envelopbundle_rows)  ? envelopbundle_rows : [] : [];
            const [index, found_dict, compare] = b_recursive_integer_lookup(data_rows, "id", selected_pk_int);
    //console.log("    data_rows", data_rows);
    //console.log("    selected_pk_int", selected_pk_int, typeof selected_pk_int);
    //console.log( "    found_dict", found_dict);
            selected_dict = (!isEmpty(found_dict)) ? found_dict : null;
        };

    //console.log("    selected_pk_int", selected_pk_int);
    //console.log("    selected_code", selected_code);
    //console.log("    selected_name", selected_name);
    //console.log( "    selected_dict", selected_dict);
    //console.log( "    tblName", tblName);

        t_MSSSS_display_in_sbr_NEW(tblName, selected_pk_int);

        // reset other select elements
        if (tblName === "subject") {
            mod_MSSSS_dict.sel_cluster_pk = null;
            setting_dict.sel_cluster_pk = null;
            t_MSSSS_display_in_sbr_NEW("cluster");

            mod_MSSSS_dict.sel_student_pk = null;
            setting_dict.sel_student_pk = null;
            t_MSSSS_display_in_sbr_NEW("student");

        } else if (tblName === "cluster") {
            mod_MSSSS_dict.sel_subjbase_pk = null;
            setting_dict.sel_subjbase_pk = null;
            t_MSSSS_display_in_sbr_NEW("subject");

            mod_MSSSS_dict.sel_student_pk = null;
            setting_dict.sel_student_pk = null;
            t_MSSSS_display_in_sbr_NEW("student");

        } else if (tblName === "student") {
            mod_MSSSS_dict.sel_subjbase_pk = null;
            setting_dict.sel_subjbase_pk = null;
            t_MSSSS_display_in_sbr_NEW("subject");

            mod_MSSSS_dict.sel_cluster_pk = null;
            setting_dict.sel_cluster_pk = null;
            t_MSSSS_display_in_sbr_NEW("cluster");
        };

        MSSSS_Response(modalName, tblName, selected_dict, selected_pk_int);
// hide modal
        $("#id_mod_select_school_subject_student").modal("hide");
    }  // t_MSSSS_Save

//========= t_MSSSS_Fill_SelectTable  ============= PR2021-01-23  PR2021-07-23 PR2022-08-12
    function t_MSSSS_Fill_SelectTableNIU(loc, tblName, data_rows, setting_dict, el_input, MSSSS_Response, selected_pk, add_all) {
        //console.log("===== t_MSSSS_Fill_SelectTable ===== ", tblName);
        //console.log("    data_rows", data_rows, typeof data_rows);
        //console.log("    tblName", tblName, typeof tblName);

// set header text
        const label_text = loc.Select + ((tblName === "school") ?  loc.a_school :
                                    (tblName === "student") ?  loc.a_candidate :
                                    (tblName === "subject") ?  loc.a_subject :
                                    (tblName === "cluster") ?  loc.a_cluster :
                                    (tblName === "envelopbundle") ?  loc.a_label_bundle : ""
                                  );

        const item = (tblName === "school") ? loc.a_school :
                     (tblName === "student") ? loc.a_candidate :
                     (tblName === "subject") ? loc.a_subject :
                     (tblName === "cluster") ?  loc.a_cluster :

                     (tblName === "envelopbundle") ? loc.a_label_bundle : "";
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
        for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
            t_MSSSS_Create_SelectRow(loc, tblName, tblBody_select, data_dict, selected_pk, el_input, MSSSS_Response);
        }
    } // t_MSSSS_Fill_SelectTable

    function t_MSSSS_AddAll_txt(tblName){
        //PR2022-06-27 Sentry debug: undefined is not an object (evaluating 'loc.Subjects.toLowerCase')
        // added : (loc.Subjects) ? ...  instead of: (tblName === "subject") ? loc.Subjects.toLowerCase() :
        const caption = (tblName === "student") ? (loc.Candidates) ? loc.Candidates.toLowerCase() : "" :
                        // PR2024-03-28 subjbase added
                        (tblName === "subject") ? (loc.Subjects) ? loc.Subjects.toLowerCase() : "" :
                        (tblName === "cluster") ? (loc.Clusters) ? loc.Clusters.toLowerCase() : "" :
                        (tblName === "school") ? (loc.Schools) ? loc.Schools.toLowerCase() : "" : "";
        return "<" + loc.All_ + caption + ">";
    }

    function t_MSSSS_NoItems_txt(tblName){
        // PR2022-05-01
        const caption = (tblName === "student") ? (loc.Candidates) ? loc.Candidates.toLowerCase() : "" :
                        (tblName === "subject") ? (loc.Subjects) ? loc.Subjects.toLowerCase() : "" :
                        (tblName === "cluster") ? (loc.Clusters) ? loc.Clusters.toLowerCase() : "" :
                        (tblName === "school") ? (loc.Schools) ? loc.Schools.toLowerCase() : "" : "";
                        (tblName === "envelopbundle") ? (loc.Label_bundles) ? loc.Label_bundles.toLowerCase() : "" : "";
        return "<" + loc.No_ + caption + ">";
    }

    function t_MSSSS_AddAll_dict(tblName){
        const add_all_text = t_MSSSS_AddAll_txt(tblName);
        return (tblName === "student") ? {id: -1, examnumber: "", fullname: add_all_text} :
                (tblName === "subject") ? {base_id: -1, code: "", name_nl: add_all_text} :
               (tblName === "cluster") ? {id: -1,  subj_code: "", name: add_all_text} :
               (tblName === "school") ? {base_id: -1,  code: "", name: add_all_text} : {};
    };

//========= t_MSSSS_Create_SelectRow  ============= PR2020-12-18 PR2020-07-14
    function t_MSSSS_Create_SelectRowNIU(loc, tblName, tblBody_select, map_dict, selected_pk, el_input, MSSSS_Response) {
        //console.log("===== t_MSSSS_Create_SelectRow ===== ");
    //console.log("    tblName", tblName);
    //console.log("    map_dict", map_dict);
    //console.log("    map_dict.name_nl", map_dict.name_nl);

//--- get info from map_dict
        // when tblName = school: pk_int = schoolbase_pk
        const pk_int = (tblName === "school") ? map_dict.base_id : map_dict.id;

        const code = (tblName === "school") ? map_dict.sb_code :
                    (tblName === "subject") ? map_dict.code :
                    (tblName === "cluster") ? map_dict.subj_code :
                    (tblName === "student") ? map_dict.name_first_init : "";

        const name =  (tblName === "school") ? map_dict.name : // map_dict.abbrev
                    (tblName === "subject") ? map_dict.name_nl :
                    (tblName === "cluster") ? map_dict.name :
                    (tblName === "student") ? map_dict.fullname  :
                    (tblName === "envelopbundle") ? map_dict.name : "";

        const is_selected_row = (!!pk_int && pk_int === selected_pk);

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
        } else if(tblName === "envelopbundle"){
            if (name) { ob1 = name.toLowerCase()};
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
            td.classList.add(cls_bc_transparent);
        };

// --- add td to tblRow.
        td = tblRow.insertCell(-1);
        el_div = document.createElement("div");
            el_div.classList.add("pointer_show")
            el_div.innerText = name;
            el_div.classList.add("tw_240", "px-1")
            td.appendChild(el_div);
        if (name) { tblRow.title = name};
        td.classList.add(cls_bc_transparent);

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

//=========  t_MSSSS_InputKeyupNIU  ================ PR2020-09-19  PR2021-07-14
    function t_MSSSS_InputKeyupNIU(el_input) {
        //console.log( "===== t_MSSSS_InputKeyupNIU  ========= ");

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
            /*
            filter_dict =
                row_count: 1,
                selected_code: "bi",
                selected_innertext: ["Biologie"],
                selected_name: "Biologie",
                selected_pk: "123",
                selected_rowid: "sel_subjbase_123"
            */
            const selected_pk = (filter_dict.selected_pk) ? filter_dict.selected_pk : null;
            if (selected_pk) {
// ---  get pk code and value from filter_dict, put values in input box
                const data_code = (filter_dict.selected_code) ? filter_dict.selected_code : null;
                const data_name = (filter_dict.selected_name) ? filter_dict.selected_name : null;

                el_input.value = data_name;
                el_input.setAttribute("data-pk", selected_pk);
                el_input.setAttribute("data-code", data_code);
                el_input.setAttribute("data-name", data_name);
            };  //  if (!!selected_pk) {
        };
    }; // t_MSSSS_InputKeyupNIU


    function t_MSSSS_get_display_text(tblName, data_dict) {
        // PR2022-05-01 PR2022-08-29
        const name_field = (tblName === "student") ? "name_first_init" :
                            (tblName === "subject") ? "name_nl" :
                            "name";
        const code_field = (tblName === "student") ? "name_first_init" :
                            "code";
        const display_txt = (data_dict && name_field in data_dict && data_dict[name_field].length < 30) ? data_dict[name_field] :
                            (data_dict && code_field in data_dict) ? data_dict[code_field] : "---";
        return display_txt;
    };
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
    // excCol_row: {index: 12, excKey: "Profiel", awpKey: "level", awpCaption: "Learning_path"}
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
        // Function returns row of array that contains keyValue in arrKey PR2019-01-05 PR2020-12-28 PR2022-06-29
        // stored_columns[3]: {awpCol: "lastname", caption: "Last name", excCol: "ANAAM" }
        // excel_columns[0]:    {excCol: "ANAAM", awpCol: "lastname", awpCaption: "Achternaam"}
        // PR2020-12-27 do not use Object.entries because it does not allow break

    //console.log("----- get_arrayRow_by_keyValue -----")
    //console.log("    dict_list", dict_list)
    //console.log("    keyValue", keyValue, typeof keyValue)

        let row = null;
        if (dict_list && arrKey && keyValue != null){

            //PR2022-08-20 debug: dont use this one, it will skip the first column with index 0:
                // was: for (let i = 0, dict; dict = dict_list[i]; i++) {

            for (let i = 0, dict, len = dict_list.length; i < len; i++) {
                const dict = dict_list[i];
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
                    };
                    if (isEqual){
    //console.log("        value", value, typeof value)
    //console.log("  >>> isEqual", isEqual)
                        row = dict;
                        break;
        }}}};
        return row;
    };  // get_arrayRow_by_keyValue

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

    function t_lookup_row_in_dictlist(data_rows, lookup_field, lookup_value){
        // PR2022-03-29  lookup datarow the oldfashioned way
        // PR2024-05-02 from tsa
        if(lookup_value && data_rows && data_rows.length){
            for (let i = 0, row; row = data_rows[i]; i++) {
                if (row[lookup_field] === lookup_value){
                    return row;
                    break;
                };
            };
        };
        return null;
    };  // t_lookup_row_in_dictlist


    function t_lookup_rowindex_in_dictlist(data_rows, lookup_field, lookup_value){
        // PR2024-07-30 lookup rowindex the oldfashioned way
        if(lookup_value && data_rows && data_rows.length){
            for (let i = 0, row; row = data_rows[i]; i++) {
                if (row[lookup_field] === lookup_value){
                    return i;
                    break;
                };
            };
        };
        return null;
    };  // t_lookup_rowindex_in_dictlist

//========= t_get_rowindex_by_sortby  ================= PR2020-06-30
    function t_get_rowindex_by_sortby(tblBody, search_sortby) {
        //console.log(" ===== t_get_rowindex_by_sortby =====");
        //console.log("search_sortby", search_sortby);
        // TODO to be deprecated, only used in examyear.js and schools.js, To be replaced by b_recursive_tblRow_lookup
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

//=========  t_tbody_selected_clear  ================ PR2021-11-18  PR2022-08-07 PR2023-04-09
    function t_tbody_selected_clear(tableBody) {
        if(tableBody){
            for (let i = 0, tblRow; tblRow = tableBody.rows[i]; i++) {
                if (tblRow.classList.contains(cls_selected)){
                    tblRow.classList.remove(cls_selected);
                };
                t_td_selected_arroe_remove(tblRow.cells[0]);
            };
        };
    };  // t_tbody_selected_clear

//=========  t_td_selected_arroe_remove  ================ PR2023-04-09
    function t_td_selected_arroe_remove(td) {
        if(td){
            const el_select = td.children[0];
            if(el_select && el_select.innerHTML){
                el_select.innerHTML = null;
            };
        };
    };  // t_td_selected_arroe_remove

//=========  t_tr_selected_set  ================ PR2021-11-18 PR2022-08-07
    function t_tr_selected_set(tblRow) {
        //console.log("=========  t_tr_selected_set =========");
        if (!tblRow.classList.contains(cls_selected)) {
            tblRow.classList.add(cls_selected);
        };
        const td_01 = tblRow.cells[0];
        if(td_01){
            const el_select = td_01.children[0];
            if(el_select){
                el_select.innerHTML = "&#9658;";  // black pointer right
            };
        //console.log("el_select", el_select);
        };
    };  // t_tr_selected_set

//=========  t_tr_selected_remove  ================ PR2023-04-09
    function t_tr_selected_remove(tblRow) {
        //console.log("=========  t_tr_selected_remove =========");
        if (tblRow.classList.contains(cls_selected)) {
            tblRow.classList.remove(cls_selected);
        };
        const td_01 = tblRow.cells[0];
        if(td_01){
            const el_select = td_01.children[0];
            if(el_select && el_select.innerHTML){
                el_select.innerHTML = null;  // black pointer right
            };
        //console.log("el_select", el_select);
        };
    };  // t_tr_selected_remove

//=========  t_td_selected_toggle  ================ PR2021-11-18 PR2022-04-13
    function t_td_selected_toggle(tblRow, select_single) {
        //console.log("=========  t_td_selected_toggle =========");
        //console.log("cls_selected", cls_selected, "cls_background", cls_background);
        if(tblRow){
// deselect all selected rows when select_single = True
            if (select_single){
                t_tbody_selected_clear(tblRow.parentNode);
            };
            const new_is_selected = !tblRow.classList.contains(cls_selected);
            if (new_is_selected) {
                tblRow.classList.add(cls_selected);
            } else {
                tblRow.classList.remove(cls_selected);
            };
            const td_01 = tblRow.cells[0];
            if(td_01){
                const el_select = td_01.children[0];
                if(el_select){
                    el_select.innerHTML = (new_is_selected) ? "&#9658;" : null;   // "&#9658;" is black pointer right
                };
            };
        };
    };  // t_td_selected_toggle

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
//=========  t_SBR_FillSelectOptionsDepbaseLvlbaseSctbase  ================
// PR2021-03-06  PR2021-05-21 PR2021-08-27 PR2022-12-13 PR2023-07-10
    function t_SBR_FillSelectOptionsDepbaseLvlbaseSctbase(tblName, rows, setting_dict, skip_show_hide) {
        // used in studsubj.js and correctors.js
        const display_rows = []
        const has_items = (!!rows && !!rows.length);
        const has_one_item = (has_items && rows.length === 1);
        const has_profiel = setting_dict.sel_dep_has_profiel;
/*
    //console.log("=== t_SBR_FillSelectOptionsDepbaseLvlbaseSctbase");
    //console.log("    tblName", tblName);
    //console.log("    rows", rows);
    //console.log("    loc", loc);
    //console.log("    setting_dict", setting_dict);
    //console.log("    has_items", has_items);
    //console.log("    has_one_item", has_one_item);
    //console.log("    has_profiel", has_profiel);
*/
        // when label has no id the text is Sector / Profiel, set in .html file
        const el_SBR_select_sector_label = document.getElementById("id_SBR_select_sector_label");
        const All_sectors_profiles_txt = (!el_SBR_select_sector_label) ? loc.All_sectors_profiles : (has_profiel) ? loc.All_profiles :loc.All_sectors;
        let caption_all = null;
        const all_txt = "&#60" + (
                (tblName === "depbase") ? loc.All_departments :
                (tblName === "lvlbase") ? loc.All_levels :
                (tblName === "sctbase") ? All_sectors_profiles_txt : "---"
             ) + "&#62";

        if (has_items){
            if (has_one_item){

            // PR2022-12-16 dont update setting dict in this function, was confusing
            //    // if only 1 level: make that the selected one
           //     if (tblName === "department"){
           //         setting_dict.sel_depbase_pk = rows.base_id;
           //     } else if (tblName === "lvlbase"){
           //         setting_dict.sel_lvlbase_pk = rows.base_id;
           //     } else if (tblName === "sctbase"){
           //         setting_dict.sel_sctbase_pk = rows.base_id
           //     }
            } else {
                //PR2022-01-08 caption_all = all_txt is necessary to skip all_txt in setting_dict.sel_sctbase_code
                caption_all = all_txt;

                // add row 'Alle leerwegen' / Alle profielen / Alle sectoren in first row
                // HTML code "&#60" = "<" HTML code "&#62" = ">";
                display_rows.push({value: -9, caption: caption_all })
            };
            for (let i = 0, row; row = rows[i]; i++) {
                display_rows.push({
                    value: row.base_id,
                    caption: (tblName === "depbase") ?  row.base_code :
                             (tblName === "sctbase") ? row.name : row.abbrev
                });
            };
//    //console.log("display_rows", display_rows);

            const selected_pk = (tblName === "depbase") ? setting_dict.sel_depbase_pk : (tblName === "lvlbase") ? setting_dict.sel_lvlbase_pk : (tblName === "sctbase") ? setting_dict.sel_sctbase_pk : null;

//    //console.log("    tblName", tblName);
//    //console.log("    selected_pk", selected_pk);

            const id_SBR_select = (tblName === "depbase") ? "id_SBR_select_department" : (tblName === "lvlbase") ? "id_SBR_select_level" : (tblName === "sctbase") ? "id_SBR_select_sector" : null;
            const el_SBR_select = (id_SBR_select) ? document.getElementById(id_SBR_select) : null;
            t_FillOptionsFromList(el_SBR_select, display_rows, "value", "caption", null, null, selected_pk);

            // put displayed text in setting_dict - PR2022-01-08 dont show 'All profielen' etc

            // PR2022-12-16 dont update setting dict in this function, was confusing
            // //PR2022-01-08 dont put 'All profielen' etc in setting_dict > skip when caption_all has value
            //if (!caption_all){
            //    const sel_code = (el_SBR_select.options[el_SBR_select.selectedIndex]) ? el_SBR_select.options[el_SBR_select.selectedIndex].innerText : null;
            //    if (tblName === "lvlbase"){
            //        setting_dict.sel_lvlbase_code = sel_code;
           //     } else if (tblName === "sctbase"){
           //         setting_dict.sel_sctbase_code = sel_code;
           //     };
            //};

        };
        // show select level and sector
        if(!skip_show_hide){
            if (tblName === "lvlbase"){
                add_or_remove_class(document.getElementById("id_SBR_container_level"), cls_hide, !has_items);
            // set label of profiel
             } else if (tblName === "sctbase"){
                add_or_remove_class(document.getElementById("id_SBR_container_sector"), cls_hide, false);
                // when label has no id the text is Sector / Profiel, set in .html file
                if(el_SBR_select_sector_label){el_SBR_select_sector_label.innerText = ( (has_profiel) ? loc.Profile : loc.Sector ) + ":"};
            };
        };

    };  // t_SBR_FillSelectOptionsDepbaseLvlbaseSctbase

//========= t_FillOptionLevelSectorFromMap  ============= PR2020-12-11 from tsa PR2021-07-18 PR2022-08-05
    function t_FillOptionLevelSectorFromMap(tblName, pk_field, data_map, depbase_pk, selected_pk, firstoption_txt, select_text) {
         //console.log( "===== t_FillOptionLevelSectorFromMap  ========= ");
         //console.log( "data_map", data_map);
         // used in page schemes
// add empty option on first row, put firstoption_txt in < > (placed here to escape \< and \>
        let option_text = "";
        if (select_text){
            option_text += "<option value=\"\" disabled selected hidden>" + select_text + "...</option>";
        };

        if(firstoption_txt){
            option_text += "<option value=\"0\" data-ppk=\"0\">" + firstoption_txt + "</option>";
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


//========= t_FillOptionLevelSectorFromDatarows  ============= PR2023-02-21
    function t_FillOptionLevelSectorFromDatarows(tblName, pk_field, data_rows, depbase_pk, selected_pk, firstoption_txt, select_text) {
         //console.log( "===== t_FillOptionLevelSectorFromDatarows  ========= ");
         //console.log( "data_map", data_map);
         // used to fill SBR select level, sector from datarows instad of datamap (datamap te be deprecated)


// add empty option on first row, put firstoption_txt in < > (placed here to escape \< and \>
        let option_text = "";
        if (select_text){
            option_text += "<option value=\"\" disabled selected hidden>" + select_text + "...</option>";
        };

        if(firstoption_txt){
            option_text += "<option value=\"0\" data-ppk=\"0\">" + firstoption_txt + "</option>";
        }
// --- loop through data_map, fill only items with department_pk in depbases
        if (data_rows && data_rows.length) {

// first sort data_rows on field 'sequence'
        data_rows.sort(b_comparator_sequence);

            for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
                if(data_dict.depbases && depbase_pk && data_dict.depbases.includes(depbase_pk)){
                    option_text += FillOptionText(tblName, pk_field, data_dict, selected_pk);
                }
            }
        };
        return option_text
    }  // t_FillOptionLevelSectorFromDatarows

//========= FillOptionText  ============= PR2020-12-11 from tsa
    function FillOptionText(tblName, pk_field, item_dict, selected_pk) {
        //console.log( "===== FillOptionText  ========= ");
        const value = (tblName === "level")
                ? (item_dict.abbrev)
                    ? item_dict.abbrev : "---"
                : (item_dict.name)
                    ? item_dict.name : "---" ;
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
        //console.log( "===== t_FillSelectOptions  ===== ");
        // called by page exam MEXQ_FillSelectTableLevel  and page_subject SBR_Select_scheme
        //console.log( "    selected_pk", selected_pk, typeof selected_pk);
        //console.log( "    data_map", data_map);

// ---  fill options of select box
        let option_text = "";
        let row_count = 0

// --- loop through data_map
        if(!!data_map){
            for (const [map_id, map_dict] of data_map.entries()) {
                const pk_int = map_dict[id_field];
                const display_value = (map_dict[display_field]) ?  map_dict[display_field] : "---";

        //console.log( "map_dict", map_dict);
        //console.log( "pk_int", pk_int, typeof pk_int);
        //console.log( "display_value", display_value);
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
         console.log( "===== t_FillOptionFromList  ========= ");
         console.log( "    data_list", data_list);
         // add empty option on first row, put firstoption_txt in < > (placed here to escape \< and \>
         // used in page customers
        let option_text = "";
        if(!!firstoption_txt){
            option_text = "<option value=\"0\" data-ppk=\"0\">" + firstoption_txt + "</option>";
        }
        for (let i = 0, len = data_list.length; i < len; i++) {
            const item_dict = data_list[i];

         console.log( "    item_dict", item_dict);
            const item_text = FillOptionText(item_dict, selected_pk);
            option_text += item_text;
        }
        return option_text
    }  // t_FillOptionFromList

//========= t_FillOptionsFromList  =======  PR2020-12-17
    function t_FillOptionsFromList(el_select, data_list, value_field, caption_field,
                                    select_text, select_text_none, selected_value, filter_field, filter_value) {
/*
        //console.log( "=== t_FillOptionsFromList ");
        //console.log( "    data_list", data_list);
        //console.log( "    value_field", value_field);
        //console.log( "    selected_value", selected_value);
        //console.log( "    filter_field", filter_field);
        //console.log( "    filter_value", filter_value, typeof filter_value);
*/
// ---  fill options of select box
        let option_text = "";
        let row_count = 0;

// --- loop through data_list
        if(data_list){
            for (let i = 0, len = data_list.length; i < len; i++) {
                const item_dict = data_list[i];
                const item_value = (item_dict[value_field]) ? item_dict[value_field] : null;
                const item_caption = (item_dict[caption_field]) ? item_dict[caption_field] : "---";
/*
        //console.log( "    item_value", item_value);
        //console.log( "    item_caption", item_caption);
        //console.log( "    filter_field", filter_field);
*/
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
       // if (select_first_option){
       //     el_select.selectedIndex = 0;
       // };
// disable element if it has none or one rows
        el_select.disabled = (row_count <= 1);

//        //console.log( "    option_text", option_text);
 //       //console.log( "    el_select", el_select);
    };  // t_FillOptionsFromList

//========= t_FillOptionTextNew  ============= PR2020-12-11 from tsa
    function t_FillOptionTextNew(value, caption, selected_value) {
        //console.log( "===== t_FillOptionTextNew  ========= ");
        let item_text = "<option value=\"" + value + "\"";
        //if (selected_value && value === selected_value) {item_text += " selected=true" };
        if (selected_value && value === selected_value) {item_text += " selected" };
        item_text +=  ">" + caption + "</option>";
        return item_text;
    };  // t_FillOptionTextNew

//###########################################################################
// +++++++++++++++++ REFRESH DATADICTS ++++++++++++++++++++++++++++++++++++++++++++++++++

//=========  t_Refresh_DataDicts  ================  PR2021-06-21 PR2023-01-05
    function t_Refresh_DataDicts(tblName, update_rows, data_dicts, CreateTblRow) {
        //console.log(" ===== t_Refresh_DataDicts  =====");
        //console.log("    tblName", tblName);
        //console.log("    field_settings", field_settings);
        //console.log("    update_rows", update_rows);

        // PR2021-01-13 debug: when update_rows = [] then !!update_rows = true. Must add !!update_rows.length
        if (update_rows && update_rows.length ) {
            const field_setting = field_settings[selected_btn];
        //console.log("    selected_btn", selected_btn);
        //console.log("    field_setting", field_setting);
            const pk_fldName = (tblName === "studsubj") ? "studsubj_id" :
                                (tblName === "cluster") ?  "id" :  "";
            for (let i = 0, update_dict; update_dict = update_rows[i]; i++) {
                t_Refresh_DatadictItem(tblName, field_setting, update_dict, data_dicts, pk_fldName, CreateTblRow);
            };
        };

    };  //  t_Refresh_DataDicts

//=========  t_Refresh_DatadictItem  ================ PR2020-08-16 PR2020-09-30 PR2021-06-21 PR2022-03-04 PR2023-01-05
    function t_Refresh_DatadictItem(tblName, field_setting, update_dict, data_dicts, pk_fldName, CreateTblRow) {
        //console.log(" --- t_Refresh_DatadictItem  ---");
        //console.log("    tblName", tblName);
        //console.log("    pk_fldName", pk_fldName);
        //console.log("field_setting", field_setting);
        //console.log("    update_dict", update_dict);
        //console.log("    update_dict.err_fields", update_dict.err_fields);

        if(!isEmpty(update_dict)){
            const field_names = field_setting.field_names;

            const pk_int = (update_dict[pk_fldName]) ? update_dict[pk_fldName] : null;

            const map_id = update_dict.mapid;
            const is_deleted = (!!update_dict.deleted);
            const is_created = (!!update_dict.created);
            const is_restored = (!!update_dict.restored);
            const is_changed = (!!update_dict.changed);

        //console.log("    pk_int", pk_int, typeof pk_int);
        //console.log("    is_deleted", is_deleted);
        //console.log("    is_created", is_created);
        //console.log("    is_restored", is_restored);

    // ---  get list of hidden columns
        const col_hidden = b_copy_array_to_new_noduplicates(mod_MCOL_dict.cols_hidden);

    // ---  get list of columns that are not updated because of errors
            const error_columns = [];
            if (update_dict.err_fields){
                // replace field 'subj_auth2by' by 'subj_status'
                for (let i = 0, err_field; err_field = update_dict.err_fields[i]; i++) {
                    if (err_field && err_field.includes("_auth")){
                        const arr = err_field.split("_");
                        err_field = arr[0] + "_status";
                    };
                    error_columns.push(err_field);
                };
            };

// ++++ created ++++
            // PR2021-06-16 from https://stackoverflow.com/questions/586182/how-to-insert-an-item-into-an-array-at-a-specific-index-javascript
            //arr.splice(index, 0, item); will insert item into arr at the specified index
            // (deleting 0 items first, that is, it's just an insert).

            if(is_created){
    // ---  first remove key 'created' from update_dict
                delete update_dict.created;

    // --- lookup index where new row must be inserted in data_rows
                // PR2021-06-21 not necessary, new row has always pk higher than existing. Add at end of rows

    // ---  add new item to  data_dicts with key
                //data_rows.push(update_dict);
                const pk_int = (tblName === "cluster") ? update_dict.id : update_dict.stud_id;
                const key_str = b_get_datadicts_keystr(tblName, pk_int, update_dict.studsubj_id);

                data_dicts[key_str] = update_dict;

    // - delete row without subjects
                if (tblName === "studsubj"){
                const nosubjects_keystr = b_get_datadicts_keystr(tblName, update_dict.stud_id);
                    if (data_dicts[nosubjects_keystr]){
                        delete data_dicts[nosubjects_keystr];
                    };
                };
    // clusters are not table rows, skip Filter_TableRows when tblName = "cluster"
                if (tblName !== "cluster"){
        // ---  create row in table., insert in alphabetical order
                    const new_tblRow = CreateTblRow(tblName, field_setting, map_id, update_dict, col_hidden);

                    if(new_tblRow){
        // --- add1 to item_count and show total in sidebar
                        selected.item_count += 1;
        // ---  scrollIntoView,
                        new_tblRow.scrollIntoView({ block: 'center',  behavior: 'smooth' });

        // ---  make new row green for 2 seconds,
                        ShowOkElement(new_tblRow);
                    };
                };
            } else {

// +++ get existing data_dict from data_rows. data_rows is ordered by: stud_id, studsubj_id'
                let data_dict = null, datarow_index = null;
                if (tblName === "cluster"){
                    //const cluster_pk = update_dict.id;
                    //const [index, found_dict, compare] = b_recursive_integer_lookup(cluster_rows, "id", cluster_pk);
                    //if (!isEmpty(found_dict)){
                    //    data_dict = found_dict;
                    //    datarow_index = index;
                    //};
                    data_dict = (!isEmpty(cluster_dictsNEW[update_dict.id])) ? cluster_dictsNEW[update_dict.id] : null;
                } else {
                    // 'ORDER BY st.id, studsubj.studsubj_id NULLS FIRST'
                    const student_pk = (update_dict && update_dict.stud_id) ? update_dict.stud_id : null;
                    const studsubj_pk = (update_dict && update_dict.studsubj_id) ? update_dict.studsubj_id : null;
                    //const [index, found_dict] = get_datadict_by_studpk_studsubjpk(student_pk, studsubj_pk);
                    //if (!isEmpty(found_dict)){
                    //    data_dict = found_dict;
                    //    datarow_index = index;
                    //};
                    data_dict = get_datadict_by_studpk_studsubjpk (student_pk, studsubj_pk);
                };

        //console.log("    data_dict", data_dict);

// ++++ deleted ++++
                if(is_restored){

    // ---  remove key 'restored' from update_dict
                    delete update_dict.restored;

    // ---  update data_dict
                    data_dicts[map_id] = update_dict;
                    let tblRow = document.getElementById(map_id);

    // ---  update tblRow
                    UpdateTblRow(tblRow, tblName, update_dict);

                } else if(is_changed){
    // ---  remove key 'changed' from update_dict
                    delete update_dict.changed;

    // ---  update data_dict
                    data_dicts[map_id] = update_dict;
                    let tblRow = document.getElementById(map_id);

    // ---  update tblRow
                    UpdateTblRow(tblRow, tblName, update_dict);

                } else if(is_deleted){

    // ---  delete key/value from data_dict
                    if (map_id && map_id in data_dicts){
                        delete data_dicts[map_id];

        //--- delete tblRow
                        if (tblName !== "cluster"){
                            const tblRow_tobe_deleted = document.getElementById(map_id);
                            if (tblRow_tobe_deleted ){
                                tblRow_tobe_deleted.parentNode.removeChild(tblRow_tobe_deleted);
            // --- subtract 1 from item_count and show total in sidebar
                                selected.item_count -= 1;
                            };
                        };
                    };

                } else {

// +++++++++++ updated row +++++++++++
    //console.log("updated row");
    // ---  check which fields are updated, add to list 'updated_columns'
                    if(!isEmpty(data_dict) && field_names){

    // ---  first add updated fields to updated_columns list, before updating data_row
                        let updated_columns = [];
                        // first column subj_error
                        for (let i = 0, col_field, old_value, new_value; col_field = field_names[i]; i++) {

    // ---  'status' fields are not in data_row
                            if (col_field.includes("_status")){
                                const [old_status_className, old_status_title] = UpdateFieldStatus(col_field, data_dict);
                                const [new_status_className, new_status_title] = UpdateFieldStatus(col_field, update_dict);
                                if (old_status_className !== new_status_className || old_status_title !== new_status_title ) {
                                    updated_columns.push(col_field)
                                };
                            } else if (col_field === "subj_error"){
                                    // PR2023-01-16
                                    if (update_dict.subj_composition_ok !== data_dict.subj_composition_ok ||
                                        update_dict.subj_dispensation !== data_dict.subj_dispensation) {
                                            updated_columns.push(col_field);
                                        };

                            } else if (col_field in data_dict && col_field in update_dict){
                                if (data_dict[col_field] !== update_dict[col_field] ) {
                                    updated_columns.push(col_field)
                                };
                            };
                        };

// ---  update fields in data_row
                        for (const [key, new_value] of Object.entries(update_dict)) {
                            if (key in data_dict){
                                const old_value = data_dict[key];
                                if (new_value !== data_dict[key]) {
                                    data_dict[key] = new_value;
                                };
                            };
                        };

// ---  update field in tblRow
                        // note: when updated_columns is empty, then updated_columns is still true.
                        // Therefore don't use Use 'if !!updated_columns' but use 'if !!updated_columns.length' instead
                        // PR2021-09-29 always update all columns, to remove strikethrough after undelete
                        // was: if(updated_columns.length || field_error_list.length){

// --- get existing tblRow
                            let tblRow = document.getElementById(map_id);
    //console.log("tblRow", tblRow);
    //console.log("updated_columns", updated_columns);
                            if(tblRow){

    // - to make it perfect: move row when first or last name have changed
                                if (updated_columns.includes("name")){
                                //--- delete current tblRow
                                    tblRow.parentNode.removeChild(tblRow);
                                //--- insert row new at new position
                                    tblRow = CreateTblRow(tblName, field_setting, map_id, update_dict, col_hidden)
                                };

    // - loop through cells of row
                                const tobedeleted = (update_dict.tobedeleted) ? update_dict.tobedeleted : false;
                                const st_tobedeleted = (update_dict.st_tobedeleted) ? update_dict.st_tobedeleted : false;

    //console.log("tobedeleted", tobedeleted);
                                for (let i = 1, el_fldName, el, td; td = tblRow.cells[i]; i++) {
                                    el = td.children[0];
                                    if (el){
                                        el_fldName = get_attr_from_el(el, "data-field");
                                        const is_updated_field = updated_columns.includes(el_fldName);
                                        const is_err_field = error_columns.includes(el_fldName);

    // - update field and make field green when field name is in updated_columns
                                        // PR2022-01-18 debug: UpdateField also when record is tobedeleted
                                        if(is_updated_field || tobedeleted){
                                            UpdateField(el, update_dict, tobedeleted);
                                        };
                                        if(is_updated_field){ShowOkElement(el)};
                                        if(is_err_field){
    // - make field red when error and reset old value after 2 seconds
                                            reset_element_with_errorclass(el, update_dict, tobedeleted, st_tobedeleted);
                                        };

                                    }  //  if (el){
                                };  //  for (let i = 1, el_fldName, el; el = tblRow.cells[i]; i++)
                            };  // if(tblRow)
                        //}; // if(updated_columns.length)
                    };  // if(!isEmpty(data_dict) && field_names)
                };  //  if(is_deleted)
            }; // if(is_created)

    // ---  show total in sidebar
            t_set_sbr_itemcount_txt(loc, selected.item_count, loc.Subject, loc.Subjects, setting_dict.user_lang);

        };  // if(!isEmpty(update_dict))
    }  // t_Refresh_DatadictItem

//###########################################################################

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
                        sel_pk = get_attr_from_el_int(tblRow, "data-pk")
                        sel_ppk = get_attr_from_el_int(tblRow, "data-ppk")

                        // PR2024-03-30 don't use get_attr_from_el_int(tblRow, "data-pk"), it converts null to 0
                        sel_pk = (tblRow.dataset.pk) ? parseInt(tblRow.dataset.pk, 10) : null;
                        sel_ppk = (tblRow.dataset.ppk) ? parseInt(tblRow.dataset.ppk, 10) : null;

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
    //console.log(">>> filter_dict", filter_dict);
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
                                        el_value = el.options[el.selectedIndex].innerText;
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
        //console.log( "    filter_dict", filter_dict);

        selected.item_count = 0
// ---  loop through tblBody.rows
        for (let i = 0, tblRow, show_row; tblRow = tblBody_datatable.rows[i]; i++) {
            tblRow = tblBody_datatable.rows[i]
            show_row = t_Filter_TableRow_Extended(filter_dict, tblRow);
            add_or_remove_class(tblRow, cls_hide, !show_row);
            if (show_row) {selected.item_count += 1};
        }

// ---  show total in sidebar
        t_set_sbr_itemcount_txt(loc, selected.item_count, count_unit_sing, count_unit_plur, setting_dict.user_lang);
    }; // t_Filter_TableRows

//========= t_reset_filterrow  ==================================== PR2020-08-17  PR2021-08-10  PR2023-03-09
    function t_reset_filterrow(tblHead_datatable) {
        //console.log( "===== t_reset_filterrow  ========= ");
        //console.log( "filter_dict", filter_dict);
        // function clears elements in filterrow of tblHead_datatable
        let filterRow = tblHead_datatable.rows[1];
        if(filterRow){
            for (let j = 0, cell, el; cell = filterRow.cells[j]; j++) {
                if(cell){
                    el = cell.children[0];
                    if(el){
                        const filter_tag = get_attr_from_el(el, "data-filtertag")
                        if (el.tagName === "INPUT"){
                            el.value = null;
                        } else if (filter_tag === "select"){
                            // remove arrow  PR2023-04-09
                            el.innerHTML = null;
                        } else {
                            const el_icon = el.children[0];
                            if(el_icon){
                                let classList = el_icon.classList;
                                while (classList.length > 0) {
                                    classList.remove(classList.item(0));
                                };
                                el_icon.classList.add("tickmark_0_0")
                            };
                        };
                    };
                };
            };
       };

    }; // t_reset_filterrow

//========= t_set_sbr_itemcount_txt  ==================================== PR2021-12-20
    function t_set_sbr_itemcount_txt(loc, item_count, count_unit_sing, count_unit_plur, user_lang) {
        //console.log( "===== t_set_sbr_itemcount_txt  ========= ");
        //console.log( "    item_count", item_count);

// ---  show total in sidebar
        const el_SBR_item_count = document.getElementById("id_SBR_item_count");

        if (el_SBR_item_count){
            let inner_text = null;
            if (item_count){
                const count_txt = f_format_count(user_lang, item_count);
                const unit_sing = (count_unit_sing) ? count_unit_sing.toLowerCase() : "";
                const unit_plur = (count_unit_plur) ? count_unit_plur.toLowerCase() : "";
                const unit_txt = (item_count === 1) ? unit_sing : unit_plur;
                inner_text = [loc.Total, count_txt, unit_txt].join(" ");
            }
        //console.log( "    inner_text", inner_text);
            el_SBR_item_count.innerText = inner_text;
        };
    }; // t_set_sbr_itemcount_txt

//========= t_Filter_TableRow_Extended  ==================================== PR2020-07-12 PR2020-09-12 PR2021-10-28
    function t_Filter_TableRow_Extended(filter_dict, tblRow, data_inactive_field) {
        //console.log( "===== t_Filter_TableRow_Extended");
        //console.log( "filter_dict", filter_dict);
        //console.log( "data_inactive_field", data_inactive_field);
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

        // PR223-04-22 --- in userpage: put filter of column 1 (username in filterrow, because filter stays when tab btn changes PR223-04-22
        // doesnt work because index refers to diferent columns in different tabs. filter_dict must use fieldname instead of index
       // TODO use fieldnames in filterdict instead of index. Check if that is much slower, because you must get fieldname from attribute data-field

        let hide_row = false;

// ---  show all rows if filter_dict is empty - except for inactive ones
        if (tblRow){

// --- PR2021-10-28 new way of filtering inactive rows: (for now: only used in mailbox - deleted)
            // - set filter inactive before other filters, inactive value is stored in tblRow, "data-inactive", skip when data_inactive_field is null
            // - filter_dict has key 'showinactive', value is integer.
            // values of showinactive are:  '0'; is show all, '1' is show active only, '2' is show inactive only
            if (data_inactive_field){
                const filter_showinactive = (filter_dict && filter_dict.showinactive != null) ? filter_dict.showinactive : 1;
                const is_inactive = !!get_attr_from_el_int(tblRow, data_inactive_field);

                hide_row = (filter_showinactive === 1) ? (is_inactive) :
                           (filter_showinactive === 2) ? (!is_inactive) : false;
    //console.log("     filter_showinactive", filter_showinactive)
    //console.log("     is_inactive", is_inactive)
    //console.log("   >>>  hide_row", hide_row)
            };

            if (!hide_row && !isEmpty(filter_dict)){
    // ---  loop through filter_dict key = index_str, value = filter_arr
               for (const [index_str, filter_arr] of Object.entries(filter_dict)) {

    // ---  skip column if no filter on this column, also if hide_row is already true
                    if(!hide_row && filter_arr){
                        // filter text is already trimmed and lowercase
                        const col_index = Number(index_str);
                        const filter_tag = filter_arr[0];
                        const filter_value = filter_arr[1];
                        const filter_mode = filter_arr[2];

                        const cell = tblRow.cells[col_index];
    //console.log(" ===> cell", cell);
                        if(cell){
                            const el = cell.children[0];
                            if (el){
                                const cell_value = get_attr_from_el(el, "data-filter")
/*
    //console.log("     filter_tag", filter_tag)
    //console.log("     filter_value", filter_value, typeof filter_value)
    //console.log("     cell_value", cell_value, typeof cell_value)
*/
                                if (filter_tag === "grade_status"){

                                    // PR2023-02-21 in page grades
                                    // filter_values are: '0'; is show all, 1: not approved, 2: auth1 approved, 3: auth2 approved, 4: auth1+2 approved, 5: submitted,   TODO '6': tobedeleted '7': locked
                                    // filter_array  = ['grade_status', '1']
                                   if (filter_value === "1") {
                                        hide_row = (cell_value && cell_value !== "diamond_0_0"); // none approved - outlined diamond
                                    } else if (filter_value === "2") {  // filter_value === "2") ? "diamond_3_2" :  // not approved by chairperson
                                        hide_row = !["diamond_0_0", "diamond_0_2",
                                                    "diamond_1_0", "diamond_1_2",
                                                    "diamond_2_0", "diamond_2_2",
                                                    "diamond_3_0", "diamond_3_2"].includes(cell_value);
                                    } else if (filter_value === "3") {  // filter_value === "3": not approved by secretary
                                        hide_row = !["diamond_0_0", "diamond_0_1",
                                                    "diamond_1_0", "diamond_1_1",
                                                    "diamond_2_0", "diamond_2_1",
                                                    "diamond_3_0", "diamond_3_1"].includes(cell_value);
                                    } else if (filter_value === "4") {  // filter_value === "4": // not approved by examiner
                                        hide_row = !["diamond_0_0", "diamond_0_1", "diamond_0_2", "diamond_0_3",
                                                    "diamond_2_0", "diamond_2_1",  "diamond_2_2", "diamond_2_3"].includes(cell_value);

                                    } else if (filter_value === "5") {  // filter_value === "5": // not approved by second corrector
                                        hide_row = !["diamond_0_0", "diamond_0_1", "diamond_0_2", "diamond_0_3",
                                                     "diamond_1_0", "diamond_1_1", "diamond_1_2", "diamond_1_3"].includes(cell_value);

                                    } else if (filter_value === "6") {  // filter_value === "6": all approved - full black diamond
                                        hide_row = cell_value !== "diamond_3_3";

                                    } else if (filter_value === "7") {  // filter_value === "7": // submitted - full blue diamond
                                        hide_row = cell_value !== "diamond_0_4";  // submitted - full blue diamond

                                    } else if (filter_value === "8") {  // filter_value === "8": // blocked - full red diamond
                                        hide_row = cell_value !== "diamond_1_4";
                                    };

                                } else if (filter_tag === "status"){
                                    // PR2023-02-21 in page studsubj
                                    // filter_values are: '0'; is show all, 1: not approved, 2: auth1 approved, 3: auth2 approved, 4: auth1+2 approved, 5: submitted,   TODO '6': tobedeleted '7': locked

                                    // default filter status '0'; is show all, '1' is show tickmark, '2' is show without tickmark
                                    hide_row = (filter_value && Number(filter_value) !== Number(cell_value));

                                } else if (filter_tag === "toggle"){
                                    // default filter toggle '0'; is show all, '1' is show tickmark, '2' is show without tickmark
                                    if (filter_value === "2"){
                                        // only show rows without tickmark
                                         if (cell_value === "1") { hide_row = true };
                                    } else if (filter_value === "1"){
                                        // only show rows with tickmark
                                         if (cell_value !== "1") { hide_row = true };
                                    };
/*
    //console.log("filter_tag", filter_tag);
    //console.log("filter_value", filter_value, typeof filter_value);
    //console.log("cell_value", cell_value, typeof cell_value);
    //console.log("hide_row", hide_row);
*/
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
                                     };
                                } else if( filter_tag === "number") {
                                    // numeric columns: make blank cells zero
/*
    //console.log( "filter_value", filter_value, typeof filter_value);
    //console.log( "Number(filter_value)", Number(filter_value), typeof Number(filter_value));
    //console.log( "cell_value", cell_value, typeof cell_value);
    //console.log( "Number(cell_value)", Number(cell_value), typeof Number(cell_value));
*/
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
    }; // t_Filter_TableRow_Extended

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


// +++++++++++++++++ MODAL SELECT COLUMNS ++++++++++++++++++++++++++++++++++++++++++ PR2021-08-18 PR2021-12-16 PR2022-07-21

//  mod_MCOL_dict.columns        is a fixed array of fields that may be hidden, per page and tab, set on loading page
//  setting_dict.cols_hidden   contains saved list of hidden columns, retrieved on opening page
//  mod_MCOL_dict.cols_hidden  is deep copy of setting_dict.cols_hidden, fields are added / removed from this array

// mod_MCOL_dict is only used in this script for modal. pages use columns_hidden and mod_MCOL_dict.columns
// mod_MCOL_dict.cols_hidden holds fields in modal before they are saved, columns_hidden holds saved fields

// these function use selected_btn, columns_hidden[tblName], mod_MCOL_dict.columns[tblName].fields;
// PR2022-05-15 cols_skipped is dict with key: sel_btn and value: list of fieldnames to be skipped when filling tables with columns

// variable 'mod_MCOL_dict.columns' and 'mod_MCOL_dict.cols_hidden'  gets values in grades.js etc.
// PR2022-07-21
// - key 'columns' contains all columns that can appear in modal, gets values in grades.js etc.
// - key 'cols_skipped' contains columns that must be skipped, like: cols_skipped: {all: ["lvl_abbrev"]}, gets value in grades.js etc.
// - key 'cols_hidden' contains saved list of hidden columns, gets values from setting_dict.cols_hidden in grades.js etc.
// - key 'cols_tobe_hidden' contains new list of hidden columns, before saving.

const mod_MCOL_dict = {
    selected_btn: null,
    columns: {},
    cols_skipped: {},
    cols_hidden: [],
    columns_excl_skipped: []
}

//=========  t_MCOL_Open  ================ PR2021-08-02 PR2021-12-02 PR2022-05-15 PR2022-07-21 PR2023-01-12
    function t_MCOL_Open(page) {
        console.log(" -----  t_MCOL_Open   ----")
    console.log("    mod_MCOL_dict", mod_MCOL_dict)
    console.log("    mod_MCOL_dict.cols_skipped", mod_MCOL_dict.cols_skipped)

        // note: this function uses global variable 'selected_btn'

        //  setting_dict.cols_hidden was dict with key 'all' or sel_btn, changed to array PR2021-12-14
        //  skip when setting_dict.cols_hidden is not an array,
        // will be changed into an array when saving with t_MCOL_Save

        mod_MCOL_dict.page = page;
        mod_MCOL_dict.selected_btn = selected_btn;

// - fill cols_skipped_list
        // from https://stackoverflow.com/questions/1374126/how-to-extend-an-existing-javascript-array-with-another-array-without-creating
        const cols_skipped_list = [];
        if (mod_MCOL_dict.cols_skipped){
            if (mod_MCOL_dict.cols_skipped[mod_MCOL_dict.selected_btn]){
                cols_skipped_list.push(...mod_MCOL_dict.cols_skipped[mod_MCOL_dict.selected_btn]);
            };
            if(mod_MCOL_dict.cols_skipped.all){
                cols_skipped_list.push(...mod_MCOL_dict.cols_skipped.all);
            };
        };

    console.log("    cols_skipped_list", cols_skipped_list)

// - fill columns_excl_skipped
        mod_MCOL_dict.columns_excl_skipped = [];
        // loop through values of key 'all' and key selected_btn
        for (const [key, dict] of Object.entries(mod_MCOL_dict.columns)) {
    console.log("....key", key)
    console.log("    dict", dict)
    console.log("    mod_MCOL_dict.selected_btn", mod_MCOL_dict.selected_btn)
            if (key === mod_MCOL_dict.selected_btn || key === 'all'){
                for (const [field, value] of Object.entries(dict)) {
                    // translate value, caption = 'Profile' when dep has_profile and field - sctbase_id
                    const caption = (field === "sctbase_id" && mod_MCOL_dict.sel_dep_has_profiel) ? loc.Profile : (loc[value]) ? loc[value] : value;
        // add 'skip' if field is in cols_skipped
            // note: 'skip' fields are also added to preserve 'is_hidden' of skipped fields'
                    const skip = (cols_skipped_list.includes(field));
    //console.log("    skip", skip)
                    const is_hidden = (field && mod_MCOL_dict.cols_hidden.includes(field));
    //console.log("    is_hidden", is_hidden)
                    mod_MCOL_dict.columns_excl_skipped.push({field: field, sortby: caption, skip: skip, hidden: is_hidden});
        }}};

    // sort by field 'sortby'
        mod_MCOL_dict.columns_excl_skipped.sort(b_comparator_sortby);
    //console.log("mod_MCOL_dict.columns_excl_skipped", mod_MCOL_dict.columns_excl_skipped)
        t_MCOL_FillSelectTable();

// ---  disable save btn
        const el_MCOL_btn_save = document.getElementById("id_MCOL_btn_save")
        el_MCOL_btn_save.disabled = true

// ---  show modal, set focus on save button
       $("#id_mod_select_columns").modal({backdrop: true});
    }  // t_MCOL_Open

//=========  t_MCOL_Save  ================ PR2021-08-02 PR2021-12-02 PR2022-07-21
    function t_MCOL_Save(url_usersetting_upload, HandleBtnSelect) {
        //console.log(" -----  t_MCOL_Save   ----")
        const upload_dict = {};
        const upload_colhidden_list = []
        if (mod_MCOL_dict.columns_excl_skipped && mod_MCOL_dict.columns_excl_skipped.length){
            for (let i = 0, dict; dict = mod_MCOL_dict.columns_excl_skipped[i]; i++) {
                // include skipped fields, to preserve is_hidden
                if (dict.hidden){
                    upload_colhidden_list.push(dict.field);
                };
            };
        };
        upload_dict[mod_MCOL_dict.page] = {cols_hidden: upload_colhidden_list}

    //console.log("    upload_dict", upload_dict);
    //console.log("    url_usersetting_upload", url_usersetting_upload);

        b_UploadSettings (upload_dict, url_usersetting_upload);

    // update mod_MCOL_dict.cols_hidden
        b_copy_array_noduplicates(upload_colhidden_list, mod_MCOL_dict.cols_hidden);

    //console.log("   mod_MCOL_dict.cols_hidden", mod_MCOL_dict.cols_hidden);
        HandleBtnSelect(mod_MCOL_dict.selected_btn, true)  // true = skip_upload
// hide modal
        // in HTML: data-dismiss="modal"
    }  // t_MCOL_Save

//=========  t_MCOL_FillSelectTable  ================ PR2021-07-07 PR2021-08-02 PR2021-12-14 PR2022-05-15 PR2022-07-21
    function t_MCOL_FillSelectTable(just_linked_field) {
        //console.log("===  t_MCOL_FillSelectTable == ");

        const el_MCOL_tblBody_available = document.getElementById("id_MCOL_tblBody_available");
        const el_MCOL_tblBody_show = document.getElementById("id_MCOL_tblBody_show");
        el_MCOL_tblBody_available.innerHTML = null;
        el_MCOL_tblBody_show.innerHTML = null;

//+++ loop through dict of fields
        if(!isEmpty(mod_MCOL_dict.columns_excl_skipped)){
            for (let i = 0, dict; dict = mod_MCOL_dict.columns_excl_skipped[i]; i++) {
                if (!dict.skip) {
                    const field = dict.field;
                    const caption = dict.sortby;
    // - display 'Profiel' when sel_dep_has_profiel
                    const caption_str = (field === "sct_abbrev") ?
                                    (setting_dict.sel_dep_has_profiel) ? loc.Profile : loc.Sector :
                                    (loc[caption]) ? loc[caption] : caption;
                    const is_hidden = dict.hidden;
                    const tBody = (is_hidden) ? el_MCOL_tblBody_available : el_MCOL_tblBody_show;

    // +++ insert tblRow into tBody
                    const tblRow = tBody.insertRow(-1);
                    tblRow.setAttribute("data-field", field);
                    tblRow.addEventListener("click", function() {MCOL_SelectItem(tblRow);}, false )

    // --- if new appended row: highlight row for 1 second
                    if (just_linked_field && just_linked_field === field) {
                        let cell = tblRow.cells[0];
                        tblRow.classList.add("tsa_td_unlinked_selected");
                        setTimeout(function (){  tblRow.classList.remove("tsa_td_unlinked_selected")  }, 1000);
                    };

    //- add hover to tableBody row
                    add_hover(tblRow);
    // - insert td into tblRow
                    const td = tblRow.insertCell(-1);
                    td.innerText = caption_str;
                    td.classList.add("tw_240");
                };
            };
        };
    }; // t_MCOL_FillSelectTable

//=========  MCOL_SelectItem  ================ PR2021-07-07 PR2022-07-21
    function MCOL_SelectItem(tr_clicked) {
        //console.log("===  MCOL_SelectItem == ");
        //console.log("tr_clicked", tr_clicked);
        const is_hidden = (tr_clicked.parentNode.id !== "id_MCOL_tblBody_show");
        //console.log("is_hidden", is_hidden);

        const field_name = get_attr_from_el(tr_clicked, "data-field")

        for (let i = 0, dict; dict = mod_MCOL_dict.columns_excl_skipped[i]; i++) {
            if(dict.field === field_name){
                dict.hidden = !is_hidden;
            };
        };
        t_MCOL_FillSelectTable(field_name);

// - enable save btn
        const el_MCOL_btn_save = document.getElementById("id_MCOL_btn_save")
        el_MCOL_btn_save.disabled = false;

    }  // MCOL_SelectItem

// +++++++++++++++++ END OF MODAL SELECT COLUMNS ++++++++++++++++++++++++++++++++++++++++++

// +++++++++++++++++ SBR SELECT DEPARTMENT ++++++++++++++++++++++++++++++++++++++++++


// +++++++++++++++++ SBR SELECT LEVEL SECTOR ++++++++++++++++++++++++++++++++++++++++++

//=========  t_SBR_select_department  ================  PR2023-07-09
    function t_SBR_select_department(el_select, SBR_department_response, skip_upload) {
        //console.log("===== t_SBR_select_department =====");
        //console.log( "    el_select.value: ", el_select.value, typeof el_select.value)

        // only used in correctors.js, for now,  to be implemented in subjects.js, exam.js, orderlist.js
        // selecting department in hdrbar uses t_MSED_Open, that saves depbase in selected_pk

// - clear datatable, don't delete table header
        const tblBody_datatable = document.getElementById("id_tblBody_datatable");
        if (tblBody_datatable) {tblBody_datatable.innerText = null};

        if (el_select){
// - get new value from el_select
            // value "-9" is 'All departments'
            const sel_pk_int = (el_select.value && Number(el_select.value)) ? Number(el_select.value) : null;

// - put new value in setting_dict
            const tblName = "depbase";
            const sel_pk_key_str = "sel_depbase_pk";
            const code_key_str = "base_code";
            const data_rows = department_rows;

            let selected_dict = null;
            if (data_rows && data_rows.length){
                for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
                    if(data_dict.base_id && data_dict.base_id === sel_pk_int ){
                        selected_dict = data_dict;
                        break;
            }}};
            //console.log( "    selected_dict: ", selected_dict);

            const selected_pk_int = (selected_dict) ? selected_dict.base_id : null;
            const new_sel_code = (selected_dict && selected_dict[code_key_str]) ? selected_dict[code_key_str] : "---";
            setting_dict[sel_pk_key_str] = selected_pk_int;
            setting_dict["sel_depbase_code"] = new_sel_code;

            if (!skip_upload) {
                const selected_pk_dict = {};
                selected_pk_dict[sel_pk_key_str] = selected_pk_int
                const upload_dict = {selected_pk: selected_pk_dict};

        // ---  upload new setting
                b_UploadSettings (upload_dict, urls.url_usersetting_upload);
            };
    //console.log("    selected_pk_int", selected_pk_int);
    //console.log("    selected_dict", selected_dict);
            SBR_department_response(tblName, selected_dict, selected_pk_int);
        };
    };  // t_SBR_select_department

//=========  t_SBR_select_level_sector  ================ PR2021-08-02 PR2023-03-26
    function t_SBR_select_level_sector(tblName, el_select, SBR_lvl_sct_response, skip_upload) {
        //console.log("===== t_SBR_select_level_sector =====");
        //console.log( "    tblName: ", tblName) // tblName = "lvlbase" or "sctbase"
        //console.log( "    el_select.value: ", el_select.value, typeof el_select.value)
        // PR2023-09-01 debug: must return -9 when el_select.value = -9, but returned null
        // solved by adding : const selected_pk_int = (sel_pk_int !== -9) ? -9 :

// - clear tblBody_datatable, don't delete table header
        const tblBody_datatable = document.getElementById("id_tblBody_datatable");
        if (tblBody_datatable) {tblBody_datatable.innerText = null};

        if (el_select && ["lvlbase", "sctbase"].includes (tblName)){
            const is_sctbase = (tblName === "sctbase");

// - get new value from el_select
            const sel_pk_int = (el_select.value && Number(el_select.value)) ? Number(el_select.value) : null;
            // all levels /sectors has value sel_pk_int =  -9 number
    //console.log("    sel_pk_int", sel_pk_int, typeof sel_pk_int);
// - put new value in setting_dict
            const sel_pk_key_str = (is_sctbase) ? "sel_sctbase_pk" : "sel_lvlbase_pk";
            const code_key_str = (is_sctbase) ? "name" : "lvlbase_code";

            const data_rows = (is_sctbase) ? sector_rows : level_rows;

            let selected_dict = null;
            if (sel_pk_int !== -9 && data_rows && data_rows.length){
                for (let i = 0, data_dict; data_dict = data_rows[i]; i++) {
                    if(data_dict.base_id && data_dict.base_id === sel_pk_int ){
                        selected_dict = data_dict;
                        break;
            }}};

            const selected_pk_int = (selected_dict) ? selected_dict.base_id : (sel_pk_int === -9) ? -9 : null;
            const new_sel_code = (selected_dict && selected_dict[code_key_str]) ? selected_dict[code_key_str] : "---";
    //console.log("    selected_pk_int", selected_pk_int);
    //console.log("    new_sel_code", new_sel_code);

            setting_dict[sel_pk_key_str] = selected_pk_int;
            if (is_sctbase) {
                setting_dict["sel_sector_name"] = new_sel_code;
            } else {
                setting_dict["sel_lvlbase_code"] = new_sel_code;
            };

            if (!skip_upload) {
                const selected_pk_dict = {};
                selected_pk_dict[sel_pk_key_str] = selected_pk_int
                const upload_dict = {selected_pk: selected_pk_dict};

        // ---  upload new setting
                b_UploadSettings (upload_dict, urls.url_usersetting_upload);
            };
    //console.log("    selected_pk_int", selected_pk_int);
    //console.log("    selected_dict", selected_dict);
            SBR_lvl_sct_response(tblName, selected_dict, selected_pk_int);
        };
    };  // t_SBR_select_level_sector

//=========  t_SBR_filloptions_level_sector  ================ PR2021-08-02 PR2023-01-11
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
                                        (has_profiel) ? loc.All_profiles : loc.All_sectors ) + "&#62";
        if (!has_items){
             const caption_none = (tblName === "level") ? loc.No_level_found :
                                  (has_profiel) ? loc.No_profiel_found : loc.No_sector_found ;
            display_rows.push({value: 0, caption: caption_none})
        } else {
            if (rows.length === 1){
    // - if only 1 level: make that the selected one
                if (tblName === "level"){
                    setting_dict.sel_lvlbase_pk = rows.base_id;
                } else if (tblName === "sector"){
                    setting_dict.sel_sctbase_pk = rows.base_id
                }
            } else if (rows.length > 1){
    // - add row 'Alle leerwegen' / Alle profielen / Alle sectoren in first row
                display_rows.push({value: -9, caption: caption_all })
            }
            for (let i = 0, row; row = rows[i]; i++) {
                display_rows.push({
                value: row.base_id,
                caption: (tblName === "sector") ? row.name : row.abbrev
                });
            };
        };  // if (!has_items)

    //console.log("display_rows", display_rows);

        const selected_pk = (tblName === "level") ? setting_dict.sel_lvlbase_pk :
                            (tblName === "sector") ? setting_dict.sel_sctbase_pk : -9;
    //console.log("setting_dict", setting_dict);
    //console.log("selected_pk", selected_pk);

        const id_str = (tblName === "level") ? "id_SBR_select_level" :
                        (tblName === "sector") ? "id_SBR_select_sector" : null;
        const el_SBR_select = document.getElementById(id_str);
        t_FillOptionsFromList(el_SBR_select, display_rows, "value", "caption", null, null, selected_pk);

        // put displayed text in setting_dict
        const sel_code = (el_SBR_select.options[el_SBR_select.selectedIndex]) ? el_SBR_select.options[el_SBR_select.selectedIndex].innerText : null;
        if (tblName === "level"){
            setting_dict.sel_lvlbase_code = sel_code;
        } else if (tblName === "sector"){
            setting_dict.sel_sctbase_code = sel_code;
        };
        //console.log("el_SBR_select.parentNode", el_SBR_select.parentNode);
        add_or_remove_class(el_SBR_select.parentNode, cls_hide, !show_select_element);

        const el_SBR_select_showall = document.getElementById("id_SBR_select_showall")
        add_or_remove_class(el_SBR_select_showall, cls_hide, false);

    // - show select level and sector
        if (tblName === "sector"){
            // when label has no id the text is Sector / Profiel, set in .html file
            const el_SBR_select_sector_label = document.getElementById("id_SBR_select_sector_label")
            if(el_SBR_select_sector_label){el_SBR_select_sector_label.innerText = ( (has_profiel) ? loc.Profile : loc.Sector ) + ":"};
        };
    };  // t_SBR_filloptions_level_sector

//=========  t_SBR_show_all  ================ PR2021-08-02 PR2022-03-03 PR2022-12-06 PR2023-01-11
    function t_SBR_show_all(SBR_show_all_response) {
        //console.log("===== t_SBR_show_all =====");
        //console.log("    SBR_show_all_response", SBR_show_all_response);

        // PR2022-06-15 dont reset department
        //setting_dict.sel_depbase_pk = null;
        //setting_dict.sel_depbase_code = null;

        setting_dict.sel_lvlbase_pk = null;
        setting_dict.sel_lvlbase_code = null;

        setting_dict.sel_sctbase_pk = null;
        setting_dict.sel_sctbase_code = null;

        // PR22024-03-29 added:
        setting_dict.sel_subjbase_pk = null;
        setting_dict.sel_subject_pk = null;  // to be deprecated
        setting_dict.sel_subjbase_code = null;
        setting_dict.sel_subject_name = null;

        setting_dict.sel_cluster_pk = null;

        setting_dict.sel_classname = null;

        setting_dict.sel_student_pk = null;
        setting_dict.sel_student_name = null;
        setting_dict.sel_student_name_init = null;

        setting_dict.sel_exam_pk = null;

        //const el_SBR_select_department = document.getElementById("id_SBR_select_department");
        const el_SBR_select_level = document.getElementById("id_SBR_select_level");
        const el_SBR_select_sector = document.getElementById("id_SBR_select_sector");
        const el_SBR_select_subject = document.getElementById("id_SBR_select_subject");
        const el_SBR_select_cluster = document.getElementById("id_SBR_select_cluster");
        const el_SBR_select_class = document.getElementById("id_SBR_select_class");
        const el_SBR_select_student = document.getElementById("id_SBR_select_student");

        //if (el_SBR_select_department){ el_SBR_select_department.value = null};
        if (el_SBR_select_level){ el_SBR_select_level.value = -9}; // -9 is value of 'all levels'
        if (el_SBR_select_sector){ el_SBR_select_sector.value = -9}; // -9 is value of 'all levels'

        if (el_SBR_select_class){ el_SBR_select_class.value = "0"};

        t_SBR_display_subject_cluster_student();

// ---  upload new setting
        const upload_dict = {selected_pk: {
            //sel_depbase_pk: null,
            sel_lvlbase_pk: null,
            sel_sctbase_pk: null,
            sel_classname: null,

            sel_subjbase_pk: null, // PR2024-03-29 added
            sel_subject_pk: null, //  PR2024-03-29to be deprecated
            sel_cluster_pk: null,
            sel_student_pk: null
            }};

    //console.log( " upload_dict", upload_dict);
        b_UploadSettings (upload_dict, urls.url_usersetting_upload);

        SBR_show_all_response();
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