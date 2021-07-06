// PR2020-10-21 added
    "use strict";
    let setting = {margin_left: 15,
                    margin_top: 15,
                    page_height: 180,
                    column00_width: 20,
                    column_width: 35,
                    thead_height: 10,
                    weekheader_height: 7,
                    header_width: 260,
                    line_height: 5,
                    font_height: 4,
                    dist_underline: 1, // distance between bottom text and undeline
                    max_char: 20, // maximum characters on one line in weekday
                    fontsize_weekheader: 12,
                    fontsize_line: 10,
                    fontsize_footer: 8,
                    padding_left: 2};

// XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

//========= function test printPDF  ====  PR2020-10-21
    function printPDFlogfile(log_list, file_name, printtoscreen) {
        //console.log("printPDFlogfile")
        let doc = new jsPDF();

        //doc.addFont('courier', 'courier', 'normal');
        doc.setFont('courier');

        doc.setFontSize(9);

        let startHeight = 25;
        let noOnFirstPage = 60;
        let noOfRows = 60;
        let z = 1;

        const pos_x = 15
        const line_height = 4
        if (!!log_list && log_list.length > 0){
            const len = log_list.length;
            for (let i = 0, item; i < len; i++) {
                item = log_list[i];
                if (!!item) {
                    if(i <= noOnFirstPage){
                        startHeight = startHeight + line_height;
                        addData(item, pos_x, startHeight, doc);
                    } else {
                        if(z === 1 ){
                            startHeight = 25;
                            doc.addPage();
                        }
                        if(z <= noOfRows){
                            startHeight = startHeight + line_height;
                            addData(item, pos_x, startHeight, doc);
                            z += 1;
                        } else {
                            z = 1;
                        }
                    }
                }  //  if (!item.classList.contains("display_none")) {
            }
            // doc.output('datauri) not wortking, blocked by browser PR2020-01-02
            // if (printtoscreen){
            //     doc.output('datauri');
            // } else {
                doc.save(file_name);
                    console.log("doc.save(file_name: ", file_name)
            // }  // if (printtoscreen){
        }  // if (len > 0){
    }  // function printPDFlogfile

    function addData(item, pos_x, height, doc){
        if(!!item){
            doc.text(pos_x, height, item);
        }  // if(!!tblRow){
    }  // function addData
