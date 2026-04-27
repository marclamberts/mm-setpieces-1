from pathlib import Path

_WRAPPER_FILE = Path(__file__).resolve()
_TEMPLATE_FILE = _WRAPPER_FILE.parent / "mm_setpieces" / "page_template.py"
_WRAPPER_GLOBALS = globals()
_WRAPPER_GLOBALS["__file__"] = str(_TEMPLATE_FILE)
exec(_TEMPLATE_FILE.read_text(), _WRAPPER_GLOBALS)
_WRAPPER_GLOBALS["__file__"] = str(_WRAPPER_FILE)
