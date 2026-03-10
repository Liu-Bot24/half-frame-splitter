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


def enhance_image(img_gray):
    """图像增强：提高对比度"""
    img_float = img_gray.astype(np.float32)
    min_val = np.percentile(img_float, 2)
    max_val = np.percentile(img_float, 98)

    if max_val > min_val:
        enhanced = (img_float - min_val) / (max_val - min_val) * 255
        enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)
    else:
        enhanced = img_gray

    enhanced = cv2.convertScaleAbs(enhanced, alpha=1.5, beta=0)
    return enhanced


def find_black_gap_by_curve(img_gray):
    """曲线法：分析边缘密度曲线，找到最平坦的区域"""
    w = img_gray.shape[1]

    edges = cv2.Canny(img_gray, 30, 100)
    edge_density = np.sum(edges > 0, axis=0)

    search_start = w // 4
    search_end = 3 * w // 4

    window_size = 60
    min_score = float('inf')
    best_start = search_start

    for start in range(search_start, search_end - window_size):
        window = edge_density[start:start + window_size]
        mean_val = np.mean(window)
        std_val = np.std(window)
        score = mean_val + std_val * 0.5

        if score < min_score:
            min_score = score
            best_start = start

    gap_start = best_start
    gap_end = best_start + window_size

    return gap_start, gap_end


def find_black_gap_basic(img_gray):
    """基础方法：用阈值找黑缝边界"""
    w = img_gray.shape[1]

    edges = cv2.Canny(img_gray, 30, 100)
    edge_density = np.sum(edges > 0, axis=0)

    search_start = w // 4
    search_end = 3 * w // 4

    min_density = float('inf')
    min_col = w // 2
    for col in range(search_start, search_end):
        if edge_density[col] < min_density:
            min_density = edge_density[col]
            min_col = col

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

    return gap_start, gap_end


def rerun_manual(img_path, output_dir, prefix='frame_'):
    """手动重新裁切单张图片"""
    img = cv2.imread(str(img_path))
    if img is None:
        raise ValueError(f"无法读取图像: {img_path}")

    height, width = img.shape[:2]
    print(f"图像尺寸: {width}x{height}")
    print("框选左侧照片区域，然后框选右侧照片区域，按Esc取消")

    # 缩放图像以适应屏幕
    try:
        import ctypes
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
    except:
        screen_width = 1920
        screen_height = 1080

    scale = min(1.0, min(screen_width * 0.9 / width, screen_height * 0.9 / height))
    display_w = int(width * scale)
    display_h = int(height * scale)
    scale_x = width / display_w
    scale_y = height / display_h

    display_img = cv2.resize(img.copy(), (display_w, display_h))
    regions = []
    current_rect = [0, 0, 0, 0]
    drawing = False

    def mouse_callback(event, x, y, flags, param):
        nonlocal drawing, current_rect, display_img

        real_x = int(x * scale_x)
        real_y = int(y * scale_y)

        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            current_rect = [real_x, real_y, real_x, real_y]
            display_img = cv2.resize(img.copy(), (display_w, display_h))
            for i, rect in enumerate(regions):
                label = "左侧" if i == 0 else "右侧"
                scaled_rect = (int(rect[0] * scale), int(rect[1] * scale), int(rect[2] * scale), int(rect[3] * scale))
                cv2.rectangle(display_img, (scaled_rect[0], scaled_rect[1]), (scaled_rect[2], scaled_rect[3]), (0, 255, 0), 2)
                cv2.putText(display_img, f"{label}", (scaled_rect[0], max(0, scaled_rect[1]-10)),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7 * max(scale, 0.5), (0, 255, 0), 2)

        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                display_img = cv2.resize(img.copy(), (display_w, display_h))
                for i, rect in enumerate(regions):
                    label = "左侧" if i == 0 else "右侧"
                    scaled_rect = (int(rect[0] * scale), int(rect[1] * scale), int(rect[2] * scale), int(rect[3] * scale))
                    cv2.rectangle(display_img, (scaled_rect[0], scaled_rect[1]), (scaled_rect[2], scaled_rect[3]), (0, 255, 0), 2)
                    cv2.putText(display_img, f"{label}", (scaled_rect[0], max(0, scaled_rect[1]-10)),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7 * max(scale, 0.5), (0, 255, 0), 2)
                cv2.rectangle(display_img,
                             (int(current_rect[0] * scale), int(current_rect[1] * scale)),
                             (int(real_x * scale), int(real_y * scale)),
                             (0, 255, 255), 2)

        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            current_rect[2] = real_x
            current_rect[3] = real_y

            x1, y1 = min(current_rect[0], current_rect[2]), min(current_rect[1], current_rect[3])
            x2, y2 = max(current_rect[0], current_rect[2]), max(current_rect[1], current_rect[3])
            current_rect = [x1, y1, x2, y2]

            if len(regions) < 2:
                regions.append(current_rect.copy())
                display_img = cv2.resize(img.copy(), (display_w, display_h))

    cv2.namedWindow('选择裁切区域', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('选择裁切区域', display_w, display_h)
    cv2.setMouseCallback('选择裁切区域', mouse_callback)

    while len(regions) < 2:
        cv2.imshow('选择裁切区域', display_img)
        key = cv2.waitKey(10) & 0xFF
        if key == 27:
            cv2.destroyAllWindows()
            print("取消操作")
            return None

    cv2.destroyAllWindows()
    cv2.waitKey(1)

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

    single_file_fallback = None
    if len(image_files) == 1:
        img = cv2.imread(str(image_files[0]))
        if img is not None:
            single_file_fallback = img.shape[1] // 2

    results = []
    failed_files = []
    all_widths = []

    for i, image_file in enumerate(image_files):
        try:
            frame_number = 2 * i + 1 if use_sequence else None
            fallback_width = single_file_fallback
            left_path, right_path, warnings, used_width, method_used = split_single_frame(
                image_file, output_dir, frame_number=frame_number, prefix=prefix, fallback_width=fallback_width, return_width=True
            )
            results.append({
                'index': i + 1,
                'original_name': image_file.name,
                'left': left_path,
                'right': right_path,
                'warnings': warnings,
                'width': used_width,
                'method': method_used
            })
            all_widths.append(used_width)
        except Exception as e:
            error_msg = str(e)
            if "vs" in error_msg:
                parts = error_msg.split(": ")[-1]
                print(f"处理失败 {image_file.name}: {parts}")
                print(f"偏差过大，统一处理")
            else:
                print(f"处理失败 {image_file.name}: {e}")
            failed_files.append((image_file.name, image_file, 2 * i + 1 if use_sequence else None))

    if failed_files and not all_widths:
        print(f"\n错误: 所有图片识别失败，无法自动裁剪，建议手动操作")
        return results, failed_files

    if failed_files and all_widths:
        avg_width = sum(all_widths) // len(all_widths)
        print(f"\n{'='*50}")
        print(f"统一处理")
        print(f"{'='*50}")

        for original_name, image_file, frame_number in failed_files:
            try:
                left_path, right_path, warnings, _, method_used = split_single_frame(
                    image_file, output_dir, frame_number=frame_number, prefix=prefix, fallback_width=avg_width, return_width=True
                )
                results.append({
                    'index': 0,
                    'original_name': image_file.name,
                    'left': left_path,
                    'right': right_path,
                    'warnings': ["使用平均宽度裁剪"],
                    'width': avg_width,
                    'method': method_used
                })
            except Exception as e:
                print(f"平均宽度裁剪失败 {image_file.name}: {e}")

    print(f"\n{'='*50}")
    print(f"处理完成: {len(results)}/{len(image_files)} 张")
    print(f"{'='*50}")

    enhance_list = [r for r in results if '图像增强' in r.get('warnings', [])]
    curve_list = [r for r in results if '曲线法' in r.get('warnings', [])]
    center_list = [r for r in results if r.get('method') == '居中拆分']
    avg_list = [r for r in results if r.get('method') == '平均宽度裁剪']

    if enhance_list:
        print(f"\n⚠️ 以下图片自动识别失败，经过图像增强处理后进行裁剪，建议人工检查确认:")
        for r in enhance_list:
            left_name = r['left'].split('/')[-1].split('\\')[-1]
            right_name = r['right'].split('/')[-1].split('\\')[-1]
            print(f"  {left_name}, {right_name} (原文件: {r['original_name']})")

    if curve_list:
        print(f"\n⚠️ 以下图片自动识别失败，经过连续边缘密度检测后进行裁剪，建议人工检查确认:")
        for r in curve_list:
            left_name = r['left'].split('/')[-1].split('\\')[-1]
            right_name = r['right'].split('/')[-1].split('\\')[-1]
            print(f"  {left_name}, {right_name} (原文件: {r['original_name']})")

    if center_list:
        print(f"\n⚠️ 以下图片自动识别失败，使用居中拆分方式进行裁剪，建议人工检查确认:")
        for r in center_list:
            left_name = r['left'].split('/')[-1].split('\\')[-1]
            right_name = r['right'].split('/')[-1].split('\\')[-1]
            print(f"  {left_name}, {right_name} (原文件: {r['original_name']})")

    if avg_list:
        print(f"\n⚠️ 以下图片自动识别失败，使用了平均图片输出宽度进行裁剪，建议人工检查确认:")
        for r in avg_list:
            left_name = r['left'].split('/')[-1].split('\\')[-1]
            right_name = r['right'].split('/')[-1].split('\\')[-1]
            print(f"  {left_name}, {right_name} (原文件: {r['original_name']})")

    return results, []


def split_single_frame(img_path, output_dir, frame_number=None, prefix='', fallback_width=None, return_width=False, verbose=True):
    """裁切单张半格胶片扫描图"""
    img = cv2.imread(str(img_path))
    if img is None:
        raise ValueError(f"无法读取图像: {img_path}")

    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = img_gray.shape

    original_name = Path(img_path).name

    if verbose:
        print(f"\n处理: {original_name}")
        print(f"图像尺寸: {w}x{h}")

    method_used = "基础方法"

    is_first_frame = (frame_number is not None and frame_number == 1)
    if is_first_frame:
        edges = cv2.Canny(img_gray, 30, 100)
        edge_density = np.sum(edges > 0, axis=0)

        left_half = np.mean(edge_density[:w//2])
        right_half = np.mean(edge_density[w//2:])

        if left_half < 10 and right_half > 50:
            threshold = max(right_half * 0.3, 20)
            frame2_start = w // 2
            for col in range(w // 2, w):
                if edge_density[col] > threshold:
                    frame2_start = col
                    break

            frame2_width = w - frame2_start
            frame1_end = frame2_start - 5

            gap_start = frame1_end
            gap_end = frame2_start
            left_width = frame1_end
            right_width = frame2_width
            width_ratio = 1.0
            method_used = "片头处理"
        else:
            gap_start, gap_end = find_black_gap_basic(img_gray)
            left_width = gap_start
            right_width = w - 1 - gap_end
            width_ratio = min(left_width, right_width) / max(left_width, right_width) if max(left_width, right_width) > 0 else 0
    else:
        gap_start, gap_end = find_black_gap_basic(img_gray)
        left_width = gap_start
        right_width = w - 1 - gap_end
        width_ratio = min(left_width, right_width) / max(left_width, right_width) if max(left_width, right_width) > 0 else 0

    if width_ratio >= 0.85:
        method_used = "基础方法"
    else:
        enhanced = enhance_image(img_gray)
        gap_start2, gap_end2 = find_black_gap_basic(enhanced)
        left_width2 = gap_start2
        right_width2 = w - 1 - gap_end2
        width_ratio2 = min(left_width2, right_width2) / max(left_width2, right_width2) if max(left_width2, right_width2) > 0 else 0

        gap_start3, gap_end3 = find_black_gap_by_curve(img_gray)
        left_width3 = gap_start3
        right_width3 = w - 1 - gap_end3
        width_ratio3 = min(left_width3, right_width3) / max(left_width3, right_width3) if max(left_width3, right_width3) > 0 else 0

        if width_ratio2 >= 0.85 and width_ratio3 >= 0.85:
            if width_ratio2 >= width_ratio3:
                gap_start, gap_end = gap_start2, gap_end2
                left_width, right_width = left_width2, right_width2
                width_ratio = width_ratio2
                method_used = "图像增强"
            else:
                gap_start, gap_end = gap_start3, gap_end3
                left_width, right_width = left_width3, right_width3
                width_ratio = width_ratio3
                method_used = "曲线法"
        elif width_ratio2 >= 0.85:
            gap_start, gap_end = gap_start2, gap_end2
            left_width, right_width = left_width2, right_width2
            width_ratio = width_ratio2
            method_used = "图像增强"
        elif width_ratio3 >= 0.85:
            gap_start, gap_end = gap_start3, gap_end3
            left_width, right_width = left_width3, right_width3
            width_ratio = width_ratio3
            method_used = "曲线法"

    if width_ratio < 0.85 and fallback_width:
        if fallback_width == w // 2:
            gap_center = w // 2
            gap_start = gap_center
            gap_end = gap_center
            left_width = gap_start
            right_width = w - 1 - gap_end
            method_used = "居中拆分"
        else:
            avg_photo_width = fallback_width
            gap_start = avg_photo_width
            gap_end = w - avg_photo_width
            left_width = gap_start
            right_width = w - 1 - gap_end
            method_used = "平均宽度裁剪"
        width_ratio = 1.0

    if width_ratio < 0.85:
        raise ValueError(f"识别失败，偏差过大: {left_width} vs {right_width}")

    if verbose:
        print(f"黑缝区域: {gap_start} - {gap_end}")
        print(f"左侧: {left_width}px, 右侧: {right_width}px")

    warnings = []

    if method_used == "图像增强":
        warnings.append("图像增强")
    elif method_used == "曲线法":
        warnings.append("曲线法")

    pil_img = Image.open(img_path)

    left_crop = (0, 0, gap_start, h)
    left_img = pil_img.crop(left_crop)

    right_crop = (gap_end + 1, 0, w, h)
    right_img = pil_img.crop(right_crop)

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

    used_width = left_width

    if return_width:
        return str(left_path), str(right_path), warnings, used_width, method_used
    return str(left_path), str(right_path), warnings, method_used


def main():
    parser = argparse.ArgumentParser(description='半格胶片裁切工具')
    parser.add_argument('input', help='输入文件或目录')
    parser.add_argument('--output', '-o', default='./output/', help='输出目录')
    parser.add_argument('--prefix', default='', help='输出文件前缀')
    parser.add_argument('--no-sequence', action='store_true', help='不使用连续编号')
    parser.add_argument('--rerun', '-r', action='store_true', help='手动重新裁切')

    args = parser.parse_args()

    input_path = Path(args.input)

    if args.rerun:
        if not input_path.exists():
            print(f"文件不存在: {input_path}")
            sys.exit(1)

        rerun_manual(input_path, args.output, args.prefix)
        return

    if not input_path.exists():
        print(f"错误: 输入路径不存在: {input_path}")
        sys.exit(1)

    use_sequence = not args.no_sequence
    process_directory(input_path, args.output, prefix=args.prefix, use_sequence=use_sequence)


if __name__ == '__main__':
    main()
