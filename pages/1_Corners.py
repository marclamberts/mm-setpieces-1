from pathlib import Path

_PAGE_FILE = Path(__file__).resolve()
_TEMPLATE_FILE = _PAGE_FILE.parents[1] / "mm_setpieces" / "page_template.py"
_PAGE_GLOBALS = globals()
_PAGE_GLOBALS["__file__"] = str(_TEMPLATE_FILE)
exec(_TEMPLATE_FILE.read_text(), _PAGE_GLOBALS)
_PAGE_GLOBALS["__file__"] = str(_PAGE_FILE)

render_page('Corners')
