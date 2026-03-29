FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HERMES_DIR_NAME=hermes_module

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN python -c "import os; import pathlib; base = pathlib.Path('/app'); matches = [p for p in base.iterdir() if p.is_dir() and (p / 'hermes_db').is_dir()]; assert matches, 'HERMES directory not found'; target = base / 'hermes_module'; (target.exists() or target.is_symlink()) and target.unlink(); os.symlink(matches[0], target, target_is_directory=True)"
RUN mkdir -p /data/user-models

EXPOSE 8010

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8010"]
