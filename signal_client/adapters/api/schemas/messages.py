from pydantic import BaseModel


class SendMessageRequest(BaseModel):
    number: str
    recipients: list[str]
    message: str
