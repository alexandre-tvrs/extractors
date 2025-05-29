import re
from asyncio import run
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from playwright.async_api import async_playwright

API_URL: str = "https://app.powerbi.com/view?r=eyJrIjoiMGIzOGJmMjQtNWMyYS00YWRmLWFkZWYtMGQwNTc4NjNjYzViIiwidCI6IjcyNzEwODAyLTlhMzMtNGQyZC1hMDU1LTMzZDMxY2I0N2Q2MSJ9"
COLUMNS: list = ["ORDEM", "ENTE", "EXERCÍCIO", "Nº DO PRECATÓRIO", "DATA DE APRESENTAÇÃO DO OFÍCIO",  \
    "HORA DE APRESENTAÇÃO DO OFÍCIO", "NATUREZA", "VALOR REQUISITÓRIO", "SITUAÇÃO", "SUPERFREFERÊNCIA"]
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

async def get_precatory_data():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        await page.goto(API_URL)

        await page.wait_for_selector(".small-multiples-grid-cell-content.pageNavigator")
        await page.locator(".small-multiples-grid-cell-content.pageNavigator").nth(1).click()
        await page.wait_for_timeout(2000)

        await page.locator(".tableExContainer").hover()
        await page.locator('[data-testid="focus-mode-btn"]').click()

        idx = 1
        last = 0
        
        try:
            while True:
                print(f"Extraidos até o momento: {len(DATA)}")
                last_rowindex = await page.evaluate('''
                    () => {
                        let el = document.querySelector(".mid-viewport");
                        let divs = el.querySelectorAll("div[aria-rowindex]");
                        let last = divs[divs.length - 1];
                        return last ? last.getAttribute("aria-rowindex") : null;
                    }
                ''')

                if last_rowindex == last:
                    print("Fim da página.")
                    break

                for i in range(idx, int(last_rowindex) + 1):
                    try:
                        row = await page.query_selector(f'[aria-rowindex="{i}"]')

                        async def get_col(col_index):
                            cell = await row.query_selector(f'[aria-colindex="{col_index}"]')
                            return await cell.text_content() if cell else ""

                        ordem = await get_col("2")
                        ente = await get_col("3")
                        exercicio = await get_col("4")
                        num_precatorio = await get_col("5")
                        data_apresentacao = await get_col("6")
                        hora_apresentacao = await get_col("7")
                        natureza = await get_col("8")
                        valor_requisitorio = await get_col("9")
                        situacao = await get_col("10")
                        superpreferencia = await get_col("11")

                        ordem = ordem.strip()
                        ente = ente.upper().strip()
                        exercicio = exercicio.strip()
                        natureza = natureza.upper().strip()
                        situacao = situacao.upper().strip()
                        superpreferencia = superpreferencia.upper().strip() if superpreferencia else None
                        num_precatorio = re.sub(NUM_PREC_REGEX, r'\1-\2.\3.\4.\5.\6', num_precatorio.strip())
                        valor_requisitorio = parse_valor_requisitorio(valor_requisitorio)

                        if valor_requisitorio is None:
                            idx += 1
                            continue

                        if data_apresentacao.strip() == '':
                            data_apresentacao = None
                        else:
                            data_apresentacao = datetime.strptime(data_apresentacao.strip(), '%m/%d/%Y').strftime('%Y-%m-%d')

                        DATA.append([
                            ordem, ente, exercicio, num_precatorio, data_apresentacao,
                            hora_apresentacao, natureza, valor_requisitorio, situacao, superpreferencia
                        ])

                        idx += 1

                    except Exception as e:
                        print(f"Erro na linha {i}: {e}")
                        idx += 1
                        continue

                await page.wait_for_selector(".scrollDown")
                await page.evaluate('''document.querySelector(".scrollDown").click()''')

                last = last_rowindex

        except Exception as e:
            print("Erro ou fim:", e)

        await browser.close()

def generate_csv(option: int, save_path: str) -> None:
    run(get_precatory_data())
    
    df: DataFrame = pd.DataFrame(DATA, columns=COLUMNS)
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    df.to_csv(f"{save_path}/{OPTIONS[option]}_{today}.csv", encoding='ISO-8859-1', index=False)