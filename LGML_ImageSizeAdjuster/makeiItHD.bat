for %%I IN ( %1 ) do set "DIRNAME=%%~dpI"
call  ..\venv\Scripts\activate.bat
python %~dp0LGMLImageSizeAdjuster.py %1 -wpx 1280 -hpx 720 -o "%DIRNAME%out\HD-{n}.png" --dev__result_as_json



