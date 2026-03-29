"""
core.py
Main interactive engine for RF Explorer.
Handles:
    - interactive menu for Python & Robot Framework exploration
    - search & selection system
    - stable Ctrl+C behavior (always exit)
    - Back returns normally
"""
import importlib
import inspect
import re, sys
from rich.console import Console
from InquirerPy import inquirer

from rf_explorer.python_doc import show_python_doc
from rf_explorer.robot_doc import show_robot_doc
from rf_explorer.utils import delete_log_files, is_robot_library
from rf_explorer.scanner import scan_modules

console = Console()

# Try import Robot Framework
try:
    from robot.libdoc import LibraryDocumentation
except ImportError:
    LibraryDocumentation = None

# =============================================================================
# PYTHON: DISCOVERY
# =============================================================================

def list_python_functions(module_name: str, regex= None):
    """Return list of (name, object) for all public functions/classes."""

    if not module_name or not module_name.strip():
        console.print("\n[red] Module name cannot be empty.[/red]")
        return 
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        console.print(f"\n[red] Module '{module_name}' not found or cannot be loaded.[/red]")
        return

    results = []

    # Functions
    for name, func in inspect.getmembers(module, inspect.isroutine):
        if not name.startswith("_"):
            results.append((name, func))

    # Classes + methods
    for cls_name, cls in inspect.getmembers(module, inspect.isclass):
        if cls_name.startswith("_"):
            continue

        results.append((cls_name, cls))

        for mname, method in inspect.getmembers(cls, inspect.isfunction):
            if not mname.startswith("_"):
                results.append((f"{cls_name}.{mname}", method))

    # Regex filter
    if regex:
        pattern = re.compile(regex, re.IGNORECASE)
        results = [(name, obj) for (name, obj) in results if pattern.search(name)]

    return results


# =============================================================================
# ROBOT FRAMEWORK: DISCOVERY
# =============================================================================

def list_robot_keywords(lib_name: str, regex= None):
    
    if not lib_name or not lib_name.strip():
        console.print("[red]\n Library name cannot be empty.[/red]")
        return 

    if LibraryDocumentation is None:
        console.print("[red]Robot Framework is not installed.[/red]")
        return 

    # Verify if it's a valid Robot library (built‑in or standard)
    if not is_robot_library(lib_name):
        console.print(f"[red] Library '{lib_name}' not found or cannot be loaded.[/red]")
        return

    # Built‑in libraries → libdoc auomatically loads them
    try:
        libdoc = LibraryDocumentation(lib_name)
    except Exception:
        return
    #delete_log_files()

    # Extract public keywords
    keywords = [
        {"name": kw.name, "args": kw.args, "doc": kw.doc}
        for kw in libdoc.keywords
        if not kw.name.startswith("_")
    ]

    # Filter with regex if provided
    if regex:
        pattern = re.compile(regex, re.IGNORECASE)
        keywords = [k for k in keywords if pattern.search(k["name"])]

    return keywords


# =============================================================================
# ROBOT FRAMEWORK Keyword Browser
# =============================================================================
def interactive_keyword_browser(keyword_list):
    """
    Shows an interactive menu to browse found keywords.
    Clicking one shows documentation.
    """
    if not keyword_list:
        console.print("[yellow]No keywords matched your search.[/yellow]")
        return

    # Build choices for Inquirer
    choices = [
        f"{entry['lib']}.{entry['name']}"
        for entry in keyword_list
    ]
    choices.insert(0, "← Back")

    while True:
        selected = inquirer.select(
            message="Select a keyword:",
            choices=choices
        ).execute()

        if selected == "← Back":
            return

        # Find selected keyword
        for entry in keyword_list:
            if f"{entry['lib']}.{entry['name']}" == selected:
                show_robot_doc(entry, entry["lib"])
                console.print("\n[cyan]Press ENTER to go back...[/cyan]")
                input()
                break


# ---------------------------------------------------------------------------
# Search ALL nstalled Robot Framework libraries
# ---------------------------------------------------------------------------

def search_robot_keywords(pattern: str):
    """
    Search Robot Framework keywords across all detected Robot libraries.
    """
    # Get scanned modules list

    result = scan_modules()

    robot_libs = result["robot"]  
    matches = []
    regex = re.compile(pattern, re.IGNORECASE)

    # Search inside real Robot libraries
    for lib_name, kw_count in robot_libs:

        # Load Robot library documentation
        try:
            libdoc = LibraryDocumentation(lib_name)
        except Exception:
            continue 
        delete_log_files()

        # Search matching keywords
        for kw in libdoc.keywords:
            if regex.search(kw.name):
                matches.append({
                    "lib": lib_name,
                    "name": kw.name,
                    "args": kw.args,
                    "doc": kw.doc
                })

    # No result
    if not matches:
        console.print(f"[yellow] No keywords found matching:[/yellow] [cyan]{pattern}[/cyan]")
        return


    # Build choice list for interactive menu
    choices = [f"{m['lib']}.{m['name']}" for m in matches]
    choices.insert(0, "← Back")

    while True:
        console.print(f"[bold cyan]{len(matches)}[/bold cyan] [bold yellow]keywords Found[/bold yellow]\n")
        selected = inquirer.select(
            message= "Select a Keyword (Ctrl+C to exit):",
            choices=choices
        ).execute()

        # Back to CLI
        if selected == "← Back":
            return

    
        # Show selected keyword documentation
    
        for entry in matches:
            full = f"{entry['lib']}.{entry['name']}"
            if full == selected:
                show_robot_doc(entry, entry["lib"])
                console.print("\n[cyan]Press ENTER to continue...[/cyan]")
                input()
                break
            
# =============================================================================
# MENU SELECTION
# =============================================================================

def select_and_show(items, module_name=None, is_python=None):
    """Displays menu and opens doc viewer."""

    if not items:
        console.print("[red]No items to display.[/red]")
        return

    # auto detect type
    if is_python is None:
        is_python = isinstance(items[0], tuple)

    console.print("\n[bold white]────────────────────────────────────────────[/bold white]")

    if is_python:
        console.print(f"[bold yellow]Module:[/bold yellow] [bold cyan]{module_name}[/bold cyan]")
        console.print(f"[bold yellow]Total functions:[/bold yellow] [bold cyan]{len(items)}[/bold cyan]")
    else:
        console.print(f"[bold yellow]Library:[/bold yellow] [bold cyan]{module_name}[/bold cyan]")
        console.print(f"[bold yellow]Total keywords:[/bold yellow] [bold cyan]{len(items)}[/bold cyan]")

    console.print("[bold white]────────────────────────────────────────────[/bold white]\n")

    while True:
        # build choices
        if is_python:
            choices = [name for name, _ in items]
        else:
            choices = [kw["name"] for kw in items]

        choices.insert(0, "← Back")

        try:
            selected = inquirer.select(
                message="Select an item (Ctrl+C to exit):",
                choices=choices,
                vi_mode=False,
            ).execute()
        except KeyboardInterrupt:
            console.print("\n[red]Interruption detected. Exiting...[/red]")
            sys.exit(0)

        if selected == "← Back":
            console.print("[cyan]Returning to previous menu...[/cyan]\n")
            return

        # Python doc viewer
        if is_python:
            for name, func in items:
                if name == selected:
                    show_python_doc(func)
                    console.print("\n[cyan]Press ENTER to return...[/cyan]")
                    input()
                    break

        # Robot doc viewer
        else:
            for kw in items:
                if kw["name"] == selected:
                    show_robot_doc(kw, module_name)
                    console.print("\n[cyan]Press ENTER to return...[/cyan]")
                    input()
                    break

# =============================================================================
# MAIN INTERACTIVE ENGINE
# =============================================================================

def interactive():
    """Main interactive mode for RF Explorer."""
    while True:
        try:
            console.print(
                "[bold underline magenta]RF EXPLORER — Interactive Mode[/bold underline magenta]\n"
            )

            lib_type = inquirer.select(
                message="Library type:",
                choices=["python", "robot"]
            ).execute()

            module_name = inquirer.text(
                message="Library/Module name:"
            ).execute().strip()

            regex = inquirer.text(
                message="Regex filter (optional):"
            ).execute().strip() or None

            # PYTHON MODE
            if lib_type == "python":
                funcs = list_python_functions(module_name, regex)
                
                if not funcs:
                    console.print("[yellow] No public functions found.[/yellow]\n")
                    continue

                select_and_show(funcs, module_name, is_python=True)

            # ROBOT MODE
            else:
                kws = list_robot_keywords(module_name, regex)

                if not kws:
                    console.print("[yellow] No public keywords found.[/yellow]\n")
                    continue

                select_and_show(kws, module_name, is_python=False)

        except KeyboardInterrupt:
            console.print("\n[red]Interruption detected. Exiting...[/red]")
            break


# Backward compatibility
main = interactive


if __name__ == "__main__":
    try:
        interactive()
    except KeyboardInterrupt:
        console.print("\n[red]Interruption detected. Exiting...[/red]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)