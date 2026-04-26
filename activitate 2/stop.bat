@echo off
echo Closing python instances...

taskkill /f /im python.exe >nul 2>&1
echo Closing terminals

powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"name='cmd.exe' AND commandline LIKE '%%server.py%%'\" | Invoke-CimMethod -MethodName Terminate | Out-Null"
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"name='cmd.exe' AND commandline LIKE '%%client.py%%'\" | Invoke-CimMethod -MethodName Terminate | Out-Null"

echo Done
pause