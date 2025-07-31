<template>
  <div class="novel-reader">
    <div class="header">
      <h1>{{ novelTitle }}</h1>
      <button @click="toggleSettings">设置</button>
    </div>

    <div class="book-container">
      <div 
        class="page" 
        :class="{ 'page-flipped': isFlipped }"
        @click="flipPage"
      >
        <div class="page-front" :style="contentStyle">
          {{ currentPageContent }}
        </div>
        <div class="page-back" :style="contentStyle">
          {{ nextPageContent }}
        </div>
      </div>
    </div>

    <div class="footer">
      <button @click="prevChapter">上一章</button>
      <button @click="nextChapter">下一章</button>
    </div>

    <div v-if="showSettings" class="settings-modal">
      <h2>阅读设置</h2>
      <div>
        <label>字体大小：</label>
        <input type="range" v-model="fontSize" min="12" max="24" />
      </div>
      <div>
        <label>背景颜色：</label>
        <input type="color" v-model="backgroundColor" />
      </div>
      <button @click="closeSettings">关闭</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NovelReader',
  data() {
    return {
      novelTitle: '小说标题',
      currentChapterContent: '这里是小说内容...',
      currentPageContent: '这里是当前页内容...',
      nextPageContent: '这里是下一页内容...',
      isFlipped: false,
      showSettings: false,
      fontSize: 16,
      backgroundColor: '#ffffff',
    };
  },
  computed: {
    contentStyle() {
      return {
        fontSize: `${this.fontSize}px`,
        backgroundColor: this.backgroundColor,
      };
    },
  },
  methods: {
    toggleSettings() {
      this.showSettings = !this.showSettings;
    },
    closeSettings() {
      this.showSettings = false;
    },
    prevChapter() {
      // 上一章逻辑
      console.log('上一章');
    },
    nextChapter() {
      // 下一章逻辑
      console.log('下一章');
    },
    flipPage() {
      this.isFlipped = !this.isFlipped;
      if (this.isFlipped) {
        // 翻页后加载下一页内容
        this.currentPageContent = this.nextPageContent;
        this.nextPageContent = '这里是新加载的下一页内容...';
      }
    },
  },
};
</script>

<style scoped>
.novel-reader {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.book-container {
  perspective: 1000px;
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.page {
  width: 80%;
  height: 80%;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 0.6s;
  cursor: pointer;
}

.page-flipped {
  transform: rotateY(180deg);
}

.page-front, .page-back {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  padding: 20px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
  background: white;
  overflow-y: auto;
  line-height: 1.6;
}

.page-back {
  transform: rotateY(180deg);
}

.footer {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
}

.settings-modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  padding: 20px;
  border: 1px solid #ccc;
  z-index: 1000;
}
</style>