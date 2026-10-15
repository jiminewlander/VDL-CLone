var validPatterns = {};
var invalidMsg = {};
var validated = {};
var shownFieldNames = {};

// Setup the validation
validPatterns['name'] = /^[a-zA-Z\' .-]{1,80}$/;
invalidMsg['name'] = 'Can contain only letters, hyphen, space, period or apostrophe, of maximum length 80';
shownFieldNames['name'] = 'Name';

validPatterns['address1'] = /^[a-zA-Z0-9 \'. -]{1,240}$/;
invalidMsg['address1'] = 'Can contain only letters, numbers, hyphen, space, apostrophe or period, of maximum length 240';
shownFieldNames['address1'] = 'Address Line 1';

validPatterns['address2'] = /^[a-zA-Z0-9 \'. -]{0,240}$/;
invalidMsg['address2'] = 'Can contain only letters, numbers, hyphen, space, apostrophe or period, of maximum length 240';
shownFieldNames['address2'] = 'Address Line 2';

validPatterns['city'] = /^[a-zA-Z .-]{1,80}$/;
invalidMsg['city'] = 'Can contain only letters, period, space or a hyphen, of maximum length 80';
shownFieldNames['city'] = 'City';

validPatterns['state'] = /^[a-zA-Z .]{1,50}$/;
invalidMsg['state'] = 'Can contain only letters, period or space, of maximum length 50';
shownFieldNames['state'] = 'State';

validPatterns['zip'] = /^[0-9]{5,5}([- ]?[0-9]{4,4})?$/;
invalidMsg['zip'] = 'Must be a zip code format:  nnnnn or nnnnn-nnnn';
shownFieldNames['zip'] = 'Zip Code';

//validPatterns['email'] = /^(?=[_a-zA-Z0-9@.-]{6,254}[_a-zA-Z0-9-]+(\.[_a-zA-Z0-9-]+)*@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*(\.[a-zA-Z]{2,})$/;
validPatterns['email'] = /(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))/;
invalidMsg['email'] = 'Must match an email format, of maximum length 254';
shownFieldNames['email'] = 'Email';

validPatterns['telephone1'] = /^[0-9]{3,3}$/;
invalidMsg['telephone1'] = 'Phone Area Code must match exactly three numbers:  nnn';
shownFieldNames['telephone1'] = 'Phone Area Code';

validPatterns['telephone2'] = /^[0-9]{3,3}$/;
invalidMsg['telephone2'] = 'Phone Prefix must match exactly three numbers:  nnn';
shownFieldNames['telephone2'] = 'Phone Prefix';

validPatterns['telephone3'] = /^[0-9]{4,4}$/;
invalidMsg['telephone3'] = 'Phone Suffix must match exactly four numbers:  nnnn';
shownFieldNames['telephone3'] = 'Phone Suffix';

validPatterns['fax1'] = /^([0-9]{3,3})*$/;
invalidMsg['fax1'] = 'Fax Area Code must match exactly three numbers:  nnn';
shownFieldNames['fax1'] = 'Fax Area Code';

validPatterns['fax2'] = /^([0-9]{3,3})*$/;
invalidMsg['fax2'] = 'Fax Prefix must match exactly three numbers:  nnn';
shownFieldNames['fax2'] = 'Fax Prefix';

validPatterns['fax3'] = /^([0-9]{4,4})*$/;
invalidMsg['fax3'] = 'Fax Suffix must match exactly four numbers:  nnnn';
shownFieldNames['fax3'] = 'Fax Suffix';

function validateForm() {
    //Query your elements
    var inputs = document.getElementsByTagName('input');
    var retVal = true;

    // Loop your elements
    for (i = 0, len = inputs.length; i < len; i++) {

        // Skip the submit input
        if ( inputs[i].hasAttribute('type') && ( inputs[i].type == 'submit' || inputs[i].type == 'reset' ) ) continue;

        var name = inputs[i].id;
        if ( !validated[name] ) {
            // Call validate
            if ( !validateField(name) ) {
                // Prevent submit
                retVal = false;
            }
        }
    }
    return retVal;
}

function validateField(field) {
    // Get the  value of the input field being submitted
    var value = document.getElementById(field).value;

    // Set the error field tag in the html
    var errorField = field + 'Error';

    if (value == '' && field != "address2" && field != "fax1" && field != "fax2" && field != "fax3") {
        document.getElementById(errorField).innerHTML = shownFieldNames[field] + " cannot be blank";
        document.getElementById(errorField).style.display = 'block';
        return false;
    } else {
        var re = validPatterns[field];
        if ( re.test(value) ) {
            /* if ( field == "email" ) {
                // For email, also validate is neither hotmail nor yahoo
                if ( value.search(/yahoo/i) || value.search(/hotmail/i) ) {
                    document.getElementById(errorField).innerHTML = 'Cannot be hotmail nor yahoo email';
                    document.getElementById(errorField).style.display = 'block';
                    return false;
                }
            }  */
            document.getElementById(errorField).innerHTML = '';
            document.getElementById(errorField).style.display = 'none';
            return true;
        } else {
            document.getElementById(errorField).innerHTML = invalidMsg[field];
            document.getElementById(errorField).style.display = 'block';
            return false;
        }
    }
}
