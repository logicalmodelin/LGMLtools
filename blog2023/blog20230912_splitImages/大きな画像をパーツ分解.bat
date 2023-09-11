call  %~dp0\..\..\venv\Scripts\activate.bat
python %~dp0split_image_island.py %1 --create_subdir -ms 4 4 --border 4 -ca 2
pause

