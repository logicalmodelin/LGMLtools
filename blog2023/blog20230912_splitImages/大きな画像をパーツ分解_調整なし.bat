call  %~dp0\..\..\venv\Scripts\activate.bat
python %~dp0split_image_island.py %1 --create_subdir -ms 0 0 --border 0 -ca 0
pause

