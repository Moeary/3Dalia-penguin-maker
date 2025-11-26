<script setup>
import { ref, watch, onMounted, onBeforeUnmount, computed, nextTick } from 'vue'
import { ElMessage, ElDialog, ElInput, ElColorPicker, ElInputNumber, ElSelect, ElOption } from 'element-plus'

const props = defineProps({
  image: String,
  textColor: {
    type: String,
    default: '#000000'
  },
  fontSize: {
    type: Number,
    default: 48
  },
  fontFamily: {
    type: String,
    default: 'Arial'
  }
})

const canvasRef = ref(null)
const canvas = ref(null)
const ctx = ref(null)

const baseImage = ref(null)
const imageLoaded = ref(false)

const texts = ref([])
const selectedTextId = ref(null)
const editingTextId = ref(null)

const isAddingText = ref(false)
const showTextDialog = ref(false)
const textInput = ref('')
const textInputX = ref(0)
const textInputY = ref(0)

const dialogColor = ref(props.textColor)
const dialogFont = ref(props.fontFamily)
const dialogSize = ref(props.fontSize)

const isDragging = ref(false)
const dragOffset = ref({ x: 0, y: 0 })

const contextMenu = ref({ visible: false, x: 0, y: 0, targetId: null })

const history = ref([])
const historyStep = ref(-1)

const canvasSize = computed(() => Math.min(window.innerWidth * 0.45, 640))

const initCanvas = () => {
  canvas.value = canvasRef.value
  if (!canvas.value) return
  ctx.value = canvas.value.getContext('2d', { willReadFrequently: true })
  const size = canvasSize.value
  canvas.value.width = size
  canvas.value.height = size
  drawCanvas()
}

const resizeListener = () => {
  if (!canvas.value) return
  const size = canvasSize.value
  canvas.value.width = size
  canvas.value.height = size
  drawCanvas()
}

onMounted(() => {
  initCanvas()
  window.addEventListener('resize', resizeListener)
  window.addEventListener('click', closeContextMenu)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeListener)
  window.removeEventListener('click', closeContextMenu)
})

const loadImage = (imagePath) => {
  if (!imagePath) {
    imageLoaded.value = false
    return
  }

  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => {
    baseImage.value = img
    imageLoaded.value = true
    
    nextTick(() => {
      initCanvas()
      texts.value = []
      selectedTextId.value = null
      editingTextId.value = null
      drawCanvas()
      resetHistory()
    })
  }
  img.onerror = () => {
    ElMessage.error('表情包加载失败')
    imageLoaded.value = false
  }
  img.src = imagePath.startsWith('/') ? imagePath : `/${imagePath}`
}

const drawCanvas = () => {
  if (!canvas.value || !ctx.value) return
  ctx.value.clearRect(0, 0, canvas.value.width, canvas.value.height)
  ctx.value.fillStyle = '#f0f0f0'
  ctx.value.fillRect(0, 0, canvas.value.width, canvas.value.height)

  if (baseImage.value && imageLoaded.value) {
    const imgW = baseImage.value.width
    const imgH = baseImage.value.height
    const scale = Math.min(canvas.value.width / imgW, canvas.value.height / imgH)
    const drawW = imgW * scale
    const drawH = imgH * scale
    const offsetX = (canvas.value.width - drawW) / 2
    const offsetY = (canvas.value.height - drawH) / 2
    ctx.value.drawImage(baseImage.value, offsetX, offsetY, drawW, drawH)
  }

  drawTexts()
}

const drawTexts = () => {
  if (!ctx.value) return
  ctx.value.save()
  texts.value.forEach(text => {
    ctx.value.font = `bold ${text.size}px ${text.font}`
    ctx.value.textAlign = 'center'
    ctx.value.textBaseline = 'middle'
    ctx.value.lineWidth = 4
    ctx.value.strokeStyle = 'rgba(255, 255, 255, 0.85)'
    ctx.value.strokeText(text.text, text.x, text.y)
    ctx.value.fillStyle = text.color
    ctx.value.fillText(text.text, text.x, text.y)

    if (text.id === selectedTextId.value) {
      const bounds = getTextBounds(text)
      if (bounds) {
        ctx.value.save()
        ctx.value.setLineDash([6, 4])
        ctx.value.strokeStyle = '#667eea'
        ctx.value.lineWidth = 2
        ctx.value.strokeRect(bounds.x, bounds.y, bounds.width, bounds.height)
        ctx.value.restore()
      }
    }
  })
  ctx.value.restore()
}

const cloneTexts = () => JSON.parse(JSON.stringify(texts.value))

const resetHistory = () => {
  history.value = []
  historyStep.value = -1
  saveHistory()
}

const saveHistory = () => {
  history.value = history.value.slice(0, historyStep.value + 1)
  history.value.push(cloneTexts())
  historyStep.value = history.value.length - 1
}

const restoreHistory = () => {
  if (historyStep.value < 0 || !history.value[historyStep.value]) return
  texts.value = JSON.parse(JSON.stringify(history.value[historyStep.value]))
  drawCanvas()
}

const undo = () => {
  if (historyStep.value <= 0) return
  historyStep.value -= 1
  restoreHistory()
}

const redo = () => {
  if (historyStep.value >= history.value.length - 1) return
  historyStep.value += 1
  restoreHistory()
}

const toggleTextTool = () => {
  isAddingText.value = !isAddingText.value
  if (canvas.value) {
    canvas.value.style.cursor = isAddingText.value ? 'crosshair' : 'default'
  }
  closeContextMenu()
}

const applyToolbarDefaults = () => {
  dialogColor.value = props.textColor
  dialogFont.value = props.fontFamily
  dialogSize.value = props.fontSize
}

const canvasClick = (event) => {
  if (!canvas.value) return
  const { x, y } = getCanvasCoordinates(event)

  if (isAddingText.value) {
    textInput.value = ''
    textInputX.value = x
    textInputY.value = y
    editingTextId.value = null
    applyToolbarDefaults()
    showTextDialog.value = true
    return
  }

  const target = getTextAtPosition(x, y)
  selectedTextId.value = target?.id ?? null
  drawCanvas()
}

const addTextToCanvas = (color = dialogColor.value, size = dialogSize.value, family = dialogFont.value) => {
  if (!textInput.value.trim()) {
    ElMessage.warning('请输入文字')
    return
  }

  const payload = {
    id: editingTextId.value ?? crypto.randomUUID?.() ?? `text-${Date.now()}`,
    text: textInput.value,
    x: textInputX.value,
    y: textInputY.value,
    color,
    size,
    font: family
  }

  if (editingTextId.value) {
    const idx = texts.value.findIndex(t => t.id === editingTextId.value)
    if (idx > -1) {
      texts.value[idx] = { ...texts.value[idx], ...payload }
    }
    ElMessage.success('文字已更新')
  } else {
    texts.value.push(payload)
    ElMessage.success('文字已添加')
  }

  selectedTextId.value = payload.id
  editingTextId.value = null
  showTextDialog.value = false
  textInput.value = ''
  drawCanvas()
  saveHistory()
}

const exportImage = () => {
  if (!canvas.value) return
  
  // 临时取消选中以隐藏虚线框
  const prevSelection = selectedTextId.value
  selectedTextId.value = null
  drawCanvas()

  canvas.value.toBlob(blob => {
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `meme-${Date.now()}.png`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('已导出 PNG')
    
    // 恢复选中状态
    selectedTextId.value = prevSelection
    drawCanvas()
  }, 'image/png')
}

const copyImage = async () => {
  if (!canvas.value) return
  
  // 临时取消选中以隐藏虚线框
  const prevSelection = selectedTextId.value
  selectedTextId.value = null
  drawCanvas()

  try {
    const blob = await new Promise(resolve => canvas.value.toBlob(resolve, 'image/png'))
    const data = [new ClipboardItem({ 'image/png': blob })]
    await navigator.clipboard.write(data)
    ElMessage.success('图片已复制')
  } catch (error) {
    console.error(error)
    ElMessage.error('复制失败: ' + error.message)
  } finally {
    // 恢复选中状态
    selectedTextId.value = prevSelection
    drawCanvas()
  }
}

const getCanvasCoordinates = (event) => {
  const rect = canvas.value.getBoundingClientRect()
  const scaleX = canvas.value.width / rect.width
  const scaleY = canvas.value.height / rect.height
  return {
    x: (event.clientX - rect.left) * scaleX,
    y: (event.clientY - rect.top) * scaleY
  }
}

const getTextBounds = (text) => {
  if (!ctx.value) return null
  ctx.value.font = `bold ${text.size}px ${text.font}`
  const metrics = ctx.value.measureText(text.text)
  const width = metrics.width
  const height = text.size * 1.2
  return {
    x: text.x - width / 2 - 6,
    y: text.y - height / 2 - 6,
    width: width + 12,
    height: height + 12
  }
}

const getTextAtPosition = (x, y) => {
  for (let i = texts.value.length - 1; i >= 0; i -= 1) {
    const bounds = getTextBounds(texts.value[i])
    if (bounds && x >= bounds.x && x <= bounds.x + bounds.width && y >= bounds.y && y <= bounds.y + bounds.height) {
      return texts.value[i]
    }
  }
  return null
}

const onMouseDown = (event) => {
  if (!canvas.value || isAddingText.value) return
  const { x, y } = getCanvasCoordinates(event)
  const target = getTextAtPosition(x, y)
  if (target) {
    selectedTextId.value = target.id
    dragOffset.value = { x: x - target.x, y: y - target.y }
    isDragging.value = true
    canvas.value.style.cursor = 'grabbing'
    closeContextMenu()
  } else {
    selectedTextId.value = null
  }
  drawCanvas()
}

const onMouseMove = (event) => {
  if (!isDragging.value || !canvas.value) return
  const { x, y } = getCanvasCoordinates(event)
  const target = texts.value.find(t => t.id === selectedTextId.value)
  if (!target) return
  target.x = x - dragOffset.value.x
  target.y = y - dragOffset.value.y
  drawCanvas()
}

const onMouseUp = () => {
  if (!isDragging.value) return
  isDragging.value = false
  canvas.value.style.cursor = 'default'
  drawCanvas()
  saveHistory()
}

const onDoubleClick = (event) => {
  if (!canvas.value) return
  const { x, y } = getCanvasCoordinates(event)
  const target = getTextAtPosition(x, y)
  if (target) {
    startEditingText(target)
  }
}

const startEditingText = (text) => {
  editingTextId.value = text.id
  textInput.value = text.text
  textInputX.value = text.x
  textInputY.value = text.y
  dialogColor.value = text.color
  dialogFont.value = text.font
  dialogSize.value = text.size
  showTextDialog.value = true
}

const onContextMenu = (event) => {
  event.preventDefault()
  if (!canvas.value) return
  const { x, y } = getCanvasCoordinates(event)
  const target = getTextAtPosition(x, y)
  if (target) {
    selectedTextId.value = target.id
    contextMenu.value = {
      visible: true,
      x: event.clientX,
      y: event.clientY,
      targetId: target.id
    }
    drawCanvas()
  } else {
    closeContextMenu()
  }
}

const closeContextMenu = () => {
  if (!contextMenu.value.visible) return
  contextMenu.value.visible = false
  contextMenu.value.targetId = null
}

const deleteSelectedText = () => {
  if (!contextMenu.value.targetId) return
  texts.value = texts.value.filter(t => t.id !== contextMenu.value.targetId)
  if (selectedTextId.value === contextMenu.value.targetId) {
    selectedTextId.value = null
  }
  closeContextMenu()
  drawCanvas()
  saveHistory()
  ElMessage.success('文字已删除')
}

const editSelectedText = () => {
  const target = texts.value.find(t => t.id === contextMenu.value.targetId)
  if (!target) return
  closeContextMenu()
  startEditingText(target)
}

watch(() => props.image, (value) => {
  if (value) {
    loadImage(value)
  }
})

watch(() => props.textColor, (value) => {
  if (!showTextDialog.value || editingTextId.value) return
  dialogColor.value = value
})

watch(() => props.fontSize, (value) => {
  if (!showTextDialog.value || editingTextId.value) return
  dialogSize.value = value
})

watch(() => props.fontFamily, (value) => {
  if (!showTextDialog.value || editingTextId.value) return
  dialogFont.value = value
})

defineExpose({
  undo,
  redo,
  exportImage,
  copyImage,
  toggleTextTool,
  addTextToCanvas
})
</script>

<template>
  <div class="canvas-editor">
    <div v-if="!imageLoaded" class="placeholder">
      <p>👈 从左侧选择一张表情包</p>
    </div>

    <canvas
      v-else
      ref="canvasRef"
      class="canvas"
      :class="{ 'text-mode': isAddingText }"
      @click="canvasClick"
      @mousedown="onMouseDown"
      @mousemove="onMouseMove"
      @mouseup="onMouseUp"
      @mouseleave="onMouseUp"
      @dblclick="onDoubleClick"
      @contextmenu="onContextMenu"
    />

    <div
      v-if="contextMenu.visible"
      class="context-menu"
      :style="{ top: `${contextMenu.y}px`, left: `${contextMenu.x}px` }"
      @click.stop
    >
      <button @click="editSelectedText">✏️ 编辑文字</button>
      <button @click="deleteSelectedText">🗑 删除文字</button>
    </div>

    <el-dialog v-model="showTextDialog" title="文字设置" width="460px">
      <el-input
        v-model="textInput"
        type="textarea"
        :rows="3"
        placeholder="输入要添加的文字"
        @keyup.enter="addTextToCanvas()"
      />

      <div class="dialog-tools">
        <div class="tool">
          <label>颜色</label>
          <el-color-picker v-model="dialogColor" show-alpha />
        </div>
        <div class="tool">
          <label>字号</label>
          <el-input-number v-model="dialogSize" :min="12" :max="120" size="small" />
        </div>
        <div class="tool stretch">
          <label>字体</label>
          <el-select v-model="dialogFont" size="small">
            <el-option label="Arial" value="Arial" />
            <el-option label="宋体" value="宋体" />
            <el-option label="黑体" value="黑体" />
            <el-option label="Comic Sans" value="Comic Sans MS" />
            <el-option label="Georgia" value="Georgia" />
            <el-option label="Times New Roman" value="Times New Roman" />
            <el-option label="Courier New" value="Courier New" />
          </el-select>
        </div>
      </div>

      <template #footer>
        <el-button @click="showTextDialog = false">取消</el-button>
        <el-button type="primary" @click="addTextToCanvas()">
          {{ editingTextId ? '更新文字' : '添加文字' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.canvas-editor {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  gap: 15px;
  padding: 20px;
  position: relative;
}

.placeholder {
  color: #999;
  font-size: 18px;
  font-weight: 500;
}

.canvas {
  aspect-ratio: 1;
  width: 100%;
  max-width: 620px;
  max-height: 620px;
  border: 2px solid #ddd;
  border-radius: 10px;
  background: white;
  cursor: default;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

.canvas.text-mode {
  cursor: crosshair;
  border: 2px dashed #667eea;
  box-shadow: 0 6px 18px rgba(102, 126, 234, 0.35);
}

.context-menu {
  position: fixed;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 6px;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.18);
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 999;
}

.context-menu button {
  border: none;
  background: none;
  padding: 6px 12px;
  border-radius: 4px;
  text-align: left;
  font-size: 13px;
  cursor: pointer;
}

.context-menu button:hover {
  background: #f5f5f5;
}

.dialog-tools {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.dialog-tools .tool {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 120px;
}

.dialog-tools .tool label {
  font-size: 12px;
  color: #666;
  font-weight: 600;
}

.dialog-tools .tool.stretch {
  flex: 1;
}

:deep(.el-dialog__body) {
  padding: 18px 20px 0;
}
</style>
