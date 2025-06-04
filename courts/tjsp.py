import requests
from requests import Session
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Browser, Page


API_URL: str = "https://www.tjsp.jus.br/cac/scp/webRelPublicLstPagPrecatPendentes.aspx"
COLUMNS: list = []
DATA: list = []

OPTIONS = {
    56: "ESTADO DE SÃO PAULO",
    621: "MUNICÍPIO DE SÃO PAULO",
}

payload = {
    "vENT_ID": "621",
    "vENT_NOME": "smile",
    "IMGPALICARFILTRO": "https://www.tjsp.jus.br/cac/scp/Resources/Portuguese/PortaisTJAzul/Select.png",
    "vENT_TIPO": "smile",
    "cfield": "CAPTCHA_AQUI",
    "BUTTON3": "Abrir Relatório",
    "viSPECOAVANCADA": "",
    "GXState": "VALOR_AQUI"
}

def solve_captcha(img_path: str) -> str:
    return

def download_captcha(page: Page):
    page.wait_for_selector("#CAPTCHA1Container img", timeout=10000)
    captcha_element = page.query_selector("#CAPTCHA1Container img")
    captcha_url = captcha_element.get_attribute("src")
    
    captcha_img = requests.get(captcha_url)
    with open("captcha.jpg", "wb") as f:
        f.write(captcha_img.content)
        


def get_pdf(option: int) -> None:
    with sync_playwright() as p:
        browser: Browser = p.chromium.launch(headless=False)
        page: Page = browser.new_page()
        page.goto(API_URL)
        download_captcha(page)
        

def generate_csv(option: int, save_path: str) -> None:
    get_pdf(option)