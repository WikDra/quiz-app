# Test API requests and cookie handling
# Run this script to test the API endpoints and cookie handling from outside the browser

$apiBaseUrl = "http://localhost:5000"

Write-Host "=== Testing API Endpoints and Cookies ==="

# Create a temp cookie file
$cookieJar = [System.IO.Path]::GetTempFileName()
Write-Host "Using cookie jar at: $cookieJar"

# Function to make requests with cookie jar
function Invoke-ApiRequest {
    param (
        [string]$Endpoint,
        [string]$Method = "GET"
    )
    
    Write-Host "`nTesting $Method $Endpoint..."
    
    $headers = @{
        "Content-Type" = "application/json"
        "Accept" = "application/json"
    }
    
    try {
        $result = Invoke-WebRequest -Uri "$apiBaseUrl$Endpoint" -Method $Method -Headers $headers -SessionVariable session -WebSession $session
        
        Write-Host "Status: $($result.StatusCode)"
        Write-Host "Headers:"
        foreach ($header in $result.Headers.GetEnumerator()) {
            Write-Host "  $($header.Key): $($header.Value)"
        }
        
        # Check for cookies in the response
        if ($result.Headers.ContainsKey("Set-Cookie")) {
            Write-Host "Cookies set in response:"
            foreach ($cookie in $result.Headers."Set-Cookie") {
                Write-Host "  $cookie"
            }
        } else {
            Write-Host "No cookies set in response"
        }
        
        # Show response content
        Write-Host "Response:"
        try {
            $content = $result.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3
            Write-Host $content
        } catch {
            Write-Host $result.Content
        }
        
        return $result
    } catch {
        Write-Host "Error: $_"
        if ($_.Exception.Response) {
            Write-Host "Status: $($_.Exception.Response.StatusCode)"
        }
        return $null
    }
}

# Test endpoints
$endpoints = @(
    "/api/health",
    "/api/test-cookies",
    "/api/debug/auth",
    "/api/users",
    "/api/users/me/profile"
)

foreach ($endpoint in $endpoints) {
    Invoke-ApiRequest -Endpoint $endpoint
}

# Try a direct login if Google OAuth isn't an option from command line
Write-Host "`n=== Testing Login Endpoint ==="
$loginData = @{
    email = "test@example.com"
    password = "password123"
} | ConvertTo-Json

try {
    $loginResult = Invoke-WebRequest -Uri "$apiBaseUrl/api/login" -Method POST -Body $loginData -ContentType "application/json" -SessionVariable session
    
    Write-Host "Login Status: $($loginResult.StatusCode)"
    
    # Check for cookies in the response
    if ($loginResult.Headers.ContainsKey("Set-Cookie")) {
        Write-Host "Cookies set in login response:"
        foreach ($cookie in $loginResult.Headers."Set-Cookie") {
            Write-Host "  $cookie"
        }
        
        # Try the profile endpoint again after login
        Write-Host "`nTrying profile endpoint after login..."
        $profileResult = Invoke-WebRequest -Uri "$apiBaseUrl/api/users/me/profile" -Method GET -WebSession $session
        Write-Host "Profile Status: $($profileResult.StatusCode)"
        Write-Host "Profile Response: $($profileResult.Content)"
    } else {
        Write-Host "No cookies set in login response"
    }
} catch {
    Write-Host "Login error: $_"
    if ($_.Exception.Response) {
        Write-Host "Status: $($_.Exception.Response.StatusCode)"
        
        # Try to get response body
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response: $responseBody"
    }
}

Write-Host "`n=== End of Test ==="
