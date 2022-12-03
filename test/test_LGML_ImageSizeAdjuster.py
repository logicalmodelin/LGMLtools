import subprocess
import os
import sys
from pathlib import Path
from PIL import Image
from typing import List, Tuple, Any, ClassVar, Literal, Callable, Union


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
        "100",
        "50",
        "-o",
        "work",
    ]
    print(" ".join(commands))
    result = subprocess.run(commands)
    print(result)


if __name__ == "__main__":
    main()
