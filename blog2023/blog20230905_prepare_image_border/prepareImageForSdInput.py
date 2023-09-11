import sys
from typing import List
import PIL
from PIL import Image
from pathlib import Path
import argparse

TARGET_SIZES = [8192, 4096, 2048, 1024, 512, 256, 128, 64, 32, 16, 8, 4, 2, 1]


def find_fit_size_power_of_2(size: tuple[int, int], force_square: bool) -> tuple[int, int]:
    w: int = -1
    h: int = -1
    for i in range(len(TARGET_SIZES) - 1):
        if TARGET_SIZES[i] >= size[0] > TARGET_SIZES[i + 1]:
            w = TARGET_SIZES[i]
            break
    for i in range(len(TARGET_SIZES) - 1):
        if TARGET_SIZES[i] >= size[1] > TARGET_SIZES[i + 1]:
            h = TARGET_SIZES[i]
            break
    if force_square:
        w = max(w, h)
        h = w
    return w, h


def get_clip_position(base_size: tuple[int, int], size: tuple[int, int], align: str) -> tuple[int, int]:
    new_pos = [int((base_size[0] - size[0]) / 2), int((base_size[1] - size[1]) / 2)]
    if align == 'TL':
        new_pos[0] = 0
        new_pos[1] = 0
    elif align == 'BR':
        new_pos[1] = base_size[1] - size[1]
        new_pos[0] = base_size[0] - size[0]
    return new_pos[0], new_pos[1]


def resize(img: Image, border_width: int, min_size: tuple[int, int],
           bg_color: tuple[int, int, int, int], align: str, power_of_2: bool, square: bool) -> Image:

    temp_img: Image
    new_size: tuple[int, int]

    # remove transparent area first
    img = img.crop(img.getbbox())

    # add border
    if border_width > 0:
        temp_img = PIL.Image.new('RGBA', (img.width + border_width * 2, img.height + border_width * 2), bg_color)
        temp_img.paste(img, (border_width, border_width))
        img = temp_img

    # calc new size
    new_size = (img.width, img.height)
    if new_size[0] < min_size[0]:
        new_size = (min_size[0], new_size[1])
    if new_size[1] < min_size[1]:
        new_size = (new_size[0], min_size[1])

    # convert to power of 2
    if power_of_2:
        new_size = find_fit_size_power_of_2(new_size, force_square=square)
    temp_img = PIL.Image.new('RGBA', new_size, bg_color)
    temp_img.paste(img, get_clip_position(new_size, img.size, align))
    return temp_img


def find_files(files: list[str], extensions: None | list[str] = None) -> list[Path]:
    """
    find files recursively
    """
    ret: list[Path] = []
    for file in files:
        p: Path = Path(file)
        assert p.exists(), f'File not found: {file}'
        if p.is_file():
            if extensions is None or p.suffix in extensions:
                ret.append(p)
        if p.is_dir():
            ret.extend(find_files([str(x) for x in p.iterdir()]))
    return ret


def main() -> None:
    parser = argparse.ArgumentParser(
        # 真ん中よせ時に 半ドットずれないように注意'
        description='画像サイズに適切に余白をつける\n' +
                    '* 一度余白全部削除　->\n' +
                    '* 任意のサイズの余白追加　->\n' +
                    '* 最低サイズ指定あればそこまで大きくする ->\n' +
                    '* 2のべき乗吸着指定あればさらに調整')
    parser.add_argument('src_images', type=str, nargs='*', help='source image')
    parser.add_argument('-o', '--output_dir', type=str, default='', help='output image dir')
    parser.add_argument('--overwrite', action='store_true', help='overwrite output image file')
    parser.add_argument('-bw', '--border_width', type=int, default=0, help='transparent border width')
    parser.add_argument('-al', '--align', type=str, default='CENTER', choices=['CENTER', 'TL', 'BR'])
    parser.add_argument('-p2', '--power_of_2', action='store_true', default=False,
                        help='output image size is power of 2.')
    parser.add_argument('-sq', '--square', action='store_true', default=False,
                        help='output image size is square.')
    parser.add_argument('-min', '--min_size', type=int, nargs=2, default=[0, 0], help='minimum final size')
    parser.add_argument('--auto_min_size', action="store_true", help='when more than 2 images are specified,' +
                        'the min_size argument  is automatically determined from the size of the input image.')
    parser.add_argument('-bg', '--bg_color', type=int, nargs=4, default=[0, 0, 0, 0],
                        help='background color like 255 255 255 255')
    args = parser.parse_args()
    if len(args.output_dir) > 0:
        assert Path(args.output_dir).exists()
        assert Path(args.output_dir).is_dir()

    files = find_files(args.src_images, ['.png', '.jpg', '.gif'])
    assert len(files) > 0, 'No image file found.'

    if args.auto_min_size:
        min_size: List[int] = [0, 0]
        for file in files:
            img: Image = PIL.Image.open(file)
            if img.size[0] > min_size[0]:
                min_size[0] = img.size[0]
            if img.size[1] > min_size[1]:
                min_size[1] = img.size[1]
        if args.min_size[0] < min_size[0]:
            args.min_size[0] = min_size[0]
        if args.min_size[1] < min_size[1]:
            args.min_size[1] = min_size[1]

    output_image_path: Path
    for file in files:
        if args.overwrite:
            output_image_path = file
        elif len(args.output_dir) > 0:
            output_image_path = Path(args.output_dir) / file.name
        else:
            output_image_path = Path(args.output_dir).parent / Path(file.stem + '__out.png')

        img: Image = PIL.Image.open(file)
        assert img.size[0] <= TARGET_SIZES[0] and img.size[1] <= TARGET_SIZES[0]
        img = resize(img, args.border_width, args.min_size, tuple(args.bg_color),
                     args.align, args.power_of_2, args.square)

        if output_image_path.suffix == '.jpg' or output_image_path.suffix == '.gif':
            print('Save image format should not be jpg or gif.'
                  'This program makes image with transparent background.', file=sys.stderr)
            img = img.convert('RGB')
        img.save(output_image_path)


if __name__ == '__main__':
    main()


"""
# sample command
python prepareImageForSdInput.py images/icon.png -o out -bw 100 -al TL -p2 -min 512 512 -bg 255 0 0 255
"""
