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


def main():
    tool_path: Path = Path(__file__).absolute().parent.parent / Path("LGML_ImageSizeAdjuster/LGMLImageSizeAdjuster.py")
    print(tool_path.as_posix())
    assert tool_path.exists()
    commands: List[str] = []
    image_file = Path(__file__).parent.absolute() / Path("images/test1080x1920.png")
    assert image_file.exists()
    commands += [
        "py",
        tool_path.as_posix(),
        image_file.as_posix(),
        "540",
        "50",
        "-o",
        "work",
        "--result_as_json",
    ]
    # print(" ".join(commands))
    # result: subprocess.CompletedProcess = subprocess.run(commands)
    result = subprocess.run(commands, stdout=subprocess.PIPE).stdout.decode()
    o: dict = json.loads(result)
    _print_result(o)


if __name__ == "__main__":
    main()
