import os

# VisDrone 官方类别映射 (根据你的数据样例补充了 0 和 11)
# 0 通常是 Ignored regions, 1-10 是标准目标
VISDRONE_CLASS_MAP = {
    '0': 'Ignore', '1': 'Pedestrian', '2': 'People', '3': 'Bicycle', '4': 'Car',
    '5': 'Van', '6': 'Truck', '7': 'Tricycle', '8': 'Awning-tricycle',
    '9': 'Bus', '10': 'Motor', '11': 'Others'
}


def clean_line(line):
    """
    通用行处理：
    1. 去除首尾空格
    2. 将逗号替换为空格 (解决 VisDrone 行末多逗号问题)
    3. 再次去除多余空格并分割
    """
    return line.strip().replace(',', ' ').split()


def parse_aitod(line_parts, img_w, img_h):
    """
    AI-TOD 格式样例: 479.0000 103.0000 494.0000 117.0000 ship
    解析: x1, y1, x2, y2, class_name
    """
    if len(line_parts) < 5:
        return None

    try:
        x1, y1, x2, y2 = map(float, line_parts[:4])
        class_name = line_parts[4]

        # 简单的边界检查 (AI-TOD 有时是微小目标，不做过于严格的过滤，只防越界)
        # 加上 +50 像素容错，防止某些标注稍微出界导致读取失败
        if x1 > img_w + 50 or y1 > img_h + 50:
            raise ValueError("Coordinates out of bounds")

        return {
            'type': 'box',
            'coords': [x1, y1, x2, y2],
            'class_name': class_name
        }
    except ValueError:
        return None


def parse_dota(line_parts, img_w, img_h):
    """
    DOTA 格式样例:
    (前两行) imagesource:GoogleEarth ...
    (数据行) 2753 2408 2861 2385 ... plane 0
    解析: x1, y1, x2, y2, x3, y3, x4, y4, category, difficulty
    """
    # 1. 过滤元数据行 (imagesource, gsd)
    # 检查第一个元素是否包含冒号或特定关键词
    first_item = line_parts[0].lower()
    if 'imagesource' in first_item or 'gsd' in first_item:
        return None

    # 2. 检查数据长度 (DOTA 至少要有 8个坐标 + 1个类别 = 9列)
    if len(line_parts) < 9:
        return None

    try:
        # 提取前8个坐标
        coords = [float(x) for x in line_parts[:8]]
        category = line_parts[8]

        # 边界检查 (DOTA图很大，且有时会有负坐标用于裁剪边缘，这里放宽限制)
        # 只要不是所有点都在图外即可
        # 这里不做严格抛出异常，只做记录

        return {
            'type': 'poly',
            'coords': coords,
            'class_name': category
        }
    except ValueError:
        return None


def parse_visdrone(line_parts, img_w, img_h):
    """
    VisDrone 格式样例: 85,386,83,42,1,4,0,0
    解析: x, y, w, h, score, category, ...
    """
    if len(line_parts) < 6:
        return None

    try:
        # VisDrone 前4位是 x,y,w,h
        x, y, w, h = map(float, line_parts[:4])
        # 第6位 (Index 5) 是类别
        cls_id = line_parts[5]

        x2, y2 = x + w, y + h

        # 映射类别名称
        class_name = VISDRONE_CLASS_MAP.get(str(cls_id), f"Class {cls_id}")

        return {
            'type': 'box',
            'coords': [x, y, x2, y2],
            'class_name': class_name
        }
    except ValueError:
        return None


# 注册解析器
DATASET_PARSERS = {
    'AI-TOD': parse_aitod,
    'DOTA': parse_dota,
    'VisDrone2019': parse_visdrone
}


def parse_label_file(file_path, dataset_type, img_size):
    img_w, img_h = img_size
    parser_func = DATASET_PARSERS.get(dataset_type)

    if not parser_func:
        raise ValueError(f"未知的解析类型: {dataset_type}")

    objects = []
    is_bounds_error = False

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for idx, line in enumerate(lines):
        line = line.strip()
        if not line: continue

        # 使用通用清理函数处理逗号和空格
        parts = clean_line(line)

        try:
            obj = parser_func(parts, img_w, img_h)
            if obj:
                obj['id'] = len(objects) + 1  # 重置 ID 顺序，排除被跳过的 header
                obj['raw_line'] = line
                objects.append(obj)
            # 如果 obj 是 None (比如 header 行)，则直接跳过，不报错

        except ValueError:
            is_bounds_error = True
        except Exception as e:
            print(f"解析行 {idx + 1} 失败: {e}")
            continue

    return objects, is_bounds_error