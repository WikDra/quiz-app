/**
 * Quiz App Cookie Checker
 * A simple script to check and fix cookie visibility in the browser.
 * Run this in the browser console to diagnose cookie issues.
 */

console.log("=== Quiz App Cookie Checker ===");

// Check all cookies
const allCookies = document.cookie;
const cookieList = allCookies.split(';').map(c => c.trim()).filter(c => c);

console.log(`Found ${cookieList.length} cookies visible to JavaScript:`);
cookieList.forEach(cookie => console.log(`- ${cookie}`));

// Check for auth_success cookie
const hasAuthCookie = cookieList.some(c => c.startsWith('auth_success='));
console.log(`Auth success cookie: ${hasAuthCookie ? 'Present ✅' : 'Missing ❌'}`);

// Check JWT cookies (these won't be visible if HttpOnly)
console.log("Note: JWT cookies are HttpOnly and won't be visible to JavaScript");

// Set a test cookie
console.log("\nSetting test cookie...");
try {
  const expires = new Date();
  expires.setTime(expires.getTime() + 3600 * 1000); // 1 hour
  document.cookie = `check_cookie_test=true; path=/; expires=${expires.toUTCString()}; SameSite=None; Secure`;
  console.log("Test cookie set successfully");
} catch (error) {
  console.error("Error setting test cookie:", error);
}

// Verify the test cookie was set
const updatedCookies = document.cookie;
const testCookieSet = updatedCookies.includes('check_cookie_test=true');
console.log(`Test cookie visible: ${testCookieSet ? 'Yes ✅' : 'No ❌'}`);

// Set auth_success cookie
console.log("\nTrying to set auth_success cookie...");
try {
  const expires = new Date();
  expires.setTime(expires.getTime() + 3600 * 1000); // 1 hour
  document.cookie = `auth_success=true; path=/; expires=${expires.toUTCString()}; SameSite=None; Secure`;
  console.log("auth_success cookie set attempt complete");
} catch (error) {
  console.error("Error setting auth_success cookie:", error);
}

// Verify the auth cookie was set
const authCookieSet = document.cookie.includes('auth_success=true');
console.log(`auth_success cookie now visible: ${authCookieSet ? 'Yes ✅' : 'No ❌'}`);

// Final report
console.log("\n=== Cookie Status Summary ===");
console.log(`Total visible cookies: ${document.cookie.split(';').filter(c => c.trim()).length}`);
console.log(`Can set cookies from JavaScript: ${testCookieSet ? 'Yes ✅' : 'No ❌'}`);
console.log(`auth_success cookie present: ${document.cookie.includes('auth_success') ? 'Yes ✅' : 'No ❌'}`);

// Check if the page is running in a secure context
console.log(`Running in secure context: ${window.isSecureContext ? 'Yes ✅' : 'No ❌'}`);

// Suggestions
console.log("\n=== Suggestions ===");
if (!testCookieSet) {
  console.log("⚠️ Your browser may be blocking third-party cookies.");
  console.log("Try these fixes:");
  console.log("1. Use the same domain for backend and frontend");
  console.log("2. Check browser settings to allow cookies from this site");
  console.log("3. Consider using localStorage as a fallback for auth state");
}

if (window.location.protocol !== 'https:') {
  console.log("⚠️ You're using HTTP instead of HTTPS.");
  console.log("Cookies with SameSite=None require a secure context (HTTPS).");
}

console.log("\nUse the Cookie Diagnostics tool for more detailed testing:");
console.log("Open cookie-diagnostics.html in your browser");
