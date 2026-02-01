from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

class BaseHandler(ABC):
    def __init__(self, name: str):
        self.name = name
        self.states = self.define_states()

    @abstractmethod
    def define_states(self) -> Enum:
        ...

    @abstractmethod
    def get_conversation_handler(self) -> ConversationHandler:
        ...

    @abstractmethod
    def is_available_for_user(self, user_id: int) -> bool:
        ...