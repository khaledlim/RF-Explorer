"""
python_doc.py
Scan installed Python modules and Robot Framwork libraries
"""
import pkgutil
import os, sys
import pkgutil
import contextlib
from rich.console import Console
from rich.table import Table
from rf_explorer.utils import is_robot_library, list_rpa_libraries, delete_log_files

console = Console()

# Optional -> If Robot Framework is installed
try:
    from robot.libdoc import LibraryDocumentation
except ImportError:
    LibraryDocumentation = None


# ======================================================
# HELPERS
# ======================================================

@contextlib.contextmanager
def suppress_output():
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")
    try:
        yield
    finally:
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = old_out
        sys.stderr = old_err


def is_internal(name):
    return name.startswith("_") or "__" in name


def classify(name):
    lname = name.lower()

    if lname.endswith("library"):
        return "robot"
    if "robotframework" in lname or "rpa" in lname:
        return "robot"

    if "py" in lname:
        return "python"

    if name[0].isupper() and name.isalpha():
        return "robot"

    return "python"


def count_keywords(lib_name):

    if LibraryDocumentation is None:
        return 0
    try:
        with suppress_output():
            doc = LibraryDocumentation(lib_name)
            return len(doc.keywords)
    except Exception:
        return 0
    delete_log_files()

# ======================================================
# MAIN SCAN ENGINE
# ======================================================

def scan_modules():
    """Scan installed modules & classify them."""
    modules = sorted([name for _, name, _ in pkgutil.iter_modules()])

    modules.extend(list_rpa_libraries())
    modules = sorted(set(modules))

    console.log(f"🔍[magenta][b] Scan of [cyan]{len(modules)}[/cyan] modules...[/b][/magenta]\n")

    robot_libs = []
    python_libs = []
    unknown_libs = []
    skipped = 0

    for name in modules:
        if is_internal(name):
            skipped += 1
            continue

        category = classify(name)

        if category == "robot":
            kw_count = count_keywords(name)

            if kw_count == 0:
                if is_robot_library(name):
                    robot_libs.append((name, kw_count))
                else:
                    python_libs.append(name)
            else:
                robot_libs.append((name, kw_count))
        else:
            python_libs.append(name)

    return {
        "robot": robot_libs,
        "python": python_libs,
        "unknown": unknown_libs,
        "skipped": skipped
    }

# ======================================================
# PRINT RESULT (improved)
# ======================================================

def print_scan(result, show_all=False, filter_type=None):
    total_robot = len(result["robot"])
    total_python = len(result["python"])
    total_unknown = len(result["unknown"])
    total_skipped = result.get("skipped", 0)

    # Merge unknown into skipped
    merged_skipped = total_skipped + total_unknown

    total_all = total_robot + total_python + merged_skipped

    # ---------------- ROBOT SECTION ----------------
    if show_all or filter_type == "robot" or filter_type is None:
        table = Table(title=f"Robot Framework Libraries • [bold cyan]{total_robot}[/bold cyan] found",
                      title_style="bold yellow")
        table.title_justify = "left"
        table.add_column("Library", style="cyan", min_width=20)
        table.add_column("Keywords", style="green", min_width=5)
        for lib, kw in sorted(result["robot"]):
            table.add_row(lib, str(kw))

        console.print(table)
        console.print()

    # ---------------- PYTHON SECTION ---------------
    if show_all or filter_type == "python" or filter_type is None:
        table = Table(title=f"Python Modules • [bold cyan]{total_python}[/bold cyan] found",
                      title_style="bold yellow")
        table.add_column("Module", style="cyan")
        table.title_justify = "left"
        for mod in sorted(result["python"]):
            table.add_row(mod)

        console.print(table)
        console.print()

    # ---------------- INTERNAL MERGED --------------
    if show_all and merged_skipped:
        console.print(
            f"[dim] [bold cyan]{merged_skipped}[/bold cyan] internal/system modules skipped (hidden or not usable)[/dim]\n"
        )