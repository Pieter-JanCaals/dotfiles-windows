# Helper Functions
function Get-AliasCommand {
    param(
        $Command
    )

    try {
        $alias = Get-Alias $Command
        return ($alias | Select-Object -Property ResolvedCommandName).ResolvedCommandName
    }
    catch {
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

if ((Get-AliasCommand gp -ne "Push-Git")) {
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
            Set-Location -Path "$HOME/01-projects"
        }
        "dot" {
            Set-Location -Path "$HOME/.dotfiles"
        }
        default {
            Write-Host "Invalid location"
        }
    }
}

if (Get-AliasCommand ls -ne "Get-Files") {
    Remove-Alias ls
    Set-Alias ls Get-Files
}

function Get-Files {
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