<div align="center">

# Half-Frame Splitter

![Stars](https://img.shields.io/github/stars/Liu-Bot24/half-frame-splitter?style=flat&label=Stars&cache=20260704) ![Forks](https://img.shields.io/github/forks/Liu-Bot24/half-frame-splitter?style=flat&label=Forks&cache=20260704) ![Views 14d](https://github-stats.liu-qi.cn/api/badge/Liu-Bot24/half-frame-splitter/views14d.svg?v=4) ![Clones 14d](https://github-stats.liu-qi.cn/api/badge/Liu-Bot24/half-frame-splitter/clones14d.svg?v=4)

Languages: [简体中文](README.md) · [English](README-en.md)

</div>

Smartly recognize the black gap in scanned half-frame film photos and automatically extract individual images.

## System Requirements

Python 3.x, requiring the following installation:
```bash
pip install -r requirements.txt
```

## Quick Start

### Method 1: Double-click to run
1. Place scanned images into the `input` folder.
2. Double-click `裁切.bat`.
3. Results will be saved in the `output` folder.

### Method 2: Command Line
```bash
pip install -r requirements.txt
python main.py ./scanned_images/ -o ./output_directory/
```

## Features

- **Smart Gap Detection**: Automatically identifies the position of the black gap in the middle of scanned photos.
- **Edge Density Analysis**: Accurately extracts the image frame.
- **Sequential Numbering**: Outputs sequential numbers like 01, 02, 03, 04... based on file sorting order.
- **Anomaly Alerts**: Alerts the user for manual inspection when suspicious results are detected.
- **Manual Resplitting**: Supports specifying a file to manually redraw and split.
- **Multi-level Fault Tolerance**: Falls back to average width when automatic recognition fails.

## Parameters

| Parameter | Description |
|------|------|
| `input` | Input file or directory |
| `--output`, `-o` | Output directory (Default: `./output/`) |
| `--prefix` | Output file prefix |
| `--no-sequence` | Disable sequential numbering |
| `--rerun` | Manually resplit a specified file |

## Usage Examples

```bash
# Batch processing
python main.py ./scans/ -o ./output/

# Add prefix
python main.py ./scans/ -o ./output/ --prefix "film_"

# Manual resplit
python main.py ./scans/ -o ./output/ --rerun 03.jpg
```

## Output Description

- Input files are sorted by filename.
- Each half-frame film outputs two JPGs.
- Numbering rule: For the N-th film, left side = 2N-1, right side = 2N.
- An alert is displayed upon recognition failure, recommending manual inspection.

## Supported Formats

JPG, JPEG, PNG, BMP, TIFF, TIF
