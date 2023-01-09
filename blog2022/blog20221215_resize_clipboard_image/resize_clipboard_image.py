import sys
from PIL import ImageGrab
import io

if __name__ == '__main__':
    try:
        import win32clipboard
    except ImportError:
        print('win32clipboard モジュールが必要です。'
              ' >pip install pywin32 | python -m pip install pywin32', file=sys.stderr)
        sys.exit(1)
    if len(sys.argv) < 2:
        print('画像の横幅を第一引数に指定してください。', file=sys.stderr)
        sys.exit(1)
    img = ImageGrab.grabclipboard()
    if not img:
        print('クリップボードに画面がありません。', file=sys.stderr)
        sys.exit(1)

    width = int(sys.argv[1])

    # if img.size[0] < width:
    #     print('画像の横幅が指定より小さいです。', file=sys.stderr)
    #     sys.exit(1)

    ratio = float(img.size[0] / img.size[1])
    size = (width, int(width / ratio))
    img = img.resize(size)
    # img.show()

    output = io.BytesIO()
    img = img.convert('RGB')
    img.save(output, 'BMP')
    data = output.getvalue()[14:]
    output.close()

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()

    print(f'クリップボードに画面({size[0]}x{size[1]})を保存しました。')

# 参考
# https://jangle.tokyo/2020/07/07/post-2241/
# https://code.tiblab.net/python/pil/clipboard_send_image


