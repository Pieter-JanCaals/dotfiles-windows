#Requires -Version 5.1
[CmdletBinding()]
param(
    # Download and install JetBrains Mono Nerd Font. Only needed on a new
    # machine, or to pick up a newer Nerd Fonts release.
    [switch]$Fonts
)

$dotfiles = "$env:USERPROFILE\.dotfiles"

function New-FileLink([string]$path, [string]$target) {
    if (Test-Path $path) {
        $item = Get-Item $path -Force
        if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
            Write-Host "  already linked: $path"
        } else {
            Write-Warning "  exists but is not a symlink - skipping: $path"
        }
        return
    }
    New-Item -ItemType SymbolicLink -Path $path -Target $target | Out-Null
    Write-Host "  created symlink: $path -> $target"
}

function New-Junction([string]$path, [string]$target) {
    if (Test-Path $path) {
        $item = Get-Item $path -Force
        if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
            Write-Host "  already linked: $path"
        } else {
            Write-Warning "  exists but is not a junction - skipping: $path"
        }
        return
    }
    New-Item -ItemType Junction -Path $path -Target $target | Out-Null
    Write-Host "  created junction: $path -> $target"
}

# --- Home directory junctions ---
# Each name is created as ~\<name> -> $dotfiles\<name>

$homeJunctions = @(
    ".config"
    ".pwsh"
    ".claude/skills"
)

foreach ($name in $homeJunctions) {
    $target = Join-Path $dotfiles $name
    $path   = Join-Path $env:USERPROFILE $name
    New-Junction $path $target
}

# --- PowerShell profile shims ---
# powershell.exe (5.1) and pwsh (7+) use different profile directories.
# We write CurrentUserAllHosts (profile.ps1) for each engine that is installed.

$shimContent = ". `"$env:USERPROFILE\.pwsh\profile.ps1`""

$profileDirs = @(
    "$env:USERPROFILE\Documents\WindowsPowerShell"  # powershell.exe (5.1)
    "$env:USERPROFILE\Documents\PowerShell"         # pwsh (7+)
)

foreach ($dir in $profileDirs) {
    $shim = "$dir\profile.ps1"
    if (Test-Path $shim) {
        Write-Host "  already exists: $shim"
    } else {
        New-Item -ItemType Directory $dir -Force | Out-Null
        Set-Content -Path $shim -Value $shimContent -Encoding UTF8
        Write-Host "  created profile shim: $shim"
    }
}

# --- Fonts ---
# Opt-in: this is a large download that only matters on first setup, or when
# refreshing to a newer Nerd Fonts release. Everything above is idempotent and
# cheap, so the common re-run skips this entirely.

function Install-NerdFont {
    $fontZip  = "$env:TEMP\JetBrainsMono.zip"
    $fontDir  = "$env:TEMP\JetBrainsMono"
    $fontsUrl = "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.zip"

    Write-Host "  downloading JetBrains Mono Nerd Font..."
    Invoke-WebRequest -Uri $fontsUrl -OutFile $fontZip -UseBasicParsing

    Expand-Archive -Path $fontZip -DestinationPath $fontDir -Force

    $shellFonts     = (New-Object -ComObject Shell.Application).Namespace(0x14)
    $systemFontsDir = $shellFonts.Self.Path
    $userFontsDir   = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts"

    Get-ChildItem -Path $fontDir -Include "*.ttf","*.otf" -Recurse | ForEach-Object {
        $inSystem = Test-Path (Join-Path $systemFontsDir $_.Name)
        $inUser   = Test-Path (Join-Path $userFontsDir   $_.Name)
        if ($inSystem -or $inUser) {
            Write-Host "  already installed: $($_.Name)"
        } else {
            $shellFonts.CopyHere($_.FullName, 0x10)
        }
    }

    Remove-Item $fontZip -Force
    Remove-Item $fontDir -Recurse -Force
    Write-Host "  installed JetBrains Mono Nerd Font"
}

if ($Fonts) {
    Install-NerdFont
} else {
    Write-Host "  skipping fonts (re-run with -Fonts to install or refresh them)"
}

# --- App-specific junctions ---

# Windows Terminal: detect package family name so the path survives version changes
$wtPkg = Get-AppxPackage -Name 'Microsoft.WindowsTerminal' -ErrorAction SilentlyContinue
if (-not $wtPkg) {
    $wtPkg = Get-AppxPackage -Name 'Microsoft.WindowsTerminalPreview' -ErrorAction SilentlyContinue
}

if ($wtPkg) {
    $wtLocalState = "$env:LOCALAPPDATA\Packages\$($wtPkg.PackageFamilyName)\LocalState"
    $wtTarget     = Join-Path $dotfiles ".config\windows-terminal"
    New-Junction $wtLocalState $wtTarget
} else {
    Write-Warning "  Windows Terminal not found - skipping LocalState junction"
}

# --- VSCode ---
New-FileLink "$env:APPDATA\Code\User\settings.json" "$dotfiles\.vscode\settings.json"