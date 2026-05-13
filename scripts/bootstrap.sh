#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/clubosvenv"
WEB_DIR="${ROOT_DIR}/apps/clubos-web"
PYTHON_CMD="${PYTHON_CMD:-python3.11}"

echo "==> ClubOS bootstrap starting"
echo "Root: ${ROOT_DIR}"

if ! command -v "${PYTHON_CMD}" >/dev/null 2>&1; then
  echo "Error: ${PYTHON_CMD} is required but was not found."
  echo "Install Python 3.11 and rerun bootstrap."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "Error: npm is required but was not found."
  exit 1
fi

PYTHON_VERSION="$(${PYTHON_CMD} -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
echo "Detected Python via ${PYTHON_CMD}: ${PYTHON_VERSION}"

PYTHON_MAJOR_MINOR="$(${PYTHON_CMD} -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')"
if [[ "${PYTHON_MAJOR_MINOR}" != "3.11" ]]; then
  echo "Error: ClubOS requires Python 3.11.x. Detected ${PYTHON_VERSION}."
  exit 1
fi

echo "==> Creating/updating virtual environment: clubosvenv"
${PYTHON_CMD} -m venv "${VENV_DIR}"

echo "==> Activating clubosvenv"
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "==> Upgrading pip"
python -m pip install --upgrade pip

echo "==> Installing Python dependencies"
pip install -r "${ROOT_DIR}/requirements/dev.txt"

echo "==> Installing frontend dependencies"
cd "${WEB_DIR}"
npm install

echo
echo "Bootstrap complete."
echo
echo "Next steps:"
echo "1. Activate Python env: source clubosvenv/bin/activate"
echo "2. Start frontend: cd apps/clubos-web && npm run dev"
echo "3. Start backend later from backend/api once API implementation advances"
echo "4. Optional live Databricks mode: pip install databricks-sql-connector==4.2.6"
