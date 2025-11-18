param(
    [Parameter(Mandatory=$true)]
    [string]$FilePath,
    [string]$NewContent
)

if (-Not (Test-Path $FilePath)) {
    Write-Host "File not found: $FilePath"
    exit 1
}
try {
    Set-Content -Path $FilePath -Value $NewContent -ErrorAction Stop
    Write-Host "File updated successfully: $FilePath"
    exit 0
}
catch {
    Write-Host "Error updating file: $_"
    exit 1
}
