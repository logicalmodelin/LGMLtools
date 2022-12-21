import PIL
from PIL import Image
from pathlib import Path
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="画像の不透明部分をクロップします。")
    parser.add_argument('image', default="", type=str, help='不透明部分を切り出す入力画像')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--width', type=int, default=-1, help='最終的な横幅 縦幅と同時指定無効')
    group.add_argument('--height', type=int, default=-1, help='最終的な縦幅 横幅と同時指定無効')
    parser.add_argument('--output', type=str, default="", help='出力画像のパス')
    parser.version = '1.0.0'
    args = parser.parse_args()
    img = PIL.Image.open(args.image)
    img = img.crop(img.getbbox())
    if args.width > 0:
        img = img.resize((args.width, int(img.height * args.width / img.width)))
    elif args.height > 0:
        img = img.resize((int(img.width * args.height / img.height), args.height))
    if args.output:
        img.save(args.output)
    else:
        # img.save(Path(args.image).stem + '_crop' + Path(args.image).suffix)
        img.show()


if __name__ == '__main__':
    main()

