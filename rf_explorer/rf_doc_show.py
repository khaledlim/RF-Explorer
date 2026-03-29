"""
rf_doc_show.py
Handles the documentation rendering for Robot Framwork Keywpords inside RF Explorer.
"""

from robot.libdocpkg import LibraryDocumentation

def main():
    lib_name = input("Enter the Robot Framework library name or path : ").strip()
    
    try:
        lib = LibraryDocumentation(lib_name)
        
        print(f"\nLibrary: {lib.name}  Version: {lib.version}\n")
        print(f"Library Documentation : {lib.doc}\n")
        
        keywords = lib.keywords
        
        if not keywords:
            print("No Keywords found in this library.")
            return
        
        keywords_sorted = sorted(keywords, key=lambda k: k.name.lower())
        
        print(f"Total Keywords: {len(keywords_sorted)}\n")
        print("Available Keywords (sorted alphabetically):\n")
        
        for kw in keywords_sorted:
            print(f"Keyword : {kw.name}")
            print(f"Arguments : {kw.args}")
            print(f"Documentation : {kw.doc}\n")
            
    except Exception as e:
        print(f"Error : failed to load the library '{lib_name}'.")
        print(e)

if __name__ == "__main__":
    main()