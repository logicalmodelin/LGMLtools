call  %~dp0\..\..\venv\Scripts\activate.bat
REM test -- python %~dp0prepareImageForSdInput.py -p2 -o %~dp0\out -min 1024 1024 %1 %2 %3 %4 %5 %6 %7 %8 %9
python %~dp0prepareImageForSdInput.py %1 --overwrite -p2 -sq --auto_min_size
pause

