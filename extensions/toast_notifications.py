from dataclasses import dataclass, asdict
from enum import Enum

from flask import Flask
from flask_socketio import SocketIO, emit

from extensions.session_manager import get_all_session_ids_for_user
from src import log

logger = log.get_logger(__name__)


class NotificationType(str, Enum):
    """Available AntDV Notification types."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class NotificationPlacement(str, Enum):
    """Possible AntDV Notification placement."""

    TOP = "top"
    TOP_LEFT = "topLeft"
    TOP_RIGHT = "topRight"
    BOTTOM = "bottom"
    BOTTOM_LEFT = "bottomLeft"
    BOTTOM_RIGHT = "bottomRight"


@dataclass
class ToastNotification:
    title: str
    description: str = ""
    type: NotificationType = NotificationType.INFO
    placement: NotificationPlacement = NotificationPlacement.TOP_RIGHT
    close_after_seconds: float = 5  # '0': don't close automatically

    def as_dict(self) -> dict:
        return asdict(self)


class ToastNotifications:
    def __init__(
        self,
        flask_app: Flask,
        socket: SocketIO,
    ):
        self.flask_app = flask_app
        self.socketio = socket

        self.register()

    def register(self):
        logger.info("Registering ToastNotifications extension")

        @self.socketio.on("toast_notifications_service_ready", namespace="/esdl")
        def toast_notifications_service_ready() -> None:
            """
            When front-end toast notification component is ready, send backed-up notifications.

            """
            logger.info(f"toast_notifications_service_ready, sending backed-up notifications if present.")

            # TODO send backed up messages after 'toast_notifications_service_ready'
            # user = get_session("user-email")
            # user_projects = get_session("user-group")
            # model_runs = self.external_models_storage.get_model_runs_for_current_user(user, user_projects, model_name)
            #
            # return None

    @staticmethod
    def send(toast_notification: ToastNotification):
        emit("toast_notification", toast_notification.as_dict())

    def send_from_outside_request_context(
        self, user_email: str, toast_notification: ToastNotification, resend_if_user_offline: bool = False
    ):
        connected_user_client_ids = get_all_session_ids_for_user(user_email)
        if len(connected_user_client_ids) > 0:
            for client_id in connected_user_client_ids:
                self.socketio.emit(
                    "toast_notification",
                    toast_notification.as_dict(),
                    namespace="/esdl",
                    room=client_id,
                )
        elif resend_if_user_offline:
            # TODO save notification in mongodb user settings and send upon next login
            pass
