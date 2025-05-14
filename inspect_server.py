# Inspeccionar la clase Server de MCP
import inspect
import mcp.server

# Obtener detalles sobre la clase Server
server_class = mcp.server.Server
print(f"Clase Server encontrada en: {server_class.__module__}")

# Verificar si Server es un objeto FastAPI
print(f"¿Server hereda de FastAPI? {issubclass(server_class, mcp.server.FastAPI) if hasattr(mcp.server, 'FastAPI') else 'No se puede determinar'}")

# Explorar el constructor
try:
    init_signature = inspect.signature(server_class.__init__)
    print("\nConstructor de Server:")
    for param_name, param in init_signature.parameters.items():
        if param_name != 'self':
            default = f" = {param.default}" if param.default is not inspect.Parameter.empty else ""
            print(f"  - {param_name}{default}")
except Exception as e:
    print(f"Error al inspeccionar el constructor: {e}")

# Explorar los métodos y atributos
print("\nMétodos y atributos de Server:")
for name in dir(server_class):
    if not name.startswith('_'):  # Excluir métodos/atributos privados
        try:
            attr = getattr(server_class, name)
            attr_type = type(attr).__name__
            if inspect.isfunction(attr) or inspect.ismethod(attr):
                signature = inspect.signature(attr)
                params = []
                for param_name, param in signature.parameters.items():
                    if param_name != 'self':
                        default = f"={param.default}" if param.default is not inspect.Parameter.empty else ""
                        params.append(f"{param_name}{default}")
                print(f"  - Método: {name}({', '.join(params)})")
            else:
                print(f"  - Atributo: {name} ({attr_type})")
        except Exception as e:
            print(f"  - {name}: Error al inspeccionar - {e}")

# Intentar crear una instancia y examinarla
print("\nCreando una instancia de Server con herramientas vacías:")
try:
    server_instance = mcp.server.Server([], "Test Server")
    print("  Instancia creada correctamente")
    
    # Verificar si tiene un atributo app o algo similar
    print("\nAtributos de la instancia:")
    for name in dir(server_instance):
        if not name.startswith('_'):  # Excluir métodos/atributos privados
            try:
                attr = getattr(server_instance, name)
                attr_type = type(attr).__name__
                print(f"  - {name} ({attr_type})")
            except Exception as e:
                print(f"  - {name}: Error al inspeccionar - {e}")
    
    # Verificar si es una aplicación ASGI
    print("\nVerificación ASGI:")
    if hasattr(server_instance, '__call__'):
        print("  La instancia parece ser una aplicación ASGI (tiene método __call__)")
    else:
        print("  La instancia NO parece ser una aplicación ASGI (no tiene método __call__)")
except Exception as e:
    print(f"  Error al crear la instancia: {e}")
