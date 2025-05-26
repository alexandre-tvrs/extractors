import requests
import pdfplumber
import pandas as pd
from io import BytesIO
from pandas import DataFrame
from bs4 import BeautifulSoup
from selenium import webdriver
from utils import get_selenium_options


API_URL: str = "https://precatorios.tjal.jus.br/api/precatorios/baixar/"
COLUMNS = ['N°', 'Nº PRECATÓRIO', 'RECEBIMENTO', 'HORÁRIO DE RECEBIMENTO', 'NATUREZA', 'ORÇ.', 'Nº PROC. NA ORIGEM', 'VALOR ATUALIZADO', 'ATUALIZADO ATÉ', 'TIPO']
DATA: list = []

OPTIONS = {
    739: "ESTADO DE ALAGOAS",
}

def generate_csv(option: int) -> None:
    pdf_link:str = f"{API_URL}{option}"
    response = requests.get(pdf_link, stream=True)
    pdf_bytes = BytesIO(response.content)
    with pdfplumber.open(pdf_bytes) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for data in table:
                    if data[0] != "" and data[0] != "N°" and len(data) == 10 and data[1] != None:
                        for i, value in enumerate(data):
                            if isinstance(value, str):
                                data[i] = value.replace('\n', '').strip()
                                
                        DATA.append(data)
                
    df: DataFrame = pd.DataFrame(DATA, columns=COLUMNS)
    df["VALOR ATUALIZADO"] = df["VALOR ATUALIZADO"].str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip()
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    df.to_csv(f"{OPTIONS[option]}_{today}.csv", encoding='ISO-8859-1', index=False)