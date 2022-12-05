import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from PIL import Image
from typing import List, Tuple, Any, Dict, ClassVar, Literal, Callable, Union
from enum import Enum, auto
# from strenum import StrEnum


TARGET_FORMATS: Tuple[str] = ("png", "jpg", "gif", "bmp", "tif", "tga")  # StrEnumにする？


class PreferredDirections(Enum):

    WIDTH = auto()
    HEIGHT = auto()
    AUTO_PAD = auto()
    AUTO_CROP = auto()

    @classmethod
    def get_all(cls) -> List[str]:
        arr: List[str] = []
        for i in PreferredDirections:
            arr.append(i.name)
        return arr


class Resampling(Enum):

    NEAREST = auto()
    BOX = auto()
    BILINEAR = auto()
    HAMMING = auto()
    BICUBIC = auto()
    LANCZOS = auto()
    # see Image.Resampling

    @classmethod
    def default_name(cls) -> str:
        return cls.BILINEAR.name

    @classmethod
    def get_all_names(cls) -> List[str]:
        arr: List[str] = []
        for i in Resampling:
            arr.append(i.name)
        return arr

    @classmethod
    def get_resampling(cls, resampling: object) -> Image.Resampling:
        if resampling is Resampling.NEAREST:
            return Image.Resampling.NEAREST
        if resampling is Resampling.BOX:
            return Image.Resampling.BOX
        if resampling is Resampling.BILINEAR:
            return Image.Resampling.BILINEAR
        if resampling is Resampling.HAMMING:
            return Image.Resampling.HAMMING
        if resampling is Resampling.BICUBIC:
            return Image.Resampling.BICUBIC
        if resampling is Resampling.LANCZOS:
            return Image.Resampling.LANCZOS
        assert False
        return None


class Processed(Enum):
    """
    処理内容を表す列挙型
    """
    RESIZE_ONLY = auto()
    SCALE = auto()
    CROP = auto()
    PAD = auto()


class ProcessInfo:
    source_file_name: str
    width: int
    height: int
    image: Image.Image
    # output_path: Path
    # force: bool = False
    preferred_direction: PreferredDirections
    padding_color: int
    scaling_instead_of_padding: bool
    scaling_instead_of_cropping: bool
    resampling: Resampling
    source_pixel_ratio: float
    source_width: int
    source_height: int
    processed: Processed
    output_path: Path
    _log: List[str]

    def __init__(self, image: Image.Image, file_name: str, resampling: Resampling, output_path: Path):
        self.image = image
        self.source_file_name = file_name
        self.source_width = image.width
        self.source_height = image.height
        self.source_pixel_ratio = image.width / image.height
        self.resampling = resampling
        self.output_path = output_path
        self.processed = Processed.RESIZE_ONLY
        self._log = []

    # @property
    # def is_output_dir(self) -> bool:
    #     return self.output_path.is_dir()

    @property
    def ratio(self) -> float:
        return self.width / self.height

    @property
    def file_format(self) -> str:
        return os.path.splitext(self.self.source_file_name)[1]

    def add_log(self, s: str) -> None:
        # 自動テストの関係で、とりあえず日本語は渡さないようにする
        self._log.append(s)

    def get_log(self) -> str:
        return "/".join(self._log)


def _open_image(file_path: Path, extensions: List[str]) -> Tuple[Union[Image.Image, None], Union[Path, None]]:
    """
    画像ファイルを開く。対象ファイルがなかったら同じファイル名で拡張子だけ違うものを探して開く。
    Args:
        file_path (Path): 画像のファイルパス
        extensions (List[str]): 拡張子の羅列。"." は含まずに指定する。 ex) ["jpg", "png"]
    Returns:
        Image: 画像が見つかった場合はImage、そうでなければ None / 実際に開いたファイルパス
    """
    ext: str = file_path.suffix[1:]
    extensions_: List[str] = [ext]
    for ext in extensions:
        if ext not in extensions_:
            extensions_.append(ext)

    for ext in extensions_:
        f = Path("{}/{}.{}".format(file_path.parent.as_posix(), file_path.stem, ext))
        if not f.exists():
            # print("not found! {}".format(f))
            continue
        try:
            img: Image.Image = Image.open(f)
            if img is not None:
                img = img.convert("RGBA")
                # print("found {} {}".format(img, f))
                return img, f
        except Exception as ex:
            print(ex)
            pass
    return None, None


def _resize_by_width(info: ProcessInfo, nolog=True) -> Image.Image:
    """
    横幅のサイズ優先でサイズ変更を行う
    """
    ratio: float = info.width / info.image.width
    size: Tuple = (info.image.width, info.image.height)
    resize: Tuple = (info.width, int(info.image.height * ratio))
    img: Image.Image = info.image.resize(resize, Resampling.get_resampling(info.resampling))
    if not nolog:
        print("resize {}: {} -> {}".format(info.source_file_name, size, resize))
    return img


def _resize_by_height(info: ProcessInfo, nolog=True) -> Image.Image:
    """
    縦幅のサイズ優先でサイズ変更を行う
    """
    ratio: float = info.height / info.image.height
    size: Tuple = (info.image.width, info.image.height)
    resize: Tuple = (int(info.image.width * ratio), info.height)
    img: Image.Image = info.image.resize(resize, Resampling.get_resampling(info.resampling))
    if not nolog:
        print("resize {}: {} -> {}".format(info.source_file_name, size, resize))
    return img


def _clip_or_scale_or_padding(image: Image.Image, info: ProcessInfo):
    dw: int = image.width - info.width
    dh: int = image.height - info.height
    assert dw == 0 or dh == 0  # 事前処理でどちらかは揃えてある
    info_area: int = info.width * info.height
    image_area: int = image.width * image.height
    da: int = image_area - info_area
    if da < 0:
        if info.scaling_instead_of_padding:
            image = info.image.resize((info.width, info.height), Resampling.get_resampling(info.resampling))
            info.processed = Processed.SCALE
            info.add_log("scaled(instead of pad)")
        else:
            # パディング 処理
            new_image: Image.Image = Image.new(
                mode="RGBA", size=(info.width, info.height), color=info.padding_color
            )
            # info.padding_color はとりあえず透明度ありで処理してよい jpg保存時などに自動で破棄される
            info.add_log("padded ({},{} -> {},{})".format(image.width, image.height, info.width, info.height))
            new_image.paste(image, (-int(dw / 2), -int(dh / 2)))
            image = new_image
            info.processed = Processed.PAD
    elif da > 0:
        if info.scaling_instead_of_cropping:
            image = info.image.resize((info.width, info.height), Resampling.get_resampling(info.resampling))
            info.processed = Processed.SCALE
            info.add_log("scaled(instead of rop)")
        else:
            # クリッピング 処理
            cropped: bool = False
            if dw > 0:
                info.add_log("cropped ({},{} -> {},{})".format(image.width, image.height, info.width, info.height))
                image = image.crop((dw / 2, 0, dw / 2 + info.width, info.height))
                cropped = True
            if dh > 0:
                info.add_log("cropped ({},{} -> {},{})".format(image.width, image.height, info.width, info.height))
                image = image.crop((0, dh / 2, info.width, dh / 2 + info.height))
                cropped = True
            if cropped:
                info.processed = Processed.CROP
    return image


def _resize_image(info: ProcessInfo) -> Image:
    pd: PreferredDirections = info.preferred_direction
    image: Image.Image = None
    image_by_width: Image.Image = None
    image_by_height: Image.Image = None
    ratio_w: float
    ratio_h: float
    if pd != PreferredDirections.HEIGHT:
        image_by_width = _resize_by_width(info)
    if pd != PreferredDirections.WIDTH:
        image_by_height = _resize_by_height(info)

    if pd == PreferredDirections.WIDTH:
        info.add_log("[dir width]")
        return _clip_or_scale_or_padding(image_by_width, info)
    if pd == PreferredDirections.HEIGHT:
        info.add_log("[dir height]")
        return _clip_or_scale_or_padding(image_by_height, info)

    # ratio_w: float = image_by_width.width / image_by_width.height
    # ratio_h: float = image_by_height.width / image_by_height.height
    size_w: float = image_by_width.width * image_by_width.height
    size_h: float = image_by_height.width * image_by_height.height
    xx: int
    yy: int
    if pd == PreferredDirections.AUTO_CROP:
        if size_w > size_h:
            info.add_log("[dir auto crop width]")
            image = image_by_width
        else:
            info.add_log("[dir auto crop height]")
            image = image_by_height
        return _clip_or_scale_or_padding(image, info)
    else:
        if size_w > size_h:
            info.add_log("[dir auto height]")
            image = image_by_height
        else:
            info.add_log("[dir auto width]")
            image = image_by_width
        return _clip_or_scale_or_padding(image, info)


def _modify_output_path(input_path: str, output_path: str, w: int, h: int, index: int) -> Path:
    """
    出力ファイル名の変数展開
    """
    output_path = output_path.replace("{n}", os.path.splitext(
        os.path.basename(input_path))[0]).replace("{w}", str(w)).replace("{h}", str(h)).replace("{i}", str(index))
    return Path(output_path)


def _create_process_info(args: Any) -> List[ProcessInfo]:
    padding_color_str: str = args.padding_color
    if len(padding_color_str) == 8:
        padding_color_str = padding_color_str
    elif len(padding_color_str) == 6:
        padding_color_str = "ff" + padding_color_str
    else:
        print("カラー値は16進数6文字または8文字で指定してください。: {}".format(padding_color_str), file=sys.stderr)
        sys.exit(1)
    # ABGR -> ARGB
    padding_color_str = \
        padding_color_str[0:2] + padding_color_str[6:8] + padding_color_str[4:6] + padding_color_str[2:4]
    padding_color: int = int('0x' + padding_color_str, 16)

    assert (len(padding_color_str) == 6 or len(padding_color_str) == 8)
    other_formats: List[str] = []
    if args.search_other_format:
        other_formats = args.other_formats
    image_file_infos: List[ProcessInfo] = []

    for image_file_index, image_file in enumerate(args.image_files):
        image_file_path: Path = Path(image_file)
        output_path: Path
        if not args.output:
            output_path = image_file_path
        else:
            output_path = _modify_output_path(image_file, args.output, args.width, args.height, image_file_index)

        is_target_dir: bool = image_file_path.is_dir()
        is_output_dir: bool = output_path.is_dir()
        if is_target_dir and not is_output_dir:
            # TODO 名前にINDEX番号が入れば可能？
            print("読み込み対象がディレクトリの場合は出力先もディレクトリにする必要があります。", file=sys.stderr)
            sys.exit(1)

        # 処理対象のImage一覧を作る
        image: Image.Image
        if is_target_dir:
            # もし読み込み指定がディレクトリなら画像ぽい物を探す
            for f in os.listdir(image_file_path):
                ext: str = os.path.splitext(f)
                if not ext:
                    continue
                if ext[1:] not in TARGET_FORMATS:
                    continue
                image, fp = _open_image(image_file_path, other_formats)
                if image:
                    info = ProcessInfo(image, fp.name, Resampling[args.resampling], output_path)
        else:
            image, fp = _open_image(image_file_path, other_formats)
            if image:
                info = ProcessInfo(image, fp.name, Resampling[args.resampling], output_path)
        info.width = args.width
        info.height = args.height
        info.preferred_direction = PreferredDirections[args.preferred_direction]
        info.padding_color = padding_color
        info.scaling_instead_of_padding = args.scaling_instead_of_padding
        info.scaling_instead_of_cropping = args.scaling_instead_of_cropping
        info.image = image
        image_file_infos.append(info)

    if len(image_file_infos) == 0:
        print("no image input: {}{}".format(
                image_file_path.as_posix(),
                " ({})".format(" | ".join(other_formats)) if len(other_formats) > 0 else ""
            ),
            file=sys.stderr)
        sys.exit(1)
    return image_file_infos


def _adjust_images(image_file_infos: List[ProcessInfo], args) -> None:
    filename_with_input_params: bool = args.dev__filename_with_input_params
    force: bool = args.force
    json_response = {
        "command": sys.argv[1:],
        "items": [],
    }
    for info in image_file_infos:
        image = _resize_image(info)
        output_file_path: Path
        # def _modify_filename_for_dev(fn:str):
        # TODO dir書き出しでない場合にも適用
        #     return fn
        if info.output_path.is_dir():
            output_base_name: str = os.path.splitext(info.source_file_name)[0]
            if filename_with_input_params:
                output_base_name += "_"
                output_base_name += "[{}]".format(info.processed.name)
                output_base_name += "_{}x{}".format(image.width, image.height)
                if args.preferred_direction:
                    output_base_name += "_{}".format(args.preferred_direction)
                if args.scaling_instead_of_padding:
                    output_base_name += "_scaling4padding"
                if args.scaling_instead_of_cropping:
                    output_base_name += "_scaling4cropping"
                if force:
                    output_base_name += "_force"
                if info.resampling.name != Resampling.default_name():
                    output_base_name += "_{}".format(info.resampling)
                output_base_name += os.path.splitext(info.source_file_name)[1]
            else:
                output_base_name = info.source_file_name
                # TODO dir書き出しでない場合にも適用
            output_file_path = info.output_path / Path(output_base_name)
        else:
            output_file_path = info.output_path
        if output_file_path.exists() and not force and not args.dev__result_as_json:
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
                    "processed": info.processed.name,
                    "log": info.get_log()
                },
                "params": {
                    "preferred_direction": info.preferred_direction.name,
                    "padding_color": hex(info.padding_color),
                    "scaling_instead_of_padding": info.scaling_instead_of_padding,
                    "scaling_instead_of_cropping": info.scaling_instead_of_cropping,
                    "filename_with_input_params": filename_with_input_params,
                    "width": info.width,
                    "height": info.height,
                    "pixel_ratio": info.width / info.height,
                },
                "source": {
                    "file_name": info.source_file_name,
                    "width": info.source_width,
                    "height": info.source_height,
                    "pixel_ratio": info.source_pixel_ratio,
                },
            }
            json_response["items"].append(o)
        if not args.dev__no_image_output:
            if not output_file_path.parent.exists():
                # フォルダがなければ作る
                os.makedirs(output_file_path.parent)
            if output_file_path.name.endswith(".jpg"):
                image = image.convert("RGB")
            image.save(output_file_path)
        json_str: str = json.dumps(json_response, allow_nan=True, indent=2)
        print(json_str, file=sys.stdout)


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description='画像のサイズを適切に調整する。'
                    'jpgとpngなどフォーマットの違いを修正する。'
                    'ディレクトリを指定するとその中のすべてのファイルを処理対象にする。',
    )
    parser.add_argument("image_files", nargs='*',  help="処理対象となる画像ファイルまたはフォルダのパス。")
    parser.add_argument("-wpx", "--width", type=int, help="出力画像の横幅。")
    parser.add_argument("-hpx", "--height", type=int, help="出力画像の高さ。")
    parser.add_argument("-o", "--output", type=str, default="",
                        help="アウトプットファイルパス。指定ない場合入力と同じ場所に同名で上書きされる。"
                             "指定されタフォルダが存在しない場合、自動で作られる。"
                             "{n},{w},{h},{i}という記述はそれぞれ、"
                             "入力ファイル名の拡張を除いた部分・横幅・縦幅・処理番号に変数展開される。")
    parser.add_argument("-f", "--force", action="store_true",
                        help="処理結果ファイル保存時に同名ファイルが存在していても確認をしない場合に指定。")
    parser.add_argument(
        "-pd", "--preferred_direction", default="HEIGHT",
        choices=PreferredDirections.get_all(),
        help="\n".join([
            "リサイズ後に縦横比が合わない場合の優先方向指定。",
            "auto指定の場合はクリップしないですむ方向(全部の画像エリアを保持)を優先。",
            "auto_clip指定の場合はクリップが発生する方向を優先(できるかぎり大きく)。",
            "実際にクリップ・パディングするしないは別オプションで指定する。"
        ])
    )
    parser.add_argument(
        "-rs", "--resampling", default=Resampling.default_name(),
        choices=Resampling.get_all_names(),
        help="リサイズ時のピクセル補完方法。",
    )
    parser.add_argument(
        "--padding_color", type=str, default="11223344",
        help="パディング色をARGB値16進数8桁もしくはRGB値16進数6桁で指定。"
             "透明度指定は出力フォーマットがjpg/bmp/gifの場合無視される。")
    parser.add_argument(
        "--scaling_instead_of_padding", action="store_true",
        help="パディングの代わりにスケーリングをしたい場合に指定。")
    parser.add_argument(
        "--scaling_instead_of_cropping", action="store_true",
        help="クリッピングの代わりにスケーリングをしたい場合に指定。")
    parser.add_argument(
        "-sof", "--search_other_format", action="store_true",
        help="指定ファイルパスの画像が見つからない際に、別のフォーマットを入力に採用する。")
    parser.add_argument(
        "-of", "--other_formats", nargs="*", type=str, default=TARGET_FORMATS,
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
    _adjust_images(_create_process_info(args), args)


if __name__ == "__main__":
    main()

"""
usage: LGMLImageSizeAdjuster.py [-h] [-o OUTPUT] [-f] [-pd {WIDTH,HEIGHT,AUTO,AUTO_CROP}] [-rs {NEAREST,BOX,BILINEAR,HAMMING,BICUBIC,LANCZOS}] [--padding] [--padding_color PADDING_COLOR] [--scaling] [-sofmt] [-ofmt [OTHER_FORMATS ...]] [--dev__result_as_json]
                                [--dev__no_image_output] [--dev__filename_with_input_params] [-V]
                                image_file width height

画像のサイズを適切に調整する。jpgとpngなどフォーマットの違いを修正する。ディレクトリを指定するとその中のすべてのファイルを処理対象にする。

positional arguments:
  image_file            処理対象となる画像ファイルのパス。
  width                 出力画像の横幅。
  height                出力画像の高さ。

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        アウトプットファイルパス。指定ない場合入力と同じ場所に同名で上書きされる。指定されタフォルダが存在しない場合、自動で作られる。{n}や{w},{h}という記述はそれぞれ、入力ファイル名の拡張を除いた部分・横幅・縦幅に変数展開される。
  -f, --force           処理結果ファイル保存時に同名ファイルが存在していても確認をしない場合に指定。
  -pd {WIDTH,HEIGHT,AUTO,AUTO_CROP}, --preferred_direction {WIDTH,HEIGHT,AUTO,AUTO_CROP}
                        リサイズ後に縦横比が合わない場合の優先方向指定。 auto指定の場合はクリップしないですむ方向(全部の画像エリアを保持)を優先。 auto_clip指定の場合はクリップが発生する方向を優先(できるかぎり大きく)。 実際にクリップ・パディングするしないは別オプション
で指定する。
  -rs {NEAREST,BOX,BILINEAR,HAMMING,BICUBIC,LANCZOS}, --resampling {NEAREST,BOX,BILINEAR,HAMMING,BICUBIC,LANCZOS}
                        リサイズ時のピクセル補完方法。
  --padding             パディング(余白埋め)を許可する場合に指定。
  --padding_color PADDING_COLOR
                        パディング色をRGBA値16進数8桁で指定。透明度は出力フォーマットがjpgの場合無視される。
  --scaling             サイズがあわない場合にスケーリングをしたい場合に指定。padding指定がある場合はpaddingを優先。スケーリングもパディングもしない場合はクリッピングになる。
  -sofmt, --search_other_format
                        指定ファイルパスの画像が見つからない際に、別のフォーマットを入力に採用する。
  -ofmt [OTHER_FORMATS ...], --other_formats [OTHER_FORMATS ...]
                        異なるファイルフォーマットのファイル名を自動検索する場合の優先度。入力がディレクトリの場合は無効。
  --dev__result_as_json
                        開発用コマンド、jsonデータで処理の概要を標準出力する。
  --dev__no_image_output
                        開発用コマンド、画像を出力しない。dev__result_as_jsonと合わせて使う想定。
  --dev__filename_with_input_params
                        開発用コマンド、出力ファイル名にパラメータ値を含める。
  -V, --version         show program's version number and exit
"""