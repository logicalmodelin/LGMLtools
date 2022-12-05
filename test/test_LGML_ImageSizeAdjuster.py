import json
import subprocess
import os
import sys
from pathlib import Path
from PIL import Image
from typing import List, Tuple, Any, ClassVar, Literal, Callable, Union

tool_path: Path = Path(__file__).absolute().parent.parent / Path("LGML_ImageSizeAdjuster/LGMLImageSizeAdjuster.py")
assert tool_path.exists()


def _print_result(o: dict) -> None:
    if o is None:
        print("None")
        return
    for k1, v1 in o.items():
        print("[{}]".format(k1))
        if k1 == "command":
            print("\t{}".format(v1))
        else:
            for k2, v2 in v1.items():
                print("\t{}: {}".format(k2, v2))


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
        images: List[str], width: int, height: int, preferred_direction: str = None,
        result_as_json: bool = True,
        filename_with_input_params: bool = True,
        additional: List[str] = None) -> List[str]:
    commands: List[str]
    image_paths: List[Path] = []
    for i in images:
        image_file: Path = Path(__file__).parent.absolute() / Path(i)
        assert image_file.exists()
        image_paths.append(image_file)
    commands = [
        "py",
        tool_path.as_posix(),
        " ".join([x.as_posix() for x in image_paths]),
        "-wpx",
        str(width),
        "-hpx",
        str(height),
        "-o",
        "work"
    ]
    if preferred_direction is not None:
        commands += ["--preferred_direction", preferred_direction]
    if result_as_json:
        commands.append("--dev__result_as_json")
    if filename_with_input_params:
        commands.append("--dev__filename_with_input_params")
    if additional is not None and len(additional) > 0:
        commands += additional
    print("> " + " ".join(commands))
    return commands


def _execute_command(commands: List[str], print_result: bool = True) -> dict:
    result = subprocess.run(commands, stdout=subprocess.PIPE).stdout.decode()
    o: dict = None
    try:
        o = json.loads(result)
    except json.decoder.JSONDecodeError as err:
        print(result)
        raise err
    if print_result:
        _print_result(o)
    # print(o["params"]["width"], o["result"]["width"])
    # print(o["params"]["height"], o["result"]["height"])
    # print(o["params"]["pixel_ratio"], o["result"]["pixel_ratio"])
    assert o["params"]["width"] == o["result"]["width"]
    assert o["params"]["height"] == o["result"]["height"]
    assert _nealy_equals(o["params"]["pixel_ratio"], o["result"]["pixel_ratio"])
    return o


def main():
    commands: List[str]
    width: int
    height: int
    o: dict = None
    image_list1: List[str] = ["images/test_640x427.png"]

    # _print_help()

    try:

        # ######### HEIGHT優先挙動チェック ######### #

        def test1():
            # 同じサイズ および基本チェック
            o = _execute_command(_get_command_base(image_list1, 640, 427))
            assert o["result"]["processed"] == "RESIZE_ONLY"

            # 同じ比率のリサイズ 小さく
            o = _execute_command(_get_command_base(image_list1, 320, 214))
            assert o["result"]["processed"] == "RESIZE_ONLY"

            # 同じ比率のリサイズ 大きく
            # 確認していない事 resampling 指定による画質の変化 -> 目視
            o = _execute_command(_get_command_base(image_list1, 1280, 854, additional=["--resampling", "NEAREST"]))
            assert o["result"]["processed"] == "RESIZE_ONLY"

            # 比率が違う画像(crop)
            o = _execute_command(_get_command_base(image_list1, 320, 320))
            assert o["result"]["processed"] == "CROP"

            # 比率が違う画像(scaling4crop)
            o = _execute_command(_get_command_base(image_list1, 320, 320,
                                                   additional=["--scaling_instead_of_cropping"]))
            assert o["result"]["processed"] == "SCALE"

            # 比率が違う画像(padding)
            # 確認していない事 パディング色 -> 目視 オレンジ
            o = _execute_command(
                _get_command_base(image_list1, 640, 320, additional=["--padding_color", "ffff8800"]))
            assert o["result"]["processed"] == "PAD"

            # 比率が違う画像(scaling4pad)
            o = _execute_command(
                _get_command_base(image_list1, 640, 320, additional=["--scaling_instead_of_padding"]))
            assert o["result"]["processed"] == "SCALE"

        # ######### 上記までのテストを WIDTH優先で行うもの ######### #

        def test2():
            # 同じサイズ および基本チェック
            o = _execute_command(_get_command_base(image_list1, 640, 427, "WIDTH"))
            assert o["result"]["processed"] == "RESIZE_ONLY"

            # 同じ比率のリサイズ 小さく
            o = _execute_command(_get_command_base(image_list1, 320, 214, "WIDTH"))
            assert o["result"]["processed"] == "PAD"
            o = _execute_command(
                _get_command_base(image_list1, 320, 214 - 1, "WIDTH"))  # 元画像の縦ドット数が奇数なのでずれがでる
            assert o["result"]["processed"] == "RESIZE_ONLY"

            # 同じ比率のリサイズ 大きく
            # 確認していない事 resampling 指定による画質の変化 -> 目視
            o = _execute_command(
                _get_command_base(image_list1, 1280, 854, "WIDTH", additional=["--resampling", "BOX"]))
            assert o["result"]["processed"] == "RESIZE_ONLY"

            # 比率が違う画像(pad)
            # 確認していない事 パディング色 -> 目視 暗い青緑
            o = _execute_command(
                _get_command_base(image_list1, 320, 320, "WIDTH", additional=["--padding_color", "440088ff"]))
            assert o["result"]["processed"] == "PAD"

            # 比率が違う画像(scaling4pad)
            o = _execute_command(_get_command_base(image_list1, 320, 320, "WIDTH",
                                                   additional=["--scaling_instead_of_padding"]))
            assert o["result"]["processed"] == "SCALE"
            # 比率が違う画像(crop)
            o = _execute_command(
                _get_command_base(image_list1, 640, 320, "WIDTH"))
            assert o["result"]["processed"] == "CROP"

            # 比率が違う画像(scaling4crop)
            o = _execute_command(
                _get_command_base(image_list1, 640, 320, "WIDTH", additional=["--scaling_instead_of_cropping"]))
            assert o["result"]["processed"] == "SCALE"

        # ######### 自動クロップ方向優先 ######### #

        def test3():
            # 同じサイズ および基本チェック
            o = _execute_command(_get_command_base(image_list1, 640, 427, "AUTO_CROP"))
            assert o["result"]["processed"] == "RESIZE_ONLY"

            # 同じ比率のリサイズ 小さく
            o = _execute_command(_get_command_base(image_list1, 320, 214, "AUTO_CROP"))
            assert o["result"]["processed"] == "RESIZE_ONLY"

            # 同じ比率のリサイズ 大きく
            # 確認していない事 resampling 指定による画質の変化 -> 目視
            o = _execute_command(
                _get_command_base(image_list1, 1280, 854, "AUTO_CROP", additional=["--resampling", "HAMMING"]))
            assert o["result"]["processed"] == "RESIZE_ONLY"

            # 比率が違う画像(crop)
            o = _execute_command(_get_command_base(image_list1, 320, 320, "AUTO_CROP"))
            assert o["result"]["processed"] == "CROP"

            # 比率が違う画像(scaling4crop)
            o = _execute_command(_get_command_base(image_list1, 320, 320, "AUTO_CROP",
                                                   additional=["--scaling_instead_of_cropping"]))
            assert o["result"]["processed"] == "SCALE"

            # 比率が違う画像(padding)
            # 確認していない事 パディング色 -> 目視 完全透明
            o = _execute_command(
                _get_command_base(image_list1, 640, 320, "AUTO_CROP", additional=["--padding_color", "00ff8800"]))
            assert o["result"]["processed"] == "CROP"

            # 比率が違う画像(scaling4pad)
            o = _execute_command(
                _get_command_base(image_list1, 640, 320, "AUTO_CROP", additional=["--scaling_instead_of_cropping"]))
            assert o["result"]["processed"] == "SCALE"

        # ######### 自動パディング方向優先 ######### #

        def test4():
            # 同じサイズ および基本チェック
            o = _execute_command(_get_command_base(image_list1, 640, 427, "AUTO_PAD"))
            assert o["result"]["processed"] == "RESIZE_ONLY"

            # 同じ比率のリサイズ 小さく
            o = _execute_command(_get_command_base(image_list1, 320, 214, "AUTO_PAD"))
            assert o["result"]["processed"] == "PAD"
            # o = _execute_command(_get_command_base(image_list1, 320, 214 - 1, "AUTO_PAD"))
            # RESIZE_ONLYになるサイズ指定を見つけるのが難しい
            # assert o["result"]["processed"] == "RESIZE_ONLY"

            # 同じ比率のリサイズ 大きく
            # 確認していない事 resampling 指定による画質の変化 -> 目視
            o = _execute_command(
                _get_command_base(image_list1, 1280, 854, "AUTO_PAD", additional=["--resampling", "HAMMING"]))
            assert o["result"]["processed"] == "RESIZE_ONLY"

            # 比率が違う画像(crop)
            o = _execute_command(_get_command_base(image_list1, 320, 320, "AUTO_PAD"))
            assert o["result"]["processed"] == "PAD"

            # 比率が違う画像(scaling4crop)
            o = _execute_command(_get_command_base(image_list1, 320, 320, "AUTO_PAD",
                                                   additional=["--scaling_instead_of_padding"]))
            assert o["result"]["processed"] == "SCALE"

            # 比率が違う画像(padding)
            # 確認していない事 パディング色 -> 目視 完全透明
            o = _execute_command(
                _get_command_base(image_list1, 640, 320, "AUTO_PAD", additional=["--padding_color", "00ff8800"]))
            assert o["result"]["processed"] == "PAD"

            # 比率が違う画像(scaling4pad)
            o = _execute_command(
                _get_command_base(image_list1, 640, 320, "AUTO_PAD", additional=["--scaling_instead_of_padding"]))
            assert o["result"]["processed"] == "SCALE"

        test1()
        test2()
        test3()
        test4()

    except AssertionError as err:
        _print_result(o)
        raise err


if __name__ == "__main__":
    main()
