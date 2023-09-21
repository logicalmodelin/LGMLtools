import argparse
import os.path
import shutil
import tomllib
from pathlib import Path
from typing import List, Dict, Tuple, Any
import tempfile
import json
from datetime import datetime
import subprocess
from PIL import Image

CONTENT_ASSETS_REQUIRED: List[str] = [
    "config.toml",
    "bg.png",
]

TEMPLATE_ASSETS_REQUIRED: List[str] = [
    "template.aep",
]

ICON_FILE_NAMES: List[str] = [
    "icon01.png",
    "icon02.png",
    "icon03.png",
    "icon04.png",
    "icon05.png",
]

class Config:
    template_dir_path: Path
    title: str
    description: str
    output_image_size: Tuple[int, int]
    output_file_path: Path
    work_dir_path: Path | None
    ae_version: str = "2023"

    def __init__(self, config_toml_path: Path):
        config_toml_path = config_toml_path.absolute()
        with open(config_toml_path, "rb") as fp:
            o: Dict = tomllib.load(fp)
        assert "title" in o, "config.tomlに title が設定されていません"
        self.title = o["title"]
        assert "description" in o, "config.tomlに description が設定されていません"
        self.description = o["description"]
        assert "template_dir" in o, "config.tomlに template_dir が設定されていません"
        self.template_dir_path = Path(o["template_dir"])
        if not self.template_dir_path.is_absolute():
            self.template_dir_path = Path(os.path.normpath(config_toml_path.parent / self.template_dir_path))
            self.template_dir_path = self.template_dir_path.absolute()
        print(self.template_dir_path.as_posix())
        assert self.template_dir_path.is_dir(), "config.tomlの template_dir がディレクトリではありません"
        for asset in TEMPLATE_ASSETS_REQUIRED:
            assert (self.template_dir_path / asset).exists(), f"{asset}が存在しません"
        if "output_image_size" in o:
            assert len(o["output_image_size"]) == 2, "config.tomlの output_image_size が配列2要素ではありません"
            assert isinstance(o["output_image_size"][0], int) and \
                   isinstance(o["output_image_size"][1], int), "config.tomlの output_image_size の要素が整数ではありません"
            self.output_image_size = (o["output_image_size"][0], o["output_image_size"][1])
        else:
            self.output_image_size = (-1, -1)
        if "output_dir" in o:
            self.output_file_path = Path(o["output_dir"])
            if not self.output_file_path.is_absolute():
                self.output_file_path = Path(os.path.normpath(config_toml_path.parent / self.output_file_path))
                self.output_file_path = self.output_file_path.absolute()
            assert self.output_file_path.is_dir(), "config.tomlの output_dir がディレクトリではありません"
        else:
            self.output_file_path = config_toml_path.parent
        if "output_file_name" in o:
            self.output_file_path = self.output_file_path / o["output_file_name"]
        else:
            self.output_file_path = self.output_file_path / f"{config_toml_path.stem}.png"
        if "work_dir" in o:
            self.work_dir_path = Path(o["work_dir"])
            if not self.work_dir_path.is_absolute():
                self.work_dir_path = Path(os.path.normpath(config_toml_path.parent / self.work_dir_path))
                self.work_dir_path = self.work_dir_path.absolute()
            assert self.work_dir_path.is_dir(), "config.tomlの work_dir がディレクトリではありません"
        else:
            self.work_dir_path = None
        if "ae_version" in o:
            self.ae_version = o["ae_version"]

    def create_json_obj(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
        }


def _export(work_dir_path: Path, config: Config):
    output_file_path: Path = config.output_file_path
    output_image_size: Tuple[int, int] = config.output_image_size
    commands: List[str] = [
        f'C:/Program Files/Adobe/Adobe After Effects {config.ae_version}/Support Files/afterfx',
        '-s',
        f'var file = new File(\'{work_dir_path.as_posix()}/template.aep\');'
        f'app.open(file);app.project.renderQueue.render();',
        '-noui',
    ]
    print(commands)
    try:
        result = subprocess.run(commands)
    except Exception as e:
        print(e)



def main():
    parser = argparse.ArgumentParser(description="LGML thumbnail generator")
    parser.add_argument("content_dir", type=str, help="コンテンツフォルダのパス")
    params = parser.parse_args()
    content_dir_path: Path = Path(params.content_dir)
    assert content_dir_path.exists(), "コンテンツフォルダが存在しません"
    assert content_dir_path.is_dir(), "コンテンツフォルダのパスがディレクトリではありません"
    for asset in CONTENT_ASSETS_REQUIRED:
        assert (content_dir_path / asset).exists(), f"{asset}が存在しません"
    config: Config = Config(content_dir_path / "config.toml")
    temp_dir_path: tempfile.TemporaryDirectory | None = None
    work_dir_path: Path = config.work_dir_path
    if work_dir_path is None:
        tempfile.TemporaryDirectory()
        work_dir_path: Path = Path(temp_dir_path.name) / datetime.now().strftime("%Y%m%d%H%M%S")
    else:
        work_dir_path = work_dir_path / datetime.now().strftime("%Y%m%d%H%M%S")

    shutil.copytree(config.template_dir_path, work_dir_path)

    # config json の作成 上書きOK
    o:  Dict[str, Any] = config.create_json_obj()
    with open((work_dir_path / "info.json").as_posix(), "w", encoding="utf-8") as fp:
        json.dump(o, fp, indent=4, ensure_ascii=False)

    # bg.png のコピー 上書きOK
    shutil.copyfile(content_dir_path / "bg.png", (work_dir_path / "bg.png").as_posix())

    # iconファイルのコピー 上書きOK
    dummy_icon_path: Path = Path(__file__).parent / "resources/transparent64x64.png"
    for icon_file_name in ICON_FILE_NAMES:
        target_icon_path: Path = (work_dir_path / icon_file_name)
        if target_icon_path.exists():
            target_icon_path.unlink()
        src_icon_path: Path = content_dir_path / icon_file_name
        if src_icon_path.exists():
            # アイコンファイルがあればコピー
            shutil.copyfile(src_icon_path, target_icon_path)
        else:
            # 透明の物で埋める
            shutil.copyfile(dummy_icon_path, target_icon_path)

    # AEで画像出力
    _export(work_dir_path, config)  # TODO FIX
    if temp_dir_path is not None:
        temp_dir_path.cleanup()
    export_image_path: Path = work_dir_path / "image_00000.png"
    assert export_image_path.exists(), "画像が出力されていません"

    # リサイズとフォーマット変換しつつ出力フォルダにコピー
    im = Image.open(export_image_path)
    if config.output_image_size[0] > 0 and config.output_image_size[1] > 0:
        # 本当は LGMLImageSizeAdjuster.py を使いたい
        im = im.resize(config.output_image_size)
    if config.output_file_path.suffix == ".jpg":
        im = im.convert("RGB")
    if config.output_file_path.exists():
        config.output_file_path.unlink()
    im.save(config.output_file_path.as_posix())


if __name__ == "__main__":
    main()
