call  %~dp0\..\..\venv\Scripts\activate.bat
python %~dp0split_image_island.py %1 --create_subdir --min_size 4 4 --alpha_spread 10 --cutout_alpha 2
pause

