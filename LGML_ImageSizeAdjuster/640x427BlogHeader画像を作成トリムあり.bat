for %%I IN ( %1 ) do set "DIRNAME=%%~dpI"
call  ..\venv\Scripts\activate.bat
python %~dp0LGMLImageSizeAdjuster.py %1 -s 640 427 --force --preferred_direction AUTO_CROP -o "{p}/{n}_640x427.png"




