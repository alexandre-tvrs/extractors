from bs4 import BeautifulSoup
from requests import Response, Session
from selenium.webdriver.chrome.options import Options

def get_first_view_state(url: str, session: Session) -> str:
    response: Response = session.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.find("input", {"name": "javax.faces.ViewState"})["value"]

def get_precatory_data(url:str, session: Session, payload: dict, header: dict) -> str:
    response = session.post(url, data=payload, headers=header)
    return response.text

def get_headless_selenium_options() -> Options:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    return chrome_options

def get_selenium_options() -> Options:
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    return chrome_options