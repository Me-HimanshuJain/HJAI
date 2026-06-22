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
        Each new transcription triggers an AI answer right away.
        Latest utterance is passed separately so the AI always answers
        what was JUST said, not a mix of old + new topics.
        """
        recent = []   # rolling context — last 2 sentences only

        while self.is_running:
            try:
                new_text = context_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            new_text = new_text.strip()
            if not new_text:
                continue

            self.transcript_queue.put(new_text)   # push to UI immediately

            if len(new_text.strip()) < 15:
                recent.append(new_text)
                recent = recent[-2:]
                continue   # too short to answer

            context_history = " ".join(recent)    # previous lines as context
            recent.append(new_text)
            recent = recent[-2:]                  # keep only last 2

            self.is_thinking = True
            print(f"[AI] Answering: {new_text[:80]}...")
            answer = self._generate_answer(new_text, context_history)
            self.is_thinking = False

            if answer:
                print(f"[Answer] {answer}")
                self.answer_queue.put(answer)

    def _generate_answer(self, latest_text: str, context_history: str = ""):
        context_block = f'Previous context:\n"{context_history}"\n\n' if context_history.strip() else ""
        prompt = f"""You are HJAI — a silent AI copilot listening live to a meeting or interview.

{context_block}Latest statement/question:
"{latest_text}"

STRICT RULES:
- Answer ONLY the latest statement/question above.
- If ONE question → answer in 1-2 sentences. Direct, no filler.
- If MULTIPLE questions → number them (1. 2. 3.). One sentence each.
- If no question → one useful insight sentence.
- If unclear/noise → reply only: (listening...)
- ALWAYS answer in ENGLISH regardless of input language.
- NEVER repeat the question. NEVER say "Sure!", "Great!", "Of course!".
- MAX 60 words. STOP after your answer.

Examples:
"What is Newton's third law?" → "Every action has an equal and opposite reaction."
"India mein kitne states hain?" → "India has 28 states and 8 Union Territories."
"What opportunities for training? What does success look like?" →
1. Training is offered through mentorship and quarterly workshops.
2. Success means hitting KPIs and growing team impact within 12 months.

Answer:"""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 100},
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
