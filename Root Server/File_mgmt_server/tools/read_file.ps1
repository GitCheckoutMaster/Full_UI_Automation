# param(
#     [Parameter(Mandatory=$true)]
#     [string]$FilePath
# )

# if (-Not (Test-Path $FilePath)) {
#     $errorJson = @{ status="error"; message="File not found"; code="ENOENT" } | ConvertTo-Json -Compress
#     Write-Output $errorJson
#     exit 1
# }

# try {
#     $content = Get-Content -Path $FilePath -ErrorAction Stop | Out-String
#     $successJson = @{ status="success"; data=$content } | ConvertTo-Json -Compress
#     Write-Output $successJson
#     exit 0
# }
# catch {
#     $errorJson = @{ status="error"; message=$_.Exception.Message; code="EIO" } | ConvertTo-Json -Compress
#     Write-Output $errorJson
#     exit 1
# }
param(
    [Parameter(Mandatory=$true)]
    [string]$FilePath
)

$result = @{
    success = $false
    data = $null
    message = ""
}

if (-not (Test-Path $FilePath)) {
    $result.message = "File not found: $FilePath"
}
else {
    try {
        $content = Get-Content -Path $FilePath -Raw -ErrorAction Stop
        $result.success = $true
        $result.data = $content
    }
    catch {
        $result.message = "Error reading file: $_"
    }
}

$result | ConvertTo-Json -Compress
