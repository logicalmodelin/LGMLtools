call ..\venv\Scripts\activate.bat
python %~dp0LGMLImageSizeAdjuster.py %1 -s 320 320 --force --preferred_direction AUTO_PAD
pause