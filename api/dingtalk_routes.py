from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/dingtalk", tags=["dingtalk"])


class DingTalkCallback(BaseModel):
    msgtype: str = ""
    text: dict = {}
    senderId: str = ""
    conversationId: str = ""
    chatbotUserId: str = ""
    msgId: str = ""
    senderNick: str = ""
    isAdmin: bool = False
    createAt: int = 0


@router.post("/webhook")
async def dingtalk_webhook(data: DingTalkCallback):
    return {"msgtype": "text", "text": {"content": "收到消息，功能开发中..."}}
