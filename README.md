# dotfiles

Windows dotfiles managed via directory junctions.

## Structure

| Managed folder | Contents |
|---|---|
| `.config/` | Starship config |
| `.config/windows-terminal/` | Windows Terminal `settings.json` (junctioned from `LocalState`) |
| `.pwsh/` | PowerShell profile and aliases |

## Installation

### 1. Clone the repo

```powershell
git clone https://github.com/pieter-jan-caals/dotfiles $env:USERPROFILE\.dotfiles
```

### 2. Install prerequisites

```powershell
winget import -i .\winget_packages.json
```
Restart powershell

### 3. Allow local scripts (once per machine)

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 4. Run the install script

```powershell
& "$env:USERPROFILE\.dotfiles\install.ps1" -Fonts
```

This creates directory junctions so `~\.config`, `~\.pwsh`, and Windows Terminal's `LocalState` all point into the repo. The Windows Terminal path is auto-detected via `Get-AppxPackage` so it works for both the stable and preview releases.

`-Fonts` downloads and installs JetBrains Mono Nerd Font. It is only needed on first setup, or to pick up a newer Nerd Fonts release — so later re-runs can just be:

```powershell
& "$env:USERPROFILE\.dotfiles\install.ps1"
```

## Adding a new home directory folder

1. Move the folder into `~\.dotfiles\`
2. Add its name to `$homeJunctions` in `install.ps1`
3. Re-run `install.ps1` to create the junction
4. Commit the new folder

## Adding a new app-specific junction

For apps whose config lives at an unpredictable path (like Windows Terminal), add a detection + `New-Junction` call in the `# App-specific junctions` section of `install.ps1`.
