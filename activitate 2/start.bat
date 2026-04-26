@echo off
cd /d "%~dp0"

start "UDP Server" cmd /k "title UDP Server & python server.py"
timeout /t 1 /nobreak >nul

start "Client 1" cmd /k "title Client 1 & python client.py"
start "Client 2" cmd /k "title Client 2 & python client.py"
start "Client 3" cmd /k "title Client 3 & python client.py"
