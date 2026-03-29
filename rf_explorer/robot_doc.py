"""
robot_doc.py
Rendering logic for Robot Framework keyword documentation in RF Explorer.
"""

import re
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich import box

from rf_explorer.utils import (
    compute_code_width,
    convert_pipe_table,
    split_robot_sections,
)

console = Console()


# ------------------------------------------------------------------------------------------
# Render raw Robot Framework doc text into Rich-friendly Markdown-like output
# ------------------------------------------------------------------------------------------
def render_robot_doc(text: str):
    """
    Render generic Robot Framework documentation text.A
    Handles:
        - blank lines
        - plain text
        - table-like content
        - section headers
        - pipe-style table rows
    """

    lines = text.splitlines()

    section_pattern = re.compile(
        r"^\s*(Parameters|Returns|Raises|See Also|Notes|Examples|Attributes|Methods)\b",
        re.IGNORECASE,
    )

    for raw in lines:
        stripped = raw.strip()

        if not stripped:
            console.print("")
            continue

        if section_pattern.match(stripped):
            console.print(f"[bold cyan]{stripped}[/bold cyan]")
            continue

        if "|" in raw:
            console.print(raw, style="green")
            continue

        console.print(raw, style="white")


# ------------------------------------------------------------------------------------------
# Main Keyword Renderer
# ------------------------------------------------------------------------------------------

def show_robot_doc(kw: dict, library_name: str):
    """
    Display a full Robot Framework keyword documentation block:
        - title panel
        - argument table
        - description
        - argument details
        - examples (Robot syntax highlighted)
    """

    # ----------------------------------------
    # Title Block
    # ----------------------------------------
    console.print(
        Panel(
            f"[bold blue]{kw['name']}[/bold blue]",
            title="[bold magenta]Keyword[/bold magenta]",
            expand=False,
        )
    )

    # ----------------------------------------
    # Arguments
    # ----------------------------------------
    console.print("\n[bold magenta]Arguments:[/bold magenta]")

    args = kw.get("args", [])

    if args:
        table = Table(
            show_header=True,
            header_style="bold yellow",
            box=box.MINIMAL,
            border_style="white",
        )

        table.add_column("Name", style="white")
        table.add_column("Type", style="white")
        table.add_column("Default", style="white")

        for arg in args:
            raw = str(arg).strip()

            if "=" in raw:
                left, default = raw.split("=", 1)
                left, default = left.strip(), default.strip()
            else:
                left, default = raw, ""

            if ":" in left:
                name, typ = left.split(":", 1)
                name, typ = name.strip(), typ.strip()
            else:
                name, typ = left, ""

            typ = re.sub(r"\s*\|\s*", " | ", typ)
            table.add_row(name, typ, default)

        console.print(table)
    else:
        console.print("[grey58]None[/grey58]")

    # ----------------------------------------
    # DOCUMENTATION SECTIONS
    # -----------------------------------------
    doc_text = kw.get("doc") or ""
    sections = split_robot_sections(doc_text)

    description = sections["description"]
    arg_details = sections["arguments"]
    examples_text = sections["examples"]

    console.print("\n[bold magenta]Description:[/bold magenta]\n")
    render_robot_doc(description)

    if arg_details.strip():
        console.print("\n[bold magenta]Argument details:[/bold magenta]\n")
        render_robot_doc(arg_details)

    # ----------------------------------------
    # EXAMPLES
    # ----------------------------------------
    if not examples_text.strip():
        return

    console.print("\n[bold magenta]Examples:[/bold magenta]\n")

    EX_HEADER = re.compile(
        r"^\s*[\*\-=]*\s*(?:Exemples?|Examples?)\s*[\*\-=]*\s*$",
        re.IGNORECASE,
    )

    lines = [l.rstrip() for l in examples_text.splitlines() if l.strip()]

    # Skip header
    if lines and EX_HEADER.match(lines[0]):
        lines = lines[1:]

    # ----------------------------------------
    # RST code-block parser
    # ----------------------------------------
    rst_header = re.compile(r"^\s*\.\.\s*code-block::\s*(\w+)", re.I)

    in_rst = False
    rst_lang = None
    rst_buf = []
    next_title = None

    def flush_rst():
        nonlocal rst_buf, rst_lang, next_title
        if not rst_buf:
            return

        if next_title == "robot":
            console.print("[bold cyan]Robot Framework:[/bold cyan]\n")
        elif next_title == "python":
            console.print("[bold cyan]Python:[/bold cyan]\n")

        # Add RF header for RPA libs
        if rst_lang == "robotframework" and library_name.startswith("RPA"):
            rst_buf = ["    " + line for line in rst_buf]
            rst_buf = [
                "*** Settings ***",
                f"Library    {library_name}",
                "",
                "*** Tasks ***",
                "Example",
                "",
            ] +  rst_buf

        width = compute_code_width(rst_buf)

        console.print(
            Syntax(
                "\n".join(rst_buf),
                rst_lang,
                theme="monokai",
                code_width=width,
                background_color="#262626",
                line_numbers=False,
            )
        )
        console.print("")
        rst_buf.clear()
        rst_lang = None
        next_title = None

    # ----------------------------------------
    # TABLE buffer parser
    # ----------------------------------------
    buffer = []

    def flush_buffer():
        nonlocal buffer
        if not buffer:
            return
        
        table_lines = convert_pipe_table(buffer)

        if table_lines:
            # Add indentation for lines after "Example"
            table_lines = [line for line in table_lines]

            if library_name.startswith("RPA"):
                full_block = [
                    "*** Settings ***",
                    f"Library    {library_name}",
                    "",
                    "*** Tasks ***",
                    "Example",
                ] + "t" + table_lines
            else:
                full_block = [
                    "*** Settings ***",
                    f"Library    {library_name}",
                    "",
                    "*** Test Cases ***",
                    "Example",
                ] + table_lines

            width = compute_code_width(full_block)

            console.print(
                Syntax(
                    "\n".join(full_block),
                    "robotframework",
                    theme="monokai",
                    code_width=width,
                    background_color="#262626",
                    line_numbers=False,
                )
            )
            console.print("")
        else:
            for l in buffer:
                render_robot_doc(l)

        buffer = []

    # ----------------------------------------
    # MAIN LOOP (Examples parsing)
    # ----------------------------------------

    EXPECTED_RESULTS = re.compile(
    r"^\s*[#>\-*\s]*\s*(?:résultat attendu|résultats attendus|expected results?)\s*:?\s*$",
    re.IGNORECASE)
    
    in_expected_results = False

    for l in lines:

        l_strip = l.strip()

        # Detection Start of bloc Expected Results 
        if re.match(EXPECTED_RESULTS, l_strip):
            flush_buffer()
            flush_rst()
            in_expected_results = True
            render_robot_doc(l)
            continue

        # Bloc "Expected Results"
        if in_expected_results:
            if "|" in l:
                # Line table of Expected Results
                render_robot_doc(l)
                continue
            else:
                # End of bloc Expected Results
                in_expected_results = False

        # Detection RST code-block
        rst_match = rst_header.match(l_strip)
        if rst_match:
            flush_buffer()
            flush_rst()
            in_rst = True
            rst_lang = rst_match.group(1).lower()
            continue

        # Bloc RST code-block
        if in_rst:
            indent_match = re.match(r"(\s+)(.*)", l)
            if indent_match:
                rst_buf.append(indent_match.group(2))
                continue
            else:
                flush_rst()
                in_rst = False

        # Tables  (hors Expected Results)
        if "|" in l and l.count("|") >= 1:
            buffer.append(l)
            continue

        # Texte
        flush_buffer()
        render_robot_doc(l)

    # Flush final
    flush_buffer()
    flush_rst()
    console.print("")