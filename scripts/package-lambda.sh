#!/bin/bash
set -eo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build"
PACKAGE_DIR="$BUILD_DIR/package"
SITE_DIR="$BUILD_DIR/site"
ZIP_PATH="$BUILD_DIR/lambda.zip"
IMAGE="public.ecr.aws/lambda/python:3.14"
MAX_UNPACKED_BYTES=$((220 * 1024 * 1024))

rm -rf "$PACKAGE_DIR" "$SITE_DIR" "$ZIP_PATH"
mkdir -p "$PACKAGE_DIR" "$SITE_DIR"

docker run --rm \
  --platform linux/amd64 \
  --entrypoint /bin/bash \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -e PIP_CACHE_DIR=/tmp/pip-cache \
  -v /etc/passwd:/etc/passwd:ro \
  -v /etc/group:/etc/group:ro \
  -v "$ROOT_DIR:/src:ro" \
  -v "$BUILD_DIR:/out" \
  "$IMAGE" \
  -lc 'set -eo pipefail
python -m pip install --no-cache-dir --target /out/package -r /src/requirements-lambda.txt
cp -R /src/src/seasonality_app /out/package/
cp /src/plot.py /src/iisd_colours.py /out/package/

cp -R /src/web/. /out/site/
mkdir -p /out/site/assets/fonts /out/site/assets/images /out/site/vendor
cp "/src/static/fonts/Proxima Nova Regular.ttf" /out/site/assets/fonts/proxima-nova-regular.ttf
cp "/src/static/fonts/Proxima Nova Semibold.ttf" /out/site/assets/fonts/proxima-nova-semibold.ttf
cp "/src/static/images/iisd-ela-logo-2019 1.jpg" /out/site/assets/images/iisd-ela-logo-2019.jpg
cp /out/package/plotly/package_data/plotly.min.js /out/site/vendor/plotly.min.js

python - <<'"'"'PY'"'"'
import shutil
from pathlib import Path

root = Path("/out/package")
for path in list(root.rglob("__pycache__")):
    if path.is_dir():
        shutil.rmtree(path)
for path in list(root.rglob("tests")):
    if path.is_dir():
        shutil.rmtree(path)
for path in root.rglob("*"):
    if path.suffix in (".pyc", ".pyo"):
        path.unlink()
PY'

UNPACKED_BYTES="$(du -sb "$PACKAGE_DIR" | cut -f1)"
if [ "$UNPACKED_BYTES" -gt "$MAX_UNPACKED_BYTES" ]; then
  echo "Lambda package is $UNPACKED_BYTES bytes; limit is $MAX_UNPACKED_BYTES bytes." >&2
  exit 1
fi

python3 - "$PACKAGE_DIR" "$ZIP_PATH" <<'PY'
import sys
import zipfile
from pathlib import Path

package_dir = Path(sys.argv[1])
zip_path = sys.argv[2]
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(item for item in package_dir.rglob("*") if item.is_file()):
        info = zipfile.ZipInfo(
            path.relative_to(package_dir).as_posix(),
            date_time=(1980, 1, 1, 0, 0, 0),
        )
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, path.read_bytes())
PY

du -sh "$PACKAGE_DIR" "$SITE_DIR"
ls -lh "$ZIP_PATH"
