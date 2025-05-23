import requests
import pandas as pd
from pandas import DataFrame
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from requests import Response, Session


API_URL: str = "https://sistemas.tjms.jus.br/sapre/publico/classificacao.xhtml"
COLUMNS = ["ORDEM", "EXECUÇÃO", "NÚMERO DO PROCESSO", "COMARCA", "ANO LANÇAMENTO", "NATUREZA", "DATA CADASTRO", "TIPO DE CLASSIFICAÇÃO", "VALOR ORIGINAL", "VALOR ATUAL", "SITUAÇÃO"]
ROWS_PER_PAGE: int = 300
ROOF: int = 10000
DATA: list = []
HEADER: dict = {
    "Faces-Request": "partial/ajax",
    "X-Requested-With": "XMLHttpRequest",
}

OPTIONS = {
    1: "ESTADO DO MATO GROSSO DO SUL - REGIME ESPECIAL",
    113: "ESTADO DO MATO GROSSO DO SUL",
}

def get_first_response(session: Session, view_state: str, option: int) -> str:
    payload: dict = {
        "javax.faces.partial.ajax": "true",
        "javax.faces.source": "formPesquisa:j_idt21",
        "javax.faces.partial.execute": "@all",
        "javax.faces.partial.render": "formPesquisa:itens messages",
        "formPesquisa:j_idt21": "formPesquisa:j_idt21",
        "formPesquisa": "formPesquisa",
        "formPesquisa:j_idt17_focus": "formPesquisa:j_idt17",
        "formPesquisa:j_idt17_input": f"{str(option)}",
        "formPesquisa:j_idt23_input": "on",
        "javax.faces.ViewState": view_state
    }
    
    response: Response = session.post(API_URL, data=payload, headers=HEADER)
    return response.text

def get_precatory_data(session: Session, payload: dict) -> str:
    response = session.post(API_URL, data=payload, headers=HEADER)
    return response.text

def get_view_state(response: str) -> str:
    view_state: str = response.split('javax.faces.ViewState:0"><![CDATA[')[1]
    view_state: str = view_state.split("]]")
    return view_state

def get_first_view_state(session: Session) -> str:
    response: Response = session.get(API_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.find("input", {"name": "javax.faces.ViewState"})["value"]

def transform_xml_to_list(response: str) -> None:
    root = ET.fromstring(response)
    html_fragment = None
    for update in root.findall('.//update'):
        if update.attrib.get('id') == 'formPesquisa:listaResultadoPesquisa':
            html_fragment = update.text
            break

    if html_fragment is None:
        return 1

    soup_table = BeautifulSoup(f'<table>{html_fragment}</table>', 'html.parser')
    table = soup_table.find('table')
    for tr in table.find_all('tr'):
        cells = [td.get_text(strip=True) for td in tr.find_all('td')]
        if cells:
            cells.pop()
            cells[-3] = float(cells[-3].replace(".", "").replace(",", ".") if cells[-3] else 0)
            cells[-2] = float(cells[-2].replace(".", "").replace(",", ".") if cells[-2] else 0)
            DATA.append(cells)
                
def generate_csv(option: int) -> None:
    page: int = 1
    start: int = 0
    session: Session = requests.session()
    view_state: str = get_first_view_state(session)
    response: str = get_first_response(session, view_state, option)
    
    while True:
        print(f"Coletando página {page}")
        
        payload: dict = {
            "javax.faces.partial.ajax": "true",
            "javax.faces.source": "formPesquisa:listaResultadoPesquisa",
            "javax.faces.partial.execute": "formPesquisa:listaResultadoPesquisa",
            "javax.faces.partial.render": "formPesquisa:listaResultadoPesquisa",
            "formPesquisa:listaResultadoPesquisa": "formPesquisa:listaResultadoPesquisa",
            "formPesquisa:listaResultadoPesquisa_pagination": "true",
            "formPesquisa:listaResultadoPesquisa_first": str(start),
            "formPesquisa:listaResultadoPesquisa_rows": str(ROWS_PER_PAGE),
            "formPesquisa:listaResultadoPesquisa_skipChildren": "true",
            "formPesquisa:listaResultadoPesquisa_encodeFeature": "true",
            "formPesquisa": "formPesquisa",
            "formPesquisa:j_idt17_focus": "",  # exatamente como veio
            "formPesquisa:j_idt17_input": f"{str(option)}",
            "formPesquisa:j_idt23_input": "on",
            "formPesquisa:listaResultadoPesquisa:j_idt40:filter": "",
            "formPesquisa:listaResultadoPesquisa:j_idt44:filter": "",
            "formPesquisa:listaResultadoPesquisa:j_idt46:filter": "",
            "formPesquisa:listaResultadoPesquisa:j_idt48:filter": "",
            "formPesquisa:listaResultadoPesquisa:j_idt50:filter": "",
            "formPesquisa:listaResultadoPesquisa:j_idt54:filter": "",
            "formPesquisa:listaResultadoPesquisa:j_idt62:filter": "",
            "javax.faces.ViewState": view_state,
        }
        
        response: str = get_precatory_data(session, payload)
        view_state = get_view_state(response)
        response = transform_xml_to_list(response)
        if response:
            break
        page += 1
        start += ROWS_PER_PAGE
        
    df: DataFrame = pd.DataFrame(DATA, columns=COLUMNS)
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    df.to_csv(f"{OPTIONS[option]}{today}.csv", encoding='ISO-8859-1', index=False)