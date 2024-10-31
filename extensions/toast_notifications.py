from dataclasses import dataclass, asdict
from enum import Enum

from flask import Flask
from flask_socketio import SocketIO, emit

from extensions.session_manager import get_all_session_ids_for_user
from src import log

logger = log.get_logger(__name__)


class NotificationType(str, Enum):
    """AntDV Notification type options."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class NotificationPlacement(str, Enum):
    """AntDV Notification placement options."""

    TOP = "top"
    TOP_LEFT = "topLeft"
    TOP_RIGHT = "topRight"
    BOTTOM = "bottom"
    BOTTOM_LEFT = "bottomLeft"
    BOTTOM_RIGHT = "bottomRight"


@dataclass
class ToastNotification:
    """AntDV notification configuration."""

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
    ) -> None:
        self.flask_app = flask_app
        self.socketio = socket
        self.register()

    def register(self) -> None:
        logger.info("Registering ToastNotifications extension")

        @self.socketio.on("toast_notifications_service_ready", namespace="/esdl")
        def toast_notifications_service_ready() -> None:
            """
            When front-end toast notification component is ready, send backed-up notifications.
            """
            logger.info(f"toast_notifications_service_ready, sending backed-up notifications if present.")

            # TODO send backed up messages after 'toast_notifications_service_ready'
            # user = get_session("user-email")
            # user_group_paths = get_session("user-group-path")
            # model_runs = self.external_models_storage.get_model_runs_for_current_user(user, user_group_paths, model_name)

    @staticmethod
    def send(toast_notification: ToastNotification):
        """Send notification to active client."""
        emit("toast_notification", toast_notification.as_dict())

    def send_from_outside_request_context(
        self, user_email: str, toast_notification: ToastNotification, resend_if_user_offline: bool = False
    ) -> None:
        """
        Send notification to all connected clients for a specific user, if available.

        :param user_email: Email address of the user.
        :param toast_notification: ToastNotification instance.
        :param resend_if_user_offline: If the user is offline, whether to resend this notification upon login.
        """
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
