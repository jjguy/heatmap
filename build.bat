@echo off
rem in theory, as long as you launch the VS command prompt, the rest of this should 
rem just work.  I built the distributed DLLs on VS2012 cmd prompt from the distribution directory with just:
rem  c:\heatmap-2.0\build\win32> build.bat
rem
rem ----------- x86 -------------
call "%vcinstalldir%\bin\vcvars32.bat"
if not exist x86 mkdir x86
"%VCINSTALLDIR%\bin\cl.exe" /c /Zi /nologo /W3 /WX- /O2 /Oi /Oy- /GL /D WIN32 /D NDEBUG /D _WINDOWS /D _USRDLL /D HEATMAP_EXPORTS /D _WINDLL /D _UNICODE /D UNICODE /Gm- /EHsc /MD /GS /Gy /fp:precise /Zc:wchar_t /Zc:forScope /Fo"x86\\" /Fd"x86\VC110.PDB" /Gd /TC /analyze- HEATMAP\HEATMAP.C
@if not ERRORLEVEL 0 goto bad


"%VCINSTALLDIR%\bin\link.exe" /OUT:".\cHeatmap-x86.dll" /INCREMENTAL:NO /NOLOGO kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /MANIFEST /MANIFESTUAC:"level='asInvoker' uiAccess='false'" /manifest:embed /PDB:"x86\HEATMAP.PDB" /SUBSYSTEM:WINDOWS /OPT:REF /OPT:ICF /LTCG /TLBID:1 /DYNAMICBASE /NXCOMPAT /IMPLIB:"x86\HEATMAP.LIB" /MACHINE:X86 /SAFESEH /DLL x86\HEATMAP.OBJ
@if not ERRORLEVEL 0 goto bad

rem ----------- x64 -------------
call "%vcinstalldir%\bin\x86_amd64\vcvarsx86_amd64.bat"
if not exist x64 mkdir x64

"%VCINSTALLDIR%\bin\x86_amd64\cl.exe" /c /Zi /nologo /W3 /WX- /O2 /Oi /GL /D WIN32 /D NDEBUG /D _WINDOWS /D _USRDLL /D HEATMAP_EXPORTS /D _WINDLL /D _UNICODE /D UNICODE /Gm- /EHsc /MD /GS /Gy /fp:precise /Zc:wchar_t /Zc:forScope /Fo"X64\\" /Fd"X64\VC110.PDB" /Gd /TC HEATMAP\HEATMAP.C
@if not ERRORLEVEL 0 goto bad

"%VCINSTALLDIR%\bin\x86_amd64\link.exe" /OUT:".\cHeatmap-x64.dll" /INCREMENTAL:NO /NOLOGO kernel32.lib user32.lib gdi32.lib winspool.lib comdlg32.lib advapi32.lib shell32.lib ole32.lib oleaut32.lib uuid.lib odbc32.lib odbccp32.lib /MANIFEST /MANIFESTUAC:"level='asInvoker' uiAccess='false'" /manifest:embed /PDB:"X64\HEATMAP.PDB" /SUBSYSTEM:WINDOWS /OPT:REF /OPT:ICF /LTCG /TLBID:1 /DYNAMICBASE /NXCOMPAT /IMPLIB:"X64\HEATMAP.LIB" /MACHINE:X64 /DLL X64\HEATMAP.OBJ
@if not ERRORLEVEL 0 goto bad

echo x86 and x64 DLLs compiled.
echo Cleaning up...
rmdir /s /q x86\
rmdir /s /q x64\

goto end

:bad
echo Error

:end
