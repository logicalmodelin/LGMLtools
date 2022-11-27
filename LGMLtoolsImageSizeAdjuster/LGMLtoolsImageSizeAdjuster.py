import argparse
import codecs
import datetime
import os
import sys
from pathlib import Path
from PIL import Image
import shutil
from typing import List, Any, ClassVar, Literal, Callable, Union
# https://future-architect.github.io/articles/20201223/



def _open_image(filepath:Path, extentions:List[str]) -> Image or None:
    """画像ファイルを開く。対象ファイルがなかったら同じファイル名で拡張子だけ違うものを探して開く。

    Args:
        filepath (Path): 画像のファイルパス
        extentions (List[str]): 拡張子の羅列。"." は含まずに指定する。 ex) ["jpg", "png"]

    Returns:
        Image: 画像が見つかった場合はImage、そうでなければ None
    """
    extentions = extentions[:]
    ext = filepath.suffix[1:]
    if ext not in extentions:
        extentions.insert(0, ext)

    for ext in extentions:
        f = Path("{}/{}.{}".format(filepath.parent.as_posix(), filepath.stem, ext))
        if not f.exists():
            continue
        try:
            img = Image.open(f)
            if img is not None:
                img = img.convert("RGBA")
                return img
        except Exception as ex:
            print(ex)
            pass
    return None


def _resize_by_width(file:Path, img:Image, w:int) -> Image:
    """横幅のサイズ優先でサイズ変更を行う

    Args:
        file (Path): _description_
        img (Image): _description_
        w (int): _description_

    Returns:
        Image: _description_
    """
    ratio = w / img.width
    size = (img.width, img.height)
    resize = (w, int(img.height * ratio))
    print("resize {}: {} -> {}".format(file.name, size, resize))
    img = img.resize(resize, Image.Resampling.NEAREST)
    return img


def _resize_by_height(file:Path, img:Image, h:int) -> Image:
    ratio = h / img.height
    size = (img.width, img.height)
    resize = (int(img.width * ratio), h)
    print("resize {}: {} -> {}".format(file.name, size, resize))
    img = img.resize(resize, Image.Resampling.NEAREST)
    return img


def main():

    parser = argparse.ArgumentParser(
        prog='lgmd_resize_image.py',
        usage='画像のサイズを適切に調整する。',
        description='画像の縦横サイズを指定のサイズに変更する。jpgとpngなどフォーマットの違いを調整する。',
    )
    parser.add_argument("imagefile", type=str, help="処理対象となる画像ファイルのパス。")
    parser.add_argument("width", type=int, help="出力画像の横幅。")
    parser.add_argument("height", type=int, help="出力画像の高さ。")
    parser.add_argument("-o", "--output", type=str, default="",
        help="アウトプットファイルパス。指定ない場合入力と同じ場所に同名で上書きされる。")
    parser.add_argument("-f", "--force", action="store_true",
        help="処理結果ファイル保存時に同盟ファイルが存在していても確認をしない場合に指定。")
    parser.add_argument("-pdir", "--preferred_direction", default="height",
        choices=["width", "height", "auto", "auto_clip"],
        help="\n".join([
            "リサイズ後に縦横比が合わない場合の優先方向指定。", 
            "auto指定の場合はクリップしないですむ方向(全部の画像エリアを保持)を優先。",
            "auto_clip指定の場合はクリップが発生する方向を優先(できるかぎり大きく)。",
            "実際にクリップ・パディングするしないは別オプションで指定する。"
        ])
    )
    parser.add_argument("--padding", action="store_true",
        help="パディング(余白埋め)を許可する場合に指定。")
    parser.add_argument("--padding_color", type=str, default="111111",
        help="パディング色をRGBA値16進数8桁で指定。透明度は出力フォーマットがjpgの場合無視される。")
    parser.add_argument("--scaling", action="store_true",
        help="サイズがあわない場合にスケーリングをしたい場合に指定。padding指定がある場合はpaddingを優先。")
    parser.add_argument("-sofmt", "--search_other_format", action="store_true",
        help="指定ファイルパスの画像が見つからない際に、別のフォーマットを入力に採用する。")
    parser.add_argument("-ofmt", "--other_formats", nargs="*", type=str, default=["png", "jpg"],
        help="自動検索する他のフォーマット拡張子。")
    args = parser.parse_args()

    imagefile = Path(args.imagefile)
    other_formats = []
    if args.search_other_format:
        other_formats = args.other_formats
    image = _open_image(imagefile, other_formats)
    if image is None:
        print("no image input: {}{}".format(
                imagefile.as_posix(),
                " ({})".format(" | ".join(other_formats)) if len(other_formats) > 0 else ""
            ),
            file=sys.stderr)
        sys.exit(1)
    print(image)

if __name__ == "__main__":
    main()

