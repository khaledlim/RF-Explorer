"""
python_doc.py
Handles the documentation rendering for Python functions/classes inside RF Explorer.
"""

import inspect
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from rf_explorer.utils import compute_code_width

console = Console()

# ---------------------------------------------------------------------------
# Main Python Documentation Renderer
# ---------------------------------------------------------------------------

def show_python_doc(obj):
    """
    Display Python documentation for a function, method, or class.
    Supports:
        - signature
        - docstring
        - doctest blocks (>>> ...), grouped correctly
        - plain text documentation
    """

    # ---------------------------------------------------------
    # Header panel
    # ---------------------------------------------------------
    name = obj.__name__ if hasattr(obj, "__name__") else str(obj)
    console.print(
        Panel(
            f"[bold blue]{name}[/bold blue]",
            title="[bold magenta]Function[/bold magenta]",
            expand=False,
        )
    )

    # ---------------------------------------------------------
    # Signature
    # ---------------------------------------------------------
    try:
        sig = str(inspect.signature(obj))
    except Exception:
        sig = "()"

    console.print(f"[bold magenta]Signature:[/bold magenta]\n{name}{sig}\n")

    # ---------------------------------------------------------
    # Docstring
    # ---------------------------------------------------------
    doc = inspect.getdoc(obj) or ""
    if not doc.strip():
        console.print("[grey58]No documentation available.[/grey58]")
        return

    console.print("[bold magenta]Documentation:[/bold magenta]\n")

    lines = doc.splitlines()

    # ---------------------------------------------------------
    # DOCTEST GROUPING
    # ---------------------------------------------------------
    doctest_block = []
    in_doctest = False

    def flush_doctest():
        """Render and clear accumulated doctest lines."""
        nonlocal doctest_block

        if not doctest_block:
            return

        width = compute_code_width(doctest_block)
        code = "\n".join(doctest_block)

        console.print(
            Syntax(
                code,
                "python",
                theme="monokai",
                line_numbers=False,
                code_width=width,
                background_color="#262626",
            )
        )
        console.print("")

        doctest_block = []

    # ---------------------------------------------------------
    # Parsing loop
    # ---------------------------------------------------------
    for line in lines:
        stripped = line.strip()

        # Start doctest line
        if stripped.startswith(">>>") or stripped.startswith("..."):
            in_doctest = True
            doctest_block.append(stripped)
            continue

        # If inside doctest block, consume continuation/result lines
        if in_doctest:
            if stripped != "":
                doctest_block.append(stripped)
                continue
            else:
                # blank line ends the doctest block
                flush_doctest()
                in_doctest = False
                console.print("")
                continue

        # Outside doctest: normal text
        flush_doctest()
        console.print(line, style="white")

    # End-of-loop flush
    flush_doctest()