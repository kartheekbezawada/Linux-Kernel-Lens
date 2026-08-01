"""Minimal, dependency-free PDF writer.

A real PDF library (weasyprint/reportlab) is the normal way to do this, but
both pull in a large dependency tree for what is fundamentally "print some
lines of text on pages." PDF's text-object syntax is simple enough to
generate directly: this writes a valid single-font, left-aligned, paginated
PDF using only the standard library.
"""

from __future__ import annotations

PAGE_WIDTH = 612  # US Letter, in PDF points (72 points/inch)
PAGE_HEIGHT = 792
MARGIN = 50
FONT_SIZE = 10
LINE_HEIGHT = 14
LINES_PER_PAGE = (PAGE_HEIGHT - 2 * MARGIN) // LINE_HEIGHT


def _escape(text: str) -> str:
    """Escape the three characters that are special inside a PDF string literal."""
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _wrap(line: str, max_chars: int = 95) -> list[str]:
    """Hard-wrap a line to max_chars -- no real font-metrics-based wrapping,
    just enough to keep long evidence/recommendation strings from running
    off the page edge."""
    if len(line) <= max_chars:
        return [line]
    words = line.split(" ")
    wrapped, current = [], ""
    for word in words:
        if len(current) + len(word) + 1 > max_chars:
            wrapped.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        wrapped.append(current)
    return wrapped


def _paginate(lines: list[str]) -> list[list[str]]:
    pages = []
    for i in range(0, len(lines), LINES_PER_PAGE):
        pages.append(lines[i : i + LINES_PER_PAGE])
    return pages or [[]]


def build_pdf(lines: list[str]) -> bytes:
    """Turn a flat list of text lines into a minimal multi-page PDF."""
    wrapped_lines = [w for line in lines for w in _wrap(line)]
    pages = _paginate(wrapped_lines)

    objects: list[bytes] = []

    def add_object(body: bytes) -> int:
        objects.append(body)
        return len(objects)  # PDF object numbers are 1-indexed

    font_obj = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_obj_numbers = []
    content_obj_numbers = []
    for page_lines in pages:
        content_lines = [f"BT /F1 {FONT_SIZE} Tf {MARGIN} {PAGE_HEIGHT - MARGIN} Td {LINE_HEIGHT} TL"]
        for line in page_lines:
            content_lines.append(f"({_escape(line)}) Tj T*")
        content_stream = "\n".join(content_lines) + "\nET"
        content_bytes = content_stream.encode("latin-1", errors="replace")
        content_obj_numbers.append(
            add_object(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content_bytes), content_bytes))
        )

    pages_placeholder = add_object(b"")  # filled in below once page objects exist
    for content_num in content_obj_numbers:
        page_obj_numbers.append(
            add_object(
                (
                    "<< /Type /Page /Parent %d 0 R /Resources << /Font << /F1 %d 0 R >> >> "
                    "/MediaBox [0 0 %d %d] /Contents %d 0 R >>"
                    % (pages_placeholder, font_obj, PAGE_WIDTH, PAGE_HEIGHT, content_num)
                ).encode("ascii")
            )
        )

    kids = " ".join(f"{n} 0 R" for n in page_obj_numbers)
    objects[pages_placeholder - 1] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_obj_numbers)} >>".encode("ascii")
    )

    catalog_obj = add_object(f"<< /Type /Catalog /Pages {pages_placeholder} 0 R >>".encode("ascii"))

    # Assemble the file: header, each object with its byte offset tracked for
    # the xref table, then the trailer pointing at the catalog.
    buffer = bytearray(b"%PDF-1.4\n")
    offsets = [0] * (len(objects) + 1)
    for i, body in enumerate(objects, start=1):
        offsets[i] = len(buffer)
        buffer += f"{i} 0 obj\n".encode("ascii") + body + b"\nendobj\n"

    xref_offset = len(buffer)
    buffer += f"xref\n0 {len(objects) + 1}\n".encode("ascii")
    buffer += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        buffer += f"{offset:010d} 00000 n \n".encode("ascii")

    buffer += (
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_obj} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF"
    ).encode("ascii")

    return bytes(buffer)
