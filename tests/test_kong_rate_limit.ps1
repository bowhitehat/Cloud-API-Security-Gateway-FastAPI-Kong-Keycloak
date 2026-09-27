$BaseUrl = if ($env:BASE_URL) { $env:BASE_URL } else { "http://localhost:8080" }
Write-Host "Sending 8 failed login requests to $BaseUrl/auth/login"
Write-Host "Kong config allows only 5 login requests per minute per IP."

for ($i = 1; $i -le 8; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "$BaseUrl/auth/login" `
            -Method POST `
            -ContentType "application/x-www-form-urlencoded" `
            -Body "username=user1&password=wrong_password" `
            -SkipHttpErrorCheck
        Write-Host "Attempt $i -> HTTP $($response.StatusCode)"
        Write-Host $response.Content
        Write-Host "---"
    } catch {
        Write-Host "Attempt $i -> ERROR"
        Write-Host $_.Exception.Message
        Write-Host "---"
    }
}
