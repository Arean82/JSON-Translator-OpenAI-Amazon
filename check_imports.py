# check_imports.py
import ast
import os

def check_file_imports(file_path):
    """Check if a Python file has proper Callable import"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        
        # Check if Callable is imported from typing
        has_callable = any('typing.Callable' in imp or 'Callable' in imp for imp in imports)
        
        # Check if file uses Callable in function signatures
        uses_callable = 'Callable' in content
        
        return has_callable, uses_callable
        
    except Exception as e:
        print(f"❌ Error parsing {file_path}: {e}")
        return False, False

def main():
    files_to_check = [
        "core/translation_base.py",
        "core/translation_engine.py", 
        "core/general_translation.py",
        "core/blog_translation.py",
        "core/deepseek_translation.py",
        "engines/deepseek_engine.py",
        "engines/openai_engine.py",
        "engines/aws_engine.py",
    ]
    
    print("🔍 Checking Callable imports...")
    print("=" * 50)
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            has_import, uses_callable = check_file_imports(file_path)
            status = "✅" if has_import or not uses_callable else "❌"
            print(f"{status} {file_path}")
            if uses_callable and not has_import:
                print(f"   ⚠️  Uses Callable but no import!")
        else:
            print(f"❌ {file_path} - FILE NOT FOUND")
    
    print("=" * 50)

if __name__ == "__main__":
    main()

