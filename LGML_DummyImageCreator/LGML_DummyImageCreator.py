import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import argparse
from typing import List, Tuple, Any, ClassVar, Literal, Callable, Union


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        usage='ダミー画像を生成する。',
        description='適当な数とサイズでダミー画像を作ります。',
    )
    parser.add_argument("output_path", type=str, help="画像をアウトプットするフォルダ")
    parser.add_argument("width", type=int, help="出力画像の横幅")
    parser.add_argument("height", type=int, help="出力画像の高さ")
    parser.add_argument("-n", "--number_of_image", type=int, default=1, help="出力画像数")
    parser.add_argument("-p", "--prefix", default="img_", type=str, help="出力画像名の接頭語")
    parser.add_argument("-s", "--suffix", default="", type=str, help="出力画像名の接尾語")
    parser.add_argument("-fmt", "--format", default="png", help="エクスポート画像フォーマットの指定")
    parser.add_argument("-c", "--color", type=str, default="eeeeee", help="色の指定(16進数6文字)")
    parser.add_argument("-t", "--title", type=str, default="[DUMMY IMAGE]\n{w}x{h}",
                        help="画像に埋め込むタイトル文字 英語のみ {w}は横幅に{h}は縦幅に変換される")
    parser.add_argument("--text_contents", type=str, default="", help="画像右下に埋め込む本文文字 英語のみ")
    parser.add_argument("--force", action="store_true", help="上書き確認せずファイルを書き出すか")
    # デフォルトビットマップフォントがかっこいいが、サイズ指定できない
    # parser.add_argument("-fs", "--font_size", type=int, default=24, help="タイトル文字の大きさ")

    args = parser.parse_args()
    output_path: Path = Path(args.output_path)
    if output_path.is_file():
        output_path = output_path.parent
    if not output_path.exists():
        output_path.mkdir()
    small_size: Tuple[int, int] = (int(args.width / 3), int(args.height / 3))
    size: Tuple[int, int] = (args.width, args.height)
    filename_template: str = args.prefix + "{}x{}" + args.suffix + "{}." + args.format
    color_str: str = args.color
    if color_str.startswith("0x"):
        color_str = color_str[2:]
    if len(color_str) != 6:
        print("カラーはRRGGBB形式の16進数6文字(例 ffeeee)で指定してください。", file=sys.stderr)
        sys.exit(1)
    color: tuple[int, int, int] = \
        (int(color_str[4:6], base=16), int(color_str[2:4], base=16), int(color_str[0:2], base=16))  # BGR -> RGB
    text_color: tuple[int, int, int] = (255 - color[0], 255 - color[1], 255 - color[2])  # 補色
    line_color: tuple[int, int, int] = text_color
    font: ImageFont = ImageFont.load_default()
    # font = ImageFont.truetype("arial.ttf", args.font_size)

    # print(filename_template)
    # print(color, text_color)

    index: int
    for index in range(args.number_of_image):
        image: Image = Image.new("RGB", small_size, color)
        draw = ImageDraw.Draw(image)
        xx: int = small_size[0] - 2 - 1
        yy: int = small_size[1] - 2 - 1
        draw.rectangle((2, 2, xx, yy), outline=text_color, width=1)
        # draw.line(((2, 2), (xx, yy)), fill=line_color)
        draw.line(((2, yy), (xx, 2)), fill=line_color)
        title: str = args.title.replace("{w}", str(size[0])).replace("{h}", str(size[1])).replace("\\n", "\n")
        draw.text(
            (6, 6), "{}".format(title, size[0], size[1]),
            text_color, spacing=3, align='left', font=font
        )
        text_contents: str = args.text_contents
        # print(text_contents)
        text_contents_size = font.getbbox(text_contents)
        # print(text_contents_size)
        draw.text(
            (small_size[0] - text_contents_size[2] - 6, small_size[1] - text_contents_size[3] - 6),
            text_contents, text_color
        )
        # 小さく作って拡大している 文字の見栄えの調整
        image = image.resize(size, resample=Image.Resampling.NEAREST)
        index_str: str = "#{}".format(index) if args.number_of_image > 1 else ""
        output: Path = output_path / Path(filename_template.format(size[0], size[1], index_str))
        if output.exists() and not args.force:
            res: str = input("{}はすでに存在します。処理を進める場合 Y と入力して下さい。".format(output.name))
            if res != "Y":
                print("処理を中止しました。")
                sys.exit(0)
        print(output)
        image.save(output)


if __name__ == "__main__":
    main()
