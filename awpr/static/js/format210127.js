
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



/*
          <div  class="d-flex flex-wrap" id="id_dflex">

                <svg id="id_svg00" height="32" width="90">
                    <a href="/?menu=mn_schl&amp;sub=home" >
                        <polygon id="'id_plg' +" points="0,0 80,0 90,16.0 80,32 0,32 " style="fill:#2d4e77;stroke:#2d4e77;stroke-width:1"></polygon>
                        <text id="'id_txt' +"
                            x="45"
                            y="20"
                            fill="#EDF2F8"
                            text-anchor="middle"
                            alignment-baseline="middle">
                                School
                        </text>
                    </a>
                </svg>

                <svg id="id_svg01" height="32" width="100">
                    <a href="/?menu=mn_subj&amp;sub=home" >
                        <polygon id="'id_plg' +" points="0,0 90,0 100,16.0 90,32 0,32 10,16.0" style="fill:#bacee6;stroke:#bacee6;stroke-width:1"></polygon>
                        <text id="'id_txt' +"
                            x="50"
                            y="20"
                            fill="#212529"
                            text-anchor="middle"
                            alignment-baseline="middle">
                                Vakken
                        </text>
                    </a>
                </svg>

                <svg id="id_svg02" height="32" width="140">
                    <a href="/?menu=mn_pack&amp;sub=home" >
                        <polygon id="'id_plg' +" points="0,0 130,0 140,16.0 130,32 0,32 10,16.0" style="fill:#bacee6;stroke:#bacee6;stroke-width:1"></polygon>
                        <text id="'id_txt' +"
                            x="70"
                            y="20"
                            fill="#212529"
                            text-anchor="middle"
                            alignment-baseline="middle">
                                Study program
                        </text>
                    </a>
                </svg>

                <svg id="id_svg03" height="32" width="120">
                    <a href="/?menu=mn_stud&amp;sub=home" >
                        <polygon id="'id_plg' +" points="0,0 110,0 120,16.0 110,32 0,32 10,16.0" style="fill:#bacee6;stroke:#bacee6;stroke-width:1"></polygon>
                        <text id="'id_txt' +"
                            x="60"
                            y="20"
                            fill="#212529"
                            text-anchor="middle"
                            alignment-baseline="middle">
                                Kandidaten
                        </text>
                    </a>
                </svg>

                <svg id="id_svg04" height="32" width="140">
                    <a href="/?menu=mn_se&amp;sub=home" >
                        <polygon id="'id_plg' +" points="0,0 130,0 140,16.0 130,32 0,32 10,16.0" style="fill:#bacee6;stroke:#bacee6;stroke-width:1"></polygon>
                        <text id="'id_txt' +"
                            x="70"
                            y="20"
                            fill="#212529"
                            text-anchor="middle"
                            alignment-baseline="middle">
                                Schoolexamen
                        </text>
                    </a>
                </svg>

                <svg id="id_svg05" height="32" width="140">
                    <a href="/?menu=mn_ce&amp;sub=home" >
                        <polygon id="'id_plg' +" points="0,0 130,0 140,16.0 130,32 0,32 10,16.0" style="fill:#bacee6;stroke:#bacee6;stroke-width:1"></polygon>
                        <text id="'id_txt' +"
                            x="70"
                            y="20"
                            fill="#212529"
                            text-anchor="middle"
                            alignment-baseline="middle">
                                Centraal examen
                        </text>
                    </a>
                </svg>

                <svg id="id_svg06" height="32" width="120">
                    <a href="/?menu=mn_reex&amp;sub=home" >
                        <polygon id="'id_plg' +" points="0,0 110,0 120,16.0 110,32 0,32 10,16.0" style="fill:#bacee6;stroke:#bacee6;stroke-width:1"></polygon>
                        <text id="'id_txt' +"
                            x="60"
                            y="20"
                            fill="#212529"
                            text-anchor="middle"
                            alignment-baseline="middle">
                                Re-exam
                        </text>
                    </a>
                </svg>

                <svg id="id_svg07" height="32" width="120">
                    <a href="/?menu=mns_res&amp;sub=home" >
                        <polygon id="'id_plg' +" points="0,0 110,0 120,16.0 110,32 0,32 10,16.0" style="fill:#bacee6;stroke:#bacee6;stroke-width:1"></polygon>
                        <text id="'id_txt' +"
                            x="60"
                            y="20"
                            fill="#212529"
                            text-anchor="middle"
                            alignment-baseline="middle">
                                Results
                        </text>
                    </a>
                </svg>

                <svg id="id_svg08" height="32" width="120">
                    <a href="/?menu=mn_rep&amp;sub=home" >
                        <polygon id="'id_plg' +" points="0,0 120,0 120,32 0,32 10,16.0" style="fill:#bacee6;stroke:#bacee6;stroke-width:1"></polygon>
                        <text id="'id_txt' +"
                            x="60"
                            y="20"
                            fill="#212529"
                            text-anchor="middle"
                            alignment-baseline="middle">
                                Reports
                        </text>
                    </a>
                </svg>



*/