"""One launcher for macOS and Windows. Run with Python 3.10 or newer."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import threading
import venv
import webbrowser

ROOT = Path(__file__).resolve().parent
ENV = ROOT / '.venv-portable'
PYTHON = ENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
REQUIREMENTS = ROOT / 'backend' / 'requirements.txt'
STAMP = ENV / '.requirements-sha256'


def ensure_environment():
    if not PYTHON.exists():
        print('Создание окружения приложения…', flush=True)
        # Bootstrap pip explicitly so interrupted setups can be repaired next time.
        venv.EnvBuilder(with_pip=False).create(ENV)
    probe = subprocess.run([str(PYTHON), '-m', 'pip', '--version'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if probe.returncode != 0:
        print('Восстановление pip в окружении приложения…', flush=True)
        # A previous dependency stamp is not valid for a damaged environment.
        STAMP.unlink(missing_ok=True)
        subprocess.run([str(PYTHON), '-m', 'ensurepip', '--upgrade', '--default-pip'], check=True)
        subprocess.run([str(PYTHON), '-m', 'pip', '--version'], check=True)


def main():
    if sys.version_info < (3, 10):
        raise SystemExit('Требуется Python 3.10 или новее.')
    os.chdir(ROOT)
    ensure_environment()
    digest = hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()
    if not STAMP.exists() or STAMP.read_text().strip() != digest:
        print('Установка зависимостей (при первом запуске нужен интернет)…', flush=True)
        subprocess.run([str(PYTHON), '-m', 'pip', 'install', '-r', str(REQUIREMENTS)], check=True)
        STAMP.write_text(digest)
    # Adds missing tables and base catalogs; existing projects are retained.
    subprocess.run([str(PYTHON), '-m', 'app.seed'], cwd=ROOT / 'backend', check=True)
    port = int(os.environ.get('PASPORT_PORT', '8000'))
    url = f'http://127.0.0.1:{port}/app/index.html'
    print(f'Открыть приложение: {url}\nДля остановки нажмите Ctrl+C.', flush=True)
    if os.environ.get('PASPORT_NO_BROWSER') != '1':
        timer = threading.Timer(2, lambda: webbrowser.open(url))
        timer.daemon = True
        timer.start()
    try:
        subprocess.run([str(PYTHON), '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT / 'backend', check=True)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        raise SystemExit(f'Не удалось запустить приложение (код {error.returncode}). См. сообщение выше.')
