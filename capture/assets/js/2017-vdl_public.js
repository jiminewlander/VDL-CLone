// JavaScript Document
$(function(){
	if ( $("#frm_ident_user").length > 0) {
		// functions for initial reset password form
		// fields: user_name, user_email
		var user_name = $("#PasswordForm_user_name");
		var user_email = $("#PasswordForm_user_email");
		$(user_name).blur(function() {
			disable_input(this, "#PasswordForm_user_email");
		});
		$(user_name).keyup(function() {
			disable_input(this, "#PasswordForm_user_email");
		});
		$(user_email).blur(function() {
			disable_input(this, "#PasswordForm_user_name");
		});
		$(user_email).keyup(function() {
			disable_input(this, "#PasswordForm_user_name");
		});
	}
	function disable_input(current, alternate) {
		if ($(current).val().length > 0) {
			$(alternate).attr("disabled","disabled").addClass("disabled");
		} else {
			$(alternate).removeAttr("disabled").removeClass("disabled");
		}
	}
	if ($(".kill").length > 0) {
		$(".kill").click(function() {
			$(this).parent().parent().hide('blind');
		});
	}

	function checkCookie(){
		var cookieEnabled=(navigator.cookieEnabled)? true : false   
		if (typeof navigator.cookieEnabled=="undefined" && !cookieEnabled){ 
			document.cookie="testcookie";
			cookieEnabled=(document.cookie.indexOf("testcookie")!=-1)? true : false;
		}
		return (cookieEnabled)?true:showCookieFail();
	}

	function showCookieFail(){
		$( '.cookieWarn' ).removeClass( 'hide' );
		console.log('no cookies');
	}

	// within a window load,dom ready or something like that place your:
	checkCookie();

        $('#frm_requestAccount').on('beforeSubmit', function(e) {
            var pswd = document.getElementById('ldapuser-password').value;
            document.getElementById('ldapuser-password').value = encodeURIComponent(pswd);
            var pswd_ck = document.getElementById('ldapuser-password_check').value;
            document.getElementById('ldapuser-password_check').value = encodeURIComponent(pswd_ck);
            return true;
        });

        $('#frm_resetPass').on('beforeSubmit', function(e) {
            var pswd = document.getElementById('passwordform-password').value;
            document.getElementById('passwordform-password').value = encodeURIComponent(pswd);
            var pswd_ck = document.getElementById('passwordform-password_check').value;
            document.getElementById('passwordform-password_check').value = encodeURIComponent(pswd_ck);
            return true;
        });

});

