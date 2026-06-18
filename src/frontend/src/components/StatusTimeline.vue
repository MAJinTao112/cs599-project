<template>
  <aside class="status-panel">
    <div class="status-head">
      <Activity :size="18" />
      <h2>Agent 工况</h2>
    </div>
    <div v-if="analysisText" class="analysis-card">
      <span>运行模式</span>
      <strong>{{ analysisText }}</strong>
    </div>
    <div class="gauge-row">
      <div>
        <span>R1 推理</span>
        <strong>{{ analysis.needs_r1 ? "ARMED" : "STANDBY" }}</strong>
      </div>
      <div>
        <span>事件缓存</span>
        <strong>{{ items.length }}</strong>
      </div>
    </div>
    <ol class="timeline">
      <li v-for="item in items" :key="item.id">
        <time>{{ item.time }}</time>
        <p>{{ item.text }}</p>
      </li>
    </ol>
    <p v-if="!items.length" class="empty-state">总线空闲，等待新的旅行任务。</p>
  </aside>
</template>

<script setup lang="ts">
import { Activity } from "lucide-vue-next";
import { computed } from "vue";

const props = defineProps<{
  items: Array<{ id: number; text: string; time: string }>;
  analysis: Record<string, unknown>;
}>();

const analysisText = computed(() => {
  const type = props.analysis.scenario_type;
  const needsR1 = props.analysis.needs_r1;
  if (!type) return "";
  if (type === "multi_destination") return "多目的地深度规划";
  if (needsR1) return "复杂需求深度分析";
  return "常规旅行规划";
});
</script>
