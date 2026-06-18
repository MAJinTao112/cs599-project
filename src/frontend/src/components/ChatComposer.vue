<template>
  <form class="composer" @submit.prevent="submit">
    <textarea
      v-model="draft"
      :disabled="busy"
      rows="3"
      placeholder="例如：我想 7 月从上海去杭州和苏州玩 4 天，预算 3000，想少走路。"
      @keydown.enter.exact.prevent="submit"
    />
    <button :disabled="busy || !draft.trim()" title="发送旅行需求">
      <Send :size="18" />
      <span>发送</span>
    </button>
  </form>
</template>

<script setup lang="ts">
import { Send } from "lucide-vue-next";
import { ref } from "vue";

defineProps<{ busy: boolean }>();
const emit = defineEmits<{ send: [message: string] }>();
const draft = ref("");

function submit() {
  const value = draft.value.trim();
  if (!value) return;
  emit("send", value);
  draft.value = "";
}
</script>
