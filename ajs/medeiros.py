import re
import os
import shutil
import aiohttp
import asyncio
from pathlib import Path
from pandas import DataFrame
from playwright.async_api import async_playwright, Page, Browser, Locator


URL: str = "https://www.administradorjudicial.adv.br"
CREDITORS_COLUMNS: list[str] = [
    "NOME",
    "CPF/CNPJ",
    "CLASSE",
    "VALOR TOTAL",
    "FGTS CORRENTE",
    "FGTS RESCISÓRIO",
    "ILÍQUIDO",
    "LÍQUIDO",
]


def clean_string(s: str) -> str:
    return (
        re.sub(r"\s+", " ", s)
        .replace("\xa0", " ")
        .replace(".", "")
        .replace("/", "-")
        .strip()
    )


def create_dir(dir_name: str) -> None:
    os.makedirs(dir_name, exist_ok=True)


def create_temp_dir() -> None:
    create_dir("temp")


def delete_temp_dir() -> None:
    shutil.rmtree("temp")


def create_process_files_path(process_name: str) -> tuple[str, str]:
    creditors_path = f"temp/{process_name.upper()}/Credores"
    create_dir(creditors_path)

    prj_path = f"temp/{process_name.upper()}/PRJ"
    create_dir(prj_path)

    return creditors_path, prj_path


async def download_pdf(url: str, filename: str) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(filename, "wb") as f:
                    f.write(await resp.read())


async def get_creditors_files_from_process(
    page: Page, process_endpoint: str, creditors_path: str
):
    docs: list[Locator] = await page.locator("#tabs-ta1 p a").all()
    files = False

    for doc in docs:
        doc_name: str = clean_string(await doc.text_content()).upper()
        print(doc_name)

        if any(_ in doc_name for _ in [""]):
            doc_link: str = await doc.get_attribute("href")
            await download_pdf(doc_link, f"{creditors_path}/{doc_name}.pdf")
            files = True

    if not files:
        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(headless=False)
            page = await browser.new_page(base_url=URL)
            await page.goto(f"/{process_endpoint}")
            await page.locator("tbody.tabela-creadores").scroll_into_view_if_needed(
                timeout=3000
            )
            await page.wait_for_selector("tbody.tabela-creadores tr", timeout=3000)

            creditors_table_trs = await page.locator("tbody.tabela-creadores tr").all()
            creditors_data = []

            for tr in creditors_table_trs:
                cells = await tr.locator("td").all()
                cells = [
                    clean_string(await cell.text_content())
                    for cell in cells
                    if len(cells) > 3
                ]

                if cells:
                    cells.pop(4)
                    cells.pop(4)
                    cells.pop(5)
                    cells.pop(6)
                    cells.pop(7)
                    creditors_data.append(cells)

            df_creditors: DataFrame = DataFrame(
                creditors_data, columns=CREDITORS_COLUMNS
            )
            df_creditors.to_excel(
                f"{creditors_path}/Lista de credores.xlsx", index=False
            )


async def get_process_files(browser: Browser, process_endpoint: str) -> None:
    page = await browser.new_page(base_url=URL)
    await page.goto(f"/{process_endpoint}")

    process_name: str = await page.locator("h3.title-custom").all_inner_texts
    process_name = clean_string(process_name)
    print(process_name)

    creditors_path, prj_path = create_process_files_path(process_name)

    get_creditors_files_from_process(page, process_endpoint, creditors_path)


async def get_all_endpoints(page: Page, browser: Browser) -> list[str]:
    tasks: list = []
    next_li = page.locator("li.paginate_button.next").first
    next_a = next_li.locator("a")

    while True:
        page_trs = await page.locator(
            "#DataTables_Table_0 tbody tr a.text-left.btn-processo"
        ).all()

        for tr in page_trs:
            process_endpoint = await tr.get_attribute("href")
            (
                tasks.append(get_process_files(browser, process_endpoint))
                if process_endpoint
                else ...
            )

        classes = await next_li.get_attribute("class")
        if "disabled" in classes:
            break
        await next_a.click()
        break

    return tasks


async def run_medeiros() -> None:
    create_temp_dir()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(base_url=URL)
        await page.goto("/recuperacoes-judiciais")

        tasks = await get_all_endpoints(page=page, browser=browser)

        await asyncio.gather(*tasks, return_exceptions=True)

        await browser.close()


def main() -> None:
    asyncio.run(run_medeiros())