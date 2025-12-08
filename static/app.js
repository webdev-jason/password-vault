/* static/app.js */

let warningTimer; // Starts at 4 minutes (240s)
let logoutTimer;  // Failsafe at 5 minutes (300s)
let countdownInterval; // Updates the visual number

window.onload = async function() {
    // Setup Activity Listeners
    document.onmousemove = resetTimer;
    document.onkeypress = resetTimer;
    document.onclick = resetTimer;
    document.onscroll = resetTimer;
    document.ontouchstart = resetTimer; 
    
    // NEW: Expanded Validation Regex for "Banned Characters"
    const bannedChars = /[\s\\^~"'\[\]{};|]/;

    // Listener for Settings Password
    const newPassInput = document.getElementById('set-new-pass');
    if (newPassInput) {
        newPassInput.addEventListener('input', function(e) {
            const bubble = document.getElementById('pass-bubble');
            if (bannedChars.test(this.value)) {
                bubble.classList.add('visible');
            } else {
                bubble.classList.remove('visible');
            }
        });
    }

    // Listener for Registration Password
    const regPassInput = document.getElementById('reg-pass');
    if (regPassInput) {
        regPassInput.addEventListener('input', function(e) {
            const bubble = document.getElementById('reg-bubble');
            if (bannedChars.test(this.value)) {
                bubble.classList.add('visible');
            } else {
                bubble.classList.remove('visible');
            }
        });
    }

    // NEW: Listener for Registration Username
    const regUserInput = document.getElementById('reg-user');
    if (regUserInput) {
        regUserInput.addEventListener('input', function(e) {
            const bubble = document.getElementById('user-bubble');
            if (bannedChars.test(this.value)) {
                bubble.classList.add('visible');
            } else {
                bubble.classList.remove('visible');
            }
        });
    }

    const savedKey = sessionStorage.getItem('masterKey');
    if (savedKey) {
        try {
            const response = await fetch('/api/check_session');
            const data = await response.json();
            
            if (response.ok) {
                if(data.username) sessionStorage.setItem('currentUser', data.username);
                showVault(savedKey);
                resetTimer(); 
            } else {
                sessionStorage.removeItem('masterKey');
                sessionStorage.removeItem('currentUser');
            }
        } catch(e) { console.log("Server unreachable"); }
    }
};

/* --- TIMEOUT LOGIC --- */
function resetTimer() {
    const vaultSection = document.getElementById('vault-section');
    const modal = document.getElementById('timeout-modal');
    
    // If vault isn't open, or the modal is ALREADY visible, don't reset.
    if (vaultSection.classList.contains('hidden')) return;
    if (!modal.classList.contains('hidden')) return; 

    // Clear all existing timers
    clearTimeout(warningTimer);
    clearTimeout(logoutTimer);
    clearInterval(countdownInterval);
    
    // Timer 1: Show Warning after 4 minutes (240,000ms)
    warningTimer = setTimeout(() => {
        showTimeoutWarning();
    }, 240000); 

    // Timer 2: Actually Logout after 5 minutes (300,000ms)
    logoutTimer = setTimeout(() => {
        logout();
    }, 300000); 
}

function showTimeoutWarning() {
    const modal = document.getElementById('timeout-modal');
    const display = document.getElementById('countdown-timer');
    
    modal.classList.remove('hidden');
    
    let secondsLeft = 60; // 60 Second Countdown
    display.innerText = secondsLeft;

    // Start visual countdown
    countdownInterval = setInterval(() => {
        secondsLeft--;
        display.innerText = secondsLeft;
        
        if (secondsLeft <= 0) {
            clearInterval(countdownInterval);
            logout();
        }
    }, 1000);
}

function stayLoggedIn() {
    document.getElementById('timeout-modal').classList.add('hidden');
    clearInterval(countdownInterval); // Stop the countdown
    resetTimer(); // Restart the inactivity clock
}

/* --- UTILITIES --- */
function togglePassword(inputId, btn) {
    const input = document.getElementById(inputId);
    const iconEye = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
    const iconSlash = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`;

    if (input.type === "password") {
        input.type = "text";
        btn.innerHTML = iconSlash;
    } else {
        input.type = "password";
        btn.innerHTML = iconEye;
    }
}

function generateRandomPassword() {
    const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()";
    let password = "";
    for (let i = 0; i < 16; i++) {
        const randomValues = new Uint32Array(1);
        window.crypto.getRandomValues(randomValues);
        password += chars[randomValues[0] % chars.length];
    }
    document.getElementById('new-pass').value = password;
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => alert("Copied!"));
}

// NEW: Copy 2FA Secret
function copySecret() {
    const code = document.getElementById('secret-code-display').innerText;
    navigator.clipboard.writeText(code).then(() => alert("Secret Copied!"));
}

async function logout() {
    clearTimeout(warningTimer);
    clearTimeout(logoutTimer);
    clearInterval(countdownInterval);
    
    await fetch('/api/logout', { method: 'POST' });
    sessionStorage.removeItem('masterKey');
    sessionStorage.removeItem('currentUser');
    location.reload();
}

function showVault(masterKey) {
    document.getElementById('login-section').classList.add('hidden');
    document.getElementById('vault-section').classList.remove('hidden');
    
    const username = sessionStorage.getItem('currentUser') || 'My';
    const formattedUser = username.charAt(0).toUpperCase() + username.slice(1) + "'s";
    document.getElementById('header-username').innerText = formattedUser;
    
    loadPasswords(masterKey);
    resetTimer(); 
}

/* --- REGISTRATION LOGIC --- */
function toggleRegister() {
    const loginCard = document.getElementById('login-section');
    const regCard = document.getElementById('register-section');

    if (regCard.classList.contains('hidden')) {
        loginCard.classList.add('hidden');
        regCard.classList.remove('hidden');
    } else {
        loginCard.classList.remove('hidden');
        regCard.classList.add('hidden');
    }
}

async function registerUser() {
    const user = document.getElementById('reg-user').value.trim(); // Trim spaces
    const pass = document.getElementById('reg-pass').value.trim();
    const passConfirm = document.getElementById('reg-pass-confirm').value.trim();
    const btn = document.querySelector('#register-section .btn-primary');
    
    if(!user || !pass) return alert("Username and Password required");
    
    if(pass !== passConfirm) return alert("Passwords do not match");

    const originalText = btn.innerText;
    btn.innerText = "Creating Account...";
    btn.disabled = true;

    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ username: user, password: pass })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Success: Move to 2FA Setup
            document.getElementById('register-section').classList.add('hidden');
            document.getElementById('setup-2fa-section').classList.remove('hidden');
            
            // Set QR Code and Secret
            document.getElementById('qr-image').src = "data:image/png;base64," + result.qr_code;
            document.getElementById('secret-code-display').innerText = result.secret;
            
            // NEW: Set the Deep Link for Mobile App
            document.getElementById('otp-link').href = result.totp_uri;
            
        } else {
            document.getElementById('reg-error').innerText = result.error;
            btn.innerText = originalText;
            btn.disabled = false;
        }
    } catch(e) {
        document.getElementById('reg-error').innerText = "Server Error";
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

function finishRegistration() {
    // 1. Grab username BEFORE clearing fields
    const newUser = document.getElementById('reg-user').value.trim();

    document.getElementById('setup-2fa-section').classList.add('hidden');
    document.getElementById('login-section').classList.remove('hidden');
    
    // 2. Auto-fill the login field
    if (newUser) {
        document.getElementById('login-user').value = newUser;
        document.getElementById('login-pass').focus(); // Move cursor to password
    }

    // 3. Clear registration inputs
    document.getElementById('reg-user').value = "";
    document.getElementById('reg-pass').value = "";
    document.getElementById('reg-pass-confirm').value = "";
}

/* --- SETTINGS LOGIC --- */
function toggleSettings() {
    const card = document.getElementById('settings-card');
    const addCard = document.getElementById('add-card');
    
    if (card.classList.contains('hidden')) {
        card.classList.remove('hidden');
        addCard.classList.add('hidden'); 
        
        const username = sessionStorage.getItem('currentUser');
        if (username) {
            document.getElementById('set-new-user').placeholder = username;
        }
    } else {
        card.classList.add('hidden');
        addCard.classList.remove('hidden');
    }
}

async function updateAccount() {
    const newUser = document.getElementById('set-new-user').value;
    const newPass = document.getElementById('set-new-pass').value;
    const currentKey = sessionStorage.getItem('masterKey');

    if (!newUser && !newPass) return alert("Please enter a new username or password.");
    
    const bannedChars = /[\s\\^~"'\[\]{};|]/;
    if (newPass) {
        if (bannedChars.test(newPass)) return alert("Password contains invalid characters.");
        if (newPass.length < 8) return alert("Password must be at least 8 characters.");
    }
    
    if (!confirm("Changing your Password will re-encrypt your entire vault. This cannot be undone. Continue?")) return;

    const btn = document.querySelector('#settings-card .btn-primary');
    const originalText = btn.innerText;
    btn.innerText = "Processing Encryption...";
    btn.disabled = true;

    try {
        const response = await fetch('/api/update_account', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                current_password: currentKey,
                new_username: newUser,
                new_password: newPass
            })
        });

        const result = await response.json();

        if (response.ok) {
            alert("Account Updated! Please log in with your new credentials.");
            logout(); 
        } else {
            alert("Error: " + result.error);
            btn.innerText = originalText;
            btn.disabled = false;
        }
    } catch (e) {
        alert("Server Error");
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

async function deleteAccount() {
    if (!confirm("⚠️ DANGER: This will permanently delete your account and ALL saved passwords. This cannot be undone.\n\nAre you absolutely sure?")) return;
    
    const password = prompt("Please enter your Password to confirm deletion:");
    if (!password) return;

    // NEW: Auto-trim whitespace from mobile keyboard
    const cleanPassword = password.trim();

    try {
        const response = await fetch('/api/delete_account', {
            method: 'DELETE',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ password: cleanPassword })
        });

        if (response.ok) {
            alert("Account Deleted.");
            logout();
        } else {
            const result = await response.json();
            alert("Deletion Failed: " + (result.error || "Unknown error"));
        }
    } catch (e) {
        alert("Server connection error.");
    }
}

/* --- API CALLS --- */
async function attemptLogin() {
    const user = document.getElementById('login-user').value.trim(); // Trim for login too
    const pass = document.getElementById('login-pass').value.trim();
    const code = document.getElementById('login-code').value;
    const btn = document.querySelector('#login-section .btn');
    btn.innerText = "Verifying...";
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ username: user, password: pass, "2fa_code": code })
        });

        const result = await response.json();
        if (response.ok) {
            sessionStorage.setItem('masterKey', pass);
            if(result.username) sessionStorage.setItem('currentUser', result.username);
            showVault(pass);
        } else {
            document.getElementById('error-msg').innerText = result.error || "Login Failed";
        }
    } catch (e) {
        document.getElementById('error-msg').innerText = "Server Error";
    } finally { btn.innerText = "Unlock Vault"; }
}

async function loadPasswords(masterKey) {
    const response = await fetch('/api/get_passwords', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ master_password: masterKey })
    });
    
    if (response.status === 401) return logout();

    const passwords = await response.json();
    const listDiv = document.getElementById('password-list');
    listDiv.innerHTML = ""; 

    passwords.forEach(p => {
        const item = document.createElement('div');
        item.className = 'vault-item';
        item.id = `row-${p.id}`;
        
        item.innerHTML = `
            <div id="display-${p.id}" style="display:flex; justify-content:space-between; width:100%; align-items:center;">
                <div class="vault-info">
                    <span class="vault-site">${p.site}</span>
                    <span class="vault-user">${p.username}</span>
                </div>
                <div class="vault-actions">
                    <button class="btn-icon" onclick="copyToClipboard('${p.password}')" title="Copy">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                    </button>
                    <button class="btn-icon" onclick="toggleEdit(${p.id})" title="Edit" style="color: var(--primary);">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                    </button>
                    <button class="btn-icon" onclick="deletePassword(${p.id})" title="Delete" style="color: var(--danger);">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                </div>
            </div>

            <div id="edit-${p.id}" class="edit-mode-inputs hidden">
                <input type="text" id="edit-site-${p.id}" value="${p.site}">
                <input type="text" id="edit-user-${p.id}" value="${p.username}">
                <div class="password-wrapper">
                    <input type="password" id="edit-pass-${p.id}" value="${p.password}">
                    <button class="btn-eye" onclick="togglePassword('edit-pass-${p.id}', this)" type="button">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                    </button>
                </div>
                <div style="display:flex; gap:10px; margin-top:5px;">
                    <button class="btn btn-primary" onclick="saveEdit(${p.id})" style="padding: 5px;">Save</button>
                    <button class="btn btn-danger" onclick="toggleEdit(${p.id})" style="padding: 5px; color: var(--text-main);">Cancel</button>
                </div>
            </div>
        `;
        listDiv.appendChild(item);
    });
}

function toggleEdit(id) {
    const displayRow = document.getElementById(`display-${id}`);
    const editRow = document.getElementById(`edit-${id}`);
    
    if (displayRow.classList.contains('hidden')) {
        displayRow.classList.remove('hidden');
        editRow.classList.add('hidden');
    } else {
        displayRow.classList.add('hidden');
        editRow.classList.remove('hidden');
    }
}

async function saveEdit(id) {
    const site = document.getElementById(`edit-site-${id}`).value;
    const user = document.getElementById(`edit-user-${id}`).value;
    const pass = document.getElementById(`edit-pass-${id}`).value;
    const masterKey = sessionStorage.getItem('masterKey');

    const response = await fetch('/api/update_password', {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            id: id,
            master_password: masterKey,
            site_name: site,
            site_username: user,
            site_password: pass
        })
    });

    if (response.ok) {
        loadPasswords(masterKey); 
    } else {
        alert("Failed to update");
    }
}

async function addPassword() {
    const site = document.getElementById('new-site').value;
    const user = document.getElementById('new-user').value;
    const pass = document.getElementById('new-pass').value;
    const masterKey = sessionStorage.getItem('masterKey');

    if(!site || !pass) return alert("Site and Password are required");

    const response = await fetch('/api/add_password', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            master_password: masterKey,
            site_name: site,
            site_username: user,
            site_password: pass
        })
    });

    if (response.ok) {
        document.getElementById('new-site').value = "";
        document.getElementById('new-user').value = "";
        document.getElementById('new-pass').value = "";
        loadPasswords(masterKey);
    }
}

async function deletePassword(id) {
    if(!confirm("Are you sure?")) return;
    const masterKey = sessionStorage.getItem('masterKey');
    const response = await fetch('/api/delete_password', {
        method: 'DELETE',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ id: id })
    });
    if(response.ok) loadPasswords(masterKey);
}