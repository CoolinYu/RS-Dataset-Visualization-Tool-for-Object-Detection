# RS Detection Viewer (遥感图像目标检测可视化工具)

![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-green)

一个基于 Python (Tkinter) 开发的轻量级、交互式遥感图像目标检测数据集可视化工具。
专为 Windows 10/11 设计，支持 **DOTA**, **VisDrone**, **AI-TOD** 等主流遥感数据集格式。

## ✨ 主要功能 (Features)

* **多数据集支持**：内置支持 AI-TOD、DOTA (OBB/HBB)、VisDrone2019 数据集解析。
* **交互式筛选**：
    * 支持**鼠标点击**图片上的目标直接选中/取消选中。
    * 右侧列表支持全选、清空、滚动查看。
* **高度自定义绘图**：
    * 支持自定义边框颜色。
    * 支持 **实线 / 虚线 / 点线** 切换。
    * 支持调节线条粗细。
    * 支持显示/隐藏类别标签。
* **DOTA 专属支持**：支持 DOTA 数据集的 **旋转框 (OBB)** 和 **水平外接框 (HBB)** 两种展示模式。
* **高清保存**：基于原图分辨率进行绘制和保存，拒绝截图造成的模糊。
* **智能解析**：自动处理不同数据集的格式差异（如 VisDrone 的多余逗号、DOTA 的头部信息过滤）。

## 🛠️ 安装与依赖 (Installation)

本项目完全基于 Python 标准库开发，唯一的第三方依赖是图像处理库 `Pillow`。

1.  **克隆仓库**
    ```bash
    git clone [https://github.com/你的用户名/你的仓库名.git](https://github.com/你的用户名/你的仓库名.git)
    cd 你的仓库名
    ```

2.  **安装依赖**
    ```bash
    pip install pillow
    ```

## 🚀 快速开始 (Usage)

1.  运行主程序：
    ```bash
    python main.py
    ```
2.  在左侧面板选择 **数据集类型** (例如 VisDrone2019)。
3.  点击 **"📂 图片"** 加载 `.jpg` / `.png` 图像。
4.  点击 **"📝 标注"** 加载对应的 `.txt` 标注文件。
5.  **交互操作**：
    * 点击图片上的方框区域，可快速隐藏/显示该目标。
    * 在右侧面板调整颜色、线型、线宽。
    * 点击底部 **"▶ 展示"** 刷新视图。
6.  点击 **"💾 保存"** 将带有标注的图片保存到本地。

## 📂 项目结构 (File Structure)

```text
RS_Viewer/
├── main.py       # 主程序入口，包含 UI 布局与交互逻辑
├── drawer.py     # 绘图模块，负责实线/虚线绘制算法
├── parsers.py    # 解析模块，处理不同数据集的文本格式
└── README.md     # 项目说明文档
```
## ⚠️ 声明 (Disclaimer)
本项目遵循 GPL-3.0 开源协议。

本项目仅供学术研究、个人学习及非商业用途使用。

未经作者许可，严禁将本项目中的代码逻辑直接用于闭源商业软件。

如果您修改了本项目并发布，请务必开源您的修改部分。

Created by Colin_Yu
