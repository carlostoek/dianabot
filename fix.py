import os
from pathlib import Path

def fix_python_file(filepath):
    """
    Corrige un archivo Python con:
    - Elimina retorno de carro inicial si existe
    - Elimina exactamente 4 espacios al inicio de la primera línea
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Eliminar retorno de carro inicial si existe
        if content.startswith('\n'):
            content = content[1:]
        
        lines = content.splitlines(keepends=True)
        
        if not lines:
            return False  # Archivo vacío
        
        # Procesar primera línea (eliminar exactamente 4 espacios)
        if lines[0].startswith('    '):
            lines[0] = lines[0][4:]
            modified = True
        else:
            modified = False
        
        # Reconstruir contenido
        fixed_content = ''.join(lines)
        
        # Guardar solo si hubo cambios
        if modified or original_content.startswith('\n'):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error procesando {filepath}: {str(e)}")
        return False

def process_directory(root_dir):
    """
    Recorre recursivamente un directorio y procesa todos los archivos .py
    """
    root_path = Path(root_dir).expanduser()
    
    if not root_path.exists():
        print(f"Error: El directorio no existe: {root_path}")
        return
    
    print(f"\nBuscando archivos Python en: {root_path}\n")
    
    modified_files = 0
    total_files = 0
    
    for py_file in root_path.rglob('*.py'):
        total_files += 1
        relative_path = py_file.relative_to(root_path)
        
        if fix_python_file(py_file):
            print(f"Corregido: {relative_path}")
            modified_files += 1
    
    print(f"\nResumen:")
    print(f"- Directorio analizado: {root_path}")
    print(f"- Archivos Python encontrados: {total_files}")
    print(f"- Archivos modificados: {modified_files}")

if __name__ == "__main__":
    import sys
    
    # Configuración de rutas
    DEFAULT_PATH = "~/storage/downloads/proyecto_extraido_v2"
    
    target_dir = sys.argv[1] if len(sys.argv) > 1 else input(
        f"Ingrese la ruta del directorio [Enter para {DEFAULT_PATH}]: "
    ) or DEFAULT_PATH
    
    process_directory(target_dir)