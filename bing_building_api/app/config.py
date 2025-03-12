from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_VERSION: str = "0.1.0"
    PROJECT_NAME: str = "Bing Building Footprint API"
    # zoom value 9 to match https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv 
    ZOOM_LEVEL: int = 9
    BING_BUILDING_CRS: int = 4326
    
    data_dir: str = "data"
    cache_dir: str = "cache"

    class Config:
        case_sensitive = True


settings = Settings()