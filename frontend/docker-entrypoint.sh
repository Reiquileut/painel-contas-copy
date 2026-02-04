#!/bin/sh
# Generate runtime environment config from environment variables
# This allows changing API_URL without rebuilding the frontend image
cat > /usr/share/nginx/html/env-config.js <<EOF
window.__ENV__ = {
  VITE_API_URL: "${VITE_API_URL:-}",
};
EOF
exec "$@"
