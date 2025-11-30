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
    default: 36
  },
  fontFamily: {
    type: String,
    default: 'Arial'
  }
})

const canvasRef = ref(null)
const canvas = ref(null)
const ctx = ref(null)

const elements = ref([])
const selectedId = ref(null)
const imageLoaded = ref(false)

const isAddingText = ref(false)
const showTextDialog = ref(false)
const textInput = ref('')
const editingTextId = ref(null)

const dialogColor = ref(props.textColor)
const dialogFont = ref(props.fontFamily)
const dialogSize = ref(props.fontSize)

const isDragging = ref(false)
const dragMode = ref(null) // 'move', 'rotate', 'scale-tl', 'scale-tr', 'scale-bl', 'scale-br'
const dragStart = ref({ x: 0, y: 0 })
const initialElementState = ref(null)

const contextMenu = ref({ visible: false, x: 0, y: 0, targetId: null })

const history = ref([])
const historyStep = ref(-1)

const CANVAS_SIZE = 512

const initCanvas = () => {
  canvas.value = canvasRef.value
  if (!canvas.value) {
    console.warn('initCanvas: canvasRef is null')
    return
  }
  ctx.value = canvas.value.getContext('2d', { willReadFrequently: true })
  canvas.value.width = CANVAS_SIZE
  canvas.value.height = CANVAS_SIZE
  drawCanvas()
}

const handleKeyDown = (e) => {
  if (showTextDialog.value) return
  
  if (e.key.toLowerCase() === 't') {
    toggleTextTool()
  }
  
  if (e.ctrlKey || e.metaKey) {
    if (e.key === 'c') {
      e.preventDefault()
      copyImage()
    } else if (e.key === 'v') {
      // Paste handled by 'paste' event
    } else if (e.key === 'z') {
      e.preventDefault()
      if (e.shiftKey) redo()
      else undo()
    }
  }
  
  if (e.key === 'Delete' || e.key === 'Backspace') {
    if (selectedId.value && !isAddingText.value) {
      deleteSelectedElement()
    }
  }
}

const handlePaste = async (e) => {
  const items = e.clipboardData?.items
  if (!items) return
  
  for (const item of items) {
    if (item.type.indexOf('image') !== -1) {
      const blob = item.getAsFile()
      const img = new Image()
      img.src = URL.createObjectURL(blob)
      img.onload = () => {
        let w = img.width
        let h = img.height
        
        // Auto-scale if too large (fit within 80% of canvas)
        if (w > CANVAS_SIZE || h > CANVAS_SIZE) {
          const scale = (CANVAS_SIZE * 0.8) / Math.max(w, h)
          w *= scale
          h *= scale
        }

        addElement({
          type: 'image',
          content: img,
          width: w,
          height: h,
          x: CANVAS_SIZE / 2,
          y: CANVAS_SIZE / 2
        })
      }
    }
  }
}

const closeContextMenu = () => {
  if (!contextMenu.value.visible) return
  contextMenu.value.visible = false
  contextMenu.value.targetId = null
}

onMounted(() => {
  initCanvas()
  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('paste', handlePaste)
  window.addEventListener('click', closeContextMenu)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('paste', handlePaste)
  window.removeEventListener('click', closeContextMenu)
})

const loadImage = (imagePath) => {
  console.log('Loading image:', imagePath)
  if (!imagePath) {
    imageLoaded.value = false
    return
  }

  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => {
    console.log('Image loaded:', img.width, 'x', img.height)
    if (img.width === 0 || img.height === 0) {
      console.error('Image has 0 dimensions')
      ElMessage.error('图片加载失败：无效的图片')
      imageLoaded.value = false
      return
    }

    imageLoaded.value = true
    
    // Calculate cover scale
    const scale = Math.max(CANVAS_SIZE / img.width, CANVAS_SIZE / img.height)
    const w = img.width * scale
    const h = img.height * scale
    
    nextTick(() => {
      console.log('Initializing canvas with ref:', canvasRef.value)
      initCanvas()
      if (!canvas.value) {
        console.error('Canvas ref is missing after nextTick')
        return
      }
      
      elements.value = [{
        id: `img-${Date.now()}`,
        type: 'image',
        content: img,
        x: CANVAS_SIZE / 2,
        y: CANVAS_SIZE / 2,
        width: w,
        height: h,
        rotation: 0
      }]
      selectedId.value = null
      drawCanvas()
      resetHistory()
    })
  }
  img.onerror = (e) => {
    console.error('Image load error:', e)
    ElMessage.error('表情包加载失败')
    imageLoaded.value = false
  }
  img.src = imagePath.startsWith('/') ? imagePath : `/${imagePath}`
}

const drawCanvas = () => {
  if (!canvas.value || !ctx.value) return
  ctx.value.clearRect(0, 0, CANVAS_SIZE, CANVAS_SIZE)
  ctx.value.fillStyle = '#ffffff'
  ctx.value.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE)

  elements.value.forEach(el => {
    ctx.value.save()
    ctx.value.translate(el.x, el.y)
    ctx.value.rotate(el.rotation)
    
    if (el.type === 'image') {
      ctx.value.drawImage(el.content, -el.width / 2, -el.height / 2, el.width, el.height)
    } else if (el.type === 'text') {
      ctx.value.font = `bold ${el.size}px ${el.font}`
      ctx.value.textAlign = 'center'
      ctx.value.textBaseline = 'middle'
      ctx.value.lineWidth = 4
      ctx.value.strokeStyle = 'rgba(255, 255, 255, 0.85)'
      ctx.value.strokeText(el.text, 0, 0)
      ctx.value.fillStyle = el.color
      ctx.value.fillText(el.text, 0, 0)
    }
    
    // Draw selection box if selected
    if (el.id === selectedId.value) {
      const w = el.type === 'text' ? getTextWidth(el) + 20 : el.width
      const h = el.type === 'text' ? el.size * 1.2 + 20 : el.height
      
      ctx.value.strokeStyle = '#667eea'
      ctx.value.lineWidth = 2
      ctx.value.setLineDash([6, 4])
      ctx.value.strokeRect(-w/2, -h/2, w, h)
      
      // Draw handles
      ctx.value.setLineDash([])
      ctx.value.fillStyle = '#fff'
      ctx.value.strokeStyle = '#667eea'
      
      // Rotate handle
      ctx.value.beginPath()
      ctx.value.moveTo(0, -h/2)
      ctx.value.lineTo(0, -h/2 - 20)
      ctx.value.stroke()
      ctx.value.beginPath()
      ctx.value.arc(0, -h/2 - 20, 5, 0, Math.PI * 2)
      ctx.value.fill()
      ctx.value.stroke()
      
      // Resize handles
      const handles = [
        [-w/2, -h/2], [w/2, -h/2],
        [w/2, h/2], [-w/2, h/2]
      ]
      handles.forEach(([hx, hy]) => {
        ctx.value.fillRect(hx - 4, hy - 4, 8, 8)
        ctx.value.strokeRect(hx - 4, hy - 4, 8, 8)
      })
    }
    
    ctx.value.restore()
  })
}

const getTextWidth = (el) => {
  ctx.value.font = `bold ${el.size}px ${el.font}`
  return ctx.value.measureText(el.text).width
}

const getElementBounds = (el) => {
  const w = el.type === 'text' ? getTextWidth(el) + 20 : el.width
  const h = el.type === 'text' ? el.size * 1.2 + 20 : el.height
  return { w, h }
}

// Transform point from canvas space to element local space
const getLocalPoint = (px, py, el) => {
  const dx = px - el.x
  const dy = py - el.y
  const cos = Math.cos(-el.rotation)
  const sin = Math.sin(-el.rotation)
  return {
    x: dx * cos - dy * sin,
    y: dx * sin + dy * cos
  }
}

const hitTest = (x, y) => {
  // Check handles first if something is selected
  if (selectedId.value) {
    const el = elements.value.find(e => e.id === selectedId.value)
    if (el) {
      const { w, h } = getElementBounds(el)
      const local = getLocalPoint(x, y, el)
      
      // Rotate handle
      if (Math.abs(local.x) < 10 && Math.abs(local.y - (-h/2 - 20)) < 10) return { el, handle: 'rotate' }
      
      // Corners: tl, tr, br, bl
      if (Math.abs(local.x - (-w/2)) < 10 && Math.abs(local.y - (-h/2)) < 10) return { el, handle: 'scale-tl' }
      if (Math.abs(local.x - (w/2)) < 10 && Math.abs(local.y - (-h/2)) < 10) return { el, handle: 'scale-tr' }
      if (Math.abs(local.x - (w/2)) < 10 && Math.abs(local.y - (h/2)) < 10) return { el, handle: 'scale-br' }
      if (Math.abs(local.x - (-w/2)) < 10 && Math.abs(local.y - (h/2)) < 10) return { el, handle: 'scale-bl' }
    }
  }

  // Check bodies (reverse order)
  for (let i = elements.value.length - 1; i >= 0; i--) {
    const el = elements.value[i]
    const { w, h } = getElementBounds(el)
    const local = getLocalPoint(x, y, el)
    if (Math.abs(local.x) <= w/2 && Math.abs(local.y) <= h/2) {
      return { el, handle: 'move' }
    }
  }
  return null
}

const onMouseDown = (event) => {
  if (!canvas.value || isAddingText.value) return
  const { x, y } = getCanvasCoordinates(event)
  const hit = hitTest(x, y)
  
  if (hit) {
    selectedId.value = hit.el.id
    dragMode.value = hit.handle
    dragStart.value = { x, y }
    initialElementState.value = { ...hit.el }
    isDragging.value = true
    closeContextMenu()
  } else {
    selectedId.value = null
  }
  drawCanvas()
}

const onMouseMove = (event) => {
  if (!isDragging.value || !selectedId.value) return
  const { x, y } = getCanvasCoordinates(event)
  const el = elements.value.find(e => e.id === selectedId.value)
  if (!el) return

  const dx = x - dragStart.value.x
  const dy = y - dragStart.value.y
  const init = initialElementState.value

  if (dragMode.value === 'move') {
    el.x = init.x + dx
    el.y = init.y + dy
  } else if (dragMode.value === 'rotate') {
    const angle = Math.atan2(y - el.y, x - el.x)
    const startAngle = Math.atan2(dragStart.value.y - el.y, dragStart.value.x - el.x)
    el.rotation = init.rotation + (angle - startAngle)
  } else if (dragMode.value.startsWith('scale')) {
    // Simple scaling logic (center-based for simplicity)
    // For better UX, scaling should be anchor-based, but center-based is easier to implement robustly in one go
    const currentDist = Math.hypot(x - el.x, y - el.y)
    const startDist = Math.hypot(dragStart.value.x - el.x, dragStart.value.y - el.y)
    const scaleFactor = currentDist / startDist
    
    if (el.type === 'text') {
      el.size = Math.max(10, init.size * scaleFactor)
    } else {
      el.width = Math.max(20, init.width * scaleFactor)
      el.height = Math.max(20, init.height * scaleFactor)
    }
  }
  drawCanvas()
}

const onMouseUp = () => {
  if (isDragging.value) {
    isDragging.value = false
    dragMode.value = null
    saveHistory()
  }
}

const onDoubleClick = (event) => {
  const { x, y } = getCanvasCoordinates(event)
  const hit = hitTest(x, y)
  if (hit && hit.el.type === 'text') {
    startEditingText(hit.el)
  }
}

// ... (keep cloneTexts, resetHistory, saveHistory, restoreHistory, undo, redo but adapted for elements) ...
const cloneElements = () => elements.value.map(el => ({...el}))

const resetHistory = () => {
  history.value = []
  historyStep.value = -1
  saveHistory()
}

const saveHistory = () => {
  history.value = history.value.slice(0, historyStep.value + 1)
  history.value.push(cloneElements())
  historyStep.value = history.value.length - 1
}

const restoreHistory = () => {
  if (historyStep.value < 0 || !history.value[historyStep.value]) return
  elements.value = history.value[historyStep.value].map(el => {
    // Restore image objects if needed (images are references, so shallow copy might be tricky if we replaced images, but here we just move them)
    // Actually, JSON.stringify kills Image objects. We need a better way or just store props.
    // For now, let's assume content is preserved if we don't deep clone the Image object itself but the reference.
    // Wait, JSON.parse(JSON.stringify) WILL kill the Image object.
    // Fix: Don't use JSON for history. Use shallow copy of props, but keep content ref.
    return el
  })
  drawCanvas()
}

// Fix history for Image objects
const cloneForHistory = () => {
  return elements.value.map(el => {
    const clone = { ...el }
    return clone
  })
}
// Override saveHistory to use cloneForHistory
const saveHistoryFixed = () => {
  history.value = history.value.slice(0, historyStep.value + 1)
  history.value.push(cloneForHistory())
  historyStep.value = history.value.length - 1
}
// Override restoreHistory
const restoreHistoryFixed = () => {
  if (historyStep.value < 0 || !history.value[historyStep.value]) return
  // Deep copy back? No, just replace array.
  // We need to be careful about object references.
  // For this simple app, let's just restore the array structure.
  elements.value = history.value[historyStep.value].map(el => ({...el}))
  drawCanvas()
}

const undo = () => {
  if (historyStep.value <= 0) return
  historyStep.value -= 1
  restoreHistoryFixed()
}

const redo = () => {
  if (historyStep.value >= history.value.length - 1) return
  historyStep.value += 1
  restoreHistoryFixed()
}

const emit = defineEmits(['mode-change'])

const toggleTextTool = () => {
  isAddingText.value = !isAddingText.value
  closeContextMenu()
  emit('mode-change', isAddingText.value)
}


const canvasClick = (event) => {
  if (isAddingText.value) {
    const { x, y } = getCanvasCoordinates(event)
    textInput.value = ''
    editingTextId.value = null
    // Create temp text element
    addElement({
      type: 'text',
      text: '点击编辑',
      x, y,
      color: dialogColor.value,
      size: dialogSize.value,
      font: dialogFont.value,
      rotation: 0
    }, true) // true = open dialog immediately
    isAddingText.value = false
    return
  }
}

const addElement = (el, editImmediately = false) => {
  const newEl = {
    id: `el-${Date.now()}`,
    rotation: 0,
    ...el
  }
  elements.value.push(newEl)
  selectedId.value = newEl.id
  drawCanvas()
  saveHistoryFixed()
  
  if (editImmediately && newEl.type === 'text') {
    startEditingText(newEl)
  }
}

const addTextToCanvas = () => {
  if (!textInput.value.trim()) return
  
  const el = elements.value.find(e => e.id === editingTextId.value)
  if (el) {
    el.text = textInput.value
    el.color = dialogColor.value
    el.size = dialogSize.value
    el.font = dialogFont.value
    ElMessage.success('文字已更新')
  }
  
  showTextDialog.value = false
  textInput.value = ''
  editingTextId.value = null
  drawCanvas()
  saveHistoryFixed()
}

const startEditingText = (el) => {
  editingTextId.value = el.id
  textInput.value = el.text
  dialogColor.value = el.color
  dialogFont.value = el.font
  dialogSize.value = el.size
  showTextDialog.value = true
}

const deleteSelectedElement = () => {
  if (!selectedId.value) return
  elements.value = elements.value.filter(e => e.id !== selectedId.value)
  selectedId.value = null
  drawCanvas()
  saveHistoryFixed()
}

const exportImage = () => {
  if (!canvas.value) return
  const prevSel = selectedId.value
  selectedId.value = null
  drawCanvas()
  
  canvas.value.toBlob(blob => {
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `meme-${Date.now()}.png`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('已导出 PNG')
    selectedId.value = prevSel
    drawCanvas()
  }, 'image/png')
}

const copyImage = async () => {
  if (!canvas.value) return
  const prevSel = selectedId.value
  selectedId.value = null
  drawCanvas()
  
  try {
    const blob = await new Promise(resolve => canvas.value.toBlob(resolve, 'image/png'))
    const data = [new ClipboardItem({ 'image/png': blob })]
    await navigator.clipboard.write(data)
    ElMessage.success('图片已复制')
  } catch (error) {
    ElMessage.error('复制失败')
  } finally {
    selectedId.value = prevSel
    drawCanvas()
  }
}

const getCanvasCoordinates = (event) => {
  const rect = canvas.value.getBoundingClientRect()
  const scaleX = CANVAS_SIZE / rect.width
  const scaleY = CANVAS_SIZE / rect.height
  return {
    x: (event.clientX - rect.left) * scaleX,
    y: (event.clientY - rect.top) * scaleY
  }
}

watch(() => props.image, (value) => {
  console.log('Watch props.image:', value)
  if (value) loadImage(value)
})

const deselectAll = () => {
  selectedId.value = null
  drawCanvas()
}

defineExpose({
  undo,
  redo,
  exportImage,
  copyImage,
  toggleTextTool,
  addTextToCanvas: () => {
    // Compatibility wrapper for App.vue
    // App.vue calls this to add text from toolbar
    // We'll just open the dialog or add default text
    isAddingText.value = true
    ElMessage.info('请点击画布添加文字')
  }
})
</script>

<template>
  <div class="canvas-editor" @click="deselectAll">
    <!-- 移除 v-if="!imageLoaded" 占位符，让画布始终显示 -->
    <!-- <div v-if="!imageLoaded" class="placeholder">
      <p>👈 从左侧选择一张表情包</p>
    </div> -->

    <canvas
      ref="canvasRef"
      class="canvas"
      :class="{ 'text-mode': isAddingText }"
      @click.stop="canvasClick"
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
      <button @click="deleteSelectedElement">🗑 删除文字</button>
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
