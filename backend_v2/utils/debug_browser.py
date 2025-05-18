"""
Debugging script for cookie issues in the browser
"""

# Instructions for debugging in the browser console
debugging_instructions = """
// Copy and paste this into your browser console to debug cookie issues

// First, let's check what cookies we currently have
console.log("Current cookies:", document.cookie);

// Function to make a request to our test endpoint
async function testAuth() {
  try {
    console.log("Making test request to /api/test-cookies...");
    const response = await fetch("http://localhost:5000/api/test-cookies", {
      method: "GET",
      credentials: "include" // This is important - it sends cookies with the request
    });
    
    console.log("Status:", response.status);
    console.log("Headers:");
    response.headers.forEach((value, key) => {
      console.log(`  ${key}: ${value}`);
    });
    
    const data = await response.json();
    console.log("Response data:", data);
    
    // Check cookies again after request
    console.log("Cookies after request:", document.cookie);
    
    return { success: true, data };
  } catch (error) {
    console.error("Error testing cookies:", error);
    return { success: false, error: error.message };
  }
}

// Function to test our profile endpoint
async function testProfile() {
  try {
    console.log("Testing profile endpoint...");
    const response = await fetch("http://localhost:5000/api/users/me/profile", {
      method: "GET",
      credentials: "include" // Include cookies
    });
    
    console.log("Profile status:", response.status);
    
    try {
      const data = await response.json();
      console.log("Profile data:", data);
      return { success: response.ok, data };
    } catch (e) {
      console.log("Could not parse JSON response");
      return { success: false, error: "Invalid JSON response" };
    }
  } catch (error) {
    console.error("Error testing profile:", error);
    return { success: false, error: error.message };
  }
}

// Function to debug cookie issues
async function debugCookies() {
  console.log("=== COOKIE DEBUGGING ===");
  
  // First check if we have cookies
  const hasCookies = document.cookie.length > 0;
  console.log("Has cookies:", hasCookies);
  
  // Test setting a test cookie
  console.log("Testing cookie setting...");
  const testResult = await testAuth();
  
  // Try to access profile
  console.log("Testing profile access...");
  const profileResult = await testProfile();
  
  console.log("=== DEBUG SUMMARY ===");
  console.log("1. Can set cookies:", testResult.success);
  console.log("2. Can access profile:", profileResult.success);
  console.log("3. Current cookies:", document.cookie);
  
  if (!testResult.success) {
    console.log("ISSUE DETECTED: Cannot set test cookies. Check CORS and SameSite settings.");
  }
  
  if (!profileResult.success) {
    console.log("ISSUE DETECTED: Cannot access profile. JWT cookie might not be working correctly.");
  }
  
  return {
    hasCookies,
    testResult,
    profileResult
  };
}

// Run the debugging
debugCookies().then(results => {
  console.log("Debug complete:", results);
  
  if (!results.hasCookies && !results.testResult.success) {
    console.log("RECOMMENDATION: Your browser might be blocking cookies. Try disabling any privacy extensions.");
  }
  
  if (results.testResult.success && !results.profileResult.success) {
    console.log("RECOMMENDATION: The test cookie works but JWT doesn't. Try manually logging in again.");
  }
});
"""

print(debugging_instructions)
