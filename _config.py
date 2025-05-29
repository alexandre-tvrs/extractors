import yaml
from pydantic import BaseModel
from yaml import CLoader as Loader

class AppConfig(BaseModel):
    SAVE_PATH: str

class Config(BaseModel):
    APP: AppConfig
        
def load_app_config() -> Config:    
    with open("settings.yaml", "r") as f:
        config_yaml = yaml.load(f, Loader=Loader)
    
    return Config(**config_yaml)

def update_app_config(config: Config) -> None:
    with open("settings.yaml", "w") as f:
        yaml.dump(config.model_dump(), f)