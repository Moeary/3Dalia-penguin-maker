# 🐧 企鹅表情包制作工具 (Penguin Meme Maker)

一个基于 Vue 3 + Vite 的在线表情包制作工具，支持拖拽文字、自定义字体颜色、导出图片等功能。

郑重申明,本项目的表情包来源于网络,如有侵权我将立马删除

## 🚀 在线使用

本项目已部署在 [Vercel](https://3dalia-penguin-maker.vercel.app/ ) 上，可直接访问。
![](https://raw.githubusercontent.com/Moeary/pic_bed/main/img/202511260954885.png)
**访问验证：**
为了防止滥用，进入网站前需要进行简单的填空验证。
- 题目：高雅"__ " / 恶俗"__ "
- 答案：`人士` 或 `企鹅` （即双引号内的内容）

### 使用说明
1. 点击左侧的表情包库里面的任何一个图片
2. 点击下方的文字工具
3. 在cavans中间单击一次,出现文字输入框,键入文字
4. 再点击下方的文字工具,取消选择
5. 鼠标长按文字框即可拖动,双击文字框即可重新编辑
6. 点击下方导出按钮即可导出webp格式图片,点击复制按钮即可复制jpeg格式的表情包方便qq群斗图等作用

## 🛠️ 本地开发与部署

如果你想在本地运行或自行部署，请按照以下步骤操作。

### 环境要求
- **Node.js**: `v22.21.1` (推荐使用此版本以确保兼容性)

### 安装与运行

1. **克隆项目**
   ```bash
   git clone https://github.com/Moeary/3Dalia-penguin-maker.git
   cd 3Dalia-penguin-maker
   ```

2. **安装依赖**
   ```bash
   npm install
   ```

3. **启动开发服务器**
   ```bash
   npm run dev
   ```
   访问终端显示的地址（通常是 `http://localhost:5173`）。

4. **构建生产版本**
   ```bash
   npm run build
   ```

## 🎨 自定义表情包库 (Meme Base)

如果你想替换默认的企鹅表情包，制作属于自己的表情包生成器，可以按照以下步骤操作：

### 1. 准备图片
准备好你想要使用的图片素材（支持 `.jpg`, `.png`, `.webp` 等格式）。

### 2. 替换图片文件
将你的图片文件放入 `public/meme-base` 文件夹中。
*注意：请先清空该文件夹中原有的图片。*

### 3. 生成清单文件
运行提供的 Python 脚本来自动生成表情包清单 (`meme-manifest.json`)。

```bash
# 确保你已安装 Python 3
python scripts/generate_manifest.py
```

该脚本会扫描 `public/meme-base` 目录下的所有图片，并在 `public/meme-manifest.json` 中生成索引。前端页面会自动读取这个文件来展示表情包列表。

### 4. (可选) 批量处理脚本
如果你有大量原始图片需要裁剪水印或转换格式，可以使用 `scripts/crop_and_convert.py`。
*需自行修改脚本中的 `source_dir` 和 `output_folder` 路径以适配你的文件夹结构。*

## 🎈TODOLIST

1. 键盘快捷键完善,比如按T切换文本模式,再按一次取消文本模式
2. 考虑使用CDN存储表情包图片,加速访问
3. 在QQ群里面大肆宣传(逃

## 📄 License

MIT License
