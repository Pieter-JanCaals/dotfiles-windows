# GIT
function gac {
    param (
        $Message
    )

    git add . ; git commit -m $Message
}

# Movement
New-Alias gt goto

function goto {
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

function Set-AliasLs {
    [alias('ls')]
    param(
        [string]$Path = "."
    )

    eza.exe --group-directories-first --git --icons $Path
}

function Set-AliasLl {
    [alias('ll')]
    param(
        [string]$Path = "."
    )

    eza.exe --group-directories-first -l --git --icons $Path
}

function Set-AliasLa {
    [alias('la')]
    param(
        [string]$Path = "."
    )

    eza.exe -lab --group-directories-first -l --git --icons $Path
}

# Enable tab completion for AZ CLI
Register-ArgumentCompleter -Native -CommandName az -ScriptBlock {
    param($commandName, $wordToComplete, $cursorPosition)
    $completion_file = New-TemporaryFile
    $env:ARGCOMPLETE_USE_TEMPFILES = 1
    $env:_ARGCOMPLETE_STDOUT_FILENAME = $completion_file
    $env:COMP_LINE = $wordToComplete
    $env:COMP_POINT = $cursorPosition
    $env:_ARGCOMPLETE = 1
    $env:_ARGCOMPLETE_SUPPRESS_SPACE = 0
    $env:_ARGCOMPLETE_IFS = "`n"
    $env:_ARGCOMPLETE_SHELL = 'powershell'
    az 2>&1 | Out-Null
    Get-Content $completion_file | Sort-Object | ForEach-Object {
        [System.Management.Automation.CompletionResult]::new($_, $_, "ParameterValue", $_)
    }
    Remove-Item $completion_file, Env:\_ARGCOMPLETE_STDOUT_FILENAME, Env:\ARGCOMPLETE_USE_TEMPFILES, Env:\COMP_LINE, Env:\COMP_POINT, Env:\_ARGCOMPLETE, Env:\_ARGCOMPLETE_SUPPRESS_SPACE, Env:\_ARGCOMPLETE_IFS, Env:\_ARGCOMPLETE_SHELL
}

Set-PSReadlineKeyHandler -Key Tab -Function MenuComplete

$ENV:STARSHIP_CONFIG = "$HOME\.dotfiles\.config\starship.toml"
$ENV:STARSHIP_DISTRO = "者 xcad"
Invoke-Expression (&starship init powershell)