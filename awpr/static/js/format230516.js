
    // PR2023-04-16 create constants for readability
    const icon_blue = "0_4", icon_red = "1_4", icon_orange = "2_4", icon_blank = "3_4";
    const icon_auth_0 = "0_0", icon_auth_1 = "0_1", icon_auth_2 = "0_2", icon_auth_12 = "0_3";
    const icon_auth_3 = "1_0", icon_auth_13 = "1_1", icon_auth_23 = "1_2", icon_auth_123 = "1_3";
    const icon_auth_4 = "2_0", icon_auth_14 = "2_1", icon_auth_24= "2_2", icon_auth_124 = "2_3";
    const icon_auth_34 = "3_0", icon_auth_134 = "3_1", icon_auth_234 = "3_2", icon_auth_1234 = "3_3";

//========= format_date with vanilla js  ======== PR2020-07-31
    function format_dateISO_vanilla (loc, date_iso, hide_weekday, hide_year, is_months_long, is_weekdays_long) {
        let date_formatted = null;
        if (date_iso){
            const date_JS = get_dateJS_from_dateISO(date_iso);
            date_formatted = format_dateJS_vanilla(loc, date_JS, hide_weekday, hide_year, is_months_long, is_weekdays_long)
        }
        return date_formatted;
    }


//========= get_dateJS_from_dateISO  ======== PR2019-10-28
    function get_dateJS_from_dateISO (date_iso) {
        //console.log( "===== get_dateJS_from_dateISO  ========= ");
        //console.log( "date_iso: ", date_iso, typeof date_iso);
        let date_JS = null;
        if (date_iso){
            // PR2020-06-22 debug: got error because date_iso was Number
            const date_iso_str = date_iso.toString()
            const arr = date_iso_str.split("-");
            if (arr.length > 2) {
                // Month 4 april has index 3
                date_JS = new Date(parseInt(arr[0]), parseInt(arr[1]) - 1, parseInt(arr[2]))
            }
        }
        return date_JS
    }  //  get_dateJS_from_dateISO


//========= format_date with vanilla js  ======== PR2023-04-19
    function get_dateISO_from_dateJS (date_JS) {
        console.log(" ----- get_dateISO_from_dateJS", date_JS);
        let dateISO = null
        if(date_JS) {
            const year_str = date_JS.getFullYear().toString();
            const month_index = date_JS.getMonth();
        console.log("    month_index", month_index);
        console.log("    month_index", month_index);
            const month_str =  ("0" + (month_index + 1).toString()).slice(-2);
        console.log("    month_str", month_str);
            const date_str = ("0" + date_JS.getDate().toString()).slice(-2);
        console.log("    date_str", date_str);

            dateISO = [year_str, month_str, date_str ].join("-")
        };
        return dateISO
    };  // function format_dateJS_vanilla


//========= format_date with vanilla js  ======== PR2019-10-12 PR2020-07-31
    function format_dateJS_vanilla (loc, date_JS, hide_weekday, hide_year, is_months_long, is_weekdays_long) {
        //console.log(" ----- format_dateJS_vanilla", date_JS);
        let display_value = "";
        if(date_JS) {
            const is_en = (loc.user_lang === "en");
            const comma_space = (is_en) ? ", " : " ";

            const month_list = (is_months_long) ? loc.months_long : loc.months_abbrev;
            const month_index =  date_JS.getMonth();
            const month_str = (!!month_list) ? month_list[month_index + 1] : "";
            const date_str = date_JS.getDate().toString();

            if(is_en){
                display_value = month_str + " " + date_str;
            } else {
                display_value = date_str + " " + month_str;
            }

            if (!hide_year) {
                const year_str = date_JS.getFullYear().toString();
                display_value += comma_space + year_str;
            };

            if (!hide_weekday) {
                // index 0 is index 7 in weekday_list
                const weekday_list = (is_weekdays_long) ? loc.weekdays_long : loc.weekdays_abbrev;
                const weekday_index = (date_JS.getDay()) ? date_JS.getDay() : 7;
                const weekday_str = (weekday_list) ? weekday_list[weekday_index] : "";
                display_value = weekday_str + comma_space  + display_value;
            };
        }  // if(!!date_JS)
        return display_value
    }  // function format_dateJS_vanilla

//=========  format_datetime_from_datetimeJS ================ PR2021-08-18
    function format_datetime_from_datetimeISO(loc, datetimeISO, hide_weekday, hide_year, hide_time, hide_suffix) {
        const datetimeJS = parse_dateJS_from_dateISO(datetimeISO);
        return format_datetime_from_datetimeJS(loc, datetimeJS, hide_weekday, hide_year, hide_time, hide_suffix);
    };

//=========  format_date_from_dateISO ================ PR2022-03-09
    function format_date_from_dateISO(loc, date_iso) {
        //console.log( "===== format_date_from_dateISO  ========= ");
        // PR2022-03-09 debug: date_JS gives birthdate one day before birthdate, because of timezone
        // data_dict.birthdate 2004-05-30 becomes date_JS = Sat May 29 2004 20:00:00 GMT-0400 (Venezuela Time)
        // use format_date_from_dateISO instead

        "use strict";
        let date_formatted = "";
        if(date_iso){
            const arr = date_iso.split("-");

            const year_str = (arr[0]) ? arr[0].toString() : "";
            const month_int = (Number(arr[1])) ? Number(arr[1]) : null;
            const month_str = (month_int && loc.months_abbrev[month_int]) ? loc.months_abbrev[month_int] : "";
            // convert date to number to remove leading 0: '06' becomes '6'
            const date_int = (Number(arr[2])) ? Number(arr[2]) : null;
            const date_str = (date_int) ? date_int.toString() : "";
            if (loc.user_lang === "en") {
                date_formatted = [month_str, " ", date_str, ", ", year_str].join("");
            } else {
                date_formatted = [date_str, month_str, year_str].join(" ");
            };
        }
        return date_formatted
    }  // format_date_from_dateISO

//=========  format_datetime_from_datetimeJS ================ PR2020-07-22  PR2020-10-04
    function format_datetime_from_datetimeJS(loc, datetimeJS, hide_weekday, hide_year, hide_time, hide_suffix) {
        //console.log( "===== format_datetime_from_datetimeJS  ========= ");
        //  when display24 = true: zo 00.00 u is displayed as 'za 24.00 u'
        //  format: wo 16.30 u or Sat, 12:00 pm
        "use strict";
        // this is only for duration format:
        // let hide_value = (offset == null) || (blank_when_zero && offset === 0);
        let date_formatted = "" , time_formatted = "";
        if(datetimeJS){
            const isEN = (loc.user_lang === "en");
            const isAmPm = (loc.timeformat === "AmPm");
            const year_int = datetimeJS.getFullYear();
            const year_str = (!hide_year) ? " " + year_int.toString() : "";
            const date = datetimeJS.getDate();

            const weekday_index = (datetimeJS.getDay()) ? datetimeJS.getDay() : 7 // JS sunday = 0, iso sunday = 7
            const weekday_str = (!hide_weekday) ? loc.weekdays_abbrev[weekday_index] + ( (isEN) ? ", " : " " ) : ""

            const month_str = " " + loc.months_abbrev[ (1 + datetimeJS.getMonth()) ];

            // midnight, begin of day = 00:00 am
            // noon = 12:00 am
            // midnight, end of day = 12:00 pmm
            let is_pm = false;
            let hours = datetimeJS.getHours();
            if(isAmPm && hours > 12) {
                hours -= 12
                is_pm = true;
            }
            const hour_str = " " + ("0" + hours).slice(-2);
            const minute_str = ("0" + datetimeJS.getMinutes()).slice(-2);
            const ampm_str = (isAmPm) ?  ( (is_pm) ? " pm" : " am" ) : "";
            const suffix = (!hide_suffix) ? " u" : "";
            if(hide_time){
                if (isEN) {
                    time_formatted = weekday_str + month_str + " " + date + ", " + year_str;
                } else {
                    time_formatted = weekday_str + date + " " + month_str + " " + year_str;
                }
            } else {
                if (isEN) {
                    time_formatted = weekday_str + month_str + " " + date + ", " + year_str + ", " + hour_str + ":" + minute_str;
                    if(ampm_str) { time_formatted += ampm_str};
                } else {
                    time_formatted = weekday_str + date + " " + month_str + " " + year_str + ", " + hour_str + "." + minute_str + suffix;
                }
            }
        }
        return time_formatted
    }  // format_datetime_from_datetimeJS

//========= f_format_last_modified ======== PR2021-08-21 PR223-03-30
    function f_format_last_modified_txt(prefix_txt, modifiedat, modified_by) {
        let display_txt = null;
        if (modifiedat || modified_by ) {
            if (prefix_txt) { display_txt = prefix_txt };
            if (modifiedat){
                if (prefix_txt) { display_txt += loc._on_ };
                const modified_dateJS = parse_dateJS_from_dateISO(modifiedat);
                display_txt += format_datetime_from_datetimeJS(loc, modified_dateJS);
            };
            if (modified_by){
                if (prefix_txt) { display_txt += loc._by_ };
                display_txt += modified_by;
            };
        };
        return display_txt;
    }  // f_format_last_modified


//========= f_format_count ======== PR2021-08-18
    // based on TSA f_format_pricerate
    function f_format_count (user_lang, value_int, show_zero) {
        //console.log(" --- f_format_count  -----")
       // console.log("value_int", value_int)
        let display_text = "";
        if (!value_int) {
            if(!!show_zero) {display_text = "0"};
        } else {
            const thousand_separator = (user_lang === "en") ? "," : ".";
            display_text = value_int.toString()
// --- add thousand_separator when value >= 1,000
            if (value_int >= 1000) {
                const pos = display_text.length - 3 ;
                display_text = [display_text.slice(0, pos), display_text.slice(pos)].join(thousand_separator);
            }
        }
        return display_text
    }  // f_format_count


//========= f_format_percentage ======== PR2022-04-27
    function f_format_percentage (user_lang, rate_int, number_of_decimals) {
        //console.log(" --- f_format_percentage  -----")
        if (!number_of_decimals){number_of_decimals = 0};

        let display_text = "";

        if (rate_int) {
            // rate_int is rate: 0.56125
            const value_percentage = 100 * rate_int;
        // from https://www.delftstack.com/howto/javascript/javascript-round-to-2-decimal-places/
            let value_str = value_percentage.toFixed(number_of_decimals)

            display_text = (user_lang !== "en") ? value_str.replace(".", ",") : value_str;
    //console.log("value_str", value_str)
    //console.log("display_text", display_text)

            display_text += "%"
        }  // if (!!value_int)

        return display_text
    }  // f_format_percentage



//=========  f_format_status_grade  ================ PR2021-12-19 PR2022-08-28 PR2023-03-24
    function f_format_status_grade(field_name, fld_value, data_dict) {
    //NOT IN USE YET, must replace UpdateFieldStatus in grades.js
        //console.log("=========  f_format_status_grade =========");
        //console.log("    field_name", field_name);
        //console.log("    fld_value", fld_value);
        //console.log("    data_dict", data_dict);

        const field_arr = field_name.split("_");
        const prefix_str = field_arr[0];
        // field_name = "se_status", "sr_status", "pe_status", "ce_status", "note_status"
        let className = "diamond_" + icon_blank;  // diamond_3_4 is blank img
        let title_text = null, filter_value = null;
        if (prefix_str === "note"){
            // dont show note icon when user has no permit_read_note
            className = "note_" + ( (permit_dict.permit_read_note && fld_value && fld_value !== "0") ?
            (fld_value.length === 3) ? fld_value : "0_1" : "0_0" )

        } else {
            // only show status when weight > 0

            // TODO enable this next year. It is turned off because empty scores were submitted
            //const grade_has_value = get_grade_has_value(field_name, data_dict, true);
            //if (grade_has_value){

            const show_status = (["se_status", "sr_status"].includes(field_name) && data_dict.weight_se) ||
                                (["pe_status", "ce_status"].includes(field_name) && data_dict.weight_ce);
            if (true){
                const field_auth1by_id = prefix_str + "_auth1by_id";
                const field_auth2by_id = prefix_str + "_auth2by_id";
                const field_auth3by_id = prefix_str + "_auth3by_id";
                const field_auth4by_id = prefix_str + "_auth4by_id";
                const field_published_id = prefix_str + "_published_id";
                const field_blocked = prefix_str + "_blocked";
                const field_status = prefix_str + "_status";

                const auth1by_id = (data_dict[field_auth1by_id]) ? data_dict[field_auth1by_id] : null;
                const auth2by_id = (data_dict[field_auth2by_id]) ? data_dict[field_auth2by_id] : null;
                const auth3by_id = (data_dict[field_auth3by_id]) ? data_dict[field_auth3by_id] : null;
                const auth4by_id = (data_dict[field_auth4by_id]) ? data_dict[field_auth4by_id] : null;
                const published_id = (data_dict[field_published_id]) ? data_dict[field_published_id] : null;
                const is_blocked = (data_dict[field_blocked]) ? data_dict[field_blocked] : null;

                // - auth3 does not have to sign when secret exam (aangewezen examen)
                // - auth3 also does not have to sign when exemption (vrijstelling) PR2023-02-02

                // PR2023-02-07 debug: this is not correct value: !data_dict.examperiod === 4, must be: data_dict.examperiod !== 4
                const auth3_must_sign = (!data_dict.secret_exam && data_dict.examperiod !== 4);

                // - auth4 does not have to sign when secret exam (aangewezen examen) or when se-grade
                // - auth4 does not have to sign when se-grade
                // - auth4 also does not have to sign when exemption (vrijstelling) PR2023-02-02

                // PR2023-02-07 debug: this is not correct value: !data_dict.examperiod === 4, must be: data_dict.examperiod !== 4
                const auth4_must_sign = (!data_dict.secret_exam && data_dict.examperiod !== 4
                                            && ["pe_status", "ce_status"].includes(field_name));

                className = f_get_status_auth_iconclass(published_id, is_blocked, auth1by_id, auth2by_id, auth3_must_sign, auth3by_id, auth4_must_sign, auth4by_id);
                filter_value = className;

                let formatted_publ_modat = "";
                if (published_id){
                    const field_publ_modat = prefix_str + "_publ_modat" // subj_publ_modat
                    const publ_modat = (data_dict[field_publ_modat]) ? data_dict[field_publ_modat] : null;
                    const modified_dateJS = parse_dateJS_from_dateISO(publ_modat);
                    formatted_publ_modat = format_datetime_from_datetimeJS(loc, modified_dateJS);
                };
                if (is_blocked) {
                    if (published_id){
                        title_text = loc.blocked_11 + "\n" + loc.blocked_12 + formatted_publ_modat + "\n" + loc.blocked_13;
                    } else {
                        title_text = loc.blocked_01 + "\n" + loc.blocked_02 + "\n" + loc.blocked_03;
                    };

                } else if(auth1by_id || auth2by_id || auth3by_id || auth4by_id){
                    title_text = (data_dict.secret_exam) ? loc.Designated_exam + "\n" : "";
                    title_text += loc.Approved_by + ": ";
                    for (let i = 1; i < 5; i++) {
                        const auth_id = (i === 1) ? auth1by_id :
                                        (i === 2) ? auth2by_id :
                                        (i === 3) ? auth3by_id :
                                        (i === 4) ?  auth4by_id : null;
                        const prefix_auth = prefix_str + "_auth" + i;
                        if(auth_id){
                            const function_str = (i === 1) ?  loc.Chairperson :
                                                (i === 2) ? loc.Secretary :
                                                (i === 3) ?  loc.Examiner :
                                                (i === 4) ? loc.Corrector : "";
                            const field_usr = prefix_auth + "by_usr";
                            const auth_usr = (data_dict[field_usr]) ?  data_dict[field_usr] : "-";

                            title_text += "\n" + function_str.toLowerCase() + ": " + auth_usr;
                        };
                    };
                };
            };
        };
        return [className, title_text, filter_value]
    };  // f_format_status_grade


//=========  f_format_status_subject  ================ PR2021-12-19 PR2022-08-28 PR2023-03-24
    function f_format_status_subject(prefix_str, data_dict) {
        //console.log("=========  f_format_status_subject =========");
        //console.log("    prefix_str", prefix_str);
        //console.log("    data_dict", data_dict);
        // for now: only used in page correctors UpdateField

        // field_name = "uc_auth1by_id", "uc_auth2by_id", "uc_published_id"
        // prefix_str = "uc"
        let className = "diamond_" + icon_blank;  // diamond_3_4 is blank img
        let title_text = null, filter_value = null;

        const field_auth1by_id = prefix_str + "_auth1by_id";
        const field_auth2by_id = prefix_str + "_auth2by_id";
        const field_published_id = prefix_str + "_published_id";

        const auth1by_id = (data_dict[field_auth1by_id]) ? data_dict[field_auth1by_id] : null;
        const auth2by_id = (data_dict[field_auth2by_id]) ? data_dict[field_auth2by_id] : null;
        const published_id = (data_dict[field_published_id]) ? data_dict[field_published_id] : null;

        className = f_get_status_auth_iconclass(published_id, false, auth1by_id, auth2by_id, false, null, false, null);
        filter_value = className;

        let formatted_publ_modat = "";
        if (published_id){
            const field_publ_modat = prefix_str + "_publ_modat" // subj_publ_modat
            const publ_modat = (data_dict[field_publ_modat]) ? data_dict[field_publ_modat] : null;
            const modified_dateJS = parse_dateJS_from_dateISO(publ_modat);
            formatted_publ_modat = format_datetime_from_datetimeJS(loc, modified_dateJS);
        };
        if(auth1by_id || auth2by_id){
            title_text = loc.Approved_by + ": ";
            for (let i = 1; i < 3; i++) {
                const auth_id = (i === 1) ? auth1by_id :
                                (i === 2) ? auth2by_id : null;
                const prefix_auth = prefix_str + "_auth" + i;
                if(auth_id){
                    const function_str = (i === 1) ?  loc.Chairperson :
                                        (i === 2) ? loc.Secretary : "";
                    const field_usr = prefix_auth + "by_usr";
                    const auth_usr = (data_dict[field_usr]) ?  data_dict[field_usr] : "-";
        //console.log("    field_usr", field_usr);
        //console.log("    field_usr", field_usr);

                    title_text += "\n" + function_str.toLowerCase() + ": " + auth_usr;
                };
            };
        };

        //console.log("    className", className);
        //console.log("    title_text", title_text);
        //console.log("    filter_value", filter_value);

        return [className, title_text, filter_value]
    };  // f_format_status_subject

    function f_get_status_auth_iconclass(publ, blocked, auth1, auth2, auth3_must_sign, auth3, auth4_must_sign, auth4) {
        //console.log( " ==== f_get_status_auth_iconclass ====");
        //console.log("   publ", publ, "blocked", blocked)
        //console.log("   auth1", auth1, "auth2", auth2)
        //console.log("   auth3_must_sign", auth3_must_sign, "auth4_must_sign", auth4_must_sign)
        //console.log("   auth3", auth3, "auth4", auth4)

        // PR2022-08-28 PR2023-01-24
        // when auth4_must_sign : use function f_get_status_auth1234_iconclass
        // when auth3_must_sign : use function f_get_status_auth123_iconclass
        // orhetrwise: use function f_get_status_auth12_iconclass

        const icon_class =  (auth4_must_sign) ? f_get_status_auth1234_iconclass(publ, blocked, auth1, auth2, auth3_must_sign, auth3, auth4_must_sign, auth4) :
                            (auth3_must_sign) ? f_get_status_auth123_iconclass(publ, blocked, auth1, auth2, auth3) :
                                                f_get_status_auth12_iconclass(publ, blocked, auth1, auth2);
        //console.log("    icon_class", icon_class);

        return icon_class;
    };  // f_get_status_auth_iconclass

    function f_get_status_auth1234_iconclass(publ, blocked, auth1, auth2, auth3_must_sign, auth3, auth4_must_sign, auth4) {
    // PR2021-05-07 PR2021-12-18 PR2022-04-17 PR2022-06-13
        //console.log( " ==== f_get_status_auth1234_iconclass ====");
        //console.log("publ", publ, "blocked", blocked, "auth1", auth1, "auth2", auth2)
        //console.log("auth3_must_sign", auth3_must_sign, "auth3", auth3)
        //console.log("auth4_must_sign", auth4_must_sign, "auth4", auth4)

        // PR 2022-06-13 shen secret exam (aangewezen examen) auth3 and auth4 dont have to approve
        // - solved as follows:
        // - when auth3_must_sign = false, auth4_must_sign is also false
        // - when auth3_must_sign = false: make auth3 = auth2 and auth 4 = auth1
        // - this way the left half of the diamond turns black when auth1 approves, the right part when auth2 approves
        // when only  auth4_must_sign = false:
        // - make the diamond full black when auth1, auth2 and auth 3 have approved

        const prefix = (blocked) ? "blocked_" : "diamond_";
        let img_class = prefix + icon_auth_0; // empty diamond

        if (auth3_must_sign) {
            if (auth4_must_sign) {
                // all must sign, pass
            } else {
                if (auth1 && auth2 && auth3){
                    auth4 = true;
                };
            };
        } else {
            // if auth3 must not sign, also auth4 must not sign
            if (auth1 && auth2){
                auth3 = true;
                auth4 = true;
            };
        };
    //console.log( "img_class", img_class);
        if(publ){
            if (blocked){
                img_class = prefix + icon_orange;  // orange diamond: published after blocked by Inspectorate
            } else {
                img_class = prefix + icon_blue;  // blue diamond: published
            };
        } else {
            if (auth1){
                if (auth2){
                    if (auth3){
                        img_class = (auth4) ? prefix + icon_auth_1234 : prefix + icon_auth_123; // auth 1+2+3+4 // auth 1+2+3
                    } else {
                        img_class = (auth4) ? prefix + icon_auth_124 : prefix + icon_auth_12; // auth 1+2+4 // auth 1+2
                    };
                } else {
                    if (auth3){
                        img_class = (auth4) ? prefix + icon_auth_134 : prefix + icon_auth_13; // auth 1+3+4 // auth 1+3
                    } else {
                        img_class = (auth4) ? prefix + icon_auth_14 : prefix + icon_auth_1; // auth 1+4  // auth 1
                    }
                }
            } else {
                if (auth2){
                    if (auth3){
                        img_class = (auth4) ? prefix + icon_auth_234 : prefix + icon_auth_23; // auth 2+3+4 // auth 2+3
                    } else {
                        img_class = (auth4) ? prefix + icon_auth_24 : prefix + icon_auth_2; // auth 2+4 // auth 2
                    }
                } else {
                    if (auth3){
                        img_class = (auth4) ? prefix + icon_auth_34 :  prefix + icon_auth_3; // auth 3+4 // auth 3
                    } else {
                        img_class = (auth4) ? prefix + icon_auth_4 : prefix + icon_auth_0;  // auth 4 // auth -
                    };
                };
            };
        };
    //console.log( "img_class", img_class);
        return img_class;
    };

    function f_get_status_auth123_iconclass(publ, blocked, auth1, auth2, auth3) {
    // PR2022-08-28
        //console.log( " ==== f_get_status_auth123_iconclass ====");
        //console.log("publ", publ, "blocked", blocked, "auth1", auth1, "auth2", auth2, "auth3", auth3);

        // auth1, auth2, auth3 must approve school grades and wolf exam

        const prefix = (blocked) ? "blocked_" : "diamond_";
        let img_class = prefix + icon_auth_0; // empty diamond

    //console.log( "img_class", img_class);
        if(publ){
            if (blocked){
                img_class = prefix + icon_orange;  // orange diamond: published after blocked by Inspectorate
            } else {
                img_class = prefix + icon_blue;  // blue diamond: published
            };
        } else {
            if (auth1){
                if (auth2){
                    img_class = (auth3) ? prefix + icon_auth_1234 : prefix + icon_auth_12; //  auth 1+2+3+4 / auth 1+2
                } else {
                    img_class = (auth3) ? prefix + icon_auth_13 : prefix + icon_auth_1; //  auth 1+3 / auth 1
                };
            } else {
                if (auth2){
                    img_class = (auth3) ? prefix + icon_auth_23 : prefix + icon_auth_2; //  auth 2+3 / auth 2
                } else {
                    img_class = (auth3) ? prefix + icon_auth_3 : prefix + icon_auth_0; //  auth 3 /  auth -
                };
            };
        };
    //console.log( "img_class", img_class);
        return img_class;
    };  // f_get_status_auth123_iconclass

    function f_get_status_auth12_iconclass(publ, blocked, auth1, auth2) {
    // PR2022-04-17
        const prefix = (blocked) ? "blocked_" : "diamond_";
        let img_class = prefix + icon_auth_0; // empty diamond
        if(publ){
            if (blocked){
                img_class = prefix + icon_orange;  // orange diamond: published after blocked by Inspectorate
            } else {
                img_class = prefix + icon_blue;  // blue diamond: published
            };
        } else {
            if (blocked){
                img_class = prefix + icon_red;  // red diamond: blocked by Inspectorate, published is removed to enable correction
            } else {
                if (auth1){
                    img_class = (auth2) ? prefix + icon_auth_1234 : prefix + icon_auth_14; // auth 1+2+3+4 / auth 1+4

                } else {
                    img_class = (auth2) ? prefix + icon_auth_23 : prefix + icon_auth_0; //  auth 2+3 / auth -

        }}};
        return img_class;
    };



