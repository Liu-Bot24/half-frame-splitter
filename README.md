# 半格胶片裁切工具

智能识别半格胶片扫描照片中的黑缝，自动提取单张照片。

## 功能特点

- **智能黑缝检测**：自动识别扫描照片中间的黑缝位置
- **边缘密度分析**：精准提取照片画面
- **连续编号**：按文件排序顺序输出 01, 02, 03, 04... 编号
- **异常警告**：检测到可疑结果时提醒用户
- **手动重裁**：支持指定文件重新手动裁切

## 快速开始

### 方法一：双击运行
1. 将扫描图片放入 `input` 文件夹
2. 双击 `裁切.bat`
3. 结果保存在 `output` 文件夹

### 方法二：命令行
```bash
pip install -r requirements.txt
python main.py ./扫描图片/ -o ./输出目录/
```

## 参数说明

| 参数 | 说明 |
|------|------|
| `--output`, `-o` | 输出目录 (默认: ./output/) |
| `--prefix` | 输出文件前缀 |
| `--no-sequence` | 不使用连续编号 |
| `--rerun` | 手动重新裁切指定文件 |

## 使用示例

```bash
# 批量处理
python main.py ./scans/ -o ./output/

# 添加前缀
python main.py ./scans/ -o ./output/ --prefix "film_"

# 手动重裁错误文件
python main.py ./scans/ -o ./output/ --rerun 03.jpg
```

## 输出说明

- 输入文件按文件名排序
- 每张半格胶片输出两张 JPG
- 编号规则：第N张胶片的左侧=2N-1，右侧=2N

## 支持格式

JPG, JPEG, PNG, BMP, TIFF, TIF

## 环境要求

Python 3.x，需要安装：
```
pip install -r requirements.txt
```
