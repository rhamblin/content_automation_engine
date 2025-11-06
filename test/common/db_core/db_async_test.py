import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import OperationalError, DBAPIError
from tenacity import RetryError
import time
import logging

import os
os.environ['DB_URL'] = 'postgresql+asyncpg://dummy:dummy@localhost/dummy'

class TestDatabaseRetryLogic:
    """Tests for database connection retry logic in db_async.py"""

    @patch('common.db_core.db_async.create_async_engine')
    def test_successful_connection_on_first_attempt(self, mock_create_engine):
        """
        GIVEN: Database is available
        WHEN: get_engine() is called
        THEN: Connection succeeds on first attempt without retries
        """
        # Arrange
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        # Act
        from common.db_core.db_async import get_engine
        result = get_engine()

        # Assert
        assert mock_create_engine.call_count == 1
        assert result == mock_engine


    @patch('common.db_core.db_async.create_async_engine')
    def test_retry_on_operational_error_then_success(self, mock_create_engine):
        """
        GIVEN: Database fails first attempt, succeeds second attempt
        WHEN: get_engine() is called
        THEN: Retries once and succeeds
        """
        # Arrange
        mock_engine = MagicMock()
        mock_create_engine.side_effect = [
            OperationalError("connection refused", None, None),  # 1st attempt fails
            mock_engine  # 2nd attempt succeeds
        ]

        # Act
        from common.db_core.db_async import get_engine
        result = get_engine()

        # Assert
        assert mock_create_engine.call_count == 2
        assert result == mock_engine


    @patch('common.db_core.db_async.create_async_engine')
    def test_retry_exhausted_after_max_attempts(self, mock_create_engine):
        """
        GIVEN: Database is persistently unavailable
        WHEN: get_engine() is called
        THEN: Retries 3 times then raises RetryError
        """
        # Arrange
        mock_create_engine.side_effect = OperationalError(
            "connection refused", None, None
        )

        # Act & Assert
        from common.db_core.db_async import get_engine
        with pytest.raises(RetryError):
            get_engine()

        # Should attempt 3 times total (initial + 2 retries based on your config)
        assert mock_create_engine.call_count == 3


    @patch('common.db_core.db_async.create_async_engine')
    def test_retries_on_connection_refused_error(self, mock_create_engine):
        """
        GIVEN: Database refuses connection initially
        WHEN: get_engine() is called
        THEN: Retries and eventually succeeds
        """
        # Arrange
        mock_engine = MagicMock()
        mock_create_engine.side_effect = [
            ConnectionRefusedError("DB not accepting connections"),
            mock_engine
        ]

        # Act
        from common.db_core.db_async import get_engine
        result = get_engine()

        # Assert
        assert mock_create_engine.call_count == 2
        assert result == mock_engine


    @patch('common.db_core.db_async.create_async_engine')
    def test_retries_on_dbapi_error(self, mock_create_engine):
        """
        GIVEN: Database driver error occurs
        WHEN: get_engine() is called
        THEN: Retries on DBAPIError
        """
        # Arrange
        mock_engine = MagicMock()
        mock_create_engine.side_effect = [
            DBAPIError("asyncpg driver error", None, None),
            mock_engine
        ]

        # Act
        from common.db_core.db_async import get_engine
        result = get_engine()

        # Assert
        assert mock_create_engine.call_count == 2


    @patch('common.db_core.db_async.create_async_engine')
    def test_no_retry_on_programming_error(self, mock_create_engine):
        """
        GIVEN: Programming error in code (e.g., bad URL format)
        WHEN: get_engine() is called
        THEN: Fails immediately WITHOUT retrying
        """
        # Arrange
        mock_create_engine.side_effect = ValueError("Invalid DATABASE_URL")

        # Act & Assert
        from common.db_core.db_async import get_engine
        with pytest.raises(ValueError):
            get_engine()

        # Should only attempt once (no retries for programming errors)
        assert mock_create_engine.call_count == 1


    @patch('common.db_core.db_async.create_async_engine')
    def test_exponential_backoff_timing(self, mock_create_engine):
        """
        GIVEN: Database fails multiple times
        WHEN: get_engine() retries
        THEN: Wait time increases exponentially (1s, 2s, 4s)
        """
        # Arrange
        mock_create_engine.side_effect = [
            OperationalError("fail", None, None),
            OperationalError("fail", None, None),
            OperationalError("fail", None, None),
        ]

        # Act
        start_time = time.time()
        from common.db_core.db_async import get_engine

        with pytest.raises(RetryError):
            get_engine()

        elapsed = time.time() - start_time

        # Assert
        # With min=1, max=10: waits should be ~1s + ~2s = ~3s total
        # Allow some margin for execution time
        assert 3 <= elapsed <= 6, f"Expected ~3-6s with backoff, got {elapsed:.2f}s"


    @patch('common.db_core.db_async.create_async_engine')
    def test_logs_retry_attempts(self, mock_create_engine, caplog):
        """
        GIVEN: Database fails then succeeds
        WHEN: get_engine() retries
        THEN: Retry attempts are logged at WARNING level
        """
        # Arrange
        mock_engine = MagicMock()
        mock_create_engine.side_effect = [
            OperationalError("fail", None, None),
            mock_engine
        ]

        # Act
        with caplog.at_level(logging.WARNING):
            from common.db_core.db_async import get_engine
            get_engine()

        # Assert
        # Should see "Retrying" in warning logs
        retry_logs = [record for record in caplog.records if "Retrying" in record.message]
        assert len(retry_logs) >= 1, "Expected retry attempt to be logged"


    @patch('common.db_core.db_async.create_async_engine')
    def test_multiple_exception_types_during_retry(self, mock_create_engine):
        """
        GIVEN: Different retryable errors occur across attempts
        WHEN: get_engine() is called
        THEN: Continues retrying until success
        """
        # Arrange
        mock_engine = MagicMock()
        mock_create_engine.side_effect = [
            OperationalError("connection timeout", None, None),
            ConnectionRefusedError("connection refused"),
            mock_engine  # Success
        ]

        # Act
        from common.db_core.db_async import get_engine
        result = get_engine()

        # Assert
        assert mock_create_engine.call_count == 3
        assert result == mock_engine