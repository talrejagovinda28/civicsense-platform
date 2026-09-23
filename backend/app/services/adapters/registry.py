from __future__ import annotations

from app.core.config import settings
from app.models.authority_channel import ChannelActivation, ChannelMode, ExternalChannel
from app.services.adapters.base import SubmissionAdapter
from app.services.adapters.fake import FakeAdapter
from app.services.adapters.guided import GuidedPortalAdapter, GuidedWhatsAppAdapter


class ChannelNotEnabled(Exception):
    def __init__(self, message: str = "Channel not enabled for live dispatch") -> None:
        self.message = message
        super().__init__(message)


def _guided_channel_enabled(channel: ExternalChannel) -> bool:
    activation = ChannelActivation(channel.activation)
    if activation == ChannelActivation.DISABLED or not channel.enabled:
        return False
    return activation in {ChannelActivation.MANUAL, ChannelActivation.LIVE_APPROVED}


def get_adapter(channel: ExternalChannel) -> SubmissionAdapter:
    mode = ChannelMode(channel.mode)
    activation = ChannelActivation(channel.activation)

    if mode in {ChannelMode.GUIDED_PORTAL, ChannelMode.GUIDED_WHATSAPP}:
        if not _guided_channel_enabled(channel):
            raise ChannelNotEnabled(
                f"Guided channel {channel.id} is not enabled (activation={activation.value})"
            )
        if mode == ChannelMode.GUIDED_PORTAL:
            return GuidedPortalAdapter()
        return GuidedWhatsAppAdapter()

    if activation == ChannelActivation.TEST_ONLY and settings.fake_adapters_allowed:
        return FakeAdapter()

    if activation in {ChannelActivation.AUTOMATED, ChannelActivation.LIVE_APPROVED}:
        if channel.enabled and settings.EXTERNAL_DISPATCH_GLOBAL_ENABLED:
            raise ChannelNotEnabled(f"Live adapter for {mode.value} is not implemented")
        raise ChannelNotEnabled(f"Channel {channel.id} not enabled for live dispatch")

    raise ChannelNotEnabled(
        f"Channel {channel.id} activation={activation.value} is not enabled for dispatch"
    )
