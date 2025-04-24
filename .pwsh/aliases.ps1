# Helper Functions
function Get-AliasCommand {
    param(
        $Command
    )

    try {
        $alias = ""
        $alias = Get-Alias $Command -ErrorAction SilentlyContinue

        if ($alias -eq "") {
            return $alias
        }
        else {
            return ($alias | Select-Object -Property ResolvedCommandName).ResolvedCommandName
        }
    }
    catch {
        Write-Host "In catch"
        return ""
    }

}

# General
function Set-Profile {
    [Alias("rl")]
    [Alias("source")]
    param()

    . $HOME\.dotfiles\.pwsh\aliases.ps1
}

function New-File {
    [Alias("touch")]
    param(
        [string]$Path
    )

    New-Item -Path $Path -ItemType File
}

# GIT
function Get-GitStatus {
    [Alias("gs")]
    param()
    git status
}

function gd {
    git diff
}

$gpAlias = Get-AliasCommand gp
if ($gpAlias -eq "") {
    Set-Alias gp Push-Git
}
elseif ($gpAlias -ne "Push-Git") {
    Remove-Alias gp -Force
    Set-Alias gp Push-Git
}
function Push-Git {
    [Alias("gp")]
    param()
    
    git push
}

function gpu {
    param (
        $Branch
    )

    git push -u origin $Branch
}

function gac {
    param (
        $Message
    )

    git add . ; git commit -m $Message
}

# Movement
function goto {
    [Alias("gt")]
    param (
        $location
    )

    Switch ($location) {
        "devo" {
            Set-Location -Path "$HOME/devoteam"
        }
        "pr" {
            Set-Location -Path "$HOME/01-projects/$(Get-Files $HOME/01-projects | fzf)"
        }
        "dot" {
            Set-Location -Path "$HOME/.dotfiles"
        }
        default {
            Write-Host "Invalid location"
        }
    }
}

# List files

if (Get-AliasCommand ls -ne "Get-Files") {
    Remove-Alias ls
    Set-Alias ls Get-Files
}

function Get-Files {
    [Alias("ls")]
    param(
        [string]$Path = "."
    )

    eza.exe --group-directories-first --git --icons $Path
}

function ll {
    param(
        [string]$Path = "."
    )

    eza.exe --group-directories-first -l --git --icons $Path
}

function la {
    param(
        [string]$Path = "."
    )

    eza.exe -lab --group-directories-first -l --git --icons $Path
}

function Get-Tree {
    [Alias("tr")]
    param(
        [string]$Path = ".",
        [int]$Depth = 3
    )

    lsd.exe --tree --depth=$Depth $Path
}