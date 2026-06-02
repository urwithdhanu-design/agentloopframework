# Build React UI
FROM node:20-alpine AS ui-build
WORKDIR /ui
COPY deploy/cloud-run/ui/package.json ./
RUN npm install
COPY deploy/cloud-run/ui/ ./
RUN npm run build

# Python API + agentloop
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8080

COPY deploy/cloud-run/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agentloop/ ./agentloop/
COPY deploy/cloud-run/api/ ./api/
COPY --from=ui-build /static ./static

EXPOSE 8080

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
