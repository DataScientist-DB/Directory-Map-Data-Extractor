FROM apify/actor-python:3.11

COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser + all required OS dependencies
RUN python -m playwright install --with-deps chromium

CMD ["python", "-m", "src.main"]
