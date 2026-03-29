FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . /app

RUN python -c "import pathlib, shutil; base = pathlib.Path('/app'); matches = [p for p in base.rglob('server.py') if p.parent.name == 'roketsim-main']; assert matches, 'roketsim server.py not found'; shutil.copyfile(matches[0], base / 'server.py')"

EXPOSE 5000

CMD ["python", "server.py"]
