import importlib
from prompt_toolkit import Application
from prompt_toolkit.shortcuts import radiolist_dialog

ESTATES_OPTIONS: list = [
    {"name": "TRIBUNAL DE JUSTIÇA DE MATO GROSSO DO SUL", "court": "tjms"},
]

app = Application(full_screen=True)
    
def main() -> None:
    result = radiolist_dialog(
        title="Extrator Precatórios",
        text="Escolha o estado",
        values=[(option["court"], option["name"]) for option in ESTATES_OPTIONS],
    ).run()
    
    module = importlib.import_module(f"courts.{result}")
    
    options = module.OPTIONS
    
    federative_entity = radiolist_dialog(
        title="Selecionar Ente",
        text="Selecione o Ente Federativo desejado",
        values=[(k, v) for k, v in options.items()],
    ).run()
    
    module.generate_csv(federative_entity)
    
if __name__ == '__main__':
    main()