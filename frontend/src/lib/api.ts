export const API_BASE = "http://localhost:8000/api";

export async function uploadDocument(userId: string, file: File) {
  const formData = new FormData();
  formData.append("user_id", userId);
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}

export async function uploadImage(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/vision/ocr`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}

export async function uploadAudio(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/voice/transcribe`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}

export async function dispatchAgentTask(taskType: string, prompt: string) {
  const res = await fetch(`${API_BASE}/agents/task`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_type: taskType, prompt }),
  });
  return res.json();
}

export async function checkAgentTask(taskId: string) {
  const res = await fetch(`${API_BASE}/agents/task/${taskId}`);
  return res.json();
}
