import json
import subprocess
import os
import sys
from pathlib import Path
from PIL import Image
from typing import List, Tuple, Any, ClassVar, Literal, Callable, Union


def _print_result(o: dict) -> None:
    for k1, v1 in o.items():
        print("[{}]".format(k1))
        for k2, v2 in v1.items():
            print("\t{}: {}".format(k2, v2))


def _nealy_equals(a:float, b:float) -> bool:
    return abs(a - b) < 0.01


def main():
    tool_path: Path = Path(__file__).absolute().parent.parent / Path("LGML_ImageSizeAdjuster/LGMLImageSizeAdjuster.py")
    print(tool_path.as_posix())
    assert tool_path.exists()
    commands: List[str] = []
    image_file = Path(__file__).parent.absolute() / Path("images/test_640x427.png")
    assert image_file.exists()
    # 同じ比率のリサイズ
    width: int = 320
    height: int = 213
    commands += [
        "py",
        tool_path.as_posix(),
        image_file.as_posix(),
        str(width),
        str(height),
        "-o",
        "work",
        "--dev__result_as_json",
    ]
    result = subprocess.run(commands, stdout=subprocess.PIPE).stdout.decode()
    o: dict = json.loads(result)
    _print_result(o)
    assert width == o["result"]["width"]
    assert height == o["result"]["height"]
    assert _nealy_equals(o["source"]["pixel_ratio"], o["result"]["pixel_ratio"])


if __name__ == "__main__":
    main()
