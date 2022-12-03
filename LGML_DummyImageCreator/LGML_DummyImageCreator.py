import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import argparse
from typing import List, Tuple, Any, ClassVar, Literal, Callable, Union


def _replace_text(text: str, size: tuple[int, int], index: str) -> str:
    return text.replace(
        "{w}", str(size[0])).replace(
        "{h}", str(size[1])).replace(
        "{i}", index).replace(
        "\\n", "\n")


def _get_text_size(text: str, font: ImageFont, spacing : int = 2) -> Tuple[int, int]:
    contents_width: int = 0
    s: str
    for s in text.split("\n"):
        contents_width = max(contents_width, font.getbbox(s)[2])
    contents_height: int = font.getbbox(text)[3]
    contents_height *= (text.count("\n") + 1)
    contents_height += spacing * text.count("\n")
    return contents_width, contents_height


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description='指定された枚数とサイズでダミー画像を生成します。 '
                    'テキスト系の指定は英語のみで、{i}は連番番号に{w}は横幅に{h}は縦幅に変換されます。\nで改行指定も可能です。',
    )
    parser.add_argument("output_path", type=str, help="画像をアウトプットするフォルダ")
    parser.add_argument("width", type=int, help="出力画像の横幅")
    parser.add_argument("height", type=int, help="出力画像の高さ")
    parser.add_argument("-n", "--number_of_image", type=int, default=1, help="出力画像数")
    parser.add_argument("-p", "--prefix", default="img_", type=str, help="出力画像名の接頭語")
    parser.add_argument("-s", "--suffix", default="", type=str, help="出力画像名の接尾語")
    parser.add_argument("-fmt", "--format", default="png", help="エクスポート画像フォーマットの指定")
    parser.add_argument("-c", "--color", type=str, default="eeeeee", help="色の指定(16進数6文字)")
    parser.add_argument("-tc", "--text_color", type=str, default="",
                        help="文字色の指定(16進数6文字) 指定ない場合背景色の補色")
    parser.add_argument("-t", "--title", type=str, default="[DUMMY IMAGE]\n{w}x{h}",
                        help="画像に埋め込むタイトル文字")
    parser.add_argument("-zp", "--zero_padding", type=int, default=3, help="画像INDEX番号を0でうめる桁数。")
    parser.add_argument("--center_text", type=str, default="{i}", help="画像中央に埋め込む文字")
    parser.add_argument("--bottom_contents", type=str, default="", help="画像右下に埋め込む文字")
    parser.add_argument("--force", action="store_true", help="上書き確認せずファイルを書き出すか")
    # デフォルトビットマップフォントがかっこいいが、サイズ指定できない
    # parser.add_argument("-fs", "--font_size", type=int, default=24, help="タイトル文字の大きさ")
    parser.add_argument("-V", '--version', action='version', version='%(prog)s 1.1')

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
    if len(color_str) != 6:
        print("カラーはRRGGBB形式の16進数6文字(例 ffeeee)で指定してください。", file=sys.stderr)
        sys.exit(1)
    color: tuple[int, int, int] = \
        (int(color_str[0:2], base=16), int(color_str[2:4], base=16), int(color_str[4:6], base=16))
    text_color_str: str = args.text_color
    if len(text_color_str) != 6 and len(text_color_str) != 0:
        print("textカラーはRRGGBB形式の16進数6文字(例 ffeeee)で指定してください。", file=sys.stderr)
        sys.exit(1)
    text_color: tuple[int, int, int]
    if text_color_str == "":
        text_color = (255 - color[0], 255 - color[1], 255 - color[2])  # 補色
    else:
        text_color = \
            (int(text_color_str[0:2], base=16), int(text_color_str[2:4], base=16), int(text_color_str[4:6], base=16))
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
        # line_color: tuple[int, int, int] = text_color
        # draw.line(((2, 2), (xx, yy)), fill=line_color)  # ななめ線
        # draw.line(((2, yy), (xx, 2)), fill=line_color)  # ななめ線
        index_with_zero_pad = str(index).zfill(args.zero_padding)
        # 左上のタイトル文字
        title: str = _replace_text(args.title, size, index_with_zero_pad)
        draw.text(
            (6, 6), "{}".format(title, size[0], size[1]),
            text_color, spacing=2, align='left', font=font
        )
        # 右下の文字
        bottom_contents: str = _replace_text(args.bottom_contents, size, index_with_zero_pad)
        bottom_contents_size = _get_text_size(bottom_contents, font, spacing=2)
        draw.text(
            (small_size[0] - bottom_contents_size[0] - 6, small_size[1] - bottom_contents_size[1] - 6),
            bottom_contents, text_color, spacing=2, align='right'
        )
        # 中央の文字
        center_text: str = _replace_text(args.center_text, size, index_with_zero_pad)
        center_text_size = _get_text_size(center_text, font, spacing=2)
        draw.text(
            (small_size[0] / 2 - center_text_size[0] / 2, small_size[1] / 2 - center_text_size[1] / 2),
            center_text, text_color, spacing=2, align='center', font=font
        )
        # 小さく作って拡大している 文字の見栄えの調整
        image = image.resize(size, resample=Image.Resampling.NEAREST)
        index_str: str = "#{}".format(index_with_zero_pad) if args.number_of_image > 1 else ""
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
