import axios from "axios";

export type ChatRole = "user" | "assistant" | "system";

export interface ChatMessage {
  role: ChatRole;
  content: string;
}

export interface ChatRequest {
  message: string;
  messages: ChatMessage[];
  max_iterations: number;
}

export interface ToolStatus {
  tools: string[];
  count: number;
  mcp_available: boolean;
  uploaded_files: string[];
  rag_total: number;
}

export interface StreamHandlers {
  onStatus: (message: string) => void;
  onAnalysis: (data: Record<string, unknown>) => void;
  onFinal: (data: { answer: string; scenario_type: string; needs_r1: boolean; extraction: Record<string, unknown> }) => void;
  onError: (message: string) => void;
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "/api",
  timeout: 30000
});

const apiBase = import.meta.env.VITE_API_BASE || "/api";

export async function getTools(): Promise<ToolStatus> {
  const { data } = await api.get<ToolStatus>("/tools");
  return data;
}

export async function uploadDocuments(files: FileList): Promise<{ uploaded: number; files: string[]; message: string }> {
  const form = new FormData();
  Array.from(files).forEach((file) => form.append("files", file));
  const { data } = await api.post("/documents/upload", form, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}

export async function streamChat(request: ChatRequest, handlers: StreamHandlers): Promise<void> {
  const response = await fetch(`${apiBase}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request)
  });

  if (!response.ok || !response.body) {
    handlers.onError(`请求失败：${response.status}`);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";

    for (const part of parts) {
      const eventLine = part.split("\n").find((line) => line.startsWith("event:"));
      const dataLine = part.split("\n").find((line) => line.startsWith("data:"));
      if (!eventLine || !dataLine) continue;

      const event = eventLine.replace("event:", "").trim();
      const rawData = dataLine.replace("data:", "").trim();
      const data = JSON.parse(rawData);

      if (event === "status") handlers.onStatus(data.message || "");
      if (event === "analysis") handlers.onAnalysis(data);
      if (event === "final") handlers.onFinal(data);
      if (event === "error") handlers.onError(data.message || "未知错误");
    }
  }
}
