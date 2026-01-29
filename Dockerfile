FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Запускаємо app.py. Важливо, щоб в app.py було host='0.0.0.0'
CMD ["python", "app.py"]