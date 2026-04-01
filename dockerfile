# stage 1 : build

FROM python:3.10-slim AS builder

WORKDIR /app


COPY requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt


# Stage : Create the final image

FROM python:3.10-slim AS final

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY . .

EXPOSE 8001

CMD ["python", "app.py"]
