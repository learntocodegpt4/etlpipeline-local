#!/bin/sh
set -e

# Normalize encodings and strip null bytes in Python sources when bind-mounted from Windows
if command -v file >/dev/null 2>&1; then
  for f in $(find /app/src -type f -name "*.py"); do
    enc=$(file -bi "$f" 2>/dev/null || echo "")
    case "$enc" in
      *charset=utf-16*)
        # Convert UTF-16 -> UTF-8
        if command -v iconv >/dev/null 2>&1; then
          iconv -f utf-16 -t utf-8 "$f" -o "${f}.utf8" && mv "${f}.utf8" "$f"
        else
          # Fallback: strip nulls (crude but prevents interpreter error)
          tr -d '\000' < "$f" > "${f}.nn" && mv "${f}.nn" "$f"
        fi
        ;;
      *)
        # Strip any stray nulls
        tr -d '\000' < "$f" > "${f}.nn" && mv "${f}.nn" "$f"
        ;;
    esac
  done
fi

# Normalize CRLF line endings
find /app/src -type f -name "*.py" -exec dos2unix {} + 2>/dev/null || true

# Launch the app
exec python run.py
