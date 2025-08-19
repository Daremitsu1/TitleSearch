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
EXPOSE 8001 8002 8501

# Make the shell script executable
RUN chmod +x run-uvicorn.sh

# Run both FastAPI and Streamlit
CMD ["sh", "-c", "./run-uvicorn.sh & streamlit run app/titleapp.py --server.port 8501 --server.address 0.0.0.0"]
