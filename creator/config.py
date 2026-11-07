from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / '.tools'
SDK_VERSION = '1.0.4191.47'
SDK = TOOLS / 'webview2' / SDK_VERSION
BOOTSTRAPPER = TOOLS / 'MicrosoftEdgeWebview2Setup.exe'
ISCC = TOOLS / 'inno' / 'ISCC.exe'
PBKDF2_ITERATIONS = 210_000
MAX_DOCUMENT_BYTES = 49_000_000
