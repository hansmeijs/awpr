// PR2023-02-14
// ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    "use strict";

    console.log("+++++++ DOMContentLoaded 'modallowed'")

// +++++++++ MOD USER ALLOWED SECTIONS SUBJECTS ++++++++++++++++ PR2022-10-23 PR2022-11-21 PR2022-12-04 PR2023-01-06
    function t_MUPS_Open(el_input){
        console.log(" -----  t_MUPS_Open   ---- ")
        console.log("  permit_dict: ", permit_dict);
        console.log("  mod_MUPS_dict: ", mod_MUPS_dict);

        let data_dict = {}, user_pk = null, user_role = null;
        let user_schoolbase_pk = null, user_schoolbase_code = null, user_mapid = null;
        let user_allowed_sections = {};
        let modifiedat = null, modby_username = null;
        // el_input is undefined when opened from headerbar
        if(!el_input && !permit_dict.allowed_sections && !permit_dict.allowed_subjbases){
                b_show_mod_message_html(["<p class='p-2'>",
                loc.All_sections_are_allowed, "</p>"].join(""));
        } else {
            if(!el_input ){
                if(!isEmpty(permit_dict)){
                    mod_MUPS_dict = {
                        may_edit: false,
                        user_pk: permit_dict.requsr_pk,
                        user_role: permit_dict.requsr_role,
                        user_schoolbase_pk: permit_dict.requsr_schoolbase_pk,
                        user_schoolbase_code: permit_dict.requsr_schoolbase_code,
                        user_schoolname: permit_dict.requsr_schoolbase_code,
                        user_mapid: null,
                        allowed_sections: permit_dict.allowed_sections,
                        username: permit_dict.requsr_name,
                        last_name: permit_dict.requsr_name,
                        requsr_same_school: permit_dict.requsr_same_school,
                        expanded: {}
                        };
                console.log("    mod_MUPS_dict: ", mod_MUPS_dict);
                };
            } else {

                const tblRow = t_get_tablerow_selected(el_input);
                user_mapid = tblRow.id;

    // --- get existing data_dict from data_rows
                data_dict = get_datadict_from_mapid(tblRow.id);
                if(!isEmpty(data_dict)){
                    user_pk = data_dict.id;
                    user_role = data_dict.role;
                    user_schoolbase_pk = data_dict.schoolbase_id;
                    user_schoolbase_code = data_dict.sb_code;
                    user_allowed_sections = (data_dict.allowed_sections) ? data_dict.allowed_sections : {};

                    modifiedat= data_dict.modifiedat;
                    modby_username = data_dict.modby_username;
                };

        console.log("  data_dict: ", data_dict);

            selected_user_pk = user_pk;

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
        console.log("    mod_MUPS_dict: ", mod_MUPS_dict);

            };

    // - create ordered list of all schools with schoolbase.role = c.ROLE_008_SCHOOL:
            t_MUPS_CreateSchoolDepLvlSubjlist();

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


            const el_MUPS_username = document.getElementById("id_MUPS_username");
            console.log(" el_MUPS_username", el_MUPS_username);
            if (el_MUPS_username) {el_MUPS_username.value = mod_MUPS_dict.last_name};

            const el_MUPS_loader = document.getElementById("id_MUPS_loader");
            add_or_remove_class(el_MUPS_loader, cls_hide, true);
            const el_MUPS_tbody_container = document.getElementById("id_MUPS_tbody_container");

            add_or_remove_class( el_MUPS_tbody_container, cls_hide, false);

            const el_MUPS_btn_expand_all = document.getElementById("id_MUPS_btn_expand_all");
            if (el_MUPS_btn_expand_all) {add_or_remove_class(el_MUPS_btn_expand_all.parentNode, cls_hide, false)};

    // ---  fill selecttable
            t_MUPS_FillSelectTable();

    // ---  expand all rows
            t_MUPS_ExpandCollapse_all();
    // ---  show modal
            $("#id_mod_userallowedsection").modal({backdrop: true});
        };
    };  // t_MUPS_Open

//========= t_MUPS_Save  ============= PR2022-11-04
    function t_MUPS_Save(mode, el_input){
        console.log(" ----- t_MUPS_Save ---- mode: ", mode);

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
    };  // t_MUPS_Save

//========= t_MUPS_CreateSchoolDepLvlSubjlist  ============= PR2022-11-04
    function t_MUPS_CreateSchoolDepLvlSubjlist() {
        console.log("===== t_MUPS_CreateSchoolDepLvlSubjlist ===== ");

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

    console.log("    mod_MUPS_dict.sorted_school_list", mod_MUPS_dict.sorted_school_list);
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
    console.log("    mod_MUPS_dict.sorted_department_list", mod_MUPS_dict.sorted_department_list);

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
    console.log("    mod_MUPS_dict.sorted_level_list", mod_MUPS_dict.sorted_level_list);

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
    console.log("    mod_MUPS_dict.sorted_subject_list", mod_MUPS_dict.sorted_subject_list);

    }; // t_MUPS_CreateSchoolDepLvlSubjlist

//========= t_MUPS_FillSelectTable  ============= PR2022-10-24 PR2023-01-06
    function t_MUPS_FillSelectTable() {
        console.log("===== t_MUPS_FillSelectTable ===== ");

        const data_rows = school_rows;

        const el_MUPS_tbody_select = document.getElementById("id_MUPS_tbody_select");
        el_MUPS_tbody_select.innerText = null;

// ---  loop through mod_MUPS_dict.sorted_school_list
        if(mod_MUPS_dict.sorted_school_list.length){
        console.log(" >>>>>>>>>>>>   mod_MUPS_dict.sorted_school_list ", mod_MUPS_dict.sorted_school_list);

            if (mod_MUPS_dict.may_edit) {

                // Select school only allowed if req_usr and user have both role greater than ROLE_008_SCHOOL PR2023-01-26
                const select_schools_allowed = (permit_dict.requsr_role > 8 && mod_MUPS_dict.user_role > 8) // ROLE_008_SCHOOL}

        console.log(" >>>>>>>>>>>>   select_schools_allowed ", select_schools_allowed);
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
                        t_MUPS_CreateTblrowSchool(el_MUPS_tbody_select, addnew_dict);
                    };
                };
            };
        console.log("    mod_MUPS_dict.allowed_sections", mod_MUPS_dict.allowed_sections);

 // ---  add selected schools to table
        console.log("    mod_MUPS_dict.sorted_school_list", mod_MUPS_dict.sorted_school_list);
        console.log("    mod_MUPS_dict.allowed_sections", mod_MUPS_dict.allowed_sections);
        console.log("    mod_MUPS_dict.sorted_school_list", mod_MUPS_dict.sorted_school_list);
            for (let i = 0, sb_pk_str, school_dict; school_dict = mod_MUPS_dict.sorted_school_list[i]; i++) {
        console.log("    school_dict", school_dict);
                //sb_pk_str = (school_dict.base_id) ? school_dict.base_id.toString() : "0"
                if(mod_MUPS_dict.allowed_sections && school_dict.base_id.toString() in mod_MUPS_dict.allowed_sections){
                    t_MUPS_CreateTblrowSchool(el_MUPS_tbody_select, school_dict);
                };
            };
        };
    }; // t_MUPS_FillSelectTable

    function t_MUPS_CreateTblrowSchool(el_MUPS_tbody_select, school_dict) {
        console.log("-----  t_MUPS_CreateTblrowSchool   ----");
        console.log("    school_dict", school_dict);
        // PR2022-11-05

// ---  get info from school_dict
        const schoolbase_pk = school_dict.base_id;
        const code = (school_dict.sb_code) ? school_dict.sb_code : "";
        const name = (school_dict.name) ? school_dict.name : "";
        const depbases = (school_dict.depbases) ? school_dict.depbases : null;
        //console.log("    depbases", depbases);

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
                td.addEventListener("click", function() {t_MUPS_SelectSchool(tblRow)}, false);
            } else {
                td.addEventListener("click", function() {t_MUPS_SelectSchool(tblRow)}, false);
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
                td.addEventListener("click", function() {t_MUPS_DeleteTblrow(tblRow)}, false);

                td.appendChild(el_div);
            };
// ---  add department rows
            const expanded_schoolbase_dict = mod_MUPS_dict.expanded[schoolbase_pk.toString()];

        console.log("    schoolbase_pk", schoolbase_pk);
        console.log("    >>>> mod_MUPS_dict.expanded", mod_MUPS_dict.expanded);
        console.log("    expanded_schoolbase_dict", expanded_schoolbase_dict);
            let show_item = false;
            if (expanded_schoolbase_dict) {
                show_item = expanded_schoolbase_dict.expanded
            };

        console.log("    show_item", show_item);
            if (show_item){
                t_MUPS_CreateTableDepartment(school_dict);
            };
        };
    };  // t_MUPS_CreateTblrowSchool

    function t_MUPS_CreateTableDepartment(school_dict) { // PR2022-11-04
        console.log("===== t_MUPS_CreateTableDepartment ===== ");
    console.log("    school_dict", school_dict);

// ---  get info from school_dict
        const schoolbase_pk = school_dict.base_id;
        const schoolbase_pk_str = schoolbase_pk.toString();

        const sb_depbases = (school_dict.depbases) ? school_dict.depbases : "";
        const sb_depbases_arr = (school_dict.depbases) ? school_dict.depbases.split(";") : [];
    console.log("  !!!!  sb_depbases", sb_depbases);
    console.log("  @@@@@@@  sb_depbases_arr", sb_depbases_arr);

// -  get allowed_depbases from this school from mod_MUPS_dict.allowed_sections
        const allowed_depbases = (mod_MUPS_dict.allowed_sections && schoolbase_pk_str in mod_MUPS_dict.allowed_sections) ?  mod_MUPS_dict.allowed_sections[schoolbase_pk_str] : {};
    console.log("    allowed_depbases", allowed_depbases);

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
    console.log("    has_unselected_departments", has_unselected_departments);
            if (has_unselected_departments){
                const addnew_dict = {base_id: -1, name: "< " + loc.Add_department + " >"};
                t_MUPS_CreateTblrowDep(addnew_dict, schoolbase_pk, sb_depbases, false); // allow_delete = false
            };
        };
    console.log("   ????  mod_MUPS_dict.sorted_department_list", mod_MUPS_dict.sorted_department_list);

// add rows with department if there is only 1
        if (sb_depbases_arr.length === 1){
    console.log("  ?????????   sb_depbases_arr", sb_depbases_arr);
// add rows with the only department of s to school
            for (let i = 0, dep_dict; dep_dict = mod_MUPS_dict.sorted_department_list[i]; i++) {
    console.log("  ?????????   dep_dict", dep_dict);
                if (sb_depbases_arr.includes(dep_dict.base_id.toString())){
    console.log("  ?????????   sb_depbases_arr.includes(dep_dict.base_id", dep_dict.base_id);
                    t_MUPS_CreateTblrowDep(dep_dict, schoolbase_pk, sb_depbases, false); // allow_delete = false
                };
            };

        } else if (mod_MUPS_dict.sorted_department_list.length > 1){
//console.log("    mod_MUPS_dict.sorted_department_list", mod_MUPS_dict.sorted_department_list);

// add rows with selected departments to school
            for (let i = 0, dep_dict; dep_dict = mod_MUPS_dict.sorted_department_list[i]; i++) {
                if (dep_dict.base_id.toString() in allowed_depbases){
                    t_MUPS_CreateTblrowDep(dep_dict, schoolbase_pk, sb_depbases, true); // allow_delete = true
                };
            };
        };
    };  // t_MUPS_CreateTableDepartment

    function t_MUPS_CreateTblrowDep(department_dict, schoolbase_pk, sb_depbases, allow_delete) {
        console.log("===== t_MUPS_CreateTblrowDep ===== ");
        //console.log("    department_dict", department_dict);
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

// ---  add level rows
        if (depbase_pk !== -1){
            let is_expanded = false;
            const expanded_schoolbase_dict = mod_MUPS_dict.expanded[schoolbase_pk.toString()];
             if (expanded_schoolbase_dict) {
                const expanded_depbase_dict = expanded_schoolbase_dict[depbase_pk.toString()];
                if (expanded_depbase_dict) {
                    is_expanded = expanded_depbase_dict.expanded;
            }};

            if (is_expanded) {
                if (lvl_req) {
                    t_MUPS_CreateTableLevel(department_dict, schoolbase_pk);
                } else {
                    // in Havo Vwo there is no level, use lvlbase_pk = -9 to show all subjects PR2022-22-21
                    t_MUPS_CreateTableSubject(-9, depbase_pk, schoolbase_pk);
                };
            };
        };
    };  // t_MUPS_CreateTblrowDep

//========= t_MUPS_CreateTableLevel  =============
    function t_MUPS_CreateTableLevel(dep_dict, schoolbase_pk) { // PR2022-11-06
        console.log("===== t_MUPS_CreateTableLevel ===== ");
        console.log("    dep_dict", dep_dict);

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
                    t_MUPS_CreateTblrowLvl(addnew_dict, depbase_pk, schoolbase_pk, false); // allow_delete = false
                };

                for (let i = 0, lvlbase_pk_str, level_dict; level_dict = mod_MUPS_dict.sorted_level_list[i]; i++) {
                    lvlbase_pk_str = level_dict.base_id.toString();
                    if(lvlbase_pk_str in allowed_lvlbases){
                        t_MUPS_CreateTblrowLvl(level_dict, depbase_pk, schoolbase_pk, true);
                    };
                };
            };
        };
    };  // t_MUPS_CreateTableLevel

//========= t_MUPS_CreateTblrowLvl  =============
    function t_MUPS_CreateTblrowLvl(level_dict, depbase_pk, schoolbase_pk, allow_delete) { // PR2022-11-05
        console.log("===== t_MUPS_CreateTblrowLvl ===== ");
        console.log("  level_dict", level_dict);

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
                t_MUPS_CreateTableSubject(lvlbase_pk, depbase_pk, schoolbase_pk);
            };
        };
    };  // t_MUPS_CreateTblrowLvl

//========= t_MUPS_CreateTableSubject  ============= PR2022-11-05
    function t_MUPS_CreateTableSubject(lvlbase_pk, depbase_pk, schoolbase_pk) { // PR2022-11-05
        //console.log("===== t_MUPS_CreateTableSubject ===== ");
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
            t_MUPS_CreateTblrowSubject(addnew_dict, lvlbase_pk, depbase_pk, schoolbase_pk);
        };
// ---  loop through mod_MUPS_dict.sorted_subject_list
        if(mod_MUPS_dict.sorted_subject_list.length ){
            for (let i = 0, subject_dict; subject_dict = mod_MUPS_dict.sorted_subject_list[i]; i++) {
                if (subject_dict.depbase_id_arr.includes(depbase_pk)){

                    // add when lvlbase_pk is in lvlbase_id_arr or when lvlbase_pk = -9 ('all levels')
                    if (subject_dict.lvlbase_id_arr.includes(lvlbase_pk) || lvlbase_pk === -9){
                        if (allowed_subjbase_arr && allowed_subjbase_arr.includes(subject_dict.base_id)){
                            t_MUPS_CreateTblrowSubject(subject_dict, lvlbase_pk, depbase_pk, schoolbase_pk);
                        };
                    };
                };
            };
        };
    };  // t_MUPS_CreateTableSubject

//========= t_MUPS_CreateTblrowSubject  =============
    function t_MUPS_CreateTblrowSubject(subject_dict, lvlbase_pk, depbase_pk, schoolbase_pk) {
    // PR2022-11-05
        //console.log("===== t_MUPS_CreateTblrowSubject ===== ");
        //console.log("subject_dict", subject_dict);

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
    };  // t_MUPS_CreateTblrowSubject

    function t_MUPS_SelectSchool(tblRow ) {
        //console.log(" -----  t_MUPS_SelectSchool   ----");
        const tblName = get_attr_from_el(tblRow, "data-table");
        const pk_int = get_attr_from_el_int(tblRow, "data-schoolbase_pk");

        //console.log("    tblRow", tblRow);
        //console.log("    pk_int", pk_int);
        //console.log("    tblName", tblName);
        //console.log("    mod_MUPS_dict.allowed_sections", mod_MUPS_dict.allowed_sections);

// ---  get unselected_school_list
        const unselected_school_list = t_MUPS_get_unselected_school_list();
        //console.log("    unselected_school_list", unselected_school_list);

        t_MSSSS_Open(loc, "school", unselected_school_list, false, false, setting_dict, permit_dict, t_MUPS_SelectSchool_Response);
    };

    function t_MUPS_SelectDepartment(tblRow ) {
        //console.log(" -----  t_MUPS_SelectDepartment   ----");
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
        console.log("  @@@>>>>   mod_MUPS_dict.sorted_department_list", mod_MUPS_dict.sorted_department_list);
        if(mod_MUPS_dict.sorted_department_list.length ){
            for (let i = 0, depbase_pk_str, data_dict; data_dict = mod_MUPS_dict.sorted_department_list[i]; i++) {
                depbase_pk_str = (data_dict.base_id) ? data_dict.base_id.toString() : "0";
        console.log("  @@@  depbase_pk_str", depbase_pk_str);
        console.log("    sb_depbases_arr", sb_depbases_arr);
                if ( (sb_depbases_arr && sb_depbases_arr.includes(depbase_pk_str)) || (depbase_pk_str === "-9")  ){
        console.log("    allowed_depbases", allowed_depbases);
                    if(isEmpty(allowed_depbases) || !(depbase_pk_str in allowed_depbases)){
                        unselected_dep_list.push(data_dict);
            }}};
        };
        //console.log("  ????  unselected_dep_list", unselected_dep_list);
        t_MSED_OpenDepLvlFromRows(tblName, unselected_dep_list, schoolbase_pk, null, t_MUPS_DepFromRows_Response)

    };  // t_MUPS_SelectDepartment

    function t_MUPS_SelectLevel(tblRow ) {
        //console.log(" -----  t_MUPS_SelectLevel   ----");
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
        t_MSED_OpenDepLvlFromRows(tblName, unselected_level_list, schoolbase_pk, depbase_pk, t_MUPS_LvlFromRows_Response)
    };  // t_MUPS_SelectLevel

    function t_MUPS_SelectSubject(tblRow ) {
        //console.log(" -----  t_MUPS_SelectSubject   ----");
        //console.log("    tblRow", tblRow);

        const schoolbase_pk = get_attr_from_el_int(tblRow, "data-schoolbase_pk");
        const depbase_pk = get_attr_from_el_int(tblRow, "data-depbase_pk");
        const lvlbase_pk = get_attr_from_el_int(tblRow, "data-lvlbase_pk");

        mod_MUPS_dict.sel_schoolbase_pk_str = schoolbase_pk.toString();
        mod_MUPS_dict.sel_depbase_pk_str = depbase_pk.toString();
        mod_MUPS_dict.sel_lvlbase_pk_str = lvlbase_pk.toString();

// ---  get unselected_subject_list
        const unselected_subject_list = t_MUPS_get_unselected_subject_list(schoolbase_pk, depbase_pk, lvlbase_pk);

        //console.log("    unselected_subject_list", unselected_subject_list);
        t_MSSSS_Open(loc, "subject", unselected_subject_list, false, false, {}, permit_dict, t_MUPS_SelectSubject_Response);

    };  // t_MUPS_SelectSubject

    function t_MUPS_get_unselected_school_list() {
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

    function t_MUPS_get_unselected_subject_list(schoolbase_pk, depbase_pk, lvlbase_pk) { //PR2022-11-07
        //console.log(" -----  t_MUPS_get_unselected_subject_list   ----");
        //console.log("    lvlbase_pk", lvlbase_pk);
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

        //console.log("    allowed_lvlbase", allowed_lvlbase);
            for (let i = 0, subjectbase_pk_str, data_dict; data_dict = mod_MUPS_dict.sorted_subject_list[i]; i++) {
        // check if subject exists in this dep and level
                if (data_dict.depbase_id_arr.includes(depbase_pk)) {
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

    function t_MUPS_DeleteTblrow(tblRow ) {
        console.log(" ###########-----  t_MUPS_DeleteTblrow   ----");
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

        t_MUPS_FillSelectTable() ;
    };  // t_MUPS_DeleteTblrow

    function t_MUPS_LvlFromRows_Response(sel_lvlbase_pk, schoolbase_pk, depbase_pk) {
        console.log(" -----  t_MUPS_LvlFromRows_Response   ----");
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

        t_MUPS_FillSelectTable();
    };

    function t_MUPS_DepFromRows_Response(sel_depbase_pk, schoolbase_pk, depbase_pkNIU) {
        console.log(" -----  t_MUPS_DepFromRows_Response   ----");
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
        t_MUPS_FillSelectTable();
    };

//=========  t_MUPS_SelectSchool_Response  ================ PR2022-10-26 PR2022-11-21
    function t_MUPS_SelectSchool_Response(tblName, selected_dict, selected_pk) {
        console.log( "===== t_MUPS_SelectSchool_Response ========= ");
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
            t_MUPS_FillSelectTable();
        };
    }  // t_MUPS_SelectSchool_Response

//=========  t_MUPS_SelectSubject_Response  ================ PR2022-10-26 PR2022-11-21
    function t_MUPS_SelectSubject_Response(tblName, selected_dict, selected_pk) {
        console.log( "===== t_MUPS_SelectSubject_Response ========= ");
        console.log( "    tblName", tblName);
        console.log( "    selected_dict", selected_dict);
        console.log( "    selected_pk", selected_pk, typeof selected_pk);

        // Note: when tblName = school: pk_int = schoolbase_pk
        if (selected_pk === -1) { selected_pk = null};
        if (selected_pk){
            const selected_pk_str = selected_pk.toString();

            const subjbase_pk = selected_dict.base_id;
            if (subjbase_pk){
                const allowed_sections = (mod_MUPS_dict.allowed_sections) ? mod_MUPS_dict.allowed_sections : {};
                const allowed_depbases = (mod_MUPS_dict.sel_schoolbase_pk_str in allowed_sections) ? allowed_sections[mod_MUPS_dict.sel_schoolbase_pk_str] : {};
                const allowed_lvlbases = (mod_MUPS_dict.sel_depbase_pk_str in allowed_depbases) ? allowed_depbases[mod_MUPS_dict.sel_depbase_pk_str] : {};

                // allowed_subjbase_arr contains integers, not strings PR2022-12-04
                const allowed_subjbase_arr = (mod_MUPS_dict.sel_lvlbase_pk_str in allowed_lvlbases) ? allowed_lvlbases[mod_MUPS_dict.sel_lvlbase_pk_str] : [];

                if (allowed_subjbase_arr && !allowed_subjbase_arr.includes(subjbase_pk)){
                        allowed_subjbase_arr.push(subjbase_pk);
                };
            };

    // ---  fill selecttable
            t_MUPS_FillSelectTable();
        };
    }  // t_MUPS_SelectSubject_Response

//=========  t_MUPS_MessageClose  ================ PR2022-10-26
    function t_MUPS_MessageClose() {
        console.log(" --- t_MUPS_MessageClose --- ");

        $("#id_mod_userallowedsection").modal("hide");
    }  // t_MUPS_MessageClose

    function t_MUPS_ExpandTblrows(tblRow ) {
        console.log("-----  t_MUPS_ExpandTblrows   ----");
        console.log("    tblRow", tblRow);

        const tblName = get_attr_from_el(tblRow, "data-table");
        console.log("    tblName", tblName);

        const schoolbase_pk = get_attr_from_el_int(tblRow, "data-schoolbase_pk");
        if (schoolbase_pk){
            const schoolbase_pk_str = schoolbase_pk.toString();
            if (!(schoolbase_pk_str in mod_MUPS_dict.expanded)){
                mod_MUPS_dict.expanded[schoolbase_pk_str] = {expanded: false};
            };
            const expanded_school_dict = mod_MUPS_dict.expanded[schoolbase_pk_str];

            if (tblName === "school"){
                expanded_school_dict.expanded = !expanded_school_dict.expanded;
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

        console.log("    mod_MUPS_dict.expanded", mod_MUPS_dict.expanded);
            t_MUPS_FillSelectTable();
        };
    };  // t_MUPS_ExpandTblrows

    function t_MUPS_ExpandCollapse_all(){
     // PR2022-11-06
        console.log("===== t_MUPS_ExpandCollapse_all ===== ");
        console.log("    mod_MUPS_dict.allowed_sections", mod_MUPS_dict.allowed_sections);
        const is_expand = !mod_MUPS_dict.expand_all;

        mod_MUPS_dict.expand_all = is_expand;
        // remove all expanded items when setting 'Collapse_all'
        if (!is_expand){
            mod_MUPS_dict.expanded = {};
        };

        console.log("    mod_MUPS_dict.expand_all", mod_MUPS_dict.expand_all);

        const el_MUPS_btn_expand_all = document.getElementById("id_MUPS_btn_expand_all");
        el_MUPS_btn_expand_all.innerText = (is_expand) ? loc.Collapse_all : loc.Expand_all;

// ---  loop through mod_MUPS_dict.allowed_sections and expand all items
        for (const [schoolbase_pk_str, allowed_schoolbase] of Object.entries(mod_MUPS_dict.allowed_sections)) {
            if (!(schoolbase_pk_str in mod_MUPS_dict.expanded)){
                mod_MUPS_dict.expanded[schoolbase_pk_str] = {};
            }
            const expanded_schoolbase = mod_MUPS_dict.expanded[schoolbase_pk_str];
            expanded_schoolbase.expanded = is_expand;
        console.log("    expanded_schoolbase", expanded_schoolbase);

            for (const [depbase_pk_str, allowed_depbase] of Object.entries(allowed_schoolbase)) {
                if (!(depbase_pk_str in expanded_schoolbase)){
                    expanded_schoolbase[depbase_pk_str] = {};
                }
                const expanded_depbase = expanded_schoolbase[depbase_pk_str];
                expanded_depbase.expanded = is_expand;
        console.log("    expanded_depbase", expanded_depbase);

                for (const [lvlbase_pk_str, allowed_lvlbases] of Object.entries(allowed_depbase)) {
                    if (!(lvlbase_pk_str in expanded_depbase)){
                        expanded_depbase[lvlbase_pk_str] = {};
                    }
                    const expanded_lvlbase = expanded_depbase[lvlbase_pk_str];
                    expanded_lvlbase.expanded = is_expand;
                };
            };
        };
        console.log(">>>>>>>>> mod_MUPS_dict.expanded", mod_MUPS_dict.expanded);

        t_MUPS_FillSelectTable();
    };  // t_MUPS_ExpandCollapse_all

// +++++++++ END OF MOD USER PERMIT SECTIONS ++++++++++++++++ PR20220-10-23

// ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
