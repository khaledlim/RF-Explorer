"""
cli.py
Command-line interface entry point for RF Explorer.
Handles:
    - interactive mode
    - direct CLI mode (python/robot + regex)
    - --scan mode
    - --list mode
    - custom help/version
"""
import importlib, sys
from rich.console import Console

from rf_explorer.core import (
    interactive,
    list_python_functions,
    list_robot_keywords,
    select_and_show,
)

from rf_explorer.scanner import scan_modules, print_scan
from rf_explorer.utils import list_installed_packages, is_robot_library
from rf_explorer.core import search_robot_keywords

console = Console()

VERSION = "1.0.0"


ASCII_LOGO = r"""
  _____  ______    _____            _                      
 |  __ \|  ____|  | ____|_  ___ __ | | ___  _ __ ___  _ __ 
 | |__) | |__     |  _| \ \/ / '_ \| |/ _ \| '__/ _ \  '__|
 |  _  /|  __|    | |___ >  <| |_) | | (_) | | |  __/| |  
 |_| \_\|_|       |_____/_/\_\ .__/|_|\___/|_|  \___ |_|
                             |_|                      
                         RF EXPLORER
                                 
"""
# =============================================================================
# HELP
# =============================================================================

def print_help():
    console.print(ASCII_LOGO, style="magenta")

    console.print(
        "[bold cyan]Usage:[/bold cyan]\n"
        "  rf-explorer                       Run interactive explorer\n"
        "  rf-explorer --help                Show help message\n"
        "  rf-explorer --version             Show version\n"
        "\n"
        "  rf-explorer --scan                Scan Python & Robot libraries\n"
        "  rf-explorer --scan robot          Scan only Robot Framework libs\n"
        "  rf-explorer --scan python         Scan only Python modules\n"
        "  rf-explorer --scan --all          Full scan + unknown modules\n"
        "  rf-explorer --scan --all          Full scan + unknown modules\n"
        "\n"
        "  rf-explorer --list                Equivalent of 'pip list'\n"
        "  rf-explorer --list --filter       Equivalent of 'pip list' with filter\n"
        "  rf-explorer --search <[bold magenta]keyword[/bold magenta]>    Search robot keywords in libraries\n"
        "\n"
        "  rf-explorer python <module> [regex |--all]\n"
        "  rf-explorer robot <[bold magenta]library[/bold magenta]> [regex | --all]\n"
       
    )

# =============================================================================
# MAIN
# =============================================================================

def cli():
    args = sys.argv[1:]

    # ------------------------------------
    # HELP / VERSION
    # ------------------------------------
    if len(args) == 1 and args[0] in ("--help", "-h"):
        print_help()
        return

    if len(args) == 1 and args[0] in ("--version", "-v"):
        console.print(f"rf-explorer version [bold green]{VERSION}[/bold green]")
        return

    # ------------------------------------
    # INTERACTIVE (no args)
    # ------------------------------------
    if len(args) == 0:
        console.print(ASCII_LOGO, style="magenta")
        try:
            interactive()
        except KeyboardInterrupt:
            console.print("\n[red]Interruption detected. Exiting...[/red]")
        return

    # =============================================================================
    # --LIST : pip list
    # =============================================================================
    if args[0] == "--list":

        filter_value = None
        i = 1

        while i < len(args):
            arg = args[i]

            if arg in ("--filter", "-f"):
                if i + 1 >= len(args):
                    console.print("[red]ERROR: Missing value after --filter/-f[/red]")
                    return
                filter_value = args[i + 1]
                i += 2
                continue

            console.print(f"[red]ERROR: Unexpected argument:[/red] {arg}")
            return

        list_installed_packages(filter_value)
        return

    # =============================================================================
    # --SCAN : module scanning
    # =============================================================================
    if args[0] == "--scan":

        # --- No argument after --scan → ERROR ---
        if len(args) == 1:
            console.print(
                "[red]ERROR: --scan requires one of:[/red]\n"
                "  robot | python | --all\n"
                "\n[magenta]Examples:[/magenta]\n"
                "  rf-explorer --scan robot\n"
                "  rf-explorer --scan python\n"
                "  rf-explorer --scan --all\n"
            )
            return

        mode = args[1]

        # --- Invalid mode → ERROR ---
        if mode not in ("robot", "python", "--all"):
            console.print(
                f"[red]ERROR: Invalid scan mode '{mode}'[/red]\n"
                "Valid options are:\n"
                "  robot | python | --all\n"
            )
            return

        # --- Extra arguments → ERROR ---
        if len(args) > 2:
            extra = " ".join(args[2:])
            console.print(
                f"[red]ERROR: Unexpected extra arguments:[/red] {extra}\n"
                f"Usage: rf-explorer --scan {mode}\n"
            )
            return

        # --- Normal execution ---
        filter_type = None
        show_all = False

        if mode == "robot":
            filter_type = "robot"
        elif mode == "python":
            filter_type = "python"
        elif mode == "--all":
            show_all = True

        result = scan_modules()
        print_scan(result, show_all=show_all, filter_type=filter_type)
        return

    # =============================================================================
    # --SEARCH : keyword search
    # =============================================================================

    if args[0] == "--search":

        try:
            # Missing argument
            if len(args) == 1:
                console.print(
                    "[red]ERROR:[/red] --search requires a keyword or regex.\n"
                    "\n[magenta]Examples:[/magenta]\n"
                    "  rf-explorer --search browser\n"
                    "  rf-explorer --search json\n"
                    "  rf-explorer --search file\n"
                )
                return

            pattern = args[1]

            # Extra unexpected arguments
            if len(args) > 2:
                console.print(
                    f"[red]ERROR:[/red] Unexpected extra arguments: {' '.join(args[2:])}\n"
                    "Usage:\n"
                    "  rf-explorer --search <keyword or regex>\n"
                )
                return
            
            if pattern.startswith("-"):
                console.print(
                    f"[red]ERROR:[/red] Invalid search parameter: [yellow]{pattern}[/yellow]\n")
                return
            
            # Execute the search
            try:
                search_robot_keywords(pattern)
            except KeyboardInterrupt:
                console.print("[yellow]Search cancelled by user.[/yellow]")
                return
            except Exception as e:
                console.print(
                    "[red]ERROR during search execution.[/red]\n"
                )
                return

            return

        except KeyboardInterrupt:
            console.print("\n[yellow] Search cancelled by user.[/yellow]")
            return

        except Exception as e:
            console.print("[red]FATAL ERROR in --search[/red]")
            return
        
    # =============================================================================
    # PYTHON MODE
    # =============================================================================
    if args[0] == "python":
        if len(args) < 2:
            console.print("[red]Usage: rf-explorer python <module> [regex|--all][/red]")
            return

        module = args[1]

        try:
            importlib.import_module(module)
        except ModuleNotFoundError:
            console.print(f"[red]Module '{module}' was not found.[/red]")
            return

        regex = None
        if len(args) >= 3 and args[2] not in ("--all", "-all"):
            regex = args[2]

        funcs = list_python_functions(module, regex)

        if regex and not funcs:
            console.print(f"[yellow]No functions matching '{regex}' found.[/yellow]")
            return

        if not regex and not funcs:
            console.print(f"[red]Module '{module}' has no public functions.[/red]")
            return

        try:
            select_and_show(funcs, module, is_python=True)
        except KeyboardInterrupt:
            console.print("[red]Interruption detected. Exiting...[/red]")
        return

    # =============================================================================
    # ROBOT MODE
    # =============================================================================

    if args[0] == "robot":

        if len(args) < 2:
            console.print("[red]Usage: rf-explorer robot <library> [regex|--all][/red]")
            return

        library = args[1]

        if not is_robot_library(library):
            console.print(f"[red]{library} is not a Robot Framework library.[/red]")
            return

        regex = None
        if len(args) >= 3 and args[2] not in ("--all", "-all"):
            regex = args[2]

        kws = list_robot_keywords(library, regex)

        if regex and not kws:
            console.print(f"[yellow]No keywords matching '{regex}' found.[/yellow]")
            return

        if not regex and not kws:
            console.print(f"[red]Library '{library}' has no public keywords.[/red]")
            return

        try:
            select_and_show(kws, library, is_python=False)
        except KeyboardInterrupt:
            console.print("[red]Interruption detected. Exiting...[/red]")

        return
    
    # =============================================================================
    # UNKNOWN COMMAND
    # =============================================================================
    console.print(
        f"[red]Unknown command:[/red] {args[0]}\n"
        "Use: rf-explorer --help"
    )
