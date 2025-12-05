/* static/privacy.js */

document.addEventListener("DOMContentLoaded", function() {
    // 1. Define parts
    const user = "appcontactpwvault"; 
    const domain = "gmail.com"; 
    
    // 2. Find the element
    const link = document.getElementById('contact-link');
    
    // 3. Update the element
    if (link) {
        const email = user + '@' + domain;
        link.innerText = email;
        link.href = "mailto:" + email;
    } else {
        console.error("Could not find element with id 'contact-link'");
    }
});