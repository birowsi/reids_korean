@echo off
setlocal
pushd "%~dp0"
echo Compiling Patcher.cs...
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /target:exe /win32icon:icon.ico /out:Korean_Patcher.exe Patcher.cs PatchManifest.cs
set "patcher_build_result=%ERRORLEVEL%"
if %patcher_build_result% equ 0 (
    echo Compilation successful! Korean_Patcher.exe created.
) else (
    echo Compilation failed.
)
pause
popd
exit /b %patcher_build_result%
