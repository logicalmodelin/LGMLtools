call  ..\..\venv\Scripts\activate.bat
REM copy %1 %~dp1%~n1.bkup%~x1  // �ϊ�����ƑO�̏�Ԃ��c�炸�S�~���ɂ�����Ȃ��̂ŕs���ł���΃o�b�N�A�b�v�����
python %~dp0LGMLImageSizeAdjuster.py %1 -s 320 320 --force --preferred_direction AUTO_PAD





