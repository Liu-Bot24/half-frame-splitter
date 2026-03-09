#!/usr/bin/env python3
"""
半格胶片裁切工具
自动识别半格胶片扫描照片中的黑缝，提取单张照片
"""

import argparse
import sys
from pathlib import Path
from PIL import Image
import numpy as np
import cv2


def find_black_gap(img_gray):
    """
    找到中间黑缝区域的边界
    返回: (gap_start, gap_end, gap_center)
    """
    h, w = img_gray.shape

    edges = cv2.Canny(img_gray, 30, 100)
    edge_density = np.sum(edges > 0, axis=0)

    search_start = w // 4
    search_end = 3 * w // 4

    # 找到密度最低的点
    min_density = float('inf')
    min_col = w // 2
    for col in range(search_start, search_end):
        if edge_density[col] < min_density:
            min_density = edge_density[col]
            min_col = col

    # 用阈值100扩展边界
    threshold = 100

    gap_start = min_col
    for col in range(min_col, max(0, min_col - 300), -1):
        if edge_density[col] > threshold:
            gap_start = col
            break

    gap_end = min_col
    for col in range(min_col, min(w, min_col + 300)):
        if edge_density[col] > threshold:
            gap_end = col
            break

    return gap_start, gap_end, min_col


def split_single_frame(img_path, output_dir, frame_number=None, prefix='', verbose=True):
    """
    裁切单张半格胶片扫描图
    """
    img = cv2.imread(str(img_path))
    if img is None:
        raise ValueError(f"无法读取图像: {img_path}")

    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = img_gray.shape

    if verbose:
        print(f"\n处理: {Path(img_path).name}")
        print(f"图像尺寸: {w}x{h}")

    # 找到黑缝区域
    gap_start, gap_end, _ = find_black_gap(img_gray)
    if verbose:
        print(f"检测到黑缝区域: {gap_start} - {gap_end}")

    # 裁切边界
    left_edge = 0
    right_edge = w - 1

    left_width = gap_start - left_edge
    right_width = right_edge - gap_end

    if verbose:
        print(f"左侧画面: {left_width}px, 右侧画面: {right_width}px")

    # 检查宽度差异
    warnings = []
    width_ratio = min(left_width, right_width) / max(left_width, right_width) if max(left_width, right_width) > 0 else 0
    if width_ratio < 0.85:
        warnings.append(f"左右宽度差异较大 ({left_width} vs {right_width})")

    if left_width > w * 0.8 or right_width > w * 0.8:
        warnings.append("检测到画面可能异常")

    # 执行裁切
    pil_img = Image.open(img_path)

    left_crop = (left_edge, 0, gap_start, h)
    left_img = pil_img.crop(left_crop)

    right_crop = (gap_end + 1, 0, right_edge + 1, h)
    right_img = pil_img.crop(right_crop)

    # 保存
    if frame_number is not None:
        left_num = frame_number
        right_num = frame_number + 1
        left_path = Path(output_dir) / f"{prefix}{left_num:02d}.jpg"
        right_path = Path(output_dir) / f"{prefix}{right_num:02d}.jpg"
    else:
        stem = Path(img_path).stem
        left_path = Path(output_dir) / f"{prefix}{stem}_L.jpg"
        right_path = Path(output_dir) / f"{prefix}{stem}_R.jpg"

    left_img.save(left_path, quality=100, subsampling=0)
    right_img.save(right_path, quality=100, subsampling=0)

    if verbose:
        print(f"已保存: {left_path.name}, {right_path.name}")

    for w_msg in warnings:
        print(f"  ⚠️ {w_msg}")

    return str(left_path), str(right_path), warnings


def rerun_manual(img_path, output_dir, prefix='frame_'):
    """手动重新裁切单张图片"""
    img = cv2.imread(str(img_path))
    if img is None:
        raise ValueError(f"无法读取图像: {img_path}")

    height, width = img.shape[:2]
    print(f"图像尺寸: {width}x{height}")
    print("框选左侧照片区域，然后框选右侧照片区域，按Esc取消")

    display_img = img.copy()
    regions = []
    current_rect = [0, 0, 0, 0]
    drawing = False

    def mouse_callback(event, x, y, flags, param):
        nonlocal drawing, current_rect, display_img

        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            current_rect = [x, y, x, y]
            display_img = img.copy()
            for i, rect in enumerate(regions):
                label = "左侧" if i == 0 else "右侧"
                cv2.rectangle(display_img, (rect[0], rect[1]), (rect[2], rect[3]), (0, 255, 0), 2)
                cv2.putText(display_img, f"{label}", (rect[0], rect[1]-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                display_img = img.copy()
                for i, rect in enumerate(regions):
                    label = "左侧" if i == 0 else "右侧"
                    cv2.rectangle(display_img, (rect[0], rect[1]), (rect[2], rect[3]), (0, 255, 0), 2)
                    cv2.putText(display_img, f"{label}", (rect[0], rect[1]-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.rectangle(display_img, (current_rect[0], current_rect[1]), (x, y), (0, 255, 255), 2)

        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            current_rect[2] = x
            current_rect[3] = y

            x1, y1 = min(current_rect[0], current_rect[2]), min(current_rect[1], current_rect[3])
            x2, y2 = max(current_rect[0], current_rect[2]), max(current_rect[1], current_rect[3])
            current_rect = [x1, y1, x2, y2]

            if len(regions) < 2:
                regions.append(current_rect.copy())
                display_img = img.copy()
                for i, rect in enumerate(regions):
                    label = "左侧" if i == 0 else "右侧"
                    cv2.rectangle(display_img, (rect[0], rect[1]), (rect[2], rect[3]), (0, 255, 0), 2)
                    cv2.putText(display_img, f"{label}", (rect[0], rect[1]-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.namedWindow('选择裁切区域')
    cv2.setMouseCallback('选择裁切区域', mouse_callback)

    while len(regions) < 2:
        cv2.imshow('选择裁切区域', display_img)
        key = cv2.waitKey(10) & 0xFF
        if key == 27:
            cv2.destroyAllWindows()
            print("取消操作")
            return None

    cv2.destroyAllWindows()

    pil_img = Image.open(img_path)
    stem = Path(img_path).stem

    left_crop = (regions[0][0], regions[0][1], regions[0][2], regions[0][3])
    left_img = pil_img.crop(left_crop)
    left_path = Path(output_dir) / f"{prefix}{stem}_L.jpg"
    left_img.save(left_path, quality=100, subsampling=0)

    right_crop = (regions[1][0], regions[1][1], regions[1][2], regions[1][3])
    right_img = pil_img.crop(right_crop)
    right_path = Path(output_dir) / f"{prefix}{stem}_R.jpg"
    right_img.save(right_path, quality=100, subsampling=0)

    print(f"已重新裁切: {left_path.name}, {right_path.name}")
    return str(left_path), str(right_path)


def process_directory(input_dir, output_dir, prefix='', use_sequence=True):
    """处理整个目录"""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']

    image_files = set()
    for ext in image_extensions:
        for f in input_dir.glob(f'*{ext}'):
            image_files.add(f)
        for f in input_dir.glob(f'*{ext.upper()}'):
            image_files.add(f)

    image_files = list(image_files)

    if not image_files:
        print(f"目录中没有图片文件: {input_dir}")
        return

    image_files = sorted(image_files)
    print(f"找到 {len(image_files)} 张图片")

    results = []
    error_files = []

    for i, image_file in enumerate(image_files):
        try:
            frame_number = 2 * i + 1 if use_sequence else None
            left_path, right_path, warnings = split_single_frame(
                image_file, output_dir, frame_number=frame_number, prefix=prefix
            )
            results.append({
                'index': i + 1,
                'left': left_path,
                'right': right_path,
                'warnings': warnings
            })
            if warnings:
                error_files.append(image_file.name)
        except Exception as e:
            print(f"处理失败 {image_file.name}: {e}")
            error_files.append(image_file.name)

    print(f"\n{'='*50}")
    print(f"处理完成: {len(results)}/{len(image_files)} 张")
    print(f"{'='*50}")

    if error_files:
        print(f"\n⚠️ 需要手动检查: {error_files}")
        print("  使用 --rerun <文件名> 重新裁切")

    return results, error_files


def main():
    parser = argparse.ArgumentParser(description='半格胶片裁切工具')
    parser.add_argument('input', help='输入文件或目录')
    parser.add_argument('--output', '-o', default='./output/', help='输出目录')
    parser.add_argument('--prefix', default='', help='输出文件前缀')
    parser.add_argument('--no-sequence', action='store_true', help='不使用连续编号')
    parser.add_argument('--rerun', '-r', help='手动重新裁切指定文件')

    args = parser.parse_args()

    input_path = Path(args.input)

    if args.rerun:
        rerun_file = Path(args.rerun)
        if not rerun_file.exists():
            rerun_file = Path(args.output) / args.rerun

        if not rerun_file.exists():
            print(f"文件不存在: {args.rerun}")
            sys.exit(1)

        rerun_manual(rerun_file, args.output, args.prefix)
        return

    if not input_path.exists():
        print(f"错误: 输入路径不存在: {input_path}")
        sys.exit(1)

    use_sequence = not args.no_sequence

    if input_path.is_file():
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        if use_sequence:
            split_single_frame(input_path, output_dir, frame_number=1, prefix=args.prefix)
        else:
            split_single_frame(input_path, output_dir, prefix=args.prefix)
    elif input_path.is_dir():
        process_directory(input_path, args.output, prefix=args.prefix, use_sequence=use_sequence)


if __name__ == '__main__':
    main()
