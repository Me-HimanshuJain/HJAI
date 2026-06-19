import requests
import threading
import queue
import time


class AIEngine:
    def __init__(self, ollama_url="http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "llama3:latest"  # Model confirmed installed via `ollama list`
        self.answer_queue = queue.Queue()
        self.transcript_queue = queue.Queue()  # For showing raw transcript in UI
        self.is_running = False

    def start_worker(self, context_queue: queue.Queue):
        self.is_running = True
        self.thread = threading.Thread(target=self._worker, args=(context_queue,))
        self.thread.daemon = True
        self.thread.start()

    def _worker(self, context_queue: queue.Queue):
        context_buffer = ""
        last_process_time = time.time()

        while self.is_running:
            try:
                new_text = context_queue.get(timeout=0.5)
                context_buffer += new_text + " "
                # Always push the latest transcript to UI
                self.transcript_queue.put(new_text)
            except queue.Empty:
                pass

            # Generate an answer every 5 seconds if there's enough spoken content
            if time.time() - last_process_time > 5.0 and len(context_buffer.strip()) > 20:
                answer = self._generate_answer(context_buffer)
                if answer:
                    self.answer_queue.put(answer)

                # Keep a sliding window of context (last 800 chars)
                context_buffer = context_buffer[-800:]
                last_process_time = time.time()

    def _generate_answer(self, context_text: str):
        prompt = f"""You are a real-time meeting copilot assistant.

Someone said this during a live call or meeting:
"{context_text}"

Your task:
- If they asked a question (directly or indirectly), answer it in 1-3 short, clear sentences.
- Use simple, direct language. No filler words like "Sure!" or "Of course!".
- If no question was asked, write a 1-sentence summary of the key topic discussed.
- Do NOT repeat the question. Just give the answer directly.

Examples:
- Question: "What is Newton's third law?" → Answer: "Every action has an equal and opposite reaction."
- Question: "Who founded Microsoft?" → Answer: "Microsoft was founded by Bill Gates and Paul Allen in 1975."
- Statement (no question) → Brief topic summary.

Answer:"""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2, "num_predict": 100},
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            print(f"Ollama API Error: {e}")
            return None

    def get_latest_answer(self):
        """Returns the newest AI answer, or None if none available."""
        answer = None
        while not self.answer_queue.empty():
            answer = self.answer_queue.get()
        return answer

    def get_latest_transcript(self):
        """Returns recently transcribed text snippets for display in UI."""
        parts = []
        while not self.transcript_queue.empty():
            parts.append(self.transcript_queue.get())
        return " ".join(parts) if parts else None

    def stop(self):
        self.is_running = False
        if hasattr(self, "thread"):
            self.thread.join(timeout=2.0)
