<template>
  <article :class="['message', message.role]">
    <div class="message-meta">
      <span>{{ message.role === "user" ? "你" : "小桃" }}</span>
    </div>
    <div class="message-body" v-html="rendered"></div>
  </article>
</template>

<script setup lang="ts">
import MarkdownIt from "markdown-it";
import { computed } from "vue";
import type { ChatMessage } from "../api/client";

const props = defineProps<{ message: ChatMessage }>();

const md = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: true
});

const rendered = computed(() => {
  if (!props.message.content) {
    return "<p class=\"typing-line\">正在整理旅行线索...</p>";
  }
  return md.render(props.message.content);
});
</script>
