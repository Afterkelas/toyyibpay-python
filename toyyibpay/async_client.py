"""Async ToyyibPay client."""

from decimal import Decimal
from typing import Optional, List, Dict, Any, Union

from .config import ToyyibPayConfig, get_config
from .http_client import AsyncHTTPClient
from .models import (
    CreateBillInput,
    BillResponse,
    TransactionData,
    InitPaymentInput,
    CategoryInput,
)
from .enums import PaymentStatus, CORPORATE_BANKING_THRESHOLD
from .exceptions import ValidationError
from .utils import generate_ulid, dict_to_form_data


class AsyncToyyibPayClient:
    """Async client for interacting with ToyyibPay API.

    Example:
        >>> import asyncio
        >>> import toyyibpay
        >>> 
        >>> async def main():
        ...     async with toyyibpay.AsyncClient(api_key="your-api-key") as client:
        ...         bill = await client.create_bill(
        ...             name="John Doe",
        ...             email="john@example.com",
        ...             phone="0123456789",
        ...             amount=100.00,
        ...             order_id="ORD-12345"
        ...         )
        ...         print(bill.payment_url)
        >>> 
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[ToyyibPayConfig] = None,
        **kwargs: Any
    ) -> None:
        """Initialize async ToyyibPay client.

        Args:
            api_key: API key for ToyyibPay. If not provided, will use global config.
            config: Complete configuration object. Takes precedence over api_key.
            **kwargs: Additional configuration options.
        """
        if config:
            self.config = config
        elif api_key:
            self.config = ToyyibPayConfig(api_key=api_key, **kwargs)
        else:
            self.config = get_config()

        self._http_client: Optional[AsyncHTTPClient] = None

    async def __aenter__(self) -> "AsyncToyyibPayClient":
        """Enter async context manager."""
        self._http_client = AsyncHTTPClient(self.config)
        await self._http_client.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        if self._http_client:
            await self._http_client.__aexit__(exc_type, exc_val, exc_tb)

    async def create_bill(
        self,
        name: str,
        email: str,
        phone: str,
        amount: Union[float, Decimal],
        order_id: str,
        description: Optional[str] = None,
        return_url: Optional[str] = None,
        callback_url: Optional[str] = None,
        **kwargs: Any
    ) -> BillResponse:
        """Create a new bill for payment.

        Args:
            name: Customer name
            email: Customer email
            phone: Customer phone number
            amount: Payment amount (in MYR)
            order_id: Your internal order/reference ID
            description: Bill description (optional)
            return_url: URL to redirect after payment (optional)
            callback_url: URL for payment notification (optional)
            **kwargs: Additional bill parameters

        Returns:
            BillResponse with bill_code and payment_url

        Example:
            >>> async with client:
            ...     bill = await client.create_bill(
            ...         name="John Doe",
            ...         email="john@example.com",
            ...         phone="0123456789",
            ...         amount=100.00,
            ...         order_id="ORD-12345"
            ...     )
        """
        if not self._http_client:
            raise RuntimeError(
                "AsyncToyyibPayClient must be used as async context manager")

        # Convert amount to Decimal for precision
        if isinstance(amount, float):
            amount = Decimal(str(amount))

        # Validate amount
        if amount <= 0:
            raise ValidationError("Amount must be greater than 0")

        # Enable corporate banking for large amounts
        enable_fpx_b2b = 1 if amount >= CORPORATE_BANKING_THRESHOLD else 0

        # Prepare bill data
        bill_data = CreateBillInput(
            category_code=kwargs.get("category_code", self.config.category_id),
            bill_name=kwargs.get("bill_name", generate_ulid()),
            bill_description=description or "Payment",
            bill_amount=float(amount),
            bill_to=name,
            bill_email=email,
            bill_phone=phone,
            bill_external_reference_no=order_id,
            bill_return_url=return_url or self.config.return_url or "",
            bill_callback_url=callback_url or self.config.callback_url or "",
            enable_fpx_b2b=enable_fpx_b2b,
            **kwargs
        )

        # Convert model to dict and ensure all values are properly formatted for form data
        bill_dict = bill_data.model_dump(by_alias=True)
        form_data = dict_to_form_data(bill_dict)

        # Send request
        response = await self._http_client.post(
            "createBill",
            form_data
        )

        # Handle response
        if not response.get("BillCode"):
            raise ValidationError(f"Failed to create bill: {response}")

        bill_response = BillResponse(bill_code=response["BillCode"])
        # Set proper payment URL based on environment
        bill_response.__dict__[
            "payment_url"] = f"{self.config.base_url}/{bill_response.bill_code}"

        return bill_response

    async def create_bill_from_input(self, payment_input: InitPaymentInput) -> BillResponse:
        """Create a bill from InitPaymentInput model.

        Args:
            payment_input: Payment initialization input

        Returns:
            BillResponse with bill_code and payment_url
        """
        return await self.create_bill(
            name=payment_input.name,
            email=payment_input.email,
            phone=payment_input.phone,
            amount=payment_input.amount,
            order_id=payment_input.order_id,
            return_url=payment_input.return_url,
        )

    async def get_bill_transactions(
        self,
        bill_code: str,
        status: Optional[PaymentStatus] = None
    ) -> List[TransactionData]:
        """Get transactions for a specific bill.

        Args:
            bill_code: The bill code to query
            status: Filter by payment status (optional)

        Returns:
            List of transaction data

        Example:
            >>> async with client:
            ...     transactions = await client.get_bill_transactions("abc123")
            ...     successful = await client.get_bill_transactions(
            ...         "abc123",
            ...         status=PaymentStatus.SUCCESS
            ...     )
        """
        if not self._http_client:
            raise RuntimeError(
                "AsyncToyyibPayClient must be used as async context manager")

        data = {"billCode": bill_code}
        if status is not None:
            data["billpaymentStatus"] = int(status)

        response = await self._http_client.post("getBillTransactions", data)

        # Handle response - could be list or dict
        if isinstance(response, dict) and "data" in response:
            transactions_data = response["data"]
        elif isinstance(response, list):
            transactions_data = response
        else:
            transactions_data = []

        # Convert to TransactionData models
        transactions = []
        for tx_data in transactions_data:
            # Handle PHP's weird type conversions
            if "billStatus" in tx_data and isinstance(tx_data["billStatus"], str):
                tx_data["billStatus"] = int(tx_data["billStatus"])
            if "billpaymentStatus" in tx_data and isinstance(tx_data["billpaymentStatus"], str):
                tx_data["billpaymentStatus"] = int(
                    tx_data["billpaymentStatus"])
            if "billSplitPayment" in tx_data:
                tx_data["billSplitPayment"] = tx_data["billSplitPayment"] == "1"
            if "billpaymentAmount" in tx_data and isinstance(tx_data["billpaymentAmount"], str):
                tx_data["billpaymentAmount"] = float(
                    tx_data["billpaymentAmount"])

            transactions.append(TransactionData(**tx_data))

        return transactions

    async def check_payment_status(self, bill_code: str) -> Optional[PaymentStatus]:
        """Check the payment status of a bill.

        Args:
            bill_code: The bill code to check

        Returns:
            Payment status or None if no successful payment found

        Example:
            >>> async with client:
            ...     status = await client.check_payment_status("abc123")
            ...     if status == PaymentStatus.SUCCESS:
            ...         print("Payment successful!")
        """
        transactions = await self.get_bill_transactions(
            bill_code,
            status=PaymentStatus.SUCCESS
        )

        if transactions:
            return PaymentStatus.SUCCESS

        # Check all transactions to get latest status
        all_transactions = await self.get_bill_transactions(bill_code)
        if all_transactions:
            # Return the latest transaction status
            return all_transactions[-1].bill_payment_status

        return None

    async def create_category(self, name: str, description: str) -> Dict[str, Any]:
        """Create a new payment category.

        Args:
            name: Category name
            description: Category description

        Returns:
            Response with category code

        Example:
            >>> async with client:
            ...     category = await client.create_category(
            ...         name="Online Store",
            ...         description="Payments for online store"
            ...     )
        """
        if not self._http_client:
            raise RuntimeError(
                "AsyncToyyibPayClient must be used as async context manager")

        response = await self._http_client.post("createCategory", {
            "catname": name,
            "catdescription": description,
        })

        return response


# Convenience function for creating async client
def AsyncClient(
    api_key: Optional[str] = None,
    **kwargs: Any
) -> AsyncToyyibPayClient:
    """Create an async ToyyibPay client instance.

    Args:
        api_key: API key for ToyyibPay
        **kwargs: Additional configuration options

    Returns:
        AsyncToyyibPayClient instance

    Example:
        >>> import asyncio
        >>> import toyyibpay
        >>> 
        >>> async def main():
        ...     async with toyyibpay.AsyncClient(api_key="your-api-key") as client:
        ...         # Use client
        ...         pass
        >>> 
        >>> asyncio.run(main())
    """
    return AsyncToyyibPayClient(api_key=api_key, **kwargs)
