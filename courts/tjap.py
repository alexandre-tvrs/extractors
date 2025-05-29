from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

API_URL: str = "https://sig.tjap.jus.br/sgpe_control_lista_precatorios/"
COLUMNS: list = ["ORDEM", "DF REF ORDEM", "PROCESSO PRECATÓRIO", "NATUREZA", "PRIORIDADE", "VALOR REQUISITADO", "ANO VENCIMENTO", "DT ÚLTIMO PAGAMENTO", "SITUAÇÃO PAGAMENTO"]
DATA: list = []

OPTIONS = {
    1: "ESTADO DO AMAPÁ",
}

def set_chrome_options(save_path: str) -> Options:
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")

    prefs = {
        "download.default_directory": save_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
        }
    chrome_options.add_experimental_option("prefs", prefs)
    
    return chrome_options

def generate_csv(option: int, save_path: str) -> None:
    driver = webdriver.Chrome(options=set_chrome_options(save_path))

    driver.get(API_URL)
    wait = WebDriverWait(driver, 60)

    select_element = wait.until(EC.presence_of_element_located((By.ID, "id_sc_field_entidade")))
    select = Select(select_element)
    select.select_by_value(str(option))
    botao_pesquisar = wait.until(EC.element_to_be_clickable((By.ID, "sub_form_b")))
    botao_pesquisar.click()
    botao_exportar = wait.until(EC.element_to_be_clickable((By.ID, "csv_top")))
    botao_exportar.click()
    botao_baixar = wait.until(EC.element_to_be_clickable((By.ID, "idBtnDown")))
    botao_baixar.click()
    driver.quit()