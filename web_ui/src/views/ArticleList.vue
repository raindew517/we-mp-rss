<template>
  <ArticleList v-if="!isMobile" />
  <ArticleListMobile v-else />
</template>
<script setup>
import { computed } from 'vue'
import ArticleList from '@/views/article/ArticleListDesktop.vue'
import ArticleListMobile from '@/views/article/ArticleListMobile.vue'
const isMobile = computed(() => window.innerWidth <= 768)
</script>