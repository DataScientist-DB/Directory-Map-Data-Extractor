FROM apify/actor-python:3.11

COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium) into the image
RUN python -m playwright install chromium

CMD ["python", "src/main.py"]
