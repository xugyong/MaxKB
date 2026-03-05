<template>
  <div>
    <!-- 搜索 -->
    <el-card
      class="workflow-search"
      v-if="showSearch"
      shadow="always"
      style="--el-card-padding: 8px 12px; --el-card-border-radius: 8px"
    >
      <div class="workflow-search-container flex-between">
        <el-input
          ref="searchInputRef"
          v-model="searchText"
          :placeholder="$t('workflow.tip.searchPlaceholder')"
          clearable
          @keyup.enter="handleSearch"
          @keyup.esc="closeSearch"
        >
        </el-input>
        <span>
          <el-space :size="4">
            <span class="lighter"> 2/3 </span>
            <el-divider direction="vertical" />

            <el-button text>
              <el-icon><ArrowUp /></el-icon>
            </el-button>
            <el-button text>
              <el-icon><ArrowDown /></el-icon>
            </el-button>
            <el-button text @click="closeSearch()">
              <el-icon><Close /></el-icon>
            </el-button>
          </el-space>
        </span>
      </div>
    </el-card>
    <!-- 开启搜索按钮 -->
    <!-- <el-button v-else @click="openSearch()" circle class="workflow-search-button" size="large">
      <el-icon :size="20"><Search /></el-icon>
    </el-button> -->
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'

// Props定义
interface Props {
  onSearch?: (keyword: string) => void // 搜索回调
}
const props = withDefaults(defineProps<Props>(), {
  onSearch: undefined,
})

// 状态
const showSearch = ref(false)
const searchText = ref('')
const searchInputRef = ref<any>(null)

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
.workflow-search-button {
  position: absolute;
  top: 72px;
  left: 24px;
  z-index: 2;
}
.workflow-search {
  position: absolute;
  top: 72px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2;
}
.workflow-search-container {
  width: 360px;
  :deep(.el-input__wrapper) {
    box-shadow: none;
    padding: 0 8px 0 1px!important;
  }
}
</style>
