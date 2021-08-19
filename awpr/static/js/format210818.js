
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

