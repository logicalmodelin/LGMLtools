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
    for k1, v1 in o.items():
        print("[{}]".format(k1))
        for k2, v2 in v1.items():
            print("\t{}: {}".format(k2, v2))


def _nealy_equals(a:float, b:float) -> bool:
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
    return o


def main():
    commands: List[str]
    width: int
    height: int
    o: dict
    image_list1: List[str] = ["images/test_640x427.png"]

    # _print_help()

    try:

        # 同じサイズ および基本チェック
        o = _execute_command(_get_command_base(image_list1, 640, 427))
        assert o["result"]["width"] == 640
        assert o["result"]["height"] == 427
        assert _nealy_equals(o["source"]["pixel_ratio"], o["result"]["pixel_ratio"])
        assert o["result"]["processed"] == "RESIZE_ONLY"

        # 同じ比率のリサイズ 小さく
        o = _execute_command(_get_command_base(image_list1, 320, 214))
        assert o["result"]["width"] == 320
        assert o["result"]["height"] == 214
        assert o["result"]["processed"] == "RESIZE_ONLY"
        assert _nealy_equals(o["source"]["pixel_ratio"], o["result"]["pixel_ratio"])

        # 同じ比率のリサイズ 大きく
        # 確認していない事 resampling 指定による画質の変化 -> 目視
        o = _execute_command(_get_command_base(image_list1, 1280, 854, additional=["--resampling", "NEAREST"]))
        assert o["result"]["width"] == 1280
        assert o["result"]["height"] == 854
        assert o["result"]["processed"] == "RESIZE_ONLY"
        assert _nealy_equals(o["source"]["pixel_ratio"], o["result"]["pixel_ratio"])

        # 比率が違う画像
        o = _execute_command(_get_command_base(image_list1, 320, 320, "HEIGHT"))
        assert o["result"]["width"] == 320
        assert o["result"]["height"] == 320
        assert o["result"]["processed"] == "CROP"
        assert not _nealy_equals(o["source"]["pixel_ratio"], o["result"]["pixel_ratio"])

    except AssertionError as err:
        _print_result(o)
        raise err


if __name__ == "__main__":
    main()
