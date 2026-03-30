FROM python:3.11-slim

WORKDIR /app

RUN pip install hatchling

COPY pyproject.toml .
RUN pip install -e ".[all]" 2>/dev/null || pip install -e .

COPY . .

EXPOSE 8000

CMD ["uvicorn", "probe.main:api", "--host", "0.0.0.0", "--port", "8000"]
