$ErrorActionPreference = 'Stop'
$logPath = Join-Path $PSScriptRoot 'wsl_repair.log'
function Log($message) {
    Add-Content -LiteralPath $logPath -Value ((Get-Date -Format o) + ' ' + $message) -Encoding UTF8
}
try {
    Log 'Starting WSL service recovery with administrator rights.'
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Administrator token not available.'
    }
    Get-Process -Name wsl -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Log 'Stopped waiting wsl.exe clients.'
    $service = Get-Service -Name WslService
    if ($service.Status -ne 'Stopped') {
        try {
            $service.Stop()
            $service.WaitForStatus([System.ServiceProcess.ServiceControllerStatus]::Stopped, [TimeSpan]::FromSeconds(20))
            Log 'WslService stopped normally.'
        } catch {
            Log ('Normal service stop failed or timed out: ' + $_.Exception.Message)
            $processes = @(Get-Process -Name wslservice -ErrorAction SilentlyContinue)
            foreach ($process in $processes) {
                Log ('Stopping unresponsive WSL service process ' + $process.Id)
                Stop-Process -Id $process.Id -Force
            }
            Start-Sleep -Seconds 3
        }
    }
    $service = Get-Service -Name WslService
    if ($service.Status -ne 'Running') {
        Start-Service -Name WslService
        $service.Refresh()
        $service.WaitForStatus([System.ServiceProcess.ServiceControllerStatus]::Running, [TimeSpan]::FromSeconds(20))
    }
    Log 'SUCCESS: WslService is running. Linux readiness still needs verification.'
} catch {
    Log ('FAILED: ' + $_.Exception.Message)
    exit 1
}
