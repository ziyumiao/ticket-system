from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "钉钉工单系统"
    app_version: str = "0.1.0"

    database_url: str = "sqlite:///./ticket.db"

    dingtalk_app_key: str = ""
    dingtalk_app_secret: str = ""
    dingtalk_agent_id: int = 0
    dingtalk_robot_code: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
BASE_DIR = Path(__file__).parent
