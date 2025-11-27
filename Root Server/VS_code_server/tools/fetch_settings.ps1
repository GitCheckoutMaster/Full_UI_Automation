$settingsPath = Join-Path $env:APPDATA "Code\User\settings.json"

# Prepare response
$res = @{
    success = $false
    message = ""
    data    = $null
}

# Ensure settings.json exists
# if (-not (Test-Path $settingsPath)) {
#     "{}" | Out-File -Encoding utf8 $settingsPath
# }

# Load current settings
try {
    $json = Get-Content $settingsPath -Raw | ConvertFrom-Json -ErrorAction Stop
} catch {
    $res.message = "Error: settings.json contains invalid JSON. Fix it manually."
    return ($res | ConvertTo-Json -Depth 10)
}


# Process each argument
foreach ($item in $Settings) {

    $parts = $item -split "=", 2
    $key = $parts[0]
    $value = $parts[1]

    # Convert "true", "false", numbers to proper types
    if ($value -match '^(true|false)$') {
        $value = [System.Boolean]::Parse($value)
    } elseif ($value -match '^\d+$') {
        $value = [int]$value
    }

    $json | Add-Member -NotePropertyName $key -NotePropertyValue $value -Force
}

# Save updated JSON
$json | ConvertTo-Json -Depth 10 | Out-File -Encoding utf8 $settingsPath

$res.success = $true
$res.message = "VS Code settings fetched successfully!"
$res.data = $json

# Return result as JSON
return ($res | ConvertTo-Json -Depth 10)
