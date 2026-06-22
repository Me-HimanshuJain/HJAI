import requests
import threading
import queue
import time


class AIEngine:
    def __init__(self, ollama_url="http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "phi3:mini"   # Fast 3.8B model — ~5-15s response
        self.answer_queue = queue.Queue()
        self.transcript_queue = queue.Queue()
        self.is_running = False
        self.is_thinking = False   # True while Ollama is generating

    def start_worker(self, context_queue: queue.Queue):
        self.is_running = True
        self.thread = threading.Thread(
            target=self._worker, args=(context_queue,), daemon=True
        )
        self.thread.start()

    def _worker(self, context_queue: queue.Queue):
        """
        Immediate-response worker:
        Each new transcription that arrives triggers an AI answer right away.
        No timer — the silence-detector in the transcriber already batched
        the speech into a complete utterance before sending it here.
        """
        sentences = []   # rolling context window (last 6 utterances)

        while self.is_running:
            try:
                new_text = context_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            new_text = new_text.strip()
            if not new_text:
                continue

            sentences.append(new_text)
            sentences = sentences[-6:]                    # keep last 6 sentences
            self.transcript_queue.put(new_text)           # push to UI immediately

            context_buffer = " ".join(sentences)
            if len(context_buffer.strip()) < 15:
                continue                                   # too short to answer

            self.is_thinking = True
            print(f"[AI] Generating answer for: {context_buffer[:90]}...")
            answer = self._generate_answer(context_buffer)
            self.is_thinking = False

            if answer:
                print(f"[Answer] {answer}")
                self.answer_queue.put(answer)

    def _generate_answer(self, context_text: str):
        prompt = f"""You are HJAI — a silent AI copilot listening live to a meeting or interview.

What was just said:
"{context_text}"

STRICT RULES:
- If ONE question was asked → answer in exactly 1-2 sentences. Direct, no filler.
- If MULTIPLE questions were asked → answer each on its own numbered line (1. 2. 3.). One sentence each.
- If no question → one useful insight sentence about the topic.
- If unclear/noise → reply only: (listening...)
- Match the language: English → English. Hindi → Hindi.
- NEVER repeat the question. NEVER say "Sure!", "Great!", "Of course!".
- MAX 60 words total. STOP writing after your answer. Do NOT add extra paragraphs or insights.

Examples:
Q: "What is Newton's third law?" → "Every action has an equal and opposite reaction."
Q: "What opportunities for training? What does success look like? Best thing about the company?" →
1. Training is offered through mentorship and quarterly skill workshops.
2. Success means hitting agreed KPIs and growing team impact within 12 months.
3. The best thing is a culture that rewards initiative and personal growth.

Answer:"""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 150},
                },
                timeout=45,
            )
            response.raise_for_status()
            result = response.json().get("response", "").strip()
            if result and "(listening...)" not in result.lower():
                return result
            return None
        except Exception as e:
            print(f"Ollama API Error: {e}")
            return None

    def reset(self):
        """Clear both queues (called by Reset button)."""
        for q in (self.answer_queue, self.transcript_queue):
            while not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    break

    def get_latest_answer(self):
        answer = None
        while not self.answer_queue.empty():
            answer = self.answer_queue.get()
        return answer

    def get_latest_transcript(self):
        parts = []
        while not self.transcript_queue.empty():
            parts.append(self.transcript_queue.get())
        return " ".join(parts) if parts else None

    def stop(self):
        self.is_running = False
        if hasattr(self, "thread"):
            self.thread.join(timeout=20.0)
