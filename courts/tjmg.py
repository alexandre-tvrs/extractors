import json
import requests
import pandas as pd
from pandas import DataFrame
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from requests import Response, Session
from bs4.element import NavigableString
from utils import get_first_view_state, get_precatory_data

API_URL: str = "https://www8.tjmg.jus.br/juridico/pe/listaCronologia.jsf"
COLUMNS = ["ORDEM ABERTO", "ORDEM CRONOLÓGICA", "ENTE", "NÚMERO PRECATÓRIO", "VENCIMENTO", "NATUREZA", "NÚMERO SEI", "CREDOR", "PROTOCOLO", "SITUAÇÃO", "NÚMERO PROCESSO EXECUÇÃO", "VALOR FACE"]
ROWS_PER_PAGE: int = 300
DATA: list = []
HEADER: dict = {
    "Faces-Request": "partial/ajax",
    "X-Requested-With": "XMLHttpRequest",
}

OPTIONS = {
    1: "ESTADO DE MINAS GERAIS",
}

def get_first_response(session: Session, view_state: str, option: int) -> str:
    payload: dict = {
        "javax.faces.partial.ajax": "true",
        "javax.faces.source": "consulta2",
        "javax.faces.partial.execute": "@all",
        "javax.faces.partial.render": "frm_pesquisa",
        "consulta2": "consulta2",
        "frm_pesquisa": "frm_pesquisa",
        "entidade_devedora_input": OPTIONS[option],
        "entidade_devedora_hinput": "MG;24;2",
        "ocultaFechados_input": "1",
        "ocultaFechados_focus": "",
        "javax.faces.ViewState": view_state
    }
    
    response: Response = session.post(API_URL, data=payload, headers=HEADER)
    return response.text

def get_view_state(response: str) -> str:
    view_state: str = response.split('javax.faces.ViewState"><![CDATA[')[1]
    view_state: str = view_state.split("]]")
    return view_state[0]

def get_total_records(response: str) -> int:
    root = ET.fromstring(response)
    for ext in root.iter("extension"):
        if ext.attrib.get("ln") == "primefaces" and ext.attrib.get("type") == "args":
            data = json.loads(ext.text)
            return int(data.get("totalRecords", 0))
        
def transform_xml_to_list(response: str, start: int) -> None:
    root = ET.fromstring(response)
    html_fragment = None
    for update in root.findall(".//update"):
        if update.attrib.get('id') == 'resultado':
            html_fragment = update.text
            break

    if html_fragment is None:
        return 1
    
    soup_table = BeautifulSoup(f'<table>{html_fragment}</table>', 'html.parser')
    
    table = soup_table.find('table')
    
    for index, tr in enumerate(table.find_all("tr", attrs={'data-ri': True})):
        ente = tr.find(id=f"resultado:{index + start}:j_idt52").get_text(strip=True)
        numero_precatorio = tr.find(id=f"resultado:{index + start}:nprecatorio").get_text(strip=True)
        ordem_cronologica = tr.find(id=f"resultado:{index + start}:j_idt54:ordemGeral2").get_text(strip=True)
        ordem_aberto = tr.find(id=f"resultado:{index + start}:j_idt54:ordemAtual2").get_text(strip=True)
        vencimento = None
        natureza = None
        numero_sei = None
        credor = None
        valor_face = None
        protocolo = None
        numero_processo_execucao = None
        situacao = None
            
        for idx, value in enumerate(tr.find_all(role="gridcell")):
            if idx == 7:
                vencimento = value.get_text(strip=True)
            elif idx == 8:
                natureza = value.get_text(strip=True)
            elif idx == 9:
                numero_sei = value.get_text(strip=True)
            elif idx == 10:
                credor = value.get_text(strip=True)
            elif idx == 11:
                valor_face = float(value.get_text(strip=True).split("R$ ")[1].replace(".", "").replace(",", "."))
            elif idx == 14:
                protocolo = value.get_text(strip=True)
            elif idx == 15:
                numero_processo_execucao = value.get_text(strip=True)
            elif idx == 17:
                situacao = value.get_text(strip=True)
                
        DATA.append([ordem_aberto, ordem_cronologica, ente, numero_precatorio, vencimento, natureza, numero_sei, credor, protocolo, situacao, numero_processo_execucao, valor_face])

def generate_csv(option: int, save_path: str) -> None:
    page: int = 1
    start: int = 0
    session: Session = requests.session()
    view_state: str = get_first_view_state(API_URL, session)
    response: str = get_first_response(session, view_state, option)
    total_records: int = get_total_records(response)
    total_pages = (total_records // 50) + 1 if total_records % 50 != 0 else total_records // 50

    view_state = get_view_state(response)
    
    while start <= total_records:
        print(f"Coletando página {page} de {total_pages}")
        payload: dict = {
            "javax.faces.partial.ajax": "true",
            "javax.faces.source": "resultado",
            "javax.faces.partial.execute": "resultado",
            "javax.faces.partial.render": "resultado",
            "resultado": "resultado",
            "resultado_pagination": "true",
            "resultado_first": str(start),
            "resultado_rows": "50",
            "resultado_encodeFeature": "true",
            "frm_pesquisa": "frm_pesquisa",
            "entidade_devedora_input": OPTIONS[option],
            "entidade_devedora_hinput": "MG;24;2",
            "ocultaFechados_input": "1",
            "ocultaFechados_focus": "",
            "javax.faces.ViewState": view_state
        }
        
        response: str = get_precatory_data(API_URL, session, payload, HEADER)
        
        transform_xml_to_list(response, start)
        
        view_state = get_view_state(response)
        start += 50
        page += 1
        
    df: DataFrame = pd.DataFrame(DATA, columns=COLUMNS)
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    df.to_csv(f"{save_path}/{OPTIONS[option]}_{today}.csv", encoding='ISO-8859-1', index=False)