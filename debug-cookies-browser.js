/**
 * Cookie-based Authentication Debug Tool for Quiz App
 * 
 * Usage: Copy this entire file and paste it into your browser console
 * when you're on your application page to diagnose authentication issues.
 */

(async function() {
  // Configuration
  const API_BASE_URL = 'http://localhost:5000';
  const FRONTEND_URL = 'http://localhost:5173';
  
  console.log('=== 🔍 Auth Debugging Tool for Quiz App ===');
  
  // Check for the presence of cookies
  function checkCookies() {
    console.log('\n📝 Checking cookies in browser:');
    
    // Get all cookies
    const cookies = document.cookie.split(';').reduce((acc, cookie) => {
      const [name, value] = cookie.trim().split('=');
      if (name) acc[name] = value;
      return acc;
    }, {});
    
    // Check for JWT cookies (though they should be httpOnly)
    const hasAccessToken = 'access_token_cookie' in cookies;
    const hasRefreshToken = 'refresh_token_cookie' in cookies;
    const hasAuthSuccess = 'auth_success' in cookies;
    
    console.log('Cookies found:', Object.keys(cookies).join(', ') || 'None');
    console.log('JWT Access Token visible in document.cookie:', hasAccessToken);
    console.log('JWT Refresh Token visible in document.cookie:', hasRefreshToken);
    console.log('Auth Success indicator cookie:', hasAuthSuccess);
    
    if (!hasAccessToken && !hasRefreshToken) {
      console.log('❌ No authentication cookies found. This may be due to httpOnly setting or cookies not being set.');
    }
    
    return cookies;
  }
  
  // Test endpoints
  async function testEndpoints() {
    const endpoints = [
      '/api/test-cookies',
      '/api/debug/auth',
      '/api/health',
      '/api/users/me/profile',
      '/api/users'
    ];
    
    console.log('\n🔄 Testing API endpoints:');
    
    for (const endpoint of endpoints) {
      try {
        console.log(`\nTesting ${endpoint}...`);
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        console.log(`Status: ${response.status}`);
        
        // Check credentials mode
        console.log(`Credentials mode used: include`);
        
        // Log response headers
        const headers = {};
        response.headers.forEach((value, key) => {
          headers[key] = value;
        });
        console.log('Response headers:', headers);
        
        if (response.status === 200) {
          try {
            const data = await response.json();
            console.log('Response data:', data);
          } catch (e) {
            console.log('Error parsing JSON:', e);
          }
        }
      } catch (error) {
        console.error(`Error with ${endpoint}:`, error);
      }
    }
  }
  
  // Attempt to fix by manually logging in
  async function attemptFix() {
    console.log('\n🔧 Attempting to fix authentication...');
    
    // Try a direct cookie-based login with fixed SameSite and Secure attributes
    const loginFixScript = document.createElement('script');
    loginFixScript.textContent = `
      // Create a function to set custom cookies with proper attributes
      function setAuthCookie(name, value) {
        document.cookie = name + "=" + value + "; path=/; SameSite=None";
      }
      
      // Set a marker cookie the server can check
      setAuthCookie('auth_debug_marker', 'true');
      
      console.log('Set auth_debug_marker cookie to help diagnose issues');
    `;
    document.body.appendChild(loginFixScript);
    document.body.removeChild(loginFixScript);
    
    console.log('Added cookie marker for server-side debugging');
    
    // Try to make a debug auth request
    try {
      const response = await fetch(`${API_BASE_URL}/api/debug/auth`, {
        credentials: 'include',
        cache: 'no-store'
      });
      
      if (response.ok) {
        const debug = await response.json();
        console.log('Authentication debug info:', debug);
        
        if (debug.jwt_identity) {
          console.log('✅ You are authenticated as user ID:', debug.jwt_identity);
          return true;
        } else {
          console.log('❌ Not authenticated according to debug endpoint');
          return false;
        }
      }
    } catch (e) {
      console.error('Error checking authentication status:', e);
      return false;
    }
  }
  
  // Provide manual OAuth login option
  function provideManualLogin() {
    console.log('\n🔑 Manual login option:');
    
    const loginButton = document.createElement('button');
    loginButton.textContent = 'Login with Google (Debug Mode)';
    loginButton.style.position = 'fixed';
    loginButton.style.top = '10px';
    loginButton.style.right = '10px';
    loginButton.style.zIndex = '9999';
    loginButton.style.padding = '10px';
    loginButton.style.backgroundColor = '#4285F4';
    loginButton.style.color = 'white';
    loginButton.style.border = 'none';
    loginButton.style.borderRadius = '4px';
    loginButton.style.cursor = 'pointer';
    
    loginButton.onclick = () => {
      const w = window.open(`${API_BASE_URL}/api/login/google`, 'oauth-login', 'width=600,height=700');
      
      // Poll to check when the window closes
      const checkInterval = setInterval(() => {
        if (w.closed) {
          clearInterval(checkInterval);
          console.log('OAuth login window closed, checking auth status...');
          setTimeout(() => {
            checkCookies();
            testEndpoints();
          }, 1000);
        }
      }, 500);
    };
    
    document.body.appendChild(loginButton);
    console.log('Added debug login button to the page');
  }
  
  // Apply a fix for third-party cookies (SameSite=None requires Secure)
  function applyCookieFix() {
    // Create a helper script to fix cookies if needed
    const fixScript = document.createElement('script');
    fixScript.textContent = `
      // Fix cookies that might be incorrectly set
      window.fixCookies = function() {
        // Make a fetch to the test-cookies endpoint
        return fetch('${API_BASE_URL}/api/test-cookies', {
          credentials: 'include',
          cache: 'no-store'
        }).then(response => {
          console.log('Test cookies response status:', response.status);
          return response.json();
        }).then(data => {
          console.log('Test cookies response:', data);
          console.log('Current cookies after test:', document.cookie);
          return true;
        }).catch(err => {
          console.error('Error testing cookies:', err);
          return false;
        });
      };
      
      // Create an event listener to capture new cookies
      window.__capturedCookies = [];
      const originalSetCookie = document.cookie.__lookupSetter__('cookie');
      document.__defineSetter__('cookie', function(val) {
        window.__capturedCookies.push(val);
        console.log('Cookie being set:', val);
        return originalSetCookie.call(document, val);
      });
      
      console.log('Cookie debugging helpers installed');
    `;
    
    document.body.appendChild(fixScript);
    document.body.removeChild(fixScript);
    
    // Call the fix function
    if (typeof window.fixCookies === 'function') {
      window.fixCookies().then(() => {
        console.log('Completed cookie fix attempt');
      });
    }
  }
  
  // Run the debug sequence
  const cookies = checkCookies();
  await testEndpoints();
  const isAuthenticated = await attemptFix();
  
  if (!isAuthenticated) {
    console.log('\n⚠️ Not authenticated. Applying additional fixes...');
    applyCookieFix();
    provideManualLogin();
    
    console.log(`
      ℹ️ Troubleshooting Instructions:
      
      1. Check if you're seeing any cookies in the output above
      2. Try clicking the "Login with Google (Debug Mode)" button added to the page
      3. After login completes, look for new debug output
      4. If still not working, try these fixes:
         - Check Chrome settings: chrome://settings/cookies
           Ensure third-party cookies are not blocked
         - Try in an Incognito window (fewer cookie restrictions)
         - Try Firefox (often more lenient with cross-site cookies)
    `);
  } else {
    console.log('✅ Authentication appears to be working!');
  }
  
  console.log('=== 🔍 End of Auth Debugging Tool ===');
})();
