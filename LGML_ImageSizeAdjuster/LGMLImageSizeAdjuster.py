import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from PIL import Image
from typing import List, Tuple, Any, Dict, ClassVar, Literal, Callable, Union
from enum import Enum, auto
from pprint import pprint
# from strenum import StrEnum


TARGET_FORMATS: Tuple[str] = ("png", "jpg", "gif", "bmp", "tif", "tga")  # StrEnumにする？


class ImageSize:

    width: str
    height: str

    def __init__(self, width: str, height: str):
        checked: bool = self._check_format(width) and self._check_format(height)
        if not checked:
            raise ValueError(f"Invalid Size format. {width} x {height}")
        self.width = width
        self.height = height

    @staticmethod
    def _check_format(size_str: str) -> bool:
        if size_str.isdigit():
            return True
        elif size_str.endswith("%"):
            return True
        else:
            return False

    def get_actual_image_size(self, image: Image) -> Tuple[int, int]:
        """
        実際のイメージサイズを計算して返す
        仕様）
        サイズ指定が％の場合は、元のサイズに対する割合を計算する
        数値が1以上の場合は数値そのものを返す
        数値が0の場合は自動計算の意味で、
        widthもheightも0の場合は画像そのものの大きさを返す
        片方が0の場合は元の画像の比率を保った大きさに調整して返す
        """
        w: int
        h: int
        if self.width.isdigit():
            w = int(self.width)
        elif self.width.endswith("%"):
            w = int(image.width * float(self.width[:-1]) / 100)
        if self.height.isdigit():
            h = int(self.height)
        elif self.width.endswith("%"):
            h = int(image.height * float(self.height[:-1]) / 100)
        ratio: float = image.width / image.height
        if w == 0 and h == 0:
            return image.width, image.height
        elif w == 0:
            w = int(h * ratio)
        elif h == 0:
            h = int(w / ratio)
        return w, h



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
    source_path: Path
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

    def __init__(self, image: Image.Image, source_path: Path, resampling: Resampling, output_path: Path):
        self.image = image
        self.source_path = source_path
        self.source_width = image.width
        self.source_height = image.height
        self.source_pixel_ratio = image.width / image.height
        self.resampling = resampling
        self.output_path = output_path
        self.processed = Processed.RESIZE_ONLY
        self._log = []

    def as_filenames_str(self):
        return "[ProcessInfo] {} -> {}".format(self.source_path, self.output_path)

    # @property
    # def is_output_dir(self) -> bool:
    #     return self.output_path.is_dir()

    @property
    def ratio(self) -> float:
        return self.width / self.height

    @property
    def source_base_name(self) -> str:
        return self.source_path.name

    @property
    def file_format(self) -> str:
        return os.path.splitext(self.self.source_base_name)[1]

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
        print("resize {}: {} -> {}".format(info.source_base_name, size, resize))
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
        print("resize {}: {} -> {}".format(info.source_base_name, size, resize))
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


def _is_output_dir_like(p: Path) -> bool:
    # 指定されたパス文字はディレクトリぽいか？
    if not p.exists():
        # まだ存在しない場合拡張子がなければ新規作成のディレクトリと判断
        return p.suffix == ""
    return p.is_dir()


def _modify_output_path(input_path: str, output_path: Path, w: int, h: int, index: int) -> Path:
    """
    出力ファイル名の変数展開
    """
    return Path(output_path.as_posix().replace("{n}", os.path.splitext(
        os.path.basename(input_path))[0]).replace(
        "{p}", input_path.parent.as_posix()).replace("{w}", str(w)).replace(
        "{h}", str(h)).replace("{i}", str(index)))


def _create_process_info(args: Any) -> List[ProcessInfo]:
    """
    実際の処理前に処理設計情報（ProcessInfo）を画像の枚数分作成する。
    """
    image_size: ImageSize = ImageSize(args.size[0], args.size[1])
    padding_color: int = _get_padding_color(args)
    other_formats: List[str] = args.other_formats if args.search_other_format else []
    image_file_infos: List[ProcessInfo] = []

    for image_file in args.image_files:
        image_file_path: Path = Path(image_file)
        output_path: Path = Path(args.output) if args.output else image_file_path

        # 変数展開でiやnを使うと全てのファイル上書きを回避できるのでエラーにしない
        # if (len(args.image_files) > 1 or image_file_path.is_dir()) and not is_output_dir:
        #     print("読み込み対象がディレクトリや複数ファイルの場合は出力先もディレクトリにする必要があります。", file=sys.stderr)
        #     sys.exit(1)

        def create_info(im: Image.Image, source_path: Path, output_path_: Path):
            """
            infoに基本情報を付与して一覧に加える
            """
            index: int = len(image_file_infos)
            if _is_output_dir_like(output_path):
                output_path_ = output_path_ / source_path.name
            size: Tuple[int, int] = image_size.get_actual_image_size(im)
            output_path_ = _modify_output_path(source_path, output_path_, size[0], size[1], index)
            pi = ProcessInfo(im, source_path, Resampling[args.resampling], output_path_)
            pi.width = size[0]
            pi.height = size[1]
            pi.preferred_direction = PreferredDirections[args.preferred_direction]
            pi.padding_color = padding_color
            pi.scaling_instead_of_padding = args.scaling_instead_of_padding
            pi.scaling_instead_of_cropping = args.scaling_instead_of_cropping
            image_file_infos.append(pi)

        if image_file_path.is_dir():
            # もし読み込み指定がディレクトリなら画像ぽい物を探す
            for f in os.listdir(image_file_path):
                _, ext = os.path.splitext(f)
                if not ext:
                    continue
                if ext[1:] not in TARGET_FORMATS:
                    continue
                image, fp = _open_image(image_file_path / f, other_formats)
                if image:
                    create_info(image, fp, output_path)
        else:
            # 読み込み対象が画像なので
            image, fp = _open_image(image_file_path, other_formats)
            if image:
                create_info(image, fp, output_path)

    _check_info_list(image_file_infos, other_formats)

    return image_file_infos


def _get_padding_color(args) -> int:
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
    return padding_color


def _check_info_list(image_file_infos: List[ProcessInfo], other_formats: List[str]):
    """
    ProcessInfo全ての整合性チェック
    """

    def print_info_all():
        for i, x in enumerate(image_file_infos):
            print("#{} {}".format(i, x.as_filenames_str()))

    def check_info_count():
        """
        書き出し存在チェック
        """
        if len(image_file_infos) == 0:
            print("入力となる画像がありません: {}".format(
                    " ({})".format(" | ".join(other_formats)) if len(other_formats) > 0 else ""
                ),
                file=sys.stderr)
            sys.exit(1)

    def check_duplicated_info_output():
        """
        # 書き出し重複チェック
        """
        counts: dict = {}
        duplicated_output_path: dict = {}
        x: ProcessInfo
        for x in image_file_infos:
            p = x.output_path.as_posix()
            if p not in counts:
                counts[p] = 0
            counts[p] += 1
        k: str
        v: int
        for k, v in counts.items():
            if v > 1:
                duplicated_output_path[k] = v
        if len(duplicated_output_path.keys()) > 0:
            print("出力ファイル指定に重複ができています。\n{}".format(
                "\n".join(["\t{} x {}".format(x, duplicated_output_path[x]) for x in duplicated_output_path.keys()])),
                file=sys.stderr)
            sys.exit(1)

    print_info_all()
    check_info_count()
    check_duplicated_info_output()


def _adjust_images(image_file_infos: List[ProcessInfo], args) -> None:
    filename_with_input_params: bool = args.dev__filename_with_input_params
    json_response = {
        "command": "{}".format(" ".join(sys.argv[1:])),
        "items": [],
    }
    for info in image_file_infos:
        image = _resize_image(info)
        output_file_path: Path = info.output_path
        if filename_with_input_params:
            output_base_name = output_file_path.stem
            output_base_name += "_"
            output_base_name += "[{}]".format(info.processed.name)
            output_base_name += "_{}x{}".format(image.width, image.height)
            if args.preferred_direction:
                output_base_name += "_{}".format(args.preferred_direction)
            if args.scaling_instead_of_padding:
                output_base_name += "_scaling4padding"
            if args.scaling_instead_of_cropping:
                output_base_name += "_scaling4cropping"
            if args.force:
                output_base_name += "_force"
            if args.overwrite_err:
                output_base_name += "_ow_err"
            if info.resampling.name != Resampling.default_name():
                output_base_name += "_{}".format(info.resampling)
            output_file_path = output_file_path.parent / Path(output_base_name + output_file_path.suffix)

        if output_file_path.exists():
            print("{} exists.".format(output_file_path.name))
            if args.overwrite_err:
                print("ファイルが上書きされます。{}".format(output_file_path.name), file=sys.stderr)
                sys.exit(1)
            elif not args.force:
                r: str = input("上書き確認({}) y/n".format(output_file_path.name))
                if r.lower() != "y":
                    continue
        if args.dev__write_result_json != "":
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
                    "file_name": info.source_base_name,
                    "width": info.source_width,
                    "height": info.source_height,
                    "pixel_ratio": info.source_pixel_ratio,
                },
            }
            json_response["items"].append(o)
        if not args.dryrun:
            if not output_file_path.parent.exists():
                # フォルダがなければ作る
                os.makedirs(output_file_path.parent)
            if output_file_path.name.endswith(".jpg"):
                image = image.convert("RGB")
            image.save(output_file_path)

    try:
        with open(args.dev__write_result_json, "w") as fp:
            json.dump(json_response, fp, indent=2)
    except Exception as ex:
        print(str(ex), file=sys.stderr)


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description='画像のサイズを適切に調整する。'
                    'jpgとpngなどフォーマットの違いを修正する。'
                    'ディレクトリを指定するとその中のすべてのファイルを処理対象にする。',
    )
    parser.add_argument("image_files", nargs='*',  help="処理対象となる画像ファイルまたはフォルダのパス。")
    parser.add_argument("-s", "--size", nargs=2, type=str, default=["100%", "100%"],
                        help="出力画像の横幅と高さ。数値もしくは元画像サイズの％で指定する。"
                             "例) 320 240, 50%% 0, 0 0 など。"
                             "数値の片方が0の場合、縦横比率を保って自動調整される。"
                             "幅高さともに0の場合は入力画像と同じになる。"
                        )
    parser.add_argument("-o", "--output", type=str, default="",
                        help="アウトプットファイルパス。指定ない場合入力と同じ場所に同名で上書きされる。"
                             "指定されタフォルダが存在しない場合、自動で作られる。"
                             "{p},{n},{w},{h},{i}という記述はそれぞれ、"
                             "入力ファイルの親フォルダパス（最後のスラッシュは含まない）、"
                             "入力ファイル名の拡張子を除いた部分・横幅・縦幅・処理番号に変数展開される。")
    parser.add_argument("-f", "--force", action="store_true",
                        help="処理結果ファイル保存時に同名ファイルが存在していても確認をしない場合に指定。")
    parser.add_argument("-owerr", "--overwrite_err", action="store_true",
                        help="ファイル上書き時はエラーで止める。forceより優先。")
    parser.add_argument(
        "-pd", "--preferred_direction", default="HEIGHT",
        choices=PreferredDirections.get_all(),
        help="\n".join([
            "リサイズ後に元画像と縦横比が合わない場合、優先処理する方向をWIDTHまたはHEIGHTで指定。",
            "AUTO_PAD指定の場合はクリップしないですむ方向を優先。(小さくなっても元画像全体を表示)",
            "AUTO_CROP指定の場合はクリップが発生する方向を優先。(見きれてもできるかぎり大きく表示)",
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
        "--dryrun", action="store_true",
        help="開発用コマンド、画像を出力しない。dev__write_result_jsonと合わせて使う想定。")
    parser.add_argument(
        "--dev__write_result_json", default="", type=str,
        help="開発用コマンド、指定されたパスにjsonデータで処理の概要を出力する。")
    parser.add_argument(
        "--dev__filename_with_input_params", action="store_true",
        help="開発用コマンド、出力ファイル名にパラメータ値を含める。")
    parser.add_argument("-V", '--version', action='version', version='%(prog)s 1.1')
    args: argparse.Namespace = parser.parse_args()
    _adjust_images(_create_process_info(args), args)


if __name__ == "__main__":
    main()
