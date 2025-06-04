from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    newsapi_key: str = "e84e1023a6dd43bfa41e70e3ca7c5157"
    guardian_key: str = "test"
    reuters_key: str = ""  # Necesitarás registrarte en Reuters API para obtener una key
    newsdata_key: str = "pub_4e2e29053a7844e08d5fa2eceb7231c7"
