FROM python:3.11-slim

WORKDIR /app

# Install CPU-only PyTorch first to prevent sentence-transformers from
# pulling the full GPU version (~2.5GB of CUDA libraries).
RUN pip install --no-cache-dir \
    torch==2.6.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Install the rest of the application dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
