#  This work is based on original code developed and copyrighted by TNO.
#  Subsequent contributions are licensed to you by the developers of such code and are
#  made available to the Project under one or several contributor license agreements.
#
#  This work is licensed to you under the Apache License, Version 2.0.
#  You may obtain a copy of the license at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Contributors:
#      TNO         - Initial implementation
#  Manager:
#      TNO

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone, timedelta
from typing import Callable
import uuid

from flask import Flask
from flask_socketio import SocketIO

from extensions.session_manager import get_all_session_ids_for_user
from src import log

logger = log.get_logger(__name__)


class PromptType(str, Enum):

    CHOICE = "choice"
    INFO = "info"
    ERROR = "error"


@dataclass
class PromptChoice:
    key: str
    label: str
    style: str = "default"


@dataclass
class Prompt:
    prompt_type: PromptType
    title: str
    message: str
    choices: list[PromptChoice]
    user_email: str
    continuation_id: str | None = None
    context: dict = field(default_factory=dict)
    details: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def payload(self) -> dict:
        """Return the dict sent to the frontend. Strips server-side fields."""
        data = asdict(self)
        data.pop("continuation_id", None)
        data.pop("context", None)
        data.pop("user_email", None)
        return data


class PromptManager:
    _continuation_handlers: dict[str, Callable] = {}
    _instance = None

    _PROMPT_TTL = timedelta(hours=24)

    def __init__(self, flask_app: Flask, socket: SocketIO):
        self.flask_app = flask_app
        self.socketio = socket
        self._pending_prompts: dict[str, Prompt] = {}
        self._prompt_sent_at: dict[str, datetime] = {}
        self.register()
        PromptManager._instance = self

    @classmethod
    def get_instance(cls) -> "PromptManager | None":
        """Return the shared instance used by import and service handlers."""
        return cls._instance

    @classmethod
    def register_handler(cls, continuation_id: str, handler: Callable):
        """Register a callback for when the user responds to a prompt with the given continuation_id."""
        cls._continuation_handlers[continuation_id] = handler

    def register(self) -> None:
        logger.info("Registering PromptManager extension")

        @self.socketio.on("prompt_response", namespace="/esdl")
        def _prompt_response(data):
            if not isinstance(data, dict):
                logger.warning("prompt_response payload is not a dict")
                return
            prompt_id = data.get("prompt_id")
            choice_key = data.get("choice_key")
            if not prompt_id or not choice_key:
                logger.warning("prompt_response missing prompt_id or choice_key")
                return
            self.handle_prompt_response(prompt_id, choice_key)

    def handle_prompt_response(self, prompt_id: str, choice_key: str) -> None:
        """Look up the pending prompt and invoke its continuation handler."""
        self._prompt_sent_at.pop(prompt_id, None)
        prompt = self._pending_prompts.pop(prompt_id, None)
        if prompt is None:
            logger.warning(f"Prompt response for unknown prompt_id={prompt_id}")
            return
        if not prompt.continuation_id:
            return
        handler = self._continuation_handlers.get(prompt.continuation_id)
        if handler is None:
            logger.warning(f"No continuation handler for id={prompt.continuation_id}")
            return
        handler(choice_key, prompt.context)

    def send(self, prompt: Prompt) -> str:
        """Store the prompt and emit it to all sessions of the target user."""
        self._purge_expired_prompts()
        self._pending_prompts[prompt.id] = prompt
        self._prompt_sent_at[prompt.id] = datetime.now(timezone.utc)
        connected_user_client_ids = get_all_session_ids_for_user(prompt.user_email)
        if not connected_user_client_ids:
            logger.info(f"No active sessions for user '{prompt.user_email}', prompt queued")
            return prompt.id
        payload = prompt.payload()
        for client_id in connected_user_client_ids:
            self.socketio.emit("prompt", payload, namespace="/esdl", room=client_id)
        return prompt.id

    def _purge_expired_prompts(self) -> None:
        cutoff = datetime.now(timezone.utc) - self._PROMPT_TTL
        expired = [pid for pid, sent in self._prompt_sent_at.items() if sent < cutoff]
        for pid in expired:
            self._pending_prompts.pop(pid, None)
            self._prompt_sent_at.pop(pid, None)
        if expired:
            logger.debug(f"Purged {len(expired)} expired pending prompt(s)")

    def send_error(
        self,
        user_email: str,
        title: str,
        exception: Exception,
        details: str | None = None,
    ) -> None:
        """Send a dismissible error prompt."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        exc_type = type(exception).__name__
        message = f"{exc_type}: {exception} [{timestamp}]"
        if not self.flask_app.debug:
            details = None
        self.send(Prompt(
            prompt_type=PromptType.ERROR,
            title=title,
            message=message,
            choices=[PromptChoice("ok", "OK", "primary")],
            user_email=user_email,
            details=details,
        ))
