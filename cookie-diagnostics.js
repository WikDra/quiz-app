/**
 * Quiz App Cookie Fix Script 
 * 
 * This script diagnoses and fixes common cookie-related issues in the Quiz App.
 * It's designed to help identify why cookies are not working properly, especially
 * when they're visible on the server but not accessible via JavaScript.
 */

(function() {
  console.log("=== Quiz App Cookie Diagnostics ===");
  const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5000'
    : '';

  // Create UI for cookie diagnostics
  function createDiagnosticsUI() {
    // Create container
    const container = document.createElement('div');
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.left = '20px';
    container.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    container.style.color = 'white';
    container.style.padding = '20px';
    container.style.borderRadius = '10px';
    container.style.zIndex = '9999';
    container.style.maxWidth = '500px';
    container.style.boxShadow = '0 4px 10px rgba(0, 0, 0, 0.3)';
    container.style.fontFamily = 'Arial, sans-serif';
    
    // Add title
    const title = document.createElement('h2');
    title.textContent = 'Cookie Diagnostics';
    title.style.marginTop = '0';
    title.style.marginBottom = '15px';
    title.style.fontSize = '18px';
    title.style.color = '#fff';
    container.appendChild(title);
    
    // Add cookie info section
    const cookieInfo = document.createElement('div');
    cookieInfo.id = 'cookie-diagnostics-info';
    cookieInfo.style.marginBottom = '15px';
    cookieInfo.style.fontSize = '14px';
    cookieInfo.style.lineHeight = '1.5';
    container.appendChild(cookieInfo);
    
    // Add action buttons
    const buttonContainer = document.createElement('div');
    buttonContainer.style.display = 'flex';
    buttonContainer.style.flexWrap = 'wrap';
    buttonContainer.style.gap = '10px';
    
    // Button styles
    const buttonStyle = {
      padding: '8px 12px',
      borderRadius: '4px',
      border: 'none',
      cursor: 'pointer',
      fontSize: '14px',
      fontWeight: 'bold',
      flex: '1'
    };
    
    // Create and add buttons
    const buttons = [
      {
        text: 'Check Cookies',
        color: '#4285F4',
        onClick: checkCookies
      },
      {
        text: 'Set JS Cookie',
        color: '#0F9D58',
        onClick: setJSCookie
      },
      {
        text: 'Set Server Cookie',
        color: '#DB4437',
        onClick: setServerCookie
      },
      {
        text: 'Test API Cookies',
        color: '#F4B400',
        onClick: testApiCookies
      },
      {
        text: 'Close',
        color: '#666',
        onClick: () => document.body.removeChild(container)
      }
    ];
    
    buttons.forEach(btnConfig => {
      const button = document.createElement('button');
      button.textContent = btnConfig.text;
      button.style.backgroundColor = btnConfig.color;
      button.style.color = 'white';
      
      // Apply styles
      Object.keys(buttonStyle).forEach(key => {
        button.style[key] = buttonStyle[key];
      });
      
      button.addEventListener('click', btnConfig.onClick);
      buttonContainer.appendChild(button);
    });
    
    container.appendChild(buttonContainer);
    document.body.appendChild(container);
    
    // Initial check
    checkCookies();
  }
  
  // Check for cookies and display info
  function checkCookies() {
    const infoElement = document.getElementById('cookie-diagnostics-info');
    if (!infoElement) return;
    
    // Get all cookies
    const cookies = document.cookie;
    const cookieList = cookies.split(';').map(c => c.trim()).filter(c => c);
    const cookieMap = {};
    
    cookieList.forEach(cookie => {
      const [name, value] = cookie.split('=');
      if (name) cookieMap[name] = value || '';
    });
    
    // Format cookie info
    let infoHtml = `
      <p>Total client cookies: <strong>${cookieList.length}</strong></p>
      <p>auth_success cookie: <strong>${cookieMap['auth_success'] ? '✅ Present' : '❌ Missing'}</strong></p>
      <p>visible_auth cookie: <strong>${cookieMap['visible_auth'] ? '✅ Present' : '❌ Missing'}</strong></p>
      <p>js_test_cookie: <strong>${cookieMap['js_test_cookie'] ? '✅ Present' : '❌ Missing'}</strong></p>
    `;
    
    if (cookieList.length > 0) {
      infoHtml += `<p><strong>Cookie list:</strong></p><ul style="margin: 0; padding-left: 20px;">`;
      cookieList.forEach(cookie => {
        infoHtml += `<li>${cookie}</li>`;
      });
      infoHtml += `</ul>`;
    } else {
      infoHtml += `<p style="color: #ff6b6b;">No client-side cookies detected!</p>`;
    }
    
    infoElement.innerHTML = infoHtml;
  }
  
  // Set a cookie with JavaScript
  function setJSCookie() {
    const infoElement = document.getElementById('cookie-diagnostics-info');
    try {
      // Create an expiration date
      const expires = new Date();
      expires.setTime(expires.getTime() + 3600 * 1000); // 1 hour
      
      // Set cookies with different attributes to test what works
      document.cookie = `js_test_cookie=true; path=/; expires=${expires.toUTCString()}`;
      document.cookie = `js_test_secure=true; path=/; expires=${expires.toUTCString()}; Secure`;
      document.cookie = `js_test_samesite=true; path=/; expires=${expires.toUTCString()}; SameSite=None; Secure`;
      document.cookie = `auth_success=true; path=/; expires=${expires.toUTCString()};`;
      
      // Log success
      console.log("Test cookies set via JavaScript");
      infoElement.innerHTML += `<p style="color: #42f584">✅ Test cookies set from JavaScript</p>`;
      
      // Update the display
      setTimeout(checkCookies, 100);
    } catch (error) {
      console.error("Error setting cookies:", error);
      infoElement.innerHTML += `<p style="color: #ff6b6b">❌ Error setting cookies: ${error.message}</p>`;
    }
  }
  
  // Set cookies via server API
  async function setServerCookie() {
    const infoElement = document.getElementById('cookie-diagnostics-info');
    
    try {
      infoElement.innerHTML += `<p>Requesting cookies from server...</p>`;
      
      // Call the server API endpoint that sets cookies
      const response = await fetch(`${API_BASE_URL}/api/debug/set-visible-cookie`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        infoElement.innerHTML += `<p style="color: #42f584">✅ Server request successful</p>`;
        
        // Check the response headers for Set-Cookie
        let cookieHeaders = [];
        if (response.headers) {
          cookieHeaders = response.headers.get('set-cookie');
        }
        
        if (cookieHeaders) {
          infoElement.innerHTML += `<p>Server sent cookies in response headers</p>`;
        } else {
          infoElement.innerHTML += `<p style="color: #ffcc00">⚠️ No Set-Cookie headers visible (normal due to browser security)</p>`;
        }
        
        // Update cookie display after a brief delay
        setTimeout(checkCookies, 500);
      } else {
        infoElement.innerHTML += `<p style="color: #ff6b6b">❌ Server request failed: ${response.status} ${response.statusText}</p>`;
      }
    } catch (error) {
      console.error("Error requesting cookies from server:", error);
      infoElement.innerHTML += `<p style="color: #ff6b6b">❌ Error: ${error.message}</p>`;
    }
  }
  
  // Test the API's cookie handling
  async function testApiCookies() {
    const infoElement = document.getElementById('cookie-diagnostics-info');
    
    try {
      infoElement.innerHTML += `<p>Testing API cookie handling...</p>`;
      
      // Call the test endpoint
      const response = await fetch(`${API_BASE_URL}/api/test-auth-cookies`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        
        infoElement.innerHTML += `<p style="color: #42f584">✅ API request successful</p>`;
        infoElement.innerHTML += `<p><strong>Server detected ${Object.keys(data.cookies || {}).length} cookies</strong></p>`;
        
        if (data.cookies && Object.keys(data.cookies).length > 0) {
          infoElement.innerHTML += `<p><strong>Cookies on server:</strong></p><ul style="margin: 0; padding-left: 20px;">`;
          for (const [name, value] of Object.entries(data.cookies)) {
            infoElement.innerHTML += `<li>${name}: ${value}</li>`;
          }
          infoElement.innerHTML += `</ul>`;
        }
        
        if (data.jwt_valid) {
          infoElement.innerHTML += `<p style="color: #42f584">✅ JWT token is valid (User ID: ${data.user_id})</p>`;
        } else {
          infoElement.innerHTML += `<p style="color: #ffcc00">⚠️ JWT token is not valid or not present</p>`;
          if (data.error) {
            infoElement.innerHTML += `<p>Error: ${data.error}</p>`;
          }
        }
        
        console.log("API cookie test response:", data);
      } else {
        infoElement.innerHTML += `<p style="color: #ff6b6b">❌ API request failed: ${response.status} ${response.statusText}</p>`;
      }
    } catch (error) {
      console.error("Error testing API cookies:", error);
      infoElement.innerHTML += `<p style="color: #ff6b6b">❌ Error: ${error.message}</p>`;
    }
  }
  
  // Initialize the diagnostics
  createDiagnosticsUI();
  
  console.log("=== Cookie Diagnostics UI Ready ===");
})();
