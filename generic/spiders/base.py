from pydantic import BaseModel


class SpiderBaseConfig(BaseModel):
    urls: str
