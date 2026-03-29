# RF Explorer

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-stable-brightgreen)

📦 **PyPI:** https://pypi.org/project/lib-explorer/  
🌐 **GitHub:** https://github.com/khaledlim/rf-explorer


**RF Explorer** is an interactive command-line tool for exploring Python modules and Robot Framework libraries.  
It displays readable, syntax‑highlighted documentation directly in the terminal using **Rich**.

The tool can run in:

- **Interactive mode** (menu-driven text UI using Inquirer — runs in the terminal)
- **Direct mode** (CLI arguments)

---

## Features

- Explore **Python modules**: functions,  methods
- Explore **Robot Framework libraries**: keywords, arguments, examples
- Syntax‑highlighted documentation (Rich)
- Clean rendering of Robot Framework examples and pipe tables
- Colored ASCII banner

### CLI shortcuts:

  - `rf-explorer --help`
  - `rf-explorer python <module>`
  - `rf-explorer robot <library>`
  - `rf-explorer --search <keyword>`
  - `--all` to display all entries

### Fully modular architecture:

  - `core.py` → Interactive engine
  - `python_doc.py` → Python doc renderer
  - `robot_doc.py` → Robot doc renderer
  - `rf_doc_show.py` → Robot doc display
  - `scanner.py` → Module scanning
  - `utils.py` → Shared utilities
  - `cli.py` → Command‑line interface

---

##  Installation

```bash
pip install lib-explorer