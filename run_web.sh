#!/bin/bash
# Streamlit launch wrapper
# Do NOT set --browser.serverAddress — let the browser derive the WebSocket
# URL from window.location so it automatically uses wss:// over HTTPS proxy.
exec /home/runner/workspace/.pythonlibs/bin/streamlit run web/app.py \
  --server.port 8099 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection false \
  --browser.gatherUsageStats false
