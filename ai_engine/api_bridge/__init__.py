"""
API Bridge / Communication Layer
Decouples the AI Engine from the Backend for independent scaling.
Provides a clean interface for inference requests and results.
"""

from .inference_service import InferenceService
from .message_broker import MessageBroker
from .api_gateway import AIGateway

__all__ = ["InferenceService", "MessageBroker", "AIGateway"]
