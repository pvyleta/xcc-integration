#!/bin/bash

echo "🔧 Fixing HACS configuration and creating new release..."

# Add and commit the hacs.json fix
git add hacs.json
git commit -m "fix: Remove filename field from hacs.json to fix HACS download

- Removed 'filename' field that was causing HACS to look for non-existent release asset
- HACS will now use source code download method properly
- This should resolve the 404 error when downloading via HACS"

# Push the changes
git push origin main

# Create new tag
git tag v1.2.2

# Push the tag
git push origin v1.2.2

# Create GitHub release
gh release create v1.2.2 \
  --title "XCC Integration v1.2.2 - HACS Download Fix" \
  --notes "## 🔧 Critical HACS Fix

**Fixed HACS Download Issue**: Removed problematic filename field from hacs.json that was causing 404 errors.

HACS should now properly download and install the integration using source code method.

### Installation
1. Remove old version from HACS if installed
2. Re-add custom repository: https://github.com/pvyleta/xcc-integration  
3. Install XCC Heat Pump Controller v1.2.2
4. Restart Home Assistant
5. Add integration via Settings > Devices & Services"

echo "✅ Done! Try installing v1.2.2 from HACS now."
