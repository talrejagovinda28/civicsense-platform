from __future__ import annotations

from app.models.authority_channel import ChannelActivation, ChannelMode, ExternalChannel
from app.services.adapters.base import SubmissionAdapter
from app.services.adapters.fake import FakeAdapter
from app.services.adapters.guided import GuidedPortalAdapter, GuidedWhatsAppAdapter


class ChannelNotEnabled(Exception):
    def __init__(self, message: str = "Channel not enabled for live dispatch") -> None:
        self.message = message
        super().__init__(message)


def get_adapter(
    channel: ExternalChannel,
    *,
    simulation: bool = False,
) -> SubmissionAdapter:
    mode = ChannelMode(channel.mode)
    activation = ChannelActivation(channel.activation)

    if mode == ChannelMode.GUIDED_PORTAL:
        return GuidedPortalAdapter()
    if mode == ChannelMode.GUIDED_WHATSAPP:
        return GuidedWhatsAppAdapter()

    if activation in {ChannelActivation.TEST_ONLY, ChannelActivation.DISABLED} and simulation:
        return FakeAdapter()

    if activation in {ChannelActivation.AUTOMATED, ChannelActivation.LIVE_APPROVED}:
        raise ChannelNotEnabled(f"Live adapter for {mode.value} is not implemented")

    raise ChannelNotEnabled(
        f"Channel {channel.id} activation={activation.value}; use TEST_ONLY simulation or guided mode"
    )
