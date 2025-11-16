param(
    [Parameter(Mandatory=$true)]
    [string]$AppName
)

# Normalize input
$AppName = $AppName.Trim().ToLower()

Write-Host "Searching for application: $AppName"

# 1️⃣ Direct executable attempt
try {
    Start-Process $AppName -ErrorAction Stop
    Write-Host "Opened using direct executable name."
    exit 0 # Explicit success exit code
}
catch {
    # Write-Host "Executable not found directly. Searching directories..."
}

# 2️⃣ Search in Program Files & Program Files (x86)
$searchDirs = @(
    "$env:ProgramFiles",
    "$env:ProgramFiles (x86)"
)

$exePath = $null

foreach ($dir in $searchDirs) {
    if (Test-Path $dir) {
        # Note: Using Select-Object -First 1 is generally better for performance
        $found = Get-ChildItem -Path $dir -Recurse -Filter "*.exe" -ErrorAction SilentlyContinue |
                     Where-Object { $_.Name.ToLower() -like "*$AppName*" } |
                     Select-Object -First 1

        if ($found) {
            $exePath = $found.FullName
            break
        }
    }
}

if ($exePath) {
    Start-Process $exePath
    Write-Host "Application found and opened: $exePath"
    exit 0 # Explicit success exit code
}

# 3️⃣ Search Start Menu shortcuts
$startMenuDirs = @(
    "$env:APPDATA\Microsoft\Windows\Start Menu\Programs",
    "$env:ProgramData\Microsoft\Windows\Start Menu\Programs"
)

foreach ($dir in $startMenuDirs) {
    if (Test-Path $dir) {
        $shortcut = Get-ChildItem -Path $dir -Recurse -Filter "*.lnk" -ErrorAction SilentlyContinue |
                         Where-Object { $_.Name.ToLower() -like "*$AppName*" } |
                         Select-Object -First 1

        if ($shortcut) {
            Start-Process $shortcut.FullName
            Write-Output "Application opened using Start Menu shortcut."
            exit 0 # Explicit success exit code
        }
    }
}

# 🛑 Application not found - Exit with an error code (e.g., 1)
Write-Host "Application search FAILED. No executable or shortcut found."
exit 1