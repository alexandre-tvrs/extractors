import os
import re
import zipfile
import fitz
import pandas as pd
from io import BytesIO
from pandas import DataFrame
from utils import solve_captcha
from playwright.sync_api import sync_playwright, Browser, Page


API_URL: str = "https://www.tjsp.jus.br/cac/scp/webRelPublicLstPagPrecatPendentes.aspx"
COLUMNS: list = ["ORDEM DE PAGAMENTO", "ORDEM ORÇAMENTÁRIA", "NATUREZA", "NÚMERO DO PROCESSO", "SUSPENÇÃO", "DATA DO PROTOCOLO", "ENTE DEVEDOR", "NUMERO DE AUTOS ANTIGOS", "ES/EP", "NÚMERO DO PROTOCOLO GERAL"]
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

def extract_blocks(raw_text: str) -> None:
    flat_text = raw_text.replace("\n", " ")
    
    if "pelos respectivos Tribunais." in flat_text:
        flat_text = flat_text.split("pelos respectivos Tribunais.")[1]
    
    flat_text = flat_text.strip()
    pattern = re.compile(r'(?=\d{7}-\d{2}\.\d{4}\.8\.26\.\d{4} (?:OUTRAS ESPÉCIES|ALIMENTARES) Ordem de Pagamento:)')
    matches = list(pattern.finditer(flat_text))
    blocks = []
    
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(flat_text)
        blocks.append(flat_text[start:end].strip())
    
    for block in blocks:
        aux = block.split("Ordem de Pagamento:")[0].split(" ")
        auto_number = aux[0]
        nature = aux[1] if len(aux) == 2 else " ".join(aux[1:])
        aux = block.split("Ordem Orçamentária: ")[1].split(" ")
        payment_order = aux[0]
        budgeting_order = aux[1]
        process_number = aux[2]
        es_ep = aux[4]
        suspended = aux[5]
        protocol_date = aux[11]
        general_protocol_number = aux[10]
        debtor = block.split("Devedora: ")[1]
    
        DATA.append([payment_order, budgeting_order, nature, process_number, suspended, protocol_date, debtor, auto_number, es_ep, general_protocol_number])

def get_data_from_pdf(pdf_bytes: bytes) -> None:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_text = ""
    for page in doc:
        all_text += page.get_text() + "\n"
    doc.close()
    
    extract_blocks(all_text)

def get_zip(option: int) -> None:
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
        download.save_as("temp.zip")
        
def read_pdf(zip_path: str = "temp.zip") -> None:
    with zipfile.ZipFile(zip_path, 'r') as z:
        for filename in z.namelist():
            if filename.lower().endswith(".pdf"):
                with z.open(filename) as pdf_file:
                    pdf_bytes = BytesIO(pdf_file.read())
                    get_data_from_pdf(pdf_bytes)
                            
    os.remove(zip_path)

def generate_csv(option: int, save_path: str) -> None:
    get_zip(option)
    read_pdf()
    
    df: DataFrame = DataFrame(DATA, columns=COLUMNS)
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    df.to_csv(f"{save_path}/{OPTIONS[option]}_{today}.csv", encoding='ISO-8859-1', index=False)