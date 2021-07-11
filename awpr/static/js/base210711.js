    "use strict";

// ============================
    // add csrftoken to ajax header to prevent error 403 Forbidden PR2018-12-03
    // from https://docs.djangoproject.com/en/dev/ref/csrf/#ajax
    const csrftoken = Cookies.get('csrftoken');

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    // PR2018-12-02 from: https://github.com/js-cookie/js-cookie/tree/latest#readme
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

//========= SUBMENU ==================================
//========= SetMenubuttonActive  ====================================
    function SetMenubuttonActive(btn_clicked) {
        "use strict";
        // PR2019-03-03 function highlights clicked menubutton

// ---  get clicked button
        if(btn_clicked) {
            let menubar = btn_clicked.parentNode

// ---  remove class 'active' from all buttons in this menubar
            let menubuttons = menubar.children;
            for (let i = 0, len = menubuttons.length; i < len; i++) {
              menubuttons[i].classList.remove ("active");
            }

// ---  add class 'active' to clicked buttons
           btn_clicked.classList.add ("active");
        }; //if(!!e.target)
    }; //function SetMenubuttonActive()

//=========  AddSubmenuButton  === PR2020-01-26 PR2021-04-26 PR2021-06-23
    function AddSubmenuButton(el_div, a_innerText, a_function, classnames_list, a_id, a_href, a_download) {
        //console.log(" ---  AddSubmenuButton --- ");
        let el_a = document.createElement("a");
            if(a_id){el_a.setAttribute("id", a_id)};

            if(a_href) {
                el_a.setAttribute("href", a_href);
                if(a_download){ el_a.setAttribute("target", "_blank") }
            };
            el_a.innerText = a_innerText;
            if(!!a_function){el_a.addEventListener("click", a_function, false)};
            el_a.classList.add("no_select");
            // set background color of btn
            el_a.classList.add("tsa_tr_selected");
            el_a.classList.add("px-2", "mr-2");
            if (classnames_list && classnames_list.length) {
                for (let i = 0, len = classnames_list.length; i < len; i++) {
                    const classname = classnames_list[i];
                    if(!!classname){
                        el_a.classList.add(classname);
                    }
                }
            }

            el_div.classList.add("pointer_show")
        el_div.appendChild(el_a);
    };//function AddSubmenuButton

//========= UploadSettings  ============= PR2019-10-09
    function UploadSettings (upload_dict, url_str) {
        //console.log("=== UploadSettings");
        //console.log("url_str", url_str);
        //console.log("upload_dict", upload_dict);
        if(!!upload_dict) {
            const parameters = {"upload": JSON.stringify (upload_dict)}
            let response = "";
            $.ajax({
                type: "POST",
                url: url_str,
                data: parameters,
                dataType:'json',
                success: function (response) {
                    //console.log( "response");
                    //console.log( response);
                },  // success: function (response) {
                error: function (xhr, msg) {
                    console.log(msg + '\n' + xhr.responseText);
                }
            });
        }
    };  // UploadSettings

//========= UpdateHeaderbar  ================== PR2020-11-14 PR2020-12-02
    function b_UpdateHeaderbar(loc, setting_dict, permit_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school){
        //console.log(" --- UpdateHeaderbar ---" )
        //console.log("setting_dict", setting_dict )
        //console.log("permit_dict", permit_dict )

        const cls_hide = "display_hide";

// --- EXAM YEAR
       //console.log("setting_dict.sel_examyear_pk", setting_dict.sel_examyear_pk )
        if(el_hdrbar_examyear) {
            let examyer_txt = "";
            if (setting_dict.sel_examyear_pk){
               examyer_txt = loc.Examyear + " " + setting_dict.sel_examyear_code
            } else {
                // there is always an examyear selected, unless table is empty
                examyer_txt = "<" + loc.No_examyears + ">"
            }
            el_hdrbar_examyear.innerText = examyer_txt;

        //console.log("permit_dict.may_select_examyear", permit_dict.may_select_examyear )
            add_or_remove_class(el_hdrbar_examyear, "awp_navbaritem_may_select", permit_dict.may_select_examyear, "awp_navbar_item" )

        }
// --- DEPARTMENT
        if(el_hdrbar_department) {
            const display_department = (!!permit_dict.display_department);

        //console.log("display_department", display_department )
            const allowed_depbases_count = (permit_dict.allowed_depbases) ? permit_dict.allowed_depbases.length : 0
            const may_select_department = (display_department && allowed_depbases_count > 1);

            add_or_remove_class(el_hdrbar_department, cls_hide, !display_department)
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
                        }
                    }
                }
            }
            el_hdrbar_department.innerText = department_txt;

        }
// --- SCHOOL
        if(el_hdrbar_school) {

            const display_school = (!!permit_dict.display_school);
            const may_select_school = (display_school && permit_dict.may_select_school);

            add_or_remove_class(el_hdrbar_school, cls_hide, !display_school)
            // set hover when user has permit to goto different school.
            add_or_remove_class(el_hdrbar_school, "awp_navbaritem_may_select", permit_dict.may_select_school, "awp_navbar_item" )

            let schoolname_txt = null;
            if (!setting_dict.sel_schoolbase_pk){
                if (permit_dict.may_select_school) {
                    schoolname_txt = " <" + loc.Select_school + ">";
                } else {
                    schoolname_txt = " <" + loc.No_school + ">";
                }
            } else {
                schoolname_txt = setting_dict.sel_schoolbase_code;
                if (!setting_dict.sel_examyear_pk) {
                    schoolname_txt += " <" + loc.No_examyear_selected + ">"
                } else {
                    if (!setting_dict.sel_school_pk){
                        schoolname_txt += " <" + loc.School_notfound_thisexamyear + ">"
                    } else {
                        schoolname_txt += " " + setting_dict.sel_school_name
                    }
                }
            }
            el_hdrbar_school.innerText = schoolname_txt;

//console.log("display_school", display_school)
//console.log("may_select_school", may_select_school)

        }
//console.log(el_hdrbar_school)

    }  // UpdateHeaderbar

//========= b_get_depbases_display  ============= PPR2021-05-06
    function b_get_depbases_display(department_map, fldName, fld_value) {
        // function converts "1;2;3" into "Vsbo, Havo, Vwo"
        let depbase_codes = ""
        if(fld_value){
            const arr = fld_value.split(";");
// --- loop through department_map, because base_id must be looked up, not department_id PR2021-05-06
            if (arr && arr.length){
                for (const [map_id, map_dict] of department_map.entries()) {
                    const depbase_id = map_dict.base_id;
                    const code = (map_dict[fldName]) ? map_dict[fldName] : "-";
                    if(depbase_id){
                        if (arr.includes(depbase_id.toString())){
                            if(depbase_codes) { depbase_codes += ", "}
                            depbase_codes += code;
            }}}};
        }
        return depbase_codes;
    }  // b_get_depbases_display

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//========= b_get_permits_from_permitlist  ============= PPR2021-04-26
    function b_get_permits_from_permitlist(permit_dict) {
        //console.log("----- b_get_permits_from_permitlist -----");
        //console.log("permit_dict", permit_dict);
        // function puts permits from permit_list as key in permit_dict, for ease of use
        if(permit_dict.permit_list){
            for (let i = 0, action; action = permit_dict.permit_list[i]; i++) {
                permit_dict[action] = true;
            }
        }
    }  // b_get_permits_from_permitlist

//========= isEmpty  ============= PR2019-05-11
    //PR2019-05-05 from https://coderwall.com/p/_g3x9q/how-to-check-if-javascript-object-is-empty'
    function isEmpty(obj) {
        "use strict";
        for(let key in obj) {
            if(obj.hasOwnProperty(key))
                {return false}
        }
    return true;
}

//========= get_attr_from_el  =============PR2019-06-07
    function get_attr_from_el(element, key, default_value){
        "use strict";
    // ---  get attr value from key: i.e. element["name"] = "breakduration"
        let value = null;
        if(!!element && !!key){
            if(element.hasAttribute(key)){
                value = element.getAttribute(key);
            };
        }
        // (value == null) equals to (value === undefined || value === null)
        if (value == null && default_value != null) {
            value = default_value
        }
        return value;
    };

//========= get_attr_from_el_str  ============= PR2019-06-07
    function get_attr_from_el_str(element, key){
        "use strict";
        let value_str = "";
        if(!!element && !!key){
            if(element.hasAttribute(key)){
                value_str = element.getAttribute(key);
            };
        }
        return value_str;
    };

//========= get_attr_from_el_int  ============= PR2019-06-07 PR2020-08-14 PR2020-08-17
    function get_attr_from_el_int(element, key){
        "use strict";
        let value_int = 0; //PR2020-08-17 default changed from null to 0
        if(!!element && !!key){
            if(element.hasAttribute(key)){
                const value = element.getAttribute(key);
                if (Number(value)){
                    value_int = Number(element.getAttribute(key));
                }
            };
        }
        return value_int;
    };

//========= get_dict_value  ================= PR2020-02-02
    function get_dict_value (dict, keylist, default_value) {
        //console.log(" -----  get_dict_value   ----")
        if (!!keylist && !!dict) {
            for (let i = 0, key, len = keylist.length; i < len; i++) {
                key = keylist[i];
                // key == 0 is valid value
                if (key != null && !!dict && dict.hasOwnProperty(key)) {
                    dict = dict[key];
                } else {
                    dict = null;
                    break;
        }}};
        // (value == null) equals to (value === undefined || value === null)
        if (dict == null && default_value != null) {
            dict = default_value}
        return dict
    }  // get_dict_value

//========= b_show_hide_selected_elements_byClass  ====  PR2020-02-19  PR2020-06-20
    function b_show_hide_selected_elements_byClass(container_classname, contains_classname, container_element) {
        // this function shows / hides elements in container_element or (if null) on page,
        // based on classnames: example: <div class="tab_show tab_shift tab_team display_hide">
        // - all elements with class 'container_classname' will be checked. example:'tab_show' is the container_classname.
        // - if an element contains class 'contains_classname', it will be shown, if not it will be hidden. example: 'tab_shift' and 'tab_team' are classes of the select buttons ('contains_classname')
        // - class 'display_hide' in html is necessary to prevent showing all elements when page opens
        if(!container_element){ container_element = document };
        let list = container_element.getElementsByClassName(container_classname);
        for (let i=0, el; el = list[i]; i++) {
            const is_show = el.classList.contains(contains_classname)
            show_hide_element(el, is_show)
        }
    }  // b_show_hide_selected_elements_byClass

//========= function show_hide_element_by_id  ====  PR2019-12-13
    function show_hide_element_by_id(el_id, is_show) {
        if(!!el_id){
            let el = document.getElementById(el_id);
            if(!!el){
                if(is_show){
                    el.classList.remove("display_hide")
                } else{
                    el.classList.add("display_hide")
    }}}};

//========= show_hide_element  ====  PR2019-12-13
    function show_hide_element(el, is_show) {
        if(!!el){
            if(is_show){
                el.classList.remove("display_hide")
            } else{
                el.classList.add("display_hide")
    }}};

//========= set_element_class  ====  PR2019-12-13
    function set_element_class(el_id, is_add_class, clsName) {
        if(!!el_id){
            let el = document.getElementById(el_id);
            if(!!el){
                if(is_add_class){
                    el.classList.add(clsName)
                } else{
                    el.classList.remove(clsName)
        }}};
    };

//========= b_ShowTblrowError_byID  ====  PR2020-04-13
    function b_ShowTblrowError_byID(tr_id) {
        let tblRow = document.getElementById(tr_id);
        b_ShowTblrowError(tblRow);
    }

//========= b_ShowTblrowError set_element_class  ====  PR2020-04-13
    function b_ShowTblrowError(tblRow) {
        const cls_error = "tsa_tr_error";
        if(tblRow){
            tblRow.classList.add(cls_error);
            setTimeout(function (){ tblRow.classList.remove(cls_error); }, 2000);
        }
    }

    function ShowOkRow(tblRow ) {
        // make row green, / --- remove class 'ok' after 2 seconds
        tblRow.classList.add("tsa_tr_ok");
        setTimeout(function (){
            tblRow.classList.remove("tsa_tr_ok");
        }, 2000);
    }

//=========  ShowOkElement  ================ PR2019-11-27 PR2020-07-23
    function ShowOkElement(el_input, ok_class, cur_class) {
        // make element green, green border / --- remove class 'ok' after 2 seconds
        //console.log("ShowOkElement");
        if(cur_class) {el_input.classList.remove(cur_class)};
        if(!ok_class) {ok_class = "border_bg_valid"};
        el_input.classList.add(ok_class);
        setTimeout(function (){
            el_input.classList.remove(ok_class);
            if(cur_class) {el_input.classList.add(cur_class)};
        }, 2000);
    }

//=========  ShowClassWithTimeout  ================ PR2020-04-26 PR2020-07-15
    function ShowClassWithTimeout(el, className, timeout) {
        // show class, remove it after timeout milliseconds
        if(el && className){
            if(!timeout) { timeout = 2000};
            el.classList.add(className);
            setTimeout(function (){el.classList.remove(className)}, timeout);
        };
    }

// ++++++++++++++++ SELECT ELEMENTS by Classname  +++++++++++++++

//========= select_elements_in_containerId_byClass  ====  PR2020-10-06
    function select_elements_in_containerId_byClass(container_elementId, selectby_class) {
        let el_container = null;
        if(container_elementId){
            el_container = document.getElementById(container_elementId);
        } else {
            el_container = document;
        };
        const list = select_elements_in_container_byClass(el_container, selectby_class);
        return list;
    }  // select_elements_in_containerId_byClass

//========= select_elements_in_container_byClass  ====  PR2020-10-05
    function select_elements_in_container_byClass(el_container, selectby_class) {
        // this function shows / hides elements on page, based on classnames: example: <div class="tab_show tab_shift tab_team display_hide">
        // - all elements with class 'container_classname' will be checked. example:'tab_show' is the container_classname.
        // - if an element contains class 'contains_classname', it will be shown, if not it will be hidden. example: 'tab_shift' and 'tab_team' are classes of the select buttons ('contains_classname')
        // - class 'display_hide' in html is necessary to prevent showing all elements when page opens
        let list = [];
        if(el_container){
            if(selectby_class){
                list = el_container.getElementsByClassName(selectby_class);
            } else {
            // from https://stackoverflow.com/questions/8321874/how-to-get-all-childnodes-in-js-including-all-the-grandchildren
                list = el_container.getElementsByTagName("*");
            };
        };
        return list;
    }  // select_elements_in_container_byClass

// ++++++++++++++++ ADD REMOVE CLASS / ATTRIBUTE  +++++++++++++++

//========= add_or_remove_class_with_qsAll  ====================================
    function add_or_remove_class_with_qsAll(el_container, classname, is_add, filter_class){
        // add or remove selected cls_hide from all elements with class 'filter_class' PR2020-04-29
//console.log(" --- add_or_remove_class_with_qsAll --- ")
//console.log("is_add: ", is_add)
//console.log("filter_class: ", filter_class)
        // from https://stackoverflow.com/questions/34001917/queryselectorall-with-multiple-conditions
        // document.querySelectorAll("form, p, legend") means filter: class = (form OR p OR legend)
        // document.querySelectorAll("form.p.legend") means filter: class = (form AND p AND legend)

         // multipe filter: document.querySelectorAll(".filter1.filter2")
        //let elements =  document.querySelectorAll("." + filter_class)
        let elements = el_container.querySelectorAll(filter_class)
        for (let i = 0, len = elements.length; i < len; i++) {
            add_or_remove_class (elements[i], classname, is_add)
//console.log(elements[i])
        };
//console.log(" --- end of add_or_remove_class_with_qsAll --- ")
    }

//========= add_or_remove_class  ========================  PR2020-06-20
    function add_or_remove_class (el, classname, is_add, default_class) {
        if(el && classname){
            if (is_add){
                if (default_class){el.classList.remove(default_class)};
                el.classList.add(classname);
            } else {
                el.classList.remove(classname);
                if (default_class){el.classList.add(default_class)};
            }
        }
    }

//========= add_or_remove_attr_with_qsAll  ======== PR2020-05-01
    function add_or_remove_attr_with_qsAll(el_container, filter_str, atr_name, is_add, atr_value){
        // add or remove attribute from all elements with filter 'filter_str' PR2020-04-29
    //console.log(" --- add_or_remove_attr_with_qsAll --- ")
    //console.log("is_add: ", is_add)
    //console.log("filter_str: ", filter_str)
        // from https://stackoverflow.com/questions/34001917/queryselectorall-with-multiple-conditions
        // document.querySelectorAll("form, p, legend") means filter: class = (form OR p OR legend)
        // document.querySelectorAll("form.p.legend") means filter: class = (form AND p AND legend)

         // multipe filter: document.querySelectorAll(".filter1.filter2")
        //let elements =  document.querySelectorAll("." + filter_str)
        let elements = el_container.querySelectorAll(filter_str)
        for (let i = 0, len = elements.length; i < len; i++) {
            add_or_remove_attr(elements[i], atr_name, is_add, atr_value)
    //console.log(elements[i])
        };
    }  // add_or_remove_attr_with_qsAll

//========= add_or_remove_attr  =========== PR2020-05-01
    function add_or_remove_attr (el, atr_name, is_add, atr_value) {
        if(!!el){
            if (is_add){
                el.setAttribute(atr_name, atr_value)
            } else {
                el.removeAttribute(atr_name)
            }
        }
    }  // add_or_remove_attr

//========= function add_hover  =========== PR2020-05-20 PR2020-08-10
    function add_hover(el, hover_class, default_class) {
//- add hover to element
        if(!hover_class){hover_class = "tr_hover"};
        if(el){
            el.addEventListener("mouseenter", function(){
                if(default_class) {el.classList.remove(default_class)}
                el.classList.add(hover_class)
            });
            el.addEventListener("mouseleave", function(){
                if(default_class) {el.classList.add(default_class)}
                el.classList.remove(hover_class)
            });
        }
        el.classList.add("pointer_show")
    }  // add_hover

//=========  append_background_class ================ PR2020-09-10
    function append_background_class(el, default_class, hover_class) {
        if (el) {
            el.classList.add(default_class, "pointer_show");
            // note: dont use on icons that will change, like 'inactive' or 'status'
            // add_hover_class will replace 'is_inactive' icon by default_class
            if (hover_class) {add_hover_class (el, hover_class, default_class)};
        }
    }

//=========  refresh_background_class ================ PR2020-09-12
    function b_refresh_icon_class(el, img_class) {
        if (el) {
            const el_img = el.children[0];
            if (el_img){el_img.className = img_class};
        }
    }  // b_refresh_icon_class

//========= add_hover_class  =========== PR2020-09-20
    function add_hover_class (el, hover_class, default_class) {
        //console.log(" === add_hover_class === ")
        // note: dont use on icons that will change, like 'inactive' or 'status'
        // add_hover_class will replace 'is_inactive' icon by default_class on mouseleave
        if(el && hover_class && default_class){
            el.addEventListener("mouseenter", function() {add_or_remove_class (el, hover_class, true, default_class)});
            el.addEventListener("mouseleave", function() {add_or_remove_class (el, default_class, true, hover_class)});
        };
    }  // add_hover_class

//=========  add_hover  =========== PR2020-06-09
    function add_hover_image(el, hover_image, default_image) {
        //console.log(" === add_hover_image === ")
//- add hover image to element
        if(el && hover_image && default_image){
            const img = el.children[0];
            if(img){
                el.addEventListener("mouseenter", function() { img.setAttribute("src", hover_image) });
                el.addEventListener("mouseleave", function() { img.setAttribute("src", default_image) });
        }}
    }  // add_hover_image

//========= set_focus_on_id_with_timeout  =========== PR2020-05-09
    function set_focus_on_id_with_timeout(id, ms) {
        if(!!id && ms){
            const el = document.getElementById(id);
            set_focus_on_el_with_timeout(el, ms);
        }
    }  // set_focus_on_id_with_timeout

//========= set_focus_on_el_with_timeout  =========== PR2020-05-09
    function set_focus_on_el_with_timeout(el, ms) {
        if(!!el && ms){
            setTimeout(function() { el.focus() }, ms);
        }
    }  // set_focus_on_el_with_timeout

//========= highlight_BtnSelect  ============= PR2020-02-20 PR2020-08-31
    function highlight_BtnSelect(btn_container, selected_btn, btns_disabled){
        //console.log( "//========= highlight_BtnSelect  ============= ")
        // ---  highlight selected button
        let btns = btn_container.children;
        for (let i = 0, btn; btn = btns[i]; i++) {
            const data_btn = get_attr_from_el(btn, "data-btn")
            // highlight selected btn
            add_or_remove_class(btn, "tsa_btn_selected", (data_btn === selected_btn) );
            // disable btn, except when btn is selected btn
            btn.disabled = (btns_disabled && data_btn !== selected_btn)
        }
    }  //  highlight_BtnSelect

//========= get_mapdict_from_datamap_by_tblName_pk  ============= PR2019-11-01 PR2020-08-24
    function get_mapdict_from_datamap_by_tblName_pk(data_map, tblName, pk_str) {
        // function gets map_id form tblName and  pk_int, looks up 'map_id' in data_map
        let map_dict;
        if(tblName && pk_str){
            const map_id = tblName + "_" + pk_str;
            map_dict = data_map.get(map_id);
            // instead of: map_dict = get_mapdict_from_datamap_by_id(data_map, map_id);
        };
        // map.get returns 'undefined' if the key can't be found in the Map object.
        if (!map_dict) {map_dict = {}}
        return map_dict
    }    // get_mapdict_from_datamap_by_tblName_pk

//========= get_mapdict_from_datamap_by_id  ============= PR2019-09-26
    function get_mapdict_from_datamap_by_id(data_map, map_id) {
        // function looks up map_id in data_map and returns dict from map
        let map_dict;
        if(data_map && map_id){
            map_dict = data_map.get(map_id);
            // instead of:
            //for (const [key, data_dict] of data_map.entries()) {
            //    if(key === map_id){
            //        map_dict = data_dict;
            //        break;
            //    }
            //};
        };
        // map.get returns 'undefined' if the key can't be found in the Map object.
        if (!map_dict) {map_dict = {}}
        return map_dict
    }

//========= b_get_itemdict_from_datamap_by_el  ============= PR2019-10-12 PR2020-09-13 PR2021-01-014
    function b_get_itemdict_from_datamap_by_el(el, data_map) {
        // function gets map_id form 'data-map_id' of tblRow, looks up 'map_id' in data_map
        let item_dict = {};
        const tblRow = get_tablerow_selected(el);
        if(tblRow){
            // was: const map_id = get_attr_from_el(tblRow, "data-table") + "_" + get_attr_from_el(tblRow, "data-pk")
            item_dict = get_mapdict_from_datamap_by_id(data_map, tblRow.id);
        }
        return item_dict
    }  // b_get_itemdict_from_datamap_by_el

//========= b_get_status_bool_at_index  ============= PR2021-01-15 PR2021-02-05
    function b_get_status_bool_at_index(status_sum, index) {
        const status_array = b_get_status_array(status_sum);
        return b_get_status_bool_at_arrayindex(status_array, index);
    }  // b_get_status_bool_at_index

//========= b_get_status_bool_at_index  ============= PR2021-02-05
    function b_get_status_bool_at_arrayindex(status_array, index) {
        let status_bool = false;
        if(status_array && index < status_array.length) {
            status_bool = (status_array[index] === 1);
        }
        return status_bool
    }

//========= b_set_status_bool_at_index  ============= PR2021-01-15 PR2021-02-05
    function b_set_status_bool_at_index(status_int, index, new_value) {
        //console.log( " ==== b_set_status_bool_at_index ====");

        if(status_int == null){status_int = 0};
        let new_status_sum = 0;
        const status_array = b_get_status_array(status_int)
        if(status_array && index < status_array.length) {
    // ---  put new_value at index
            status_array[index] = (new_value) ? 1 : 0;
    // ---  convert to integer
            new_status_sum =  b_get_statussum_from_array(status_array);
        }
        return new_status_sum
    }  // b_set_status_bool_at_index

//========= b_get_statussum_from_array  =============  PR2021-02-05
    function b_get_statussum_from_array(status_array) {
        // ---  convert to integer
        let status_sum = null;
        if(status_array && status_array.length){
            status_array.reverse();
            const arr_joined = status_array.join("");
            status_sum = parseInt(arr_joined,2);
        }
        return status_sum;
    }

//========= b_get_status_array  ============= PR2021-01-15 PR2021-02-05
    function b_get_status_array(status_sum) {
        //console.log( " ==== b_set_status_bool_at_index ====");
        const array_length = 15
        const leading_zeros = "0".repeat(array_length);

        if(status_sum == null){status_sum = 0};
        const status_binary = status_sum.toString(2)  // status_binary:  '1110101' string
        const status_binary_extended = leading_zeros + status_binary;  // status_binary_extended: '000000000000001110101' string
        const status_binary_sliced = status_binary_extended.slice(array_length * -1);  // status_binary_sliced: '000000001110101' string

        // PR2021-01-15 from https://www.samanthaming.com/tidbits/83-4-ways-to-convert-string-to-character-array/
        const status_array = [...status_binary_sliced];   // ... is the spread operator
        const status_array_reversed = status_array.reverse();

        for (let i = 0, len = status_array_reversed.length; i < len; i++) {
            status_array_reversed[i] = Number(status_array_reversed[i]);
        }
        // status_array_reversed = [1, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]

        return status_array_reversed
    }  // b_get_status_array

    function b_get_status_iconclass(publ, auth1, auth2, auth3) { //  PR2021-05-07
        const img_class = (publ) ? "appr_1_5" :
                          (auth1 && auth2 && auth3) ? "appr_1_4" :
                          (auth2 && auth3) ? "appr_1_3" :
                          (auth1 && auth3) ? "appr_1_2" :
                          (auth1 && auth2) ? "appr_0_4" :
                          (auth3) ? "appr_1_1" :
                          (auth2 ) ? "appr_0_3" :
                          (auth1 ) ? "appr_0_2" : "appr_0_0"
        return img_class
    }

    function get_status_class(status_sum) { // PR2021-01-15
        //console.log( " ==== get_status_class ====");
        //console.log( "status_sum", status_sum);
        let img_class = "appr_0_0";

        if (status_sum < 32) {
            const status_array = b_get_status_array(status_sum);
            //console.log( "status_array", status_array);

            const created = b_get_status_bool_at_arrayindex(status_array, 0)  // STATUS_00_CREATED
            const auth1 = b_get_status_bool_at_arrayindex(status_array, 1)  // STATUS_01_AUTH1 = 2
            const auth2 = b_get_status_bool_at_arrayindex(status_array, 2) // STATUS_02_AUTH2 = 4
            const auth3 = b_get_status_bool_at_arrayindex(status_array, 3) // STATUS_03_AUTH3 = 8
            const submitted = b_get_status_bool_at_arrayindex(status_array, 4) // STATUS_04_SUBMITTED = 16

            img_class = (submitted) ? "appr_1_5" :
                        (auth1 && auth2 && auth3) ? "appr_1_4" :
                        (auth1 && auth2) ? "appr_0_4" :
                        (auth1 && auth3) ? "appr_1_2" :
                        (auth2 && auth3) ? "appr_1_3" :
                        (auth3) ? "appr_1_1" :
                        (auth2) ? "appr_0_3" :
                        (auth1) ? "appr_0_2" :
                        (created) ? "stat_0_1" : "stat_0_0"

        } else if (status_sum < 64) {img_class = "note_1_2" // STATUS_05_REQUEST = 32
        } else if (status_sum < 128) {img_class = "note_1_3"// STATUS_06_WARNING = 64
        } else if (status_sum < 256) {img_class = "note_1_4"// STATUS_07_REJECTED = 128
        } else if (status_sum < 512) {img_class = "note_2_2"// STATUS_08_REQUEST_ANSWERED = 256
        } else if (status_sum < 1024) {img_class = "note_2_3" // STATUS_09_WARNING_ANSWERED = 512
        } else if (status_sum < 2048) {img_class = "note_2_4" // STATUS_10_REJECTED_ANSWERED = 1024
        } else if (status_sum < 4096) {img_class = "note_1_5"  // STATUS_11_EDIT = 2048
        } else if (status_sum < 8192) {img_class = "note_2_5" // STATUS_12_EDIT_ANSWERED = 4096
        } else if (status_sum < 16384) {img_class = "note_2_6"  // STATUS_13_APPROVED = 8192
        } else {img_class = "appr_2_6"}; // STATUS_14_LOCKED = 16384

        //console.log("img_class", img_class);
        return img_class;
    }  // get_status_class

//#########################################################################
// +++++++++++++++++ DATAMAP +++++++++++++++++++++++++++++++++++++++

//=========  b_fill_datamap  ================ PR2020-09-06
    function b_fill_datamap(data_map, rows) {
        //console.log(" --- b_fill_datamap  ---");
        //console.log("rows", rows);
        data_map.clear();
        if (rows && rows.length) {
            for (let i = 0, dict; dict = rows[i]; i++) {
                data_map.set(dict.mapid, dict);
            }
        }
        //console.log("data_map", data_map);
        //console.log("data_map.size", data_map.size)
    };  // b_fill_datamap


//=========  deepcopy_dict  ================ PR2020-05-03
    let deepcopy_dict = function copy_fnc(data_dict) {
        //console.log(" === Deepcopy_Dict ===")
        let dict_clone = {};
        for(let key in data_dict) {
            if(data_dict.hasOwnProperty(key)){
                const value = data_dict[key];
                if (typeof value==='object' && value!==null && !(value instanceof Array) && !(value instanceof Date)) {
                   dict_clone[key] = copy_fnc(value);
                } else {
                    dict_clone[key] = value;
        }}};
        return dict_clone;
    }  // deepcopy_dict

//=========  deepcopy_dict  ================ PR2021-05-31
// TODO replace old one with this one
    let deepcopy_dictNEW = function copy_fnc(data_dict) {
        //console.log(" === Deepcopy_Dict ===")
        let dict_clone = {};
        for (const [key, value] of Object.entries(mod_studentsubject_dict)) {
            if (typeof value==='object' && value!==null && !(value instanceof Array) && !(value instanceof Date)) {
               dict_clone[key] = copy_fnc(value);
            } else {
                dict_clone[key] = value;
            }
        };
        return dict_clone;
    }  // deepcopy_dict



//#########################################################################
// +++++++++++++++++ SORT DICTIONARY +++++++++++++++++++++++++++++++++++++++

//========= b_comparator_sortby  =========  PR2020-09-03
// PR2020-09-01 from: https://stackoverflow.com/questions/5435228/sort-an-array-with-arrays-in-it-by-string/5435341
// explained in https://www.javascripttutorial.net/javascript-array-sort/
// function used in Array.sort to sort list of dicts by key 'code', null or '---' last  PR2021-02-25
    function b_comparator_sortby(a, b) {
        const max_len = 24 // CODE_MAX_LENGTH = 24;
        const z_str = "z".repeat(max_len);

        const a_lc = (a.sortby && a.sortby !== "---" && a.sortby !== "-") ? a.sortby.toLowerCase() : z_str;
        const b_lc = (b.sortby && b.sortby !== "---" && b.sortby !== "-") ? b.sortby.toLowerCase() : z_str;

        if (a_lc < b_lc) return -1;
        if (a_lc > b_lc) return 1;
        return 0;
    }  // b_comparator_sortby

// this one sorts integers, not in use yet PR2021-02-26
    function b_comparator_sortby_integer(a, b) {
    // PR2021-02-25 from https://stackoverflow.com/questions/1063007/how-to-sort-an-array-of-integers-correctly
       // exc_subject_ColIndex_list.sort((a, b) => a - b);
       return a - b;
    };


//#########################################################################
// +++++++++++++++++ DATE FUNCTIONS +++++++++++++++++++++++++++++++++++++++

//========= add_daysJS  ======== PR2019-11-03
    function add_daysJS(date_JS, days) {
        // this function returns a new date object, instead of updating the existing one
        // from https://codewithhugo.com/add-date-days-js/
        // see also: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date
        let copy_JS = null;
        if (!!date_JS){
            copy_JS = new Date(Number(date_JS));
            if (!!copy_JS){
                copy_JS.setDate(date_JS.getDate() + days)
            };
        };
        return copy_JS
    }

//=========  parse_dateJS_from_dateISO ================ PR2020-07-22
    function parse_dateJS_from_dateISO(date_iso) {
        //console.log( "===== parse_dateJS_from_dateISO  ========= ");
        // function creates date in local timezone.
        // date_iso = '2020-07-22T12:03:52.842Z'
        // date_JS = Wed Jul 22 2020 08:03:52 GMT-0400 (Bolivia Time)

        let date_JS = null;
        if (date_iso){
           date_JS =  new Date(Date.parse(date_iso));
        }
        return  date_JS;
    }  // parse_dateJS_from_dateISO

//========= get_now_arr ========== PR2020-07-08 tsa
    function get_now_arr() {
        // send 'now' as array to server, so 'now' of local computer will be used
        const now = new Date();
        const now_arr = [now.getFullYear(), now.getMonth() + 1, now.getDate(), now.getHours(), now.getMinutes()];
        return now_arr;
    }

//=========  get_now_formatted ================ PR2021-04-28 from tsa format_time_from_offset_JSvanilla PR2020-04-10
    function get_now_formatted() {
        //console.log( "===== get_now_formatted  ========= ");

        const now = new Date();
        const year = now.getFullYear();
        const month_int = now.getMonth() + 1;
        const date_int = now.getDate();
        const hours_int = now.getHours();
        const minutes_int = now.getMinutes();

        const month_str = ("00" + month_int).slice(-2);
        const date_str = ("00" + date_int).slice(-2);
        const hour_str = ("00" + hours_int).slice(-2);
        const minute_str = ("00" + minutes_int).slice(-2);

        return [year, "-", month_str, "-", date_str, " ", hour_str, ".", minute_str, "u"].join('');

    }  // format_time_from_offset_JSvanilla


//#########################################################################
// +++++++++++++++++ VALIDATORS +++++++++++++++++++++++++++++++++++++++++++

//========= b_get_number_from_input  ========== PR2020-06-10
    function b_get_number_from_input(loc, fldName, input_value) {
        //console.log("--------- b_get_number_from_input ---------")
        //console.log("fldName", fldName)
        //console.log("input_value", input_value)
        let caption_str = (loc.Number) ? loc.Number : null;

        let multiplier = 1, min_value = 0, max_value = null;  // max $ 1000, max 1000%
        let integer_only = false, is_percentage = false
        if(fldName === "cycle"){
            caption_str = loc.Cycle ;
            integer_only = true;
            min_value = 1;
            max_value = 28;
        } else if(fldName === "sequence"){
            caption_str = loc.Sequence ;
            integer_only = true;
            min_value = 1;
            max_value = 10000;
        }

        let output_value = null, value_int = 0, value_decimal = 0, is_not_valid = false, err_msg = null;
        if(!input_value){
            output_value = 0;
        } else {
            // replace comma's with dots
            const replace_value_with_dot = input_value.replace(/\,/g,".");
            // get index of last dot - not in use
            // const index_last_dot = value_with_dot.lastIndexOf(".")
            let value_as_number = Number(replace_value_with_dot);
            // not valid when Number = false , i.e. NaN, except when value = 0
            is_not_valid = (!value_as_number && value_as_number !== 0)

            if(is_not_valid){
                if(!err_msg){err_msg = "'" + ((input_value) ? input_value : "") + "' " + loc.err_msg_is_invalid_number};
            } else {
                // Math.trunc() returns the integer part of a floating-point number
                const has_decimal_part = !!(value_as_number - Math.trunc(value_as_number));
                is_not_valid = (integer_only && has_decimal_part)
                if(is_not_valid){
                    if(!err_msg){err_msg = caption_str + " " + loc.err_msg_must_be_integer};
                } else {
                    // multiply to get minutes instead of hours or days / "pricecode * 100 / taxcode, addition * 10.000
                    output_value = Math.round(multiplier * (value_as_number));

                    is_not_valid =( (min_value != null && output_value < min_value) || (max_value != null && output_value > max_value) ) ;
                    if(is_not_valid){
                        if(!err_msg){
                            if(min_value !== null) {
                                if(max_value !== null) {
                                    const must_be_str = (is_percentage) ? loc.err_msg_must_be_percentage_between : loc.err_msg_must_be_number_between;
                                    err_msg = caption_str + " " + must_be_str + " " + min_value / multiplier + " " + loc.err_msg_and + " " + max_value / multiplier + ".";
                                } else {
                                    const must_be_str = (is_percentage) ? loc.err_msg_must_be_percentage_greater_than_or_equal_to : loc.err_msg_must_be_number_greater_than_or_equal_to;
                                    err_msg = caption_str + " " + must_be_str + " " + min_value / multiplier + "."

                                    //console.log("max_value", max_value, "multiplier", multiplier )
                                    //console.log("err_msg", err_msg )
                                }
                            } else if(max_value !== null) {
                                const must_be_str = (is_percentage) ? loc.err_msg_must_be_percentage_less_than_or_equal_to : loc.err_msg_must_be_number_less_than_or_equal_to;
                                err_msg = caption_str + " " + must_be_str + " " + max_value / multiplier + "."
                }
        }}}}};
        return [output_value, err_msg];
    }  // b_get_number_from_input

//========= validate_blank_unique_text  ================= PR2020-06-10
    function validate_blank_unique_text(loc, data_map, mapName, fldName, input_value, cur_pk_int, no_blank) {
        //console.log(" ===== validate_blank_unique_text =====");
        const field_caption = (mapName === "abscat" && fldName === "code") ? loc.The_absence_category :
                              (mapName === "abscat" && fldName === "sequence") ? loc.The_priority : loc.This_field
        const input_value_trimmed = input_value.trim();
// ---  get tblName, is null when btn = "btn_grid"
        let msg_err = null;
        if (!input_value_trimmed){
            if(no_blank){msg_err = field_caption + loc.must_be_completed};
        } else if(cur_pk_int && data_map.size){
            const input_value_lowercase = input_value_trimmed.toLowerCase();
            for (const [map_id, item_dict] of data_map.entries()) {
                const item_pk_int = get_dict_value(item_dict, ["id", "pk"])
                // skip current item
                if (item_pk_int && item_pk_int !== cur_pk_int){
                    const item_value = get_dict_value(item_dict, [fldName, "value"])
                    const item_value_trimmed = item_value.trim();
                    const item_value_lowercase = item_value_trimmed.toLowerCase();
                    if(item_value){
                        if(input_value_lowercase === item_value_lowercase){
                            msg_err = field_caption + " '" + input_value + "' " + loc.already_exists + ".";
                            break;
        }}}}};
        return msg_err;
    }  // validate_blank_unique_text


//######### IT WORKS !!! #################################################################
// +++++++++++++++++ LOOKUP dict in ordered dictlist +++++++++++++++++++++++++++ PR2021-06-16

//========= b_get_mapdict_from_datarows  ================== PR2021-06-21
    function b_get_mapdict_from_datarows(data_rows, map_id, user_lang){
        const [middle_index, found_dict, compare] = b_recursive_lookup(data_rows, map_id, user_lang);
        const selected_dict = (!isEmpty(found_dict)) ? found_dict : null;
        return selected_dict;
    }

//========= b_recursive_lookup  ========== PR2020-06-16
    function b_recursive_lookup(dict_list, search_value, user_lang){
        //console.log( " ----- b_recursive_lookup -----");
        // function can handle list of 2 ^ (max_loop -2) rows , which is over 1 million rows
        // don't use recursive function, it is less efficient than a loop because it puts each call i the stack
        // function returns rowindex of searched value, or rowindex of row to be inserted
        // dict_list must be ordered by id (as text field), done by server

        let compare = null, middle_index = null, found_dict = null;
        if (dict_list && dict_list.length){
            const lookup_field = "mapid";
            const last_index = dict_list.length - 1;
            let min_index = 0;
            let max_index = last_index;
            middle_index =  Math.floor( (min_index + max_index) / 2);

            if(!search_value){search_value = ""};
        //console.log( "search_value: ", search_value);
        //console.log( "lookup_field: ", lookup_field);

            const max_loop = 25;
            for (let i = 0; i < max_loop; i++) {
                if (i > 23) {
                // exit when loop not breaked (should not be possible), put index at end of list
                    compare = 1;
                    middle_index = last_index;
                    break;
                } else {
                    const middle_dict = dict_list[middle_index];
                    const middle_value = middle_dict[lookup_field];

        //console.log( i, "LOOP : ", min_index, " - ", max_index, " > ", middle_index);
        //console.log( "middle_value: ", middle_value);

                    // PR2021-06-08 note: toLowerCase is not necessary, because sensitivity: 'base' ignores lower- / uppercase and accents;
                    // sort function from https://stackoverflow.com/questions/51165/how-to-sort-strings-in-javascript
                    // localeCompare from https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/localeCompare
                    // 'acu'.localeCompare('giro') = -1
                    // 'mcb'.localeCompare('giro') = 1
                    // note: value of compare can be 2 or -2 in some browsers, teherfore use compare < 0 instead of compare === -1
                    compare = search_value.localeCompare(middle_value, user_lang, {sensitivity: 'base'});
        //console.log( "compare : ", compare);
        //console.log( "min_index : ", min_index);
        //console.log( "max_index : ", max_index);
                    if (!compare) {
                        //  search_value === middle_value
                        // exit, return middle_index (compare = 0 means item is found at index: middle_index
                        found_dict = middle_dict;
                        break;

                    } else {
                        // value not found, return compare and middle_index
                        if (min_index === max_index){
                            // if returnvalue of compare = 0: value found at middle_index
                            // if returnvalue of compare < 0: value not found in list, must be inserted just before middle_index
                            // if returnvalue of compare > 0: value not found in list, must be inserted just after middle_index

        //console.log( "compare = 0, middle_index === max_index");

                            break;
                        } else {
                            // value not found, next lookup
                            if (compare < 0) {
                                if (middle_index === min_index){
                                    // exit if middle_index equals min_index and comapre is negative: means that value is not found

        //console.log( "compare < 0, middle_index === max_index");
                                    break;
                                } else {
                                    //  search_value < middle_value
                                    // set middle_index to halfway lower part
                                    //  set max_index = middle_index - 1
                                    // rounddown to integer
                                    max_index = middle_index - 1;
                                    middle_index =  Math.floor( (min_index + max_index) / 2);
        //console.log( "new middle_index", middle_index);
                                }
                            } else if (compare > 0) {
                                if (middle_index === max_index){
                                    // exit if middle_index equals max_index and comapre is positive: means that value is not found

        //console.log( "compare > 0, middle_index === max_index");

                                    break;
                                } else {
                                    //  search_value > middle_value
                                    // set middle_index to halfway upper part
                                    //  set min_index = middle_index + 1
                                    // round up to integer
                                    min_index = middle_index + 1;
                                    middle_index =  Math.ceil( (min_index + max_index) / 2);

        //console.log( "min_index", min_index);
        //console.log( "new middle_index", middle_index);
                                }
                            }
        //console.log( "GOTO NEXT LOOP 2 : ", min_index, " - ", max_index, " >< ", middle_index);
                        }
                    }
                };  // if (i > 23)
            };  // for (let i = 0,
        };  //  if (dict_list && dict_list.length){

        //console.log( "found_dict: ", found_dict);
        //console.log( "compare: ", compare);
        return [middle_index, found_dict, compare];
    };  // b_recursive_lookup

//========= b_recursive_tblRow_lookup  ========== PR2020-06-16
    function b_recursive_tblRow_lookup(tblBody, search_value_1, search_value_2, search_value_3, user_lang){
        // console.log( " ----- b_recursive_tblRow_lookup -----");
        // function can handle list of 2 ^ (max_loop -2) rows , which is over 1 million rows
        // don't use recursive function, it is less efficient than a loop because it puts each call i the stack
        // function returns rowindex of searched value, or rowindex of row to be inserted

        const lookup_field_1 = "data-ob1", lookup_field_2 = "data-ob2", lookup_field_3 = "data-ob3";
        let compare = null, middle_index = null, found_row = null;
        const last_index = (tblBody.rows && tblBody.rows.length) ? tblBody.rows.length -1 : 0;
        if (tblBody.rows && tblBody.rows.length){
            let min_index = 0;
            let max_index = last_index;
            middle_index =  Math.floor( (min_index + max_index) / 2);

            const s_val_1 = (search_value_1) ? search_value_1.toLowerCase() : "";
            const s_val_2 = (search_value_2) ? search_value_2.toLowerCase() : "";
            const s_val_3 = (search_value_3) ? search_value_3.toLowerCase() : "";

            const max_loop = 25;
            for (let i = 0; i < max_loop; i++) {
                if (i > 23) {
                // exit when loop not breaked (should not be possible), put index at end of list
                    compare = 1;
                    middle_index = last_index;
                    break;
                } else {
                    const tblRow = tblBody.rows[middle_index];
                    const middle_value_field_1 = get_attr_from_el(tblRow, lookup_field_1, "");
                    const middle_value_field_2 = get_attr_from_el(tblRow, lookup_field_2, "");
                    const middle_value_field_3 = get_attr_from_el(tblRow, lookup_field_3, "");

        //console.log( i, "LOOP : ", min_index, " - ", max_index, " > ", middle_index);
        //console.log( "lookup_values: ", search_value_1, " - ",  search_value_2, search_value_3);
        //console.log( "row_values: ", middle_value_field_1, " - ",  middle_value_field_2, middle_value_field_3);

                    // PR2021-06-08 note: toLowerCase is not necessary, because sensitivity: 'base' ignores lower- / uppercase and accents;
                    // sort function from https://stackoverflow.com/questions/51165/how-to-sort-strings-in-javascript
                    // localeCompare from https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/localeCompare
                    // 'acu'.localeCompare('giro') = -1
                    // 'mcb'.localeCompare('giro') = 1
                    // note: value of compare can be 2 or -2 in some browsers, therefore use compare < 0 instead of compare === -1
                    const compare1 = s_val_1.localeCompare(middle_value_field_1, user_lang, {sensitivity: 'base'});
                    // if first lookup field matches: compare has value of second field
                    // if first lookup field does not match: compare has value of first field
                    if (!compare1){
                        const compare2 = s_val_2.localeCompare(middle_value_field_2, user_lang, {sensitivity: 'base'});
                        if (!compare2){
                             compare = s_val_3.localeCompare(middle_value_field_3, user_lang, {sensitivity: 'base'});
                        } else {
                            compare = compare2;
                        };
                    } else {
                        compare = compare1;
                    }
        //console.log( "compare : ", compare);
                    if (!compare ) {
                        //  search_value === middle_value
                        // exit, return middle_index (compare = 0 means item is found at index: middle_index
                        found_row = tblRow;
                        break;

                    } else {
                        // value not found, return compare and middle_index
                        if (min_index === max_index){
                            // if returnvalue of compare = 0: value found at middle_index
                            // if returnvalue of compare < 0: value not found in list, must be inserted just before middle_index
                            // if returnvalue of compare > 0: value not found in list, must be inserted just after middle_index
                            break;
                        } else {
                            // value not found, next lookup
                            if (compare < 0) {
                                if (middle_index === min_index){
                                    // exit if middle_index equals min_index and comapre is neagtive: means that value is not found
                                    break;
                                } else {
                                    //  search_value < middle_value
                                    // set middle_index to halfway lower part
                                    //  set max_index = middle_index - 1
                                    // rounddown to integer
                                    max_index = middle_index - 1;
                                    middle_index =  Math.floor( (min_index + max_index) / 2);
                                }
                            } else if (compare > 0) {
                                if (middle_index === max_index){
                                    // exit if middle_index equals max_index and comapre is positive: means that value is not found
                                    break;
                                } else {
                                    //  search_value > middle_value
                                    // set middle_index to halfway upper part
                                    //  set min_index = middle_index + 1
                                    // round up to integer
                                    min_index = middle_index + 1;
                                    middle_index =  Math.ceil( (min_index + max_index) / 2);
                                }
                            }
                        }
                    }
                };  // if (i > 23)
            };  // for (let i = 0

            // set index = -1 when new row comes after last tablerow, add 1 to index at other rows
            if (compare > 0) {
                if (middle_index === last_index){
                    middle_index = -1;
                } else {
                    middle_index += 1;
                }
            }
        } else {
            // table is empty
            compare = 1;
            middle_index = -1;
        };  //  if (tblBody.rows && tblBody.rows.length)

        //console.log( "return : index", middle_index, " found_row ", found_row, " compare ", return_compare);
        return middle_index;
    };  // b_recursive_tblRow_lookup

// when list is not sorted - lookup the oldfashioned way
//========= b_lookup_dict_in_dictlist  ========== PR2020-06-25
    function b_lookup_dict_in_dictlist(dictlist, search_field, search_value){
        let lookup_dict = null;
        for (let i = 0, lookup_value, dict; dict = dictlist[i]; i++) {
            lookup_value = dict[search_field];
            if(lookup_value && lookup_value === search_value){
                lookup_dict = dict;
                break;
            }
        }
        return lookup_dict;
    };  // b_lookup_dict_in_dictlist

//========= b_lookup_dict_in_dictlist  ========== PR2020-06-25
    function b_lookup_dict_with_index_in_dictlist(dictlist, search_field, search_value){
        let lookup_dict = null, lookup_index = null;
        for (let i = 0, lookup_value, dict; dict = dictlist[i]; i++) {
            lookup_value = dict[search_field];
            if(lookup_value && lookup_value === search_value){
                lookup_index = i;
                lookup_dict = dict;
                break;
            }
        }
        return [lookup_index, lookup_dict];
    };  // b_lookup_dict_in_dictlist

//=========  b_remove_item_from_array  ================ PR2021-07-07
    function b_remove_item_from_array(array, item){
        // PR2021-07-07 remove item from array used in mod select columsn
        // from https://stackoverflow.com/questions/3954438/how-to-remove-item-from-array-by-value
        for(let i in array){
            if(array[i]==item){
                array.splice(i,1);
                break;
            }
        }
    }  // b_remove_item_from_array

//=========  b_remove_item_from_array  ================ PR2021-07-07
    function b_clear_array(array){
       // clear the array. from https://love2dev.com/blog/javascript-remove-from-array/
        if(array){
            while (array.length) {
                array.pop();
            };
        };
    };  // b_clear_array

//#########################################################################
// +++++++++++++++++ MESSAGES +++++++++++++++++++++++++++++++++++++++

    function b_show_mod_message(msg_html, header_text){  // PR2021-01-26 PR2021-03-25 PR2021-07-03
        // TODO header, set focus after closing messagebox

        const el_msg_header = document.getElementById("id_mod_message_header");
        if(el_msg_header){el_msg_header.innerText = (header_text) ? header_text : null};

        const el_msg_container = document.getElementById("id_mod_message_container");
        if(el_msg_container){el_msg_container.innerHTML = (msg_html) ? msg_html : null};

        const el_msg_btn_cancel = document.getElementById("id_modmessage_btn_cancel");
        if(el_msg_btn_cancel){set_focus_on_el_with_timeout(document.getElementById("id_modmessage_btn_cancel"), 150 )};

        $("#id_mod_message").modal({backdrop: false});
    }  // show_mod_message

//========= b_render_awp_messages  =================
    function b_render_awp_messages(awp_messages) {
        //console.log( "===== b_render_awp_messages -----")
        //console.log( "awp_messages", awp_messages)
        // PR2020-10-30 renders messages PR2021-04-27
        // PR2021-05-13 only messages with key 'class' must be shown, other messages have key 'field' and must be shown in modal 'subject' etc

        if (awp_messages && awp_messages.length) {
            const el_mod_awpmessages = document.getElementById("id_awpmessage_container")
            if (el_mod_awpmessages){
                el_mod_awpmessages.innerHTML = null;
                let show_modal = false;

                for (let i = 0, msg_dict ; msg_dict = awp_messages[i]; i++) {
                    if (msg_dict && msg_dict.class){
                        const msg_class = msg_dict.class;
                        const msg_list = msg_dict.msg_list;
                        show_modal = true;
// --- insert el_div
                        let el_div = document.createElement("div");
                        el_div.classList.add("m-2", "p-2")
                        el_div.classList.add(msg_class)

                        if(msg_list && msg_list.length){
                            for (let j = 0, msg, el_p; msg = msg_list[j]; j++) {
                                if(msg){
                                    el_p = document.createElement("p");
                                    el_p.innerHTML = msg
                                    el_div.appendChild(el_p);
                                }
                            }
                        }
                        el_mod_awpmessages.appendChild(el_div);
                    }  // if (msg_dict && msg_dict.class)
                }  // for (let i = 0, msg_dict ; msg_dict = awp_messages[i]; i++)
                if (show_modal){
// ---  set focus to close button - not working
                const el_modmessage_btn_cancel = document.getElementById("id_modmessage_btn_cancel");
                set_focus_on_el_with_timeout(el_modmessage_btn_cancel, 50);
// ---  show modal
                    $("#id_mod_awpmessages").modal({backdrop: true});
                }
            }
        }  //   if (awp_messages && awp_messages.length)
    }  // b_render_awp_messages

//========= b_render_msg_box  ================= PR2021-05-13
    function b_render_msg_box(id_el_msg, msg_list) {
        console.log( "===== b_render_msg_box -----")
        console.log( "id_el_msg", id_el_msg)
        console.log( "msg_list", msg_list)

        const el_msg = document.getElementById(id_el_msg);
        console.log("el_msg", el_msg)
        if (el_msg){
            const has_msg = (!!msg_list && !!msg_list.length)
        console.log("has_msg", has_msg)
    // put msg in el_msg
            let msg_html = ""
            if (has_msg){
                for (let j = 0, msg, el_p; msg = msg_list[j]; j++) {
                    if (j){msg_html += "<br>"};
                    if(msg){msg_html +=msg};
                }
            }
        console.log("msg_html", msg_html)
            el_msg.innerHTML = msg_html;
    // show el_msg when has_msg
            add_or_remove_class(el_msg, cls_hide, !has_msg)
        }
    }  // b_render_msg_box


//=========  ShowModMessages  ================ PR2021-06-27  PR2021-07-03
    function b_ShowModMessages(msg_dictlist) {
        console.log("==== ShowModMessages  ======")
        console.log("msg_dictlist", msg_dictlist)

        //  [ { class: "alert-warning", header: 'Update this',
        //      msg_html: "Deze loonperiode heeft 7 diensten."]

        if(msg_dictlist && msg_dictlist.length){
            const el_container = document.getElementById("id_mod_message_container");
            let header_text = null
            console.log("el_container", el_container)
            if(el_container){
                el_container.innerHTML = null;
                for (let i = 0, msg_dict; msg_dict = msg_dictlist[i]; i++) {
                    const class_str = (msg_dict.class) ? msg_dict.class : "border_bg_transparent";
                    if(!header_text && msg_dict.header){
                        header_text = msg_dict.header;
                    }
                    const msg_html = msg_dict.msg_html;
                    if (msg_html){
            // --- create div element with alert border for each message in messages
                        const el_border = document.createElement("div");
                        el_border.classList.add(class_str, "p-2", "my-2");
                        const el_div = document.createElement("div");
                        el_div.innerHTML = msg_html;
                        el_border.appendChild(el_div);
                        el_container.appendChild(el_border);
                    };
                };
            }  // if(el_container)

            const el_header =  document.getElementById("id_mod_message_header");
            if(el_header) {el_header.innerText = header_text};
// ---  set focus to close button - not working
            const el_btn_cancel = document.getElementById("id_mod_message_btn_cancel");
            set_focus_on_el_with_timeout(el_btn_cancel, 150);

            $("#id_mod_message").modal({backdrop: true});
        };
    }  // ShowModMessages




//#########################################################################
// +++++++++++++++++ SVG  +++++++++++++++++++++++++++++++++++++++++++
    function create_svg_html(id_svg, href, caption, txt_x, txt_y,
                                height, width, indent_left, indent_right,
                                polygon_class, fill) {

        const points = get_svg_arrow_points(height, width, indent_left, indent_right);

        let svg_html = "<svg id=\"" + id_svg + "\" height=\"" + height + "\" width=\"" + width + "\">"
        svg_html += "<a href=\"" + href + "\">"
        svg_html += "<polygon points=\"" + points + "\" class=\"" + polygon_class + "\"></polygon>"
        svg_html += "<text x=\"" + txt_x + "\" y=\"" + txt_y + "\" fill=\"" + fill + "\""
        svg_html +=  "text-anchor=\"middle\" alignment-baseline=\"middle\">"
        svg_html += caption
        svg_html += "</text></a></svg>"
        return svg_html
    };
//========= get_svg_arrow_points  =================
    function get_svg_arrow_points(height, width, indent_left, indent_right) {
        // PR2018-12-21 creates arrow shape
        points = "0,0 " // lower left corner
        if (indent_right) {
            points += (width - indent_right) + ",0 " // lower right corner
            points += (width) + "," + (height/2) + " "  // middle right point
            points += (width - indent_right) + "," + (height) + " " // top right corner
        } else {
            points += (width) + ",0 " // lower right corner
            points += (width) + "," + (height) + " " // top right corner
        };
        points += "0," + (height) + " " // top left corner
        if (indent_left) {
            points += (indent_left) + "," + (height/2)  // middle left point
        }
        return points
    };  // get_svg_arrow_points

