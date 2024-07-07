    "use strict";

// ========= GLOBAL VARIABLES=================== PR2022-07-21
    // these variables are used in all pages

    //console.log("GLOBAL VARIABLES")

    // selected_btn is also used in t_MCOL_Open
    let selected_btn = null;
    let permit_dict = {};
    let setting_dict = {};
    let filter_dict = {};
    let selected = {};
    let loc = {};
    let urls = {};

    const field_settings = {};  // PR2023-04-20 made global


    // examyear_rows and department_rows are used in t_MSED_ PR2022-08-01
    // to be replaced by _dicts PR2023-06-27
    let examyear_rows = [];
    let department_rows = [];  //PR2023-07-11 also used in correctors.js

    // PR2023-01-13  these variables are declared in base.js to make them global variables for t_MUPS_Open
    let school_rows = [];
    let level_rows = [];
    let sector_rows = [];
    let subject_rows = [];
    //let cluster_rows = [];

    const studsubj_dictsNEW = {}; //PR2023-01-05 new approach, dict instead of sorted list
    const cluster_dictsNEW = {}; //PR2023-01-26 new approach, dict instead of sorted list
    const grade_dictsNEW = {}; //PR2023-05-29 only used in secretaxam.js, for now

    const manual_dict = {'test': true}


    // TODO 2023-03-13 change examyear_rows to examyear_dicts
    // new structure: _dicts PR2023-06-27
    const examyear_dicts = {};
    const department_dicts = {};
    const school_dicts = {}; // PR2023-05-29 only used in secretaxam.js, home.js for now

    const cls_hide = "display_hide";
    const cls_hover = "tr_hover";
    const cls_visible_hide = "visibility_hide";
    const cls_selected = "tsa_tr_selected";
    const cls_error = "tsa_tr_error";

    const cls_bc_transparent = "tsa_bc_transparent";

// ============================
    // add csrftoken to ajax header to prevent error 403 Forbidden PR2018-12-03
    // from https://docs.djangoproject.com/en/dev/ref/csrf/#ajax
    const csrftoken = Cookies.get('csrftoken');
    // PR2023-03-13 Sentry error: $ is not defined
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

//=========  AddSubmenuButton  === PR2020-01-26 PR2021-04-26 PR2021-06-23 PR21-10-22
    function AddSubmenuButton(el_div, a_innerHTML, a_function, classnames_list, a_id, a_href, a_download) {
        //console.log(" ---  AddSubmenuButton --- ");
        let el_a = document.createElement("a");
            if(a_id){el_a.setAttribute("id", a_id)};

            if(a_href) {
                el_a.setAttribute("href", a_href);
                if(a_download){ el_a.setAttribute("target", "_blank") };
            };
            el_a.innerHTML = a_innerHTML;

            if(!!a_function){el_a.addEventListener("click", a_function, false)};

            el_a.classList.add("no_select");
            // set background color of btn
            el_a.classList.add("tsa_tr_selected");
            el_a.classList.add("px-2", "mr-2");
            if (classnames_list && classnames_list.length) {
                for (let i = 0, classname; classname = classnames_list[i]; i++) {
                    el_a.classList.add(classname);
                };
            };

            el_div.classList.add("pointer_show");
        el_div.appendChild(el_a);
    };//function AddSubmenuButton

//========= b_UploadSettings  ============= PR2019-10-09
    function b_UploadSettings (upload_dict, url_str) {
        //console.log("=== b_UploadSettings ===");
        //console.log("    url_str", url_str);
        //console.log("    upload_dict", upload_dict);

        if(!!upload_dict) {
            const parameters = {"upload": JSON.stringify (upload_dict)}
            let response = "";
            $.ajax({
                type: "POST",
                url: url_str,
                data: parameters,
                dataType:'json',
                success: function (response) {
                    //console.log( "response", response);
                },
                error: function (xhr, msg) {
                    console.log(msg + '\n' + xhr.responseText);
                }
            });
        }
    };  // b_UploadSettings

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
                            if(depbase_codes) { depbase_codes += ", "};
                            depbase_codes += code;
            }}}};
        };
        return depbase_codes;
    };  // b_get_depbases_display

//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
//========= b_get_permits_from_permitlist  ============= PPR2021-04-26
    function b_get_permits_from_permitlist(permit_dict) {
        //console.log("----- b_get_permits_from_permitlist -----");
        //console.log("permit_dict", permit_dict);
        //console.log("permit_dict.permit_list", permit_dict.permit_list);
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
            dict = default_value};
        return dict;
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
            const is_show = el.classList.contains(contains_classname);
            show_hide_element(el, is_show);
        };
    };  // b_show_hide_selected_elements_byClass

//========= function show_hide_element_by_id  ====  PR2019-12-13
    function show_hide_element_by_id(el_id, is_show) {
        if(el_id){
            let el = document.getElementById(el_id);
            if(el){
                if(is_show){
                    el.classList.remove("display_hide");
                } else{
                    el.classList.add("display_hide");
    }}}};

//========= show_hide_element  ====  PR2019-12-13
    function show_hide_element(el, is_show) {
        if(el){
            if(is_show){
                el.classList.remove("display_hide");
            } else{
                el.classList.add("display_hide");
    }}};

//========= set_element_class  ====  PR2019-12-13
    function set_element_class(el_id, is_add_class, clsName) {
        if(el_id){
            let el = document.getElementById(el_id);
            if(el){
                if(is_add_class){
                    el.classList.add(clsName);
                } else{
                    el.classList.remove(clsName);
        }}};
    };

//========= b_ShowTblrowError_byID  ====  PR2020-04-13
    function b_ShowTblrowError_byID(tr_id) {
        let tblRow = document.getElementById(tr_id);
        b_ShowTblrowError(tblRow);
    };

//========= b_ShowTblrowError set_element_class  ====  PR2020-04-13
    function b_ShowTblrowError(tblRow) {
        if(tblRow){
            tblRow.classList.add(cls_error);
            setTimeout(function (){ tblRow.classList.remove(cls_error); }, 2000);
        };
    };

    function ShowOkRow(tblRow ) {
        // make row green, / --- remove class 'ok' after 2 seconds
        tblRow.classList.add("tsa_tr_ok");
        setTimeout(function (){
            tblRow.classList.remove("tsa_tr_ok");
        }, 2000);
    };

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
    };

//=========  ShowClassWithTimeout  ================ PR2020-04-26 PR2020-07-15 PR2022-04-06
    function ShowClassWithTimeout(el, className, timeout) {
        // show class, remove it after timeout milliseconds
        if(el && className){
            if(!timeout) { timeout = 2000};
            el.classList.add(className);
            setTimeout(function (){el.classList.remove(className)}, timeout);
        };
    };

//=========  UndoInvalidInput  ================ PR2022-06-19
    function UndoInvalidInput(el_input, old_value) {
        // show class, remove it after timeout milliseconds
        if(el_input){
            el_input.classList.add("border_bg_invalid");
            setTimeout(function (){
                el_input.classList.remove("border_bg_invalid");
                el_input.value = old_value;
            }, 2000);
        };
    };

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
    };  // select_elements_in_containerId_byClass

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
    };  // select_elements_in_container_byClass

// ++++++++++++++++ ADD REMOVE CLASS / ATTRIBUTE  +++++++++++++++

//========= add_or_remove_class_with_qsAll  ====================================
    function add_or_remove_class_with_qsAll(el_container, class_name, is_add, filter_class, default_class){
        // add or remove selected cls_hide from all elements with class 'filter_class' PR2020-04-29
console.log(" --- add_or_remove_class_with_qsAll --- ")
console.log("    is_add: ", is_add)
console.log("    filter_class: ", filter_class)
        // from https://stackoverflow.com/questions/34001917/queryselectorall-with-multiple-conditions
        // document.querySelectorAll("form, p, legend") means filter: class = (form OR p OR legend)
        // document.querySelectorAll("form.p.legend") means filter: class = (form AND p AND legend)

         // multipe filter: document.querySelectorAll(".filter1.filter2")
        //let elements =  document.querySelectorAll("." + filter_class)
        let elements = el_container.querySelectorAll(filter_class);
console.log("    elements", elements)
        for (let i = 0, el; el = elements[i]; i++) {
            add_or_remove_class (el, class_name, is_add, default_class);
console.log(el)
        };
console.log(" --- end of add_or_remove_class_with_qsAll --- ")
    };


//========= add_or_remove_class_by_id  ========================  PR2022-04-23
    function add_or_remove_class_by_id (id, class_name, is_add, default_class) {
        const el = document.getElementById(id);
        add_or_remove_class (el, class_name, is_add, default_class);
    };

//========= add_or_remove_class  ========================  PR2020-06-20 PR2023-03-19
    function add_or_remove_class (el, class_name, is_add, default_class) {
        if(el && class_name){
            if (is_add){
                if (default_class){el.classList.remove(default_class)};
                // dont add class if it already exists PR2023-03-19
                if(!el.classList.contains(class_name)){
                    el.classList.add(class_name);
                };
            } else {
                el.classList.remove(class_name);
                if (default_class){
                    // dont add class if it already exists PR2023-03-19
                    if(!el.classList.contains(default_class)){
                        el.classList.add(default_class);
        }}}};
    };

//========= add_or_remove_attr_with_qsAll  ======== PR2020-05-01
    function add_or_remove_attr_with_qsAll(el_container, filter_str, attr_name, is_add, attr_value){
        // add or remove attribute from all elements with filter 'filter_str' PR2020-04-29
    //console.log(" --- add_or_remove_attr_with_qsAll --- ")
    //console.log("is_add: ", is_add)
    //console.log("filter_str: ", filter_str)
        // from https://stackoverflow.com/questions/34001917/queryselectorall-with-multiple-conditions
        // document.querySelectorAll("form, p, legend") means filter: class = (form OR p OR legend)
        // document.querySelectorAll("form.p.legend") means filter: class = (form AND p AND legend)

         // multipe filter: document.querySelectorAll(".filter1.filter2")
        //let elements =  document.querySelectorAll("." + filter_str)
        let elements = el_container.querySelectorAll(filter_str);
        for (let i = 0, len = elements.length; i < len; i++) {
            add_or_remove_attr(elements[i], attr_name, is_add, attr_value);
    //console.log(elements[i])
        };
    };  // add_or_remove_attr_with_qsAll

//========= b_get_element_by_data_value  ======== PR2022-04-15
    function b_get_element_by_data_value(el_container, data_field, data_value){
        if (data_field && data_value) {
            const filter_str = ["[data-", data_field, "='", data_value, "']"].join("");
            return el_container.querySelector(filter_str);
        } else {
            return false;
        };
    };  // b_get_element_by_data_value

//========= add_or_remove_attr  =========== PR2020-05-01
    function add_or_remove_attr (el, attr_name, is_add, attr_value) {
        if(!!el){
            if (is_add){
                el.setAttribute(attr_name, attr_value);
            } else {
                el.removeAttribute(attr_name);
            };
        };
    };  // add_or_remove_attr



//========= get_elements_by_classname_with_qsAll  ====================================
    function get_elements_by_classname_with_qsAll(el_container, class_name){
        // count elements that have classname PR2023-03-17, for now only used in orderlist.js MENVPR
//console.log(" --- count_elements_with_qsAll --- ")
//console.log("is_add: ", is_add)
//console.log("filter_class: ", filter_class)

        // from https://stackoverflow.com/questions/34001917/queryselectorall-with-multiple-conditions
        // document.querySelectorAll("form, p, legend") means filter: class = (form OR p OR legend)
        // document.querySelectorAll("form.p.legend") means filter: class = (form AND p AND legend)

         // multipe filter: document.querySelectorAll(".filter1.filter2")
        //let elements =  document.querySelectorAll("." + filter_class)
        return el_container.querySelectorAll(class_name);

    };  // get_elements_by_classname_with_qsAll





//========= function b_add_hover_delete_btn  =========== PR2021-10-28
    function b_add_hover_delete_btn(el, hover_class, class_1, class_0) {
//- add hover to element, with img_class that contains deleted or not, must be no other classes in this div
        if(!hover_class) {hover_class = "delete_0_2"};
        if(!class_1) { class_1 = "delete_0_2"};
        if(!class_0) { class_0 = "delete_0_1"};
        if(el){
            el.addEventListener("mouseenter", function(){
                const value = get_attr_from_el_int(el, "data-filter");
                el.className = (value) ? class_0 : class_1;
            });
            el.addEventListener("mouseleave", function(){
                const value = get_attr_from_el_int(el, "data-filter");
                el.className = (value) ? class_1 : class_0;
            });
        };
        el.classList.add("pointer_show");
    };  // b_add_hover_delete_btn

//========= function add_hover  =========== PR2020-05-20 PR2020-08-10
    function add_hover(el, hover_class, default_class) {
//- add hover to element
        if(!hover_class){hover_class = "tr_hover"};
        if(el){
            el.addEventListener("mouseenter", function(){
                if(default_class) {el.classList.remove(default_class)};
                el.classList.add(hover_class);
            });
            el.addEventListener("mouseleave", function(){
                if(default_class) {el.classList.add(default_class)};
                el.classList.remove(hover_class);
            });
            el.classList.add("pointer_show");
        };
    };  // add_hover

//=========  append_background_class ================ PR2020-09-10
    function append_background_class(el, default_class, hover_class) {
        if (el) {
            el.classList.add(default_class, "pointer_show");
            // note: dont use on icons that will change, like 'inactive' or 'status'
            // add_hover_class will replace 'is_inactive' icon by default_class
            if (hover_class) {add_hover_class (el, hover_class, default_class)};
        };
    };

//=========  refresh_background_class ================ PR2020-09-12
    function b_refresh_icon_class(el, img_class) {
        if (el) {
            const el_img = el.children[0];
            if (el_img){el_img.className = img_class};
        };
    };  // b_refresh_icon_class

//========= add_hover_class  =========== PR2020-09-20
    function add_hover_class (el, hover_class, default_class) {
        //console.log(" === add_hover_class === ")
        // note: dont use on icons that will change, like 'inactive' or 'status'
        // add_hover_class will replace 'is_inactive' icon by default_class on mouseleave
        if(el && hover_class && default_class){
            el.addEventListener("mouseenter", function() {add_or_remove_class (el, hover_class, true, default_class)});
            el.addEventListener("mouseleave", function() {add_or_remove_class (el, default_class, true, hover_class)});
        };
    };  // add_hover_class

//=========  add_hover  =========== PR2020-06-09
    function add_hover_image(el, hover_image, default_image) {
        //console.log(" === add_hover_image === ")
//- add hover image to element
        if(el && hover_image && default_image){
            const img = el.children[0];
            if(img){
                el.addEventListener("mouseenter", function() { img.setAttribute("src", hover_image) });
                el.addEventListener("mouseleave", function() { img.setAttribute("src", default_image) });
        }};
    };  // add_hover_image

//========= set_focus_on_id_with_timeout  =========== PR2020-05-09 PR2022-11-03
    function set_focus_on_id_with_timeout(id, ms) {
        if(id){
            const el_focus = document.getElementById(id);
            set_focus_on_el_with_timeout(el_focus, ms);
        };
    }; // set_focus_on_id_with_timeout

//========= set_focus_on_el_with_timeout  =========== PR2020-05-09 PR2022-11-03
    function set_focus_on_el_with_timeout(el_focus, ms) {
        if(el_focus){
            if (!ms){ ms = 150};
            setTimeout(function() { el_focus.focus() }, ms);
        };
    };  // set_focus_on_el_with_timeout

//========= b_highlight_BtnSelect  ============= PR2020-02-20 PR2020-08-31
    function b_highlight_BtnSelect(btn_container, selected_btn, btns_disabled){
        //console.log( "//========= b_highlight_BtnSelect  ============= ")
        //console.log( "btn_container", btn_container)
        //console.log( "selected_btn", selected_btn)
        //console.log( "btns_disabled", btns_disabled)

        // ---  highlight selected button
        if (btn_container){
            const btns = btn_container.children;
            for (let i = 0, btn; btn = btns[i]; i++) {
                const data_btn = get_attr_from_el(btn, "data-btn");
                // highlight selected btn
                add_or_remove_class(btn, "tsa_btn_selected", (data_btn === selected_btn) );
                // disable btn, except when btn is selected btn
                btn.disabled = (btns_disabled && data_btn !== selected_btn);
            };
        };
    };  //  b_highlight_BtnSelect

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
        if (!map_dict) {map_dict = {}};
        return map_dict;
    };    // get_mapdict_from_datamap_by_tblName_pk

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
        if (!map_dict) {map_dict = {}};
        return map_dict;
    };

//========= b_get_itemdict_from_datamap_by_el  ============= PR2019-10-12 PR2020-09-13 PR2021-01-014
    function b_get_itemdict_from_datamap_by_el(el, data_map) {
        // function gets map_id form 'data-map_id' of tblRow, looks up 'map_id' in data_map
        let item_dict = {};
        const tblRow = t_get_tablerow_selected(el);
        if(tblRow){
            // was: const map_id = get_attr_from_el(tblRow, "data-table") + "_" + get_attr_from_el(tblRow, "data-pk")
            item_dict = get_mapdict_from_datamap_by_id(data_map, tblRow.id);
        };
        return item_dict;
    };  // b_get_itemdict_from_datamap_by_el

//========= b_get_auth_bool_at_index  ============= PR2021-01-15 PR2021-02-05
    function b_get_auth_bool_at_index(status_sum, index) {
        const status_array = b_get_status_array(status_sum);
        return b_get_status_bool_at_arrayindex(status_array, index);
    };  // b_get_auth_bool_at_index

//========= b_get_status_bool_at_arrayindex  ============= PR2021-02-05
    function b_get_status_bool_at_arrayindex(status_array, index) {
        let status_bool = false;
        if(status_array && index < status_array.length) {
            status_bool = (status_array[index] === 1);
        };
        return status_bool;
    };

//========= b_set_auth_bool_at_index  ============= PR2021-01-15 PR2021-02-05
    function b_set_auth_bool_at_index(status_int, index, new_value) {
        //console.log( " ==== b_set_auth_bool_at_index ====");

        if(status_int == null){status_int = 0};
        let new_status_sum = 0;
        const status_array = b_get_status_array(status_int);
        if(status_array && index < status_array.length) {
    // ---  put new_value at index
            status_array[index] = (new_value) ? 1 : 0;
    // ---  convert to integer
            new_status_sum =  b_get_statussum_from_array(status_array);
        };
        return new_status_sum
    };  // b_set_auth_bool_at_index

//========= b_get_statussum_from_array  =============  PR2021-02-05
    function b_get_statussum_from_array(status_array) {
        // ---  convert to integer
        let status_sum = null;
        if(status_array && status_array.length){
            status_array.reverse();
            const arr_joined = status_array.join("");
            status_sum = parseInt(arr_joined,2);
        };
        return status_sum;
    };

//========= b_get_status_array  ============= PR2021-01-15 PR2021-02-05
    function b_get_status_array(status_sum) {
        //console.log( " ==== b_set_auth_bool_at_index ====");
        const array_length = 15;
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
        };
        // status_array_reversed = [1, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]

        return status_array_reversed;
    };  // b_get_status_array

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
            const auth4 = b_get_status_bool_at_arrayindex(status_array, 4) // STATUS_04_AUTH4 = 16
            const submitted = b_get_status_bool_at_arrayindex(status_array, 5) // STATUS_04_SUBMITTED = 32

            img_class = (submitted) ? "appr_1_5" :
                        (auth1 && auth2 && auth3) ? "appr_1_4" :
                        (auth1 && auth2) ? "appr_0_4" :
                        (auth1 && auth3) ? "appr_1_2" :
                        (auth2 && auth3) ? "appr_1_3" :
                        (auth3) ? "appr_1_1" :
                        (auth2) ? "appr_0_3" :
                        (auth1) ? "appr_0_2" :
                        (created) ? "stat_0_1" : "stat_0_0"

        } else if (status_sum < 128) {img_class = "note_1_2" // STATUS_06_REQUEST = 64
        } else if (status_sum < 256) {img_class = "note_1_3"// STATUS_07_WARNING = 128
        } else if (status_sum < 512) {img_class = "note_1_4"// STATUS_08_REJECTED = 256
        } else if (status_sum < 1024) {img_class = "note_2_2"// STATUS_09_REQUEST_ANSWERED = 512
        //} else if (status_sum < 1024) {img_class = "note_2_3" // STATUS_09_WARNING_ANSWERED = 512
        } else if (status_sum < 2048) {img_class = "note_2_4" // STATUS_10_REJECTED_ANSWERED = 1024
        } else if (status_sum < 4096) {img_class = "note_1_5"  // STATUS_11_EDIT = 2048
        } else if (status_sum < 8192) {img_class = "note_2_5" // STATUS_12_EDIT_ANSWERED = 4096
        } else if (status_sum < 16384) {img_class = "note_2_6"  // STATUS_13_APPROVED = 8192
        } else {img_class = "appr_2_6"}; // STATUS_14_LOCKED = 16384

        //console.log("img_class", img_class);
        return img_class;
    };  // get_status_class

//#########################################################################

// +++++++++++++++++ DATA DICTS PR2023-02-22 +++++++++++++++++++++++++++++++++++++++

//=========  b_fill_datadicts_by_mapid  ===  PR2023-04-16
    function b_fill_datadicts_by_mapid(data_rows, data_dicts) {
        //console.log("=====  b_fill_datadicts_by_mapid ===== ");

    // - clear data_dicts
        b_clear_dict(data_dicts);

        if (data_rows && data_rows.length){
            for (let i = 0, row; row = data_rows[i]; i++) {
                data_dicts[row.mapid] = row;
            };
        };
    };
//=========  b_fill_datadicts  ===  PR2023-02-22
    function b_fill_datadicts(tblName, fldName_pk1, fldName_pk2, data_rows, data_dicts) {
        //console.log("=====  b_fill_datadicts ===== ");

    // - clear data_dicts
        b_clear_dict(data_dicts);

        if (data_rows && data_rows.length){
            for (let i = 0, row; row = data_rows[i]; i++) {
                //const pk1_int = (tblName === "cluster") ? row.id : row.stud_id;
                const pk_1int = (fldName_pk1 && fldName_pk1 in row) ? row[fldName_pk1] : 0;
                const pk_2int = (fldName_pk2 && fldName_pk2 in row) ? row[fldName_pk2] : null;
                const key_str = b_get_datadicts_keystr(tblName, pk_1int, pk_2int);
                data_dicts[key_str] = row;
            };
        };
        //console.log("    tblName", tblName);
        //console.log("    data_dicts", data_dicts);
    };  // b_fill_datadicts

    function b_get_datadicts_keystr(tblName, pk_1int, pk_2int) {  // PR2023-01-05 PR2023-02-24

        let key_str = tblName + "_" + ((pk_1int) ? pk_1int : 0);
        if (pk_2int) {
            key_str += "_" + pk_2int;
        };
        return key_str
    };  // b_get_datadicts_keystr


// +++++++++++++++++ DATAMAP to be deprecated +++++++++++++++++++++++++++++++++++++++

//=========  b_fill_datamap  ================ PR2020-09-06
    function b_fill_datamap(data_map, rows) {
        //console.log(" --- b_fill_datamap  ---");
        //console.log("rows", rows);
        data_map.clear();
        if (rows && rows.length) {
            for (let i = 0, dict; dict = rows[i]; i++) {
                data_map.set(dict.mapid, dict);
            };
        };
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
    };  // deepcopy_dict


//=========  copy_updatedict_to_datadict  ================ PR2022-08-14
    function copy_updatedict_to_datadict(data_dict, update_dict, field_names, updated_columns){
    // ---  loop through fields of update_dict
        for (const [key, new_value] of Object.entries(update_dict)) {
            if (key in data_dict){
                if (new_value !== data_dict[key]) {
// ---  update field in data_row when value has changed
                    data_dict[key] = new_value;
// ---  add field to updated_columns list when field exists in field_names
                    if (field_names && field_names.includes(key)) {
// ---  add field to updated_columns list
                        updated_columns.push(key);
        }}}};
    };  // copy_updatedict_to_datadict

//#########################################################################
// +++++++++++++++++ SORT DICTIONARY +++++++++++++++++++++++++++++++++++++++

//========= b_comparator_sortby  =========  PR2020-09-03
// PR2020-09-01 from: https://stackoverflow.com/questions/5435228/sort-an-array-with-arrays-in-it-by-string/5435341
// explained in https://www.javascripttutorial.net/javascript-array-sort/
// function used in Array.sort to sort list of dicts by key 'sortby', null or '---' last  PR2021-02-25
    function b_comparator_sortby(a, b) {
        const max_len = 24 // CODE_MAX_LENGTH = 24;
        const z_str = "z".repeat(max_len);

        const a_lc = (a.sortby && a.sortby !== "---" && a.sortby !== "-") ? a.sortby.toLowerCase() : z_str;
        const b_lc = (b.sortby && b.sortby !== "---" && b.sortby !== "-") ? b.sortby.toLowerCase() : z_str;

        if (a_lc < b_lc) return -1;
        if (a_lc > b_lc) return 1;
        return 0;
    };  // b_comparator_sortby

// this one sorts integers, only used in mailbox.js mailinglist MML_Save - for now PR2021-10-22
    function b_comparator_sortby_integer(a, b) {
    // PR2021-02-25 from https://stackoverflow.com/questions/1063007/how-to-sort-an-array-of-integers-correctly
       // exc_subject_ColIndex_list.sort((a, b) => a - b);
       return a - b;
    };

//========= b_comparator_sequence  =========  PR2023-02-21
// PR2020-09-01 from: https://stackoverflow.com/questions/5435228/sort-an-array-with-arrays-in-it-by-string/5435341
// explained in https://www.javascripttutorial.net/javascript-array-sort/
// function used in Array.sort to sort list of dicts by integer key 'sequence' PR2023-02-21
    function b_comparator_sequence(a, b) {
        if (a.sequence < b.sequence) return -1;
        if (a.sequence > b.sequence) return 1;
        return 0;
    };  // b_comparator_sequence

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
    };


//=========  parse_dateJS_from_dateISO ================ PR2023-01-28
    function get_birthdate_from_idnumber(id_number) {
        //console.log( "===== get_birthdate_from_idnumber  ========= ");
        //console.log( "    id_number", id_number);

        let birthdate_iso = null;
        if (id_number){

        // see https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/Date#return_value
        // and https://bobbyhadz.com/blog/javascript-create-date-without-timezone

    // remove dots
            const id_number_str = id_number.replaceAll('.', '')
            const len = id_number_str.length;

    // idnumber without dots must have 8 characters at least
            if(len >= 8){
                const year_str = id_number_str.slice(0, 4);
                const month_str = id_number_str.slice(4, 6);
                const day_str = id_number_str.slice(6, 8);

        //console.log( "    year_str", year_str, "month_str", month_str, "day_str", day_str);

    // check if is numeric
                const year_int = Number(year_str);
                const current_year = new Date().getFullYear() ; // returns the current year

                if (year_int && year_int > 1900 && year_int < current_year){
                    const month_int = Number(month_str);
                    const day_int = Number(day_str);
                    if (month_int && month_int <= 12){
                        if (day_int  && day_int <= 31){
                            const month_index = month_int -1;
                            const birthdate_JS = new Date(year_int, month_index, day_int);

        //console.log( "    birthdate_JS", birthdate_JS);

        // ATTENTION: 2010-02-30 converts to JS date: Tue Mar 02 2010 00:00:00 GMT+0100 (Central European Standard Time)
        // solved by checking if month index is correct
                            if (birthdate_JS && birthdate_JS.getMonth() === month_index) {
                                birthdate_iso = [year_str, month_str, day_str].join("-");
        }}}}}};

        return birthdate_iso;
    };  // get_birthdate_from_idnumber

//=========  parse_dateJS_from_dateISO ================ PR2020-07-22
    function parse_dateJS_from_dateISO(date_iso) {
        //console.log( "===== parse_dateJS_from_dateISO  ========= ");
        // function creates date in local timezone.
        // date_iso = '2020-07-22T12:03:52.842Z'
        // date_JS = Wed Jul 22 2020 08:03:52 GMT-0400 (Bolivia Time)

        // PR2022-03-09 debug: dont use this one for dates.
        // date_JS gives birthdate one day before birthdate, because of timezone
        // data_dict.birthdate 2004-05-30 becomes date_JS = Sat May 29 2004 20:00:00 GMT-0400 (Venezuela Time)
        // use format_date_from_dateISO instead
        // was:
        // const date_JS = parse_dateJS_from_dateISO(data_dict.birthdate);


        //https://bobbyhadz.com/blog/javascript-create-date-without-timezone


        let date_JS = null;
        if (date_iso){
           date_JS =  new Date(Date.parse(date_iso));
        };
        return  date_JS;
    };  // parse_dateJS_from_dateISO

//========= get_now_arr ========== PR2020-07-08 tsa
    function get_now_arr() {
        // send 'now' as array to server, so 'now' of local computer will be used
        const now = new Date();
        const now_arr = [now.getFullYear(), now.getMonth() + 1, now.getDate(), now.getHours(), now.getMinutes()];
        return now_arr;
    };

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

    };  // format_time_from_offset_JSvanilla


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
        };

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
                                };
                            } else if(max_value !== null) {
                                const must_be_str = (is_percentage) ? loc.err_msg_must_be_percentage_less_than_or_equal_to : loc.err_msg_must_be_number_less_than_or_equal_to;
                                err_msg = caption_str + " " + must_be_str + " " + max_value / multiplier + ".";
                };
        }}}}};
        return [output_value, err_msg];
    };  // b_get_number_from_input

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
    };  // validate_blank_unique_text


//######### IT WORKS !!! #################################################################
// +++++++++++++++++ LOOKUP dict in ordered dictlist +++++++++++++++++++++++++++ PR2021-06-16

//========= b_get_datadict_by_integer_from_datarows  ================== PR2021-07-25
    function b_get_datadict_by_integer_from_datarows(data_rows, lookup_1_field, search_1_int, lookup_2_field, search_2_int){
        // studsubj order by: 'ORDER BY st.id, studsubj.studsubj_id NULLS FIRST'
        const [middle_index, found_dict, compare] = b_recursive_integer_lookup(data_rows, lookup_1_field, search_1_int, lookup_2_field, search_2_int);
        const data_dict = (!isEmpty(found_dict)) ? found_dict : null;
        return data_dict;
    };

//========= b_get_mapdict_from_datarows  ================== PR2021-06-21
    // NOT IN USE PR2021-09-18
    function b_get_mapdict_from_datarows(data_rows, map_id, user_lang){
        const [middle_index, found_dict, compare] = b_recursive_lookup(data_rows, map_id, user_lang);
        const data_dict = (!isEmpty(found_dict)) ? found_dict : null;
        return data_dict;
    };

//========= b_recursive_integer_lookup  ========== PR2020-07-14 PR2020-07-25
    function b_recursive_integer_lookup(data_rows, lookup_1_field, search_1_int, lookup_2_field, search_2_int){
        //console.log( " ----- b_recursive_integer_lookup -----");
    //console.log( "data_rows", data_rows);

        // function can handle list of 2 ^ (max_loop -2) rows , which is over 1 million rows
        // don't use recursive function, it is less efficient than a loop because it puts each call in the stack
        // function returns rowindex of searched value, or rowindex of row to be inserted
        // data_rows must be ordered by id, done by server

    //console.log( ".....lookup_1_field: ", lookup_1_field, "search_1_int:", search_1_int);
    //console.log( ".....lookup_2_field: ", lookup_2_field, "search_2_int:", search_2_int);

        let compare = null, middle_index = null, found_dict = null;
        // PR2021-11-01 debug. when looking up new item search_1_int = 0, returned row when there was only one row.
        // add check that search_1_int must have value, also lookup_1_field
        // was: if (data_rows && data_rows.length){
        if (lookup_1_field && search_1_int && data_rows && data_rows.length){
            const last_index = data_rows.length - 1;
            let min_index = 0;
            let max_index = last_index;
            middle_index =  Math.floor( (min_index + max_index) / 2);

            // not necessary any more
            if(!search_1_int){search_1_int = 0};
            if(!search_2_int){search_2_int = 0};

            const max_loop = 25;
            for (let i = 0; i < max_loop; i++) {
                if (i === max_loop - 1) {
                // exit when loop not breaked (should not be possible), put index at end of list
                    compare_1 = 1;
                    middle_index = last_index;
                    break;
                } else {
    //console.log( i, "LOOP : ", min_index, " - ", max_index, " > ", middle_index);
    //console.log( ".....middle_index: ", middle_index);
                    const middle_dict = data_rows[middle_index];
    //console.log( ".....middle_dict: ", middle_dict);

                    // studsubj_id can be None, it is ordered first so it can be given the value of 0 in lookup
                    const middle_1_value = (middle_dict[lookup_1_field]) ? middle_dict[lookup_1_field] : 0;
                    const middle_2_value = (middle_dict[lookup_2_field]) ? middle_dict[lookup_2_field] : 0;

    //console.log( ".....middle_value: ", middle_1_value, typeof middle_1_value, " --- ", middle_2_value, typeof middle_2_value);
    //console.log( ".....search_int  : ", search_1_int, typeof search_1_int , " --- ", search_2_int, typeof search_2_int);
                    // NULL values are sorted last in default ascending order.
                    const compare_1 = (search_1_int === middle_1_value) ? 0 :
                                (search_1_int  >  middle_1_value) ? 1 : -1;
                    if (!compare_1){
                        const compare_2 = (search_2_int === middle_2_value) ? 0 :
                                        (search_2_int  >  middle_2_value) ? 1 : -1;
                        compare = compare_2;
                    } else {
                        compare = compare_1;
                    }
    //console.log( "    compare : ", compare);
                    if (!compare) {
                        found_dict = middle_dict;
                        break;
                    } else {
                        if (min_index === max_index){
                            break;
                        } else {
                            if (compare < 0) {
                                if (middle_index === min_index){
                                    break;
                                } else {
                                    max_index = middle_index - 1;
                                    middle_index =  Math.floor( (min_index + max_index) / 2);
                                }
                            } else if (compare > 0) {
                                if (middle_index === max_index){
                                    break;
                                } else {
                                    min_index = middle_index + 1;
                                    middle_index =  Math.ceil( (min_index + max_index) / 2);
                                };
                            };
                        };
                    };
                };  // if (i > 23)
            };  // for (let i = 0,
        };  //  if (data_rows && data_rows.length){

    //console.log( "    middle_index: ", middle_index);
    //console.log( "    found_dict: ", found_dict);
    //console.log( "    compare: ", compare);

        return [middle_index, found_dict, compare];
    };  // b_recursive_integer_lookup

//========= b_recursive_lookup  ========== PR2020-06-16
    function b_recursive_lookup(data_rows, search_value, user_lang){
        //console.log( " ----- b_recursive_lookup -----");
        // function can handle list of 2 ^ (max_loop -2) rows , which is over 1 million rows
        // don't use recursive function, it is less efficient than a loop because it puts each call i the stack
        // function returns rowindex of searched value, or rowindex of row to be inserted
        // data_rows must be ordered by id (as text field), done by server

    //console.log( "data_rows: ", data_rows);

        let compare = null, middle_index = null, found_dict = null;
        if (data_rows && data_rows.length){
            const lookup_field = "mapid";
            const last_index = data_rows.length - 1;
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
                    const middle_dict = data_rows[middle_index];
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
                                };
                            };
    //console.log( "GOTO NEXT LOOP 2 : ", min_index, " - ", max_index, " >< ", middle_index);
                        };
                    };
                };  // if (i > 23)
            };  // for (let i = 0,
        };  //  if (data_rows && data_rows.length){

    //console.log( "found_dict: ", found_dict);
    //console.log( "compare: ", compare);
        return [middle_index, found_dict, compare];
    };  // b_recursive_lookup

//========= b_recursive_tblRow_lookup  ========== PR2020-06-16
    function b_recursive_tblRow_lookup(tblBody, user_lang, search_value_1, search_value_2, search_value_3,
                descending_order_1, descending_order_2, descending_order_3){
        //console.log( " ----- b_recursive_tblRow_lookup -----");
        // function can handle list of 2 ^ (max_loop -2) rows , which is over 1 million rows
        // don't use recursive function, it is less efficient than a loop because it puts each call i the stack
        // function returns rowindex of searched value, or rowindex of row to be inserted

        const lookup_field_1 = "data-ob1", lookup_field_2 = "data-ob2", lookup_field_3 = "data-ob3";
        let compare = null, middle_index = null, found_row = null;
        const last_index = (tblBody.rows && tblBody.rows.length) ? tblBody.rows.length -1 : 0;
        // TODO test descending
        const is_desc_1 = (descending_order_1) ? -1 : 1;  // value = 1 when not descending
        const is_desc_2 = (descending_order_2) ? -1 : 1;  // value = 1 when not descending
        const is_desc_3 = (descending_order_3) ? -1 : 1;  // value = 1 when not descending
    //console.log( "last_index: ", last_index);
        if (tblBody.rows && tblBody.rows.length){
            let min_index = 0;
            let max_index = last_index;
            middle_index =  Math.floor( (min_index + max_index) / 2);

            const s_val_1 = (search_value_1) ? search_value_1.toString().toLowerCase() : "";
            const s_val_2 = (search_value_2) ? search_value_2.toString().toLowerCase() : "";
            const s_val_3 = (search_value_3) ? search_value_3.toString().toLowerCase() : "";

            const max_loop = 25;
            for (let i = 0; i < max_loop; i++) {
                if (i > 23) {
                // exit when loop not breaked (should not be possible), put index at end of list
                    compare = 1 * is_desc_1;
                    middle_index = last_index;
                    break;
                } else {
                    const tblRow = tblBody.rows[middle_index];
                    const middle_value_field_1 = get_attr_from_el(tblRow, lookup_field_1, "");
                    const middle_value_field_2 = get_attr_from_el(tblRow, lookup_field_2, "");
                    const middle_value_field_3 = get_attr_from_el(tblRow, lookup_field_3, "");

    //console.log( i, "LOOP : ", min_index, " - ", max_index, " > ", middle_index);
    //console.log( "lookup_values: ", search_value_1, " - ",  search_value_2, " - ", search_value_3);
    //console.log( "row_values: ", middle_value_field_1, " - ",  middle_value_field_2, " - ", middle_value_field_3);

                    // PR2021-06-08 note: toLowerCase is not necessary, because sensitivity: 'base' ignores lower- / uppercase and accents;
                    // sort function from https://stackoverflow.com/questions/51165/how-to-sort-strings-in-javascript
                    // localeCompare from https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/localeCompare
                    // 'acu'.localeCompare('giro') = -1
                    // 'mcb'.localeCompare('giro') = 1
                    // note: value of compare can be 2 or -2 in some browsers, therefore use compare < 0 instead of compare === -1
                    const compare1 = is_desc_1 * s_val_1.localeCompare(middle_value_field_1, user_lang, {sensitivity: 'base'});
                    // if first lookup field matches: compare has value of second field
                    // if first lookup field does not match: compare has value of first field
                    if (!compare1){
                        const compare2 = is_desc_2 * s_val_2.localeCompare(middle_value_field_2, user_lang, {sensitivity: 'base'});
                        if (!compare2){
                             compare = is_desc_3 * s_val_3.localeCompare(middle_value_field_3, user_lang, {sensitivity: 'base'});
                        } else {
                            compare = compare2;
                        };
                    } else {
                        compare = compare1;
                    };
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
                }}}}};  // if (i > 23)
            };  // for (let i = 0

            // set index = -1 when new row comes after last tablerow, add 1 to index at other rows
            if (compare > 0) {
                if (middle_index === last_index){
                    middle_index = -1;
                } else {
                    middle_index += 1;
                };
            };
        } else {
            // table is empty
            compare = -1;
            middle_index = -1;
        };  //  if (tblBody.rows && tblBody.rows.length)

    //console.log( "return : index", middle_index, " found_row ", found_row, " compare ", compare);
        return middle_index;
    };  // b_recursive_tblRow_lookup

// when list is not sorted - lookup the oldfashioned way
//========= b_lookup_dict_in_dictlist  ========== PR2020-06-25  PR2022-06-02
    function b_lookup_dict_in_dictlist(dictlist, search_field_01, search_value_01, search_field_02, search_value_02){
        let lookup_dict = null;
        for (let i = 0, lookup_value_01, lookup_value_02, dict; dict = dictlist[i]; i++) {
            lookup_value_01 = dict[search_field_01];
            if (search_field_02) { lookup_value_02 = dict[search_field_02] };
            if(lookup_value_01 && lookup_value_01 === search_value_01){
                if (!lookup_value_02) {
                    lookup_dict = dict;
                    break;
                } else if(lookup_value_02 === search_value_02){
                    lookup_dict = dict;
                    break;
                };
            };
        };
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
            };
        };
        return [lookup_index, lookup_dict];
    };  // b_lookup_dict_in_dictlist

//=========  b_remove_item_from_array  ================ PR2021-07-07
    function b_remove_item_from_array(array, value){
        // PR2021-07-07 remove item from array used in mod select columns
        // from https://stackoverflow.com/questions/3954438/how-to-remove-item-from-array-by-value
        // PR2022-11-06 https://love2dev.com/blog/javascript-remove-from-array/#remove-from-array-splice-value

        if(array && array.length){
            for (let i = 0, item; item = array[i]; i++) {
                if (item === value){
                    array.splice(i, 1);
                    break;
                };
            };
        };
    }; // b_remove_item_from_array

// =========  b_remove_item_from_array2  === PR2021-10-20 NOT IN USE yet
    function b_remove_item_from_array2(array, item){
        // from https://stackoverflow.com/questions/3954438/how-to-remove-item-from-array-by-value
        // this function returns a new array without element 'item'
        // In ECMA6 (arrow function syntax):
        const new_array = array.filter(e => e !== item);

        return new_array;
    }; // b_remove_item_from_array2

//=========  b_copy_array_noduplicates  ================ PR2021-12-16 PR2022-07-21
    function b_copy_array_noduplicates(old_array, new_array, skip_clear){
        if (!skip_clear){
            b_clear_array(new_array);
        };
        // skip if old_array is not an array type
        if(old_array && Array.isArray(old_array)){
            if(old_array.length){
                for (let i = 0, item; item = old_array[i]; i++) {
        // skip if item already exists in new_array
                    if (!new_array.includes(item)){
                        new_array.push(item);
                    };
                };
            };
        };
        // from https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/filter?retiredLocale=nl
        // new_array = array.filter(item => true);
    };  // b_copy_array_noduplicates

//=========  b_copy_array_noduplicates  ================ PR2022-07-21
    function b_copy_array_to_new_noduplicates(old_array){
        const new_array = [];
        // skip if old_array is not an array type
        if(old_array && Array.isArray(old_array)){
            if(old_array.length){
                for (let i = 0, item; item = old_array[i]; i++) {
        // skip if item already exists in new_array
                    if (!new_array.includes(item)){
                        new_array.push(item);
                    };
                };
            };
        };
        // from https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/filter?retiredLocale=nl
        // new_array = array.filter(item => true);
        return new_array;
    };  // b_copy_array_noduplicates

//=========  b_clear_array  ================ PR2021-07-07 PR2022-03-24 PR2023-07-20
    function b_clear_array(array){
        // according to https://stackoverflow.com/questions/1232040/how-do-i-empty-an-array-in-javascript
        // according to https://stackoverflow.com/questions/1232040/how-do-i-empty-an-array-in-javascript
        if(array){
            array.length = 0
        };

        //if(array){
        //    array.splice(0, array.length);
        //};

       // clear the array. from https://love2dev.com/blog/javascript-remove-from-array/
        //if(array){
        //    while (array.length) {
        //        array.pop();
        //    };
        //};

    };  // b_clear_array

//=========  b_clear_dict  ================ PR2021-10-23
    function b_clear_dict(dict){
       // remove all key / value pairs from a dictionary. from https://attacomsian.com/blog/javascript-iterate-objects
        if(dict){
            for (const key in dict) {
                if (dict.hasOwnProperty(key)) {
                    delete dict[key];
                };
            };
        };
    };  // b_clear_dict

//========= b_get_multiple_auth_index_of_requsr  ======== PR2022-02-22
    function b_get_multiple_auth_index_of_requsr(permit_dict){
        // function returns list of 0/1 values, key = auth_index, val 0 = false, 1 = true
        // USERGROUP_AUTH1_PRES, USERGROUP_AUTH2_SECR, USERGROUP_AUTH3_EXAM, USERGROUP_AUTH4_CORR

    //console.log( "-----  b_get_multiple_auth_index_of_requsr  -----");
    //console.log( "permit_dict", permit_dict);

        // index = 1 of auth1, value 1 = has permit, 0 = no permit
        const permit_auth_list = [null, 0, 0, 0, 0]
        if (permit_dict.usergroup_list){
            for (let i = 1; i < 5; i++) {
                if (permit_dict.usergroup_list.includes("auth" + i)){
                    permit_auth_list[i] = 1;
        }}};
    //console.log( "permit_auth_list", permit_auth_list);
        return permit_auth_list;
    };  // b_get_multiple_auth_index_of_requsr

//========= b_get_auth_index_pres_secr_of_requsr  ======== PR2022-02-24
    function b_get_auth_index_pres_secr_of_requsr(loc, permit_dict){
        // function returns auth_index of auth user, only pres and secr, ignores examiner an corrector
        // only used in exam approve
        // gives err messages when requsr his both auth pres and auth secr

        //console.log( "-----  b_get_auth_index_pres_secr_of_requsr  -----");
        //console.log( "permit_dict.usergroup_list", permit_dict.usergroup_list);
        let is_auth_1 = false, is_auth_2 = false, auth_index = 0;

        if (permit_dict.usergroup_list){
            is_auth_1 = permit_dict.usergroup_list.includes("auth1");
            is_auth_2 = permit_dict.usergroup_list.includes("auth2");
        };

// skip if user has no auth usergroup
        if (is_auth_1 && is_auth_2){
// show msg error if user has multiple auth usergroups
            const functions = loc.Chairperson + loc._and_ + loc.Secretary;
            const msg_html = loc.approve_err_list.You_have_functions + functions + ". " + "<br>" +
                        loc.approve_err_list.Only_1_allowed;
            b_show_mod_message_html(msg_html);
        } else if (is_auth_1){
            auth_index = 1;
        } else if (is_auth_2){
            auth_index = 2;
        };
        return auth_index;
    };  // b_get_auth_index_pres_secr_of_requsr

//========= b_get_auth_index_of_requsr  ======== // PR2021-03-26 PR2021-07-26 PR2021-12-18 PR2023-05-16 PR2023-09-11
    function b_get_auth_index_of_requsr(loc, permit_dict, auth12_only){
        // function returns auth_index of auth user, returns 0 when user has none or multiple auth usergroups
        //
        // gives err messages when multiple found.
        // STATUS_01_AUTH1 = 2,  STATUS_02_AUTH2 = 4, STATUS_03_AUTH3 = 8, STATUS_04_AUTH3 = 16

        //console.log( "-----  b_get_auth_index_of_requsr  -----");
        //console.log( "permit_dict", permit_dict);

        let auth_index = 0;
        // key = '1' of auth1, value 1 = has permit, 0 = no permit
        const permit_auth = {1: 0, 2: 0, 3: 0, 4: 0}
        if (permit_dict.usergroup_list){
            for (let i = 1; i < 5; i++) {
                if (permit_dict.usergroup_list.includes("auth" + i)){
                    auth_index = i;
                    permit_auth[i] = 1;
        }}};
    //console.log( "permit_auth", permit_auth);
        const is_chairperson_and_secretary = (permit_auth[1] === 1 && permit_auth[2] === 1);
        const is_examiner_and_corrector =  (permit_auth[3] === 1 && permit_auth[4] === 1);
    //console.log( "is_chairperson_and_secretary[3]", is_chairperson_and_secretary, typeof is_chairperson_and_secretary);
    //console.log( "is_examiner_and_corrector[3]", is_examiner_and_corrector, typeof is_examiner_and_corrector);

// skip if user has no auth usergroup

        if (auth_index){
    // if user has multiple auth usergroups: show msg error and set auth_index = 0
            if ( is_chairperson_and_secretary || (!auth12_only && is_examiner_and_corrector)  ){
                auth_index = 0;

    // show msg error if user has multiple auth usergroups
                const functions = (is_chairperson_and_secretary) ? loc.Chairperson + loc._and_ + loc.Secretary :
                                  (is_examiner_and_corrector) ? loc.Second_corrector + loc._and_ + loc.Examiner : "";

                const msg_html = ["<p class='p-2 border_bg_invalid'>", loc.You_have_functions_of,functions, ".<br>",
                                    loc.Only_1_allowed, "</p>"].join('');
                b_show_mod_message_html(msg_html);
            };
        };
        return auth_index;
    };  // b_get_auth_index_of_requsr

//========= b_get_function_of_auth_index  ======== // PR2022-03-07
    function b_get_function_of_auth_index(loc, auth_index){
        return (auth_index === 1) ? loc.Chairperson :
                (auth_index === 2) ? loc.Secretary :
                (auth_index === 3) ? loc.Examiner :
                (auth_index === 4) ? loc.Corrector : "-";
    };  // b_get_function_of_auth_index

//#########################################################################
// +++++++++++++++++ MESSAGES +++++++++++++++++++++++++++++++++++++++
    function b_show_mod_message_html(msg_html, header_text, max_size, ModMessageClose){
    // PR2021-01-26 PR2021-03-25 PR2021-07-03
        // TODO header, set focus after closing messagebox

        //console.log( " -----b_show_mod_message_html -----");
        //console.log( "    msg_html", msg_html);
        //console.log( "    header_text", header_text);
        //console.log( "    max_size", max_size);

        const el_msg_header = document.getElementById("id_mod_message_header");
        if(el_msg_header){el_msg_header.innerText = (header_text) ? header_text : null};

        const el_msg_container = document.getElementById("id_mod_message_container");
        if(el_msg_container){el_msg_container.innerHTML = (msg_html) ? msg_html : null};

        const el_msg_btn_cancel = document.getElementById("id_mod_message_btn_cancel");
        if(el_msg_btn_cancel){set_focus_on_el_with_timeout(el_msg_btn_cancel, 150 )};

    // hide btn 'Dont show again - used in anouncements - anouncements use b_show_mod_message_dictlist PR2022-06-01
        const el_mod_message_btn_hide = document.getElementById("id_mod_message_btn_hide");
        add_or_remove_class(el_mod_message_btn_hide, cls_hide, true);

        $("#id_mod_message").modal({backdrop: true});

        const el_mod_message_size = document.getElementById("id_mod_message_size");
        const size_class = (max_size === "xl") ?  "modal-xl" : (max_size === "lg") ? "modal-lg" : "modal-md";
    //console.log( "    size_class", size_class);
        add_or_remove_class(el_mod_message_size, size_class, (["xl", "lg"].includes(max_size)), "modal-md");
    //console.log( "    el_mod_message_size", el_mod_message_size);

        /*
        'hide.bs.modal' executes when the .modal (modal window) gets closed.
         So, whenever you open a modal window with the class modal (obviously),
         at some point it gets closed. When that modal window gets hidden (or closed)
         the event hidden.bs.modal gets triggered and the function gets executed.
         This is not managed by the user (you didn't write explicit code) but the Bootstrap library has it built in.
        */

        $('#id_mod_message').on('hide.bs.modal', function (e) {
            try {
                // ModMessageClose sets the focus to the element mod_dict.el_focus
                // in userpage MUPS_Open it close modal PR2022-10-26
                ModMessageClose();
            } catch (error) {
            }
        });
    };  // b_show_mod_message_html


// +++++++++++++++++ MESSAGES +++++++++++++++++++++++++++++++++++++++
    function b_show_mod_message_html_with_border(msg_list, border_class, header_text, max_size, ModMessageClose){
    // PR2024-06-30
        if (msg_list && msg_list.length){
            if (!border_class) { border_class = ''};
            const html_list = ["<p class='p-2 ", border_class, "'>"];
            html_list.push(...msg_list);
            html_list.push("</p>");
            const msg_html = html_list.join("");
            b_show_mod_message_html(msg_html, header_text, max_size, ModMessageClose)
        };
    };  // b_show_mod_message_html_with_border


//=========  b_show_mod_message_dictlist  ================ PR2021-06-27  PR2021-07-03 PR2021-12-01 PR2022-08-28
    function b_show_mod_message_dictlist(msg_dictlist, skip_warning_messages) {
        //console.log("==== b_show_mod_message_dictlist  ======")
        //console.log("msg_dictlist", msg_dictlist, typeof msg_dictlist)
        //console.log("skip_warning_messages", skip_warning_messages)

        //  [ { class: "border_bg_invalid", header: 'Update this', msg_html: "An eror occurred."]
        // added for anouncements: key 'size' and 'btn_hide'
        //  {'msg_html': [msg], 'class': 'border_bg_transparent', 'size': 'lg', 'btn_hide': True}

        const el_container = document.getElementById("id_mod_message_container");

        //console.log("el_container", el_container);

        if(el_container){
            if(msg_dictlist){
                // convert to list when msg_dictlist is not a list
                if (!Array.isArray(msg_dictlist)){
                    msg_dictlist = [msg_dictlist];
                };

                if(msg_dictlist.length){
                    // when skip_warning_messages = true:
                    // skip showing warning messages,
                    // in page grade msg 'Not current examyear' kept showing) PR2021-12-01
                    // used in page grade (for now)
                    let has_non_warning_msg = false;

                    let header_text = null, max_size = "md";
                    let show_btn_dontshowagain = false;
                    el_container.innerHTML = null;
                    for (let i = 0, msg_dict; msg_dict = msg_dictlist[i]; i++) {

                    //console.log("is object", (typeof msg_dict === "object"))
            // skip if msg_dict is not a dictionary
                        if (typeof msg_dict  === "object") {

                //console.log("msg_dict", msg_dict)
                            let class_str = null;
                            if ("header" in msg_dict && msg_dict.header ) {
                                // msgbox only has 1 header. Use first occurring header
                                if (!header_text){ header_text = msg_dict.header};
                            };

                            if ("class" in msg_dict && msg_dict.class ) {
                                // each msg_html has a border
                                class_str = msg_dict.class;
                                if (class_str !== "border_bg_warning") { has_non_warning_msg = true };
                            };

                            if ("msg_html" in msg_dict && msg_dict.msg_html ) {
                    // --- create div element with alert border for each message in messages
                                const el_border = document.createElement("div");
                                if (!class_str) { class_str = "border_bg_transparent"};
                                el_border.classList.add(class_str, "p-2", "my-2");
                                const el_div = document.createElement("div");
                                el_div.innerHTML = msg_dict.msg_html;
                                el_border.appendChild(el_div);
                                el_container.appendChild(el_border);
                            };

                // set size of modal - used in anouncements
                            // {'msg_html': [msg], 'class': 'border_bg_transparent', 'size': 'lg', 'btn_hide': True}
                            if (msg_dict.size === "lg") {
                                max_size = "lg";
                            };

                            if (msg_dict.btn_hide){
                                show_btn_dontshowagain = true;
                            };
                        };
                    };
        // set size of modal - used in anouncements
                    // {'msg_html': [msg], 'class': 'border_bg_transparent', 'size': 'lg', 'btn_hide': True}
                    const el_mod_message_size = document.getElementById("id_mod_message_size")
                    add_or_remove_class(el_mod_message_size, "modal-lg", (max_size === "lg"), "modal-md");

        // show btn 'Dont show again - used in anouncements
                    const el_mod_message_btn_hide = document.getElementById("id_mod_message_btn_hide");
                    add_or_remove_class(el_mod_message_btn_hide, cls_hide, !show_btn_dontshowagain);

            //console.log("!skip_warning_messages || has_non_warning_msg", !skip_warning_messages || has_non_warning_msg)
                    if (!skip_warning_messages || has_non_warning_msg ){
                        const el_header = document.getElementById("id_mod_message_header");
                        if(el_header) {el_header.innerText = header_text};
            // ---  set focus to close button - not working
                        const el_btn_cancel = document.getElementById("id_mod_message_btn_cancel");
                        set_focus_on_el_with_timeout(el_btn_cancel, 150);

    //console.log( "    id_mod_message")
                        $("#id_mod_message").modal({backdrop: true});
                    };
                };
            };
        }; // if(el_container)
        skip_warning_messages = false;
    };  // b_show_mod_message_dictlist

//========= b_render_msg_containerNEW  ================= PR2021-08-13
    function b_render_msg_containerNEW(el_msg_container, msg_list, class_list) {
        // used for el_confirm_msg_container
        el_msg_container.className = "p-3";

        if (class_list && class_list.length) {
            // The new spread operator makes it even easier to apply multiple CSS classes as array:
            el_msg_container.classList.add(...class_list);
        }
        let msg_html = "";
        if (msg_list && msg_list.length){
            for (let i = 0, msg_txt ; msg_txt = msg_list[i]; i++) {
                if (msg_txt) {
                    msg_html += "<p>" + msg_txt + "</p>";
                };
            };
        };
        el_msg_container.innerHTML = msg_html;
    };  // b_render_msg_containerNEW

//========= b_render_msg_container  ================= PR2021-05-13
    function b_render_msg_container(id_el_msg, msg_list) {
        //console.log( "===== b_render_msg_container -----")
        //console.log( "id_el_msg", id_el_msg)
        //console.log( "msg_list", msg_list)
          // only used in subjects.js MSJT_validate_and_disable and MSUBJ_validate_and_disable
        const el_msg = document.getElementById(id_el_msg);
        //console.log("el_msg", el_msg)
        if (el_msg){
            const has_msg = (!!msg_list && !!msg_list.length)
        //console.log("has_msg", has_msg)
    // put msg in el_msg
            let msg_html = ""
            if (has_msg){
                for (let j = 0, msg; msg = msg_list[j]; j++) {
                    if(j){msg_html += "<br>"};
                    if(msg){msg_html +=msg};
                };
            };
        //console.log("msg_html", msg_html)
            el_msg.innerHTML = msg_html;
    // show el_msg when has_msg
            add_or_remove_class(el_msg, cls_hide, !has_msg);
        };
    };  // b_render_msg_container

    function b_ManualLoadPage() {  // PR2023-01-31
       //console.log( "===== b_ManualLoadPage ========= ");
       // console.log( "    page", page);
        //console.log( "    paragraph_id", paragraph_id);
    //console.log( "    manual_dict", manual_dict);

        // NIU: const el_btn = document.getElementById("id_btn_" + page)
        //console.log( "el_btn", el_btn);

        const is_en = (setting_dict.user_lang === "en");
    //console.log( "is_en", is_en);

        const page = setting_dict.sel_page;
        const html_dict = (page === "home") ? man_home :
                        (page === "user") ? man_user :
                        (page === "corrector") ? man_corrector :
                        (page === "upload") ? man_upload :
                        (page === "student") ? man_student :
                        (page === "studsubj") ? man_studsubj :
                        (page === "cluster") ? man_cluster :
                        (page === "exemption") ? man_exemption :
                        (page === "wolf") ? man_wolf :
                        (page === "approve") ? man_approve :
                        (page === "mailbox") ? man_mailbox : man_home;
    //console.log( "    html_dict", html_dict);

        const html_list = (html_dict) ? (user_lang === 'en' && html_dict.en) ?  html_dict.en :  html_dict.nl : null;
        //console.log( "html_list", html_list);

        const html_str = (html_list && html_list.length) ? html_list.join('') : (is_en) ? "<h4 class='p-5'> This page is not available yet.</h4>" : "<h4 class='p-5'> Deze pagina is nog niet beschikbaar.</h4>";

        document.getElementById("id_content").innerHTML = html_str;

        FillSideNav(is_en);

        SelectBtnAndDeselctOthers("id_btn_" + page )

        if (paragraph_id){
            //console.log(" ----- GotoParagraph ----- ")
            //console.log("    paragraph_id", paragraph_id)
            // PR2023-01-27 debug: Timeout added, to load page first before going to paragraph element
            setTimeout(function (){
                GotoParagraph(paragraph_id)
            }, 150);

        };
    };

// ###########################################

// +++++++++ MOD USER PERMIT SUBJECTS ++++++++++++++++ PR2022-10-23 PR2022-11-21 PR2022-12-04 PR2023-01-06 PR2023-03-2f
    function b_MUPS_Open(el_input){
        //console.log(" -----  b_MUPS_Open   ---- ")

        let data_dict = {}, user_pk = null, user_role = null;
        let user_schoolbase_pk = null, user_schoolbase_code = null, user_mapid = null;
        let user_allowed_sections = {};
        let modifiedat = null, modby_username = null;

        if(el_input){
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

        //console.log("  data_dict: ", data_dict);



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

        //console.log("  permit_dict.requsr_schoolbase_pk: ", permit_dict.requsr_schoolbase_pk);
        //console.log("  user_schoolbase_pk: ", user_schoolbase_pk);
        //console.log("  may_edit: ", may_edit);

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
        //console.log("    mod_MUPS_dict: ", mod_MUPS_dict);

    // - create ordered list of all schools with schoolbase.role = c.ROLE_008_SCHOOL:
            MUPS_CreateSchoolDepLvlSubjlist();

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

           el_MUPS_username.value = mod_MUPS_dict.last_name;

            add_or_remove_class(el_MUPS_loader, cls_hide, true);
            add_or_remove_class( el_MUPS_tbody_container, cls_hide, false);
            add_or_remove_class(el_MUPS_btn_expand_all.parentNode, cls_hide, false);

    // ---  fill selecttable
            MUPS_FillSelectTable();

    // ---  expand all rows
            MUPS_ExpandCollapse_all();
    // ---  show modal
            $("#id_mod_userallowedsection").modal({backdrop: true});
        };
    };  // MUPS_Open

//========= MUPS_Save  ============= PR2022-11-04
    function MUPS_Save(mode, el_input){
        //console.log(" ----- MUPS_Save ---- mode: ", mode);

    // --- get urls.url_user_allowedsections_upload
        const upload_dict = {
            mode: "update",
            user_pk: mod_MUPS_dict.user_pk,
            allowed_sections: mod_MUPS_dict.allowed_sections
        }
        const url_str = urls.url_user_allowedsections_upload;
        //console.log("  url_str: ", url_str);

        UploadChanges(upload_dict, url_str);

    // ---  show modal
       $("#id_mod_userallowedsection").modal("hide");
    };  // MUPS_Save

//========= MUPS_CreateSchoolDepLvlSubjlist  ============= PR2022-11-04
    function MUPS_CreateSchoolDepLvlSubjlist() {
        //console.log("===== MUPS_CreateSchoolDepLvlSubjlist ===== ");

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

    //console.log("    mod_MUPS_dict.sorted_school_list", mod_MUPS_dict.sorted_school_list);
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
    //console.log("    mod_MUPS_dict.sorted_department_list", mod_MUPS_dict.sorted_department_list);

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
    //console.log("    mod_MUPS_dict.sorted_level_list", mod_MUPS_dict.sorted_level_list);

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
    //console.log("    mod_MUPS_dict.sorted_subject_list", mod_MUPS_dict.sorted_subject_list);

    }; // MUPS_CreateSchoolDepLvlSubjlist

//========= MUPS_FillSelectTable  ============= PR2022-10-24 PR2023-01-06
    function MUPS_FillSelectTable() {
        //console.log("===== MUPS_FillSelectTable ===== ");

        const data_rows = school_rows;

        el_MUPS_tbody_select.innerText = null;

// ---  loop through mod_MUPS_dict.sorted_school_list
        if(mod_MUPS_dict.sorted_school_list.length){
            if (mod_MUPS_dict.may_edit) {

                // Select school only allowed if req_usr and user have both role greater than ROLE_008_SCHOOL PR2023-01-26
                const select_schools_allowed = (permit_dict.requsr_role > 8 && mod_MUPS_dict.user_role > 8) // ROLE_008_SCHOOL}

    // - check if there are unselected schools
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

    // - add row 'Add school' when there are unselected schools
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
                        MUPS_CreateTblrowSchool(addnew_dict);
                    };
                };
            };

    // -  add selected schools to table
            for (let i = 0, sb_pk_str, school_dict; school_dict = mod_MUPS_dict.sorted_school_list[i]; i++) {
                //sb_pk_str = (school_dict.base_id) ? school_dict.base_id.toString() : "0"
                if(mod_MUPS_dict.allowed_sections && school_dict.base_id.toString() in mod_MUPS_dict.allowed_sections){
                    MUPS_CreateTblrowSchool(school_dict);
                };
            };
        };
    }; // MUPS_FillSelectTable

    function MUPS_CreateTblrowSchool(school_dict) {
        //console.log("-----  MUPS_CreateTblrowSchool   ----");
        //console.log("    school_dict", school_dict);
        // PR2022-11-05

// ---  get info from school_dict
        const schoolbase_pk = school_dict.base_id;
        const code = (school_dict.sb_code) ? school_dict.sb_code : "";
        const name = (school_dict.name) ? school_dict.name : "";
        const depbases = (school_dict.depbases) ? school_dict.depbases : null;

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
                td.addEventListener("click", function() {MUPS_SelectSchool(tblRow)}, false);
            } else {
                td.addEventListener("click", function() {MUPS_ExpandTblrows(tblRow)}, false);
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
                td.addEventListener("click", function() {MUPS_DeleteTblrow(tblRow)}, false);

                td.appendChild(el_div);
            };
// ---  add department rows
            const expanded_schoolbase_dict = mod_MUPS_dict.expanded[schoolbase_pk.toString()];

            const show_item = (!!expanded_schoolbase_dict && expanded_schoolbase_dict.expanded);
            if (show_item){
                MUPS_CreateTableDepartment(school_dict);
            };
        };
    };  // MUPS_CreateTblrowSchool

    function MUPS_CreateTableDepartment(school_dict) { // PR2022-11-04
        //console.log("===== MUPS_CreateTableDepartment ===== ");
    //console.log("    school_dict", school_dict);

// ---  get info from school_dict
        const schoolbase_pk = school_dict.base_id;
        const schoolbase_pk_str = schoolbase_pk.toString();

        const sb_depbases = (school_dict.depbases) ? school_dict.depbases : "";
        const sb_depbases_arr = (school_dict.depbases) ? school_dict.depbases.split(";") : [];

// -  get allowed_depbases from this school from mod_MUPS_dict.allowed_sections
        const allowed_depbases = (mod_MUPS_dict.allowed_sections && schoolbase_pk_str in mod_MUPS_dict.allowed_sections) ?  mod_MUPS_dict.allowed_sections[schoolbase_pk_str] : {};

    //console.log("    allowed_depbases", JSON.stringify(allowed_depbases));
    //console.log("    mod_MUPS_dict.may_edit", mod_MUPS_dict.may_edit);

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
    // - add row 'Adddep' when there are unselected departments
            if (has_unselected_departments){
                const addnew_dict = {base_id: -1, name: "< " + loc.Add_department + " >"};
                MUPS_CreateTblrowDep(addnew_dict, schoolbase_pk, sb_depbases, false); // allow_delete = false
            };
        };

// add rows with department if there is only 1
    //console.log("  @@@   sb_depbases_arr", JSON.stringify(sb_depbases_arr));
    //console.log("    mod_MUPS_dict.sorted_department_list", mod_MUPS_dict.sorted_department_list);

        if (sb_depbases_arr.length === 1){
// add rows with the only department of s to school
            for (let i = 0, dep_dict; dep_dict = mod_MUPS_dict.sorted_department_list[i]; i++) {
    //console.log("    dep_dict", dep_dict);
    //console.log("    dep_dict.base_id", dep_dict.base_id);
                if (sb_depbases_arr.includes(dep_dict.base_id.toString())){
    //console.log("    MUPS_CreateTblrowDep");
                    MUPS_CreateTblrowDep(dep_dict, schoolbase_pk, sb_depbases, false); // allow_delete = false
                };
            };

        } else if (mod_MUPS_dict.sorted_department_list.length > 1){
//console.log("    mod_MUPS_dict.sorted_department_list", mod_MUPS_dict.sorted_department_list);

// add rows with selected departments to school
            for (let i = 0, dep_dict; dep_dict = mod_MUPS_dict.sorted_department_list[i]; i++) {
                if (dep_dict.base_id.toString() in allowed_depbases){
                    MUPS_CreateTblrowDep(dep_dict, schoolbase_pk, sb_depbases, true); // allow_delete = true
                };
            };
        };
    };  // MUPS_CreateTableDepartment

    function MUPS_CreateTblrowDep(department_dict, schoolbase_pk, sb_depbases, allow_delete) {
        //console.log("===== MUPS_CreateTblrowDep ===== ");
        //console.log("    department_dict", department_dict);
        //console.log("    schoolbase_pk", schoolbase_pk);
        //console.log("    sb_depbases", sb_depbases);
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

        //console.log("  ?? depbase_pk", depbase_pk);
// ---  add level rows
        if (depbase_pk !== -1){
            let is_expanded = false;
            const expanded_schoolbase_dict = mod_MUPS_dict.expanded[schoolbase_pk.toString()];
             if (expanded_schoolbase_dict) {
                const expanded_depbase_dict = expanded_schoolbase_dict[depbase_pk.toString()];
                if (expanded_depbase_dict) {
                    is_expanded = expanded_depbase_dict.expanded;
            }};

        //console.log("  ?? is_expanded", is_expanded);
            if (is_expanded) {
                if (lvl_req) {
                    MUPS_CreateTableLevel(department_dict, schoolbase_pk);
                } else {
                    // in Havo Vwo there is no level, use lvlbase_pk = -9 to show all subjects PR2022-22-21
                    MUPS_CreateTableSubject(-9, depbase_pk, schoolbase_pk);
                };
            };
        };
    };  // MUPS_CreateTblrowDep

//========= MUPS_CreateTableLevel  =============
    function MUPS_CreateTableLevel(dep_dict, schoolbase_pk) { // PR2022-11-06
        //console.log("===== MUPS_CreateTableLevel ===== ");
        //console.log("    dep_dict", dep_dict);

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
                    MUPS_CreateTblrowLvl(addnew_dict, depbase_pk, schoolbase_pk, false); // allow_delete = false
                };

                for (let i = 0, lvlbase_pk_str, level_dict; level_dict = mod_MUPS_dict.sorted_level_list[i]; i++) {
                    lvlbase_pk_str = level_dict.base_id.toString();
                    if(lvlbase_pk_str in allowed_lvlbases){
                        MUPS_CreateTblrowLvl(level_dict, depbase_pk, schoolbase_pk, true);
                    };
                };
            };
        };
    };  // MUPS_CreateTableLevel

//========= MUPS_CreateTblrowLvl  =============
    function MUPS_CreateTblrowLvl(level_dict, depbase_pk, schoolbase_pk, allow_delete) { // PR2022-11-05
        //console.log("===== MUPS_CreateTblrowLvl ===== ");
        //console.log("  level_dict", level_dict);

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
                MUPS_CreateTableSubject(lvlbase_pk, depbase_pk, schoolbase_pk);
            };
        };
    };  // MUPS_CreateTblrowLvl

//========= MUPS_CreateTableSubject  ============= PR2022-11-05
    function MUPS_CreateTableSubject(lvlbase_pk, depbase_pk, schoolbase_pk) { // PR2022-11-05
        //console.log("===== MUPS_CreateTableSubject ===== ");
        //console.log("    lvlbase_pk", lvlbase_pk, typeof lvlbase_pk);

// -  get levels from this department from mod_MUPS_dict.allowed_sections
        const schoolbase_pk_str = schoolbase_pk.toString();
        const depbase_pk_str = depbase_pk.toString();
        const lvlbase_pk_str = lvlbase_pk.toString();
        const allowed_depbases = (mod_MUPS_dict.allowed_sections && schoolbase_pk_str in mod_MUPS_dict.allowed_sections) ?  mod_MUPS_dict.allowed_sections[schoolbase_pk_str] : {};
        const allowed_lvlbases = (allowed_depbases && depbase_pk_str in allowed_depbases) ?  allowed_depbases[depbase_pk_str] : {};
        const allowed_subjbase_arr = (allowed_lvlbases && lvlbase_pk_str in allowed_lvlbases) ?  allowed_lvlbases[lvlbase_pk_str] : [];

        //console.log("    allowed_lvlbases", allowed_lvlbases);
        //console.log("    allowed_subjbase_arr", allowed_subjbase_arr);

// - add row 'Add_subject' in first row if may_edit
        if (mod_MUPS_dict.may_edit){
            const addnew_dict = {base_id: -1, name_nl: "< " + loc.Add_subject + " >"};
            MUPS_CreateTblrowSubject(addnew_dict, lvlbase_pk, depbase_pk, schoolbase_pk);
        };
// ---  loop through mod_MUPS_dict.sorted_subject_list
        //console.log("    mod_MUPS_dict.sorted_subject_list", mod_MUPS_dict.sorted_subject_list);
        if(mod_MUPS_dict.sorted_subject_list.length ){
            for (let i = 0, subject_dict; subject_dict = mod_MUPS_dict.sorted_subject_list[i]; i++) {
        //console.log("    subject_dict.depbase_id_arr", subject_dict.depbase_id_arr);
        //console.log("    depbase_pk", depbase_pk);
                if (subject_dict.depbase_id_arr.includes(depbase_pk) || depbase_pk === -9 ){

                    // add when lvlbase_pk is in lvlbase_id_arr or when lvlbase_pk = -9 ('all levels')
                    if (subject_dict.lvlbase_id_arr.includes(lvlbase_pk) || lvlbase_pk === -9){
                        if (allowed_subjbase_arr && allowed_subjbase_arr.includes(subject_dict.base_id)){
                            MUPS_CreateTblrowSubject(subject_dict, lvlbase_pk, depbase_pk, schoolbase_pk);
                        };
                    };
                };
            };
        };
    };  // MUPS_CreateTableSubject

//========= MUPS_CreateTblrowSubject  =============
    function MUPS_CreateTblrowSubject(subject_dict, lvlbase_pk, depbase_pk, schoolbase_pk) {
    // PR2022-11-05
        //console.log("===== MUPS_CreateTblrowSubject ===== ");
        //console.log("    subject_dict", subject_dict);

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
    };  // MUPS_CreateTblrowSubject

    function MUPS_SelectSchool(tblRow ) {
        //console.log(" -----  MUPS_SelectSchool   ----");
        const tblName = get_attr_from_el(tblRow, "data-table");
        const pk_int = get_attr_from_el_int(tblRow, "data-schoolbase_pk");

        //console.log("    tblRow", tblRow);
        //console.log("    pk_int", pk_int);
        //console.log("    tblName", tblName);
        //console.log("    mod_MUPS_dict.allowed_sections", mod_MUPS_dict.allowed_sections);

// ---  get unselected_school_list
        const unselected_school_list = MUPS_get_unselected_school_list();
        //console.log("    unselected_school_list", unselected_school_list);

        t_MSSSS_Open(loc, "school", unselected_school_list, false, false, setting_dict, permit_dict, MUPS_SelectSchool_Response);
    };

    function MUPS_SelectDepartment(tblRow ) {
        //console.log(" -----  MUPS_SelectDepartment   ----");
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
        if(mod_MUPS_dict.sorted_department_list.length ){
            for (let i = 0, depbase_pk_str, data_dict; data_dict = mod_MUPS_dict.sorted_department_list[i]; i++) {
                depbase_pk_str = (data_dict.base_id) ? data_dict.base_id.toString() : "0";
                if ( (sb_depbases_arr && sb_depbases_arr.includes(depbase_pk_str)) || (depbase_pk_str === "-9")  ){
                    if(isEmpty(allowed_depbases) || !(depbase_pk_str in allowed_depbases)){
                        unselected_dep_list.push(data_dict);
            }}};
        };
        //console.log("  ????  unselected_dep_list", unselected_dep_list);
        t_MSED_OpenDepLvlFromRows(tblName, unselected_dep_list, schoolbase_pk, null, MUPS_DepFromRows_Response)
    };  // MUPS_SelectDepartment

    function MUPS_SelectLevel(tblRow ) {
        //console.log(" -----  MUPS_SelectLevel   ----");
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
        t_MSED_OpenDepLvlFromRows(tblName, unselected_level_list, schoolbase_pk, depbase_pk, MUPS_LvlFromRows_Response)
    };  // MUPS_SelectLevel

    function MUPS_SelectSubject(tblRow ) {
        //console.log(" -----  MUPS_SelectSubject   ----");
        //console.log("    tblRow", tblRow);

        const schoolbase_pk = get_attr_from_el_int(tblRow, "data-schoolbase_pk");
        const depbase_pk = get_attr_from_el_int(tblRow, "data-depbase_pk");
        const lvlbase_pk = get_attr_from_el_int(tblRow, "data-lvlbase_pk");

        mod_MUPS_dict.sel_schoolbase_pk_str = schoolbase_pk.toString();
        mod_MUPS_dict.sel_depbase_pk_str = depbase_pk.toString();
        mod_MUPS_dict.sel_lvlbase_pk_str = lvlbase_pk.toString();

// ---  get unselected_subject_list
        const unselected_subject_list = MUPS_get_unselected_subject_list(schoolbase_pk, depbase_pk, lvlbase_pk);

        //console.log("    unselected_subject_list", unselected_subject_list);
        t_MSSSS_Open(loc, "subject", unselected_subject_list, false, false, {}, permit_dict, MUPS_SelectSubject_Response);

    };  // MUPS_SelectSubject

    function MUPS_get_unselected_school_list() {
// ---  get unselected_school_list
        const unselected_school_list = [];
        if(mod_MUPS_dict.sorted_school_list.length ){
            for (let i = 0, sb_pk_str, data_dict; data_dict = mod_MUPS_dict.sorted_school_list[i]; i++) {
                sb_pk_str = (data_dict.base_id) ? data_dict.base_id.toString() : "0";
                if(mod_MUPS_dict.allowed_sections && sb_pk_str in mod_MUPS_dict.allowed_sections){
                    //console.log("    sb_pk_str in mod_MUPS_dict.allowed_sections", sb_pk_str);
                } else {
                    unselected_school_list.push(data_dict);
                };
            };
        };
        return unselected_school_list;
    };

    function MUPS_get_unselected_subject_list(schoolbase_pk, depbase_pk, lvlbase_pk) { //PR2022-11-07 PR2023-03-27
        //console.log(" -----  MUPS_get_unselected_subject_list   ----");
        //console.log("    depbase_pk", depbase_pk);
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

            for (let i = 0, subjectbase_pk_str, data_dict; data_dict = mod_MUPS_dict.sorted_subject_list[i]; i++) {
        // check if subject exists in this dep and level
                // add when depbase_pk is in depbase_id_arr or when depbase_pk = -9 ('all levels')
                if (data_dict.depbase_id_arr.includes(depbase_pk) || depbase_pk === -9) {
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

    function MUPS_DeleteTblrow(tblRow ) {
        //console.log(" ###########-----  MUPS_DeleteTblrow   ----");
        //console.log("    tblRow", tblRow);
        const tblName = get_attr_from_el(tblRow, "data-table");
        //console.log("    tblName", tblName);

        const schoolbase_pk_str = get_attr_from_el_int(tblRow, "data-schoolbase_pk").toString();
        const depbase_pk_str = get_attr_from_el_int(tblRow, "data-depbase_pk").toString();
        const lvlbase_pk_str = get_attr_from_el_int(tblRow, "data-lvlbase_pk").toString();

        const allowed_sections = (mod_MUPS_dict.allowed_sections) ? mod_MUPS_dict.allowed_sections : {};
        const allowed_schoolbase = (schoolbase_pk_str in allowed_sections) ? allowed_sections[schoolbase_pk_str] : {};
        const allowed_depbase = (depbase_pk_str in allowed_schoolbase) ? allowed_schoolbase[depbase_pk_str] : {};

        //console.log("    allowed_sections", allowed_sections);
        //console.log("    allowed_schoolbase", allowed_schoolbase);
        //console.log("    allowed_depbase", allowed_depbase);

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

        MUPS_FillSelectTable() ;
    };  // MUPS_DeleteTblrow

    function MUPS_LvlFromRows_Response(sel_lvlbase_pk, schoolbase_pk, depbase_pk) {
        //console.log(" -----  MUPS_LvlFromRows_Response   ----");
        //console.log("    sel_lvlbase_pk", sel_lvlbase_pk);
        //console.log("    schoolbase_pk", schoolbase_pk);
        //console.log("    depbase_pk", depbase_pk);

        if (sel_lvlbase_pk && schoolbase_pk && depbase_pk){
            const schoolbase_pk_str = schoolbase_pk.toString();
            const depbase_pk_str = depbase_pk.toString();
            const lvlbase_pk_str = sel_lvlbase_pk.toString();

            const allowed_sections = (mod_MUPS_dict.allowed_sections) ? mod_MUPS_dict.allowed_sections : {};
            const allowed_schoolbase = (schoolbase_pk_str in allowed_sections) ? allowed_sections[schoolbase_pk_str] : {};
            const allowed_depbase = (depbase_pk_str in allowed_schoolbase) ? allowed_schoolbase[depbase_pk_str] : {};

        //console.log("    lvlbase_pk_str", lvlbase_pk_str);
        //console.log("    allowed_depbase", allowed_depbase);
            if( isEmpty(allowed_depbase) || !(lvlbase_pk_str in allowed_depbase) ){
                allowed_depbase[lvlbase_pk_str] = [];
        //console.log("    allowed_depbase[lvlbase_pk_str]", allowed_depbase[lvlbase_pk_str]);

                // when lvl added and mode = showall: show 'add subject' PR20223-01-26
                if (mod_MUPS_dict.expand_all) {
                    const expanded_schoolbase_dict = mod_MUPS_dict.expanded[schoolbase_pk_str];
                //console.log("    expanded_schoolbase_dict", expanded_schoolbase_dict);
                    if (expanded_schoolbase_dict) {
                        const expanded_depbase_dict = expanded_schoolbase_dict[depbase_pk_str];
                //console.log("    expanded_depbase_dict", expanded_depbase_dict);
                        if (expanded_depbase_dict) {
                            if (!(lvlbase_pk_str in expanded_depbase_dict)){
                                expanded_depbase_dict[lvlbase_pk_str] = {"expanded": true}
                            };
                        };
                    };
                };
            };
        };

        MUPS_FillSelectTable();
    };

    function MUPS_DepFromRows_Response(sel_depbase_pk, schoolbase_pk, depbase_pkNIU) {
        //console.log(" -----  MUPS_DepFromRows_Response   ----");
        //console.log("    sel_depbase_pk", sel_depbase_pk, typeof sel_depbase_pk);
        //console.log("    schoolbase_pk", schoolbase_pk, typeof schoolbase_pk);

        if (sel_depbase_pk && schoolbase_pk){
            // lookup depbase, get lvl_req
             let lvl_req = false;
             for (let i = 0, data_dict; data_dict = mod_MUPS_dict.sorted_department_list[i]; i++) {
                if (data_dict.base_id == sel_depbase_pk) {
                    lvl_req = data_dict.lvl_req;
                    break;
                };
            };
            //console.log("    lvl_req", lvl_req)

            const allowed_sections = mod_MUPS_dict.allowed_sections[schoolbase_pk.toString()];
            //console.log("    allowed_sections", allowed_sections, typeof allowed_sections);
            const schoolbase_pk_str = schoolbase_pk.toString();
            const depbase_pk_str = sel_depbase_pk.toString();
            if( isEmpty(allowed_sections) || !(depbase_pk_str in allowed_sections) ){
                // add 'all levels' (-9) when lvl_req is false (Havo Vwo)
                allowed_sections[depbase_pk_str] = (!lvl_req) ? {"-9": []} : {};

                // when dep added and mode = showall: show 'add level' PR20223-01-26
                if (mod_MUPS_dict.expand_all) {
                    const expanded_schoolbase_dict = mod_MUPS_dict.expanded[schoolbase_pk_str];
                //console.log("    expanded_schoolbase_dict", expanded_schoolbase_dict);
                    if (expanded_schoolbase_dict) {
                        const expanded_depbase_dict = expanded_schoolbase_dict[depbase_pk_str];
                //console.log("    expanded_depbase_dict", expanded_depbase_dict);
                        if (!(depbase_pk_str in expanded_schoolbase_dict)){
                            expanded_schoolbase_dict[depbase_pk_str] = {"expanded": true}
                        };
                    };
                };
            };
            const allowed_depbases = allowed_sections[depbase_pk_str];
            //console.log("    allowed_depbases", allowed_depbases);
        };
        //console.log("@@@ mod_MUPS_dict.allowed_sections", mod_MUPS_dict.allowed_sections);

// ---  fill selecttable
        MUPS_FillSelectTable();
    };

//=========  MUPS_SelectSchool_Response  ================ PR2022-10-26 PR2022-11-21
    function MUPS_SelectSchool_Response(tblName, selected_dict, selected_pk) {
        //console.log( "===== MUPS_SelectSchool_Response ========= ");
        //console.log( "    tblName", tblName);
        //console.log( "    selected_dict", selected_dict);
        //console.log( "    selected_pk", selected_pk, typeof selected_pk);

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
                        //console.log("   @@@@@@@@@@@@  schoolbase_pk_str", schoolbase_pk_str);
                        //console.log("   @@@@@@@@@@@@  mod_MUPS_dict.expanded", mod_MUPS_dict.expanded);
                        //console.log("   @@@@@@@@@@@@  expanded_schoolbase_dict", expanded_schoolbase_dict);
                            if (expanded_schoolbase_dict) {
                                const expanded_depbase_dict = expanded_schoolbase_dict[depbase_pk_str];
                        //console.log("    expanded_depbase_dict", expanded_depbase_dict);
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
            MUPS_FillSelectTable();
        };
    }  // MUPS_SelectSchool_Response

//=========  MUPS_SelectSubject_Response  ================ PR2022-10-26 PR2022-11-21
    function MUPS_SelectSubject_Response(tblName, selected_dict, selected_pk) {
        //console.log( "===== MUPS_SelectSubject_Response ========= ");
        //console.log( "    tblName", tblName);
        //console.log( "    selected_dict", selected_dict);
        //console.log( "    selected_pk", selected_pk, typeof selected_pk);

        // Note: when tblName = school: pk_int = schoolbase_pk
        if (selected_pk === -1) { selected_pk = null};
        if (selected_pk){
            const selected_pk_str = selected_pk.toString();

            const subjbase_pk = selected_dict.base_id;
        //console.log( "    subjbase_pk", subjbase_pk, typeof subjbase_pk);
        //console.log( "    mod_MUPS_dict.sel_schoolbase_pk_str", mod_MUPS_dict.sel_schoolbase_pk_str, typeof mod_MUPS_dict.sel_schoolbase_pk_str);
        //console.log( "    mod_MUPS_dict.sel_depbase_pk_str", mod_MUPS_dict.sel_depbase_pk_str, typeof mod_MUPS_dict.sel_depbase_pk_str);
        //console.log( "    mod_MUPS_dict.sel_lvlbase_pk_str", mod_MUPS_dict.sel_lvlbase_pk_str, typeof mod_MUPS_dict.sel_lvlbase_pk_str);

            if (subjbase_pk){
                const allowed_sections = (mod_MUPS_dict.allowed_sections) ? mod_MUPS_dict.allowed_sections : {};
                const allowed_depbases = (mod_MUPS_dict.sel_schoolbase_pk_str in allowed_sections) ? allowed_sections[mod_MUPS_dict.sel_schoolbase_pk_str] : {};

        //console.log( "    allowed_depbases", allowed_depbases);
                const allowed_lvlbases = (mod_MUPS_dict.sel_depbase_pk_str in allowed_depbases) ? allowed_depbases[mod_MUPS_dict.sel_depbase_pk_str] : {};

        //console.log( "    allowed_lvlbases", allowed_lvlbases);
                // allowed_subjbase_arr contains integers, not strings PR2022-12-04
                const allowed_subjbase_arr = (mod_MUPS_dict.sel_lvlbase_pk_str in allowed_lvlbases) ? allowed_lvlbases[mod_MUPS_dict.sel_lvlbase_pk_str] : [];

        //console.log( "    allowed_subjbase_arr", allowed_subjbase_arr);
                if (allowed_subjbase_arr && !allowed_subjbase_arr.includes(subjbase_pk)){
                    allowed_subjbase_arr.push(subjbase_pk);
                };
            };

    // ---  fill selecttable
            MUPS_FillSelectTable();
        };
    }  // MUPS_SelectSubject_Response

//=========  MUPS_MessageClose  ================ PR2022-10-26
    function MUPS_MessageClose() {
        //console.log(" --- MUPS_MessageClose --- ");

        $("#id_mod_userallowedsection").modal("hide");
    }  // MUPS_MessageClose

    function MUPS_ExpandTblrows(tblRow ) {
        //console.log("-----  MUPS_ExpandTblrows   ----");
        //console.log("    tblRow", tblRow);

        const tblName = get_attr_from_el(tblRow, "data-table");
        //console.log("    tblName", tblName);

        const schoolbase_pk = get_attr_from_el_int(tblRow, "data-schoolbase_pk");
        //console.log("    schoolbase_pk", schoolbase_pk);
        if (schoolbase_pk){
            const schoolbase_pk_str = schoolbase_pk.toString();

            if (!(schoolbase_pk_str in mod_MUPS_dict.expanded)){
                mod_MUPS_dict.expanded[schoolbase_pk_str] = {expanded: false};
            };
            const expanded_school_dict = mod_MUPS_dict.expanded[schoolbase_pk_str];

            if (tblName === "school"){
                expanded_school_dict.expanded = !expanded_school_dict.expanded;

        //console.log("     expanded_school_dict", JSON.stringify ( expanded_school_dict));
        // ABel tasman {"2":{"expanded":false,"-9":{"expanded":false}},"expanded":true}
        // St Jozef    {"1":{"expanded":false},"expanded":true}

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

        //console.log("  **********  mod_MUPS_dict.expanded", mod_MUPS_dict.expanded);
            MUPS_FillSelectTable();
        };
    };  // MUPS_ExpandTblrows

    function MUPS_ExpandCollapse_all(){
     // PR2022-11-06
        //console.log("===== MUPS_ExpandCollapse_all ===== ");
        //console.log("    mod_MUPS_dict.allowed_sections", mod_MUPS_dict.allowed_sections);

        const is_expand = !mod_MUPS_dict.expand_all;
        mod_MUPS_dict.expand_all = is_expand;
        // remove all expanded items when setting 'Collapse_all'
        if (!is_expand){
            mod_MUPS_dict.expanded = {};
        };

        el_MUPS_btn_expand_all.innerText = (is_expand) ? loc.Collapse_all : loc.Expand_all;

// ---  loop through mod_MUPS_dict.allowed_sections and create mod_MUPS_dict.expanded with all items expanded
        for (const [schoolbase_pk_str, allowed_schoolbase] of Object.entries(mod_MUPS_dict.allowed_sections)) {

            if (!(schoolbase_pk_str in mod_MUPS_dict.expanded)){
                mod_MUPS_dict.expanded[schoolbase_pk_str] = {};
            }
            const expanded_schoolbase = mod_MUPS_dict.expanded[schoolbase_pk_str];
            expanded_schoolbase.expanded = is_expand;

            for (const [depbase_pk_str, allowed_depbase] of Object.entries(allowed_schoolbase)) {
                if (!(depbase_pk_str in expanded_schoolbase)){
                    expanded_schoolbase[depbase_pk_str] = {};
                }
                const expanded_depbase = expanded_schoolbase[depbase_pk_str];
                expanded_depbase.expanded = is_expand;

                for (const [lvlbase_pk_str, allowed_lvlbases] of Object.entries(allowed_depbase)) {
                    if (!(lvlbase_pk_str in expanded_depbase)){
                        expanded_depbase[lvlbase_pk_str] = {};
                    }
                    const expanded_lvlbase = expanded_depbase[lvlbase_pk_str];
                    expanded_lvlbase.expanded = is_expand;
                };
            };
        };
    //console.log("     mod_MUPS_dict.expanded", mod_MUPS_dict.expanded);

        MUPS_FillSelectTable();
    };  // MUPS_ExpandCollapse_all

/////////////////////


// ###########################################










//?????????????????????????????????????????????????????????????????

// PR2021-03-16 from https://stackoverflow.com/questions/2320069/jquery-ajax-file-upload
    const b_UploadFile = function (upload_json, file, url_str) {
        this.upload_json = upload_json;
        this.file = file;
        this.url_str = url_str;
    };

    b_UploadFile.prototype.getType = function() {
        return (this.file) ? this.file.type : null;
    };
    b_UploadFile.prototype.getSize = function() {
        return (this.file) ? this.file.size : 0;
    };
    b_UploadFile.prototype.getName = function() {
        return (this.file) ? this.file.name : null;
    };
    b_UploadFile.prototype.doUpload = function (RefreshDataRows) {
        var that = this;
        var formData = new FormData();
        // from https://blog.filestack.com/thoughts-and-knowledge/ajax-file-upload-formdata-examples/
        // add to input html:  <input id="id_ModNote_filedialog" type="file" multiple="multiple"
        // Loop through each of the selected files.
        //for(var i = 0; i < files.length; i++){
        //  var file = files[i];
        // formData.append('myfiles[]', file, file.name);

        // add assoc key values, this will be posts values
        //console.log( "attachment type",  this.getType())
        //console.log( "attachment name", this.getName())

        formData.append("upload_file", true);
        formData.append("filename", this.getName());
        formData.append("contenttype", this.getType());

        if (this.file){
            formData.append("file", this.file, this.getName());
        }
        // from https://stackoverflow.com/questions/16761987/jquery-post-formdata-and-csrf-token-together
        const csrftoken = Cookies.get('csrftoken');
        formData.append('csrfmiddlewaretoken', csrftoken);
        formData.append('upload', this.upload_json);

        //const parameters = {"upload": JSON.stringify (upload_dict)}
        const parameters = formData;
        $.ajax({
            type: "POST",
            url: this.url_str,
                //xhr: function () {
                //     var myXhr = $.ajaxSettings.xhr();
                //      if (myXhr.upload) {
                //         myXhr.upload.addEventListener('progress', that.progressHandling, false);
                //      }
                //     return myXhr;
                //   },
            data: parameters,
            dataType:'json',
            success: function (response) {
                // ---  hide loader
                const el_loader = document.getElementById("id_loader");
                if(el_loader){el_loader.classList.add("visibility_hide")}

                RefreshDataRows(response);

                if ("grade_note_icon_rows" in response) {
                    const tblName = "grades";
                    const field_names = (field_settings[tblName]) ? field_settings[tblName].field_names : null;
                    RefreshDataMap(tblName, field_names, response.grade_note_icon_rows, grade_map, false);  // false = don't show green ok background
                }

            },  // success: function (response) {

            error: function (xhr, msg) {
                // ---  hide loader
                const el_loader = document.getElementById("id_loader");
                if(el_loader){el_loader.classList.add("visibility_hide")}
                console.log(msg + '\n' + xhr.responseText);
            },
            async: true,
            data: formData,
            cache: false,
            contentType: false,
            processData: false,
            timeout: 60000
        });
    };

    b_UploadFile.prototype.progressHandling = function (event) {
    //console.log("progressHandling", event)
        let percent = 0;
        const position = event.loaded || event.position;
        const total = event.total;
        const progress_bar_id = "#progress-wrp";
        if (event.lengthComputable) {
            percent = Math.ceil(position / total * 100);
        }
    //console.log("percent", percent)
        // update progressbars classes so it fits your code
        $(progress_bar_id + " .progress-bar").css("width", +percent + "%");
        $(progress_bar_id + " .status").text(percent + "%");
    };

    function b_setCaretPosition(ctrl,pos) {
        // PR2023-01-29 from https://stackoverflow.com/questions/512528/set-keyboard-caret-position-in-html-textbox
        // used in mod_student add symbol
        if (ctrl.setSelectionRange){
            ctrl.focus();
            ctrl.setSelectionRange(pos,pos);
        } else if (ctrl.createTextRange) {
            const range = ctrl.createTextRange();
            range.collapse(true);
            range.moveEnd('character', pos);
            range.moveStart('character', pos);
            range.select();
        };
    };

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
        points = "0,0 "; // lower left corner
        if (indent_right) {
            points += (width - indent_right) + ",0 "; // lower right corner
            points += (width) + "," + (height/2) + " ";  // middle right point
            points += (width - indent_right) + "," + (height) + " "; // top right corner
        } else {
            points += (width) + ",0 " // lower right corner
            points += (width) + "," + (height) + " "; // top right corner
        };
        points += "0," + (height) + " "; // top left corner
        if (indent_left) {
            points += (indent_left) + "," + (height/2);  // middle left point
        }
        return points;
    };  // get_svg_arrow_points

