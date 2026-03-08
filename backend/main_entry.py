"""
PyInstaller entry point — standalone binary for bundled distribution.
This file is separate from main.py to keep imports clean for PyInstaller.

NOTE: We import the app object directly (not as a string) so PyInstaller
can detect all dependencies. uvicorn.run() with a string path does NOT
work in frozen binaries.
"""
import os
import sys

# When frozen by PyInstaller, __file__ points inside the temp extraction dir.
# We do NOT manipulate sys.path here — the app and all modules are bundled.
import uvicorn
from backend.main import app  # direct import so PyInstaller bundles it

if __name__ == '__main__':
    port = int(os.environ.get('OPENTILL_PORT', 47821))
    uvicorn.run(app, host='127.0.0.1', port=port, reload=False)
