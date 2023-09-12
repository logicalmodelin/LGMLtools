import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import cv2
import numpy as np
from PIL import Image


def split(image_path: Path, output_dir_path: Path, prefix: str,
          cutout_alpha: int, min_size: Tuple[int, int], alpha_spread: int, padding:int) -> None:
    """
    大きなカラー画像を透明度を元にパーツに分割する
    ※ 透明度を持たない画像はエラーになる
    :param image_path: 入力画像ファイルパス
    :param output_dir_path: 出力ディレクトリパス
    :param prefix: 出力パーツのファイル名のプレフィックス
    :param cutout_alpha: 透明度の閾値(0~255)。この値以下の透明度はパーツ出力時に0にする
    :param min_size: 出力するパーツの最小サイズ これ以下のパーツは出力されない
    :param alpha_spread: 入力画像のパーツの不透明美便を拡張する太さ 太くすると近くに配置されたパーツがくっつく
    :param padding: 出力するパーツおのおのの余白サイズ
    """
    # MEMO: cv2は透明度のある画像をch所苦節扱えないようなのでPILも併用している
    col_image: Image = Image.open(image_path)
    buf = np.array(col_image)
    org_alpha_channel = buf[..., 3]
    alpha_channel = org_alpha_channel.copy()
    alpha_channel = cv2.GaussianBlur(alpha_channel, (5, 5), 0)
    alpha_channel[alpha_channel > 0] = 255
    # cv2.imshow('alpha_channel', alpha_channel)
    # cv2.waitKey(0)
    _, alpha_channel = cv2.threshold(alpha_channel, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    height: int
    width: int
    height, width = alpha_channel.shape[:3]
    contours: np.ndarray  # points of contours
    hierarchy: np.ndarray
    contours, hierarchy = cv2.findContours(alpha_channel, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if alpha_spread > 0:
        # 透明度の境界線を太くする
        alpha_channel = cv2.drawContours(alpha_channel, contours, -1, (255, 255, 255), alpha_spread)
        contours, hierarchy = cv2.findContours(alpha_channel, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # cv2.imshow('alpha_channel', alpha_channel)
    # cv2.waitKey(0)
    index: int = 0
    cnt: int = 0
    skip_cnt: int = 0
    h0: List[List[int]] = hierarchy[0]
    while True:
        contour = contours[index]
        min_x: int = width
        max_x: int = 0
        min_y: int = height
        max_y: int = 0
        for ct in contour:
            if min_x > ct[0][0]:
                min_x = ct[0][0]
            elif max_x < ct[0][0]:
                max_x = ct[0][0]
            if min_y > ct[0][1]:
                min_y = ct[0][1]
            elif max_y < ct[0][1]:
                max_y = ct[0][1]
        parts_width: int = max_x - min_x
        parts_height: int = max_y - min_y
        parts_img: np.ndarray = np.empty((parts_height, parts_width, 4), dtype=np.uint8)
        if parts_width < min_size[0] or parts_height < min_size[1]:
            print(f'output #{cnt + skip_cnt} / {len(contours)} : skip small parts ({parts_width}x{parts_height})')
            skip_cnt += 1
        else:
            for yy in range(parts_height):
                for xx in range(parts_width):
                    parts_img[yy, xx] = np.array([0, 0, 0, 0], dtype=np.uint8)
                    if cv2.pointPolygonTest(contour, (float(min_x + xx), float(min_y + yy)), True) >= 0:
                        parts_img[yy, xx] = buf[min_y + yy, min_x + xx]
                        new_alpha: int = org_alpha_channel[min_y + yy, min_x + xx]
                        if new_alpha <= cutout_alpha:
                            new_alpha = 0
                        parts_img[yy, xx, 3] = new_alpha
            print(f'output #{cnt + skip_cnt} / {len(contours)} : {prefix}{cnt:03d}.png'
                  f' ({parts_width}x{parts_height} @ {min_x},{min_y})')
            if padding > 0:
                parts_img = cv2.copyMakeBorder(parts_img, padding, padding, padding, padding, cv2.BORDER_CONSTANT,
                                               value=(0, 0, 0, 0))
            Image.fromarray(parts_img).save((output_dir_path / f'{prefix}{cnt:03d}.png').as_posix())
            cnt += 1
        node: List[int] = h0[index]
        if node[0] >= 0:
            index = node[0]
        elif node[2] >= 0:
            index = node[2]
        else:
            break
    print(f'output {cnt} images, skip {skip_cnt} images')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('src_image', type=str, help='source image file path')
    parser.add_argument('-o', '--output_dir', type=str, default='', help='output directory')
    parser.add_argument('--create_subdir', action="store_true",
                        help='create output subdirectory named by source image file name')
    parser.add_argument('-ca', '--cutout_alpha', type=int, default=0,
                        help='cutout alpha threshold(0~255) for final image')
    parser.add_argument('-ms', '--min_size', type=int, nargs=2, default=(0, 0),
                        help='images smaller than this size are not exported')
    parser.add_argument('-as', '--alpha_spread', type=int, default=0,
                        help='Spread px size for parts alpha channel, it makes parts boundary bigger.')
    parser.add_argument('-mg', '--padding', type=int, default=0,
                        help='padding px size for exported parts.')
    args = parser.parse_args()

    src_image_path: Path = Path(args.src_image)
    assert src_image_path.exists(), f'file not found: {args.src_image}'
    output_dir_path: Path = src_image_path.parent
    if len(args.output_dir) > 0:
        output_dir_path = Path(args.output_dir)
    prefix: str = src_image_path.stem + '_'
    if args.create_subdir:
        prefix = ''
        output_dir_path = output_dir_path / src_image_path.stem
        output_dir_path.mkdir(parents=True, exist_ok=True)
    assert output_dir_path.exists(), f'file not found: {args.output_dir}'
    cutout_alpha: int = args.cutout_alpha
    assert 0 <= cutout_alpha <= 255, f'cutout_alpha must be 0~255: {cutout_alpha}'
    min_size: Tuple[int, int] = args.min_size
    assert 0 <= min_size[0] and 0 <= min_size[1], f'min_size must be 0~: {min_size}'
    alpha_spread: int = args.alpha_spread
    assert 0 <= alpha_spread, f'alpha_spread must be 0~: {alpha_spread}'
    padding: int = args.padding
    assert 0 <= padding, f'padding must be 0~: {padding}'
    split(src_image_path, output_dir_path, prefix, cutout_alpha, min_size, alpha_spread, padding)


if __name__ == '__main__':
    main()

"""
python .\split_image_island.py .\images\test.png -o .\out\ -ms 100 100 --alpha_spread 10 --create_subdir

--

usage: split_image_island.py [-h] [-o OUTPUT_DIR] [--create_subdir] [-ca CUTOUT_ALPHA]
    [-ms MIN_SIZE MIN_SIZE] [-b alpha_spread] src_image

positional arguments:
  src_image             source image file path

options:
  -h, --help            show this help message and exit
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        output directory
  --create_subdir       create output subdirectory named by source image file name
  -ca CUTOUT_ALPHA, --cutout_alpha CUTOUT_ALPHA
                        cutout alpha threshold(0~255) for final image
  -ms MIN_SIZE MIN_SIZE, --min_size MIN_SIZE MIN_SIZE
                        images smaller than this size are not exported
  -b alpha_spread, --alpha_spread alpha_spread
                        alpha_spread size for parts alpha channel
"""

#  参考 https://emotionexplorer.blog.fc2.com/blog-entry-88.html
