//PR2024-06-14
document.addEventListener("DOMContentLoaded", function() {
    "use strict";

// ---  HEADER BAR ------------------------------------

    const el_hdrbar_auth1 = document.getElementById("id_hdrbar_auth1");
    if (el_hdrbar_auth1) {el_hdrbar_auth1.addEventListener("click", function() {h_AUTH_Change(el_hdrbar_auth1)}, false)};
    const el_hdrbar_auth2 = document.getElementById("id_hdrbar_auth2");
    if (el_hdrbar_auth2) {el_hdrbar_auth2.addEventListener("click", function() {h_AUTH_Change(el_hdrbar_auth2)}, false)};
    const el_hdrbar_auth3 = document.getElementById("id_hdrbar_auth3");
    if (el_hdrbar_auth3) {el_hdrbar_auth3.addEventListener("click", function() {h_AUTH_Change(el_hdrbar_auth3)}, false)};
    const el_hdrbar_auth4 = document.getElementById("id_hdrbar_auth4");
    if (el_hdrbar_auth4) {el_hdrbar_auth4.addEventListener("click", function() {h_AUTH_Change(el_hdrbar_auth4)}, false)};

//=========  h_AUTH_Change  ================ PR2024-06-14
    function h_AUTH_Change(el_item) {
        //console.log( "===== h_AUTH_Change ========= ");
        //console.log( "el_item", el_item);

        const id_str = el_item.id.slice(-1);
        const new_auth_index = parseInt(id_str,10);

        if (new_auth_index !== setting_dict.sel_auth_index){
            let el_data = document.getElementById("id_data");
            if (el_data) {
                const url_usersetting_upload = get_attr_from_el(el_data, "data-url_usersetting_upload");

    // ---  upload new setting
                const upload_dict = {selected_pk: {sel_auth_index: new_auth_index}};
//console.log( "upload_dict", upload_dict);
                b_UploadSettings (upload_dict, url_usersetting_upload);
    // ---  update setting_dict
                setting_dict.sel_auth_index = new_auth_index;
    // ---  update el_hdrbar_function
                const el_hdrbar_function = document.getElementById("id_hdrbar_function");
                if (el_hdrbar_function) {
                    el_hdrbar_function.innerText = el_item.innerText;
                };
    // ---  update selected in dropdown list
                const el_hdrbar_dropdown_auth = document.getElementById("id_hdrbar_dropdown_auth")
                if(el_hdrbar_dropdown_auth){
                    const items = el_hdrbar_dropdown_auth.children;
                    for (let i = 0, el; el = items[i]; i++) {
                        const is_selected = (el.id === el_item.id);
                        add_or_remove_class(el, "tsa_tr_selected", is_selected);
                    };
                };
            };
        };
    };
});

// keep outside document.addEventListener("DOMContentLoaded", function()

//========= UpdateHeaderbar  ================== PR2020-11-14 PR2020-12-02 PR2023-01-08 PR2024-06-25
//PR2024-06-25  moved from base.js
function h_UpdateHeaderBar(el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school){
    //console.log(" --- h_UpdateHeaderBar ---" )
    //console.log("    setting_dict", setting_dict )
    //console.log("    permit_dict", permit_dict )

// --- EXAM YEAR
    if(el_hdrbar_examyear) {
        let examyer_txt = "";
        if (setting_dict.sel_examyear_pk){
           examyer_txt = loc.Examyear + " " + setting_dict.sel_examyear_code
        } else {
            // there is always an examyear selected, unless table is empty
            examyer_txt = "<" + loc.No_examyears + ">"
        }
        el_hdrbar_examyear.innerText = examyer_txt;

// add pointer on hover when there are multiple examyears
        // PR2023-01-08 user may have only one allowed_examyear,
        add_or_remove_class(el_hdrbar_examyear, "awp_navbaritem_may_select", permit_dict.may_select_examyear, "awp_navbar_item" );
    };
    // PR2023-04-12 show / hide padlock in headerbar
    const el_hdrbar_examyear_locked = document.getElementById("id_hdrbar_examyear_locked");
    if (el_hdrbar_examyear_locked){
        add_or_remove_class(el_hdrbar_examyear_locked.children[0], "stat_0_6", setting_dict.sel_examyear_locked,"stat_0_0" );
    };

// --- DEPARTMENT
    if(el_hdrbar_department) {
        const display_department = (!!permit_dict.display_department);

//console.log("    display_department", display_department )
//console.log("    permit_dict.allowed_depbases", permit_dict.allowed_depbases )
        const allowed_depbases_count = (permit_dict.allowed_depbases) ? permit_dict.allowed_depbases.length : 0
        //PR2023-06-14 debug: must get may_select_department from permit_dict
        // was: const may_select_department = (display_department && allowed_depbases_count > 1);
        const may_select_department = (display_department && permit_dict.may_select_department);

//console.log("    allowed_depbases_count", allowed_depbases_count )
//console.log("    may_select_department", may_select_department )
        add_or_remove_class(el_hdrbar_department, cls_hide, !display_department)
        // add pointer on hover when tehere are multiple departments
        add_or_remove_class(el_hdrbar_department, "awp_navbaritem_may_select", may_select_department, "awp_navbar_item" )

        let department_txt = null;
        if (display_department) {
            if (!setting_dict.sel_depbase_pk){
                if (may_select_department) {
                    department_txt = " <" + loc.Select_department + ">";
                } else if (allowed_depbases_count === 0) {
                    department_txt = " <" + loc.School_has_no_departments + ">";
                } else {
                    department_txt = " <" + loc.No_department_selected + ">"
                }
            } else {
                if (!setting_dict.sel_examyear_pk) {
                    department_txt = " <" + loc.No_examyear_selected + ">"
                } else {
                    if (!setting_dict.sel_department_pk){
                        department_txt = " <" + loc.department_notfound_thisexamyear + ">"
                    } else {
                        department_txt = " " + setting_dict.sel_depbase_code
                    };
                };
            };
        };
        el_hdrbar_department.innerText = department_txt;
    };
// --- SCHOOL
    if(el_hdrbar_school) {

        // when display_requsrschool = True the organization of the user is shown, not the selected school
        //  Note: this must also be set in get_headerbar_param
        const display_requsrschool = ['page_user', 'page_subject', 'page_examyear', 'page_school', 'page_corrector',
                                            'page_exampaper', 'page_archive', 'page_orderlist'].includes(setting_dict.sel_page);

        const display_school = true; //  (!!permit_dict.display_school);
        const may_select_school = (display_school && permit_dict.may_select_school && !display_requsrschool);

        add_or_remove_class(el_hdrbar_school, cls_hide, !display_school)
        // set hover when user has permit to goto different school.
        add_or_remove_class(el_hdrbar_school, "awp_navbaritem_may_select", may_select_school, "awp_navbar_item" )

        let schoolname_txt = null;
        if (display_requsrschool) {
            schoolname_txt = permit_dict.requsr_schoolbase_code + " " + permit_dict.requsr_school_name;

        } else if (!setting_dict.sel_schoolbase_pk){
            if (permit_dict.may_select_school) {
                schoolname_txt = " <" + loc.Select_school + ">";
            } else {
                schoolname_txt = " <" + loc.No_school + ">";
            };
        } else {
            schoolname_txt = setting_dict.sel_schoolbase_code;
            if (!setting_dict.sel_examyear_pk) {
                schoolname_txt += " <" + loc.No_examyear_selected + ">"
            } else {
                if (!setting_dict.sel_school_pk){
                    schoolname_txt += " <" + loc.School_notfound_thisexamyear + ">"
                } else {
                    schoolname_txt += " " + setting_dict.sel_school_name
                };
            };
        };
        el_hdrbar_school.innerText = schoolname_txt;
    };

// --- FUNCTION
    const el_hdrbar_function = document.getElementById("id_hdrbar_function");

    if(el_hdrbar_function) {

// ---  update function text in  el_hdrbar_function
        const function_names = [null, loc.Chairperson, loc.Secretary, loc.Examiner, loc.Second_corrector];
        const sel_auth_function = (setting_dict.sel_auth_index && function_names[setting_dict.sel_auth_index]) ?
                                    function_names[setting_dict.sel_auth_index] : "";

        let has_auth = false;
// ---  update dropdown list
        const el_hdrbar_dropdown_auth = document.getElementById("id_hdrbar_dropdown_auth")
        if(el_hdrbar_dropdown_auth){
            for (let i = 1; i < 5; i++) {
                const el_dropdown_item = document.getElementById("id_hdrbar_auth" + i);
                if (el_dropdown_item){
    // hide item if it is not in the auth ist
                    const is_auth = (permit_dict.usergroup_list &&  permit_dict.usergroup_list.includes("auth" + i));
                    add_or_remove_class(el_dropdown_item, "display_hide", !is_auth);
                    if (is_auth) {has_auth = true};
    // show selected if is selected
                    const is_selected = (setting_dict.sel_auth_index === i);
                    add_or_remove_class(el_dropdown_item, "tsa_tr_selected", is_selected);
                };
            };
        };
    // hide function when user has no functions
        //PR2024-06-27 dont show function in page user - also set in get_headerbar_param
        //if (setting_dict.sel_page === "page_user"){ has_auth = false};
        add_or_remove_class(el_hdrbar_function.parentNode, "display_hide", !has_auth);
        el_hdrbar_function.innerText = sel_auth_function;

    //console.log("    has_auth", has_auth )
    //console.log("    sel_auth_function", sel_auth_function )
    };
};  // h_UpdateHeaderBar
