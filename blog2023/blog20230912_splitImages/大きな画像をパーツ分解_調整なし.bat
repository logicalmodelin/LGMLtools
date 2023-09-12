call  %~dp0\..\..\venv\Scripts\activate.bat
python %~dp0split_image_island.py %1 --create_subdir --min_size 0 0 --alpha_spread 0 --cutout_alpha 0
pause

