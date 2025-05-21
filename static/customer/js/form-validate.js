function valid_datas(f) {
  if (f.name.value == "") {
    jQuery("#form_status").html(
      '<span class="wrong">Your name must not be empty!</span>'
    );
    notice(f.name);
  } else if (f.email.value == "") {
    jQuery("#form_status").html(
      '<span class="wrong">Your email must not be empty and correct format!</span>'
    );
    notice(f.email);
  } else if (f.phone.value == "") {
    jQuery("#form_status").html(
      '<span class="wrong">Your phone must not be empty and correct format!</span>'
    );
    notice(f.phone);
  } else if (f.subject.value == "") {
    jQuery("#form_status").html(
      '<span class="wrong">Your subject must not be empty!</span>'
    );
    notice(f.subject);
  } else if (f.message.value == "") {
    jQuery("#form_status").html(
      '<span class="wrong">Your message must not be empty!</span>'
    );
    notice(f.message);
  } else {
    return true;
  }

  return false;
}

function notice(f) {
  jQuery("#cookies-contact-form").find("input,textarea").css("border", "none");
  f.style.border = "1px solid red";
  f.focus();
}

function valid_login(f) {
  if (f.email.value == "") {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">Email must not be empty!</span>'
    );
    notice(f.email);
  } else if (f.password.value == "") {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">Password must not be empty!</span>'
    );
    notice(f.password);
  } else {
    // We can submit normally (no AJAX for login right now)
    return true;
  }

  return false;
}

function valid_signup(f) {
  if (f.name.value == "") {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">Name must not be empty!</span>'
    );
    notice(f.name);
  } else if (f.email.value == "") {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">Email must not be empty and must be valid!</span>'
    );
    notice(f.email);
  } else if (f.password1.value == "") {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">Password must not be empty!</span>'
    );
    notice(f.password1);
  } else if (f.password2.value == "") {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">Confirm Password must not be empty!</span>'
    );
    notice(f.password2);
  } else if (f.password1.value != f.password2.value) {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">Passwords do not match!</span>'
    );
    notice(f.password2);
  } else {
    // We can submit normally (no AJAX for signup yet)
    return true;
  }

  return false;
}

function valid_forgot_password(f) {
  if (f.email.value == "") {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">Please enter your registered email address!</span>'
    );
    notice(f.email);
    return false;
  } else {
    return true;
  }
}

function valid_reset_password(f) {
  if (f.otp.value == "") {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">Please enter otp!</span>'
    );
    notice(f.otp);
  } else if (f.new_password1.value == "") {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">New password must not be empty!</span>'
    );
    notice(f.new_password1);
  } else if (f.new_password2.value == "") {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">Please confirm your new password!</span>'
    );
    notice(f.new_password2);
  } else if (f.new_password1.value != f.new_password2.value) {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">Passwords do not match!</span>'
    );
    notice(f.new_password2);
  } else {
    return true; // Form is valid
  }

  return false; // Prevent form submission
}

function valid_edit_form(f) {
  if (f.name.value.trim() === "") {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">Full name must not be empty!</span>'
    );
    notice(f.name);
  } else if (f.phone.value.trim() === "") {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">Phone number must not be empty!</span>'
    );
    notice(f.phone);
  } else if (f.address.value.trim() === "") {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">Address must not be empty!</span>'
    );
    notice(f.address);
  } else {
    return true; // valid, allow form to submit
  }

  return false; // prevent form submission if any check fails
}

function valid_change_password(f) {
  if (f.old_password.value.trim() === "") {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">Current password must not be empty!</span>'
    );
    notice(f.old_password);
  } else if (f.new_password1.value.trim() === "") {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">New password must not be empty!</span>'
    );
    notice(f.new_password1);
  } else if (f.new_password2.value.trim() === "") {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">Confirm new password must not be empty!</span>'
    );
    notice(f.new_password2);
  } else if (f.new_password1.value !== f.new_password2.value) {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">Passwords do not match!</span>'
    );
    notice(f.new_password2);
  } else {
    return true; // valid, allow form to submit
  }

  return false; // prevent form submission if any check fails
}

function valid_otp(f) {
  if (f.otp.value.trim() === "") {
    jQuery("#login_signup_form_status").html(
      '<span class="wrong">OTP must not be empty!</span>'
    );
    notice(f.otp);
    return false;
  } else {
    return true;
  }
}
