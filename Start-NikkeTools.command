#!/bin/zsh
set -eu
cd -- "${0:A:h}"
export PATH="/opt/homebrew/opt/node@24/bin:/opt/homebrew/bin:$PATH"
if [[ ! -x .venv/bin/python ]]; then
  print -u2 '先にdocs/mac-migration.mdのPython環境セットアップを実行してください。'
  exit 1
fi
if ! command -v node >/dev/null; then
  print -u2 'Node 24が必要です。brew install node@24 を実行してください。'
  exit 1
fi
export NIKKE_PYTHON="$PWD/.venv/bin/python"
exec node server.mjs
