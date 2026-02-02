import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os

# 导入自定义模块
import parsers
import drawer

# 配置
COLORS = ['red', 'limegreen', 'lightblue', 'darkblue', 'orange', 'purple', 'gray', 'yellow']
LINE_STYLES = {'实线（Solid）': 'solid', '虚线（Loose）': 'dashed_loose', '点线（Dense）': 'dashed_dense'}
DATASETS = list(parsers.DATASET_PARSERS.keys())


class RSImageViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("RS Detection Viewer")
        self.root.geometry("1200x800")

        self.style = ttk.Style()
        self.style.theme_use('clam')

        # === 数据状态 ===
        self.current_image_path = None
        self.current_label_path = None
        self.pil_image_original = None
        self.pil_image_display = None
        self.tk_image = None
        self.objects = []

        # 渲染参数
        self.render_params = {'ratio': 1.0, 'offset_x': 0, 'offset_y': 0}

        self.setup_ui()

    def setup_ui(self):
        # ============================================
        # 1. 左侧栏 (设置与文件)
        # ============================================
        self.left_frame = ttk.Frame(self.root, width=220, padding=10)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)

        # -- 数据集 --
        lbl_group1 = ttk.LabelFrame(self.left_frame, text="数据集", padding=10)
        lbl_group1.pack(fill=tk.X, pady=5)

        self.dataset_var = tk.StringVar(value=DATASETS[0])
        for ds in DATASETS:
            ttk.Radiobutton(lbl_group1, text=ds, variable=self.dataset_var, value=ds,
                            command=self.on_dataset_switch).pack(anchor='w', pady=1)

        # -- 文件加载 --
        lbl_group2 = ttk.LabelFrame(self.left_frame, text="文件操作", padding=10)
        lbl_group2.pack(fill=tk.X, pady=10)

        ttk.Button(lbl_group2, text="📂 图片", command=self.load_image_dialog).pack(fill=tk.X, pady=(5, 2))
        self.ent_img_name = ttk.Entry(lbl_group2, state="readonly")
        self.ent_img_name.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(lbl_group2, text="📝 标注", command=self.load_label_dialog).pack(fill=tk.X, pady=(5, 2))
        self.ent_label_name = ttk.Entry(lbl_group2, state="readonly")
        self.ent_label_name.pack(fill=tk.X)

        # ============================================
        # 2. 右侧栏 (目标列表与绘图选项)
        # ============================================
        self.right_frame = ttk.Frame(self.root, width=170, padding=5)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # -- 绘图选项 --
        opt_group = ttk.LabelFrame(self.right_frame, text="绘图选项", padding=5)
        opt_group.pack(fill=tk.X, pady=5)
        # 颜色
        row1 = ttk.Frame(opt_group)
        row1.pack(fill=tk.X)
        ttk.Label(row1, text="颜色:").pack(side=tk.LEFT)
        self.color_var = tk.StringVar(value=COLORS[0])
        ttk.Combobox(row1, textvariable=self.color_var, values=COLORS, state="readonly", width=8).pack(side=tk.LEFT,
                                                                                              padx=5)
        # 线型
        row2 = ttk.Frame(opt_group)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="线型:").pack(side=tk.LEFT)
        self.line_style_var = tk.StringVar(value='实线（Solid）')
        ttk.Combobox(row2, textvariable=self.line_style_var, values=list(LINE_STYLES.keys()), state="readonly",
                     width=8).pack(side=tk.LEFT, padx=5)
        # 线宽
        row3 = ttk.Frame(opt_group)
        row3.pack(fill=tk.X, pady=2)
        ttk.Label(row3, text="线宽:").pack(side=tk.LEFT)
        self.line_width_var = tk.IntVar(value=2)
        ttk.Spinbox(row3, from_=1, to=10, textvariable=self.line_width_var, width=6).pack(side=tk.LEFT, padx=5)
        # 类别显示
        self.show_label_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_group, text="显示类别名", variable=self.show_label_var).pack(anchor='w', pady=2)
        # DOTA 框型
        self.dota_mode_frame = ttk.Frame(opt_group)
        self.dota_mode_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.dota_mode_frame, text="DOTA 框型:").pack(anchor='w')
        self.dota_style_var = tk.StringVar(value="OBB")
        ttk.Radiobutton(self.dota_mode_frame, text="旋转 (OBB)", variable=self.dota_style_var, value="OBB").pack(
            anchor='w')
        ttk.Radiobutton(self.dota_mode_frame, text="水平 (HBB)", variable=self.dota_style_var, value="HBB").pack(
            anchor='w')

        # -- 目标列表 --
        list_group = ttk.LabelFrame(self.right_frame, text="目标列表", padding=5)
        list_group.pack(fill=tk.BOTH, expand=True, pady=10)

        ctrl_frame = ttk.Frame(list_group)
        ctrl_frame.pack(fill=tk.X, pady=2)
        ttk.Button(ctrl_frame, text="全选", command=self.select_all, width=5).pack(side=tk.LEFT)
        ttk.Button(ctrl_frame, text="清空", command=self.deselect_all, width=5).pack(side=tk.RIGHT)

        list_container = ttk.Frame(list_group)
        list_container.pack(fill=tk.BOTH, expand=True, pady=5)

        self.obj_canvas = tk.Canvas(list_container, bg="white", width=160, height=300, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.obj_canvas.yview)

        self.scrollable_frame = ttk.Frame(self.obj_canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.obj_canvas.configure(scrollregion=self.obj_canvas.bbox("all"))
        )

        self.obj_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.obj_canvas.configure(yscrollcommand=scrollbar.set)

        self.obj_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.obj_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # ============================================
        # 3. 中间区域
        # ============================================
        self.center_frame = ttk.Frame(self.root)
        self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas_frame = tk.Frame(self.center_frame, bg="#333333", bd=2, relief=tk.SUNKEN)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="#333333", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        # 绑定鼠标左键交互
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        self.bottom_bar = ttk.Frame(self.center_frame, padding=10)
        self.bottom_bar.pack(side=tk.BOTTOM, fill=tk.X)

        btn_container = ttk.Frame(self.bottom_bar)
        btn_container.pack(anchor=tk.CENTER)

        style_btn = ttk.Style()
        style_btn.configure("Big.TButton", font=("Arial", 11, "bold"))

        ttk.Button(btn_container, text="▶ 展示 (Show)", style="Big.TButton", command=self.show_visualization,
                   width=15).pack(side=tk.LEFT, padx=15)
        ttk.Button(btn_container, text="💾 保存 (Save)", style="Big.TButton", command=self.save_image_dialog,
                   width=15).pack(side=tk.LEFT, padx=15)

    # ================= 逻辑处理 =================
    def on_canvas_click(self, event):
        """处理画布点击事件，实现点选物体"""
        if not self.objects or not self.pil_image_display:
            return

        # 1. 获取点击坐标
        cx, cy = event.x, event.y
        # 2. 转换为原图坐标
        ratio = self.render_params['ratio']
        off_x = self.render_params['offset_x']
        off_y = self.render_params['offset_y']

        if cx < off_x or cy < off_y:
            return
        img_x = (cx - off_x) / ratio
        img_y = (cy - off_y) / ratio
        # 3. 检测点击位置是否在某个目标内
        changed = False
        dota_hbb = (self.dota_style_var.get() == 'HBB' and self.dataset_var.get() == 'DOTA')
        for obj in self.objects:
            if self.is_point_in_object(img_x, img_y, obj, dota_hbb):
                current_val = obj['var'].get()
                obj['var'].set(not current_val)
                changed = True
        if changed:
            self.show_visualization()

    def is_point_in_object(self, x, y, obj, force_hbb=False):
        """碰撞检测算法"""
        corrds = obj['coords']
        if obj['type'] == 'box' or force_hbb:
            if obj['type'] == 'box':
                x1, y1, x2, y2 = corrds
            else:
                xs = corrds[::2]
                ys = corrds[1::2]
                x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
            return x1 <= x <= x2 and y1 <= y <= y2
        elif obj['type'] == 'poly':
            poly_points = list(zip(corrds[::2], corrds[1::2]))
            return self.point_in_polygon(x, y, poly_points)

    def point_in_polygon(self, x, y, polygon):
        """射线法检测点在多边形内"""
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside
    # ==========通用功能==========
    def set_entry_text(self, entry, text):
        entry.config(state='normal')
        entry.delete(0, tk.END)
        entry.insert(0, text)
        entry.config(state='readonly')

    def _on_mousewheel(self, event):
        x, y = self.root.winfo_pointerxy()
        widget = self.root.winfo_containing(x, y)
        if str(self.obj_canvas) in str(widget) or str(self.scrollable_frame) in str(widget):
            self.obj_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_dataset_switch(self):
        """核心修改：切换数据集时重新解析，但重置图片显示，不自动绘制"""
        self.update_ui_controls()

        if self.current_label_path:
            # 重新解析，这会更新右侧的目标列表
            self.process_labels()

            # 无论解析成功与否，都显示干净的原图，等待用户手动点击“展示”
            if self.pil_image_original:
                self.display_image(self.pil_image_original)

    def update_ui_controls(self):
        ds = self.dataset_var.get()
        if ds == 'DOTA':
            for child in self.dota_mode_frame.winfo_children():
                child.configure(state='normal')
        else:
            for child in self.dota_mode_frame.winfo_children():
                child.configure(state='disabled')

    def load_image_dialog(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.png;*.bmp;*.tif;*.jpeg")])
        if path:
            self.load_image(path)

    def load_image(self, path):
        try:
            self.pil_image_original = Image.open(path)
            self.current_image_path = path

            self.set_entry_text(self.ent_img_name, os.path.basename(path))

            self.current_label_path = None
            self.set_entry_text(self.ent_label_name, "未选择")
            self.clear_objects_ui()

            self.display_image(self.pil_image_original)
        except Exception as e:
            messagebox.showerror("错误", f"加载图片失败: {e}")

    def load_label_dialog(self):
        if not self.current_image_path:
            messagebox.showwarning("提示", "请先加载图片！")
            return
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
        if path:
            self.current_label_path = path
            self.set_entry_text(self.ent_label_name, os.path.basename(path))
            self.process_labels()

    def process_labels(self):
        if not self.pil_image_original: return

        dataset = self.dataset_var.get()
        img_size = self.pil_image_original.size

        self.clear_objects_ui()

        try:
            objects, is_bounds_error = parsers.parse_label_file(
                self.current_label_path, dataset, img_size
            )
            if is_bounds_error:
                if not messagebox.askyesno("警告", "部分坐标越界，可能文件不匹配或解析格式错误。\n是否继续加载？"):
                    self.objects = []
                    return

            self.objects = objects
            self.populate_list()
            # 这里不需要 display_image，由调用方(load_label 或 switch)决定

        except Exception as e:
            messagebox.showerror("解析错误", f"无法使用 {dataset} 格式解析当前文件。\n错误详情: {e}")
            self.objects = []

    def clear_objects_ui(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.objects = []
        self.obj_canvas.yview_moveto(0)

    def populate_list(self):
        if not self.objects:
            ttk.Label(self.scrollable_frame, text="无目标").pack()
            return

        for obj in self.objects:
            var = tk.BooleanVar(value=False)
            obj['var'] = var

            cls_name = obj['class_name']
            if len(cls_name) > 10: cls_name = cls_name[:8] + ".."

            text = f"#{obj['id']} {cls_name}"
            cb = tk.Checkbutton(self.scrollable_frame, text=text, variable=var, anchor='w', bg="white")
            cb.pack(fill=tk.X, pady=1, padx=2)

    def display_image(self, pil_img):
        if not pil_img: return
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10: cw, ch = 800, 600

        iw, ih = pil_img.size
        ratio = min(cw / iw, ch / ih)
        new_size = (int(iw * ratio), int(ih * ratio))

        offset_x = (cw - new_size[0]) // 2
        offset_y = (ch - new_size[1]) // 2

        self.render_params = {'ratio': ratio, 'offset_x': offset_x, 'offset_y': offset_y}

        self.pil_image_display = pil_img.resize(new_size, Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(self.pil_image_display)

        self.canvas.delete("all")
        self.canvas.create_image(cw // 2, ch // 2, anchor=tk.CENTER, image=self.tk_image)

    def show_visualization(self):
        if not self.pil_image_original: return

        color = self.color_var.get()
        show_lbl = self.show_label_var.get()
        dota_mode = self.dota_style_var.get()
        line_style_name = self.line_style_var.get()
        line_style = LINE_STYLES.get(line_style_name, 'solid')
        line_width = self.line_width_var.get()

        img_drawn, count = drawer.draw_on_image(
            self.pil_image_original,
            self.objects,
            color_name=color,
            show_labels=show_lbl,
            dota_mode=dota_mode,
            line_style=line_style,
            line_width=line_width
        )
        self.display_image(img_drawn)

    def save_image_dialog(self):
        if not self.pil_image_original: return
        path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPG", "*.jpg"), ("PNG", "*.png")])
        if path:
            color = self.color_var.get()
            show_lbl = self.show_label_var.get()
            dota_mode = self.dota_style_var.get()
            line_style_name = self.line_style_var.get()
            line_style = LINE_STYLES.get(line_style_name, 'solid')
            line_width = self.line_width_var.get()

            img_to_save, _ = drawer.draw_on_image(
                self.pil_image_original,
                self.objects,
                color_name=color,
                show_labels=show_lbl,
                dota_mode=dota_mode,
                line_style=line_style,
                line_width=line_width
            )
            try:
                img_to_save.save(path)
                messagebox.showinfo("成功", f"保存成功: {path}")
            except Exception as e:
                messagebox.showerror("失败", str(e))

    def select_all(self):
        for obj in self.objects: obj['var'].set(True)

    def deselect_all(self):
        for obj in self.objects: obj['var'].set(False)


if __name__ == "__main__":
    root = tk.Tk()
    app = RSImageViewer(root)

    def on_resize(event):
        if event.widget == app.canvas_frame:
            if hasattr(app, '_resize_job'): root.after_cancel(app._resize_job)
            app._resize_job = root.after(100, lambda: app.show_visualization() if app.objects else app.display_image(
                app.pil_image_original))


    root.bind("<Configure>", on_resize)
    root.mainloop()