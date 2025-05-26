import importlib
from prompt_toolkit.shortcuts import radiolist_dialog

ESTATES_OPTIONS: list = [
    {"name": "TRIBUNAL DE JUSTIÇA DE ACRE", "court": "tjac"},
    {"name": "TRIBUNAL DE JUSTIÇA DE ALAGOAS", "court": "tjal"},
    {"name": "TRIBUNAL DE JUSTIÇA DO AMAPÁ", "court": "tjap"},
    {"name": "TRIBUNAL DE JUSTIÇA DO AMAZONAS", "court": "tjam"},
    {"name": "TRIBUNAL DE JUSTIÇA DA BAHIA", "court": "tjba"},
    {"name": "TRIBUNAL DE JUSTIÇA DO CEARÁ", "court": "tjce"},
    {"name": "TRIBUNAL DE JUSTIÇA DO DISTRITO FEDERAL E DOS TERRITÓRIOS", "court": "tjdf"},
    {"name": "TRIBUNAL DE JUSTIÇA DO ESPÍRITO SANTO", "court": "tjes"},
    {"name": "TRIBUNAL DE JUSTIÇA DE GOIÁS", "court": "tjgo"},
    {"name": "TRIBUNAL DE JUSTIÇA DO MARANHÃO", "court": "tjma"},
    {"name": "TRIBUNAL DE JUSTIÇA DO MATO GROSSO", "court": "tjmt"},
    {"name": "TRIBUNAL DE JUSTIÇA DE MATO GROSSO DO SUL", "court": "tjms"},
    {"name": "TRIBUNAL DE JUSTIÇA DE MINAS GERAIS", "court": "tjmg"},
    {"name": "TRIBUNAL DE JUSTIÇA DO PARÁ", "court": "tjpa"},
    {"name": "TRIBUNAL DE JUSTIÇA DA PARAÍBA", "court": "tjpb"},
    {"name": "TRIBUNAL DE JUSTIÇA DO PARANÁ", "court": "tjpr"},
    {"name": "TRIBUNAL DE JUSTIÇA DE PERNAMBUCO", "court": "tjpe"},
    {"name": "TRIBUNAL DE JUSTIÇA DO PIAUÍ", "court": "tjpi"},
    {"name": "TRIBUNAL DE JUSTIÇA DO RIO DE JANEIRO", "court": "tjrj"},
    {"name": "TRIBUNAL DE JUSTIÇA DO RIO GRANDE DO NORTE", "court": "tjrn"},
    {"name": "TRIBUNAL DE JUSTIÇA DO RIO GRANDE DO SUL", "court": "tjrs"},
    {"name": "TRIBUNAL DE JUSTIÇA DE RONDÔNIA", "court": "tjro"},
    {"name": "TRIBUNAL DE JUSTIÇA DE RORAIMA", "court": "tjrr"},
    {"name": "TRIBUNAL DE JUSTIÇA DE SANTA CATARINA", "court": "tjsc"},
    {"name": "TRIBUNAL DE JUSTIÇA DE SÃO PAULO", "court": "tjsp"},
    {"name": "TRIBUNAL DE JUSTIÇA DE SERGIPE", "court": "tjse"},
    {"name": "TRIBUNAL DE JUSTIÇA DO TOCANTINS", "court": "tjto"}
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