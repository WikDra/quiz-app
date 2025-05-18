// Cookie debug helper for quiz-app
// Copy and paste this code into your browser console to diagnose cookie issues

// Check current cookies
function checkCookies() {
  console.log("Current cookies:", document.cookie);
  
  // Check if JWT cookies exist (these should be HttpOnly, so not visible in document.cookie)
  const accessTokenExists = document.cookie.includes('access_token_cookie');
  const refreshTokenExists = document.cookie.includes('refresh_token_cookie');
  
  console.log("Access token visible in document.cookie:", accessTokenExists);
  console.log("Refresh token visible in document.cookie:", refreshTokenExists);
  console.log("Note: JWT cookies should be HttpOnly and not visible here");
  
  return {accessTokenExists, refreshTokenExists};
}

// Test the API endpoints
async function testEndpoints() {
  const baseUrl = 'http://localhost:5000';
  const endpoints = [
    '/api/test-cookies',
    '/api/debug/auth',
    '/api/health',
    '/api/users/me/profile'
  ];
  
  console.log("Testing API endpoints with credentials:");
  
  for (const endpoint of endpoints) {
    try {
      console.log(`\nTesting ${endpoint}...`);
      const response = await fetch(`${baseUrl}${endpoint}`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      console.log(`Status: ${response.status}`);
      
      // Log response headers
      console.log("Response headers:");
      response.headers.forEach((value, key) => {
        console.log(`  ${key}: ${value}`);
      });
      
      // Log response body
      try {
        const data = await response.json();
        console.log("Response body:", data);
      } catch (e) {
        console.log("Error parsing response JSON:", e);
      }
    } catch (error) {
      console.error(`Error with ${endpoint}:`, error);
    }
  }
}

// Test cookie setting
async function testCookieSetting() {
  const baseUrl = 'http://localhost:5000';
  
  console.log("\nTesting cookie setting...");
  try {
    const response = await fetch(`${baseUrl}/api/test-cookies`, {
      credentials: 'include'
    });
    
    console.log(`Status: ${response.status}`);
    console.log("Set-Cookie headers:");
    if (response.headers.get('set-cookie')) {
      console.log(`  ${response.headers.get('set-cookie')}`);
    } else {
      console.log("  No Set-Cookie headers found");
    }
    
    // Check if cookies were set
    setTimeout(() => {
      console.log("\nChecking if test cookie was set:");
      checkCookies();
    }, 500);
    
  } catch (error) {
    console.error("Error testing cookie setting:", error);
  }
}

// Run tests
(async function() {
  console.log("=== COOKIE DEBUGGING TOOL FOR QUIZ-APP ===");
  console.log("Current cookies:");
  checkCookies();
  await testEndpoints();
  await testCookieSetting();
  console.log("\n=== END OF DEBUGGING TOOL ===");
})();
