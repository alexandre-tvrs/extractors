from io import BytesIO
from bs4 import BeautifulSoup
from _config import load_app_config
from requests import Response, Session
from selenium.webdriver.chrome.options import Options
from python_anticaptcha import AnticaptchaClient, ImageToTextTask

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

def solve_captcha(captcha_binary: bytes) -> str:
    config = load_app_config()
    client = AnticaptchaClient(config.APP.CREDENTIALS.ANTICAPTCHA)
    task = ImageToTextTask(BytesIO(captcha_binary))
    job = client.createTask(task)
    job.join()
    return job.get_captcha_text()