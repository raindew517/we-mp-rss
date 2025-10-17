<template>
  <a-modal v-model:visible="visible" title="导出设置" @ok="handleOk" @cancel="handleCancel">
    <a-form :model="form">
      <a-form-item label="导出范围" field="scope">
        <a-select v-model="form.scope" placeholder="请选择导出范围" disabled>
          <a-option value="all">指定页数</a-option>
          <a-option value="selected">已选文章</a-option>
        </a-select>
      </a-form-item>
      <a-form-item label="导出格式" field="format">
        <a-select v-model="form.format" placeholder="请选择导出格式" multiple>
          <a-option value="csv">Excel列表</a-option>
          <a-option value="md">MarDown</a-option>
          <a-option value="json">JSON附加信息</a-option>
          <a-option value="pdf">PDF归档</a-option>
          <a-option value="docx">WORD文档</a-option>
        </a-select>
      </a-form-item>
      <a-form-item label="导出数量" field="limit" v-if="form.scope === 'all' || form.scope === 'current'">
        <a-input-number v-model="form.page_count" :min="1" :max="10000" />
        <span>页</span>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { exportArticles } from '@/api/tools';

const visible = ref(false);
const form = ref({
  scope: 'all',
  format: ['pdf', 'docx', 'json', 'csv',"md"],
  page_count: 10,
  mp_id: '',
  ids:[],
});

const emit = defineEmits(['confirm']);

const show = (mp_id: string, ids:any) => {
  visible.value = true;
  form.value.mp_id = mp_id;
  console.log(ids)
  form.value.scope = ids && ids.length > 0 ? 'selected' : 'all';
  form.value.ids=ids;
};

const hide = () => {
  visible.value = false;
};

const handleOk = () => {
  SubmitExport(form.value);
  emit('confirm', form.value);
  hide();
};
const SubmitExport = async (params: any) => {
  try {
    const result = await exportArticles(params);
    console.log('导出成功:', result);
  } catch (error) {
    console.error('导出失败:', error);
  }
};
const handleCancel = () => {
  hide();
};

defineExpose({
  show,
  hide,
});
</script>