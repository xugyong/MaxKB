<template>
  <div>
    <!-- 搜索 -->
    <el-card
      v-if="showSearch"
      shadow="always"
      style="--el-card-padding: 8px 12px; --el-card-border-radius: 8px"
    >
      <div class="workflow-search-container">
        <el-input
          ref="searchInputRef"
          v-model="searchText"
          placeholder="搜索..."
          :prefix-icon="Search"
          clearable
          @keyup.enter="handleSearch"
          @keyup.esc="closeSearch"
        >
          <template #append>
            <el-button @click="closeSearch">取消</el-button>
          </template>
        </el-input>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { Search } from '@element-plus/icons-vue'

// Props定义
interface Props {
  onSearch?: (keyword: string) => void // 搜索回调
}

const props = withDefaults(defineProps<Props>(), {
  useElementPlus: false,
  onSearch: undefined,
})

// 状态
const showSearch = ref(false)
const searchText = ref('')
const searchInputRef = ref<any>(null)
const nativeInputRef = ref<HTMLInputElement | null>(null)

// 快捷键处理
const handleKeyDown = (e: KeyboardEvent) => {
  // Ctrl+F 或 Cmd+F (Mac)
  if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
    e.preventDefault() // 阻止浏览器默认搜索
    openSearch()
  }

  // 按ESC关闭
  if (e.key === 'Escape' && showSearch.value) {
    closeSearch()
  }
}

// 打开搜索
const openSearch = () => {
  showSearch.value = true
  searchText.value = ''

  nextTick(() => {
    searchInputRef.value?.focus()
  })
}

// 关闭搜索
const closeSearch = () => {
  showSearch.value = false
  searchText.value = ''
}

// 执行搜索
const handleSearch = () => {
  if (searchText.value.trim()) {
    props.onSearch?.(searchText.value)
  }
}

// 生命周期
onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.workflow-search-container {
  width: 360px;
}
</style>
