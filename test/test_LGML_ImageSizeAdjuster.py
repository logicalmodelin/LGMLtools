import json
import shutil
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
images_folder2: Path = Path(__file__).parent / Path("images2")
temp_folder: Path = Path(__file__).parent / Path("temp_for_test")
temp_sub_folder_path: Path = temp_folder / Path("sub_folder")
debug_json_path: Path = temp_folder / Path("result.json")


def _print_result(o: dict) -> None:
    pprint(o)


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
        no_output_param: bool = False,
        result_as_json: bool = True,
        filename_with_input_params: bool = True,
        dryrun: bool = False,
        force:bool = False,
        overwrite_err: bool = False,
        additional: List[str] = None) -> List[str]:
    commands: List[str]
    if debug_json_path.exists():
        os.unlink(debug_json_path)
    image_paths: List[Path] = []
    if isinstance(images_or_dir, List):
        # files or dirs
        for i in images_or_dir:
            image_file: Path = Path(i)
            # assert image_file.exists()  # テストとしては存在しないものを渡すこともある
            image_paths.append(image_file)
    else:
        # a file or dir
        image_paths.append(Path(images_or_dir))
    commands = [
        "py",
        tool_path.as_posix()
    ]
    for x in image_paths:
        commands.append(x.as_posix())
    commands += [
        "-s",
        str(width),
        str(height),
    ]
    if not no_output_param:
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
    if force:
        commands.append("--force")
    if dryrun:
        commands.append("--dryrun")
    if overwrite_err:
        commands.append("--overwrite_err")
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
    try:
        result: subprocess.CompletedProcess = subprocess.check_output(commands)
        print(result.decode())
    except subprocess.CalledProcessError as err:
        print(err)
        return None
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
            # 複数画像入力テスト
            #   デフォ出力、ファイル出力、ディレクトリ出力
            #   フォルダ自動作成

            # フォルダ入力テスト
            # # デフォ出力
            _clear_temp_folder()
            shutil.copy(images_folder / "test1920x1080.png", temp_folder)  # 上書きが起こるのでいったんコピー
            o = _execute_command(
                _get_command_base(
                    temp_folder.as_posix(), 100, 640,
                    no_output_param=True, filename_with_input_params=False, force=True))
            assert (temp_folder / Path("test1920x1080.png")).exists()

            # フォルダ入力テスト
            # # # ディレクトリ出力
            _clear_temp_folder()
            o = _execute_command(
                _get_command_base(images_folder.as_posix(), 200, 640, out=temp_folder.as_posix(),
                                  filename_with_input_params=False, force=True))
            assert (temp_folder / Path("test1080x1920.png")).exists()
            assert (temp_folder / Path("test1920x1080.png")).exists()
            assert (temp_folder / Path("test_640x427.png")).exists()

            # フォルダ入力テスト
            # # ファイル出力
            _clear_temp_folder()
            o = _execute_command(
                _get_command_base(images_folder.as_posix(), 300, 640, out=(temp_folder / "test{i}.png").as_posix(),
                                  filename_with_input_params=False, additional=["--search_other_format"]))
            assert (temp_folder / Path("test0.png")).exists()
            assert (temp_folder / Path("test1.png")).exists()
            assert (temp_folder / Path("test2.png")).exists()

            # 複数フォルダ入力テスト
            # # デフォ出力
            _clear_temp_folder()
            o = _execute_command(
                _get_command_base([images_folder.as_posix(), images_folder2.as_posix()], 300, 640,
                                  no_output_param=True, dryrun=True,  # 全部上書きしちゃうのでdryrun
                                  filename_with_input_params=False, force=True))
            assert len(o["items"]) == 6
            assert o["items"][2]["result"]["output_file_path"].endswith(r"images/test_640x427.png")
            assert o["items"][5]["result"]["output_file_path"].endswith(r"images2/test_640x427.png")

            # 複数フォルダ入力テスト
            # # ファイル出力
            _clear_temp_folder()
            o = _execute_command(
                _get_command_base([images_folder.as_posix(), images_folder2.as_posix()], 300, 640,
                                  out=(temp_folder / "test{i}.png").as_posix(),
                                  filename_with_input_params=False, additional=["--search_other_format"]))
            assert (temp_folder / Path("test0.png")).exists()
            assert (temp_folder / Path("test1.png")).exists()
            assert (temp_folder / Path("test2.png")).exists()
            assert (temp_folder / Path("test3.png")).exists()
            assert (temp_folder / Path("test4.png")).exists()
            assert (temp_folder / Path("test5.png")).exists()

            # 複数フォルダ入力テスト
            # # フォルダ出力
            _clear_temp_folder()
            # 書き出し重複エラーになる
            o = _execute_command(
                _get_command_base(
                    [images_folder.as_posix(), images_folder2.as_posix()], 300, 640,
                    out=temp_folder.as_posix(), dryrun=True,
                    filename_with_input_params=False))
            assert o is None  # エラーが起きた、の意味

            # 複数画像入力テスト
            # # デフォ出力
            _clear_temp_folder()
            o = _execute_command(
                _get_command_base(image_list2, 640, 320,
                                  no_output_param=True,
                                  filename_with_input_params=False,  # 同名上書きになる
                                  force=True,  # 上書きOKになる
                                  dryrun=True))  # inputr dir にファイル上書きしてしまうので dryrun
            assert len(o["items"]) == 2
            assert o["items"][0]["result"]["output_file_path"].endswith("images/test1080x1920.png")
            assert o["items"][1]["result"]["output_file_path"].endswith("images/test1920x1080.png")

            # 複数画像入力テスト
            # # ファイル出力
            _clear_temp_folder()
            o = _execute_command(
                _get_command_base(image_list2, 640, 320,
                                  filename_with_input_params=True,
                                  out=(temp_folder / "hoge.jpg").as_posix(),
                                  dryrun=True))
            assert o is None  # 上書きエラー

            # 複数画像入力テスト
            # # デフォ出力
            _clear_temp_folder()
            o = _execute_command(
                _get_command_base(image_list2, 640, 320,
                                  no_output_param=True,
                                  filename_with_input_params=False,  # 同名上書きになる
                                  force=True,  # 上書きOKになる
                                  dryrun=True))  # inputr dir にファイル上書きしてしまうので dryrun
            assert len(o["items"]) == 2
            assert o["items"][0]["result"]["output_file_path"].endswith("images/test1080x1920.png")
            assert o["items"][1]["result"]["output_file_path"].endswith("images/test1920x1080.png")

            # 複数画像入力テスト
            # # ファイル出力
            _clear_temp_folder()
            o = _execute_command(
                _get_command_base(image_list2, 640, 320,
                                  filename_with_input_params=True,
                                  out=(temp_folder / "hoge.jpg").as_posix(),
                                  dryrun=True))
            assert o is None  # 上書きエラー

            # 複数画像入力テスト
            # # ファイル名指定出力
            _clear_temp_folder()
            o = _execute_command(
                _get_command_base(image_list2, 640, 320,
                                  filename_with_input_params=False,
                                  out=(temp_folder / "hoge{i}.jpg").as_posix(),
                                  force=True,
                                  dryrun=True))
            assert len(o["items"]) == 2
            assert o["items"][0]["result"]["output_file_path"].endswith("temp_for_test/hoge0.jpg")
            assert o["items"][1]["result"]["output_file_path"].endswith("temp_for_test/hoge1.jpg")

            # 複数画像入力テスト
            # # ディレクトリ出力
            _clear_temp_folder()
            o = _execute_command(
                _get_command_base(image_list2, 640, 320,
                                  filename_with_input_params=False,
                                  out=temp_folder.as_posix(),
                                  force=True,
                                  dryrun=True))
            assert len(o["items"]) == 2
            assert o["items"][0]["result"]["output_file_path"].endswith("temp_for_test/test1080x1920.png")
            assert o["items"][1]["result"]["output_file_path"].endswith("temp_for_test/test1920x1080.png")

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

            o = _execute_command(
                _get_command_base(
                    image_list1, 640, 320,
                    dryrun=True,
                    out=(Path("{p}/hoge.png")).as_posix(), filename_with_input_params=False))
            assert o["items"][0]["result"]["output_file_path"].endswith("images/hoge.png")

        def test9():
            # フォルダ自動作成

            # 単一画像入力テスト
            _clear_temp_folder()
            assert not temp_sub_folder_path.exists()
            o = _execute_command(
                _get_command_base(
                    image_list1, 640, 320,
                    out=temp_sub_folder_path.as_posix()))
            assert temp_sub_folder_path.exists()

            # 複数画像入力テスト
            _clear_temp_folder()
            assert not temp_sub_folder_path.exists()
            o = _execute_command(
                _get_command_base(
                    image_list2, 640, 320,
                    out=temp_sub_folder_path.as_posix()))
            assert temp_sub_folder_path.exists()

            # フォルダ入力テスト
            _clear_temp_folder()
            assert not temp_sub_folder_path.exists()
            o = _execute_command(
                _get_command_base(
                    images_folder.as_posix(), 640, 320,
                    out=temp_sub_folder_path.as_posix()))
            assert temp_sub_folder_path.exists()

        def test10():

            # 上書きエラーテスト
            _clear_temp_folder()
            o = _execute_command(
                _get_command_base(image_list1, 640, 320, no_output_param=True,
                                  filename_with_input_params=False,  # 同名上書きになる
                                  force=True,  # 上書きOKになる
                                  dryrun=True))
            assert o is not None
            _clear_temp_folder()
            o = _execute_command(
                _get_command_base(image_list1, 640, 320, no_output_param=True,
                                  filename_with_input_params=False,  # 同名上書きになる
                                  overwrite_err=True,  # 上書きerrorになる
                                  dryrun=True))
            assert o is None

        def testA():
            # 新規テスト開発中の単独実行用
            pass

        def _clear_temp_folder():
            files: List[str] = []
            for fmt in all_format:
                files += list(temp_folder.glob("*.{}".format(fmt)))
            for f in files:
                # print("unlink {}".format(f))
                os.unlink(f)
            if temp_sub_folder_path.exists():
                shutil.rmtree(temp_sub_folder_path)

        test1()
        test2()
        test3()
        test4()
        test5()
        test6()
        test7()
        test8()
        test9()
        test10()
        testA()

    except AssertionError as err:
        _print_result(o)
        raise err


if __name__ == "__main__":
    _print_help()
    # main()

