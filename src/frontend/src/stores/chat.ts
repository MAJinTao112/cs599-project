import { defineStore } from "pinia";
import { getTools, streamChat, uploadDocuments, type ChatMessage, type ToolStatus } from "../api/client";

interface TimelineItem {
  id: number;
  text: string;
  time: string;
}

export const useChatStore = defineStore("chat", {
  state: () => ({
    messages: [
      {
        role: "assistant",
        content:
          "你好呀，我是小桃。告诉我出发地、目的地、时间、预算和偏好，我会帮你把交通、住宿、天气和行程一起规划好。"
      }
    ] as ChatMessage[],
    timeline: [] as TimelineItem[],
    tools: { tools: [], count: 0, mcp_available: false, uploaded_files: [], rag_total: 0 } as ToolStatus,
    maxIterations: 30,
    busy: false,
    uploadBusy: false,
    error: "",
    analysis: {} as Record<string, unknown>
  }),
  actions: {
    addStatus(text: string) {
      if (!text) return;
      this.timeline.unshift({
        id: Date.now() + Math.random(),
        text,
        time: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" })
      });
      this.timeline = this.timeline.slice(0, 8);
    },
    async refreshTools() {
      try {
        this.tools = await getTools();
      } catch (error) {
        this.error = error instanceof Error ? error.message : "工具状态获取失败";
      }
    },
    async upload(files: FileList) {
      this.uploadBusy = true;
      this.error = "";
      try {
        const result = await uploadDocuments(files);
        this.addStatus(result.message);
        await this.refreshTools();
      } catch (error) {
        this.error = error instanceof Error ? error.message : "文档上传失败";
      } finally {
        this.uploadBusy = false;
      }
    },
    async send(message: string) {
      const clean = message.trim();
      if (!clean || this.busy) return;

      this.busy = true;
      this.error = "";
      this.messages.push({ role: "user", content: clean });
      const assistantIndex = this.messages.push({ role: "assistant", content: "" }) - 1;

      try {
        await streamChat(
          {
            message: clean,
            messages: this.messages.filter((_, index) => index !== assistantIndex),
            max_iterations: this.maxIterations
          },
          {
            onStatus: (status) => this.addStatus(status),
            onAnalysis: (data) => {
              this.analysis = data;
            },
            onFinal: (data) => {
              this.messages[assistantIndex].content = data.answer;
              this.analysis = {
                scenario_type: data.scenario_type,
                needs_r1: data.needs_r1,
                extraction: data.extraction
              };
            },
            onError: (msg) => {
              this.error = msg;
              this.messages[assistantIndex].content = `抱歉，处理请求时出现错误：${msg}`;
            }
          }
        );
      } finally {
        this.busy = false;
      }
    },
    clear() {
      this.messages = [
        {
          role: "assistant",
          content:
            "聊天记录已清空。重新告诉我你的旅行想法，我会重新规划。"
        }
      ];
      this.timeline = [];
      this.analysis = {};
      this.error = "";
    }
  }
});
