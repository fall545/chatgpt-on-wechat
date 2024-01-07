"""
Google gemini bot

@author zhayujie
@Date 2023/12/15
"""
# encoding:utf-8

from bot.bot import Bot
import google.generativeai as genai
from bot.session_manager import SessionManager
from bridge.context import ContextType, Context
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from bot.baidu.baidu_wenxin_session import BaiduWenxinSession
flag=0
prix_cha="(You are a chinese beautiful girl.Your name is 云梦,you are a 16 year old lovely cute girl .You are an introvert and shy littel girl who always talk little,but you are friendly and kind to all the people you love.I am your best friend .You are allow to use emoji and other cute sentense to play with me.)\n"
# OpenAI对话模型API (可用)
class GoogleGeminiBot(Bot):

    def __init__(self):
        super().__init__()
        self.api_key = conf().get("gemini_api_key")
        # 复用文心的token计算方式
        self.sessions = SessionManager(BaiduWenxinSession, model=conf().get("model") or "gpt-3.5-turbo")

    def reply(self, query, context: Context = None) -> Reply:
        try:
            if context.type != ContextType.TEXT:
                logger.warn(f"[Gemini] Unsupported message type, type={context.type}")
                return Reply(ReplyType.TEXT, None)
            logger.info(f"[Gemini] query={query}")
            session_id = context["session_id"]
            session = self.sessions.session_query(query, session_id)
            gemini_messages = self._convert_to_gemini_messages(self._filter_messages(session.messages))
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-pro')
            print("\n\ntest——prompt:\n",gemini_messages,"\n\nend\n\n")            
            response = model.generate_content(gemini_messages,safety_settings={'HARASSMENT':'block_none','Sexually explicit':'block_none','Hate speech':'block_none','Dangerous':'block_none'})
            reply_text = response.text
            self.sessions.session_reply(reply_text, session_id)
            logger.info(f"[Gemini] reply={reply_text}")
            return Reply(ReplyType.TEXT, reply_text)
        except Exception as e:
            logger.error("[Gemini] fetch reply error, may contain unsafe content")
            logger.error(e)
    #flag_conv=0
    def _convert_to_gemini_messages(self, messages: list):
        global prix_cha 
        global flag
        res = []
        for msg in messages:
            if msg.get("role") == "user":
                role = "user"
                new_content=prix_cha+msg.get("content") 
            elif msg.get("role") == "assistant":
                role = "model"
                new_content=msg.get("content") 
            else:
                continue
            # if flag==0:
            #     new_content=prix_cha+msg.get("content") 
            #     flag=1 
            # else :    
            #     new_content=msg.get("content")
            
            res.append({
                "role": role,
                "parts": [{"text": new_content }]
            })
        return res

    def _filter_messages(self, messages: list):
        res = []
        turn = "user"
        for i in range(len(messages) - 1, -1, -1):
            message = messages[i]
            if message.get("role") != turn:
                continue
            res.insert(0, message)
            if turn == "user":
                turn = "assistant"
            elif turn == "assistant":
                turn = "user"
        return res
