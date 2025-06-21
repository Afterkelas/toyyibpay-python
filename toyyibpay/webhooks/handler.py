"""Webhook handler for ToyyibPay callbacks."""

import hmac
import hashlib
import json
from typing import Dict, Any, Optional, Callable, Union
from datetime import datetime

from ..models import CallbackData
from ..exceptions import WebhookError, SignatureVerificationError
from ..enums import PaymentStatus


class WebhookHandler:
    """Handler for ToyyibPay webhook callbacks.

    Example:
        >>> handler = WebhookHandler()
        >>> handler.on_payment_success(lambda data: print(f"Payment {data.order_id} successful!"))
        >>> handler.on_payment_failed(lambda data: print(f"Payment {data.order_id} failed!"))
    """

    def __init__(self, secret_key: Optional[str] = None) -> None:
        """Initialize webhook handler.

        Args:
            secret_key: Secret key for signature verification (if implemented by ToyyibPay)
        """
        self.secret_key = secret_key
        self._handlers: Dict[str, list[Callable]] = {
            "payment.success": [],
            "payment.failed": [],
            "payment.pending": [],
            "all": [],
        }

    def on_payment_success(self, handler: Callable[[CallbackData], Any]) -> None:
        """Register handler for successful payments.

        Args:
            handler: Callback function that receives CallbackData
        """
        self._handlers["payment.success"].append(handler)

    def on_payment_failed(self, handler: Callable[[CallbackData], Any]) -> None:
        """Register handler for failed payments.

        Args:
            handler: Callback function that receives CallbackData
        """
        self._handlers["payment.failed"].append(handler)

    def on_payment_pending(self, handler: Callable[[CallbackData], Any]) -> None:
        """Register handler for pending payments.

        Args:
            handler: Callback function that receives CallbackData
        """
        self._handlers["payment.pending"].append(handler)

    def on_all_events(self, handler: Callable[[CallbackData], Any]) -> None:
        """Register handler for all payment events.

        Args:
            handler: Callback function that receives CallbackData
        """
        self._handlers["all"].append(handler)

    def process(
        self,
        payload: Union[str, bytes, Dict[str, Any]],
        headers: Optional[Dict[str, str]] = None,
        verify_signature: bool = False,
    ) -> CallbackData:
        """Process webhook payload.

        Args:
            payload: Webhook payload (JSON string, bytes, or dict)
            headers: Request headers (for signature verification)
            verify_signature: Whether to verify signature

        Returns:
            Processed CallbackData

        Raises:
            WebhookError: If processing fails
            SignatureVerificationError: If signature verification fails
        """
        # Parse payload
        if isinstance(payload, (str, bytes)):
            try:
                data = json.loads(payload)
            except json.JSONDecodeError as e:
                raise WebhookError(f"Invalid JSON payload: {e}")
        else:
            data = payload

        # Verify signature if requested
        if verify_signature and self.secret_key:
            self._verify_signature(payload, headers)

        # Create CallbackData model
        try:
            callback_data = CallbackData(**data)
        except Exception as e:
            raise WebhookError(f"Invalid callback data: {e}")

        # Determine event type based on status
        event_type = self._get_event_type(callback_data.status)

        # Call registered handlers
        self._call_handlers(event_type, callback_data)
        self._call_handlers("all", callback_data)

        return callback_data

    def _verify_signature(
        self,
        payload: Union[str, bytes, Dict[str, Any]],
        headers: Optional[Dict[str, str]],
    ) -> None:
        """Verify webhook signature.

        Note: This is a placeholder implementation. 
        ToyyibPay doesn't document webhook signatures in their API.
        Implement based on their actual signature scheme if available.
        """
        if not headers:
            raise SignatureVerificationError(
                "No headers provided for signature verification"
            )

        # Example signature verification (adjust based on ToyyibPay's actual implementation)
        signature_header = headers.get("X-ToyyibPay-Signature", "")

        if not signature_header:
            raise SignatureVerificationError("No signature header found")

        # Convert payload to bytes if needed
        if isinstance(payload, dict):
            payload_bytes = json.dumps(payload, separators=(",", ":")).encode()
        elif isinstance(payload, str):
            payload_bytes = payload.encode()
        else:
            payload_bytes = payload

        # Calculate expected signature
        expected_signature = hmac.new(
            self.secret_key.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        # Compare signatures
        if not hmac.compare_digest(signature_header, expected_signature):
            raise SignatureVerificationError("Invalid signature")

    def _get_event_type(self, status: PaymentStatus) -> str:
        """Get event type from payment status."""
        if status == PaymentStatus.SUCCESS:
            return "payment.success"
        elif status == PaymentStatus.FAILED:
            return "payment.failed"
        else:
            return "payment.pending"

    def _call_handlers(self, event_type: str, data: CallbackData) -> None:
        """Call all handlers for an event type."""
        for handler in self._handlers.get(event_type, []):
            try:
                handler(data)
            except Exception as e:
                # Log error but don't stop processing other handlers
                print(f"Error in webhook handler: {e}")


def create_webhook_response(success: bool = True, message: str = "OK") -> Dict[str, Any]:
    """Create a standard webhook response.

    Args:
        success: Whether the webhook was processed successfully
        message: Response message

    Returns:
        Response dictionary
    """
    return {
        "success": success,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }
