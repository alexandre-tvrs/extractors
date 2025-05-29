import requests
import pdfplumber
import pandas as pd
from io import BytesIO
from pandas import DataFrame
from bs4 import BeautifulSoup
from selenium import webdriver
from utils import get_headless_selenium_options


API_URL: str = "https://www.tjac.jus.br/adm/sepre/"
COLUMNS = ['ORDEM', 'TIPO', 'TRIBUNAL', 'ANO', 'APRESENTAÇÃO', 'NATUREZA', 'PRECATÓRIO', 'VALOR', 'DATA ATUALIZAÇÃO']
DATA: list = []

OPTIONS = {
    "Estado do Acre (Ad. Direta)": "ESTADO DO ACRE",
    "Município de Feijó": "MUNICÍPIO DE FEIJÓ",
    "Município de Jordão": "MUNICÍPIO DE JORDÃO"
}

def get_html_source() -> str:
    chrome_options = get_headless_selenium_options()
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(API_URL)
    html_source = driver.page_source
    driver.quit()
    return html_source

def get_pdf_link(option: str) -> str:
    html_source = get_html_source()
    soup = BeautifulSoup(html_source, "html.parser")
    linhas = soup.find_all("tr")

    for linha in linhas:
        strong_tag = linha.find("strong")
        if strong_tag and option in strong_tag.text:
            a_tag = linha.find("a")
            if a_tag and a_tag.has_attr("href"):
                pdf_link = a_tag["href"]
                
                return pdf_link

def generate_csv(option: str, save_path: str) -> None:
    pdf_link = get_pdf_link(option)
    response = requests.get(pdf_link, stream=True)
    pdf_bytes = BytesIO(response.content)
    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if len(DATA) == 0:
                    df: DataFrame = pd.DataFrame(table[2:], columns=COLUMNS)
                else:
                    df: DataFrame = pd.DataFrame(table, columns=COLUMNS)
                DATA.append(df)
                
    df: DataFrame = pd.concat(DATA, ignore_index=True, axis=0)
    df = df.replace(r'\n', ' ', regex=True)
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    df.to_csv(f"{save_path}/{OPTIONS[option]}_{today}.csv", encoding='ISO-8859-1', index=False)