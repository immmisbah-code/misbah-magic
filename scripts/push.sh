#!/bin/bash
cd /Users/misbah/Desktop/misbah-magic
git add -A
git commit -m "feat: complete professional rebuild v2.0

- Modular Flask blueprint backend (auth, reconciliation, reports)
- Clean frontend with 4 CSS files + 7 JS modules
- Reactive state management (state.js)
- Drag-and-drop file uploader (uploader.js)
- Animated results table with tabs + search (results.js)
- Toast notifications, progress bar, loading overlay (ui.js)
- Excel/CSV and PDF+AI reconciliation modes
- Served from Flask (no CORS issues)"

git push origin main
echo ""
echo "Done! Visit: http://localhost:8080"
