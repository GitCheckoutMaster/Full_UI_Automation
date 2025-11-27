param(
    [Parameter(Mandatory=$true, ValueFromPipeline=$true, ValueFromPipelineByPropertyName=$true)]
    [Alias('FullPath','File')]
    [string]$Path
)

$res = @{
    success = $false
    message = ""
    data = $null
}

if (-not $Path) { 
    $res.message = "No path supplied"
    return ($res | ConvertTo-Json -Depth 10)
}

try {
    $FullPath = [System.IO.Path]::GetFullPath([Environment]::ExpandEnvironmentVariables($Path))
}
catch {
    $res.message = "Invalid path: $Path"
    return ($res | ConvertTo-Json -Depth 10)
}

$dir = Split-Path -Parent $FullPath
if ($dir -and -not (Test-Path -LiteralPath $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

if (-not (Test-Path -LiteralPath $FullPath)) {
    New-Item -ItemType File -Path $FullPath -Force | Out-Null
}

# Try using the 'code' command (VS Code CLI)
$vsCodeCmd = Get-Command "code" -ErrorAction SilentlyContinue

if ($vsCodeCmd) {
    try {
        code $FullPath
        $res.success = $true
        $res.message = "VS Code opened successfully"
        $res.data = $FullPath
    }
    catch {
        $res.message = "Failed to launch VS Code using 'code' command"
    }
}
else {
    $res.message = "'code' command not found in PATH"
}

return ($res | ConvertTo-Json -Depth 10)
