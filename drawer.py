# drawer.py
import math

from PIL import ImageDraw, ImageFont


def draw_dashed_line(draw, p1, p2, width=1, dash_len=10, gap_len=5, color='red'):
    """
    在PIL ImageDraw上绘制虚线
    :param draw:
    :param p1: 起点
    :param p2: 终点
    """
    x1, y1 = p1
    x2, y2 = p2

    dx = x2 - x1
    dy = y2 - y1
    total_len = math.hypot(dx, dy)

    if total_len == 0:
        return

    vx = dx / total_len
    vy = dy / total_len

    current_dist = 0
    while current_dist < total_len:
        start_x = x1 + vx * current_dist
        start_y = y1 + vy * current_dist
        end_dist = min(current_dist + dash_len, total_len)
        end_x = x1 + vx * end_dist
        end_y = y1 + vy * end_dist

        draw.line([(start_x, start_y), (end_x, end_y)], fill=color, width=width)

        current_dist += (dash_len + gap_len)


def draw_on_image(pil_image, objects,
                  color_name='red',
                  show_labels=True,
                  dota_mode='OBB',
                  line_style='solid',
                  line_width=2):
    """
    在图片上绘制目标
    :param show_labels: 是否显示类别文字 (bool)
    :param dota_mode: DOTA数据集展示模式 'OBB' (旋转框) 或 'HBB' (水平外接框)
    """
    img_copy = pil_image.copy()
    draw = ImageDraw.Draw(img_copy)

    width, height = img_copy.size
    # line_width = max(2, int(width / 800))
    font_size = max(10, int(width / 800 * 5))

    font = None
    if show_labels:
        try:
            font = ImageFont.truetype("arial.ttf", size=font_size)
        except:
            pass

    # 设定虚线参数
    dash_params = None
    if line_style == 'dashed_loose':
        dash_params = (15, 10)
    elif line_style == 'dashed_dense':
        dash_params = (5, 5)

    draw_count = 0

    for obj in objects:
        if 'var' in obj and not obj['var'].get():
            continue

        draw_count += 1
        coords = obj['coords']
        label_text = f"{obj['class_name']}"

        # === 绘制逻辑分支 ===
        points_to_draw = []
        # 1. 普通矩形框 (AI-TOD, VisDrone)
        if obj['type'] == 'box':
            # draw.rectangle(coords, outline=color_name, width=line_width)
            x1, y1, x2, y2 = coords
            points_to_draw = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
            if show_labels:
                text_x = coords[0]
                text_y = coords[1] - font_size - 2
                if text_y < 0: text_y = coords[1]
                draw.text((text_x, text_y), label_text, fill=color_name, font=font)

        # 2. 多边形框 (DOTA)
        elif obj['type'] == 'poly':
            # DOTA 数据通常是 [x1, y1, x2, y2, x3, y3, x4, y4]

            # 如果用户选择 'HBB' (水平框)，则计算外接矩形
            if dota_mode == 'HBB':
                xs = coords[::2]
                ys = coords[1::2]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                points_to_draw = [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y), (min_x, min_y)]

                # draw.rectangle([min_x, min_y, max_x, max_y], outline=color_name, width=line_width)

                if show_labels:
                    draw.text((min_x, min_y - font_size - 2), label_text, fill=color_name, font=font)

            # 否则默认为 'OBB' (旋转框/多边形)
            else:
                poly_points = list(zip(coords[::2], coords[1::2]))
                if len(poly_points) >= 3:
                    points_to_draw = poly_points + [poly_points[0]]  # 闭合
                    # draw.line(poly_points_draw, fill=color_name, width=line_width)

                    if show_labels:
                        # 找最高点写字
                        top_point = min(poly_points, key=lambda p: p[1])
                        draw.text((top_point[0], top_point[1] - font_size - 2), label_text, fill=color_name, font=font)

        if not points_to_draw:
            continue

        if line_style == 'solid':
            draw.line(points_to_draw, fill=color_name, width=line_width)
        else:
            d_len, g_len = dash_params
            for i in range(len(points_to_draw) - 1):
                draw_dashed_line(draw, points_to_draw[i], points_to_draw[i + 1],
                                 width=line_width, dash_len=d_len, gap_len=g_len, color=color_name)

    return img_copy, draw_count