#!/bin/zsh
cd -- "$(dirname -- "$0")" || exit 1
python3 start.py
if [ $? -ne 0 ]; then
  printf '\nНе удалось запустить приложение. Проверьте наличие Python 3.10+.\n'
  read '?Нажмите Enter для закрытия…'
fi
