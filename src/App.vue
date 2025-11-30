<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElButton, ElSpace, ElSelect, ElOption, ElInputNumber, ElColorPicker } from 'element-plus'
import { Fold, Expand, Plus, Delete, DocumentCopy } from '@element-plus/icons-vue'
import MemeList from './components/MemeList.vue'
import CanvasEditor from './components/CanvasEditor.vue'
import ExportPanel from './components/ExportPanel.vue'

const isVerified = ref(false)
const authQuestion = ref({ q: '', a: '' })
const authAnswer = ref('')

const questions = [
  { q: '高雅', a: '人士' },
  { q: '恶俗', a: '企鹅' }
]

onMounted(() => {
  const verified = localStorage.getItem('meme-auth-verified')
  if (verified) {
    isVerified.value = true
  } else {
    const idx = Math.floor(Math.random() * questions.length)
    authQuestion.value = questions[idx]
  }
})

const checkAuth = () => {
  if (authAnswer.value.trim() === authQuestion.value.a) {
    isVerified.value = true
    localStorage.setItem('meme-auth-verified', 'true')
    ElMessage.success('验证通过')
  } else {
    ElMessage.error('回答错误')
    authAnswer.value = ''
  }
}

const selectedImage = ref(null)
const editorRef = ref(null)
const headerCollapsed = ref(false)
const textToolActive = ref(false)
const fontSize = ref(24)
const fontFamily = ref('Arial')
const textColor = ref('#000000')

const fontsOptions = [
  { label: 'Arial', value: 'Arial' },
  { label: '宋体', value: '宋体' },
  { label: '黑体', value: '黑体' },
  { label: 'Comic Sans', value: 'Comic Sans MS' },
  { label: 'Georgia', value: 'Georgia' },
  { label: 'Times New Roman', value: 'Times New Roman' },
  { label: 'Courier New', value: 'Courier New' },
]

const headerHeightVal = ref(100)
const isDraggingHeader = ref(false)
const startY = ref(0)
const startHeight = ref(0)

const headerHeight = computed(() => `${headerHeightVal.value}px`)

const onImageSelect = (imagePath) => {
  selectedImage.value = imagePath
  console.log('Selected meme:', imagePath)
}

const toggleHeader = () => {
  headerCollapsed.value = !headerCollapsed.value
  headerHeightVal.value = headerCollapsed.value ? 12 : 100
}

const startDragHeader = (e) => {
  isDraggingHeader.value = true
  startY.value = e.clientY
  startHeight.value = headerHeightVal.value
  document.addEventListener('mousemove', onDragHeader)
  document.addEventListener('mouseup', stopDragHeader)
  document.body.style.userSelect = 'none'
}

const onDragHeader = (e) => {
  if (!isDraggingHeader.value) return
  const delta = e.clientY - startY.value
  const newHeight = Math.max(12, Math.min(300, startHeight.value + delta))
  headerHeightVal.value = newHeight
  headerCollapsed.value = newHeight < 60
}

const stopDragHeader = () => {
  isDraggingHeader.value = false
  document.removeEventListener('mousemove', onDragHeader)
  document.removeEventListener('mouseup', stopDragHeader)
  document.body.style.userSelect = ''
}

const toggleTextTool = () => {
  textToolActive.value = !textToolActive.value
  editorRef.value?.toggleTextTool()
}

const onUndo = () => {
  editorRef.value?.undo()
}

const onRedo = () => {
  editorRef.value?.redo()
}

const onExport = () => {
  editorRef.value?.exportImage()
}

const onCopy = () => {
  editorRef.value?.copyImage()
}

const addText = () => {
  editorRef.value?.addTextToCanvas(textColor.value, fontSize.value, fontFamily.value)
}
</script>

<template>
  <div v-if="!isVerified" class="auth-container">
    <div class="auth-box">
      <h2>🔒 访问验证</h2>
      <p>为了防止滥用，请完成以下填空：</p>
      <div class="auth-question">
        <span>{{ authQuestion.q }}</span>
        <input 
          v-model="authAnswer" 
          class="auth-input"
          placeholder="" 
          @keyup.enter="checkAuth"
        />
      </div>
      <!-- 去掉提示内容 
      <p class="hint">提示：{{ authQuestion.q }}"{{ authQuestion.q === '高雅' ? '人士' : '企鹅' }}" (""内的内容即为正确答案)</p>
      -->
      <el-button type="primary" size="large" @click="checkAuth" style="margin-top: 20px; width: 100%">进入网站</el-button>
    </div>
  </div>

  <div v-else class="app-container">

    <!-- 可折叠标题栏 -->
    <!--标题栏也去掉了 有点丑 后面也不要再改了
    <header class="header" :class="{ collapsed: headerCollapsed }" :style="{ height: headerHeight }">
      <div class="header-content">
        <div class="title-section">
          <h1>🐧 企鹅表情包制作工具</h1>
          <p v-if="!headerCollapsed" class="subtitle">Click to create amazing memes!</p>
        </div>
        <button class="collapse-btn" @click="toggleHeader" :title="headerCollapsed ? 'Show' : 'Hide'">
          <component :is="headerCollapsed ? Expand : Fold" />
        </button>
        </div>
        <div class="drag-handle" @mousedown="startDragHeader">
        <div class="handle-bar"></div>
      </div>
    </header>
    -->

    <!-- 主要内容区域 -->
    <div class="main-wrapper">
      <!-- 左侧表情包列表 -->
      <aside class="sidebar">
        <MemeList @select="onImageSelect" />
      </aside>

      <!-- 中间画布编辑器 -->
      <section class="editor-container">
        <CanvasEditor 
          ref="editorRef" 
          :image="selectedImage"
          :text-color="textColor"
          :font-size="fontSize"
          :font-family="fontFamily"
          @mode-change="(val) => textToolActive = val"
        />
      </section>

      <!-- 右侧导出面板 -->
      <!-- 不要改了 右侧导出面板不用了 太难看了 
      <aside class="export-panel">
        <ExportPanel 
          @export="onExport" 
          @copy="onCopy"
        />
      </aside>
      -->
    </div>

    <!-- 底部工具栏 -->
    <footer class="footer-toolbar">
      <el-space>
        <!-- 撤销重做 -->
        <el-button 
          size="small" 
          @click="onUndo"
          title="撤销"
        >
          ↶ 撤销
        </el-button>
        <el-button 
          size="small" 
          @click="onRedo"
          title="重做"
        >
          ↷ 重做
        </el-button>

        <div class="toolbar-divider"></div>

        <!-- 文字工具 -->
        <el-button 
          v-if="selectedImage"
          :type="textToolActive ? 'primary' : 'default'"
          size="small" 
          @click="toggleTextTool"
          :title="textToolActive ? '点击切换到元素操作模式' : '点击切换到文字输入模式'"
        >
          {{ textToolActive ? '📝 插入文字模式' : '👆 元素操作模式' }}
        </el-button>

        <!-- 字体大小 -->
        <div class="tool-group">
          <label>字号:</label>
          <el-input-number 
            v-model="fontSize" 
            :min="12" 
            :max="100" 
            size="small"
            style="width: 80px"
          />
        </div>

        <!-- 字体选择 -->
        <div class="tool-group">
          <label>字体:</label>
          <el-select 
            v-model="fontFamily" 
            size="small"
            style="width: 120px"
          >
            <el-option 
              v-for="font in fontsOptions" 
              :key="font.value" 
              :label="font.label" 
              :value="font.value"
            />
          </el-select>
        </div>

        <!-- 颜色选择 -->
        <div class="tool-group">
          <label>颜色:</label>
          <el-color-picker 
            v-model="textColor" 
            size="small"
            show-alpha
          />
        </div>

        <div class="toolbar-divider"></div>

        <!-- 导出按钮 -->
        <el-button 
          type="success" 
          size="small" 
          @click="onExport"
          title="导出为 WebP"
        >
          💾 导出
        </el-button>
        <el-button 
          type="info" 
          size="small" 
          @click="onCopy"
          title="复制为 JPEG"
        >
          📋 复制
        </el-button>
      </el-space>
    </footer>
  </div>
</template>

<style scoped>
* {
  box-sizing: border-box;
}

/* 验证页面样式 */
.auth-container {
  height: 100vh;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f0f2f5;
}

.auth-box {
  background: white;
  padding: 40px;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.1);
  text-align: center;
  width: 400px;
}

.auth-question {
  font-size: 24px;
  margin: 30px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-weight: bold;
  color: #333;
}

.auth-input {
  border: none;
  border-bottom: 2px solid #ddd;
  width: 100px;
  font-size: 24px;
  text-align: center;
  outline: none;
  padding: 5px;
  transition: border-color 0.3s;
}

.auth-input:focus {
  border-color: #409eff;
}

.hint {
  font-size: 12px;
  color: #999;
  margin-bottom: 20px;
}

/* 应用容器 */
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 标题栏样式 */
.header {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(240, 245, 250, 0.95) 100%);
  padding: 15px 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-bottom: 2px solid #667eea;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 100;
}

.header.collapsed {
  padding: 8px 15px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  gap: 15px;
  text-align: center;
}

.title-section h1 {
  margin: 0;
  color: #333;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 1px;
  transition: all 0.3s ease;
}

.header.collapsed .title-section h1 {
  font-size: 18px;
}

.title-section .subtitle {
  margin: 5px 0 0 0;
  color: #999;
  font-size: 12px;
  opacity: 0.8;
  transition: opacity 0.3s ease;
}

.header.collapsed .title-section .subtitle {
  display: none;
}

.collapse-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 20px;
  color: #667eea;
  padding: 5px 10px;
  border-radius: 4px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
}

.collapse-btn:hover {
  background: rgba(102, 126, 234, 0.1);
  transform: scale(1.1);
}

/* 主要内容区域 */
.main-wrapper {
  display: flex;
  flex: 1;
  gap: 12px;
  padding: 12px;
  overflow: hidden;
  min-height: 0;
}

/* 左侧栏 */
.sidebar {
  width: 280px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

/* 中间编辑器 */
.editor-container {
  flex: 1;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: auto;
  min-width: 400px;
  min-height: 400px;
}

/* 右侧导出面板 */
.export-panel {
  width: 240px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: auto;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

/* 底部工具栏 */
.footer-toolbar {
  background: rgba(255, 255, 255, 0.95);
  padding: 12px 20px;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.1);
  border-top: 1px solid #e0e0e0;
  overflow-x: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  flex-shrink: 0;
}

.toolbar-divider {
  width: 1px;
  height: 30px;
  background: #e0e0e0;
}

.tool-group {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.tool-group label {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

/* 拖拽手柄样式 */
.drag-handle {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 12px;
  cursor: ns-resize;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

.drag-handle:hover .handle-bar {
  background-color: #99a;
}

.handle-bar {
  width: 40px;
  height: 4px;
  background-color: #ddd;
  border-radius: 2px;
  transition: background-color 0.2s;
}

/* 响应式布局 */
@media (max-width: 1400px) {
  .main-wrapper {
    gap: 8px;
    padding: 8px;
  }

  .sidebar {
    width: 240px;
  }

  .export-panel {
    width: 200px;
  }
}

@media (max-width: 1000px) {
  .main-wrapper {
    flex-direction: column;
  }

  .sidebar,
  .export-panel {
    width: 100%;
    max-height: 150px;
  }

  .editor-container {
    min-width: 300px;
    flex-grow: 1;
  }

  .title-section h1 {
    font-size: 20px;
  }

  .header.collapsed .title-section h1 {
    font-size: 14px;
  }
}

@media (max-width: 600px) {
  .footer-toolbar {
    flex-wrap: wrap;
    gap: 8px;
    padding: 8px 10px;
  }

  .tool-group {
    gap: 4px;
  }

  .tool-group label {
    display: none;
  }
}
</style>
