FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 ATLAS_HOST=0.0.0.0 ATLAS_ENV=production
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY requirements-runtime.txt ./
RUN pip install --no-cache-dir -r requirements-runtime.txt && pip install --no-cache-dir --no-deps . \
    && useradd --create-home --uid 10001 atlas
COPY config ./config
COPY reports/selection.json ./reports/selection.json
COPY artifacts/model.joblib artifacts/model.sha256 artifacts/metadata.json artifacts/training_reference.csv ./artifacts/
RUN mkdir runtime && chown -R atlas:atlas /app/runtime
USER atlas
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"
CMD ["python", "-m", "bank_marketing.service"]
