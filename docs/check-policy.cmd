@echo off
setlocal
set FAILED=0
call :expect allowed pypi.org:443
call :expect allowed github.com:443
call :expect allowed archive.ubuntu.com:443
call :expect allowed cdn.playwright.dev:443
call :expect blocked s3.amazonaws.com:443
call :expect blocked api.openai.com:443
call :expect blocked sourceforge.net:443
echo.
if %FAILED%==0 goto :allpass
echo %FAILED% checks failed.
exit /b 1
:allpass
echo All checks passed.
exit /b 0

:expect
sbx policy check network %2 >nul 2>&1
if errorlevel 1 goto :isblocked
set RESULT=allowed
goto :compare
:isblocked
set RESULT=blocked
:compare
if "%RESULT%"=="%1" goto :pass
echo FAIL  %2  expected %1, got %RESULT%
set /a FAILED+=1
exit /b 0
:pass
echo PASS  %2  expected %1
exit /b 0
