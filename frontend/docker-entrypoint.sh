#!/bin/sh
npm install --prefer-offline --no-audit 2>/dev/null || npm install --no-audit
exec "$@"
