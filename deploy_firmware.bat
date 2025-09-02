@echo off
:: ============================================================================
:: Deploys firmware and libraries to a CircuitPython microcontroller.
::
:: USAGE:
::   deploy_firmware.bat <DRIVE_LETTER>
::
:: EXAMPLE:
::   deploy_firmware.bat G
::
:: WHAT IT DOES:
::   1. Checks if a drive letter was provided.
::   2. Checks if the target drive exists.
::   3. Creates a 'lib' directory on the drive if it doesn't exist.
::   4. Deletes the old 'firmware', 'communicate', and 'shared_lib'
::      directories from the drive's 'lib' folder. This is crucial
::      to remove any old or deleted files.
::   5. Copies the new versions of these directories from the project
::      folder to the drive's 'lib' folder.
:: ============================================================================

set "DRIVE_LETTER=%~1"

:: --- Input Validation ---
if "%DRIVE_LETTER%"=="" (
    echo.
    echo ERROR: No drive letter provided.
    echo.
    echo USAGE: %~n0 G
    echo.
    goto :end
)

if not exist %DRIVE_LETTER%:\ (
    echo.
    echo ERROR: Drive %DRIVE_LETTER%: does not exist.
    echo Please check the drive letter and try again.
    echo.
    goto :end
)

:: --- Set up paths ---
set "DEST_DRIVE=%DRIVE_LETTER%:"
set "DEST_LIB_PATH=%DEST_DRIVE%\lib"

echo.
echo ======================================================================
echo  Deploying to CircuitPython Device on Drive %DEST_DRIVE%
echo ======================================================================
echo.

:: Create the 'lib' directory if it doesn't exist
if not exist "%DEST_LIB_PATH%" (
    echo Creating destination directory: %DEST_LIB_PATH%
    mkdir "%DEST_LIB_PATH%"
)

:: --- List of directories to copy ---
set "DIRS_TO_COPY=firmware communicate shared_lib"

:: --- Main Deployment Loop ---
for %%d in (%DIRS_TO_COPY%) do (
    echo.
    echo --- Processing %%d ---
    
    REM First, remove the old directory from the device to ensure a clean copy
    if exist "%DEST_LIB_PATH%\%%d\" (
        echo  - Removing old version of %%d from device...
        rd /s /q "%DEST_LIB_PATH%\%%d"
    ) else (
        echo  - No old version of %%d found on device.
    )

    REM Now, copy the new directory from the project source
    if exist "%%d\" (
        echo  - Copying new version of %%d to device...
        xcopy "%%d" "%DEST_LIB_PATH%\%%d\" /E /I /Y /Q /C
    ) else (
        echo  - WARNING: Source directory %%d not found in project folder.
    )
)

echo.
echo ======================================================================
echo  Deployment complete!
echo ======================================================================
echo.

:end
pause