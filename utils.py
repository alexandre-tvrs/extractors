from bs4 import BeautifulSoup
from requests import Response, Session

def get_first_view_state(url: str, session: Session) -> str:
    response: Response = session.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.find("input", {"name": "javax.faces.ViewState"})["value"]

def get_precatory_data(url:str, session: Session, payload: dict, header: dict) -> str:
    response = session.post(url, data=payload, headers=header)
    return response.text