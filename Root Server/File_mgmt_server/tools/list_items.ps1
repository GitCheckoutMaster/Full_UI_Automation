param(
    [Parameter(Mandatory=$true)]
    [string]$DirectoryPath
)

$result = @{
    success = $false
    data = $null
    message = ""
}  

if (-Not (Test-Path $DirectoryPath)) {
    $result.message = "Directory not found: $DirectoryPath"
}
else {
    try {
        $items = Get-ChildItem -Path $DirectoryPath -ErrorAction Stop | Select-Object Name, FullName, Length, LastWriteTime
        $result.success = $true
        $result.data = $items
    }
    catch {
        $result.message = "Error listing items: $_"
    }
}
$result | ConvertTo-Json -Compress
