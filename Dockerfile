# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Expose ports
EXPOSE 8000 8501

# Run both FastAPI and Streamlit
CMD ["sh", "-c", "uvicorn api.__init__:app --host 0.0.0.0 --port 8000 & streamlit run app/titleapp.py --server.port 8501 --server.address 0.0.0.0"]
