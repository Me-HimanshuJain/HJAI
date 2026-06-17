class TextChunker:
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
        """
        Splits text into chunks of roughly `chunk_size` tokens.
        Since we don't have a tokenizer loaded for this simple implementation, 
        we approximate tokens with words (1 token ~ 1.3 words).
        We'll use an approximation of ~380 words for 500 tokens.
        """
        words = text.split()
        approx_words_per_chunk = int(chunk_size / 1.3)
        approx_words_overlap = int(overlap / 1.3)
        
        chunks = []
        start = 0
        while start < len(words):
            end = min(start + approx_words_per_chunk, len(words))
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            if end == len(words):
                break
            # move start forward, keeping the overlap
            start += approx_words_per_chunk - approx_words_overlap
            
        return chunks
