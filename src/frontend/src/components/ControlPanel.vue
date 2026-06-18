<template>
  <aside class="control-panel">
    <div class="panel-rivets" aria-hidden="true"><span></span><span></span><span></span><span></span></div>
    <div class="brand-block">
      <div class="brand-mark">
        <Cpu :size="24" />
      </div>
      <div>
        <p class="eyebrow">XT-07 Route Engine</p>
        <h1>小桃旅行助手</h1>
      </div>
    </div>

    <section class="panel-section">
      <div class="section-title">
        <UploadCloud :size="17" />
        <span>攻略文档</span>
      </div>
      <label class="upload-zone">
        <input type="file" multiple accept=".txt,.md,.pdf,.csv" :disabled="uploadBusy" @change="handleUpload" />
        <FileUp :size="22" />
        <span>{{ uploadBusy ? "索引模块运行中..." : "接入攻略文档 TXT / PDF / CSV / MD" }}</span>
      </label>
    </section>

    <section class="panel-section">
      <div class="section-title">
        <SlidersHorizontal :size="17" />
        <span>规划配置</span>
      </div>
      <label class="range-row">
        <span>最大迭代</span>
        <strong>{{ modelValue }}</strong>
      </label>
      <input
        class="range"
        type="range"
        min="10"
        max="100"
        step="5"
        :value="modelValue"
        @input="$emit('update:modelValue', Number(($event.target as HTMLInputElement).value))"
      />
    </section>

    <section class="panel-section">
      <div class="section-title">
        <Wrench :size="17" />
        <span>工具状态</span>
      </div>
      <div class="metric-grid">
        <div>
          <span>工具单元</span>
          <strong>{{ tools.count }}</strong>
        </div>
        <div>
          <span>MCP 总线</span>
          <strong>{{ tools.mcp_available ? "在线" : "离线" }}</strong>
        </div>
        <div>
          <span>RAG 块</span>
          <strong>{{ tools.rag_total }}</strong>
        </div>
        <div>
          <span>文档</span>
          <strong>{{ tools.uploaded_files.length }}</strong>
        </div>
      </div>
      <button class="ghost-button" title="刷新工具状态" @click="$emit('refresh-tools')">
        <RefreshCw :size="16" />
        <span>刷新</span>
      </button>
    </section>

    <button class="clear-button" title="清空聊天记录" @click="$emit('clear')">
      <Trash2 :size="16" />
      <span>清空会话</span>
    </button>
  </aside>
</template>

<script setup lang="ts">
import { Cpu, FileUp, RefreshCw, SlidersHorizontal, Trash2, UploadCloud, Wrench } from "lucide-vue-next";
import type { ToolStatus } from "../api/client";

defineProps<{
  tools: ToolStatus;
  modelValue: number;
  uploadBusy: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: number];
  upload: [files: FileList];
  clear: [];
  "refresh-tools": [];
}>();

function handleUpload(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files?.length) emit("upload", target.files);
  target.value = "";
}
</script>
