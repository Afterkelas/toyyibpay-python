"""Performance benchmark tests for ToyyibPay SDK."""

import asyncio
import time
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch, Mock

import pytest

import toyyibpay
from toyyibpay.models import CallbackData
from toyyibpay.db.postgres import PostgresPaymentStore
from tests.factories import (
    CreateBillInputFactory,
    CallbackDataFactory,
    BatchDataFactory,
    create_test_bill,
)


@pytest.mark.benchmark
class TestClientPerformance:
    """Benchmark client operations."""
    
    @pytest.mark.parametrize("num_requests", [1, 10, 100])
    def test_create_bill_performance(self, benchmark, test_config, num_requests):
        """Benchmark bill creation performance."""
        client = toyyibpay.Client(config=test_config)
        
        # Mock HTTP client to avoid network calls
        with patch.object(client._http_client, "post") as mock_post:
            mock_post.return_value = {"BillCode": "PERF123"}
            
            def create_bills():
                bills = []
                for i in range(num_requests):
                    bill_data = create_test_bill(order_id=f"PERF-{i:04d}")
                    bill = client.create_bill(**bill_data)
                    bills.append(bill)
                return bills
            
            result = benchmark(create_bills)
            assert len(result) == num_requests
    
    def test_model_validation_performance(self, benchmark):
        """Benchmark model validation performance."""
        def validate_models():
            models = []
            for _ in range(1000):
                model = CreateBillInputFactory.create()
                models.append(model)
            return models
        
        result = benchmark(validate_models)
        assert len(result) == 1000
    
    def test_webhook_processing_performance(self, benchmark):
        """Benchmark webhook processing performance."""
        handler = toyyibpay.WebhookHandler()
        
        # Register handlers
        events = []
        
        @handler.on_payment_success
        def on_success(data: CallbackData):
            events.append("success")
        
        @handler.on_payment_failed
        def on_failed(data: CallbackData):
            events.append("failed")
        
        # Create test data
        webhooks = [CallbackDataFactory.create() for _ in range(100)]
        
        def process_webhooks():
            for webhook in webhooks:
                handler.process(webhook)
        
        benchmark(process_webhooks)
        assert len(events) > 0


@pytest.mark.benchmark
@pytest.mark.asyncio
class TestAsyncPerformance:
    """Benchmark async operations."""
    
    async def test_async_concurrent_requests(self, benchmark, test_config):
        """Benchmark concurrent async requests."""
        
        async def make_concurrent_requests():
            async with toyyibpay.AsyncClient(config=test_config) as client:
                # Mock the HTTP client
                async def mock_post(*args, **kwargs):
                    await asyncio.sleep(0.001)  # Simulate network delay
                    return {"BillCode": "ASYNC123"}
                
                client._http_client.post = mock_post
                
                # Create concurrent tasks
                tasks = []
                for i in range(50):
                    bill_data = create_test_bill(order_id=f"ASYNC-{i:04d}")
                    task = client.create_bill(**bill_data)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                return results
        
        # Run benchmark
        loop = asyncio.get_event_loop()
        result = benchmark(lambda: loop.run_until_complete(make_concurrent_requests()))
        assert len(result) == 50
    
    async def test_async_vs_sync_performance(self, benchmark, test_config):
        """Compare async vs sync performance."""
        num_requests = 20
        
        # Sync version
        def sync_requests():
            client = toyyibpay.Client(config=test_config)
            with patch.object(client._http_client, "post") as mock_post:
                mock_post.return_value = {"BillCode": "SYNC123"}
                
                results = []
                for i in range(num_requests):
                    bill = client.create_bill(**create_test_bill())
                    results.append(bill)
                return results
        
        # Async version
        async def async_requests():
            async with toyyibpay.AsyncClient(config=test_config) as client:
                async def mock_post(*args, **kwargs):
                    return {"BillCode": "ASYNC123"}
                
                client._http_client.post = mock_post
                
                tasks = []
                for i in range(num_requests):
                    task = client.create_bill(**create_test_bill())
                    tasks.append(task)
                
                return await asyncio.gather(*tasks)
        
        # Benchmark both
        sync_time = time.time()
        sync_result = sync_requests()
        sync_duration = time.time() - sync_time
        
        async_time = time.time()
        loop = asyncio.get_event_loop()
        async_result = loop.run_until_complete(async_requests())
        async_duration = time.time() - async_time
        
        print(f"\nSync: {sync_duration:.3f}s, Async: {async_duration:.3f}s")
        assert len(sync_result) == len(async_result) == num_requests


@pytest.mark.benchmark
@pytest.mark.db
class TestDatabasePerformance:
    """Benchmark database operations."""
    
    def test_bulk_insert_performance(self, benchmark, db_engine):
        """Benchmark bulk payment insertion."""
        payment_store = PostgresPaymentStore(db_engine)
        payment_store.create_tables()
        
        def bulk_insert():
            payments = BatchDataFactory.create_payment_batch(count=100)
            
            with payment_store.session() as session:
                for payment_data in payments:
                    payment_store.create_payment(
                        session,
                        order_id=payment_data["order_id"],
                        amount=payment_data["amount"],
                        bill_code=payment_data["tp_bill_code"],
                    )
            
            return len(payments)
        
        result = benchmark(bulk_insert)
        assert result == 100
    
    def test_query_performance(self, benchmark, db_engine):
        """Benchmark database query performance."""
        payment_store = PostgresPaymentStore(db_engine)
        payment_store.create_tables()
        
        # Insert test data
        with payment_store.session() as session:
            for i in range(500):
                payment_store.create_payment(
                    session,
                    order_id=f"QUERY-{i:04d}",
                    amount=Decimal("100.00"),
                    bill_code=f"QRY{i:04d}",
                )
        
        def query_payments():
            results = []
            
            with payment_store.session() as session:
                # Test various queries
                results.append(payment_store.list_payments(session, limit=10))
                results.append(payment_store.list_payments(
                    session,
                    status=toyyibpay.PaymentStatus.PENDING,
                    limit=50
                ))
                results.append(payment_store.get_payment_by_order_id(
                    session,
                    "QUERY-0250"
                ))
            
            return results
        
        results = benchmark(query_payments)
        assert len(results) == 3
    
    def test_concurrent_database_access(self, benchmark, db_engine):
        """Benchmark concurrent database access."""
        payment_store = PostgresPaymentStore(db_engine)
        payment_store.create_tables()
        
        def concurrent_operations():
            def create_payment(i):
                with payment_store.session() as session:
                    return payment_store.create_payment(
                        session,
                        order_id=f"CONC-{i:04d}",
                        amount=Decimal("100.00"),
                        bill_code=f"CNC{i:04d}",
                    )
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(create_payment, i) for i in range(50)]
                results = [f.result() for f in futures]
            
            return len(results)
        
        result = benchmark(concurrent_operations)
        assert result == 50


@pytest.mark.benchmark
class TestMemoryUsage:
    """Test memory usage and efficiency."""
    
    def test_large_payload_handling(self, benchmark, test_config):
        """Test handling large payloads."""
        client = toyyibpay.Client(config=test_config)
        
        with patch.object(client._http_client, "post") as mock_post:
            # Create large response
            large_transactions = [
                CallbackDataFactory.create()
                for _ in range(1000)
            ]
            mock_post.return_value = {"data": large_transactions}
            
            def process_large_response():
                return client.get_bill_transactions("LARGE123")
            
            result = benchmark(process_large_response)
            assert len(result) == 1000
    
    def test_model_serialization_performance(self, benchmark):
        """Test model serialization performance."""
        # Create complex nested data
        bills = [CreateBillInputFactory.create() for _ in range(100)]
        
        def serialize_models():
            serialized = []
            for bill in bills:
                data = bill.model_dump(by_alias=True)
                serialized.append(data)
            return serialized
        
        result = benchmark(serialize_models)
        assert len(result) == 100


@pytest.mark.benchmark
class TestOptimizations:
    """Test various optimizations."""
    
    def test_connection_pooling_benefit(self, benchmark, test_config):
        """Test benefit of connection pooling."""
        # Without pooling (new client each time)
        def without_pooling():
            results = []
            for i in range(20):
                client = toyyibpay.Client(config=test_config)
                with patch.object(client._http_client, "post") as mock_post:
                    mock_post.return_value = {"BillCode": f"NO-POOL-{i}"}
                    bill = client.create_bill(**create_test_bill())
                    results.append(bill)
                client.close()  # Close connection
            return results
        
        # With pooling (reuse client)
        def with_pooling():
            client = toyyibpay.Client(config=test_config)
            results = []
            
            with patch.object(client._http_client, "post") as mock_post:
                for i in range(20):
                    mock_post.return_value = {"BillCode": f"POOL-{i}"}
                    bill = client.create_bill(**create_test_bill())
                    results.append(bill)
            
            return results
        
        # Compare performance
        no_pool_time = time.time()
        no_pool_result = without_pooling()
        no_pool_duration = time.time() - no_pool_time
        
        pool_time = time.time()
        pool_result = with_pooling()
        pool_duration = time.time() - pool_time
        
        print(f"\nWithout pooling: {no_pool_duration:.3f}s")
        print(f"With pooling: {pool_duration:.3f}s")
        print(f"Improvement: {(no_pool_duration - pool_duration) / no_pool_duration * 100:.1f}%")
        
        assert len(no_pool_result) == len(pool_result) == 20
    
    def test_caching_benefit(self, benchmark):
        """Test potential caching benefits."""
        # Simulate caching configuration
        cache = {}
        
        def get_config(key):
            if key in cache:
                return cache[key]
            
            # Simulate expensive operation
            time.sleep(0.001)
            value = f"config-{key}"
            cache[key] = value
            return value
        
        def with_caching():
            results = []
            for i in range(100):
                # Repeated access to same configs
                config_key = f"key-{i % 10}"  # Only 10 unique keys
                value = get_config(config_key)
                results.append(value)
            return results
        
        result = benchmark(with_caching)
        assert len(result) == 100
        assert len(cache) == 10  # Only 10 unique values cached