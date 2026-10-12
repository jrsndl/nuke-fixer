@echo off
rem Build dist\NukeFixer\NukeFixer.exe. Run from anywhere.
cd /d "%~dp0"
python -m PyInstaller --noconfirm NukeFixer.spec || goto :error
rem user-editable example scripts next to the exe
xcopy /E /I /Y scripts dist\NukeFixer\scripts >nul
echo.
echo Built: %~dp0dist\NukeFixer\NukeFixer.exe
pause
exit /b 0
:error
echo Build FAILED
pause
exit /b 1
