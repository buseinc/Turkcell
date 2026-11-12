@echo off
"%~dp0.venv\Scripts\python.exe" "%~dp0run_project.py" %*
exit /b %errorlevel%
