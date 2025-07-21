@echo off
echo OneDrive Custom Backup Tool - Console Debug Mode
echo ===============================================
echo.
echo This will run the console version with administrator privileges
echo for detailed debugging and error reporting.
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul

echo.
echo Starting OneDriveBackupTool-Console.exe...
echo.

powershell -Command "Start-Process 'OneDriveBackupTool-Console.exe' -Verb RunAs"

echo.
echo Console application started with administrator privileges.
echo Check the console window for detailed output and error messages.
echo.
pause
