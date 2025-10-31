# main_launcher.py
import sys
import os

def main():
    """Main application launcher"""
    # Add core directory to path
    sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
    sys.path.append(os.path.join(os.path.dirname(__file__), 'gui'))
    
    from gui.engine_selector import EngineSelector
    
    # Launch engine selector
    import tkinter as tk
    root = tk.Tk()
    app = EngineSelector(root)
    root.mainloop()

if __name__ == "__main__":
    main()
    