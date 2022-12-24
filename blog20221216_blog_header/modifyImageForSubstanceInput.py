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

    w, h = size
    if w == h:
        return size
    if w > h:
        return w, w
    else:
        return h, h


def get_clip_position(base_size: tuple[int, int], size: tuple[int, int], valign: str, align: str) -> tuple[int, int]:
    new_pos = [int((base_size[0] - size[0]) / 2), int((base_size[1] - size[1]) / 2)]
    if valign == 'top':
        new_pos[1] = 0
    elif valign == 'bottom':
        new_pos[1] = base_size[1] - size[1]
    if align == 'left':
        new_pos[0] = 0
    elif align == 'right':
        new_pos[0] = base_size[0] - size[0]
    return new_pos


def extract(img: Image, extract_size_image_: str, extract_size: tuple[int, int], valign: str, align: str,
            scale: float, force_square: bool) -> Image:
    if len(extract_size_image_) > 0:
        assert Path(extract_size_image_).exists()
        extract_size_image: Image = PIL.Image.open(extract_size_image_)
        if scale != 1.0:
            extract_size_image = extract_size_image.resize(
                (int(extract_size_image.size[0] * scale), int(extract_size_image.size[1] * scale)))
        extract_size = extract_size_image.size
        extract_size = find_fit_size_power_of_2(extract_size, force_square)

    new_pos: tuple[int, int] = get_clip_position(img.size, extract_size, valign, align)
    return img.crop((new_pos[0], new_pos[1], new_pos[0] + extract_size[0], new_pos[1] + extract_size[1]))


def resize(img: Image, scale: float, bg_color: tuple[int, int, int],
           alpha: int, valign: str, align: str, force_square: bool) -> Image:
    if scale != 1.0:
        img = img.resize((int(img.size[0] * scale), int(img.size[1] * scale)))
    assert img.size[0] <= TARGET_SIZES[0] and img.size[1] <= TARGET_SIZES[0]
    col = bg_color
    new_size = find_fit_size_power_of_2(img.size, force_square)
    bg_img = PIL.Image.new(
        'RGBA', new_size, (col[0], col[1], col[2], int(alpha)))
    new_pos = get_clip_position(new_size, img.size, valign, align)
    bg_img.paste(img, new_pos)
    return bg_img


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['resize', 'extract'], help='resize: 画像をリサイズする。extract: 画像を切り抜く。')
    parser.add_argument('src_image', type=str, help='source image')
    parser.add_argument('-o', '--output_image', type=str, default='', help='output image file path')
    parser.add_argument('-s', '--scale', type=float, default=1.0,
                        help='src image scale for resize mode, target image scale for extract mode')
    parser.add_argument('--valign', type=str, default='middle', choices=['middle', 'top', 'bottom'])
    parser.add_argument('--align', type=str, default='center', choices=['center', 'left', 'right'])
    parser.add_argument('--resize_force_square', type=bool, default=True,
                        help='If True, the output image is square. resize mode only.')
    parser.add_argument('--resize_bg_color', type=int, nargs=3, default=[0, 0, 0], help='resize mode only')
    parser.add_argument('--resize_bg_alpha', type=int, default=0, help='resize mode only')
    extract_options = parser.add_mutually_exclusive_group()
    extract_options.add_argument('--extract_size_image',
                                 type=str, default="", help='extract mode only')
    extract_options.add_argument('--extract_size',
                                 type=int, nargs=2, default=[100, 100], help='extract mode only')
    args = parser.parse_args()
    assert Path(args.src_image).exists()
    if len(args.output_image) == 0:
        output_image_path: Path = Path(args.src_image).parent / Path(Path(args.src_image).stem + '_out.png')
    else:
        output_image_path: Path = Path(args.output_image)
    img: Image = PIL.Image.open(args.src_image)
    if args.mode == 'resize':
        img = resize(img, args.scale, args.resize_bg_color, args.resize_bg_alpha,
                     args.valign, args.align, args.resize_force_square)
    elif args.mode == 'extract':
        img = extract(img, args.extract_size_image, args.extract_size, args.valign, args.align,
                      args.scale, args.resize_force_square)
    if output_image_path.suffix == '.jpg' or output_image_path.suffix == '.gif':
        img = img.convert('RGB')
    img.save(output_image_path)


if __name__ == '__main__':
    main()


"""
sample command
python modifyImageForSubstanceInput.py resize images/qbg.jpg -o images/qbg_out.png --valign top --align left --resize_bg_color 200 20 24
python modifyImageForSubstanceInput.py extract images/qbg_out.png -o images/qbg_out2.png --extract_size_image images/qbg.jpg --valign top --align left
python modifyImageForSubstanceInput.py extract images/qbg_out.png -o images/qbg_out3.png --extract_size 758 578 --valign top --align left
"""
