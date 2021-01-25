// PR2020-09-29
// with pure vanilla Javascript. Was jQuery: $(function() {
document.addEventListener('DOMContentLoaded', function() {
    "use strict";

    console.log( "==== signup_setpassword210125 ========= ");

    const cls_hide = "display_hide";
    const cls_visible_hide = "visibility_hide";
    const el_btn_submit = document.getElementById("id_btn_submit");
    if (!!el_btn_submit){ el_btn_submit.addEventListener("click", function() {ShowLoader()}, false );}

    const el_btn_cancel = document.getElementById("id_btn_cancel");
    if (!!el_btn_cancel){ el_btn_cancel.addEventListener("click", function() {HandleCancelClicked()}, false )};

    const el_btn_close = document.getElementById("id_btn_close");
    if (!!el_btn_close){ el_btn_close.addEventListener("click", function() {HandleCancelClicked()}, false )};

    const el_loader = document.getElementById("id_loader");
    if(el_loader){el_loader.classList.add(cls_visible_hide)};

//###########################################################################
// +++++++++++++++++ UPLOAD +++++++++++++++++++++++++++++++++++++++++++++++++

//=========  HandleCancelClicked  ================ PR2020-03-31
    function HandleCancelClicked() {
        //console.log( "==== HandleCancelClicked ========= ");
        // hide card till home page is loaded PR2021-01-25
        document.getElementById("id_card").classList.add(cls_hide)

    };  // HandleCancelClicked

//=========  ShowLoader  ================ PR2020-04-07
    function ShowLoader() {
        //console.log( "==== ShowLoader ========= ");
        if(el_loader){el_loader.classList.remove(cls_visible_hide)}
    };  // SubmitPassword

});