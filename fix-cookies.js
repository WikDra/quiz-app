// Cross-Site Cookie Fix for Quiz App
// Run this in your browser console when you're on the front-end application page

(function() {
  console.log("🍪 Quiz App Cookie Fix running...");
  
  // Configuration
  const API_BASE_URL = 'http://localhost:5000';
  const APP_URL = 'http://localhost:5173';
  
  // Force SameSite=None and Secure=true on cookies
  function patchCookieApi() {
    console.log("Patching document.cookie API...");
    
    // Save the original setters and getters
    const originalCookieGetter = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie').get;
    const originalCookieSetter = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie').set;
    
    // Replace the setter
    Object.defineProperty(document, 'cookie', {
      get: function() {
        return originalCookieGetter.call(document);
      },
      set: function(val) {
        console.log("Setting cookie:", val);
        
        // Fix SameSite attribute if needed
        if (val.indexOf('SameSite=') === -1 && val.indexOf('samesite=') === -1) {
          val += '; SameSite=None';
        }
        
        // Call the original setter
        return originalCookieSetter.call(document, val);
      },
      configurable: true
    });
    
    console.log("Cookie API patched");
  }
  
  // Create a specialized login function
  function setupSpecializedLogin() {
    console.log("Setting up specialized login...");
    
    // Create and add a special login button
    const loginButton = document.createElement('button');
    loginButton.textContent = 'Login with Google (Fixed)';
    loginButton.style.position = 'fixed';
    loginButton.style.top = '10px';
    loginButton.style.right = '10px';
    loginButton.style.zIndex = '9999';
    loginButton.style.padding = '10px 15px';
    loginButton.style.backgroundColor = '#4285F4';
    loginButton.style.color = 'white';
    loginButton.style.fontWeight = 'bold';
    loginButton.style.border = 'none';
    loginButton.style.borderRadius = '4px';
    loginButton.style.cursor = 'pointer';
    loginButton.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
      loginButton.onclick = function() {
      // Redirect directly to the Google login endpoint
      window.location.href = `${API_BASE_URL}/api/login/google`;
      console.log("Redirecting to Google login...");
    };
    
    document.body.appendChild(loginButton);
    console.log("Login button added to page");
  }
  
  // Add debug UI to show if we're authenticated
  function addDebugUi() {
    const debugPanel = document.createElement('div');
    debugPanel.style.position = 'fixed';
    debugPanel.style.bottom = '10px';
    debugPanel.style.right = '10px';
    debugPanel.style.padding = '10px';
    debugPanel.style.backgroundColor = 'rgba(0,0,0,0.7)';
    debugPanel.style.color = 'white';
    debugPanel.style.fontFamily = 'monospace';
    debugPanel.style.zIndex = '9999';
    debugPanel.style.borderRadius = '4px';
    debugPanel.style.maxWidth = '300px';
    
    // Update the debug info periodically
    function updateDebugInfo() {
      const cookies = document.cookie;
      const hasAuthCookie = cookies.includes('auth_success');
      
      debugPanel.innerHTML = `
        <div style="margin-bottom: 5px;"><b>Auth Debug:</b></div>
        <div>Cookie count: ${cookies.split(';').filter(c => c.trim().length > 0).length}</div>
        <div>Auth cookie: ${hasAuthCookie ? '✅' : '❌'}</div>
        <div>LocalStorage backup: ${localStorage.getItem('user_backup') ? '✅' : '❌'}</div>
        <div style="margin-top: 10px;">
          <button id="debug-check-auth">Check Auth</button>
        </div>
      `;
      
      // Add event listener to the check auth button
      setTimeout(() => {
        const checkButton = document.getElementById('debug-check-auth');
        if (checkButton) {
          checkButton.onclick = async function() {
            try {
              const response = await fetch(`${API_BASE_URL}/api/users/me/profile`, {
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' }
              });
              
              if (response.ok) {
                const userData = await response.json();
                alert(`Authenticated as: ${userData.username || userData.email}`);
              } else {
                alert("Not authenticated!");
              }
            } catch (error) {
              alert(`Error: ${error.message}`);
            }
          };
        }
      }, 0);
    }
    
    updateDebugInfo();
    setInterval(updateDebugInfo, 5000);
    
    document.body.appendChild(debugPanel);
  }
  
  // Run all fixes
  patchCookieApi();
  setupSpecializedLogin();
  addDebugUi();
  
  console.log("🍪 Quiz App Cookie Fix complete! Check the 'Login with Google (Fixed)' button at top-right.");
})();
