from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_VERSION: str = "0.1.0"
    PROJECT_NAME: str = "Overture Building Footprint API"

    class Config:
        case_sensitive = True


settings = Settings()