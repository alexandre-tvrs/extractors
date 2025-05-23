import importlib
from prompt_toolkit.shortcuts import radiolist_dialog

ESTATES_OPTIONS: list = [
    {"name": "TRIBUNAL DE JUSTIÇA DE MATO GROSSO DO SUL", "court": "tjms"},
    {"name": "TRIBUNAL DE JUSTIÇA DE MINAS GERAIS", "court": "tjmg"},
]
    
def main() -> None:
    result = radiolist_dialog(
        title="Extrator Precatórios",
        text="Escolha o estado",
        values=[(option["court"], option["name"]) for option in ESTATES_OPTIONS],
    ).run()
    
    if not result:
        exit()
    
    module = importlib.import_module(f"courts.{result}")
    
    options = module.OPTIONS
    
    federative_entity = radiolist_dialog(
        title="Selecionar Ente",
        text="Selecione o Ente Federativo desejado",
        values=[(k, v) for k, v in options.items()],
    ).run()
    
    if not federative_entity:
        exit()
    
    module.generate_csv(federative_entity)
    
if __name__ == '__main__':
    main()