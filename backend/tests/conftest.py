import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Isolated, offline, deterministic test environment
os.environ["LLM_PROVIDER"] = "offline"
os.environ["ENABLE_LIVE_URL_CHECKS"] = "false"
os.environ["DATABASE_PATH"] = str(Path(tempfile.mkdtemp()) / "test.db")
