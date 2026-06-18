<template>
  <main class="travel-desk">
    <ControlPanel
      v-model="store.maxIterations"
      :tools="store.tools"
      :upload-busy="store.uploadBusy"
      @upload="store.upload"
      @clear="store.clear"
      @refresh-tools="store.refreshTools"
    />

    <section class="chat-shell">
      <header class="chat-header">
        <div>
          <p class="eyebrow">Mission Deck / Vue + FastAPI</p>
          <h2>旅行任务舱</h2>
        </div>
        <div class="live-pill" :class="{ active: store.busy }">
          <span></span>
          {{ store.busy ? "引擎运行" : "系统待命" }}
        </div>
      </header>

      <div v-if="store.error" class="error-banner">{{ store.error }}</div>

      <div class="message-list">
        <MessageBubble v-for="(message, index) in store.messages" :key="index" :message="message" />
      </div>

      <ChatComposer :busy="store.busy" @send="store.send" />
    </section>

    <StatusTimeline :items="store.timeline" :analysis="store.analysis" />
  </main>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import ChatComposer from "../components/ChatComposer.vue";
import ControlPanel from "../components/ControlPanel.vue";
import MessageBubble from "../components/MessageBubble.vue";
import StatusTimeline from "../components/StatusTimeline.vue";
import { useChatStore } from "../stores/chat";

const store = useChatStore();

onMounted(() => {
  store.refreshTools();
});
</script>
