call  ..\..\venv\Scripts\activate.bat
REM copy %1 %~dp1%~n1.bkup%~x1  // 変換すると前の状態が残らずゴミ箱にも入らないので不安であればバックアップを取る
python %~dp0LGMLImageSizeAdjuster.py %1 -s 320 320 --force --preferred_direction AUTO_PAD





