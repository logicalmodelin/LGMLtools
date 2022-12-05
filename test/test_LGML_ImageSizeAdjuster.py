import json
import subprocess
import os
import sys
from pathlib import Path
from PIL import Image
from typing import List, Tuple, Any, ClassVar, Literal, Callable, Union
from pprint import pprint

tool_path: Path = Path(__file__).absolute().parent.parent / Path("LGML_ImageSizeAdjuster/LGMLImageSizeAdjuster.py")
assert tool_path.exists()
images_folder: Path = Path(__file__).parent / Path("images")
temp_folder: Path = Path(__file__).parent / Path("temp_for_test")
debug_json_path: Path = temp_folder / Path("result.json")


def _print_result(o: dict) -> None:
    pprint(o)
    # if o is None:
    #     print("None")
    #     return
    # if "command" in o:
    #     print("[command]\n\t{}".format(o["command"]))
    # if "items" in o:
    #     for index, item in enumerate(o["items"]):
    #         print("[item #{}]".format(index))
    #         for k1, v1 in item.items():
    #             print("    [{}]".format(k1))
    #             for k2, v2 in v1.items():
    #                 print("\t{}: {}".format(k2, v2))


def _nealy_equals(a: float, b: float) -> bool:
    return abs(a - b) < 0.01


def _print_help():
    commands: List[str] = [
        "py",
        tool_path.as_posix(),
        "-h",
    ]
    subprocess.run(commands)


def _get_command_base(
        images_or_dir: Union[str, List[str]], width: int, height: int, preferred_direction: str = None,
        out: str = None,
        result_as_json: bool = True,
        filename_with_input_params: bool = True,
        additional: List[str] = None) -> List[str]:
    commands: List[str]
    if debug_json_path.exists():
        os.unlink(debug_json_path)
    image_paths: List[Path] = []
    if isinstance(images_or_dir, List):
        # files
        for i in images_or_dir:
            image_file: Path = Path(__file__).parent.absolute() / Path(i)
            # assert image_file.exists()
            image_paths.append(image_file)
    else:
        # dir
        image_paths.append(Path(images_or_dir))
    commands = [
        "py",
        tool_path.as_posix()
    ]
    for x in image_paths:
        commands.append(x.as_posix())
    commands += [
        "-wpx",
        str(width),
        "-hpx",
        str(height),
    ]
    if out is None:
        commands += [
            "-o",
            temp_folder.as_posix()
        ]
    else:
        commands += [
            "-o",
            out
        ]
    if preferred_direction is not None:
        commands += ["--preferred_direction", preferred_direction]
    if result_as_json:
        commands.append("--dev__write_result_json")
        commands.append(debug_json_path.as_posix())
    if filename_with_input_params:
        commands.append("--dev__filename_with_input_params")
    if additional is not None and len(additional) > 0:
        commands += additional
    print("> " + " ".join(commands))
    return commands


def _execute_command(commands: List[str], print_result: bool = True) -> dict:
    subprocess.run(commands, stdout=subprocess.PIPE).stdout.decode()
    o: dict = None
    if debug_json_path.exists():
        with open(debug_json_path, "r") as fp:
            o = json.load(fp)
    if o is not None:
        if print_result:
            _print_result(o)
        # print(o["params"]["width"], o["result"]["width"])
        # print(o["params"]["height"], o["result"]["height"])
        # print(o["params"]["pixel_ratio"], o["result"]["pixel_ratio"])
        for item in o["items"]:
            assert item["params"]["width"] == item["result"]["width"]
            assert item["params"]["height"] == item["result"]["height"]
            assert _nealy_equals(item["params"]["pixel_ratio"], item["result"]["pixel_ratio"])
    return o


def main():
    commands: List[str]
    width: int
    height: int
    o: dict = None
    all_format: List[str] = ["png", "jpg", "gif", "bmp", "tga", "tif"]
    image_list1: List[str] = ["images/test_640x427.png"]
    image_list2: List[str] = ["images/test1080x1920.png", "images/test1920x1080.png"]

    # _print_help()

    try:

        # ######### HEIGHT優先挙動チェック ######### #

        def test1():
            _clear_temp_folder()
            # 同じサイズ および基本チェック
            o = _execute_command(_get_command_base(image_list1, 640, 427))
            assert o["items"][0]["result"]["processed"] == "RESIZE_ONLY"

            # 同じ比率のリサイズ 小さく
            o = _execute_command(_get_command_base(image_list1, 320, 214))
            assert o["items"][0]["result"]["processed"] == "RESIZE_ONLY"

            # 同じ比率のリサイズ 大きく
            # 確認していない事 resampling 指定による画質の変化 -> 目視
            o = _execute_command(_get_command_base(image_list1, 1280, 854, additional=["--resampling", "NEAREST"]))
            assert o["items"][0]["result"]["processed"] == "RESIZE_ONLY"

            # 比率が違う画像(crop)
            o = _execute_command(_get_command_base(image_list1, 320, 320))
            assert o["items"][0]["result"]["processed"] == "CROP"

            # 比率が違う画像(scaling4crop)
            o = _execute_command(_get_command_base(image_list1, 320, 320,
                                                   additional=["--scaling_instead_of_cropping"]))
            assert o["items"][0]["result"]["processed"] == "SCALE"

            # 比率が違う画像(padding)
            # 確認していない事 パディング色 -> 目視 オレンジ
            o = _execute_command(
                _get_command_base(image_list1, 640, 320, additional=["--padding_color", "ffff8800"]))
            assert o["items"][0]["result"]["processed"] == "PAD"

            # 比率が違う画像(scaling4pad)
            o = _execute_command(
                _get_command_base(image_list1, 640, 320, additional=["--scaling_instead_of_padding"]))
            assert o["items"][0]["result"]["processed"] == "SCALE"

        # ######### 上記までのテストを WIDTH優先で行うもの ######### #

        def test2():
            _clear_temp_folder()
            # 同じサイズ および基本チェック
            o = _execute_command(_get_command_base(image_list1, 640, 427, "WIDTH"))
            assert o["items"][0]["result"]["processed"] == "RESIZE_ONLY"

            # 同じ比率のリサイズ 小さく
            o = _execute_command(_get_command_base(image_list1, 320, 214, "WIDTH"))
            assert o["items"][0]["result"]["processed"] == "PAD"
            o = _execute_command(
                _get_command_base(image_list1, 320, 214 - 1, "WIDTH"))  # 元画像の縦ドット数が奇数なのでずれがでる
            assert o["items"][0]["result"]["processed"] == "RESIZE_ONLY"

            # 同じ比率のリサイズ 大きく
            # 確認していない事 resampling 指定による画質の変化 -> 目視
            o = _execute_command(
                _get_command_base(image_list1, 1280, 854, "WIDTH", additional=["--resampling", "BOX"]))
            assert o["items"][0]["result"]["processed"] == "RESIZE_ONLY"

            # 比率が違う画像(pad)
            # 確認していない事 パディング色 -> 目視 暗い青緑
            o = _execute_command(
                _get_command_base(image_list1, 320, 320, "WIDTH", additional=["--padding_color", "440088ff"]))
            assert o["items"][0]["result"]["processed"] == "PAD"

            # 比率が違う画像(scaling4pad)
            o = _execute_command(_get_command_base(image_list1, 320, 320, "WIDTH",
                                                   additional=["--scaling_instead_of_padding"]))
            assert o["items"][0]["result"]["processed"] == "SCALE"
            # 比率が違う画像(crop)
            o = _execute_command(
                _get_command_base(image_list1, 640, 320, "WIDTH"))
            assert o["items"][0]["result"]["processed"] == "CROP"

            # 比率が違う画像(scaling4crop)
            o = _execute_command(
                _get_command_base(image_list1, 640, 320, "WIDTH", additional=["--scaling_instead_of_cropping"]))
            assert o["items"][0]["result"]["processed"] == "SCALE"

        # ######### 自動クロップ方向優先 ######### #

        def test3():
            _clear_temp_folder()
            # 同じサイズ および基本チェック
            o = _execute_command(_get_command_base(image_list1, 640, 427, "AUTO_CROP"))
            assert o["items"][0]["result"]["processed"] == "RESIZE_ONLY"

            # 同じ比率のリサイズ 小さく
            o = _execute_command(_get_command_base(image_list1, 320, 214, "AUTO_CROP"))
            assert o["items"][0]["result"]["processed"] == "RESIZE_ONLY"

            # 同じ比率のリサイズ 大きく
            # 確認していない事 resampling 指定による画質の変化 -> 目視
            o = _execute_command(
                _get_command_base(image_list1, 1280, 854, "AUTO_CROP", additional=["--resampling", "HAMMING"]))
            assert o["items"][0]["result"]["processed"] == "RESIZE_ONLY"

            # 比率が違う画像(crop)
            o = _execute_command(_get_command_base(image_list1, 320, 320, "AUTO_CROP"))
            assert o["items"][0]["result"]["processed"] == "CROP"

            # 比率が違う画像(scaling4crop)
            o = _execute_command(_get_command_base(image_list1, 320, 320, "AUTO_CROP",
                                                   additional=["--scaling_instead_of_cropping"]))
            assert o["items"][0]["result"]["processed"] == "SCALE"

            # 比率が違う画像(padding)
            # 確認していない事 パディング色 -> 目視 完全透明
            o = _execute_command(
                _get_command_base(image_list1, 640, 320, "AUTO_CROP", additional=["--padding_color", "00ff8800"]))
            assert o["items"][0]["result"]["processed"] == "CROP"

            # 比率が違う画像(scaling4pad)
            o = _execute_command(
                _get_command_base(image_list1, 640, 320, "AUTO_CROP", additional=["--scaling_instead_of_cropping"]))
            assert o["items"][0]["result"]["processed"] == "SCALE"

        # ######### 自動パディング方向優先 ######### #

        def test4():
            _clear_temp_folder()
            # 同じサイズ および基本チェック
            o = _execute_command(_get_command_base(image_list1, 640, 427, "AUTO_PAD"))
            assert o["items"][0]["result"]["processed"] == "RESIZE_ONLY"

            # 同じ比率のリサイズ 小さく
            o = _execute_command(_get_command_base(image_list1, 320, 214, "AUTO_PAD"))
            assert o["items"][0]["result"]["processed"] == "PAD"
            # o = _execute_command(_get_command_base(image_list1, 320, 214 - 1, "AUTO_PAD"))
            # RESIZE_ONLYになるサイズ指定を見つけるのが難しい
            # assert o["result"]["processed"] == "RESIZE_ONLY"

            # 同じ比率のリサイズ 大きく
            # 確認していない事 resampling 指定による画質の変化 -> 目視
            o = _execute_command(
                _get_command_base(image_list1, 1280, 854, "AUTO_PAD", additional=["--resampling", "HAMMING"]))
            assert o["items"][0]["result"]["processed"] == "RESIZE_ONLY"

            # 比率が違う画像(crop)
            o = _execute_command(_get_command_base(image_list1, 320, 320, "AUTO_PAD"))
            assert o["items"][0]["result"]["processed"] == "PAD"

            # 比率が違う画像(scaling4crop)
            o = _execute_command(_get_command_base(image_list1, 320, 320, "AUTO_PAD",
                                                   additional=["--scaling_instead_of_padding"]))
            assert o["items"][0]["result"]["processed"] == "SCALE"

            # 比率が違う画像(padding)
            # 確認していない事 パディング色 -> 目視 完全透明
            o = _execute_command(
                _get_command_base(image_list1, 640, 320, "AUTO_PAD", additional=["--padding_color", "00ff8800"]))
            assert o["items"][0]["result"]["processed"] == "PAD"

            # 比率が違う画像(scaling4pad)
            o = _execute_command(
                _get_command_base(image_list1, 640, 320, "AUTO_PAD", additional=["--scaling_instead_of_padding"]))
            assert o["items"][0]["result"]["processed"] == "SCALE"

        def test5():
            _clear_temp_folder()
            # 複数画像入力テスト
            #   デフォ出力、ファイル出力、ディレクトリ出力
            #   フォルダ自動作成

            # フォルダ入力テスト
            #   デフォ出力、ファイル出力、ディレクトリ出力
            o = _execute_command(
                _get_command_base(images_folder.as_posix(), 640, 640, out=temp_folder.as_posix(),
                                  filename_with_input_params=False))
            assert (temp_folder / Path("test1080x1920.png")).exists()
            assert (temp_folder / Path("test1920x1080.png")).exists()
            assert (temp_folder / Path("test_640x427.png")).exists()

            # _clear_temp_folder()
            # o = _execute_command(
            #     _get_command_base(images_folder.as_posix(), 640, 640, out=(temp_folder / "test{i}.png").as_posix(),
            #                       filename_with_input_params=False, additional=["--search_other_format"]))

        def test6():
            _clear_temp_folder()
            # すべてのフォーマット出力テスト
            for fmt in all_format:
                o = _execute_command(
                    _get_command_base(image_list1, 640, 320, out="{}/{}.{}".format(temp_folder.as_posix(), "{n}", fmt)))
                assert len(list(temp_folder.glob("*.{}".format(fmt)))) == 1

        def test7():
            _clear_temp_folder()
            # 自動拡張子変換テスト
            image_list: List[str] = [x.replace(".png", ".jpg") for x in image_list2]
            o = _execute_command(
                _get_command_base(image_list, 640, 320, out=(temp_folder / Path("pic{i}.png")).as_posix(),
                                  filename_with_input_params=False, additional=["--search_other_format"]))
            assert (temp_folder / Path("pic0.png")).exists()
            assert (temp_folder / Path("pic1.png")).exists()

        def test8():
            _clear_temp_folder()
            # 変数展開テスト
            o = _execute_command(
                _get_command_base(
                    image_list1, 640, 320,
                    out=(temp_folder / Path("{w}x{h}.jpg")).as_posix(), filename_with_input_params=False))
            assert (temp_folder / Path("640x320.jpg")).exists()

        def _clear_temp_folder():
            files: List[str] = []
            for fmt in all_format:
                files += list(temp_folder.glob("*.{}".format(fmt)))
            for f in files:
                print("unlink {}".format(f))
                os.unlink(f)

        _clear_temp_folder()
        test1()
        test2()
        test3()
        test4()
        test5()
        test6()
        test7()
        test8()

    except AssertionError as err:
        _print_result(o)
        raise err


if __name__ == "__main__":
    # _print_help()
    main()
