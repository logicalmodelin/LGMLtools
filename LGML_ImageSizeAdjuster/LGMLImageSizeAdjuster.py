import argparse
import json
import os
import sys
from pathlib import Path
from PIL import Image
from typing import List, Tuple, Any, Dict, ClassVar, Literal, Callable, Union


TARGET_FORMATS: Tuple[str] = ("png", "jpg", "gif", "bmp", "tga", "tif")


class PreferredDirections:

    WIDTH: str = "width"
    HEIGHT: str = "height"
    AUTO: str = "auto"
    AUTO_CLIP: str = "auto_clip"

    @classmethod
    def get_all(cls) -> List[str]:
        return [cls.WIDTH, cls.HEIGHT, cls.AUTO, cls.AUTO_CLIP]


class Resampling:

    name: str
    enum: int

    default_name: ClassVar[str] = "bilinear"
    instances: ClassVar[Dict[str, object]] = {}

    @classmethod
    def create(cls, name: str, enum: int):
        o: Resampling = Resampling(name, enum)
        cls.instances[name] = o
        return o

    @classmethod
    def get_all_names(cls) -> List[str]:
        return cls.instances.keys()

    @classmethod
    def get_resampling(cls, name: str) -> int:
        return cls.instances[name].enum

    def __init__(self, name: str, enum: int):
        self.name = name
        self.enum = enum


Resampling.create("nearest", Image.Resampling.NEAREST)
Resampling.create("box", Image.Resampling.BOX)
Resampling.create("bilinear", Image.Resampling.BILINEAR)
Resampling.create("hamming", Image.Resampling.HAMMING)
Resampling.create("bicubic", Image.Resampling.BICUBIC)
Resampling.create("lanczos", Image.Resampling.LANCZOS)


class ProcessInfo:
    source_file_name: str
    width: int
    height: int
    image: Image
    # output_path: Path
    # force: bool = False
    preferred_direction: str
    padding: bool
    padding_color: int
    scaling: bool
    source_pixel_ratio: float
    source_width: int
    source_height: int
    resampling: str

    def __init__(self, image: Image, file_name: str, resampling:str):
        self.image = image
        self.source_file_name = file_name
        self.source_width = image.width
        self.source_height = image.height
        self.source_pixel_ratio = image.width / image.height
        self.resampling = resampling

    # @property
    # def is_output_dir(self) -> bool:
    #     return self.output_path.is_dir()

    @property
    def ratio(self) -> float:
        return self.width / self.height


def _open_image(file_path: Path, extensions: List[str]) -> Image:
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


def _resize_by_width(info: ProcessInfo, nolog=True) -> Image:
    """
    横幅のサイズ優先でサイズ変更を行う
    """
    ratio: float = info.width / info.image.width
    size: Tuple = (info.image.width, info.image.height)
    resize: Tuple = (info.width, int(info.image.height * ratio))
    img: Image = info.image.resize(resize, Resampling.get_resampling(info.resampling))
    if not nolog:
        print("resize {}: {} -> {}".format(info.source_file_name, size, resize))
    return img


def _resize_by_height(info: ProcessInfo, nolog=True) -> Image:
    """
    縦幅のサイズ優先でサイズ変更を行う
    """
    ratio: float = info.height / info.image.height
    size: Tuple = (info.image.width, info.image.height)
    resize: Tuple = (int(info.image.width * ratio), info.height)
    img: Image = info.image.resize(resize, Resampling.get_resampling(info.resampling))
    if not nolog:
        print("resize {}: {} -> {}".format(info.source_file_name, size, resize))
    return img


def _resize_image(info: ProcessInfo) -> Image:
    pd: str = info.preferred_direction
    image: Image
    image_by_width: Image
    image_by_height: Image
    ratio_w: float
    ratio_h: float
    if pd != PreferredDirections.HEIGHT:
        image_by_width = _resize_by_width(info)
    if pd != PreferredDirections.WIDTH:
        image_by_height = _resize_by_height(info)

    if pd == PreferredDirections.WIDTH:
        return image_by_width
    if pd == PreferredDirections.HEIGHT:
        return image_by_height

    ratio_w: float = image_by_width.width / image_by_width.height
    ratio_h: float = image_by_height.width / image_by_height.height
    size_w: float = image_by_width.width * image_by_width.height
    size_h: float = image_by_height.width * image_by_height.height
    xx: int
    yy: int
    if pd == PreferredDirections.AUTO_CLIP:
        if size_w > size_h:
            image = image_by_width
        else:
            image = image_by_height
        xx = int((info.width - image.width) / 2)
        yy = int((info.height - image.height) / 2)
        image.crop((xx, yy, xx + info.width, info.height))
    elif pd == PreferredDirections.AUTO:
        if size_w > size_h:
            image = image_by_height
        else:
            image = image_by_width
        xx = int((info.width - image.width) / 2)
        yy = int((info.height - image.height) / 2)
        if info.padding_color and image.width * image.height < info.width * info.height:
            new_image: Image = Image.new(mode="RGBA", size=(info.width, image.height), color=info.padding_color)
            new_image.paste(image, (xx, yy))
            image = new_image
    return image


def process_args(args: Any) -> None:

    other_formats: List[str] = []
    if args.search_other_format:
        other_formats = args.other_formats
    image_file_path: Path = Path(args.image_file)
    output_path: Path
    if not args.output:
        output_path = Path(image_file_path)
    else:
        output_path = Path(args.output)
    image_file_infos: List[ProcessInfo] = []
    filename_with_input_params: bool = args.dev__filename_with_input_params
    force: bool = args.force

    is_target_dir: bool = image_file_path.is_dir()
    is_output_dir: bool = output_path.is_dir()
    if is_target_dir and not is_output_dir:
        print("読み込み対象がディレクトリの場合は出力先もディレクトリにする必要があります。", file=sys.stderr)
        sys.exit(1)

    # 処理対象のImage一覧を作る
    image: Image
    if is_target_dir:
        # もし読み込み指定がディレクトリなら画像ぽい物を探す
        for f in os.listdir(image_file_path):
            ext: str = os.path.splitext(f)
            if not ext:
                continue
            if ext[1:] not in TARGET_FORMATS:
                continue
            image = _open_image(image_file_path, other_formats)
            if image:
                image_file_infos.append(ProcessInfo(image, image_file_path.name, args.resampling))
    else:
        image = _open_image(image_file_path, other_formats)
        if image:
            image_file_infos.append(ProcessInfo(image, image_file_path.name, args.resampling))

    if len(image_file_infos) == 0:
        print("no image input: {}{}".format(
                image_file_path.as_posix(),
                " ({})".format(" | ".join(other_formats)) if len(other_formats) > 0 else ""
            ),
            file=sys.stderr)
        sys.exit(1)

    for info in image_file_infos:
        info.width = args.width
        info.height = args.height
        info.image = image
        info.preferred_direction = args.preferred_direction
        info.padding = args.padding
        info.padding_color = int('0x' + args.padding_color, 16)
        info.scaling = args.scaling

        image = _resize_image(info)
        output_file_path: Path
        if is_output_dir:
            output_base_name: str = os.path.splitext(info.source_file_name)[0]
            if filename_with_input_params:
                output_base_name += "_"
                output_base_name += "_{}x{}".format(image.width, image.height)
                if args.preferred_direction:
                    output_base_name += "_{}".format(args.preferred_direction)
                if args.scaling:
                    output_base_name += "_scaling"
                if args.padding:
                    output_base_name += "_padding"
                if force:
                    output_base_name += "_force"
                # if info.resampling != Resampling.default_name:
                output_base_name += "_{}".format(info.resampling)
                output_base_name += os.path.splitext(info.source_file_name)[1]
            else:
                output_base_name = info.source_file_name
            output_file_path = output_path / Path(output_base_name)
        else:
            output_file_path = output_path
        if output_file_path.exists() and not args.force and not args.dev__result_as_json:
            r: str = input("上書き確認 y/n")
            if r.lower() != "y":
                continue
        if args.dev__result_as_json:
            o: dict = {
                "result": {
                    "output_file_path": output_file_path.as_posix(),
                    "width": image.width,
                    "height": image.height,
                    "pixel_ratio": image.width / image.height,
                },
                "params": {
                    "preferred_direction": info.preferred_direction,
                    "padding": info.padding,
                    "padding_color": hex(info.padding_color),
                    "scaling": info.scaling,
                    "filename_with_input_params": filename_with_input_params,
                },
                "source": {
                    "file_name": info.source_file_name,
                    "width": info.source_width,
                    "height": info.source_height,
                    "pixel_ratio": info.source_pixel_ratio,
                },
            }
            json_str: str = json.dumps(o, allow_nan=True)
            print(json_str, file=sys.stdout)
        else:
            print(output_file_path)  # TODO 書き出し
        if not args.dev__no_image_output:
            image.save(output_file_path)


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description='画像のサイズを適切に調整する。'
                    'jpgとpngなどフォーマットの違いを修正する。'
                    'ディレクトリを指定するとその中のすべてのファイルを処理対象にする。',
    )
    parser.add_argument("image_file", type=str, help="処理対象となる画像ファイルのパス。")
    parser.add_argument("width", type=int, help="出力画像の横幅。")
    parser.add_argument("height", type=int, help="出力画像の高さ。")
    parser.add_argument("-o", "--output", type=str, default="",
                        help="アウトプットファイルパス。指定ない場合入力と同じ場所に同名で上書きされる。")
    parser.add_argument("-f", "--force", action="store_true",
                        help="処理結果ファイル保存時に同名ファイルが存在していても確認をしない場合に指定。")
    parser.add_argument(
        "-prdir", "--preferred_direction", default="height",
        choices=PreferredDirections.get_all(),
        help="\n".join([
            "リサイズ後に縦横比が合わない場合の優先方向指定。", 
            "auto指定の場合はクリップしないですむ方向(全部の画像エリアを保持)を優先。",
            "auto_clip指定の場合はクリップが発生する方向を優先(できるかぎり大きく)。",
            "実際にクリップ・パディングするしないは別オプションで指定する。"
        ])
    )
    parser.add_argument(
        "-rs", "--resampling", default=Resampling.default_name,
        choices=Resampling.get_all_names(),
        help="リサイズ時のピクセル補完方法。",
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
    parser.add_argument(
        "--dev__result_as_json", action="store_true",
        help="開発用コマンド、jsonデータで処理の概要を標準出力する。")
    parser.add_argument(
        "--dev__no_image_output", action="store_true",
        help="開発用コマンド、画像を出力しない。dev__result_as_jsonと合わせて使う想定。")
    parser.add_argument(
        "--dev__filename_with_input_params", action="store_true",
        help="開発用コマンド、出力ファイル名にパラメータ値を含める。")
    parser.add_argument("-V", '--version', action='version', version='%(prog)s 1.0')
    args: argparse.Namespace = parser.parse_args()
    process_args(args)


if __name__ == "__main__":
    main()

"""
画像のサイズを適切に調整する。。jpgとpngなどフォーマットの違いを修正する。ディレクトリを指定するとその中のすべてのファイルを処理対象にする。

positional arguments:
  image_file            処理対象となる画像ファイルのパス。
  width                 出力画像の横幅。
  height                出力画像の高さ。

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        アウトプットファイルパス。指定ない場合入力と同じ場所に同名で上書きされる。
  -f, --force           処理結果ファイル保存時に同名ファイルが存在していても確認をしない場合に指定。
  -prdir {width,height,auto,auto_clip}, --preferred_direction {width,height,auto,auto_clip}
                        リサイズ後に縦横比が合わない場合の優先方向指定。 auto指定の場合はクリップしないですむ方向(全部の画像エリアを保持)を優先。 auto_clip指定の場合はクリップが発生する方向を優先(できるかぎり大きく)。 実際にクリップ・パディングするしないは別オプショ 
ンで指定する。
  --padding             パディング(余白埋め)を許可する場合に指定。
  --padding_color PADDING_COLOR
                        パディング色をRGBA値16進数8桁で指定。透明度は出力フォーマットがjpgの場合無視される。
  --scaling             サイズがあわない場合にスケーリングをしたい場合に指定。padding指定がある場合はpaddingを優先。
  -sofmt, --search_other_format
                        指定ファイルパスの画像が見つからない際に、別のフォーマットを入力に採用する。
  -ofmt [OTHER_FORMATS ...], --other_formats [OTHER_FORMATS ...]
                        異なるファイルフォーマットのファイル名を自動検索する場合の優先度。入力がディレクトリの場合は無効。
  --dev__result_as_json      開発用コマンド、実際に画像を出力せずjsonデータで概要を標準出力する。
  -V, --version         show program's version number and exit
"""