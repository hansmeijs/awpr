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
              menubuttons[i].classList.remove (cls_active);
            }

// ---  add class 'active' to clicked buttons
           btn_clicked.classList.add (cls_active);
        }; //if(!!e.target)
    }; //function SetMenubuttonActive()

//=========  AddSubmenuButton  === PR2020-01-26
    function AddSubmenuButton(el_div, a_innerText, a_function, classnames_list, a_id, a_href) {
        //console.log(" ---  AddSubmenuButton --- ");
        let el_a = document.createElement("a");
            if(!!a_id){el_a.setAttribute("id", a_id)};

            if(!!a_href) {el_a.setAttribute("href", a_href)};
            el_a.innerText = a_innerText;
            if(!!a_function){el_a.addEventListener("click", a_function, false)};
            // set background color of btn
            el_a.classList.add("tsa_tr_selected");
            el_a.classList.add("px-2");
            if (!!classnames_list) {
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
        console.log("=== UploadSettings");
        console.log("url_str", url_str);
        console.log("upload_dict", upload_dict);
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
                    //console.log(msg + '\n' + xhr.responseText);
                    //alert(msg + '\n' + xhr.responseText);
                }  // error: function (xhr, msg) {
            });  // $.ajax({
        }  //  if(!!row_upload)
    };  // UploadSettings

//========= UpdateHeaderbar  ================== PR2020-11-14 PR2020-12-02
    function b_UpdateHeaderbar(loc, setting_dict, el_hdrbar_examyear, el_hdrbar_department, el_hdrbar_school){
        //console.log(" --- UpdateHeaderbar ---" )
        //console.log("setting_dict", setting_dict )

// --- EXAM YEAR
       // console.log("setting_dict.sel_examyear_pk", setting_dict.sel_examyear_pk )
        if(el_hdrbar_examyear) {
            let examyer_txt = "";
            if (setting_dict.sel_examyear_pk){
               examyer_txt = loc.Exam_year + " " + setting_dict.sel_examyear_code
            } else {
                // there is always an examyear selected, unless table is empty
                examyer_txt = "<" + loc.No_examyears + ">"
            }
            el_hdrbar_examyear.innerText = examyer_txt;

        //console.log("setting_dict.may_select_examyear", setting_dict.may_select_examyear )
            add_or_remove_class(el_hdrbar_examyear, "awp_navbaritem_may_select", setting_dict.may_select_examyear, "awp_navbar_item" )

        }
// --- DEPARTMENT
        if(el_hdrbar_department) {
            const allowed_depbases_count = (setting_dict.allowed_depbases) ? setting_dict.allowed_depbases.length : 0
            const may_select_department = (allowed_depbases_count > 1);

            add_or_remove_class(el_hdrbar_department, "awp_navbaritem_may_select", may_select_department, "awp_navbar_item" )
            let department_txt = null;
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
            el_hdrbar_department.innerText = department_txt;
        }
//>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        if(el_hdrbar_school) {
            // set hove when user has permit to goto different school.
            const permit_select_school = setting_dict.may_select_school;
            console.log("permit_select_school", permit_select_school )
            add_or_remove_class(el_hdrbar_school, "awp_navbaritem_may_select", permit_select_school, "awp_navbar_item" )

            let schoolname_txt = null;
            if (!setting_dict.sel_schoolbase_pk){
                if (setting_dict.may_select_school) {
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
        }
    }  // UpdateHeaderbar

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


//========= isEmpty  ============= PR2019-05-11
    //PR2019-05-05 from https://coderwall.com/p/_g3x9q/how-to-check-if-javascript-object-is-empty'
    function isEmpty(obj) {
        "use strict";
        for(var key in obj) {
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

//========= show_hide_selected_elements_byClass  ====  PR2020-02-19  PR2020-06-20
    function show_hide_selected_elements_byClass(container_classname, contains_classname, container_element) {
        // this function shows / hides elements on page, based on classnames: example: <div class="tab_show tab_shift tab_team display_hide">
        // - all elements with class 'container_classname' will be checked. example:'tab_show' is the container_classname.
        // - if an element contains class 'contains_classname', it will be shown, if not it will be hidden. example: 'tab_shift' and 'tab_team' are classes of the select buttons ('contains_classname')
        // - class 'display_hide' in html is necessary to prevent showing all elements when page opens
        if(!container_element){ container_element = document };
        let list = container_element.getElementsByClassName(container_classname);
        for (let i=0, el; el = list[i]; i++) {
            const is_show = el.classList.contains(contains_classname)
            show_hide_element(el, is_show)
        }
    }  // show_hide_selected_elements_byClass

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
    function refresh_background_class(el, img_class) {
        if (el) {
            let el_img = el.children[0];
            if (el_img){
                el_img.className = img_class;
            }
        }
    }  // refresh_background_class

//========= add_hover_class  =========== PR2020-09-20
    function add_hover_class (el, hover_class, default_class) {
        //console.log(" === add_hover_class === ")
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


//#########################################################################
// +++++++++++++++++ VALIDATORS +++++++++++++++++++++++++++++++++++++++++++

//========= get_number_from_input  ========== PR2020-06-10
    function get_number_from_input(loc, fldName, input_value) {
        //console.log("--------- get_number_from_input ---------")
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

                                    console.log("max_value", max_value, "multiplier", multiplier )
                                    console.log("err_msg", err_msg )
                                }
                            } else if(max_value !== null) {
                                const must_be_str = (is_percentage) ? loc.err_msg_must_be_percentage_less_than_or_equal_to : loc.err_msg_must_be_number_less_than_or_equal_to;
                                err_msg = caption_str + " " + must_be_str + " " + max_value / multiplier + "."
                }
        }}}}};
        return [output_value, err_msg];
    }  // get_number_from_input

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


//#########################################################################
// +++++++++++++++++ MESSAGES +++++++++++++++++++++++++++++++++++++++

//========= render_messages  =================
    function render_messages(awp_messages) {
        console.log( "=== render_messages ")
        console.log( "awp_messages", awp_messages)
        // PR202020-10-30 renders messages
        /*
            {% for message in awp_messages %}
              <div id="{{ message.id }}" class="alert {{ message.class }} alert-dismissible mx-2" role="alert">
                <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                  <span aria-hidden="true">&times;</span>
                </button>
                {{ message.info }}
              </div>
            {% endfor %}
        */

        const el_msg_container = document.getElementById("id_awpmsg_container")
        console.log( "el_msg_container", el_msg_container)
        if (el_msg_container){
            el_msg_container.innerText = null;
            if (!isEmpty(awp_messages)) {
                for (let i = 0 ; i <awp_messages.length; i++) {
                    const awp_message = awp_messages[i];
        console.log( "awp_message", awp_message)
                    if (awp_message){

// --- insert td element,
                        let el_div = document.createElement("div");
                            if(awp_message.id){
                                el_div.id = awp_message.id
                            }
                            el_div.classList.add("alert", "alert-dismissible", "mx-2" )
                            if(awp_message.class){
                                el_div.classList.add(awp_message.class)
                            }
                            el_div.setAttribute("role", "alert")
                            el_div.innerText = (awp_message.info) ? awp_message.info : null;

                            //  <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                            let el_btn = document.createElement("button");
                                el_btn.classList.add("close" )
                                el_btn.setAttribute("data-dismiss", "alert")
                                el_btn.setAttribute("aria-label", "Close")
                                el_btn.innerHTML = "<span aria-hidden=\"true\">&times;</span>";
                            el_div.appendChild(el_btn);
                        el_msg_container.appendChild(el_div);
                    }
                }
            }
        }
    }  // render_messages

