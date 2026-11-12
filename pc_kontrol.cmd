@echo off
"%~dp0.venv\Scripts\python.exe" "%~dp0verify_pc.py" %*
exit /b %errorlevel%
