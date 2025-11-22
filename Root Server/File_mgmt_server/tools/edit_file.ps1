param(
    [string]$filePath,
    [string]$NewContent
)

$result = @{
    success = $false
    message = ""
    data = $null
}

if (Test-Path $filePath) {
    Set-Content -Path $filePath -Value $NewContent
    $result.success = $true
    $result.message = "File content updated successfully."
} else {
    $result.message = "File not found."
}
$result | ConvertTo-Json -Compress
