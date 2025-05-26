import re
import time
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver import Chrome, ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

API_URL: str = "https://app.powerbi.com/view?r=eyJrIjoiMGIzOGJmMjQtNWMyYS00YWRmLWFkZWYtMGQwNTc4NjNjYzViIiwidCI6IjcyNzEwODAyLTlhMzMtNGQyZC1hMDU1LTMzZDMxY2I0N2Q2MSJ9"
COLUMNS: list = ['ORDEM', 'ENTE DEVEDOR', 'EXERCICIO', 'DATA DA APRESENTAÇÃO', 'HORA DA APRESENTAÇÃO', 'NATUREZA', 'VALOR REQUISITÓRIO', 'SITUAÇÃO', 'SUPERPREFERÊNCIA']
DATA: list = []
NUM_PREC_REGEX = re.compile(r"(\d{7})[-–](\d{2})\.(\d{4})\.(\d{1})\.(\d{2})\.(\d{4})")

OPTIONS = {
    1: "EXTRAÇÃO GERAL",
}

def parse_valor_requisitorio(valor):
    try:
        valor = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
        return float(valor)
    except:
        return None

def load_chrome_options() -> Options:
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-features=NetworkService")
    
    return options

def get_precatory_data() -> None:
    driver = Chrome(options=load_chrome_options())
    driver.get(API_URL)
    
    time.sleep(3)
    elements = WebDriverWait(driver, 20).until(
        lambda d: d.find_elements(By.CSS_SELECTOR, ".small-multiples-grid-cell-content.pageNavigator")
    )
    target = elements[1]
    actions = ActionChains(driver)
    actions.move_to_element(target).click().perform()
    time.sleep(2)
    
    idx:int = 1
    last = None
    
    try:
        while True:
            print("Extraindo dados...")
            print(f"{len(DATA)} dados extraidos até o momento")
            mid_viewport = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".mid-viewport"))
            )
            rows = mid_viewport.find_elements(By.CSS_SELECTOR, 'div[aria-rowindex]')
            if not rows:
                break

            last_rowindex = int(rows[-1].get_attribute("aria-rowindex"))

            if last_rowindex == last:
                raise Exception("End of page")

            while idx <= last_rowindex:
                try:
                    row = mid_viewport.find_element(By.CSS_SELECTOR, f'div[aria-rowindex="{idx}"]')

                    def get_col(col_index):
                        return row.find_element(By.CSS_SELECTOR, f'div[aria-colindex="{col_index}"]').text.strip()

                    ordem = get_col("2")
                    ente = get_col("3").upper()
                    exercicio = get_col("4")
                    num_precatorio = re.sub(NUM_PREC_REGEX, r'\1-\2.\3.\4.\5.\6', get_col("5").strip())
                    data_apresentacao_raw = get_col("6")
                    hora_apresentacao = get_col("7")
                    natureza = get_col("8").upper()
                    valor_requisitorio = parse_valor_requisitorio(get_col("9"))
                    situacao = get_col("10").upper()
                    superpreferencia_raw = get_col("11")
                    superpreferencia = superpreferencia_raw.upper() if superpreferencia_raw else None

                    if valor_requisitorio is None:
                        idx += 1
                        continue

                    if data_apresentacao_raw.strip() == "":
                        data_apresentacao = None
                    else:
                        data_apresentacao = datetime.strptime(
                            data_apresentacao_raw.strip(), "%m/%d/%Y"
                        ).strftime("%Y-%m-%d")

                    DATA.append([
                        ordem, ente, exercicio, data_apresentacao,
                        hora_apresentacao, natureza, valor_requisitorio,
                        situacao, superpreferencia
                    ])

                except Exception:
                    pass

                idx += 1

            scroll_btn = driver.find_element(By.CSS_SELECTOR, ".scrollDown")
            driver.execute_script("arguments[0].click();", scroll_btn)
            time.sleep(1)
            last = last_rowindex

    except Exception as e:
        print("Fim da extração:", str(e))

    finally:
        driver.quit()

def generate_csv(option: int) -> None:
    get_precatory_data()
    
    df: DataFrame = pd.DataFrame(DATA, columns=COLUMNS)
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    df.to_csv(f"{OPTIONS[option]}_{today}.csv", encoding='ISO-8859-1', index=False)