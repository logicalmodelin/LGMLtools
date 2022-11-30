import argparse
import os
import sys
from pathlib import Path
from PIL import Image
from typing import List, Tuple, Any, ClassVar, Literal, Callable, Union


TARGET_FORMATS: Tuple[str] = ("png", "jpg", "gif", "bmp", "tga", "tif")


def _open_image(file_path: Path, extensions: List[str]) -> Union[Image, None]:
    """
    画像ファイルを開く。対象ファイルがなかったら同じファイル名で拡張子だけ違うものを探して開く。
    Args:
        file_path (Path): 画像のファイルパス
        extensions (List[str]): 拡張子の羅列。"." は含まずに指定する。 ex) ["jpg", "png"]
    Returns:
        Image: 画像が見つかった場合はImage、そうでなければ None
    """
    ext: str = file_path.suffix[1:]
    extensions_: List[str] = [ext]
    for ext in extensions:
        if ext not in extensions_:
            extensions_.append(ext)

    for ext in extensions_:
        f = Path("{}/{}.{}".format(file_path.parent.as_posix(), file_path.stem, ext))
        if not f.exists():
            continue
        try:
            img: Image = Image.open(f)
            if img is not None:
                img = img.convert("RGBA")
                return img
        except Exception as ex:
            print(ex)
            pass
    return None


def _resize_by_width(file: Path, img: Image, w: int) -> Image:
    """
    横幅のサイズ優先でサイズ変更を行う
    """
    ratio: float = w / img.width
    size: Tuple = (img.width, img.height)
    resize: Tuple = (w, int(img.height * ratio))
    print("resize {}: {} -> {}".format(file.name, size, resize))
    img: Image = img.resize(resize, Image.Resampling.NEAREST)
    return img


def _resize_by_height(file: Path, img: Image, h: int) -> Image:
    ratio: float = h / img.height
    size: Tuple = (img.width, img.height)
    resize: Tuple = (int(img.width * ratio), h)
    print("resize {}: {} -> {}".format(file.name, size, resize))
    img: Image = img.resize(resize, Image.Resampling.NEAREST)
    return img


def main():
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        usage='画像のサイズを適切に調整する。',
        description='画像の縦横サイズを指定のサイズに変更する。'
                    'jpgとpngなどフォーマットの違いを調整する。'
                    'ディレクトリを指定するとその中のすべてのファイルを処理対象にする。',
    )
    parser.add_argument("image_file", type=str, help="処理対象となる画像ファイルのパス。")
    parser.add_argument("width", type=int, help="出力画像の横幅。")
    parser.add_argument("height", type=int, help="出力画像の高さ。")
    parser.add_argument("-o", "--output", type=str, default="",
                        help="アウトプットファイルパス。指定ない場合入力と同じ場所に同名で上書きされる。")
    parser.add_argument("-f", "--force", action="store_true",
                        help="処理結果ファイル保存時に同盟ファイルが存在していても確認をしない場合に指定。")
    parser.add_argument(
        "-prdir", "--preferred_direction", default="height",
        choices=["width", "height", "auto", "auto_clip"],
        help="\n".join([
            "リサイズ後に縦横比が合わない場合の優先方向指定。", 
            "auto指定の場合はクリップしないですむ方向(全部の画像エリアを保持)を優先。",
            "auto_clip指定の場合はクリップが発生する方向を優先(できるかぎり大きく)。",
            "実際にクリップ・パディングするしないは別オプションで指定する。"
        ])
    )
    parser.add_argument(
        "--padding", action="store_true",
        help="パディング(余白埋め)を許可する場合に指定。")
    parser.add_argument(
        "--padding_color", type=str, default="111111",
        help="パディング色をRGBA値16進数8桁で指定。透明度は出力フォーマットがjpgの場合無視される。")
    parser.add_argument(
        "--scaling", action="store_true",
        help="サイズがあわない場合にスケーリングをしたい場合に指定。padding指定がある場合はpaddingを優先。")
    parser.add_argument(
        "-sofmt", "--search_other_format", action="store_true",
        help="指定ファイルパスの画像が見つからない際に、別のフォーマットを入力に採用する。")
    parser.add_argument(
        "-ofmt", "--other_formats", nargs="*", type=str, default=TARGET_FORMATS,
        help="異なるファイルフォーマットのファイル名を自動検索する場合の優先度。"
             "入力がディレクトリの場合は無効。")
    args: argparse.Namespace = parser.parse_args()

    other_formats: List[str] = []
    if args.search_other_format:
        other_formats = args.other_formats
    image_file_path: Path = Path(args.image_file)
    output_path: Path
    if not args.output:
        output_path = Path(image_file_path)
    else:
        output_path = Path(args.output)
    image_files: List[Image] = []

    is_target_dir: bool = image_file_path.is_dir()
    is_output_dir: bool = output_path.is_dir()
    if is_target_dir and not is_output_dir:
        print("読み込み対象がディレクトリの場合は出力先もディレクトリにする必要があります。", file=sys.stderr)
        sys.exit(1)

    # 処理対象のImage一覧を作る
    if is_target_dir:
        # もし読み込み指定がディレクトリなら画像ぽい物を探す
        for f in os.listdir(image_file_path):
            ext: str = os.path.splitext(f)
            if not ext:
                continue
            if ext[1:] not in TARGET_FORMATS:
                continue
            image_files.append(_open_image(image_file_path, other_formats))
    else:
        image_files.append(_open_image(image_file_path, other_formats))
    image: Image
    image_files = [image for image in image_files if image is not None]

    if len(image_files) == 0:
        print("no image input: {}{}".format(
                image_file_path.as_posix(),
                " ({})".format(" | ".join(other_formats)) if len(other_formats) > 0 else ""
            ),
            file=sys.stderr)
        sys.exit(1)

    for image in image_files:
        pass


if __name__ == "__main__":
    main()

