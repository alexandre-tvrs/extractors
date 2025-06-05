import os
import fitz
import camelot
import pandas as pd
from pandas import DataFrame
from utils import solve_captcha
from concurrent.futures import ProcessPoolExecutor
from playwright.sync_api import sync_playwright, Browser, Page


API_URL: str = "https://www.tjsp.jus.br/cac/scp/aPublicacao_ConsultaDividaAnual.aspx"
COLUMNS: list = ["PROCESSO DEPRE", "NATUREZA", "PROTOCOLO", "NÚMERO ORDEM", "DATA DE ENSEJO DA ORDEM", "CONDIÇÃO DE SUPERPREFERÊNCIA", "VALOR PAGO", "SALDO"]
DATA: list = []

OPTIONS = {
    56: "ESTADO DE SÃO PAULO",
    621: "MUNICÍPIO DE SÃO PAULO",
}

def captcha(page: Page):
    page.wait_for_selector("#CAPTCHA1Container img", timeout=10000)
    captcha_element = page.query_selector("#CAPTCHA1Container img")
    captcha_url = captcha_element.get_attribute("src")
    img_bytes = page.request.get(captcha_url).body()

    return solve_captcha(img_bytes)

def clean_value(value: str) -> float:
    if pd.isna(value):
        return 0.0
    value = value.replace(".", "").replace(",", ".")
    return float(value)

def remove_empty_columns(df: DataFrame, limit: float = 0.5) -> DataFrame:
    df = df.replace('', pd.NA)
    prop_nulls = df.isna().mean()
    valid_columns = prop_nulls[prop_nulls <= limit].index
    return df[valid_columns]
    

def process_pdf_pages(args) -> None:
    pdf_path, page_range = args
    dfs: list[DataFrame] = []
    tables = camelot.read_pdf(pdf_path, pages=page_range, flavor='stream')
    float_columns = ['VALOR PAGO', 'SALDO']
    for table in tables:
        try:
            processo_row = table.df[table.df[0] == 'Processo DEPRE'].index[0]
        except:
            continue
        table_df: DataFrame = table.df.iloc[processo_row+1:].copy()
        table_df = table_df.replace({r'\*|\n': '', r'\s+': ' '}, regex=True)
        table_df = table_df[table_df.isnull().sum(axis=1) <= 2]
        table_df = table_df[~table_df[0].astype(str).str.startswith("Total do Ano")]
        table_df = table_df[~table_df[0].astype(str).str.startswith("TOTAL GERAL")]
        table_df = remove_empty_columns(table_df)
        table_df = table_df.loc[:, ~(table_df.isna().all() | (table_df == '').all())]
        table_df.reset_index(drop=True, inplace=True)
        
        if len(table_df.columns) != 8:
            print(table_df.head())
            continue
        
        table_df.columns = COLUMNS
        
        for col in float_columns:
            table_df[col] = table_df[col].apply(clean_value)
            
        dfs.append(table_df)
        
    return dfs

def get_data_from_pdf(pdf_path: str) -> None:
    with fitz.open(pdf_path) as doc:
        qt_pages = len(doc)
    
    pages = [f"{start}-{min(start+49, qt_pages)}" for start in range(1, qt_pages+1, 50)]
    with ProcessPoolExecutor() as executor:
        args = [(pdf_path, page_range) for page_range in pages]
        results = executor.map(process_pdf_pages, args)
        for df in results:
            DATA.extend(df)
        
def get_pdf(option: int) -> None:
    with sync_playwright() as p:
        browser: Browser = p.chromium.launch(headless=False)
        page: Page = browser.new_page()
        page.goto(API_URL)
        captcha_response = captcha(page).replace("1", "l")
        page.select_option("#vENT_ID", str(option))
        page.fill("#_cfield", captcha_response)
        with page.expect_download() as download_info:
            page.click("text=Abrir Relatório")
            
        download = download_info.value
        download.save_as("temp.pdf")
        
def read_pdf(pdf_path: str = "temp.pdf") -> None:
    get_data_from_pdf(pdf_path)
                            
    os.remove(pdf_path)

def generate_csv(option: int, save_path: str) -> None:
    get_pdf(option)
    read_pdf()
    df: DataFrame = pd.concat(DATA, ignore_index=True)
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    df.to_csv(f"{save_path}/{OPTIONS[option]}_{today}.csv", encoding='ISO-8859-1', index=False)